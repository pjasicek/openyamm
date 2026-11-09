"""Write review tours of Starport Reach: eye-level views of each place and an aerial overview, from the layout.

    python3 level_generation/projects/hesper_out1/make_tour.py <name>   (writes review_tour_<name>.yml)
"""
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'design/kreegan_world/zone1'))
from starport_terrain import CELL, CELL_UNITS, at  # noqa: E402
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

name = sys.argv[1]                 # a tour of TOURS
native = parse_odm_file(PROJECT / 'runtime/worlds/hesper/maps/hes_out1.odm')['payload']
heights = native['height_map']


def world(cell, fx, fy):
    px, py = at(cell, fx, fy)
    return (px / CELL - 4) * CELL_UNITS, (4 - py / CELL) * CELL_UNITS


def ground(x, y):
    gx = int(round((x + 32768) / 512))
    gy = int(round((32768 - y) / 512))
    return heights[min(max(gy, 0), 127) * 128 + min(max(gx, 0), 127)] * 32


def shot(label, eye, target, lift=180, pitch=None):
    ex, ey = world(*eye)
    tx, ty = world(*target)
    z = ground(ex, ey) + lift
    yaw = math.atan2(ty - ey, tx - ex)
    if pitch is None:
        distance = math.hypot(tx - ex, ty - ey)
        pitch = math.atan2(ground(tx, ty) + 150 - z, distance)
    return {'name': label, 'position': [round(ex), round(ey), round(z)], 'yaw': round(yaw, 4),
            'pitch': round(pitch, 4)}


def door_shots(events, distance=560.0, eye=0.0, aside=140.0):
    """A shot in front of each BModel face whose event is in `events` (one per model), standing on the ground (a
    shot's position is the party's feet; the game adds the eye height)."""
    found = []
    for model in native['bmodels']:
        for face in model['faces']:
            if face['cog_triggered_number'] not in events:
                continue
            points = [(model['vertices'][i]['x'], model['vertices'][i]['y'], model['vertices'][i]['z'])
                      for i in face['vertex_indices']]
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
            z0 = min(p[2] for p in points)
            (ax, ay, _), (bx, by, _) = points[0], points[1]
            nx, ny = by - ay, -(bx - ax)                    # the face's horizontal normal, either way
            length = math.hypot(nx, ny) or 1.0
            nx, ny = nx / length, ny / length
            # out of the door: away from the model's centre
            mx = sum(v['x'] for v in model['vertices']) / len(model['vertices'])
            my = sum(v['y'] for v in model['vertices']) / len(model['vertices'])
            if (cx - mx) * nx + (cy - my) * ny < 0:
                nx, ny = -nx, -ny
            ex, ey = cx + nx * distance - ny * aside, cy + ny * distance + nx * aside
            found.append({'name': model['name'].replace('BMODEL_', ''), 'position': [round(ex), round(ey),
                          round(z0 + eye)], 'yaw': round(math.atan2(cy - ey, cx - ex), 4), 'pitch': 0.08})
            break
    return found


def look(label, eye, target):
    """A shot from eye to target, both world (x, y, height above the ground there)."""
    (ex, ey, lift), (tx, ty, tlift) = eye, target
    z, tz = ground(ex, ey) + lift, ground(tx, ty) + tlift
    yaw = math.atan2(ty - ey, tx - ex)
    pitch = math.atan2(tz - z - 160, math.hypot(tx - ex, ty - ey))      # from the eye, 160 over the feet
    return {'name': label, 'position': [round(ex), round(ey), round(z)], 'yaw': round(yaw, 4),
            'pitch': round(pitch, 4)}


