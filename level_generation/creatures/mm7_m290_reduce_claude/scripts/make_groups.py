#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 Cleric (faces -y, staff in the right hand). After the weld the body is a few large pieces: skin (face on the head
atlas, chest, arms, feet), robe top + collar + hair, the robe skirt, two hands; plus small pieces (eyes, sash, belt,
beads, wrist cuffs). Labels: 0 rest (robe, collar, skin), 1 face (head-atlas part of the skin piece), 2 hair (region
mask R, the hair ramp), 3 left hand, 4 right hand, 5 robe skirt (the large piece below the belt),
6 robe top and collar (the rest of the hair piece). The feet (skin below 15 cm, soles) are kept exactly: at 72 % the right
foot collapsed under the hem (80 mm at rest). Kept exactly: pieces of up to 250 faces (eyes, sash, belt, beads,
cuffs) and the right hand (fitted staff grip)."""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); u = info['u']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
mask = np.asarray(Image.open('work/tex_m460_region_mask_head_atlas.png'))[..., 0].astype(float) / 255; H, W = mask.shape
uv = d['wuv'].reshape(-1, 3, 2); p = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)
x = np.clip((p[..., 0] % 1 * W).astype(int), 0, W - 1); y = np.clip(((1 - p[..., 1] % 1) * H).astype(int), 0, H - 1)
hair = mask[y, x].mean(1) > .5
g = np.zeros(len(f), int)
skin_piece = pc[np.argmax((u > .505) & (info['dom'] == 'B_Head') & ~hair)]
g[(pc == skin_piece) & (u > .505) & ~hair] = 1
g[hair] = 2
hands = (size >= 600) & (size <= 1200) & (np.abs(c[:, 0]) > .4)
g[hands & (c[:, 0] > 0)] = 3; g[hands & (c[:, 0] < 0)] = 4
skirt = max((p for p in np.unique(pc) if sizes[p] > 250), key=lambda p: -c[pc == p, 2].mean())
g[pc == skirt] = 5
hair_piece = np.bincount(pc[hair]).argmax()
g[(pc == hair_piece) & (g == 0)] = 6
keep = (size <= 250) | (g == 4) | ((pc == skin_piece) & (g == 0) & (c[:, 2] < .15))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(7)}, 'keep', int(keep.sum()), 'hair', int(hair.sum()))
