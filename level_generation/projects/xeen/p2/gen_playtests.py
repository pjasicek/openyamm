#!/usr/bin/env python3
"""P2's L4 playtests (A6, seventeenth session, 2026-11-21; after P1's), from the build's scene (the guardians'
indices): the walk, hostility, the test (and a save and reload, the curtain passable both times, D-64), the P-2 proof
(straight into the curtain before the test, and round the gate's stones), and three falls in D-54's shape (D-58 P2 Q1:
off the Kite Isle's west rim, the Eye's east rim and the Singing Stones' north rim, back onto the Gale Landing; HP
measured, then held exact 0.5 s after the landing and again after 20 s). Run with output/studio_cal/p2/run.sh.

    python3 level_generation/projects/xeen/p2/gen_playtests.py
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
sys.path.insert(0, str(pathlib.Path(_REPO_ROOT, 'level_generation/projects/xeen/common/planes')))
import pieces as PC  # noqa: E402

L4 = gen.BRIEF / 'L4'
BUILD = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p2') / 'build'
MAP = 'xeen_p2.blv'
SCENE = yaml.safe_load(open(BUILD / 'xeen_p2.scene.yml'))
ACTORS = SCENE['initial_state']['actors']
GUARDS = [i for i, a in enumerate(ACTORS) if a.get('group') == gen.GUARD_GROUP]
ARRIVAL = gen.PLACE['entrance:d7_fall']['at']
EYE = gen.EYE_FL
SX = gen.STAIR_X
GATE_Y = gen.GATE_Y
FRONT = (SX, GATE_Y - 260)                 # on the Eye, facing the curtain
LEVEL = 60
PROBE = os.environ.get('P2_FALL_PROBE') == '1'
# A new party's HP is random, the fall's damage is not: each member is set to START_HP before the fall, and the HP
# is asserted exact 0.5 s after the landing and again 20 s later (D-54); tools/check_falls.py (run.sh) reports it.
FALL_HP = None
START_HP = [200, 140, 140, 140]    # each member set to this before the fall (a new party's HP is random; under max)
FALL_LOSS = [112, 49, 69, 46]      # measured 2026-11-21 (xrun/run_051347, 6 runs): the same each fall
# where each push round a gate stone ends (probed, then fixed): never on the stair
BYPASS_END = [(ARRIVAL[0], ARRIVAL[1], 256, -8, 40)] * 2   # walked off the rim, thrown back onto the Gale Landing


def party():
    names = [('Brokk', 'Knight'), ('Hild', 'Cleric'), ('Ivar', 'Archer'), ('Sefa', 'Sorcerer')]
    return {'gold': 0, 'food': 20, 'members': [{'name': n, 'class': c, 'level': LEVEL, 'skills': [], 'equipment': {}}
                                               for n, c in names]}


def head(immortal=True):
    s = [{'new_game_flow': {'start_map': MAP, 'party': party()}}]
    if immortal:
        s.append({'setup_shortcut': {'kind': 'immortal', 'value': True}})
    s += [{'play_lua': {'source': 'wait(2); close()'}}, {'assert': {'map': MAP}}]
    return s


def walk(x, y, z, radius=128, timeout=60, clear=1500, ztol=160):
    return {'walk_to': {'x': int(x), 'y': int(y), 'z': int(z), 'z_tolerance': ztol, 'radius': radius,
                        'timeout_seconds': timeout, 'clear_hostiles': clear, 'close_dialogs': True}}


def lua(src):
    return {'play_lua': {'source': src}}


def pose(x, y, z, yaw=0):
    return {'set_pose': {'map': MAP, 'x': int(x), 'y': int(y), 'z': int(z), 'yaw_degrees': yaw, 'pitch': 0}}


def at(x, y, r, zmin, zmax):
    return {'assert': {'party_position': {'x': int(x), 'y': int(y), 'radius': r, 'z_min': int(zmin),
                                          'z_max': int(zmax)}}}


def push(x, y, z, yaw, seconds=4.0):
    return {'movement_segment': {'input': 'forward', 'seconds': seconds, 'actor_collision': True, 'actor_ai': False,
                                 'start': {'map': MAP, 'x': int(x), 'y': int(y), 'z': int(z), 'yaw_degrees': yaw,
                                           'pitch': 0},
                                 'expect_stop': {'map': MAP, 'x': int(x), 'y': int(y), 'z': int(z),
                                                 'yaw_degrees': yaw, 'pitch': 0},
                                 'loose_tolerance': True, 'tolerance_xy': 40000, 'tolerance_z': 8000}}


def write(name, title, comment, steps):
    doc = {'id': f'xeen.p2.l4.{name}', 'title': f'Plane of Air (P2): {title}', 'world': 'xeen', 'mode': 'faithful',
           'steps': steps}
    path = L4 / (f'playtest_{name}.yml' if name != 'walk' else 'playtest.yml')
    with open(path, 'w') as f:
        f.write(f'# {comment}\n# Written by output/studio_cal/p2/tools/gen_playtests.py; run with --world xeen --map '
                f'{MAP}.\n')
        yaml.safe_dump(doc, f, sort_keys=False, width=120, allow_unicode=True)


def curtain_blocks():
    """Straight north into the curtain from the Eye: the party stops south of it, on the Eye's floor."""
    return [push(FRONT[0], FRONT[1], EYE, 90, 3.0),
            at(SX, GATE_Y - 120, 110, EYE - 8, EYE + 16)]


