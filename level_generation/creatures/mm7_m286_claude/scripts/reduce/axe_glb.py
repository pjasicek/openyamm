"""Shared GLB helpers for the axe scripts: read a GLB, read accessors as numpy arrays."""
import json
import struct
import numpy as np


def read(path):
    b = open(path, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]
    return json.loads(b[20:20 + n]), b, 20 + n + 8


def acc(doc, b, base, i):
    a = doc['accessors'][i]; bv = doc['bufferViews'][a['bufferView']]
    comp = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a['componentType']]
    k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    return np.frombuffer(b, comp, a['count'] * k, base + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], k)


def prim(doc, b, base, mesh):
    p = doc['meshes'][mesh]['primitives'][0]
    return (acc(doc, b, base, p['attributes']['POSITION']).astype(float), acc(doc, b, base, p['attributes']['NORMAL']).astype(float),
            acc(doc, b, base, p['attributes']['TEXCOORD_0']).astype(float), acc(doc, b, base, p['indices']).reshape(-1, 3).astype(int))
