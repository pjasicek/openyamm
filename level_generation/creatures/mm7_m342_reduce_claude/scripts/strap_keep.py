#!/usr/bin/env python3
"""Painted shoulder straps (m342): the dress straps are painted green on the skin shell (piece 0), and the cut put
jagged triangles on their straight edges (close-ups of ladders c and d). Skin-shell faces whose base colour (tier A
atlas, work/basecolor.png) at any of 7 sample points is dress green, plus their edge neighbours on the skin shell,
are added to the exact keep set. Usage: strap_keep.py <keep in .npy> <keep out .npy>"""
import sys
import colorsys
import numpy as np
from PIL import Image
src, out = sys.argv[1:3]
d = np.load('work/mesh_in.npz'); f, uv = d['faces'], d['wuv'].reshape(-1, 3, 2)
fp = np.load('work/face_piece.npy'); keep = np.load(src)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3], [.5, .5, 0], [0, .5, .5], [.5, 0, .5]])
u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
c = img[y, x]
hsv = np.array([colorsys.rgb_to_hsv(*p) for p in c.reshape(-1, 3)]).reshape(c.shape)
green = ((hsv[..., 0] * 360 > 70) & (hsv[..., 0] * 360 < 175) & (hsv[..., 1] > 0.25) & (hsv[..., 2] > 0.1)).any(1)
strap = (fp == 0) & green
vs = set(f[strap].ravel().tolist())
grow = (fp == 0) & np.array([any(i in vs for i in t) for t in f])
new = keep | grow
np.save(out, new)
print('STRAPKEEP green skin faces', int(strap.sum()), 'with neighbours', int(grow.sum()), 'keep', int(keep.sum()), '->', int(new.sum()))
