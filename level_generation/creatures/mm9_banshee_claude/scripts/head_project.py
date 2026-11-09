#!/usr/bin/env python3
"""Head colour by projection of Codex repaints of our own exact renders (head_views.py): known orthographic cameras, depth test, weights by facing. Texels no view sees keep the base image.
Args: <views dir> <base png> <out png>. Uses work/uv_v1.npz. Run from the project folder."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ni
VD, BASE, OUT = sys.argv[1:4]
D = np.load('work/uv_v1.npz')
idx = D['Head_idx']; co = D['Head_co']; uvc = D['Head_uv']
P = co[idx]
SIZE = 1024
ORTHO, C = 0.46, np.array([0, -0.235, 0.60])
VIEWS = {'01_front': ((1, 0, 0), (0, -1, 0)), '02_back': ((-1, 0, 0), (0, 1, 0)), '03_left': ((0, -1, 0), (-1, 0, 0)), '04_right': ((0, 1, 0), (1, 0, 0))}   # image right, to camera
fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
Vn = np.zeros_like(co); np.add.at(Vn, idx.ravel(), np.repeat(fn, 3, 0)); Vn /= np.maximum(np.linalg.norm(Vn, axis=1, keepdims=True), 1e-12)
VN = Vn[idx]
tex_pos = np.zeros((SIZE, SIZE, 3), np.float32); tex_n = np.zeros((SIZE, SIZE, 3), np.float32); cov = np.zeros((SIZE, SIZE), bool)
uvp = uvc * SIZE; uvp[..., 1] = SIZE - uvp[..., 1]
for i in range(len(P)):
    a, b, c = uvp[i]
    x0, x1 = int(np.floor(min(a[0], b[0], c[0]))) - 1, int(np.ceil(max(a[0], b[0], c[0]))) + 2
    y0, y1 = int(np.floor(min(a[1], b[1], c[1]))) - 1, int(np.ceil(max(a[1], b[1], c[1]))) + 2
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, SIZE), min(y1, SIZE)
    if x1 <= x0 or y1 <= y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-9:
        continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
    l2 = 1 - l0 - l1
    m = (l0 > -0.03) & (l1 > -0.03) & (l2 > -0.03)
    if not m.any():
        continue
    yy, xx = ys[m].astype(int), xs[m].astype(int)
    w = np.stack([l0[m], l1[m], l2[m]], 1)
    tex_pos[yy, xx] = w @ P[i]; tex_n[yy, xx] = w @ VN[i]; cov[yy, xx] = True
tex_n /= np.maximum(np.linalg.norm(tex_n, axis=2, keepdims=True), 1e-9)
base = np.asarray(Image.open(BASE).convert('RGB').resize((SIZE, SIZE)), np.float64) / 255
acc = np.zeros((SIZE, SIZE, 3)); wsum = np.zeros((SIZE, SIZE))
for v, (rx, cam) in VIEWS.items():
    rx, cam = np.array(rx, float), np.array(cam, float)
    up = np.array([0, 0, 1.0])
    im = np.asarray(Image.open(Path(VD) / f'{v}.png').convert('RGBA').resize((1024, 1024), Image.LANCZOS), np.float64) / 255
    h, w_ = im.shape[:2]
    solid = ni.binary_erosion(im[..., 3] > 0.9, iterations=3)
    ind = ni.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    im = im[ind[0], ind[1]]
    # depth buffer of the head in this view
    px = lambda q: ((q - C) @ rx / ORTHO + 0.5) * w_
    py = lambda q: (0.5 - (q - C) @ up / ORTHO) * h
    tri_x = px(P); tri_y = py(P); tri_z = (P - C) @ cam
    zb = np.full((h // 2, w_ // 2), -1e9)
    fnv = fn @ cam
    for i in np.where(fnv > 0)[0]:
        a, b, c = tri_x[i] / 2, tri_y[i] / 2, tri_z[i]
        x0, x1 = int(a.min()), int(a.max()) + 2; y0, y1 = int(b.min()), int(b.max()) + 2
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, w_ // 2), min(y1, h // 2)
        if x1 <= x0 or y1 <= y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
        d = (b[1] - b[2]) * (a[0] - a[2]) + (a[2] - a[1]) * (b[0] - b[2])
        if abs(d) < 1e-9:
            continue
        l0 = ((b[1] - b[2]) * (xs - a[2]) + (a[2] - a[1]) * (ys - b[2])) / d
        l1 = ((b[2] - b[0]) * (xs - a[2]) + (a[0] - a[2]) * (ys - b[2])) / d
        l2 = 1 - l0 - l1
        m = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
        if not m.any():
            continue
        z = l0 * c[0] + l1 * c[1] + l2 * c[2]
        yy, xx = ys[m].astype(int), xs[m].astype(int)
        zb[yy, xx] = np.maximum(zb[yy, xx], z[m])
    tx = px(tex_pos); ty = py(tex_pos); tz = (tex_pos - C) @ cam
    ix = np.clip((tx / 2).astype(int), 0, w_ // 2 - 1); iy = np.clip((ty / 2).astype(int), 0, h // 2 - 1)
    vis = tz > zb[iy, ix] - 0.004
    wt = np.clip(tex_n @ cam, 0, 1) ** 4 * vis * cov
    col = np.stack([ni.map_coordinates(im[..., c], [ty - 0.5, tx - 0.5], order=1, mode='nearest') for c in range(3)], -1)
    acc += col * wt[..., None]; wsum += wt
    print(v, 'visible texels', int((wt > 0.01).sum()))
out = base.copy()
m = wsum > 0.02
k = np.clip(wsum / 0.08, 0, 1)[..., None]
out = base * (1 - k) + (acc / np.maximum(wsum, 1e-6)[..., None]) * k
out[wsum <= 1e-6] = base[wsum <= 1e-6]
Image.fromarray((out.clip(0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT)
print('PROJECT seen', float(m.sum() / cov.sum()))
