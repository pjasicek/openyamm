#!/usr/bin/env python3
"""A6: a screenshot tour of D4 from the build's heights. tour.py <build> <out_dir> <tour.yml> [set]"""
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
 'a': [  # D4's first look: (name, at, eye over the land, look at, look-at lift, time)
  ('arrival_d3', (88, 104), 180, (82, 70), 0, '10:00'),
  ('signature_day', (72, 79.8), 300, (87, 47.5), 2600, '12:00'),
  ('signature_dusk', (72, 79.8), 300, (87, 47.5), 2600, '19:30'),
  ('signature_night', (72, 79.8), 300, (87, 47.5), 2600, '23:30'),
  ('square', (73, 92.5), 180, (68, 89), None, '11:00'),
  ('guild_door', (70.5, 89.2), 180, (67.5, 89), 250, '11:00'),
  ('waterfront', (62, 82.8), 180, (74, 83.4), None, '11:00'),
  ('jetty_foot', (72, 85.8), 180, (72, 80), None, '11:00'),
  ('gatehouse', (73.5, 54), 180, (77.4, 53), 350, '11:00'),
  ('crag_from_shore', (68, 54), 180, (87, 47.5), 2400, '11:00'),
  ('isle_landing', (72.4, 76.8), 220, (72, 68), 500, '11:00'),
  ('isle_tower_door', (72, 71.2), 180, (72, 68), 300, '11:00'),
  ('leafpoint_grove', (42, 64.8), 180, (42, 61), 300, '11:00'),
  ('ector_cabin', (36.5, 74), 180, (34, 72), None, '11:00'),
  ('octopods_west', (55.5, 62), 400, (61, 63), -100, '11:00'),
  ('octopods_east', (90, 78.5), 400, (86, 70), -100, '11:00'),
  ('crag_top', (80.5, 47.5), 900, (87, 47.5), 900, '11:00'),
  ('castle_high', (70, 62), 2600, (87, 47.5), 1200, '11:00'),
  ('witches_circle', (46.5, 92.5), 180, (50, 90), None, '11:00'),
  ('wizard_camp', (31, 54), 200, (28, 50), None, '11:00'),
  ('lair', (46.5, 46.5), 200, (46, 41), 250, '11:00'),
  ('falls', (98.5, 65.5), 250, (104, 67), -300, '11:00'),
  ('mirabeth', (92.5, 79), 180, (95, 76), None, '11:00'),
  ('high_overview', (72, 108), 6000, (72, 60), None, '11:00'),
  ('octopod_close_w', (63.6, 60.2), -1300, (60.0, 64.0), -1150, '11:00'),
  ('octopod_close_e', (89.2, 67.6), -1300, (86.0, 65.5), -1150, '11:00'),
  ('stalls_square', (77.4, 89.0), 180, (70, 89), None, '11:00'),
 ],
 'b': [
  ('arrival_brow', (88, 102), 180, (80, 70), 0, '10:00'),
  ('signature_day', (72, 79.8), 300, (87, 47.5), 2600, '12:00'),
  ('signature_dusk', (72, 79.8), 300, (87, 47.5), 2600, '19:30'),
  ('signature_night', (72, 79.8), 300, (87, 47.5), 2600, '23:30'),
  ('gatehouse', (73.5, 54), 180, (77.4, 53), 350, '11:00'),
  ('crag_top', (80.5, 47.5), 900, (87, 47.5), 900, '11:00'),
  ('crag_top_night', (80.5, 47.5), 900, (87, 47.5), 900, '23:30'),
  ('wizard_camp', (31, 54), 200, (28, 50), None, '11:00'),
  ('high_overview', (72, 100), 3000, (72, 60), None, '11:00'),
 ],
 'sig': [
  ('arrival_brow', (88, 102), 180, (80, 70), 0, '10:00'),
  ('signature_day', (72, 79.8), 300, (87, 47.5), 2600, '12:00'),
  ('signature_dusk', (72, 79.8), 300, (87, 47.5), 2600, '19:30'),
  ('signature_night', (72, 79.8), 300, (87, 47.5), 2600, '23:30'),
  ('high_overview', (72, 100), 3000, (72, 60), None, '11:00'),
 ],
 'haze': [
  ('square', (73, 92.5), 180, (68, 89), None, '11:00'),
  ('guild_door', (71.5, 89.2), 180, (67.5, 89), 250, '11:00'),
  ('crag_from_shore', (68, 54), 180, (87, 47.5), 2400, '11:00'),
  ('high_overview', (72, 100), 3000, (72, 60), None, '11:00'),
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
