#!/usr/bin/env python3
"""Tier B braids from tier A's plaited braid paint (pass 5): Meshy painted B's braids flat near-black (no plait). Every braid texel of B's
head map takes A's braid texel recoloured dark brown with A's luminance detail (MM9 F3b's hair 40/28/22 at A's median braid tone).
Args: <tier A head png> <tier B head png in> <out png>   (project folder; parts from work/uv.npz)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
D = np.load('work/uv.npz'); uv, tri, mat, comp = D['uv'], D['tri'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
A = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32) / 255; B = np.asarray(Image.open(sys.argv[2]).convert('RGB'), np.float32) / 255
S = A.shape[0]; m = Image.new('L', (S, S), 0); d = ImageDraw.Draw(m)
for f in np.where((mat == 1) & (comp[tri[:, 0]] == names.index('braids')))[0]:
    d.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in tri[f]], fill=255)
from scipy import ndimage as ni
m = ni.binary_dilation(np.asarray(m) > 0, iterations=2)
lum = A @ np.array([0.2126, 0.7152, 0.0722]); mid = float(np.median(lum[m]))
dark = np.array([40, 28, 22], np.float32) / 255 * np.clip(lum / mid, 0.35, 1.9)[..., None]
out = B.copy(); out[m] = np.clip(dark[m], 0, 1)
Image.fromarray((out * 255 + 0.5).astype('u1')).save(sys.argv[3]); print('BRAID_B texels', int(m.sum()))
