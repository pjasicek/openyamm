#!/usr/bin/env python3
"""Paint the ivory tusk swatch (add_tusks.py's HeadUV square u 0.03..0.07, v 0.90..0.96, Blender v up) into a head set:
base colour a root-to-tip ivory gradient (root 196/178/150, tip 240/233/214) with a faint lengthwise streak, 10 px margin;
normal flat; ORM roughness 0.45. Usage (project folder): tusk_swatch.py <head prefix>"""
import sys
import numpy as np
from PIL import Image
pre = sys.argv[1]
U0, U1, V0, V1 = 0.03, 0.07, 0.90, 0.96
for name, kind in (('head_basecolor', 'c'), ('head_normal_1k', 'n'), ('head_metal_rough_1k', 'm')):
    f = f'textures/{pre}_{name}.png'
    im = np.array(Image.open(f).convert('RGB'))
    N = im.shape[0]
    x0, x1 = int(U0 * N) - 10 * N // 2048, int(U1 * N) + 10 * N // 2048
    y0, y1 = int((1 - V1) * N) - 10 * N // 2048, int((1 - V0) * N) + 10 * N // 2048
    if kind == 'c':
        t = np.clip(((1 - V0) * N - np.arange(y0, y1)) / ((V1 - V0) * N), 0, 1)[:, None, None]   # 0 root .. 1 tip
        root, tipc = np.array([196, 178, 150]), np.array([240, 233, 214])
        col = root * (1 - t) + tipc * t
        streak = 1 + 0.04 * np.sin(np.arange(x0, x1) / max(1, (x1 - x0)) * 6 * np.pi)[None, :, None]
        im[y0:y1, x0:x1] = np.clip(col * streak, 0, 255).astype(np.uint8)
    elif kind == 'n':
        im[y0:y1, x0:x1] = (128, 128, 255)
    else:
        im[y0:y1, x0:x1] = (255, 115, 0)
    Image.fromarray(im).save(f)
print('TUSKSWATCH', pre)
