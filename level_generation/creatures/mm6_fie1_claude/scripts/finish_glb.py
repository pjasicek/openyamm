#!/usr/bin/env python3
"""Runtime GLB of the fire elemental: export/mm6_fie1_raw.glb -> export/mm6_fie1.glb.

LODs: the FireElemental mesh lists FireElemental_LOD1 and _LOD2 under extras.openyamm_lods; their own nodes lose
their mesh and skin (the engine skins a LOD with its owner's node).

Materials, all unlit like the sprite they replace, without specular sheen or creature edge darkening:
FireElemental_Body opaque; FireElemental_Flame and _Fringe alpha blended, single-sided (build_model.py orders their
faces), repeating in u and v and scrolling upward (SCROLL texture tiles per second; one tile is about 0.6 of the cage
height); FireElemental_Fx alpha blended, clamped.

Tiers: the restored package recolours only the dark red figure (materials.coverage, LUTs in recolor_vectors.json:
palette 204 unchanged, 728 green, 729 blue); its flames are the same in every tier. So only the body material gets
a region (the whole figure) and ramps fitted to that recolour of its own baked texture, through
claude_shared/region_variants.py: fie1_a/b/c.
"""
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
RESTORED = HERE.parent / 'mm6_fie1' / 'redo_2x'
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants  # noqa: E402

# Texture tiles per second in v. A tile spans about 0.6 of the 2.4-unit cage, so 0.4 tiles/s raises the flames by
# about 0.58 units (40 game units) a second.
SCROLL = 0.4
VARIANTS = {'fie1_a': 204, 'fie1_b': 728, 'fie1_c': 729}
REPEAT, CLAMP = 10497, 33071
LUMA = np.array([0.2126, 0.7152, 0.0722])


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


def fit_tiers():
    """Region mask (the whole figure texture) and per-tier ramps fitted to the restored recolour of the baked body."""
    vectors = {int(k): v for k, v in json.loads((RESTORED / 'recolor_vectors.json').read_text()).items()}
    base = np.asarray(Image.open(HERE / 'textures' / 'fie1_body.png').convert('RGB'), dtype=np.float64) / 255.0
    level = np.clip(np.round((base @ LUMA) * 255), 0, 255).astype(int)
    targets = {variant: base if palette == 204 else np.array(vectors[palette])[level]
               for variant, palette in VARIANTS.items()}
    weight = np.ones(base.shape[:2])
    ramps, report = region_variants.fit_ramps(base, targets, weight)
    region_variants.write_mask([weight], HERE / 'textures' / 'fie1_body_mask.png', size=64)
    config = {'variants': list(VARIANTS), 'palettes': VARIANTS, 'fit_report': report,
              'materials': [{'base': 'FireElemental_Body', 'prefix': 'FireElemental_Body',
                             'mask': 'fie1_body_mask.png', 'ramps': {v: [ramps[v]] for v in VARIANTS}}]}
    path = HERE / 'textures' / 'fie1_ramps.json'
    path.write_text(json.dumps(config, indent=1))
    return path, report


def material_kind(name):
    for kind in ('Body', 'Flame', 'Fringe', 'Fx'):
        if name == f'FireElemental_{kind}' or name.startswith(f'FireElemental_{kind}.'):
            return kind
    sys.exit(f'unexpected material {name}')


def main():
    source = HERE / 'export' / 'mm6_fie1_raw.glb'
    staged = HERE / 'export' / 'mm6_fie1_lods.glb'
    target = HERE / 'export' / 'mm6_fie1.glb'
    document, binary = read_glb(source)
    if len(document.get('skins', [])) != 1:
        sys.exit('expected one skin shared by every LOD')
    names = [mesh['name'] for mesh in document['meshes']]
    lods = [names.index(name) for name in ('FireElemental_LOD1', 'FireElemental_LOD2')]
    for node in document['nodes']:
        if node.get('mesh') in lods:
            node.pop('mesh')
            node.pop('skin', None)
    document['meshes'][names.index('FireElemental')].setdefault('extras', {})['openyamm_lods'] = lods
    for mesh in document['meshes']:
        kinds = [material_kind(document['materials'][p['material']]['name']) for p in mesh['primitives']]
        if kinds != ['Body', 'Flame', 'Fringe', 'Fx']:
            sys.exit(f'{mesh["name"]}: primitive order {kinds}, expected body, flame, fringe, fx')
    samplers = document.setdefault('samplers', [])
    used = document.setdefault('extensionsUsed', [])
    if 'KHR_materials_unlit' not in used:
        used.append('KHR_materials_unlit')
    for material in document['materials']:
        kind = material_kind(material['name'])
        pbr = material.setdefault('pbrMetallicRoughness', {})
        pbr['metallicFactor'] = 0.0
        pbr['roughnessFactor'] = 1.0
        material.pop('doubleSided', None)
        material.pop('emissiveTexture', None)
        material.pop('emissiveFactor', None)
        material['extensions'] = {'KHR_materials_unlit': {}}
        material['extras'] = {'openyamm_specular': 0.0, 'openyamm_edge_darkening': 0.0}
        wrap = CLAMP
        if kind == 'Body':
            material['alphaMode'] = 'OPAQUE'
        else:
            material['alphaMode'] = 'BLEND'
            if kind in ('Flame', 'Fringe'):
                material['extras']['openyamm_uv_scroll'] = [0.0, SCROLL]
                wrap = REPEAT
        texture = document['textures'][pbr['baseColorTexture']['index']]
        samplers.append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': wrap, 'wrapT': wrap})
        texture['sampler'] = len(samplers) - 1
    write_glb(staged, document, binary)
    ramps, report = fit_tiers()
    print('tier fit (8-bit error):', json.dumps(report))
    region_variants.apply_variants(staged, target, ramps)
    staged.unlink()
    print('wrote', target)


if __name__ == '__main__':
    main()
