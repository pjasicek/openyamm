"""Exercise the shared chest-take operation and compare actual saves before/after reload and map revisit."""
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
REVIEW = PROJECT / 'review/rewards'
STAGE = Path('/tmp/openyamm-brackenford-greywatch')
generation = json.loads((REVIEW / 'generation.json').read_text())
registry = json.loads((PROJECT / 'source/reward_registry.json').read_text())
cases = [case for case in generation['cases'] if case['run'] == 0]
steps = []
for case in cases:
    fixed = registry['maps'][case['map']]['fixed_by_chest'][case['chest_id']]
    case['taken_item'] = fixed
    name = case['checkpoint']
    other_map = 'lg02.blv' if case['map'] == 'lg01.odm' else 'lg01.odm'
    steps += [{'load_game': {'path': case['save']}},
              {'assert': {'item_received': {'item_id': fixed, 'source': 'chest',
                                           'chest_id': case['chest_id'], 'destination': 'held'}}},
              {'assert': {'held_item': {'active': True, 'item_id': fixed}}},
              {'press_action': {'action': 'escape'}}, {'save_game': name + '_taken'},
              {'load_game': name + '_taken'},
              {'assert': {'held_item': {'active': True, 'item_id': fixed}}},
              {'save_game': name + '_reloaded'},
              {'assert': {'held_item': {'active': False, 'item_id': fixed}}},
              {'assert': {'inventory_any_member': [{'item_id': fixed, 'count': 1}]}},
              {'load_map': {'map': other_map}}, {'load_map': {'map': case['map']}},
              {'set_pose': case['pose']}, {'press_interact': {}},
              {'assert': {'chest_opened': {'chest_id': case['chest_id']}}},
              {'save_game': name + '_revisited'}]
scenario_id = 'levelgen_reward_persistence'
source = REVIEW / 'persistence.yml'
source.write_text(yaml.safe_dump(dict(id=scenario_id, world='mm8', mode='faithful', steps=steps), sort_keys=False))
with (REVIEW / 'persistence.log').open('w') as stream:
    subprocess.run([str(ROOT/'build/game/openyamm'), '--world', 'mm8', '--headless-run-scenario', str(source),
                    '--scenario-no-color'], cwd=STAGE, stdout=stream, stderr=subprocess.STDOUT, check=True)
for case in cases:
    views = []
    for suffix in ['taken', 'reloaded', 'revisited']:
        save = Path('/tmp/openyamm_scenario_saves') / scenario_id / (case['checkpoint'] + '_' + suffix + '.oysav')
        text = subprocess.check_output([str(ROOT/'build/tools/openyamm_levelgen_inspect_save'), str(save)], text=True)
        snapshot = yaml.safe_load(text)
        (REVIEW / (save.stem + '.yml')).write_text(text)
        if suffix == 'revisited':
            assert not snapshot['held_item_active']
            owned = [item for member in snapshot['party'] for item in member['inventory']
                     if item['item_id'] == case['taken_item']]
            assert len(owned) == 1 and owned[0]['quantity'] == 1
        else:
            assert snapshot['held_item_active'] and snapshot['held_item_id'] == case['taken_item']
        kind = 'outdoor' if case['map'].endswith('.odm') else 'indoor'
        chests = snapshot[kind]['materialized_chests']
        view = next(chest for chest in chests if chest['id'] == case['chest_id'])
        assert all(item['item_id'] != case['taken_item'] for item in view['items'] + view['hidden_items'])
        views.append(view)
    assert views[0] == views[1] == views[2], 'Chest contents changed without refill'
report = dict(passed=True, chests=8, taken_items=[case['taken_item'] for case in cases],
              binary_sha256=hashlib.sha256((ROOT/'build/game/openyamm').read_bytes()).hexdigest(),
              scope='Existing scenario chest-take adapter calls shared native chest removal, holds the real item and '
                    'persists it. Saved chest contents remain identical after reload and direct map unload/revisit. '
                    'This is not a cursor placement test or continuous travel/combat route; timed refill is separate.')
(REVIEW/'persistence.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: eight chest removals, held-item save/load and unchanged rewards on ordinary map revisit.')
