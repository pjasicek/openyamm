#!/usr/bin/env python3
"""LOD0 of a rigid attachment GLB (bow / arrow: one node, one primitive) -> work/<name>.npz: positions, normals,
triangles, wedge UVs, and connected parts (work/<name>_comp.npy). Prints each part's size and extent.
Usage: prop_dump.py <glb> <name>"""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
glb, name = sys.argv[1], sys.argv[2]
d, b = read_glb(Path(glb)); node = next(n for n in d['nodes'] if 'mesh' in n)
p = d['meshes'][node['mesh']]['primitives'][0]
get = lambda i, k: np.frombuffer(accessor_bytes(d, b, i), {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[d['accessors'][i]['componentType']]).reshape(-1, k)
V = get(p['attributes']['POSITION'], 3).astype(float); N = get(p['attributes']['NORMAL'], 3).astype(float)
UV = get(p['attributes']['TEXCOORD_0'], 2).astype(float); F = get(p['indices'], 3).astype(np.int64)
# weld exact position+UV duplicates? keep glTF vertices (normals/UV per vertex); weld positions only for parts
key = np.round(V, 6); _, pos_id = np.unique(key, axis=0, return_inverse=True); pos_id = pos_id.ravel()
e = pos_id[np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])]
n = pos_id.max() + 1
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
comp = lab[pos_id[F[:, 0]]]
_, comp = np.unique(comp, return_inverse=True)
np.savez(f'work/{name}.npz', verts=V, normals=N, uv=UV, faces=F, wuv=UV[F].reshape(-1, 2), pos_id=pos_id)
np.save(f'work/{name}_comp.npy', comp)
print(name, len(V), 'verts', len(F), 'tris, bounds', V.min(0).round(3), V.max(0).round(3))
for k in range(comp.max() + 1):
    m = comp == k; vs = V[np.unique(F[m])]
    print(' part', k, int(m.sum()), 'tris, lo', vs.min(0).round(3), 'hi', vs.max(0).round(3))
