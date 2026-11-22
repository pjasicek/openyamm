#!/usr/bin/env python3
"""Stage 3: the bakes -> export maps. Normal-bake misses (black) and wild hits (tilted past ~55 degrees) become flat;
every map is re-filled outside the UV islands from the nearest island texel (claude_shared/gutter_fill.py, last step).
Prints the base colour's sRGB luminance range (Khronos 30-243 check). Usage: finish_maps.py <id>"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'level_generation' / 'creatures' / 'claude_shared'))
from gutter_fill import coverage, pad  # noqa: E402

work = HERE.parent / 'work' / sys.argv[1]
tri_uv = np.load(work / 'uv.npz')['uv'].astype(np.float64)
for src, dst in (('bake_color.png', 'map_basecolor.png'), ('bake_normal.png', 'map_normal.png'),
                 ('bake_mr.png', 'map_mr.png'), ('bake_emit.png', 'map_emit.png')):
    if not (work / src).exists():
        continue
    a = np.asarray(Image.open(work / src).convert('RGB'))
    covered = coverage(tri_uv, a.shape[0], a.shape[1])
    if src == 'bake_normal.png':
        n = a.astype(float) / 127.5 - 1.0
        bad = covered & ((a.sum(-1) < 30) | (n[..., 2] < 0.57))
        a = a.copy()
        a[bad] = (128, 128, 255)
        print('NORMAL flat-filled %.1f %% of island texels' % (100 * bad.sum() / max(1, covered.sum())))
    a = pad(a, covered)
    if src == 'bake_mr.png':
        a = a.copy()
        a[..., 0] = 255
        print('MR roughness p5 %.2f p50 %.2f p95 %.2f, metallic mean %.2f' % (
            *(np.percentile(a[covered][:, 1], [5, 50, 95]) / 255), a[covered][:, 2].mean() / 255))
    if src == 'bake_color.png':
        lum = a[covered].astype(float) @ [0.2126, 0.7152, 0.0722]
        print('COLOUR atlas %.1f %%, sRGB luminance p1 %.0f p50 %.0f p99 %.0f, below 30: %.1f %%, above 243: %.1f %%' % (
            100 * covered.mean(), *np.percentile(lum, [1, 50, 99]), 100 * (lum < 30).mean(), 100 * (lum > 243).mean()))
    Image.fromarray(a, 'RGB').save(work / dst, optimize=True)
    print('MAP', dst, a.shape[1])
