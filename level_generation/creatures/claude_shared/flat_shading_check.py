#!/usr/bin/env python3
"""Report how flat-shaded a GLB's first mesh is: per primitive, the share of faces whose three vertex normals all equal
the face normal, and vertices per unique position. Bodies should be about 0 flat; a smooth mesh has about 2 vertices
per position, a faceted one 5 or more. Thin wing sheets may be flat by design.

    python3 level_generation/creatures/claude_shared/flat_shading_check.py <model.glb> [...]
"""
import json
import struct
import sys

import numpy as np

COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
TYPES = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}


def load(path):
    with open(path, 'rb') as glb:
        data = glb.read()
    json_length = struct.unpack('<I', data[12:16])[0]
    return json.loads(data[20:20 + json_length]), data[20 + json_length + 8:]


def accessor(gltf, binary, index):
    entry = gltf['accessors'][index]
    view = gltf['bufferViews'][entry['bufferView']]
    size = COMPONENTS[entry['type']]
    dtype = TYPES[entry['componentType']]
    offset = view.get('byteOffset', 0) + entry.get('byteOffset', 0)
    stride = view.get('byteStride', 0)
    count = entry['count']
    item = np.dtype(dtype).itemsize * size
    if stride and stride != item:
        raw = np.frombuffer(binary, np.uint8, count=stride * count, offset=offset).reshape(count, stride)[:, :item]
        return np.frombuffer(raw.tobytes(), dtype).reshape(count, size)
    return np.frombuffer(binary, dtype, count=count * size, offset=offset).reshape(count, size)


def report(path):
    gltf, binary = load(path)
    mesh = gltf['meshes'][0]
    parts = []
    for primitive in mesh['primitives']:
        positions = accessor(gltf, binary, primitive['attributes']['POSITION'])
        normals = accessor(gltf, binary, primitive['attributes']['NORMAL'])
        faces = accessor(gltf, binary, primitive['indices']).reshape(-1, 3)
        corners = positions[faces]
        face_normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        face_normals /= np.linalg.norm(face_normals, axis=1, keepdims=True) + 1e-12
        agreement = np.einsum('fk,fvk->fv', face_normals, normals[faces])
        flat = float((agreement.min(axis=1) > 0.999).mean())
        unique = len(np.unique(positions.round(5), axis=0))
        material = gltf['materials'][primitive['material']]['name'] if 'material' in primitive else '-'
        parts.append(f'{material}: {len(faces)} faces, flat {flat:.2f}, vertices per position {len(positions) / unique:.1f}')
    print(path.rsplit('/', 1)[-1], mesh.get('name'), ' | '.join(parts))


if __name__ == '__main__':
    for glb_path in sys.argv[1:]:
        report(glb_path)
