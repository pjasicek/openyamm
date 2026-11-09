#!/usr/bin/env python3
"""After F1's tweak (tweak_pf1.py: ear plates smoothed and clamped, re-wound faces) and the chin sculpt, some head and old-hood faces beside
the cheeks and jaw lie within a few mm of PF4's new hood (it hugs the head there) or poke through it: black specks on the hood in the
viewer (hidden head texels Meshy never painted). Every head or old-hood vertex whose nearest point of the hood's outer surface is not on
the hood's last two rings where they hug the face (the opening edge: there the face shows) and that lies less than 2.5 mm under that surface (or
outside it) moves along the hood normal to 2.5 mm under it, with every row of the same asm vertex. Positions only.
Args: <uv_tex2 npz in> <out npz> <asm npz>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
U = dict(np.load(sys.argv[1])); A = np.load(sys.argv[3])
co, tri, comp, orig = U['co'].copy(), U['tri'], U['comp'], U['orig']; names = [str(x) for x in U['names']]
KH, KS, K4 = names.index('head'), names.index('scarf'), names.index('hood4')
par = A['f4_param']; twin = A['f4_twin_v']; Kr = par[comp == K4, 2].max() if False else par[A['comp'] == K4, 2].max()
ht = tri[(comp[tri] == K4).all(1) & (twin[orig[tri]] < 0).all(1)]
fn = np.cross(co[ht[:, 1]] - co[ht[:, 0]], co[ht[:, 2]] - co[ht[:, 0]]); fa = np.linalg.norm(fn, axis=1, keepdims=True); fn = fn / np.maximum(fa, 1e-12)
cen = co[ht].mean(1); ring = par[orig[ht], 2].min(1)
# the opening edge hugs the face (1.5 mm): hood faces within 5 mm of the head at rest are left out (the face shows there)
ac = A['co']; hd = cKDTree(ac[A['comp'] == A['names'].tolist().index('head')])
dh = hd.query(ac[orig[ht]].reshape(-1, 3))[0].reshape(-1, 3).min(1)
sel = ~((ring >= Kr - 2) & (dh < 0.005))
kd = cKDTree(cen); TOL = 0.0025
mv = np.where(np.isin(comp, [KH, KS]))[0]
total = 0
for it in range(4):
    d, j = kd.query(co[mv]); s = ((co[mv] - cen[j]) * fn[j]).sum(1)
    tol = np.where(comp[mv] == KS, 0.006, TOL)      # F1's old hood (hidden skull) kept deeper: its weights differ from the hood's in head turns
    bad = (d < 0.03) & sel[j] & (s > -tol)
    if not bad.any(): break
    tgt = co[mv[bad]] - (s[bad] + tol[bad])[:, None] * fn[j[bad]]
    av = {}
    for r, p in zip(mv[bad], tgt): av.setdefault(int(orig[r]), []).append(p)
    for r in mv:
        o = int(orig[r])
        if o in av: co[r] = np.mean(av[o], 0)
    total += int(bad.sum()); print('iter', it, 'pushed', int(bad.sum()))
# F1's old hood (the hidden skull; its weights differ from the new hood's in motion, so a few mm were not enough): every free old-hood
# vertex goes at least DEEP under the new hood along the ray from the head centre (seam vertices with the face stay)
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
DEEP = 0.012; Cc = np.array([0.0, 0.0, 0.665])
key = np.round(A['co'], 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
onh = np.zeros(inv.max() + 1, bool); onh[inv[A['comp'] == KH]] = True
sv = np.where((comp == KS) & ~onh[inv[orig]])[0]
dd = co[sv] - Cc; rr = np.linalg.norm(dd, axis=1); uu = dd / rr[:, None]
th = raycast(Cc + uu * 0.6, -uu, co, ht); rh = np.where(np.isfinite(th), 0.6 - th, np.inf)
newr = np.minimum(rr, rh - DEEP); newr = np.maximum(newr, 0.03)
pos = Cc + uu * newr[:, None]
av = {}
for r, p_ in zip(sv, pos): av.setdefault(int(orig[r]), []).append(p_)
for r in sv: co[r] = np.mean(av[int(orig[r])], 0)
print('OLDHOOD deepened rows', int((newr < rr - 1e-6).sum()), 'of', len(sv))
U['co'] = co; np.savez(sys.argv[2], **U); print('UNDERHOOD rows moved', total)
