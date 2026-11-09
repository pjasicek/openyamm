#!/usr/bin/env python3
"""Pale speck under the chin (r10, 2026-11-04): both fresh head paints (a3, b3) left a 2-4 texel tusk-pale streak (~255/215/162) on
the chin island's edge at UV (0.4697, 0.1234) (Blender v up), seen in the viewer as a bright dot below her right lower lip. Texels
within R px of that UV that are much brighter than the skin around them (luminance > the window's skin median + DL) take the
skin median of the window, with a 2 px feather; the hair island beside it (dark orange) is left alone.
Args: <head basecolor png> [u 0.4697] [v 0.1234] [r 24] [dl 30]"""
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
p = sys.argv[1]
f = lambda i, d: float(sys.argv[i]) if len(sys.argv) > i else d
U, V, R, DL = f(2, 0.4697), f(3, 0.1234), int(f(4, 24)), f(5, 30.0)
im = np.asarray(Image.open(p).convert('RGB')).astype(float); H, W, _ = im.shape
cx, cy = int(U * W), int((1 - V) * H)
y0, y1, x0, x1 = cy - R, cy + R, cx - R, cx + R
win = im[y0:y1, x0:x1]
L = win @ np.array([0.299, 0.587, 0.114])
skin = (win[..., 0] > 170) & (win[..., 1] > 100) & (win[..., 1] < 175) & (win[..., 2] < 150) & (win[..., 2] > 70)
med = np.median(win[skin], axis=0); ml = float(med @ np.array([0.299, 0.587, 0.114]))
bad = (L > ml + DL) & (win[..., 0] > 170)
m = gaussian_filter(bad.astype(float), 1.0); m = (np.clip(m * 2.0 + bad, 0, 1) * (win[..., 1] > 90))[..., None]
im[y0:y1, x0:x1] = win * (1 - m) + med * m
Image.fromarray(np.clip(im + 0.5, 0, 255).astype(np.uint8)).save(p)
print('CHINSPECK', p, 'skin median', np.round(med, 1), 'texels replaced', int(bad.sum()))
