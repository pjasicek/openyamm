#!/usr/bin/env python3
"""Mean sRGB colour of the native sprites' regions (the targets of the build scripts' TINTS). Each region is a band
of content rows (fractions of the content height from the bottom) and an optional colour test. Prints the pixel
count and mean per region. Usage: measure.py"""
import os

import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')


def warm(c):
    """Yellowed bone: warmer and brighter than the iron (its shaded parts included, so the mean is not biased to
    the highlights)."""
    return (c[..., 0] > c[..., 2] + 20) & (c.mean(-1) > 40)


def not_warm(c):
    return ~warm(c)


def light(c):
    """Grey bone, shaded parts included (the iron around it is below 25)."""
    return c.mean(-1) > 40


def dark(c):
    return c.mean(-1) <= 40


def bright(c):
    return c.mean(-1) > 150


REGIONS = {
    'hngncge2_p546': {'all': (0.0, 1.0, None), 'iron': (0.0, 1.0, not_warm), 'bone': (0.08, 0.92, warm),
                      'top band': (0.92, 1.0, None), 'bottom band': (0.0, 0.08, None)},
    'empty_p546': {'all': (0.0, 1.0, None), 'top band': (0.9, 1.0, None), 'bottom band': (0.0, 0.1, None),
                   'bars': (0.12, 0.88, None)},
    'bonecage_p546': {'all': (0.0, 1.0, None), 'top band': (0.9, 1.0, None), 'bottom band': (0.0, 0.08, None),
                      'bars': (0.55, 0.88, None), 'bone': (0.08, 0.55, light), 'iron low': (0.08, 0.55, dark)},
    'chndlir0_p546': {'all': (0.0, 1.0, None), 'iron': (0.0, 1.0, lambda c: c.mean(-1) < 110),
                      'wax': (0.0, 1.0, lambda c: (c.mean(-1) >= 150) & (c[..., 2] > 90)),
                      'chain': (0.62, 1.0, None)},
}

if __name__ == '__main__':
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
            print(f'{name:16s} {region:12s} {int(mask.sum()):6d} {tuple(mean.round(1))}')
