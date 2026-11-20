#!/usr/bin/env python3
"""Staff atlas (256 x 512, three swatches: dark red-brown wood with grain, polished gold, red faceted gem) for
make_staff.py UVs, colours sampled from the native m274 staff (wood ~ (110, 40, 30), gold ~ (205, 160, 70),
gem ~ (210, 30, 30) with a bright facet highlight). Also writes a flat normal map and the metal/roughness map
(R specular mask, G roughness, B 0). Args: <prefix> [wood r,g,b] [gem r,g,b]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
T = Path(__file__).resolve().parents[1] / 'textures'; T.mkdir(exist_ok=True)
X = sys.argv[1] if len(sys.argv) > 1 else 'm274'
WOOD = [int(v) for v in (sys.argv[2] if len(sys.argv) > 2 else '112,42,30').split(',')]
GEM = [int(v) for v in (sys.argv[3] if len(sys.argv) > 3 else '215,28,30').split(',')]
W, H = 255, 512
rng = np.random.default_rng(7)
img = np.zeros((H, W, 3)); mr = np.zeros((H, W, 3))
y = np.arange(H)[:, None]; x = np.arange(85)[None, :]
grain = 0.85 + 0.15 * np.sin(x * 0.9 + np.sin(y * 0.05) * 3) + rng.normal(0, 0.03, (H, 85))
img[:, :85] = np.array(WOOD)[None, None, :] / 255 * grain[..., None]
mr[:, :85] = (0.15, 0.7, 0)
shine = 0.85 + 0.2 * np.sin(np.arange(85)[None, :] * 0.25) + rng.normal(0, 0.02, (H, 85))
img[:, 85:170] = np.array([212, 165, 70])[None, None, :] / 255 * shine[..., None]
mr[:, 85:170] = (1.0, 0.3, 0)
gx, gy = np.meshgrid(np.linspace(-1, 1, 85), np.linspace(-1, 1, H))
facet = 0.75 + 0.25 * np.sign(np.sin(gx * 5) * np.cos(gy * 7)) * 0.4
hi = np.exp(-((gx + 0.3) ** 2 + (gy - 0.3) ** 2) / 0.05) * 0.35
img[:, 170:] = np.clip(np.array(GEM)[None, None, :] / 255 * facet[..., None] + hi[..., None], 0, 1)
mr[:, 170:] = (0.9, 0.15, 0)
Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T / f'{X}_staff_basecolor.png')
Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(T / f'{X}_staff_metal_rough.png')
Image.fromarray(np.full((H, W, 3), (128, 128, 255), np.uint8)).save(T / f'{X}_staff_normal.png')
print('STAFFTEX', T / f'{X}_staff_basecolor.png')
