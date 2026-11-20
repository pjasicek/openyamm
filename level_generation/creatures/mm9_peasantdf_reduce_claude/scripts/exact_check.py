#!/usr/bin/env python3
"""Candidate LOD0 vs installed LOD0 of one design: every candidate vertex byte-identical to an installed vertex (position, UV,
normal, joints, weights); head primitive: every installed non-hand face present exactly (by vertex bytes); body: the faces of
the candidate equal across designs (compares the body face set to DF1's candidate under the byte keys).
Usage: exact_check.py <n>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack as G
n = sys.argv[1]

def lod0(path):
    doc, b = G.read(path); b = bytes(b)
    node = next(x for x in doc['nodes'] if x.get('name') == 'PeasantDF' and 'mesh' in x)
    out = []
    for p in doc['meshes'][node['mesh']]['primitives']:
        a = p['attributes']
        rows = np.concatenate([G.raw_rows(doc, b, a[s]) for s in ('POSITION', 'TEXCOORD_0', 'NORMAL', 'JOINTS_0', 'WEIGHTS_0')], 1)
        T = G.acc(doc, b, p['indices']).reshape(-1, 3).astype(np.int64)
        out.append(([r.tobytes() for r in rows], T))
    return out
inst = lod0(f'before/mm9_peasantdf{n}.glb'); D = __import__("os").environ.get("CAND", "export"); cand = lod0(f"{D}/mm9_peasantdf{n}.glb"); c1 = lod0(f"{D}/mm9_peasantdf1.glb")
fs = lambda k, T: {tuple(sorted((k[a], k[b], k[c]))) for a, b, c in T.tolist()}
for pi, ((ki, Ti), (kc, Tc), (k1, T1)) in enumerate(zip(inst, cand, c1)):
    si = set(ki); new = sum(1 for x in kc if x not in si)
    Fi, Fc = fs(ki, Ti), fs(kc, Tc)
    msg = f'df{n} prim{pi}: verts {len(kc)} not installed {new}; faces {len(Tc)}, installed faces kept {len(Fi & Fc)} of {len(Fi)}'
    if pi == 0 and n != '1':
        F1 = fs(k1, T1); msg += f'; body faces equal to DF1 candidate {len(F1 & Fc)} of {len(Fc)}'
    print(msg)
