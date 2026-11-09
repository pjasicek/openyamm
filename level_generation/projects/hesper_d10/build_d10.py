"""Compile D10, bind its reviewed content, and stage its own runtime tree."""
import csv
import importlib.util
import json
import shutil
import struct
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build

spec = importlib.util.spec_from_file_location('plans', ROOT / 'design/kreegan_world/zone1/dungeons/make_dungeon_plans.py')
plans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plans)
budget = plans.budget(plans.d10)
assert not plans.ceiling_problems(plans.d10) and not plans.stacking_problems(plans.d10)
assert budget['max_lights_at_a_point'] <= 4
semantic = json.loads((PROJECT / 'source/hes_d10.semantic.json').read_text())
glb = (PROJECT / 'source/hes_d10.glb').read_bytes()
chunk_length = struct.unpack_from('<I', glb, 12)[0]
gltf = json.loads(glb[20:20 + chunk_length])
room_nodes = [gltf['nodes'][i]['name'].lower() for i in gltf['scenes'][gltf['scene']]['nodes']
              if gltf['nodes'][i]['name'].startswith('ROOM_')]
assert room_nodes == sorted(semantic['sectors']), room_nodes
with (ROOT / 'design/kreegan_world/data/monster_data.txt').open(newline='') as stream:
    rows = {int(r[0]): r for r in csv.reader(stream, delimiter='\t') if r and r[0].isdigit()}
sizes = {m['id']: (m['radius'], m['height']) for m in
         yaml.safe_load((PROJECT.parent / 'hesper_stage/monsters.yml').read_text())['monsters']}
# Native wildlife stays behind the southern stacks and in the sealed vault hall, away from the machines.
for group, room, points in [
        (5, 'stacks_b', [(6660, 150, 0), (6960, 150, 0), (7260, 150, 0), (7560, 150, 0)]),
        (6, 'hall_a', [(-1500, -3600, -512), (-1200, -3600, -512),
                       (-1500, -3300, -512), (-1200, -3300, -512)])]:
    for position in points:
        semantic['actors'].append(dict(monster=10321, position=position, group=group, posted=False,
                                        yaw_degrees=90, sector=room_nodes.index('room_' + room) + 1))
actors = []
for a in semantic['actors']:
    monster, row = a['monster'], rows[a['monster']]
    radius, height = sizes[monster]
    x, y, z = map(round, a['position'])
    actors.append({'actor_index': len(actors), 'name': row[1], 'npc_id': 0, 'attributes': 0, 'hp': int(row[4]),
                   'hostility_type': int(row[12]), 'monster_info_id': monster, 'monster_id': monster,
                   'radius': radius, 'height': height, 'move_speed': 0 if a['posted'] else int(row[13]),
                   'position': dict(x=x, y=y, z=z), 'immobile': a['posted'],
                   'initial_yaw_units': round(a['yaw_degrees'] % 360 / 360 * 2048) % 2048,
                   'sprite_ids': [0, 0, 0, 0], 'sector_id': a['sector'], 'current_action_animation': 0,
                   'carried_item_id': 0, 'group': a['group'], 'ally': 0, 'unique_name_index': 0})

# out1 has no archive_arrival record yet. Read its exported event-13 door geometry, never typed outdoor coordinates.
out1 = PROJECT.parent / 'hesper_out1/source'
geometry = json.loads((out1 / 'hes_out1.geometry.yml').read_text())
scene = json.loads((out1 / 'hes_out1.scene.yml').read_text())
entry = next(f for f in scene['bmodel_faces']['interactive_faces'] if f['cog_triggered_number'] == 13)
model = next(m for m in geometry['bmodels'] if m['runtime_bmodel_index'] == entry['bmodel_index'])
assert model['geometry_id'] == 'hes_out1:archive_dome'
vertices, faces = [], []
for line in Path(model['source']['asset_path']).read_text().splitlines():
    fields = line.split()
    if fields and fields[0] == 'v':
        vertices.append([float(v) * model['source']['scale'] for v in fields[1:4]])
    elif fields and fields[0] == 'f':
        faces.append([vertices[int(v.split('/')[0]) - 1] for v in fields[1:]])
