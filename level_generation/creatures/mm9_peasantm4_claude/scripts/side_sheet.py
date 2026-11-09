"""Rows of MM9 renders: side_sheet.py <dir> <out> <prefix body|head> <size> name1 name2 ... (labels drawn)."""
import sys
from PIL import Image, ImageDraw
d, out, pre, size = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
names = sys.argv[5:]
views = ['q34', 'front', 'left', 'back', 'right']
S = Image.new('RGB', (size * len(views), size * len(names)), (60, 60, 60))
dr = ImageDraw.Draw(S)
for r, n in enumerate(names):
    for c, v in enumerate(views):
        im = Image.open(f'{d}/{n}/{pre}_{v}.png').convert('RGB').resize((size, size))
        S.paste(im, (c * size, r * size))
    dr.text((6, r * size + 6), n, fill=(255, 255, 0))
S.save(out)
