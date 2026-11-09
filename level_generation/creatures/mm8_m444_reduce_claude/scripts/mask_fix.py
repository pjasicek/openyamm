#!/usr/bin/env python3
"""Smuggler region-mask fix (exists in the installed model): green cloth texels outside the cloth channel (R), so tiers
B and C (blue, burgundy) show green-teal patches: at the collar beside the bandolier, along the collar's lower edge,
and on surfaces painted cloth green under the cuffs, the belt and the trouser hems. Texels that are cloth green (hue
100-190 deg, saturation > 0.3, value > 0.12) join channel R when they lie (a) inside the UV triangles, dilated 2 px,
of faces whose samples are over 20 % unmasked green, or (b) on a used texel within 4 px of the masked cloth (the
anti-aliased mask edge). Base colour unchanged. -> work/regionmask_fixed.png"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
d = np.load('work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2)
base = Image.open('work/basecolor.png'); W, H = base.size
hsv = np.asarray(base.convert('HSV'), np.float32) / 255
h, s, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
mask = np.asarray(Image.open('work/regionmask.png').convert('RGBA')).copy()
green = (h > 100) & (h < 190) & (s > .3) & (val > .12) & (mask[..., 0] < 128)
B = np.random.default_rng(1).dirichlet((1, 1, 1), 24); su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip(su[..., 0] * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1]) * H, 0, H - 1).astype(int)
spill = green[y, x].mean(1) > .2


def raster(faces):
    im = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(im)
    for t in uv[faces]:
        dr.polygon([(u * W, (1 - v) * H) for u, v in t], fill=255)
    return im


cover = np.asarray(raster(np.where(spill)[0]).filter(ImageFilter.MaxFilter(5))) > 0
used = np.asarray(raster(np.arange(len(uv)))) > 0
near = np.asarray(Image.fromarray(((mask[..., 0] >= 128) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
add = green & (cover | (used & near))
mask[add, 0] = 255
Image.fromarray(mask, 'RGBA').save('work/regionmask_fixed.png')
print('MASKFIX spill faces', int(spill.sum()), 'texels added', int(add.sum()), '(faces', int((green & cover).sum()),
      ', mask edge', int((green & used & near & ~cover).sum()), ') of', int(green.sum()), 'unmasked green')
