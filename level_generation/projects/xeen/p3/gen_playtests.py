#!/usr/bin/env python3
"""P3's L4 playtests (A6, seventeenth session, 2026-11-21; after P1's and P2's), from the build's scene (the
guardians' indices): the walk (arrival, the statue, the Pillar Field, the Anvil; the slab holds), hostility, the test
(Yes, the guardians shown and killed, qbit 111766, the slab sunk, down the Root Stair into the Hollow; a save and
reload keeping it), the P-2 proof (into the slab, from the Anvil's rim beside the cheeks, from the scree against the
Hollow's lip and the cheeks) and the scree (a drop off the statue's terrace is a real fall: HP lost, then the party
walks back up the terrace's scree slope). Run with output/studio_cal/p3/run.sh (tools/check_scree.py checks the fall).

    python3 level_generation/projects/xeen/p3/gen_playtests.py
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
sys.path.insert(0, str(pathlib.Path(_REPO_ROOT, 'level_generation/projects/xeen/common/planes')))
import pieces as PC  # noqa: E402

L4 = gen.BRIEF / 'L4'
BUILD = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p3') / 'build'
MAP = 'xeen_p3.blv'
SCENE = yaml.safe_load(open(BUILD / 'xeen_p3.scene.yml'))
ACTORS = SCENE['initial_state']['actors']
GUARDS = [i for i, a in enumerate(ACTORS) if a.get('group') == gen.GUARD_GROUP]
ARRIVAL = gen.PLACE['entrance:d7_fall']['at']
ARENA = gen.ARENA_FL
HOLLOW = gen.HOLLOW_FL
SCREE = gen.SCREE
LEVEL = 60
FRONT = gen.along(-420)                    # on the Anvil, facing the slab down the stair
STAIR_YAW = gen.STAIR_FAC
PLATFORMS = {p['id']: p for p in gen.ROOMS['rooms'][0]['platforms']}


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


def in_scree():
    """Down in the scree (never on the Root Stair, -416 to -764, or in the Hollow, -768)."""
    return at(0, 0, 100000, SCREE - 8, SCREE + 200)


def write(name, title, comment, steps):
    doc = {'id': f'xeen.p3.l4.{name}', 'title': f'Plane of Earth (P3): {title}', 'world': 'xeen', 'mode': 'faithful',
           'steps': steps}
    path = L4 / (f'playtest_{name}.yml' if name != 'walk' else 'playtest.yml')
    with open(path, 'w') as f:
        f.write(f'# {comment}\n# Written by output/studio_cal/p3/tools/gen_playtests.py; run with --world xeen --map '
                f'{MAP}.\n')
        yaml.safe_dump(doc, f, sort_keys=False, width=120, allow_unicode=True)


def link_pts(lid):
    l = next(l for l in gen.D['links'] if l['id'] == lid)
    a, b, _ = gen.link_cut(l)
    return a, b, gen.FLOOR_OF[l['a']], gen.FLOOR_OF[l['b']]


def slab_holds():
    return [push(FRONT[0], FRONT[1], ARENA, STAIR_YAW, 3.0), at(*gen.along(-150), 160, ARENA - 8, ARENA + 24)]


def through_slab():
    p1, p2, p3 = gen.along(-200), gen.along(gen.FIRST_STEP_T + 6 * gen.STEP_RUN), gen.along(gen.STAIR_END_T + 500)
    return [walk(*FRONT, ARENA, clear=0), walk(*p1, ARENA, clear=0), walk(*p2, ARENA - 192, clear=0, ztol=120),
            walk(*p3, HOLLOW, clear=0), at(*p3, 200, HOLLOW - 8, HOLLOW + 24)]


def slope_ends(sid):
    e = PLATFORMS[f'platform:{gen.key(sid)}_scree']
    f = math.radians(e['facing'])
    u = (math.cos(f), math.sin(f))
    L = e['size'][0]
    top = (e['at'][0] - u[0] * (L / 2 + 250), e['at'][1] - u[1] * (L / 2 + 250))
    bottom = (e['at'][0] + u[0] * (L / 2 + 260), e['at'][1] + u[1] * (L / 2 + 260))
    return top, bottom, math.degrees(f)


def drop_dir(sid):
    """The direction from the terrace's middle that runs off its rim into open scree (no link, slope or talus near)."""
    s = gen.SPACE[sid]
    c = s['at']
    solid = [gen.foot(p) for p in gen.ROOMS['rooms'][0]['platforms']
             if not p['id'].startswith(f"platform:{gen.key(sid)}") or p['id'].endswith('_scree')]
    best = None
    sdeg = slope_ends(sid)[2]                       # the slope runs out from the terrace this way
    for deg in range(0, 360, 10):
        if abs((deg - sdeg + 180) % 360 - 180) > 75:
            continue
        th = math.radians(deg)
        rim = gen.PG.ray_exit(list(gen.OUTLINE[sid]), c, (c[0] + 20000 * math.cos(th), c[1] + 20000 * math.sin(th)))
        pts = [(rim[0] + math.cos(th) * t, rim[1] + math.sin(th) * t) for t in range(64, 900, 48)]
        d = min(gen.poly_dist(q, f) for q in pts for f in solid)
        if best is None or d > best[0]:
            best = (d, deg, rim)
    return best


