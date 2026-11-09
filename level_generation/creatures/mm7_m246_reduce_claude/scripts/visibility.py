#!/usr/bin/env python3
"""Per-face visibility of the rest mesh (work/mesh_in.npz) inside a height band: face-id z-buffers from REA_VIEWS
(default 42) directions over the sphere (those from below REA_ZDIR_MIN dropped) (orthographic, 0.8 mm pixels), counting in how many views each face owns at
least REA_MIN_PIX pixels. Hidden faces (scalp under the helmet, neck under the coif and collar) can take a harder cut.
Usage: visibility.py <zmin> <zmax> -> work/visible.npy (views per face)"""
import os
import sys
import numpy as np

d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']
z0, z1 = float(sys.argv[1]), float(sys.argv[2])
sel = np.flatnonzero((v[f][:, :, 2].max(1) >= z0) & (v[f][:, :, 2].min(1) <= z1))
N = int(os.environ.get('REA_VIEWS', '42')); PIX = float(os.environ.get('REA_PIX', '0.0008'))
MINPIX = int(os.environ.get('REA_MIN_PIX', '2'))
k = np.arange(N) + .5; phi = np.arccos(1 - 2 * k / N); th = np.pi * (1 + 5 ** .5) * k
dirs = np.stack([np.sin(phi) * np.cos(th), np.sin(phi) * np.sin(th), np.cos(phi)], 1)
# game cameras look from about head height or above: drop directions from well below (REA_ZDIR_MIN)
dirs = dirs[dirs[:, 2] >= float(os.environ.get('REA_ZDIR_MIN', '-0.25'))]
# m246: REA_YDIR_MAX keeps only directions from the front (the goblin faces -y): the visible face front
dirs = dirs[dirs[:, 1] <= float(os.environ.get('REA_YDIR_MAX', '1'))]
seen = np.zeros(len(f), int)
tri_all = v[f[sel]]
for dv in dirs:
    t = dv / np.linalg.norm(dv); a = np.array([0, 0, 1.]) if abs(t[2]) < .9 else np.array([1., 0, 0])
    r = np.cross(a, t); r /= np.linalg.norm(r); u = np.cross(t, r)
    x = tri_all @ r; y = tri_all @ u; z = tri_all @ t
    lo = np.array([x.min(), y.min()]); W = int((x.max() - lo[0]) / PIX) + 2; H = int((y.max() - lo[1]) / PIX) + 2
    px = (x - lo[0]) / PIX; py = (y - lo[1]) / PIX
    zb = np.full((H, W), -1e9); ib = np.full((H, W), -1)
    for i in range(len(tri_all)):
        x0, x1 = int(np.floor(px[i].min())), int(np.ceil(px[i].max())); y0, y1 = int(np.floor(py[i].min())), int(np.ceil(py[i].max()))
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        (ax, ay), (bx, by), (cx, cy) = zip(px[i], py[i])
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den; w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
        w2 = 1 - w0 - w1; m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        zz = w0 * z[i, 0] + w1 * z[i, 1] + w2 * z[i, 2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= zz > sub; sub[m] = zz[m]; ib[y0:y1 + 1, x0:x1 + 1][m] = i
    cnt = np.bincount(ib[ib >= 0], minlength=len(sel))
    seen[sel] += cnt >= MINPIX
np.save(os.environ.get('REA_VIS_OUT', 'work/visible.npy'), seen)
print('VISIBLE band', z0, z1, 'faces', len(sel), 'never seen', int((seen[sel] == 0).sum()), 'seen in <=2 views', int((seen[sel] <= 2).sum()))
