#!/usr/bin/env python3
"""The sphinxes' collision proxies (D-141, F61): each model's LOD2 mesh alone, in the visible model's coordinates, as
a plain GLB of triangles (no material, no LODs) for `collision_model:` in worlds/xeen/models/decorations.yml.

Why LOD2 and not `collision_model: lod` (LOD3): measured 2026-11-25 against LOD0 below 1,300 (the party's reach),
LOD3 lies up to 40 inside LOD0 at the north sphinx's paws, 33 at its door frame and 23 at its haunches (south 19, 19,
17), over D-141's 16; LOD2 lies at most 8 (north) and 11 (south) inside. 3,400 + 2,091 triangles.

    python3 level_generation/decorations/xeen_sphinx_claude/scripts/collision_proxy.py

Reads the sources (assets_source/worlds/xeen/models/xeen_deco_sphinx_<side>.glb) and writes
export/xeen_deco_sphinx_<side>_collision.glb; install each with
`tools/install_model.py <export> --world xeen` (runtime copy worlds/xeen/models/xeen_deco_sphinx_<side>_collision.glb).
"""
import json
import struct
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = PROJECT.parents[2]
SOURCES = REPO / 'assets_source/worlds/xeen/models'
LOD = 2


def read_mesh(path, name):
    raw = path.read_bytes()
    jlen = struct.unpack_from('<I', raw, 12)[0]
    gj = json.loads(raw[20:20 + jlen])
    bin_off = 20 + jlen + 8
    assert all(not ({'matrix', 'rotation', 'scale', 'translation'} & set(n)) for n in gj['nodes']), 'node transforms'
    mesh = next(m for m in gj['meshes'] if m['name'] == name)

    def acc(i):
        a = gj['accessors'][i]
        bv = gj['bufferViews'][a['bufferView']]
        comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a['componentType']]
        n = {'SCALAR': 1, 'VEC3': 3}[a['type']]
        assert 'byteStride' not in bv or bv['byteStride'] == 4 * n
        arr = np.frombuffer(raw, comp, a['count'] * n, bin_off + bv.get('byteOffset', 0) + a.get('byteOffset', 0))
        return arr.reshape(a['count'], n) if n > 1 else arr

    positions, indices = [], []
    base = 0
    for p in mesh['primitives']:
        v = acc(p['attributes']['POSITION']).astype(np.float32)
        positions.append(v)
        indices.append(acc(p['indices']).astype(np.uint32) + base)
        base += len(v)
    return np.concatenate(positions), np.concatenate(indices)


def write_glb(path, name, positions, indices):
    pos = positions.astype('<f4').tobytes()
    idx = indices.astype('<u4').tobytes()
    gj = {
        'asset': {'version': '2.0', 'generator': 'xeen_sphinx_claude/scripts/collision_proxy.py'},
        'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'name': name, 'mesh': 0}],
        'meshes': [{'name': name, 'primitives': [{'attributes': {'POSITION': 0}, 'indices': 1, 'mode': 4}]}],
        'accessors': [
            {'bufferView': 0, 'componentType': 5126, 'count': len(positions), 'type': 'VEC3',
             'min': [float(v) for v in positions.min(0)], 'max': [float(v) for v in positions.max(0)]},
            {'bufferView': 1, 'componentType': 5125, 'count': len(indices), 'type': 'SCALAR'}],
        'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': len(pos), 'target': 34962},
                        {'buffer': 0, 'byteOffset': len(pos), 'byteLength': len(idx), 'target': 34963}],
        'buffers': [{'byteLength': len(pos) + len(idx)}],
    }
    js = json.dumps(gj, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    binary = pos + idx
    binary += b'\0' * (-len(binary) % 4)
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binary))
    out += struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(binary), 0x004E4942) + binary
    path.write_bytes(out)


def main():
    for side in ('north', 'south'):
        name = 'xeen_deco_sphinx_%s' % side
        positions, indices = read_mesh(SOURCES / (name + '.glb'), '%s_LOD%d' % (name, LOD))
        target = PROJECT / 'export' / (name + '_collision.glb')
        write_glb(target, name + '_collision', positions, indices)
        print('%s: %d triangles, bounds %s .. %s m' % (target.relative_to(REPO), len(indices) // 3,
                                                        np.round(positions.min(0), 2), np.round(positions.max(0), 2)))


if __name__ == '__main__':
    main()
