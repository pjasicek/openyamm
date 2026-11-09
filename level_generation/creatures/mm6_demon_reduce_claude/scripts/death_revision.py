#!/usr/bin/env python3
"""Burn-death revision of the reduced demon (user 2026-10-13: hold the last death frame, then burn in the variant's
colour; the ash mound goes). Drops the Demon_Body_Visibility scale channels (the old disintegration scaled the body
to zero 0.375 s into Death), removes the ash node, its mesh, its five materials, its scale channel in every clip and
the Ash_Remains clip; adds `Dead`, every Death channel held at its last key for 1 s; compacts the buffer.
Usage: death_revision.py <in.glb> <out.glb>"""
import copy
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

source, destination = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(source); binary = bytearray(binary)

visibility = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'Demon_Body_Visibility')
assert 'scale' not in doc['nodes'][visibility]
for a in doc['animations']:
    a['channels'] = [c for c in a['channels'] if c['target']['node'] != visibility]

# Dead: the last key of every Death channel, held
death = next(a for a in doc['animations'] if a['name'] == 'Death')
times = append_accessor(doc, binary, {'componentType': 5126, 'type': 'SCALAR', 'count': 2, 'min': [0.0], 'max': [1.0]},
                        struct.pack('<2f', 0.0, 1.0))
dead = {'name': 'Dead', 'channels': [], 'samplers': []}
for channel in death['channels']:
    sampler = death['samplers'][channel['sampler']]
    output = doc['accessors'][sampler['output']]
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[output['type']]
    assert output['componentType'] == 5126 and sampler.get('interpolation', 'LINEAR') != 'CUBICSPLINE'
    values = struct.unpack(f'<{output["count"] * width}f', accessor_bytes(doc, binary, sampler['output']))
    last = values[-width:]
    held = {k: v for k, v in output.items() if k not in ('bufferView', 'byteOffset', 'min', 'max')}
    held.update(count=2, min=list(last), max=list(last))
    dead['samplers'].append({'input': times, 'interpolation': 'STEP',
                             'output': append_accessor(doc, binary, held, struct.pack(f'<{2 * width}f', *last, *last))})
    dead['channels'].append({'sampler': len(dead['samplers']) - 1, 'target': copy.deepcopy(channel['target'])})
doc['animations'] = [a for a in doc['animations'] if a['name'] != 'Ash_Remains'] + [dead]

# the ash node, mesh and materials
ash = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'Demon_Ash_Remains')
ash_mesh = doc['nodes'][ash]['mesh']
assert not any(ash in n.get('children', []) for n in doc['nodes']) and ash not in doc['skins'][0]['joints']
nmap = lambda i: i - (i > ash)
del doc['nodes'][ash]
for n in doc['nodes']:
    if 'children' in n:
        n['children'] = [nmap(c) for c in n['children']]
    if 'mesh' in n and n['mesh'] > ash_mesh:
        n['mesh'] -= 1
for s in doc['scenes']:
    s['nodes'] = [nmap(i) for i in s['nodes'] if i != ash]
for s in doc['skins']:
    s['joints'] = [nmap(j) for j in s['joints']]
    if 'skeleton' in s:
        s['skeleton'] = nmap(s['skeleton'])
for a in doc['animations']:
    a['channels'] = [c for c in a['channels'] if c['target']['node'] != ash]
    used = sorted({c['sampler'] for c in a['channels']})
    smap = {old: new for new, old in enumerate(used)}
    a['samplers'] = [a['samplers'][i] for i in used]
    for c in a['channels']:
        c['sampler'] = smap[c['sampler']]; c['target']['node'] = nmap(c['target']['node'])
ash_materials = {p['material'] for p in doc['meshes'][ash_mesh]['primitives']}
del doc['meshes'][ash_mesh]
assert not any(p['material'] in ash_materials for m in doc['meshes'] for p in m['primitives'])
keep = [i for i in range(len(doc['materials'])) if i not in ash_materials]
mmap = {old: new for new, old in enumerate(keep)}
doc['materials'] = [doc['materials'][i] for i in keep]
for m in doc['meshes']:
    for p in m['primitives']:
        p['material'] = mmap[p['material']]
        for x in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
            x['material'] = mmap[x['material']]
for m in doc['meshes']:
    lods = m.get('extras', {})
    for key in ('openyamm_lods', 'openyamm_shadow_lods'):
        if key in lods:
            lods[key] = [i - (i > ash_mesh) for i in lods[key]]

# compact: only referenced accessors and buffer views
used_acc = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used_acc |= set(p['attributes'].values()) | {p['indices']}
for s in doc['skins']:
    used_acc.add(s['inverseBindMatrices'])
for a in doc['animations']:
    for s in a['samplers']:
        used_acc |= {s['input'], s['output']}
amap = {old: new for new, old in enumerate(sorted(used_acc))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used_acc}
               | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, packed, new_views = {}, bytearray(), []
for new, old in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed)
    packed.extend(binary[start:start + v['byteLength']]); new_views.append(v); vmap[old] = new
doc['accessors'] = [dict(doc['accessors'][i], bufferView=vmap[doc['accessors'][i]['bufferView']]) for i in sorted(used_acc)]
doc['bufferViews'] = new_views
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
for s in doc['skins']:
    s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc['animations']:
    for s in a['samplers']:
        s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
write_glb(destination, doc, bytes(packed))
print('DEATH REVISION', [a['name'] for a in doc['animations']], 'materials', [m['name'] for m in doc['materials']],
      f'{len(packed) / 1e6:.1f} MB')
