#!/usr/bin/env python3
"""X7 Mount Firestone: the L1 brief (MU-3 plan) for the phase 5 review (A5, 2026-11-20).

    gen_l1.py [--with-census]     writes devdocs/xeen/briefs/x7/L1/{project,plan,sketch,atmosphere}.yml

Then `oymap fmt` and `oymap validate --assets assets_dev` (run.sh does all of it, the drawings and the board). Later
passes edit this script, not the YAML. Cells are [x, y] on the 128-cell grid (512 units), x east, y south.
Form after X6's L1 (level_generation/projects/xeen/x6/gen_l1.py).

Source geography: Clouds E1 (north-west: the Volcano Cave, the Dragon Cave), F1 (north-east: Mount Firestone, the Fire
corner), E2 (south-west: the Red Dwarf Range, the Well of Speed, the Shrine of Fire, an orc outpost, the hot rock) and
F2 (south-east: the Red River Basin, the orc caves), with D1's lava lake and Dragon Tower (MAPS X7). Each source area is
16 x 16 tiles of 2,048 units; here they are pressed into the land inside the rims.

The map is a trap map (MAPS 0): the south slopes are mild (orcs 5-12, the Orc Caves' back gate, Sablewing's cave,
D-5.2); the Red Dwarf Range is quiet; north of the Firestone Gap the land belongs to hydras, dragons and lava golems.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'devdocs/xeen/briefs/x7/L1'

# ---------------------------------------------------------------- the edges, rims and crossings
RIM_Y = 24           # the north rim: X4's north rim is at y 24 (X4 L4 frame), so the cliff runs on unbroken
RIM_X = 104          # the east rim: X1's east rim cliff is at x 104 (X1 L4), so the cliff runs on unbroken
WEST_Y = 66          # X4's Firestone road reaches its x 128 at y 66 (X4 L4 rim span [60, 72], level at 1,300)
SOUTH_X = 69         # X1's north road reaches its y 0 at x 69 (X1 L4 sketch, town.py NORTH_ROAD; built row 1,856)
GAP = [62, 66]       # the Firestone Gap: the pass where both roads meet and the track north begins
LAVA_FORK = [61, 52]  # north of the Gap: the lake track west, the Volcano Cave east, the black bridge north
SLOPE_FORK = [66, 94]  # on the X1 road: Sablewing's lane east, the shrine lane west

# ---------------------------------------------------------------- project.yml
SLOTS = [
    {'monster': 'Xeen Orc', 'tier': 1, 'per_marker': [1, 2], 'weight': 21},   # F10: 1-2 (was 2-3), spread over 13 markers
    {'monster': 'Xeen Hydra', 'tier': 3, 'per_marker': [1, 3], 'weight': 40},
    {'monster': 'Xeen Dragon', 'tier': 5, 'per_marker': [1, 2], 'weight': 39},
]

PROJECT = {
    'format': 0,
    'id': 'xeen_x7',
    'name': 'Mount Firestone',
    'world': 'xeen',
    'kind': 'outdoor',
    'profile': 'odm',
    'map_code': 'X7',
    'units': {'plan_grid': 512},
    'extent': {'terrain_cells': 128},
    'map_stats': {
        'id': 9105,
        'continent': 6,
        'encounter_chance': 10,
        'treasure_level': 5,
        'trap_dice': 5,
        'perception_difficulty': 5,
        'refill_days': 672,
        'music': 26,
        'environment': 'mountains',
        'lock_difficulty': 10,
        'slots': SLOTS,
    },
    'neighbours': [
        {'id': 'edge:west', 'to': 'xeen_x4.odm', 'kind': 'edge', 'side': 'west', 'days': 5, 'arrival_side': 'east',
         'approach': f'The Firestone road in from the west edge at y {WEST_Y}, up the valley under the Red Dwarf '
                     'Range.',
         'notes': "X4 Burlock Savannah (installed): its Firestone road (link:firestone_road) runs out to its x 128 at "
                  "y 66 over a level span 60-72 at 1,300, sealed until X7 exists; X4's arrival from X7 is "
                  "entrance:east_road [107, 66.5]. The same y here and the same span and height; X4's other east "
                  "spans continue (rim 0-24, lava fields 24-60 at 1,800-2,600, red dwarf hills 72-128 at "
                  "1,900-2,700)."},
        {'id': 'edge:south', 'to': 'xeen_x1.odm', 'kind': 'edge', 'side': 'south', 'days': 5,
         'arrival_side': 'north',
         'approach': f'The north road in from the south edge at x {SOUTH_X}, up from Vertigo\'s hills.',
         'notes': "X1 Vertigo Meadows (A5, installed): its north road runs out to its y 0 at x 69 (built row: 1,600, "
                  "the road 1,856), sealed with a sign until X7 exists; X1's arrival from X7 is entrance:north_road "
                  "[69, 21]. The same x here; X1's east rim (x 104) goes on as X7's."},
        {'id': 'door:xd16', 'to': 'xeen_xd16.blv', 'kind': 'door',
         'arrival_hint': "Inside the Volcano Cave's mouth, on the first ledge above the lava.",
         'notes': "XD-16 Volcano Cave (A7, phase 5; Q-C26): a cave mouth at Mount Firestone's west foot, two idols "
                  "(a demon, a devil) flanking it. \"Enter the Volcano Cave?\" Sealed until XD-16 exists."},
        {'id': 'door:xd17', 'to': 'xeen_xd17.blv', 'kind': 'door', 'condition': {'qbit': 'q_c26_done'},
         'arrival_hint': "In the valley's back passage, at the foot of the cleft's stair.",
         'notes': "XD-17 Shangri-La (A5, phase 5; Q-C26): the valley's back gate, a cleft in the black rock east of "
                  "the Volcano Cave. Shut by a rockfall from the X7 side until q-c26.done (both skulls smashed); the "
                  "first way in stays the Volcano Cave (question 3). Sealed until XD-17 exists."},
        {'id': 'door:xd18', 'to': 'xeen_xd18.blv', 'kind': 'door',
         'arrival_hint': "Inside the Dragon Cave's mouth, before the Dragon Tax Office's counter (D-5.2).",
         'notes': "XD-18 Dragon Cave (A7, phase 6; Q-C25, optional): the cave in the crag over the north rim; "
                  "Scaldrith's Dragon Tax Office (house 4852) is inside at its mouth, before the first dragon "
                  "(D-5.2). \"The Dragon Cave smells pretty bad. Are you sure you wish to enter?\" Sealed until "
                  "XD-18 exists."},
        {'id': 'door:fd04', 'to': 'xeen_fd04.blv', 'kind': 'door',
         'arrival_hint': "Inside the Dragon Tower's gate.",
         'notes': "FD-04 Dragon Tower and the Dungeon of Death (A7, phase 6; Q-F1, Q-F2, optional): D1's tower on "
                  "its crag over the lava lake's north shore at the rim. Sealed until FD-04 exists."},
        {'id': 'door:xd05', 'to': 'xeen_xd05.blv', 'kind': 'door', 'condition': {'qbit': 'orc_back_gate'},
         'arrival_hint': "Inside the Orc Caves' back gate.",
         'notes': "XD-05 Orc Caves (A7, built): the back gate on the south-east slopes, opened from inside "
                  "(x1-tam's back_gate sets 110051); from the X7 side barred until then. XD-05 seals it with a "
                  "rockfall until X7 exists (its L4 notes): A7 opens it when X7 is installed."},
    ],
    'qbits': {
        # A3's bits (source/quests/*.yml); the names here are the map's.
        'orc_back_gate': 110051,      # x1-tam.orc_back_gate_open: the back gate barred from inside until thrown
        'q_c26_done': 112522,         # q-c26.done: both skulls smashed, the way to Shangri-La open
        'q_c14_started': 112280,      # q-c14.started: Halon asked for the lava
        'rock_found': 112281,         # q-c14.rock_found: the Ever-Hot Lava Rock taken (the hook's own bit)
        'reflector_fire': 111741,     # m37.fire
        'm36_started': 111720,        # the Reflectors wake only after M36 starts (m37.reflector_fire requires it)
        'cloud_7': 115046,            # obelisks.x7 (SPHINX)
    },
    'items': {
        'lava_rock': 12314,
    },
    'rules': {
        'weather': 'ash',
        'rim': {'sides': ['north', 'east'], 'cliff_x': RIM_X, 'cliff_y': RIM_Y, 'fall': 'death'},
    },
    'notes': 'X7 Mount Firestone, MU-3 plan for the phase 5 review (A5, 2026-11-20). No geometry until a decider has '
             'approved it. Plan: plan.yml; to-scale layout: sketch.yml; air: atmosphere.yml; generator, drawings and '
             'review board: output/studio_cal/x7/ (tools/gen_l1.py writes these four files). Sky: the shipped fair '
             'preset with the ashen theme (A6 already lists xeen_x7.odm: ashen in the world sky.yml); ash fall needs '
             'a weather row (NOTES, requests). A trap map: mild south slopes, a quiet range, a deadly north.',
}

# ---------------------------------------------------------------- the land: zones and bands
ZONES = {
    'zone:rim': [[0, 0], [128, 0], [128, 128], [RIM_X, 128], [RIM_X, RIM_Y], [78, RIM_Y], [76, 28], [70, 28],
                 [68, RIM_Y], [0, RIM_Y]],
    'zone:lava_basin': [[0, RIM_Y], [52, RIM_Y], [52, 54], [44, 58], [30, 59], [0, 60]],
    'zone:ash_flats': [[52, RIM_Y], [70, RIM_Y], [74, 32], [78, 44], [76, 56], [62, 60], [44, 58], [52, 54]],
    'zone:firestone': [[70, RIM_Y], [RIM_X, RIM_Y], [RIM_X, 58], [88, 61], [76, 56], [78, 44], [74, 32]],
    'zone:red_dwarf_range': [[0, 60], [30, 59], [44, 58], [62, 60], [76, 56], [88, 61], [RIM_X, 58], [RIM_X, 76],
                             [84, 78], [70, 74], [58, 76], [44, 74], [24, 76], [0, 74]],
    'zone:south_slopes': [[0, 74], [24, 76], [44, 74], [58, 76], [70, 74], [84, 78], [RIM_X, 76], [RIM_X, 128],
                          [0, 128]],
}

TOWNS = {
    'zone:the_gap': [[58, 62], [67, 62], [67, 69], [58, 69]],
    'zone:dwarf_watch': [[64, 79], [71, 79], [71, 86], [64, 86]],
    'zone:sablewing_cave': [[73, 87], [79, 87], [79, 93], [73, 93]],
    'zone:orc_outpost': [[28, 83], [34, 83], [34, 89], [28, 89]],
    'zone:volcano_mouth': [[63, 42], [69, 42], [69, 48], [63, 48]],
    'zone:dragon_crag': [[52, 25], [60, 25], [60, 31], [52, 31]],
    'zone:tower_crag': [[25, 25], [33, 25], [33, 33], [25, 33]],
    'zone:lava_island': [[30, 40], [39, 40], [39, 48], [30, 48]],
    'zone:crater': [[83, 35], [93, 35], [93, 45], [83, 45]],
    'zone:fire_corner': [[98, RIM_Y], [RIM_X, RIM_Y], [RIM_X, 30], [98, 30]],
}

BANDS = [
    ('band:rim_sea', 'zone:rim'),
    ('band:basin', 'zone:lava_basin'),
    ('band:flats', 'zone:ash_flats'),
    ('band:volcano', 'zone:firestone'),
    ('band:range', 'zone:red_dwarf_range'),
    ('band:slopes', 'zone:south_slopes'),
]

HEIGHT_POINTS = [
    # the south slopes (E2, F2): mild, red stony ground rising north to the range
    ([SOUTH_X, 107], 1850, "the X1 arrival (X1's north road meets its edge at about 1,850)"),
    ([SLOPE_FORK[0], SLOPE_FORK[1]], 1950, 'the slope fork'),
    ([52, 98], 2050, 'the Shrine of Fire on a knoll west of the road'),
    ([28, 102], 1800, 'the Well of Speed by the old west track'),
    ([31, 86], 2000, 'the orc outpost on the west slopes'),
    ([67, 83], 2100, "the dwarves' watch: a stockade and a signal tower beside the road"),
    ([76, 90], 2050, "Sablewing's cave mouth under a red crag"),
    ([78, 88], 2600, None),
    ([88, 100], 2000, "the Orc Caves' back gate in the hillside (XD-05)"),
    ([90, 97], 2500, None),
    ([94, 84], 2150, 'a hot spring in the red rock'),
    ([20, 92], 2100, None),
    ([98, 104], 2300, None),
    # the Red Dwarf Range and the two roads up into it
    ([21, WEST_Y], 1400, "the X4 arrival (X4's edge span is level at 1,300)"),
    ([30, 66], 1550, None),
    ([40, 65], 1800, 'the cairn of the unreturned beside the Firestone road'),
    ([44, 70], 2050, "a dwarf miner's old adit"),
    ([50, 68], 2000, None),
    ([GAP[0], GAP[1]], 2300, 'the Firestone Gap: the pass between the range\'s peaks, both roads meet'),
    ([64, 63], 2350, "the obelisk on the Gap's north lip, the whole north in view"),
    ([36, 61], 3000, 'the Red Dwarf Range'),
    ([50, 61], 3200, 'the Red Dwarf Range'),
    ([30, 73], 2700, None),
    ([46, 73], 2800, None),
    ([78, 66], 3000, None),
    ([92, 65], 3100, None),
    ([100, 70], 2800, None),
    # the north (E1, F1, D1's lake): ash flats, the lava lake, Mount Firestone
    ([LAVA_FORK[0], LAVA_FORK[1]], 2050, 'the lava fork'),
    ([61, 43], 2000, 'the black bridge over the lava river'),
    ([58, 36], 2150, "a knight's remains by the tax road"),
    ([56, 28], 2700, "the Dragon Cave's crag over the north rim"),
    ([67, 25], 2300, "the lava cove's west lip (the signature camera)"),
    ([73, 29], 2350, "the lava falls' lip on the cove's south wall"),
    ([66, 45], 2250, "the Volcano Cave at Firestone's west foot, two idols at its mouth"),
    ([73, 48], 2500, "a cleft in the black rock: Shangri-La's back gate"),
    ([29, 29], 2600, "the Dragon Tower's crag over the north rim"),
    ([42, 56], 1700, "the hydras' wallow on the lake shore"),
    ([20, 44], 1800, None),
    ([40, 30], 1900, None),
    ([48, 50], 1650, None),
    ([35, 44], 1560, "the Ever-Hot Lava Rock's island: a cooled flow"),
    ([88, 36], 4900, 'Mount Firestone: the crater rim'),
    ([92, 40], 4900, None),
    ([88, 44], 4800, None),
    ([84, 40], 4700, "the crater's west notch, where the lava river leaves"),
    ([80, 40], 3600, None),
    ([96, 40], 3800, None),
    ([88, 51], 3300, None),
    ([88, 30], 3500, None),
    ([97, 46], 3000, "a dragon's hoard on Firestone's east shoulder"),
    ([101, 26], 2900, 'the Fire corner: a rock spit where the rims meet; the Reflector'),
    ([80, 49], 2700, None),
]

CLIFFS = [
    {'line': [[RIM_X, RIM_Y], [78, RIM_Y], [76, 28], [70, 28], [68, RIM_Y], [0, RIM_Y]], 'drop': 1500,
     'down': 'right',
     'notes': "The north rim at y 24 (as X4's), drawn east to west, the low side north; the lava cove (x 68-78) bites "
              "four cells into it, and the lava falls pour over its south wall into the stars (D-35's lesson: the "
              "falls' faces toward the signature camera on the cove's west lip)."},
    {'line': [[RIM_X, RIM_Y], [RIM_X, 70], [RIM_X, 128]], 'drop': 1500, 'down': 'left',
     'notes': "The east rim at x 104 (as X1's), drawn north to south, the low side east."},
]

RIDGES = [
    {'line': [[6, 60], [22, 60], [38, 59.5], [52, 60]], 'height': 3000, 'width': 2, 'slope': 3,
     'notes': "The Red Dwarf Range's north wall over the Firestone road."},
    {'line': [[4, 74], [20, 73], [38, 72], [54, 72.5]], 'height': 2800, 'width': 2, 'slope': 3,
     'notes': "The range's southern crest above the west slopes."},
    {'line': [[70, 64], [80, 66], [92, 66], [102, 64]], 'height': 3000, 'width': 2, 'slope': 3,
     'notes': 'The range east of the Gap.'},
]

LAVA_LAKE = {'id': 'water:lava_lake', 'kind': 'lake', 'level': 1500,
             # the outline runs round the island and its causeway, which stay land (a cooled flow)
             'polygon': [[22, 46], [24, 38], [32, 34], [42, 36], [46, 42], [44, 50], [38, 54], [37, 54],
                         [37, 48], [39, 47], [39, 42], [36, 40], [32, 41], [30, 44], [32, 47], [34, 48], [34, 54],
                         [28, 52]],
             'notes': "D1's lava lake under the north rim: the island of cooled flow with the Ever-Hot Lava Rock, "
                      "joined to the south shore by a causeway (lava: the world's MM7 tile table has no lava set; a liquid lava set is asked of A6/A1, NOTES)."}
CRATER = {'id': 'water:crater', 'kind': 'pond', 'level': 4600,
          'polygon': [[86, 38], [88, 37], [90, 38], [91, 40], [90, 42], [88, 43], [86, 42], [85, 40]],
          'notes': "Mount Firestone's crater: a lava pool under the smoking rim."}
RIM_SEA = {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': ZONES['zone:rim'],
           'notes': 'Below the rims: stands for the stars.'}
RIVERS = [
    {'id': 'water:lava_river', 'line': [[84, 40], [78, 37], [72, 38], [66, 40], [61, 43], [54, 45], [47, 46]],
     'width_cells': 2,
     'notes': 'The lava river from the crater down the west flank to the lava lake; the black bridge crosses it at '
              '[61, 43].'},
    {'id': 'water:lava_falls', 'line': [[78, 37], [76, 33], [74, 30], [73, 28]], 'width_cells': 1.5,
     'notes': "The river's north arm: it pours over the lava cove's south wall into the stars (the signature)."},
]

ROADS = [
    ('link:north_road', [[SOUTH_X, 128], [SOUTH_X, 107], [68, 100], SLOPE_FORK, [64, 88], [63, 82], [62, 76],
                         [62, 70], GAP], 'road', 'road_pebbles'),
    ('link:firestone_road', [[0, WEST_Y], [21, WEST_Y], [30, 66.5], [40, 67], [50, 67.5], [56, 67], GAP], 'road',
     'road_pebbles'),
    ('link:north_track', [GAP, [61.5, 60], LAVA_FORK, [61, 47], [61, 43], [59.5, 39], [58, 35], [56.5, 30.5]],
     'lane', None),
    ('link:volcano_path', [[61, 47], [64, 46], [66, 45.5]], 'lane', None),
    ('link:lake_track', [LAVA_FORK, [54, 54], [46, 56], [40, 56.5], [35.5, 54], [35.5, 48]], 'lane', None),
    ('link:tower_path', [[40, 56.5], [30, 57], [22, 52], [19.5, 45], [21, 38], [25, 34], [29, 32.5]], 'lane', None),
    ('link:cleft_path', [[66, 45.5], [70, 47], [73, 48]], 'lane', None),
    ('link:firestone_path', [[73, 48], [80, 49], [88, 48], [95, 45], [99, 38], [101, 31], [101, 27]], 'lane',
     None),
    ('link:sablewing_lane', [SLOPE_FORK, [70, 92.5], [74, 91], [75.5, 90.5]], 'lane', None),
    ('link:shrine_lane', [SLOPE_FORK, [60, 96], [54, 97.5], [53, 98]], 'lane', None),
    ('link:west_track', [[54, 97.5], [44, 99], [36, 101], [29, 102]], 'lane', None),
    ('link:outpost_track', [[36, 101], [34, 94], [32, 88], [31.5, 87]], 'lane', None),
    ('link:gate_lane', [[68, 100], [76, 101], [82, 101], [87, 100.5]], 'lane', None),
    ('link:spring_lane', [[82, 101], [88, 94], [92, 88], [94, 85]], 'lane', None),
]

# ---------------------------------------------------------------- points
POINTS = [
    # arrivals and edges
    ('entrance:west_road', [21, WEST_Y], 'e', 'Arrival from X4 Burlock Savannah (the Firestone road; X4 leaves at y '
                                              '66).'),
    ('entrance:south_road', [SOUTH_X, 107], 'n', 'Arrival from X1 Vertigo Meadows (the north road; X1 leaves at x '
                                                 '69).'),
    ('entrance:xd16_mouth', [66, 45], 'w', "XD-16 Volcano Cave: the cave mouth at Firestone's west foot, between a "
                                           "demon idol and a devil idol."),
    ('entrance:xd17_cleft', [73, 48], 'w', "XD-17 Shangri-La: the valley's back gate, a cleft east of the Volcano "
                                           "Cave (q-c26.done)."),
    ('entrance:xd18_mouth', [56, 30], 's', "XD-18 Dragon Cave: the cave in the crag over the north rim; the Dragon "
                                           "Tax Office inside its mouth (D-5.2)."),
    ('entrance:fd04_door', [29, 32], 's', "FD-04 Dragon Tower: the tower's gate on its crag over the lava lake "
                                          "(phase 6)."),
    ('entrance:xd05_gate', [88, 100], 'w', "XD-05 Orc Caves: the back gate in the south-east hillside, barred from "
                                           "inside until thrown (110051)."),
    # junctions
    ('junction:gap', GAP, None, None),
    ('junction:lava_fork', LAVA_FORK, None, None),
    ('junction:slope_fork', SLOPE_FORK, None, None),
    # places
    ('poi:obelisk', [64, 63], None, "On the Gap's north lip ('Obelisk of Mount Firestone'), the deadly north below."),
    ('poi:shrine_fire', [52, 98], None, 'The Shrine of Fire on its knoll (source E2).'),
    ('poi:well_speed', [28, 102], None, 'The Well of Speed by the old west track (source E2).'),
    ('poi:fire_reflector', [101, 26], None, 'The Fire Reflector on the rock spit where the north and east rims meet '
                                            '(m37.reflector_fire).'),
    ('poi:lava_rock', [35, 44], None, "The Ever-Hot Lava Rock on the island of cooled flow (q-c14.lava_rock)."),
    ('poi:demon_idols', [66, 46], None, "The demon and devil idols flanking the Volcano Cave's mouth."),
    ('poi:hot_spring', [94, 84], None, 'A hot spring in the red rock, where the dwarves of the watch bathed.'),
    ('poi:cairn', [40, 65], None, 'The cairn of the unreturned beside the Firestone road.'),
    ('poi:orc_outpost', [31, 86], None, "An orc outpost on the west slopes (source E2's: \"Put it to the torch?\")."),
    # people outdoors (A4's NPCs without a house: places for the 6,000 rule, not POIs by D-20)
    ('poi:sablewing', [76, 90], None, 'Sablewing the Dragon Hermit (4720): Dragon Master, at his cave mouth (D-5.2).'),
    # chests with a reason
    ('poi:watch_chest', [68, 84], None, None),
    ('poi:outpost_chest', [31, 87], None, None),
    ('poi:orc_den', [83, 104], None, None),
    ('poi:miner_cache', [44, 70], None, None),
    ('poi:knight_remains', [58, 36], None, None),
    ('poi:dragon_hoard', [97, 46], None, None),
    ('poi:hydra_wallow', [42, 57], None, None),
    # landmarks (no click)
    ('landmark:firestone', [88, 40], None, None),
    ('landmark:lava_falls', [73, 28], None, "The lava river's north arm pouring over the cove's south wall into "
                                            "the stars."),
    ('landmark:dragon_tower', [29, 29], None, None),
    ('landmark:watch_tower', [66, 81], None, None),
    ('landmark:black_bridge', [61, 43], None, None),
    ('landmark:red_dwarf_range', [50, 61], None, None),
    ('landmark:east_lookout', [84, 70], None, "The dwarves' east lookout: a roofless stone hut on the range's crest, "
                                             "its spyglass mount pointing north."),
    ('landmark:slag_heaps', [52, 84], None, "The dwarves' old slag heaps and a fallen ore chute on the west slopes."),
    ('landmark:boundary_stone', [31, 68], None, "A dwarf boundary stone by the Firestone road, carved with a dragon "
                                                "and a line."),
    ('landmark:dragon_skull', [98, 74], None, "A dragon's skull on the range's east end, picked clean: one came south "
                                              "once."),
    ('landmark:fallen_cart', [42, 106], None, 'An ore cart overturned beside the old west track.'),
    ('landmark:pony_shed', [76, 76], None, "The watch's pony shed under the range, its roof fallen in."),
    ('landmark:charcoal_pits', [57, 90], None, "The dwarves' charcoal pits, long cold."),
]
SIGNPOSTS = ['junction:gap', 'junction:lava_fork', 'junction:slope_fork']

# ---------------------------------------------------------------- monsters
# Encounter areas: (id, slot, markers, polygon, family note)
AREAS = [
    ('pop:lava_basin', 2, 10, [[19, 30], [36, 28], [48, 32], [52, 42], [52, 52], [46, 58], [26, 58], [19, 54]],
     "Hydras (Hydra 45, Venomous Hydra 55, Great Hydra 65) round the lava lake's shores and the Dragon Tower's crag; "
     "the lake track and the tower path run through them."),
    ('pop:ash_flats', 2, 9, [[52, 32], [66, 30], [72, 34], [76, 44], [74, 54], [64, 56], [52, 52], [52, 42]],
     "Hydras on the ash flats round the black bridge and the Volcano Cave, below the Dragon Cave's crag; the first "
     "fight north of the Gap (about 5,000 from it)."),
    ('pop:firestone', 3, 18, [[79, 25], [103, 25], [103, 58], [88, 60], [80, 52], [78, 42], [76, 34], [74, 30],
                              [77, 28]],
     "Dragons (Water Dragon 60, Acid Dragon 66, Fire Dragon 75; Dif 5: mostly acid and fire) on Mount Firestone's "
     "flanks, the lava falls and the Fire corner; at least 4,000 from the tax road and the Volcano Cave."),
    ('pop:west_slopes', 1, 4, [[20, 76], [42, 76], [46, 92], [40, 106], [20, 106]],   # F10: to the X1 edge
     "Orcs (Orc 5, Orc Archer 7, Orc Guard 10) round their outpost on the west slopes; the first fight from X4 "
     "(about 5,000)."),
    ('pop:red_river', 1, 3, [[80, 97], [102, 95], [102, 108], [80, 108]],   # F10: the basin's south half
     "Orcs round the Orc Caves' back gate in the Red River Basin; the first fight from X1 (about 4,600), at least "
     "4,000 from Sablewing's cave."),
    # F10 (2026-11-21, the user: "ultra empty, no mobs in radius" at (12816, -9160)): the south slopes' middle and east
    # held no marker within 12,000. Four more orc areas spread the orcs (A2: per marker 1-2, 13 markers = 19.5 orcs,
    # 20 before as 8 x 2.5; Act I stays at 1.15: a 14th marker tips it over), clear of Sablewing's 5,888 (D-85), the watch and the Gap.
    ('pop:east_range', 1, 3, [[84, 63], [103, 62], [103, 93], [92, 93], [84, 78]],
     "Orcs on the range's east shoulders above the Red River Basin (F10)."),
    ('pop:gap_south', 1, 1, [[38, 66], [54, 66], [57, 73], [56, 80], [42, 80], [38, 74]],
     "Orcs in the hills south-west of the Firestone Gap, off the Firestone road (F10)."),
    ('pop:south_hills', 1, 1, [[46, 97], [58, 97], [60, 106], [46, 106]],
     "Orcs in the low hills along the X1 edge, west of the north road (F10)."),
    ('pop:pony_ridge', 1, 1, [[70, 66], [84, 64], [84, 77], [75, 77], [70, 72]],
     "Orcs on the ridge above the pony shed, east of the Gap (F10)."),
]
ACTORS = [
    ('11593', [35, 44.5], 6, 1.5, 1, "Lava Golems 55 on the Ever-Hot Lava Rock's island (MAPS: the north's lava "
                                     "golems)."),
    ('11593', [35.5, 51], 2, 1, 1, 'Two more on the causeway.'),
    ('11030', [31, 86], 2, 1, 2, "Orcs 5 at the outpost to burn (as X1's outposts: placed, never refilled)."),
    ('11032', [31.5, 86.5], 1, 0, 2, "An Orc Guard 10, the outpost's chief."),
]
KEEP_CLEAR = [
    ('zone:sablewing_cave', [[71, 85], [81, 85], [81, 95], [71, 95]], "Sablewing's cave mouth (D-5.2: the safe "
                                                                      "south slope)."),
    ('zone:dwarf_watch', [[59, 77], [74, 77], [74, 89], [59, 89]], "The dwarves' watch with its buffer."),
    ('zone:the_gap', [[55, 61], [69, 61], [69, 71], [55, 71]], 'The Firestone Gap: the obelisk and the signpost at '
                                                               'the pass.'),
    ('edge:south_end', [[64, 101], [74, 101], [74, 110], [64, 110]], 'The X1 arrival.'),
    ('edge:west_end', [[16, 61], [27, 61], [27, 71], [16, 71]], 'The X4 arrival.'),
]
OPEN = [
    ('zone:red_dwarf_range', ZONES['zone:red_dwarf_range'],
     'The Red Dwarf Range: quiet by design, the line between the mild south and the deadly north.'),
]

VIEWS = [
    {'id': 'view:arrival', 'at': [SOUTH_X, 106], 'height': 200, 'look': [76, 40],
     'purpose': "MU-4 arrival view from X1's north road just inside the south edge: north up the road over the red "
                "slopes to the dwarves' watch and its signal tower, the Red Dwarf Range across the view with the "
                "Gap in it, and beyond the range Mount Firestone's smoking cone under falling ash."},
    {'id': 'view:signature', 'at': [67, 25], 'height': 200, 'look': [80, 36],
     'purpose': "MU-4 signature view (earned, in hydra country): from the west lip of the lava cove where the north rim "
                "bites into the land, south-east across the cove: the lava river pours over the cove's far wall "
                "and falls glowing into the stars below; above it Mount Firestone's smoking cone."},
]


def half(at):
    return [round(v * 2) / 2 for v in at]


def cell(at):
    return [int(math.floor(at[0])), int(math.floor(at[1]))]


# ---------------------------------------------------------------- sketch.yml
def sketch():
    bands = [{'band': b, 'space': s, 'polygon': ZONES.get(s) or TOWNS[s]} for b, s in BANDS]
    districts = []
    notes = {
        'zone:dwarf_watch': "The dwarves' watch (MAPS: a dwarf outpost on the south slope): a stockade of red "
                            "fieldstone and timber with a signal tower, its gate west onto the road; abandoned since "
                            "the dragons came south (question 8).",
        'zone:sablewing_cave': "D-5.2: Sablewing's cave mouth under a red crag east of the road; his hoard heaped "
                               "inside the mouth as dressing (no click).",
        'zone:the_gap': 'The Firestone Gap: the saddle where the north road and the Firestone road meet; the obelisk '
                        'on its north lip; from here the whole deadly north is in view.',
        'zone:orc_outpost': "An orc outpost of hides and poles round a fire, to burn (source E2), with its chest.",
        'zone:volcano_mouth': "XD-16's mouth at Firestone's west foot between a demon idol and a devil idol.",
        'zone:dragon_crag': "XD-18: a cave in a black crag at the rim's edge; scorched ground before it.",
        'zone:tower_crag': "FD-04: D1's Dragon Tower, black stone on a crag over the lava lake at the rim.",
        'zone:lava_island': 'The cooled-flow island in the lava lake and its causeway: the Ever-Hot Lava Rock, the '
                            'lava golems.',
        'zone:crater': "Mount Firestone's crater: a lava pool under the smoking rim; the lava river leaves through "
                       "its west notch.",
        'zone:fire_corner': 'A rock spit where the north and east rims meet: the Fire Reflector (M37).',
    }
    for space, poly in TOWNS.items():
        d = {'space': space, 'polygon': poly}
        if space in notes:
            d['notes'] = notes[space]
        districts.append(d)
    for space, poly in ZONES.items():
        districts.append({'space': space, 'polygon': poly})

    points = []
    for pid, at, facing, note in POINTS:
        p = {'id': pid, 'at': cell(at)}
        if facing:
            p['facing'] = facing
        if note:
            p['notes'] = note
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
        'notes': "X7 Mount Firestone, MU-3 to-scale plan (A5, 2026-11-20), for the phase 5 review: composition, scale "
                 "and density only. Cells [x, y], x east, y south. Heights in map units above the stars below the rims "
                 "(0): the lava lake 1,500, the south slopes 1,800-2,200, the Red Dwarf Range to 3,200 with the "
                 "Firestone Gap at 2,300, the ash flats 1,900-2,500, Mount Firestone to 5,000 (its crater's lava "
                 "pool 4,600). North and east the land ends in the world rim (y 24 as X4's north rim, x 104 as X1's "
                 "east rim). Generated by output/studio_cal/x7/tools/gen_l1.py; the later L3 adds detail, ground, "
                 "scatter and structures.",
        'frame': {
            'playable': [19, 19, 90, 90],
            'edges': [
                {'side': 'west', 'span': [60, 72], 'neighbour': 'edge:west',
                 'notes': f'The Firestone road runs out to x 0 at y {WEST_Y} (X4\'s east edge, the same y).'},
                {'side': 'south', 'span': [64, 74], 'neighbour': 'edge:south',
                 'notes': f'The north road runs out to y 128 at x {SOUTH_X} (X1\'s north edge, the same x).'},
            ],
            'rim': [
                {'side': 'north', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': f'The world rim: the cliff at y {RIM_Y} (as X4\'s north rim); the lava falls pour over it.'},
                {'side': 'east', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': f'The world rim: the cliff at x {RIM_X} (as X1\'s east rim); below, water at 0 stands for '
                          'the stars.'},
                {'side': 'west', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': "The north rim's west end (X4's north rim continues it)."},
                {'side': 'west', 'span': [24, 60], 'form': 'ridge', 'height': [1800, 2600], 'floor': 1500,
                 'crest': 10, 'roughness': 120, 'notes': "X4's lava fields climb to the lava basin (X4's east edge "
                                                         "[24, 60])."},
                {'side': 'west', 'span': [60, 72], 'form': 'level', 'height': 1300, 'meet': 6,
                 'notes': "The Firestone road's valley, open to X4 (X4's edge [60, 72] is level at 1,300)."},
                {'side': 'west', 'span': [72, 128], 'form': 'ridge', 'height': [1900, 2700], 'floor': 1300,
                 'crest': 10, 'roughness': 100, 'notes': "X4's red dwarf hills go on east as the range's west end "
                                                         "and the west slopes (X4's edge [72, 128])."},
                {'side': 'south', 'span': [0, 64], 'form': 'ridge', 'height': [1800, 2400], 'floor': 1600,
                 'crest': 10, 'roughness': 100,
                 'notes': "X1's northern hills (X1's built north row 1,600, its hills 1,750-1,900 within four "
                          "cells of the edge)."},
                {'side': 'south', 'span': [64, 74], 'form': 'level', 'height': 1850, 'meet': 6,
                 'notes': "The north road, open to X1 (X1's road reaches its edge at about 1,850)."},
                {'side': 'south', 'span': [74, 104], 'form': 'ridge', 'height': [1800, 2400], 'floor': 1600,
                 'crest': 10, 'roughness': 100, 'notes': "X1's north-east hills (above its orc caves)."},
                {'side': 'south', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': "The east rim's south end (X1's rim continues it)."},
            ],
            'edge': {'height': 1600, 'north': 0, 'east': 0, 'west': 1300, 'south': 1600},
        },
        'heights': {
            'bands': bands,
            'points': [dict({'at': cell(at), 'h': h}, **({'notes': n} if n else {})) for at, h, n in HEIGHT_POINTS],
            'cliffs': CLIFFS,
            'ridges': RIDGES,
        },
        'water': {'bodies': [RIM_SEA, LAVA_LAKE, CRATER], 'rivers': RIVERS},
        'roads': [dict({'link': link, 'line': [half(q) for q in line], 'width': width}, **({'surface': s} if s else {}))
                  for link, line, width, s in ROADS],
        'districts': districts,
        'points': points,
        'areas': areas,
        'views': VIEWS,
        'actors': [dict({'monster': m, 'at': at, 'count': c, 'spread': s, 'group': g, 'hostile': True},
                        **({'notes': n} if n else {})) for m, at, c, s, g, n in ACTORS],
    }
    return out


# ---------------------------------------------------------------- plan.yml
def plan():
    mean = {s: (SLOTS[s - 1]['per_marker'][0] + SLOTS[s - 1]['per_marker'][1]) / 2 for s in (1, 2, 3)}
    marker_hostiles = sum(count * mean[slot] for _aid, slot, count, _p, _n in AREAS)
    placed = sum(a[2] for a in ACTORS)
    markers = sum(a[2] for a in AREAS)

    def pop(aid):
        a = next(x for x in AREAS if x[0] == aid)
        levels = {1: [5, 10], 2: [45, 65], 3: [60, 75]}[a[1]]
        fam = {1: 'Orcs', 2: 'Hydras', 3: 'Dragons'}[a[1]]
        per = SLOTS[a[1] - 1]['per_marker']
        return {'id': aid, 'slot': a[1], 'groups': a[2], 'per_marker': per, 'levels': levels,
                'notes': f'Encounter area: {fam}.'}

    spaces = [
        # ---- the south: the mild slopes ----
        {'id': 'zone:south_slopes', 'name': 'The south slopes', 'kind': 'wild', 'floor': [1700, 2300],
         'relief': 'slope', 'density': 'sparse',
         'purpose': "The Red Dwarf Range's mild southern slopes (source E2, F2): red stony ground and dry scrub "
                    "rising from X1's hills; the north road, the dwarves' watch, Sablewing's cave, the Shrine of "
                    "Fire, the Well of Speed, an orc outpost to burn, the Orc Caves' back gate; orcs only.",
         'population': [pop('pop:west_slopes'), pop('pop:red_river'), pop('pop:gap_south'), pop('pop:south_hills')]},
        {'id': 'zone:dwarf_watch', 'name': "The dwarves' watch", 'kind': 'district', 'part_of': 'zone:south_slopes',
         'floor': 2100, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "A stockade and a signal tower beside the road where the dwarves watched the north; abandoned "
                    "since the dragons came south; its pay chest left behind."},
        {'id': 'zone:sablewing_cave', 'name': "Sablewing's cave", 'kind': 'district', 'part_of': 'zone:south_slopes',
         'floor': 2050, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "D-5.2: Sablewing the Dragon Hermit (4720) at his cave mouth under a red crag off the road from "
                    "X1; Dragon Master (A4's teacher); the hoard heaped behind him (dressing)."},
        {'id': 'zone:orc_outpost', 'name': 'The orc outpost', 'kind': 'zone', 'part_of': 'zone:south_slopes',
         'floor': 2000, 'purpose': "An orc outpost on the west slopes (source E2): hides on poles round a fire, three "
                                   "placed orcs, a chest; burnable."},
        # ---- the range ----
        {'id': 'zone:red_dwarf_range', 'name': 'The Red Dwarf Range', 'kind': 'wild', 'floor': [2000, 3200],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "Bare red peaks across the map (source E2's north half): the line between the mild south and "
                    "the deadly north; the Firestone road runs up its valley from X4 to the Gap; a few orc bands on "
                    "its southern shoulders (F10: the user found it 'ultra empty'), nothing on the north side.",
         'population': [pop('pop:east_range'), pop('pop:pony_ridge')]},
        {'id': 'zone:the_gap', 'name': 'The Firestone Gap', 'kind': 'zone', 'part_of': 'zone:red_dwarf_range',
         'floor': 2300,
         'purpose': "The pass where the north road and the Firestone road meet; the obelisk on its north lip; the "
                    "whole north below: the ash flats, the lava river, Mount Firestone."},
        # ---- the north: the deadly half ----
        {'id': 'zone:lava_basin', 'name': 'The lava basin', 'kind': 'wild', 'floor': [1500, 2000],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "D1's lava lake under the north rim: the cooled-flow island with the Ever-Hot Lava Rock and its "
                    "lava golems, the hydras' wallow, the Dragon Tower on its crag at the rim; hydras.",
         'population': [pop('pop:lava_basin')]},
        {'id': 'zone:lava_island', 'name': "The lava rock's island", 'kind': 'zone', 'part_of': 'zone:lava_basin',
         'floor': 1560,
         'purpose': "A tongue of cooled flow in the lava lake, a causeway to the south shore; the Ever-Hot Lava Rock "
                    "(Q-C14); eight lava golems (placed)."},
        {'id': 'zone:tower_crag', 'name': "The Dragon Tower's crag", 'kind': 'zone', 'part_of': 'zone:lava_basin',
         'floor': 2600, 'purpose': "FD-04: a tower of black stone on a crag over the lava lake at the rim (phase 6)."},
        {'id': 'zone:ash_flats', 'name': 'The ash flats', 'kind': 'wild', 'floor': [1900, 2500], 'relief': 'uneven',
         'density': 'sparse',
         'purpose': "Grey ash plains and cooled flows below the Gap (source E1): the black bridge over the lava "
                    "river, the Volcano Cave and Shangri-La's cleft at Firestone's west foot, the Dragon Cave's crag "
                    "on the rim, a knight's remains by the tax road; hydras.",
         'population': [pop('pop:ash_flats')]},
        {'id': 'zone:volcano_mouth', 'name': "The Volcano Cave's mouth", 'kind': 'zone', 'part_of': 'zone:ash_flats',
         'floor': 2250, 'purpose': "XD-16: a cave mouth breathing heat between a demon idol and a devil idol."},
        {'id': 'zone:dragon_crag', 'name': "The Dragon Cave's crag", 'kind': 'zone', 'part_of': 'zone:ash_flats',
         'floor': 2500, 'purpose': "XD-18: a cave in a black crag at the rim; the Dragon Tax Office inside its mouth."},
        {'id': 'zone:firestone', 'name': 'Mount Firestone', 'kind': 'wild', 'floor': [2300, 5000],
         'relief': 'uneven', 'density': 'sparse',
         'purpose': "The volcano (source F1): a black cone to 5,000 smoking under falling ash, the crater's lava "
                    "pool, the lava river down its west flank and over the north rim, a dragon's hoard on its east "
                    "shoulder, the Fire Reflector at the corner; dragons.",
         'population': [pop('pop:firestone')]},
        {'id': 'zone:crater', 'name': 'The crater', 'kind': 'zone', 'part_of': 'zone:firestone', 'floor': 4600,
         'purpose': 'A lava pool under the smoking rim (a landmark; nothing to take).'},
        {'id': 'zone:fire_corner', 'name': 'The Fire corner', 'kind': 'zone', 'part_of': 'zone:firestone',
         'floor': 2900, 'purpose': 'A rock spit where the north and east rims meet: the Fire Reflector (M37).'},
        {'id': 'zone:rim', 'name': 'The world rim', 'kind': 'wild', 'floor': 0, 'empty': True,
         'purpose': 'North and east the land ends in a cliff; below, the stars (water at 0 stands for them).'},
        {'id': 'water:rim_sea', 'name': 'Below the rim', 'kind': 'water', 'purpose': 'The stars below the edge.'},
        {'id': 'water:lava_lake', 'name': 'The lava lake', 'kind': 'water', 'part_of': 'zone:lava_basin',
         'purpose': "D1's lava lake (lava liquid)."},
        {'id': 'water:crater', 'name': "The crater's lava pool", 'kind': 'water', 'part_of': 'zone:crater',
         'purpose': 'Lava under the rim.'},
        {'id': 'water:lava_river', 'name': 'The lava river', 'kind': 'water', 'part_of': 'zone:ash_flats',
         'purpose': 'From the crater down the west flank to the lava lake; one crossing, the black bridge.'},
        {'id': 'water:lava_falls', 'name': 'The lava falls', 'kind': 'water', 'part_of': 'zone:firestone',
         'purpose': "The river's north arm over the lava cove's south wall into the stars."},
        # ---- junctions and edges ----
        {'id': 'junction:gap', 'name': 'The Gap', 'kind': 'junction', 'signpost': True,
         'purpose': 'The roads south to Vertigo and west to Burlock; the track north into the dragons\' country.'},
        {'id': 'junction:lava_fork', 'name': 'Lava fork', 'kind': 'junction', 'signpost': True,
         'purpose': 'North of the Gap: the lake track west, the Volcano Cave east, the black bridge north to the '
                    'Dragon Cave.'},
        {'id': 'junction:slope_fork', 'name': 'Slope fork', 'kind': 'junction', 'signpost': True,
         'purpose': "On the north road: Sablewing's lane east, the shrine lane west."},
        {'id': 'edge:west_end', 'name': 'West edge (X4)', 'kind': 'road', 'part_of': 'zone:red_dwarf_range',
         'purpose': 'Where the Firestone road leaves for X4.'},
        {'id': 'edge:south_end', 'name': 'South edge (X1)', 'kind': 'road', 'part_of': 'zone:south_slopes',
         'purpose': 'Where the north road leaves for X1.'},
    ]
    links = [
        {'id': 'link:north_road', 'from': 'edge:south_end', 'to': 'junction:gap', 'kind': 'road',
         'purpose': 'travel: X1', 'notes': "by the slope fork and the dwarves' watch, up to the Gap"},
        {'id': 'link:firestone_road', 'from': 'edge:west_end', 'to': 'junction:gap', 'kind': 'road',
         'purpose': 'travel: X4', 'notes': 'up the valley under the range, past the cairn'},
        {'id': 'link:north_track', 'from': 'junction:gap', 'to': 'zone:dragon_crag', 'kind': 'path',
         'notes': 'down to the lava fork, over the black bridge, the tax road to the Dragon Cave'},
        {'id': 'link:volcano_path', 'from': 'link:north_track', 'to': 'zone:volcano_mouth', 'kind': 'path'},
        {'id': 'link:lake_track', 'from': 'junction:lava_fork', 'to': 'zone:lava_island', 'kind': 'path',
         'notes': 'along the lake shore and over the causeway'},
        {'id': 'link:tower_path', 'from': 'link:lake_track', 'to': 'zone:tower_crag', 'kind': 'path',
         'notes': "round the lake's west shore"},
        {'id': 'link:cleft_path', 'from': 'zone:volcano_mouth', 'to': 'zone:firestone', 'kind': 'path',
         'notes': "to Shangri-La's cleft"},
        {'id': 'link:firestone_path', 'from': 'zone:volcano_mouth', 'to': 'zone:fire_corner', 'kind': 'path',
         'notes': "round Firestone's south shoulder to the Fire corner"},
        {'id': 'link:sablewing_lane', 'from': 'junction:slope_fork', 'to': 'zone:sablewing_cave', 'kind': 'path'},
        {'id': 'link:shrine_lane', 'from': 'junction:slope_fork', 'to': 'zone:south_slopes', 'kind': 'path',
         'notes': 'to the Shrine of Fire'},
        {'id': 'link:west_track', 'from': 'link:shrine_lane', 'to': 'zone:south_slopes', 'kind': 'path',
         'notes': 'to the Well of Speed'},
        {'id': 'link:outpost_track', 'from': 'link:west_track', 'to': 'zone:orc_outpost', 'kind': 'path'},
        {'id': 'link:gate_lane', 'from': 'link:north_road', 'to': 'zone:south_slopes', 'kind': 'path',
         'notes': "to the Orc Caves' back gate"},
        {'id': 'link:spring_lane', 'from': 'link:gate_lane', 'to': 'zone:south_slopes', 'kind': 'path',
         'notes': 'to the hot spring'},
    ]
    entrances = [
        {'id': 'entrance:west_road', 'space': 'edge:west_end', 'kind': 'both', 'neighbour': 'edge:west',
         'facing': 'e', 'how': "The Firestone road from X4's lava fields."},
        {'id': 'entrance:south_road', 'space': 'edge:south_end', 'kind': 'both', 'neighbour': 'edge:south',
         'facing': 'n', 'how': "The north road from X1's hills."},
        {'id': 'entrance:xd16_mouth', 'space': 'zone:volcano_mouth', 'kind': 'both', 'neighbour': 'door:xd16',
         'facing': 'w', 'how': 'The cave mouth between the idols ("Enter the Volcano Cave?").'},
        {'id': 'entrance:xd17_cleft', 'space': 'zone:firestone', 'kind': 'both', 'neighbour': 'door:xd17',
         'facing': 'w', 'condition': {'qbit': 'q_c26_done'},
         'how': "Shangri-La's back gate: a cleft in the black rock, a warm green-smelling wind blowing out of it; "
                "before q-c26.done \"A cleft choked with fallen rock. Warm air seeps between the stones.\""},
        {'id': 'entrance:xd18_mouth', 'space': 'zone:dragon_crag', 'kind': 'both', 'neighbour': 'door:xd18',
         'facing': 's', 'how': '"The Dragon Cave smells pretty bad. Are you sure you wish to enter?"'},
        {'id': 'entrance:fd04_door', 'space': 'zone:tower_crag', 'kind': 'both', 'neighbour': 'door:fd04',
         'facing': 's', 'how': "The Dragon Tower's gate (phase 6, optional)."},
        {'id': 'entrance:xd05_gate', 'space': 'zone:south_slopes', 'kind': 'both', 'neighbour': 'door:xd05',
         'facing': 'w', 'condition': {'qbit': 'orc_back_gate'},
         'how': "The Orc Caves' back gate: barred from inside until thrown (x1-tam.back_gate); before, \"A heavy "
                "door of logs in the hillside, barred from within.\""},
    ]
    pois = [
        {'id': 'poi:obelisk', 'space': 'zone:the_gap', 'kind': 'obelisk', 'rule': 'native:obelisk',
         'behaviour': "Cloudside's seventh obelisk (A3's obelisks.x7: SPHINX).",
         'notes': "On the Gap's north lip, safe ground: an Act IV party collecting the words reaches it without a "
                  "fight."},
        {'id': 'poi:shrine_fire', 'space': 'zone:south_slopes', 'kind': 'shrine',
         'behaviour': "The Shrine of Fire (source E2: \"Shrine of Fire\" / \"You don't think anyone is "
                      "listening.\"): +Fire resistance, temporary, daily (X4 already has a permanent Shrine of Fire; "
                      "question 2).", 'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:well_speed', 'space': 'zone:south_slopes', 'kind': 'well',
         'behaviour': "The Well of Speed (source E2: \"The water is cool and refreshing.\"): +2 Speed, permanent, "
                      "once per character (the map's permanent device; question 2).",
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:fire_reflector', 'space': 'zone:fire_corner', 'kind': 'device',
         'behaviour': "A3's m37.reflector_fire: \"Reflector. Activate?\"; after m36.started it hums (8,000 XP once); "
                      "before, \"A machine of the Ancients, cold and silent.\""},
        {'id': 'poi:lava_rock', 'space': 'zone:lava_island', 'kind': 'device',
         'behaviour': "A3's q-c14.lava_rock: the Ever-Hot Lava Rock on the cooled flow (source E2: \"You have found a "
                      "rock that is still hot from an ancient volcanic eruption! Strangely, you are able to pick it "
                      "up without getting burnt.\"); once."},
        {'id': 'poi:demon_idols', 'space': 'zone:volcano_mouth', 'kind': 'device',
         'behaviour': "Two idols at the Volcano Cave's mouth, a demon and a devil: \"Their skulls are not here. "
                      "Someone has scratched an arrow pointing inside.\" (Q-C26's hint; no effect)."},
        {'id': 'poi:hot_spring', 'space': 'zone:south_slopes', 'kind': 'fountain',
         'behaviour': "The dwarves' hot spring: \"You soak until the ache leaves your bones.\" Heals Hit Points, "
                      "daily.", 'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:cairn', 'space': 'zone:red_dwarf_range', 'kind': 'device',
         'behaviour': "The cairn of the unreturned: names scratched on the stones of those who went north. \"Add "
                      "yours?\" +Luck, temporary, daily (\"The stones seem to wish you luck.\")",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:orc_outpost', 'space': 'zone:orc_outpost', 'kind': 'camp',
         'behaviour': "Source E2: \"You have found an Orc Outpost. Put it to the torch?\" / \"The Outpost burns "
                      "well.\" Burns once (the source's +1,000 experience at MM6-MM8 scale, A3)."},
        {'id': 'poi:watch_chest', 'space': 'zone:dwarf_watch', 'kind': 'chest',
         'behaviour': "The watch's pay chest, left when the dwarves ran (a chest)."},
        {'id': 'poi:outpost_chest', 'space': 'zone:orc_outpost', 'kind': 'chest',
         'behaviour': "The orcs' loot from the road (a chest)."},
        {'id': 'poi:orc_den', 'space': 'zone:south_slopes', 'kind': 'chest',
         'behaviour': "The gate pickets' den by the Orc Caves' back gate (source F2: \"Crude furnishings and filthy "
                      "bedding tell you that orcs have been living in this cave. Pillage?\"): a chest."},
        {'id': 'poi:miner_cache', 'space': 'zone:red_dwarf_range', 'kind': 'chest',
         'behaviour': "A dwarf miner's old adit beside the Firestone road, his cache behind a fallen prop (a chest)."},
        {'id': 'poi:knight_remains', 'space': 'zone:ash_flats', 'kind': 'chest',
         'behaviour': "A knight who came for the Dragon Cave, his armour run into the rock; his strongbox (a chest)."},
        {'id': 'poi:dragon_hoard', 'space': 'zone:firestone', 'kind': 'chest',
         'behaviour': "A dragon's hoard on Firestone's east shoulder, among scorched bones (a chest)."},
        {'id': 'poi:hydra_wallow', 'space': 'zone:lava_basin', 'kind': 'chest',
         'behaviour': "The hydras' wallow on the lake shore: bones and a pilgrim's pack (a chest)."},
        {'id': 'poi:signposts', 'spaces': SIGNPOSTS, 'kind': 'signpost', 'count': 3,
         'behaviour': 'Signposts at the forks.'},
        {'id': 'poi:sablewing', 'space': 'zone:sablewing_cave', 'kind': 'teacher',
         'behaviour': "Sablewing the Dragon Hermit (4720): Dragon Master (A4's teachers; D-5.2); \"I came up the "
                      "mountain to be alone. Then everyone came up the mountain to fight me.\""},
    ]
    landmarks = [
        {'id': 'landmark:firestone', 'space': 'zone:firestone',
         'what': 'A black volcanic cone to 5,000, smoke and ash streaming from its crater, red lava down its west '
                 'flank',
         'seen_from': ['zone:south_slopes', 'zone:the_gap', 'zone:ash_flats', 'zone:lava_basin', 'edge:west_end']},
        {'id': 'landmark:lava_falls', 'space': 'zone:firestone',
         'what': 'The lava river pouring over the north rim and falling glowing into the stars',
         'seen_from': ['zone:ash_flats', 'zone:dragon_crag', 'zone:the_gap']},
        {'id': 'landmark:dragon_tower', 'space': 'zone:tower_crag',
         'what': 'A tower of black stone on a crag over the lava lake, the stars behind it',
         'seen_from': ['zone:lava_basin', 'zone:the_gap', 'edge:west_end']},
        {'id': 'landmark:watch_tower', 'space': 'zone:dwarf_watch',
         'what': "The dwarves' signal tower beside the road, its brazier cold",
         'seen_from': ['edge:south_end', 'zone:south_slopes']},
        {'id': 'landmark:black_bridge', 'space': 'zone:ash_flats',
         'what': 'A bridge of black cooled flow arching over the lava river',
         'seen_from': ['zone:the_gap', 'zone:ash_flats']},
        {'id': 'landmark:east_lookout', 'space': 'zone:red_dwarf_range',
         'what': "The dwarves' east lookout: a roofless stone hut on the crest, its spyglass mount pointing north",
         'seen_from': ['zone:south_slopes', 'zone:dwarf_watch']},
        {'id': 'landmark:slag_heaps', 'space': 'zone:south_slopes',
         'what': "The dwarves' old slag heaps and a fallen ore chute", 'seen_from': ['zone:south_slopes']},
        {'id': 'landmark:boundary_stone', 'space': 'zone:red_dwarf_range',
         'what': 'A dwarf boundary stone carved with a dragon and a line', 'seen_from': ['edge:west_end']},
        {'id': 'landmark:dragon_skull', 'space': 'zone:red_dwarf_range',
         'what': "A dragon's skull picked clean on the range's east end", 'seen_from': ['zone:south_slopes']},
        {'id': 'landmark:fallen_cart', 'space': 'zone:south_slopes',
         'what': 'An ore cart overturned beside the old west track', 'seen_from': ['zone:south_slopes']},
        {'id': 'landmark:pony_shed', 'space': 'zone:south_slopes',
         'what': "The watch's pony shed, its roof fallen in", 'seen_from': ['zone:dwarf_watch']},
        {'id': 'landmark:charcoal_pits', 'space': 'zone:south_slopes',
         'what': "The dwarves' charcoal pits, long cold", 'seen_from': ['zone:south_slopes']},
        {'id': 'landmark:red_dwarf_range', 'space': 'zone:red_dwarf_range',
         'what': 'Bare red peaks across the map, the Gap in them',
         'seen_from': ['zone:south_slopes', 'edge:south_end', 'zone:ash_flats']},
    ]
    sightlines = [
        {'id': 'view:arrival', 'from': 'entrance:south_road',
         'to': ['landmark:watch_tower', 'landmark:red_dwarf_range', 'landmark:firestone'],
         'what': "Arrival from X1: the road up the red slopes to the dwarves' watch, the range with the Gap, and "
                 "Mount Firestone smoking beyond it."},
        {'id': 'view:signature', 'from': 'zone:dragon_crag', 'to': ['landmark:lava_falls', 'landmark:firestone'],
         'what': "The signature view: the lava river pouring over the world's north rim into the stars, Mount "
                 "Firestone smoking above it."},
    ]
    states = [
        {'id': 'state:xd05_barred', 'condition': {'not': {'qbit': 'orc_back_gate'}}, 'locks': ['entrance:xd05_gate'],
         'atmosphere': 'The back gate barred from within.',
         'notes': 'Opened from inside XD-05 (x1-tam.back_gate, 110051); then a two-way shortcut to X1.'},
        {'id': 'state:cleft_shut', 'condition': {'not': {'qbit': 'q_c26_done'}}, 'locks': ['entrance:xd17_cleft'],
         'atmosphere': 'Fallen rock in the cleft; warm air between the stones.',
         'notes': 'Opens on q-c26.done (both skulls smashed in XD-16); question 3.'},
        {'id': 'state:reflector_cold', 'condition': {'not': {'qbit': 'm36_started'}},
         'atmosphere': 'The Reflector cold and silent until M36 starts.'},
        {'id': 'state:rock_taken', 'condition': {'qbit': 'rock_found'},
         'atmosphere': 'The cooled flow empty; the golems still there.'},
    ]
    totals = {
        'hostiles_at_load': int(marker_hostiles + placed),
        'encounter_areas': len(AREAS),
        'spawn_markers': markers,
        'outdoor_chests': sum(1 for p in pois if p['kind'] == 'chest'),
        'points_of_interest': 0,      # filled in by run.sh from render_x7.py's census (figures.json)
        'dungeon_entrances': 5,
    }
    return {
        'format': 0,
        'level': 'L1',
        'pitch': "Cloudside's north-east corner: the world's volcano. From Vertigo's hills the north road climbs red "
                 "slopes past an abandoned dwarf watch and a dragon hermit's cave to the Firestone Gap; from there "
                 "the whole north lies below, grey with ash: a lava river crossing the flats to a lava lake, the "
                 "Volcano Cave and the Dragon Cave, a black tower on the rim, and Mount Firestone smoking over it "
                 "all, its lava pouring off the edge of the world into the stars.",
        'purpose': "Act V's trap and endgame map (party 40-55; the south slopes from level 5): Sablewing's Dragon "
                   "Master (D-5.2, levels 20-30), the seventh obelisk, the Orc Caves' back gate (XD-05), the "
                   "Ever-Hot Lava Rock (Q-C14), the Volcano Cave (XD-16, Q-C26) and Shangri-La's back gate "
                   "(XD-17), the Dragon Cave (XD-18, Q-C25, optional), the Dragon Tower (FD-04, Q-F1/Q-F2, "
                   "optional), the Fire Reflector (M37, Act VI).",
        'mood': "Grey ash drifting down through a dull red-brown light; heat shimmer over the flows; the roar of the "
                "crater and the hiss of lava; the south slopes merely dry and windy, the north scorched and still "
                "but for the wings overhead.",
        'datum': 'water:rim_sea',
        'spaces': spaces,
        'links': links,
        'entrances': entrances,
        'critical_path': ['edge:south_end', 'junction:slope_fork', 'zone:dwarf_watch', 'junction:gap',
                          'junction:lava_fork', 'zone:volcano_mouth'],
        'goals': [
            {'id': 'goal:sablewing', 'space': 'zone:sablewing_cave', 'kind': 'reach',
             'what': 'Learn Dragon Master from Sablewing (D-5.2).', 'story': 'D-5.2'},
            {'id': 'goal:obelisk', 'space': 'zone:the_gap', 'kind': 'use',
             'what': "Read the seventh Cloudside word (OBELISKS).", 'story': 'OBELISKS'},
            {'id': 'goal:lava_rock', 'space': 'zone:lava_island', 'kind': 'use',
             'what': "Take the Ever-Hot Lava Rock past its golems (Q-C14).", 'story': 'Q-C14'},
            {'id': 'goal:volcano', 'space': 'zone:volcano_mouth', 'kind': 'reach',
             'what': 'Enter the Volcano Cave; smash both skulls (Q-C26).', 'story': 'Q-C26'},
            {'id': 'goal:dragon_cave', 'space': 'zone:dragon_crag', 'kind': 'reach',
             'what': 'Pay the dragon tax at the Dragon Cave (Q-C25, optional).', 'story': 'Q-C25'},
            {'id': 'goal:reflector', 'space': 'zone:fire_corner', 'kind': 'use',
             'what': 'Wake the Fire Reflector (M37, after M36 starts).', 'story': 'M37'},
        ],
        'points_of_interest': pois,
        'landmarks': landmarks,
        'sightlines': sightlines,
        'states': states,
        'height_bands': [
            {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
            {'id': 'band:basin', 'range': [1500, 2600], 'spaces': ['zone:lava_basin', 'water:lava_lake'],
             'notes': 'The lava lake at 1,500; the Dragon Tower\'s crag to 2,600 at the rim.'},
            {'id': 'band:slopes', 'range': [1700, 2600], 'spaces': ['zone:south_slopes']},
            {'id': 'band:flats', 'range': [1900, 2700], 'spaces': ['zone:ash_flats', 'water:lava_river']},
            {'id': 'band:range', 'range': [1300, 3200], 'spaces': ['zone:red_dwarf_range'],
             'notes': 'Peaks 2,800-3,200; the Gap 2,300; the west road\'s valley 1,300-2,300.'},
            {'id': 'band:volcano', 'range': [2300, 5000], 'spaces': ['zone:firestone', 'water:crater',
                                                                     'water:lava_falls']},
        ],
        'landform': {
            'relief': "The south slopes (1,800-2,200) rise from X1's hills to the Red Dwarf Range (peaks to 3,200, "
                      "the Gap 2,300); the Firestone road climbs its valley from X4's 1,300. North of the range the "
                      "ash flats (1,900-2,500) fall west to the lava lake (1,500) and rise east into Mount Firestone, "
                      "a cone to 5,000 with a crater pool at 4,600. Inside the square: 1,500 to 5,000.",
            'height_range': [1500, 5000],
            'water': 'No water: the lava lake (about 250 cells), the crater pool, the lava river and its north arm '
                     '(lava liquid).',
            'water_share': 0.04,
            'caps': [{'kind': 'bare rock', 'share': 0.3,
                      'where': 'the range, Mount Firestone, the crags, the rim cliffs'},
                     {'kind': 'ash and cooled flow', 'share': 0.3, 'where': 'the north'}],
            'rim': {'notes': 'The world rim along the whole north (y 24) and east (x 104): a cliff of 1,500-2,900 '
                             'down to the stars; the lava falls pour over the north rim; the Dragon Tower and the '
                             'Dragon Cave stand on crags at its edge, the Fire Reflector on the corner spit. West '
                             'and south the land runs to the map edge; the roads run out to it.'},
        },
        'atmosphere': "Sky: the shipped fair preset with the ashen theme (A6's world sky.yml already lists "
                      "xeen_x7.odm: ashen); ash fall (WORLD_DESIGN 4: \"ash fall in X7\") from a weather row "
                      "(engine weather.yml's per-map ash chance; the studio has no word for it: NOTES); no rain; "
                      "music 26 (MM7 Mount Nighon). Lava hiss and the crater's rumble in the north, wind on the "
                      "slopes (E9's ODM ambient sounds).",
        'sketch': {'file': 'sketch.yml', 'grid': 512},
        'totals': totals,
        'notes': 'MU-3 for the phase 5 review (A5, 2026-11-20). Source geography: Clouds E1, E2, F1, F2 and D1\'s '
                 'lava lake (MAPS X7). Drawing and review board: output/studio_cal/x7/mockups/. Generated by '
                 'output/studio_cal/x7/tools/gen_l1.py.',
    }


ATMOSPHERE = {
    'format': 0,
    'sky_theme': 'ashen',
    'weather': {},
    'notes': "The world default sky (Cloudside's fair preset) with the shipped ashen theme (A6's world sky.yml "
             "already maps xeen_x7.odm to it); no rain or snow. Ash fall (WORLD_DESIGN 4) is engine weather.yml's "
             "per-map ash chance, which atmosphere.yml cannot say yet: asked of A1 (NOTES).",
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
    write('atmosphere.yml', ATMOSPHERE)
    print('written', OUT)


if __name__ == '__main__':
    import json
    import sys
    fig = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x7') / 'mockups/figures.json'
    count = None
    if '--with-census' in sys.argv and fig.exists():
        count = json.loads(fig.read_text())['poi_count']
    main(count)
