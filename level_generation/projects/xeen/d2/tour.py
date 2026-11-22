#!/usr/bin/env python3
"""A6: a screenshot tour of D2 from the build's heights. tour.py <build> <out_dir> <tour.yml> [set]"""
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
 'l3': [  # D-23: an eye-level picture of the village and the great tree at L3
  ('village_from_lane', (36, 75), 180, (28, 89), None),
  ('great_tree_from_glade', (42, 69), 180, (42, 79), 1800),
  ('village_green', (31.5, 90.5), 180, (25.5, 84), None),
  ('great_tree_far', (32, 61), 180, (42, 79), 2600),
 ],
 'a': [
  ('arrival_west', (21, 60), 180, (40, 70), None),
  ('village_from_lane', (36, 75), 180, (28, 89), None),
  ('village_green', (31.5, 90.5), 180, (25.5, 84), None),
  ('village_green_e', (27, 90), 180, (34.5, 86), None),
  ('sharla_stair', (21.5, 82), 180, (25.5, 84), None),
  ('great_tree_door', (42, 74), 180, (42, 79), 600),
  ('great_tree_from_glade', (42, 69), 180, (42, 79), 1800),
  ('great_tree_far', (32, 61), 180, (42, 79), 2600),
  ('nibbler', (43.5, 75.5), 180, (45.5, 75.5), None),
  ('pass_view', (60, 44), 180, (84, 37), None),
  ('west_fort', (69, 40), 180, (72, 34), None),
  ('parley_fire', (77, 38.5), 180, (79.5, 36.5), None),
  ('east_fort', (90, 40), 180, (87, 45), None),
  ('arrival_east', (106, 44), 180, (84, 38), None),
  ('troll_holes', (58, 72), 180, (61, 76), None),
  ('troll_hole_c', (66, 98), 180, (69, 98), None),
  ('fruit_hut', (57.5, 86.5), 180, (58, 90), None),
  ('glimmerbrook', (46, 70), 180, (50, 80), None),
  ('brink_falls', (62.5, 103.2), 180, (57.5, 105), -500),
  ('rim_west', (40.5, 101.5), 200, (52, 106), -500),
  ('southern_tower', (92, 74), 180, (95, 81), 800),
  ('shrine', (104, 91), 180, (104, 94), None),
  ('adit', (34, 34), 180, (34, 30), None),
  ('obelisk', (38, 54), 180, (36, 51), None),
  ('high_overview', (64, 100), 6000, (60, 50), None),
  ('high_village', (40, 100), 2500, (30, 88), None),
 ],
 'fix': [  # A6's review: the hut, Sharla's open stair, the village and the darker forest
  ('fruit_hut', (58.6, 87.6), 180, (55.9, 89.2), None),
  ('fruit_counter', (57.2, 91.6), 180, (55.9, 90.0), 60),
  ('sharla_stair', (25.5, 79.6), 180, (25.0, 83.0), 500),
  ('sharla_stair_w', (21.3, 84.6), 180, (24.0, 83.0), 400),
  ('sharla_deck', (23.86, 84.45), 860, (28, 89), -500),
  ('village_from_lane', (36, 75), 180, (28, 89), None),
  ('great_tree_from_glade', (42, 69), 180, (42, 79), 1800),
  ('great_tree_west', (37, 80), 180, (42, 79), 1200),
  ('forest_west', (33, 70), 180, (22, 76), None),
  ('troll_holes', (59.0, 74.4), 180, (61, 76), None),
  ('troll_holes_out', (62.6, 77.6), 180, (66, 82), None),
  ('troll_hole_b', (69.0, 82.5), 180, (71, 84), None),
  ('glimmerbrook', (46, 70), 180, (50, 80), None),
 ],
 'crown': [  # S's crown on the great tree, Sharla's stair head, the DD-06 door, the east road into D3
  ('crown_from_glade', (44.5, 71.5), 180, (42, 79), 3300),
  ('crown_from_village', (30, 88.5), 180, (42, 79), 3600),
  ('crown_far', (32, 61), 180, (42, 79), 3800),
  ('crown_junction_n', (42, 76.6), 3000, (42, 79), 3060),
  ('crown_junction_e', (44.4, 79.6), 3150, (42, 79), 3000),
  ('crown_under', (40.2, 77.4), 3000, (42, 79), 3400),
  ('great_tree_eye', (40.5, 74.0), 160, (42, 79), 1500),
  ('great_tree_door', (42, 74), 180, (42, 79), 600),
  ('sharla_head_out', (21.8, 83.2), 900, (24.0, 84.5), 700),
  ('sharla_head_deck', (24.7, 84.0), 860, (23.4, 84.8), 640),
  ('sharla_stair', (25.5, 79.6), 180, (25.0, 83.0), 500),
  ('dd06_door', (95, 77.4), 180, (95, 81), 250),
  ('east_road_end', (117, 44), 180, (127.5, 44), 150),
  ('arrival_east', (106, 44), 180, (84, 38), None),
 ],
 'fit': [  # texture fit and the dungeon doors: the tower, the obelisk, the trunk doors, the holes, the east road
  ('dd06_door', (95, 77.4), 180, (95, 81), 250),
  ('southern_tower', (92, 74), 180, (95, 81), 800),
  ('obelisk', (38, 54), 180, (36, 51), 300),
  ('village_green_e', (27, 90), 180, (34.5, 86), None),
  ('trunk_door_close', (28.6, 86.6), 140, (27.0, 85.3), 160),
  ('great_tree_door', (42, 74), 180, (42, 79), 600),
  ('crown_junction_n', (42, 76.6), 3000, (42, 79), 3060),
  ('troll_holes', (59.0, 74.4), 180, (61, 76), None),
  ('east_road_end', (117, 44), 180, (127.5, 44), 150),
  ('arrival_east', (106, 44), 180, (84, 38), None),
  ('west_fort', (69, 40), 180, (72, 34), None),
  ('sharla_head_out', (21.8, 83.2), 900, (24.0, 84.5), 700),
 ],
 'gates': [  # DD-13's two fort gates, DD-10B's adit, the lanterns beside the trunk doors
  ('west_gate', (72, 38.6), 180, (72, 36.1), 250),
  ('east_gate', (87, 39.6), 180, (87, 42.1), 250),
  ('adit', (34, 33.2), 180, (34, 30.2), 250),
  ('lanterns_potions', (24.6, 91.6), 160, (23.0, 89.5), 200),
  ('lanterns_guild', (33.0, 86.0), 160, (34.5, 83.5), 200),
  ('great_tree_door', (42, 74), 180, (42, 79), 600),
 ]}
shots = []
for name, at, eye, look, lift in SETS[which]:
    X, Y = W(*at); LX, LY = W(*look)
    z = g(*at) + eye
    lz = g(*look) + (150 if lift is None else lift)
    dist = math.hypot(LX - X, LY - Y)
    yaw = math.atan2(LY - Y, LX - X)
    pitch = math.atan2(lz - z, dist)
    shots.append({'name': name, 'position': [round(X), round(Y), round(z)], 'yaw': round(yaw, 4),
                  'pitch': round(pitch, 4)})
shots[0]['commands'] = ['render hud off']        # a tour's commands go on its first shot (tools/RUN_GAME.md)
yaml.safe_dump({'output_dir': OUTD, 'settle_seconds': 2.0, 'exit': True, 'shots': shots}, open(TY, 'w'),
               sort_keys=False)
print(len(shots), 'shots')
