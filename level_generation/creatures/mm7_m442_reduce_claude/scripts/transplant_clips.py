#!/usr/bin/env python3
"""Replace the clips of the reduced GLB with the clips of a newer production export (review 2026-10-20: the goblin's
Standing floor lift and the Armed Death 1 death were made in ../mm7_m442_claude after this reduction). The reduction
changed only the body mesh: nodes, skin and clips were identical to the source (compare_glb.py), so the new export's
animations are copied as they are, by node index, after checking that both GLBs have the same node names in the same
order and the same inverse bind matrices. The old animation accessors are dropped and the buffer repacked
(claude_shared/region_variants.py _compact). Everything else (meshes, LODs, materials, variants) is untouched.
Usage: [REBIND=<joint,...>] transplant_clips.py <reduced.glb> <new production.glb> <out.glb>"""
import copy
import os
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV

TYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
COMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def accessor_bytes(doc, binary, index):
    acc = doc['accessors'][index]; view = doc['bufferViews'][acc['bufferView']]
    size = np.dtype(TYPES[acc['componentType']]).itemsize * COMP[acc['type']]
    stride = view.get('byteStride', size); start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    if stride == size:
        return bytes(binary[start:start + size * acc['count']])
    return b''.join(bytes(binary[start + i * stride:start + i * stride + size]) for i in range(acc['count']))


def main(reduced, new, out):
    rd, rb = RV.read_glb(Path(reduced)); nd, nb = RV.read_glb(Path(new))
    rb = bytearray(rb)
    names_r = [n.get('name') for n in rd['nodes']]; names_n = [n.get('name') for n in nd['nodes']]
    assert names_r == names_n, 'node lists differ'
    # REBIND=<node,...> (m442 sickle grip fix 2026-10-20: the solved fist moved the Sword joint): those joints may
    # differ; their node transforms and inverse binds are taken from the new export, every other joint must match
    rebind = set(filter(None, os.environ.get('REBIND', '').split(',')))
    new_ibm = {}
    for k, (sr, sn) in enumerate(zip(rd.get('skins', []), nd.get('skins', []))):
        assert sr['joints'] == sn['joints'], 'skin joints differ'
        ir = np.frombuffer(accessor_bytes(rd, rb, sr['inverseBindMatrices']), np.float32).reshape(-1, 16)
        inn = np.frombuffer(accessor_bytes(nd, nb, sn['inverseBindMatrices']), np.float32).reshape(-1, 16)
        bad = {names_r[j] for j, row in zip(sr['joints'], np.abs(ir - inn).max(1)) if row >= 1e-5}
        assert bad <= rebind, f'inverse bind matrices differ: {sorted(bad - rebind)}'
        if bad:
            new_ibm[k] = inn.astype(np.float32).tobytes(); print('REBIND skin', k, sorted(bad))
    for j, (a, b) in enumerate(zip(rd['nodes'], nd['nodes'])):
        if names_r[j] in rebind:
            for key in ('translation', 'rotation', 'scale', 'matrix'):
                if key in b:
                    a[key] = copy.deepcopy(b[key])
                else:
                    a.pop(key, None)
    # accessors used by anything but the animations
    keep = set()
    for mesh in rd['meshes']:
        for prim in mesh['primitives']:
            keep.update(prim['attributes'].values())
            if 'indices' in prim:
                keep.add(prim['indices'])
            for target in prim.get('targets', []):
                keep.update(target.values())
    for skin in rd.get('skins', []):
        if 'inverseBindMatrices' in skin:
            keep.add(skin['inverseBindMatrices'])
    amap = {old: new for new, old in enumerate(sorted(keep))}
    rd['accessors'] = [rd['accessors'][old] for old in sorted(keep)]
    for mesh in rd['meshes']:
        for prim in mesh['primitives']:
            prim['attributes'] = {k: amap[v] for k, v in prim['attributes'].items()}
            if 'indices' in prim:
                prim['indices'] = amap[prim['indices']]
            for target in prim.get('targets', []):
                for k in target:
                    target[k] = amap[target[k]]
    for skin in rd.get('skins', []):
        if 'inverseBindMatrices' in skin:
            skin['inverseBindMatrices'] = amap[skin['inverseBindMatrices']]
    for k, data in new_ibm.items():                      # replaced inverse binds (REBIND)
        rb += b'\0' * (-len(rb) % 4)
        rd['bufferViews'].append({'buffer': 0, 'byteOffset': len(rb), 'byteLength': len(data)})
        rb += data
        acc = copy.deepcopy(rd['accessors'][rd['skins'][k]['inverseBindMatrices']]); acc['bufferView'] = len(rd['bufferViews']) - 1
        acc.pop('byteOffset', None); rd['accessors'].append(acc); rd['skins'][k]['inverseBindMatrices'] = len(rd['accessors']) - 1
    # the new animations, their accessors and data appended
    anims = copy.deepcopy(nd['animations']); cache = {}
    for anim in anims:
        for sampler in anim['samplers']:
            for key in ('input', 'output'):
                old = sampler[key]
                if old not in cache:
                    data = accessor_bytes(nd, nb, old)
                    rb += b'\0' * (-len(rb) % 4)
                    rd['bufferViews'].append({'buffer': 0, 'byteOffset': len(rb), 'byteLength': len(data)})
                    rb += data
                    acc = copy.deepcopy(nd['accessors'][old]); acc['bufferView'] = len(rd['bufferViews']) - 1
                    acc.pop('byteOffset', None)
                    rd['accessors'].append(acc); cache[old] = len(rd['accessors']) - 1
                sampler[key] = cache[old]
    rd['animations'] = anims
    rd, packed = RV._compact(rd, bytes(rb))
    RV.write_glb(Path(out), rd, bytearray(packed))
    dur = {a['name']: round(max(rd['accessors'][s['input']]['max'][0] for s in a['samplers']), 3) for a in rd['animations']}
    print('TRANSPLANT', out, 'clips', dur)


if __name__ == '__main__':
    main(*sys.argv[1:4])
