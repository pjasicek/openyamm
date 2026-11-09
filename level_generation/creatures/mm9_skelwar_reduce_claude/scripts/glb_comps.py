#!/usr/bin/env python3
"""Connected components (position-welded) of each LOD0 primitive of a GLB, with dominant bone, triangle count,
size and closedness. Args: <glb> [out npz]. Writes per-face comp id, primitive, dominant bone name."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g)
names = [g.json['nodes'][j].get('name') for j in m.joints]
mats = [g.json['materials'][p['material']]['name'] for p in g.json['meshes'][0]['primitives']]
allc, allp, allb, allf = [], [], [], []
off = 0
for pi, p in enumerate(m.primitives):
    P, T = p['positions'], p['triangles']
    key = np.round(P / 1e-6).astype(np.int64)
    _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
    t = wid[T]; n = wid.max() + 1
    r = np.concatenate([t[:, 0], t[:, 1], t[:, 2]]); c = np.concatenate([t[:, 1], t[:, 2], t[:, 0]])
    nc, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fl = lab[t[:, 0]]
    # dominant bone per face: max weight joint of first vertex
    jw = p['joints'][np.arange(len(P)), p['weights'].argmax(1)]
    fb = jw[T[:, 0]]
    print(f'== prim {pi} {mats[pi]} tris {len(T)} comps {nc}')
    rows = []
    for k in range(nc):
        s = np.where(fl == k)[0]
        bones, cnt = np.unique(fb[s], return_counts=True)
        # open edges
        e = np.sort(np.concatenate([t[s][:, [0, 1]], t[s][:, [1, 2]], t[s][:, [2, 0]]]), 1)
        _, ec = np.unique(e, axis=0, return_counts=True)
        vs = P[np.unique(T[s])]
        rows.append((len(s), k, names[bones[cnt.argmax()]], int((ec == 1).sum()), np.ptp(vs, 0).max(), vs.mean(0)))
    rows.sort(key=lambda r: -r[0])
    for r in rows:
        print(f'  c{r[1]:3d} tris {r[0]:5d} bone {r[2]:24s} open {r[3]:4d} size {r[4]*100:6.1f}cm cen {np.round(r[5],3)}')
    allc.append(fl + off); off += nc; allp.append(np.full(len(T), pi)); allb.append(np.array(names)[fb])
if len(sys.argv) > 2:
    np.savez(sys.argv[2], comp=np.concatenate(allc), prim=np.concatenate(allp), bone=np.concatenate(allb))
