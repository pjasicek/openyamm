#!/usr/bin/env python3
"""Review-viewer GLBs for every PeasantDF design and tier (after viewer_tiers.py): three.js has no region ramps, so each
tier's body AND head ramps are baked into copies of that material's base colour with the engine rule, in copies of the
delivered GLB (export/mm9_peasantdf<N>.glb). Writes review/viewer/<variant>.glb (pdf1_a, pdf1_b, pdf2_b, pdf3_a, ...).
Args: d1 [d2 ...]"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
OUT = HERE / 'review' / 'viewer'
OUT.mkdir(parents=True, exist_ok=True)
for d in sys.argv[1:]:
    k = d[1:]
    R = json.load(open(HERE / 'textures' / f'{d}_ramps.json'))
    GLB = HERE / 'export' / f'mm9_peasantdf{k}.glb'
    src = {'PeasantDF': HERE / 'textures' / f'pdf{k}_tp_basecolor_graded.png',
           'PeasantDFHead': HERE / 'textures' / f'pdf{k}_tp_head_basecolor.png'}
    for idx, variant in enumerate(R['variants']):
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
        for e in R['materials']:
            base = np.asarray(Image.open(src[e['base']]).convert('RGB'), np.float64) / 255
            mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                             for ch in Image.open(HERE / 'textures' / e['mask']).convert('RGBA').split()], -1)
            img = Image.fromarray((np.clip(TT.apply(base, mask, e['ramps'][variant]), 0, 1) * 255).astype(np.uint8))
            buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
            mat = doc['materials'][names[f"{e['prefix']}_{variant.split('_')[1].upper()}"]]
            binary.extend(b'\0' * (-len(binary) % 4))
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
            binary.extend(data)
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{e["prefix"]}_{variant}'})
            doc['textures'].append({'source': len(doc['images']) - 1,
                                    'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
            mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        for m_ in doc['materials']:
            m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
        doc.get('extensions', {}).pop('KHR_materials_variants', None)
        doc['extensionsUsed'] = [x for x in doc.get('extensionsUsed', []) if x != 'KHR_materials_variants'] + ['KHR_materials_specular']
        d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(OUT / f'{variant}.glb', d2, b2)
        print('viewer', variant)
