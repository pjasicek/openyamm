#!/usr/bin/env python3
"""Replace one animation of a runtime GLB by the same-named animation of another GLB with the same skeleton, matching
channels by target node name and path; geometry, skins, LODs, materials and variants are untouched (the buffer is
compacted afterwards). Arrow scale keys keep STEP interpolation (prepare_runtime.py of the m532 project).
Usage: transplant_attack.py <source.glb> <target.glb> <out.glb> [animation=Attack]
       transplant_attack.py --compare <a.glb> <b.glb> [animation]   (max abs difference per channel)"""
import sys, struct
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared'))
from merge_head_material import read_glb, write_glb, accessor_array
import region_variants as R

COMP = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


def channels(d, b, name):
    a = next(x for x in d['animations'] if x['name'] == name); out = {}
    for c in a['channels']:
        s = a['samplers'][c['sampler']]; key = (d['nodes'][c['target']['node']].get('name'), c['target']['path'])
        out[key] = (accessor_array(d, b, s['input']), accessor_array(d, b, s['output']), s.get('interpolation', 'LINEAR'))
    return a, out


def add_accessor(d, b, arr, kind, minmax=False):
    arr = np.ascontiguousarray(arr, dtype=np.float32)
    while len(b) % 4:
        b.append(0)
    off = len(b); b.extend(arr.tobytes())
    d['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes})
    acc = {'bufferView': len(d['bufferViews']) - 1, 'componentType': 5126, 'count': int(arr.shape[0]), 'type': kind}
    if minmax:
        acc['min'] = [float(arr.min())]; acc['max'] = [float(arr.max())]
    d['accessors'].append(acc); return len(d['accessors']) - 1


def main():
    if sys.argv[1] == '--compare':
        name = sys.argv[4] if len(sys.argv) > 4 else 'Attack'
        da, ba = read_glb(Path(sys.argv[2])); db, bb = read_glb(Path(sys.argv[3]))
        _, ca = channels(da, ba, name); _, cb = channels(db, bb, name)
        worst = 0.; missing = set(ca) ^ set(cb)
        for k in set(ca) & set(cb):
            if ca[k][1].shape != cb[k][1].shape:
                print('SHAPE', k, ca[k][1].shape, cb[k][1].shape); worst = 1e9; continue
            diff = float(np.abs(ca[k][1] - cb[k][1]).max()); tdiff = float(np.abs(ca[k][0] - cb[k][0]).max())
            worst = max(worst, diff, tdiff)
        print('COMPARE', name, 'channels', len(ca), len(cb), 'unmatched', sorted(missing)[:6], 'max abs diff', worst); return
    src, dst, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); name = sys.argv[4] if len(sys.argv) > 4 else 'Attack'
    ds, bs = read_glb(src); d, b = read_glb(dst); b = bytearray(b)
    _, cs = channels(ds, bs, name)
    a = next(x for x in d['animations'] if x['name'] == name)
    nodes = {n.get('name'): i for i, n in enumerate(d['nodes'])}
    done = 0; inputs = {}
    for c in a['channels']:
        key = (d['nodes'][c['target']['node']].get('name'), c['target']['path'])
        if key not in cs:
            raise SystemExit(f'missing source channel {key}')
        t, v, interp = cs[key]; s = a['samplers'][c['sampler']]
        tk = t.astype(np.float32).tobytes()                        # one shared time accessor per distinct key set
        if tk not in inputs:
            inputs[tk] = add_accessor(d, b, t.reshape(-1), 'SCALAR', minmax=True)
        s['input'] = inputs[tk]
        s['output'] = add_accessor(d, b, v, {1: 'SCALAR', 3: 'VEC3', 4: 'VEC4'}[v.shape[1] if v.ndim > 1 else 1])
        s['interpolation'] = 'STEP' if key == ('Arrow', 'scale') else interp
        done += 1
    extra = set(cs) - {(d['nodes'][c['target']['node']].get('name'), c['target']['path']) for c in a['channels']}
    if extra:
        raise SystemExit(f'source has channels the target lacks: {sorted(extra)[:5]}')
    for k in ('extras',):
        if k in next(x for x in ds['animations'] if x['name'] == name):
            a[k] = next(x for x in ds['animations'] if x['name'] == name)[k]
    d, b = R._compact(d, b); write_glb(out, d, bytearray(b))
    print('TRANSPLANTED', name, done, 'channels ->', out)


main()
