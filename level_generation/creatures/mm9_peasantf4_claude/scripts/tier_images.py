#!/usr/bin/env python3
"""Tier images that ramps cannot give: every tier's head colour (faces differ), and the lower set where textures/tier_images.json names one. Materials PeasantF1Head (no ramps) and region_variants' SorcererLow_<tier>.
Normal and ORM shared unless named. Args: <in glb> <out glb>"""
import copy, io, json, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src); blob = bytearray(blob)
cfg = json.load(open('textures/tier_images.json'))
def add_image(path, mode='RGB'):
    im = Image.open(path).convert(mode); buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    return len(doc['images']) - 1
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
names = [m['name'] for m in doc['materials']]; print('materials', names, 'variants', variants)
hi = names.index('PeasantF4Head'); hm = doc['materials'][hi]
hm.setdefault('extras', {})['openyamm_specular'] = 0.0; hm['pbrMetallicRoughness']['metallicFactor'] = 0.0
smp = doc['textures'][hm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
mats = {}
for v in variants:
    png = cfg['head'].get(v)
    if png is None: mats[v] = hi; continue
    m = copy.deepcopy(hm); m['name'] = 'PeasantF4Head_' + v
    doc['textures'].append({'source': add_image(png), 'sampler': smp})
    m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    doc['materials'].append(m); mats[v] = len(doc['materials']) - 1
n = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if prim.get('material') == hi:
            prim.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(variants)]}; n += 1
print('head prims', n)
for v, spec in cfg.get('low', {}).items():
    mn = names.index('SorcererLow_' + v.split('_')[1].upper())
    m = doc['materials'][mn]
    doc['textures'].append({'source': add_image(spec['base']), 'sampler': smp}); m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    if spec.get('normal'):
        doc['textures'].append({'source': add_image(spec['normal']), 'sampler': smp}); m['normalTexture'] = {'index': len(doc['textures']) - 1}
    # own image: no ramps on this tier's lower set
    if spec.get('no_ramps'):
        m.get('extras', {}).pop('openyamm_region_mask', None); m.get('extras', {}).pop('openyamm_region_ramps', None)
RV.write_glb(dst, doc, bytes(blob))
print('tier images', dst)
