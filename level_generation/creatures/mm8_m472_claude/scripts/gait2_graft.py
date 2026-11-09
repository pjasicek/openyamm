#!/usr/bin/env python3
"""gait2 (2026-10-21): append the Walk2 and Run2 clips of work/gait2_anim.glb (gait2_export.py) to a runtime Necromancer
GLB, matched by joint name (pattern: mm8_m500_reduce_claude/scripts/graft_cast.py). Every existing clip stays as it is.
Checks first: the joints' rest TRS agree, and the export's Walking reproduces the runtime's Walking (max abs difference
per channel), so the local values mean the same in both files. Usage: gait2_graft.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

NEW = ['Walk2', 'Run2']
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
    doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5126, 'count': len(values),
                             'type': kind, **({'min': values.min(0).tolist(), 'max': values.max(0).tolist()}
                                              if kind == 'SCALAR' else {})})
    return len(doc['accessors']) - 1


def channels(doc, binary, anim):
    out = {}
    for ch in anim['channels']:
        s = anim['samplers'][ch['sampler']]; t, _ = read(doc, binary, s['input']); v, kind = read(doc, binary, s['output'])
        out[(doc['nodes'][ch['target']['node']]['name'], ch['target']['path'])] = (t[:, 0] - t[0, 0], v, kind)
    return out


src, sbin = read_glb(HERE / 'work/gait2_anim.glb')
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
assert not {a['name'] for a in doc['animations']} & set(NEW), 'clips already present'
dnodes = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
for n in src['nodes']:
    if n.get('name') in dnodes and 'mesh' not in n and 'skin' not in n:
        d = doc['nodes'][dnodes[n['name']]]
        for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
            assert np.allclose(n.get(key, default), d.get(key, default), atol=1e-5), (n['name'], key)
sanims = {a['name']: a for a in src['animations']}
# pipeline check on the installed Walking
mine = channels(src, sbin, sanims['Walking'])
theirs = channels(doc, bytes(binary), next(a for a in doc['animations'] if a['name'] == 'Walking'))
assert set(mine) == set(theirs), sorted(set(mine) ^ set(theirs))[:10]
worst = 0.
for k, (t, v, _) in mine.items():
    t2, v2, _ = theirs[k]; assert len(t) == len(t2) and np.allclose(t, t2, atol=1e-4), k
    if k[1] == 'rotation': v, v2 = v * np.sign((v * v2).sum(1))[:, None], v2
    worst = max(worst, float(np.abs(v - v2).max()))
print(f'CHECK Walking: {len(mine)} channels, max abs difference {worst:.2e}')
assert worst < 2e-3
for name in NEW:
    anim = {'name': name, 'channels': [], 'samplers': []}
    for (node, path), (t, v, kind) in channels(src, sbin, sanims[name]).items():
        anim['samplers'].append({'input': append(doc, binary, t[:, None].copy(), 'SCALAR'),
                                 'output': append(doc, binary, v.copy(), kind), 'interpolation': 'LINEAR'})
        anim['channels'].append({'sampler': len(anim['samplers']) - 1, 'target': {'node': dnodes[node], 'path': path}})
    doc['animations'].append(anim)
    print(f'GRAFTED {name}: {len(anim["channels"])} channels, {len(t)} samples, end {float(t[-1]):.4f} s')
write_glb(Path(sys.argv[2]), doc, bytes(binary))
