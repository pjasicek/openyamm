#!/usr/bin/env python3
"""Move every vertex of the reduced shadow meshes (shadow LOD 1..3) to at least `margin` inside the full-detail
surface, in bind space. A decimated shadow caster that pokes out of the smooth colour surface self-shadows the
skin in a triangle pattern at medium/low shadow quality; tucked inside, it still casts the same silhouette onto
the ground. Usage: shrink_shadow_lods.py in.glb out.glb"""
import json
import struct
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

MARGIN = {1: 0.004, 2: 0.007, 3: 0.012}   # metres (model is 1.58 m tall in bind space)


def read_glb(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def view(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    comp = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    if v.get('byteStride', 0) not in (0, comp * np.dtype(dtype).itemsize):
        raise ValueError('interleaved accessor')
    return np.frombuffer(binary, dtype=dtype, count=a['count'] * comp, offset=offset).reshape(a['count'], comp), offset


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    doc, binary = read_glb(src)
    node = next(n for n in doc['nodes'] if n.get('name') == 'Thief')
    base = doc['meshes'][node['mesh']]
    shadows = base['extras']['openyamm_shadow_lods']
    ref_pos, ref_nrm = [], []
    for p in base['primitives']:
        ref_pos.append(view(doc, binary, p['attributes']['POSITION'])[0].astype(np.float64))
        ref_nrm.append(view(doc, binary, p['attributes']['NORMAL'])[0].astype(np.float64))
    ref_pos = np.concatenate(ref_pos); ref_nrm = np.concatenate(ref_nrm)
    ref_nrm /= np.maximum(np.linalg.norm(ref_nrm, axis=1, keepdims=True), 1e-9)
    tree = cKDTree(ref_pos)
    used = {}
    for mi, m in enumerate(doc['meshes']):
        for p in m['primitives']:
            used.setdefault(p['attributes']['POSITION'], set()).add(mi)
    report = {}
    for level, mesh_index in enumerate(shadows):
        if level == 0:
            continue
        for p in doc['meshes'][mesh_index]['primitives']:
            acc = p['attributes']['POSITION']
            if used[acc] != {mesh_index}:
                raise ValueError('shadow positions are shared with another mesh')
            pos, offset = view(doc, binary, acc)
            pos = pos.astype(np.float64)
            _, nn = tree.query(pos, k=1)
            # signed distance to the tangent plane of the nearest full-detail vertex (positive = outside)
            n = ref_nrm[nn]
            d = np.einsum('ij,ij->i', pos - ref_pos[nn], n)
            push = np.clip(d + MARGIN[level], 0.0, 0.015)
            pos -= n * push[:, None]
            binary[offset:offset + pos.size * 4] = pos.astype(np.float32).tobytes()
            a = doc['accessors'][acc]
            a['min'] = pos.min(0).tolist(); a['max'] = pos.max(0).tolist()
            report[doc['meshes'][mesh_index]['name']] = {'vertices': len(pos), 'moved': int((push > 0).sum()),
                                                         'max_push_mm': round(float(push.max()) * 1000, 1)}
    write_glb(dst, doc, binary)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