def through_curtain():
    """Through the stilled curtain, up the Stair of Wind into the aerie."""
    return [walk(FRONT[0], FRONT[1], EYE, clear=0), walk(SX, GATE_Y + 600, EYE + 80, clear=0),
            walk(SX, gen.HEAD_Y - 300, gen.AERIE_FL, clear=0, timeout=90),
            walk(SX + 128, gen.HEAD_Y + 400, gen.AERIE_FL, clear=0),
            at(SX + 128, gen.HEAD_Y + 400, 200, gen.AERIE_FL - 8, gen.AERIE_FL + 24)]


def rim_point(sid, deg, inset=192):
    c = gen.SPACE[sid]['at']
    far = (c[0] + 40000 * math.cos(math.radians(deg)), c[1] + 40000 * math.sin(math.radians(deg)))
    rim = gen.PG.ray_exit([tuple(p) for p in gen.TOPS[sid]], c, far)
    L = math.hypot(rim[0] - c[0], rim[1] - c[1])
    return (rim[0] - (rim[0] - c[0]) / L * inset, rim[1] - (rim[1] - c[1]) / L * inset)


def clear_deg(sid, deg):
    """The direction nearest `deg` whose run from the rim point out over the edge meets no crag or stone."""
    solid = [gen.foot(p) for p in gen.ROOMS['rooms'][0]['platforms']
             if any(w in p['id'] for w in ('crag', '_stone', 'singing', 'cairn', 'plinth', 'column'))]
    for dd in sorted(range(-60, 61, 5), key=abs):
        d = deg + dd
        x, y = rim_point(sid, d)
        u = (math.cos(math.radians(d)), math.sin(math.radians(d)))
        pts = [(x + u[0] * t, y + u[1] * t) for t in range(-64, 520, 32)]
        if all(not gen.PG.point_in(q, f) and gen.poly_dist_outline(q, f) > 120 for q in pts for f in solid):
            return d
    raise SystemExit(f'no clear fall from {sid}')


def hp(label, exact=None):
    exact = exact or ([h - d for h, d in zip(START_HP, FALL_LOSS)] if FALL_LOSS else None)
    if PROBE or exact is None:
        return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': 1,
                                                                    'health_max': 100000}}} for k in range(4)]
    return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': v, 'health_max': v}}}
                                for k, v in enumerate(exact)]


