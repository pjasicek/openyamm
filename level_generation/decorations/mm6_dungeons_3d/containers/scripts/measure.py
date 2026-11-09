#!/usr/bin/env python3
"""Mean sRGB colour of the native sprites' regions (the targets of the build scripts' TINTS): each region is a band
of content rows (fractions of the content height from the bottom) and an optional colour test (low saturation for
rope, hoops and iron). Prints the pixel count and mean per region. Usage: measure.py"""
import os

import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')


def grey(rgb):
    return (rgb.max(-1) - rgb.min(-1)) < 22


def coloured(rgb):
    return ~grey(rgb)


REGIONS = {
    'bag_a_p547': {'body': (0.0, 1.0, coloured), 'rope': (0.0, 1.0, lambda c: grey(c) & (c.mean(-1) > 80))},
    'bag01_p547': {'burlap': (0.0, 1.0, None)},
    'floursac_p547': {'burlap': (0.0, 1.0, None)},
    'bucket_p547': {'wood': (0.0, 0.93, coloured), 'hoop': (0.0, 0.93, grey), 'rim': (0.93, 1.0, None)},
    'trasheap_p547': {'all': (0.0, 1.0, None), 'mound': (0.0, 0.25, None), 'grey': (0.25, 1.0, grey),
                      'warm': (0.25, 1.0, lambda c: coloured(c) & (c[..., 0] > c[..., 2] + 30))},
    'mushrm01_p547': {'cap': (0.80, 1.0, None), 'gills': (0.74, 0.80, None), 'stem': (0.0, 0.73, None)},
    'mushrm02_p547': {'cap': (0.42, 1.0, None), 'stem': (0.08, 0.38, None), 'base': (0.0, 0.08, None)},
    'mushrm03_p547': {'cap': (0.60, 1.0, None), 'ring': (0.45, 0.58, None), 'stem': (0.0, 0.45, None)},
    'mushrm05_p547': {'caps': (0.62, 1.0, lambda c: c.mean(-1) < 200), 'stem': (0.0, 0.6, None)},
    'crysdisc_p549': {'all': (0.0, 1.0, None), 'rim': (0.0, 1.0, lambda c: c.mean(-1) > 90),
                      'crystal': (0.0, 1.0, lambda c: c.mean(-1) <= 90)},
}

for name, regions in REGIONS.items():
    image = np.asarray(Image.open(os.path.join(X2, name + '.png')).convert('RGBA')).astype(np.float64)
    alpha = image[..., 3] > 128
    rows = np.where(alpha.any(1))[0]
    top, bottom = rows[0], rows[-1]
    height = np.arange(image.shape[0])[:, None] * np.ones((1, image.shape[1]))
    height = (bottom - height) / (bottom - top)
    for region, (lo, hi, test) in regions.items():
        mask = alpha & (height >= lo) & (height <= hi)
        if test is not None:
            mask &= test(image[..., :3])
        mean = image[mask][:, :3].mean(0) if mask.any() else np.zeros(3)
        print(f'{name:16s} {region:8s} {int(mask.sum()):6d} {tuple(mean.round(1))}')
