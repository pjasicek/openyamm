"""Shared builders of the hanging batch (cages, chandelier): the dungeon helpers (../../scripts/dungeon_lib.py, read
only) plus textures from this batch's textures/ first, swept tubes, chain links, a procedural skull and a posed
skeleton, cage rings, and the COLOR_0 tint toward measured native colours. All sizes are given in map units (the
native sprite's world units) and converted with units()."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import dungeon_lib as dl  # noqa: E402

pl = dl.pl
u = dl.units
TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')


def material(name, texture, alpha=False, extras=None):
    """Material from this batch's textures/<texture>_basecolor.png when present, else the dungeon/props textures."""
    if os.path.exists(os.path.join(TEXTURES, f'{texture}_basecolor.png')):
        pl.TEX = TEXTURES
        try:
            m = pl.material(name, texture, alpha=alpha, extras=extras)
        finally:
            pl.TEX = dl.PROPS_TEXTURES
    else:
        m = dl.material(name, texture, alpha=alpha, extras=extras)
    return m


def apply(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


# ---------------------------------------------------------------- swept tubes
def _frames(points, closed, up=None):
    """Tangent and a normal per point: a fixed normal for planar loops (up), else parallel transport."""
    n = len(points)
    tangents = []
    for i in range(n):
        if closed:
            t = points[(i + 1) % n] - points[i - 1]
        else:
            t = points[min(i + 1, n - 1)] - points[max(i - 1, 0)]
        tangents.append(t.normalized())
    normals = []
    if up is not None:
        for t in tangents:
            normals.append((Vector(up) - t * t.dot(Vector(up))).normalized())
        return tangents, normals
    normal = tangents[0].orthogonal().normalized()
    for i, t in enumerate(tangents):
        if i:
            axis = tangents[i - 1].cross(t)
            if axis.length > 1e-8:
                angle = math.asin(min(1.0, axis.length))
                normal = Matrix.Rotation(angle, 3, axis.normalized()) @ normal
        normal = (normal - t * t.dot(normal)).normalized()
        normals.append(normal)
    return tangents, normals


def sweep(name, points, radii, sides, mat, closed=False, caps=True, up=None, v_scale=6.0, flat=1.0, phase=0.0):
    """Tube along points (map units) with a radius per point (or one radius); flat < 1 squashes the section along
    the normal (a strap). u around the section, v along the path."""
    points = [Vector(p) * (1 / dl.UNITS_PER_METRE) for p in points]
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * len(points)
    radii = [u(r) for r in radii]
    tangents, normals = _frames(points, closed, up)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    rings = []
    for p, t, nrm, r in zip(points, tangents, normals, radii):
        binormal = t.cross(nrm)
        ring = []
        for s in range(sides):
            a = 2 * math.pi * s / sides + phase
            ring.append(bm.verts.new(p + (nrm * math.cos(a) * flat + binormal * math.sin(a)) * r))
        rings.append(ring)
    lengths = [0.0]
    for a, b in zip(points, points[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    if closed:
        lengths.append(lengths[-1] + (points[0] - points[-1]).length)
    segments = len(points) if closed else len(points) - 1
    for i in range(segments):
        j = (i + 1) % len(points)
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[j][s2], rings[j][s]))
            for loop, (uu, vv) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (uu / sides, lengths[vv] * v_scale)
    if caps and not closed:
        for ring in (rings[0], rings[-1]):
            f = bm.faces.new(ring)
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, True)


def bone(name, a, b, radius, sides, mat, knob=1.6, rings=4):
    """A long bone from a to b: knobbed ends (knob x radius) and a slimmer shaft."""
    a, b = Vector(a), Vector(b)
    if rings == 2:
        return sweep(name, [a, b], [radius * knob * 0.8, radius * knob * 0.8], sides, mat, caps=False, v_scale=4.0)
    ts = (0.0, 0.12, 0.88, 1.0) if rings == 4 else (0.0, 0.15, 0.5, 0.85, 1.0)
    rs = [radius * knob, radius, radius, radius * knob] if rings == 4 else \
        [radius * knob, radius, radius * 0.9, radius, radius * knob]
    return sweep(name, [a.lerp(b, t) for t in ts], rs, sides, mat, v_scale=4.0)


