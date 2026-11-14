"""Minimal GLB reading and writing for the Oblivion weapon skins (README.md): the skin keeps the template's JSON (nodes,
names, transforms, animations, morph weights, the other materials) and replaces one primitive's vertex data and one
material's three images."""
import json
import struct

import numpy as np

TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
COUNTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read(path):
    data = open(path, 'rb').read()
    jlen = struct.unpack('<I', data[12:16])[0]
    doc = json.loads(data[20:20 + jlen])
    rest = data[20 + jlen:]
    binary = rest[8:8 + struct.unpack('<I', rest[0:4])[0]] if rest else b''
    return doc, binary


def accessor(doc, binary, index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    n = COUNTS[a['type']]
    start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    out = np.frombuffer(binary, TYPES[a['componentType']], a['count'] * n, start)
    return out.reshape(a['count'], n) if n > 1 else out


def view_bytes(doc, binary, view_index):
    view = doc['bufferViews'][view_index]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def mesh_primitive(doc, mesh_name_prefix=None):
    """(mesh index, primitive dict) of the first mesh whose name starts with the prefix (any mesh without one)."""
    for index, mesh in enumerate(doc['meshes']):
        if mesh_name_prefix is None or mesh.get('name', '').startswith(mesh_name_prefix):
            return index, mesh['primitives'][0]
    raise KeyError(mesh_name_prefix)


def share_wound_with_normals(doc, binary, prim):
    """Share of a primitive's triangles whose corner order (counter-clockwise, glTF) agrees with their vertex normals.
    The Oblivion templates measured 0 before fix_winding.py, 1 after (the bow 0.996: a few string slivers)."""
    pos = accessor(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
    nrm = accessor(doc, binary, prim['attributes']['NORMAL']).astype(np.float64)
    tri = accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
    face = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    return float(np.mean((face * nrm[tri].sum(1)).sum(1) > 0))


def write(path, doc, views):
    """Writes doc with the binary chunk rebuilt from `views` (one bytes object per bufferView, in order)."""
    blob = bytearray()
    for index, chunk in enumerate(views):
        while len(blob) % 4:
            blob.append(0)
        doc['bufferViews'][index]['byteOffset'] = len(blob)
        doc['bufferViews'][index]['byteLength'] = len(chunk)
        doc['bufferViews'][index]['buffer'] = 0
        blob += chunk
    while len(blob) % 4:
        blob.append(0)
    doc['buffers'] = [{'byteLength': len(blob)}]
    text = json.dumps(doc, separators=(',', ':')).encode()
    while len(text) % 4:
        text += b' '
    total = 12 + 8 + len(text) + 8 + len(blob)
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<III', 0x46546C67, 2, total))
        handle.write(struct.pack('<II', len(text), 0x4E4F534A) + text)
        handle.write(struct.pack('<II', len(blob), 0x004E4942) + bytes(blob))
