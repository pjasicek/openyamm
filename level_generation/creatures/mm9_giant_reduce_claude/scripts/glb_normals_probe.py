"""Per primitive of the LOD0 mesh: how many split positions carry different normals (hard edges) and how far the
vertex normals are from the area-weighted smooth normal (custom/flat shading). Usage: glb_normals_probe.py <glb> [mesh index]"""
import json, struct, sys
import numpy as np
d = open(sys.argv[1], 'rb').read(); n = struct.unpack('<I', d[12:16])[0]; g = json.loads(d[20:20 + n]); b = d[20 + n + 8:]
def acc(i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
    k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]; dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); cnt = a['count'] * k
    st = bv.get('byteStride')
    if st and st != k * np.dtype(dt).itemsize:
        raw = np.frombuffer(b, np.uint8, a['count'] * st, off).reshape(a['count'], st)[:, :k * np.dtype(dt).itemsize]
        return raw.copy().view(dt).reshape(a['count'], k)
    return np.frombuffer(b, dt, cnt, off).reshape(a['count'], k) if k > 1 else np.frombuffer(b, dt, cnt, off)
mi = int(sys.argv[2]) if len(sys.argv) > 2 else 0
for p in g['meshes'][mi]['primitives']:
    P = acc(p['attributes']['POSITION']); N = acc(p['attributes']['NORMAL']); I = acc(p['indices']).reshape(-1, 3)
    key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
    sm = np.zeros((inv.max() + 1, 3))
    for k in range(3):
        np.add.at(sm, inv[I[:, k]], fn)
    sm /= np.linalg.norm(sm, axis=1, keepdims=True) + 1e-12
    dev = np.degrees(np.arccos(np.clip((N * sm[inv]).sum(1), -1, 1)))
    # split positions with different normals
    groups = {}
    for vi, gi in enumerate(inv):
        groups.setdefault(gi, []).append(vi)
    hard = sum(1 for vs in groups.values() if len(vs) > 1 and np.ptp(N[vs], axis=0).max() > 0.05)
    print(g['materials'][p['material']]['name'], 'verts', len(P), 'positions', inv.max() + 1, 'split positions with differing normals', hard,
          'normal vs smooth deg p50/p90/max', np.round(np.percentile(dev, [50, 90, 100]), 1))
