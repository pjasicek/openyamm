#!/usr/bin/env python3
"""Flat head-square normals (relayout_head.py turned the face chart; Meshy's nearly flat head normal cannot be carried
across a rotated chart without re-deriving its tangent frame). Usage (project folder): head_normal_flat.py <prefix> ..."""
import sys
import numpy as np
from PIL import Image
for pre in sys.argv[1:]:
    p = f'textures/{pre}_head_normal_1k.png'
    a = np.asarray(Image.open(p).convert('RGB')).copy()
    H = a.shape[0]; k = int(round(H * 0.8))
    a[H - k:, :k] = (128, 128, 255)
    Image.fromarray(a).save(p)
    print('NORMAL_FLAT', pre)
