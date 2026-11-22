#!/usr/bin/env python3
"""A6 (2026-11-21, session 15): give `xafield` a soft graded alpha for translucent use (D5's Barrier curtain,
merge point 23's outdoor `translucent: true`; DD-16's and XD-19's indoor fields at `translucent: 0.5`).

The colour stays as it is; the alpha follows the light: the bright hex lines and lightning near ALPHA_HI, the dark hex
cells near ALPHA_LO. ALPHA_LO stays well above the cut-outs (outdoor faces cut texels at alpha 0.1 or below, indoor
faces cut alpha 0), so every opaque use of the texture (D6's Alamar walls) still draws whole, in its own colour.

    field_alpha.py            # writes finished/xafield.png, _x2.png, _x1.png (originals kept as *_pre_alpha.png)
                              # and the master copy in assets_source/worlds/xeen/textures_x4/xafield.png
"""
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
FINISHED = ROOT / 'level_generation/xeen_art/kit_textures/landmarks/finished'
SOURCE_COPY = ROOT / 'assets_source/worlds/xeen/textures_x4/xafield.png'
ALPHA_LO = 0.45
ALPHA_HI = 0.95


def keep(path):
    backup = path.with_name(path.stem + '_pre_alpha.png')
    if not backup.exists():
        shutil.copy2(path, backup)
    return backup


def graded(rgb):
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    low, high = np.percentile(luma, [5, 99])
    t = np.clip((luma - low) / (high - low), 0.0, 1.0)
    t = np.sqrt(t * t * (3.0 - 2.0 * t))
    return ALPHA_LO + (ALPHA_HI - ALPHA_LO) * t


def reduce(rgba):
    h, w = rgba.shape[0] // 2, rgba.shape[1] // 2
    return rgba.reshape(h, 2, w, 2, 4).mean(axis=(1, 3))


def save(array, path):
    Image.fromarray(np.clip(array + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(path)


def main():
    x4_path = FINISHED / 'xafield.png'
    original = keep(x4_path)
    for suffix in ('_x2', '_x1'):
        keep(FINISHED / f'xafield{suffix}.png')
    rgb = np.asarray(Image.open(original).convert('RGB'), float)
    rgba = np.dstack([rgb, graded(rgb) * 255.0])
    save(rgba, x4_path)
    x2 = reduce(rgba)
    save(x2, FINISHED / 'xafield_x2.png')
    save(reduce(x2), FINISHED / 'xafield_x1.png')
    shutil.copy2(x4_path, SOURCE_COPY)
    a = rgba[..., 3] / 255.0
    print('alpha min %.3f mean %.3f max %.3f; p10 %.3f p50 %.3f p90 %.3f' % (
        a.min(), a.mean(), a.max(), *np.percentile(a, [10, 50, 90])))


if __name__ == '__main__':
    main()
