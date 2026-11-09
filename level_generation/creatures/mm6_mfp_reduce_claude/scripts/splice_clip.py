#!/usr/bin/env python3
"""Replace one animation of a runtime GLB with the same-named clip of an armature-only GLB (export_clip.py): channels
matched to target nodes by name, keys copied as new accessors; the old clip's samplers are dropped and unreferenced
buffer data compacted (swap_lod0.py does the compaction the same way). Every target channel of the old clip must get a
new channel (same node and path) so no bone falls back to its rest pose.
Usage: splice_clip.py <target glb> <clip glb> <clip name> <out glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
tgt, clip, name, out = sys.argv[1:5]
doc, binary = read_glb(Path(tgt)); cdoc, cbin = read_glb(Path(clip)); binary = bytearray(binary)
ca = next(a for a in cdoc['animations'] if a['name'] == name)
ti = next(i for i, a in enumerate(doc['animations']) if a['name'] == name)
old = doc['animations'][ti]
tnode = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
new = {'name': name, 'channels': [], 'samplers': []}
cache = {}
for ch in ca['channels']:
    nn = cdoc['nodes'][ch['target']['node']].get('name')
    if nn not in tnode:
        continue
    s = ca['samplers'][ch['sampler']]
    ins = []
    for key in ('input', 'output'):
        idx = s[key]
        if idx not in cache:
            cache[idx] = append_accessor(doc, binary, cdoc['accessors'][idx], accessor_bytes(cdoc, cbin, idx))
        ins.append(cache[idx])
    new['samplers'].append({'input': ins[0], 'output': ins[1], 'interpolation': s.get('interpolation', 'LINEAR')})
    new['channels'].append({'sampler': len(new['samplers']) - 1, 'target': {'node': tnode[nn], 'path': ch['target']['path']}})
have = {(c['target']['node'], c['target']['path']) for c in new['channels']}
need = {(c['target']['node'], c['target']['path']) for c in old['channels']}
missing = need - have
assert not missing, f'{len(missing)} old channels have no new keys, e.g. {[(doc["nodes"][n]["name"], p) for n, p in list(missing)[:5]]}'
doc['animations'][ti] = new
# compact: drop accessors and views no longer referenced (old clip keys)
used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()) | ({p['indices']} if 'indices' in p else set())
        for t in p.get('targets', []): used |= set(t.values())
for s in doc.get('skins', []):
    if 'inverseBindMatrices' in s: used.add(s['inverseBindMatrices'])
for a in doc['animations']:
    for s in a['samplers']: used |= {s['input'], s['output']}
amap = {o: n for n, o in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, packed, nviews = {}, bytearray(), []
for n_, o in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][o]); st = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed)
    packed.extend(binary[st:st + v['byteLength']]); nviews.append(v); vmap[o] = n_
doc['accessors'] = [doc['accessors'][o] for o in sorted(used)]
for a in doc['accessors']: a['bufferView'] = vmap[a['bufferView']]
doc['bufferViews'] = nviews
for im in doc.get('images', []):
    if 'bufferView' in im: im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
        if 'indices' in p: p['indices'] = amap[p['indices']]
        if 'targets' in p: p['targets'] = [{k: amap[v] for k, v in t.items()} for t in p['targets']]
for s in doc.get('skins', []):
    if 'inverseBindMatrices' in s: s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc['animations']:
    for s in a['samplers']: s['input'], s['output'] = amap[s['input']], amap[s['output']]
doc['buffers'][0]['byteLength'] = len(packed)
write_glb(Path(out), doc, bytes(packed))
t = doc['accessors'][new['samplers'][0]['input']]
print(f'SPLICED {name}: {len(new["channels"])} channels, duration {t["max"][0]:.4f} s, old {len(old["channels"])} channels -> {out}')
