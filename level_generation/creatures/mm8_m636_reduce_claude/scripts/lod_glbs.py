#!/usr/bin/env python3
"""One GLB per LOD of a school GLB (the School node pointed at LOD k's mesh), for renders of the lower LODs:
work/lodview/<label>_lod<k>.glb. Usage: lod_glbs.py <glb> <label>"""
import copy, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
d, b = read_glb(Path(sys.argv[1])); node = next(n for n in d['nodes'] if n.get('name') == 'School')
out = HERE / 'work' / 'lodview'; out.mkdir(exist_ok=True)
for k, m in enumerate([node['mesh']] + d['meshes'][node['mesh']]['extras']['openyamm_lods']):
    e = copy.deepcopy(d); next(n for n in e['nodes'] if n.get('name') == 'School')['mesh'] = m
    write_glb(out / f'{sys.argv[2]}_lod{k}.glb', e, b)
