#!/usr/bin/env python3
"""Per-layer audit of the head projection: which view paints each layer, and whether a texel's paint came from behind another layer. For every head texel and every projected view, the layer the view actually sees at that pixel (z-buffer of all head faces) against the texel's own layer. Counts texels with weight in a view where the first surface along the ray is a DIFFERENT layer, and how far in front it is. Project folder."""
import sys
import numpy as np
sys.path.insert(0, 'scripts')
Z = np.load('work/head_faces.npz'); CO, PART = Z['co'], Z['part']
C = np.array([0.0, -0.029010720551013947, 0.47669053077697754]); ORTHO = 0.5; R = 700
VIEWS = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1)}
def cam(d):
    d = np.array(d, float); d /= np.linalg.norm(d); up = np.array([0, 0, 1.0])
    if abs(d @ up) > 0.99: up = np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); return d, r, np.cross(d, r)
names = {20: 'face', 21: 'helm', 22: 'eyes', 23: 'horns', 24: 'neck'}
for nm, dv in VIEWS.items():
    d, r, u = cam(dv)
    zb = np.full((R, R), -1e9, np.float32); lb = np.zeros((R, R), np.int32)
    px = ((CO - C) @ r / ORTHO + 0.5) * R; py = (0.5 - (CO - C) @ u / ORTHO) * R; dz = (CO - C) @ d
    for t in range(len(CO)):
        x, y, z = px[t], py[t], dz[t]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        det = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(det) < 1e-9: continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / det; b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / det; g = 1 - a - b
        m = (a >= 0) & (b >= 0) & (g >= 0); zz = a * z[0] + b * z[1] + g * z[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; sl = lb[y0:y1 + 1, x0:x1 + 1]
        w = m & (zz > sub); sub[w] = zz[w]; sl[w] = PART[t]
    tol = 0.006
    c = CO.mean(1); ix = np.clip(((c - C) @ r / ORTHO + 0.5) * R, 0, R - 1).astype(int); iy = np.clip((0.5 - (c - C) @ u / ORTHO) * R, 0, R - 1).astype(int)
    dzc = (c - C) @ d; N = np.cross(CO[:, 1] - CO[:, 0], CO[:, 2] - CO[:, 0]); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    facing = N @ d > 0.1
    rep = {}
    for p, n in names.items():
        q = (PART == p) & facing
        seen = q & (dzc >= zb[iy, ix] - tol)                  # what project_head.py accepts
        wrong = seen & (lb[iy, ix] != p)                      # accepted, but the first surface there is another layer
        rep[n] = (int(q.sum()), int(seen.sum()), int(wrong.sum()))
    print(nm, 'layer: facing, accepted, accepted though another layer is in front:', rep)
