#!/usr/bin/env python3
"""PeasantM2d tier variants on the runtime GLB (project folder): pm2d_d (row 26, PEASANTM2D, base head), pm2d_c (row 24, PEASANTM2C:
its own head colour from the Codex face projection, D's head normal/ORM). From PeasantM2's tiers_pm2.py.
Torso set: one shared image + region mask + ramps (textures/pm2d_ramps.json, tiers_fit_pm2.py) through claude_shared/region_variants.py.
Head set: per-tier images (the two skins are two different men: bearded / clean-shaven, white / ash-grey hair); shared ORM.
Limbs set (trousers, boots, hands): shared, no variant (the MM9 skins share them). Args: <in glb> <out glb>"""
import copy, io, sys, tempfile, os
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
fd, tmp = tempfile.mkstemp(suffix='.glb', dir='work'); os.close(fd)
RV.apply_variants(src, tmp, 'textures/pm2d_ramps.json')
doc, blob = RV.read_glb(tmp); blob = bytearray(blob); os.remove(tmp)
def add_image(path):
    data = io.BytesIO(); Image.open(path).convert('RGB').save(data, 'PNG'); data = data.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}); blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    return len(doc['images']) - 1
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
names = [m['name'] for m in doc['materials']]
hi = next(i for i, n in enumerate(names) if n == 'Pm2dHead' or n.startswith('Pm2dHead.'))
hm = doc['materials'][hi]
smp = doc['textures'][hm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
mb = copy.deepcopy(hm); mb['name'] = 'Pm2dHead_C'
doc['textures'].append({'source': add_image('textures/pm2d_head_c_final.png'), 'sampler': smp})
mb['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
# PeasantM2d: tier C shares tier D's head normal and ORM (same mesh; C's face differs in colour only)
doc['materials'].append(mb); bi = len(doc['materials']) - 1
mats = {'pm2d_d': hi, 'pm2d_c': bi}; n = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if prim.get('material') == hi:
            prim.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(variants)]}; n += 1
RV.write_glb(dst, doc, bytes(blob))
print('TIERS variants', variants, 'head prims', n, 'images', len(doc['images']), round(len(blob) / 1e6, 1), 'MB')
