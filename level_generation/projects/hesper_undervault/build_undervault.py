"""Compile the Undervault and assemble its scene and Lua into runtime/worlds/hesper, the tree the shared Hesper stage installs
(level_generation/projects/hesper_stage/stage.py, which also cooks the textures and registers the map; assets_dev is
never modified).

    blender --background --factory-startup --python level_generation/projects/hesper_undervault/author_undervault_blender.py
    python3 level_generation/projects/hesper_undervault/build_undervault.py
    python3 level_generation/projects/hesper_stage/stage.py

Launch it with:

    ./tools/run_game.sh --isolated undervault --world hesper --map hes_undervault.blv --assets output/hesper_stage/assets_editor_dev
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
SOURCE = PROJECT / 'source'
RUNTIME = PROJECT / 'runtime'
MAP = 'hes_undervault.blv'

# --- Compile ---------------------------------------------------------------------------------------------------------
RUNTIME.mkdir(exist_ok=True)
subprocess.run([str(ROOT / 'build/tools/mm9_compile_indoor_source'), str(SOURCE / 'hes_undervault.glb'),
                str(SOURCE / 'hes_undervault.geometry.yml'), str(RUNTIME / MAP), str(SOURCE / 'hes_undervault.doors.yml'),
                str(SOURCE / 'hes_undervault.faces.yml')], check=True)
metadata = json.loads((SOURCE / 'hes_undervault.geometry.yml').read_text())
semantic = json.loads((SOURCE / 'hes_undervault.semantic.json').read_text())
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402
native = parse_blv_file(RUNTIME / MAP)['payload']
bound = {f['face_param']['cog_triggered'] for f in native['faces'] if f['face_param']['cog_triggered']}
expected = {int(e) for e in semantic['events']}
assert bound == expected, (sorted(bound), sorted(expected))
assert len(native['lights']) == len(metadata['lights'])
assert len(native['entities']) == len(metadata['entities'])

# --- Scene -----------------------------------------------------------------------------------------------------------
template = ROOT / 'level_generation/projects/brackenford_greywatch/calibration/calibration.scene.yml'
scene = json.loads(template.read_text())
scene['source']['geometry_file'] = MAP
scene['environment']['ceiling'] = 2048
arrival = semantic['arrivals']['lift']
scene['party_start_points'] = [{'start_index': 0, 'source_name': 'StartPoint0', 'position': arrival['position'],
                                'direction_degrees': arrival['direction_degrees']}]
scene['initial_state']['doors'] = []
# Warder Halm (P4's NPC 9550), a Guard Sergeant (Hesper row 10068, hesper_stage/monsters.yml) posted at the Lift Gate
# beside the arrival, facing the party stepping off the lift; Odo (9506) by the Water Works arch, shown from M2 (the
# load event clears group 1's Invisible bit); the hall's fifteen street people (9553-9567, P4's NPCS) on the villager
# rows, wandering (hesper_stage/npcs_undervault.yml has their talk).
HALM, SERGEANT = 9550, 10068
ODO, ODO_GROUP = 9506, 1
VILLAGERS = [10073, 10074, 10075, 10076, 10077, 10078]
# The street people's spots on the hall floor (x 0-6400, y 0-4800): off the great pillars, the stalls, the fountain's
# market ring, the benches, braziers and salvage heaps, and 500 or more from every door.
STREET_SPOTS = [(2250, 1000), (3200, 1000), (4150, 1000), (800, 1750), (5600, 1750), (2350, 1500), (800, 2700),
                (5600, 2800), (2300, 3550), (3200, 3650), (4100, 3550), (800, 3300), (5600, 3700), (2650, 4250),
                (3800, 4250)]
STREET_NPCS = list(range(9553, 9568))
rows = {int(row[0]): row for row in (line.split('\t') for line in
        (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if row[0].isdigit()}
sizes = {m['id']: (m['radius'], m['height']) for m in
         yaml.safe_load((PROJECT.parent / 'hesper_stage/monsters.yml').read_text())['monsters']}
lift_gate = semantic['sectors'].index('room_liftgate') + 1        # sector 0 is the empty one
radius, height = sizes[SERGEANT]
scene['initial_state']['actors'] = [
    {'actor_index': 0, 'name': 'Warder Halm', 'npc_id': HALM, 'attributes': 0, 'hp': int(rows[SERGEANT][4]),
     'hostility_type': 0, 'monster_info_id': SERGEANT, 'monster_id': SERGEANT, 'radius': radius, 'height': height,
     'move_speed': 0, 'position': {'x': 3520, 'y': -200, 'z': 0},
     'initial_yaw_units': round(180 / 360 * 2048) % 2048, 'immobile': True, 'sprite_ids': [0, 0, 0, 0],
     'sector_id': lift_gate, 'current_action_animation': 0, 'carried_item_id': 0, 'group': 0, 'ally': 0,
     'unique_name_index': 0}]


def hall_sector(x, y):
    """The hall's sector at a floor point (its 3 x 3 grid: author_undervault_blender.py's hall_<row><column>)."""
    row = min(2, int(y // 1600))
    column = 0 if x < 2133 else 1 if x < 4267 else 2
    return semantic['sectors'].index(f'room_hall_{row}{column}') + 1


def villager(name, npc, monster, x, y, degrees, posted=False, group=0, attributes=0):
    radius, height = sizes[monster]
    scene['initial_state']['actors'].append({
        'actor_index': len(scene['initial_state']['actors']), 'name': name, 'npc_id': npc, 'attributes': attributes,
        'hp': int(rows[monster][4]), 'hostility_type': 0, 'monster_info_id': monster, 'monster_id': monster,
        'radius': radius, 'height': height, 'move_speed': 0 if posted else int(rows[monster][13]),
        'position': {'x': x, 'y': y, 'z': 0}, 'initial_yaw_units': round(degrees / 360 * 2048) % 2048,
        'immobile': posted, 'sprite_ids': [0, 0, 0, 0], 'sector_id': hall_sector(x, y), 'current_action_animation': 0,
        'carried_item_id': 0, 'group': group, 'ally': 0, 'unique_name_index': 0})


villager('Odo', ODO, VILLAGERS[0], 5450, 450, 135, posted=True, group=ODO_GROUP, attributes=0x00010000)   # Invisible
for k, (npc, (x, y)) in enumerate(zip(STREET_NPCS, STREET_SPOTS)):
    villager('Undervault street person', npc, VILLAGERS[k % len(VILLAGERS)], x, y, (k * 77) % 360)
scene['loot_containers'] = []
(RUNTIME / 'hes_undervault.scene.yml').write_text(json.dumps(scene, indent=2) + '\n')

# --- Lua --------------------------------------------------------------------------------------------------------------
events = {int(k): v for k, v in semantic['events'].items()}
events[1] = 'map_load'
text = '-- Generated by build_undervault.py; author source/hes_undervault.handlers.lua and the Blender source instead.\n'
text += 'SetMapMetadata({onLoad = {1}, onLeave = {}, openedChestIds = {}})\n'
handlers = (SOURCE / 'hes_undervault.handlers.lua').read_text()


def fill(token, value):
    global handlers
    assert token in handlers, token
    handlers = handlers.replace(token, value)


def place(x, y, z, degrees):
    """evt.MoveToMap's position, direction and the four unused arguments before the map name."""
    return f'{x}, {y}, {z}, {round(degrees / 360 * 2048) % 2048}, 0, 0, 0, 0, '


