#!/usr/bin/env python3
"""Rest-pose (and optional clip:time) source vertex -> candidate surface distance per class (work/glb_sets_<tag>.npz cls of the
faces each source vertex belongs to), from the installed LOD0 and an mpqem step npz. Usage: rest_error.py <mp npz> <sets tag> [clip:t]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glbio  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_krohn.glb', 'Krohn')
mp = np.load(HERE / 'work' / sys.argv[1]); S = np.load(HERE / 'work' / f'glb_sets_{sys.argv[2]}.npz'); cls = S['cls']
Ps = [d['P'] for d in D.values()]
if len(sys.argv) > 3:
    from glb_pose import Glb, Model
    m = Model(Glb(str(HERE / 'before' / 'mm9_krohn.glb'))); c, t = sys.argv[3].split(':')
    Ps = [p for p, _ in m.skinned_positions(m.world(m.sample(c, float(t))))[:3]]
def samples(P, T, step=0.0015):
    out = []
    for t in T:
        a, b_, c = P[t]; k = int(np.clip(max(np.linalg.norm(b_ - a), np.linalg.norm(c - a), np.linalg.norm(c - b_)) / step, 1, 80))
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); mm = i + j <= k
        w = np.stack([i[mm], j[mm], k - i[mm] - j[mm]], 1) / k; out.append(w @ P[t])
    return np.concatenate(out)
cand = np.concatenate([samples(P, mp[name]) for P, name in zip(Ps, D)])
tree = cKDTree(cand); off = np.cumsum([0] + [len(d['T']) for d in D.values()])
names = {}
for k, (name, d) in enumerate(D.items()):
    dist = tree.query(Ps[k])[0]
    c = cls[off[k]:off[k + 1]]
    vc = np.full(len(Ps[k]), -1); vc[d['T'].ravel()] = np.repeat(c, 3)
    for cc in np.unique(c):
        v = np.unique(d['T'][c == cc]); e = dist[v] * 1000
        print(f'{name:10s} cls {cc:2d} verts {len(v):5d} p99 {np.percentile(e, 99):6.2f} max {e.max():6.2f} >8mm {(e > 8).sum():4d}')
