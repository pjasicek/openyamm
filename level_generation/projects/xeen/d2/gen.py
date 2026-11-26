#!/usr/bin/env python3
"""D2 Sprite Forest and Ogre Pass: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml) and the L2
and L3 briefs beside it (L1 is the approved mock-up of 2026-11-20 and stays as it is).

The design is the approved L1 (devdocs/xeen/briefs/d2/L1, board level_generation/xeen_art/phase3/d2/) with the
decider's changes D-23: the south rim at y 104 (the Brink and Sprite Falls on it), the Glimmerbrook rising and falling
inside the map; the treehouses as tapered many-sided BModel trunks with root buttresses, round foot doors with lanterns,
decks and rope walks, shipped crowns on top, only Sharla's stair walkable (to the chest's deck); the great tree (the
Temple of Bark's door in its trunk) the same at 1,500 across under S's crown (xeen_greatcrown) sunk into its top; Graalg's 22 pass ogres hostile at load, Graalg and his two Brutes (A2's 11064,
11065) peaceful at the parley fire until q-d11.hostile or a fort burned (D-12.3); the forts swapped to charred ruins on
q-d11.west_burned / east_burned; the wild sprites the Darkside tiers (slot 3), the eight village sprites X2's rows.
World: xeen. Houses: A4's source/towns/d2.yml. Hooks: A3's quest files (`map: D2`). Rows: A2's.
The project files are this script's output: edit here and run ../v.sh, never the files.
Coordinates: terrain cells [x, y], x east, y south from the north-west corner; X = (x - 64) * 512, Y = (64 - y) * 512.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import math
import os
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml
import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kit as K

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/d2'
OUT = os.path.join(BRIEFS, 'L4')
STEM = 'xeen_d2'
WORLD = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/worlds/xeen')
XEEN_SOURCE = os.path.join(WORLD, 'source')

def live(stem, env):
    """A neighbour or a dungeon is live when its map is installed in the world (or the env override says so)."""
    return os.path.exists(os.path.join(WORLD, 'maps', stem)) or os.environ.get(env) == '1'

# D1 Castleview Vale (west, the road at y 60) and D3 Sandcaster (east, the caravan road at y 44): each edge is live only
# when the neighbour is installed; until then the road ends at a sign and the edge has no arrival (X5's X3_LIVE).
D1_LIVE = live('xeen_d1.odm', 'D2_D1_LIVE')
D3_LIVE = live('xeen_d3.odm', 'D2_D3_LIVE')
# a dungeon door opens only when its BLV is installed AND A2's map_stats row names it (without the row the game cannot
# resolve the map's world and the move fails: DD-09 and DD-11A-C were installed at 18:45 before their rows)
_STATS = open(os.path.join(WORLD, 'data_tables/map_stats.txt')).read()
DUNGEON = {k: live('xeen_%s.blv' % k, 'D2_%s_LIVE' % k.upper()) and ('\txeen_%s.blv\t' % k in _STATS
                                                                     or os.environ.get('D2_%s_LIVE' % k.upper()) == '1')
           for k in ('dd06', 'dd09', 'dd10b', 'dd11a', 'dd11b', 'dd11c', 'dd13')}


def studio_entrances(stem):
    """The named arrivals a built map's studio sidecar lists (`oymap install` writes `name`; D-37)."""
    f = os.path.join(WORLD, 'maps', stem.replace('.blv', '.studio.yml').replace('.odm', '.studio.yml'))
    if not os.path.exists(f):
        return {}
    d = yaml.safe_load(open(f)) or {}
    return {a.get('name') or a.get('id'): a for a in (d.get('arrivals') or []) if isinstance(a, dict)}


WEST_START = (21, 60)         # the D1 arrival on the Castleview road at the forest's edge, looking east
EAST_START = (106, 44)        # the D3 arrival on the caravan road's end, looking west up to the pass

# ---------------------------------------------------------------------------------------------------------------
# A3's hooks on D2 (quest files' `hooks` with `map: D2`); every one must be used (checked at the end)
HOOKS = {}
for _f in sorted(os.listdir(os.path.join(XEEN_SOURCE, 'quests'))):
    _q = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'quests', _f)))
    for _k, _v in (_q.get('hooks') or {}).items():
        if isinstance(_v, dict) and _v.get('map') == 'D2':
            HOOKS['%s.%s' % (_f[:-4], _k)] = _v
USED = set()

def hook(name):
    assert name in HOOKS, name
    USED.add(name)
    return [{'lua': 'XeenQuests.hook("%s")' % name}]

def reads(name):
    """A hook that only reads bits (q-d10.sprites_hostile, q-d11.pass_ogres): the map's own events do its work."""
    assert name in HOOKS, name
    USED.add(name)
    return name

# A4's houses (source/towns/d2.yml): door -> house id and name
TOWN = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'towns/d2.yml')))
HOUSE = {h['door']: (h['id'], h['name']) for h in TOWN['houses']}

# A2's rows (data_tables/monster_data.txt, source/monsters.yml)
ROW = {'ogre': 11066, 'ogre_brute': 11067, 'ogre_chief': 11068, 'graalg': 11064, 'graalg_brute': 11065,
       'medusa_sprite': 11537, 'killer_sprite': 11538}
SLOT = {'wolves': 'Xeen Wolf', 'trolls': 'Xeen Troll', 'dark_sprites': 'Xeen Dark Sprite'}
QBIT = {'sprites_robbery': 113203, 'sprites_slain': 113208, 'ogres_friends': 113221, 'ogres_hostile': 113222,
        'west_fort_burned': 113224, 'east_fort_burned': 113225}
ITEMS = {'bark_key': 12342, 'south_tower_key': 12339, 'energy_disk': 12334}
G_WEST, G_EAST, G_ROAD_W, G_ROAD_E, G_GRAALG, G_VILLAGE = 1, 2, 3, 4, 5, 6
PASS_GROUPS = (G_WEST, G_EAST, G_ROAD_W, G_ROAD_E)

def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))

def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def bump(x, y, cx, cy, r, h):
    d = math.hypot(x - cx, y - cy)
    return h * (1 - smooth(d / r)) if d < r else 0.0

def dist_to_line(px, py, line):
    return min(K.seg_dist((px, py), a, b) for a, b in zip(line, line[1:]))

def msg(text):
    return {'lua': 'evt.SimpleMessage("%s")' % text.replace('\\', '\\\\').replace('"', '\\"')}

def lua_str(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')

def sign(sid, at, title, text=None, height=224, width=160, effects=None):
    return {'id': sid, 'kind': 'sign', 'at': list(at), 'height': height, 'width': width, 'title': title,
            'effects': effects if effects is not None else [msg(text)]}


def daily(key, effects, refusal, everyone=True):
    """D-70 Q2: a temporary source once a day for the party (Xeen.usedToday / Xeen.markToday), every member present
    (evt.ForPlayer(Players.All) before the effect); a second use the same day gives the refusal line only."""
    return {'condition': {'not': {'lua': 'Xeen.usedToday("%s")' % key}},
            'effects': [{'lua': 'Xeen.markToday("%s")' % key}] +
                       ([{'lua': 'evt.ForPlayer(Players.All)'}] if everyone else []) + effects,
            'else_effects': [{'text': refusal}]}

def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d

def facing_turn(dx, dy):
    """The plot `turn` (degrees clockwise from above) that turns a part's wall 0 (looking south) toward (dx, dy)."""
    t = int(round(math.degrees(math.atan2(-dx, dy)))) % 360
    return t - 360 if t > 180 else t

# ---------------------------------------------------------------------------------------------------------------
# Land. Heights are map units above the stars below the rim (water at 0).
# ---------------------------------------------------------------------------------------------------------------
RIM_Y = 104         # the world rim, south (D-23): the land ends in a cliff along y 104
BROOK = [[52, 21], [52, 26], [52, 32], [52, 40], [51, 48], [49, 56], [48, 64], [48, 70], [49, 76], [51, 82],
         [53, 88], [55, 94], [57, 100], [58, 104]]
FALLS_X = 58
CASTLEVIEW_ROAD = [[0, 60], [10, 60], [21, 60], [27, 60], [32, 60]]
LOG_BRIDGE = [[48.5, 48], [53, 48]]     # D-170: square across the brook (thing:log_bridge)
CARAVAN_WEST = [[32, 60], [37, 57], [42, 54], [47, 51], LOG_BRIDGE[0], LOG_BRIDGE[1], [56, 45.5], [61, 43], [66, 41],
                [71, 39.5], [75, 37.5], [79, 37]]
CARAVAN_EAST = [[79, 37], [83, 38], [87, 40.5], [92, 41.5], [97, 42.5], [102, 43.5], [106, 44], [116, 44], [128, 44]]
FOREST_TRACK = [[32, 60], [35, 64], [38, 67], [42, 70]]
GLADE_TRACK = [[42, 70], [46, 70], [48.5, 70], [51, 70], [54, 69], [60, 67], [66, 66], [72, 66.5], [78, 67.5],
               [83, 64], [87, 61], [90, 58]]
SOUTH_CLIMB = [[90, 58], [92, 54], [94, 50], [96, 46], [97, 42.5]]
VILLAGE_LANE = [[42, 70], [39, 72], [36, 75], [33.5, 79], [31.5, 83], [30, 86.5]]
TOWER_LANE = [[90, 58], [91, 64], [92, 70], [93.5, 75], [94.5, 78.5]]
SHRINE_PATH = [[93.5, 75], [97, 82], [100, 87], [103, 91], [103.5, 92.5]]
MINE_LANE = [[42, 54], [40, 48], [37, 42], [35, 36], [34, 32.5]]
FRUIT_LANE = [[54, 69], [55, 74], [56, 80], [57, 86], [57.5, 88.5]]
BRINK_PATH = [[57.5, 88.5], [59, 93], [60, 97], [61, 101], [61, 102.5]]
ROADS = [CASTLEVIEW_ROAD, CARAVAN_WEST, CARAVAN_EAST]
PATHS = [FOREST_TRACK, GLADE_TRACK, SOUTH_CLIMB, VILLAGE_LANE, TOWER_LANE, SHRINE_PATH, MINE_LANE, FRUIT_LANE,
         BRINK_PATH]

# control heights (cells, height): L1's points and the rises between them, interpolated (inverse distance) on the
# 4-cell grid; the ridges, terraces and cliffs below carry what the grid cannot
CONTROL = [
    # the Gemstone Range (north)
    (4, 6, 3200), (20, 8, 3700), (44, 7, 4100), (62, 9, 3800), (88, 10, 4300), (106, 10, 3600), (122, 10, 3300),
    (12, 17, 2500), (30, 16, 2600), (46, 16, 2600), (60, 16, 2500), (72, 17, 2700), (98, 18, 2700),
    (116, 19, 2500), (126, 22, 2500),
    (10, 20, 2700), (30, 21, 2800), (50, 19, 2900), (66, 21, 2900), (100, 22, 2800), (118, 23, 2700),
    # the foothills
    (8, 28, 1950), (18, 32, 1800), (26, 40, 1650), (34, 33, 1700), (44, 26, 2050), (50, 36, 1800), (58, 26, 2150),
    (66, 30, 2250), (12, 44, 1400), (22, 49, 1250), (36, 51, 1250), (44, 45, 1350), (56, 38, 1700),
    # Ogre Pass (the road, the knolls, the saddle)
    (61, 43, 1600), (66, 41, 1800), (72, 34, 2000), (71, 39.5, 1930), (79, 37, 2050), (87, 45, 2150),
    (87, 40.5, 1950), (92, 41.5, 1850), (97, 42.5, 1600), (102, 43.5, 1400), (106, 44, 1300), (116, 44, 1300),
    (126, 44, 1300),
    # the spur (crest words on top)
    (80, 25, 3000), (80, 30, 2800), (80, 43, 2700), (80, 49, 2500), (79, 55, 2000), (77, 60, 1500),
    # the east descent and the hills over it
    (100, 30, 2300), (110, 32, 1900), (120, 34, 2000), (112, 51, 1350), (122, 50, 1450),
    # the Whispering Glades
    (60, 54, 1350), (52, 50, 1250), (67, 50, 1500), (56, 60, 1150), (46, 58, 1100), (70, 57, 1450),
    # the forest's edge and the west
    (2, 60, 1000), (21, 60, 1000), (32, 60, 1000), (8, 52, 1200), (4, 72, 1100), (4, 90, 1150), (8, 100, 1000),
    (14, 66, 1020),
    # the Sprite Forest
    (42, 70, 1000), (42, 78, 1000), (29, 89, 980), (16, 88, 1000), (60, 76, 960), (70, 84, 950), (67, 98, 930),
    (58, 90, 950), (61, 102, 920), (30, 101, 930), (45, 96, 950), (75, 93, 970), (80, 75, 1020), (50, 82, 970),
    (20, 76, 1000), (38, 92, 960),
    # the Southern Woods
    (90, 58, 1150), (95, 81, 1050), (104, 94, 1000), (106, 101, 980), (90, 70, 1150), (110, 70, 1300),
    (122, 80, 1450), (122, 64, 1500), (118, 96, 1100), (90, 95, 1020), (100, 60, 1280), (86, 102, 960),
]

CALM = [(21, 60, 5), (106, 44, 5), (29, 89, 9), (42, 76, 6), (79, 36.5, 3.5), (72, 33.6, 3.2), (87, 44.8, 3.2),
        (95, 81, 4), (104, 94, 3), (58, 90, 3), (61, 102, 2.5), (36, 51, 2.5), (34, 31, 3), (60, 76, 2), (70, 84, 2),
        (67, 98, 2), (32, 60, 2), (90, 58, 2), (42, 70, 2), (59, 46, 2), (100, 30, 2), (16, 88, 2.5), (21.5, 96.5, 2.5)]

def roll(x, y):
    w = 1.0
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 4.0))
    w = min(w, smooth((RIM_Y - 2 - y) / 4.0))
    v = (110 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.6 + 1.1) + 70 * math.sin((x + 1.4 * y) / 4.7 + 0.3)
         + 40 * math.sin((x - 1.7 * y) / 2.6))
    return w * v

def land(x, y):
    if y > RIM_Y:
        return 0.0
    num = den = 0.0
    for cx, cy, h in CONTROL:
        d2 = (x - cx) ** 2 + (y - cy) ** 2
        if d2 < 0.01:
            return float(h) + roll(x, y)
        w = 1.0 / (d2 ** 1.3)
        num += w * h
        den += w
    h = num / den + roll(x, y)
    # the brook's bed: a shallow valley along the Glimmerbrook
    d = dist_to_line(x, y, BROOK)
    if d < 3:
        h -= 60 * (1 - smooth(d / 3.0))
    return h

