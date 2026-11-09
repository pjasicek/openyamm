#!/usr/bin/env python3
"""Orthographic flat-shaded PIL render of GLB rest faces coloured by a class array (painter's order).
render(P, T, cls, colours, views, out, box=None) ; views: list of (name, right, up) axis vectors (view dir = up x right)."""
import numpy as np
from PIL import Image, ImageDraw
PAL = [(150, 150, 150), (230, 60, 60), (60, 200, 60), (60, 90, 230), (230, 200, 40), (200, 60, 220), (40, 210, 210), (250, 140, 30), (120, 60, 20), (255, 255, 255)]
VIEWS = {'front': ((1, 0, 0), (0, 1, 0)), 'side': ((0, 0, 1), (0, 1, 0)), 'back': ((-1, 0, 0), (0, 1, 0)), 'top': ((1, 0, 0), (0, 0, -1)),
         'q34': ((0.707, 0, 0.707), (0, 1, 0)), 'below': ((1, 0, 0), (0, 0, 1)), 'lside': ((0, 0, -1), (0, 1, 0))}


def render(P, T, cls, views, out, size=700, box=None):
    ims = []
    for v in views:
        r, u = (np.array(a, float) for a in VIEWS[v]); d = np.cross(u, r)   # toward the viewer
        X = P @ r; Y = P @ u; Z = P @ d
        sel = np.arange(len(T)) if box is None else np.flatnonzero(np.all((P[T].mean(1) >= box[0]) & (P[T].mean(1) <= box[1]), 1))
        lo = np.array([X[T[sel]].min(), Y[T[sel]].min()]); hi = np.array([X[T[sel]].max(), Y[T[sel]].max()])
        s = (size - 20) / max(hi - lo)
        im = Image.new('RGB', (size, size), (30, 30, 40)); dr = ImageDraw.Draw(im)
        n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        lit = np.clip(n @ d, 0, 1) * 0.7 + 0.3
        order = sel[np.argsort(Z[T[sel]].mean(1))]
        for f in order:
            if n[f] @ d <= 0: continue
            pts = [(10 + (X[i] - lo[0]) * s, size - 10 - (Y[i] - lo[1]) * s) for i in T[f]]
            c = PAL[int(cls[f]) % len(PAL)]; dr.polygon(pts, fill=tuple(int(k * lit[f]) for k in c))
        dr.text((5, 5), v, fill=(255, 255, 255)); ims.append(im)
    W = Image.new('RGB', (size * len(ims), size)); [W.paste(im, (i * size, 0)) for i, im in enumerate(ims)]; W.save(out)
