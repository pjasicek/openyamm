"""Write the Brood Spires' headless scenarios (BROOD_SPIRES.md BUILD-READY, Verification) from the built map's record
(out3_build.json: actor indices, arrivals, the door poses), so they follow every rebuild:

    brood_round_trips.yml  both edges and back; each dungeon door and back to its outdoor arrival
    brood_acid_rain.yml    a rainy hour: a character without a sealed helm burns (100503, autonote 10201), one with
                           the Rebreather Helm (11106) does not
    brood_nest.yml         the S10 nest killed: 100510 set (Hesk's topic then closes S10: 100110, Wren teaches)
    brood_turrets.yml      kite roost clearance bits 100501/100502 persist after reload
    brood_tablets.yml      the three plinths give 11366-11368 once each

    python3 level_generation/projects/hesper_out3/make_scenarios.py

Run them from output/hesper_stage/scenario_run (its settings.ini mounts the stage), under the shared engine lock:
    flock -s ../locks/engine_build.lock ../../../build/game/openyamm --world hesper --headless-run-scenario \\
        ../../../level_generation/projects/hesper_out3/<scenario>.yml --scenario-no-color
"""
import json
import math
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
record = json.loads((PROJECT / 'out3_build.json').read_text())
arrivals = record['arrivals']
groups = record['actor_groups']
CONFIRM = {'kind': 'map_transition_confirm', 'source_id': 0, 'action_id': 0, 'secondary_id': 0, 'selection_index': 0,
           'house_dialog': False, 'enabled': True, 'label': 'OK'}
# Where a scenario stands to click each dungeon door (in front of its face, facing it) and where each dungeon's own
# exit is (their scenarios' poses: hesper_d05/relay_spire_climb.yml, hesper_d09's exit face at x 8 400, y 1 800,
# hesper_d11/seedship_sabotage.yml).
D5_DOOR = (-11480 + 240, -12384, math.pi)
D9_DOOR = (-8986 - 177 + 170, 6970 + 177 - 170, 3 * math.pi / 4)   # the mouth is set 250 into the wall
D11_DOOR = (arrivals['d11_breach']['position'][0], arrivals['d11_breach']['position'][1],
            math.radians(arrivals['d11_breach']['direction_degrees'] + 180))
DUNGEON_EXITS = {'hes_d05.blv': (5600, 3200, 0, 0.0), 'hes_d09.blv': (8200, 1800, 0, 0.0),
                 'hes_d11.blv': (250, 2800, 0, math.pi)}


def write(name, comment, steps, mode='faithful'):
    text = ''.join(f'# {line}\n' if line else '#\n' for line in comment.strip().split('\n'))
    text += yaml.safe_dump({'id': f'hesper.out3.{name}', 'world': 'hesper', 'mode': mode, 'steps': steps},
                           sort_keys=False, width=120)
    (PROJECT / f'{name}.yml').write_text(text)


def pose(map_file, x, y, z, yaw):
    return {'set_pose': {'map': map_file, 'x': round(x), 'y': round(y), 'z': round(z), 'yaw': round(yaw, 4),
                         'pitch': 0}}


def arrived(map_file, xyz):
    return {'assert': {'map': map_file, 'map_arrived': {'map': map_file, 'pos': '(%d,%d,%d)' % tuple(xyz)}}}


start = {'new_game_flow': {'start_map': 'hes_out3.odm'}}
steps = [start, {'assert': {'map': 'hes_out3.odm'}},
         {'note': {'text': 'Spinefall Pass: south to Starport Reach, arriving at (288, 22 540) facing south, and back.'}},
         {'setup_shortcut': {'kind': 'map_transition_prompt', 'source_id': 1}},
         {'select_topic': CONFIRM},
         arrived('hes_out1.odm', (288, 22540, 1120)),
         {'setup_shortcut': {'kind': 'map_transition_prompt', 'source_id': 0}},
         {'select_topic': CONFIRM},
         arrived('hes_out3.odm', arrivals['south_edge']['position']),
         {'note': {'text': 'The Crown road: east to the Crown (-21 800, 8 640), and back to (21 800, 8 640).'}},
         {'setup_shortcut': {'kind': 'map_transition_prompt', 'source_id': 2}},
         {'select_topic': CONFIRM},
         {'assert': {'map': 'hes_out4.odm'}},
         {'setup_shortcut': {'kind': 'map_transition_prompt', 'source_id': 3}},
         {'select_topic': CONFIRM},
         arrived('hes_out3.odm', arrivals['east_edge']['position'])]
