#!/usr/bin/env python3
"""Body and head sets from the 4K Meshy paints on our UVs: padded from inside the charts at 4K, cracks repaired, colour downsampled once (body 2K, head 1K per identity), normal and roughness 1K.
No baked AO: a see-through body has no contact shadows to fake. Writes textures/ghost_basecolor.png, ghost_normal_1k.png, ghost_metal_rough_1k.png, ghost_head_<b|c>.png, ghost_head_normal_1k.png,
ghost_head_metal_rough_1k.png. Run from the project folder."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
d = np.load('work/uv_v1.npz')
T = Path('textures'); J = Path('meshy')


def coverage(tris, size):
    im = Image.new('L', (size, size), 0); dr = ImageDraw.Draw(im)
    for t in tris:
        dr.polygon([(float(u * size), float(v * size)) for u, v in t], fill=255)
    return np.asarray(im) > 0


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return img[iy, ix]


def decrack(im, tris, cov, thresh=0.022):
    """As the Lich: hair-thin pale cracks along triangle edges take the colour of the texels beside them."""
    n = im.shape[0]
    m = Image.new('L', (n, n), 0); dr = ImageDraw.Draw(m)
    for t in tris:
        p = [(float(u * n), float(v * n)) for u, v in t]
        dr.line(p + p[:1], fill=255, width=7)
    edge = (np.asarray(m) > 0) & cov
    a = np.asarray(im, np.float32) / 255
    if a.ndim == 2:
        a = a[..., None]
    keep = (~edge).astype(np.float32)
    w = ndimage.gaussian_filter(keep, 3.5)
    near = np.stack([ndimage.gaussian_filter(a[..., c] * keep, 3.5) for c in range(a.shape[2])], -1) / np.maximum(w, 1e-3)[..., None]
    dev = (a - near).max(2)
    fix = edge & (dev > thresh)
    print('decrack', im.shape, 'edge texels', int(edge.sum()), 'fixed', int(fix.sum()))
    a[fix] = near[fix]
    out = (a.clip(0, 1) * 255 + 0.5).astype(np.uint8)
    return out[..., 0] if np.asarray(im).ndim == 2 else out


def load(job, name, mode, size, tris, erode=3, crack=False):
    im = np.asarray(Image.open(J / job / f'texture_urls_0_{name}.png').convert(mode))
    cov = ndimage.binary_erosion(coverage(tris, im.shape[0]), iterations=erode)
    im = pad(im, cov)
    if crack:
        im = decrack(im, tris, cov)
    return np.asarray(Image.fromarray(im).resize((size, size), Image.LANCZOS))


def flip(u):
    o = u.copy(); o[..., 1] = 1 - o[..., 1]; return o


bt = flip(d['Body_uv']); ht = flip(d['Head_uv'])
base = pad(load('retexture_v1', 'base_color', 'RGB', 2048, bt), coverage(bt, 2048)).copy()
c1 = coverage(bt, 1024)
nrm = pad(load('retexture_v1', 'normal', 'RGB', 1024, bt, crack=False), c1).copy()
# the rebuilt sleeve ends' chart (sleeve_repair.py): texels copied from the forearm above the cut; flat normals, a chart's tangent frame does not carry over
for side in 'RL':
    s = np.load(f'work/sleeve_{side}.npz')
    x, y, w, h = [int(v) for v in s['rect']]
    src = s['src'].copy()
    src[..., 1] = 1 - src[..., 1]
    for c in range(3):
        base[y:y + h, x:x + w, c] = ndimage.map_coordinates(base[..., c].astype(np.float32), [src[..., 1] * 2048 - 0.5, src[..., 0] * 2048 - 0.5], order=1)
    nrm[y // 2:(y + h) // 2, x // 2:(x + w) // 2] = (128, 128, 255)
# pale specks Meshy left on the dark upper robe (small blobs far above their surroundings), filled from around them
lumb = base.astype(np.float32) @ np.array([0.3, 0.59, 0.11]) / 255
rs_ = d['Body_robe_s'][d['Body_idx']].mean(1)
rc = coverage(bt[(d['Body_part'] == 1) & (rs_ > 0.055)], 2048)      # below the belt: its knotwork is meant to be pale
sp = rc & (lumb - ndimage.median_filter(lumb, size=41) > 0.28)
sp = ndimage.binary_dilation(sp, iterations=3) & rc
keep_ = (~sp).astype(np.float32); w_ = np.maximum(ndimage.gaussian_filter(keep_, 6), 1e-3)
for c in range(3):
    base[..., c][sp] = (ndimage.gaussian_filter(base[..., c].astype(np.float32) * keep_, 6) / w_)[sp].clip(0, 255).astype(np.uint8)
print('specks', int(sp.sum()))
Image.fromarray(base).save(T / 'ghost_basecolor.png')
Image.fromarray(nrm).save(T / 'ghost_normal_1k.png')
r = pad(load('retexture_v1', 'roughness', 'L', 1024, bt, crack=False), c1)
Image.merge('RGB', [Image.new('L', (1024, 1024), 255), Image.fromarray(np.maximum(r, 150).astype(np.uint8)), Image.new('L', (1024, 1024), 0)]).save(T / 'ghost_metal_rough_1k.png')
h1 = coverage(ht, 1024)
for k in ('b', 'c'):
    Image.fromarray(pad(load(f'head_retexture_{k}', 'base_color', 'RGB', 1024, ht), h1)).save(T / f'ghost_head_{k}.png')
Image.fromarray(pad(load('head_retexture_b', 'normal', 'RGB', 1024, ht, crack=False), h1)).save(T / 'ghost_head_normal_1k.png')
r = pad(load('head_retexture_b', 'roughness', 'L', 1024, ht, crack=False), h1)
Image.merge('RGB', [Image.new('L', (1024, 1024), 255), Image.fromarray(np.maximum(r, 170).astype(np.uint8)), Image.new('L', (1024, 1024), 0)]).save(T / 'ghost_head_metal_rough_1k.png')
print('COMPOSE body %.1f%% head %.1f%%' % (100 * coverage(bt, 2048).mean(), 100 * h1.mean()))
