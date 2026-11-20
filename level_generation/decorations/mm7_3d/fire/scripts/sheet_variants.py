#!/usr/bin/env python3
"""Variant sheet: native sprite (restored x2 first frame) above each variant's LOD0 front render (and its night view).
Usage: sheet_variants.py <folder> <native texture>:<render stem> ..."""
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_legacy', 'decorations_x2_20261016')
W, H = 200, 300
BACKGROUND = (96, 104, 112)


def tile(path, crop=True):
    image = Image.open(path).convert('RGBA')
    if crop:
        image = image.crop(image.getbbox())
    scale = min(W * 0.92 / image.width, H * 0.94 / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    canvas = Image.new('RGBA', (W, H), BACKGROUND + (255,))
    canvas.alpha_composite(image, ((W - image.width) // 2, H - image.height - 4))
    return canvas.convert('RGB')


folder, pairs = sys.argv[1], [p.split(':') for p in sys.argv[2:]]
night = all(os.path.exists(os.path.join(HERE, 'review', folder, stem + '_night.png')) for _, stem in pairs)
sheet = Image.new('RGB', (W * len(pairs), (3 if night else 2) * H + 54), (255, 255, 255))
draw = ImageDraw.Draw(sheet)
for i, (native, stem) in enumerate(pairs):
    sheet.paste(tile(sorted(glob.glob(os.path.join(X2, f'{native}_p*.png')))[0]), (i * W, 18))
    sheet.paste(tile(os.path.join(HERE, 'review', folder, stem + '.png')), (i * W, H + 36))
    draw.text((i * W + 4, 3), native, fill=(0, 0, 0))
    draw.text((i * W + 4, H + 21), stem.replace('mm7_deco_', ''), fill=(0, 0, 0))
    if night:
        sheet.paste(tile(os.path.join(HERE, 'review', folder, stem + '_night.png'), crop=False), (i * W, 2 * H + 54))
        draw.text((i * W + 4, 2 * H + 39), 'night (halo)', fill=(0, 0, 0))
path = os.path.join(HERE, 'review', folder, 'sheet_variants.png')
sheet.save(path)
print('SHEET', path)
