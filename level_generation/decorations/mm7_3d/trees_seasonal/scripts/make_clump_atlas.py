#!/usr/bin/env python3
"""LOD2 clump cards, step 2: work/<id>/clump<v>_<view>_<pass>.png -> clumps_basecolor.png (1024 RGBA) and
clumps_normal.png. Usage: make_clump_atlas.py <id>. Cells: row 0 = side views of variants 0/1, row 1 = their top views (image top = +v).
Colour and normals are dilated into transparent texels; alpha keeps the 0.5 cutout."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
import common
W = common.load()['work']
base = np.zeros((1024, 1024, 4), np.uint8); nrm = np.zeros((1024, 1024, 3), np.uint8); nrm[...] = (128, 128, 255)
coverage = []
for row, view in enumerate(('side', 'top')):
    for col in range(2):
        a = np.asarray(Image.open(os.path.join(W, f'clump{col}_{view}_albedo.png')).convert('RGBA')).copy()
        n = np.asarray(Image.open(os.path.join(W, f'clump{col}_{view}_normal.png')).convert('RGB')).copy()
        inside = a[..., 3] >= 128
        idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
        a[..., :3] = a[..., :3][idx[0], idx[1]]; n = n[idx[0], idx[1]]
        a[..., 3] = np.where(inside, 255, 0)
        a[:6] = a[-6:] = 0; a[:, :6, 3] = 0; a[:, -6:, 3] = 0       # keep cell borders clear (mip bleed)
        a[:6, :, 3] = 0; a[-6:, :, 3] = 0
        base[row * 512:(row + 1) * 512, col * 512:(col + 1) * 512] = a
        nrm[row * 512:(row + 1) * 512, col * 512:(col + 1) * 512] = n
        coverage.append(round(float(inside.mean()), 3))
Image.fromarray(base, 'RGBA').save(os.path.join(W, 'clumps_basecolor.png'))
Image.fromarray(nrm, 'RGB').save(os.path.join(W, 'clumps_normal.png'))
print('CLUMP atlas coverage per cell (side0, side1, top0, top1)', coverage)
