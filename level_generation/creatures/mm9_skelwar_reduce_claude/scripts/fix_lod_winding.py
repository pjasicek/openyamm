#!/usr/bin/env python3
"""Decimation turned the thin dagger inside out in the coarse LODs (check_winding): closed parts of LOD and shadow meshes with a negative signed volume get their triangles reversed. Args: <in glb> <out glb>"""
import json, struct, sys
from pathlib import Path
import numpy as np
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); bin_ = bytearray(raw[28 + n:])


def view(i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]; off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    w = {'SCALAR': 1, 'VEC3': 3}[a['type']]; dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    return np.frombuffer(bin_, dt, a['count'] * w, off).reshape(a['count'], w).copy(), off, dt


fixed = 0
for m in doc['meshes']:
    if 'LOD' not in m.get('name', '') and 'Shadow' not in m.get('name', ''): continue
    for p in m['primitives']:
        P = view(p['attributes']['POSITION'])[0].astype(np.float64); idx, off, dt = view(p['indices']); T = idx.reshape(-1, 3).astype(np.int64)
        _, wid = np.unique(np.round(P, 5), axis=0, return_inverse=True); wid = wid.ravel(); W = wid[T]
        par = np.arange(wid.max() + 1)

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]; x = par[x]
            return x
        for a, b, c in W:
            ra, rb = find(a), find(b); par[ra] = rb; ra, rc = find(rb), find(c); par[ra] = rc
        root = np.array([find(int(x)) for x in W[:, 0]])
        for r in np.unique(root):
            f = np.where(root == r)[0]; t = P[T[f]]
            e = {}
            for tri in W[f]:
                for i in range(3):
                    k = tuple(sorted((int(tri[i]), int(tri[(i + 1) % 3])))); e[k] = e.get(k, 0) + 1
            if any(v % 2 for v in e.values()): continue
            vol = np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6
            if vol < 0:
                T[f] = T[f][:, ::-1]; fixed += 1
        bin_[off:off + idx.size * np.dtype(dt).itemsize] = T.astype(dt).tobytes()
# (the skeleton's copy cut its chain at LOD2 here; the Skeleton Warrior keeps LOD1-3 as installed)
js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
body = bytes(bin_)
Path(dst).write_bytes(struct.pack('<III', 0x46546C67, 2, 20 + len(js) + 8 + len(body)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(body), 0x004E4942) + body)
print('LOD winding fixed', fixed)
