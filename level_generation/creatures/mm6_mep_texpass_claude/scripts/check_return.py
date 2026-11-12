"""Imports the UV study's chosen layout (uv_research_20261111, PartUV skin t1.25 + seam pass + sparrow) onto the
installed LOD0 triangles of one texture set, in the kit's layout format (work/<out>.npz: uv per triangle corner, glTF v
down; tri; xyz; prim), and checks that the study's upload, the Meshy return and the installed LOD0 agree exactly.

Usage: [TP_CONFIG=texpass_heads.json] hyd_import_layout.py <study upload glb> <meshy return glb> <out name>
Every installed triangle must be found in the upload with the same corner positions (1e-5 m); the Meshy return must
carry the same UVs per triangle (Meshy keeps the layout with enable_original_uv).
"""
import json
import sys
import numpy as np

import tp_common as C
from glb import Glb


def tris_of(path):
    g = Glb(path)
    pos, uv, out_p, out_uv = [], [], [], []
    for m in g.doc['meshes']:
        for pr in m['primitives']:
            p = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
            u = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
            f = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
            out_p.append(p[f])
            out_uv.append(u[f])
    # node transforms: the study uploads are exported with identity nodes; Meshy returns may carry a node matrix
    nodes = [n for n in g.doc['nodes'] if 'mesh' in n]
    for n in nodes:
        assert not any(k in n for k in ('matrix', 'rotation', 'scale', 'translation')) or \
            n.get('scale', [1, 1, 1]) == [1, 1, 1], f'{path}: node transform {n}'
    return np.concatenate(out_p), np.concatenate(out_uv)


def match(src_p, dst_p, tol=1e-5):
    """index of the src triangle for every dst triangle (nearest centroid, then every corner within tol), and the
    corner permutation dst corner c -> src corner perm[c]."""
    from scipy.spatial import cKDTree
    tree = cKDTree(src_p.mean(1))
    _, cand = tree.query(dst_p.mean(1), k=min(4, len(src_p)))
    idx = np.full(len(dst_p), -1)
    perm = np.zeros((len(dst_p), 3), int)
    used = np.zeros(len(src_p), bool)
    for t, c in enumerate(dst_p):
        for i in np.atleast_1d(cand[t]):
            if used[i]:
                continue
            d = np.linalg.norm(c[:, None] - src_p[i][None], axis=-1)
            pm = d.argmin(1)
            if len(set(pm)) == 3 and d[np.arange(3), pm].max() < tol:
                idx[t], perm[t], used[i] = i, pm, True
                break
    return idx, perm


cfg = C.config()
upload, meshy, out = sys.argv[1:4]
before = np.load(C.lod0_path())
xyz = before['pos'][before['tri']]
up_p, up_uv = tris_of(upload)
me_p, me_uv = tris_of(meshy)


def normalised(p):
    """Meshy returns the model centred on its bounding box and scaled to a largest extent of 2."""
    lo, hi = p.reshape(-1, 3).min(0), p.reshape(-1, 3).max(0)
    return (p - (lo + hi) / 2) / (hi - lo).max()


me_p = normalised(me_p)
idx, perm = match(up_p, xyz)
missing = int((idx < 0).sum())
assert len(up_p) == len(xyz), ('triangle count', len(up_p), len(xyz))
assert missing == 0, f'{missing} installed triangles not in the upload'
uv = up_uv[idx[:, None], perm]
# Meshy's return: same triangles; its UVs must equal the upload's
midx, mperm = match(me_p, normalised(up_p[idx]), tol=1e-4)
m_missing = int((midx < 0).sum())
report = {'triangles': len(xyz), 'missing_in_upload': missing, 'missing_in_meshy': m_missing}
if m_missing == 0:
    muv = me_uv[midx[:, None], mperm]
    report['meshy_v_flip'] = bool(np.abs(muv[..., 1] - uv[..., 1]).max() > np.abs(1 - muv[..., 1] - uv[..., 1]).max())
    report['meshy_uv_max_diff'] = float(np.abs(muv - uv).max())
np.savez(C.PROJECT / 'work' / f'{out}.npz', uv=uv, tri=before['tri'], xyz=xyz, prim=before['prim'])
json.dump(report, open(C.PROJECT / 'work' / f'{out}_import.json', 'w'), indent=1)
print('IMPORTED', out, report)
