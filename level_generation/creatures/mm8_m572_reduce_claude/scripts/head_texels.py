#!/usr/bin/env python3
"""Head texel map of the Phoenix atlas (2048²): per texel the rest-pose position (barycentric over the source face
that covers it) and region label (1 Head/Jaw, 2 Neck, 0 other) -> work/retex/head_texels.npz. Inputs: work/mesh_in.npz,
work/src_face_bone.npz (scripts/face_bones.py)."""
import numpy as np
d = np.load('work/mesh_in.npz'); fb = np.load('work/src_face_bone.npz'); names = [str(n) for n in fb['names']]
N = 2048; uv = d['wuv'].reshape(-1, 3, 2); tri = d['verts'][d['faces']]
cls = np.array([1 if names[b] in ('Head', 'Jaw') else (2 if names[b].startswith('Neck') else 0) for b in fb['bone']])
lab = np.zeros((N, N), np.uint8); pos = np.zeros((N, N, 3), np.float32)
for i in np.where(cls > 0)[0]:
    p = np.stack([uv[i][:, 0] % 1 * N, (1 - uv[i][:, 1] % 1) * N], 1)
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, N)), np.arange(max(y0, 0), min(y1 + 1, N)))
    q = np.stack([xs.ravel() + .5, ys.ravel() + .5], 1)
    a, b, c = p; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    l0 = ((b[1] - c[1]) * (q[:, 0] - c[0]) + (c[0] - b[0]) * (q[:, 1] - c[1])) / den
    l1 = ((c[1] - a[1]) * (q[:, 0] - c[0]) + (a[0] - c[0]) * (q[:, 1] - c[1])) / den
    l2 = 1 - l0 - l1; ins = (l0 >= -.02) & (l1 >= -.02) & (l2 >= -.02)
    if not ins.any():
        continue
    yy, xx = q[ins, 1].astype(int), q[ins, 0].astype(int)
    keep = (lab[yy, xx] == 0) | (cls[i] == 1)
    yy, xx = yy[keep], xx[keep]; w = np.stack([l0, l1, l2], 1)[ins][keep]
    lab[yy, xx] = cls[i]; pos[yy, xx] = w @ tri[i]
np.savez_compressed('work/retex/head_texels.npz', lab=lab, pos=pos)
print('HEADTEXELS head', int((lab == 1).sum()), 'neck', int((lab == 2).sum()))
