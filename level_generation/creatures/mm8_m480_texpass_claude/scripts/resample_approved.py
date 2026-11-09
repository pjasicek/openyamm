"""Carries the approved (installed) Troll maps onto a texture-pass layout at the same surface points: each texel of the
new layout finds its triangle and barycentrics, takes that point's UV in the installed 2080x1024 body | head atlas and
samples the installed image there (colour and region mask bilinear, metal/roughness nearest: its values are classes).
Gutters are padded with the nearest island texel. The normal map is not carried (tangent frames differ per chart).

Usage: resample_approved.py <layout npz> <out prefix> [colour size 2048] [mask/mr size 1024]
Writes <out prefix>_{basecolor,region_mask,metal_rough}.png and <out prefix>_raster<size>.npz (triangle id per texel).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
import texlib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
layout_path, prefix = sys.argv[1], sys.argv[2]
SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
SMALL = int(sys.argv[4]) if len(sys.argv) > 4 else 1024
layout = np.load(layout_path)
before = np.load(HERE / 'work' / 'lod0_before.npz')
old_uv = before['uv'][before['tri']]
g = Glb(HERE / 'work' / 'before_texpass' / 'mm8_m480.glb')
mat = g.doc['materials'][0]
src = {'basecolor': mat['pbrMetallicRoughness']['baseColorTexture']['index'],
       'metal_rough': mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
       'region_mask': mat['extras']['openyamm_region_mask']['index']}
for kind, size, mode in (('basecolor', SIZE, 'RGB'), ('region_mask', SMALL, 'RGBA'), ('metal_rough', SMALL, 'RGB')):
    raster_path = Path(f'{prefix}_raster{size}.npz')
    if raster_path.exists():
        r = np.load(raster_path)
        tri_id, bary = r['tri_id'], r['bary']
    else:
        tri_id, bary = texlib.raster(layout['uv'], size)
        np.savez_compressed(raster_path, tri_id=tri_id, bary=bary)
    cov, uv = texlib.corresponding_uv(tri_id, bary, old_uv)
    img = np.asarray(g.image(g.doc['textures'][src[kind]]['source']).convert(mode), np.float32)
    values = texlib.nearest(img, uv) if kind == 'metal_rough' else texlib.bilinear(img, uv)
    out = np.zeros((size, size, img.shape[2]), np.float32)
    out[cov] = values
    out = texlib.pad(out, cov)
    Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8), mode).save(f'{prefix}_{kind}.png')
    print('WROTE', f'{prefix}_{kind}.png', f'{cov.mean():.1%} covered')