face = faces[entry['face_index']]
assert len(face) == 4
# This authored porch faces south; verify that exported face before stepping away from it.
assert max(v[1] for v in face) - min(v[1] for v in face) < 0.1
arrival = dict(position=[round(sum(v[0] for v in face) / 4), round(face[0][1] - 500),
                         round(min(v[2] for v in face))], direction_degrees=270)
exit_values = ', '.join(map(str, [*arrival['position'], 1536, 0, 0, 0, 0]))
report = build(PROJECT, 'hes_d10.blv', {'ARCHIVE_RETURN': exit_values}, arrival='dome_stair', actors=actors, chests=[
    {'name': 'Reading-room locker (H3)', 'gold': 9000}, {'name': 'Stacks locker (H3)', 'gold': 9000},
    {'name': 'Founders casket', 'fixed': [11481, 11332, 11331, 11331, 11331], 'gold': 0, 'random': False}])
runtime = PROJECT / 'runtime'
scene_path = runtime / 'hes_d10.scene.yml'
scene = json.loads(scene_path.read_text())
for chest in scene['loot_containers'][:2]:
    chest['random_treasure_level'] = 6  # shortcut: native T6 until the shared Hesper H3 loot pool exists.
scene['loot_containers'][2]['presentation'] = 'founders casket'
stage = ROOT / 'output/hesper_stage/assets_editor_dev'
with (stage / 'engine/data_tables/items.txt').open(encoding='latin1', newline='') as stream:
    items = {int(r[0]): r for r in csv.reader(stream, delimiter='\t') if r and r[0].isdigit()}
# World contributions carry the new item ids; their borrowed ground objects resolve through the engine table.
with (stage / 'worlds/hesper/data_tables/items.txt').open(encoding='latin1', newline='') as stream:
    items.update({int(r[0]): r for r in csv.reader(stream, delimiter='\t') if r and r[0].isdigit()})
objects = [int(line.split('\t')[2]) for line in (stage / 'engine/data_tables/object_list.txt')
           .read_text(encoding='latin1').splitlines()[1:] if line.strip()]
scene['initial_state']['sprite_objects'] = []
for ground in semantic['ground_items']:
    item = bytearray(36)
    struct.pack_into('<I', item, 0, ground['item'])
    struct.pack_into('<I', item, 12, ground.get('amount', 0))
    sprite = int(items[ground['item']][11])
    x, y, z = ground['position']
    scene['initial_state']['sprite_objects'].append({
        'sprite_id': sprite, 'object_description_id': objects.index(sprite),
        'position': dict(x=x, y=y, z=z), 'velocity': dict(x=0, y=0, z=0),
        'yaw_angle': 0, 'sound_id': 0, 'attributes': 0, 'sector_id': ground['sector'], 'time_since_created': 0,
        'temporary_lifetime': 0, 'glow_radius_multiplier': 0, 'spell_id': 0, 'spell_level': 0, 'spell_skill': 0,
        'field54': 0, 'spell_caster_pid': 0, 'spell_target_pid': 0, 'lod_distance': 0, 'spell_caster_ability': 0,
        'initial_position': dict(x=0, y=0, z=0), 'raw_containing_item_hex': item.hex()})
assert len(actors) == 19 and len(scene['loot_containers']) == 3
assert {g['item'] for g in semantic['ground_items']} >= {11372, 11420, 189}
assert 18 not in report['events']
scene_path.write_text(json.dumps(scene, indent=2) + '\n')
shutil.copy2(scene_path, runtime / 'worlds/hesper/maps/hes_d10.scene.yml')
report.update(actors=len(actors), ground_items=semantic['ground_items'], outdoor_return=arrival, plan_budget=budget,
              outdoor_return_source='hesper_out1/source: archive_dome event 13 exported face')
(PROJECT / 'd10_build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
