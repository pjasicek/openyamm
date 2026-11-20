#!/usr/bin/env python3
"""Swap the composed bat maps (base colour, metal/roughness, normal, region mask) into a bat GLB whose geometry
already carries the new UVs (swap_lod0.py output). Images are replaced in place (the tier materials share them); the
accepted ramps stay; unreferenced buffer data is compacted. Usage: apply_textures.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; T = P / 'textures'
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = R.read_glb(src); binary = bytearray(binary)
m = next(x for x in doc['materials'] if x['name'] == 'Bat_A')
slots = {m['pbrMetallicRoughness']['baseColorTexture']['index']: T / 'bat_basecolor_2k.png',
         m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']: T / 'bat_metal_rough_1k.png',
         m['normalTexture']['index']: T / 'bat_normal_1k.png',
         m['extras']['openyamm_region_mask']['index']: T / 'bat_region_mask.png'}
assert len(slots) == 4
for tex, path in slots.items():
    data = path.read_bytes(); img = doc['textures'][tex]['source']
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    doc['images'][img] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': path.stem}
doc, binary = R._compact(doc, bytes(binary))
R.write_glb(dst, doc, binary); print('APPLIED', len(slots), 'images ->', dst, f'{len(binary) / 1e6:.1f} MB')
