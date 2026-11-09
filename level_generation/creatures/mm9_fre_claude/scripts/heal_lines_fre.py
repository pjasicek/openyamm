#!/usr/bin/env python3
"""Fre pass 2 (orchestrator pre-screen r20: thin dark lines on the cheek and down both sides of the neck, a dark V at the chin point).
detect: in the unlit, nearest-texel base-colour renders of the head (scripts/uv_probe_render.py, work/uvprobe/base_<view>.png with the
        matching UV renders uv_<view>.npy), skin pixels (their 9-px median is skin) darker than THR of that median are thin paint lines;
        their texels (UV lookup) minus the face features (eyes, brows, lips, nostrils: 3D zones on the head shell) are written to
        work/line_texels.npy, grown by 1 texel.
apply:  <in png> <out png> [normal]: every listed texel takes the median of the unlisted head-skin texels within R px (colour), or their
        renormalised mean (normal map). Args: detect [THR] [probe dir] [earlier npy to union] | apply <in> <out> [normal]   (project folder)"""
import sys, glob, os
import numpy as np
from PIL import Image
from scipy import ndimage as ni
S = 1024
if sys.argv[1] == 'detect':
    THR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.90
    D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
    POS = np.full((S, S, 3), np.nan)
    for f in np.where((mat == 1) & (comp[tri[:, 0]] == names.index('head')))[0]:
        q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
        if abs(np.linalg.det(T_)) < 1e-12: continue
        l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); b = np.vstack([l, 1 - l.sum(0)]); ok = (b >= -1e-4).all(0)
        if ok.any(): POS[gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)] = (b[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1)
    x, z, y = POS[..., 0], np.nan_to_num(POS[..., 2], nan=-9), np.nan_to_num(POS[..., 1], nan=9); ax = np.abs(np.nan_to_num(x, nan=9))
    feat = ((z > 0.663) & (z < 0.74) & (ax < 0.065) & (y < -0.06)) | ((z > 0.598) & (z < 0.632) & (ax < 0.030) & (y < -0.085)) | \
           ((z > 0.632) & (z < 0.66) & (ax < 0.014) & (y < -0.10)) | (z > 0.74)
    L = np.zeros((S, S), bool)
    PD = sys.argv[3] if len(sys.argv) > 3 else 'work/uvprobe'
    for bp in sorted(glob.glob(f'{PD}/base_*.png')):
        v = os.path.basename(bp)[5:-4]; im = np.asarray(Image.open(bp).convert('RGBA'), np.float32) / 255; U = np.load(f'{PD}/uv_{v}.npy')
        head = (U[..., 2] > 0.5) & (im[..., 3] > 0.5); rgb = im[..., :3]; lum = rgb @ [0.2126, 0.7152, 0.0722]
        med = np.stack([ni.median_filter(rgb[..., c], size=int(os.environ.get('MEDSZ', '9'))) for c in range(3)], -1); ml = med @ [0.2126, 0.7152, 0.0722]
        skin = head & (med[..., 0] > 0.45) & (med[..., 0] > med[..., 1] * 1.08) & (med[..., 1] > med[..., 2])
        line = skin & ((lum < THR * ml) | (np.linalg.norm(rgb - med, axis=-1) > float(os.environ.get('CDIFF', '9'))))
        ys, xs = np.where(line); tu = np.clip((U[ys, xs, 0] * S).astype(int), 0, S - 1); tv = np.clip(((1 - U[ys, xs, 1]) * S).astype(int), 0, S - 1)
        L[tv, tu] = True; print('VIEW', v, 'line px', len(ys))
    L = ni.binary_dilation(L, iterations=int(os.environ.get('LDIL', '1'))) & ~np.isnan(POS[..., 0]) & ~feat
    if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): L |= np.load(sys.argv[4])      # union with an earlier pass
    np.save('work/line_texels.npy', L); print('LINES texels', int(L.sum()))
else:
    SRC, DST = sys.argv[2:4]; NORMAL = len(sys.argv) > 4 and sys.argv[4] == 'normal'
    L = np.load('work/line_texels.npy'); im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255
    if im.shape[0] != S: raise SystemExit('size')
    good = ~L & ((im[..., 0] > 0.45) & (im[..., 0] > im[..., 1]) & (im[..., 1] > im[..., 2]) if not NORMAL else True); R = int(os.environ.get('HEALR', '6'))
    acc = np.zeros_like(im); cnt = np.zeros((S, S))
    ys, xs = np.where(L); out = im.copy()
    for yy, xx in zip(ys, xs):
        y0, y1, x0, x1 = max(yy - R, 0), min(yy + R + 1, S), max(xx - R, 0), min(xx + R + 1, S)
        blk = im[y0:y1, x0:x1][good[y0:y1, x0:x1]]
        if len(blk) == 0: continue
        if NORMAL:
            n = (blk * 2 - 1).mean(0); n /= max(np.linalg.norm(n), 1e-6); out[yy, xx] = (n + 1) / 2
        else:
            out[yy, xx] = np.median(blk, 0)
    Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST); print('HEAL', DST, len(ys))
