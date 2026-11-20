#!/usr/bin/env python3
"""Fre pass 4 (PeasantF2's hair transplant, component 'hair2'): replaces under_hood_pf4.py in geo_chain_fre.sh. After the chain's face
tweaks (ear plates, chin), every head-shell or hidden old-hood row that the hair cap covers (ray from the head centre) and that lies less
than CLR under the cap or outside it moves along its ray to CLR under it, with every row of the same asm vertex. Rows on the neckline seam
with the bodice and the braid tube are left alone. Positions only. Args: <uv npz in> <out npz>   (project folder; work/asm_frozen.npz)"""
import sys, os
import numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
U = dict(np.load(sys.argv[1])); A = np.load('work/asm_frozen.npz')
co, tri, comp, orig = U['co'].copy(), U['tri'], U['comp'], U['orig']; names = [str(x) for x in U['names']]
KH, KS, K2, KD = (names.index(x) for x in ('head', 'scarf', 'hair2', 'dress'))
CLR = float(os.environ.get('CLR', '0.004')); C = np.array([0.0, 0.0, 0.665])
tube = A['hair2_tube'][orig]
capT = tri[(comp[tri] == K2).all(1) & ~tube[tri].any(1)]
# asm vertices shared with the bodice (the neckline) stay
key = np.round(A['co'], 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
nd = np.zeros(inv.max() + 1, int); np.add.at(nd, inv[A['comp'] == names.index('dress')], 1)
q = np.where(np.isin(comp, [KH, KS]) & (co[:, 2] > 0.55) & (nd[inv[orig]] == 0))[0]
d = co[q] - C; r = np.linalg.norm(d, axis=1); u = d / r[:, None]
t = raycast(C + u * 0.6, -u, co, capT); rh = 0.6 - t
mv = np.isfinite(t) & (rh > 0.05) & (r > rh - CLR) & (r - (rh - CLR) < 0.03)
tgt = {}
for v, p in zip(q[mv], C + u[mv] * (rh[mv] - CLR)[:, None]):
    tgt.setdefault(inv[orig[v]], p)
rows = np.where(np.isin(inv[orig], list(tgt.keys())))[0]
dist = np.array([np.linalg.norm(tgt[inv[orig[v]]] - co[v]) for v in rows]) if len(rows) else np.zeros(1)
for v in rows: co[v] = tgt[inv[orig[v]]]
U['co'] = co; np.savez(sys.argv[2], **U)
print('UNDER_HAIR2 rows moved', len(rows), 'max mm', round(float(dist.max()) * 1000, 2))
