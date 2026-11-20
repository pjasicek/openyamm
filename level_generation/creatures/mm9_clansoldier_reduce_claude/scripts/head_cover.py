#!/usr/bin/env python3
"""Which face/neck skin faces (part 20) are hidden at rest: a ray from the centroid along the face normal hits a helmet face
(part 21) or a torso face (coat/collar, part 1) within REACH. Prints counts by height; writes work/head_cover.npz (per GLB face:
covered_by 0 none, 21 helmet, 1 coat)."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(str(HERE / 'before' / 'mm9_clansoldier.glb')))
PR = [p for p in m.primitives if p['node'] == m.primitives[0]['node']][:4]
off = np.cumsum([0] + [len(p['positions']) for p in PR])
V = np.vstack([np.asarray(p['positions']) for p in PR]); T = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, off)])
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; lin = g['lining'].astype(bool)
X = V[T]; c = X.mean(1); n = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
REACH = 0.08
def hits(orig, d, tris):
    A, B, C = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = B - A, C - A
    out = np.full(len(orig), np.inf)
    for i in range(len(orig)):
        p = np.cross(d[i], e2); det = (e1 * p).sum(1)
        ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        s = orig[i] - A; u = (s * p).sum(1) * inv
        q = np.cross(s, e1); v = (d[i] * q).sum(1) * inv; t = (e2 * q).sum(1) * inv
        good = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5) & (t < REACH)
        if good.any(): out[i] = t[good].min()
    return out
sk = np.where(part == 20)[0]
cov = np.zeros(len(T), int)
for lab, sel in ((21, part == 21), (1, (part == 1) | (part == 9))):
    t = hits(c[sk] + n[sk] * 1e-4, n[sk], X[sel])
    cov[sk[(t < np.inf) & (cov[sk] == 0)]] = lab
y = c[:, 1]
print('part20', len(sk), 'covered by helmet', int((cov == 21).sum()), 'by coat/sash', int((cov == 1).sum()), 'open', int((cov[sk] == 0).sum()))
for lo in np.arange(1.55, 2.1, 0.05):
    s = sk[(y[sk] >= lo) & (y[sk] < lo + 0.05)]
    print(f'y {lo:.2f}: {len(s):4d} helmet {int((cov[s]==21).sum()):4d} coat {int((cov[s]==1).sum()):4d} open {int((cov[s]==0).sum()):4d}')
h = np.where(part == 21)[0]; print('helmet y', y[h].min().round(3), y[h].max().round(3), 'eyes y', y[part == 22].min().round(3), y[part == 22].max().round(3))
w = g['weapon']; print('weapons sword', int((w == 1).sum()), 'shield', int((w == 2).sum()))
np.savez(HERE / 'work' / 'head_cover.npz', cov=cov)
