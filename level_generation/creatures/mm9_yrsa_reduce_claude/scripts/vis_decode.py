#!/usr/bin/env python3
"""Decode work/vis/*.png (face-ID renders) -> work/vis.npz: per face, the number of frontal views (|yaw| <= 110) where it shows
with >= MINPX pixels, and the max pixels seen."""
import re, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
NF = 3375 + 5301; MINPX = 2
cnt = np.zeros(NF, int); mx = np.zeros(NF, int)
for f in sorted((HERE / 'work' / 'vis').glob('*.png')):
    a = np.asarray(Image.open(f).convert('RGB')).astype(int)
    ids = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    ids = ids[(ids > 0) & (ids <= NF)] - 1
    u, c = np.unique(ids, return_counts=True)
    ok = c >= MINPX; cnt[u[ok]] += 1; mx[u] = np.maximum(mx[u], c)
np.savez(HERE / 'work' / 'vis.npz', cnt=cnt, mx=mx)
print('visible faces', int((cnt > 0).sum()), 'of', NF, 'head set visible', int((cnt[3375:] > 0).sum()), 'of 5301')
