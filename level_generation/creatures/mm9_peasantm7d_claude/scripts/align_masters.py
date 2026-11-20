#!/usr/bin/env python3
"""Codex's HOM2 masters drift from the HOM1 masters they were edited from (the mesh we paint is HOM1's): fit an axis-aligned
affine (sx, sy, tx, ty) per view that maximises the silhouette IoU with the HOM1 clean master (Nelder-Mead on a 1/4 scale
mask, the horns' rows excluded), warp the halo-free image with it, and report the IoU before/after.
Args: <hom2 view png (clean)> <hom1 clean view png> <out png> [skip_top_fraction]"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage, optimize
src, ref, dst = sys.argv[1:4]
skip = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
B = Image.open(src).convert('RGBA'); A = np.asarray(Image.open(ref).convert('RGBA'))[..., 3] > 128
H, W = A.shape
k = 4
a = A[::k, ::k].astype(np.float32); b = (np.asarray(B)[..., 3] > 128)[::k, ::k].astype(np.float32)
rows = np.where(A.any(1))[0]; y0 = int((rows[0] + skip * (rows[-1] - rows[0])) / k)
def warp(m, p):
    sx, sy, tx, ty = p
    # output pixel (y, x) samples input at ((y - ty) / sy, (x - tx) / sx)
    return ndimage.affine_transform(m, [1 / sy, 1 / sx], offset=[-ty / k / sy, -tx / k / sx], order=1)
def iou(p):
    w = warp(b, p)[y0:] > 0.5; r = a[y0:] > 0.5
    return (w & r).sum() / max((w | r).sum(), 1)
p0 = np.array([1.0, 1.0, 0.0, 0.0])
before = iou(p0)
best = optimize.minimize(lambda p: -iou(p), p0, method='Nelder-Mead',
                         options=dict(initial_simplex=[p0, p0 + [0.04, 0, 0, 0], p0 + [0, 0.04, 0, 0], p0 + [0, 0, 20, 0], p0 + [0, 0, 0, 20]],
                                      xatol=1e-3, fatol=1e-4, maxiter=400))
p = best.x
im = np.asarray(B).astype(np.float32)
out = np.stack([ndimage.affine_transform(im[..., c], [1 / p[1], 1 / p[0]], offset=[-p[3] / p[1], -p[2] / p[0]], order=1)
                for c in range(4)], -1)
Image.fromarray(np.uint8(np.clip(out, 0, 255).round())).save(dst)
print('ALIGN', json.dumps(dict(view=src.split('/')[-1], params=[round(float(x), 4) for x in p], iou_before=round(float(before), 3),
                               iou_after=round(float(iou(p)), 3))))
