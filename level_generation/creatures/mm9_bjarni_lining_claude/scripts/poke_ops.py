#!/usr/bin/env python3
"""Which line.py op (and role: twin / rim strip / cap) the see-through gate's lining-poke pixels land on: the gate's
<json stem>_faces.npz (pokes per Blender polygon, rest centres) matched to the lined GLB's triangles by rest centre; per op the
poke pixels, the poked triangles and their rest-centre spread. Usage: poke_ops.py <lined glb> <lining npz> <faces npz> [top 25]"""
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_common as C  # noqa: E402
glb, linz, fz = sys.argv[1:4]; TOP = int(sys.argv[4]) if len(sys.argv) > 4 else 25
doc, binary, nd, prims, jn = C.load(glb); z = np.load(linz); F = np.load(fz)
RC = F['rest_centre']; RCg = np.c_[RC[:, 0], RC[:, 2], -RC[:, 1]]; PK = F['pokes']
kd = cKDTree(RCg); acc = defaultdict(lambda: [0, 0, []])
rows = []
for name, d in prims.items():
    n0 = int(z[f'nvert_{name}']); tags = z[f'vtag_{name}']
    cen = d['P'][d['T']].mean(1); dist, idx = kd.query(cen)
    for t in np.where((dist < 1e-4) & (PK[idx] > 0))[0]:
        vs = [v for v in d['T'][t] if v >= n0]
        if not vs:
            key = (name, 'ORIGINAL')
        else:
            op, role, _ = tags[vs[0] - n0].split('|'); roles = {tags[v - n0].split('|')[1] for v in vs}
            key = (name, op + ':' + '+'.join(sorted(roles)))
        a = acc[key]; a[0] += int(PK[idx[t]]); a[1] += 1; a[2].append(cen[t])
        rows.append((int(PK[idx[t]]), key, np.round(cen[t], 3)))
for k, (px, n, cs) in sorted(acc.items(), key=lambda x: -x[1][0]):
    cs = np.array(cs); print(f'{k[0]:10s} {k[1]:28s} poke px {px:6d} on {n:4d} tris, rest y {cs[:, 1].min():.3f}..{cs[:, 1].max():.3f}')
print('top triangles:')
for px, k, c in sorted(rows, key=lambda r: -r[0])[:TOP]:
    print(f'  {px:5d} {k[1]:28s} {c}')
