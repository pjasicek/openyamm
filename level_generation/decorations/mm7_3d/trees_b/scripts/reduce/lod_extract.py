#!/usr/bin/env python3
"""Write one LOD level of a linked static GLB as a standalone single-node GLB (the node takes that level's mesh, no
openyamm_lods), so the mm6_reduce_pilot route (deco_dump / deco_ladder / deco_build) can reduce a coarser level.
Usage: lod_extract.py <in.glb> <level 1..> <out.glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[6] / 'tools'))
from link_static_model_lods import read_glb, write_glb  # noqa: E402
src, level, out = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
doc, binary = read_glb(src)
doc = copy.deepcopy(doc)
node = next(n for n in doc['nodes'] if 'mesh' in n)
mesh = doc['meshes'][node['mesh']]
node['mesh'] = mesh['extras']['openyamm_lods'][level - 1]
doc['meshes'][node['mesh']].pop('extras', None)
write_glb(out, doc, binary)
print('EXTRACTED', src.name, 'level', level, '->', out)
