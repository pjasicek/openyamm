#!/usr/bin/env python3
"""DD-15's tours: tour.py rooms|things <name> writes shots/<name>.yml. 'rooms': every room from a corner looking to its
middle (the stairs also from their heads); 'things': the interactive things. The commands open the doors and show the
niche mummies (the tour's console cannot run the torch events)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd15')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd15'
E = 160
DOORS = [f'lua evt.SetDoorState({n}, DoorAction.Open)' for n in range(2, 31) if n not in (11, 12, 14)]
HEADS = {'stair_foot': ((-1024, -3500), geo.L2), 'registry_stair': ((-2400, 1472), geo.L3),
         'apex_stair': ((2624, -1600), geo.L4)}
SKIP = {'porch'}


def rooms():
    out = []
    for rid in sorted(geo.R):
        if rid in SKIP:
            continue
        x0, y0, x1, y1 = geo.bbox(rid)
        fl = geo.R[rid][2]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if rid == 'sky_corridor':
            out.append((f'{rid}-a', [1300, 2432, fl + E], P, -0.05))
            out.append((f'{rid}-b', [0, 2300, fl + E], P / 2, 0.0))
            continue
        px, py = x0 + 0.12 * (x1 - x0), y0 + 0.12 * (y1 - y0)
        out.append((f'{rid}-a', [int(px), int(py), fl + E], math.atan2(cy - py, cx - px), -0.05))
        if rid in HEADS:
            (hx, hy), hz = HEADS[rid]
            out.append((f'{rid}-head', [hx, hy, hz + E], math.atan2(cy - hy, cx - hx), -0.35))
    return out


L1, L2, L3, L4 = geo.L1 + E, geo.L2 + E, geo.L3 + E, geo.L4 + E
THINGS = [
    ('01-arrival', [0, 4736, L1], -P / 2, 0.0),
    ('02-green-doors', [0, 4300, L1], P / 2, 0.05),
    ('03-welcome-statue', [-500, 4096, L1], P, 0.0),
    ('04-atrium', [0, 2700, L1], -P / 2, -0.05),
    ('05-chapel-ne-lever-plaque', [3840, 4300, L1], P / 2, 0.05),
    ('06-chapel-ne-niches', [3600, 4300, L1], 0.0, 0.0),
    ('07-chapel-se-niches-lever', [2816, -2900, L1], -P / 2, 0.0),
    ('08-stair-door', [-1024, -2700, L1], -P / 2, 0.05),
    ('09-number-niches', [2700, -800, L1], 0.0, 0.0),
    ('10-overseer-desk-vault', [4224, -2650, L1], -P / 2, -0.2),
    ('11-grand-stair', [-1024, -4600, L1], P / 2 + 0.4, 0.25),
    ('12-lift-foot', [-700, -3584, L1], 0.0, 0.0),
    ('13-processional', [-896, -1900, L2], P / 2, 0.0),
    ('14-verse-statue', [-900, -1280, L2], P, -0.1),
    ('15-registry-door-plaque', [-1100, 3200, L2], P, 0.05),
    ('16-west-tomb', [-2000, -400, L2], P, -0.1),
    ('17-east-tomb', [0, 0, L2], 0.4, -0.1),
    ('18-pad-hall', [-960, 1000, L3], -P / 2 + 0.3, -0.35),
    ('19-pads-close', [192, 0, L3], -P / 2, -0.6),
    ('20-cell-sun', [-2688, -512, L3], -P / 2 + 0.6, -0.2),
    ('21-cell-eye-map', [2600, -700, L3], P / 2, 0.05),
    ('22-cell-scarab-rack', [2500, 640, L3], 0.0, -0.1),
    ('23-cell-bird-pads', [128, -1800, L3], -P / 2, -0.4),
    ('24-far-cell-door', [1300, -2000, L3], -0.3, -0.1),
    ('25-antechamber', [-400, -2800, L4], 0.5, 0.0),
    ('26-lift-top', [256, -2700, L4], -P / 2, 0.0),
    ('27-great-doors', [448, -1300, L4], P / 2, 0.05),
    ('28-throne-pharaoh', [-384, 400, L4], P / 2, 0.05),
    ('29-throne-vat', [700, 900, L4], P / 2 + 0.3, -0.2),
    ('30-bedchamber', [1900, 1400, L4], 0.8, 0.0),
    ('31-bed-tapestry', [2300, 1700, L4], P / 2, 0.15),
    ('32-sky-door', [0, 2400, L4], P / 2, 0.05),
]


def write(kind, name):
    shots = rooms() if kind == 'rooms' else THINGS
    doc = {'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.2, 'exit': True,
           'commands': ['render hud off'] + DOORS + ['lua for g = 21, 24 do evt.SetMonGroupBit(g, MonsterBits.Invisible, 0) end'],
           'shots': [{'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt} for n, p, y, pt in shots]}
    with open(f'{X}/shots/{name}.yml', 'w') as f:
        yaml.safe_dump(doc, f, sort_keys=False, width=200)
    print(len(shots), 'shots')


if __name__ == '__main__':
    write(sys.argv[1], sys.argv[2])
