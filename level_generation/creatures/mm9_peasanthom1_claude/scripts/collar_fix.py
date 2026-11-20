#!/usr/bin/env python3
"""Collar paint fix: Meshy painted the top rim of the vest collar (behind and beside the neck, z > 0.68) in skin pink
(237/143/101), which read as bare skin round the neck in the close-ups. Those texels (trunk, |x| < 0.3, hue 5-28,
saturation 0.2-0.62, value > 0.55) take the collar's rust leather (median of its rust texels) with their own
brightness detail (luminance ratio ^ 0.6), feathered 1.5 texels.
Usage (project folder): python3 scripts/collar_fix.py  (textures/phom1_basecolor_graded_pre.png -> textures/phom1_basecolor_graded.png;
then scripts/tier_ramps_phom1.py)."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, 'scripts')
from tier_ramps import hsv
base = np.asarray(Image.open('textures/phom1_basecolor_graded_pre.png').convert('RGB'), float) / 255
N2 = base.shape[0]
t = np.load('v2/work/texel_body_1k.npz'); X, cov = t['xyz'], t['cov']
X = np.repeat(np.repeat(X, N2 // 1024, 0), N2 // 1024, 1); cov = np.repeat(np.repeat(cov, N2 // 1024, 0), N2 // 1024, 1)
h, s, v = hsv(base); x, z = X[..., 0], X[..., 2]
col = cov & (z > 0.68) & (np.abs(x) < 0.3)
pink = col & (h > 5) & (h < 28) & (s > 0.2) & (s < 0.62) & (v > 0.55)
rust = col & (h > 12) & (h < 32) & (s > 0.8) & (v > 0.3)
L = base @ np.array([0.2126, 0.7152, 0.0722])
target = np.median(base[rust], 0)
ratio = (L / np.median(L[pink])) ** 0.6
new = np.clip(target[None, None] * ratio[..., None] * (np.median(L[rust]) / (target @ np.array([0.2126, 0.7152, 0.0722]))), 0, 1)
w = np.clip(ndi.gaussian_filter(pink.astype(float), 1.5) * 1.5, 0, 1) * col
out = base * (1 - w[..., None]) + new * w[..., None]
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save('textures/phom1_basecolor_graded.png')
print('COLLAR pink texels', int(pink.sum()), 'target', (target * 255).round().tolist())
