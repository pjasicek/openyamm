#!/usr/bin/env python3
"""Replace a GLB's clips with those of a re-exported source of the same rig (review 2026-10-20: the source project's
walk/run feet were fixed after this reduction; the reduced geometry, LODs, materials and variants stay byte-for-byte).
Channels are re-targeted by node name (the viewer copies carry extra attachment nodes); every animated node must exist
in the target under a unique name. Every animation of <clips.glb> replaces the target's, and unreferenced
accessors/buffer views are compacted away.
Usage: transplant_clips.py <clips.glb> <target.glb> <out.glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, dst, out = (Path(a) for a in sys.argv[1:4])
sdoc, sbin = read_glb(src)
doc, binary = read_glb(dst); binary = bytearray(binary)
names = [n.get('name') for n in doc['nodes']]
index = {n: i for i, n in enumerate(names) if names.count(n) == 1}
anims = []
for a in sdoc.get('animations', []):
    a = copy.deepcopy(a)
    for c in a['channels']:
        c['target']['node'] = index[sdoc['nodes'][c['target']['node']]['name']]
    for s in a['samplers']:
        s['input'] = append_accessor(doc, binary, sdoc['accessors'][s['input']], accessor_bytes(sdoc, sbin, s['input']))
        s['output'] = append_accessor(doc, binary, sdoc['accessors'][s['output']], accessor_bytes(sdoc, sbin, s['output']))
    anims.append(a)
old = [a['name'] for a in doc.get('animations', [])]
assert sorted(old) == sorted(a['name'] for a in anims), f'clip sets differ: {old}'
doc['animations'] = anims

used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values())
        if 'indices' in p:
            used.add(p['indices'])
        for t in p.get('targets', []):
            used |= set(t.values())
for s in doc.get('skins', []):
    if 'inverseBindMatrices' in s:
        used.add(s['inverseBindMatrices'])
for a in doc['animations']:
    for s in a['samplers']:
        used |= {s['input'], s['output']}
amap = {o: n for n, o in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} |
               {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, newbin, new_views = {}, bytearray(), []
for n, o in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][o]); start = v.get('byteOffset', 0)
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin)
    newbin.extend(binary[start:start + v['byteLength']]); new_views.append(v); vmap[o] = n
doc['accessors'] = [dict(doc['accessors'][o], bufferView=vmap[doc['accessors'][o]['bufferView']]) for o in sorted(used)]
doc['bufferViews'] = new_views
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
        if 'indices' in p:
            p['indices'] = amap[p['indices']]
        if 'targets' in p:
            p['targets'] = [{k: amap[v] for k, v in t.items()} for t in p['targets']]
for s in doc.get('skins', []):
    if 'inverseBindMatrices' in s:
        s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc['animations']:
    for s in a['samplers']:
        s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
write_glb(out, doc, bytes(newbin))
print('TRANSPLANTED', len(anims), 'clips', src.name, '->', out.name, f'{len(newbin) / 1e6:.2f} MB')
