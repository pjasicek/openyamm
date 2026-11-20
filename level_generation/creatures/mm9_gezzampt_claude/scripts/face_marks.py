#!/usr/bin/env python3
"""Landmarks of the front paint against the geometry, in image fractions of the clay view. Writes work/face_marks.json."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ORTHO = 0.8; C = np.array([-0.00020475685596466064, -0.10504328459501266, 0.9583269357681274])
Z = np.load('work/faces.npz'); hc, hp = Z['hc'], Z['hp']
fx = lambda p: (p[..., 0] - C[0]) * -1 / ORTHO * -1
# front camera: d=(0,-1,0), r = up x d = (1,0,0)?, u = z
d = np.array([0, -1, 0.]); up = np.array([0, 0, 1.]); r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
sx = lambda p: (p - C) @ r / ORTHO + 0.5
sy = lambda p: 0.5 - (p - C) @ u / ORTHO
eye = hc[hp == 13].reshape(-1, 3); teeth = hc[hp == 14].reshape(-1, 3)
E_ = eye[eye[:, 0] * r[0] > 0]; ex = sx(E_).mean(); ey = sy(E_).mean()
ty0, ty1 = sy(teeth).min(), sy(teeth).max(); tx0, tx1 = sx(teeth).min(), sx(teeth).max()
cl = np.asarray(Image.open('references_head/clay_01_front.png').convert('RGBA'))[..., 3] > 128
ys, xs = np.nonzero(cl); H0, W0 = cl.shape
print('clay eye x,y', round(ex, 4), round(ey, 4), 'teeth y', round(ty0, 4), round(ty1, 4), 'x', round(tx0, 4), round(tx1, 4), 'bbox', xs.min() / W0, xs.max() / W0, ys.min() / H0, ys.max() / H0)
im = np.asarray(Image.open('references_head/a_01_front_clean.png').convert('RGBA'), np.float32) / 255
H, W = im.shape[:2]; al = im[..., 3] > 0.5; a = im[..., :3]
mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-3)
ys, xs = np.nonzero(al); print('paint bbox', xs.min() / W, xs.max() / W, ys.min() / H, ys.max() / H)
hue = np.degrees(np.arctan2(np.sqrt(3) * (a[..., 1] - a[..., 2]), 2 * a[..., 0] - a[..., 1] - a[..., 2])) % 360
yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
ir = (sat > 0.75) & (mx > 0.5) & (hue < 30) & (yy > 0.38) & (yy < 0.62) & (np.abs(xx - 0.5) > 0.03) & (np.abs(xx - 0.5) < 0.17)
lab, n = ndi.label(ndi.binary_closing(ir, iterations=2)); sz = ndi.sum(ir, lab, range(1, n + 1)); o = np.argsort(sz)[::-1][:6]
print('iris blobs', [(int(sz[i]), np.round(ndi.center_of_mass(lab == i + 1), 0).tolist()) for i in o])
iv = (mx > 0.55) & (sat < 0.5) & (yy > 0.55) & (np.abs(xx - 0.5) < 0.2) & al
ys, xs = np.nonzero(iv); print('ivory y', np.percentile(ys / H, [1, 50, 99]).round(4), 'x', np.percentile(xs / W, [1, 99]).round(4))
