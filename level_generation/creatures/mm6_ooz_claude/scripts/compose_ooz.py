#!/usr/bin/env python3
"""Ooze runtime maps from meshy/retexture_v1 (one shared skin for the three tiers):
- base colour 1024: Meshy's map graded with the baked AO (work/ao_body.png, claude_shared/bake_creature_ao.py on
  work/blob_only.blend) by claude_shared/grade_basecolor.py;
- normal 1024 (Meshy); ORM 1024: R specular mask (crease- and AO-darkened), G roughness ROUGH (+-0.05 from Meshy's variation: the slime is wet and
  glossy, the one creature that keeps engine specular), B metallic 0;
- optional native shading transfer (env OOZ_SHADE = amount, 0 = off; claude_shared/native_shading.py, config
  native_shading.json, height mode: the sprites are rendered from an almost level camera, so sprite rows track height):
  the slime takes the native brightness at its texel height (dark underside and lump bases, bright top) times Meshy's
  own lump detail;
- crease/highlight shading from the rest mesh's curvature (scripts/dump_uv3d.py): creases toward black, convex
  up-facing lump tops toward white (user review: more white-ish and black so it reads 3D);
- the whole slime is one region (weight 1), recoloured per tier by scripts/tier_ramps.py from palettes 780/781/782;
- textures/ooz_material_classes.png: 11 (other: slime) on the islands.
The pod has no texels of its own: export_glb.py maps it onto the blob's top surface."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
M = HERE / 'meshy' / 'retexture_v1'
N = 1024
ROUGH = 0.5                      # user: less glossy (was 0.32)
CREASE_AT, CREASE_DARK, HIGHLIGHT = 0.12, 0.8, 0.7   # curvature crease/highlight shading (user: more contrast)
SHADE = float(__import__('os').environ.get('OOZ_SHADE', '0'))
T.mkdir(exist_ok=True)
raw = T / 'ooz_a_basecolor.png'
Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS).save(raw)
ao = Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((N, N), Image.LANCZOS)
ao.save(HERE / 'work' / 'ao_1k.png')
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                str(HERE / 'work' / 'ao_1k.png'), '--ao-strength', '0.6', '--local', '0.4', '--contrast', '1.08',
                '--saturation', '1.1', str(raw)], check=True)
def raster_attrs(data, names):
    """Rest-pose attributes per texel (barycentric over the blob's UV triangles in work/uv3d.npz); NaN outside."""
    out = {n: np.full((N, N) + data[n].shape[2:], np.nan) for n in names}
    for k, uv in enumerate(data['uv']):
        p = np.stack([uv[:, 0] * N, (1 - uv[:, 1]) * N], 1)
        x0, y0 = np.maximum(np.floor(p.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(p.max(0)).astype(int), N - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        ys, xs = np.nonzero(inside)
        for n in names:
            v = data[n][k]
            val = (w0[inside, None] * v[0] + w1[inside, None] * v[1] + w2[inside, None] * v[2]) if v.ndim == 2 else \
                (w0[inside] * v[0] + w1[inside] * v[1] + w2[inside] * v[2])
            out[n][y0 + ys, x0 + xs] = val
    return out


data = np.load(HERE / 'work' / 'uv3d.npz')
attrs = raster_attrs(data, ['xyz', 'curv', 'nz'])
graded = T / 'ooz_a_basecolor_graded.png'
# crevices and highlights (user review: more white-ish and black, read more 3D): concave creases darken toward black,
# convex up-facing lump tops lift toward white, as in the sprites' baked shading
base = np.asarray(Image.open(graded).convert('RGB'), np.float64) / 255
curv, nz = np.nan_to_num(attrs['curv']), np.nan_to_num(attrs['nz'])
crease = np.clip(curv / CREASE_AT, 0, 1) ** 0.8
top = np.clip((-curv - 0.12) / 0.3, 0, 1) * np.clip(nz, 0, 1) ** 1.5
base = base * (1 - CREASE_DARK * crease[..., None])
base = base + (1 - base) * (HIGHLIGHT * top[..., None])
Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)).save(graded)
print('CAVITY crease texels', int((crease > 0.5).sum()), 'highlight texels', int((top > 0.5).sum()))
if SHADE > 0:
    sys.path.insert(0, str(HERE.parent / 'claude_shared'))
    import native_shading as NS
    xyz = attrs['xyz']
    region = ~np.isnan(xyz[..., 0])
    coord = NS.texel_coordinate(np.nan_to_num(xyz), 'height', z_range=(0.0, float(data['xyz'][..., 2].max())))
    profile = json.loads((HERE / 'work' / 'native_shading' / 'profile.json').read_text())
    base = np.asarray(Image.open(graded).convert('RGB'), np.float64) / 255
    NS.shade(base, coord, region, profile, scale=1.0, detail_strength=1.0, detail=NS.detail_of(base), amount=SHADE,
             luminance=profile['regions']['slime']['luminance'])
    Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)).save(graded)
    print('SHADED amount', SHADE, 'texels', int(region.sum()))
Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS).save(T / 'ooz_normal_1k.png')
mr = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS), np.float64) / 255
rough = np.clip(ROUGH + 0.05 * (mr - mr.mean()) / max(mr.std(), 1e-3), ROUGH - 0.12, ROUGH + 0.12)
# R = per-texel specular scale (material extra openyamm_specular_mask): no sheen in the creases and in occlusion, so
# dark creases stay near-black instead of mirroring the sky (user review: black crevices)
spec = np.clip(1 - 0.95 * crease, 0, 1) * (np.asarray(ao, np.float64) / 255) ** 1.5
orm = np.stack([spec, rough, np.zeros_like(rough)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(T / 'ooz_metal_rough_1k.png')
weight = np.ones((N, N))
np.save(HERE / 'work' / 'slime_weight.npy', weight)
Image.fromarray(np.full((N, N), 11, np.uint8), 'L').save(T / 'ooz_material_classes.png')
subprocess.run([sys.executable, str(HERE / 'scripts' / 'tier_ramps.py'), str(T / 'ooz_a_basecolor_graded.png'),
                str(HERE / 'work' / 'slime_weight.npy')], check=True)
print('COMPOSED')
