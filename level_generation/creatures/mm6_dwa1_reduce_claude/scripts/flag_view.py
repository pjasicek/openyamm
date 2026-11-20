"""Flat-shaded front/back/side projections of the rest mesh with faces coloured by labels (painter's order).
Usage: flag_view.py <out.png> <label .npy> [...]   (bool or int arrays; later arrays draw over earlier ones)"""
import sys, numpy as np
from PIL import Image, ImageDraw
d = np.load('work/mesh_in.npz'); V, F = d['verts'], d['faces']
lab = np.zeros(len(F), int)
for k, p in enumerate(sys.argv[2:], 1):
    a = np.load(p); lab[a.astype(bool) if a.dtype == bool else a > 0] = k
pal = [(170, 170, 170), (230, 60, 60), (60, 160, 230), (240, 200, 40), (80, 200, 90), (200, 90, 220)]
S = 700; im = Image.new('RGB', (S * 3, S), (30, 30, 30)); dr = ImageDraw.Draw(im)
tri = V[F]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
lo, hi = V.min(0), V.max(0); sc = (S - 40) / (hi - lo).max()
for k, (ax, sgn) in enumerate([(1, -1), (1, 1), (0, 1)]):  # front looks from -Y, back from +Y, side from +X
    h = 0 if ax == 1 else 1
    depth = tri[:, :, ax].mean(1) * sgn
    for i in np.argsort(-depth):
        if n[i, ax] * sgn < 0: continue
        shade = .45 + .55 * abs(n[i, ax])
        c = tuple(int(x * shade) for x in pal[lab[i] % len(pal)])
        pts = [(k * S + 20 + (p[h] - lo[h]) * sc * (-sgn if ax == 1 else -1) + (S - 40 if (ax == 1 and sgn < 0) or ax == 0 else 0) * 1, S - 20 - (p[2] - lo[2]) * sc) for p in tri[i]]
        dr.polygon(pts, fill=c)
im.save(sys.argv[1])
