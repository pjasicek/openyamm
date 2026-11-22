#!/usr/bin/env python3
"""X7's eye-level tour (A5, 2026-11-20; X6's gen_tour.py): writes tour/tour_x7.yml (debug.screenshot_tour_path) from
cells; the eye 200 over the land of land.py. Usage: gen_tour.py [out_dir]   (TOUR_ONLY=a,b picks shots)"""
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import land as LD   # noqa: E402

HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'tour/shots')
SHOTS = [  # name, eye cell, look-at cell, extra height, pitch, time
    ('arrival_from_x1', (69, 106), (66, 60), 0, 0.06, '10:00'),     # D-40 change 7: bare peaks, the Gap's saddle
    ('road_to_gap', (65.6, 92.0), (63, 64), 0, 0.07, '10:00'),     # D-40 change 7: the saddle from the X1 road
    ('gap_saddle', (62.6, 77.6), (62, 64), 0, 0.08, '10:00'),       # the saddle from the X1 road above the watch
    ('watch', (63.0, 89.0), (68, 81), 0, 0.04, '11:00'),
    ('sablewing', (70.5, 92.5), (77, 90), 0, 0.0, '15:00'),
    ('gap_north', (62.6, 67.4), (66, 42), 160, -0.04, '12:00'),          # D-40 question 7: the whole north from the Gap
    ('arrival_from_x4', (22, 66), (60, 66), 0, 0.03, '10:00'),
    ('signature', (67, 25), (75.5, 32), 0, -0.22, '17:30'),          # D-40 question 7: the cove seen across
    ('cove_falls', (66.4, 27.0), (73.5, 28.6), 250, -0.3, '15:00'),
    ('volcano_mouth', (60.5, 45.0), (66, 45), 0, 0.02, '12:00'),
    ('cleft', (69.0, 49.6), (74, 48), 0, 0.04, '12:00'),
    ('dragon_cave', (56, 36), (56, 29), 0, 0.06, '12:00'),
    ('lava_island', (40.5, 56.8), (35, 44), 150, -0.08, '12:00'),
    ('dragon_tower', (22, 44), (29, 29.5), 0, 0.1, '15:00'),
    ('black_bridge', (57.5, 47.5), (61, 43), 0, 0.0, '12:00'),
    ('outpost', (36, 90), (31, 86), 0, 0.0, '12:00'),
    ('back_gate', (82, 101.5), (88, 100), 0, 0.02, '12:00'),
    ('fire_corner', (97, 33), (101.2, 26.6), 0, 0.02, '12:00'),
    ('firestone_over', (60, 60), (88, 40), 1400, -0.1, '12:00'),
]


def W(x, y):
    return round((x - 64) * 512), round((64 - y) * 512)


ONLY = [n for n in os.environ.get('TOUR_ONLY', '').split(',') if n]
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
path = os.path.join(HERE, 'tour/tour_x7.yml')
with open(path, 'w') as f:
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print(path, len(shots))