def fall(name, sid, deg, label):
    deg = clear_deg(sid, deg)
    x, y = rim_point(sid, deg)
    fl = gen.FLOOR_OF[sid]
    s = head(immortal=False)
    s += [{'clear_hostiles': {'radius': 40000}}]
    s += [{'setup_shortcut': {'kind': 'set_member_points', 'member_index': k, 'health': START_HP[k]}} for k in range(4)]
    s += hp('Before the fall: the HP set (logged)', START_HP)
    s += [push(x, y, fl, deg, 1.5),
          {'advance_runtime': {'seconds': 6.0, 'follow_map_move': True}},
          {'advance_runtime': {'seconds': 0.5}},
          {'assert': {'map': MAP}},
          at(ARRIVAL[0], ARRIVAL[1], 256, -8, 40)]
    s += hp("0.5 s after the landing: everyone alive, the fall's damage only (D-6.2)")
    s += [{'advance_runtime': {'seconds': 20.0}}]
    s += hp('After 20 s on the Gale Landing (D-54): nobody has lost a point more')
    s += [at(ARRIVAL[0], ARRIVAL[1], 256, -8, 40)]
    write(f'fall_{name}', f'a fall off {label} lands on the Gale Landing; the party lives and loses nothing more '
          'in 20 s (D-58 P2 Q1, D-54)', f'A fall off {label} (D-58 P2 Q1): Xeen.skyFallTo("p2").', s)


