#!/usr/bin/env python3
"""Engine source for the retextured goblin from the installed GLB: the body primitive takes the new geometry, a head
primitive is added (GoblinHead_A/B/C copied from Goblin_A/B/C with the head maps, same tier ramps), both with the
gob2_a/b/c variant mappings; the Goblin_* materials take the new body maps and ramps (textures/gob2_ramps.json).
Rig, clips, sockets and the Sword joint stay byte-for-byte; old LOD/shadow meshes, images and textures are dropped
and the buffer compacted. The runtime chain then rebuilds LODs and merges the head into the body atlas
(build_gob_runtime.sh). Usage: assemble_gob.py <installed.glb> <master_export.glb> <out.glb>"""
import copy
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

HERE = Path(__file__).resolve().parents[1]; T = HERE / 'textures'
src, exp_path, out = (Path(a) for a in sys.argv[1:4])
doc, binary = read_glb(src); binary = bytearray(binary)
exp, payload = read_glb(exp_path)
NODE = 'Goblin'
node = next(n for n in doc['nodes'] if n.get('name') == NODE)
enode = next(n for n in exp['nodes'] if n.get('name') == NODE)
for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
    assert all(abs(a - b) < 1e-4 for a, b in zip(node.get(key, default), enode.get(key, default))), key
joints = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
bind = list(struct.iter_unpack('<16f', accessor_bytes(doc, binary, doc['skins'][node['skin']]['inverseBindMatrices'])))
eskin = exp['skins'][enode['skin']]
remap = [joints.index(exp['nodes'][i]['name']) for i in eskin['joints']]
ebind = list(struct.iter_unpack('<16f', accessor_bytes(exp, payload, eskin['inverseBindMatrices'])))
assert all(abs(a - b) < 1e-4 for i, m in zip(remap, ebind) for a, b in zip(bind[i], m)), 'bind space changed'


def geometry(e):
    attrs = {}
    for sem, idx in e['attributes'].items():
        acc = exp['accessors'][idx]; packed = accessor_bytes(exp, payload, idx)
        if sem.startswith('JOINTS_'):
            code = {5121: 'B', 5123: 'H'}[acc['componentType']]
            packed = struct.pack('<' + code * (len(packed) // struct.calcsize(code)),
                                 *(remap[v[0]] for v in struct.iter_unpack('<' + code, packed)))
        attrs[sem] = append_accessor(doc, binary, acc, packed)
    return attrs, append_accessor(doc, binary, exp['accessors'][e['indices']], accessor_bytes(exp, payload, e['indices']))


def image(path):
    data = Path(path).read_bytes()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0})
    return len(doc['textures']) - 1


cfg = json.loads((T / 'gob2_ramps.json').read_text())
ramps = {m['prefix']: m['ramps'] for m in cfg['materials']}
maps = {prefix: {'base': image(T / f'{stem}basecolor_1k.png'), 'mr': image(T / f'{stem}metal_rough_1k.png'),
                 'normal': image(T / f'{stem}normal_1k.png'), 'mask': image(T / f'{stem}region_mask.png')}
        for prefix, stem in (('Goblin', 'gob2_'), ('GoblinHead', 'gob2_head_'))}


def retexture(material, prefix, variant):
    material['pbrMetallicRoughness']['baseColorTexture'] = {'index': maps[prefix]['base']}
    material['pbrMetallicRoughness']['metallicRoughnessTexture'] = {'index': maps[prefix]['mr']}
    material['normalTexture'] = dict(material.get('normalTexture', {}), index=maps[prefix]['normal'])
    material['extras']['openyamm_region_mask'] = {'index': maps[prefix]['mask']}
    material['extras']['openyamm_region_ramps'] = ramps[prefix][variant]


