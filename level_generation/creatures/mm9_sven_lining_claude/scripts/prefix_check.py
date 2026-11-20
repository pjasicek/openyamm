#!/usr/bin/env python3
"""Added faces only: for every mesh and primitive of the installed GLB, the candidate's attribute rows (raw bytes) begin with
the installed rows and its triangle list begins with the installed triangles; meshes without linings (shadow meshes) are
identical; the mesh extras are equal. Prints per primitive installed -> candidate vertex and face counts.
Usage: prefix_check.py <installed glb> <candidate glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack  # noqa: E402
from bglbio import acc  # noqa: E402
(a, ab), (b, bb) = glbpack.read(sys.argv[1]), glbpack.read(sys.argv[2])
bad = 0
assert len(a['meshes']) == len(b['meshes'])
for ma, mb in zip(a['meshes'], b['meshes']):
    if ma.get('extras') != mb.get('extras') or ma.get('name') != mb.get('name') or len(ma['primitives']) != len(mb['primitives']):
        print('MESH DIFFERS', ma.get('name')); bad += 1; continue
    for pa, pb in zip(ma['primitives'], mb['primitives']):
        if pa['material'] != pb['material'] or set(pa['attributes']) != set(pb['attributes']):
            print('PRIM DIFFERS', ma['name']); bad += 1; continue
        for k in pa['attributes']:
            ra = glbpack.raw_rows(a, ab, pa['attributes'][k]); rb = glbpack.raw_rows(b, bb, pb['attributes'][k])
            if not np.array_equal(rb[:len(ra)], ra):
                print('ATTRIBUTE CHANGED', ma['name'], k); bad += 1
        ta = acc(a, bytes(ab), pa['indices']).reshape(-1, 3); tb = acc(b, bytes(bb), pb['indices']).reshape(-1, 3)
        if not np.array_equal(tb[:len(ta)], ta):
            print('TRIANGLES CHANGED', ma['name']); bad += 1
        na, nb = a['accessors'][pa['attributes']['POSITION']]['count'], b['accessors'][pb['attributes']['POSITION']]['count']
        print(f"{ma['name']:18s} {a['materials'][pa['material']]['name']:9s} verts {na:5d} -> {nb:5d}  faces {len(ta):5d} -> "
              f"{len(tb):5d} (+{len(tb) - len(ta)})")
print('PREFIX_CHECK', 'ok' if not bad else f'{bad} problems')
