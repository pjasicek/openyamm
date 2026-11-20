#!/usr/bin/env python3
"""Hands to the face's skin (HOM1's hand_clean.py idea): the head set's hand texels (rest positions |x| > 0.5 m) take one
cheek colour (median of the front cheek band, as face_paint_phof.py) times their own luminance detail ^ DETAIL. Tier C's
compose took its hand reference from the blonde fringe and painted the hands yellow. Usage (project folder):
hand_tone.py <export glb> <head prefix> [--dy 0] [--dz 0] [--detail 0.8]"""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('head')
ap.add_argument('--dy', type=float, default=0.0); ap.add_argument('--dz', type=float, default=0.0)
ap.add_argument('--detail', type=float, default=0.8)
o = ap.parse_args()
f = Path(f'textures/{o.head}_head_basecolor.png')
H = np.asarray(Image.open(f).convert('RGB'), float)
pos, part, _ = texel_parts(o.glb, 'PeasantHOFHead', H.shape[0]); P = np.nan_to_num(pos); P[..., 1] -= o.dy; P[..., 2] -= o.dz
mx, mn = H.max(-1), H.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
cheek = (part == 0) & (P[..., 2] > -0.03) & (P[..., 1] > 1.74) & (P[..., 1] < 1.775) & (np.abs(P[..., 0] + 0.009) > 0.03) & \
    (np.abs(P[..., 0] + 0.009) < 0.06) & (sat > 0.15) & (sat < 0.65)
C = np.median(H[cheek], 0)
hand = (part >= 0) & (np.abs(P[..., 0]) > 0.5)
lum = H.mean(-1); r = np.clip(lum / max(np.median(lum[hand]), 1), 0.5, 1.4) ** o.detail
H[hand] = C[None] * r[hand][:, None]
Image.fromarray(np.uint8(np.clip(np.round(H), 0, 255))).save(f)
print('HANDTONE', o.head, 'cheek', C.round(1).tolist(), 'hand texels', int(hand.sum()))
