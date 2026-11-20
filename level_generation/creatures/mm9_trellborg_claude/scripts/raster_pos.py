#!/usr/bin/env python3
"""Texel -> rest position maps per set. Writes work/body_pos.npz, work/head_pos.npz (pos, cov, prt). Arg: size"""
import sys
import numpy as np
S = int(sys.argv[1]) if len(sys.argv) > 1 else 2048
Z = np.load('work/faces.npz')
def rast(CO, UV, PT, out):
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
        cov[y0:y1 + 1, x0:x1 + 1][m] = True; prt[y0:y1 + 1, x0:x1 + 1][m] = PT[t]
    np.savez(out, pos=pos, cov=cov, prt=prt); print('RASTER', out, cov.mean())
rast(Z['bc'], Z['bu'], Z['bp'], 'work/body_pos.npz'); rast(Z['hc'], Z['hu'], Z['hp'], 'work/head_pos.npz')
