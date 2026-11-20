#!/usr/bin/env python3
"""Opaque foliage textures for the crown shells: shared/<atlas>_shell.png (RGB, same layout and cells as the leaf or
needle atlas). Only foliage texels are kept (alpha >= 0.5, minus the twig and stem strokes: the leaf atlas draws twigs
in one colour (61, 48, 31); the needle atlas's twigs and buds are the texels redder than green), then every other
texel takes the nearest foliage texel and a light blur softens the mosaic. A shell mapped onto most of a cell then
reads as a continuous leaf mass, not as magnified dark twig bands. Usage: make_shell_atlas.py [leaves] [needles]"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
import common
for name in sys.argv[1:] or ['leaves', 'needles']:
    src = np.asarray(Image.open(common.shared_path(f'{name}_basecolor.png')).convert('RGBA')).astype(np.int32)
    rgb, alpha = src[..., :3], src[..., 3]
    foliage = alpha >= 128
    if name == 'leaves':
        twig = np.abs(rgb - np.array([61, 48, 31])).max(-1) <= 8
    else:
        twig = rgb[..., 0] > rgb[..., 1]
    keep = foliage & ~twig
    idx = ndimage.distance_transform_edt(~keep, return_distances=False, return_indices=True)
    out = rgb[idx[0], idx[1]].astype(np.float32)
    out = np.stack([ndimage.gaussian_filter(out[..., c], 1.2) for c in range(3)], -1)
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), 'RGB').save(common.shared_path(f'{name}_shell.png'))
    lum = out @ np.array([0.2126, 0.7152, 0.0722])
    print('SHELL ATLAS', name, 'foliage kept', round(float(keep.mean()), 3), 'luminance p1/p5/p50',
          np.percentile(lum, [1, 5, 50]).round(0))
