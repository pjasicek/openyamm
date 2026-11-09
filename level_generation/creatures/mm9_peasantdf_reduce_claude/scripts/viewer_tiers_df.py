#!/usr/bin/env python3
"""Review-viewer GLBs (three.js has no region ramps): per tier, a copy of the GLB with that tier's materials selected and
their base colours replaced by the tier colours baked with the engine rule (work/tex_p<prim>_d<n><tier>.png from
tex_extract_df.py: the installed images, which the candidates share byte for byte). LOD0 only is what the viewer draws.
Usage: viewer_tiers_df.py <glb> <n> <prefix> -> work/viewer_<prefix>_d<n><tier>.glb for every tier of design n"""
import io, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402
GLB, n, PREFIX = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
doc0, _ = RV.read_glb(GLB)
variants = [v['name'] for v in doc0['extensions']['KHR_materials_variants']['variants']]
for idx, variant in enumerate(variants):
    tier = variant.split('_')[1].upper()
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    node = next(x for x in doc['nodes'] if x.get('name') == 'PeasantDF' and 'mesh' in x)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    done = set()
    for pi, prim in enumerate(doc['meshes'][node['mesh']]['primitives']):
        mat = doc['materials'][prim['material']]
        if prim['material'] in done:
            continue
        done.add(prim['material'])
        buf = io.BytesIO(); Image.open(HERE / 'work' / f'tex_p{pi}_d{n}{tier}.png').save(buf, 'PNG'); data = buf.getvalue()
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'p{pi}_{variant}'})
        doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(HERE / 'work' / f'viewer_{PREFIX}_d{n}{tier.lower()}.glb', d2, b2)
    print('viewer', PREFIX, variant)
