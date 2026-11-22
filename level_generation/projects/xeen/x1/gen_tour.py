#!/usr/bin/env python3
"""Writes X1's picture tour (tour.yml for the game's screenshot tour) and captions.yml. Cameras in cells."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json, math, os, sys, yaml

C = _REPO_ROOT + '/output/studio_cal/x1'
OUT = sys.argv[1] if len(sys.argv) > 1 else C + '/tour'
hm = json.load(open(C + '/build/export.json'))['map']['terrain']['height_map']

def g(x, y):
    return hm[int(min(127, max(0, round(y)))) * 128 + int(min(127, max(0, round(x))))] * 32

# name, camera cell, look-at cell, height over ground, caption
SHOTS = [
    ('square_start', (54, 47.6), (54, 40), 170, 'Arrival in Vertigo square: the north street, the town hall tower, shops'),
    ('square_south', (54, 45), (54, 52), 170, 'From the square south: the south gate, the bridge, the guild row'),
    ('main_street_west', (60, 44), (43, 44), 170, 'Main street looking west to the west gate'),
    ('main_street_east', (44, 44), (62, 44), 170, 'Main street looking east to the east gate'),
    ('north_row', (51, 43.5), (47, 40.5), 170, 'North row: armoury, ironworks, town hall'),
    ('temple', (55, 43.5), (58, 47), 170, 'The temple and its spire'),
    ('tavern_inn', (47, 43.4), (45, 46.5), 170, "Lady Geraldine's Tavern and the Adventurer's Inn"),
    ('wall_aerial', (52, 64), (52, 44), 2600, 'Vertigo from the air: walled core, creek, south bank'),
    ('west_gate_out', (36, 44.5), (44, 44), 170, 'The west gate from outside, Thylon\'s Training on the left'),
    ('east_gate_out', (67, 44.5), (60, 44), 170, 'The east gate from the orchard road, the stables'),
    ('bridge', (52, 57), (52, 49), 170, 'Vertigo Bridge and the south gate from the guild lane'),
    ('guild_row', (50, 54.4), (44, 57), 170, 'The guild row on the south bank'),
    ('joes_yard', (58, 59), (61.5, 58.3), 170, "Joe's yard: the warehouse doors, the rain barrel, Joe's shop"),
    ('culvert', (61, 55.2), (61, 53.4), 170, 'The culvert grate on the riverbank (XD-01, barred from inside)'),
    ('north_road', (52, 37), (60, 30), 170, 'Out of the north gate: the north road into the hills'),
    ('hill_fork', (58, 34), (62, 31), 170, 'The hill fork and its signpost'),
    ('mine_portal', (44, 33.5), (44, 31.3), 170, 'XD-02: the Red Dwarf Mines portal'),
    ('shaft_head', (62, 30.8), (62, 28.6), 170, "XD-03: the Clan King's shaft head (barred from below)"),
    ('orc_mouth', (82, 32.6), (82, 30.4), 170, 'XD-05: the orc caves\' mouth'),
    ('orc_outpost', (56, 26), (56, 23), 200, 'An orc outpost: fire, crate, three orcs'),
    ('obelisk', (72, 36), (74, 34), 170, 'The obelisk on the hill'),
    ('hills_view', (66, 26), (52, 46), 600, 'From the hills down to Vertigo'),
    ('orchard_road', (72, 44.8), (104, 46.5), 170, 'Signature view: the orchard road east to the rim'),
    ('pyramid', (80, 48.5), (84, 46), 170, 'The travel pyramid on its knoll (sealed)'),
    ('rim', (100, 47), (110, 47), 170, 'The world rim: the cliff, the water far below'),
    ('rim_falls', (99, 57), (104, 60), 300, 'The creek falling over the rim'),
    ('delta', (60, 62), (68, 66), 300, "The delta pond and Orothin's isles"),
    ('toad_meadow', (70, 73.5), (77, 72), 170, "Toad Meadow: Myra's hut, Valia's cottage"),
    ('witch_tower', (84, 79), (88, 84), 170, 'The Witch Tower from the hamlet path'),
    ('tower_door', (88, 87.6), (88, 85.6), 170, 'XD-04: the Witch Tower door'),
    ('tower_from_town', (55, 50), (88, 84), 700, 'The Witch Tower seen from Vertigo\'s south wall'),
    ('dead_forest', (40, 82), (32, 92), 200, 'The Forest of the Walking Dead'),
    ('yak_door', (30, 99), (30, 96.6), 170, 'The sealed Temple of Yak (XD-06, not built)'),
    ('fountain_ability', (44, 72), (46, 70), 170, 'The Fountain of Ability'),
]

os.makedirs(OUT, exist_ok=True)
lines = ['output_dir: "%s"' % OUT, 'exit: true', 'settle_seconds: 2.5', 'shots:']
caps = {}
for i, (name, cam, look, h, cap) in enumerate(SHOTS):
    X, Y = (cam[0] - 64) * 512, (64 - cam[1]) * 512
    z = g(*cam) + h
    dx, dy = (look[0] - cam[0]) * 512, (cam[1] - look[1]) * 512
    yaw = math.atan2(dy, dx)
    lz = g(*look) + 150
    pitch = math.atan2(lz - z, math.hypot(dx, dy))
    lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, commands: ["render hud off"]}'
                 % (name, X, Y, z, yaw, pitch))
    caps['%02d-%s.png' % (i + 1, name)] = cap
open(C + '/tour.yml', 'w').write('\n'.join(lines) + '\n')
yaml.safe_dump(caps, open(OUT + '/captions.yml', 'w'), sort_keys=False, width=120)
print(len(SHOTS))
