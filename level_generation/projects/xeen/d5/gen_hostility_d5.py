#!/usr/bin/env python3
"""A6 (2026-11-21): D5's playtest_hostility.yml (D-47, D-49 Q1/Q2, A2's relations): at load the six People
(11083-11085, xeen_giants_people) and Gurodel (5452 on 11085) peaceful at the hold, the eyrie's griffins hostile, and
the wild cyclopes of the Quivering Forest (11080-11082, xeen_giants, spawned by slot 3 markers) hostile; one blow on a
People member: the map's timer calls q-d16.hold_attacked (113323) and A2's relations turn the People hostile.
Usage: gen_hostility_d5.py <project L4> <build folder>"""
import os
import sys
import yaml

P, B = sys.argv[1], sys.argv[2]
M = 'xeen_d5.odm'
scene = yaml.load(open(os.path.join(B, 'xeen_d5.scene.yml')), Loader=yaml.CSafeLoader)
acts = scene['initial_state']['actors']
people = [i for i, a in enumerate(acts) if a.get('monster_id') in (11083, 11084, 11085) and not a.get('npc_id')]
assert people == list(range(6)), 'the People must be actors 0-5 (the struck timer reads them): %s' % people


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def count(mid, hostile=None, lo=None, hi=None):
    a = {'monster_id': mid}
    if hostile is not None:
        a['hostile'] = hostile
    if lo is not None:
        a['min'] = lo
    if hi is not None:
        a['max'] = hi
    steps.append({'assert': {'actor_count': a}})


steps = [{'new_game_flow': {'start_map': M}}, {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'note': 'At load (D-49 Q1/Q2): the People and Gurodel peaceful, the griffins and wild cyclopes hostile'},
         {'advance_runtime': {'seconds': 2}}]
count(11083, False, lo=3)
count(11084, False, lo=2)
count(11085, False, lo=2)
for mid in (11083, 11084, 11085):
    count(mid, True, hi=0)
count(11562, True, lo=3)
hx, hy = W(86.0, 49.5)
steps += [{'note': 'The party at the hold: nobody turns in 10 s'},
          {'set_pose': {'map': M, 'x': hx, 'y': hy, 'z': 2700, 'yaw': 1.5708, 'pitch': 0.0}},
          {'advance_runtime': {'seconds': 10}},
          {'play_lua': {'source': "close(); if qbit(113323) then error('hall_attacked set at peace') end"}}]
for mid in (11083, 11084, 11085):
    count(mid, True, hi=0)
fx, fy = W(36.0, 45.0)
steps += [{'note': "The Quivering Forest: the wild cyclopes (11080-11082) hostile (spawned near the lair)"},
          {'set_pose': {'map': M, 'x': fx, 'y': fy, 'z': 2700, 'yaw': 1.5708, 'pitch': 0.0}},
          {'advance_runtime': {'seconds': 2}},
          {'play_lua': {'source': 'close()'}}]
count(11080, True, lo=1)
count(11080, False, hi=0)
count(11081, False, hi=0)
count(11082, False, hi=0)
steps += [{'note': 'One blow on a People giant (actor 0): the timer calls q-d16.hold_attacked; the People turn'},
          {'set_pose': {'map': M, 'x': hx, 'y': hy, 'z': 2700, 'yaw': 1.5708, 'pitch': 0.0}},
          {'damage_actor': {'actor_index': 0, 'amount': 1}},
          {'advance_runtime': {'seconds': 3}},
          {'play_lua': {'source': "close(); if not qbit(113323) then error('hall_attacked 113323 not set') end"}}]
for mid in (11083, 11084):
    count(mid, False, hi=0)
steps += [{'note': 'Reloaded after the blow: the People stay hostile (A2: long after 113323)'},
          {'load_map': {'map': M}}, {'advance_runtime': {'seconds': 3}}]
count(11083, True, lo=3)
count(11084, True, lo=2)
doc = {'id': 'xeen.d5.hostility', 'title': 'D5: the People peaceful, the wild giants hostile, one blow turns the People',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest_hostility.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/d5/tools/gen_hostility_d5.py (A6).\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps))
