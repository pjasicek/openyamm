#!/usr/bin/env python3
"""Attack v2: replace one clip of a runtime body GLB with the same clip from an animation-only export of the
creature master (../mm8_m432_claude/scripts/attack_v2_export.py), by joint name; geometry, skin, materials,
variants and the other clips stay byte-identical (only the buffer layout of the replaced clip changes).

  attack_transplant.py compare <body.glb> <anim.glb> [clip]       rest TRS and sampled channel differences
  attack_transplant.py apply <body.glb> <anim.glb> <out.glb> [clip]"""
import struct
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
import normal_map_convention as G  # noqa: E402

COMPONENTS = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


def load(path):
    document, binary = G.read_glb(Path(path).read_bytes())
    views = [binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']] for v in document['bufferViews']]
    return document, views


def accessor_array(document, views, index):
    accessor = document['accessors'][index]
    assert accessor['componentType'] == 5126 and 'sparse' not in accessor and 'byteStride' not in \
        document['bufferViews'][accessor['bufferView']]
    n = COMPONENTS[accessor['type']]
    data = views[accessor['bufferView']]
    start = accessor.get('byteOffset', 0)
    return np.frombuffer(data[start:start + accessor['count'] * n * 4], '<f4').reshape(accessor['count'], n)


def channels(document, views, clip):
    animation = next(a for a in document['animations'] if a['name'] == clip)
    out = {}
    for channel in animation['channels']:
        sampler = animation['samplers'][channel['sampler']]
        assert sampler.get('interpolation', 'LINEAR') in ('LINEAR', 'STEP')
        key = (document['nodes'][channel['target']['node']]['name'], channel['target']['path'])
        out[key] = (accessor_array(document, views, sampler['input'])[:, 0],
                    accessor_array(document, views, sampler['output']), sampler)
    return animation, out


def evaluate(times, values, at, path):
    result = np.stack([np.interp(at, times, values[:, c]) for c in range(values.shape[1])], 1)
    if path == 'rotation':
        result /= np.linalg.norm(result, axis=1)[:, None]
    return result


def compare(body, anim, clip):
    bd, bv = load(body)
    ad, av = load(anim)
    bnodes = {n['name']: n for n in bd['nodes']}
    rest = 0.0
    for node in ad['nodes']:
        other = bnodes.get(node['name'])
        if other is None or 'mesh' in node:
            continue
        for key, default in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])):
            a, b = np.array(node.get(key, default)), np.array(other.get(key, default))
            if key == 'rotation' and a.dot(b) < 0:
                b = -b
            rest = max(rest, float(np.abs(a - b).max()))
    _, bc = channels(bd, bv, clip)
    _, ac = channels(ad, av, clip)
    print('REST max TRS difference', rest)
    print('CHANNELS body', len(bc), 'anim', len(ac), 'missing in anim', sorted(set(bc) - set(ac))[:10],
          'extra in anim', sorted(set(ac) - set(bc))[:10])
    worst = {}
    for key in sorted(set(bc) & set(ac)):
        at = np.union1d(bc[key][0], ac[key][0])
        a = evaluate(*ac[key][:2], at, key[1])
        b = evaluate(*bc[key][:2], at, key[1])
        if key[1] == 'rotation':
            b = np.where((np.sum(a * b, 1) < 0)[:, None], -b, b)
        d = float(np.abs(a - b).max())
        if d > worst.get(key[1], (0, None))[0]:
            worst[key[1]] = (d, key[0])
        duration = (float(bc[key][0][-1]), float(ac[key][0][-1]))
    print('MAX sampled difference by path', worst, 'durations body/anim', duration)


def apply(body, anim, out, clip):
    bd, bv = load(body)
    ad, av = load(anim)
    old, bc = channels(bd, bv, clip)
    _, ac = channels(ad, av, clip)
    assert set(ac) == set(bc), ('channel sets differ', sorted(set(ac) ^ set(bc))[:10])
    index = {n['name']: i for i, n in enumerate(bd['nodes'])}
    new = {'name': clip, 'channels': [], 'samplers': []}
    for (name, path), (times, values, sampler) in sorted(ac.items()):
        accessors = []
        for array, kind in ((times[:, None], 'SCALAR'), (values, 'VEC4' if values.shape[1] == 4 else 'VEC3')):
            bv.append(np.ascontiguousarray(array, '<f4').tobytes())
            bd['bufferViews'].append({'buffer': 0, 'byteOffset': 0, 'byteLength': len(bv[-1])})
            accessor = {'bufferView': len(bd['bufferViews']) - 1, 'componentType': 5126, 'count': len(array),
                        'type': kind}
            if kind == 'SCALAR':
                accessor['min'], accessor['max'] = [float(times.min())], [float(times.max())]
            bd['accessors'].append(accessor)
            accessors.append(len(bd['accessors']) - 1)
        new['samplers'].append({'input': accessors[0], 'output': accessors[1],
                                'interpolation': sampler.get('interpolation', 'LINEAR')})
        new['channels'].append({'sampler': len(new['samplers']) - 1, 'target': {'node': index[name], 'path': path}})
    bd['animations'][bd['animations'].index(old)] = new
    # Drop the replaced clip's accessors and views; every other reference is renumbered unchanged.
    references = []
    for mesh in bd['meshes']:
        for primitive in mesh['primitives']:
            references.extend((primitive['attributes'], k) for k in primitive['attributes'])
            if 'indices' in primitive:
                references.append((primitive, 'indices'))
            for target in primitive.get('targets', []):
                references.extend((target, k) for k in target)
    for skin in bd.get('skins', []):
        if 'inverseBindMatrices' in skin:
            references.append((skin, 'inverseBindMatrices'))
    for animation in bd['animations']:
        for sampler in animation['samplers']:
            references.extend(((sampler, 'input'), (sampler, 'output')))
    used = sorted({o[k] for o, k in references})
    renumber = {old_i: new_i for new_i, old_i in enumerate(used)}
    bd['accessors'] = [bd['accessors'][i] for i in used]
    for o, k in references:
        o[k] = renumber[o[k]]
    view_refs = [(a, 'bufferView') for a in bd['accessors'] if 'bufferView' in a]
    view_refs += [(img, 'bufferView') for img in bd.get('images', []) if 'bufferView' in img]
    used_views = sorted({o[k] for o, k in view_refs})
    vmap = {old_i: new_i for new_i, old_i in enumerate(used_views)}
    bd['bufferViews'] = [bd['bufferViews'][i] for i in used_views]
    bv = [bv[i] for i in used_views]
    for o, k in view_refs:
        o[k] = vmap[o[k]]
    Path(out).write_bytes(G.write_glb(bd, bv))
    print('WROTE', out, 'clip', clip, 'channels', len(new['channels']))


if __name__ == '__main__':
    mode, args = sys.argv[1], sys.argv[2:]
    if mode == 'compare':
        compare(args[0], args[1], args[2] if len(args) > 2 else 'Attack')
    else:
        apply(args[0], args[1], args[2], args[3] if len(args) > 3 else 'Attack')
