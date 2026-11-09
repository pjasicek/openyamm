"""Minimal GLB read/write helpers (JSON chunk + BIN chunk) and accessor decoding for the splice/compare scripts."""
import json, struct
import numpy as np

COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]; doc = json.loads(b[20:20 + n])
    rest = 20 + n; binary = b''
    if rest < len(b):
        m = struct.unpack('<I', b[rest:rest + 4])[0]; binary = b[rest + 8:rest + 8 + m]
    return doc, bytearray(binary)


def write(path, doc, binary):
    js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
    binary = bytes(binary) + b'\0' * (-len(binary) % 4)
    doc_len = 12 + 8 + len(js) + (8 + len(binary) if binary else 0)
    out = struct.pack('<III', 0x46546C67, 2, doc_len) + struct.pack('<I', len(js)) + b'JSON' + js
    if binary:
        out += struct.pack('<I', len(binary)) + b'BIN\0' + binary
    open(path, 'wb').write(out)


def accessor(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    dt = np.dtype(COMP[a['componentType']]); n = NCOMP[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', 0) or dt.itemsize * n
    if stride == dt.itemsize * n:
        return np.frombuffer(binary, dt, a['count'] * n, off).reshape(a['count'], n)
    return np.array([np.frombuffer(binary, dt, n, off + k * stride) for k in range(a['count'])])


def clips(doc, binary):
    """{anim name: {(node name, path): (times, values)}}"""
    out = {}
    for an in doc.get('animations', []):
        ch = {}
        for c in an['channels']:
            s = an['samplers'][c['sampler']]; t = c['target']
            ch[(doc['nodes'][t['node']]['name'], t['path'])] = (accessor(doc, binary, s['input'])[:, 0],
                                                               accessor(doc, binary, s['output']))
        out[an['name']] = ch
    return out
