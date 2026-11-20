#!/usr/bin/env python3
"""The belly disc painted out of the body colour: inside an ellipse on the front of the belly the colour is a diffused fill from
the surrounding skin plus the fine grain of the abdomen 14 cm higher (by 3D position). Args: <in png> <out png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
src, dst = sys.argv[1:3]
im = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
S = im.shape[0]
Z = np.load('work/body_pos.npz'); pos, cov = Z['pos'], Z['cov']
if pos.shape[0] != S:
    k = pos.shape[0] // S; pos = pos[::k, ::k]; cov = cov[::k, ::k]
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
e = (x / 0.20) ** 2 + ((z - 0.37) / 0.16) ** 2
belt = np.clip((z - 0.222) / 0.012, 0, 1)                         # the belt's top edge stays
e = np.where(z < 0.222, 9.0, e)
hole = cov & (y < -0.12) & (e < 1.0)
r_, g_, b_ = im[..., 0], im[..., 1], im[..., 2]; lum = im @ np.array([0.2126, 0.7152, 0.0722])
skin = (r_ > g_ * 1.12) & (g_ > b_ * 1.05) & (lum > 0.28) & (lum < 0.75)
ring = cov & (y < -0.12) & (e >= 1.0) & (e < 2.2) & skin & (z > 0.25)
# low frequency: the ring's colour diffused over the hole, by 3D distance
rp = pos[ring]; rc = im[ring]; hp = pos[hole]
d, nn = cKDTree(rp[::3]).query(hp, k=64)
wgt = 1 / (d + 0.01) ** 2; low = (rc[::3][nn] * wgt[..., None]).sum(1) / wgt.sum(1, keepdims=True)
# fine grain from higher up the abdomen
src_m = cov & (y < -0.15) & (z > 0.50) & (z < 0.60) & (np.abs(x) < 0.12) & skin
sp = pos[src_m]; lf = np.stack([ndimage.gaussian_filter(im[..., c], 4) for c in range(3)], -1)
fine = (im - lf)[src_m]
q = hp.copy(); q[:, 2] = 0.50 + (q[:, 2] - 0.21) * (0.10 / 0.32); q[:, 0] *= 0.85
_, j = cKDTree(sp).query(q)
out = im.copy()
fill = np.clip(low + fine[j] * 1.3, 0, 1)
a = (np.clip((1.0 - e[hole]) / 0.2, 0, 1) * belt[hole])[:, None]
out[hole] = out[hole] * (1 - a) + fill * a
Image.fromarray((out * 255 + .5).astype('u1')).save(dst)
print('BELLYTEX texels', int(hole.sum()))
# the normal map and the ORM's occlusion keep the disc's ring: flattened over the same region (1K maps)
import os
if os.environ.get('MAPS', '1') == '1':
    for f, mode in (('textures/gi_body_normal.png', 'n'), ('textures/gi_body_orm.png', 'o')):
        m_ = np.asarray(Image.open(f).convert('RGB'), np.float32) / 255; s_ = m_.shape[0]; k = S // s_
        hs = hole[::k, ::k]; es = e[::k, ::k]; bs = belt[::k, ::k]
        a2 = (np.clip((1.0 - es) / 0.2, 0, 1) * bs)[..., None] * hs[..., None]
        if mode == 'n':
            fine = m_ - np.stack([ndimage.gaussian_filter(m_[..., c], 3) for c in range(3)], -1)
            tgt = np.array([0.5, 0.5, 1.0]) + fine * 0.6
        else:
            ring2 = ring[::k, ::k]; tgt = m_.copy(); tgt[..., 0] = np.median(m_[ring2][:, 0]) if ring2.any() else 1.0
        m_ = m_ * (1 - a2) + tgt * a2
        Image.fromarray((np.clip(m_, 0, 1) * 255 + .5).astype('u1')).save(f)
    print('BELLYTEX maps flattened')
