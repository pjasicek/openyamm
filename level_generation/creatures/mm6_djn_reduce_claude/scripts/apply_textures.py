#!/usr/bin/env python3
"""Swap the composed atlases (body half new, head half installed) into a djinn GLB whose geometry already carries the
new body UVs (swap_lod0.py output). Images replaced in place (the tier materials share them); ramps unchanged; unused
buffer data compacted. Usage: apply_textures.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; T = P / 'textures'
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
doc, binary = R.read_glb(sys.argv[1]); binary = bytearray(binary)
m = next(x for x in doc['materials'] if x['name'] == 'Genie_A')
slots = {m['pbrMetallicRoughness']['baseColorTexture']['index']: T / 'djn_basecolor_atlas.png',
         m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']: T / 'djn_metal_rough_atlas.png',
         m['normalTexture']['index']: T / 'djn_normal_atlas.png',
         m['extras']['openyamm_region_mask']['index']: T / 'djn_region_mask_atlas.png'}
for tex, path in slots.items():
    data = path.read_bytes(); img = doc['textures'][tex]['source']
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    doc['images'][img] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': path.stem}
doc, binary = R._compact(doc, bytes(binary)); R.write_glb(sys.argv[2], doc, binary)
print('APPLIED', len(slots), 'images ->', sys.argv[2], f'{len(binary) / 1e6:.1f} MB')
