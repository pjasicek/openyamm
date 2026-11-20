#!/usr/bin/env python3
"""Extra keep set for the m218 head skin (after the c87 close-ups): both ears (head-skin faces within M218_EAR_R,
default 0.035 m, of each ear's outermost point between 1.50 and 1.60 m) and the hairline (head-skin faces within
M218_LINE_R, default 0.012 m, of both a dark hair face and a light skin face by base-colour luminance; the 50 % cut
notched the temple hairline). Usage: head_keep.py <out.npy>"""
import os
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; uv = d['wuv'].reshape(-1, 3, 2); c = v[f].mean(1)
p = np.load('work/pieces.npy'); head = p == 1
img = np.asarray(Image.open('work/basecolor.png').convert('L'), np.float32); H, W = img.shape
cu = uv.mean(1); lum = img[np.clip(((1 - cu[:, 1] % 1) * H).astype(int), 0, H - 1), np.clip(((cu[:, 0] % 1) * W).astype(int), 0, W - 1)]
keep = np.zeros(len(f), bool)
hv = np.unique(f[head]); band = hv[(v[hv, 2] > 1.50) & (v[hv, 2] < 1.60)]
ears = []
for s in (-1, 1):
    b = band[np.sign(v[band, 0]) == s]; e = v[b[np.argmax(np.abs(v[b, 0]))]]; ears.append(e)
    keep |= head & (np.linalg.norm(c - e, axis=1) < float(os.environ.get('M218_EAR_R', '0.035')))
ear_n = int(keep.sum())
dark = head & (lum < 70); light = head & (lum > 120)
R = float(os.environ.get('M218_LINE_R', '0.012'))
near = lambda m: cKDTree(c[m]).query(c)[0] < R
line = head & near(dark) & near(light)
keep |= line
np.save(sys.argv[1], keep)
print('EARS', np.round(ears, 3).tolist(), 'ear faces', ear_n, 'hairline', int(line.sum()), 'dark', int(dark.sum()), 'light', int(light.sum()), 'total', int(keep.sum()))
