#!/usr/bin/env python3
"""Topology check of a decimated npz against work/mesh_in.npz: open edges (by welded position), non-manifold edges,
degenerate faces, mirror symmetry of the vertex set. Usage: check_npz.py <tag,...>"""
import sys
from collections import Counter
import numpy as np
from scipy.spatial import cKDTree


def stats(v, f):
    e = Counter(tuple(sorted(x)) for t in f for x in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
    area = 0.5 * np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
    dup = len(f) - len({tuple(sorted(t)) for t in f.tolist()})
    return sum(1 for c in e.values() if c == 1), sum(1 for c in e.values() if c > 2), int((area < 1e-10).sum()), dup


s = np.load('work/mesh_in.npz'); print('source', len(s['faces']), 'open/nonmanifold/degenerate/dup', stats(s['verts'], s['faces']))
for tag in sys.argv[1].split(','):
    d = np.load(f'work/mesh_r{tag}.npz'); v, f = d['verts'], d['faces']
    dm, _ = cKDTree(v).query(v * [-1, 1, 1])
    print(tag, len(f), 'open/nonmanifold/degenerate/dup', stats(v, f), 'mirror max %.2e' % dm.max(), 'src verts', int((d['src_index'] >= 0).sum()), 'of', len(v))
