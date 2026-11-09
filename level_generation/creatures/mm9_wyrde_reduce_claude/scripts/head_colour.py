#!/usr/bin/env python3
"""Per head face colour class from the two tier head images (work/tex_WyrdeHead_{A,B}.png): Verdandi (B) paints the hair and the
hood in her green mantle colour, so a head face is 'cloth' when its B samples are green (and in A blue hood or blonde hair), and
'face' (skin, neck, lips, circlet, jewel, eyes) otherwise. Fraction of green samples per face -> work/head_colour.npz
(green_frac per head face, meanA, meanB). Also writes work/diag/head_col.npz for label_render.py."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_wyrde.glb', 'Wyrde')
h = D['WyrdeHead']; U, T = h['UV'], h['T']
k = 6; i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
W = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
uv = np.einsum('sk,fkc->fsc', W, U[T])
out = {}
for t in 'AB':
    im = np.asarray(Image.open(HERE / 'work' / f'tex_WyrdeHead_{t}.png').convert('RGB'), float); H, Wd = im.shape[:2]
    x = np.clip((uv[..., 0] * Wd).astype(int), 0, Wd - 1); y = np.clip((uv[..., 1] * H).astype(int), 0, H - 1)
    out[t] = im[y, x]                                           # (f, s, 3)
B = out['B']; r, g, bl = B[..., 0], B[..., 1], B[..., 2]
import colorsys
hsv = np.array(np.vectorize(colorsys.rgb_to_hsv)(r / 255, g / 255, bl / 255))   # (3, f, s)
hue = hsv[0] * 360; sat = hsv[1]
green = (hue >= 48) & (hue <= 160) & (sat > 0.2)              # Verdandi's moss-green (yellow-green) mantle colour
gf = green.mean(1)
A = out['A']; blue = (A[..., 2] > A[..., 0] * 1.3); bf = blue.mean(1)
np.savez(HERE / 'work' / 'head_colour.npz', green_frac=gf, blue_frac=bf, meanA=A.mean(1), meanB=B.mean(1))
g = np.load(HERE / 'work' / 'glb_parts.npz'); hm = g['mat'] == 1; sub = g['sub'][hm]
L = np.where(gf > 0.5, 2, 0); L[sub == 3] = 3; L[(gf > 0.05) & (gf <= 0.5)] = 1
L[g['inner'][hm]] = 5
for n_, v in (('face-ish (not green)', 0), ('mixed', 1), ('green cloth', 2), ('eye', 3), ('inner', 5)):
    print(n_, int((L == v).sum()), 'by seg sub', np.bincount(sub[L == v], minlength=4).tolist())
np.savez(HERE / 'work' / 'diag' / 'head_col.npz', P=h['P'], T=T, L=L)
