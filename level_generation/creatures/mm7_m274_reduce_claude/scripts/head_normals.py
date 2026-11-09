#!/usr/bin/env python3
"""Carry the installed head's custom normals onto the reduced LOD0 (MM8 Bedraggled Human). The installed body shades
with plain smooth normals, but the separately modelled head (head-atlas half, u > 0.505) carries custom normals: on the
kept eye and lip faces, whose geometry is identical, the reduction's smooth normals differed by 22-28 deg (median) and
the clay renders lost the lid, lip and stubble creases (review/glbclose). Each head-atlas vertex of the reduced mesh
takes the source normal interpolated at its UV (the source triangle containing that UV; the head UV charts do not
overlap); if that source point lies over REA_NRM_MM (default 8) mm away in rest space, the nearest source head vertex's
normal is used instead. Body normals are unchanged. Usage: head_normals.py <source.glb> <in.glb> <out.glb> [node]"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes  # noqa: E402


def prim(doc, binary, node):
    p = doc['meshes'][next(n for n in doc['nodes'] if n.get('name') == node)['mesh']]['primitives'][0]
    get = lambda a, k: np.frombuffer(accessor_bytes(doc, binary, p['attributes'][a]), np.float32).reshape(-1, k)
    ia = doc['accessors'][p['indices']]
    tri = np.frombuffer(accessor_bytes(doc, binary, p['indices']), np.uint32 if ia['componentType'] == 5125 else np.uint16)
    return p, get('POSITION', 3), get('NORMAL', 3), get('TEXCOORD_0', 2), tri.reshape(-1, 3).astype(np.int64)


src, inp, out = (Path(a) for a in sys.argv[1:4]); node = sys.argv[4] if len(sys.argv) > 4 else 'Bedraggled'
sd, sb = read_glb(src); _, SP, SN, SU, ST = prim(sd, sb, node)
doc, binary = read_glb(inp); binary = bytearray(binary); p, P, N, U, T = prim(doc, binary, node)
lim = float(os.environ.get('REA_NRM_MM', '8')) / 1000
ht = ST[(SU[ST][:, :, 0] > .505).all(1)]                      # source head-atlas triangles
a, b, c = SU[ht[:, 0]], SU[ht[:, 1]], SU[ht[:, 2]]
tree = cKDTree((a + b + c) / 3); hv = np.unique(ht); vtree = cKDTree(SP[hv])
out_n = N.copy(); sel = np.where(U[:, 0] > .505)[0]; by_uv = fallback = 0
_, cand = tree.query(U[sel], k=24)
for q, i in enumerate(sel):
    best = None
    for t in cand[q]:
        v0, v1 = b[t] - a[t], c[t] - a[t]; v2 = U[i] - a[t]
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-14:
            continue
        l1 = (v2[0] * v1[1] - v1[0] * v2[1]) / den; l2 = (v0[0] * v2[1] - v2[0] * v0[1]) / den; l0 = 1 - l1 - l2
        if min(l0, l1, l2) >= -1e-4:
            w = np.array([l0, l1, l2]); pos = w @ SP[ht[t]]
            if np.linalg.norm(pos - P[i]) < lim:
                best = w @ SN[ht[t]]; break
    if best is None:
        best = SN[hv[vtree.query(P[i])[1]]]; fallback += 1
    else:
        by_uv += 1
    out_n[i] = best / np.linalg.norm(best)
acc = doc['accessors'][p['attributes']['NORMAL']]; view = doc['bufferViews'][acc['bufferView']]
off = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
assert view.get('byteStride', 12) == 12
binary[off:off + out_n.nbytes] = out_n.astype(np.float32).tobytes()
write_glb(out, doc, bytes(binary))
ang = np.degrees(np.arccos(np.clip((out_n[sel] * N[sel]).sum(1), -1, 1)))
print('HEAD NORMALS', len(sel), 'vertices: by uv', by_uv, 'nearest', fallback, '| change median %.1f p90 %.1f deg' % (np.median(ang), np.percentile(ang, 90)))
