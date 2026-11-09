#!/usr/bin/env python3
"""Sheets of a metal prop (small_review_metal.py renders): review/<prop>/metal_compare.png, one row per light
(dungeon emulation, lit metal), each the native x2 sprite then LOD0 front, three-quarter and side with the mean of
its opaque pixels; and metal_lods.png (lit, every LOD). The x2 sprite comes from assets_legacy/decorations_x2_20261016
(assets_dev/engine/decorations_x2 before 2026-10-16).
Usage: small_sheet_metal.py <prop> <x2 sprite file> [--lit-only]"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(HERE, '..', '..', '..', '..')
prop, sprite = sys.argv[1], sys.argv[2]
out = os.path.join(HERE, 'review', prop)
BACKGROUND = (110, 110, 120)
W, H = 300, 450
for folder in ('assets_legacy/decorations_x2_20261016', 'assets_dev/engine/decorations_x2'):
    native = os.path.join(REPO, folder, sprite)
    if os.path.exists(native):
        break


def tile(path):
    image = Image.open(path).convert('RGBA')
    image = image.crop(image.split()[-1].getbbox() or (0, 0, image.width, image.height))
    rgba = np.asarray(image).astype(float)
    mask = rgba[..., 3] > 128
    mean = tuple(int(v) for v in rgba[mask][:, :3].mean(0)) if mask.any() else (0, 0, 0)
    scale = min(W * 0.92 / image.width, H * 0.92 / image.height)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (W, H), BACKGROUND + (255,))
    canvas.alpha_composite(image, ((W - image.width) // 2, H - image.height - 6))
    return canvas.convert('RGB'), mean


def rows(spec, name):
    height = (H + 36) * len(spec)
    sheet = Image.new('RGB', (W * max(len(r[1]) for r in spec), height), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for k, (title, paths, labels) in enumerate(spec):
        y = k * (H + 36)
        for i, (p, label) in enumerate(zip(paths, labels)):
            t, mean = tile(p)
            sheet.paste(t, (i * W, y + 18)); draw.text((i * W + 6, y + 3), f'{title}: {label}', fill=(0, 0, 0))
            draw.text((i * W + 6, y + H + 21), f'mean {mean}', fill=(0, 0, 0))
    sheet.save(os.path.join(out, name)); print('SHEET', os.path.join(out, name))


def views(prefix):
    return sorted(glob.glob(os.path.join(out, f'{prefix}_y*.png')), key=os.path.getmtime)[-3:]


labels = ['native ' + sprite, 'LOD0 front', 'LOD0 three-quarter', 'LOD0 side']
spec = [] if '--lit-only' in sys.argv else [('dungeon (engine indoor emulation)', [native] + views('dungeon'), labels)]
spec.append(('lit metal', [native] + views('lit'), labels))
rows(spec, 'metal_compare.png')
levels = sorted(glob.glob(os.path.join(out, 'litlevel*_y*.png')))
rows([('lit', levels, [os.path.basename(p).split('_')[0] for p in levels])], 'metal_lods.png')
