#!/usr/bin/env python3
"""Shared textures of the great-tree crown (shared/):

 - leaves_basecolor.png (2048 RGBA) / leaves_normal.png (2048 RGB): 2 x 2 cells of 1024 px, each a spray cluster for
   a ~2.4 m card: 11-14 MM8 maple sprays (the green cells 0-7 of the MM8 broadleaf batch's shared atlas, copied into
   source/mm8_leaves_*.png) scaled to ~0.85 m each (leaves ~18-24 cm, the great tree's leaves stay leaf-sized),
   rotated and scattered in a ragged disc, larger sprays first so smaller ones lie on top. Each spray is recoloured
   to a cool deep green (BASE_SRGB, per-spray hue/value jitter kept low), keeping the leaf's own luminance (veins,
   folds) and a little of its per-channel variation; tangent normals are rotated with their spray. RGB and normals
   are dilated into transparent texels.
 - bark_basecolor.png: the Xeen trunk texture xdbark (byte copy of assets_source/worlds/xeen/textures_x4/xdbark.png,
   512 x 1024, read only); bark_normal.png: a tangent normal map derived from its blurred luminance (wrap-around
   filters, so it tiles like the colour).
 - atlas.json: per cell the alpha-weighted mean linear colour and coverage (common.tints()).
Usage: make_shared.py"""
import json, math, os, shutil
import numpy as np
from PIL import Image
from scipy import ndimage
import common

OUT = common.SHARED
os.makedirs(OUT, exist_ok=True)
lin, srgb = common.lin, common.srgb
CELL = 1024
SRC_CELL = 512
BASE_SRGB = np.array([80, 165, 120]) / 255.0    # cool green: COLOR_0 (tint x occlusion) darkens it in place
rng = np.random.default_rng(2323)

# ---------------------------------------------------------------- leaves
src = np.asarray(Image.open(os.path.join(common.SOURCE, 'mm8_leaves_basecolor.png')).convert('RGBA')).astype(np.float32) / 255
src_n = np.asarray(Image.open(os.path.join(common.SOURCE, 'mm8_leaves_normal.png')).convert('RGB')).astype(np.float32) / 255


def source_cell(k):
    row, col = divmod(k, 4)
    sl = (slice(row * SRC_CELL, (row + 1) * SRC_CELL), slice(col * SRC_CELL, (col + 1) * SRC_CELL))
    return src[sl], src_n[sl]


def recolour(rgba, base, keep=0.15):
    """base x (luminance ratio x (1 - keep) + per-channel ratio x keep) against the spray's own mean (linear)."""
    c = lin(rgba[..., :3]); m = rgba[..., 3] > 0.5
    mean = c[m].mean(0)
    lum = c @ [0.2126, 0.7152, 0.0722]; mlum = float(mean @ [0.2126, 0.7152, 0.0722])
    ratio = ((lum / mlum) ** 1.25)[..., None]          # a little more value contrast (veins, folds)
    per = c / np.maximum(mean, 1e-4)
    out = lin(base) * (ratio * (1 - keep) + per * keep)
    return np.concatenate([srgb(np.clip(out, 0, 1)), rgba[..., 3:]], 2)


def rotate(img, angle, scale, mode):
    size = int(round(SRC_CELL * scale))
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), mode).resize((size, size), Image.LANCZOS)
    return np.asarray(im.rotate(angle, resample=Image.BICUBIC, expand=True)).astype(np.float32) / 255


