#!/usr/bin/env python3
"""Before/after sheet of fix_shots.py renders: one block per tier, rows before/after, columns = shots.
Usage: fix_sheet.py <before dir> <after dir> <out.png> <tier,...> <shot,...> [title]"""
import sys
from PIL import Image, ImageDraw
bd, ad, out, tiers, shots = sys.argv[1:6]
title = sys.argv[6] if len(sys.argv) > 6 else ''
tiers, shots = tiers.split(','), shots.split(',')
C, L, H = 260, 90, 28
img = Image.new('RGB', (L + C * len(shots), H + len(tiers) * (2 * C + H)), (32, 33, 36))
dr = ImageDraw.Draw(img)
dr.text((8, 8), title, fill=(230, 230, 230))
for j, s in enumerate(shots):
    dr.text((L + j * C + 6, H - 14), s, fill=(200, 200, 200))
for i, t in enumerate(tiers):
    y0 = H + i * (2 * C + H)
    dr.text((8, y0 + 4), f'tier {t.upper()}', fill=(255, 220, 120))
    for r, (lab, d) in enumerate((('before', bd), ('after', ad))):
        dr.text((8, y0 + H + r * C + C // 2), lab, fill=(220, 220, 220))
        for j, s in enumerate(shots):
            im = Image.open(f'{d}/{t}_{s}.png').convert('RGB').resize((C - 4, C - 4))
            img.paste(im, (L + j * C + 2, y0 + H + r * C + 2))
img.save(out)
print('SHEET', out, img.size)
