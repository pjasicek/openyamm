"""MM6 dungeon cauldron `cauld00` (39 placements, six frames: the fire under the pot flickers). Not the outdoor
ckfyr00 tripod: a big, bulbous black pot standing on stones over a fire. Traced from the native frames (x2 pixels at
0.5 units, bottom row 192; 101 x 96 units): the pot 83 units wide at 50-60, narrowing to a neck at 82 and flaring
to a red-brown rim band 70 units wide whose top is at 94; a brew surface just under the rim (openyamm_uv_scroll:
the procedural bubbling brew drifts slowly, so the pot's contents churn); three big pink-grey stones in front where
the sprite has them and two behind carrying the pot, two charred logs lying across under it (the sprite's dark
beams reaching both edges), coals and an unlit ember bed; and the fire as three cards on the shared flame02
flipbook between the stones, flames rising from the embers to 33 units like the sprite's. COLOR_0: the sprite's
dark grey pot, reddened toward the fire below, dark red rim band, grey-brown rim top and brew, pink stones darkening
downward, near-black logs and coals. Writes work/cauldron_export.glb.
Usage: blender --background --python build_cauldron.py"""
import math
import os
import random
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fire_lib as fl  # noqa: E402

pl, u = fl.pl, fl.u
pl.reset()
mats = {
    'Pot': fl.material('Pot', 'ph_iron'),
    'Brew': fl.material('Brew', 'brew', extras={'openyamm_uv_scroll': [0.035, 0.02]}),
    'Stone': fl.material('Stone', 'ph_rock'),
    'Logs': fl.material('Logs', 'ph_charwood'),
    'Coals': fl.material('Coals', 'ph_charcoal'),
    # The ember bed: lit ember texture plus a constant glow (emissiveFactor), flickering with the fire.
    'Glow': fl.glow_material('Glow', 'ph_ember', (180, 70, 18), pulse=(0.2, 0.6)),
    'Fire': fl.flame_material('Fire', 'flame02'),
    'Ring': fl.flame_material('Ring', 'flame02', billboard=False),
}
POT = [(0, 21), (12, 21.4), (24, 23), (31, 26), (35, 29.5), (37.5, 35.5), (39.5, 41.5), (41.5, 49.5), (41.5, 59.5),
       (40, 67.5), (37.5, 72), (34, 76), (30, 79.5), (28.5, 82.5), (29.2, 84), (32, 86.5), (34.2, 91), (34.8, 93.2),
       (34, 94.2), (32, 94), (30.6, 92.2), (30, 91.4)]
BREW_Z = 91.3
# Stones: centre (x, y, z bottom), size (x, y, z half extents), seed. Front three where the sprite shows them.
STONES = [((-30, -27, 9), (11.5, 8.5, 13), 1), ((-1, -31, 5), (13, 9, 13), 2), ((31, -26, 9.5), (10.5, 8, 12.5), 3),
          ((-20, 24, 7), (10.5, 8.5, 11), 4), ((21, 25, 7), (10.5, 8.5, 11), 5)]


def stone(name, centre, size, seed, points):
    """A broken, crystalline rock: the convex hull of `points` seeded random points in the stone's ellipsoid (a
    flatter underside), each facet with its own vertices so COLOR_0 lights the facets apart."""
    rng = random.Random(seed * 7919 + points)
    cloud = []
    for i in range(points):
        while True:
            p = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if p.length <= 1.0:
                break
        p = p.normalized() * (0.9 + 0.2 * rng.random()) * 1.1     # the hull is smaller than its ellipsoid
        p.z = max(p.z, -0.55)
        cloud.append(p)
    bm = bmesh.new()
    verts = [bm.verts.new((u(centre[0] + p.x * size[0]), u(centre[1] + p.y * size[1]),
                           u(centre[2] + size[2] * 0.55 + p.z * size[2]))) for p in cloud]
    bmesh.ops.convex_hull(bm, input=verts)
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.split_edges(bm, edges=bm.edges[:])
    uv = bm.loops.layers.uv.verify()
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x * 3 + seed * 0.37, loop.vert.co.z * 3 + loop.vert.co.y * 3)
    return pl.to_object(name, bm, mats['Stone'], smooth=False)