build = json.loads((PROJECT / 'out1_build.json').read_text())
if 'party_start' in build:                          # the arrival (README "The arrival"), from the build's report
    sx, sy, sz, sfacing = build['party_start']
    wx, wy, _ = build['wreck']
    cx, cy = world('C6', 0.85, 0.75)                # the crash crater's centre (starport_terrain.CRATER)
    out_x, out_y = (wx - cx) / math.hypot(wx - cx, wy - cy), (wy - cy) / math.hypot(wx - cx, wy - cy)
    ARRIVAL = [
        {'name': 'start_view', 'position': [sx, sy, sz], 'yaw': round(math.radians(sfacing), 4), 'pitch': -0.12},
        look('start_turned_to_wreck', (sx, sy, 0), (wx, wy, 150)),
        look('wreck_close', (wx + out_x * 900 - out_y * 500, wy + out_y * 900 + out_x * 500, 120), (wx, wy, 200)),
        look('debris_trail', (cx + 1500, cy + 900, 250), (wx, wy, 150)),
        look('wreck_far', (cx + 3500, cy + 2200, 500), (wx, wy, 150)),
        look('crater_from_east_gate_road', (-9300, -14000, 0), (wx, wy, 300)),
    ]


TOURS = {
    # The arrival (2026-10-22): the start, the wreck close and far, the East Gate guard and the Warden's Post. A tour
    # holds the game still (no game time, no timers): the drones are single timed screenshots (README).
    'arrival': (ARRIVAL + [look('east_gate_guard', (-9150, -15950, 0), (-9740, -15820, 150)),
                           look('wardens_post', (-14700, -16700, 0), (-14700, -17750, 300))])
    if 'party_start' in build else [],
    # Landfall's people (2026-10-22): the gates, the streets, the square, the walls and their turrets.
    'people': [
        look('east_gate_arrival', (-8300, -15400, 0), (-10200, -15400, 300)),
        look('east_gate_guard', (-9150, -15950, 0), (-9740, -15820, 150)),
        look('main_street', (-10800, -15250, 0), (-14300, -15600, 150)),
        look('square', (-14250, -15300, 0), (-15600, -16400, 200)),
        look('lift_sergeants', (-14250, -16200, 0), (-15270, -16200, 250)),
        look('wardens_post', (-14700, -16700, 0), (-14700, -17750, 300)),
        look('north_gate_outside', (-15800, -10500, 0), (-15800, -12400, 400)),
        look('north_street', (-15800, -12850, 0), (-15800, -16000, 150)),
        look('north_wall_turrets', (-13600, -13700, 0), (-13000, -12400, 750)),
        look('east_wall_outside', (-8700, -17000, 0), (-10200, -18000, 700)),
        look('gate_bastion_close', (-9300, -14300, 1100), (-10200, -14870, 1000)),
        look('wall_walk_close', (-11000, -13300, 900), (-10200, -14350, 700)),
        look('south_lane', (-11400, -19400, 0), (-16000, -19500, 150)),
        look('stone_lane_fountain', (-16800, -16050, 0), (-19000, -16000, 150)),
        look('aerial', (-12500, -23500, 4200), (-15700, -16500, 0)),
        {'name': 'top_down', 'position': [-15900, -16400, 1478 + 9000], 'yaw': 1.5708, 'pitch': -1.5},
    ],
    # The same town 25 s a shot later: the wanderers spread, the posts held.
    'people_later': [
        look('main_street', (-10800, -15250, 0), (-14300, -15600, 150)),
        look('square', (-14250, -15300, 0), (-15600, -16400, 200)),
        look('south_lane', (-11400, -19400, 0), (-16000, -19500, 150)),
        look('square_above', (-13600, -14400, 1500), (-15600, -16600, 0)),
        look('west_above', (-17000, -14200, 1600), (-19200, -16800, 0)),
    ],

    'first': [
        shot('arrival_to_lift', ('D6', 0.25, 0.25), ('E5', 0.5, 0.28)),
        shot('crater_from_rim', ('D6', 0.1, 0.3), ('C6', 0.65, 0.75)),
        shot('apron_to_terminal', ('D4', 0.4, 0.5), ('F4', 0.55, 0.5)),
        shot('terminal_front', ('E4', 0.75, 0.45), ('F4', 0.3, 0.5)),
        shot('gantries', ('E4', 0.3, 0.1), ('E3', 0.5, 0.35)),
        shot('hangars', ('D4', 0.2, 0.2), ('D3', 0.5, 0.45)),
        shot('camp', ('C3', 0.4, 0.6), ('B3', 0.5, 0.5)),
        shot('canyon', ('F5', 0.4, 0.2), ('G6', 0.5, 0.5)),
        shot('pumping_station', ('G6', 0.4, 0.5), ('G6', 0.82, 0.5)),
        shot('scrapyard', ('F4', 0.85, 0.7), ('G4', 0.5, 0.5)),
        shot('glassfields', ('F2', 0.6, 0.6), ('G2', 0.5, 0.4)),
        shot('archive_dome', ('C2', 0.5, 0.4), ('C1', 0.5, 0.45)),
        shot('aerial', ('D7', 0.5, 0.9), ('D4', 0.5, 0.5), lift=9000, pitch=-0.75),
    ],
    # The house kit in the Hesperian village (2026-10-21): every door, then the village.
    'houses': door_shots({14, 26, 27, 29}),
    'shops': door_shots({25, 29}, distance=800.0, aside=260.0),
    'camp_houses': door_shots({20, 21, 22, 23, 24, 25}) + [
        shot('camp_overview', ('C3', 0.3, 0.75), ('B3', 0.5, 0.5), lift=900, pitch=-0.3)],
    # The Hesperian village round the Lift Head (2026-10-21).
    'village': [
        shot('village_road_gate', ('E5', 0.55, -0.15), ('E5', 0.5, 0.28)),
        shot('village_track_gate', ('D5', 0.6, 0.85), ('E5', 0.5, 0.28)),
        shot('plaza_to_lift', ('E5', 0.35, 0.5), ('E5', 0.5, 0.28), lift=200),
        shot('plaza_east', ('E5', 0.45, 0.3), ('E5', 0.78, 0.3), lift=200),
        shot('plaza_west', ('E5', 0.55, 0.25), ('E5', 0.2, 0.3), lift=200),
        shot('plaza_south', ('E5', 0.5, 0.18), ('E5', 0.5, 0.55), lift=200),
        shot('lift_cage', ('E5', 0.5, 0.18), ('E5', 0.5, 0.28), lift=170),
        shot('village_aerial', ('E5', 0.5, 0.85), ('E5', 0.5, 0.28), lift=2400, pitch=-0.65),
    ],
    # The second building pass (2026-10-21): the user's notes on the first build.
    'pass3': [
        shot('lowfolk_gate', ('D5', 0.75, 0.95), ('E5', 0.5, 0.4)),
        shot('lowfolk_inside', ('E5', 0.75, 0.6), ('E5', 0.4, 0.35), lift=260),
        shot('lowfolk_aerial', ('E6', 0.2, 0.3), ('E5', 0.55, 0.45), lift=2600, pitch=-0.7),
        shot('camp', ('C3', 0.4, 0.6), ('B3', 0.5, 0.5)),
        shot('camp_inside', ('B3', 0.65, 0.75), ('B3', 0.4, 0.35), lift=220),
        shot('camp_aerial', ('C3', 0.2, 0.8), ('B3', 0.5, 0.5), lift=2400, pitch=-0.6),
        shot('hangars', ('D4', 0.2, 0.2), ('D3', 0.5, 0.45)),
        shot('hangar_inside', ('D3', 0.3, 0.75), ('D3', 0.3, 0.2), lift=200),
        shot('scrapyard', ('F4', 0.85, 0.7), ('G4', 0.5, 0.5)),
        shot('outpost', ('H4', 0.1, 0.75), ('H4', 0.4, 0.45)),
        shot('road_north', ('E1', 0.1, 0.4), ('E1', 0.05, -0.8)),
        shot('road_east', ('H5', 0.6, 0.45), ('H5', 1.8, 0.45)),
        shot('crater_hatch', ('C6', 0.5, 0.45), ('C6', 0.65, 0.75), lift=700),
        shot('terminal_front', ('E4', 0.75, 0.45), ('F4', 0.3, 0.5)),
    ],
}
shots = TOURS[name]
SETTLE = {'people_later': 25.0}
tour = {'output_dir': str(PROJECT / 'review' / name), 'settle_seconds': SETTLE.get(name, 2.5), 'exit': True,
        'shots': shots}
path = PROJECT / f'review_tour_{name}.yml'
path.write_text(json.dumps(tour, indent=1) + '\n')
print(path)
