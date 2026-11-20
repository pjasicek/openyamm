"""Analyse hand pieces: principal-axis end points and chain links. Args: -- <parts blend>"""
import bpy, sys, os
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
pieces = {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    c = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    m = c.mean(0)
    if abs(m[0]) > 0.39 and m[2] < 0.87:
        u, s, vt = np.linalg.svd(c - m, full_matrices=False)
        ax = vt[0]
        if ax[2] > 0: ax = -ax                       # axis points down (toward fingertips)
        t = (c - m) @ ax
        top, bot = m + ax * t.min(), m + ax * t.max()
        pieces[o.name] = (m, top, bot, t.max() - t.min())
for side, sgn in (('R', -1), ('L', 1)):
    names = [n for n, p in pieces.items() if np.sign(p[0][0]) == sgn]
    print('SIDE', side, len(names))
    for n in sorted(names, key=lambda n: -pieces[n][1][2]):
        m, top, bot, ln = pieces[n]
        # parent: piece whose bottom is closest to this top
        best = min(((np.linalg.norm(pieces[k][2] - top), k) for k in names if k != n), default=(9, None))
        print(f'  {n} len {ln*100:.1f}cm top {np.round(top,3)} bot {np.round(bot,3)} near-parent {best[1]} {best[0]*100:.1f}cm')
