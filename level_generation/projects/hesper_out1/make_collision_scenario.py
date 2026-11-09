"""Write building_collision.yml: headless walks into the model buildings' invisible collision boxes (build_out1.py,
`building`), expected to stop at the box rather than walk through: into Landfall through its wall, and in
through its North Gate, which must not block.
(The houses are BModels and collide as any building does.)

    python3 level_generation/projects/hesper_out1/make_collision_scenario.py
    (cd output/hesper_stage/scenario_run && ../../../build/game/openyamm --world hesper \
        --headless-run-scenario ../../../level_generation/projects/hesper_out1/building_collision.yml)
"""
import json
import math
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

native = parse_odm_file(PROJECT / 'runtime/worlds/hesper/maps/hes_out1.odm')['payload']
heights = native['height_map']
scene = json.loads((PROJECT / 'source/hes_out1.scene.yml').read_text())


def ground(x, y):
    gx, gy = int(round((x + 32768) / 512)), int(round((32768 - y) / 512))
    return heights[gy * 128 + gx] * 32


def entity(name, index=0):
    found = [e['position'] for e in scene['entities'] if e['name'] == name]
    return found[index]


def walk(label, start, toward, stop_short, stop_far, slide=200):
    """Walk forward from start toward a point for four seconds (about 1 500 units unblocked); the party must stop
    between stop_short and stop_far units along, give or take `slide` units sliding along the wall."""
    yaw = math.atan2(toward[1] - start[1], toward[0] - start[0])
    middle = (stop_short + stop_far) / 2
    stop = (start[0] + math.cos(yaw) * middle, start[1] + math.sin(yaw) * middle)
    pose = {'map': 'hes_out1.odm', 'yaw': round(yaw, 6), 'pitch': 0.0}
    return [{'note': label},
            {'movement_segment': {
                'input': 'forward', 'duration_ms': 4000, 'delta_game_minutes': 0.0,
                'start': {'x': round(start[0], 1), 'y': round(start[1], 1), 'z': float(ground(*start)), **pose},
                'expect_stop': {'x': round(stop[0], 1), 'y': round(stop[1], 1), 'z': float(ground(*stop)), **pose},
                'tolerance_xy': round(math.hypot((stop_far - stop_short) / 2, slide)), 'tolerance_z': 200,
                'loose_tolerance': True, 'actor_collision': False, 'actor_ai': False}}]


# Landfall's wall and gates (out1_build.json): walked into half way along the north wall between its west end (in the
# cliff) and the North Gate, then in through the North Gate itself, which must not block.
build = json.loads((PROJECT / 'out1_build.json').read_text())
line = build['landfall']['wall']
north_y = line[1][1]
west_x = line[0][0]
gate_x, gate_y = build['landfall']['gates'][1]
wall_x = (west_x + gate_x) / 2
steps = walk('In through the north wall: blocked at it', (wall_x, north_y + 600), (wall_x, north_y - 2000), 380, 560)
steps += walk('In through the North Gate: open (at a run, about 3 000 in four seconds)', (gate_x, gate_y + 600),
              (gate_x, gate_y - 4000), 2750, 3300)
scenario = {'id': 'hesper.out1.building_collision', 'world': 'hesper', 'mode': 'faithful',
            'steps': [{'new_game_flow': {'start_map': 'hes_out1.odm'}}] + steps}
(PROJECT / 'building_collision.yml').write_text(yaml.safe_dump(scenario, sort_keys=False))
print(PROJECT / 'building_collision.yml')
