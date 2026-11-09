#!/usr/bin/env python3
"""Which forearm skin vertices stand outside the sleeve cloth, per clip: the sleeve gate's radial ray test, against cloth
only. Usage: forearm_poke.py <glb> [json out]"""
import sys, json
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
import numpy as np
path = sys.argv[1]
m = Model(Glb(path)); d = m.glb.json
names = [d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
nodes = [d['nodes'][p['node']].get('name', '') for p in m.primitives]
print(sorted(set(nodes)))
cloth = next(i for i, p in enumerate(m.primitives) if p['skinned'] and p['positions'][:, 1].min() < 0.05)
skin = [i for i, p in enumerate(m.primitives) if p['skinned'] and i != cloth and p['node'] == m.primitives[cloth]['node']]
print('cloth', cloth, 'skin', skin)
jn = {n: j for j, n in enumerate(names)}
res = {}
for S in 'LR':
    fa, ha = jn[f'Bip01 {S} Forearm'], jn[f'Bip01 {S} Hand']
    for sk in skin:
        p = m.primitives[sk]; dom = p['joints'][np.arange(len(p['weights'])), p['weights'].argmax(1)]
        ids = np.where(dom == fa)[0]
        out = {}
        for clip in m.glb.json['animations']:
            c = clip['name']; ts = m.clip_times(c); ts = np.unique(np.round(np.linspace(ts[0], ts[-1], 13), 4))
            for t in ts:
                w = m.world(m.sample(c, t)); X = m.skinned_positions(w)
                pal = w[m.joints if hasattr(m, 'joints') and False else d['skins'][0]['joints']]
                e, h = pal[fa][:3, 3], pal[ha][:3, 3]
                ax = (h - e) / np.linalg.norm(h - e); u = np.cross(ax, [0.3, 0.9, 0.1]); u /= np.linalg.norm(u); v = np.cross(ax, u)
                T = m.primitives[cloth]['triangles']; C = X[cloth][0] if isinstance(X[cloth], tuple) else X[cloth]
                tri = C[T]; c0 = tri.mean(1); s = np.clip((c0 - e) @ ax, -0.05, 0.4); near = np.linalg.norm(c0 - (e + s[:, None] * ax), axis=1) < 0.3
                tri = tri[near]
                V = (X[sk][0] if isinstance(X[sk], tuple) else X[sk])[ids]
                dirs = np.array([u * np.cos(k * np.pi / 6) + v * np.sin(k * np.pi / 6) for k in range(12)])
                a = tri[:, 0]; e1 = tri[:, 1] - a; e2 = tri[:, 2] - a
                for dd in dirs:
                    h_ = np.cross(dd, e2); det = (e1 * h_).sum(1); ok = np.abs(det) > 1e-12
                    S_ = V[:, None] - a[None]
                    with np.errstate(divide='ignore', invalid='ignore'):
                        uu = (S_ * h_[None]).sum(2) / det; q = np.cross(S_, e1); vv = (q * dd).sum(2) / det; tt = (q * e2).sum(2) / det
                    hit = (ok[None] & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tt > 0)).any(1)
                    for i in np.where(~hit)[0]:
                        out.setdefault(int(ids[i]), set()).add(c)
        if not len(ids): continue
        P = p['positions'][list(out)] if out else np.zeros((0, 3))
        print(S, 'prim', sk, 'forearm verts', len(ids), 'out', len(out), 'clips', sorted({x[:5] for v_ in out.values() for x in v_}))
        res[f'{S}{sk}'] = sorted(out)
        if len(P):
            print('  rest bbox', np.round(P.min(0), 3).tolist(), np.round(P.max(0), 3).tolist())
if len(sys.argv) > 2:
    json.dump(res, open(sys.argv[2], 'w'))
