#!/usr/bin/env python3
"""Installed GLB + work/mp_<..>.npz (per primitive triangles into the GLB's own LOD0 vertices, mpqem.py) -> a LOD0-only GLB
with those index buffers (from mm9_banshee_reduce_claude/scripts/swap_mp.py). Each LOD0 primitive keeps only the vertices it
still uses, every attribute copied byte for byte (positions, normals, UVs, joints, weights exactly the installed ones); a
primitive whose triangles are unchanged keeps its accessors. The old LOD and shadow meshes are dropped (tools/build_actor_lods.py
rebuilds them); materials, variants, images, clips, skin and nodes are unchanged. Usage: swap_mp.py in.glb mp.npz out.glb"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack as G  # noqa: E402

src, mp, out = sys.argv[1:4]
doc, binary = G.read(src); d = np.load(mp)
node = next(n for n in doc['nodes'] if n.get('name') == 'Sheep' and 'mesh' in n)
mesh = doc['meshes'][node['mesh']]; counts = {}
for p in mesh['primitives']:
    name = doc['materials'][p['material']]['name']
    T = d[name].astype(np.int64); T0 = G.acc(doc, bytes(binary), p['indices']).reshape(-1, 3).astype(np.int64)
    counts[name] = len(T)
    if T.shape == T0.shape and (T == T0).all():
        continue
    used = np.unique(T); remap = -np.ones(doc['accessors'][p['attributes']['POSITION']]['count'], np.int64)
    remap[used] = np.arange(len(used))
    for sem, i in list(p['attributes'].items()):
        rows = G.raw_rows(doc, binary, i)[used]
        p['attributes'][sem] = G.append(doc, binary, doc['accessors'][i], rows)
        G.set_minmax(doc, binary, p['attributes'][sem])
    ct = doc['accessors'][p['indices']]['componentType']; assert len(used) < 65536 or ct == 5125
    p['indices'] = G.append(doc, binary, {'componentType': ct, 'type': 'SCALAR'},
                            remap[T].reshape(-1).astype(np.uint16 if ct == 5123 else np.uint32).reshape(-1, 1))
mesh.pop('extras', None)
keep = sorted({n['mesh'] for n in doc['nodes'] if 'mesh' in n}); mmap = {o: k for k, o in enumerate(keep)}
doc['meshes'] = [doc['meshes'][i] for i in keep]
for n in doc['nodes']:
    if 'mesh' in n:
        n['mesh'] = mmap[n['mesh']]
doc, binary = G.compact(doc, binary)
G.write(out, doc, binary)
print('SWAPPED', counts, 'total', sum(counts.values()))
