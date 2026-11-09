#!/usr/bin/env python3
"""Review sheet of one model: native x2 sprite(s) | LOD0 front | three-quarter | side (review/<prop>/compare.png),
and a row of all LODs (lods.png), on grey; the mean colour of each tile's opaque pixels is printed under it.
Usage: sheet.py <prop> <x2 sprite file> [more x2 sprite files...] [--tile WxH]"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2')
args = sys.argv[1:]
W, H = 300, 450
if '--tile' in args:                       # --tile WxH: tile size (wide tiles for long, low models)
    i = args.index('--tile'); W, H = (int(v) for v in args[i + 1].split('x')); args = args[:i] + args[i + 2:]
prop, sprites = args[0], args[1:]
out = os.path.join(HERE, 'review', prop)
BACKGROUND = (110, 110, 120)


def tile(path):
    image = Image.open(path).convert('RGBA')
    bbox = image.split()[-1].getbbox() or (0, 0, image.width, image.height)
    image = image.crop(bbox)
    rgba = np.asarray(image).astype(float)
    mask = rgba[..., 3] > 128
    mean = tuple(int(v) for v in rgba[mask][:, :3].mean(0)) if mask.any() else (0, 0, 0)
    scale = min(W * 0.92 / image.width, H * 0.92 / image.height)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (W, H), BACKGROUND + (255,))
    canvas.alpha_composite(image, ((W - image.width) // 2, H - image.height - 6))
    return canvas.convert('RGB'), mean


def row(paths, labels, name):
    tiles = [tile(p) for p in paths]
    sheet = Image.new('RGB', (W * len(tiles), H + 36), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for i, ((t, mean), label) in enumerate(zip(tiles, labels)):
        sheet.paste(t, (i * W, 18)); draw.text((i * W + 6, 3), label, fill=(0, 0, 0))
        draw.text((i * W + 6, H + 21), f'mean {mean}', fill=(0, 0, 0))
    sheet.save(os.path.join(out, name)); print('SHEET', os.path.join(out, name))


views = sorted(glob.glob(os.path.join(out, 'lod0_y*.png')), key=lambda p: os.path.getmtime(p))[-3:]
row([os.path.join(X2, s) for s in sprites] + views,
    ['native ' + s for s in sprites] + ['LOD0 front', 'LOD0 three-quarter', 'LOD0 side'], 'compare.png')
levels = sorted(glob.glob(os.path.join(out, 'level*_y*.png')))
row(levels, [os.path.basename(p).split('_')[0] for p in levels], 'lods.png')
