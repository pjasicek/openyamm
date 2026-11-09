#!/usr/bin/env python3
"""Add the skirt's swing-only thigh helper joints to a runtime GLB: nodes as children of B_Pelvis with the export's rest
transforms, skin joints with the export's inverse binds, and their rotation/translation channels in every animation
(matched by name). Usage: add_helpers.py <runtime.glb> <helpers export.glb> <out.glb> [helper ...]"""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, exp_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
helpers = sys.argv[4:] or ['B_L_ThighSwing', 'B_R_ThighSwing']
doc, binary = read_glb(src); binary = bytearray(binary)
exp, ebin = read_glb(exp_path)
dnames = [n.get('name') for n in doc['nodes']]; enames = [n.get('name') for n in exp['nodes']]
pelvis = dnames.index('B_Pelvis')
eskin = exp['skins'][0]; eibm = list(struct.iter_unpack('<16f', accessor_bytes(exp, ebin, eskin['inverseBindMatrices'])))
ejoint = {enames[j]: k for k, j in enumerate(eskin['joints'])}
# the export's other joints must bind like the runtime's
for skin in doc['skins']:
    ibm = list(struct.iter_unpack('<16f', accessor_bytes(doc, binary, skin['inverseBindMatrices'])))
    for k, j in enumerate(skin['joints']):
        n = dnames[j]
        if n in ejoint and n.startswith('B_'):
            assert max(abs(a - b) for a, b in zip(ibm[k], eibm[ejoint[n]])) < 1e-3, n
new_index = {}
for h in helpers:
    e = exp['nodes'][enames.index(h)]
    node = {'name': h}
    for key in ('translation', 'rotation', 'scale'):
        if key in e:
            node[key] = e[key]
    doc['nodes'].append(node); new_index[h] = len(doc['nodes']) - 1
    doc['nodes'][pelvis].setdefault('children', []).append(new_index[h])
for skin in doc['skins']:
    ibm = list(struct.iter_unpack('<16f', accessor_bytes(doc, binary, skin['inverseBindMatrices'])))
    for h in helpers:
        skin['joints'].append(new_index[h]); ibm.append(eibm[ejoint[h]])
    acc = dict(doc['accessors'][skin['inverseBindMatrices']]); acc['count'] = len(ibm); acc.pop('bufferView', None)
    acc.pop('byteOffset', None)
    skin['inverseBindMatrices'] = append_accessor(doc, binary, acc, b''.join(struct.pack('<16f', *m) for m in ibm))
added = 0
for anim in doc['animations']:
    ea = next(x for x in exp['animations'] if x['name'] == anim['name'])
    for ch in ea['channels']:
        name = enames[ch['target']['node']]
        if name not in new_index or ch['target']['path'] not in ('rotation', 'translation'):
            continue
        s = ea['samplers'][ch['sampler']]
        anim['samplers'].append({'input': append_accessor(doc, binary, exp['accessors'][s['input']], accessor_bytes(exp, ebin, s['input'])),
                                 'output': append_accessor(doc, binary, exp['accessors'][s['output']], accessor_bytes(exp, ebin, s['output'])),
                                 'interpolation': s.get('interpolation', 'LINEAR')})
        anim['channels'].append({'sampler': len(anim['samplers']) - 1, 'target': {'node': new_index[name], 'path': ch['target']['path']}})
        added += 1
write_glb(out, doc, bytes(binary))
print('HELPERS', helpers, 'joints per skin', [len(s['joints']) for s in doc['skins']], 'channels added', added)
