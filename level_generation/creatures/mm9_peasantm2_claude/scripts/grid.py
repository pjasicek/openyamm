"""Compose a clay_frames .list into a grid: <list> <out png> [blocks per row] [tile px]. Each row of the list (clip:time, views) is a block."""
import sys
from PIL import Image, ImageDraw
L = [l.split('\t') for l in open(sys.argv[1]).read().splitlines()]
per = int(sys.argv[3]) if len(sys.argv) > 3 else 4; ts = int(sys.argv[4]) if len(sys.argv) > 4 else 300
nv = len(L[0]) - 1; rows = (len(L) + per - 1) // per
out = Image.new('RGB', (per * nv * ts, rows * ts), (40, 40, 40)); d = ImageDraw.Draw(out)
for k, r in enumerate(L):
    bx, by = (k % per) * nv * ts, (k // per) * ts
    for j, f in enumerate(r[1:]):
        out.paste(Image.open(f).convert('RGB').resize((ts, ts)), (bx + j * ts, by))
    d.text((bx + 4, by + 4), r[0], fill=(255, 255, 0))
out.save(sys.argv[2]); print('GRID', sys.argv[2], out.size)
