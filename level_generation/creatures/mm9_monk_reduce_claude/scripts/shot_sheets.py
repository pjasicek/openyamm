#!/usr/bin/env python3
"""Viewer shots (review/shots/<tier>_<inst|c72>_<shot>.png) -> side-by-side sheets per tier (installed | reduced) and the
face pixel difference (head shots). Usage: shot_sheets.py <tag>   -> review/sheet_body_<tier>.png, review/sheet_face.png"""
import sys
import numpy as np
from PIL import Image, ImageDraw
tag = sys.argv[1]; S = 'review/shots'; tiers = ['mk_a', 'mk_b', 'mk_c']
body = ['front', 'quarter', 'back', 'walk', 'cast', 'death']; head = ['hfront', 'hquarter', 'hleft', 'hright']
def im(t, k, s): return Image.open(f'{S}/{t}_{k}_{s}.png').convert('RGB')
W = 360
for t in tiers:
    sh = Image.new('RGB', (W * len(body), (W + 20) * 2), (25, 25, 25)); d = ImageDraw.Draw(sh)
    for j, k in enumerate(['inst', tag]):
        for i, s in enumerate(body):
            a = im(t, k, s); a = a.resize((W, int(W * a.height / a.width))).crop((0, 0, W, W))
            sh.paste(a, (i * W, j * (W + 20) + 20)); d.text((i * W + 4, j * (W + 20) + 4), f'{t} {k} {s}', fill=(255, 220, 120))
    sh.save(f'review/sheet_body_{t}.png')
sh = Image.new('RGB', (W * len(head) * 2, (W + 20) * len(tiers)), (25, 25, 25)); d = ImageDraw.Draw(sh)
for r, t in enumerate(tiers):
    for i, s in enumerate(head):
        a, b = np.asarray(im(t, 'inst', s), float), np.asarray(im(t, tag, s), float)
        diff = np.abs(a - b).max(-1); print(f'FACE {t} {s}: pixels differing >8: {(diff > 8).mean() * 100:.2f} %, >24: {(diff > 24).mean() * 100:.2f} %, max {diff.max():.0f}')
        for j, x in enumerate((a, b)):
            p = Image.fromarray(x.astype(np.uint8)); p = p.resize((W, int(W * p.height / p.width))).crop((0, 0, W, W))
            sh.paste(p, ((2 * i + j) * W, r * (W + 20) + 20)); d.text(((2 * i + j) * W + 4, r * (W + 20) + 4), f'{t} {["inst", tag][j]} {s}', fill=(255, 220, 120))
        Image.fromarray(np.clip(diff * 4, 0, 255).astype(np.uint8)).save(f'review/shots_diff_{t}_{s}.png')
sh.save('review/sheet_face.png')
