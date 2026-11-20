"""Write review tours of the Scour: the BUILD-READY's named shots (THE_SCOUR.md section 22, item 7), eye-level views of
each place, aerials and a top-down, from the layout and the build record (out2_build.json).

    python3 level_generation/projects/hesper_out2/make_tour.py <name>   (writes review_tour_<name>.yml)

Run a tour minimized from the repository root (the shots are the party's position, yaw and pitch in radians):
    flock -s output/hesper_stage/locks/engine_build.lock ./tools/run_game.sh --isolated scour --world hesper \
        --map <map> --assets "$PWD/output/hesper_stage/assets_editor_dev" \
        --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_out2/review_tour_<name>.yml" --seconds 0
`edges_out1` and `edges_out4` are shots of the Scour's crossings from Starport Reach and the Crown (their maps).
"""
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

name = sys.argv[1]
record = json.loads((PROJECT / 'out2_build.json').read_text())
MAPS = {'hes_out2.odm': PROJECT / 'runtime/worlds/hesper/maps/hes_out2.odm',
        'hes_out1.odm': ROOT / 'level_generation/projects/hesper_out1/runtime/worlds/hesper/maps/hes_out1.odm',
        'hes_out4.odm': ROOT / 'level_generation/projects/hesper_out4/runtime/worlds/hesper/maps/hes_out4.odm'}
heights = {}


def cw(cx, cy):
    return (cx - 4) * 5760.0, (4 - cy) * 5760.0


def ground(x, y, map_file='hes_out2.odm'):
    if map_file not in heights:
        heights[map_file] = parse_odm_file(MAPS[map_file])['payload']['height_map']
    h = heights[map_file]
    gx = int(round((x + 32768) / 512))
    gy = int(round((32768 - y) / 512))
    return h[min(max(gy, 0), 127) * 128 + min(max(gx, 0), 127)] * 32


def shot(label, eye, target, lift=180, pitch=None, map_file='hes_out2.odm', target_lift=150):
    """eye and target as world points (x, y) or cells (a tuple of two numbers below 8.5 is cells)."""
    ex, ey = cw(*eye) if max(abs(v) for v in eye) < 8.5 else eye
    tx, ty = cw(*target) if max(abs(v) for v in target) < 8.5 else target
    z = ground(ex, ey, map_file) + lift
    yaw = math.atan2(ty - ey, tx - ex)
    if pitch is None:
        pitch = math.atan2(ground(tx, ty, map_file) + target_lift - z, math.hypot(tx - ex, ty - ey))
    return {'name': label, 'position': [round(ex), round(ey), round(z)], 'yaw': round(yaw, 4),
            'pitch': round(pitch, 4)}


def toward(point, target, distance):
    dx, dy = target[0] - point[0], target[1] - point[1]
    length = math.hypot(dx, dy)
    return point[0] + dx / length * distance, point[1] + dy / length * distance


arrivals = {key: value['position'][:2] for key, value in record['arrivals'].items()}
camps = record['camps']


def camp_shot(n, back=900):
    """From the road in, `back` outside the camp gate (camp 5 sits in the dunes: from just inside its gate)."""
    camp = camps[str(n)]
    gate, node = camp['gate'], camp['node']
    eye = toward(gate, node, -back)
    return shot(f'camp{n}', eye, node, lift=200)


