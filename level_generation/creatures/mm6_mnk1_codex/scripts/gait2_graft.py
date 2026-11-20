#!/usr/bin/env python3
"""Append the Walk2 and Run2 clips of work/gait2/anim.glb (gait2_export.py) to a copy of the runtime GLB, keeping every
existing clip byte-for-byte. Channels are matched by joint name and path; the joints' rest TRS must agree. Parity first:
the re-exported Walking must reproduce the runtime GLB's Walking (same export path), else the graft is refused.
Usage: gait2_graft.py <runtime in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

COMPONENTS = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}
NEW = ['Walk2', 'Run2']


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


def sample(doc, binary, anim, times):
    """{(joint, path): values at times}, LINEAR/STEP as stored; quaternions sign-aligned to +w."""
    out = {}
    for ch in anim['channels']:
        s = anim['samplers'][ch['sampler']]; t, _ = read(doc, binary, s['input']); v, _ = read(doc, binary, s['output'])
        t = t[:, 0]; name = doc['nodes'][ch['target']['node']]['name']
        if s.get('interpolation') == 'STEP' or len(t) == 1:
            idx = np.clip(np.searchsorted(t, times, side='right') - 1, 0, len(t) - 1); vals = v[idx]
        else:
            vals = np.stack([np.interp(times, t, v[:, c]) for c in range(v.shape[1])], 1)
        if ch['target']['path'] == 'rotation':
            vals = vals / np.linalg.norm(vals, axis=1, keepdims=True); vals *= np.sign(vals[:, 3:4] + 1e-12)
        out[name, ch['target']['path']] = vals
    return out


src, sbin = read_glb(HERE / 'work/gait2/anim.glb')
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
dnodes = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
checked = 0
for n in src['nodes']:
    if n.get('name') in dnodes and 'mesh' not in n and 'skin' not in n:
        d = doc['nodes'][dnodes[n['name']]]; checked += 1
        for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
            assert np.allclose(n.get(key, default), d.get(key, default), atol=1e-5), (n['name'], key)
sanims = {a['name']: a for a in src['animations']}
danims = {a['name']: a for a in doc['animations']}
times = np.linspace(0, 0.8, 97)
a, b = sample(src, sbin, sanims['Walking'], times), sample(doc, binary, danims['Walking'], times)
assert set(a) == set(b), sorted(set(a) ^ set(b))[:10]
worst = max((float(np.abs(a[k] - b[k]).max()), k) for k in a)
print('PARITY Walking re-export vs runtime: max channel difference', worst, 'joints checked', checked)
assert worst[0] < 2e-4, worst
for name in NEW:
    assert name not in danims, name
    sanim = sanims[name]; channels, samplers = [], []
    start = min(read(src, sbin, s['input'])[0][0, 0] for s in sanim['samplers'])
    for ch in sanim['channels']:
        jn = src['nodes'][ch['target']['node']]['name']
        s = sanim['samplers'][ch['sampler']]
        t, _ = read(src, sbin, s['input']); t = t - start; v, kind = read(src, sbin, s['output'])
        samplers.append({'input': append(doc, binary, t.copy(), 'SCALAR'), 'output': append(doc, binary, v.copy(), kind),
                         'interpolation': s.get('interpolation', 'LINEAR')})
        channels.append({'sampler': len(samplers) - 1, 'target': {'node': dnodes[jn], 'path': ch['target']['path']}})
    old = {(doc['nodes'][c['target']['node']]['name'], c['target']['path']) for c in danims['Walking']['channels']}
    new = {(doc['nodes'][c['target']['node']]['name'], c['target']['path']) for c in channels}
    assert old == new, sorted(old ^ new)[:10]
    doc['animations'].append({'name': name, 'channels': channels, 'samplers': samplers})
    print('GRAFTED', name, len(channels), 'channels, end', float(max(read(doc, binary, s['input'])[0][-1, 0] for s in samplers)))
write_glb(Path(sys.argv[2]), doc, bytes(binary))
