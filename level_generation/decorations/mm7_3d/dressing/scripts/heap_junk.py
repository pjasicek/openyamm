"""`7dec10` (dungeon 7d29, 1 placement): a junk heap. A broad, flat-topped mound of streaky brown earth (256 x 230,
about 50 high with lumps, steep at its rim) carries the sprite's clutter: upright, tipped and fallen barrels, open
crates (plank frames with grey panels), bulbous iron pots with knobbed lids, round teal lids, red cloth sheets, bones
and a white jug, each laid out after the x2 sprite (seen from above: its 202-unit art includes the heap's depth) and
rested on the mound surface. Textures (Poly Haven, CC0): brown_mud_dry (mound), wooden_barrel (staves and hoops),
weathered_planks (crate frames, barrel ends), rock_boulder_dry (crate panels, jug), rusty_metal_05 (pots),
green_metal_rust (lids), dirty_carpet (cloth, recoloured red); props `bone`. COLOR_0 = vertex occlusion x a tint per
part group toward the sprite's region colours (hanging_lib.tint). LOD1 drops the smallest pieces, LOD2 keeps the
barrels, crates as blocks and the pots, LOD3 the mound and the large barrels.
Usage: blender --background --python heap_junk.py"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402
import heap_lib as hp  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u
PROP = '7dec10'
RX, RY = 128.0, 115.0
# Sprite region colours (sRGB; measured on the x2 sprite, small_measure.py, and sampled per region).
TARGET = {'mound': (24, 15, 7), 'barrel': (31, 21, 13), 'end': (25, 22, 20), 'frame': (28, 20, 13),
          'panel': (49, 39, 42), 'pot': (19, 17, 16), 'lid': (28, 34, 29), 'cloth': (44, 9, 6),
          'bone': (128, 119, 94), 'jug': (128, 119, 102)}


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def height(x, y):
    """Flat-topped mound, higher at the back, lumpy, falling steeply at its rounded-square rim."""
    rr = (abs(x / RX) ** 3 + abs(y / RY) ** 3) ** (1 / 3)
    top = 44 + 10 * smoothstep(-80, 80, y) + 7 * hp.fbm(x, y, scale=35, seed=2.0)
    return max(0.0, top * smoothstep(1.0, 0.7, rr))


PLACED = []        # world-space triangles (map units) of the items already placed at the current level
MAX_PILE = 46.0    # the clutter stays within this height above the mound (the sprite's pile is one layer deep)


def support(x0, x1, y0, y1):
    """Ground under a footprint: rays straight down at nine points of its inner half onto the mound and the items
    placed before it; the median hit, so an item leans into the pile rather than balancing on one high point."""
    from mathutils.bvhtree import BVHTree
    tree = None
    if PLACED:
        verts = [v for tri in PLACED for v in tri]
        tree = BVHTree.FromPolygons(verts, [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(PLACED))])
    hits = []
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for fx in (-0.25, 0.0, 0.25):
        for fy in (-0.25, 0.0, 0.25):
            x, y = cx + fx * (x1 - x0), cy + fy * (y1 - y0)
            z = height(x, y)
            if tree is not None:
                hit = tree.ray_cast(Vector((x, y, 500.0)), Vector((0, 0, -1)))
                if hit[0] is not None:
                    z = max(z, min(hit[0].z, height(x, y) + MAX_PILE))
            hits.append(z)
    return float(np.median(hits))


def transform(obj, rotation, position, sink=2.0):
    """Rotate (Euler degrees) about the origin, move to (x, y) and rest the lowest point on the mound or on the items
    placed before it, sink deep."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)          # closed pieces: outward
    bm.to_mesh(obj.data); bm.free()
    obj.rotation_euler = Euler([math.radians(a) for a in rotation], 'XYZ')
    dlib.apply(obj)
    x, y = position
    co = np.array([v.co[:] for v in obj.data.vertices]) * dlib.UNITS_PER_METRE
    lo, hi = co.min(0), co.max(0)
    base = support(x + lo[0], x + hi[0], y + lo[1], y + hi[1])
    obj.location = (u(x), u(y), u(base - sink - lo[2]))
    dlib.apply(obj)
    me = obj.data
    me.calc_loop_triangles()
    for tri in me.loop_triangles:
        PLACED.append([Vector(me.vertices[i].co) * dlib.UNITS_PER_METRE for i in tri.vertices])
    return obj


