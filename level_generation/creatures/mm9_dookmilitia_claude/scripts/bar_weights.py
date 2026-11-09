"""Print the cheek bars' skin weights in a runtime GLB (diagnosis): bar_weights.py <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose
g = glb_pose.Glb(sys.argv[1]); J = g.json
skin = J['skins'][0]; names = [J['nodes'][j].get('name') for j in skin['joints']]
for mi, m in enumerate(J['meshes']):
    if 'LOD' in m.get('name', '') or 'hadow' in m.get('name', ''): continue
    for pi, p in enumerate(m['primitives']):
        a = p['attributes']; P = g.accessor(a['POSITION']); I = g.accessor(p['indices'])[:, 0].astype(int).reshape(-1, 3)
        Jt = g.accessor(a['JOINTS_0']).astype(int); W = g.accessor(a['WEIGHTS_0'])
        key = np.round(P / 1e-5).astype(np.int64); _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
        par = np.arange(wid.max() + 1)
        def f(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for t in I:
            a_, b_, c_ = f(wid[t[0]]), f(wid[t[1]]), f(wid[t[2]]); par[b_] = a_; par[f(c_)] = a_
        comp = np.array([f(w) for w in wid]); u, cnt = np.unique(comp[I[:, 0]], return_counts=True)
        for c, n in zip(u, cnt):
            if n != 48: continue
            vs = np.where(comp == c)[0]
            print(m.get('name'), pi, 'component tris', n, 'verts', len(vs), 'mean', P[vs].mean(0).round(3))
            acc = {}
            for v in vs:
                for j, w in zip(Jt[v], W[v]):
                    if w > 0: acc[names[j]] = acc.get(names[j], 0) + w / len(vs)
            print('   ', sorted(((k, round(float(v), 3)) for k, v in acc.items()), key=lambda kv: -kv[1]))