for label, door, dungeon, arrival in (('D5 Relay Spire', D5_DOOR, 'hes_d05.blv', 'd05_root_door'),
                                      ('D9 Brood Pits', D9_DOOR, 'hes_d09.blv', 'd09_mouth'),
                                      ('D11 the Seedship', D11_DOOR, 'hes_d11.blv', 'd11_breach')):
    x, y, yaw = door
    ex, ey, ez, eyaw = DUNGEON_EXITS[dungeon]
    steps += [{'note': {'text': f'{label}: its door here, then its own exit back to the arrival "{arrival}".'}},
              pose('hes_out3.odm', x, y, record['arrivals'][arrival]['position'][2], yaw),
              {'press_interact': {}},
              {'assert': {'map': dungeon}},
              pose(dungeon, ex, ey, ez, eyaw),
              {'press_interact': {}},
              {'select_topic': CONFIRM},                     # leaving a dungeon asks, as every indoor exit does
              arrived('hes_out3.odm', arrivals[arrival]['position'])]
write('brood_round_trips', """
The Brood Spires' round trips (BROOD_SPIRES.md BUILD-READY 7): both edges (map_navigation from the stage's edges.yml)
and each dungeon door and back to its outdoor arrival (out3_build.json `arrivals`, which the dungeons' builds read).
""", steps)

# The former turret regression file now checks both kite-roost groups and their saved clearance bits.
roosts = groups['1'] + groups['2']
steps = [start, {'assert': {'qbit_clear': [100501, 100502]}}]
steps += [{'damage_actor': {'actor_index': i, 'amount': 100000}} for i in roosts]
steps += [{'advance_runtime': {'seconds': 3}}]
steps += [{'assert': {'actor_visible': {'actor_index': i, 'dead': True, 'report_state': True}}} for i in roosts]
steps += [{'load_map': {'map': 'hes_out3.odm'}},
          {'assert': {'qbit_set': [100501], 'qbit_clear': [100502]}}]
steps += [{'assert': {'actor_visible': {'actor_index': i, 'dead': True}}} for i in roosts]
steps += [{'damage_actor': {'actor_index': i, 'amount': 100000}} for i in groups['4'] + groups['5']]
steps += [{'advance_runtime': {'seconds': 3}}, {'load_map': {'map': 'hes_out3.odm'}},
          {'assert': {'qbit_set': [100501, 100502]}}]
write('brood_turrets', """
Kite roosts replacing the pass and Crown-road turrets: both clearance bits persist after reload.
The historical scenario filename remains registered in the shared regression queue; no turret shields or autonote.
""", steps)

# The nest: kill group 11 (the Matron and her seven Brood Crawlers): 100510; Hesk then closes S10.
nest = groups['11']
steps = [start, {'assert': {'qbit_clear': [100510, 100110]}},
         {'speak_npc': {'source_id': 9510}}, {'select_topic': {'kind': 'npc_topic', 'action_id': 9726}},
         {'assert': {'qbit_set': [100230]}}, {'press_action': {'action': 'cancel_dialog'}}]
steps += [{'damage_actor': {'actor_index': i, 'amount': 100000}} for i in nest]
steps += [{'advance_runtime': {'seconds': 0.5}}]
steps += [{'advance_runtime': {'seconds': 3}}, {'load_map': {'map': 'hes_out3.odm'}},
          {'assert': {'qbit_set': [100510]}},
          {'speak_npc': {'source_id': 9510}}, {'select_topic': {'kind': 'npc_topic', 'action_id': 9726}},
          {'assert': {'qbit_set': [100110], 'qbit_clear': [100230]}}, {'press_action': {'action': 'cancel_dialog'}}]
write('brood_nest', """
S10's nest (BROOD_SPIRES.md section 7, events 5, 150; P4's Hesk 9726): Hesk gives S10 (100230); the Matron and her
brood killed, the nest is quiet (100510; the mounds go dark: checked in the game, a decoration swap); Hesk closes S10
(100110, 100230 cleared).
""", steps)

# The tablets (events 13-15): each gives its tablet once (map variables 5-7).
steps = [start, {'load_map': {'map': 'hes_out3.odm'}}]
for k, (cell, item) in enumerate((('A4', 11366), ('F6', 11367), ('C5', 11368))):
    steps += [{'interact_target': {'triggered_event': 13 + k}},
              {'assert': {'inventory_any_member': [{'item_id': item}]}},
              {'interact_target': {'triggered_event': 13 + k}}]
write('brood_tablets', """
The colony log tablets VII-IX (BROOD_SPIRES.md events 13-15; S9): each plinth gives its tablet once (map variables
5-7). Hybrid: the plinths are model decorations, which headless runs cannot click, so the events run directly
(hybrid runs have no event state to read the map variables from: the second click's "empty" is checked in the game).
""", steps, mode='hybrid')

