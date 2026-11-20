#!/usr/bin/env python3
"""One GLB per colour LOD (the LOD's mesh on the mesh node) for renders: work/lodcheck_<label>_<level>.glb.
Usage: split_lods.py <glb> <label> <mesh node>"""
import copy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
D, B = read_glb(Path(sys.argv[1])); label, name = sys.argv[2], sys.argv[3]
node = next(n for n in D['nodes'] if n.get('name') == name)
for level, index in enumerate([node['mesh']] + D['meshes'][node['mesh']]['extras']['openyamm_lods']):
    d = copy.deepcopy(D); next(n for n in d['nodes'] if n.get('name') == name)['mesh'] = index
    write_glb(P / 'work' / f'lodcheck_{label}_{level}.glb', d, B)
