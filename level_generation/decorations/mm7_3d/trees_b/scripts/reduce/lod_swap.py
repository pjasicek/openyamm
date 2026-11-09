#!/usr/bin/env python3
"""Swap a reduced coarser level (deco_build.py's <name>_lod0.glb, built from lod_extract.py's standalone level) into
level N of a linked static GLB: each opaque primitive of that level's mesh takes the reduced geometry of its material
(matched by name); alpha-mask primitives (twig cards) stay byte-for-byte. Prints the LOD chain, which must still fall.
Usage: lod_swap.py <source.glb> <level 1..> <reduced.glb> <out.glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[6] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
src, level, new, out = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
doc, binary = read_glb(src); binary = bytearray(binary)
exp, payload = read_glb(new)
node = next(n for n in doc['nodes'] if 'mesh' in n)
lods = doc['meshes'][node['mesh']]['extras']['openyamm_lods']
mesh = doc['meshes'][lods[level - 1]]
enode = next(n for n in exp['nodes'] if 'mesh' in n)
eprims = {}
for p in exp['meshes'][enode['mesh']]['primitives']:
    eprims.setdefault(exp['materials'][p['material']]['name'], []).append(p)
for prim in mesh['primitives']:
    m = doc['materials'][prim['material']]
    if m.get('alphaMode', 'OPAQUE') != 'OPAQUE':
        continue
    (e,) = eprims[m['name']]
    prim['attributes'] = {sem: append_accessor(doc, binary, exp['accessors'][idx], accessor_bytes(exp, payload, idx))
                          for sem, idx in e['attributes'].items() if sem in prim['attributes']}
    prim['indices'] = append_accessor(doc, binary, exp['accessors'][e['indices']], accessor_bytes(exp, payload, e['indices']))
tris = lambda m: sum(doc['accessors'][p['indices']]['count'] // 3 for p in m['primitives'])
chain = [tris(doc['meshes'][node['mesh']])] + [tris(doc['meshes'][i]) for i in lods]
assert all(a > b for a, b in zip(chain, chain[1:])), chain
write_glb(out, doc, bytes(binary))
print('SWAPPED level', level, 'LOD chain', chain)
