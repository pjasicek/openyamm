#!/usr/bin/env python3
"""HOM2 face pre-screen fix: the head retexture painted a thin pale teeth line along the closed mouth's slit (a second, pale
lip edge between the lips). Pixels of a flat front close-up of the mouth (uv_probe.py renders: work/mouthz_col.png and the
UV-coded work/mouthz_uv.png, nearest sampling) in the slit band that are paler and yellower than the lips (g/r > 0.62 and
lum > 1.15 x the band median) are mapped to their texels; those texels (dilated 2 px in UV, limited to texels of the same
colour test) take a darker lip colour (median lip x 0.7). Writes v2/textures/phom2_head_basecolor.png, keeps the input as
v2/textures/phom2_head_basecolor_premouth.png. Usage (project folder): mouth_line.py"""
import shutil, json
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage as ndi
T = Path('v2/textures/phom2_head_basecolor.png'); B = Path('v2/textures/phom2_head_basecolor_premouth.png')
if not B.exists():
    shutil.copyfile(T, B)
img = np.asarray(Image.open(B).convert('RGB')).astype(float); N = img.shape[0]
c = np.asarray(Image.open('work/mouthz_col.png').convert('RGB')).astype(float)
u = np.asarray(Image.open('work/mouthz_uv.png').convert('RGB')).astype(int)
lum = c @ np.array([0.299, 0.587, 0.114])
band = np.zeros(lum.shape, bool); band[284:300, 140:520] = True
med = np.median(lum[band])
pale = band & (c[..., 1] / np.maximum(c[..., 0], 1) > 0.62) & (lum > 1.15 * med)
U = u[..., 0] * 8 + (u[..., 2] >> 5); V = u[..., 1] * 8 + ((u[..., 2] >> 2) & 7)
m = np.zeros((N, N), bool)
m[V[pale], U[pale]] = True
il = img @ np.array([0.299, 0.587, 0.114])
lip_px = c[band & ~pale & (c[..., 0] > c[..., 1] * 1.5)]
lip = np.median(lip_px, 0)
cand = ndi.binary_dilation(m, iterations=6) & (img[..., 1] / np.maximum(img[..., 0], 1) > 0.6) & (il > 0.9 * med)
mask = ndi.binary_dilation(m | cand, iterations=1)
w = ndi.gaussian_filter(mask.astype(float), 0.8)
out = img * (1 - w[..., None]) + (lip * 0.7)[None, None, :] * w[..., None]
Image.fromarray(np.uint8(np.clip(out.round(), 0, 255))).save(T)
print('MOUTH_LINE', json.dumps(dict(screen_px=int(pale.sum()), texels=int(mask.sum()), lip=lip.round().tolist())))
