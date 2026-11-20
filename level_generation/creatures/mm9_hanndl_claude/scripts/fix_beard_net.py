#!/usr/bin/env python3
"""Beard net on the cheeks and jaw (Hanndl head retexture, 2026-11-02): Meshy drew the white beard's sides as a net of thin
crossing strands with skin between (the brief: no net-like strand patterns on skin). MM9's Hanndl has a full white beard
there, so the net is filled in, not removed: in the beard zone (face shell texels by rest position, texel_pos.py: beside
the mouth |x - CX| > X_IN, between the neck and the cheekbone, front of the ears) every texel where the white-strand
density is mid (the net, D between SPARSE and DENSE: Gaussian SIGMA of the white indicator) and skin shows between,
takes a densified beard: the strands thickened (grey dilation DIL px) mixed with the local mean of the white texels
(normalised convolution, SIGMA_W px), weighted by smoothstep(SPARSE, MID, D) x the zone fade. Dense beard and clean skin
stay as painted. Reads <head>_head_basecolor_prenet.png (made on the first run), writes <head>_head_basecolor.png and
review/fix_net_mask.png. Usage (project folder): fix_beard_net.py <head prefix> <texpos npz>"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

head, tp = sys.argv[1], sys.argv[2]
T = Path('v2/textures'); src = T / f'{head}_head_basecolor.png'; bak = T / f'{head}_head_basecolor_prenet.png'
if not bak.exists(): shutil.copy(src, bak)
img = np.asarray(Image.open(bak).convert('RGB'), np.float32)
pos = np.load(tp)['pos']
CX, X_IN, Z_LO, Z_HI, Y_MAX = -0.009, 0.022, 0.64, 0.775, 0.02
SIGMA, SPARSE, MID, SIGMA_W, DIL = 5.0, 0.10, 0.40, 6.0, 3
x, y, z = pos[..., 0] - CX, pos[..., 1], pos[..., 2]
ok = np.isfinite(x)
zone = ok & (np.abs(np.nan_to_num(x)) > X_IN) & (np.nan_to_num(z) > Z_LO) & (np.nan_to_num(z) < Z_HI) & (np.nan_to_num(y) < Y_MAX)
zone_f = ndimage.gaussian_filter(zone.astype(np.float32), 6) * ok
lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
mx, mn = img.max(2), img.min(2); sat = (mx - mn) / np.maximum(mx, 1)
white = (lum > 150) & (sat < 0.22)
skin = (sat > 0.28) & (lum > 60)
D = ndimage.gaussian_filter(white.astype(np.float32), SIGMA)
S = ndimage.gaussian_filter(skin.astype(np.float32), SIGMA)
DB = ndimage.gaussian_filter(white.astype(np.float32), 14.0)     # smooth beard extent: weights without blotches
ss = lambda a, b, v: np.clip((v - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((v - a) / (b - a), 0, 1))
w = ss(SPARSE, MID, DB) * zone_f
num = ndimage.gaussian_filter(img * white[..., None], (SIGMA_W, SIGMA_W, 0))
den = ndimage.gaussian_filter(white.astype(np.float32), SIGMA_W)[..., None]
wmean = num / np.maximum(den, 1e-3)
dil = np.stack([ndimage.grey_dilation(img[..., c], size=DIL) for c in range(3)], 2)
dil = ndimage.gaussian_filter(dil, (0.7, 0.7, 0))
dense = np.where(white[..., None], img, 0.75 * dil + 0.25 * wmean)
out = img * (1 - w[..., None]) + dense * w[..., None]
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(src)
Path('review').mkdir(exist_ok=True)
Image.fromarray((np.stack([w, zone_f * 0.5, D], 2) * 255).astype(np.uint8)).save('review/fix_net_mask.png')
print('FIX_NET texels changed > 0.1:', int((w > 0.1).sum()), 'zone texels', int(zone.sum()))
