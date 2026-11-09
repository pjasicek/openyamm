#!/usr/bin/env python3
"""Overlay: master (aligned, align_side.py) with the Meshy fit silhouette (red) and the clean body (cyan outline).
Usage: side_overlay.py <align json> <master png> <meshy npz> <body npz> <out png>"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
al = json.load(open(sys.argv[1])); m = Image.open(sys.argv[2]).convert('RGBA')
def sil(V, T, size, f):
    im = Image.new('L', size, 0); dr = ImageDraw.Draw(im)
    p = f(V)
    for t in T:
        dr.polygon([tuple(p[i]) for i in t], fill=255)
    return np.asarray(im) > 0
k, ox, oy, res, u0, w1, sgn = al['k'], al['ox'], al['oy'], al['res'], al['u0'], al['w1'], al['sgn']
def to_img(V):
    u = sgn * V[:, 1]
    return np.stack([(u - u0) / res * k + ox, (w1 - V[:, 2]) / res * k + oy], 1)
d = np.load(sys.argv[3]); b = np.load(sys.argv[4])
S = sil(d['meshy_fit_v'], d['meshy_fit_t'], m.size, to_img)
B = sil(b['Body_v'], b['Body_t'], m.size, to_img)
bg = Image.new('RGBA', m.size, (90, 100, 90, 255)); bg.alpha_composite(m)
a = np.asarray(bg.convert('RGB')).astype(float)
edge = B ^ np.roll(B, 1, 0) | B ^ np.roll(B, 1, 1)
a[S & ~(np.asarray(m)[..., 3] > 128)] = a[S & ~(np.asarray(m)[..., 3] > 128)] * 0.4 + np.array([255, 0, 0]) * 0.6
a[edge] = (0, 255, 255)
Image.fromarray(a.astype(np.uint8)).save(sys.argv[5])
