#!/usr/bin/env python3
"""The creature's own LOD0 runtime export (mm8_m560_claude/export/mm8_m560_lod0.glb: rig, the five clips byte-identical
to the installed model, one Wyvern primitive, three maps) with the rebuilt geometry and the new maps: the Wyvern
primitive takes the skinned export's attributes and indices (joints remapped by name, bind matrices checked), and
the images wyvern_basecolor / wyvern_normal_1k / wyvern_orm_1k take the composed PNGs. Unreferenced data is
compacted. Usage: swap_rt.py <geometry.glb> <out.glb>"""
import copy, struct, sys
from pathlib import Path
H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

geom, out = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(H.parent / 'mm8_m560_claude/export/mm8_m560_lod0.glb'); binary = bytearray(binary)
exp, payload = read_glb(geom)
node = next(n for n in doc['nodes'] if n.get('name') == 'Wyvern')
enode = next(n for n in exp['nodes'] if n.get('name') == 'Wyvern')
joints = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
bind = list(struct.iter_unpack('<16f', accessor_bytes(doc, binary, doc['skins'][node['skin']]['inverseBindMatrices'])))
eskin = exp['skins'][enode['skin']]
remap = [joints.index(exp['nodes'][i]['name']) for i in eskin['joints']]
ebind = list(struct.iter_unpack('<16f', accessor_bytes(exp, payload, eskin['inverseBindMatrices'])))
assert all(abs(a - b) < 1e-4 for i, m in zip(remap, ebind) for a, b in zip(bind[i], m)), 'bind space changed'
prim = doc['meshes'][node['mesh']]['primitives']; eprim = exp['meshes'][enode['mesh']]['primitives']
assert len(prim) == 1 and len(eprim) == 1
attrs = {}
for sem, idx in eprim[0]['attributes'].items():
    acc = exp['accessors'][idx]; packed = accessor_bytes(exp, payload, idx)
    if sem.startswith('JOINTS_'):
        code = {5121: 'B', 5123: 'H'}[acc['componentType']]
        packed = struct.pack('<' + code * (len(packed) // struct.calcsize(code)),
                             *(remap[v[0]] for v in struct.iter_unpack('<' + code, packed)))
    attrs[sem] = append_accessor(doc, binary, acc, packed)
prim[0]['attributes'] = attrs
prim[0]['indices'] = append_accessor(doc, binary, exp['accessors'][eprim[0]['indices']], accessor_bytes(exp, payload, eprim[0]['indices']))
maps = {'wyvern_basecolor': 'wyvern_basecolor.png', 'wyvern_normal_1k': 'wyvern_normal_1k.png', 'wyvern_orm_1k': 'wyvern_orm_1k.png'}
for im in doc['images']:
    data = (H / 'textures' / maps.pop(im['name'])).read_bytes()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    im['bufferView'] = len(doc['bufferViews']) - 1; im['mimeType'] = 'image/png'
assert not maps, maps
# compact: keep only referenced accessors and buffer views
used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()) | {p['indices']}
for s in doc['skins']:
    used.add(s['inverseBindMatrices'])
for a in doc.get('animations', []):
    for s in a['samplers']:
        used |= {s['input'], s['output']}
amap = {old: new for new, old in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc['images']})
vmap, newbin, nviews = {}, bytearray(), []
for new, old in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin)
    newbin.extend(binary[start:start + v['byteLength']]); nviews.append(v); vmap[old] = new
doc['accessors'] = [dict(doc['accessors'][old], bufferView=vmap[doc['accessors'][old]['bufferView']]) for old in sorted(used)]
doc['bufferViews'] = nviews
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
write_glb(out, doc, bytes(newbin))
print('SWAPPED', doc['accessors'][prim[0]['indices']]['count'] // 3, 'triangles', f'{len(newbin) / 1e6:.1f} MB')
