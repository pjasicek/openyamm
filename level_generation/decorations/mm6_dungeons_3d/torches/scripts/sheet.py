#!/usr/bin/env python3
"""Review sheet of one model: native sprite | LOD0 flat front | LOD0 front | three-quarter | side, and a row of all
LODs (review/<prop>/compare.png, lods.png). Prints the mean colour of horizontal bands (given in native logical
units above the sprite's bottom) in the native sprite and in the flat front render, both cropped to their opaque
bounds and scaled to the native height. Usage: sheet.py <prop> <native texture> [z0:z1 ...]"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2')
prop, sprite = sys.argv[1:3]
bands = [tuple(float(v) for v in b.split(':')) for b in sys.argv[3:]]
out = os.path.join(HERE, 'review', prop)


def tile(path, size=320, background=(70, 72, 82)):
    image = Image.open(path).convert('RGBA')
    image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = size * 0.92 / max(image.size)
    resample = Image.NEAREST if scale > 2 else Image.LANCZOS
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), resample)
    canvas = Image.new('RGBA', (size, size), background + (255,))
    canvas.alpha_composite(image, ((size - image.width) // 2, size - image.height - 6))
    return canvas.convert('RGB')


def row(paths, labels, name):
    tiles = [tile(p) for p in paths]
    sheet = Image.new('RGB', (320 * len(tiles), 340), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (t, label) in enumerate(zip(tiles, labels)):
        sheet.paste(t, (i * 320, 20)); draw.text((i * 320 + 6, 4), label, fill=(0, 0, 0))
    sheet.save(os.path.join(out, name)); print('SHEET', os.path.join(out, name))


def band_means(path, logical_height, native_height):
    """Band means of an image whose opaque bounds span logical_height units (scaled from the sprite's bottom)."""
    image = Image.open(path).convert('RGBA')
    image = image.crop(image.getbbox())
    a = np.asarray(image).astype(float)
    rows = a.shape[0]
    result = []
    for z0, z1 in bands:
        top = int(rows * (1 - (z1 - native_height[0]) / logical_height))
        bottom = int(rows * (1 - (z0 - native_height[0]) / logical_height))
        part = a[max(top, 0):min(bottom, rows)]
        mask = part[..., 3] > 200
        result.append(tuple(int(v) for v in part[mask][:, :3].mean(0)) if mask.any() else None)
    return result


native = sorted(glob.glob(os.path.join(X2, sprite + '_p*.png')))[0]
flat = os.path.join(out, 'flat_y000.png')
views = sorted(glob.glob(os.path.join(out, 'lod0_y*.png')))
row([native, flat] + views, ['native ' + sprite, 'LOD0 flat (light 1)', 'LOD0 front', 'LOD0 three-quarter',
                             'LOD0 side'], 'compare.png')
levels = sorted(glob.glob(os.path.join(out, 'level*_y*.png')))
row(levels, [os.path.basename(p).split('_')[0] for p in levels], 'lods.png')
if bands:
    image = Image.open(native).convert('RGBA'); box = image.getbbox()
    span = ((image.height - box[3]) / 2, (image.height - box[1]) / 2)          # logical units of the opaque bounds
    for (z0, z1), n, m in zip(bands, band_means(native, span[1] - span[0], span),
                              band_means(flat, span[1] - span[0], span)):
        print(f'BAND {z0:5.1f}-{z1:5.1f} native {n} model {m}')
