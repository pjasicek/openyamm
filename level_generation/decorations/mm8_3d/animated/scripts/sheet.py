#!/usr/bin/env python3
"""Review sheet of one model: native sprite frames (restored x2) | LOD0 front | three-quarter | side, a row of
every LOD, and, when review.py rendered one, the motion strip (the shader's vertex animation or the swing at six
times). review/<prop>/sheet.png. Usage: sheet.py <prop> <native texture> [<native texture> ...]"""
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Restored x2 sprites, retired from assets_dev on 2026-10-16.
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_legacy', 'decorations_x2_mm8_20261016')
SIZE = 300
BACKGROUND = (96, 100, 110)


def tile(path, crop=True, background=BACKGROUND):
    image = Image.open(path).convert('RGBA')
    if crop == 'dark':
        # Dark-background render: crop to what is brighter than the background (model and glow), with a margin.
        floor = image.convert('L').getpixel((2, 2)) + 10
        grey = image.convert('L').point(lambda v: 255 if v > floor else 0)
        box = grey.getbbox() or (0, 0, image.width, image.height)
        pad = 12
        image = image.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(image.width, box[2] + pad),
                            min(image.height, box[3] + pad)))
        background = image.convert('RGB').getpixel((2, 2))
    elif crop:
        image = image.crop(image.getbbox() or (0, 0, image.width, image.height))
    scale = SIZE * 0.92 / max(image.size)
    image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), background + (255,))
    canvas.alpha_composite(image, ((SIZE - image.width) // 2, SIZE - image.height - 6))
    return canvas.convert('RGB')


def row(paths, labels, crop=True):
    strip = Image.new('RGB', (SIZE * len(paths), SIZE + 18), (255, 255, 255))
    draw = ImageDraw.Draw(strip)
    for i, (path, label) in enumerate(zip(paths, labels)):
        strip.paste(tile(path, crop), (i * SIZE, 18))
        draw.text((i * SIZE + 6, 3), label, fill=(0, 0, 0))
    return strip


BMP = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', '_legacy', 'sprites_original')


def native(sprite, out):
    """The restored x2 frame, or (not archived: dec24x) the native bitmap at x2, palette index 0 transparent."""
    found = sorted(glob.glob(os.path.join(X2, f'{sprite}_p*.png')))
    if found:
        return found[0]
    name = next(f for f in os.listdir(BMP) if f.lower() == f'{sprite.lower()}.bmp')
    image = Image.open(os.path.join(BMP, name))
    rgba = image.convert('RGBA')
    if image.mode == 'P':
        index = image.load()
        pixels = rgba.load()
        for y in range(image.height):
            for x in range(image.width):
                if index[x, y] == 0:
                    pixels[x, y] = (0, 0, 0, 0)
    path = os.path.join(out, f'native_{sprite}.png')
    rgba.resize((rgba.width * 2, rgba.height * 2), Image.NEAREST).save(path)
    return path


def main():
    prop, sprites = sys.argv[1], sys.argv[2:]
    out = os.path.join(HERE, 'review', prop)
    natives = [native(s, out) for s in sprites]
    views = sorted(glob.glob(os.path.join(out, 'lod0_*.png')))
    levels = sorted(glob.glob(os.path.join(out, 'level*.png')))
    motion = sorted(glob.glob(os.path.join(out, 'motion_*.png')))
    rows = [row(natives + views, [f'native {s}' for s in sprites] + ['LOD0 front', 'LOD0 three-quarter',
                                                                      'LOD0 side', 'LOD0 from 60 deg below']),
            row(levels, [os.path.basename(p)[:-4] for p in levels])]
    dark = sorted(glob.glob(os.path.join(out, 'dark_*.png')))
    if dark:
        rows.append(row(dark, ['dark: front', 'dark: three-quarter'], crop='dark'))
    if motion:
        rows.append(row(motion, [f'motion t{i}' for i in range(len(motion))], crop=False))
    sheet = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)), (255, 255, 255))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    path = os.path.join(out, 'sheet.png')
    sheet.save(path)
    print('SHEET', path)


if __name__ == '__main__':
    main()
