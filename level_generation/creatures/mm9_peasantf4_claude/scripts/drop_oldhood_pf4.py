#!/usr/bin/env python3
"""F1's old hood lappets beside the cheeks and jaw (asm z < 0.66, in front of the ears, |x| > 5 cm) are dropped from the asm and the uv npz
(rows matched by their asm vertex triple; the paid layout of every other row unchanged). In motion they poked up to 1.2 cm through the
new hood's cape (their weights cannot match the cape's in head turns); behind them there is only the neck and the cape's lining.
Runs once after reline_pf4.py. Args: <asm in> <uv in> <asm out> <uv out> [gap m]"""
import sys
import numpy as np
A = dict(np.load(sys.argv[1])); U = dict(np.load(sys.argv[2]))
co, tri, comp = A['co'], A['tri'], A['comp']; names = [str(x) for x in A['names']]; KS = names.index('scarf')
c = co[tri].mean(1)
from scipy.spatial import cKDTree
hv = np.unique(tri[(comp[tri] == names.index('head')).all(1)]); dh = cKDTree(co[hv]).query(c)[0]
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
onh = np.zeros(inv.max() + 1, bool); onh[inv[hv]] = True
# only the hanging lappet faces: no vertex on the face/neck seam, centre more than GAP from the head shell (the strips that close the
# neck's sides under the jaw stay: without them the neck showed background from below)
GAP = float(sys.argv[5]) if len(sys.argv) > 5 else 0.008
drop = (comp[tri] == KS).all(1) & (c[:, 2] < 0.66) & (c[:, 1] < 0.02) & (np.abs(c[:, 0]) > 0.05) & ~onh[inv[tri]].any(1) & (dh > GAP)
keys = {tuple(sorted(t)) for t in tri[drop]}
keep = ~drop; newidx = -np.ones(len(tri), int); newidx[keep] = np.arange(keep.sum())
tf = A['f4_twin_face']; assert not drop[tf[tf >= 0]].any()
A['tri'] = tri[keep]
for k in ('f4_inner', 'f4_rim'): A[k] = A[k][keep]
A['f4_twin_face'] = np.where(tf[keep] >= 0, newidx[np.maximum(tf[keep], 0)], -1)
np.savez(sys.argv[3], **A)
ukeys = [tuple(sorted(U['orig'][t])) for t in U['tri']]
ukeep = np.array([k not in keys for k in ukeys])
U['tri'] = U['tri'][ukeep]; U['mat'] = U['mat'][ukeep]; U['inner'] = U['inner'][ukeep]
used = np.unique(U['tri']); remap = -np.ones(len(U['co']), int); remap[used] = np.arange(len(used))
for k in ('co', 'uv', 'orig', 'comp'): U[k] = U[k][used]
U['tri'] = remap[U['tri']]
np.savez(sys.argv[4], **U)
print('OLDHOOD lappet faces dropped', int(drop.sum()), 'uv rows dropped', int((~ukeep).sum()), 'tris', len(A['tri']))
