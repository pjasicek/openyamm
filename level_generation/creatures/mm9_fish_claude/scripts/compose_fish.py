#!/usr/bin/env python3
"""Texture set of the MM9 fish body (one MM9 skin, FISH.dtx: no tiers, so no region mask or ramps).
Usage: compose_fish.py   (run, then grade_basecolor.py, then run again: the second run only re-reads the grade)
Outputs in textures/: fish_basecolor.png (2K, the 4K Meshy paint downsampled once, padded), fish_normal_1k.png,
fish_metal_rough_1k.png (R baked AO, G roughness, B metallic 0), fish_material_classes.png (1 skin, 6 eye, 7 mouth
interior). The fins are a separate material (fish_fins_basecolor.png, build_fins.py) and keep the side master's paint
with its alpha.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
M = HERE / 'meshy' / 'fish_retexture_v1'


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
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (1 - l1 - l2 >= -1e-4)
        iy, ix = np.nonzero(inside)
        tri[size - 1 - (iy + y0), ix + x0] = t
    return tri, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


tri2, d = raster(HERE / 'work' / 'uv3d_body.npz', 2048)
cov2 = tri2 >= 0
base = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                  np.float32) / 255


def flank_repair(images):
    """The side masters paint the pectoral fin onto the flank under our fin leaf (a grey smear) and leave a small dotted
    oval on the stub of Meshy's fin behind the gill. The smear keeps its fine scale detail: only its low frequencies
    (blur over the body texels, sigma 22 px) are replaced by the flank's from 7.5 cm further back at the same elevation,
    so back spots, pink band and belly run through it. The oval is a small soft copy from 2.6 cm further back."""
    t = np.load(HERE / 'work' / 'texel_xyz.npz')
    xyz = t['xyz']
    body = cov2 & (d['part'][np.maximum(tri2, 0)] == 0)
    v = d['xyz'][d['part'] == 0].reshape(-1, 3)
    k = np.round(v[:, 1] * 500).astype(int)
    keys = np.unique(k)
    top = np.array([v[k == i, 2].max() for i in keys]); bot = np.array([v[k == i, 2].min() for i in keys])
    top = ndimage.uniform_filter1d(top, 5); bot = ndimage.uniform_filter1d(bot, 5)
    zc = lambda y: np.interp(y * 500, keys, (top + bot) / 2)
    hh = lambda y: np.interp(y * 500, keys, (top - bot) / 2)
    m = body.astype(np.float32)
    nm = np.maximum(ndimage.gaussian_filter(m, 22), 1e-3)
    out = [im.copy() for im in images]
    report = {}
    for side in (1, -1):
        sel = body & (np.sign(xyz[..., 0]) == side)
        ry, rx = np.nonzero(sel)
        P = xyz[ry, rx]
        tree = cKDTree(P[:, 1:3])
        for ii, (im, o) in enumerate(zip(images, out)):
            if ii == 0:     # colour only; the normal map keeps its scale relief
                low = np.stack([ndimage.gaussian_filter(im[..., c] * m, 22) / nm for c in range(3)], -1)
                rr = np.hypot((P[:, 1] + 0.050) / 0.030, (P[:, 2] - 0.070) / 0.036)
                hit = rr < 1.3
                y, z = P[hit, 1], P[hit, 2]
                y2 = y + 0.075
                z2 = zc(y2) + (z - zc(y)) * hh(y2) / np.maximum(hh(y), 1e-4)
                _, nn = tree.query(np.stack([y2, z2], 1))
                w = np.clip((1.3 - rr[hit]) / 0.5, 0, 1)[:, None]
                w = w * w * (3 - 2 * w)
                ty, tx = ry[hit], rx[hit]
                o[ty, tx] = np.clip(o[ty, tx] + (low[ry[nn], rx[nn]] - low[ty, tx]) * w, 0, 1)
                report[f'smear_{side}'] = int(hit.sum())
            rr = np.hypot((P[:, 1] + 0.098) / 0.009, (P[:, 2] - 0.071) / 0.012)
            hit = rr < 1.3
            _, nn = tree.query(np.stack([P[hit, 1] + 0.026, P[hit, 2]], 1))
            w = np.clip((1.3 - rr[hit]) / 0.5, 0, 1)[:, None]
            w = w * w * (3 - 2 * w)
            ty, tx = ry[hit], rx[hit]
            o[ty, tx] = o[ty, tx] * (1 - w) + im[ry[nn], rx[nn]] * w
            report[f'oval_{side}'] = int(hit.sum())
    print('REPAIR', report)
    return out


nrm2 = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                  np.float32) / 255
base, nrm2 = flank_repair([base, nrm2])
Image.fromarray((pad(base, cov2) * 255).round().astype(np.uint8)).save(T / 'fish_basecolor.png')
S = 1024
tri, _ = raster(HERE / 'work' / 'uv3d_body.npz', S)
cov = tri >= 0
ti = np.maximum(tri, 0)
part = np.where(cov, d['part'][ti], -1)
cen = d['xyz'].mean(1)[ti]
eye = cov & (part == 1)
ymin = d['xyz'][..., 1].min()
# the open mouth: texels inside the lip ring (behind the snout tip, close to the midline axis)
mouth = cov & ~eye & (cen[..., 1] < ymin + 0.02) & (np.hypot(cen[..., 0], cen[..., 2] - 0.0635) < 0.0075) & \
    (cen[..., 1] > ymin + 0.004)
classes = np.where(eye, 6, np.where(mouth, 7, np.where(cov, 1, 0))).astype(np.uint8)
Image.fromarray(classes).save(T / 'fish_material_classes.png')
Image.fromarray((pad(nrm2, cov2) * 255).round().astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'fish_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = np.where(eye, 0.2, np.where(mouth, 0.7, np.clip(rough + 0.3, 0.68, 0.85)))
# matte scales: the engine runs specular 0 anyway, and a low roughness shows a white sheen along the back in the viewer
rough = pad(rough, cov)
ao = np.asarray(Image.open(T / 'fish_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'fish_metal_rough_1k.png')
print('COMPOSED', json.dumps({'eye_texels': int(eye.sum()), 'mouth_texels': int(mouth.sum()), 'covered': int(cov.sum())}))
