#!/usr/bin/env python3
"""Installed GLB + work/mp_r<NN>.npz (per LOD0 primitive, triangles into the installed primitive's own vertices) -> a LOD0-only
GLB for tools/build_actor_lods.py: each LOD0 primitive keeps only the vertices it still uses, every attribute copied byte
for byte (positions, normals, UVs, joints, weights exactly the installed ones); the old LOD and shadow meshes and the mesh's
LOD extras are dropped; materials, variants, images, skin, nodes, sockets and clips are untouched.
Usage: swap_inst.py <installed.glb> <mp.npz> <out.glb>"""
import sys
import numpy as np
import glbpack as G

src, mp, out = sys.argv[1:4]
doc, binary = G.read(src); d = np.load(mp)
node = next(n for n in doc['nodes'] if 'mesh' in n and n.get('name') == 'Nosferatu')
assert node['mesh'] == 0
mesh = doc['meshes'][0]
counts = {}
for p in mesh['primitives']:
    name = doc['materials'][p['material']]['name']
    T = d[name].astype(np.int64)
    if np.array_equal(T.reshape(-1), G.acc(doc, bytes(binary), p['indices']).reshape(-1).astype(np.int64)):
        counts[name] = (len(T), 'unchanged'); continue
    used = np.unique(T); remap = -np.ones(doc['accessors'][p['attributes']['POSITION']]['count'], np.int64)
    remap[used] = np.arange(len(used))
    for sem, i in list(p['attributes'].items()):
        rows = G.raw_rows(doc, binary, i)[used]
        p['attributes'][sem] = G.append(doc, binary, doc['accessors'][i], rows)
        G.set_minmax(doc, binary, p['attributes'][sem])
    idx = remap[T].reshape(-1)
    dt, ct = (np.uint16, 5123) if len(used) < 65536 else (np.uint32, 5125)
    p['indices'] = G.append(doc, binary, {'componentType': ct, 'type': 'SCALAR'}, idx.astype(dt).reshape(-1, 1))
    counts[name] = (len(T), f'{len(used)} vertices')
mesh.pop('extras', None)
doc['meshes'] = [mesh]
doc, binary = G.compact(doc, binary)
G.write(out, doc, binary)
print('SWAPPED', counts, 'total', sum(c[0] for c in counts.values()))
