#!/usr/bin/env python3
"""X6 Desert of the Sphinx: the L1 brief (MU-3 plan) for the phase 4 review (A5, 2026-11-20).

    gen_l1.py [--with-census]     writes devdocs/xeen/briefs/x6/L1/{project,plan,sketch}.yml

Then `oymap fmt` and `oymap validate --assets assets_dev` (run.sh does all three, the drawings and the board). Later
passes edit this script, not the YAML. Cells are [x, y] on the 128-cell grid (512 units), x east, y south.
Form after D3's L1 (level_generation/projects/xeen/d3/gen_l1.py) and X4's.

Source geography: Clouds A1 (north-west: Castle Basenji, Arie, the Air corner), B1 (north-east: the Northern Sphinx),
A2 (south-west: the Southern Sphinx, Saul) and B2 (south-east: the Barbaric Mountains, the Warzone gate, the Summer
Druid). Each source area is 16 x 16 tiles of 2,048 units; here they are pressed into the land inside the rims.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'devdocs/xeen/briefs/x6/L1'

# ---------------------------------------------------------------- the edges, rims and crossings
RIM_X = 24           # the west rim: X5's west rim is at x 24 too (X5 L4 frame), so the cliff runs on unbroken
RIM_Y = 24           # the north rim: X4's north rim is at y 24 (X4 L4 frame)
EAST_Y = 60          # X4's west road reaches its x 0 at y 60 (level span 54-66 at 1,150): the same y here
SOUTH_X = 50         # X5's steppe road reaches its y 0 at x 50 (level span 45-56 at 1,460): the same x here
WELLS = [61.5, 61.5]  # Sphinx Wells' well, the middle of the caravan stop
FORK = [55.5, 61.5]   # the wells fork west of the hamlet

# ---------------------------------------------------------------- project.yml
SLOTS = [
    {'monster': 'Xeen Sand Worm', 'tier': 2, 'per_marker': [2, 3], 'weight': 37},
    {'monster': 'Xeen Werewolf', 'tier': 4, 'per_marker': [2, 3], 'weight': 30},
    {'monster': 'Xeen Elemental Golem', 'tier': 2, 'per_marker': [2, 3], 'weight': 33},
]

PROJECT = {
    'format': 0,
    'id': 'xeen_x6',
    'name': 'Desert of the Sphinx',
    'world': 'xeen',
    'kind': 'outdoor',
    'profile': 'odm',
    'map_code': 'X6',
    'units': {'plan_grid': 512},
    'extent': {'terrain_cells': 128},
    'map_stats': {
        'id': 9104,
        'continent': 6,
        'encounter_chance': 10,
        'treasure_level': 3,
        'trap_dice': 4,
        'perception_difficulty': 4,
        'refill_days': 672,
        'music': 17,
        'environment': 'desert',
        'lock_difficulty': 8,
        'slots': SLOTS,
    },
    'neighbours': [
        {'id': 'edge:east', 'to': 'xeen_x4.odm', 'kind': 'edge', 'side': 'east', 'days': 5, 'arrival_side': 'west',
         'approach': f'The desert road in from the east edge at y {EAST_Y}, over the dry downs from the Asp road.',
         'notes': "X4 Burlock Savannah (installed): its west road (L4 link:west_road) runs out to its x 0 at y 60 over "
                  "the desert road's saddle (level span 54-66 at 1,150), sealed until X6 exists. The same y here and "
                  "the same span and height; X4's other west spans continue (Gargoyle Range 0-50, dry downs 66-128)."},
        {'id': 'edge:south', 'to': 'xeen_x5.odm', 'kind': 'edge', 'side': 'south', 'days': 5, 'arrival_side': 'north',
         'approach': f'The steppe road in from the south edge at x {SOUTH_X}, up from Winterkill\'s steppe.',
         'notes': "X5 Winterkill Tundra (A6, installed): its steppe road runs out to its y 0 at x 50 (level span 45-56 "
                  "at 1,460), sealed with a sign until X6 exists. The same x here; X5's other north spans continue "
                  "(rim 0-24, stony rises 24-45, the Frostspine and Ogre Hills' backs 56-128)."},
        {'id': 'door:xd14', 'to': 'xeen_xd14.blv', 'kind': 'door',
         'arrival_hint': "Inside Castle Basenji's gate, in its entry hall.",
         'notes': "XD-14 Castle Basenji (A7, phase 4; Q-C8): the castle on its crag at the north rim, its gate at the "
                  "top of the cliff path above Arie's camp. Sealed until XD-14 exists."},
        {'id': 'door:xd15', 'to': 'xeen_xd15.blv', 'kind': 'door', 'condition': {'item': 'northern_sphinx_amulet'},
         'arrival_hint': "Inside the Sphinx's breast, at the foot of the stair to the body.",
         'notes': "XD-15 The Sphinx (A7, phase 4; Q-C9): the door between the Northern Sphinx's paws. A3's q-c9.door "
                  "wants the Jewelled Amulet (12317, Arie's). Sealed until XD-15 exists."},
        {'id': 'door:xd20', 'to': 'xeen_xd20.blv', 'kind': 'door',
         'arrival_hint': 'Inside the arena gate, in the fighters\' passage.',
         'notes': "XD-20 The Warzone (A7, phase 4; D-8.1): the arena gate in the cliff at the back of the walled coach "
                  "yard. \"Enter the War Zone?\" Sealed until XD-20 exists."},
        {'id': 'door:fd02', 'to': 'xeen_fd02.blv', 'kind': 'door', 'condition': {'item': 'southern_sphinx_amulet'},
         'arrival_hint': "Inside the Southern Sphinx's breast, on the first step.",
         'notes': "FD-02 The Southern Sphinx (A7, phase 6; M40): a second, half-buried sphinx in the western dunes; "
                  "A3's m40.sphinx_door wants Roland's amulet (12372). Sealed until FD-02 exists."},
        {'id': 'stable:sphinx_wells_asp', 'to': 'xeen_x4.odm', 'kind': 'stable', 'days': 2,
         'schedule': {'weekdays': ['monday', 'friday']}, 'service': 'Sphinx Wells Caravans (4302), route 427',
         'notes': "A4's x6.yml: to Asp's Travel Pit; Asp's route 431 lands here (arrival sphinx_wells)."},
        {'id': 'stable:sphinx_wells_rivercity', 'to': 'xeen_x2.odm', 'kind': 'stable', 'days': 4,
         'schedule': {'weekdays': ['wednesday']}, 'service': 'Sphinx Wells Caravans (4302), route 428',
         'notes': "A4's x6.yml: to Rivercity's stables."},
        {'id': 'stable:warzone_rivercity', 'to': 'xeen_x2.odm', 'kind': 'stable', 'days': 4,
         'schedule': {'weekdays': ['monday']}, 'service': 'The Warzone Coach (4305), route 429',
         'notes': "A4's x6.yml: Gorm's coach back to Rivercity; Rivercity's 406 lands at warzone_coach."},
        {'id': 'stable:warzone_castleview', 'to': 'xeen_d1.odm', 'kind': 'stable', 'days': 5,
         'schedule': {'weekdays': ['tuesday']}, 'condition': {'qbit': 'm7_sigil'},
         'service': 'The Warzone Coach (4305), route 430',
         'notes': "D-8.1: the coach to Castleview, a way between the faces, waits for the Pyramid Sigil (m7.sigil); "
                  "Castleview's 415 lands at warzone_coach."},
    ],
    'qbits': {
        # A3's bits (source/quests/*.yml); the names here are the map's.
        'warzone_gate': 116100,       # x6.warzone_gate: the coach yard's desert gate opened from the desert side
        'sphinx_entered': 112180,     # q-c9.entered: the Northern Sphinx's door opened to the amulet
        'q_c8_done': 112163,          # q-c8.done: Arie gave the Jewelled Amulet
        'summer_given': 112021,       # q-c1.summer: the Summer Druid gave the Last Flower of Summer
        'reflector_air': 111740,      # m37.air
        'm36_started': 111720,        # the Reflectors wake only after M36 starts (m37.reflector_air requires it)
        'cloud_6': 115045,            # obelisks.x6 (THE)
        'cloud_hoard_found': 115048,  # obelisks.cloud_hoard: the iron box before the Sphinx
        'm7_sigil': 110100,           # the Pyramid Sigil: the coach to Castleview
    },
    'items': {
        'northern_sphinx_amulet': 12317,
        'southern_sphinx_amulet': 12372,
    },
    'rules': {
        'weather': 'clear',
        'town_portal_anchor': 'entrance:sphinx_wells',
        'rim': {'sides': ['west', 'north'], 'cliff_x': RIM_X, 'cliff_y': RIM_Y, 'fall': 'death'},
    },
    'notes': 'X6 Desert of the Sphinx, MU-3 plan for the phase 4 review (A5, 2026-11-20). No geometry until a decider '
             'has approved it. Plan: plan.yml; to-scale layout: sketch.yml; generator, drawings and review board: '
             'output/studio_cal/x6/ (tools/gen_l1.py writes these three files). Sky: the shipped clear preset with '
             'the arid theme (as Bracada 7out06 and Dragonsand outb3).',
}

# ---------------------------------------------------------------- the land: zones and bands
ZONES = {
    'zone:rim': [[0, 0], [128, 0], [128, RIM_Y], [RIM_X, RIM_Y], [RIM_X, 128], [0, 128]],
    'zone:basenji_heights': [[RIM_X, RIM_Y], [58, RIM_Y], [58, 32], [54, 37], [46, 38], [36, 38], [RIM_X, 42]],
    'zone:cliff_foot': [[RIM_X, 42], [36, 38], [46, 38], [54, 37], [58, 32], [60, 44], [62, 52], [56, 56],
                        [RIM_X, 56]],
    'zone:sphinx_desert': [[58, RIM_Y], [100, RIM_Y], [100, 50], [90, 54], [76, 54], [62, 52], [60, 44], [58, 32]],
    'zone:gargoyle_foothills': [[100, RIM_Y], [128, RIM_Y], [128, 54], [110, 56], [100, 50]],
    'zone:central_pan': [[RIM_X, 56], [56, 56], [62, 52], [76, 54], [90, 54], [100, 50], [110, 56], [128, 54],
                         [128, 66], [104, 66], [88, 64], [72, 68], [56, 70], [40, 70], [RIM_X, 68]],
    'zone:east_downs': [[88, 64], [104, 66], [128, 66], [128, 86], [108, 86], [96, 88], [88, 80]],
    'zone:ruin_fields': [[56, 70], [72, 68], [88, 64], [88, 80], [96, 88], [90, 90], [80, 90], [66, 92], [56, 88]],
    'zone:west_dunes': [[RIM_X, 68], [40, 70], [56, 70], [56, 88], [48, 100], [44, 110], [RIM_X, 110]],
    'zone:south_steppe': [[56, 88], [66, 92], [80, 90], [90, 90], [90, 128], [44, 128], [44, 110], [48, 100]],
    'zone:stony_rises': [[RIM_X, 110], [44, 110], [44, 128], [RIM_X, 128]],
    'zone:barbaric_mountains': [[90, 90], [96, 88], [108, 86], [128, 86], [128, 128], [90, 128]],
}

TOWNS = {
    'town:sphinx_wells': [[57, 57], [66, 57], [66, 65], [57, 65]],
    'zone:coach_yard': [[83, 92], [89, 92], [89, 98], [83, 98]],
    'zone:basenji_crag': [[33, 27], [44, 27], [44, 37], [33, 37]],
    'zone:arie_camp': [[43, 43], [48, 43], [48, 48], [43, 48]],
    'zone:oasis': [[37, 59], [45, 59], [45, 66], [37, 66]],
    'zone:saul_hermitage': [[28, 68], [33, 68], [33, 73], [28, 73]],
    'zone:sphinx_forecourt': [[78, 33], [87, 33], [87, 46], [78, 46]],
    'zone:southern_sphinx': [[31, 81], [39, 81], [39, 88], [31, 88]],
    'zone:druid_grove': [[68, 87], [73, 87], [73, 92], [68, 92]],
    'zone:air_corner': [[RIM_X, RIM_Y], [29, RIM_Y], [29, 29], [RIM_X, 29]],
}

BANDS = [
    ('band:rim_sea', 'zone:rim'),
    ('band:heights', 'zone:basenji_heights'),
    ('band:heights', 'zone:gargoyle_foothills'),
    ('band:peaks', 'zone:barbaric_mountains'),
    ('band:desert', 'zone:cliff_foot'),
    ('band:dunes', 'zone:sphinx_desert'),
    ('band:pan', 'zone:central_pan'),
    ('band:downs', 'zone:east_downs'),
    ('band:desert', 'zone:ruin_fields'),
    ('band:dunes', 'zone:west_dunes'),
    ('band:desert', 'zone:south_steppe'),
    ('band:downs', 'zone:stony_rises'),
    ('band:oasis', 'zone:oasis'),
]

HEIGHT_POINTS = [
    ([38, 31], 2750, "Castle Basenji's crag: the castle on its cliff at the north rim, 1,300 over the desert"),
    ([30, 30], 2500, None),
    ([50, 29], 2450, None),
    ([26, 26], 2350, 'the Air corner: a rock spit where the two rims meet; the Reflector'),
    ([30, 34], 2400, 'the Waters of Great Power on the heights'),
    ([52, 31], 2300, "the werewolves' den under the castle's east wall"),
    ([38, 37], 2600, "Castle Basenji's gate terrace at the cliff top"),
    ([45, 45], 1450, "Arie's camp at the cliff foot"),
    ([28, 54], 1450, 'the Shrine of Energy by the west rim'),
    ([69, 103], 1500, "the sun stones on the south steppe"),
    ([96, 57], 1180, 'a caravan cairn by the desert road'),
    ([41, 62], 1080, 'the oasis: palms round a pond (water 1,000)'),
    ([FORK[0], FORK[1]], 1240, 'the wells fork'),
    ([61, 61], 1250, 'Sphinx Wells: the caravan stop at the desert\'s wells'),
    ([66, 34], 2250, 'a red mesa'),
    ([70, 41], 2050, 'a red mesa'),
    ([75, 51], 1650, "the obelisk's red rock knoll"),
    ([82, 39], 1400, 'the Northern Sphinx lies in the dunes facing south'),
    ([94, 32], 1550, 'a wagon the dunes swallowed'),
    ([92, 44], 1600, None),
    ([104, 32], 2600, 'the Gargoyle Range\'s western foothills (X4\'s west edge 2,400-3,200 at y 24-50)'),
    ([115, 40], 3000, None),
    ([80, 61], 1200, 'the Sphinx fork on the desert road'),
    ([107, 60], 1150, "the X4 arrival (X4's edge span is level at 1,150)"),
    ([97, 74], 1900, 'a lone mesa in the dry downs'),
    ([104, 80], 1850, None),
    ([78, 76], 1500, 'the ruined caravanserai (sand golems)'),
    ([62, 81], 1350, 'the bone fields'),
    ([70, 90], 1450, "the Summer Druid's grove: a spring under olive trees"),
    ([86, 95], 1500, 'the Warzone coach yard against the Barbaric cliffs'),
    ([92, 95], 2600, 'the cliff over the arena gate'),
    ([98, 98], 3700, 'the Barbaric Mountains\' highest peak inside the playable square'),
    ([104, 92], 3300, None),
    ([94, 106], 3200, None),
    ([106, 104], 3500, None),
    ([99, 100], 2700, "a prospector's camp in a high notch"),
    ([52, 92], 1420, 'the Well of Accuracy by the steppe road'),
    ([SOUTH_X, 107], 1460, "the X5 arrival (X5's edge span is level at 1,460)"),
    ([30, 70], 1400, "Saul's hermitage and the urn"),
    ([35, 84], 1550, 'the Southern Sphinx, half buried in the western dunes'),
    ([28, 92], 1650, 'dunes pouring over the west rim'),
    ([26, 100], 1700, "an explorer's pack at the rim's lip"),
    ([34, 112], 2200, "the stony rises (X5's north edge 1,900-2,700 at x 24-45)"),
]

CLIFFS = [
    {'line': [[RIM_X, RIM_Y], [RIM_X, 70], [RIM_X, 128]], 'drop': 1400, 'down': 'right',
     'notes': 'The west rim (drawn north to south, the low side west, on the right): a cliff of 1,400-2,400 above the '
             'stars; dunes pour over its lip, sand streaming off in the wind (particles).'},
    {'line': [[128, RIM_Y], [60, RIM_Y], [RIM_X, RIM_Y]], 'drop': 1500, 'down': 'right',
     'notes': 'The north rim at y 24 (as X4\'s), drawn east to west, the low side north.'},
    {'line': [[RIM_X, 42], [36, 38], [46, 38], [54, 37], [57, 33]], 'drop': 1100, 'down': 'right',
     'notes': "Basenji's cliff: the heights drop 1,100 to the desert floor (drawn west to east, the low side south); "
             "the cliff path zigzags up it from Arie's camp to the castle gate."},
]

RIDGES = [
    {'line': [[27, 29], [33, 28], [44, 28], [56, 28]], 'height': 2550, 'width': 2, 'slope': 3,
     'notes': 'The Basenji heights along the north rim.'},
    {'line': [[102, 28], [108, 36], [116, 46], [124, 52]], 'height': 2900, 'width': 2, 'slope': 3,
     'notes': "The Gargoyle Range's western foothills (X4's Gargoyle Range goes on west)."},
    {'line': [[92, 92], [98, 98], [104, 104], [110, 112], [118, 120]], 'height': 3500, 'width': 2, 'slope': 3,
     'notes': 'The Barbaric Mountains: a broken crest from the coach yard\'s cliffs to the south-east corner.'},
]

OASIS_POND = {'id': 'water:oasis_pond', 'kind': 'pond', 'level': 1000,
              'polygon': [[39, 61], [42, 60], [44, 61], [44, 64], [41, 65], [38, 63]],
              'notes': 'The oasis pond: clear water under palms in a hollow of the pan; the only water on X6.'}
RIM_SEA = {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': ZONES['zone:rim'],
           'notes': 'Below the rims: stands for the stars.'}

ROADS = [
    ('link:desert_road', [[128, EAST_Y], [107, EAST_Y], [96, 60.5], [88, 61], [80, 61], [72, 61], [66, 61],
                          WELLS, FORK], 'road', 'road_pebbles'),
    ('link:steppe_road', [FORK, [54, 68], [52, 76], [SOUTH_X, 84], [SOUTH_X, 92], [SOUTH_X, 100], [SOUTH_X, 107],
                          [SOUTH_X, 128]], 'road', 'road_pebbles'),
    ('link:basenji_road', [FORK, [54, 56], [51, 51], [48, 47.5], [46, 46]], 'road', 'road_pebbles'),
    ('link:cliff_path', [[46, 46], [43, 44], [44.5, 42], [41, 40.5], [42, 39], [38.5, 37.5]], 'lane', None),
    ('link:reflector_path', [[38.5, 37.5], [33, 36], [30, 34.5], [28, 31], [26.5, 27.5]], 'lane', None),
    ('link:sphinx_track', [[80, 61], [81, 56], [82, 50], [82.5, 45]], 'lane', None),
    ('link:obelisk_path', [[81.3, 54.5], [78, 52.5], [75.5, 51.5]], 'lane', None),
    ('link:oasis_track', [FORK, [50, 62], [45, 62.5], [42.5, 62.8], [37, 65.5], [33, 69], [31.5, 70.5]], 'lane',
     None),
    ('link:shrine_path', [[42, 60.5], [36, 57.5], [29, 55]], 'lane', None),
    ('link:rim_track', [[SOUTH_X, 84], [45, 84.5], [39.5, 85]], 'lane', None),
    ('link:coach_track', [[SOUTH_X, 84], [56, 87], [62, 89], [68, 90.5], [74, 93], [80, 95.3], [83, 96.5]], 'lane',
     None),
]

# ---------------------------------------------------------------- buildings and plots
# Sphinx Wells (A4's x6.yml): (building id, service, A4 house, footprint [front, depth], at (top-left), facing,
# door_to, kit)
HAMLET = [
    ('building:x6_tavern', 'The Last Waterskin', 4301, [2.5, 2], [57.5, 58], 's', 'town:sphinx_wells', 'plaster'),
    ('building:x6_stables', 'Sphinx Wells Caravans', 4302, [2.5, 2], [62.5, 58], 's', 'town:sphinx_wells', 'poor'),
]
HAMLET_HOUSES = [  # x6_houses#1-2 = 4303 the Well Keeper's House (Old Ibb), 4304 the Saddle Loft (Tansy)
    (4303, [1.5, 1], [58, 62.5], 'n', 'poor'),
    (4304, [1, 1], [63, 62.5], 'n', 'poor'),
]
COACH = ('building:warzone_coach', 'The Warzone Coach', 4305, [2.5, 1.5], [84, 92.5], 's', 'zone:coach_yard', 'stone')


# ---------------------------------------------------------------- points
POINTS = [
    # arrivals and edges
    ('entrance:east_road', [107, EAST_Y], 'w', 'Arrival from X4 Burlock Savannah (the desert road; X4 leaves at y 60).'),
    ('entrance:south_road', [SOUTH_X, 107], 'n', 'Arrival from X5 Winterkill Tundra (the steppe road; X5 leaves at x '
                                                 '50).'),
    ('entrance:sphinx_wells', [63, 61], 'w', "A4 arrival sphinx_wells: in front of the caravans' stables (Town "
                                             "Portal, routes 427, 428 and Asp's 431)."),
    ('entrance:warzone_coach', [86, 96], 'w', "A4 arrival warzone_coach: inside the walled coach yard (Rivercity's "
                                              "406, Castleview's 415)."),
    ('entrance:yard_gate', [83, 96], 'w', "The coach yard's desert gate (D-8.1): barred from inside until a party "
                                          "opens it from the desert side (x6.warzone_gate)."),
    ('entrance:xd14_gate', [38, 37], 's', "XD-14 Castle Basenji: the gate at the top of the cliff path."),
    ('entrance:xd15_door', [82, 44], 's', "XD-15 The Sphinx: the door between the Northern Sphinx's paws "
                                          "(q-c9.door, the Jewelled Amulet)."),
    ('entrance:xd20_gate', [88, 95], 'w', 'XD-20 The Warzone: the arena gate in the cliff at the back of the coach '
                                          'yard.'),
    ('entrance:fd02_door', [38, 85], 'e', "FD-02 The Southern Sphinx: a door in the half-buried sphinx's breast "
                                          "(m40.sphinx_door, Roland's amulet; phase 6)."),
    # junctions
    ('junction:wells_fork', FORK, None, None),
    ('junction:sphinx_fork', [80, 61], None, None),
    ('junction:south_fork', [SOUTH_X, 84], None, None),
    # places
    ('poi:obelisk', [75, 51], None, "On the red rock knoll west of the Sphinx track ('Obelisk of the Sphinx')."),
    ('poi:wells_well', [61, 61], None, "Old Ibb's well in the middle of Sphinx Wells."),
    ('poi:oasis_fountain', [41, 62], None, 'The oasis fountain at the pond (+2 Endurance, permanent).'),
    ('poi:well_accuracy', [51, 92], None, None),
    ('poi:shrine_energy', [28, 54], None, None),
    ('poi:sun_stones', [69, 103], None, None),
    ('poi:caravan_cairn', [96, 57], None, None),
    ('poi:waters_power', [30, 34], None, None),
    ('poi:air_reflector', [26, 26], None, 'The Air Reflector on the rock spit where the west and north rims meet '
                                          '(m37.reflector_air).'),
    ('poi:saul_urn', [31, 71], None, "Saul's urn, beside his hermitage."),
    ('poi:cloud_hoard', [82, 44], None, "A mound of sand between the Sphinx's paws (obelisks.cloud_hoard)."),
    # people outdoors (A4's NPCs without a house: places for the 6,000 rule, not POIs by D-20)
    ('poi:arie', [45, 45], None, "Arie the Apprentice (4608, Q-C8) at her camp below Castle Basenji."),
    ('poi:saul', [30, 70], None, 'Saul the Hermit (4602): Meditation Master, outdoors.'),
    ('poi:summer_druid', [70, 89], None, 'The Summer Druid (4601, Q-C1) in her grove.'),
    # chests with a reason
    ('poi:swallowed_wagon', [94, 32], None, None),
    ('poi:werewolf_den', [52, 31], None, None),
    ('poi:caravanserai', [78, 76], None, None),
    ('poi:bone_field', [62, 81], None, None),
    ('poi:rim_pack', [26, 100], None, None),
    ('poi:mesa_nest', [67, 35], None, None),
    ('poi:prospector_camp', [99, 100], None, None),
    # landmarks (no click)
    ('landmark:basenji', [38, 31], None, None),
    ('landmark:northern_sphinx', [82, 39], None, None),
    ('landmark:southern_sphinx', [34, 84], None, None),
    ('landmark:red_mesas', [68, 38], None, None),
    ('landmark:barbaric_mountains', [98, 98], None, None),
    ('landmark:sand_falls', [25, 88], None, 'Dunes pouring over the west rim, sand streaming off into the stars.'),
]
SIGNPOSTS = ['junction:wells_fork', 'junction:sphinx_fork', 'junction:south_fork']

# ---------------------------------------------------------------- monsters
# Encounter areas: (id, slot, markers, polygon, family note)
AREAS = [
    ('pop:sphinx_dunes', 1, 11, [[60, 30], [74, 27], [100, 27], [103, 44], [96, 51], [88, 52], [86, 47], [79, 47],
                                 [72, 47], [62, 46]],
     "Sand burrowers (Sand Worm 30, Armadillo 38, Great Worm 45) in the dunes round the Northern Sphinx and the red "
     "mesas; they surface by the Sphinx track. The obelisk's knoll and the desert road stay outside."),
    ('pop:west_dunes', 1, 9, [[26, 76], [40, 74], [47, 79], [48, 96], [42, 104], [26, 104]],
     'Sand burrowers in the western dunes round the Southern Sphinx, down to the rim; the first fight from X5.'),
    ('pop:basenji_heights', 2, 16, [[27, 25], [56, 25], [57, 33], [54, 37], [48, 38], [42, 37], [35, 38],
                                    [30, 40], [27, 47]],
     "Werewolves (Wolfman 20, Werewolf 30, Greater Werewolf 40) of the Basenji cult on the heights round the "
     "castle, the Waters of Great Power and the Air Reflector, and down the west slope; at least 2,000 from Arie's "
     "camp."),
    ('pop:east_downs', 3, 6, [[88, 66], [108, 65], [108, 84], [98, 85], [88, 81]],
     'Sand golems (Sand Golem 22, Water Golem 28, Cloud Golem 50) among the dry downs and the lone mesa; the first '
     'fight from X4.'),
    ('pop:ruin_fields', 3, 7, [[60, 72], [74, 69], [88, 66], [88, 80], [84, 84], [72, 84], [62, 84], [58, 78]],
     'Sand golems round the ruined caravanserai and the bone fields.'),
    ('pop:barbaric', 3, 5, [[96, 86], [109, 85], [109, 109], [76, 109], [78, 104], [94, 102]],
     "Sand golems in the Barbaric Mountains' notches round the prospector's camp; at least 2,500 from the coach "
     "yard."),
    # F10 (A5 s30, 2026-11-22): the west of the pan, the oasis and the cliff foot were one empty zone (empty_zones.py:
    # 601 tiles, deepest 11,192 at tile [45, 57]). Two single markers at fixed spots (gen.py FIXED_SPOTS), outside the
    # oasis, the central pan's quiet road and 12.5 cells (5,888 + the circle) from Arie and Saul.
    ('pop:pan_west', 1, 2, [[24, 50], [39, 50], [39, 55], [30, 59], [30, 61], [24, 61]],
     'Sand burrowers on the west of the pan, between the cliff foot, the Shrine of Energy and the oasis.'),
]
ACTORS = []   # no placed hostiles: everything is on markers
KEEP_CLEAR = [
    ('town:sphinx_wells', [[52, 53], [71, 53], [71, 69], [52, 69]],
     'The caravan stop with its buffer (about 2,500 round the doors and the arrival).'),
    ('zone:coach_yard', [[78, 87], [92, 87], [92, 103], [78, 103]],
     'D-8.1: the walled coach yard outside every encounter area, with its buffer.'),
    ('zone:arie_camp', [[41, 41], [50, 41], [50, 50], [41, 50]], "Arie's camp."),
    ('zone:saul_hermitage', [[27, 66], [34, 66], [34, 74], [27, 74]], "Saul's hermitage and the urn."),
    ('zone:druid_grove', [[66, 87], [75, 87], [75, 94], [66, 94]], "The Summer Druid's grove."),
    ('edge:east_end', [[102, 56], [110, 56], [110, 64], [102, 64]], 'The X4 arrival.'),
    ('edge:south_end', [[46, 103], [54, 103], [54, 110], [46, 110]], 'The X5 arrival.'),
]
OPEN = [
    ('zone:central_pan', [[52, 53], [100, 53], [104, 64], [88, 64], [72, 68], [56, 70], [45, 69], [36, 66], [30, 58],
                          [44, 52]],
     'The quiet pan of the caravan road: Sphinx Wells, the oasis, the obelisk knoll, the long view to the Sphinx.'),
    ('zone:oasis', [[36, 58], [46, 58], [46, 67], [36, 67]], 'The oasis: palms, the pond and the fountain.'),
]

VIEWS = [
    {'id': 'view:arrival', 'at': [106, EAST_Y], 'height': 200, 'look': [60, 50],
     'purpose': "MU-4 arrival view from X4's desert road just inside the east edge: west-north-west down the road "
                "over the pan to Sphinx Wells' palms; on the right the Northern Sphinx lying in the dunes and the red "
                "mesas; far ahead Castle Basenji on its cliff at the north rim; on the left the dry downs."},
    {'id': 'view:signature', 'at': [38, 96], 'height': 200, 'look': [26, 78],
     'purpose': "MU-4 signature view: from a dune crest in the rim dunes, north-west along the world's west rim: on "
                "the left the dunes pour over the edge into the stars, sand streaming off the lip in the wind; ahead "
                "right the Southern Sphinx buried to its shoulders; far off on the right Castle Basenji on its cliff "
                "over the north rim."},
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
    plots = []
    for bid, service, house, fp, at, facing, door_to, kit in HAMLET:
        plots.append({'building': bid, 'at': at, 'facing': facing, 'door_to': door_to, 'kit': kit, 'house': house})
        plot_rects.append((bid, at, fp, facing))
    for i, (house, fp, at, facing, kit) in enumerate(HAMLET_HOUSES, 1):
        plots.append({'building': 'building:x6_houses', 'index': i, 'at': at, 'facing': facing, 'kit': kit,
                      'house': house})
        plot_rects.append((f'x6_houses#{i}', at, fp, facing))
    districts.append({'space': 'town:sphinx_wells', 'polygon': TOWNS['town:sphinx_wells'], 'plots': plots,
                      'notes': "A4's x6.yml: the caravan stop at the desert's wells (WORLD_DESIGN 5.1 hamlet): the "
                               "tavern and the caravans' stables facing the road, two homes across it, Old Ibb's "
                               "well between, a camel pen behind the stables, palms (9 x 8 cells)."})
    bid, service, house, fp, at, facing, door_to, kit = COACH
    districts.append({'space': 'zone:coach_yard', 'polygon': TOWNS['zone:coach_yard'],
                      'plots': [{'building': bid, 'at': at, 'facing': facing, 'door_to': door_to, 'kit': kit,
                                 'house': house}],
                      'notes': "D-8.1: a walled pocket (6 x 6 cells) against the Barbaric cliffs holding only the "
                               "arena gate (XD-20, in the cliff) and Gorm's coach house (4305); its desert gate in "
                               "the west wall is barred from inside until opened from the desert side."})
    plot_rects.append((bid, at, fp, facing))
    for space in ['zone:basenji_crag', 'zone:arie_camp', 'zone:oasis', 'zone:saul_hermitage', 'zone:sphinx_forecourt',
                  'zone:southern_sphinx', 'zone:druid_grove', 'zone:air_corner']:
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

    out = {
        'format': 0,
        'grid': 512,
        'map_cells': 128,
        'notes': 'X6 Desert of the Sphinx, MU-3 to-scale plan (A5, 2026-11-20), for the phase 4 review: composition, '
                 'scale and density only. Cells [x, y], x east, y south. Heights in map units above the stars below '
                 'the rims (0): the oasis pond 1,000, the pan and Sphinx Wells 1,250, the desert floor and dunes '
                 '1,300-1,700, red mesas to 2,250, the Basenji heights 2,350-2,750 (Castle Basenji on its cliff), the '
                 'Barbaric Mountains to 3,700 in the south-east. West and north the land ends in the world rim (x 24, '
                 'y 24, as X5\'s west rim and X4\'s north rim). Generated by output/studio_cal/x6/tools/gen_l1.py; '
                 'the later L3 adds plots\' detail, ground, scatter and structures.',
        'frame': {
            'playable': [19, 19, 90, 90],
            'edges': [
                {'side': 'east', 'span': [54, 66], 'neighbour': 'edge:east',
                 'notes': f'The desert road runs out to x 128 at y {EAST_Y} (X4\'s west edge, the same y).'},
                {'side': 'south', 'span': [45, 56], 'neighbour': 'edge:south',
                 'notes': f'The steppe road runs out to y 128 at x {SOUTH_X} (X5\'s north edge, the same x).'},
            ],
            'rim': [
                {'side': 'west', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': f'The world rim: the land ends in a cliff at x {RIM_X}; below, water at 0 stands for the '
                          'stars; dunes pour over its lip.'},
                {'side': 'north', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': f'The world rim: the cliff at y {RIM_Y} (as X4\'s north rim); Castle Basenji stands over '
                          'it.'},
                {'side': 'east', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': "The north rim's east end (X4's north rim continues it)."},
                {'side': 'east', 'span': [24, 50], 'form': 'ridge', 'height': [2400, 3200], 'floor': 1600,
                 'crest': 10, 'roughness': 120, 'notes': "The Gargoyle Range (X4's west edge [0, 50])."},
                {'side': 'east', 'span': [50, 54], 'form': 'ridge', 'height': [1500, 1900], 'floor': 1300,
                 'crest': 10, 'roughness': 100, 'notes': "X4's edge [50, 54]."},
                {'side': 'east', 'span': [54, 66], 'form': 'level', 'height': 1150, 'meet': 6,
                 'notes': "The desert road's saddle, open to X4 (X4's edge [54, 66] is level at 1,150)."},
                {'side': 'east', 'span': [66, 86], 'form': 'ridge', 'height': [1500, 2200], 'floor': 1100,
                 'crest': 10, 'roughness': 100, 'notes': "Dry downs (X4's edge [66, 128])."},
                {'side': 'east', 'span': [86, 128], 'form': 'ridge', 'height': [1800, 2200], 'floor': 1400,
                 'crest': 10, 'roughness': 100,
                 'notes': "The Barbaric Mountains' east foot falls to X4's dry downs (X4's edge [66, 128] is "
                          "1,500-2,200)."},
                {'side': 'south', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': "The west rim's south end (X5's rim [0, 24] continues it)."},
                {'side': 'south', 'span': [24, 45], 'form': 'ridge', 'height': [1900, 2700], 'floor': 1500,
                 'crest': 10, 'roughness': 100, 'notes': "Stony rises (X5's north edge [24, 45])."},
                {'side': 'south', 'span': [45, 56], 'form': 'level', 'height': 1460, 'meet': 6,
                 'notes': "The steppe road's valley, open to X5 (X5's edge [45, 56] is level at 1,460)."},
                {'side': 'south', 'span': [56, 128], 'form': 'ridge', 'height': [2000, 3200], 'floor': 1600,
                 'crest': 10, 'roughness': 100,
                 'notes': "The Barbaric Mountains' south flank meets the Frostspine's north end and the Ogre Hills' "
                          "backs (X5's north edge [56, 128])."},
            ],
            'edge': {'height': 1400, 'west': 0, 'north': 0, 'east': 1150, 'south': 1460},
        },
        'heights': {
            'bands': bands,
            'points': [dict({'at': cell(at), 'h': h}, **({'notes': n} if n else {})) for at, h, n in HEIGHT_POINTS],
            'cliffs': CLIFFS,
            'ridges': RIDGES,
        },
        'water': {'bodies': [RIM_SEA, OASIS_POND]},
        'roads': [dict({'link': link, 'line': [half(q) for q in line], 'width': width}, **({'surface': s} if s else {}))
                  for link, line, width, s in ROADS],
        'districts': districts,
        'points': points,
        'areas': areas,
        'views': VIEWS,
    }
    if ACTORS:
        out['actors'] = ACTORS
    return out


# ---------------------------------------------------------------- plan.yml
def building(bid, service, fp, count=1, notes=None):
    b = {'id': bid, 'type': 'house', 'service': service, 'count': count, 'doors': 1,
         'footprint_cells': fp if count > 1 else [fp]}
    if notes:
        b['notes'] = notes
    return b


def plan():
    hamlet_buildings = [building(bid, service, fp, notes=f'A4 house {house}.')
                        for bid, service, house, fp, at, facing, door_to, kit in HAMLET]
    hamlet_buildings.append(building('building:x6_houses', 'residence', [h[1] for h in HAMLET_HOUSES],
                                     count=len(HAMLET_HOUSES),
                                     notes="A4 houses 4303 The Well Keeper's House (Old Ibb, 4606) and 4304 The Saddle "
                                           "Loft (Tansy, 4607)."))
    mean = {s: (SLOTS[s - 1]['per_marker'][0] + SLOTS[s - 1]['per_marker'][1]) / 2 for s in (1, 2, 3)}
    marker_hostiles = sum(count * mean[slot] for _aid, slot, count, _p, _n in AREAS)
    markers = sum(a[2] for a in AREAS)

    def pop(aid):
        a = next(x for x in AREAS if x[0] == aid)
        levels = {1: [30, 45], 2: [20, 40], 3: [22, 50]}[a[1]]
        fam = {1: 'Sand burrowers', 2: 'Werewolves', 3: 'Sand golems'}[a[1]]
        return {'id': aid, 'slot': a[1], 'groups': a[2], 'per_marker': [2, 3], 'levels': levels,
                'notes': f'Encounter area: {fam}.'}

    spaces = [
        # ---- the north-west: the heights, Castle Basenji, the cliff foot ----
        {'id': 'zone:basenji_heights', 'name': 'The Basenji heights', 'kind': 'wild', 'floor': [2300, 2750],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Red-brown rock along the north rim (the source's \"mountain edge\"): Castle Basenji on its crag, "
                    "the Waters of Great Power, the werewolves' den, and at the corner where the rims meet the Air "
                    "Reflector.",
         'population': [pop('pop:basenji_heights')]},
        {'id': 'zone:basenji_crag', 'name': "Castle Basenji's crag", 'kind': 'zone', 'part_of': 'zone:basenji_heights',
         'floor': 2700, 'purpose': "The wizard cult's castle (XD-14) on a cliff top over the desert, the stars behind "
                                   "it; its gate at the top of the cliff path."},
        {'id': 'zone:air_corner', 'name': 'The Air corner', 'kind': 'zone', 'part_of': 'zone:basenji_heights',
         'floor': 2350, 'purpose': 'A rock spit where the west and north rims meet: the Air Reflector (M37).'},
        {'id': 'zone:cliff_foot', 'name': "Under Basenji's cliff", 'kind': 'wild', 'floor': [1350, 1600],
         'relief': 'slope', 'density': 'sparse',
         'purpose': "Scree and sand under the cliff: Arie's camp at the foot of the cliff path, the Shrine of Energy "
                    "by the west rim.",
         'population': [pop('pop:pan_west')]},
        {'id': 'zone:arie_camp', 'name': "Arie's camp", 'kind': 'district', 'part_of': 'zone:cliff_foot',
         'floor': 1450, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "Arie the Apprentice (4608, Q-C8): a small tent, a fire and her master's books, where the cliff "
                    "path starts up to the castle."},
        # ---- the north-east: the desert of the Sphinx ----
        {'id': 'zone:sphinx_desert', 'name': 'The Desert of the Sphinx', 'kind': 'wild', 'floor': [1300, 1700],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Open dunes and red mesas north of the road: the Northern Sphinx lying in the sand, a wagon the "
                    "dunes swallowed, a nest on a mesa top; sand worms.",
         'population': [pop('pop:sphinx_dunes')]},
        {'id': 'zone:sphinx_forecourt', 'name': "The Sphinx's forecourt", 'kind': 'zone',
         'part_of': 'zone:sphinx_desert', 'floor': 1400,
         'purpose': "The Northern Sphinx (XD-15): a great sandstone sphinx facing south, its door between its paws "
                    "and a mound of sand before it (the obelisks' hoard)."},
        {'id': 'zone:gargoyle_foothills', 'name': 'The Gargoyle foothills', 'kind': 'wild', 'floor': [2000, 3000],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "The Gargoyle Range's western foothills in the north-east corner, mostly beyond the playable "
                    "square (X4's range goes on east)."},
        # ---- the middle: the pan and the caravan stop ----
        {'id': 'zone:central_pan', 'name': 'The pan', 'kind': 'wild', 'floor': [1150, 1350], 'relief': 'flat',
         'density': 'sparse',
         'purpose': 'Hard sand and cracked pans along the caravan road between the edges: Sphinx Wells, the oasis, '
                    'the obelisk knoll; quiet.'},
        {'id': 'town:sphinx_wells', 'name': 'Sphinx Wells', 'kind': 'town', 'floor': 1250,
         'where': 'the middle of the pan, on the caravan road', 'safe': True, 'keep_clear': ['spawns'],
         'density': 'medium',
         'theme': "cloudside_town kit, its plain grade: ochre plaster and fieldstone, flat roofs with awnings; MM7 "
                  "Bracada's palms.",
         'purpose': 'The caravan stop (WORLD_DESIGN 5.1 hamlet): the tavern, the caravans to Asp and Rivercity, two '
                    'homes and the well "deeper than the Sphinx is tall".',
         'buildings': hamlet_buildings},
        {'id': 'zone:oasis', 'name': 'The oasis', 'kind': 'district', 'part_of': 'zone:central_pan', 'floor': 1080,
         'safe': True, 'keep_clear': ['spawns'],
         'purpose': 'Palms round a clear pond in a hollow of the pan; the oasis fountain (+2 Endurance, permanent).'},
        # ---- the west: the rim dunes ----
        {'id': 'zone:west_dunes', 'name': 'The rim dunes', 'kind': 'wild', 'floor': [1350, 1750], 'relief': 'uneven',
         'density': 'sparse',
         'purpose': "Dunes running west to the rim and pouring over it into the stars, sand streaming off the lip; "
                    "the Southern Sphinx half buried; Saul's hermitage; an explorer's pack at the edge; sand worms.",
         'population': [pop('pop:west_dunes')]},
        {'id': 'zone:saul_hermitage', 'name': "Saul's hermitage", 'kind': 'district', 'part_of': 'zone:west_dunes',
         'floor': 1400, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "Saul the Hermit (4602): a stone hut with an awning and his urn; Meditation Master."},
        {'id': 'zone:southern_sphinx', 'name': 'The Southern Sphinx', 'kind': 'zone', 'part_of': 'zone:west_dunes',
         'floor': 1550, 'purpose': "FD-02: a second sphinx facing east, buried to its shoulders; its jaw shut until "
                                   "Roland's amulet (M40, Act VI)."},
        {'id': 'zone:stony_rises', 'name': 'The stony rises', 'kind': 'wild', 'floor': [1800, 2400],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "The south-west corner's stony rises toward X5 (outside the playable square)."},
        # ---- the south and east ----
        {'id': 'zone:east_downs', 'name': 'The dry downs', 'kind': 'wild', 'floor': [1500, 2100], 'relief': 'uneven',
         'density': 'sparse', 'purpose': 'Dry downs toward X4 with a lone mesa; sand golems.',
         'population': [pop('pop:east_downs')]},
        {'id': 'zone:ruin_fields', 'name': 'The bone fields', 'kind': 'wild', 'floor': [1300, 1550],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Cracked ground strewn with the bones of something enormous, a dead caravan's strongbox among "
                    "them; the ruined caravanserai with its sand golems.",
         'population': [pop('pop:ruin_fields')]},
        {'id': 'zone:south_steppe', 'name': 'The south steppe', 'kind': 'wild', 'floor': [1350, 1500],
         'relief': 'slope', 'density': 'sparse',
         'purpose': "Dry grass and stones down to X5: the steppe road, the Well of Accuracy, the Summer Druid's "
                    "grove, the coach track to the Warzone yard."},
        {'id': 'zone:druid_grove', 'name': "The Summer Druid's grove", 'kind': 'district',
         'part_of': 'zone:south_steppe', 'floor': 1450, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': 'The Summer Druid (4601, Q-C1): olive trees round a spring, the one green place in the south.'},
        {'id': 'zone:coach_yard', 'name': 'The Warzone coach yard', 'kind': 'district', 'part_of': 'zone:south_steppe',
         'floor': 1500, 'safe': True, 'keep_clear': ['spawns'],
         'theme': "Fieldstone walls of the cloudside_town kit; the arena gate cut in the Barbaric cliff (MM6 "
                  "castle-stone portal).",
         'purpose': "D-8.1: a walled pocket holding only the arena gate (XD-20) and Gorm's coach house (4305; routes "
                    "429 to Rivercity, 430 to Castleview on m7.sigil); its desert gate barred from inside until a party "
                    "opens it from the desert side (x6.warzone_gate).",
         'buildings': [building(COACH[0], COACH[1], COACH[3], notes='A4 house 4305.')]},
        {'id': 'zone:barbaric_mountains', 'name': 'The Barbaric Mountains', 'kind': 'wild', 'floor': [2200, 3700],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Bare red-brown peaks in the south-east (the source's B2): the coach yard's cliffs, a "
                    "prospector's camp in a high notch; sand golems.",
         'population': [pop('pop:barbaric')]},
        {'id': 'zone:rim', 'name': 'The world rim', 'kind': 'wild', 'floor': 0, 'empty': True,
         'purpose': 'West and north the land ends in a cliff; below, the stars (water at 0 stands for them).'},
        {'id': 'water:rim_sea', 'name': 'Below the rim', 'kind': 'water', 'purpose': 'The stars below the edge.'},
        {'id': 'water:oasis_pond', 'name': 'The oasis pond', 'kind': 'water', 'part_of': 'zone:oasis',
         'purpose': 'Clear water under palms.'},
        # ---- junctions and edges ----
        {'id': 'junction:wells_fork', 'name': 'Wells fork', 'kind': 'junction', 'signpost': True,
         'purpose': 'West of Sphinx Wells: the road east to Burlock, south to Winterkill, north to Castle Basenji; '
                    'the oasis track west.'},
        {'id': 'junction:sphinx_fork', 'name': 'Sphinx fork', 'kind': 'junction', 'signpost': True,
         'purpose': 'The track north to the Sphinx and the obelisk.'},
        {'id': 'junction:south_fork', 'name': 'South fork', 'kind': 'junction', 'signpost': True,
         'purpose': 'The rim track west to the Southern Sphinx, the coach track east to the Warzone.'},
        {'id': 'edge:east_end', 'name': 'East edge (X4)', 'kind': 'road', 'part_of': 'zone:central_pan',
         'purpose': 'Where the desert road leaves for X4.'},
        {'id': 'edge:south_end', 'name': 'South edge (X5)', 'kind': 'road', 'part_of': 'zone:south_steppe',
         'purpose': 'Where the steppe road leaves for X5.'},
    ]
    links = [
        {'id': 'link:desert_road', 'from': 'edge:east_end', 'to': 'junction:wells_fork', 'kind': 'road',
         'purpose': 'travel: X4', 'notes': 'by the Sphinx fork and through Sphinx Wells'},
        {'id': 'link:steppe_road', 'from': 'junction:wells_fork', 'to': 'edge:south_end', 'kind': 'road',
         'purpose': 'travel: X5', 'notes': 'by the South fork and the Well of Accuracy'},
        {'id': 'link:basenji_road', 'from': 'junction:wells_fork', 'to': 'zone:arie_camp', 'kind': 'road'},
        {'id': 'link:cliff_path', 'from': 'zone:arie_camp', 'to': 'zone:basenji_crag', 'kind': 'path', 'rise': 1150,
         'features': ['a zigzag path up the cliff face, 1,150 in four turns']},
        {'id': 'link:reflector_path', 'from': 'zone:basenji_crag', 'to': 'zone:air_corner', 'kind': 'path',
         'notes': 'along the cliff top past the Waters of Great Power'},
        {'id': 'link:sphinx_track', 'from': 'junction:sphinx_fork', 'to': 'zone:sphinx_forecourt', 'kind': 'path'},
        {'id': 'link:obelisk_path', 'from': 'link:sphinx_track', 'to': 'zone:central_pan', 'kind': 'path',
         'notes': "up the obelisk's knoll"},
        {'id': 'link:oasis_track', 'from': 'junction:wells_fork', 'to': 'zone:saul_hermitage', 'kind': 'path',
         'notes': 'by the oasis'},
        {'id': 'link:shrine_path', 'from': 'zone:oasis', 'to': 'zone:cliff_foot', 'kind': 'path',
         'notes': 'to the Shrine of Energy'},
        {'id': 'link:rim_track', 'from': 'junction:south_fork', 'to': 'zone:southern_sphinx', 'kind': 'path'},
        {'id': 'link:coach_track', 'from': 'junction:south_fork', 'to': 'zone:coach_yard', 'kind': 'path',
         'notes': "by the Summer Druid's grove to the yard's desert gate"},
    ]
    entrances = [
        {'id': 'entrance:east_road', 'space': 'edge:east_end', 'kind': 'both', 'neighbour': 'edge:east',
         'facing': 'w', 'how': "The desert road from X4's Asp road."},
        {'id': 'entrance:south_road', 'space': 'edge:south_end', 'kind': 'both', 'neighbour': 'edge:south',
         'facing': 'n', 'how': "The steppe road from X5's Winterkill."},
        {'id': 'entrance:sphinx_wells', 'space': 'town:sphinx_wells', 'kind': 'arrival',
         'neighbours': ['stable:sphinx_wells_asp', 'stable:sphinx_wells_rivercity'],
         'how': "A4's sphinx_wells: in front of the caravans' stables; Town Portal (Sphinx Wells)."},
        {'id': 'entrance:warzone_coach', 'space': 'zone:coach_yard', 'kind': 'arrival',
         'neighbours': ['stable:warzone_rivercity', 'stable:warzone_castleview'],
         'how': "A4's warzone_coach: inside the walled coach yard (Rivercity's 406, Castleview's 415)."},
        {'id': 'entrance:yard_gate', 'space': 'zone:coach_yard', 'kind': 'both', 'facing': 'w',
         'condition': {'qbit': 'warzone_gate'},
         'how': "D-8.1: the yard's desert gate. From the desert side it always opens and calls A3's x6.warzone_gate "
                "(sets 116100); from the yard side it asks x6.warzone_gate_open, and before the bit Gorm says \"The "
                "sand's no place for you yet. Arena or home.\""},
        {'id': 'entrance:xd14_gate', 'space': 'zone:basenji_crag', 'kind': 'both', 'neighbour': 'door:xd14',
         'facing': 's', 'how': "Castle Basenji's gate at the top of the cliff path (\"Castle Basenji. Enter?\")."},
        {'id': 'entrance:xd15_door', 'space': 'zone:sphinx_forecourt', 'kind': 'both', 'neighbour': 'door:xd15',
         'facing': 's', 'condition': {'item': 'northern_sphinx_amulet'},
         'how': "The door between the Sphinx's paws: A3's q-c9.door wants the Jewelled Amulet and keeps it."},
        {'id': 'entrance:xd20_gate', 'space': 'zone:coach_yard', 'kind': 'both', 'neighbour': 'door:xd20',
         'facing': 'w', 'how': 'The arena gate in the cliff ("Enter the War Zone?").'},
        {'id': 'entrance:fd02_door', 'space': 'zone:southern_sphinx', 'kind': 'both', 'neighbour': 'door:fd02',
         'facing': 'e', 'condition': {'item': 'southern_sphinx_amulet'},
         'how': "A3's m40.sphinx_door: \"The Sphinx's stone eyes find Roland's amulet. Its jaw opens on a stair.\"; "
                "without it \"A sphinx of sand-coloured stone, its jaw shut. There is a hollow in its breast the size "
                "of an amulet.\""},
    ]
    pois = [
        {'id': 'poi:obelisk', 'space': 'zone:central_pan', 'kind': 'obelisk', 'rule': 'native:obelisk',
         'behaviour': "Cloudside's sixth obelisk (A3's obelisks.x6: THE).",
         'notes': 'On the red rock knoll by the Sphinx track; the Sphinx in view.'},
        {'id': 'poi:wells_well', 'space': 'town:sphinx_wells', 'kind': 'well',
         'behaviour': "Old Ibb's well: \"The water is cool and refreshing.\" (the source's line; a plain well)."},
        {'id': 'poi:oasis_fountain', 'space': 'zone:oasis', 'kind': 'fountain',
         'behaviour': 'The oasis fountain (MAPS X6): +2 Endurance, permanent, once per character.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:well_accuracy', 'space': 'zone:south_steppe', 'kind': 'well',
         'behaviour': 'The Well of Accuracy by the steppe road: +Accuracy, temporary, daily.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:shrine_energy', 'space': 'zone:cliff_foot', 'kind': 'shrine',
         'behaviour': "The Shrine of Energy (source A1: \"Shrine of Energy. Pray?\"): +5 Air resistance, permanent, "
                      "once per character (D-4's +5).", 'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:sun_stones', 'space': 'zone:south_steppe', 'kind': 'shrine',
         'behaviour': "A ring of red standing stones the Summer Druid keeps for the solstice: +Fire resistance, "
                      "temporary, daily (\"The stones are warm long after dark.\").",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:caravan_cairn', 'space': 'zone:central_pan', 'kind': 'device',
         'behaviour': "A cairn the caravans add to for luck on the crossing: add a stone, +Luck, temporary, daily.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:waters_power', 'space': 'zone:basenji_heights', 'kind': 'fountain',
         'behaviour': 'The Waters of Great Power (source A1): +Hit Points, temporary, daily.',
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:air_reflector', 'space': 'zone:air_corner', 'kind': 'device',
         'behaviour': "A3's m37.reflector_air: \"Reflector. Activate?\"; after m36.started it hums and answers the "
                      "south (8,000 XP once); before, \"A machine of the Ancients, cold and silent.\""},
        {'id': 'poi:saul_urn', 'space': 'zone:saul_hermitage', 'kind': 'device',
         'behaviour': "Saul's urn: \"The urn is full of sand and old coins. Saul says the coins are for the sand.\" "
                      "(the source's urn took 10,000 gold for Prayermaster; Saul now teaches Meditation by talk)."},
        {'id': 'poi:cloud_hoard', 'space': 'zone:sphinx_forecourt', 'kind': 'device',
         'behaviour': "A3's obelisks.cloud_hoard: a mound of sand between the paws; with all seven Cloudside words, "
                      "an iron box (10,000 gold, two treasure-6 items); else \"Sand, and more sand.\""},
        {'id': 'poi:swallowed_wagon', 'space': 'zone:sphinx_desert', 'kind': 'chest',
         'behaviour': "A wagon half under a dune, a worm's hole beside it: its strongbox (a chest)."},
        {'id': 'poi:werewolf_den', 'space': 'zone:basenji_heights', 'kind': 'chest',
         'behaviour': "The werewolves' den under the castle's east wall: gnawed bones and a chest of what their "
                      "victims carried."},
        {'id': 'poi:caravanserai', 'space': 'zone:ruin_fields', 'kind': 'chest',
         'behaviour': 'The ruined caravanserai, its sand golems round it: the old keeper\'s strongbox (a chest).'},
        {'id': 'poi:bone_field', 'space': 'zone:ruin_fields', 'kind': 'chest',
         'behaviour': "A dead caravan among the giant bones: its pay chest."},
        {'id': 'poi:rim_pack', 'space': 'zone:west_dunes', 'kind': 'chest',
         'behaviour': "An explorer's pack at the rim's lip, a rope going over: \"Gone to see where the sand goes.\" "
                      '(a chest)'},
        {'id': 'poi:mesa_nest', 'space': 'zone:sphinx_desert', 'kind': 'chest',
         'behaviour': "A great bird's nest on a mesa top, reached by a crack: glittering things (a chest)."},
        {'id': 'poi:prospector_camp', 'space': 'zone:barbaric_mountains', 'kind': 'chest',
         'behaviour': "A prospector's camp in a high notch, the fire long cold: his strongbox (a chest)."},
        {'id': 'poi:signposts', 'spaces': SIGNPOSTS, 'kind': 'signpost', 'count': 3,
         'behaviour': 'Signposts at the forks.'},
        {'id': 'poi:arie', 'space': 'zone:arie_camp', 'kind': 'npc',
         'behaviour': "Arie the Apprentice (4608): A3's Q-C8 topics (\"The wizards of Castle Basenji killed my "
                      "master. His scroll is still in there.\"); after Q-C8, the Sphinx's name."},
        {'id': 'poi:saul', 'space': 'zone:saul_hermitage', 'kind': 'teacher',
         'behaviour': "Saul the Hermit (4602): Meditation Master (A4's teachers); \"Sit by the urn. Breathe. The sand "
                      "will wait.\""},
        {'id': 'poi:summer_druid', 'space': 'zone:druid_grove', 'kind': 'npc',
         'behaviour': "The Summer Druid (4601): A3's Q-C1 (the Last Flower of Summer)."},
    ]
    landmarks = [
        {'id': 'landmark:basenji', 'space': 'zone:basenji_crag',
         'what': 'A dark castle of grey rubble and black timber on a cliff top, nothing but stars behind it',
         'seen_from': ['zone:central_pan', 'zone:cliff_foot', 'zone:sphinx_desert', 'edge:east_end']},
        {'id': 'landmark:northern_sphinx', 'space': 'zone:sphinx_forecourt',
         'what': 'A great sandstone sphinx lying in the dunes, its head 1,600 above the sand',
         'seen_from': ['zone:central_pan', 'zone:sphinx_desert', 'edge:east_end', 'zone:east_downs']},
        {'id': 'landmark:southern_sphinx', 'space': 'zone:southern_sphinx',
         'what': 'A second sphinx buried to its shoulders, facing the morning',
         'seen_from': ['zone:west_dunes', 'zone:south_steppe']},
        {'id': 'landmark:red_mesas', 'space': 'zone:sphinx_desert',
         'what': 'Flat-topped red mesas north of the road', 'seen_from': ['zone:central_pan', 'edge:east_end']},
        {'id': 'landmark:barbaric_mountains', 'space': 'zone:barbaric_mountains',
         'what': 'Bare red-brown peaks to 3,700 in the south-east',
         'seen_from': ['zone:south_steppe', 'zone:ruin_fields', 'edge:south_end']},
        {'id': 'landmark:sand_falls', 'space': 'zone:west_dunes',
         'what': 'Dunes pouring over the west rim, sand streaming off into the stars',
         'seen_from': ['zone:west_dunes', 'zone:saul_hermitage']},
    ]
    sightlines = [
        {'id': 'view:arrival', 'from': 'entrance:east_road',
         'to': ['town:sphinx_wells', 'landmark:northern_sphinx', 'landmark:red_mesas', 'landmark:basenji'],
         'what': "Arrival from X4: the road over the pan to Sphinx Wells' palms, the Sphinx in the dunes on the "
                 "right, the mesas, Castle Basenji far ahead on its cliff."},
        {'id': 'view:signature', 'from': 'zone:west_dunes', 'to': ['landmark:sand_falls', 'landmark:southern_sphinx'],
         'what': "The signature view: the dunes pouring over the world's west rim into the stars, the Southern "
                 "Sphinx half buried beside them."},
    ]
    states = [
        {'id': 'state:yard_barred', 'condition': {'not': {'qbit': 'warzone_gate'}}, 'locks': ['entrance:yard_gate'],
         'atmosphere': "A beam across the gate on the yard side; Gorm by his coach.",
         'notes': "Only from the yard side: from the desert side the gate opens and sets the bit (A3's "
                  "x6.warzone_gate)."},
        {'id': 'state:sphinx_shut', 'condition': {'not': {'qbit': 'sphinx_entered'}},
         'locks': ['entrance:xd15_door'],
         'notes': "Opens once to the Jewelled Amulet (q-c9.door), then stays open."},
        {'id': 'state:southern_sphinx_shut', 'condition': {'not': {'item': 'southern_sphinx_amulet'}},
         'locks': ['entrance:fd02_door'], 'atmosphere': "Its jaw shut; a hollow in its breast."},
        {'id': 'state:reflector_cold', 'condition': {'not': {'qbit': 'm36_started'}},
         'atmosphere': 'The Reflector cold and silent until M36 starts.'},
        {'id': 'state:coach_castleview', 'condition': {'not': {'qbit': 'm7_sigil'}},
         'notes': "Route 430 (to Castleview) waits for the Pyramid Sigil (D-8.1); route 429 runs from the start."},
    ]
    totals = {
        'hostiles_at_load': int(marker_hostiles),
        'encounter_areas': len(AREAS),
        'spawn_markers': markers,
        'outdoor_chests': sum(1 for p in pois if p['kind'] == 'chest'),
        'points_of_interest': 0,      # filled in by run.sh from render_x6.py's census (figures.json)
        'dungeon_entrances': 4,
    }
    return {
        'format': 0,
        'level': 'L1',
        'pitch': "Cloudside's north-west corner: a hot desert of dunes and red mesas between two edges of the world. "
                 "Castle Basenji stands on a cliff at the north rim with nothing but stars behind it; the Northern "
                 "Sphinx lies in the dunes; in the west the sand pours over the rim and streams off into space, past "
                 "a second sphinx buried to its shoulders. Between them the caravan road crosses the pan to Sphinx "
                 "Wells, and in the south-east the Barbaric Mountains hide the yard of the Warzone.",
        'purpose': "Act IV's wilderness (party 30-33): Arie and Castle Basenji (Q-C8, XD-14), the Northern Sphinx "
                   "(Q-C9, XD-15), the Warzone arena and its coach (XD-20, D-8.1), the Summer Druid (Q-C1), Saul "
                   "(Meditation), the Air Reflector (M37, Act V), the obelisks' hoard before the Sphinx, and the "
                   "Southern Sphinx sealed until Act VI (M40, FD-02).",
        'mood': "Glare and heat under a pale clear sky; wind hissing over the dunes, sand blowing off their crests; "
                "palms and camels at the wells; the dark castle silent on its cliff; the hush at the rim where the "
                "sand falls into the stars.",
        'datum': 'water:rim_sea',
        'spaces': spaces,
        'links': links,
        'entrances': entrances,
        'critical_path': ['edge:east_end', 'junction:sphinx_fork', 'town:sphinx_wells', 'junction:wells_fork',
                          'zone:arie_camp', 'zone:basenji_crag'],
        'goals': [
            {'id': 'goal:arie', 'space': 'zone:arie_camp', 'kind': 'reach',
             'what': "Meet Arie below Castle Basenji; take her master's note (Q-C8).", 'story': 'Q-C8'},
            {'id': 'goal:basenji', 'space': 'zone:basenji_crag', 'kind': 'reach',
             'what': 'Climb the cliff path into Castle Basenji (XD-14) for the Scroll of Insight.', 'story': 'Q-C8'},
            {'id': 'goal:sphinx', 'space': 'zone:sphinx_forecourt', 'kind': 'use',
             'what': "Open the Northern Sphinx with Arie's amulet (Q-C9).", 'story': 'Q-C9'},
            {'id': 'goal:summer', 'space': 'zone:druid_grove', 'kind': 'reach',
             'what': 'Take the Last Flower of Summer from the Summer Druid (Q-C1).', 'story': 'Q-C1'},
            {'id': 'goal:hoard', 'space': 'zone:sphinx_forecourt', 'kind': 'use',
             'what': "Dig where the seven Cloudside obelisks said (OBELISKS).", 'story': 'OBELISKS'},
            {'id': 'goal:reflector', 'space': 'zone:air_corner', 'kind': 'use',
             'what': 'Wake the Air Reflector (M37, after M36 starts).', 'story': 'M37'},
        ],
        'points_of_interest': pois,
        'landmarks': landmarks,
        'sightlines': sightlines,
        'states': states,
        'height_bands': [
            {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
            {'id': 'band:oasis', 'range': [1000, 1150], 'spaces': ['zone:oasis', 'water:oasis_pond']},
            {'id': 'band:pan', 'range': [1150, 1350], 'spaces': ['zone:central_pan', 'town:sphinx_wells']},
            {'id': 'band:desert', 'range': [1300, 1600],
             'spaces': ['zone:cliff_foot', 'zone:ruin_fields', 'zone:south_steppe']},
            {'id': 'band:dunes', 'range': [1300, 2300], 'spaces': ['zone:sphinx_desert', 'zone:west_dunes'],
             'notes': 'Dunes 1,300-1,750; the red mesas stand up to 2,250 out of them.'},
            {'id': 'band:downs', 'range': [1500, 2400], 'spaces': ['zone:east_downs', 'zone:stony_rises']},
            {'id': 'band:heights', 'range': [2200, 3000], 'spaces': ['zone:basenji_heights', 'zone:gargoyle_foothills']},
            {'id': 'band:peaks', 'range': [2200, 3700], 'spaces': ['zone:barbaric_mountains']},
        ],
        'landform': {
            'relief': "The pan (1,250) along the caravan road, the oasis hollow (1,080, the pond 1,000); dunes "
                      "1,300-1,750 north and west; red mesas to 2,250; Basenji's heights (2,350-2,750) on the north "
                      "rim with a 1,100 cliff to the desert; the Barbaric Mountains to 3,700 in the south-east, "
                      "inside the playable square. Inside the square: 1,000 to 3,700.",
            'height_range': [1000, 3700],
            'water': 'The oasis pond (about 15 cells); no river.',
            'water_share': 0.003,
            'caps': [{'kind': 'bare rock', 'share': 0.14,
                      'where': "Basenji's heights and cliff, the mesas, the Barbaric Mountains, the rim cliffs"},
                     {'kind': 'sand', 'share': 0.55, 'where': 'the dunes, the pan, the rim dunes'}],
            'rim': {'notes': 'The world rim along the whole west (x 24) and north (y 24): a cliff of 1,400-2,700 down '
                             'to the stars; the dunes pour over the west rim (sand streaming off, particles); Castle '
                             'Basenji over the north rim. East and south the land runs to the map edge; the roads '
                             'run out to it.'},
        },
        'atmosphere': "Sky: the shipped clear preset with the arid theme (Bracada, Dragonsand); no weather; music 17. "
                      "Wind over the dunes and sand blowing off their crests (a particle gap at the rim, MU-2); "
                      "camels and a creaking well at Sphinx Wells; crowd noise faint from the arena gate; silence at "
                      "the rim.",
        'sketch': {'file': 'sketch.yml', 'grid': 512},
        'totals': totals,
        'notes': 'MU-3 for the phase 4 review (A5, 2026-11-20). Source geography: Clouds A1, A2, B1, B2 (MAPS X6). '
                 'Drawing and review board: output/studio_cal/x6/mockups/. Generated by '
                 'output/studio_cal/x6/tools/gen_l1.py.',
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
    fig = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x6') / 'mockups/figures.json'
    count = None
    if '--with-census' in sys.argv and fig.exists():
        count = json.loads(fig.read_text())['poi_count']
    main(count)
