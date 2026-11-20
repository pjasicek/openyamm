#!/usr/bin/env python3
"""Igrid body colour fixes by 3D position (work/texel_pos.npy), textures/wo_body_final.png -> textures/wo_body_tone.png:
1. NECKLINE: Meshy painted the robe's neckline inside the hood opening (beside the jaw, z 0.36-0.50) as pale cream cloth (the masters'
   pearl choker smeared): pale low-saturation texels there take the hood's dark cloth by their own luminance detail (MM9: a dark collar).
2. HANDS: Meshy painted the MPFB hands with a scaly net pattern: one clean skin colour (the face's cheek skin of the head paint, x HGAIN)
   times the paint's broad luminance only (Gaussian 2.5 px: the net goes, knuckles and nail edges stay soft), within +-15 %.
Project folder."""
import numpy as np
from PIL import Image
from scipy import ndimage as ni
im = np.asarray(Image.open('textures/wo_body_final.png').convert('RGB'), np.float32) / 255
P = np.load('work/texel_pos.npy'); part = np.load('work/texel_part.npy')
X, Y, Z = (np.nan_to_num(P[..., i]) for i in range(3))
LUMA = np.array([0.2126, 0.7152, 0.0722]); L = im @ LUMA
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255
zone = (part == 0) & (np.abs(X) < 0.15) & (Z > 0.36) & (Z < 0.52) & (Y < -0.10)
pale = zone & (hsv[..., 1] < 0.35) & (L > 0.30)
pale = ni.binary_dilation(pale, iterations=2) & zone
ref = (part == 0) & (np.abs(X) < 0.2) & (Z > 0.5) & (Z < 0.7) & (Y > 0.0)        # hood cloth behind the head
hood = np.median(im[ref], 0); print('hood colour', (hood * 255).round(0))
det = L - ni.gaussian_filter(L, 4)
col = np.clip(hood * 0.8 + det[..., None] * 0.6, 0, 1)
w = np.clip(ni.gaussian_filter(pale.astype(np.float32), 1.2) * 1.4, 0, 1) * zone
out = im * (1 - w[..., None]) + col * w[..., None]
# 2. hands
names = [str(x) for x in np.load('work/asm_tw.npz')['names']]; HN = names.index('hands')
hm_ = part == HN
head = np.asarray(Image.open('textures/wo_head_final.png').convert('RGB'), np.float32) / 255
HP = np.load('work/texel_pos_head.npy'); hpart = np.load('work/texel_part_head.npy'); hx, hy, hz = (np.nan_to_num(HP[..., i]) for i in range(3))
cheek = (hpart == names.index('head')) & (np.abs(hx) > 0.03) & (np.abs(hx) < 0.05) & (hz > 0.5) & (hz < 0.53) & (hy < -0.28)
skin = np.median(head[cheek], 0) * float(__import__('os').environ.get('HGAIN', '0.95')); print('hand skin', (skin * 255).round(0))
Lb = ni.gaussian_filter(np.where(hm_, L, 0), 2.5) / np.maximum(ni.gaussian_filter(hm_.astype(np.float32), 2.5), 1e-4)
det_h = np.clip((Lb / max(float(np.median(L[hm_])), 1e-4)) ** 0.6, 0.85, 1.15)
out[hm_] = skin * det_h[hm_][:, None]
print('BODYFIX hand texels', int(hm_.sum()))
cov = part >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save('textures/wo_body_tone.png'); print('BODYFIX neckline texels', int(pale.sum()))
