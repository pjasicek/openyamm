#!/usr/bin/env python3
"""Body and head sets from the 4K Meshy paints on our UVs: padded from inside the charts at 4K, cracks repaired, colour downsampled once (body 2K, head 1K), normal and roughness 1K.
No baked AO: a see-through body has no contact shadows to fake. Writes textures/banshee_basecolor.png, banshee_normal_1k.png, banshee_metal_rough_1k.png, banshee_head_a.png, banshee_head_normal_1k.png, banshee_head_metal_rough_1k.png. Run from the project folder."""
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
    """Hair-thin pale cracks along triangle edges take the colour of the texels beside them."""
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
nrm = pad(load('retexture_v1', 'normal', 'RGB', 1024, bt), c1).copy()
Image.fromarray(base).save(T / 'banshee_basecolor.png')
Image.fromarray(nrm).save(T / 'banshee_normal_1k.png')
r = pad(load('retexture_v1', 'roughness', 'L', 1024, bt), c1)
Image.merge('RGB', [Image.new('L', (1024, 1024), 255), Image.fromarray(np.maximum(r, 150).astype(np.uint8)), Image.new('L', (1024, 1024), 0)]).save(T / 'banshee_metal_rough_1k.png')
h1 = coverage(ht, 1024)
Image.fromarray(pad(load('head_retexture_a', 'base_color', 'RGB', 1024, ht), h1)).save(T / 'banshee_head_a.png')
Image.fromarray(pad(load('head_retexture_a', 'normal', 'RGB', 1024, ht), h1)).save(T / 'banshee_head_normal_1k.png')
r = pad(load('head_retexture_a', 'roughness', 'L', 1024, ht), h1)
Image.merge('RGB', [Image.new('L', (1024, 1024), 255), Image.fromarray(np.maximum(r, 170).astype(np.uint8)), Image.new('L', (1024, 1024), 0)]).save(T / 'banshee_head_metal_rough_1k.png')
print('COMPOSE body %.1f%% head %.1f%%' % (100 * coverage(bt, 2048).mean(), 100 * h1.mean()))
