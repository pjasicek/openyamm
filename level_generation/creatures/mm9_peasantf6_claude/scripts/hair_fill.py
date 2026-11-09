#!/usr/bin/env python3
"""The bob's lowest band beside and behind the jaw (the hair shell reaches the neck there; the Codex masters showed neck skin) came back
painted as plain pale skin-blond with no strands: in profile a pale patch on the neck. Those hair-shell texels (Z < ZTOP, outside the face,
in front of the nape) take the colour of the shell texel UP m higher on the same side (nearest shell texel in 3D to the raised point),
blended in over 1.5 cm, so the strands run on down to the edge. Args: <in png> <out png> [ztop 0.675] [up 0.045]   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
from scipy.spatial import cKDTree
SRC, DST = sys.argv[1:3]; ZTOP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.675; UP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.045
H = np.load('work/headmap.npz'); pos, cov, face = H['pos'], H['cov'], H['face']
D = np.load('work/uv.npz'); comp, tri = D['comp'], D['tri']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32); out = im.copy()
fc = np.full(cov.shape, -1); fc[cov] = comp[tri[face[cov], 0]]
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]
shell = cov & (fc == names.index('hair'))
band = shell & (Z < ZTOP) & (Y > -0.075) & (Y < 0.06)
src = shell & (Z > ZTOP + 0.005)
q = pos[band].copy(); q[:, 2] += UP
d, n = cKDTree(pos[src]).query(q, k=3); w = 1 / np.maximum(d, 1e-4)
new = (im[src][n] * w[..., None]).sum(1) / w.sum(1)[:, None]
k = np.clip((ZTOP - Z[band]) / 0.015, 0, 1)[:, None]
out[band] = im[band] * (1 - k) + new * k
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray(np.clip(out + .5, 0, 255).astype('u1')).save(DST)
print('HAIR_FILL', int(band.sum()), 'texels')
