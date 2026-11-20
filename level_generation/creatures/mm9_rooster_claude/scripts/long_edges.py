"""List faces of 'Body' with an edge longer than a threshold. Args: blend thr"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
P = np.array([tuple(v.co) for v in me.vertices])
part = me.attributes.get('part')
out = {}
for p in me.polygons:
    vs = list(p.vertices)
    L = max(np.linalg.norm(P[vs[i]] - P[vs[(i + 1) % len(vs)]]) for i in range(len(vs)))
    if L > float(a[1]):
        k = part.data[p.index].value if part else -1
        out.setdefault(k, []).append((round(float(L), 3), P[vs].mean(0).round(3).tolist()))
for k, v in out.items():
    print('LONG part', k, len(v), sorted(v, reverse=True)[:6])
