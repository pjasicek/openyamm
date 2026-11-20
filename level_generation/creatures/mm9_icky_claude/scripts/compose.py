#!/usr/bin/env python3
"""Shared texture set for the Flying Icky (CLAUDE_CREATURE_TEXTURES.md; ported from mm9_lobber_claude/scripts/compose.py).

All three MM9 rows (Airborne Icky L7, Flying Icky L11, Astral Icky L18) use the one MM9 skin FLYINGICKY.dtx and differ
only by MONSTERS.txt Scale (0.5 / 1 / 2), so there are no tier ramps: one skin, identity for every row.

Inputs: meshy/icky_retexture_v2 maps (4K on the texture pass UVs), textures/icky_ao_2k.png, work/uv3d_icky_v3.npz (dump_uv3d.py),
textures/icky_wing_basecolor_src.png (prep_wings.py).
Outputs in textures/: icky_basecolor.png (2K, gutters padded; graded separately by grade_basecolor.py),
icky_normal_1k.png, icky_metal_rough_1k.png (R AO, G roughness, B metallic 0), icky_material_classes.png,
icky_wing_basecolor.png (the HD top view crop), icky_wing_metal_rough.png.
Roughness: the red mouth ring and throat (warm red texels) 0.4 (wet), horns/teeth/spikes (cream/yellow) 0.5,
scales the Meshy roughness clipped to 0.55-0.8.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
M = HERE / 'meshy' / 'icky_retexture_v2'
UV3D = HERE / 'work' / 'uv3d_icky_v3.npz'
S = 1024


def load_map(name, size, mode='RGB'):
    """Meshy's 4K map downsampled once (Lanczos), never re-baked."""
    image = Image.open(M / name).convert(mode)
    return np.asarray(image.resize((size, size), Image.LANCZOS), np.float32) / 255


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def raster(npz, size):
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
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
        iy, ix = np.nonzero(inside)
        tri[size - 1 - (iy + y0), ix + x0] = t
    return tri


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


tri2k = raster(UV3D, 2048)
cov2k = tri2k >= 0
base2k = load_map('texture_urls_0_base_color.png', 2048)
Image.fromarray((pad(base2k, cov2k) * 255).astype(np.uint8)).save(T / 'icky_basecolor.png')
tri1k = raster(UV3D, S)
cov = tri1k >= 0
nrm = load_map('texture_urls_0_normal.png', S)
Image.fromarray((pad(nrm, cov) * 255).astype(np.uint8)).save(T / 'icky_normal_1k.png')
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
ind_red = ndimage.gaussian_filter((((h < 22) | (h > 330)) & (s > 0.35) & cov).astype(np.float32), 1.5) > 0.5
ind_cream = ndimage.gaussian_filter((((h >= 22) & (h < 62)) & (v > 0.55) & cov).astype(np.float32), 1.5) > 0.5
classes = np.zeros((S, S), np.uint8)
classes[cov] = 1
classes[ind_cream] = 2
classes[ind_red] = 3
Image.fromarray(classes * 80).save(T / 'icky_material_classes.png')
rough = load_map('texture_urls_0_roughness.png', S, 'L')
rough = np.where(ind_red, 0.4, np.where(ind_cream, 0.5, np.clip(rough, 0.55, 0.8)))
rough = pad(rough, cov)
ao = np.asarray(Image.open(T / 'icky_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'icky_metal_rough_1k.png')

# wings: the HD top-view crop as is; roughness 0.6 (leathery), AO 1
wing = Image.open(T / 'icky_wing_basecolor_src.png').convert('RGB')
wing.save(T / 'icky_wing_basecolor.png')
ws = (512, 128)
Image.merge('RGB', [Image.new('L', ws, 255), Image.new('L', ws, 153), Image.new('L', ws, 0)]).save(
    T / 'icky_wing_metal_rough.png')
print('COMPOSED', {'covered_1k': int(cov.sum()), 'red': int(ind_red.sum()), 'cream': int(ind_cream.sum())})
