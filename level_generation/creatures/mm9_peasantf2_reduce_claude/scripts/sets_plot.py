#!/usr/bin/env python3
"""Diagnostic plot of a set (PIL): faces front/side/back/top, kept black, lining yellow, groups coloured
(0 grey, 1 hands red, 2 cap orange, 3 skirt green, 4 shins blue, 5 braid purple, 6 tie brown). Usage: sets_plot.py <tag>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
tag = sys.argv[1]; s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); L = np.load(HERE / 'work' / 'glb_parts.npz')
sys.path.insert(0, str(HERE / 'scripts')); import bglbio as g  # noqa: E402
doc, b = g.read(HERE / 'before' / 'mm9_peasantf2.glb'); node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantF2' and 'mesh' in n)
pr = g.prims(doc, b, node['mesh']); TRI = np.concatenate([p['POSITION'].astype(float)[p['T']] for p in pr])
k = s['keep']; gr = s['group']; li = s['lining']
col = np.array([(190, 190, 190), (220, 40, 40), (255, 150, 0), (40, 170, 40), (40, 90, 230), (150, 60, 200), (140, 90, 40)])
fc = col[gr]; fc[k] = (20, 20, 20); fc[li] = (255, 240, 160)
S = 700; out = Image.new('RGB', (S * 4, S * 2 + 40), (255, 255, 255)); d0 = ImageDraw.Draw(out)
ymin, ymax = TRI[..., 1].min(), TRI[..., 1].max(); sc = (S * 2 - 20) / (ymax - ymin)
for vi, (ax, sg) in enumerate([(0, 1), (2, 1), (0, -1), (2, -1)]):
    im = Image.new('RGB', (S, S * 2), (255, 255, 255)); dr = ImageDraw.Draw(im)
    depth = TRI[..., 2 - ax if ax == 0 else 0].mean(1) * (sg if ax == 0 else -sg)
    for f in np.argsort(depth):
        pts = [(S / 2 + sg * p[ax] * sc, 10 + (ymax - p[1]) * sc) for p in TRI[f]]
        dr.polygon(pts, fill=tuple(int(x) for x in fc[f]), outline=(90, 90, 90))
    out.paste(im, (vi * S, 40))
d0.text((10, 10), f'set {tag}: kept black, lining yellow, hands red, cap orange, skirt green, shins blue, braid purple, tie brown; views front, side(+z right), back, side', fill=(0, 0, 0))
out.save(HERE / 'review' / f'sets_{tag}.png')
