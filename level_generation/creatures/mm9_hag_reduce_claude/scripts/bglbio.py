"""Small GLB reader: doc, binary, accessor -> numpy."""
import json, struct
import numpy as np
SIZES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
DT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
K = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(path):
    raw = open(path, 'rb').read()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]


def acc(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    k = K[a['type']]; s = SIZES[a['componentType']]
    st = v.get('byteStride') or s * k
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    out = np.ndarray((a['count'], k), DT[a['componentType']], binary, off, (st, s)).copy()
    if a.get('normalized') and a['componentType'] in (5121, 5123):
        out = out.astype(np.float64) / (255 if a['componentType'] == 5121 else 65535)
    return out


def prims(doc, binary, mesh_index):
    out = []
    for p in doc['meshes'][mesh_index]['primitives']:
        at = p['attributes']
        out.append(dict(material=doc['materials'][p['material']]['name'], T=acc(doc, binary, p['indices']).reshape(-1, 3).astype(np.int64),
                        **{k: acc(doc, binary, v) for k, v in at.items()}))
    return out
