#!/usr/bin/env python3
"""A6 (2026-11-20): D4's playtest_hostility.yml (D-36, A2's relations): at load the coven's two groups (11170-11172,
xeen_coven) hostile, the octopods hostile and alive in the water, Leafpoint (453), Slibo (611) and the peasants peaceful;
joined (113449): the coven peaceful; after the Head Witch's death (113447) the map's load event hides them
(q-d22.coven_gone; the hide itself is seen in the tour, the scenario cannot see visibility) and the Circle's chest still
opens. The octopods are MM6's sea serpents' kind on a home radius (D-200, U-19: classic AI, the Swimmer kind walks on
water, the placed leash keeps them in it): with the party on land (the Isle, the town's waterfront nearest the south
basin) none notices it (their relation `short`, 2,560) and each stays at home; on the East Skerry the nearest one
(group 7's Great Octopod, about 2,300 off) shoots its ink from the water (ai_trace attack_ranged on the party) and
stays within its leash over water; in the water they still keep their leashes. Positions are reported (report_state)
for the in-water check of octo_check.py."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import yaml
R = _REPO_ROOT
M = 'xeen_d4.odm'
ids = yaml.safe_load(open(f'{R}/devdocs/xeen/briefs/d4/L4/ids.lock.yml'))
scene = yaml.load(open(f'{R}/output/studio_cal/d4/build/xeen_d4.scene.yml'), Loader=yaml.CSafeLoader)
OCTO = [(i, a) for i, a in enumerate(scene['initial_state']['actors']) if a.get('monster_id') in (11470, 11471)]
assert len(OCTO) == 5 and all(a.get('leash_radius') for _, a in OCTO), 'five leashed octopods expected'
ev = dict(ids['events'])


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


steps = [{'new_game_flow': {'start_map': M}}, {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'note': 'At load (D-36)'}, {'advance_runtime': {'seconds': 2}},
         {'console': {'line': 'arena trace on'}}]


def count(mid, hostile=None, lo=None, hi=None, near=None):
    a = {'monster_id': mid}
    if hostile is not None:
        a['hostile'] = hostile
    if lo is not None:
        a['min'] = lo
    if hi is not None:
        a['max'] = hi
    if near:
        a['near'] = near
    steps.append({'assert': {'actor_count': a}})


for mid, n in ((11170, 9), (11171, 4), (11172, 1), (11470, 3), (11471, 2)):
    count(mid, True, lo=n)
for mid in (453, 611, 361, 377):
    count(mid, True, hi=0)


def octopods(note):
    steps.append({'note': note})
    steps.append({'advance_runtime': {'seconds': 20}})
    for i, a in OCTO:
        p = a['position']
        count(a['monster_id'], lo=1, near=[p['x'], p['y'], a['leash_radius'] + 150])
        steps.append({'assert': {'actor_visible': {
            'actor_index': i, 'dead': False, 'report_state': True, 'over_water': True,
            'near': {'x': p['x'], 'y': p['y'], 'max_distance': a['leash_radius'] + 150}}}})


def shots(index, least=None, most=None):
    """The ink (D-200): the classic ranged attack on the party, counted in the decision trace."""
    trace = {'actor_index': index, 'decision': 'attack_ranged', 'target': 'party'}
    if least is not None:
        trace['min_count'] = least
    if most is not None:
        trace['max_count'] = most
    steps.append({'assert': {'ai_trace': trace}})


octopods('The octopods 20 s later, the party at the start (the griffin): each within its leash (+150) of its home')
WF = W(85.0, 83.5)
steps += [{'note': 'The party on the waterfront nearest the south basin (cell 85, 83.5, dry land)'},
          {'set_pose': {'map': M, 'x': WF[0], 'y': WF[1], 'z': 1140, 'yaw': 1.5708, 'pitch': 0.0}}]
octopods('The octopods 20 s later, the party on the waterfront: still in the water, each within its leash')
for i, a in OCTO:
    shots(i, most=0)   # D-200 (3): nobody inked in town (the leash plus 2,560 stays off the waterfront)
G7 = next((i, a) for i, a in OCTO if a['group'] == 7)
SK = W(88.2, 70.8)
steps += [{'note': "The party on the East Skerry's south-west beach (cell 88.2, 70.8: land), about 2,300 from group "
                   "7's Great Octopod (D-200)"},
          {'set_pose': {'map': M, 'x': SK[0], 'y': SK[1], 'z': 1056, 'yaw': -2.356, 'pitch': 0.0}}]
octopods('The octopods 20 s later, the party on the skerry: the nearest attacks from the water and stays within its '
         'leash, over water')
shots(G7[0], least=1)
WET = W(86.0, 68.0)
steps += [{'note': 'The party in the water (cell 86, 68), 1,300 from the Great Octopod of the north basin: it swims'},
          {'set_pose': {'map': M, 'x': WET[0], 'y': WET[1], 'z': 1056, 'yaw': 1.5708, 'pitch': 0.0}}]
octopods('The octopods 20 s later, the party in the water: still within their leashes (octo_check.py: moved)')
steps += [{'note': 'q-d22.joined (113449): the coven peaceful to members (A2)'},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 113449, 'value': True}}, {'load_map': {'map': M}},
          {'advance_runtime': {'seconds': 3}}]
for mid, n in ((11170, 9), (11171, 4), (11172, 1)):
    count(mid, False, lo=n)
    count(mid, True, hi=0)
steps += [{'assert': {'actor_visible': {'actor_index': 0, 'hidden': False}}}]
steps += [{'note': "The Head Witch slain (113447): the load event q-d22.coven_gone hides both groups; A2's relation "
                   "long again"},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 113447, 'value': True}}, {'load_map': {'map': M}},
          {'advance_runtime': {'seconds': 3}},
          {'assert': {'actor_visible': {'actor_index': 0, 'hidden': True}}},
          {'assert': {'actor_visible': {'actor_index': 8, 'hidden': True}}},
          {'note': "The Circle's chest still opens"},
          {'set_pose': {'map': M, 'x': W(51.2, 92.4)[0], 'y': W(51.2, 92.4)[1], 'z': 1460, 'yaw': 1.5708,
                        'pitch': 0.0}},
          {'play_lua': {'source': 'click(%d); wait(0.5); close()' % ev['evt:thing:circle_chest']}}]
doc = {'id': 'xeen.d4.l4.hostility', 'title': "D4 Lakeside and Blackfang: the coven by Q-D22, the octopods in the lake",
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(f'{R}/devdocs/xeen/briefs/d4/L4/playtest_hostility.yml', 'w') as f:
    f.write('# Hostility check of D4 (written by output/studio_cal/d4/tools/gen_hostility_d4.py).\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('wrote playtest_hostility.yml', len(steps))
