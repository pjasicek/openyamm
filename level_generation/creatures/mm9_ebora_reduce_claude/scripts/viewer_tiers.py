#!/usr/bin/env python3
"""(copy of mm9_ebora_claude/scripts/viewer_tiers.py: GLB and output prefix as arguments, Ebora's textures read from
her project) Review-viewer GLBs (three.js has no region ramps): per tier, the tier's material on every primitive and the ramps baked
into the base colour with the engine rule (claude_shared/tier_textures.py). Writes work/viewer_<tier>.glb. Project folder."""
import io, json, sys
import numpy as np
from PIL import Image
import os
EB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../mm9_ebora_claude')
sys.path.insert(0, os.path.join(EB, '../claude_shared'))
import tier_textures as TT
import region_variants as RV
cfg = json.load(open(os.path.join(EB, 'textures/eb_tiers.json'))); V = cfg['variants']
GLB, OUT = sys.argv[1], sys.argv[2]
for vi, variant in enumerate(V):
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if vi in mp['variants']: prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'): prim.pop('extensions', None)
    for m in doc['materials']:
        ex = m.get('extras', {})
        if 'openyamm_region_ramps' in ex:
            base_name = m['name'].rsplit('_', 1)[0]; e = cfg['materials'][base_name]
            base = np.asarray(Image.open(os.path.join(EB, 'textures', e['base'])).convert('RGB'), np.float64) / 255
            mask = np.stack([np.asarray(c.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                             for c in Image.open(os.path.join(EB, 'textures', e['mask'])).convert('RGBA').split()], -1)
            img = Image.fromarray((np.clip(TT.apply(base, mask, ex['openyamm_region_ramps']), 0, 1) * 255 + 0.5).astype(np.uint8))
            buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
            binary.extend(b'\0' * (-len(binary) % 4))
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
            binary.extend(data)
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': m['name'] + '_baked'})
            doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0})
            m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    doc, binary = RV._compact(doc, bytes(binary))
    RV.write_glb(f'{OUT}_{variant}.glb', doc, binary)
    print('viewer', variant)
