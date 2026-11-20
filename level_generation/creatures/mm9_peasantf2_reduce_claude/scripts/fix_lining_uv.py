#!/usr/bin/env python3
"""Re-emitted skirt-lining faces whose UV triangle still leaves the source charts after mpqem.py's one-chart pick (10 in f r45:
the back centre seam and the side seams, where coincident centre-seam vertices with other weights carry other lining charts):
each corner may take any lining GLB vertex within RAD of its twin (same lining surface, hidden inside the skirt); the
combination (non-degenerate, same facing) with the smallest outside fraction, then the smallest UV perimeter, is used. Index-degenerate faces (draw nothing) are dropped. Writes <out npz>.
Usage: fix_lining_uv.py <mp in npz> <mp out npz>"""
import itertools, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
RAD = 0.004; RES = 2048
_, _, _, S = glbio.load(HERE / 'before' / 'mm9_peasantf2.glb', 'PeasantF2')
d = dict(np.load(sys.argv[1])); name = 'PeasantF2_A'
U, P, T0 = S[name]['UV'], S[name]['P'], S[name]['T']
L = np.load(HERE / 'work' / 'glb_sets_f.npz'); lin = L['lining'][:len(T0)]
lv = np.unique(T0[lin]); tree = cKDTree(P[lv])
im = Image.new('L', (RES, RES)); dr = ImageDraw.Draw(im)
for t in T0:
    dr.polygon([tuple(U[k] * RES) for k in t], fill=255)
cov = ndimage.binary_dilation(np.asarray(im) > 0, iterations=2)
k = 12; i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k; w = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k


def outside(tri):
    s = w @ U[list(tri)]; x = np.clip((s[:, 0] * RES).astype(int), 0, RES - 1); y = np.clip((s[:, 1] * RES).astype(int), 0, RES - 1)
    return float((~cov[y, x]).mean())


T = d[name].astype(np.int64).copy(); lset = set(lv.tolist()); n = 0
deg = (T[:, 0] == T[:, 1]) | (T[:, 1] == T[:, 2]) | (T[:, 0] == T[:, 2])
print('index-degenerate faces dropped', int(deg.sum())); T = T[~deg]
for f, t in enumerate(T):
    if not all(int(v) in lset for v in t) or outside(t) <= 0.02:
        continue
    opts = [lv[tree.query_ball_point(P[v], RAD)] for v in t]
    combos = [c for c in itertools.product(*opts) if len(set(c)) == 3
              and np.linalg.norm(np.cross(P[c[1]] - P[c[0]], P[c[2]] - P[c[0]])) > 1e-8
              and np.dot(np.cross(P[c[1]] - P[c[0]], P[c[2]] - P[c[0]]), np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])) > 0]
    best = min(combos, key=lambda c: (round(outside(c), 3), sum(np.linalg.norm(U[c[a]] - U[c[(a + 1) % 3]]) for a in range(3))))
    print('face', f, 'outside', round(outside(t), 3), '->', round(outside(best), 3), 'moved mm', round(max(np.linalg.norm(P[a] - P[b]) for a, b in zip(t, best)) * 1000, 2))
    T[f] = best; n += 1
d[name] = T.astype(d[name].dtype); np.savez(sys.argv[2], **d); print('FIXED', n)
