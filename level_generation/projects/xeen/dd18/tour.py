#!/usr/bin/env python3
"""DD-18's tours: tour.py <set> <name> writes shots/<name>.yml (every room and interactive thing, before and after)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd18'
E = 160
D = -640 + E
G = 1504 + 170


def door(n):
    return f'lua evt.SetDoorState({n}, DoorAction.Open)'


ALL = [door(n) for n in range(1, 8)]
SETS = {
    'rooms': [
        ('01-shaft-arrival-south', [0, 128, E], -P / 2, 0.1, None, []),
        ('02-shaft-ladder', [0, -150, E], P / 2, 0.25, None, []),
        ('03-shaft-up', [0, -100, E], P / 2, 1.3, None, []),
        ('04-gym-from-door', [0, -560, E], -P / 2, -0.05, None, [door(5)]),
        ('05-gym-shelf-brews', [0, -1300, E], -P / 2, -0.35, None, []),
        ('06-gym-bench', [-150, -1100, E], P, -0.25, None, []),
        ('07-gym-back-to-door', [0, -1500, E], P / 2, 0.0, None, []),
        ('08-main-drain', [620, 0, E], 0.0, 0.0, None, [door(4)]),
        ('09-main-drain-mid', [2000, -240, E], 0.0, 0.0, None, []),
        ('10-warren', [3700, 0, E], 0.0, 0.0, None, []),
        ('11-breeding-vault', [4352, 900, E], P / 2, 0.0, None, []),
        ('12-cistern-from-warren', [5400, 0, E], 0.0, 0.05, None, [door(7)]),
        ('13-cistern-from-se', [7400, -1200, E], 3 * P / 4, 0.1, None, []),
        ('14-cistern-chest', [7000, 448, E], 0.0, -0.3, None, []),
        ('15-alcoves', [1200, -960, E], 0.0, 0.0, None, [door(2)]),
        ('16-alcove-chest', [2240, -1300, E], -P / 2, -0.3, None, []),
        ('17-alcove-empty', [1472, -1300, E], -P / 2, -0.1, None, []),
        ('18-cobra-drain', [3700, -1500, E], 0.0, 0.0, None, []),
        ('19-broken-drain', [6528, -1800, E], -P / 2, -0.1, None, []),
        ('20-rubble-slope', [6528, -3300, E], -P / 2, -0.25, None, []),
        ('21-tunnel-head', [6528, -5300, D], -P / 2 - 0.5, 0.0, None, []),
        ('22-mantis-gallery', [5400, -5760, D], P, 0.0, None, []),
        ('23-mantis-nest', [4608, -6800, D], -P / 2, 0.0, None, []),
        ('24-egg-cells', [5950, -8064, D], 0.0, 0.0, None, []),
        ('25-drowned-vault', [2368, -6250, D], -P / 2, -0.1, None, [door(3)]),
        ('26-tunnel-east', [3300, -5696, D], P, 0.0, None, []),
        ('27-sand-drift', [-500, -5696, D], P, 0.0, None, []),
        ('28-tunnel-west', [-3300, -5696, D], P, 0.0, None, []),
        ('29-desert-gate', [-6950, -5696, D], P, 0.05, None, [door(6)]),
        ('30-desert-gate-pack', [-7400, -5500, D], -P * 0.8, -0.3, None, []),
    ],
    'd3': [
        ('01-arrival-east', [-16896, 16384, G], 0.0, 0.0, None, []),
        ('02-arrival-back-to-lid', [-16500, 16384, G], P, -0.15, None, []),
        ('03-lid-from-south', [-17408, 15500, G], P / 2, -0.15, None, []),
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
