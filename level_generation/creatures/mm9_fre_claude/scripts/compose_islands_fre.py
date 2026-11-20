#!/usr/bin/env python3
"""Head-set maps from Meshy's 4K paint with ISLAND-AWARE padding (2026-11-04, viewer r6-r8: a dotted dark line along a UV seam across the
cheek). compose_pf.py pads Meshy's gutters from the charts eroded by 2 px and downsamples with Lanczos, so a chart's border texels mix in a
NEIGHBOURING chart's colours (the hidden old hood's dark hair a few texels away in the atlas). Here, at 4K, every chart (faces connected
through shared uv rows) first extends its own interior colours 6 px out (gutters), then re-paints its own polygon's 3-px border band from
its own interior; the result is box-downsampled (each output texel averages only its 4x4 block, never across the gap) to SIZE.
Args: <meshy png> <out png> <size> [material index (1)]   (project folder; work/uv.npz)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
Image.MAX_IMAGE_PIXELS = None
SRC, DST, SIZE = sys.argv[1], sys.argv[2], int(sys.argv[3]); M = int(sys.argv[4]) if len(sys.argv) > 4 else 1
D = np.load(__import__('os').environ.get('UVNPZ', 'work/uv.npz')); tri, uv, mat = D['tri'], D['uv'], D['mat']
src = Image.open(SRC); mode = 'L' if src.mode in ('L', 'I', 'I;16') else 'RGB'
im = np.asarray(src.convert(mode)); S = im.shape[0]
if S != 4096: im = np.asarray(Image.fromarray(im).resize((4096, 4096), Image.LANCZOS)); S = 4096
F = np.where(mat == M)[0]; t = tri[F]; n = len(uv)
g = coo_matrix((np.ones(len(t) * 2), (np.r_[t[:, 0], t[:, 1]], np.r_[t[:, 1], t[:, 2]])), shape=(n, n))
_, lab = connected_components(g, directed=False); fl = lab[t[:, 0]]
out = im.copy(); charts = []
for L in np.unique(fl):
    q = uv[t[fl == L]] * [S, -S] + [0, S]
    x0, y0 = np.maximum(np.floor(q.reshape(-1, 2).min(0)).astype(int) - 8, 0); x1, y1 = np.minimum(np.ceil(q.reshape(-1, 2).max(0)).astype(int) + 8, S - 1)
    cv = Image.new('L', (x1 - x0 + 1, y1 - y0 + 1), 0); dr = ImageDraw.Draw(cv)
    for p in q: dr.polygon([(float(a - x0), float(b - y0)) for a, b in p], fill=255)
    m = np.asarray(cv) > 0; inner = ni.binary_erosion(m, iterations=int(__import__("os").environ.get("ISL_BAND", "6")))
    if inner.sum() < 4: inner = ni.binary_erosion(m, iterations=1)
    if inner.sum() < 1: inner = m
    idx = ni.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    charts.append((x0, y0, x1, y1, m, inner, idx))
U_ = np.zeros((S, S), bool)
for x0, y0, x1, y1, m, inner, idx in charts: U_[y0:y1 + 1, x0:x1 + 1] |= m
for x0, y0, x1, y1, m, inner, idx in charts:          # pass 1: gutters (6 px round each chart, never into any chart's polygon)
    ext = ni.binary_dilation(m, iterations=6) & ~U_[y0:y1 + 1, x0:x1 + 1]; sub = im[y0:y1 + 1, x0:x1 + 1]; o = out[y0:y1 + 1, x0:x1 + 1]
    o[ext] = sub[idx[0][ext], idx[1][ext]]
for x0, y0, x1, y1, m, inner, idx in charts:          # pass 2: each chart's own polygon from its own interior
    band = m & ~inner; sub = im[y0:y1 + 1, x0:x1 + 1]; o = out[y0:y1 + 1, x0:x1 + 1]
    o[band] = sub[idx[0][band], idx[1][band]]
Image.fromarray(out).resize((SIZE, SIZE), Image.BOX).save(DST); print('COMPOSEISL', DST, 'charts', len(charts))
