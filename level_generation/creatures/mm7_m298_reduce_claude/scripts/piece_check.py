#!/usr/bin/env python3
"""Separate-piece gate on every colour and shadow LOD of a GLB: connected pieces (positions welded at 1e-6) are
classified by each vertex's dominant joint (blob = Body/Lump_*, pod = PodRoot/Pod*/Knob, Glob_NN each its own), and a
piece whose vertices fall into more than one class (a triangle joining blob, pod and globules, or two globules) fails.
Also prints the lowest rest height per LOD. Usage: piece_check.py <glb> [mesh node, default Ooze]"""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
doc, binary = read_glb(Path(sys.argv[1])); NODE = sys.argv[2] if len(sys.argv) > 2 else 'Ooze'
node = next(n for n in doc['nodes'] if n.get('name') == NODE); extras = doc['meshes'][node['mesh']]['extras']
joints = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
cls = lambda n: 'blob' if n == 'Body' or n.startswith('Lump') else 'pod' if n.startswith('Pod') or n == 'Knob' else n
DT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
arr = lambda i: np.frombuffer(accessor_bytes(doc, binary, i), DT[doc['accessors'][i]['componentType']])
ok = True
for mi in [node['mesh']] + extras['openyamm_lods'] + extras['openyamm_shadow_lods']:
    for p in doc['meshes'][mi]['primitives']:
        a = p['attributes']; pos = arr(a['POSITION']).reshape(-1, 3); idx = arr(p['indices']).reshape(-1, 3)
        j = arr(a['JOINTS_0']).reshape(-1, 4); w = arr(a['WEIGHTS_0']).reshape(-1, 4)
        dom = np.array([cls(joints[j[k, np.argmax(w[k])]]) for k in range(len(pos))])
        _, uniq = np.unique(np.round(pos / 1e-6).astype(np.int64), axis=0, return_inverse=True); uniq = uniq.reshape(-1)
        e = np.concatenate([idx[:, [0, 1]], idx[:, [1, 2]]]); n = uniq.max() + 1
        _, lab = connected_components(coo_matrix((np.ones(len(e)), (uniq[e[:, 0]], uniq[e[:, 1]])), shape=(n, n)), directed=False)
        vl = lab[uniq]; mixed = [c for c in np.unique(vl) if len(set(dom[vl == c])) > 1]
        ok &= not mixed
        print(doc['meshes'][mi]['name'], 'tris', len(idx), 'pieces', len(np.unique(vl)), 'mixed', len(mixed),
              [sorted(set(dom[vl == c])) for c in mixed][:3], 'min height mm', round(float(pos[:, 1].min()) * 1000, 2))
print('PIECES', 'PASS' if ok else 'FAIL')
