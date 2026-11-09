"""MM6 candle `cndlab0` (6 placements, four frames, 60 x 60 logical at frame scale 0.6: 36 x 36 world units): one
white candle on a black candlestick. Built in the sprite's logical units (x2 pixels at 0.5, bottom row 119.5; the
binding height scales it): a black bell foot 36 wide and 23 high, a narrow neck, a pewter drip pan 30 wide at 25-31
with a socket, the candle 6 wide from 33 to 50.5 with a few wax drips, a dark wick, and the flame card (the shared
flame03 flipbook, small and narrow) with its base on the wick and its tip at the sprite top (59.75). COLOR_0: the
sprite's near-black foot, grey pan (pale top, dark underside) and cream wax (paler at the top).
Writes work/candle_export.glb. Usage: blender --background --python build_candle.py"""
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fire_lib as fl  # noqa: E402

pl, u = fl.pl, fl.u
pl.reset()
mats = {
    'Iron': fl.material('Iron', 'ph_ironpit'),
    'Pan': fl.material('Pan', 'ph_pewter'),
    'Wax': fl.material('Wax', 'ph_wax'),
    'Flame': fl.flame_material('Flame', 'flame03'),
}
FOOT = [(0, 0), (10.5, 0.4), (16, 2.5), (18, 5), (18, 8.5), (17, 11.5), (16, 14), (14, 16.5), (11.5, 19), (8, 21.5),
        (4.2, 23), (3.6, 24.2)]
PAN = [(3.6, 24.2), (5.5, 24.8), (10, 25.3), (13, 26.6), (15, 28.6), (15.3, 30.6), (14.7, 31.3), (13.6, 30.8),
       (8, 30.3), (6.2, 30.6), (5.6, 32.3), (4.4, 33.1), (3.0, 33.1)]
CANDLE_TOP = 50.5


def drip(name, angle, z, length, level):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=(1, 0, 0)[level], radius=1.0)
    uv = bm.loops.layers.uv.verify()
    out = Vector((math.cos(angle), math.sin(angle), 0))
    for v in bm.verts:
        p = v.co.copy()
        v.co = out * u(3.0 + 0.45 * (p.x + 1) * 0.5) + Vector((-out.y, out.x, 0)) * u(0.9 * p.y) \
            + Vector((0, 0, u(z - length / 2 + p.z * length / 2)))
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (0.5 + loop.vert.co.x, loop.vert.co.z * 4)
    return pl.to_object(name, bm, mats['Wax'])


def build(level):
    segments = (16, 10, 6)[level]
    foot = FOOT if level < 2 else [FOOT[i] for i in (0, 2, 4, 7, 9, 11)]
    pan = PAN if level < 2 else [PAN[i] for i in (0, 3, 5, 7, 9, 12)]
    solids = [pl.lathe('foot', [(u(r), u(z)) for r, z in foot], segments, mats['Iron'], u_repeat=2.0, v_scale=4.0),
              pl.lathe('pan', [(u(r), u(z)) for r, z in pan], segments, mats['Pan'], u_repeat=2.0, v_scale=4.0),
              pl.lathe('candle', [(u(3.0), u(32.8)), (u(3.0), u(CANDLE_TOP - 0.6)), (u(2.6), u(CANDLE_TOP)),
                                  (u(1.2), u(CANDLE_TOP - 0.4)), (0, u(CANDLE_TOP - 0.3))], (12, 8, 6)[level],
                       mats['Wax'], u_repeat=1.0, v_scale=6.0)]
    # Melted wax pooled over the socket (the sprite's bright disc round the candle's foot).
    # Lit by the candle above it, so no occlusion (a white part, tinted only).
    pool = [(3.0, 33.3), (5.0, 33.0), (6.6, 31.8), (7.6, 30.6)]
    pool = pl.lathe('pool', [(u(r), u(z)) for r, z in pool], (12, 8, 6)[level], mats['Wax'], u_repeat=1.0,
                    v_scale=6.0)
    if level < 2:
        for k, (angle, z, length) in enumerate(((-1.9, 47, 5.5), (-0.6, 45.5, 8), (1.2, 46.5, 6), (2.6, 48, 4))):
            solids.append(drip(f'drip{k}', angle, z, length, level))
        solids.append(pl.tube('wick', (0, 0, u(CANDLE_TOP - 0.5)), (0, 0, u(CANDLE_TOP + 1.4)), u(0.35), u(0.25), 4,
                              mats['Iron'], v_scale=4.0))
    fl.apply(solids)
    return solids, [pool, fl.flame_card('flame', mats['Flame'], 'flame03', CANDLE_TOP + 0.6, 59.75, 6.0)]


FOOT_COLOURS = [(0, (37, 29, 27)), (2, (28, 22, 22)), (7, (22, 16, 15)), (12, (23, 19, 18)), (16, (36, 33, 34)),
                (19, (29, 26, 26)), (22, (25, 22, 21)), (23.5, (9, 6, 5)), (24.2, (9, 6, 5))]
COLOURS = {
    'Iron': lambda co, n: (12, 8, 6) if co.z > 49 else fl.stops(FOOT_COLOURS, co.z),
    # Measured on cndlab0: the dish greyer toward its dark rim, its outer side and underside dark.
    'Pan': lambda co, n: fl.stops([(3, (140, 125, 115)), (8, (118, 103, 96)), (12, (92, 79, 72)),
                                   (15.3, (72, 63, 57))], co.xy.length) if n.z > 0.35 and co.z > 28 else
    fl.stops([(24, (30, 25, 23)), (26, (60, 50, 46)), (28.6, (80, 70, 64)), (31.3, (75, 66, 60))], co.z),
    'Wax': lambda co, n: fl.stops([(30.5, (252, 242, 208)), (33.4, (236, 214, 188)), (40, (232, 214, 190)),
                                   (46, (243, 230, 203)), (50.5, (250, 225, 195))], co.z),
}
fl.build_lods('Candle', 'candle', build, COLOURS, rays=(32, 20, 12), distance=6.0, strength=0.5)
