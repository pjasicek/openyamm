#!/usr/bin/env python3
"""Installed vs reduced sheets from review/glbclose (glb_close.py on the tier viewer GLBs): per tier the face sheet and the
body/wing/motion sheet, installed row above reduced, textured and clay; prints the per-pixel difference of the textured
and clay face spots. -> review/sheet_face_<t>_<mode>.png, review/sheet_body_<t>_<mode>.png"""
from pathlib import Path
import os
import numpy as np
from PIL import Image, ImageDraw
REV, TRIS = os.environ.get('REV', 'r82'), os.environ.get('TRIS', '10,693')
H = Path(__file__).resolve().parents[1]; G = H / 'review' / 'glbclose'
SETS = {'face': ['face_front', 'face_q34', 'face_profile', 'face_low34', 'party', 'head_back', 'hair_top'],
        'body': ['body_front', 'body_q34', 'body_back', 'wing_l_front', 'wing_l_back', 'wing_knuckle', 'flap', 'attack', 'death']}
for t in 'abc':
    for name, spots in SETS.items():
        for mode in ('tex', 'clay'):
            W = 420; s = Image.new('RGB', (W * len(spots), 2 * W + 40), (20, 20, 20)); d = ImageDraw.Draw(s)
            d.text((6, 4), f'tier {t.upper()}: installed 12,599 (top) vs reduced {REV} {TRIS} (bottom), {mode}', fill=(240, 240, 240))
            for i, sp in enumerate(spots):
                for j, lab in enumerate(('installed', REV)):
                    s.paste(Image.open(G / f'{t}_{lab}_{sp}_{mode}.png').convert('RGB'), (i * W, 20 + j * (W + 20)))
                d.text((i * W + 6, 20 + W + 4), sp, fill=(240, 220, 120))
            s.save(H / 'review' / f'sheet_{name}_{t}_{mode}.png')
    for sp in SETS['face'][:5]:
        for mode in ('tex', 'clay'):
            a = np.asarray(Image.open(G / f'{t}_installed_{sp}_{mode}.png').convert('RGB'), float)
            b = np.asarray(Image.open(G / f'{t}_{REV}_{sp}_{mode}.png').convert('RGB'), float)
            dd = np.abs(a - b).max(2)
            Image.fromarray((np.clip(dd * 8, 0, 255)).astype(np.uint8)).save(G / f'diff_{t}_{sp}_{mode}.png')
            print(t, sp, mode, 'pixels differing >8:', int((dd > 8).sum()), 'of', dd.size, 'max', int(dd.max()))
