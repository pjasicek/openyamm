#!/usr/bin/env python3
"""A6: a screenshot tour of X5 from the build's heights. tour.py <build> <out_dir> <tour.yml> [set]"""
import json, math, sys, yaml
B, OUTD, TY = sys.argv[1], sys.argv[2], sys.argv[3]
which = sys.argv[4] if len(sys.argv) > 4 else 'a'
hm = json.load(open(B + '/export.json'))['map']['terrain']['height_map']
def g(x, y):
    i, j = int(round(x)), int(round(y))
    return hm[max(0, min(127, j)) * 128 + max(0, min(127, i))] * 32
def W(x, y):
    return ((x - 64) * 512, (64 - y) * 512)
SETS = {
 'a': [  # name, at (cells), eye height over ground, look at (cells), look height, pitch override
  ('square', (37, 41.5), 180, (37, 36), None),
  ('square_s', (37, 37.8), 180, (36, 46), None),
  ('town_from_e', (47, 40), 260, (36, 41), None),
  ('mere_from_obelisk', (58, 43), 200, (55, 61), None),
  ('arrival_view', (106, 59), 180, (84, 54), None),
  ('glacier_view', (48, 101), 200, (30, 104), None),
  ('gongs', (37, 42.5), 180, (37, 39), None),
  ('monastery_foot', (73, 41.5), 180, (69, 31), None),
  ('monastery_court', (69, 35), 180, (68, 29), None),
  ('pass_crest', (82, 47), 180, (70, 40), None),
  ('pocket_halon', (99, 55), 200, (95, 48), None),
  ('golem_door', (100.5, 69), 180, (100.5, 73), None),
  ('cave_north', (96, 47), 180, (96, 43), None),
  ('troll_forest', (60, 82), 180, (70, 92), None),
  ('xd10_south', (74, 82), 180, (79, 82), None),
  ('spur_from_e', (92, 82), 200, (82, 82), None),
  ('giants', (40, 84), 200, (44, 94), None),
  ('edge_watch', (28, 41.5), 180, (18, 41.5), None),
  ('darkstone_close', (55, 66), 180, (55, 61), None),
  ('high_overview', (64, 100), 6000, (60, 50), None),
  ('high_town', (37, 55), 3000, (37, 41), None),
 ],
 's15': [  # session 15, D-56: P5's fall point on Darkstone's widened rock, the terrace, the rock from the ice
  ('p5_fall_south', (55, 59), 180, (55, 61), None),
  ('rock_from_north', (55, 53), 200, (55, 60), None),
  ('rock_from_west', (47, 60), 200, (55, 60), None),
  ('mere_from_obelisk', (58, 43), 200, (55, 61), None),
 ],
 'fit': [  # session 8: the texture-fit rule (one-off motifs once per face; matching backgrounds)
  ('fit_square_n', (37, 44), 180, (37, 38), None),
  ('fit_square_w', (40, 41.5), 180, (32, 41.5), None),
  ('fit_town_e', (44, 40), 200, (38, 40), None),
  ('fit_monastery', (70, 37), 180, (69, 30), None),
  ('fit_monastery_tower', (75, 44), 200, (70, 40), None),
  ('fit_halon_tower', (97, 52), 200, (95, 48), None),
  ('fit_pagoda', (64.5, 42), 180, (64.5, 46.5), None),
  ('fit_darkstone', (55, 65), 220, (55, 61), None),
  ('fit_warren', (65.5, 91.5), 180, (65.5, 95), None),
 ],
 'x6edge': [  # session 9: the north edge open to X6 (the steppe road's end looking north, the arrival looking south)
  ('road_end_north', (50, 24), 180, (50, 12), None),
  ('arrival_south', (50, 20), 180, (50, 32), None),
 ],
 'glacier': [  # D-6.5 (session 6): the icefall from the north, the lookout's view down the tongue
  ('glacier_view', (43.5, 99.7), 200, (31, 102), None),
  ('glacier_from_glom', (42, 77), 180, (32.5, 82.5), None),
  ('glacier_from_shrine', (50.5, 75.2), 180, (32.5, 82.5), None),
  ('glacier_from_south_track', (40, 72), 180, (32.5, 82.5), None),
  ('glacier_from_south_track_far', (36, 62), 180, (32.5, 82.5), None),
  ('icefall_snout', (37, 75.5), 180, (32, 81), None),
  ('glacier_lip_side', (46, 103), 200, (30, 103.5), None),
  ('lookout_from_waters', (47, 100.5), 200, (43.5, 99.7), None),
 ]}
shots = []
for name, at, eye, look, _ in SETS[which]:
    X, Y = W(*at); LX, LY = W(*look)
    z = g(*at) + eye
    lz = g(*look) + 150
    dist = math.hypot(LX - X, LY - Y)
    yaw = math.atan2(LY - Y, LX - X)
    pitch = math.atan2(lz - z, dist)
    shots.append({'name': name, 'position': [round(X), round(Y), round(z)], 'yaw': round(yaw, 4),
                  'pitch': round(pitch, 4)})
shots[0]['commands'] = ['render hud off']        # a tour's commands go on its first shot (tools/RUN_GAME.md)
yaml.safe_dump({'output_dir': OUTD, 'settle_seconds': 2.0, 'exit': True, 'shots': shots}, open(TY, 'w'),
               sort_keys=False)
print(len(shots), 'shots')
