#!/usr/bin/env python3
"""Neck strip of a PeasantHOF head set toned to the body's neck skin (finishing round 2026-11-04: the face sheet showed the
pale-pink body neck between jagged orange polygons below the jaw: the head shell's lowest strip, sides and nape, is painted
a saturated orange (sRGB ~185/111/72) where the tier's body skin under it is ~223/141/110; a flat-colour render had no
such pattern, so it is paint). Head skin-shell texels (part SKIN) below Y_TOP take the target colour (the tier's body skin
next to the seam, measured on its shader-equivalent ramp preview, or --target r,g,b) as their broad colour in place of
their own (mask-normalised UV low-pass, sigma 8 texels at 2K, smoothed across islands in 3D over SIGMA); the paint's
detail (texel / own low-pass) is kept. Weight 1 below Y_TOP - RAMP, easing
to 0 at Y_TOP; Y_TOP is lower at the face front (under the chin) than at the sides and back. Runs last in the head chains
(after face_paint / copy_tusks / hair_color). Reads <prefix>_head_basecolor_preneck.png (written on the first run, or
rewritten from the current file with RESET=1).
Usage (project folder): neck_even.py <export glb> <head prefix> (--preview <tier body preview png> | --target r,g,b)
       [--region-mask textures/a_region_mask.png] [--y-front 1.690] [--y-back 1.725] [--ramp 0.02] [--sigma 0.025]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
from headpos import texel_positions
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('head')
ap.add_argument('--y-front', type=float, default=1.690); ap.add_argument('--y-back', type=float, default=1.725)
ap.add_argument('--ramp', type=float, default=0.02); ap.add_argument('--sigma', type=float, default=0.025)
ap.add_argument('--preview', default=''); ap.add_argument('--region-mask', default='textures/a_region_mask.png'); ap.add_argument('--target', default='')
ap.add_argument('--skin', type=int, default=0); ap.add_argument('--head-mat', default='PeasantHOFHead')
o = ap.parse_args()
f = Path(f'textures/{o.head}_head_basecolor.png'); bk = f.with_name(f.stem + '_preneck.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
H = np.asarray(Image.open(bk).convert('RGB'), float); N = H.shape[0]
ph, part, _ = texel_parts(o.glb, o.head_mat, N)
P = np.nan_to_num(ph); skin = part == o.skin
x, y, z = P[..., 0], P[..., 1], P[..., 2]
front = np.clip((z + 0.02) / 0.04, 0, 1) * np.clip(1 - (np.abs(x) - 0.04) / 0.03, 0, 1)   # 1 at the face front, 0 at sides/back
ytop = o.y_front * front + o.y_back * (1 - front)
w = np.clip((ytop - y) / o.ramp, 0, 1); w = w * w * (3 - 2 * w); w = np.where(skin, w, 0.0)
src = skin & (w > 0.5)
# own island broad colour (mask-normalised UV low-pass inside the skin shell)
s2 = 8 * N / 2048
num = ndimage.gaussian_filter(H * skin[..., None], (s2, s2, 0)); den = ndimage.gaussian_filter(skin.astype(float), s2)
lp = num / np.maximum(den, 1e-3)[..., None]
# 3D broad colour across islands: Gaussian over the neck's own texels (subsampled)
si = np.nonzero(src); step = max(1, len(si[0]) // 60000)
SP = P[si][::step]; SC = lp[si][::step]; tree = cKDTree(SP)
if o.target:
    T = np.array([float(v) for v in o.target.split(',')])
else:
    Bp = np.asarray(Image.open(o.preview).convert('RGB'), float); nb = Bp.shape[0]
    Mk = np.asarray(Image.open(o.region_mask).convert('RGB').resize((nb, nb), Image.NEAREST), float)
    pb, cb = texel_positions(o.glb, 'PeasantHOF', nb); yb = np.nan_to_num(pb[..., 1]); zb = np.nan_to_num(pb[..., 2])
    sel = cb & (Mk[..., 2] > 128) & (yb > 1.56) & (yb < 1.64) & (zb > -0.06)
    T = np.median(Bp[sel], 0)
ti = np.nonzero(w > 0); out = H.copy(); k = 96
for s in range(0, len(ti[0]), 40000):
    r_, c_ = ti[0][s:s + 40000], ti[1][s:s + 40000]
    d, nn = tree.query(P[r_, c_], k)
    g = np.exp(-0.5 * (d / o.sigma) ** 2); g /= np.maximum(g.sum(1, keepdims=True), 1e-9)
    C3 = (SC[nn] * g[..., None]).sum(1)
    ratio = np.clip(T[None] / np.maximum(C3, 1), 0.6, 1.6) * np.clip(C3 / np.maximum(lp[r_, c_], 1), 0.6, 1.6)
    ww = w[r_, c_][:, None]
    out[r_, c_] = H[r_, c_] * (1 - ww + ww * ratio)
dev_b = np.abs(lp[src] - T).mean(-1)
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
num = ndimage.gaussian_filter(out * skin[..., None], (s2, s2, 0)); lp2 = num / np.maximum(den, 1e-3)[..., None]
dev_a = np.abs(lp2[src] - T).mean(-1)
print('NECKEVEN', o.head, 'target', T.round(0), 'texels', int((w > 0).sum()), 'broad-colour distance to the target: mean',
      round(float(dev_b.mean()), 1), '-> ', round(float(dev_a.mean()), 1), ' p95', round(float(np.percentile(dev_b, 95)), 1),
      '->', round(float(np.percentile(dev_a, 95)), 1))
