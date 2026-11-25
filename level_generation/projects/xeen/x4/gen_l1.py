#!/usr/bin/env python3
"""X4 Burlock Savannah: the L1 brief (MU-3 plan) for gate G1 (A5, 2026-11-20).

    gen_l1.py      writes devdocs/xeen/briefs/x4/L1/{project,plan,sketch}.yml

Then `oymap fmt` and `oymap validate --assets assets_dev` (run.sh does all three and the drawings). Later passes edit
this script, not the YAML. Cells are [x, y] on the 128-cell grid (512 units), x east, y south.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'devdocs/xeen/briefs/x4/L1'

# ---------------------------------------------------------------- the edges and crossings
SOUTH_X3_X = 36      # the Asp road to X3 Lifeforce Lagoon (west half of the south edge)
RIVER_OUT_X = 79     # the river leaves for X2 (X2's north_river enters at its x 30: the west part of X2's north edge)
SOUTH_X2_X = 96      # the Rivercity road (X2's north road reaches its edge at x 67, in its 58-74 level span)
WEST_Y = 60          # the desert road to X6
EAST_Y = 66          # the Firestone road to X7
RIM_Y = 24           # the north rim: the Gargoyle Range ends in a cliff, the stars below


def flow(seq):
    return seq


# ---------------------------------------------------------------- project.yml
SLOTS = [
    {'monster': 'Xeen Knight', 'tier': 1, 'per_marker': [2, 3], 'weight': 27},
    {'monster': 'Xeen Ogre', 'tier': 0, 'per_marker': [2, 3], 'weight': 33},
    {'monster': 'Xeen Gargoyle', 'tier': 1, 'per_marker': [2, 4], 'weight': 40},
]

PROJECT = {
    'format': 0,
    'id': 'xeen_x4',
    'name': 'Burlock Savannah',
    'world': 'xeen',
    'kind': 'outdoor',
    'profile': 'odm',
    'map_code': 'X4',
    'units': {'plan_grid': 512},
    'extent': {'terrain_cells': 128},
    'map_stats': {
        'id': 9102,
        'continent': 6,
        'encounter_chance': 10,
        'treasure_level': 2,
        'trap_dice': 2,
        'perception_difficulty': 4,
        'refill_days': 672,
        'music': 29,
        'environment': 'plains',
        'lock_difficulty': 4,
        'slots': SLOTS,
    },
    'neighbours': [
        {'id': 'edge:south_x2', 'to': 'xeen_x2.odm', 'kind': 'edge', 'side': 'south', 'days': 5,
         'arrival_side': 'north',
         'approach': f'The Rivercity road up from the south edge at x {SOUTH_X2_X}, east of the river.',
         'notes': 'X2 Rivercity: the main arrival. D-11.6: the south edge east of x 64 (the river included) leads '
                  'to X2. On X2 the north road reaches its edge at x 67 (its level span 58-74), sealed today by the '
                  '"bridge out" sign at [67.1, 20.6]; X2 opens it when X4 is built.'},
        {'id': 'edge:south_x3', 'to': 'xeen_x3.odm', 'kind': 'edge', 'side': 'south', 'days': 5,
         'arrival_side': 'north',
         'approach': f'The Asp road up from the south edge at x {SOUTH_X3_X} (the west half).',
         'notes': "D-11.6: X4's south edge west of x 64 leads to X3's north arrival on its road at x 50 (X3's "
                  "DOORS.md); X3's north edge leads back to this x 36 arrival. Neither road moves."},
        {'id': 'edge:west', 'to': 'xeen_x6.odm', 'kind': 'edge', 'side': 'west', 'days': 7, 'arrival_side': 'east',
         'approach': f'The desert road in from the west edge at y {WEST_Y}, under the range foot.',
         'notes': 'X6 Desert of the Sphinx (a wilderness edge, 7 days); not built: plan crossing only.'},
        {'id': 'edge:east', 'to': 'xeen_x7.odm', 'kind': 'edge', 'side': 'east', 'days': 5, 'arrival_side': 'west',
         'approach': f'The Firestone road in from the east edge at y {EAST_Y}, south of the lava fields.',
         'notes': 'X7 Mount Firestone (trap and endgame); not built: plan crossing only.'},
        {'id': 'door:xd07', 'to': 'xeen_xd07.blv', 'kind': 'door',
         'arrival_hint': "Inside Castle Burlock's gate, before the Crusaders' portcullis.",
         'notes': "XD-07 Castle Burlock (A7): the castle's south gate above the village square. The village outside "
                  "needs no title; the portcullis inside does (m4.done)."},
        {'id': 'fall:xd07_throne', 'to': 'xeen_xd07.blv', 'kind': 'fall', 'one_way': True,
         'arrival_hint': "In the air beside the castle's west tower, outside the walls, about 1,000 above the ground.",
         'notes': "D-4 (XD-07 5): the old throne throws the party out of the castle; they land on X4 by the west "
                  "tower with ordinary fall damage. A fall, not a door."},
        {'id': 'door:xd25', 'to': 'xeen_xd25.blv', 'kind': 'door',
         'arrival_hint': "At the foot of the undercroft stair under Asp's square.",
         'notes': "XD-25 Asp Undercroft (Q-C5, Q-C11): a cellar stair on Asp's square beside the rule stone, open "
                  "from day one; the field of light inside drops with the pedestals' qbit."},
        {'id': 'door:xd26', 'to': 'xeen_xd26.blv', 'kind': 'door',
         'arrival_hint': 'At the bottom of the eyrie shaft, facing in.',
         'notes': "XD-26 Gargoyle Eyrie (Q-C10): a cave mouth high on Gargoyle Peak's south face, up the eyrie path "
                  "past Carlawna's hut."},
        {'id': 'door:xd26_sky_crack', 'to': 'xeen_xd26.blv', 'kind': 'door', 'one_way': True,
         'arrival_hint': 'On the sky-crack ledge high on Gargoyle Peak (about 3,300), the eyrie below.',
         'notes': "XD-26's sky crack: a one-way exit onto a ledge on the same peak (D-4); down by the ledge's "
                  "goat path to the eyrie mouth, or a fall."},
        {'id': 'door:xd02_adit', 'to': 'xeen_xd02.blv', 'kind': 'door', 'condition': {'qbit': 'x4_adit_open'},
         'arrival_hint': "In the west adit's mouth, beside the winch, facing in.",
         'notes': "XD-02 Red Dwarf Mines' west adit (M3): caved in until the party winches it open from inside; "
                  "then a two-way shortcut to X1 for Act II. Before that the mouth is a rock fall (a message)."},
        {'id': 'stable:burlock_vertigo', 'to': 'xeen_x1.odm', 'kind': 'stable', 'days': 4,
         'schedule': {'weekdays': ['wednesday', 'sunday']}, 'service': 'Royal Stables of Burlock (4155), route 408',
         'notes': 'A4 writes the routes; the arrival is burlock_stables.'},
        {'id': 'stable:burlock_rivercity', 'to': 'xeen_x2.odm', 'kind': 'stable', 'days': 2,
         'schedule': {'weekdays': ['tuesday', 'thursday', 'saturday']},
         'service': 'Royal Stables of Burlock (4155), route 409'},
        {'id': 'stable:asp_rivercity', 'to': 'xeen_x2.odm', 'kind': 'stable', 'days': 3,
         'schedule': {'weekdays': ['wednesday']}, 'service': 'The Travel Pit (4170), route 412',
         'notes': 'Routes 410 and 411 join the two stables on this map (Burlock and the Travel Pit, 1 day).'},
        {'id': 'boat:nystor', 'to': 'xeen_x2.odm', 'kind': 'boat', 'condition': {'qbit': 'nystor_upriver'},
         'service': "Captain Nystor's boat (X2's dock, 486), upriver",
         'arrival_hint': "On Nystor's landing, the jetty behind.",
         'notes': 'After Q-C23 (q-c23.done) the boat calls here; arrival x4_river_landing.'},
    ],
    'qbits': {
        'crusaders': 110047,
        'x4_adit_open': 110020,
        'asp_pedestals': 112101,
        'asp_liberated': 112102,
        'nystor_upriver': 112461,
        'mirror_burlock': 119003,
        'mirror_asp': 119013,
    },
    'rules': {
        'weather': 'fair',
        'town_portal_anchor': 'entrance:burlock_square',
        'rim': {'sides': ['north'], 'cliff_y': RIM_Y, 'fall': 'death'},
    },
    'notes': 'X4 Burlock Savannah, MU-3 plan for gate G1 (A5, 2026-11-20). No geometry until the user has seen it. '
             'Plan: plan.yml; to-scale layout: sketch.yml; generator, drawings and review board: '
             'output/studio_cal/x4/ (tools/gen_l1.py writes these three files).',
}

# ---------------------------------------------------------------- the land: zones (districts) and bands
ZONES = {
    'zone:rim': [[0, 0], [128, 0], [128, RIM_Y], [0, RIM_Y]],
    'zone:gargoyle_range': [[0, RIM_Y], [100, RIM_Y], [100, 36], [94, 42], [86, 44], [80, 40], [74, 44], [68, 43],
                            [60, 42], [52, 44], [44, 45], [36, 46], [28, 47], [18, 49], [0, 49]],
    'zone:lava_fields': [[100, RIM_Y], [128, RIM_Y], [128, 58], [112, 60], [104, 58], [98, 52], [94, 42], [100, 36]],
    'zone:uplands': [[0, 49], [18, 49], [28, 47], [36, 46], [44, 45], [52, 44], [56, 43], [56, 62], [54, 70],
                     [46, 66], [36, 63], [0, 63]],
    'zone:west_downs': [[0, 63], [36, 63], [46, 66], [50, 74], [47, 79], [34, 79], [34, 92], [32, 128], [0, 128]],
    'zone:castle_fields': [[56, 43], [60, 42], [68, 43], [74, 44], [80, 42], [82, 48], [82, 79], [54, 79],
                           [50, 74], [54, 70], [56, 62]],
    'zone:south_fields': [[34, 92], [50, 92], [50, 79], [82, 79], [82, 128], [32, 128]],
    'zone:east_savannah': [[82, 44], [86, 44], [94, 42], [98, 52], [104, 58], [112, 60], [128, 58], [128, 80],
                           [100, 78], [94, 82], [90, 96], [98, 104], [100, 128], [82, 128]],
    'zone:red_hills': [[94, 82], [100, 78], [128, 80], [128, 128], [100, 128], [98, 104], [90, 96]],
}

TOWNS = {
    'town:burlock_castle': [[56, 43], [68, 43], [68, 50], [56, 50]],
    'town:burlock': [[55, 50], [69, 50], [69, 62], [55, 62]],
    'zone:burlock_square': [[59, 54], [66, 54], [66, 59], [59, 59]],
    'zone:lists': [[65, 63], [74, 63], [74, 72], [65, 72]],
    'town:asp': [[34, 79], [51, 79], [51, 92], [34, 92]],
    'zone:asp_square': [[38, 82], [46, 82], [46, 88], [38, 88]],
    'zone:carlawna_yard': [[38, 51], [43, 51], [43, 55], [38, 55]],
    'zone:falagar_yard': [[98, 59], [103, 59], [103, 64], [98, 64]],
    'zone:druid_grove': [[22, 66], [30, 66], [30, 74], [22, 74]],
    'zone:nystor_landing': [[80, 98], [86, 98], [86, 104], [80, 104]],
    'zone:falls': [[74, 43], [83, 43], [83, 49], [74, 49]],
}

BANDS = [
    ('band:rim_sea', 'zone:rim'),
    ('band:peaks', 'zone:gargoyle_range'),
    ('band:high', 'zone:lava_fields'),
    ('band:high', 'zone:red_hills'),
    ('band:mid', 'zone:uplands'),
    ('band:mid', 'town:burlock_castle'),
    ('band:mid', 'town:burlock'),
    ('band:low', 'zone:west_downs'),
    ('band:low', 'zone:castle_fields'),
    ('band:low', 'zone:south_fields'),
    ('band:low', 'zone:east_savannah'),
]

HEIGHT_POINTS = [
    ([14, 31], 2900, 'the range beyond the west edge'),
    ([26, 30], 3300, None),
    ([38, 29], 3600, None),
    ([50, 30], 3900, 'Gargoyle Peak (the eyrie inside it)'),
    ([62, 30], 3400, None),
    ([72, 29], 3700, None),
    ([84, 30], 3400, None),
    ([94, 30], 3000, None),
    ([102, 30], 2400, 'the range ends in the lava fields; the rim lookout'),
    ([49, 35], 3300, "the sky-crack ledge on Gargoyle Peak's south shoulder"),
    ([46, 41], 1900, "the eyrie's mouth"),
    ([42, 47], 1500, 'the eyrie path under the crags'),
    ([40, 53], 1350, "Carlawna's hut"),
    ([28, 53], 1350, 'the barbarian camp'),   # D-142: 4 east, 2 north
    ([20, 60], 1150, 'the X6 arrival'),
    ([36, 62], 1200, 'the west fork'),
    ([48, 66.5], 1350, "the obelisk's knoll"),
    ([62, 46.5], 1900, "Castle Burlock's rise"),
    ([57, 45.5], 1900, "the castle's west tower; the throne's landing 1,000 above the ground beside it"),
    ([62, 56], 1300, 'the village square'),
    ([69, 67], 1050, 'the jousting lists'),
    ([62.5, 76], 1000, 'Burlock Cross'),
    ([69, 74], 1000, "the signature camera, the lists' south end"),
    ([80.5, 40.5], 1700, 'the falls head'),
    ([81, 45], 700, 'the falls pool'),
    ([77, 47.5], 1100, 'the Olympian Fountain terrace'),
    ([88, 76], 900, 'the east fork'),
    ([87, 87], 850, "Joe's caravan"),
    ([85, 99], 780, 'the landing fork'),
    ([82, 101], 720, "Nystor's landing"),
    ([96, 107], 1100, 'the X2 arrival'),
    ([96, 120], 1150, 'the Rivercity road at the edge (X2: 1,150)'),
    ([100, 61], 1400, "Falagar's hut on a lava shoulder"),
    ([107, 66.5], 1300, 'the X7 arrival'),
    ([108, 40], 1800, 'the lava fields'),
    ([104, 46], 1750, 'the Shrine of Fire (D-11.2: inside the playable square, x <= 105)'),
    ([106, 52], 1550, 'the burned caravan'),
    ([104, 30.5], 2200, 'the rim lookout'),
    ([106, 86], 1750, "the ogres' hollow"),
    ([114, 92], 2400, 'red dwarf hills'),
    ([110, 104], 2200, 'red dwarf hills'),
    ([104, 95.5], 1500, 'the west adit (XD-02)'),
    ([96, 90], 1300, 'the dwarf boundary stone'),
    ([60, 93], 950, 'the quintain field'),
    ([56, 103], 1000, "the renegade knights' camp"),
    ([41, 86], 1050, "Asp's square"),
    ([36, 107], 1050, 'the X3 arrival'),
    ([26, 70], 1100, "the Autumn Druid's grove"),
    ([27, 96], 1150, "Asp's old cemetery"),
]

CLIFFS = [
    {'line': [[0, RIM_Y], [64, RIM_Y], [128, RIM_Y]], 'drop': 2500, 'down': 'left',
     'notes': 'The world rim (drawn west to east, the low side north, on the left): the Gargoyle Range ends in a '
              'cliff of 2,000-3,500 above the stars; about 1,600 at the lava fields.'},
    {'line': [[79, 41], [82, 41]], 'drop': 900, 'down': 'right',
     'notes': "The falls: the river leaves the range over a 900 step into its pool."},
    {'line': [[55, 50], [69, 50]], 'drop': 450, 'down': 'right',
     'notes': "The castle rise's south face: the castle wall over the village."},
]

RIDGES = [
    {'line': [[0, 32], [14, 31], [26, 30], [38, 29], [50, 30], [62, 30], [72, 29], [84, 30], [94, 30], [102, 31]],
     'height': 3300, 'width': 2, 'slope': 3, 'notes': 'The Gargoyle Range crest, bare rock.'},
    {'line': [[104, 84], [110, 90], [114, 96], [112, 104]], 'height': 2200, 'width': 2, 'slope': 3,
     'notes': 'The red dwarf hills.'},
]

RIVER = {'id': 'water:river',
         'line': [[80.5, 41], [81, 45], [80.5, 52], [80, 58], [81, 64], [81, 70], [80, 76], [81, 82], [80, 88],
                  [79, 94], [79, 100], [80, 106], [79, 112], [79, 120], [RIVER_OUT_X, 128]],
         'width_cells': 3, 'level': 650,
         'notes': 'The Great River\'s upper reach: out of the Gargoyle Range over the falls, south past the castle '
                  'and the lists, under the King\'s Bridge, past Nystor\'s landing, out at x 79 to X2 (X2\'s '
                  'north_river, level 576, enters there at its x 30).'}

RIM_SEA = {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': ZONES['zone:rim'],
           'notes': 'Below the rim: stands for the stars.'}
FALLS_POOL = {'id': 'water:falls_pool', 'kind': 'pond', 'level': 650,
              'polygon': [[79, 43], [83, 43], [84, 46], [79, 47]], 'notes': 'The pool under the falls.'}

ROADS = [
    ('link:kings_road', [[62.5, 58.8], [62.5, 62], [62.5, 68], [62.5, 76]], 'road', 'road_pebbles'),
    ('link:castle_lane', [[62, 50.5], [62, 54]], 'lane', None),
    ('link:bridge_road', [[62.5, 76], [70, 76], [76, 76], [84, 76], [88, 76]], 'road', 'road_pebbles'),
    ('link:river_road', [[88, 76], [87, 82], [86.5, 88], [85, 94], [85, 99]], 'road', 'soil'),
    ('link:landing_lane', [[85, 99], [82, 101]], 'lane', None),
    ('link:rivercity_road', [[85, 99], [90, 103], [95, 107], [96, 112], [SOUTH_X2_X, 128]], 'road', 'road_pebbles'),
    ('link:firestone_road', [[88, 76], [94, 72], [100, 68.5], [107, 66.5], [116, EAST_Y], [128, EAST_Y]], 'road',
     'soil'),
    ('link:falagar_lane', [[100, 68.5], [100, 63]], 'lane', None),
    ('link:lava_track', [[100, 63], [104, 56], [108, 48], [106, 38], [104, 31]], 'lane', None),
    ('link:adit_lane', [[95, 107], [99, 101], [103.5, 95.5]], 'lane', None),
    ('link:asp_road', [[62.5, 76], [56, 78], [51, 84], [48, 85], [46, 85.3]], 'road', 'road_pebbles'),
    ('link:x3_road', [[40.5, 88.4], [40.5, 92.5], [38, 97], [36, 102], [SOUTH_X3_X, 128]], 'road', 'soil'),
    ('link:west_road', [[0, WEST_Y], [19, WEST_Y], [28, 61], [36, 62], [44, 65], [50, 69], [56, 73], [62.5, 76]],
     'road', 'soil'),
    ('link:eyrie_path', [[36, 62], [38, 57], [40, 55], [43, 49], [46, 42]], 'lane', None),
    ('link:druid_path', [[30, 61.2], [27, 66], [26, 69]], 'lane', None),
    ('link:falls_path', [[69, 57.5], [73, 55], [76, 51], [77, 48]], 'lane', None),
    ('link:quintain_track', [[62.5, 76], [62, 84], [60, 92], [57, 100], [56, 102]], 'lane', None),
    ('link:barbarian_track', [[28, 61], [29, 57.5], [28.5, 55.5]], 'lane', None),
]

# ---------------------------------------------------------------- buildings and plots
# (building id, service, A4 house, footprint [front, depth], at (top-left), facing, door_to, kit, notes)
BURLOCK = [
    ('building:burlock_temple', 'Chapel of the Crown', 4153, [2.5, 2.5], [56, 51], 's', 'zone:burlock_square',
     'stone'),
    ('building:burlock_tavern', 'The Jousting Pig', 4156, [2, 2], [59.0, 52.0], 's', 'zone:burlock_square', 'timber'),
    ('building:burlock_weapons', 'The Royal Armoury', 4151, [2, 1.5], [64.0, 51.5], 's', 'zone:burlock_square',
     'stone'),
    ('building:burlock_armour', 'Plate and Mail by Royal Appointment', 4152, [2, 1.5], [66.5, 51.5], 's',
     'zone:burlock_square', 'plaster'),
    ('building:burlock_training', "The King's Lists", 4154, [3, 2.5], [55.5, 54.5], 's', 'zone:burlock_square',
     'stone'),
    ('building:burlock_stables', 'Royal Stables of Burlock', 4155, [2, 2.5], [66, 55.0], 'w', 'zone:burlock_square',
     'timber'),
]
BURLOCK_HOUSES = [  # (house, footprint, at, facing, kit)
    (4158, [1.5, 1.5], [56, 58.3], 'e', 'plaster'),
    (4159, [1, 1.5], [56, 60.3], 'e', 'timber'),
    (4160, [1.5, 1], [58.5, 60.0], 'n', 'timber'),   # set back (TOWN_FEEL 2: mirror share)
    (4161, [1, 1], [60.0, 60.5], 'e', 'plaster'),
    (4162, [1.5, 1], [63.0, 59.5], 'n', 'grey'),
    (4163, [1, 1], [65.5, 60.5], 'w', 'poor'),
    (4164, [1.5, 1], [67, 58.0], 'n', 'timber'),
    (4165, [1, 1], [67.5, 60.5], 'n', 'plaster'),
]
ASP = [
    ('building:asp_travel_pit', 'The Travel Pit', 4170, [2, 3], [48.5, 80.3], 's', 'link:asp_road', 'timber',
     'Open from day one, outside the curse (WORLD_DESIGN 5.1).'),
    ('building:asp_shrine', 'Roadside Shrine', 4171, [1.5, 1.5], [48.8, 86.3], 'n', 'link:asp_road', 'stone',
     'Open from day one, outside the curse.'),
    ('building:asp_guild_earth', 'Asp Guild of Earth', 4175, [2, 2], [37.8, 79.8], 's', 'zone:asp_square', 'stone',
     'Opens with q-c5.done.'),
    ('building:asp_guild_body', 'Asp Guild of Body', 4176, [2, 2], [42.4, 79.8], 's', 'zone:asp_square', 'stone',
     'Opens with q-c5.done.'),
    ('building:asp_alchemist', 'Snake Oil', 4173, [1.5, 2], [35.6, 82.4], 'e', 'zone:asp_square', 'timber',
     'Opens with q-c5.done.'),
    ('building:asp_armour', 'Scale House', 4174, [1.5, 1.5], [46.3, 82.3], 'w', 'zone:asp_square', 'plaster',
     'Opens with q-c5.done.'),
]
ASP_HOUSES = [  # 4172 Sarah Slither open from day one; 4178-4186 open with q-c5.done
    (4172, [1, 1.5], [36.3, 84.6], 'e', 'grey'),
    (4178, [1, 1], [36.8, 86.4], 'e', 'poor'),
    (4179, [1, 1], [35.5, 88.6], 'e', 'poor'),
    (4180, [1.5, 1], [37.8, 88.8], 'n', 'timber'),
    (4181, [1, 1], [43.6, 88.8], 'n', 'plaster'),
    (4182, [1.5, 1], [45, 88.8], 'n', 'poor'),
    (4183, [1, 1], [46.5, 86.0], 'n', 'grey'),   # F67 p12 (2026-11-25): its door onto the Asp road's end, not sideways
    (4184, [1, 1], [47.2, 88.8], 'n', 'poor'),
    (4185, [1, 1.5], [44.8, 79.8], 's', 'poor'),
    (4186, [1.5, 1.5], [35.4, 90.2], 'e', 'timber'),
]
HUTS = [
    ('zone:carlawna_yard', 'building:carlawna_hut', "Carlawna's Hut", 4166, [1.5, 1.5], [39.6, 52.2], 's', 'poor'),
    ('zone:falagar_yard', 'building:falagar_hut', "Falagar's Hut", 4167, [1.5, 1.5], [99.2, 60.2], 's', 'stone'),
]

# Asp's well and the eight two-colour pedestals round it (D-4, XD-25 1): index 1 is the south-west one.
ASP_WELL = [41, 85]


def pedestals():
    # the eight cells round the well's cell, from the south-west one clockwise as seen from above (north up)
    x, y = ASP_WELL
    return [[x - 1, y + 1], [x - 1, y], [x - 1, y - 1], [x, y - 1], [x + 1, y - 1], [x + 1, y], [x + 1, y + 1],
            [x, y + 1]]


# ---------------------------------------------------------------- points
POINTS = [
    # arrivals and edges
    ('entrance:x2_road', [96, 107], 'n', "Main arrival from X2 Rivercity (the Rivercity road)."),
    ('entrance:x3_road', [36, 107], 'n', 'Arrival from X3 Lifeforce Lagoon (the Asp road).'),
    ('entrance:west_road', [20, 60], 'e', 'Arrival from X6 Desert of the Sphinx.'),
    ('entrance:east_road', [107, 66.5], 'w', 'Arrival from X7 Mount Firestone.'),
    ('entrance:burlock_square', [61, 57], 's', 'A4 arrival burlock_square: by the mirror (Town Portal).'),
    ('entrance:burlock_stables', [65.2, 56], 'w', "A4 arrival burlock_stables: before the Royal Stables' door "
     "(the stables moved to [66, 55] for TOWN_FEEL's mirror share; [67, 57] stood on its wall)."),
    ('entrance:asp_travel_pit', [50, 84], 'w', 'A4 arrival asp_travel_pit: the Travel Pit, outside the curse.'),
    ('entrance:asp_square', [39, 87], 'n', "A4 arrival asp_square: by the well (Asp's mirror, q-c5.done)."),
    ('entrance:river_landing', [83, 101], 'w', "A4 arrival x4_river_landing: Nystor's jetty (after Q-C23)."),
    ('entrance:xd07_gate', [62, 50], 'n', 'XD-07 Castle Burlock: the castle gate.'),
    ('entrance:throne_landing', [55, 45], 'e',
     "XD-07's throne fall (D-4): lands at ground + 1,000 (about 2,900) beside the west tower, outside the walls; "
     "a fall, ordinary fall damage."),
    ('entrance:xd25_stair', [41, 81], 'n', "XD-25 Asp Undercroft: the cellar stair on Asp's square, the rule "
                                             "stone beside it."),
    ('entrance:xd26_eyrie', [46, 43], 's', "XD-26 Gargoyle Eyrie: in front of the mouth on Gargoyle Peak's south "
                                           "face, facing out (A5 s18: off the mound, merge point 25)."),
    ('entrance:xd26_sky_crack', [49, 35], 's', "XD-26's sky-crack ledge (D-4): a one-way exit from the eyrie's top "
                                               "onto a ledge at about 3,300 on the same peak; a goat path down to "
                                               "the eyrie mouth."),
    ('entrance:xd02_adit', [103, 95], 'w', "XD-02's west adit in the red dwarf hills (rock fall until M3's "
                                           "winch): on the lane 416 before the adit's face, facing out (A5 s19; it "
                                           "stood beside the adit's north wall facing in)."),
    # junctions
    ('junction:burlock_cross', [62.5, 76], None, None),
    ('junction:east_fork', [88, 76], None, None),
    ('junction:landing_fork', [85, 99], None, None),
    ('junction:west_fork', [36, 62], None, None),
    ('junction:asp_gate', [48, 84], None, None),
    # places
    ('poi:obelisk', [48, 66.5], None, None),
    ('poi:well_might', [63, 57], None, 'On the village square.'),
    ('poi:burlock_mirror', [60, 55], None, "A4 4157, the village square's mirror."),
    ('poi:olympian_fountain', [77, 47.5], None, None),
    ('poi:jousting_lists', [69, 67], None, None),
    ('poi:carlawna', [40.4, 54.3], None, "Carlawna (4303) at her hut's door."),
    ('poi:falagar', [100, 62.3], None, "Falagar (4304) at his hut's door."),
    ('poi:joe_caravan', [87.5, 87], None, 'Joe the Merchant (4320) at his wagon on the river road.'),
    ('poi:barbarian_camp', [28, 53], None, None),
    ('poi:nystor_landing', [81.5, 101], None, None),
    ('poi:autumn_druid', [26, 70], None, 'The Autumn Druid (4321) in her ring of stones.'),
    ('poi:asp_well', ASP_WELL, None, None),
    ('poi:rule_stone', [40, 81], None, 'Beside the undercroft stair: the pedestal rhyme.'),
    ('poi:adam_eve', [43, 84], None, 'Adam (4301), by the well just outside the pedestal ring, off the door lines.'),
    ('poi:adam_eve', [43, 86], None, 'Eve (4302), beside him.'),
    ('poi:asp_mirror', [42, 88], None, "A4 4177: Asp's mirror on the square's west side (q-c5.done)."),
    ('poi:king_statue', [61, 74.6], None, None),
    ('poi:shrine_fire', [104, 46], None, 'D-11.2: moved inside the map.'),
    ('poi:rim_lookout', [104, 30.5], None, None),
    ('poi:quintain_field', [60, 93], None, None),
    ('poi:herders_well', [40, 101], None, None),
    ('poi:wayfarers_well', [96, 71], None, None),
    ('poi:dwarf_stone', [96, 90], None, None),
    ('poi:asp_cemetery', [27, 96], None, None),
    ('poi:ogre_camp', [106, 86], None, None),
    ('poi:knights_camp', [56, 103], None, None),
    ('poi:gargoyle_roost', [88, 37], None, None),
    ('poi:saddlebags', [52, 91.5], None, None),
    ('poi:champions_barrow', [70, 86], None, None),
    ('poi:sunken_barge', [77.6, 91], None, None),
    ('poi:ore_cart', [101, 97.5], None, None),
    ('poi:burned_caravan', [106, 52], None, None),
    ('poi:mill_ruin', [85, 61], None, None),
    # D-11.5: small devices where only a fight area lay within 6,000
    ('poi:bridge_cairn', [77, 77.5], None, "A cairn at the King's Bridge."),
    ('poi:savannah_well', [93, 50], None, "A herders' well on the east savannah."),
    ('poi:standing_stone', [21, 83], None, 'A standing stone on the west downs.'),
    ('poi:jousters_grave', [69, 106], None, "A jouster's grave in the south fields."),
    ('poi:eyrie_waystone', [42, 50.5], None, 'A waystone on the eyrie path.'),
    ('poi:red_waymark', [104, 76], None, 'A red waymark stone where the Firestone road meets the red hills.'),
    ('landmark:castle_burlock', [62, 46.5], None, None),
    ('landmark:gargoyle_peak', [50, 30], None, None),
    ('landmark:falls', [80.5, 42], None, None),
    ('landmark:lava_fields', [112, 40], None, None),
    ('landmark:red_hills', [112, 96], None, None),
    ('landmark:kings_beacon', [64, 32], None, None),
]
SIGNPOSTS = ['junction:burlock_cross', 'junction:east_fork', 'junction:landing_fork', 'junction:west_fork',
             'junction:asp_gate']

# ---------------------------------------------------------------- monsters
# Encounter areas: (id, slot, markers, polygon, family note)
AREAS = [
    # D-15/D-133 (2026-11-24, check_d85 first fight): markers came out 1,888 from XD-26's set-down on the Sky Crack
    # ledge (49.5, 35.5) and 373 from the eyrie mouth's arrival (46, 43): the area ends at x 41, 2,560 clear of the
    # mouth and 4,352 of the ledge (it ran to x 56)
    ('pop:range_west', 3, 9, [[20, 34], [41, 34], [41, 46], [38, 47], [28, 49], [20, 50]],
     'Gargoyles (16/22/28) along the range foot and round the eyrie path; none within 6 cells of the castle.'),
    ('pop:range_east', 3, 9, [[74, 32], [109, 32], [109, 56], [102, 56], [96, 48], [88, 48], [82, 50], [76, 48],
                              [74, 44]],
     'Gargoyles over the falls, the roost and the lava fields; the Olympian Fountain is the lure.'),
    ('pop:red_hills', 2, 8, [[97, 78], [109, 76], [109, 109], [103, 109], [99, 101], [100, 95], [100, 88], [98, 82]],
     "Ogres (18/22/30) in the red dwarf hills round their camp; no marker within 4 cells of the adit; the west "
     "side cut back so no marker stands within 5,888 of Joe's caravan (D-85)."),
    ('pop:south_fields', 1, 9, [[46, 92], [56, 88], [66, 82], [76, 80], [77, 96], [76, 109], [44, 109],
                                 [42, 100]],
     'Burlock knights gone bad: Jousters 14, Yang Knights 20, Knight Captains 26 roam the jousting fields.'),
    ('pop:west_downs', 2, 4, [[19, 76], [32, 76], [33, 92], [30, 109], [19, 109]],
     "Ogres on the downs west of Asp, round the old cemetery."),
    # D-11.2: six markers moved (south fields 12 -> 9, west downs 7 -> 4), none added, into three wandering pairs on
    # the longest fightless roads, each >= 2,500 from town doors and arrivals.
    ('pop:pair_river_road', 1, 2, [[88, 100], [90, 100], [90, 103], [88, 103]],
     'D-11.2: a pair of renegade knights on the Rivercity road just past the landing fork (D-85: moved off the '
     "river road, out of missile range of Joe's caravan)."),
    ('pop:pair_firestone_road', 2, 2, [[92, 71], [96, 71], [96, 75], [92, 75]],
     'D-11.2: a pair of ogres on the Firestone road east of the east fork.'),
    ('pop:pair_west_ogres', 2, 1, [[40, 62], [43, 62], [43, 65], [40, 65]],
     "D-11.2: the west road's pair, an ogre band below the obelisk's knoll ..."),
    ('pop:pair_west_knights', 1, 1, [[52, 70], [55, 70], [55, 73], [52, 73]],
     '... and a knight band nearer Burlock Cross (one marker each: the pair is a downs marker and a fields marker).'),
]
# D-142 / D-157 (2026-11-25, F64): the sketch's encounter areas are circle markers (x, y, count, r), each pack at
# its spot inside its AREAS polygon above (the places the studio had drawn from the polygons), so gen.py can hold them
# to D-142 (common/d142.py enforce: 4,096 from the edge arrivals and the dungeon exits, centres 1,024 from every road,
# lane and path) and print each move. The polygons stay the populations' ranges (the plan's words).
MARKERS = {
    'pop:range_west': [(26, 48, 1, 0.5), (27, 35, 1, 0.5), (31, 47, 1, 0.5), (33, 38, 1, 0.5),
                       (39, 38, 1, 0.5), (22, 44, 1, 0.5), (23, 47, 1, 0.5), (39, 46, 2, 1)],
    'pop:range_east': [(87, 33, 1, 0.5), (75, 38, 1, 0.5), (103, 38, 1, 0.5), (101, 34, 1, 0.5),
                       (94, 44, 1, 0.5), (103, 36, 1, 0.5), (84, 48, 1, 0.5), (105, 40, 1, 0.5),
                       (76, 46, 1, 0.5)],
    'pop:red_hills': [(105, 89, 2, 1), (109, 90, 1, 0.5), (98, 82, 1, 0.5), (103, 81, 1, 0.5),
                      (103, 103, 1, 0.5), (104, 108, 1, 0.5), (105, 105, 1, 0.5)],
    'pop:south_fields': [(68, 84, 1, 0.5), (56, 98, 1, 0.5), (71, 87, 1, 0.5), (44, 98, 1, 0.5),
                         (62, 104, 1, 0.5), (67, 93, 1, 0.5), (59, 108, 1, 0.5), (72, 104, 1, 0.5),
                         (57, 106, 1, 0.5)],
    'pop:west_downs': [(32, 85, 1, 0.5), (22, 102, 1, 0.5), (22, 98, 1, 0.5),   # x 22: 768 off the bounds (F63)
                       (29, 108, 1, 0.5)],
    'pop:pair_river_road': [(90, 101, 2, 1)],
    'pop:pair_firestone_road': [(92, 73, 2, 1)],
    'pop:pair_west_ogres': [(40, 64, 1, 0.5)],
    'pop:pair_west_knights': [(53, 72, 1, 0.5)],
}
assert all(sum(m[2] for m in MARKERS[a[0]]) == a[2] for a in AREAS), 'MARKERS and AREAS disagree on a count'
# Placed hostiles (monster id, at, count, spread, group, note)
ACTORS = [
    ('11100', [28, 53], 4, 2, 1, 'Barbarians 14 at the camp to burn.'),
    ('11101', [29, 54], 1, 1, 1, 'A Sardaj Warrior 20.'),
    ('11102', [27.5, 52], 1, 0, 1, 'The Barbarian Chief 28 by the chest.'),
    ('11060', [106, 86], 3, 2, 2, "Ogres 18 at their camp in the hollow."),
    ('11061', [107, 87], 1, 1, 2, 'An Ogre Brute 22.'),
    ('11140', [56, 103], 3, 2, 3, "Jousters 14 at the renegade knights' camp."),
    ('11141', [57, 104], 1, 1, 3, 'A Yang Knight 20, their leader.'),
]
KEEP_CLEAR = [
    ('town:burlock', [[50, 40], [74, 40], [76, 64], [72, 72], [52, 72], [50, 62]],
     'The castle, the village and the lists with their buffer (about 2,500 round the doors).'),
    ('town:asp', [[30, 76], [54, 76], [54, 95], [30, 95]], 'Asp and its edge services with their buffer.'),
    ('zone:druid_grove', [[21, 65], [31, 65], [31, 75], [21, 75]], None),
    ('edge:south_x2_end', [[90, 100], [102, 100], [102, 110], [90, 110]], "The X2 arrival and Nystor's landing road."),
    ('zone:nystor_landing', [[79, 96], [87, 96], [87, 104], [79, 104]], None),
    ('zone:falagar_yard', [[96, 58], [104, 58], [104, 70], [96, 70]], 'Falagar and the X7 arrival.'),
    ('edge:west_end', [[19, 57], [26, 57], [26, 64], [19, 64]], None),
]
OPEN = [
    ('zone:uplands', [[26, 52], [56, 50], [56, 62], [50, 68], [36, 64], [26, 62]],
     'Quiet high grass under the range: the obelisk, the eyrie path, Carlawna.'),
    ('zone:east_savannah', [[84, 52], [96, 52], [100, 66], [92, 80], [84, 80]],
     'Quiet river meadows east of the bridge: the caravan road.'),
]

VIEWS = [
    {'id': 'view:arrival', 'at': [96, 107], 'height': 180, 'look': [80, 84],
     'purpose': "MU-4 arrival view from X2's road: the river valley north-west, Nystor's landing and the jetty on "
                "the left, the Rivercity road bending to the landing fork, Joe's caravan by the river road beyond, "
                "the red dwarf hills on the right, and the Gargoyle Range's bare peaks across the horizon."},
    {'id': 'view:signature', 'at': [69, 74], 'height': 300, 'look': [63, 46],
     'purpose': "MU-4 signature view: from the south end of the jousting lists, north over the lists to the walled "
                "village and Castle Burlock on its rise, the Gargoyle Range's peaks behind and the falls on the "
                "right."},
]


def half(at):
    return [round(v * 2) / 2 for v in at]


def cell(at):
    import math
    return [int(math.floor(at[0])), int(math.floor(at[1]))]


def poly_area(p):
    s = 0.0
    for i in range(len(p)):
        x1, y1 = p[i]
        x2, y2 = p[(i + 1) % len(p)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


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
    burlock_plots = []
    for bid, service, house, fp, at, facing, door_to, kit in BURLOCK:
        at = half(at)
        burlock_plots.append({'building': bid, 'at': at, 'facing': facing, 'door_to': door_to, 'kit': kit,
                              'house': house})
        plot_rects.append((bid, at, fp, facing))
    for i, (house, fp, at, facing, kit) in enumerate(BURLOCK_HOUSES, 1):
        at = half(at)
        burlock_plots.append({'building': 'building:burlock_houses', 'index': i, 'at': at, 'facing': facing,
                              'kit': kit, 'house': house})
        plot_rects.append((f'burlock_houses#{i}', at, fp, facing))
    districts.append({'space': 'town:burlock_castle', 'polygon': TOWNS['town:burlock_castle'],
                      'notes': "Castle Burlock's exterior on its rise (royal_castle kit: cream ashlar on grey footings, "
                               "slate cones): keep, four towers, curtain wall, the gate over the village (XD-07's "
                               "door). The castle itself is the BLV."})
    districts.append({'space': 'town:burlock', 'polygon': TOWNS['town:burlock'], 'plots': burlock_plots,
                      'notes': "The walled village before the castle gate: 15 doors of A4's x4.yml (4151-4165; the "
                               "mirror 4157 on the square); about 160 cells inside the wall; gates south (the King's "
                               "road) and east (the stables, the falls path)."})
    districts.append({'space': 'zone:burlock_square', 'polygon': TOWNS['zone:burlock_square']})
    districts.append({'space': 'zone:lists', 'polygon': TOWNS['zone:lists'],
                      'notes': 'The jousting lists: a tilt barrier north-south (it leads the eye to the castle), '
                               'stands on the east side, pavilions at the north end.'})
    asp_plots = []
    for bid, service, house, fp, at, facing, door_to, kit, note in ASP:
        at = half(at)
        asp_plots.append({'building': bid, 'at': at, 'facing': facing, 'door_to': door_to, 'kit': kit,
                          'house': house})
        plot_rects.append((bid, at, fp, facing))
    for i, (house, fp, at, facing, kit) in enumerate(ASP_HOUSES, 1):
        at = half(at)
        asp_plots.append({'building': 'building:asp_houses', 'index': i, 'at': at, 'facing': facing, 'kit': kit,
                          'house': house})
        plot_rects.append((f'asp_houses#{i}', at, fp, facing))
    districts.append({'space': 'town:asp', 'polygon': TOWNS['town:asp'], 'plots': asp_plots,
                      'notes': "Asp: 16 doors of A4's x4.yml (4170-4186, the mirror 4177 on the square). The Travel "
                               "Pit and the Roadside Shrine stand on the Asp road at the east edge, outside the curse; "
                               "Sarah Slither's house is open; the rest open with q-c5.done. The square keeps a clear "
                               "ring round the well's pedestals and a clear line to every door."})
    districts.append({'space': 'zone:asp_square', 'polygon': TOWNS['zone:asp_square']})
    for space, bid, service, house, fp, at, facing, kit in HUTS:
        at = half(at)
        districts.append({'space': space, 'polygon': TOWNS[space],
                          'plots': [{'building': bid, 'at': at, 'facing': facing, 'kit': kit, 'house': house}]})
        plot_rects.append((bid, at, fp, facing))
    for space in ['zone:druid_grove', 'zone:nystor_landing', 'zone:falls']:
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
        if pid == 'poi:adam_eve':
            p['index'] = sum(1 for q in points if q['id'] == pid) + 1
        points.append(p)
    for i, at in enumerate(pedestals(), 1):
        points.append({'id': 'poi:pedestals', 'index': i, 'at': at,
                       'notes': ('the south-west pedestal: start here, red' if i == 1 else
                                 f'pedestal {i} clockwise; red when {"odd" if i % 2 else "even"}'
                                 + (' (red)' if i % 2 else ' (blue)'))})
    for i, j in enumerate(SIGNPOSTS, 1):
        at = next(p[1] for p in POINTS if p[0] == j)
        points.append({'id': 'poi:signposts', 'index': i, 'at': [int(at[0]) + 1, int(at[1]) - 1]})

    areas = []
    for aid, slot, count, poly, note in AREAS:
        for i, (x, y, n, r) in enumerate(MARKERS[aid], 1):
            a = {'id': aid, 'index': i, 'kind': 'encounter', 'count': n, 'slot': slot, 'circle': {'at': [x, y], 'r': r}}
            if i == 1:
                a['notes'] = note
            areas.append(a)
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
        'notes': 'X4 Burlock Savannah, MU-3 to-scale plan (A5, 2026-11-20), for gate G1: composition, scale and '
                 'density only. Cells [x, y], x east, y south. Heights in map units above the stars below the rim '
                 '(0): the river 650, the savannah 850-1,150, the castle rise 1,900, the red dwarf hills to 2,400, '
                 'the lava fields 1,500-1,900, the Gargoyle Range to 3,900. Generated by '
                 'output/studio_cal/x4/tools/gen_l1.py; the later L3 adds plots\' detail, ground, scatter and '
                 'structures.',
        'frame': {
            'playable': [19, 19, 90, 90],
            'edges': [
                {'side': 'south', 'span': [30, 42], 'neighbour': 'edge:south_x3',
                 'notes': f'The Asp road runs out to y 128 at x {SOUTH_X3_X}.'},
                {'side': 'south', 'span': [90, 102], 'neighbour': 'edge:south_x2',
                 'notes': f'The Rivercity road runs out to y 128 at x {SOUTH_X2_X}; the river at x {RIVER_OUT_X}.'},
                {'side': 'west', 'span': [54, 66], 'neighbour': 'edge:west',
                 'notes': f'The desert road runs out to x 0 at y {WEST_Y}.'},
                {'side': 'east', 'span': [60, 72], 'neighbour': 'edge:east',
                 'notes': f'The Firestone road runs out to x 128 at y {EAST_Y}.'},
            ],
            'rim': [
                {'side': 'north', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': f'The world rim: the Gargoyle Range ends in a cliff at y {RIM_Y}; below, water at 0 '
                          'stands for the stars (as X2\'s south rim).'},
                {'side': 'west', 'span': [0, 50], 'form': 'ridge', 'height': [2400, 3200], 'floor': 1500,
                 'crest': 10, 'roughness': 100, 'notes': 'The Gargoyle Range goes on west.'},
                {'side': 'west', 'span': [50, 54], 'form': 'ridge', 'height': [1500, 1900], 'floor': 1300,
                 'crest': 10, 'roughness': 100},
                {'side': 'west', 'span': [54, 66], 'form': 'level', 'height': 1150, 'meet': 6,
                 'notes': 'The desert road\'s saddle, open to the edge.'},
                {'side': 'west', 'span': [66, 128], 'form': 'ridge', 'height': [1500, 2200], 'floor': 1100,
                 'crest': 10, 'roughness': 100, 'notes': 'Dry downs rising toward the desert.'},
                {'side': 'east', 'span': [24, 60], 'form': 'ridge', 'height': [1800, 2600], 'floor': 1500,
                 'crest': 10, 'roughness': 120, 'notes': 'The lava fields climb toward Mount Firestone.'},
                {'side': 'east', 'span': [60, 72], 'form': 'level', 'height': 1300, 'meet': 6,
                 'notes': 'The Firestone road, open to the edge.'},
                {'side': 'east', 'span': [72, 128], 'form': 'ridge', 'height': [1900, 2700], 'floor': 1300,
                 'crest': 10, 'roughness': 100, 'notes': 'The red dwarf hills go on east (toward X1\'s mines).'},
                {'side': 'south', 'span': [0, 30], 'form': 'ridge', 'height': [1500, 2200], 'floor': 1100,
                 'crest': 10, 'roughness': 100},
                {'side': 'south', 'span': [30, 42], 'form': 'level', 'height': 1050, 'meet': 6,
                 'notes': 'The Asp road to X3.'},
                {'side': 'south', 'span': [42, 74], 'form': 'ridge', 'height': [1400, 2000], 'floor': 1000,
                 'crest': 10, 'roughness': 100, 'notes': 'Low downs south of the jousting fields.'},
                {'side': 'south', 'span': [74, 85], 'form': 'level', 'height': 700, 'meet': 6,
                 'notes': 'The river valley: the river leaves at x 79 for X2 (a gorge on X2\'s side).'},
                {'side': 'south', 'span': [85, 90], 'form': 'ridge', 'height': [1300, 1700], 'floor': 1100,
                 'crest': 8, 'roughness': 80},
                {'side': 'south', 'span': [90, 102], 'form': 'level', 'height': 1150, 'meet': 6,
                 'notes': 'The Rivercity road to X2 (X2\'s north edge span is level at 1,150).'},
                {'side': 'south', 'span': [102, 128], 'form': 'ridge', 'height': [2000, 2800], 'floor': 1400,
                 'crest': 10, 'roughness': 100, 'notes': 'The red dwarf hills.'},
            ],
            'edge': {'height': 1300, 'north': 0},
        },
        'heights': {
            'bands': bands,
            'points': [dict({'at': cell(at), 'h': h}, **({'notes': n} if n else {})) for at, h, n in HEIGHT_POINTS],
            'cliffs': CLIFFS,
            'ridges': RIDGES,
        },
        'water': {'bodies': [RIM_SEA, FALLS_POOL], 'rivers': [dict(RIVER, line=[cell(q) for q in RIVER['line']])]},
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


def plan():
    burlock_buildings = [building(bid, service, fp, notes=f'A4 house {house}.')
                         for bid, service, house, fp, at, facing, door_to, kit in BURLOCK]
    burlock_buildings.append(building('building:burlock_houses', 'residence', [h[1] for h in BURLOCK_HOUSES],
                                      count=len(BURLOCK_HOUSES),
                                      notes='A4 houses 4158-4165 in index order (Dame Ysolde, The Weathervane, '
                                            'Keeper of the Bestiary, Pomfrey, Royal Laundry, Wat, Bakehouse, Holt).'))
    asp_buildings = [building(bid, service, fp, notes=f'A4 house {house}. {note}')
                     for bid, service, house, fp, at, facing, door_to, kit, note in ASP]
    asp_buildings.append(building('building:asp_houses', 'residence', [h[1] for h in ASP_HOUSES],
                                  count=len(ASP_HOUSES),
                                  notes="A4 houses in index order: 4172 Sarah Slither (open from day one), then "
                                        "4178-4186 (open with q-c5.done)."))
    marker_hostiles = 0.0
    mean = {1: 2.5, 2: 2.5, 3: 3.0}
    for _aid, slot, count, _p, _n in AREAS:
        marker_hostiles += count * mean[slot]
    placed = sum(a[2] for a in ACTORS)
    hostiles = int(marker_hostiles + placed)  # 135.5 expected
    markers = sum(a[2] for a in AREAS)

    spaces = [
        # ---- the range and the north-east ----
        {'id': 'zone:gargoyle_range', 'name': 'The Gargoyle Range', 'kind': 'wild', 'floor': [1300, 3900],
         'relief': 'uneven', 'density': 'sparse',
         'where': 'the whole north, y 24 to 44: bare peaks ending in the rim cliff',
         'purpose': "Bare grey peaks along the world's north rim; gargoyles nest in them. The Gargoyle Eyrie (XD-26) "
                    "opens in Gargoyle Peak's south face; the river falls out of the range above the castle.",
         'population': [
             {'id': 'pop:range_west', 'slot': 3, 'groups': 9, 'per_marker': [2, 4], 'levels': [16, 28],
              'notes': 'Encounter area 1: Gargoyles round the eyrie path.'},
             {'id': 'pop:range_east', 'slot': 3, 'groups': 9, 'per_marker': [2, 4], 'levels': [16, 28],
              'notes': 'Encounter area 2: Gargoyles over the falls, the roost and the lava fields.'}]},
        {'id': 'zone:falls', 'name': 'The falls', 'kind': 'zone', 'part_of': 'zone:gargoyle_range',
         'floor': [650, 1700],
         'purpose': 'The river leaves the range over a 900 step into a pool; the Olympian Fountain on a terrace '
                    'beside it.'},
        {'id': 'zone:lava_fields', 'name': 'The lava fields', 'kind': 'wild', 'floor': [1500, 1900],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Black crusted rock and smoking vents at the north-east edge, toward Mount Firestone: the Shrine "
                    "of Fire, a burned caravan, the rim lookout at the range's end."},
        {'id': 'zone:rim', 'name': 'The world rim', 'kind': 'wild', 'floor': 0, 'empty': True,
         'purpose': 'North the land ends in a cliff; below, the stars (water at 0 stands for them).'},
        {'id': 'water:rim_sea', 'name': 'Below the rim', 'kind': 'water', 'purpose': 'The stars below the edge.'},
        # ---- Castle Burlock ----
        {'id': 'town:burlock_castle', 'name': 'Castle Burlock', 'kind': 'town', 'floor': 1900,
         'where': 'on a rise at the range foot, north-centre', 'safe': True, 'keep_clear': ['spawns'],
         'theme': 'royal_castle kit: cream hc ashlar with orange-tan quoins on grey cs footings, xtslate cones, the '
                  'Burlock crest and banners.',
         'purpose': "The royal seat: the castle's exterior; its gate leads into XD-07 (the Crusaders' portcullis is "
                    "inside). The throne's fall lands beside its west tower."},
        {'id': 'town:burlock', 'name': "Castle Burlock's village", 'kind': 'town', 'floor': 1300,
         'where': "inside a wall below the castle gate", 'safe': True, 'keep_clear': ['spawns'], 'density': 'dense',
         'theme': 'cloudside_town kit, middle and rich grades (hhm2 ochre, 7hhr1 cream), chb1 fieldstone services, '
                  'the royal_castle grey curtain wall with two gates.',
         'purpose': 'Services that need no title (WORLD_DESIGN 5.1): armoury, armourer, chapel, training to 40, '
                    'stables, tavern, the mirror, eight homes with teachers.',
         'buildings': burlock_buildings},
        {'id': 'zone:burlock_square', 'name': 'The village square', 'kind': 'zone', 'part_of': 'town:burlock',
         'floor': 1300, 'safe': True, 'purpose': 'The mirror and the Well of Might.'},
        {'id': 'zone:lists', 'name': 'The jousting lists', 'kind': 'zone', 'floor': 1050, 'safe': True,
         'keep_clear': ['spawns'],
         'purpose': "The King's tiltyard south of the village: a tilt barrier, stands and pavilions; the stat "
                    "challenge."},
        {'id': 'zone:castle_fields', 'name': 'The castle fields', 'kind': 'wild', 'floor': [900, 1300],
         'relief': 'slope', 'density': 'sparse',
         'purpose': 'Paddocks and hay meadows from the castle down to Burlock Cross and the river.'},
        # ---- the west ----
        {'id': 'zone:uplands', 'name': 'The range foot', 'kind': 'wild', 'floor': [1150, 1500],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "High dry grass under the range: Carlawna's hut and the eyrie path, the obelisk's knoll, the "
                    "barbarian camp by the desert road.",
         'population': [{'id': 'pop:pair_west_ogres', 'slot': 2, 'groups': 1, 'per_marker': [2, 3],
                         'levels': [18, 30], 'notes': "D-11.2: the west road's wandering pair, an ogre band ..."},
                        {'id': 'pop:pair_west_knights', 'slot': 1, 'groups': 1, 'per_marker': [2, 3],
                         'levels': [14, 26], 'notes': '... and a knight band nearer Burlock Cross.'}]},
        {'id': 'zone:carlawna_yard', 'name': "Carlawna's yard", 'kind': 'district', 'part_of': 'zone:uplands',
         'floor': 1350, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': 'Carlawna the Cleric (Q-C10, T1-C) at the foot of the eyrie path.',
         'buildings': [building('building:carlawna_hut', "Carlawna's Hut", [1.5, 1.5], notes='A4 house 4166.')]},
        {'id': 'zone:west_downs', 'name': 'The west downs', 'kind': 'wild', 'floor': [1000, 1400],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Rolling dry downs toward the desert: the Autumn Druid's grove, Asp's old cemetery, ogres.",
         'population': [{'id': 'pop:west_downs', 'slot': 2, 'groups': 4, 'per_marker': [2, 3], 'levels': [18, 30],
                         'notes': 'Encounter area 5: Ogres.'}]},
        {'id': 'zone:druid_grove', 'name': "The Autumn Druid's grove", 'kind': 'zone', 'part_of': 'zone:west_downs',
         'floor': 1100, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "A ring of stones under red and gold trees, the only autumn on Xeen (Q-C1's Autumn step, T1-C)."},
        {'id': 'town:asp', 'name': 'Asp', 'kind': 'town', 'floor': 1050, 'safe': True, 'keep_clear': ['spawns'],
         'density': 'medium',
         'where': 'south-west, on the Asp road between Burlock Cross and the X3 edge',
         'theme': 'cloudside_town kit, poor and middle grades (hhp1, hhp2, hhm3), shutters down, snake-skin on the '
                  'sills; chb1 fieldstone guild halls.',
         'purpose': 'The cursed town (Q-C5): townsfolk turning into snakes. The Travel Pit and the Roadside Shrine '
                    'work from day one at the edge; the rest opens with q-c5.done.',
         'buildings': asp_buildings},
        {'id': 'zone:asp_square', 'name': "Asp's square", 'kind': 'zone', 'part_of': 'town:asp', 'floor': 1050,
         'safe': True,
         'purpose': "The well with eight two-colour pedestals round it, the rule stone by the undercroft stair "
                    "(XD-25), Adam and Eve by the well, the mirror."},
        # ---- the south and east ----
        {'id': 'zone:south_fields', 'name': 'The jousting fields', 'kind': 'wild', 'floor': [850, 1150],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Rolling savannah south of Burlock Cross where knights train and some have gone bad: the "
                    "quintain field, the renegade knights' camp, the champions' barrow.",
         'population': [{'id': 'pop:south_fields', 'slot': 1, 'groups': 9, 'per_marker': [2, 3],
                         'levels': [14, 26], 'notes': 'Encounter area 4: Burlock knights.'},
                        {'id': 'pop:knights_camp', 'actor': 'Xeen Knight', 'groups': 1, 'placed': True,
                         'hostile': True, 'notes': "Four placed at the renegade knights' camp."}]},
        {'id': 'zone:east_savannah', 'name': 'The river meadows', 'kind': 'wild', 'floor': [700, 1400],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "The river's east bank: the river road with Joe's caravan, Nystor's landing, the Rivercity "
                    "road, the Firestone road and Falagar's hut under the lava.",
         'population': [{'id': 'pop:pair_river_road', 'slot': 1, 'groups': 2, 'per_marker': [2, 3],
                         'levels': [14, 26], 'notes': 'D-11.2, D-85: a renegade knight pair on the Rivercity road.'},
                        {'id': 'pop:pair_firestone_road', 'slot': 2, 'groups': 2, 'per_marker': [2, 3],
                         'levels': [18, 30], 'notes': 'D-11.2: a wandering pair of ogres on the Firestone road.'}]},
        {'id': 'zone:nystor_landing', 'name': "Nystor's landing", 'kind': 'zone', 'part_of': 'zone:east_savannah',
         'floor': 720, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "Captain Nystor's upriver landing: a jetty, a mooring post, a boathouse; the boat calls after "
                    "Q-C23."},
        {'id': 'zone:falagar_yard', 'name': "Falagar's yard", 'kind': 'district', 'part_of': 'zone:east_savannah',
         'floor': 1400, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': 'Falagar the Wizard (Q-C11) in a stone hut on a lava shoulder.',
         'buildings': [building('building:falagar_hut', "Falagar's Hut", [1.5, 1.5], notes='A4 house 4167.')]},
        {'id': 'zone:red_hills', 'name': 'The red dwarf hills', 'kind': 'wild', 'floor': [1200, 2400],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Red rock hills in the south-east: the Red Dwarf Mines' west adit (XD-02), the ogres' camp.",
         'population': [{'id': 'pop:red_hills', 'slot': 2, 'groups': 8, 'per_marker': [2, 3], 'levels': [18, 30],
                         'notes': 'Encounter area 3: Ogres.'},
                        {'id': 'pop:ogre_camp', 'actor': 'Xeen Ogre', 'groups': 1, 'placed': True, 'hostile': True,
                         'notes': 'Four placed at the camp to burn.'}]},
        {'id': 'water:river', 'name': 'The Great River (upper reach)', 'kind': 'water',
         'purpose': 'From the falls south to X2; crossed by the King\'s Bridge.'},
        {'id': 'water:falls_pool', 'name': 'The falls pool', 'kind': 'water', 'part_of': 'zone:falls',
         'purpose': 'Under the falls.'},
        # ---- junctions and edges ----
        {'id': 'junction:burlock_cross', 'name': 'Burlock Cross', 'kind': 'junction', 'signpost': True,
         'purpose': "King Burlock's statue: north the castle, east the bridge, west the desert, south-west Asp."},
        {'id': 'junction:east_fork', 'name': 'East fork', 'kind': 'junction', 'signpost': True,
         'purpose': "East of the King's Bridge: Firestone, the river road south."},
        {'id': 'junction:landing_fork', 'name': 'Landing fork', 'kind': 'junction', 'signpost': True,
         'purpose': "Nystor's landing, Rivercity, the castle."},
        {'id': 'junction:west_fork', 'name': 'West fork', 'kind': 'junction', 'signpost': True,
         'purpose': 'The desert road, the eyrie path north.'},
        {'id': 'junction:asp_gate', 'name': 'Asp gate', 'kind': 'junction', 'signpost': True,
         'purpose': 'The Travel Pit and the shrine, Asp, Burlock.'},
        {'id': 'edge:south_x2_end', 'name': 'South edge (X2)', 'kind': 'road', 'part_of': 'zone:east_savannah',
         'purpose': 'Where the Rivercity road leaves for X2.'},
        {'id': 'edge:south_x3_end', 'name': 'South edge (X3)', 'kind': 'road', 'part_of': 'zone:south_fields',
         'purpose': 'Where the Asp road leaves for X3.'},
        {'id': 'edge:west_end', 'name': 'West edge', 'kind': 'road', 'part_of': 'zone:west_downs',
         'purpose': 'Where the desert road leaves for X6.'},
        {'id': 'edge:east_end', 'name': 'East edge', 'kind': 'road', 'part_of': 'zone:east_savannah',
         'purpose': 'Where the Firestone road leaves for X7.'},
    ]
    links = [
        {'id': 'link:rivercity_road', 'from': 'edge:south_x2_end', 'to': 'junction:landing_fork', 'kind': 'road',
         'purpose': 'travel: X2 to the landing fork'},
        {'id': 'link:river_road', 'from': 'junction:landing_fork', 'to': 'junction:east_fork', 'kind': 'road',
         'notes': "Joe the Merchant's caravan halfway"},
        {'id': 'link:landing_lane', 'from': 'junction:landing_fork', 'to': 'zone:nystor_landing', 'kind': 'path'},
        {'id': 'link:bridge_road', 'from': 'junction:east_fork', 'to': 'junction:burlock_cross', 'kind': 'road',
         'crosses': ['water:river'], 'features': ["the King's Bridge, three stone arches over the river at x 78-83"]},
        {'id': 'link:kings_road', 'from': 'junction:burlock_cross', 'to': 'zone:burlock_square', 'kind': 'road',
         'rise': 300, 'notes': "past the lists to the village's south gate"},
        {'id': 'link:castle_lane', 'from': 'zone:burlock_square', 'to': 'town:burlock_castle', 'kind': 'path'},
        {'id': 'link:firestone_road', 'from': 'junction:east_fork', 'to': 'edge:east_end', 'kind': 'road',
         'purpose': 'travel: X7'},
        {'id': 'link:falagar_lane', 'from': 'link:firestone_road', 'to': 'zone:falagar_yard', 'kind': 'path'},
        {'id': 'link:lava_track', 'from': 'zone:falagar_yard', 'to': 'zone:lava_fields', 'kind': 'path',
         'notes': 'past the Shrine of Fire to the rim lookout'},
        {'id': 'link:adit_lane', 'from': 'link:rivercity_road', 'to': 'zone:red_hills', 'kind': 'path',
         'notes': "to XD-02's west adit"},
        {'id': 'link:asp_road', 'from': 'junction:burlock_cross', 'to': 'zone:asp_square', 'kind': 'road',
         'notes': 'by the Asp gate, the Travel Pit and the shrine'},
        {'id': 'link:x3_road', 'from': 'zone:asp_square', 'to': 'edge:south_x3_end', 'kind': 'road',
         'purpose': 'travel: X3'},
        {'id': 'link:west_road', 'from': 'edge:west_end', 'to': 'junction:burlock_cross', 'kind': 'road',
         'purpose': 'travel: X6', 'notes': 'by the west fork and the obelisk knoll'},
        {'id': 'link:eyrie_path', 'from': 'junction:west_fork', 'to': 'zone:gargoyle_range', 'kind': 'path',
         'rise': 700, 'notes': "past Carlawna's hut to the eyrie mouth"},
        {'id': 'link:druid_path', 'from': 'link:west_road', 'to': 'zone:druid_grove', 'kind': 'path'},
        {'id': 'link:falls_path', 'from': 'town:burlock', 'to': 'zone:falls', 'kind': 'path',
         'notes': 'from the east gate up the river to the Olympian Fountain'},
        {'id': 'link:quintain_track', 'from': 'junction:burlock_cross', 'to': 'zone:south_fields', 'kind': 'path'},
        {'id': 'link:barbarian_track', 'from': 'link:west_road', 'to': 'zone:uplands', 'kind': 'path',
         'notes': 'to the barbarian camp'},
    ]
    entrances = [
        {'id': 'entrance:x2_road', 'space': 'edge:south_x2_end', 'kind': 'both', 'neighbour': 'edge:south_x2',
         'facing': 'n', 'how': 'The Rivercity road up from the river gorge; the landing and the river valley ahead.'},
        {'id': 'entrance:x3_road', 'space': 'edge:south_x3_end', 'kind': 'both', 'neighbour': 'edge:south_x3',
         'facing': 'n', 'how': "The Asp road from the lagoon's north edge."},
        {'id': 'entrance:west_road', 'space': 'edge:west_end', 'kind': 'both', 'neighbour': 'edge:west',
         'facing': 'e', 'how': 'The desert road over the saddle.'},
        {'id': 'entrance:east_road', 'space': 'edge:east_end', 'kind': 'both', 'neighbour': 'edge:east',
         'facing': 'w', 'how': 'The Firestone road below the lava fields.'},
        {'id': 'entrance:burlock_square', 'space': 'zone:burlock_square', 'kind': 'arrival',
         'how': 'Town Portal and the mirror (4157, qbit 119003).'},
        {'id': 'entrance:burlock_stables', 'space': 'town:burlock', 'kind': 'arrival',
         'neighbours': ['stable:burlock_vertigo', 'stable:burlock_rivercity'], 'how': "The stables' yard."},
        {'id': 'entrance:asp_travel_pit', 'space': 'town:asp', 'kind': 'arrival',
         'neighbours': ['stable:asp_rivercity'], 'how': 'The Travel Pit at the east edge.'},
        {'id': 'entrance:asp_square', 'space': 'zone:asp_square', 'kind': 'arrival',
         'how': "Asp's mirror (4177, after q-c5.done)."},
        {'id': 'entrance:river_landing', 'space': 'zone:nystor_landing', 'kind': 'both', 'neighbour': 'boat:nystor',
         'how': "Nystor's boat, after Q-C23."},
        {'id': 'entrance:xd07_gate', 'space': 'town:burlock_castle', 'kind': 'both', 'neighbour': 'door:xd07',
         'facing': 'n', 'how': "The castle gate at the top of the castle lane."},
        {'id': 'entrance:throne_landing', 'space': 'town:burlock_castle', 'kind': 'arrival',
         'neighbour': 'fall:xd07_throne',
         'how': "A fall: the party appears at ground + 1,000 beside the west tower, outside the walls, and drops "
                "(ordinary fall damage; D-4)."},
        {'id': 'entrance:xd25_stair', 'space': 'zone:asp_square', 'kind': 'both', 'neighbour': 'door:xd25',
         'facing': 'n', 'how': 'A stone-framed cellar stair on the square, the rule stone beside it.'},
        {'id': 'entrance:xd26_eyrie', 'space': 'zone:gargoyle_range', 'kind': 'both', 'neighbour': 'door:xd26',
         'facing': 's', 'how': "A dark mouth in Gargoyle Peak's south face, bones below it."},
        {'id': 'entrance:xd26_sky_crack', 'space': 'zone:gargoyle_range', 'kind': 'arrival',
         'neighbour': 'door:xd26_sky_crack',
         'how': "XD-26's sky crack: a one-way exit onto a ledge at about 3,300 on Gargoyle Peak, the whole savannah "
                "below; a goat path down to the eyrie mouth."},
        {'id': 'entrance:xd02_adit', 'space': 'zone:red_hills', 'kind': 'both', 'neighbour': 'door:xd02_adit',
         'facing': 'e', 'condition': {'qbit': 'x4_adit_open'},
         'how': "A timbered adit in the red rock, a winch frame beside it; a rock fall until M3's winch."},
    ]
    pois = [
        {'id': 'poi:obelisk', 'space': 'zone:uplands', 'kind': 'obelisk', 'rule': 'native:obelisk',
         'behaviour': "One of Cloudside's obelisks: a word of the world's riddle.",
         'notes': 'On a knoll north of the desert road, the castle in view.'},
        {'id': 'poi:well_might', 'space': 'zone:burlock_square', 'kind': 'well',
         'behaviour': 'Well of Might: +Might, temporary.', 'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:olympian_fountain', 'space': 'zone:falls', 'kind': 'fountain',
         'behaviour': 'The Olympian Fountain: +2 Might, permanent, once (the permanent device).',
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:jousting_lists', 'space': 'zone:lists', 'kind': 'stat_challenge', 'rule': 'native:stat_challenge',
         'behaviour': "Ride a tilt against the lists' champion: a Might and Speed check (A2 sets the threshold); "
                      "success gives +2 Accuracy, permanent, once (the map's stat challenge).",
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:carlawna', 'space': 'zone:carlawna_yard', 'kind': 'npc',
         'behaviour': "Carlawna the Cleric (4303): the gargoyles stole her Scarab of Imaging (Q-C10); T1-C."},
        {'id': 'poi:falagar', 'space': 'zone:falagar_yard', 'kind': 'npc',
         'behaviour': 'Falagar the Wizard (4304): the Crystals of Piezoelectricity (Q-C11).'},
        {'id': 'poi:joe_caravan', 'space': 'zone:east_savannah', 'kind': 'teacher',
         'behaviour': "Joe the Merchant (4320) at his caravan on the river road: Merchant teacher.",
         'notes': 'A covered wagon, two mules, crates; outdoors, no door.'},
        {'id': 'poi:barbarian_camp', 'space': 'zone:uplands', 'kind': 'camp',
         'behaviour': "The barbarian camp by the desert road: burn it (XP); the chief's chest (a chest)."},
        {'id': 'poi:nystor_landing', 'space': 'zone:nystor_landing', 'kind': 'set_piece',
         'behaviour': "Captain Nystor's upriver landing: a jetty and a boathouse; his boat calls after Q-C23."},
        {'id': 'poi:autumn_druid', 'space': 'zone:druid_grove', 'kind': 'npc',
         'behaviour': "The Autumn Druid (4321): Q-C1's Autumn step; T1-C after q-c10.done."},
        {'id': 'poi:asp_well', 'space': 'zone:asp_square', 'kind': 'well',
         'behaviour': "Asp's well: the centre of the pedestal ring (Q-C5); a plain well (no effect)."},
        {'id': 'poi:pedestals', 'space': 'zone:asp_square', 'kind': 'set_piece', 'count': 8,
         'behaviour': "Eight two-colour pedestals round Asp's well (D-4, XD-25 1): each turns red or blue on touch; "
                      "solved when the south-west one (index 1) and every second one round the ring are red; sets "
                      "the pedestals qbit (one qbit across X4 and XD-25).",
         'notes': 'A ring of radius 1.6 cells (about 820) round the well; a clear walking line to every door.'},
        {'id': 'poi:rule_stone', 'space': 'zone:asp_square', 'kind': 'sign',
         'behaviour': "The rule stone by the undercroft stair (q-c5.pedestal_rhyme): \"The southwest corner is where "
                      "to start / Begin with red to tell them apart. Alternate the colors around the well / Then the "
                      "machine can no longer repel.\""},
        {'id': 'poi:burlock_mirror', 'space': 'zone:burlock_square', 'kind': 'mirror',
         'behaviour': 'The Mirror of Castle Burlock (A4 4157, qbit 119003): a transport mirror and the Town Portal '
                      'anchor.'},
        {'id': 'poi:asp_mirror', 'space': 'zone:asp_square', 'kind': 'mirror',
         'behaviour': "The Mirror of Asp (A4 4177, qbit 119013): fogged with shed skin until q-c5.done; set against "
                      "the south row's gable, clear of the doors."},
        {'id': 'poi:adam_eve', 'space': 'zone:asp_square', 'kind': 'npc', 'count': 2,
         'behaviour': 'Adam (4301) and Eve (4302) by the well: Q-C5 (Curse, Transformer).'},
        {'id': 'poi:king_statue', 'space': 'junction:burlock_cross', 'kind': 'statue',
         'behaviour': "King Burlock's statue at the cross: a plaque (\"Don't worry, be happy.\" stays inside the "
                      "castle; this one names the roads)."},
        {'id': 'poi:shrine_fire', 'space': 'zone:lava_fields', 'kind': 'shrine',
         'behaviour': 'Shrine of Fire among the vents: +Fire resistance, permanent, once.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:rim_lookout', 'space': 'zone:lava_fields', 'kind': 'ruin',
         'behaviour': "A broken watch post where the range meets the rim: the stars below; an old note."},
        {'id': 'poi:quintain_field', 'space': 'zone:south_fields', 'kind': 'device',
         'behaviour': 'A quintain on a post: tilt at it for +Accuracy, temporary, daily.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:herders_well', 'space': 'zone:south_fields', 'kind': 'well',
         'behaviour': "Herders' well by the Asp road: +Endurance, temporary.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:wayfarers_well', 'space': 'zone:east_savannah', 'kind': 'well',
         'behaviour': "Wayfarers' well on the Firestone road: +Speed, temporary.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:dwarf_stone', 'space': 'zone:red_hills', 'kind': 'sign',
         'behaviour': 'A red boundary stone: "Here begin the hills of the Red Dwarves. Mind the adits."'},
        {'id': 'poi:asp_cemetery', 'space': 'zone:west_downs', 'kind': 'ruin',
         'behaviour': "Asp's old cemetery, snake-skins on the graves; a sexton's chest (a chest)."},
        {'id': 'poi:ogre_camp', 'space': 'zone:red_hills', 'kind': 'camp',
         'behaviour': "The ogres' camp in a hollow: burn it (XP); a chest of loot."},
        {'id': 'poi:knights_camp', 'space': 'zone:south_fields', 'kind': 'camp',
         'behaviour': "The renegade knights' camp: torn pavilions, a broken lance rack; burn it (XP); their chest."},
        {'id': 'poi:gargoyle_roost', 'space': 'zone:gargoyle_range', 'kind': 'chest',
         'behaviour': "A gargoyle roost on a ledge above the falls: a heap of stolen shiny things (a chest)."},
        {'id': 'poi:saddlebags', 'space': 'zone:south_fields', 'kind': 'chest',
         'behaviour': "A fallen charger's saddlebags in the grass: a jouster who did not come back (a chest)."},
        {'id': 'poi:champions_barrow', 'space': 'zone:south_fields', 'kind': 'chest',
         'behaviour': "The champions' barrow: old jousters' grave goods (a chest)."},
        {'id': 'poi:sunken_barge', 'space': 'water:river', 'kind': 'chest',
         'behaviour': 'A river barge aground on a sandbar, its cargo box still aboard (a chest).'},
        {'id': 'poi:ore_cart', 'space': 'zone:red_hills', 'kind': 'chest',
         'behaviour': "The dwarves' ore cart left outside the caved-in adit (a chest)."},
        {'id': 'poi:burned_caravan', 'space': 'zone:lava_fields', 'kind': 'chest',
         'behaviour': 'A caravan that tried the short cut over the lava: charred wagon, a strongbox (a chest).'},
        {'id': 'poi:mill_ruin', 'space': 'zone:east_savannah', 'kind': 'ruin',
         'behaviour': "A burnt-out watermill on the river's east bank, its wheel still in the race: the miller's "
                      "last ledger (a note: gargoyles came down from the falls)."},
        {'id': 'poi:bridge_cairn', 'space': 'zone:castle_fields', 'kind': 'device',
         'behaviour': "D-11.5: a cairn of river stones at the King's Bridge's west end; add a stone: +Luck, temporary.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:savannah_well', 'space': 'zone:east_savannah', 'kind': 'well',
         'behaviour': "D-11.5: a herders' well under an acacia: +Might, temporary.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:standing_stone', 'space': 'zone:west_downs', 'kind': 'device',
         'behaviour': 'D-11.5: a lone standing stone on the downs, warm in the sun: +Personality, temporary.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:jousters_grave', 'space': 'zone:south_fields', 'kind': 'device',
         'behaviour': "D-11.5: a jouster's grave under his broken lance: an epitaph; +Accuracy, temporary.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:eyrie_waystone', 'space': 'zone:uplands', 'kind': 'sign',
         'behaviour': "D-11.5: a waystone on the eyrie path: Carlawna's hut below, the eyrie above, a warning."},
        {'id': 'poi:red_waymark', 'space': 'zone:east_savannah', 'kind': 'device',
         'behaviour': 'D-11.5: a red waymark stone of the dwarves: +Endurance, temporary.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:signposts', 'spaces': SIGNPOSTS, 'kind': 'signpost', 'count': 5,
         'behaviour': 'Signposts at the forks.'},
    ]
    landmarks = [
        {'id': 'landmark:castle_burlock', 'space': 'town:burlock_castle',
         'what': 'White castle of four towers and a keep on its rise, banners, the range behind',
         'seen_from': ['zone:south_fields', 'zone:castle_fields', 'zone:uplands', 'zone:east_savannah',
                       'junction:burlock_cross']},
        {'id': 'landmark:gargoyle_peak', 'space': 'zone:gargoyle_range',
         'what': 'The highest peak of the range (3,900), the eyrie in its face', 'seen_from': ['zone:uplands',
                                                                                            'zone:west_downs',
                                                                                            'town:asp']},
        {'id': 'landmark:falls', 'space': 'zone:falls', 'what': 'The river falling out of the range',
         'seen_from': ['town:burlock', 'zone:east_savannah', 'junction:east_fork']},
        {'id': 'landmark:kings_beacon', 'space': 'zone:gargoyle_range',
         'what': "The King's beacon: a signal tower of white stone on the crest above the castle, lit when "
                 "gargoyles fly", 'seen_from': ['zone:castle_fields', 'zone:south_fields', 'town:burlock']},
        {'id': 'landmark:lava_fields', 'space': 'zone:lava_fields', 'what': 'Smoke columns over black rock',
         'seen_from': ['zone:east_savannah', 'edge:east_end']},
        {'id': 'landmark:red_hills', 'space': 'zone:red_hills', 'what': 'Red rock hills',
         'seen_from': ['edge:south_x2_end', 'zone:east_savannah']},
    ]
    sightlines = [
        {'id': 'view:arrival', 'from': 'entrance:x2_road',
         'to': ['poi:nystor_landing', 'landmark:red_hills', 'landmark:gargoyle_peak'],
         'what': "Arrival from X2: the river valley, Nystor's landing, the red hills, the range on the horizon."},
        {'id': 'view:signature', 'from': 'zone:lists',
         'to': ['landmark:castle_burlock', 'poi:jousting_lists', 'landmark:gargoyle_peak'],
         'what': 'The signature view: the lists, the walled village and Castle Burlock on its rise, the Gargoyle '
                 'Range behind.'},
    ]
    set_pieces = [
        {'id': 'set:asp_pedestals', 'kind': 'puzzle', 'spaces': ['zone:asp_square'],
         'rule': 'Eight pedestals round the well, each red or blue on touch. Solved when the south-west one and '
                 'every second one round the ring are red (the rule stone\'s rhyme; Eve says it plainly).',
         'inputs': ['poi:pedestals'], 'states': ['unsolved', 'solved'],
         'solution': 'pedestals 1, 3, 5, 7 red; 2, 4, 6, 8 blue',
         'gives': {'qbit': 'asp_pedestals'}},
    ]
    states = [
        {'id': 'state:asp_cursed', 'condition': {'not': {'qbit': 'asp_liberated'}},
         'locks': ['building:asp_alchemist', 'building:asp_armour', 'building:asp_guild_earth',
                   'building:asp_guild_body'],
         'atmosphere': 'Empty streets, hissing behind doors, snake-skins on the sills, a few snakes on the square.',
         'notes': "A4's closed texts; the Travel Pit, the shrine and Sarah Slither (asp_houses 1) stay open; the "
                  "other houses (asp_houses 2-10) are closed too."},
        {'id': 'state:asp_liberated', 'condition': {'qbit': 'asp_liberated'},
         'opens': ['building:asp_alchemist', 'building:asp_armour', 'building:asp_guild_earth',
                   'building:asp_guild_body', 'building:asp_houses'],
         'effects': ['Townsfolk about (about 8), the mirror works (qbit 119013).']},
    ]
    totals = {
        'hostiles_at_load': hostiles,
        'encounter_areas': len(AREAS),
        'spawn_markers': markers,
        'outdoor_chests': 9,
        'points_of_interest': len(pois) - 1 + 5,
        'dungeon_entrances': 4,
    }
    return {
        'format': 0,
        'level': 'L1',
        'pitch': "The north-centre of Cloudside: a warm, rolling savannah under the Gargoyle Range, whose bare peaks "
                 "end in the world's north rim. Castle Burlock, the royal seat, stands white on a rise at the range "
                 "foot, its walled village below the gate and the jousting lists below that. The Great River falls "
                 "out of the range beside the castle and runs south to Rivercity past Captain Nystor's landing. "
                 "South-west lies Asp, a small town whose people are turning into snakes; west, dry downs toward "
                 "the desert; south-east, the red dwarf hills; north-east, lava fields smoking toward Mount Firestone.",
        'purpose': "Act II's royal map (party 11-15): the audience at Castle Burlock (M5, XD-07), Asp's curse (Q-C5, "
                   "XD-25), the gargoyles' eyrie (Q-C10, XD-26), Falagar's crystals (Q-C11), the Autumn Druid "
                   "(Q-C1), the dwarves' adit (M3's shortcut from X1), stables and Nystor's boat as travel.",
        'mood': 'Dry gold grass, wide sky, a fair breeze; banners over the white castle; Asp silent and wrong; the '
                'range grey and sharp in the north.',
        'datum': 'water:rim_sea',
        'spaces': spaces,
        'links': links,
        'entrances': entrances,
        'critical_path': ['edge:south_x2_end', 'junction:landing_fork', 'junction:east_fork',
                          'junction:burlock_cross', 'zone:burlock_square', 'town:burlock_castle'],
        'goals': [
            {'id': 'goal:audience', 'space': 'town:burlock_castle', 'kind': 'reach',
             'what': 'Enter Castle Burlock as Crusaders: the audience (M5).', 'story': 'M5'},
            {'id': 'goal:asp', 'space': 'zone:asp_square', 'kind': 'set',
             'what': 'Set the pedestals; break the transformer in XD-25 (Q-C5).', 'story': 'Q-C5'},
            {'id': 'goal:scarab', 'space': 'zone:carlawna_yard', 'kind': 'use',
             'what': "Bring Carlawna her scarab from the eyrie (Q-C10).", 'story': 'Q-C10'},
            {'id': 'goal:crystals', 'space': 'zone:falagar_yard', 'kind': 'use',
             'what': "Bring Falagar the crystals from under Asp (Q-C11).", 'story': 'Q-C11'},
            {'id': 'goal:autumn', 'space': 'zone:druid_grove', 'kind': 'use',
             'what': "Carry the Summer flower to the Autumn Druid (Q-C1).", 'story': 'Q-C1'},
        ],
        'points_of_interest': pois,
        'landmarks': landmarks,
        'sightlines': sightlines,
        'set_pieces': set_pieces,
        'height_bands': [
            {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
            {'id': 'band:low', 'range': [650, 1400],
             'spaces': ['zone:west_downs', 'zone:castle_fields', 'zone:south_fields', 'zone:east_savannah',
                        'town:asp', 'water:river']},
            {'id': 'band:mid', 'range': [1100, 1950],
             'spaces': ['zone:uplands', 'town:burlock_castle', 'town:burlock']},
            {'id': 'band:high', 'range': [1300, 2400], 'spaces': ['zone:lava_fields', 'zone:red_hills']},
            {'id': 'band:peaks', 'range': [1300, 3900], 'spaces': ['zone:gargoyle_range']},
        ],
        'states': states,
        'landform': {
            'relief': 'A river valley (650) through rolling savannah (850-1,150) rising north to the castle rise '
                      '(1,900) and the Gargoyle Range (to 3,900, ending in the rim cliff); red dwarf hills to 2,400 '
                      'in the south-east, lava fields 1,500-1,900 in the north-east.',
            'height_range': [650, 3900],
            'water': 'The river (about 3 cells wide, 87 cells long), the falls pool.',
            'water_share': 0.03,
            'caps': [{'kind': 'bare rock', 'share': 0.18, 'where': 'the Gargoyle Range and the red hills'},
                     {'kind': 'lava rock', 'share': 0.05, 'where': 'the north-east lava fields'}],
            'rim': {'notes': 'The world rim along the whole north edge: the range breaks off in a cliff of '
                             '2,000-3,500 above the stars. West, south and east the land runs to the map edge; the '
                             'roads and the river run out to it.'},
        },
        'atmosphere': 'Sky fair (shipped), a dry tint; music 29. Wind in the grass, the falls\' roar near the '
                      'castle, horses and a herald\'s trumpet at the lists; Asp: hissing and a loose shutter; '
                      'the lava fields hiss and rumble.',
        'sketch': {'file': 'sketch.yml', 'grid': 512},
        'totals': totals,
        'notes': 'MU-3 for gate G1 (A5, 2026-11-20). Source geography: Clouds C1, C2, D1, D2 (MAPS X4). Drawing and '
                 'review board: output/studio_cal/x4/mockups/. Generated by output/studio_cal/x4/tools/gen_l1.py.',
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write('project.yml', PROJECT)
    write('plan.yml', plan())
    write('sketch.yml', sketch())
    print('written', OUT)


if __name__ == '__main__':
    main()
