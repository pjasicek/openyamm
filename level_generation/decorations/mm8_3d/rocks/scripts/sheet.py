#!/usr/bin/env python3
"""Review sheet: native sprite (restored x2) | LOD0 front | three-quarter | side over a row of all LODs with their
triangle counts, saved as review/<rock>/compare.png. Prints the mean colour of the sprite's opaque pixels and of
the front render. Usage: sheet.py <rock> [triangles...]"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw



def sprite_path(name):
    """A native x2 sprite: the runtime copy, else the 2026-10-16 retirement archive (read only)."""
    live = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', name)
    return live if os.path.exists(live) else os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', name)


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
INV = {e['name']: e for e in json.load(open(os.path.join(HERE, '..', 'inventory.json')))}
prop, *tris = sys.argv[1:]
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


native = sprite_path(INV[prop]['files'][0])
views = sorted(glob.glob(os.path.join(out, 'lod0_y*.png')))     # front, three-quarter (+40), side (+90)
levels = sorted(glob.glob(os.path.join(out, 'level*_y*.png')))
top = [(native, f"native {INV[prop]['files'][0]} (h{INV[prop]['height']} w{INV[prop]['width']})")] + \
    list(zip(views, ['LOD0 front', 'three-quarter', 'side']))
bottom = [(p, os.path.basename(p).split('_')[0].replace('level', 'LOD') + (f'  {tris[i]} tris' if i < len(tris) else ''))
          for i, p in enumerate(levels)]
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
