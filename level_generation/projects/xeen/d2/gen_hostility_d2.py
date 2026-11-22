#!/usr/bin/env python3
"""A6 (2026-11-20): D2's playtest_hostility.yml (D-23, A2's relations): at load the 22 pass ogres (11066-11068,
xeen_ogres_pass) hostile, Graalg (11064) and his two Brutes (11065, xeen_ogres_graalg) peaceful, the village sprites
(11537, 11538, A2's village rows) peaceful until 113203, the slot kinds (wolves, trolls, Darkside sprites) hostile; with q-d11.friends (113221) the
pass ogres peaceful; after a burned fort (113224 with 113222, as DD-13's hook sets them) every ogre hostile."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import yaml
R = _REPO_ROOT
M = 'xeen_d2.odm'
steps = [{'new_game_flow': {'start_map': M}}, {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'note': 'At load (D-23)'}, {'advance_runtime': {'seconds': 2}}]

def count(mid, hostile, lo=None, hi=None):
    a = {'monster_id': mid, 'hostile': hostile}
    if lo is not None:
        a['min'] = lo
    if hi is not None:
        a['max'] = hi
    steps.append({'assert': {'actor_count': a}})

for mid, n in ((11066, 14), (11067, 6), (11068, 2)):
    count(mid, True, lo=n)
    count(mid, False, hi=0)
for mid, n in ((11064, 1), (11065, 2), (11537, 5), (11538, 3)):
    count(mid, False, lo=n)
    count(mid, True, hi=0)
for mid in (11410, 11411, 11412, 11070, 11071, 11072, 11534, 11535, 11536):
    count(mid, False, hi=0)
steps += [{'note': 'q-d11.friends (113221): the pass ogres peaceful, Graalg still peaceful'},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 113221, 'value': True}}, {'advance_runtime': {'seconds': 3}}]
for mid, n in ((11066, 14), (11067, 6), (11068, 2), (11064, 1), (11065, 2)):
    count(mid, False, lo=n)
    count(mid, True, hi=0)
steps += [{'note': 'The friends kept over a reload of the map'}, {'load_map': {'map': M}},
          {'advance_runtime': {'seconds': 2}}]
count(11066, True, hi=0)
count(11064, True, hi=0)
steps += [{'note': 'A burned fort (DD-13 sets west_burned 113224 and hostile 113222): every ogre hostile (D-12.3)'},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 113224, 'value': True}},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 113222, 'value': True}},
          {'load_map': {'map': M}}, {'advance_runtime': {'seconds': 3}}]
for mid, n in ((11066, 14), (11067, 6), (11068, 2), (11064, 1), (11065, 2)):
    count(mid, True, lo=n)
    count(mid, False, hi=0)
count(11537, False, lo=5)
steps += [{'note': "q-d10.robbery (113203, Sharla's 'stick up'): the village sprites hostile (A2's relations)"},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 113203, 'value': True}}, {'advance_runtime': {'seconds': 3}}]
count(11537, True, lo=5)
count(11538, True, lo=3)
count(11537, False, hi=0)
doc = {'id': 'xeen.d2.l4.hostility', 'title': 'D2 Sprite Forest and Ogre Pass: the ogres by Q-D11, the village at peace',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(f'{R}/devdocs/xeen/briefs/d2/L4/playtest_hostility.yml', 'w') as f:
    f.write('# Hostility check of D2 (written by output/studio_cal/d2/tools/gen_hostility_d2.py): load, friends, a '
            'burned fort.\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('wrote playtest_hostility.yml', len(steps))
