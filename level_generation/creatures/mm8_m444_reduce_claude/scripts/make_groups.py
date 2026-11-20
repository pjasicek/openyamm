#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 Smuggler, human form (faces -y; one 2080x1024 atlas, body left, head image from x = 1056). Material classes
come from the production class maps (mm8_m444_claude/textures/*material_classes.png: skin 1, hair 2, eyes 6, mouth 7,
cloth/leather 8, metal 9), sampled at each face's three corners and centre.
Labels: 0 rest (tunic, trousers, boots, bandolier, sheath), 1 head piece (face, bald scalp, beard, ears, neck),
3 left hand, 4 right hand (faces dominated by a hand or finger bone).
Kept exactly: the separate head-atlas pieces (eyes, mouth interior), head faces with any eye or mouth texels, head
faces within REA_LID_R (default 8 mm) of those pieces (lids, lips; the head piece carries no eye/mouth class), body faces with metal texels (buckles, studs), pieces of up to REA_SMALL faces (default 40), the soles (faces
below 1.5 cm) and, with REA_KEEP_RHAND=1 (default), the sword hand: right hand and finger faces (fitted grip)."""
import os
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
wuv = d['wuv'].reshape(-1, 3, 2); c = v[f].mean(1); head = info['u'] > .505; dom = info['dom']
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mm8_m444_claude', 'textures')
HC = np.asarray(Image.open(os.path.join(T, 'smuggler_head_material_classes.png')))
BC = np.asarray(Image.open(os.path.join(T, 'smuggler_material_classes.png')))
pts = np.concatenate([wuv, wuv.mean(1, keepdims=True)], 1)          # (F, 4, 2)
x = pts[..., 0] * 2080; y = np.clip(((1 - pts[..., 1]) * 1024).astype(int), 0, 1023)
cls = np.where(x >= 1056, HC[y, np.clip((x - 1056).astype(int), 0, 1023)], BC[y, np.clip(x.astype(int), 0, 1023)])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
head_piece = max((p for p in np.unique(pc[head]) if head[pc == p].all()), key=lambda p: sizes[p])
g = np.zeros(len(f), int)
g[pc == head_piece] = 1
lhand = np.array([b.startswith(('B_L_Hand', 'B_L_Finger')) for b in dom])
rhand = np.array([b.startswith(('B_R_Hand', 'B_R_Finger')) for b in dom])
g[lhand] = 3; g[rhand] = 4
eye_mouth = head & np.isin(cls, (6, 7)).any(1)
metal = ~head & (cls == 9).any(1)
keep = head & (pc != head_piece)
from scipy.spatial import cKDTree
near = cKDTree(v[np.unique(f[keep])]).query(c, distance_upper_bound=float(os.environ.get('REA_LID_R', '0.008')))[0]
lids = (pc == head_piece) & np.isfinite(near)
keep |= lids
keep |= eye_mouth | metal
keep |= size <= int(os.environ.get('REA_SMALL', '40'))
keep |= v[f][:, :, 2].max(1) < 0.015
if os.environ.get('REA_KEEP_RHAND', '1') == '1':
    keep |= rhand
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep); np.save('work/face_cls.npy', cls)
print('GROUPS free', {k: int(((g == k) & ~keep).sum()) for k in (0, 1, 3, 4)}, 'keep', int(keep.sum()),
      'eye/mouth pieces', int((head & (pc != head_piece)).sum()), 'lids/lips', int(lids.sum()), 'metal', int(metal.sum()),
      'small pieces', int((size <= int(os.environ.get('REA_SMALL', '40'))).sum()), 'rhand', int(rhand.sum()),
      'soles', int((v[f][:, :, 2].max(1) < 0.015).sum()))
