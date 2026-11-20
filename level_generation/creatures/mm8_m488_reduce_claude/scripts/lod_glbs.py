#!/usr/bin/env python3
"""Per-LOD review copies: the creature GLB with the Minotaur node pointing at colour LOD n (and the LOD extras
dropped) -> work/<label>_lod<n>.glb, for glb_close.py and hidden_skin.py. Usage: lod_glbs.py <glb> <label>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
D, B = read_glb(Path(sys.argv[1])); node = next(n for n in D['nodes'] if n.get('name') == 'Minotaur')
for n, index in enumerate([node['mesh']] + D['meshes'][node['mesh']]['extras']['openyamm_lods']):
    d = copy.deepcopy(D); nd = next(x for x in d['nodes'] if x.get('name') == 'Minotaur'); nd['mesh'] = index
    d['meshes'][index].pop('extras', None)
    write_glb(Path(__file__).resolve().parents[1] / 'work' / f'{sys.argv[2]}_lod{n}.glb', d, B)
print('LOD GLBS', sys.argv[2])