mesh = doc['meshes'][node['mesh']]
assert len(mesh['primitives']) == 1
body = mesh['primitives'][0]
eprims = {exp['materials'][p['material']]['name']: p for p in exp['meshes'][enode['mesh']]['primitives']}
body['attributes'], body['indices'] = geometry(eprims['Goblin_A'])
head = {'attributes': {}, 'indices': 0, 'material': 0,
        'extensions': {'KHR_materials_variants': {'mappings': []}}}
head['attributes'], head['indices'] = geometry(eprims['GoblinHead_A'])
for mapping in body['extensions']['KHR_materials_variants']['mappings']:
    bm = doc['materials'][mapping['material']]
    variant = cfg['variants'][mapping['variants'][0]]
    retexture(bm, 'Goblin', variant)
    hm = copy.deepcopy(bm); hm['name'] = bm['name'].replace('Goblin_', 'GoblinHead_')
    retexture(hm, 'GoblinHead', variant)
    doc['materials'].append(hm)
    head['extensions']['KHR_materials_variants']['mappings'].append(
        {'material': len(doc['materials']) - 1, 'variants': mapping['variants']})
    if mapping['material'] == body['material']:
        head['material'] = len(doc['materials']) - 1
mesh['primitives'].append(head)
mesh.pop('extras', None)
keep = sorted({n['mesh'] for n in doc['nodes'] if 'mesh' in n})
mmap = {old: new for new, old in enumerate(keep)}
doc['meshes'] = [doc['meshes'][i] for i in keep]
for n in doc['nodes']:
    if 'mesh' in n:
        n['mesh'] = mmap[n['mesh']]

# drop unused textures/images, then unreferenced accessors/buffer views
SLOTS = [('pbrMetallicRoughness', 'baseColorTexture'), ('pbrMetallicRoughness', 'metallicRoughnessTexture'),
         ('normalTexture',), ('occlusionTexture',), ('emissiveTexture',), ('extras', 'openyamm_region_mask'),
         ('extras', 'openyamm_burn_map')]


def slots(material):
    for path in SLOTS:
        ref = material
        for key in path:
            ref = ref.get(key) if isinstance(ref, dict) else None
        if isinstance(ref, dict) and 'index' in ref:
            yield ref


used_tex = sorted({ref['index'] for m in doc['materials'] for ref in slots(m)})
tmap = {old: new for new, old in enumerate(used_tex)}
for m in doc['materials']:
    for ref in slots(m):
        ref['index'] = tmap[ref['index']]
doc['textures'] = [doc['textures'][i] for i in used_tex]
used_img = sorted({t['source'] for t in doc['textures']})
imap = {old: new for new, old in enumerate(used_img)}
doc['images'] = [doc['images'][i] for i in used_img]
for t in doc['textures']:
    t['source'] = imap[t['source']]
used_acc = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used_acc |= set(p['attributes'].values()) | {p['indices']}
for s in doc['skins']:
    used_acc.add(s['inverseBindMatrices'])
for a in doc.get('animations', []):
    for s in a['samplers']:
        used_acc |= {s['input'], s['output']}
amap = {old: new for new, old in enumerate(sorted(used_acc))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used_acc} | {im['bufferView'] for im in doc['images']})
vmap, packed, new_views = {}, bytearray(), []
for new, old in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed)
    packed.extend(binary[start:start + v['byteLength']]); new_views.append(v); vmap[old] = new
doc['accessors'] = [dict(doc['accessors'][i], bufferView=vmap[doc['accessors'][i]['bufferView']]) for i in sorted(used_acc)]
doc['bufferViews'] = new_views
for im in doc['images']:
    im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
for s in doc['skins']:
    s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc.get('animations', []):
    for s in a['samplers']:
        s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
write_glb(out, doc, bytes(packed))
tris = {doc['materials'][p['material']]['name']: doc['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives']}
print('ASSEMBLED', tris, 'materials', [m['name'] for m in doc['materials']], len(doc['images']), 'images',
      f'{len(packed) / 1e6:.1f} MB')
