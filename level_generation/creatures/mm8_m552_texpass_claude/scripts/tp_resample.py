"""Carries the approved (installed) maps onto a texture-pass layout at the same surface points: each texel of the new
layout finds its triangle and barycentrics, takes that point's old UV and samples the old image of the triangle's
primitive (its default material): colour, burn map bilinear, region mask bilinear (primitives without a mask: 0),
metal/roughness nearest (classes). Gutters are padded with the nearest island texel. The normal map is not carried
(tangent frames differ per chart).

Usage: tp_resample.py <layout npz> <out prefix> [colour size 2048] [mask/mr/burn size 1024]
Writes <out prefix>_{basecolor,region_mask,metal_rough,burn_map}.png, <out prefix>_raster<size>.npz (triangle id and
barycentrics per texel) and <out prefix>_prim<size>.png is not written (prim per texel = layout prim[tri_id]).
"""
import sys

import numpy as np
from PIL import Image

import tp_common as C
import texlib

cfg = C.config()
layout_path, prefix = sys.argv[1], sys.argv[2]
SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else cfg.get('size', 2048)
SMALL = int(sys.argv[4]) if len(sys.argv) > 4 else 1024
layout = np.load(layout_path)
before = np.load(C.PROJECT / 'work' / 'lod0_before.npz')
old_uv = before['uv'][before['tri']]
prim_of_tri = before['prim']
g = C.Glb(C.before_glb(cfg))
doc = g.doc
mesh = doc['meshes'][C.lod0_mesh_index(doc, cfg['node'])]
sources = {pi: C.material_maps(doc['materials'][mesh['primitives'][pi]['material']]) for pi in cfg['atlas_prims']}
cache = {}


def picture(texture, mode):
    key = (texture, mode)
    if key not in cache:
        cache[key] = np.asarray(g.image(doc['textures'][texture]['source']).convert(mode), np.float32)
    return cache[key]


for kind, size, mode in (('basecolor', SIZE, 'RGB'), ('region_mask', SMALL, 'RGBA'), ('metal_rough', SMALL, 'RGB'),
                         ('burn_map', SMALL, 'RGB')):
    if not any(kind in s for s in sources.values()):
        continue
    raster_path = f'{prefix}_raster{size}.npz'
    try:
        r = np.load(raster_path)
        tri_id, bary = r['tri_id'], r['bary']
    except FileNotFoundError:
        tri_id, bary = texlib.raster(layout['uv'], size)
        np.savez_compressed(raster_path, tri_id=tri_id, bary=bary)
    cov, uv = texlib.corresponding_uv(tri_id, bary, old_uv)
    tprim = prim_of_tri[tri_id[cov]]
    channels = 4 if mode == 'RGBA' else 3
    values = np.zeros((len(uv), channels), np.float32)
    for pi, maps in sources.items():
        sel = tprim == pi
        if kind not in maps or not sel.any():
            continue
        img = picture(maps[kind], mode)
        values[sel] = texlib.nearest(img, uv[sel]) if kind == 'metal_rough' else texlib.bilinear(img, uv[sel])
    out = np.zeros((size, size, channels), np.float32)
    out[cov] = values
    out = texlib.pad(out, cov)
    Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8), mode).save(f'{prefix}_{kind}.png')
    print('WROTE', f'{prefix}_{kind}.png', f'{cov.mean():.1%} covered')
