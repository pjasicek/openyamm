"""MM6 iron chandelier `chndlir0` (sprite 249 x 181, seen from below): a wheel of a flat iron band (radius 121,
13 high) braced by two crossed squares of bars, four arms curving down from a hub to the wheel, a chain from the hub
up to the ceiling, and twelve candles of uneven height in dishes standing on the band.
The model's base is the wheel's underside: the native sprite's wheel ellipse centres about 27 units above the
sprite's bottom, so bind it with z_offset 22 and height 159 (chain top at the sprite's top, 181 above the placement);
the bounds top is the chain's ceiling end, the swing pivot.
Candle flames: the shared CC0 flipbook ../../textures/flame03_basecolor.png (16 x 4 frames, 30 fps; card recipe in
../../textures/FLAMES.md) on two crossed cards per candle. Not camera-facing: the engine's billboard turns a card
about the model's own vertical axis and keeps only its offset across the model, which suits a flame on the axis but
would collapse twelve flames around a wheel into one plane.
Writes work/chndlir0_export.glb. Usage: blender --background --python build_chandelier.py"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hanging_lib as hl  # noqa: E402

pl = hl.pl
u = hl.u
PROP = 'chndlir0'
FLAME_COLUMNS, FLAME_ROWS, FLAME_FPS = 16, 4, 30     # flame03: a seamless 64-frame loop of 2.1 s
FLAME_W, FLAME_H = 3.5, 7.0                           # the native candle flame (units)
CARD_W, CARD_H = FLAME_W / 0.6, FLAME_H / 0.85        # FLAMES.md: the flame fills 60 % x 85 % of the card
TOP = 159.0                                            # chain top above the wheel's underside
R_IN, R_OUT, BAND = 108.0, 121.0, 13.0
HUB = 54.0
CANDLE_R = 114.5
CANDLES = 12
COLOURS = {'iron': (28, 18, 14), 'wax': (251, 238, 187)}   # measure.py, the sprite is drawn self-lit

pl.reset()
mats = {
    'Iron': hl.material('Iron', 'iron'),
    'Wax': hl.material('Wax', 'wax'),
    'Flame': hl.material('Flame', 'flame03', alpha=True,
                         extras={'openyamm_flipbook': [FLAME_COLUMNS, FLAME_ROWS, FLAME_FPS],
                                 'openyamm_specular': 0.0}),
}
rng = random.Random(6)
HEIGHTS = [rng.uniform(24.0, 34.0) for _ in range(CANDLES)]      # burnt down unevenly, as in the sprite


def direction(angle):
    return Vector((math.cos(angle), math.sin(angle), 0))


def iron(level):
    parts = [hl.ring('wheel', R_IN, R_OUT, 0, BAND, (32, 20, 12)[level], mats['Iron'])]
    corners = [math.radians(45 + 90 * k) for k in range(4)]
    squares = (corners, [c + math.pi / 4 for c in corners]) if level < 2 else (corners,)
    for s, square in enumerate(squares):
        for k in range(4):
            a, b = direction(square[k]) * (R_IN + 1), direction(square[(k + 1) % 4]) * (R_IN + 1)
            parts.append(hl.sweep(f'bar{s}{k}', [a + Vector((0, 0, BAND * 0.45)), b + Vector((0, 0, BAND * 0.45))],
                                  2.2, (4, 4, 3)[level], mats['Iron'], caps=False, flat=0.8))
    for k, a in enumerate(corners):
        d = direction(a)
        pts = hl.bezier(Vector((0, 0, HUB)), d * 40 + Vector((0, 0, 22)), d * (R_IN + 2) + Vector((0, 0, BAND - 1)),
                        (7, 5, 3)[level])
        parts.append(hl.sweep(f'arm{k}', pts, [3.6 - 1.0 * i / (len(pts) - 1) for i in range(len(pts))],
                              (5, 4, 3)[level], mats['Iron'], caps=level < 2, flat=0.75))
    parts.append(pl.lathe('hub', [(0.0, u(HUB - 6)), (u(5), u(HUB - 5)), (u(7), u(HUB - 1)), (u(6), u(HUB + 3)),
                                  (u(3), u(HUB + 6)), (u(2.2), u(HUB + 9))], (8, 6, 5)[level], mats['Iron'],
                          u_repeat=1.0, v_scale=6.0))
    if level < 2:
        links, bottom = hl.chain('link', HUB + 7, TOP, 13.0, 7.5, 1.4, (10, 8)[level], (4, 3)[level], mats['Iron'])
        parts += links
        if bottom > HUB + 8:
            parts.append(hl.sweep('eye', [(0, 0, HUB + 7), (0, 0, bottom + 3)], 1.6, 4, mats['Iron']))
    else:
        parts.append(hl.sweep('chain', [(0, 0, HUB + 7), (0, 0, TOP)], 2.4, 4, mats['Iron'], flat=0.5))
    if level < 2:
        for k in range(CANDLES):
            c = direction(2 * math.pi * (k + 0.5) / CANDLES) * CANDLE_R
            dish = pl.lathe(f'dish{k}', [(u(3.0), u(BAND)), (u(10.5), u(BAND + 2.5)), (u(11.0), u(BAND + 4.0)),
                                         (u(3.0), u(BAND + 3.5))], (8, 6)[level], mats['Iron'], u_repeat=1.0,
                            v_scale=6.0, centre=(u(c.x), u(c.y), 0.0))
            parts.append(dish)
    return parts


def candles(level):
    parts = []
    for k in range(CANDLES):
        c = direction(2 * math.pi * (k + 0.5) / CANDLES) * CANDLE_R
        base = BAND + (3.0 if level < 2 else 0.0)
        parts.append(hl.sweep(f'candle{k}', [c + Vector((0, 0, base)), c + Vector((0, 0, BAND + HEIGHTS[k]))],
                              2.6, (6, 4, 3)[level], mats['Wax'], caps=level < 2, v_scale=3.0))
    return parts


def flames(level):
    """Two crossed flame cards on each candle top (one card on the farthest level), CARD_W x CARD_H units, showing
    the lower 80 % of a flipbook frame (texture v 0 to 0.8, the empty space above the tips cut, FLAMES.md)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    for k in range(CANDLES):
        a = 2 * math.pi * (k + 0.5) / CANDLES
        c = direction(a) * CANDLE_R
        z0 = BAND + HEIGHTS[k] - 0.025 * CARD_H
        for turn in ((0.0, math.pi / 2) if level < 2 else (0.0,)):
            across = direction(a + math.pi / 2 + turn) * (CARD_W / 2)
            corners = [c - across + Vector((0, 0, z0)), c + across + Vector((0, 0, z0)),
                       c + across + Vector((0, 0, z0 + CARD_H)), c - across + Vector((0, 0, z0 + CARD_H))]
            face = bm.faces.new([bm.verts.new(p * (1 / hl.dl.UNITS_PER_METRE)) for p in corners])
            for loop, st in zip(face.loops, ((0, 0), (1, 0), (1, 0.8), (0, 0.8))):
                loop[uv].uv = st
    return pl.to_object('flames', bm, mats['Flame'], smooth=False)


lods = []
for level in range(3):
    metal = hl.tag(iron(level), COLOURS['iron'])
    wax = hl.tag(candles(level), COLOURS['wax'])
    for obj in metal + wax:
        hl.apply(obj)
    name = 'Chndlir0' if level == 0 else f'Chndlir0_LOD{level}'
    solid = pl.join(name + 'Solid', metal + wax)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12)[level], distance=u(20), strength=0.5, floor=False)
    hl.tint(solid, report=f'{PROP} L{level}', soften={'Wax': 0.25})
    card = flames(level); pl.white_colour(card)
    obj = pl.join(name, [solid, card])
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occlusion, 3))
    lods.append(obj)
lo, hi = pl.bounds(lods[:1])
print('BOUNDS', PROP, [round(v * hl.dl.UNITS_PER_METRE, 1) for v in lo], [round(v * hl.dl.UNITS_PER_METRE, 1)
                                                                         for v in hi])
os.makedirs(hl.WORK, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(hl.WORK, f'{PROP}.blend'))
pl.export(lods, os.path.join(hl.WORK, f'{PROP}_export.glb'))
