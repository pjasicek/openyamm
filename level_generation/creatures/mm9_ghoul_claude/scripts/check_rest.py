import sys, numpy as np
from pygltflib import GLTF2
a = GLTF2().load('work/quick_clips.glb'); b = GLTF2().load('source/z1/zombie1_true.glb')
na = {n.name: n for n in a.nodes}; nb = {n.name: n for n in b.nodes}
md = 0
for k, n in nb.items():
    if k in na and n.mesh is None:
        qa = np.array(na[k].rotation or [0, 0, 0, 1]); qb = np.array(n.rotation or [0, 0, 0, 1])
        d = min(np.linalg.norm(qa - qb), np.linalg.norm(qa + qb))
        ta = np.array(na[k].translation or [0, 0, 0]); tb = np.array(n.translation or [0, 0, 0])
        md = max(md, d)
        if d > 1e-3 or np.linalg.norm(ta - tb) > 1e-3: print(k, 'dq', round(d, 4), 'T', ta.round(3), tb.round(3))
print('max dq', md)