# clearings the stands leave open (x0, y0, x1, y1 in cells): the ways in, the set pieces and their arrivals
# (A6's review: the troll holes' and the great tree's glade drawn in, so the woods close round them)
CLEARINGS = [(89.5, 75.5, 100.5, 86), (101, 90.5, 107, 97), (54.5, 86.5, 61.5, 93.5), (58.8, 74.3, 62.8, 77.7),
             (68.8, 82.3, 73.3, 86.2), (65.8, 96.3, 69.8, 99.7), (55.5, 98.5, 65.5, 104), (13.5, 85.5, 18.5, 90.5),
             (38.5, 73.0, 47.3, 83.2), (103.5, 98.5, 108.5, 103), (38.5, 98.5, 42.5, 102.5), (39, 61, 42.5, 64),
             (19, 101, 22, 104), (68.5, 30.5, 75.5, 37.5), (83.5, 41.5, 90.5, 48.5), (75.5, 33.5, 82.5, 39.5),
             (30.5, 27.5, 37.5, 35.5), (34, 49, 38, 53), (98, 28, 102, 32), (46.5, 26.5, 49.5, 29.5),
             (60, 50, 62.5, 52.5), (57.5, 44.5, 60.5, 47.5), (104.5, 39, 108.5, 42.5),
             # the caravan road's last stretch from the east arrival to D3's edge (a tree stood on it, the lane lead's
             # review of the crown tour), and its verge below the west fort
             (104.5, 42.5, 128, 45.5), (62.5, 41, 66, 43.5)]

def clip(poly, axis, value, keep_less):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina = (a[axis] <= value) if keep_less else (a[axis] >= value)
        inb = (b[axis] <= value) if keep_less else (b[axis] >= value)
        if ina:
            out.append(a)
        if ina != inb:
            t = (value - a[axis]) / (b[axis] - a[axis])
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out

def minus_clearings(poly, band=2.0):
    """The polygon cut into horizontal bands, each band split round the clearings it meets (convex pieces kept as
    polygons; a concave band piece is fine for the build's area test)."""
    ys = [p[1] for p in poly]
    pieces = []
    y = math.floor(min(ys))
    while y < max(ys):
        b = clip(clip(poly, 1, y, False), 1, y + band, True)
        if len(b) >= 3:
            xs = [p[0] for p in b]
            cuts = sorted((c[0], c[2]) for c in CLEARINGS if c[1] < y + band and c[3] > y)
            x = min(xs)
            spans = []
            for c0, c1 in cuts:
                if c1 <= x:
                    continue
                if c0 > x:
                    spans.append((x, c0))
                x = max(x, c1)
            spans.append((x, max(xs)))
            for x0, x1 in spans:
                if x1 - x0 < 0.5:
                    continue
                q = clip(clip(b, 0, x0, False), 0, x1, True)
                if len(q) >= 3 and K.poly_area(q) > 0.5:
                    pieces.append([[round(a, 2), round(c, 2)] for a, c in q])
        y += band
    return pieces

