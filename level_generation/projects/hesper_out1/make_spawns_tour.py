"""Write `review_tour_monsters.yml`: a shot of each hostile group of Starport Reach (work/spawns_plan.json, spawns.py)
from 1 100 units off, toward the map's middle, and three aerial views over the busiest areas.

    python3 level_generation/projects/hesper_out1/make_spawns_tour.py <output_dir>
"""
import json
import math
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2] / 'util'))
from map_export import parse_odm_file  # noqa: E402

output = sys.argv[1]
plan = json.loads((PROJECT / 'work/spawns_plan.json').read_text())
heights = parse_odm_file(PROJECT / 'runtime/worlds/hesper/maps/hes_out1.odm')['payload']['height_map']


def ground(x, y):
    gx, gy = int(round((x + 32768) / 512)), int(round((32768 - y) / 512))
    return heights[min(max(gy, 0), 127) * 128 + min(max(gx, 0), 127)] * 32


def look(name, target, distance=1100, lift=380):
    tx, ty = target
    d = math.hypot(tx, ty) or 1.0
    ex, ey = tx - tx / d * distance, ty - ty / d * distance           # from the map's middle side
    z = max(ground(ex, ey), ground(tx, ty)) + lift
    pitch = math.atan2(ground(tx, ty) + 60 - z - 160, distance)
    return {'name': name, 'position': [round(ex), round(ey), round(z)],
            'yaw': round(math.atan2(ty - ey, tx - ex), 4), 'pitch': round(pitch, 4)}


shots = []
for spawn in plan['spawns']:
    shots.append(look(spawn['name'].replace(' ', '_').replace("'", ''), spawn['position'][:2]))
for squad in plan['squads']:
    xs, ys = [a[0] for a in squad['actors']], [a[1] for a in squad['actors']]
    shots.append(look(squad['name'].replace(' ', '_').replace("'", ''), (sum(xs) / len(xs), sum(ys) / len(ys)),
                      distance=1300, lift=450))
for name, (x, y) in [('aerial_apron_ruins', (-4000, 5000)), ('aerial_glassfields', (16000, 14000)),
                     ('aerial_scrapyard_outpost', (17000, 2500))]:
    shots.append({'name': name, 'position': [x, y - 4500, ground(x, y) + 5500], 'yaw': 1.5708, 'pitch': -0.95})
tour = {'output_dir': output, 'settle_seconds': 1.5, 'exit': True, 'shots': shots}
(PROJECT / 'review_tour_monsters.yml').write_text(yaml.safe_dump(tour, sort_keys=False, width=120))
print(len(shots), 'shots')
