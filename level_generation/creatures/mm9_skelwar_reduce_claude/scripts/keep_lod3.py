#!/usr/bin/env python3
"""Put the installed LOD3 and LOD3 shadow back (in place): every rebuild of LOD3 from the reduced LOD0 lost the thighs and
forearms (tools/build_actor_lods.py at 0.06 and 0.075: the reduced limbs have few faces left, and the collapse removed whole
pieces), while the installed 578-triangle LOD3 keeps them at the same count. Same skeleton, skin, UVs and materials, so the
installed LOD3 is valid as it is; its primitives (with their variant mappings) are copied over by mesh name.
Usage: keep_lod3.py <installed.glb> <glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
A, ab = read_glb(src); B, bb = read_glb(dst); bb = bytearray(bb)
mi = {m['name']: m for m in B['meshes']}
for name in ('SkelWar_LOD3', 'SkelWar_LOD3_Shadow'):
    ma = next(m for m in A['meshes'] if m['name'] == name); mb = mi[name]
    prims = []
    for p in ma['primitives']:
        q = copy.deepcopy(p)
        q['attributes'] = {s: append_accessor(B, bb, A['accessors'][i], accessor_bytes(A, ab, i)) for s, i in p['attributes'].items()}
        q['indices'] = append_accessor(B, bb, A['accessors'][p['indices']], accessor_bytes(A, ab, p['indices']))
        assert A['materials'][p['material']]['name'] == B['materials'][p['material']]['name']
        prims.append(q)
    old = sum(B['accessors'][p['indices']]['count'] // 3 for p in mb['primitives'])
    mb['primitives'] = prims
    print('KEPT', name, old, '->', sum(B['accessors'][p['indices']]['count'] // 3 for p in prims))
write_glb(dst, B, bytes(bb))
