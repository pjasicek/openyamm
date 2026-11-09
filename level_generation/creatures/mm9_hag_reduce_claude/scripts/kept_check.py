#!/usr/bin/env python3
"""Exactness of the kept parts: every LOD0 triangle of the installed GLB whose corners all lie on the kept parts' vertices
(work/keep.npy faces of work/mesh_in.npz: hands, face, eyes, braid, wrist zone, small pieces, soles) must exist in the reduced GLB with
the same corner positions, UVs, normals, joints and weights. Prints per part the triangles found and the largest difference of each.
Usage: kept_check.py <installed glb> <reduced glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb  # noqa: E402


def corners(path):
    g = Glb(path); doc = g.json; node = next(n for n in doc['nodes'] if n.get('name') == 'Hag'); out = []
    for p in doc['meshes'][node['mesh']]['primitives']:
        A = {k: np.asarray(g.accessor(p['attributes'][k]), float) for k in ('POSITION', 'TEXCOORD_0', 'NORMAL', 'JOINTS_0', 'WEIGHTS_0')}
        t = np.asarray(g.accessor(p['indices'])).astype(np.int64).reshape(-1, 3)
        out.append({k: v[t] for k, v in A.items()})
    return {k: np.concatenate([o[k] for o in out]) for k in out[0]}


S, C = corners(sys.argv[1]), corners(sys.argv[2])
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); keep = np.load('work/keep.npy')
# installed triangles -> parts: centroid match against the dumped mesh (Blender z-up: glTF (x, y, z) = (x, z, -y))
cen = d['verts'][d['faces']].mean(1); cen = np.c_[cen[:, 0], cen[:, 2], -cen[:, 1]]
sc = S['POSITION'].mean(1); cen = cen + (S['POSITION'].reshape(-1, 3).min(0) - np.c_[d['verts'][:, 0], d['verts'][:, 2], -d['verts'][:, 1]].min(0))  # node lift
dist, j = cKDTree(cen).query(sc)
assert dist.max() < 1e-5, dist.max()
part, kept = info['part'][j], keep[j]
tree = cKDTree(C['POSITION'].mean(1)); dd, jj = tree.query(sc)
names = {0: 'hands', 20: 'face', 22: 'eyes', 23: 'braid', 1: 'armour (wrist zone)', 5: 'legs (soles)', 9: 'belt (buckle)', 12: 'lames (small)'}
for p in np.unique(part[kept]):
    m = kept & (part == p); found = m & (dd < 2e-5)  # float32 round trip through the node lift: up to 4 um
    a, b = np.where(m & found)[0], jj[m & found]
    # corners may be stored in another order: match each installed corner to the reduced triangle's corner at the same position
    o = np.argmin(np.linalg.norm(S['POSITION'][a][:, :, None] - C['POSITION'][b][:, None], axis=-1), axis=2)
    pick = lambda k: np.take_along_axis(C[k][b], o[..., None], axis=1)
    diff = {k: float(np.abs(S[k][a] - pick(k)).max()) if len(a) else None for k in ('POSITION', 'TEXCOORD_0', 'NORMAL')}
    nj = int(max(S['JOINTS_0'].max(), C['JOINTS_0'].max())) + 1

    def dense(J, W):
        out = np.zeros(J.shape[:-1] + (nj,)); np.put_along_axis(out, J.astype(int), 0, axis=-1)
        for k in range(J.shape[-1]):
            np.add.at(out.reshape(-1, nj), (np.arange(out.reshape(-1, nj).shape[0]), J[..., k].reshape(-1).astype(int)), W[..., k].reshape(-1))
        return out
    diff['WEIGHTS_0'] = float(np.abs(dense(S['JOINTS_0'][a], S['WEIGHTS_0'][a]) - dense(pick('JOINTS_0'), pick('WEIGHTS_0'))).max()) if len(a) else None
    jo = diff['WEIGHTS_0'] is not None and diff['WEIGHTS_0'] < 1e-3
    print(f'{names.get(int(p), p):22s} kept {int(m.sum()):5d} found {int(found.sum()):5d}  max diff pos {diff["POSITION"]:.2e} uv {diff["TEXCOORD_0"]:.2e} '
          f'normal {diff["NORMAL"]:.2e} weight {diff["WEIGHTS_0"]:.2e} skin equal {jo}')
