"""Compose render_strip.py frames into before/after rows: compose_strip.py <strip dir> <out.png> <view> <tag>..."""
import sys
from PIL import Image, ImageDraw
d, out, view, tags = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
rows = []
for tag in tags:
    k = 0; ims = []
    while True:
        try:
            ims.append(Image.open(f'{d}/{tag}_{view}_{k}.png')); k += 1
        except FileNotFoundError:
            break
    w, h = ims[0].size; row = Image.new('RGB', (w * len(ims), h + 22), (20, 20, 22)); dr = ImageDraw.Draw(row)
    for k, im in enumerate(ims):
        row.paste(im, (k * w, 22)); dr.text((k * w + 6, 4), f'{tag}  viewer frame {k * 38.4 / len(ims):.1f}', fill=(255, 230, 120))
    rows.append(row)
img = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows))); y = 0
for r in rows:
    img.paste(r, (0, y)); y += r.height
img.save(out)
