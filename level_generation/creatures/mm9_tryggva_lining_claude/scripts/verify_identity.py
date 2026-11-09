#!/usr/bin/env python3
"""Additions only? Compares a lined GLB with the installed one: every mesh primitive's original vertex rows (raw bytes of
every attribute) and triangles must be the candidate's first rows; images, materials, textures, samplers, skins, nodes,
animations (sampler input/output bytes) and the mesh extras identical. Prints the added vertices/triangles per mesh.
Usage: verify_identity.py <before glb> <candidate glb>"""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack  # noqa: E402
from bglbio import acc  # noqa: E402

A, B = sys.argv[1:3]
da, ba = glbpack.read(A); db, bb = glbpack.read(B)
bad = []


def view_bytes(doc, binary, v):
    v = doc['bufferViews'][v]; s = v.get('byteOffset', 0)
    return bytes(binary[s:s + v['byteLength']])


for key in ('materials', 'textures', 'samplers', 'skins', 'nodes', 'scenes', 'scene'):
    x, y = da.get(key), db.get(key)
    if key == 'skins':
        x = [{k: v for k, v in s.items() if k != 'inverseBindMatrices'} for s in x]
        y = [{k: v for k, v in s.items() if k != 'inverseBindMatrices'} for s in y]
    if x != y:
        bad.append(key)
for sa, sb in zip(da['skins'], db['skins']):
    if glbpack.raw_rows(da, ba, sa['inverseBindMatrices']).tobytes() != glbpack.raw_rows(db, bb, sb['inverseBindMatrices']).tobytes():
        bad.append('inverseBindMatrices')
if len(da['images']) != len(db['images']) or any(
        view_bytes(da, ba, x['bufferView']) != view_bytes(db, bb, y['bufferView']) or
        {k: v for k, v in x.items() if k != 'bufferView'} != {k: v for k, v in y.items() if k != 'bufferView'}
        for x, y in zip(da['images'], db['images'])):
    bad.append('images')
if len(da['animations']) != len(db['animations']):
    bad.append('animation count')
for x, y in zip(da['animations'], db['animations']):
    if x['name'] != y['name'] or x['channels'] != y['channels']:
        bad.append('animation ' + x['name'])
    for s, t in zip(x['samplers'], y['samplers']):
        for k in ('input', 'output'):
            if glbpack.raw_rows(da, ba, s[k]).tobytes() != glbpack.raw_rows(db, bb, t[k]).tobytes():
                bad.append('clip bytes ' + x['name'])
if len(da['meshes']) != len(db['meshes']):
    bad.append('mesh count')
for mi, (ma, mb) in enumerate(zip(da['meshes'], db['meshes'])):
    if ma.get('name') != mb.get('name') or ma.get('extras') != mb.get('extras') or len(ma['primitives']) != len(mb['primitives']):
        bad.append(f'mesh {mi} header')
    for pi, (pa, pb) in enumerate(zip(ma['primitives'], mb['primitives'])):
        if pa.get('material') != pb.get('material') or set(pa['attributes']) != set(pb['attributes']):
            bad.append(f'mesh {mi} prim {pi} header')
            continue
        n = da['accessors'][pa['attributes']['POSITION']]['count']
        m = db['accessors'][pb['attributes']['POSITION']]['count']
        for k in pa['attributes']:
            ra = glbpack.raw_rows(da, ba, pa['attributes'][k]); rb = glbpack.raw_rows(db, bb, pb['attributes'][k])
            if ra.shape[1] != rb.shape[1] or not np.array_equal(ra, rb[:n]):
                bad.append(f'mesh {mi} prim {pi} {k}')
        ta = acc(da, ba, pa['indices']).ravel(); tb = acc(db, bb, pb['indices']).ravel()
        if not np.array_equal(ta.astype(np.int64), tb[:len(ta)].astype(np.int64)):
            bad.append(f'mesh {mi} prim {pi} indices')
        added = tb[len(ta):]
        if len(added) and added.min() < n and mi not in ():
            # new triangles may reference original vertices only if they are rim corners; this body's rims use copies
            bad.append(f'mesh {mi} prim {pi}: new triangles use original vertices')
        print(f'mesh {mi} {ma.get("name")} prim {pi}: +{m - n} vertices, +{(len(tb) - len(ta)) // 3} triangles '
              f'({len(ta) // 3} -> {len(tb) // 3})')
print('IDENTITY', 'OK' if not bad else 'FAIL ' + ', '.join(sorted(set(bad))))