def bezier(p0, p1, p2, count):
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    return [p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t
            for t in (i / (count - 1) for i in range(count))]


# ---------------------------------------------------------------- chain
def link(name, centre, length, width, wire, plane, path, sides, mat):
    """One oval chain link (outer length x width, wire radius) standing vertically in the xz (plane 'x') or yz
    plane, as a closed stadium sweep of `path` points."""
    r = width / 2 - wire
    straight = max(0.0, length / 2 - width / 2)
    pts = []
    per_end = max(2, path // 2)
    for end, sign in ((0, 1), (1, -1)):
        for k in range(per_end):
            a = math.pi * k / (per_end - 1) if per_end > 1 else 0.0
            # end 0: the top arc from +across to -across; end 1: the bottom arc back.
            across = math.cos(a) * r * (1 if end == 0 else -1)
            up = sign * (straight + math.sin(a) * r)
            pts.append((across, up))
    cx, cy, cz = centre
    points = [(cx + a, cy, cz + v) if plane == 'x' else (cx, cy + a, cz + v) for a, v in pts]
    normal = (0, 1, 0) if plane == 'x' else (1, 0, 0)
    return sweep(name, points, wire, sides, mat, closed=True, up=normal, v_scale=8.0)


def chain(name, bottom, top, length, width, wire, path, sides, mat, start_plane='x'):
    """Links hanging from top (the topmost link's outer end exactly at top) down to about bottom (map units)."""
    pitch = length - 4 * wire
    count = max(1, int(math.ceil((top - bottom - length) / pitch)) + 1)
    parts = []
    for k in range(count):
        cz = top - length / 2 - k * pitch
        plane = start_plane if k % 2 == 0 else ('y' if start_plane == 'x' else 'x')
        parts.append(link(f'{name}{k}', (0, 0, cz), length, width, wire, plane, path, sides, mat))
    return parts, top - length / 2 - (count - 1) * pitch - length / 2


# ---------------------------------------------------------------- rings and plates
def ring(name, r_in, r_out, z0, z1, segments, mat, u_repeat=4.0):
    """A flat band (rectangular section) about the vertical axis: bottom, outer, top and inner faces."""
    return pl.lathe(name, [(u(r_in), u(z0)), (u(r_out), u(z0)), (u(r_out), u(z1)), (u(r_in), u(z1)),
                           (u(r_in), u(z0))], segments, mat, u_repeat=u_repeat, v_scale=6.0, smooth=False)


def disc(name, radius, z0, z1, segments, mat):
    """A closed slab (cage floor)."""
    return pl.lathe(name, [(0.0, u(z0)), (u(radius), u(z0)), (u(radius), u(z1)), (0.0, u(z1))], segments, mat,
                    u_repeat=2.0, v_scale=6.0, smooth=False)


def rivet(name, position, outward, size, mat):
    """A four-sided pyramid head on a surface (no base), pointing along outward."""
    p = Vector(position) * (1 / dl.UNITS_PER_METRE); n = Vector(outward).normalized()
    side = n.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize(); upv = side.cross(n)
    s = u(size)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    tip = bm.verts.new(p + n * s * 0.8)
    base = [bm.verts.new(p + (side * math.cos(a) + upv * math.sin(a)) * s)
            for a in (k * math.pi / 2 + math.pi / 4 for k in range(4))]
    for k in range(4):
        f = bm.faces.new((base[k], base[(k + 1) % 4], tip))
        for loop, c in zip(f.loops, ((0, 0), (1, 0), (0.5, 1))):
            loop[uv].uv = c
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, False)


# ---------------------------------------------------------------- skull and skeleton
# The skull follows the skull pile's construction (../../../mm6_new_sorpigal_3d/props/scripts/build_skullpile.py,
# same project): a deformed sphere whose grid nodes sit on the painted features of the non-tiling `skull` texture
# (u around, front at u = 0.5, v bottom to top), with the sockets and nose pushed in.
U_NODES = ([0, 0.2, 0.33, 0.418, 0.5, 0.582, 0.67, 0.8, 1.0],
           [0, 0.25, 0.418, 0.5, 0.582, 0.75, 1.0],
           [0, 0.33, 0.5, 0.67, 1.0])
