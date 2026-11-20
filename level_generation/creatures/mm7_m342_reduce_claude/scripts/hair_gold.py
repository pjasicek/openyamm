#!/usr/bin/env python3
"""Hair faces of a ladder mesh (group 2) that sample the collar's gold-cream texels (MM8 Cleric: a collapse near the
collar dragged a hair face's UV onto the collar trim, a light fleck beside the cheek). Usage: hair_gold.py <mesh npz>"""
import sys
import numpy as np
from PIL import Image
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
d = np.load(sys.argv[1]); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2); g = d['group']
B = np.random.default_rng(1).dirichlet((1, 1, 1), 300)
u = np.einsum('sk,fkc->fsc', B, uv); x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int)
y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int); col = img[y, x]
gold = (col[..., 0] > 200) & (col[..., 1] > 170) & (col[..., 2] > 100)
bad = [(int(i), int(gold[i].sum()), np.round(v[f[i]].mean(0), 3).tolist()) for i in np.where(g == 2)[0] if gold[i].any()]
print('HAIRGOLD', len(bad), bad)
