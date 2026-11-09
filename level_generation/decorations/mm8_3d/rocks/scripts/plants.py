"""Plants on the rune stones (rock65/68/69), added to each LOD object by build_rock.py after the rock's own bake:
woody vines and roots (tubes, material `Bark`) and leaf, flower, sprig and grass cards (material `Plant`, alpha
tested, double-sided), all on the procedural atlas textures/plants_* (scripts/make_plant_atlas.py). Positions come
from the sprite (x2 canvas pixels, rocks.json `plants`) through sprite_to_model, and are put on the stone's front by
casting rays from the front (-y) onto the LOD itself. Coarser LODs keep fewer cards (larger) and thinner tubes.

Kinds: vine {path [[px, py]...], radius [base, tip] px, kind 'root' = grey root bark}; leaves {kind ivy|orange, box
[px0, py0, px1, py1], count, size px}; sprig {at, count, height px, spread deg}; grass {at, count, height px};
lily {at [[px, py]...], size px}."""
import json
import math
import os
import zlib

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'textures')
REGIONS = json.load(open(os.path.join(TEX, 'plants_regions.json')))
KEEP = (1.0, 0.6, 0.3, 0.12)                     # share of cards per LOD
GROW = (1.0, 1.2, 1.45, 1.9)                     # their size per LOD
SIDES = (6, 5, 4, 3)
_materials = {}


