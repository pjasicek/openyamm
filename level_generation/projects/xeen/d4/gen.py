#!/usr/bin/env python3
"""D4 Lakeside and Blackfang: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml) and the L2
and L3 briefs beside it (L1 is the approved mock-up of 2026-11-20 and stays as it is).

The design is the approved L1 (devdocs/xeen/briefs/d4/L1, board level_generation/xeen_art/phase4/d4/) with the
decider's changes D-36: E3 (the Rimward crags' rocs) stretched north to six encounter units; POIs at most 35 and
outdoor chests at most 10; Castle Blackfang in the towers kit (Darkside: hkm2bs black rubble, the hkm3b skull frieze as
one band at a storey's top, hkm3elw yellow-glass windows once per storey and face, xtslate cones) on its crag 17,600
from the ferry jetty's end, the Isle 2,500 and more of deep water from the crag, the gatehouse at the crag's west
foot (m25.blackfang_gate, never opens, a hinged pair); the bat storm's two spots (BAT_STORM_SPOTS) wait on S's model,
their shrieks a map timer; the Fly knock-down over the crag top (Fly ended by evt.RemovePartyBuff, then m25.bat_storm);
five octopods placed in the two deep basins as swimmers (A1's outdoor water facts, merge point 18) on a home radius
(OCTOPOD_LEASH); the coven's two groups hidden on load by
q-d22.coven_gone; DD-20's shaft by the jetty, the guild riddle, DD-12, DD-23 (each sealed until its dungeon is
installed and lists the entrance); Leafpoint (MM7 Treant 453), Ector, Naomi; the Isle Ferry back (A4's 4667); the
beached boat. World: xeen. Houses: A4's source/towns/d4.yml. Hooks: A3's quest files (`map: D4`). Rows: A2's.
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
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kit as K  # noqa: E402

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/d4'
OUT = os.path.join(BRIEFS, 'L4')
STEM = 'xeen_d4'
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
WORLD = os.path.join(REPO, 'assets_dev/worlds/xeen')
XEEN_SOURCE = os.path.join(WORLD, 'source')


def live(stem, env):
    return os.path.exists(os.path.join(WORLD, 'maps', stem)) or os.environ.get(env) == '1'


_STATS = open(os.path.join(WORLD, 'data_tables/map_stats.txt')).read()


def studio_entrances(stem):
    f = os.path.join(WORLD, 'maps', stem.replace('.blv', '.studio.yml').replace('.odm', '.studio.yml'))
    if not os.path.exists(f):
        return {}
    d = yaml.safe_load(open(f)) or {}
    out = {}
    for a in d.get('arrivals') or d.get('entrances') or []:
        if isinstance(a, dict) and (a.get('id') or a.get('name')):
            out[a.get('id') or a.get('name')] = a     # oymap install writes `name` (MP17 sidecars)
    return out


# D3 Sandcaster (south; installed, A5's): the road crosses at x 88. D5 (west, y 80): not planned yet, sealed.
D3_LIVE = live('xeen_d3.odm', 'D4_D3_LIVE')
D5_LIVE = live('xeen_d5.odm', 'D4_D5_LIVE')
# a dungeon door opens when its BLV is installed, A2's map_stats row names it and its studio sidecar lists the
# entrance the door names (D-37: entrance:d4_*); until then the door shows a short sealed line (D1/D2's rule)
ENTRANCE = {'dd14': 'entrance:d4_griffin', 'dd12': 'entrance:d4_isle', 'dd20_shaft': 'entrance:d4_shaft', 'dd20_guild': 'entrance:d4_guild',
            'dd20_trapdoor': 'entrance:d4_trapdoor', 'dd23': 'entrance:d4_mouth'}


def dungeon_live(key):
    blv = 'xeen_%s.blv' % key.split('_')[0]
    env = os.environ.get('D4_%s_LIVE' % key.upper())
    if env == '1':
        return True
    return (live(blv, '_') and ('\t%s\t' % blv in _STATS) and ENTRANCE[key] in studio_entrances(blv))


DUNGEON = {k: dungeon_live(k) for k in ENTRANCE}
# A4's Isle Ferry back (house 4667 at poi:isle_boat): live when the house is in A4's town file
TOWN = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'towns/d4.yml')))
HOUSE = {h['door']: (h['id'], h['name']) for h in TOWN['houses']}
ISLE_FERRY_DOOR = next((k for k in ('thing:isle_ferry', 'poi:isle_boat') if k in HOUSE), None)
HOUSE_LIVE = ISLE_FERRY_DOOR is not None
# S's bat storm (D-36 (1)): two copies of one looping decoration once the model exists in the world's bindings
_DECOS = yaml.safe_load(open(os.path.join(WORLD, 'models/decorations.yml')))['decorations']
BAT_STORM_MODEL = next((str(d.get('name')) for d in _DECOS if 'bat' in str(d.get('name')).lower()), None)

# ---------------------------------------------------------------------------------------------------------------
# A3's hooks on D4 (quest files' `hooks` with `map: D4`); every one must be used (checked at the end)
HOOKS = {}
for _f in sorted(os.listdir(os.path.join(XEEN_SOURCE, 'quests'))):
    _q = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'quests', _f)))
    for _k, _v in (_q.get('hooks') or {}).items():
        if isinstance(_v, dict) and _v.get('map') == 'D4':
            HOOKS['%s.%s' % (_f[:-4], _k)] = _v
USED = set()


def use(name):
    assert name in HOOKS, name
    USED.add(name)
    return name


def hook(name):
    return [{'lua': 'XeenQuests.hook("%s")' % use(name)}]


def hcall(name):
    return 'XeenQuests.hook("%s")' % use(name)


# A2's rows (data_tables/monster_data.txt)
ROW = {'witch': 11170, 'coven_witch': 11171, 'coven_mother': 11172, 'octopod': 11470, 'great_octopod': 11471,
       'treant': 453, 'peasant_m': 361, 'peasant_f': 377, 'mage': 611}
SLOT = {'gargoyles': 'Xeen Mountain Gargoyle', 'rocs': 'Xeen Roc', 'coven': 'Xeen Coven'}
QBIT = {'cache_dug': 112484, 'coven_broken': 113441, 'coven_joined': 113449, 'lucio_open': 111600,
        'mirror_lakeside': 119010, 'obelisk_dark_4': 115053, 'riddle_answered': 113442, 'woodpile_found': 113421,
        'head_witch_slain': 113447, 'blackfang_done': 111503}
ITEMS = {'ectors_ring': 12522, 'lost_souls_key': 12344, 'real_treasure_map': 12356}
G_CIRCLE, G_REEDS = 1, 2
G_OCTOPODS = (3, 4, 5, 6, 7)
G_NAOMI, G_SLIBO, G_ECTOR, G_LEAFPOINT = 8, 9, 10, 11
NPC = {'slibo': 5317, 'naomi': 5318, 'leafpoint': 5319, 'ector': 5320}
HOUSE_MIRROR = HOUSE['thing:lk_mirror'][0]


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def dist_to_line(px, py, line):
    return min(K.seg_dist((px, py), a, b) for a, b in zip(line, line[1:]))


def poly_dist(p, poly):
    return min(K.seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def msg(text):
    return {'lua': 'evt.SimpleMessage(%s)' % lstr(text)}


def lstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')


def sign(sid, at, title, text=None, height=224, width=160, effects=None, **kw):
    s = {'id': sid, 'kind': 'sign', 'at': [round(at[0], 3), round(at[1], 3)], 'height': height, 'width': width,
         'title': title, 'effects': effects if effects is not None else [msg(text)]}
    s.update(kw)
    return s



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


def bays(n, window_at=None, word='wall'):
    """A wall's bays from the left: `n` plain bays with one window (a picture once, whole) at `window_at`."""
    out = [word] * n
    if window_at is not None:
        out[window_at] = 'window'
    return out


# ---------------------------------------------------------------------------------------------------------------
# Land. Heights are map units above the stars below the rim (water at 0).
# ---------------------------------------------------------------------------------------------------------------
RIM_N = 24            # the world rim, north: the land ends in a cliff along y 24
RIM_E = 104           # the world rim, east: along x 104 (D3's east rim continues)
LAKE_H = 1056
TOWN_H = 1120
CRAG_TOP = 3104       # Castle Blackfang's floor on the crag top
CAMP_H = 2304
CLEARING_H = 1888
GROVE_H = 1504
ECTOR_H = 1440
LAKE = [[57, 57], [61, 55], [66, 55], [71, 56], [76, 57], [79, 59], [84, 60], [90, 60], [95, 59], [98, 61],
        [100, 64], [100, 69], [98, 72], [95, 73], [93, 76], [95, 78], [94, 80], [90, 81], [85, 81], [80, 80],
        [76, 80], [72, 81], [68, 81], [64, 80], [60, 79], [56, 76], [54, 71], [54, 65], [55, 60]]
ISLE = [[67, 66], [70, 64], [74, 64], [77, 66], [78, 69], [76, 72], [73, 74], [70, 73], [67, 71]]
SKERRY_W = [[60, 69], [62, 69], [62, 71], [60, 71]]          # whole cells: the studio's water outlines are
SKERRY_E = [[88, 69], [90, 69], [90, 71], [88, 71]]          # drawn on whole cells
ISLETS = (ISLE, SKERRY_W, SKERRY_E)
SPLIT_Y = 69.0        # the lake drawn as two bodies, north and south of y 69, notched round the islets
CRAG = [[78, 42], [84, 38], [92, 38], [96, 44], [98, 60], [95, 59], [90, 60], [84, 60], [79, 59], [77, 50]]
SNOW_RIVER = [[62, 32], [62, 34], [61, 38], [60, 42], [59, 46], [59, 50], [59, 53], [59, 56]]
TARN = [[60, 29], [63, 29], [64, 31], [63, 32], [60, 31]]
OUTFLOW = [[100, 67], [102, 67], [104, 67]]

# control heights (cells, height): L1's points and the rises between them, interpolated (inverse distance) on the
# 4-cell grid; the lake, the terraces, ridges and cliffs carry what the grid cannot
CONTROL = [
    # Magic Mountain and the north-west (its north face falls over the rim)
    (30, 36, 4100), (38, 31, 3700), (24, 30, 3500), (45, 36, 3200), (20, 42, 3000), (22, 52, 2400),
    (40, 50, 2500), (50, 45, 2400), (52, 34, 2600), (36, 43, 3000), (28, 50, CAMP_H), (33, 56, 1800),
    (46, 42, 2304), (48, 51, CLEARING_H), (44, 27, 3300), (32, 26, 3600), (52, 28, 2700),
    # the Snow River uplands and the rim corner
    (61, 30, 2300), (56, 28, 2500), (68, 28, 2400), (70, 33, 2200), (64, 40, 1900), (58, 44, 1700),
    (66, 46, 1600), (74, 44, 1800), (76, 32, 2100), (86, 30, 2000), (94, 31, 1900), (100, 38, 1824),
    (100, 30, 1950), (101, 47, 1900), (101, 55, 1700), (72, 38, 2000), (82, 34, 2050), (90, 35, 1950),
    # Blackfang's crag
    (86, 48, CRAG_TOP), (83, 46, CRAG_TOP), (90, 46, CRAG_TOP), (88, 51, CRAG_TOP), (84, 51, 3000),
    (92, 50, 3000), (82, 55, 2500), (93, 55, 2600), (88, 56, 2600), (86, 41, 2700), (92, 42, 2600),
    # the north shore, the gatehouse
    (60, 52, 1150), (68, 54, 1130), (77, 53, 1184), (64, 52.5, 1140), (72, 51, 1300), (66, 49, 1450),
    # the west shore, Gull Knoll, the reeds
    (53, 58, 1300), (52, 66, 1180), (53, 69, 1100), (57, 81, 1184), (50, 84, 1300), (51, 75, 1200),
    (52, 61, 1250),
    # the Forest of Peril
    (24, 80, 1500), (36, 81, 1450), (44, 83, 1350), (34, 72, ECTOR_H), (42, 61, GROVE_H), (30, 66, 1650),
    (24, 70, 1700), (22, 88, 1650), (40, 74, 1400), (46, 66, 1450), (28, 60, 1900), (38, 57, 1700),
    (24, 62, 1950), (46, 76, 1300), (30, 76, 1550),
    # the desert heath
    (21, 100, 1450), (30, 95, 1550), (40, 98, 1600), (52, 99, 1650), (62, 100, 1750), (74, 104, 2000),
    (72, 105, 1700), (60, 105, 1600), (46, 105, 1500), (34, 105, 1400), (24, 105, 1300), (50, 90, 1450),
    (44, 92, 1500), (58, 95, 1400), (66, 99, 1500), (80, 99, 1700),
    # Lakeside and its rim, the brow, the D3 road
    (72, 90, TOWN_H), (64, 89, TOWN_H), (80, 89, TOWN_H), (72, 95, TOWN_H), (62, 95, TOWN_H),
    (82, 95, 1220), (86, 97, 1600), (86, 95, 1450), (84, 92, 1180),
    (81, 103, 2150), (94, 102, 2300), (80, 106, 1750), (88, 105, 2050), (88, 101.5, 2272), (87.5, 98, 1800),
    # the east shore and the Rimward crags
    (98, 92, 2000), (100, 99, 2350), (97, 106, 1950), (101, 106, 1750), (101, 88, 1900), (95, 86, 1500),
    (90, 84, 1150), (95, 76, 1152), (97, 82, 1300), (101, 75, 1500), (101, 66, 1150), (102, 60, 1700),
    (100, 81, 1700), (102, 94, 2200),
]
CALM = [(72, 89, 13), (28, 50, 4), (47.5, 51.5, 3), (42, 61, 3.5), (34, 72, 3), (24, 80, 4), (88, 104, 4),
        (78, 53, 3), (100, 38, 2), (57, 81, 2), (91, 84, 2), (95, 76, 2.5), (88, 96, 2), (86, 47.5, 7),
        (72, 69, 6)]


