#!/usr/bin/env python3
"""Pad a baked AO map's gutters with the nearest chart texel (the bake leaves them black, and the grade multiplies AO into the colour, so
bilinear filtering drew dark lines along every UV seam: the line down the chin). Args: <uv npz> <material index> <in png> <out png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
D = np.load(sys.argv[1]); tri, uv, mat = D['tri'], D['uv'], D['mat']; M = int(sys.argv[2])
im = np.asarray(Image.open(sys.argv[3]).convert('L')); H, W = im.shape
cv = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(cv)
for t in tri[mat == M]: dr.polygon([(float(uv[v, 0] * W), float((1 - uv[v, 1]) * H)) for v in t], fill=255)
cov = ndimage.binary_erosion(np.asarray(cv) > 0, iterations=1) & (im > 0)
import os
nmp = 'work/needle_mask.png' if M == 0 else 'work/needle_mask_head.png'
if os.path.exists(nmp):          # fix_needles.py: texels the dropped needle faces baked over
    nm = np.asarray(Image.open(nmp).resize((W, H), Image.BILINEAR)) > 0; cov &= ~nm
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
Image.fromarray(im[idx[0], idx[1]]).save(sys.argv[4]); print('PADAO', sys.argv[4], int((~cov).sum()), 'gutter texels')
