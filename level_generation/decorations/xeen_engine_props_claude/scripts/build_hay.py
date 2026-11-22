"""`haybale2` "Hay" (MM7 engine decoration, placed by the Xeen towns' farms): a loose domed haystack, wider than tall,
traced from the x2 sprite (220 x 188 world units: steep, slightly bulging sides over the lower half, then a rounded
dome). Body: the upper half of a cube-sphere (no poles, no fans) mapped onto the measured profile by elevation and
lumped with noise; texture `hay` (tileable straw), cylindrical on the sides and planar on the top (seam ring at 62 %
of the profile, where the straw texture hides it). Fringe: alpha-tested, double-sided straw tuft cards (`haystrand`,
own material Strands) splaying from the base, sticking out of the dome and bristling on top, so the silhouette reads
as loose straw. COLOR_0: vertex occlusion x darker damp patches (as the sprite's brown blotches) x an outdoor grade;
the cards take the colour of the nearest body vertex, lighter toward their tips.
Usage: blender --background --python build_hay.py -- [grade_r grade_g grade_b]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlib  # noqa: E402

pl, u = xlib.pl, xlib.u
PROP = 'haybale2'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
GRADE = [float(a) for a in args[:3]] if len(args) >= 3 else [1.0, 1.0, 1.0]

H = 178.0                      # dome height (map units); the top tufts add a little
RX, RY = 116.0, 106.0          # base radii
# measured on the x2 sprite: (height fraction, radius fraction)
PROFILE = [(0.0, 0.95), (0.06, 0.99), (0.2, 1.0), (0.36, 0.97), (0.49, 0.92), (0.57, 0.87), (0.66, 0.81),
           (0.74, 0.75), (0.83, 0.66), (0.9, 0.53), (0.95, 0.37), (0.985, 0.18), (1.0, 0.0)]
TILE = 1.2                     # metres per hay texture repeat
S_CAP = 0.62                   # profile arc fraction where the planar top mapping starts
AROUND = 6                     # texture repeats around the sides
# per level: cube-sphere segments (even), card counts (skirt, body, top), occlusion rays
LEVELS = [(16, (30, 70, 10), 48), (10, (18, 30, 6), 24), (6, (10, 0, 4), 12), (4, (0, 0, 0), 8)]


def profile_by_arc():
    """(arc fraction, r fraction, z fraction) samples of PROFILE, by arc length in real proportions."""
    pts = [(r * (RX + RY) / 2, h * H) for h, r in PROFILE]
    arc = [0.0]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        arc.append(arc[-1] + math.hypot(r1 - r0, z1 - z0))
    total = arc[-1]
    return [a / total for a in arc], total


ARC, ARC_TOTAL = profile_by_arc()


def at_arc(s):
    s = min(max(s, 0.0), 1.0)
    for i in range(len(ARC) - 1):
        if s <= ARC[i + 1]:
            t = (s - ARC[i]) / max(ARC[i + 1] - ARC[i], 1e-9)
            h = PROFILE[i][0] * (1 - t) + PROFILE[i + 1][0] * t
            r = PROFILE[i][1] * (1 - t) + PROFILE[i + 1][1] * t
            return r, h
    return 0.0, 1.0


def body(name, segments, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=segments - 1, use_grid_fill=True)
    # equal-area cube-to-sphere mapping, then drop the lower half (rows at z = 0 exist: segments is even)
    for v in bm.verts:
        x, y, z = v.co
        v.co = Vector((x * math.sqrt(max(0, 1 - y * y / 2 - z * z / 2 + y * y * z * z / 3)),
                       y * math.sqrt(max(0, 1 - z * z / 2 - x * x / 2 + z * z * x * x / 3)),
                       z * math.sqrt(max(0, 1 - x * x / 2 - y * y / 2 + x * x * y * y / 3))))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z < -1e-4], context='FACES')
    arc_of = {}
    for v in bm.verts:
        d = v.co.normalized()
        e = math.asin(max(-1.0, min(1.0, d.z)))
        s = max(0.0, e / (math.pi / 2))
        arc_of[v] = s
        r, h = at_arc(s)
        flat = Vector((d.x, d.y, 0.0))
        flat = flat.normalized() if flat.length > 1e-6 else Vector((0, 0, 0))
        p = Vector((flat.x * r * RX, flat.y * r * RY, h * H))
        # lumps: low and mid frequency, along the direction from the dome's core; the base ring stays on the ground
        out = (p - Vector((0, 0, 0.3 * H))).normalized()
        amount = 0.06 * RX * xlib.fbm(p, 3, 70.0, 1.7) + 0.025 * RX * xlib.fbm(p, 2, 24.0, 5.3)
        q = p + out * amount
        if s < 1e-4:
            q.z = 0.0
        q.z = max(q.z, 0.0)
        v.co = Vector((u(q.x), u(q.y), u(q.z)))
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        s_face = sum(arc_of[v] for v in f.verts) / len(f.verts)
        if s_face >= S_CAP:
            for loop in f.loops:
                loop[uv].uv = (loop.vert.co.x / TILE, loop.vert.co.y / TILE)
        else:
            us = []
            for loop in f.loops:
                a = math.atan2(loop.vert.co.y, loop.vert.co.x) / (2 * math.pi) % 1.0
                us.append(a * AROUND)
            if max(us) - min(us) > AROUND / 2:
                us = [x + AROUND if x < AROUND / 2 else x for x in us]
            for loop, uu in zip(f.loops, us):
                loop[uv].uv = (uu, arc_of[loop.vert] * u(ARC_TOTAL) / TILE)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    obj = pl.to_object(name, bm, mat, True)
    return obj, arc_of


def card(bm, uv, root, grow, side, width, height, quadrant):
    """A straw tuft quad: bottom edge centred on root along side, rising along grow (map units)."""
    root, grow, side = Vector(root), Vector(grow).normalized(), Vector(side).normalized()
    a = root - side * width / 2; b = root + side * width / 2
    c = b + grow * height; d = a + grow * height
    verts = [bm.verts.new(Vector((u(p.x), u(p.y), u(max(p.z, 0.3))))) for p in (a, b, c, d)]
    f = bm.faces.new(verts)
    qx, qy = quadrant % 2, quadrant // 2
    u0, u1 = qx * 0.5 + 0.01, qx * 0.5 + 0.49
    v0 = 0.5 * (1 - qy) + 0.004
    v1 = v0 + 0.49
    for loop, t in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        loop[uv].uv = t
    return f


def cards(name, body_obj, counts, mat, rng):
    """Fringe cards on body_obj's surface: skirt at the base, body cards, top tufts."""
    me = body_obj.data
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    tris = [(Vector(me.vertices[p.vertices[0]].co), Vector(me.vertices[p.vertices[1]].co),
             Vector(me.vertices[p.vertices[2]].co), Vector(p.normal)) for p in me.polygons]
    areas = np.array([((b - a).cross(c - a)).length / 2 for a, b, c, _ in tris])
    upm = xlib.UNITS_PER_METRE

    def sample(zmin, zmax):
        for _ in range(200):
            i = rng.choice(len(tris), p=areas / areas.sum())
            a, b, c, n = tris[i]
            r1, r2 = rng.uniform(0, 1, 2)
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            p = (a + (b - a) * r1 + (c - a) * r2) * upm
            if zmin <= p.z / H <= zmax:
                return p, n
        return p, n

    skirt, middle, top = counts
    for k in range(skirt):
        ang = 2 * math.pi * (k + rng.uniform(-0.3, 0.3)) / max(skirt, 1)
        radial = Vector((math.cos(ang), math.sin(ang), 0))
        root = Vector((radial.x * RX * 0.9, radial.y * RY * 0.9, rng.uniform(1.0, 8.0)))
        grow = radial * rng.uniform(0.75, 1.0) + Vector((0, 0, rng.uniform(0.25, 0.6)))
        side = Vector((-radial.y, radial.x, 0)) + Vector(rng.normal(0, 0.15, 3))
        card(bm, uv, root, grow, side, rng.uniform(30, 42), rng.uniform(20, 28), int(rng.integers(0, 4)))
    for k in range(middle):
        p, n = sample(0.1, 0.9)
        tangent = Vector(rng.normal(0, 1, 3)); tangent -= n * tangent.dot(n); tangent.normalize()
        tilt = rng.uniform(0.45, 0.9)
        grow = n * math.sin(tilt) + tangent * math.cos(tilt)
        side = n.cross(grow)
        card(bm, uv, p - n * 1.5, grow, side, rng.uniform(22, 32), rng.uniform(16, 24), int(rng.integers(0, 4)))
    for k in range(top):
        p, n = sample(0.86, 1.0)
        tangent = Vector(rng.normal(0, 1, 3)); tangent -= n * tangent.dot(n); tangent.normalize()
        grow = n * 0.8 + tangent * 0.5 + Vector((0, 0, 0.3))
        side = Vector((0, 0, 1)).cross(grow) if abs(grow.normalized().z) < 0.95 else Vector((1, 0, 0))
        card(bm, uv, p - n * 1.5, grow, side, rng.uniform(20, 28), rng.uniform(13, 19), int(rng.integers(0, 4)))
    return pl.to_object(name, bm, mat, False)


