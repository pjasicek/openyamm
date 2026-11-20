"""The terrain relief review (2026-10-24): the same shots before and after the Crown's relief change, each pose's
height and pitch read from the given built map, so a shot stands on its own map's ground.

    python3 level_generation/projects/hesper_out4/make_relief_tour.py <before|after> [map.odm]
        (writes review/relief_20261024/tour_<name>.yml, its shots into review/relief_20261024/<name>/)

The shots: review_tour_big.yml's and review_tour_rim.yml's (the earlier reviews), then the relief's own: both
entrances, along the gate road and the ring road, a basin, the rim and high aerials.
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
odm = Path(sys.argv[2]) if len(sys.argv) > 2 else PROJECT / 'runtime/worlds/hesper/maps/hes_out4.odm'
heights = parse_odm_file(odm)['payload']['height_map']
build = json.loads((PROJECT / 'out4_build.json').read_text())


def ground(x, y):
    """The native triangle height (the cell splits along fracX + fracY <= 1, as build_out4.height_at)."""
    fx, fy = (x + 32768.0) / 512, (32768.0 - y) / 512
    ix, iy = min(max(int(math.floor(fx)), 0), 126), min(max(int(math.floor(fy)), 0), 126)
    tx, ty = fx - ix, fy - iy

    def h(gx, gy):
        return heights[gy * 128 + gx] * 32.0
    if tx + ty <= 1:
        return h(ix, iy) + (h(ix + 1, iy) - h(ix, iy)) * tx + (h(ix, iy + 1) - h(ix, iy)) * ty
    return h(ix + 1, iy + 1) + (h(ix, iy + 1) - h(ix + 1, iy + 1)) * (1 - tx) + \
        (h(ix + 1, iy) - h(ix + 1, iy + 1)) * (1 - ty)


def shot(label, eye, target, lift=0.0, eye_z=None, pitch=None):
    """At eye (x, y) looking at target (x, y[, z above its ground]); the position is the party's feet."""
    ex, ey = eye
    z = (ground(ex, ey) if eye_z is None else eye_z) + lift
    tx, ty = target[:2]
    tz = ground(tx, ty) + (target[2] if len(target) > 2 else 150)
    if pitch is None:
        pitch = math.atan2(tz - (z + 160), math.hypot(tx - ex, ty - ey))
    return {'name': label, 'position': [round(ex), round(ey), round(z)],
            'yaw': round(math.atan2(ty - ey, tx - ex), 4), 'pitch': round(pitch, 4)}


shots = [
    # review_tour_big.yml
    shot('plaza_signature', (3700, -15800), (0, 0, 1400)),
    shot('kreegan_road_notch', (2880, -21800), (2880, -14400, 500)),
    shot('west_run', (-12000, 0), (-9805, 0, 200)),
    shot('spire_gate', (0, -7800), (0, -4320, 2100)),
    shot('aerial_citadel', (0, -14000), (0, 0, 2900), lift=6500),
    shot('aerial_killing_ground', (-12000, -12000), (0, 0, 100), lift=6000),
    {'name': 'top_down', 'position': [0, -2500, 15000], 'yaw': 1.5708, 'pitch': -1.4},
    # review_tour_rim.yml
    shot('grafting_nw', (-13300, 13300), (-15800, 15800)),
    shot('south_edge_from_crown', (2880, -20200), (2880, -26000, 200)),
    {'name': 'top_down_full', 'position': [0, -1000, 26000], 'yaw': 1.5708, 'pitch': -1.55},
    # The relief's own: from both entrances, along the roads, into a basin, from the rim and from high up.
    shot('south_entrance_view', (2880, -18600), (0, 0, 1200)),
    shot('west_entrance_view', (-19200, 8640), (0, 0, 1200)),
    shot('gate_road_climb', (0, -13000), (0, -5400, 400)),
    shot('ring_road_east', (14400, -6000), (14400, 6000, 150)),
    shot('ring_road_north', (-6000, 14400), (6000, 14400, 150)),
    shot('basin_ne', (8600, 7000), (2000, 2000, 900)),
    shot('basin_sw_from_ring', (-11000, -11000), (-3000, -3000, 900)),
    shot('rim_se_outcrops', (16000, -10500), (20500, -2500, 900)),
    shot('rim_crest_nw', (-20600, 19200), (0, 0, 900), lift=400),
    shot('ring_pit', (14700, 12600), (17700, 9400, 0), lift=1200),
    shot('aerial_high_sw', (-17000, -17000), (0, 0, 0), lift=6000),
    shot('aerial_high_east', (20000, 2000), (0, 0, 0), lift=5000),
    shot('aerial_low_north', (0, 21000), (0, 4000, 0), lift=3500),
]
shots[0]['commands'] = ['config set immortal 1', 'config set invisible 1']
out = PROJECT / 'review/relief_20261024' / name
out.mkdir(parents=True, exist_ok=True)
tour = {'output_dir': str(out), 'settle_seconds': 2.5, 'exit': True, 'shots': shots}
path = PROJECT / f'review/relief_20261024/tour_{name}.yml'
path.write_text(json.dumps(tour, indent=1) + '\n')
print(path, len(shots))
