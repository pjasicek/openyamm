#!/usr/bin/env python3
"""D3 Sandcaster and the Aging Forest: the L1 brief (MU-3 plan) for the phase 3 review (A5, 2026-11-20).

    gen_l1.py      writes devdocs/xeen/briefs/d3/L1/{project,plan,sketch}.yml

Then `oymap fmt` and `oymap validate --assets assets_dev` (run.sh does all three, the drawings and the board). Later
passes edit this script, not the YAML. Cells are [x, y] on the 128-cell grid (512 units), x east, y south.
Form after X4's L1 (level_generation/projects/xeen/x4/gen_l1.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'devdocs/xeen/briefs/d3/L1'

# ---------------------------------------------------------------- the edges and crossings
WEST_Y = 44          # D2's caravan road leaves D2's east edge at y 44 (D2 L1 edge:east); it arrives here at y 44
NORTH_X = 88         # the Lakeside road to D4 (D4 is not planned: D4 aligns its south road to this x)
RIM_X = 104          # the east rim: the bright face's glow above it (MAPS D3)
RIM_Y = 104          # the Darkside's south rim (D-23: D1 and D2 at y 104)
CROSS = [60, 44]     # the Crossroads: six roads meet in the market ring

# ---------------------------------------------------------------- project.yml
SLOTS = [
    {'monster': 'Xeen Mantis', 'tier': 1, 'per_marker': [2, 3], 'weight': 50},
    {'monster': 'Xeen Cobra', 'tier': 1, 'per_marker': [2, 3], 'weight': 26},
    {'monster': 'Xeen Sand Worm', 'tier': 1, 'per_marker': [2, 3], 'weight': 24},
]
LEVELS = {1: (22, 30, 38), 2: (30, 38, 45), 3: (30, 38, 45)}

PROJECT = {
    'format': 0,
    'id': 'xeen_d3',
    'name': 'Sandcaster and the Aging Forest',
    'world': 'xeen',
    'kind': 'outdoor',
    'profile': 'odm',
    'map_code': 'D3',
    'units': {'plan_grid': 512},
    'extent': {'terrain_cells': 128},
    'map_stats': {
        'id': 9110,
        'continent': 7,
        'encounter_chance': 10,
        'treasure_level': 3,
        'trap_dice': 4,
        'perception_difficulty': 4,
        'refill_days': 672,
        'music': 39,
        'environment': 'forest',
        'lock_difficulty': 8,
        'slots': SLOTS,
    },
    'neighbours': [
        {'id': 'edge:west', 'to': 'xeen_d2.odm', 'kind': 'edge', 'side': 'west', 'days': 5, 'arrival_side': 'east',
         'approach': f'The caravan road in from the west edge at y {WEST_Y}, down the dry valley under the last '
                     'Gemstone crags.',
         'notes': "D2 Sprite Forest and Ogre Pass (A6's L1): its caravan road leaves its east edge at y 44 (level "
                  "span 32-56 at 1,300; D2's entrance:east_road at its [106, 44]). The same y here; the level span "
                  "matches."},
        {'id': 'edge:north', 'to': 'xeen_d4.odm', 'kind': 'edge', 'side': 'north', 'days': 5, 'arrival_side': 'south',
         'approach': f'The Lakeside road in from the north edge at x {NORTH_X}, down the east bank of the River of '
                     'Wrath.',
         'notes': 'D4 Lakeside and Blackfang (phase 4, not planned): D4 aligns its south road to x 88 (each map keeps '
                  'its own arrival point, D-11.6). Plan crossing only until D4 exists.'},
        {'id': 'door:dd18', 'to': 'xeen_dd18.blv', 'kind': 'door',
         'arrival_hint': 'At the foot of the shaft ladder in the members\' room (A8 gives the inside point).',
         'notes': "DD-18 Sandcaster Sewer (A8, phase 3, optional; D-27): Barticus' members' room under the gym's "
                  "sign, with a long tunnel to D5 bolted on the desert side. A street shaft against the gym's "
                  "south-east corner (Barticus' Gym, 4607), off the west lane's walking line; the entrance preset "
                  "(D-24: \"Descend to the sewer?\"), no question of its own. Sealed with a line (\"The iron lid is "
                  "bolted from below.\") until A8 gives the inside point and DD-18 is installed."},
        {'id': 'door:dd19', 'to': 'xeen_dd19.blv', 'kind': 'door',
         'arrival_hint': 'Inside the guild gate, in the guild halls\' entry court.',
         'notes': "DD-19 Wizard Quarter (A8, phase 4; Q-D14): the guild gate at the back of the wizard quarter "
                  "(A3's q-d14.quarter_gate, open from the start; the quarter's five houses stay sealed until "
                  "q-d14.done). Sealed with a line after the hook until DD-19 is installed."},
        {'id': 'door:dd07', 'to': 'xeen_dd07.blv', 'kind': 'door', 'condition': {'item': 'east_tower_key'},
         'arrival_hint': 'Inside the Eastern Tower\'s door, at the foot of its stair.',
         'notes': "DD-07 Eastern Tower (A7, phase 4, D-9.3): the tower on its knoll by the east rim, north of the falls; A3's "
                  "q-d18.tower_door needs Q-D19's key. Sealed with a line after the hook until DD-07 is installed."},
        {'id': 'stable:sandcaster_castleview', 'to': 'xeen_d1.odm', 'kind': 'stable', 'days': 3,
         'schedule': {'weekdays': ['wednesday', 'saturday']},
         'service': 'Sandcaster Caravans (4611), route 416',
         'notes': "A4's d3.yml; the arrival is sandcaster_stables, the caravan yard outside the south gate."},
        {'id': 'stable:sandcaster_lakeside', 'to': 'xeen_d4.odm', 'kind': 'stable', 'days': 3,
         'schedule': {'weekdays': ['sunday']}, 'service': 'Sandcaster Caravans (4611), route 417',
         'notes': 'After D4 is built (A4).'},
        {'id': 'boat:lucio', 'to': 'xeen_d7.blv', 'kind': 'boat', 'condition': {'qbit': 'lucio_open'},
         'service': "Lucio's Jetty (4649), route 425 to olympus_dock", 'listed_only': True,
         'notes': "D-5.3 and D-28: the celestial boat to Olympus departs only (tue, fri), opens with m30.done; no "
                  "boat lands here (no sandcaster_jetty arrival). The jetty is a timber deck with mooring posts on "
                  "the top of the Sky Stair, a sandstone tower on the city's north-west corner."},
    ],
    'qbits': {
        # A3's bits (source/quests/*.yml); the names here are the map's.
        'handle_found': 113161,      # q-d8.handle_found: the ruin's emerald handle taken
        'quarter_open': 113281,      # q-d14.done: the wizard quarter's five houses open
        'q_d18_started': 113360,     # q-d18.started: set by the tower door hook
        'fountain_restored': 113364,  # q-d18.done: the Fountain of Youth works
        'celia_done': 112442,        # q-c22.done: Celia rescued on Cloudside
        'celia_moved': 112443,       # q-c22.moved: Celia and Derek live in house 4647
        'lucio_open': 111600,        # m30.done: the Chosen Ones; Lucio's Jetty opens
        'obelisk_dark_3': 115052,    # obelisks.dark_3
        'mirror_sandcaster': 119009,
    },
    'items': {
        'sandcaster_pass': 12335,
        'east_tower_key': 12340,
        'vespars_handle': 12345,
    },
    'rules': {
        'weather': 'none',
        'town_portal_anchor': 'entrance:sandcaster_square',
        'rim': {'sides': ['east', 'south'], 'cliff_x': RIM_X, 'cliff_y': RIM_Y, 'fall': 'death'},
    },
    'notes': 'D3 Sandcaster and the Aging Forest, MU-3 plan for the phase 3 review (A5, 2026-11-20). No geometry '
             'until a decider has approved it. Plan: plan.yml; to-scale layout: sketch.yml; generator, drawings and '
             'review board: output/studio_cal/d3/ (tools/gen_l1.py writes these three files). Sky xeendark1 '
             '(xeen_darkside_day; A3\'s Lua switches the failing-sun stages).',
}

# ---------------------------------------------------------------- the land: zones and bands
ZONES = {
    'zone:rim': [[RIM_X, 0], [128, 0], [128, 128], [0, 128], [0, RIM_Y], [RIM_X, RIM_Y]],
    'zone:gemstone_crags': [[0, 0], [24, 0], [22, 8], [20, 16], [16, 24], [12, 30], [0, 34]],
    'zone:desert_edge': [[24, 0], [80, 0], [79, 10], [80, 20], [78, 28], [77, 36], [72, 40], [64, 36], [56, 36],
                         [50, 38], [47, 39], [47, 20], [27, 20], [20, 16], [22, 8]],
    'zone:caravan_valley': [[0, 34], [12, 30], [16, 24], [20, 20], [27, 20], [27, 43], [36, 44], [50, 44], [50, 48],
                            [40, 49], [30, 50], [20, 51], [0, 54]],
    'zone:crossroads_plain': [[47, 39], [50, 38], [56, 36], [64, 36], [72, 40], [73, 44], [70, 52], [66, 56],
                              [60, 56], [54, 52], [50, 48], [50, 44]],
    'zone:wrath_hills': [[80, 0], [RIM_X, 0], [RIM_X, 54], [92, 56], [88, 50], [84, 44], [80, 40], [77, 36],
                         [78, 28], [80, 20], [79, 10]],
    'zone:river_meadows': [[70, 52], [73, 44], [72, 40], [77, 36], [80, 40], [84, 44], [88, 50], [92, 56],
                           [RIM_X, 54], [RIM_X, 72], [90, 72], [80, 70], [72, 66], [66, 56]],
    'zone:howling_woods': [[0, 54], [20, 51], [30, 50], [36, 54], [38, 64], [36, 80], [34, 92], [32, RIM_Y],
                           [0, RIM_Y]],
    'zone:aging_forest': [[30, 50], [40, 49], [50, 48], [54, 52], [60, 56], [62, 64], [64, 74], [62, 86],
                          [60, RIM_Y], [32, RIM_Y], [34, 92], [36, 80], [38, 64], [36, 54]],
    'zone:venom_fen': [[60, 56], [66, 56], [72, 66], [80, 70], [90, 72], [RIM_X, 72], [RIM_X, RIM_Y], [60, RIM_Y],
                       [62, 86], [64, 74], [62, 64]],
}

TOWNS = {
    'town:sandcaster': [[27, 20], [47, 20], [47, 39], [27, 39]],
    'zone:sc_square': [[33, 27], [40, 27], [40, 33], [33, 33]],
    'zone:wizard_quarter': [[40, 20], [47, 20], [47, 27], [40, 27]],
    'zone:caravan_yard': [[34, 39], [44, 39], [44, 45], [34, 45]],
    'town:crossroads': [[55, 39], [65, 39], [65, 49], [55, 49]],
    'zone:celia_yard': [[63, 45], [67, 45], [67, 49], [63, 49]],
    'zone:thaddeus_yard': [[78, 73], [84, 73], [84, 79], [78, 79]],
    'zone:cornelius_glade': [[37, 69], [43, 69], [43, 75], [37, 75]],
    'zone:tower_knoll': [[93, 42], [101, 42], [101, 50], [93, 50]],
    'zone:wrath_falls': [[97, 55], [RIM_X, 55], [RIM_X, 66], [97, 66]],
}

BANDS = [
    ('band:rim_sea', 'zone:rim'),
    ('band:peaks', 'zone:gemstone_crags'),
    ('band:high', 'zone:wrath_hills'),
    ('band:mid', 'zone:desert_edge'),
    ('band:mid', 'town:sandcaster'),
    ('band:ridge', 'zone:howling_woods'),
    ('band:plain', 'zone:caravan_valley'),
    ('band:plain', 'zone:crossroads_plain'),
    ('band:low', 'zone:aging_forest'),
    ('band:low', 'zone:river_meadows'),
    ('band:fen', 'zone:venom_fen'),
]

HEIGHT_POINTS = [
    ([6, 12], 3400, 'the last Gemstone crag (D2: the range\'s east end, 2,800-3,600 at the shared edge)'),
    ([14, 6], 3000, None),
    ([10, 24], 2600, None),
    ([20, 44], 1300, 'the D2 arrival (D2\'s edge span is level at 1,300)'),
    ([36.5, 44], 1280, 'the gate fork'),
    ([37, 30], 1500, "Sandcaster's terrace (the walls stand on its edge, 300 over the valley)"),
    ([43, 23], 1700, 'the wizard quarter, raised over the city'),
    ([28, 21], 1500, 'the Sky Stair, a sandstone tower with Lucio\'s Jetty on its top'),
    ([50.5, 27], 1650, "the obelisk's dune knoll"),
    ([60, 26], 1600, 'dunes of the desert edge'),
    ([63.5, 28], 1500, 'the caravan well'),
    ([66, 12], 1900, 'the desert edge beyond the north boundary'),
    ([60, 44], 1250, 'the Crossroads'),
    ([65, 47], 1240, "Celia and Derek's cottage"),
    ([81, 21], 1100, 'the Wrath Spring: the river bursts from a cave at the head of its gorge'),
    ([88, 20], 1750, 'the D4 arrival on the Lakeside road'),
    ([88, 24], 1850, 'the Lakeside saddle: the D4 road corridor x 86-90 (D-28: at most 1,900)'),
    ([92, 27], 3300, 'the Wrath crest (D-28: a broken crest at 3,100-3,400 east of the river)'),
    ([96, 24], 3400, "the Wrath crest's high point, Wrathtop"),
    ([100, 30], 3200, None),
    ([94, 34], 3100, None),
    ([99, 37], 3150, None),
    ([73, 23], 2400, 'the west-bank hills over the gorge (D-28: to about 2,400)'),
    ([70, 29], 2100, None),
    ([97, 46], 1950, "the Eastern Tower's knoll by the rim, over the falls"),
    ([82, 45], 1250, 'the east fork'),
    ([75.5, 46], 1250, 'Wrath Bridge (the river 250 below in its cut)'),
    ([101, 57], 1150, 'the Rim Watch over the falls'),
    ([103, 64], 1000, 'the Wrath Falls: the river drops off the rim into the stars'),
    ([88, 65], 1080, 'the river fruit hut on the south bank'),
    ([80.5, 75], 960, "Thaddeus's hut and the Fountain of Youth"),
    ([72, 82], 864, 'Venom Pond'),
    ([95, 95], 980, 'the Fountain of Great Protection near the rims\' corner'),
    ([40, 72], 1120, "Cornelius's glade"),
    ([53, 65], 1150, 'the great oak of the Aging Forest'),
    ([46, 101], 1050, 'the edge cairn on the south rim'),
    ([24, 60], 1950, 'the Howling ridge (D-28: 1,900-2,200, falling west to D2\'s edge heights)'),
    ([25, 70], 2150, None),
    ([24, 80], 2200, 'the howling stone on the ridge'),
    ([24, 90], 2050, None),
    ([27, 98], 1900, None),
    ([30, 101], 1300, "the smugglers' rope over the rim"),
]

CLIFFS = [
    {'line': [[RIM_X, 0], [RIM_X, 64], [RIM_X, RIM_Y]], 'drop': 1000, 'down': 'left',
     'notes': 'The east rim (drawn north to south, the low side east, on the left): a cliff of 900-2,300 above the '
              'stars; the bright face\'s glow stands above it.'},
    {'line': [[RIM_X, RIM_Y], [52, RIM_Y], [0, RIM_Y]], 'drop': 1000, 'down': 'left',
     'notes': 'The south rim at y 104 (D-23), drawn east to west, the low side south.'},
    {'line': [[27, 39], [36, 39]], 'drop': 300, 'down': 'right',
     'notes': "Sandcaster's terrace edge under the south wall (west of the gate)."},
    {'line': [[37, 39], [47, 39], [47, 20]], 'drop': 300, 'down': 'right',
     'notes': "The terrace edge under the south-east walls (the east gate's ramp at y 31)."},
]

RIDGES = [
    {'line': [[2, 30], [6, 20], [8, 12], [14, 6], [22, 2]], 'height': 3200, 'width': 2, 'slope': 3,
     'notes': 'The last Gemstone crags (D2\'s range ends here).'},
    {'line': [[90, 28], [93, 25.5], [97, 23.5]], 'height': 3300, 'width': 2, 'slope': 3,
     'notes': 'The Wrath crest, north part (D-28): broken by a saddle of about 2,600 at [98, 27].'},
    {'line': [[99.5, 29.5], [100, 33], [98, 38]], 'height': 3150, 'width': 2, 'slope': 3,
     'notes': 'The Wrath crest, south part, above the tower knoll.'},
    {'line': [[24, 56], [25, 66], [23.5, 77], [24, 88], [27, 98]], 'height': 2050, 'width': 2, 'slope': 5,
     'notes': "The Howling ridge (D-28): walkable shoulders both sides; west it falls to D2's east-edge hills "
              '(1,300-1,700 at [56, 104]).'},
]

RIVER = {'id': 'water:wrath',
         'line': [[81, 21], [79.5, 26], [78.5, 32], [77.5, 38], [76.5, 42], [75.5, 46], [76.5, 50], [78.5, 53],
                  [82, 57], [88, 60], [94, 62], [100, 63.5], [RIM_X, 64]],
         'width_cells': 2.5, 'level': 1000,
         'notes': 'The River of Wrath (D-23: it rises and falls inside D3): it bursts from the Wrath Spring\'s cave '
                  'at the head of a gorge between the west-bank hills (2,400) and the Lakeside saddle (1,850), runs '
                  'south in a cut 300-1,300 deep, under Wrath Bridge, then east through the meadows and '
                  'over the east rim at the Wrath Falls. It touches neither the y 44 west edge nor any map edge.'}

RIM_SEA = {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': ZONES['zone:rim'],
           'notes': 'Below the rim: stands for the stars.'}
VENOM_POND = {'id': 'water:venom_pond', 'kind': 'pond', 'level': 864,
              'polygon': [[67, 77], [72, 75], [77, 77], [78, 81], [75, 87], [69, 88], [66, 83]],
              'notes': 'Venom Pond: green, still, reeds; cobras round it; it seeps into the fen (no outflow).'}

ROADS = [
    ('link:caravan_road', [[0, WEST_Y], [20, WEST_Y], [28, WEST_Y], [36.5, WEST_Y], [44, 45], [52, 45],
                           [57, WEST_Y], CROSS], 'road', 'road_flagstone'),
    ('link:gate_lane', [[36.5, 39], [36.5, 41.5], [36.5, WEST_Y]], 'road', 'road_flagstone'),
    ('link:city_road', [[47, 31.5], [50, 31.5], [52, 34], [55, 38], [57.8, 41.8], CROSS], 'road', 'road_flagstone'),
    ('link:dune_track', [CROSS, [60, 41.2], [61, 36], [62.5, 31], [63.5, 28.5], [60.5, 25.5], [57.5, 25.5]], 'lane', None),
    ('link:obelisk_path', [[50, 31.5], [50.5, 28]], 'lane', None),
    ('link:bridge_road', [CROSS, [63, 44], [68, 45.5], [74, 46], [77, 46], [82, 45]], 'road', 'soil'),
    ('link:lakeside_road', [[82, 45], [84, 40], [86, 34], [87.5, 28], [88, 20], [NORTH_X, 0]], 'road', 'soil'),
    ('link:tower_lane', [[82, 45], [88, 45.5], [93, 46.5], [96, 46.5]], 'lane', None),
    ('link:spring_path', [[87.5, 28], [85.5, 25], [84, 22.5]], 'lane', None),
    ('link:high_path', [[88, 22], [92, 21], [95.5, 20.5], [98, 21]], 'lane', None),
    ('link:rim_track', [[82, 45], [86, 50], [92, 55], [98, 57], [101, 57]], 'lane', None),
    ('link:venom_road', [CROSS, [62.5, 46.5], [64.5, 49], [64.5, 51], [68, 55], [71, 61], [75, 67], [79, 72], [80.5, 74.5]], 'road',
     'soil'),
    ('link:orchard_path', [[75, 67], [80, 66.5], [84, 65.5], [87.5, 65.5]], 'lane', None),
    ('link:fen_track', [[75, 67], [86, 74], [92, 82], [94, 92], [95, 95]], 'lane', None),
    ('link:forest_road', [CROSS, [59, 47.5], [57, 52], [52, 58], [46, 64], [42, 70], [40, 78], [42, 88], [45, 97],
                          [46, 101]], 'road', 'soil'),
    ('link:howling_track', [[40, 78], [34, 79], [26, 78.5], [22, 83], [24, 92], [30, 100]], 'lane', None),
    ('link:oak_lane', [[49, 61], [51, 63], [52.5, 64.2]], 'lane', None),
]

# ---------------------------------------------------------------- buildings and plots
# Sandcaster's services: (building id (A4's door), service, A4 house, footprint [front, depth], at (top-left),
# facing, door_to, kit)
SANDCASTER = [
    ('building:sc_lucio_jetty', "Lucio's Jetty", 4649, [2, 2], [27.5, 20.5], 's', 'zone:sc_north_street', 'castle'),
    ('building:sc_guild_mind', 'Sandcaster Guild of Mind', 4608, [2.5, 2.5], [30, 21], 's', 'zone:sc_north_street',
     'stone'),
    ('building:sc_guild_spirit', 'Sandcaster Guild of Spirit', 4609, [2.5, 2.5], [33, 21], 's',
     'zone:sc_north_street', 'stone'),
    # F49 (2026-11-24): two cells wide, not 2.5: it stood 56 from Astra's House (houses.jammed), and plots keep to
    # half cells between the Guild of Spirit and Astra's House (the quarter's wall behind it)
    ('building:sc_guild_light', 'Sandcaster Guild of Light', 4610, [2, 2.5], [36, 21], 's',
     'zone:sc_north_street', 'stone'),
    ('building:sc_magic', "Aladdin's Lamps", 4603, [2, 2], [33, 25], 's', 'zone:sc_square', 'rich'),
    ('building:sc_alchemist', 'Vulture Repellant and Other Remedies', 4604, [1.5, 2], [37.5, 25], 's',
     'zone:sc_square', 'plaster'),
    ('building:sc_temple', 'Temple of the Desert Sun', 4605, [2.5, 3], [27.5, 25.5], 'e', 'zone:sc_west_lane',
     'stone'),
    ('building:sc_training', "Barticus' Gym", 4607, [2.5, 3], [27.5, 29], 'e', 'zone:sc_west_lane', 'plaster'),
    ('building:sc_tavern', 'The Thirsty Camel', 4606, [2.5, 2], [33.5, 35], 'e', 'zone:sc_main_street', 'rich'),
    ('building:sc_weapons', 'Sandsteel Blades', 4601, [2, 1.5], [40, 32.5], 'n', 'zone:sc_east_street', 'rich'),
    ('building:sc_armour', 'The Brass Scale', 4602, [2, 1.5], [42.5, 32.5], 'n', 'zone:sc_east_street', 'plaster'),
    ('building:sc_stables', 'Sandcaster Caravans', 4611, [2.5, 2], [40.5, 40], 'w', 'zone:caravan_yard', 'poor'),
]
# The wizard quarter (opens with q-d14.done): (building id, service, house, fp, at, facing, kit)
QUARTER = [
    ('building:wq_guild_dark', 'The Guild of Night', 4613, [2, 2], [40.5, 21.5], 'e', 'stone'),
    ('building:wq_magic', 'Esoterica', 4614, [2, 1.5], [44.5, 21.5], 'w', 'stone'),
]
QUARTER_HOUSES = [  # wq_houses#1-3 = 4615 Mindwright, 4616 Appraiser, 4617 Alembic (towers)
    (4615, [1.5, 1.5], [40.5, 24.5], 's', 'castle'),
    (4616, [1.5, 1.5], [42.5, 25], 'n', 'castle'),
    (4617, [1.5, 1.5], [44.5, 24.5], 's', 'castle'),
]
# sc_houses#1-23 = 4618-4640 in index order (A4's d3.yml): (house, fp, at, facing, kit)
SC_HOUSES = [
    (4618, [1, 1.5], [38.5, 21.5], 's', 'rich'),       # Astra's House, outside the quarter, by the guild row
    (4619, [1.5, 1.5], [35.5, 25], 's', 'rich'),     # Natasha the Enchantress, on the square (M25)
    (4620, [1, 1], [32, 27.5], 'e', 'plaster'),        # Madame Gloriana's, on the square's west side
    (4621, [1, 1], [32, 29.5], 'e', 'plaster'),        # School of Trade
    (4622, [1, 1], [32, 31], 'e', 'plaster'),        # School of Letters
    (4623, [1.5, 1], [27.5, 32.5], 's', 'poor'),         # The Quiet House (the retired thief)
    (4624, [1, 1.5], [27.5, 34.5], 'e', 'plaster'),      # School of Navigation
    (4625, [1.5, 1.5], [27.5, 36.5], 'n', 'poor'),       # School of Tongues
    (4626, [1, 1], [29.5, 36.5], 'n', 'poor'),         # The Knife House (Kirra)
    (4627, [1.5, 1], [32, 33.5], 'e', 'plaster'),      # Saffron House
    (4628, [1.5, 1], [31, 37.5], 'n', 'plaster'),    # The Archer's House
    (4629, [1, 1], [45, 32.5], 'n', 'poor'),           # Dune House
    (4630, [1, 1.5], [38, 34], 'w', 'plaster'),        # The Dyer's
    (4631, [1.5, 1.5], [38, 36], 'w', 'plaster'),      # Glassblower's House
    (4632, [1.5, 1], [40.5, 35], 'n', 'poor'),         # The Water Seller's
    (4633, [1, 1], [43, 35], 'n', 'poor'),           # Camel House
    (4634, [1, 1.5], [45, 35], 'w', 'plaster'),        # Scribe's House
    (4635, [1.5, 1], [41, 37.5], 'n', 'poor'),         # Potter's Yard
    (4636, [1.5, 1], [44, 37.5], 'n', 'rich'),         # The Tax House
    (4637, [1.5, 1], [41, 28], 's', 'rich'),         # Courtyard House
    (4638, [1, 1], [43.5, 28], 's', 'plaster'),      # Sandal Maker's
    (4639, [1, 1], [45.5, 28], 's', 'plaster'),      # Date Palm House
    (4640, [1.5, 1], [30.5, 24.5], 'n', 'plaster'),    # Well House (Omid; the deep well is on the square)
]

# The Crossroads: six stalls round the ring where six roads meet; stall centres at radius 2.8 between the roads.
CROSS_STALLS = [  # (xr_stall index, house, angle deg (image coords, clockwise from east), facing, fp)
    (1, 4641, 140, 'e', [1, 1]),      # The Food Stall (south-west, by the forest road)
    (2, 4642, 202.5, 'e', [1, 1]),    # Robes and Cloaks
    (3, 4643, 247.5, 's', [1, 1]),    # Necklaces of Note
    (4, 4644, 315, 'w', [1, 1]),      # Belts and Buckles
    (5, 4645, 22.5, 'w', [1, 1]),     # Boots for the Road
    (6, 4646, 72.5, 'n', [1.5, 1.5]),  # Caleb's Workshop (Q-D15)
]
HUTS = [
    ('zone:celia_yard', 'building:celia_derek_cottage', "Celia and Derek's Cottage", 4647, [1.5, 1.5], [64, 46],
     's', 'poor'),    # D-28: about 1,400 from the ring's edge, the door south toward Venom Pond
    ('zone:thaddeus_yard', 'building:thaddeus_hut', "The Fountain Keeper's Hut", 4648, [1.5, 1.5], [81, 74], 'w',
     'poor'),
]


def stall_at(angle, fp):
    a = math.radians(angle)
    cx, cy = CROSS[0] + 2.8 * math.cos(a), CROSS[1] + 2.8 * math.sin(a)
    return [round((cx - fp[0] / 2) * 2) / 2, round((cy - fp[1] / 2) * 2) / 2]


# ---------------------------------------------------------------- points
POINTS = [
    # arrivals and edges
    ('entrance:west_road', [20, WEST_Y], 'e', 'Arrival from D2 Sprite Forest (the caravan road; D2 leaves at y 44).'),
    ('entrance:north_road', [NORTH_X, 20], 's', 'Arrival from D4 Lakeside (the Lakeside road).'),
    ('entrance:sandcaster_square', [36, 30], 's', "A4 arrival sandcaster_square: by the mirror (Town Portal)."),
    ('entrance:sandcaster_stables', [37, 41.5], 'e', 'A4 arrival sandcaster_stables: the caravan yard outside the '
                                                    'south gate.'),
    ('entrance:south_gate', [36.5, 39], 's', "Sandcaster's south gate: A3's q-d8.sandcaster_gate (the pass) from "
                                             "outside; always opens from inside."),
    ('entrance:east_gate', [47, 31.5], 'e', "Sandcaster's east gate onto the Crossroads road: the same pass check."),
    ('entrance:dd18_shaft', [30, 32], 'n', "DD-18 Sandcaster Sewer (D-27): a street shaft against Barticus' Gym's "
                                            "south-east corner, clear of the gym door and the west lane."),
    ('entrance:dd19_gate', [43.5, 20.6], 'n', 'DD-19 Wizard Quarter: the guild gate at the back of the quarter '
                                              '(q-d14.quarter_gate).'),
    ('entrance:dd07_door', [96, 46.5], 'w', 'DD-07 Eastern Tower: the door on the knoll by the east rim '
                                            '(q-d18.tower_door, the Eastern Tower key).'),
    # junctions
    ('junction:gate_fork', [36.5, WEST_Y], None, None),
    ('junction:crossroads', CROSS, None, None),
    ('junction:east_fork', [82, 45], None, None),
    ('junction:venom_fork', [75, 67], None, None),
    ('junction:forest_fork', [40, 78], None, None),
    # places
    ('poi:obelisk', [50.5, 27], None, "On a dune knoll outside the east gate ('Obelisk by Sandcaster')."),
    ('poi:sc_mirror', [33.5, 31.5], None, "A4 4612 (thing:sc_mirror): the square's mirror, the Town Portal anchor."),
    ('poi:sc_well', [38.5, 31], None, "Omid's deep well on the square."),
    ('poi:market_well', CROSS, None, "The Crossroads' trough well in the ring."),
    ('poi:cornelius', [40, 72], None, 'Cornelius the Leprechaun (5247) in his glade: the outdoor Perception teacher.'),
    ('poi:vespar_ruin', [45, 47.5], None, "A roadside ruin at the Aging Forest's edge (q-d8.handle)."),
    ('poi:fountain_youth', [79.6, 76.4], None, "Beside Thaddeus's hut by Venom Pond (q-d18.fountain)."),
    ('poi:fountain_protection', [95, 95], None, None),
    ('poi:fruit_hut_river', [88, 65], None, None),
    ('poi:fruit_hut_forest', [60, 72], None, "The fig hut at the forest's east edge (closes the 6,000 rule there)."),
    ('poi:wrath_spring', [84, 22], None, 'The spring basin on the gorge head\'s lip (the cave below).'),
    ('poi:rim_watch', [101, 57], None, 'Over the Wrath Falls: the rim view and the watchman\'s locker.'),
    ('poi:howling_stone', [24, 80], None, None),
    ('poi:edge_cairn', [46, 101], None, None),
    ('poi:caravan_well', [63.5, 28.5], None, None),
    ('poi:great_oak', [53, 65], None, 'D-28: about 2,900 east of the forest road, by the oak lane.'),
    ('poi:wayside_shrine', [69, 58], None, None),
    # chests with a reason
    ('poi:caravan_wreck', [57.5, 25.5], None, None),
    ('poi:mantis_mound', [25, 66], None, None),
    ('poi:aged_skeleton', [52, 88], None, None),
    ('poi:drowned_skiff', [70, 88.6], None, None),
    ('poi:tower_cart', [92, 42], None, None),
    ('poi:smugglers_rope', [30, 101], None, None),
    ('poi:fallen_courier', [98.5, 21], None, 'On the crest\'s north shoulder (D-28: the high path round Wrathtop).'),
    # landmarks (no click)
    ('landmark:sandcaster', [37, 29], None, None),
    ('landmark:sky_stair', [28.5, 21.5], None, None),
    ('landmark:eastern_tower', [97, 46], None, None),
    ('landmark:wrath_falls', [103, 64], None, None),
    ('landmark:rim_glow', [110, 40], None, 'The bright face\'s glow above the east rim (sky, not geometry).'),
    ('landmark:gemstone_crags', [8, 14], None, None),
]
SIGNPOSTS = ['junction:gate_fork', 'junction:crossroads', 'junction:east_fork', 'junction:venom_fork',
             'junction:forest_fork']

# ---------------------------------------------------------------- monsters
# Encounter areas: (id, slot, markers, polygon, family note)
AREAS = [
    ('pop:dune_scrub', 3, 11, [[53, 19], [77, 19], [77, 30], [75, 38], [70, 40], [66, 37], [60, 35], [53, 34]],
     'Sand burrowers (Sand Worm 30, Armadillo 38, Great Worm 45) in the dunes between the city, the river and the '
     'Crossroads; at least 5 cells from the east gate and the stalls.'),
    ('pop:wrath_hills', 1, 12, [[83, 27], [89, 27], [96, 20], [103, 20], [103, 24], [98, 24], [91, 30], [90, 40],
                                [103, 40], [103, 54], [92, 56], [86, 50], [84, 42]],
     'Mantis ants (22/30/38) on the Wrath hills\' walkable shoulders (D-28): the road shelf under the crest, its north '
     'shoulder and its south foot round the Eastern Tower; none on the crest\'s steep flanks.'),
    ('pop:howling_woods', 1, 12, [[19, 53], [33, 52], [37, 60], [35, 76], [33, 90], [31, 103], [19, 103]],
     'Mantis ants on the Howling ridge\'s shoulders (the mantis mound); the first fight from D2.'),
    ('pop:venom_fen', 2, 12, [[62, 84], [70, 90], [80, 86], [88, 80], [103, 76], [103, 103], [60, 103]],
     'Cobras (Guardian Asp 30, Killer Cobra 38, King Cobra 45) round Venom Pond\'s south shore and the fen to the '
     'rims\' corner; at least 7 cells from Thaddeus\'s hut.'),    # F10 (A5 s30, 2026-11-22; the orchestrator's decision: a population outside the walls): the land west and south
    # of Sandcaster's walls, the caravan valley and the river meadows were one empty zone (empty_zones.py: 765 tiles,
    # deepest 16,804 at tile [20, 20]). Three single markers at fixed spots (gen.py FIXED_SPOTS): outside the city's
    # buffer, off the roads, 7,300 or more from the D7 fall landing (34, 41) and the D2 arrival, the meadows and the
    # Aging Forest kept open (a first try at (34, 47), 3,100 from the landing, failed playtest_d7_fall's D-54 20 s).
    ('pop:outside_walls', 3, 2, [[19, 19], [22, 19], [22, 46], [48, 46], [48, 51], [19, 51]],
     'Sand burrowers outside the walls: under the west wall by the rim and in the caravan valley south of the city.'),
    ('pop:forest_edge', 1, 1, [[63, 56], [71, 56], [71, 66], [63, 66]],
     "Mantis ants between the Aging Forest's east edge and the river meadows."),
]
# Placed hostiles (monster id, at, count, spread, group, note): the Aging Forest's hornet nests (MAPS: hell hornets
# only there). Three nests, each five Hell Hornets 35 and one Hornet Swarm 42; no Hornet Queen 50 (over C 45).
ACTORS = [
    ('11350', [53.5, 64.5], 5, 2, 1, 'Hell Hornets 35 at the nest in the great oak (D-28: >= 2,000 off the road).'),
    ('11351', [54, 65.5], 1, 1, 1, 'A Hornet Swarm 42.'),
    ('11350', [55, 82], 5, 2, 2, 'Hell Hornets at the hollow-log nest.'),
    ('11351', [56, 83], 1, 1, 2, 'A Hornet Swarm.'),
    ('11350', [44, 93], 5, 2, 3, 'Hell Hornets at the nest near the south rim.'),
    ('11351', [45, 94], 1, 1, 3, 'A Hornet Swarm.'),
]
KEEP_CLEAR = [
    ('town:sandcaster', [[22, 15], [52, 15], [52, 45], [22, 45]],
     'The city, its gates and the caravan yard with their buffer (about 2,500 round the doors).'),
    ('town:crossroads', [[52, 36], [69, 36], [70, 55], [52, 53]],
     'The market ring and Celia and Derek\'s cottage with their buffer.'),
    ('zone:thaddeus_yard', [[75, 70], [86, 70], [86, 81], [75, 81]], "Thaddeus's hut and the Fountain of Youth."),
    ('zone:cornelius_glade', [[36, 68], [44, 68], [44, 76], [36, 76]], None),
    ('edge:west_end', [[19, 40], [27, 40], [27, 48], [19, 48]], 'The D2 arrival.'),
    ('edge:north_end', [[85, 19], [91, 19], [91, 24], [85, 24]], 'The D4 arrival.'),
]
OPEN = [
    ('zone:river_meadows', [[72, 44], [82, 46], [92, 56], [100, 56], [100, 70], [90, 70], [80, 68], [72, 64]],
     'Quiet meadows by the lower river: the bridge, the river fruit hut, the Rim Watch over the falls.'),
    ('zone:aging_forest', [[38, 50], [54, 52], [60, 58], [62, 72], [60, 100], [38, 100], [38, 80], [40, 64]],
     'The Aging Forest is quiet but for its three hornet nests: falling leaves, the great oak, Cornelius.'),
]

VIEWS = [
    {'id': 'view:arrival', 'at': [15, WEST_Y], 'height': 200, 'look': [42, 31],
     'purpose': "MU-4 arrival view from D2's caravan road just inside the edge: east-north-east down the dry valley; on the left Sandcaster's "
                "sandstone walls and towers on their terrace, the Sky Stair with Lucio's jetty at the corner, the "
                "wizard quarter's pink towers above; ahead the road to the Crossroads' awnings, the ruin by the "
                "road; on the right the dark Howling Woods and the gold-red crowns of the Aging Forest; far east "
                "the pale glow above the rim."},
    {'id': 'view:signature', 'at': [84, 62], 'height': 200, 'look': [104, 54],
     'purpose': "MU-4 signature view: from the river meadows' south bank, east down the River of Wrath to the "
                "Wrath Falls, where it drops off the east rim into the stars; above the rim the bright face's glow; "
                "the Eastern Tower on its knoll by the rim at the left, the Rim Watch on the bluff between."},
]


def half(at):
    return [round(v * 2) / 2 for v in at]


def cell(at):
    return [int(math.floor(at[0])), int(math.floor(at[1]))]


def rect_of(at, fp, facing):
    front, depth = fp
    wx, wy = (front, depth) if facing in 'ns' else (depth, front)
    return (at[0], at[1], at[0] + wx, at[1] + wy)


def check_plots(plots):
    rects = [(name, rect_of(at, fp, f)) for name, at, fp, f in plots]
    bad = []
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i][1], rects[j][1]
            if a[0] < b[2] - 0.05 and b[0] < a[2] - 0.05 and a[1] < b[3] - 0.05 and b[1] < a[3] - 0.05:
                bad.append((rects[i][0], rects[j][0]))
    return bad


# ---------------------------------------------------------------- sketch.yml
def sketch():
    bands = [{'band': b, 'space': s, 'polygon': ZONES.get(s) or TOWNS[s]} for b, s in BANDS]
    districts = []
    plot_rects = []
    sc_plots = []
    yard_plots = []
    for bid, service, house, fp, at, facing, door_to, kit in SANDCASTER:
        plot = {'building': bid, 'at': at, 'facing': facing, 'door_to': door_to, 'kit': kit, 'house': house}
        (yard_plots if bid == 'building:sc_stables' else sc_plots).append(plot)
        plot_rects.append((bid, at, fp, facing))
    for i, (house, fp, at, facing, kit) in enumerate(SC_HOUSES, 1):
        sc_plots.append({'building': 'building:sc_houses', 'index': i, 'at': at, 'facing': facing, 'kit': kit,
                         'house': house})
        plot_rects.append((f'sc_houses#{i}', at, fp, facing))
    districts.append({'space': 'town:sandcaster', 'polygon': TOWNS['town:sandcaster'], 'plots': sc_plots,
                      'notes': "A4's d3.yml: 11 services, Lucio's Jetty (4649) on the Sky Stair, the mirror (4612, a "
                               "thing on the square) and 23 homes inside a sandstone wall on a terrace 300 over the "
                               "valley (20 x 19 cells); the caravan yard (stables 4611) outside the south gate. Two "
                               "gates (south to the caravan road, east to the Crossroads), each with the pass check."})
    wq_plots = []
    for bid, service, house, fp, at, facing, kit in QUARTER:
        wq_plots.append({'building': bid, 'at': at, 'facing': facing, 'door_to': 'zone:wizard_quarter', 'kit': kit,
                         'house': house})
        plot_rects.append((bid, at, fp, facing))
    for i, (house, fp, at, facing, kit) in enumerate(QUARTER_HOUSES, 1):
        wq_plots.append({'building': 'building:wq_houses', 'index': i, 'at': at, 'facing': facing, 'kit': kit,
                         'house': house})
        plot_rects.append((f'wq_houses#{i}', at, fp, facing))
    districts.append({'space': 'zone:wizard_quarter', 'polygon': TOWNS['zone:wizard_quarter'], 'plots': wq_plots,
                      'notes': "The wizard quarter on a terrace 200 over the city, pink ashlar (the kit's hc): a small "
                               "court with the Guild of Night, Esoterica and three towers (4613-4617, sealed until "
                               "q-d14.done) and the guild gate in the back wall (DD-19, open from the start). A stair "
                               "from the square's north-east corner."})
    districts.append({'space': 'zone:sc_square', 'polygon': TOWNS['zone:sc_square']})
    districts.append({'space': 'zone:caravan_yard', 'polygon': TOWNS['zone:caravan_yard'], 'plots': yard_plots,
                      'notes': 'The caravan yard outside the south gate (D-28): a fenced pocket in sight of the gate, '
                               'the stables (4611), camels, a water trough; its opening faces the gate lane.'})
    xr_plots = []
    for idx, house, angle, facing, fp in CROSS_STALLS:
        at = stall_at(angle, fp)
        xr_plots.append({'building': 'building:xr_stall', 'index': idx, 'at': at, 'facing': facing, 'kit': 'poor',
                         'house': house})
        plot_rects.append((f'xr_stall#{idx}', at, fp, facing))
    districts.append({'space': 'town:crossroads', 'polygon': TOWNS['town:crossroads'], 'plots': xr_plots,
                      'notes': "The Crossroads (A4's town Crossroads): six striped stalls (4641-4646, Caleb's workshop "
                               "the sixth) in a ring where six roads meet, a trough well in the middle."})
    for space, bid, service, house, fp, at, facing, kit in HUTS:
        districts.append({'space': space, 'polygon': TOWNS[space],
                          'plots': [{'building': bid, 'at': at, 'facing': facing, 'kit': kit, 'house': house}]})
        plot_rects.append((bid, at, fp, facing))
    for space in ['zone:cornelius_glade', 'zone:tower_knoll', 'zone:wrath_falls']:
        districts.append({'space': space, 'polygon': TOWNS[space]})
    for space, poly in ZONES.items():
        districts.append({'space': space, 'polygon': poly})
    bad = check_plots(plot_rects)
    if bad:
        raise SystemExit(f'overlapping plots: {bad}')

    points = []
    for pid, at, facing, notes in POINTS:
        p = {'id': pid, 'at': cell(at)}
        if facing:
            p['facing'] = facing
        if notes:
            p['notes'] = notes
        points.append(p)
    for i, j in enumerate(SIGNPOSTS, 1):
        at = next(p[1] for p in POINTS if p[0] == j)
        points.append({'id': 'poi:signposts', 'index': i, 'at': [int(at[0]) + 1, int(at[1]) - 1]})

    areas = []
    for aid, slot, count, poly, note in AREAS:
        areas.append({'id': aid, 'count': count, 'slot': slot, 'polygon': poly, 'notes': note})
    for aid, poly, note in KEEP_CLEAR:
        a = {'id': aid, 'kind': 'keep_clear', 'polygon': poly}
        if note:
            a['notes'] = note
        areas.append(a)
    for aid, poly, note in OPEN:
        areas.append({'id': aid, 'kind': 'open', 'polygon': poly, 'notes': note})

    return {
        'format': 0,
        'grid': 512,
        'map_cells': 128,
        'notes': 'D3 Sandcaster and the Aging Forest, MU-3 to-scale plan (A5, 2026-11-20), for the phase 3 review: '
                 'composition, scale and density only. Cells [x, y], x east, y south. Heights in map units above the '
                 'stars below the rim (0): Venom Pond 900, the River of Wrath 1,000 in its cut, the forest and fen '
                 '950-1,200, the Crossroads 1,250, Sandcaster\'s terrace 1,500 (the quarter 1,700), the Wrath hills '
                 'to 2,300, the last Gemstone crags to 3,400 in the north-west. East and south the land ends in the '
                 'world rim (x 104, y 104). Generated by output/studio_cal/d3/tools/gen_l1.py; the later L3 adds '
                 'plots\' detail, ground, scatter and structures.',
        'frame': {
            'playable': [19, 19, 90, 90],
            'edges': [
                {'side': 'west', 'span': [36, 52], 'neighbour': 'edge:west',
                 'notes': f'The caravan road runs out to x 0 at y {WEST_Y} (D2\'s east edge, the same y).'},
                {'side': 'north', 'span': [82, 94], 'neighbour': 'edge:north',
                 'notes': f'The Lakeside road runs out to y 0 at x {NORTH_X}.'},
            ],
            'rim': [
                {'side': 'east', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': f'The world rim: the land ends in a cliff at x {RIM_X}; below, water at 0 stands for the '
                          'stars; the bright face\'s glow above it (sky).'},
                {'side': 'south', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': f'The world rim: the cliff at y {RIM_Y} (D-23, as D1 and D2).'},
                {'side': 'west', 'span': [0, 32], 'form': 'ridge', 'height': [2800, 3600], 'floor': 2200,
                 'crest': 10, 'roughness': 120, 'notes': "The Gemstone Range's east end (D2's edge [0, 32])."},
                {'side': 'west', 'span': [32, 56], 'form': 'level', 'height': 1300, 'meet': 6,
                 'notes': "The caravan road's valley, open to D2 (D2's edge [32, 56] is level at 1,300)."},
                {'side': 'west', 'span': [56, 104], 'form': 'ridge', 'height': [1300, 1700], 'floor': 1100,
                 'crest': 8, 'roughness': 80, 'notes': "Wooded hills: the Howling Woods (D2's edge [56, 104])."},
                {'side': 'west', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': "The rim's west end (D2's edge [104, 128])."},
                {'side': 'north', 'span': [0, 24], 'form': 'ridge', 'height': [2600, 3400], 'floor': 2000,
                 'crest': 10, 'roughness': 120, 'notes': 'The crags go on north.'},
                {'side': 'north', 'span': [24, 82], 'form': 'ridge', 'height': [1500, 2000], 'floor': 1400,
                 'crest': 10, 'roughness': 80, 'notes': 'Dunes of the desert edge toward D5 and D4.'},
                {'side': 'north', 'span': [82, 94], 'form': 'level', 'height': 1750, 'meet': 6,
                 'notes': 'The Lakeside road to D4.'},
                {'side': 'north', 'span': [94, 104], 'form': 'ridge', 'height': [1900, 2400], 'floor': 1700,
                 'crest': 8, 'roughness': 100, 'notes': 'The Wrath hills go on north.'},
                {'side': 'north', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': "The rim's north end (D4's east rim continues it)."},
            ],
            'edge': {'height': 1500, 'west': 1300, 'south': 0, 'east': 0},
        },
        'heights': {
            'bands': bands,
            'points': [dict({'at': cell(at), 'h': h}, **({'notes': n} if n else {})) for at, h, n in HEIGHT_POINTS],
            'cliffs': CLIFFS,
            'ridges': RIDGES,
        },
        'water': {'bodies': [RIM_SEA, VENOM_POND], 'rivers': [dict(RIVER, line=[cell(q) for q in RIVER['line']])]},
        'roads': [dict({'link': link, 'line': [half(q) for q in line], 'width': width}, **({'surface': s} if s else {}))
                  for link, line, width, s in ROADS],
        'districts': districts,
        'points': points,
        'areas': areas,
        'views': VIEWS,
        'actors': [dict({'monster': m, 'at': at, 'count': c, 'spread': s, 'group': g, 'hostile': True},
                        **({'notes': n} if n else {})) for m, at, c, s, g, n in ACTORS],
    }


# ---------------------------------------------------------------- plan.yml
def building(bid, service, fp, count=1, notes=None):
    b = {'id': bid, 'type': 'house', 'service': service, 'count': count, 'doors': 1,
         'footprint_cells': fp if count > 1 else [fp]}
    if notes:
        b['notes'] = notes
    return b


PASS = {'any': [{'item': 'sandcaster_pass'}]}


def plan():
    sc_buildings = [building(bid, service, fp, notes=f'A4 house {house}.')
                    for bid, service, house, fp, at, facing, door_to, kit in SANDCASTER
                    if bid not in ('building:sc_stables',)]
    sc_buildings.append(building('building:sc_houses', 'residence', [h[1] for h in SC_HOUSES], count=len(SC_HOUSES),
                                 notes="A4 houses 4618-4640 in index order (Astra, Natasha, Madame Gloriana, the "
                                       "schools of Trade, Letters, Navigation and Tongues, the Quiet House, the "
                                       "Knife House, the Archer's House ... the Well House)."))
    wq_buildings = [building(bid, service, fp, notes=f'A4 house {house}; opens with q-d14.done.')
                    for bid, service, house, fp, at, facing, kit in QUARTER]
    wq_buildings.append(building('building:wq_houses', 'residence', [h[1] for h in QUARTER_HOUSES],
                                 count=len(QUARTER_HOUSES),
                                 notes="A4 houses 4615 Mindwright's Tower, 4616 Appraiser's Tower, 4617 Alembic Tower "
                                       "(the three Grandmasters); open with q-d14.done."))
    stables = next(s for s in SANDCASTER if s[0] == 'building:sc_stables')
    xr_buildings = [building('building:xr_stall', 'market stall', [s[4] for s in CROSS_STALLS], count=6,
                             notes="A4 houses 4641-4646 in index order: food, robes, necklaces, belts, boots, Caleb's "
                                   "Workshop (residence, Q-D15).")]
    mean = {s: (SLOTS[s - 1]['per_marker'][0] + SLOTS[s - 1]['per_marker'][1]) / 2 for s in (1, 2, 3)}
    marker_hostiles = sum(count * mean[slot] for _aid, slot, count, _p, _n in AREAS)
    placed = sum(a[2] for a in ACTORS)
    markers = sum(a[2] for a in AREAS)

    spaces = [
        # ---- the north-west: the crags, the desert edge, the city ----
        {'id': 'zone:gemstone_crags', 'name': 'The last Gemstone crags', 'kind': 'wild', 'floor': [2000, 3400],
         'relief': 'uneven', 'density': 'sparse', 'where': 'the north-west corner, beyond the playable square',
         'purpose': "Slate crags where the Gemstone Range of D2 ends; the city's backdrop."},
        {'id': 'zone:desert_edge', 'name': 'The desert edge', 'kind': 'wild', 'floor': [1400, 2400],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Dunes and thorn scrub north and east of the city, the desert of D5 beyond: the obelisk's knoll, "
                    "the caravan well, a caravan the worms swallowed; east, the west-bank hills (to 2,400) over the "
                    "river's gorge.",
         'population': [{'id': 'pop:dune_scrub', 'slot': 3, 'groups': 11, 'per_marker': [2, 3], 'levels': [30, 45],
                         'notes': 'Encounter area 1: Sand burrowers.'}]},
        {'id': 'town:sandcaster', 'name': 'Sandcaster', 'kind': 'town', 'floor': 1500,
         'where': 'north-west, on a sandstone terrace under the last crags', 'safe': True, 'keep_clear': ['spawns'],
         'density': 'dense',
         'theme': 'sandcaster kit (MM8 t07 ochre sandstone in three grades, gravel and terracotta roofs; MM6 hc pink '
                  'ashlar for the guilds and the quarter; t30 sandstone for the walls and gates).',
         'purpose': 'The wizard-ruled merchant city (WORLD_DESIGN 5.2): weapons, armour, magic, the Vulture Repellant '
                    'stall, temple, tavern, Barticus\' Gym (training to 80), three guilds, the caravans, the mirror, '
                    'Lucio\'s Jetty; the skill schools. Only pass holders get in (Q-D8).',
         'buildings': sc_buildings},
        {'id': 'zone:sc_square', 'name': 'The square', 'kind': 'zone', 'part_of': 'town:sandcaster', 'floor': 1500,
         'safe': True, 'purpose': "The mirror, Omid's deep well, the stair up to the wizard quarter."},
        {'id': 'zone:sc_north_street', 'name': 'Guild row', 'kind': 'zone', 'part_of': 'town:sandcaster',
         'floor': 1500, 'safe': True, 'purpose': 'The three guilds and the Sky Stair along the north wall.'},
        {'id': 'zone:sc_west_lane', 'name': 'The west lane', 'kind': 'zone', 'part_of': 'town:sandcaster',
         'floor': 1500, 'safe': True, 'purpose': "The temple, Barticus' Gym and the sewer grate (DD-18)."},
        {'id': 'zone:sc_main_street', 'name': 'Gate street', 'kind': 'zone', 'part_of': 'town:sandcaster',
         'floor': 1500, 'safe': True, 'purpose': 'From the south gate to the square; the tavern first inside.'},
        {'id': 'zone:sc_east_street', 'name': 'Bazaar street', 'kind': 'zone', 'part_of': 'town:sandcaster',
         'floor': 1500, 'safe': True, 'purpose': 'From the square to the east gate: the blades and the brass scale.'},
        {'id': 'zone:wizard_quarter', 'name': 'The wizard quarter', 'kind': 'district', 'part_of': 'town:sandcaster',
         'floor': 1700, 'safe': True, 'keep_clear': ['spawns'],
         'theme': 'MM6 hc pink ashlar with balconies and statue niches.',
         'purpose': "Xenoc's and Morgana's quarter: five sealed doors until q-d14.done; the guild gate into DD-19 "
                    "open from the start.",
         'buildings': wq_buildings},
        {'id': 'zone:caravan_yard', 'name': 'The caravan yard', 'kind': 'zone', 'part_of': 'town:sandcaster',
         'floor': 1300, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': 'Outside the south gate, a fenced pocket in sight of it (D-28): the caravans to Castleview and '
                    'Lakeside (no pass needed; the pass check stays at the gate).',
         'buildings': [building(stables[0], stables[1], stables[3], notes='A4 house 4611, routes 416 and 417.')]},
        # ---- the west and the middle ----
        {'id': 'zone:caravan_valley', 'name': 'The caravan valley', 'kind': 'wild', 'floor': [1250, 1400],
         'relief': 'slope', 'density': 'sparse',
         'purpose': "The dry valley the caravan road comes down from D2, under the city's terrace; sand burrowers "
                    "outside the walls (F10).",
         'population': [{'id': 'pop:outside_walls', 'slot': 3, 'groups': 2, 'per_marker': [2, 3], 'levels': [30, 45],
                         'notes': 'Encounter area 5 (F10): Sand burrowers outside the walls.'}]},
        {'id': 'zone:crossroads_plain', 'name': 'The Crossroads plain', 'kind': 'wild', 'floor': [1200, 1350],
         'relief': 'flat', 'density': 'sparse', 'purpose': 'Open ground round the market where six roads meet.',
         'population': [{'id': 'pop:forest_edge', 'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [22, 38],
                         'notes': "Encounter area 6 (F10): Mantis ants at the Aging Forest's east edge."}]},
        {'id': 'town:crossroads', 'name': 'The Crossroads', 'kind': 'town', 'floor': 1250, 'safe': True,
         'keep_clear': ['spawns'], 'density': 'medium',
         'theme': 'MM6 striped market tents on sandstone footings, flagstones in the ring.',
         'purpose': 'An open-air market (WORLD_DESIGN 5.2): food, robes, necklaces, belts, boots, Caleb the '
                    'inventor (Q-D15).',
         'buildings': xr_buildings},
        {'id': 'zone:celia_yard', 'name': "Celia and Derek's yard", 'kind': 'district',
         'part_of': 'zone:crossroads_plain', 'floor': 1220, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "Their cottage on the Venom road by the Crossroads (A3's q-c22.cottage): shut until Q-C22 is "
                    "done, then Celia and Derek live there.",
         'buildings': [building('building:celia_derek_cottage', "Celia and Derek's Cottage", [1.5, 1.5],
                                notes='A4 house 4647.')]},
        {'id': 'zone:howling_woods', 'name': 'The Howling Woods', 'kind': 'wild', 'floor': [1200, 2200],
         'relief': 'uneven', 'density': 'dense',
         'purpose': "Dark old wood on the Howling ridge (1,900-2,200, D-28) toward D2; the wind howls through a hollow standing stone (no "
                    "wolves); mantis ants and their mound; a smugglers' rope over the south rim.",
         'population': [{'id': 'pop:howling_woods', 'slot': 1, 'groups': 12, 'per_marker': [2, 3],
                         'levels': [22, 38], 'notes': 'Encounter area 3: Mantis ants.'}]},
        {'id': 'zone:aging_forest', 'name': 'The Aging Forest', 'kind': 'wild', 'floor': [1050, 1200],
         'relief': 'uneven', 'density': 'dense',
         'purpose': "Old broad trees in red and gold whose leaves fall all year; the great oak, Cornelius's glade, a "
                    "forbidden fruit hut, a skeleton in a young man's clothes, the edge cairn on the south rim. Quiet "
                    "but for three hell hornet nests.",
         'population': [{'id': 'pop:hornet_nests', 'actor': 'Xeen Hornet', 'groups': 3, 'placed': True,
                         'hostile': True,
                         'notes': 'Three nests, each five Hell Hornets 35 and a Hornet Swarm 42 (18 at load).'}]},
        {'id': 'zone:cornelius_glade', 'name': "Cornelius's glade", 'kind': 'zone', 'part_of': 'zone:aging_forest',
         'floor': 1120, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': 'Cornelius the Leprechaun (5247) on a stump: Perception Master (outdoor teacher).'},
        # ---- the north-east and the east ----
        {'id': 'zone:wrath_hills', 'name': 'The Wrath hills', 'kind': 'wild', 'floor': [1500, 3400],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Stony hills east of the river's gorge under the broken Wrath crest (3,100-3,400, D-28), up to "
                    "the east rim: the Wrath Spring at the gorge head, the Lakeside road over its saddle (1,850), the "
                    "Eastern Tower on its knoll. The mantis ants keep to the walkable shoulders.",
         'population': [{'id': 'pop:wrath_hills', 'slot': 1, 'groups': 12, 'per_marker': [2, 3], 'levels': [22, 38],
                         'notes': 'Encounter area 2: Mantis ants.'}]},
        {'id': 'zone:tower_knoll', 'name': "The Eastern Tower's knoll", 'kind': 'zone', 'part_of': 'zone:wrath_hills',
         'floor': 1950, 'purpose': 'The Great Eastern Tower (DD-07) by the rim: a tall dark tower, its door locked.'},
        {'id': 'zone:river_meadows', 'name': 'The river meadows', 'kind': 'wild', 'floor': [1000, 1250],
         'relief': 'slope', 'density': 'sparse',
         'purpose': "Grass on both banks of the lower river: Wrath Bridge, the fruit hut on the south bank, a "
                    "wayside shrine, the Rim Watch over the falls."},
        {'id': 'zone:wrath_falls', 'name': 'The Wrath Falls', 'kind': 'zone', 'part_of': 'zone:river_meadows',
         'floor': [1000, 1150], 'purpose': 'The river drops off the east rim into the stars; the glow above.'},
        # ---- the south-east ----
        {'id': 'zone:venom_fen', 'name': 'Venom Pond and the fen', 'kind': 'wild', 'floor': [900, 1050],
         'relief': 'flat', 'density': 'medium',
         'purpose': "A green pond and reed fen running to the rims' corner: Thaddeus's hut and his fountain, a "
                    "drowned skiff, the Fountain of Great Protection; cobras.",
         'population': [{'id': 'pop:venom_fen', 'slot': 2, 'groups': 12, 'per_marker': [2, 3], 'levels': [30, 45],
                         'notes': 'Encounter area 4: Cobras.'}]},
        {'id': 'zone:thaddeus_yard', 'name': "Thaddeus's yard", 'kind': 'district', 'part_of': 'zone:venom_fen',
         'floor': 960, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "Thaddeus the fountain keeper (Q-D18, Q-D19) and the Fountain of Youth by Venom Pond.",
         'buildings': [building('building:thaddeus_hut', "The Fountain Keeper's Hut", [1.5, 1.5],
                                notes='A4 house 4648.')]},
        {'id': 'zone:rim', 'name': 'The world rim', 'kind': 'wild', 'floor': 0, 'empty': True,
         'purpose': 'East and south the land ends in a cliff; below, the stars (water at 0 stands for them).'},
        {'id': 'water:rim_sea', 'name': 'Below the rim', 'kind': 'water', 'purpose': 'The stars below the edge.'},
        {'id': 'water:wrath', 'name': 'The River of Wrath', 'kind': 'water',
         'purpose': 'From the Wrath Spring south in its cut, under Wrath Bridge, east over the rim at the falls.'},
        {'id': 'water:venom_pond', 'name': 'Venom Pond', 'kind': 'water', 'part_of': 'zone:venom_fen',
         'purpose': 'Still green water and reeds.'},
        # ---- junctions and edges ----
        {'id': 'junction:gate_fork', 'name': 'Gate fork', 'kind': 'junction', 'signpost': True,
         'purpose': "The south gate's lane off the caravan road."},
        {'id': 'junction:crossroads', 'name': 'The Crossroads', 'kind': 'junction', 'signpost': True,
         'purpose': 'Six roads: west to D2, north-west to Sandcaster, north to the dunes, east to Wrath Bridge, '
                    'south-east to Venom Pond, south into the Aging Forest.'},
        {'id': 'junction:east_fork', 'name': 'East fork', 'kind': 'junction', 'signpost': True,
         'purpose': 'Lakeside north, the Eastern Tower, the falls.'},
        {'id': 'junction:venom_fork', 'name': 'Venom fork', 'kind': 'junction', 'signpost': True,
         'purpose': "Thaddeus's hut, the fen track to the Fountain of Great Protection."},
        {'id': 'junction:forest_fork', 'name': 'Forest fork', 'kind': 'junction', 'signpost': True,
         'purpose': 'The Howling Woods west, the south rim.'},
        {'id': 'edge:west_end', 'name': 'West edge (D2)', 'kind': 'road', 'part_of': 'zone:caravan_valley',
         'purpose': 'Where the caravan road leaves for D2.'},
        {'id': 'edge:north_end', 'name': 'North edge (D4)', 'kind': 'road', 'part_of': 'zone:wrath_hills',
         'purpose': 'Where the Lakeside road leaves for D4.'},
    ]
    links = [
        {'id': 'link:caravan_road', 'from': 'edge:west_end', 'to': 'junction:crossroads', 'kind': 'road',
         'purpose': 'travel: D2', 'notes': 'by the gate fork and Vespar\'s ruin'},
        {'id': 'link:gate_lane', 'from': 'junction:gate_fork', 'to': 'zone:caravan_yard', 'kind': 'road',
         'notes': "the caravan yard, then the south gate (the pass)"},
        {'id': 'link:city_road', 'from': 'town:sandcaster', 'to': 'junction:crossroads', 'kind': 'road',
         'notes': 'from the east gate'},
        {'id': 'link:dune_track', 'from': 'junction:crossroads', 'to': 'zone:desert_edge', 'kind': 'path',
         'notes': 'to the caravan well and the swallowed caravan'},
        {'id': 'link:obelisk_path', 'from': 'link:city_road', 'to': 'zone:desert_edge', 'kind': 'path',
         'notes': "up the obelisk's knoll"},
        {'id': 'link:bridge_road', 'from': 'junction:crossroads', 'to': 'junction:east_fork', 'kind': 'road',
         'crosses': ['water:wrath'], 'features': ['Wrath Bridge: one stone arch over the river\'s cut at x 74-77']},
        {'id': 'link:lakeside_road', 'from': 'junction:east_fork', 'to': 'edge:north_end', 'kind': 'road',
         'purpose': 'travel: D4', 'rise': 500},
        {'id': 'link:tower_lane', 'from': 'junction:east_fork', 'to': 'zone:tower_knoll', 'kind': 'path'},
        {'id': 'link:spring_path', 'from': 'link:lakeside_road', 'to': 'zone:wrath_hills', 'kind': 'path',
         'notes': 'down into the gorge head to the Wrath Spring'},
        {'id': 'link:high_path', 'from': 'link:lakeside_road', 'to': 'zone:wrath_hills', 'kind': 'path',
         'notes': "from the Lakeside saddle east up the crest's north shoulder (D-28)"},
        {'id': 'link:rim_track', 'from': 'junction:east_fork', 'to': 'zone:wrath_falls', 'kind': 'path',
         'notes': 'along the north bank to the Rim Watch'},
        {'id': 'link:venom_road', 'from': 'junction:crossroads', 'to': 'zone:thaddeus_yard', 'kind': 'road',
         'notes': "past Celia and Derek's cottage and the wayside shrine"},
        {'id': 'link:orchard_path', 'from': 'junction:venom_fork', 'to': 'zone:river_meadows', 'kind': 'path',
         'notes': "along the river's south bank to the fruit hut"},
        {'id': 'link:fen_track', 'from': 'junction:venom_fork', 'to': 'zone:venom_fen', 'kind': 'path',
         'notes': 'to the Fountain of Great Protection'},
        {'id': 'link:forest_road', 'from': 'junction:crossroads', 'to': 'zone:aging_forest', 'kind': 'road',
         'notes': "past the great oak and Cornelius's glade to the edge cairn"},
        {'id': 'link:howling_track', 'from': 'junction:forest_fork', 'to': 'zone:howling_woods', 'kind': 'path',
         'notes': "past the howling stone to the smugglers' rope"},
        {'id': 'link:oak_lane', 'from': 'link:forest_road', 'to': 'zone:aging_forest', 'kind': 'path',
         'notes': 'D-28: a short lane east from the forest road to the great oak and its nest'},
    ]
    entrances = [
        {'id': 'entrance:west_road', 'space': 'edge:west_end', 'kind': 'both', 'neighbour': 'edge:west',
         'facing': 'e', 'how': "The caravan road down from D2's Ogre Pass mouth."},
        {'id': 'entrance:north_road', 'space': 'edge:north_end', 'kind': 'both', 'neighbour': 'edge:north',
         'facing': 's', 'how': 'The Lakeside road from D4.'},
        {'id': 'entrance:sandcaster_square', 'space': 'zone:sc_square', 'kind': 'arrival',
         'how': 'Town Portal and the mirror (4612, qbit 119009).'},
        {'id': 'entrance:sandcaster_stables', 'space': 'zone:caravan_yard', 'kind': 'arrival',
         'neighbours': ['stable:sandcaster_castleview', 'stable:sandcaster_lakeside'],
         'how': "The caravan yard outside the south gate."},
        {'id': 'entrance:south_gate', 'space': 'town:sandcaster', 'kind': 'both', 'facing': 'n', 'condition': PASS,
         'how': "The south gate: A3's q-d8.sandcaster_gate wants the Sandcaster Pass from outside (\"The gate guards "
                "want a pass. Wizards' orders.\"); from inside it always opens."},
        {'id': 'entrance:east_gate', 'space': 'town:sandcaster', 'kind': 'both', 'facing': 'w', 'condition': PASS,
         'how': 'The east gate onto the Crossroads road: the same pass check.'},
        {'id': 'entrance:dd18_shaft', 'space': 'zone:sc_west_lane', 'kind': 'both', 'neighbour': 'door:dd18',
         'facing': 'n', 'how': "D-27: a street shaft with an iron lid against the gym's south-east corner, under "
                               "Barticus' sign; the entrance preset (D-24: \"Descend to the sewer?\"), no question of "
                               "its own; 900 from the gym door, off the walking line between the door and the lane."},
        {'id': 'entrance:dd19_gate', 'space': 'zone:wizard_quarter', 'kind': 'both', 'neighbour': 'door:dd19',
         'facing': 'n', 'how': "The guild gate in the quarter's back wall: A3's q-d14.quarter_gate (\"Enter?\")."},
        {'id': 'entrance:dd07_door', 'space': 'zone:tower_knoll', 'kind': 'both', 'neighbour': 'door:dd07',
         'facing': 'w', 'condition': {'item': 'east_tower_key'},
         'how': "The Eastern Tower's door: A3's q-d18.tower_door (\"A tower door with no handle and a very smug "
                "lock.\" without the key)."},
    ]
    pois = [
        {'id': 'poi:obelisk', 'space': 'zone:desert_edge', 'kind': 'obelisk', 'rule': 'native:obelisk',
         'behaviour': "The Darkside's third obelisk (A3's obelisks.d3: THE).",
         'notes': 'On a dune knoll outside the east gate, the city in view.'},
        {'id': 'poi:sc_mirror', 'space': 'zone:sc_square', 'kind': 'mirror',
         'behaviour': 'The Mirror of Sandcaster (A4 4612, thing:sc_mirror, qbit 119009): the Town Portal anchor.'},
        {'id': 'poi:sc_well', 'space': 'zone:sc_square', 'kind': 'well',
         'behaviour': "Omid's deep well (\"something at the bottom hums\"): +Intellect, temporary.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:market_well', 'space': 'town:crossroads', 'kind': 'well',
         'behaviour': "The Crossroads' trough well: \"Refreshing!\" (a plain well)."},
        {'id': 'poi:cornelius', 'space': 'zone:cornelius_glade', 'kind': 'teacher',
         'behaviour': 'Cornelius the Leprechaun (5247): Perception Master, outdoors (teachers_plan cornelius); '
                      "\"Spotting secret doors is an art ...\"."},
        {'id': 'poi:vespar_ruin', 'space': 'zone:aging_forest', 'kind': 'ruin',
         'behaviour': "A roadside ruin by the caravan road (A3's q-d8.handle): \"You found an emerald handle.\" once; "
                      "then \"Rubble, and nothing green in it.\""},
        {'id': 'poi:fountain_youth', 'space': 'zone:thaddeus_yard', 'kind': 'fountain',
         'behaviour': "The Fountain of Youth (A3's q-d18.fountain): venom before q-d18.done (the map's own poison), "
                      "then it removes unnatural aging (the permanent device of the quest)."},
        {'id': 'poi:fountain_protection', 'space': 'zone:venom_fen', 'kind': 'fountain',
         'behaviour': 'The Fountain of Great Protection (source F4: +AC): +AC, temporary, daily.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:fruit_hut_river', 'space': 'zone:river_meadows', 'kind': 'shrine',
         'behaviour': "The pear hut (source F3, D-28): a whitewashed mud hut under an old pear tree on the river's "
                      "south bank, a basket of pears on the sill: \"The pear of plenty. You feel stronger, and then "
                      "very tired.\" +2 Might, permanent, and Weak; once per character (A2's boon, a player bit).",
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:fruit_hut_forest', 'space': 'zone:aging_forest', 'kind': 'shrine',
         'behaviour': "The fig hut (source E4, D-28): a mossy log hut in the roots of a fig tree, figs in a bowl by "
                      "the door: \"The fig of foresight. You see everything. Everything sees you.\" +2 Intellect, "
                      "permanent, and Insane; once per character (A2's boon, a player bit).",
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:wrath_spring', 'space': 'zone:wrath_hills', 'kind': 'well',
         'behaviour': "The Wrath Spring, where the river bursts from a cave: +Might, temporary (\"The water is "
                      "angry. So, briefly, are you.\").", 'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:rim_watch', 'space': 'zone:wrath_falls', 'kind': 'chest',
         'behaviour': "A ruined watch post on the bluff over the falls: the rim view east (the bright face's glow); "
                      "the watchman's locker (a chest)."},
        {'id': 'poi:howling_stone', 'space': 'zone:howling_woods', 'kind': 'sign',
         'behaviour': "A hollow standing stone the wind sings through: \"It is only the wind. The wolves left years "
                      "ago. Probably.\""},
        {'id': 'poi:edge_cairn', 'space': 'zone:aging_forest', 'kind': 'device',
         'behaviour': 'A pilgrims\' cairn at the south rim: add a stone, +Luck, temporary.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:caravan_well', 'space': 'zone:desert_edge', 'kind': 'well',
         'behaviour': "The caravan well in the dunes: +Endurance, temporary.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:great_oak', 'space': 'zone:aging_forest', 'kind': 'device',
         'behaviour': "The great oak, hollow and ancient, off the forest road by a short lane (D-28: about 2,900 east "
                      "of the road); a hornet nest in its crown. Rest a hand on it: +Personality, "
                      "temporary (\"You feel older and wiser. Mostly older.\").",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:wayside_shrine', 'space': 'zone:river_meadows', 'kind': 'shrine',
         'behaviour': 'A wayside shrine of the desert sun on the Venom road: +Fire resistance, temporary.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:caravan_wreck', 'space': 'zone:desert_edge', 'kind': 'chest',
         'behaviour': 'A caravan half swallowed by the dunes, a worm hole beside it: its strongbox (a chest).'},
        {'id': 'poi:mantis_mound', 'space': 'zone:howling_woods', 'kind': 'chest',
         'behaviour': "A mantis ants' mound: an explorer's pack in the spoil heap (a chest)."},
        {'id': 'poi:aged_skeleton', 'space': 'zone:aging_forest', 'kind': 'chest',
         'behaviour': "A skeleton in a young man's clothes under the falling leaves: his satchel (a chest); a note: "
                      "\"Just a nap.\""},
        {'id': 'poi:drowned_skiff', 'space': 'zone:venom_fen', 'kind': 'chest',
         'behaviour': "A skiff sunk in the reeds of Venom Pond's south shore: its locker (a chest)."},
        {'id': 'poi:tower_cart', 'space': 'zone:tower_knoll', 'kind': 'chest',
         'behaviour': "The tower mages' supply cart, overturned at the foot of the knoll: a crate (a chest)."},
        {'id': 'poi:smugglers_rope', 'space': 'zone:howling_woods', 'kind': 'chest',
         'behaviour': "A rope tied to a stake runs over the south rim into nothing; a bundle at the top (a chest): "
                      "\"Someone meant to come back.\""},
        {'id': 'poi:fallen_courier', 'space': 'zone:wrath_hills', 'kind': 'chest',
         'behaviour': "A courier from Lakeside who took the high path round Wrathtop and never came down: his "
                      "satchel (a chest), on the crest's north shoulder with the rim view."},
        {'id': 'poi:signposts', 'spaces': SIGNPOSTS, 'kind': 'signpost', 'count': 5,
         'behaviour': 'Signposts at the forks.'},
    ]
    landmarks = [
        {'id': 'landmark:sandcaster', 'space': 'town:sandcaster',
         'what': 'Ochre sandstone walls and towers on a terrace, the pink wizard towers above',
         'seen_from': ['zone:caravan_valley', 'zone:crossroads_plain', 'zone:desert_edge', 'edge:west_end']},
        {'id': 'landmark:sky_stair', 'space': 'zone:sc_north_street',
         'what': "The Sky Stair: the city's tallest tower with a timber jetty sticking out of its top into the air",
         'seen_from': ['zone:caravan_valley', 'zone:crossroads_plain', 'zone:desert_edge']},
        {'id': 'landmark:eastern_tower', 'space': 'zone:tower_knoll',
         'what': 'A tall dark tower on a knoll at the very edge of the world',
         'seen_from': ['zone:river_meadows', 'zone:crossroads_plain', 'zone:wrath_hills']},
        {'id': 'landmark:wrath_falls', 'space': 'zone:wrath_falls',
         'what': 'The River of Wrath dropping off the rim into the stars',
         'seen_from': ['zone:river_meadows', 'zone:venom_fen']},
        {'id': 'landmark:rim_glow', 'space': 'zone:rim',
         'what': "The bright face's glow standing above the east rim: a pale gold band in the eastern sky",
         'seen_from': ['zone:river_meadows', 'zone:crossroads_plain', 'zone:venom_fen', 'edge:west_end']},
        {'id': 'landmark:gemstone_crags', 'space': 'zone:gemstone_crags',
         'what': 'The last slate crags of the Gemstone Range behind the city',
         'seen_from': ['zone:crossroads_plain', 'zone:caravan_valley']},
    ]
    sightlines = [
        {'id': 'view:arrival', 'from': 'entrance:west_road',
         'to': ['landmark:sandcaster', 'landmark:sky_stair', 'town:crossroads', 'landmark:rim_glow'],
         'what': "Arrival from D2: the dry valley, Sandcaster on its terrace on the left, the Crossroads' awnings "
                 "ahead, the woods on the right, the glow above the rim far east."},
        {'id': 'view:signature', 'from': 'zone:river_meadows',
         'to': ['landmark:wrath_falls', 'landmark:rim_glow', 'landmark:eastern_tower'],
         'what': "The signature view: the River of Wrath running east over the rim into the stars, the bright "
                 "face's glow above, the Eastern Tower at the edge."},
    ]
    states = [
        {'id': 'state:gates_shut', 'condition': {'not': PASS},
         'locks': ['entrance:south_gate', 'entrance:east_gate'],
         'atmosphere': "Guards in the gate arches; A3's fail text \"The gate guards want a pass. Wizards' orders.\"",
         'notes': 'From inside (Town Portal, the mirror) the gates always open.'},
        {'id': 'state:quarter_sealed', 'condition': {'not': {'qbit': 'quarter_open'}},
         'locks': ['building:wq_guild_dark', 'building:wq_magic', 'building:wq_houses'],
         'atmosphere': "Wizard locks glowing on the doors; A4's closed texts (\"The wizards are sensitive to insults; "
                       "best not to knock twice.\")."},
        {'id': 'state:quarter_open', 'condition': {'qbit': 'quarter_open'},
         'opens': ['building:wq_guild_dark', 'building:wq_magic', 'building:wq_houses']},
        {'id': 'state:jetty_closed', 'condition': {'not': {'qbit': 'lucio_open'}},
         'locks': ['building:sc_lucio_jetty'],
         'atmosphere': "A jetty that ends in thin air. A sign: \"Celestial boats. Chosen Ones only.\" (A4's closed "
                       "text)"},
        {'id': 'state:jetty_open', 'condition': {'qbit': 'lucio_open'}, 'opens': ['building:sc_lucio_jetty'],
         'effects': ["Lucio's boat at the jetty's end twice a week (tue, fri); it departs only (D-28)."]},
        {'id': 'state:cottage_shut', 'condition': {'not': {'qbit': 'celia_moved'}},
         'locks': ['building:celia_derek_cottage'],
         'notes': "A3's q-c22.cottage: the door refuses until q-c22.done, then moves Celia (4041) and Derek (4046) "
                  "in and sets q-c22.moved."},
        {'id': 'state:fountain_venom', 'condition': {'not': {'qbit': 'fountain_restored'}},
         'atmosphere': 'The Fountain of Youth runs green; the jewel socket on its spout is empty.'},
    ]
    totals = {
        'hostiles_at_load': int(marker_hostiles + placed),
        'encounter_areas': len(AREAS),
        'spawn_markers': markers,
        'outdoor_chests': sum(1 for p in pois if p['kind'] == 'chest'),
        'points_of_interest': 0,      # filled in by run.sh from render_d3.py's census (figures.json)
        'dungeon_entrances': 3,
    }
    return {
        'format': 0,
        'level': 'L1',
        'pitch': "The Darkside's south-east corner: a sandstone merchant city at the desert's edge under the last "
                 "Gemstone crags, the open market where six roads meet, and south of them the Aging Forest, whose "
                 "red and gold leaves fall all year. The River of Wrath bursts from a cave in the eastern hills, "
                 "runs south in its cut and turns east to fall off the edge of the world; above the east rim stands "
                 "the glow of the bright face. Venom Pond lies in the fen of the south-east, and on a knoll at the "
                 "very edge the Great Eastern Tower.",
        'purpose': "Act III's town map (party 27-30): Sandcaster behind its pass (Q-D8: the emerald handle in the "
                   "ruin, the gate), Natasha's bridle (M25), Astra's quarter (Q-D14, DD-19, Act IV), Barticus' Gym "
                   "and the sewer (DD-18), Thaddeus and the Fountain of Youth (Q-D18 with the Eastern Tower DD-07, "
                   "Act IV; Q-D19), Caleb at the Crossroads (Q-D15), Celia and Derek (Q-C22), Cornelius, the skill "
                   "schools, training to 80, Lucio's Jetty after M30.",
        'mood': "Warm sandstone and dusty olive scrub under the amber Darkside sky; a busy market; the Aging "
                "Forest's red-gold leaves falling in still air; the hiss of the fen; the river's roar at the falls "
                "and the pale glow beyond the rim.",
        'datum': 'water:rim_sea',
        'spaces': spaces,
        'links': links,
        'entrances': entrances,
        'critical_path': ['edge:west_end', 'junction:gate_fork', 'zone:caravan_yard', 'town:sandcaster',
                          'zone:sc_square'],
        'goals': [
            {'id': 'goal:handle', 'space': 'zone:aging_forest', 'kind': 'use',
             'what': "Find Vespar's emerald handle in the roadside ruin (Q-D8).", 'story': 'Q-D8'},
            {'id': 'goal:city', 'space': 'town:sandcaster', 'kind': 'reach',
             'what': 'Enter Sandcaster with the pass (Q-D8); Natasha enchants the bridle (M25).', 'story': 'M25'},
            {'id': 'goal:quarter', 'space': 'zone:wizard_quarter', 'kind': 'reach',
             'what': "Through the guild gate into DD-19; Astra's quest (Q-D14) opens the quarter.", 'story': 'Q-D14'},
            {'id': 'goal:jewel', 'space': 'zone:tower_knoll', 'kind': 'reach',
             'what': "Open the Eastern Tower with Q-D19's key; bring Thaddeus the Jewel of Ages (Q-D18).",
             'story': 'Q-D18'},
            {'id': 'goal:caleb', 'space': 'town:crossroads', 'kind': 'use',
             'what': "Bring Caleb his magnifying glass from the gargoyles of D4 (Q-D15).", 'story': 'Q-D15'},
            {'id': 'goal:celia', 'space': 'zone:celia_yard', 'kind': 'reach',
             'what': "Visit Celia and Derek in their Darkside cottage after Q-C22.", 'story': 'Q-C22'},
        ],
        'points_of_interest': pois,
        'landmarks': landmarks,
        'sightlines': sightlines,
        'states': states,
        'height_bands': [
            {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
            {'id': 'band:fen', 'range': [864, 1050], 'spaces': ['zone:venom_fen', 'water:venom_pond']},
            {'id': 'band:low', 'range': [1000, 1250],
             'spaces': ['zone:aging_forest', 'zone:river_meadows', 'water:wrath']},
            {'id': 'band:plain', 'range': [1200, 1400],
             'spaces': ['zone:caravan_valley', 'zone:crossroads_plain', 'town:crossroads']},
            {'id': 'band:mid', 'range': [1300, 2400], 'spaces': ['zone:desert_edge', 'town:sandcaster']},
            {'id': 'band:ridge', 'range': [1200, 2200], 'spaces': ['zone:howling_woods']},
            {'id': 'band:high', 'range': [1000, 3400], 'spaces': ['zone:wrath_hills']},
            {'id': 'band:peaks', 'range': [2000, 3400], 'spaces': ['zone:gemstone_crags']},
        ],
        'landform': {
            'relief': "A dry valley (1,300) from D2 under Sandcaster's terrace (1,500, the quarter 1,700) and the last "
                      "Gemstone crags (to 3,400); dunes to 1,900 north of the city and the west-bank hills (2,400) "
                      "over the river's gorge; the Crossroads plain (1,250); east of the river the broken Wrath "
                      "crest (3,100-3,400) with the Lakeside saddle (1,850) on the D4 road; the Howling ridge "
                      "(1,900-2,200) in the south-west; the Aging Forest and the fen falling to 864 at Venom Pond; "
                      "the rim cliff along the east and south. D-28: the range inside the playable box is about "
                      "2,500 (864-3,400).",
            'height_range': [864, 3400],
            'water': 'The River of Wrath (about 2.5 cells wide, 80 cells long, in a cut 300-700 deep above the '
                     'bridge), Venom Pond (about 100 cells).',
            'water_share': 0.03,
            'caps': [{'kind': 'bare rock', 'share': 0.06, 'where': 'the crags, the river\'s cut, the rim cliffs'},
                     {'kind': 'sand', 'share': 0.12, 'where': 'the desert edge and the caravan valley'}],
            'rim': {'notes': 'The world rim along the whole east (x 104) and south (y 104): a cliff of about 1,000 '
                             'down to the stars; the River of Wrath falls over it at y 64. West and north the land '
                             'runs to the map edge; the roads run out to it.'},
        },
        'atmosphere': "Sky xeendark1 (xeen_darkside_day; A3's Lua switches to xeendark2/3 at M17/M27); no weather; "
                      "music 39. Market bustle and camels at the Crossroads; wind in the scrub; the Howling Woods' "
                      "stone moaning; leaves and insects in the Aging Forest (falling leaves: a particle gap, MU-2); "
                      "frogs and hiss at Venom Pond; the falls' roar near the rim.",
        'sketch': {'file': 'sketch.yml', 'grid': 512},
        'totals': totals,
        'notes': 'MU-3 for the phase 3 review (A5, 2026-11-20). Source geography: Darkside E3, E4, F3, F4 (MAPS D3). '
                 'Drawing and review board: output/studio_cal/d3/mockups/. Generated by '
                 'output/studio_cal/d3/tools/gen_l1.py.',
    }


class Dumper(yaml.SafeDumper):
    pass


def _list(dumper, data):
    flat = all(not isinstance(v, (list, dict)) for v in data)
    pairs = all(isinstance(v, list) and all(not isinstance(w, (list, dict)) for w in v) for v in data) and data
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=bool(flat or pairs))


Dumper.add_representer(list, _list)


def write(name, data):
    (OUT / name).write_text(yaml.dump(data, Dumper=Dumper, sort_keys=False, width=118, allow_unicode=True))


def main(poi_count=None):
    OUT.mkdir(parents=True, exist_ok=True)
    p = plan()
    if poi_count is not None:
        p['totals']['points_of_interest'] = poi_count
    write('project.yml', PROJECT)
    write('plan.yml', p)
    write('sketch.yml', sketch())
    print('written', OUT)


if __name__ == '__main__':
    import json
    import sys
    fig = pathlib.Path(_REPO_ROOT, 'output/studio_cal/d3') / 'mockups/figures.json'
    count = None
    if '--with-census' in sys.argv and fig.exists():
        count = json.loads(fig.read_text())['poi_count']
    main(count)
