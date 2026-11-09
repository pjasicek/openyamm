"""Inspect actual random rewards from three fresh sessions per map using native saved runtime state.

The ordinary party picks every chest through its real face. Explicit review poses isolate reward generation
from the combat route. No seeded inventory, direct event dispatch or patched native save is used.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import yaml
from build_outdoor_content import terrain_height

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
STAGE = Path('/tmp/openyamm-brackenford-greywatch')
REVIEW = PROJECT / 'review/rewards'
REVIEW.mkdir(parents=True, exist_ok=True)
party = json.loads((PROJECT / 'source/baseline_party.json').read_text())
terrain = bytes.fromhex(json.loads((PROJECT / 'source/lg01.terrain.yml').read_text())['height_map_hex'])
steps = []
cases = []
policies = json.loads((PROJECT / 'source/reward_registry.json').read_text())
for map_file in ['lg01.odm', 'lg02.blv']:
    scene = json.loads((PROJECT / 'runtime/worlds/mm8/maps' / (Path(map_file).stem + '.scene.yml')).read_text())
    for run in range(3):
        steps.append({'new_game_flow': {'start_map': map_file, 'party': party}})
        for chest in scene['loot_containers']:
            x, y, z = [chest['position'][k] for k in 'xyz']
            y -= 256
            if map_file.endswith('.odm'):
                z = terrain_height(x, y, terrain)
            name = Path(map_file).stem + '_' + str(run) + '_' + str(chest['container_id'])
            pose = dict(map=map_file, x=x, y=y, z=z, yaw=math.pi/2, pitch=-0.55)
            # Baseline Expert7 Disarm is below these maps' doubled disarm threshold. The first
            # click discharges the one-shot chest trap; the second opens the now-safe chest.
            steps += [{'set_pose': pose}, {'press_interact': {}}, {'save_game': name + '_trap'},
                      {'press_interact': {}},
                      {'assert': {'chest_opened': {'chest_id': chest['container_id']}}},
                      {'save_game': name}, {'press_action': {'action': 'escape'}}]
            cases.append(dict(map=map_file, run=run, chest_id=chest['container_id'], checkpoint=name, pose=pose))
scenario_id = 'levelgen_chest_generation'
scenario = dict(id=scenario_id, world='mm8', mode='faithful', steps=steps)
source = REVIEW / 'generation.yml'
source.write_text(yaml.safe_dump(scenario, sort_keys=False))
with (REVIEW / 'generation.log').open('w') as stream:
    subprocess.run([str(ROOT / 'build/game/openyamm'), '--world', 'mm8', '--headless-run-scenario', str(source),
                    '--scenario-no-color'], cwd=STAGE, stdout=stream, stderr=subprocess.STDOUT, check=True)
for case in cases:
    save = Path('/tmp/openyamm_scenario_saves') / scenario_id / (case['checkpoint'] + '.oysav')
    process = subprocess.run([str(ROOT / 'build/tools/openyamm_levelgen_inspect_save'), str(save)],
                             capture_output=True, text=True, check=True)
    snapshot = yaml.safe_load(process.stdout)
    (REVIEW / (case['checkpoint'] + '.yml')).write_text(process.stdout)
    kind = 'outdoor' if case['map'].endswith('.odm') else 'indoor'
    view = snapshot[kind]['active_chest']
    assert view['id'] == case['chest_id'] and view['items']
    policy = policies['maps'][case['map']]
    fixed = policy['fixed_by_chest'][case['chest_id']]
    equipment = [item for item in view['items'] + view['hidden_items'] if not item['is_gold'] and item['item_id'] != 770]
    assert len(equipment) == policy['draws'] + 1
    assert fixed in [item['item_id'] for item in equipment]
    assert all(item['item_id'] in policy['pool'] + [fixed] for item in equipment)
    trap_save = save.with_name(save.stem + '_trap.oysav')
    trap = yaml.safe_load(subprocess.check_output([str(ROOT / 'build/tools/openyamm_levelgen_inspect_save'),
                                                  str(trap_save)], text=True))
    trap_health = [member['health'] for member in trap['party']]
    assert trap_health == [member['health'] for member in snapshot['party']], 'Opening retriggered chest damage'
    case.update(seed=snapshot[kind]['chest_seed'], items=view['items'], hidden_items=view['hidden_items'],
                health_after_trap=trap_health, equipment_count=len(equipment),
                save_sha256=hashlib.sha256(save.read_bytes()).hexdigest(), save=str(save))
for map_file in ['lg01.odm', 'lg02.blv']:
    seeds = {case['seed'] for case in cases if case['map'] == map_file}
    assert len(seeds) == 3, (map_file, seeds)
report = dict(cases=cases, passed=True, binary_sha256=hashlib.sha256((ROOT/'build/game/openyamm').read_bytes()).hexdigest(),
              scope='24 real chest openings: four chests, three fresh seeds per map. Contents inspection; '
                    'Guaranteed and random equipment stays in the explicit MM8 pool; second opening causes no '
                    'additional chest damage. Loot removal, refill/revisit and combat routes are separate checks.',
              source_hashes={name: hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() for name in
                            ['source/reward_registry.json', 'runtime/worlds/mm8/maps/lg01.scene.yml',
                             'runtime/worlds/mm8/maps/lg02.scene.yml']})
(REVIEW / 'generation.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS: 24 chest openings and native saved contents across three fresh seeds per map.')
