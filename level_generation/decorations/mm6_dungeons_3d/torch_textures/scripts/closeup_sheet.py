#!/usr/bin/env python3
"""Close-up sheet: the native sprite cropped to native heights z0..z1 (same window as closeup.py) next to the model's
close-up renders. Writes review/<prop>/closeup.png. Usage: closeup_sheet.py <prop> <native texture> <z0> <z1>"""
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2')
prop, sprite, z0, z1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
out = os.path.join(HERE, 'review', prop)
native = Image.open(sorted(glob.glob(os.path.join(X2, sprite + '_p*.png')))[0]).convert('RGBA')
span = (z1 - z0) * 2                                   # x2 pixels per native unit
cx = native.width / 2
window = native.crop((int(cx - span / 2), int(native.height - z1 * 2), int(cx + span / 2), int(native.height - z0 * 2)))
tiles = [window.resize((512, 512), Image.NEAREST)]
tiles += [Image.open(p).convert('RGBA') for p in sorted(glob.glob(os.path.join(out, 'closeup_y*.png')))]
sheet = Image.new('RGB', (512 * len(tiles), 532), (255, 255, 255))
draw = ImageDraw.Draw(sheet)
for i, (tile, label) in enumerate(zip(tiles, ['native ' + sprite, 'LOD0 front', 'LOD0 three-quarter', 'LOD0 side'])):
    background = Image.new('RGBA', tile.size, (70, 72, 82, 255))
    background.alpha_composite(tile)
    sheet.paste(background.convert('RGB'), (i * 512, 20)); draw.text((i * 512 + 6, 4), label, fill=(0, 0, 0))
sheet.save(os.path.join(out, 'closeup.png')); print('SHEET', os.path.join(out, 'closeup.png'))