def _d3_row():
    sys.path.insert(0, os.path.join(REPO, 'util'))
    from map_export import parse_odm_file
    d = parse_odm_file(Path(os.path.join(WORLD, 'maps/xeen_d3.odm')))
    hm = d['payload']['height_map']
    return [hm[19 * 128 + x] * 32 for x in range(128)]


D3_ROW = _d3_row() if D3_LIVE else None


def inside(p, poly):
    return K.inside(p, poly)


def roll(x, y):
    w = 1.0
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 4.0))
    v = (110 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.6 + 1.1) + 70 * math.sin((x + 1.4 * y) / 4.7 + 0.3)
         + 40 * math.sin((x - 1.7 * y) / 2.6))
    return w * v


def in_lake(x, y):
    return inside((x, y), LAKE) and not any(inside((x, y), p) for p in ISLETS)


def land(x, y):
    if y < RIM_N or x > RIM_E:
        return 0.0
    num = den = 0.0
    for cx, cy, h in CONTROL:
        d2 = (x - cx) ** 2 + (y - cy) ** 2
        if d2 < 0.01:
            num, den = float(h), 1.0
            break
        w = 1.0 / (d2 ** 1.3)
        num += w * h
        den += w
    h = num / den + roll(x, y)
    p = (x, y)
    on_crag = inside(p, CRAG)
    # the lake: its bed under the water, its shores come down to it (not the crag's south face: a cliff)
    if inside(p, LAKE):
        if inside(p, ISLE):
            return max(LAKE_H + 48, 1120 + 260 * (1 - smooth(math.hypot(x - 72, y - 69) / 4.0)))
        if inside(p, SKERRY_W) or inside(p, SKERRY_E):
            return LAKE_H + 72
        d = poly_dist(p, LAKE)
        return LAKE_H - min(560, 64 + 180 * d)
    if not on_crag:
        d = poly_dist(p, LAKE)
        if d < 7:
            h = min(h, LAKE_H + 40 + 150 * d)
    # the Snow River's cut
    d = dist_to_line(x, y, SNOW_RIVER)
    if d < 3 and y > 32:
        h -= 120 * (1 - smooth(d / 3.0))
    # D3's border (its row y 19, installed): the land runs into it over the last cells (D-28 (6))
    if D3_ROW is not None and y > 100:
        t = smooth((y - 100) / 8.0)
        h = h * (1 - t) + D3_ROW[max(0, min(127, int(round(x))))] * t
    return h


