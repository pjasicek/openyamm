#!/usr/bin/env python3
"""Textures of a Meshy prop from its raw bakes (meshy_prop.py): base colour x AO^ao x linear gains, tangent normal,
luminance contrast, chroma-aware gains (keep_grey),
roughness rescaled into cfg['rough'] with the scan's glossiest 4 % as small wet spots (cfg['wet'], meat only).
Blender bake arrays are bottom-up; PNG rows are top-down. Writes props/textures/<name>_{basecolor,normal,mr}.png.
Usage: meshy_textures.py <work/<name>_bake.npz> <cfg json>"""
import json
import os
import sys

import numpy as np
from PIL import Image

path, cfg = sys.argv[1], json.loads(sys.argv[2])
name = os.path.basename(path).replace('_bake.npz', '')
TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures')
d = np.load(path)
base, rough, normal, ao = d['base'], d['rough'], d['normal'], d['ao']
flip = lambda a: a[::-1]
lin = base * np.clip(ao[..., :1], 0, 1) ** cfg['ao']
# luminance contrast about the mean (the sprites' dark crevices), then the grade: chromatic texels (meat, bone) take
# the per-channel gains, near-neutral ones (grey skin) a neutral gain of the same brightness, so they stay grey
lum = lin @ np.array([0.2126, 0.7152, 0.0722])
lin = lin * (np.maximum(lum, 1e-5) / lum.mean())[..., None] ** (cfg.get('contrast', 1.0) - 1)
gains = np.array(cfg.get('gain', (1.0, 1.0, 1.0)))
if cfg.get('keep_grey'):
    chroma = (lin.max(-1) - lin.min(-1)) / np.maximum(lin.max(-1), 1e-5)
    w = np.clip((chroma - 0.12) / 0.25, 0, 1)[..., None]
    neutral = np.full(3, gains @ np.array([0.2126, 0.7152, 0.0722]))
    gains = neutral * (1 - w) + gains * w
lin = np.clip(lin * gains, 0, 1)
srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
Image.fromarray((flip(srgb) * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEX, f'{name}_basecolor.png'),
                                                                 optimize=True)
half = cfg['res'] // 2
Image.fromarray((flip(np.clip(normal, 0, 1)) * 255 + 0.5).astype(np.uint8)).resize((half, half), Image.LANCZOS).save(
    os.path.join(TEX, f'{name}_normal.png'), optimize=True)
r = rough[..., 0]
lo, hi = cfg['rough']
q1, q9 = np.quantile(r, [0.05, 0.95])
rr = lo + (hi - lo) * np.clip((r - q1) / max(q9 - q1, 1e-6), 0, 1)
if cfg['wet']:
    rr = np.where(r < np.quantile(r, 0.04), cfg['wet'], rr)
mr = np.zeros(r.shape + (3,)); mr[..., 0] = 1.0; mr[..., 1] = rr
Image.fromarray((flip(mr) * 255 + 0.5).astype(np.uint8)).resize((half // 2, half // 2), Image.LANCZOS).save(
    os.path.join(TEX, f'{name}_mr.png'), optimize=True)
print('TEXTURES', name, 'linear mean', np.round(lin.reshape(-1, 3).mean(0), 3))
