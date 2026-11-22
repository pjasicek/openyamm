#!/usr/bin/env python3
"""A6 (2026-11-20, texture fit): a town tour from build.json's doors (porches, open sheds, the towers) plus tour.py's
s9 shots (gatehouses, Kalindra at stages 0 and 4). tour_town.py <build> <out_dir> <tour.yml>"""
import json, math, subprocess, sys, yaml, os
B, OUTD, TY = sys.argv[1:4]
here = os.path.dirname(os.path.realpath(__file__))
subprocess.run([sys.executable, os.path.join(here, 'tour.py'), B, OUTD, TY, 's9'], check=True, stdout=subprocess.DEVNULL)
s9 = yaml.safe_load(open(TY))['shots']
doors = {b['id']: (b['door'], b['normal']) for b in json.load(open(B + '/build.json'))['buildings'] if b.get('door')}
# name, building, distance out from the door, sideways (right of the door seen from outside), eye over the door's sill
PICKS = [('porch_alchemist', 'building:cv_alchemist', 700, 250, 200), ('porch_house1', 'building:cv_houses#1', 650, -250, 200),
         ('porch_house3', 'building:cv_houses#3', 650, 300, 200), ('porch_house10_close', 'building:cv_houses#10', 380, 120, 170),
         ('shed_weapons', 'building:cv_weapons', 800, 500, 260), ('jetty_armour', 'building:cv_armour', 750, -400, 230),
         ('shed_gemsmith1', 'building:gemsmith#1', 900, 700, 260), ('tavern_porch', 'building:cv_tavern', 700, 300, 200),
         ('western_tower', 'thing:western_tower', 2600, 0, 500),
         ('western_tower_top', 'thing:western_tower', 1500, 600, 1800)]
shots = []
for name, bid, out, side, eye in PICKS:
    (dx, dy, dz), (nx, ny) = doors[bid]
    rx, ry = -ny, nx
    X, Y = dx + nx * out + rx * side, dy + ny * out + ry * side
    Z = dz + eye
    lz = dz + (eye if 'top' in name else 120)
    tz = dz + 2300 if 'top' in name else lz
    yaw = math.atan2(dy - Y, dx - X)
    pitch = math.atan2(tz - Z, math.hypot(dx - X, dy - Y))
    shots.append({'name': name, 'position': [round(X), round(Y), round(Z)], 'yaw': round(yaw, 4),
                  'pitch': round(pitch, 4)})
# Ellinger's five storeys over the roofs from the square (tour.py's set a)
X, Y, LX, LY = 0, 3840, 3686, 9267
shots.append({'name': 'ellinger_from_square', 'position': [X, Y, 1330], 'yaw': round(math.atan2(LY - Y, LX - X), 4),
              'pitch': round(math.atan2(1300, math.hypot(LX - X, LY - Y)), 4)})
# D-42: the Western Tower's north face (the rope, the slits, the window over it) from the rope's foot and further out
for name, (X, Y, Z), (LX, LY, LZ) in (('mok_rope_foot', (-16896, 17500, 1800), (-16896, 16490, 2700)),
                                       ('mok_window', (-16896, 17300, 3700), (-16896, 16490, 4000)),
                                       ('mok_north_mid', (-16896, 18300, 2000), (-16896, 16490, 3000)),
                                       ('mok_north_far', (-16200, 20200, 2100), (-16896, 16490, 3000))):
    d = math.hypot(LX - X, LY - Y)
    shots.append({'name': name, 'position': [X, Y, Z], 'yaw': round(math.atan2(LY - Y, LX - X), 4),
                  'pitch': round(math.atan2(LZ - Z, d), 4)})
shots[0]['commands'] = ['render hud off']
for s in s9:
    s['commands'] = [c for c in s.get('commands', []) if c != 'render hud off']
    if not s['commands']:
        del s['commands']
yaml.safe_dump({'output_dir': OUTD, 'settle_seconds': 2.0, 'exit': True, 'shots': shots + s9}, open(TY, 'w'),
               sort_keys=False)
print(len(shots) + len(s9), 'shots')
