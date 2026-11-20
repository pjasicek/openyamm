import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
mp = bpy.data.objects['MeshyPosed']
P = np.array([tuple(v.co) for v in mp.data.vertices])
F = [list(p.vertices) for p in mp.data.polygons]
L = []
for k, f in enumerate(F):
    e = max(np.linalg.norm(P[f[i]] - P[f[(i + 1) % len(f)]]) for i in range(len(f)))
    L.append(e)
L = np.array(L)
print('edge p50 p99 max', np.percentile(L, 50).round(3), np.percentile(L, 99).round(3), L.max().round(3))
idx = np.argsort(-L)[:30]
for k in idx:
    c = P[F[k]].mean(0)
    print('F', k, round(L[k], 2), c.round(2))
