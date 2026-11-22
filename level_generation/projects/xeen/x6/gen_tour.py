#!/usr/bin/env python3
"""X6's eye-level tour (A5, 2026-11-20; D3's gen_tour.py): writes tour/tour_x6.yml (debug.screenshot_tour_path) from
cells; the eye 200 over the land of land.py. Usage: gen_tour.py [out_dir]"""
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import land as LD   # noqa: E402

HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'tour/shots')
SHOTS = [  # name, eye cell, look-at cell, extra height, pitch, time
    ('arrival_from_x4', (106, 60), (60, 50), 0, 0.02, '10:00'),
    ('sphinx_wells', (67.0, 62.6), (58, 59.5), 0, 0.02, '12:00'),
    ('wells_street', (56.0, 61.6), (66, 60.5), 0, 0.02, '16:00'),
    ('sphinx_from_road', (88, 58), (82, 39), 0, 0.08, '10:00'),
    ('sphinx_door', (82, 50), (82, 42), 0, 0.12, '12:00'),
    ('basenji_from_arie', (48.5, 48.5), (38, 31), 0, 0.22, '15:00'),
    ('arie_camp', (49.0, 46.5), (44.5, 44.5), 0, -0.02, '15:00'),
    ('basenji_gate', (40.0, 37.2), (38, 33), 0, 0.15, '12:00'),
    ('coach_yard', (84.0, 97.4), (89, 94.5), 0, 0.06, '12:00'),
    ('yard_gate_desert', (79.5, 96.5), (83, 96), 0, 0.03, '12:00'),
    ('signature', (38, 96), (31, 81), 0, -0.08, '17:30'),       # D-35: north-north-west, the falls' faces and the Sphinx
    ('cove_falls', (28.5, 95.4), (28.5, 84.0), 150, -0.22, '15:00'),
    ('cove_from_sphinx', (35.2, 88.8), (26.0, 89.0), 100, -0.12, '16:00'),
    ('oasis', (48.5, 64.5), (41, 62), 0, 0.0, '12:00'),
    ('rolling_downs', (94, 63), (106, 80), 0, 0.0, '11:00'),
    ('steppe_south', (50, 104), (60, 88), 0, 0.02, '11:00'),
    ('pan_over', (60, 75), (62, 55), 1200, -0.25, '12:00'),
    ('sphinx_north_side', (91, 37), (82, 38), 0, 0.10, '11:00'),     # s16: lane S's models
    ('sphinx_south_front', (45, 84.5), (38, 84), 0, 0.06, '09:00'),
    ('sphinx_south_door', (41.5, 84.2), (39.4, 84), 0, 0.05, '10:00'),
]


def W(x, y):
    return round((x - 64) * 512), round((64 - y) * 512)


ONLY = [n for n in os.environ.get('TOUR_ONLY', '').split(',') if n]   # e.g. TOUR_ONLY=signature,cove_falls
shots = []
for name, eye, look, up, pitch, t in SHOTS:
    if ONLY and name not in ONLY:
        continue
    x, y = W(*eye)
    z = round(max(LD.raw_height(*eye), 0) + 200 + up)
    yaw = math.atan2(-(look[1] - eye[1]), look[0] - eye[0])
    shots.append({'name': name, 'position': [x, y, z], 'yaw': round(yaw, 4), 'pitch': pitch, 'time': t,
                  'commands': ['render hud off', 'sky weather 0', 'weather clear']})
doc = {'output_dir': OUT, 'exit': True, 'settle_seconds': 2.5, 'shots': shots}
path = os.path.join(HERE, 'tour/tour_x6.yml')
with open(path, 'w') as f:
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print(path, len(shots))