atlas = np.zeros((2048, 2048, 4), np.float32)
normals = np.zeros((2048, 2048, 3), np.float32); normals[...] = (0.5, 0.5, 1.0)
meta = {'grid': common.GRID, 'cells': []}
for cell in range(common.GRID * common.GRID):
    row, col = divmod(cell, common.GRID)
    acc = np.zeros((CELL, CELL, 4), np.float32); accn = np.zeros((CELL, CELL, 3), np.float32); accn[...] = (0.5, 0.5, 1.0)
    count = int(rng.integers(17, 21))
    sprays = []
    for k in range(count):
        a = rng.uniform(0, 2 * math.pi); rad = 0.33 * CELL * math.sqrt(rng.uniform(0.0, 1.0))
        sprays.append((rng.uniform(0.62, 0.78), (CELL / 2 + rad * math.cos(a), CELL / 2 + rad * math.sin(a)),
                       rng.uniform(0, 360), int(rng.integers(8))))
    sprays.sort(key=lambda s: -s[0])                # larger sprays below, smaller ones on top
    for order, (scale, (cx, cy), angle, k) in enumerate(sprays):
        rgba, nrm = source_cell(k)
        depth = 0.78 + 0.27 * order / max(count - 1, 1)     # sprays underneath darker: the cluster's own depth
        hue = np.array([rng.uniform(0.94, 1.06), 1.0, rng.uniform(0.92, 1.08)]) * rng.uniform(0.95, 1.05) * depth
        rgba = recolour(rgba, np.clip(BASE_SRGB * hue, 0, 1))
        r = rotate(rgba, angle, scale, 'RGBA')
        n = rotate(nrm, angle, scale, 'RGB')
        # rotate the tangent normals with the spray (PIL turns counter-clockwise; normal map y is up)
        t = math.radians(angle); x = n[..., 0] * 2 - 1; y = n[..., 1] * 2 - 1
        n[..., 0] = (x * math.cos(t) - y * math.sin(t)) * 0.5 + 0.5
        n[..., 1] = (x * math.sin(t) + y * math.cos(t)) * 0.5 + 0.5
        h, w = r.shape[:2]; x0 = int(cx - w / 2); y0 = int(cy - h / 2)
        xs, ys = max(x0, 0), max(y0, 0); xe, ye = min(x0 + w, CELL), min(y0 + h, CELL)
        piece = r[ys - y0:ye - y0, xs - x0:xe - x0]; pn = n[ys - y0:ye - y0, xs - x0:xe - x0]
        al = (piece[..., 3:] > 0.5).astype(np.float32)
        acc[ys:ye, xs:xe, :3] = acc[ys:ye, xs:xe, :3] * (1 - al) + piece[..., :3] * al
        acc[ys:ye, xs:xe, 3:] = np.maximum(acc[ys:ye, xs:xe, 3:], piece[..., 3:])
        accn[ys:ye, xs:xe] = accn[ys:ye, xs:xe] * (1 - al) + pn * al
    border = 16                                     # keep the cell border clear (mip bleed between cells)
    acc[:border, :, 3] = acc[-border:, :, 3] = 0; acc[:, :border, 3] = acc[:, -border:, 3] = 0
    inside = acc[..., 3] >= 0.5
    idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
    acc[..., :3] = acc[..., :3][idx[0], idx[1]]; accn = accn[idx[0], idx[1]]
    atlas[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL] = acc
    normals[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL] = accn
    mean = lin(acc[..., :3][inside]).mean(0)
    meta['cells'].append({'group': 'cool_green', 'sprays': count, 'coverage': round(float(inside.mean()), 4),
                          'mean_linear': [float(v) for v in mean]})
    print('CELL', cell, 'sprays', count, 'coverage', round(float(inside.mean()), 3),
          'mean sRGB', (srgb(mean) * 255).round(1).tolist())
Image.fromarray((atlas * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'leaves_basecolor.png'))
Image.fromarray((normals * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'leaves_normal.png'))
prev = Image.new('RGBA', (1024, 1024), (40, 44, 52, 255))
prev.alpha_composite(Image.open(os.path.join(OUT, 'leaves_basecolor.png')).resize((1024, 1024), Image.LANCZOS))
prev.convert('RGB').save(os.path.join(OUT, 'atlas_preview.png'))

# ---------------------------------------------------------------- bark: the trunk's xdbark, plus a derived normal map
shutil.copyfile(common.XDBARK, os.path.join(OUT, 'bark_basecolor.png'))
bark = np.asarray(Image.open(common.XDBARK).convert('RGB')).astype(np.float32) / 255
height = ndimage.gaussian_filter(lin(bark) @ [0.2126, 0.7152, 0.0722], 1.5, mode='wrap')
height = height / max(float(height.max()), 1e-6)
STRENGTH = 6.0
dx = ndimage.sobel(height, 1, mode='wrap') / 8 * STRENGTH
dy = ndimage.sobel(height, 0, mode='wrap') / 8 * STRENGTH
n = np.stack([-dx, dy, np.ones_like(dx)], 2)          # image y runs down; OpenGL normal maps have +y up
n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'bark_normal.png'))
meta['bark_mean_linear'] = [float(v) for v in lin(bark).reshape(-1, 3).mean(0)]
json.dump(meta, open(os.path.join(OUT, 'atlas.json'), 'w'), indent=1)
print('BARK', bark.shape, 'mean sRGB', (srgb(np.array(meta['bark_mean_linear'])) * 255).round(1).tolist())
