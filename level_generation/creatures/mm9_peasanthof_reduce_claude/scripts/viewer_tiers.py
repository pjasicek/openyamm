#!/usr/bin/env python3
"""Review-viewer GLBs of one half-orc woman (M=1|2): three.js has no region ramps, so each tier's ramps are baked into its body
base colour with the engine rule, in copies of the given GLB. The baked images are tex_extract.py's (the GLB's own tone image,
mask and ramps: work/hof$M/tex_<body>_<A|B>.png), so the installed and the reduced copies get the same pixels; the head keeps
its tier material (tier B's own head image). Variants are resolved to plain materials.
Usage: M=1 viewer_tiers.py <glb> <prefix> -> work/hof$M/viewer_<prefix>_<a|b|c>.glb"""
import os
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402
M_ = os.environ['M']; WK = HERE / 'work' / f'hof{M_}'
GLB = Path(sys.argv[1]); PREFIX = sys.argv[2]
tiers = [('phof1_a', 'A', 'PeasantHOF_A'), ('phof1_b', 'B', 'PeasantHOF_B')] if M_ == '1' else [('phof2_c', 'A', 'PeasantHOF_C')]
body = 'PeasantHOF_A' if M_ == '1' else 'PeasantHOF_C'
for idx, (variant, t, mname) in enumerate(tiers):
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    data = (WK / f'tex_{body}_{t}.png').read_bytes()
    mat = doc['materials'][names[mname]]
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{body}_{variant}'})
    doc['textures'].append({'source': len(doc['images']) - 1,
                            'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
    mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    mat.get('extras', {}).pop('openyamm_region_ramps', None)
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [x for x in doc.get('extensionsUsed', []) if x != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(WK / f'viewer_{PREFIX}_{variant.split("_")[1]}.glb', d2, b2)
    print('viewer', variant, WK / f'viewer_{PREFIX}_{variant.split("_")[1]}.glb')
