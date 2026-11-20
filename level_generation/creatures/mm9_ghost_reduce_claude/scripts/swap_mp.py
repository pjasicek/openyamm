#!/usr/bin/env python3
"""runtime_lod0 GLB + work/mp_r<NN>.npz (per primitive triangles into the GLB's own vertices) -> a runtime LOD0 GLB with
those index buffers; each primitive keeps only the vertices it still uses, every attribute copied byte for byte (positions,
normals, UVs, joints, weights exactly the source's). Everything else is unchanged. Usage: swap_mp.py in.glb mp.npz out.glb"""
import sys
import numpy as np
import glbpack as G

src, mp, out = sys.argv[1:4]
doc, binary = G.read(src); d = np.load(mp)
counts = {}
for p in doc['meshes'][doc['nodes'][[i for i, n in enumerate(doc['nodes']) if 'mesh' in n][0]]['mesh']]['primitives']:
    name = doc['materials'][p['material']]['name']
    T = d[name].astype(np.int64)
    used = np.unique(T); remap = -np.ones(doc['accessors'][p['attributes']['POSITION']]['count'], np.int64)
    remap[used] = np.arange(len(used))
    for sem, i in list(p['attributes'].items()):
        rows = G.raw_rows(doc, binary, i)[used]
        p['attributes'][sem] = G.append(doc, binary, doc['accessors'][i], rows)
        G.set_minmax(doc, binary, p['attributes'][sem])
    idx = remap[T].reshape(-1)
    dt, ct = (np.uint16, 5123) if len(used) < 65536 else (np.uint32, 5125)
    p['indices'] = G.append(doc, binary, {'componentType': ct, 'type': 'SCALAR'}, idx.astype(dt).reshape(-1, 1))
    counts[name] = len(T)
doc, binary = G.compact(doc, binary)
G.write(out, doc, binary)
print('SWAPPED', counts, 'total', sum(counts.values()))
