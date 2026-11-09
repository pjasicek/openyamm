#!/usr/bin/env python3
"""Review sheets of one prop: native x2 sprite | LOD0 front | three-quarter | side | back (review/<prop>/compare.png)
and every LOD (lods.png). The sprite and the front render are scaled to the same height, as the engine binds them.
Usage: sheet.py <prop> <sprite texture name, e.g. dec05 or dec01a0>"""
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
prop, sprite = sys.argv[1:3]
out = os.path.join(HERE, 'review', prop)
SIZE = 360


def tile(path, background=(128, 136, 150)):
    image = Image.open(path).convert('RGBA')
    image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = SIZE * 0.92 / max(image.size)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), background + (255,))
    canvas.alpha_composite(image, ((SIZE - image.width) // 2, SIZE - image.height - 6))
    return canvas.convert('RGB')


def row(paths, labels, name):
    tiles = [tile(p) for p in paths]
    sheet = Image.new('RGB', (SIZE * len(tiles), SIZE + 20), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (t, label) in enumerate(zip(tiles, labels)):
        sheet.paste(t, (i * SIZE, 20)); draw.text((i * SIZE + 6, 4), label, fill=(0, 0, 0))
    sheet.save(os.path.join(out, name)); print('SHEET', os.path.join(out, name))


natives = sorted(glob.glob(os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', sprite + '_p*.png')))
views = sorted(glob.glob(os.path.join(out, 'lod0_y*.png')), key=lambda p: int(p.rsplit('_y', 1)[1][:-4]))
row(natives[:1] + views, ['native ' + sprite, 'LOD0 front', 'three-quarter', 'side', 'back'], 'compare.png')
levels = sorted(glob.glob(os.path.join(out, 'level*_y*.png')))
row(levels, [os.path.basename(p).split('_')[0] for p in levels], 'lods.png')
