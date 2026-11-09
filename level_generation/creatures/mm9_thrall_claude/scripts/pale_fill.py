#!/usr/bin/env python3
"""Armpit and inner shoulder faces that no master showed: Meshy leaves them pale and smeared. Texels near the arm root that lost the skin's saturation are refilled from the nearest good skin, blurred (Zombie's route). Tier B's pelt: its beady contrast calmed. Overwrites the *_soft / *_final images (run after soft_tex.py)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
src = open('scripts/seam_fix.py').read()
exec(src[src.index('T = Path'):src.index('PT, CT = raster')])
PT, CT = raster(MAT == 1, 2048); PL, CL = raster(MAT == 0, 2048)
def hsv(a):
    mx, mn = a.max(2), a.min(2); s = (mx - mn) / np.maximum(mx, 1e-6); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, s, mx
def fix(path, P, cov, torso):
    a = np.asarray(Image.open(path).convert('RGB'), np.float32) / 255
    h, s, v = hsv(a)
    near = np.zeros(cov.shape, bool)
    for sd in 'LR':
        o, f = Z[sd + 'u'], Z[sd + 'f']; u = (f - o) / np.linalg.norm(f - o)
        st = (P - o) @ u
        q = (np.linalg.norm(P - o, axis=2) < 0.17) & cov
        if torso: q &= st > 0.0
        near |= q
    pale = near & (s < 0.50) & (v > 0.36) & (h > 8) & (h < 50)
    pale = ndimage.binary_opening(pale, iterations=2)
    fillm = ndimage.binary_dilation(pale, iterations=5) & near
    good = cov & ~fillm
    idx = ndimage.distance_transform_edt(~good, return_distances=False, return_indices=True)
    nn = a[idx[0], idx[1]]
    bl = np.stack([ndimage.gaussian_filter(nn[..., c], 7) for c in range(3)], -1)
    w = ndimage.gaussian_filter(fillm.astype(np.float32), 2.5)[..., None]
    a = a * (1 - w) + bl * w
    print('PALE', path.name, int(pale.sum()), int(fillm.sum()))
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype('u1')).save(path)
for t in 'abc':
    fix(T / f'thrall_limbs_{t}_soft.png', PL, CL, False)
    fix(T / f'thrall_torso_{t}_final.png', PT, CT, True)
# pelt of tier B: the beady pattern low-passed
p = T / 'thrall_torso_b_final.png'
a = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
h, s, v = hsv(a)
pelt = (s > 0.62) & ((h < 22) | (h > 345))
pelt = ndimage.gaussian_filter(ndimage.binary_closing(pelt, iterations=4).astype(np.float32), 3)[..., None]
lo = np.stack([ndimage.gaussian_filter(a[..., c], 10) for c in range(3)], -1); mid = np.stack([ndimage.gaussian_filter(a[..., c], 1.2) for c in range(3)], -1)
soft = lo + (mid - lo) * 0.55 + (a - mid) * 0.8
a = a * (1 - pelt) + soft * pelt
print('PELT', float(pelt.mean()))
Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype('u1')).save(p)
