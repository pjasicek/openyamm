#!/usr/bin/env python3
"""Shading check of a reduced export against the source (hard-surface drone): every reduced LOD0 vertex that sits on
a source vertex position takes the best-matching source normal there; prints the angle distribution (a lost hard edge
shows as many 20-90 degree angles). Usage: normal_check.py <source.glb> <reduced.glb> <mesh node>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402


def pn(path, node):
    d, b = read_glb(Path(path)); n = next(x for x in d['nodes'] if x.get('name') == node); P, N = [], []
    for p in d['meshes'][n['mesh']]['primitives']:
        P.append(np.frombuffer(accessor_bytes(d, b, p['attributes']['POSITION']), np.float32).reshape(-1, 3))
        N.append(np.frombuffer(accessor_bytes(d, b, p['attributes']['NORMAL']), np.float32).reshape(-1, 3))
    return np.concatenate(P), np.concatenate(N)


sp, sn = pn(sys.argv[1], sys.argv[3]); cp, cn = pn(sys.argv[2], sys.argv[3])
t = cKDTree(sp); near = t.query_ball_point(cp, 1e-5)
ang = np.array([np.degrees(np.arccos(np.clip(max(sn[j] @ cn[i] for j in js), -1, 1))) for i, js in enumerate(near) if js])
print('NORMALS on source positions', len(ang), 'of', len(cp), '| median %.2f p99 %.2f max %.1f deg | over 15 deg: %d'
      % (np.median(ang), np.percentile(ang, 99), ang.max(), (ang > 15).sum()))
