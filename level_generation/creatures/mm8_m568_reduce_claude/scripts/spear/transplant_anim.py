#!/usr/bin/env python3
"""Replace every clip of a runtime creature GLB with the clips of an animation-only export of the same rig
(export_anim.py), matched by node name. Every animated node's rest TRS must agree (1e-5); meshes, skins, LODs,
materials and variants are kept, and the old clip data is dropped from the buffer.
Usage: transplant_anim.py <base.glb> <anim.glb> <out.glb>"""
import copy, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes  # noqa: E402

base, bbin = read_glb(Path(sys.argv[1])); anim, abin = read_glb(Path(sys.argv[2]))
names = {n.get('name'): i for i, n in enumerate(base['nodes'])}
def trs(n): return np.concatenate([n.get('translation', [0, 0, 0]), n.get('rotation', [0, 0, 0, 1]), n.get('scale', [1, 1, 1])])
worst = 0.
for a in anim['animations']:
    for c in a['channels']:
        an = anim['nodes'][c['target']['node']]; bn = base['nodes'][names[an['name']]]
        d = trs(an) - trs(bn)
        if np.dot(an.get('rotation', [0, 0, 0, 1]), bn.get('rotation', [0, 0, 0, 1])) < 0:
            d[3:7] = np.array(an.get('rotation')) + bn.get('rotation')
        worst = max(worst, float(np.abs(d).max()))
assert worst < 1e-5, f'rest TRS mismatch {worst}'
# keep every accessor and buffer view not used only by the old clips
old = {i for a in base.get('animations', []) for s in a['samplers'] for i in (s['input'], s['output'])}
keep = [i for i in range(len(base['accessors'])) if i not in old]
views = sorted({base['accessors'][i]['bufferView'] for i in keep if 'bufferView' in base['accessors'][i]} |
               {im['bufferView'] for im in base.get('images', []) if 'bufferView' in im})
binary = bytearray(); vmap = {}
for v in views:
    bv = copy.deepcopy(base['bufferViews'][v]); s = bv.get('byteOffset', 0)
    binary.extend(b'\0' * (-len(binary) % 16)); data = bbin[s:s + bv['byteLength']]
    bv['byteOffset'] = len(binary); binary.extend(data); vmap[v] = len(vmap); base['bufferViews'][v] = bv
base['bufferViews'] = [base['bufferViews'][v] for v in views]
amap = {}
accs = []
for i in keep:
    a = copy.deepcopy(base['accessors'][i])
    if 'bufferView' in a:
        a['bufferView'] = vmap[a['bufferView']]
    amap[i] = len(accs); accs.append(a)
base['accessors'] = accs
for im in base.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
def remap(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ('indices', 'inverseBindMatrices') and isinstance(v, int):
                obj[k] = amap[v]
            elif k == 'attributes':
                obj[k] = {kk: amap[vv] for kk, vv in v.items()}
            elif k == 'targets' and isinstance(v, list):
                obj[k] = [{kk: amap[vv] for kk, vv in t.items()} for t in v]
            else:
                remap(v)
    elif isinstance(obj, list):
        for x in obj:
            remap(x)
remap(base['meshes']); remap(base.get('skins', []))
anims = []
for a in anim['animations']:
    samplers = []
    for s in a['samplers']:
        ns = dict(s)
        for key in ('input', 'output'):
            src = anim['accessors'][s[key]]; packed = accessor_bytes(anim, abin, s[key])
            binary.extend(b'\0' * (-len(binary) % 16))
            base['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(packed)}); binary.extend(packed)
            na = copy.deepcopy(src); na['bufferView'] = len(base['bufferViews']) - 1; na.pop('byteOffset', None)
            base['accessors'].append(na); ns[key] = len(base['accessors']) - 1
        samplers.append(ns)
    channels = [{'sampler': c['sampler'], 'target': {'node': names[anim['nodes'][c['target']['node']]['name']], 'path': c['target']['path']}}
                for c in a['channels']]
    anims.append({'name': a['name'], 'samplers': samplers, 'channels': channels})
base['animations'] = anims
write_glb(Path(sys.argv[3]), base, bytes(binary))
print('TRANSPLANTED', [a['name'] for a in anims], 'rest worst', worst, 'bytes', len(binary))
