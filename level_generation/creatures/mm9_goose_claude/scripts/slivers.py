"""List sliver triangles of 'Body' below a height. Args: <blend> <zmax> [min long edge] [max altitude]"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
z = float(argv[1]); ml = float(argv[2]) if len(argv) > 2 else 0.015; alt = float(argv[3]) if len(argv) > 3 else 0.0025
me = bpy.data.objects['Body'].data
me.calc_loop_triangles()
P = np.array([tuple(v.co) for v in me.vertices])
out = []
for t in me.loop_triangles:
    a, b, c = P[list(t.vertices)]
    L = sorted([np.linalg.norm(a - b), np.linalg.norm(b - c), np.linalg.norm(c - a)])
    ar = np.linalg.norm(np.cross(b - a, c - a)) / 2
    h = 2 * ar / max(L[2], 1e-9)
    if L[2] > ml and h < alt and min(a[2], b[2], c[2]) < z:
        out.append((round(L[2], 4), round(h, 5), list(t.vertices), np.round((a + b + c) / 3, 3).tolist()))
print('SLIVERS', len(out))
for o in sorted(out, reverse=True)[:30]:
    print('S', o)
