#!/usr/bin/env python3
"""Make the reworked one-handed attack (front_onehand.py output) the Minotaur's only attack in a GLB: a new `Attack`
animation with the AttackOneHand channel layout and the reworked outputs, and `Cast` (the native self-buff alias)
sharing its samplers' accessors. The two-handed Attack/Cast and the `AttackOneHand` name are removed; every other
clip, mesh, skin, material and image is kept; unreferenced buffer data is compacted.
A constant channel that did not change keeps its original accessors; every other channel gets the new 60 Hz key times
and a new output accessor. Usage: ship_onehand.py <in.glb> <onehand.npz> <out.glb>"""
import copy
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, npz, dst = Path(sys.argv[1]), np.load(sys.argv[2]), Path(sys.argv[3])
doc, binary = read_glb(src); binary = bytearray(binary)
names = [n.get('name') for n in doc['nodes']]
one = next(a for a in doc['animations'] if a['name'] == 'AttackOneHand')
times = npz['times'].astype(np.float32)
tpl = next(dict(doc['accessors'][s['input']]) for s in one['samplers'] if doc['accessors'][s['input']]['count'] > 2)
tpl.update(count=len(times), min=[float(times[0])], max=[float(times[-1])])
time_acc = append_accessor(doc, binary, tpl, times.tobytes())
new = {'name': 'Attack', 'channels': [], 'samplers': []}
changed = 0
for ch in one['channels']:
    s = one['samplers'][ch['sampler']]; key = f"{names[ch['target']['node']]}|{ch['target']['path']}"
    vals = npz[key].astype(np.float32)
    old_t = np.frombuffer(accessor_bytes(doc, binary, s['input']), np.float32)
    old_v = np.frombuffer(accessor_bytes(doc, binary, s['output']), np.float32).reshape(len(old_t), -1)
    same = np.allclose(vals, old_v[0], atol=1e-6) and np.allclose(old_v, old_v[0], atol=1e-7)   # constant, unchanged
    if same:
        ns = dict(s)
    else:
        acc = dict(doc['accessors'][s['output']], count=len(times)); acc.pop('min', None); acc.pop('max', None)
        ns = {'input': time_acc, 'output': append_accessor(doc, binary, acc, vals.tobytes()),
              'interpolation': s.get('interpolation', 'LINEAR')}
        changed += 1
    new['samplers'].append(ns); new['channels'].append({'sampler': len(new['samplers']) - 1, 'target': dict(ch['target'])})
cast = {'name': 'Cast', 'channels': copy.deepcopy(new['channels']), 'samplers': copy.deepcopy(new['samplers'])}
rest = [a for a in doc['animations'] if a['name'] not in ('Attack', 'Cast', 'AttackOneHand')]
doc['animations'] = [new, cast] + rest
# compact: keep only referenced accessors and buffer views
used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()) | ({p['indices']} if 'indices' in p else set())
for sk in doc.get('skins', []):
    used.add(sk['inverseBindMatrices'])
for a in doc['animations']:
    for s in a['samplers']:
        used |= {s['input'], s['output']}
amap = {old: k for k, old in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} |
               {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, nb, nv = {}, bytearray(), []
for k, old in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    nb.extend(b'\0' * (-len(nb) % 4)); v['byteOffset'] = len(nb); nb.extend(binary[start:start + v['byteLength']])
    nv.append(v); vmap[old] = k
doc['accessors'] = [dict(doc['accessors'][old], bufferView=vmap[doc['accessors'][old]['bufferView']]) for old in sorted(used)]
doc['bufferViews'] = nv
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
        if 'indices' in p:
            p['indices'] = amap[p['indices']]
for sk in doc.get('skins', []):
    sk['inverseBindMatrices'] = amap[sk['inverseBindMatrices']]
for a in doc['animations']:
    for s in a['samplers']:
        s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
write_glb(dst, doc, bytes(nb))
print('SHIPPED', dst.name, 'clips', [a['name'] for a in doc['animations']], 'changed channels', changed,
      f'{len(nb) / 1e6:.2f} MB')
