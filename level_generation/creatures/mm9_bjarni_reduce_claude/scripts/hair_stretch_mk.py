#!/usr/bin/env python3
"""PeasantM5 hair-shell stretch gate (crown-streak fix, 2026-11-05; after beard_gate_m5.py): the hair shell = the head primitive's
second-largest non-hand component (the scalp cap). Per clip at 48 fps: the largest posed/rest length ratio over every hair edge and
over the edges of at least 5 mm (rest). Usage: hair_stretch_m5.py <glb> <out json>"""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
g = Glb(Path(sys.argv[1])); m = Model(g)
prim = g.json['meshes'][next(n['mesh'] for n in g.json['nodes'] if n.get('name') == 'Bjarni' and 'mesh' in n)]['primitives']
kh = [g.json['materials'][p['material']]['name'] for p in prim].index('BjarniHead')
rh = m.skinned_positions(m.world({}))[kh][0]
T = np.asarray(m.primitives[kh]['triangles']).reshape(-1, 3)
_, w = np.unique(np.round(rh, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; c = rh[T].mean(1)
comps = sorted([k for k in np.unique(fl) if np.abs(c[fl == k][:, 0]).max() < 0.3], key=lambda k: -(fl == k).sum())
hf = fl == comps[1]
E_ = np.unique(np.sort(np.vstack([T[hf][:, [0, 1]], T[hf][:, [1, 2]], T[hf][:, [2, 0]]]), 1), axis=0)
L0 = np.linalg.norm(rh[E_[:, 0]] - rh[E_[:, 1]], axis=1); E_, L0 = E_[L0 > 1e-4], L0[L0 > 1e-4]; big = L0 >= 0.005
res = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; sa = sb = 0.0
    for t in np.append(np.arange(0, t1, 1 / 48), t1):
        ph = m.skinned_positions(m.world(m.sample(clip, t)))[kh][0]
        r = np.linalg.norm(ph[E_[:, 0]] - ph[E_[:, 1]], axis=1) / L0
        sa = max(sa, float(r.max())); sb = max(sb, float(r[big].max()) if big.any() else 0.0)
    res[clip] = {'stretch_all': round(sa, 3), 'stretch_5mm': round(sb, 3)}
    print(f'{clip:12s} hair stretch all {sa:.3f}  edges >= 5 mm {sb:.3f}')
print('HAIR faces', int(hf.sum()), 'edges', len(E_), '>= 5 mm', int(big.sum()))
json.dump({'hair_faces': int(hf.sum()), 'clips': res}, open(sys.argv[2], 'w'), indent=1)
