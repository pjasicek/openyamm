#!/usr/bin/env python3
"""Review sheet of one fixture: native sprite (first frame, restored x2) | LOD0 front | three-quarter | side, over a
row of every LOD, all on one neutral background and scaled to the same height as the native sprite's frame
(review/<prop>/sheet.png). Usage: sheet.py <prop> <native texture name> [<native texture name> ...]"""
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2')
SIZE = 300
BACKGROUND = (96, 100, 110)


def tile(path, crop=True):
    image = Image.open(path).convert('RGBA')
    if crop:
        image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = SIZE * 0.92 / max(image.size)
    image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), BACKGROUND + (255,))
    canvas.alpha_composite(image, ((SIZE - image.width) // 2, SIZE - image.height - 6))
    return canvas.convert('RGB')


def row(paths, labels):
    strip = Image.new('RGB', (SIZE * len(paths), SIZE + 18), (255, 255, 255))
    draw = ImageDraw.Draw(strip)
    for i, (path, label) in enumerate(zip(paths, labels)):
        strip.paste(tile(path), (i * SIZE, 18))
        draw.text((i * SIZE + 6, 3), label, fill=(0, 0, 0))
    return strip


def main():
    prop, sprites = sys.argv[1], sys.argv[2:]
    out = os.path.join(HERE, 'review', prop)
    natives = [sorted(glob.glob(os.path.join(X2, f'{s}_p*.png')))[0] for s in sprites]
    views = sorted(glob.glob(os.path.join(out, 'lod0_*.png')))
    levels = sorted(glob.glob(os.path.join(out, 'level*.png')))
    top = row(natives + views, [f'native {s}' for s in sprites] + ['LOD0 front', 'LOD0 three-quarter', 'LOD0 side'])
    bottom = row(levels, [os.path.basename(p)[:-4] for p in levels])
    sheet = Image.new('RGB', (max(top.width, bottom.width), top.height + bottom.height), (255, 255, 255))
    sheet.paste(top, (0, 0))
    sheet.paste(bottom, (0, top.height))
    path = os.path.join(out, 'sheet.png')
    sheet.save(path)
    print('SHEET', path)


if __name__ == '__main__':
    main()