def barrel(name, level, mats, radius=15.0, length=40.0):
    """A bulged barrel along +z from 0 to length: staves (wooden_barrel, v once over the height, two repeats around)
    and plank ends set in by a short chime."""
    seg = (8, 6, 6, 5)[level]
    zs = [0, 0.18, 0.5, 0.82, 1.0] if level == 0 else [0, 0.5, 1.0]
    bulge = lambda t: radius * (0.86 + 0.14 * math.sin(math.pi * t))
    side = pl.lathe(name, [(u(bulge(t)), u(t * length)) for t in zs], seg, mats['barrel'], u_repeat=2.0,
                    v_scale=1.0 / u(length))
    parts = [side]
    for z, flip in ((0.0, True), (length, False)):
        r = bulge(0.0) * 0.95
        zz = z + (1.2 if flip else -1.2)
        cap = pl.lathe(name + 'cap', [(u(r), u(zz)), (0.0, u(zz))] if not flip else [(0.0, u(zz)), (u(r), u(zz))],
                       seg, mats['end'], smooth=False)
        rim = pl.lathe(name + 'rim', [(u(bulge(0.0)), u(z)), (u(r), u(zz))] if flip else
                       [(u(r), u(zz)), (u(bulge(1.0)), u(z))], seg, mats['barrel'], u_repeat=2.0, v_scale=1.0,
                       smooth=False)
        parts += [cap, rim]
    return parts


def crate(name, level, mats, size=(34, 30, 26)):
    """An open crate: four corner posts and the rim and base frames as plank beams, two grey side panels
    (LOD2+: a solid block)."""
    sx, sy, sz = size
    if level >= 1:
        return [pl.box(name, (0, 0, u(sz / 2)), (u(sx), u(sy), u(sz)), mats['panel'], uv_scale=3.0)]
    t = 3.0
    parts = []
    for cx in (-1, 1):
        for cy in (-1, 1):
            parts.append(pl.box(f'{name}p{cx}{cy}', (u(cx * (sx - t) / 2), u(cy * (sy - t) / 2), u(sz / 2)),
                                (u(t), u(t), u(sz)), mats['frame'], uv_scale=4.0))
    for z in (t / 2, sz - t / 2):
        for cy in (-1, 1):
            parts.append(pl.box(f'{name}bx{z}{cy}', (0, u(cy * (sy - t) / 2), u(z)), (u(sx), u(t), u(t)),
                                mats['frame'], uv_scale=4.0))
        for cx in (-1, 1):
            parts.append(pl.box(f'{name}by{z}{cx}', (u(cx * (sx - t) / 2), 0, u(z)), (u(t), u(sy), u(t)),
                                mats['frame'], uv_scale=4.0))
    # panels: floor and two adjacent sides (the open frame shows through the others)
    parts.append(pl.box(f'{name}floor', (0, 0, u(1.0)), (u(sx - 1), u(sy - 1), u(1.5)), mats['panel'], uv_scale=3.0))
    parts.append(pl.box(f'{name}sideA', (0, u(sy / 2 - 1), u(sz / 2)), (u(sx - 2), u(1.2), u(sz - 2)),
                        mats['panel'], uv_scale=3.0))
    parts.append(pl.box(f'{name}sideB', (u(-sx / 2 + 1), 0, u(sz / 2)), (u(1.2), u(sy - 2), u(sz - 2)),
                        mats['panel'], uv_scale=3.0))
    return parts


def pot(name, level, mats, r=13.0):
    """A bulbous iron pot with a short neck, a lid and a knob."""
    seg = (10, 6, 5, 5)[level]
    prof = [(0, 0), (r * 0.6, 0.5), (r * 0.95, r * 0.5), (r, r * 0.9), (r * 0.8, r * 1.4), (r * 0.45, r * 1.65),
            (r * 0.45, r * 1.8), (r * 0.5, r * 1.85), (r * 0.2, r * 1.95), (r * 0.15, r * 2.2), (0, r * 2.25)]
    if level >= 1:
        prof = [(0, 0), (r * 0.95, r * 0.5), (r * 0.8, r * 1.4), (r * 0.4, r * 1.8), (0, r * 2.2)]
    return [pl.lathe(name, [(u(a), u(b)) for a, b in prof], seg, mats['pot'], u_repeat=2.0, v_scale=3.0)]


def disc(name, level, mats, r=9.0, h=3.0):
    seg = (12, 8, 6, 6)[level]
    return [pl.lathe(name, [(0, 0), (u(r), 0), (u(r), u(h)), (u(r * 0.8), u(h * 1.4)), (0, u(h * 1.4))], seg,
                     mats['lid'], u_repeat=1.0, v_scale=3.0, smooth=False)]


