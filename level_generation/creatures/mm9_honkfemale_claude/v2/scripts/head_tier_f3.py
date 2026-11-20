#!/usr/bin/env python3
"""Elder head (MM9 skin HONKF3) from the tier A head set by colour alone. The Codex repaint would not project cleanly on this head (a wider face
than the mesh: double lips at every view seam), so the geometry-true paint of tier A stays and only its colours change: warmer skin, dark brows,
brown eyes, redder lips, dark brown hair for the veil, side locks and braids, blue-grey linen on the neck. Parts by loose component.
Usage: head_tier_f3.py <A png> <out png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
src, dst = sys.argv[1:3]
S = 2048
D = np.load('v2/work/uv_head.npz')
base = np.asarray(Image.open(src).convert('RGB'), np.float32)
H = D['head'].astype(bool) & ~D['hand'].astype(bool)
comps = np.unique(D['comp'][H])
info = {c: (int((D['comp'] == c).sum()), D['xyz'][D['comp'] == c].reshape(-1, 3).min(0).round(3), D['xyz'][D['comp'] == c].reshape(-1, 3).max(0).round(3)) for c in comps}
for c, v in info.items():
    print(c, v[0], v[1], v[2])
shell = max(comps, key=lambda c: (info[c][0] if info[c][1][2] < 0.6 else 0))
hairish = [c for c in comps if c != shell and info[c][2][2] < 0.8 and info[c][2][2] - info[c][1][2] > 0.15]   # veil, side locks, braids
print('shell', shell, 'hair', hairish)
def foot(cs):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    for uv in D['uv'][np.isin(D['comp'], cs) & H]:
        d.polygon([(u * S, (1 - v) * S) for u, v in uv], fill=255)
    return np.asarray(im) > 0
Z = np.zeros((S, S), np.float32); XS = np.zeros((S, S), np.float32)
im = None
for uv, x in zip(D['uv'][D['comp'] == shell], D['xyz'][D['comp'] == shell]):
    p = uv * S; p = np.stack([p[:, 0], S - p[:, 1]], 1)
    lo = np.floor(p.min(0)).astype(int); hi = np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if not xs.size: continue
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9: continue
    st = (np.stack([xs + .5, ys + .5], -1) - p[0]) @ np.linalg.inv(T).T
    ins = (st[..., 0] >= 0) & (st[..., 1] >= 0) & (st.sum(-1) <= 1)
    w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
    Z[ys[ins], xs[ins]] = w[ins] @ x[:, 2]; XS[ys[ins], xs[ins]] = w[ins] @ x[:, 0]
hair = ndimage.binary_dilation(foot(hairish), iterations=3)
sh = foot([shell])
out = base.copy()
lum = base @ np.array([.299, .587, .114])
r, g, b = base[..., 0], base[..., 1], base[..., 2]
# skin: warmer, deeper
skin = sh & (Z > 0.53)
out[skin] = np.clip(base[skin] * np.array([0.93, 0.80, 0.70]), 0, 255)
# brows and lashes: everything much darker than the local skin
blur = ndimage.gaussian_filter(lum, 14)
dark = skin & (lum < blur - 22)
sd = ndimage.gaussian_filter(dark.astype(np.float32), 1.0)[..., None]
out = out * (1 - sd * .55) + np.array([38, 26, 22.]) * sd * .55
# irises: cool texels of the shell and the eye parts become brown
eye = (base[..., 2] > base[..., 0] * 1.02) & (lum > 50) & (lum < 190) & sh
eye |= foot([c for c in comps if info[c][2][2] - info[c][1][2] < 0.06 and info[c][1][2] > 0.62 and info[c][2][2] < 0.75 and info[c][0] < 200]) & (base[..., 2] > base[..., 0] * 1.02)
ey = ndimage.gaussian_filter(eye.astype(np.float32), .8)[..., None]
out = out * (1 - ey) + (np.array([74, 46, 30.]) * (lum[..., None] / 120).clip(.4, 1.3)) * ey
# lips
lip = skin & (Z > 0.655) & (Z < 0.685) & (np.abs(XS + 0.01) < 0.032) & (r > g * 1.75) & (r > b * 1.7) & (lum > 60)
lp = ndimage.gaussian_filter(lip.astype(np.float32), 1.2)[..., None]
out = out * (1 - lp * .6) + np.clip(base * np.array([.82, .52, .5]), 0, 255) * lp * .6
# hair
hl = lum[hair]; lo, hi = np.percentile(hl, 4), np.percentile(hl, 98)
t = np.clip((lum - lo) / (hi - lo), 0, 1)[..., None]
brown = np.array([38, 26, 20.]) * (1 - t) + np.array([98, 72, 52.]) * t
out[hair] = brown[hair]
# neck: blue-grey linen
nk = sh & (Z < 0.55)
fade = np.clip((0.55 - Z) / 0.012, 0, 1)[..., None]
fine = (lum - ndimage.gaussian_filter(lum, 6))[..., None]
lin = np.array([70, 88, 112.]) + fine * 1.5
out = np.where(nk[..., None], out * (1 - fade) + lin * fade, out)
pad = ~(sh | hair | foot(list(comps)))
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(dst)
print('TIERF3 done')
