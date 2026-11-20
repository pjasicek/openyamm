#!/usr/bin/env python3
"""Paint fixes on the composed maps (project folder; work/uv.npz layout, never re-laid):
- BODY: the robe's inner cap and the neck tube -> near-black cloth (Meshy's detail kept at low contrast): they read as the shadow inside
  the robe and the hood, as MM9's black neck.
- HEAD: the staff's charts (not in the head upload, so only padding there) -> aged bone from the skull's own cranium texels: their colour
  statistics, a fine grain and soft stains (UV-space noise), darker toward the knuckle swellings by AO later.
- EMISSION: textures/sk_head_glow.png, the ember eye spheres (head label 3) as a grey mask scaled by the paint's red-orange brightness.
Args: <body raw png> <head raw png> -> textures/sk_body_fix.png, sk_head_fix.png, sk_head_glow.png"""
import sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from scipy import ndimage
D = np.load('work/uv.npz'); tri, uv, mat, comp = D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
hl = D['head_label']
def mask(faces, S):
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
    for t in faces: dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
    return np.asarray(im) > 0
fc = comp[tri[:, 0]]
body = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32); SB = body.shape[0]
dark = mask(tri[(mat == 0) & np.isin(fc, [names.index('cap'), names.index('cowl')])], SB)
dark = ndimage.binary_dilation(dark, iterations=2)
lum = body.mean(2, keepdims=True); detail = lum / max(float(np.median(lum[dark])), 1)
base = np.array([22, 21, 24], np.float32)
body[dark] = (base * (0.75 + 0.25 * detail[dark]))
# the robe's collar inside the hood opening: Meshy painted the masters' necklace there as pale streaks (the necklace is geometry now)
A = np.load('work/asm4.npz') if Path('work/asm4.npz').exists() else np.load('work/asm2.npz')
fcen = A['co'][D['orig'][tri]].mean(1)
col = (mat == 0) & (fc == names.index('robe')) & (np.abs(fcen[:, 0]) < 0.10) & (fcen[:, 2] > 0.36) & (fcen[:, 2] < 0.56) & (fcen[:, 1] < 0.02)
cm = mask(tri[col], SB); lum2 = body.mean(2)
pale = cm & (lum2 > 45)
body[pale] = base * (0.8 + 0.2 * (lum2[pale, None] / 255.0))
print('COLLAR pale texels', int(pale.sum()), 'of', int(cm.sum()))
# the rust tabard toward MM9's darker brown-rust (ours read bright orange in the viewer's light): robe texels by hue/saturation, soft
rm = mask(tri[(mat == 0) & (fc == names.index('robe'))], SB)
p = body / 255.0; mx = p.max(2); mn = p.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.degrees(np.arctan2(np.sqrt(3) * (p[..., 1] - p[..., 2]), 2 * p[..., 0] - p[..., 1] - p[..., 2])) % 360
wt = rm * np.clip((sat - 0.30) / 0.15, 0, 1) * ((hue < 45) | (hue > 345))
g = p.mean(2, keepdims=True); tone = (g + (p - g) * 0.88) * np.array([0.84, 0.84, 0.92])
body = (p * (1 - wt[..., None]) + tone * wt[..., None]) * 255
print('TABARD toned texels', int((wt > 0.5).sum()))
# the masters' fang collar painted as white leaf-shaped blotches on the tabard's shoulders (the necklace is geometry now): pale,
# unsaturated robe texels on the shoulders are refilled from the nearest cloth texel of the same region, with the cloth's grain kept
sh_ = (mat == 0) & (fc == names.index('robe')) & (fcen[:, 2] > 0.36) & (np.abs(fcen[:, 0]) > 0.07)
sm = mask(tri[sh_], SB); p = body / 255.0; lum3 = p.mean(2); mx = p.max(2); sat3 = (mx - p.min(2)) / np.maximum(mx, 1e-6)
pale2 = sm & (lum3 > 0.38) & (sat3 < 0.45)
pale2 = ndimage.binary_dilation(pale2, iterations=2) & sm
src = sm & ~pale2
idx = ndimage.distance_transform_edt(~src, return_distances=False, return_indices=True)
fill = body[idx[0], idx[1]]
g0 = ndimage.gaussian_filter(lum3, 1.0); fine = (lum3 - g0)[..., None] * 255 * 0.3
body[pale2] = (fill + fine)[pale2]
print('SHOULDER pale texels refilled', int(pale2.sum()))
Image.fromarray(body.clip(0, 255).astype('u1')).save('textures/sk_body_fix.png')
head = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32); SH = head.shape[0]
staff = ndimage.binary_dilation(mask(tri[(mat == 1) & (fc == names.index('staff'))], SH), iterations=3)
cran = mask(tri[(mat == 1) & (fc == names.index('head')) & (hl[tri[:, 0]] == 0)], SH)
ref = head[ndimage.binary_erosion(cran, iterations=3)]; mu = np.median(ref, 0); sd = ref.std(0)
rng = np.random.default_rng(3); H, W = SH, SH
def noise(scale, amp):
    n = rng.standard_normal((H // scale + 2, W // scale + 2)).astype(np.float32)
    return np.asarray(Image.fromarray(n).resize((W, H), Image.BICUBIC)) * amp
grain = noise(1, 0.035) + noise(3, 0.05) + noise(12, 0.07) + noise(40, 0.08)
stain = np.clip(noise(24, 1.0), 0, None) * 0.18
col = mu[None, None, :] * (1 + grain[..., None]) * (1 - stain[..., None] * np.array([0.6, 0.9, 1.25])[None, None, :])
head[staff] = (col[staff] * 0.92)
Image.fromarray(head.clip(0, 255).astype('u1')).save('textures/sk_head_fix.png')
eyes = mask(tri[(mat == 1) & (fc == names.index('head')) & (hl[tri[:, 0]] == 3)], SH)
h0 = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32) / 255
heat = np.clip((h0[..., 0] - 0.5 * h0[..., 2] - 0.15) / 0.6, 0, 1)
glow = np.where(eyes, 0.35 + 0.65 * heat, 0)
glow = ndimage.gaussian_filter(glow, 0.8) * ndimage.binary_dilation(eyes, iterations=2)
Image.fromarray((glow.clip(0, 1) * 255).astype('u1')).save('textures/sk_head_glow.png')
print('FIX dark texels', int(dark.sum()), 'staff texels', int(staff.sum()), 'bone ref', mu.round(1), 'eye texels', int(eyes.sum()))