def link(record, arrival, map_file, missing):
    """The move to another Hesper map's arrival (a semantic record's `arrivals`, or a build record's
    [x, y, z, degrees] as out1_build.json's), or a status text while that map is not built (as hesper_out1's dungeon
    entries do it). Returns the Lua statement and whether the map is built."""
    if not record.exists():
        return f'evt.StatusText({json.dumps(missing)})', False
    data = json.loads(record.read_text())
    if 'arrivals' in data:
        a = data['arrivals'][arrival]
        return f'evt.MoveToMap({place(*a["position"], a["direction_degrees"])}"{map_file}")', True
    return f'evt.MoveToMap({place(*data[arrival])}"{map_file}")', True


fill('LIFT_ARRIVAL, ', place(*json.loads((PROJECT.parent / 'hesper_out1/out1_build.json').read_text())['lift_arrival']))
works = json.loads((PROJECT.parent / 'hesper_d02/source/hes_d02.semantic.json').read_text())['arrivals']['water_works']
fill('D2_WORKS, ', place(*works['position'], works['direction_degrees']))
fill('BULKHEAD_COG', str(semantic['cogs']['bulkhead']))
# D15 The Undercroft (P3): its arrival `deep_stair`, inside the bulkhead; the Scour (P1): its `tunnel_arrival` at the
# tunnel mouth (A3), which its build records as out1 records `lift_arrival` (out2_build.json).
d15, _ = link(PROJECT.parent / 'hesper_d15/source/hes_d15.semantic.json', 'deep_stair', 'hes_d15.blv',
              "The bulkhead stands open, its glyph ring lit cyan; beyond it the Ancients' freight line runs into "
              "the dark. The way is blocked.")
fill('ENTER_D15()', d15)
scour, scour_built = link(PROJECT.parent / 'hesper_out2/out2_build.json', 'tunnel_arrival', 'hes_out2.odm',
                          "The old service tunnel west to the Scour is blocked.")
fill('SCOUR_TUNNEL()', scour)
fill('SCOUR_BUILT', 'true' if scour_built else 'false')
text += handlers + '\n'
# The Water Works door's two ways are topics of its dialogue (hesper_stage/npcs.yml) that run this map's events of
# their ids (topics without Lua there): register them with the map's events.
npcs = yaml.safe_load((PROJECT.parent / 'hesper_stage/npcs.yml').read_text())
for topic in npcs['topics']:
    if topic.get('map_event') == MAP:
        events[topic['id']] = topic['title']
for event_id in sorted(set(events)):
    title = events[event_id].replace('_', ' ').capitalize()
    text += f'assert(type(handlers[{event_id}]) == "function", "Missing Undervault handler {event_id}")\n'
    text += f'RegisterEvent({event_id}, {json.dumps(title)}, handlers[{event_id}], {json.dumps(title)})\n'
(RUNTIME / 'hes_undervault.lua').write_text(text)

# --- Runtime tree ------------------------------------------------------------------------------------------------------
TREE = RUNTIME / 'worlds/hesper'
(TREE / 'maps').mkdir(parents=True, exist_ok=True)
(TREE / 'events/maps').mkdir(parents=True, exist_ok=True)
shutil.copy2(RUNTIME / MAP, TREE / 'maps' / MAP)
shutil.copy2(RUNTIME / 'hes_undervault.scene.yml', TREE / 'maps/hes_undervault.scene.yml')
shutil.copy2(RUNTIME / 'hes_undervault.lua', TREE / 'events/maps/hes_undervault.lua')
sectors = native['sectors']
report = {'map': MAP, 'faces': len(native['faces']), 'vertices': len(native['vertices']), 'sectors': len(sectors),
          'portals': sum(1 for f in native['faces'] if f['is_portal']), 'lights': len(native['lights']),
          'decorations': len(native['entities']), 'outlines': len(native['outlines']), 'events': sorted(bound)}
(PROJECT / 'undervault_build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
