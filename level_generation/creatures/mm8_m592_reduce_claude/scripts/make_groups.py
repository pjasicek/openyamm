#!/usr/bin/env python3
"""Plane Guardian per-region budgets for decimate_tex.py (REA_GROUPS / REA_KEEP_FACES):
keep exactly: small pieces (<= 80 faces: mane tufts, loose fangs), shiny head/jaw faces from the runtime specular
mask (red channel of the metal-rough map: eyes, teeth, gums) with one ring of neighbours, soles (faces below 4 cm);
group 1 head and jaw, group 2 claws (shiny finger faces: rigid cones, about 240 faces each), group 3 hands (claw bases
and palms), group 4 feet and toes, 0 the body (already economical: 1,576 faces for the whole torso).
-> work/groups.npy, work/keep.npy (prints the counts)"""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
fb = np.load('work/face_bones.npz'); names = [str(n) for n in fb['names']]; bone = np.array([names[i] for i in fb['dom']])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; small = np.bincount(fl)[fl] <= 80
spec = np.asarray(Image.open('work/img1.png').convert('RGB'), np.float32)[..., 0]; H, W = spec.shape
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 16)
su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
shiny = np.median(spec[y, x], 1) > 64
# one ring of neighbours around shiny faces (shared vertex)
head = np.isin(bone, ['B_Head', 'Jaw'])
finger = np.char.find(bone, 'Finger') >= 0
vs = np.zeros(n, bool); vs[f[shiny & head].ravel()] = True; ring = vs[f].any(1)
sole = v[f][:, :, 2].max(1) < .04
keep = small | ring | sole
claw = finger & shiny
hand = (finger | np.isin(bone, ['B_L_Hand', 'B_R_Hand'])) & ~claw
foot = np.isin(bone, ['B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'])
g = np.zeros(len(f), int); g[head] = 1; g[claw] = 2; g[hand] = 3; g[foot] = 4; g[keep] = 0
np.save('work/keep.npy', keep); np.save('work/groups.npy', g)
print('faces', len(f), 'small', small.sum(), 'shiny', shiny.sum(), 'ring', ring.sum(), 'sole', sole.sum(), 'keep', keep.sum(),
      'head', (g == 1).sum(), 'claws', (g == 2).sum(), 'hands', (g == 3).sum(), 'feet', (g == 4).sum(),
      'body', ((g == 0) & ~keep).sum())
for b in ['B_Head', 'Jaw', 'B_L_Hand', 'B_L_Finger0', 'B_L_Finger1', 'B_L_Finger2', 'B_Spine2', 'B_L_Foot']:
    m = bone == b; print(f'  {b:12s} faces {m.sum():5d} shiny {(shiny & m).sum():4d} kept {(keep & m).sum():4d}')