V_NODES = ([0, 0.2, 0.33, 0.43, 0.585, 0.72, 1.0],
           [0, 0.35, 0.585, 0.8, 1.0],
           [0, 0.45, 0.8, 1.0])
FEATURES = [(0.418, 0.585, 0.065, 0.10, -0.15), (0.582, 0.585, 0.065, 0.10, -0.15),
            (0.5, 0.43, 0.05, 0.10, -0.10), (0.5, 0.675, 0.17, 0.05, 0.035),
            (0.375, 0.45, 0.05, 0.07, 0.045), (0.625, 0.45, 0.05, 0.07, 0.045)]


def skull(name, level, centre, size, rotation, mat):
    """Skull of length size (map units) at centre, front toward -y before rotation (Euler degrees)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    grid = []
    for v in V_NODES[level]:
        phi = math.pi * (1 - v)
        row = []
        for uu in U_NODES[level]:
            theta = 2 * math.pi * uu
            d = Vector((math.sin(phi) * math.sin(theta), -math.cos(theta) * math.sin(phi), math.cos(phi)))
            p = Vector((d.x * 0.36, d.y * 0.48, d.z * 0.40))
            front = max(d.y, 0.0)
            if p.z < 0:
                p.z *= 1 + 0.45 * front
                p.x *= 1 - 0.3 * front * min(-d.z / 0.6, 1.0)
            for cu, cv, ru, rv, offset in FEATURES:
                w = 1 - ((uu - cu) / ru) ** 2 - ((v - cv) / rv) ** 2
                if w > 0:
                    p += d * offset * w ** 0.7
            row.append((bm.verts.new(p), uu, v))
        grid.append(row)
    for lower, upper in zip(grid, grid[1:]):
        for j in range(len(lower) - 1):
            quad = (lower[j], lower[j + 1], upper[j + 1], upper[j])
            f = bm.faces.new([q[0] for q in quad])
            for loop, (_, uu, v) in zip(f.loops, quad):
                loop[uv].uv = (uu, v)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # Face toward -y (the cage front): the unit skull faces +y.
    turn = Matrix.Rotation(math.pi, 4, 'Z')
    rot = Euler([math.radians(a) for a in rotation], 'XYZ').to_matrix().to_4x4()
    transform = Matrix.Translation(Vector(centre) * (1 / dl.UNITS_PER_METRE)) @ rot @ turn @ \
        Matrix.Scale(u(size), 4)
    bmesh.ops.transform(bm, matrix=transform, verts=bm.verts)
    return pl.to_object(name, bm, mat, True)


def ribcage(name, level, spine_top, spine_bottom, width, depth, mat, forward=(0, -1, 0)):
    """Ribs curving forward from the spine (spine_top to spine_bottom, map units) around a cage of the given
    half-width and depth, plus a sternum. forward: the chest direction (unit, horizontal-ish)."""
    pairs = (6, 4, 0)[level]
    if pairs == 0:
        return []
    top, bottom = Vector(spine_top), Vector(spine_bottom)
    fwd = Vector(forward).normalized()
    axis = (top - bottom).normalized()
    side = fwd.cross(axis).normalized()
    fwd = axis.cross(side).normalized()
    parts = []
    for k in range(pairs):
        t = (k + 0.5) / pairs * 0.62
        base = top.lerp(bottom, t)
        w = width * (0.72 + 0.28 * math.sin(math.pi * min(1.0, t / 0.62 * 0.85 + 0.15)))
        for sign in (1, -1):
            pts = []
            steps = (6, 4)[level]
            for s in range(steps):
                a = 0.15 + (math.pi - 0.55) * s / (steps - 1)
                droop = -axis * (depth * 0.25 * s / (steps - 1))
                pts.append(base + side * (sign * w * math.sin(a)) + fwd * (depth / 2 * (1 - math.cos(a)) * 0.95)
                           + droop)
            parts.append(sweep(f'{name}{k}{sign}', pts, 1.7, 3, mat, caps=False, v_scale=4.0))
    sternum_top = top.lerp(bottom, 0.08) + fwd * depth * 0.93
    sternum_bottom = top.lerp(bottom, 0.55) + fwd * depth * 0.88 - axis * depth * 0.2
    parts.append(sweep(f'{name}St', [sternum_top, sternum_bottom], 2.4, 4, mat, v_scale=4.0, flat=0.5))
    return parts


def pelvis(name, level, centre, width, mat, rotation=(0, 0, 0)):
    """A squashed open bowl (the hip bones) about the vertical axis at centre."""
    w = width
    obj = pl.lathe(name, [(u(w * 0.16), u(-w * 0.28)), (u(w * 0.3), u(-w * 0.12)), (u(w * 0.5), u(w * 0.12)),
                          (u(w * 0.56), u(w * 0.2))], (8, 6, 5)[level], mat, u_repeat=1.0, v_scale=4.0)
    obj.scale = (1.0, 0.42, 1.0)
    obj.rotation_euler = [math.radians(a) for a in rotation]
    obj.location = Vector(centre) * (1 / dl.UNITS_PER_METRE)
    return apply(obj)


def skeleton(name, level, joints, mats, skull_rotation, skull_size=27.0, chest_forward=(0, -1, 0)):
    """A posed skeleton from joint positions (map units): head, neck, chest (ribcage bottom on the spine), hips
    (pelvis centre), shoulder_l/r, elbow_l/r, hand_l/r, hip_l/r, knee_l/r, foot_l/r, toe_l/r."""
    j = {k: Vector(v) for k, v in joints.items()}
    if level == 3:
        # The farthest level: skull, trunk and four straight limbs.
        parts = [skull(f'{name}Skull', 2, j['head'], skull_size, skull_rotation, mats['Skull']),
                 sweep(f'{name}Trunk', [j['neck'], j['chest'], j['hips']], [8.0, 8.0, 6.0], 3, mats['Bone'],
                       caps=False, v_scale=4.0, flat=0.7)]
        for side in ('l', 'r'):
            parts.append(sweep(f'{name}Arm{side}', [j[f'shoulder_{side}'], j[f'elbow_{side}'], j[f'hand_{side}']],
                               3.0, 3, mats['Bone'], caps=False, v_scale=4.0))
            parts.append(sweep(f'{name}Leg{side}', [j[f'hip_{side}'], j[f'knee_{side}'], j[f'foot_{side}']],
                               3.8, 3, mats['Bone'], caps=False, v_scale=4.0))
        return parts
    sides = (5, 4, 3)[level]
    rings = (4, 2, 2)[level]
    parts = [skull(f'{name}Skull', level, j['head'], skull_size, skull_rotation, mats['Skull'])]
    spine = [j['neck'], j['neck'].lerp(j['chest'], 0.5), j['chest'], j['chest'].lerp(j['hips'], 0.5), j['hips']]
    if level == 2:
        spine = [j['neck'], j['hips']]
    parts.append(sweep(f'{name}Spine', spine, 2.8, (5, 4, 3)[level], mats['Bone'], v_scale=4.0))
    reach = j['chest'] - j['neck']
    parts += ribcage(f'{name}Rib', level, j['neck'] + reach * 0.05, j['chest'] + reach * 0.25, 19.0, 20.0,
                     mats['Bone'], chest_forward)
    if level == 2:
        parts.append(sweep(f'{name}Chest', [j['neck'].lerp(j['chest'], 0.1), j['chest']], [9.0, 8.0], 4,
                           mats['Bone'], v_scale=4.0, flat=0.7))
    parts.append(pelvis(f'{name}Pelvis', level, j['hips'], 30.0, mats['Bone'], joints.get('pelvis_rotation',
                                                                                            (0, 0, 0))))
    parts.append(bone(f'{name}Clavicle', j['shoulder_l'], j['shoulder_r'], 2.0, max(3, sides - 1), mats['Bone'],
                      knob=1.3, rings=rings))
    limbs = [('shoulder', 'elbow', 3.0), ('elbow', 'hand', 2.5), ('hip', 'knee', 3.8), ('knee', 'foot', 3.2)]
    for side in ('l', 'r'):
        for a, b, r in limbs:
            parts.append(bone(f'{name}{a}{side}', j[f'{a}_{side}'], j[f'{b}_{side}'], r, sides, mats['Bone'],
                              rings=rings))
        if level < 2:
            parts.append(sweep(f'{name}Foot{side}', [j[f'foot_{side}'], j[f'toe_{side}']], [3.6, 2.4], 4,
                               mats['Bone'], v_scale=4.0, flat=0.5))
            hand_end = j[f'hand_{side}'] + (j[f'hand_{side}'] - j[f'elbow_{side}']).normalized() * 7.0
            parts.append(sweep(f'{name}Hand{side}', [j[f'hand_{side}'], hand_end], [3.0, 2.0], 4, mats['Bone'],
                               v_scale=4.0, flat=0.5))
    return parts


# ---------------------------------------------------------------- colour
def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


_means = {}


def texture_mean(mat):
    """Mean sRGB (0..255) of the material's base colour image."""
    key = mat.name
    if key not in _means:
        tex = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE')
        img = tex.image
        pixels = np.empty(len(img.pixels), np.float32); img.pixels.foreach_get(pixels)
        pixels = pixels.reshape(-1, 4)
        alpha = pixels[:, 3] > 0.5
        _means[key] = pixels[alpha, :3].mean(0) * 255.0
    return _means[key]


