#!/usr/bin/env python3
"""Runtime GLB of the air elemental: export/mm6_aie1_raw.glb -> export/mm6_aie1.glb.

LODs: the AirElemental mesh lists AirElemental_LOD1 and _LOD2 under extras.openyamm_lods; their own nodes lose their
mesh and skin (the engine skins a LOD with its owner's node). Tiers: textures/aie1_ramps.json through
claude_shared/region_variants.py (one material per tier, aie1_a/b/c, sharing every image).

The wind is alpha blended and single-sided (build_model.py orders its faces back to front), spins by texture scroll
(the core turns once per 1 / SCROLL seconds; the outer shell repeats the texture twice round, so it turns at half
that), is unlit and has no specular sheen or creature edge darkening.
"""
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants  # noqa: E402

SCROLL = 1.0


def read_glb(path):
    data = path.read_bytes()
    offset, document, binary = 12, None, b''
    while offset < len(data):
        size, kind = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8:offset + 8 + size]
        if kind == 0x4E4F534A:
            document = json.loads(chunk)
        else:
            binary = chunk
        offset += 8 + size
    return document, binary


def write_glb(path, document, binary):
    text = json.dumps(document, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    binary = bytes(binary) + b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    path.write_bytes(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(text), 0x4E4F534A) + text
                     + struct.pack('<II', len(binary), 0x004E4942) + binary)


def main():
    source = HERE / 'export' / 'mm6_aie1_raw.glb'
    staged = HERE / 'export' / 'mm6_aie1_lods.glb'
    target = HERE / 'export' / 'mm6_aie1.glb'
    document, binary = read_glb(source)
    if len(document.get('skins', [])) != 1:
        sys.exit('expected one skin shared by every LOD')
    names = [mesh['name'] for mesh in document['meshes']]
    lods = [names.index(name) for name in ('AirElemental_LOD1', 'AirElemental_LOD2')]
    for node in document['nodes']:
        if node.get('mesh') in lods:
            node.pop('mesh')
            node.pop('skin', None)
    document['meshes'][names.index('AirElemental')].setdefault('extras', {})['openyamm_lods'] = lods
    if len(document['materials']) != 1:
        sys.exit('expected one material')
    material = document['materials'][0]
    material['alphaMode'] = 'BLEND'
    material.pop('doubleSided', None)
    pbr = material.setdefault('pbrMetallicRoughness', {})
    pbr['metallicFactor'] = 0.0
    pbr['roughnessFactor'] = 1.0
    # Unlit like the sprite it replaces: the wind shows its own colours under any light.
    material['extensions'] = {'KHR_materials_unlit': {}}
    used = document.setdefault('extensionsUsed', [])
    if 'KHR_materials_unlit' not in used:
        used.append('KHR_materials_unlit')
    material['extras'] = {
        'openyamm_uv_scroll': [SCROLL, 0.0],
        'openyamm_specular': 0.0,
        'openyamm_edge_darkening': 0.0,
    }
    for sampler in document.get('samplers', []):
        sampler['wrapS'] = 10497
        sampler['wrapT'] = 33071
    write_glb(staged, document, binary)
    region_variants.apply_variants(staged, target, HERE / 'textures' / 'aie1_ramps.json')
    staged.unlink()
    print('wrote', target)


if __name__ == '__main__':
    main()
