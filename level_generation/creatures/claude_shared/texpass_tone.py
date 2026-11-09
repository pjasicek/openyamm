#!/usr/bin/env python3
"""Tone check of a texture pass: the same surface points on the approved and the new texture set, per tier and region.

Usage: texpass_tone.py <before textures dir> <after textures dir> <body> <old uv npz> <new uv npz> [out json]
Both npz hold `uv` (faces x 3 x 2, same face order) and `xyz`-independent areas come from `xyz` of the new one. Each tier
goes through its ramps (the engine rule, tier_textures.py) on <body>_basecolor_graded.png + the region mask of its set.
Points are grouped by the region of the NEW mask (R, G, B, A, none); prints mean sRGB, luminance sd and the mean absolute
difference, and the fine detail (RMS of luminance minus a blur) for sharpness."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tier_textures as TT

before, after, body, old_npz, new_npz = sys.argv[1:6]
W = np.array([0.2126, 0.7152, 0.0722])


def tiers(folder):
    folder = Path(folder)
    ramps = json.load(open(folder / f'{body}_ramps.json'))
    entry = ramps['materials'][0]
    base = np.asarray(Image.open(folder / f'{body}_basecolor_graded.png').convert('RGB'), np.float64) / 255
    mask = np.stack([np.asarray(c.resize(base.shape[:2][::-1], Image.BILINEAR), np.float64) / 255
                     for c in Image.open(folder / entry['mask']).convert('RGBA').split()], -1)
    return {v: np.clip(TT.apply(base, mask, entry['ramps'][v]), 0, 1) for v in ramps['variants']}, mask


def sample(img, uv):
    h, w = img.shape[:2]
    x = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    y = np.clip(((1 - uv[:, 1]) * h).astype(int), 0, h - 1)
    return img[y, x]


old, new = np.load(old_npz), np.load(new_npz)
uv0, uv1, xyz = old['uv'], new['uv'], new['xyz']
area = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
rng = np.random.default_rng(1)
n = 400000
face = rng.choice(len(area), n, p=area / area.sum())
b = rng.dirichlet((1, 1, 1), n)[..., None]
p0 = (uv0[face] * b).sum(1)
p1 = (uv1[face] * b).sum(1)
t0, m0 = tiers(before)
t1, m1 = tiers(after)
region = sample(m1, p1)
label = np.where(region.max(1) > 0.5, region.argmax(1), 4)
report = {}
for v in t0:
    c0, c1 = sample(t0[v], p0), sample(t1[v], p1)
    for r in sorted(set(label.tolist())):
        s = label == r
        l0, l1 = c0[s] @ W, c1[s] @ W
        row = {'share_pct': round(100 * s.mean(), 1),
               'approved_rgb': [round(float(x) * 255) for x in c0[s].mean(0)],
               'new_rgb': [round(float(x) * 255) for x in c1[s].mean(0)],
               'approved_sd': round(float(l0.std()) * 255, 1), 'new_sd': round(float(l1.std()) * 255, 1),
               'approved_p5_p95': [round(float(np.percentile(l0, q)) * 255) for q in (5, 95)],
               'new_p5_p95': [round(float(np.percentile(l1, q)) * 255) for q in (5, 95)]}
        report[f'{v}/{"RGBA-"[r]}'] = row
        print(v, 'RGBA-'[r], row)
if len(sys.argv) > 6:
    json.dump(report, open(sys.argv[6], 'w'), indent=1)
