#!/usr/bin/env python3
"""Hands toned to the new face (2026-11-02, shared-body variants): the head + hands set keeps the approved model's hand
texels (compose_head_texpass.py), graded to THAT person's skin; a different person needs his own hand tone. Face skin =
head-square texels (lower-left 0.8 square) of skin hue/saturation; hand texels = everything outside the square that is
painted. Each hand texel is multiplied per channel (in linear light) by face median / hand median, so the hands keep
their own detail and take the face's tone. Reads <prefix>_head_basecolor_prehand.png (made on the first run), writes
<prefix>_head_basecolor.png. Usage (project folder): hand_tone.py <head prefix> [strength 1.0] [texpos npz cx]
With a texel_pos.py npz (and the head centre x), the face reference is the cheeks only (front of the face, beside the
nose, eye to mouth height): the median of every head-square skin texel also counts the shaded neck and reads too dark."""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
pre = sys.argv[1]; k = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
T = Path('v2/textures'); src = T / f'{pre}_head_basecolor.png'; bak = T / f'{pre}_head_basecolor_prehand.png'
if not bak.exists(): shutil.copy(src, bak)
img = np.asarray(Image.open(bak).convert('RGB'), np.float32) / 255
H, W = img.shape[:2]; S = int(round(0.8 * W))
lin = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4)
yy, xx = np.mgrid[0:H, 0:W]
headsq = (xx < S) & (yy >= H - S)
mx, mn = img.max(2), img.min(2); sat = (mx - mn) / np.maximum(mx, 1e-3)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
skin = headsq & (sat > 0.22) & (sat < 0.75) & (mx > 0.35) & (r >= g) & (g >= b)
hand = ~headsq & (mx > 0.08)
if len(sys.argv) > 4:
    p = np.load(sys.argv[3])['pos']; cx = float(sys.argv[4]); x, y, z = (np.nan_to_num(p[..., i]) for i in range(3))
    ok = np.isfinite(p[..., 0])
    zs = z[ok & (y < -0.04)]; ztop = np.percentile(zs, 99)       # top of the face shell's front
    skin = skin & ok & (y < -0.06) & (z > ztop - 0.19) & (z < ztop - 0.13) & (np.abs(x - cx) > 0.025) & (np.abs(x - cx) < 0.06)
fm = np.median(lin[skin], 0); hm = np.median(lin[hand], 0)
gain = (fm / np.maximum(hm, 1e-4)) ** k
out = lin.copy(); out[hand] = np.clip(lin[hand] * gain, 0, 1)
srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * out ** (1 / 2.4) - 0.055)
Image.fromarray(np.clip(srgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(src)
print('HAND_TONE face median', np.round(fm, 3).tolist(), 'hand median', np.round(hm, 3).tolist(), 'gain', np.round(gain, 3).tolist(),
      'skin texels', int(skin.sum()), 'hand texels', int(hand.sum()))
