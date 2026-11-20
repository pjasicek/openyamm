#!/usr/bin/env python3
"""Static decoration GLB with the reduced LOD0 (deco_build.py's work/<name>_lod0.glb): each LOD0 primitive takes the
reduced geometry of its material (matched by name), except alpha-mask/blend primitives (leaf cards, foam), which
stay byte-for-byte; materials, images and the LOD meshes stay; a LOD level that is no
longer coarser than the new LOD0 is dropped from openyamm_lods; unreferenced buffer data is compacted. The new LOD0
must fill the old bounds (max deviation printed). Usage: deco_swap_glb.py <source.glb> <lod0.glb> <out.glb>"""
import copy
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor, merge_shadow  # noqa: E402

src, new, out = (Path(a) for a in sys.argv[1:4])
doc, binary = read_glb(src); binary = bytearray(binary)
exp, payload = read_glb(new)
node = next(n for n in doc['nodes'] if 'mesh' in n)
enode = next(n for n in exp['nodes'] if 'mesh' in n)
for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
    if any(abs(a - b) > 1e-5 for a, b in zip(node.get(key, default), enode.get(key, default))):
        raise ValueError(f'node {key} differs: {node.get(key)} vs {enode.get(key)}')
mesh = doc['meshes'][node['mesh']]
tris = lambda d, m: sum(d['accessors'][p['indices']]['count'] // 3 for p in m['primitives'])


def positions(d, b, prim):
    return np.frombuffer(accessor_bytes(d, b, prim['attributes']['POSITION']), np.float32).reshape(-1, 3)


old_pts = np.concatenate([positions(doc, binary, p) for p in mesh['primitives']])
eprims = {}
for p in exp['meshes'][enode['mesh']]['primitives']:
    eprims.setdefault(exp['materials'][p['material']]['name'], []).append(p)
for prim in mesh['primitives']:
    name = doc['materials'][prim['material']]['name']
    e = eprims.pop(name)
    if doc['materials'][prim['material']].get('alphaMode', 'OPAQUE') != 'OPAQUE':
        continue    # untouched leaf cards / foam keep their source primitive byte-for-byte (the exporter wrote them white)
    assert len(e) == 1, (name, len(e))
    e = e[0]
    missing = set(prim['attributes']) - set(e['attributes'])
    assert not missing, (name, missing)
    prim['attributes'] = {sem: append_accessor(doc, binary, exp['accessors'][idx], accessor_bytes(exp, payload, idx))
                          for sem, idx in e['attributes'].items() if sem in prim['attributes']}
    prim['indices'] = append_accessor(doc, binary, exp['accessors'][e['indices']], accessor_bytes(exp, payload, e['indices']))
assert not eprims, f'unmatched materials {list(eprims)}'
new_pts = np.concatenate([positions(doc, binary, p) for p in mesh['primitives']])
dev = float(np.abs(np.concatenate([new_pts.min(0) - old_pts.min(0), new_pts.max(0) - old_pts.max(0)])).max())
height = float(np.ptp(old_pts[:, 1]))
assert dev < 0.02 * height, f'bounds moved {dev:.4f} (height {height:.3f})'
lod0 = tris(doc, mesh)
lods = mesh.get('extras', {}).get('openyamm_lods', [])
kept = [i for i in lods if tris(doc, doc['meshes'][i]) < lod0]
counts = [lod0] + [tris(doc, doc['meshes'][i]) for i in kept]
assert all(a > b for a, b in zip(counts, counts[1:])), counts
if kept:
    mesh.setdefault('extras', {})['openyamm_lods'] = kept
elif 'extras' in mesh:
    mesh['extras'].pop('openyamm_lods', None)
dropped = [i for i in lods if i not in kept]
# shadow LODs (lizard bow) pair with [LOD0] + LODs: rebuild LOD0's shadow, keep those of the kept LODs
shadows = mesh.get('extras', {}).get('openyamm_shadow_lods', [])
if shadows:
    assert len(shadows) == len(lods) + 1, (shadows, lods)
    doc['meshes'].append(merge_shadow(doc, binary, mesh))
    mesh['extras']['openyamm_shadow_lods'] = [len(doc['meshes']) - 1] + [shadows[1 + lods.index(i)] for i in kept]
    shadows = mesh['extras']['openyamm_shadow_lods']
# drop unreferenced LOD meshes (they are referenced only by the extras), then compact accessors and views
used_meshes = sorted({n['mesh'] for n in doc['nodes'] if 'mesh' in n} | set(kept) | set(shadows))
mmap = {o: n for n, o in enumerate(used_meshes)}
doc['meshes'] = [doc['meshes'][i] for i in used_meshes]
for n in doc['nodes']:
    if 'mesh' in n:
        n['mesh'] = mmap[n['mesh']]
for m in doc['meshes']:
    if m.get('extras', {}).get('openyamm_lods'):
        m['extras']['openyamm_lods'] = [mmap[i] for i in m['extras']['openyamm_lods']]
    if m.get('extras', {}).get('openyamm_shadow_lods'):
        m['extras']['openyamm_shadow_lods'] = [mmap[i] for i in m['extras']['openyamm_shadow_lods']]
used_acc = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used_acc |= set(p['attributes'].values()) | {p['indices']}
for s in doc.get('skins', []):
    used_acc.add(s['inverseBindMatrices'])
for a in doc.get('animations', []):
    for s in a['samplers']:
        used_acc |= {s['input'], s['output']}
amap = {o: n for n, o in enumerate(sorted(used_acc))}
views = sorted({doc['accessors'][i]['bufferView'] for i in used_acc}
               | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
vmap, packed, new_views = {}, bytearray(), []
for n_, o in enumerate(views):
    v = copy.deepcopy(doc['bufferViews'][o]); start = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed)
    packed.extend(binary[start:start + v['byteLength']]); new_views.append(v); vmap[o] = n_
doc['accessors'] = [dict(doc['accessors'][i], bufferView=vmap[doc['accessors'][i]['bufferView']]) for i in sorted(used_acc)]
doc['bufferViews'] = new_views
for im in doc.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
for s in doc.get('skins', []):
    s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc.get('animations', []):
    for s in a['samplers']:
        s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
write_glb(out, doc, bytes(packed))
print('SWAPPED', src.name, 'LOD chain', counts, 'dropped LOD meshes', len(dropped), f'bounds dev {dev * 1000:.1f} mm')
