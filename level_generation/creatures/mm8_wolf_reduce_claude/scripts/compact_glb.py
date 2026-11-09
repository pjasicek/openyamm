#!/usr/bin/env python3
"""Drop accessors and buffer views nothing references any more (the head/neck/shoulder fix scripts append new
accessors and leave the replaced ones behind). Usage: compact_glb.py <in.glb> <out.glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

doc, binary = read_glb(Path(sys.argv[1]))
used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()) | ({p['indices']} if 'indices' in p else set())
used |= {s['inverseBindMatrices'] for s in doc.get('skins', []) if 'inverseBindMatrices' in s}
for a in doc.get('animations', []):
    live = {c['sampler'] for c in a['channels']}
    a['samplers'] = [s for i, s in enumerate(a['samplers']) if i in live] if live else a['samplers']
    remap = {old: new for new, old in enumerate(sorted(live))}
    for c in a['channels']:
        c['sampler'] = remap[c['sampler']]
    for s in a['samplers']:
        used |= {s['input'], s['output']}
amap = {old: new for new, old in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, out, new_views = {}, bytearray(), []
for new, old in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    out.extend(b'\0' * (-len(out) % 4)); v['byteOffset'] = len(out)
    out.extend(binary[start:start + v['byteLength']]); new_views.append(v); vmap[old] = new
doc['accessors'] = [dict(doc['accessors'][old], bufferView=vmap[doc['accessors'][old]['bufferView']]) for old in sorted(used)]
doc['bufferViews'] = new_views
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
        if 'indices' in p:
            p['indices'] = amap[p['indices']]
for s in doc.get('skins', []):
    if 'inverseBindMatrices' in s:
        s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc.get('animations', []):
    for s in a['samplers']:
        s['input'], s['output'] = amap[s['input']], amap[s['output']]
write_glb(Path(sys.argv[2]), doc, bytes(out))
print('COMPACT', f'{len(binary) / 1e6:.2f} -> {len(out) / 1e6:.2f} MB')
