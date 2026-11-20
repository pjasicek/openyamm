#!/usr/bin/env python3
"""Review-viewer GLBs (three.js has no region ramps): per tier a copy of the given GLB with each primitive switched to that
tier's material (KHR_materials_variants) and the material's region ramps baked into its base colour by the engine rule
(claude_shared/tier_textures.apply), the tone image, mask and ramps all read from the GLB itself (PeasantM1d: body and head sets
both carry ramps). Usage: viewer_tiers.py <glb> <prefix> -> work/viewer_<prefix>_th_{c,d}.glb"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
GLB = Path(sys.argv[1]); PREFIX = sys.argv[2]
doc0, bin0 = RV.read_glb(GLB)
variants = [v['name'] for v in doc0['extensions']['KHR_materials_variants']['variants']]


def image(doc, binary, i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


for idx, variant in enumerate(variants):
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    used = set()
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
            used.add(prim['material'])
    for mi in sorted(used):
        mat = doc['materials'][mi]; ex = mat.get('extras', {})
        if 'openyamm_region_ramps' not in ex:
            continue
        tex = doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
        base = np.asarray(image(doc, binary, tex['source']).convert('RGB'), np.float64) / 255
        mimg = image(doc, binary, doc['textures'][ex['openyamm_region_mask']['index']]['source']).convert('RGBA')
        mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
        img = Image.fromarray((np.clip(TT.apply(base, mask, ex['openyamm_region_ramps']), 0, 1) * 255 + 0.5).astype(np.uint8))
        buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f"{mat['name']}_{variant}"})
        doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': tex.get('sampler', 0)})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(HERE / 'work' / f"viewer_{PREFIX}_th_{variant.split('_')[1]}.glb", d2, b2)
    print('viewer', variant, sorted(used))
