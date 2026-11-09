#!/usr/bin/env python3
"""Bake each tier's ramps into the base colour with the shader's rule (per region: t = linear luminance normalised over
the region's range; colour = mix(colour, ramp(t), mask)) -> work/tier_<variant>_<material>.png (previews, viewer).
Args: none"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
H = Path(__file__).resolve().parents[1]; T = H / 'textures'
W = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
cfg = json.loads((T / 'm332_ramps.json').read_text())
SRC = {'Elf_A': 'm332_basecolor_1k.png', 'ElfHead_A': 'm332_head_basecolor_1k.png'}
for m in cfg['materials']:
    base = lin(np.asarray(Image.open(T / SRC[m['base']]).convert('RGB'), np.float64) / 255)
    mask = np.asarray(Image.open(T / m['mask']).convert('RGBA'), np.float64) / 255
    lum = base @ W
    for v in cfg['variants']:
        out = base.copy()
        for c, reg in enumerate(m['ramps'][v]):
            lo, hi = reg['range']; col = np.array(reg['colors'])
            x = np.clip((lum - lo) / (hi - lo), 0, 1) * 15; i = np.minimum(x.astype(int), 14); f = (x - i)[..., None]
            out = out * (1 - mask[..., c:c + 1]) + (col[i] * (1 - f) + col[i + 1] * f) * mask[..., c:c + 1]
        Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + 0.5).astype(np.uint8)).save(H / 'work' / f'tier_{v}_{m["base"]}.png')
        print('TIER', v, m['base'])
