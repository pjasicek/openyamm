#!/usr/bin/env python3
"""Approved paint against the new one at the same surface points (texture pass 2026-10-30): area-weighted random
points on the bind mesh, sampled through each layout's UVs (work/uv3d_basilisk.npz and _v2.npz hold the same triangles
in the same order). Zones come from the approved region mask, so a hue change of the new paint shows as a difference
rather than moving the zone. Prints mean sRGB and luminance sd per zone, approved -> new.

Usage: paint_compare.py <approved png> <new png> [<approved png> <new png> ...]   (pairs, e.g. tier A then tier C)
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
W = HERE / 'work'
OLD_MASK = W / 'before_texpass' / 'textures' / 'basilisk_region_mask.png'
N = 400000


def bilinear(img, uv):
    h, w = img.shape[:2]
    x, y = uv[:, 0] * w - 0.5, (1 - uv[:, 1]) * h - 0.5
    x0, y0 = np.clip(np.floor(x).astype(int), 0, w - 2), np.clip(np.floor(y).astype(int), 0, h - 2)
    fx, fy = np.clip(x - x0, 0, 1)[:, None], np.clip(y - y0, 0, 1)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


old, new = np.load(W / 'uv3d_basilisk.npz'), np.load(W / 'uv3d_basilisk_v2.npz')
assert np.allclose(old['xyz'], new['xyz'], atol=1e-5), 'triangles differ between the layouts'
xyz = old['xyz']
area = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
rng = np.random.default_rng(1)
tri = rng.choice(len(area), N, p=area / area.sum())
b = rng.dirichlet((1, 1, 1), N)
pick = lambda uv: (uv[tri] * b[:, :, None]).sum(1)
uv_old, uv_new = pick(old['uv']), pick(new['uv'])
head = (old['head'][tri] * b).sum(1) > 0.5
limb = (old['limb'][tri] * b).sum(1) > 0.5
piece = old['part'][tri]
red = bilinear(np.asarray(Image.open(OLD_MASK).convert('RGBA'), np.float32) / 255, uv_old)[:, 0] > 0.5
zones = {'frill': red & ~head & ~limb, 'mouth/head red': red & head, 'other red': red & ~head & limb,
         'back+flank': ~red & ~head & ~limb, 'legs/tail': ~red & ~head & limb, 'head scales': ~red & head,
         'small pieces': piece > 0}
lum = lambda c: c @ np.array([0.2126, 0.7152, 0.0722])
args = sys.argv[1:]
result = {}
for a, c in zip(args[::2], args[1::2]):
    A = bilinear(np.asarray(Image.open(a).convert('RGB'), np.float32), uv_old)
    C = bilinear(np.asarray(Image.open(c).convert('RGB'), np.float32), uv_new)
    print(f'{Path(a).name} -> {Path(c).name}')
    for z, m in zones.items():
        if m.sum() < 50:
            continue
        ma, mc = A[m].mean(0), C[m].mean(0)
        print(f'  {z:15s} {100 * m.mean():5.1f}%  mean {ma.round(0).astype(int)} -> {mc.round(0).astype(int)}'
              f'  lum sd {lum(A[m]).std():5.1f} -> {lum(C[m]).std():5.1f}'
              f'  p5/p95 lum {np.percentile(lum(A[m]), 5):5.1f}/{np.percentile(lum(A[m]), 95):5.1f} ->'
              f' {np.percentile(lum(C[m]), 5):5.1f}/{np.percentile(lum(C[m]), 95):5.1f}')
        result.setdefault(Path(c).name, {})[z] = {'approved': ma.tolist(), 'new': mc.tolist(),
                                                  'lum_sd': [float(lum(A[m]).std()), float(lum(C[m]).std())]}
(W / 'paint_compare.json').write_text(json.dumps(result, indent=1))
