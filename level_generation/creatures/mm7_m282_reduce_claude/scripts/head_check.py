#!/usr/bin/env python3
"""The accepted face must not change: every LOD0 triangle of the source GLB in the head texture set (u > 0.51 of the
merged atlas: face, scalp, neck top, eyes) must exist in the reduced GLB with the same three positions, UVs and
normals (per corner). Also checks the hands (hand + finger weight > 0.5) the same way.
Usage: head_check.py <source.glb> <reduced.glb> [node]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
NODE = sys.argv[3] if len(sys.argv) > 3 else 'M282'
DT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}


def lod0(path):
    d, b = read_glb(Path(path)); n = next(x for x in d['nodes'] if x.get('name') == NODE)
    p = d['meshes'][n['mesh']]['primitives'][0]; a = p['attributes']
    get = lambda i: np.frombuffer(accessor_bytes(d, b, i), DT[d['accessors'][i]['componentType']])
    pos = get(a['POSITION']).reshape(-1, 3); nrm = get(a['NORMAL']).reshape(-1, 3); uv = get(a['TEXCOORD_0']).reshape(-1, 2)
    names = [d['nodes'][i]['name'] for i in d['skins'][n['skin']]['joints']]
    J = get(a['JOINTS_0']).reshape(-1, 4).astype(int); W = get(a['WEIGHTS_0']).reshape(-1, 4).astype(float)
    if W.max() > 1.5:
        W = W / 255.
    hand = np.array([n.startswith(('Hand_', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for n in names])
    hw = (W * hand[J]).sum(1)
    return pos, nrm, uv, get(p['indices']).reshape(-1, 3), hw


sp, sn, su, si, shw = lod0(sys.argv[1]); cp, cn, cu, ci, _ = lod0(sys.argv[2])
from scipy.spatial import cKDTree  # noqa: E402
tree = cKDTree(cp[ci].mean(1))
for label, sel in (('head set', su[si][:, :, 0].mean(1) > 0.51), ('hands', (shw[si] > 0.5).all(1))):
    miss = 0; dn = dp = du = 0.0
    for t in si[sel]:
        _, j = tree.query(sp[t].mean(0)); c = ci[j]
        m = [int(np.argmin(np.linalg.norm(cp[c] - sp[k], axis=1))) for k in t]
        e_p = max(float(np.linalg.norm(cp[c[m[q]]] - sp[k])) for q, k in enumerate(t))
        e_u = max(float(np.linalg.norm(cu[c[m[q]]] - su[k])) for q, k in enumerate(t))
        if len(set(m)) < 3 or e_p > 1e-5 or e_u > 1e-5:
            miss += 1; continue
        dp, du = max(dp, e_p), max(du, e_u)
        dn = max(dn, max(float(np.linalg.norm(cn[c[m[q]]] - sn[k])) for q, k in enumerate(t)))
    print(f'{label}: source triangles {int(sel.sum())}, missing in reduced {miss}; max corner difference position '
          f'{dp * 1000:.4f} mm, uv {du:.2e}, normal {dn:.5f}')
