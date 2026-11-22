#!/usr/bin/env python3
"""X3 Lifeforce Lagoon: the L1 brief (MU-3 plan for gate G1), written from the data below (lane A5, 2026-11-20).

    python3 level_generation/projects/xeen/x3/gen_l1.py      # writes devdocs/xeen/briefs/x3/L1/{project,plan,sketch}.yml

Then `oymap fmt` and `oymap validate` the folder (run_l1.sh does all three and the drawings). Later passes edit this
script, not the YAML. Cells [x, y]: x east, y south, 512 units a cell. Heights are map units above the stars below the
rim (0): the lagoon at 860, the fens 900-1,000, Nightshadow 1,000, Ebenezer's camp 1,020, Newcastle's rise 1,750, the
Crow's Crown 3,450.
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'devdocs/xeen/briefs/x3/L1'
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ------------------------------------------------------------------ geometry (cells)

LAGOON = [[56, 65], [58, 60], [62, 57.5], [63, 57.5],
          # the causeway's west side, round the Tower's islet, up its east side
          [63, 66], [61, 66.5], [60.5, 69], [61.5, 72], [64.5, 73], [67.5, 72], [68.5, 69], [67.5, 66.5], [65, 66],
          [65, 57.5], [70, 56], [78, 57], [85, 59], [89, 63], [91, 69], [90, 76],
          # Mirabeth's spit off Nightshadow's south-west shore
          [88.5, 79.2], [85, 79.6], [84.2, 81], [85.2, 82.4], [87.6, 82.2],
          [86, 84.5], [82, 86], [75, 88], [68, 87], [62, 84], [58, 79], [56, 72]]
RIVER = [[56.5, 69], [50, 67.5], [44, 66], [38, 64.5], [30, 63], [22, 62], [10, 62], [0, 62]]
PONDS = {
    'water:fen_pool': ([[40, 70], [43.5, 69.5], [45, 72], [42, 73.5], [39.5, 72.5]], 885, 'A black pool in the fen.'),
    'water:gloom_pool': ([[23, 78], [27, 77.5], [28.5, 81], [25, 82.5], [22.5, 80.5]], 905,
                         "The Gloomwood's still pool, the drowned pilgrim's pack on its bank."),
    'water:drowned_pools': ([[64, 95], [69, 94], [71, 97], [67, 98.5], [63.5, 97]], 885, 'Pools on the Drowned Shore.'),
    'water:bog_pool': ([[33, 26], [36.5, 25.5], [37.5, 28.5], [34, 29.5]], 1240, 'A bog pool in the hills.'),
}
RIM_SEA = [[0, 105], [128, 105], [128, 128], [0, 128]]

ZONES = {  # space: polygon (the land partition; the lagoon cuts the middle)
    'zone:bogwood': [[0, 0], [47, 0], [47, 48], [42, 51], [0, 51]],
    'zone:north_vale': [[47, 0], [58, 0], [58, 22], [64, 30], [66, 42], [62, 49], [56, 52], [50, 53], [47, 48]],
    'zone:crow_hills': [[58, 0], [128, 0], [128, 36], [108, 37], [96, 37], [90, 30], [82, 26], [70, 25], [64, 30],
                        [58, 22]],
    'zone:newcastle_rise': [[64, 30], [70, 25], [82, 26], [90, 30], [93, 38.5], [83, 38.5], [76, 42], [66, 42]],
    'zone:east_meadow': [[93, 38.5], [96, 37], [108, 37], [128, 36], [128, 47], [112, 48], [102, 51], [94, 50],
                         [93, 46.5]],
    'zone:reedbeds': [[56, 52], [62, 49], [66, 42], [76, 42], [83, 38.5], [83, 46.5], [93, 46.5], [94, 50],
                      [102, 51], [100, 57], [92, 60], [89, 63], [85, 59], [78, 57], [70, 56], [62, 57.5], [58, 60],
                      [56, 63], [52, 58]],
    'zone:east_ridge': [[102, 51], [112, 48], [128, 47], [128, 104], [112, 104], [109, 82], [109, 62], [108, 57],
                        [100, 57]],
    'zone:black_fen': [[0, 51], [42, 51], [47, 48], [50, 53], [52, 58], [56, 63], [56, 72], [58, 79], [50, 79],
                       [40, 77], [0, 77]],
    'zone:gloomwood': [[0, 77], [40, 77], [50, 79], [58, 79], [60, 86], [56, 94], [54, 104], [0, 104]],
    'zone:drowned_shore': [[54, 104], [56, 94], [60, 86], [62, 84], [68, 87], [75, 88], [82, 86], [87, 84],
                           [94, 85], [103, 86], [109, 82], [112, 104]],
    'zone:rim': [[0, 104], [128, 104], [128, 128], [0, 128]],
}
TOWN_NIGHTSHADOW = [[92, 60], [100, 57], [108, 57], [109, 62], [109, 82], [103, 86.5], [94, 85.5], [90, 79],
                    [91, 69], [89, 63]]
SQUARE = [[97, 70], [102, 70], [102, 75], [97, 75]]
CAMP = [[83, 39.5], [93, 39.5], [93, 46.5], [83, 46.5]]
NEWCASTLE = [[77, 29.5], [88, 29.5], [88, 38], [77, 38]]
ISLET = [[60.5, 66], [68.5, 66], [68.5, 73], [60.5, 73]]
TOMB_SITE = [[29, 82], [39, 82], [39, 91], [29, 91]]
RANGER_CAMP = [[24, 31], [31, 31], [31, 37], [24, 37]]
GRAVEYARD = [[101.5, 81], [108, 81], [108, 86], [101.5, 86]]

# Encounter areas: (id, slot, markers, polygon, family, notes)
AREAS = [
    ('pop:bogwood_things', 1, 5, 'E1', [[19, 19], [44, 19], [44, 30], [46, 44], [44, 50], [19, 50]],
     'Swamp things in the hill bogs; the rangers\' camp placed in the middle.'),
    ('pop:bogwood_toads', 2, 3, 'E1', [[19, 19], [44, 19], [44, 30], [46, 44], [44, 50], [19, 50]],
     'Toads on the west and north edges.'),
    ('pop:fen_things', 1, 5, 'E2',   # F10: 6 -> 5, one to the north vale
     [[28, 52], [41, 52], [50, 55], [55, 62], [55, 74], [44, 76], [28, 74]],
     'Swamp things along the Lagoon Water; the west arrival keeps 6 cells clear.'),
    ('pop:fen_toads', 2, 2, 'E2', [[28, 52], [41, 52], [50, 55], [55, 62], [55, 74], [44, 76], [28, 74]],
     'Toads at the fen\'s west end.'),
    ('pop:gloomwood_dead', 3, 14, 'E3', [[19, 79], [44, 79], [56, 81], [58, 88], [54, 103], [19, 103]],
     'Zombies, ghouls and grave ghouls round the Tomb; none on the tomb door\'s step (2 cells).'),
    ('pop:shore_things', 1, 7, 'E4', [[58, 90], [66, 89.5], [76, 91], [86, 89.5], [94, 89], [108, 88.5],
                                      [108, 103], [56, 103]],
     'Swamp things on the Drowned Shore round the Lifeforce Spring and the wreck.'),
    ('pop:shore_dead', 3, 2, 'E4',   # F10: 4 -> 2, two to the reedbeds (the Gloomwood's 14 kept: a re-seeded
    # Gloomwood put a zombie 1,774 from XD-08's exit)
    [[58, 90], [66, 89.5], [76, 91], [86, 89.5], [94, 89], [108, 88.5],
                                    [108, 103], [56, 103]],
     'Drowned dead at the shore\'s west end, toward the Gloomwood.'),
    ('pop:crow_toads', 2, 3, 'E5', [[66, 19], [109, 19], [109, 35], [98, 35], [91, 31], [84, 26], [70, 25],
                                    [66, 23]],
     'Toads in the Crow Hills\' wet hollows: the first fight from the X2 road (about 4,900).'),
    # D-11.1 (2026-11-20): two of the Crow Hills' toad markers moved to the hills' south foot, so that the nearest
    # monsters stand about 6,000 from Ebenezer's camp and the Newcastle gate (5,000-6,500), not 8,200.
    ('pop:crow_foot', 2, 2, 'E5', [[92, 30], [96, 30], [96, 33], [92, 33]],
     "Toads at the Crow Hills' south foot, about 6,000 from the camp's doors and the Newcastle gate (D-11.1)."),
    # F10 (2026-11-21, the user found Xeen's outdoor land 'ultra empty'; tools/xeen/empty_zones.py): the north vale,
    # the reedbeds and the east ridge were one empty zone of 1,208 tiles (deepest 15,194), the paved roads a median
    # 7,768 from a monster. Seven single markers at fixed spots (FIRST_SPOTS), three of them moved from the fen and the
    # Gloomwood: D-11.1's 5,000-6,500 round the camp and the Newcastle gate, D-15's 2,000-6,000 from the edge
    # arrivals, D-85's 5,888 round Mirabeth and Nightshadow's 2,500 door buffer all hold.
    ('pop:vale_toads', 2, 2, 'E6', [[47, 20], [62, 20], [64, 30], [66, 42], [60, 50], [50, 53], [46, 46], [46, 30]],
     "Toads in the north vale's wet hollows, west of the road and below the obelisk's knoll (F10)."),
    ('pop:vale_things', 1, 1, 'E6', [[47, 20], [62, 20], [64, 30], [66, 42], [60, 50], [50, 53], [46, 46], [46, 30]],
     "Swamp things on the vale's east side, off the north road (F10)."),
    ('pop:reed_dead', 3, 2, 'E7', [[60, 44], [78, 43], [84, 48], [92, 50], [90, 58], [78, 56], [70, 55], [62, 50]],
     "Drowned dead in the reeds of the lagoon's north shore, by the camp road (F10)."),
    ('pop:reed_things', 1, 1, 'E7', [[60, 44], [78, 43], [84, 48], [92, 50], [90, 58], [78, 56], [70, 55], [62, 50]],
     "Swamp things at the reedbeds' east end, by the lagoon below the camp (F10)."),
    ('pop:ridge_toads', 2, 1, 'E8', [[100, 50], [108, 49], [108, 56], [100, 56]],
     "Toads on the east ridge's foot above the Nightshadow road, south of the meadow (F10)."),
]
# The spot of each arrival's first fight (counted in its area's markers; the studio keeps one marker there).
FIRST_SPOTS = {
    'pop:crow_toads': [[100, 33]],          # east arrival (X2)
    'pop:fen_toads': [[30, 56]],            # west arrival (X5)
    'pop:bogwood_toads': [[41, 26]],        # north arrival (X4)
    # L4 (2026-11-20): one marker of each of three areas set where the land lay farther than 6,000 from a place or
    # a fight (D-11.1's 6,000 rule): the Bogwood's north-west corner, the fen by the lagoon's west shore, the
    # Gloomwood's east edge
    'pop:bogwood_things': [[22, 22], [45, 45]],
    'pop:fen_things': [[52, 72]],
    'pop:gloomwood_dead': [[59, 83], [35, 100]],
    # F10: single markers at fixed spots (see AREAS)
    'pop:vale_toads': [[55, 27], [56, 47]],
    'pop:vale_things': [[60, 37]],
    'pop:reed_dead': [[68, 48], [76, 53]],
    'pop:reed_things': [[88, 57]],
    'pop:ridge_toads': [[103, 51]],
}
SPOT_NOTES = {pid: 'A single marker (F10: no land far from a fight).' for pid in (
    'pop:vale_toads', 'pop:vale_things', 'pop:reed_dead', 'pop:reed_things', 'pop:ridge_toads')}
AREA_NAMES = {'E1': 'Bogwood', 'E2': 'Black Fen', 'E3': 'Gloomwood', 'E4': 'Drowned Shore', 'E5': 'Crow Hills',
              'E6': 'North vale', 'E7': 'Reedbeds', 'E8': 'East ridge'}   # E6-E8: F10
SLOT_MEAN = {1: 2.5, 2: 3.0, 3: 2.5}

QUIET = [  # keep_clear / open areas
    ('town:nightshadow', 'keep_clear', [[88, 55], [111, 55], [111, 86], [100, 88.5], [92, 88], [86, 82], [88, 62]],
     'Nightshadow and its buffer (about 2,500 round the doors).'),
    ('town:ebenezer_camp', 'keep_clear', [[78, 36], [98, 36], [98, 50], [78, 50]],
     "Ebenezer's camp and the Newcastle gate: no spawns."),
    ('town:newcastle', 'keep_clear', [[72, 27], [90, 27], [90, 38], [72, 38]], 'The ruin on its rise.'),
    ('zone:east_meadow', 'keep_clear', [[96, 37], [109, 37], [109, 50], [96, 50]],
     'The arrival from X2: open meadow by the road.'),
    ('zone:north_vale', 'open', [[57, 28], [62, 28], [62, 32], [57, 32]],
     'Quiet on purpose: the obelisk\'s knoll (F10: the rest of the vale holds three markers).'),
    ('zone:reedbeds', 'open', [[56, 52], [62, 49], [66, 50], [67, 56], [64, 56.5], [58, 59.5], [53, 57]],
     'The causeway head and the X8 landing (F10: the rest of the reedbeds holds three markers).'),
    ('zone:west_landing', 'keep_clear', [[19, 53], [27, 53], [27, 72], [19, 72]],
     "The arrival from X5 and the eel-fisher's hut."),
    ('water:lagoon', 'open', LAGOON, 'The water: open on purpose, the Tower on its islet in the middle.'),
]

# Points (cells); kind is for the drawing: entrance, dungeon, junction, poi, chest, npc, camp, landmark, device
POINTS = [
    ('entrance:east_road', [106, 40.5], 'w', 'entrance', None),
    ('entrance:west_road', [21, 59], 'e', 'entrance', None),
    ('entrance:north_road', [50, 21], 's', 'entrance', None),
    ('entrance:nightshadow_square', [100, 75], 's', 'entrance', 'square (TP, mirror, 3 sundials)'),
    ('entrance:newcastle_gate', [82, 38.5], 's', 'entrance', 'Newcastle gate (mirror)'),
    ('entrance:camp_fire', [87.5, 45.2], 'n', 'entrance', None),
    ('entrance:x8_landing', [66.5, 53.5], 's', 'entrance', 'X8 fall landing'),
    ('entrance:xd13_keep', [82, 33], 's', 'dungeon', 'XD-13 Newcastle Keep'),
    ('entrance:xd11_tower', [64.5, 67.5], 'n', 'dungeon', 'XD-11 Tower of High Magic'),
    ('entrance:xd08_tomb', [34, 82.5], 'n', 'dungeon', 'XD-08 Tomb of a Thousand Terrors'),
    ('entrance:xd24_crypt', [99, 73], 'n', 'dungeon', "XD-24 (Draco's coffin)"),
    ('junction:lagoon_cross', [94, 42.5], None, 'junction', 'Lagoon Cross'),
    ('junction:causeway_fork', [63, 52], None, 'junction', 'Causeway fork'),
    ('junction:fen_fork', [35, 58.5], None, 'junction', 'Fen fork'),
    ('junction:tomb_fork', [34, 79], None, 'junction', 'Tomb fork'),
    ('poi:obelisk', [59.5, 30], None, 'device', 'Obelisk'),
    ('poi:marsh_well', [58.5, 46.5], None, 'device', 'Marsh Well (resistances)'),
    ('poi:lifeforce_spring', [74, 93.5], None, 'device', 'Lifeforce Spring (+2 End.)'),
    ('poi:food_trees', [25.5, 62.8], None, 'device', 'food tree'),
    ('poi:food_trees', [95.5, 55.5], None, 'device', 'food tree'),
    ('poi:mirabeth', [84.6, 81], None, 'npc', "Mirabeth's rock"),
    ('poi:sundials', [98, 71], None, 'device', None),
    ('poi:sundials', [101, 71], None, 'device', None),
    ('poi:sundials', [101, 74], None, 'device', None),
    ('poi:count_sign', [97, 70], None, 'device', None),
    ('poi:rhyme_board', [100, 73], None, 'device', None),
    ('poi:draco_coffin', [99, 73], None, 'device', None),
    ('poi:town_well', [98, 74], None, 'device', None),
    ('poi:nightshadow_mirror', [100, 71], None, 'device', None),
    ('poi:newcastle_mirror', [80.6, 37.4], None, 'device', None),
    ('poi:ebenezer_fire', [85, 45.3], None, 'camp', None),
    ('poi:work_yard', [76.5, 38.5], None, 'chest', "Emerson's work yard"),
    ('poi:ranger_camp', [27.5, 34], None, 'camp', "Rangers' camp (burn)"),
    ('poi:ranger_chest', [29.8, 35.8], None, 'chest', None),
    ('poi:sunken_punt', [59, 59], None, 'chest', 'Sunken punt'),
    ('poi:tax_coffer', [76.5, 54.8], None, 'chest', "Ebenezer's lost coffer"),
    ('poi:eel_fisher', [23.5, 65.5], None, 'chest', "Eel-fisher's hut"),
    ('poi:pilgrim_pack', [29.3, 80.3], None, 'chest', "Pilgrim's pack"),
    ('poi:wreck', [76.5, 99], None, 'chest', 'Wreck on the rim'),
    ('poi:crow_watchtower', [98, 25.5], None, 'chest', 'Fallen watchtower'),
    ('poi:sexton_shed', [102.6, 84.6], None, 'chest', None),
    ('poi:sunken_graves', [38.8, 82.8], None, 'device', 'Sunken graves'),
    ('poi:garlic_shrine', [98.8, 53.5], None, 'device', 'Garlic shrine'),
    ('poi:signposts', [94, 42.5], None, 'junction', None),
    ('poi:signposts', [63, 52], None, 'junction', None),
    ('poi:signposts', [35, 58.5], None, 'junction', None),
    ('poi:signposts', [34, 79], None, 'junction', None),
    ('landmark:high_magic', [64.5, 69.5], None, 'landmark', None),
    ('landmark:newcastle', [82.5, 33], None, 'landmark', None),
    ('landmark:nightshadow_mist', [100, 72], None, 'landmark', None),
    ('landmark:crow_crown', [102, 22], None, 'landmark', "Crow's Crown 3,450"),
    ('landmark:tomb_mound', [34, 86.5], None, 'landmark', None),
]

# Height points
HPOINTS = [
    ([106, 40.5], 1024, 'the X2 arrival (X2\'s west road level)'),
    ([94, 42.5], 990, 'Lagoon Cross'),
    ([87, 43.5], 1020, "Ebenezer's camp"),
    ([82.5, 33], 1750, "Newcastle's rise, the ruin's floor"),
    ([79, 31], 1750, None), ([86, 32], 1750, None), ([82, 37.5], 1700, 'the gate'),
    ([74, 34], 1450, "the rise's west shoulder"),
    ([92, 30], 2000, None), ([96, 27], 2400, None), ([98, 25.5], 2300, 'the fallen watchtower'),
    ([102, 22], 3450, "the Crow's Crown, the map's high point"),
    ([92, 21], 2700, None), ([108, 26], 2900, None), ([80, 22], 2000, None), ([70, 21], 2050, None),
    ([59.5, 30], 1550, "the obelisk's knoll"), ([57, 30], 1450, None), ([51, 22], 1300, 'the X4 arrival'),
    ([63, 52], 960, 'Causeway fork'), ([64.5, 69.5], 1050, "the Tower's islet"),
    ([27.5, 34], 1350, "the rangers' knoll"), ([36, 22], 1700, None), ([25, 24], 1900, None),
    ([40, 40], 1400, None), ([30, 45], 1200, None),
    ([35, 58.5], 920, 'Fen fork'), ([21, 59], 900, 'the X5 arrival (X5\'s fen level)'),
    ([34, 86.5], 1250, "the Tomb's mound"), ([38.8, 82.8], 1100, 'the sunken graves'), ([24, 92], 1100, None),
    ([48, 84], 1000, None),
    ([74, 93.5], 1000, "the Lifeforce Spring's knoll"), ([76.5, 99], 950, 'the wreck above the rim'),
    ([99.5, 72.5], 1000, 'Nightshadow square'), ([105, 83.5], 1060, 'the churchyard'),
    ([112, 70], 2100, 'the east ridge over Nightshadow'), ([114, 58], 2200, None),
]
RIDGES = [
    ([[90, 22], [96, 21], [102, 22], [108, 23], [114, 21]], 3000, 2, 3, "The Crow Hills' crest, north-east."),
    ([[112, 52], [113, 62], [112, 74], [113, 88]], 2300, 2, 3,
     'The east ridge behind Nightshadow (X2\'s west hills go on beyond the edge).'),
]
CLIFFS = [
    ([[0, 104], [40, 104], [80, 104], [128, 104]], 900, 'right',
     'The world rim (drawn west to east, the low side south): land 900-1,100 to the stars at 0, as on X2 and X5.'),
    ([[77, 29], [77, 37]], 300, 'left', "Newcastle's rise: a low crag under the ruin's west wall."),
]

# Roads (link, line, width, surface)
ROADS = [
    ('link:east_road', [[128, 40], [116, 40], [106, 40.5], [99, 41.5], [94, 42.5]], 'road', 'road_pebbles'),
    ('link:camp_road', [[94, 42.5], [90, 43.8], [86, 44.2], [80, 45.5], [74, 47.5], [68, 49.5], [63, 52]], 'road',
     'road_pebbles'),
    ('link:north_road', [[63, 52], [60, 46], [57, 38], [54, 30], [51, 22], [50, 12], [50, 0]], 'road', 'soil'),
    ('link:west_road', [[63, 52], [58, 54], [52, 55.5], [46, 57], [40, 58], [35, 58.5], [28, 59], [20, 59], [0, 59]],
     'road', 'soil'),
    ('link:nightshadow_road', [[94, 42.5], [95.5, 48], [97, 54], [98.5, 59], [99.5, 62], [99.5, 70]], 'road',
     'road_pebbles'),
    ('link:south_street', [[100, 75], [101, 79], [102.5, 82], [103, 84.5]], 'lane', None),
    ('link:quay_lane', [[97, 77.5], [94, 77.8], [91, 78.5], [89, 79.8]], 'lane', None),
    ('link:newcastle_stair', [[86, 44.2], [84, 41.5], [82.5, 39.5], [82, 37.8]], 'lane', None),
    ('link:causeway', [[63, 52], [64, 57], [64, 62], [64.5, 66.5]], 'lane', None),
    ('link:tomb_path', [[35, 58.5], [36, 61], [37, 63.5], [36, 68], [34.5, 74], [34, 79]], 'lane', None),
    ('link:tomb_lane', [[34, 79], [34, 82]], 'lane', None),
    ('link:gloom_path', [[34, 79], [42, 84], [50, 88], [58, 90.5], [66, 92], [74, 93.5]], 'lane', None),
    ('link:shore_path', [[103, 84.5], [96, 87.5], [88, 89], [80, 91.5], [74, 93.5]], 'lane', None),
]

# Buildings: (space, id, service, footprint [front, depth]) and plots (id, index, at, facing, door_to, kit, house id)
BUILDINGS = {
    'town:nightshadow': [
        ('building:moon_guild', 'The Moon Guild (houses 4103, 4104 after q-c7.done)', [2, 2]),
        ('building:du_monay_manor', 'Du Monay Manor (house 4105, the open house)', [2.5, 2.5]),
        ('building:nightshadow_temple', 'Temple of the Dawn (house 4106)', [2.5, 2.5]),
        ('building:nightshadow_tavern', 'The Coffin and Candle (house 4107)', [2, 1.5]),
        ('building:treasure_trove', 'Treasure Trove (house 4108)', [1.5, 1.5]),
        ('building:nightshadow_alchemist', 'Garlic and Grave Goods (house 4109)', [1.5, 1.5]),
        ('building:gnome_home', 'Gnome Home (house 4111)', [1.5, 1.5]),
    ],
    'town:ebenezer_camp': [
        ('building:ebenezer_tent', "Ebenezer's Tent (house 4101, tavern)", [2, 1.5]),
        ('building:camp_shrine', 'The Camp Shrine (house 4102, temple)', [1.5, 1.5]),
    ],
}
NS_HOUSES = [  # building:nightshadow_houses, index 1-9 = houses 4112-4120
    ([96, 61], 'e', [1, 1.5], 'poor'), ([96, 68], 'e', [1, 1], 'timber'), ([101, 64.5], 'w', [1, 1], 'poor'),
    ([97, 76], 'n', [1, 1.5], 'plaster'), ([94.5, 78.5], 'n', [1, 1], 'poor'), ([96.5, 78.5], 'n', [1.5, 1], 'timber'),
    ([93, 75.5], 's', [1, 1], 'poor'), ([103, 76], 'w', [1, 1.5], 'grey'), ([103, 78.5], 'w', [1, 1], 'poor'),
]
NS_HOUSE_NAMES = ["Agatha's House", "The Sexton's House", "Lenore's House", 'Crow House', 'Vey Residence',
                  "Ambrose's Lean-to", "The Dial Keeper's House", "The Lamplighter's", 'Wick House']
PLOTS = {
    'town:nightshadow': [
        ('building:moon_guild', None, [95, 65.5], 'e', 'link:nightshadow_road', 'stone', 4103),
        ('building:du_monay_manor', None, [102, 66.5], 'w', 'link:nightshadow_road', 'stone', 4105),
        ('building:nightshadow_temple', None, [94, 70.5], 'e', 'zone:nightshadow_square', 'stone', 4106),
        ('building:nightshadow_tavern', None, [101, 61.5], 'w', 'link:nightshadow_road', 'timber', 4107),
        ('building:treasure_trove', None, [102.5, 70.5], 'w', 'zone:nightshadow_square', 'plaster', 4108),
        ('building:nightshadow_alchemist', None, [102.5, 72.5], 'w', 'zone:nightshadow_square', 'timber', 4109),
        ('building:gnome_home', None, [95.5, 63], 'e', 'link:nightshadow_road', 'poor', 4111),
    ] + [('building:nightshadow_houses', i + 1, at, f, None, kit, 4112 + i) for i, (at, f, _, kit) in
         enumerate(NS_HOUSES)],
    'town:ebenezer_camp': [
        ('building:ebenezer_tent', None, [85.5, 41.5], 's', 'link:camp_road', 'plaster', 4101),
        ('building:camp_shrine', None, [88.5, 45], 'n', 'link:camp_road', 'stone', 4102),
    ],
}

# Placed actors (monster row, at, count, spread, group, notes)
ACTORS = [
    ('11131', [27.5, 34], 4, 2, 1, 'Evil Rangers 12 round the fire.'),
    ('11132', [28.5, 33], 2, 1, 1, 'Elite Rangers 18.'),
    ('11130', [26, 35.5], 1, 0, 1, 'An Evil Archer 8 on watch.'),
    ('11310', [100, 94], 2, 1, 2, 'Bat Queens 10 in the dead trees below the churchyard.'),
    ('11311', [101, 95], 2, 1, 2, 'Vampire Bats 14.'),
    ('11310', [92, 96], 2, 1, 3, 'Bat Queens 10 over the shore pools.'),
    ('11311', [93, 96.5], 1, 0, 3, 'Vampire Bat 14.'),
    ('11312', [91.5, 95.5], 1, 0, 3, 'Beholder Bat 20.'),
]
XP = {  # per monster (L(L+10)), and the A/B/C mix assumed for a slot at tier 1
    1: [600, 936, 1344], 2: [75, 144, 231], 3: [144, 264, 504],
    '11130': 144, '11131': 264, '11132': 504, '11310': 200, '11311': 336, '11312': 600,
}
TIER_MIX = [0.5, 0.35, 0.15]

# Notes on sketch points (the quest hooks that stand there), by (id, index of that id from 1)
POINT_NOTES = {
    ('entrance:xd24_crypt', 1): "Count Draco's coffin on the square: hooks q-c7.coffin and q-c7.sign_night (the plinth).",
    ('poi:draco_coffin', 1): 'hooks q-c7.coffin (the stair down to XD-24) and q-c7.sign_night (the sign on its plinth)',
    ('poi:rhyme_board', 1): 'hook q-c7.rhyme: the signboard by the coffin; sets q-c7.started',
    ('poi:count_sign', 1): "hook q-c7.sign_nine: the sign at the dial walk's entrance",
    ('poi:sundials', 1): 'sundial 1, hook q-c7.clue_stitch on its plinth; dials_set rule: see the plan',
    ('poi:sundials', 2): 'sundial 2, hook q-c7.clue_cat on its plinth; dials_set rule: see the plan',
    ('poi:sundials', 3): 'sundial 3; dials_set rule: see the plan',
    ('poi:town_well', 1): 'hook q-c7.well: the town well, its magic only after q-c7.done',
}

VIEWS = [
    {'id': 'view:arrival', 'at': [106, 40.5], 'height': 180, 'look': [76, 47.5],
     'purpose': ("MU-4 arrival view: on the road in from X2, looking west-south-west. Ahead the road runs down to "
                 "Lagoon Cross and Ebenezer's camp (tents, smoke); Newcastle's ruined walls on their rise to the "
                 "right; the lagoon opening on the left with the Tower of High Magic on its islet far off; the mist "
                 "bank over Nightshadow at the left edge.")},
    {'id': 'view:signature', 'at': [63, 55.5], 'height': 180, 'look': [73.6, 71],
     'purpose': ("MU-4 signature view, from the causeway head on the lagoon's north shore, looking south-east: the "
                 "stone causeway runs out across the water to the Tower of High Magic on its rock (right); "
                 "Mirabeth's rock in the middle distance; across the lagoon Nightshadow's dark roofs and spire in "
                 "a grey bank of mist under a low sky (left).")},
]


# ------------------------------------------------------------------ snapping (the studio's rule)
# Every sketch coordinate is a whole cell, but road lines and plot corners, which may use half cells.

def _snap(v, step):
    import math
    if isinstance(v, (int, float)):
        r = math.floor(v / step + 0.5) * step
        return int(r) if float(r).is_integer() else r
    return [_snap(x, step) for x in v]


LAGOON = _snap(LAGOON, 1)
RIVER = _snap(RIVER, 1)
PONDS = {k: (_snap(p, 1), lvl, n) for k, (p, lvl, n) in PONDS.items()}
ZONES = {k: _snap(p, 1) for k, p in ZONES.items()}
TOWN_NIGHTSHADOW, SQUARE, CAMP, NEWCASTLE, ISLET, TOMB_SITE, RANGER_CAMP, GRAVEYARD = (
    _snap(p, 1) for p in (TOWN_NIGHTSHADOW, SQUARE, CAMP, NEWCASTLE, ISLET, TOMB_SITE, RANGER_CAMP, GRAVEYARD))
AREAS = [(a[0], a[1], a[2], a[3], _snap(a[4], 1), a[5]) for a in AREAS]
QUIET = [(q[0], q[1], _snap(q[2], 1), q[3]) for q in QUIET]
POINTS = [(p[0], _snap(p[1], 1), p[2], p[3], p[4]) for p in POINTS]
HPOINTS = [(_snap(h[0], 1), h[1], h[2]) for h in HPOINTS]
RIDGES = [(_snap(r[0], 1),) + tuple(r[1:]) for r in RIDGES]
CLIFFS = [(_snap(c[0], 1),) + tuple(c[1:]) for c in CLIFFS]
FIRST_SPOTS = {k: _snap(v, 1) for k, v in FIRST_SPOTS.items()}
ROADS = [(r[0], _snap(r[1], 0.5), r[2], r[3]) for r in ROADS]
PLOTS = {k: [(p[0], p[1], _snap(p[2], 0.5)) + tuple(p[3:]) for p in v] for k, v in PLOTS.items()}
for _v in VIEWS:
    _v['at'], _v['look'] = _snap(_v['at'], 1), _snap(_v['look'], 1)


# ------------------------------------------------------------------ the three files

def flow(d):
    return d


def project():
    return {
        'format': 0,
        'id': 'xeen_x3',
        'name': 'Lifeforce Lagoon',
        'world': 'xeen',
        'kind': 'outdoor',
        'profile': 'odm',
        'map_code': 'X3',
        'units': {'plan_grid': 512},
        'extent': {'terrain_cells': 128},
        'map_stats': {
            'id': 9101, 'continent': 6, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 2,
            'perception_difficulty': 2, 'refill_days': 672, 'music': 48, 'environment': 'plains',
            'lock_difficulty': 4,
            'slots': [
                {'monster': 'Xeen Swamp Thing', 'tier': 1, 'per_marker': [2, 3], 'weight': 40},
                {'monster': 'Xeen Toad', 'tier': 1, 'per_marker': [2, 4], 'weight': 20},
                {'monster': 'Xeen Zombie', 'tier': 1, 'per_marker': [2, 3], 'weight': 40},
            ],
        },
        'neighbours': [
            {'id': 'edge:east', 'to': 'xeen_x2.odm', 'kind': 'edge', 'side': 'east', 'days': 5, 'arrival_side': 'west',
             'approach': "The lagoon road west from Rivercity's west road, at y 40 on both maps.",
             'notes': ("X2 Rivercity and Lake Darzog, the main way in (party 13). X2 seals its west edge today "
                       "with the flooded sign at [20.6, 39.1]; the sign goes when X3 is installed.")},
            {'id': 'edge:west', 'to': 'xeen_x5.odm', 'kind': 'edge', 'side': 'west', 'days': 5,
             'arrival_side': 'east',
             'approach': "The fen road along the Lagoon Water's north bank, at y 59; the river at y 62.",
             'notes': "X5 Winterkill Tundra: lands in X5's east pocket (its lagoon road at y 59)."},
            {'id': 'edge:north', 'to': 'xeen_x4.odm', 'kind': 'edge', 'side': 'north', 'days': 5,
             'arrival_side': 'south',
             'approach': "The north road up the vale between the Bogwood and the Crow Hills, at x 50.",
             'notes': ("X4 Burlock Savannah (D-11.6): X3's north road leaves at x 50 and arrives at X4's own "
                       "south arrival on its road at x 36; X4's south edge west of x 64 arrives here at x 50 "
                       "(entrance:north_road). Neither road moves; each arrival faces inward.")},
            {'id': 'door:xd13', 'to': 'xeen_xd13.blv', 'kind': 'door',
             'arrival_hint': "At the foot of the foundation stair inside the ruin.",
             'notes': ("XD-13 Newcastle Keep (staged). The stair down into the ruin's foundation (wood golems at "
                       "stage 0, M8); the keep's houses come with its stages (xd13.yml).")},
            {'id': 'door:xd11', 'to': 'xeen_xd11.blv', 'kind': 'door', 'condition': {'item': 'enchanted_key'},
             'arrival_hint': "Inside the tower's door.",
             'notes': ("XD-11 Tower of High Magic (M13): the door on the islet at the causeway's end; the Enchanted "
                       "Key from the Cave of Illusion (M12). Its roof's Stairway to Heaven leads up to X8.")},
            {'id': 'door:xd08', 'to': 'xeen_xd08.blv', 'kind': 'door', 'condition': {'item': 'stone_of_terrors'},
             'arrival_hint': "Inside the tomb door, by the statue with the plaque.",
             'notes': ("XD-08 Tomb of a Thousand Terrors (M10): the tomb door in the Gloomwood's mound; "
                       "Ebenezer's Stone of a Thousand Terrors after the walls (M9).")},
            {'id': 'door:xd24', 'to': 'xeen_xd24.blv', 'kind': 'door',
             'condition': {'qbit': 'nightshadow_dials_set'},
             'arrival_hint': "At the foot of the coffin's stair, inside the crypt.",
             'notes': ("XD-24 Nightshadow Crypt (Q-C7): Count Draco's coffin on Nightshadow's square opens on a stair "
                       "down to the crypt once all three sundials read 9 (q-c7.dials_set) and it is night (21-6, "
                       "Xeen.isNight); q-c7.coffin sets q-c7.coffin_opened.")},
            {'id': 'fall:x8', 'to': 'xeen_x8.blv', 'kind': 'fall', 'listed_only': True,
             'notes': ("Inbound only: a fall from the High Magic Clouds (X8, west of x 0) lands at "
                       "entrance:x8_landing on the reed shore by the causeway head.")},
        ],
        'qbits': {
            'newcastle_deed': 111160,
            'newcastle_walls': 111181,
            'newcastle_keep': 111221,
            'nightshadow_started': 112140,
            'nightshadow_dials_set': 112142,
            'nightshadow_coffin_opened': 112143,
            'nightshadow_liberated': 112141,
            'mirabeth_gone': 112240,
            'mirror_nightshadow': 119005,
            'mirror_newcastle': 119006,
        },
        'items': {
            'deed_to_newcastle': 12303,
            'stone_of_terrors': 12304,
            'golem_stone': 12305,
            'enchanted_key': 12306,
        },
        'rules': {
            'weather': 'world default; Nightshadow keeps a local mist (always overcast) until q-c7.done',
            'town_portal_anchor': 'entrance:nightshadow_square',
            'respawn': 'entrance:camp_fire',
        },
        'notes': ("X3 Lifeforce Lagoon, MU-3 plan for gate G1 (lane A5, 2026-11-20). No geometry until the user "
                  "has seen it. Plan: plan.yml; to-scale layout: sketch.yml; drawings and review board: "
                  "output/studio_cal/x3/mockups/ (board_x3.png). Written by output/studio_cal/x3/tools/gen_l1.py."),
    }


def pop(pid, slot, groups, notes):
    return {'id': pid, 'slot': slot, 'groups': groups, 'per_marker': [2, 4] if slot == 2 else [2, 3],
            'notes': notes}


def plan(figures):
    areas = {a[0]: a for a in AREAS}

    def pops(*ids):
        out = []
        for pid in ids:
            a = areas[pid]
            out.append(pop(pid, a[1], a[2], f'{a[3]} {AREA_NAMES[a[3]]}: {a[5]}'))
        return out

    spaces = [
        # ---- the east: arrival, the camp, Newcastle ----
        {'id': 'zone:east_meadow', 'name': 'The lagoon road', 'kind': 'zone', 'floor': [1000, 1100],
         'where': 'east, from the X2 edge to Lagoon Cross, y 37 to 50',
         'purpose': "The arrival from X2: the road comes over X2's hill gap at 1,024 and runs down to the lagoon country.",
         'safe': True, 'keep_clear': ['spawns']},
        {'id': 'zone:crow_hills', 'name': 'The Crow Hills', 'kind': 'wild', 'floor': [1600, 3450], 'relief': 'uneven',
         'density': 'sparse',
         'purpose': "Dark wooded hills north of the road rising to the Crow's Crown (3,450), the map's high point; "
                    "toads in the wet hollows, a fallen watchtower with a view over the whole lagoon.",
         'population': pops('pop:crow_toads', 'pop:crow_foot')},
        {'id': 'zone:newcastle_rise', 'name': "Newcastle's rise", 'kind': 'zone', 'floor': [1020, 1750],
         'purpose': "The rise above the camp: rough grass, broken walls on the top, Emerson's work yard on the west shoulder.",
         'safe': True, 'keep_clear': ['spawns']},
        {'id': 'town:newcastle', 'name': 'Newcastle', 'kind': 'town', 'part_of': 'zone:newcastle_rise',
         'floor': 1750,
         'purpose': ("The party's castle site (M8-M23): stage 0 a ruin of weathered brown castle stone (Harmondale's ch1b1 ruin "
                     "pieces) with the foundation stair (XD-13); stage 1 walls (m9.walls); stage 2 the keep "
                     "(m11.keep: smith and training inside, the mirror 4121 at the gate); stage 3 the dungeon dug."),
         'safe': True, 'keep_clear': ['spawns'],
         'theme': 'Royal castle kit (royal_castle: ch1b1 ruin pieces at stages 0-1, hc walls and gate at 2+).'},
        {'id': 'town:ebenezer_camp', 'name': "Ebenezer's camp", 'kind': 'town', 'floor': 1020,
         'where': "at the foot of Newcastle's rise, on the camp road west of Lagoon Cross",
         'purpose': ("Open from day one, outside Nightshadow's curse (WORLD_DESIGN 5.1): Ebenezer's tent (tavern; "
                     "he sells the deed, M8) and Brother Tobit's camp shrine (temple). Where a defeated party wakes."),
         'safe': True, 'keep_clear': ['spawns'],
         'theme': "A big striped tent and a fieldstone shrine (cloudside_town chb1), a fire, carts and timber stacks.",
         'buildings': [{'id': b, 'type': 'house', 'service': s, 'count': 1, 'doors': 1, 'footprint_cells': fp}
                       for b, s, fp in BUILDINGS['town:ebenezer_camp']]},
        # ---- the lagoon ----
        {'id': 'water:lagoon', 'name': 'The Lifeforce Lagoon', 'kind': 'water',
         'purpose': ("Still green-black water with reed beds, about 900 cells: the Tower of High Magic on its rock "
                     "islet joined to the north shore by a causeway, Mirabeth's rock off Nightshadow's shore. "
                     "Drains west by the Lagoon Water to X5.")},
        {'id': 'zone:tower_islet', 'name': "The Tower's islet", 'kind': 'zone', 'part_of': 'water:lagoon',
         'floor': 1050, 'purpose': "A rock in the lagoon at the causeway's end; the Tower of High Magic on it."},
        {'id': 'water:river', 'name': 'The Lagoon Water', 'kind': 'water',
         'purpose': "The lagoon's outflow west through the Black Fen to the edge (y 62), on into X5's pocket."},
        {'id': 'zone:reedbeds', 'name': 'The Reedbeds', 'kind': 'wild', 'floor': [880, 1000], 'relief': 'flat',
         'density': 'medium',
         'purpose': "The lagoon's north shore: reeds, willows, the causeway head, the Marsh Well, a food tree, "
                    "a sunken punt; drowned dead and swamp things in the reeds (F10).",
         'population': pops('pop:reed_dead', 'pop:reed_things')},
        # ---- Nightshadow ----
        {'id': 'town:nightshadow', 'name': 'Nightshadow', 'kind': 'town', 'floor': 1000,
         'where': "the lagoon's east shore, in a hollow under the east ridge",
         'purpose': ("The cursed vampire town (Q-C7) in perpetual mist: before q-c7.done only the Moon Guild (night "
                     "hours) and Du Monay Manor open; the rest opens when Count Draco dies. The three sundials, the "
                     "signs, the town well and Count Draco's coffin (the stair to XD-24) on the square."),
         'safe': True, 'keep_clear': ['spawns'], 'density': 'medium',
         'theme': ("Cloudside half-timber kit (MU-5), its darkest grades: grey daub and grey planks, dark oak, "
                   "slate-grey shingle; the temple and the manor in chb1 fieldstone; shutters closed, garlic on "
                   "doors; a low broken wall on the land side."),
         'buildings': [{'id': b, 'type': 'house', 'service': s, 'count': 1, 'doors': 1, 'footprint_cells': fp}
                       for b, s, fp in BUILDINGS['town:nightshadow']] +
                      [{'id': 'building:nightshadow_houses', 'type': 'house',
                        'service': 'residence (houses 4112-4120)', 'count': 9, 'doors': 1,
                        'footprint_cells': [fp for _, _, fp, _ in NS_HOUSES]}]},
        {'id': 'zone:nightshadow_square', 'name': 'Nightshadow square', 'kind': 'zone', 'part_of': 'town:nightshadow',
         'floor': 1000, 'empty': True, 'safe': True,
         'purpose': ("The dial walk with three sundials, Count Draco's coffin on its plinth (XD-24's stair), the "
                     "rhyme signboard, the town well, the mirror (4110); the Town Portal arrival.")},
        {'id': 'zone:churchyard', 'name': 'The churchyard', 'kind': 'zone', 'part_of': 'town:nightshadow',
         'floor': 1060, 'purpose': "Leaning stones, dead trees, the sexton's shed."},
        {'id': 'zone:east_ridge', 'name': 'The east ridge', 'kind': 'wild', 'floor': [1100, 2700],
         'purpose': "Bare slopes behind Nightshadow rising to X2's western hills: holds the mist in the hollow; a "
                    "garlic-hung wayside shrine at its foot by the Nightshadow road; toads at its north foot (F10).",
         'population': pops('pop:ridge_toads')},
        # ---- the west and south ----
        {'id': 'zone:north_vale', 'name': 'The north vale', 'kind': 'wild', 'floor': [960, 1450], 'relief': 'slope',
         'density': 'sparse',
         'purpose': "The north road's valley from the causeway fork up to X4: open grass, the obelisk on its knoll; "
                    "toads and swamp things off the road (F10).",
         'population': pops('pop:vale_toads', 'pop:vale_things')},
        {'id': 'zone:bogwood', 'name': 'The Bogwood', 'kind': 'wild', 'floor': [1100, 1900], 'relief': 'uneven',
         'density': 'dense',
         'purpose': ("Dark marsh woods on broken hills north-west (swamp trees, tree60/tree65): the evil rangers' "
                     "camp on a dry knoll, a bog pool."),
         'population': pops('pop:bogwood_things', 'pop:bogwood_toads') +
                       [{'id': 'pop:ranger_camp', 'actor': 'Xeen Ranger', 'groups': 1, 'placed': True,
                         'hostile': True, 'notes': "Seven rangers (8-18) at their camp (the source's C4 camp)."}]},
        {'id': 'zone:black_fen', 'name': 'The Black Fen', 'kind': 'wild', 'floor': [880, 1000], 'relief': 'flat',
         'density': 'medium',
         'purpose': "Reeds, mud flats and black pools along the Lagoon Water: the fen road to X5, Fen fork, a food tree.",
         'population': pops('pop:fen_things', 'pop:fen_toads')},
        {'id': 'zone:west_landing', 'name': 'The fen landing', 'kind': 'zone', 'part_of': 'zone:black_fen',
         'floor': 900, 'safe': True, 'keep_clear': ['spawns'],
         'purpose': "Where the party comes in from X5: the eel-fisher's hut on stilts by the river."},
        {'id': 'zone:gloomwood', 'name': 'The Gloomwood', 'kind': 'wild', 'floor': [950, 1250], 'relief': 'uneven',
         'density': 'dense',
         'purpose': ("Dead marsh woods (dead tree41, swptree) south of the river: the Tomb of a Thousand Terrors in "
                     "its mound, sunken graves, the still pool; the walking dead."),
         'population': pops('pop:gloomwood_dead')},
        {'id': 'zone:tomb', 'name': 'The Tomb mound', 'kind': 'zone', 'part_of': 'zone:gloomwood', 'floor': 1250,
         'purpose': "A grassed mound faced with black stone and iron; the tomb door in its north face (XD-08)."},
        {'id': 'zone:drowned_shore', 'name': 'The Drowned Shore', 'kind': 'wild', 'floor': [880, 1050],
         'relief': 'flat', 'density': 'sparse',
         'purpose': ("Marsh between the lagoon's south shore and the world rim: the Lifeforce Spring on its knoll, "
                     "a wreck at the cliff's edge, pools; night bats near Nightshadow's end."),
         'population': pops('pop:shore_things', 'pop:shore_dead') +
                       [{'id': 'pop:night_bats', 'actor': 'Xeen Night Bat', 'groups': 2, 'placed': True,
                         'hostile': True, 'notes': "Two flocks (8) below Nightshadow's churchyard."}]},
        {'id': 'zone:rim', 'name': 'The world rim', 'kind': 'wild', 'floor': 0, 'empty': True,
         'purpose': "South the land ends in a cliff of about 900; below, the stars (water at 0 stands for them)."},
        {'id': 'water:rim_sea', 'name': 'Below the rim', 'kind': 'water',
         'purpose': "The stars below the world's edge (water at 0, as X2 and X5)."},
        {'id': 'water:pools', 'name': 'Fen and bog pools', 'kind': 'water',
         'purpose': 'Black pools in the fen, the Gloomwood, the Drowned Shore and the Bogwood.'},
        # ---- junctions and edge ends ----
        {'id': 'junction:lagoon_cross', 'name': 'Lagoon Cross', 'kind': 'junction', 'signpost': True,
         'purpose': "East: Rivercity. West: Ebenezer's camp, Newcastle. South: Nightshadow."},
        {'id': 'junction:causeway_fork', 'name': 'Causeway fork', 'kind': 'junction', 'signpost': True,
         'purpose': "North: Burlock (X4). West: Winterkill (X5). South: the Tower of High Magic. East: the camp."},
        {'id': 'junction:fen_fork', 'name': 'Fen fork', 'kind': 'junction', 'signpost': True,
         'purpose': "The tomb path south over the plank bridge; the fen road west."},
        {'id': 'junction:tomb_fork', 'name': 'Tomb fork', 'kind': 'junction', 'signpost': True,
         'purpose': "The tomb door; the path east along the shore to the spring and Nightshadow."},
        {'id': 'edge:east_end', 'name': 'East edge', 'kind': 'road', 'part_of': 'zone:east_meadow',
         'purpose': 'Where the lagoon road leaves for X2.'},
        {'id': 'edge:west_end', 'name': 'West edge', 'kind': 'road', 'part_of': 'zone:black_fen',
         'purpose': 'Where the fen road leaves for X5.'},
        {'id': 'edge:north_end', 'name': 'North edge', 'kind': 'road', 'part_of': 'zone:north_vale',
         'purpose': 'Where the north road leaves for X4.'},
    ]
    links = [
        {'id': 'link:east_road', 'from': 'edge:east_end', 'to': 'junction:lagoon_cross', 'kind': 'road',
         'purpose': 'travel: X2 to the lagoon'},
        {'id': 'link:camp_road', 'from': 'junction:lagoon_cross', 'to': 'junction:causeway_fork', 'kind': 'road',
         'notes': "past Ebenezer's camp and the foot of the rise"},
        {'id': 'link:north_road', 'from': 'junction:causeway_fork', 'to': 'edge:north_end', 'kind': 'road',
         'purpose': 'travel: X4', 'rise': 340},
        {'id': 'link:west_road', 'from': 'junction:causeway_fork', 'to': 'edge:west_end', 'kind': 'road',
         'purpose': 'travel: X5', 'notes': 'by Fen fork'},
        {'id': 'link:nightshadow_road', 'from': 'junction:lagoon_cross', 'to': 'zone:nightshadow_square',
         'kind': 'road'},
        {'id': 'link:south_street', 'from': 'zone:nightshadow_square', 'to': 'zone:churchyard', 'kind': 'path'},
        {'id': 'link:quay_lane', 'from': 'zone:nightshadow_square', 'to': 'poi:mirabeth', 'kind': 'path',
         'notes': "to the quay and the black-rock spit with Mirabeth's rock"},
        {'id': 'link:newcastle_stair', 'from': 'town:ebenezer_camp', 'to': 'town:newcastle', 'kind': 'stairs',
         'rise': 680},
        {'id': 'link:causeway', 'from': 'junction:causeway_fork', 'to': 'zone:tower_islet', 'kind': 'path',
         'crosses': ['water:lagoon'], 'features': ['a low stone causeway, two cells wide, 900 high']},
        {'id': 'link:tomb_path', 'from': 'junction:fen_fork', 'to': 'junction:tomb_fork', 'kind': 'path',
         'crosses': ['water:river'], 'features': ['a plank bridge over the Lagoon Water at (37, 63.5)']},
        {'id': 'link:tomb_lane', 'from': 'junction:tomb_fork', 'to': 'zone:tomb', 'kind': 'path'},
        {'id': 'link:gloom_path', 'from': 'junction:tomb_fork', 'to': 'poi:lifeforce_spring', 'kind': 'path',
         'notes': 'through the dead woods past the sunken graves'},
        {'id': 'link:shore_path', 'from': 'zone:churchyard', 'to': 'poi:lifeforce_spring', 'kind': 'path',
         'notes': "closes the south loop: camp, Nightshadow, the shore, the tomb, the fen, the causeway"},
    ]
    entrances = [
        {'id': 'entrance:east_road', 'space': 'edge:east_end', 'kind': 'both', 'neighbour': 'edge:east',
         'facing': 'w', 'how': "The lagoon road over X2's hill gap; the camp and the ruin ahead, the lagoon beyond."},
        {'id': 'entrance:west_road', 'space': 'zone:west_landing', 'kind': 'both', 'neighbour': 'edge:west',
         'facing': 'e', 'how': "The fen road on the Lagoon Water's north bank."},
        {'id': 'entrance:north_road', 'space': 'edge:north_end', 'kind': 'both', 'neighbour': 'edge:north',
         'facing': 's', 'how': 'The north road down the vale; the lagoon and the Tower ahead.'},
        {'id': 'entrance:nightshadow_square', 'space': 'zone:nightshadow_square', 'kind': 'arrival',
         'how': "Town Portal and the mirror (house 4110, opens with q-c7.done; A4's arrival nightshadow_square)."},
        {'id': 'entrance:newcastle_gate', 'space': 'town:newcastle', 'kind': 'arrival',
         'how': "The mirror at the gate (house 4121, opens with m11.keep; A4's arrival newcastle_gate)."},
        {'id': 'entrance:camp_fire', 'space': 'town:ebenezer_camp', 'kind': 'arrival',
         'how': "Where a defeated party wakes, by the camp shrine's fire."},
        {'id': 'entrance:x8_landing', 'space': 'zone:reedbeds', 'kind': 'arrival', 'neighbour': 'fall:x8',
         'how': "A fall from the High Magic Clouds lands here, in the reeds by the causeway head."},
        {'id': 'entrance:xd13_keep', 'space': 'town:newcastle', 'kind': 'both', 'neighbour': 'door:xd13',
         'facing': 's', 'how': "A stair down into the ruin's foundation (stage 0); the keep's door from stage 2."},
        {'id': 'entrance:xd11_tower', 'space': 'zone:tower_islet', 'kind': 'both', 'neighbour': 'door:xd11',
         'facing': 'n', 'condition': {'item': 'enchanted_key'},
         'how': "The tower door at the causeway's end: 'The tower door has no lock you can see, only a faint "
                "shimmer where a key would go.' (m13.tower_door)"},
        {'id': 'entrance:xd08_tomb', 'space': 'zone:tomb', 'kind': 'both', 'neighbour': 'door:xd08', 'facing': 'n',
         'condition': {'item': 'stone_of_terrors'},
         'how': "'The tomb door is sealed. A hollow in it is shaped for a stone.' (m10.tomb_door)"},
        {'id': 'entrance:xd24_crypt', 'space': 'zone:nightshadow_square', 'kind': 'both', 'neighbour': 'door:xd24',
         'facing': 'n', 'condition': {'qbit': 'nightshadow_dials_set'},
         'how': ("Count Draco's coffin on the square (hook q-c7.coffin): at night with the dials set the lid slides "
                 "aside on a stair down. Else: 'The lid refuses to budge. A symbol etched on the surface of the lid "
                 "flashes pale blue whenever you try to move it.'")},
    ]
    goals = [
        {'id': 'goal:deed', 'space': 'town:ebenezer_camp', 'kind': 'use',
         'what': "Buy the deed to Newcastle from Ebenezer for 12,000 gold (M8; hook m8.site).", 'story': 'M8'},
        {'id': 'goal:walls', 'space': 'town:newcastle', 'kind': 'set',
         'what': "Newcastle's walls appear (M9, m9.walls; hook m9.walls).", 'story': 'M9'},
        {'id': 'goal:tomb', 'space': 'zone:tomb', 'kind': 'use',
         'what': "Open the Tomb of a Thousand Terrors with the Stone (M10; hook m10.tomb_door).", 'story': 'M10'},
        {'id': 'goal:keep', 'space': 'town:newcastle', 'kind': 'set',
         'what': "Newcastle's keep appears (M11, m11.keep; hook m11.keep).", 'story': 'M11'},
        {'id': 'goal:tower', 'space': 'zone:tower_islet', 'kind': 'use',
         'what': "Open the Tower of High Magic with the Enchanted Key (M13; hook m13.tower_door).", 'story': 'M13'},
        {'id': 'goal:count', 'space': 'zone:nightshadow_square', 'kind': 'set',
         'what': "Set the three sundials to nine, slay Count Draco at night: Nightshadow liberated (Q-C7).",
         'story': 'Q-C7'},
        {'id': 'goal:mirabeth', 'space': 'water:lagoon', 'kind': 'reach',
         'what': "Bring Mirabeth the Elixir of Restoration (Q-C12; hook q-c12.lagoon_rock).", 'story': 'Q-C12'},
    ]
    pois = [
        {'id': 'poi:obelisk', 'space': 'zone:north_vale', 'kind': 'obelisk', 'rule': 'native:obelisk',
         'behaviour': "One of Cloudside's obelisks: a word of the world's riddle.",
         'notes': "On a knoll east of the north road, the lagoon and the Tower in view."},
        {'id': 'poi:marsh_well', 'space': 'zone:reedbeds', 'kind': 'well',
         'behaviour': "The Marsh Well: +Fire, Air, Water and Earth resistance, temporary (the sheet's well of "
                      "temporary resistance; A2 sets the amount).",
         'uses': {'times': 1, 'per': 'character', 'reset': 'daily'}},
        {'id': 'poi:lifeforce_spring', 'space': 'zone:drowned_shore', 'kind': 'fountain',
         'behaviour': "The Lifeforce Spring, which names the lagoon: +2 Endurance, permanent, once (the map's "
                      "permanent device).", 'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:food_trees', 'spaces': ['zone:black_fen', 'zone:reedbeds'], 'kind': 'device', 'count': 2,
         'behaviour': "Swamp food trees (the sheet's): a basket of marsh fruit, food +2, once a day.",
         'uses': {'times': 1, 'per': 'party', 'reset': 'daily'}},
        {'id': 'poi:mirabeth', 'space': 'water:lagoon', 'kind': 'npc',
         'behaviour': "Mirabeth the Mermaid (4202) on her rock at the end of a black-rock spit (Q-C12 giver; hook "
                      "q-c12.lagoon_rock): gone once she has the elixir (q-c12.done).",
         'condition': {'not': {'qbit': 'mirabeth_gone'}}},
        {'id': 'poi:sundials', 'space': 'zone:nightshadow_square', 'kind': 'set_piece', 'count': 3,
         'behaviour': "Three sundials on the dial walk; each click turns one an hour on (its own map variable).",
         'notes': ("dials_set rule: the map sets q-c7.dials_set (112142) while all three read 9 and clears it when "
                   "one is turned off 9. Plinths: sundial 1 hook q-c7.clue_stitch ('A stitch in time.'), sundial 2 "
                   "hook q-c7.clue_cat ('Lives of a cat.'), sundial 3 bare.")},
        {'id': 'poi:count_sign', 'space': 'zone:nightshadow_square', 'kind': 'sign',
         'behaviour': "A sign (a message): 'The Count wakes at nine and sleeps at nine.'",
         'notes': "hook q-c7.sign_nine, at the dial walk's entrance"},
        {'id': 'poi:rhyme_board', 'space': 'zone:nightshadow_square', 'kind': 'sign',
         'behaviour': "The signboard by the coffin: 'If the dials are properly set, the count will definitely be "
                      "upset. Open his coffin and bid him farewell; only then can you use the magic of the well.'",
         'notes': "hook q-c7.rhyme; reading it sets q-c7.started (once)"},
        {'id': 'poi:draco_coffin', 'space': 'zone:nightshadow_square', 'kind': 'set_piece',
         'behaviour': "Count Draco's coffin on a plinth: XD-24's entrance (see entrance:xd24_crypt). The plinth's "
                      "sign: 'Only at night can you put up a fight.'",
         'notes': "hooks q-c7.coffin (sets q-c7.coffin_opened) and q-c7.sign_night"},
        {'id': 'poi:town_well', 'space': 'zone:nightshadow_square', 'kind': 'well',
         'behaviour': "Nightshadow's well: its magic works only once the Count is gone (A2 sets the effect).",
         'condition': {'qbit': 'nightshadow_liberated'},
         'notes': "hook q-c7.well (reads q-c7.done)"},
        {'id': 'poi:nightshadow_mirror', 'space': 'zone:nightshadow_square', 'kind': 'mirror',
         'behaviour': "The Mirror of Nightshadow (4110): 'The mirror shows the square, but not you.' until "
                      "q-c7.done (qbit 119005)."},
        {'id': 'poi:newcastle_mirror', 'space': 'town:newcastle', 'kind': 'mirror',
         'behaviour': "The Mirror of Newcastle (4121): an empty frame in the rubble until m11.keep (qbit 119006)."},
        {'id': 'poi:ebenezer_fire', 'space': 'town:ebenezer_camp', 'kind': 'camp',
         'behaviour': "Ebenezer's camp fire between the tent and the shrine: carts, timber, Brother Tobit outside "
                      "by day (hook m8.site: rubble, the tent, the workers)."},
        {'id': 'poi:work_yard', 'space': 'zone:newcastle_rise', 'kind': 'chest',
         'behaviour': "Emerson's work yard on the rise's west shoulder, where the old walls are cut up for new "
                      "stone: block stacks, a crane, barrels and crates in pairs and a mason's chest against the "
                      "shed wall (the workers' wages)."},
        {'id': 'poi:ranger_camp', 'space': 'zone:bogwood', 'kind': 'camp',
         'behaviour': "The evil rangers' camp on a dry knoll: burn it (XP, A3 rescales the source's 10,000)."},
        {'id': 'poi:ranger_chest', 'space': 'zone:bogwood', 'kind': 'chest',
         'behaviour': "The rangers' strongbox behind their tents: what they took off travellers on the X5 road."},
        {'id': 'poi:sunken_punt', 'space': 'zone:reedbeds', 'kind': 'chest',
         'behaviour': "A smuggler's punt sunk in the reeds, its locked box above water (a chest)."},
        {'id': 'poi:tax_coffer', 'space': 'zone:reedbeds', 'kind': 'chest',
         'behaviour': "A tax coffer that slid off Ebenezer's cart into the shallows by an old jetty (a chest)."},
        {'id': 'poi:eel_fisher', 'space': 'zone:west_landing', 'kind': 'chest',
         'behaviour': "The eel-fisher's hut on stilts, a dead fire, his savings under the floor (a chest)."},
        {'id': 'poi:pilgrim_pack', 'space': 'zone:gloomwood', 'kind': 'chest',
         'behaviour': "A drowned pilgrim's pack on the Gloomwood pool's bank (a chest), the dead walking near."},
        {'id': 'poi:wreck', 'space': 'zone:drowned_shore', 'kind': 'chest',
         'behaviour': "A boat wrecked on the shore above the rim cliff, its sea chest in the bilge."},
        {'id': 'poi:crow_watchtower', 'space': 'zone:crow_hills', 'kind': 'chest',
         'behaviour': "A fallen watchtower on the Crow Hills: a chest in the rubble, the whole lagoon in view."},
        {'id': 'poi:sexton_shed', 'space': 'zone:churchyard', 'kind': 'chest',
         'behaviour': "The sexton's shed: Ostrick's tools and grave goods (a chest; locked until q-c7.done)."},
        {'id': 'poi:garlic_shrine', 'space': 'zone:reedbeds', 'kind': 'shrine',
         'behaviour': "A wayside shrine on the Nightshadow road hung with garlic and charms: cures Disease, once a "
                      "day; a carved warning: 'Be indoors by nine.'", 'uses': {'times': 1, 'per': 'party', 'reset': 'daily'}},
        {'id': 'poi:sunken_graves', 'space': 'zone:gloomwood', 'kind': 'ruin',
         'behaviour': "Sunken graves and a leaning stone: 'Here lie the ones the Count let go.'"},
        {'id': 'poi:signposts', 'spaces': ['junction:lagoon_cross', 'junction:causeway_fork', 'junction:fen_fork',
                                           'junction:tomb_fork'], 'kind': 'signpost', 'count': 4,
         'behaviour': 'Signposts at the forks.'},
    ]
    landmarks = [
        {'id': 'landmark:high_magic', 'space': 'zone:tower_islet',
         'what': "The Tower of High Magic: grey rubble under black timber friezes, pale plaster storeys, a "
                 "black-slate roof (towers kit, hwm2 and hwp1), about 2,600 tall on its rock",
         'seen_from': ['zone:east_meadow', 'zone:reedbeds', 'town:nightshadow', 'zone:north_vale', 'zone:black_fen',
                       'zone:drowned_shore']},
        {'id': 'landmark:newcastle', 'space': 'town:newcastle',
         'what': "Newcastle's broken walls of weathered castle stone on their rise (later pale royal walls and the keep)",
         'seen_from': ['zone:east_meadow', 'zone:reedbeds', 'water:lagoon']},
        {'id': 'landmark:nightshadow_mist', 'space': 'town:nightshadow',
         'what': "A grey mist bank in the hollow, Nightshadow's roofs and the temple's spire in it",
         'seen_from': ['zone:reedbeds', 'water:lagoon', 'zone:east_meadow']},
        {'id': 'landmark:crow_crown', 'space': 'zone:crow_hills', 'what': "The Crow's Crown, a bare dark peak",
         'seen_from': ['zone:reedbeds', 'zone:north_vale', 'zone:east_meadow']},
        {'id': 'landmark:tomb_mound', 'space': 'zone:tomb', 'what': "The tomb's black-faced mound among dead trees",
         'seen_from': ['zone:black_fen', 'zone:gloomwood']},
    ]
    sightlines = [
        {'id': 'view:arrival', 'from': 'entrance:east_road',
         'to': ['landmark:newcastle', 'landmark:high_magic', 'landmark:nightshadow_mist'],
         'what': "Arrival from X2: the road down to the camp, the ruin on its rise, the Tower across the lagoon."},
        {'id': 'view:signature', 'from': 'junction:causeway_fork',
         'to': ['landmark:high_magic', 'landmark:nightshadow_mist'],
         'what': "The signature view: the causeway to the Tower; Nightshadow in its mist across the water."},
    ]
    set_pieces = [
        {'id': 'set:sundials', 'kind': 'puzzle', 'spaces': ['zone:nightshadow_square'],
         'rule': ("Three sundials, each clicked round the hours (map variables). While all three read 9 the map "
                  "sets q-c7.dials_set (112142) and clears it when one leaves 9; with it set and at night (21-6) "
                  "Draco's coffin opens on the stair to XD-24 (q-c7.coffin)."),
         'states': ['wrong', 'set'], 'gives': {'qbit': 'nightshadow_dials_set'}},
        {'id': 'set:newcastle_stages', 'kind': 'scripted', 'spaces': ['town:newcastle'],
         'rule': "BModel groups by Xeen.stageOf(\"newcastle\"): 0 the ruin; 1 the walls; 2 the keep and the "
                 "mirror; 3 the dungeon dug (QUESTS 4.1).",
         'states': ['ruin', 'walls', 'keep', 'dungeon']},
    ]
    height_bands = [
        {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
        {'id': 'band:water', 'range': [850, 860], 'spaces': ['water:lagoon', 'water:river']},
        {'id': 'band:low', 'range': [880, 1100],
         'spaces': ['zone:black_fen', 'zone:reedbeds', 'zone:drowned_shore', 'town:nightshadow', 'zone:east_meadow',
                    'zone:west_landing']},
        {'id': 'band:mid', 'range': [950, 1900],
         'spaces': ['zone:gloomwood', 'zone:bogwood', 'zone:north_vale', 'town:ebenezer_camp']},
        {'id': 'band:high', 'range': [1020, 2400], 'spaces': ['zone:newcastle_rise', 'town:newcastle'],
         'partly': ['zone:crow_hills', 'zone:east_ridge']},
        {'id': 'band:peaks', 'range': [2000, 3450], 'spaces': ['zone:crow_hills'], 'partly': ['zone:east_ridge'],
         'notes': "The Crow's Crown 3,450; the edges' ridges to 3,400 beyond the playable square."},
    ]
    states = [
        {'id': 'state:nightshadow_cursed', 'condition': {'not': {'qbit': 'nightshadow_liberated'}},
         'locks': ['building:nightshadow_temple', 'building:nightshadow_tavern', 'building:treasure_trove',
                   'building:nightshadow_alchemist', 'building:gnome_home', 'building:nightshadow_houses'],
         'atmosphere': "Mist in the hollow, no townsfolk by day, shutters closed; the Moon Guild open 21-6.",
         'notes': "A4's closed texts on each door (towns/x3.yml)."},
        {'id': 'state:nightshadow_liberated', 'condition': {'qbit': 'nightshadow_liberated'},
         'opens': ['building:nightshadow_temple', 'building:nightshadow_tavern', 'building:treasure_trove',
                   'building:nightshadow_alchemist', 'building:gnome_home', 'building:nightshadow_houses'],
         'effects': ["Townsfolk in the streets, lamps lit, the mirror works (qbit 119005), the Moon Guild keeps "
                     "day hours (4104); the mist thins (open question to the user)."]},
        {'id': 'state:mirabeth_gone', 'condition': {'qbit': 'mirabeth_gone'},
         'effects': ["Mirabeth's actor is gone from her rock (q-c12.lagoon_rock)."]},
    ]
    totals = {
        'hostiles_at_load': figures['hostiles'],
        'encounter_areas': figures['areas'],
        'spawn_markers': figures['markers'],
        'outdoor_chests': figures['chests'],
        'points_of_interest': figures['pois'],
        'dungeon_entrances': 4,
        'kill_xp_per_member_estimate': figures['kill_xp_member'],
    }
    return {
        'format': 0,
        'level': 'L1',
        'pitch': ("The swamp south of Burlock: a still green lagoon in dark marsh woods, a grey tower on a rock in "
                  "it, a ruined castle on a rise, a vampire town that never sees the sun. In the east, where the "
                  "road comes in from Rivercity, Ebenezer the taxman camps at the foot of Newcastle's rise selling "
                  "the ruin; across the water Nightshadow sits in its mist. West the Black Fen drains the lagoon "
                  "to the tundra; south-west the Gloomwood's dead trees hide the Tomb of a Thousand Terrors; "
                  "south the Drowned Shore ends at the world's rim."),
        'purpose': ("Act II's castle map (party 13-16): the Newcastle chain (M8, M9, M11; XD-13), the Tomb (M10, "
                    "XD-08), the Tower of High Magic (M13, XD-11, the way up to X8), Nightshadow's curse (Q-C7, "
                    "XD-24) and Mirabeth (Q-C12). Services from day one at Ebenezer's camp."),
        'mood': ("Damp, green-grey and quiet; low light under a pale overcast, mist on the water at dawn. Frogs, "
                 "reeds in the wind; Nightshadow silent in its fog; the camp's fire and hammering at the ruin."),
        'datum': 'water:rim_sea',
        'spaces': spaces,
        'links': links,
        'entrances': entrances,
        'critical_path': ['edge:east_end', 'town:ebenezer_camp', 'town:newcastle', 'zone:tomb', 'zone:tower_islet'],
        'goals': goals,
        'points_of_interest': pois,
        'landmarks': landmarks,
        'sightlines': sightlines,
        'set_pieces': set_pieces,
        'height_bands': height_bands,
        'states': states,
        'landform': {
            'relief': ("A shallow bowl: the lagoon (860) in the middle, fens and reed shores (880-1,000) round it, "
                       "the Bogwood's broken hills north-west (to 1,900), Newcastle's rise (1,750) and the Crow "
                       "Hills (to 3,450) north-east, the east ridge behind Nightshadow, the rim cliff south."),
            'height_range': [860, 3450],
            'water': ("The lagoon (about 900 cells) with its islet, the Lagoon Water from it to the west edge, "
                      "four pools."),
            'water_share': figures['water_share'],
            'rim': {'notes': ("The world rim along the whole south: a cliff of about 900 down to the stars. North, "
                              "east and west the land runs past the playable square to the map's edge; the roads "
                              "and the river run out to it.")},
        },
        'atmosphere': ("Sky: a pale overcast (A6 picks the preset); music 48. Nightshadow's local mist (always "
                       "overcast) until q-c7.done. Frogs, reeds, distant hammering at Newcastle by day, bats at "
                       "night."),
        'sketch': {'file': 'sketch.yml', 'grid': 512},
        'totals': totals,
        'notes': ("MU-3 for gate G1 (A5, 2026-11-20). Source geography: Clouds C4 and D4 (MM4_CLOUDS_CONTENT 3a); "
                  "positions moved where the design needs (Newcastle and Ebenezer's camp to the east, by the X2 "
                  "road; the Tower into the lagoon as M12's text says). Measured: " + figures['summary']),
    }


def sketch(figures):
    seen = {}

    def pt(p):
        out = {'id': p[0], 'at': p[1]}
        if p[2]:
            out['facing'] = p[2]
        seen[p[0]] = seen.get(p[0], 0) + 1
        note = POINT_NOTES.get((p[0], seen[p[0]]))
        if note:
            out['notes'] = note
        return out

    districts = []
    for space, poly in [('town:nightshadow', TOWN_NIGHTSHADOW), ('town:ebenezer_camp', CAMP)]:
        plots = []
        for b, idx, at, facing, door_to, kit, house in PLOTS[space]:
            plot = {'building': b}
            if idx:
                plot['index'] = idx
            plot.update({'at': at, 'facing': facing})
            if door_to:
                plot['door_to'] = door_to
            plot['kit'] = kit
            plot['notes'] = f'house {house}' + (f': {NS_HOUSE_NAMES[idx - 1]}' if idx else '')
            if b == 'building:ebenezer_tent':
                plot['notes'] += ": a large striped tent at L3 (form none and a tent model), not a house kit"
            plots.append(plot)
        districts.append({'space': space, 'polygon': poly, 'plots': plots,
                          'notes': ('16 doors of A4\'s x3.yml (4103/4104-4109, 4111-4120) and the mirror 4110 in the '
                                    'square; about ' + str(figures['ns_cells']) + ' cells.')
                          if space == 'town:nightshadow' else "Houses 4101 and 4102 (A4's x3.yml)."})
    districts += [
        {'space': 'zone:nightshadow_square', 'polygon': SQUARE},
        {'space': 'zone:churchyard', 'polygon': GRAVEYARD},
        {'space': 'town:newcastle', 'polygon': NEWCASTLE,
         'notes': ("The ruin's footprint, 7 x 6 cells at [78.5, 30.5]: drawn as a structure at L3 (royal_castle "
                   "ruin pieces), stage groups by Xeen.stageOf(\"newcastle\").")},
        {'space': 'zone:tower_islet', 'polygon': ISLET},
        {'space': 'zone:tomb', 'polygon': TOMB_SITE},
        {'space': 'zone:west_landing', 'polygon': [[19, 53], [27, 53], [27, 70], [19, 70]]},
    ]
    for space, poly in ZONES.items():
        districts.append({'space': space, 'polygon': poly})
    band_of = {'zone:black_fen': 'band:low', 'zone:reedbeds': 'band:low', 'zone:drowned_shore': 'band:low',
               'zone:east_meadow': 'band:low', 'zone:gloomwood': 'band:mid', 'zone:bogwood': 'band:mid',
               'zone:north_vale': 'band:mid', 'zone:newcastle_rise': 'band:high', 'zone:crow_hills': 'band:peaks',
               'zone:east_ridge': 'band:high'}
    bands = [{'band': 'band:rim_sea', 'space': 'zone:rim', 'polygon': ZONES['zone:rim']},
             {'band': 'band:water', 'space': 'water:lagoon', 'polygon': LAGOON},
             {'band': 'band:low', 'space': 'town:nightshadow', 'polygon': TOWN_NIGHTSHADOW}]
    bands += [{'band': band, 'space': space, 'polygon': ZONES[space]} for space, band in band_of.items()]
    areas = []
    for pid, slot, count, key, poly, notes in AREAS:
        areas.append({'id': pid, 'count': count, 'slot': slot, 'polygon': poly,
                      'notes': f'{key} {AREA_NAMES[key]}: {notes}'})
    for qid, kind, poly, notes in QUIET:
        areas.append({'id': qid, 'kind': kind, 'polygon': poly, 'notes': notes})
    actors = [{'monster': m, 'at': at, 'count': c, 'spread': s, 'group': g, 'hostile': True, 'notes': n}
              for m, at, c, s, g, n in ACTORS]
    actors.append({'monster': 'Peasant', 'at': [84.6, 81], 'npc': 4202, 'group': 4, 'hostile': False,
                   'notes': "Mirabeth the Mermaid on her rock (Q-C12); hidden by the map once q-c12.done."})
    return {
        'format': 0,
        'grid': 512,
        'map_cells': 128,
        'notes': ("X3 Lifeforce Lagoon, MU-3 to-scale plan (lane A5, 2026-11-20), for gate G1: composition, scale "
                  "and density only. Cells [x, y], x east, y south. Heights are map units above the stars below "
                  "the rim (0): the lagoon at 860, the fens 900-1,000, Nightshadow 1,000, Ebenezer's camp 1,020, "
                  "Newcastle's rise 1,750, the Crow's Crown 3,450. Edges: X2 east at y 40 (road), X5 west at y 59 "
                  "(road) and 62 (river), X4 north at x 50 (road). Written by output/studio_cal/x3/tools/gen_l1.py; "
                  "the later L3 adds plots' detail, ground, scatter and structures to this file."),
        'frame': {
            'playable': [19, 19, 90, 90],
            'edges': [
                {'side': 'east', 'span': [36, 46], 'neighbour': 'edge:east',
                 'notes': "The lagoon road runs out to x 127 at y 40, X2's west road (its line [31.5, 40] to [0, 40])."},
                {'side': 'west', 'span': [50, 68], 'neighbour': 'edge:west',
                 'notes': "The fen road (y 59) and the Lagoon Water (y 62) run out to x 0, on into X5's east pocket."},
                {'side': 'north', 'span': [42, 58], 'neighbour': 'edge:north',
                 'notes': "The north road runs out to y 0 at x 50 (X4)."},
            ],
            'rim': [
                {'side': 'south', 'form': 'level', 'height': 0, 'meet': 1,
                 'notes': "The world rim: the land ends in a cliff at y 104; below it, water at 0 stands for the stars."},
                {'side': 'north', 'span': [0, 42], 'form': 'ridge', 'height': [1800, 2600], 'floor': 1500, 'crest': 10,
                 'roughness': 100, 'notes': "The Bogwood's hills go on toward the savannah."},
                {'side': 'north', 'span': [42, 58], 'form': 'level', 'height': 1300, 'meet': 6,
                 'notes': "The north road's vale, open to the edge."},
                {'side': 'north', 'span': [58, 128], 'form': 'ridge', 'height': [2200, 3400], 'floor': 1700,
                 'crest': 10, 'roughness': 100, 'notes': "The Crow Hills' backs."},
                {'side': 'east', 'span': [0, 36], 'form': 'ridge', 'height': [2200, 3200], 'floor': 1500,
                 'crest': 10, 'roughness': 100, 'notes': "Meets X2's west ridge (2,200-3,200, y 0-36)."},
                {'side': 'east', 'span': [36, 46], 'form': 'level', 'height': 1024, 'meet': 6,
                 'notes': "X2's west road gap at 1,024."},
                {'side': 'east', 'span': [46, 94], 'form': 'ridge', 'height': [1700, 2700], 'floor': 1100,
                 'crest': 10, 'roughness': 100, 'notes': "Meets X2's west ridge (1,700-2,700, y 46-94)."},
                {'side': 'east', 'span': [94, 104], 'form': 'level', 'height': 1100, 'meet': 6,
                 'notes': "As X2: the ridge ends before the rim."},
                {'side': 'west', 'span': [0, 50], 'form': 'ridge', 'height': [1800, 2600], 'floor': 1400,
                 'crest': 10, 'roughness': 100, 'notes': "Meets X5's Ogre Hills (1,800-2,600, y 0-50)."},
                {'side': 'west', 'span': [50, 104], 'form': 'level', 'height': 900, 'meet': 6,
                 'notes': "The fen and the river at X5's level (900)."},
            ],
            'edge': {'height': 1600, 'east': 1024, 'west': 900, 'south': 0},
        },
        'heights': {
            'bands': bands,
            'points': [dict({'at': at, 'h': h}, **({'notes': n} if n else {})) for at, h, n in HPOINTS],
            'cliffs': [{'line': line, 'drop': drop, 'down': down, 'notes': n} for line, drop, down, n in CLIFFS],
            'ridges': [{'line': line, 'height': h, 'width': w, 'slope': s, 'notes': n} for line, h, w, s, n in RIDGES],
        },
        'water': {
            'bodies': [
                {'id': 'water:lagoon', 'kind': 'lake', 'level': 860, 'polygon': LAGOON,
                 'notes': ("The Lifeforce Lagoon; the causeway (x 63-65) and the Tower's islet are left out of the "
                           "polygon, and so is Mirabeth's spit off the east shore.")},
                {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': RIM_SEA,
                 'notes': 'Below the rim: stands for the stars.'},
            ] + [{'id': 'water:pools', 'index': i + 1, 'kind': 'pond', 'level': lvl, 'polygon': poly, 'notes': n}
                 for i, (pid, (poly, lvl, n)) in enumerate(PONDS.items())],
            'rivers': [{'id': 'water:river', 'line': RIVER, 'width_cells': 2.5, 'level': 850,
                        'notes': "The Lagoon Water: the lagoon's outflow to the west edge at y 62, X5's river."}],
        },
        'roads': [dict({'link': link, 'line': line, 'width': width}, **({'surface': s} if s else {}))
                  for link, line, width, s in ROADS],
        'districts': districts,
        'points': [pt(p) for p in POINTS],
        'areas': areas,
        'views': [{'id': v['id'], 'at': v['at'], 'height': v['height'], 'look': v['look'], 'purpose': v['purpose']}
                  for v in VIEWS],
        'actors': actors,
    }


def write(name, data):
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=118, default_flow_style=None)
    (OUT / name).write_text(text)


def main():
    import x3lib
    OUT.mkdir(parents=True, exist_ok=True)
    figures = x3lib.figures_for_brief()
    write('project.yml', project())
    write('plan.yml', plan(figures))
    write('sketch.yml', sketch(figures))
    print('written', OUT, figures['summary'])


if __name__ == '__main__':
    main()
