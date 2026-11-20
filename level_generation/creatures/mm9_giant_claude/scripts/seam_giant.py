#!/usr/bin/env python3
"""Neck seam (after mm9_bigfoot_claude/scripts/seam_fix.py): the head set and the body set meet on a jagged line of faces round the
neck. Head texels within a few cm of the body set (3D distance to the nearest body texel) take the body's colour there, fine grain of
the head kept, so both tiers' heads run into the shared body paint (no tier ramp covers the neck). Writes textures/gi_head_{t}_final.png
(1536) from gi_head_{t}_raw.png (2048). Args: <tiers>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
zb = np.load('work/body_pos.npz'); zh = np.load('work/head_pos.npz')
B = np.asarray(Image.open('textures/gi_body_final.png').convert('RGB'), np.float32) / 255
mb = zb['cov'] & (zb['pos'][..., 2] > 0.80) & (zb['pos'][..., 2] < 0.95) & (np.abs(zb['pos'][..., 0]) < 0.3)
Pb = zb['pos'][mb]; Cb = B[mb]
tb = cKDTree(Pb[::2])
mh = zh['cov'] & (zh['prt'] < 13) & (zh['pos'][..., 2] < 0.99)
Ph = zh['pos'][mh]
d, ib = tb.query(Ph, k=24)
near = Cb[::2][ib].mean(1)
w = 1 - np.clip((d[:, 0] - 0.004) / 0.018, 0, 1); w = w * w * (3 - 2 * w)
for t in sys.argv[1]:
    H = np.asarray(Image.open(f'textures/gi_head_{t}_raw.png').convert('RGB'), np.float32) / 255
    lo = np.stack([ndimage.gaussian_filter(H[..., c], 6) for c in range(3)], -1)
    fine = (H - lo)[mh]
    new = np.clip(near + fine * 0.8, 0, 1)
    out = H.copy(); out[mh] = H[mh] * (1 - w[:, None]) + new * w[:, None]
    Image.fromarray((out * 255 + .5).astype('u1')).resize((1536, 1536), Image.LANCZOS).save(f'textures/gi_head_{t}_final.png')
    print('SEAM', t, 'texels blended', int((w > 0.05).sum()), 'full', int((w > 0.95).sum()))
