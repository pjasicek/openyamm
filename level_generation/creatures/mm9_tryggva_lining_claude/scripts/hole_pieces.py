#!/usr/bin/env python3
"""Which pieces the see-through holes land on: see_through_gate.py's face_holes (faces=1) mapped to LOD0 primitive, piece
(welded connected component, numbered as rims.py) and dominant bone; hole pixels summed over every view and frame, and the
largest count of one face in one view. Faces past a primitive's original count are the linings (piece 'lining').
Usage: hole_pieces.py <glb> <see_through json> [orig counts 2270,6135]"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack  # noqa: E402
from bglbio import acc  # noqa: E402

doc, binary = glbpack.read(sys.argv[1]); rep = json.load(open(sys.argv[2]))
counts = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else '2270,6135').split(',')]
node = next(n for n in doc['nodes'] if 'mesh' in n and 'skin' in n)
bname = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
info = []
for pi, p in enumerate(doc['meshes'][node['mesh']]['primitives']):
    a = p['attributes']; P = acc(doc, binary, a['POSITION']).astype(float); T = acc(doc, binary, p['indices']).reshape(-1, 3).astype(int)
    J = acc(doc, binary, a['JOINTS_0']); W = acc(doc, binary, a['WEIGHTS_0'])
    _, w = np.unique(np.round(P, 5), axis=0, return_inverse=True); w = w.ravel(); TW = w[T]; n = w.max() + 1
    r = np.r_[TW[:, 0], TW[:, 1]]; c = np.r_[TW[:, 1], TW[:, 2]]
    comp = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1]
    dom = J[np.arange(len(P)), np.argmax(W, 1)]
    for fi, t in enumerate(T):
        b = Counter(bname[dom[v]] for v in t).most_common(1)[0][0]
        piece = 'lining' if fi >= counts[pi] else int(comp[TW[fi, 0]])
        info.append((pi, fi, piece, b, P[t].mean(0)))
fh = {int(k): v for k, v in rep['face_holes'].items()}
by = defaultdict(lambda: [0, 0, 0])
for f, (s, m) in fh.items():
    pi, fi, piece, b, c = info[f]
    k = (pi, piece); by[k][0] += s; by[k][1] = max(by[k][1], m); by[k][2] += 1
print('prim piece: hole px summed, max one face one view, faces')
for k, v in sorted(by.items(), key=lambda kv: -kv[1][0]):
    print(f'  {k}: {v}')
bb = defaultdict(int)
for f, (s, m) in fh.items():
    pi, fi, piece, b, c = info[f]; bb[(pi, piece, b)] += s
print('by prim, piece, dominant bone (top 25)')
for k, v in sorted(bb.items(), key=lambda kv: -kv[1])[:25]:
    print(f'  {k}: {v}')
print('top faces')
for f, (s, m) in sorted(fh.items(), key=lambda kv: -kv[1][0])[:15]:
    pi, fi, piece, b, c = info[f]
    print(f'  face {f} prim {pi} tri {fi} piece {piece} {b} rest ({c[0]:+.3f},{c[1]:.3f},{c[2]:+.3f}) sum {s} max {m}')
