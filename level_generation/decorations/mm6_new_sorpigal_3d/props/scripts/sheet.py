#!/usr/bin/env python3
"""Review sheet of one prop: native sprite | LOD0 front | LOD0 three-quarter | LOD0 back, and a row of all LODs
(review/<prop>/compare.png, lods.png). Usage: sheet.py <prop> <native sprite name>"""
import glob, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prop, sprite = sys.argv[1:3]
out = os.path.join(HERE, 'review', prop)
NATIVE = os.path.join(HERE, '..', '..', 'mm6_new_sorpigal', 'native')


def tile(path, size=320, background=(128, 136, 150)):
    image = Image.open(path).convert('RGBA')
    bbox = image.getbbox() or (0, 0, image.width, image.height)
    image = image.crop(bbox)
    scale = size * 0.92 / max(image.size)
    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
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


views = sorted(glob.glob(os.path.join(out, 'lod0_y*.png')))
native = os.path.join(NATIVE, sprite + '.png')
if not os.path.exists(native):
    # Decorations outside New Sorpigal: the restored x2 sprite (any palette variant).
    native = sorted(glob.glob(os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2',
                                           sprite + '_p*.png')))[0]
row([native] + views, ['native ' + sprite, 'LOD0 front', 'LOD0 three-quarter',
    'LOD0 back'], 'compare.png')
levels = sorted(glob.glob(os.path.join(out, 'level*_y*.png')))
row(levels, [os.path.basename(p).split('_')[0] for p in levels], 'lods.png')
