#!/usr/bin/env python3
"""MM9 vs ours, tier by tier: MM9's model with each skin (Blender renders, references_hd/renders full_<t>_*) beside our viewer
shots (review/shots/cmp_<tier>_*). Rows: tiers; columns: MM9 q34, ours q34, MM9 front, ours front, MM9 head, ours head.
Writes review/mm9_vs_ours_tiers.png"""
from PIL import Image, ImageDraw
C = 420
rows = [('a', 'cw_a', 'Colloidal Soldier'), ('b', 'cw_b', 'Colloidal Warrior'), ('c', 'cw_c', 'Colloidal Guardian')]
s = Image.new('RGB', (6 * C, 3 * C + 30), (30, 30, 34)); d = ImageDraw.Draw(s)
for k, h in enumerate(['MM9 3/4', 'ours 3/4', 'MM9 front', 'ours front', 'MM9 head', 'ours head']):
    d.text((k * C + 8, 8), h, fill=(255, 240, 120))
def fit(p, crop=None):
    im = Image.open(p).convert('RGB')
    if crop: w, h = im.size; im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    k = min(C / im.width, C / im.height); return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
for r, (t, v, name) in enumerate(rows):
    i = {'a': 1, 'b': 2, 'c': 3}[t]
    cells = [fit(f'references_hd/renders/full_{i}_q34.png'), fit(f'review/shots/cmp_{v}_q.png'),
             fit(f'references_hd/renders/full_{i}_front.png'), fit(f'review/shots/cmp_{v}_f.png'),
             fit(f'references_hd/mm9_head/t{i}_front.png'), fit(f'review/shots/cmp_{v}_h.png')]
    for k, im in enumerate(cells):
        s.paste(im, (k * C + (C - im.width) // 2, 30 + r * C + (C - im.height) // 2))
    d.text((8, 30 + r * C + 8), name, fill=(255, 255, 255))
s.save('review/mm9_vs_ours_tiers.png'); print('CMP written')
