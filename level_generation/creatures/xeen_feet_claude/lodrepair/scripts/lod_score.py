"""Score each LOD switch as the player sees it: the previous level and the new level, downsampled to the size at
which the game makes that switch (LOD1 450 px, LOD2 180 px, LOD3 72 px), compared per pixel.

outline = changed silhouette pixels / union silhouette pixels (%), colour = mean RGB difference inside the union (0-255),
worst view of front / three-quarter / side. Usage: lod_score.py <split_dir> -> TSV on stdout.
"""
import os
import sys

import numpy as np
from PIL import Image

SWITCH_PIXELS = {1: 450, 2: 180, 3: 72}
VIEWS = ('front', 'q34', 'side')
BACKGROUND = np.array([120, 120, 128], dtype=np.float64)


def at_size(path, size):
    image = Image.open(path).convert('RGBA').resize((size, size), Image.LANCZOS)
    rgba = np.asarray(image, dtype=np.float64)
    alpha = rgba[..., 3:] / 255.0
    return rgba[..., :3] * alpha + BACKGROUND * (1 - alpha), alpha[..., 0]


def compare(a_path, b_path, size):
    a_rgb, a_alpha = at_size(a_path, size)
    b_rgb, b_alpha = at_size(b_path, size)
    a_in, b_in = a_alpha > 0.5, b_alpha > 0.5
    union = a_in | b_in
    if union.sum() == 0:
        return 0.0, 0.0
    outline = 100.0 * (a_in ^ b_in).sum() / union.sum()
    colour = np.abs(a_rgb - b_rgb).mean(axis=2)[union].mean()
    return outline, colour


split_dir = sys.argv[1]
print('model\tlod\tswitch_px\toutline_pct\tcolour_diff\tvs_lod0_outline\tvs_lod0_colour')
for stem in sorted(os.listdir(split_dir)):
    folder = os.path.join(split_dir, stem)
    level = 1
    while all(os.path.exists(os.path.join(folder, f'lod{level}_{v}.png')) for v in VIEWS) and level in SWITCH_PIXELS:
        size = SWITCH_PIXELS[level]
        try:
            step = [compare(os.path.join(folder, f'lod{level - 1}_{v}.png'),
                            os.path.join(folder, f'lod{level}_{v}.png'), size) for v in VIEWS]
            base = [compare(os.path.join(folder, f'lod0_{v}.png'), os.path.join(folder, f'lod{level}_{v}.png'), size)
                    for v in VIEWS]
        except Exception as error:
            print(f'{stem}\tLOD{level}\t{error}', file=sys.stderr)
            break
        print(f'{stem}\t{level}\t{size}\t{max(s[0] for s in step):.1f}\t{max(s[1] for s in step):.1f}\t'
              f'{max(b[0] for b in base):.1f}\t{max(b[1] for b in base):.1f}')
        level += 1