def main():
    # the walk: arrival, the ramp to the statue, the ramp to the Pillar Field, the ramp to the Anvil; the slab holds
    s = head()
    s.append(at(ARRIVAL[0], ARRIVAL[1], 96, -8, 40))
    a, b, za, zb = link_pts('link:ramp_n')
    s.append({'note': "Down the ramp to the Stone Statue (S's statue blocked; its plinth stands)."})
    s += [walk(*a, za), walk(*b, zb)]
    a, b, za, zb = link_pts('link:ramp_c')
    s.append({'note': 'Down to the Pillar Field.'})
    s += [walk(*a, za), walk(*b, zb)]
    a, b, za, zb = link_pts('link:ramp_a')
    s.append({'note': "Down to the Anvil's east gate, then across the Anvil to the Root Stair's slab."})
    s += [walk(*a, za), walk(*b, zb), walk(-3000, -2300, ARENA), walk(*FRONT, ARENA)]
    s.append({'note': 'The slab bars the Root Stair before the test.'})
    s += slab_holds()
    write('walk', "arrival, the statue, the Pillar Field, the Anvil; the slab holds before the test",
          'The walk (D-58): arrival, the statue, the Anvil, the slab shut before the test.', s)

    # hostility
    s = head()
    s.append({'advance_runtime': {'seconds': 2}})
    s.append({'assert': {'actor_count': {'hostile': True, 'min': 27}}})
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append({'advance_runtime': {'seconds': 6}})
    s.append(at(ARRIVAL[0], ARRIVAL[1], 96, -8, 40))
    write('hostility', "27 hostiles placed, the test's three hidden, a quiet arrival",
          'Hostility: the field groups hostile, the guardians hidden until the test.', s)

    # the test
    tp = gen.PLACE['poi:test']['at']
    plate = (tp[0] - 64, tp[1])
    s = head()
    s += [pose(plate[0] - 380, plate[1], ARENA + 8, 0), {'clear_hostiles': {'radius': 40000}},
          {'advance_runtime': {'seconds': 1}}]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append({'note': "Onto the test's floor: 'Accept the test of Earth?' Yes."})
    s += [{'walk_to': {'x': plate[0], 'y': plate[1], 'z': ARENA + 4, 'z_tolerance': 60, 'radius': 48,
                       'timeout_seconds': 20, 'expect': 'dialog'}},
          {'answer_input': {'text': 'Yes'}}, {'advance_runtime': {'seconds': 1.5}},
          lua("close(); wait(0.5); close()")]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': False}}})
    s.append(lua(f"if qbit({gen.TEST_QBIT}) then error('the test qbit is set before the guardians die') end"))
    s.append({'note': 'Before the kill the slab still holds.'})
    s += slab_holds()
    s.append({'note': 'The three guardians die (the scenario strikes them): Xeen.planeTestCheck sets 111766.'})
    for i in GUARDS:
        s.append({'damage_actor': {'actor_index': i, 'amount': 1000000}})
    s += [{'advance_runtime': {'seconds': 3}}, lua('close(); wait(0.5); close()'),
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit {gen.TEST_QBIT} not set after the kill') end"),
          {'advance_runtime': {'seconds': 5}}, lua('close(); wait(0.5); close()')]
    s.append({'note': "The slab sunk: down the Root Stair into the Sleeper's Hollow."})
    s += through_slab()
    s.append({'note': 'A save and a reload: the qbit kept, the guardians dead, the slab sunk again.'})
    s += [{'reload': {}}, {'advance_runtime': {'seconds': 2}},
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit lost') end"), pose(*FRONT, ARENA + 8, STAIR_YAW),
          {'advance_runtime': {'seconds': 5}}]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'dead': True}}})
    s += through_slab()
    write('test', "the test raises the guardians, their deaths set 111766 and sink the slab, kept over a reload",
          'The test (D-58 C3, C4, P-1).', s)

    # P-2: no way onto the Root Stair or into the Hollow before the test
    s = head()
    s += [{'clear_hostiles': {'radius': 40000}}]
    s.append({'note': 'Straight into the slab: the party stays on the Anvil.'})
    s += slab_holds()
    for k, sgn in enumerate((-1, 1)):
        side = sgn * (gen.STAIR_W / 2 + gen.CHEEK_W + 260)
        st = gen.along(-260, side)
        yaw = STAIR_YAW - sgn * 35
        s.append({'note': f"From the Anvil's rim beside the {'right' if sgn < 0 else 'left'} cheek, along the cheek and off the rim: into the scree, never onto the stair."})
        s += [push(st[0], st[1], ARENA, STAIR_YAW, 5.0), {'advance_runtime': {'seconds': 4.0}}, in_scree()]
    hx, hy = gen.HOLLOW_AT
    hp = gen.OUTLINE['room:chamber']
    for k, deg in enumerate((180, 0, 90)):
        th = math.radians(deg)
        rim = gen.PG.ray_exit(list(hp), (hx, hy), (hx + 20000 * math.cos(th), hy + 20000 * math.sin(th)))
        st = (rim[0] + math.cos(th) * 260, rim[1] + math.sin(th) * 260)
        s.append({'note': f"From the scree against the Hollow's {('west', 'east', 'north')[k]} lip (256 high)."})
        s += [push(st[0], st[1], SCREE, (deg + 180) % 360, 4.0), {'advance_runtime': {'seconds': 2.0}},
              in_scree()]
    for k, sgn in enumerate((-1, 1)):
        st = gen.along(gen.FIRST_STEP_T + 5 * gen.STEP_RUN, sgn * (gen.STAIR_W / 2 + gen.CHEEK_W + 300))
        s.append({'note': f"From the scree against the stair's {'right' if sgn < 0 else 'left'} cheek."})
        yaw = (STAIR_YAW + (90 if sgn < 0 else -90)) % 360
        s += [push(st[0], st[1], SCREE, yaw, 4.0), {'advance_runtime': {'seconds': 2.0}},
              in_scree()]
    write('bypass', 'before the test nobody reaches the Root Stair or the Hollow (P-2)',
          'P-2: no way to the Hollow but past the sunken slab.', s)

    # the scree: a real fall off the statue's terrace, then back up its scree slope
    sid = 'room:statue'
    clear, deg, rim = drop_dir(sid)
    th = math.radians(deg)
    st = (rim[0] - math.cos(th) * 160, rim[1] - math.sin(th) * 160)
    fl = gen.FLOOR_OF[sid]
    top, bottom, sdeg = slope_ends(sid)
    s = head(immortal=False)
    s += [{'clear_hostiles': {'radius': 40000}}]
    s += [{'setup_shortcut': {'kind': 'set_member_points', 'member_index': k, 'health': 140}} for k in range(4)]
    s += [{'note': 'Before the drop: 140 HP each (logged)'}]
    s += [{'assert': {'member_points': {'member_index': k, 'health_min': 140, 'health_max': 140}}} for k in range(4)]
    s += [push(st[0], st[1], fl, deg, 2.0), {'advance_runtime': {'seconds': 4.0}},
          at(0, 0, 100000, SCREE - 8, SCREE + 40)]
    s += [{'note': 'After the drop into the scree: the falling damage (logged; tools/check_scree.py)'}]
    s += [{'assert': {'member_points': {'member_index': k, 'health_min': 1, 'health_max': 140}}} for k in range(4)]
    s += [{'note': "Back up the statue terrace's scree slope."},
          walk(*bottom, SCREE, clear=0, timeout=90, ztol=200), walk(*top, fl, clear=0, timeout=90, ztol=120),
          {'advance_runtime': {'seconds': 2.0}}, at(*top, 200, fl - 8, fl + 24)]
    write('scree', "a drop off the statue's terrace into the scree is a real fall; the scree slope leads back up",
          'The scree (D-58 P3 Q1): falling damage, no teleport; a scree slope back up.', s)
    # session 20: S's pieces: the sleeper's three answers and the dais, the column asks like the way up
    ids = yaml.safe_load(open(L4 / 'ids.lock.yml'))
    if 'evt:sleeper' in ids['events']:
        sx, sy = gen.PLACE['poi:sleeper']['at']
        f = math.radians(90)
        near = (sx + 420 * math.cos(f), sy + 420 * math.sin(f), gen.HOLLOW_FL + 8)
        write('sleeper', "the Earth Sleeper's three answers, the dais rising when he wakes, kept over a reload, to D7",
              "The sleeper (A3's m38.sleeper_earth) and the return dais (D-58 C5, C7).",
              PC.sleeper_steps('earth', MAP, head, ids, near, 270))
        s = head()
        s += [{'note': "S's column asks like the way up"},
              lua(f"click({ids['events']['evt:way_up_column']}); wait(0.5)"),
              {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}}, {'advance_runtime': {'seconds': 2.0, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_d7.blv'}},
              {'assert': {'party_position': {'x': PC.RETURN['earth'][0], 'y': PC.RETURN['earth'][1], 'radius': 256}}}]
        write('way_up_column', "S's column asks like the way up (D-58 C5)", "The way up's decoration.", s)
    print('playtests written; guardians', GUARDS, 'drop', deg, int(clear), 'slope', [int(v) for v in top + bottom])


if __name__ == '__main__':
    main()
