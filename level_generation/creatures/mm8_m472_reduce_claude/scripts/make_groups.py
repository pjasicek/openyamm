#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
Labels: 0 rest (robe, cuirass, slippers, sleeves), 1 face skin (head set, Head-dominant, front of the head below the
hairline), 2 hair and scalp (rest of the head set), 3 hands and fingers, 4 lining (mostly covered by the cuirass),
5 skull cords. Kept exactly: eyes and the small face pieces (pieces of up to 250 faces in the head set).
Rune faces (region mask red under the face) are counted, not kept: see the README."""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom']; head = info['u'] > .505
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; size = np.bincount(pc)[pc]
g = np.zeros(len(f), int)
face = head & (dom == 'B_Head') & (c[:, 1] < -0.06) & (c[:, 2] < 1.655)
g[head & ~face] = 2; g[face] = 1
hands = np.array([('Hand' in x) or ('Finger' in x) for x in dom])
g[hands & ~head] = 3
big = np.bincount(pc).argsort()[::-1]
lining = pc == [p for p in big[:4] if abs(c[pc == p][:, 2].mean() - 1.298) < .02][0]
g[lining] = 4
cords = (~head) & (size > 300) & (size < 450) & (np.abs(c[:, 1] + .19) < .05) & (c[:, 2] < 1.0)
g[cords] = 5
keep = head & (size <= 250)
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
mask = np.asarray(Image.open('work/regionmask.png'))[..., 0] > 127
uv = d['wuv'].reshape(-1, 3, 2).mean(1); H, W = mask.shape
rune = mask[np.clip(((1 - uv[:, 1] % 1) * H).astype(int), 0, H - 1), np.clip((uv[:, 0] % 1 * W).astype(int), 0, W - 1)]
np.save('work/rune_faces.npy', rune)
print('GROUPS', {k: int((g == k).sum()) for k in range(6)}, 'keep', int(keep.sum()), 'rune faces', int(rune.sum()))
