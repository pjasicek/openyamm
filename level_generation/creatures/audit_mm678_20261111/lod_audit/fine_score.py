#!/usr/bin/env python3
"""Texture-detail score of the audit renders at full render size (512 px), which lod_score.py's switch-size colour
score cannot see: inside both silhouettes (eroded 3 px), the high-pass detail (image minus a 2.5 px Gaussian) of LOD N
against LOD0's. `hf_corr` = correlation of the two detail layers (1 = LOD0's pattern kept; low = scrambled or new
grain); `hf_ratio` = detail energy of LOD N / LOD0 (above 1 = added grain, below = smeared). Worst view of three.
Usage: fine_score.py <split_dir> -> TSV on stdout"""
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, gaussian_filter

VIEWS = ('front', 'q34', 'side')


def load(path):
    rgba = np.asarray(Image.open(path).convert('RGBA'), np.float64)
    grey = rgba[..., :3] @ np.array([0.299, 0.587, 0.114])
    return grey, rgba[..., 3] > 127


def score(a_path, b_path):
    a, a_in = load(a_path)
    b, b_in = load(b_path)
    inside = binary_erosion(a_in & b_in, iterations=3)
    if inside.sum() < 200:
        return np.nan, np.nan
    ha = a - gaussian_filter(a, 2.5)
    hb = b - gaussian_filter(b, 2.5)
    x, y = ha[inside], hb[inside]
    corr = float(np.corrcoef(x, y)[0, 1]) if x.std() > 1e-6 and y.std() > 1e-6 else np.nan
    ratio = float(y.std() / max(x.std(), 1e-6))
    return corr, ratio


split_dir = sys.argv[1]
print('model\tlod\thf_corr\thf_ratio')
for stem in sorted(os.listdir(split_dir)):
    folder = os.path.join(split_dir, stem)
    for level in (1, 2, 3):
        if not all(os.path.exists(os.path.join(folder, f'lod{level}_{v}.png')) for v in VIEWS):
            break
        rows = [score(os.path.join(folder, f'lod0_{v}.png'), os.path.join(folder, f'lod{level}_{v}.png'))
                for v in VIEWS]
        corr = np.nanmin([r[0] for r in rows])
        ratio = max((r[1] for r in rows), key=lambda r: abs(np.log(max(r, 1e-6))))
        print(f'{stem}\t{level}\t{corr:.3f}\t{ratio:.2f}')
