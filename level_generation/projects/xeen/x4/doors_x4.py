#!/usr/bin/env python3
"""X4's doors and arrivals from the installed build (A5, 2026-11-20): the click things' middles and stand points
(`oymap things`) and the land's height (the ODM's height map, bilinear on its nodes) under every arrival of
DOORS.md. Usage: doors_x4.py [things.json] [map.odm]"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

things = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'output/studio_cal/x4/run/things.json'))
odm = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / 'assets_dev/worlds/xeen/maps/xeen_x4.odm')
h = np.array(parse_odm_file(odm)['payload']['height_map']).reshape(128, 128) * 32.0


def ground(x, y):
    fx, fy = x / 512 + 64, 64 - y / 512
    ix, iy = int(fx), int(fy)
    tx, ty = fx - ix, fy - iy
    a = h[iy, ix] * (1 - tx) + h[iy, ix + 1] * tx
    b = h[iy + 1, ix] * (1 - tx) + h[iy + 1, ix + 1] * tx
    return a * (1 - ty) + b * ty


want = ('castle_burlock', 'xd25_stair', 'xd26_eyrie', 'xd02_adit', 'x3_plate', 'sky_crack_ledge', 'castle_ramp')
for t in things['things']:
    if any(w in t['id'] for w in want) and t['kind'] not in ('name',):
        print('%-40s middle %s stand %s low %s high %s' % (t['id'], t['middle'], t.get('stand'), t['low'], t['high']))
arrivals = {
    'X2 north edge -> X4 south start': (16384, -22016),
    'X3 -> X4 x 36 arrival': (-14336, -22016),
    'XD-07 gate outside': (-1024, 6768),
    'XD-07 throne fall (ground)': (-4608, 9728),
    'XD-25 stair outside': (-11520, -9360),
    'XD-26 mouth outside': (-9216, 11376),
    'XD-26 sky crack ledge (ground)': (-7424, 14592),
    'XD-02 adit outside': (20336, -16128),
    'burlock_square': (-1536, 3584), 'burlock_stables': (1536, 3584), 'asp_travel_pit': (-7168, -10240),
    'asp_square': (-12800, -11776), 'x4_river_landing': (9728, -18944),
}
for k, (x, y) in arrivals.items():
    print('%-34s (%6d, %6d)  ground %5.0f' % (k, x, y, ground(x, y)))
