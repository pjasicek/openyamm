"""Author the pickups test room (hes_pickups_test.blv) in Blender, with the Hesper indoor kit (hesper_stage/blv_kit.py):
one lit colony room holding a stim canister, a serum vat, three colony satchels and a scrap bundle for the pickups
scenario (pickups.yml). It has no entrance: only the scenario loads it.

Run headless:  blender --background --factory-startup --python author_pickups_test_blender.py
Writes source/hes_pickups_test.glb, .geometry.yml, .semantic.json and .blend.
"""
import os
import sys
from pathlib import Path

ROOT = Path('/home/pjasicek/github/OpenYAMM')
sys.path.insert(0, str(ROOT / 'level_generation/projects/hesper_stage'))
import blv_kit  # noqa: E402

PROJECT = ROOT / 'level_generation/projects/hesper_pickups_test'
ROLE = {'wall': 'hcpanel', 'trim': 'hctrim', 'strip': 'hcstripd', 'floor': 'hcfloor', 'ceiling': 'hcceiling',
        'marker': 'hcconsole'}
# Each pickup: (decoration, event and cog, x, y); the ids are the shared Lua's (hesper_stage/common/pickups.lua).
PICKUPS = [('hes_stim_canister', 701, 300, 700), ('hes_serum_vat', 702, 600, 700),
           ('hes_colony_satchel', 751, 900, 700), ('hes_colony_satchel', 752, 1100, 700),
           ('hes_colony_satchel', 753, 1300, 700), ('hes_scrap_bundle', 754, 1300, 300)]

b = blv_kit.Builder('hes_pickups_test.blv', ROLE, PROJECT / 'source', role_scale={'wall': 1.5, 'floor': 1.5})
b.box_room('room', 0, 0, 1536, 1024, 0, 384, [(0, 16, 'trim'), (16, 352, 'wall'), (352, 384, 'strip')], ambient=8)
for name, event, x, y in PICKUPS:
    b.decoration(name, x, y, 0, facing=270, event=event, cog=event)
b.light('room_a', 500, 500, 320, 900, (225, 235, 255))
b.light('room_b', 1100, 500, 320, 900, (225, 235, 255))
b.export({'arrivals': {'start': {'position': [768, 160, 0], 'direction_degrees': 90}}, 'door_ids': {}})
os._exit(0)
