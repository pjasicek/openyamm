"""Refresh tier colour ramps while preserving the reviewed mesh and motion byte for byte."""
import copy
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb

path = PROJECT / 'export/hes_hound.glb'
config = json.loads((PROJECT / 'textures/hound_ramps.json').read_text())
ramps = config['materials'][0]['ramps']
doc, binary = read_glb(path)
before = copy.deepcopy(doc)
changed = []
for tier in 'ABC':
    for suffix in ['', '_LOD2', '_LOD3']:
        name = 'HoundHide_' + tier + suffix
        material = next(m for m in doc['materials'] if m['name'] == name)
        material['extras']['openyamm_region_ramps'] = ramps['hound_' + tier.lower()]
        changed.append(name)
expected = copy.deepcopy(doc)
for material, old in zip(expected['materials'], before['materials']):
    if material['name'] in changed:
        material['extras']['openyamm_region_ramps'] = old['extras']['openyamm_region_ramps']
assert expected == before, 'Only region ramps may change'
write_glb(path, doc, binary)
after, result = read_glb(path)
assert after == doc and result == binary, 'Round-trip changed data'
print('Updated nine tier/LOD materials; geometry, textures and all nine clips unchanged')
