#!/usr/bin/env python3
"""Ether Knight region-mask fix (exists in the installed model): green cloth texels on the mantle and the tabard strips
lie outside the cloth channel (R), so tiers B and C show green patches beside purple/red cloth. Meshy also painted
cloth green on body faces under the tabard and mantle and on two chest-chain pieces at the collar, which peek out.
Texels inside the UV triangles (dilated 2 px) of the cloth pieces and of every face whose samples are over 25 %
unmasked cloth green, whose base colour is cloth green (hue 60-160 deg, saturation > 0.35, value > 0.15) and that no
channel covers, join channel R. Base colour unchanged.
-> work/regionmask_fixed.png"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); cen = v[f].mean(1)
order = np.argsort(-sizes)
cloth = [p for p in order[:12] if abs(cen[fl == p][:, 2].mean() - 1.5) < .05 and sizes[p] > 1000]
tabard = [p for p in order[:12] if 200 < sizes[p] < 300 and abs(cen[fl == p][:, 1].mean()) > .1 and abs(cen[fl == p][:, 2].mean() - .8) < .05]
base = Image.open('work/basecolor.png'); W, H = base.size
hsv = np.asarray(base.convert('HSV'), np.float32) / 255
h, s, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
mask = np.asarray(Image.open('work/regionmask.png').convert('RGBA')).copy()
green = (h > 60) & (h < 160) & (s > .35) & (val > .15) & (mask[..., 0] < 128) & (mask[..., 1] < 128)
B = np.random.default_rng(1).dirichlet((1, 1, 1), 24); su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
spill = green[y, x].mean(1) > .25
cover = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(cover)
for i in np.where(np.isin(fl, cloth + tabard) | spill)[0]:
    dr.polygon([(u * W, (1 - t) * H) for u, t in uv[i]], fill=255)
cover = np.asarray(cover.filter(ImageFilter.MaxFilter(5))) > 0
add = cover & green
mask[add, 0] = 255
Image.fromarray(mask, 'RGBA').save('work/regionmask_fixed.png')
print('MASKFIX cloth pieces', cloth, 'tabard', tabard, 'spill faces', int(spill.sum()), 'texels added', int(add.sum()), 'of', int(green.sum()), 'unmasked green')
