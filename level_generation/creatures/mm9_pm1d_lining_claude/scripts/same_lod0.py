#!/usr/bin/env python3
"""The lined LOD0 keeps the installed LOD0 exactly: per primitive, the first n vertex rows of every attribute (raw bytes) and the
first m triangles are the installed ones; only rows and triangles after them are new. Usage: same_lod0.py <installed> <candidate>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack as G  # noqa: E402
(a, ab), (b, bb) = G.read(sys.argv[1]), G.read(sys.argv[2])
def lod0(d):
    nd = next(n for n in d['nodes'] if n.get('name') == 'PM1d' and 'mesh' in n)
    return {d['materials'][p['material']]['name']: p for p in d['meshes'][nd['mesh']]['primitives']}, nd
pa, na = lod0(a); pb, nb = lod0(b); ok = True
for name, p in pa.items():
    q = pb[name]
    for sem, i in p['attributes'].items():
        ra = G.raw_rows(a, ab, i); rb = G.raw_rows(b, bb, q['attributes'][sem])
        same = (rb[:len(ra)] == ra).all(); ok &= bool(same)
        print(f'{name} {sem}: installed {len(ra)} rows, candidate {len(rb)} (+{len(rb) - len(ra)}), first rows identical {same}')
    ta = G.acc(a, bytes(ab), p['indices']).reshape(-1, 3); tb = G.acc(b, bytes(bb), q['indices']).reshape(-1, 3)
    same = (tb[:len(ta)] == ta).all(); ok &= bool(same)
    print(f'{name} triangles: installed {len(ta)}, candidate {len(tb)} (+{len(tb) - len(ta)}), first triangles identical {same}')
    ok &= p.get('extensions') == q.get('extensions')
print('LOD0 EXACT + APPENDED' if ok else 'LOD0 DIFFERS')
