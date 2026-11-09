#!/usr/bin/env python3
"""Paste the transferred head paint (transfer_head_paint.py: work/transfer/<name>_bake.png at 2x) into the head square
(lower-left 0.8 of the set) of the head-set image, box-downsampled once; texels the bake did not reach take the
nearest baked texel. Hands and ear islands outside the square keep their texels.
Usage (project folder): transfer_head_merge.py <image png> ...  (written in place)"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
for path in sys.argv[1:]:
    name = os.path.splitext(os.path.basename(path))[0]
    b = np.asarray(Image.open(f'work/transfer/{name}_bake.png').convert('RGBA')).astype(np.float64)
    rgb = b[..., :3] * (b[..., 3:] / 255.0)
    a = b[..., 3] / 255.0
    H = b.shape[0] // 2
    rgb = rgb.reshape(H, 2, H, 2, 3).sum((1, 3)); a = a.reshape(H, 2, H, 2).sum((1, 3))
    have = a > 0.05
    col = np.where(have[..., None], rgb / np.maximum(a, 1e-6)[..., None], 0)
    _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
    col = col[iy, ix]
    im = np.asarray(Image.open(path).convert('RGB')).copy()
    k = int(round(H * 0.8))
    im[H - k:, :k] = np.clip(col[H - k:, :k], 0, 255).astype(np.uint8)
    Image.fromarray(im).save(path)
    print('XFER_MERGE', name, 'baked texels', int(have.sum()))
