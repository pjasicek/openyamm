#!/usr/bin/env python3
"""Maps of the texture-quality pass (2026-10-31): compose_bone.py's bone and membrane recipe on the 4K Meshy return
over the new UVs, downsampled once (colour 4K -> 2K, normal 4K -> 1K, Lanczos).

Parts per triangle (wings 1 and 2 hold the membranes) come from work/uv3d.npz by the nearest triangle centre; the
installed LOD0 is the reduced mesh in the same bind space. --soften scales compose_bone.py's ivory blur (0.8 there,
against the grain of the old fragment islands); --ao-strength the AO term (0.1 there).
--crack-fill R: the 4K paint covers the bone with a black crackle network that neither the HD masters (smooth ivory)
nor the approved paint have. Thin dark lines on bone (black-hat of a radius-R disk closing, ramped between --crack-lo
and --crack-hi levels) are filled from the surrounding bone texels (normalised Gaussian, sigma 2 px).
Usage: compose_texpass.py <corners npz> <meshy dir> <ao png> <out dir> [--soften 0.8] [--ao-strength 0.1]
       [--crack-fill 3 --crack-lo 10 --crack-hi 35]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path[:0] = [str(P.parent / 'mm6_gob_claude/scripts'), str(P.parent / 'claude_shared'), str(REPO / 'tools')]
import compose_textures_v2 as C  # noqa: E402
import region_variants as RV  # noqa: E402
import normal_map_convention as NM  # noqa: E402

parser = argparse.ArgumentParser()
for name in ('corners', 'meshy', 'ao', 'out'):
    parser.add_argument(name)
parser.add_argument('--soften', type=float, default=0.8)
parser.add_argument('--ao-strength', type=float, default=0.1)
parser.add_argument('--crack-fill', type=int, default=0)
parser.add_argument('--crack-lo', type=float, default=10)
parser.add_argument('--crack-hi', type=float, default=35)
args = parser.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
S = Path(args.meshy)

corners = np.load(args.corners)
old = np.load(P / 'work/uv3d.npz')
_, nearest_old = cKDTree(old['xyz'].mean(1)).query(corners['xyz'].mean(1))
part_of_face = old['part'][nearest_old]
np.savez(out / 'uv3d_texpass.npz', uv=corners['uv'], xyz=corners['xyz'], part=part_of_face)
part, xyz = C.rasterise({'uv': corners['uv'], 'xyz': corners['xyz'], 'part': part_of_face}, tol=0)
valid = part >= 0

raw = Image.open(S / 'texture_urls_0_base_color.png').convert('RGB')
base = np.asarray(raw.resize((C.SIZE, C.SIZE), Image.Resampling.LANCZOS), np.float32) / 255
lum = base @ RV.LUMA
membrane = np.isin(part, [1, 2]) & (ndimage.gaussian_filter(lum, .8) < .34)
ao = np.asarray(Image.open(args.ao).convert('L'), np.float32) / 255
base *= (1 - args.ao_strength) + args.ao_strength * ndimage.gaussian_filter(ao, 1)[..., None]
base = np.clip(base, 0, 1)
nearest = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
base[~valid] = base[tuple(nearest[:, ~valid])]
# compose_bone.py: soften only the ivory surface and pull it towards 0.75; --soften 0 keeps the tone pull only.
smooth = ndimage.gaussian_filter(base, (args.soften, args.soften, 0)) if args.soften > 0 else base
weight = (~membrane) * np.clip((lum - .15) / .3, 0, 1) * .8
base = base * (1 - weight[..., None]) + np.clip(.75 + .6 * (smooth - .75), 0, 1) * weight[..., None]
crack_share = 0.0
if args.crack_fill:
    r = args.crack_fill
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    level = base @ RV.LUMA * 255
    black_hat = ndimage.grey_closing(level, footprint=xx ** 2 + yy ** 2 <= r * r + .5) - level
    crack = np.clip((black_hat - args.crack_lo) / (args.crack_hi - args.crack_lo), 0, 1) * (valid & ~membrane)
    keep = 1 - crack
    fill = np.stack([ndimage.gaussian_filter(base[..., k] * keep, 2.0) for k in range(3)], -1) \
        / np.maximum(ndimage.gaussian_filter(keep, 2.0), 1e-3)[..., None]
    base = base * keep[..., None] + fill * crack[..., None]
    crack_share = float(crack[valid & ~membrane].mean())
classes = np.zeros(part.shape, np.uint8)
classes[valid] = 5
classes[membrane] = 3
Image.fromarray(classes).resize((1024, 1024), Image.Resampling.NEAREST).save(out / 'm616_material_classes.png')
padded = classes.copy()
padded[~valid] = padded[tuple(nearest[:, ~valid])]
rough = np.where(padded == 3, .91, .67)
spec = np.where(padded == 3, .02, .38)
orm = np.dstack([spec, rough, np.zeros_like(rough)])
Image.fromarray((orm * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS).save(
    out / 'm616_metal_rough.png')
Image.fromarray((base * 255 + .5).astype(np.uint8)).save(out / 'm616_basecolor.png')
normal = np.array(Image.open(S / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024),
                                                                                   Image.Resampling.LANCZOS))
before = NM.measure(normal)
if before < -.1:
    normal[..., 1] = 255 - normal[..., 1]
bone = np.asarray(Image.fromarray((padded == 5).astype(np.uint8) * 255).resize((1024, 1024),
                                                                              Image.Resampling.NEAREST)) > 127
vec = normal.astype(np.float32) / 127.5 - 1
vec[bone, :2] *= .35
vec /= np.maximum(np.linalg.norm(vec, axis=2, keepdims=True), 1e-6)
normal = np.clip((vec + 1) * 127.5 + .5, 0, 255).astype(np.uint8)
Image.fromarray(normal).save(out / 'm616_normal.png')
(out / 'compose.json').write_text(json.dumps(dict(
    meshy_size=raw.size, soften=args.soften, ao_strength=args.ao_strength, crack_fill=args.crack_fill,
    crack_lo=args.crack_lo, crack_hi=args.crack_hi, crack_share=crack_share, normal_before=before,
    normal_after=NM.measure(normal), membrane_texels=float(membrane[valid].mean()),
    classes=np.unique(classes).tolist()), indent=2) + '\n')
print('COMPOSED', raw.size, before, NM.measure(normal), f'membrane {membrane[valid].mean():.1%}')
