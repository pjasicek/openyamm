#!/usr/bin/env python3
"""Hostility pass (2026-11-16): writes each Xeen map's `playtest_hostility.yml` (devdocs/xeen/briefs/<key>/L4; X2's into
output/studio_cal/hostility/scenarios/, X2's brief being reshaped by another agent). Each scenario enters the map with
the party of the map's own playtest.yml and checks, after the map's entry events have run:
- every kind of the map's slots and placed foes is hostile to the party (none peaceful), a slot-only kind and a placed
  kind present and hostile;
- the intended peaceful ones (townsfolk, guards, captives) stay peaceful;
- the map's kinds that hostile.txt sets on each other (and the peaceful ones' kinds), spawned 96 apart some 500 to
  1,500 from the party (a monster takes the nearest of its foes; far off it does not think at all), do not take each
  other as targets for 12 seconds (no `target actor` line in the AI trace of any actor of the map) and are not hurt.
  Outdoors the party is first set down in the wilds by the spot, away from the town's guards.
Usage: gen_hostility_tests.py [key ...]"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[5])  # the repository root
import os
import sys
import yaml

R = _REPO_ROOT
FAM = {'goblin': [271, 272, 273], 'fly': [226, 227, 228], 'skeleton': [397, 398, 399], 'rat': [385, 386, 387],
       'archer': [202, 203, 204], 'wisp': [97, 98, 99], 'ogre': [592, 593, 594], 'dwarf': [229, 230, 231],
       'spider': [400, 401, 402], 'bat': [205, 206, 207], 'trog': [412, 413, 414], 'moon': [214, 215, 216],
       'lich': [289, 290, 291], 'golem': [277, 278, 279], 'eye': [211, 212, 213], 'thief': [406, 407, 408],
       'leather': [256, 257, 258], 'wolf': [85, 86, 87], 'ogre_mage': [106, 107, 108]}
TOWN = [371, 368, 354, 350, 404]


def fam(*names):
    return [kind for name in names for kind in FAM[name]]


# foes: every kind that is to be the party's foe; slot: kinds only the slots bring (present, hostile); placed: a placed
# foe's kind; peaceful: kinds that stay peaceful; pair: kinds spawned side by side at `at`.
SPECS = {
    'x1': dict(title='X1 Vertigo Meadows', foes=fam('goblin', 'fly', 'skeleton'), slot=[397], placed=[226],
               peaceful=TOWN, pair=[226, 271, 397], at=[11264, -3072, 640], pose=[11264, -2072, 2000],
               after_entry=[{'advance_runtime': {'seconds': 1.5}}, {'assert': {'dialog': {'active': True}}},
                            {'press_action': {'action': 'cancel_dialog'}}]),
    'x2': dict(title='X2 Rivercity and Lake Darzog', foes=fam('archer', 'wisp', 'ogre') + [192], slot=[],
               placed=[203], peaceful=TOWN, pair=[202, 592, 98], at=[12288, -3072, 800], pose=[12288, -2072, 2000]),
    'xd01': dict(title="Joe's Warehouse (XD-01)", foes=fam('rat', 'fly'), slot=[226], placed=[385], peaceful=[],
                 pair=[226, 385, 387], at=[250, -700, 128]),
    'xd02': dict(title='the Red Dwarf Mines (XD-02)', foes=fam('dwarf', 'spider', 'trog', 'bat'), slot=[205],
                 placed=[229, 412], peaceful=[], pair=[229, 401, 412], at=[13450, 3392, 0]),
    'xd03': dict(title='the Deep Mine (XD-03)', foes=fam('dwarf', 'spider', 'trog', 'bat'), slot=[412], placed=[229],
                 peaceful=[], pair=[229, 401, 412], at=[7790, 1000, 384]),
    'xd04': dict(title="the Witches' Tower (XD-04)", foes=fam('goblin', 'moon', 'bat'), slot=[272], placed=[214],
                 peaceful=[439, 430, 433, 442], pair=[433, 205, 214, 271], at=[-200, -1800, 0]),
    'xd05': dict(title='the Orc Caves (XD-05)', foes=fam('goblin', 'bat', 'spider'), slot=[205], placed=[273],
                 peaceful=[358], pair=[358, 271, 205, 400], at=[-650, 850, 0]),
    'xd06': dict(title='the Temple of Yak (XD-06)', foes=fam('moon', 'lich', 'skeleton') + [307, 308],
                 slot=[215, 289], placed=[307], peaceful=[], pair=[215, 289, 399], at=[-300, 1050, 0]),
    'xd12': dict(title="Darzog's Tower (XD-12)", foes=fam('golem', 'eye') + [293, 294], slot=[278, 293, 211],
                 placed=[294], peaceful=[292], pair=[292, 278, 211, 293], at=[2200, -1500, 0]),
    'xd21': dict(title="the Robbers' Den (XD-21)", foes=fam('thief', 'leather'), slot=[407], placed=[408],
                 peaceful=[], pair=[407, 257], at=[-2400, 900, 0]),
    'xd27': dict(title='the Ogre Lair (XD-27)', foes=fam('ogre', 'wolf', 'ogre_mage'), slot=[86, 106],
                 placed=[592], peaceful=[], pair=[592, 86, 106], at=[-300, 1000, 0]),
}


def scenario(key, spec):
    playtest = yaml.safe_load(open(f'{R}/devdocs/xeen/briefs/{key}/L4/playtest.yml'))
    entry = next(step for step in playtest['steps'] if 'new_game_flow' in step)
    steps = [entry, {'setup_shortcut': {'kind': 'immortal', 'value': True}},
             {'note': 'The map entry events run (the build\'s evt:studio_relations sets the map\'s relations).'},
             {'advance_runtime': {'seconds': 2}}]
    # Mayor Gunther's errand on entering X1 (a window that holds the world still): closed first.
    steps += spec.get('after_entry', [])
    for kind in spec['foes']:
        steps.append({'assert': {'actor_count': {'monster_id': kind, 'hostile': False, 'max': 0}}})
    for kind in spec['slot'] + spec['placed']:
        steps.append({'assert': {'actor_count': {'monster_id': kind, 'hostile': True, 'min': 1}}})
    for kind in spec['peaceful']:
        steps.append({'assert': {'actor_count': {'monster_id': kind, 'hostile': True, 'max': 0}}})
    steps.append({'note': 'Kinds of the map side by side, nearer each other than the party (a monster takes the nearest '
                          'of its foes): they must not take each other on.'})
    if 'pose' in spec:
        steps.append({'set_pose': {'map': entry['new_game_flow']['start_map'], 'x': spec['pose'][0],
                                   'y': spec['pose'][1], 'z': spec['pose'][2], 'yaw_degrees': -90}})
        steps.append({'advance_runtime': {'seconds': 2}})
    steps.append({'console': {'line': 'arena trace on'}})
    x, y, z = spec['at']
    for index, kind in enumerate(spec['pair']):
        steps.append({'spawn_actor': {'monster_id': kind, 'x': x + 96 * index, 'y': y, 'z': z}})
    steps.append({'advance_runtime': {'seconds': 12}})
    steps.append({'assert': {'ai_trace': {'event': 'target', 'target': 'actor', 'max_count': 0, 'report': True}}})
    # The last one spawned (a foe) thought all the while: it took the party.
    steps.append({'assert': {'ai_trace': {'actor_index': 'last', 'event': 'target', 'target': 'party', 'min_count': 1}}})
    for kind in spec['pair']:
        steps.append({'assert': {'actor_count': {'monster_id': kind, 'hurt': True, 'max': 0}}})
    for kind in spec['peaceful']:
        steps.append({'assert': {'actor_count': {'monster_id': kind, 'hurt': True, 'max': 0}}})
    head = (f"# Hostility check of {spec['title']} (written by output/studio_cal/hostility/gen_hostility_tests.py; "
            "devdocs/xeen/ACT2_BUILD.md, \"Hostility pass\"):\n# its foes hostile to the party, its peaceful ones "
            "peaceful, its kinds not fighting each other.\n")
    return head + yaml.safe_dump({'id': f'xeen.{key}.l4.hostility',
                                  'title': f"{spec['title']}: foes hostile to the party, no fights among them",
                                  'world': 'mm7', 'mode': 'faithful', 'steps': steps},
                                 sort_keys=False, allow_unicode=True, width=120)


for key in sys.argv[1:] or SPECS:
    folder = (f'{R}/output/studio_cal/hostility/scenarios' if key == 'x2'
              else f'{R}/devdocs/xeen/briefs/{key}/L4')
    path = os.path.join(folder, 'playtest_hostility.yml' if key != 'x2' else 'x2_playtest_hostility.yml')
    open(path, 'w').write(scenario(key, SPECS[key]))
    print(path)
