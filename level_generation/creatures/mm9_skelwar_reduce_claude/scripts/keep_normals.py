#!/usr/bin/env python3
"""Source normals on the kept surface (in place): export_cand.py writes smooth normals computed on the candidate, which
lost the axe's hard edges (85 vertices over 10 deg, its blade looked rounded in clay) and shifted a few border vertices of
the kept hands and face. Every LOD0 vertex that matches a source vertex of the same primitive by position and UV, and whose
source vertex is used only by kept faces (KEEP .npy over mesh_in faces = GLB face order), takes the source normal.
Usage: keep_normals.py <installed.glb> <lod0.glb> <keep.npy>"""
import struct, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes  # noqa: E402
src, out, keepf = Path(sys.argv[1]), Path(sys.argv[2]), np.load(sys.argv[3])
A, ab = read_glb(src); B, bb = read_glb(out); bb = bytearray(bb)


def arr(doc, binary, idx, n):
    acc = doc['accessors'][idx]; dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[acc['componentType']]
    return np.frombuffer(accessor_bytes(doc, binary, idx), dt).reshape(-1, n) if n > 1 else np.frombuffer(accessor_bytes(doc, binary, idx), dt)


import os
NODE = os.environ.get('REA_NODE', 'SkelWar')
node = next(n for n in A['nodes'] if n.get('name') == NODE); bnode = next(n for n in B['nodes'] if n.get('name') == NODE)
NPRIM = int(os.environ.get('KEEP_NPRIM', '2'))   # skelwar: body and head; the scimitar primitive is kept whole (swap_lod0 KEEP_PRIMS)
off = 0; total = 0
for pa, pb in list(zip(A['meshes'][node['mesh']]['primitives'], B['meshes'][bnode['mesh']]['primitives']))[:NPRIM]:
    assert pa['material'] == pb['material']
    ta = arr(A, ab, pa['indices'], 1).astype(int).reshape(-1, 3); kf = keepf[off:off + len(ta)]; off += len(ta)
    na = len(arr(A, ab, pa['attributes']['POSITION'], 3))
    allkept = np.ones(na, bool); np.logical_and.at(allkept, ta.ravel(), np.repeat(kf, 3))
    qa = np.c_[arr(A, ab, pa['attributes']['POSITION'], 3), arr(A, ab, pa['attributes']['TEXCOORD_0'], 2)].astype(float)
    qb = np.c_[arr(B, bb, pb['attributes']['POSITION'], 3), arr(B, bb, pb['attributes']['TEXCOORD_0'], 2)].astype(float)
    NA = arr(A, ab, pa['attributes']['NORMAL'], 3); nacc = B['accessors'][pb['attributes']['NORMAL']]
    view = B['bufferViews'][nacc['bufferView']]; assert view.get('byteStride', 12) == 12 and nacc['componentType'] == 5126
    start = view.get('byteOffset', 0) + nacc.get('byteOffset', 0)
    NB = np.frombuffer(bytes(bb[start:start + 12 * nacc['count']]), np.float32).reshape(-1, 3).copy()
    # split vertices of hard edges share position and UV and differ only in the normal: among the coincident source
    # vertices take the one whose normal is closest to the current one (a kept primitive then stays byte-identical)
    dk, ik = cKDTree(qa).query(qb, k=4); ok = dk < 1e-5
    score = np.where(ok, np.einsum('vkc,vc->vk', NA[ik].astype(float), NB.astype(float)), -9)
    pick = score.argmax(1); i = ik[np.arange(len(qb)), pick]; m = ok[np.arange(len(qb)), pick] & allkept[i]
    NB[m] = NA[i[m]]; bb[start:start + 12 * nacc['count']] = NB.astype(np.float32).tobytes(); total += int(m.sum())
    print('NORMALS', A['materials'][pa['material']]['name'], int(m.sum()), 'of', len(qb))
assert off <= len(keepf)  # the rest of keepf is the kept scimitar
write_glb(out, B, bytes(bb)); print('KEEPNORMALS', total)
