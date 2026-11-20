#!/usr/bin/env python3
"""Review sheet: native sprite (restored x2, decorations_x2/<file>) | LOD0 front | three-quarter | side over a row of
all LODs, saved as review/<prop>/compare.png (both rows). Also prints the mean colour of the sprite's opaque pixels
and of the front render, to check the tints. Usage: sheet.py <prop> <x2 file name, e.g. corpse_p143.png>"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
prop, sprite = sys.argv[1:3]
out = os.path.join(HERE, 'review', prop)
TILE = 300


def tile(path, background=(96, 100, 110)):
    image = Image.open(path).convert('RGBA')
    image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = TILE * 0.92 / max(image.size)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (TILE, TILE), background + (255,))
    canvas.alpha_composite(image, ((TILE - image.width) // 2, TILE - image.height - 6))
    return canvas.convert('RGB')


def mean(path):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(float)
    m = a[..., 3] > 128
    return tuple(int(v) for v in a[m][:, :3].mean(0))


native = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', sprite)
views = sorted(glob.glob(os.path.join(out, 'lod0_y*.png')))
levels = sorted(glob.glob(os.path.join(out, 'level*_y*.png')))
top = [(native, 'native ' + sprite)] + list(zip(views, ['LOD0 front', 'three-quarter', 'side']))
bottom = [(p, os.path.basename(p).split('_')[0].replace('level', 'LOD')) for p in levels]
columns = max(len(top), len(bottom))
sheet = Image.new('RGB', (TILE * columns, 2 * (TILE + 20)), (255, 255, 255))
draw = ImageDraw.Draw(sheet)
for r, row in enumerate((top, bottom)):
    for i, (path, label) in enumerate(row):
        sheet.paste(tile(path), (i * TILE, r * (TILE + 20) + 20))
        draw.text((i * TILE + 6, r * (TILE + 20) + 4), label, fill=(0, 0, 0))
path = os.path.join(out, 'compare.png')
sheet.save(path)
print('SHEET', path, 'native mean', mean(native), 'front mean', mean(views[0]) if views else None)
