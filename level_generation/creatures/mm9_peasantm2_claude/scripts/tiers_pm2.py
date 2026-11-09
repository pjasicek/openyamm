#!/usr/bin/env python3
"""Tier variants on the runtime GLB (project folder): pm2_a (row 50, PEASANTM2A), pm2_b (row 44, PEASANTM2B).
Torso set: one shared image + region mask + ramps (textures/pm2_ramps.json, tiers_fit_pm2.py) through claude_shared/region_variants.py.
Head set: per-tier images (the two skins are two different men: bearded / clean-shaven, white / ash-grey hair); shared ORM.
Limbs set (trousers, boots, hands): shared, no variant (the MM9 skins share them). Args: <in glb> <out glb>"""
import copy, io, sys, tempfile, os
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
fd, tmp = tempfile.mkstemp(suffix='.glb', dir='work'); os.close(fd)
RV.apply_variants(src, tmp, 'textures/pm2_ramps.json')
doc, blob = RV.read_glb(tmp); blob = bytearray(blob); os.remove(tmp)
def add_image(path):
    data = io.BytesIO(); Image.open(path).convert('RGB').save(data, 'PNG'); data = data.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}); blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    return len(doc['images']) - 1
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
names = [m['name'] for m in doc['materials']]
hi = next(i for i, n in enumerate(names) if n == 'Pm2Head' or n.startswith('Pm2Head.'))
hm = doc['materials'][hi]
smp = doc['textures'][hm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
mb = copy.deepcopy(hm); mb['name'] = 'Pm2Head_B'
doc['textures'].append({'source': add_image('textures/pm2_head_b_final.png'), 'sampler': smp})
mb['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
doc['textures'].append({'source': add_image('textures/pm2_head_b_normal.png'), 'sampler': smp})
mb['normalTexture'] = dict(hm.get('normalTexture', {}), index=len(doc['textures']) - 1)
doc['materials'].append(mb); bi = len(doc['materials']) - 1
mats = {'pm2_a': hi, 'pm2_b': bi}; n = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if prim.get('material') == hi:
            prim.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(variants)]}; n += 1
RV.write_glb(dst, doc, bytes(blob))
print('TIERS variants', variants, 'head prims', n, 'images', len(doc['images']), round(len(blob) / 1e6, 1), 'MB')
