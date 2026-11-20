#!/usr/bin/env python3
"""Fit the Codex repaint's nose onto the geometry's nose (nose fix 2026-11-02, user: "something wrong with her nose + lip? like double
textures?"). The repaint draws a nose about 1.35x wider than ours whose tip ends ~6 mm below our nose's underside, so projected from the
front its tip, nostrils and alae landed on the upper lip while our nose's own down-facing underside (visible from the front and shaded dark)
cut across it: a grey patch with a second pair of nostrils under it. (The previous pass kept Meshy's first paint on the nose tip instead,
which is also lower than the geometry and lighter along the bridge, so a paint boundary ringed the alae and a pale stripe ran up the bridge.)
This warps the repaint in the flat front frame (in_face render: 1254 px, centre z 0.6703, 0.26 m wide; nose centre column 627) so that
its tip highlight sits on the geometry's tip (rows 665-680), its nostrils on the underside band (685-720) and its tip shadow on the
columella base (~738), and its alae at the geometry's width (half 60 px against the repaint's 81). Pull map: rows by piecewise-linear knots,
columns scaled about the centre; both eased out sideways (the cheeks and nasolabial folds stay) and above/below the nose.
Tier A's repaint drew the nose as two separate ear-like flaps with no tip (it traced Meshy's ringed nostrils): with --nose-from <tier B's
aligned repaint> the nose (an ellipse round it, soft edge) is taken from that repaint instead, its colour matched to this one by per-channel
gains on a ring round the nose (bridge, cheeks beside it, upper lip), before the warp.
Args: <aligned repaint png> <out png> [--nose-from <aligned repaint png>]   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
A, OUT = sys.argv[1:3]
b = np.asarray(Image.open(A).convert('RGB'), float); H, W = b.shape[:2]; C = 627.0
if '--nose-from' in sys.argv:
    o = np.asarray(Image.open(sys.argv[sys.argv.index('--nose-from') + 1]).convert('RGB'), float)
    yy0, xx0 = np.mgrid[0:H, 0:W].astype(float); r = np.sqrt(((xx0 - C) / 100.0) ** 2 + ((yy0 - 672.0) / 118.0) ** 2)
    ring = (r > 1.15) & (r < 1.6) & (yy0 < 830)
    g = b[ring].mean(0) / np.maximum(o[ring].mean(0), 1e-3); print('nose from other repaint, gains', np.round(g, 3))
    k = np.clip((1.15 - r) / 0.25, 0, 1); k = (k * k * (3 - 2 * k))[..., None]
    b = b * (1 - k) + np.clip(o * g, 0, 255) * k
OUT_K = np.array([0, 560, 672, 700, 722, 738, 790, 830, 1254], float)       # rows of the output (geometry)
REP_K = np.array([0, 560, 700, 727, 752, 767, 805, 830, 1254], float)       # rows of the repaint sampled there
yy, xx = np.mgrid[0:H, 0:W].astype(float); dx = xx - C
def ss(v, a, c): t = np.clip((v - a) / (c - a), 0, 1); return t * t * (3 - 2 * t)
side = 1 - ss(np.abs(dx), 70, 140)                                   # vertical pull full on the nose, none on the cheeks
sy = yy + (np.interp(yy, OUT_K, REP_K) - yy) * side
K = 1 + 0.35 * ss(yy, 600, 670) * (1 - ss(yy, 770, 815))             # the nose's width
w = 1 - np.clip((np.abs(dx) - 60) / 70, 0, 1)
sx = C + dx * (1 + (K - 1) * w)
out = np.stack([ndimage.map_coordinates(b[..., c], [sy, sx], order=1, mode='nearest') for c in range(3)], -1)
Image.fromarray(np.uint8(np.clip(out, 0, 255) + 0.5)).save(OUT); print('NOSE WARP', OUT)
