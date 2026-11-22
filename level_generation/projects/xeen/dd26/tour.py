#!/usr/bin/env python3
"""DD-26's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners; 'things':
the interactive things and the set piece. The commands open the doors unless a shot closes them."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd26')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd26'
E = 160


def door(n, a='Open'):
    return f'lua evt.SetDoorState({n}, DoorAction.{a})'


ALL_DOORS = [door(n) for n in range(1, 7)]
CLOSED = [door(n, 'Close') for n in range(1, 7)]


def rooms():
    out = []
    for rid in geo.ORDER:
        name, o, fl, ce, th = geo.R[rid]
        x0, y0, x1, y1 = geo.bounds(rid)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        pts = [(x0 + 0.1 * (x1 - x0), y0 + 0.1 * (y1 - y0)), (x0 + 0.9 * (x1 - x0), y0 + 0.9 * (y1 - y0))]
        for tag, (px, py) in zip('ab', pts):
            yaw = math.atan2(cy - py, cx - px)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], yaw, -0.12, None, []))
    return out


THINGS = [
    ('01-arrival', [0, 0, E], P / 2, 0.0, None, []),
    ('02-stair-up', [0, 200, E], -P / 2, 0.3, None, []),
    ('03-stair-head-grate', [0, -900, geo.STAIR_TOP + E], -P / 2, 0.1, None, []),
    ('04-scroll', [-60, -192, E], P, 0.0, None, []),
    ('05-conduit-west', [-200, 320, E], P, -0.1, None, []),
    ('06-den-door', [0, 500, E], P / 2, 0.0, None, CLOSED),
    ('07-den-counter', [0, 1150, E], P / 2, -0.05, None, []),
    ('08-den-bed', [100, 1500, E], -0.6, -0.25, None, []),
    ('09-west-culvert', [-2080, 400, E], P / 2, -0.05, None, []),
    ('10-drain-tr', [-2120, 1536, E], 0.0, -0.3, None, []),
    ('11-spill-grate', [-2150, 1088, E], P, 0.0, None, CLOSED),
    ('12-spillway', [-2620, 800, E], P / 2 + 0.6, -0.15, None, []),
    ('13-cistern-west', [-2200, 2100, E], 0.25, -0.15, None, []),
    ('14-cistern-basin', [0, 2100, E + 64], P / 2, -0.35, None, []),
    ('15-drain-bl', [0, 2800, E], P / 2, -0.3, None, []),
    ('16-tribble-door', [2350, 2560, E], 0.0, 0.1, None, CLOSED),
    ('17-tribble-landing', [2650, 2560, E], 0.0, 0.25, None, CLOSED),
    ('18-vault', [3300, 2300, E], 0.3, -0.1, None, []),
    ('19-vault-chest', [3800, 2560, E], 0.0, -0.15, None, []),
    ('20-outfall', [2620, 1088, E], 0.0, -0.1, None, []),
    ('21-east-culvert', [2080, 1750, E], -P / 2, -0.05, None, []),
    ('22-conduit-east', [200, 704, E], 0.0, -0.1, None, []),
]
SETS = {'rooms': rooms(), 'things': THINGS}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt,
         'commands': ['render hud off'] + ALL_DOORS + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
