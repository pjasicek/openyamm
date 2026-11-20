#!/usr/bin/env python3
"""Per-face label renders of the rest mesh (work/mesh_in.npz) without Blender: orthographic z-buffered rasterizer,
flat shading by the face normal, one colour per label (0 grey). Usage: label_view.py <labels .npy (int or bool per face, or (faces, 3) RGB)>
<out.png> [zmin,zmax (crop, metres)] [views, default front,left,back,right]"""
import os
import sys
import numpy as np
from PIL import Image

lab = np.load(sys.argv[1]); out = sys.argv[2]
RGB = lab.ndim == 2  # (faces, 3) colours 0-255 instead of labels (sampled base colour)
if RGB:
    cols = lab.astype(float); lab = np.ones(len(lab), int)
else:
    lab = lab.astype(int)
d = np.load(os.environ.get('REA_VIEW_NPZ', 'work/mesh_in.npz')); v, f = d['verts'], d['faces']
zr = [float(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 and sys.argv[3] != '-' else [v[:, 2].min(), v[:, 2].max()]
views = sys.argv[4].split(',') if len(sys.argv) > 4 else ['front', 'left', 'back', 'right']
PAL = np.array([[150, 150, 150], [230, 80, 70], [70, 170, 230], [240, 200, 60], [120, 210, 110], [200, 110, 220],
                [250, 140, 40], [60, 220, 200], [240, 120, 170], [140, 120, 250], [180, 230, 90], [250, 250, 250],
                [90, 90, 200], [200, 60, 60]], float)
S = 520


def render(view):
    # camera axes: right (image x), up (image y), towards the camera (depth)
    ax = {'front': ([1, 0, 0], [0, -1, 0]), 'back': ([-1, 0, 0], [0, 1, 0]), 'left': ([0, -1, 0], [-1, 0, 0]),
          'right': ([0, 1, 0], [1, 0, 0])}[view]
    r, t = np.array(ax[0], float), np.array(ax[1], float); up = np.array([0, 0, 1.])
    sel = (v[f][:, :, 2].max(1) >= zr[0]) & (v[f][:, :, 2].min(1) <= zr[1])
    if os.environ.get('REA_ONLY') == '1':  # labelled faces only (see what other parts cover)
        sel &= lab > 0
    tri = v[f[sel]]; L = lab[sel]; C = cols[sel] if RGB else PAL[L % len(PAL)]
    x = tri @ r; y = tri @ up; z = tri @ t
    lo = np.array([x.min(), y.min()]); span = max(x.max() - x.min(), y.max() - y.min()) * 1.05
    px = (x - lo[0]) / span * S + (S - (x.max() - lo[0]) / span * S) / 2; py = S - (y - lo[1]) / span * S
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    shade = 0.35 + 0.65 * np.abs(n @ (t * .8 + up * .4 + r * .2) / np.linalg.norm(t * .8 + up * .4 + r * .2))
    img = np.full((S, S, 3), 30.0); zb = np.full((S, S), -1e9)
    for i in range(len(tri)):
        x0, x1 = int(max(0, np.floor(px[i].min()))), int(min(S - 1, np.ceil(px[i].max())))
        y0, y1 = int(max(0, np.floor(py[i].min()))), int(min(S - 1, np.ceil(py[i].max())))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        (ax_, ay), (bx, by), (cx, cy) = zip(px[i], py[i])
        den = (by - cy) * (ax_ - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
        w1 = ((cy - ay) * (gx - cx) + (ax_ - cx) * (gy - cy)) / den
        w2 = 1 - w0 - w1; m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        zz = w0 * z[i, 0] + w1 * z[i, 1] + w2 * z[i, 2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= zz > sub
        sub[m] = zz[m]; img[y0:y1 + 1, x0:x1 + 1][m] = C[i] * (shade[i] if not RGB else .55 + .45 * shade[i])
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


ims = [render(vw) for vw in views]
sheet = Image.new('RGB', (S * len(ims), S))
for k, im in enumerate(ims):
    sheet.paste(im, (k * S, 0))
sheet.save(out); print('LABELS', out, {int(k): int((lab == k).sum()) for k in np.unique(lab)})
