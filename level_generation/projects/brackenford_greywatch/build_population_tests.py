"""Generate population checks from authored placement and immutable MM8 monster stats.

These are initial-load/AI diagnostics, not the required equipped level-25 town-route/combat acceptance run.
"""
import json
from pathlib import Path
import yaml
from build_outdoor_content import table, terrain_height

PROJECT = Path(__file__).resolve().parent
content = json.loads((PROJECT/'source/lg01.content.json').read_text())
samples = bytes.fromhex(json.loads((PROJECT/'source/lg01.terrain.yml').read_text())['height_map_hex'])
stats = table('monster_data.txt')
checks = []
for actor in content['actors']:
    entry = stats[actor['monster_id']]
    checks.append({'assert': {'actor_visible': {
        'actor_index': actor['actor_index'], 'monster_id': actor['monster_id'], 'name': entry[1],
        'dead': False, 'current_hp': int(entry[4]), 'max_hp': int(entry[4]),
        'hostile_to_party': actor['actor_index'] >= 29,
        'has_detected_party': False, 'combat_targeting_party': False}}})
steps = [{'new_game_flow': {'start_map': 'lg01.odm'}},
         {'set_pose': {'map': 'lg01.odm', 'x': -10000, 'y': 2048,
                       'z': terrain_height(-10000,2048,samples), 'yaw': 0, 'pitch': 0}}]
steps += checks + [{'advance_runtime': {'seconds': 30}}] + checks
for item in content['world_items']:
    steps.append({'assert': {'item_visible': {'source': 'world_item', 'item_id': item['item_id']}}})


def write(name, title, steps):
    data = {'id': 'levelgen.brackenford.'+name, 'title': title, 'world': 'mm8', 'mode': 'faithful', 'steps': steps}
    (PROJECT/(name+'.yml')).write_text(yaml.safe_dump(data,sort_keys=False))


write('town_population_smoke', '43 real MM8 actors; thirty seconds of active AI at the square', steps)
write('wilderness_ai_control', 'Approaching the wilderness activates the authored ogre pack', [
    {'new_game_flow': {'start_map': 'lg01.odm'}},
    {'set_pose': {'map': 'lg01.odm', 'x': 18048, 'y': 3328, 'z': terrain_height(18048,3328,samples),
                  'yaw': 0, 'pitch': 0}},
    {'advance_runtime': {'seconds': 1}},
    {'assert': {'actor_visible': {'actor_index': 29, 'monster_id': 32, 'dead': False,
                                  'hostile_to_party': True, 'has_detected_party': True,
                                  'combat_targeting_party': True}}},
])
