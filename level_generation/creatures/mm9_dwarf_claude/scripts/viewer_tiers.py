#!/usr/bin/env python3
"""Review-viewer GLBs: three.js has no region ramps, so each tier's ramps are baked into its body and head base colours with the engine rule, in copies of the delivered GLB; the torso keeps its tier material.
Writes review/viewer/dwarf_a.glb, _b, _c."""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
R = json.load(open(HERE / 'textures' / 'dwarf_ramps.json'))
SRC = {'DwarfTorso': 'dwarf_torso_a_final.png', 'DwarfLimbs': 'dwarf_limbs_a_final.png', 'DwarfHead': 'dwarf_head_a_final.png'}
GLB = HERE / 'export' / (sys.argv[1] if len(sys.argv) > 1 else 'mm9_dwarf.glb')
OUT = HERE / 'review' / 'viewer'
OUT.mkdir(parents=True, exist_ok=True)
baked = {}
for e in R['materials']:
    base = np.asarray(Image.open(HERE / 'textures' / SRC[e['base']]).convert('RGB'), np.float64) / 255
    mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255 for ch in Image.open(HERE / 'textures' / e['mask']).convert('RGBA').split()], -1)
    for v in R['variants']:
        img = Image.fromarray((np.clip(TT.apply(base, mask, e['ramps'][v]), 0, 1) * 255).astype(np.uint8))
        buf = io.BytesIO(); img.save(buf, 'PNG'); baked[(v, e['prefix'])] = buf.getvalue()
for variant in R['variants']:
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    idx = R['variants'].index(variant)
    sfx = variant.split('_')[1].upper()
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            ms = prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
            for mp in ms:
                if idx in mp['variants']: prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'): prim.pop('extensions', None)
    for (v, prefix), data in baked.items():
        if v != variant: continue
        mat = doc['materials'][names[f'{prefix}_{sfx}']]
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary.extend(data)
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{prefix}_{variant}'})
        doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        mat.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.3 if m_['name'].startswith('DwarfWeapon') else 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    RV.write_glb(OUT / f'{variant}.glb', doc, bytes(binary))
    print('viewer', variant)
