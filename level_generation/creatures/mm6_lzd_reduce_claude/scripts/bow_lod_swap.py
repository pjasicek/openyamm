#!/usr/bin/env python3
"""Replace the geometry of LOD levels of a static prop GLB (the shared gate wants LOD1 <= 55 %, LOD2 <= 25 %,
LOD3 <= 10 % of LOD0): each given level's primitive takes the reduced geometry of a prop_build.py export; its own
LOD material, variants and the shadow copy (rebuilt with build_actor_lods.merge_shadow) follow; unreferenced data is
compacted by a pass through prop_swap_glb-style cleanup. Usage: bow_lod_swap.py <in.glb> <out.glb> <level>:<lod0.glb> ..."""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor, merge_shadow  # noqa: E402
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
node = next(n for n in doc['nodes'] if 'mesh' in n); mesh = doc['meshes'][node['mesh']]; ex = mesh['extras']
for spec in sys.argv[3:]:
    level, path = spec.split(':', 1); level = int(level)
    exp, payload = read_glb(Path(path)); ep = exp['meshes'][next(n for n in exp['nodes'] if 'mesh' in n)['mesh']]['primitives']
    assert len(ep) == 1
    target = doc['meshes'][ex['openyamm_lods'][level - 1]]; assert len(target['primitives']) == 1
    p = target['primitives'][0]
    p['attributes'] = {k: append_accessor(doc, binary, exp['accessors'][i], accessor_bytes(exp, payload, i))
                       for k, i in ep[0]['attributes'].items() if k in p['attributes']}
    p['indices'] = append_accessor(doc, binary, exp['accessors'][ep[0]['indices']], accessor_bytes(exp, payload, ep[0]['indices']))
    if ex.get('openyamm_shadow_lods'):
        sh = merge_shadow(doc, binary, target); doc['meshes'][ex['openyamm_shadow_lods'][level]] = dict(sh, name=doc['meshes'][ex['openyamm_shadow_lods'][level]]['name'])
# compact accessors and buffer views
used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()) | {p['indices']}
amap = {o: n for n, o in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc.get('images', [])})
vmap, packed, nv = {}, bytearray(), []
for n_, o in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][o]); s = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed); packed.extend(binary[s:s + v['byteLength']]); nv.append(v); vmap[o] = n_
doc['accessors'] = [dict(doc['accessors'][i], bufferView=vmap[doc['accessors'][i]['bufferView']]) for i in sorted(used)]
doc['bufferViews'] = nv
for im in doc.get('images', []):
    im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
tris = lambda m: sum(doc['accessors'][p['indices']]['count'] // 3 for p in m['primitives'])
counts = [tris(mesh)] + [tris(doc['meshes'][i]) for i in ex['openyamm_lods']]
assert all(a > b for a, b in zip(counts, counts[1:])), counts
write_glb(Path(sys.argv[2]), doc, bytes(packed))
print('LODS', counts, [round(c / counts[0], 3) for c in counts[1:]])
