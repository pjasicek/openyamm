#!/usr/bin/env python3
"""Gog per-region budgets for decimate_tex.py (REA_GROUPS / REA_KEEP_FACES). Material classes from the runtime
specular mask (metal-rough red: 64 skin, 255 keratin = horns, claws, spines, tail barb, teeth; 128 tongue).
Kept exactly: the head's small pieces (teeth, tongue, mouth cap, back-of-head cap), the yellow eyes (base colour)
and the lips (head faces within 1.5 cm of a tooth) with one ring of neighbours, soles (faces below 2 cm).
Groups: 1 head skin, 2 horns (head keratin), 3 claws (keratin on hand, finger, foot and toe bones), 4 hand and foot
skin, 5 spines (tail spine pieces and keratin on the back, shoulders and tail), 0 the body.
-> work/groups.npy, work/keep.npy (prints the counts)"""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
fb = np.load('work/face_bones.npz'); names = [str(n) for n in fb['names']]; bone = np.array([names[i] for i in fb['dom']])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; small = np.bincount(fl)[fl] <= 200


def sample(img):
    a = np.asarray(Image.open(img).convert('RGB'), np.float32); H, W = a.shape[:2]
    uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 16)
    su = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
    return np.median(a[y, x], 1)


spec = sample('work/img1.png')[:, 0]; col = sample('work/img0.png')
ker = spec > 190
head = bone == 'B_Head'
eye = head & (col[:, 0] > 140) & (col[:, 1] > 120) & (col[:, 2] < 90)
teeth_v = np.unique(f[small & head & ker])
lips = head & ~small & (cKDTree(v[teeth_v]).query(v[f].mean(1))[0] < .015)
vs = np.zeros(n, bool); vs[f[eye | lips].ravel()] = True; ring = vs[f].any(1) & head
sole = v[f][:, :, 2].max(1) < .02
tailspine = small & np.char.startswith(bone, 'Tail')
keep = (small & ~tailspine) | ring | sole
limb = np.char.find(bone, 'Finger') >= 0
limb |= np.isin(bone, ['B_L_Hand', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'])
g = np.zeros(len(f), int)
g[head & ~ker] = 1; g[head & ker] = 2; g[limb & ker] = 3; g[limb & ~ker] = 4
g[(ker & ~head & ~limb) | tailspine] = 5
g[keep] = 0
np.save('work/keep.npy', keep); np.save('work/groups.npy', g)
print('faces', len(f), 'small', small.sum(), 'tail spines', tailspine.sum(), 'eyes', eye.sum(), 'lips', lips.sum(),
      'ring', ring.sum(), 'sole', sole.sum(), 'keep', keep.sum())
print('groups: head skin', (g == 1).sum(), 'horns', (g == 2).sum(), 'claws', (g == 3).sum(), 'hand/foot skin',
      (g == 4).sum(), 'spines', (g == 5).sum(), 'body', ((g == 0) & ~keep).sum())
