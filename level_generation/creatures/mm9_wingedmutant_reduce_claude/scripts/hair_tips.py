#!/usr/bin/env python3
"""Hair lock tips kept exactly (fix pass b: the half-edge collapse took tip vertices of the thin locks, which then ended
up to 52 mm short in Hit2). Per hair component (mesh_in faces of head kind 3): geodesic distance from the vertex nearest the
head joint; tips = local maxima further than 5 cm; faces with a vertex within TIP_R (geodesic) of a tip are locked.
Usage: hair_tips.py <TIP_R m> <out .npy>"""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
R, out = float(sys.argv[1]), sys.argv[2]
s = np.load(HERE / 'work' / 'mesh_in.npz'); L = np.load(HERE / 'work' / 'glb_labels.npz'); v, f = s['verts'], s['faces']
hair = (L['prim'] == 2) & (L['kind'] == 3)
m = Model(Glb(str(HERE / 'before' / 'mm9_wingedmutant.glb'))); names = [m.glb.json['nodes'][j]['name'] for j in m.joints]
hj = np.linalg.inv(m.inverse_binds[names.index('Bip01 Head')])[:3, 3]; hj = np.array([hj[0], -hj[2], hj[1]])
hf = f[hair]; e = np.concatenate([hf[:, [0, 1]], hf[:, [1, 2]], hf[:, [2, 0]]])
w = np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(v),) * 2).tocsr()
hv = np.unique(hf); _, comp = connected_components(G, directed=False)
tips = []
for c in np.unique(comp[hv]):
    cv = hv[comp[hv] == c]; root = cv[np.argmin(np.linalg.norm(v[cv] - hj, axis=1))]
    d = dijkstra(G, indices=root)
    for x in cv:
        nb = G.indices[G.indptr[x]:G.indptr[x + 1]]
        if d[x] > 0.05 and np.isfinite(d[x]) and (d[nb] <= d[x] + 1e-9).all():
            tips.append(x)
dt = dijkstra(G, indices=tips, min_only=True)
near = dt < R
lock = hair & near[f].any(1)
np.save(out, lock); print('HAIRTIPS', len(tips), 'tips;', int(lock.sum()), 'of', int(hair.sum()), 'hair faces locked within', R, 'm')
