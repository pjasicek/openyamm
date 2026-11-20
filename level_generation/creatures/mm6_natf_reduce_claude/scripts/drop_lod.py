#!/usr/bin/env python3
"""Drop one level from a static prop's LOD chain (natf blade/shield: the kept LOD2 was no longer under the gate's
0.28 ratio of the reduced LOD0; LOD3 takes its place). The mesh leaves the document; run prune_materials.py after.
Usage: drop_lod.py <in.glb> <out.glb> <level, 1-based>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

src, out, level = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
doc, binary = read_glb(src)
root = next(n for n in doc['nodes'] if 'mesh' in n)
lods = doc['meshes'][root['mesh']]['extras']['openyamm_lods']
gone = lods.pop(level - 1)
remap = lambda i: i - (i > gone)
del doc['meshes'][gone]
for n in doc['nodes']:
    if 'mesh' in n:
        n['mesh'] = remap(n['mesh'])
for m in doc['meshes']:
    ex = m.get('extras', {})
    for key in ('openyamm_lods', 'openyamm_shadow_lods'):
        if key in ex:
            ex[key] = [remap(i) for i in ex[key]]
write_glb(out, doc, binary)
print('DROPPED LOD', level, 'chain', doc['meshes'][remap(root['mesh'])]['extras']['openyamm_lods'])
