#!/usr/bin/env python3
"""Second pass: the reviewer's views of Vertigo (eye, centre, above, high, wall) plus the user's walk points, as a
game screenshot tour. Cameras in cells, fixed, so before and after are the same views.
gen_review.py <build folder (export.json)> <output dir> <tour.yml>"""
import json, math, os, sys

B, OUT, TOUR = sys.argv[1], sys.argv[2], sys.argv[3]
hm = json.load(open(os.path.join(B, 'export.json')))['map']['terrain']['height_map']

def g(x, y):
    return hm[int(min(127, max(0, round(y)))) * 128 + int(min(127, max(0, round(x))))] * 32

C = (52, 45)          # Vertigo's middle
R = 4500 / 512.0      # 'above' cameras: 4,500 out, 1,800 up
SHOTS = [
    # eye: standing back from doors along the streets
    ('eye0', (45.5, 44.6), (44.5, 41.0), 170),
    ('eye1', (49.5, 43.8), (49.5, 47.5), 170),
    ('eye2', (57.5, 43.6), (58.5, 40.0), 170),
    ('eye3', (59.5, 44.8), (60.5, 48.0), 170),
    ('eye4', (46.0, 54.6), (45.0, 57.5), 170),
    # centre: the square and the streets from it
    ('centre0', (54.0, 47.5), (52.0, 39.0), 170),
    ('centre1', (54.0, 46.0), (43.0, 44.0), 170),
    ('centre2', (54.0, 46.0), (62.0, 46.0), 170),
    # above: 1,800 up, 4,500 out, looking at the middle
    ('above0', (C[0], C[1] + R), C, 1800),
    ('above1', (C[0] - R, C[1]), C, 1800),
    ('above2', (C[0], C[1] - R), C, 1800),
    ('above3', (C[0] + R, C[1]), C, 1800),
    ('high_town', (52, 66), (52, 44), 1500),
    ('wall_outside_n', (52, 33.5), (52, 40), 170),
    ('west_gate_out', (36, 44.5), (44, 44), 170),
    ('square_eye', (55.0, 48.6), (51.0, 42.0), 300),
    # the user's walk points
    ('road_under_house', (55.0, 54.6), (60.0, 55.6), 170),
    ('rip_north_road', (54.0, 37.0), (54.8, 34.4), 300),
    ('rip_hill_fork', (60.0, 35.5), (61.2, 32.8), 300),
    ('waterfall_lip', (99, 57.5), (104.5, 60), 300),
    ('waterfall_below', (113, 66), (104, 60), 600),
    ('dead_forest', (47.5, 74.5), (42, 81), 200),
    ('farm_belt', (60, 64.5), (45, 61), 500),
    ('farm_west', (41, 51.5), (32, 47), 500),
    ('orc_camp', (51, 29), (56, 24), 900),
    ('rip_close', (53.6, 35.2), (54.6, 33.6), 260),
]

os.makedirs(OUT, exist_ok=True)
lines = ['output_dir: "%s"' % os.path.abspath(OUT), 'exit: true', 'settle_seconds: 2.5', 'shots:']
for name, cam, look, h in SHOTS:
    X, Y = (cam[0] - 64) * 512, (64 - cam[1]) * 512
    z = max(g(*cam), 0) + h
    dx, dy = (look[0] - cam[0]) * 512, (cam[1] - look[1]) * 512
    yaw = math.atan2(dy, dx)
    lz = g(*look) + 150
    pitch = math.atan2(lz - z, math.hypot(dx, dy))
    lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, commands: ["render hud off"]}'
                 % (name, X, Y, z, yaw, pitch))
open(TOUR, 'w').write('\n'.join(lines) + '\n')
print(len(SHOTS))
