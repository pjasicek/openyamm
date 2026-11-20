"""Three-branch candlestick `dec02` (one placement in d06; six frames in 12/16 s, light 86; 78 x 123 units): a
copper candelabrum traced from dec02a (x2 pixels at 0.5 units): a domed round foot (52 wide, 0-15), a thin stem to a
knob and the centre cup (77-81, 22 wide) under the tall centre candle (81-109), a crossbar at 26.5 from which two arms
curve out and up to cups at +-28.7 (62-71) carrying the side candles (to 97 and 101, uneven as in the sprite). The
frames change only the three flames.

Surfaces: `copper` (CC0 Blue Metal Plate scratches graded to copper; semi-metallic, glossy) tinted to the sprite's
dark bronze with orange highlights, `wax` (CC0 Leather White grain) cream. Flames (2026-10-16): `candleglow` (the shared Flame03 flipbook with a soft halo baked round each frame), additive
with a smooth random flicker; the side flames are card billboards turning about their own centres (one primitive
each), the centre flame turns about the model axis. Earlier: the shared Flame03 candle flipbook;
the centre flame is camera-facing on the axis, the side flames are two crossed fixed cards each (a camera-facing card
keeps only its offset across the model), each flame on its own frame offset so they do not flicker in step. A soft
warm halo round the centre flame pulses.
Writes work/candlestick_export.glb. Usage: blender --background --python build_candlestick.py"""
import math
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
pl.reset()
mats = {
    'Copper': al.material('Copper', 'copper', extras={'openyamm_specular': 0.8}),
    'Wax': al.material('Wax', 'wax', extras={'openyamm_specular': 0.4}),
    'Flame': al.flame_material('Flame', 'candleglow', additive=True, flicker=(0.3, 8.0), emission=(26, 10, 2)),
    'CandleFar': al.flame_material('CandleFar', 'candleglow', billboard=False, additive=True, flicker=(0.3, 8.0),
                                   emission=(26, 10, 2)),
}
FOOT = [(0.0, 0.0), (18.0, 0.0), (23.5, 1.2), (26.0, 3.4), (26.0, 5.4), (23.0, 7.6), (17.0, 10.0), (11.0, 12.0),
        (6.0, 13.6), (3.4, 14.8), (2.4, 16.0)]
STEM = [(2.4, 16.0), (2.1, 25.0), (3.4, 25.6), (3.4, 27.6), (2.1, 28.4), (2.1, 73.6), (3.6, 74.6), (3.8, 76.2),
        (2.6, 77.0)]
CUP = [(2.6, 77.0), (6.0, 77.8), (9.5, 79.2), (11.2, 80.6), (11.0, 81.6), (9.0, 81.4), (3.0, 81.0)]
SIDE_CUP = [(1.6, 60.8), (3.4, 62.0), (5.4, 63.8), (7.6, 66.0), (8.6, 68.6), (8.4, 70.4), (6.2, 70.4), (2.8, 70.2)]
X_SIDE = 28.7
CANDLES = [(0.0, 81.0, 109.0, 2.3), (-X_SIDE, 70.2, 97.0, 2.2), (X_SIDE, 70.2, 101.0, 2.2)]
# The centre card's top (its halo above the flame, texture v 0.80) is the sprite top, 123: flame tip 121.2.
FLAME_TIP = {0.0: 121.2, -X_SIDE: 109.5, X_SIDE: 113.5}
CENTRE_TOP_V = 0.80


def lathe(name, profile, segments, mat, x=0.0, step=1, u_repeat=2.0, v_scale=4.0):
    pts = profile[::step] + ([profile[-1]] if (len(profile) - 1) % step else [])
    return pl.lathe(name, [(u(r), u(z)) for r, z in pts], segments, mat, u_repeat=u_repeat, v_scale=v_scale,
                    centre=(u(x), 0, 0))


def candle(name, x, z0, z1, r, segments):
    profile = [(r, z0), (r, z1 - 0.8), (r * 0.8, z1), (0.0, z1 - 0.2)]
    return pl.lathe(name, [(u(a), u(b)) for a, b in profile], segments, mats['Wax'], u_repeat=1.0, v_scale=6.0,
                    centre=(u(x), 0, 0))


def build(level):
    seg = (24, 14, 8)[level]
    step = (1, 2, 3)[level]
    solids = [lathe('foot', FOOT, seg, mats['Copper'], step=step),
              lathe('stem', STEM, (10, 8, 5)[level], mats['Copper'], step=step),
              lathe('cup', CUP, (16, 10, 6)[level], mats['Copper'], step=step)]
    solids.append(pl.tube('bar', (u(-10.5), 0, u(26.6)), (u(10.5), 0, u(26.6)), u(1.9), u(1.9), (6, 5, 4)[level],
                          mats['Copper']))
    for side in (-1, 1):
        path = [Vector((u(side * x), 0, u(z))) for x, z in ((9.5, 26.8), (16.0, 29.4), (21.4, 33.4), (25.2, 38.6),
                                                             (27.6, 45.0), (28.6, 52.0), (28.7, 61.0))]
        if level < 2:
            path = al.bezier(path, (12, 7)[level])
        solids.append(al.sweep(f'arm{side}', path, u(1.9), (6, 5, 4)[level], mats['Copper'], v_scale=3.0))
        solids.append(lathe(f'sidecup{side}', SIDE_CUP, (14, 8, 6)[level], mats['Copper'], x=side * X_SIDE,
                            step=step))
    for k, (x, z0, z1, r) in enumerate(CANDLES):
        solids.append(candle(f'candle{k}', x, z0, z1, r, (12, 8, 6)[level]))
        if level < 2:
            solids.append(pl.tube(f'wick{k}', (u(x), 0, u(z1 - 0.4)), (u(x), 0, u(z1 + 1.2)), u(0.35), u(0.25), 4,
                                  mats['Copper']))
    al.apply(solids)
    whites = []
    span = al.FLAME_SPAN['candleglow']
    for k, (x, z0, z1, r) in enumerate(CANDLES):
        tip = FLAME_TIP[x]
        if x == 0.0:
            whites.append(al.flame_card('flame', mats['Flame'], 'candleglow', z1 + 0.4, tip, 4.2 / span,
                                        v_top=CENTRE_TOP_V))
        elif level < 2:
            whites.append(al.candle_card(f'Candle{k}', x, 0.0, z1 + 0.4, tip, 3.6, 19 * k))
        else:
            whites += al.flame_star(f'far{k}', mats['CandleFar'], 'candleglow', z1 + 0.4, tip, 3.6 / span, x, 0.0,
                                    cards=2, frame_offset=19 * k, yaw=45.0)
    return solids, whites


def copper(co, n):
    """dec02's dark bronze: an orange highlight round the foot's shoulder and on the cups' rims, near black in the
    hollows and on the shadowed stem."""
    if co.z < 16:
        return al.stops([(0, (40, 22, 10)), (3, (80, 44, 18)), (5.5, (84, 44, 17)), (8.5, (45, 25, 11)),
                         (12, (62, 34, 14)), (16, (38, 24, 13))], co.z)
    if 60 < co.z < 72 or 76 < co.z < 82:
        return (74, 46, 26)
    return (38, 24, 13)


COLOURS = {'Copper': copper,
           'Wax': lambda co, n: al.stops([(70, (196, 186, 160)), (90, (222, 214, 188)), (110, (250, 246, 226))],
                                         co.z),
           }
al.build_lods('Candlestick', 'candlestick', build, COLOURS, rays=(32, 20, 12), distance=12.0, strength=0.5,
              last=('Candle', 'Flame'))
