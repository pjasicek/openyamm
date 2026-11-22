#!/usr/bin/env python3
"""Scratch check only: an overlay copy of D5's scene (work/ingame/mount/worlds/xeen/maps/xeen_d5.scene.yml) in which
A6's rock24 stand-ins for the Enchanted Boulders (both rings) become xeen_boulder (decoration_list_id 4013 = row
4014), each facing outward from its ring's centre (the map facing in degrees: 0 east, 90 north). Never written to
assets_dev. Also writes work/ingame/tour.yml (screenshot tour, noon, clear sky).
Usage: ingame_scene.py"""
import math
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
PROJECT = Path(__file__).resolve().parents[1]
src = REPO / 'assets_dev/worlds/xeen/maps/xeen_d5.scene.yml'
dst = PROJECT / 'work/ingame/mount/worlds/xeen/maps/xeen_d5.scene.yml'
WEST_C = ((37.2 - 64) * 512, (64 - 70.6) * 512)
EAST_C = ((85.6 - 64) * 512, (64 - 81.2) * 512)
RINGS = {1061: WEST_C, 1062: WEST_C, 1063: WEST_C, 1057: EAST_C, 1058: EAST_C, 1059: EAST_C, 1060: EAST_C}
lines = src.read_text().splitlines(keepends=True)
out, cur, pos = [], None, {}
for line in lines:
    if line.startswith('  - entity_index:'):
        cur = int(line.split(':')[1])
    if cur in RINGS:
        if line.startswith('    name: '):
            line = '    name: xeen_boulder\n'
        elif line.startswith('    decoration_list_id: '):
            line = '    decoration_list_id: 4013\n'
        elif line.startswith('      x: '):
            pos[cur] = [float(line.split(':')[1])]
        elif line.startswith('      y: '):
            pos[cur].append(float(line.split(':')[1]))
        elif line.startswith('      z: '):
            pos[cur].append(float(line.split(':')[1]))
        elif line.startswith('    facing: '):
            (x, y, _), (cx, cy) = pos[cur], RINGS[cur]
            facing = round(math.degrees(math.atan2(y - cy, x - cx))) % 360
            pos[cur].append(facing)
            line = '    facing: %d\n' % facing
    out.append(line)
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(''.join(out))
print('WROTE', dst)
for k, v in sorted(pos.items()):
    print('BOULDER entity', k, 'at', v[:3], 'facing', v[3])

# tour: boulder 1 (entity 1061, west ring, facing south) head-on from 300, 1,000 and 3,000; the west ring; boulder 7;
# the east ring
b1x, b1y, b1z, _ = pos[1061]
GROUND = {300: 1504, 1000: 1566, 3000: 1754}


def shot(name, x, y, z, look_x, look_y, pitch=0.0, time='12:00'):
    return {'name': name, 'position': [round(x, 1), round(y, 1), z], 'yaw': round(math.atan2(look_y - y, look_x - x), 4),
            'pitch': pitch, 'commands': ['render hud off', 'sky weather 0', 'weather clear'], 'time': time}


shots = [shot('b1_300', b1x, b1y - 300, 1504, b1x, b1y, 0.02),
         shot('b1_1000', b1x, b1y - 1000, 1566, b1x, b1y, -0.03),
         shot('b1_3000', b1x, b1y - 3000, 1754, b1x, b1y, -0.07),
         shot('b1_q_450', b1x + 320, b1y - 320, 1504, b1x, b1y, 0.03)]
b7x, b7y, b7z, f7 = pos[1063]
shots.append(shot('b7_400', b7x + 400 * math.cos(math.radians(f7)), b7y + 400 * math.sin(math.radians(f7)), 1504,
                  b7x, b7y, 0.0))
shots.append(shot('west_ring_700', WEST_C[0] + 500, WEST_C[1] - 500, 1504, WEST_C[0], WEST_C[1], -0.08))
shots.append(shot('b1_side_400', b1x + 400, b1y - 120, 1504, b1x, b1y, 0.0))
ex, ey = EAST_C
shots.append(shot('east_ring_900', ex, ey - 900, 1376, ex, ey, -0.08))
shots.append(shot('b1_1000_evening', b1x, b1y - 1000, 1566, b1x, b1y, -0.03, '18:00'))
tour = {'output_dir': str(PROJECT / 'review' / 'ingame'), 'settle_seconds': 2.5, 'exit': True, 'shots': shots}
(PROJECT / 'work/ingame/tour.yml').write_text(yaml.safe_dump(tour, sort_keys=False, width=200))
print('TOUR', len(shots), 'shots')
