#!/usr/bin/env python3
"""DD-21's tours: tour.py <set> <name> writes shots/<name>.yml. Set 'rooms': every room from two corners; 'things':
the interactive things. The commands open the doors (unless a shot keeps them) and may show hidden groups."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd21')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd21'
E = 160


def door(n):
    return f'lua evt.SetDoorState({n}, DoorAction.Open)'


ALL_DOORS = [door(n) for n in range(1, 8)]
CORNERS = {'west_culvert': [(-3100, -1900), (-2000, -2800)], 'east_culvert': [(550, -1900), (-300, -2800)]}


def rooms():
    out = []
    for rid in sorted(geo.R):
        name, o, fl, ce, th = geo.R[rid]
        x0, y0, x1, y1 = geo.bounds(rid)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        pts = CORNERS.get(rid) or [(x0 + 0.12 * (x1 - x0), y0 + 0.12 * (y1 - y0)),
                                   (x0 + 0.88 * (x1 - x0), y0 + 0.88 * (y1 - y0))]
        for tag, (px, py) in zip('ab', pts):
            tx, ty = (cx, cy) if rid not in CORNERS else ((-2848, -2848) if tag == 'a' and rid == 'west_culvert' else
                                                          (-2848, -1900) if rid == 'west_culvert' else
                                                          (288, -2848) if tag == 'a' else (288, -1900))
            yaw = math.atan2(ty - py, tx - px)
            out.append((f'{rid}-{tag}', [int(px), int(py), fl + E], yaw, -0.08, None, []))
    return out


C, S, L = geo.CRYPT + E, geo.SEWER + E, geo.LOW + E
SHOW = ['lua evt.SetMonGroupBit(30, MonsterBits.Invisible, 0)', 'lua evt.SetMonGroupBit(20, MonsterBits.Invisible, 0)']
THINGS = [
    ('01-arrival', [0, 0, C], -P / 2, 0.0, None, []),
    ('02-stair-up-wings', [0, 100, C], P / 2, 0.35, None, []),
    ('03-stair-head-wings', [0, 950, geo.STAIR_TOP + E], P / 2, 0.0, None, []),
    ('04-hall-doors-seal', [0, -1100, C], -P / 2, 0.08, None, ['lua evt.SetDoorState(2, DoorAction.Close)', 'lua evt.SetDoorState(3, DoorAction.Close)']),
    ('05-hall-niches', [-300, -300, C], -P / 2 + 0.35, -0.1, None, []),
    ('06-hall-west-stair-head', [100, -1408, C], P, -0.05, None, []),
    ('07-crypt-dais', [0, -2300, C], -P / 2, -0.1, 2.0, SHOW),
    ('08-crypt-grille', [200, -2816, C], 0.0, 0.0, None, ['lua evt.SetDoorState(4, DoorAction.Close)']),
    ('09-reliquary', [950, -2816, C], 0.0, -0.15, None, []),
    ('10-landing-from-head', [-850, -1300, C], P, -0.4, None, []),
    ('11-landing-foot', [-1500, -1700, S], P / 2 + 0.5, 0.25, None, []),
    ('12-main-west', [-1900, -1500, S], P, 0.0, None, []),
    ('13-vault-door', [-3200, -1500, S], P, 0.0, None, ['lua evt.SetDoorState(7, DoorAction.Close)']),
    ('14-mummy-vault', [-3800, -1408, S], P, -0.1, None, []),
    ('15-main-east', [-400, -1500, S], 0.0, 0.0, None, []),
    ('16-cellar-door', [900, -1408, S], 0.0, 0.0, None, ['lua evt.SetDoorState(1, DoorAction.Close)']),
    ('17-cellar-barrels', [1500, -1408, S], 0.0, -0.15, 2.0, SHOW),
    ('18-west-culvert', [-2848, -1900, S], -P / 2, -0.05, None, []),
    ('19-sluice-wheel', [-2240, -2400, S], P / 2, 0.0, None, []),
    ('20-outfall-basin', [-1600, -2560, S], -0.5, -0.25, None, []),
    ('21-outfall-gate', [-704, -2900, S], -P / 2, 0.0, None, ['lua evt.SetDoorState(5, DoorAction.Close)']),
    ('22-heart-steps', [-704, -3700, S], -P / 2, -0.3, None, []),
    ('23-heart-jar', [-800, -4300, L], -P / 2 - 0.2, -0.15, None, []),
    ('24-heart-cistern', [-1000, -3900, L], P + 0.9, -0.25, None, []),
    ('27-statuettes', [1000, -2900, C], 0.4, -0.1, None, ['lua evt.SetDoorState(4, DoorAction.Open)']),
    ('25-east-culvert-box', [288, -2300, S], P + 0.3, -0.1, None, []),
    ('26-drain', [-2224, -1450, S], -P / 2, -0.25, None, []),
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
