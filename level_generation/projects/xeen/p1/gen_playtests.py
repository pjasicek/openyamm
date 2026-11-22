#!/usr/bin/env python3
"""P1's L4 playtests (A6's planes sub-agent, 2026-11-21), from the build's ids.lock.yml (event numbers, doors) and the
scene's actor order (the guardians' indices): the walk, hostility, the lava, the test (and a save and reload), and the
P-2 proof. Run with output/studio_cal/p1/run.sh (headless, through the lane's game slots).

    python3 level_generation/projects/xeen/p1/gen_playtests.py
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
sys.path.insert(0, str(pathlib.Path(_REPO_ROOT, 'level_generation/projects/xeen/common/planes')))
import pieces as PC  # noqa: E402
import math  # noqa: E402

L4 = gen.BRIEF / 'L4'
BUILD = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p1') / 'build'
MAP = 'xeen_p1.blv'
IDS = yaml.safe_load(open(L4 / 'ids.lock.yml'))
SCENE = yaml.safe_load(open(BUILD / 'xeen_p1.scene.yml'))
ACTORS = SCENE['initial_state']['actors']
GUARDS = [i for i, a in enumerate(ACTORS) if a.get('group') == gen.GUARD_GROUP]
GATE = IDS['doors']['door:sleeper']
EVT = IDS['events']
ARRIVAL = gen.PLACE['entrance:d7_fall']['at']


def party():
    names = [('Brokk', 'Knight'), ('Hild', 'Cleric'), ('Ivar', 'Archer'), ('Sefa', 'Sorcerer')]
    return {'gold': 0, 'food': 20, 'members': [{'name': n, 'class': c, 'level': 60, 'skills': [], 'equipment': {}}
                                               for n, c in names]}


def head(immortal=True):
    s = [{'new_game_flow': {'start_map': MAP, 'party': party()}}]
    if immortal:
        s.append({'setup_shortcut': {'kind': 'immortal', 'value': True}})
    s += [{'play_lua': {'source': 'wait(2); close()'}}, {'assert': {'map': MAP}}]
    return s


def walk(x, y, z, radius=128, timeout=60, clear=1500):
    return {'walk_to': {'x': int(x), 'y': int(y), 'z': int(z), 'z_tolerance': 160, 'radius': radius,
                        'timeout_seconds': timeout, 'clear_hostiles': clear, 'close_dialogs': True}}


def lua(src):
    return {'play_lua': {'source': src}}


def pose(x, y, z, yaw=0):
    return {'set_pose': {'map': MAP, 'x': int(x), 'y': int(y), 'z': int(z), 'yaw_degrees': yaw, 'pitch': 0}}


def write(name, title, comment, steps):
    doc = {'id': f'xeen.p1.l4.{name}', 'title': f'Plane of Fire (P1): {title}', 'world': 'xeen', 'mode': 'faithful',
           'steps': steps}
    path = L4 / (f'playtest_{name}.yml' if name != 'walk' else 'playtest.yml')
    with open(path, 'w') as f:
        f.write(f'# {comment}\n# Written by output/studio_cal/p1/tools/gen_playtests.py; run with --world xeen --map '
                f'{MAP}.\n')
        yaml.safe_dump(doc, f, sort_keys=False, width=120, allow_unicode=True)


def gate_closed():
    return lua(f"if door_state({GATE}) == 'open' then error('the gate is open: ' .. door_state({GATE})) end")


def main():
    # the walk: arrival, the statue's spot, the islet, the Crucible, round the pit to the bridge, the gate shut
    s = head()
    s.append({'assert': {'party_position': {'x': ARRIVAL[0], 'y': ARRIVAL[1], 'radius': 96, 'z_min': -8,
                                            'z_max': 40}}})
    s.append({'note': "The statue of Fire (S's, on its own plinth, solid): before its plaque; the plaque reads Step One."})
    stx, sty = gen.PLACE['poi:statue']['at']
    front = (stx + 420 * math.cos(math.radians(315)), sty + 420 * math.sin(math.radians(315)))
    s += [walk(2200, -3240, 32), walk(*front, 64),
          lua(f"click({EVT['evt:plaque']}); wait(0.5)"),
          {'assert': {'dialog': {'active': True, 'text_contains': 'Step One'}}}, lua('close(); wait(0.3); close()'),
          walk(stx - 200, sty - 420, 64)]
    s.append({'note': 'Up the causeway to the Ember Islet, then the long causeway to the Crucible.'})
    s += [walk(-200, -1400, 80), walk(-896, -256, 96), walk(-300, 900, 180), walk(256, 1760, 256)]
    s.append({'note': "Round the test's plate and the pit on the glass, onto the bridge: the gate shut before the test."})
    s += [walk(900, 2300, 256), walk(1100, 3500, 256), walk(300, 4700, 256), walk(-900, 4000, 256),
          walk(-2600, 4090, 380, radius=96)]
    s.append(gate_closed())
    s.append({'assert': {'party_position': {'x': -2600, 'y': 4090, 'radius': 160, 'z_min': 340, 'z_max': 420}}})
    write('walk', 'arrival, statue, Crucible, the gate shut before the test',
          'The walk (D-58): arrival, the statue, the Crucible, the gate shut before the test.', s)

    # hostility: 27 placed hostiles awake, the three guardians hidden
    s = head()
    s.append({'advance_runtime': {'seconds': 2}})
    s.append({'assert': {'actor_count': {'hostile': True, 'min': 27}}})
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append({'note': 'No hostile on the Cinder Shelf (quiet arrival): the nearest group stands 2,500 away.'})
    s.append({'advance_runtime': {'seconds': 6}})
    s.append({'assert': {'party_position': {'x': ARRIVAL[0], 'y': ARRIVAL[1], 'radius': 96}}})
    write('hostility', '27 hostiles placed, the test\'s three hidden, a quiet arrival',
          'Hostility: the field groups hostile, the guardians hidden until the test.', s)

    # the lava burns, the crust does not
    s = head(immortal=False)
    s += [{'clear_hostiles': {'radius': 30000}}, pose(0, -4800, gen.LAVA + 8, 90),
          {'setup_shortcut': {'kind': 'set_member_points', 'member_index': 0, 'health': 400}},
          {'advance_runtime': {'seconds': 4}},
          {'assert': {'party_position': {'x': 0, 'y': -4800, 'radius': 200, 'z_min': gen.LAVA - 8,
                                         'z_max': gen.LAVA + 16}}},
          {'assert': {'member_points': {'member_index': 0, 'health_max': 399}}},
          {'note': 'On the crust of the Cinder Shelf: no burn.'},
          pose(ARRIVAL[0], ARRIVAL[1], 8, 135),
          {'setup_shortcut': {'kind': 'set_member_points', 'member_index': 0, 'health': 400}},
          {'advance_runtime': {'seconds': 4}},
          {'assert': {'member_points': {'member_index': 0, 'health_min': 400, 'health_max': 400}}},
          {'note': 'Out of the lava: from the lake onto the floor-0 shelf (a 40 step).'},
          pose(2560, -4480, gen.LAVA + 8, 0), walk(3400, -4300, 0, radius=128, timeout=30, clear=0)]
    write('lava', 'the lava burns, the crust does not, the party steps out',
          'The lava (D-58 Q1): standing on lavtyl hurts, the crust does not; a floor-0 shelf is a bank.', s)

    # the test: accept, the guardians rise, kill them, the qbit and the gate; a save and reload
    plate = gen.PLACE['poi:test']['at']
    s = head()
    s += [pose(plate[0], plate[1] - 320, 260, 90), {'clear_hostiles': {'radius': 2600}},
          {'advance_runtime': {'seconds': 1}}]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append(gate_closed())
    s.append({'note': "Onto the test's plate: 'Accept the test of Fire?' Yes."})
    s += [{'walk_to': {'x': plate[0], 'y': plate[1], 'z': 262, 'z_tolerance': 60, 'radius': 48,
                       'timeout_seconds': 20, 'expect': 'dialog'}},
          {'answer_input': {'text': 'Yes'}}, {'advance_runtime': {'seconds': 1.5}},
          lua("close(); wait(0.5); close()")]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': False}}})
    s.append(lua(f"if qbit({gen.TEST_QBIT}) then error('the test qbit is set before the guardians die') end"))
    s.append(gate_closed())
    s.append({'note': 'The three guardians die (the scenario strikes them): Xeen.planeTestCheck sets 111764.'})
    for i in GUARDS:
        s.append({'damage_actor': {'actor_index': i, 'amount': 1000000}})
    s += [{'advance_runtime': {'seconds': 3}}, lua('close(); wait(0.5); close()'),
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit {gen.TEST_QBIT} not set after the kill') end"),
          {'advance_runtime': {'seconds': 6}},
          lua(f"if door_state({GATE}) ~= 'open' then error('the gate: ' .. door_state({GATE})) end")]
    s.append({'note': "Through the gate into the Sleeper's Hall."})
    s += [walk(-1200, 3950, 256, clear=0), walk(-2600, 4090, 380, radius=96, clear=0),
          walk(-3300, 4096, gen.HALL_FLOOR, radius=128, clear=0),
          {'assert': {'party_position': {'x': -3300, 'y': 4096, 'radius': 200, 'z_min': 360, 'z_max': 420}}}]
    s.append({'note': 'A save and a reload: the gate open, the guardians dead and hidden.'})
    s += [{'reload': {}}, {'advance_runtime': {'seconds': 2}},
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit lost') end; if door_state({GATE}) ~= 'open' then "
              f"error('gate after the reload: ' .. door_state({GATE})) end")]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'dead': True}}})
    write('test', 'the test raises the guardians, their deaths set 111764 and open the gate, kept over a reload',
          'The test (D-58 C3, C4, P-1).', s)

    # P-2: a party in the lava cannot step into the hall (its walls to the sky; the gate's sill 424 over the lava):
    # west into the notch's east wall north of the gate's frame, then north into its south wall
    s = head()
    s += [{'clear_hostiles': {'radius': 30000}},
          {'movement_segment': {'input': 'forward', 'seconds': 4.0, 'actor_collision': True, 'actor_ai': False,
                                'start': {'map': MAP, 'x': -2650, 'y': 5150, 'z': gen.LAVA, 'yaw_degrees': 180,
                                          'pitch': 0},
                                'expect_stop': {'map': MAP, 'x': -2800, 'y': 5150, 'z': gen.LAVA,
                                                'yaw_degrees': 180, 'pitch': 0},
                                'loose_tolerance': True, 'tolerance_xy': 120, 'tolerance_z': 48}},
          {'assert': {'party_position': {'x': -2790, 'y': 5150, 'radius': 120, 'z_min': gen.LAVA - 8,
                                         'z_max': gen.LAVA + 16}}},
          {'note': "South of the hall: north into the notch's south wall, the lava under the party."},
          {'movement_segment': {'input': 'forward', 'seconds': 4.0, 'actor_collision': True, 'actor_ai': False,
                                'start': {'map': MAP, 'x': -3600, 'y': 3150, 'z': gen.LAVA, 'yaw_degrees': 90,
                                          'pitch': 0},
                                'expect_stop': {'map': MAP, 'x': -3600, 'y': 3400, 'z': gen.LAVA,
                                                'yaw_degrees': 90, 'pitch': 0},
                                'loose_tolerance': True, 'tolerance_xy': 120, 'tolerance_z': 48}},
          {'assert': {'party_position': {'x': -3600, 'y': 3400, 'radius': 120, 'z_min': gen.LAVA - 8,
                                         'z_max': gen.LAVA + 16}}}]
    write('bypass', "a party in the lava cannot step up into the Sleeper's Hall (P-2)",
          'P-2: no way into the hall but the gate.', s)
    # the way up (session 18): the heat column asks A3's question first (No stays), Yes moves to D7's p1_return
    if 'evt:way_up' in EVT:
        w = EVT['evt:way_up']
        s = head()
        s += [{'note': "The heat column: 'Ride the heat back to the Skyroads?' No stays on P1"},
              lua(f'click({w}); wait(0.5)'),
              {'assert': {'dialog': {'active': True, 'action_label_present': 'Close'}}}, {'select_topic': {'match_label': 'Close'}}, {'advance_runtime': {'seconds': 1.0}},
              {'assert': {'map': MAP}}, lua('close()'),
              {'note': "Yes: up to D7's entrance:p1_return"},
              lua(f'click({w}); wait(0.5)'), {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}},
              {'advance_runtime': {'seconds': 2.0, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_d7.blv'}},
              {'assert': {'party_position': {'x': -27456, 'y': 17728, 'radius': 256}}}]
        write('way_up', "the heat column asks before it lifts the party to D7 (D-58 C5)",
              "The way up asks A3's m38.way_up_fire question, then moves to D7's entrance:p1_return.", s)
    if 'evt:way_up_column' in EVT:
        s = head()
        s += [{'note': "S's heat column asks too (session 20)"},
              lua(f"click({EVT['evt:way_up_column']}); wait(0.5)"),
              {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}}, {'advance_runtime': {'seconds': 2.0, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_d7.blv'}}]
        write('way_up_column', "S's heat column asks like the way up (D-58 C5)", "The heat column's decoration.", s)
    # session 20: the sleeper on S's couch, the dais hidden until he wakes, Yes on it to D7
    if 'evt:sleeper' in EVT:
        sx, sy = gen.PLACE['poi:sleeper']['at']
        f = math.radians(gen.COMPASS['se'])
        near = (sx + 420 * math.cos(f), sy + 420 * math.sin(f), gen.HALL_FLOOR + 8)
        write('sleeper', "the Fire Sleeper's three answers, the dais rising when he wakes, kept over a reload, to D7",
              "The sleeper (A3's m38.sleeper_fire) and the return dais (D-58 C5, C7).",
              PC.sleeper_steps('fire', MAP, head, IDS, near, (gen.COMPASS['se'] + 180) % 360))
    print('playtests written; guardians', GUARDS, 'gate door', GATE)


if __name__ == '__main__':
    main()
