#!/usr/bin/env python3
"""Embed the demon's burn maps (claude_shared/burn_maps.py) on the base materials, then point every variant material
at its base material's map (the engine burns the variant's materials; one image each, shared by the variants).
Usage: embed_burn.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from burn_maps import add_burn_maps  # noqa: E402
from region_variants import read_glb, write_glb  # noqa: E402
source, destination = Path(sys.argv[1]), Path(sys.argv[2])
T = HERE / 'textures'
add_burn_maps(source, destination, {'Demon_Body_A': T / 'demon_body_burn.png', 'Demon_Iris': T / 'demon_iris_burn.png',
                                    'Demon_Black_Pupil': T / 'demon_pupil_burn.png',
                                    'Demon_White_Claws': T / 'demon_claws_burn.png'})
doc, binary = read_glb(destination)
shared = 0
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        base = doc['materials'][p['material']].get('extras', {}).get('openyamm_burn_map')
        for x in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
            if base and x['material'] != p['material']:
                doc['materials'][x['material']].setdefault('extras', {})['openyamm_burn_map'] = dict(base); shared += 1
missing = [m['name'] for m in doc['materials'] if 'openyamm_burn_map' not in m.get('extras', {})]
assert not missing, missing
write_glb(destination, doc, binary)
print('BURN MAPS on', len(doc['materials']), 'materials,', shared, 'variant links')
