"""Write the Brood Spires' review tour: BUILD-READY's fifteen named shots (BROOD_SPIRES.md section 22, yaw 0 = east,
radians; pitch from degrees), then close views of the doors, the edges from this side, the nest, an egg field and the
acid, from the built map's record (out3_build.json).

    python3 level_generation/projects/hesper_out3/make_tour.py <name> [HH:MM]    (writes review_tour_<name>.yml; every
    shot at that clock time when given, as the night captures)

Run it minimized with the stage (the tour's output_dir is review/<name>):
    flock -s output/hesper_stage/locks/engine_build.lock ./tools/run_game.sh --isolated out3 --world hesper \\
        --map hes_out3.odm --assets "$PWD/output/hesper_stage/assets_editor_dev" \\
        --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_out3/review_tour_<name>.yml" --seconds 0
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

name = sys.argv[1]
clock = sys.argv[2] if len(sys.argv) > 2 else None
native = parse_odm_file(PROJECT / 'runtime/worlds/hesper/maps/hes_out3.odm')['payload']
heights = native['height_map']
record = json.loads((PROJECT / 'out3_build.json').read_text())


def ground(x, y):
    gx = int(round((x + 32768) / 512))
    gy = int(round((32768 - y) / 512))
    return heights[min(max(gy, 0), 127) * 128 + min(max(gx, 0), 127)] * 32


def shot(label, x, y, z, yaw, pitch_degrees):
    return {'name': label, 'position': [round(x), round(y), round(z)], 'yaw': round(yaw, 4),
            'pitch': round(math.radians(pitch_degrees), 4)}


def look(label, eye, target, lift=200.0):
    """From eye (x, y) at the ground + lift toward target (x, y, z)."""
    z = ground(*eye) + lift
    yaw = math.atan2(target[1] - eye[1], target[0] - eye[0])
    pitch = math.degrees(math.atan2(target[2] - z, math.hypot(target[0] - eye[0], target[1] - eye[1])))
    return shot(label, eye[0], eye[1], z, yaw, pitch)


# The design's shots, three moved: the yard's looked into Wren's post (now from the yard's west
# corner, east-north-east), the aerial and the top-down were
# lost in the fog at 14 000 and 30 000 (lower, the aerial from the south).
BUILD_READY = [
    ('01_the_pass', 288, -22400, 1280, 1.57, 5), ('02_the_saddle', 288, -19900, 1670, 1.57, 0),
    ('03_the_farms_gate', -300, -5900, 1760, 3.14, 0), ('04_the_yard', -4950, -6450, 1410, 0.45, 2),
    ('05_hale', -300, -1900, 1460, 2.4, -10), ('06_the_relay_spire', -9000, -12384, 1660, 3.14, 15),
    ('07_the_sinkhole', -8064, 3974, 1050, 1.9, -25), ('08_the_seedship', 6500, 3500, 1350, 1.4, 8),
    ('09_the_gantry', 5843, 11056, 1760, 0.0, 10), ('10_the_hatchery', -16500, 13500, 1520, 2.2, 5),
    ('11_the_causeway', -2100, 1500, 1110, 1.57, 0), ('12_the_crown_gap', 20500, 8640, 1360, 0.0, 5),
    ('13_the_crown_gap_west', 21000, 8640, 1360, 3.14, 5), ('14_aerial', 0, -16000, 6500, 1.57, -28),
    ('15_top_down', 0, 0, 11000, 1.57, -88)]
shots = [shot(*row) for row in BUILD_READY]
a = record['arrivals']
gate = record['garden']['gate']
shots += [
    look('16_south_edge_looking_south', (288, -21000), (288, -24500, 1200)),
    look('17_d05_door', (-10300, -12200), (-11480, -12384, a['d05_root_door']['position'][2] + 250)),
    look('18_d09_mouth', (-8250, 6100), (-8986, 6970, 300)),
    look('19_gantry_top_breach', (7400, 11100), (8014, 10918, 2250), lift=2050 - ground(7400, 11100)),
    look('20_farm_store_door', (-1450, -4450), (-2500, -4500, 1300), lift=230),
    look('21_s10_nest', (-6000, -4300), (-7200, -5184, 900)),
    look('22_egg_field_e2', (1400, 13300), (2592, 14400, 1000)),
    look('23_acid_lake_shore', (900, -2600), (3168, 0, 800)),
    look('24_pass_kite_roosts_from_road', (288, -21200), (288, -19700, 1900)),
    look('25_heavy_sentinel_bluff', (18000, 8640), (19296, 12096, 2000)),
    look('26_gate_from_lane', (300, -6600), (gate[0], gate[1], 1500)),
]
if clock:
    for row in shots:
        row['time'] = clock
tour = {'output_dir': str(PROJECT / 'review' / name), 'settle_seconds': 2.5, 'exit': True, 'shots': shots}
(PROJECT / f'review_tour_{name}.yml').write_text(yaml.safe_dump(tour, sort_keys=False))
print(PROJECT / f'review_tour_{name}.yml', len(shots))
