#!/usr/bin/env python3
"""X4's review tour (A5, 2026-11-20): every shot's feet on the installed land (+ a lift for overviews), HUD off, noon,
clear weather. Usage: gen_tour.py <name>  -> output/studio_cal/x4/tour/tour_<name>.yml, shots in tour/<name>/"""
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

name = sys.argv[1] if len(sys.argv) > 1 else 'a'
h = np.array(parse_odm_file(ROOT / 'assets_dev/worlds/xeen/maps/xeen_x4.odm')['payload']['height_map']).reshape(
    128, 128) * 32.0


def ground(cx, cy):
    ix, iy = int(cx), int(cy)
    tx, ty = cx - ix, cy - iy
    a = h[iy, ix] * (1 - tx) + h[iy, ix + 1] * tx
    b = h[iy + 1, ix] * (1 - tx) + h[iy + 1, ix + 1] * tx
    return a * (1 - ty) + b * ty


D = {'e': 0.0, 'ne': math.pi / 4, 'n': math.pi / 2, 'nw': 3 * math.pi / 4, 'w': math.pi, 'sw': -3 * math.pi / 4,
     's': -math.pi / 2, 'se': -math.pi / 4}
SHOTS = [  # name, cell, facing (word or radians), lift over the land, pitch
    ('signature_lists_to_castle', (69, 74), 'n', 0, 0.06),
    ('arrival_x2_road', (96, 106), 2.2, 0, 0.0),
    ('arrival_x3_asp_road', (36, 106.3), 'n', 0, 0.0),
    ('burlock_overview', (62, 64.5), 'n', 1400, -0.38),
    ('burlock_square_to_gate', (62, 57.8), 'n', 0, 0.16),
    ('burlock_square_west', (64.6, 56.4), 'w', 0, 0.0),
    ('burlock_square_east', (59.4, 56.2), 'e', 0, 0.0),
    ('burlock_south_gate_outside', (62.5, 64.5), 'n', 0, 0.04),
    ('burlock_stables_yard', (63.6, 56.0), 'e', 0, 0.0),
    ('castle_gate_close', (62, 51.6), 'n', 330, 0.10),
    ('castle_from_west', (51.5, 47), 'e', 0, 0.12),
    ('lists_overview', (73, 75), 'nw', 800, -0.3),
    ('falls_and_fountain', (73.5, 51.5), 'ne', 0, 0.12),
    ('asp_overview', (41, 93.5), 'n', 1300, -0.45),
    ('asp_pedestals', (44.0, 85.5), 'w', 0, -0.12),
    ('asp_undercroft_stair', (41.5, 83.6), 'n', 0, -0.15),
    ('asp_square_east', (38.6, 86.0), 'e', 0, 0.0),
    ('asp_stair_from_behind', (41.5, 79.6), 's', 0, -0.12),
    ('asp_travel_pit', (52.5, 84.5), 'w', 0, 0.0),
    ('eyrie_mouth', (46, 43.6), 'n', 0, 0.12),
    ('eyrie_ledge_view', (49.5, 35.8), 's', 60, -0.18),
    ('xd02_adit', (101.6, 95.5), 'e', 0, 0.05),
    ('barbarian_camp', (27.5, 59), 'nw', 0, 0.0),
    ('druid_ring', (26, 74), 'n', 0, 0.0),
    ('renegade_camp', (59, 98.5), 'sw', 0, 0.0),
    ('kings_bridge', (80.5, 79.5), 'n', 0, 0.05),
    ('nystor_landing', (85.5, 101.5), 'w', 0, 0.0),
    ('shrine_of_fire', (104, 48.5), 'n', 0, 0.05),
    ('edge_south', (75, 105), 's', 0, 0.0),
    ('edge_west', (22, 60), 'w', 0, 0.0),
    ('edge_east', (106, 66.5), 'e', 0, 0.0),
    ('edge_north_rim', (64, 28.5), 'n', 0, -0.1),
]
out = ROOT / 'output/studio_cal/x4/tour' / name
lines = ['output_dir: "%s"' % out, 'exit: true', 'settle_seconds: 2.5', 'shots:']
for sid, (cx, cy), facing, lift, pitch in SHOTS:
    yaw = D[facing] if isinstance(facing, str) else facing
    x, y = round((cx - 64) * 512), round((64 - cy) * 512)
    z = round(ground(cx, cy) + lift)
    lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.2f, time: "12:00", commands: '
                 '["render hud off", "sky weather 0", "weather clear"]}' % (sid, x, y, z, yaw, pitch))
p = ROOT / 'output/studio_cal/x4/tour' / ('tour_%s.yml' % name)
p.write_text('\n'.join(lines) + '\n')
print(p, len(SHOTS))
