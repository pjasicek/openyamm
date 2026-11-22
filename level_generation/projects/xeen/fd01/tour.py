#!/usr/bin/env python3
"""FD-01's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners; 'things':
the interactive things and the set piece. The commands open the doors unless a shot closes them."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/fd01')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/fd01'
E = 160
LOCK = yaml.safe_load(open(_REPO_ROOT + '/devdocs/xeen/briefs/fd01/L4/ids.lock.yml'))
DOORS = [n for k, n in LOCK['doors'].items() if k.startswith('door:')]


def door(n, a='Open'):
    return f'lua evt.SetDoorState({n}, DoorAction.{a})'


ALL_DOORS = [door(n) for n in DOORS]
CLOSED = [door(n, 'Close') for n in DOORS]


def rooms():
    out = []
    for rid in geo.ORDER:
        name, o, fl, ce, th = geo.R[rid]
        x0, y0, x1, y1 = geo.bounds(rid)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        pts = [(x0 + 0.12 * (x1 - x0), y0 + 0.12 * (y1 - y0)), (x0 + 0.88 * (x1 - x0), y0 + 0.88 * (y1 - y0))]
        for tag, (px, py) in zip('ab', pts):
            yaw = math.atan2(cy - py, cx - px)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], yaw, -0.1, None, []))
    return out


L = geo.LOW
THINGS = [
    ('01-arrival', [0, 0, E], P, 0.0, None, []),
    ('02-stair-up', [-100, 0, E], 0.0, 0.3, None, []),
    ('03-hatch', [1150, 0, 640 + E], 0.0, 0.1, None, []),
    ('04-statue', [-1100, -500, E], P / 2 + 0.3, 0.05, None, []),
    ('05-gallery-door', [-1300, -512, E], P, 0.0, None, CLOSED),
    ('06-south-gallery', [-2000, -512, E], P, -0.05, None, []),
    ('07-grate-gallery', [-3328, -600, E], P / 2, 0.05, None, CLOSED),
    ('08-guard-door', [-6300, -512, E], P, 0.0, None, CLOSED),
    ('09-west-gallery', [-7168, -400, E], P / 2, -0.05, None, []),
    ('10-shaft-arrival', [-7744, 7168, E], P, 0.15, None, []),
    ('11-shaft-up', [-8000, 7168, E], P, 1.2, None, []),
    ('12-ladder', [-8800, 7168, E], P, 0.2, None, []),
    ('13-shaft-door', [-7800, 7168, E], 0.0, 0.0, None, CLOSED),
    ('14-north-gallery', [-6800, 7168, E], 0.0, -0.05, None, []),
    ('15-north-door', [-2816, 7168, E], -P / 2, 0.0, None, CLOSED),
    ('16-hub', [-2816, 4500, E], -P / 2 - 0.3, -0.05, None, []),
    ('17-plaque-nine', [-2500, 3840, E], 0.0, 0.1, None, []),
    ('18-lever-hall', [-3456, 2950, E], -P / 2, -0.15, None, []),
    ('19-lever-west', [-3700, 2496, E], P, 0.0, None, []),
    ('20-west-slab', [-4608, 1600, E], -P / 2, 0.0, None, CLOSED),
    ('21-workshop', [-5700, 400, E], 0.0, -0.05, None, []),
    ('22-grate-workshop', [-3328, 200, E], -P / 2, 0.05, None, CLOSED),
    ('23-pyramid', [-6200, 200, E], P / 2 + 0.5, 0.05, None, []),
    ('24-assembly', [-5632, 3400, E], P / 2 + 0.2, -0.05, None, []),
    ('25-plaque-fewaee', [-5952, 4700, E], P / 2, 0.15, None, []),
    ('26-east-slab', [-2600, 700, E], 0.0, 0.0, None, CLOSED),
    ('27-keyvault-box', [-1216, 1300, E], -P / 2, -0.2, None, []),
    ('28-warden', [-1216, 2300, E], P / 2 + 0.4, -0.05, None, []),
    ('29-skull-door', [-1216, 2900, E], P / 2, 0.05, None, CLOSED),
    ('30-lift-head', [-1216, 3650, E], P / 2, -0.4, None, []),
    ('31-vault-pair', [-1300, 3904, L + E], 0.0, 0.0, None, CLOSED),
    ('32-stasis', [-600, 3904, L + E], 0.0, -0.08, None, []),
    ('33-coffin', [-260, 3700, L + 200], 0.5, -0.35, None, []),
    ('34-stasis-ring', [500, 4300, L + E], -P + 0.6, -0.05, None, []),
]
MOV = LOCK['doors']
THROWN = {side: [door(MOV[f'mover:lever_{side}_arm'])] for side in ('west', 'east')}
NOMON = ['render actors off']
# session 19 (D-71 P1-P3): the ladder close, the levers up and thrown, the key vault without its robots
POLISH = [
    ('10-shaft-arrival', [-7744, 7168, E], P, 0.15, None, []),
    ('12-ladder', [-8800, 7168, E], P, 0.2, None, []),
    ('12b-ladder-close', [-8980, 7300, E], P + 0.5, 0.35, None, []),
    ('12c-ladder-side', [-9000, 6800, E], P / 2 + 0.6, 0.3, None, []),
    ('18-lever-hall', [-3456, 2950, E], -P / 2, -0.15, None, []),
    ('18b-lever-hall-mid', [-3456, 2496, E], P, -0.05, None, []),
    ('18c-lever-hall-mid-east', [-3456, 2496, E], 0.0, -0.05, None, []),
    ('19-lever-west', [-3700, 2496, E], P, 0.0, None, []),
    ('19b-lever-west-thrown', [-3700, 2496, E], P, 0.0, 4, THROWN['west']),
    ('19c-lever-east', [-3200, 2350, E], 0.3, 0.0, None, []),
    ('19d-lever-east-thrown', [-3200, 2350, E], 0.3, 0.0, 4, THROWN['east']),
    ('27-keyvault-box', [-1216, 1300, E], -P / 2, -0.2, None, []),
    ('27b-keyvault-no-robots', [-1216, 1300, E], -P / 2, -0.2, None, NOMON),
    ('27c-keyvault-back', [-1216, 1900, E + 80], -P / 2, -0.3, None, ['render actors on']),
]
SETS = {'rooms': rooms(), 'things': THINGS, 'polish': POLISH}
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
