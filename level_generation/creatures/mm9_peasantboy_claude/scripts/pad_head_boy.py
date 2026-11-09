#!/usr/bin/env python3
"""Pad every gutter texel of a head set from its nearest covered texel (coverage of work/head_texel_pos.npz dilated by
1 px, head_texel_pos.py), so island edges never sample dark or unrelated gutter paint (a dotted line along the neck's
UV seam). Last step of head_paint.sh; with HEADPOS=work/head_texel_pos_old.npz ORM=1 it pads the composed old-layout maps
before the transfer (bilinear samples at an old island's edge then stay on its own colour). Usage (project folder): pad_head_boy.py <prefix> ..."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
import os
POS = os.environ.get('HEADPOS', 'work/head_texel_pos.npz')
cov = np.isfinite(np.load(POS)['pos'][..., 0])
cov = ndimage.binary_dilation(cov, iterations=1)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
g = ~cov
for pre in sys.argv[1:]:
    for f in ([f'textures/{pre}_head_basecolor.png'] + ([f'textures/{pre}_head_metal_rough_1k.png'] if os.environ.get('ORM') else [])):
        img = np.asarray(Image.open(f).convert('RGB')).copy()
        if img.shape[0] != g.shape[0]:
            gg = np.asarray(Image.fromarray(np.uint8(g * 255)).resize(img.shape[:2][::-1], Image.NEAREST)) > 0
            _, (jy, jx) = ndimage.distance_transform_edt(gg, return_indices=True)
            img[gg] = img[jy[gg], jx[gg]]
        else:
            img[g] = img[iy[g], ix[g]]
        Image.fromarray(img).save(f)
    print('PAD_HEAD', pre, POS, 'gutter texels', int(g.sum()))
