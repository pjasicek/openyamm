#!/usr/bin/env python3
"""Lizardman Warrior region-mask fix (exists in the installed model): Meshy painted the torso under the mantle green
(neck, collar bones, upper back: 284 faces of the torso piece), outside the mantle channel (R), so tiers B and C show
green patches where the torso shows beside and through the blue / red mantle. Texels inside the UV triangles (dilated
2 px) of every face whose samples are over 25 % unmasked green, and whose base colour is green (hue 60-160 deg,
saturation > 0.3, value > 0.12) and no channel covers, join channel R. Base colour unchanged.
-> work/regionmask_fixed.png"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
d = np.load('work/mesh_in.npz'); f = d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
base = Image.open('work/basecolor.png'); W, H = base.size
hsv = np.asarray(base.convert('HSV'), np.float32) / 255
h, s, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
mask = np.asarray(Image.open('work/regionmask.png').convert('RGBA')).copy()
green = (h > 60) & (h < 160) & (s > .3) & (val > .12) & (mask[..., :3].max(-1) < 128)
B = np.random.default_rng(1).dirichlet((1, 1, 1), 24); su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
spill = green[y, x].mean(1) > .25
cover = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(cover)
for i in np.where(spill)[0]:
    dr.polygon([(u * W, (1 - t) * H) for u, t in uv[i]], fill=255)
cover = np.asarray(cover.filter(ImageFilter.MaxFilter(5))) > 0
add = cover & green
mask[add, 0] = 255
Image.fromarray(mask, 'RGBA').save('work/regionmask_fixed.png')
np.save('work/mask_spill_faces.npy', spill)
print('MASKFIX spill faces', int(spill.sum()), 'texels added', int(add.sum()), 'of', int(green.sum()), 'unmasked green')
