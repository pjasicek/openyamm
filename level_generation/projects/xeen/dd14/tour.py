#!/usr/bin/env python3
"""DD-14's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners (two-storey
rooms also from their head); 'things': the interactive things; 'fix': the shots of a fix. The commands open the doors
and, in 'rooms', show the hidden sleepers."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd14')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd14'
E = 160


def door(n):
    return f'lua evt.SetDoorState({n}, DoorAction.Open)'


ALL_DOORS = [door(n) for n in range(1, 20)]
HEADS = {'sw_tower': geo.L1, 'se_tower': geo.L1, 'stair_hall3': geo.L2, 'back_stair': geo.L2, 'dstair': geo.L3}
HEAD_AT = {'sw_tower': (-1600, -1344), 'se_tower': (1600, -1344), 'stair_hall3': (640, 2240),
           'back_stair': (-2752, 640), 'dstair': (-1920, 2752)}


def rooms():
    out = []
    for rid in sorted(geo.R):
        name, (x0, y0, x1, y1), fl, ce, th = geo.R[rid]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for tag, fx, fy in (('a', 0.15, 0.15), ('b', 0.85, 0.85)):
            px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
            yaw = math.atan2(cy - py, cx - px)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], yaw, -0.05, None, []))
        if rid in HEADS:
            hx, hy = HEAD_AT[rid]
            yaw = math.atan2(cy - hy, cx - hx)
            out.append((f'{rid}-head', [hx, hy, HEADS[rid] + E], yaw, -0.35, None, []))
    return out


L1, L2, L3, D = geo.L1 + E, geo.L2 + E, geo.L3 + E, geo.DUN + E
SHOW = ['lua for g = 11, 15 do evt.SetMonGroupBit(g, MonsterBits.Invisible, 0) end']
THINGS = [
    ('01-arrival', [0, -1472, L1], P / 2, 0.0, None, []),
    ('02-arrival-down', [0, -1400, L1], P / 2, -0.45, None, []),
    ('03-landing-coffins', [0, -1300, L1], -P / 2 - 0.4, -0.2, None, []),
    ('04-perch-bones', [0, -1500, L1], -P / 2 + 0.3, -0.3, None, []),
    ('05-yard-gate-landing', [-960, -1500, L1], P / 2, -0.05, None, []),
    ('06-sw-tower-head', [-1600, -1344, L1], P + 0.6, -0.4, None, []),
    ('07-sw-tower-foot', [-1600, -1700, L2], P, 0.25, None, []),
    ('08-west-walk', [-1920, -900, L1], P / 2, 0.0, None, []),
    ('09-nw-gong', [-1900, 1664, L1], P, 0.0, None, []),
    ('10-north-walk-keepdoor', [-600, 1300, L1], 0.6, 0.0, None, []),
    ('11-roost-trapdoor', [-300, 2200, L1], 0.6, 0.6, None, []),
    ('12-east-walk-plates', [1600, -900, L1], P / 2, -0.25, None, []),
    ('13-se-tower-coffin', [1700, -1344, L1], 0.3, -0.25, None, []),
    ('14-gallery-portraits', [-700, -1300, L2], -P / 2, 0.0, None, []),
    ('15-chapel-altar', [640, -1300, L2], -P / 2, -0.05, None, []),
    ('16-chapel-doors', [300, -1664, L2], P, 0.0, None, ['lua evt.SetDoorState(5, DoorAction.Close)', 'lua evt.SetDoorState(6, DoorAction.Close)']),
    ('17-library', [1700, -800, L2], P / 2, -0.05, None, []),
    ('18-keep-hall', [-2200, 1300, L2], 0.4, 0.05, None, []),
    ('19-grand-stair-down', [640, 2200, L2], -P / 2, -0.5, None, []),
    ('20-study', [-1100, 2700, L2], 0.4, -0.1, None, []),
    ('21-countess', [-1600, 300, L2], P - 0.4, -0.1, None, []),
    ('22-dorm-coffins', [-2048, -900, L2], P / 2, -0.15, None, []),
    ('23-dorm-sleepers', [-2048, -900, L2], P / 2, -0.15, 2.0, SHOW),
    ('24-courtyard', [800, -400, L3], P - 0.6, 0.15, None, []),
    ('25-courtyard-stair', [900, 500, L3], -P / 2 - 0.5, 0.25, None, []),
    ('26-yard-head', [-1000, -800, geo.L1 + E], 0.6, -0.4, None, []),
    ('27-kitchen', [-1600, -100, L3], P / 2 + 0.4, -0.05, None, []),
    ('28-cellar-hatch', [-2200, -500, L3], -0.2, -0.4, None, []),
    ('29-great-hall', [-500, 1400, L3], P - 0.2, -0.05, None, []),
    ('30-great-crest', [-1300, 1792, L3], P, 0.1, None, []),
    ('31-throne', [600, 3264, L3], P, 0.0, None, []),
    ('32-throne-bar', [-700, 2900, L3], P - 0.4, 0.0, None, []),
    ('33-crypt', [-640, 4100, L3], P / 2, -0.2, None, []),
    ('34-crypt-sleepers', [-640, 4100, L3], P / 2, -0.2, 2.0, SHOW),
    ('35-dstair-head', [-1920, 2752, L3], P / 2, -0.4, None, []),
    ('36-dstair-foot', [-2112, 3800, D], -P / 2, 0.1, None, []),
    ('37-undercroft', [-1100, 600, D], 0.9, 0.0, None, []),
    ('38-cells-queen', [-1900, -100, D], 0.0, 0.0, None, []),
    ('39-queen-cell', [-1150, -192, D], 0.0, -0.1, None, []),
    ('40-shaft-ladder', [-2200, -700, D], 0.0, 0.3, None, []),
    ('41-cistern', [1300, 600, D], 0.8, -0.1, None, []),
    ('42-question', [-1600, 1600, D], P - 0.4, -0.05, None, []),
    ('43-back-stair', [-2752, 448, L3], P, 0.2, None, []),
]
FIX = [
    ('01-landing-griffin', [320, -1350, L1], -P / 2, -0.1, 2.5, ['lua evt.SetMonGroupBit(30, MonsterBits.Invisible, 0)']),
    ('02-landing-coffins', [-800, -1300, L1], -P / 2 - 0.3, -0.3, None, []),
    ('03-dorm-coffins', [-1900, -350, L2], P - 0.3, -0.25, 2.5, SHOW),
    ('04-cells-bars', [-1600, 1100, D], -P / 2 - 0.4, -0.05, None, []),
    ('05-cells-bars-2', [-1700, -100, D], P / 2 + 0.4, -0.05, None, []),
    ('06-crypt-coffins', [-640, 4150, L3], P / 2, -0.3, 2.0, SHOW),
    ('07-courtyard-parapet', [-1000, 300, L3], -0.3, 0.55, None, []),
    ('08-landing-parapet', [600, -1180, L1], P / 2, -0.25, None, []),
]
SETS = {'rooms': rooms(), 'things': THINGS, 'fix': FIX}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    keep_shut = n in ('16-chapel-doors',)
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt,
         'commands': ['render hud off'] + ([] if keep_shut else ALL_DOORS) + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
