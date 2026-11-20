#!/usr/bin/env python3
"""Before/after review sheets from views.py renders (same spec on the installed and the lined GLB): pairs side by side, and a
face diff (|after - before| x 10, black = identical). Usage: pair_sheets.py <before dir> <after dir> <out prefix>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
B, A, OUT = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]


def load(p):
    return Image.open(p).convert('RGB')


def pairs(names, out, cell=520, cols=2):
    rows = (len(names) + cols - 1) // cols
    s = Image.new('RGB', (cols * 2 * cell, rows * (cell + 18)), 'white'); dr = ImageDraw.Draw(s)
    for k, n in enumerate(names):
        x0, y0 = (k % cols) * 2 * cell, (k // cols) * (cell + 18)
        for j, (d, tag) in enumerate(((B, 'installed'), (A, 'lined'))):
            im = load(d / f'{n}.png'); im.thumbnail((cell, cell)); s.paste(im, (x0 + j * cell, y0 + 18))
            dr.text((x0 + j * cell + 4, y0 + 3), f'{n} - {tag}', fill='black')
    s.save(out); print('SHEET', out, s.size)


names = sorted(p.stem for p in B.glob('*.png') if (A / p.name).exists())
face = [n for n in names if n.startswith('face_')]
for n in face:
    a, b = np.asarray(load(A / f'{n}.png'), np.int16), np.asarray(load(B / f'{n}.png'), np.int16)
    d = np.clip(np.abs(a - b) * 10, 0, 255).astype(np.uint8)
    Image.fromarray(d).save(f'{OUT}_diff_{n}.png')
    print('DIFF', n, 'max', int(np.abs(a - b).max()), 'pixels differing', int((np.abs(a - b).max(2) > 0).sum()))
groups = {'body': [n for n in names if n.startswith(('body_', 'party_', 'face_'))],
          'fur': [n for n in names if n.startswith('fur')],
          'cuffs': [n for n in names if n.startswith('cuff')],
          'collar_hair_hem': [n for n in names if n.startswith(('collar', 'hair', 'hem'))],
          'sweep': [n for n in names if n.startswith('sweep_')]}
for g, ns in groups.items():
    if ns:
        pairs(ns, f'{OUT}_{g}.png')
