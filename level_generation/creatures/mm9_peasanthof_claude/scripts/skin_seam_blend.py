#!/usr/bin/env python3
"""Skin tone continuous across the head paint's projection seams outside the central face (coordinator pre-screen of r6, 2026-11-04:
tier B "the faint line on her left cheek and any pale panel edge at the cheek sides near the braids"; tier A "the pale wedge at the left
jaw corner beside the braid"). Meshy's head paint changes tone where its front and side projections meet (a vertical line ~7 cm from
the centre line) and the head shell's flap at the jaw corner beside the braid catches the light against the dark collar.
Skin-coloured texels of the skin shell (own broad saturation < SATMAX, value > 90; hair painted on the shell stays) OUTSIDE the
central face box (|x| < XC, Y0 < y < Y1, z > -0.01: eyes, brows, nose, mouth untouched) take, as their broad colour, the 3D Gaussian
average (SIGMA) of the broad colours of all skin-coloured texels around them, across UV islands; detail (texel / own broad colour,
sigma 4 texels) kept. A weight eases in over 1 cm outside the box. Jaw-corner flap: skin texels below JAWY with |x| > JAWX are darkened
by JAWK (they sit in the jaw's shadow on MM9's model).
Reads <prefix>_head_basecolor_preskinseam.png (first run or RESET=1). Args: <glb> <head prefix> [--sigma 0.012] [--xc 0.05]
[--y0 1.665] [--y1 1.83] [--satmax 0.66] [--jawy 1.675] [--jawx 0.045] [--jawk 0.86]
[--sidex 0.066] [--sidek 1.0] [--sidey0 1.67] [--sidey1 1.80] [--jawz 9]
(r7: the pale wedge beside the jaw is the shell's strip at the nape sides, z < -0.03, lit sideways: --jawz -0.02 --jawk 0.65)"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('head')
for k, d in (('sigma', 0.012), ('xc', 0.05), ('y0', 1.665), ('y1', 1.83), ('satmax', 0.66), ('jawy', 1.675), ('jawx', 0.045), ('jawk', 1.0), ('sidex', 0.066), ('sidek', 1.0), ('sidey0', 1.67), ('sidey1', 1.80), ('jawz', 9.0)):
    ap.add_argument('--' + k, type=float, default=d)
o = ap.parse_args()
f = Path(f'textures/{o.head}_head_basecolor.png'); bk = f.with_name(f.stem + '_preskinseam.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
H = np.asarray(Image.open(bk).convert('RGB'), float); N = H.shape[0]
ph, part, _ = texel_parts(o.glb, 'PeasantHOFHead', N); P = np.nan_to_num(ph); skin = part == 0
x, y, z = np.abs(P[..., 0]), P[..., 1], P[..., 2]
s2 = 4 * N / 2048
num = ndimage.gaussian_filter(H * skin[..., None], (s2, s2, 0)); den = ndimage.gaussian_filter(skin.astype(float), s2)
lp = num / np.maximum(den, 1e-3)[..., None]
mx, mn = lp.max(-1), lp.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
skinc = skin & (sat < o.satmax) & (mx > 90)
dx = np.clip((x - o.xc) / 0.01, 0, 1); dy = np.maximum(np.clip((o.y0 - y) / 0.01, 0, 1), np.clip((y - o.y1) / 0.01, 0, 1))
dz = np.clip((-0.01 - z) / 0.01, 0, 1)
w = np.maximum(np.maximum(dx, dy), dz); w = np.where(skinc, w * w * (3 - 2 * w), 0.0)
si = np.nonzero(skinc); step = max(1, len(si[0]) // 80000)
tree = cKDTree(P[si][::step]); SC = lp[si][::step]
ti = np.nonzero(w > 0); out = H.copy()
for s in range(0, len(ti[0]), 40000):
    r_, c_ = ti[0][s:s + 40000], ti[1][s:s + 40000]
    d, nn = tree.query(P[r_, c_], 64, distance_upper_bound=3 * o.sigma)
    ok = np.isfinite(d); nn = np.where(ok, nn, 0)
    g = np.exp(-0.5 * (np.where(ok, d, 1e3) / o.sigma) ** 2) * ok
    C3 = (SC[nn] * g[..., None]).sum(1) / np.maximum(g.sum(1, keepdims=True), 1e-9)
    has = g.sum(1) > 1e-6
    ratio = np.where(has[:, None], np.clip(C3 / np.maximum(lp[r_, c_], 1), 0.7, 1.4), 1.0)
    ww = w[r_, c_][:, None]
    out[r_, c_] = H[r_, c_] * (1 - ww + ww * ratio)
jaw = skinc & (y < o.jawy) & (x > o.jawx) & (z < o.jawz)   # jawz: only behind the neck centre (the strip at the nape sides)
jw = np.clip((o.jawy - y) / 0.01, 0, 1) * np.clip((x - o.jawx) / 0.01, 0, 1) * jaw
out = out * (1 - (1 - o.jawk) * jw[..., None])
# cheek sides beside the braids (|x| > SIDEX between SIDEY0 and SIDEY1): the shell's side wall faces the key light where MM9's bob
# covers it; darkened by SIDEK (eased in over 1 cm) so the strip between cheek and braid stops reading as a pale panel
sw = skinc * np.clip((x - o.sidex) / 0.01, 0, 1) * np.clip((y - o.sidey0) / 0.01, 0, 1) * np.clip((o.sidey1 - y) / 0.01, 0, 1) * (z < 0.02)
out = out * (1 - (1 - o.sidek) * sw[..., None])
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
print('SKINSEAM', o.head, 'texels', int((w > 0).sum()), 'jaw flap texels', int(jaw.sum()))
