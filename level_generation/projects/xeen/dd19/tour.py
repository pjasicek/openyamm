#!/usr/bin/env python3
"""DD-19's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners (two-storey
rooms also from their head); 'things': the interactive things and the set pieces; 'fix': the shots of a fix. The
commands open the doors (except where a shot shows a door shut)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd19')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd19'
E = 160


def door(n, a='Open'):
    return f'lua evt.SetDoorState({n}, DoorAction.{a})'


ALL_DOORS = [door(n) for n in range(1, 16) if n != 10]      # not the mirage (10, never opens) nor the ward (16)
HEADS = {'mirage_stair': (geo.UP, (-3008, 1856)), 'hq_stair': (geo.UP, (3008, 1344)), 'alcoves': (geo.G0, (-3904, 2300)),
         'quarters_stair': (geo.G0, (0, 3776)), 'back_stair': (geo.G0, (4288, 1856))}


def rooms():
    out = []
    for rid in sorted(geo.R):
        name, (x0, y0, x1, y1), fl, ce, th = geo.R[rid]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for tag, fx, fy in (('a', 0.12, 0.12), ('b', 0.88, 0.88)):
            px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
            yaw = math.atan2(cy - py, cx - px)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], yaw, -0.05, None, []))
        if rid in HEADS:
            z, (hx, hy) = HEADS[rid]
            yaw = math.atan2(cy - hy, cx - hx)
            out.append((f'{rid}-head', [hx, hy, z + E], yaw, -0.35, None, []))
    return out


U, G, N = geo.UP + E, geo.G0 + E, geo.UN + E
SHOW = ['lua evt.SetMonGroupBit(7, MonsterBits.Invisible, 0)', 'lua evt.SetMonGroupBit(20, MonsterBits.Invisible, 0)']
SHUT = [door(n, 'Close') for n in range(1, 17)]
THINGS = [
    ('01-arrival', [0, 384, G], P / 2, 0.05, None, []),
    ('02-arrival-up', [0, 300, G], P / 2, 0.45, None, []),
    ('03-court-gate', [0, 1200, G], -P / 2, 0.1, None, SHUT),
    ('04-court-west-doors', [600, 768, G], P, 0.15, None, SHUT),
    ('05-court-east-doors', [-600, 768, G], 0.0, 0.15, None, SHUT),
    ('06-court-arcade', [0, 500, G], P / 2, 0.3, None, []),
    ('07-arcade', [-800, 1856, G], 0.0, 0.0, None, SHUT),
    ('08-common-font', [300, 2400, G], P - 0.3, -0.15, None, []),
    ('09-common-blastem', [0, 2500, G], 0.6, -0.05, None, []),
    ('10-common-hearth', [200, 2600, G], P - 0.7, 0.0, None, []),
    ('11-weights', [1250, 2300, G], 0.6, -0.2, None, []),
    ('12-foyer', [-1300, 400, G], P - 0.6, 0.0, None, []),
    ('13-illusions', [-2600, 400, G], P - 0.5, -0.05, None, []),
    ('14-painted-door', [-2752, 900, G], P / 2, 0.0, None, []),
    ('15-mirage-stair', [-2600, 2800, G], P + 0.3, 0.2, None, []),
    ('16-gallery-mirror', [-2600, 896, U], P, 0.0, None, []),
    ('17-gallery-mirage', [-3050, 896, U], 0.0, 0.0, None, []),
    ('18-hall-chair', [-1700, 1700, U], -P / 2 - 0.3, 0.1, None, []),
    ('19-hall-floor', [-1300, 1900, U], -P / 2 - 0.6, -0.45, None, []),
    ('20-hall-bridge-door', [-1600, 1856, U], 0.0, 0.0, None, SHUT),
    ('21-study', [-2200, 0, U], -0.6, -0.15, None, []),
    ('22-bridge', [-900, 1856, U], 0.0, 0.0, None, []),
    ('23-bridge-window', [0, 1760, U], -P / 2, -0.35, None, []),
    ('24-scrying-lamp', [1500, 1100, U], -0.8, -0.25, None, []),
    ('25-scrying-crystal', [1500, 1200, U], 0.9, -0.1, None, []),
    ('26-ward', [3008, 1000, U], P / 2, 0.0, None, SHUT),
    ('27-hq-stair-down', [3008, 1400, U], -P / 2, -0.45, None, []),
    ('28-hq-foyer', [1300, 400, G], 0.7, 0.0, None, []),
    ('29-robing-lamp', [4200, 800, G], 0.7, 0.15, None, []),
    ('30-sanctum', [3328, 1900, U], P / 2, 0.05, None, []),
    ('31-wardrobe', [4500, 1800, U], 0.6, -0.1, None, []),
    ('32-qstair-down', [0, 3700, G], P / 2, -0.4, None, []),
    ('33-undercroft', [0, 3200, N], -P / 2, 0.0, None, []),
    ('34-vault', [0, 300, N], -P / 2, -0.05, None, []),
    ('35-quarters-w', [-1100, 1900, N], P - 0.2, -0.05, None, SHOW),
    ('36-alcoves', [-4000, 1900, N], P - 0.3, -0.05, None, []),
    ('37-alcoves-stair', [-4700, 1900, N], 0.6, 0.35, None, []),
    ('38-quarters-e', [1100, 1900, N], 0.3, -0.05, None, []),
    ('39-alembic', [2600, 1900, N], 0.6, -0.05, None, []),
    ('40-back-stair', [4000, 2800, N], -P / 2 + 0.3, 0.3, None, []),
    ('41-blastem-swap', [300, 2700, G], 0.9, 0.0, 2.0, SHOW),
]
FIX = []
SETS = {'rooms': rooms(), 'things': THINGS, 'fix': FIX}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    keep_shut = any('Close' in c for c in cmds)
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt,
         'commands': ['render hud off'] + ([] if keep_shut else ALL_DOORS) + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
