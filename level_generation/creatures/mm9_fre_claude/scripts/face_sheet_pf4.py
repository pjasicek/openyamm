#!/usr/bin/env python3
"""Face pre-screen sheet (VARIANTS_BRIEF face lessons): per tier MM9 F4 (Blender, studio light, bind) above ours in the review viewer's own
lighting (scripts/face_shots_pf4.sh): front close-up, 3/4, true profile (left), low 3/4 from below, party view and its 128 px simulation;
a second sheet with the right profile, Talk at 1.4 s, both hood-edge / ear close-ups and under the jaw.
Args: <rev> (project folder) -> review/sheet_face_<rev>.png, review/sheet_face2_<rev>.png"""
import sys
from PIL import Image, ImageDraw
R = sys.argv[1]; C = 360; d = f'review/faces/{R}'
def sq(p, crop=True):
    im = Image.open(p).convert('RGB'); w, h = im.size
    if crop:
        c = min(w, h); im = im.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c))
    return im.resize((C, C), Image.LANCZOS)
def sim(p):
    im = Image.open(p).convert('RGB'); w, h = im.size; c = min(w, h)
    im = im.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c))
    return im.resize((128, 128), Image.LANCZOS).resize((C, C), Image.NEAREST)
cols = ['front', '3/4', 'profile', 'low 3/4 below', 'party view', 'party 128 px']
S = Image.new('RGB', (len(cols) * C, 4 * C + 30), (28, 28, 28)); dr = ImageDraw.Draw(S)
for c, lab in enumerate(cols): dr.text((c * C + 6, 8), lab, fill=(255, 255, 0))
r = 0
for t in 'ab':
    m = [sq(f'review/faces/mm9/pf4{t}_{v}.png') for v in ('front', 'q34', 'profile', 'q34low', 'party')] + [sim(f'review/faces/mm9/pf4{t}_party.png')]
    o = [sq(f'{d}/{t}_{v}.png') for v in ('front', 'q34', 'profL', 'low34', 'party')] + [sim(f'{d}/{t}_party.png')]
    for row, lab in ((m, f'MM9 F4{t}'), (o, f'ours pf4_{t} {R}')):
        for c, im in enumerate(row): S.paste(im, (c * C, 30 + r * C))
        dr.text((6, 30 + r * C + 6), lab, fill=(255, 255, 0)); r += 1
S.save(f'review/sheet_face_{R}.png')
cols2 = ['right profile', 'Talk 1.4 s', 'hood edge / ear L', 'hood edge / ear R', 'under the jaw']
S2 = Image.new('RGB', (len(cols2) * C, 2 * C + 30), (28, 28, 28)); dr = ImageDraw.Draw(S2)
for c, lab in enumerate(cols2): dr.text((c * C + 6, 8), lab, fill=(255, 255, 0))
for r, t in enumerate('ab'):
    for c, v in enumerate(('profR', 'talk', 'earL', 'earR', 'jaw')): S2.paste(sq(f'{d}/{t}_{v}.png'), (c * C, 30 + r * C))
    dr.text((6, 30 + r * C + 6), f'ours pf4_{t}', fill=(255, 255, 0))
S2.save(f'review/sheet_face2_{R}.png'); print('SHEETS', R)
