#!/usr/bin/env python3
"""Neck colour probe (finishing round 2026-11-04): median colour and pale-texel share of the body set below the cut and the head
set above it, per 45-degree sector round the neck (0 = front). Args: <glb> <body prefix> <head prefix> [cut 1.632] [band 0.05]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
from headpart import texel_parts
glb, bp, hp = sys.argv[1:4]; cut = float(sys.argv[4]) if len(sys.argv) > 4 else 1.632; band = float(sys.argv[5]) if len(sys.argv) > 5 else 0.05
B = np.asarray(Image.open(f'textures/{bp}_basecolor_graded.png').convert('RGB'), float)
H = np.asarray(Image.open(f'textures/{hp}_head_basecolor.png').convert('RGB'), float)
pb, cb = texel_positions(glb, 'PeasantHOF', B.shape[0]); ph, parth, _ = texel_parts(glb, 'PeasantHOFHead', H.shape[0])
def sat(I): mx, mn = I.max(-1), I.min(-1); return (mx - mn) / np.maximum(mx, 1)
for name, I, P, cov, lo, hi in (('body', B, pb, cb, cut - band, cut), ('head', H, ph, parth == 0, cut, cut + band)):
    y = np.nan_to_num(P[..., 1]); x = np.nan_to_num(P[..., 0]); z = np.nan_to_num(P[..., 2])
    m = cov & (y >= lo) & (y < hi) & (np.hypot(x, z - np.median(z[cov & (y >= lo) & (y < hi)])) < 0.09)
    ang = (np.degrees(np.arctan2(x, z - np.median(z[m]))) + 360 + 22.5) % 360 // 45
    for s in range(8):
        mm = m & (ang == s)
        if mm.sum() < 20: continue
        S = sat(I[mm]); L = I[mm].mean(-1)
        print(f'{name} sector {s*45:3d}: texels {mm.sum():6d} median {np.median(I[mm],0).round(0)} pale(sat<0.2) {np.mean(S<0.2)*100:4.1f}% light(L>200) {np.mean(L>200)*100:4.1f}%')
