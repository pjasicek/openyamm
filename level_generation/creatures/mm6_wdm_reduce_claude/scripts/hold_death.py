#!/usr/bin/env python3
"""Burn-death clips (user 2026-10-13: the flying demon dies like the ground demon, a flung pose held while it burns):
Death keeps its keys up to HOLD seconds and holds that pose to its old end; Dead holds the same pose (STEP, 1 s).
Scale channels of --drop-scale nodes are removed from both (the old disintegration shrank the hips to 0.005).
--time-scale stretches the new Death (1.25 plays it 25 % slower: user 2026-10-13).
Usage: hold_death.py <in.glb> <out.glb> HOLD [--drop-scale NODE ...] [--time-scale K]"""
import argparse
import copy
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path); parser.add_argument('destination', type=Path)
parser.add_argument('hold', type=float); parser.add_argument('--drop-scale', nargs='*', default=[])
parser.add_argument('--time-scale', type=float, default=1.0)
args = parser.parse_args()
doc, binary = read_glb(args.source); binary = bytearray(binary)
names = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
dropped = {names[n] for n in args.drop_scale}
for n in dropped:
    assert 'scale' not in doc['nodes'][n], 'the rest scale must be 1 for a dropped scale channel'
WIDTH = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


def floats(index):
    accessor = doc['accessors'][index]
    assert accessor['componentType'] == 5126
    return struct.unpack(f'<{accessor["count"] * WIDTH[accessor["type"]]}f', accessor_bytes(doc, binary, index))


def add(values, template, count):
    accessor = {k: v for k, v in template.items() if k not in ('bufferView', 'byteOffset', 'min', 'max')}
    accessor['count'] = count
    width = WIDTH[accessor['type']]
    accessor['min'] = [min(values[i::width]) for i in range(width)]
    accessor['max'] = [max(values[i::width]) for i in range(width)]
    return append_accessor(doc, binary, accessor, struct.pack(f'<{len(values)}f', *values))


def sample(times, values, width, t, path, interpolation):
    """Channel value at t: the bracketing keys, linear (normalised lerp for rotations) or STEP."""
    key = lambda i: list(values[i * width:(i + 1) * width])
    if t <= times[0]:
        return key(0)
    if t >= times[-1]:
        return key(len(times) - 1)
    i = next(k for k in range(len(times) - 1) if times[k] <= t <= times[k + 1])
    if interpolation == 'STEP':
        return key(i)
    f = (t - times[i]) / (times[i + 1] - times[i])
    a, b = key(i), key(i + 1)
    if path == 'rotation' and sum(x * y for x, y in zip(a, b)) < 0:
        b = [-x for x in b]
    out = [x + (y - x) * f for x, y in zip(a, b)]
    if path == 'rotation':
        length = sum(x * x for x in out) ** .5
        out = [x / length for x in out]
    return out


death = next(a for a in doc['animations'] if a['name'] == 'Death')
old_end = max(max(floats(s['input'])) for s in death['samplers'])
dead = next(a for a in doc['animations'] if a['name'] == 'Dead')
new_death, new_dead = {'name': 'Death', 'channels': [], 'samplers': []}, {'name': 'Dead', 'channels': [], 'samplers': []}
scalar = {'componentType': 5126, 'type': 'SCALAR'}
for channel in death['channels']:
    if channel['target']['node'] in dropped and channel['target']['path'] == 'scale':
        continue
    sampler = death['samplers'][channel['sampler']]
    assert sampler.get('interpolation', 'LINEAR') != 'CUBICSPLINE'
    times, values = floats(sampler['input']), floats(sampler['output'])
    width = WIDTH[doc['accessors'][sampler['output']]['type']]
    held = sample(times, values, width, args.hold, channel['target']['path'], sampler.get('interpolation', 'LINEAR'))
    keep = [i for i, t in enumerate(times) if t < args.hold - 1e-4]
    ends = [args.hold, old_end] if old_end - args.hold > 1e-4 else [args.hold]   # glTF key times strictly increase
    t = [args.time_scale * x for x in [times[i] for i in keep] + ends]
    v = [x for i in keep for x in values[i * width:(i + 1) * width]] + held * len(ends)
    output = doc['accessors'][sampler['output']]
    new_death['samplers'].append({'input': add(t, scalar, len(t)), 'output': add(v, output, len(t)),
                                  'interpolation': sampler.get('interpolation', 'LINEAR')})
    new_death['channels'].append({'sampler': len(new_death['samplers']) - 1, 'target': copy.deepcopy(channel['target'])})
    new_dead['samplers'].append({'input': add([0.0, 1.0], scalar, 2), 'output': add(held + held, output, 2),
                                 'interpolation': 'STEP'})
    new_dead['channels'].append({'sampler': len(new_dead['samplers']) - 1, 'target': copy.deepcopy(channel['target'])})
doc['animations'] = [new_death if a is death else new_dead if a is dead else a for a in doc['animations']]

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
write_glb(args.destination, doc, bytes(packed))
print('HELD DEATH at', args.hold, 's to', round(old_end, 3), 's, time x', args.time_scale, ';', len(new_death['channels']), 'channels; dropped scale on',
      args.drop_scale, f'{len(packed) / 1e6:.1f} MB')
