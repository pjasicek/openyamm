#!/usr/bin/env python3
"""Club against the skin, every clip at 24 fps: club vertices and face centres, excluding the right hand; inside = behind the nearest skin vertex's normal within 6 cm. Also fingers inside the grip cylinder (rest, the fist is rigid with the club). Args: <glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
cnt = np.cumsum([0] + [len(p['positions']) for p in P])
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
T = np.vstack([p['triangles'].reshape(-1, 3) + o for p, o in zip(P, cnt)])
club = dom == 'Yclub'; rh = np.char.find(dom, 'R Hand') >= 0
skin = ~club & ~rh
ft = skin[T].all(1)
def X(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(P))])
rest = X(m.world({}))
ct = T[club[T].all(1)]
for clip in [a['name'] for a in m.glb.json['animations']]:
    d = m.clip_times(clip)[-1]; worst = 0; nf = 0
    for t in np.arange(0, d + 1e-6, 1 / 24):
        Q = X(m.world(m.sample(clip, float(t))))
        tri = Q[T[ft]]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        cen = tri.mean(1); tr = cKDTree(cen)
        pts = np.vstack([Q[club], Q[ct].mean(1)]); dd, ii = tr.query(pts, k=1)
        s = ((pts - cen[ii]) * n[ii]).sum(1); ins = (s < 0) & (dd < 0.06)
        dep = float(-s[ins].min()) if ins.any() else 0
        worst = max(worst, dep); nf += dep > 0.01
    print(f'{clip:13s} club in skin {worst * 100:4.1f} cm, frames over 1 cm {nf}', flush=True)
