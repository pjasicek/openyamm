#!/usr/bin/env python3
"""Island-aware border repaint for a texture set (2026-11-04, viewer r6/r7: dotted dark lines along the cheek's UV seams). compose_pf.py
pads Meshy's gutters from the 4K charts eroded by 2 px, so a chart's own border texels can take the nearest interior texel of a
NEIGHBOURING chart (the hidden old hood's dark hair 2-3 px away). Here every chart (faces connected through shared uv rows) of material MAT
re-paints its border band (its rasterised polygon minus its 1-px erosion) from its OWN interior (nearest texel). Gutters are left for
gutter_fill. Args: <material index> <in png> <out png> [npz]   (project folder)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
M = int(sys.argv[1]); SRC, DST = sys.argv[2:4]; NPZ = sys.argv[4] if len(sys.argv) > 4 else 'work/uv.npz'
D = np.load(NPZ); tri, uv, mat = D['tri'], D['uv'], D['mat']
im = np.asarray(Image.open(SRC).convert('RGB')).copy(); S = im.shape[0]
F = np.where(mat == M)[0]
if len(sys.argv) > 5: F = F[np.isin(D['comp'][tri[F, 0]], [[str(x) for x in D['names']].index(c) for c in sys.argv[5].split(',')])]      # only these parts' charts
t = tri[F]
n = len(uv); g = coo_matrix((np.ones(len(t) * 2), (np.r_[t[:, 0], t[:, 1]], np.r_[t[:, 1], t[:, 2]])), shape=(n, n))
_, lab = connected_components(g, directed=False); fl = lab[t[:, 0]]
out = im.copy(); fixed = 0
# pass 3: each chart first extends its own interior 3 px into the gutter (never into any chart's polygon): bilinear sampling at a chart's
# edge then reads its own colour, not a neighbouring chart's (dark hair lines along the neck's seams in the viewer, r40)
Fall = np.where(mat == M)[0]; U_ = Image.new('L', (S, S), 0); dU = ImageDraw.Draw(U_)
for f in Fall: dU.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in tri[f]], fill=255)
U_ = np.asarray(U_) > 0
for L in np.unique(fl):
    ft = t[fl == L]; q = uv[ft] * [S, -S] + [0, S]
    x0, y0 = np.maximum(np.floor(q.reshape(-1, 2).min(0)).astype(int) - 3, 0); x1, y1 = np.minimum(np.ceil(q.reshape(-1, 2).max(0)).astype(int) + 3, S - 1)
    cv = Image.new('L', (x1 - x0 + 1, y1 - y0 + 1), 0); dr = ImageDraw.Draw(cv)
    for p in q: dr.polygon([(float(a - x0), float(b - y0)) for a, b in p], fill=255)
    m = np.asarray(cv) > 0; inner = ni.binary_erosion(m, iterations=1)
    if inner.sum() < 4: continue
    band = m & ~inner
    ext = ni.binary_dilation(m, iterations=3) & ~U_[y0:y1 + 1, x0:x1 + 1]
    band = band | ext
    idx = ni.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    sub = im[y0:y1 + 1, x0:x1 + 1]; o = out[y0:y1 + 1, x0:x1 + 1]
    o[band] = sub[idx[0][band], idx[1][band]]; fixed += int(band.sum())
Image.fromarray(out).save(DST); print('ISLANDPAD charts', len(np.unique(fl)), 'border texels', fixed)
