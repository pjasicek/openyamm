#!/usr/bin/env python3
"""DD-17's picture tour: tour.py <name> writes shots/<name>.yml (every room and the set pieces, doors, slabs and the
gate opened by the tour's commands). Positions in the generator's frame, enlarged as the written map (gen.sc)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402
import geo  # noqa: E402

P = math.pi
X = Path(_REPO_ROOT + '/output/studio_cal/dd17')
E = 160
sc = gen.sc
L1, L2, L3 = geo.L1 + E, geo.L2 + E, geo.L3 + E
OPEN = [f'lua evt.SetDoorState({n}, DoorAction.Open)' for n in range(2, 39) if n not in (6, 7, 8, 9, 10, 11)]


def at(x, y, z):
    return [sc(x), sc(y), z]


SHOTS = [
    ('01-gatehall', at(0, -3800, L1), P / 2, 0.0),
    ('02-hall-order', at(-1300, -3100, L1), 0.35, 0.0),
    ('03-hall-statue', at(-900, -3050, L1), P / 2 + 0.6, 0.05),
    ('04-west-ward', at(-3500, -2944, L1), 0.0, 0.0),
    ('05-fire-belt', at(-1920, -2300, L1), P / 2, -0.15),
    ('06-fire-head', at(-2304, 1950, L1), P / 2, 0.05),
    ('07-west-return', at(-2624, -2300, L1), P / 2, 0.0),
    ('08-water-head', at(-3392, 200, L1), P / 2, 0.05),
    ('09-sump', at(-400, -2300, L1), P - 0.3, 0.0),
    ('10-stair-hall', at(-60, -2420, L1), 0.3, 0.2),
    ('11-south-walk', at(1700, -2944, L2), P, 0.0),
    ('12-sw-bay-field', at(-1600, -2176, L2), P, 0.0),
    ('13-water-dial', at(-2560, -2176, L2), P, -0.5),
    ('14-west-walk', at(-1800, -1150, L2), P / 2, 0.0),
    ('15-dial-hall-lip', at(-1100, -150, L2), 0.0, -0.25),
    ('16-dial-hall-chasms', at(-1100, 1700, L2), -0.6, -0.45),
    ('17-island-gate', at(700, -200, L2), 0.2, 0.0),
    ('18-island-statue', at(750, 150, L2), -0.9, -0.1),
    ('19-lift-core', at(1350, 0, L2), 0.0, -0.1),
    ('20-deck', at(1050, 0, L3), P, -0.35),
    ('21-deck-traps', at(-1000, 1500, L3), -0.7, -0.5),
    ('22-robot-bay', at(150, 2100, L3), 0.4, 0.0),
    ('23-screen-room', at(-300, 2100, L3), P / 2 + 0.6, 0.0),
    ('24-west-hall', at(-1500, -900, L3), P / 2 + 0.4, 0.0),
    ('25-hatch-room', at(-1500, 1450, L3), P - 0.3, 0.35),
    ('26-juice', at(-2700, 0, L3), P, -0.1),
    ('27-antechamber', at(-1450, -1400, L3), -P / 2 - 0.5, 0.0),
    ('28-strongroom', at(-2700, -1792, L3), P, -0.1),
    ('29-command', at(-1500, -3072, L3), P, 0.0),
    ('30-throne', at(-2350, -3072, L3), P, 0.05),
    ('31-watch', at(2800, -3550, L1), 0.0, 0.0),
    ('32-north-walk-statue', at(352, 2150, L2), P / 2, 0.05),
]


def write(name):
    out = X / 'shots' / name
    out.mkdir(parents=True, exist_ok=True)
    doc = {'output_dir': str(out), 'settle_seconds': 1.5, 'exit': True,
           'commands': ['lua AddValue(InventoryItem(12364), 12364)', 'render hud off'] + OPEN,
           'shots': [{'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt} for n, p, y, pt in SHOTS]}
    path = X / 'shots' / f'{name}.yml'
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    print(path)


if __name__ == '__main__':
    write(sys.argv[1] if len(sys.argv) > 1 else 'look1')
