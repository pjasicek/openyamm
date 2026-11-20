#!/usr/bin/env python3
"""Neck under the beard (PeasantM1's collar-paint lesson, 2026-11-01): the head references show the tunic's knotwork
neckline round the neck, so the head retexture painted the lowest neck faces (inside the tunic's front slit, under
the beard) navy and gold. Head texels of the neck (|x| < 13 cm, below NECK_TOP, front half) whose colour is not skin
(dark or off-skin chroma) take the tier's own skin (median cheek colour) darkened toward the collar (the beard's
shadow), with the paint's fine luminance detail kept at 35 %, on a soft mask; gutters refilled.
Rewrites textures/<prefix>_head_basecolor.png (backup <prefix>_head_basecolor_preneck.png on the first run).
Usage (project folder): fix_neck_pdm1.py <export glb> <prefix> [...]"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
NECK_TOP = 0.935      # m above the floor: the beard starts here at the front (export GLB rest pose)
glb, prefixes = sys.argv[1], sys.argv[2:]
N = 2048
pos, cov = texel_positions(glb, 'PeasantDM1Head', N)
y = np.nan_to_num(pos[..., 1]); x = np.nan_to_num(pos[..., 0]); z = np.nan_to_num(pos[..., 2])
neck = cov & (np.abs(x) < 0.13) & (y < 1.0)
zone = neck & (y < NECK_TOP + 0.01) & (z > -0.03)
cheek = cov & (y > 1.06) & (y < 1.09) & (z > 0.05)
for p in prefixes:
    f = Path(f'textures/{p}_head_basecolor.png')
    bk = Path(f'textures/{p}_head_basecolor_preneck.png')
    if not bk.exists():
        shutil.copyfile(f, bk)
    img = np.asarray(Image.open(bk).convert('RGB'), float)
    lum = img @ [0.299, 0.587, 0.114]
    ref = np.median(img[cheek], 0)
    chroma = img / np.maximum(img.sum(-1, keepdims=True), 1)
    dist = np.linalg.norm(chroma - ref / ref.sum(), axis=-1)
    bad = zone & ((dist > 0.05) | (lum < 70))
    bad = ndimage.binary_dilation(ndimage.binary_closing(bad, iterations=3), iterations=3) & zone
    w = ndimage.gaussian_filter(bad.astype(float), 3.0) * zone
    shade = (0.55 + 0.25 * np.clip((y - 0.87) / (NECK_TOP - 0.87), 0, 1))[..., None]
    detail = np.clip(lum - ndimage.gaussian_filter(lum, 4), -6, 6)[..., None] * 0.35
    out = img * (1 - w[..., None]) + (ref[None, None] * shade + detail) * w[..., None]
    near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out[near] = out[iy[near], ix[near]]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
    print('FIXNECK', p, 'skin ref', ref.round(), 'texels recoloured', int((w > 0.5).sum()))
