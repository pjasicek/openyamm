#!/usr/bin/env python3
"""Sheet from a review/faces/<rev> folder: crops of the viewer shots (centre crop, the shots are 1440x1060). Args: <dir> <out> names..."""
import sys
from PIL import Image, ImageDraw
d, out, names = sys.argv[1], sys.argv[2], sys.argv[3:]
S = 520; cols = min(4, len(names)); rows = (len(names) + cols - 1) // cols
sh = Image.new('RGB', (S * cols, S * rows), (30, 30, 30)); dr = ImageDraw.Draw(sh)
for i, n in enumerate(names):
    im = Image.open(f'{d}/{n}.png').convert('RGB'); w, h = im.size; c = min(w, h)
    im = im.crop(((w - c) // 2, (h - c) // 2, (w + c) // 2, (h + c) // 2)).resize((S, S), Image.LANCZOS)
    sh.paste(im, ((i % cols) * S, (i // cols) * S)); dr.text(((i % cols) * S + 6, (i // cols) * S + 6), n, fill=(255, 255, 0))
sh.save(out); print('SHEET', out)
