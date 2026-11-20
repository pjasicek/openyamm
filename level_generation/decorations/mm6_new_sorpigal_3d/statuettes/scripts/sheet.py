#!/usr/bin/env python3
"""Review sheet of a statuette pedestal: native x2 sprite | LOD0 front | three-quarter | side, and the statuette's top
(sprite crop | close front | close three-quarter), plus the LODs. Writes review/<animal>/compare.png and lods.png.
Usage: sheet.py <animal> <sprite>"""
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2')
animal, sprite = sys.argv[1:3]
out = os.path.join(HERE, 'review', animal)


def tile(image, size=320, background=(70, 72, 82)):
    image = image.convert('RGBA')
    image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = size * 0.92 / max(image.size)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))),
                         Image.NEAREST if scale > 2 else Image.LANCZOS)
    canvas = Image.new('RGBA', (size, size), background + (255,))
    canvas.alpha_composite(image, ((size - image.width) // 2, size - image.height - 6))
    return canvas.convert('RGB')


def row(images, labels, name):
    tiles = [tile(i) for i in images]
    sheet = Image.new('RGB', (320 * len(tiles), 340), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (t, label) in enumerate(zip(tiles, labels)):
        sheet.paste(t, (i * 320, 20)); draw.text((i * 320 + 6, 4), label, fill=(0, 0, 0))
    return sheet


native = Image.open(sorted(glob.glob(os.path.join(X2, sprite + '_p*.png')))[0]).convert('RGBA')
views = [Image.open(p) for p in sorted(glob.glob(os.path.join(out, 'lod0_y*.png')))]
top = native.crop((0, 0, native.width, int(native.height * 0.36)))
a = row([native] + views, ['native ' + sprite, 'LOD0 front', 'LOD0 three-quarter', 'LOD0 side'], '')
b = row([top, Image.open(os.path.join(out, 'top_front.png')), Image.open(os.path.join(out, 'top_tq.png'))],
        ['native top', 'statuette front (ortho)', 'statuette three-quarter'], '')
sheet = Image.new('RGB', (max(a.width, b.width), a.height + b.height), (255, 255, 255))
sheet.paste(a, (0, 0)); sheet.paste(b, (0, a.height))
sheet.save(os.path.join(out, 'compare.png'))
levels = [Image.open(p) for p in sorted(glob.glob(os.path.join(out, 'level*_y*.png')))]
row(levels, [f'LOD{k}' for k in range(len(levels))], '').save(os.path.join(out, 'lods.png'))
print('SHEET', os.path.join(out, 'compare.png'))
