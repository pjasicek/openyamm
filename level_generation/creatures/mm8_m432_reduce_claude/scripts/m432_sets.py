#!/usr/bin/env python3
"""Keep set and region groups for the Dark Elf warrior ladder (work/regions.npy, work/soles.npy, work/basecolor.png).
Kept exactly: both gloves (two-handed sword grip), studs and other small pieces, the boot soles (contact patches) and
the face's painted features (head faces whose base colour is far from the median skin: lips, brows, eye make-up),
one ring dilated (M432_KEEP_FACE=1: the whole front of the face). Groups: 2 face skin (front of the head), 3 hair, 5 boots, 6 pauldrons, 7 eyes, 9 rest of the
head skin (neck, ears, scalp under the hair); label 0 (body suit) takes the ladder budget.
Usage: m432_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import sys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
reg = np.load('work/regions.npy'); soles = np.load('work/soles.npy'); c = v[f].mean(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 9); uv = d['wuv'].reshape(-1, 3, 2)
u = np.einsum('sk,fkc->fsc', B, uv)
col = img[np.clip(((1 - u[..., 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[..., 0] % 1) * W).astype(int), 0, W - 1)]
head = reg == 2
front = head & (c[:, 1] < -0.045) & (c[:, 2] > 1.66) & (c[:, 2] < 1.84)
skin = np.median(col[front].reshape(-1, 3), 0)
dev = np.linalg.norm(col - skin, axis=-1).max(1)
feat = front & (dev > 0.16)
vf = np.zeros(len(v), bool); vf[f[feat].ravel()] = True
feat |= head & vf[f].any(1)
keep = (reg == 4) | (reg == 8) | soles | feat
import os
if os.environ.get('M432_KEEP_FACE') == '1':  # whole front of the face (the 75 % face skin cut creased the cheek)
    keep |= front
groups = np.zeros(len(f), int)
for r in (3, 5, 6, 7):
    groups[(reg == r) & ~keep] = r
groups[front & ~keep] = 2; groups[head & ~front & ~keep] = 9
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('skin', skin.round(2), 'KEEP', int(keep.sum()), '(features', int(feat.sum()), ')',
      {g: int((groups == g).sum()) for g in (0, 2, 3, 5, 6, 7, 9)})
