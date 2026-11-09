"""MM9 vs ours sheet: rows of renders (ref_renders.py outputs) at the same views. Args: <out png> <label=prefix> ...
(prefix: path without _<view>.png). Views q34, front, left, back, right."""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; rows = [a.split('=', 1) for a in sys.argv[2:]]
views = ['q34', 'front', 'left', 'back', 'right']; W = 400
im = Image.new('RGB', (W * len(views), W * len(rows)), 'white'); d = ImageDraw.Draw(im)
for r, (lab, pre) in enumerate(rows):
    for c, v in enumerate(views):
        im.paste(Image.open(f'{pre}_{v}.png').convert('RGB').resize((W, W)), (c * W, r * W))
        d.text((c * W + 6, r * W + 6), f'{lab} {v}', fill='black')
im.save(out)
