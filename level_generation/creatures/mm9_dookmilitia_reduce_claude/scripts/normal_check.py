#!/usr/bin/env python3
"""Normals of a candidate LOD0 against its own geometry: per primitive, the angle between each vertex's stored normal and
the area-weighted normal of the faces round its position (merged by rounded position within the primitive). Lists the worst
vertices with rest position (glTF) and whether the vertex is a source vertex of the installed file.
Usage: normal_check.py <cand.glb> [source.glb]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402


def arr(doc, binary, idx):
    a = doc['accessors'][idx]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    v = np.frombuffer(accessor_bytes(doc, binary, idx), ct)
    return v.reshape(-1, n) if n > 1 else v


def load(path):
    doc, b = read_glb(Path(path)); node = next(n for n in doc['nodes'] if n.get('name') == 'DookMilitia')
    out = {}
    for p in doc['meshes'][node['mesh']]['primitives']:
        a = p['attributes']
        out[doc['materials'][p['material']]['name']] = (arr(doc, b, a['POSITION']).astype(float), arr(doc, b, a['NORMAL']).astype(float),
                                                        arr(doc, b, p['indices']).astype(int).reshape(-1, 3))
    return out


C = load(sys.argv[1]); S = load(sys.argv[2]) if len(sys.argv) > 2 else None
for name, (P, N, T) in C.items():
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    _, inv = np.unique(np.round(P, 5), axis=0, return_inverse=True); inv = inv.ravel()
    G = np.zeros((inv.max() + 1, 3))
    for c in range(3):
        np.add.at(G, inv[T[:, c]], fn)
    G = G[inv]; G /= np.maximum(np.linalg.norm(G, axis=1, keepdims=True), 1e-12)
    ang = np.degrees(np.arccos(np.clip((G * N).sum(1), -1, 1)))
    src = np.zeros(len(P), bool)
    if S:
        d, _ = cKDTree(S[name][0]).query(P); src = d < 1e-5
    print(name, 'verts', len(P), 'angle p50/p95/p99/max', np.round(np.percentile(ang, [50, 95, 99, 100]), 1),
          '>45: source', int((ang[src] > 45).sum()), 'new', int((ang[~src] > 45).sum()))
    for i in np.argsort(-ang * ~src)[:6]:
        print('   new', i, round(float(ang[i]), 1), np.round(P[i], 3))
