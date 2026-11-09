"""Author the walkability test room (hes_walk_test.blv) in Blender, with the Hesper indoor kit (hesper_stage/blv_kit.py):
one lit hall with a raised platform along its north wall, 96 above the floor (a sheer edge no walker climbs), and a
ramp up to it at the east end. Engine checks of monster movement (walk_test.yml): a monster below the edge pursuing a
party on the platform must take the ramp. It has no entrance: only its scenario loads it.

Run headless:  blender --background --factory-startup --python author_walk_test_blender.py
Writes source/hes_walk_test.glb, .geometry.yml, .semantic.json and .blend.
"""
import os
import sys
from pathlib import Path

ROOT = Path('/home/pjasicek/github/OpenYAMM')
sys.path.insert(0, str(ROOT / 'level_generation/projects/hesper_stage'))
import blv_kit  # noqa: E402

PROJECT = ROOT / 'level_generation/projects/hesper_walk_test'
ROLE = {'wall': 'hcpanel', 'trim': 'hctrim', 'strip': 'hcstripd', 'floor': 'hcfloor', 'ceiling': 'hcceiling',
        'marker': 'hcconsole'}
# The platform: the hall's north part from PLATFORM_Y, PLATFORM_Z high; the ramp rises north to it at the east end.
PLATFORM_Y = 1300
PLATFORM_Z = 96
RAMP_X = 2560

b = blv_kit.Builder('hes_walk_test.blv', ROLE, PROJECT / 'source', role_scale={'wall': 1.5, 'floor': 1.5})
hall = b.box_room('hall', 0, 0, 3072, 2048, 0, 512, [(0, 16, 'trim'), (16, 480, 'wall'), (480, 512, 'strip')],
                  ambient=8)
# The floor stops at the ramp and the platform (a floor running on under them lets a walker in underneath).
floor = blv_kit.floor(0, 0, 3072, 2048, 0, 'floor')
hall[:] = [panel for panel in hall if panel not in floor]
hall += blv_kit.floor(0, 0, 3072, 500, 0, 'floor') + blv_kit.floor(0, 500, RAMP_X, PLATFORM_Y, 0, 'floor')
b.surface('platform', 'hall', blv_kit.box((0, PLATFORM_Y, 0), (3072, 2048, PLATFORM_Z), 'trim', top='floor',
                                          skip=('north', 'west', 'east')))
b.surface('ramp', 'hall', blv_kit.ramp(RAMP_X, 500, 3072, PLATFORM_Y, 0, PLATFORM_Z, 'north', skirt='trim'))
b.light('hall_a', 800, 1000, 448, 1400, (225, 235, 255))
b.light('hall_b', 2300, 1000, 448, 1400, (225, 235, 255))
b.export({'arrivals': {'start': {'position': [1000, 1700, PLATFORM_Z], 'direction_degrees': 270}}, 'door_ids': {}})
os._exit(0)
