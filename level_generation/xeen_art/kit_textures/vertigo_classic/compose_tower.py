#!/usr/bin/env python3
"""The classic tower kit (2026-11-24): Clouds of Xeen's tower walls (ftowr1/ftowr2) as bays that join seamlessly.

The wall is one seamless tile of big dark blocks (finished/xvatwall, three courses to a storey), so every bay meets
its neighbours and the storeys above by itself, and the corners are the wall (the blocks wrap round). The door (its
pilasters, lintel and the plank door with its iron ring: DOOR, LINTEL, measured on its painting) and the window (by
its outline, as compose_stone.py cuts it) are set into the tile.

Writes finished/<name>.png (x4) and _x2, _x1 for xvtwall, xvtdoor, xvtwin; sheets/tower_facade.png.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
FINISHED = HERE / 'finished'
SHEETS = HERE / 'sheets'
W, H = 512, 1024
# On finished/xvatdoor.png (v1): the pilasters' outer edges at 58 and 452, the lintel across 20-493 in rows 0-85.
DOOR = (58, 452)
LINTEL = (20, 493, 85)


def load(name):
    return np.asarray(Image.open(FINISHED / f'{name}.png').convert('RGB'), float)


def save(rgb, name):
    image = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))
    image.save(FINISHED / f'{name}.png')
    image.resize((W // 2, H // 2), Image.LANCZOS).save(FINISHED / f'{name}_x2.png')
    image.resize((W // 4, H // 4), Image.LANCZOS).save(FINISHED / f'{name}_x1.png')
    print(name, image.size)


def joint(rgb, mask):
    """A thin dark joint round an inserted shape."""
    ring = ndimage.binary_dilation(mask, iterations=2) & ~ndimage.binary_erosion(mask, iterations=1)
    return rgb * (1 - 0.35 * ndimage.gaussian_filter(ring.astype(float), 1.0))[..., None]


def window_mask(source, wall):
    """The window and its stone ring and sill: where the painting differs from the wall's blocks in colour or
    darkness, closed and filled, the largest part, kept round the bay's middle line."""
    lum = source.mean(2)
    dark = lum < np.percentile(wall.mean(2), 3)
    edges = ndimage.gaussian_gradient_magnitude(lum, 1.5) > 14
    mask = ndimage.binary_closing(dark | edges, iterations=12)
    mask[:, :40] = False
    mask[:, W - 40:] = False
    mask[:160] = False
    mask[H - 200:] = False
    mask = ndimage.binary_opening(ndimage.binary_fill_holes(mask), iterations=8)
    labels, count = ndimage.label(mask)
    sizes = ndimage.sum(np.ones_like(labels), labels, range(1, count + 1))
    mask = labels == 1 + int(np.argmax(sizes))
    ys, xs = np.nonzero(mask)
    reach = W // 2 - xs.min()
    mask[:, :W // 2 - reach] = False
    mask[:, W // 2 + reach:] = False
    return mask


def main():
    SHEETS.mkdir(exist_ok=True)
    wall = load('xvatwall')
    save(wall, 'xvtwall')

    door = load('xvatdoor')
    mask = np.zeros((H, W), bool)
    mask[:, DOOR[0]:DOOR[1]] = True
    mask[:LINTEL[2], LINTEL[0]:LINTEL[1]] = True
    bay = wall.copy()
    bay[mask] = door[mask]
    save(joint(bay, mask), 'xvtdoor')

    # The double door's wing (finished/xvatdoorw: the left leaf of the original's braced pair), as it is.
    save(load('xvatdoorw'), 'xvtdoorw')
    source = load('xvatwin')
    mask = window_mask(source, wall)
    ys, xs = np.nonzero(mask)
    print('window outline', xs.min(), ys.min(), xs.max(), ys.max())
    alpha = ndimage.gaussian_filter(ndimage.binary_erosion(mask, iterations=2).astype(float), 1.5)[..., None]
    save(joint(wall * (1 - alpha) + source * alpha, mask), 'xvtwin')

    rows = [['xvtwall', 'xvtwin', 'xvtdoor', 'xvtwall', 'xvtwin', 'xvtwall'],
            ['xvtwall', 'xvtwall', 'xvtwin', 'xvtwall', 'xvtwall', 'xvtwin']]
    out = Image.new('RGB', (W // 2 * 6, H // 2 * 2))
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            out.paste(Image.open(FINISHED / f'{name}.png').resize((W // 2, H // 2), Image.LANCZOS),
                      (c * W // 2, (1 - r) * H // 2))
    out.save(SHEETS / 'tower_facade.png')


if __name__ == '__main__':
    main()
