#!/usr/bin/env python3
"""(Cow copy: tiers a, b; Running instead of AttackMelee; close sheet of the n/m/u/r/s/h/k/t shots) Viewer shots (review/shots/<inst|red>_<tier>/<shot>.png, shots.sh) -> side-by-side sheets: per tier the body row
(installed over reduced) and one face sheet (every tier, installed | reduced, with the per-shot pixel difference of the face
box printed). Usage: shot_sheets.py <tag>  -> review/sheet_body_<tag>_<tier>.png, review/sheet_face_<tag>.png"""
import sys
import numpy as np
from PIL import Image, ImageDraw
tag = sys.argv[1]; S = 'review/shots'; tiers = 'ab'
body = ['b0', 'b1', 'b2', 'b3', 'b4', 'b5']; head = ['f0', 'f1', 'f2', 'f3', 'f4']
LB = dict(b0='Standing front', b1='Standing 3/4', b2='Standing back', b3='Walking 3/4', b4='Running 3/4', b5='Death 3/4',
          f0='face front', f1='face 3/4', f2='profile', f3='low 3/4', f4='party')
def im(k, t, s): return Image.open(f'{S}/{k}_{t}/{s}.png').convert('RGB')
W = 400
for t in tiers:
    sh = Image.new('RGB', (W * len(body), (int(W * 1060 / 1440) + 20) * 2), (25, 25, 25)); d = ImageDraw.Draw(sh); H = int(W * 1060 / 1440)
    for j, k in enumerate(['inst', 'red']):
        for i, s in enumerate(body):
            a = im(k, t, s).resize((W, H)); sh.paste(a, (i * W, j * (H + 20) + 20))
            d.text((i * W + 4, j * (H + 20) + 4), f'{t} {"installed" if k == "inst" else tag} {LB[s]}', fill=(255, 220, 120))
    sh.save(f'review/sheet_body_{tag}_{t}.png')
H = int(W * 1060 / 1440)
sh = Image.new('RGB', (W * len(head), (H + 20) * 2 * len(tiers)), (25, 25, 25)); d = ImageDraw.Draw(sh)
for r, t in enumerate(tiers):
    for i, s in enumerate(head):
        a, b = np.asarray(im('inst', t, s), float), np.asarray(im('red', t, s), float)
        h, w = a.shape[:2]; box = (slice(int(h * 0.1), int(h * 0.75)), slice(int(w * 0.3), int(w * 0.7)))
        diff = np.abs(a - b).max(-1)
        print(f'FACE {t} {LB[s]}: whole image >8: {(diff > 8).mean() * 100:.2f} %, centre box >8: {(diff[box] > 8).mean() * 100:.2f} %, max {diff.max():.0f}')
        for j, x in enumerate((a, b)):
            p = Image.fromarray(x.astype(np.uint8)).resize((W, H)); y = (2 * r + j) * (H + 20)
            sh.paste(p, (i * W, y + 20)); d.text((i * W + 4, y + 4), f'{t} {["installed", tag][j]} {LB[s]}', fill=(255, 220, 120))
        Image.fromarray(np.clip(diff * 4, 0, 255).astype(np.uint8)).save(f'review/shots/diff_{t}_{s}.png')
sh.save(f'review/sheet_face_{tag}.png')

CL = ['n0', 'n1', 'm0', 'u0', 'r0', 's0', 'h0', 'k0', 't0']
CLB = dict(n0='neck side', n1='neck above-behind', m0='Fidget neck', u0='udder below', r0='rump rear-above', s0='Standup2 0.7 rump',
           h0='front hoof', k0='hind hoof', t0='tail tassel')
for t in tiers:
    sh = Image.new('RGB', (W * 5, (H + 20) * 4), (25, 25, 25)); d = ImageDraw.Draw(sh)
    for i, s in enumerate(CL[:5]):
        for j, k in enumerate(['inst', 'red']):
            sh.paste(im(k, t, s).resize((W, H)), (i * W, j * (H + 20) + 20)); d.text((i * W + 4, j * (H + 20) + 4), f'{t} {["installed", tag][j]} {CLB[s]}', fill=(255, 220, 120))
    for i, s in enumerate(CL[5:]):
        for j, k in enumerate(['inst', 'red']):
            y = (2 + j) * (H + 20)
            sh.paste(im(k, t, s).resize((W, H)), (i * W, y + 20)); d.text((i * W + 4, y + 4), f'{t} {["installed", tag][j]} {CLB[s]}', fill=(255, 220, 120))
    sh.save(f'review/sheet_close_{tag}_{t}.png')
