"""Compile D1 Starport Terminal and assemble its scene and Lua into runtime/worlds/hesper, the tree the shared Hesper
stage installs (level_generation/projects/hesper_stage/stage.py; assets_dev is never modified).

Run the locked commands in README.md.
"""
import csv
import json
import shutil
import struct
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build  # noqa: E402

semantic = json.loads((PROJECT / 'source/hes_d01.semantic.json').read_text())
raw = (PROJECT / 'source/hes_d01.glb').read_bytes()
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
        actors.append(dict(actor_index=len(actors), name=row[1], npc_id=0, attributes=0, hp=int(row[4]),
                           hostility_type=int(row[12]), monster_info_id=monster, monster_id=monster,
                           radius=binding['radius'], height=binding['height'], move_speed=int(row[13]),
                           position=dict(x=x, y=y, z=z), initial_yaw_units=round(yaw / 360 * 2048) % 2048,
                           immobile=posted, sprite_ids=[0, 0, 0, 0], sector_id=rooms.index('room_' + room) + 1,
                           current_action_animation=0, carried_item_id=0, group=index + 1, ally=0,
                           unique_name_index=0))


# Spread each pack about its plan mark, clear of the carousels, counters, catwalk edges and existing props.
pack(0, [10050]*3, 'concourse_w', 180, [(-160, 0), (0, 120), (160, 0)])
pack(1, [10050]*3, 'concourse_e', 180, [(-160, 0), (0, 120), (160, 0)])
pack(2, [10054]*2, 'customs', 0, [(0, -150), (0, 150)], posted=True)
pack(3, [10050]*3, 'customs', 180, [(0, -120), (0, 0), (0, 120)])
pack(4, [10090]*5, 'claim', 0, [(0, 120*k) for k in range(-2, 3)])
pack(5, [10050]*6, 'sorting', 180, [(x, y) for y in (-100, 100) for x in (-150, 0, 150)])
pack(6, [10054]*2, 'plant_n', -768, [(-220, 0), (220, 0)], yaw=270, posted=True)
pack(7, [10050]*4, 'plant_s', -588, [(120*k-180, 0) for k in range(4)], yaw=90)
pack(8, [10090]*3, 'service', -768, [(-120, 0), (0, 0), (120, 0)])
pack(9, [10050]*3, 'tower', 948, [(-160, 0), (0, 120), (160, 0)], yaw=270)
pack(10, [10000]*4 + [10050]*3, 'concourse_c', 0,
     [(-90, -90), (90, -90), (-90, 90), (90, 90), (-180, 150), (0, 150), (180, 150)], yaw=0)
for actor in actors[-3:]:
    actor['position']['z'] = 180
pack(11, [10100], 'dc_n', -768, [(0, 0)], yaw=0, posted=True)
assert len(actors) == 42 and all(int(rows[a['monster_id']][3]) <= 90 for a in actors)

out1 = json.loads((PROJECT.parent / 'hesper_out1/out1_build.json').read_text())
x, y, z, degrees = out1['terminal_arrival']
report = build(PROJECT, 'hes_d01.blv', {'TERMINAL_ARRIVAL': f'{x}, {y}, {z}, {round(degrees / 360 * 2048) % 2048}, 0, 0, 0, 0'},
      arrival='apron_doors', actors=actors, chests=[
          # Chest A (P4's ITEM_PLACEMENT, follow-up 44): an Engram, 2 Shield Cells, the Drone Control Duty Log (11373);
          # the Militia Warrant (11488) waits for its voucher lesson (not staged).
          {'name': 'chest A (Security)', 'fixed': [11331, 11300, 11300, 11373], 'random': False, 'gold': 0},
          'chest B (Control Tower)', 'luggage locker', 'luggage locker', 'lost luggage', 'maintenance locker',
          # The cache before Drone Control (follow-up 28).
          {'name': 'cache (Power Plant)', 'fixed': [11300, 11300, 11302], 'random': False, 'gold': 0}])

# The Custodian's default behaviour (behaviors.yml names it; the stage installs the runtime tree).
behavior = PROJECT / 'runtime/worlds/hesper/behaviors/bosses/custodian.lua'
behavior.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(PROJECT / 'source/custodian.lua', behavior)
report.update(actors=len(actors), actor_records=actors)
(PROJECT / 'd01_build.json').write_text(json.dumps(report, indent=2) + '\n')