def grid_rows(step=4, unit=32):
    rows = []
    for j in range(128 // step):
        row = []
        for i in range(128 // step):
            x, y = step * i + step / 2, step * j + step / 2
            row.append(int(round(land(x, y) / unit)))
        rows.append(row)
    return rows

# ---------------------------------------------------------------------------------------------------------------
# The treehouses (D-23, route a). A trunk: a 12-sided foot with root buttresses and the round door, a tapered trunk
# above it, a deck round it with a railing, a shipped crown on its top. Only Sharla's deck is reached (her stair).
# ---------------------------------------------------------------------------------------------------------------
GREEN = (29.5, 89.0)
VILLAGE_FLOOR = 980
VILLAGE_GROUND = 992        # the terrace as built (980 on the 32 grid): the doors' and the decks' base
STAIR_ARC_R = 900           # Sharla's stair: its middle line's radius round the trunk (the deck's rim at 740)
STAIR_W = 192
STAIR_POST = 16
BARK = 'xdbark'             # the new bark (D-23; output/studio_cal/d2/tex, registered in source/textures.yml)
ROOTS = 'swpcnr2'           # MM6's mossy roots: the buttresses' faces
DOOR = 'tavsmdr'            # MM6's arched plank door with its iron knocker (the round foot doors)
DECK = 't68a13mm'           # MM8's dark planks: decks, rope walks
SLATE = 'xtslate'
# (building, index, centre, radius, trunk height, deck bottom, crown, title)
# the four decks the rope walks join stand at one height (2026-11-24, F48: the guild's at 720 and house 1's at 680 left
# a walk's end 34-40 under the deck it ran onto, town_fit_check bridges.step)
TREES = [
    ('building:sharla_tree', None, (25.5, 84.0), 440, 1150, 640, 'tree69'),
    ('building:sprite_guild_light', None, (34.5, 83.5), 400, 1050, 700, 'tree69'),
    ('building:sprite_potions', None, (23.0, 89.5), 380, 980, 700, 'tree62a'),
    ('building:sprite_houses', 1, (34.5, 89.5), 360, 940, 700, 'tree12'),
    ('building:sprite_houses', 2, (29.0, 94.5), 360, 960, 700, 'tree10'),
]
FOOT_H = 320
# the treehouse services' boards (D-92: every service house hangs one; house_signs.py)
TREE_SIGNS = {'building:sprite_guild_light': 'sglight', 'building:sprite_potions': 'sgalch'}

def house_of(bid, index):
    key = bid if index is None else '%s#%d' % (bid, index)
    return HOUSE[key]

plots_by_space = {}
plan_buildings = {}
footprints = []
doors_out = []
tree_info = {}

# texture fit (the user, 2026-11-20): the timber kit's window wall hhm1bw (a house wall with a window in it) stood in
# the strip over every trunk door and its trim band trim2_32a lay across the foot's flat top; both in the bark
TRUNK_TEX = {'window': BARK, 'trim': BARK}

def trunk_parts(r, h, deck_bottom, deck_r, railing=True, foot_h=FOOT_H, sides=12, roots=True):
    foot = {'id': 'foot', 'shape': 'round', 'at': None, 'radius': r, 'sides': sides, 'wall_height': foot_h,
            'roof': 'flat', 'windows': 'none', 'door_height': 256,
            'textures': {'wall': BARK, 'door': DOOR, 'roof': BARK, 'trim': BARK, 'window': BARK}}
    if roots:
        foot['buttresses'] = {'count': 1, 'width': 112, 'depth': int(r * 0.5), 'height': foot_h - 32,
                              'walls': [k for k in range(2, sides - 1)]}
    trunk = {'id': 'trunk', 'shape': 'round', 'at': None, 'radius': r, 'sides': sides, 'bottom': foot_h,
             'wall_height': h, 'taper': 0.72, 'roof': 'flat', 'windows': 'none',
             'textures': {'wall': BARK, 'roof': BARK, 'trim': BARK, 'window': BARK}}
    parts = [foot, trunk]
    if deck_bottom:
        deck = {'id': 'deck', 'shape': 'round', 'at': None, 'radius': deck_r, 'sides': sides, 'bottom': deck_bottom,
                'wall_height': 32, 'roof': 'flat', 'windows': 'none',
                'textures': {'wall': DECK, 'roof': DECK, 'trim': DECK}}
        if railing:
            deck['railing'] = {'height': 112, 'posts': 16, 'every': 160}
            deck['textures'].update({'railing': DECK, 'rail': DECK})
        parts.append(deck)
    return parts

def add_tree(bid, index, centre, r, h, deck_bottom, crown):
    fp = 3 if bid == 'building:sharla_tree' else 2
    cx, cy = centre
    at = (cx - fp / 2.0, cy - fp / 2.0)
    turn = facing_turn(GREEN[0] - cx, GREEN[1] - cy)
    deck_r = r + (300 if bid == 'building:sharla_tree' else 220)
    parts = trunk_parts(r, h, deck_bottom, deck_r, railing=(bid != 'building:sharla_tree'))
    mid = fp * 256
    for p in parts:
        p['at'] = [mid, mid]
    hid, hname = house_of(bid, index)
    if TREE_SIGNS.get(bid):
        # D-92 (A4, 2026-11-22): a service hangs its kind's board on the trunk's foot, on the facet beside the door
        # (wall 0 holds the door; the root buttresses take walls 2 to sides - 2)
        parts[0]['signs'] = [{'wall': '1', 'bay': 0, 'texture': TREE_SIGNS[bid], 'hang': True,
                              'size': K.sign_size(TREE_SIGNS[bid]), 'out': 48, 'bottom': 192}]
    plot = {'building': bid, 'at': [round(at[0], 3), round(at[1], 3)], 'facing': 's', 'kit': 'timber',
            'turn': turn, 'floor': VILLAGE_FLOOR, 'house': hid, 'title': hname, 'parts': parts,
            'door': {'part': 'foot', 'wall': '0'}, 'textures': dict(TRUNK_TEX)}
    if index is not None:
        plot['index'] = index
    plots_by_space.setdefault('town:sprite_village', []).append(plot)
    pb = plan_buildings.setdefault('town:sprite_village', {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [], 'service': hname}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append((index or 0, [fp, fp]))
    poly = [(at[0], at[1]), (at[0] + fp, at[1]), (at[0] + fp, at[1] + fp), (at[0], at[1] + fp)]
    footprints.append((bid, index, poly))
    t = math.radians(turn)
    fx, fy = -math.sin(t), math.cos(t)          # the door's way out (cells, y south)
    rc = r / 512.0
    dc = (cx + fx * rc, cy + fy * rc)
    doors_out.append((bid, index, dc, (cx + fx * (rc + 0.9), cy + fy * (rc + 0.9))))
    tree_info[(bid, index)] = {'centre': centre, 'r': r, 'h': h, 'deck_bottom': deck_bottom, 'deck_r': deck_r,
                               'top': FOOT_H + h, 'crown': crown, 'turn': turn, 'out': (fx, fy)}

for _t in TREES:
    add_tree(*_t)
# Nibbler's Hollow (4556): a hollow stump under a root of the great tree, its door to the glade (west)
NIBBLER_C = (45.5, 75.5)
def add_nibbler():
    bid = 'building:nibbler_hollow'
    cx, cy = NIBBLER_C
    at = (cx - 0.5, cy - 0.5)
    turn = facing_turn(-1, 0)
    parts = trunk_parts(224, 160, 0, 0, foot_h=288, sides=10, roots=True)
    parts[0]['buttresses']['walls'] = [k for k in range(2, 9)]
    for p in parts:
        p['at'] = [256, 256]
    parts[1]['taper'] = 0.6
    hid, hname = house_of(bid, None)
    plot = {'building': bid, 'at': [at[0], at[1]], 'facing': 's', 'kit': 'timber', 'turn': turn, 'floor': 1000,
            'house': hid, 'title': hname, 'parts': parts, 'door': {'part': 'foot', 'wall': '0'},
            'textures': dict(TRUNK_TEX)}
    plots_by_space.setdefault('zone:bark_glade', []).append(plot)
    plan_buildings.setdefault('zone:bark_glade', {})[bid] = {'id': bid, 'type': 'house', 'count': 1, 'doors': 1,
                                                            'footprint_cells': [(0, [1, 1])], 'service': 'residence'}
    footprints.append((bid, None, [(at[0], at[1]), (at[0] + 1, at[1]), (at[0] + 1, at[1] + 1), (at[0], at[1] + 1)]))
    doors_out.append((bid, None, (cx - 0.45, cy), (cx - 1.3, cy)))
add_nibbler()
for _pb in plan_buildings.values():
    for _b in _pb.values():
        _b['footprint_cells'] = [fp for _, fp in sorted(_b['footprint_cells'], key=lambda t: t[0])]

# the great tree of Bark (DD-09's door in its trunk, facing north to the glade)
GREAT_C = (42.0, 79.0)
GREAT_R = 760
GREAT_H = 2600
GREAT_FOOT = 448
# The great tree's plot turn: 180 (its door north) less half a facet. A round part's wall 0 looks south, so the trunk's
# 16 corners stood at 11.25 + 22.5 k degrees; S's crown (a decoration, facing 0: the studio writes no facing for a
# decoration, its `turn` is dropped) has its stub's corners at 0 + 22.5 k. Turning the trunk 11.25 lines them up.
GREAT_TURN = 180 - 11.25

def check_roads():
    bad = []
    for b, ix, poly in footprints:
        for line in ROADS:
            if K.line_hits_poly(line, poly, 0.45):
                bad.append('road under or against %s#%s: %s' % (b, ix, line[:3]))
        for line in PATHS:
            if K.line_hits_poly(line, poly, 0.3):
                bad.append('path under %s#%s: %s' % (b, ix, line[:3]))
    if bad:
        raise SystemExit('\n'.join(bad))
check_roads()

# ---------------------------------------------------------------------------------------------------------------
# Ways in. Arrival points (the dungeon exits come back to these) stand on open level ground beside the door.
# ---------------------------------------------------------------------------------------------------------------
WEST_FORT = (72.0, 33.6)
EAST_FORT = (87.0, 44.6)
DD13_WEST = (72.0, 36.1)            # the west fort's gate, looking south to the road
DD13_EAST = (87.0, 42.1)            # the east fort's gate, looking north to the road
# texture fit (the user, 2026-11-20): the Southern Tower in Castle Ironfist's seamless ashlar hcwall, not the one-storey
# skull-frieze panel hkm3b that tiled up it in bands, nor the castle kit's brown rubble ch1b1 in its window bays; no
# windows (a round part's window bay is two 256-high faces 145 wide: the arrow slit xkarrow, 128 x 256, tiled in it);
# the obelisk in the seamless ashlar cswl128
TOWER_STONE = 'hcwall'
OBELISK_STONE = 'cswl128'
DD06_C = (95.0, 81.0)               # the Southern Tower's middle; its door looks north
DD06_R = 420
DD06_JAMB = round((2 * DD06_R * math.sin(math.pi / 10) - 192) / 2, 3)   # D-180: beside the Southern Tower's 192 door
DD10B = (34.0, 30.0)                # the adit's mouth in the foothill rock face, looking south
HOLES = {'dd11a': ((61.0, 76.0), (60, 76), 'w'), 'dd11b': ((71.0, 84.0), (70, 84), 'w'),
         'dd11c': ((68.0, 98.0), (67, 98), 'w')}   # pit, its return arrival (about 300-600 beside), facing
# A7's inside points of the Troll Holes (a coordinate in each pocket's BLV), facing east (0); the holes open when the
# BLV and A2's map_stats row both exist (DUNGEON above)
# A7's DD-11A/B starts moved 176/182 into the pit's corner (2026-11-24: the tunnel trolls saw the old landing)
HOLE_INSIDE = {'dd11a': (80, -208, 0), 'dd11b': (144, -208, 0), 'dd11c': (128, -64, 0)}
# A8's DD-09 start (its NOTES.md): at the foot of the temple's first stair inside the trunk door, facing north (512)
DD09_INSIDE = (0, -1920, 0)
PARLEY = (79.0, 36.4)
# D-120 (2026-11-24): the fairy ring stood at (16, 88), past the map's bounds (cell 18.9): no party reached it. Now in
# the village's empty south-west corner, its caps (1.1 cells round) east of cell 20
FAIRY = (21.5, 96.5)
# D-25 (b): DD-13's east gate enters at A7's explicit inside point (a coordinate in xeen_dd13.blv) until A1's
# second-arrival word lands; None until A7 gives it (the door is sealed while DD-13 is not installed)
DD13_EAST_INSIDE = (7552, 32, 0)    # A7 (session 8): the east gate's inside point, facing south (1536); the west
                                    # gate enters at DD-13's start (0, -64, 0) facing north
DD13_WEST_INSIDE = (0, -64, 0)      # A7's DD-13 NOTES: the map's start in room:gate_w, facing north (512)
DD10B_INSIDE = (0, 192, 0)          # A8's DD-10B NOTES: just inside the adit's mouth, facing north (512)
# A7's DD-06 inside point: the party arrives in the Southern Tower's hall at (640, 1700, 0) facing south (1536); DD-06's
# own front door (its event 17) lands on D2 at (15872, -7680, 1056) facing north = entrance:dd06_door (95, 79)
DD06_INSIDE = (640, 1700, 0)
DD06_FACING = 1536
SEALED = 'The way in is choked and dark. (Not yet open: this place comes in a later part of the world.)'

def dungeon_way(key, title, hint_name, hook_name=None, sealed=None, inside=None, facing=None, arrival=None):
    """into + condition when the dungeon is installed; else the hook (if any) and a sealed message. The door names
    the dungeon's entrance (`arrival`, D-37) when its studio sidecar lists it, else the inside point."""
    target = 'xeen_%s.blv' % key
    if DUNGEON[key]:
        w = {'into': {'map': target}}
        if arrival and arrival in studio_entrances(target):
            w['into']['arrival'] = arrival
        elif inside:
            w['into']['at'] = list(inside)
        if facing is not None and 'arrival' not in w['into']:
            w['into']['facing'] = facing
        if hook_name:
            w['condition'] = {'lua': 'XeenQuests.hook("%s")' % hook_name}
            USED.add(hook_name)
        return w
    text = sealed or SEALED
    if hook_name:
        USED.add(hook_name)
        return {'effects': [{'lua': 'if XeenQuests.hook("%s") then evt.SimpleMessage(%s) end'
                             % (hook_name, lua_str(text))}]}
    return {'effects': [msg(text)]}

# build()'s keep_clear areas (the arrivals, the village, the great tree, the mine mouth, the parley, the clearings)
KEEP_CLEAR = [[[17, 54], [30, 54], [30, 65], [17, 65]], [[17, 78], [41, 78], [41, 100], [17, 100]],
              [[34, 67], [48, 67], [48, 82], [34, 82]], [[30, 28], [38, 28], [38, 35], [30, 35]],
              [[75, 32], [84, 32], [84, 41], [75, 41]], [[100, 38], [112, 38], [112, 49], [100, 49]],
              [[55, 87], [61, 87], [61, 93], [55, 93]], [[89, 75], [101, 75], [101, 86], [89, 86]],
              [[101, 90], [107, 90], [107, 97], [101, 97]], [[56, 99], [65, 99], [65, 104], [56, 104]]]

def d142_enforce(areas, village_doors):
    """D-142 / D-157 (2026-11-25, F64) for the encounter circles (common/d142.py): the edge arrivals and the dungeon
    exits (the troll holes, DD-13's gates, DD-06/09/10B's mouths; D2 in check_arrivals.D142_EXITS) 4,096 from a
    marker's edge (5,888 for a slot that shoots or casts); every road, lane and path 1,024 from its centre. A failing
    circle moves to the nearest spot off the water, the keep-clear areas and steep land that keeps build()'s own rules
    (2,500 from the village doors, D-85's 5,120 from the edge arrivals, 1,500 from the parley fire, 3 cells from the
    adit)."""
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import d142
    sys.path.pop(0)
    d142.CA.D142_EXITS.add(STEM)   # the floors this build is held to (the checker's set takes D2 at its install)
    l4 = os.path.join(OUT, 'sketch.yml')
    base = d142.standard_ok(l4, land, keep_off=KEEP_CLEAR)

    def ok(x, y, r):
        return (base(x, y, r)
                and min(math.hypot(x - d[0], y - d[1]) for d in village_doors) * 512 >= 2600
                and all(math.hypot(x - e[0], y - e[1]) * 512 >= 5220 + r * 512 for e in (WEST_START, EAST_START))
                and math.hypot(x - PARLEY[0], y - PARLEY[1]) * 512 >= 1600
                and math.hypot(x - MINE_LANE[-1][0], y - MINE_LANE[-1][1]) - r >= 3)
    # F63 (2026-11-25, check_spawn_clear `spawn.at_hull`): a circle whose markers can stand within 768 of the bounds
    # moves too (the west glade's (20, 76), the woods' (107.5, 86))
    d142.enforce(STEM, areas, d142.road_cells(l4), {}, ok, also=d142.hull_reason(l4))

def build():
    os.makedirs(OUT, exist_ok=True)
    # ================================ project.yml
    neighbours = [
        {'id': 'door:dd09', 'to': 'xeen_dd09.blv', 'kind': 'door', 'condition': {'item': 'bark_key'},
         'arrival_hint': "Inside the great tree's trunk, at the foot of the temple's first stair.",
         'notes': "DD-09 Temple of Bark (A8): the door in the great tree's trunk (q-d9.bark_door)."},
        {'id': 'door:dd11a', 'to': 'xeen_dd11a.blv', 'kind': 'door', 'arrival_hint': 'At the bottom of the first pit.',
         'notes': 'DD-11A Troll Holes, first pocket (A7): a pit in the forest floor (q-d13.troll_holes).'},
        {'id': 'door:dd11b', 'to': 'xeen_dd11b.blv', 'kind': 'door', 'arrival_hint': 'At the bottom of the second pit.',
         'notes': 'DD-11B, second pocket (A7).'},
        {'id': 'door:dd11c', 'to': 'xeen_dd11c.blv', 'kind': 'door',
         'arrival_hint': "At the bottom of the third pit, outside Hobstadt's hall.",
         'notes': "DD-11C, third pocket with Hobstadt's throne (A7)."},
        {'id': 'door:dd13_west', 'to': 'xeen_dd13.blv', 'kind': 'door', 'arrival_hint': "Inside the west fort's gate.",
         'notes': 'DD-13 Ogre Forts (A7), the west fort: one BLV, two entrances.'},
        {'id': 'door:dd13_east', 'to': 'xeen_dd13.blv', 'kind': 'door', 'arrival_hint': "Inside the east fort's gate.",
         'notes': 'DD-13, the east fort.'},
        {'id': 'door:dd06', 'to': 'xeen_dd06.blv', 'kind': 'door', 'condition': {'item': 'south_tower_key'},
         'arrival_hint': "Inside the Southern Tower's door.",
         'notes': "DD-06 Southern Tower (A7): the thieves' den (q-d19.tower_door; key from Thaddeus, D3)."},
        {'id': 'door:dd10b', 'to': 'xeen_dd10b.blv', 'kind': 'door', 'arrival_hint': "In the adit's mouth, facing in.",
         'notes': 'DD-10B Gemstone Mines, east pocket (A7/A8): an adit in the Gemstone foothills.'},
    ]
    if D1_LIVE:
        neighbours.insert(0, {
            'id': 'edge:west', 'to': 'xeen_d1.odm', 'kind': 'edge', 'side': 'west', 'days': 5, 'arrival_side': 'east',
            'approach': "The Castleview road from D1's east edge, at y 60 (fixed with D1).",
            'notes': "D1 Castleview Vale: D1's own east edge arrives at D2's west start (21, 60) facing east."})
    if D3_LIVE:
        neighbours.insert(0, {
            'id': 'edge:east', 'to': 'xeen_d3.odm', 'kind': 'edge', 'side': 'east', 'days': 5, 'arrival_side': 'west',
            'approach': "The caravan road down from Ogre Pass's east mouth, at y 44.",
            'notes': "D3 Sandcaster (A5): D3's west edge arrives at D2's east start (106, 44) facing west."})
    project = {
        'format': 0, 'id': STEM, 'name': 'Sprite Forest and Ogre Pass', 'world': 'xeen', 'kind': 'outdoor',
        'profile': 'odm', 'map_code': 'D2', 'units': {'plan_grid': 512}, 'extent': {'terrain_cells': 128},
        'map_stats': {
            'id': 9109, 'continent': 7, 'encounter_chance': 10, 'treasure_level': 3, 'trap_dice': 3,
            'perception_difficulty': 3, 'refill_days': 672, 'music': 33, 'environment': 'forest',
            'lock_difficulty': 6,
            # A2's live row 9109 (D-23; A2's kill-XP recount, 2026-11-20): wolves, trolls, the Darkside sprite tiers
            # (Gorgon 16, Elder Gorgon 22, the Queen 18 the rare third), all Dif 3 in groups of 2-3 (150 hostiles)
            'slots': [
                {'monster': SLOT['wolves'], 'tier': 3, 'per_marker': [2, 3], 'weight': 40},
                {'monster': SLOT['trolls'], 'tier': 3, 'per_marker': [2, 3], 'weight': 35},
                {'monster': SLOT['dark_sprites'], 'tier': 3, 'per_marker': [2, 3], 'weight': 25},
            ]},
        'neighbours': neighbours,
        'qbits': {k: v for k, v in QBIT.items()},
        'items': dict(ITEMS),
        'rules': {'respawn': 'entrance:forest_edge' if D1_LIVE else 'entrance:west_road'},
        'notes': ("D2 Sprite Forest and Ogre Pass (A6, 2026-11-20), built from the approved L1 with D-23. The west edge "
                  "(D1) and the east edge (D3) are sealed with a sign until their maps are installed (D1_LIVE, "
                  "D3_LIVE); each dungeon door shows its hook and a sealed line until its BLV is installed. "
                  "Written by output/studio_cal/d2/tools/gen.py."),
    }
    # ================================ plan.yml (L1's spaces with D-23 applied)
    L1 = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'plan.yml')))
    plan = copy.deepcopy(L1)
    plan['level'] = 'L3'
    for s in plan['spaces']:
        if s['id'] in plan_buildings:
            s['buildings'] = list(plan_buildings[s['id']].values())
        if s['id'] == 'zone:ogre_pass':
            s['population'] = [
                {'id': 'pop:pass_ogres', 'actor': str(ROW['ogre']), 'groups': 4, 'placed': True, 'hostile': True,
                 'notes': ('22 placed (Ogres 18, Brutes 22, two Chiefs 30) in the two fort yards and two road groups: '
                           'hostile at load, peaceful on q-d11.friends, hostile again on q-d11.hostile or a fort '
                           'burned (D-12.3, D-23).')},
                {'id': 'pop:graalg', 'actor': str(ROW['graalg']), 'groups': 1, 'placed': True, 'hostile': False,
                 'notes': ("Graalg (A2's 11064, talking actor 5108) and two Graalg's Brutes (11065), their own "
                           "faction, peaceful at the parley fire until q-d11.hostile or a fort burned.")}]
        if s['id'] == 'town:sprite_village':
            s['purpose'] = ("The sprites' village (A4's d2.yml, 4551-4555): Dewdrop Potions, the Light Guild of the "
                            "Treetops, Sharla's Treehouse and two bowers, each a giant tapered trunk with a round door "
                            "at its foot and a lantern each side, a deck round it and a crown on top; rope walks "
                            "between the decks; only Sharla's stair goes up (to her chest). Peaceful sprites until "
                            "q-d10.robbery.")
            s['population'] = [
                {'id': 'pop:village_sprites', 'actor': str(ROW['medusa_sprite']), 'groups': 1, 'placed': True,
                 'hostile': False, 'notes': ("8 village sprites on A2's village rows 11537/11538 (Medusa 10, Killer "
                                             "14, faction xeen_sprites_village): peaceful; hostile on q-d10.robbery "
                                             "(A2's relations); all dead sets q-d10.sprites_slain.")}]
            s['theme'] = 'Giant tapered trunks of bark with root buttresses, round doors with lanterns, plank decks.'
        if s['id'] == 'zone:brink':
            s['purpose'] = ("Where the forest ends at the rim (y 104, D-23): the sprites' lookout bench by the "
                            "Glimmerbrook's fall over the edge; the stars below.")
    sealed = []
    if not D1_LIVE:
        sealed.append('edge:west')
    if not D3_LIVE:
        sealed.append('edge:east')
    ents = []
    for e in plan['entrances']:
        if e.get('neighbour') == 'edge:west' and not D1_LIVE:
            e = {'id': e['id'], 'space': e['space'], 'kind': 'arrival', 'facing': 'e',
                 'how': ("The Castleview road at the forest's edge: the respawn and the tests' start; the edge to D1 "
                         "is sealed until D1 is installed (then D1's arrival).")}
        if e.get('neighbour') == 'edge:east' and not D3_LIVE:
            continue
        ents.append(e)
    # the tests' start and the respawn: a plain arrival on the west road (with D1 live the edge's arrival stands by it)
    if D1_LIVE:
        ents.insert(0, {'id': 'entrance:forest_edge', 'space': 'zone:west_edge', 'kind': 'arrival', 'facing': 'e',
                        'how': "The Castleview road at the forest's edge: the respawn and the tests' start."})
    plan['entrances'] = ents
    # D-58 Q10 (A6 s16): a fall from D7's zone C3-D4 lands here (Xeen.SkyFalls.d7_d2); whole flat cell, 256 clear
    plan['entrances'].append({'id': 'entrance:d7_fall', 'space': next(e['space'] for e in ents if e['id'] == 'entrance:dd06_door'),
                              'kind': 'both', 'facing': 's',   # 'arrival' would make it the party start
                              'how': "D-58 Q10: a fall from D7 lands here, 1,024 north of the Southern Tower's door (its roof leads up to D7 after m30.done)."})
    for v in plan['sightlines']:
        if v['from'] == 'entrance:east_road' and not D3_LIVE:
            v['from'] = 'zone:east_meadow'
    plan.pop('totals', None)
    plan['sketch'] = {'file': 'sketch.yml', 'grid': 512}
    plan['landform']['rim']['notes'] = ("The world rim along the whole south edge at y 104 (D-23): a cliff of about 900 "
                                        "to the stars. West and east the land runs on to D1 and D3; north the range "
                                        "closes the map.")
    plan['notes'] = ('L3/L4 written by output/studio_cal/d2/tools/gen.py from the approved L1 and D-23. The plan keeps '
                     "the L1 spaces; the pass ogres, Graalg's three and the village sprites are placed actors, the "
                     'wolves, trolls and wild sprites slot markers.')
    # ================================ sketch.yml
    rim = [
        {'side': 'south', 'form': 'level', 'height': 0, 'meet': 1,
         'notes': 'The world rim: the land ends in a cliff at y 104 (D-23); below, water at 0 stands for the stars.'},
        {'side': 'north', 'form': 'ridge', 'height': [3400, 4400], 'floor': 2600, 'crest': 10, 'roughness': 140,
         'notes': 'The Gemstone Range: slate crags with crystal veins.'},
        {'side': 'west', 'span': [0, 50], 'form': 'ridge', 'height': [1900, 2600], 'floor': 1600, 'crest': 10,
         'roughness': 100, 'notes': "The foothills go on into D1's north-east."},
        {'side': 'west', 'span': [50, 70], 'form': 'level', 'height': 1000, 'meet': 6,
         'notes': "The road's valley, open to D1."},
        {'side': 'west', 'span': [70, 104], 'form': 'ridge', 'height': [1150, 1450], 'floor': 1000, 'crest': 8,
         'roughness': 60, 'notes': "Wooded rises toward D1's south-east."},
        {'side': 'west', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1},
        {'side': 'east', 'span': [0, 32], 'form': 'ridge', 'height': [2800, 3600], 'floor': 2200, 'crest': 10,
         'roughness': 120, 'notes': "The range's east end."},
        {'side': 'east', 'span': [32, 56], 'form': 'level', 'height': 1300, 'meet': 6,
         'notes': "The caravan road's valley, open to D3."},
        {'side': 'east', 'span': [56, 104], 'form': 'ridge', 'height': [1300, 1700], 'floor': 1100, 'crest': 8,
         'roughness': 80, 'notes': 'Wooded hills toward the Aging Forest.'},
        {'side': 'east', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1},
    ]
    edges = []
    if D1_LIVE:
        edges.append({'side': 'west', 'span': [52, 68], 'neighbour': 'edge:west',
                      'notes': 'The Castleview road runs out to x 0 at y 60 (fixed with D1).'})
    if D3_LIVE:
        edges.append({'side': 'east', 'span': [36, 52], 'neighbour': 'edge:east',
                      'notes': 'The caravan road runs out to x 127 at y 44 (A5, D3).'})
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its land function.'},
        'points': [
            {'at': [44, 8], 'h': 4200, 'notes': "the range's highest crystal crag"},
            {'at': [88, 12], 'h': 4400, 'notes': "the spur's root"},
            {'at': [24, 10], 'h': 3800}, {'at': [62, 10], 'h': 3900}, {'at': [106, 12], 'h': 3700},
            {'at': [80, 25], 'h': 3400, 'notes': "the spur's north peak"},
            {'at': [100, 30], 'h': 2300, 'notes': "the genie's ledge"},
            {'at': [48, 28], 'h': 2000, 'notes': 'the crystal seam'},
        ],
        'ridges': [
            {'line': [[30, 28.5], [34, 28], [38, 28.5]], 'height': [2250, 2350, 2250], 'width': 2, 'slope': 1,
             'notes': "The rock the east adit is cut into (its face the cliff at y 30)."},
            {'line': [[80, 18], [80, 24], [80, 29], [80, 32.5]], 'height': [3600, 3400, 3200, 2600], 'width': 3,
             'slope': 2, 'notes': 'The Gemstone Spur north of the pass.'},
            {'line': [[80, 40.5], [80, 44], [80, 48], [79, 54], [77.5, 59.5]],
             'height': [2600, 3100, 3000, 2600, 1800], 'width': 3, 'slope': 2,
             'notes': 'The spur south of the pass, falling to crags over the forest track.'},
        ],
        'terraces': [
            {'polygon': [[76.5, 34.2], [81.5, 34.2], [81.5, 38.8], [76.5, 38.8]], 'height': 2050, 'slope': 3,
             'notes': "Ogre Pass's saddle: Graalg's parley fire."},
            {'polygon': [[69.2, 30.8], [74.8, 30.8], [74.8, 36.4], [69.2, 36.4]], 'height': 2000, 'slope': 3,
             'notes': "The west fort's knoll."},
            {'polygon': [[84.2, 42.0], [89.8, 42.0], [89.8, 47.6], [84.2, 47.6]], 'height': 2150, 'slope': 3,
             'notes': "The east fort's knoll."},
            {'polygon': [[19, 80], [39, 80], [39, 98], [19, 98]], 'height': VILLAGE_FLOOR, 'slope': 4,
             'notes': "Sharla's treehouse village and its green."},
            {'polygon': [[36, 72], [48, 72], [48, 85], [36, 85]], 'height': 1000, 'slope': 4,
             'notes': 'The glade of the great tree.'},
            {'polygon': [[90, 76], [100, 76], [100, 85], [90, 85]], 'height': 1050, 'slope': 3,
             'notes': "The Southern Tower's clearing."},
            {'polygon': [[101.5, 91], [106.5, 91], [106.5, 96.5], [101.5, 96.5]], 'height': 1000, 'slope': 2,
             'notes': 'The Shrine of the Elements.'},
            {'polygon': [[55, 87], [61, 87], [61, 93], [55, 93]], 'height': 950, 'slope': 2,
             'notes': 'The Forbidden Fruit clearing.'},
            {'polygon': [[31, 30.6], [37, 30.6], [37, 35], [31, 35]], 'height': 1700, 'slope': 2,
             'notes': "The ground before the east adit (DD-10B)."},

            {'polygon': [[98.5, 28.6], [101.5, 28.6], [101.5, 31.4], [98.5, 31.4]], 'height': 2300, 'slope': 2,
             'notes': "The genie's ledge."},
            {'polygon': [[34.5, 49.5], [37.5, 49.5], [37.5, 52.5], [34.5, 52.5]], 'height': 1260, 'slope': 2,
             'notes': "The obelisk's knoll."},
            {'polygon': [[17, 55], [26, 55], [26, 65], [17, 65]], 'height': 1000, 'slope': 3,
             'notes': 'The D1 arrival at the forest edge.'},
            {'polygon': [[101, 40], [111, 40], [111, 48], [101, 48]], 'height': 1300, 'slope': 3,
             'notes': 'The D3 arrival: the Sandcaster road\'s end.'},
        ],
        'cliffs': [
            {'line': [[0, RIM_Y], [128, RIM_Y]], 'drop': 940, 'down': 'right',
             'notes': 'The world rim, south (D-23: y 104); the Glimmerbrook falls over it at x 58 (Sprite Falls).'},
            {'line': [[74, 48], [73, 55], [74, 61]], 'drop': 500, 'down': 'right',
             'notes': "The spur's west face over the Whispering Glades."},
            {'line': [[31, 30], [37, 30]], 'drop': 300, 'down': 'right',
             'notes': "The rock face with the mines' adit."},
        ],
        'peaks': [
            {'polygon': [[4, 4], [124, 4], [124, 19], [4, 19]], 'count': 26, 'height': [3000, 4400],
             'radius': [2, 4], 'profile': 'cone', 'spacing': 4, 'seed': 3,
             'notes': 'The Gemstone Range broken into crags, its foot at y 19-22 seen from the forest and the pass.'},
            {'polygon': [[78, 18], [82, 18], [82, 31], [78, 31]], 'count': 4, 'height': [3200, 3700],
             'radius': [1.5, 2.5], 'profile': 'cone', 'spacing': 3, 'seed': 5,
             'notes': "The spur's crest north of the saddle broken into tops."},
            {'polygon': [[78, 41], [82, 41], [82, 52], [78, 52]], 'count': 3, 'height': [2900, 3300],
             'radius': [1.5, 2.5], 'profile': 'cone', 'spacing': 3, 'seed': 7,
             'notes': "The spur's crest south of the saddle."},
        ],
    }
    water = {
        'rivers': [
            {'id': 'water:brook', 'line': BROOK, 'width_cells': 1.5,
             'notes': ("The Glimmerbrook: from the range's foot (52, 21) under the caravan road's log bridge (51, 48) "
                       "and the forest track's footbridge (48.5, 70), past the great tree, over the rim at x 58 "
                       "(Sprite Falls). It touches no map edge (D-23).")},
        ],
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0,
             'polygon': [[0, RIM_Y + 1], [128, RIM_Y + 1], [128, 128], [0, 128]],
             'notes': 'Below the rim: stands for the stars (the game draws no void).'},
        ],
    }
    roads = [
        {'link': 'link:castleview_road', 'line': CASTLEVIEW_ROAD, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:caravan_west', 'line': CARAVAN_WEST, 'width': 'road', 'surface': 'soil_stony',
         'notes': 'Over the Glimmerbrook by the log bridge (thing:log_bridge).'},
        {'link': 'link:caravan_east', 'line': CARAVAN_EAST, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:forest_track', 'line': FOREST_TRACK, 'width': 'lane'},
        {'link': 'link:glade_track', 'line': GLADE_TRACK, 'width': 'lane',
         'notes': 'Over the Glimmerbrook by the footbridge (thing:footbridge).'},
        {'link': 'link:south_climb', 'line': SOUTH_CLIMB, 'width': 'lane'},
        {'link': 'link:village_lane', 'line': VILLAGE_LANE, 'width': 'lane'},
        {'link': 'link:tower_lane', 'line': TOWER_LANE, 'width': 'lane'},
        {'link': 'link:shrine_path', 'line': SHRINE_PATH, 'width': 'lane'},
        {'link': 'link:mine_lane', 'line': MINE_LANE, 'width': 'lane', 'surface': 'soil_stony'},
        {'link': 'link:fruit_lane', 'line': FRUIT_LANE, 'width': 'lane'},
        {'link': 'link:brink_path', 'line': BRINK_PATH, 'width': 'lane'},
    ]
    districts = [
        {'space': 'town:sprite_village', 'polygon': [[19, 80], [39, 80], [39, 98], [19, 98]],
         'plots': plots_by_space['town:sprite_village']},
        {'space': 'zone:village_green', 'polygon': [[26, 86], [33, 86], [33, 92], [26, 92]]},
        {'space': 'zone:bark_glade', 'polygon': [[34, 67], [48, 67], [48, 80], [34, 80]],
         'plots': plots_by_space['zone:bark_glade']},
        {'space': 'zone:west_edge', 'polygon': [[0, 54], [24, 54], [36, 52], [40, 56], [34, 64], [16, 66], [0, 68]]},
        {'space': 'zone:range', 'polygon': [[0, 0], [128, 0], [128, 22], [116, 22], [104, 19], [96, 21], [88, 17],
                                            [80, 20], [72, 18], [62, 17], [50, 15], [38, 17], [26, 15], [14, 19],
                                            [0, 21]]},
        {'space': 'zone:foothills', 'polygon': [[0, 21], [14, 19], [26, 15], [38, 17], [50, 15], [62, 17], [72, 18],
                                                [74, 30], [60, 30], [60, 40], [52, 44], [44, 48], [36, 52], [24, 54],
                                                [0, 54]]},
        {'space': 'zone:mine_mouth', 'polygon': [[30, 28], [38, 28], [38, 35], [30, 35]]},
        {'space': 'zone:ogre_pass', 'polygon': [[60, 30], [98, 30], [100, 48], [86, 48], [70, 48], [60, 46]]},
        {'space': 'zone:pass_saddle', 'polygon': [[76, 34], [82, 34], [82, 39], [76, 39]]},
        {'space': 'zone:spur_crags', 'polygon': [[72, 48], [88, 48], [86, 58], [80, 65], [73, 62], [70, 54]]},
        {'space': 'zone:whispering_glades', 'polygon': [[44, 48], [52, 44], [60, 40], [60, 46], [70, 48], [70, 54],
                                                        [73, 62], [68, 62], [56, 63], [46, 60], [40, 56]]},
        {'space': 'zone:east_descent', 'polygon': [[98, 30], [104, 19], [116, 22], [128, 22], [128, 52], [100, 50],
                                                   [100, 48]]},
        {'space': 'zone:east_meadow', 'polygon': [[100, 38], [112, 38], [112, 49], [100, 49]]},
        {'space': 'zone:sprite_forest', 'polygon': [[0, 68], [16, 66], [34, 64], [40, 56], [46, 60], [56, 63],
                                                    [68, 62], [73, 62], [80, 65], [82, 70], [82, 104], [0, 104]]},
        {'space': 'zone:west_glades', 'polygon': [[17, 66], [28, 66], [32, 72], [27, 78], [17, 78]]},
        {'space': 'zone:troll_country', 'polygon': [[50, 73], [66, 70], [78, 70], [82, 78], [82, 103], [64, 103],
                                                    [52, 98], [49, 90]]},
        {'space': 'zone:fruit_clearing', 'polygon': [[55, 87], [61, 87], [61, 93], [55, 93]]},
        {'space': 'zone:brink', 'polygon': [[56, 99], [65, 99], [65, 104], [56, 104]]},
        {'space': 'zone:southern_woods', 'polygon': [[86, 48], [100, 48], [100, 50], [128, 52], [128, 104], [82, 104],
                                                     [82, 70], [80, 65], [86, 58]]},
        {'space': 'zone:tower_clearing', 'polygon': [[89, 75], [101, 75], [101, 86], [89, 86]]},
        {'space': 'zone:shrine_glade', 'polygon': [[101, 90], [107, 90], [107, 97], [101, 97]]},
        {'space': 'zone:rim', 'polygon': [[0, RIM_Y], [128, RIM_Y], [128, 128], [0, 128]]},
    ]
    points = [{'id': 'entrance:west_road', 'at': list(WEST_START), 'facing': 'e'}]
    points.append({'id': 'entrance:d7_fall', 'at': [95, 77], 'facing': 's'})   # D-58 Q10 (A6 s16)
    if D1_LIVE:
        points.append({'id': 'entrance:forest_edge', 'at': [WEST_START[0] + 1, WEST_START[1]], 'facing': 'e'})
    if D3_LIVE:
        points.append({'id': 'entrance:east_road', 'at': list(EAST_START), 'facing': 'w'})
    points += [
        {'id': 'entrance:dd09_door', 'at': [42, 77], 'facing': 'n'},
        {'id': 'entrance:dd13_west', 'at': [72, 37], 'facing': 's'},
        {'id': 'entrance:dd13_east', 'at': [87, 41], 'facing': 'n'},
        {'id': 'entrance:dd06_door', 'at': [95, 79], 'facing': 'n'},
        {'id': 'entrance:dd10b_adit', 'at': [34, 32], 'facing': 's'},
    ]
    for key, (pit, arr, fac) in HOLES.items():
        points.append({'id': 'entrance:%s_hole' % key, 'at': list(arr), 'facing': fac})
    points += [{'id': 'junction:forest_fork', 'at': [32, 60]}, {'id': 'junction:bark_glade', 'at': [42, 70]},
               {'id': 'junction:south_fork', 'at': [90, 58]}, {'id': 'junction:pass_saddle', 'at': [79, 37]},
               {'id': 'landmark:great_tree', 'at': list(GREAT_C)}, {'id': 'landmark:range', 'at': [88, 12]},
               {'id': 'landmark:west_fort', 'at': list(WEST_FORT)}, {'id': 'landmark:east_fort', 'at': list(EAST_FORT)},
               {'id': 'landmark:southern_tower', 'at': list(DD06_C)},
               {'id': 'landmark:sprite_falls', 'at': [FALLS_X, RIM_Y]}]
    POI_AT = {'poi:obelisk': (36, 51), 'poi:shrine_elements': (104, 93.8), 'poi:forbidden_fruit': (58, 90),
              'poi:genie_lamp': (100, 30), 'poi:pot_of_gold': (106, 101), 'poi:graalg': PARLEY,
              'poi:treehouse_chest': (25.5, 84), 'poi:kramer_wagon': (59, 46.2), 'poi:crystal_seam': (48, 28),
              'poi:fairy_ring': FAIRY, 'poi:dead_adventurer': (71, 84.6), 'poi:thieves_drop': (98.4, 83.4),
              'poi:brink_bench': (61, 103)}
    for k, at in POI_AT.items():
        points.append({'id': k, 'at': list(at)})
    for i, at in enumerate([(33, 60.8), (43, 69), (91, 58.8), (80.2, 38.4)]):
        points.append({'id': 'poi:signposts', 'index': i + 1, 'at': list(at)})
    # ---------------------------------------------------------------- encounter areas (46 markers of 2-3)
    areas = []
    def markers(pop, spots, slot):
        for (cx, cy, n, r) in spots:
            k = sum(1 for a in areas if a['id'] == pop) + 1
            areas.append({'id': pop, 'index': k, 'kind': 'encounter', 'count': n, 'slot': slot,
                          'circle': {'at': [cx, cy], 'r': r}})
    # E1: the foothills (wolves); none within 3 cells of the adit
    markers('pop:foothill_wolves', [(22, 26, 2, 1.5), (22, 36, 1, 1), (29, 41, 2, 1.5), (41, 24, 2, 1.5),
                                    (46, 40, 2, 1.5), (56, 23, 2, 1.5), (62, 33, 1, 1), (28, 101, 1, 1)], 1)
    # F10 (s32): the lone wolf at the west rim (12, 30) moved to the empty south-west corner (28, 101); the woods'
    # lone wolf beyond the east rim (120, 70) to the empty north-east corner (104, 24)
    # E2: the wild sprites (the Darkside tiers, slot 3): the western glades (the first fight from D1) and the
    # Whispering Glades
    # D-85 (A6 s30): the first sprites from D1 moved south, the built marker 6,001 from the arrival (was (22, 69):
    # 4,789; D-15's band ends at 6,000)
    markers('pop:west_sprites', [(22, 72, 1, 1), (27, 73, 2, 1.5), (20, 76, 1, 1)], 3)
    markers('pop:glade_sprites', [(46.5, 56, 2, 1.2), (58, 52, 2, 1.5), (64, 56, 1, 1), (55, 59, 1, 1)], 3)
    # E3: troll country (trolls), by the holes and lanes
    # D-138 (2026-11-24): no troll circle within 2,000 of a hole's return spot (D-15's first-fight buffer, counting
    # markers, D-133): (58, 79) 1,717 from DD-11A's and (63, 96) 1,824 from DD-11C's moved out to the nearest spots
    # past it on the same plain, (72, 89) half a cell south (its circle's edge 1,989 from DD-11B's)
    markers('pop:trolls', [(56, 80.5, 2, 1.5), (66, 80, 2, 1.5), (72, 89.5, 2, 1.5), (61.5, 95.5, 2, 1.5),
                           (76, 98, 2, 1.5), (78, 78, 1, 1), (51, 93, 1, 1), (70, 76, 1, 1), (73, 94, 1, 1)], 2)
    # E5: the Southern Woods (wolves); the first fight from D3 (D-85, A6 s30: moved from (101, 52), 4,438; the
    # nearest built marker 6,027 from the arrival, at D-15's 6,000)
    # bounds (2026-11-24): (16, 38), (112, 80) and (118, 95) stood past the map's bounds (cells 18.9-109.1): their
    # wolves spawned where no party walks; moved in (check_reach.py reach.spawn)
    markers('pop:woods_wolves', [(100, 54, 2, 1.5), (90, 66, 2, 1.5), (105, 64, 2, 1.5), (86, 91, 2, 1.5),
                                 (106, 78, 2, 1.5), (107.5, 86, 1, 1), (97, 100, 1, 1), (104, 24, 1, 1),
                                 (94, 94, 1, 1)], 1)
    village_doors = [d[2] for d in doors_out if d[0] != 'building:nibbler_hollow']
    d142_enforce(areas, village_doors)
    for a in areas:
        c = a['circle']['at']
        near = min(math.hypot(c[0] - d[0], c[1] - d[1]) for d in village_doors)
        if near * 512 < 2500:
            raise SystemExit('monsters within 2,500 of a village door: %s %s' % (a['id'], c))
        # D-25, D-138: no marker's circle within 2,000 of a hole's return spot (was 512 for the trolls)
        for key, (pit, arr, fac) in HOLES.items():
            dd = (math.hypot(c[0] - arr[0], c[1] - arr[1]) - a['circle']['r']) * 512
            if dd < 2000:
                raise SystemExit('D-138: a marker circle within 2,000 of the %s return spot: %s %s' % (key, a['id'], c))
        # D-85: no marker within missile range (5,120) of an edge arrival
        for edge in (WEST_START, EAST_START):
            if math.hypot(c[0] - edge[0], c[1] - edge[1]) * 512 < 5120 + a['circle']['r'] * 512:
                raise SystemExit('D-85: a marker within 5,120 of an edge arrival: %s %s' % (a['id'], c))
        if math.hypot(c[0] - PARLEY[0], c[1] - PARLEY[1]) * 512 < 1500:
            raise SystemExit('a marker within 1,500 of the parley fire: %s' % c)
    areas += [
        {'id': 'zone:west_edge', 'kind': 'keep_clear', 'polygon': [[17, 54], [30, 54], [30, 65], [17, 65]],
         'notes': 'The D1 arrival.'},
        {'id': 'town:sprite_village', 'kind': 'keep_clear', 'polygon': [[17, 78], [41, 78], [41, 100], [17, 100]],
         'notes': 'The village and its buffer.'},
        {'id': 'zone:bark_glade', 'kind': 'keep_clear', 'polygon': [[34, 67], [48, 67], [48, 82], [34, 82]],
         'notes': 'The great tree, Nibbler, the temple door.'},
        {'id': 'zone:mine_mouth', 'kind': 'keep_clear', 'polygon': [[30, 28], [38, 28], [38, 35], [30, 35]]},
        {'id': 'zone:pass_saddle', 'kind': 'keep_clear', 'polygon': [[75, 32], [84, 32], [84, 41], [75, 41]],
         'notes': "Graalg's parley ground."},
        {'id': 'zone:east_meadow', 'kind': 'keep_clear', 'polygon': [[100, 38], [112, 38], [112, 49], [100, 49]],
         'notes': 'The D3 arrival.'},
        {'id': 'zone:fruit_clearing', 'kind': 'keep_clear', 'polygon': [[55, 87], [61, 87], [61, 93], [55, 93]]},
        {'id': 'zone:tower_clearing', 'kind': 'keep_clear', 'polygon': [[89, 75], [101, 75], [101, 86], [89, 86]]},
        {'id': 'zone:shrine_glade', 'kind': 'keep_clear', 'polygon': [[101, 90], [107, 90], [107, 97], [101, 97]]},
        {'id': 'zone:brink', 'kind': 'open', 'polygon': [[56, 99], [65, 99], [65, 104], [56, 104]],
         'notes': 'The lookout over the stars.'},
    ]
    views = [
        {'id': 'view:arrival', 'at': list(WEST_START), 'height': 180, 'look': [40, 70],
         'purpose': "From the D1 arrival: the road into the forest's edge, the great tree's crown south-east."},
        {'id': 'view:pass', 'at': [60, 44], 'height': 180, 'look': [84, 37],
         'purpose': 'The signature view: the caravan road climbing into Ogre Pass between the two forts.'},
        {'id': 'view:village', 'at': [42, 70], 'height': 180, 'look': [28, 88],
         'purpose': "The great tree's trunk at the left, the village lane to the treehouse trunks."},
    ]
    structures = []
    S = structures.append
    # ---------------------------------------------------------------- the treehouse village
    for (bid, index), t in sorted(tree_info.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        cx, cy = t['centre']
        fx, fy = t['out']
        rc = t['r'] / 512.0
        tag = bid.split(':')[1] + ('_%d' % index if index else '')
        # two torches, one each side of the door, 384 aside of the door's middle (the dressing rule: nothing in a box
        # 288 either side of a door; at 0.62 cell straight aside one stood 260 off it) and just outside the root
        # buttresses (depth half the radius; walls 1 and 11 beside the door have none), so they show
        lr = rc * 1.5 + 48 / 512.0
        th = math.asin(min(0.95, (384 / 512.0) / lr))
        for side, sgn in (('l', 1), ('r', -1)):
            ca, sa = math.cos(th), math.sin(th) * sgn
            at = (cx + (fx * ca - fy * sa) * lr, cy + (fy * ca + fx * sa) * lr)
            # the standing torch dec06 (MM8's model): the lantern dec07 has an indoor model only and drew nothing here
            S(deco('thing:lantern_%s_%s' % (tag, side), 'dec06', at))
        # the crown: a shipped tree model sunk into the trunk's top, and two smaller ones beside it
        top = t['top']
        S(deco('thing:crown_%s' % tag, t['crown'], (cx, cy), raise_=None))
        structures[-1].pop('raise_', None)
        structures[-1]['raise'] = top - (900 if t['crown'] == 'tree69' else 500)
        for k, (ang, name) in enumerate(((40, 'tree12'), (220, 'tree62a'))):
            a = math.radians(ang + t['turn'])
            S(deco('thing:crown_%s_%d' % (tag, k + 1), name,
                   (cx + math.cos(a) * rc * 0.55, cy + math.sin(a) * rc * 0.55)))
            structures[-1]['raise'] = top - 380
    # Sharla's stair (the only way up, D-23) to her deck and the chest on it (q-d10.treehouse)
    sh = tree_info[('building:sharla_tree', None)]
    scx, scy = sh['centre']
    deck_top = sh['deck_bottom'] + 32
    # A6's review: an open stair winding round the trunk outside the deck's rim (a walkway: a cleated plank flight
    # on side stringers, posts to the ground, open beneath, a plank handrail on the posts each side), from its foot
    # on the trunk's back (north-west, off the green) up 77 degrees of arc with a landing half way, then a short
    # level stub in onto the deck. Heights are the built ones: the village terrace 992, the deck's top 992 + 672.
    deck_z = VILLAGE_GROUND + deck_top
    arc_r = STAIR_ARC_R / 512.0
    phi_top = sh['turn'] + 110                     # the stub's way in: the trunk's back-left (west), off the green
    seg = 11.0                                     # degrees per stretch; stretch 4 (of 7) is the landing
    rises = [1, 1, 1, 0, 1, 1, 1]
    z = VILLAGE_GROUND + 4
    dz = (deck_z - z) / sum(rises)
    pts = []
    def on_ring(phi, r):
        a = math.radians(phi)
        return (scx - math.sin(a) * r, scy + math.cos(a) * r)
    for k in range(len(rises) + 1):
        phi = phi_top + seg * (len(rises) - k)
        if k:
            z += dz * rises[k - 1]
        pts.append(on_ring(phi, arc_r) + (round(z),))
    line = [[round(p[0], 3), round(p[1], 3), p[2]] for p in pts]
    S({'id': 'thing:sharla_stair', 'kind': 'walkway', 'line': line, 'width': STAIR_W, 'thickness': 48,
       'kerb': 64, 'kerb_width': 16, 'pier_every': 256, 'pier_radius': STAIR_POST, 'pier_above': 144,
       'textures': {'top': DECK, 'wall': DECK, 'under': DECK, 'post': DECK},
       'title': "Sharla's stair", 'notes': ('The one way up in the village (D-23): to the deck with the chest. An '
                                             'open plank flight round the trunk on posts.')})
    # the stair's head: a short level landing beside the flight's top end (on past it round the ring), running in onto
    # the deck; its own walkway without piers or kerbs (a walkway stands piers at every point of its line: the old
    # stub's inner end lay on the deck and its two posts stood up through the deck's edge; kerbs across its mouth
    # would bar the flight). 2 over the deck's top so the two never share a plane.
    half = STAIR_W / 2.0
    phi_h = phi_top - math.degrees((half - 4) / STAIR_ARC_R)      # its near edge 4 over the flight's end
    head = [on_ring(phi_h, (STAIR_ARC_R + half) / 512.0), on_ring(phi_h, arc_r),
            on_ring(phi_h, (sh['deck_r'] - 10) / 512.0)]
    S({'id': 'thing:sharla_stair_head', 'kind': 'walkway',
       'line': [[round(p[0], 3), round(p[1], 3), deck_z + 2] for p in head],
       'width': STAIR_W, 'thickness': 48, 'kerb': 0, 'piers': 0,
       'textures': {'top': DECK, 'wall': DECK, 'under': DECK}, 'title': "Sharla's stair"})
    # the handrails: a plank on the posts' tops each side, to the flight's top (the head lies on past its end)
    reach = (STAIR_W / 2.0 + STAIR_POST) / 512.0
    for side, sgn, upto in (('outer', 1, len(pts)), ('inner', -1, len(pts))):
        rail = []
        for k in range(upto):
            phi = phi_top + seg * (len(rises) - k)
            p = on_ring(phi, arc_r + sgn * reach)
            rail.append([round(p[0], 3), round(p[1], 3), pts[k][2] + 64 + 144 + 8])
        S({'id': 'thing:sharla_stair_rail_%s' % side, 'kind': 'walkway', 'line': rail, 'width': 64,
           'thickness': 16, 'kerb': 0, 'piers': 0, 'textures': {'top': DECK, 'wall': DECK, 'under': DECK},
           'title': "Sharla's stair"})
    ca = math.radians(sh['turn'] + 180 - 25)
    cdist = (sh['r'] + 160) / 512.0
    chest_at = (scx - math.sin(ca) * cdist, scy + math.cos(ca) * cdist)
    S({'id': 'thing:treehouse_chest', 'kind': 'chest', 'at': [round(chest_at[0], 3), round(chest_at[1], 3)],
       'raise': deck_top, 'title': "A sprite's chest", 'chest': {'level': 3, 'random_items': 1},
       'condition': {'lua': 'XeenQuests.hook("q-d10.treehouse")'},
       'notes': ("q-d10.treehouse: the robbery route's two Energy Disks (map_gives) once the village is slain; "
                 "else A3's lines.")})
    USED.add('q-d10.treehouse')
    structures[-1]['lua_before'] = None
    structures[-1].pop('lua_before')
    # rope walks between the other decks (none to Sharla's: only her stair is walked)
    def deck_edge(key, toward):
        t = tree_info[key]
        cx, cy = t['centre']
        dx, dy = toward[0] - cx, toward[1] - cy
        d = math.hypot(dx, dy)
        e = t['deck_r'] / 512.0 - 0.1
        return (cx + dx / d * e, cy + dy / d * e)
    for i, (a, b) in enumerate([(('building:sprite_guild_light', None), ('building:sprite_houses', 1)),
                                (('building:sprite_potions', None), ('building:sprite_houses', 2)),
                                (('building:sprite_houses', 1), ('building:sprite_houses', 2))]):
        p = deck_edge(a, tree_info[b]['centre'])
        q = deck_edge(b, tree_info[a]['centre'])
        h = VILLAGE_FLOOR + min(tree_info[a]['deck_bottom'], tree_info[b]['deck_bottom']) + 32
        S({'id': 'thing:rope_walk_%d' % (i + 1), 'kind': 'bridge',
           'line': [[round(p[0], 3), round(p[1], 3)], [round(q[0], 3), round(q[1], 3)]], 'width': 128, 'height': h,
           'rise': -64, 'piers': 0, 'railing': 'rope', 'rope': 24, 'railing_height': 144,
           'textures': {'deck': DECK, 'side': DECK}, 'title': 'Rope walk'})
    # the green: a ring of glowing caps, mossy stones
    for i in range(10):
        a = 2 * math.pi * i / 10
        S(deco('thing:green_cap_%d' % (i + 1), ['mushrm04', 'mushrm05', 'mushrm06'][i % 3],
               (GREEN[0] + 1.6 * math.cos(a), GREEN[1] + 1.6 * math.sin(a))))
    # ---------------------------------------------------------------- the great tree and Nibbler
    gx, gy = GREAT_C
    great_parts = trunk_parts(GREAT_R, GREAT_H, 0, 0, foot_h=GREAT_FOOT, sides=16)
    great_parts[0]['door_height'] = 352
    great_parts[0]['buttresses'] = {'count': 1, 'width': 192, 'depth': 360, 'height': GREAT_FOOT - 32,
                                    'walls': [k for k in range(2, 15)]}
    great_parts[1]['taper'] = 0.72
    fp = 4
    for p in great_parts:
        p['at'] = [fp * 256, fp * 256]
    S({'id': 'thing:great_tree', 'kind': 'building', 'at': [gx - fp / 2.0, gy - fp / 2.0], 'size': [fp, fp],
       'kit': 'timber', 'facing': 's', 'turn': GREAT_TURN, 'floor': 1000, 'title': 'The great tree of Bark',
       'parts': great_parts, 'door': {'part': 'foot', 'wall': '0'}, 'hint': 'The great tree of Bark',
       'textures': dict(TRUNK_TEX),
       **dungeon_way('dd09', 'Enter the Temple of Bark', 'Temple of Bark', 'q-d9.bark_door', inside=DD09_INSIDE,
                     arrival='entrance:d2_trunk',
                     facing=512,
                     sealed=("Behind the door a stair climbs into the dark of the trunk, and the orcs have blocked it "
                             "from above. (The Temple of Bark comes in a later part of the world.)")),
       'notes': "DD-09's door in the trunk (q-d9.bark_door, bark_key 12342). S's crown on top (D-23)."})
    gtop = GREAT_FOOT + GREAT_H
    # the crown: S's great-tree crown (world decoration xeen_greatcrown, row 4001), its 16-sided stub (radius 539,
    # corners at 0, 22.5, ... degrees about the model's +x) sunk 200 into the trunk's flat top; the trunk is turned
    # (GREAT_TURN) so that its corners meet the stub's
    S(deco('thing:great_crown', 'xeen_greatcrown', (gx, gy)))
    structures[-1]['raise'] = gtop - 200
    for i, (d, ang, r) in enumerate([('mushrm07', 20, 2.3), ('mushrm05', 70, 2.2), ('mushrm06', 140, 2.4),
                                     ('mushrm04', 200, 2.3), ('mushrm07', 225, 2.2), ('mushrm05', 320, 2.4)]):
        a = math.radians(ang)
        S(deco('thing:root_caps_%d' % (i + 1), d, (gx + r * math.cos(a), gy + r * math.sin(a))))
    nx, ny = NIBBLER_C
    S(deco('thing:nibbler_bowl', '7dec18', (nx - 0.3, ny + 0.9), title="Nibbler's bowl (empty)"))
    # ---------------------------------------------------------------- the forest
    # Sprite Falls: the Glimmerbrook over the rim into the stars
    S({'id': 'thing:sprite_falls', 'kind': 'waterfall', 'line': [[FALLS_X, RIM_Y - 0.3], [FALLS_X, RIM_Y + 3]],
       'top': 860, 'foot': 0, 'width': 448, 'rise': 48, 'textures': {'rock': ROOTS}, 'title': 'Sprite Falls',
       'notes': "The Glimmerbrook falls off the world's edge (D-23)."})
    S({'id': 'thing:brink_bench', 'kind': 'decoration', 'decoration': 'stump5a', 'at': [61.0, 103.0],
       'title': "The sprites' lookout",
       'effects': [msg('A bench of living root at the very edge of the world. Below, the Glimmerbrook falls and falls '
                       'into a sky full of stars, and never lands.')]})
    # places along the ways (POIs by the census; they also keep the land within 6,000 of something)
    S({'id': 'thing:woodcutter_chest', 'kind': 'chest', 'at': [40.6, 62.6], 'title': "A woodcutter's box",
       'chest': {'level': 2, 'random_items': 2}})
    S(deco('thing:woodcutter_stump', 'stump5a', (41.4, 62.2)))
    S(sign('thing:woodcutter_note', (39.9, 62.0), 'A note',
           "Nailed to the stump: 'Gone home. The trees here talk back. -- Wim'", height=192, width=128))
    structures.pop()
    S({'id': 'thing:dewdrop_spring', 'kind': 'fountain', 'at': [40.5, 100.5], 'title': 'Dewdrop Spring',
       'tiers': [[64, 24]], 'textures': {'wall': ROOTS},
       'effects': [{'add': {'var': 'SP', 'value': 100}}, {'text': 'Cold water with starlight in it. +100 Spell points'}]})
    S(sign('thing:rim_cairn', (20.5, 102.6), 'A cairn',
           'Scratched on the top stone: HERE THE WORLD ENDS. MIND THE STEP.', height=160, width=128))
    S(sign('thing:milestone', (106.5, 40.6), 'A milestone',
           'SANDCASTER. Under it, newer: OGRES IN THE PASS. PAY OR GO ROUND. There is no round.', height=192,
           width=128))
    S(deco('thing:whispering_stone', 'rock16', (75.4, 65.4), title='The Whispering Stone',
           effects=[{'text': "You put your ear to the stone. It whispers: 'Beneath.' Then, rudely: 'Go away.'"}]))
    S({'id': 'thing:glimmer_pool', 'kind': 'well', 'at': [61.0, 51.0], 'title': 'The Glimmer Pool',
       **daily('d2_glimmer_pool', [{'add': {'var': 'LuckBonus', 'value': 20}}, {'text': '+20 Luck until you rest.'}],
               'The water is cool and refreshing.')})
    for i, at in enumerate([(72, 21.5), (80, 21), (88, 22.5), (77, 54), (76.5, 61.5), (75.5, 49.5), (108, 22)]):
        # F59 (2026-11-25, town_fit_check decorations.slope): the fourth cluster stood 26 over its rim on the pass's
        # south slope; sunk into the slope as level_pads.py sinks a rock (a crystal is not one of its natural words)
        S(deco('thing:landmark_crystals_%d' % (i + 1), 'crclstr', at, **({'raise': -32} if i == 3 else {})))
    S({'id': 'thing:footbridge', 'kind': 'bridge', 'line': [[46.5, 70], [50.5, 70]], 'width': 256, 'rise': 32,
       'kerb': 32, 'textures': {'deck': DECK}, 'title': 'Footbridge'})
    # D-170 (2026-11-25): square across the Glimmerbrook on y 48, the road with it (LOG_BRIDGE). The studio lays the
    # brook two cells wide and its water falls 64 a cell north to south here: the old deck crossed it on the slant,
    # its east end ran on beside the brook's higher water (1,312 at y 46) and lay on it, wherever that end was put.
    # The east end stands on the node line x 53 (the caravan road grades the nodes past it, (54, 47) to 1,344, after
    # the end's pad), 24 over the pad (`raise`; at 16 its north corner lay on the road's grade)
    S({'id': 'thing:log_bridge', 'kind': 'bridge', 'line': LOG_BRIDGE, 'width': 448, 'rise': 32, 'raise': 24,
       'kerb': 48, 'textures': {'deck': DECK}, 'title': 'Log bridge'})
    # the troll holes (q-d13.troll_holes): pits in the forest floor, one into each pocket of DD-11
    for key, (pit, arr, fac) in HOLES.items():
        S({'id': 'thing:%s_hole' % key, 'kind': 'hatch', 'form': 'pit', 'at': list(pit), 'height': 48,
           'size': [512, 512],
           'textures': {'wall': '7dirttyl', 'door': '7solid01'}, 'title': 'Troll Hole', 'hint': 'Troll Hole',
           **dungeon_way(key, 'Troll Hole', 'Troll Hole', 'q-d13.troll_holes', inside=HOLE_INSIDE[key], facing=0,
                         arrival='entrance:d2_hole',
                         sealed='The hole is plugged a little way down with earth and bones. Something below snores.'),
           'notes': 'DD-11%s (A7): one way in and out per pocket.' % key[-1].upper()})
    S(deco('thing:dd11b_pack', '7dec41', (72.0, 85.4), title="A dead adventurer's pack"))
    S({'id': 'thing:dead_adventurer', 'kind': 'chest', 'at': [72.5, 85.0], 'title': "A dead adventurer's pack",
       'chest': {'level': 3, 'random_items': 2}})
    for i, at in enumerate([(59.0, 77.3), (61.2, 74.8), (69.0, 85.4), (71.2, 82.8), (66.0, 99.2), (68.4, 96.8)]):
        S(deco('thing:hole_bones_%d' % (i + 1), ['7dec18', 'dec05'][i % 2], at))
    # the Forbidden Fruit hut and its basket of four fruits (each eaten once): +2 to a stat and a condition
    # A6's review: a small hut (Darkside's poor grade: Ravenshore's boulder stone between dark timber posts under
    # mossy slate), its front open east to the brink path, a plank counter with the fruit along its south wall and
    # baskets beside it (never before the opening)
    HUT = (55.2, 88.4, 1.4, 1.5)                    # x, y, width, depth in cells
    hx, hy, hw, hd = HUT
    S({'id': 'thing:fruit_hut', 'kind': 'building', 'at': [hx, hy], 'size': [hw, hd], 'kit': 'poor',
       'facing': 'e', 'door': 'none', 'title': 'A hut in the clearing',
       'parts': [{'id': 'hut', 'at': [64, 64], 'size': [round(hw * 512) - 128, round(hd * 512) - 128],
                  'wall_height': 256, 'posts': 32, 'post_every': 352, 'sill': 208, 'sill_walls': ['n', 's', 'w'],
                  'roof': 'gable', 'ridge_along': 'ew', 'roof_pitch': 40, 'eaves': 48, 'windows': 'none',
                  'textures': {'sill': 't06a01', 'wall': 't06a01', 'window': 't06a01', 'door': 't06a03',
                               'post_left': 't06a09', 'post_right': 't06a08', 'post': 't06a10', 'trim': 't06a10',
                               'roof': 'xlslatemos', 'gable': 't06a01', 'ridge': 't06a10'}}]})
    wall_s = hy + hd - 64 / 512.0                   # the south wall's outer face
    counter = (hx + hw / 2.0 - 0.05, wall_s + 0.14)
    S({'id': 'thing:fruit_counter', 'kind': 'platform', 'at': [round(counter[0], 3), round(counter[1], 3)],
       'size': [384, 112], 'height': 80, 'textures': {'wall': DECK, 'top': DECK}, 'title': 'A plank counter'})
    # a pair of barrels by the wall beyond the counter's west end (the only outdoor basket and fruit models the
    # engine binds are the barrel and the food bowl: unbound decorations draw nothing outdoors)
    S(deco('thing:fruit_barrel_1', 'bigbarel', (counter[0] - 0.53, wall_s + 0.1)))
    S(deco('thing:fruit_barrel_2', 'bigbarel', (counter[0] - 0.7, wall_s + 0.1)))
    # the source's fruit lines (aaze0012, the C4 huts), the +10 stats scaled to +2 (MAPS D2)
    FRUITS = [('coconut', 'a coconut', 'BasePersonality', 'Insane',
               "You realize that you shouldn't have eaten the coconut of confusion. (+2 Personality, permanent)"),
              ('plum', 'a plum', 'BaseSpeed', 'Unconscious',
               'Yuk! The plum of unconsciousness. (+2 Speed, permanent)'),
              ('fig', 'an orange', 'BaseIntellect', 'Asleep',
               'Yuk! The orange of sleepiness. (+2 Intellect, permanent)'),
              ('pear', 'a pear', 'BaseEndurance', 'Paralyzed',
               'Yuk! The pear of paralysis. (+2 Endurance, permanent)')]
    for i, (k, name, stat, cond, text) in enumerate(FRUITS):
        # on the counter: four food bowls (foodbowl, the engine's outdoor bowl model)
        S(deco('thing:fruit_%s' % k, 'foodbowl',
               (counter[0] - 0.27 + 0.18 * i, counter[1]), raise_=None,
               title='Forbidden Fruit: %s' % name, once=True,
               effects=[{'add': {'var': stat, 'value': 2}}, {'set': {'var': cond, 'value': 1}}, {'text': text}]))
        structures[-1].pop('raise_')
        structures[-1]['raise'] = 80
    S(sign('thing:fruit_sign', (counter[0] + 0.5, wall_s + 0.12), 'A label',
           'Inside the hut you find a basket labeled "Forbidden Fruit".', height=192, width=128))
    # the fairy ring: tall glowing caps in a ring; inside, healing. 2026-11-24: Xeen's own xeen_fairycap (MM6's cap
    # about 200 high, lit pale green); the 64-high mushrm04/06/07 sprites were lost in the grass from 1.8 cells
    for i in range(9):
        a = 2 * math.pi * i / 9
        S(deco('thing:fairy_cap_%d' % (i + 1), 'xeen_fairycap',
               (FAIRY[0] + 1.1 * math.cos(a), FAIRY[1] + 1.1 * math.sin(a))))
    S(deco('thing:fairy_ring', 'mushrm05', FAIRY, title='The fairy ring',
           effects=[{'add': {'var': 'HP', 'value': 200}}, {'set': {'var': 'PoisonedGreen', 'value': 0}},
                    {'text': 'The caps glow brighter as you step into the ring. +200 Hit points; poison cured.'}]))
    # texture fit (the user, 2026-11-20): hkm3b is a one-storey panel (a skull frieze over a bone band) that tiled up
    # the shaft; the seamless ashlar cswl128 instead
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [36, 51], 'height': 768, 'title': 'Obelisk',
       'textures': {'wall': OBELISK_STONE},
       'effects': hook('obelisks.d2')})
    # ---------------------------------------------------------------- the foothills
    S({'id': 'thing:dd10b_adit', 'kind': 'doorway', 'at': [DD10B[0], DD10B[1] + 0.2], 'floor': 1700,
       'height': 320, 'width': 256, 'depth': 256, 'hood': 64, 'textures': {'door': '7solid01', 'wall': DECK},
       'title': 'Gemstone Mines', 'hint': 'Gemstone Mines',
       **dungeon_way('dd10b', 'Gemstone Mines', 'Gemstone Mines', inside=DD10B_INSIDE, facing=512,
                     arrival='entrance:adit',
                     sealed='The adit is shored shut with new timbers. Tool marks, and a chalked sign: CLOSED.'),
       'notes': "DD-10B Gemstone Mines' east adit (A7/A8): a timbered door in the foothill rock face."})
    for i, (d, at) in enumerate([('rock16', (32.6, 32.6)), ('rock16', (35.6, 32.8)), ('7dec41', (36.2, 31.8))]):
        S(deco('thing:adit_spoil_%d' % (i + 1), d, at))
    S(deco('thing:crystal_seam', 'crclstr', (48.0, 28.0), title='A seam of glowing crystal',
           condition={'stat': {'name': 'BaseMight', 'at_least': 30}}, once=True,
           effects=[{'gold': 1500}, {'text': 'You chip a handful of glowing crystals out of the seam. (+1,500 gold)'}],
           else_effects=[{'text': 'The crystal is set hard in the rock. (Might 30)'}]))
    for i, at in enumerate([(47.4, 27.6), (48.6, 28.5), (47.8, 28.7)]):
        S(deco('thing:seam_crystal_%d' % (i + 1), ['crys5', 'crys6', 'crys5'][i], at))
    S(deco('thing:genie_lamp', 'dec05', (100.0, 30.0), title="A genie's lamp",
           condition={'not': {'map_var': 'genie_lamp_rubbed'}},
           else_effects=[{'text': 'The lamp is cold. Its genie has gone back in for good.'}],
           effects=[{'set': {'var': {'map_var': 'genie_lamp_rubbed'}, 'value': 1}}, {'gold': 5000},
                    {'text': ("You rub the lamp. A genie unfolds out of it, yawns, and grants you a small wish: 5,000 "
                              "gold. 'Small wishes come true,' it says, and goes back in.")}]))
    # ---------------------------------------------------------------- Ogre Pass: the forts, the parley fire
    fort_parts = {}
    for side, (fx_, fy_), gate, gate_turn in (('west', WEST_FORT, DD13_WEST, 0), ('east', EAST_FORT, DD13_EAST, 180)):
        x0, y0, x1, y1 = fx_ - 2.4, fy_ - 2.4, fx_ + 2.4, fy_ + 2.4
        gy_ = y1 if gate_turn == 0 else y0
        if gate_turn == 0:
            line = [[fx_ + 0.55, gy_], [x1, gy_], [x1, y0], [x0, y0], [x0, gy_], [fx_ - 0.55, gy_]]
            house_at = [fx_ - 1.6, y0 + 0.35]
        else:
            line = [[fx_ - 0.55, gy_], [x0, gy_], [x0, y1], [x1, y1], [x1, gy_], [fx_ + 0.55, gy_]]
            house_at = [fx_ - 1.6, y1 - 1.95]
        intact = ['thing:%s_palisade' % side, 'thing:%s_blockhouse' % side]
        S({'id': intact[0], 'kind': 'wall', 'line': line, 'height': 416, 'thickness': 64, 'battlements': True,
           'textures': {'wall': DECK, 'top': DECK}, 'title': 'Log palisade',
           'notes': "Graalg's %s fort: hides when q-d11.%s_burned is set (D-23)." % (side, side)})
        S({'id': intact[1], 'kind': 'building', 'at': house_at, 'size': [3.2, 1.6], 'kit': 'timber', 'door': 'none',
           'facing': 's' if gate_turn == 0 else 'n', 'floor': 2000 if side == 'west' else 2150,
           'title': 'Ogre blockhouse',
           'parts': [{'id': 'b', 'at': [64, 64], 'size': [1536, 672], 'wall_height': 448, 'roof': 'gable',
                      'roof_pitch': 35, 'windows': 'none', 'textures': {'wall': DECK, 'roof': 'hhp2rf'}}]})
        S(deco('thing:%s_banner' % side, 'dec60', (fx_ + 1.9, fy_ - 1.9) if side == 'west' else (fx_ - 1.9, fy_ + 1.9),
               title='Beacon fire'))
        intact.append('thing:%s_banner' % side)
        ruin = ['thing:%s_ruin' % side]
        S({'id': ruin[0], 'kind': 'building', 'at': house_at, 'size': [3.2, 1.6], 'kit': 'timber', 'door': 'none',
           'facing': 's', 'floor': 2000 if side == 'west' else 2150, 'title': 'A burned blockhouse', 'hidden': True,
           'ruin': {'height': [64, 288], 'gaps': 0.4, 'thickness': 48, 'seed': 7 if side == 'west' else 9},
           'parts': [{'id': 'b', 'at': [64, 64], 'size': [1536, 672], 'wall_height': 448, 'roof': 'none',
                      'windows': 'none', 'textures': {'wall': 'vlcwl2'}}]})
        for k, (u, v) in enumerate([(x1, y0 + 0.8), (x1, y1 - 0.9), (x0, y0 + 1.2), (x0, y1 - 0.7),
                                    (fx_ + 1.1, y0), (fx_ - 1.0, y0), (fx_ + 1.3, y1), (fx_ - 1.4, y1)]):
            sid = 'thing:%s_char_%d' % (side, k + 1)
            S(deco(sid, ['stump5a', 'dec24x'][k % 2], (u, v), hidden=True))
            ruin.append(sid)
        fort_parts[side] = (intact, ruin)
        S({'id': 'thing:dd13_%s' % side, 'kind': 'doorway', 'at': [gate[0], gate[1] - (0.15 if gate_turn == 0 else -0.15)],
           # D-189 (2026-11-26): a built gate shows a door picture, not a black 7solid01 face (read as a texture
           # missing): a barred pair of the house kit's plank wing xvdoorw, the second leaf mirrored, each fitted
           # whole to its 160 x 384 leaf, 128 behind the frame
           'turn': gate_turn, 'floor': 2000 if side == 'west' else 2150, 'height': 384, 'width': 320, 'depth': 128,
           'leaves': 2, 'textures': {'door': {'texture': 'xvdoorw', 'fit': True, 'size': [128, 256]}, 'wall': DECK},
           'title': "Graalg's %s fort" % side,
           **dungeon_way('dd13', 'Ogre fort', 'Ogre fort',
                         sealed='The gate is barred from inside. Ogre snoring, and a smell of ogre cooking.',
                         inside=DD13_EAST_INSIDE if side == 'east' else DD13_WEST_INSIDE,
                         arrival='entrance:d2_%s' % side,
                         facing=1536 if side == 'east' else 512),
           'notes': 'DD-13 (A7): the %s fort\'s gate; stays open after the fort burns (D-23).' % side})
    reads('q-d11.pass_ogres')
    # the parley fire in the saddle: a ring of stones, Graalg's log seat, bones
    px_, py_ = PARLEY
    S(deco('thing:parley_fire', 'dec24', (px_ + 0.6, py_ + 0.6), title="Graalg's fire"))
    for k in range(8):
        a = 2 * math.pi * k / 8
        S(deco('thing:parley_stone_%d' % (k + 1), 'rock16', (px_ + 0.6 + 0.9 * math.cos(a),
                                                          py_ + 0.6 + 0.9 * math.sin(a))))
    S(deco('thing:graalg_seat', 'stump5a', (px_ - 0.5, py_ - 0.2), title="Graalg's log seat"))
    S(deco('thing:parley_bones', '7dec18', (px_ + 1.8, py_ + 1.3)))
    # Kramer's wagon below the west fort (Q-D11): a strongbox the ogres missed
    S({'id': 'thing:kramer_wagon', 'kind': 'chest', 'at': [59.0, 46.2], 'title': "Kramer's strongbox",
       'chest': {'level': 3, 'random_items': 2}})
    for i, (d, at) in enumerate([('dec24x', (58.2, 46.8)), ('7dec18', (59.8, 46.9)), ('7dec41', (58.6, 45.6))]):
        S(deco('thing:wagon_wreck_%d' % (i + 1), d, at))
    # ---------------------------------------------------------------- the Southern Woods
    S({'id': 'thing:southern_tower', 'kind': 'building', 'at': [DD06_C[0] - 1.25, DD06_C[1] - 1.25], 'size': [2.5, 2.5],
       'kit': 'castle', 'floor': 1050, 'title': 'The Southern Tower', 'facing': 's', 'turn': 180,
       'parts': [
           # D-189 and D-180 rule a (2026-11-26): a door picture (was a black 7solid01 face, read as a texture
           # missing), 192 x 384 as DD-06's way back out (was 130 x 256): the tower kit's door xvtdoor laid once over
           # the leaf (classic_kit.py, D-196; MM7's framed hkm1d showed 1.5 doors there); the rows over the door listed
           # as wall (unlisted, the kit's window filled the door's column)
           {'id': 'base', 'shape': 'round', 'at': [640, 640], 'radius': DD06_R, 'sides': 10, 'wall_height': 1280,
            'roof': 'none', 'windows': 'none', 'door_height': 384,
            'walls': {'0': [['wall', DD06_JAMB], ['door', 192], ['wall', DD06_JAMB]]},
            'upper_walls': {'0': [['wall', DD06_JAMB], ['wall', 192], ['wall', DD06_JAMB]]},
            'textures': {'wall': TOWER_STONE, 'trim': TOWER_STONE, 'window': TOWER_STONE, 'door': 'xvtdoor'}},
           {'id': 'top', 'shape': 'round', 'at': [640, 640], 'radius': DD06_R + 48, 'sides': 10, 'bottom': 1280,
            'wall_height': 512, 'roof': 'cone', 'roof_pitch': 70, 'windows': 'none',
            'textures': {'wall': TOWER_STONE, 'trim': TOWER_STONE, 'window': TOWER_STONE, 'roof': SLATE}}],
       'door': {'part': 'base', 'wall': '0'}, 'hint': 'The Southern Tower',
       **dungeon_way('dd06', 'The Southern Tower', 'The Southern Tower', 'q-d19.tower_door',
                     inside=DD06_INSIDE, facing=DD06_FACING, arrival='entrance:d2_door',
                     sealed=('The key turns, and the door opens on a wall of rubble: the stair inside has come down. '
                             '(The thieves\' den comes in a later part of the world.)')),
       'notes': "DD-06 (A7): the door needs south_tower_key 12339 (q-d19.tower_door)."})
    S(sign('thing:tower_plate', (DD06_C[0] + 0.7, DD06_C[1] - 1.1), 'A brass plate', 'NO THIEVES.', height=160,
           width=128))
    S({'id': 'thing:thieves_drop', 'kind': 'chest', 'at': [98.4, 83.4], 'title': 'A hollow stump',
       'chest': {'level': 2, 'random_items': 2}})
    S(deco('thing:drop_stump', 'stump5a', (98.0, 83.0)))
    S({'id': 'thing:shrine_ring', 'kind': 'stone_ring', 'at': [104, 93.8], 'radius': 384, 'count': 4,
       'lintel': False, 'title': 'Shrine of the Elements'})
    S(deco('thing:shrine_altar', 'crys6', (104.0, 93.8), title='Shrine of the Elements',
           condition={'not': {'map_var': 'shrine_used'}},
           effects=[{'set': {'var': {'map_var': 'shrine_used'}, 'value': 1}},
                    {'add': {'var': 'FireResistance', 'value': 5}}, {'add': {'var': 'AirResistance', 'value': 5}},
                    {'add': {'var': 'WaterResistance', 'value': 5}}, {'add': {'var': 'EarthResistance', 'value': 5}},
                    {'text': '+5 Fire, Air, Water and Earth resistance (permanent)'}],
           else_effects=[{'text': 'The four stones hum, and nothing more.'}]))
    S(deco('thing:pot_of_gold', 'rock16', (106.0, 101.0), title='A ring of rocks',
           condition={'all': [{'stat': {'name': 'PerceptionSkill', 'at_least': 4}},
                              {'not': {'map_var': 'pot_found'}}]},
           effects=[{'set': {'var': {'map_var': 'pot_found'}, 'value': 1}}, {'gold': 3000},
                    {'text': ("Under the rocks, a small iron pot full of gold, and a note: 'Finders keepers. "
                              "-- L.' (+3,000 gold)")}],
           else_effects=[{'text': 'A ring of rocks at the edge of the world.'}]))
    for i, at in enumerate([(105.5, 100.6), (106.5, 100.6), (105.6, 101.5), (106.5, 101.4)]):
        S(deco('thing:pot_rocks_%d' % (i + 1), 'rock16', at))
    # ---------------------------------------------------------------- signposts and the sealed edges
    for sid, at, arms in (
            ('sign_fork', (33, 60.8), [('Castleview', 'w'), ('Ogre Pass', 'e'), ('Bark Glade', 's')]),
            ('sign_glade', (43, 69), [('Treehouse village', 'w'), ('The great tree', 's'), ('Southern Woods', 'e')]),
            ('sign_south', (91, 58.8), [('Ogre Pass', 'n'), ('Southern Tower', 's'), ('Bark Glade', 'w')]),
            ('sign_pass', (80.2, 38.4), [('Castleview', 'w'), ('Sandcaster', 'e')])):
        S({'id': 'thing:%s' % sid, 'kind': 'sign', 'at': list(at), 'height': 256,
           'arms': [{'title': t, 'toward': d} for t, d in arms]})
    if not D1_LIVE:
        S(sign('thing:west_road_end', (3.0, 61.0), 'Sign',
               'The road west to Castleview is closed by a rockfall. Turn back.'))
    if not D3_LIVE:
        S(sign('thing:east_road_end', (124.5, 45.0), 'Sign',
               'The caravan road east to Sandcaster is washed out. Turn back.'))
    # ---------------------------------------------------------------- actors
    actors = []
    # A2's relations.yml decides the ogres' mood by the quest bits (xeen_ogres_pass long, friendly after 113221, long
    # again after 113222; xeen_ogres_graalg friendly until 113222): the actors carry no `hostile` of their own
    def place(row, at, count, spread, group, **kw):
        a = {'monster': str(row), 'at': list(at), 'count': count, 'spread': spread, 'group': group}
        a.update(kw)
        actors.append(a)
    # Graalg's 22 pass ogres, hostile at load (D-23): the fort yards and two road groups
    wy = WEST_FORT[1] + 1.0
    place(ROW['ogre'], (WEST_FORT[0], wy), 5, 1.0, G_WEST)
    place(ROW['ogre_brute'], (WEST_FORT[0] - 1.2, wy + 0.2), 2, 0.5, G_WEST)
    place(ROW['ogre_chief'], (WEST_FORT[0] + 1.2, wy + 0.2), 1, 0, G_WEST)
    ey = EAST_FORT[1] - 1.0
    place(ROW['ogre'], (EAST_FORT[0], ey), 5, 1.0, G_EAST)
    place(ROW['ogre_brute'], (EAST_FORT[0] - 1.2, ey - 0.2), 2, 0.5, G_EAST)
    place(ROW['ogre_chief'], (EAST_FORT[0] + 1.2, ey - 0.2), 1, 0, G_EAST)
    # D-142 (2026-11-25, F64): the road groups 4,096 from DD-13's gate exits (were 3,119 and 3,132), 3 cells down
    # the road on each side (from (65.5, 40.0) and (93.5, 40.6))
    place(ROW['ogre'], (62.5, 42.5), 2, 0.6, G_ROAD_W)
    place(ROW['ogre_brute'], (63.4, 41.9), 1, 0, G_ROAD_W)
    place(ROW['ogre'], (96.5, 42.2), 2, 0.6, G_ROAD_E)
    place(ROW['ogre_brute'], (97.4, 41.8), 1, 0, G_ROAD_E)
    for a in actors:
        if a['group'] in (G_ROAD_W, G_ROAD_E):
            for gate in ((72, 37), (87, 41), WEST_START, EAST_START):   # entrance:dd13_west/east, the edges
                if (math.hypot(a['at'][0] - gate[0], a['at'][1] - gate[1]) - a['spread']) * 512 < 4096 + 64:
                    raise SystemExit('D-142: a road ogre group within 4,096 of %s: %s' % (gate, a))
    # Graalg and his two Brutes: their own faction, peaceful at the parley fire
    actors.append({'monster': str(ROW['graalg']), 'npc': 5108, 'at': [PARLEY[0], PARLEY[1]], 'spread': 0,
                   'group': G_GRAALG})
    for at in ((PARLEY[0] - 0.9, PARLEY[1] - 0.7), (PARLEY[0] + 0.9, PARLEY[1] - 0.7)):
        actors.append({'monster': str(ROW['graalg_brute']), 'at': list(at), 'spread': 0, 'group': G_GRAALG})
    # the eight village sprites (X2's rows), peaceful until the robbery
    # A2's village rows (11537, 11538, faction xeen_sprites_village: friendly, hostile after q-d10.robbery 113203)
    actors.append({'monster': str(ROW['medusa_sprite']), 'at': list(GREEN), 'count': 5, 'spread': 2.0,
                   'group': G_VILLAGE})
    actors.append({'monster': str(ROW['killer_sprite']), 'at': [GREEN[0] - 0.5, GREEN[1] - 1.0], 'count': 3,
                   'spread': 1.5, 'group': G_VILLAGE})
    for a in actors:
        if a['group'] in PASS_GROUPS:
            d = math.hypot(a['at'][0] - PARLEY[0], a['at'][1] - PARLEY[1]) * 512
            if d < 1500:
                raise SystemExit('a hostile marker within 1,500 of the parley fire: %s' % a)
    relations = []
    # ---------------------------------------------------------------- events: hostility, the forts' state
    reads('q-d10.sprites_hostile')
    # q-d10.sprites_hostile is A2's relations too (xeen_sprites_village long after 113203)
    events = [
        {'id': 'evt:sprites_slain', 'trigger': 'timer', 'every': 5, 'once': True,
         'condition': {'kills': {'group': G_VILLAGE}}, 'effects': hook('q-d10.sprites_slain'),
         'notes': "q-d10.sprites_slain: every village sprite dead."},
    ]
    for side, qb in (('west', 'west_fort_burned'), ('east', 'east_fort_burned')):
        intact, ruin = fort_parts[side]
        events.append({'id': 'evt:%s_fort_burned' % side, 'trigger': 'load', 'condition': {'qbit': qb},
                       'effects': [{'hide': intact}, {'show': ruin}],
                       'notes': 'q-d11.%s: the %s fort outside as a charred ruin (D-23); its gate stays.' % (qb, side)})
        # AU's xeen_fire_ignite once, the first time the party is back on D2 after the fort burned (named map
        # variable, as D1's Kalindra phase sound): the blaze is heard over the pass, not on every load
        fx_, fy_ = WEST_FORT if side == 'west' else EAST_FORT
        X_, Y_ = W(fx_, fy_)
        var = '%s_fort_fire_heard' % side
        events.append({'id': 'evt:%s_fort_ignite' % side, 'trigger': 'load', 'condition': {'qbit': qb},
                       'effects': [{'lua': 'if evt.GetMapVar("%s", 0) == 0 then evt.SetMapVar("%s", 1) '
                                           'evt.PlaySoundName("xeen_fire_ignite", %d, %d, %d) end'
                                           % (var, var, X_, Y_, 2000 if side == 'west' else 2150)}],
                       'notes': "AU (2026-11-20): xeen_fire_ignite at the %s fort once after it burns (map variable "
                                "%s)." % (side, var)})
    # the treehouse chest's robbery branch gives the two Energy Disks (q-d10.treehouse map_gives)
    for s in structures:
        if s['id'] == 'thing:treehouse_chest':
            s['effects'] = [{'give_item': 'energy_disk'}, {'give_item': 'energy_disk'}]
    # ---------------------------------------------------------------- scatter and ground
    scatter = []
    def sc(sid, deco_, count, poly=None, circle=None, clusters=None, spacing=None, line=None, steep=None):
        e = {'id': sid, 'decoration': deco_, 'count': count}
        if poly: e['polygon'] = poly
        if circle: e['circle'] = circle
        if line: e['line'] = line
        if clusters: e['clusters'] = clusters
        if spacing: e['spacing'] = spacing
        if steep: e['steep'] = True
        scatter.append(e)
    def stand(sid, poly, kinds_, per_100, spacing, close=0.1, edge=True, close_spacing=1.0):
        for piece in minus_clearings(poly):
            n = int(round(per_100 * K.poly_area(piece) / 100.0))
            if n < 1:
                continue
            e = {'id': sid, 'count': n, 'polygon': piece, 'spacing': spacing, 'close_share': close,
                 'close_spacing': close_spacing, 'spacing_group': 'trees'}
            if len(kinds_) == 1:
                e['decoration'] = list(kinds_)[0]
            else:
                e['kinds'] = dict(kinds_)
            scatter.append(e)
    BROAD = {'tree12': 3, 'tree62a': 3, 'tree10': 2, 'tree18': 2, 'tree11': 2}
    FOREST_W = [[0.5, 67], [16, 66], [33, 64], [36, 66], [34, 72], [33, 79], [18, 79], [18, 99], [40, 99], [40, 86],
                [47, 86], [50, 103.5], [0.5, 103.5]]
    # A6's review: the Sprite Forest denser and darker round the village, the great tree and the troll holes:
    # closer spacing, the dark crowns (tree60a, tree62a, tree12, the fir tree30, tree61a) over the bright tree10/
    # tree11 and the autumn tree18 (MM8 trees_broadleaf/review/sprites.png)
    DARK = {'tree60a': 3, 'tree62a': 3, 'tree12': 2, 'tree30': 2, 'tree61a': 1, 'tree10': 1}
    stand('scatter:forest_west', FOREST_W, DARK, 30.0, 1.05, close=0.15, close_spacing=0.8)
    # the great tree's glade: woods close round it (its clearing, the lane, the track and the brook stay open)
    stand('scatter:bark_glade', [[34, 66], [48, 66], [48, 86], [34, 86]], DARK, 26.0, 1.1, close=0.15,
          close_spacing=0.85)
    FOREST_E = [[50, 72], [66, 69.5], [78, 70], [81.5, 72], [81.5, 103.5], [52, 103.5], [48, 88]]
    stand('scatter:troll_country', FOREST_E, DARK, 28.0, 1.05, close=0.15, close_spacing=0.8)
    WOODS = [[86, 50], [100, 50], [127.5, 52.5], [127.5, 103.5], [82.5, 103.5], [82.5, 70], [86, 60]]
    stand('scatter:southern_woods', WOODS, {'tree60a': 2, 'tree12': 2, 'tree30': 2, 'tree62a': 2, 'tree10': 1},
          26.0, 1.1, close=0.15, close_spacing=0.85)
    GLADES = [[44, 48], [52, 44], [60, 41], [60, 46], [70, 48], [72, 56], [73, 62], [56, 63], [46, 60], [40, 56]]
    stand('scatter:glades', GLADES, {'tree62a': 2, 'tree25': 2, 'tree11': 1}, 4.0, 2.2)
    FOOT = [[0.5, 21], [14, 19], [26, 16], [38, 17], [50, 16], [62, 17], [72, 18], [74, 30], [60, 30], [60, 40],
            [52, 44], [44, 48], [36, 52], [24, 54], [0.5, 54]]
    stand('scatter:foothill_trees', FOOT, {'tree25': 3, 'tree62a': 1, 'tree12': 1}, 2.4, 2.4)
    sc('scatter:foothill_rocks', 'rock16', 50, FOOT, clusters=16)
    sc('scatter:foothill_rocks', '6rock07', 40, FOOT, clusters=12, steep=True)
    sc('scatter:foothill_crystals', 'crys5', 18, FOOT, clusters=7)
    sc('scatter:foothill_crystals', 'crys6', 12, FOOT, clusters=5)
    RANGE = [[0.5, 0.5], [127.5, 0.5], [127.5, 21], [0.5, 21]]
    sc('scatter:range_rocks', '6rock07', 60, RANGE, clusters=18, steep=True)
    sc('scatter:range_crystals', 'crclstr', 14, RANGE, clusters=6)
    PASS = [[60, 30], [98, 30], [100, 48], [86, 48], [70, 48], [60, 46]]
    sc('scatter:pass_rocks', 'rock16', 40, PASS, clusters=12)
    sc('scatter:pass_rocks', '6rock07', 30, PASS, clusters=10, steep=True)
    stand('scatter:pass_trees', PASS, {'tree25': 2, 'tree62a': 1}, 1.6, 2.6)
    SPUR = [[72, 48], [88, 48], [86, 58], [80, 65], [73, 62], [70, 54]]
    sc('scatter:spur_rocks', '6rock07', 30, SPUR, clusters=10, steep=True)
    EAST = [[98, 30], [104, 19], [127.5, 22], [127.5, 52], [100, 50], [100, 48]]
    stand('scatter:east_trees', EAST, {'tree25': 2, 'tree12': 1, 'tree62a': 1}, 3.0, 2.2)
    sc('scatter:east_rocks', 'rock16', 30, EAST, clusters=10)
    # the forest floor (A6's review): undergrowth of dark shrubs (plant32), ferns (plant05, the fern bush bush03),
    # a few stumps (plant47), and clusters of caps
    for sid, poly in (('w', FOREST_W), ('e', FOREST_E), ('s', WOODS)):
        sc('scatter:undergrowth_%s' % sid, 'plant32', 110, poly, clusters=36)
        sc('scatter:undergrowth_%s' % sid, 'plant05', 130, poly, clusters=40)
        sc('scatter:undergrowth_%s' % sid, 'bush03', 45, poly, clusters=18)
        sc('scatter:plants_%s' % sid, 'plant47', 30, poly, clusters=12)
        sc('scatter:caps_%s' % sid, 'mushrm01', 140, poly, clusters=34)
        sc('scatter:caps_%s' % sid, 'mushrm02', 60, poly, clusters=20)
        sc('scatter:caps_%s' % sid, 'mushrm03', 90, poly, clusters=24)
    # (A6's review: the caps along the brook's line stood in its water; the forest's clusters stand in for them)
    # rocks along the rim's lip, stacks below
    sc('scatter:lip_rocks', 'rock16', 40, line=[[1, RIM_Y - 0.6], [126.5, RIM_Y - 0.6]])
    scatter.append({'id': 'scatter:sea_stacks', 'decoration': '6rock07', 'count': 14, 'on': 'water',
                    'polygon': [[4, RIM_Y + 2], [124, RIM_Y + 2], [124, 112], [4, 112]]})
    ground = [
        {'material': 'grass', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'The forest floor and the meadows: grass (darkened in D2\'s terrain materials).'},
        {'material': 'dirt', 'polygon': [[0, 0], [128, 0], [128, 22], [0, 22]], 'notes': 'The range: bare stone.'},
        {'material': 'dirt', 'polygon': [[69, 31], [75, 31], [75, 37], [69, 37]], 'notes': 'The west fort: trodden.'},
        {'material': 'dirt', 'polygon': [[84, 42], [90, 42], [90, 48], [84, 48]], 'notes': 'The east fort: trodden.'},
        {'material': 'dirt', 'polygon': [[76, 34], [82, 34], [82, 39], [76, 39]], 'notes': "Graalg's saddle."},
        {'material': 'dirt', 'polygon': [[31, 30], [37, 30], [37, 35], [31, 35]], 'notes': "The adit's spoil."},
        {'material': 'dirt', 'steeper_than': 560, 'polygon': [[0, 0], [128, 0], [128, RIM_Y], [0, RIM_Y]],
         'notes': 'Bare rock on the steep slopes.'},
        {'material': 'dirt', 'polygon': [[26, 86], [33, 86], [33, 92], [26, 92]], 'notes': 'The village green: moss '
         'and trodden earth.'},
    ]
    for line in PATHS:
        ground.append({'material': 'dirt', 'line': line, 'width': 1, 'notes': 'a forest track'})
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('D2 Sprite Forest and Ogre Pass, written by output/studio_cal/d2/tools/gen.py. Cells [x, y], x east, '
                  'y south. Heights are map units above the stars below the rim (0): the forest floor 920-1,100 to the '
                  'rim at y 104, the foothills 1,200-2,100, Ogre Pass\'s saddle 2,050, the Gemstone Range to 4,400.'),
        'frame': {'playable': [19, 19, 90, 90], 'edges': edges,
                  'edge': {'height': 1500, 'west': 1000, 'south': 0, 'east': 1300}, 'rim': rim},
        'heights': heights, 'water': water, 'roads': roads, 'districts': districts, 'points': points,
        'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground, 'structures': structures,
        'actors': actors + V.sketch_actors('D2'), 'relations': relations + V.relations('D2'),
        'events': events,
    }
    if not relations:
        sketch.pop('relations')
    atmosphere = {'format': 0,
                  'notes': ("Darkside's sky by the continent (7: xeendark1; A3's Lua sets the failing-sun stages); "
                            "no weather (D2's brief).")}

    def half(v):
        return round(v * 2) / 2.0
    for r in roads:
        r['line'] = [[half(a), half(b)] for a, b in r['line']]
    for g in ground:
        if 'line' in g:
            g['line'] = [[half(a), half(b)] for a, b in g['line']]
        if 'polygon' in g:
            g['polygon'] = [[round(a), round(b)] for a, b in g['polygon']]
    for d in districts:
        d['polygon'] = [[round(a), round(b)] for a, b in d['polygon']]
    for a in areas:
        if 'circle' in a:
            a['circle']['at'] = [round(v) for v in a['circle']['at']]
        if 'polygon' in a:
            a['polygon'] = [[round(x), round(y)] for x, y in a['polygon']]
    for q in points:
        q['at'] = [round(x) for x in q['at']]
    for v in views:
        v['at'] = [round(x) for x in v['at']]
        v['look'] = [round(x) for x in v['look']]
    missing = sorted(set(HOOKS) - USED)
    if missing:
        raise SystemExit('hooks with map D2 not wired: %s' % missing)

    def dump(folder, name, data):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)
    dump(OUT, 'project.yml', project)
    dump(OUT, 'plan.yml', plan)
    # AU's outdoor bed (E9, merge point 20; devdocs/xeen/AUDIO.md "Outdoor beds"): the scene's ambient_sounds
    sketch['sounds'] = (sketch.get('sounds') or []) + yaml.safe_load(open(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '../common/beds/d2.yml')))['sounds']
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    import house_doors as HD
    import entrance_screens as ES     # F16/D-90 (s32): each dungeon door's trans.txt row in its entrance window
    for _note in HD.double_doors_sketch(sketch) + HD.bury_mouths_sketch(sketch) + HD.blind_mouths_sketch(sketch):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sketch, 'd2'):
        print('wild:', _note)
    # The classic kits (2026-11-24): Clouds of Xeen's own walls on the map's buildings (classic_kit.yml)
    import classic_kit as CK
    for _note in CK.apply(sketch, 'd2'):
        print(_note)
    print('entrance screens:', ES.apply_sketch(sketch, 'xeen_d2'))
    dump(OUT, 'sketch.yml', sketch)
    dump(OUT, 'atmosphere.yml', atmosphere)
    dump(os.path.join(BRIEFS, 'L3'), 'project.yml', project)
    dump(os.path.join(BRIEFS, 'L3'), 'plan.yml', plan)
    dump(os.path.join(BRIEFS, 'L3'), 'sketch.yml', sketch)
    dump(os.path.join(BRIEFS, 'L3'), 'atmosphere.yml', atmosphere)
    p2 = copy.deepcopy(plan)
    p2['level'] = 'L2'
    p2.pop('sketch', None)
    dump(os.path.join(BRIEFS, 'L2'), 'project.yml', project)
    dump(os.path.join(BRIEFS, 'L2'), 'plan.yml', p2)
    print('D1_LIVE', D1_LIVE, 'D3_LIVE', D3_LIVE, 'dungeons live', sorted(k for k, v in DUNGEON.items() if v))


if __name__ == '__main__':
    build()
