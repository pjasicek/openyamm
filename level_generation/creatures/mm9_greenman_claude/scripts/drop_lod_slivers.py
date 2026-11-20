#!/usr/bin/env python3
"""Drop the tiny closed parts that collapse flat in the reduced LODs (a wattle or eye decimated to a 4-triangle
tetrahedron with ~0 volume reads as an inverted closed part in check_winding.py and is invisible anyway): in every
LOD1..3 mesh (shadow copies included), closed connected parts of at most MAX_TRIS triangles whose |volume| is below
MAX_VOL are removed from the index buffer. LOD0 is never touched. Usage: drop_lod_slivers.py in.glb out.glb"""
import json, re, struct, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

MAX_TRIS, MAX_VOL = 12, 5e-6   # m^3 (mm9_sigmund: a 6-triangle LOD2 sliver of the lining rims, -2e-6)
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


dropped = 0
for mesh in doc['meshes']:
    if not re.search(r'LOD[123]', mesh.get('name', '')):
        continue
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
        keep = np.ones(len(tris), bool)
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
            if abs(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6) < MAX_VOL:
                keep[part] = False
        if keep.all():
            continue
        dropped += int((~keep).sum())
        idx = tris[keep].astype(np.uint32).ravel()
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
print('SLIVERS dropped triangles', dropped)
