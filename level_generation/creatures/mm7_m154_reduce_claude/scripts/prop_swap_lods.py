#!/usr/bin/env python3
"""Attachment GLB (one node: LOD0 mesh + openyamm_lods) with new geometry per level: each given level's primitive takes
the positions, normals, UVs and triangles of work/<npz> (from bow_rings.py / arrow_rings.py); '-' keeps the source
level. Materials, variants, images, node and mesh names stay; unreferenced buffer data is compacted.
Usage: prop_swap_lods.py <source glb> <out glb> <lod0.npz|-> <lod1.npz|-> <lod2.npz|-> <lod3.npz|->"""
import copy, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
src, out = Path(sys.argv[1]), Path(sys.argv[2]); levels = sys.argv[3:]
doc, binary = read_glb(src); binary = bytearray(binary)
node = next(n for n in doc['nodes'] if 'mesh' in n); base = doc['meshes'][node['mesh']]
chain = [node['mesh']] + base.get('extras', {}).get('openyamm_lods', [])
assert len(chain) == len(levels), (len(chain), levels)


def add(data, ctype, kind, target=None, minmax=False):
    raw = data.tobytes(); binary.extend(b'\0' * (-len(binary) % 4)); off = len(binary); binary.extend(raw)
    view = {'buffer': 0, 'byteOffset': off, 'byteLength': len(raw)}
    if target:
        view['target'] = target
    doc['bufferViews'].append(view)
    acc = {'bufferView': len(doc['bufferViews']) - 1, 'componentType': ctype, 'count': len(data), 'type': kind}
    if minmax:
        acc['min'] = data.min(0).tolist(); acc['max'] = data.max(0).tolist()
    doc['accessors'].append(acc); return len(doc['accessors']) - 1


counts = []
for mi, lv in zip(chain, levels):
    prim = doc['meshes'][mi]['primitives'][0]
    if lv != '-':
        d = np.load(lv)
        prim['attributes'] = {'POSITION': add(d['verts'].astype(np.float32), 5126, 'VEC3', 34962, True),
                              'NORMAL': add(d['normals'].astype(np.float32), 5126, 'VEC3', 34962),
                              'TEXCOORD_0': add(d['uv'].astype(np.float32), 5126, 'VEC2', 34962)}
        prim['indices'] = add(d['faces'].astype(np.uint32).ravel()[:, None], 5125, 'SCALAR', 34963)
        doc['accessors'][prim['indices']]['count'] = d['faces'].size
    counts.append(doc['accessors'][prim['indices']]['count'] // 3)
# compact
used = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()) | {p['indices']}
amap = {o: i for i, o in enumerate(sorted(used))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, packed, nviews = {}, bytearray(), []
for i, o in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][o]); s = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed); packed.extend(binary[s:s + v['byteLength']])
    nviews.append(v); vmap[o] = i
doc['accessors'] = [dict(doc['accessors'][o], bufferView=vmap[doc['accessors'][o]['bufferView']]) for o in sorted(used)]
doc['bufferViews'] = nviews
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
write_glb(out, doc, bytes(packed))
print('PROP', out.name, 'LOD tris', counts)
