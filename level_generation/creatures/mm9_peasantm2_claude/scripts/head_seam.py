#!/usr/bin/env python3
"""Mirror-midline UV seam on the forehead (a pale vertical line in both head paints): texels of the face shell within 8 mm of x = 0 from the
nose bridge to the crown take the mean colour of the face-shell texels 11 mm to each side in 3D (texel_pos.py positions), blended in over
4-8 mm. Reads textures/pm2_head_{t}_raw.png, writes textures/pm2_head_{t}_tone.png. Project folder."""
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
Z = np.load('work/faces.npz'); PART = Z['part']
D = np.load('work/texpos_head.npz'); pos, ok, fid = D['pos'], D['ok'], D['face']
skin = ok & (PART[np.maximum(fid, 0)] == 20)
ys, xs = np.nonzero(skin); P = pos[ys, xs]; tree = cKDTree(P)
ax = np.abs(P[:, 0])
band = (ax < 0.008) & (P[:, 2] > 0.775) & (P[:, 2] < 0.95)
w = np.clip((0.008 - ax[band]) / 0.004, 0, 1)
for t in 'ab':
    im = np.asarray(Image.open(f'textures/pm2_head_{t}_raw.png').convert('RGB'), np.float32)
    col = im[ys, xs]
    q = P[band]; acc = np.zeros((len(q), 3))
    for s in (-1, 1):
        _, j = tree.query(q + [s * 0.011, 0, 0]); acc += col[j]
    new = col[band] * (1 - w[:, None]) + acc / 2 * w[:, None]
    out = im.copy(); out[ys[band], xs[band]] = new
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f'textures/pm2_head_{t}_tone.png')
    print('SEAM', t, 'texels', int(band.sum()))
