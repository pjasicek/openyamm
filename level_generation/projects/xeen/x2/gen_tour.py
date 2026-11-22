#!/usr/bin/env python3
"""Writes a screenshot tour of X2 (for tools/run_game.sh --set debug.screenshot_tour_path=...).
gen_tour.py <export.json> <out tour.yml> <out dir> [set]"""
import json, math, sys
exp, out, odir = sys.argv[1], sys.argv[2], sys.argv[3]
which = sys.argv[4] if len(sys.argv) > 4 else 'main'
m = json.load(open(exp))['map']
hm = m['terrain']['height_map']
def W(x, y):
    return ((x - 64) * 512, (64 - y) * 512)
def ground(x, y):
    i, j = int(math.floor(x)), int(math.floor(y)); fx, fy = x - i, y - j
    h = lambda a, b: hm[max(0, min(127, b)) * 128 + max(0, min(127, a))] * 32
    return h(i, j) * (1 - fx) * (1 - fy) + h(i + 1, j) * fx * (1 - fy) + h(i, j + 1) * (1 - fx) * fy + h(i + 1, j + 1) * fx * fy
def shot(name, at, look, up=170, z=None, pitch=None):
    X, Y = W(*at); TX, TY = W(*look)
    zz = z if z is not None else ground(*at) + up
    yaw = math.atan2(TY - Y, TX - X)
    if pitch is None:
        d = math.hypot(TX - X, TY - Y)
        pitch = math.atan2(ground(*look) + 120 - zz, d)
    return {'name': name, 'position': [round(X), round(Y), round(zz)], 'yaw': round(yaw, 4), 'pitch': round(pitch, 4),
            'commands': ['render hud off']}
S = []
if which == 'main':
    S += [shot('over_town_se', (86, 70), (64, 50), z=3400), shot('over_town_nw', (44, 30), (66, 52), z=3600),
          shot('over_town_sw', (44, 70), (66, 48), z=3200), shot('over_town_ne', (86, 30), (64, 54), z=3200),
          shot('bridge_square_s', (64, 40.5), (64, 52)), shot('bridge_from_north_quay', (58, 48.6), (64, 52), up=170),
          shot('bridge_from_river_e', (74, 52.5), (64, 52), z=900), shot('bridge_deck', (64, 47.0), (64, 57), z=1200),
          shot('main_street_e', (83.5, 43), (66, 42)), shot('main_street_w', (50, 43), (60, 42)),
          shot('tavern_corner', (80, 44.6), (78, 40)), shot('south_square', (64, 61.5), (64, 54)),
          shot('guild_row', (60, 62), (52, 63)), shot('skill_row_temple', (69, 61), (78, 62)),
          shot('den_door', (68.5, 55.6), (66.5, 56.6), z=820), shot('dock', (78, 55.3), (84, 54.5), z=820),
          shot('north_promenade', (53, 46.0), (62, 46)), shot('stables_north', (64, 32), (65, 36)),
          shot('darzog_from_jetty', (47, 60.5), (31, 58), z=900), shot('darzog_door', (35.5, 58.1), (32.7, 58.1)),
          shot('lake_from_north', (32, 40), (31, 58), z=1500), shot('ogre_lair', (23, 33.5), (23, 29.7)),
          shot('ogre_bridge', (38, 41.5), (31, 40)), shot('temple_of_yak', (62, 95.5), (62, 99.1)),
          shot('fairy_woods', (60, 75), (58, 86), z=1400), shot('danulf_ring', (56, 78.5), (56, 82)),
          shot('rim_south', (64, 101), (64, 110), z=1300), shot('farmland', (66, 28), (80, 22), z=1500),
          shot('ranger_camp', (88, 28), (88, 24)), shot('east_road_in', (104, 46), (84, 44), z=1200),
          shot('dark_end', (55, 92), (64, 99), z=1300), shot('island_tower_far', (60, 56), (31, 58), z=1500)]
else:
    pass
doc = {'output_dir': odir, 'exit': True, 'settle_seconds': 2.5, 'shots': S}
with open(out, 'w') as f:
    f.write('output_dir: "%s"\nexit: true\nsettle_seconds: 2.5\nshots:\n' % odir)
    for s in S:
        f.write('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, time: "12:00", commands: ["render hud off", "sky weather 0", "weather clear"]}\n'
                % (s['name'], s['position'][0], s['position'][1], s['position'][2], s['yaw'], s['pitch']))
print(len(S), 'shots')
