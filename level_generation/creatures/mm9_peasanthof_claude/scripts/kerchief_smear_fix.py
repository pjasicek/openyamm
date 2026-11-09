#!/usr/bin/env python3
"""HOF2: the pink smear where the kerchief edge meets the ear tip (coordinator pre-screen of r6, 2026-11-04). The head retexture painted
a band of ear skin onto the kerchief beside each ear. Kerchief texels (parts KERCHIEF of the head set) near the ears (|x| > X0,
Y0 < y < Y1, in the export frame shifted by --dy/--dz like paint_chain_c) that are pinker than the cloth (hue < HUE deg with saturation
> 0.2) or much darker than their neighbourhood (a speck) are refilled from the surrounding cloth (mask-normalised Gaussian, sigma 3).
Reads <prefix>_head_basecolor_presmear.png (first run or RESET=1). Args: <glb> <prefix> [--parts 1,4] [--x0 0.05] [--y0 1.66] [--y1 1.84]
[--hue 22] [--dy 0] [--dz 0]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('prefix')
ap.add_argument('--parts', default='1,4'); ap.add_argument('--x0', type=float, default=0.05); ap.add_argument('--y0', type=float, default=1.66)
ap.add_argument('--y1', type=float, default=1.84); ap.add_argument('--hue', type=float, default=22); ap.add_argument('--dy', type=float, default=0)
ap.add_argument('--dz', type=float, default=0)
o = ap.parse_args()
f = Path(f'textures/{o.prefix}_head_basecolor.png'); bk = f.with_name(f.stem + '_presmear.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
H = np.asarray(Image.open(bk).convert('RGB'), float); N = H.shape[0]
ph, part, _ = texel_parts(o.glb, 'PeasantHOFHead', N); P = np.nan_to_num(ph); P[..., 1] -= o.dy; P[..., 2] -= o.dz
k = np.isin(part, [int(x) for x in o.parts.split(',')])
r, g, b = H[..., 0], H[..., 1], H[..., 2]; mx, mn = H.max(-1), H.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
L = H.mean(-1); med = ndimage.median_filter(L, 7)
zone = k & (np.abs(P[..., 0]) > o.x0) & (P[..., 1] > o.y0) & (P[..., 1] < o.y1)
bad = zone & (((hue < o.hue) | (hue > 340)) & (sat > 0.2) | (L < 0.6 * med))
bad = ndimage.binary_dilation(bad, iterations=1) & k
ok = k & ~ndimage.binary_dilation(bad, iterations=1)
num = ndimage.gaussian_filter(H * ok[..., None], (3, 3, 0)); den = ndimage.gaussian_filter(ok.astype(float), 3)
fill = num / np.maximum(den, 1e-3)[..., None]
out = H.copy(); out[bad] = fill[bad]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
print('SMEARFIX', o.prefix, 'kerchief zone texels', int(zone.sum()), 'refilled', int(bad.sum()))