def build(level):
    segments = (20, 14, 8)[level]
    profile = POT if level < 2 else [POT[i] for i in (0, 2, 4, 6, 8, 10, 12, 13, 15, 17, 19, 21)]
    solids = [pl.lathe('pot', [(u(r), u(z)) for r, z in profile], segments, mats['Pot'], u_repeat=3.0,
                       v_scale=1.0)]
    solids.append(pl.lathe('brew', [(0, u(BREW_Z)), (u(30.4), u(BREW_Z))], segments, mats['Brew'], u_repeat=1.0,
                           v_scale=1.0, cap_top=False))
    for k, (centre, size, seed) in enumerate(STONES):
        if level == 2 and k >= 3:
            continue
        solids.append(stone(f'stone{k}', centre, size, seed, (16, 12, 9)[level]))
    sides = (8, 6, 4)[level]
    solids.append(pl.tube('log0', (u(-50), u(10), u(4.6)), (u(50), u(4), u(5.4)), u(4.6), u(4.2), sides,
                          mats['Logs'], v_scale=1.5))
    if level < 2:
        solids.append(pl.tube('log1', (u(-48), u(-6), u(4.2)), (u(49), u(-14), u(3.8)), u(4.2), u(4.0), sides,
                              mats['Logs'], v_scale=1.5))
    # The glowing bed reaches out between the stones (the sprite's fire shows in the gaps at the front).
    whites = [pl.lathe('embers', [(0, u(5.0)), (u(14), u(4.4)), (u(24), u(2.6)), (u(31), u(0.4))],
                       (14, 10, 6)[level], mats['Glow'], u_repeat=3.0, v_scale=3.0)]
    if level < 2:
        # Charcoal lumps heaped on the bed: an inner ring under the pot and lumps in the front gaps.
        lumps = [(2 * math.pi * k / 8 + 0.3, 11 + 7 * (k % 3), 4.0, 1.0) for k in range(8)]
        lumps += [(-1.95, 29, 2.2, 0.9), (-1.2, 29, 2.0, 0.8), (-1.6, 24, 3.2, 1.0), (-2.4, 26, 2.8, 0.8),
                  (-0.75, 26, 2.8, 0.9), (-2.75, 30, 1.6, 0.7), (0.2, 25, 2.6, 0.9), (1.0, 27, 2.4, 0.8),
                  (2.1, 26, 2.4, 0.9), (2.9, 25, 2.6, 0.8), (-0.3, 21, 3.4, 0.9), (-2.1, 20, 3.6, 1.0)]
        for k, (a, r, z, scale) in enumerate(lumps if level == 0 else lumps[:8:2]):
            cb = bmesh.new()
            bmesh.ops.create_icosphere(cb, subdivisions=0, radius=1.0)
            cuv = cb.loops.layers.uv.verify()
            for i, v in enumerate(cb.verts):
                j = 1 + 0.25 * math.sin(i * 7.31 + k * 3.7)
                v.co = Vector((u(math.cos(a) * r + v.co.x * 4.0 * scale * j), u(math.sin(a) * r + v.co.y * 3.4 * scale * j),
                               u(z + v.co.z * 2.6 * scale * j)))
            for face in cb.faces:
                for loop in face.loops:
                    loop[cuv].uv = (loop.vert.co.x * 4 + k * 0.3, loop.vert.co.y * 4)
            solids.append(pl.to_object(f'coal{k}', cb, mats['Coals'], smooth=False))
    # One camera-facing core flame under the pot, and a ring of fixed cards between the stones facing outward:
    # a billboard keeps only its offset across the model, so only fixed cards can stand in front of the pot's
    # belly, where the sprite's flames lick up it (the ring always shows two or three cards toward the camera).
    whites.append(fl.flame_card('fire', mats['Fire'], 'flame02', 3.0, 34.0, 30.0))
    ring = [(-115, 26, 22, 36.0, False), (-65, 26, 22, 37.0, True), (-12, 28, 20, 33.0, False),
            (-168, 28, 20, 33.0, True), (90, 27, 22, 34.0, False)]
    for k, (angle, radius, width, tip, mirrored) in enumerate(ring if level < 2 else ring[:3]):
        card = fl.flame_card(f'ring{k}', mats['Ring'], 'flame02', 3.0, tip, width, mirrored=mirrored)
        a = math.radians(angle)
        card.rotation_euler = (0, 0, a + math.pi / 2)
        card.location = (math.cos(a) * u(radius), math.sin(a) * u(radius), 0)
        fl.apply([card])
        whites.append(card)
    return solids, whites


# Measured on cauld00 by 4-unit band (the pot's middle columns): fire-lit red bottom, dark belly, greyer shoulder,
# red-black neck and rim band, grey-brown rim top.
POT_COLOURS = [(21, (110, 50, 30)), (25, (80, 36, 22)), (29, (52, 21, 12)), (35, (45, 21, 15)), (42, (40, 26, 22)),
               (50, (35, 30, 29)), (58, (42, 39, 39)), (66, (58, 53, 53)), (74, (58, 53, 53)), (78, (50, 27, 23)),
               (82.5, (62, 12, 5)), (86, (74, 14, 6)), (91, (80, 40, 32)), (93.5, (89, 74, 68))]


def pot(co, normal):
    if co.z > 93.0 and normal.z > 0.4:
        return (87, 73, 67)                   # rim top
    if co.xy.length < 31.0 and co.z > 90.5:
        return (60, 30, 22)                   # inner rim wall above the brew
    return fl.stops(POT_COLOURS, co.z)


def facet(colour, co, normal):
    """The sprite's crystalline rocks: pale pink-white faces turned up, dark flanks and undersides, and a little
    per-facet variation."""
    k = 0.35 + 0.8 * max(0.0, normal.z) - 0.15 * max(0.0, -normal.z) + 0.2 * max(0.0, -normal.y)
    k *= 1 + 0.3 * math.sin(normal.x * 9.1 + normal.y * 7.3 + normal.z * 5.7)
    return tuple(min(255.0, c * k) for c in colour)


COLOURS = {
    'Pot': pot,
    'Brew': (80, 68, 60),
    'Stone': lambda co, n: facet(fl.stops([(4, (35, 22, 20)), (11, (60, 36, 32)), (17, (110, 68, 60)),
                                           (24, (150, 98, 90)), (30, (170, 115, 106))], co.z), co, n),
    'Logs': lambda co, n: (40, 10, 2) if co.z > 3 else (28, 6, 2),
    'Coals': lambda co, n: (34, 14, 8) if co.z > 4 else (22, 9, 5),
    'Glow': lambda co, n: fl.stops([(1, (90, 30, 8)), (3.5, (140, 55, 14)), (5, (160, 66, 18))], co.z),
}
fl.build_lods('CauldronPot', 'cauldron', build, COLOURS, rays=(32, 20, 12), distance=20.0, strength=0.5)
