#!/usr/bin/env python3
"""Before/after sheet from review-viewer shots (identical cameras). Args: <out png> <shot name> ... (tp_before_<n>, tp_after_<n>)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
S = Path(__file__).resolve().parents[2] / 'review' / 'shots'
out, names = sys.argv[1], sys.argv[2:]
cols = 2
w, h = 800, 556
sheet = Image.new('RGB', (cols * 2 * w, h * ((len(names) + cols - 1) // cols)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    x, y = (i % cols) * 2 * w, (i // cols) * h
    for k, tag in enumerate(('before', 'after')):
        im = Image.open(S / f'tp_{tag}_{n}.png').convert('RGB').crop((0, 40, 1036, 760)).resize((w, h), Image.LANCZOS)
        sheet.paste(im, (x + k * w, y))
        d.text((x + k * w + 8, y + 6), f'{n} {tag}', fill=(255, 255, 255))
sheet.save(out)
