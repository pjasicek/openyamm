#!/usr/bin/env python3
"""Texture set for the MM9 pig (row 271 Pig, pig.dtx; one skin, no tiers, so no region mask or ramps, as the
Isle of Ashes NPCs). Usage: compose_pig.py   (from mm9_crow_claude/scripts/compose_crow.py)

Outputs in textures/: pig_basecolor.png (2K, padded; graded by grade_basecolor.py), pig_normal_1k.png,
pig_metal_rough_1k.png (R AO, G roughness, B 0), pig_material_classes.png (skin 1, hooves 4, eyes 6).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
M = HERE / 'meshy' / 'pig_retexture_v1'
S = 1024


def raster(npz, size):
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    xyz = np.zeros((size, size, 3), np.float32)
    for t in range(len(uv)):
        p = uv[t]
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
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        rows, cols = size - 1 - (iy + y0), ix + x0
        tri[rows, cols] = t
        xyz[rows, cols] = np.stack([l1[inside], l2[inside], l3[inside]], 1) @ d['xyz'][t]
    return tri, xyz, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


tri, xyz, d = raster(HERE / 'work' / 'uv3d_pig.npz', S)
covered = tri >= 0
part = np.where(covered, d['part'][np.maximum(tri, 0)], -1)
eyes = covered & (part == 2)
hooves = covered & ~eyes & (xyz[..., 2] < 0.035)
classes = np.zeros((S, S), np.uint8)
classes[covered] = 1
classes[hooves] = 4
classes[eyes] = 6
Image.fromarray(classes * 20).save(T / 'pig_material_classes.png')
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255
tri2, _, _ = raster(HERE / 'work' / 'uv3d_pig.npz', 2048)
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'pig_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS), np.float32) / 255
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'pig_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = np.where(eyes, 0.15, np.where(hooves, 0.5, np.clip(rough, 0.6, 0.85)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'pig_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'pig_metal_rough_1k.png')
print('COMPOSED', {'covered': int(covered.sum()), 'eyes': int(eyes.sum()), 'hooves': int(hooves.sum())})
