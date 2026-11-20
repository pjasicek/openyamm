#!/usr/bin/env python3
"""Fallback / comparison: carry PeasantF1's approved face paint onto PF4's head layout. The head shell is F1's (same asm triangles), so every
PF4 head-shell texel (face window: |x| < 7 cm, 1.495-1.69 m over the soles) takes F1's colour at the same barycentric point of the same
asm triangle in F1's head layout (read only from ../mm9_peasantf1_claude). Args: <F1 head png> <PF4 base png> <out png> (project folder)"""
import sys
import numpy as np
from PIL import Image
SRCF1, BASE, OUT = sys.argv[1:4]
F = np.load('../mm9_peasantf1_claude/work/uv.npz'); U = np.load('work/uv.npz'); A = np.load('work/asm_frozen.npz')
f1 = np.asarray(Image.open(SRCF1).convert('RGB'), np.float32); N1 = f1.shape[0]
im = np.asarray(Image.open(BASE).convert('RGB'), np.float32).copy(); S = im.shape[0]
names = [str(x) for x in U['names']]; kh = names.index('head'); Z0 = -0.9297
# F1 head faces keyed by their sorted asm vertex triple
key1 = {}
for r in np.where(F['mat'] == 1)[0]:
    t = F['tri'][r]; key1[tuple(sorted(F['orig'][t]))] = r
done = 0
for r in np.where((U['mat'] == 1) & (U['comp'][U['tri'][:, 0]] == kh))[0]:
    t = U['tri'][r]; o = U['orig'][t]; r1 = key1.get(tuple(sorted(o)))
    if r1 is None: continue
    t1 = F['tri'][r1]; o1 = F['orig'][t1]; perm = [int(np.where(o1 == v)[0][0]) for v in o]; uv1 = F['uv'][t1][perm]
    c = A['co'][o].mean(0)
    if not (abs(c[0]) < 0.075 and 1.48 < c[2] - Z0 < 1.70): continue
    q = U['uv'][t] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l, 1 - l.sum(1)]; ins = (L3 >= -0.02).all(1)
    if not ins.any(): continue
    p1 = L3[ins] @ uv1; px = np.clip((p1[:, 0] * N1).astype(int), 0, N1 - 1); py = np.clip(((1 - p1[:, 1]) * N1).astype(int), 0, N1 - 1)
    yy, xx = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)
    im[yy, xx] = f1[py, px]; done += 1
Image.fromarray(np.clip(im, 0, 255).astype('u1')).save(OUT); print('F1FACE faces', done)
