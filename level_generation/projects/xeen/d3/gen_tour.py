#!/usr/bin/env python3
"""D3's eye-level tour (A5, 2026-11-20): writes tour/tour_d3.yml (debug.screenshot_tour_path) from cells; the eye
200 over the land of land.py. Usage: gen_tour.py [out_dir]"""
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import land as LD   # noqa: E402

HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'tour/shots')
SHOTS = [  # name, eye cell, look-at cell, extra height, pitch, time
    ('arrival_from_d2', (21, 44), (42, 31), 0, 0.02, '10:00'),
    ('square_north', (36.5, 32.6), (36, 21), 0, 0.10, '12:00'),
    ('quarter_stair', (42.5, 31.0), (43.5, 22), 0, 0.14, '12:00'),
    ('guild_row_east', (31.0, 24.4), (44, 24.4), 0, 0.06, '12:00'),
    ('sky_stair', (31.5, 24.3), (28.5, 21.5), 0, 0.32, '16:00'),
    ('sky_stair_deck', (33.0, 24.5), (28.5, 20.0), 1800, -0.32, '16:00'),
    ('yard_to_gate', (39.5, 43.2), (36.5, 39.0), 0, 0.10, '12:00'),
    ('south_gate', (36.5, 41.8), (36.5, 39.0), 0, 0.12, '12:00'),
    ('east_gate', (49.6, 31.5), (47.0, 31.5), 0, 0.10, '12:00'),
    ('guild_gate', (43.5, 23.2), (43.5, 20.2), 0, 0.12, '12:00'),
    ('crossroads', (60.0, 50.0), (60.0, 41.0), 0, 0.02, '12:00'),
    ('signature', (107.5, 72), (99, 55), 1100, -0.06, '18:00'),
    # D-50: the rim glow's own named view (the signature stays north-north-west): the east rim at night, the rim's
    # grass in the lower-left foreground, the falls' lip at the right edge (trials tour/s14_rimtry*_sheet.jpg)
    ('rim_glow', (102.0, 59.0), (120, 55), 50, 0.0, '23:00'),
    ('south_bank', (86, 66), (100, 57), 500, -0.08, '18:00'),
    ('eastern_tower', (88.0, 45.6), (97, 46), 0, 0.12, '12:00'),
    ('gorge_head', (85.0, 25.0), (80.5, 21.5), 0, -0.25, '12:00'),
    ('gorge_south', (79.5, 41.0), (80.5, 22.0), 500, -0.16, '12:00'),
    ('wrath_crest', (86.5, 36.0), (96, 28), 0, 0.12, '12:00'),
    ('crest_from_meadows', (84, 45), (96, 28), 300, 0.04, '12:00'),
    ('crest_from_saddle', (88.0, 21.0), (97, 28), 350, 0.06, '12:00'),
    ('oak_lane', (48.6, 60.4), (53, 65), 0, 0.10, '12:00'),
    ('howling_ridge', (36.0, 79.0), (24, 80), 0, 0.10, '12:00'),
    ('venom_pond', (77.0, 70.5), (72, 81), 0, -0.05, '12:00'),
    ('valley_over', (22.0, 50.0), (40, 34), 900, -0.12, '12:00'),
    ('city_from_road', (24.0, 50.0), (37, 28), 0, 0.06, '12:00'),
    ('city_from_dunes', (56.0, 27.0), (37, 25), 0, 0.05, '12:00'),
    ('town_over', (37.0, 50.0), (37, 29), 1400, -0.30, '12:00'),
]
# tenth session (texture fit, D-41, D-42): the adobe grades' houses, the guilds, the Eastern Tower, the gates, the
# stables' sign, the ruin and the guild precinct north of the wall; D3_TOUR=fit picks these
FIT = [
    ('poor_row', (42.0, 33.6), (42.5, 36.5), 0, 0.10, '12:00'),
    ('poor_tall', (28.8, 35.2), (28.3, 32.8), 0, 0.16, '12:00'),
    ('rich_flat2', (40.6, 30.6), (41.2, 33.2), 0, 0.12, '12:00'),
    ('rich_north', (37.6, 24.6), (39.0, 22.0), 0, 0.14, '12:00'),
    ('guild_front', (34.6, 24.3), (31.2, 22.2), 0, 0.12, '12:00'),
    ('quarter_court', (43.6, 22.8), (41.4, 21.4), 0, 0.12, '12:00'),
    ('eastern_tower', (88.0, 45.6), (97, 46), 0, 0.12, '12:00'),
    ('tower_close', (93.2, 47.8), (97, 46), 0, 0.30, '12:00'),
    ('south_gate', (36.5, 41.8), (36.5, 39.0), 0, 0.12, '12:00'),
    ('east_gate', (49.6, 31.5), (47.0, 31.5), 0, 0.10, '12:00'),
    ('stables_sign', (39.2, 41.6), (40.8, 41.2), 0, 0.05, '12:00'),
    ('vespar_ruin', (43.0, 48.8), (45.6, 47.6), 0, 0.05, '12:00'),
    ('precinct_from_quarter', (43.5, 23.6), (43.5, 17.0), 0, 0.16, '12:00'),
    ('precinct_from_square', (37.0, 30.0), (43.5, 17.5), 0, 0.10, '12:00'),
    ('precinct_over', (50.5, 23.5), (43.5, 17.5), 900, -0.22, '12:00'),
    ('precinct_north', (43.5, 10.5), (43.5, 18.0), 300, -0.04, '12:00'),
    ('dd19_return', (43.5, 20.74), (43.5, 24.0), 0, 0.0, '12:00'),
]
if os.environ.get('D3_TOUR') == 'fit':
    SHOTS = FIT


def W(x, y):
    return round((x - 64) * 512), round((64 - y) * 512)


shots = []
for name, eye, look, up, pitch, t in SHOTS:
    x, y = W(*eye)
    z = round(max(LD.raw_height(*eye), 0) + 200 + up)
    yaw = math.atan2(-(look[1] - eye[1]), look[0] - eye[0])
    shots.append({'name': name, 'position': [x, y, z], 'yaw': round(yaw, 4), 'pitch': pitch, 'time': t,
                  'commands': ['render hud off', 'sky weather 0', 'weather clear']})
doc = {'output_dir': OUT, 'exit': True, 'settle_seconds': 2.5, 'shots': shots}
path = os.path.join(HERE, 'tour/tour_d3.yml')
with open(path, 'w') as f:
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print(path, len(shots))
