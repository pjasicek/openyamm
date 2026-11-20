"""Small GLB reader: read_glb(path) -> (doc, bin); acc(doc, bin, index) -> numpy array."""
import json, struct
import numpy as np
def read_glb(p):
    raw = open(p, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]
def acc(d, b, i):
    a = d['accessors'][i]; v = d['bufferViews'][a['bufferView']]; o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    c = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    t = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    return np.frombuffer(b, t, a['count'] * c, o).reshape(a['count'], c)
