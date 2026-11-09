#!/usr/bin/env python3
"""Review sheet of one model: native sprite(s) (restored x2 first frame) | LOD0 front | three-quarter | side, over a
row of every LOD, all on one neutral background and scaled to the same height (review/<prop>/sheet.png). Prints the
mean sRGB of the native sprite and of the LOD0 front render in six horizontal bands, top to bottom.
Usage: sheet.py <prop> <native texture> [<native texture> ...]"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_legacy', 'decorations_x2_20261016')
SIZE = 300
BACKGROUND = (96, 104, 112)


def crop(path):
    image = Image.open(path).convert('RGBA')
    return image.crop(image.getbbox() or (0, 0, image.width, image.height))


def tile(path):
    image = crop(path) if not path.endswith('night.png') else Image.open(path).convert('RGBA')
    scale = SIZE * 0.92 / max(image.size)
    image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), BACKGROUND + (255,))
    canvas.alpha_composite(image, ((SIZE - image.width) // 2, SIZE - image.height - 6))
    return canvas.convert('RGB')


def bands(path, count=6):
    a = np.asarray(crop(path)).astype(float)
    out = []
    for part in np.array_split(a, count, axis=0):
        m = part[..., 3] > 128
        out.append(tuple(int(v) for v in part[m][:, :3].mean(0)) if m.any() else None)
    return out


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
    levels += [p for p in [os.path.join(out, 'night.png')] if os.path.exists(p)]
    top = row(natives + views, [f'native {s}' for s in sprites] + ['LOD0 front', 'LOD0 three-quarter', 'LOD0 side'])
    bottom = row(levels, [os.path.basename(p)[:-4].replace('level', 'LOD').replace('night', 'night (glows)')
                          for p in levels])
    sheet = Image.new('RGB', (max(top.width, bottom.width), top.height + bottom.height), (255, 255, 255))
    sheet.paste(top, (0, 0))
    sheet.paste(bottom, (0, top.height))
    path = os.path.join(out, 'sheet.png')
    sheet.save(path)
    for label, p in (('native', natives[0]), ('model', views[0])):
        print(f'{label:7s}', ' '.join(str(b) for b in bands(p)))
    print('SHEET', path)


if __name__ == '__main__':
    main()
