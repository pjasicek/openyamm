#!/usr/bin/env python3
"""Neck seam (viewer, r3: a hard jagged line where the head set meets the body set across the beard's tip, the hair's lower rim
and the collar). Body texels within BAND below the neck plane (uv_yan.py's split) take, by a smooth ramp that is 1 at the plane,
the head paint at their mirror point above the plane (nearest head texel in 3D), so the hair and beard strands run on across the
cut and the line itself disappears. Writes textures/yan_body_final.png from textures/yan_body_preseam.png (in place otherwise)."""
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
BAND = 0.035
C = np.array([0.0, 0.0, 0.932]); Nk = np.array([0.0, -0.25, 0.97]); Nk /= np.linalg.norm(Nk)
src = Path('textures/yan_body_preseam.png')
if not src.exists(): shutil.copyfile('textures/yan_body_final.png', src)
B = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
H = np.asarray(Image.open('textures/yan_head_final.png').convert('RGB'), np.float32) / 255
zb = np.load('work/body_pos.npz'); zh = np.load('work/head_pos.npz')
kb = B.shape[0] / zb['pos'].shape[0]; kh = H.shape[0] / zh['pos'].shape[0]
assert kb == 1 and kh == 1, (B.shape, zb['pos'].shape, H.shape, zh['pos'].shape)
pb = zb['pos']; d = (pb - C) @ Nk
m = zb['cov'] & (d < 0.002) & (d > -BAND) & (np.abs(pb[..., 0]) < 0.27)
mh = zh['cov'] & (zh['prt'] < 13)
Ph = zh['pos'][mh]; Ch = H[mh]
tree = cKDTree(Ph)
P = pb[m]; dd = d[m]
q = P - 2 * dd[:, None] * Nk[None] + Nk[None] * 0.004          # the mirror point, 4 mm above the plane
dist, ix = tree.query(q, k=4)
wq = 1 / np.maximum(dist, 1e-4); col = (Ch[ix] * wq[..., None]).sum(1) / wq.sum(1, keepdims=True)
near = dist[:, 0] < 0.03                                        # only where the head surface is there above the cut
t = np.clip(1 + dd / BAND, 0, 1); w = t * t * (3 - 2 * t) * near
out = B.copy(); out[m] = B[m] * (1 - w[:, None]) + col * w[:, None]
# the throat behind the beard (pulled onto the beard's back by tunnel_close.py, its paint stretched to a pale smear): the beard's
# own paint from the nearest head texel, blended in by a soft box
p = pb; s_ = lambda x, a_, b_: np.clip((x - a_) / (b_ - a_), 0, 1)
box = s_(-p[..., 1], 0.0, 0.03) * s_(0.13 - np.abs(p[..., 0]), 0.0, 0.03) * s_(p[..., 2], 0.85, 0.88) * s_(1.0 - p[..., 2], 0.0, 0.03)
mt = zb['cov'] & (box > 0) & (d < 0.04)
dist2, ix2 = tree.query(pb[mt], k=6)
w2 = 1 / np.maximum(dist2, 1e-4); col2 = (Ch[ix2] * w2[..., None]).sum(1) / w2.sum(1, keepdims=True)
bx = box[mt] * (dist2[:, 0] < 0.05)
out[mt] = out[mt] * (1 - bx[:, None]) + col2 * bx[:, None]
print('THROAT texels', int(mt.sum()))
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save('textures/yan_body_final.png')
print('SEAM texels', int(m.sum()), 'blended', int((w > 0.05).sum()))
