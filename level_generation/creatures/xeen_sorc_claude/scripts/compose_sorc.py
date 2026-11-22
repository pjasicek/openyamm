#!/usr/bin/env python3
"""Sorceress texture sets from meshy/retexture_v1 (ONE 4K paint on the uv_sorc.py layout: body square in the lower-left
2048 quadrant, head square in the lower-right one). Each quadrant is cut out and downsampled ONCE (Lanczos) to its 1K
set (CLAUDE_CREATURE_TEXTURES.md "Head detail": body 1K + head 1K; merge_head_material.py joins them at runtime):
- colour 1K, normal 1K, ORM 1K (R baked AO from textures/sorc_ao_2k.png's matching half, G roughness clamped
  0.45-0.95, B 0) for the body (sorc_*) and the head (sorc_head_*);
- region mask (body only, R) = the white cloth: the halter on the skin shell (low saturation, light), the shoulder caps
  (garment 4, light texels: the studs stay out), the halter's strap ties (P44/P51, labelled with the
  jewellery, garment 5: light texels; the choker, crescent and gem are dark, gold or green; the halter only between 1.15 and 1.52 m, since the skin under the
  girdle carries a silver projection of it) and both panels (garments 3, 7, light texels); The paint has no
  distinct dark hems (a trim channel found 0.01 % of the islands), so Morgana's black trim (D-32) is a ramp whose dark
  stops go to near-black (tier_ramps_sorc.py). The head set has no region (skin, hair, gems are kept in every tier).
- material classes (texture doc labels: 1 skin, 2 hair, 8 cloth/leather, 9 metal, 6 eye, 11 other/gems).
Rasters per triangle from work/uv_body.npz / uv_head.npz (dump_uv_sets.py). Grading, ramps and the gutter fill follow
in build_runtime.sh."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
Image.MAX_IMAGE_PIXELS = None


def raster(npz, values, n):
    """Per-texel label of the triangle covering it (255 = no triangle); corners, midpoints and centroid also land."""
    d = np.load(npz); uv = d['uv'] * n; lab = d[values]
    img = np.full((n, n), 255, np.uint8)
    for t, g in zip(uv, lab):
        A, B, C = t
        lo = np.floor(np.minimum(np.minimum(A, B), C)).astype(int); hi = np.ceil(np.maximum(np.maximum(A, B), C)).astype(int)
        x0, y0 = max(lo[0], 0), max(lo[1], 0); x1, y1 = min(hi[0], n - 1), min(hi[1], n - 1)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
        if abs(den) > 1e-12:
            l1 = ((B[1] - C[1]) * (xs - C[0]) + (C[0] - B[0]) * (ys - C[1])) / den
            l2 = ((C[1] - A[1]) * (xs - C[0]) + (A[0] - C[0]) * (ys - C[1])) / den
            m = (l1 >= -1e-6) & (l2 >= -1e-6) & (1 - l1 - l2 >= -1e-6)
            img[ys[m].astype(int), xs[m].astype(int)] = g
        for p in (A, B, C, (A + B) / 2, (B + C) / 2, (C + A) / 2, (A + B + C) / 3):
            x, y = int(min(max(p[0], 0), n - 1)), int(min(max(p[1], 0), n - 1))
            img[y, x] = g
    return img


def quad(path, which, mode='RGB'):
    im = Image.open(path).convert(mode); w, h = im.size; s = w // 2
    box = (0, h - s, s, h) if which == 'body' else (w - s, h - s, w, h)
    return im.crop(box)


base4 = Image.open(f'{SRC}_base_color.png'); print('COMPOSE Meshy colour', base4.size)
ao2 = Image.open(OUT / 'sorc_ao_2k.png').convert('L')
for which, pre in (('body', 'sorc'), ('head', 'sorc_head')):
    col = quad(f'{SRC}_base_color.png', which).resize((1024, 1024), Image.LANCZOS)
    col.save(OUT / f'{pre}_basecolor.png')
    quad(f'{SRC}_normal.png', which).resize((1024, 1024), Image.LANCZOS).save(OUT / f'{pre}_normal_1k.png')
    rough = np.asarray(quad(f'{SRC}_roughness.png', which, 'L').resize((1024, 1024), Image.LANCZOS)) / 255.0
    w2, h2 = ao2.size; s2 = w2 // 2
    ao = ao2.crop((0, h2 - s2, s2, h2) if which == 'body' else (w2 - s2, h2 - s2, w2, h2)).resize((1024, 1024), Image.LANCZOS)
    ao.save(OUT / f'{pre}_ao_1k.png')
    ao = np.asarray(ao) / 255.0
    orm = np.stack([ao, np.clip(rough, 0.45, 0.95), np.zeros_like(ao)], -1)
    Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(OUT / f'{pre}_mr_1k.png')
    rgb = np.asarray(col, np.float64) / 255.0
    mx = rgb.max(-1); mn = rgb.min(-1)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    gar = raster(ROOT / f'work/uv_{which}.npz', 'garment', 1024)
    # texels within 3 px of a triangle that the centre test missed (island rims): nearest triangle's label, so the
    # masks reach the island edges that gutter_fill.py counts as island (it keeps them, it does not pad them)
    dist, (iy, ix) = ndimage.distance_transform_edt(gar == 255, return_indices=True)
    gar = np.where((gar == 255) & (dist <= 3), gar[iy, ix], gar)
    np.save(ROOT / f'work/garment_{which}_1k.npy', gar)
    gold = (hue > 30) & (hue < 65) & (sat > 0.3) & (mx > 0.3)
    green = (hue > 90) & (hue < 170) & (sat > 0.35)
    cls = np.full(gar.shape, 11, np.uint8)
    if which == 'body':
        light = (sat < 0.22) & (mx > 0.42)
        zcm = raster(ROOT / 'work/uv_body.npz', 'zcm', 1024)
        dz, (jy, jx) = ndimage.distance_transform_edt(zcm == 255, return_indices=True)
        zcm = np.where((zcm == 255) & (dz <= 3), zcm[jy, jx], zcm)
        # the halter is the only cloth on the skin shell (z 1.15-1.45 m); the skin under the girdle carries a silver
        # projection of the girdle that must stay out
        # elsewhere on the skin shell only bright white (the skin under the panels carries their projection; the
        # girdle's silver projection is darker)
        cloth = light & (np.isin(gar, (3, 4, 5, 7)) | ((gar == 0) & ~green & (((zcm >= 115) & (zcm <= 152)) | (mx > 0.8))))
        # opening only on the skin shell (stray specks): the panels' and caps' thin side strips are cloth too
        cloth = (ndimage.binary_opening(cloth & (gar == 0), iterations=1)) | (cloth & np.isin(gar, (3, 4, 5, 7)))
        cloth = ndimage.binary_closing(cloth, iterations=2) & (gar != 255)
        # the panels are cloth from girdle to hem: dark folds inside them stay in
        cloth |= ndimage.binary_fill_holes(cloth) & np.isin(gar, (3, 7))
        # the cloth's edge texels on the skin shell mix white and brown at 1K: two texels more where still pale, so
        # the B/C/M tiers show no white outline round the halter
        for _ in range(2):
            cloth |= ndimage.binary_dilation(cloth) & (gar != 255) & np.isin(gar, (0, 4, 5)) & (mx > 0.45) & (sat < 0.45) & ~green & ~gold
        wr = ndimage.gaussian_filter(cloth.astype(np.float32), 1.0)
        R = Image.fromarray((wr * 255 + 0.5).astype(np.uint8), 'L')
        Image.merge('RGBA', [R] + [Image.new('L', R.size, 0)] * 3).save(OUT / 'sorc_region_mask.png')
        print('COMPOSED body: cloth share of the islands', round(float(cloth.sum() / max((gar != 255).sum(), 1)), 3))
        cls[gar == 0] = 1
        cls[(gar == 0) & (mx < 0.2)] = 8                       # black gloves and boots (leather)
        cls[cloth] = 8
        cls[gar == 1] = 2
        cls[np.isin(gar, (5, 6, 4)) & (gold | (sat < 0.15))] = 9
        cls[green] = 11
    else:
        cls[gar == 0] = 1
        cls[(gar == 2) & gold] = 9
        cls[(gar == 2) & ~gold] = 6
        cls[green & (gar == 2)] = 11
    cls[gar == 255] = 0
    Image.fromarray(cls, 'L').save(OUT / f'{pre}_material_classes.png')
