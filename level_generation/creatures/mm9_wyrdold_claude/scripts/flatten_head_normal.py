#!/usr/bin/env python3
"""Head normal map (shared by both tiers): flat over the nose underside/tip and the lip ellipse (r5: Meshy's relief there drew a dark
nostril smudge and a second lip edge whatever the paint). From textures/wy_head_normal_meshy.png -> textures/wy_head_normal.png. Project folder."""
import numpy as np
from PIL import Image
from scipy import ndimage as ni
n = np.asarray(Image.open('textures/wy_head_normal_meshy.png').convert('RGB'), np.float32); S = n.shape[0]
P = np.load('work/texel_pos_head.npy'); ok = ~np.isnan(P[..., 0]); P = np.nan_to_num(P); x, y, z = P[..., 0], P[..., 1], P[..., 2]
if P.shape[0] != S: raise SystemExit('size mismatch')
nose = ok & (np.abs(x) < 0.021) & (z > 0.628) & (z < 0.655) & (y < -0.112)
lips = ok & (np.abs(x) < 0.032) & (z > 0.606) & (z < 0.636) & (y < -0.09)      # r10: the whole old lip area
w = np.clip(ni.gaussian_filter((nose | lips).astype(np.float32), 1.2) * 1.3, 0, 1)[..., None] * ok[..., None]
flat = np.array([128.0, 128.0, 255.0])
out = n * (1 - w) + flat * w
Image.fromarray(np.clip(out + .5, 0, 255).astype('u1')).save('textures/wy_head_normal.png'); print('NORMAL flattened', int((w[..., 0] > 0.5).sum()), 'texels')
