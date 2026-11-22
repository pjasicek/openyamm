#!/usr/bin/env python3
"""A6: a screenshot tour of D5 from the build's heights. tour.py <build> <out_dir> <tour.yml> [set]"""
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
 'a': [  # D5: (name, at, eye over the land, look at, look-at lift, time)
  ('arrival_d4', (105, 80), 180, (64, 86), 2600, '11:00'),
  ('signature', (82, 98), 180, (64, 86), 2400, '12:00'),
  ('signature_dusk', (82, 98), 180, (64, 86), 2400, '18:30'),
  ('pyramid_door', (64, 75.5), 180, (64, 79.4), 250, '11:00'),
  ('pyramid_near', (52, 74), 300, (64, 86), 1600, '11:00'),
  ('hold_doors', (86, 50.5), 200, (86, 42.4), 300, '11:00'),
  ('boulders_east', (88.5, 83.5), 180, (85.6, 81.2), 60, '11:00'),
  ('boulders_west', (39.8, 72.8), 180, (37.2, 70.6), 60, '11:00'),
  ('barrier', (73, 44), 250, (73, 34.5), 700, '11:00'),
  ('barrier_end', (50, 33), 400, (46, 25), 600, '11:00'),
  ('grate', (101, 98.5), 180, (101, 102), 200, '11:00'),
  ('quivering_forest', (36, 48), 200, (35, 40), 150, '11:00'),
  ('tower', (69, 45.5), 180, (69, 39), 500, '11:00'),
  ('bosco', (65.5, 46.3), 180, (61, 46.25), 200, '11:00'),
  ('broken_pyramid', (98.5, 76.5), 180, (95, 72.5), 150, '11:00'),
  ('last_water', (44, 83.5), 180, (45, 78.5), 50, '11:00'),
  ('arrival_d6', (23, 64), 180, (64, 86), 2600, '11:00'),
  ('high_overview', (64, 116), 6000, (64, 60), None, '11:00'),
 ],
 'night': [  # A6 session 14: the Barrier by night with the xaenergy/xafield glow maps (video.surface_materials on)
  ('barrier_night', (73, 44), 250, (73, 34.5), 700, '23:30'),
  ('barrier_end_night', (50, 33), 400, (46, 25), 600, '23:30'),
  ('barrier_far_night', (73, 60), 400, (73, 34.5), 900, '23:30'),
  ('barrier_day', (73, 44), 250, (73, 34.5), 700, '11:00'),
 ],
 'curtain': [  # A6 session 15: the translucent curtain (xafield's graded alpha, merge point 23) from both sides
  ('curtain_south', (73, 44), 250, (73, 34.5), 700, '11:00'),
  ('curtain_near', (70, 38.5), 120, (73, 32), 400, '11:00'),
  ('curtain_north', (73, 28), 250, (73, 40), 300, '11:00'),
  ('curtain_end', (50, 33), 400, (46, 25), 600, '11:00'),
  ('curtain_far', (73, 60), 400, (73, 34.5), 900, '11:00'),
  ('curtain_dusk', (73, 44), 250, (73, 34.5), 700, '19:30'),
  ('curtain_night', (73, 44), 250, (73, 34.5), 700, '23:30'),
  ('curtain_night_far', (73, 60), 400, (73, 34.5), 900, '23:30'),
 ],
}
shots = []
for item in SETS[which]:
    name, at, eye, look, lift, t = item[:6]
    extra = item[6] if len(item) > 6 else []
    X, Y = W(*at); LX, LY = W(*look)
    z = -eye if eye < 0 else g(*at) + eye
    lz = -lift if (lift is not None and lift < -1000) else g(*look) + (150 if lift is None else lift)
    dist = math.hypot(LX - X, LY - Y)
    yaw = math.atan2(LY - Y, LX - X)
    pitch = math.atan2(lz - z, dist)
    shot = {'name': name, 'position': [round(X), round(Y), round(z)], 'yaw': round(yaw, 4),
            'pitch': round(pitch, 4), 'commands': ['render hud off', 'sky weather 0', 'weather clear'] + extra}
    if t:
        shot['time'] = t
    shots.append(shot)
yaml.safe_dump({'output_dir': OUTD, 'settle_seconds': 2.0, 'exit': True, 'shots': shots}, open(TY, 'w'),
               sort_keys=False)
print(len(shots), 'shots')
