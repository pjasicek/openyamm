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
zone = cov & (y < 1.56) & (r_axis < 0.14)        # r17: the whole lower neck (beard texels are excluded by tone below)
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
    # r17 (neck fix): tone correction of the whole lower neck, not only of detected collar paint: the low-frequency
    # colour L (island-normalised Gaussian, 8 texels) moves to the skin reference with a vertical ramp (none above
    # 1.56 m, full below 1.52 m), keeping the paint's own detail; the hard zone edge of r16 drew a straight seam across
    # the neck. Beard and hair texels (L darker than 0.6 x the reference) are left out with a soft edge.
    covf = cov.astype(float)
    L = ndimage.gaussian_filter(img * covf[..., None], (8, 8, 0)) / np.maximum(ndimage.gaussian_filter(covf, 8), 1e-3)[..., None]
    Llum = L @ [0.299, 0.587, 0.114]
    yy = np.nan_to_num(y)
    t = np.clip((1.56 - yy) / 0.04, 0, 1); wy = t * t * (3 - 2 * t)
    Lch = L / np.maximum(L.sum(-1, keepdims=True), 1)
    Ldist = np.linalg.norm(Lch - ref / ref.sum(), axis=-1)
    # beard: dark AND skin-hued (brown) AND on the jaw underside; dark olive/rust collar paint is not beard
    beard = (Llum < 0.6 * lref) & (Ldist < 0.05) & (yy > 1.495) & (pos[..., 2] > -0.02)
    notbeard = ndimage.gaussian_filter((~beard).astype(float), 3)
    shade = (0.92 + 0.08 * np.clip((yy - 1.47) / 0.07, 0, 1))[..., None]   # a faint collar shadow only (fix_seam.py continues the skin)
    w_tone = (wy * notbeard * zone)[..., None]
    out = img + (ref[None, None] * shade - L) * w_tone
    # strong collar paint and rust lines (chroma far from the skin) are replaced outright, grey pore detail kept
    bad = zone & (dist > 0.035) & (lum > 20) & (lum < 170) & (notbeard > 0.5)
    bad = ndimage.binary_dilation(ndimage.binary_closing(bad, iterations=3), iterations=3) & cov
    w = np.clip(ndimage.gaussian_filter(bad.astype(float), 3.0) / np.maximum(ndimage.gaussian_filter(covf, 3.0), 1e-3), 0, 1) * zone
    detail = np.clip(lum - ndimage.gaussian_filter(lum, 4), -6, 6)[..., None] * 0.35
    out = out * (1 - w[..., None]) + (ref[None, None] * shade + detail) * w[..., None]
    w = np.maximum(w, w_tone[..., 0] * 0.5)          # for the normal flattening below
    # refill the gutters next to recoloured islands from their nearest island texel (bilinear sampling at the UV seams
    # otherwise picks up the old collar colour as thin lines)
    near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out[near] = out[iy[near], ix[near]]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
    # the normal map there carries the collar folds Meshy painted with the collar colour: flatten it under the same mask
    # (face fix, 2026-11-01: the recoloured flange read as hard-edged flat panels under the jaw)
    fn = Path(f'textures/{p}_head_normal_1k.png')
    bn = Path(f'textures/{p}_head_normal_1k_preneck.png')
    if not bn.exists():
        shutil.copyfile(fn, bn)
    nm = np.asarray(Image.open(bn).convert('RGB'), float)
    w1 = np.asarray(Image.fromarray(np.uint8(np.clip(w, 0, 1) * 255)).resize(nm.shape[1::-1], Image.BILINEAR), float)[..., None] / 255 * 0.9
    Image.fromarray(np.uint8(np.clip(nm * (1 - w1) + np.array([128, 128, 255.0]) * w1, 0, 255))).save(fn)
    print('FIXNECK', p, 'skin ref', ref.round(), 'texels recoloured', int((w > 0.5).sum()))
