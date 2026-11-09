#!/usr/bin/env python3
"""F1's old hood ('scarf', kept as the hidden skull) poked green shards through the new hood beside the cheeks and jaw where a ray from
the head centre missed the hood (add_parts_pf4.py's pull is by ray). Here every free old-hood vertex (not on the head seam) within 3 cm of
the new hood's outer surface and less than 3 mm inside it (or outside) moves along the hood normal to 3 mm inside; the move is spread to
its old-hood neighbours (3 smoothing passes, never outward), repeated until none is left. Positions only (asm and uv npz rows).
Args: <asm npz> <uv npz> (both rewritten in place)"""
import sys
import numpy as np
from scipy.spatial import cKDTree
A_, U_ = sys.argv[1:3]
A = dict(np.load(A_)); U = dict(np.load(U_))
co, tri, comp = A['co'].copy(), A['tri'], A['comp']; names = [str(x) for x in A['names']]
KH, KS, K4 = names.index('head'), names.index('scarf'), names.index('hood4')
key = np.round(A['co'], 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
ch = np.zeros(inv.max() + 1, int); np.add.at(ch, inv[comp == KH], 1)
free = np.where((comp == KS) & (ch[inv] == 0))[0]
ht = tri[(comp[tri] == K4).all(1) & (A['f4_twin_face'][np.arange(len(tri))] < 0) if 'f4_twin_face' in A else (comp[tri] == K4).all(1)]
hv = np.unique(ht)
fn = np.cross(co[ht[:, 1]] - co[ht[:, 0]], co[ht[:, 2]] - co[ht[:, 0]]); vn = np.zeros_like(co)
for c in range(3): np.add.at(vn, ht[:, c], fn)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
# sample the hood surface densely (centroids + vertices) with normals
S = np.vstack([co[hv], co[ht].mean(1)]); SN = np.vstack([vn[hv], fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)])
kd = cKDTree(S)
st = tri[(comp[tri] == KS).all(1)]
e = np.unique(np.sort(np.vstack([st[:, [0, 1]], st[:, [1, 2]], st[:, [2, 0]]]), 1), axis=0)
isfree = np.zeros(len(co), bool); isfree[free] = True
moved_total = 0
for it in range(6):
    d, j = kd.query(co[free]); s = ((co[free] - S[j]) * SN[j]).sum(1)
    bad = (d < 0.03) & (s > -0.003)
    if not bad.any(): break
    disp = np.zeros_like(co); disp[free[bad]] = -(s[bad] + 0.003)[:, None] * SN[j[bad]]
    for _ in range(3):
        acc = np.zeros_like(co); cnt = np.zeros(len(co))
        np.add.at(acc, e[:, 0], disp[e[:, 1]]); np.add.at(acc, e[:, 1], disp[e[:, 0]]); np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
        sm = acc / np.maximum(cnt, 1)[:, None]
        disp = np.where((np.linalg.norm(sm, axis=1) > np.linalg.norm(disp, axis=1))[:, None] & isfree[:, None], sm, disp)
    co[isfree] += disp[isfree]; moved_total += int(bad.sum())
    print('iter', it, 'pushed', int(bad.sum()), 'max mm', round(float(np.linalg.norm(disp, axis=1).max()) * 1000, 1))
A['co'] = co; np.savez(A_, **A)
U['co'] = co[U['orig']]; np.savez(U_, **U)
print('SHARDS fixed', moved_total)
