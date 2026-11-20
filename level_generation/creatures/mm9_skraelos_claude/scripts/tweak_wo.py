#!/usr/bin/env python3
"""Igrid geometry tweaks after the paint (positions only, UVs unchanged; no face-shell vertex moves).
1. The circlet gem (Meshy's shield-shaped forehead piece, 3.6 x 3.4 cm, read as a crown ornament): scaled GEMS about its back centre and
   set onto the forehead (MM9's circlet stone is small).
Writes <out asm npz> and <out uv npz> (uv npz co = tweaked asm co[orig]). Args: <asm npz> <uv npz> <out asm npz> <out uv npz>"""
import sys, os
import numpy as np
A, U, OA, OU = sys.argv[1:5]
S = dict(np.load(A)); co, tri, comp = S['co'].copy(), S['tri'], S['comp']; names = [str(x) for x in S['names']]
H = names.index('head'); hv = np.where(comp == H)[0]; ht = tri[np.isin(tri[:, 0], hv)]
par = {v: v for v in hv}
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in ht: r = f(a); par[f(b)] = r; par[f(c)] = r
root = np.array([f(v) for v in hv]); u, cnt = np.unique(root, return_counts=True)
gr = [r for r, n in zip(u, cnt) if n < 200 and abs(co[r, 0]) < 0.03 and co[r, 2] > 0.57 and co[r, 1] < -0.3]
g = hv[np.isin(root, gr)]; G = co[g]
c = G.mean(0); back = c.copy(); back[1] = G[:, 1].max()
GEMS = float(os.environ.get('GEMS', '0.5'))
co[g] = back + (G - back) * GEMS
print('GEM', len(g), 'verts, size', np.ptp(G, 0).round(4), '->', np.ptp(co[g], 0).round(4))
# 2. Legs (review r9: the shoes came out under the robe in Death / Dead, robe gate 7.8 cm): Meshy's shoes are 24 cm boots and the shin tube
#    reached the knee; everything above BOOTTOP over the floor is compressed to BOOTK of its height (low shoes, a short stub inside the hem).
L_ = names.index('legs'); lv = np.where(comp == L_)[0]; Z0 = -0.923; t0 = Z0 + float(os.environ.get('BOOTTOP', '0.09')); BK = float(os.environ.get('BOOTK', '0.12'))
zz = co[lv, 2]; hi = zz > t0; zmax = zz.max()
co[lv[hi], 2] = t0 + (zz[hi] - t0) * BK
print('LEGS top', round(float(zmax), 3), '->', round(float(co[lv, 2].max()), 3))
# 3. The forearm stubs of the grafted hands (inside the cuffs) poked 24 mm through the right sleeve in Fidget (sleeve_poke_gate): the stub
#    behind the wrist is shortened to STUBK of its length and narrowed to STUBN of its radius toward the arm axis.
Hh = names.index('hands'); hv2 = np.where(comp == Hh)[0]; wr0, ax0 = S['wr'], S['ax']
STUBK, STUBN = float(os.environ.get('STUBK', '0.6')), float(os.environ.get('STUBN', '0.8'))
nst = 0
for sg in (1, -1):
    w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]; q = hv2[co[hv2, 0] * sg > 0]
    al = (co[q] - w) @ a; b = al < -0.005
    rv = co[q] - w - al[:, None] * a
    f = np.clip((-al - 0.005) / 0.02, 0, 1)
    al2 = np.where(b, -0.005 + (al + 0.005) * (1 - (1 - STUBK) * f), al)
    rv2 = rv * np.where(b, 1 - (1 - STUBN) * f, 1)[:, None]
    co[q] = w + al2[:, None] * a + rv2; nst += int(b.sum())
print('STUB verts', nst, 'length x', STUBK, 'radius x', STUBN)
S['co'] = co; np.savez(OA, **S)
D = dict(np.load(U)); D['co'] = co[D['orig']]; np.savez(OU, **D); print('TWEAKED', OA, OU)
