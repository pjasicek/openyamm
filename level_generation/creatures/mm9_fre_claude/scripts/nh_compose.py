#!/usr/bin/env python3
"""Pass 7: one head-set map from Meshy's 4K paint: gutters (texels outside every chart of work/nh/head_uv.npz) take the nearest chart texel at
4K, then ONE Lanczos downsample to SIZE. Nothing inside a chart is repainted: compose_islands_fre.py's border-band repaint cut the brow
ends and the lids into blocks along the face's chart seams (r74 close-ups, review/newhead/eyes_flat.png). Args: <meshy png> <out png> <size>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
Image.MAX_IMAGE_PIXELS = None
SRC, DST, SIZE = sys.argv[1], sys.argv[2], int(sys.argv[3])
D = np.load('work/nh/head_uv.npz'); uv, tri = D['uv'], D['tri']
src = Image.open(SRC); mode = 'L' if src.mode in ('L', 'I', 'I;16') else 'RGB'
im = np.asarray(src.convert(mode))
if im.shape[0] != 4096: im = np.asarray(Image.fromarray(im).resize((4096, 4096), Image.LANCZOS))
S = 4096; cv = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cv)
for t in tri: dr.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in t], fill=255)
cov = np.asarray(cv) > 0
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
out = im[idx[0], idx[1]]
Image.fromarray(out).resize((SIZE, SIZE), Image.LANCZOS).save(DST); print('NHCOMPOSE', DST, 'gutter texels', int((~cov).sum()))
