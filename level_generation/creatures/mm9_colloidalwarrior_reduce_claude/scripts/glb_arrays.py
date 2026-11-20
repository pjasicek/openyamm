"""GLB primitive arrays (positions, normals, uvs, joints, weights, indices) by mesh index and material name.
Imported by the mallet rebuild scripts."""
import json, struct
import numpy as np
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(path):
    d = open(path, 'rb').read(); n = struct.unpack('<I', d[12:16])[0]
    return json.loads(d[20:20 + n]), d[20 + n + 8:]


def acc(g, b, i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]; k = NC[a['type']]; dt = CT[a['componentType']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); st = bv.get('byteStride'); isz = np.dtype(dt).itemsize
    if st and st != k * isz:
        raw = np.frombuffer(b, np.uint8, a['count'] * st, off).reshape(a['count'], st)[:, :k * isz]
        out = raw.copy().view(dt).reshape(a['count'], k)
    else:
        out = np.frombuffer(b, dt, a['count'] * k, off).reshape(a['count'], k).copy()
    if a.get('normalized') and dt != np.float32:
        out = out.astype(np.float32) / np.iinfo(dt).max
    return out


def prim(g, b, mesh, material):
    for p in g['meshes'][mesh]['primitives']:
        if g['materials'][p['material']]['name'] == material:
            at = p['attributes']
            return {'P': acc(g, b, at['POSITION']), 'N': acc(g, b, at['NORMAL']), 'UV': acc(g, b, at['TEXCOORD_0']),
                    'J': acc(g, b, at['JOINTS_0']), 'W': acc(g, b, at['WEIGHTS_0']), 'I': acc(g, b, p['indices']).reshape(-1, 3)}
    raise KeyError(material)
