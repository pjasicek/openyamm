#!/usr/bin/env python3
"""One contact sheet per tour: 480x270 tiles labelled with the shot name. Usage: contact_sheet.py <tour> | <sheet>=<tour>,<tour> [...]

Tiles are brightened (gamma 0.55 and auto-contrast) for legibility; the raw shots stay in shots/<tour>/.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

STUDY = Path(__file__).resolve().parents[1]
W, H, COLS = 480, 270, 3


def sheet(arg):
    name, _, tours = arg.partition('=')
    shots = [p for t in (tours or name).split(',') for p in sorted((STUDY / 'shots' / t).glob('*.png'))]
    rows = (len(shots) + COLS - 1) // COLS
    out = Image.new('RGB', (W * COLS, H * rows), (20, 20, 20))
    draw = ImageDraw.Draw(out)
    for i, path in enumerate(shots):
        x, y = (i % COLS) * W, (i // COLS) * H
        tile = Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS)
        tile = ImageOps.autocontrast(tile.point(lambda v: int(255 * (v / 255) ** 0.55)), cutoff=0.5)
        out.paste(tile, (x, y))
        label = path.stem if not tours else path.parent.name + '/' + path.stem
        draw.rectangle([x, y, x + 7 * len(label) + 8, y + 16], fill=(0, 0, 0))
        draw.text((x + 4, y + 3), label, fill=(255, 255, 0))
    target = STUDY / 'sheets' / (name + '.jpg')
    out.save(target, quality=88)
    print(target)


for n in sys.argv[1:]:
    sheet(n)
