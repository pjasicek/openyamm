#!/usr/bin/env python3
"""Review-viewer GLBs: three.js has no region ramps, so each tier's ramps are baked into its body and head base colours with the engine rule, in copies of the delivered GLB; the torso keeps its tier material.
PeasantF3 copy (ramps pf3_ramps.json, tone pf_body_tone.png of ../mm9_peasantf3_claude/textures, read in place); after ../mm9_thrall_claude/scripts/viewer_tiers.py (its ramps, limbs image and mask read in place) with the GLB and
an output prefix as arguments. Usage: viewer_tiers.py <glb> <prefix> -> work/viewer_<prefix>_th_{a,b}.glb"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
NB = HERE.parent / 'mm9_peasantf3_claude'
R = json.load(open(NB / 'textures' / 'pf3_ramps.json'))
SRC = {'PeasantF3': 'pf_body_tone.png'}
GLB = Path(sys.argv[1]); PREFIX = sys.argv[2]
OUT = HERE / 'work'
baked = {}
for e in R['materials']:
    base = np.asarray(Image.open(NB / 'textures' / SRC[e['base']]).convert('RGB'), np.float64) / 255
    mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255 for ch in Image.open(NB / 'textures' / e['mask']).convert('RGBA').split()], -1)
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
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(OUT / f"viewer_{PREFIX}_th_{variant.split('_')[1]}.glb", d2, b2)
    print('viewer', variant)
