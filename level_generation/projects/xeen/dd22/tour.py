#!/usr/bin/env python3
"""DD-22's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners; 'things':
the interactive things and the set piece. The commands open the doors (unless a shot keeps them shut)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd22')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd22'
E = 0


def door(n, a='Open'):
    return f'lua evt.SetDoorState({n}, DoorAction.{a})'


ALL_DOORS = [door(n) for n in range(3, 11)]


def rooms():
    out = []
    for rid in sorted(geo.R):
        name, o, fl, ce, th = geo.R[rid]
        x0, y0, x1, y1 = geo.bounds(rid)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for tag, (px, py) in zip('ab', [(x0 + 0.15 * (x1 - x0), y0 + 0.15 * (y1 - y0)),
                                        (x0 + 0.85 * (x1 - x0), y0 + 0.85 * (y1 - y0))]):
            yaw = math.atan2(cy - py, cx - px)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], yaw, -0.05, None, []))
    return out


D1, D2, D3 = geo.D1 + E, geo.D2 + E, geo.D3 + E
THINGS = [
    ('01-arrival', [0, -832, D1], P / 2, 0.0, None, []),
    ('02-hatch', [0, -700, D1], -P / 2, 0.0, None, []),
    ('03-ring-south', [-560, -384, D1], 0.0, 0.0, None, []),
    ('04-ring-east-maint', [576, -360, D1], P / 2, 0.0, None, [door(8, 'Close')]),
    ('05-lift-a-foot', [160, -40, D1], math.atan2(300, -320), 0.0, None, []),
    ('06-stores', [-480, 96, D1], P, -0.1, None, []),
    ('07-drive', [144, 620, D1], P / 2, -0.05, None, []),
    ('08-drive-devices', [-200, 860, D1], P / 2 + 0.6, 0.0, None, []),
    ('09-generator-rack', [300, 900, D1], 0.1, -0.1, None, []),
    ('10-ladder-room', [960, -80, D1], P / 2, 0.35, None, []),
    ('11-ring1-lifts', [0, -300, D2], P / 2, -0.1, None, []),
    ('12-gun-weapons', [760, 256, D2], 0.0, -0.1, None, []),
    ('13-ladder-hatch-above', [960, 520, D2], -P / 2, -0.55, None, []),
    ('14-brig-cells', [-760, 0, D2], P, -0.05, None, []),
    ('15-security-console', [-896, 680, D2], P / 2, -0.1, None, []),
    ('16-blast-door-shut', [-256, -40, D3], P / 2, 0.05, None, [door(4, 'Close'), door(5, 'Close')]),
    ('17-bridge-entry', [-256, 680, D3], P / 2 - 0.35, 0.15, None, []),
    ('18-bridge-dome', [0, 640, D3], P / 2, 0.7, None, []),
    ('19-bridge-consoles', [0, 1220, D3 + 40], P / 2, -0.05, None, []),
    ('20-log-computer', [560, 1088, D3], 0.0, 0.0, None, []),
    ('21-couch-locker', [0, 660, D3], P / 2, -0.25, None, []),
    ('22-bridge-back', [500, 1450, D3 + 60], -P / 2 - 0.5, -0.1, None, []),
    ('23-drive-grille-z0', [-200, 860, 0], P / 2 + 0.6, 0.0, None, []),
    ('24-drive-rack-z0', [300, 900, 0], 0.1, -0.1, None, []),
    ('25-oculus', [0, 1056, D3], P / 2, 1.3, None, []),
    ('26-couch-side', [-520, 1100, D3], -0.25, -0.2, None, []),
    ('27-couch-front', [0, 1380, D3], -P / 2, -0.3, None, []),
]
SETS = {'rooms': rooms(), 'things': THINGS}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt,
         'commands': ['render hud off'] + ALL_DOORS + [door(4), door(5)] + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
