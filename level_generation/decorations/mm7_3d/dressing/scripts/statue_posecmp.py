#!/usr/bin/env python3
"""Pose check sheet: the native views next to pose renders. Usage: statue_posecmp.py <prop> <out.png>
<x2 file>:<render file> ... (render files relative to review/<prop>/pose/)."""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2')
if not os.path.exists(os.path.join(X2, '7dec54a0_p3.png')):        # the statue sprites were archived 2026-10-16
    X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_legacy', 'decorations_x2_20261016')
prop, out = sys.argv[1], sys.argv[2]
H = 360
tiles = []
for pair in sys.argv[3:]:
    a, b = pair.split(':')
    for path in (os.path.join(X2, a), os.path.join(HERE, 'review', prop, 'pose', b)):
        im = Image.open(path).convert('RGBA'); im = im.crop(im.split()[-1].getbbox())
        im = im.resize((max(1, int(im.width * H / im.height)), H), Image.LANCZOS)
        tiles.append((os.path.basename(path), im))
W = sum(t.width for _, t in tiles) + 10 * len(tiles)
sheet = Image.new('RGB', (W, H + 20), (110, 110, 120)); d = ImageDraw.Draw(sheet); x = 0
for name, t in tiles:
    sheet.paste(t, (x, 20), t); d.text((x, 2), name[:18], fill=(255, 255, 255)); x += t.width + 10
sheet.save(out); print('SHEET', out)
