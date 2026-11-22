#!/usr/bin/env python3
"""Scratch check only: the in-game tour of both sphinxes on X6 (debug.screenshot_tour_path). Eye 200 over the land of
A5's land.py (imported read-only from output/studio_cal/x6/tools, as A5's gen_tour.py does).
Usage: ingame_tour.py <out_dir>  (writes work/ingame/tour.yml)"""
import math
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
sys.dont_write_bytecode = True     # never write into A5's folder
sys.path.insert(0, str(REPO / 'output/studio_cal/x6/tools'))
import land as LD  # noqa: E402

OUT = Path(sys.argv[1]).resolve()
SHOTS = [  # name, eye cell, look-at cell, extra height, pitch
    ('n_head3000', (82, 49.9), (82, 40), 0, 0.10),
    ('n_head8000', (82, 59.6), (82, 40), 0, 0.04),
    ('n_road', (88, 58), (82, 39), 0, 0.08),
    ('n_q', (75.5, 49), (82, 40), 0, 0.08),
    ('n_side', (94, 37), (82, 37), 0, 0.08),
    ('n_door', (82, 45.7), (82, 43), 0, 0.22),
    ('n_back', (87, 27), (82, 36), 0, 0.08),
    ('s_signature', (38, 96), (31, 81), 0, -0.08),
    ('s_crest', (38, 96), (38.5, 84), 0, -0.06),
    ('s_head', (45.5, 84), (38, 84), 0, 0.06),
    ('s_q', (44, 89), (38.5, 84), 0, 0.06),
    ('s_door', (41.3, 84), (39.4, 84), 0, 0.15),
    ('s_side', (37.5, 90.5), (37.5, 84), 0, 0.06),
    # the clean copies: north at cell (72, 82) facing south, south at (66, 92) facing east
    ('cn_head3000', (72, 87.9), (72, 78), 0, 0.10),
    ('cn_head8000', (72, 97.6), (72, 78), 0, 0.04),
    ('cn_q', (65.5, 87), (72, 78), 0, 0.08),
    ('cn_side', (82, 75), (72, 75), 0, 0.08),
    ('cn_door', (72, 83.6), (72, 81), 0, 0.22),
    ('cs_head', (72, 92), (65, 92), 0, 0.06),
    ('cs_q', (71, 96.5), (65, 92), 0, 0.06),
    ('cs_side', (63.5, 99), (63.5, 92), 0, 0.06),
]


def W(x, y):
    return [round((x - 64) * 512), round((64 - y) * 512)]


shots = []
for name, eye, look, up, pitch in SHOTS:
    x, y = W(*eye)
    z = round(max(LD.raw_height(*eye), 0) + 200 + up)
    yaw = math.atan2(-(look[1] - eye[1]), look[0] - eye[0])
    shots.append({'name': name, 'position': [x, y, z], 'yaw': round(yaw, 4), 'pitch': pitch, 'time': '11:00',
                  'commands': ['render hud off', 'sky weather 0', 'weather clear']})
doc = {'output_dir': str(OUT), 'exit': True, 'settle_seconds': 2.5, 'shots': shots}
path = Path(__file__).resolve().parents[1] / 'work/ingame/tour.yml'
path.write_text(yaml.safe_dump(doc, sort_keys=False, width=120))
print(path, len(shots))
