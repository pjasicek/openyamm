#!/usr/bin/env python3
"""Ladder source without the vest/strap/hip-strip linings: the installed Skel primitive ends with 575 lining faces,
exact reversed copies of the outer sheet faces with every UV on one dark texel (finish_skel.py). The weld in
import_source.py would merge each pair into one face. The linings are dropped here (only LOD0's Skel primitive; unused
vertices compacted) and rebuilt from the reduced outer sheets after the swap (add_lining.py).
Usage: strip_lining.py <installed.glb> <lining.npy (per Skel face)> <out.glb>"""
import struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
src, linf, out = Path(sys.argv[1]), np.load(sys.argv[2]), Path(sys.argv[3])
doc, binary = read_glb(src); binary = bytearray(binary)
prim = doc['meshes'][0]['primitives'][0]
assert doc['materials'][prim['material']]['name'] == 'Skel_A'
ia = doc['accessors'][prim['indices']]
idx = np.frombuffer(accessor_bytes(doc, binary, prim['indices']), {5125: np.uint32, 5123: np.uint16}[ia['componentType']]).reshape(-1, 3)
assert len(idx) == len(linf)
keep = idx[~linf]; used = np.unique(keep); remap = -np.ones(int(idx.max()) + 1, np.int64); remap[used] = np.arange(len(used))
attrs = {}
for sem, ai in prim['attributes'].items():
    acc = doc['accessors'][ai]; raw = accessor_bytes(doc, binary, ai); sz = len(raw) // acc['count']
    packed = b''.join(raw[i * sz:(i + 1) * sz] for i in used.tolist())
    a2 = dict(acc, count=len(used))
    if 'min' in acc and acc['type'] == 'VEC3' and acc['componentType'] == 5126:
        v = np.frombuffer(packed, np.float32).reshape(-1, 3); a2['min'] = v.min(0).tolist(); a2['max'] = v.max(0).tolist()
    attrs[sem] = append_accessor(doc, binary, a2, packed)
prim['attributes'] = attrs
newidx = remap[keep].astype(np.uint32)
prim['indices'] = append_accessor(doc, binary, dict(ia, count=newidx.size, componentType=5125), newidx.tobytes())
write_glb(out, doc, bytes(binary))
print('STRIPPED', int(linf.sum()), 'lining faces; Skel', len(keep), 'faces', len(used), 'vertices')
