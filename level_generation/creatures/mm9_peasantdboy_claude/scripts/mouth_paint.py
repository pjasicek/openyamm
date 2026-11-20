#!/usr/bin/env python3
"""Paint the mouth-slit plate (work/mouth_uv.json from mouth_mask.py, dilated 3 px) as a closed mouth's shadow, not a pink plate or
teeth: the plate texels take one dark lip-shadow colour (84, 40, 36); normal flat.
Usage (project folder): mouth_paint.py <head set prefix> ..."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
import json
from PIL import ImageDraw
N = 2048
img = Image.new('L', (N, N), 0); d = ImageDraw.Draw(img)
for t in json.load(open('work/mouth_uv.json')):
    d.polygon([(u * N, (1 - v) * N) for u, v in t], fill=255)
m = ndimage.binary_dilation(np.asarray(img) > 0, iterations=3)
ring = ndimage.binary_dilation(m, iterations=25) & ~m
for pre in sys.argv[1:]:
    p = f'textures/{pre}_head_basecolor.png'
    im = np.asarray(Image.open(p).convert('RGB')).astype(float)
    px = im[ring]; lum = px @ [0.299, 0.587, 0.114]
    red = px[(px[:, 0] > px[:, 1] * 1.2)]
    src = red if len(red) > 50 else px
    lr = src @ [0.299, 0.587, 0.114]
    col = np.array([84.0, 40.0, 36.0])     # a fixed dark lip shadow: the UV ring mixes hair and skin islands
    im[m] = col
    Image.fromarray(np.uint8(np.clip(im, 0, 255))).save(p)
    q = f'textures/{pre}_head_normal_1k.png'
    a = np.asarray(Image.open(q).convert('RGB')).copy()
    mm = np.asarray(Image.fromarray(np.uint8(m * 255)).resize((a.shape[1], a.shape[0]), Image.NEAREST)) > 0
    a[mm] = (128, 128, 255)
    Image.fromarray(a).save(q)
    print('MOUTHPAINT', pre, 'colour', col.round(1).tolist(), 'texels', int(m.sum()))
