#!/usr/bin/env python3
"""Mirror a skinned, animated glTF binary across X (m270: the lich is built mirrored so the shared right-hand tools -
grip solve, carry, clearance - hold its staff; the native holds it in the LEFT hand, so the export is mirrored back).
- POSITION and NORMAL x -> -x, TANGENT x -> -x and w -> -w (the bitangent flips with the handedness), triangle
  winding reversed; POSITION min/max updated;
- node translation x -> -x, rotation (x, y, z, w) -> (x, -y, -z, w), matrices and inverse bind matrices S M S
  (S = diag(-1, 1, 1, 1): a proper rotation stays proper);
- animation outputs: translation x -> -x, rotation as the nodes; scale unchanged;
- node names: '_L_' <-> '_R_' (B_L_Hand <-> B_R_Hand), so names describe the mirrored sides again.
Each accessor is converted once. Usage: mirror_glb.py in.glb out.glb"""
import json
import struct
import sys
from pathlib import Path

import numpy as np

COMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
DT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}


def read_glb(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n]); bin_len = struct.unpack_from('<I', raw, 20 + n)[0]
    return doc, bytearray(raw[28 + n:28 + n + bin_len])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                           + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def view(doc, binary, ai):
    a = doc['accessors'][ai]
    assert 'sparse' not in a, 'sparse accessors are not supported'
    bv = doc['bufferViews'][a['bufferView']]
    k = COMP[a['type']]; dt = np.dtype(DT[a['componentType']])
    stride = bv.get('byteStride', 0)
    assert stride in (0, k * dt.itemsize), 'interleaved buffer views are not supported'
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    arr = np.frombuffer(binary, dtype=dt, count=a['count'] * k, offset=off).reshape(a['count'], k)
    return arr, off


def put(binary, off, arr):
    b = arr.tobytes(); binary[off:off + len(b)] = b


S = np.diag([-1.0, 1, 1, 1])


def mirror_mat(m16):
    M = np.array(m16, np.float64).reshape(4, 4).T          # glTF matrices are column-major
    return list((S @ M @ S).T.ravel())


def main(src, dst):
    doc, binary = read_glb(src)
    done = set()

    def conv(ai, how):
        if ai in done:
            return
        done.add(ai)
        arr, off = view(doc, binary, ai); a = doc['accessors'][ai]
        out = arr.astype(np.float64).copy()
        if how == 'vec3':
            out[:, 0] *= -1
        elif how == 'tangent':
            out[:, 0] *= -1; out[:, 3] *= -1
        elif how == 'quat':
            out[:, 1] *= -1; out[:, 2] *= -1
        elif how == 'mat4':
            out = np.array([mirror_mat(r) for r in out])
        elif how == 'winding':
            out = out.reshape(-1, 3)[:, [0, 2, 1]].reshape(-1, 1)
        put(binary, off, out.astype(arr.dtype))
        if how == 'vec3' and 'min' in a and 'max' in a:
            lo, hi = list(a['min']), list(a['max'])
            lo[0], hi[0] = -a['max'][0], -a['min'][0]
            a['min'], a['max'] = lo, hi
    for mesh in doc.get('meshes', []):
        for p in mesh['primitives']:
            at = p['attributes']
            if 'POSITION' in at: conv(at['POSITION'], 'vec3')
            if 'NORMAL' in at: conv(at['NORMAL'], 'vec3')
            if 'TANGENT' in at: conv(at['TANGENT'], 'tangent')
            assert p.get('mode', 4) == 4, 'only triangle lists'
            if 'indices' in p: conv(p['indices'], 'winding')
            assert 'targets' not in p, 'morph targets are not supported'
    for sk in doc.get('skins', []):
        if 'inverseBindMatrices' in sk:
            conv(sk['inverseBindMatrices'], 'mat4')
    for n in doc.get('nodes', []):
        if 'translation' in n:
            n['translation'][0] *= -1
        if 'rotation' in n:
            n['rotation'][1] *= -1; n['rotation'][2] *= -1
        if 'matrix' in n:
            n['matrix'] = mirror_mat(n['matrix'])
        if 'name' in n:
            nm = n['name']
            n['name'] = nm.replace('_L_', '_TMP_').replace('_R_', '_L_').replace('_TMP_', '_R_')
    for an in doc.get('animations', []):
        for ch in an['channels']:
            path = ch['target']['path']; out = an['samplers'][ch['sampler']]['output']
            if path == 'translation':
                conv(out, 'vec3')
            elif path == 'rotation':
                conv(out, 'quat')
    write_glb(dst, doc, binary)
    print('MIRROR', src, '->', dst, 'accessors converted', len(done))


if __name__ == '__main__':
    main(*sys.argv[1:3])
