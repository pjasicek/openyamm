#!/usr/bin/env python3
"""Drop accessors and buffer views no mesh, skin, animation or image references (knee_cuts.py appends new ones and
leaves the old ones in the buffer). Same compaction as swap_lod0.py. Usage: compact_glb.py <glb, rewritten in place>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
path = Path(sys.argv[1]); doc, binary = read_glb(path); n0 = len(binary)
used_acc = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used_acc |= set(p['attributes'].values()) | {p['indices']}
for s in doc['skins']:
    used_acc.add(s['inverseBindMatrices'])
for a in doc.get('animations', []):
    for s in a['samplers']:
        used_acc |= {s['input'], s['output']}
amap = {old: new for new, old in enumerate(sorted(used_acc))}
used_views = sorted({doc['accessors'][i]['bufferView'] for i in used_acc} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, newbin, views = {}, bytearray(), []
for new, old in enumerate(used_views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin)
    newbin.extend(binary[start:start + v['byteLength']]); views.append(v); vmap[old] = new
doc['accessors'] = [dict(doc['accessors'][old], bufferView=vmap[doc['accessors'][old]['bufferView']]) for old in sorted(used_acc)]
doc['bufferViews'] = views
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
for s in doc['skins']:
    s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc.get('animations', []):
    for s in a['samplers']:
        s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
write_glb(path, doc, bytes(newbin))
print('COMPACTED', f'{n0 / 1e6:.1f} -> {len(newbin) / 1e6:.1f} MB')
