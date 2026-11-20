#!/usr/bin/env python3
"""Per-texel 3D positions of the body atlas (2048): work/texel_xyz.npz (xyz float32, tri int32), for the paint repairs in
compose_fish.py, plus an unrolled review image: rows = elevation around the body (top to belly), columns = y.
Usage: texel_map.py [image to unroll] [out png]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent.parent
S = 2048
d = np.load(HERE / 'work' / 'uv3d_body.npz')
uv, xyz = d['uv'] * S, d['xyz']
tri = np.full((S, S), -1, np.int32)
pos = np.zeros((S, S, 3), np.float32)
for t in range(len(uv)):
    p = uv[t]
    x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), S - 1)
    y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), S - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    l3 = 1 - l1 - l2
    ins = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
    iy, ix = np.nonzero(ins)
    r, c_ = S - 1 - (iy + y0), ix + x0
    tri[r, c_] = t
    pos[r, c_] = (l1[ins, None] * xyz[t, 0] + l2[ins, None] * xyz[t, 1] + l3[ins, None] * xyz[t, 2])
np.savez(HERE / 'work' / 'texel_xyz.npz', xyz=pos, tri=tri)
if len(sys.argv) > 2:
    im = np.asarray(Image.open(sys.argv[1]).convert('RGB').resize((S, S)))
    bodyt = tri >= 0
    bodyt &= d['part'][np.maximum(tri, 0)] == 0
    P = pos[bodyt]; C = im[bodyt]
    v = d['xyz'][d['part'] == 0].reshape(-1, 3)
    ybins = np.round((P[:, 1] + 0.17) * 3000).astype(int)
    # elevation by height and half depth at y
    yk = np.round(v[:, 1] * 500).astype(int)
    top = {}; bot = {}
    for k, z in zip(yk, v[:, 2]):
        top[k] = max(top.get(k, -9), z); bot[k] = min(bot.get(k, 9), z)
    kk = np.array(sorted(top)); tv = np.array([top[k] for k in kk]); bv = np.array([bot[k] for k in kk])
    ty = np.interp(P[:, 1] * 500, kk, tv); by = np.interp(P[:, 1] * 500, kk, bv)
    e = (ty - P[:, 2]) / np.maximum(ty - by, 1e-4)
    H = 500; W = 1040
    for side, name in ((P[:, 0] >= 0, 'pos'), (P[:, 0] < 0, 'neg')):
        out = np.zeros((H, W, 3), np.uint8)
        r = np.clip((e[side] * (H - 1)).astype(int), 0, H - 1)
        c = np.clip(ybins[side], 0, W - 1)
        out[r, c] = C[side]
        Image.fromarray(out).save(sys.argv[2].replace('.png', f'_{name}.png'))
print('TEXELS', int((tri >= 0).sum()))
