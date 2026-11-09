"""`7dec16` (outdoor, out11, 1 placement): a weathered dead snag in a pile of fallen logs. Two gnarled uprights rise
from the middle: the left one leans out to a broken fork (a stub to the right), the right one winds up thin to a
U-shaped forked tip; five bleached logs lie criss-crossed around their foot, one bent across the front. Traced from
the x2 sprite (127 high, 123 wide; map units); the logs fan out in depth so the pile reads from every side.
Each branch is a swept tube (hanging_lib.sweep) along its path with radii per point, roughened by noise along its
normals; texture: Poly Haven rough_wood (CC0), u around, v along the branch. COLOR_0 = vertex occlusion x the
outdoor grade. Usage: blender --background --python heap_logs.py -- [grade_r grade_g grade_b]"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u
PROP = '7dec16'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
GRADE = [float(a) for a in args[:3]] if len(args) >= 3 else [1.0, 1.0, 1.0]

# name: (points (x, y, z), radii, level from which it is dropped (4 = never))
BRANCHES = {
    # uprights
    'left': ([(-6, 2, 4), (-12, 2, 30), (-17, 1, 50), (-20, 0, 72), (-23, -1, 88), (-34, -2, 97), (-44, -3, 103)],
             [10.5, 9.5, 8.5, 8.0, 7.2, 6.0, 5.0], 4),
    'left_tip': ([(-44, -3, 103), (-48, -4, 109), (-50, -4, 116)], [4.6, 3.6, 2.2], 2),
    'left_stub': ([(-44, -3, 103), (-55, -3, 104), (-60, -3, 108)], [4.2, 3.5, 3.0], 2),
    'left_knob': ([(-20, 0, 86), (-12, -1, 90), (-6, -1, 92)], [5.5, 5.2, 4.6], 2),
    'right': ([(2, -2, 2), (0, -3, 30), (-1, -4, 50), (2, -4, 65), (0, -3, 78), (3, -3, 92), (1, -2, 104),
               (2, -2, 112)], [10.0, 9.5, 8.5, 7.5, 5.6, 4.6, 3.6, 3.0], 4),
    'right_u1': ([(2, -2, 112), (-2, -2, 118), (-3, -2, 124)], [2.8, 2.0, 1.2], 1),
    'right_u2': ([(2, -2, 112), (5, -2, 118), (6, -2, 125)], [2.8, 2.0, 1.2], 1),
    'right_knot': ([(4, -4, 62), (7, -6, 64)], [5.5, 4.0], 2),
    # fallen logs
    'log_back': ([(-58, 14, 30), (-20, 18, 33), (20, 20, 36), (60, 22, 36)], [8.5, 8.8, 9.0, 9.2], 4),
    'log_low': ([(-54, -12, 8), (-15, -16, 9), (20, -20, 11), (50, -22, 12)], [9.5, 9.8, 9.5, 9.0], 4),
    'log_cross': ([(-46, -24, 50), (-30, -24, 42), (-10, -26, 30), (14, -26, 20), (22, -24, 16)],
                  [7.0, 7.5, 8.0, 8.0, 7.5], 4),
    'log_bent': ([(-20, -30, 30), (-4, -32, 36), (14, -32, 44), (26, -30, 38), (36, -28, 30)],
                 [6.0, 6.5, 6.5, 6.0, 5.5], 4),
    'log_side': ([(-30, 40, 8), (-10, 20, 10), (10, 0, 12), (24, -14, 9)], [8.0, 8.5, 8.0, 7.5], 2),
    'log_side2': ([(40, 38, 9), (28, 18, 10), (18, -2, 9)], [8.5, 8.0, 7.5], 2),
}
SIDES = (9, 6, 4)
SEED = {name: i * 7.31 for i, name in enumerate(BRANCHES)}


def resample(points, radii, level):
    """LOD0: points subdivided once (smoother bends); LOD2: every second interior point."""
    pts = [Vector(p) for p in points]
    if level == 0:
        out_p, out_r = [], []
        for i in range(len(pts) - 1):
            out_p += [pts[i], pts[i].lerp(pts[i + 1], 0.5)]
            out_r += [radii[i], (radii[i] + radii[i + 1]) / 2]
        return out_p + [pts[-1]], out_r + [radii[-1]]
    if level == 2 and len(pts) > 3:
        keep = list(range(0, len(pts) - 1, 2)) + [len(pts) - 1]
        return [pts[i] for i in keep], [radii[i] for i in keep]
    return pts, radii


def roughen(obj, seed, amount):
    """Gnarl: displace vertices along their normals by low-frequency noise (map units)."""
    me = obj.data
    for v in me.vertices:
        p = v.co * dlib.UNITS_PER_METRE / 9.0 + Vector((seed, seed * 0.5, 0))
        v.co += v.normal * u(amount * noise.noise(p))


pl.reset()
mat = dlib.material('Wood', 'misc_driftwood', extras={'openyamm_specular': 0.25})
lods = []
for level in range(3):
    parts = []
    for name, (points, radii, drop) in BRANCHES.items():
        if level >= drop:
            continue
        pts, rs = resample(points, radii, level)
        obj = hl.sweep(name, pts, rs, SIDES[level], mat, caps=True, v_scale=1.2, phase=SEED[name])
        obj.data.update()
        if level < 2:
            roughen(obj, SEED[name], 1.6)
        parts.append(obj)
    for p in parts:
        dlib.apply(p)
    obj = pl.join('Base' if level == 0 else f'Base_LOD{level}', parts)
    # buried log undersides: nothing below the ground
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, 0.0)
    pl.vertex_occlusion(obj, rays=(48, 24, 12)[level], distance=u(30), strength=0.7, floor=True)
    me = obj.data
    c = np.empty(len(me.vertices) * 4, np.float32); me.color_attributes['Color'].data.foreach_get('color', c)
    c = c.reshape(-1, 4); c[:, :3] = np.clip(c[:, :3] * np.array(GRADE, np.float32), 0, 1)
    me.color_attributes['Color'].data.foreach_set('color', c.ravel())
    lods.append(obj)
dlib.save(PROP, lods)
