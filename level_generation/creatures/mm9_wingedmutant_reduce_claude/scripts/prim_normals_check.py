#!/usr/bin/env python3
"""Per LOD0 primitive: candidate vertices that match an installed vertex by position + UV, and how their normals differ
(kept surface should be identical). Usage: prim_normals_check.py <installed.glb> <candidate.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
A, ab = read_glb(Path(sys.argv[1])); B, bb = read_glb(Path(sys.argv[2]))
def arr(doc, b, idx, n):
    acc = doc['accessors'][idx]; dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[acc['componentType']]
    return np.frombuffer(accessor_bytes(doc, b, idx), dt).reshape(-1, n)
na = next(n for n in A['nodes'] if n.get('name') == 'Wmut'); nb = next(n for n in B['nodes'] if n.get('name') == 'Wmut')
for pa, pb in zip(A['meshes'][na['mesh']]['primitives'], B['meshes'][nb['mesh']]['primitives']):
    qa = np.c_[arr(A, ab, pa['attributes']['POSITION'], 3), arr(A, ab, pa['attributes']['TEXCOORD_0'], 2)].astype(float)
    qb = np.c_[arr(B, bb, pb['attributes']['POSITION'], 3), arr(B, bb, pb['attributes']['TEXCOORD_0'], 2)].astype(float)
    NA = arr(A, ab, pa['attributes']['NORMAL'], 3).astype(float); NB = arr(B, bb, pb['attributes']['NORMAL'], 3).astype(float)
    d, i = cKDTree(qa).query(qb, k=4); ok = d < 1e-5
    dots = np.where(ok, np.einsum('vkc,vc->vk', NA[i], NB), -9).max(1)
    m = ok.any(1)
    ang = np.degrees(np.arccos(np.clip(dots[m], -1, 1)))
    print(A['materials'][pa['material']]['name'], 'matched', int(m.sum()), 'of', len(qb), 'normal diff deg p50/p90/p99/max',
          np.percentile(ang, [50, 90, 99, 100]).round(2), '>1deg', int((ang > 1).sum()))
    # vertices of faces identical to installed faces (same three positions): which of them differ
    ta = arr(A, ab, pa['indices'], 1).reshape(-1, 3).astype(int); tb = arr(B, bb, pb['indices'], 1).reshape(-1, 3).astype(int)
    PA = qa[:, :3]; PB = qb[:, :3]
    key = lambda P, t: {tuple(sorted(tuple(np.round(P[x], 5)) for x in tri)): k for k, tri in enumerate(t)}
    ka = key(PA, ta); same = np.array([tuple(sorted(tuple(np.round(PB[x], 5)) for x in tri)) in ka for tri in tb])
    vs = np.zeros(len(qb), bool); vs[tb[same].ravel()] = True
    full = np.full(len(qb), 999.0); full[m] = ang
    print('   faces identical to installed', int(same.sum()), 'of', len(tb), '; their vertices', int(vs.sum()),
          'normal >1 deg', int((vs & (full > 1)).sum()), '>5 deg', int((vs & (full > 5)).sum()), 'unmatched', int((vs & (full == 999)).sum()))
