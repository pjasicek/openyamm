#!/usr/bin/env python3
"""Viewer shots (review/shots/{inst,red}/<shot>.png, shots.sh) -> side-by-side sheets, installed over reduced, plus the
pixel difference x4 for the face shots (one skin, no tiers). Usage: shot_sheets.py <tag>
-> review/sheet_face_<tag>.png, review/sheet_body_<tag>.png, review/sheet_close_<tag>.png"""
import sys
import numpy as np
from PIL import Image, ImageDraw
tag = sys.argv[1]; S = 'review/shots'; W = 400; H = int(W * 1060 / 1440)
LB = dict(b0='Standing front', b1='Standing 3/4', b2='Standing back', b3='Walking 3/4', b4='AttackMelee 3/4', b5='Death 3/4',
          f0='face front', f1='face 3/4', f2='profile', f3='low 3/4', f4='party', m0='mouth open (AttackRanged)',
          h0='horns from behind', h1='horns from above', c0='talons 3/4', c1='talons AttackMelee')
def im(k, s): return Image.open(f'{S}/{k}/{s}.png').convert('RGB')
def sheet(shots, out, diff=False):
    rows = 3 if diff else 2
    sh = Image.new('RGB', (W * len(shots), (H + 20) * rows), (25, 25, 25)); d = ImageDraw.Draw(sh)
    for i, s in enumerate(shots):
        a, b = im('inst', s), im('red', s)
        for j, (x, lab) in enumerate(((a, 'installed'), (b, tag))):
            sh.paste(x.resize((W, H)), (i * W, j * (H + 20) + 20)); d.text((i * W + 4, j * (H + 20) + 4), f'{lab} {LB[s]}', fill=(255, 220, 120))
        if diff:
            A, B = np.asarray(a, float), np.asarray(b, float); df = np.abs(A - B).max(-1)
            h, w = df.shape; box = df[int(h * .15):int(h * .85), int(w * .25):int(w * .75)]
            print(f'DIFF {LB[s]}: whole >8 {(df > 8).mean() * 100:.2f} %, centre box >8 {(box > 8).mean() * 100:.2f} %, max {df.max():.0f}')
            sh.paste(Image.fromarray(np.clip(df * 4, 0, 255).astype(np.uint8)).convert('RGB').resize((W, H)), (i * W, 2 * (H + 20) + 20))
            d.text((i * W + 4, 2 * (H + 20) + 4), f'diff x4 {LB[s]}', fill=(255, 220, 120))
    sh.save(out)
sheet(['f0', 'f1', 'f2', 'f3', 'f4', 'm0'], f'review/sheet_face_{tag}.png', True)
sheet(['b0', 'b1', 'b2', 'b3', 'b4', 'b5'], f'review/sheet_body_{tag}.png')
sheet(['c0', 'c1', 'h0', 'h1'], f'review/sheet_close_{tag}.png', True)
