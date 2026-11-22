#!/usr/bin/env python3
"""A6 (2026-11-20): re-cut a cutout texture to hard alpha (0/255) with the transparent texels' colour filled from the
nearest opaque texel, so no fringe colour (magenta, black) bleeds in through filtering or mip levels.

    recut.py <finished x4 png> [<finished x2 png>]

The x4 master keeps its alpha mask (thresholded at 128) and gets its hidden colour filled; the x2 is made again from
the new x4: coverage of each 2x2 block >= 0.5 is opaque, colour the mean of the block's opaque texels, then filled.
The originals are kept beside them as <name>_pre_recut.png."""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def fill(rgb, opaque):
    _, (iy, ix) = ndimage.distance_transform_edt(~opaque, return_indices=True)
    return rgb[iy, ix]


def recut_x4(path):
    a = np.array(Image.open(path).convert('RGBA'))
    opaque = a[..., 3] >= 128
    rgb = fill(a[..., :3], opaque)
    return np.dstack([rgb, np.where(opaque, 255, 0)]).astype(np.uint8)


def make_x2(x4):
    h, w = x4.shape[0] // 2, x4.shape[1] // 2
    blocks = x4.reshape(h, 2, w, 2, 4).astype(float)
    weight = (blocks[..., 3] > 0).astype(float)
    count = weight.sum(axis=(1, 3))
    opaque = count >= 2
    colour = (blocks[..., :3] * weight[..., None]).sum(axis=(1, 3)) / np.maximum(count, 1)[..., None]
    colour = np.where(count[..., None] > 0, colour, blocks[..., :3].mean(axis=(1, 3)))
    rgb = fill(np.clip(colour + 0.5, 0, 255).astype(np.uint8), opaque)
    return np.dstack([rgb, np.where(opaque, 255, 0)]).astype(np.uint8)


def keep(path):
    backup = path.with_name(path.stem + '_pre_recut.png')
    if not backup.exists():
        shutil.copy2(path, backup)


def main():
    x4_path = Path(sys.argv[1])
    keep(x4_path)
    x4 = recut_x4(x4_path)
    Image.fromarray(x4, 'RGBA').save(x4_path)
    print(x4_path, 'opaque', int((x4[..., 3] == 255).sum()), 'clear', int((x4[..., 3] == 0).sum()))
    if len(sys.argv) > 2:
        x2_path = Path(sys.argv[2])
        keep(x2_path)
        x2 = make_x2(x4)
        Image.fromarray(x2, 'RGBA').save(x2_path)
        print(x2_path, 'opaque', int((x2[..., 3] == 255).sum()), 'clear', int((x2[..., 3] == 0).sum()))


if __name__ == '__main__':
    main()
