#!/usr/bin/env python3
"""Pass 7: the kept braid (PeasantF2's tube on textures/fre_hair_base.png) toned to the new head's hair: per-channel mean and spread of the
braid's texels matched to the new hair's visible texels (outer hair faces of work/nh/head_uv.npz on textures/nh_head_base.png), in linear-ish
0-1 RGB. Writes textures/nh_braid_base.png (the FreHair base). Project folder."""
import numpy as np
from PIL import Image, ImageDraw
def mask(uv, tri, size):
    cv = Image.new('L', (size, size), 0); dr = ImageDraw.Draw(cv)
    for t in tri: dr.polygon([(float(uv[v, 0] * size), float((1 - uv[v, 1]) * size)) for v in t], fill=255)
    return np.asarray(cv) > 0
H = np.load('work/nh/head_uv.npz'); keep = (H['fpiece'] == 1) & ~H['hidden']
hb = np.asarray(Image.open('textures/nh_head_base.png').convert('RGB'), np.float32) / 255
hm = mask(H['uv'], H['tri'][keep], hb.shape[0]); hp = hb[hm]
R = np.load('work/uv_tex2.npz'); A = np.load('work/asm_frozen.npz'); names = [str(x) for x in R['names']]
tube = (R['comp'] == names.index('hair2')) & A['hair2_tube'][R['orig']]
bt = R['tri'][tube[R['tri']].all(1)]
src = Image.open('textures/fre_hair_base.png').convert('RGB'); bb = np.asarray(src, np.float32) / 255
bm = mask(R['uv'], bt, bb.shape[0]); bp = bb[bm]
out = (bb - bp.mean(0)) / np.maximum(bp.std(0), 1e-3) * hp.std(0) * 0.6 + hp.mean(0) * 0.92
# round 2: MM9's braid is bound with gold: GOLD_Z bands (r72 tube heights, each GOLD_H tall) painted on the braid's texels, the plait's
# own light/dark kept as shading (luminance relative to its mean), soft 1-px edges
S = bb.shape[0]; zmap = np.full((S, S), np.nan, np.float32); co = R['co']
for t in bt:
    p = np.c_[R['uv'][t, 0] * S, (1 - R['uv'][t, 1]) * S]
    x0, y0 = np.maximum(np.floor(p.min(0)).astype(int) - 1, 0); x1, y1 = np.minimum(np.ceil(p.max(0)).astype(int) + 1, S - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); q = np.c_[xs.ravel() + .5, ys.ravel() + .5]
    T = np.array([[p[1, 0] - p[0, 0], p[2, 0] - p[0, 0]], [p[1, 1] - p[0, 1], p[2, 1] - p[0, 1]]])
    if abs(np.linalg.det(T)) < 1e-9: continue
    b = np.linalg.solve(T, (q - p[0]).T).T; l = np.c_[1 - b.sum(1), b]; ok = (l > -0.05).all(1)
    zmap[ys.ravel()[ok], xs.ravel()[ok]] = l[ok] @ co[t][:, 2]
import os
GZ = [float(x) for x in os.environ.get('GOLD_Z', '0.578,0.468,0.372').split(',')]; GH = float(os.environ.get('GOLD_H', '0.011'))
zz = np.nan_to_num(zmap, nan=-1); band = np.zeros((S, S), np.float32)
for z0 in GZ: band = np.maximum(band, np.clip((GH / 2 - np.abs(zz - z0)) / 0.002, 0, 1))
from scipy import ndimage as ni
band = ni.gaussian_filter(band, 0.7)[..., None]
lum = out.mean(2, keepdims=True); rel = np.clip(lum / max(float(lum[bm].mean()), 1e-3), 0.55, 1.5) ** 0.6
gold = np.array([0.86, 0.64, 0.24], np.float32) * rel
out = out * (1 - band) + gold * band
print('BRAID gold bands at z', GZ, 'texels', int((band[..., 0] > 0.5).sum()))
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save('textures/nh_braid_base.png')
print('BRAID tone: braid mean', (bp.mean(0) * 255).round(0), '-> hair mean', (hp.mean(0) * 255).round(0), 'texels', int(bm.sum()), int(hm.sum()))
