#!/usr/bin/env python3
"""Final Naga keep set and groups (after the per-region tests in README): everything kept exactly except
group 1 = head outside the face (scalp / hair shell), group 7 = face skin away from painted features (non-skin faces
of the face set - lips, eye make-up, brows - plus two rings stay exact), group 8 = the twelve cuffs and arm bands,
label 0 = torso skin without the painted gold trims (ladder budget). Writes work/keep_d.npy, work/groups_d.npy and
prints the ladder ratio for each torso ratio given. Usage: naga_sets_d.py <torso ratio,...>"""
import sys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
k = np.load('work/keep_naga.npy'); fi = np.load('work/face_info.npz'); reg = fi['region']
small = np.load('work/keep_small.npy'); gb = np.load('work/groups_naga_b.npy')
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
m = uv.mean(1); col = img[np.clip(((1 - m[:, 1] % 1) * H).astype(int), 0, H - 1), np.clip(((m[:, 0] % 1) * W).astype(int), 0, W - 1)]
r, g, b = col.T
skin = (r > .55) & (r > g * 1.05) & (g > b * .95) & ((r - b) < .45)
face = k & (reg == 'head') & ~small
feat = face & ~skin
for _ in range(2):
    vf = np.zeros(len(d['verts']), bool); vf[f[feat].ravel()] = True; feat |= face & vf[f].any(1)
cuffs = small & (reg == 'arm'); headrest = (gb == 1) & ~k; torso = (gb == 4) & ~k
groups = np.zeros(len(f), int); groups[headrest] = 1; groups[face & ~feat] = 7; groups[cuffs] = 8
keep = ~(headrest | (face & ~feat) | cuffs | torso)
np.save('work/keep_d.npy', keep); np.save('work/groups_d.npy', groups)
RAT = {1: .55, 7: .65, 8: .65}
fixed = keep.sum() + sum(int((groups == x).sum() * q) for x, q in RAT.items())
print('KEEP', int(keep.sum()), 'face features', int(feat.sum()), 'face skin', int((groups == 7).sum()), 'cuffs', int(cuffs.sum()),
      'head rest', int(headrest.sum()), 'torso', int(torso.sum()))
print('LADDER', ','.join(f'{(fixed + int(torso.sum() * float(q))) / len(f):.4f}' for q in sys.argv[1].split(',')))
