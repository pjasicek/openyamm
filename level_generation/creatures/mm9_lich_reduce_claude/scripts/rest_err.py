#!/usr/bin/env python3
"""Rest-pose error of an mpqem step on Lich_A: for every installed vertex, distance to the candidate surface (point-triangle,
nearest 40 candidate faces by centroid), worst per part. Usage: rest_err.py work/mp_r70.npz [n worst]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402


def pt_tri(p, a, b, c):
    # Ericson, closest point on triangle; vectorised over rows
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b; d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - c; d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v = vb / den; w = vc / den
    q = a + ab * v[..., None] + ac * w[..., None]
    # clamp fallback: also test the three edges and pick the min
    def seg(p, x, y):
        t = np.clip(((p - x) * (y - x)).sum(-1) / np.maximum(((y - x) ** 2).sum(-1), 1e-30), 0, 1)
        return np.linalg.norm(p - (x + (y - x) * t[..., None]), axis=-1)
    inside = (va >= 0) & (vb >= 0) & (vc >= 0)
    dq = np.where(inside, np.linalg.norm(p - q, axis=-1), np.inf)
    return np.minimum.reduce([dq, seg(p, a, b), seg(p, b, c), seg(p, c, a)])


doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_lich.glb', 'Lich')
P = D['Lich_A']['P']; T0 = D['Lich_A']['T']
T = np.load(sys.argv[1])['Lich_A']
g = np.load(HERE / 'work' / 'glb_parts.npz'); part0 = g['part'][:len(T0)]
vpart = np.zeros(len(P), int); vpart[T0.ravel()] = np.repeat(part0, 3)
cen = P[T].mean(1); tree = cKDTree(cen)
_, nn = tree.query(P, 40)
d = pt_tri(P[:, None], P[T[nn, 0]], P[T[nn, 1]], P[T[nn, 2]]).min(1)
used = np.unique(T0)
d = d[used]; vp = vpart[used]
for p in np.unique(vp):
    s = vp == p; print(f'part {p:2d} verts {s.sum():5d} p99 {np.percentile(d[s], 99) * 1000:6.2f} max {d[s].max() * 1000:6.2f} mm')
n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
for i in np.argsort(-d)[:n]:
    print('  v', used[i], 'part', vp[i], P[used[i]].round(3), f'{d[i] * 1000:.1f} mm')
