"""Write the Crown's review tour (THE_CROWN.md BUILD-READY 8): the named eye-level shots, aerials over the citadel and
the killing ground, a top-down view and each edge from this side, from the built map.

    python3 level_generation/projects/hesper_out4/make_tour.py <name> [shot ...]   (writes review_tour_<name>.yml, its
    shots into review/<name>/; only the named shots when given)
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
native = parse_odm_file(PROJECT / 'runtime/worlds/hesper/maps/hes_out4.odm')['payload']
heights = native['height_map']
build = json.loads((PROJECT / 'out4_build.json').read_text())


def ground(x, y):
    gx = int(round((x + 32768) / 512))
    gy = int(round((32768 - y) / 512))
    return heights[min(max(gy, 0), 127) * 128 + min(max(gx, 0), 127)] * 32


def shot(label, eye, target, lift=0.0, pitch=None, eye_z=None):
    """A shot at eye (x, y) looking at target (x, y[, z]); the position is the party's feet (the game adds the eye
    height), lifted by `lift` for an aerial."""
    ex, ey = eye
    z = (ground(ex, ey) if eye_z is None else eye_z) + lift
    tx, ty = target[:2]
    tz = target[2] if len(target) > 2 else ground(tx, ty) + 150
    yaw = math.atan2(ty - ey, tx - ex)
    if pitch is None:
        pitch = math.atan2(tz - (z + 160), math.hypot(tx - ex, ty - ey))
    return {'name': label, 'position': [round(ex), round(ey), round(z)], 'yaw': round(yaw, 4),
            'pitch': round(pitch, 4)}


shots = [
    shot('plaza_signature', (3700, -15800), (0, 0, 2500)),
    shot('kreegan_road_notch', (2880, -21800), (2880, -14400, 1600)),
    shot('west_notch', (-21800, 8640), (-14400, 8640, 1600)),
    shot('test_emplacement', (12800, -13600), (15200, -12000)),
    shot('west_run', (-12000, 0), (-9805, 0, 1300)),
    shot('north_run', (0, 12000), (0, 9805, 1300)),
    shot('east_run', (12000, 0), (9805, 0, 1300)),
    shot('spire_gate', (0, -7800), (0, -4320, 3200)),
    shot('grafting_nw', (-13300, 13300), (-15800, 15800)),
    shot('roosts', (13000, 15200), (17000, 17000, 3400)),
    shot('kept_market', (-13400, -13400), (-15800, -15800)),
    shot('colony_ruins', (-6600, 14900), (-6600, 17400)),
    shot('cable_yards', (15300, -4300), (17800, -5000)),
    shot('west_ward', (-14600, 8640), (-17400, 8640, 1500)),
    shot('aerial_citadel', (0, -14000), (0, 0, 4000), lift=6500),
    shot('aerial_killing_ground', (-12000, -12000), (0, 0, 1200), lift=6000),
    shot('south_edge_from_crown', (2880, -20200), (2880, -26000, 1400)),
    shot('west_edge_from_crown', (-20200, 8640), (-26000, 8640, 1400)),
    shot('mast_from_south_notch', (2880, -22600), (0, 0, 9000)),
    shot('node_door_west', (-10700, 300), (-9805, 0, 1250)),
    shot('hatch_d6', (-16400, -2880), (-17600, -2880, 1400)),
    shot('pad_lift', (2880, -14200), (2880, -12960, 1500), eye_z=build['plaza_top']),
    {'name': 'top_down', 'position': [0, -2500, 15000], 'yaw': 1.5708, 'pitch': -1.4},
    # The Blooding Ring (a follow-up): from the ring road's patrol, the track, the gate's passage, the gate, the dais's
    # far side, above it and from straight above.
    shot('ring_from_patrol', (14400, 6000), (17700, 9400, 1300)),
    shot('ring_track', (14900, 9400), (17700, 9400, 1500)),
    shot('ring_passage', (15830, 10300), (15950, 9400, 1250)),
    shot('ring_gate', (16650, 9400), (17700, 9400, 1300)),
    shot('ring_dais', (18550, 9100), (16500, 9400, 1300)),
    shot('ring_aerial', (14600, 6600), (17700, 9400, 1100), lift=3200),
    {'name': 'ring_top', 'position': [17200, 8300, 6200], 'yaw': 1.5708, 'pitch': -1.42},
]
if len(sys.argv) > 2:                                  # only the named shots
    shots = [s for s in shots if s['name'] in sys.argv[2:]]
out = PROJECT / 'review' / name
out.mkdir(parents=True, exist_ok=True)
tour = {'output_dir': str(out), 'settle_seconds': 2.5, 'exit': True, 'shots': shots}
path = PROJECT / f'review_tour_{name}.yml'
path.write_text(json.dumps(tour, indent=1) + '\n')
print(path)
