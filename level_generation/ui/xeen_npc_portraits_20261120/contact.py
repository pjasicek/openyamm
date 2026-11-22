#!/usr/bin/env python3
"""Contact sheet: contact.py OUT.png COLS SCALE PNG [PNG ...]; each portrait labelled with its NPC id.
A path given as mm7:NNNN adds a real MM7 portrait (labelled 'MM7') for comparison."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
out, cols, scale, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
w, h = 126 * scale, 146 * scale
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (w + 4) + 4, rows * (h + 18) + 4), (24, 24, 24))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    if f.startswith('mm7:'):
        path, label = ROOT / f'assets_dev/worlds/mm7/icons_x2/npc{f[4:]}.png', 'MM7 ' + f[4:]
    else:
        path, label = Path(f), Path(f).stem[3:]
        label = str(int(label) - 10000) if label.isdigit() else label
    im = Image.open(path).convert('RGB').resize((w, h), Image.NEAREST if scale > 1 else Image.LANCZOS)
    x, y = 4 + (i % cols) * (w + 4), 4 + (i // cols) * (h + 18)
    sheet.paste(im, (x, y))
    d.text((x + 2, y + h + 3), label, fill=(230, 230, 230))
sheet.save(out)
