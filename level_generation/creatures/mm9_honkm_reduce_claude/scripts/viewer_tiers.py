#!/usr/bin/env python3
"""Review-viewer GLBs (after ../mm9_honkmale_claude/v2/scripts/viewer_tiers.py): three.js has no region ramps, so each tier is
a copy of the given GLB with its ramps baked into the body base colour (claude_shared/tier_textures.py, the engine rule) and its
own head material. Base colour and mask are the installed GLB's own images (work/tex_HonkM_A_{0,1}.png), ramps the creature's
textures/honkm_ramps.json. Usage: viewer_tiers.py <glb> <prefix> -> review/viewer/<prefix>_{a,b}.glb"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
GLB = Path(sys.argv[1]); PREFIX = sys.argv[2]; Mesh = 'HonkM'
R = json.load(open(HERE.parent / 'mm9_honkmale_claude' / 'textures' / 'honkm_ramps.json'))
entry = R['materials'][0]
base = np.asarray(Image.open(HERE / 'work' / 'tex_HonkM_A_0.png').convert('RGB'), np.float64) / 255
mask = np.stack([np.asarray(c.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                 for c in Image.open(HERE / 'work' / 'tex_HonkM_A_1.png').convert('RGBA').split()], -1)
OUT = HERE / 'review' / 'viewer'; OUT.mkdir(parents=True, exist_ok=True)
for variant in R['variants']:
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    vi = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']].index(variant)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            ext = prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if ext:
                prim['material'] = next(m['material'] for m in ext['mappings'] if vi in m['variants'])
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    img = Image.fromarray((np.clip(TT.apply(base, mask, entry['ramps'][variant]), 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{Mesh}_{variant}'})
    for m in doc['materials']:
        if m['name'].startswith(Mesh) and 'Head' not in m['name'] and variant.split('_')[-1].upper() == m['name'].rsplit('_', 1)[-1].upper():
            t = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]
            doc['textures'].append({**t, 'source': len(doc['images']) - 1})
            m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
            m.get('extras', {}).pop('openyamm_region_mask', None); m.get('extras', {}).pop('openyamm_region_ramps', None)
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    if 'extensionsUsed' in doc:
        doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
        if not doc['extensionsUsed']:
            doc.pop('extensionsUsed')
    RV.write_glb(OUT / f"{PREFIX}_{variant.split('_')[1]}.glb", doc, bytes(binary))
    print('viewer', PREFIX, variant)