def main():
    # the walk: arrival, bridge to the statue, east bridge to the Eye (round the test's plate), the curtain shut
    s = head()
    s.append(at(ARRIVAL[0], ARRIVAL[1], 96, -8, 40))
    s.append({'note': 'Across the south bridge to the Wind Statue (S: the statue, blocked; its plinth stands).'})
    s += [walk(-3300, -3750, 0), walk(-2600, -3370, 32), walk(-1700, -2780, 120), walk(-700, -2250, 128)]
    s.append({'note': "The east bridge to the Eye of the Winds, round the test's plate."})
    s += [walk(500, -2380, 128), walk(1400, -2720, 200), walk(2200, -3060, 256), walk(2500, -3500, 256),
          walk(3500, -3300, 256), walk(3700, -2000, 256), walk(*FRONT, EYE)]
    s.append({'note': 'The curtain of wind holds before the test (D-64).'})
    s += curtain_blocks()
    write('walk', "arrival, the statue's island, the Eye; the curtain holds before the test",
          'The walk (D-58): arrival, the statue, the Eye, the curtain shut before the test.', s)

    # hostility: 27 placed hostiles awake, the three guardians hidden, a quiet arrival
    s = head()
    s.append({'advance_runtime': {'seconds': 2}})
    s.append({'assert': {'actor_count': {'hostile': True, 'min': 27}}})
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append({'advance_runtime': {'seconds': 6}})
    s.append(at(ARRIVAL[0], ARRIVAL[1], 96, -8, 40))
    write('hostility', "27 hostiles placed, the test's three hidden, a quiet arrival",
          'Hostility: the field groups hostile, the guardians hidden until the test.', s)

    # the test: accept, the guardians rise, kill them, the qbit stills the curtain; a save and reload
    tp = gen.PLACE['poi:test']['at']
    plate = (tp[0] + 96, tp[1])
    s = head()
    s += [pose(plate[0] + 360, plate[1], EYE + 8, 180), {'clear_hostiles': {'radius': 3000}},
          {'advance_runtime': {'seconds': 1}}]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append({'note': "Onto the test's floor: 'Accept the test of Air?' Yes."})
    s += [{'walk_to': {'x': plate[0], 'y': plate[1], 'z': EYE + 4, 'z_tolerance': 60, 'radius': 48,
                       'timeout_seconds': 20, 'expect': 'dialog'}},
          {'answer_input': {'text': 'Yes'}}, {'advance_runtime': {'seconds': 1.5}},
          lua("close(); wait(0.5); close()")]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': False}}})
    s.append(lua(f"if qbit({gen.TEST_QBIT}) then error('the test qbit is set before the guardians die') end"))
    s.append({'note': 'Before the kill the curtain still holds.'})
    s += curtain_blocks()
    s.append({'note': 'The three guardians die (the scenario strikes them): Xeen.planeTestCheck sets 111765.'})
    for i in GUARDS:
        s.append({'damage_actor': {'actor_index': i, 'amount': 1000000}})
    s += [{'advance_runtime': {'seconds': 3}}, lua('close(); wait(0.5); close()'),
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit {gen.TEST_QBIT} not set after the kill') end"),
          {'advance_runtime': {'seconds': 2}}, lua('close(); wait(0.5); close()')]
    # The field's groups roam (since the 3.3 AI no monster stands still): a Lesser Air Elemental of group 5 drifted from
    # its post (720, 1114) onto the Stair of Wind and stood in the party's way after the reload (xeen-fb4-dungeon6,
    # 2026-11-25). The test is the curtain's, not a fight: clear the field before each walk through it.
    s.append({'note': "The curtain stilled: through it and up the Stair of Wind into the Sleeper's Aerie."})
    s += [{'clear_hostiles': {'radius': 40000}}]
    s += through_curtain()
    s.append({'note': 'A save and a reload: the qbit kept, the guardians dead; the curtain passable again.'})
    s += [{'reload': {}}, {'advance_runtime': {'seconds': 2}},
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit lost') end"), pose(*FRONT, EYE + 8, 90),
          {'advance_runtime': {'seconds': 1}}]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'dead': True}}})
    s += [{'clear_hostiles': {'radius': 40000}}]
    s += through_curtain()
    write('test', 'the test raises the guardians, their deaths set 111765 and still the curtain, kept over a reload',
          'The test (D-58 C3, C4, P-1; D-64).', s)

    # P-2: before the test nobody reaches the stair: straight into the curtain, and round each gate stone toward
    # the stair's first steps (the stone and the cheek stop the party, or it walks off the rim and falls back onto
    # the Gale Landing); never on the stair
    s = head()
    s += [{'clear_hostiles': {'radius': 40000}}]
    s.append({'note': 'Straight into the curtain (D-64): the party stays on the Eye.'})
    s += curtain_blocks()
    for k, sgn in enumerate((-1, 1)):
        x0 = SX + sgn * 700
        yaw = 90 - sgn * 35
        s.append({'note': f"Beside the {'west' if sgn < 0 else 'east'} gate stone, toward the stair's foot."})
        s += [push(x0, GATE_Y - 300, EYE, yaw, 4.0), {'advance_runtime': {'seconds': 5.0, 'follow_map_move': True}},
              at(*BYPASS_END[k])]
    write('bypass', 'before the test nobody reaches the Stair of Wind (P-2, D-64)',
          'P-2: no way to the aerie but through the stilled curtain.', s)

    fall('kite_west', 'room:kite_isle', 180, "the Kite Isle's west rim")
    fall('eye_east', 'room:arena', 0, "the Eye's east rim")
    fall('stones_north', 'room:stones', 90, "the Singing Stones' north rim")
    # session 20: S's pieces: the sleeper's three answers and the dais, the updraft's column asks like the way up
    ids = yaml.safe_load(open(L4 / 'ids.lock.yml'))
    if 'evt:sleeper' in ids['events']:
        cx, cy = gen.DOME_AT
        f = math.radians(225)
        near = (cx + 420 * math.cos(f), cy + 420 * math.sin(f), gen.AERIE_FL + 8)
        write('sleeper', "the Air Sleeper's three answers, the dais rising when he wakes, kept over a reload, to D7",
              "The sleeper (A3's m38.sleeper_air) and the return dais (D-58 C5, C7).",
              PC.sleeper_steps('air', MAP, head, ids, near, 45))
        s = head()
        s += [{'note': "S's updraft column asks like the way up"},
              lua(f"click({ids['events']['evt:way_up_column']}); wait(0.5)"),
              {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}}, {'advance_runtime': {'seconds': 2.0, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_d7.blv'}},
              {'assert': {'party_position': {'x': PC.RETURN['air'][0], 'y': PC.RETURN['air'][1], 'radius': 256}}}]
        write('way_up_column', "S's updraft asks like the way up (D-58 C5)", "The updraft's decoration.", s)
    print('playtests written; guardians', GUARDS)


if __name__ == '__main__':
    main()
