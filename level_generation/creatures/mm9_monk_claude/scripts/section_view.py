#!/usr/bin/env python3
"""Cross sections of a mesh npz as images. Args: npz out comp spec... where spec = x=0.0 | y=0 | z=1.0 | arm"""
import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import section
D = np.load(sys.argv[1]); co, tri, comp = D['co'], D['tri'], D['comp']
out = sys.argv[2]; cs = [int(x) for x in sys.argv[3].split(',')]; specs = sys.argv[4:]
t = tri[np.isin(comp[tri[:, 0]], cs)]
S = 600; W = Image.new('RGB', (S * len(specs), S), (20, 20, 25)); dr = ImageDraw.Draw(W)
ax = {'x': 0, 'y': 1, 'z': 2}
for k, s in enumerate(specs):
    a, v = s.split('='); v = float(v); n = np.zeros(3); n[ax[a]] = 1
    L = section(co, t, n * v, n)
    u, w = [i for i in range(3) if i != ax[a]]
    pts = np.vstack([l['pts'] for l in L]) if L else np.zeros((1, 3))
    c = pts.mean(0); sc = 0.9 * S / max(np.ptp(pts[:, u]), np.ptp(pts[:, w]), 0.01)
    for l in L:
        for p in l['pts']:
            x = S / 2 + (p[u] - c[u]) * sc + k * S; y = S / 2 - (p[w] - c[w]) * sc
            dr.point((x, y), fill=(255, 220, 120)); dr.point((x + 1, y), fill=(255, 220, 120))
    dr.text((k * S + 5, 5), f'{s} loops {len(L)} {[round(l["per"],2) for l in L][:6]} span {np.ptp(pts[:, u]):.2f}', fill=(255, 255, 255))
W.save(out)
