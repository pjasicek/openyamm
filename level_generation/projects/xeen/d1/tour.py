#!/usr/bin/env python3
"""A6: a screenshot tour of D1 from the build's heights (X5's tour.py). tour.py <build> <out_dir> <tour.yml> [set]"""
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
 'a': [  # name, at (cells), eye height over ground, look at (cells)
  ('arrival_pyramid', (61.6, 38.4), 180, (69, 46)),
  ('north_gate_out', (63, 41.5), 180, (63, 44)),
  ('gate_yard_w', (66, 41.5), 180, (56, 41)),
  ('north_gate_in', (63, 47), 180, (63, 43)),
  ('gate_street', (63, 46), 180, (63, 56)),
  ('square_n', (63, 52), 180, (63, 57)),
  ('square_s', (63, 56.3), 180, (63, 50)),
  ('square_w', (66.5, 54), 180, (57, 53)),
  ('guild_row', (52, 57.8), 180, (66, 58)),
  ('back_lane', (56, 60.8), 180, (66, 62)),
  ('yard_lane', (71.5, 49), 180, (71.5, 57)),
  ('ellinger', (68.5, 47.5), 180, (71.2, 45.9)),
  ('jetty_stair', (52.5, 59.5), 180, (50.5, 54.5)),
  ('jetty_top', (51.2, 54.6), 820, (45, 54.9)),
  ('queens_gate_out', (50.0, 65.5), 180, (52.25, 62.5)),
  ('queens_gate_in', (54, 60.5), 180, (52.25, 62.5)),
  ('walls_from_east', (79, 52), 220, (70, 52)),
  ('gorge_bridge', (77.4, 41.0), 200, (82, 44)),
  ('outfall', (80.5, 50.5), 200, (79, 47.8)),
  ('mill', (76.8, 47.5), 180, (79, 46)),
  ('kalindra_ramp', (49, 66), 200, (42, 70)),
  ('kalindra_gate', (46.4, 70), 180, (43, 70)),
  ('dark_grove', (40, 33), 180, (47, 35)),
  ('great_tree', (49.5, 37), 180, (47, 35)),
  ('western_tower', (34, 40), 200, (31, 33)),
  ('tower_rope', (32.5, 29.5), 180, (31, 31.6)),
  ('gemsmiths', (37, 28), 180, (37, 24)),
  ('river_south', (60, 85), 200, (45, 82)),
  ('signature', (53.6, 91.6), 200, (46, 62)),
  ('falls_rim', (36, 101), 200, (30, 104)),
  ('sardaj_camp', (88, 31), 200, (88, 24)),
  ('east_arrival', (106, 60), 180, (80, 58)),
  ('ellinger_from_square', (64, 56.5), 180, (71.2, 45.9)),
  ('kalindra_from_bank', (44, 86), 220, (39, 70)),
  ('street_grate_gate', (63, 47.5), 160, (63, 45.5)),
 ],
 'fix': [  # A6 fixes (2026-11-20): the gate lanes, the gemsmiths' workshops, the Dark Grove and its great tree
  ('queens_gate_out', (50.0, 65.5), 180, (52.25, 62.5)),
  ('queens_gate_in', (54, 60.5), 180, (52.25, 62.5)),
  ('queens_gate_in_far', (55.4, 61.0), 180, (52.25, 62.5)),
  ('north_gate_in', (63, 47), 180, (63, 43)),
  ('north_gate_out', (63, 41.5), 180, (63, 44)),
  ('gemsmiths', (37, 28), 180, (37, 24)),
  ('gemsmith_shed', (40.4, 26.6), 180, (39.1, 24.3)),
  ('gemsmiths_east', (43.5, 25.5), 180, (35, 24.5)),
  ('weapons_shed', (64.0, 48.2), 180, (65.7, 46.6)),
  ('dark_grove', (40, 33), 180, (47, 35)),
  ('grove_edge', (36, 41), 200, (46.2, 34), 1800),
  ('great_tree', (48.9, 36.9), 180, (46.2, 34), 1200),
  ('rope_foot', (48.4, 36.6), 180, (47.5, 35.45), 400),
  ('great_tree_up', (48.6, 36.2), 180, (46.2, 34), 3000),
  ('grove_from_tower', (34, 40), 200, (46.2, 34), 1500),
  ('signature', (53.6, 91.6), 200, (46, 62)),
 ],
 'd30': [  # A6 (2026-11-20): S's crown on the great tree, the gates (D-30), Castle Kalindra at stages 0, 1, 2 and 4
  ('tree_wide', (34, 46), 600, (46.2, 34), 4600),
  ('tree_from_rope', (49.4, 37.6), 180, (46.2, 34), 2600),
  ('junction_ne', (48.27, 36.07), 3000, (46.2, 34), 3190),
  ('junction_sw', (44.13, 31.93), 3050, (46.2, 34), 3190),
  ('rope_up', (48.3, 36.3), 160, (47.51, 35.45), 3600),
  ('north_gate_out', (63, 41.5), 180, (63, 44)),
  ('north_gate_in', (63, 47), 180, (63, 43)),
  ('queens_gate_out', (50.0, 65.5), 180, (52.25, 62.5)),
  ('queens_gate_in', (54, 60.5), 180, (52.25, 62.5)),
 ] + [shot for stage, bit in ((0, None), (1, 111381), (2, 111382), (4, 111522)) for shot in (
  ('kal%d_bank' % stage, (44, 86), 220, (39, 70), 600,
   (['qbit set %d' % bit] if bit else []) + ['event %d' % e for e in (256, 257, 258, 259)]),
  ('kal%d_ne' % stage, (49.5, 60.5), 450, (39, 70), 700),
  ('kal%d_forecourt' % stage, (48.5, 71.5), 220, (39, 68), 900))],
 'tex': [  # A6 (2026-11-20): texture fit (slits, arms, portcullis leaves, windows), the stable gate, DD-10A's adit
  ('north_gate_out', (63, 41.5), 180, (63, 44)),
  ('north_gate_close', (63, 42.3), 200, (63, 44), 380),
  ('north_gate_tower', (60.2, 41.8), 220, (62.0, 43.6), 620),
  ('north_gate_in', (63, 47), 180, (63, 43)),
  ('queens_gate_out', (50.0, 65.5), 180, (52.25, 62.5)),
  ('queens_gate_in', (54, 60.5), 180, (52.25, 62.5)),
  ('adit', (45, 25.5), 200, (45, 22.2), 250),
  ('kal0_forecourt', (48.5, 71.5), 220, (39, 68), 900, ['event 256', 'event 257', 'event 258', 'event 259']),
  ('kal0_gate', (45.8, 70), 200, (43.2, 70), 450),
  ('kal0_north', (39.75, 61.2), 300, (39.75, 66), 700),
  ('kal4_forecourt', (48.5, 71.5), 220, (39, 68), 900,
   ['qbit set 111522', 'event 256', 'event 257', 'event 258', 'event 259']),
  ('kal4_gate', (45.8, 70), 200, (43.2, 70), 450),
  ('kal4_north', (39.75, 61.2), 300, (39.75, 66), 700),
  ('kal4_ne', (49.5, 60.5), 450, (39, 70), 700),
  ('kal4_stable_door', (39.75, 62.6), 160, (39.75, 64.3), 140),
  ('tavern_sign', (62.9, 46.5), 160, (61.2, 46.5), 330),
 ],
 's9': [  # A6 (2026-11-20, ninth session): the stable yard's double gate (stage 4), the gatehouses
  ('north_gate_out', (63, 41.5), 180, (63, 44)),
  ('north_gate_close', (63, 42.3), 200, (63, 44), 380),
  ('north_gate_in', (63, 47), 180, (63, 43)),
  ('queens_gate_out', (50.0, 65.5), 180, (52.25, 62.5)),
  ('queens_gate_in', (54, 60.5), 180, (52.25, 62.5)),
  ('kal0_gate', (45.8, 70), 200, (43.2, 70), 450, ['event 256', 'event 257', 'event 258', 'event 259']),
  ('kal0_north', (39.75, 61.2), 300, (39.75, 66), 700),
  ('kal4_gate', (45.8, 70), 200, (43.2, 70), 450,
   ['qbit set 111522', 'event 256', 'event 257', 'event 258', 'event 259']),
  ('kal4_north', (39.75, 61.2), 300, (39.75, 66), 700),
  ('kal4_stable_wide', (39.75, 61.8), 200, (39.75, 64.3), 300),
  ('kal4_stable_door', (39.75, 62.6), 160, (39.75, 64.3), 140),
  ('kal4_stable_side', (38.6, 62.8), 160, (39.75, 64.3), 140),
 ]}
shots = []
for item in SETS[which]:
    name, at, eye, look = item[:4]
    lookz = item[4] if len(item) > 4 else 150
    X, Y = W(*at); LX, LY = W(*look)
    z = g(*at) + eye
    lz = g(*look) + lookz
    dist = math.hypot(LX - X, LY - Y)
    yaw = math.atan2(LY - Y, LX - X)
    pitch = math.atan2(lz - z, dist)
    shots.append({'name': name, 'position': [round(X), round(Y), round(z)], 'yaw': round(yaw, 4),
                  'pitch': round(pitch, 4)})
    if len(item) > 5:
        shots[-1]['commands'] = list(item[5])
shots[0]['commands'] = ['render hud off'] + shots[0].get('commands', [])
yaml.safe_dump({'output_dir': OUTD, 'settle_seconds': 2.0, 'exit': True, 'shots': shots}, open(TY, 'w'),
               sort_keys=False)
print(len(shots), 'shots')
