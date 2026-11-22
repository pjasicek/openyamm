"""`7dec12` "wood" (MM7 engine decoration, placed by the Xeen maps): a pile of weathered grey-brown driftwood. Traced
from the x2 sprite (119 high, 127 wide, map units): two forked limbs stand up crossed in the middle (the left one
leans out to an antler-like U fork, the right one winds up to a split tip and carries a twiggy side branch), a limb
curls between them, a gnarled log with a knotted head lies to the left, a broken root head with finger twigs juts up to
the right, and long logs lie across the base; the base logs fan out in depth so the pile reads from every side.
Each branch is a swept tube (xlib.sweep: whole bark repeats around, one density along) through its traced points with
a radius per point, gnarled by noise along the normals; texture `driftwood` (Poly Haven rough_wood, CC0). Like the
MM7 dressing's 7dec16 (heap_logs.py), whose layout this follows. COLOR_0 = vertex occlusion x the outdoor grade.
Usage: blender --background --python build_wood.py -- [grade_r grade_g grade_b]"""
import os
import sys

import numpy as np
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlib  # noqa: E402

pl, u = xlib.pl, xlib.u
PROP = '7dec12'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
GRADE = [float(a) for a in args[:3]] if len(args) >= 3 else [1.0, 1.0, 1.0]

# name: (points (x, y, z) in map units, radii, level from which it is dropped (3 = never)); -y is the sprite's view
BRANCHES = {
    # the two crossed uprights (the left leans back, the right forward, so the pile has depth)
    'up_left': ([(-1, 1, 4), (-5, 3, 28), (-9, 5, 48), (-15, 8, 68), (-21, 10, 84), (-26, 11, 97)],
                [8.0, 7.4, 6.8, 6.0, 5.0, 4.0], 3),
    'ul_fork_a': ([(-26, 11, 97), (-31, 11, 104), (-33, 12, 111), (-31, 12, 118)], [3.6, 3.0, 2.4, 1.4], 2),
    'ul_fork_b': ([(-26, 11, 97), (-22, 10, 104), (-20, 10, 110), (-22, 9, 117)], [3.2, 2.8, 2.2, 1.3], 2),
    'ul_twig': ([(-18, 9, 88), (-14, 8, 94), (-14, 6, 100)], [2.8, 2.2, 1.3], 1),
    'up_right': ([(1, -2, 4), (2, -4, 28), (6, -6, 48), (10, -8, 63), (8, -9, 76), (12, -10, 88), (16, -10, 99)],
                 [9.0, 8.5, 8.0, 7.4, 6.4, 5.4, 4.4], 3),
    'ur_tip_a': ([(16, -10, 99), (18, -10, 109), (17, -11, 119)], [3.6, 2.8, 1.4], 2),
    'ur_tip_b': ([(16, -10, 99), (22, -9, 105), (26, -8, 111)], [3.2, 2.5, 1.4], 2),
    'ur_branch': ([(10, -10, 80), (3, -14, 84), (-5, -16, 84), (-10, -17, 80)], [2.8, 2.4, 2.0, 1.2], 2),
    'ur_twig': ([(3, -14, 84), (-3, -15, 88), (-8, -17, 90)], [1.9, 1.5, 1.0], 1),
    'curl': ([(9, -9, 61), (-3, -12, 62), (-15, -10, 60), (-21, -4, 54), (-20, 2, 47)], [4.6, 4.5, 4.2, 3.8, 3.0], 2),
    # gnarled log to the left, its knotted head angled back
    'log_left': ([(6, 4, 24), (-12, 6, 32), (-32, 10, 34), (-48, 14, 31), (-58, 17, 26), (-62, 19, 22)],
                 [7.5, 8.5, 9.0, 8.5, 7.5, 4.0], 3),
    'log_left_knot': ([(-50, 12, 30), (-55, 5, 31), (-57, 0, 28)], [5.0, 4.4, 2.6], 2),
    # root head jutting up to the right and toward the viewer, with finger twigs
    'root_right': ([(6, -2, 20), (18, -8, 32), (29, -13, 43), (36, -15, 50)], [7.5, 7.0, 6.2, 5.0], 3),
    'root_f1': ([(35, -15, 49), (42, -16, 54), (49, -17, 56)], [3.0, 2.2, 1.3], 2),
    'root_f2': ([(36, -15, 51), (40, -18, 58), (42, -20, 63)], [2.8, 2.0, 1.2], 2),
    'root_f3': ([(33, -14, 45), (41, -18, 43), (47, -22, 45)], [2.8, 2.1, 1.2], 2),
    # logs across the base, fanning out in a star
    'log_front': ([(-63, -10, 9), (-30, -12, 10), (0, -12, 10), (30, -10, 9), (62, -6, 8)],
                  [5.0, 8.5, 9.0, 8.5, 4.5], 3),
    'log_right_low': ([(8, 2, 22), (28, 8, 19), (46, 14, 15), (60, 18, 12)], [7.0, 6.8, 6.0, 3.6], 3),
    'log_back': ([(-46, 26, 7), (-14, 22, 8), (16, 20, 8), (44, 18, 6)], [4.5, 7.5, 7.5, 4.0], 3),
    'log_back_left': ([(0, 4, 9), (-16, 28, 8), (-30, 46, 6)], [7.0, 6.5, 3.6], 2),
    'log_front_right': ([(4, -6, 9), (20, -26, 8), (32, -42, 6)], [7.0, 6.2, 3.4], 2),
}
SIDES = (7, 5, 4)
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
    for v in obj.data.vertices:
        p = v.co * xlib.UNITS_PER_METRE / 7.0 + Vector((seed, seed * 0.5, 0))
        v.co += v.normal * u(amount * noise.noise(p))


pl.reset()
mat = xlib.material('Wood', 'driftwood', extras={'openyamm_specular': 0.2})
lods = []
for level in range(3):
    parts = []
    for name, (points, radii, drop) in BRANCHES.items():
        if level >= drop:
            continue
        pts, rs = resample(points, radii, level)
        obj = xlib.sweep(name, pts, rs, SIDES[level], mat, tile=0.6, phase=SEED[name])
        obj.data.update()
        if level < 2:
            roughen(obj, SEED[name], 2.0)
        parts.append(obj)
    obj = pl.join('Base' if level == 0 else f'Base_LOD{level}', parts)
    low = min(v.co.z for v in obj.data.vertices) + u(1.5)
    for v in obj.data.vertices:             # logs sink 1.5 units: their undersides end flat on the ground
        v.co.z = max(v.co.z - low, 0.0)
    pl.vertex_occlusion(obj, rays=(48, 24, 12)[level], distance=u(30), strength=0.75, floor=True)
    me = obj.data
    c = np.empty(len(me.vertices) * 4, np.float32); me.color_attributes['Color'].data.foreach_get('color', c)
    c = c.reshape(-1, 4); c[:, :3] = np.clip(c[:, :3] * np.array(GRADE, np.float32), 0, 1)
    me.color_attributes['Color'].data.foreach_set('color', c.ravel())
    lods.append(obj)
xlib.save(PROP, lods)