def tag(objects, target):
    """Mark objects' vertices with their native target colour (sRGB 0..255) for tint()."""
    for obj in objects:
        me = obj.data
        attr = me.attributes.new('Target', 'FLOAT_COLOR', 'POINT')
        values = np.tile(np.array([target[0] / 255, target[1] / 255, target[2] / 255, 1.0], np.float32),
                         len(me.vertices))
        attr.data.foreach_set('color', values)
    return objects


def tint(obj, report='', soften=None):
    """COLOR_0 = occlusion x tint, tint = linear(native) / linear(texture mean) / mean occlusion of that group (the
    vertices sharing a target colour), so each group's displayed mean matches its native colour. soften: {material
    name: fraction of the occlusion kept}, for near-white materials whose tint would otherwise pass one (COLOR_0 is
    stored normalised and clamps there)."""
    me = obj.data
    colour = me.color_attributes['Color']
    target = me.attributes['Target']
    occ = np.empty(len(me.vertices) * 4, np.float32); colour.data.foreach_get('color', occ); occ = occ.reshape(-1, 4)
    tgt = np.empty(len(me.vertices) * 4, np.float32); target.data.foreach_get('color', tgt); tgt = tgt.reshape(-1, 4)
    materials = np.zeros(len(me.vertices), int)
    for polygon in me.polygons:
        for index in polygon.vertices:
            materials[index] = polygon.material_index
    keys = {}
    for index in range(len(me.vertices)):
        keys.setdefault((materials[index], tuple(np.round(tgt[index, :3] * 255).astype(int))), []).append(index)
    for (slot, native), indices in keys.items():
        mat = me.materials[slot]
        mean = texture_mean(mat)
        keep = (soften or {}).get(mat.name)
        if keep is not None:
            occ[indices, :3] = 1.0 - (1.0 - occ[indices, :3]) * keep
        occlusion = float(occ[indices, 0].mean())
        factor = np.array([srgb_to_linear(n) / srgb_to_linear(m) for n, m in zip(native, mean)]) / occlusion
        occ[indices, :3] *= factor
        clipped = float((occ[indices, :3] > 1.0).mean())
        if report:
            print('TINT', report, mat.name, native, 'texture', np.round(mean).astype(int).tolist(), 'occlusion',
                  round(occlusion, 3), 'factor', np.round(factor, 3).tolist(), 'clipped', round(clipped, 3))
    colour.data.foreach_set('color', occ.ravel())
    me.attributes.remove(me.attributes['Target'])
    me.color_attributes.active_color = me.color_attributes['Color']
    me.color_attributes.render_color_index = me.color_attributes.active_color_index
