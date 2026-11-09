#!/usr/bin/env python3
"""Eyelids and nose from PeasantF1's approved paint (2026-11-02). The Codex repaint (eyes, mouth, hair, skin) was projected from the front,
but its lid and nose shapes do not sit on F1's lid and nose geometry (shared by PF4): a jagged dark lash line above a pale band over the
iris, and a brown blob on the nose tip (a dirty, doubled nose). F1's own paint was fitted to exactly this geometry over three user
reviews (nose fitted to the geometry's tip and underside, lids and the under-lid crescent fixed), so in two zones of the head shell every
texel takes F1's colour at the same point of the same asm triangle (read only from ../mm9_peasantf1_claude, its tier B head), carried as
luminance detail (F1's paint over its own local mean) on the repaint's local skin tone, blended in with soft 3D edges:
  lids: round each eye (x +-2.87 cm, 1.6136 m over the soles), the eyeballs themselves left with the repaint's iris;
  nose: the bridge below the brows, the tip, the alae and the underside.
Args: <F1 head png> <in png (projected repaint)> <out png> [zones: lids,nose] (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRCF1, SRC, OUT = sys.argv[1:4]; ZONES = (sys.argv[4] if len(sys.argv) > 4 else 'lids,nose').split(',')
F = np.load('../mm9_peasantf1_claude/work/uv.npz'); U = np.load('work/uv.npz'); A = np.load('work/asm_frozen.npz')
f1 = np.asarray(Image.open(SRCF1).convert('RGB'), np.float32); N1 = f1.shape[0]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32); S = im.shape[0]
names = [str(x) for x in U['names']]; kh = names.index('head'); Z0 = -0.9297
key1 = {}
for r in np.where(F['mat'] == 1)[0]: key1[tuple(sorted(F['orig'][F['tri'][r]]))] = r
# eyeball pieces: small connected pieces of the head part near the eyes
hf = np.where((U['mat'] == 1) & (U['comp'][U['tri'][:, 0]] == kh))[0]
ao = U['orig'][U['tri'][hf]]; par = {}
def fnd(a):
    while par.setdefault(a, a) != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in ao:
    r0 = fnd(int(t[0])); par[fnd(int(t[1]))] = r0; par[fnd(int(t[2]))] = r0
root = np.array([fnd(int(t[0])) for t in ao]); cnt = {r: int((root == r).sum()) for r in np.unique(root)}
C3 = A['co'][ao].mean(1)
eyeball = np.array([cnt[r] < 400 and 0.015 < abs(c[0]) < 0.05 and 1.58 < c[2] - Z0 < 1.65 for r, c in zip(root, C3)])
SRCI = np.zeros((S, S, 3), np.float32); POS = np.full((S, S, 3), np.nan); OK = np.zeros((S, S), bool); EB = np.zeros((S, S), bool)
for k, r in enumerate(hf):
    t = U['tri'][r]; o = U['orig'][t]; r1 = key1.get(tuple(sorted(o)))
    q = U['uv'][t] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l, 1 - l.sum(1)]; ins = (L3 >= -0.02).all(1)
    if not ins.any(): continue
    yy, xx = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)
    POS[yy, xx] = L3[ins] @ A['co'][o]
    if eyeball[k]: EB[yy, xx] = True; continue
    if r1 is None: continue
    t1 = F['tri'][r1]; o1 = F['orig'][t1]; perm = [int(np.where(o1 == v)[0][0]) for v in o]; p1 = L3[ins] @ F['uv'][t1][perm]
    px = np.clip((p1[:, 0] * N1).astype(int), 0, N1 - 1); py = np.clip(((1 - p1[:, 1]) * N1).astype(int), 0, N1 - 1)
    SRCI[yy, xx] = f1[py, px]; OK[yy, xx] = True
x, y, z = (np.nan_to_num(POS[..., i]) for i in range(3)); zs = z - Z0; cov = ~np.isnan(POS[..., 0])
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
ex = np.abs(np.abs(x) - 0.0287); ez = zs - 1.6136
lids = (1 - ramp(np.sqrt((ex / 0.019) ** 2 + (np.where(ez > 0, ez / 0.010, ez / 0.014)) ** 2), 0.75, 1.0)) * (y < -0.07)
nose = (1 - ramp(np.abs(x), 0.017, 0.024)) * ramp(zs, 1.560, 1.568) * (1 - ramp(zs, 1.632, 1.645)) * (y < -0.09)
out = im.copy(); rep = {}
LUMA = np.array([0.2126, 0.7152, 0.0722])
def lowpass(img, m, sig):
    wv = ni.gaussian_filter(m.astype(np.float32), sig)
    return np.stack([ni.gaussian_filter(img[..., c] * m, sig) for c in range(3)], -1) / np.maximum(wv, 1e-4)[..., None]
for nm, w in (('lids', lids), ('nose', nose)):
    if nm not in ZONES: continue
    w = w * OK * ~EB
    # F1's shading and features as a luminance ratio over its own local mean, on the repaint's local skin tone (dark outliers of the
    # repaint, its misplaced lashes and nose blob, left out of that tone)
    l1 = SRCI @ LUMA; m1 = lowpass(SRCI, OK & ~EB, 10.0) @ LUMA
    ratio = np.clip(l1 / np.maximum(m1, 1), 0.62 if nm == 'nose' else 0.25, 1.6)      # nose: soft nostrils (round dark dots read as a snout)
    li = im @ LUMA; zone = (w > 0.02) | ni.binary_dilation(w > 0.02, iterations=14)
    med = np.median(li[zone & cov]); clean = cov & ~EB & (li > med * 0.82)
    tone = lowpass(im, clean, 10.0)
    blend = tone * ratio[..., None]
    rep[nm] = round(float(np.median(ratio[w > 0.5])), 3) if (w > 0.5).any() else None
    out = out * (1 - w[..., None]) + blend * w[..., None]
Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(OUT); print('F1LIDSNOSE median ratio', rep)
