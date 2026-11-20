"""Carries the approved (installed) maps onto the texture-pass layout at the same surface points: per texel of the new
layout its triangle and barycentrics, then that point's UV in the installed layout; colour, region mask and normal
bilinear, metal/roughness nearest (classes). Gutters padded with the nearest island texel. Also writes the part id per
texel (for per-mesh rules such as wings without AO).
Usage: resample.py [layout npz (texpass.json layout)] [out prefix work/approved] [source glb (installed)]
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
g = tp.Glb(sys.argv[3] if len(sys.argv) > 3 else tp.before_glb())
if len(sys.argv) > 3:   # another build of the same mesh (e.g. a pre-material source): its UVs must be the installed ones
    src_doc = g.doc
    uv_src = np.concatenate([g.accessor(src_doc['meshes'][mi]['primitives'][pi]['attributes']['TEXCOORD_0'])
                             for mi, pi in tp.layout_prims(src_doc)])
    assert np.allclose(uv_src, before['uv'], atol=1e-6), 'source GLB UVs differ from the installed ones'
images = tp.body_images(g.doc)
sets = tp.part_images(g.doc)           # per layout primitive: each texel samples its own primitive's installed image
sizes = {'basecolor': 2048, 'region_mask': 1024, 'metal_rough': 1024, 'normal_installed': 2048}
for kind in ('region_mask', 'metal_rough'):       # the installed size (square, at most 2048)
    if kind in images:
        sizes[kind] = min(2048, max(g.image(images[kind]).size) * (2 if tp.CFG.get('merge_sets') else 1))
for kind in ('emissive', 'occlusion', 'burn'):          # carried as they are (emissive glow masks, separate AO)
    if kind in images:
        sizes[kind] = g.image(images[kind]).size[0]
rasters = {}
for kind, size in sizes.items():
    key = 'normal' if kind == 'normal_installed' else kind
    if images.get(key) is None:
        continue
    if size not in rasters:
        rasters[size] = texlib.raster(layout['uv'], size)
        np.savez_compressed(f'{prefix}_raster{size}.npz', tri_id=rasters[size][0], bary=rasters[size][1])
    tri_id, bary = rasters[size]
    cov, uv = texlib.corresponding_uv(tri_id, bary, old_uv)
    tex_part = layout['part'][tri_id[cov]]
    mode = 'RGBA' if kind == 'region_mask' or (kind == 'burn' and g.image(images['burn']).mode == 'RGBA') else 'RGB'
    out = np.zeros((size, size, 4 if mode == 'RGBA' else 3), np.float32)
    values = np.zeros((int(cov.sum()), out.shape[2]), np.float32)
    for k, part_set in enumerate(sets):
        sel = tex_part == k
        if not sel.any() or part_set.get(key) is None:
            continue
        pic = g.image(part_set[key])
        img = np.asarray(pic.convert(mode), np.float32)
        values[sel] = texlib.nearest(img, uv[sel]) if kind == 'metal_rough' else texlib.bilinear(img, uv[sel])
        if img.shape[2] != out.shape[2]:
            raise SystemExit(f'{kind}: channel count differs between primitives')
    out[cov] = values
    out = texlib.pad(out, cov)
    Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8), mode).save(f'{prefix}_{kind}.png')
    print('WROTE', f'{prefix}_{kind}.png', size, f'{cov.mean():.1%} covered')
tri_id = rasters[2048][0]
part = np.where(tri_id >= 0, layout['part'][np.maximum(tri_id, 0)] + 1, 0).astype(np.uint8)
Image.fromarray(part).save(f'{prefix}_part.png')
