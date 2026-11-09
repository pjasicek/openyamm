#!/usr/bin/env python3
"""Map a side master onto the fitted fish: a 2D similarity (scale, offset; no rotation) between the master's alpha
silhouette and the Meshy fit's side silhouette (fins included), maximising IoU.
Usage: align_side.py <meshy_fit npz> <master png> <side: left|right> <out json>
World: left view looks from +X (image right = +Y), right view from -X (image right = -Y); image up = +Z."""
import sys, json
import numpy as np
from PIL import Image, ImageDraw

npz, png, side, out = sys.argv[1:5]
d = np.load(npz)
V, T = d['meshy_fit_v'], d['meshy_fit_t']
RES = 0.0005
sgn = 1 if side == 'left' else -1
u = sgn * V[:, 1]
w = V[:, 2]
u0, w1 = u.min() - 0.01, w.max() + 0.01
W, H = int((u.max() + 0.01 - u0) / RES), int((w1 - w.min() + 0.01) / RES)
sil = Image.new('L', (W, H), 0)
dr = ImageDraw.Draw(sil)
px = np.stack([(u - u0) / RES, (w1 - w) / RES], 1)
for t in T:
    dr.polygon([tuple(px[i]) for i in t], fill=255)
S = np.asarray(sil) > 0
m = Image.open(png).convert('RGBA')
A = np.asarray(m)[..., 3] > 128
ys, xs = np.nonzero(A)
sy, sx = np.nonzero(S)
# initial: bounding boxes (x extent sets the scale)
k0 = (xs.max() - xs.min()) / (sx.max() - sx.min())
best = None
for k in k0 * np.linspace(0.94, 1.06, 25):
    for dx in np.arange(-12, 13, 2):
        for dy in np.arange(-12, 13, 2):
            ox = xs.min() - k * sx.min() + dx
            oy = (ys.min() + ys.max()) / 2 - k * (sy.min() + sy.max()) / 2 + dy
            # sample master alpha at silhouette-grid positions
            gx = (np.arange(W) * k + ox).astype(int)
            gy = (np.arange(H) * k + oy).astype(int)
            ok_x = (gx >= 0) & (gx < A.shape[1]); ok_y = (gy >= 0) & (gy < A.shape[0])
            Ms = np.zeros((H, W), bool)
            Ms[np.ix_(ok_y, ok_x)] = A[np.ix_(gy[ok_y], gx[ok_x])]
            iou = (Ms & S).sum() / max((Ms | S).sum(), 1)
            if best is None or iou > best[0]:
                best = (iou, k, ox, oy)
iou, k, ox, oy = best
# image pixel (x, y) -> world: u = u0 + (x - ox) / k * RES, z = w1 - (y - oy) / k * RES; y_world = sgn * u
rep = {'side': side, 'iou': round(float(iou), 4), 'px_per_m': float(k / RES), 'u0': float(u0), 'w1': float(w1),
       'ox': float(ox), 'oy': float(oy), 'k': float(k), 'res': RES, 'sgn': sgn,
       'note': 'world_y = sgn*(u0 + (x-ox)/k*res), world_z = w1 - (y-oy)/k*res'}
json.dump(rep, open(out, 'w'), indent=1)
print('ALIGN', json.dumps(rep))
