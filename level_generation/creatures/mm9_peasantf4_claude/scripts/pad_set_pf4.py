#!/usr/bin/env python3
"""Re-pad a texture set's gutters after the paint steps (the face projection and the later fixes write island texels only, so the gutters kept
earlier colours and bilinear filtering drew thin pale lines along the UV seams of the neck). Every texel outside the rasterised charts of
material MAT takes its nearest chart texel. Args: <material index> <in png> <out png> (project folder; work/uv.npz)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
M = int(sys.argv[1]); im = np.asarray(Image.open(sys.argv[2]).convert('RGB')); S = im.shape[0]
D = np.load('work/uv.npz'); tri, uv, mat = D['tri'], D['uv'], D['mat']
cv = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cv)
for t in tri[mat == M]: dr.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in t], fill=255)
cov = ni.binary_erosion(np.asarray(cv) > 0, iterations=1)
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
Image.fromarray(im[idx[0], idx[1]]).save(sys.argv[3]); print('PADSET', sys.argv[3], int((~cov).sum()), 'gutter texels')
