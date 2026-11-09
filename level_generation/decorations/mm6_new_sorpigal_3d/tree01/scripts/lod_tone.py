#!/usr/bin/env python3
"""Mean canopy colour per LOD in the eye-level renders (work/<prefix>_<LOD>_eye.png, upper 65 % of the frame)."""
import sys
import numpy as np
from PIL import Image
prefix = sys.argv[1]
for n in ('Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3'):
    try:
        im = np.asarray(Image.open(f'work/{prefix}_{n}_eye.png').convert('RGBA')).astype(float)
    except FileNotFoundError:
        continue
    top = im[:int(im.shape[0] * 0.65)]; a = top[..., 3] > 128
    print('TONE', n, top[..., :3][a].mean(0).round(1).tolist(), 'coverage', round(float(a.mean()), 3))
