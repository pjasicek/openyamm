"""Compose src_strips.py renders into one sheet: a row per clip. Args: dir out clip1,clip2,... [N]"""
import sys, os
from PIL import Image, ImageDraw
d, out, clips = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
N = int(sys.argv[4]) if len(sys.argv) > 4 else 6
rows = [c for c in clips if os.path.exists(os.path.join(d, f'{c}_0.png'))]
s = Image.open(os.path.join(d, f'{rows[0]}_0.png')).size[0]
o = Image.new('RGB', (s * N, s * len(rows)), (90, 90, 90)); dr = ImageDraw.Draw(o)
for r, c in enumerate(rows):
    for i in range(N):
        o.paste(Image.open(os.path.join(d, f'{c}_{i}.png')).convert('RGB'), (i * s, r * s))
    dr.text((4, r * s + 4), c, fill=(255, 255, 0))
o.save(out); print('SHEET', out, o.size)
