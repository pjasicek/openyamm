#!/usr/bin/env python3
"""HOF2 dress paint: thin pale straight streaks (coordinator pre-screen of r6, 2026-11-04: "thin pale diagonal streaks across the dark
dress, front and back"; in the texture they are 1-2 texel perfectly straight lines, hundreds of texels long, drawn across the dress
islands by the texpass compose, already in phofc_tp_basecolor.png). Ridge texels (brighter than their 5x5 median by DL, on a background
darker than DARK) vote in a Hough transform (0.25 deg x 1 texel); every line with more than VOTES ridge texels is walked texel by texel
and its ridge texels (plus a 1-texel margin, only where the ridge runs for at least RUN texels) are refilled from the surrounding texels
(mask-normalised Gaussian, sigma 2.5). The dress's own speckle is not straight over hundreds of texels and stays.
Reads <tex>_prestreak.png (written on the first run or with RESET=1). Args: <basecolor png> [--dl 10] [--dark 140] [--votes 120] [--run 12]"""
import argparse, os, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
ap = argparse.ArgumentParser(); ap.add_argument('tex')
ap.add_argument('--dl', type=float, default=10); ap.add_argument('--dark', type=float, default=140)
ap.add_argument('--votes', type=int, default=120); ap.add_argument('--run', type=int, default=12)
o = ap.parse_args()
f = Path(o.tex); bk = f.with_name(f.stem + '_prestreak.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
I = np.asarray(Image.open(bk).convert('RGB'), float); N = I.shape[0]
L = I @ np.array([0.299, 0.587, 0.114]); med = ndimage.median_filter(L, 5); bg = ndimage.median_filter(L, 9)
R = ((L - med) > o.dl) & (bg < o.dark)
ys, xs = np.nonzero(R)
TH = np.radians(np.arange(0, 180, 0.25)); ct, st = np.cos(TH), np.sin(TH); D = int(np.ceil(N * 1.42))
acc = np.zeros((len(TH), 2 * D + 1), np.int32)
for s in range(0, len(xs), 20000):
    r = np.round(xs[s:s + 20000, None] * ct[None] + ys[s:s + 20000, None] * st[None]).astype(int) + D
    for k in range(len(TH)):
        acc[k] += np.bincount(r[:, k], minlength=2 * D + 1)
M = np.zeros_like(R); nl = 0
pk = (acc > o.votes) & (acc == ndimage.maximum_filter(acc, size=(9, 7)))
for k, rr in zip(*np.nonzero(pk)):
    rho = rr - D; t = np.arange(-D, D, 0.5)
    px = np.round(rho * ct[k] - t * st[k]).astype(int); py = np.round(rho * st[k] + t * ct[k]).astype(int)
    ins = (px >= 0) & (px < N) & (py >= 0) & (py < N); px, py = px[ins], py[ins]
    hit = np.zeros(len(px), bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            qx, qy = np.clip(px + dx, 0, N - 1), np.clip(py + dy, 0, N - 1); hit |= R[qy, qx]
    lab, n = ndimage.label(hit); took = 0
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl[0].stop - sl[0].start >= o.run * 2:          # samples are half-texel steps
            seg = np.arange(sl[0].start, sl[0].stop); M[py[seg], px[seg]] = True; took += 1
    nl += took > 0
M = ndimage.binary_dilation(M, iterations=1)
ok = ~ndimage.binary_dilation(M, iterations=1)
num = ndimage.gaussian_filter(I * ok[..., None], (2.5, 2.5, 0)); den = ndimage.gaussian_filter(ok.astype(float), 2.5)
fill = num / np.maximum(den, 1e-3)[..., None]
out = I.copy(); out[M] = fill[M]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
print('STREAKHEAL', o.tex, 'ridge texels', len(xs), 'lines', nl, 'texels healed', int(M.sum()))
