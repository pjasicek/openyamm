#!/usr/bin/env python3
"""Neck skin under the collar (2026-11-01, viewer shots): the head references show the jacket collar around the neck,
so the head retexture painted the lowest neck faces (inside the collar, seen at the nape and the throat) collar colour
- olive on A, rust on B - which read as a flat tan/red patch above the real collar. Head texels below the jaw within
11 cm of the neck axis whose chromaticity is more than 0.045 from the tier's skin (wool paint; skin varies under 0.03; the beard and hair are darker) take the tier's own front-neck skin colour with their luminance kept (power 0.6), on a soft mask.
Rewrites textures/<prefix>_head_basecolor.png (backup <prefix>_head_basecolor_preneck.png on the first run).
Usage (project folder): fix_neck.py <export glb> <prefix> [...]"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefixes = sys.argv[1], sys.argv[2:]
N = 2048
pos, cov = texel_positions(glb, 'PeasantM1Head', N)
y = pos[..., 1]
r_axis = np.hypot(np.nan_to_num(pos[..., 0]), np.nan_to_num(pos[..., 2]) - 0.002)
zone = cov & (y < 1.545) & (r_axis < 0.13) & ~((pos[..., 2] > 0.03) & (y > 1.515))   # not the beard on the jaw
front = cov & (y > 1.48) & (y < 1.52) & (pos[..., 2] > 0.03)
for p in prefixes:
    f = Path(f'textures/{p}_head_basecolor.png')
    bk = Path(f'textures/{p}_head_basecolor_preneck.png')
    if not bk.exists():
        shutil.copyfile(f, bk)
    img = np.asarray(Image.open(bk).convert('RGB'), float)
    rg = img[..., 0] / np.maximum(img[..., 1], 1)
    gb = img[..., 1] / np.maximum(img[..., 2], 1)
    lum = img @ [0.299, 0.587, 0.114]
    skinlike = front & (rg > 1.25) & (rg < 1.9) & (gb > 1.2) & (gb < 2.0)
    ref = np.median(img[skinlike], 0)
    lref = ref @ [0.299, 0.587, 0.114]
    chroma = img / np.maximum(img.sum(-1, keepdims=True), 1)
    dist = np.linalg.norm(chroma - ref / ref.sum(), axis=-1)
    bad = zone & (dist > 0.045) & (lum > 35) & (lum < 170)   # olive collar paint (~0.065) or rust lines (~0.08); skin < 0.03
    bad = ndimage.binary_dilation(ndimage.binary_closing(bad, iterations=3), iterations=3) & cov
    w = ndimage.gaussian_filter(bad.astype(float), 3.0) * zone
    # skin with a soft collar shadow toward the bottom of the neck, plus 35 % of the paint's own fine luminance detail
    shade = (0.72 + 0.28 * np.clip((np.nan_to_num(y) - 1.475) / 0.06, 0, 1))[..., None]
    detail = np.clip(lum - ndimage.gaussian_filter(lum, 4), -6, 6)[..., None] * 0.35   # grey pore detail only (the paint's seam lines are rust)
    out = img * (1 - w[..., None]) + (ref[None, None] * shade + detail) * w[..., None]
    # refill the gutters next to recoloured islands from their nearest island texel (bilinear sampling at the UV seams
    # otherwise picks up the old collar colour as thin lines)
    near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out[near] = out[iy[near], ix[near]]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
    print('FIXNECK', p, 'skin ref', ref.round(), 'texels recoloured', int((w > 0.5).sum()))
