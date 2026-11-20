#!/usr/bin/env python3
"""Where lining_gate.py's largest outward distance comes from: the same signed distance at one clip time, printing the worst
lining vertices (rest position) and the outer face they are measured against (rest centroid; installed or cut).
Usage: lining_probe.py <glb> <clip> <seconds>"""
import sys, runpy
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
glb, clip, t = sys.argv[1], sys.argv[2], float(sys.argv[3])
sys.argv = [sys.argv[0], glb, '/dev/null', '1000']
src = (HERE / 'scripts' / 'lining_gate.py').read_text().split('\nrep = {}')[0]
g = {'__file__': str(HERE / 'scripts' / 'lining_gate.py'), '__name__': 'probe'}
exec(compile(src, 'lining_gate', 'exec'), g)
m, sets, closest = g['m'], g['sets'], g['closest_on_triangles']
from scipy.spatial import cKDTree
pz = m.skinned_positions(m.world(m.sample(clip, t)))
for k, To, lv in sets:
    X = pz[k][0]; R = m.primitives[k]['positions']
    tr = X[To]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    Q = X[lv]; _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q)); fb = np.zeros(len(Q), int)
    for kk in range(8):
        i = ids[:, kk]; q, _ = closest(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
        best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1); fb[u] = i[u]
    for j in np.argsort(-sd)[:6]:
        print(f'lining v {lv[j]} rest {np.round(R[lv[j]], 3)} out {sd[j] * 1000:.2f} mm  face rest centre {np.round(R[To[fb[j]]].mean(0), 3)}')
