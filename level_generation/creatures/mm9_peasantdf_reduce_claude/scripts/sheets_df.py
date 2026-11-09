#!/usr/bin/env python3
"""Viewer shots (review/shots/<inst|red>_d<tier>/<shot>.png, shots_df.sh) -> review sheets for every tier of the four designs:
- review/sheet_face_<tag>_<tier>.png: the five face shots, installed / reduced / |difference| x4 (face must be black);
- review/sheet_body_<tag>_<tier>.png: the six body shots, installed over reduced;
- review/sheet_close_<tag>_<tier>.png: the twelve close-ups (arms, skirt, hem, feet, hands), installed over reduced.
Prints per tier and face shot the share of pixels that differ by > 8 in the whole image and in the face box.
Usage: sheets_df.py <tag> [tiers d1a d1b ...]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
tag = sys.argv[1]; tiers = sys.argv[2:] or ['d1a', 'd1b', 'd2b', 'd3a', 'd3b', 'd4a', 'd4b']; S = 'review/shots'
LB = dict(b0='Standing front', b1='Standing 3/4', b2='Standing back', b3='Walking 3/4', b4='Talk 3/4', b5='Death 3/4',
          f0='face front', f1='face 3/4', f2='true profile', f3='low 3/4', f4='party', c0='arms 3/4', c1='skirt front',
          c2='skirt back', c3='Running skirt', c4='feet', c5='Talk arms', c6='shoulders back', c7='Hit', c8='L hand outside',
          c9='R hand outside', c10='R hand front', c11='hem from below')
W = 420; H = int(W * 763 / 1036)
im = lambda k, t, s: Image.open(f'{S}/{k}_{t}/{s}.png').convert('RGB')
for t in tiers:
    for kind, shots, rows in (('face', ['f0', 'f1', 'f2', 'f3', 'f4'], 3), ('body', ['b0', 'b1', 'b2', 'b3', 'b4', 'b5'], 2),
                              ('close', [f'c{i}' for i in range(12)], 2)):
        cols = 6 if kind == 'close' else len(shots); nrow = rows * (2 if kind == 'close' else 1)
        sh = Image.new('RGB', (W * cols, (H + 20) * nrow), (25, 25, 25)); d = ImageDraw.Draw(sh)
        for i, s in enumerate(shots):
            a, b = np.asarray(im('inst', t, s), float), np.asarray(im('red', t, s), float); diff = np.abs(a - b).max(-1)
            imgs = [a, b] + ([np.repeat(np.clip(diff * 4, 0, 255)[..., None], 3, -1)] if kind == 'face' else [])
            names = ['installed', tag, f'|diff| x4']
            c = i % cols; blk = (i // cols) * rows
            for j, x in enumerate(imgs):
                y = (blk + j) * (H + 20)
                sh.paste(Image.fromarray(x.astype(np.uint8)).resize((W, H)), (c * W, y + 20))
                d.text((c * W + 4, y + 4), f'{t} {names[j]} {LB[s]}', fill=(255, 220, 120))
            if kind == 'face':
                h, w = diff.shape; box = diff[int(h * 0.15):int(h * 0.85), int(w * 0.3):int(w * 0.7)]
                print(f'FACE {t} {LB[s]:12s}: image >8 {(diff > 8).mean() * 100:5.2f} %, centre box >8 {(box > 8).mean() * 100:5.2f} %, max {diff.max():.0f}')
        sh.save(f'review/sheet_{kind}_{tag}_{t}.png')
print('SHEETS', tag, tiers)
