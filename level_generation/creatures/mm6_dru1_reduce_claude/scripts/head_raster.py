"""Texel raster of the new head layout (work/headuv.npz) at SIZE (default 1024): per texel the face index (-1 empty),
uvpart, rest-pose 3D position and interpolated normal; texels are covered when any corner/edge/centre sample of a
face lands in them (sub-texel faces). -> work/head_raster.npz. Usage: head_raster.py [size]"""
import sys
import numpy as np
S = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
d = np.load('work/headuv.npz'); uv = d['huv'] * S; uv[..., 1] = S - uv[..., 1]
fid = -np.ones((S, S), np.int32); bary = np.zeros((S, S, 3), np.float32)
for i, t in enumerate(uv):
    x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    (ax, ay), (bx, by), (cx, cy) = t
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-12: continue
    l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
    l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den; l3 = 1 - l1 - l2
    inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
    yy, xx = (ys[inside] - .5).astype(int), (xs[inside] - .5).astype(int)
    fid[yy, xx] = i; bary[yy, xx] = np.stack([l1[inside], l2[inside], l3[inside]], 1)
    # sub-texel faces: corners, edge midpoints, centre
    for w in ([1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1 / 3] * 3):
        px, py = (np.array(w) @ t).astype(int)
        if 0 <= px < S and 0 <= py < S and fid[py, px] < 0: fid[py, px] = i; bary[py, px] = w
cov = fid >= 0
pos = np.zeros((S, S, 3), np.float32); nrm = np.zeros((S, S, 3), np.float32)
pos[cov] = np.einsum('nk,nkc->nc', bary[cov], d['pos'][fid[cov]]); nrm[cov] = np.einsum('nk,nkc->nc', bary[cov], d['nrm'][fid[cov]])
nrm[cov] /= np.linalg.norm(nrm[cov], axis=1, keepdims=True) + 1e-9
part = np.where(cov, d['uvpart'][np.maximum(fid, 0)], 0)
np.savez_compressed('work/head_raster.npz', fid=fid, part=part, pos=pos, nrm=nrm)
print('RASTER', S, 'covered %.3f' % cov.mean(), {int(k): int((part == k).sum()) for k in np.unique(part)})
