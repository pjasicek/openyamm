#!/usr/bin/env python3
"""The stat stone's orb texture: the red marble block of the upscaled skin (found on the native skin: red-dominant
texels), cropped and mirrored side by side so it tiles horizontally (textures/statstone_orb_basecolor.png); the UV
rectangle (u0, v0, u1, v1, Blender convention: v up) goes to work/orb_region.json for build.py's UV remap."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
native = np.array(Image.open(HERE / 'work/raw/statstone/skins/statstone.png').convert('RGB')).astype(float)
red = (native[..., 0] > 90) & (native[..., 0] > 2 * native[..., 1]) & (native[..., 0] > 2 * native[..., 2])
from scipy import ndimage
labels, n = ndimage.label(ndimage.binary_closing(red, iterations=2))
biggest = 1 + int(np.argmax(ndimage.sum(np.ones_like(labels), labels, range(1, n + 1))))
ys, xs = np.nonzero(labels == biggest)
h, w = red.shape
x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
print('red block px', x0, x1, y0, y1, 'of', w, h, 'coverage', red[y0:y1, x0:x1].mean().round(3))
region = [float(x0 / w), float(1 - y1 / h), float(x1 / w), float(1 - y0 / h)]
big = Image.open(HERE / 'textures/statstone_basecolor.png').convert('RGB')
s = big.width / w
crop = big.crop((int(x0 * s) + 2, int(y0 * s) + 2, int(x1 * s) - 2, int(y1 * s) - 2)).resize((256, 256))
tile = Image.new('RGB', (512, 256))
tile.paste(crop, (0, 0)); tile.paste(crop.transpose(Image.FLIP_LEFT_RIGHT), (256, 0))
tile.save(HERE / 'textures/statstone_orb_basecolor.png')
(HERE / 'work/orb_region.json').write_text(json.dumps(region))
print('region', region)
