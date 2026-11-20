#!/usr/bin/env python3
"""Replace one animation (default Attack, ANIM=<name>) of a runtime GLB with the same-named animation of a clips GLB
(scripts/export_clips.py), matching channels by target node name. Channels of the base animation whose node the
clips GLB does not animate (the static Socket_Palm_* keys) keep their first value over the new duration. Mesh,
skin, materials, variants, images and every other animation keep their bytes; unreferenced accessors and buffer
views are dropped (buffer compacted). Works on LOD'd GLBs: animations target skeleton nodes only.
Usage: splice_attack.py <in.glb> <clips.glb> <out.glb>"""
import copy, os, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

base_p, clips_p, out_p = (Path(a) for a in sys.argv[1:4])
NAME = os.environ.get('ANIM', 'Attack')
doc, binary = read_glb(base_p); binary = bytearray(binary)
cdoc, cbin = read_glb(clips_p)
node_ix = {n['name']: i for i, n in enumerate(doc['nodes'])}
ai = next(i for i, a in enumerate(doc['animations']) if a['name'] == NAME)
old = doc['animations'][ai]
src = next(a for a in cdoc['animations'] if a['name'] == NAME)
new = {'name': NAME, 'channels': [], 'samplers': []}
done, t_end = set(), 0.0
for ch in src['channels']:
    nname = cdoc['nodes'][ch['target']['node']]['name']
    if nname not in node_ix:
        continue
    s = src['samplers'][ch['sampler']]
    inp = append_accessor(doc, binary, cdoc['accessors'][s['input']], accessor_bytes(cdoc, cbin, s['input']))
    out = append_accessor(doc, binary, cdoc['accessors'][s['output']], accessor_bytes(cdoc, cbin, s['output']))
    t_end = max(t_end, cdoc['accessors'][s['input']]['max'][0])
    new['samplers'].append({'input': inp, 'output': out, 'interpolation': s.get('interpolation', 'LINEAR')})
    new['channels'].append({'sampler': len(new['samplers']) - 1, 'target': {'node': node_ix[nname], 'path': ch['target']['path']}})
    done.add((nname, ch['target']['path']))
kept = []
times = np.array([0.0, t_end], np.float32).tobytes()
tin = append_accessor(doc, binary, {'componentType': 5126, 'count': 2, 'type': 'SCALAR', 'min': [0.0], 'max': [t_end]}, times)
for ch in old['channels']:
    nname = doc['nodes'][ch['target']['node']]['name']
    if (nname, ch['target']['path']) in done:
        continue
    s = old['samplers'][ch['sampler']]; acc = doc['accessors'][s['output']]
    raw = accessor_bytes(doc, binary, s['output']); width = len(raw) // acc['count']
    out = append_accessor(doc, binary, dict(acc, count=2), raw[:width] * 2)
    new['samplers'].append({'input': tin, 'output': out, 'interpolation': s.get('interpolation', 'LINEAR')})
    new['channels'].append({'sampler': len(new['samplers']) - 1, 'target': dict(ch['target'])})
    kept.append(f'{nname}.{ch["target"]["path"]}')
doc['animations'][ai] = new

# compact: every accessor referenced anywhere in the JSON, then their buffer views
used = set()
def walk(o, key=None):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('indices', 'inverseBindMatrices', 'input', 'output') and isinstance(v, int):
                used.add(v)
            elif k == 'attributes' or k == 'targets':
                for x in (v if isinstance(v, list) else [v]):
                    used.update(i for i in x.values() if isinstance(i, int))
            else:
                walk(v, k)
    elif isinstance(o, list):
        for v in o:
            walk(v, key)
walk({k: v for k, v in doc.items() if k not in ('accessors', 'bufferViews')})
amap = {o: n for n, o in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, nb, nviews = {}, bytearray(), []
for n, o in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][o]); st = v.get('byteOffset', 0)
    nb.extend(b'\0' * (-len(nb) % 4)); v['byteOffset'] = len(nb); nb.extend(binary[st:st + v['byteLength']])
    nviews.append(v); vmap[o] = n
doc['accessors'] = [dict(doc['accessors'][o], bufferView=vmap[doc['accessors'][o]['bufferView']]) for o in sorted(used)]
doc['bufferViews'] = nviews
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
def remap(o):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k in ('indices', 'inverseBindMatrices', 'input', 'output') and isinstance(v, int):
                o[k] = amap[v]
            elif k in ('attributes', 'targets'):
                for x in (v if isinstance(v, list) else [v]):
                    for kk in x:
                        x[kk] = amap[x[kk]]
            else:
                remap(v)
    elif isinstance(o, list):
        for v in o:
            remap(v)
for k in list(doc):
    if k not in ('accessors', 'bufferViews'):
        remap(doc[k])
write_glb(out_p, doc, bytes(nb))
print(f'SPLICED {NAME}: {len(new["channels"])} channels, {t_end:.3f} s; static kept {kept}; {len(nb) / 1e6:.2f} MB')
