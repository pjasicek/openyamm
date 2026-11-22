"""A6 (2026-11-21): D6's playtest_hostility.yml. At load the archers (11104/11105), the lava dwellers (11620/11621) and
the robots (11610/11611) hostile; Ambrose (5512) and the tethered griffin (11913) peaceful. The elementals stay over
the lake and its shores on their home radius (20 s with the party at Ash Fork, then on the lake's east shore). After
m33.done (111662) the load event hides the robots (m33.robots_gone); after m25.done (111503) Ambrose and the griffin
(m25.camp_gone). Written from the build's scene (actor indices)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import yaml
R = _REPO_ROOT
M = 'xeen_d6.odm'
scene = yaml.load(open(f'{R}/output/studio_cal/d6/build/xeen_d6.scene.yml'), Loader=yaml.CSafeLoader)
ACT = list(enumerate(scene['initial_state']['actors']))
ELEM = [(i, a) for i, a in ACT if a.get('monster_id') in (11620, 11621)]
ROBOT = [i for i, a in ACT if a.get('monster_id') in (11610, 11611)]
AMB = [i for i, a in ACT if a.get('npc_id') == 5512 or a.get('monster_id') == 11913]
assert len(ELEM) == 14 and len(ROBOT) == 18 and len(AMB) == 2, (len(ELEM), len(ROBOT), len(AMB))


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


steps = [{'new_game_flow': {'start_map': M}}, {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'note': 'At load'}, {'advance_runtime': {'seconds': 2}}]


def count(mid, hostile=None, lo=None, hi=None, near=None):
    a = {'monster_id': mid}
    for k, v in (('hostile', hostile), ('min', lo), ('max', hi), ('near', near)):
        if v is not None:
            a[k] = v
    steps.append({'assert': {'actor_count': a}})


for mid, n in ((11104, 9), (11105, 3), (11620, 11), (11621, 3), (11610, 16), (11611, 2)):
    count(mid, True, lo=n)
count(11913, True, hi=0)
steps.append({'assert': {'actor_visible': {'actor_index': AMB[0], 'hidden': False}}})


def elementals(note):
    steps.append({'note': note})
    steps.append({'advance_runtime': {'seconds': 20}})
    for i, a in ELEM:
        p = a['position']
        count(a['monster_id'], lo=1, near=[p['x'], p['y'], (a.get('leash_radius') or 1024) + 400])
        steps.append({'assert': {'actor_visible': {'actor_index': i, 'dead': False, 'report_state': True}}})


AF = W(66.0, 86.0)
steps.append({'set_pose': {'map': M, 'x': AF[0], 'y': AF[1], 'z': 1800, 'yaw': 1.5708, 'pitch': 0.0}})
elementals('The lava dwellers 20 s later, the party at Ash Fork: each near its home (leash + 400)')
ES = W(82.0, 72.0)
steps.append({'set_pose': {'map': M, 'x': ES[0], 'y': ES[1], 'z': 1700, 'yaw': 3.1416, 'pitch': 0.0}})
elementals("The lava dwellers 20 s later, the party on the lake's east shore (the signature's place)")
steps += [{'note': 'm33.done (111662): m33.robots_gone hides the robots on load'},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 111662, 'value': True}}, {'load_map': {'map': M}},
          {'advance_runtime': {'seconds': 3}}]
steps += [{'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}} for i in ROBOT]
steps += [{'assert': {'actor_visible': {'actor_index': AMB[0], 'hidden': False}}},
          {'note': 'm25.done (111503): m25.camp_gone hides Ambrose and the tethered griffin on load'},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 111503, 'value': True}}, {'load_map': {'map': M}},
          {'advance_runtime': {'seconds': 3}}]
steps += [{'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}} for i in AMB]
count(11104, True, lo=9)
doc = {'id': 'xeen.d6.l4.hostility', 'title': 'D6 The Forbidden Zone: camps, lava dwellers, robots and Ambrose by state',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(f'{R}/devdocs/xeen/briefs/d6/L4/playtest_hostility.yml', 'w') as f:
    f.write('# Hostility check of D6 (written by output/studio_cal/d6/tools/gen_hostility_d6.py).\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('wrote playtest_hostility.yml', len(steps))
