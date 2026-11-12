"""Write a map's review tour: a raised pose in front of each building's door, a raised three-quarter pose on every
other large model (walls, towers, bridges, castles), then the map's hand-placed poses (`poses:` in its map file;
New Sorpigal's are below).

  python3 source/town_tour.py [--map <stem>] <output_dir>
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'util'))
import map_export  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import maps  # noqa: E402
SKIP = ('Create', 'Sgn', 'Sign', 'BridgeT', 'mm6_ship', 'Fountain', 'Wop', 'Wer', 'Well')
MANUAL = [
    # name, position, aim point
    ('gate', (-9728, -10900, 161), (-9728, -9916, 400)),
    ('town_walls', (-12500, -10700, 400), (-10688, -9932, 230)),
    ('dock_ship', (-400, -11400, 500), (2168, -10200, 300)),
    ('ship_close', (900, -11000, 200), (2168, -10200, 400)),
    ('fountain_square', (-10400, -6000, 400), (-9728, -7168, 160)),
    ('crypt', (-16944, -10700, 400), (-16944, -9708, 250)),
    ('dungeon_entrance', (-21456, 900, 1000), (-21456, -248, 350)),
    ('obelisk', (-13566.536, 14966.146, 1268.005), (-14056, 16048, 500)),
    ('temple', (-9744, -3200, 1300), (-9744, -1072, 900)),
    ('bridge_north', (-16144, -5400, 400), (-16144, -4720, 200)),
]


# The user's pilot views (yaw, pitch in radians) and close-ups of details the far concept views do not show; added
# after the numbered poses above so the concept names stay the same.
DIRECT = [
    ('tavern_v01', (-9563.396, -8718.901, 161), 0.023, math.radians(0.172)),
    ('tavern_roof', (-9600, -9900, 1000), math.atan2(1210, 1664), math.radians(-8)),
    ('bridge_v08', (-19384.920, -11222.390, 658.781), 2.181, math.radians(-40.050)),
    ('goblinwatch_v07', (-18421.469, -13917.778, 2338.048), 4.719, math.radians(-22.775)),
    ('goblinwatch_front', (-18432, -14450, 1660), -math.pi / 2, math.radians(10)),
    ('armory_v03', (-8892.189, -6804.438, 161), 0.567, math.radians(-8.079)),
]
CLOSE = [
    ('close_gate_pillar', (-9300, -10350, 161), (-9424, -9916, 300)),
    ('close_gate_top', (-9250, -10250, 700), (-9424, -9916, 640)),
    ('close_wall', (-11000, -10350, 161), (-10688, -9932, 230)),
    ('close_tavern_porch', (-9250, -8900, 161), (-8900, -8690, 160)),
    ('close_goblinwatch', (-18000, -14700, 1700), (-18432, -15104, 1800)),
]


def pose(name, position, aim):
    name = re.sub(r'[^A-Za-z0-9_-]', '_', name)  # the tour accepts letters, digits, '_' and '-'
    d = np.array(aim, float) - np.array(position, float)
    yaw = math.atan2(d[1], d[0])
    pitch = math.atan2(d[2] - 140, math.hypot(d[0], d[1]))
    return {'name': name, 'position': [float(c) for c in position], 'yaw': round(yaw, 4), 'pitch': round(pitch, 4)}


def main():
    args = sys.argv[1:]
    stem = 'oute3'
    if '--map' in args:
        stem = args.pop(args.index('--map') + 1)
        args.remove('--map')
    out = Path(args[0])
    data = map_export.parse_odm_file(maps.odm(stem))['payload']
    scale = maps.config(stem).get('pose_scale', 1.0)  # closer poses on foggy maps
    shots = []
    for model in data['bmodels']:
        if model['name'].startswith(SKIP) or len(model['faces']) < 15:
            continue
        V = model['vertices']
        xs, ys, zs = ([v[k] for v in V] for k in 'xyz')
        size = max(max(xs) - min(xs), max(ys) - min(ys))
        doors = [f for f in model['faces'] if f['attributes'] & 0x02000000 and f['cog_triggered_number']]
        if not doors:
            if stem != 'oute3' and len(model['faces']) >= 30:
                centre = np.array([(max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)])
                distance = max(900, 1.4 * size) * scale
                position = centre + np.array([0.6, -0.8, 0]) * distance + [0, 0, 500 + 0.3 * (max(zs) - min(zs))]
                aim = [centre[0], centre[1], min(zs) + (max(zs) - min(zs)) * 0.4]
                shots.append(pose(f"{model['index']:02d}_{model['name']}", position, aim))
            continue
        door = max(doors, key=lambda f: len(f['vertex_indices']))
        P = np.array([[V[i]['x'], V[i]['y'], V[i]['z']] for i in door['vertex_indices']], float)
        n = np.zeros(3)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
        n /= np.linalg.norm(n)
        if abs(n[2]) > 0.5:
            continue
        centre = P.mean(axis=0)
        distance = max(800, 1.5 * size) * scale
        position = centre + np.array([n[0], n[1], 0]) * distance
        position[2] = min(zs) + 420 * scale
        aim = [centre[0], centre[1], min(zs) + (max(zs) - min(zs)) * 0.45]
        # step to one side so the facade is seen at an angle
        side = np.array([-n[1], n[0], 0]) * distance * 0.35
        shots.append(pose(f"{model['index']:02d}_{model['name']}", position + side, aim))
    if stem == 'oute3':
        shots += [pose(*entry) for entry in MANUAL]
        shots += [{'name': name, 'position': [float(c) for c in position], 'yaw': round(yaw, 4),
                   'pitch': round(pitch, 4)} for name, position, yaw, pitch in DIRECT]
        shots += [pose(*entry) for entry in CLOSE]
    shots += [pose(p['name'], p['position'], p['aim']) for p in maps.config(stem).get('poses', [])]
    lines = [f'output_dir: {out.resolve()}', 'exit: true', 'settle_seconds: 3.0', 'shots:']
    for shot in shots:
        lines += [f"  - name: {shot['name']}", f"    position: {shot['position']}", f"    yaw: {shot['yaw']}",
                  f"    pitch: {shot['pitch']}"]
    out.mkdir(parents=True, exist_ok=True)
    (out / 'tour.yml').write_text('\n'.join(lines) + '\n')
    print(len(shots), 'shots')


if __name__ == '__main__':
    main()
