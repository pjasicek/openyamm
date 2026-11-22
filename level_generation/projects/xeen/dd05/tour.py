#!/usr/bin/env python3
"""DD-05's tours: tour.py <set> <name> writes shots/<name>.yml from L4's rooms.yml. Set 'rooms': every room from two
corners, every stair from its foot and its head; 'things': the chapel's cone and beams, the altar and sun, the
alcoves, the tapestries, the mirror, the fountains, the cells. Every door open, HUD off."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

P = math.pi
R = _REPO_ROOT
X = R + '/output/studio_cal/dd05'
E = 160
ROOMS = yaml.safe_load(open(R + '/devdocs/xeen/briefs/dd05/L4/rooms.yml'))['rooms']
DOORS = [f'lua evt.SetDoorState({n}, DoorAction.Open)' for n in range(1, 14)]
# Stairs: (room, rising toward 'north' or 'south', floor at the foot)
STAIRS = {'east_stair2': 'north', 'south_stair2': 'north', 'outer_stair3': 'north', 'west_stair3': 'north',
          'altar_stair': 'north', 'tower_stair': 'south'}


def rooms():
    out = []
    for r in ROOMS:
        rid = r['id'].split(':')[1]
        xs = [p[0] for p in r['outline']]
        ys = [p[1] for p in r['outline']]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        fl = r['floor']
        if rid in STAIRS:
            cx = (x0 + x1) / 2
            n = STAIRS[rid] == 'north'
            foot, head = (y0 + 40, y1 - 40) if n else (y1 - 40, y0 + 40)
            out.append((f'{rid}-foot', [int(cx), int(foot), fl + E], P / 2 if n else -P / 2, 0.25))
            out.append((f'{rid}-head', [int(cx), int(head), fl + 640 + E], -P / 2 if n else P / 2, -0.35))
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for tag, fx, fy in (('a', 0.12, 0.12), ('b', 0.88, 0.88)):
            px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], math.atan2(cy - py, cx - px), -0.05))
    return out


L4, L3, L2, L1 = 1920 + E, 1280 + E, 640 + E, E
THINGS = [
    ('01-chapel-cone-up', [-704, 1216, L4], P, 1.1),
    ('02-chapel-cone-beams', [200, 1216, L4], P, 0.45),
    ('03-chapel-altar-sun', [-900, 1216, L4], P, 0.1),
    ('04-chapel-doors-in', [-300, 1216, L4], 0.0, 0.0),
    ('05-chapel-from-altar', [-1300, 1500, L4], -0.25, 0.15),
    ('06-tapestries', [-224, -450, L4], P / 2, 0.1),
    ('07-tapestries-wide', [200, -500, L4], P - 0.6, 0.05),
    ('08-vestry-panel', [-1000, -384, L4], 0.0, 0.0),
    ('09-hoist-window', [1376, 1200, L4], P / 2, 0.05),
    ('10-gallery-bones', [672, 0, L4], P / 2, -0.1),
    ('11-alcoves-north', [0, 0, L1], P / 2, 0.05),
    ('12-alcove-west-disc', [-560, 832, L1], P, -0.1),
    ('13-alcove-east-disc', [560, 832, L1], 0.0, -0.1),
    ('14-alcove-pegasus', [0, 900, L1], P / 2, -0.15),
    ('15-mirror', [-448, -1040, L1], P / 2, 0.0),
    ('16-front-door', [0, -1300, L1], -P / 2, 0.05),
    ('17-fountains3', [0, 300, L3], -P / 2, -0.05),
    ('18-fountains2', [-900, 900, L2], P / 2, -0.05),
    ('19-pious', [0, -1350, L3], -P / 2, -0.1),
    ('20-humble', [1024, 1400, L2], P / 2, -0.1),
    ('21-cloister-windows', [-1200, -960, L3], 0.0, 0.05),
    ('22-kitchen-hearth', [1100, -900, L2], -0.5, -0.05),
    ('23-refectory', [0, -900, L2], P / 2, -0.05),
    ('24-guardians', [1100, -1250, L1], -0.6, -0.05),
]
SETS = {'rooms': rooms(), 'things': THINGS}
s, name = sys.argv[1], sys.argv[2]
only = set(sys.argv[3:])
shots = []
for n, p, y, pt in SETS[s]:
    if only and not any(n.startswith(o) for o in only):
        continue
    shots.append({'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt,
                  'commands': ['render hud off'] + DOORS})
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
