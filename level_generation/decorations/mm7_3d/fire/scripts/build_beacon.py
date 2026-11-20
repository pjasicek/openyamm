"""Beacon fires dec60 (blue), dec62 (orange), dec63 (white): one carved stone bowl on a round pedestal, traced from
the restored native frames (x2 pixels at 0.8 units; frame bottom = ground); and dec61: a golden brazier on clawed
feet. Each variant: a glowing ember bed in the bowl (openyamm_flicker), a centre flame card on the model axis, three
off-axis flame cards (openyamm_billboard "card", each turned about its own centre and showing other flipbook frames)
for a fuller, ragged fire, and a soft additive halo card round the flame.
Writes work/beacon_<variant>_export.glb.
Usage: blender --background --python build_beacon.py -- stone_blue|stone_orange|stone_white|gold"""
import math
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firelib as fl  # noqa: E402

pl = fl.pl
VARIANT = sys.argv[sys.argv.index('--') + 1]
STONE = VARIANT.startswith('stone')
COLOUR = VARIANT.split('_')[1] if STONE else 'orange'
GLOW = {'orange': (205, 95, 30), 'blue': (40, 125, 225), 'white': (150, 152, 165)}[COLOUR]
pl.reset()

flame = fl.flame_material('Flame', COLOUR)
cards = {name: fl.flame_card_material(name, COLOUR) for name in ('FlameA', 'FlameB', 'FlameC')}
halo = fl.halo_material('Halo')
bed = fl.glow_material('Glow', f'ember_{COLOUR}', GLOW, extras={'openyamm_flicker': [0.35, 6.0]})
HALO = {'orange': (1.0, 0.42, 0.1), 'blue': (0.1, 0.42, 1.0), 'white': (0.75, 0.77, 0.85)}[COLOUR]
# Off-axis cards (x, y, base offset, tip below the centre tip, width share, mirrored, flipbook shift, min level).
CARDS = [('FlameA', -16, -10, 1, 12, 0.72, True, 5, 3), ('FlameB', 15, 9, 1, 18, 0.68, False, 9, 1),
         ('FlameC', 2, 15, 2, 8, 0.62, True, 13, 0)]

# ---------------------------------------------------------------- stone beacon (dec60 / dec62 / dec63)
# (radius, z) in units, bottom to top, over the lip and down the inside to the ember bed.
STONE_PROFILE = [
    (0, 0), (27.5, 0), (29, 1.5), (29, 12.5), (28, 13.8), (25.5, 14.5), (25.5, 18.2), (24, 19), (21, 19.5),
    (19.5, 21.2), (17.5, 22), (16, 23.5), (15.2, 26), (15, 30), (15.5, 42), (16, 52), (15.5, 62), (14.8, 68.5),
    (14.5, 70.5), (16.2, 71.2), (17.5, 73), (17.5, 82.5), (16.2, 84), (13.5, 85), (12, 87), (11.5, 89), (11.5, 95),
    (14, 97), (20, 99.5), (25.5, 102.5), (30, 106), (33.5, 111), (36.5, 116), (38.5, 119.3), (42, 120.2),
    (44.5, 121.8), (45, 125), (44.3, 127.8), (42, 128.5), (39.5, 128.5), (37, 126.5), (34, 124.5)]
# Coal bed: a low mound inside the bowl, just under the lip.
STONE_BED = [(35, 124.0), (26, 125.5), (14, 126.5), (0, 126.8)]

# ---------------------------------------------------------------- golden brazier (dec61)
GOLD_BOWL = [
    (0, 99), (8.5, 99), (9, 104), (12, 106.5), (22, 108.3), (29, 110.5), (33.5, 114), (36.5, 119), (37.5, 124),
    (38, 129.5), (40.5, 131.5), (44, 133), (44.8, 135), (43.5, 137), (40.5, 137.5), (38.5, 136), (36, 133.5),
    (32, 131.5)]
GOLD_BED = [(33, 131.0), (24, 132.5), (12, 133.5), (0, 133.8)]
GOLD_COLLAR = [(8.5, 85.5), (13, 86), (16, 87.5), (18.5, 90.5), (17, 93.5), (13, 96), (8.5, 99)]
GOLD_LOWER = [
    (0, 18), (14, 18), (24, 20), (26, 22.5), (24, 25), (18, 26.5), (16.5, 28.5), (19, 30), (19, 32),
    (16.5, 33.5), (14, 35), (12.5, 38), (12.5, 43.5), (15.5, 44.5), (16.5, 46.5), (13, 48.5), (10, 49.5),
    (9.5, 84), (12, 85.5)]


