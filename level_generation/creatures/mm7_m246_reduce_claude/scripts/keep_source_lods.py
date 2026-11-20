#!/usr/bin/env python3
"""Put the source GLB's own LOD meshes back for the listed levels (colour and shadow), in place: the rebuilt LOD3 of
the reduced Goblin flattened the crest into a ribbon and hid the face under the helmet (review/lods/), while the
source's accepted LOD3 (553) keeps both. Same skin and joint order in both files (swap_lod0.py keeps the source's),
so the primitives are copied with their accessors; KHR_materials_variants mappings come along. Unreferenced buffer data
is compacted. Usage: keep_source_lods.py <source.glb> <glb> <level,...> [mesh node, default M246]"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src_path, path, levels = Path(sys.argv[1]), Path(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')]
NODE = sys.argv[4] if len(sys.argv) > 4 else 'M246'
sd, sb = read_glb(src_path); doc, binary = read_glb(path); binary = bytearray(binary)
sn = next(n for n in sd['nodes'] if n.get('name') == NODE); dn = next(n for n in doc['nodes'] if n.get('name') == NODE)
sj = [sd['nodes'][i]['name'] for i in sd['skins'][sn['skin']]['joints']]
dj = [doc['nodes'][i]['name'] for i in doc['skins'][dn['skin']]['joints']]
assert sj == dj, 'joint order differs'
smat = [m['name'] for m in sd['materials']]; dmat = [m['name'] for m in doc['materials']]
assert smat == dmat, 'materials differ'
se, de = sd['meshes'][sn['mesh']]['extras'], doc['meshes'][dn['mesh']]['extras']
for lv in levels:
    for key in ('openyamm_lods', 'openyamm_shadow_lods'):
        si = se[key][lv - 1] if key == 'openyamm_lods' else se[key][lv]
        di = de[key][lv - 1] if key == 'openyamm_lods' else de[key][lv]
        prims = []
        for p in sd['meshes'][si]['primitives']:
            q = copy.deepcopy(p)
            q['attributes'] = {k: append_accessor(doc, binary, sd['accessors'][a], accessor_bytes(sd, sb, a)) for k, a in p['attributes'].items()}
            q['indices'] = append_accessor(doc, binary, sd['accessors'][p['indices']], accessor_bytes(sd, sb, p['indices']))
            prims.append(q)
        old = sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][di]['primitives'])
        doc['meshes'][di]['primitives'] = prims
        print('KEPT', doc['meshes'][di]['name'], old, '->', sum(doc['accessors'][p['indices']]['count'] // 3 for p in prims))
# compact (as swap_lod0.py)
used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()) | {p['indices']}
for s in doc['skins']:
    used.add(s['inverseBindMatrices'])
for a in doc.get('animations', []):
    for s in a['samplers']:
        used |= {s['input'], s['output']}
amap = {o: n for n, o in enumerate(sorted(used))}
views_used = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, nb, views = {}, bytearray(), []
for n, o in enumerate(views_used):
    v = copy.deepcopy(doc['bufferViews'][o]); st = v.get('byteOffset', 0)
    nb.extend(b'\0' * (-len(nb) % 4)); v['byteOffset'] = len(nb); nb.extend(binary[st:st + v['byteLength']]); views.append(v); vmap[o] = n
doc['accessors'] = [dict(doc['accessors'][o], bufferView=vmap[doc['accessors'][o]['bufferView']]) for o in sorted(used)]
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
write_glb(path, doc, bytes(nb)); print('WROTE', path, f'{len(nb) / 1e6:.2f} MB')
