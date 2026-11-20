#!/usr/bin/env python3
"""Flat-coloured orthographic views (painter's order) of the installed LOD0 faces for checking sets: per face a colour from a
label array. Usage (library): views(P, T, rgb, region, out) with region = (xmin, xmax, ymin, ymax) in glTF metres."""
import numpy as np
from PIL import Image, ImageDraw


def view(P, T, rgb, axis, region, size=600):
    # axis: 'front' (+z towards camera), 'back', 'left' (camera at -x... looking +x), 'right'
    X = P[T]
    if axis == 'front':
        u, v, d = X[..., 0], X[..., 1], X[..., 2]
    elif axis == 'back':
        u, v, d = -X[..., 0], X[..., 1], -X[..., 2]
    elif axis == 'right':      # camera on +x looking -x
        u, v, d = -X[..., 2], X[..., 1], X[..., 0]
    else:                      # camera on -x
        u, v, d = X[..., 2], X[..., 1], -X[..., 0]
    x0, x1, y0, y1 = region
    if axis in ('left', 'right'):
        x0, x1 = -0.25, 0.25
    s = size / max(x1 - x0, y1 - y0)
    W = int((x1 - x0) * s); H = int((y1 - y0) * s)
    im = Image.new('RGB', (W, H), (40, 40, 40)); dr = ImageDraw.Draw(im)
    fn = np.cross(np.stack([u[:, 1] - u[:, 0], v[:, 1] - v[:, 0], d[:, 1] - d[:, 0]], 1),
                  np.stack([u[:, 2] - u[:, 0], v[:, 2] - v[:, 0], d[:, 2] - d[:, 0]], 1))
    order = np.argsort(d.mean(1))
    for f in order:
        if fn[f, 2] <= 0:
            continue
        pts = [((u[f, k] - x0) * s, (y1 - v[f, k]) * s) for k in range(3)]
        sh = 0.55 + 0.45 * abs(fn[f, 2]) / (np.linalg.norm(fn[f]) + 1e-20)
        dr.polygon(pts, fill=tuple(int(c * sh) for c in rgb[f]))
    return im


def views(P, T, rgb, region, out, axes=('front', 'right', 'back', 'left'), size=600):
    ims = [view(P, T, rgb, a, region, size) for a in axes]
    W = sum(i.width for i in ims) + 10 * (len(ims) - 1); H = max(i.height for i in ims)
    sheet = Image.new('RGB', (W, H), (0, 0, 0)); x = 0
    for i in ims:
        sheet.paste(i, (x, 0)); x += i.width + 10
    sheet.save(out)
