#!/usr/bin/env python3
"""Silhouette check of the Codex masters against their guides (README.md, step 2): IoU of the alpha masks, bounding
boxes, and the share of the master's opaque pixels outside a 6 px dilation of the guide.
Usage: python3 -I master_check.py <icon>"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(os.path.dirname(HERE), 'work', sys.argv[1], 'references_hd')
for view, name in (('front', '01_front'), ('back', '02_back'), ('left', '03_left'), ('right', '04_right')):
    g = Image.open(os.path.join(folder, f'guide_{view}.png')).convert('RGBA').split()[3]
    m = Image.open(os.path.join(folder, f'{name}.png')).convert('RGBA')
    if m.size != g.size:
        m = m.resize(g.size, Image.LANCZOS)
    ga = np.asarray(g) > 128
    ma = np.asarray(m.split()[3]) > 128
    dil = np.asarray(g.filter(ImageFilter.MaxFilter(13))) > 128
    iou = (ga & ma).sum() / max((ga | ma).sum(), 1)
    out = (ma & ~dil).sum() / max(ma.sum(), 1)

    def box(a):
        ys, xs = np.nonzero(a)
        return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None
    print(f'{name}: IoU {iou:.2f}, outside guide+6px {out * 100:.1f} %, guide box {box(ga)}, master box {box(ma)}')
