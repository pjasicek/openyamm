"""Silhouette overlay: MM9 PeasantF6 (red) vs a mesh npz (green), front (x,z) and side (y,z), head window. Args: <npz> <out png> [parts,...]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
D = np.load(sys.argv[1]); co, tri = D['co'], D['tri']
if len(sys.argv) > 3:
    names = [str(x) for x in D['names']]; keep = np.isin(D['comp'][tri[:, 0]], [names.index(n) for n in sys.argv[3].split(',')]); tri = tri[keep]
M = np.load('work/mm9_f6_head.npz'); P6, T6 = M['P6'], M['T6']
S = 1600; win = (0.38, 0.92); sc = S / (win[1] - win[0])
def img(P, T, a, col):
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
    for t in T:
        pts = [((P[k, a] + 0.27) * sc, (win[1] - P[k, 2]) * sc) for k in t]; dr.polygon(pts, fill=255)
    return np.array(im) > 0
def imgxy(P, T):
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im); H = P[:, 2] > 0.55
    for t in T:
        if not H[t].all(): continue
        dr.polygon([((P[k, 0] + 0.27) * sc, (P[k, 1] + 0.27) * sc) for k in t], fill=255)
    return np.array(im) > 0
out = []
for a in (0, 1, 2):
    ax = 1 if a == 2 else a
    m = img(P6, T6, ax, 0); o = img(co, tri, ax, 0)
    if a == 2:      # top-down silhouette (x, y): the cap's width round the skull
        m = imgxy(P6, T6); o = imgxy(co, tri)
    rgb = np.zeros((S, S, 3), np.uint8) + 40; rgb[m] = (200, 60, 60); rgb[o] = (60, 190, 60); rgb[m & o] = (220, 210, 80)
    out.append(rgb)
Image.fromarray(np.hstack(out)).resize((2400, 800)).save(sys.argv[2])
