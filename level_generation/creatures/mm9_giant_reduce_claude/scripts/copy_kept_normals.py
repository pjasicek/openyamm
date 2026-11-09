#!/usr/bin/env python3
"""Give the vertices of a swapped primitive that are source vertices (same position and UV, 1e-6) the source GLB's
normals (pass 2: the head set is cut in the hair, and the export recomputes every normal; the face must stay
pixel-identical). Usage: copy_kept_normals.py <source.glb> <in.glb> <out.glb> <material>[,<material>...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import glb_arrays as GA  # noqa: E402
from build_actor_lods import read_glb, write_glb  # noqa: E402
src, inp, out, mats = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
gs, bs = GA.load(src)
doc, binary = read_glb(Path(inp)); binary = bytearray(binary)
for m in mats:
    s = GA.prim(gs, bs, 0, m)
    prim = next(p for p in doc['meshes'][0]['primitives'] if doc['materials'][p['material']]['name'] == m)
    a = doc['accessors'][prim['attributes']['POSITION']]; P = GA.acc(doc, bytes(binary), prim['attributes']['POSITION']).astype(float)
    UV = GA.acc(doc, bytes(binary), prim['attributes']['TEXCOORD_0']).astype(float)
    na = doc['accessors'][prim['attributes']['NORMAL']]; N = GA.acc(doc, bytes(binary), prim['attributes']['NORMAL']).copy()
    tree = cKDTree(np.hstack([s['P'], s['UV']]).astype(float)); dd, j = tree.query(np.hstack([P, UV]))
    ok = dd < 1e-5; N[ok] = s['N'][j[ok]]
    bv = doc['bufferViews'][na['bufferView']]; off = bv.get('byteOffset', 0) + na.get('byteOffset', 0)
    assert na['componentType'] == 5126 and bv.get('byteStride', 12) == 12
    binary[off:off + N.nbytes] = N.astype(np.float32).tobytes()
    print('NORMALS', m, 'copied', int(ok.sum()), 'of', len(P))
write_glb(Path(out), doc, bytes(binary))
