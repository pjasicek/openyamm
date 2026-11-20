#!/usr/bin/env python3
"""Remove straight painted lines across the face (mm9_greenman r2): Meshy's head retexture drew hair-thin straight dark
lines across the face chart (left temple -> chin, and from the left eye's inner corner toward the nose); viewer close-ups
showed them as cracks across the cheek. Per segment (rough end points in texture px of the 2K head set, scripts/
face_lines_gm.json): in a corridor of +-CORR px the darkest point of the high-pass luminance (lum - blur 3 px) is found
per step and a straight line (or a quadratic, `curve`) is fitted to those points robustly (two passes, outliers > 1.2 px
dropped); then every texel within HALF px of the fitted line takes the median of the texels 3-5 px either side of it
across the line. Usage (project folder): face_lines.py <head basecolor png>   (edits in place; rerun from the composed copy)"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage
p = sys.argv[1]
img = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
lum = img @ np.array([0.299, 0.587, 0.114]); hp = lum - ndimage.gaussian_filter(lum, 3.0)
cfg = json.load(open('scripts/face_lines_gm.json'))
out = img.copy(); rep = []
def samp(a, x, y):
    return ndimage.map_coordinates(a, [[y], [x]], order=1)[0]
for seg in cfg['segments']:
    p0, p1 = np.array(seg['p0'], float), np.array(seg['p1'], float)
    CORR, HALF = seg.get('corr', 8.0), seg.get('half', 1.5)
    d = p1 - p0; L = np.linalg.norm(d); d /= L; n = np.array([-d[1], d[0]])
    ts = np.arange(0, L, 0.5); cand = np.arange(-CORR, CORR + 0.01, 0.25)
    pts = []
    for t in ts:
        c = p0 + d * t
        xy = c[None] + n[None] * cand[:, None]
        v = ndimage.map_coordinates(hp, [xy[:, 1], xy[:, 0]], order=1)
        pts.append((t, cand[int(np.argmin(v))], v.min()))
    pts = np.array(pts)
    deg = 2 if seg.get('curve') else 1
    keep = pts[:, 2] < np.percentile(pts[:, 2], 70)
    for _ in range(2):
        cf = np.polyfit(pts[keep, 0], pts[keep, 1], deg)
        res = np.abs(np.polyval(cf, pts[:, 0]) - pts[:, 1]); keep = keep & (res < 1.2)
    off = np.polyval(cf, ts)
    H, W = lum.shape; writes = 0
    for t, o in zip(ts, off):
        c = p0 + d * t + n * o
        side = np.concatenate([c[None] + n[None] * s for s in (-5, -4, -3, 3, 4, 5)])
        cols = np.stack([ndimage.map_coordinates(img[..., k], [side[:, 1], side[:, 0]], order=1) for k in range(3)], 1)
        med = np.median(cols, 0)
        for s in np.arange(-HALF, HALF + 0.01, 0.5):
            q = c + n * s; xi, yi = int(round(q[0])), int(round(q[1]))
            if 0 <= xi < W and 0 <= yi < H:
                out[yi, xi] = med; writes += 1
    rep.append({'kept_points': int(keep.sum()), 'of': len(pts), 'writes': writes, 'fit': np.round(cf, 4).tolist()})
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(p)
print('FACELINES', rep)
