#!/usr/bin/env python3
"""Bake each tier's ramps into a preview base colour (the shader's math: linear luminance, 16 stops, mix per mask channel in order).
Args: <base png> <mask png> <ramps json> <out prefix>  -> <prefix>_<variant>.png"""
import sys, json
import numpy as np
from PIL import Image
base_p, mask_p, rj, pre = sys.argv[1:5]
b = np.asarray(Image.open(base_p).convert('RGB'), np.float32) / 255
lin = np.where(b <= 0.04045, b / 12.92, ((b + 0.055) / 1.055) ** 2.4); lum = lin @ np.array([0.2126, 0.7152, 0.0722])
m = np.asarray(Image.open(mask_p).convert('RGBA').resize(b.shape[1::-1], Image.BILINEAR), np.float32) / 255
cfg = json.load(open(rj)); mat = cfg['materials'][0]
for v in cfg['variants']:
    out = lin.copy()
    for ch, r in enumerate(mat['ramps'][v]):
        lo, hi = r['range']; t = np.clip((lum - lo) / (hi - lo), 0, 1) * 15; i = np.minimum(t.astype(int), 14); f = (t - i)[..., None]
        C = np.array(r['colors']); col = C[i] * (1 - f) + C[i + 1] * f
        out = out * (1 - m[..., ch:ch + 1]) + col * m[..., ch:ch + 1]
    s = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.maximum(out, 0) ** (1 / 2.4) - 0.055)
    Image.fromarray((np.clip(s, 0, 1) * 255 + .5).astype('u1')).save(f'{pre}_{v}.png'); print('PREVIEW', v)
