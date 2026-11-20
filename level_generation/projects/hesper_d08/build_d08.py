"""Compile and stage D8's authored source; all output stays in this project or the Hesper stage."""
import csv
import json
import shutil
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build

semantic = json.loads((PROJECT / 'source/hes_d08.semantic.json').read_text())
with (ROOT / 'design/kreegan_world/data/monster_data.txt').open(newline='') as stream:
    rows = {int(r[0]): r for r in csv.reader(stream, delimiter='\t') if r and r[0].isdigit()}
sizes = {m['id']: (m['radius'], m['height']) for m in
         yaml.safe_load((PROJECT.parent / 'hesper_stage/monsters.yml').read_text())['monsters']}
actors = []
for a in semantic['actors']:
    monster, row = a['monster'], rows[a['monster']]
    radius, height = sizes[monster]
    x, y, z = a['position']
    actors.append({'actor_index': len(actors), 'name': row[1], 'npc_id': 0, 'attributes': 0, 'hp': int(row[4]),
                   'hostility_type': int(row[12]), 'monster_info_id': monster, 'monster_id': monster,
                   'radius': radius, 'height': height, 'move_speed': 0 if a['posted'] else int(row[13]),
                   'position': {'x': x, 'y': y, 'z': z}, 'immobile': a['posted'],
                   'initial_yaw_units': round(a['yaw_degrees'] % 360 / 360 * 2048) % 2048,
                   'sprite_ids': [0, 0, 0, 0], 'sector_id': a['sector'], 'current_action_animation': 0,
                   'carried_item_id': 0, 'group': a['group'], 'ally': 0, 'unique_name_index': 0})

# The Scour is a separate build dependency. Do not invent an outdoor height or a substitute destination.
out2_path = PROJECT.parent / 'hesper_out2/out2_build.json'
exit_lua = 'evt.StatusText("Beyond the Slag Gate the way is not yet open.")'
if out2_path.exists():
    out2 = json.loads(out2_path.read_text())
    arrival = out2['arrivals']['d08_return']
    x, y, z = arrival['position']
    direction = round(arrival['direction_degrees'] / 360 * 2048) % 2048
    exit_lua = f'evt.MoveToMap({x}, {y}, {z}, {direction}, 0, 0, 0, 0, "hes_out2.odm")'

report = build(PROJECT, 'hes_d08.blv', {
    'BOSS_ACTOR': str(semantic['boss_actor']), 'SCOUR_EXIT': 'function() ' + exit_lua + ' end'},
    arrival='d08_slag_gate', actors=actors, chests=[
        {'name': 'unused container zero', 'random': False, 'gold': 0},
        # The chests' Engrams are Engram Cores (CR-INT-1: the Engram supply +20 %).
        {'name': 'Chest A', 'fixed': [11008, 11332, 11332], 'random': False, 'gold': 25000},
        {'name': 'Chest B', 'fixed': [11224, 11332, 11375], 'random': False, 'gold': 0},
        {'name': 'Chest C', 'fixed': [11477, 11102, 11105, 11332], 'random': False, 'gold': 0},
        *[{'name': name, 'gold': 9000} for name in
          ('Furnace Bank pod', 'Mould Shop pod', 'Slag Sump pod', 'Foundryman locker', 'Coolant Plant locker')]])

runtime = PROJECT / 'runtime'
scene_path = runtime / 'hes_d08.scene.yml'
scene = json.loads(scene_path.read_text())
for chest in scene['loot_containers'][4:]:
    chest['random_treasure_level'] = 6  # shortcut: native T6 loot until Hesper's H3 pool is integrated.
for chest in scene['loot_containers'][1:7]:
    chest['presentation'] = 'kreegan pod'
scene_path.write_text(json.dumps(scene, indent=2) + '\n')
shutil.copy2(scene_path, runtime / 'worlds/hesper/maps/hes_d08.scene.yml')
boss = runtime / 'worlds/hesper/behaviors/bosses/forgemaster.lua'
boss.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(PROJECT / 'source/forgemaster.lua', boss)
report.update({'outdoor_arrival_available': out2_path.exists(), 'actors': len(actors),
               'boss_actor': semantic['boss_actor']})
(PROJECT / 'd08_build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
