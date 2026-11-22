"""Rows of <name>_front/_q/_side renders. Usage: rowsheet.py <dir> <out> [scale]"""
import os, sys
from PIL import Image, ImageDraw
d, out = sys.argv[1:3]; s = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
names = sorted({f.rsplit('_', 1)[0] for f in os.listdir(d) if f.endswith('_front.png')})
w, h = int(400 * s), int(500 * s)
sheet = Image.new('RGB', (w * 3, h * len(names)), 'white'); dr = ImageDraw.Draw(sheet)
for r, n in enumerate(names):
    for c, v in enumerate(('front', 'q', 'side')):
        sheet.paste(Image.open(f'{d}/{n}_{v}.png').convert('RGB').resize((w, h)), (c * w, r * h))
    dr.text((4, r * h + 4), n, fill='yellow')
sheet.save(out)
