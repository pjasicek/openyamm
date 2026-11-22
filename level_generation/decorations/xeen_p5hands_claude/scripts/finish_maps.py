#!/usr/bin/env python3
"""Stage 3: the bakes -> export maps. Colour, normal and roughness are re-filled outside the UV islands from the
nearest island texel (claude_shared/gutter_fill.py, last step on every map); the roughness becomes a glTF
metallic-roughness map (G roughness, B metallic 0). Prints the colour range (Khronos sRGB 30-243 check).
Usage: finish_maps.py (adapted from xeen_idols_claude)"""
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'level_generation' / 'creatures' / 'claude_shared'))
from gutter_fill import coverage, pad  # noqa: E402

work = HERE.parent / 'work'
tri_uv = np.load(work / 'uv.npz')['uv'].astype(np.float64)
for src, dst in (('bake_color.png', 'map_basecolor.png'), ('bake_normal.png', 'map_normal.png'),
                 ('bake_rough.png', 'map_mr.png')):
    a = np.asarray(Image.open(work / src).convert('RGB'))
    covered = coverage(tri_uv, a.shape[0], a.shape[1])
    if src == 'bake_normal.png':
        # projection misses (black, margin 0) and wild hits on other parts (tilted past ~55 degrees) become flat
        n = a.astype(float) / 127.5 - 1.0
        bad = covered & ((a.sum(-1) < 30) | (n[..., 2] < 0.57))
        a = a.copy()
        a[bad] = (128, 128, 255)
        print('NORMAL flat-filled %.1f %% of island texels' % (100 * bad.sum() / covered.sum()))
    a = pad(a, covered)
    if src == 'bake_rough.png':
        mr = np.zeros_like(a)
        mr[..., 0] = 255
        mr[..., 1] = a[..., 1]
        a = mr
    if src == 'bake_color.png':
        lum = a[covered].astype(float) @ [0.2126, 0.7152, 0.0722]
        print('COLOUR atlas %.1f %%, sRGB luminance p1 %.0f p50 %.0f p99 %.0f, below 30: %.1f %%' % (
            100 * covered.mean(), *np.percentile(lum, [1, 50, 99]), 100 * (lum < 30).mean()))
    Image.fromarray(a, 'RGB').save(work / dst, optimize=True)
    print('MAP', dst, a.shape[1])
