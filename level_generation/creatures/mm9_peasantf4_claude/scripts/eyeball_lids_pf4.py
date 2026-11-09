#!/usr/bin/env python3
"""Lids painted on the eyeballs (after mm9_wyrde_claude/scripts/face_fix_wy.py; orchestrator review 2026-11-02: large staring eyes, whites
above and below the iris). The front projection cannot reach the parts of the eyeball sphere that the lid geometry hides from the front, so
those kept Meshy's white sclera, and from any other angle the eyes stared. Every eyeball texel above UP x r over the ball centre or below
LO x r under it takes the lid skin (the skin just above the socket), with a soft dark lash line along the upper lid edge; the lid
geometry's own edge (head texels within 2.5 mm of the ball, above its centre) loses the repaint's jagged dark lash marks (luminance below
70 % of the lid skin -> the lid skin). Args: <in png> <out png> [UP] [LO] (project folder; positions from work/uv_tex2.npz)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; UP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.42; LO = float(sys.argv[4]) if len(sys.argv) > 4 else -0.55
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
kh = names.index('head'); EC = np.array([0.0288, -0.0953, 0.6839])
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32); S = im.shape[0]
# eyeball faces: small welded head pieces at the eyes
hf = np.where((mat == 1) & (comp[tri[:, 0]] == kh))[0]
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); par = np.arange(inv.max() + 1)
def fnd(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in tri[hf]:
    r = fnd(inv[t[0]]); par[fnd(inv[t[1]])] = r; par[fnd(inv[t[2]])] = r
root = np.array([fnd(inv[t[0]]) for t in tri[hf]]); cnt = np.bincount(root, minlength=len(par))
isball = cnt[root] < 600
POS = np.full((S, S, 3), np.nan, np.float32); BALL = np.zeros((S, S), bool)
for k, f in enumerate(hf):
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l, 1 - l.sum(1)]; ins = (L3 >= -0.01).all(1)
    yy, xx = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)
    POS[yy, xx] = L3[ins] @ co[tri[f]]; BALL[yy, xx] = isball[k]
cov = ~np.isnan(POS[..., 0]); P = np.nan_to_num(POS)
out = im.copy()
for sx in (1, -1):
    c = EC * [sx, 1, 1]; q = P - c; d = np.linalg.norm(q, axis=-1)
    ball = BALL & cov & (d < 0.016) & (q[..., 1] < 0.004)
    r = np.linalg.norm(q[..., [0, 2]], axis=-1)
    # the lid skin: head texels 4-8 mm above the ball centre, in front, not on the ball
    above = cov & ~BALL & (q[..., 2] > 0.012) & (q[..., 2] < 0.018) & (np.abs(q[..., 0]) < 0.008) & (q[..., 1] < 0.0)
    lk = np.median(im[above], 0) if above.sum() > 20 else np.array([200.0, 130, 95])
    # r21: the lid on the ball takes the lid margin's own tone (head texels within 3.5 mm of the ball, above its centre) when that is darker:
    # B's skin above the socket was lighter than her shaded lid and drew a pale crescent over each eye
    rim = cov & ~BALL & (d < 0.0118 + 0.0035) & (q[..., 2] > 0.002) & (q[..., 1] < 0.0)
    if rim.sum() > 20:
        lm = np.median(im[rim], 0) * 0.95
        if lm.sum() < lk.sum(): lk = lm
    zr = q[..., 2] / 0.0118
    up = np.clip((zr - UP) / 0.08, 0, 1); lo = np.clip((LO - zr) / 0.08, 0, 1)
    lash = np.clip(1 - np.abs(zr - UP) / 0.07, 0, 1)
    w = np.maximum(up, lo) * ball; wl = lash * ball * 0.65
    out = np.where(ball[..., None], out * (1 - w[..., None]) + lk * w[..., None], out)
    out = np.where(ball[..., None], out * (1 - wl[..., None]) + np.array([45.0, 30, 25]) * wl[..., None], out)
    # the lid geometry's edge above the ball: the repaint's jagged dark lash marks -> lid skin
    edge = cov & ~BALL & (d < 0.0118 + 0.0035) & (q[..., 2] > 0.002) & (q[..., 1] < 0.0)
    lum = out @ np.array([0.2126, 0.7152, 0.0722]); lkl = float(lk @ np.array([0.2126, 0.7152, 0.0722]))
    # r22: the jagged dark line was the geometry lid's margin (F1's low-poly lid edge) painted with the repaint's lashes, above the smooth
    # painted lid: every margin texel darker than the lid tone takes it (soft, by darkness), so the ball's smooth lash line is the margin
    wdk = np.clip((0.97 * lkl - lum) / (0.25 * lkl), 0, 1) * edge
    wdk = ni.gaussian_filter(wdk, 0.7) * edge
    out = out * (1 - wdk[..., None]) + lk * 0.95 * wdk[..., None]
    dk = wdk > 0.5
    print('LIDS', sx, 'ball texels', int(ball.sum()), 'lid', int((w > 0.5).sum()), 'lid skin', np.round(lk).tolist(), 'edge marks', int(dk.sum()))
Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(DST)
