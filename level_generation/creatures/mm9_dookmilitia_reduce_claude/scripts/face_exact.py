#!/usr/bin/env python3
"""Face skin check: every installed head-primitive triangle of parts 20 (face, ears, neck), 22 (eyes) and 2 (old neck V)
must exist in the candidate's head primitive with the same corner positions, UVs and normals (within 1e-5 m / 1e-5 UV / 0.05 deg: positions, UVs and normals pass Blender glTF import/export as float32; measured: 2.5e-7 m, 0 UV, 0.032 deg).
Usage: face_exact.py <installed.glb> <candidate.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbio  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
g = np.load(HERE / 'work' / 'glb_parts.npz')
_, _, _, A = glbio.load(sys.argv[1], 'DookMilitia'); _, _, _, B = glbio.load(sys.argv[2], 'DookMilitia')
off = sum(len(A[n]['T']) for n in ('DookMilitia_A', 'DookTorso_A'))
a, b = A['DookHead_A'], B['DookHead_A']
part = g['part'][off:off + len(a['T'])]
from scipy.spatial import cKDTree
sel = np.isin(part, [20, 22, 2])
ca = a['P'][a['T']].mean(1); cb = b['P'][b['T']].mean(1); tree = cKDTree(cb)
worst = dict(pos=0.0, uv=0.0, ndeg=0.0); miss = []; ndev = []
for i in np.where(sel)[0]:
    ok = False
    for j in tree.query_ball_point(ca[i], 1e-5):
        ta, tb = a['T'][i], b['T'][j]
        m = [int(np.argmin(np.linalg.norm(b['P'][tb] - a['P'][v], axis=1))) for v in ta]
        dp = max(np.linalg.norm(b['P'][tb[m[k]]] - a['P'][ta[k]]) for k in range(3))
        du = max(np.abs(b['UV'][tb[m[k]]] - a['UV'][ta[k]]).max() for k in range(3))
        dn = max(np.degrees(np.arccos(np.clip(b['N'][tb[m[k]]] @ a['N'][ta[k]], -1, 1))) for k in range(3))
        if dp < 1e-5 and du < 1e-5:
            ndev.append(dn)
        if dp < 1e-5 and du < 1e-5 and dn < 0.05:
            ok = True; worst = dict(pos=max(worst['pos'], dp), uv=max(worst['uv'], du), ndeg=max(worst['ndeg'], dn)); break
    if not ok:
        miss.append(i)
nd = np.array(ndev); print('geometry/UV matched', len(nd), 'normal deviation deg p50/p90/p99/max', np.round(np.percentile(nd, [50, 90, 99, 100]), 3), 'over 1 deg', int((nd > 1).sum()))
print('worst kept-corner deviation: position %.2e m, uv %.2e, normal %.4f deg' % (worst['pos'], worst['uv'], worst['ndeg']))
print('FACE triangles', int(sel.sum()), 'missing or changed', len(miss), '| helm/hood (21)', int((part == 21).sum()), '->',
      len(b['T']) - int(sel.sum()) + len(miss))
