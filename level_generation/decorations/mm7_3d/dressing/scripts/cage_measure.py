#!/usr/bin/env python3
"""Mean sRGB of the MM7 cage sprites' regions (first x2 frames; rows in x2 pixels from the top of the 512 frame):
chain (above the lid), lid (top disc and its band), bars and hoops (the cage body, figure pixels excluded), bottom
band, and the figure inside (7dec06's skeleton, 7dec07's prisoner: warm pixels in the cage interior columns).
Usage: cage_measure.py"""
import os

import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
ROWS = {'chain': (0, 90), 'lid': (90, 142), 'body': (142, 392), 'bottom': (392, 445)}


def warm(c):
    """Lit figure: clearly warmer than the rusty iron and brighter."""
    return (c[..., 0] > c[..., 2] + 30) & (c.mean(-1) > 45)


for name in ('7dec05a_p1', '7dec06a_p1', '7dec07a_p1'):
    image = np.asarray(Image.open(os.path.join(X2, name + '.png')).convert('RGBA')).astype(float)
    alpha = image[..., 3] > 128
    rows = np.arange(image.shape[0])[:, None] * np.ones((1, image.shape[1]))
    cols = np.ones((image.shape[0], 1)) * np.arange(image.shape[1])[None, :]
    interior = (cols > 185) & (cols < 325) & (rows > 150) & (rows < 400)
    fig = alpha & interior & warm(image[..., :3])
    print(name, 'all', image[alpha][:, :3].mean(0).round(1))
    for key, (a, b) in ROWS.items():
        mask = alpha & (rows >= a) & (rows < b)
        if key == 'body' and not name.startswith('7dec05'):
            mask &= ~fig
        print(f'  {key:8s} {int(mask.sum()):6d} {tuple(image[mask][:, :3].mean(0).round(1))}')
    if not name.startswith('7dec05'):
        print(f'  figure   {int(fig.sum()):6d} {tuple(image[fig][:, :3].mean(0).round(1))}')
        loose = alpha & interior & (image[..., :3].mean(-1) > 30) & (image[..., 0] > image[..., 2] + 12)
        print(f'  fig_wide {int(loose.sum()):6d} {tuple(image[loose][:, :3].mean(0).round(1))}')
