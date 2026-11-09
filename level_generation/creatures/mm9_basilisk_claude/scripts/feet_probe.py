"""Print foot clusters (lowest vertices) of the aligned Meshy mesh and the MM9 bind mesh. Args: <align blend>"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
def pts(o):
    return np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
M = pts(bpy.data.objects['Meshy'])
A = np.concatenate([pts(o) for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Meshy'])
for name, X in (('meshy', M), ('mm9', A)):
    low = X[X[:, 2] < 0.06]
    print(name, 'low verts', len(low), 'y range', X[:, 1].min().round(3), X[:, 1].max().round(3), 'z max', X[:, 2].max().round(3))
    for side in (1, -1):
        s = low[np.sign(low[:, 0]) == side]
        ys = np.sort(s[:, 1])
        # split into 3 groups by the two biggest gaps
        gaps = np.argsort(np.diff(ys))[-2:]
        cuts = sorted(ys[g] + 1e-6 for g in gaps)
        for lo, hi in ((-9, cuts[0]), (cuts[0], cuts[1]), (cuts[1], 9)):
            g = s[(s[:, 1] > lo) & (s[:, 1] <= hi)]
            print('  side', side, 'n', len(g), 'centroid', g.mean(0).round(3), 'x', g[:, 0].min().round(3), g[:, 0].max().round(3))
