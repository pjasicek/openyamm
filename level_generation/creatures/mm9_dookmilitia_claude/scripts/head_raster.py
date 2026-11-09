"""Texel raster of the head set (position, part per texel) from work/head_faces.npz, as project_head.py builds it. raster(S) -> pos (S,S,3), cov, prt"""
import numpy as np
def raster(S, path='work/head_faces.npz'):
    Z = np.load(path); CO, UV, PART = Z['co'], Z['uv'], Z['part']
    pos = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool); prt = np.zeros((S, S), np.uint8)
    for t in range(len(CO)):
        u = UV[t]; x = u[:, 0] * S; y = (1 - u[:, 1]) * S
        x0, x1 = int(max(np.floor(x.min()) - 1, 0)), int(min(np.ceil(x.max()) + 1, S - 1)); y0, y1 = int(max(np.floor(y.min()) - 1, 0)), int(min(np.ceil(y.max()) + 1, S - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-9: continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        g = 1 - a - b
        m = (a >= -0.02) & (b >= -0.02) & (g >= -0.02)
        pos[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * CO[t, 0] + b[..., None] * CO[t, 1] + g[..., None] * CO[t, 2])[m]
        cov[y0:y1 + 1, x0:x1 + 1][m] = True; prt[y0:y1 + 1, x0:x1 + 1][m] = PART[t]
    return pos, cov, prt
