#!/usr/bin/env python3
"""Flip the closed parts with negative signed volume (check_winding.py) in place: the LOD builder collapses some of
the 58-82-face crest ribs to 4-triangle tetrahedra whose winding comes out inverted at LOD3. Only the index order of
those triangles changes. Usage: fix_lod_winding.py <glb>"""
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'level_generation/decorations/mm8_3d/animated/scripts'))
from link_static_model_lods import read_glb  # noqa: E402
from check_winding import array, components, TYPES  # noqa: E402

path = Path(sys.argv[1]); doc, binary = read_glb(path); data = bytearray(binary); flipped = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        pos = array(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
        acc = doc['accessors'][prim['indices']]; view = doc['bufferViews'][acc['bufferView']]
        dtype = np.dtype(TYPES[acc['componentType']]); start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        idx = np.frombuffer(binary, dtype, acc['count'], start).copy().reshape(-1, 3)
        keys = [tuple(np.round(p, 5)) for p in pos]
        for part in components(idx, keys):
            t = idx[part]; a, b, c = pos[t[:, 0]], pos[t[:, 1]], pos[t[:, 2]]
            edges = defaultdict(int)
            for tri in t:
                for i in range(3):
                    edges[tuple(sorted((keys[tri[i]], keys[tri[(i + 1) % 3]])))] += 1
            if any(n != 2 for n in edges.values()):
                continue
            if np.einsum('ij,ij->i', a, np.cross(b, c)).sum() < 0:
                idx[part] = idx[part][:, [0, 2, 1]]; flipped += 1
                print('FLIP', mesh.get('name'), len(part), 'triangles at', np.round(a.mean(0), 3))
        data[start:start + idx.nbytes] = idx.astype(dtype).tobytes()
from link_static_model_lods import write_glb  # noqa: E402
write_glb(path, doc, bytes(data)); print('FLIPPED', flipped)
