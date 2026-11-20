#!/usr/bin/env python3
"""Texture set of the MM9 goat (one MM9 skin, no tiers, no region mask): Meshy maps on our UVs, the mouth cavity
painted, class map, normal and ORM. Inputs: meshy/goat_retexture_v1, textures/goat_ao_2k.png, work/uv3d_goat.npz
(dump_uv3d.py with ATTRS=cav_t,cav_low,cav_x). Outputs in textures/: goat_basecolor.png (graded separately),
goat_normal_1k.png, goat_metal_rough_1k.png, goat_material_classes.png."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / 'scripts'))
from compose_common import hsv, raster, pad, paint_cavity, write_maps

T = HERE / 'textures'
M = HERE / 'meshy' / 'goat_retexture_v1'
HOOF_TOP = 0.075
S = 1024
src = Image.open(M / 'texture_urls_0_base_color.png').convert('RGB')
base2k = np.asarray(src if src.size == (2048, 2048) else src.resize((2048, 2048), Image.LANCZOS), np.float32) / 255
tri, f, d = raster(HERE / 'work' / 'uv3d_goat.npz', 2048, ['attr_cav_t', 'attr_cav_low', 'attr_cav_x'])
cov2 = tri >= 0
ti = np.maximum(tri, 0)
cav2 = cov2 & (d['cavity'][ti] == 1)
base2k = paint_cavity(base2k, cov2, cav2, f['attr_cav_t'], f['attr_cav_low'], f['attr_cav_x'])
# Eyes: Meshy painted the whole eye on the skin just in front of the eye piece, which also took an iris: two eyes side by
# side. The painted skin eye sits where the master has it, so the piece becomes a brow bump in the colour of the skin
# around it (per side: the median of the head skin within 3 cm).
dx = np.load(HERE / 'work' / 'uv3d_goat.npz')
tmp = HERE / 'work' / 'uv3d_goat_xyz.npz'
np.savez(tmp, uv=dx['uv'], x=dx['xyz'][..., 0], y=dx['xyz'][..., 1], z=dx['xyz'][..., 2])
_, fx, _ = raster(tmp, 2048, ['x', 'y', 'z'])
P3 = np.stack([fx['x'], fx['y'], fx['z']], -1)
eye2 = cov2 & (d['part'][ti] % 10 == 2) & (P3[..., 2] > 0.72)
midx = 0.0035
for side in (-1, 1):
    m = eye2 & ((P3[..., 0] - midx) * side > 0)
    c = P3[m].mean(0)
    dist = np.linalg.norm(P3 - c, axis=-1)
    ring = cov2 & ~eye2 & (dist < 0.05) & (dist > 0.025) & ((P3[..., 1] - c[1]) > 0)     # behind the eye, away from the paint
    base2k[m] = np.median(base2k[ring], axis=0)
# Meshy embossed the coat with a pebbled wave (8-14 px at 2K, also in its normal map): the HD masters' hair read as
# relief. From a metre it reads as a scaly hide, so that band is damped in the luminance (the hue stays) and in the normal.
DETAIL, SIGMA = 0.45, 7.0
padded = pad(base2k, cov2)
lum = padded.mean(-1) + 1e-3
blur = ndimage.gaussian_filter(lum, SIGMA)
damped = blur + (lum - blur) * DETAIL
ratio = np.where(cov2 & ~cav2, damped / lum, 1.0)
base2k = np.clip(padded * ratio[..., None], 0, 1)
Image.fromarray((pad(base2k, cov2) * 255).astype(np.uint8)).save(T / 'goat_basecolor.png')
tri1, f1, _ = raster(HERE / 'work' / 'uv3d_goat.npz', S, ['head'])
covered = tri1 >= 0
ti1 = np.maximum(tri1, 0)
part = np.where(covered, d['part'][ti1], -1)
cen = d['xyz'].mean(1)[ti1]
cavity = covered & (d['cavity'][ti1] == 1)
piece = covered & (part % 10 == 2)
eyes = np.zeros_like(piece)        # the eye pieces are brow bumps, see above; the eye is painted on the skin
beard = piece & (cen[..., 2] <= 0.72)
hoof = covered & (cen[..., 2] < HOOF_TOP)
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
horn = covered & (cen[..., 2] > 0.86) & (f1['head'] > 0.5) & (h > 22) & (h < 50) & (s > 0.3) & ~piece
coat = covered & ~(cavity | eyes | hoof | horn)
classes = np.zeros((S, S), np.uint8)
classes[coat] = 2
classes[hoof | horn] = 4
classes[eyes] = 6
classes[cavity] = 7
Image.fromarray(classes).save(T / 'goat_material_classes.png')
if (T / 'goat_ao_2k.png').exists():
    def cls_rough(r):
        r = np.where(coat, np.clip(r, 0.7, 0.9), r)
        r = np.where(hoof | horn, 0.5, r)
        r = np.where(eyes, 0.2, r)
        return np.where(cavity, 0.4, r)
    write_maps(M, T, 'goat', covered, cls_rough, S, cov2)
    # the same relief in the normal map, flattened: xy toward 0.5 on the coat
    n1k = np.asarray(Image.open(T / 'goat_normal_1k.png').convert('RGB'), np.float32) / 255
    k = np.where(pad(coat.astype(np.float32), covered) > 0.5, 0.35, 1.0)[..., None]
    n1k[..., :2] = 0.5 + (n1k[..., :2] - 0.5) * k
    Image.fromarray((np.clip(n1k, 0, 1) * 255).astype(np.uint8)).save(T / 'goat_normal_1k.png')
print('COMPOSED', {k: int(m.sum()) for k, m in dict(coat=coat, hoof=hoof, horn=horn, eyes=eyes, beard=beard, cavity=cavity).items()})
