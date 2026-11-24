#!/usr/bin/env python3
"""X2 Rivercity and Lake Darzog: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml) and the
L1, L2 and L3 briefs beside it (each a whole project folder: L1 the plan, L2 the specification, L3 with the sketch).

The design is devdocs/xeen/MAPS.md "X2 Rivercity and Lake Darzog", WORLD_DESIGN.md 3-5, QUESTS.md (M5-M13, Q-C2,
Q-C3, Q-C12, Q-C13, Q-C17-Q-C19, Q-C23) and devdocs/xeen/ACT2_BUILD.md. Every number is a design value (no original
exists); measured ranges come from devdocs/map_studio/TOWN_FEEL.md and OUTDOOR_REBUILD_PROCEDURE.md. The project files
are this script's output: edit here and run ../v.sh, never the files.
Coordinates: terrain cells [x, y], x east, y south from the north-west corner; X = (x - 64) * 512, Y = (64 - y) * 512.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import math
import os
import random
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml
import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kit as K

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/x2'

# ---------------------------------------------------------------------------------------------------------------
# The Xeen world (A5, 2026-11-20): one switch, as X1's. IN_WORLD = True: `world: xeen`, A2's rows and items, A4's
# houses (devdocs/xeen/lanes/A4.md "House ids for the map lanes"), A3's hooks (XeenQuests.hook); False rebuilds the
# MM7 stand-in of 2026-11-16.
IN_WORLD = True
# The west and north edges (A5, fourth session): True once X3 / X4 are installed in assets_dev/worlds/xeen/maps; each
# then leads there for real (the neighbour's east / south start) and its closing sign goes. X4's south edge is split
# (D-11.6): east of its x 64 it leads here, so X2's north edge arrives at X4's south start, the X2 road.
X3_LIVE = True
X4_LIVE = True
for _live, _stem in ((X3_LIVE, 'xeen_x3.odm'), (X4_LIVE, 'xeen_x4.odm')):
    assert not _live or os.path.exists(os.path.join('assets_dev/worlds/xeen/maps', _stem)), _stem + ' not installed'
XEEN_SOURCE = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/worlds/xeen/source')
HOOKS = {}
for _f in sorted(os.listdir(os.path.join(XEEN_SOURCE, 'quests'))) + ['../npcs/x2.yml']:
    _q = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'quests', _f)))
    for _k, _v in (_q.get('hooks') or {}).items():
        if _v.get('map') == 'X2':
            HOOKS['%s.%s' % (os.path.basename(_f)[:-4], _k)] = _v
# A4's house per door: the stand-in's MM7 row -> the Xeen house and its name
HOUSE_XEEN = {
    10: (4051, 'Rivercity Smithing'), 49: (4052, 'Rivercity Armoury'), 86: (4053, "Witch's Cauldron"),
    118: (4054, 'The Bubbling Flask'), 287: (4055, 'The Bank'), 241: (4056, "Bull's Tavern"),
    1572: (4057, "Street Fightin'"), 312: (4058, 'Pray N Pay'), 165: (4059, 'Guild of Body'),
    159: (4060, 'Guild of Mind'), 153: (4061, 'Guild of Spirit'), 462: (4062, 'Royal Steeds of Rivercity'),
    486: (4063, "Captain Nystor's Dock"), 910: (4065, 'Barlow House'), 911: (4066, 'Kettle Residence'),
    912: (4067, 'Rook House'), 913: (4068, 'Sallow Residence'), 914: (4069, 'School of Navigation'),
    915: (4070, 'Tanner Residence'), 920: (4071, 'Lantern Residence'), 924: (4072, "Captain Yang's House"),
    916: (4073, 'Ferris House'), 917: (4074, 'Quill Residence'), 919: (4075, 'Mudd House'),
    922: (4076, 'Ostler Residence'), 921: (4077, 'Gaff House'), 943: (4078, 'Tackle House'),
    945: (4079, "Arnold's Gym"), 923: (4080, 'Martial Training'), 929: (4081, "Lindon's Temps"),
    926: (4082, 'Crane Residence'), 927: (4083, 'Wharf House'), 928: (4084, 'Ladle Residence'),
    936: (4085, 'Scull Residence'), 939: (4086, 'Ferry House'), 940: (4087, 'Hawser Residence'),
    941: (4088, 'Brine House'), 931: (4089, 'Bargeman House'), 932: (4090, 'Vatawna the Guildmaster'),
    933: (4091, 'Mind Guild Steward'), 937: (4092, 'Spirit Guild Steward'), 942: (4093, 'Reed Residence'),
    944: (4094, 'Spratt Residence')}
HOUSE_MIRROR, HOUSE_BAROK, HOUSE_MEDIN, HOUSE_TITO = 4064, 4095, 4096, 4097
LIGONO_GROUP = 55
# NPCs without a house that the map places (A4): Danulf at his ring, Ligono on the cliff top at the rim
NPC_ACTORS = [(4154, '371', (56.8, 82.6)), (4155, '270', (27.0, 102.0))]   # 371 MM7's Peasant Human2 MaleB
XD06_EXIT = [(62.0, 98.0), (62.0, 98.84)]   # D-88: XD-06's named arrival and its own MoveToMap (-1024, -17840)
# A2's rows: slot names (map_stats) and placed rows. Sprites 10/14/18 (Medusa Sprite, Killer Sprite, Sprite Queen),
# rangers 8/12/18 (Evil Archer, Evil Ranger, Elite Ranger), ogres 18/22/30 (Ogre, Ogre Brute, Ogre Chief; the slot at
# Dif 0, Ogres only, and the lair's leader a Brute: kill XP, tools/xeen/balance.py); the lake's
# three water dragons (60, Q-C13's trap) the Cloudside dragons' first tier.
XEEN_SLOT = {'sprites': 'Xeen Sprite', 'rangers': 'Xeen Ranger', 'ogres': 'Xeen Ogre'}
XEEN_ROW = {'202': 11130, '203': 11131, '594': 11061, '593': 11061, '98': 11531, '97': 11530, '192': 11640,
            'ogre_wanderer': 11060}
XEEN_ITEMS = {'skeleton_key': 12100, 'baroks_pendant': 12152}

def W_(m):
    """A placed monster's row in the world (the stand-in's MM7 number before)."""
    return str(XEEN_ROW[m]) if IN_WORLD else m

def hook(name):
    """A3's hook `name` (a quest file's hook on X2): its call (the texts are A3's)."""
    assert name in HOOKS, name
    return [{'lua': 'XeenQuests.hook("%s")' % name}]

OUT = os.path.join(BRIEFS, 'L4')
STEM = 'xeen_x2'

def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))

def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def bump(x, y, cx, cy, r, h):
    d = math.hypot(x - cx, y - cy)
    return h * (1 - smooth(d / r)) if d < r else 0.0

def dist_to_line(px, py, line):
    best = 1e9
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        best = min(best, K.seg_dist((px, py), (ax, ay), (bx, by)))
    return best

def poly_dist(p, poly):
    return min(K.seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))

# ---------------------------------------------------------------------------------------------------------------
# Land and water
# ---------------------------------------------------------------------------------------------------------------
PLATEAU = 1024     # the farmland, the woods' floor and Rivercity's two terraces
BANK = 640         # the quays and the river banks
RIVER = 576        # the Great River and Lake Darzog
ISLE_H = 768       # the island
X9_FALL = [34, 58]   # X9's fall landing (D-50 change 4, kept by D-54): (-15360, 3072, 768) facing east
# D-54: the three lake dragons' homes and leash radii (north-west lobe, west channel, south lobe); leash circles 6,587 /
# 6,656 / 6,307 from X9_FALL and 6,147 / 5,985 / 5,997 from Darzog's door (-16031, 3014)
LAKE_DRAGONS = [((23, 48), 1024), ((19.5, 58), 768), ((28, 71), 1024)]
RIM_Y = 104        # the world rim: the land ends in a cliff along y 104, the stars (water at 0) below
# 2026-11-16 (the compact town): the river narrows between Rivercity's quays to the water nodes y 51-55 (49-55 before)
# so that the two halves stand 8 cells apart instead of 11; 4 wide from the lake's outlet and east of the dock.
RIVER_W = [[44, 52], [49, 52], [53, 53]]                       # from the lake's outlet to the town, 4 wide
RIVER_TOWN = [[53, 53], [82, 53]]                              # between the quays: water nodes 51-55
RIVER_E = [[82, 53], [88, 52], [90, 52]]                       # east of the dock, 4 wide
RIVER_MID = [[90, 52], [100, 51]]                              # narrowing east
RIVER_EAST = [[100, 51], [128, 51]]                            # to X1, where it is Pitchfork Creek (3 wide, y 51)
NORTH_RIVER = [[30, 0], [30, 10], [28, 18], [27, 24], [28, 30], [31, 35], [34, 40], [35, 45]]   # from X4, the ogres'
ISLAND = [[31, 52], [35, 53], [37, 56], [37, 60], [35, 63], [31, 64], [27, 63], [25, 60], [25, 56], [27, 53]]
# Lake Darzog in two bodies that overlap round the island (a body's outline may not cross or touch itself)
LAKE_N = [[18, 53], [21, 46], [29, 43], [37, 43], [43, 46], [47, 50], [47, 55], [46, 59], [38, 59], [37, 57],
          [37, 56], [35, 53], [31, 52], [27, 53], [25, 56], [24, 59], [18, 59]]
LAKE_S = [[18, 57], [24, 57], [25, 60], [27, 63], [31, 64], [35, 63], [37, 60], [38, 57], [46, 57], [45, 62],
          [42, 69], [35, 73], [27, 73], [21, 69], [18, 62]]
LAKE_OUT = [[18, 53], [21, 46], [29, 43], [37, 43], [43, 46], [47, 50], [47, 55], [46, 58], [45, 62], [42, 69],
            [35, 73], [27, 73], [21, 69], [18, 62]]

def in_lake(p):
    return K.inside(p, LAKE_OUT) and not K.inside(p, ISLAND)

# calm places: no rolling ground (the town, the doors, the places)
CALM_BOXES = [(47, 32, 85, 69)]
CALM = [(23, 29, 4), (62, 99, 4), (31, 58, 5), (46, 60, 3), (80, 76, 3), (56, 82, 4), (70, 86, 3), (96, 33, 3),
        (44, 36.5, 3), (100, 36, 3), (24, 100, 3), (88, 24, 4), (46, 22, 4), (33, 39, 3), (66, 26, 3)]

def roll(x, y):
    w = 1.0
    for (x0, y0, x1, y1) in CALM_BOXES:
        dx = max(x0 - x, 0, x - x1)
        dy = max(y0 - y, 0, y - y1)
        w = min(w, smooth(math.hypot(dx, dy) / 5.0))
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 4.0))
    w = min(w, smooth((RIM_Y - 2 - y) / 5.0))
    v = (560 * math.sin(x / 3.3 + 0.4) * math.sin(y / 3.9 + 1.3) + 380 * math.sin((x + 1.3 * y) / 5.1 + 0.9)
         + 170 * math.sin((x - 1.6 * y) / 2.7))
    return w * max(v, -380.0)

def height(x, y):
    h = PLATEAU
    # The north-west hills the north river cuts through (the ogres' country): to about 2,000.
    h += bump(x, y, 24, 22, 14, 1900) + bump(x, y, 38, 20, 8, 600) + bump(x, y, 19, 36, 7, 650)
    # The farmland rises gently north; a low hill in the north-east by the rangers' camp and the shrine.
    if x > 40:
        h += 140 * smooth((38 - y) / 18.0)
    h += bump(x, y, 96, 30, 8, 420) + bump(x, y, 102, 22, 9, 700) + bump(x, y, 90, 93, 8, 450) + bump(x, y, 42, 92, 7, 380)
    # The fairy woods roll; their dark south end lies in a hollow before the rim.
    h -= bump(x, y, 62, 94, 10, 200)
    # 2026-11-16 (the lead, after the land-to-the-edge pass: "the south is still bare"): a coastal rise of heath knolls
    # along the world rim west and east of the dark end (the rolling ground is held flat within 7 cells of the rim),
    # clear of Ligono's rock, his skull, the temple and the cairn.
    h += (bump(x, y, 34, 98, 6, 380) + bump(x, y, 43, 101, 4, 260) + bump(x, y, 21, 94, 5, 300)
          + bump(x, y, 86, 99, 6, 420) + bump(x, y, 93, 95, 5, 300) + bump(x, y, 104, 99, 5, 380))
    # The east: the river valley opens toward Vertigo.
    if 38 < y < 64:
        h -= 260 * smooth((x - 96) / 24.0)
    h += roll(x, y)
    # The Great River's valley: banks at 640, the valley side back to the land over 3.5 cells.
    d = min(dist_to_line(x, y, RIVER_W) + 0.4, dist_to_line(x, y, RIVER_TOWN) + 1, dist_to_line(x, y, RIVER_E) + 0.4,
            dist_to_line(x, y, RIVER_MID) + 0.4, dist_to_line(x, y, RIVER_EAST) + 1)
    if d < 6:
        h = BANK + (h - BANK) * smooth((d - 2.6) / 3.4)
    # The north river: a gorge through the hills.
    d2 = dist_to_line(x, y, NORTH_RIVER)
    if d2 < 5.5:
        h = BANK + (h - BANK) * smooth((d2 - 1.6) / 3.9)
    # Lake Darzog: shores at 640, the land back over four cells; the island at 768.
    if K.inside((x, y), ISLAND):
        e = poly_dist((x, y), ISLAND)
        return BANK + (ISLE_H - BANK) * smooth(e / 1.5)
    if in_lake((x, y)):
        return RIVER - 64
    dl = poly_dist((x, y), LAKE_OUT)
    if dl < 5:
        h = BANK + (h - BANK) * smooth((dl - 0.8) / 4.2)
    return h

