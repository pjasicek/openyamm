"""Carries the approved (installed) maps onto the texture-pass layout at the same surface points: per texel of the new
layout its triangle and barycentrics, then that point's UV in the installed layout; colour, region mask and normal
bilinear, metal/roughness nearest (classes). Gutters padded with the nearest island texel. Also writes the part id per
texel (for per-mesh rules such as wings without AO).
Usage: resample.py [layout npz (texpass.json layout)] [out prefix work/approved]
Writes <prefix>_{basecolor,region_mask,metal_rough,normal_installed}.png, <prefix>_raster<size>.npz, <prefix>_part.png"""
import sys

import numpy as np
from PIL import Image

import tp
import texlib

layout_path = sys.argv[1] if len(sys.argv) > 1 else tp.HERE / tp.CFG['layout']
prefix = sys.argv[2] if len(sys.argv) > 2 else str(tp.HERE / 'work' / 'approved')
layout = np.load(layout_path)
before = np.load(tp.HERE / 'work' / 'lod0_before.npz')
old_uv = before['uv'][before['tri']]
g = tp.Glb(tp.before_glb())
images = tp.body_images(g.doc)
sizes = {'basecolor': 2048, 'region_mask': 1024, 'metal_rough': 1024, 'normal_installed': 2048}
rasters = {}
for kind, size in sizes.items():
    src = images.get('normal' if kind == 'normal_installed' else kind)
    if src is None:
        continue
    if size not in rasters:
        rasters[size] = texlib.raster(layout['uv'], size)
        np.savez_compressed(f'{prefix}_raster{size}.npz', tri_id=rasters[size][0], bary=rasters[size][1])
    tri_id, bary = rasters[size]
    cov, uv = texlib.corresponding_uv(tri_id, bary, old_uv)
    pic = g.image(src)
    mode = 'RGBA' if kind == 'region_mask' else 'RGB'
    img = np.asarray(pic.convert(mode), np.float32)
    values = texlib.nearest(img, uv) if kind == 'metal_rough' else texlib.bilinear(img, uv)
    out = np.zeros((size, size, img.shape[2]), np.float32)
    out[cov] = values
    out = texlib.pad(out, cov)
    Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8), mode).save(f'{prefix}_{kind}.png')
    print('WROTE', f'{prefix}_{kind}.png', pic.size, '->', size, f'{cov.mean():.1%} covered')
tri_id = rasters[2048][0]
part = np.where(tri_id >= 0, layout['part'][np.maximum(tri_id, 0)] + 1, 0).astype(np.uint8)
Image.fromarray(part).save(f'{prefix}_part.png')
