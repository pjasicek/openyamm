"""Rest-pose 3D position of every head-set texel: rasterise the head (and hand) faces of a dump_mesh.py npz in HeadUV
space at the head set's size. Writes <out npz>: pos (H, W, 3) metres (NaN where no face), face (H, W) face index.
Usage: texel_pos.py <dump npz> <size> <out npz>"""
import sys, numpy as np
d = np.load(sys.argv[1], allow_pickle=True); N = int(sys.argv[2])
P, L, ls, lt, U = d['P'], d['L'], d['ls'], d['lt'], d['huv']
sel = np.where(d['head'] | d['hand'])[0]
pos = np.full((N, N, 3), np.nan, np.float32); face = -np.ones((N, N), np.int32)
for f in sel:
    li = np.arange(ls[f], ls[f] + lt[f])
    for k in range(1, lt[f] - 1):
        tri = [li[0], li[k], li[k + 1]]
        uv = U[tri] * [N, N]; uv[:, 1] = N - uv[:, 1]          # image rows top-down
        xyz = P[L[tri]]
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
        if x1 < x0 or y1 < y0: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = uv
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12: continue
        w0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
        w1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.01) & (w1 >= -0.01) & (w2 >= -0.01)
        ys, xs = np.where(m)
        pos[y0 + ys, x0 + xs] = (w0[m, None] * xyz[0] + w1[m, None] * xyz[1] + w2[m, None] * xyz[2])
        face[y0 + ys, x0 + xs] = f
np.savez_compressed(sys.argv[3], pos=pos, face=face)
print('TEXELPOS', np.isfinite(pos[..., 0]).mean())
