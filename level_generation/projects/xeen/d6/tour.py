#!/usr/bin/env python3
"""A6: a screenshot tour of D6 from the build's heights. tour.py <build> <out_dir> <tour.yml> [set]"""
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
 'a': [  # (name, at, eye over the land, look at, look-at lift, time)
  ('arrival_griffin_pass', (64, 97), 200, (56, 52), 600, '10:00'),
  ('signature_day', (82, 72), 400, (51, 46), 1400, '12:00'),
  ('signature_dusk', (82, 72), 400, (51, 46), 1400, '19:30'),
  ('signature_night', (82, 72), 400, (51, 46), 1400, '23:30'),
  ('alamar_gate', (51, 58.5), 200, (51, 52), 600, '11:00'),
  ('pylons_pyramid', (54, 66), 250, (54, 59), 300, '11:00'),
  ('alamar_high', (51, 70), 2500, (51, 46), 800, '11:00'),
  ('corak_pod', (77, 72.5), 200, (72.5, 67.5), 500, '11:00'),
  ('hatch_close', (74.8, 70.4), 160, (73.4, 68.4), 150, '11:00'),
  ('necropolis_gate', (91, 69.5), 180, (91, 74), 300, '11:00'),
  ('necropolis_square', (91, 76.6), 180, (90, 82), None, '11:00'),
  ('books_mirror', (90.5, 80.5), 180, (90.5, 78), None, '11:00'),
  ('ambrose_camp', (63.5, 97.5), 180, (60.5, 94.5), None, '11:00'),
  ('archers_camp', (38, 88), 200, (34, 85.5), None, '11:00'),
  ('adit', (46, 93.5), 200, (46, 97.5), 200, '11:00'),
  ('sheltem_pod', (78, 43), 200, (78, 38), 500, '11:00'),
  ('north_falls', (50, 28), 400, (44, 24), -400, '11:00'),
  ('high_overview', (64, 110), 6000, (64, 60), None, '11:00'),
 ],
 'sig': [
  ('arrival_griffin_pass', (64, 97), 200, (56, 52), 600, '10:00'),
  ('signature_day', (82, 72), 400, (51, 46), 1400, '12:00'),
  ('signature_dusk', (82, 72), 400, (51, 46), 1400, '19:30'),
  ('signature_night', (82, 72), 400, (51, 46), 1400, '23:30'),
 ],
 'adit': [  # session 14: the adit mouth centred in its frame, the crag behind it
  ('adit', (46, 93.5), 200, (46, 97.5), 200, '11:00'),
  ('adit_ne', (49, 93), 200, (46, 97.5), 200, '11:00'),
  ('adit_far', (46, 90), 300, (46, 98), 300, '11:00'),
 ],
 'd55': [  # A6 session 15: D-55's glow-only drawing with Surface materials off (merge point 24)
  ('arrival_day', (64, 97), 200, (56, 52), 600, '10:00'),
  ('arrival_night', (64, 97), 200, (56, 52), 600, '23:30'),
  ('signature_day', (82, 72), 400, (51, 46), 1400, '12:00'),
  ('signature_dusk', (82, 72), 400, (51, 46), 1400, '19:30'),
  ('signature_night', (82, 72), 400, (51, 46), 1400, '23:30'),
  ('alamar_gate_day', (51, 58.5), 200, (51, 52), 600, '12:00'),
  ('alamar_gate_night', (51, 58.5), 200, (51, 52), 600, '23:30'),
  ('pylons_night', (54, 66), 250, (54, 59), 300, '23:30'),
 ],
 'night': [  # A6 session 14: Alamar by night with the xaenergy/xafield glow maps (video.surface_materials on)
  ('signature_dusk', (82, 72), 400, (51, 46), 1400, '19:30'),
  ('signature_night', (82, 72), 400, (51, 46), 1400, '23:30'),
  ('arrival_night', (64, 97), 200, (56, 52), 600, '23:30'),
  ('alamar_gate_night', (51, 58.5), 200, (51, 52), 600, '23:30'),
  ('pylons_night', (54, 66), 250, (54, 59), 300, '23:30'),
  ('alamar_high_night', (51, 70), 2500, (51, 46), 800, '23:30'),
  ('signature_day', (82, 72), 400, (51, 46), 1400, '12:00'),
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
