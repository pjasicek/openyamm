#!/usr/bin/env python3
"""Face review sheet: MM9's head (front, profile) then our viewer shots (front, q34r, profl, low, under, party + party at 128 px).
Args: <shot dir> <prefix> <out png> [mm9 head strip]"""
import sys
from PIL import Image, ImageDraw
d, pre, out = sys.argv[1:4]; mm = sys.argv[4] if len(sys.argv) > 4 else 'references_hd/mm9_head_views.png'
C = 420; names = ['front', 'q34r', 'q34l', 'profl', 'low', 'under', 'party']
strip = Image.open(mm).convert('RGB'); n = strip.width // strip.height
cells = [strip.crop((k * strip.height, 0, (k + 1) * strip.height, strip.height)).resize((C, C)) for k in (0, 2)]
labels = ['MM9 front', 'MM9 profile']
for nm in names:
    im = Image.open(f'{d}/{pre}_{nm}.png').convert('RGB'); w, h = im.size; s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)); cells.append(im.resize((C, C))); labels.append(nm)
p = Image.open(f'{d}/{pre}_party.png').convert('RGB'); w, h = p.size; s = min(w, h); p = p.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
cells.append(p.resize((128, 128)).resize((C, C), Image.NEAREST)); labels.append('party 128 px')
o = Image.new('RGB', (C * 5, C * 2), (40, 40, 40)); dr = ImageDraw.Draw(o)
for k, (c, l) in enumerate(zip(cells, labels)):
    o.paste(c, ((k % 5) * C, (k // 5) * C)); dr.text(((k % 5) * C + 6, (k // 5) * C + 6), l, fill=(255, 255, 0))
o.save(out); print('SHEET', out)
