#!/usr/bin/env python3
"""PeasantDM1 reduction copy of ../mm9_peasantdm1_claude/scripts/viewer_tiers.py (ramps and masks read in place from that
project; base colours from the GLB itself): args <glb> <prefix> -> work/viewer_<prefix>_th_{a,b}.glb. Original docstring:
Review-viewer GLBs (after mm9_peasantdm1_claude/scripts/viewer_tiers.py): three.js has no region ramps, so each tier's
ramps are baked into the base colour of every ramped material (body and head) with the engine rule, in copies of the
delivered GLB; the base colour is read from the GLB itself. Writes review/viewer/pdm1_a.glb, pdm1_b.glb. Args: [glb]"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
NB = HERE.parent / 'mm9_peasantdm1_claude'
R = json.load(open(NB / 'textures' / 'pdm1_ramps.json'))
GLB = Path(sys.argv[1]).resolve(); PREFIX = sys.argv[2]
OUT = HERE / 'work'
OUT.mkdir(parents=True, exist_ok=True)


def image_of(doc, binary, mat):
    tex = doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
    bv = doc['bufferViews'][doc['images'][tex['source']]['bufferView']]
    data = bytes(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
    return np.asarray(Image.open(io.BytesIO(data)).convert('RGB'), np.float64) / 255


for idx, variant in enumerate(R['variants']):
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    for e in R['materials']:
        mat = doc['materials'][names[f"{e['prefix']}_{variant.split('_')[1].upper()}"]]
        base = image_of(doc, binary, mat)
        mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                         for ch in Image.open(NB / 'textures' / e['mask']).convert('RGBA').split()], -1)
        img = Image.fromarray((np.clip(TT.apply(base, mask, e['ramps'][variant]), 0, 1) * 255).astype(np.uint8))
        buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary.extend(data)
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f"{e['prefix']}_{variant}"})
        doc['textures'].append({'source': len(doc['images']) - 1,
                                'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        mat.get('extras', {}).pop('openyamm_region_mask', None); mat.get('extras', {}).pop('openyamm_region_ramps', None)
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [x for x in doc.get('extensionsUsed', []) if x != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(OUT / f"viewer_{PREFIX}_th_{variant.split('_')[1]}.glb", d2, b2)
    print('viewer', variant)
