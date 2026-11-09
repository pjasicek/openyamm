#!/usr/bin/env python3
"""Horn curve points for the LOD build: on each helmet horn of the picked candidate (work/mesh_r<tag>.npz, group 4),
bin the vertices by edge-graph distance from the horn root (vertices nearest the helmet) and take the highest and
lowest vertex of every bin, so the LOD collapse keeps the horn's curve and not only its tip (reduced LOD3 horns came
out straight). Usage: horn_points.py <tag> [bins] -> work/horn_points.json"""
import json, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
tag = sys.argv[1]; bins = int(sys.argv[2]) if len(sys.argv) > 2 else 6
d = np.load(f'work/mesh_r{tag[1:]}.npz'); v, f, g = d['verts'], d['faces'], d['group']
hf = f[g == 4]; n = len(v)
e = np.concatenate([hf[:, [0, 1]], hf[:, [1, 2]], hf[:, [2, 0]]]); w = np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1)
G = coo_matrix((w, (e[:, 0], e[:, 1])), shape=(n, n)).tocsr(); G = G.maximum(G.T)
_, lab = connected_components(G, directed=False); used = np.unique(hf)
points = []
for horn in np.unique(lab[used]):
    vs = used[lab[used] == horn]
    if len(vs) < 20:
        continue
    root = vs[np.argsort(np.abs(v[vs, 0]))[:6]]
    dist = dijkstra(G, indices=root, min_only=True)[vs]
    edges = np.linspace(0, dist.max() + 1e-9, bins + 1)
    for k in range(bins):
        m = vs[(dist >= edges[k]) & (dist < edges[k + 1])]
        if len(m):
            points += [v[m[np.argmax(v[m, 2])]].tolist(), v[m[np.argmin(v[m, 2])]].tolist()]
    points.append(v[vs[np.argmax(dist)]].tolist())
points = [list(p) for p in {tuple(p) for p in points}]
json.dump(points, open('work/horn_points.json', 'w'), indent=1); print('HORN POINTS', len(points))
