#!/usr/bin/env python3
"""Face pre-screen sheet: per tier one row of the MM9 head (front, 3/4, profile; raw conversion = mirror image, flipped
here to game handedness) and ours (head_closeups.py rows: front, q34, true profile, low 3/4 from below, party view, and the
party view at 128 px). Args: <out png> <tier>=<closeups png>... (closeups rendered with views front,q34,rside,low34,party,back)"""
import sys
from PIL import Image, ImageDraw, ImageOps
out = sys.argv[1]
rows = []
for spec in sys.argv[2:]:
    tier, png = spec.split('=')
    lst = [l.split('\t') for l in open(png + '.list').read().splitlines()][0][1:]
    ours = [Image.open(f).convert('RGB').resize((300, 300)) for f in lst]
    small = ours[4].resize((128, 128), Image.LANCZOS).resize((300, 300), Image.NEAREST)
    mm = [ImageOps.mirror(Image.open(f'review/mm9_head/{tier.replace("_", "")}_{v}.png').convert('RGB')).resize((300, 300))
          for v in ('front', 'q34', 'left', 'back')]
    rows.append((tier, mm + ours + [small]))
W = 300 * len(rows[0][1]); s = Image.new('RGB', (W, 300 * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(s)
labels = ['MM9 front', 'MM9 3/4', 'MM9 profile', 'MM9 back', 'front', '3/4', 'profile', 'low 3/4', 'party', 'back', 'chest', 'chest 3/4', 'party @128px']
for r, (tier, ims) in enumerate(rows):
    for c, im in enumerate(ims):
        s.paste(im, (c * 300, r * 300)); d.text((c * 300 + 5, r * 300 + 5), f'{tier} {labels[c]}', fill=(255, 255, 0))
s.save(out); print('FACESHEET', out, s.size)
