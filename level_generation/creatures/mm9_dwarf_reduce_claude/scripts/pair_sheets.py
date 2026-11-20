#!/usr/bin/env python3
"""Installed vs reduced sheets from review/glbclose (glb_close.py): per tier one sheet of the face spots and one of the
cut regions, installed row above reduced. Also the per-pixel difference of the textured face close-ups.
-> review/sheet_face_<t>.png, review/sheet_body_<t>.png, prints face diff stats."""
from pathlib import Path
import os
import numpy as np
REV, TRIS = os.environ.get('REV', '71'), os.environ.get('TRIS', '9,683')
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parents[1]; G = H / 'review' / 'glbclose'
SETS = {'face': ['face_front', 'face_q34', 'face_profile', 'face_low34', 'party', 'head_back'],
        'body': ['chest', 'back', 'boots', 'fist_r', 'fist_l', 'attack', 'death'],
        'escapes': ['arm_r_out', 'arm_r_front', 'arm_r_back', 'arm_l_out', 'arm_l_back', 'calves_back']}
for t in 'abc':
    for name, spots in SETS.items():
        for mode in ('tex', 'clay'):
            W = 420; s = Image.new('RGB', (W * len(spots), 2 * W + 40), (20, 20, 20)); d = ImageDraw.Draw(s)
            d.text((6, 4), f'{t.upper()} installed 13,643 (top) vs reduced {TRIS} (bottom), {mode}', fill=(240, 240, 240))
            for i, sp in enumerate(spots):
                for j, lab in enumerate(('100', REV)):
                    s.paste(Image.open(G / f'{t}{lab}_{sp}_{mode}.png').convert('RGB'), (i * W, 20 + j * (W + 20)))
                d.text((i * W + 6, 20 + W + 4), sp, fill=(240, 220, 120))
            s.save(H / 'review' / f'sheet_{name}_{t}_{mode}.png')
    for sp in SETS['face'][:4]:
        a = np.asarray(Image.open(G / f'{t}100_{sp}_tex.png').convert('RGB'), float)
        b = np.asarray(Image.open(G / f'{t}{REV}_{sp}_tex.png').convert('RGB'), float)
        dd = np.abs(a - b).max(2)
        print(t, sp, 'pixels differing >8:', int((dd > 8).sum()), 'of', dd.size, 'max', int(dd.max()))