def cloth(name, level, mats, w=30.0, h=34.0, seed=1.0):
    """A draped sheet: a grid bent over a ridge with noise folds, standing in the xz plane."""
    n = (5, 3, 2, 2)[level]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    verts = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            s, t = i / n, j / n
            x = (s - 0.5) * w
            z = t * h
            y = 6 * math.sin(math.pi * t) + 4 * hp.fbm(x, z, scale=12, seed=seed)
            row.append(bm.verts.new((u(x), u(y), u(z))))
        verts.append(row)
    for j in range(n):
        for i in range(n):
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uvl].uv = (a / n, b / n)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return [pl.to_object(name, bm, mats['cloth'], True)]


def bone_item(name, level, mats, length=20.0):
    return [hl.bone(name, (0, 0, 0), (length, 0, 0), 1.6, (5, 4)[min(level, 1)], mats['bone'], knob=1.8)]


def jug(name, level, mats, r=6.0):
    prof = [(0, 0), (r * 0.7, 0), (r, r * 0.8), (r * 0.9, r * 1.6), (r * 0.35, r * 2.2), (r * 0.35, r * 2.9),
            (r * 0.6, r * 3.1), (0, r * 3.0)]
    return [pl.lathe(name, [(u(a), u(b)) for a, b in prof], (10, 8)[min(level, 1)], mats['jug'], u_repeat=1.0,
                     v_scale=3.0)]


# kind, (x, y), rotation (Euler degrees), size args, last level kept. Listed bottom tier first: each item rests on the
# mound or on the items already placed under it (stacking by bounding boxes), so later entries pile on earlier ones.
ITEMS = [
    # first tier
    ('barrel', (-30, 78), (0, 0, 10), dict(radius=19, length=48), 3),
    ('barrel', (30, 84), (90, 0, 20), dict(radius=19, length=48), 3),
    ('barrel', (78, 76), (0, 0, 40), dict(radius=18, length=46), 3),
    ('barrel', (-100, 24), (90, 0, 70), dict(radius=17, length=42), 2),
    ('barrel', (4, 24), (0, 0, 0), dict(radius=19, length=46), 3),
    ('barrel', (70, -4), (90, 0, -60), dict(radius=18, length=44), 2),
    ('barrel', (-38, 0), (0, 0, 30), dict(radius=17, length=42), 2),
    ('barrel', (96, -50), (90, 0, 10), dict(radius=17, length=42), 2),
    ('barrel', (16, -66), (25, 10, 0), dict(radius=19, length=46), 3),
    ('barrel', (-102, -54), (90, 0, 100), dict(radius=16, length=40), 1),
    ('barrel', (-76, 72), (90, 0, 0), dict(radius=16, length=40), 1),
    ('crate', (100, 54), (0, 0, 20), dict(size=(40, 36, 32)), 2),
    ('crate', (-64, 50), (0, 15, -10), dict(size=(40, 36, 30)), 2),
    ('crate', (-66, -16), (10, 0, 25), dict(size=(42, 38, 30)), 2),
    ('crate', (40, -6), (0, 0, 5), dict(size=(32, 32, 28)), 2),
    ('crate', (-40, -74), (0, 0, 15), dict(size=(26, 22, 18)), 1),
    ('pot', (-48, 30), (0, 0, 0), dict(r=15), 2),
    ('pot', (-24, -32), (0, 0, 0), dict(r=16), 2),
    ('pot', (54, -26), (0, 0, 0), dict(r=14), 2),
    ('cloth', (92, 50), (0, 0, 20), dict(w=28, h=40, seed=1.0), 1),
    ('cloth', (108, 12), (0, 0, -40), dict(w=26, h=36, seed=2.0), 1),
    ('cloth', (-90, 36), (0, 0, 60), dict(w=24, h=30, seed=3.0), 1),
    ('cloth', (-10, -50), (60, 0, 10), dict(w=36, h=26, seed=4.0), 1),
    ('cloth', (108, -36), (0, 0, -80), dict(w=20, h=26, seed=5.0), 0),
    # second tier, on the first
    ('barrel', (-20, 60), (90, 0, 35), dict(radius=17, length=44), 2),
    ('barrel', (48, 64), (60, 0, -30), dict(radius=18, length=46), 2),
    ('barrel', (0, 20), (0, 0, 15), dict(radius=17, length=42), 2),
    ('barrel', (-56, 30), (90, 0, -20), dict(radius=15, length=38), 1),
    ('barrel', (60, 20), (90, 0, 80), dict(radius=16, length=40), 1),
    ('crate', (-36, 70), (0, 0, -25), dict(size=(32, 30, 26)), 1),
    ('crate', (30, 36), (10, 0, 45), dict(size=(30, 28, 24)), 1),
    ('crate', (82, 66), (0, 20, 10), dict(size=(30, 28, 24)), 1),
    ('pot', (-14, 46), (0, 25, 0), dict(r=12), 1),
    ('pot', (24, 2), (0, 0, 0), dict(r=12), 1),
    ('disc', (44, 30), (0, 0, 0), dict(r=11), 1),
    ('disc', (-8, 62), (10, 0, 0), dict(r=10), 1),
    ('disc', (82, 30), (0, 0, 0), dict(r=10), 1),
    ('disc', (-80, 32), (0, 0, 0), dict(r=9), 0),
    ('disc', (62, 50), (20, 0, 0), dict(r=10), 0),
    ('disc', (-30, 16), (0, 0, 0), dict(r=9), 0),
    ('disc', (8, -34), (0, 0, 0), dict(r=10), 0),
    ('bone', (-82, -82), (0, 0, 20), dict(length=24), 0),
    ('bone', (70, -90), (0, 0, -30), dict(length=20), 0),
    ('bone', (104, -66), (0, 0, 70), dict(length=18), 0),
    ('bone', (-114, 6), (0, 0, 80), dict(length=20), 0),
    ('bone', (-94, 44), (0, 0, 10), dict(length=18), 0),
    ('bone', (20, 50), (0, 0, 40), dict(length=18), 0),
    ('jug', (46, -56), (0, 0, 0), dict(r=7), 1),
    # quality pass (2026-10-16): more of the sprite's small lids and bones
    ('disc', (-62, 2), (15, 0, 0), dict(r=9), 0),
    ('disc', (30, -40), (0, 0, 0), dict(r=8), 0),
    ('bone', (-22, -62), (0, 0, 60), dict(length=18), 0),
    ('bone', (56, -72), (0, 0, 10), dict(length=16), 0),
]
BUILDERS = {'barrel': (barrel, ('barrel', 'end')), 'crate': (crate, ('frame', 'panel')), 'pot': (pot, ('pot',)),
            'disc': (disc, ('lid',)), 'cloth': (cloth, ('cloth',)), 'bone': (bone_item, ('bone',)),
            'jug': (jug, ('jug',))}

