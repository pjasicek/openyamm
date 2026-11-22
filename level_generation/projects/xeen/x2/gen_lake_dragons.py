#!/usr/bin/env python3
"""A5 (2026-11-21, D-54): X2's playtest_lake_dragons.yml. The three Water Dragons (11640, group 80) are leashed on
Lake Darzog away from X9's fall landing:
  1. a level-46 party at entrance:x9_fall (-15360, 3072, 768): nobody hurt in 30 s;
  2. after 60 s each dragon within its leash + 256 of its home;
  3. group 80 killed (damage_actor): `lake_beasts_slain` (qbit 110201) set by the map's evt:lake_beasts, and Medin's
     boat (event 141) rows the party to the island landing (-14848, 1792).
And playtest_lake_dragons_leash.yml, the leash itself (A1's repro, 2026-11-21: fails on merge point 22): the party on
the north shore 2,816 from the north-west dragon's home (inside its sight, outside its leash), immortal, 30 s: each
dragon still within its leash + 256 of home.
The dragons' actor indices (44-46) are the build's scene order, checked by monster id first."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
sys.argv = sys.argv[:1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402

L4 = R / 'devdocs/xeen/briefs/x2/L4'
LOCK = yaml.safe_load(open(L4 / 'ids.lock.yml'))
EV = dict(LOCK.get('events', {}))
DRAGON = 11640
INDICES = [44, 45, 46]
LAKE_BEASTS = 110201
LANDING = (-15360, 3072, 768)
ISLAND_LANDING = (-14848, 1792)
SHORE = (23, 42.5)          # land north of the north-west lobe, 5.5 cells (2,816) from the dragon at [23, 48]


def units(c):
    return int((c[0] - 64) * 512), int((64 - c[1]) * 512)


def party(level=46):
    return {'gold': 0, 'food': 20, 'members': [
        {'name': 'Brokk', 'class': 'Knight', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Hild', 'class': 'Cleric', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Ivar', 'class': 'Archer', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Sefa', 'class': 'Sorcerer', 'level': level, 'skills': [], 'equipment': {}}]}


def pose(x, y, z, yaw=0):
    return {'set_pose': {'map': 'xeen_x2.odm', 'x': x, 'y': y, 'z': z, 'yaw_degrees': yaw, 'pitch': 0}}


def dragons_home(label):
    s = [{'note': f'{label}: each Water Dragon within its leash + 256 of its home (D-54)'}]
    for (cell, leash) in gen.LAKE_DRAGONS:
        x, y = units(cell)
        s.append({'assert': {'actor_count': {'monster_id': DRAGON, 'near': [x, y, leash + 256], 'min': 1, 'max': 1}}})
    return s


def start():
    s = [{'new_game_flow': {'start_map': 'xeen_x2.odm', 'party': party()}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'note': "The three lake dragons are the build's actors 44-46"}]
    return s + [{'assert': {'actor_visible': {'actor_index': i, 'monster_id': DRAGON, 'dead': False}}} for i in INDICES]


def leash():
    sx, sy = units(SHORE)
    s = start()
    s += [{'note': "On the north shore 2,816 from the north-west dragon's home, outside its leash (immortal)"},
          {'setup_shortcut': {'kind': 'immortal', 'value': True}},
          pose(sx, sy, 1400, 270)]
    for k in range(6):
        s += [{'advance_runtime': {'seconds': 5.0}}]
        s += [{'assert': {'actor_visible': {'actor_index': i, 'report_state': True}}} for i in INDICES]
    s += dragons_home('With the party on the shore 30 s')
    return {'id': 'xeen.x2.l4.lake_dragons_leash',
            'title': "X2 Lake Darzog: a Water Dragon that sees the party from its home stays within its leash (D-54)",
            'world': 'xeen', 'mode': 'faithful', 'steps': s}


def scenario():
    boat = EV['evt:thing:medin_boat']
    s = start()
    s += [{'note': "X9's fall landing (entrance:x9_fall): a level-46 party stands there 30 s and nobody is hurt"},
          pose(*LANDING),
          {'advance_runtime': {'seconds': 30.0}},
          {'assert': {'party_position': {'x': LANDING[0], 'y': LANDING[1], 'radius': 256}}},
          {'assert': {'party_health': {'full': True}}},
          {'advance_runtime': {'seconds': 30.0}},
          {'assert': {'party_health': {'full': True}}}]
    s += dragons_home('After 60 s')
    s += [{'note': "Group 80 killed: evt:lake_beasts sets lake_beasts_slain (110201)"}]
    s += [{'damage_actor': {'actor_index': i, 'amount': 100000}} for i in INDICES]
    s += [{'advance_runtime': {'seconds': 3.0}},
          {'assert': {'actor_count': {'monster_id': DRAGON, 'max': 0}}},
          {'assert': {'qbit_set': [LAKE_BEASTS]}},
          {'play_lua': {'source': 'wait(0.5); close()'}},
          {'note': "Medin's boat runs: the party is rowed to the island"},
          pose(-9779, 1536, 700, 180),
          {'advance_runtime': {'seconds': 0.5}},
          {'execute_event': {'id': boat}},
          {'advance_runtime': {'seconds': 1.5}},
          {'assert': {'map': 'xeen_x2.odm'}},
          {'assert': {'party_position': {'x': ISLAND_LANDING[0], 'y': ISLAND_LANDING[1], 'radius': 256}}}]
    return {'id': 'xeen.x2.l4.lake_dragons',
            'title': "X2 Lake Darzog: the leashed Water Dragons stay home, X9's fall landing is safe, and killing them "
                     "frees Medin's boat (D-54)",
            'world': 'xeen', 'mode': 'faithful', 'steps': s}


head = ("# Lake Darzog's three Water Dragons (D-54; written by output/studio_cal/x2/tools/gen_lake_dragons.py):\n"
        "# leashed at home, X9's fall landing unhurt, then killed for Medin's boat (Q-C13).\n")
(L4 / 'playtest_lake_dragons.yml').write_text(head + yaml.safe_dump(scenario(), sort_keys=False, width=120))
head = ("# Lake Darzog's north-west Water Dragon sees the party on the shore and must stay within its leash (D-54;\n"
        "# written by output/studio_cal/x2/tools/gen_lake_dragons.py). A1's repro: fails on merge point 22.\n")
(L4 / 'playtest_lake_dragons_leash.yml').write_text(head + yaml.safe_dump(leash(), sort_keys=False, width=120))
print('wrote', L4 / 'playtest_lake_dragons.yml', L4 / 'playtest_lake_dragons_leash.yml')
