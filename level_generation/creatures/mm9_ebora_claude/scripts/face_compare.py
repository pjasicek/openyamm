#!/usr/bin/env python3
"""Face comparison sheet (head fixes 3): reference row (HD master front / three-quarter, MM9 Ebora front / three-quarter,
MM9 SIREN1 front / three-quarter), then per tier our face close-ups, front and three-quarter, beside the same crops of the
installed build before the fix when given. Usage: face_compare.py <out png> <row label>=<front png>,<q png>[,<before front>,<before q>] ..."""
import sys
from PIL import Image, ImageDraw
C = 420
H = 'references_hd/'
def crop(path, box):
    im = Image.open(path).convert('RGBA'); bg = Image.new('RGBA', im.size, (60, 60, 60, 255)); bg.alpha_composite(im)
    return bg.convert('RGB').crop(box).resize((C, C), Image.LANCZOS)
def shot(path):
    im = Image.open(path).convert('RGB'); w, h = im.size; m = min(w, h)
    return im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((C, C), Image.LANCZOS)
refs = [(crop(H + '01_front.png', (437, 112, 587, 262)), 'HD master front'),
        (crop(H + '00_three_quarter.png', (458, 132, 608, 282)), 'HD master 3/4'),
        (crop(H + 'mm9_head_views_ebora.png', (830, 190, 1090, 450)), 'MM9 Ebora front'),
        (crop(H + 'mm9_head_views_ebora.png', (270, 205, 530, 465)), 'MM9 Ebora 3/4'),
        (crop(H + 'mm9_head_views_siren1.png', (830, 190, 1090, 450)), 'MM9 SIREN1 front'),
        (crop(H + 'mm9_head_views_siren1.png', (270, 205, 530, 465)), 'MM9 SIREN1 3/4')]
rows = [refs]
for a in sys.argv[2:]:
    lab, _, ps = a.partition('='); ps = ps.split(',')
    cells = [(shot(ps[0]), f'{lab} ours front'), (shot(ps[1]), f'{lab} ours 3/4')]
    if len(ps) > 3: cells += [(shot(ps[2]), f'{lab} before front'), (shot(ps[3]), f'{lab} before 3/4')]
    rows.append(cells)
W = max(len(r) for r in rows)
out = Image.new('RGB', (W * C, len(rows) * C), (30, 30, 30)); d = ImageDraw.Draw(out)
for i, r in enumerate(rows):
    for j, (im, lab) in enumerate(r):
        out.paste(im, (j * C, i * C)); d.rectangle((j * C, i * C, j * C + 8 * len(lab) + 8, i * C + 16), fill=(0, 0, 0))
        d.text((j * C + 4, i * C + 3), lab, fill=(255, 255, 0))
out.save(sys.argv[1]); print('SHEET', sys.argv[1], out.size)
