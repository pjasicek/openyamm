#!/usr/bin/env python3
"""Finished textures shown at the proportions their faces show them: montage_fin.py <out> <height> <name>..."""
import sys
import yaml
from PIL import Image, ImageDraw
from pathlib import Path
HERE = Path(__file__).resolve().parent
sp = yaml.safe_load((HERE / 'specs.yml').read_text())['textures']
out, cell = sys.argv[1], int(sys.argv[2])
cells = []
for n in sys.argv[3:]:
    im = Image.open(HERE / 'finished' / f'{n}.png').convert('RGB')
    w, h = sp[n].get('art', sp[n]['size'])
    s = cell / max(w, h)
    im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
    ImageDraw.Draw(im).text((4, 4), n, fill=(255, 255, 0))
    cells.append(im)
width = 1600
rows, x, y, rh = [], 0, 0, 0
S = Image.new('RGB', (width, 4000), (40, 40, 40))
for im in cells:
    if x + im.width > width:
        x, y, rh = 0, y + rh + 8, 0
    S.paste(im, (x, y))
    x += im.width + 8
    rh = max(rh, im.height)
S.crop((0, 0, width, y + rh)).save(out, quality=90)
