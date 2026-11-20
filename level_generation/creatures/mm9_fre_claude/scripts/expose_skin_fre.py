#!/usr/bin/env python3
"""Fre pass 3 (drawn-back hair, user r36): head-shell texels the old bob covered and the new hair no longer does (jaw sides, below the ears,
the nape) were painted hair by Meshy. Every head-shell texel outside the new cap's domain (its direction from the head centre beyond the
cap's boundary minus MARGIN deg) whose paint is hair-like (dark, red-brown) or that lies in that band takes the skin round it: the mean of
the K nearest (3D) clean skin texels, plus a third of a clean skin texel's fine detail. Args: <in png> <out png>   (project folder;
work/uv_tex2.npz positions, work/asm_frozen.npz cap parameters)"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; MARGIN = 1.0; NORMAL = len(sys.argv) > 3 and sys.argv[3] == 'normal'      # normal: flatten the band's normal map (hair strands)
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
A = np.load('work/asm_frozen.npz'); par = A['f4_param']; acomp = A['comp']; cap = (acomp == names.index('hood4')) & (A['f4_twin_v'] < 0)
K = par[cap, 2].max(); b = np.where(cap & (par[:, 2] == K))[0]; o = np.argsort(par[b, 1]); ab, rbv = par[b, 1][o], par[b, 0][o]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
POS = np.full((S, S, 3), np.nan)
for f in np.where((mat == 1) & (comp[tri[:, 0]] == names.index('head')))[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); bb = np.vstack([l, 1 - l.sum(0)]); ok = (bb >= -1e-4).all(0)
    if ok.any(): POS[gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)] = (bb[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1)
on = ~np.isnan(POS[..., 0]); ys, xs = np.where(on); P = POS[ys, xs]
C = np.array([0, 0, 0.665]); Pp = np.array([0, 0.5, 0.866]); Pp /= np.linalg.norm(Pp); E1 = np.array([1.0, 0, 0]); E2 = np.cross(Pp, E1)
d = P - C; d /= np.linalg.norm(d, axis=1, keepdims=True); rho = np.degrees(np.arccos(np.clip(d @ Pp, -1, 1))); al = np.degrees(np.arctan2(d @ E2, d @ E1))
rb_at = np.interp(al, np.r_[ab - 360, ab, ab + 360], np.r_[rbv, rbv, rbv]); outside = rho > rb_at - MARGIN
# the band the old bob covered (pass 2 cap, work/pre_pass3/asm_frozen.npz): every texel there is repainted, hair-like or not (r39: light strand
# remnants of the bob's paint read as stripes on the neck)
A0 = np.load('work/pre_pass3/asm_frozen.npz'); p0 = A0['f4_param']; c0 = (A0['comp'] == names.index('hood4')) & (A0['f4_twin_v'] < 0)
b0 = np.where(c0 & (p0[:, 2] == p0[c0, 2].max())); b0 = b0[0]; o0 = np.argsort(p0[b0, 1])
_a0, _r0 = p0[b0, 1][o0], p0[b0, 0][o0]
rb0 = np.interp(al, np.r_[_a0 - 360, _a0, _a0 + 360], np.r_[_r0, _r0, _r0])
band = outside & (rho < rb0 + 3.0)
c = im[ys, xs]; lum = c @ [0.2126, 0.7152, 0.0722]
hair = (lum < 0.40) & (c[:, 0] > c[:, 1] * 1.4)
face_front = (P[:, 1] < -0.07) & (P[:, 2] > 0.58)      # never the face itself
tgt = ((outside & hair) | band) & ~face_front
skin = outside & ~band & ~hair & (c[:, 0] > 0.55) & (c[:, 0] > c[:, 1]) & (P[:, 2] > 0.50)
skin &= ~tgt
if NORMAL:
    m = np.zeros((S, S), np.float32); m[ys[tgt], xs[tgt]] = 1; m = np.maximum(m, ni.gaussian_filter(m, 2.0) * 1.5).clip(0, 1) * on
    flat = np.array([0.5, 0.5, 1.0], np.float32); out = im * (1 - m[..., None]) + flat * m[..., None]
    Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST); print('EXPOSESKIN normal flattened', int(tgt.sum())); sys.exit(0)
kd = cKDTree(P[skin]); _, j = kd.query(P[tgt], k=80)
base = c[skin][j].mean(1)
blur = np.stack([ni.gaussian_filter(im[..., k], 3) for k in range(3)], -1); det = im - blur
_, j1 = kd.query(P[tgt], k=1); sk_idx = np.where(skin)[0][j1]
out = im.copy(); out[ys[tgt], xs[tgt]] = np.clip(base, 0, 1)      # smooth skin (the face round it is smooth)
# feather one texel round the repainted area
m = np.zeros((S, S), bool); m[ys[tgt], xs[tgt]] = True; ring = ni.binary_dilation(m, iterations=2) & ~m & on
sm = np.stack([ni.uniform_filter(out[..., k], 3) for k in range(3)], -1); out[ring] = 0.5 * out[ring] + 0.5 * sm[ring]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST); print('EXPOSESKIN texels', int(tgt.sum()), 'skin sources', int(skin.sum()))
