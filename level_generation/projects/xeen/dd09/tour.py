#!/usr/bin/env python3
"""DD-09's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners; 'things':
the interactive things; the commands open doors where a shot needs it."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd09')
import geo
P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd09'
E = 160


def door(n):
    return f'lua evt.SetDoorState({n}, DoorAction.Open)'


ALL_DOORS = [door(n) for n in range(1, 9)]


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
        out.append((f'{rid}-up', [a[0], a[1], fl + E], yaw, 0.1 if to > fl else -0.25, None, []))
    return out


U, L, R_ = 640 + E, 1280 + E, -512 + E
THINGS = [
    ('01-arrival', [0, -2100, E], P / 2, 0.0, None, []),
    ('02-trunk-door-exit', [0, -1700, E], -P / 2, 0.0, None, []),
    ('03-hall-from-door', [0, -1300, E], P / 2, 0.1, None, []),
    ('04-hall-dome', [0, -400, E], P / 2, 0.6, None, []),
    ('05-root-west-alcove', [-6100, 0, R_], P, -0.05, None, []),
    ('06-root-west-to-pens', [-6272, 300, R_], -P / 2, -0.05, None, []),
    ('07-root-east-alcove', [-4480, 1300, R_], P / 2, -0.05, None, []),
    ('08-sap-barrel-sign', [-4512, -2100, R_], -P / 2, -0.1, None, []),
    ('09-sap-vats', [-4900, -1700, R_], -0.4, -0.15, None, []),
    ('10-pens-cages-shut', [-6500, -1760, R_], P, -0.05, None, []),
    ('11-pens-cages-open', [-6500, -1760, R_], P, -0.05, 2.5, ['lua evt.SetDoorState(11, DoorAction.Open)', 'lua evt.SetDoorState(12, DoorAction.Open)']),
    ('12-chapel-flasks', [200, 2300, E], P / 2, 0.0, None, []),
    ('13-chapel-books', [300, 2112, E], P, 0.0, None, []),
    ('14-cells', [6528, 2150, U], P / 2, -0.05, None, []),
    ('15-shaalth-hall', [6100, -1000, U], 0.35, 0.05, None, []),
    ('16-sheewana-cage', [7900, 700, U], 0.8, -0.05, None, []),
    ('17-shaalth-dais', [7300, 0, U], -0.6, -0.1, None, []),
    ('18-tea-kettle', [9600, -300, U], P / 2, -0.15, None, []),
    ('19-ascension-basins', [11392, 600, U], -P / 2, -0.25, None, []),
    ('20-ascension-dials', [11000, -600, U], P / 2 + 0.4, 0.0, None, []),
    ('21-ascension-vault-door', [11600, 0, U], 0.0, 0.0, None, []),
    ('22-limb-walk-alcoves', [6000, -4096, L], 0.0, 0.0, None, []),
    ('23-limb-alcove-1', [8864, -4150, L], P / 2, 0.0, None, []),
    ('24-barkman-hidden', [7600, -4900, L], -0.5, -0.05, None, []),
    ('25-barkman-shown', [7600, -4900, L], -0.5, -0.05, None, ['lua evt.SetMonGroupBit(30, MonsterBits.Invisible, 0)']),
    ('26-crown-fountains', [11500, -4096, L], 0.0, 0.05, None, []),
    ('27-crown-up', [12416, -4096, L], 0.0, 0.9, None, []),
    ('28-ring-stair', [700, -1900, E + 30], -P / 2, 0.0, None, []),
]
FIX = [
    ('01-sheewana-cage', [8150, 650, U], 1.0, -0.05, None, []),
    ('02-sheewana-cage-open', [8150, 650, U], 1.0, -0.05, 3.0, ['lua evt.SetDoorState(9, DoorAction.Open)']),
    ('03-barkman-shown', [7600, -4900, L], -0.75, -0.05, 4.0, ['lua SetValue(MapVar(5), 1)']),
    ('04-chapel-flask-red', [-384, 2500, E], P / 2, -0.1, None, []),
]
SETS = {'rooms': rooms(), 'things': THINGS, 'fix': FIX}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt, 'commands': ['render hud off'] + ALL_DOORS + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
