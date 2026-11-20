# Copied from mm6_cdr1_reduce_claude / mm6_cdr1_claude (v3 base model); unchanged logic.
#!/usr/bin/env python3
"""Installed source GLB with the reduced full-detail geometry: every LOD0 primitive (matched by material name) takes
the candidate's skinned geometry; materials, colour variants, region masks, clips, sockets and the ash mesh stay
byte-for-byte. The old LOD/shadow meshes are dropped (tools/build_actor_lods.py rebuilds them) and unreferenced
buffer data is compacted. Usage: swap_lod0.py <installed.glb> <cand_export.glb> <out.glb> [mesh node, default Demon_Native_Mesh]"""
import copy, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, cand, out = (Path(a) for a in sys.argv[1:4])
NODE = sys.argv[4] if len(sys.argv) > 4 else 'Demon_Native_Mesh'
doc, binary = read_glb(src); binary = bytearray(binary)
exp, payload = read_glb(cand)
node = next(n for n in doc['nodes'] if n.get('name') == NODE)
enode = next(n for n in exp['nodes'] if n.get('name') == NODE)
for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
    assert all(abs(a - b) < 1e-4 for a, b in zip(node.get(key, default), enode.get(key, default))), key
joint_names = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
bind = list(struct.iter_unpack('<16f', accessor_bytes(doc, binary, doc['skins'][node['skin']]['inverseBindMatrices'])))
eskin = exp['skins'][enode['skin']]
remap = [joint_names.index(exp['nodes'][i]['name']) for i in eskin['joints']]
ebind = list(struct.iter_unpack('<16f', accessor_bytes(exp, payload, eskin['inverseBindMatrices'])))
assert all(abs(a - b) < 1e-4 for i, m in zip(remap, ebind) for a, b in zip(bind[i], m)), 'bind space changed'
mesh = doc['meshes'][node['mesh']]
eprims = {exp['materials'][p['material']]['name']: p for p in exp['meshes'][enode['mesh']]['primitives']}
counts = {}
for prim in mesh['primitives']:
    name = doc['materials'][prim['material']]['name']
    e = eprims.pop(name)
    attrs = {}
    for sem, idx in e['attributes'].items():
        acc = exp['accessors'][idx]; packed = accessor_bytes(exp, payload, idx)
        if sem.startswith('JOINTS_'):
            code = {5121: 'B', 5123: 'H'}[acc['componentType']]
            packed = struct.pack('<' + code * (len(packed) // struct.calcsize(code)),
                                 *(remap[v[0]] for v in struct.iter_unpack('<' + code, packed)))
        attrs[sem] = append_accessor(doc, binary, acc, packed)
    prim['attributes'] = attrs
    prim['indices'] = append_accessor(doc, binary, exp['accessors'][e['indices']], accessor_bytes(exp, payload, e['indices']))
    counts[name] = exp['accessors'][e['indices']]['count'] // 3
assert not eprims, f'unmatched candidate materials {list(eprims)}'
mesh.pop('extras', None)
keep = sorted({n['mesh'] for n in doc['nodes'] if 'mesh' in n})
mmap = {old: new for new, old in enumerate(keep)}
doc['meshes'] = [doc['meshes'][i] for i in keep]
for n in doc['nodes']:
    if 'mesh' in n:
        n['mesh'] = mmap[n['mesh']]

# compact: keep only referenced accessors and buffer views
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
write_glb(out, doc, bytes(newbin))
print('SWAPPED', counts, 'total', sum(counts.values()), f'{len(newbin) / 1e6:.1f} MB')
