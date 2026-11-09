"""Silhouette overlay of our mesh npz (green) on MM9's own mesh (work/mm9.npz, red), both in the MM9 frame: full body front/side and the
head window front/side. Yellow = both. Args: <npz> <out png> [parts,...]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
D = np.load(sys.argv[1]); co, tri = D['co'], D['tri']
if len(sys.argv) > 3:
    names = [str(x) for x in D['names']]; keep = np.isin(D['comp'][tri[:, 0]], [names.index(n) for n in sys.argv[3].split(',')]); tri = tri[keep]
M = np.load('work/mm9.npz'); P9, T9 = M['co'], M['tri']
def img(P, T, ax, win, S):
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im); (x0, x1), (z0, z1) = win; sc = S / (z1 - z0)
    for t in T:
        dr.polygon([(float((P[i, ax] - x0) * sc), float((z1 - P[i, 2]) * sc)) for i in t], fill=255)
    return np.asarray(im) > 0
out = []
for ax, win in ((0, ((-0.95, 0.95), (-0.95, 0.95))), (1, ((-0.95, 0.95), (-0.95, 0.95))), (0, ((-0.22, 0.22), (0.40, 0.84))), (1, ((-0.22, 0.22), (0.40, 0.84)))):
    a = img(P9, T9, ax, win, 800); b = img(co, tri, ax, win, 800)
    rgb = np.zeros((800, 800, 3), np.uint8) + 40; rgb[a & ~b] = (220, 60, 60); rgb[b & ~a] = (60, 200, 80); rgb[a & b] = (220, 210, 90); out.append(rgb)
    print('IOU', ax, win[1], round(float((a & b).sum() / max((a | b).sum(), 1)), 3))
Image.fromarray(np.hstack(out)).save(sys.argv[2])
