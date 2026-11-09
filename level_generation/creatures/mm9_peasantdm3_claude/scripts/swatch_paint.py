#!/usr/bin/env python3
"""Paint the hair-shadow swatch of the head set: a free block of the head + hands texture (Blender HeadUV 0.95, 0.05;
no head or hand face uses it, uv_free_check.py) in a very dark brown, flat normal, rough ORM. hair_wall.py maps its wall
faces there: seen through the gap between cheek and hair curtain it reads as the deep shadow under the hair.
Usage (project folder): swatch_paint.py <prefix>   (after every other head-paint step; idempotent)"""
import sys
import numpy as np
from PIL import Image
P = sys.argv[1]
U, V, HALF = 0.95, 0.05, 0.018               # Blender UV centre, half size in UV
COL = (34, 22, 16)
for suf, val in (('head_basecolor.png', COL), ('head_normal_1k.png', (128, 128, 255)), ('head_metal_rough_1k.png', (200, 235, 0))):
    path = f'textures/{P}_{suf}'
    im = np.array(Image.open(path).convert('RGB'))
    H, W = im.shape[:2]
    c0, c1 = int((U - HALF) * W), int((U + HALF) * W)
    r0, r1 = int((1 - V - HALF) * H), int((1 - V + HALF) * H)
    im[r0:r1, c0:c1] = val
    Image.fromarray(im).save(path)
    print('SWATCH', path, (r0, r1, c0, c1))
