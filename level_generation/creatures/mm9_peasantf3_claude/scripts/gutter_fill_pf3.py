#!/usr/bin/env python3
"""Head texture gutters (pass 5, viewer close-up): the fresh Meshy head paint left its own colours between the UV islands (veil cream,
skin, eye greys), and vertices on an island's edge sample them through the bilinear filter and the mip levels: a white glint along the lip
midline and white slivers at the eye corners. Every texel no head-material triangle covers takes the colour of the nearest covered texel.
Args: <npz> <png> [<png> ...]   (each image rewritten in place; project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
D = np.load(sys.argv[1]); tri, uv, mat = D['tri'], D['uv'], D['mat']
hi = [str(x) for x in D['matnames']].index('PeasantF3Head')
for path in sys.argv[2:]:
    im = Image.open(path); mode = im.mode; a = np.asarray(im.convert('RGB')).copy(); S = a.shape[0]
    cov = np.zeros((S, S), bool)
    for f in np.where(mat == hi)[0]:
        q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int) - 1; x1, y1 = np.ceil(q.max(0)).astype(int) + 1
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
        pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
        M = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
        if abs(np.linalg.det(M)) < 1e-12:      # degenerate in UV (single-texel caps): the texels under its corners
            for p in q: cov[int(np.clip(p[1], 0, S - 1)), int(np.clip(p[0], 0, S - 1))] = True
            continue
        l = np.linalg.solve(M, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]
        # a texel counts when the triangle reaches within half a texel of its centre
        e = np.linalg.norm(q[[1, 2, 0]] - q[[0, 1, 2]], axis=1); h = 2 * abs(np.linalg.det(M)) / 2 / np.maximum(e[[1, 2, 0]], 1e-9)
        ok = (l3 > -0.7 / np.maximum(h, 1e-9)).all(1)
        cov[pts[ok, 1].astype(int), pts[ok, 0].astype(int)] = True
    _, (iy, ix) = ni.distance_transform_edt(~cov, return_indices=True)
    out = a[iy, ix]
    Image.fromarray(out).convert(mode).save(path)
    print('GUTTER', path, 'covered %.1f %%' % (100 * cov.mean()), 'filled', int((~cov).sum()))
