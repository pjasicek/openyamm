"""Compile D9 and assemble the plan's encounters, loot and authored events for the isolated Hesper stage."""
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build

spec = importlib.util.spec_from_file_location('zone3', ROOT / 'design/kreegan_world/zone3/dungeons/plans_zone3.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d9
semantic = json.loads((PROJECT / 'source/hes_d09.semantic.json').read_text())
rows = {int(row[0]): row for row in (line.split('\t') for line in
        (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if row[0].isdigit()}
sizes = {m['id']: (m['radius'], m['height']) for m in
         yaml.safe_load((PROJECT.parent / 'hesper_stage/monsters.yml').read_text())['monsters']}
# The authored pack table's order, with its explicit (non-sequential) group ids.
packs = [(1, [10301] * 3), (2, [10045] * 3), (3, [10031] + [10003] * 3), (8, [10001] * 3),
         (9, [10003] * 4), (4, [10045] * 3), (5, [10000] * 4), (6, [10045] * 4 + [10001]),
         (7, [10001] * 3 + [10000] * 2), (11, [10000] * 3), (12, [10045] * 2),
         (13, [10031] + [10003] * 3), (14, [10000] * 2), (15, [10031] * 2 + [10003] * 3),
         (17, [10031] + [10003] * 3), (16, [10045] * 4), (18, [10000] * 3), (19, [10001] * 2),
         (20, [10301] * 4), (21, [10001] * 3), (22, [10301] * 2 + [10001] * 2),
         (23, [10301] * 3), (24, [10111]), (25, [10130]), (26, [10130]), (27, [10130]),
         (28, ([10000] * 3 + [10001]) * 3), (10, [10000] * 3)]
marks = [m for m in PLAN.marks if m['kind'] in ('monster', 'boss')]
assert len(marks) == len(packs)
# Sac groups -> socket offsets from the queen's position (world units, queen facing east): rear, left, right.
SAC_SOCKETS = {25: (-310, 0, 290), 26: (20, 270, 220), 27: (20, -290, 220)}
actors, scripted = [], []


def floor_z(x, y, z):
    if z == -2944 and 0 <= x <= 600 and y >= 4:
        return -2944 + min(88, math.floor((y - 4) / 26.5) + 1) * 16
    return z


def available(x, y, z, radius, rid):
    room = next(r for r in PLAN.rooms if r['id'] == rid)
    if not (room['x'] + radius < x < room['x'] + room['w'] - radius
            and room['y'] + radius < y < room['y'] + room['h'] - radius):
        return False
    if rid == 'vats' and x > 6800 - radius and y < 3864 + radius:
        return False
    if rid == 'creche':
        for k in range(4):
            px, py = room['x'] + 250 + k % 2 * 1000, room['y'] + 100 + k // 2 * 600
            if px - radius < x < px + 400 + radius and py - radius < y < py + 400 + radius:
                return False
    return all(math.hypot(x - a['position']['x'], y - a['position']['y']) >= radius + a['radius'] + 20
               for a in actors if abs(z - a['position']['z']) < 300)


def sector_at(x, y, z):
    matches = [(name, bounds) for name, bounds in semantic['room_bounds'].items()
               if bounds[0] - 1 <= x <= bounds[2] + 1 and bounds[1] - 1 <= y <= bounds[3] + 1
               and bounds[4] - 1 <= z <= bounds[5] + 1]
    assert matches, (x, y, z)
    name, _ = min(matches, key=lambda pair: (pair[1][2] - pair[1][0]) * (pair[1][3] - pair[1][1]))
    return semantic['sectors'].index('room_' + name) + 1


for mark, (group, monsters) in zip(marks, packs):
    assert len(monsters) == mark['count']
    mz = PLAN.floors[mark['floor']]
    room = next(r for r in PLAN.rooms if r['sectors'] and r['floor'] == mark['floor']
                and r['x'] <= mark['x'] <= r['x'] + r['w'] and r['y'] <= mark['y'] <= r['y'] + r['h'])
    for index, monster in enumerate(monsters):
        row = rows[monster]
        radius, height = sizes[monster]
        x, y, z = mark['x'], mark['y'], mz
        actor_group = group
        if monster == 10301:
            # Space the long bodies, not only their collision radii; the royal kennel stays below the stair.
            points = {1: [(6650, 1600), (7050, 1750), (6750, 2050)],
                      20: [(155, -350), (445, -350), (155, -120), (445, -120)],
                      22: [(1100, 100), (1500, -250)],
                      23: [(1100, 1150), (1500, 1500), (1900, 1150)]}
            x, y = points[group][index]
            z = -2944 if group == 20 else mz
            assert available(x, y, z, radius, 'royal' if group == 20 else room['id'])
            assert floor_z(x, y, z) == z
        elif group == 28:
            actor_group += index // 4
            x = 3300 + (index // 4) * 1000
            y = 3700
            z = -3200
            x += (20, 200, 20, 200)[index % 4]
            y += (-150, -150, 150, 150)[index % 4]
        else:
            found = False
            for distance in range(0, 1100, 100):
                for angle in range(0, 360, 30):
                    px = round(mark['x'] + distance * math.cos(math.radians(angle)))
                    py = round(mark['y'] + distance * math.sin(math.radians(angle)))
                    if available(px, py, mz, radius, room['id']):
                        x, y, found = px, py, True
                        break
                if found: break
            assert found, (group, index)
            z = floor_z(x, y, mz)
        if monster == 10130:
            # The Brood Sacs stand on the Brood Mother's cradle sockets (hes_brood_mother_codex/README.md, "D9
            # placement handoff": the sacs' base origins for the queen fixed east), not on the floor beside her.
            queen = next(a for a in actors if a['monster_id'] == 10111)['position']
            dx, dy, dz = SAC_SOCKETS[group]
            x, y, z = queen['x'] + dx, queen['y'] + dy, queen['z'] + dz
        if monster != 10301 and str(len(actors)) in semantic['actor_positions']:
            x, y, z = semantic['actor_positions'][str(len(actors))]
        immobile = monster in (10045, 10111, 10130) or (group in (1, 22) and monster != 10301)
        actor = {'actor_index': len(actors), 'name': row[1], 'npc_id': 0,
                 'attributes': 0x10000 if actor_group >= 28 else 0, 'hp': int(row[4]),
                 'hostility_type': int(row[12]), 'monster_info_id': monster, 'monster_id': monster,
                 'radius': radius, 'height': height, 'move_speed': 0 if immobile else int(row[13]),
                 'position': {'x': x, 'y': y, 'z': z}, 'initial_yaw_units': 0, 'immobile': immobile,
                 'sprite_ids': [0, 0, 0, 0], 'sector_id': sector_at(x, y, z), 'current_action_animation': 0,
                 'carried_item_id': 0, 'group': actor_group, 'ally': 0, 'unique_name_index': 0}
        if monster == 10130:
            actor['keeps_height'] = True        # on its socket, not dropped to the floor (ENGINE: keeps_height)
        if monster in (10045, 10111):
            scripted.append({'index': len(actors), 'behavior': 'hes_egg_cluster' if monster == 10045 else 'hes_brood_mother'})
        actors.append(actor)
assert len(actors) == 96
assert sum(a['monster_id'] == 10301 for a in actors) == 12
assert all(not a['immobile'] for a in actors if a['monster_id'] == 10301)
assert sum(a['monster_id'] == 10045 for a in actors) == 16

out3 = PROJECT.parent / 'hesper_out3/out3_build.json'
exit_fields = 'nil'
if out3.exists():
    record = json.loads(out3.read_text())
    arrival = record['d09_mouth']
    if isinstance(arrival, dict):
        x, y, z = arrival['position']
        direction = arrival['direction_degrees']
    else:
        x, y, z, direction = arrival
    exit_fields = f'x={x}, y={y}, z={z}, direction={round(direction / 360 * 2048) % 2048}'
else:
    print('BLOCKED outdoor round-trip: hesper_out3/out3_build.json is missing; event 50 reports the missing map.')
actor_fields = ', '.join(f'{{index={a["index"]}, behavior="{a["behavior"]}"}}' for a in scripted)
chests = [
    {'name': 'Gland vat', 'fixed': [11431, 11331], 'random': False, 'gold': 0},
    {'name': "Mother's cradle", 'fixed': [11479, 11332], 'random': False, 'gold': 30000},
    {'name': 'Ovipositor Shaft', 'fixed': [11427], 'random': False, 'gold': 0},
    {'name': "Scouts' cache", 'fixed': [11302] * 4 + [11300] * 3 + [11303, 11301], 'random': False, 'gold': 0},
    'Hatchery pod', 'Sump pod', 'Barracks pod', 'Larder pod']
report = build(PROJECT, 'hes_d09.blv', {'D9_ACTORS': actor_fields, 'D9_EXIT': exit_fields},
               arrival='from_hes_out3', chests=chests, actors=actors)

# D9's H3 chest tier and placed ground supplies are scene data; rebuild them from the authored records each time.
scene_path = PROJECT / 'runtime/hes_d09.scene.yml'
scene = json.loads(scene_path.read_text())
for index, chest in enumerate(scene['loot_containers']):
    chest['presentation'] = 'ashrunner crate' if index == 3 else 'kreegan pod'
    if index >= 4:
        # shortcut: native T6 gear until the integrator installs Hesper's H3 loot pool and weighted rolls.
        chest['random_treasure_level'] = 6
        chest['gold'] = 9000
item_rows = {int(row[0]): row for row in (line.split('\t') for line in
             (ROOT / 'output/hesper_stage/assets_editor_dev/worlds/hesper/data_tables/items.txt').read_text().splitlines())
             if row[0].isdigit()}
object_ids = [int(line.split('\t')[2]) for line in
              (ROOT / 'assets_dev/engine/data_tables/object_list.txt').read_text(encoding='latin1').splitlines()[1:]]
supplies = [(11300, 1610, 280, -2944), (11300, 1650, 280, -2944),
            (11302, 1610, 320, -2944), (11304, 1650, 320, -2944)]
objects = []
for item, x, y, z in supplies:
    sprite = int(item_rows[item][11])
    raw = bytearray(36)
    raw[0:4] = item.to_bytes(4, 'little')
    objects.append({'sprite_object_index': len(objects), 'sprite_id': sprite,
                    'object_description_id': object_ids.index(sprite), 'position': {'x': x, 'y': y, 'z': z},
                    'velocity': {'x': 0, 'y': 0, 'z': 0}, 'yaw_angle': 0, 'sound_id': 0, 'attributes': 0,
                    'sector_id': sector_at(x, y, z), 'time_since_created': 0, 'temporary_lifetime': 0,
                    'glow_radius_multiplier': 0, 'spell_id': 0, 'spell_level': 0, 'spell_skill': 0, 'field54': 0,
                    'spell_caster_pid': 0, 'spell_target_pid': 0, 'lod_distance': 0, 'spell_caster_ability': 0,
                    'initial_position': {'x': 0, 'y': 0, 'z': 0}, 'raw_containing_item_hex': raw.hex().upper()})
scene['initial_state']['sprite_objects'] = objects
scene_path.write_text(json.dumps(scene, indent=2) + '\n')
tree = PROJECT / 'runtime/worlds/hesper'
shutil.copy2(scene_path, tree / 'maps' / scene_path.name)
(tree / 'behaviors').mkdir(exist_ok=True)
for name in ('hes_egg_cluster', 'hes_brood_mother'):
    shutil.copy2(PROJECT / 'source' / (name + '.lua'), tree / 'behaviors' / (name + '.lua'))
report.update(actors=len(actors), egg_clusters=16, outdoor_exit_ready=out3.exists(),
              actor_groups={str(group): [a['actor_index'] for a in actors if a['group'] == group]
                            for group in range(1, 31)})
(PROJECT / 'd09_build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
