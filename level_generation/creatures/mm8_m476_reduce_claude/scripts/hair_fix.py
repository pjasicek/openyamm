#!/usr/bin/env python3
"""Hair-lock flecks (Meshy painted skin-coloured specks on the black hair locks; the native sprites show a black crest):
in the shared base-colour atlas, texels covered only by hair-lock triangles (small head pieces behind the face, not the
eyes) whose linear luminance is over REA_HAIR_L (default 0.04) take the hair's median colour, scaled by their rank
for a little variation; texels any other face also uses are left. The gutter within 2 px of the hair islands follows.
Writes work/basecolor_hairfix.png and work/hairfix_mask.png. Usage: hair_fix.py"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
piece = np.load('work/piece.npy'); sizes = np.bincount(piece); c = v[f].mean(1)
hair = (sizes[piece] <= 160) & (c[:, 1] > -.12) & (c[:, 2] > 1.4) & (np.abs(c[:, 0]) < .14) & ~np.isin(piece, [9, 20])


def raster(sel):
    im = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(im)
    for t in uv[sel]:
        dr.polygon([((u % 1) * W, (1 - vv % 1) * H) for u, vv in t], fill=255)
    return np.asarray(im) > 0


hm, om = raster(hair), raster(~hair)
own = hm & ~ndimage.binary_dilation(om, iterations=1)
zone = (ndimage.binary_dilation(own, iterations=2) & ~om) | own
L = lin(img) @ np.array([.2126, .7152, .0722])
dark = own & (L <= float(os.environ.get('REA_HAIR_L', '0.04')))
med = np.median(lin(img)[dark], 0)
fix = zone & (L > float(os.environ.get('REA_HAIR_L', '0.04')))
rank = (L[fix] - L[fix].min()) / max(np.ptp(L[fix]), 1e-6)
out = lin(img).copy(); out[fix] = med[None] * (0.8 + 0.5 * rank)[:, None]
Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save('work/basecolor_hairfix.png')
Image.fromarray((fix * 255).astype(np.uint8)).save('work/hairfix_mask.png')
print('HAIR faces', int(hair.sum()), 'own texels', int(own.sum()), 'shared texels', int((hm & om).sum()),
      'fixed', int(fix.sum()), 'hair median', np.round(med, 4))
