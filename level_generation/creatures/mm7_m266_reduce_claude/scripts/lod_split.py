#!/usr/bin/env python3
"""Per-LOD GLBs of a runtime GLB (the mesh node pointed at each colour LOD), for lod_views.py without lod_check.py's
clip sweep. Usage: lod_split.py <glb> <label>  -> work/lodcheck_<label>_<level>.glb"""
import copy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
D, B = read_glb(Path(sys.argv[1])); node = next(n for n in D['nodes'] if n.get('name') == 'M266')
for level, index in enumerate([node['mesh']] + D['meshes'][node['mesh']]['extras']['openyamm_lods']):
    d = copy.deepcopy(D); next(n for n in d['nodes'] if n.get('name') == 'M266')['mesh'] = index
    write_glb(P / 'work' / f'lodcheck_{sys.argv[2]}_{level}.glb', d, B)
print('SPLIT', sys.argv[2])
