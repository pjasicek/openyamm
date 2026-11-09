"""Sheet from a clay_frames.py tile list: one column per item, views stacked, label on top. Args: <list file> <out png> [tile px]"""
import sys
from PIL import Image, ImageDraw
lst, out = sys.argv[1:3]; px = int(sys.argv[3]) if len(sys.argv) > 3 else 300
rows = [l.split('\t') for l in open(lst).read().splitlines() if l]
nv = len(rows[0]) - 1
S = Image.new('RGB', (px * len(rows), px * nv + 18), (30, 30, 34)); d = ImageDraw.Draw(S)
for c, r in enumerate(rows):
    d.text((c * px + 4, 3), r[0], fill=(230, 230, 230))
    for k, f in enumerate(r[1:]):
        S.paste(Image.open(f).convert('RGB').resize((px, px)), (c * px, 18 + k * px))
S.save(out); print('SHEET', out, S.size)