def grid_rows(step=4, unit=32):
    rows = []
    for j in range(128 // step):
        row = []
        for i in range(128 // step):
            x, y = step * i + step / 2, step * j + step / 2
            row.append(max(0, int(round(land(x, y) / unit))))
        rows.append(row)
    return rows


def lake_bodies():
    """The lake as two bodies, north of y 70 and south of y 69 (overlapping between), each notched round the islets'
    halves on whole cells (an islet in water is a hole; the studio's polygons have none, so X2's and X3's lakes are
    split the same way)."""
    s, n = 69, 70
    nb = [[54, n], [54, 65], [55, 60]] + LAKE[0:12] + [[100, n]]
    nb += [[90, n], [90, s], [88, s], [88, n]]
    nb += [[78, n], [78, s], [77, 66], [74, 64], [70, 64], [67, 66], [67, n]]
    nb += [[62, n], [62, s], [60, s], [60, n]]
    sb = [[54, s]]
    sb += [[60, s], [60, 71], [62, 71], [62, s]]
    sb += [[67, s], [67, 71], [70, 73], [73, 74], [76, 72], [78, s]]
    sb += [[88, s], [88, 71], [90, 71], [90, s]]
    sb += [[100, s]] + LAKE[12:27]
    return nb, sb


# ---------------------------------------------------------------------------------------------------------------
# Lakeside (A4's d4.yml): plots (building, index, at = NW corner, facing, [front, depth], grade, kind, extra)
# ---------------------------------------------------------------------------------------------------------------
GRADE = {
    'poor': {'wall': 't06a01', 'window': 't06a04', 'door': 't06a03', 'post_left': 't06a07', 'post_right': 't06a07',
             'roof': 'xlslatemos', 'trim': 't06a10', 'ridge': 't06a10', 'gable': 't06a01'},
    'middle': {'wall': 't06b01', 'window': 't06c04', 'door': 't06b03', 'post_left': 't06b07', 'post_right': 't06b06',
               'roof': 't06a05', 'trim': 't06a10', 'ridge': 't06a10', 'gable': 't06b01'},
    'rich': {'wall': 't09a01', 'window': 't09a04b', 'door': 't09a03c', 'post_left': 't09a06', 'post_right': 't09a07',
             'roof': 'xlslate', 'trim': 't09b11b', 'ridge': 't06a10', 'gable': 't09a01'},
    'service': {'wall': 't09c01', 'window': 't09a04b', 'door': 't09a03a', 'post_left': 't09c06',
                'post_right': 't09c07', 'roof': 'xlslate', 'trim': 't09b11b', 'ridge': 't06a10', 'gable': 't09c01'},
}
PLOTS = [
    ('building:lk_guild', None, (63.5, 87.0), 'e', [4, 4], 'service', 'guild', {}),
    ('building:lk_smithy', None, (78.5, 87.5), 'w', [3, 3], 'middle', 'forge', {'sign': 'sgweap'}),
    ('building:lk_tavern', None, (69.0, 93.5), 'n', [3, 3], 'middle', 'gable_porch', {'sign': 'sgtvrn'}),
    ('building:lk_temple', None, (73.5, 93.5), 'n', [4, 3], 'rich', 'temple', {}),
    ('building:lk_yachts', None, (70.5, 83.5), 'n', [3, 2], 'middle', 'L', {'sign': 'sgdock'}),   # D-92
    ('building:lk_houses', 1, (61.0, 83.5), 'n', [2, 2], 'poor', 'cottage', {}),
    ('building:lk_houses', 2, (60.0, 92.0), 'e', [3, 2], 'poor', 'cottage', {}),
    ('building:lk_houses', 3, (64.0, 83.5), 'n', [2, 2], 'middle', 'gable_porch', {}),
    ('building:lk_houses', 4, (64.5, 94.5), 'n', [3, 2], 'rich', 'cottage', {}),
    ('building:lk_houses', 5, (75.0, 83.5), 'n', [2, 2], 'poor', 'cottage', {}),
    ('building:lk_houses', 6, (79.0, 93.5), 'n', [2, 2], 'middle', 'cottage', {}),
    ('building:lk_houses', 7, (60.5, 87.0), 'e', [2, 2], 'poor', 'gable_porch', {}),
    ('building:lk_houses', 8, (67.0, 83.5), 'n', [2, 2], 'poor', 'cottage', {}),
    ('building:lk_houses', 9, (82.5, 87.5), 'w', [2, 2], 'middle', 'cottage', {}),
    ('building:lk_houses', 10, (78.0, 83.5), 'n', [3, 2], 'poor', 'barn', {}),
]
# the houses that open after Q-D22 (A4's `opens`): the door asks the qbit, else the closed text
GATED = {h['id']: h['closed_text'] for h in TOWN['houses'] if h.get('opens') == 'q-d22.done'}
# town_feel (session 10): grass yards and a tree beside or behind six houses (within 3 cells of a door, the
# checker's town; never in front of a door or on a walking line between doors)
TOWN_YARDS = [[[84, 86], [87, 86], [87, 90], [84, 90]], [[59, 90], [61, 90], [61, 92], [59, 92]],
              [[62, 95], [65, 95], [65, 98], [62, 98]], [[82, 95], [85, 95], [85, 98], [82, 98]],
              [[57, 83], [60, 83], [60, 86], [57, 86]]]
TOWN_TREES = [('tree62a', (84.7, 88.2)), ('tree12', (60.1, 91.0)), ('tree62a', (64.4, 96.2)),
              ('tree12', (82.4, 96.0)), ('tree62a', (59.3, 85.0)), ('tree12', (82.9, 85.2))]
GUILD_DOOR = (67.5, 89.0)        # the guild's double door (east wall middle)
GUILD_BACK = (63.5, 89.0)        # its back stair door (west wall middle)


def house_of(bid, index):
    key = bid if index is None else '%s#%d' % (bid, index)
    return HOUSE[key]


plots_by_space = {}
plan_buildings = {}
footprints = []
doors_out = []


def guild_parts(facing, fp):
    """Two storeys of t09 ashlar over a band of t09b11b (the floor beam), a t09 window in every other bay of both
    storeys (texture fit: a window once per bay), the carved double door as two leaves (t09a03a, the second mirrored)
    256 wide in the east front's middle, a gable roof of slate running east-west with eaves (A6's review: the town's
    grandest house, not a box under a pyramid)."""
    F, D = fp[0] * 512, fp[1] * 512
    w, d = F - 128, D - 128          # 1920 x 1920: 15 bays of 128 a row
    n = 15
    alt = ['window' if k % 2 else 'wall' for k in range(n)]
    walls = {s_: list(alt) for s_ in ('n', 's', 'w')}
    walls['e'] = ['wall', 'window', 'wall', 'window', 'wall', 'window', ['wall', 96], ['door', 256], ['wall', 96],
                  'window', 'wall', 'window', 'wall', 'window', 'wall']
    up = {s_: list(alt) for s_ in ('n', 's', 'e', 'w')}
    body = {'id': 'body', 'at': [64, 64], 'size': [w, d], 'wall_height': 544, 'band': 32, 'roof': 'gable',
            'ridge_along': 'ew', 'roof_pitch': 38, 'eaves': 64, 'walls': walls, 'upper_walls': up,
            'door_height': 288, 'textures': {'band': 't09b11b'},
            # D-92: the Water Guild's board hangs in the plain bay left of the double door (A4, 2026-11-22)
            'signs': [{'wall': facing, 'bay': 6, 'texture': 'sgwater', 'hang': True, 'size': [64, 64], 'out': 48,
                       'bottom': 192}]}
    return [body], {'part': 'body', 'wall': 'e', 'leaves': 2, 'arch': 'round'}


def add_plot(space, bid, index, at, facing, fp, grade, kind, extra):
    x, y = at
    plot = {'building': bid, 'at': [x, y], 'facing': facing, 'kit': 'grey', 'floor': TOWN_H}
    if index is not None:
        plot['index'] = index
    hid, hname = house_of(bid, index)
    plot['house'] = hid
    plot['title'] = hname
    tex = dict(GRADE[grade])
    # D4_TOWN_OPEN=1 (town_feel only, into a scratch briefs folder): the doors as after Q-D22, so the checker sees
    # the services; never for an install
    if hid in GATED and os.environ.get('D4_TOWN_OPEN') != '1':
        plot['condition'] = {'qbit': 'coven_broken'}
        plot['else_effects'] = [msg(GATED[hid])]
    Wp, Hp = K.plot_extent(facing, fp)
    if kind == 'temple':
        # a nave with its door to the square and a squat bell tower at its back, under slate (as D1's)
        nave = {'id': 'nave', 'at': [64, 64 + 256 if facing == 's' else 64], 'size': [Wp - 128, Hp - 128 - 256],
                'wall_height': 416, 'roof': 'gable', 'roof_pitch': 50, 'ridge_along': 'ns'}
        tower = {'id': 'tower', 'at': [Wp // 2 - 144, 64 if facing == 's' else Hp - 352], 'size': [288, 288],
                 'wall_height': 832, 'roof': 'hip', 'roof_pitch': 62, 'windows': 'none'}
        plot['parts'] = [nave, tower]
        plot['door'] = {'part': 'nave', 'wall': facing}
    elif kind == 'guild':
        parts, door = guild_parts(facing, fp)
        plot['parts'] = parts
        plot['door'] = door
    else:
        parts, door = K.shape(kind, facing, fp, 'grey', sign=extra.get('sign'))
        plot['parts'] = parts
        plot['door'] = door
    plot['textures'] = tex
    plots_by_space.setdefault(space, []).append(plot)
    pb = plan_buildings.setdefault(space, {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [],
                   'service': 'residence' if bid == 'building:lk_houses' else hname}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append((index or 0, fp))
    poly = K.footprint(x, y, facing, fp, 0)
    footprints.append((bid, index, poly))
    dc = K.door_cell(x, y, facing, fp, 0, 0.0)
    out = K.door_cell(x, y, facing, fp, 0, 0.9)
    doors_out.append((bid, index, dc, out))
    return plot


for (_bid, _index, _at, _facing, _fp, _grade, _kind, _extra) in PLOTS:
    add_plot('town:lakeside', _bid, _index, _at, _facing, _fp, _grade, _kind, _extra)
for _pb in plan_buildings.values():
    for _b in _pb.values():
        _b['footprint_cells'] = [fp for _, fp in sorted(_b['footprint_cells'], key=lambda t: t[0])]

# the guild's riddle (q-d22.guild_door): answered, the door opens the guild (4651); else the hook shows the riddle and
# the map asks; right: q-d22.guild_right (free membership: the bit, then the door opens); wrong: q-d22.guild_wrong and
# the trapdoor into DD-20's sewer half (entrance:d4_trapdoor; sealed with a line until DD-20 lists it)
GUILD_ID = HOUSE['building:lk_guild'][0]


def move_lua(key, text=0, direct=False):
    """evt.MoveToMap into a live dungeon's named entrance (its coordinates and facing from the studio sidecar).
    s32 (F16): the standard entrance window (picture 1, trans row `text`), or `direct` for a decided move."""
    blv = 'xeen_%s.blv' % key.split('_')[0]
    a = studio_entrances(blv)[ENTRANCE[key]]
    at = a.get('at') or a.get('position')
    face = a.get('facing', a.get('direction', 0))
    if direct:
        return 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, 0, 0, "%s", {direct = true})' % (at[0], at[1], at[2], int(face), blv)
    return 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, %d, 1, "%s")' % (at[0], at[1], at[2], int(face), text, blv)


TRAP_SEALED = ("The floor gives way under you, and a stinking grate stops your fall a few feet down. You climb back out. "
               "(The coven's sewer comes in a later part of the world.)")
for _p in plots_by_space['town:lakeside']:
    if _p['building'] == 'building:lk_guild' and os.environ.get('D4_TOWN_OPEN') != '1':
        _p['condition'] = {'qbit': 'riddle_answered'}
        # A3's q-d22.guild_wrong makes the trapdoor move itself (a status line, then DD-20's entrance:d4_trapdoor):
        # the door only calls the hook once DD-20 is live
        _wrong = '' if DUNGEON['dd20_trapdoor'] else 'evt.StatusText(%s)' % lstr(TRAP_SEALED)
        _p['else_effects'] = [{'lua': (
            'if continueStep == 2 then %s return end '
            'if continueStep == 1 then %s %s return end '
            'if continueStep ~= nil then return end '
            'if not %s then return end '
            'evt.AskQuestion(eventId, 1, 0, 2, "What am I?", {"witch", "witches", "a witch"})'
            % (hcall('q-d22.guild_right'), hcall('q-d22.guild_wrong'), _wrong, hcall('q-d22.guild_door')))}]

# ---------------------------------------------------------------------------------------------------------------
# Roads and paths (L1's, the river crossings moved onto bridges)
# ---------------------------------------------------------------------------------------------------------------
SANDCASTER_ROAD = [[88, 128], [88, 109], [88, 104], [87.5, 100], [86.5, 96.5], [86, 95]]
TOWN_ROAD_EAST = [[86, 95], [85, 92.5], [84, 91.5], [81.5, 91.5], [78, 91]]
DESERT_ROAD = [[0, 80], [19, 80], [24, 80], [30, 80], [36, 81]]
FOREST_ROAD = [[36, 81], [42, 82], [47, 84], [52, 86.5], [56, 88.5], [58.5, 90], [61, 91.0], [63, 91.5], [68, 91.5]]
SHORE_PATH = [[86, 95], [88, 91], [90, 87], [92, 84], [94, 81.5], [95.5, 79], [95.5, 76.5]]
WEST_SHORE_TRACK = [[59.5, 83], [58, 81], [56, 78.5], [54.5, 75], [53, 71], [52, 66], [52.5, 60], [55, 55.5],
                    [57, 53], [61, 53]]          # over the Snow River by thing:snow_bridge
SNOW_BRIDGE = [[57.2, 53.0], [60.8, 53.0]]       # the west-shore track over the Snow River to the junction
JUNCTION = (61, 53)
NORTH_SHORE_TRACK = [[61, 53], [64, 53.5], [68, 53.5], [73, 54], [76, 54]]
SNOW_TRACK = [[61, 53], [61.5, 48], [62, 44], [63, 39], [64, 35.5], [65, 33], [66, 32], [72, 31], [80, 32], [88, 31.5],
              [94, 33], [98, 36], [99.5, 37.5]]
FOREST_LANE = [[36, 81], [35, 77], [34.5, 74], [36, 69], [38.5, 65.5], [41, 62.5]]
CAMP_LANE = [[36, 69], [33, 64], [30.5, 60], [32, 56.5], [29.5, 54], [28.5, 52.5]]
SEAT_PATH = [[29.5, 48.5], [32, 46.5], [34.5, 44.5], [36, 43.6]]
WOODPILE_LANE = [[43.5, 60], [45, 56.5], [46.5, 53], [47.5, 51.8]]
LAIR_PATH = [[47.5, 51], [48.2, 48], [47.6, 45], [46.4, 43.4]]
ROADS = [SANDCASTER_ROAD, TOWN_ROAD_EAST, DESERT_ROAD, FOREST_ROAD]
PATHS = [SHORE_PATH, WEST_SHORE_TRACK, NORTH_SHORE_TRACK, SNOW_TRACK, FOREST_LANE, CAMP_LANE,
         SEAT_PATH, WOODPILE_LANE, LAIR_PATH]


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
# Places
# ---------------------------------------------------------------------------------------------------------------
SOUTH_START = (88.0, 105.0)       # the D3 arrival on the brow, facing north (D-28 (6))
WEST_START = (23.0, 80.0)         # the D5 arrival (sealed until D5 is installed)
SQUARE_ARRIVAL = (73.0, 89.5)     # lakeside_square: the mirror's and Town Portal's arrival, facing north
DOCK_ARRIVAL = (73.0, 82.0)       # lakeside_dock: the jetty's foot, facing south (the town)
JETTY = [[72.0, 82.2], [72.0, 79.2]]
JETTY_END = (72.0, 79.6)          # the signature view: 17,600 from the keep
ISLE_JETTY = [[72.6, 73.3], [72.6, 75.8]]
ISLE_ARRIVAL = (72.0, 72.0)       # isle_landing: the jetty's head on the Isle, facing north (the tower)
ISLE_BOAT = (73.4, 73.6)          # A4's poi:isle_boat (cells 73, 74): Tern's sign and the Isle Ferry's door
ISLE_TOWER = (72.0, 68.0)         # DD-12's ruined round tower, its door south
ISLE_TOWER_R = 520            # D-42: at least ~1,000 across, roofless, a ruin
GATEHOUSE = (77.4, 53.0)          # Blackfang's gatehouse at the crag's west foot, its gate west
KEEP = (87.0, 47.5)
CASTLE_BOX = (83.6, 44.4, 90.4, 50.6)
SHAFT = (69.75, 84.6)             # DD-20's shaft between the Eel House and Lakeside Yachts
BEACHED_BOAT = (82.6, 82.2)
LAIR = (46.0, 41.0)               # DD-23's cave mouth (its front's middle), looking south over the clearing
LAIR_ARRIVAL = (46.4, 43.0)
WOODPILE = (48.0, 51.0)
GROVE = (42.0, 61.0)              # Leafpoint
ECTOR_CABIN = (33.0, 71.0)        # Ector's cabin plot's NW corner
OBELISK = (57.0, 81.0)
CAMP = (28.0, 50.0)
# the bat storm (D-36 (1)): S's looping model xeen_batstorm (row 4003; its origin the storm's centre at the lowest
# ring, the bats -70 to +600 round it, about 2,650 across), two copies: about 400 over the keep's roof (its top 2,700
# over the crag top) and over the south-east corner tower's cone (2,430); z is absolute, the last figure the width
BAT_STORM_SPOTS = [('keep', (87.0, 47.5), CRAG_TOP + 3100, 2650), ('tower_se', (90.4, 50.6), CRAG_TOP + 2800, 2650)]
# the Fly knock-down: the air over the crag top (cells) above this height; the party is set down on the north-shore
# track by the gatehouse, facing it
STORM_BOX = (81.0, 41.0, 94.0, 56.0)
STORM_Z = 2700
STORM_DROP = (75.6, 54.0)
OCTOPOD_LEASH = 1500  # the octopods' home radius (game units; the scene's leash_radius, D-36 (2))
SEALED = 'The way in is choked and dark. (Not yet open: this place comes in a later part of the world.)'


def build():
    os.makedirs(OUT, exist_ok=True)
    L1P = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'project.yml')))
    # ================================ project.yml
    neighbours = []
    for n in L1P['neighbours']:
        n = copy.deepcopy(n)
        nid = n['id']
        if nid == 'edge:south':
            if not D3_LIVE:
                continue
            n['notes'] = ("D3 Sandcaster (A5): the road crosses the edge at x 88; D3's north edge arrives at D4's "
                          "entrance:south_road (88, 105) facing north (D-28 (6)).")
        elif nid == 'edge:west':
            if not D5_LIVE:
                continue
            n.pop('listed_only', None)
            n['notes'] = ("D5 Desert of Doom (A6): the desert road crosses the edge at y 80, a level valley at 1,500; "
                          "D5's east edge arrives at D4's entrance:west_road (23, 80) facing east; D4's west edge "
                          "arrives at D5's entrance:d4_road (105, 80) facing west (D-36 (7)).")
        elif nid in ('boat:isle', 'boat:lucio', 'boat:isle_return', 'stable:castleview', 'stable:sandcaster'):
            # the routes are A4's houses (4655, 4667) and the caravan houses of D1/D3: listed here
            n['listed_only'] = True
            n.pop('schedule', None)
            n.pop('service', None)
            n.pop('condition', None)
            if nid == 'boat:isle_return':
                n['notes'] = ("The Isle Ferry (A4's house 4667, Tern) at poi:isle_boat on the Isle's landing: route 432 "
                              "daily to lakeside_dock (D-36 (6)).")
        elif nid == 'mirror:darkside':
            continue
        elif nid == 'door:dd20_sewer':
            n['notes'] = ("The shaft by the jetty's foot: \"Climb down to the sewer?\" (aaze0033:3), open from day one "
                          "(D-36 (4)), into DD-20's entrance:d4_shaft.")
            if DUNGEON['dd20_shaft']:
                n.pop('listed_only', None)
                n['arrival'] = ENTRANCE['dd20_shaft']
            else:
                n['listed_only'] = True
        neighbours.append(n)
    project = {
        'format': 0, 'id': STEM, 'name': 'Lakeside and Blackfang', 'world': 'xeen', 'kind': 'outdoor',
        'profile': 'odm', 'map_code': 'D4', 'units': {'plan_grid': 512}, 'extent': {'terrain_cells': 128},
        'map_stats': copy.deepcopy(L1P['map_stats']),
        'neighbours': neighbours,
        'qbits': dict(QBIT),
        'items': dict(ITEMS),
        'rules': {'respawn': 'entrance:lakeside_square', 'town_portal_anchor': 'entrance:lakeside_square'},
        'notes': ("D4 Lakeside and Blackfang (A6, 2026-11-20), built from the approved L1 with D-36. The south edge "
                  "(D3) is live; the west edge (D5) is sealed by a sign until D5 is installed; each dungeon door shows "
                  "its hook and a sealed line until its BLV is installed and lists the door's entrance. Written by "
                  "output/studio_cal/d4/tools/gen.py."),
    }
    project['map_stats']['continent'] = 7
    # ================================ plan.yml (L1's spaces with D-36 applied)
    L1 = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'plan.yml')))
    plan = copy.deepcopy(L1)
    plan['level'] = 'L3'
    for s in plan['spaces']:
        if s['id'] in plan_buildings:
            s['buildings'] = list(plan_buildings[s['id']].values())
    ents = []
    for e in plan['entrances']:
        if e.get('neighbour') == 'edge:west' and not D5_LIVE:
            e = {'id': e['id'], 'space': e['space'], 'kind': 'arrival', 'facing': 'e',
                 'how': ("The desert road at the forest's west edge: the edge to D5 is sealed by a sign until D5 is "
                         "installed (then D5's arrival).")}
        if e.get('neighbour') == 'edge:south' and not D3_LIVE:
            e = {'id': e['id'], 'space': e['space'], 'kind': 'arrival', 'facing': 'n', 'how': e['how']}
        if e.get('neighbour') == 'mirror:darkside':
            e = {k: v for k, v in e.items() if k != 'neighbour'}
        if e['id'] == 'entrance:dd20_guild':
            e = dict(e, facing='w')       # as the sketch's point and DD-20's exit (1024; A8, 2026-11-20)
        ents.append(e)
    ents.append({'id': 'entrance:dd14_griffin', 'space': 'zone:north_shore', 'kind': 'arrival', 'facing': 'w',
                 'how': ("D-42: where Ambrose's griffin from DD-14's walls sets the party down, on the north-shore track "
                         "before Blackfang's gate.")})
    # the respawn's and the new game's arrival first (the build starts at the first arrival)
    ents.sort(key=lambda e: (e['id'] != 'entrance:lakeside_square', e['id'] != 'entrance:south_road'))
    plan['entrances'] = ents
    # D-58 Q10 (A6 s16): a fall from D7's zone E1-F2 lands here (Xeen.SkyFalls.d7_d4); whole flat cell, 256 clear
    plan['entrances'].append({'id': 'entrance:d7_fall', 'space': next(e['space'] for e in ents if e['id'] == 'entrance:lakeside_square'),
                              'kind': 'both', 'facing': 'w',   # 'arrival' would make it the party start
                              'how': "D-58 Q10: a fall from D7 lands here, on Lakeside's square, by the ferry dock (Lucio's boat to Olympus after m30.done) and the mirror."})
    plan.pop('totals', None)
    plan['sketch'] = {'file': 'sketch.yml', 'grid': 512}
    plan['notes'] = ('L3/L4 written by output/studio_cal/d4/tools/gen.py from the approved L1 and D-36. The plan keeps '
                     "the L1 spaces; the coven's two groups and the five octopods are placed actors, the gargoyles and "
                     'the rocs slot markers.')
    # ================================ sketch.yml
    L1S = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'sketch.yml')))
    frame = copy.deepcopy(L1S['frame'])
    frame['edges'] = [e for e in frame['edges'] if (e['side'] == 'south' and D3_LIVE) or (e['side'] == 'west'
                                                                                          and D5_LIVE)]
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its land function.'},
        'points': [
            {'at': [30, 36], 'h': 4100, 'notes': 'Magic Mountain'},
            {'at': [38, 31], 'h': 3700},
            {'at': [24, 31], 'h': 3500},
            {'at': [88, 105], 'h': 2048, 'notes': 'the D3 arrival, climbing to the brow'},
            {'at': [88, 108], 'h': 1760, 'notes': "the road at the D3 edge (D3's bed 1,760)"},
        ],
        'ridges': [
            {'line': [[95, 88], [100, 96], [99, 104]], 'height': [2100, 2400, 2200], 'width': 2, 'slope': 3,
             'notes': "The Rimward crags, D3's Wrath shoulder running on north."},
            {'line': [[22, 30], [30, 35], [38, 31], [45, 35]], 'height': [3500, 3900, 3600, 3100], 'width': 2,
             'slope': 4, 'notes': "Magic Mountain's crest."},
        ],
        'terraces': [
            {'polygon': ISLE, 'height': 1104, 'slope': 0, 'notes': "The Isle of Lost Souls' shore."},
            {'polygon': SKERRY_W, 'height': 1120, 'slope': 0, 'notes': 'The West Skerry.'},
            {'polygon': SKERRY_E, 'height': 1120, 'slope': 0, 'notes': 'The East Skerry.'},
            {'polygon': [[59.0, 81.8], [86.6, 81.8], [86.6, 97.6], [59.0, 97.6]], 'height': TOWN_H, 'slope': 3,
             'notes': 'Lakeside: the waterfront and the square.'},
            {'polygon': [[CASTLE_BOX[0] - 0.8, CASTLE_BOX[1] - 0.8], [CASTLE_BOX[2] + 0.8, CASTLE_BOX[1] - 0.8],
                         [CASTLE_BOX[2] + 0.8, CASTLE_BOX[3] + 0.8], [CASTLE_BOX[0] - 0.8, CASTLE_BOX[3] + 0.8]],
             'height': CRAG_TOP, 'slope': 2, 'notes': "Castle Blackfang's crag top."},
            {'polygon': [[24, 47], [32, 47], [32, 53], [24, 53]], 'height': CAMP_H, 'slope': 3,
             'notes': "Xanthus and Slibo's camp on its shelf."},
            {'polygon': [[45, 49], [50, 49], [50, 54], [45, 54]], 'height': CLEARING_H, 'slope': 3,
             'notes': "The woodcutters' clearing (Ector's woodpile)."},
            {'polygon': [[44.5, 41.6], [48.0, 41.6], [48.0, 44.4], [44.5, 44.4]], 'height': 2304, 'slope': 2,
             'notes': "The ledge before DD-23's cave mouth."},
            {'polygon': [[39, 58], [45, 58], [45, 64], [39, 64]], 'height': GROVE_H, 'slope': 3,
             'notes': "Leafpoint's grove."},
            {'polygon': [[31, 69], [37, 69], [37, 74], [31, 74]], 'height': ECTOR_H, 'slope': 3,
             'notes': "Ector's clearing and cabin."},
            {'polygon': [[70.0, 66.4], [74.0, 66.4], [74.0, 70.0], [70.0, 70.0]], 'height': 1376, 'slope': 2,
             'notes': "The Isle's tower knoll."},
            {'polygon': [[74.6, 51.2], [78.6, 51.2], [78.6, 55.2], [74.6, 55.2]], 'height': 1184, 'slope': 2,
             'notes': "The gatehouse's forecourt on the north shore."},
            {'polygon': [[98.6, 36.4], [101.4, 36.4], [101.4, 39.4], [98.6, 39.4]], 'height': 1824, 'slope': 2,
             'notes': "The Fountain of Great Resilience's ledge where the rims meet."},
            {'polygon': [[56.0, 80.0], [58.0, 80.0], [58.0, 82.0], [56.0, 82.0]], 'height': 1184, 'slope': 2,
             'notes': 'Gull Knoll: the obelisk.'},
            {'polygon': [[93.2, 74.6], [96.6, 74.6], [96.6, 77.6], [93.2, 77.6]], 'height': 1152, 'slope': 2,
             'notes': 'Mirabeth Point.'},
            {'polygon': [[86.5, 100.5], [89.5, 100.5], [89.5, 103.0], [86.5, 103.0]], 'height': 2272, 'slope': 3,
             'notes': 'Lakeside Brow: the lake country opens below (the D3 road tops the heath here).'},
            {'polygon': [[20, 77], [27, 77], [27, 83], [20, 83]], 'height': 1504, 'slope': 3,
             'notes': 'The D5 arrival at the forest edge.'},
        ],
        'cliffs': [
            {'line': [[0, RIM_N], [RIM_E, RIM_N], [RIM_E, 128]], 'drop': 1500, 'down': 'left',
             'notes': "The world rim, north then east; the lake's outflow falls over it at (104, 67)."},
            {'line': [[79, 59], [84, 60], [90, 60], [95, 59]], 'drop': 1200, 'down': 'right',
             'notes': "Blackfang's crag: its south face straight into the lake."},
            {'line': [[79, 42], [78, 46], [78, 51], [79, 56], [79, 59]], 'drop': 900, 'down': 'right',
             'notes': "The crag's west face over the north-shore track and the gatehouse."},
            {'line': [[95, 59], [97, 52], [96, 46], [94, 41]], 'drop': 800, 'down': 'right',
             'notes': "The crag's east face over the rim corner."},
            {'line': [[94, 41], [88, 39], [82, 39], [79, 42]], 'drop': 700, 'down': 'right',
             'notes': "The crag's north face over the snow track."},
            {'line': [[43, 41], [50, 41]], 'drop': 448, 'down': 'right',
             'notes': "The rock face over the ledge: DD-23's cave mouth in its foot at (46, 41)."},
        ],
        'peaks': [
            {'polygon': [[21, 25.5], [46, 25.5], [46, 38], [21, 38]], 'count': 9, 'height': [3200, 4200],
             'radius': [1.5, 3], 'profile': 'cone', 'spacing': 3, 'seed': 4,
             'notes': "Magic Mountain's crags, their north faces over the rim."},
            {'polygon': [[96, 86], [103, 86], [103, 104], [96, 104]], 'count': 4, 'height': [2200, 2600],
             'radius': [1.2, 2], 'profile': 'cone', 'spacing': 3, 'seed': 6,
             'notes': 'The Rimward crags broken into tops.'},
        ],
    }
    nb, sb = lake_bodies()
    water = {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0,
             'polygon': [[0, 0], [128, 0], [128, 128], [RIM_E, 128], [RIM_E, RIM_N], [0, RIM_N]],
             'notes': 'Below the rim: stands for the stars.'},
            {'id': 'water:octopod_lake', 'index': 1, 'kind': 'lake', 'level': LAKE_H, 'polygon': nb,
             'notes': "Octopod Lake, north of y 69 (two bodies round the Isle and the two skerries)."},
            {'id': 'water:octopod_lake', 'index': 2, 'kind': 'lake', 'level': LAKE_H, 'polygon': sb,
             'notes': "Octopod Lake, south of y 69."},
            {'id': 'water:snow_springs', 'kind': 'pond', 'level': 2272, 'polygon': TARN,
             'notes': "The Snow Springs' tarn under the snowfield."},
        ],
        'rivers': [
            {'id': 'water:snow_river', 'line': SNOW_RIVER, 'width_cells': 1.5,
             'notes': ("The Snow River: rapids from the springs (2,270) down a rocky cut to the lake's north-west bay "
                       "(1,056), under the spring bridge and the shore bridge (D-23: it rises and falls inside the "
                       "map).")},
            {'id': 'water:outflow', 'line': OUTFLOW, 'width_cells': 2, 'level': LAKE_H,
             'notes': 'The race from the lake to the rim, where it falls into the stars (the Octopod Falls).'},
        ],
    }
    roads = [
        {'link': 'link:sandcaster_road', 'line': SANDCASTER_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:town_road_east', 'line': TOWN_ROAD_EAST, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:desert_road', 'line': DESERT_ROAD, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:forest_road', 'line': FOREST_ROAD, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:shore_path', 'line': SHORE_PATH, 'width': 'lane', 'surface': 'soil'},
        {'link': 'link:west_shore_track', 'line': WEST_SHORE_TRACK, 'width': 'lane', 'surface': 'soil'},
        {'link': 'link:north_shore_track', 'line': NORTH_SHORE_TRACK, 'width': 'lane', 'surface': 'soil'},
        {'link': 'link:snow_track', 'line': SNOW_TRACK, 'width': 'lane', 'surface': 'soil_stony'},
        {'link': 'link:forest_lane', 'line': FOREST_LANE, 'width': 'lane', 'surface': 'soil'},
        {'link': 'link:camp_lane', 'line': CAMP_LANE, 'width': 'lane', 'surface': 'soil_stony'},
        {'link': 'link:seat_path', 'line': SEAT_PATH, 'width': 'lane', 'surface': 'soil_stony'},
        {'link': 'link:woodpile_lane', 'line': WOODPILE_LANE, 'width': 'lane', 'surface': 'soil'},
        {'link': 'link:lair_path', 'line': LAIR_PATH, 'width': 'lane', 'surface': 'soil_stony'},
    ]
    districts = []
    for d in L1S['districts']:
        d = copy.deepcopy(d)
        if d['space'] in plots_by_space:
            d['plots'] = plots_by_space[d['space']]
        districts.append(d)
    points = [{'id': 'entrance:south_road', 'at': list(SOUTH_START), 'facing': 'n'},
              {'id': 'entrance:west_road', 'at': list(WEST_START), 'facing': 'e'},
              {'id': 'entrance:lakeside_square', 'at': list(SQUARE_ARRIVAL), 'facing': 'n'},
              {'id': 'entrance:lakeside_dock', 'at': list(DOCK_ARRIVAL), 'facing': 's'},
              {'id': 'entrance:isle_landing', 'at': list(ISLE_ARRIVAL), 'facing': 'n'},
              {'id': 'entrance:dd12_door', 'at': [ISLE_TOWER[0], ISLE_TOWER[1] + 1.6], 'facing': 's'},
              {'id': 'entrance:dd20_guild', 'at': [62, 90], 'facing': 'w'},
              {'id': 'entrance:dd14_griffin', 'at': [76, 54], 'facing': 'w'},
              {'id': 'entrance:dd20_shaft', 'at': [SHAFT[0], SHAFT[1] - 1.2], 'facing': 'n'},
              {'id': 'entrance:dd23_lair', 'at': list(LAIR_ARRIVAL), 'facing': 's'},
              {'id': 'entrance:blackfang_gate', 'at': [GATEHOUSE[0] - 1.8, GATEHOUSE[1]], 'facing': 'w'},
              {'id': 'junction:well_fork', 'at': [86, 95]}, {'id': 'junction:ector_fork', 'at': [36, 81]},
              {'id': 'junction:snow_bridge', 'at': list(JUNCTION)}]
    points.append({'id': 'entrance:d7_fall', 'at': [75, 90], 'facing': 'w'})   # D-58 Q10 (A6 s16)
    POI_AT = {'poi:obelisk': OBELISK, 'poi:fountain_magic': (29, 49), 'poi:warding_well': (88.6, 97.4),
              'poi:fountain_resilience': (100, 38), 'poi:woodpile': WOODPILE, 'poi:cairn': (91.6, 84.0),
              'poi:mirabeth': (95, 76), 'poi:genie_seat': (36, 43.6), 'poi:genie_skerry': (89, 70.1),
              'poi:witches_circle': (50, 90), 'poi:reed_cauldron': (51.4, 68.8), 'poi:beached_boat': BEACHED_BOAT,
              'poi:roc_nest': (70, 33), 'poi:frozen_pilgrim': (64.6, 31.0), 'poi:skerry_strongbox': (61, 70.1),
              'poi:roc_hunter': (99.4, 99.0), 'poi:heath_wagon': (52, 100), 'poi:circle_chest': (51.2, 91.2),
              'poi:hunters_hide': (24, 64), 'poi:falls_chest': (101, 63.4), 'poi:gibbet': (74, 104),
              'poi:isle_boat': ISLE_BOAT, 'poi:naomi': (70.6, 90.1), 'poi:slibo': (26.5, 51),
              'poi:leafpoint': GROVE, 'poi:ector': (34.4, 72.6), 'poi:mirror': (73.0, 87.5)}
    for k, at in POI_AT.items():
        points.append({'id': k, 'at': [round(at[0], 2), round(at[1], 2)]})
    for i, at in enumerate([(38, 67.5), (30, 85)]):
        points.append({'id': 'poi:animal_trap', 'index': i + 1, 'at': list(at)})
    for i, at in enumerate([(87.0, 94.0), (37.0, 82.4), (61.8, 54.0)]):
        points.append({'id': 'poi:signposts', 'index': i + 1, 'at': list(at)})
    points += [{'id': 'landmark:blackfang', 'at': list(KEEP)}, {'id': 'landmark:isle', 'at': list(ISLE_TOWER)},
               {'id': 'landmark:magic_mountain', 'at': [30, 36]}, {'id': 'landmark:octopod_falls', 'at': [104, 67]},
               {'id': 'landmark:rapids', 'at': [59.6, 44]}]
    # ---------------------------------------------------------------- encounter areas (47 markers)
    areas = []

    def markers(pop, spots, slot):
        for (cx, cy) in spots:
            k = sum(1 for a in areas if a['id'] == pop) + 1
            areas.append({'id': pop, 'index': k, 'kind': 'encounter', 'count': 1, 'slot': slot,
                          'circle': {'at': [cx, cy], 'r': 1}})
    # E1: Mountain Gargoyles on Magic Mountain's perches round DD-23 (slot 1); none on the camp's shelf or in the
    # woodcutters' clearing
    markers('pop:mountain_gargoyles', [(24, 29), (30, 27.5), (36, 27), (42, 28), (48, 30), (52, 34), (26, 37),
                                        (33, 36.5), (40, 35), (47, 37), (53, 40), (42.4, 44.6), (36.5, 40.4)], 1)
    # E2: rocs over the uplands, the rapids and the rim corner behind the crag (slot 2)
    markers('pop:snow_rocs', [(60, 27.5), (67, 27), (74, 27.5), (81, 27), (88, 27.5), (95, 28), (101.5, 31),
                              (70, 36.5), (78, 35), (66, 42), (100.5, 47), (101, 54)], 2)
    # E3 (D-36): the Rimward crags' rocs, the same 8 markers over an area stretched north up the east shore's crags
    # to the falls' lip (six encounter units: 6 x 4,096 squared)
    markers('pop:rimward_rocs', [(102, 62), (100.5, 73.5), (102, 80.5), (98.5, 88), (102, 93.5), (96.5, 97),
                                 (101.5, 101.5), (97.5, 106)], 2)
    # E5: rocs over the desert edge; the first fight from D5
    markers('pop:heath_rocs', [(21.5, 89.8), (27, 96), (22, 101.5), (28, 105.5), (34, 99.5), (35, 106),
                               (40, 102.5), (46, 98.5), (46, 106), (52.5, 104.5), (53.5, 100.5), (58, 106),
                               (21.5, 64), (40, 96.5)], 2)
    # F10 (s32): the heath roc at (31.5, 92.5) moved to the empty west edge's middle (21.5, 64)
    E3_AREA = [[97.5, 61.5], [103.6, 61.5], [103.6, 108.5], [92.5, 108.5], [92.5, 86], [97.5, 82]]
    town_doors = [d[2] for d in doors_out]
    for a in areas:
        c = a['circle']['at']
        near = min(math.hypot(c[0] - d[0], c[1] - d[1]) for d in town_doors)
        if near * 512 < 2500:
            raise SystemExit('monsters within 2,500 of a town door: %s %s' % (a['id'], c))
        for k, (u, v) in (('isle', ISLE_ARRIVAL), ('dock', DOCK_ARRIVAL), ('square', SQUARE_ARRIVAL)):
            if math.hypot(c[0] - u, c[1] - v) * 512 < 2500:
                raise SystemExit('a marker within 2,500 of the %s arrival: %s' % (k, c))
    for (cx, cy, r) in ((28, 50, 5), (47.5, 51.5, 3), (42, 61, 3)):
        for a in areas:
            c = a['circle']['at']
            if math.hypot(c[0] - cx, c[1] - cy) < r:
                raise SystemExit('a marker in a calm place (%s): %s' % ((cx, cy), c))
    areas += [
        {'id': 'zone:lakeside_brow', 'kind': 'keep_clear', 'polygon': [[83, 99], [93, 99], [93, 109], [83, 109]],
         'notes': 'The D3 arrival.'},
        {'id': 'zone:west_edge', 'kind': 'keep_clear', 'polygon': [[19, 75], [29, 75], [29, 86], [19, 86]],
         'notes': 'The D5 arrival.'},
        {'id': 'town:lakeside', 'kind': 'keep_clear', 'polygon': [[55, 77], [90, 77], [91, 102], [55, 102]],
         'notes': 'Lakeside and its buffer (about 2,500 round the doors).'},
        {'id': 'zone:isle', 'kind': 'keep_clear', 'polygon': ISLE},
        {'id': 'zone:wizard_camp', 'kind': 'keep_clear', 'polygon': [[24, 47], [32, 47], [32, 53], [24, 53]]},
        {'id': 'zone:leafpoint_grove', 'kind': 'keep_clear', 'polygon': [[39, 58], [45, 58], [45, 64], [39, 64]]},
        {'id': 'zone:ector_clearing', 'kind': 'keep_clear', 'polygon': [[31, 69], [37, 69], [37, 74], [31, 74]]},
        {'id': 'zone:mirabeth_point', 'kind': 'keep_clear', 'polygon': [[92, 73], [97, 73], [97, 78], [92, 78]]},
        {'id': 'zone:woodcutters_clearing', 'kind': 'keep_clear',
         'polygon': [[45, 49], [50, 49], [50, 54], [45, 54]]},
    ]
    views = [
        {'id': 'view:arrival', 'at': [88, 102], 'height': 180, 'look': [82, 70],
         'purpose': ("From the brow on the D3 road, looking north: Lakeside's slate roofs and jetty below, the lake "
                     "with the Isle, Castle Blackfang on its crag across the water, the falls at the east rim.")},
        {'id': 'view:signature', 'at': [72, 80], 'height': 180, 'look': [86, 48],
         'purpose': ("From the ferry jetty's end (17,600 from the keep), north-north-east: the Isle's ruined tower "
                     "ahead-left, Castle Blackfang on its black crag beyond (lit windows, the bat storm), its sealed "
                     "gatehouse at the crag's foot.")},
    ]
    structures = []
    S = structures.append
    # ---------------------------------------------------------------- Lakeside
    S({'id': 'thing:lk_mirror', 'kind': 'portal', 'at': [73.0, 87.5], 'radius': 112, 'sides': 12, 'turn': 0,
       'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'The Mirror of Lakeside',
       'effects': [{'lua': 'Xeen.useMirror(%d, eventId, continueStep)' % HOUSE_MIRROR}],
       'notes': "A4's 4656: asleep until q-d22.done (and Kalindra's stage 4, A3's mirror helper)."})
    # Naomi's stocks on the square, facing the guild's door (Q-D22): a post and a board, Naomi behind it
    S({'id': 'thing:stocks', 'kind': 'building', 'at': [70.05, 89.85], 'size': [0.35, 0.5], 'kit': 'grey',
       'door': 'none', 'title': 'The stocks', 'floor': TOWN_H + 8,
       'parts': [{'id': 'post', 'at': [72, 64], 'size': [40, 128], 'wall_height': 192, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 't06a10', 'roof': 't06a10'}},
                 {'id': 'board', 'at': [56, 40], 'size': [72, 176], 'bottom': 128, 'wall_height': 48,
                  'roof': 'flat', 'windows': 'none', 'textures': {'wall': '7trimda', 'roof': '7trimda'}}]})
    # the guild's back stair (DD-20's coven hall, entrance:d4_guild): a cellar door in its west wall, for members
    back = {'id': 'thing:guild_back_stair', 'kind': 'hatch', 'form': 'wedge',
            'at': [round(GUILD_BACK[0] - 0.55, 3), GUILD_BACK[1]], 'turn': 90, 'height': 160, 'size': [384, 384],
            'textures': {'wall': 't09c01', 'door': '7trimda'}, 'title': "The guild's back stair",
            'hint': "The Lakeside Guild", 'condition': {'qbit': 'riddle_answered'},
            'locked_text': 'A cellar door. The front door asks first.'}
    if DUNGEON['dd20_guild']:
        back['into'] = {'map': 'xeen_dd20.blv', 'arrival': ENTRANCE['dd20_guild']}
    else:
        back['effects'] = [{'text': ("Steps go down under the guild into the dark, and the coven's door at their foot "
                                     "is shut. (The coven's hall comes in a later part of the world.)")}]
    S(back)
    # DD-20's shaft by the jetty's foot (D-36 (4)): the source's question (aaze0033:3), open from day one
    shaft = {'id': 'thing:sewer_shaft', 'kind': 'hatch', 'form': 'pit', 'at': list(SHAFT), 'height': 48,
             'size': [256, 256], 'textures': {'wall': 't06a01', 'door': '7solid01'}, 'title': 'A grated shaft',
             'hint': 'A grated shaft'}
    if DUNGEON['dd20_shaft']:
        # down the ladder to DD-20's entrance:d4_shaft (a structure has no `leave` effect: the move by Lua) on Yes of
        # the source's question as Yes/No buttons (D-72 rule 3)
        # s32 (F16): no Yes/No; the entrance window with trans row 5055 asks
        shaft['effects'] = [{'lua': move_lua('dd20_shaft', text=5055)}]
    else:
        shaft['effects'] = [{'text': ("The ladder stops at a grate rusted shut a few rungs down. Something below "
                                      "smells of witches. (The sewer comes in a later part of the world.)")}]
    S(shaft)
    # the ferry jetty (Lakeside Yachts' boats leave from its end) and the ferry moored along it
    S({'id': 'thing:ferry_jetty', 'kind': 'bridge', 'line': JETTY, 'width': 256, 'height': TOWN_H + 8,
       'kerb': 32, 'textures': {'deck': '7trimda', 'side': 'btrima2'}, 'title': 'The ferry jetty'})
    S({'id': 'thing:ferry_boat', 'kind': 'bridge', 'line': [[72.62, 80.8], [72.62, 79.4]], 'width': 176,
       'height': LAKE_H + 24, 'piers': 0, 'kerb': 48, 'textures': {'deck': '7trimd', 'side': 'btrima2'},
       'title': "Ferris Gull's ferry"})
    # Skiff's beached boat (D-12.1): the source's sign, and its locker; the source's "Search the boat?" dropped (the
    # orchestrator 2026-11-22, as X7's den chest): the chest opens at once, the search's line on the status bar
    S({'id': 'thing:beached_boat', 'kind': 'building', 'at': [BEACHED_BOAT[0] - 0.35, BEACHED_BOAT[1] - 0.8],
       'size': [0.7, 1.6], 'kit': 'grey', 'door': 'none', 'title': 'A boat on the shingle', 'floor': TOWN_H,
       'parts': [{'id': 'hull', 'at': [72, 64], 'size': [216, 680], 'wall_height': 112, 'roof': 'none',
                  'windows': 'none', 'textures': {'wall': 'btrima2', 'roof': '7trimd'},
                  'title': 'A boat on the shingle',
                  'effects': [msg("There is a sign here that reads 'This boat under repair.'")]}]})
    S({'id': 'thing:boat_locker', 'kind': 'chest', 'at': [BEACHED_BOAT[0] + 0.55, BEACHED_BOAT[1] + 0.4],
       'title': "The boat's locker", 'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': "You search the beached boat and open its locker."}]})
    # the square (A6's review): flagstone paving with the mirror on its north side, Naomi's stocks facing the guild,
    # the well, two market stalls along its north and south edges, two benches, barrels in pairs by house walls
    S({'id': 'thing:square_paving', 'kind': 'platform', 'at': [73.0, 90.0], 'size': [5120, 3072], 'height': 8,
       'textures': {'top': 't09a02a', 'wall': 't09a02a'}, 'title': "Lakeside's square"})
    w = K.well('thing:town_well', (76.4, 91.4), title="Lakeside's well")
    S(w)
    for i, (at, turn) in enumerate((((69.2, 87.25), 0), ((74.6, 92.0), 180))):
        st = K.stall('thing:square_stall_%d' % (i + 1), at, turn, kit='grey', roof_tex='xlslatemos')
        st['parts'][0]['textures'] = {'roof': 'xlslatemos', 'post': 't06a10', 'trim': 't06a10', 'sill': '7trimda',
                                      'wall': '7trimda'}
        S(st)
    for i, at in enumerate(((76.6, 87.3), (70.0, 92.3))):
        S({'id': 'thing:square_bench_%d' % (i + 1), 'kind': 'building', 'at': [at[0], at[1]], 'size': [0.75, 0.3],
           'kit': 'grey', 'door': 'none', 'title': 'A bench', 'floor': TOWN_H + 8,
           'parts': [{'id': 'bench', 'at': [32, 24], 'size': [320, 96], 'wall_height': 64, 'roof': 'flat',
                      'windows': 'none', 'textures': {'wall': 't06a10', 'roof': '7trimda'}}]})
    for i, at in enumerate(((68.72, 96.0), (68.72, 96.4), (81.45, 90.2), (81.45, 90.6))):
        S(deco('thing:town_barrel_%d' % (i + 1), 'bigbarel', at))
    # ---------------------------------------------------------------- the Isle of Lost Souls
    S({'id': 'thing:isle_jetty', 'kind': 'bridge', 'line': ISLE_JETTY, 'width': 192, 'height': LAKE_H + 72,
       'kerb': 32, 'textures': {'deck': '7trimda', 'side': 'btrima2'}, 'title': "The Isle's jetty"})
    S({'id': 'thing:isle_skiff', 'kind': 'bridge', 'line': [[73.25, 74.6], [73.25, 75.9]], 'width': 160,
       'height': LAKE_H + 24, 'piers': 0, 'kerb': 48, 'textures': {'deck': '7trimd', 'side': 'btrima2'},
       'title': 'The Isle Ferry'})
    isle_ferry = sign('thing:isle_ferry', ISLE_BOAT, 'The Isle Ferry', height=224, width=128, effects=[])
    isle_ferry.pop('effects')
    if HOUSE_LIVE:
        isle_ferry['house'] = HOUSE[ISLE_FERRY_DOOR][0]
    else:
        isle_ferry['effects'] = [{'text': 'The boat is tied up and nobody is in it.'}]
    S(isle_ferry)
    S(sign('thing:isle_sign', (71.3, 73.0), 'A sign', 'Isle of Lost Souls. Abandon all hope, and mind the step.',
           height=192, width=128))
    tx, ty = ISLE_TOWER
    fp = 2.0
    tower = {'id': 'thing:isle_tower', 'kind': 'building', 'at': [tx - 1.25, ty - 1.25], 'size': [2.5, 2.5],
             'kit': 'grey', 'facing': 's', 'floor': 1376, 'title': 'The ruined tower',
             'textures': {'wall': 'hkm2bs', 'door': 'hkm1dl', 'trim': 'hkm2bs', 'window': 'hkm2bs',
                          'roof': 'hkm2bs'},
             'parts': [{'id': 'base', 'shape': 'round', 'at': [640, 640], 'radius': ISLE_TOWER_R, 'sides': 10,
                        'wall_height': 640, 'roof': 'none', 'windows': 'none', 'door_height': 320,
                        'walls': {'0': [['wall', 32], ['door', 256], ['wall', 33]]}}],
             'door': {'part': 'base', 'wall': '0', 'leaves': 2},
             'condition': {'lua': hcall('m24.isle_door')},
             'notes': "DD-12 Dungeon of Lost Souls (A8): the Isle's only gate (D-12.1), lost_souls_key (M20)."}
    if DUNGEON['dd12']:
        tower['into'] = {'map': 'xeen_dd12.blv', 'arrival': ENTRANCE['dd12']}
    else:
        tower['effects'] = [{'text': ("The key turns, and behind the leaves a stair goes down into a cold that has no "
                                      "bottom. (The Dungeon of Lost Souls comes in a later part of the world.)")}]
    S(tower)
    # its broken crown: the upper storeys fallen in, a ruin of uneven stubs on the intact base (no roof)
    S({'id': 'thing:isle_tower_crown', 'kind': 'building', 'at': [tx - 1.25, ty - 1.25], 'size': [2.5, 2.5],
       'kit': 'grey', 'door': 'none', 'floor': 1376, 'title': 'The ruined tower',
       'ruin': {'height': [64, 640], 'gaps': 0.35, 'thickness': 64, 'seed': 5},
       'textures': {'wall': 'hkm2bs', 'trim': 'hkm2bs', 'window': 'hkm2bs'},
       'parts': [{'id': 'crown', 'shape': 'round', 'at': [640, 640], 'radius': ISLE_TOWER_R, 'sides': 10,
                  'bottom': 640, 'wall_height': 640, 'roof': 'none', 'windows': 'none'}]})
    for i, (at, h) in enumerate([((69.8, 70.6), 192), ((70.6, 71.6), 160), ((74.2, 70.4), 176),
                                 ((75.0, 69.2), 160), ((69.0, 68.6), 192)]):
        S({'id': 'thing:isle_grave_%d' % (i + 1), 'kind': 'obelisk', 'at': list(at), 'height': h, 'width': 64,
           'textures': {'wall': 'cswl128'}, 'title': 'A grave'})
    for i, (d, at) in enumerate([('swptree1', (68.6, 66.8)), ('swptree3', (75.6, 66.6)), ('swptree2', (76.6, 70.4)),
                                 ('swptree4', (68.2, 71.2)), ('dec05', (70.2, 72.0)), ('7dec18', (74.6, 71.6))]):
        S(deco('thing:isle_dressing_%d' % (i + 1), d, at))
    # ---------------------------------------------------------------- Castle Blackfang (towers kit, Darkside)
    x0, y0, x1, y1 = CASTLE_BOX
    S({'id': 'thing:blackfang_curtain', 'kind': 'wall', 'line': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], 'closed': True,
       'height': 512, 'thickness': 96, 'battlements': True, 'textures': {'wall': 'hkm2bs', 'top': 'hkm2bs'},
       'title': 'Castle Blackfang'})
    TOWER_R = 328                  # 16 sides: each face 128 wide (a window once, whole)

    def round_tower(tid, at, storeys, top_win=True):
        parts = [{'id': 'base', 'shape': 'round', 'at': [512, 512], 'radius': TOWER_R, 'sides': 16,
                  'wall_height': 256 * storeys, 'roof': 'none', 'windows': 'none',
                  'textures': {'wall': 'hkm2bs', 'trim': 'hkm2bs'}},
                 {'id': 'frieze', 'shape': 'round', 'at': [512, 512], 'radius': TOWER_R, 'sides': 16,
                  'bottom': 256 * storeys, 'wall_height': 256, 'roof': 'none', 'windows': 'none',
                  'textures': {'wall': 'hkm3b', 'trim': 'hkm2bs'}},
                 {'id': 'top', 'shape': 'round', 'at': [512, 512], 'radius': TOWER_R, 'sides': 16,
                  'bottom': 256 * (storeys + 1), 'wall_height': 256, 'roof': 'cone', 'roof_pitch': 70,
                  'windows': 'alternate' if top_win else 'none',
                  'textures': {'wall': 'hkm2bs', 'window': 'hkm3elw', 'roof': 'xtslate', 'trim': 'hkm2bs'}}]
        S({'id': tid, 'kind': 'building', 'at': [at[0] - 1, at[1] - 1], 'size': [2, 2], 'kit': 'grey',
           'door': 'none', 'floor': CRAG_TOP, 'title': 'Castle Blackfang', 'parts': parts})
    for k, (u, v) in (('nw', (x0, y0)), ('ne', (x1, y0)), ('sw', (x0, y1)), ('se', (x1, y1))):
        round_tower('thing:blackfang_tower_%s' % k, (u, v), 4)
    # the keep: four storeys of black rubble with one yellow-glass window in each face's middle bay, the skull frieze
    # as the band of its fifth, a slate hip roof
    kw, kd = 1536, 1280
    nbx, nby = kw // 128, kd // 128
    # one yellow-glass window per face and storey, a bay to the side of the one below it (never stacked up the wall)
    keep_parts = []
    for k in range(6):
        off = (-2, 2)[k % 2]
        kwalls = {'s': bays(nbx, nbx // 2 + off), 'n': bays(nbx, nbx // 2 - off), 'e': bays(nby, nby // 2 + off),
                  'w': bays(nby, nby // 2 - off)}
        keep_parts.append({'id': 'storey_%d' % (k + 1), 'at': [256, 256], 'size': [kw, kd], 'bottom': 256 * k,
                           'wall_height': 256, 'roof': 'none', 'walls': kwalls})
    keep_parts[0].pop('bottom')
    keep_parts.append({'id': 'frieze', 'at': [256, 256], 'size': [kw, kd], 'bottom': 1536, 'wall_height': 256,
                       'roof': 'hip', 'roof_pitch': 55, 'windows': 'none',
                       'textures': {'wall': 'hkm3b', 'roof': 'xtslate', 'trim': 'hkm2bs'}})
    S({'id': 'thing:blackfang_keep', 'kind': 'building', 'at': [KEEP[0] - 2, KEEP[1] - 1.75], 'size': [4, 3.5],
       'kit': 'grey', 'door': 'none', 'floor': CRAG_TOP, 'title': 'The keep of Castle Blackfang',
       'textures': {'wall': 'hkm2bs', 'window': 'hkm3elw', 'trim': 'hkm2bs', 'roof': 'xtslate',
                    'post_left': 'hkm2bs', 'post_right': 'hkm2bs'},
       'parts': keep_parts})
    # beacon fires on the curtain's walk (floor fixtures on the walk), seen from Lakeside at night
    for i, (u, v) in enumerate(((x0 + 1.3, y1), (x0 + 2.9, y1), (x1 - 2.9, y1), (x1 - 1.3, y1), (x0, y0 + 2.2),
                                (x1, y0 + 2.2))):
        S(deco('thing:blackfang_beacon_%d' % (i + 1), 'dec60', (u, v), **{'raise': 512}))
    # Lakeside's yard trees (town_feel: a shipped town has a few; behind or beside houses, never before a door)
    for i, (d, at) in enumerate(TOWN_TREES):
        S(deco('thing:town_tree_%d' % (i + 1), d, at))
    # the bat storm: S's model when it exists, else nothing (no stand-in); its spots stay in BAT_STORM_SPOTS
    if BAT_STORM_MODEL:
        for name, at, z, size in BAT_STORM_SPOTS:
            S(deco('thing:bat_storm_%s' % name, BAT_STORM_MODEL, at, **{'raise': z - CRAG_TOP}))
    # the gatehouse at the crag's west foot: two squat round towers either side of a gate block; the gate a hinged
    # pair (hkm1dl, the second leaf mirrored), never opens (m25.blackfang_gate)
    gx, gy = GATEHOUSE
    # D-42 (1): the gate never opens; after m25.done (111503) its click asks aaze0021:9 and Ambrose's griffin flies the
    # party onto DD-14's walls (entrance:d4_griffin; sealed until DD-14 lists it; A3's m25.gate_flight when it exists)
    # s32 (F16, D-90 1(d)): the griffin's offer is a choice, so its answer moves directly (no entrance window), and
    # its buttons say what they do (not Yes/No: the audit's entrance.question is for questions the window asks)
    fly = (move_lua('dd14', direct=True) if DUNGEON['dd14'] else
           'evt.StatusText(%s)' % lstr("The griffin circles once and lands again. (Castle Blackfang comes in a later "
                                      "part of the world.)"))
    if 'm25.gate_flight' in HOOKS:
        fly = 'if %s then %s end' % (hcall('m25.gate_flight'), fly)
    # D-72 rule 3: one Yes/No button prompt whose own text is the source's line (it ends on the request), no
    # SetMessage before it; Yes is step 1, No 2, Escape 3
    gate_lua = ('if continueStep == 1 then %s return end if continueStep ~= nil then return end '
                'if %s then AskChoiceWithAnswerSteps(eventId, 3, "Hello again, Adventurers. Would you like my griffin '
                'to fly you inside?", {{Answer = "Fly in", Step = 1}, {Answer = "Stay here", Step = 2}}) return end %s'
                % (fly, 'XeenQuests.can("m25.gate_flight")' if 'm25.gate_flight' in HOOKS else 'Xeen.isSet("m25.done")',
                   hcall('m25.blackfang_gate')))
    gh = {'id': 'thing:blackfang_gatehouse', 'kind': 'building', 'at': [gx - 1.0, gy - 1.6], 'size': [2.0, 3.2],
          'kit': 'grey', 'facing': 'w', 'floor': 1184, 'title': "Castle Blackfang's gate",
          'textures': {'wall': 'hkm2bs', 'door': 'chb1dl', 'trim': 'hkm2bs', 'window': 'hkm2bs',
                       'roof': 'xtslate', 'post_left': 'hkm2bs', 'post_right': 'hkm2bs'},
          'parts': [{'id': 'gate', 'at': [128, 448], 'size': [768, 768], 'wall_height': 640, 'roof': 'flat',
                     'battlements': True, 'windows': 'none', 'door_height': 448,
                     'walls': {'w': [['wall', 192], ['door', 384], ['wall', 192]]}},
                    {'id': 'tower_n', 'shape': 'round', 'at': [512, 300], 'radius': 248, 'sides': 12,
                     'wall_height': 768, 'roof': 'cone', 'roof_pitch': 68, 'windows': 'none'},
                    {'id': 'tower_s', 'shape': 'round', 'at': [512, 1338], 'radius': 248, 'sides': 12,
                     'wall_height': 768, 'roof': 'cone', 'roof_pitch': 68, 'windows': 'none'}],
          'door': {'part': 'gate', 'wall': 'w', 'leaves': 2},
          'effects': [{'lua': gate_lua}],
          'notes': "m25.blackfang_gate: never opens (DD-14 is entered by the griffin from D6, m25.flight)."}
    S(gh)
    # ---------------------------------------------------------------- the north and the uplands
    S({'id': 'thing:snow_bridge', 'kind': 'bridge', 'line': SNOW_BRIDGE, 'width': 320, 'rise': 32, 'kerb': 48,
       'textures': {'deck': '7trimda'}, 'title': 'The Snow River bridge'})
    S({'id': 'thing:resilience_fountain', 'kind': 'fountain', 'at': [100.0, 38.0], 'title': 'Fountain of Great Resilience',
       'tiers': [[64, 24]], 'textures': {'wall': 'hkm2bs'},
       **daily('d4_resilience_fountain', [{'add': {'var': 'HP', 'value': 200}},
                                          {'text': 'Cold water, and the cold goes into your bones and stays there as '
                                                   'strength. +200 Hit points'}],
               'The water is still. Come back tomorrow.')})
    S({'id': 'thing:roc_nest', 'kind': 'chest', 'at': [70.0, 33.0], 'title': "A roc's nest",
       'chest': {'level': 3, 'random_items': 2},
       'notes': "A lost courier's satchel in the bones."})
    S(deco('thing:nest_bones', '7dec18', (70.7, 33.4)))
    S({'id': 'thing:frozen_pilgrim', 'kind': 'chest', 'at': [64.6, 31.0], 'title': "A frozen pilgrim's pack",
       'chest': {'level': 3, 'random_items': 2}})
    S(deco('thing:pilgrim_bones', 'dec05', (65.1, 30.6)))
    # ---------------------------------------------------------------- Magic Mountain
    cx_, cy_ = CAMP
    S({'id': 'thing:magic_fountain', 'kind': 'fountain', 'at': [29.0, 49.0], 'title': 'Fountain of Great Magic',
       'tiers': [[64, 24]], 'textures': {'wall': 'cswl128'},
       **daily('d4_magic_fountain', [{'add': {'var': 'SP', 'value': 200}},
                                     {'text': 'Xanthus says it tastes of nothing. +200 Spell points'}],
               "Xanthus' fountain is resting. Come back tomorrow.")})
    # the wizards' two tents (A6's review: a tent building of the shipped tent textures, as D3's market stalls)
    for i, (at, facing) in enumerate([((24.6, 47.6), 's'), ((30.2, 50.8), 'w')]):
        S({'id': 'thing:camp_tent_%d' % (i + 1), 'kind': 'building', 'at': list(at), 'size': [1.4, 1.4],
           'kit': 'grey', 'door': 'none', 'facing': facing, 'floor': CAMP_H, 'title': "A wizard's tent",
           'textures': {'wall': 'tentwal3', 'gable': 'tentwal3', 'roof': 'tentrf3', 'trim': 'tentwal3',
                        'ridge': 'tentwal3', 'post_left': 'tentwal3', 'post_right': 'tentwal3', 'window': 'tentwal3',
                        'door': 'tentdor3'},
           'parts': [{'id': 'tent', 'at': [80, 80], 'size': [556, 556], 'wall_height': 128, 'roof': 'gable',
                      'roof_pitch': 58, 'windows': 'none'}]})
    S(deco('thing:camp_fire', 'dec24', (27.4, 49.6), title='A camp fire'))
    S(deco('thing:genie_lamp_seat', '7dec41', (36.0, 43.6), title="A genie's lamp",
           condition={'not': {'map_var': 'lamp_seat_rubbed'}},
           else_effects=[{'text': 'The lamp is cold. Its genie has gone back in for good.'}],
           effects=[{'set': {'var': {'map_var': 'lamp_seat_rubbed'}, 'value': 1}}, {'gold': 5000},
                    {'text': ("You rub the lamp. A genie unfolds out of it and grants you a small wish: 5,000 gold. "
                              "'Small wishes come true,' it says, and goes back in.")}]))
    # Ector's woodpile (q-d21.woodpile) in the woodcutters' clearing
    S({'id': 'thing:woodpile', 'kind': 'building', 'at': [WOODPILE[0] - 0.4, WOODPILE[1] - 0.25],
       'size': [0.8, 0.5], 'kit': 'grey', 'door': 'none', 'title': 'Woodpile', 'floor': CLEARING_H,
       'parts': [{'id': 'pile', 'at': [24, 24], 'size': [360, 208], 'wall_height': 160, 'roof': 'gable',
                  'roof_pitch': 20, 'ridge_along': 'ew', 'windows': 'none',
                  'textures': {'wall': '7trimda', 'roof': 't06a10', 'gable': '7trimda'},
                  'title': 'Woodpile', 'effects': hook('q-d21.woodpile')}]})
    S(deco('thing:clearing_stump_1', 'stump5a', (46.2, 50.4)))
    S(deco('thing:clearing_stump_2', 'stump5a', (49.2, 52.8)))
    # DD-23's cave mouth: an open mouth, no leaves. D-72: no map message; q-d15.lair_door's line first (its
    # SimpleMessage), then Yes/No buttons "Enter the cave?" (the window shows both lines, A6 s24), and the studio's
    # `into` move on Yes only
    lair = {'id': 'thing:dd23_lair', 'kind': 'cave_mouth', 'at': [LAIR[0] - 1, LAIR[1] - 2], 'size': [1024, 1024],
            'title': 'A cave in the crag'}
    if DUNGEON['dd23']:
        # s32 (F16): no question; the look is trans row 5058 in the entrance window (A3 retired the hook
        # q-d15.lair_door: no use() here, A4 2026-11-22)
        lair['into'] = {'map': 'xeen_dd23.blv', 'arrival': ENTRANCE['dd23']}
    else:
        lair['effects'] = [{'text': ("Ten steps in, the cave is choked with fallen rock and droppings. (The "
                                     "gargoyles' lair comes in a later part of the world.)")}]
    S(lair)
    # ---------------------------------------------------------------- the Forest of Peril
    # Leafpoint's grove of great trees (Leafpoint himself an MM7 Treant, placed below)
    for i, (d, ang, r) in enumerate([('tree69', 20, 2.3), ('tree60a', 95, 2.4), ('tree69', 165, 2.2),
                                     ('tree60a', 230, 2.5), ('tree69', 300, 2.3)]):
        a = math.radians(ang)
        S(deco('thing:grove_tree_%d' % (i + 1), d, (GROVE[0] + r * math.cos(a), GROVE[1] + r * math.sin(a))))
    # Ector's cabin (no house: Ector talks outside it, q-d21) and his chopping block
    ex, ey = ECTOR_CABIN
    S({'id': 'thing:ector_cabin', 'kind': 'building', 'at': [ex, ey], 'size': [2, 1.5], 'kit': 'grey', 'door': 'none',
       'facing': 's', 'floor': ECTOR_H, 'title': "Ector's cabin",
       'parts': [{'id': 'cabin', 'at': [64, 64], 'size': [896, 640], 'wall_height': 256, 'roof': 'gable',
                  'roof_pitch': 40, 'ridge_along': 'ew', 'windows': 'alternate',
                  'textures': {'wall': 't06a01', 'window': 't06a04', 'roof': 'xlslatemos', 'trim': 't06a10',
                               'gable': 't06a01'}}]})
    S(deco('thing:ector_block', 'stump5a', (ex + 2.6, ey + 1.0)))
    S({'id': 'thing:hunters_hide', 'kind': 'chest', 'at': [24.0, 64.0], 'title': "An old hunter's trunk",
       'chest': {'level': 3, 'random_items': 2}})
    S({'id': 'thing:hide_hut', 'kind': 'building', 'at': [23.3, 62.4], 'size': [1.4, 1.2], 'kit': 'poor',
       'door': 'none', 'title': "An old hunters' hide",
       'parts': [{'id': 'hide', 'at': [64, 64], 'size': [588, 486], 'wall_height': 224, 'posts': 24,
                  'roof': 'lean_to', 'windows': 'none', 'textures': {'roof': 'hhp2rf', 'post': 't06a10',
                                                                      'trim': 't06a10'}}]})
    # the animal traps (hazards, not POIs): a sprung trap on the lanes, once
    for i, at in enumerate([(38, 67.5), (30, 85)]):
        S({'id': 'thing:animal_trap_%d' % (i + 1), 'kind': 'platform', 'at': list(at), 'size': [192, 192],
           'height': 8, 'textures': {'top': '7trimda', 'wall': '7trimda'}, 'title': 'Animal trap!',
           'trigger': 'step', 'once': True,
           'effects': [{'damage': {'amount': 20}}, {'text': 'Animal trap!'}]})
    # ---------------------------------------------------------------- the west shore and the heath
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': list(OBELISK), 'height': 768, 'title': 'Obelisk',
       'textures': {'wall': 'cswl128'}, 'effects': hook('obelisks.d4')})
    S(deco('thing:reed_cauldron', 'dec26', (51.4, 68.8), title="The coven's cauldron",
           # one taste by the active member (a gamble, not a party draught), once a day for the party (D-70)
           **daily('d4_reed_cauldron', [{'lua': ('if math.random(2) == 1 then AddValue(SP, 100) '
                                                'evt.StatusText("It burns all the way down. +100 Spell points") else '
                                                'SetValue(PoisonedGreen, 1) evt.StatusText("It burns all the way '
                                                'down. Poisoned!") end')}],
                   'The cauldron has gone cold. Tomorrow.', everyone=False)))
    # the Witches' Circle: standing stones round a cauldron, three skulls on stakes that speak the recipes, the
    # coven's offering chest
    S({'id': 'thing:circle_ring', 'kind': 'stone_ring', 'at': [50.0, 90.0], 'radius': 640, 'count': 7,
       'lintel': False, 'title': "The Witches' Circle"})
    S(deco('thing:circle_cauldron', 'dec26', (50.0, 90.0), title="The coven's cauldron"))
    RECIPES = ["The first skull grins: 'Eye of newt, a toad's left foot, and a broom's last bristle.'",
               "The second skull: 'Boil it till the moon looks away.'",
               "The third skull: 'Stir widdershins. Never sunwise. Never.'"]
    for i, (ang, text) in enumerate(zip((40, 160, 280), RECIPES)):
        a = math.radians(ang)
        S(deco('thing:circle_skull_%d' % (i + 1), '7dec20', (50.0 + 0.8 * math.cos(a), 90.0 + 0.8 * math.sin(a)),
               title='A skull on a stake', effects=[{'text': text}]))
    S({'id': 'thing:circle_chest', 'kind': 'chest', 'at': [51.2, 91.2], 'title': "The coven's offering chest",
       'chest': {'level': 4, 'random_items': 2}})
    S({'id': 'thing:heath_wagon', 'kind': 'chest', 'at': [52.0, 100.0], 'title': "A Sandcaster wagon's strongbox",
       'chest': {'level': 3, 'random_items': 2}})
    S(deco('thing:wagon_wreck', 'dec24x', (51.3, 100.4)))
    # Gallows Knoll: the coven's gibbet, a dead thief's purse in its cage
    S({'id': 'thing:gibbet', 'kind': 'building', 'at': [73.7, 103.6], 'size': [0.6, 0.6], 'kit': 'grey',
       'door': 'none', 'title': "The coven's gibbet",
       'parts': [{'id': 'post', 'at': [128, 128], 'size': [48, 48], 'wall_height': 512, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 't06a10', 'roof': 't06a10'}}]})
    S({'id': 'thing:gibbet_purse', 'kind': 'chest', 'at': [74.3, 104.4], 'title': "A dead thief's purse",
       'chest': {'level': 3, 'random_items': 1}})
    # ---------------------------------------------------------------- the east shore, the falls
    S({'id': 'thing:warding_well', 'kind': 'well', 'at': [88.6, 97.4], 'title': 'Fountain of Magic Resistance',
       'frame': {'height': 224, 'roof': 'gable', 'roof_height': 64},
       'condition': {'not': {'player_bit': 11340}},
       'effects': [{'player_bit': 11340}, {'add': {'var': 'MindResistance', 'value': 5}},
                   {'add': {'var': 'BodyResistance', 'value': 5}},
                   {'text': '+5 Mind and Body resistance (permanent)'}],
       'else_effects': [{'text': 'You have had your fill.'}]})
    S(deco('thing:cairn', 'searka01', (91.6, 84.0), title='A cairn of five stones', effects=hook('q-c24.cairn')))
    S(deco('thing:mirabeth', '7dec54', (95.0, 76.0), title="Mirabeth's statue",
           effects=[{'text': ("A mermaid of grey stone, looking at the water. The plaque: 'Mirabeth, who waited.'")}]))
    S({'id': 'thing:roc_hunter', 'kind': 'chest', 'at': [99.4, 99.0], 'title': "A roc-hunter's pack",
       'chest': {'level': 4, 'random_items': 2}})
    S(deco('thing:roc_hunter_bones', 'dec05', (99.9, 99.4)))
    S({'id': 'thing:falls_chest', 'kind': 'chest', 'at': [101.0, 63.4], 'title': "A fisherman's sea chest",
       'chest': {'level': 3, 'random_items': 2}})
    S({'id': 'thing:octopod_falls', 'kind': 'waterfall', 'line': [[RIM_E - 0.3, 67], [RIM_E + 3, 67]],
       'top': LAKE_H, 'foot': 0, 'width': 768, 'rise': 48, 'title': 'The Octopod Falls',
       'notes': "The lake's outflow falls off the world's edge (D-23)."})
    # the skerries' lures (water walking or flight past the octopods)
    S({'id': 'thing:skerry_strongbox', 'kind': 'chest', 'at': [61.0, 70.1], 'title': "A drowned smuggler's strongbox",
       'chest': {'level': 4, 'random_items': 2}})
    S(deco('thing:genie_lamp_skerry', '7dec41', (89.0, 70.1), title="A genie's lamp",
           condition={'not': {'map_var': 'lamp_skerry_rubbed'}},
           else_effects=[{'text': 'The lamp is cold and still wet. Its genie has gone.'}],
           effects=[{'set': {'var': {'map_var': 'lamp_skerry_rubbed'}, 'value': 1}}, {'gold': 8000},
                    {'text': ("The lamp is wet and the genie is cross about it, but it grants you a wish: 8,000 "
                              "gold, mostly dry.")}]))
    # ---------------------------------------------------------------- signposts and the sealed edge
    for sid, at, arms in (
            ('sign_well_fork', (87.0, 94.0), [('Lakeside', 'w'), ('Sandcaster', 's'), ('Mirabeth Point', 'n')]),
            ('sign_ector_fork', (37.0, 82.4), [('Lakeside', 'e'), ('The desert road', 'w'), ("Ector's", 'n')]),
            ('sign_snow_bridge', (61.8, 54.0), [('Snow Springs', 'n'), ('Lakeside', 's'), ('North shore', 'e')])):
        S({'id': 'thing:%s' % sid, 'kind': 'sign', 'at': list(at), 'height': 256,
           'arms': [{'title': t, 'toward': d} for t, d in arms]})
    if not D5_LIVE:
        S(sign('thing:west_road_end', (20.4, 80.8), 'Sign',
               'The desert road west to the Desert of Doom is closed by drifting sand. Turn back.'))
    # ---------------------------------------------------------------- actors
    actors = []

    def place(row, at, count, spread, group, **kw):
        a = {'monster': str(row), 'at': list(at), 'count': count, 'spread': spread, 'group': group}
        a.update(kw)
        actors.append(a)
    # the coven's two groups (A2's xeen_coven relations: hostile, friendly to members after q-d22.joined); hidden on
    # load once the Head Witch is dead (q-d22.coven_gone)
    place(ROW['witch'], (49.6, 89.4), 5, 1.4, G_CIRCLE)
    place(ROW['coven_witch'], (50.8, 90.4), 2, 0.8, G_CIRCLE)
    place(ROW['coven_mother'], (50.3, 89.6), 1, 0, G_CIRCLE)
    place(ROW['witch'], (50.8, 67.6), 4, 1.2, G_REEDS)
    place(ROW['coven_witch'], (50.6, 69.6), 2, 0.6, G_REEDS)
    # the five octopods in the two deep basins (D-36 (2)): A2's swim AI rows, swimmers by A1's outdoor water facts
    # (merge point 18), each home at least 2,500 from the jetty, the Isle landing and the waterfront and its home
    # radius (`leash`) inside the water: OCTOPOD_LEASH short of the nearest land (shore, Isle, skerries) by 500 and
    # never bringing it within 2,500 of those three
    OCTO = [(ROW['octopod'], (60.0, 64.0)), (ROW['octopod'], (65.0, 59.5)), (ROW['great_octopod'], (86.0, 65.5)),
            (ROW['octopod'], (93.5, 66.5)), (ROW['great_octopod'], (85.0, 74.0))]
    for (row, at), g in zip(OCTO, G_OCTOPODS):
        for (u, v) in (JETTY_END, ISLE_ARRIVAL, (at[0], 82.4)):
            if math.hypot(at[0] - u, at[1] - v) * 512 < 2500:
                raise SystemExit('an octopod within 2,500 of the jetty, the Isle landing or the waterfront: %s' % (at,))
        if not in_lake(*at) or poly_dist(at, LAKE) < 3.0:
            raise SystemExit('an octopod not in the deep water: %s' % (at,))
        land = min(poly_dist(at, p) for p in (LAKE,) + tuple(ISLETS)) * 512
        near = min(math.hypot(at[0] - u, at[1] - v) for (u, v) in (JETTY_END, ISLE_ARRIVAL, (at[0], 82.4))) * 512
        if land - OCTOPOD_LEASH < 500 or near - OCTOPOD_LEASH < 2500:
            raise SystemExit('an octopod whose home radius reaches land or the town: %s' % (at,))
        place(row, at, 1, 0, g, hostile=True, leash=OCTOPOD_LEASH)
    # townsfolk and talkers (A4's NPCs, A3's topics)
    actors.append({'monster': str(ROW['peasant_f']), 'npc': NPC['naomi'], 'at': [70.6, 90.1], 'spread': 0,
                   'group': G_NAOMI, 'hostile': False})
    actors.append({'monster': str(ROW['mage']), 'npc': NPC['slibo'], 'at': [26.5, 51.0], 'spread': 0,
                   'group': G_SLIBO, 'hostile': False})
    actors.append({'monster': str(ROW['peasant_m']), 'npc': NPC['ector'], 'at': [34.4, 72.6], 'spread': 0,
                   'group': G_ECTOR, 'hostile': False})
    actors.append({'monster': str(ROW['treant']), 'npc': NPC['leafpoint'], 'at': list(GROVE), 'spread': 0,
                   'group': G_LEAFPOINT, 'hostile': False})
    relations = [{'of': [451, 452, 453], 'toward': 'party', 'relation': 'friendly'},
                 {'of': [610, 611], 'toward': 'party', 'relation': 'friendly'}]
    # ---------------------------------------------------------------- events
    use('q-d22.coven_gone')
    sx0, sy0, sx1, sy1 = STORM_BOX
    X0, Y1 = W(sx0, sy0)
    X1, Y0 = W(sx1, sy1)
    dx, dy = W(*STORM_DROP)
    shrieks = ' '.join('evt.PlaySoundName("bat_aware", %d, %d, %d)' % (W(*at) + (z,))
                       for _, at, z, _s in BAT_STORM_SPOTS)
    events = [
        {'id': 'evt:sky', 'trigger': 'load', 'effects': [{'lua': 'Xeen.applyDarksideSky()'}],
         'notes': "Darkside's sky by the sun's stage (A3's helper)."},
        {'id': 'evt:coven_gone', 'trigger': 'load', 'condition': {'lua': 'XeenQuests.can("q-d22.coven_gone")'},
         'lua': ('evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1) evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1)'
                 % (G_CIRCLE, G_REEDS)),
         'notes': ("q-d22.coven_gone (D-36 (3)): once the Head Witch is dead the coven's two groups are gone; the "
                   "Circle's chest and skulls stay.")},
        {'id': 'evt:bat_storm', 'trigger': 'timer', 'every': 1, 'when_flying': True,
         'lua': ('local x, y, z = evt.GetPartyPosition() '
                 'if x >= %d and x <= %d and y >= %d and y <= %d and z >= %d then '
                 'evt.RemovePartyBuff("Fly") evt.MoveToMap(%d, %d, %d, 0, 0, 0, 0, 0) %s end'
                 % (X0, X1, Y0, Y1, STORM_Z, dx, dy, 1184 + 8, hcall('m25.bat_storm'))),
         'notes': ("m25.bat_storm (D-36 (1)): a flying party over the crag top is beaten out of the sky: Fly ends "
                   "(evt.RemovePartyBuff, merge point 18), the party is set down on the north-shore track, then "
                   "A3's hook (its line).")},
        {'id': 'evt:bat_shrieks', 'trigger': 'timer', 'every': 9, 'lua': shrieks,
         'notes': "The bat storm's shrieks at its two spots (BAT_STORM_SPOTS), a shipped bat sound."},
    ]
    # ---------------------------------------------------------------- scatter and ground
    scatter = []

    def sc(sid, deco_, count, poly=None, circle=None, clusters=None, spacing=None, line=None, steep=None, on=None):
        e = {'id': sid, 'decoration': deco_, 'count': count}
        if poly:
            e['polygon'] = poly
        if circle:
            e['circle'] = circle
        if line:
            e['line'] = line
        if clusters:
            e['clusters'] = clusters
        if spacing:
            e['spacing'] = spacing
        if steep:
            e['steep'] = True
        if on:
            e['on'] = on
        scatter.append(e)

    def stand(sid, poly, kinds_, per_100, spacing, close=0.1, close_spacing=1.0):
        n = int(round(per_100 * K.poly_area(poly) / 100.0))
        if n < 1:
            return
        e = {'id': sid, 'count': n, 'polygon': poly, 'spacing': spacing, 'close_share': close,
             'close_spacing': close_spacing, 'spacing_group': 'trees'}
        if len(kinds_) == 1:
            e['decoration'] = list(kinds_)[0]
        else:
            e['kinds'] = dict(kinds_)
        scatter.append(e)
    DARK = {'tree60a': 3, 'tree62a': 3, 'tree12': 2, 'tree30': 2, 'tree61a': 1}
    FOREST = [[19.5, 58], [26, 57], [36, 56], [44, 55], [45.5, 58], [38.5, 58], [38.5, 64.5], [45.5, 64.5],
              [46, 70], [50, 80], [53, 83], [44, 83.5], [37.5, 80], [37.5, 74.5], [30.5, 74.5], [30.5, 68.5],
              [37.5, 68.5], [36, 66], [28, 74], [28, 76.5], [19.5, 76.5]]
    stand('scatter:forest_north', FOREST, DARK, 26.0, 1.1, close=0.15, close_spacing=0.85)
    FOREST_S = [[19.5, 84.5], [28, 84.5], [30, 82.5], [35, 83], [44, 85], [52, 88.5], [45, 88], [44, 93.5],
                [32, 92], [19.5, 92]]
    stand('scatter:forest_south', FOREST_S, DARK, 22.0, 1.2, close=0.15, close_spacing=0.85)
    for sid, poly in (('n', FOREST), ('s', FOREST_S)):
        sc('scatter:undergrowth_%s' % sid, 'plant32', 70, poly, clusters=24)
        sc('scatter:undergrowth_%s' % sid, 'bush03', 30, poly, clusters=12)
        sc('scatter:caps_%s' % sid, 'mushrm01', 60, poly, clusters=18)
    UPLANDS = [[44, 24.6], [96, 24.6], [96, 37.5], [84, 37.5], [78, 42], [77, 50], [70, 52.6], [62, 51.6],
               [58, 50], [56, 40], [54, 28]]
    stand('scatter:snow_trees', UPLANDS, {'snotre01': 2, 'snotre03': 2, 'snotre05': 1}, 2.5, 2.4)
    sc('scatter:upland_rocks', '6rock07', 40, UPLANDS, clusters=12, steep=True)
    sc('scatter:upland_weeds', 'snoweed1', 40, UPLANDS, clusters=12)
    MOUNTAIN = [[19.5, 24.6], [44, 24.6], [54, 28], [56, 40], [54, 48], [46, 54], [36, 55.5], [26, 56.5], [19.5, 57]]
    stand('scatter:mountain_trees', MOUNTAIN, {'tree30': 2, 'snotre01': 1, 'tree25': 1}, 2.0, 2.6)
    sc('scatter:mountain_rocks', '6rock07', 60, MOUNTAIN, clusters=18, steep=True)
    sc('scatter:mountain_rocks', 'rock16', 30, MOUNTAIN, clusters=10)
    sc('scatter:crag_rocks', '6rock07', 26, CRAG, clusters=8, steep=True)
    RIMCORNER = [[96, 24.6], [103.6, 24.6], [103.6, 58], [98, 60], [96.6, 44], [96, 38]]
    sc('scatter:rimcorner_rocks', 'rock16', 16, RIMCORNER, clusters=6)
    HEATH = [[19.5, 92.5], [32, 92.5], [44, 94.5], [56, 94.5], [60, 97.5], [62, 102], [80, 100.5], [84, 101],
             [84, 108.5], [19.5, 108.5]]
    stand('scatter:heath_trees', HEATH, {'tree25': 2, 'tree62a': 1}, 1.2, 3.0)
    sc('scatter:heath_shrubs', 'plant47', 30, HEATH, clusters=12)
    sc('scatter:heath_shrubs', 'bush02', 50, HEATH, clusters=16)
    sc('scatter:heath_rocks', 'rock16', 30, HEATH, clusters=10)
    CRAGS_E = [[92.5, 86], [103.6, 84], [103.6, 108.5], [92.5, 108.5]]
    sc('scatter:rimward_rocks', '6rock07', 30, CRAGS_E, clusters=10, steep=True)
    stand('scatter:rimward_trees', CRAGS_E, {'tree25': 2, 'tree30': 1}, 2.0, 2.4)
    EAST_SHORE = [[85.5, 82.5], [90, 81.5], [94, 80.5], [95.5, 78], [93.5, 76], [95.5, 73.5], [98.5, 72.5],
                  [100.5, 69.5], [103.6, 69.5], [103.6, 84], [92, 86], [87, 90]]
    stand('scatter:east_shore_trees', EAST_SHORE, {'tree62a': 2, 'tree12': 1}, 3.0, 2.0)
    WEST_SHORE = [[46, 54], [54, 48.5], [56, 50.5], [55.5, 56], [54.5, 60], [53.5, 65], [53.5, 71], [55.5, 76],
                  [59.5, 79.4], [58.6, 81.6], [56, 83.6], [50, 80], [46, 70]]
    stand('scatter:west_shore_trees', WEST_SHORE, {'tree62a': 2, 'tree12': 1, 'tree60a': 1}, 4.0, 2.0)
    # reeds and shallows plants along the lake's south-west and north shores
    sc('scatter:reeds', 'plant05', 60, line=[[54.4, 66], [54.6, 72], [57, 77], [60, 79.6]])
    sc('scatter:reeds', 'plant05', 30, line=[[62, 55.4], [70, 56.4], [76, 57.6]])
    scatter.append({'id': 'scatter:rim_stacks', 'decoration': '6rock07', 'count': 14, 'on': 'water',
                    'polygon': [[4, 4], [100, 4], [100, 18], [4, 18]]})
    ground = [
        {'material': 'grass', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'The forest floor and the shores: grass (darkened in D4\'s terrain materials).'},
        {'material': 'dirt', 'polygon': [[19, 93], [56, 94], [62, 101], [84, 100], [84, 128], [0, 128], [0, 93]],
         'notes': ("The desert edge: dry soil (a classic map holds dirt and two more grounds: grass and the uplands' "
                   "snow; the heath is dirt).")},
        {'material': 'snow', 'polygon': [[0, 0], [104, 0], [104, 36], [92, 37], [80, 38], [60, 41], [52, 40],
                                          [40, 40], [19, 43], [0, 43]],
         'notes': "The snowfield along the north rim and Magic Mountain's head."},
        {'material': 'dirt', 'steeper_than': 560, 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'Bare rock on the steep slopes.'},
        {'material': 'dirt', 'polygon': CRAG, 'notes': "Blackfang's black crag."},
        {'material': 'dirt', 'polygon': [[59, 82.4], [86.6, 82.4], [86.6, 97.6], [59, 97.6]],
         'notes': "Lakeside's trodden ground."},
        {'material': 'dirt', 'polygon': [[24, 47], [32, 47], [32, 53], [24, 53]], 'notes': "The wizards' camp."},
    ]
    for poly in TOWN_YARDS:
        ground.append({'material': 'grass', 'polygon': poly, 'notes': "A grass yard behind Lakeside's houses (town_feel)."})
    for line in PATHS:
        ground.append({'material': 'dirt', 'line': line, 'width': 1, 'notes': 'a track'})
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('D4 Lakeside and Blackfang, written by output/studio_cal/d4/tools/gen.py. Cells [x, y], x east, y '
                  'south. Heights are map units above the stars below the rim (0): the lake 1,056, Lakeside 1,120, '
                  'the forest 1,300-1,900, the heath 1,400-2,000 (D3\'s border at y 109), the uplands to 2,400, '
                  "Blackfang's crag top 3,104, Magic Mountain 4,100."),
        'frame': frame,
        'heights': heights, 'water': water, 'roads': roads, 'districts': districts, 'points': points,
        'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground, 'structures': structures,
        'actors': actors + V.sketch_actors('D4'), 'relations': relations + V.relations('D4'),
        'events': events,
    }
    atmosphere = {'format': 0, 'sky': 'xeendark1', 'weather': {}, 'view_distance': 1.6,
                  'notes': ("Darkside's sky by the continent (7: xeendark1; A3's Lua sets the failing-sun stages); "
                            "no weather (D4's brief). view_distance 1.6: the keep at 17,600 from the jetty's end "
                            "reads in the signature view (D-36; the default far clip is 16,192). The bright face's "
                            "rim glow is the sky theme's (A6's sky file).")}
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
    if missing and os.environ.get('D4_TOWN_OPEN') != '1':
        raise SystemExit('hooks with map D4 not wired: %s' % missing)
    globals()['E3_AREA'] = E3_AREA

    def dump(folder, name, data):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)
    dump(OUT, 'project.yml', project)
    dump(OUT, 'plan.yml', plan)
    # AU's outdoor bed (E9, merge point 20; devdocs/xeen/AUDIO.md "Outdoor beds"): the scene's ambient_sounds
    sketch['sounds'] = (sketch.get('sounds') or []) + yaml.safe_load(open(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '../common/beds/d4.yml')))['sounds']
    # F2 (2026-11-21): wing door pictures (t06a03/t06b03, t09a03a) hung as double doors, never alone
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    import house_doors as HD
    for _note in HD.double_doors_sketch(sketch) + HD.bury_mouths_sketch(sketch) + HD.blind_mouths_sketch(sketch):
        print('door:', _note)   # F8 too: cave mouths as wide as their rim, no dark mouth that leads nowhere
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sketch, 'd4'):
        print('wild:', _note)
    # The classic kits (2026-11-24): Clouds of Xeen's own walls on the map's buildings (classic_kit.yml)
    import classic_kit as CK
    for _note in CK.apply(sketch, 'd4'):
        print(_note)
    import entrance_screens as ES     # F16/D-90 (s32): each dungeon door's trans.txt row in its entrance window
    print('entrance screens:', ES.apply_sketch(sketch, 'xeen_d4'))
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
    print('D3_LIVE', D3_LIVE, 'D5_LIVE', D5_LIVE, 'HOUSE_LIVE', HOUSE_LIVE, 'bat storm model', BAT_STORM_MODEL,
          'dungeons live', sorted(k for k, v in DUNGEON.items() if v))


if __name__ == '__main__':
    build()
