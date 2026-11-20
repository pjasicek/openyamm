#!/usr/bin/env python3
"""Rest-pose probe of lining twins on the wrong side (diagnostic): per prim, twins whose signed distance to their source
piece is > tol at rest; prints the source welded vertex, its faces' normal spread and the nearest outer face's identity.
Usage: rest_probe.py <candidate glb> [tol 0.0005]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import glbio  # noqa
from detached_parts_audit import closest_on_triangles  # noqa
glb = sys.argv[1]; tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0005
doc, b, nd, D = glbio.load(glb, 'Sven')
TW = json.load(open(glb + '.twins.json'))['0']
for name, d in D.items():
    t = TW[name]; nv0, nf0 = t['nv0'], t['nf0']
    P, T = d['P'], d['T']; T0 = T[:nf0]
    kind = np.array(t['kind']); src = np.array(t['src'])
    tv = nv0 + np.flatnonzero(kind == 1); sv = src[kind == 1]
    tri = P[T0]; nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-15
    c = tri.mean(1); kd = cKDTree(c)
    _, ids = kd.query(P[tv], k=32)
    best = np.full(len(tv), 1e9); sd = np.zeros(len(tv)); bf = np.zeros(len(tv), int)
    for i in range(32):
        f = ids[:, i]; q, _ = closest_on_triangles(P[tv], tri[f, 0], tri[f, 1], tri[f, 2]); dd = np.linalg.norm(q - P[tv], axis=1)
        u = dd < best; best[u] = dd[u]; sd[u] = ((P[tv] - q) * nn[f])[u].sum(1); bf[u] = f[u]
    bad = np.flatnonzero(sd > tol)
    print(name, 'twins', len(tv), 'outside at rest', len(bad))
    for i in bad[:40]:
        s = sv[i]; ps = P[s]
        adj = np.flatnonzero((np.linalg.norm(P[T0] - ps, axis=2) < 1e-6).any(1))
        ns = nn[adj]; spread = float((ns @ ns.mean(0)).min()) if len(adj) else 9
        print(f'  twin {tv[i]} src {s} pos {ps.round(3)} sd {sd[i]*1000:.2f} mm, nearest face {bf[i]} (own adj {bf[i] in adj}), '
              f'adj faces {len(adj)} normal spread min cos {spread:.2f} offset {np.linalg.norm(P[tv[i]] - ps)*1000:.2f} mm')
