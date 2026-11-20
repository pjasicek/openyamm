#!/usr/bin/env python3
"""What the fragment share of texture_quality.py is made of: islands under 8 triangles by dominant bone and whether their UVs have any
area. Faces with no UV area sit on one texel on purpose (linings, forearm stubs) and cannot blotch. Args: <glb>"""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
prims = doc['meshes'][doc['nodes'][m.primitives[0]['node']]['mesh']]['primitives']
for k, p in enumerate(m.primitives):
    if not p['skinned']:
        continue
    uv = m.glb.accessor(prims[k]['attributes']['TEXCOORD_0'])
    T = p['triangles']
    X = p['positions']
    n = len(T)
    edges = {}
    a, b = [], []
    for f, t in enumerate(T):
        for i in range(3):
            u, v = sorted((t[i], t[(i + 1) % 3]))
            key = (tuple(np.round(X[u], 5)), tuple(np.round(X[v], 5)), tuple(np.round(uv[u], 5)), tuple(np.round(uv[v], 5)))
            if key in edges:
                a.append(edges[key]); b.append(f)
            else:
                edges[key] = f
    _, lab = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n)), directed=False)
    size = np.bincount(lab)
    area = np.linalg.norm(np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]]), axis=1) / 2
    tu = uv[T]
    ua = np.abs((tu[:, 1, 0] - tu[:, 0, 0]) * (tu[:, 2, 1] - tu[:, 0, 1]) - (tu[:, 2, 0] - tu[:, 0, 0]) * (tu[:, 1, 1] - tu[:, 0, 1])) / 2
    frag = size[lab] < 8
    zero = ua < 1e-9
    print(f'prim {k}: surface {area.sum():.3f} m2, fragments {100 * area[frag].sum() / area.sum():.1f} %, of which no UV area {100 * area[frag & zero].sum() / area.sum():.1f} %, painted {100 * area[frag & ~zero].sum() / area[~zero].sum():.1f} % of the painted surface')
    dom = p['joints'][T[:, 0], p['weights'][T[:, 0]].argmax(1)]
    c = Counter()
    for f in np.where(frag & ~zero)[0]:
        c[names[dom[f]]] += area[f]
    print('   painted fragments by bone', [(k_, round(100 * v / area[~zero].sum(), 2)) for k_, v in c.most_common(6)])
