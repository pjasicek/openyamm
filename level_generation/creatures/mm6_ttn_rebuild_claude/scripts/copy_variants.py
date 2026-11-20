#!/usr/bin/env python3
"""Give every LOD primitive (colour and shadow) of the body the LOD0 primitive's KHR_materials_variants mappings
(build_actor_lods.py drops them; region_variants.py set them on the installed model). Usage: copy_variants.py in out"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb
doc, binary = read_glb(Path(sys.argv[1]))
m0 = doc['meshes'][0]; ext = m0['primitives'][0]['extensions']['KHR_materials_variants']
lods = m0['extras'].get('openyamm_lods', []) + m0['extras'].get('openyamm_shadow_lods', [])
for i in lods:
    for p in doc['meshes'][i]['primitives']:
        assert p['material'] == m0['primitives'][0]['material']
        p.setdefault('extensions', {})['KHR_materials_variants'] = copy.deepcopy(ext)
write_glb(Path(sys.argv[2]), doc, bytearray(binary)); print('VARIANTS', len(lods), 'meshes')
