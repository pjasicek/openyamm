"""Compile D2 Pumping Station and assemble its scene and Lua into runtime/worlds/hesper, the tree the shared Hesper
stage installs (level_generation/projects/hesper_stage/stage.py; assets_dev is never modified).

Run the locked commands in README.md.
"""
import csv
import json
import struct
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build  # noqa: E402


def move(position, degrees):
    x, y, z = position
    return f'{x}, {y}, {z}, {round(degrees / 360 * 2048) % 2048}, 0, 0, 0, 0'


semantic = json.loads((PROJECT / 'source/hes_d02.semantic.json').read_text())
raw = (PROJECT / 'source/hes_d02.glb').read_bytes()
gltf = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
rooms = [gltf['nodes'][i]['name'].lower() for i in gltf['scenes'][gltf.get('scene', 0)]['nodes']
         if gltf['nodes'][i]['name'].startswith('ROOM_')]
assert rooms == sorted(semantic['sectors'])
with (PROJECT.parents[2] / 'design/kreegan_world/data/monster_data.txt').open() as stream:
    rows = {int(r[0]): r for r in csv.reader(stream, delimiter='\t') if r and r[0].isdigit()}
bindings = {m['id']: m for m in yaml.safe_load((PROJECT.parent / 'hesper_stage/monsters.yml').read_text())['monsters']}
actors = []


def pack(index, monsters, room, z, offsets, yaw=180, posted=False):
    mark = semantic['monster_packs'][index]
    assert len(monsters) == len(offsets) == mark['count'], mark
    for monster, (dx, dy) in zip(monsters, offsets):
        row, binding = rows[monster], bindings[monster]
        x, y = mark['position'][0] + dx, mark['position'][1] + dy
        floor_z = z(x, y) if callable(z) else z
        actors.append(dict(actor_index=len(actors), name=row[1], npc_id=0, attributes=0, hp=int(row[4]),
                           hostility_type=int(row[12]), monster_info_id=monster, monster_id=monster,
                           radius=binding['radius'], height=binding['height'], move_speed=int(row[13]),
                           position=dict(x=x, y=y, z=floor_z), initial_yaw_units=round(yaw / 360 * 2048) % 2048,
                           immobile=posted, sprite_ids=[0, 0, 0, 0], sector_id=rooms.index('room_' + room) + 1,
                           current_action_animation=0, carried_item_id=0, group=index + 1, ally=0,
                           unique_name_index=0))


# Gallery packs follow the walkway axes; the Queen and pups stand on the actual 32-unit filter beds.
pack(0, [10090]*4, 'gal_w', 0, [(x, y) for y in (0, 140) for x in (-70, 70)], yaw=90)
pack(1, [10090]*3, 'gal_n', 0, [(-120, 0), (0, 0), (120, 0)])
pack(2, [10091]*3, 'pump', -256, [(-150, 0), (0, 0), (150, 0)])
pack(3, [10050]*2, 'pump', -76, [(-100, 0), (100, 0)])
pack(4, [10080]*3, 'filters', lambda x, y: -224 if 7374 <= x <= 8624 else -256,
     [(-180, 0), (0, 0), (180, 0)])
pack(5, [10101], 'filters', -224, [(0, 0)])
pack(6, [10090]*4, 'cistern', -768, [(x, y) for y in (-100, 100) for x in (-100, 100)])
# The deep-drain wildlife shares the sump's release, well below the Queen's Filter Beds.
semantic['monster_packs'].append({'position': [3500, 1848], 'count': 5})
pack(7, [10320]*5, 'cistern', -768, [(-150, -150), (150, -150), (0, 0), (-150, 150), (150, 150)])
assert len(actors) == 25 and {a['monster_id'] for a in actors} == {10090, 10091, 10050, 10080, 10101, 10320}

out1 = json.loads((PROJECT.parent / 'hesper_out1/out1_build.json').read_text())
lowhold = json.loads((PROJECT.parent / 'hesper_undervault/source/hes_undervault.semantic.json').read_text())
works = lowhold['arrivals']['water_works']
report = build(PROJECT, 'hes_d02.blv', {'CANYON_ARRIVAL': move(out1['station_arrival'][:3], out1['station_arrival'][3]),
                               'UNDERVAULT_WORKS': move(works['position'], works['direction_degrees'])},
      arrival='canyon_gate', actors=actors, chests=[
          # P4's ITEM_PLACEMENT: the sunken locker an Engram and 10 000 gold; the drowned worker the Rebreather Helm
          # (11106, follow-up 29); the cache before the Filter Beds 2 Shield Cells and a Stim (follow-up 28).
          {'name': 'sunken locker', 'fixed': [11331], 'random': False, 'gold': 10000}, 'tool locker',
          'filter-bed locker', {'name': 'drowned worker', 'fixed': [11106], 'random': False, 'gold': 0},
          {'name': 'cache (Pump Hall)', 'fixed': [11300, 11300, 11302], 'random': False, 'gold': 0}])

report.update(actors=len(actors), actor_records=actors)
(PROJECT / 'd02_build.json').write_text(json.dumps(report, indent=2) + '\n')
