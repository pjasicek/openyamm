#!/usr/bin/env python3
"""Runtime maps of the tier gear (after make_gear.py): base colour (textures/props/<name>.png), a flat normal map and
the ORM-packed specular mask / roughness (white ceramic R 0.6 G 0.45, gold R 0.8 G 0.3, the rest R 0.3 G 0.65; B 0)
-> textures/har_<name>_{basecolor,normal,metal_rough}.png. Args: none"""
from pathlib import Path
import numpy as np
from PIL import Image
T = Path(__file__).resolve().parents[1] / 'textures'
for name in ('chest_plate', 'buckler'):
    base = Image.open(T / 'props' / f'{name}.png').convert('RGB'); base.save(T / f'har_{name}_basecolor.png')
    Image.new('RGB', base.size, (128, 128, 255)).save(T / f'har_{name}_normal.png')
    h, s, v = [np.asarray(c, np.float64) / 255 for c in base.convert('HSV').split()]
    gold = (h * 360 > 28) & (h * 360 < 60) & (s > 0.35) & (v > 0.45); cer = (s < 0.18) & (v > 0.62)
    orm = np.zeros(base.size[::-1] + (3,))
    orm[..., 0] = np.where(gold, 0.8, np.where(cer, 0.6, 0.3)); orm[..., 1] = np.where(gold, 0.3, np.where(cer, 0.45, 0.65))
    Image.fromarray((orm * 255).astype(np.uint8)).save(T / f'har_{name}_metal_rough.png')
    print('GEARMAPS', name, base.size)
