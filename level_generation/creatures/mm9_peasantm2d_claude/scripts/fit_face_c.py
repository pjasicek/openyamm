#!/usr/bin/env python3
"""Fit Codex's tier-C face repaint to the geometry before projection (project folder). Codex kept the eyes and the lip line on their
pixels but drew the nose's alae ~28 % wider than our nose (painted nostrils beside the geometric ones = doubled nostrils) and the
smile ~12 % wider than the geometric lips (lip paint on the cheeks). Horizontal warp about the face midline, per zone:
  nose rows (z 0.742-0.785, faded 4 mm): |dx| scaled to S_NOSE near the centre, back to 1 at 5 cm;
  mouth rows (z 0.708-0.740, faded 4 mm): S_MOUTH, back to 1 at 5 cm.
Then painted catchlights (white specks inside the dark iris/pupil) take the 9 px median.
Last, the edge match: the repaint's low frequencies (Gaussian sigma 14 px) are replaced by the input render's (person D's skin, which
the neck, ears and hairline keep) near the face window's edge: weight 1 at the window border fading to 0 at 2.2 cm inside, and
partly (EDGE_IN) inside, so no ruddy rim at the jaw, the temples or under the hairline.
Args: <repaint png> <out png> [S_NOSE 0.78] [S_MOUTH 0.88] [input render png] [EDGE_IN 0.35]"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
src, dst = sys.argv[1:3]; SN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.78; SM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.88
R = 1254; CZ, ORTHO = 0.775, 0.30
im = np.asarray(Image.open(src).convert('RGB').resize((R, R), Image.LANCZOS), float)
Y, X = np.mgrid[0:R, 0:R] + 0.5
zm = CZ + (0.5 - Y / R) * ORTHO; dx = (X / R - 0.5) * ORTHO
ramp = lambda v, a, b: np.clip((v - a) / (b - a), 0, 1)
def zone(z0, z1): return ramp(zm, z0 - 0.004, z0) * (1 - ramp(zm, z1, z1 + 0.004))
def g(d, s, D):
    w = np.clip(1 - np.abs(d) / D, 0, 1); w = w * w * (3 - 2 * w)
    return d * (1 + (1 / s - 1) * w)          # output |dx| samples the repaint at a larger |dx| (compresses it)
src_dx = dx.copy()
for (z0, z1, s, D) in ((0.742, 0.785, SN, 0.050), (0.708, 0.740, SM, 0.050)):
    wz = zone(z0, z1); src_dx = src_dx * (1 - wz) + g(dx, s, D) * wz
sx = (src_dx / ORTHO + 0.5) * R - 0.5; sy = Y - 0.5
out = np.stack([ndimage.map_coordinates(im[..., c], [sy, sx], order=1, mode='nearest') for c in range(3)], -1)
lum = out.mean(2)
med = np.stack([ndimage.median_filter(out[..., c], size=15) for c in range(3)], -1)
eyes = (np.abs(np.abs(dx) - 0.031) < 0.012) & (np.abs(zm - 0.793) < 0.008)
mn = ndimage.minimum_filter(lum, size=13)
cl = eyes & (lum > 128) & (mn < 30)                 # bright specks next to the dark pupil = painted catchlights
cl = ndimage.binary_dilation(cl, iterations=2) & eyes & (lum > 95)
out[cl] = med[cl]
if len(sys.argv) > 5:
    ref = np.asarray(Image.open(sys.argv[5]).convert('RGB'), float); EI = float(sys.argv[6]) if len(sys.argv) > 6 else 0.35
    XW, ZLO, ZHI = 0.068, 0.655, 0.852                 # face_front.py's window
    d_edge = np.minimum.reduce([XW - np.abs(dx), zm - ZLO, ZHI - zm])
    e = np.clip(1 - d_edge / 0.022, 0, 1); e = EI + (1 - EI) * e * e * (3 - 2 * e)
    lo = lambda a: np.stack([ndimage.gaussian_filter(a[..., c], 14) for c in range(3)], -1)
    out = out + (lo(ref) - lo(out)) * e[..., None]
    print('FITFACE edge match on', sys.argv[5], 'inside weight', EI)
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
print('FITFACE catchlight px', int(cl.sum()), 'S_NOSE', SN, 'S_MOUTH', SM)