def gold_rib(k, count, mat, sides):
    """A cage rib: a bar curving out from the waist ring to the collar ring (three straight segments)."""
    a = 2 * math.pi * (k + 0.5) / count
    points = [(12.5, 47), (13.5, 58), (16.5, 69), (20.5, 80), (19.5, 84)]
    parts = []
    for (r0, z0), (r1, z1) in zip(points, points[1:]):
        p0 = (r0 * math.cos(a), r0 * math.sin(a), z0)
        p1 = (r1 * math.cos(a), r1 * math.sin(a), z1)
        parts.append(fl.tube(f'rib{k}_{z0}', p0, p1, 2.2, 2.2, sides, mat, caps=False))
    return parts


def gold_leg(k, count, mat, level):
    """A clawed leg: from the base dish out and down to a ball foot gripped by three talons."""
    a = 2 * math.pi * k / count + math.pi / 2
    d = Vector((math.cos(a), math.sin(a), 0))
    side = Vector((-d.y, d.x, 0))
    sides = (6, 4, 3)[level]
    points = [(20, 21), (27, 17.5), (32.5, 12), (35.5, 7)]
    parts = []
    for (r0, z0), (r1, z1), w in zip(points, points[1:], (5.0, 4.4, 3.8)):
        p0 = tuple(d * r0 + Vector((0, 0, z0)))
        p1 = tuple(d * r1 + Vector((0, 0, z1)))
        parts.append(fl.tube(f'leg{k}_{z0}', p0, p1, w, w * 0.85, sides, mat, caps=False))
    ball = Vector(d * 37 + Vector((0, 0, 5.5)))
    bm_sides = (8, 6, 4)[level]
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=bm_sides, v_segments=max(4, bm_sides // 2 + 1), radius=fl.u(6.5))
    for v in bm.verts:
        v.co += Vector([fl.u(c) for c in ball])
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x * 4, loop.vert.co.z * 4)
    parts.append(pl.to_object(f'ball{k}', bm, mat))
    if level < 2:
        for t, offset in enumerate((-1, 0, 1)):
            root = ball + d * 2.5 + side * offset * 3.5 + Vector((0, 0, 2.5))
            tip = ball + d * 8 + side * offset * 5.5 + Vector((0, 0, -5.3))
            parts.append(fl.tube(f'talon{k}_{t}', tuple(root), tuple(tip), 2.0, 0.6, 4 if level == 0 else 3, mat,
                                 caps=False))
    return parts