pit = cw(4.05, 3.05)
TOURS = {
    'build01': [
        shot('signature_sw_gate', cw(3.32, 3.86), pit, lift=200, target_lift=-400),
        shot('west_edge_arrival', arrivals['west'], cw(1.2, 4.6), lift=200),
        shot('scouts_camp', cw(0.62, 3.9), cw(0.74, 3.74), lift=200),
        shot('tunnel_mouth', toward(arrivals['tunnel_arrival'], (-21600, 8064), -500), (-21600, 8064), lift=200),
        shot('thrix_cave', cw(0.58, 1.0), cw(0.55, 0.62), lift=220),
        shot('wreck', cw(2.2, 1.85), cw(1.62, 1.42), lift=300),
        shot('d3_gate', toward(arrivals['d03_return'], (-12211, -403), -500), (-12211, -403), lift=200),
        shot('d3_mesa_from_road', cw(2.35, 4.95), cw(1.6, 4.1), lift=200, target_lift=800),
        camp_shot(1), camp_shot(2), camp_shot(3), camp_shot(4), camp_shot(5, back=-350),
        shot('d4_pens_from_rim', cw(4.42, 5.3), cw(4.6, 5.8), lift=220, target_lift=-500),
        shot('d4_door', arrivals['d04_return'], (3456, -10714), lift=200),
        shot('d4_door_bay', toward((3456, -10714), arrivals['d04_return'], 1500), (3456, -10714), lift=200,
             target_lift=380),
        shot('depot', cw(6.8, 5.75), cw(7.35, 6.05), lift=250),
        shot('foundry_slag_gate', toward(arrivals['d08_return'], (14112, 16819), -700), (14112, 16819), lift=220,
             target_lift=600),
        shot('slag_river', cw(5.2, 1.7), cw(5.75, 1.1), lift=300),
        shot('kreegan_road_cut', cw(4.5, 1.5), cw(4.5, 0.1), lift=200, target_lift=400),
        shot('north_edge', cw(4.5, 0.35), cw(4.5, -0.6), lift=200),
        shot('conveyor_under', cw(4.2, 5.4), cw(4.05, 4.4), lift=180, target_lift=1300),
        shot('pit_floor_harvester', cw(3.7, 3.05), pit, lift=250, target_lift=200),
        shot('aerial_pit', cw(4.05, 4.6), pit, lift=4200, pitch=-0.75),
        shot('aerial_camps_south', cw(5.5, 7.4), cw(5.5, 5.2), lift=5200, pitch=-0.6),
        shot('aerial_north', cw(5.0, 3.3), cw(5.6, 1.0), lift=5000, pitch=-0.55),
        shot('aerial_west', cw(2.2, 5.5), cw(1.2, 2.5), lift=5000, pitch=-0.55),
        {'name': 'top_down_pit', 'position': [288, 5472, 9000], 'yaw': 1.5708, 'pitch': -1.55},
    ],
    # The integrator's review of build01: the road's dust, Thrix's stall, D4's lit door, the slag river's channel.
    'fix01': [
        shot('signature_sw_gate', cw(3.32, 3.86), pit, lift=200, target_lift=-400),
        shot('west_edge_arrival', arrivals['west'], cw(1.2, 4.6), lift=200),
        shot('thrix_cave', cw(0.58, 1.0), cw(0.55, 0.62), lift=220),
        shot('d4_door', arrivals['d04_return'], (3456, -10714), lift=200),
        shot('slag_river', cw(5.2, 1.7), cw(5.75, 1.1), lift=300),
    ],
    # The user's review of build01: D4's door (one fitted face, its band fitted) and the dressing of the open ground.
    'fix02': [
        shot('d4_door_bay', toward((3456, -10714), arrivals['d04_return'], 1500), (3456, -10714), lift=200,
             target_lift=380),
        shot('west_edge_arrival', arrivals['west'], cw(1.2, 4.6), lift=200),
        shot('signature_sw_gate', cw(3.32, 3.86), pit, lift=200, target_lift=-400),
        shot('kreegan_road_cut', cw(4.5, 1.5), cw(4.5, 0.1), lift=200, target_lift=400),
    ],
    'edges_out1': [
        shot('out1_east_edge', (21200, -2592), (23800, -2592), map_file='hes_out1.odm', lift=200),
    ],
    'edges_out4': [
        shot('out4_south_edge', (2880, -21300), (2880, -23800), map_file='hes_out4.odm', lift=200),
    ],
}
shots = TOURS[name]
tour = {'output_dir': str(PROJECT / 'review' / name), 'settle_seconds': 2.5, 'exit': True, 'shots': shots}
path = PROJECT / f'review_tour_{name}.yml'
path.write_text(json.dumps(tour, indent=1) + '\n')
print(path)
