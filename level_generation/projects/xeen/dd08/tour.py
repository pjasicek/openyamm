#!/usr/bin/env python3
"""DD-08's tours: tour.py rooms|things <name> writes shots/<name>.yml. 'rooms': every room from a corner looking to its
middle (the stair rooms also from their heads); 'things': the interactive things. The commands open the doors (not the
gate) and show the four oath figures."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

import yaml

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd08')
import geo  # noqa: E402

P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd08'
E = 160
DOORS = [f'lua evt.SetDoorState({n}, DoorAction.Open)' for n in range(1, 17) if n not in (5, 6)]
HEADS = {'core': ((0, 1000), geo.L2), 'core2': ((0, 1000), geo.L4), 'wstair': ((-1984, 1100), geo.L3),
         'estair': ((1984, 1100), geo.L3)}
SKIP = {'porch'}
COMMANDS = ['render hud off'] + DOORS + ['lua evt.SetMonGroupBit(40, MonsterBits.Invisible, 0)']


def rooms():
    out = []
    for rid in sorted(geo.R):
        if rid in SKIP:
            continue
        x0, y0, x1, y1 = geo.bbox(rid)
        fl = geo.R[rid][2]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        px, py = x0 + 0.12 * (x1 - x0), y0 + 0.12 * (y1 - y0)
        out.append((f'{rid}-a', [int(px), int(py), fl + E], math.atan2(cy - py, cx - px), -0.05))
        if rid in HEADS:
            (hx, hy), hz = HEADS[rid]
            out.append((f'{rid}-head', [hx, hy, hz + E], -P / 2, -0.35))
    return out


L1, L2, L3, L4 = geo.L1 + E, geo.L2 + E, geo.L3 + E, geo.L4 + E
THINGS = [
    ('01-arrival', [0, -1152, L1], P / 2, 0.0),
    ('02-gate', [0, -1000, L1], -P / 2, 0.05),
    ('03-hall-statue', [300, -500, L1], P, 0.0),
    ('04-hall-south-wall', [0, -350, L1], -P / 2, 0.05),
    ('05-mirror', [-900, 512, L1], P, 0.0),
    ('06-lectern-1', [-1216, 1380, L1 + 60], P / 2, -0.45),
    ('07-dormitory', [900, 1400, L1], 0.6, -0.1),
    ('08-refectory', [1900, -650, L1], 0.9, -0.1),
    ('09-great-stair', [0, -100, L1], P / 2, 0.25),
    ('10-helms-wall', [-1000, 512, L2], P, 0.05),
    ('11-wstair-landing-book', [-1984, 60, L2 + 60], -P / 2, -0.45),
    ('12-north-gallery', [-1400, 1600, L2], 0.0, 0.0),
    ('13-mail-wall', [1000, 512, L2], 0.0, 0.05),
    ('14-quartermaster', [900, -350, L2], -0.4, -0.15),
    ('15-drill-yard', [-1400, -500, L3], -0.2, -0.05),
    ('16-estair-head-book', [1860, 820, L3 + 60], 0.9, -0.4),
    ('17-west-study', [-1600, 1550, L3], P - 0.3, -0.1),
    ('18-silence-stair', [0, -50, L3], P / 2, 0.3),
    ('19-chapter-doors', [-300, 960, L4], P, 0.0),
    ('20-chapter-plaque', [-1700, 400, L4], P / 2, 0.05),
    ('21-chapter-niches', [-1300, 700, L4], P + 0.6, -0.05),
    ('22-vowel-over-doors', [-1700, 960, L4], 0.0, 0.2),
    ('23-mask-iron-door', [0, 1400, L4], P / 2, 0.05),
    ('24-chalice', [0, 2150, L4], P / 2, -0.25),
    ('25-thrones', [900, 1000, L4], -0.5, -0.15),
    ('26-dunce', [1600, -200, L4], -P / 2, -0.15),
    ('27-east-cells', [2560, 0, L4], 0.5, -0.1),
    ('28-loft-trapdoor', [2560, 1350, L4], 0.8, 0.6),
    ('29-west-cells', [-2500, 0, L4], 2.3, -0.1),
]


def write(kind, name):
    shots = rooms() if kind == 'rooms' else THINGS
    doc = {'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.2, 'exit': True,
           'shots': [{'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt} for n, p, y, pt in shots]}
    # console lines are per shot: the first shot opens the doors, shows the figures and hides the HUD
    doc['shots'][0]['commands'] = COMMANDS
    with open(f'{X}/shots/{name}.yml', 'w') as f:
        yaml.safe_dump(doc, f, sort_keys=False, width=200)
    print(len(shots), 'shots')


if __name__ == '__main__':
    write(sys.argv[1], sys.argv[2])
