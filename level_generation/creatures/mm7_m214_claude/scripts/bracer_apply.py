#!/usr/bin/env python3
"""Copy the left forearm's bracer onto the right forearm in the body texture set (after compose_m214.py) with the
texel map of bracer_map.py: base colour, ORM, region mask and material classes sampled from the mirrored source UV
(classes and mask nearest, the rest bilinear); normals turned through the per-texel mirror frame. Rewrites
textures/m214_{basecolor,metal_rough,normal}_1k.png, m214_region_mask.png and m214_material_classes.png in place.
Args: <map npz>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
T = Path(__file__).resolve().parents[1] / 'textures'
M = np.load(sys.argv[1]); rows, cols, suv, mats, N = M['rows'], M['cols'], M['suv'], M['mats'], int(M['n'])
sx = suv[:, 0] * N - 0.5; sy = (1 - suv[:, 1]) * N - 0.5             # source pixel coordinates (row down)


def bilinear(img):
    x0 = np.clip(np.floor(sx).astype(int), 0, N - 2); y0 = np.clip(np.floor(sy).astype(int), 0, N - 2)
    fx = np.clip(sx - x0, 0, 1)[:, None]; fy = np.clip(sy - y0, 0, 1)[:, None]
    return ((img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx) * (1 - fy)
            + (img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx) * fy)


def nearest(img):
    return img[np.clip(np.round(sy).astype(int), 0, N - 1), np.clip(np.round(sx).astype(int), 0, N - 1)]


for name, mode in (('m214_basecolor_1k.png', 'bilinear'), ('m214_metal_rough_1k.png', 'bilinear'),
                   ('m214_region_mask.png', 'nearest'), ('m214_material_classes.png', 'nearest'),
                   ('m214_normal_1k.png', 'normal')):
    im = Image.open(T / name); src_mode = im.mode
    a = np.asarray(im).astype(np.float64)
    if a.shape[0] != N:
        raise SystemExit(f'{name}: {a.shape} is not {N}')
    if mode == 'nearest':
        v = nearest(a)
    else:
        v = bilinear(a)
        if mode == 'normal':
            n = v[:, :3] / 255.0 * 2 - 1
            n = np.einsum('kij,kj->ki', mats, n); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
            v[:, :3] = (n + 1) / 2 * 255
    a[rows, cols] = v
    Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8), src_mode).save(T / name)
    print(f'BRACER {name}: {len(rows)} texels copied ({mode})')
