#!/usr/bin/env python3
"""Put the composed retexture maps and tier ramps into a runtime GLB: each image is replaced by name (basecolor,
metal_rough, normal, region_mask -> textures/arc1_<label>_<key>.png, renamed arc1_<key>_retex) and every material's
openyamm_region_ramps take the variant's ramp (Archer_A/B/C -> arc1_a/b/c); unreferenced data is compacted.
Usage: patch_maps.py <in.glb> <out.glb> <label>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
src, out, label = sys.argv[1:4]
doc, binary = R.read_glb(src); binary = bytearray(binary)
for im in doc['images']:
    key = next(k for k in ('basecolor', 'metal_rough', 'normal', 'region_mask') if k in im['name'])
    data = (P / 'textures' / f'arc1_{label}_{key}.png').read_bytes()
    binary += b'\0' * (-len(binary) % 4)
    view = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}
    binary += data; doc['bufferViews'].append(view)
    im['bufferView'] = len(doc['bufferViews']) - 1; im['name'] = f'arc1_{key}_retex'; im['mimeType'] = 'image/png'
ramps = json.loads((P / 'textures' / f'arc1_{label}_ramps.json').read_text())
for m in doc['materials']:
    variant = 'arc1_' + m['name'].split('_')[-1].lower()
    m['extras']['openyamm_region_ramps'] = ramps[variant]
doc, packed = R._compact(doc, bytes(binary))
R.write_glb(out, doc, packed)
print('PATCHED', out, [im['name'] for im in doc['images']], [m['name'] for m in doc['materials']])
