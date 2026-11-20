#!/usr/bin/env python3
"""Skin on the neck below the jaw in the BODY paint (r6: the head/body seam moved up to under the jaw, so the body paint
now shows on the neck; DF2's and DF4's body retextures painted their collar / kerchief edge there as a dark band).
Body texels on the neck tube (export frame: y Y0..0.93, within 0.075 m of the neck joint's vertical axis x 0, z -0.02) that
are not skin-like take the mean colour of the 12 nearest skin-like texels of the tube (3D) times a damped luminance detail.
The necklace (light grey/silver, low saturation) lies below Y0 on every design. Runs after paint_clean.py, before
seam_tone.py. Usage (project folder): neck_fill.py <export glb> <prefix> [--y0 0.885]"""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('prefix'); ap.add_argument('--y0', type=float, default=0.885); ap.add_argument('--r', type=float, default=0.075)
o = ap.parse_args()
f = Path(f'textures/{o.prefix}_basecolor_graded.png')
B = np.asarray(Image.open(f).convert('RGB'), float)
pos, cov = texel_positions(o.glb, 'PeasantDF', B.shape[0]); P = np.nan_to_num(pos)
mx, mn = B.max(-1), B.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
hue = np.degrees(np.arctan2(np.sqrt(3) * (B[..., 1] - B[..., 2]), 2 * B[..., 0] - B[..., 1] - B[..., 2])) % 360
skin = (hue > 8) & (hue < 40) & (sat > 0.18) & (sat < 0.62) & (mx > 140)
ax = np.array([0.0, -0.02])     # the neck joint in the export frame (x, z); the texel band there is too sparse to measure
r = np.hypot(P[..., 0] - ax[0], P[..., 2] - ax[1])
tube = cov & (P[..., 1] > o.y0) & (P[..., 1] < 0.93) & (r < o.r)
bad = tube & ~skin; good = tube & skin
gi = np.nonzero(good); bi = np.nonzero(bad)
if len(gi[0]) > 12 and len(bi[0]):
    tree = cKDTree(P[gi]); _, nn = tree.query(P[bi], 12)
    col = B[gi][nn].mean(1)
    lum = B[bi].mean(-1, keepdims=True); lc = col.mean(-1, keepdims=True)
    B2 = B.copy(); B2[bi] = col * np.clip(lum / np.maximum(lc, 1), 0.85, 1.15) ** 0.3
    Image.fromarray(np.uint8(np.clip(np.round(B2), 0, 255))).save(f)
print('NECKFILL', o.prefix, 'tube', int(tube.sum()), 'filled', int(bad.sum()), 'axis', ax.round(3))
