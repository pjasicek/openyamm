#!/usr/bin/env python3
"""tools/build_actor_lods.py writes LOD and shadow primitives with only their default material. Copy each LOD0
primitive's KHR_materials_variants mapping to the LOD/shadow primitives with the same default material, as the
installed model had (distant demons otherwise lose their variant body/iris). The builder matches materials by name and
picks the last one: the Pirate Mage's six materials repeat the names PirateMage_A/B/C (Wimpy tiers), so its LOD
primitives pointed at material 3; a LOD primitive whose material has the LOD0 material's name takes LOD0's index.
Usage: carry_variants.py <glb> (in place)"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
path = Path(sys.argv[1]); doc, binary = read_glb(path)
for mesh in doc['meshes']:
    extras = mesh.get('extras', {})
    if 'openyamm_lods' not in extras:
        continue
    mapping = {p['material']: p['extensions'] for p in mesh['primitives'] if 'extensions' in p}
    carried = 0
    for index in extras['openyamm_lods'] + extras['openyamm_shadow_lods']:
        for p in doc['meshes'][index]['primitives']:
            names = {doc['materials'][m]['name']: m for m in mapping}
            p['material'] = names.get(doc['materials'][p['material']]['name'], p['material'])
            if p['material'] in mapping:
                p['extensions'] = copy.deepcopy(mapping[p['material']]); carried += 1
    print('CARRIED', mesh['name'], carried, 'primitives')
write_glb(path, doc, binary)
