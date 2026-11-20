#!/usr/bin/env python3
"""Reads BANSHEE's pieces from the converted GLB (bind pose, Blender axes: z up, faces -y, MM9 metres), welds them, and writes work/mm9_parts.npz:
per piece <name>_co, _tri, _uv (per corner), _dom (dominant bone index per welded vertex), bones (names), and prints connected components. Run from the project folder."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = Glb('source/skinA/bansheeA.glb')
doc = g.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
out = {'bones': np.array(names)}
for node in doc['nodes']:
    if 'mesh' not in node:
        continue
    mesh = doc['meshes'][node['mesh']]
    p = mesh['primitives'][0]
    P = g.accessor(p['attributes']['POSITION'])
    # node has its own transform? report
    if 'matrix' in node or 'translation' in node or 'rotation' in node:
        print('NODE XFORM', node.get('name'), {k: node[k] for k in ('matrix', 'translation', 'rotation', 'scale') if k in node})
    UV = g.accessor(p['attributes']['TEXCOORD_0'])
    J = g.accessor(p['attributes']['JOINTS_0']).astype(int); W = g.accessor(p['attributes']['WEIGHTS_0'])
    T = g.accessor(p['indices']).astype(int).reshape(-1, 3)
    co = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)   # glTF -> Blender
    key = np.round(co / 1e-4).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    Tw = inv[T]
    nv = len(first)
    # components
    par = np.arange(nv)
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in Tw:
        for a, b in ((0, 1), (1, 2)):
            ra, rb = find(t[a]), find(t[b])
            if ra != rb:
                par[ra] = rb
    roots = np.array([find(i) for i in range(nv)])
    ur, cnt = np.unique(roots, return_counts=True)
    print(mesh['name'], 'raw', len(P), 'welded', nv, 'tris', len(T), 'components', sorted(cnt.tolist(), reverse=True)[:20], 'max joints w', float(W.max()), 'multi', int((W > 0.01).sum(1).max()))
    n = mesh['name']
    out[n + '_co'] = co[first]; out[n + '_tri'] = Tw; out[n + '_uv'] = UV[T.reshape(-1)].reshape(-1, 3, 2)
    out[n + '_J'] = J[first]; out[n + '_W'] = W[first]; out[n + '_comp'] = roots
np.savez('work/mm9_parts.npz', **out)