pl.reset()
mats = {'mound': dlib.material('Mound', 'misc_mound', extras={'openyamm_specular': 0.2}),
        'barrel': dlib.material('Barrel', 'misc_barrel', extras={'openyamm_specular': 0.3}),
        'end': dlib.material('Planks', 'misc_planks', extras={'openyamm_specular': 0.3}),
        'frame': None, 'panel': dlib.material('Panel', 'misc_rock', extras={'openyamm_specular': 0.3}),
        'pot': dlib.material('Iron', 'misc_rustiron', extras={'openyamm_specular': 0.4}),
        'lid': dlib.material('Lid', 'misc_greenmetal', extras={'openyamm_specular': 0.4}),
        'cloth': dlib.material('Cloth', 'misc_cloth', extras={'openyamm_specular': 0.2}),
        'bone': dlib.material('Bone', 'bonelight', extras={'openyamm_specular': 0.3}),
        'jug': None}
mats['frame'] = mats['end']
mats['jug'] = mats['bone']
lods = []
for level in range(4):
    rings, segments = [(10, 26), (8, 20), (5, 12), (3, 8)][level]
    body = hp.mound('mound', height, RX, RY, rings, segments, [mats['mound']], lambda x, y, z: 0, 0.9)
    hl.tag([body], TARGET['mound'])
    parts = [body]
    PLACED.clear()
    for k, (kind, pos, rot, kwargs, keep) in enumerate(ITEMS):
        if level > keep:
            continue
        build, groups = BUILDERS[kind]
        pieces = build(f'{kind}{k}', level, mats, **kwargs)
        for piece in pieces:
            mat = piece.data.materials[0]
            group = next(g for g in groups if mats[g] is mat)
            if kind == 'crate' and mat is mats['end']:
                group = 'frame'
            if kind == 'jug':
                group = 'jug'
            hl.tag([piece], TARGET[group])
        whole = pl.join(f'{kind}{k}', pieces) if len(pieces) > 1 else pieces[0]
        parts.append(transform(whole, rot, pos, sink=(2.0 if kind in ('bone', 'disc', 'cloth') else 6.0)))
    obj = pl.join('Base' if level == 0 else f'Base_LOD{level}', parts)
    pl.vertex_occlusion(obj, rays=(40, 24, 12, 8)[level], distance=u(30), strength=0.6, floor=False)
    hl.tint(obj, report=f'{PROP} L{level}' if level == 0 else '')
    lods.append(obj)
dlib.save(PROP, lods)
