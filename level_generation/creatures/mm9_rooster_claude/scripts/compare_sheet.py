#!/usr/bin/env python3
"""Review sheets from viewer shots. Usage: compare_sheet.py <out.png> <cols> <name> [...]: for each shot name, the pair
review/shots/mm9_<name>.png (MM9 original, optional) and review/shots/<name>.png (ours), cropped to the viewer canvas."""
import os, sys
from pathlib import Path
from PIL import Image, ImageDraw
S = Path(__file__).resolve().parents[1] / 'review' / 'shots'
out, cols, names = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
W, H = 640, 520
cells = []
for n in names:
    for pre, lab in ((('', 'ours '),) if os.environ.get('ONLY_OURS') else (('mm9_', 'MM9 '), ('', 'ours '))):
        f = S / f'{pre}{n}.png'
        if not f.exists():
            continue
        im = Image.open(f).convert('RGB')
        im = im.crop((0, 24, im.width, im.height - 40))
        k = min(W / im.width, H / im.height)
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        c = Image.new('RGB', (W, H + 18), (40, 42, 46))
        c.paste(im, ((W - im.width) // 2, 18))
        ImageDraw.Draw(c).text((6, 3), lab + n, fill=(255, 255, 255))
        cells.append(c)
rows = (len(cells) + cols - 1) // cols
sheet = Image.new('RGB', (W * cols, (H + 18) * rows), (40, 42, 46))
for i, c in enumerate(cells):
    sheet.paste(c, ((i % cols) * W, (i // cols) * (H + 18)))
sheet.save(out)
print('SHEET', out, sheet.size)
