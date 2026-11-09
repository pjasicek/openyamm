#!/usr/bin/env python3
"""Pin a fresh paint to the approved tone (texture pass; generalises mm9_wingedmutant_claude/scripts/wing_tone.py).

Usage: ramp_match.py <before textures dir> <after textures dir> <body> <old uv npz> <new uv npz> <channel,...>
Same surface points on the approved and the new set (npz: `uv` faces x 3 x 2 in one face order, `xyz` for the areas).
For each listed region channel (0..3) and tier, a texel at quantile p of the new base colour's linear luminance targets
the approved tier's colour at the approved quantile p; the 16 stops are the least-squares fit under the shader's lookup,
range [0, 98.5th percentile]. Mean, contrast and hue follow the approved region while the sharper texels stay.
Rewrites <after>/<body>_ramps.json (run after compose). The base colour is not touched."""
import json
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tier_textures as TT

before, after, body, old_npz, new_npz, channels = sys.argv[1:7]
channels = [int(c) for c in channels.split(',')]
before, after = Path(before), Path(after)
W = np.array([0.2126, 0.7152, 0.0722])
N = 600000


def load(folder):
    ramps = json.load(open(folder / f'{body}_ramps.json'))
    entry = ramps['materials'][0]
    base = np.asarray(Image.open(folder / f'{body}_basecolor_graded.png').convert('RGB'), np.float64) / 255
    mask = np.stack([np.asarray(c.resize(base.shape[:2][::-1], Image.BILINEAR), np.float64) / 255
                     for c in Image.open(folder / entry['mask']).convert('RGBA').split()], -1)
    return ramps, entry, base, mask


def sample(img, uv):
    h, w = img.shape[:2]
    x = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    y = np.clip(((1 - uv[:, 1]) * h).astype(int), 0, h - 1)
    return img[y, x]


old, new = np.load(old_npz), np.load(new_npz)
xyz = new['xyz']
area = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
rng = np.random.default_rng(3)
face = rng.choice(len(area), N, p=area / area.sum())
b = rng.dirichlet((1, 1, 1), N)[..., None]
p0, p1 = (old['uv'][face] * b).sum(1), (new['uv'][face] * b).sum(1)
_, entry0, base0, mask0 = load(before)
ramps1, entry1, base1, mask1 = load(after)
lum = TT.srgb_to_linear(sample(base1, p1)) @ W
region = sample(mask1, p1)
for v in ramps1['variants']:
    approved = TT.srgb_to_linear(sample(np.clip(TT.apply(base0, mask0, entry0['ramps'][v]), 0, 1), p0))
    for ch in channels:
        core = region[:, ch] > 0.5
        L, A = lum[core], approved[core]
        A = A[np.argsort(A @ W)]
        rank = np.empty(len(L), np.int64)
        rank[np.argsort(L)] = np.arange(len(L))
        target = A[rank]
        hi = float(np.percentile(L, 98.5))
        x = np.clip(L / hi, 0, 1) * 15
        i0 = np.minimum(x.astype(int), 14)
        f = x - i0
        M = np.zeros((16, 16))
        y = np.zeros((16, 3))
        np.add.at(M, (i0, i0), (1 - f) ** 2)
        np.add.at(M, (i0, i0 + 1), f * (1 - f))
        np.add.at(M, (i0 + 1, i0), f * (1 - f))
        np.add.at(M, (i0 + 1, i0 + 1), f ** 2)
        for c in range(3):
            np.add.at(y[:, c], i0, (1 - f) * target[:, c])
            np.add.at(y[:, c], i0 + 1, f * target[:, c])
        colors = np.clip(np.linalg.solve(M + 1e-6 * len(L) / 16 * np.eye(16), y), 0, 1)
        entry1['ramps'][v][ch] = {'range': [0.0, hi], 'colors': colors.tolist()}
        print(v, ch, 'texels', int(core.sum()), 'range hi', round(hi, 4))
tmp = after / f'{body}_ramps.json.tmp'
json.dump(ramps1, open(tmp, 'w'), indent=1)
os.replace(tmp, after / f'{body}_ramps.json')