def build(level):
    if STONE:
        seg = (22, 14, 8)[level]
        profile = STONE_PROFILE if level == 0 else STONE_PROFILE[::2] + [STONE_PROFILE[-1]]
        if level == 2:
            profile = [p for i, p in enumerate(STONE_PROFILE) if i % 3 == 0] + [STONE_PROFILE[-1]]
        solids = [fl.lathe('stone', profile, seg, mats['Stone'], u_repeat=3, v_scale=1.2)]
        whites = [fl.lathe('bed', STONE_BED, seg, bed, u_repeat=2, v_scale=2)]
        base, tip, width, side_tip = 123.0, 190.0, 92.0, 168.0
    else:
        seg = (24, 14, 10, 6)[level]
        coarse = level >= 2
        solids = [fl.lathe('bowl', GOLD_BOWL[::2] + [GOLD_BOWL[-1]] if coarse else GOLD_BOWL, seg, mats['Gold'],
                           u_repeat=3, v_scale=1.5),
                  fl.lathe('collar', GOLD_COLLAR[::2] + [GOLD_COLLAR[-1]] if coarse else GOLD_COLLAR,
                           max(seg - 6, 6), mats['Gold'], u_repeat=2, v_scale=2),
                  fl.lathe('lower', GOLD_LOWER[::2] + [GOLD_LOWER[-1]] if coarse else GOLD_LOWER,
                           max(seg - 4, 6), mats['Gold'], u_repeat=2, v_scale=2)]
        if level < 3:
            solids.append(fl.torus('cagering', 20.5, 2.2, 82.5, max(seg - 4, 8), (6, 4, 3)[level], mats['Gold']))
            ribs = (8, 8, 6)[level]
            for k in range(ribs):
                solids += gold_rib(k, ribs, mats['Gold'], (5, 4, 3)[level])
            for k in range(5):
                solids += gold_leg(k, 5, mats['Gold'], level)
        else:
            # Far impostor of the cage and legs: a flared drum and five single leg bars.
            solids.append(fl.lathe('cage', [(12.5, 47), (15, 64), (20.5, 82)], seg, mats['Gold'], u_repeat=2))
            for k in range(5):
                a = 2 * math.pi * k / 5 + math.pi / 2
                solids.append(fl.tube(f'leg{k}', (20 * math.cos(a), 20 * math.sin(a), 21),
                                      (38 * math.cos(a), 38 * math.sin(a), 2), 5, 4, 3, mats['Gold'], caps=False))
        whites = [fl.lathe('bed', GOLD_BED, seg, bed, u_repeat=2, v_scale=2)]
        base, tip, width, side_tip = 130.0, 198.0, 90.0, 176.0
    # Halo first: the blended flames then draw over the additive glow.
    whites.append(fl.glow_card('halo', halo, (base + tip) / 2 + 6, width * 1.35, tip - base - 12))
    whites.append(fl.flame_card('flame', flame, base, tip, width))
    for name, x, y, lift, drop, share, mirrored, shift, top_level in CARDS:
        if level <= top_level:
            whites.append(fl.flame_card(name.lower(), cards[name], base + lift, tip - drop, width * share, x=x, y=y,
                                        mirrored=mirrored, shift=shift))
    return solids, whites


if STONE:
    mats = {'Stone': fl.material('Stone', 'stone', extras={'openyamm_specular': 0.4})}
    # Native stone (dec60a, measured by height): dark plinth, lighter column, dark bowl underside, lit rim.
    STONE_STOPS = [(0, (58, 50, 46)), (14, (54, 47, 43)), (24, (64, 55, 51)), (55, (96, 85, 78)),
                   (70, (86, 76, 70)), (95, (58, 51, 47)), (104, (60, 53, 49)), (118, (78, 70, 64)),
                   (125, (92, 82, 74)), (129, (52, 46, 42))]
    # Warmer and darker than measured: the review sky light greys the stone.
    colours = {'Stone': lambda co, n: tuple(c * w for c, w in zip(fl.stops(STONE_STOPS, co.z), (0.95, 0.89, 0.83)))}
    if COLOUR == 'orange':
        # dec62's flame is a deeper orange-red than the torch flame (native linear 1 : 0.16 : 0.01).
        colours['Flame'] = ('mul', (0.85, 0.27, 0.2))
    colours['Halo'] = ('mul', tuple(c * 0.55 for c in HALO))
    prop = f'beacon_{VARIANT}'
else:
    mats = {'Gold': fl.material('Gold', 'gold', extras={'openyamm_specular': 0.8})}
    # Native gold (dec61a): bright rim and collar, darker bowl underside and cage core.
    GOLD_STOPS = [(0, (150, 115, 62)), (20, (155, 120, 66)), (35, (140, 104, 57)), (50, (150, 112, 60)),
                  (70, (128, 94, 52)), (85, (158, 120, 66)), (100, (110, 82, 45)), (110, (95, 72, 42)),
                  (122, (165, 124, 70)), (134, (178, 134, 76))]
    colours = {'Gold': lambda co, n: tuple(c * w for c, w in zip(fl.stops(GOLD_STOPS, co.z), (1.05, 1.0, 0.8))),
               # dec61's flame is a paler, softer orange (native linear 1 : 0.33 : 0.10).
               'Flame': ('mul', (0.8, 0.55, 1.2)),
               'Halo': ('mul', (0.55, 0.24, 0.07))}
    prop = 'beacon_gold'

for name in cards:
    if 'Flame' in colours:
        colours[name] = colours['Flame']
fl.build_lods('Beacon', prop, build, colours, rays=(32, 20, 12, 8), distance=14.0, strength=0.55,
              levels=3 if STONE else 4,
              last=('Glow', 'Halo', 'Flame', 'FlameA', 'FlameB', 'FlameC'), sharp=30)
