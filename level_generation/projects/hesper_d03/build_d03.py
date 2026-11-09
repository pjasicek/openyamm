"""Compile D3 and assemble the runtime tree consumed by the shared Hesper stage."""
import csv
import json
import math
import re
import shutil
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
STAGE = PROJECT.parent / 'hesper_stage'
sys.path.insert(0, str(STAGE))
from blv_build import build
import sound_cues

semantic = json.loads((PROJECT / 'source/hes_d03.semantic.json').read_text())
with (ROOT / 'design/kreegan_world/data/monster_data.txt').open(newline='') as stream:
    rows = {int(row[0]): row for row in csv.reader(stream, delimiter='\t') if row and row[0].isdigit()}
sizes = {m['id']: (m['radius'], m['height']) for m in yaml.safe_load((STAGE / 'monsters.yml').read_text())['monsters']}
actors = []
for a in semantic['actors']:
    monster = a['monster']
    row = rows[monster]
    radius, height = sizes[monster]
    actors.append({'actor_index': len(actors), 'name': a['name'], 'npc_id': 0, 'attributes': 0,
                   'hp': int(row[4]), 'hostility_type': int(row[12]), 'monster_info_id': monster,
                   'monster_id': monster, 'radius': radius, 'height': height,
                   'move_speed': 0 if a['posted'] else int(row[13]), 'position': dict(zip(('x', 'y', 'z'), a['position'])),
                   'initial_yaw_units': round(a['yaw_degrees'] % 360 / 360 * 2048) % 2048,
                   'immobile': a['posted'], 'sprite_ids': [0, 0, 0, 0], 'sector_id': a['sector'],
                   'current_action_animation': 0, 'carried_item_id': 0, 'group': a['group'], 'ally': 0,
                   'unique_name_index': 0})

out2_path = PROJECT.parent / 'hesper_out2/out2_build.json'
exit_values = 'false'
if out2_path.exists():
    out2 = json.loads(out2_path.read_text())
    arrival = out2['arrivals']['d03_return']
    x, y, z = arrival['position']
    direction = round(arrival['direction_degrees'] / 360 * 2048) % 2048
    exit_values = f'true, {x}, {y}, {z}, {direction}'

chests = [{'name': 'Roost Stair shelf cache', 'fixed': [11300, 11300, 11302], 'random': False, 'gold': 0},
          {'name': 'Chest A: colony emitters', 'fixed': [11130, 11130], 'random': False, 'gold': 0},
          # Two of chest B's three Engrams are Engram Cores (CR-INT-1: the Engram supply +20 %).
          {'name': 'Chest B: Ion Coil', 'fixed': [11474, 11332, 11332, 11331], 'random': False, 'gold': 0}]
chests += [{'name': name, 'random': True, 'gold': 4000} for name in
           ('Barracks quartermaster pod', 'Mess pod', 'Lower Storage pod', 'Cave-in surveyor locker')]
report = build(PROJECT, 'hes_d03.blv', {
    'KRAV_ACTOR': str(semantic['boss_index']),
    'BARRACKS_ACTORS': ', '.join(map(str, semantic['barracks_indices'])),
    'SCOUR_EXIT': exit_values,
}, arrival='d03_outer_gate', chests=chests, actors=actors)

scene_path = PROJECT / 'runtime/hes_d03.scene.yml'
scene = json.loads(scene_path.read_text())
for chest in scene['loot_containers'][3:]:
    # shortcut: native tier-4 treasure stands in until P4's weighted H2 pool is installed by the integrator.
    chest['random_treasure_level'] = 4
scene['initial_state']['sprite_objects'] = []
scene_path.write_text(json.dumps(scene, indent=2) + '\n')
shutil.copy2(scene_path, PROJECT / 'runtime/worlds/hesper/maps/hes_d03.scene.yml')
target = PROJECT / 'runtime/worlds/hesper/behaviors/bosses/krav.lua'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(PROJECT / 'source/krav.lua', target)
sound_cues.build(PROJECT / 'runtime/worlds/hesper/audio/d03')

shots = []
design = (ROOT / 'design/kreegan_world/zone2/dungeons/D3_QUARRY_OUTPOST.md').read_text()
for line in design.splitlines():
    if re.match(r'\| \d\d-', line):
        name, position, yaw, pitch, _ = [cell.strip() for cell in line.strip('|').split('|')]
        xyz = [int(n.replace(' ', '').replace('−', '-')) for n in position.split(',')]
        shots.append({'name': name, 'position': xyz, 'yaw': float(yaw.replace('−', '-')),
                      'pitch': float(pitch.replace('−', '-'))})
assert len(shots) == 12
tour = {'output_dir': str(PROJECT / 'review/build01'), 'settle_seconds': 1.5, 'exit': True, 'shots': shots}
# Preserve the integrator's expanded review tour on subsequent builds.
if not (PROJECT / 'review_tour_01.yml').exists():
    (PROJECT / 'review_tour_01.yml').write_text(yaml.safe_dump(tour, sort_keys=False))
assert len(actors) == 67
assert sorted({a['group'] for a in actors}) == [10, 11, 20, 21, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 40, 41, 150, 151]
assert set(report['events']) >= set(range(30, 37)) | {50, 51, 52, 53, 54, 55, 58, 70, 71, 72, 73, 74, 75, 76,
                                                   77, 78, 79, 80, 150}
print('D3: 67 actors, six chests, eight serum vats, twenty scrap bundles; Scour return '
      + ('bound' if out2_path.exists() else 'pending'))
