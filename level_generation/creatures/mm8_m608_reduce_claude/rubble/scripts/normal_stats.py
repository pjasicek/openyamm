#!/usr/bin/env python3
"""Normal splits per mesh of a GLB: positions carrying several normals (hard edges) and corner-vs-face deviation.
Usage: normal_stats.py <glb> [mesh index ...]"""
import sys, collections, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes
d, b = read_glb(Path(sys.argv[1]))
def val(i):
    a = d['accessors'][i]
    return np.frombuffer(accessor_bytes(d, b, i), dtype={5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]).reshape(a['count'], -1)
for mi in [int(x) for x in sys.argv[2:]] or range(len(d['meshes'])):
    p = d['meshes'][mi]['primitives'][0]; P = val(p['attributes']['POSITION']); N = val(p['attributes']['NORMAL']); I = val(p['indices']).reshape(-1, 3)
    _, inv = np.unique(np.round(P, 5), axis=0, return_inverse=True); inv = inv.ravel()
    f = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); f /= np.linalg.norm(f, axis=1)[:, None] + 1e-12
    dev = np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', np.repeat(f, 3, 0), N[I.ravel()]), -1, 1)))
    groups = collections.defaultdict(list)
    for i, g in enumerate(inv):
        groups[g].append(i)
    split = sum(1 for g in groups.values() if len(g) > 1 and np.min(N[g] @ N[g[0]]) < 0.95)
    print(d['meshes'][mi]['name'], 'tris', len(I), 'verts', len(P), 'positions', len(groups), 'hard(>18deg)', split,
          'corner-face dev median %.1f p90 %.1f' % (np.median(dev), np.percentile(dev, 90)))
