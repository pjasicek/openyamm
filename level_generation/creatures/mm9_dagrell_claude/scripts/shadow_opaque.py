#!/usr/bin/env python3
"""Keep a creature's dedicated shadow LODs opaque in every colour tier (2026-10-30, the see-through Spectre Dagrell).

The engine refuses dedicated shadow LODs with a non-opaque material in any variant ("dedicated shadow LODs require
opaque geometry", engine/models/GltfModelLoader.cpp validateMeshLods). The shadow meshes share the tier materials
(region_variants.py), so every shadow primitive's variant mapping onto a blended material is moved to the
primitive's opaque default material: only geometry reaches the shadow pass, so the shadow keeps its shape and the
blended tier still casts it.

Usage: shadow_opaque.py in.glb out.glb
"""
import json
import struct
import sys
from pathlib import Path


def main():
    src, dst = sys.argv[1:3]
    raw = Path(src).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n])
    binary = raw[28 + n:]
    mats = doc['materials']
    moved = 0
    for mesh in doc['meshes']:
        if 'shadow' not in (mesh.get('name') or '').lower():
            continue
        for prim in mesh['primitives']:
            default = prim.get('material')
            assert default is not None and mats[default].get('alphaMode', 'OPAQUE') == 'OPAQUE', mesh.get('name')
            ext = prim.get('extensions', {}).get('KHR_materials_variants')
            if ext is None:
                continue
            for mapping in ext['mappings']:
                if mats[mapping['material']].get('alphaMode', 'OPAQUE') != 'OPAQUE':
                    mapping['material'] = default
                    moved += 1
    enc = json.dumps(doc, separators=(',', ':')).encode()
    enc += b' ' * (-len(enc) % 4)
    Path(dst).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                          + struct.pack('<II', len(enc), 0x4e4f534a) + enc
                          + struct.pack('<II', len(binary), 0x004e4942) + binary)
    print(f'{dst}: {moved} shadow variant mappings moved to opaque materials')


if __name__ == '__main__':
    main()
