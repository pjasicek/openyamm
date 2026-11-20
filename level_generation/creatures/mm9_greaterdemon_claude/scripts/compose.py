#!/usr/bin/env python3
"""Texture set for the Greater Demon (one MM9 row, one skin, so no region mask or ramps; after
mm9_lobber_claude/scripts/compose.py). Usage: compose.py

Inputs: meshy/retexture_v1 maps (our UVs), textures/gdemon_ao_2k.png, work/uv3d_body.npz (dump_uv3d.py).
Outputs in textures/: gdemon_basecolor.png (2K, gutters padded; graded by grade_basecolor.py), gdemon_normal_1k.png,
gdemon_metal_rough_1k.png (R AO, G roughness, B metallic 0).
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'mm9_lobber_claude' / 'scripts'))
T = HERE / 'textures'
M = HERE / 'meshy' / 'retexture_v1'
S = 1024


def raster_cov(npz, size):
    d = np.load(npz)
    uv = d['uv'] * size
    cov = np.zeros((size, size), bool)
    for p in uv:
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (1 - l1 - l2 >= -1e-4)
        iy, ix = np.nonzero(inside)
        cov[size - 1 - (iy + y0), ix + x0] = True
    return cov


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


cov2 = raster_cov(HERE / 'work' / 'uv3d_body.npz', 2048)
cov1 = raster_cov(HERE / 'work' / 'uv3d_body.npz', S)
base = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB'))
Image.fromarray(pad(base, cov2)).save(T / 'gdemon_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB'))
Image.fromarray(pad(nrm, cov2)).resize((S, S), Image.LANCZOS).save(T / 'gdemon_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = pad(np.clip(rough, 0.45, 0.85), cov1)
ao = np.asarray(Image.open(T / 'gdemon_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'gdemon_metal_rough_1k.png')
print('COMPOSED', T)
