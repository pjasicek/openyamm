#!/usr/bin/env python3
"""Fre pass 2 (dark/red specks at the chin point and under the lower lip): uv_sliver_fix_pf3.py puts each collapsed head sliver on one
texel (a corner's); a corner on a chart's edge rounds to a gutter texel, and the sliver - a fraction of a millimetre - draws it as a speck
(the chin V sampled gutter texels 129/64/33). Every texel a sliver row samples takes the median of the texels within 6 px that lie INSIDE
the head set's charts (rasterised faces of real area). Also (r31: some corners lay deep in the gutter): every sliver row is moved onto the nearest texel inside a chart (npz rewritten in place).
Args: <uv npz with sliver rows> <head png in> <png out>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
D = np.load(sys.argv[1]); tri, uv, mat = D['tri'], D['uv'], D['mat']
im = np.asarray(Image.open(sys.argv[2]).convert('RGB')).copy(); S = im.shape[0]
H = np.where(mat == 1)[0]; T = uv[tri[H]] * S
area = np.abs((T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 2, 0] - T[:, 0, 0]) * (T[:, 1, 1] - T[:, 0, 1]))
sl = H[area < 1e-6]
cv = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cv)
for f in H[area >= 1e-6]: dr.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in tri[f]], fill=255)
from scipy import ndimage as ni
inside = ni.binary_erosion(np.asarray(cv) > 0, iterations=1)
pts = {(int(np.clip(uv[r, 0] * S, 0, S - 1)), int(np.clip((1 - uv[r, 1]) * S, 0, S - 1))) for f in sl for r in tri[f]}
src = im.copy(); R = 6; done = 0
for x, y in pts:
    y0, y1, x0, x1 = max(y - R, 0), min(y + R + 1, S), max(x - R, 0), min(x + R + 1, S)
    m = inside[y0:y1, x0:x1]
    if m.any(): im[y, x] = np.median(src[y0:y1, x0:x1][m], 0); done += 1
import os
if not os.environ.get('NOMOVE'):
  idx = ni.distance_transform_edt(~inside, return_distances=False, return_indices=True)
  DD = dict(D); uvn = DD['uv'].copy(); rows = np.unique(tri[sl])
  xs = np.clip((uvn[rows, 0] * S).astype(int), 0, S - 1); ys = np.clip(((1 - uvn[rows, 1]) * S).astype(int), 0, S - 1)
  uvn[rows, 0] = (idx[1][ys, xs] + 0.5) / S; uvn[rows, 1] = 1 - (idx[0][ys, xs] + 0.5) / S; DD['uv'] = uvn; np.savez(sys.argv[1], **DD)
Image.fromarray(im).save(sys.argv[3]); print('SLIVERTEXELS', len(sl), 'faces', len(pts), 'texels', done, 'healed')
