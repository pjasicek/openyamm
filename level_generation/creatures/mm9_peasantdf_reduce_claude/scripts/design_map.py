#!/usr/bin/env python3
"""Exact vertex correspondence DF1 -> DF2..4 per LOD0 primitive, keyed by the raw bytes of POSITION, TEXCOORD_0, NORMAL,
JOINTS_0 and WEIGHTS_0 (with a running occurrence number for byte-identical duplicates). Reports per primitive how many
DF1 vertices have an exact twin in each design and which DF1 faces map onto a face of that design.
Writes work/design_map.npz: map_<n>_<prim> (DF1 vertex -> design vertex, -1 none)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack as G

def lod0(path):
    doc, b = G.read(path); b = bytes(b)
    node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDF' and 'mesh' in n)
    out = []
    for p in doc['meshes'][node['mesh']]['primitives']:
        a = p['attributes']
        rows = np.concatenate([G.raw_rows(doc, b, a[s]) for s in ('POSITION', 'TEXCOORD_0', 'NORMAL', 'JOINTS_0', 'WEIGHTS_0')], 1)
        T = G.acc(doc, b, p['indices']).reshape(-1, 3).astype(np.int64)
        out.append((rows, T))
    return out

def keys(rows):
    k = [r.tobytes() for r in rows]; seen = {}; out = []
    for x in k:
        c = seen.get(x, 0); seen[x] = c + 1; out.append((x, c))
    return out

ref = lod0('before/mm9_peasantdf1.glb'); res = {}
for n in '234':
    oth = lod0(f'before/mm9_peasantdf{n}.glb')
    for pi, ((ra, Ta), (rb, Tb)) in enumerate(zip(ref, oth)):
        kb = {k: i for i, k in enumerate(keys(rb))}
        m = np.array([kb.get(k, -1) for k in keys(ra)])
        res[f'map_{n}_{pi}'] = m
        ok = (m[Ta] >= 0).all(1)
        fb = {tuple(t) for t in Tb.tolist()}
        same = np.array([ok[f] and tuple(m[Ta[f]]) in fb for f in range(len(Ta))])
        print(f'df{n} prim{pi}: DF1 verts {len(ra)} matched {int((m >= 0).sum())}; DF1 faces {len(Ta)} same face in df{n} {int(same.sum())}')
        res[f'same_{n}_{pi}'] = same
np.savez('work/design_map.npz', **res)
