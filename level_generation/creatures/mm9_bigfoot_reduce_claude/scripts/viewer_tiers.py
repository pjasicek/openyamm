#!/usr/bin/env python3
"""Review-viewer GLBs for the Bigfoot reduction (after ../mm9_bigfoot_claude/scripts/viewer_tiers.py): three.js has no region
ramps, so each tier's ramps are baked into its base colours with the engine rule (claude_shared/tier_textures.apply). Unlike the
creature's script, everything is read from the GLB itself: each material's base colour image, its region mask and its
openyamm_region_ramps extras; a material without ramps (BigfootHead_C, the Yeti's own head image) keeps its image.
Usage: viewer_tiers.py <glb> <prefix> -> work/viewer_<prefix>_bf_{a,b,c}.glb"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT  # noqa: E402
import region_variants as RV  # noqa: E402
GLB, PREFIX = Path(sys.argv[1]), sys.argv[2]
OUT = HERE / 'work'
doc0, bin0 = RV.read_glb(GLB)


def image(doc, binary, tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


baked = {}
for m in doc0['materials']:
    ex = m.get('extras', {})
    if 'openyamm_region_ramps' not in ex:
        continue
    base = np.asarray(image(doc0, bin0, m['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB'), np.float64) / 255
    size = (base.shape[1], base.shape[0])
    bands = image(doc0, bin0, ex['openyamm_region_mask']['index']).convert('RGBA').split()
    mask = np.stack([np.asarray(b if b.size == size else b.resize(size, Image.BILINEAR), np.float64) / 255 for b in bands], -1)
    img = Image.fromarray((np.clip(TT.apply(base, mask, ex['openyamm_region_ramps']), 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, 'PNG'); baked[m['name']] = buf.getvalue(); print('baked', m['name'])
vnames = [v['name'] for v in doc0['extensions']['KHR_materials_variants']['variants']]
for idx, variant in enumerate(vnames):
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    for mat in doc['materials']:
        data = baked.get(mat['name'])
        if data is not None:
            binary.extend(b'\0' * (-len(binary) % 4))
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
            binary.extend(data)
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f"{mat['name']}_baked"})
            doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
            mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        mat.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    RV.write_glb(OUT / f'viewer_{PREFIX}_{variant}.glb', doc, bytes(binary))
    print('viewer', variant)
