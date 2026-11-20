"""Grid sheet: rows of images (each row a comma list), cell size, optional crop to the centre square. Args: <out> <cell> <row1 a.png,b.png> ..."""
import sys
from PIL import Image, ImageDraw
out, cell = sys.argv[1], int(sys.argv[2]); rows = [r.split(',') for r in sys.argv[3:]]
nc = max(len(r) for r in rows); W = Image.new('RGB', (cell * nc, cell * len(rows)), (40, 40, 40)); dr = ImageDraw.Draw(W)
for i, r in enumerate(rows):
    for j, f in enumerate(r):
        if not f: continue
        im = Image.open(f).convert('RGB'); w, h = im.size; m = min(w, h)
        im = im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((cell, cell), Image.LANCZOS)
        W.paste(im, (j * cell, i * cell)); dr.text((j * cell + 4, i * cell + 4), '/'.join(f.split('/')[-2:]), fill=(255, 255, 0))
W.save(out); print('GRID', out, W.size)
