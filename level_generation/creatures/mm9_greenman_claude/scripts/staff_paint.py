#!/usr/bin/env python3
"""Paint the staff's strip of the head set (staff_build.py: HeadUV u 0.82..0.98, v 0.02..0.58) from the Codex bark
swatch (references_staff/staff_bark.png, tiles both ways): colour into <prefix>_head_basecolor.png (2K), a normal from
the bark's luminance (Sobel, gentle) into <prefix>_head_normal_1k.png, roughness 210 / metallic 0 into
<prefix>_head_metal_rough_1k.png; the strip plus a 6 px margin, so mip filtering stays inside bark.
The swatch is resampled so its width spans the staff's circumference once and its aspect is kept along the length.
Usage (project folder): staff_paint.py <prefix> [circumference_m length_m]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
pre = sys.argv[1]
circ = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
length = float(sys.argv[3]) if len(sys.argv) > 3 else 2.4
U0, U1, V0, V1 = 0.82, 0.98, 0.02, 0.58
M = 6
bark = np.asarray(Image.open('references_staff/staff_bark.png').convert('RGB')).astype(np.float32)
def put(path, N, fill_fn):
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    x0, x1 = int(U0 * N) - M, int(round(U1 * N)) + M
    y0, y1 = N - int(round(V1 * N)) - M, N - int(V0 * N) + M
    w, h = x1 - x0, y1 - y0
    im[y0:y1, x0:x1] = fill_fn(w, h)
    Image.fromarray(np.uint8(np.clip(np.round(im), 0, 255))).save(path)
    return w, h
def bark_tile(w, h):
    # strip width w covers the circumference (+margins); along the length, the swatch's aspect: one swatch tile covers
    # circ * (1536/1024) m of staff, the strip's h covers `length`
    sw = int(round(w * (U1 - U0) * 0 + w))
    tile_h = max(8, int(round(h * (circ * 1.5) / length)))
    t = Image.fromarray(np.uint8(bark)).resize((sw, tile_h), Image.LANCZOS)
    reps = int(np.ceil(h / tile_h)) + 1
    col = np.concatenate([np.asarray(t)] * reps, 0)[:h]
    return col.astype(np.float32)
T = 'textures/'
w, h = put(T + f'{pre}_head_basecolor.png', 2048, bark_tile)
def normal_tile(w, h):
    c = bark_tile(w, h) @ np.array([0.299, 0.587, 0.114]) / 255.0
    c = ndimage.gaussian_filter(c, 1.0)
    gx = ndimage.sobel(c, 1); gy = ndimage.sobel(c, 0)
    k = 2.0
    n = np.stack([-gx * k, gy * k, np.ones_like(c)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5) * 255
put(T + f'{pre}_head_normal_1k.png', 1024, normal_tile)
put(T + f'{pre}_head_metal_rough_1k.png', 1024, lambda w, h: np.tile(np.array([255.0, 210.0, 0.0]), (h, w, 1)))
print('STAFFPAINT', pre, 'strip px', w, h)
