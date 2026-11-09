#!/usr/bin/env python3
"""Row profile and colours of an x2 sprite: per 5 % of the opaque height (bottom to top) the left/right extent and
half-width (map units, relative to the bbox centre) and the mean sRGB of that row band; plus the whole mean.
Usage: small_measure.py <x2 file> <world height of the opaque art> [bands]"""
import sys

import numpy as np
from PIL import Image

X2 = '/home/pjasicek/github/OpenYAMM/assets_dev/engine/decorations_x2/'
path, height = sys.argv[1], float(sys.argv[2])
bands = int(sys.argv[3]) if len(sys.argv) > 3 else 20
im = np.asarray(Image.open(X2 + path).convert('RGBA')).astype(float)
a = im[..., 3] > 128
ys, xs = np.nonzero(a)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
scale = height / (y1 - y0)
cx = (x0 + x1) / 2
print('bbox px', x0, y0, x1, y1, 'units per px', round(scale, 3), 'width units', round((x1 - x0) * scale, 1))
print('mean', np.round(im[a][:, :3].mean(0)).astype(int).tolist(), 'median lum',
      round(float(np.median(im[a][:, :3] @ [0.2126, 0.7152, 0.0722])), 1))
for b in range(bands):
    r1 = y1 - int((y1 - y0) * b / bands); r0 = y1 - int((y1 - y0) * (b + 1) / bands)
    band = a[r0:r1]
    cols = np.nonzero(band.any(0))[0]
    if not len(cols):
        continue
    m = im[r0:r1][band][:, :3].mean(0)
    print(f'{b * 100 // bands:3d}% z {round((b + 0.5) / bands * height, 1):6.1f} left {round((cols.min() - cx) * scale, 1):6.1f} '
          f'right {round((cols.max() + 1 - cx) * scale, 1):6.1f} mean {np.round(m).astype(int).tolist()}')
