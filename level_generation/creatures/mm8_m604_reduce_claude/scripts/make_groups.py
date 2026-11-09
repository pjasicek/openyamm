#!/usr/bin/env python3
"""Ether Knight per-region budgets for decimate_tex.py (REA_GROUPS / REA_KEEP_FACES):
keep exactly: small pieces (<= 80 faces: eyes, rivets, clasps, belt studs), right hand and fingers (fitted sword grip),
soles (faces below 6 cm); group 1 head piece, group 2 left hand and fingers, group 3 cloth shell piece, group 4 mid-size pieces, 0 the rest.
-> work/groups.npy, work/keep.npy"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
fb = np.load('work/face_bones.npz'); names = [str(n) for n in fb['names']]; dom = fb['dom']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
bone = np.array([names[i] for i in dom])
small = sizes[fl] <= 80
rhand = np.char.startswith(bone, 'B_R_Finger') | (bone == 'B_R_Hand')
lhand = np.char.startswith(bone, 'B_L_Finger') | (bone == 'B_L_Hand')
cen = v[f].mean(1); sole = v[f][:, :, 2].max(1) < .06
order = np.argsort(-sizes)
head_piece = next(p for p in order if cen[fl == p][:, 2].mean() > 1.6)
cloth_piece = next(p for p in order if p != head_piece and abs(cen[fl == p][:, 2].mean() - 1.5) < .05)
tab = np.isin(fl, [p for p in order[:12] if 200 < sizes[p] < 300 and abs(cen[fl == p][:, 1].mean()) > .1
                    and abs(cen[fl == p][:, 2].mean() - .8) < .05])
belt = np.isin(fl, [p for p in order[:12] if 250 < sizes[p] < 320 and abs(cen[fl == p][:, 2].mean() - 1.11) < .03])
from PIL import Image
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 12)
su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
c = np.median(img[y, x], 1)
goldc = (c[:, 0] > 140) & (c[:, 1] > 100) & (c[:, 0] - c[:, 2] > 60)
gold = goldc & (fl == order[0])
# grow by one ring of neighbouring faces so the trim edges stay put
vk = np.zeros(n, bool); vk[f[gold].ravel()] = True; gold |= vk[f].any(1) & (fl == order[0])
keep = small | rhand | sole | tab | belt | gold
print('tabard', int(tab.sum()), 'belt', int(belt.sum()), 'gold trims', int(gold.sum()))
groups = np.zeros(len(f), int)
groups[fl == head_piece] = 1; groups[lhand] = 2; groups[fl == cloth_piece] = 3
# group 4: mid-size separate pieces (gold knee pads, arm bands, back strips): a hard cut shifted them 5+ mm
mid = (sizes[fl] > 80) & (sizes[fl] < 400) & ~tab & ~belt & (fl != head_piece) & (fl != cloth_piece)
groups[mid] = 4
groups[keep] = 0
np.save('work/keep.npy', keep); np.save('work/groups.npy', groups)
print('KEEP', int(keep.sum()), '(small', int(small.sum()), 'rhand', int(rhand.sum()), 'sole', int(sole.sum()), ')',
      'head', int((groups == 1).sum()), 'lhand', int((groups == 2).sum()), 'cloth', int((groups == 3).sum()), 'mid', int((groups == 4).sum()),
      'rest', int(((groups == 0) & ~keep).sum()), 'of', len(f))
