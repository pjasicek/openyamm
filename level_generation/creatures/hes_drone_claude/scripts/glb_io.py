"""Minimal GLB reading/writing helpers (numpy)."""
import json, struct
import numpy as np

DT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    raw = open(path, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary = bytearray(binary); binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    open(path, 'wb').write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                           + struct.pack('<II', len(enc), 0x4e4f534a) + enc
                           + struct.pack('<II', len(binary), 0x004e4942) + bytes(binary))


def acc(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    dt = np.dtype(DT[a['componentType']]); c = NC[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', dt.itemsize * c)
    if stride == dt.itemsize * c:
        return np.frombuffer(binary, dt, a['count'] * c, off).reshape(a['count'], c).copy()
    rows = [np.frombuffer(binary, dt, c, off + i * stride) for i in range(a['count'])]
    return np.array(rows)
