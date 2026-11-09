#!/usr/bin/env python3
"""Plain bodice front (second review 2026-11-02: MM9's F4 has a plain fitted bodice; ours kept F1's laced bust: the lacing is modelled,
chevron bumps down the centre front that shade as lacing whatever the paint). Positions only, after puff_pf4.py (UVs and F1's weights
unchanged): dress vertices in the lacing column (|x| < 3 cm, 1.07-1.335 m over the soles, the front) are Laplacian-smoothed over the
dress's edges (60 passes; depth fully, sideways and height at 30 %), at most 12 mm, eased out over the column's last 8 mm.
Rows of one welded position move together. Args: <uv_tex2 npz in> <out npz>"""
import sys
import numpy as np
U = dict(np.load(sys.argv[1])); co, tri, comp = U['co'].copy(), U['tri'], U['comp']; names = [str(x) for x in U['names']]
kd = names.index('dress'); Z0 = -0.9297
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); n = inv.max() + 1
P = np.zeros((n, 3)); P[inv] = co
only = np.ones(n, bool); only[inv[comp != kd]] = False       # seam positions shared with other parts stay
df = tri[comp[tri[:, 0]] == kd]; T = inv[df]
e = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
zs = P[:, 2] - Z0
w = np.clip((0.03 - np.abs(P[:, 0])) / 0.008, 0, 1) * np.clip((zs - 1.07) / 0.01, 0, 1) * np.clip((1.335 - zs) / 0.01, 0, 1) * (P[:, 1] < -0.04) * only
z = w > 0; P0 = P.copy()
for _ in range(60):
    acc = np.zeros_like(P); dg = np.zeros(n); np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(dg, e[:, 0], 1); np.add.at(dg, e[:, 1], 1)
    L = acc / np.maximum(dg, 1)[:, None]; P[z] = P[z] + 0.5 * (L[z] - P[z])
d = P - P0
d[:, [0, 2]] *= 0.3
nn = np.linalg.norm(d, axis=1, keepdims=True); d = d * np.minimum(1, 0.012 / np.maximum(nn, 1e-12))
P = P0 + d * w[:, None]
# the lacing's separate small pieces (32-74 triangles, on top of the bodice) would float off the smoothed surface: each of their vertices
# in the column moves with its nearest main-bodice position (they cover holes in the bodice and ride with its rims)
par = np.arange(n)
def fnd(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in T:
    r = fnd(t[0]); par[fnd(t[1])] = r; par[fnd(t[2])] = r
rts = np.array([fnd(i) for i in range(n)]); dv = np.unique(T); cnt = np.bincount(rts[dv], minlength=n)
main = np.zeros(n, bool); main[dv] = cnt[rts[dv]] == cnt[rts[dv]].max()
small = np.zeros(n, bool); small[dv] = ~main[dv]
sm = small & (w > 0)
if sm.any():
    from scipy.spatial import cKDTree
    mi = np.where(main)[0]; _, j = cKDTree(P0[mi]).query(P0[sm])
    P[sm] = P0[sm] + (P[mi[j]] - P0[mi[j]])
    P[sm, 1] = P[sm, 1] + 0.75 * np.maximum((P[mi[j], 1] - 0.0008) - P[sm, 1], 0)      # their relief pressed 75 % toward the surface
print('BUST small lacing pieces carried', int(sm.sum()), 'positions')
mv = (w > 0)[inv]; co[mv] = P[inv][mv]; U['co'] = co; np.savez(sys.argv[2], **U)
print('BUST lacing column smoothed', int(z.sum()), 'positions, max mm', round(float(np.linalg.norm(d * w[:, None], axis=1).max() * 1000), 1))