def colour_body(obj, rays, seed):
    pl.vertex_occlusion(obj, rays=rays, distance=u(60), strength=0.55, floor=True)
    me = obj.data
    c = np.empty(len(me.vertices) * 4, np.float32); me.color_attributes['Color'].data.foreach_get('color', c)
    c = c.reshape(-1, 4)
    damp = np.array([0.50, 0.36, 0.24], np.float32)
    for i, v in enumerate(me.vertices):
        p = v.co * xlib.UNITS_PER_METRE
        t = xlib.fbm(p, 3, 45.0, seed + 11.0)
        patch = min(max((t + 0.05) / 0.3, 0.0), 1.0)
        c[i, :3] *= (1 - patch) + damp * patch
    c[:, :3] = np.clip(c[:, :3] * np.array(GRADE, np.float32), 0, 1)
    me.color_attributes['Color'].data.foreach_set('color', c.ravel())


def colour_cards(cards_obj, body_obj):
    bme = body_obj.data
    bc = np.empty(len(bme.vertices) * 4, np.float32); bme.color_attributes['Color'].data.foreach_get('color', bc)
    bc = bc.reshape(-1, 4)
    tree = KDTree(len(bme.vertices))
    for i, v in enumerate(bme.vertices):
        tree.insert(v.co, i)
    tree.balance()
    me = cards_obj.data
    colours = []
    for k, v in enumerate(me.vertices):
        _, i, _ = tree.find(v.co)
        tip = 1.12 if k % 4 >= 2 else 0.95
        colours.append(np.clip(np.concatenate([bc[i, :3] * tip, [1.0]]), 0, 1))
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.array(colours, np.float32).ravel())
    me.color_attributes.active_color = attr


pl.reset()
hay = xlib.material('Hay', 'hay', extras={'openyamm_specular': 0.15})
strands = xlib.material('Strands', 'haystrand', alpha=True, extras={'openyamm_specular': 0.1})
lods = []
for level, (segments, counts, rays) in enumerate(LEVELS):
    name = 'Base' if level == 0 else f'Base_LOD{level}'
    obj, _ = body(name, segments, hay)
    colour_body(obj, rays, 3.0)
    if sum(counts):
        fringe = cards(name + '_cards', obj, counts, strands, np.random.default_rng(91 + level))
        colour_cards(fringe, obj)
        obj = pl.join(name, [obj, fringe])
    lods.append(obj)
xlib.save(PROP, lods)
