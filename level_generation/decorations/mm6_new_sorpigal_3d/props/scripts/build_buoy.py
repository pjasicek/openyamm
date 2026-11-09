"""Buoy `bouy0`: a wide iron float (lathe), a tapering cage of hoops and bars, a red-painted dome and a cross finial,
and a dark inner column, traced from the sprite (128 x 172 units -> 1.64 x 2.2 m). Every material sways gently
(openyamm_wind). Each LOD is built at its own detail. Writes work/buoy_export.glb.
Usage: blender --background --python build_buoy.py"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

pl.reset()
WIND = 0.05
mats = {'Iron': pl.material('Iron', 'iron', extras={'openyamm_wind': WIND}),
        'Red': pl.material('Red', 'redpaint', extras={'openyamm_wind': WIND})}
FLOAT = [(0.0, 0.0), (0.70, 0.0), (0.80, 0.08), (0.82, 0.17), (0.78, 0.28), (0.62, 0.35), (0.50, 0.38), (0.0, 0.38)]
DOME = [(0.0, 1.61), (0.34, 1.61), (0.40, 1.68), (0.41, 1.78), (0.36, 1.90), (0.24, 1.99), (0.08, 2.03), (0.0, 2.04)]
CAGE_BOTTOM, CAGE_TOP = (0.48, 0.38), (0.31, 1.60)          # (radius, z)


def cage_radius(z):
    t = (z - CAGE_BOTTOM[1]) / (CAGE_TOP[1] - CAGE_BOTTOM[1])
    return CAGE_BOTTOM[0] + (CAGE_TOP[0] - CAGE_BOTTOM[0]) * t


def build(level):
    seg = (28, 14, 8)[level]
    parts = [pl.lathe('float', FLOAT if level < 2 else FLOAT[::2] + [FLOAT[-1]], seg, mats['Iron'], u_repeat=4,
                      v_scale=2),
             pl.lathe('dome', DOME if level < 2 else DOME[::2] + [DOME[-1]], seg, mats['Red'], u_repeat=3, v_scale=2)]
    hoops = (5, 4, 2)[level]
    for k in range(hoops):
        z = CAGE_BOTTOM[1] + 0.02 + (CAGE_TOP[1] - CAGE_BOTTOM[1] - 0.02) * k / (hoops - 1)
        r = cage_radius(z); t = 0.025
        profile = [(r + t * math.cos(2 * math.pi * j / 4), z + t * math.sin(2 * math.pi * j / 4)) for j in range(5)]
        parts.append(pl.lathe(f'hoop{k}', profile, seg, mats['Iron'], u_repeat=4, v_scale=4))
    bars = (16, 10, 6)[level]
    for k in range(bars):
        a = 2 * math.pi * k / bars
        bottom = Vector((math.cos(a) * CAGE_BOTTOM[0], math.sin(a) * CAGE_BOTTOM[0], CAGE_BOTTOM[1]))
        top = Vector((math.cos(a) * CAGE_TOP[0], math.sin(a) * CAGE_TOP[0], CAGE_TOP[1]))
        parts.append(pl.tube(f'bar{k}', bottom, top, 0.026, 0.02, (4, 3, 3)[level], mats['Iron'], v_scale=2))
    # dark inner column: the sprite's cage is not hollow
    core = [(CAGE_BOTTOM[0] * 0.72, CAGE_BOTTOM[1]), (CAGE_TOP[0] * 0.72, CAGE_TOP[1])]
    parts.append(pl.lathe('core', core, max(seg // 2, 6), mats['Iron'], u_repeat=3, v_scale=2))
    parts.append(pl.tube('finial', (0, 0, 2.02), (0, 0, 2.20), 0.018, 0.012, (6, 4, 3)[level], mats['Iron'], v_scale=4))
    if level < 2:
        parts.append(pl.tube('cross', (-0.07, 0, 2.13), (0.07, 0, 2.13), 0.012, 0.012, 4, mats['Iron'], v_scale=4))
    return pl.join(f'buoy{level}', parts)


lods = []
for level in range(3):
    obj = build(level)
    occl = pl.vertex_occlusion(obj, rays=(40, 24, 12)[level], distance=0.4, strength=0.6, floor=False)
    obj.name = 'Buoy' if level == 0 else f'Buoy_LOD{level}'; obj.data.name = obj.name
    print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'buoy.blend'))
pl.export(lods, os.path.join(work, 'buoy_export.glb'))
