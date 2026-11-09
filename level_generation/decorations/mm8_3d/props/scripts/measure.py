#!/usr/bin/env python3
"""Mean colour (sRGB of the linear mean over opaque pixels) of a review render next to its native x2 sprite.
Usage: measure.py <render.png> <sprite texture name>"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))


def mean(path):
    a = np.asarray(Image.open(path).convert('RGBA'), np.float64)
    c = a[..., :3][a[..., 3] > 200] / 255
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).mean(0)
    s = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.round(s * 255).astype(int), np.round(np.median(c, 0) * 255).astype(int)


render, sprite = sys.argv[1:3]
print('render', *mean(render))
print('sprite', *mean(os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', sprite + '_p8.png')))
