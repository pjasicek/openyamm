#!/usr/bin/env python3
"""Rest-pose position map of the head image (1024x1024, head-atlas faces of the source LOD0, barycentric per texel)
-> work/head_posmap.npz (pos, valid, face class of the covering face: 2 beard faces, 1 other head faces)."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
X0, S = 1056, 1024
cls = np.asarray(Image.open('../mm8_m444_claude/textures/smuggler_head_material_classes.png'))
pos = np.zeros((S, S, 3)); valid = np.zeros((S, S), bool); fcls = np.zeros((S, S), np.int8)
head = (uv[:, :, 0] * 2080 >= X0 - 1).all(1)
for i in np.where(head)[0]:
    px = np.stack([uv[i, :, 0] * 2080 - X0, (1 - uv[i, :, 1]) * S], 1)
    x0, y0 = np.floor(px.min(0)).astype(int); x1, y1 = np.ceil(px.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, S - 1) + 1), np.arange(max(y0, 0), min(y1, S - 1) + 1))
    p = np.stack([xs + .5, ys + .5], -1).reshape(-1, 2)
    a, b, c = px; m = np.array([b - a, c - a]).T
    if abs(np.linalg.det(m)) < 1e-9:
        continue
    l = np.linalg.solve(m, (p - a).T).T; w = np.c_[1 - l.sum(1), l]
    ins = (w > -0.02).all(1)
    if not ins.any():
        continue
    q = p[ins].astype(int); pos[q[:, 1], q[:, 0]] = w[ins] @ v[f[i]]; valid[q[:, 1], q[:, 0]] = True
    sc = np.bincount(cls[q[:, 1], q[:, 0]], minlength=10).argmax(); fcls[q[:, 1], q[:, 0]] = 2 if sc == 2 else 1
np.savez('work/head_posmap.npz', pos=pos, valid=valid, fcls=fcls)
print('POSMAP valid', int(valid.sum()), 'beard texels', int((fcls == 2).sum()))
