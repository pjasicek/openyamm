#!/usr/bin/env python3
"""Feature alignment of a head view to its edit target (the mesh's own reference): axis-aligned affine (sx, sy, tx, ty)
maximising the normalised cross-correlation of blurred luminance gradients inside a face box, started from
align_masters.py's silhouette fit. Used where the silhouette fit leaves the eyes/mouth off (PeasantM7c front).
Args: <view png (clean)> <target png> <out png> <box x0,y0,x1,y1 in target px>"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage, optimize
src, ref, dst, box = sys.argv[1:5]
x0, y0, x1, y1 = [int(v) for v in box.split(',')]
B = np.asarray(Image.open(src).convert('RGBA')).astype(np.float32)
A = np.asarray(Image.open(ref).convert('RGB')).astype(np.float32)
lum = lambda im: im[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
def feat(l):
    g = ndimage.gaussian_filter(l, 3)
    return np.hypot(ndimage.sobel(g, 0), ndimage.sobel(g, 1))
fa = feat(lum(A))[y0:y1, x0:x1]; fa = (fa - fa.mean()) / fa.std()
lb = lum(B)
def warp(m, p, order=1):
    sx, sy, tx, ty = p
    return ndimage.affine_transform(m, [1 / sy, 1 / sx], offset=[-ty / sy, -tx / sx], order=order)
def ncc(p):
    fb = feat(warp(lb, p))[y0:y1, x0:x1]; fb = (fb - fb.mean()) / max(fb.std(), 1e-6)
    return float((fa * fb).mean())
p0 = np.array([1.0, 1.0, 0.0, 0.0])
best = None
for dy in range(-40, 41, 8):          # coarse search of the vertical shift first (the eyes were off by ~12 px)
    for s in (0.94, 0.97, 1.0, 1.03, 1.06):
        p = np.array([s, s, (1 - s) * 627, (1 - s) * 627 + dy]); v = ncc(p)
        if best is None or v > best[0]:
            best = (v, p)
r = optimize.minimize(lambda p: -ncc(p), best[1], method='Nelder-Mead',
                      options=dict(initial_simplex=[best[1] + d for d in ([0, 0, 0, 0], [0.02, 0, 0, 0], [0, 0.02, 0, 0], [0, 0, 6, 0], [0, 0, 0, 6])],
                                   xatol=1e-3, fatol=1e-5, maxiter=300))
p = r.x
out = np.stack([warp(B[..., c], p) for c in range(4)], -1)
Image.fromarray(np.uint8(np.clip(out, 0, 255).round())).save(dst)
print('ALIGN_FACE', json.dumps(dict(view=src.split('/')[-1], params=[round(float(x), 4) for x in p], ncc_before=round(ncc(p0), 3),
                                    ncc_after=round(-float(r.fun), 3))))
