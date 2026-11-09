#!/usr/bin/env python3
"""Replace named clips of a creature GLB with the same-named clips of a donor GLB exported from the same rig (channels
remapped by node name). Meshes, LODs, skins, materials, images and every other clip keep their bytes; unreferenced
buffer data is compacted. Usage: transplant_anims.py <target.glb> <donor.glb> <out.glb> <Clip>[,<Clip>...]"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

target, donor, out = (Path(a) for a in sys.argv[1:4]); names = sys.argv[4].split(',')
doc, binary = read_glb(target); binary = bytearray(binary)
src, payload = read_glb(donor)
node_index = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
for name in names:
    new = next(a for a in src['animations'] if a['name'] == name)
    slot = next(i for i, a in enumerate(doc['animations']) if a['name'] == name)
    samplers = []
    for s in new['samplers']:
        samplers.append({'input': append_accessor(doc, binary, src['accessors'][s['input']], accessor_bytes(src, payload, s['input'])),
                         'output': append_accessor(doc, binary, src['accessors'][s['output']], accessor_bytes(src, payload, s['output'])),
                         'interpolation': s.get('interpolation', 'LINEAR')})
    channels = [{'sampler': c['sampler'], 'target': {'node': node_index[src['nodes'][c['target']['node']]['name']],
                                                     'path': c['target']['path']}} for c in new['channels']]
    old = doc['animations'][slot]
    assert {(doc['nodes'][c['target']['node']]['name'], c['target']['path']) for c in old['channels']} == \
        {(doc['nodes'][c['target']['node']]['name'], c['target']['path']) for c in channels}, f'{name}: channel set changed'
    doc['animations'][slot] = dict(old, samplers=samplers, channels=channels)

# compact: every accessor still referenced by any mesh (all LODs), skin or clip; every referenced buffer view
refs = []
for m in doc['meshes']:
    for p in m['primitives']:
        refs += [(p['attributes'], k) for k in p['attributes']] + ([(p, 'indices')] if 'indices' in p else [])
        for t in p.get('targets', []):
            refs += [(t, k) for k in t]
refs += [(s, 'inverseBindMatrices') for s in doc.get('skins', []) if 'inverseBindMatrices' in s]
for a in doc['animations']:
    for s in a['samplers']:
        refs += [(s, 'input'), (s, 'output')]
used = sorted({o[k] for o, k in refs}); amap = {old: new for new, old in enumerate(used)}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, newbin, newviews = {}, bytearray(), []
for new_i, old_i in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][old_i]); start = v.get('byteOffset', 0)
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin)
    newbin.extend(binary[start:start + v['byteLength']]); newviews.append(v); vmap[old_i] = new_i
doc['accessors'] = [dict(doc['accessors'][i], bufferView=vmap[doc['accessors'][i]['bufferView']]) for i in used]
doc['bufferViews'] = newviews
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for o, k in refs:
    o[k] = amap[o[k]]
write_glb(out, doc, bytes(newbin))
print('TRANSPLANTED', names, f'{len(newbin) / 1e6:.2f} MB')
