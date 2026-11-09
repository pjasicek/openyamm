#!/usr/bin/env python3
"""Green forearm skin texels (by rest position on the body upload: |x| 0.55..0.8 m, height 0.45..0.7 m, i.e. the
forearms in the near-T bind pose) from the graded body base colour -> work/skin_ref.npy, the hand grading reference
for compose_headhand.py --ref-texels (its reddish-skin test finds no texels on green skin).
Usage (project folder): skin_ref.py <upload glb> <basecolor png> <out npy>"""
import sys
import numpy as np
from PIL import Image
from pygltflib import GLTF2
sys.path.insert(0, 'scripts')
from headpos import texel_positions
glb, png, out = sys.argv[1:4]
mat = None   # the upload has no material: its one primitive
pos = texel_positions(glb, mat, 2048)[0]
img = np.asarray(Image.open(png).convert('RGB').resize((2048, 2048))).astype(np.float32)
x, h = np.abs(pos[..., 0]), pos[..., 1]
m = (x > 0.55) & (x < 0.8) & (h > 0.45) & (h < 0.7)
ref = img[m]
lum = ref @ np.array([0.299, 0.587, 0.114])
ref = ref[(lum > np.percentile(lum, 15)) & (lum < np.percentile(lum, 90))]
np.save(out, ref)
print('SKINREF', mat, 'texels', int(m.sum()), 'median', np.median(ref, 0).round(1), 'std', ref.std(0).round(1))
