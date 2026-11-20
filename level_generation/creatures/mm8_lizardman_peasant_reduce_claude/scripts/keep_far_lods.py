#!/usr/bin/env python3
"""Reduced export with the installed LOD2/LOD3 and their shadow meshes: Blender's collapse stalls at about 2,400
triangles on this fragmented atlas, so rebuilt LOD2/3 are no lighter than the installed ones (2,744 / 2,417) and look
worse (the collapsed head fins became one wide sheet over the head). The installed far levels already passed the
creature's review and regression. Same skin and joint order (swap_lod0.py kept the installed skin); materials and
variants are copied as they are. Usage: keep_far_lods.py <installed.glb> <reduced.glb> <out.glb> [node]"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

inst, red, out = (Path(a) for a in sys.argv[1:4]); NODE = sys.argv[4] if len(sys.argv) > 4 else 'Body'
src, sbin = read_glb(inst); doc, binary = read_glb(red); binary = bytearray(binary)
sn = next(n for n in src['nodes'] if n.get('name') == NODE); dn = next(n for n in doc['nodes'] if n.get('name') == NODE)
assert [src['nodes'][i]['name'] for i in src['skins'][sn['skin']]['joints']] == \
       [doc['nodes'][i]['name'] for i in doc['skins'][dn['skin']]['joints']], 'joint order differs'
assert [m['name'] for m in src['materials']] == [m['name'] for m in doc['materials']], 'materials differ'
sx, dx = src['meshes'][sn['mesh']]['extras'], doc['meshes'][dn['mesh']]['extras']
for key in ('openyamm_lods', 'openyamm_shadow_lods'):
    levels = (1, 2) if key == 'openyamm_lods' else (2, 3)  # LOD2, LOD3 (shadow list starts with LOD0's shadow)
    for k in levels:
        smesh = src['meshes'][sx[key][k]]; prims = []
        for p in smesh['primitives']:
            q = copy.deepcopy(p)
            q['attributes'] = {s: append_accessor(doc, binary, src['accessors'][i], accessor_bytes(src, sbin, i))
                               for s, i in p['attributes'].items()}
            q['indices'] = append_accessor(doc, binary, src['accessors'][p['indices']], accessor_bytes(src, sbin, p['indices']))
            prims.append(q)
        doc['meshes'][dx[key][k]] = {**copy.deepcopy(smesh), 'primitives': prims}
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives'])
          for i in [dn['mesh']] + dx['openyamm_lods']]
assert all(a > b for a, b in zip(counts, counts[1:])), counts
# compact as swap_lod0.py does: keep only referenced accessors and buffer views (the replaced LOD2/3 data)
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
write_glb(out, doc, bytes(newbin)); print('FAR LODS kept', counts, f'{len(newbin) / 1e6:.1f} MB')
