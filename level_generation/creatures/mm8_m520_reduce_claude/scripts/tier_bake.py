#!/usr/bin/env python3
"""Tier base colours for review renders: the engine rule (t = linear luminance normalised over the region's range,
colour = mix(colour, ramp(t), mask channel)) applied to the export's atlas with each variant material's ramps.
-> work/retex/tier_<a|b|c><suffix>.png (needs work/retex/img0.png base colour and a region mask, default img3.png).
Usage: tier_bake.py [mask.png suffix]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb  # noqa: E402
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


doc, _ = read_glb(Path('export/mm8_m520.glb'))
rgba = np.asarray(Image.open('work/retex/img0.png').convert('RGBA'), np.float32) / 255
MASK, SUF = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ('work/retex/img3.png', '')
mask = np.asarray(Image.open(MASK).convert('RGBA'), np.float32) / 255
base = lin(rgba[..., :3]); lum = base @ W
for mat, tier in zip(doc['materials'], 'abc'):
    out = base.copy()
    for ch, reg in enumerate(mat['extras']['openyamm_region_ramps']):
        lo, hi = reg['range']; m = mask[..., ch:ch + 1]
        out = out * (1 - m) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * m
    Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(f'work/retex/tier_{tier}{SUF}.png')
    print('TIER', mat['name'], tier)
