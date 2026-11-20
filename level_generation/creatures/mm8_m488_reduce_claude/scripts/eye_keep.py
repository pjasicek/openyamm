#!/usr/bin/env python3
"""Eye zones of the MM8 Minotaur (the eyes are part of the head surface): head faces whose texture samples the
orange iris give each eye's centre; every face within REA_EYE_R (default 3.5 cm) of a centre is kept exactly.
Usage: eye_keep.py <keep in.npy> <keep out.npy>"""
import os, sys, colorsys, numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npy'); f, v, wuv = d['faces'], d['verts'], d['wuv']
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
c = v[f].mean(1); uv = wuv.reshape(len(f), 3, 2).mean(1)
px = img[np.clip(((1 - uv[:, 1]) * H).astype(int), 0, H - 1), np.clip((uv[:, 0] * W).astype(int), 0, W - 1)]
hsv = np.array([colorsys.rgb_to_hsv(*p) for p in px])
iris = (g == 1) & (hsv[:, 0] > .05) & (hsv[:, 0] < .13) & (hsv[:, 1] > .55) & (hsv[:, 2] > .45) & (c[:, 2] > 1.85) & (c[:, 2] < 1.98) & (c[:, 1] < -.12)  # horns and muzzle share the hue
R = float(os.environ.get('REA_EYE_R', '0.035')); keep = np.load(sys.argv[1]).copy(); zone = np.zeros(len(f), bool)
for side in (-1, 1):
    s = iris & (np.sign(c[:, 0]) == side)
    ctr = np.median(c[s], 0); zone |= np.linalg.norm(c - ctr, axis=1) < R
    print('EYE', side, int(s.sum()), 'iris faces, centre', ctr.round(3))
keep |= zone; np.save(sys.argv[2], keep); print('KEEP', int(zone.sum()), 'eye faces; total', int(keep.sum()))
