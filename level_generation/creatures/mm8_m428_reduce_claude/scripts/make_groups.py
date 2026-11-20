#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 female Dark Elf peasant (faces -y). Pieces after the weld: main shell (head skin, bodice, sleeves, dress and
underskirt), hair, two forearm+hand pieces, hidden legs with shoes, and small pieces (eyes, mouth, fringe, lacing,
belt, buckle, shoulder bands).
Labels: 0 rest (bodice, sleeves, dress, underskirt), 1 face and neck skin (main shell above 1.44 m: the production
reduction kept it at Smart Topology density), 2 hair piece, 3 left forearm+hand, 4 right forearm+hand (dagger fist),
5 hidden legs (above the shoes).
Kept exactly: pieces of up to 400 faces; the hair (REA_CUT_HAIR=1 leaves it to its group ratio); the shoes (leg piece
below 13 cm); the sleeve-cuff ruffles (main-shell faces with an arm-weighted vertex below 1.15 m, the ruffles that
fix_cuffs.py cut free of the dress) with one ring; dress faces within 5 cm of a ruffle vertex at the old bridge
site (|x| > 0.15 m, 0.8-1.15 m), so no collapse rebuilds the bridge; gold eyelets painted on the main shell with one
ring. REA_KEEP_RHAND=1 also keeps the right hand piece (dagger grip)."""
import os
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); W = np.load('work/vweights.npz')
f, v = d['faces'], d['verts']; c = v[f].mean(1)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
order = np.argsort(-sizes)
main, hair = order[0], order[1]
hands = [p for p in order[2:5] if 600 <= sizes[p] <= 800 and abs(c[pc == p, 0].mean()) > .25]
legs = next(p for p in order[2:6] if abs(c[pc == p, 0].mean()) < .05 and c[pc == p, 2].min() < .02)
assert len(hands) == 2, hands
rows = np.repeat(np.arange(len(f)), 3)
A = coo_matrix((np.ones(len(rows)), (rows, f.ravel())), shape=(len(f), n)).tocsr()
ring = lambda m: (A @ (A.T @ m.astype(float))) > 0
g = np.zeros(len(f), int)
g[(pc == main) & (c[:, 2] > 1.44)] = 1
g[pc == hair] = 2
for p in hands:
    g[pc == p] = 3 if c[pc == p, 0].mean() > 0 else 4
g[pc == legs] = 5
keep = size <= 400
if os.environ.get('REA_CUT_HAIR') != '1':
    keep |= pc == hair
shoes = (pc == legs) & (c[:, 2] < .13)
keep |= shoes
armw = np.maximum(W['arm_l'], W['arm_r'])
ruffle_v = (lab == main) & (armw >= .15) & (v[:, 2] < 1.15)
ruffle = (pc == main) & ruffle_v[f].any(1)
ruffle = ring(ruffle) & (pc == main)
keep |= ruffle
site = (lab == main) & ruffle_v & (np.abs(v[:, 0]) > .15) & (v[:, 2] > .8) & (v[:, 2] < 1.15)
near = np.zeros(len(f), bool)
if site.any():
    dist, _ = cKDTree(v[site]).query(c)
    near = (pc == main) & (dist < .05) & (W['dress'][f].max(1) >= .5)
keep |= near
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, Wd = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
p = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((p[..., 0] % 1 * Wd).astype(int), 0, Wd - 1); y = np.clip(((1 - p[..., 1] % 1) * H).astype(int), 0, H - 1)
col = img[y, x]
gold = (col[..., 0] > 150) & (col[..., 1] > 110) & (col[..., 2] < .6 * col[..., 1]) & (col[..., 0] - col[..., 2] > 70)
eyelet = (pc == main) & (g == 0) & gold.any(1)
keep |= ring(eyelet) & (pc == main) & (g == 0)
if os.environ.get('REA_KEEP_RHAND') == '1':
    keep |= g == 4
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('PIECES main', sizes[main], 'hair', sizes[hair], 'hands', [int(sizes[p]) for p in hands], 'legs', sizes[legs],
      'small', int((size <= 400).sum()))
print('KEEP shoes', int(shoes.sum()), 'ruffle', int(ruffle.sum()), 'bridge site', int(near.sum()), 'eyelets', int(eyelet.sum()),
      'with ring', int((ring(eyelet) & (pc == main) & (g == 0)).sum()))
print('GROUPS (not kept)', {k: int(((g == k) & ~keep).sum()) for k in range(6)}, 'keep', int(keep.sum()))
