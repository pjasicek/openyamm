#!/usr/bin/env python3
"""Compare the meshes of two GLBs primitive by primitive (attributes and indices, exact). Usage: cmp_meshes.py a.glb b.glb"""
import sys, hashlib
import numpy as np, glbpack as G
A, ab = G.read(sys.argv[1]); B, bb = G.read(sys.argv[2])
print('meshes', [m['name'] for m in A['meshes']], [m['name'] for m in B['meshes']])
same = True
for ma, mb in zip(A['meshes'], B['meshes']):
    for pa, pb in zip(ma['primitives'], mb['primitives']):
        nm = A['materials'][pa['material']]['name']
        diffs = []
        for k in sorted(set(pa['attributes']) | set(pb['attributes'])):
            x = G.raw_rows(A, ab, pa['attributes'][k]); y = G.raw_rows(B, bb, pb['attributes'][k])
            if x.shape != y.shape or bytes(x) != bytes(y):
                diffs.append(k)
        x = G.acc(A, bytes(ab), pa['indices']).astype(np.int64); y = G.acc(B, bytes(bb), pb['indices']).astype(np.int64)
        if x.shape != y.shape or (x != y).any():
            diffs.append('indices')
        same &= not diffs
        print(ma['name'], nm, len(x) // 3, len(y) // 3, 'IDENTICAL' if not diffs else 'differ: ' + ','.join(diffs),
              pa.get('extensions') == pb.get('extensions'))
print('ALL IDENTICAL' if same else 'DIFFERENT')
