#!/usr/bin/env python3
"""Tier C eye rims (wave-1 lesson "no heavy red rims"): MM9's PEASANTM7C has rosy lids, the Codex views and the retexture
made them a saturated red ring round both eyes. Head texels within the eye boxes (rest position, |x - mid| 0.012..0.062,
y < -0.055, z 0.805..0.842) that are redder than the face skin (r/g above the cheek skin's by > 0.12, not iris blue, not
dark lashes) move 70 % of the way to the cheek skin's r/g and r/b ratio at their own luminance (kept rosy, no ring).
Runs after ear_paint.py on the tier's head colour. Usage (project folder): eye_rims.py <prefix> [strength 0.7]"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
prefix = sys.argv[1]; K = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
path = f'textures/{prefix}_head_basecolor.png'
img = np.asarray(Image.open(path).convert('RGB')).astype(np.float64)
N = img.shape[0]
D = np.load('work/head_faces.npz')
P = np.full((N, N, 3), np.nan)
for uv, p in zip(D['UV'], D['P']):
    if p[:, 2].max() < 0.79 or p[:, 2].min() > 0.86 or p[:, 1].min() > -0.04:
        continue
    q = uv * N; q[:, 1] = N - q[:, 1]
    x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
    if xs.size == 0:
        continue
    c = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, d = q
    m = np.array([[b[0] - a[0], d[0] - a[0]], [b[1] - a[1], d[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-9:
        continue
    l = np.linalg.solve(m, (c - a).T).T
    w = np.column_stack([1 - l.sum(1), l])
    ok = (w >= -1e-3).all(1)
    P[c[ok, 1].astype(int), c[ok, 0].astype(int)] = w[ok] @ p
MID = -0.0111
dx = np.abs(P[..., 0] - MID)
box = np.isfinite(dx) & (dx > 0.012) & (dx < 0.062) & (P[..., 1] < -0.055) & (P[..., 2] > 0.805) & (P[..., 2] < 0.842)
cheek = np.isfinite(dx) & (dx > 0.03) & (dx < 0.06) & (P[..., 1] < -0.05) & (P[..., 2] > 0.765) & (P[..., 2] < 0.795)
r, g, b = img[..., 0] + 1, img[..., 1] + 1, img[..., 2] + 1
rg0, rb0 = np.median((r / g)[cheek]), np.median((r / b)[cheek])
lum = img @ np.array([0.299, 0.587, 0.114])
red = box & (r / g > rg0 + 0.12) & (b < r * 0.8) & (lum > 40)
w = ndi.gaussian_filter(red.astype(float), 1.0) * box * K
tg = r / rg0; tb = r / rb0                         # same red, skin's ratios
L0 = lum
new = np.stack([r, tg, tb], -1) - 1
new *= (L0 / np.maximum(new @ np.array([0.299, 0.587, 0.114]), 1))[..., None]
out = img * (1 - w[..., None]) + new * w[..., None]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(path)
print('EYE_RIMS', json.dumps(dict(prefix=prefix, box=int(box.sum()), red=int(red.sum()), cheek_rg=round(float(rg0), 3),
                                  cheek_rb=round(float(rb0), 3), strength=K)))
