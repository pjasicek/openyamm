#!/usr/bin/env python3
"""The scree's regions: the scree floor cut by every block standing on it (terraces, ridges, talus, the stair; not the
arch, whose slabs hang 300+ over it), each region with the scree slopes whose feet lie in it (a fall must lead back
up). Usage: python3 level_generation/projects/xeen/p3/scree_regions.py"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402
import notes as N  # noqa: E402

plats = gen.ROOMS['rooms'][0]['platforms']
bowl = N.mask([gen.BOWL])
block = N.mask([gen.foot(p) for p in plats if p.get('base', 0) < 200 and not p['id'].endswith('_scree')])
free = bowl & ~block
free = ndimage.binary_erosion(free, iterations=2)          # 32 units: the party's girth
lab, n = ndimage.label(free)
feet = []
for p in plats:
    if p['id'].endswith('_scree'):
        f = gen.foot(p)
        b = ((f[1][0] + f[2][0]) / 2, (f[1][1] + f[2][1]) / 2)
        x, y = N.to_px(b)
        feet.append((p['id'], lab[int(y), int(x)]))
print('slope feet regions', feet)
sizes = ndimage.sum(free, lab, range(1, n + 1)) * N.RES * N.RES / 1e6
for i, s in enumerate(sizes, 1):
    if s > 0.05:
        print(f'region {i}: {s:.2f} M', 'slopes', [f for f, r in feet if r == i])
from PIL import Image
rng = np.random.default_rng(3)
cols = rng.integers(60, 255, (n + 1, 3)).astype(np.uint8)
cols[0] = 0
img = cols[lab]
img[block & bowl] = (90, 90, 90)
for p in plats:
    if p['id'].endswith('_scree'):
        for v in gen.foot(p):
            x, y = N.to_px(v)
            img[max(0, int(y) - 3):int(y) + 3, max(0, int(x) - 3):int(x) + 3] = (255, 255, 255)
Image.fromarray(img).save(str(pathlib.Path(_REPO_ROOT, 'output/studio_cal/p3') / 'pics/scree_regions.png'))
for i, s in enumerate(sizes, 1):
    if s > 0.05:
        ys, xs = np.nonzero(lab == i)
        print(i, 'centre', int(xs.mean() * N.RES - N.HALF), int(N.HALF - ys.mean() * N.RES))
