#!/usr/bin/env python3
"""Overlay a head part's outline (projected with head_clay/project_head cameras, clay->paint bbox fit as project_head) on a
painted view. Usage: part_overlay.py <head_faces npz> <tier a|s> <view> <part> <out png>"""
import sys, numpy as np
from PIL import Image, ImageDraw
Z = np.load(sys.argv[1]); CO, PART = Z['co'], Z['part']; tier, name, part, out = sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
C = np.array([0.0, 0.10, 0.85]); ORTHO = 0.56; FC = np.array([0.0, -0.02, 0.872]); FO = 0.22
VIEWS = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1),
         '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15), '08_face': (0, -1, 0)}
def cam(d):
    d = np.array(d, float); d /= np.linalg.norm(d); up = np.array([0, 0, 1.0])
    if abs(d @ up) > 0.99: up = np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); return d, r, np.cross(d, r)
d, r, u = cam(VIEWS[name]); Cc, Oo = (FC, FO) if name == '08_face' else (C, ORTHO)
im = Image.open(f'references_head/{tier}_{name}_clean.png').convert('RGBA'); W, H = im.size
al = np.asarray(im)[..., 3] > 127
cl = np.asarray(Image.open(f'references_head/clay_{name}.png').convert('RGBA'))[..., 3] > 128; CH, CW = cl.shape
def bbox(m):
    ys, xs = np.nonzero(m); return xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
if name == '08_face': kx = ky = 1.0; ox = oy = 0.0
else:
    ax0, ax1, ay0, ay1 = bbox(al); bx0, bx1, by0, by1 = bbox(cl)
    kx = (ax1 - ax0) / W / ((bx1 - bx0) / CW); ky = (ay1 - ay0) / H / ((by1 - by0) / CH); ox = ax0 / W - bx0 / CW * kx; oy = ay0 / H - by0 / CH * ky
bg = Image.new('RGBA', im.size, (90, 90, 90, 255)); bg.alpha_composite(im); dr = ImageDraw.Draw(bg)
for t in np.where(PART == part)[0]:
    P = CO[t]
    if np.cross(P[1] - P[0], P[2] - P[0]) @ d > 0: continue
    sx = (P - Cc) @ r / Oo + 0.5; sy = 0.5 - (P - Cc) @ u / Oo
    dr.polygon([((sx[k] * kx + ox) * W, (sy[k] * ky + oy) * H) for k in range(3)], outline=(255, 255, 0, 255))
bg.convert('RGB').save(out)
