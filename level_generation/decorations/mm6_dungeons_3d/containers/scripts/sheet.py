#!/usr/bin/env python3
"""Review sheet of one model (review/<prop>/sheet.png): top row native sprite | LOD0 front | three-quarter | side,
bottom row every LOD from the three-quarter view, each labelled. Usage: sheet.py <prop> <native x2 file>"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
prop, sprite = sys.argv[1:3]
out = os.path.join(HERE, 'review', prop)
SIZE = 320


def mean_colour(path):
    """Mean sRGB of the opaque pixels (compare the render's displayed colour with the sprite's)."""
    pixels = np.asarray(Image.open(path).convert('RGBA'), np.float64)
    mask = pixels[..., 3] > 128
    return tuple(int(v) for v in pixels[mask][:, :3].mean(0)) if mask.any() else (0, 0, 0)


def tile(path, background=(96, 100, 110)):
    image = Image.open(path).convert('RGBA')
    image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = SIZE * 0.92 / max(image.size)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), background + (255,))
    canvas.alpha_composite(image, ((SIZE - image.width) // 2, SIZE - image.height - 6))
    return canvas.convert('RGB')


native = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', sprite)
views = sorted(glob.glob(os.path.join(out, 'lod0_y*.png')))
levels = sorted(glob.glob(os.path.join(out, 'level*_y*.png')))
rows = [([native] + views, ['native ' + sprite, 'LOD0 front', 'LOD0 three-quarter', 'LOD0 side']),
        (levels, [os.path.basename(p).split('_')[0].replace('level', 'LOD') for p in levels])]
width = max(len(r[0]) for r in rows) * SIZE
sheet = Image.new('RGB', (width, len(rows) * (SIZE + 20)), (255, 255, 255))
draw = ImageDraw.Draw(sheet)
for r, (paths, labels) in enumerate(rows):
    for i, (path, label) in enumerate(zip(paths, labels)):
        sheet.paste(tile(path), (i * SIZE, r * (SIZE + 20) + 20))
        draw.text((i * SIZE + 6, r * (SIZE + 20) + 4), f'{label}  mean {mean_colour(path)}', fill=(0, 0, 0))
sheet.save(os.path.join(out, 'sheet.png'))
print('SHEET', os.path.join(out, 'sheet.png'))
