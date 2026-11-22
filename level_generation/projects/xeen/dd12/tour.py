#!/usr/bin/env python3
"""DD-12's tours: tour.py <set> <name> [prefix ...] writes shots/<name>.yml from L4's rooms.yml. Set 'rooms': every
room from two corners, every flight from its foot and its head; 'things': the gates, the plaque, the hourglasses, the
cells, the dials and fountains, the levers, the statues, the throne, the cages, the lift. Every door open, HUD off."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

P = math.pi
R = _REPO_ROOT
X = R + '/output/studio_cal/dd12'
E = 160
ROOMS = yaml.safe_load(open(R + '/devdocs/xeen/briefs/dd12/L4/rooms.yml'))['rooms']
LOCK = yaml.safe_load(open(R + '/devdocs/xeen/briefs/dd12/L4/ids.lock.yml'))
DOOR_IDS = [n for k, n in LOCK['doors'].items() if k.startswith('door:')]
DOORS = [f'lua evt.SetDoorState({n}, DoorAction.Open)' for n in sorted(DOOR_IDS)]
YAW = {'north': P / 2, 'south': -P / 2, 'east': 0.0, 'west': P}


def rooms():
    out = []
    for r in ROOMS:
        rid = r['id'].split(':')[1]
        xs = [p[0] for p in r['outline']]
        ys = [p[1] for p in r['outline']]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        fl = r['floor']
        if 'slope' in r:
            t = r['slope']['toward']
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if t in ('north', 'south'):
                low, high = ((cx, y0 + 40), (cx, y1 - 40)) if t == 'north' else ((cx, y1 - 40), (cx, y0 + 40))
            else:
                low, high = ((x0 + 40, cy), (x1 - 40, cy)) if t == 'east' else ((x1 - 40, cy), (x0 + 40, cy))
            out.append((f'{rid}-foot', [int(low[0]), int(low[1]), fl + E], YAW[t], 0.25))
            back = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[t]
            out.append((f'{rid}-head', [int(high[0]), int(high[1]), fl + 640 + E], YAW[back], -0.35))
            continue
        if rid.startswith('maze_'):
            # stand in the letter's first cell (from the outline's lowest-left point) looking along it
            px, py = x0 + 128, y0 + 128
            out.append((f'{rid}-a', [int(px), int(py), fl + E], math.atan2((y0 + y1) / 2 - py, (x0 + x1) / 2 - px), -0.05))
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for tag, fx, fy in (('a', 0.12, 0.12), ('b', 0.88, 0.88)):
            px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
            if rid == 'entry':
                px, py = (0, -380) if tag == 'a' else (0, 380)
            if rid == 'shaft':
                px, py = cx, cy
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], math.atan2(cy - py, cx - px), -0.05))
    return out


L1, L2, L3, L4, L5 = E, -640 + E, -1280 + E, -1920 + E, -2560 + E
THINGS = [
    ('01-entry-gate-plaque', [0, -300, L1], P / 2, 0.15),
    ('02-entry-door-out', [0, 200, L1], -P / 2, 0.0),
    ('03-entry-sky', [0, 0, L1], P / 2, 1.2),
    ('04-gallery-west-vault-lift', [-1000, 780, L1], P, 0.0),
    ('05-store-a-glass', [864, 1250, L1], P / 2, 0.0),
    ('06-store-b', [1500, 1360, L1], 0.0, 0.0),
    ('07-store-c-glass', [1152, 300, L1], -P / 2, 0.0),
    ('08-store-d-bones', [1800, 200, L1], -0.6, -0.1),
    ('09-lift-head', [-2320, 800, L1], P / 2, 0.0),
    ('10-statue2', [2592, -1600, L2], -P / 2, 0.0),
    ('11-cells', [1184, -2300, L2], -P / 2 - 0.3, -0.05),
    ('12-gate2', [0, -2048, L2], P, 0.0),
    ('13-pool', [-2000, -1600, L3], -2.4, -0.1),
    ('14-dials', [-600, -1500, L3], P / 2 + 0.6, 0.05),
    ('15-dial-statue', [-1200, -1600, L3], P + 0.3, 0.0),
    ('16-soul-waters', [768, -1600, L3], P / 2, 0.0),
    ('17-negative', [800, -2700, L3], -P / 2, 0.0),
    ('18-gate3', [1800, -2048, L3], 0.0, 0.0),
    ('19-plaque-statue', [4096, -1600, L4], -P / 2, 0.0),
    ('20-levers', [4800, -2048, L4], 0.0, 0.05),
    ('21-reserve', [5504, -3100, L4], -P / 2, 0.0),
    ('22-gate4', [6912, -2300, L4], P / 2, 0.0),
    ('23-statues5', [6900, -300, L5], P / 2 - 0.3, 0.05),
    ('24-maze-mouth', [6800, 1920, L5], P, 0.0),
    ('25-throne', [2336, 2600, L5], -P / 2, -0.15),
    ('25b-throne-close', [2600, 1940, L5], P, -0.1),
    ('26-illusion', [4640, 1980, L5], -P / 2, -0.1),
    ('27-gate5', [-1000, 2112, L5], P, 0.0),
    ('28-aviary-n', [-2672, 2300, L5], P / 2, 0.0),
    ('29-aviary-sw', [-2672, 2300, L5], -2.4, 0.0),
    ('30-aviary-lift', [-2304, 2000, L5], -P / 2, 0.0),
    ('31-barracks', [4400, -900, L4], 0.0, 0.0),
    ('32-maze-heart-in', [2336, 2900, L5], -P / 2, -0.1),
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
