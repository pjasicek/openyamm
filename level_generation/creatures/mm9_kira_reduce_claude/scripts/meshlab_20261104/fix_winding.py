#!/usr/bin/env python3
"""Flip the triangle order of every closed part with negative signed volume (the check of
level_generation/decorations/mm8_3d/animated/scripts/check_winding.py), in every mesh and LOD of a GLB.
The parts this finds are collapsed bits of decimation (a 6-triangle spike remnant at LOD0, wing shells collapsed
into 4-triangle tetrahedra at LOD2); turned outward they cull like the rest. Usage: fix_winding.py in.glb out.glb"""
import json, struct, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'level_generation' / 'decorations' / 'mm8_3d' / 'animated' / 'scripts'))
sys.path.insert(0, str(REPO / 'tools'))
from check_winding import array, components  # noqa: E402
from link_static_model_lods import read_glb  # noqa: E402

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src)
binary = bytearray(binary)
flipped = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        mat = doc['materials'][prim['material']]
        if mat.get('doubleSided') or mat.get('alphaMode') == 'BLEND':
            continue
        pos = array(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
        acc = doc['accessors'][prim['indices']]
        view = doc['bufferViews'][acc['bufferView']]
        dtype = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[acc['componentType']]
        start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        idx = np.frombuffer(binary, dtype, acc['count'], start).copy().reshape(-1, 3)
        keys = [tuple(np.round(p, 5)) for p in pos]
        changed = False
        for part in components(idx.astype(np.int64), keys):
            t = idx[part].astype(np.int64)
            edges = defaultdict(int)
            for tri in t:
                for i in range(3):
                    edges[tuple(sorted((keys[tri[i]], keys[tri[(i + 1) % 3]])))] += 1
            if not all(n == 2 for n in edges.values()):
                continue
            a, b, c = pos[t[:, 0]], pos[t[:, 1]], pos[t[:, 2]]
            if np.einsum('ij,ij->i', a, np.cross(b, c)).sum() < 0:
                idx[part] = idx[part][:, [0, 2, 1]]
                flipped += 1
                changed = True
        if changed:
            binary[start:start + idx.nbytes] = idx.astype(dtype).tobytes()
enc = json.dumps(doc, separators=(',', ':')).encode()
enc += b' ' * (-len(enc) % 4)
binary += b'\0' * (-len(binary) % 4)
dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a)
                + enc + struct.pack('<II', len(binary), 0x004e4942) + bytes(binary))
print('FLIPPED', flipped, dst)
