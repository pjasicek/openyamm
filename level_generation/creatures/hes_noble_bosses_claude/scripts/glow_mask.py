#!/usr/bin/env python3
"""Glow mask from a baked base colour (venv python): hot saturated orange (and optionally violet) energy pixels.
Usage: glow_mask.py <base.png> <out_mask.png> [orange|violet|both] [min_value]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
img = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float64) / 255
kind = sys.argv[3] if len(sys.argv) > 3 else 'orange'
vmin = float(sys.argv[4]) if len(sys.argv) > 4 else 0.75
mx = img.max(-1); mn = img.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6); dm = np.maximum(mx - mn, 1e-6)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
hue = np.where(mx == r, ((g - b) / dm) % 6, np.where(mx == g, (b - r) / dm + 2, (r - g) / dm + 4)) * 60
orange = (hue < 40) & (sat > 0.6) & (mx > vmin)
violet = (hue > 255) & (hue < 300) & (mx > vmin - 0.1) & (sat > 0.3)
m = {'orange': orange, 'violet': violet, 'both': orange | violet}[kind]
m = ndimage.binary_opening(m, iterations=1)
soft = np.clip(ndimage.gaussian_filter(m.astype(float), 0.8) * 1.5, 0, 1)
Image.fromarray((soft * 255).astype(np.uint8)).save(sys.argv[2])
print('glow fraction', round(float(m.mean()), 4))
