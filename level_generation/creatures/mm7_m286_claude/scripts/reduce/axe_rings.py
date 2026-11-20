#!/usr/bin/env python3
"""Exact haft reduction of the procedural axe (work/axe_dec/mesh_in.npz): the haft is a stack of 8-sided rings
(make_axe.py) whose radius only wiggles by 1-2 mm between the copper bands (the texture paints them), so the
quadric collapse twisted it into a lumpy, kinked shaft. Instead, rings are dropped from the profile (y, radius) by
Douglas-Peucker with tolerance AXE_RING_TOL (default 1.5 mm) and a longest span of AXE_RING_SPAN (default 0.3 m);
the grip band rings (y within the grip band, axe_dump.py) and every ring outside the straight haft (pommel, collar,
spike, y < -0.23 or > 0.66) stay. The faces between two kept rings that were adjacent stay as they are; a removed run
becomes one 8-quad strip (outward winding, the same per-vertex planar UVs). The blades are untouched.
-> work/axe_dec2/mesh_in.npz, work/axe_dec2/haft.npy (haft faces: kept exactly by the blade decimation)."""
import os
import numpy as np
E = lambda k, x: float(os.environ.get(k, x))
d = np.load('work/axe_dec/mesh_in.npz'); v, f = d['verts'], d['faces']; wuv = d['wuv'].reshape(-1, 3, 2)
grip = np.load('work/axe_dec/grip.npy')
vuv = {}
for t, w in zip(f, wuv):
    for a, uv in zip(t, w):
        vuv.setdefault(int(a), uv)
haft_v = np.where(np.abs(v[:, 0]) < 0.08)[0]
gy = v[np.unique(f[grip]), 1]; g0, g1 = gy.min() - 1e-4, gy.max() + 1e-4
rings = []
for y in np.unique(np.round(v[haft_v, 1], 4)):
    m = haft_v[np.abs(v[haft_v, 1] - y) < 2e-4]
    if len(m) == 8 and -0.23 < y < 0.66:
        ang = np.arctan2(v[m, 2], v[m, 0]); m = m[np.argsort(ang)]
        rings.append((float(v[m, 1].mean()), float(np.hypot(v[m, 0], v[m, 2]).mean()), m))
rings.sort(key=lambda r: r[0])
TOL, SPAN = E('AXE_RING_TOL', '0.0015'), E('AXE_RING_SPAN', '0.3')
keep = np.zeros(len(rings), bool); keep[0] = keep[-1] = True
for i, (y, r, m) in enumerate(rings):
    if g0 <= y <= g1:
        keep[i] = True


def dp(i, j):
    if j <= i + 1:
        return
    ys = np.array([rings[k][0] for k in range(i, j + 1)]); rs = np.array([rings[k][1] for k in range(i, j + 1)])
    lin = rs[0] + (rs[-1] - rs[0]) * (ys - ys[0]) / (ys[-1] - ys[0]); err = np.abs(rs - lin)
    k = int(err[1:-1].argmax()) + 1
    if err[k] > TOL or ys[-1] - ys[0] > SPAN:
        keep[i + k] = True; dp(i, i + k); dp(i + k, j)


idx = np.flatnonzero(keep)
for a, b in zip(idx[:-1], idx[1:]):
    dp(a, b)
idx = np.flatnonzero(keep)
remove_faces = np.zeros(len(f), bool); new_f, new_w = [], []
for a, b in zip(idx[:-1], idx[1:]):
    if b == a + 1:
        continue
    run = np.concatenate([rings[k][2] for k in range(a, b + 1)])
    remove_faces |= np.isin(f, run).all(1)
    A, B = rings[a][2], rings[b][2]
    for k in range(8):
        k2 = (k + 1) % 8
        for t in ((A[k], A[k2], B[k2]), (A[k], B[k2], B[k])):
            p = v[list(t)]; n = np.cross(p[1] - p[0], p[2] - p[0]); c = p.mean(0); rad = np.array([c[0], 0, c[2]])
            if n @ rad < 0:
                t = (t[0], t[2], t[1])
            new_f.append(t); new_w.append([vuv[int(x)] for x in t])
f2 = np.concatenate([f[~remove_faces], np.array(new_f, np.int32)]); w2 = np.concatenate([wuv[~remove_faces], np.array(new_w)])
used = np.unique(f2); remap = -np.ones(len(v), int); remap[used] = np.arange(len(used))
os.makedirs('work/axe_dec2', exist_ok=True)
haft = np.isin(f2, haft_v).all(1)
np.savez('work/axe_dec2/mesh_in.npz', verts=v[used], faces=remap[f2].astype(np.int32), wuv=w2.reshape(-1, 2), protect=np.zeros(len(f2)))
np.save('work/axe_dec2/haft.npy', haft)
print('AXERINGS rings', len(rings), 'kept', int(keep.sum()), 'at y', [round(rings[k][0], 3) for k in idx], 'faces', len(f), '->', len(f2),
      'haft faces', int(haft.sum()))