def materials():
    if not _materials:
        def image(name, colorspace):
            img = bpy.data.images.load(os.path.join(TEX, name), check_existing=True)
            img.colorspace_settings.name = colorspace
            return img
        for name, alpha in (('Bark', False), ('Plant', True)):
            m = bpy.data.materials.new(name); m.use_nodes = True
            nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            base = nt.nodes.new('ShaderNodeTexImage'); base.image = image('plants_basecolor.png', 'sRGB')
            nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
            if alpha:
                nt.links.new(base.outputs['Alpha'], bsdf.inputs['Alpha'])
            nm = nt.nodes.new('ShaderNodeNormalMap'); nmt = nt.nodes.new('ShaderNodeTexImage')
            nmt.image = image('plants_normal.png', 'Non-Color')
            nt.links.new(nmt.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
            mr = nt.nodes.new('ShaderNodeTexImage'); mr.image = image('plants_mr.png', 'Non-Color')
            sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
            nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
            nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
            if alpha:
                m['openyamm_wind'] = 0.01
                m['openyamm_translucency'] = 0.3
                m['openyamm_specular'] = 0.15
            _materials[name] = m
    return _materials


class Surface:
    """Front projection onto one LOD: sprite pixel -> point on the stone (or behind it when the ray misses)."""

    def __init__(self, obj, to_model):
        self.bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
        self.to_model = to_model
        co = np.array([v.co[:] for v in obj.data.vertices])
        self.ymin = float(co[:, 1].min()) - 1.0
        self.centre_y = float(co[:, 1].mean())

    def hit(self, px, py):
        x, z = self.to_model(px, py)
        loc, normal, *_ = self.bvh.ray_cast(Vector((x, self.ymin, max(z, 0.002))), Vector((0, 1, 0)), 100.0)
        if loc is not None:
            return loc, normal.normalized(), True
        # off the silhouette: the nearest hit toward the centre line, kept at the sprite's x and z
        for k in range(1, 40):
            loc, normal, *_ = self.bvh.ray_cast(Vector((x * (1 - k * 0.025), self.ymin, max(z, 0.002) * (1 - k * 0.01))),
                                                Vector((0, 1, 0)), 100.0)
            if loc is not None:
                break
        # past the silhouette edge, which lies about the rock's mid depth: hang there, facing sideways
        return Vector((x, self.centre_y, z)), Vector((1.0 if x > 0 else -1.0, 0, 0)), False

    def scale(self):
        (x0, _), (x1, _) = self.to_model(0, 0), self.to_model(100, 0)
        return (x1 - x0) / 100                   # metres per sprite pixel


def region_uv(name, index):
    r = REGIONS[name][index % len(REGIONS[name])]
    return r


def card(bm, uvl, centre, right, up, width, height, rect, anchor=0.5):
    """Quad with its texture rectangle; anchor 0 puts its bottom edge at centre (stems), 0.5 its middle."""
    u0, v0, u1, v1 = rect
    b = centre - up * height * anchor
    vs = [bm.verts.new(b - right * width / 2), bm.verts.new(b + right * width / 2),
          bm.verts.new(b + right * width / 2 + up * height), bm.verts.new(b - right * width / 2 + up * height)]
    f = bm.faces.new(vs)
    for loop, uv in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        loop[uvl].uv = uv
    return f


def frame(normal, rng, tilt=0.6):
    """Right/up axes of a card lying on a surface with this outward normal, turned at random."""
    n = (normal + Vector(rng.normal(size=3)) * 0.25 * tilt).normalized()
    up = Vector((0, 0, 1)) - n * n.z
    up = up.normalized() if up.length > 1e-3 else Vector((0, 1, 0))
    up = (Matrix.Rotation(rng.uniform(-0.7, 0.7), 3, n) @ up).normalized()
    return n.cross(up).normalized() * -1, up, n


def smooth_path(points, samples):
    """Catmull-Rom through the points, `samples` per span."""
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(samples):
            t = k / samples
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(points[-1])
    return out


def vine(bm, uvl, surf, item, level):
    s = surf.scale()
    r0, r1 = (r * s for r in item['radius'])
    raw = []
    for px, py in item['path']:
        loc, normal, on = surf.hit(px, py)
        raw.append(loc + normal * (r0 * 0.9))   # rests on the stone
    samples = (4, 3, 2, 1)[level]
    path = smooth_path(raw, samples)
    sides = SIDES[level]
    bark = REGIONS[item.get('kind', 'bark')][0]
    rng = np.random.default_rng(zlib.crc32(json.dumps(item['path']).encode()))
    lump = [rng.uniform(0.75, 1.3) for _ in range(len(path))]        # gnarled: knotty thickness along the vine
    u0, u1 = bark[0] + 0.004, bark[2] - 0.004
    length = 0.0; rings = []
    for i, p in enumerate(path):
        t = i / (len(path) - 1)
        tangent = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = tangent.cross(Vector((0, -1, 0)))
        if side.length < 1e-3:
            side = tangent.cross(Vector((1, 0, 0)))
        side.normalize(); other = tangent.cross(side).normalized()
        r = (r0 + (r1 - r0) * t) * (lump[i] if 0 < i < len(path) - 1 else 1.0)
        if i:
            length += (p - path[i - 1]).length
        # meander a little sideways and twist the bark round the vine
        p = p + side * r * 0.6 * math.sin(i * 1.7 + len(path)) * (0 < i < len(path) - 1)
        twist = i * 0.9
        ring = []
        for k in range(sides + 1):
            a = 2 * math.pi * k / sides + twist
            ring.append((bm.verts.new(p + (side * math.cos(a) + other * math.sin(a)) * r), u0 + (u1 - u0) * k / sides,
                         length / (2 * math.pi * r0 * 1.5)))
        rings.append(ring)
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(sides):
            f = bm.faces.new((a_ring[k][0], a_ring[k + 1][0], b_ring[k + 1][0], b_ring[k][0]))
            for loop, (_, uu, vv) in zip(f.loops, (a_ring[k], a_ring[k + 1], b_ring[k + 1], b_ring[k])):
                loop[uvl].uv = (uu, vv)
    # cap the tip
    tip = rings[-1]
    c = bm.verts.new(path[-1] + (path[-1] - path[-2]).normalized() * r1)
    for k in range(sides):
        f = bm.faces.new((tip[k][0], tip[k + 1][0], c))
        for loop, uv in zip(f.loops, ((tip[k][1], tip[k][2]), (tip[k + 1][1], tip[k][2]), ((u0 + u1) / 2, tip[k][2] + 0.02))):
            loop[uvl].uv = uv


def leaves(bm, uvl, surf, item, level, rng):
    s = surf.scale()
    px0, py0, px1, py1 = item['box']
    n = item['count']
    for i in range(n):
        x, y = rng.uniform(px0, px1), rng.uniform(py0, py1)
        keep = rng.uniform() < KEEP[level]
        size = item['size'] * s * rng.uniform(0.75, 1.2) * GROW[level]
        if not keep:
            continue
        loc, normal, _ = surf.hit(x, y)
        right, up, nrm = frame(normal, rng)
        centre = loc + nrm * (size * rng.uniform(0.12, 0.35))
        card(bm, uvl, centre, right, up, size, size, region_uv(item['kind'], i))


def sprig(bm, uvl, surf, item, level, rng):
    s = surf.scale()
    loc, normal, _ = surf.hit(*item['at'])
    base = loc + normal * 0.01
    base.z = max(base.z, 0.0)
    count = max(1, round(item['count'] * KEEP[min(level, 2)] + 0.4)) if level < 3 else 1
    rect = REGIONS['sprig'][0]
    for i in range(count):
        h = item['height'] * s * rng.uniform(0.6, 1.0) * (1.15 if level else 1.0)
        yaw = rng.uniform(0, 2 * math.pi); tilt = math.radians(item.get('spread', 30)) * rng.uniform(0.3, 1.0)
        d = Vector((math.cos(yaw), math.sin(yaw), 0))
        up = (Vector((0, 0, 1)) * math.cos(tilt) + d * math.sin(tilt)).normalized()
        if up.y > 0.2:                           # lean away from the stone (toward the front)
            up.y = -up.y
        right = up.cross(Vector((0, -1, 0)) if abs(up.y) < 0.9 else Vector((1, 0, 0))).normalized()
        right = Matrix.Rotation(rng.uniform(-0.6, 0.6), 3, up) @ right
        card(bm, uvl, base, right, up, h / 4, h, rect, anchor=0.0)


def grass(bm, uvl, surf, item, level, rng):
    if level > 1:
        return
    s = surf.scale()
    loc, normal, _ = surf.hit(*item['at'])
    base = loc + normal * 0.02; base.z = 0.0
    rect = REGIONS['grass'][0]
    for i in range(item['count']):
        h = item['height'] * s * rng.uniform(0.7, 1.1)
        a = rng.uniform(0, math.pi)
        right = Vector((math.cos(a), math.sin(a), 0))
        card(bm, uvl, base + Vector((rng.uniform(-1, 1), rng.uniform(-1, 0), 0)) * h * 0.3, right, Vector((0, 0, 1)),
             h, h, rect, anchor=0.0)


def lily(bm, uvl, surf, item, level, rng):
    s = surf.scale()
    rect = REGIONS['lily'][0]
    for i, at in enumerate(item['at']):
        if level >= 2 and i % 2:
            continue
        if level == 3:
            continue
        loc, normal, _ = surf.hit(*at)
        size = item['size'] * s * rng.uniform(0.85, 1.15) * GROW[level]
        base = Vector((loc.x, loc.y - size * 0.35, 0.0))
        # the flower card leans toward the viewer; the card's lower half holds its leaves
        up = Vector((0, -0.3, 1)).normalized(); right = Vector((1, 0, 0))
        right = Matrix.Rotation(rng.uniform(-0.3, 0.3), 3, Vector((0, -1, 0))) @ right
        card(bm, uvl, base, right, up, size, size, rect, anchor=0.0)


def add(obj, level, cfg, to_model, units):
    mats = materials()
    surf = Surface(obj, to_model)
    rng = np.random.default_rng(65 + level)
    for name in ('Bark', 'Plant'):
        obj.data.materials.append(mats[name])
    index = {m.name: i for i, m in enumerate(obj.data.materials)}
    for kind, mat in (('wood', 'Bark'), ('cards', 'Plant')):
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        for item in cfg['plants']:
            r = np.random.default_rng(zlib.crc32(json.dumps(item, sort_keys=True).encode()) + level)
            if kind == 'wood' and item['type'] == 'vine':
                vine(bm, uvl, surf, item, level)
            elif kind == 'cards' and item['type'] != 'vine':
                {'leaves': leaves, 'sprig': sprig, 'grass': grass, 'lily': lily}[item['type']](bm, uvl, surf, item, level, r)
        if not bm.faces:
            bm.free(); continue
        for v in bm.verts:                       # nothing below the ground plane
            v.co.z = max(v.co.z, 0.0)
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        for f in bm.faces:
            f.material_index = index[mat]; f.smooth = kind == 'wood'
        me = bpy.data.meshes.new('plants')
        for m in obj.data.materials:             # slots first: to_mesh keeps only valid material indices
            me.materials.append(m)
        bm.to_mesh(me); bm.free()
        part = bpy.data.objects.new('plants', me); bpy.context.scene.collection.objects.link(part)
        bpy.ops.object.select_all(action='DESELECT'); part.select_set(True); obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
    print('BUILD plants', obj.name, 'level', level, 'tris', sum(len(p.vertices) - 2 for p in obj.data.polygons))
