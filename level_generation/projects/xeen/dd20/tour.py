#!/usr/bin/env python3
"""DD-20's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners and every
stair; 'things': the interactive things; the commands open the doors where a shot needs it."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd20')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd20'
E = 160


def door(n):
    return f'lua evt.SetDoorState({n}, DoorAction.Open)'


ALL_DOORS = [door(n) for n in range(1, 11)]


def rooms():
    out = []
    for rid in sorted(geo.R):
        name, (x0, y0, x1, y1), fl, ce, th = geo.R[rid]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for tag, fx, fy in (('a', 0.2, 0.2), ('b', 0.8, 0.8)):
            px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
            yaw = math.atan2(cy - py, cx - px)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], yaw, -0.05, None, []))
    for rid, (name, path, fl, to, h, th) in geo.P.items():
        a, b = path[0], path[1]
        yaw = math.atan2(b[1] - a[1], b[0] - a[0])
        out.append((f'{rid}-down', [a[0], a[1], fl + E], yaw, -0.2, None, []))
    return out


C, S_, U = E, -256 + E, -512 + E
THINGS = [
    ('01-arrival-guild', [-640, -384, C], P / 2, 0.0, None, []),
    ('02-init-cauldron', [-640, -500, C], 0.3, -0.15, None, []),
    ('03-seal-doors-shut', [-640, 900, C], P / 2, 0.05, None, ['lua evt.SetDoorState(6, DoorAction.Close)', 'lua evt.SetDoorState(7, DoorAction.Close)']),
    ('04-seal-doors-open', [-640, 900, C], P / 2, 0.05, 2.5, []),
    ('05-hall-stair-foot', [-640, 1200, C], -P / 2, 0.0, None, []),
    ('06-guild-landing-exit', [-640, -3500, 640 + E], -P / 2, 0.0, None, []),
    ('07-head-witch-mirror', [-3200, 4400, C], P / 2, 0.0, None, []),
    ('08-head-witch-bed-chest', [-3200, 4300, C], P - 0.3, -0.1, None, []),
    ('09-brewery-cauldrons', [-640, 3200, C], P / 2, -0.1, None, []),
    ('10-dormitory', [1400, -100, C], 0.0, -0.05, None, []),
    ('11-store-hatch', [1700, -1500, C], -0.6, -0.3, None, []),
    ('12-cells-cages', [5000, 1000, S_], 0.4, 0.0, None, []),
    ('13-cells-rhett', [6900, 1000, S_], P / 2, 0.0, None, []),
    ('14-cages-open', [5000, 1000, S_], 0.4, 0.0, 3.0, [door(11), door(12), door(13), door(14)]),
    ('15-sump-arrival', [3456, -640, U], 0.0, 0.0, None, []),
    ('16-sump-trapdoor', [3456, -900, U], P / 2, 0.9, None, []),
    ('17-main-drain', [4400, -384, U], 0.0, 0.0, None, []),
    ('18-cross', [9000, -800, U], 0.6, 0.0, None, []),
    ('19-cross-ambush', [9000, -800, U], 0.6, 0.0, 2.0, ['lua evt.SetMonGroupBit(6, MonsterBits.Invisible, 0)']),
    ('20-cistern-ladder', [1500, -1700, U], 0.0, 0.1, None, [door(15)]),
    ('21-outfall-pool', [12600, 200, U], 0.6, -0.05, None, []),
    ('22-outfall-bars', [13300, 1000, U], P / 2, 0.05, None, []),
    ('23-niche-alcove', [15100, 1900, U], 0.0, -0.05, None, []),
    ('24-jetty-shaft', [14000, -1152, U], 0.0, 0.2, None, []),
    ('25-hideout-grate', [9600, -1350, U], -P / 2, 0.4, None, []),
    ('26-east-drain', [10500, -1152, U], 0.0, 0.0, None, []),
]
FIX = [
    ('01-store-hatch', [1700, -1500, C], -0.6, -0.3, None, []),
    ('02-store-hatch-near', [2176, -1500, C], -P / 2, -0.7, None, []),
    ('03-hall-benches', [-400, 640, C], P, -0.05, None, []),
    ('04-hideout-grate-up', [9600, -1500, U], -P / 2, 1.2, None, []),
    ('05-main-grate-up', [6528, -700, U], P / 2, 1.0, None, []),
    ('06-cross-grate-up', [9472, 100, U], -P / 2, 1.2, None, []),
    ('07-cistern-hatch-up', [2176, -1700, U], -P / 2, 1.0, None, [door(15)]),
]
SETS = {'rooms': rooms(), 'things': THINGS, 'fix': FIX}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt,
         'commands': ['render hud off'] + (ALL_DOORS if s == 'rooms' or n not in ('03-seal-doors-shut',) else []) + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
