#!/usr/bin/env python3
"""Pad every gutter texel of the head set from its nearest covered texel (last step of head_paint.sh: the patch faces' own
UV islands sat in unpainted space, so their edge texels bled black/white rims). Coverage is dilated by 1 px first so
partially covered edge texels keep their own colour. Usage (project folder): pad_head.py <export glb> <prefix> [...]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb = sys.argv[1]
for p in sys.argv[2:]:
    f = Path(f'textures/{p}_head_basecolor.png')
    img = np.asarray(Image.open(f).convert('RGB'), float)
    N = img.shape[0]
    _, cov = texel_positions(glb, 'PeasantDM4Head', N)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    g = ~cov
    img[g] = img[iy[g], ix[g]]
    Image.fromarray(np.uint8(np.clip(img, 0, 255))).save(f)
    print('PAD_HEAD', p, 'gutter texels', int(g.sum()))
