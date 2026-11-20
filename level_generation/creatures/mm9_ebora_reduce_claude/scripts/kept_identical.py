#!/usr/bin/env python3
"""Kept parts identical? For the head and wing LOD0 primitives (kept whole) of a candidate GLB against the installed:
triangle count, and per vertex position, UV, normal and skin weights (by joint name) of the matched source vertex;
the face triangles compared as sets of position triples. Usage: kept_identical.py <source.glb> <cand.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402


def load(path):
    doc, b = read_glb(Path(path)); node = next(n for n in doc['nodes'] if n.get('name') == 'Ebora')
    jn = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]; out = {}
    for p in doc['meshes'][node['mesh']]['primitives']:
        def A(i):
            a = doc['accessors'][i]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
            ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
            return np.frombuffer(accessor_bytes(doc, b, i), ct).reshape(-1, n)
        at = p['attributes']; J = A(at['JOINTS_0']); Wt = A(at['WEIGHTS_0'])
        out[doc['materials'][p['material']]['name']] = dict(P=A(at['POSITION']), UV=A(at['TEXCOORD_0']), N=A(at['NORMAL']),
            W=[{jn[j]: round(float(w), 4) for j, w in zip(jr, wr) if w > 1e-4} for jr, wr in zip(J, Wt)], T=A(p['indices']).reshape(-1, 3))
    return out


S, C = load(sys.argv[1]), load(sys.argv[2])
for name in ('EboraHead', 'EboraWing'):
    s, c = S[name], C[name]; t = cKDTree(np.c_[s['P'], s['UV']])
    d, j = t.query(np.c_[c['P'], c['UV']])
    ndev = np.degrees(np.arccos(np.clip((s['N'][j] * c['N']).sum(1), -1, 1)))
    wbad = sum(1 for i in range(len(j)) if any(abs(s['W'][j[i]].get(k, 0) - c['W'][i].get(k, 0)) > 2e-3 for k in set(s['W'][j[i]]) | set(c['W'][i])))
    key = lambda P, T: {tuple(sorted(tuple(np.round(P[v], 5)) for v in tr)) for tr in T}
    bytes_same = all(np.array_equal(s[k], c[k]) for k in ('P', 'UV', 'N', 'T')) and s['W'] == c['W']
    print(name, 'byte-identical', bytes_same, 'tris', len(s['T']), '->', len(c['T']), 'same triangle set', key(s['P'], s['T']) == key(c['P'], c['T']),
          '| vertices', len(s['P']), '->', len(c['P']), 'max pos/uv offset', float(d.max()), 'normal max dev deg', round(float(ndev.max()), 4),
          'weight mismatches', wbad)
