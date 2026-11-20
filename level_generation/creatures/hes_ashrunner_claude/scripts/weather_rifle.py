#!/usr/bin/env python3
"""Tier B's blaster rifle is the Landfall guard's Ancient rifle (hes_guard_claude, reference reused), scavenged: its
texture (textures/props/rifle.png and har_rifle_basecolor.png from rifle_texture.py) gets dust and scorch (low-frequency
darkening toward warm grey-brown), chipped ceramic (small dark flecks on the bright texels) and dulled gold.
Deterministic (seed 7). Args: none"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
T = Path(__file__).resolve().parents[1] / 'textures'
im = np.asarray(Image.open(T / 'props' / 'rifle.png').convert('RGB')).astype(np.float64) / 255
H, W = im.shape[:2]; rng = np.random.default_rng(7)
low = ndimage.gaussian_filter(rng.random((H, W)), 18); low = (low - low.min()) / (np.ptp(low) + 1e-9)
dust = np.array([0.46, 0.40, 0.33])
k = 0.18 + 0.32 * low[..., None]
out = im * (1 - k) + dust * k * im.mean(2, keepdims=True) * 1.6
fl = ndimage.gaussian_filter(rng.random((H, W)), 1.2); fl = fl > np.percentile(fl, 96.5)
bright = im.mean(2) > 0.6
out[fl & bright] *= 0.35
lum = out.mean(2, keepdims=True); hsv_s = (out.max(2) - out.min(2))[..., None]
out = np.where(hsv_s > 0.25, out * 0.8 + lum * 0.2, out)
img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
img.save(T / 'props' / 'rifle.png'); img.save(T / 'har_rifle_basecolor.png')
print('WEATHER rifle', img.size)
