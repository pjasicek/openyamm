#!/usr/bin/env python3
"""MM9 (flat render) beside ours (viewer) per tier, plus strip and close-up sheets. Project folder."""
from pathlib import Path
from PIL import Image, ImageDraw
C = 330
def crop(f):
    im = Image.open(f).convert('RGB'); w, h = im.size; q = min(w, h)
    return im.crop(((w - q) // 2, (h - q) // 2, (w + q) // 2, (h + q) // 2)).resize((C, C), Image.LANCZOS)
s = Image.new('RGB', (6 * C, 3 * C), (30, 30, 34)); d = ImageDraw.Draw(s)
for r, (i, t) in enumerate(((1, 'a'), (2, 'b'), (3, 'c'))):
    for k, (v, o) in enumerate((('front', 'front'), ('back', 'back'), ('q34', 'quarter'))):
        s.paste(crop(f'references_hd/mm9_flat/t{i}_{v}.png'), (k * 2 * C, r * C)); s.paste(crop(f'review/shots/s{t}_{o}.png'), ((k * 2 + 1) * C, r * C))
        d.text((k * 2 * C + 6, r * C + 4), 'MM9 ' + t, fill=(255, 240, 120)); d.text(((k * 2 + 1) * C + 6, r * C + 4), 'ours ' + t, fill=(255, 240, 120))
s.save('review/mm9_vs_ours_tiers.png')
