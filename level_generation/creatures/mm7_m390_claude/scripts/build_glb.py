"""export/mm7_m390.glb: the installed MM8 Thunderbird (reduced, LODs, shadows, clips) with MM7 Roc variants.

Only glTF JSON changes: variant names m390_a/b/c, material names Roc_A/B/C and their region ramps from
textures/m390_ramps.json. Geometry, skin, clips and every image stay byte-identical to the MM8 source.
"""
import hashlib
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402

SOURCE = REPO / 'assets_source/worlds/mm8/models/mm8_m552.glb'
config = json.loads((P / 'textures/m390_ramps.json').read_text())
doc, binary = RV.read_glb(SOURCE)
names = [variant['name'] for variant in doc['extensions']['KHR_materials_variants']['variants']]
assert names == ['m552_a', 'm552_b', 'm552_c'], names
doc['extensions']['KHR_materials_variants']['variants'] = [{'name': name} for name in config['variants']]
ramps = config['materials'][0]['ramps']
for material in doc['materials']:
    tier = material['name'].split('_')[-1].lower()
    assert material['name'].startswith('Thunderbird_') and tier in 'abc', material['name']
    material['name'] = f'Roc_{tier.upper()}'
    material['extras']['openyamm_region_ramps'] = ramps[f'm390_{tier}']
out = P / 'export/mm7_m390.glb'
RV.write_glb(out, doc, binary)
print(out, hashlib.sha256(out.read_bytes()).hexdigest(), 'source', hashlib.sha256(SOURCE.read_bytes()).hexdigest())
