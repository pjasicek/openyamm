#!/usr/bin/env python3
"""(giant reduction: textures from ../mm9_giant_claude/textures; Usage: viewer_tiers.py <glb> <suffix>, writes review/viewer/<variant>_<suffix>.glb)
Review-viewer GLBs: three.js has no region ramps, so each tier's ramps are baked into its body and head base colours with the engine rule, in copies of the delivered GLB; the torso keeps its tier material.
Writes review/viewer/thrall_a.glb, _b, _c."""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
R = json.load(open(HERE.parent / 'mm9_giant_claude' / 'textures' / 'gi_ramps.json'))
SRC = {'Giant': 'gi_body_final.png', 'GiantHead': 'gi_head_a_final.png', 'GiantMallet': 'gi_mallet_base.png'}
GLB = Path(sys.argv[1]); SUFFIX = sys.argv[2]
OUT = HERE / 'review' / 'viewer'
OUT.mkdir(parents=True, exist_ok=True)
baked = {}
# pass 2: base and mask images come from the GLB itself (the rebuilt mallet has its own baked maps)
_doc, _bin = RV.read_glb(GLB)
def glb_image(name):
    im = next(i for i in _doc['images'] if i.get('name') == name.replace('.png', '')); bv = _doc['bufferViews'][im['bufferView']]
    o = bv.get('byteOffset', 0); return Image.open(io.BytesIO(bytes(_bin[o:o + bv['byteLength']])))
for e in R['materials']:
    base = np.asarray(glb_image(SRC[e['base']]).convert('RGB'), np.float64) / 255
    mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255 for ch in glb_image(e['mask']).convert('RGBA').split()], -1)
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
        if prefix == 'GiantHead': continue          # per-tier images already in the GLB (tier_head.py)
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
    RV.write_glb(OUT / f'{variant}_{SUFFIX}.glb', doc, bytes(binary))
    print('viewer', variant)
