#!/usr/bin/env python3
"""Pin the texture-pass base colour to the approved tone, per material class (bone 5, membrane 3).

Surface points are sampled by area on LOD0 and looked up in the approved base (installed UVs) and the new base (new
UVs). Per class, a monotonic curve maps the new luminance quantiles onto the approved ones (101 stops, linear between),
blended with the identity by `strength`; each texel's RGB is scaled by curve(lum) / lum, so hue and the ordering of
the new detail stay while mean, contrast and the dark tail follow the approved paint (claude_shared/ramp_match.py does
the same through region ramps; this creature has none). The class's mean chroma (RGB minus luminance) is then shifted
to the approved one (the 4K membrane came out slightly blue). Texels outside the islands keep their padding.
Points count for a class only where the approved class map (installed UVs) agrees: the two paints split bone and
membrane slightly differently along the wing fingers.
Usage: tone_texpass.py <approved dir> <installed uv npz> <new dir> <new uv npz> <strength> <out png>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

W = np.array([0.2126, 0.7152, 0.0722])
approved_dir, old_npz, new_dir, new_npz, strength, out = sys.argv[1:7]
strength = float(strength)
new_dir = Path(new_dir)


def points(npz, n=600000):
    d = np.load(npz)
    x, u = d['xyz'].astype(np.float64), d['uv'].astype(np.float64)
    area = np.linalg.norm(np.cross(x[:, 1] - x[:, 0], x[:, 2] - x[:, 0]), axis=1) / 2
    rng = np.random.default_rng(7)
    face = rng.choice(len(area), n, p=area / area.sum())
    bary = rng.dirichlet([1, 1, 1], n)
    return face, bary


def lookup(img, npz, face, bary):
    u = np.load(npz)['uv'].astype(np.float64)
    uv = (bary[:, :, None] * u[face]).sum(1)
    h, w = img.shape[:2]
    return img[np.clip(((1 - uv[:, 1]) * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]


approved = np.asarray(Image.open(Path(approved_dir) / 'm616_basecolor.png').convert('RGB'), np.float64)
old_classes = np.asarray(Image.open(Path(approved_dir) / 'm616_material_classes.png'))
base = np.asarray(Image.open(new_dir / 'm616_basecolor.png').convert('RGB'), np.float64)
classes = np.asarray(Image.open(new_dir / 'm616_material_classes.png').resize(base.shape[1::-1], Image.NEAREST))
face, bary = points(new_npz)
old_rgb = lookup(approved, old_npz, face, bary)
old_lum = old_rgb @ W
new_lum = lookup(base, new_npz, face, bary) @ W
point_class = lookup(classes, new_npz, face, bary)
old_class = lookup(old_classes, old_npz, face, bary)
lum = base @ W
target = lum.copy()
report = {}
q = np.linspace(0, 100, 101)
for name, c in (('bone', 5), ('membrane', 3)):
    m = (point_class == c) & (old_class == c)
    src, dst = np.percentile(new_lum[m], q), np.percentile(old_lum[m], q)
    src = np.maximum.accumulate(src + np.arange(len(src)) * 1e-6)
    texels = classes == c
    mapped = np.interp(lum[texels], src, dst)
    target[texels] = (1 - strength) * lum[texels] + strength * mapped
    report[name] = dict(points=int(m.sum()),
                        approved_p5_50_95=np.percentile(old_lum[m], [5, 50, 95]).round(1).tolist(),
                        new_p5_50_95=np.percentile(new_lum[m], [5, 50, 95]).round(1).tolist())
scale = np.clip(target / np.maximum(lum, 1.0), 0, 6)
toned = base * scale[..., None]
toned_points = lookup(toned, new_npz, face, bary)
for name, c in (('bone', 5), ('membrane', 3)):
    m = (point_class == c) & (old_class == c)
    shift = (old_rgb[m] - old_lum[m, None]).mean(0) - (toned_points[m] - (toned_points[m] @ W)[:, None]).mean(0)
    toned[classes == c] += shift
    report[name]['chroma_shift'] = shift.round(2).tolist()
toned = np.clip(toned, 0, 255)
Image.fromarray((toned + .5).astype(np.uint8)).save(out)
after = lookup(toned, new_npz, face, bary) @ W
for name, c in (('bone', 5), ('membrane', 3)):
    report[name]['toned_p5_50_95'] = np.percentile(after[point_class == c], [5, 50, 95]).round(1).tolist()
report['strength'] = strength
Path(out).with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
