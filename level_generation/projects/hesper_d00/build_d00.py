"""Compile D0 Hangar Nine and assemble its scene and Lua into runtime/worlds/hesper, the tree the shared Hesper stage
installs (level_generation/projects/hesper_stage/stage.py, which also cooks the textures and registers the map;
assets_dev is never modified).

    blender --background --factory-startup --python level_generation/projects/hesper_d00/author_d00_blender.py
    python3 level_generation/projects/hesper_d00/build_d00.py
    python3 level_generation/projects/hesper_stage/stage.py

The surface door's destination is Starport Reach's arrival at the Crew Ramp door (hesper_out1/out1_build.json). The
monsters are the author script's `actors` (semantic record), written as scene actors from the Hesper monster rows the
stage installs (hesper_stage/monsters.yml, design/kreegan_world/data/monster_data.txt); the map's load event makes them
hostile (evt.SetMonsterRelation, as on Starport Reach).
"""
import json
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build  # noqa: E402

semantic = json.loads((PROJECT / 'source/hes_d00.semantic.json').read_text())
rows = {int(row[0]): row for row in (line.split('\t') for line in
        (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if row[0].isdigit()}
sizes = {m['id']: (m['radius'], m['height']) for m in
         yaml.safe_load((PROJECT.parent / 'hesper_stage/monsters.yml').read_text())['monsters']}
actors = []
for a in semantic['actors']:
    monster, row = a['monster'], rows[a['monster']]
    radius, height = sizes[monster]
    x, y, z = a['position']
    actors.append({'actor_index': len(actors), 'name': a['name'], 'npc_id': 0, 'attributes': 0, 'hp': int(row[4]),
                   'hostility_type': int(row[12]), 'monster_info_id': monster, 'monster_id': monster,
                   'radius': radius, 'height': height, 'move_speed': 0 if a['posted'] else int(row[13]),
                   'position': {'x': x, 'y': y, 'z': z},
                   'initial_yaw_units': round(a['yaw_degrees'] % 360 / 360 * 2048) % 2048, 'immobile': a['posted'],
                   'sprite_ids': [0, 0, 0, 0], 'sector_id': a['sector'], 'current_action_animation': 0,
                   'carried_item_id': 0, 'group': a['group'], 'ally': 0, 'unique_name_index': 0})

out1 = json.loads((PROJECT.parent / 'hesper_out1/out1_build.json').read_text())
x, y, z = out1['arrival']
direction = round(out1['arrival_direction_degrees'] / 360 * 2048) % 2048
build(PROJECT, 'hes_d00.blv', {'SURFACE_ARRIVAL': f'{x}, {y}, {z}, {direction}, 0, 0, 0, 0'}, arrival='surface_door',
      chests=['crew locker', 'Parts Store chest', 'arms locker', 'Fuel Depot locker'], actors=actors)
