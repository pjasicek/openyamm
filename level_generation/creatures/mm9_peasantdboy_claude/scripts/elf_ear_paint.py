#!/usr/bin/env python3
"""Paint the elf ear islands (add_elf_ears.py: Blender UV u 0.04..0.74, v 0.83..0.98 of the head set) into a head set:
the tier's own cheek skin (median of light, skin-hued head texels) with a darker, redder concha in the dish, a light
helix rim, shade toward the base (it leaves the hair) and a warm tip; the back panels plain skin a little darker.
Normal flat, ORM R 255 / G roughness 205 / B 0 there. Run on every head set (only row 73's descriptor shows the ears).
Usage (project folder): elf_ear_paint.py <head set prefix> ...   (textures/<p>_head_basecolor.png, _normal_1k, _metal_rough_1k)"""
import sys
import numpy as np
from PIL import Image
ISL = {('R', 'f'): (0.04, 0.83), ('R', 'b'): (0.22, 0.83), ('L', 'f'): (0.40, 0.83), ('L', 'b'): (0.58, 0.83)}
SU, SV, PAD = 0.16, 0.15, 0.012
SKIN_FROM = 'pboye_tp'      # the ears belong to boy e (row 73): every set carries his skin there (the attachment is cut from set a)
for pre in sys.argv[1:]:
    p = f'textures/{pre}_head_basecolor.png'
    im = np.asarray(Image.open(p).convert('RGB'), np.float64)
    H, W = im.shape[:2]
    ref = np.asarray(Image.open(f'textures/{SKIN_FROM}_head_basecolor.png').convert('RGB'), np.float64)
    head = ref[int(H * 0.2):, :int(W * 0.8)].reshape(-1, 3)
    r, g, b = head.T
    lum = head @ [0.299, 0.587, 0.114]
    sk = head[(r > g * 1.15) & (g > b * 1.05) & (lum > 150) & (r < 250)]
    skin = np.median(sk, 0)
    out = im.copy()
    for (side, key), (u0, v0) in ISL.items():
        x0, x1 = int((u0 - PAD) * W), int((u0 + SU + PAD) * W)
        y0, y1 = int((1 - (v0 + SV + PAD)) * H), int((1 - (v0 - PAD)) * H)
        xs = (np.arange(x0, x1) + 0.5) / W
        ys = 1 - (np.arange(y0, y1) + 0.5) / H
        U, V = np.meshgrid(xs, ys)
        vp = np.clip((U - u0) / SU, 0, 1) * 2 - 1          # across the ear, -1..1
        up = np.clip((V - v0) / SV, 0, 1)                   # base 0 .. tip 1
        if key == 'f':
            dish = (1 - vp ** 2) * np.sin(np.pi * np.clip(up / 0.9, 0, 1)) * (1 - up) ** 0.4
            mul = 1 - 0.30 * dish ** 1.3
            rim = np.clip((np.abs(vp) - 0.72) / 0.28, 0, 1)
            mul = mul * (1 + 0.07 * rim)
            red = 0.10 * dish + 0.06 * up ** 3
        else:
            mul = 0.93 + 0.0 * vp
            red = 0.04 * up ** 3
        mul = mul * (0.80 + 0.20 * np.clip(up / 0.18, 0, 1))  # shade where the ear leaves the hair
        col = skin[None, None, :] * mul[..., None]
        col[..., 0] *= 1 + red
        col[..., 2] *= 1 - 0.6 * red
        out[y0:y1, x0:x1] = np.clip(col, 0, 255)
    Image.fromarray(np.uint8(out)).save(p)
    for suf, val in (('normal_1k', (128, 128, 255)), ('metal_rough_1k', (255, 205, 0))):
        q = f'textures/{pre}_head_{suf}.png'
        a = np.asarray(Image.open(q).convert('RGB')).copy()
        h, w = a.shape[:2]
        for (u0, v0) in ISL.values():
            a[int((1 - (v0 + SV + PAD)) * h):int((1 - (v0 - PAD)) * h), int((u0 - PAD) * w):int((u0 + SU + PAD) * w)] = val
        Image.fromarray(a).save(q)
    print('EARPAINT', pre, 'skin', skin.round(1).tolist(), 'texels', len(sk))
