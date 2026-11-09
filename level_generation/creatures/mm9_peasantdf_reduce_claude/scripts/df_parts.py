#!/usr/bin/env python3
"""Per-face part labels of a PeasantDF LOD0 (default DF1) for the keep sets, with twin roles. Prints a table.
Body prim (0): twin roles; pieces by connected component of the outer faces. Head prim (1): head skin, ears, hair shell
(+ twin), hands, braids (DF3). Writes work/df_parts_<n>.npz."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbio
from twins import find_twins
n = sys.argv[1] if len(sys.argv) > 1 else '1'
doc, binary, nd, D = glbio.load(f'before/mm9_peasantdf{n}.glb', 'PeasantDF')
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
out = {}
for pi, (mat, A) in enumerate(D.items()):
    P, T = A['P'], A['T']
    role, partner, vmap = find_twins(P, A['UV'], A['W'], T)
    _, wid = np.unique(np.round(P, 6), axis=0, return_inverse=True); wid = wid.ravel(); WT = wid[T]; nv = wid.max() + 1
    r = np.r_[WT[:, 0], WT[:, 1], WT[:, 2]]; c = np.r_[WT[:, 1], WT[:, 2], WT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nv, nv)), directed=False)
    comp = lab[WT[:, 0]]
    # dominant joint per face
    dj = A['J'][T[:, 0], 0]
    print(f'== prim{pi} {mat}: tris {len(T)} outer-with-twin {int((role == 1).sum())} twins {int((role == 2).sum())} plain {int((role == 0).sum())}')
    for cl in sorted(np.unique(comp), key=lambda x: -(comp == x).sum()):
        m = comp == cl
        if m.sum() < 30: continue
        vs = np.unique(T[m]); lo, hi = P[vs].min(0), P[vs].max(0)
        js = np.bincount(dj[m], minlength=len(jn)); top = [jn[i] for i in np.argsort(-js)[:3] if js[i]]
        print(f'  comp {cl:3d} {m.sum():5d} outer {int((role[m] == 1).sum()):5d} twin {int((role[m] == 2).sum()):5d} {top} y {lo[1]:.3f}..{hi[1]:.3f} x {lo[0]:.3f}..{hi[0]:.3f}')
    out[f'role{pi}'] = role; out[f'partner{pi}'] = partner; out[f'comp{pi}'] = comp
    out[f'vmap{pi}'] = np.array(sorted(vmap.items()), np.int64).reshape(-1, 2)
np.savez(f'work/df_parts_{n}.npz', **out)
