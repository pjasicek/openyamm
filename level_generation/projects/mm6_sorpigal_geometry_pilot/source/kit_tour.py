"""Tour for the silhouette-kit prototype: per building its concept view and two street-level three-quarter views.

  python3 source/kit_tour.py <map> <out_dir> <shot>...      (shots as in the map's capture tour, e.g. 87-100_Stable2part1)
"""
import math
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import maps  # noqa: E402
sys.path.insert(0, str(maps.ROOT / 'util'))
import map_export  # noqa: E402


def main():
    stem, out, wanted = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
    capture = maps.original(stem) / 'tour.yml'
    poses = {s['name']: s for s in yaml.safe_load(capture.read_text())['shots']}
    data = map_export.parse_odm_file(maps.odm(stem))['payload']
    shots = []
    for shot in wanted:
        name = shot.split('-', 1)[1]
        shots.append({**poses[name], 'name': f'{name}_concept'})
        model = data['bmodels'][int(name.split('_')[0])]
        V = np.array([[v['x'], v['y'], v['z']] for v in model['vertices']], float)
        doors = [f for f in model['faces'] if f['attributes'] & 0x02000000]
        centre = (V.min(axis=0) + V.max(axis=0)) / 2
        if doors:
            P = V[doors[0]['vertex_indices']]
            n = np.cross(P[1] - P[0], P[2] - P[0])
            n[2] = 0
            n /= np.linalg.norm(n)
            if n @ (P.mean(axis=0) - centre) < 0:
                n = -n
            front = P.mean(axis=0)
        else:
            n, front = np.array([0.6, -0.8, 0]), centre
        size = float(np.ptp(V[:, :2], axis=0).max())
        # a close raised three-quarter view of the door side (the distance of the user's own screenshots)
        position = front + n * max(380, 0.7 * size) + np.array([-n[1], n[0], 0]) * max(200, 0.4 * size)
        position[2] = V[:, 2].max() + 180
        aim = front + np.array([0, 0, 80])
        d = aim - position
        shots.append({'name': f'{name}_close', 'position': [float(c) for c in position],
                      'yaw': round(math.atan2(d[1], d[0]), 4), 'pitch': round(math.atan2(d[2], math.hypot(d[0], d[1])), 4)})
        for k, side in enumerate((-1, 1)):
            lateral = np.array([-n[1], n[0], 0]) * side
            position = front + n * max(450, 0.9 * size) + lateral * max(300, 0.6 * size)
            position[2] = V[:, 2].min() + 150
            aim = front + np.array([0, 0, 120])
            d = aim - position
            shots.append({'name': f'{name}_street{k + 1}', 'position': [float(c) for c in position],
                          'yaw': round(math.atan2(d[1], d[0]), 4),
                          'pitch': round(math.atan2(d[2], math.hypot(d[0], d[1])), 4)})
    out.mkdir(parents=True, exist_ok=True)
    lines = [f'output_dir: {out.resolve()}', 'exit: true', 'settle_seconds: 3.0', 'shots:']
    for s in shots:
        lines += [f"  - name: {s['name']}", f"    position: {s['position']}", f"    yaw: {s['yaw']}",
                  f"    pitch: {s['pitch']}", '    commands: ["render hud off"]']  # review shots without the HUD
    (out / 'tour.yml').write_text('\n'.join(lines) + '\n')
    print(len(shots), 'shots')


if __name__ == '__main__':
    main()
