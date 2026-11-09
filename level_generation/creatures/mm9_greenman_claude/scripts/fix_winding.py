#!/usr/bin/env python3
"""Turn inverted thin closed parts outward (mm9_greenman, 2026-11-04): Meshy's leaf cards are thin shells; the ones
build_export_v2.py's hole fill closed (open cards with a 3-8 edge rim) are double-layer leaves of ~0 volume whose sign
is arbitrary, and check_winding.py reads 50 of them as inverted closed parts in LOD0 (and more in the LODs/shadows).
For every closed connected part (every edge shared by exactly two triangles, positions welded at 1e-5) of every mesh
whose signed volume is negative, the triangle winding is reversed (normals unchanged: each layer of a two-layer leaf
keeps its shading; a closed thin shell shows a layer from either side either way). Usage: fix_winding.py in.glb out.glb"""
import json, re, struct, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

MAX_TRIS = 400
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); binary = bytearray(raw[28 + n:])
T = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
Wd = {'SCALAR': 1, 'VEC3': 3}


def arr(i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    dt = np.dtype(T[a['componentType']]); w = Wd[a['type']]
    st = v.get('byteStride', dt.itemsize * w); o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    r = np.frombuffer(binary, np.uint8, a['count'] * st, o).reshape(a['count'], st)
    return r[:, :dt.itemsize * w].copy().view(dt).reshape(a['count'], w)


flipped = parts_flipped = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        pos = arr(prim['attributes']['POSITION']).astype(np.float64)
        tris = arr(prim['indices']).reshape(-1, 3).astype(np.int64)
        keys = [tuple(np.round(p, 5)) for p in pos]
        parent = list(range(len(tris)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        owner = {}
        for t, tri in enumerate(tris):
            for v in tri:
                k = keys[v]
                if k in owner:
                    parent[find(owner[k])] = find(t)
                else:
                    owner[k] = t
        groups = defaultdict(list)
        for t in range(len(tris)):
            groups[find(t)].append(t)
        change = False
        for part in groups.values():
            if len(part) > MAX_TRIS:
                continue
            t = tris[part]
            e = defaultdict(int)
            for tri in t:
                for i in range(3):
                    e[tuple(sorted((keys[tri[i]], keys[tri[(i + 1) % 3]])))] += 1
            if not all(c == 2 for c in e.values()):
                continue
            a, b, c = pos[t[:, 0]], pos[t[:, 1]], pos[t[:, 2]]
            if np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6 < 0:
                tris[part] = tris[part][:, ::-1]
                flipped += len(part); parts_flipped += 1; change = True
        if not change:
            continue
        idx = tris.astype(np.uint32).ravel()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': idx.nbytes, 'target': 34963})
        binary += idx.tobytes()
        doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5125, 'count': int(idx.size),
                                 'type': 'SCALAR'})
        prim['indices'] = len(doc['accessors']) - 1
binary += b'\0' * (-len(binary) % 4)
doc['buffers'][0]['byteLength'] = len(binary)
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a)
                + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)
print('FIXWINDING parts', parts_flipped, 'triangles', flipped)
