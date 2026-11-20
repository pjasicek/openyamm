"""Exercise real native doors and unchanged MM8 ambient-topic responses.

Expected text comes from audited original handlers, independently of runtime output.
The existing scenario hash includes one newline after each dialog line.
"""
import json
from pathlib import Path
import re
import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
registry = json.loads((PROJECT/'source/town_registry.json').read_text())
lua = (ROOT/'assets_dev/engine/events/Global.lua').read_text(encoding='cp1252')
handlers = {int(m[1]): m[0] for m in re.finditer(
    r'RegisterGlobalEvent\((\d+),.*?(?=\nRegisterGlobalEvent|\Z)', lua, re.S)}
steps = [{'new_game_flow': {'start_map': 'lg01.odm'}}]
count = 0
for house in registry['houses']:
    npc = house['npc']
    if not npc:
        continue
    for topic in npc['topics']:
        if topic['behavior']['kind'] != 'existing_message_only_global_handler':
            continue
        quoted = re.search(r'evt\.SetMessage\(("(?:\\.|[^"\\])*")\)', handlers[topic['id']])[1]
        message = json.loads(quoted)
        value = 1469598103934665603
        for byte in (message+'\n').encode('cp1252'):
            value = ((value ^ byte)*1099511628211) & ((1 << 64)-1)
        x, y, z = house['door_position']
        nx, ny = house['door_outward']
        steps += [
            {'set_pose': {'map': 'lg01.odm', 'x': x+nx*192, 'y': y+ny*192, 'z': z,
                          'yaw': house['approach_yaw'], 'pitch': 0}},
            {'press_interact': {}},
            {'select_topic': {'action_id': topic['id']}},
            {'assert': {'dialog': {'active': True, 'house_dialog': False,
                                  'source_id': npc['instance_id'], 'title': npc['name'],
                                  'text_hash': str(value)}}},
            {'press_action': {'action': 'escape'}},
        ]
        count += 1
scenario = {'id': 'levelgen.brackenford.ambient_topics',
            'title': 'Native house conversations preserve existing MM8 ambient text',
            'world': 'mm8', 'mode': 'faithful', 'steps': steps}
(PROJECT/'town_topics.yml').write_text(yaml.safe_dump(scenario, sort_keys=False))
print(json.dumps({'ambient_topics': count, 'steps': len(steps)}))
