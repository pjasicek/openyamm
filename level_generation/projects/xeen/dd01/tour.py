#!/usr/bin/env python3
"""DD-01's tours: tour.py <set> <name> writes shots/<name>.yml (every room and interactive thing, before and after)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd01'
E = 160
D = -512 + E


def door(n):
    return f'lua evt.SetDoorState({n}, DoorAction.Open)'


SETS = {
    'rooms': [
        ('01-hatch-shaft-ladder', [0, -1000, E], -P / 2, 0.25, None, []),
        ('02-hatch-shaft-up', [0, -1000, E], -P / 2, 1.2, None, []),
        ('03-cross-from-south', [0, -560, E], P / 2, 0.05, None, []),
        ('04-cross-from-ne', [450, 450, E], -3 * P / 4, 0.0, None, []),
        ('05-west-drain', [-900, -240, E], P, 0.0, None, []),
        ('06-west-drain-mid', [-2000, -240, E], P, 0.0, None, []),
        ('07-guild-shaft', [-3400, 0, E], P, 0.1, None, []),
        ('08-sluice-from-drain', [-1408, 700, E], P / 2, 0.05, None, []),
        ('09-sluice-lever-gate', [-1300, 1250, E], P / 2 + 0.35, 0.0, None, []),
        ('10-sluice-gate-shut', [-1300, 1250, E], P / 2 + 0.35, 0.0, 5.0, [door(9)]),
        ('11-north-drain', [-500, 1152, E], 0.0, 0.0, None, [door(6), door(5)]),
        ('12-gate-shaft-bones', [1920, 1700, E], P / 2, -0.25, None, []),
        ('13-east-drain', [1000, -240, E], 0.0, 0.0, None, [door(1), door(2)]),
        ('14-east-drain-grate', [4250, -240, E], 0.0, -0.45, None, []),
        ('15-market-shaft', [3200, 600, E], P / 2, 0.1, None, [door(4)]),
        ('16-temple-shaft', [5300, 0, E], 0.0, 0.1, None, []),
        ('17-felix-tunnel', [-2880, -700, E], -P / 2, 0.0, None, []),
        ('18-felix-bench', [-2880, -2450, E], -P / 2, -0.25, None, []),
        ('19-valio-bed', [-2420, -1560, E], -P / 2 + 0.6, -0.25, None, []),
        ('20-overflow', [-1600, -1450, E], -P / 4, -0.05, None, [door(7)]),
        ('21-overflow-stair', [-1152, -2350, E], -P / 2, -0.25, None, []),
        ('22-deep-cistern', [-1152, -3950, D], -P / 2, 0.0, None, []),
        ('23-outfall', [500, -4864, D], 0.0, 0.0, None, [door(3)]),
        ('24-outfall-grate-bar', [3900, -4864, D], 0.0, 0.0, None, []),
        ('25-rat-runs', [500, -4250, D], P / 4, 0.0, None, []),
        ('26-culvert-flooded', [1280, -3420, D], P / 2, 0.0, None, []),
        ('27-culvert-draining', [1280, -3420, D], P / 2, 0.0, 2.0, [door(10)]),
        ('28-culvert-drained', [1280, -3420, D], P / 2, 0.0, 6.0, []),
        ('29-inside-culvert', [1280, -2600, D], P / 2, 0.1, None, []),
        ('30-nest-ramp', [1500, -1408, -380 + E], 0.0, 0.05, None, []),
        ('31-nest', [2550, -1550, -224 + E], -P / 4, 0.0, None, []),
        ('32-nest-heap', [3450, -2550, -224 + E], -P / 4, -0.2, None, []),
        ('33-bone-slide', [4250, -2048, -224 + E], 0.0, -0.15, None, []),
        ('34-midden', [5450, -2100, -480 + E], 0.0, -0.05, None, []),
        ('35-cellar', [5650, -800, -480 + E], P, 0.0, None, []),
        ('36-cellar-ladder-up', [4850, -500, -480 + E], P - 0.4, 0.45, None, []),
        ('37-grate-open', [4250, -240, E], 0.0, -0.45, 3.0, [door(8)]),
    ],
    'fix': [
        ('01-hatch-shaft-up', [0, -1000, E], -P / 2, 1.2, None, []),
        ('02-outfall-grate', [3900, -4864, D], 0.0, 0.0, None, []),
        ('03-east-drain-grate', [4300, -128, E], 0.0, -0.45, None, []),
        ('04-valio-bed', [-2050, -1520, E], -P / 2 - 0.7, -0.3, None, []),
    ],
}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt, 'commands': ['render hud off'] + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 2.0, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
