#!/usr/bin/env python3
"""Rotate each arm of a front/back master about its shoulder so the arm angle matches PeasantF5's master (the mesh being painted). Arms are
the alpha pixels beyond TORSO px from the figure's centre line above row 650; the angle is a least-squares line fit of those pixels (degrees
below horizontal); pixels beyond the shoulder (x offset PIV) take the source rotated by the difference, blended over a 40 px band.
Args: <in png> <reference png> <out png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
src, ref, dst = sys.argv[1:4]; TORSO, PIV = 170, 175
def fit(a, cx, sg):
    H, W = a.shape; yy, xx = np.mgrid[0:H, 0:W]; sel = a & ((xx - cx) * sg > TORSO) & (yy < 540)
    y, x = np.nonzero(sel); k, b = np.linalg.lstsq(np.c_[x, np.ones_like(x)], y, rcond=None)[0]
    return np.degrees(np.arctan(k * sg)), k, b
S = np.asarray(Image.open(src).convert('RGBA'), np.float32); R = np.asarray(Image.open(ref).convert('RGBA'))[..., 3] > 128
a = S[..., 3] > 128; H, W = a.shape; cx = float(np.median(np.nonzero(a)[1]))
out = S.copy(); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
for sg in (-1, 1):
    ang, k, b = fit(a, cx, sg); angr, _, _ = fit(R, cx, sg); d = np.radians(ang - angr)       # positive: ours steeper -> rotate up
    px = cx + sg * PIV; py = k * px + b
    th = d * sg                                   # image y down: rotate the arm toward the horizontal
    c, s = np.cos(th), np.sin(th)
    dx, dy = xx - px, yy - py
    sx = px + c * dx - s * dy; sy = py + s * dx + c * dy
    rot = np.stack([ndimage.map_coordinates(S[..., ch], [sy, sx], order=1, mode='constant', cval=0) for ch in range(4)], -1)
    w = np.clip(((xx - px) * sg) / 40.0, 0, 1)[..., None] * np.clip((560 - yy) / 30.0, 0, 1)[..., None]
    out = out * (1 - w) + rot * w
    print('ARM', 'L' if sg < 0 else 'R', 'ours', round(ang, 1), 'ref', round(angr, 1), 'rotated', round(np.degrees(d), 1), 'pivot', round(px), round(py))
Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(dst)
