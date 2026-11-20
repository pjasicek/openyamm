#!/usr/bin/env python3
"""Embed burn maps (claude_shared/burn_maps.py) on the base materials, then point every KHR_materials_variants
material at its base material's map (the engine burns the variant's materials; one image each, shared).
Usage: embed_burn.py <in.glb> <out.glb> MATERIAL=map.png [...]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from burn_maps import add_burn_maps  # noqa: E402
from region_variants import read_glb, write_glb  # noqa: E402
source, destination = Path(sys.argv[1]), Path(sys.argv[2])
add_burn_maps(source, destination, dict(arg.split('=', 1) for arg in sys.argv[3:]))
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
