#!/usr/bin/env python3
"""Groove paint after mouth_close.py (replaces mouth_fix.py on the closed-mouth master). The faces mouth_close.py moved (Meshy's mouth
pocket, now the lips' contact groove) still carry the pocket's brown smear; seen from the front it was a brown band between the lips.
Their texels (any face with a slot vertex, selected on the original positions as mouth_close.py does: work/ears_v4.npz vs work/mouth_v2.npz rest positions) take the mean colour of the 8 nearest
unmoved lip/skin texels in 3D (KD-tree on texel_pos positions), darkened toward the groove's middle height (x0.80 at the crease,
Gaussian sigma 0.8 mm) so the lips meet at a soft line. Gutter texels around them take their nearest texel. Then the 7 px despeckle of
mouth_fix.py. Args: <in head png> <out head png>  (project folder)"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
src, dst = sys.argv[1:3]
A, B = np.load('work/ears_v4.npz'), np.load('work/mouth_v2.npz')
# the slot (as mouth_close.py selects it on the ORIGINAL positions): shell vertices in the mouth box more than 1 mm behind the lips'
# front surface near them (frontmost shell vertex within 2 mm in x, 3 mm in z) - the pocket and the slot walls, not the lips
P0 = A['P']; F0 = A['F']; sh = np.zeros(len(P0), bool); sh[np.unique(F0[A['f_part'] == 20])] = True
bx = np.where(sh & (np.abs(P0[:, 0]) < 0.036) & (P0[:, 2] > 0.708) & (P0[:, 2] < 0.738) & (P0[:, 1] < -0.03))[0]
Q0 = P0[bx]; allq = np.where(sh & (np.abs(P0[:, 0]) < 0.04) & (P0[:, 2] > 0.704) & (P0[:, 2] < 0.742) & (P0[:, 1] < -0.03))[0]
QA = P0[allq]
fr = np.array([QA[(np.abs(QA[:, 0] - q[0]) < 0.002) & (np.abs(QA[:, 2] - q[2]) < 0.003), 1].min() for q in Q0])
moved = np.zeros(len(P0), bool); moved[bx[(Q0[:, 1] - fr) > 0.001]] = True
Fm = B['F']; fmoved = moved[Fm].any(1)
TP = np.load('work/texpos_head.npz'); pos, ok, fid = TP['pos'], TP['ok'], TP['face']
Z = np.load('work/faces.npz'); PART = Z['part']
im = np.asarray(Image.open(src).convert('RGB'), float)
f_ = np.maximum(fid, 0)
tgt = ok & fmoved[f_] & (PART[f_] == 20)
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
src_m = ok & ~fmoved[f_] & (PART[f_] == 20) & (np.abs(x) < 0.04) & (z > 0.70) & (z < 0.75) & (y < -0.06)
kd = cKDTree(pos[src_m]); d, i = kd.query(pos[tgt], k=8)
col = im[src_m][i].mean(1)
zc = np.median(z[tgt])
fade = np.clip((0.0245 - np.abs(x[tgt])) / 0.004, 0, 1)
col *= (1 - 0.20 * fade * np.exp(-((z[tgt] - zc) / 0.0008) ** 2))[:, None]
out = im.copy(); out[tgt] = col
g = ndimage.binary_dilation(tgt, iterations=3) & ~ok
_, (iy, ix) = ndimage.distance_transform_edt(~tgt, return_indices=True)
out[g] = out[iy[g], ix[g]]
zone = ndimage.binary_dilation(ok & (np.abs(x) < 0.03) & (z > 0.708) & (z < 0.742) & (y < -0.06), iterations=3)
med = np.stack([ndimage.median_filter(out[..., c], size=7) for c in range(3)], -1)
sp = zone & ((out.mean(2) < 0.78 * med.mean(2)) | (out.mean(2) > 1.18 * med.mean(2)))
out[sp] = med[sp]
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
print('MOUTH2 groove texels', int(tgt.sum()), 'moved verts', int(moved.sum()), 'faces', int(fmoved.sum()), 'specks', int(sp.sum()))
