#!/usr/bin/env python3
"""Put the Cast v2 clip of work/cast_v2.glb (production rig, exported by cast_v2.py) into the Cast and Attack clips of
a runtime Water Elemental GLB, so both melee/ranged attacks and spells play the two-handed cast. Channels are matched
by joint name and path; the joints' rest TRS must agree, so the local values mean the same in both files. Usage:
graft_cast.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

COMPONENTS = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


def read(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    assert a['componentType'] == 5126 and 'byteStride' not in v
    n = a['count'] * COMPONENTS[a['type']]
    data = np.frombuffer(binary, '<f4', n, v.get('byteOffset', 0) + a.get('byteOffset', 0))
    return data.reshape(a['count'], -1), a['type']


def append(doc, binary, values, kind):
    binary.extend(b'\0' * (-len(binary) % 4)); data = values.astype('<f4').tobytes()
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5126,
                             'count': len(values), 'type': kind,
                             **({'min': values.min(0).tolist(), 'max': values.max(0).tolist()} if kind == 'SCALAR' else {})})
    return len(doc['accessors']) - 1


src, sbin = read_glb(HERE / 'work/cast_v2.glb')
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
sanim = next(a for a in src['animations'] if a['name'] == 'Cast')
dnodes = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
for n in src['nodes']:
    if n.get('name') in dnodes and 'mesh' not in n and 'skin' not in n:
        d = doc['nodes'][dnodes[n['name']]]
        for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
            assert np.allclose(n.get(key, default), d.get(key, default), atol=1e-5), (n['name'], key)
# Blender keys the clip from frame 1; remove that offset as zero_times.py does in production
start = min(read(src, sbin, s['input'])[0][0, 0] for s in sanim['samplers'])
for clip in ['Cast', 'Attack']:
    danim = next(a for a in doc['animations'] if a['name'] == clip)
    channels, samplers = [], []
    for ch in sanim['channels']:
        name = src['nodes'][ch['target']['node']]['name']
        s = sanim['samplers'][ch['sampler']]
        t, _ = read(src, sbin, s['input']); t = t - start; v, kind = read(src, sbin, s['output'])
        assert abs(t[0, 0]) < 1e-6 and abs(t[-1, 0] - 1.375) < 1e-4, (t[0], t[-1])
        samplers.append({'input': append(doc, binary, t.copy(), 'SCALAR'), 'output': append(doc, binary, v.copy(), kind),
                         'interpolation': s.get('interpolation', 'LINEAR')})
        channels.append({'sampler': len(samplers) - 1, 'target': {'node': dnodes[name], 'path': ch['target']['path']}})
    old = {(doc['nodes'][c['target']['node']]['name'], c['target']['path']) for c in danim['channels']}
    new = {(doc['nodes'][c['target']['node']]['name'], c['target']['path']) for c in channels}
    assert old == new, sorted(old ^ new)[:10]
    danim['channels'] = channels; danim['samplers'] = samplers
    print('GRAFTED', clip, len(channels), 'channels,', len(t), 'samples, end', float(t[-1, 0]))
write_glb(Path(sys.argv[2]), doc, bytes(binary))
