#!/usr/bin/env python3
"""Scholar body colour fixes by 3D position (work/texel_pos.npy), textures/sc_body_final.png -> textures/sc_body_tone.png:
1. BEARD GHOST: Meshy painted the beard (hidden in front of the chest) onto the robe and stole behind it: ginger texels (hue 15-45, sat > 0.35)
   on the robe part in the chest zone take the cloth around them (the stole's charcoal or the robe's navy, by normalised convolution of the
   non-ginger texels), with their own luminance detail. The Master Scholar's white beard would otherwise move over ginger patches.
2. HANDS: one clean skin colour (the face's cheek of head A, x HGAIN) times the paint's broad luminance (Gaussian 2.5 px), within +-15 %.
Project folder."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ni
im = np.asarray(Image.open('textures/sc_body_final.png').convert('RGB'), np.float32) / 255
P = np.load('work/texel_pos.npy'); part = np.load('work/texel_part.npy'); names = [str(x) for x in np.load('work/asm.npz')['names']]
X, Y, Z = (np.nan_to_num(P[..., i]) for i in range(3))
LUMA = np.array([0.2126, 0.7152, 0.0722]); L = im @ LUMA
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255; h, s = hsv[..., 0] * 360, hsv[..., 1]
out = im.copy()
robe = part == names.index('robe')
zone = robe & (np.abs(X) < 0.16) & (Z > 0.30) & (Z < 0.75)
gin = zone & (h > 15) & (h < 45) & (s > 0.35)
gin = ni.binary_dilation(gin, iterations=2) & zone
ok = robe & ~gin
fill = None
for sg in (24.0, 12.0, 6.0):
    wv = ni.gaussian_filter(ok.astype(np.float32), sg)
    f2 = np.stack([ni.gaussian_filter(im[..., i] * ok, sg) for i in range(3)], -1) / np.maximum(wv, 1e-6)[..., None]
    fill = f2 if fill is None else np.where((wv > 0.2)[..., None], f2, fill)
det = L - ni.gaussian_filter(L, 3)
w = np.clip(ni.gaussian_filter(gin.astype(np.float32), 1.0) * 1.5, 0, 1) * zone
out = out * (1 - w[..., None]) + np.clip(fill + 0.5 * det[..., None], 0, 1) * w[..., None]
print('BEARD ghost texels', int(gin.sum()))
hm_ = part == names.index('hands')
head = np.asarray(Image.open('textures/sc_head_a_final.png').convert('RGB'), np.float32) / 255
HP = np.load('work/texel_pos_head.npy'); hpart = np.load('work/texel_part_head.npy'); hx, hy, hz = (np.nan_to_num(HP[..., i]) for i in range(3))
cheek = (hpart == names.index('head')) & (np.abs(hx) > 0.03) & (np.abs(hx) < 0.05) & (hz > 0.76) & (hz < 0.79) & (hy < -0.03)
skin = np.median(head[cheek], 0) * float(os.environ.get('HGAIN', '0.95')); print('hand skin', (skin * 255).round(0), int(cheek.sum()))
Lb = ni.gaussian_filter(np.where(hm_, L, 0), 2.5) / np.maximum(ni.gaussian_filter(hm_.astype(np.float32), 2.5), 1e-4)
dh = np.clip((Lb / max(float(np.median(L[hm_])), 1e-4)) ** 0.6, 0.85, 1.15)
out[hm_] = skin * dh[hm_][:, None]
cov = part >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save('textures/sc_body_tone.png'); print('BODYFIX hands', int(hm_.sum()))