def grid_rows(step=4, unit=32):
    rows = []
    for j in range(128 // step):
        row = []
        for i in range(128 // step):
            x, y = step * i + step / 2, step * j + step / 2
            row.append(int(round(height(x, y) / unit)))
        rows.append(row)
    return rows

# ---------------------------------------------------------------------------------------------------------------
# Rivercity: streets, terraces, quays (cells)
# 2026-11-16, the compact town (the user: "the city way way too much stretched", against Steadwick and Alvar): the
# north half moved 3 cells south over a river narrowed to 3 cells between the quays (the halves 8 cells apart, 11
# before), 24 cells east to west (31 before), houses in rows plot against plot along a main street 1.5 cells between
# house fronts, back to back over half-cell alleys; Bridge Square paved and furnished at the bridge's north head with
# the shops round it. town_feel.py's density figures (2026-11-16) put Steadwick and Alvar beside it. The south bank's
# terrace edge, its quay and the Robbers' Den's door are where they were.
# ---------------------------------------------------------------------------------------------------------------
N_EDGE = 48.5      # the north terrace's edge (its retaining wall, 48-49); the north quay below, y 49-50.5
S_EDGE = 57.5      # the south terrace's edge; the south quay y 55.5-57
BRIDGE_X = 64
MAIN_Y = 43.5      # the north bank's main street
SOUTH_Y = 61.0     # the south bank's street
EAST_ROAD = [[128, 46], [88, 46], [85, 45.5]]
MAIN_E = [[85, 45.5], [78.5, 45.5], [78.5, MAIN_Y - 1], [73, MAIN_Y - 1], [73, MAIN_Y], [64, MAIN_Y]]   # jogs
MAIN_W = [[64, MAIN_Y], [58, MAIN_Y], [58, MAIN_Y - 1], [53, MAIN_Y - 1]]
WEST_ROAD = [[53, MAIN_Y - 1], [49, MAIN_Y - 1], [46, 41], [37, 41], [36, 40], [35.5, 40]]
WEST_ROAD2 = [[31.5, 40], [0, 40]]
NORTH_ST = [[64, MAIN_Y], [64, 36.5], [66, 34.5], [66, 0]]
SOUTH_ST_W = [[54.5, SOUTH_Y], [64, SOUTH_Y]]
SOUTH_ST_E = [[64, SOUTH_Y], [78, SOUTH_Y]]
SOUTH_RD = [[64, SOUTH_Y], [64, 62.5], [63, 63.5], [63, 67.5], [62, 67.5], [62, 72], [63, 73]]
# U-12 rebuild (agent xeen-rimmap-a, 2026-11-23): the lanes end a cell short of the terrace's edge; their last road
# cell lay on the step (48-49) and its grading lifted the quay's nodes under the steps to 960, so the walls beside
# the steps took their tops from 960 (118-176 over the terrace instead of 48)
LANE_W = [[58, MAIN_Y], [58, N_EDGE - 1.0]]           # cross lanes from the main street to the promenade and the quay steps
LANE_E = [[73, MAIN_Y], [73, N_EDGE - 1.0]]
LANE_SE = [[74.5, SOUTH_Y], [74.5, 64.5]]
LANES_C = [LANE_W, LANE_E, LANE_SE]
COBBLE = [EAST_ROAD, MAIN_E, MAIN_W, WEST_ROAD, WEST_ROAD2, NORTH_ST, SOUTH_ST_W, SOUTH_ST_E, SOUTH_RD] + LANES_C
# dirt lanes and paths (ground strips or dirt roads)
PROM_N_W = [[53.5, N_EDGE - 0.5], [62.5, N_EDGE - 0.5]]
PROM_N_E = [[65.5, N_EDGE - 0.5], [77, N_EDGE - 0.5]]
PROM_S_W = [[53.5, 58], [61, 58]]
PROM_S_E = [[67, 58], [78, 58]]
BACK_LANE_S = [[53.5, 64.5], [63.5, 64.5]]
BACK_LANE_SE = [[64.5, 64.5], [74.5, 64.5]]
LANES = [PROM_N_W, PROM_N_E, PROM_S_W, PROM_S_E, BACK_LANE_S, BACK_LANE_SE]
WOODS_PATH = [[63, 73], [61, 77], [58, 80], [58, 86], [61, 90], [62, 95], [62, 97.5]]
LAKE_PATH = [[54.5, SOUTH_Y], [49, SOUTH_Y], [47.5, 61]]
LAIR_PATH = [[31, 40], [28, 37], [25, 34], [23, 31.5]]
FARM_LANE_W = [[66, 30.5], [58, 31], [50, 28], [46, 24]]
FARM_LANE_E = [[66, 29.5], [67, 27], [74, 27], [82, 25], [88, 25]]
SHRINE_PATH = [[88, 46], [93, 40], [96, 34]]
CHAPEL_PATH = [[63, 73], [70, 74], [77.5, 75.5]]
DIRT_PATHS = [WOODS_PATH, LAKE_PATH, LAIR_PATH, FARM_LANE_W, FARM_LANE_E, SHRINE_PATH, CHAPEL_PATH]
BRIDGE_SQ = [[61, 44], [67, 44], [67, 48], [61, 48]]
SOUTH_SQ = [[61, 57], [67, 57], [67, 60], [61, 60]]
TOWN_POLY = [[50, 35], [84, 35], [84, 69], [50, 69]]

# ---------------------------------------------------------------------------------------------------------------
# Houses. (plan id, title, house, at [x, y] (NW corner), facing, [front, depth], kit, shape, turn, extra)
# Services open MM7 house rows of Steadwick (Erathia, MM7's second town, map 64) and Harmondale's guilds under
# Rivercity's names (aaze0030:44-52); residences open Erathia's residence rows 910-945, whose people teach and sell guild
# memberships (Body 932, Mind 933, Spirit 937 by the guild row; Sword 923, Mace 945, Shield 929 on the skill row).
# The rows are written by row() and column(): plots half a cell apart (the walls stand 48 to 64 in from a plot's
# edge: neighbours 352 to 384 apart, Steadwick's median 398), their fronts on one line.
# ---------------------------------------------------------------------------------------------------------------
TH = K.THATCH

def row(facing, front, x0, items):
    """Plots facing north or south with their fronts on y `front`, west to east from x `x0`; ('gap', x) jumps to x."""
    out, x = [], x0
    for it in items:
        if it[0] == 'gap':
            x = it[1]
            continue
        bid, title, house, fp, kit, kind, extra = it
        y = front - fp[1] if facing == 's' else front
        out.append((bid, title, house, x, y, facing, fp, kit, kind, 0, extra))
        x += fp[0]
    return out

def column(facing, front, y0, items):
    """Plots facing east or west with their fronts on x `front`, north to south from y `y0`."""
    out, y = [], y0
    for bid, title, house, fp, kit, kind, extra in items:
        x = front - fp[1] if facing == 'e' else front
        out.append((bid, title, house, x, y, facing, fp, kit, kind, 0, extra))
        y += fp[0]
    return out

NORTH = (
    # B: the shops along the main street (facing south onto it); the bank, the tavern and the magic shop face the square
    # (the main street jogs a cell north at the lanes west and east of the square: the end blocks stand a cell north)
    row('s', MAIN_Y - 2, 53.5, [
        ('building:training', "Street Fightin'", 1572, [2, 2], 'timber', 'barn', {'sign': '7sgtrain'}),
        ('gap', 56),
        ('building:north_houses', None, None, [1.5, 1.5], 'timber', 'gable_porch', {'index': 1}),
    ])
    + row('s', MAIN_Y - 1, 58.5, [
        ('building:magic_shop', "Witch's Cauldron", 86, [2, 2], 'grey', 'tower_house', {'sign': 'sgmagi'}),
        ('gap', 61),
        ('building:bank', 'The Bank', 287, [1.5, 1.5], 'stone', 'cottage', {'sign': '7sgbank', 'big': True}),
        ('gap', 64.5),
        # the tavern faces the square across the main street (TOWN_FEEL 4: on the way in from the bridge and the east)
        ('building:tavern', "Bull's Tavern", 241, [2, 2], 'timber', 'gable_porch', {'sign': '7sgtvrn', 'storeys': 2}),
        ('gap', 67),
        ('building:north_houses', None, None, [1.5, 1.5], 'timber', 'jetty', {'index': 3}),
        ('gap', 69),
        ('building:armour_shop', 'Rivercity Armoury', 49, [1.5, 2], 'timber', 'jetty', {'sign': '7sgarm', 'storeys': 2}),
        ('gap', 71),
        ('building:north_houses', None, None, [1.5, 2], 'grey', 'L', {'index': 4}),
    ])
    + row('s', MAIN_Y - 2, 73.5, [
        ('building:weapon_shop', 'Rivercity Smithing', 10, [2, 2], 'grey', 'forge', {'sign': 'sgweapon'}),
        ('gap', 76),
        ('gap', 76),
        ('building:north_houses', None, None, [1.5, 1.5], 'poor', 'cottage', {'index': 5, 'roof': TH}),
    ])
    # A: the riverfront blocks between the main street and the promenade, back to back over a half-cell alley
    + row('n', MAIN_Y - 0.5, 53.5, [
        ('building:river_houses', None, None, [1.5, 1.5], 'timber', 'jetty', {'index': 1, 'storeys': 2}),
        ('gap', 55.5),
        ('building:river_houses', None, None, [1.5, 1.5], 'grey', 'gable_porch', {'index': 2}),
    ])
    + row('n', MAIN_Y + 0.5, 69.5, [
        ('building:river_houses', None, None, [2, 1.5], 'poor', 'gable_porch', {'index': 7}),
    ])
    + row('n', MAIN_Y - 0.5, 73.5, [
        ('building:river_houses', None, None, [1.5, 1.5], 'grey', 'cottage', {'index': 8}),
        ('gap', 75.5),
        ('building:river_houses', None, None, [1.5, 1.5], 'timber', 'L', {'index': 9}),
    ])
    + row('s', N_EDGE - 1, 53.5, [
        ('building:river_houses', None, None, [1.5, 1.5], 'timber', 'L', {'index': 3}),
        ('gap', 55.5),
        ('building:river_houses', None, None, [1.5, 1.5], 'poor', 'cottage', {'index': 13, 'roof': TH}),
        ('gap', 69.5),
        ('building:river_houses', None, None, [2, 1.5], 'grey', 'cottage', {'index': 12, 'plain': True}),
        ('gap', 73.5),
        ('building:river_houses', None, None, [1.5, 1.5], 'grey', 'jetty', {'index': 10, 'storeys': 2}),
        ('gap', 75.5),
        ('building:river_houses', None, None, [1.5, 1.5], 'timber', 'gable_porch', {'index': 11, 'plain': True}),
    ])
    # Bridge Square's west and east sides: the alchemist and a tall house looking onto the square
    + column('e', 60.5, MAIN_Y + 0.5, [
        ('building:alchemist', 'The Bubbling Flask', 118, [3, 2], 'grey', 'jetty', {'sign': '7sgalch'}),
    ])
    + column('w', 67.5, MAIN_Y + 0.5, [
        ('building:river_houses', None, None, [3, 1.5], 'timber', 'jetty', {'index': 6, 'storeys': 2}),
    ])
)
# the quays: a fisherman's house on the north quay and a ferryman's on the south quay, beside the bridge's ends
QUAY = [
    ('building:quay_houses', None, None, 65.5, 49.0, 's', [2, 1], 'grey', 'cottage', 0, {'index': 1, 'floor': 640}),
    ('building:quay_houses', None, None, 60.5, 55.0, 'n', [1.5, 1], 'timber', 'cottage', 0, {'index': 2, 'floor': 640}),
    # 2026-11-16: warehouses against the south quay's wall (a working river front, not a bare strip), a passage of
    # half a cell before them along the water
    ('building:quay_houses', None, None, 53.5, 56.0, 'n', [2, 1], 'grey', 'barn', 0,
     {'index': 3, 'floor': 640, 'plain': True}),
    ('building:quay_houses', None, None, 56.0, 56.0, 'n', [2, 1], 'timber', 'cottage', 0,
     {'index': 4, 'floor': 640, 'plain': True}),
    ('building:quay_houses', None, None, 69.0, 56.0, 'n', [2, 1], 'poor', 'cottage', 0,
     {'index': 5, 'floor': 640, 'plain': True, 'roof': TH,
      # A5 (2026-11-20, third session): A4's house 4098 (source/towns/x2.yml), Velda and Ysmay, Q-C2
      'xeen_house': (4098, "The Sorceresses' House")}),
    ('building:quay_houses', None, None, 74.0, 56.0, 'n', [2, 1], 'grey', 'barn', 0,
     {'index': 6, 'floor': 640, 'plain': True}),
]
# the stables by the north road, behind the tavern (the way out to the farms and X4)
STABLES = ('building:stables', 'Royal Steeds of Rivercity', 462, 64.5, 37.5, 'w', [2.5, 2], 'timber', 'barn', 0,
           {'sign': '7sgstabl'})
SOUTH = (
    # D: the guild row and the skill row between the south promenade and the south street, their doors on the street,
    # the South Square between them at the bridge's head (2026-11-16: by the river, so that the shops of both banks
    # stand within 9 cells of the bridge)
    row('s', SOUTH_Y - 0.5, 53.5, [
        ('building:guild_body', 'Guild of Body', 165, [2, 2], 'stone', 'tower_house', {'sign': 'sgbody'}),
        ('gap', 56),
        ('building:guild_mind', 'Guild of Mind', 159, [2, 2], 'grey', 'L', {'sign': 'sgmind'}),
        ('gap', 58.5),
        ('building:guild_spirit', 'Guild of Spirit', 153, [2, 2], 'stone', 'gable_porch', {'sign': 'sgspirit'}),
        ('gap', 68),
        ('building:skill_gym', "Arnold's Gym", 945, [2, 1.5], 'timber', 'barn', {}),
        ('gap', 70.5),
        ('building:skill_martial', 'Martial Training', 923, [2, 1.5], 'grey', 'jetty', {}),
        ('gap', 73),
        ('building:skill_temps', "Lindon's Temps", 929, [1.5, 1.5], 'timber', 'gable_porch', {}),
    ])
    # E: homes across the south street, Pray N Pay on the south road
    + row('n', SOUTH_Y + 0.5, 53.5, [
        ('building:south_houses', None, None, [1.5, 2], 'timber', 'jetty', {'index': 1, 'storeys': 2}),
        ('gap', 55.5),
        ('building:south_houses', None, None, [1.5, 2], 'poor', 'gable_porch', {'index': 2}),
        ('gap', 57.5),
        ('building:south_houses', None, None, [1.5, 2], 'grey', 'L', {'index': 3}),
        ('gap', 59.5),
        ('building:south_houses', None, None, [1.5, 2], 'grey', 'cottage', {'index': 11}),
        ('gap', 67.5),
        ('building:south_houses', None, None, [1.5, 2], 'grey', 'jetty', {'index': 5, 'storeys': 2}),
        ('gap', 69.5),
        ('building:south_houses', None, None, [1.5, 2], 'timber', 'gable_porch', {'index': 6}),
        ('gap', 71.5),
        ('building:south_houses', None, None, [1.5, 2], 'timber', 'L', {'index': 8}),
        ('gap', 75),
        ('building:south_houses', None, None, [1.5, 2], 'grey', 'cottage', {'index': 9, 'roof': TH}),
        ('gap', 77),
        ('building:south_houses', None, None, [2, 1.5], 'poor', 'barn', {'index': 7, 'plain': True}),
    ])
    + [('building:temple', 'Pray N Pay', 312, 64.5, SOUTH_Y + 0.5, 'w', [2.5, 2.5], 'stone', 'temple', 0,
        {'sign': 'sgtempl'})]
    # F: the back lane behind them (the guild stewards' houses)
    + row('n', 65, 53.5, [
        ('building:south_houses', None, None, [1.5, 1.5], 'timber', 'cottage', {'index': 12}),
        ('gap', 55.5),
        ('building:south_houses', None, None, [1.5, 1.5], 'poor', 'round_hut', {'index': 13, 'plain': True}),
        ('gap', 57.5),
        ('building:south_houses', None, None, [1.5, 1.5], 'timber', 'gable_porch', {'index': 14}),
        ('gap', 59.5),
        ('building:south_houses', None, None, [1.5, 1.5], 'grey', 'cottage', {'index': 15, 'roof': TH}),
        ('gap', 64.5),
        ('building:south_houses', None, None, [2, 1.5], 'grey', 'L', {'index': 18}),
        ('gap', 67),
        ('building:south_houses', None, None, [1.5, 1.5], 'poor', 'gable_porch', {'index': 19, 'plain': True}),
    ])
)
# residence rows (Erathia's) and Rivercity's names; the guild membership houses by the guild row
RES = [(910, 'Barlow House'), (911, 'Kettle Residence'), (912, 'Rook House'), (913, 'Sallow Residence'),
       (914, 'Weir House'), (915, 'Tanner Residence'), (916, 'Ferris House'), (917, 'Quill Residence'),
       (919, 'Mudd House'), (920, 'Lantern Residence'), (921, 'Gaff House'), (922, 'Ostler Residence'),
       (924, 'Pike House'), (926, 'Crane Residence'), (927, 'Wharf House'), (928, 'Ladle Residence'),
       (931, 'Bargeman House'), (936, 'Scull Residence'), (939, 'Ferry House'), (940, 'Hawser Residence'),
       (941, 'Brine House'), (942, 'Reed Residence'), (943, 'Tackle House'), (944, 'Spratt Residence')]
MEMBERS = {('building:south_houses', 12): (932, "Vatawna the Guildmaster"),
           ('building:south_houses', 14): (933, 'Mind Guild Steward'),
           ('building:south_houses', 15): (937, 'Spirit Guild Steward')}
WILD_HOUSES = [
    ('building:barok_hut', "Barok's Hut", None, 43.5, 36.5, 's', [1.5, 1.5], 'poor', 'round_hut', 6, {'barok': True}),
    ('building:medin_hut', "Medin's Hut", None, 48.5, 63, 'n', [1.5, 1], 'poor', 'cottage', 0, {'medin': True,
                                                                                               'roof': TH}),
    ('building:tito_chapel', "Tito's Chapel", None, 78.5, 74.5, 'w', [2, 2.5], 'stone', 'chapel', 0, {'tito': True}),
    ('building:farmsteads', None, None, 53, 25.5, 's', [2, 1.5], 'timber', 'barn', 0, {'index': 1, 'plain': True}),
    # P2 F27 (town_fit_check houses.buried_door, agent xeen-rimmap-a 2026-11-23): the cottage faced south into the
    # rising fields, the land before its door 88 over the sill; it faces north, downhill toward the barn
    ('building:farmsteads', None, None, 57, 28, 'n', [1.5, 1.5], 'poor', 'cottage', 4, {'index': 2, 'plain': True,
                                                                                         'roof': TH}),
    ('building:farmsteads', None, None, 76, 23.5, 's', [1.5, 1.5], 'timber', 'gable_porch', 0,
     {'index': 3, 'plain': True}),
    ('building:farmsteads', None, None, 79, 23, 's', [2, 1.5], 'poor', 'barn', -5, {'index': 4, 'plain': True}),
    ('building:farmsteads', None, None, 69, 31, 'w', [1.5, 1.5], 'timber', 'cottage', 0, {'index': 5, 'plain': True,
                                                                                         'roof': TH}),
]

BAROK = ('if IsQBitSet(QBit(110204)) then evt.SimpleMessage("Barok the Sorcerer: \\"Thank you for returning my '
         'pendant. The fountain on Bridge Square runs again.\\"") else evt.SimpleMessage("Barok the Sorcerer: \\"The '
         'sorceresses of Rivercity have stolen a magical pendant of mine. I want it back, and I will reward you if '
         'you return it.\\" (The sorceresses are not built yet.)") end')
MEDIN = ('if IsQBitSet(QBit(110201)) then evt.SimpleMessage("Medin the Fisherman: \\"You have slain the monsters of '
         'the lake! My friends, I am always glad to see you. My boat at the jetty will row you to the island.\\"") '
         'else evt.SimpleMessage("Medin the Fisherman: \\"The fish supply is low. I am sure some sort of lake beasts '
         'are eating all the fish. If you kill the beasts, I will be indebted to you.\\" (Three of them circle the '
         'island; do not row out while they live.)") end')
TITO = ('evt.SimpleMessage("Tito the Elf Priest: \\"While travelling through Troll Forest recently, I was ambushed. In '
        'my haste to escape I dropped the Holy Book of Elvenkind. I will reward you well if you can return it to '
        'me.\\"")')

plots_by_space = {}
plan_buildings = {}
footprints = []          # (building id, index, polygon) for the road checks
doors_out = []           # (building id, index, door cell, cell 0.9 out)
res_iter = iter(RES)

def add_plot(space, entry, door_to):
    bid, title, house, x, y, facing, fp, kit, kind, turn, extra = entry
    want = facing
    if kind == 'round_hut':
        facing, turn = 's', (K.TURN_OF[want] + turn) % 360
        if turn > 180:
            turn -= 360
    plot = {'building': bid, 'at': [x, y], 'facing': facing, 'kit': kit}
    if extra.get('floor'):
        plot['floor'] = extra['floor']
    if turn:
        plot['turn'] = turn
    if door_to:
        plot['door_to'] = door_to
    if 'index' in extra:
        plot['index'] = extra['index']
        if (bid, extra['index']) in MEMBERS:
            house, title = MEMBERS[(bid, extra['index'])]
        elif not extra.get('plain'):
            house, title = next(res_iter)
    if IN_WORLD and extra.get('xeen_house'):
        # a house A4 added to a building the stand-in left plain
        plot['house'], plot['title'] = extra['xeen_house']
    elif IN_WORLD and (extra.get('barok') or extra.get('medin') or extra.get('tito')):
        # A4's houses for the three huts (their people's topics are A3's)
        house = HOUSE_BAROK if extra.get('barok') else HOUSE_MEDIN if extra.get('medin') else HOUSE_TITO
        plot['house'] = house
        plot['title'] = title
    elif IN_WORLD and house:
        house, title = HOUSE_XEEN[house]
        plot['house'] = house
        plot['title'] = title
    elif extra.get('barok'):
        plot['title'] = title
        plot['effects'] = [{'lua': BAROK}]
    elif extra.get('medin'):
        plot['title'] = title
        plot['effects'] = [{'lua': MEDIN}]
    elif extra.get('tito'):
        plot['title'] = title
        plot['effects'] = [{'lua': TITO}]
    elif house:
        plot['house'] = house
        plot['title'] = title
    f, d = fp
    if kind == 'temple':
        # Pray N Pay: a nave with its door to the street and a round spire at its back (Vertigo's temple's form)
        W_, H_ = K.plot_extent(facing, fp)
        plot['parts'] = [{'id': 'nave', 'at': [64 + 256, 64], 'size': [W_ - 128 - 256, H_ - 128], 'wall_height': 448,
                          'roof': 'gable', 'roof_pitch': 52, 'ridge_along': 'ew',
                          'porches': [{'wall': 'w', 'depth': 160, 'posts': 32, 'height': 288, 'floor': 16}]},
                         {'id': 'spire', 'shape': 'round', 'at': [240, H_ // 2], 'radius': 200, 'sides': 8,
                          'wall_height': 1152, 'roof': 'cone', 'roof_pitch': 74, 'windows': 'none',
                          'textures': {'roof': '7hhr1rf'}}]
        plot['door'] = {'part': 'nave', 'wall': 'w'}
        plot['parts'][1]['at'] = [W_ - 240, H_ // 2]
        if extra.get('sign'):
            # A4 2026-11-22: the temple's caduceus over its door (MM7's temples; it was asked for and dropped)
            plot['parts'][0]['signs'] = [{'wall': 'w', 'bay': 0, 'texture': extra['sign'], 'hang': True,
                                          'size': K.sign_size(extra['sign']), 'out': 48, 'bottom': 120}]
    elif kind == 'chapel':
        W_, H_ = K.plot_extent(facing, fp)
        plot['parts'] = [{'id': 'nave', 'at': [64, 96], 'size': [W_ - 384, H_ - 192], 'wall_height': 384,
                          'roof': 'gable', 'roof_pitch': 50, 'ridge_along': 'ew', 'windows': 'all'},
                         {'id': 'bell', 'at': [W_ - 288, H_ // 2 - 112], 'size': [224, 224], 'wall_height': 768,
                          'roof': 'hip', 'roof_pitch': 60, 'windows': 'none', 'textures': {'roof': '7hhr1rf'}}]
        plot['door'] = {'part': 'nave', 'wall': 'w'}
    else:
        parts, door = K.shape(kind, facing, fp, kit, sign=extra.get('sign'),
                              roof_tex=extra.get('roof') or (K.ROOFS.get(kit) if kit not in ('rich',) else None))
        if extra.get('storeys', 1) > 1:
            for p in parts:
                if 'bottom' not in p and p.get('shape') != 'round':
                    p['wall_height'] = 512
        if extra.get('big'):
            for p in parts:
                p['wall_height'] = 384
        plot['parts'] = parts
        plot['door'] = door
    plots_by_space.setdefault(space, []).append(plot)
    pb = plan_buildings.setdefault(space, {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [], 'service': 'residence'}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append((extra.get('index', 0), fp))
    if house and 'index' not in extra:
        pb[bid]['service'] = title
    poly = K.footprint(x, y, facing, fp, turn)
    footprints.append((bid, plot.get('index'), poly))
    if kind == 'round_hut':
        dc = K.door_cell(x, y, 's', fp, turn, -0.08)
        out = K.door_cell(x, y, 's', fp, turn, 0.9)
    else:
        dc = K.door_cell(x, y, facing, fp, turn, 0.0)
        out = K.door_cell(x, y, facing, fp, turn, 0.9)
    doors_out.append((bid, plot.get('index'), dc, out))

# The compact town (2026-11-16) left some houses of a group out: number each group's plots 1 to n again, in the order
# of their old numbers (the plan's groups count from 1 without holes), and the guild stewards' houses with them.
def renumber(entries):
    old = {}
    for e in entries:
        if 'index' in e[10]:
            old.setdefault(e[0], []).append(e[10]['index'])
    new_of = {(b, i): k + 1 for b, ixs in old.items() for k, i in enumerate(sorted(ixs))}
    for e in entries:
        if 'index' in e[10]:
            e[10]['index'] = new_of[(e[0], e[10]['index'])]
    return new_of
_new = renumber(list(NORTH) + QUAY + list(SOUTH))
MEMBERS = {(b, _new[(b, i)]): v for (b, i), v in MEMBERS.items()}
for e in NORTH:
    add_plot('district:north_bank', e, 'link:main_street')
add_plot('district:north_bank', STABLES, 'link:north_road')
for e in SOUTH:
    add_plot('district:south_bank', e, 'link:south_street')
for e in QUAY:
    add_plot('zone:quays', e, None)
for e in WILD_HOUSES:
    add_plot('zone:x2', e, None)
# a plan building's footprints in the order of its plots' indices (the compact town's rows list them out of order)
for _pb in plan_buildings.values():
    for _b in _pb.values():
        _b['footprint_cells'] = [fp for _, fp in sorted(_b['footprint_cells'], key=lambda t: t[0])]

def check_roads():
    bad = []
    for b, ix, poly in footprints:
        for line in COBBLE + DIRT_PATHS:
            # 2026-11-16: 0.45 (0.55 before): a house front may stand at the road tiles' edge, half a cell from
            # the line, as shipped towns' doors open onto their streets
            if K.line_hits_poly(line, poly, 0.45 if line in COBBLE else 0.55):
                bad.append('road under or against %s#%s: %s' % (b, ix, line[:3]))
        for line in LANES:
            if K.line_hits_poly(line, poly, 0.3):
                bad.append('lane under %s#%s: %s' % (b, ix, line))
    def shrunk(poly):      # plots may touch (the compact town's rows); they may not overlap
        cx = sum(v[0] for v in poly) / len(poly)
        cy = sum(v[1] for v in poly) / len(poly)
        return [(cx + (v[0] - cx) * 0.98, cy + (v[1] - cy) * 0.98) for v in poly]
    for i, (b, ix, p) in enumerate(footprints):
        for (b2, ix2, q) in footprints[i + 1:]:
            p_, q_ = shrunk(p), shrunk(q)
            if any(K.inside(v, q_) for v in p_) or any(K.inside(v, p_) for v in q_):
                bad.append('plots overlap: %s#%s and %s#%s' % (b, ix, b2, ix2))
    if bad:
        raise SystemExit('\n'.join(bad))
check_roads()

# ---------------------------------------------------------------------------------------------------------------
# The dungeon doors (DOORS.md; the dungeons' exits arrive in front of them)
# ---------------------------------------------------------------------------------------------------------------
DEN_X = 66.5                       # the Robbers' Den's door in the south quay's retaining wall, east of the bridge
DEN_Y = 56.7                       # the frame's middle on the quay (a doorway takes the land's height at its middle)
LAIR_AT = (23, 29.0)               # the Ogre Lair's cave mouth (footprint middle), looking south
YAK_AT = (60.0, 99.0)              # the Temple of Yak's front (plot NW corner), its door looking north
TOWER_C = (31, 58)                 # Darzog's Tower's middle on the island; its door looks east
TOWER_R = 896
SHIP_AT = (83.6, 53.4)             # Nystor's ship's middle, east of his pier, along the river
SHIP_WORD = True   # A1 merge point 6: `from.world` (2026-11-20)
PAIR = {11: (0, 0.35), 14: (0, 0.35), 15: (0, 0.35)}   # a town prop's partner offset in cells when not (0.35, 0)
# (dress_check.py); A5 fifth session (D-14): 11, 14, 15 pair along their walls
DROPPED_PROPS = (13, 16, 17)      # D-14: a barrel on the south street, kegs on two walking lines (decorations 1573-1582)

# ---------------------------------------------------------------------------------------------------------------
# Signs and lines (the source's, xeen/aaze0030 unless named)
# ---------------------------------------------------------------------------------------------------------------
def msg(text):
    return {'lua': 'evt.SimpleMessage("%s")' % text.replace('\\', '\\\\').replace('"', '\\"')}

def sign(sid, at, title, text, height=224, width=160):
    return {'id': sid, 'kind': 'sign', 'at': list(at), 'height': height, 'width': width, 'title': title,
            'effects': [msg(text)]}

def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d

def build():
    os.makedirs(OUT, exist_ok=True)
    # ================================ project.yml
    neighbours = [
        # 2026-11-16 (S8g): the studio writes the arrival words as the game reads them (MapStats.cpp
        # parseMergedOutdoorTravelSide: "left" enters by the east start, "right" by the west start), so the way to X1
        # is two-way and each arrival side is the true one; before, east-west ways said the opposite side, one way.
        {'id': 'edge:east', 'to': 'xeen_x1.odm', 'kind': 'edge', 'side': 'east', 'days': 3, 'arrival_side': 'west',
         'approach': 'The river road along the Great River\'s north bank, east to Vertigo, at y 46.',
         'notes': "X1 Vertigo Meadows: arrives at X1's west start (its west road); X1's own edge:west leads back here."},
        {'id': 'edge:west', 'to': 'xeen_x3.odm' if X3_LIVE else '7out03.odm', 'kind': 'edge', 'side': 'west',
         'days': 5, 'arrival_side': 'east', **({} if X3_LIVE else {'one_way': True, 'screened': True}),
         'approach': "The west road along Lake Darzog's north shore, over the ogres' bridge, to the west edge at y 40.",
         'notes': 'X3 Lifeforce Lagoon in the design (not built). Stand-in until X3 exists: Erathia (MM7), one way so '
                  'that Erathia keeps its own travel.'},
        {'id': 'edge:north', 'to': 'xeen_x4.odm' if X4_LIVE else '7out13.odm', 'kind': 'edge', 'side': 'north',
         'days': 5, 'arrival_side': 'south', **({} if X4_LIVE else {'one_way': True, 'screened': True}),
         'approach': 'The north road through the farmland to the north edge at x 66.',
         'notes': 'X4 Burlock Savannah in the design (not built). Stand-in until X4 exists: Tatalia (MM7), one way.'},
        {'id': 'boat:vertigo', 'to': 'xeen_x1.odm', 'kind': 'boat', 'days': 1, 'service': "Captain Nystor's Dock",
         'schedule': {'weekdays': ['monday', 'wednesday', 'friday']}, 'listed_only': True,
         'notes': ("Down the river to Vertigo: Captain Nystor's pier takes the party there for 100 gold (an event, "
                   "teleport to Vertigo's creek bank); the dock house opens MM7's Lady Catherine (486) with its own "
                   "MM7 routes as the stand-in (as X1's stables).")},
        {'id': 'door:xd21', 'to': 'xeen_xd21.blv', 'kind': 'door',
         'arrival_hint': "Just inside the Robbers' Den's door under the great bridge.",
         'notes': DOOR_NOTES['xd21']},
        {'id': 'door:xd27', 'to': 'xeen_xd27.blv', 'kind': 'door', 'arrival_hint': "Inside the cave mouth in the ogres' bluff.",
         'notes': DOOR_NOTES['xd27']},
        {'id': 'door:xd06', 'to': 'xeen_xd06.blv', 'kind': 'door', 'condition': {'qbit': 'yak_stone'},
         'arrival_hint': "Inside the Temple of Yak's door.", 'notes': DOOR_NOTES['xd06']},
        {'id': 'door:xd12', 'to': 'xeen_xd12.blv', 'kind': 'door', 'condition': {'item': 'skeleton_key'},
         'arrival_hint': "Inside Darzog's Tower's door.", 'notes': DOOR_NOTES['xd12']},
    ]
    project = {
        'format': 0, 'id': STEM, 'name': 'Rivercity and Lake Darzog', 'world': 'xeen' if IN_WORLD else 'mm7',
        'kind': 'outdoor',
        'profile': 'odm', 'map_code': 'X2', 'units': {'plan_grid': 512}, 'extent': {'terrain_cells': 128},
        'map_stats': {
            'id': 9136, 'reference': '7out03.odm', 'encounter_chance': 10, 'treasure_level': 1, 'trap_dice': 1, 'perception_difficulty': 2,
            'refill_days': 672, 'music': 32, 'environment': 'plains', 'lock_difficulty': 2,
            'slots': [
                {'monster': "Will ' O Wisp", 'tier': 1, 'per_marker': [2, 4], 'weight': 45},
                {'monster': 'Archer', 'tier': 1, 'per_marker': [2, 3], 'weight': 35},
                {'monster': 'Ogre', 'tier': 2, 'per_marker': [2, 3], 'weight': 20},
            ] if not IN_WORLD else [
                # Rebase (A5, 2026-11-20; MAPS 0: 135 at load, groups 2-4): sprites 2-3 a marker (2-4 before: 154
                # at load), rangers 2-3, ogres 2-3 at the crossings; A2's slot families.
                {'monster': XEEN_SLOT['sprites'], 'tier': 1, 'per_marker': [2, 3], 'weight': 45},
                {'monster': XEEN_SLOT['rangers'], 'tier': 1, 'per_marker': [2, 3], 'weight': 35},
                {'monster': XEEN_SLOT['ogres'], 'tier': 0, 'per_marker': [2, 3], 'weight': 20},
            ]},
        'neighbours': neighbours,
        'qbits': {'yak_stone': 110101, 'lake_beasts_slain': 110201, 'crodo_bottle_lake': 110202,
                  'ligono_skull': 110203, 'barok_pendant': 110204, 'faery_wand': 110205, 'sprite_eggs': 110206},
        'items': XEEN_ITEMS if IN_WORLD else {'skeleton_key': 1461},
        'rules': {'weather': 'world default', 'respawn': 'entrance:party_start',
                  'town_portal_anchor': 'entrance:party_start'},
        'notes': ("X2 Rivercity and Lake Darzog, the Cloudside hub, a new map with no original (devdocs/xeen/MAPS.md). "
                  "Built and played as an MM7 map (world: mm7) until worlds/xeen exists, as X1 is. Stand-ins: slot 1 "
                  "Killer sprites is MM7's Will o' Wisp family (Dancing Light 15; the dark south end's Wisps 23), "
                  "slot 2 Evil rangers the Archer family (Archer 9, the camps' Bowmen 19), slot 3 Ogres the Ogre "
                  "family at tier 2 (Ogre Raider 20; the lair's Ogre Chieftain 28); the three lake dragons are Young "
                  "Dragons (60). Houses open Steadwick's (Erathia, MM7) house rows and Erathia's residence rows under "
                  "Rivercity's names; the Skeleton Key is MM7's William's Tower Key 1461 (Xeen item 12100 planned). "
                  "Written by output/studio_cal/x2/tools/gen.py."),
    }
    # ================================ plan.yml
    spaces = []
    def space(sid, kind, name, purpose, **kw):
        d = {'id': sid, 'kind': kind, 'name': name, 'purpose': purpose}
        d.update(kw)
        if sid in plan_buildings:
            d['buildings'] = list(plan_buildings[sid].values())
        spaces.append(d)
    space('zone:x2', 'wild', 'Rivercity and Lake Darzog',
          'The open land round the town: farmland north, the lake west, the fairy woods south, the rim beyond.',
          floor=PLATEAU, density='sparse')
    space('town:rivercity', 'town', 'Rivercity',
          'The hub: a bridge city across the Great River, its two halves on terraces over stone quays, joined by the '
          'great bridge. Full services, the boat, the skill row; the robbers under the bridge.',
          floor=PLATEAU, safe=True, keep_clear=['spawns'])
    space('district:north_bank', 'district', 'Rivercity, north bank',
          'Bridge Square, the main street of shops (smith, armoury, tavern, bank, magic, alchemist), the training '
          'hall, the stables by the north road; the riverfront houses over the north quay.',
          part_of='town:rivercity', floor=PLATEAU, safe=True, keep_clear=['spawns'],
          theme="Erathia's and Harmondale's timber and grey stone kits (MM7), darker than Vertigo's cream plaster.",
          population=[{'id': 'pop:townsfolk', 'actor': 'Peasant', 'groups': 16, 'placed': True, 'hostile': False},
                      {'id': 'pop:guards', 'actor': 'Guard', 'groups': 8, 'placed': True, 'hostile': False}])
    space('district:south_bank', 'district', 'Rivercity, south bank',
          'The South Square, the guild row (Body, Mind, Spirit), the skill row (Arnold\'s Gym, Martial Training, '
          "Lindon's Temps), Pray N Pay; the dock and the robbers' door on the south quay.",
          part_of='town:rivercity', floor=PLATEAU, safe=True, keep_clear=['spawns'])
    space('zone:bridge_square', 'zone', 'Bridge Square',
          'Where the party starts: a paved court at the bridge\'s head with the fountain, the mirror, the market '
          'stalls and the ads, the bank, the alchemist and the tavern round it.',
          part_of='district:north_bank', floor=PLATEAU, empty=True, safe=True)
    space('zone:south_square', 'zone', 'South Square', 'The south head of the great bridge.',
          part_of='district:south_bank', floor=PLATEAU, empty=True, safe=True)
    space('zone:quays', 'zone', 'The quays', 'Stone quays under the terraces on both banks; the dock; the robbers\' door.',
          part_of='town:rivercity', floor=BANK, safe=True)
    space('zone:farmland', 'wild', 'The northern farmland',
          'Hedged fields, farmsteads and orchards on the plateau north of the town; evil rangers camp on its edges.',
          floor=[1024, 1200], density='sparse',
          population=[
              {'id': 'pop:rangers', 'slot': 2, 'groups': 11, 'per_marker': [2, 3], 'levels': [9, 9],
               'notes': 'Evil rangers (MM7 Archers as stand-ins) round their two camps and on the farm lanes.'},
              {'id': 'pop:ranger_camps', 'actor': 'Archer', 'groups': 10, 'placed': True, 'hostile': True,
               'notes': 'Five at each camp: three Archers and two Bowmen (19).'},
              {'id': 'pop:road_rangers', 'slot': 2, 'groups': 2, 'per_marker': [2, 3], 'levels': [9, 9],
               'notes': 'The first fight on the river road in from Vertigo, about 5,000 from the east arrival.'}])
    space('zone:ogre_hills', 'wild', "The ogres' hills",
          'The north-west: the north river\'s gorge through the hills, the ogres\' crossings, the Ogre Lair.',
          floor=[1024, 2200], relief='uneven', density='sparse',
          population=[
              {'id': 'pop:ogres', 'slot': 3, 'groups': 8, 'per_marker': [2, 3], 'levels': [20, 20],
               'notes': "Ogres at the river crossings only: the west road's bridge, the boulders below the lair, the "
                        'north crossing (MAPS: "river crossings only").'},
              {'id': 'pop:lair_ogres', 'actor': 'Ogre', 'groups': 3, 'placed': True, 'hostile': True,
               'notes': 'At the lair mouth: an Ogre Chieftain (28) and two Ogre Raiders.'}])
    space('water:lake', 'water', 'Lake Darzog', 'The lake west of town with the wooded island; three dragons circle it.',
          population=[{'id': 'pop:lake_dragons', 'actor': 'Young Dragon', 'groups': 3, 'placed': True, 'hostile': True,
                       'notes': "Medin's lake beasts (Q-C13): three named water dragons, level 60, a trap for a party "
                                'of 7-11. Young Dragons (60) as stand-ins, flying over the water round the island.'}])
    space('zone:lake_shore', 'wild', 'The lake shore',
          "Medin's hut and jetty, Crodo's bottle, the shore ruin, the obelisk on the south-west shore.",
          floor=BANK, density='sparse',
          population=[{'id': 'pop:west_shore', 'slot': 2, 'groups': 3, 'per_marker': [2, 3], 'levels': [9, 9],
                       'notes': 'Rangers by the obelisk and the shore ruin.'}])
    space('zone:island', 'zone', "Darzog's island", "The wooded island; Darzog's Tower (XD-12) and its jetty.",
          floor=ISLE_H)
    space('zone:fairy_woods', 'wild', 'The fairy woods',
          "South of the town: Danulf the Faery King's ring of stones, Tito's chapel, the Sage's Fountain, the sprites' "
          'egg hollow. Crazed killer sprites attack anyone in the forest (Q-C17).',
          floor=[900, 1250], density='dense',
          population=[{'id': 'pop:sprites', 'slot': 1, 'groups': 20, 'per_marker': [2, 4], 'levels': [15, 15],
                       'notes': "Killer sprites (MM7's Dancing Lights as stand-ins) in clusters through the woods, two "
                                'by each place.'}])
    space('zone:dark_end', 'wild', "The woods' dark south end",
          'A hollow of dead trees and bog before the rim: the Temple of Yak (XD-06), a fouled well, a burial cairn.',
          floor=[800, 1000], density='medium',
          population=[{'id': 'pop:dark_sprites', 'slot': 1, 'groups': 3, 'per_marker': [2, 3], 'levels': [15, 15]},
                      {'id': 'pop:temple_wisps', 'actor': 'Wisp', 'groups': 2, 'placed': True, 'hostile': True,
                       'notes': 'Wisps (23) before the temple: the band\'s C tier.'}])
    space('zone:rim', 'wild', 'The world rim', 'The cliff where the world ends along the south; Ligono in the surf.',
          floor=0, empty=True)
    space('water:river', 'water', 'The Great River', 'From Lake Darzog through Rivercity east to Vertigo.')
    space('water:north_river', 'water', 'The north river', 'Down from X4 through the ogres\' hills into the lake.')
    space('water:sky', 'water', 'Below the rim', 'Stand-in for the stars below the world rim: water far below.')
    for sid, name in (('junction:east_entry', 'East entry'), ('junction:west_end', 'West end of the main street'),
                      ('junction:north_fork', 'North fork'), ('junction:west_fork', 'West fork by the ogre bridge'),
                      ('junction:far_bank', "The ogres' bank"), ('junction:east_fork', 'East fork'),
                      ('junction:woods_fork', 'Woods fork')):
        space(sid, 'junction', name, 'A road junction.', part_of='zone:x2',
              signpost=sid in ('junction:east_entry', 'junction:north_fork', 'junction:west_fork', 'junction:woods_fork'))
    space('edge:east_end', 'road', 'East edge', 'Where the river road leaves for Vertigo (X1).', part_of='zone:x2')
    space('edge:west_end', 'road', 'West edge', 'Where the west road leaves for X3.', part_of='zone:x2')
    space('edge:north_end', 'road', 'North edge', 'Where the north road leaves for X4.', part_of='zone:farmland')
    for sid, name, part in (('zone:den_door', "The robbers' door", 'zone:quays'),
                            ('zone:lair_mouth', 'The Ogre Lair', 'zone:ogre_hills'),
                            ('zone:yak_front', 'The Temple of Yak', 'zone:dark_end'),
                            ('zone:tower_door', "Darzog's door", 'zone:island'),
                            ('zone:dock', "Captain Nystor's dock", 'zone:quays'),
                            ('zone:medin_jetty', "Medin's jetty", 'zone:lake_shore')):
        space(sid, 'zone', name, 'A way in or a crossing.', part_of=part)
    links = [
        {'id': 'link:east_road', 'from': 'junction:east_entry', 'to': 'edge:east_end', 'kind': 'road'},
        {'id': 'link:main_street', 'from': 'junction:east_entry', 'to': 'zone:bridge_square', 'kind': 'road'},
        {'id': 'link:main_street_w', 'from': 'zone:bridge_square', 'to': 'junction:west_end', 'kind': 'road'},
        {'id': 'link:west_road', 'from': 'junction:west_end', 'to': 'junction:west_fork', 'kind': 'road'},
        {'id': 'link:ogre_bridge', 'from': 'junction:west_fork', 'to': 'junction:far_bank', 'kind': 'bridge',
         'crosses': ['water:north_river']},
        {'id': 'link:west_road2', 'from': 'junction:far_bank', 'to': 'edge:west_end', 'kind': 'road'},
        {'id': 'link:north_road', 'from': 'zone:bridge_square', 'to': 'edge:north_end', 'kind': 'road'},
        {'id': 'link:great_bridge', 'from': 'zone:bridge_square', 'to': 'zone:south_square', 'kind': 'bridge',
         'crosses': ['water:river']},
        {'id': 'link:south_street', 'from': 'zone:south_square', 'to': 'district:south_bank', 'kind': 'road'},
        {'id': 'link:south_street_e', 'from': 'zone:south_square', 'to': 'district:south_bank', 'kind': 'road'},
        {'id': 'link:south_road', 'from': 'zone:south_square', 'to': 'junction:woods_fork', 'kind': 'road'},
        {'id': 'link:woods_path', 'from': 'junction:woods_fork', 'to': 'zone:yak_front', 'kind': 'path'},
        {'id': 'link:chapel_path', 'from': 'junction:woods_fork', 'to': 'zone:fairy_woods', 'kind': 'path'},
        {'id': 'link:lake_path', 'from': 'district:south_bank', 'to': 'zone:medin_jetty', 'kind': 'path'},
        {'id': 'link:lair_path', 'from': 'junction:far_bank', 'to': 'zone:lair_mouth', 'kind': 'path'},
        {'id': 'link:farm_lane_w', 'from': 'junction:north_fork', 'to': 'zone:farmland', 'kind': 'path'},
        {'id': 'link:farm_lane_e', 'from': 'junction:north_fork', 'to': 'zone:farmland', 'kind': 'path'},
        {'id': 'link:shrine_path', 'from': 'junction:east_fork', 'to': 'zone:farmland', 'kind': 'path'},
        {'id': 'link:medin_boat', 'from': 'zone:medin_jetty', 'to': 'zone:island', 'kind': 'water',
         'notes': "Medin's boat, once the lake dragons are dead (a teleport both ways)."},
        {'id': 'link:quay_stairs', 'from': 'town:rivercity', 'to': 'zone:quays', 'kind': 'stairs'},
        {'id': 'link:lane_w', 'from': 'link:main_street_w', 'to': 'district:north_bank', 'kind': 'road',
         'notes': 'The lane west of Bridge Square, from the main street to the promenade and the quay steps.'},
        {'id': 'link:lane_e', 'from': 'link:main_street', 'to': 'district:north_bank', 'kind': 'road',
         'notes': 'The lane by the smithy, from the main street to the promenade and the quay steps.'},
        {'id': 'link:lane_se', 'from': 'link:south_street_e', 'to': 'district:south_bank', 'kind': 'road',
         'notes': "The lane past Lindon's Temps to the back lane."},
    ]
    entrances = [
        {'id': 'entrance:party_start', 'space': 'zone:bridge_square', 'kind': 'arrival',
         'how': 'A new game here (tests), the respawn and the Town Portal anchor.'},
        {'id': 'entrance:east_road', 'space': 'edge:east_end', 'kind': 'both', 'neighbour': 'edge:east'},
        {'id': 'entrance:west_road', 'space': 'edge:west_end', 'kind': 'both', 'neighbour': 'edge:west'},
        {'id': 'entrance:north_road', 'space': 'edge:north_end', 'kind': 'both', 'neighbour': 'edge:north'},
        {'id': 'entrance:dock', 'space': 'zone:dock', 'kind': 'both', 'neighbour': 'boat:vertigo'},
        {'id': 'entrance:xd21_den', 'space': 'zone:den_door', 'kind': 'both', 'neighbour': 'door:xd21'},
        {'id': 'entrance:xd27_lair', 'space': 'zone:lair_mouth', 'kind': 'both', 'neighbour': 'door:xd27'},
        {'id': 'entrance:xd06_yak', 'space': 'zone:yak_front', 'kind': 'both', 'neighbour': 'door:xd06',
         'condition': {'qbit': 'yak_stone'}},
        {'id': 'entrance:xd12_tower', 'space': 'zone:tower_door', 'kind': 'both', 'neighbour': 'door:xd12',
         'condition': {'item': 'skeleton_key'}},
        {'id': 'entrance:x9_fall', 'space': 'zone:island', 'kind': 'arrival',
         'how': "A fall from X9, the Clouds of Xeen (D-50 change 4; Xeen.skyFall, with falling damage): on Darzog's "
                'island by the tower door; the lake dragons are leashed at least 5,888 from it (D-54).'},
    ]
    pois = [
        {'id': 'poi:obelisk', 'space': 'zone:lake_shore', 'kind': 'obelisk', 'behaviour': 'A word of the Cloudside riddle.'},
        {'id': 'poi:sage_fountain', 'space': 'zone:fairy_woods', 'kind': 'fountain',
         'behaviour': "Sage's Fountain: +2 Intellect, permanent, once (aaze0015:7-8, rescaled from +10)."},
        {'id': 'poi:shrine_electricity', 'space': 'zone:farmland', 'kind': 'shrine',
         'behaviour': 'Shrine of Electricity: +5 Air resistance, permanent, once (aaze0015:4-5, rescaled).'},
        {'id': 'poi:danulf_ring', 'space': 'zone:fairy_woods', 'kind': 'stone_ring',
         'behaviour': "Danulf the Faery King's ring of stones: his errand (Q-C17, aaze0011:0-3)."},
        {'id': 'poi:tito_chapel', 'space': 'zone:fairy_woods', 'kind': 'chapel',
         'behaviour': "Tito the Elf Priest's chapel: his errand (Q-C18, aaze0011:4-7)."},
        {'id': 'poi:medin_jetty', 'space': 'zone:lake_shore', 'kind': 'jetty',
         'behaviour': "Medin the Fisherman (Q-C13, aaze0011:8-12); his boat to the island once the dragons are dead."},
        {'id': 'poi:ligono', 'space': 'zone:rim', 'kind': 'spirit',
         'behaviour': 'Ligono the Spirit in the surf at the rim (Q-C19, aaze0015:10-15).'},
        {'id': 'poi:ligono_skull', 'space': 'zone:rim', 'kind': 'cairn', 'behaviour': "Ligono's skull among the rocks."},
        {'id': 'poi:ranger_camps', 'space': 'zone:farmland', 'kind': 'camp', 'count': 2,
         'behaviour': 'Evil-ranger camps with tents, a fire and a chest, five rangers each.'},
        {'id': 'poi:nystor_dock', 'space': 'zone:dock', 'kind': 'dock',
         'behaviour': "Captain Nystor's dock: the boat house (MM7's Lady Catherine) and his pier: a ride down the river "
                      "to Vertigo for 100 gold (aaze0030:65-66); his ogre errand (Q-C23, aaze0010:22-25)."},
        {'id': 'poi:crodo_bottle', 'space': 'zone:lake_shore', 'kind': 'bottle',
         'behaviour': 'Crodo\'s second bottle: "Help! I am in Darzog\'s Tower!--Crodo" (aaze0023:19).'},
        {'id': 'poi:barok_hut', 'space': 'zone:x2', 'kind': 'hut', 'behaviour': 'Barok the Sorcerer (Q-C2, aaze0030:34-38).'},
        {'id': 'poi:mirror', 'space': 'zone:bridge_square', 'kind': 'mirror',
         'behaviour': 'The town mirror: its two tips (aaze0030:68-69); the mirror network is not built.'},
        {'id': 'poi:town_fountain', 'space': 'zone:bridge_square', 'kind': 'fountain',
         'behaviour': 'Stopped by the sorceresses until Barok has his pendant (aaze0030:36); then +100 spell points.'},
        {'id': 'poi:sprite_eggs', 'space': 'zone:fairy_woods', 'kind': 'nest',
         'behaviour': 'The sprites\' egg hollow (aaze0015:0-1) and the stolen Wand of Faery Magic.'},
        {'id': 'poi:wells', 'space': 'zone:x2', 'kind': 'well', 'count': 5,
         'behaviour': 'Two in town, the farm well, the chapel\'s holy well (+25 HP), the fouled well in the dark end.'},
        {'id': 'poi:signs', 'space': 'zone:x2', 'kind': 'sign', 'count': 5, 'behaviour': 'Signposts at the forks.'},
        {'id': 'poi:ruins', 'space': 'zone:x2', 'kind': 'ruin', 'count': 4,
         'behaviour': 'The ruined watchtower, the shore ruin, the burial cairn, the grave field: three with a chest.'},
        {'id': 'poi:camps', 'space': 'zone:x2', 'kind': 'camp', 'count': 2,
         'behaviour': "The ogres' fire at the lair, a hunters' old camp in the woods."},
        {'id': 'poi:boulder', 'space': 'zone:ogre_hills', 'kind': 'stat_challenge',
         'behaviour': 'The ogres\' boulder by the west fork: Might 30 moves it (a cache under it).'},
        {'id': 'poi:ads', 'space': 'town:rivercity', 'kind': 'sign',
         'behaviour': "Rivercity's ads and the tavern patrons' lines (aaze0030:17-33, 67)."},
    ]
    landmarks = [
        {'id': 'landmark:great_bridge', 'space': 'town:rivercity', 'what': 'The great bridge on its four arches',
         'seen_from': ['zone:quays', 'water:river']},
        {'id': 'landmark:darzog_tower', 'space': 'zone:island', 'what': "Darzog's dark tower on the island",
         'seen_from': ['town:rivercity', 'zone:lake_shore']},
        {'id': 'landmark:temple_spire', 'space': 'district:south_bank', 'what': "Pray N Pay's spire"},
        {'id': 'landmark:rim', 'space': 'zone:rim', 'what': 'The cliff at the end of the world'},
    ]
    plan = {
        'format': 0, 'level': 'L3',
        'pitch': ("The hub of Cloudside. Rivercity spans the Great River: two terraced halves over stone quays, joined "
                  "by a great arched bridge, a busy, crooked, crime-ridden town with every service, the boat and the "
                  "skill row; the robbers keep their den under the bridge. West lies Lake Darzog, its wooded island "
                  "crowned by the sealed dark tower of the King's vanished sorcerer, three dragons circling it. North "
                  "is farmland where evil rangers camp; north-west the ogres hold the river crossings. South the fairy "
                  "woods, where crazed sprites attack anyone, darken toward the Temple of Yak and the world rim."),
        'purpose': ('Act II hub (party 7 to 11): full services, four dungeon doors (XD-21, XD-27, XD-06, XD-12), the '
                    'road from Vertigo, Medin, Barok, Danulf, Tito, Ligono and Nystor\'s errands.'),
        'mood': 'River light and bustle in town; open fields north; green and then gloomy woods south; the tower menacing.',
        'datum': 'water:sky',
        'spaces': spaces, 'links': links, 'entrances': entrances, 'points_of_interest': pois, 'landmarks': landmarks,
        'height_bands': [
            {'id': 'band:land', 'range': [560, 1400],
             'spaces': ['zone:x2', 'town:rivercity', 'zone:farmland', 'zone:fairy_woods', 'zone:lake_shore']},
            {'id': 'band:hills', 'range': [1000, 2400], 'spaces': ['zone:ogre_hills']},
            {'id': 'band:below_rim', 'range': [0, 64], 'spaces': ['zone:rim']},
        ],
        'atmosphere': "Fair to cloudy sky by the world's chances; Erathia's music (32) as a stand-in.",
        'sketch': {'file': 'sketch.yml', 'grid': 512},
        'notes': 'Written by output/studio_cal/x2/tools/gen.py from MAPS.md X2.',
    }
    # ================================ sketch.yml
    rim = [
        {'side': 'north', 'span': [0, 58], 'form': 'ridge', 'height': [2200, 3400], 'floor': 1600, 'crest': 10,
         'roughness': 100},
        {'side': 'north', 'span': [58, 74], 'form': 'level', 'height': 1150, 'meet': 6,
         'notes': 'The north road runs out to the edge (to X4).'},
        {'side': 'north', 'span': [74, 128], 'form': 'ridge', 'height': [1800, 2900], 'floor': 1200, 'crest': 10,
         'roughness': 100},
        {'side': 'west', 'span': [0, 36], 'form': 'ridge', 'height': [2200, 3200], 'floor': 1500, 'crest': 10,
         'roughness': 100},
        {'side': 'west', 'span': [36, 46], 'form': 'level', 'height': 1024, 'meet': 6,
         'notes': 'The west road runs out to the edge (to X3).'},
        {'side': 'west', 'span': [46, 94], 'form': 'ridge', 'height': [1700, 2700], 'floor': 1000, 'crest': 10,
         'roughness': 100},
        {'side': 'west', 'span': [94, 104], 'form': 'level', 'height': 1100, 'meet': 6,
         'notes': "2026-11-16: the ridge ends before the world rim, so that the rim's cliff is the land's 900 there "
                  'and not a cut through a 2,700 hill.'},
        {'side': 'east', 'span': [0, 40], 'form': 'ridge', 'height': [1800, 2800], 'floor': 1100, 'crest': 10,
         'roughness': 100},
        {'side': 'east', 'span': [40, 58], 'form': 'level', 'height': 760, 'meet': 6,
         'notes': 'The river and the river road run out to the edge (to X1, Vertigo).'},
        {'side': 'east', 'span': [58, 94], 'form': 'ridge', 'height': [1600, 2600], 'floor': 1000, 'crest': 10,
         'roughness': 100},
        {'side': 'east', 'span': [94, 104], 'form': 'level', 'height': 1100, 'meet': 6,
         'notes': '2026-11-16: as the west side, the ridge ends before the rim.'},
        {'side': 'south', 'form': 'level', 'height': 0, 'meet': 1,
         'notes': 'The world rim: the land ends in a cliff at y 104; below it, water at 0 stands for the stars.'},
    ]
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its height function.'},
        'terraces': [
            {'polygon': [[53, 40], [78, 40], [78, N_EDGE], [53, N_EDGE]], 'height': PLATEAU, 'slope': 0,
             'notes': "The north town's edge over the quay: a step held by the retaining wall."},
            {'polygon': [[53, S_EDGE], [81, S_EDGE], [81, 62], [53, 62]], 'height': PLATEAU, 'slope': 0,
             'notes': "The south town's edge over the quay."},
            {'polygon': [[28, 55], [35, 55], [35, 61], [28, 61]], 'height': ISLE_H, 'slope': 2,
             'notes': "The island's crown, level under the tower."},
        ],
        'cuts': [
            {'polygon': [[53, N_EDGE], [78, N_EDGE], [78, 51], [53, 51]], 'floor': BANK, 'open': [1, 3], 'slope': 3,
             'notes': 'The north quay, 640, under the terrace wall; open at both ends to the banks.'},
            {'polygon': [[53, 55], [81, 55], [81, S_EDGE], [53, S_EDGE]], 'floor': BANK, 'open': [1, 3], 'slope': 3,
             'notes': 'The south quay.'},
        ],
        'ridges': [
            {'line': [[20, 27], [26, 27]], 'height': 1800, 'width': 2, 'slope': 2,
             'notes': "The bluff the Ogre Lair's mouth is cut into."},
            {'line': [[57, 102], [67, 102]], 'height': 1600, 'width': 2, 'slope': 2,
             'notes': 'The rise the Temple of Yak is built against.'},
        ],
        'cliffs': [
            {'line': [[0, RIM_Y], [40, RIM_Y], [80, RIM_Y], [128, RIM_Y]], 'drop': 900, 'down': 'right',
             'notes': 'The world rim (drawn west to east, the low side south, on the right).'},
        ],
    }
    water = {
        'rivers': [
            {'id': 'water:river', 'line': RIVER_W, 'width_cells': 4, 'level': RIVER,
             'notes': 'The Great River from the lake to Rivercity.'},
            {'id': 'water:river', 'line': RIVER_TOWN, 'width_cells': 3, 'level': RIVER,
             'notes': "Between Rivercity's quays (2026-11-16: water nodes 51-55, 49-55 before; the town's halves 9 cells apart)."},
            {'id': 'water:river', 'line': RIVER_E, 'width_cells': 4, 'level': RIVER},
            {'id': 'water:river', 'line': RIVER_MID, 'width_cells': 4, 'level': RIVER},
            {'id': 'water:river', 'line': RIVER_EAST, 'width_cells': 3, 'level': RIVER,
             'notes': "On to X1's west edge, where it is Pitchfork Creek (y 51, 3 wide)."},
            {'id': 'water:north_river', 'line': NORTH_RIVER, 'width_cells': 3, 'level': RIVER,
             'notes': "From X4 through the ogres' gorge into the lake."},
        ],
        'bodies': [
            {'id': 'water:lake', 'kind': 'lake', 'level': RIVER, 'polygon': LAKE_N,
             'notes': 'Lake Darzog, north half (two bodies round the island).'},
            {'id': 'water:lake', 'index': 2, 'kind': 'lake', 'level': RIVER, 'polygon': LAKE_S,
             'notes': 'Lake Darzog, south half.'},
            {'id': 'water:sky', 'kind': 'sea', 'level': 0, 'polygon': [[0, RIM_Y + 1], [128, RIM_Y + 1], [128, 128],
                                                                      [0, 128]],
             'notes': 'Below the rim: stands for the stars (the game draws no void).'},
        ],
    }
    water['bodies'][0]['index'] = 1
    roads = [
        {'link': 'link:east_road', 'line': EAST_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:main_street', 'line': MAIN_E, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:main_street_w', 'line': MAIN_W, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:west_road', 'line': WEST_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:west_road2', 'line': WEST_ROAD2, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:north_road', 'line': NORTH_ST, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:south_street', 'line': SOUTH_ST_W, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:south_street_e', 'line': SOUTH_ST_E, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:south_road', 'line': SOUTH_RD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:lane_w', 'line': LANE_W, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:lane_e', 'line': LANE_E, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:lane_se', 'line': LANE_SE, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:woods_path', 'line': WOODS_PATH, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:chapel_path', 'line': CHAPEL_PATH, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:lake_path', 'line': LAKE_PATH, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:lair_path', 'line': LAIR_PATH, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:farm_lane_w', 'line': FARM_LANE_W, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:farm_lane_e', 'line': FARM_LANE_E, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:shrine_path', 'line': SHRINE_PATH, 'width': 'lane', 'surface': 'dirt'},
    ]
    districts = [
        {'space': 'zone:x2', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]], 'rest': True,
         'plots': plots_by_space['zone:x2']},
        {'space': 'town:rivercity', 'polygon': TOWN_POLY},
        {'space': 'district:north_bank', 'polygon': [[52, 35], [80, 35], [80, 49], [52, 49]],
         'plots': plots_by_space['district:north_bank']},
        {'space': 'district:south_bank', 'polygon': [[52, 57], [80, 57], [80, 68], [52, 68]],
         'plots': plots_by_space['district:south_bank']},
        {'space': 'zone:bridge_square', 'polygon': BRIDGE_SQ},
        {'space': 'zone:south_square', 'polygon': SOUTH_SQ},
        {'space': 'zone:quays', 'polygon': [[53, 49], [82, 49], [82, 57], [53, 57]],
         'plots': plots_by_space['zone:quays']},
        {'space': 'zone:farmland', 'polygon': [[38, 19], [109, 19], [109, 33], [38, 33]]},
        {'space': 'zone:ogre_hills', 'polygon': [[19, 19], [38, 19], [38, 43], [19, 43]]},
        {'space': 'zone:lake_shore', 'polygon': [[19, 43], [49, 43], [49, 79], [19, 79]]},
        {'space': 'zone:island', 'polygon': [[25, 52], [37, 52], [37, 64], [25, 64]]},
        {'space': 'zone:fairy_woods', 'polygon': [[38, 68], [98, 68], [98, 92], [38, 92]]},
        {'space': 'zone:dark_end', 'polygon': [[46, 90], [80, 90], [80, RIM_Y], [46, RIM_Y]]},
        {'space': 'zone:rim', 'polygon': [[0, RIM_Y], [128, RIM_Y], [128, 128], [0, 128]]},
    ]
    points = [
        {'id': 'entrance:party_start', 'at': [64, 45], 'facing': 's'},
        {'id': 'entrance:east_road', 'at': [106, 46], 'facing': 'w'},
        {'id': 'entrance:west_road', 'at': [21, 40], 'facing': 'e'},
        {'id': 'entrance:north_road', 'at': [66, 21], 'facing': 's'},
        {'id': 'entrance:dock', 'at': [77, 56], 'facing': 'e'},
        {'id': 'entrance:xd21_den', 'at': [67, 57]},
        {'id': 'entrance:xd27_lair', 'at': [23, 30]},
        {'id': 'entrance:xd06_yak', 'at': [62, 98]},
        {'id': 'entrance:xd12_tower', 'at': [34, 58]},
        {'id': 'entrance:x9_fall', 'at': X9_FALL, 'facing': 'e'},
        {'id': 'junction:east_entry', 'at': [85, 46]},
        {'id': 'junction:west_end', 'at': [53, 43]},
        {'id': 'junction:north_fork', 'at': [66, 30]},
        {'id': 'junction:west_fork', 'at': [36, 40]},
        {'id': 'junction:woods_fork', 'at': [63, 73]},
        {'id': 'junction:far_bank', 'at': [31, 40]},
        {'id': 'junction:east_fork', 'at': [88, 46]},
        {'id': 'poi:obelisk', 'at': [24, 77]}, {'id': 'poi:sage_fountain', 'at': [70, 86]},
        {'id': 'poi:shrine_electricity', 'at': [96, 31]}, {'id': 'poi:danulf_ring', 'at': [56, 82]},
        {'id': 'poi:tito_chapel', 'at': [80, 75]}, {'id': 'poi:medin_jetty', 'at': [46, 60]},
        {'id': 'poi:ligono', 'at': [27, 103]}, {'id': 'poi:ligono_skull', 'at': [97, 103]},
        {'id': 'poi:ranger_camps', 'index': 1, 'at': [88, 24]}, {'id': 'poi:ranger_camps', 'index': 2, 'at': [46, 22]},
        {'id': 'poi:nystor_dock', 'at': [78, 56]}, {'id': 'poi:crodo_bottle', 'at': [41, 71]},
        {'id': 'poi:barok_hut', 'at': [44, 37]}, {'id': 'poi:mirror', 'at': [62, 46]},
        {'id': 'poi:town_fountain', 'at': [64, 46]}, {'id': 'poi:sprite_eggs', 'at': [49, 87]},
        {'id': 'poi:boulder', 'at': [38, 43]}, {'id': 'poi:ads', 'at': [67, 45]},
        {'id': 'poi:wells', 'index': 1, 'at': [62, 40]}, {'id': 'poi:wells', 'index': 2, 'at': [63, 63]},
        {'id': 'poi:wells', 'index': 3, 'at': [60, 29]}, {'id': 'poi:wells', 'index': 4, 'at': [77, 78]},
        {'id': 'poi:wells', 'index': 5, 'at': [71, 98]},
        {'id': 'poi:signs', 'index': 1, 'at': [87, 45]}, {'id': 'poi:signs', 'index': 2, 'at': [67, 31]},
        {'id': 'poi:signs', 'index': 3, 'at': [37, 39]}, {'id': 'poi:signs', 'index': 4, 'at': [65, 72]},
        {'id': 'poi:signs', 'index': 5, 'at': [51, 60]},
        {'id': 'poi:ruins', 'index': 1, 'at': [100, 36]}, {'id': 'poi:ruins', 'index': 2, 'at': [34, 77]},
        {'id': 'poi:ruins', 'index': 3, 'at': [52, 96]}, {'id': 'poi:ruins', 'index': 4, 'at': [83, 78]},
        {'id': 'poi:camps', 'index': 1, 'at': [26, 31]}, {'id': 'poi:camps', 'index': 2, 'at': [60, 86]},
        {'id': 'zone:bridge_square', 'at': [64, 46]},
        {'id': 'zone:south_square', 'at': [64, 59]},
        {'id': 'landmark:great_bridge', 'at': [64, 53]},
        {'id': 'landmark:darzog_tower', 'at': [31, 58]},
        {'id': 'landmark:temple_spire', 'at': [66, 63]},
        {'id': 'landmark:rim', 'at': [64, RIM_Y]},
    ]
    def circ(cx, cy, r):
        return {'at': [cx, cy], 'r': r}
    areas = []
    def camps(pop, spots):
        for (cx, cy, n, r) in spots:
            k = sum(1 for a in areas if a['id'] == pop) + 1
            areas.append({'id': pop, 'index': k, 'kind': 'encounter', 'count': n, 'circle': circ(cx, cy, r)})
    # Encounter areas by role (MAPS X2: sprites, rangers, ogres at the crossings; none in the town buffer). Groups of
    # 2-3 (the slots' dice), clustered, about one in five by a chest, a door, a bridge or a camp.
    # D-85 (A5, 2026-11-21): no sprite marker within 5,888 of Danulf (missile range 5,120 + 768). The nest guards
    # (once (50, 86) x2), (52, 79), (66, 80) x2 and (60, 89) moved to small circles on the far side; the second marker
    # of each split pair comes last in the list, so the other areas keep their words (seeds) and their markers.
    # Area centres are whole cells (validate), so the circles are small: (46, 87) 5,971 from Danulf and 1,646 from the
    # nest, (46, 88) 6,182 / 1,677, (45, 80) 6,187, (69, 81) 6,300, (68, 78) 6,199, (60, 94) 6,062.
    # U-12 (agent xeen-rimmap-a, 2026-11-23): the void keeps the land's height on its outline, so the rim's last
    # row of tiles (y 104) is land now; the south-east corner (tile [107, 104]) lay 12,408 from every monster (521
    # tiles, empty_zones.py): the (94, 84) marker moves to (96, 86), 11,155 from the corner; counts unchanged
    camps('pop:sprites', [(44, 78, 2, 1.5), (46, 87, 1, 0.12), (47, 90, 1, 1), (45, 80, 1, 0.4),
                          (69, 81, 1, 0.3),
                          (96, 86, 1, 1), (82, 96, 1, 1),
                          (72, 88, 2, 1.5), (84, 82, 2, 1.5), (90, 88, 1, 1), (78, 91, 2, 1.5), (40, 84, 1, 1),
                          (86, 72, 1, 1), (51, 93, 1, 0.25),
                          (46, 88, 1, 0.15), (68, 78, 1, 0.25)])
    # D-88 (A5, 2026-11-21): no sprite marker within 5,888 of the XD-06 exit either (the named arrival (62, 98) and
    # XD-06's own move (62, 98.84)); the temple's five placed Killer Sprites (group 63) stay, waived by group in vw.sh.
    # (60, 94) -> (51, 93) and the three dark-end markers (55, 98) -> (49, 99), (71, 96) -> (74, 97),
    # (65, 92) -> (69, 85) (between the (69, 81) marker and the (72, 88) pair, about 2,200 from each, not on top of
    # the pair as (69, 88) would be).
    camps('pop:dark_sprites', [(49, 99, 1, 0.25), (74, 97, 1, 0.25), (69, 85, 1, 0.25)])
    # Final cloud round (2026-11-24, check_reach reach.spawn): markers whose circles crossed the north bound (cell
    # 18.9, +-23,106) put spawns where no party walks: (44, 19) r 1.5, (85, 19), (76, 18) -> (44, 21) r 1, (85, 21),
    # (76, 21); the ogres' (27, 19) r 1.5 -> (28, 21) r 1. D-133 (2026-11-24): (70, 23) -> (71, 23), its spawn stood
    # 1,997 from the north road's arrival (66, 21)
    camps('pop:rangers', [(44, 21, 2, 1), (50, 20, 1, 1), (92, 21, 2, 1.5), (85, 21, 1, 1), (58, 20, 2, 1.5), (71, 23, 1, 1),
                          (76, 21, 1, 1), (101, 27, 2, 1.5)])
    camps('pop:road_rangers', [(97, 44, 2, 1.5)])
    camps('pop:ogres', [(32, 42, 2, 1.5), (25, 42, 1, 1), (29, 32, 2, 1.5), (24, 35, 1, 1), (28, 21, 2, 1), (35, 29, 1, 1)])
    # F10 (A5 s29): the south-west rim corner (tile [20, 103]) lay 12,998 from every monster; the shore's pair moves
    # south from (22, 76) to (22, 88): 6,656 from the corner, 7,800 from Ligono (27, 103); counts unchanged
    camps('pop:west_shore', [(22, 88, 2, 1.5), (31, 78, 1, 1)])
    for a in areas:
        c = a['circle']
        near = min(math.hypot(c['at'][0] - p[0], c['at'][1] - p[1]) for p in [d[2] for d in doors_out
                   if K.inside(d[2], TOWN_POLY)]) - c['r']
        if near * 512 < 4500:
            raise SystemExit('monsters within 4,500 of a Rivercity door: %s %s (%.0f)' % (a['id'], c['at'], near * 512))
        # D-85: every talking quest giver outside the town keeps 5,888 (missile range 5,120 + 768) from every marker;
        # here the areas' centres, the built markers by tools/check_d85.py (vw.sh) (area 3's circle edge is at 5,775,
        # its marker at 6,126)
        for (npc, _, at) in NPC_ACTORS:
            gap = math.hypot(c['at'][0] - at[0], c['at'][1] - at[1]) * 512
            if gap < 5888:
                raise SystemExit('D-85: monsters within 5,888 of NPC %d: %s %s (%.0f)' % (npc, a['id'], c['at'], gap))
        if a['id'] in ('pop:sprites', 'pop:dark_sprites'):   # D-88: sprite markers off the XD-06 exit
            for at in XD06_EXIT:
                gap = (math.hypot(c['at'][0] - at[0], c['at'][1] - at[1]) - c['r']) * 512
                if gap < 5888:
                    raise SystemExit('D-88: sprites within 5,888 of the XD-06 exit: %s %s (%.0f)' % (a['id'], c['at'], gap))
    areas.append({'id': 'town:rivercity', 'kind': 'keep_clear', 'polygon': [[46, 30], [87, 30], [87, 70], [46, 70]]})
    areas.append({'id': 'zone:island', 'kind': 'keep_clear', 'polygon': [[24, 51], [38, 51], [38, 65], [24, 65]]})
    # X9's fall landing (entrance:x9_fall) lies inside zone:island's keep-clear above (D-50 change 4)
    views = [
        {'id': 'entrance:party_start', 'at': [64, 45], 'height': 200, 'look': [64, 56], 'purpose': 'The fountain and the great bridge.'},
        {'id': 'landmark:darzog_tower', 'at': [47, 58], 'height': 200, 'look': [31, 58],
         'purpose': "Darzog's Tower over the lake from Medin's jetty."},
        {'id': 'landmark:rim', 'at': [62, 96], 'height': 200, 'look': [62, 110], 'purpose': 'The rim past the temple.'},
    ]
    structures = []
    S = structures.append
    # ---------------------------------------------------------------- the great bridge, the quays, the walls
    S({'id': 'thing:great_bridge', 'kind': 'bridge', 'line': [[BRIDGE_X, N_EDGE - 0.25], [BRIDGE_X, S_EDGE + 0.25]],
       'width': 1024, 'height': PLATEAU, 'thickness': 96, 'kerb': 112,
       'arches': {'count': 4, 'rise': 288, 'form': 'segment', 'pier_width': 256},
       'towers': [160, 160, 448], 'textures': {'deck': 'cwb', 'side': 'cnb', 'pier': 'cnb'},
       'title': 'The Great Bridge',
       'notes': 'Four arches from the north terrace to the south terrace over both quays and the river.'})
    # P2 F26 (town_fit_check walls.hollow / walls.buried, as X1's terrace wall; agent xeen-rimmap-a 2026-11-23): a
    # wall's foot is its line's lowest land less 64 and its top the highest plus `height`; on the step's middle (the
    # land 832) that left a hollow 128 over the quay under the face and the terrace 74-144 over its top. Now the slab
    # is the step: `raise` takes its foot 64 into the quay and its top 48 over the terrace.
    step_mid = (PLATEAU + BANK) // 2
    # P3 F49 (pins p2, p5; 2026-11-24): the quay houses' back walls stood 33-64 in front of the walls' faces (their
    # walls are inset in their plots), a slot behind each (town_fit_check `houses.jammed`): each face comes 36 forward
    # over the quay (`toward` +1 south for the north wall, -1 north for the south wall), its back on the terrace's edge
    FILL = 36
    def retaining(tag, y, gaps, x1=77, toward=1):
        xs = [53.5] + [v for g in gaps for v in g] + [x1]
        y = y + toward * FILL / 2.0 / 512
        for k in range(0, len(xs), 2):
            if xs[k + 1] - xs[k] < 0.2:
                continue
            S({'id': 'thing:%s_wall_%d' % (tag, k // 2 + 1), 'kind': 'wall', 'line': [[xs[k], y], [xs[k + 1], y]],
               'raise': BANK - step_mid, 'height': PLATEAU + 48 - BANK, 'thickness': 512 + FILL,
               'textures': {'wall': 'cnb'}, 'title': 'Quay wall',
               'notes': 'The terrace\'s stone face over the quay.'})
    STAIRS_N = [58, 73]
    STAIRS_S = [59.5, 73]
    # F19 (the user 2026-11-22, wall pieces meet flush): the faces end 16 inside the bridge's sides (x 63 and 65);
    # at 1.05 they stopped 26 short of it, a slit beside each abutment
    BRIDGE_GAP = (BRIDGE_X - 0.97, BRIDGE_X + 0.97)
    retaining('north', N_EDGE, [(STAIRS_N[0] - 0.45, STAIRS_N[0] + 0.45), BRIDGE_GAP,
                                (STAIRS_N[1] - 0.45, STAIRS_N[1] + 0.45)])
    retaining('south', S_EDGE, [(STAIRS_S[0] - 0.45, STAIRS_S[0] + 0.45), BRIDGE_GAP,
                                (DEN_X - 0.4, DEN_X + 0.4), (STAIRS_S[1] - 0.45, STAIRS_S[1] + 0.45)], x1=81,
              toward=-1)
    for i, x in enumerate(STAIRS_N):
        S({'id': 'thing:quay_steps_n%d' % (i + 1), 'kind': 'stairs', 'line': [[x, 51.0], [x, N_EDGE - 0.15]],
           'width': 384, 'rise': PLATEAU - BANK, 'textures': {'wall': 'cnb'}, 'notes': 'Down to the north quay.'})
    for i, x in enumerate(STAIRS_S):
        S({'id': 'thing:quay_steps_s%d' % (i + 1), 'kind': 'stairs', 'line': [[x, 55.7], [x, S_EDGE + 0.15]],
           'width': 384, 'rise': PLATEAU - BANK, 'textures': {'wall': 'cnb'}, 'notes': 'Down to the south quay.'})
    # the Robbers' Den: a dark door in the south quay's wall beside the bridge's south abutment
    S({'id': 'thing:den_door', 'kind': 'doorway', 'at': [DEN_X, DEN_Y], 'turn': 180, 'height': 320, 'width': 224,
       'depth': 448, 'hood': 64, 'arch': 'round', 'textures': {'door': '7solid01', 'wall': 'cnb'},
       'title': "Enter the Robbers' Den", 'into': {'map': 'xeen_xd21.blv', 'at': [-2560, 320, 0], 'facing': 512},
       'notes': 'XD-21 (DOORS.md): the door in the quay wall under the great bridge\'s south end, facing the river.'})
    # Captain Nystor's dock: the boat house on the south quay, a pier into the river, a ship moored at it
    S({'id': 'thing:boat_house', 'kind': 'building', 'at': [77.5, 55.0], 'size': [2, 1.5], 'facing': 'n',
       'kit': 'timber', 'house': HOUSE_XEEN[486][0] if IN_WORLD else 486, 'title': "Captain Nystor's Dock",
       'parts': [{'id': 'house', 'at': [48, 48], 'size': [928, 640], 'wall_height': 384, 'roof': 'gable',
                  'ridge_along': 'ew', 'roof_pitch': 38, 'textures': {'roof': 'hhm1rf'},
                  'signs': [{'wall': 'w', 'bay': 0, 'texture': 'sgdock', 'hang': True, 'size': [64, 64], 'out': 48,
                             'bottom': 120}]}],
       'door': {'part': 'house', 'wall': 'w'}})
    S({'id': 'thing:nystor_pier', 'kind': 'bridge', 'line': [[80.2, 55.2], [80.2, 52.7]], 'width': 384,
       'height': BANK + 32, 'kerb': 0, 'textures': {'deck': 'trim11_32'}, 'title': "Captain Nystor's pier"})
    S({'id': 'thing:nystor_post', 'kind': 'sign', 'at': [80.8, 53.3], 'height': 256, 'width': 128,
       'title': 'Captain Nystor',
       **({'effects': [{'text': "Captain Nystor: \"I can give ya a boat ride to the Eastern shore for 100 gold "
                                "pieces. Ask at the dock house.\""}]} if IN_WORLD else {
       'condition': {'gold': {'at_least': 100}},
       'effects': [{'gold': -100},
                   {'text': "Captain Nystor: \"I can give ya a boat ride to the Eastern shore for 100 gold pieces.\""},
                   {'teleport': {'to': list(VERTIGO_BANK), 'direction': 0, 'map': 'xeen_x1.odm'}}],
       'locked_text': "Captain Nystor: \"A ride to Vertigo is 100 gold pieces, if ya be interested.\""})})
    S({'id': 'thing:nystor_ogres', 'kind': 'sign', 'at': [76.7, 56.6], 'height': 224, 'width': 160,
       'title': "Nystor's notice", 'effects': [msg(
           'Captain Nystor: "Those Ogres are ruining me! For months they have been throwing boulders at the boats that '
           'ply the waters around here. I want those Ogres gone and I am willing to pay well for the service." Their '
           'lair is in the hills north-west, up the north river.')]})
    # the robbers' quay: the empty strongbox (aaze0030:32-33)
    S({'id': 'thing:empty_chest', 'kind': 'crate', 'at': [67.8, 56.6], 'title': 'Chest',
       'effects': hook('x2.bank_chest') if IN_WORLD else [{'text': 'The chest is empty. What did you expect, money?'}]})
    if IN_WORLD:
        # Q-C2: the sorceresses' strongbox against the east wall of their house on the south quay (quay_houses#5, A4's
        # house 4098). Opening it brings out their two hired apprentices (A2's Apprentice Sorceress 11184, level 12,
        # placed only), hidden until then (group 54, below); the residents inside stay peaceful.
        # D-90 / F15 (A5 s29): Barok's pendant (12152) is the chest's own item; A3's q-c2.strongbox says map_gives
        S({'id': 'thing:sorceress_strongbox', 'kind': 'crate', 'at': [71.35, 56.45], 'title': 'Strongbox',
           'chest': {'items': [XEEN_ITEMS['baroks_pendant']]},
           'effects': [{'show_actors': 54}] + hook('q-c2.strongbox')})
    # ---------------------------------------------------------------- Bridge Square and the South Square
    # 2026-11-16: the square paved (a court 16 high, Steadwick's plaza stone) with the fountain on a step in its
    # middle, the mirror west of it, three market stalls along its east side and trees at the bridge's head.
    S({'id': 'thing:square_court', 'kind': 'platform', 'at': [64.0, 45.85], 'size': [3635, 1894], 'height': 16,
       'textures': {'top': 't3s2fl', 'wall': 't3s2b1'}, 'title': 'Bridge Square',
       'notes': "Bridge Square's paving, from the main street to the promenade at the bridge's head."})
    S({'id': 'thing:town_fountain', 'kind': 'fountain', 'at': [64.0, 46.0], 'title': 'Fountain', 'raise': 16,
       'tiers': [[96, 48]], 'textures': {'wall': 't3s2b1'},
       'condition': {'qbit': 'barok_pendant'},
       'effects': [{'add': {'var': 'SP', 'value': 100}}, {'text': '+100 Spell points'}],
       'else_effects': [{'text': "The fountain is dry: a brass plug stamped with a sorceress's sigil stops its spout."}]})
    S({'id': 'thing:mirror', 'kind': 'portal', 'at': [62.0, 46.9], 'radius': 112, 'sides': 12, 'turn': 90,
       'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'Magic Mirror',
       'effects': [{'lua': 'Xeen.useMirror(%d, eventId, continueStep)' % HOUSE_MIRROR}] if IN_WORLD else [msg(
           'The mirror shows Bridge Square, and you in it. Scratched round its frame: "If you say the name '
           'of a town to a mirror, it will take you there." Below, in another hand: "If you like to fight, '
           'say \'Warzone\' to a mirror." (The mirrors of Cloudside are not joined yet.)')],
       'notes': 'The town mirror (WORLD_DESIGN 3.3): a portal ring on its dais as the stand-in.'})
    S(sign('thing:ad_deep_mine', (60.85, 46.85), 'Notice board', 'REAL adventurers try Deep Mine Alpha!'))
    S(sign('thing:ad_board', (67.1, 44.5), 'Notice board', 'If you can read this ad, so can your customers.'))
    if not IN_WORLD:
        S(sign('thing:ad_navigation', (63.3, 44.35), 'Notice board',
               'School of Navigation 9N. Mountains in your way? Try due N.'))
    else:
        # A3's two hooks at their own doors (source/npcs/x2.yml): the school's sign beside its north door (house
        # 4069, door at x 54.25 on the wall y 43.1), Martin's beside his south door (4076, door x 74.25, wall y 47.4);
        # each off the door's sides by more than DRESSING's 288
        S(sign('thing:ad_navigation', (53.3, 42.85), 'School of Navigation', 'School of Navigation 9N.'))
        S(sign('thing:ad_mountains', (75.15, 47.6), 'Notice board', 'Mountains in your way? Try due N.'))
    if IN_WORLD:
        for _sid, _h in (('thing:ad_deep_mine', 'x2.ad_deep_mine'), ('thing:ad_board', 'x2.ad_customers'),
                         ('thing:ad_navigation', 'x2.ad_navigation'), ('thing:ad_mountains', 'x2.ad_mountains')):
            [st for st in structures if st['id'] == _sid][0]['effects'] = hook(_h)
    S(sign('thing:temple_board', (63.3, 63.5), 'Temple notice',
           'Pray, pay, and be healed today. (Under it someone has scratched: "I can\'t believe the cost of healing '
           'these days!")'))
    S(sign('thing:town_sign', (83.0, 44.4), 'Rivercity', 'Rivercity. Welcome, travellers. Mind your purses.'))
    # the skill row's teachers (aaze0030:0-5): their lines on boards at their doors
    S(sign('thing:board_gym', (70.25, 60.3), "Arnold's Gym",
           'Arnold the Strong: "I see that you are pale and weak. I will teach you Bodybuilding so that you can put '
           'some meat on your bones."', height=192, width=128))
    S(sign('thing:board_martial', (72.75, 60.3), 'Martial Training',
           'Flint the Armsmaster: "Fighting is simple. I\'ll teach you to be an Armsmaster in one easy lesson."',
           height=192, width=128))
    S(sign('thing:board_temps', (74.75, 60.3), "Lindon's Temps",
           'Lindon the Taskmaster: "I\'ll give you 100 gold for a week of work."', height=192, width=128))
    # the tavern's patrons (aaze0030:16-23), on the casks outside Bull's Tavern
    for i, (d, at, line) in enumerate([
            # 2026-11-20 (DRESSING.md): two pairs against the tavern's front either side of its door (65.5), not
            # out on the square. P3 F40 (2026-11-24): at 42.6, clear of its front (42.44; at 42.45 the casks stood
            # through it, town_fit_check `props.in_wall`)
            ('bigbarel', (64.85, 42.6), "A tavern patron, nose in his mug: \"Get lost. Can't you see I'm drinkin'?\""),
            ('7dec21', (66.15, 42.6), 'A tavern patron: "If Barok ever got his pendant back, this place might charge me '
                                     'for drinks."'),
            ('bigbarel', (64.55, 42.6), 'A tavern patron: "The tavern hired the sorceresses to run Barok out of town."'),
            ('7dec32', (66.45, 42.6), 'A tavern patron: "Now THIS is a wild town."')]):
        S(deco('thing:patron_%d' % (i + 1), d, at, title='Tavern patron', effects=[{'text': line}]))
    # stalls and props
    for sid, at, kit, roof in (('thing:stall_1', (66.45, 44.75), 'timber', 'hhm1rf'),
                               ('thing:stall_4', (66.45, 45.75), 'poor', 'hhp2rf'),
                               ('thing:stall_5', (66.45, 46.75), 'grey', 'hhm3rf')):
        S(K.stall(sid, at, -90, kit=kit, roof_tex=roof))
        # Final cloud round (X2 p6, the "cut path strip"): the floor was PLATEAU + 16 (the court's top), which the
        # studio's land, in steps of 32, rounded up to PLATEAU + 32 under each stall: the ground rose through the
        # court round the stalls, leaving a strip of paving at its east edge (town_fit_check `platforms.through`).
        # On the plateau the stalls' floor lies 16 under the court's top, which covers it.
        structures[-1]['floor'] = PLATEAU
    S(K.stall('thing:stall_2', (65.6, 58.9), 0, kit='poor', roof_tex='hhp2rf'))
    S(K.stall('thing:stall_3', (61.4, 58.9), 90, roof_tex='hhm3rf'))
    S(K.well('thing:well_north', (62.4, 39.6)))
    S(K.well('thing:well_south', (61.8, 64.0), roofed=True))
    # P3 (2026-11-24): prop 3 off Nystor's pier, whose foot now reaches the node line (80.6 stood in its side)
    for i, (d, at) in enumerate([('bigbarel', (76.6, 56.4)), ('7dec21', (77.0, 56.75)), ('7dec32', (81.0, 55.9)),
                                 ('7dec21', (55.0, 50.3)), ('bigbarel', (54.5, 50)), ('haybale2', (67.0, 38.2)),
                                 ('haybale2', (67.1, 38.9)), ('7dec21', (60.6, 50)), ('7dec32', (70.0, 50.2)),
                                 ('7dec21', (72.2, 56.4)), ('bigbarel', (58.15, 56.4)), ('7dec12', (53.2, 40)),
                                 ('7dec21', (63.4, 61.75)), ('7dec32', (60.68, 60.0)),
                                 # P3 F49 (p6): the pair off stall 5's corner (it stood 23 from its side)
                                 ('bigbarel', (67.7, 47.75)), ('7dec21', (67.3, 44.3)), ('7dec21', (60.5, 44.45))]):
        if IN_WORLD and i + 1 in DROPPED_PROPS:
            continue
        S(deco('thing:prop_%d' % (i + 1), d, at, **({'raise': 16} if K.inside(at, BRIDGE_SQ) else {})))
        # props 1+2 (the dock) and 4+5 (the north quay) stand as pairs already
        if IN_WORLD and d not in ('haybale2', '7dec12') and i + 1 not in (1, 2, 4, 5):     # barrels in pairs (DRESSING.md)
            _p = PAIR.get(i + 1, (0.35, 0))
            _at = (at[0] + _p[0], at[1] + _p[1])
            S(deco('thing:prop_%d_pair' % (i + 1), 'smlbarel', _at, **({'raise': 16} if K.inside(_at, BRIDGE_SQ) else {})))
    # ---------------------------------------------------------------- the ways in outside the town
    S({'id': 'thing:ogre_lair', 'kind': 'cave_mouth', 'at': list(LAIR_AT), 'size': [1024, 1024], 'floor': LAIR_FLOOR,
       'mouth': {'width': 512, 'height': 416, 'depth': 75}, 'textures': {'shell': 't2bs', 'door': '7solid01'},
       'roughness': 0.7, 'seed': 7, 'title': 'Enter the Ogre Lair', 'hint': 'Ogre Lair',
       'into': {'map': 'xeen_xd27.blv'}, 'notes': 'XD-27 (DOORS.md).'})
    for i, (d, at) in enumerate([('cmpfyr00', (24.9, 31.0)), ('dec05', (21.6, 30.9)), ('7dec18', (22.0, 31.6)),
                                 ('7dec20', (24.3, 31.5)), ('sklplrev', (21.95, 30.15)), ('sklplrev', (24.05, 30.15)),
                                 ('rock26', (20.8, 29.0)), ('rock12', (25.4, 28.8)), ('7rock08', (21.3, 27.9)),
                                 ('7rock09', (24.8, 27.7))]):
        S(deco('thing:lair_dress_%d' % (i + 1), d, at))
    # the ogres' boulders in the river below the lair (Q-C23: they block the boats)
    for i, at in enumerate([(28.0, 31.2), (28.6, 30.4), (27.6, 29.6), (28.9, 31.9)]):
        # P3 F51 (2026-11-24): the third, out in mid-stream past the party's reach, is a plain boulder (no click:
        # tools/xeen/check_reach.py); the other three carry the text
        words = {} if i == 2 else {'title': 'Boulders', 'effects': [
            {'text': "Boulders thrown into the river by the ogres: no boat gets past."}]}
        S(deco('thing:river_boulder_%d' % (i + 1), 'rock26' if i % 2 else 'rock12', at, **words))
    # Darzog's Tower: a tall dark round tower in three set-back storeys on the island; its door looks east
    S({'id': 'thing:darzog_tower', 'kind': 'building', 'at': [TOWER_C[0] - 2.5, TOWER_C[1] - 2.5], 'size': [5, 5],
       'kit': 'castle', 'floor': ISLE_H, 'title': "Darzog's Tower", 'facing': 'e',
       'parts': [
           {'id': 'base', 'shape': 'round', 'at': [1280, 1280], 'radius': TOWER_R, 'sides': 12, 'wall_height': 1024,
            'roof': 'none', 'windows': 'none', 'textures': {'wall': 'cwb1', 'door': '7solid01'}},
           {'id': 'mid', 'shape': 'round', 'at': [1280, 1280], 'radius': 704, 'sides': 12, 'bottom': 1024,
            'wall_height': 1024, 'roof': 'none', 'windows': 'alternate', 'textures': {'wall': 'cwb1'}},
           {'id': 'top', 'shape': 'round', 'at': [1280, 1280], 'radius': 576, 'sides': 12, 'bottom': 2048,
            'wall_height': 768, 'roof': 'cone', 'roof_pitch': 72, 'windows': 'all',
            'textures': {'wall': 'cwb1', 'roof': '7hhr1rf'}}],
       'door': {'part': 'base', 'wall': '3'},
       # XD-12's start in the gate hall, inside the tower door, facing west (its NOTES; A3/A8, seventh session:
       # event 96 moved the party to (0, 0, 0))
       'into': {'map': 'xeen_xd12.blv', 'at': [2752, 0, 0], 'facing': 1024},
       'condition': ({'lua': 'evt.GetHeldItemId() == %d or XeenQuests.hook("m13.darzog_door")'
                               % XEEN_ITEMS['skeleton_key']} if IN_WORLD else
                     {'any': [{'item': 'skeleton_key'}, {'lua': 'evt.GetHeldItemId() == 1461'}]}),
       'else_effects': [msg("Darzog's Tower. The door is black iron without a handle, and a keyhole shaped like a "
                            'skull. Whoever holds the key to it is not on this island.')],
       'notes': 'XD-12 (DOORS.md): the door on the east side, facing the jetty; key-gated.'})
    # the Temple of Yak: a stone front built against the rise in the dark south end, its door looking north
    S({'id': 'thing:yak_temple', 'kind': 'building', 'at': list(YAK_AT), 'size': [4, 2.5], 'facing': 'n',
       'kit': 'stone', 'title': 'Temple of Yak',
       'floor': 1088,
       'parts': [{'id': 'front', 'at': [448, 320], 'size': [1152, 896], 'wall_height': 704, 'roof': 'gable',
                  'ridge_along': 'ns', 'roof_pitch': 34, 'windows': 'none',
                  'textures': {'wall': 'cnb', 'door': '7solid01', 'roof': 'cwb1'},
                  'porches': [{'wall': 'n', 'depth': 288, 'posts': 64, 'height': 576, 'floor': 48}]},
                 {'id': 'tower_w', 'at': [96, 384], 'size': [320, 320], 'wall_height': 1088, 'roof': 'hip',
                  'roof_pitch': 62, 'windows': 'none', 'textures': {'wall': 'cnb', 'roof': 'cwb1'}},
                 {'id': 'tower_e', 'at': [1632, 384], 'size': [320, 320], 'wall_height': 1088, 'roof': 'hip',
                  'roof_pitch': 62, 'windows': 'none', 'textures': {'wall': 'cnb', 'roof': 'cwb1'}}],
       'door': {'part': 'front', 'wall': 'n'},
       'into': {'map': 'xeen_xd06.blv', 'at': [0, 384, 0], 'facing': 512},
       'condition': {'lua': 'XeenQuests.hook("q-c12.temple_door")'},
       'notes': 'XD-06 (DOORS.md), moved from X1. D-89 (A5 s29): open without the Yak Stone; A3\'s q-c12.temple_door '
                '(always true) before the entrance window (trans 5006).'})
    for i, (d, at) in enumerate([('dec06', (61.2, 99.0)), ('dec06', (62.8, 99.0)), ('sklplrev', (60.4, 98.6)),
                                 ('sklplrev', (63.6, 98.6)), ('7dec20', (60.0, 97.8)), ('7dec18', (64.2, 97.9))]):
        S(deco('thing:yak_dress_%d' % (i + 1), d, at))
    # ---------------------------------------------------------------- the lake: Medin, the island, Crodo's bottle
    S({'id': 'thing:medin_jetty', 'kind': 'bridge', 'line': [[47.6, 60.5], [44.6, 60.5]], 'width': 384,
       'height': BANK + 32, 'textures': {'deck': 'trim11_32'}, 'title': "Medin's jetty"})
    S({'id': 'thing:medin_boat', 'kind': 'sign', 'at': [44.9, 61.0], 'height': 192, 'width': 128,
       'title': "Medin's boat", 'condition': {'qbit': 'lake_beasts_slain'},
       'effects': [{'text': 'Medin rows you across to the island.'},
                   {'teleport': {'to': list(ISLAND_LANDING), 'direction': 180}}],
       'else_effects': hook('q-c13.medin_boat') if IN_WORLD else
                       [msg('Medin\'s boat is tied up. "Not while those beasts circle the island," says Medin.')]})
    S({'id': 'thing:island_jetty', 'kind': 'bridge', 'line': [[36.0, 60.5], [39.0, 60.5]], 'width': 384,
       'height': BANK + 32, 'textures': {'deck': 'trim11_32'}, 'title': 'Island jetty'})
    S({'id': 'thing:island_boat', 'kind': 'sign', 'at': [38.6, 61.0], 'height': 192, 'width': 128,
       'title': "Medin's boat",
       'effects': [{'text': 'Medin rows you back to his jetty.'},
                   {'teleport': {'to': list(MEDIN_LANDING), 'direction': 0}}]})
    S({'id': 'thing:island_chest', 'kind': 'chest', 'at': [34.4, 61.4], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 3}})
    S(deco('thing:crodo_bottle', '7dec41', (40.6, 70.7), title='Bottle',
           **({'effects': hook('m1.crodo_bottle_lake')} if IN_WORLD else {})) if IN_WORLD else
      deco('thing:crodo_bottle', '7dec41', (40.6, 70.7), title='Bottle',
           condition={'not': {'qbit': 'crodo_bottle_lake'}},
           effects=[{'qbit': 'crodo_bottle_lake'},
                    msg("Inside the bottle, washed up on the shore, you find a message that reads: Help! I am in "
                        "Darzog's Tower!--Crodo")],
           else_effects=[{'text': 'An empty bottle.'}]))
    # ---------------------------------------------------------------- the fairy woods
    S({'id': 'thing:danulf_ring', 'kind': 'stone_ring', 'at': [56, 82], 'radius': 448, 'count': 6,
       'altar': [192, 128, 96], 'title': "Danulf the Faery King",
       'condition': {'qbit': 'faery_wand'}, 'once': True,
       'effects': [{'gold': 1500},
                   msg('Danulf the Faery King: "You have returned my Wand of Faery Magic! Now peace can be restored to '
                       'the forest. Please accept this gold as a reward."')],
       'else_effects': [msg('Danulf the Faery King: "A terrible thing has happened. My Wand of Faery Magic has been '
                            'stolen by the Sprites. Now that the Sprites possess my Wand they are crazed with power, '
                            'attacking anyone in the forest. If you return my Wand I will reward you handsomely."')]})
    if IN_WORLD:
        # Danulf himself (A4's NPC 4154) stands by his altar and talks (A3's Q-C17 topics); the ring is his place
        _ring = structures[-1]
        for _k in ('condition', 'once', 'effects', 'else_effects'):
            _ring.pop(_k)
    S(deco('thing:sprite_eggs', 'mushrm05', (49.2, 87.3), title='Sprite eggs', effects=hook('q-c17.nest'))
      if IN_WORLD else
      deco('thing:sprite_eggs', 'mushrm05', (49.2, 87.3), title='Sprite eggs', once=True,
           effects=[{'qbit': 'sprite_eggs'}, {'qbit': 'faery_wand'}, {'add': {'var': 'Experience', 'value': 2000}},
                    msg('You have discovered a hollow full of blue speckled Sprite eggs. You ruin the nesting places '
                        'and crush the eggs. Among them lies a slim wand of white wood: Danulf\'s Wand of Faery Magic. '
                        '(+2,000 experience)')]))
    S({'id': 'thing:sage_fountain', 'kind': 'fountain', 'at': [70, 86], 'title': "Sage's Fountain",
       'condition': {'not': {'map_var': 'sage_drunk'}},
       'effects': [{'set': {'var': {'map_var': 'sage_drunk'}, 'value': 1}},
                   {'add': {'var': 'BaseIntellect', 'value': 2}}, {'text': '+2 Intellect (permanent)'}],
       'else_effects': [{'text': 'The water is cool and refreshing.'}]})
    S(K.well('thing:chapel_well', (77.2, 78.0), roofed=True, title='Holy well'))
    structures[-1]['effects'] = [{'add': {'var': 'HP', 'value': 25}}, {'text': '+25 Hit points'}]
    for i, at in enumerate([(82.6, 77.2), (83.4, 78.1), (82.4, 78.9), (84.2, 77.4), (83.6, 79.4)]):
        S(deco('thing:grave_%d' % (i + 1), 'rock65', at, title='Grave',
               effects=[{'text': 'An elven grave, its name worn smooth.'}]))
    for i, (d, at) in enumerate([('dec24x', (60.4, 85.6)), ('7dec18', (61.1, 86.2)), ('7dec20', (59.8, 86.4)),
                                 ('stump5a', (61.6, 85.2))]):
        S(deco('thing:hunters_camp_%d' % (i + 1), d, at))
    # ---------------------------------------------------------------- the dark end and the rim
    S({'id': 'thing:fouled_well', 'kind': 'well', 'at': [70.6, 98.2], 'title': 'Well',
       'effects': [{'damage': {'amount': 10, 'kind': 'body', 'who': 'all'}},
                   {'text': 'The water is black and stinks of the bog. You are poisoned!'}]})
    S({'id': 'thing:cairn_chest', 'kind': 'chest', 'at': [52.4, 96.4], 'title': 'Chest',
       'chest': {'level': 1, 'random_items': 2}})
    for i, (d, at) in enumerate([('7rock08', (51.6, 95.8)), ('7rock09', (53.1, 95.9)), ('7rock08', (52.2, 97.1)),
                                 ('7dec20', (51.5, 96.9))]):
        S(deco('thing:cairn_%d' % (i + 1), d, at))
    if not IN_WORLD:     # in the world Ligono is A4's NPC 4155 on the cliff top (actors below)
      S(deco('thing:ligono', 'ped03', (27.0, 102.6), title='Ligono the Spirit',
           condition={'qbit': 'ligono_skull'}, once=True,
           effects=[{'add': {'var': 'Experience', 'value': 4000}},
                    msg('Ligono the Spirit: "My skull! Thank you! Already I can feel my tie to this world fading. '
                        'Listen to the sound of the surf for your spell." (+4,000 experience)')],
           else_effects=[msg('Ligono the Spirit, a pale shape in the spray below the rim: "I hate the surf. I have been '
                             'trapped here since I died, crashing forward and pulling back. If you bring my skull and '
                             'cast it into the surf here, I will be set free. I think my skull was pulled by the '
                             'currents and lies near the edge of the world, to the east."')]))
    # D-90 (A5 s30, merge point 42): in the world Ligono's skull is a 3D ground item (12311, sketch `items`, below), the
    # click and the 7dec20 decoration gone
    if not IN_WORLD:
     S(deco('thing:ligono_skull', '7dec20', (96.6, 102.8), title='Skull',
           condition={'not': {'qbit': 'ligono_skull'}},
           effects=[{'qbit': 'ligono_skull'}, msg("Wedged among the rocks at the world's edge: a skull, still wet with "
                                                 "spray. Ligono's, surely.")],
           else_effects=[{'text': 'Only rocks and spray.'}]))
    # ---------------------------------------------------------------- the farmland
    for cid, (x, y) in (('ne', (88, 24)), ('nw', (46, 22))):
        S({'id': 'thing:camp_%s_tent' % cid, 'kind': 'tent', 'at': [x - 1.2, y - 0.6], 'size': [768, 640],
           'height': 352, 'open': True, 'title': "Rangers' tent"})
        S(deco('thing:camp_%s_fire' % cid, 'cmpfyr00', (x + 0.6, y + 0.7), title='Campfire'))
        S({'id': 'thing:camp_%s_chest' % cid, 'kind': 'chest', 'at': [x + 1.6, y - 0.4], 'title': 'Chest',
           'chest': {'level': 1, 'random_items': 2}})
        S(deco('thing:camp_%s_bones' % cid, 'dec05', (x - 0.4, y + 1.2)))
    S({'id': 'thing:shrine_electricity', 'kind': 'building', 'at': [95, 30], 'size': [2, 2], 'kit': 'stone',
       'title': 'Shrine of Electricity', 'door': 'none',
       'parts': [{'id': 's', 'at': [256, 256], 'size': [512, 512], 'wall_height': 352, 'posts': 48, 'roof': 'cone',
                  'roof_pitch': 50, 'windows': 'none', 'title': 'Shrine of Electricity',
                  'condition': {'not': {'map_var': 'shrine_used'}},
                  'effects': [{'set': {'var': {'map_var': 'shrine_used'}, 'value': 1}},
                              {'add': {'var': 'AirResistance', 'value': 5}}, {'text': '+5 Air resistance (permanent)'}],
                  'else_effects': [{'text': 'No one seems to be listening.'}]}]})
    S(K.well('thing:farm_well', (59.8, 29.0)))
    structures[-1]['effects'] = [{'text': 'The water is cool and refreshing.'}]
    S({'id': 'thing:watchtower', 'kind': 'building', 'at': [99, 35], 'size': [2, 2], 'kit': 'castle', 'door': 'none',
       'title': 'Ruined watchtower', 'ruin': {'height': [256, 768], 'gaps': 0.3, 'thickness': 48, 'seed': 5},
       'parts': [{'id': 't', 'shape': 'round', 'at': [512, 512], 'radius': 352, 'sides': 10, 'wall_height': 768,
                  'roof': 'none', 'windows': 'none', 'textures': {'wall': 'cnb'}}]})
    S({'id': 'thing:watchtower_chest', 'kind': 'chest', 'at': [101.6, 36.4], 'title': 'Chest',
       'chest': {'level': 1, 'random_items': 2}})
    S({'id': 'thing:shore_ruin', 'kind': 'building', 'at': [33, 76.5], 'size': [2, 1.5], 'kit': 'stone',
       'door': 'none', 'title': 'Ruined cottage', 'ruin': {'height': [96, 320], 'gaps': 0.35, 'thickness': 32, 'seed': 5},
       'parts': [{'id': 'r', 'at': [64, 64], 'size': [896, 640], 'wall_height': 320, 'roof': 'none',
                  'windows': 'alternate'}]})
    S({'id': 'thing:shore_chest', 'kind': 'chest', 'at': [35.6, 77.4], 'title': 'Chest',
       'chest': {'level': 1, 'random_items': 2}})
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [24, 77.5], 'height': 768, 'title': 'Obelisk',
       'effects': hook('obelisks.x2') if IN_WORLD else [msg('Carved into the obelisk: the second word of a riddle that '
                                                            'runs across Cloudside: "THE".')]})   # A3's hook
    S(deco('thing:ogre_boulder', 'rock68', (38.2, 42.6), title='A great boulder',
           condition={'stat': {'name': 'BaseMight', 'at_least': 30}}, once=True,
           effects=[{'gold': 400}, {'text': 'You heave the boulder aside: an ogre\'s stash of coins lies under it. +400 gold'}],
           else_effects=[{'text': 'The boulder does not budge. An ogre could move it (Might 30).'}]))
    # the ogres' bridge on the west road
    S({'id': 'thing:ogre_bridge', 'kind': 'bridge', 'line': [[31.3, 40], [35.7, 40]], 'width': 512, 'rise': 96,
       'kerb': 64, 'textures': {'deck': 'trim11_32'}, 'title': "The ogres' bridge"})
    # signposts
    S({'id': 'thing:sign_east', 'kind': 'sign', 'at': [86.6, 44.6], 'height': 256,
       'arms': [{'title': 'Vertigo', 'toward': 'e'}, {'title': 'Rivercity', 'toward': 'w'},
                {'title': 'Shrine', 'toward': 'n'}]})
    S({'id': 'thing:sign_north', 'kind': 'sign', 'at': [66.6, 30.6], 'height': 256,
       'arms': [{'title': 'Castle Burlock', 'toward': 'n'}, {'title': 'Rivercity', 'toward': 's'},
                {'title': 'Farms', 'toward': 'w'}]})
    S({'id': 'thing:sign_west', 'kind': 'sign', 'at': [37.4, 39.0], 'height': 256,
       'arms': [{'title': 'Newcastle, Lifeforce Lagoon', 'toward': 'w'}, {'title': 'Rivercity', 'toward': 'e'},
                {'title': 'Ogre Lair', 'toward': 'n'}]})
    S({'id': 'thing:sign_woods', 'kind': 'sign', 'at': [65.0, 72.4], 'height': 256,
       'arms': [{'title': 'Temple of Yak', 'toward': 's'}, {'title': "Tito's Chapel", 'toward': 'e'},
                {'title': 'Rivercity', 'toward': 'n'}]})
    S({'id': 'thing:sign_lake', 'kind': 'sign', 'at': [51.5, 60.2], 'height': 224,
       'arms': [{'title': "Medin's jetty", 'toward': 'w'}, {'title': 'Rivercity', 'toward': 'e'}]})
    if IN_WORLD:
        # X3 and X4 not installed: the west and north roads end at a sign until they are (no travel, no way in)
        if not X3_LIVE:
            S({'id': 'thing:west_road_end', 'kind': 'sign', 'at': [20.6, 39.1], 'height': 224, 'width': 160,
               'title': 'Sign', 'effects': [{'text': 'The road west to Lifeforce Lagoon is flooded. Turn back.'}],
               'notes': 'X3 is not built: the west edge has no travel until it is.'})
        if not X4_LIVE:
            S({'id': 'thing:north_road_end', 'kind': 'sign', 'at': [67.1, 20.6], 'height': 224, 'width': 160,
               'title': 'Sign', 'effects': [{'text': 'Bridge out. The road north to Castle Burlock is closed.'}],
               'notes': 'X4 is not built: the north edge has no travel until it is.'})
        # Captain Nystor's ship at his pier (S8g: a taken model turns): Erathia's Lady Catherine, turned to lie along
        # the east-west river, moored on the pier's east side
        # The model comes from MM7's Erathia (`from.world`, A1's merge point 6).
        if SHIP_WORD:
            S({'id': 'thing:nystor_ship', 'kind': 'model',
               'from': {'world': 'mm7', 'map': '7out03.odm', 'models': ['Boat 201_S', 'Boat 201_S_1', 'Boat 201_S_2', 'Boat 201_S_3',
                                                         'Boat 201_S_4', 'Boat 2f01 Mastprt1_SBoat 2f01 M',
                                                         'Boat 2g01 Mastprt2_SBoat 2g01 M',
                                                         'Boat 2h01 FrntMast_SBoat 2h01 F']},
               'at': list(SHIP_AT), 'turn': 90, 'raise': 560,   # Erathia's keel at its sea (0); the river is 576
               # MM7's hull boards and trim lie back to back, two trims on each other: one face kept of each (P3)
               'drop_overlaps': True,
               'title': "Captain Nystor's ship", 'house': HOUSE_XEEN[486][0]})
    # ---------------------------------------------------------------- actors
    actors = []
    # Rivercity's people: D-96's villagers (villagers.yml palette, villagers_spots.yml spots; they replace F20's
    # earlier 18 townsfolk of four MM7 kinds, Vertigo's own)
    actors += V.slots(18)     # the 18 earlier townsfolk's places in the list (actor indices stay)
    for (x, y) in [(63.2, 47.9), (64.8, 47.9), (63.2, 58.1), (64.8, 58.1), (82.6, 43.8), (52.9, 43.2),
                   (68.3, 60.9), (62.0, 38.5)]:
        actors.append({'monster': '404', 'at': [x, y], 'spread': 0, 'group': 51})
    for i, (x, y) in enumerate([(88, 24), (46, 22)]):
        actors.append({'monster': W_('202'), 'at': [x, y + 1.6], 'count': 3, 'spread': 1.0, 'group': 60 + i,
                       'hostile': True})
        actors.append({'monster': W_('203'), 'at': [x + 1.2, y + 1.0], 'count': 2, 'spread': 0.8, 'group': 60 + i,
                       'hostile': True})
    # D-15/D-133 (2026-11-24, check_d85 first fight): the lair's ogres and the temple's Killer Sprites stood 475-1,780
    # from the XD-27 and XD-06 arrivals and their move-ins; each group now stands at the nearest spot 2,000 plus its
    # spread from both, with the land (or the temple) between: the ogres on the rise south of the lair's camp, on its
    # approach; three sprites behind the temple's north-west corner (and 5,888 plus spread from NPC 4154, D-85), two
    # round its south-east corner
    actors.append({'monster': W_('594'), 'at': [21.45, 34.4], 'count': 1, 'spread': 0, 'group': 62, 'hostile': True})
    actors.append({'monster': W_('593'), 'at': [23.1, 35.45], 'count': 2, 'spread': 0.8, 'group': 62, 'hostile': True})
    actors.append({'monster': W_('98'), 'at': [57.5, 95.65], 'count': 3, 'spread': 1.0, 'group': 63, 'hostile': True})
    actors.append({'monster': W_('98'), 'at': [66.6, 101.6], 'count': 2, 'spread': 0.8, 'group': 63, 'hostile': True})
    # D-54: the lake dragons further out on the lake, each held to its home by a leash; every leash circle's nearest
    # point is at least 5,888 (Ice Blast's 5,120 + 768) from X9's and X8's fall landings and Darzog's door
    for i, (at, leash) in enumerate(LAKE_DRAGONS):
        actors.append({'monster': W_('192'), 'at': list(at), 'count': 1, 'spread': 0, 'group': 80, 'hostile': True,
                       'leash': leash, 'notes': "One of Medin's three lake beasts."})
    for i, (kind, at) in enumerate([('593', (30, 20)), ('97', (84, 69)), ('202', (100, 22)), ('97', (42, 90))]):
        kind = W_('ogre_wanderer' if kind == '593' else kind) if IN_WORLD else kind
        actors.append({'monster': kind, 'at': list(at), 'count': 1, 'spread': 0, 'group': 70 + i, 'hostile': True})
    if IN_WORLD:
        for npc, kind, (x, y) in NPC_ACTORS:
            # Ligono (4155) in a group of his own: freed (q-c19.done) he leaves the surf for Olympus (A3)
            actors.append({'monster': kind, 'npc': npc, 'at': [x, y], 'spread': 0,
                           'group': LIGONO_GROUP if npc == 4155 else 52})
        # Q-C2: the sorceresses' two hired apprentices, out of their house when the strongbox is opened
        for at in ((72.3, 56.0), (72.7, 55.5)):
            actors.append({'monster': '11184', 'at': list(at), 'spread': 0, 'group': 54, 'hostile': True,
                           'hidden': True, 'notes': "Q-C2: the sorceresses' apprentice, shown by the strongbox."})
    # Hostility pass (2026-11-16): MMerge's hostile.txt has MM7's Archers (202-204) friendly to the party, so the Archers
    # of slot 2's encounter areas left it alone while the placed ranger camps (`hostile: true`) shot at it; the family
    # is made the party's foe by kind. No two of the map's hostile kinds are set on each other by the table.
    relations = [{'of': [202, 203, 204], 'toward': 'party', 'relation': 'hostile'}]
    if IN_WORLD:
        # the world's relations.yml (A2) holds the families' hostility; Ligono's figure (MM7's Ghost, 268-270, no
        # other ghost on the map) is kept peaceful
        relations = [{'of': [268, 269, 270], 'toward': 'party', 'relation': 'friendly'}]
    events = ([
        {'id': 'evt:ligono_freed', 'trigger': 'load', 'condition': {'qbit': 112380},
         'effects': [{'hide_actors': LIGONO_GROUP}], 'else_effects': [{'show_actors': LIGONO_GROUP}],
         'notes': "Q-C19 (A3): freed, Ligono leaves the surf for Olympus (q-c19.done, 112380)."}] if IN_WORLD else []) + [
        {'id': 'evt:lake_beasts', 'trigger': 'timer', 'every': 5, 'once': True, 'condition': {'kills': {'group': 80}},
         'effects': [{'qbit': 'lake_beasts_slain'},
                     msg('The last of the lake beasts sinks beneath the waves of Lake Darzog. Medin the Fisherman will '
                         'want to hear of it.')],
         'notes': 'Q-C13: when the three dragons are dead, Medin\'s boat runs to the island.'},
    ]
    # ---------------------------------------------------------------- scatter and ground
    scatter = []
    def sc(sid, deco_, count, poly=None, circle=None, clusters=None, spacing=None, line=None, closed=None):
        e = {'id': sid, 'decoration': deco_, 'count': count}
        if poly: e['polygon'] = poly
        if circle: e['circle'] = circle
        if line: e['line'] = line
        if closed: e['closed'] = True
        if clusters: e['clusters'] = clusters
        if spacing: e['spacing'] = spacing
        scatter.append(e)
    def stand(sid, poly, kinds_, count, spacing, close=0.1, close_at=1.0):
        e = {'id': sid, 'count': count, 'polygon': poly, 'spacing': spacing, 'close_share': close,
             'close_spacing': close_at, 'edge_thin': {'width': 3, 'keep': 0.35}, 'spacing_group': 'trees'}
        if len(kinds_) == 1:
            e['decoration'] = list(kinds_)[0]
        else:
            e['kinds'] = dict(kinds_)
        scatter.append(e)
    WOODS = [[38, 70], [98, 70], [98, 91], [80, 91], [72, 92], [52, 92], [38, 91]]
    DARK = [[46, 91], [80, 91], [80, 103], [46, 103]]
    NW_HILLS = [[19, 19], [40, 19], [40, 37], [19, 37]]
    stand('scatter:woods', WOODS, {'7tree25': 5, '7tree07': 3, '7tree19': 2}, int(0.13 * K.poly_area(WOODS)), 1.45)
    sc('scatter:woods_bushes', 'bush03', 80, WOODS, clusters=20)
    sc('scatter:woods_flowers', 'flower05', 40, WOODS, clusters=12)
    sc('scatter:woods_flowers', 'flower03', 25, WOODS, clusters=8)
    for i, (cx, cy) in enumerate([(56, 82), (44, 80), (74, 84), (66, 77)]):
        sc('scatter:fairy_rings', ['mushrm01', 'mushrm02', 'mushrm03', 'mushrm05'][i], 9 if i else 12,
           line=[[cx + 1.4 * math.cos(a * math.pi / 4), cy + 1.4 * math.sin(a * math.pi / 4)] for a in range(8)],
           closed=True)
    stand('scatter:dark_trees', DARK, {'tree41': 3, 'tree42': 2, 'swptree1': 1}, int(0.11 * K.poly_area(DARK)), 1.6)
    sc('scatter:dark_bones', '7dec18', 16, DARK, clusters=6)
    sc('scatter:dark_rocks', '7rock08', 12, DARK, clusters=5)
    stand('scatter:hill_trees', NW_HILLS, {'7tree22': 3, '7tree16': 2}, 40, 2.0)
    sc('scatter:hill_rocks', '7rock09', 22, NW_HILLS, clusters=8)
    sc('scatter:hill_rocks', '7rock08', 16, NW_HILLS, clusters=6)
    # the island's trees round the tower, not against it (a ring as four stands; the jetty side open)
    for poly, n in (([[26, 52], [36, 52], [36, 55], [26, 55]], 5), ([[26, 61], [36, 61], [36, 64], [26, 64]], 5),
                    ([[25, 55], [28, 55], [28, 61], [25, 61]], 3), ([[34, 55], [37, 55], [37, 57], [34, 57]], 1)):
        stand('scatter:island_trees', poly, {'7tree25': 2, '7tree19': 1}, n, 1.4)
    # the world rim's lip: boulders and broken rock along the cliff's edge (X1's rim has them by its falls)
    sc('scatter:rim_rocks', '7rock08', 22, line=[[20, 103.5], [108, 103.5]])
    sc('scatter:rim_rocks', '7rock09', 18, line=[[22, 102.8], [106, 102.8]])
    for i, at in enumerate([(30, 103.2), (45, 103.0), (58, 103.3), (73, 103.1), (84, 103.2), (101, 103.0)]):
        S(deco('thing:rim_boulder_%d' % (i + 1), 'rock26' if i % 2 else 'rock12', at))
    SHORE = [[19, 64], [48, 64], [48, 79], [19, 79]]
    stand('scatter:shore_trees', SHORE, {'7tree19': 2, '7tree28': 2}, 30, 1.8)
    sc('scatter:shore_plants', 'plant02', 30, SHORE, clusters=10)
    FARM_W = [[40, 19], [62, 19], [62, 33], [40, 33]]
    FARM_E = [[68, 19], [109, 19], [109, 33], [68, 33]]
    stand('scatter:farm_trees', FARM_W, {'7tree19': 2, '7tree28': 1}, 16, 2.4)
    stand('scatter:farm_trees', FARM_E, {'7tree19': 2, '7tree28': 1}, 26, 2.4)
    EAST = [[86, 34], [109, 34], [109, 66], [86, 66]]
    stand('scatter:east_trees', EAST, {'7tree19': 2, '7tree28': 2, '7tree25': 1}, 34, 2.0)
    sc('scatter:east_flowers', 'flower04', 24, EAST, clusters=8)
    sc('scatter:east_flowers', 'flower08', 18, EAST, clusters=6)
    # fields: hedges and crop rows north of the town (TOWN_FEEL's farm belt)
    for (x0, y0, x1, y1) in ((52, 21, 60, 25), (68, 20, 75, 26), (80, 27, 87, 31), (42, 27, 48, 31)):
        sc('scatter:hedges', 'bush02', max(5, int((x1 - x0) * 0.9)), line=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
        sc('scatter:crops', 'flower02', int((x1 - x0) * (y1 - y0) * 0.3),
           [[x0 + 0.4, y0 + 0.4], [x1 - 0.4, y0 + 0.4], [x1 - 0.4, y1 - 0.4], [x0 + 0.4, y1 - 0.4]])
    sc('scatter:orchard', 'tree37', 7, line=[[69, 28.5], [75, 28.5]])
    sc('scatter:orchard', 'tree37', 6, line=[[56, 32.5], [61, 32.5]])
    # town: trees in yards and by the squares, flower beds (TOWN_FEEL 6: 0.008-0.13 trees a cell)
    for i, at in enumerate([(55.75, 39.6), (53.0, 40), (58.0, 40.2), (71.9, 40), (78.3, 41.5), (60.5, 40.2),
                            (52.8, 46), (77.8, 46.5), (52.8, 59.4), (78.6, 59.4), (62.6, 66), (69.3, 66),
                            (52.8, 63.5)]):
        scatter.append({'id': 'scatter:town_trees', 'decoration': ['7tree19', '7tree28', 'tree37'][i % 3], 'count': 1,
                        'circle': {'at': list(at), 'r': 0.2}})
    sc('scatter:town_flowers', 'flower04', 3, line=[[60.8, 58.0], [62.6, 58.0]])
    sc('scatter:town_flowers', 'flower04', 3, line=[[65.4, 58.0], [67.2, 58.0]])
    # the world: 5 clumps (6 put one before the bank's door; DRESSING.md, nothing before a door)
    sc('scatter:town_flowers', 'flower11', 12, [[52, 35], [80, 35], [80, 48], [52, 48]], clusters=5 if IN_WORLD else 6)
    sc('scatter:town_flowers', 'flower08', 10, [[52, 58], [80, 58], [80, 68], [52, 68]], clusters=5)
    # 2026-11-16: the land beyond the party's square (cells 0-19 and 109-128, the rim's ridges) carries trees and rocks
    # to the map's edge, as shipped maps' rims do (Harmondale 61 decorations out there, X1 202), so that the woods do
    # not stop at the line where the party stops. Not on the travel roads' valleys (north x 62-70, west y 37-43, east
    # y 42-57) or the north river's gorge; nothing south of the world rim. No thinning at the polygons' edges: the
    # stands inside run on into these.
    def rim_stand(sid, poly, kinds_, per_100, spacing, clusters=None):
        e = {'id': sid, 'count': int(per_100 * K.poly_area(poly) / 100.0), 'polygon': poly, 'spacing': spacing,
             'spacing_group': 'trees'}
        if clusters:
            e['clusters'] = clusters
        e['kinds'] = dict(kinds_)
        scatter.append(e)
    HILL = {'7tree22': 3, '7tree16': 2, '7tree19': 1}
    FARM = {'7tree19': 2, '7tree28': 2, '7tree22': 1}
    FAIRY = {'7tree25': 3, '7tree07': 2, '7tree19': 1}
    RIM_BANDS = [
        ('scatter:rim_trees_nw', [[0, 0], [27.5, 0], [25.5, 18.5], [0, 18.5]], HILL, 6.0),
        ('scatter:rim_trees_n', [[32.5, 0], [61, 0], [61, 18.5], [31, 18.5]], HILL, 5.0),
        ('scatter:rim_trees_ne', [[71, 0], [128, 0], [128, 18.5], [71, 18.5]], FARM, 4.5),
        ('scatter:rim_trees_wn', [[0, 18.5], [18.5, 18.5], [18.5, 36.5], [0, 36.5]], HILL, 6.0),
        ('scatter:rim_trees_w', [[0, 43.5], [18.5, 43.5], [18.5, 80], [0, 80]], HILL, 5.0),
        ('scatter:rim_trees_sw', [[0, 80], [18.5, 80], [18.5, 103], [0, 103]], FAIRY, 7.0),
        ('scatter:rim_trees_en', [[109.5, 18.5], [128, 18.5], [128, 41], [109.5, 41]], FARM, 5.0),
        ('scatter:rim_trees_e', [[109.5, 57], [128, 57], [128, 80], [109.5, 80]], FARM, 5.0),
        ('scatter:rim_trees_se', [[109.5, 80], [128, 80], [128, 103], [109.5, 103]], FAIRY, 7.0),
    ]
    for sid, poly, kinds_, per_100 in RIM_BANDS:
        rim_stand(sid, poly, kinds_, per_100, 1.6)
    for sid, poly, _, _ in RIM_BANDS:
        n = max(4, int(0.8 * K.poly_area(poly) / 100.0))
        scatter.append({'id': sid.replace('trees', 'rocks'), 'decoration': '7rock09', 'count': n, 'polygon': poly,
                        'clusters': max(2, n // 4), 'steep': True})
        scatter.append({'id': sid.replace('trees', 'boulders'), 'decoration': '7rock08', 'count': max(3, n // 2),
                        'polygon': poly, 'clusters': max(2, n // 6), 'steep': True})
    # 2026-11-16, the south (the lead: "the south is still bare"): the land between the woods and the world rim west
    # and east of the dark end was bare grass to the cliff (the shore and the woods' stands stopped at y 79 and 91).
    # Windswept heath: trees thinning toward the rim, shrubs and rocks to the lip, clear of Ligono's rock (27, 102.6)
    # and his skull (96.6, 102.8); a few sea stacks below the cliff.
    COAST_W = [[19, 79], [38, 79], [38, 91], [46, 91], [46, 100], [19, 100]]
    COAST_E = [[98, 66], [109, 66], [109, 101], [80, 101], [80, 91], [98, 91]]
    LIPS = [[[19, 99.5], [25, 99.5], [25, 103.6], [19, 103.6]], [[29, 99.5], [46, 99.5], [46, 103.6], [29, 103.6]],
            [[46, 102], [57, 102], [57, 103.6], [46, 103.6]], [[68, 102], [80, 102], [80, 103.6], [68, 103.6]],
            [[80, 100], [95, 100], [95, 103.6], [80, 103.6]], [[98.5, 100], [109, 100], [109, 103.6], [98.5, 103.6]]]
    HEATH = {'7tree19': 2, '7tree28': 2, '7tree22': 2, '7tree25': 1}
    rim_stand('scatter:coast_trees_w', COAST_W, HEATH, 5.0, 1.6, clusters=14)
    rim_stand('scatter:coast_trees_e', COAST_E, HEATH, 3.9, 1.6, clusters=14)
    scatter[-1]['steep'] = True        # the east ridge's foot
    for i, poly in enumerate(LIPS):
        rim_stand('scatter:lip_trees', poly, {'7tree22': 1, '7tree19': 1, '7tree28': 1}, 16.0, 1.1)
        scatter[-1]['steep'] = True
    for sid, poly in (('w', COAST_W), ('e', COAST_E)):
        a = K.poly_area(poly)
        sc('scatter:coast_bushes', 'bush03', int(a * 0.05), poly, clusters=int(a * 0.012))
        scatter[-1]['steep'] = True
        sc('scatter:coast_bushes', 'bush02', int(a * 0.03), poly, clusters=int(a * 0.008))
        sc('scatter:coast_plants', 'plant02', int(a * 0.025), poly, clusters=int(a * 0.008))
        sc('scatter:coast_rocks', '7rock09', int(a * 0.02), poly, clusters=int(a * 0.006))
        scatter[-1]['steep'] = True
    for poly in LIPS:
        sc('scatter:lip_rocks', '7rock08', max(3, int(K.poly_area(poly) * 0.12)), poly, clusters=3)
        scatter[-1]['steep'] = True
        a = K.poly_area(poly)
        sc('scatter:lip_bushes', 'bush03', max(2, int(a * 0.25)), poly, clusters=max(2, int(a * 0.06)))
        scatter[-1]['steep'] = True
        sc('scatter:lip_bushes', 'bush03', max(2, int(a * 0.12)), poly, clusters=max(2, int(a * 0.04)))
        scatter[-1]['steep'] = True
    # groves on the lip where the dark end's dead trees give way to the heath, and by Ligono's rock
    for i, (cx, cy) in enumerate([(81, 102), (66.5, 98.5), (33, 101.5), (21.5, 101.5), (104, 102)]):
        scatter.append({'id': 'scatter:lip_groves', 'kinds': {'7tree22': 2, '7tree19': 1, '7tree28': 1}, 'count': 5,
                        'circle': {'at': [cx, cy], 'r': 1.8}, 'spacing': 0.9, 'steep': True})
    scatter.append({'id': 'scatter:sea_stacks', 'decoration': 'rock26', 'count': 10, 'on': 'water',
                    'polygon': [[6, 106], [122, 106], [122, 112], [6, 112]]})
    scatter.append({'id': 'scatter:sea_stacks', 'decoration': 'rock12', 'count': 8, 'on': 'water',
                    'polygon': [[6, 106], [122, 106], [122, 112], [6, 112]]})
    # river and lake banks
    sc('scatter:bank_plants', 'plant02', 20, [[83, 47], [109, 47], [109, 57], [83, 57]], clusters=8)
    sc('scatter:bank_rocks', '7rock09', 10, [[83, 47], [109, 47], [109, 57], [83, 57]], clusters=5)
    ground = [
        {'material': 'grass_meadow', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'meadow, farmland and woods floor'},
        {'material': 'swamp', 'polygon': [[48, 92], [78, 92], [78, 102], [48, 102]],
         'notes': "the dark south end's bog"},
        {'material': 'swamp', 'polygon': [[20, 70], [30, 70], [30, 76], [20, 76]], 'notes': "the lake's reedy south-west"},
        {'material': 'soil', 'polygon': BRIDGE_SQ, 'notes': 'Bridge Square'},
        {'material': 'soil', 'polygon': SOUTH_SQ, 'notes': 'the South Square'},
        {'material': 'soil', 'polygon': [[53, 49], [77, 49], [77, 51], [53, 51]], 'notes': 'the north quay'},
        {'material': 'soil', 'polygon': [[53, 54], [81, 54], [81, 57], [53, 57]], 'notes': 'the south quay'},
        {'material': 'soil', 'polygon': [[59, 96], [65, 96], [65, 99], [59, 99]], 'notes': "the temple's forecourt"},
        {'material': 'soil', 'polygon': [[21, 30], [26, 30], [26, 33], [21, 33]], 'notes': "the ogres' trodden ground"},
    ]
    for line in LANES:
        ground.append({'material': 'soil', 'line': line, 'width': 2, 'notes': 'a lane or the promenade'})
    for (x0, y0, x1, y1) in ((52, 21, 60, 25), (68, 20, 75, 26), (80, 27, 87, 31), (42, 27, 48, 31)):
        ground.append({'material': 'soil', 'polygon': [[x0 + 1, y0 + 1], [x1 - 1, y0 + 1], [x1 - 1, y1 - 1],
                                                       [x0 + 1, y1 - 1]], 'notes': 'a ploughed field'})
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('X2 Rivercity and Lake Darzog, L3 sketch written by output/studio_cal/x2/tools/gen.py. Cells [x, y], '
                  'x east, y south. Heights are map units above the water below the rim (0): the plateau and the '
                  'town at 1024, the quays at 640, the river and the lake at 576, the island at 768, the ogres\' '
                  'hills to about 2,000, the rim cliff along y 104.'),
        'frame': {'playable': [19, 19, 90, 90],
                  'edges': [{'side': 'east', 'span': [42, 50], 'neighbour': 'edge:east'},
                            {'side': 'west', 'span': [36, 44], 'neighbour': 'edge:west'},
                            {'side': 'north', 'span': [62, 70], 'neighbour': 'edge:north'}],
                  'edge': {'height': 1600, 'east': 760, 'south': 0},
                  'rim': rim},
        'heights': heights, 'water': water, 'roads': roads, 'districts': districts, 'points': points,
        'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground, 'structures': structures,
        'actors': V.fill(actors, 'X2'), 'relations': relations + V.relations('X2'), 'events': events,
    }
    if IN_WORLD:   # D-90 (A5 s30): Ligono's skull on the ground among the rocks at the world's edge
        sketch['items'] = [{'id': 'item:ligono_skull', 'item': 12311, 'at': [96.6, 102.8]}]
    atmosphere = {'format': 0, 'notes': "World default sky and weather ('fair' to 'cloudy' by the world's chances)."}

    def dump(folder, name, data):
        if name == 'sketch.yml':   # AU's outdoor beds (A5, 2026-11-21; level_generation/projects/xeen/common/beds)
            sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common/beds')
            import beds as _beds
            data = _beds.with_beds(data, 'x2')
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)
    if IN_WORLD:
        # X3 and X4 are not built: the west and north edges lead nowhere until they are (A5 lane file, step 3); their
        # ways in go too (an arrival without a neighbour became the party start on X1); signs close the two roads.
        gone = tuple(e for e, live in (('edge:west', X3_LIVE), ('edge:north', X4_LIVE)) if not live)
        project['neighbours'] = [n for n in project['neighbours'] if n['id'] not in gone]
        project['map_stats'].pop('reference', None)
        project['map_stats']['continent'] = 6   # Cloudside (worlds/xeen continent_settings), merge point 3
        plan['entrances'] = [e for e in plan['entrances'] if e.get('neighbour') not in gone]
        gone_in = [p for p, live in (('entrance:west_road', X3_LIVE), ('entrance:north_road', X4_LIVE)) if not live]
        sketch['points'] = [q for q in sketch['points'] if q['id'] not in gone_in]
        sketch['frame']['edges'] = [e for e in sketch['frame']['edges'] if e['neighbour'] not in gone]
    # F2/F8 (2026-11-21) + F16 (A5 s29, 2026-11-22): wing doors as double doors, the Ogre Lair's mouth as wide as
    # its rim, the entrance window's trans.txt lines
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import house_doors as HD
    import entrance as EN
    for _note in HD.double_doors_sketch(sketch) + HD.bury_mouths_sketch(sketch) + EN.apply(sketch, 'x2'):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sketch, 'x2'):
        print('wild:', _note)
    # The classic Clouds kit (2026-11-24): Clouds of Xeen's own half-timbered walls on the map's houses
    import classic_kit as CK
    for _note in CK.apply(sketch, 'x2'):
        print(_note)
    dump(OUT, 'project.yml', project)
    dump(OUT, 'plan.yml', plan)
    dump(OUT, 'sketch.yml', sketch)
    dump(OUT, 'atmosphere.yml', atmosphere)
    # ---------------------------------------------------------------- L1 to L3: the same plan at less detail
    p3 = copy.deepcopy(plan)
    dump(os.path.join(BRIEFS, 'L3'), 'project.yml', project)
    dump(os.path.join(BRIEFS, 'L3'), 'plan.yml', p3)
    dump(os.path.join(BRIEFS, 'L3'), 'sketch.yml', sketch)
    dump(os.path.join(BRIEFS, 'L3'), 'atmosphere.yml', atmosphere)
    p2 = copy.deepcopy(plan)
    p2['level'] = 'L2'
    p2.pop('sketch')
    for s in p2['spaces']:
        s.pop('buildings', None)
    p2['landform'] = {'notes': ('A plateau at about 1,024 cut by the Great River (576) through the middle west to '
                                'east, its banks at 640; Lake Darzog in the west with a wooded island at 768; '
                                "hills to about 2,000 in the north-west with the north river's gorge; rolling "
                                'woods south ending in a cliff of 900 at the world rim (y 104).')}
    dump(os.path.join(BRIEFS, 'L2'), 'project.yml', project)
    dump(os.path.join(BRIEFS, 'L2'), 'plan.yml', p2)
    p1 = {k: copy.deepcopy(plan[k]) for k in ('format', 'pitch', 'purpose', 'mood', 'datum', 'links', 'entrances')}
    p1['level'] = 'L1'
    p1['spaces'] = [{k: v for k, v in s.items() if k in ('id', 'kind', 'name', 'purpose', 'part_of', 'population')}
                    for s in plan['spaces']]
    p1['diagram'] = {'text': DIAGRAM}
    dump(os.path.join(BRIEFS, 'L1'), 'project.yml', project)
    dump(os.path.join(BRIEFS, 'L1'), 'plan.yml', p1)

DIAGRAM = '''\
 N   ogres' hills ^^^ [OGRE LAIR]      farmland  ranger camp *     ranger camp *        X4 north road
     north river |    boulders         fields, farmsteads, orchards     Shrine of Electricity o
 X3 ==west road==|=ogre bridge=====[ RIVERCITY north bank: tavern, smith, bank, magic ]===river road==> X1
     Lake Darzog  ~~~ (island: DARZOG'S TOWER) ~~~~~~~ GREAT RIVER under the GREAT BRIDGE ~~~~~~~~~~~~~>
     Medin's jetty, Crodo's bottle   [ south bank: guilds, skill row, temple; dock; ROBBERS' DEN under the bridge ]
     obelisk, shore ruin        fairy woods: Danulf's ring, Tito's chapel, Sage's Fountain, sprite eggs
                                dark south end: [TEMPLE OF YAK], fouled well, cairn
 S   ===================== the world rim (cliff); Ligono in the surf; his skull to the east =================
'''

# Where Medin's boat lands on the island and back on his jetty; Nystor's ride lands on X1's creek bank (Vertigo's
# south bank, by the town bridge: X1 cell [50, 55.2], its quay side)
ISLAND_LANDING = (*W(35.0, 60.5), ISLE_H)
MEDIN_LANDING = (*W(47.0, 59.6), BANK)
VERTIGO_BANK = (-7168, 4506, 640)
LAIR_FLOOR = 1216
DOOR_NOTES = {
    'xd21': "XD-21 Robbers' Den. Door on X2: the dark face at X 1280, Y 3772, Z 640 (cells [66.5, 56.63]) in the south quay's wall beside the great bridge's south end, facing north. Outside arrival for the dungeon's exit: X 1280, Y 4172, Z 640, facing north (direction 90; MoveToMap 512). DOORS.md.",
    'xd27': "XD-27 Ogre Lair. Door on X2: the cave mouth's dark face at X -20992, Y 17555, Z 1216 (cells [23, 29.71]) in the bluff west of the north river, facing south. Outside arrival: X -20992, Y 17155, Z 1248, facing south (direction 270; MoveToMap 1536). DOORS.md.",
    'xd06': "XD-06 Temple of Yak (moved from X1). Door on X2: X -1024, Y -18240, Z 1088 (cells [62, 99.63]) in the temple front in the fairy woods' dark south end, facing north; needs the Yak Stone (qbit 110101). Outside arrival: X -1024, Y -17840, Z 1053, facing north (direction 90; MoveToMap 512). DOORS.md.",
    'xd12': "XD-12 Darzog's Tower. Door on X2: X -16031, Y 3014, Z 768 (cells [32.69, 58.11]) on the east side of the tower on Lake Darzog's island, facing east; needs the Skeleton Key (stand-in item 1461). Outside arrival: X -15631, Y 3014, Z 768, facing east (direction 0; MoveToMap 0). DOORS.md.",
}

if __name__ == '__main__':
    build()
