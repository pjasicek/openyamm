#!/usr/bin/env python3
"""Flat-shaded rest geometry of the right hand and the head, installed (top) over a candidate (bottom).
Usage: geo_views.py <candidate glb> <tag> -> review/geo_hands_<tag>.png, review/geo_head_<tag>.png"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from set_view import views  # noqa: E402
cand, tag = sys.argv[1:3]
for k, f in (('inst', HERE / 'before' / 'mm9_annud.glb'), (tag, Path(cand))):
    _, _, _, D = glbio.load(f, 'Annud'); d = D['AnnudHead']; P, T = d['P'], d['T']; C = P[T].mean(1)
    rgb = np.tile([[200, 180, 160]], (len(T), 1))
    m = C[:, 0] > 0.3
    views(P, T[m], rgb[m], (0.38, 0.82, 0.95, 1.27), HERE / 'work' / f'hands_{k}.png', axes=('front', 'back'), size=600)
    m = np.abs(C[:, 0]) < 0.2
    views(P, T[m], rgb[m], (-0.15, 0.15, 1.42, 1.82), HERE / 'work' / f'headgeo_{k}.png', axes=('front', 'right', 'back'), size=420)
for n in ('hands', 'headgeo'):
    a = Image.open(HERE / 'work' / f'{n}_inst.png'); b = Image.open(HERE / 'work' / f'{n}_{tag}.png')
    s = Image.new('RGB', (a.width, a.height * 2)); s.paste(a, (0, 0)); s.paste(b, (0, a.height))
    s.save(HERE / 'review' / f'geo_{n}_{tag}.png')
