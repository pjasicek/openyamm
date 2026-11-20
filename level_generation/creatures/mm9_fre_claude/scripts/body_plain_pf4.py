#!/usr/bin/env python3
"""Plain sleeves and bodice (orchestrator review 2026-11-02: MM9's F4 has a plain fitted bodice, long plain bell sleeves and a small
embroidered neckline; ours had F1's lace bands round the upper arms and a laced bust from the masters / F1's lacing bumps). In two zones
of the body set every texel that is not the dress's green cloth takes the green round it (normalised convolution of the green texels,
6 px) with half of its own fine detail: the arms (dress faces beyond |x| 12 cm and the sleeve tubes) and the bodice front below the
neckline placket (|x| < 7 cm, 1.14-1.355 m over the soles, the front half). The neckline embroidery, the belt, apron, skirt and skin stay.
Args: <in png> <out png> (project folder; rest positions from work/uv.npz)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]
D = np.load('work/uv.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
Z0 = -0.9297
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
PART = np.full((S, S), -1, np.int16); POS = np.zeros((S, S, 3), np.float32)
for f in np.where(mat == 0)[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l, 1 - l.sum(1)]; ins = (L3 >= -0.01).all(1)
    yy, xx = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)
    PART[yy, xx] = comp[tri[f][0]]; POS[yy, xx] = L3[ins] @ co[tri[f]]
x, y, zs = POS[..., 0], POS[..., 1], POS[..., 2] - Z0
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255
h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
kd, ks = names.index('dress'), names.index('sleeve4')
green = np.isin(PART, [kd, ks]) & (h > 50) & (h < 160) & (s > 0.15)
arms = ((PART == kd) & (np.abs(x) > 0.12)) | (PART == ks)
bust = (PART == kd) & (np.abs(x) < 0.07) & (zs > 1.14) & (zs < 1.355) & (y < -0.02)
zone = (arms | bust) & ~green
# r22: the laced bust's shadows and eyelets are green but dark: bust texels under 0.85 of the local mean (8 px) join the zone
_l = im @ np.array([0.2126, 0.7152, 0.0722]); _lo = ni.gaussian_filter(_l, 8.0)
zone |= bust & (_l < 0.85 * _lo)
# r25: the lacing column itself (|x| < 3 cm below the neckline placket) is repainted whole from the cloth either side, keeping the weave
col = bust & (np.abs(x) < 0.03) & (zs < 1.335)
zone |= col
src = green & ~ni.binary_dilation(zone, iterations=2)
wsum = ni.gaussian_filter(src.astype(np.float32), 6.0)
fill = np.stack([ni.gaussian_filter(im[..., c] * src, 6.0) for c in range(3)], -1) / np.maximum(wsum, 1e-4)[..., None]
far = wsum < 0.02
if far.any(): fill[far] = np.median(im[green], 0)
lum = im @ np.array([0.2126, 0.7152, 0.0722]); det = lum - ni.gaussian_filter(lum, 1.5)
new = np.clip(fill + det[..., None] * 0.5, 0, 1)
w = np.clip(ni.gaussian_filter(zone.astype(np.float32), 1.0) * 1.5, 0, 1) * (arms | bust)
new = np.clip(fill + det[..., None] * 0.15, 0, 1)
wc = np.clip((0.03 - np.abs(x)) / 0.008, 0, 1) * np.clip((1.335 - zs) / 0.01, 0, 1) * bust
mgb = np.median(im[bust & green & ~ni.binary_dilation(col, iterations=4)], 0)      # r28: the column's own UV islands (the lacing bumps) have no cloth round them in the atlas
# r29: the bodice paint has a lighter front panel; the column takes the cloth beside it (|x| 3.2-6 cm) at its own height (1 cm bins)
side = (PART == kd) & green & (np.abs(x) > 0.032) & (np.abs(x) < 0.06) & (y < -0.02) & ~zone
zb = np.arange(1.05, 1.35, 0.01); cb = []
for z0 in zb:
    m = side & (np.abs(zs - z0) < 0.012); cb.append(np.median(im[m], 0) if m.sum() > 30 else mgb)
cb = ni.uniform_filter1d(np.array(cb), 3, axis=0)
ccol = np.stack([np.interp(zs, zb, cb[:, k]) for k in range(3)], -1)
new = np.where((wc > 0)[..., None], np.clip(ccol + det[..., None] * 0.2, 0, 1), new); w = np.maximum(w * (wc == 0), wc)
out = im * (1 - w[..., None]) + new * w[..., None]
# the arms one even cloth: the bodice front's median green, a +-8 % share of the local brightness, a little weave (the puff and the tube
# were painted from different views: a darker band where the tube starts)
bod = (PART == kd) & (np.abs(x) < 0.08) & (zs > 1.15) & (zs < 1.40) & green
mg = np.median(out[bod], 0); lo = ni.gaussian_filter(out @ np.array([0.2126, 0.7152, 0.0722]), 8.0); ml = float(mg @ np.array([0.2126, 0.7152, 0.0722]))
dev = np.clip(lo / ml - 1, -0.08, 0.08)
lo2 = out @ np.array([0.2126, 0.7152, 0.0722]); det2 = lo2 - ni.gaussian_filter(lo2, 1.5)
even = np.clip(mg[None, None] * (1 + dev[..., None]) + det2[..., None] * 0.3, 0, 1)
wa = np.clip(ni.gaussian_filter(arms.astype(np.float32), 1.0), 0, 1) * arms
out = out * (1 - wa[..., None]) + even * wa[..., None]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
# r24: Meshy's normal map kept the lacing and the lace bands in relief (dark X marks down the bodice in the viewer): the same zones (the
# whole bust box and the arms) are flattened 85 % in a copy, textures/pf_body_normal_plain.png (finish_pf.py uses it when present)
NM = np.asarray(Image.open('textures/pf_body_normal.png').convert('RGB'), np.float32) / 255; SN = NM.shape[0]
zf = np.clip(ni.gaussian_filter((bust | arms).astype(np.float32), 2.0), 0, 1)
zf = np.asarray(Image.fromarray((zf * 255).astype('u1')).resize((SN, SN), Image.BILINEAR), np.float32)[..., None] / 255 * 0.85
NP = NM * (1 - zf) + np.array([0.5, 0.5, 1.0]) * zf; v = NP * 2 - 1; v /= np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6)
Image.fromarray(((v + 1) / 2 * 255 + .5).astype('u1')).save('textures/pf_body_normal_plain.png')
print('BODYPLAIN arms', int((zone & arms).sum()), 'bust', int((zone & bust).sum()), 'texels recoloured')
# r28: the AO bake kept the lacing's occlusion (dark chevrons down the bodice whatever the paint): in a copy of the AO the lacing column
# takes the AO either side of it (normalised convolution, 6 px), textures/pf_ao_2k_plain.png (finish_pf.py uses it when present)
AO = np.asarray(Image.open('textures/pf_ao_2k.png').convert('L'), np.float32); SA = AO.shape[0]
def rs(m): return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype('u1')).resize((SA, SA), Image.BILINEAR), np.float32) / 255
wca = rs(wc); srca = rs((bust & ~ni.binary_dilation(col, iterations=6)).astype(np.float32)) > 0.5
fa = ni.gaussian_filter(AO * srca, 6.0) / np.maximum(ni.gaussian_filter(srca.astype(np.float32), 6.0), 1e-4)
fa = np.where(ni.gaussian_filter(srca.astype(np.float32), 6.0) < 0.02, np.median(AO[srca]) if srca.any() else 255, fa)
AO2 = AO * (1 - wca) + fa * wca
Image.fromarray(np.clip(AO2 + .5, 0, 255).astype('u1')).save('textures/pf_ao_2k_plain.png'); print('AO lacing column flattened', int((wca > 0.5).sum()))