# Collision walks (BUILDER_GUIDE, outdoor extras; BUILD-READY: the gantry): into the farm's west wall (blocked at it),
# in through its gate (open), up the gantry's deck to the hull breach (it carries the party up to the breach's face).
def walk(label, start, yaw, milliseconds, stop, tolerance):
    return [{'note': {'text': label}},
            {'movement_segment': {'input': 'forward', 'duration_ms': milliseconds, 'delta_game_minutes': 0.0,
                                  'start': {'x': start[0], 'y': start[1], 'z': start[2], 'map': 'hes_out3.odm',
                                            'yaw': round(yaw, 4), 'pitch': 0.0},
                                  'expect_stop': {'x': stop[0], 'y': stop[1], 'z': stop[2], 'map': 'hes_out3.odm',
                                                  'yaw': round(yaw, 4), 'pitch': 0.0},
                                  'tolerance_xy': tolerance, 'tolerance_z': 250, 'loose_tolerance': True,
                                  'actor_collision': False, 'actor_ai': False}}]


gate = record['garden']['gate']
breach = record['arrivals']['d11_breach']['position']
steps = [start]
steps += walk('Into the west wall from the marsh: blocked at it', (-5900, -4500, 1000), 0.0, 4000,
              (-5340, -4500, 1000), 220)
steps += walk('In through the gate from the lane: open', (gate[0] + 1300, gate[1], 1260), math.pi, 2500,
              (gate[0] - 600, gate[1], 1250), 450)
foot = record['levels']['gantry_foot']
steps += walk('Up the gantry to the hull breach', (6150, 11383, foot + 10), math.radians(breach_yaw := -14.0), 4000,
              (breach[0] + 180, breach[1] - 45, breach[2] + 60), 400)
write('brood_collision', """
Collision walks: the Acid Garden's wall stops the party, its gate lets it in, and the gantry's deck carries it up from
the cradle's slope to the hull breach (BROOD_SPIRES.md BUILD-READY 7, BUILDER_GUIDE outdoor extras).
""", steps)

# The acid rain: the day's roll is a hash of the day (the map's Lua, build_out3.py RAIN_LUA). From the new game's clock
# (NEW_GAME_MINUTES) advance to the first rainy hour, reload: a party member without a sealed helm burns, one with the
# Rebreather Helm does not.
NEW_GAME_MINUTES = json.loads((PROJECT / 'work/new_game_clock.json').read_text())['minutes'] \
    if (PROJECT / 'work/new_game_clock.json').exists() else None


def rain_day(day):
    h = (day * 2654435761 + 977) % 4294967296
    h = (h ^ (h >> 13)) * 1274126177 % 4294967296
    h = h ^ (h >> 16)
    return (h % 1000) < 400, (h >> 10) % 16, 2 + (h >> 14) % 8


if NEW_GAME_MINUTES is not None:
    minute = NEW_GAME_MINUTES
    while True:
        day, hour = minute // 1440, (minute % 1440) // 60
        rains, first, length = rain_day(day)
        if rains and first <= hour < first + length - 1:
            break
        minute = (minute // 60 + 1) * 60 + 5
    advance = minute - NEW_GAME_MINUTES

    def party(helm):
        return {'gold': 0, 'food': 10, 'members': [{
            'name': 'Helmed' if helm else 'Bareheaded', 'class': 'Knight', 'level': 40, 'skills': [],
            'equipment': {'helm': 11106} if helm else {}}]}
    steps = []
    for helm in (True, False):
        steps += [{'new_game_flow': {'start_map': 'hes_out3.odm', 'party': party(helm)}},
                  {'load_map': {'map': 'hes_out3.odm'}},
                  {'assert': {'runtime_event_variable': {'id': 124, 'value': 0}}},
                  {'advance_game_time': {'minutes': advance}},
                  {'load_map': {'map': 'hes_out3.odm'}},
                  {'assert': {'runtime_event_variable': {'id': 124, 'value': 1}}},
                  {'assert': {'party_health': {'full': helm}}}]
        steps += [{'assert': {'qbit_clear': [100503]}}] if helm else [{'assert': {'qbit_set': [100503]}}]
    write('brood_acid_rain', f"""
The acid rain (BROOD_SPIRES.md section 9, events 1, 3, 4): {advance} game minutes after a new game (day
{minute // 1440}, hour {(minute % 1440) // 60}) the day's roll has it raining (map variable 1); on load the rain starts and
burns each character without a sealed helm: a party in the Rebreather Helm (11106) stays whole and 100503 stays clear,
a bareheaded party burns (3D6 Body) and meets the rain (100503; autonote 10201).
""", steps)
print('wrote', sorted(p.name for p in PROJECT.glob('brood_*.yml')))
