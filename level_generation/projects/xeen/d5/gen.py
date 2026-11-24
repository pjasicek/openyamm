#!/usr/bin/env python3
"""D5 Desert of Doom: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml) and the L2 and L3
briefs beside it from the approved L1 (devdocs/xeen/briefs/d5/L1, written by level_generation/xeen_art/phase5/
d5_brief.py with D-49 applied) and the decider's changes D-49 (briefs/d5/L1/D49_DECISION.md).

The Great Pyramid (DD-15, sealed until A8 installs it) of MM6 Tomb of VARN stone under a gilded capstone, no steps;
the broken travel pyramid with its capstone (one spot); the Parabolic Barrier (Ancient frames and an xafield curtain,
a blocking face to the fly ceiling, no event); Gurodel's hold with the People (11083-11085, peaceful, the first six
actors for the struck timer) and DD-24's great doors (live: A7's BLV lists entrance:d5_hold); DD-18's grate (live);
the Northern Tower (DD-08), Bosco's door (DD-25), both sealed until A8's BLVs exist; the Enchanted Boulders in two
chained rings (BOULDER_LIVE: S's model, else a shipped rock holds each spot); the Quivering Forest's wild cyclopes.
World: xeen. Hooks: A3's quest_hooks.yml (`map: D5`). Rows: A2's (map_stats 9112).
The project files are this script's output: edit here and run ../v.sh, never the files.
Coordinates: terrain cells [x, y], x east, y south from the north-west corner; X = (x - 64) * 512, Y = (64 - y) * 512.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import json
import math
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kit as K  # noqa: E402

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/d5'
OUT = os.path.join(BRIEFS, 'L4')
STEM = 'xeen_d5'
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
WORLD = os.path.join(REPO, 'assets_dev/worlds/xeen')
_STATS = open(os.path.join(WORLD, 'data_tables/map_stats.txt')).read()


def live(stem, env):
    return os.path.exists(os.path.join(WORLD, 'maps', stem)) or os.environ.get(env) == '1'


def studio_entrances(stem):
    f = os.path.join(WORLD, 'maps', stem.replace('.blv', '.studio.yml').replace('.odm', '.studio.yml'))
    if not os.path.exists(f):
        return {}
    d = yaml.safe_load(open(f)) or {}
    out = {}
    for a in d.get('arrivals') or d.get('entrances') or []:
        if isinstance(a, dict) and (a.get('id') or a.get('name')):
            out[a.get('id') or a.get('name')] = a
    return out


D4_LIVE = live('xeen_d4.odm', 'D5_D4_LIVE')
D6_LIVE = live('xeen_d6.odm', 'D5_D6_LIVE')
# a dungeon door opens when its BLV is installed, A2's map_stats row names it and its studio sidecar lists the
# entrance the door names (D-37: entrance:d5_*); until then the door shows a short sealed line
ENTRANCE = {'dd24': 'entrance:d5_hold', 'dd18': 'entrance:d5_grate', 'dd15': 'entrance:d5_door',
            'dd08': 'entrance:d5_tower', 'dd25': 'entrance:d5_bosco'}


def dungeon_live(key):
    blv = 'xeen_%s.blv' % key
    if os.environ.get('D5_%s_LIVE' % key.upper()) == '1':
        return True
    return live(blv, '_') and ('\t%s\t' % blv in _STATS) and ENTRANCE[key] in studio_entrances(blv)


DUNGEON = {k: dungeon_live(k) for k in ENTRANCE}
_DECOS = yaml.safe_load(open(os.path.join(WORLD, 'models/decorations.yml')))['decorations']
BOULDER_MODEL = next((str(d.get('name')) for d in _DECOS if 'boulder' in str(d.get('name')).lower()), None)
BOULDER_LIVE = BOULDER_MODEL is not None
BOULDER_STANDIN = 'rock24'      # a shipped great rock holds each boulder's spot until S's model exists
# AU's beds (D-48): the lane's copy if there is one, else AU's review list (relayed by the lead, 2026-11-21)
BEDS = next((f for f in (os.path.join(REPO, 'level_generation/projects/xeen/common/beds/xeen_d5.yml'),
                         os.path.join(REPO, 'level_generation/projects/xeen/common/beds/d5.yml'))
             if os.path.exists(f)), os.path.join(REPO, 'level_generation/projects/xeen/common/beds/xeen_d5.yml'))

# ---------------------------------------------------------------------------------------------------------------
# A3's hooks on D5 (data_tables/quest_hooks.yml, `map: D5`); every one must be used (checked at the end)
HOOKS = {k: v for k, v in yaml.safe_load(open(os.path.join(WORLD, 'data_tables/quest_hooks.yml'))).items()
         if isinstance(v, dict) and v.get('map') == 'D5'}
USED = set()


def use(name):
    assert name in HOOKS, name
    USED.add(name)
    return name


def hcall(name):
    return 'XeenQuests.hook("%s")' % use(name)


def hook(name):
    return [{'lua': hcall(name)}]


def lstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')


def msg(text):
    return {'lua': 'evt.SimpleMessage(%s)' % lstr(text)}


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d


def sign(sid, at, title, text, height=224, width=160, **kw):
    s = {'id': sid, 'kind': 'sign', 'at': [round(at[0], 3), round(at[1], 3)], 'height': height, 'width': width,
         'title': title, 'effects': [msg(text)]}
    s.update(kw)
    return s


def move_lua(key):
    blv = 'xeen_%s.blv' % key
    a = studio_entrances(blv)[ENTRANCE[key]]
    at = a.get('at') or a.get('position')
    return 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, 0, 0, "%s")' % (at[0], at[1], at[2], int(a.get('facing', 0)), blv)


SEALED = '(Not yet open: this place comes in a later part of the world.)'

# ---------------------------------------------------------------------------------------------------------------
# Land: the L1's height points (with the border points) interpolated, then the places' terraces and the borders
# carried cell for cell (east: D4's installed x 19 column; west: the shared edge file; south: D2's installed y 19).
# ---------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(REPO, 'util'))
from map_export import parse_odm_file  # noqa: E402


def _column(stem, x=None, y=None):
    hm = parse_odm_file(Path(os.path.join(WORLD, 'maps', stem)))['payload']['height_map']
    if x is not None:
        return [hm[j * 128 + x] * 32 for j in range(128)]
    return [hm[y * 128 + i] * 32 for i in range(128)]


EAST = _column('xeen_d4.odm', x=19)
SOUTH = _column('xeen_d2.odm', y=19)
WEST = json.load(open(os.path.join(REPO, 'level_generation/xeen_art/phase5/edge_d5_d6.json')))['heights_by_y']
RIM_N = 24
L1S = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'sketch.yml')))
CONTROL = [(p['at'][0], p['at'][1], p['h']) for p in L1S['heights']['points']]
# extra control (the highlands' crest raised a little: D-49 (6), relief measured inside the box at L4)
CONTROL += [(101, 103.6, 1950), (99.5, 103.4, 1900), (102.5, 103.4, 1900), (83, 40.5, 3350), (86, 40.5, 3450), (89, 40.5, 3350), (57, 46, 3150),
            (57.5, 44, 3050), (57.5, 48, 3000), (80, 30, 3850), (72, 31, 3600), (26, 30, 3300), (24, 46, 3000), (28, 100, 2600)]

PYR = (58.0, 80.0, 70.0, 92.0)          # the Great Pyramid's base, 12 x 12 cells
PYR_H = 1248
OASIS = [[42, 77], [45, 76.5], [46.5, 78.5], [45, 80.5], [42.5, 80]]
POND_H = 1312
HOLD_H = 2688
TERRACES = [
    ((57.0, 78.6, 71.0, 93.0), PYR_H, 3, "The Great Pyramid's sand plinth and the door's apron."),
    ((83.0, 42.6, 90.0, 48.5), HOLD_H, 1, "Gurodel's shelf: the ring of slabs, the fire and the great doors."),
    ((59.2, 44.5, 63.0, 48.0), 2656, 1, "Bosco's terrace under the crag."),
    ((67.0, 37.5, 71.5, 41.5), 3008, 3, "The Northern Tower's knoll."),
    ((29.0, 86.0, 34.0, 90.0), 1888, 1, "The Shrine of Great Power's mesa top."),
    ((99.5, 99.0, 103.0, 101.6), 1440, 1, "The grate's hollow before the hill foot."),
    ((102.0, 77.5, 108.0, 82.5), 1504, 4, "The D4 arrival: the level valley (D-36 (7))."),
    ((20.5, 62.0, 26.0, 66.0), 1696, 3, "The D6 arrival on the pass (edge_d5_d6.json)."),
    ((93.0, 70.5, 97.0, 74.5), 1600, 2, "The broken travel pyramid's shelf by the road."),
    ((33.5, 38.0, 37.0, 42.0), 2688, 2, "The cyclopes' lair clearing."),
    ((84.0, 79.5, 87.5, 83.0), 1376, 2, "The east boulders by the desert road."),
    ((35.5, 69.0, 39.0, 72.0), 1488, 2, "The west boulders by the west road."),
    ((45.0, 71.0, 47.5, 73.5), 1472, 2, "The obelisk's knoll."),
    ((45.5, 28.0, 48.5, 30.5), 2944, 2, "The Fountain of Energy Resistance by the Barrier's west end."),
    ((100.5, 29.5, 103.5, 32.5), 3136, 2, "The Fountain of Might under the rim."),
    ((100.0, 48.5, 104.0, 51.5), 2496, 2, "The dwarf prospectors' camp."),
]
SANDS = [[56, 59.5], [72, 60.5], [86, 62], [100, 62], [100, 86], [102, 101], [52, 101], [54, 96], [52, 78], [56, 72]]


def in_box(p, b, pad=0.0):
    return b[0] - pad <= p[0] <= b[2] + pad and b[1] - pad <= p[1] <= b[3] + pad


def box_dist(p, b):
    dx = max(b[0] - p[0], 0, p[0] - b[2])
    dy = max(b[1] - p[1], 0, p[1] - b[3])
    return math.hypot(dx, dy)


def land(x, y):
    if y < RIM_N:
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
    h = num / den
    # dunes in the Perishing Sands (long crests across the wind), stony roll elsewhere
    if K.inside((x, y), SANDS):
        h += 110 * math.sin(x / 2.3 + 0.4 * y) * math.sin(y / 3.7) + 60 * math.sin((x - 2 * y) / 3.1)
    else:
        h += 50 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.6 + 1.1)
    for b, th, slope, _n in TERRACES:
        d = box_dist((x, y), b)
        if d < slope + 0.01:
            t = smooth(d / max(slope, 0.5))
            h = th * (1 - t) + h * t
    if K.inside((x, y), OASIS):
        h = POND_H - 96
    else:
        d = min(K.seg_dist((x, y), OASIS[i], OASIS[(i + 1) % len(OASIS)]) for i in range(len(OASIS)))
        if d < 3:
            h = min(h, POND_H + 24 + 60 * d)
    # the borders, blended over the last four cells (the border cell itself is a height point below)
    if x < 23:
        t = smooth((23 - x) / 4.0)
        h = h * (1 - t) + WEST[max(0, min(127, int(round(y))))] * t
    if x > 105:
        t = smooth((x - 105) / 4.0)
        h = h * (1 - t) + EAST[max(0, min(127, int(round(y))))] * t
    if y > 105:
        t = smooth((y - 105) / 4.0)
        h = h * (1 - t) + SOUTH[max(0, min(127, int(round(x))))] * t
    return h


def grid_rows(step=4, unit=32):
    return [[max(0, int(round(land(step * i + step / 2, step * j + step / 2) / unit))) for i in range(128 // step)]
            for j in range(128 // step)]


# ---------------------------------------------------------------------------------------------------------------
# Places (cells)
# ---------------------------------------------------------------------------------------------------------------
EAST_START = (105.0, 80.0)        # entrance:d4_road, facing west
WEST_START = (23.0, 64.0)         # entrance:d6_pass, facing east
PYR_DOOR = (64.0, 79.4)           # the pyramid's north door (porch front)
HOLD_FIRE = (86.5, 46.5)
GIANTS_DOORS = (86.0, 42.4)       # the great doors' front (south face of the hall block)
DD24_ARRIVAL = (86.0, 43.0)       # A7's return point (11264, 10752), facing south
GRATE = (101.0, 102.0)
BOSCO = (61.0, 46.25)             # Bosco's door (east face of the crag block)
TOWER = (69.0, 39.0)
BROKEN = (95.0, 72.0)
CAPSTONE = (95.6, 73.35)
OBELISK = (46.25, 72.25)
LAST_WATER = (46.6, 78.8)
SHRINE = (31.5, 88.0)
FOUNTAIN_ENERGY = (47.0, 29.2)
FOUNTAIN_MIGHT = (102.0, 31.0)
LAIR = (35.2, 40.0)
LAMP_HILLS = (24.0, 98.0)
LAMP_DUNE = (85.0, 96.0)
EYRIE = (50.0, 54.0)
# F10 (s32): three of the ten (28, 74), (31, 96), (22, 104) moved north (the north birds in the areas below) and
# (24, 84) to the open sand north of the pyramid (68, 73)
DOOM_BIRDS = [(24, 72), (33, 80), (68, 73), (37, 87), (26, 92), (40, 92), (44, 98)]
# D-49 change 1: two chained rings; each boulder within 400 (0.78 cells) of the next. East: the sign and 3-6.
EAST_RING_C = (85.6, 81.2)
WEST_RING_C = (37.2, 70.6)


def ring(c, n, r_units, start_deg):
    r = r_units / 512.0
    return [(c[0] + r * math.cos(math.radians(start_deg + k * 360.0 / n)),
             c[1] + r * math.sin(math.radians(start_deg + k * 360.0 / n))) for k in range(n)]


# A6 s24 (S's boulder, 300 across, 330 deep): radius 339 east, 230 west so neighbours stand 398-399 apart, gaps 70-100
EAST_RING = ring(EAST_RING_C, 5, 339, 200)     # [sign, 3, 4, 5, 6]: 399 apart (340 rounds past the 400 chain)
WEST_RING = ring(WEST_RING_C, 3, 230, 90)      # [1, 2, 7]: 398 apart


def outward_turn(at, c):
    """S's boulder faces out of its ring: the sketch's turn (degrees clockwise from east, the cells' y running
    south) is the angle from the ring's centre to the boulder in cell axes."""
    return round(math.degrees(math.atan2(at[1] - c[1], at[0] - c[0])))     # -180..180 (the schema's range)
BARRIER = [[46, 24.2], [52, 28.5], [58, 31.5], [64, 33.5], [70, 34.5], [76, 34.5], [82, 33.5], [88, 31.5],
           [94, 28.5], [100, 24.2]]
DESERT_ROAD = [[127, 80], [109, 80], [105, 80], [100, 79], [94, 78.5], [88, 78.5], [84, 78], [80, 77]]
WEST_ROAD = [[80, 77], [76.5, 75], [74, 73], [70, 72.5], [64, 72], [58, 71.5], [52, 71], [47, 70.5], [43, 69.5],
             [40, 68], [36, 67], [32, 66], [28, 64.5], [24, 64], [19, 64], [0, 64]]


def build():
    os.makedirs(OUT, exist_ok=True)
    L1P = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'project.yml')))
    L1 = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'plan.yml')))
    # ================================ project.yml
    neighbours = []
    for n in L1P['neighbours']:
        n = copy.deepcopy(n)
        nid = n['id']
        if nid == 'edge:east':
            if not D4_LIVE:
                continue
        elif nid == 'edge:west':
            if not D6_LIVE:
                continue
            n.pop('listed_only', None)
        elif nid.startswith('door:'):
            key = nid.split(':')[1]
            n['arrival_hint'] = '%s in %s' % (ENTRANCE[key], n['to'])
            if DUNGEON[key]:
                n['arrival'] = ENTRANCE[key]
                n.pop('condition', None)
            else:
                n['listed_only'] = True
                n.pop('condition', None)
        neighbours.append(n)
    project = copy.deepcopy(L1P)
    project['neighbours'] = neighbours
    project['map_stats']['continent'] = 7
    project['notes'] = ("D5 Desert of Doom (A6, 2026-11-21), built from the approved L1 with D-49. The east edge (D4) "
                        "is live; the west edge (D6) is sealed by a sign until D6 is installed; each dungeon door shows "
                        "its hook and a sealed line until its BLV is installed and lists the door's entrance. Written "
                        "by output/studio_cal/d5/tools/gen.py.")
    # ================================ plan.yml
    plan = copy.deepcopy(L1)
    plan['level'] = 'L3'
    ents = []
    for e in plan['entrances']:
        e = dict(e)
        if e['id'] == 'entrance:dd24_doors':
            e['id'] = 'entrance:dd24_hold'
            e['how'] = ("DD-24's way out (A7): before the great doors behind Gurodel's fire, facing south, about "
                        "1,500 from Gurodel; the doors lead to DD-24's entrance:d5_hold.")
        if e.get('neighbour') == 'edge:west' and not D6_LIVE:
            e = {'id': e['id'], 'space': e['space'], 'kind': 'arrival', 'facing': 'e',
                 'how': "The road on the pass: the edge to D6 is sealed by a sign until D6 is installed."}
        if e.get('neighbour', '').startswith('door:'):
            key = e['neighbour'].split(':')[1]
            e.pop('condition', None)
            if not DUNGEON[key]:
                e = {k: v for k, v in e.items() if k != 'neighbour'}
                e['kind'] = 'arrival'
        ents.append(e)
    ents.sort(key=lambda e: e['id'] != 'entrance:d4_road')
    plan['entrances'] = ents
    # D-58 Q10 (A6 s16): a fall from D7's zone C1-D2 lands here (Xeen.SkyFalls.d7_d5); whole flat cell, 256 clear
    plan['entrances'].append({'id': 'entrance:d7_fall', 'space': next(e['space'] for e in ents if e['id'] == 'entrance:dd15_door'),
                              'kind': 'both', 'facing': 's',   # 'arrival' would make it the party start
                              'how': "D-58 Q10: a fall from D7 lands here, on the road 2,757 north of the Great Pyramid's door, facing it (its sky door leads back up after m30.done); the L1's point lay inside the pyramid."})
    for lk in plan['links']:
        if lk.get('to') == 'entrance:dd24_doors':
            lk['to'] = 'entrance:dd24_hold'
    plan.pop('totals', None)
    plan['sketch'] = {'file': 'sketch.yml', 'grid': 512}
    plan['notes'] = ('L3/L4 written by output/studio_cal/d5/tools/gen.py from the approved L1 and D-49. The People '
                     'and the eyrie griffins are placed actors, the lizards, birds and wild cyclopes slot markers.')
    # ================================ sketch.yml
    frame = copy.deepcopy(L1S['frame'])
    frame['edges'] = [e for e in frame['edges'] if (e['side'] == 'east' and D4_LIVE) or (e['side'] == 'west'
                                                                                         and D6_LIVE)]
    bpoints = []
    for y in range(RIM_N + 1, 110):
        bpoints.append({'at': [19, y], 'h': WEST[y]})
        bpoints.append({'at': [109, y], 'h': EAST[y]})
    for x in range(20, 109):
        bpoints.append({'at': [x, 109], 'h': SOUTH[x] if x < 100 else round(
            SOUTH[x] * (1 - smooth((x - 100) / 9.0)) + EAST[109] * smooth((x - 100) / 9.0))})
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its land function.'},
        'points': bpoints + [
            {'at': [80, 30], 'h': 3850, 'notes': "Gurodel's Crown, the highlands' crest (D-49 (6))"},
            {'at': [90, 92], 'h': 1000, 'notes': 'the salt pan'},
        ] + [dict({'at': [x, 41], 'h': 3264}, **({'notes': "the hillside over DD-24's doors"} if x == 86 else {}))
             for x in range(83, 91)] + [{'at': [x, 40], 'h': 3392} for x in range(83, 91)],
        'terraces': [{'polygon': [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]], 'height': h,
                      'slope': s, 'notes': n} for b, h, s, n in TERRACES],
        'cliffs': copy.deepcopy(L1S['heights']['cliffs']) + [
            {'line': [[83, 42], [90, 42]], 'drop': 560, 'down': 'right',
             'notes': "The hillside behind the hold: DD-24's great doors in its foot."},
            {'line': [[59, 44], [59, 48]], 'drop': 400, 'down': 'right',
             'notes': "Bosco's crag over his terrace (drawn north to south, the low side east)."},
        ],
        'ridges': copy.deepcopy(L1S['heights']['ridges']),
    }
    heights['cliffs'] = [c for c in heights['cliffs'] if 'shrine mesa' not in c.get('notes', '')]
    heights['cliffs'].append({'line': [[29, 86], [34, 86], [34, 90], [29, 90], [29, 86]], 'drop': 380, 'down': 'right',
                              'notes': "The shrine mesa's sides (its ramp on the north side)."})
    water = {'bodies': [
        {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': [[0, 0], [128, 0], [128, RIM_N], [0, RIM_N]],
         'notes': 'Below the rim: stands for the stars.'},
        {'id': 'water:last_water', 'kind': 'pond', 'level': POND_H, 'polygon': [[42, 77], [45, 77], [46, 78],
                                                                                 [45, 80], [43, 80]],
         'notes': "The Last Water's spring pool (D-23: no river)."}]}
    roads = copy.deepcopy(L1S['roads'])
    for r in roads:
        # the classic tiles: the two roads on the road tile (the world's terrain material draws it as a stony earth
        # track, soil_stony: D-49 (7)), the lanes dirt paths
        r['surface'] = 'road_pebbles' if r['width'] == 'road' else 'dirt'
    for r in roads:
        if r['link'] == 'link:desert_road':
            r['line'] = DESERT_ROAD if D4_LIVE else DESERT_ROAD[1:]
        if r['link'] == 'link:west_road':
            r['line'] = WEST_ROAD if D6_LIVE else WEST_ROAD[:-1]
        if r['link'] == 'link:hold_lane':
            r['line'] = [[76, 53], [79, 51], [82, 49.5], [84.5, 48.8]]
        if r['link'] == 'link:tower_lane':
            r['line'] = [[76, 53], [74.5, 49], [72, 45], [70.5, 42], [69.5, 41]]
        if r['link'] == 'link:bosco_lane':
            r['line'] = [[76, 53], [72, 52], [68, 50.5], [65, 48], [63.2, 46.5]]
        if r['link'] == 'link:pyramid_track':
            r['line'] = [[80, 77], [77, 78], [72, 78.3], [68, 78.3], [65, 78.6]]
        if r['link'] == 'link:broken_lane':
            r['line'] = [[96, 79], [95.8, 77], [95.5, 75]]
        if r['link'] == 'link:might_path':
            r['line'] = [[88.5, 47.5], [91, 45], [95, 39], [99, 35], [101, 32.6]]
        if r['link'] == 'link:barrier_path':
            r['line'] = [[35, 41.5], [38, 36], [42, 33], [45, 31], [46.5, 30.2]]
        if r['link'] == 'link:forest_track':
            r['line'] = [[30, 65.5], [31, 61], [33, 57], [34.5, 53], [35, 48], [34.8, 43]]
        if r['link'] == 'link:grate_track':
            r['line'] = [[100, 79], [100.5, 84], [100, 90], [100.5, 96], [101, 100.6]]
        if r['link'] == 'link:oasis_track':
            r['line'] = [[40, 68], [41.5, 72], [44, 75], [46.5, 76.5]]
        if r['link'] == 'link:shrine_path':
            r['line'] = [[47, 80], [45.5, 81.5], [40.5, 82.5], [37, 84], [33.5, 85.3], [32, 86.4]]
    districts = copy.deepcopy(L1S['districts'])
    points = [
        {'id': 'entrance:d4_road', 'at': list(EAST_START), 'facing': 'w'},
        {'id': 'entrance:d6_pass', 'at': list(WEST_START), 'facing': 'e'},
        {'id': 'entrance:dd15_door', 'at': [PYR_DOOR[0], PYR_DOOR[1] - 1.0], 'facing': 'n'},
        {'id': 'entrance:dd08_door', 'at': [TOWER[0], TOWER[1] + 2.0], 'facing': 's'},
        {'id': 'entrance:dd24_hold', 'at': list(DD24_ARRIVAL), 'facing': 's'},
        {'id': 'entrance:dd25_door', 'at': [BOSCO[0] + 1.6, BOSCO[1]], 'facing': 'e'},
        {'id': 'entrance:dd18_grate', 'at': [GRATE[0], GRATE[1] - 1.2], 'facing': 'n'},
    ]
    points.append({'id': 'entrance:d7_fall', 'at': [66, 73], 'facing': 's'})   # D-58 Q10 (A6 s16)
    for q in L1S['points']:
        if q['id'].startswith(('junction:', 'landmark:')):
            points.append(dict(q))
    POI_AT = {'poi:obelisk': OBELISK, 'poi:shrine_great_power': SHRINE, 'poi:last_water': LAST_WATER,
              'poi:fountain_energy': FOUNTAIN_ENERGY, 'poi:fountain_might': FOUNTAIN_MIGHT, 'poi:capstone': CAPSTONE,
              'poi:lamp_doom': LAMP_HILLS, 'poi:lamp_sands': LAMP_DUNE, 'poi:boulder_sign': EAST_RING[0],
              'poi:giants_lair': LAIR, 'poi:lair_hoard': (LAIR[0] + 0.6, LAIR[1] - 0.6), 'poi:eyrie_nest': EYRIE,
              'poi:caravan_wreck': (95.0, 91.0), 'poi:prospector': (28.0, 77.0), 'poi:dwarf_camp': (102.0, 50.0),
              'poi:robbers_camp': (72.0, 93.2), 'poi:gurodel': HOLD_FIRE}
    for k, at in POI_AT.items():
        points.append({'id': k, 'at': [round(at[0], 2), round(at[1], 2)]})
    for i, at in enumerate(EAST_RING[1:]):
        points.append({'id': 'poi:boulders', 'index': i + 1, 'at': [round(at[0], 2), round(at[1], 2)]})
    for i, at in enumerate(WEST_RING):
        points.append({'id': 'poi:boulders_west', 'index': i + 1, 'at': [round(at[0], 2), round(at[1], 2)]})
    for i, at in enumerate([(38, 95), (70, 99)]):
        points.append({'id': 'poi:munchies', 'index': i + 1, 'at': list(at)})
    for i, at in enumerate([(81.0, 76.0), (77.0, 52.0), (41.0, 67.0)]):
        points.append({'id': 'poi:signposts', 'index': i + 1, 'at': list(at)})
    # ---------------------------------------------------------------- encounter areas (L1's 47 markers) and clear zones
    areas = copy.deepcopy(L1S['areas'])
    for a in areas:
        if a['id'].startswith('pop:'):
            a['kind'] = 'encounter'
    # E5 by hand (the first fight from D6 inside 6,000; clear of the west boulders, the oasis and the mesa)
    areas = [a for a in areas if a['id'] != 'pop:doom_birds']
    for k, (cx, cy) in enumerate(DOOM_BIRDS):
        areas.append({'id': 'pop:doom_birds', 'index': k + 1, 'kind': 'encounter', 'count': 1, 'slot': 2,
                      'circle': {'at': [cx, cy], 'r': 1}})
    # F10 (s32): the north-east corner was the Xeen world's largest empty stretch (1,276 tiles, 20,123 deep): three of
    # the doom birds (slot 2 as the cliffs') fly over the highland in front of the Barrier's middle and the corner east of the Barrier's end instead (the strip behind the
    # Barrier is not walkable land: tools/xeen/empty_zones.yml, D-49) (kill XP unchanged)
    for a in areas:
        if a['id'] == 'pop:cliff_birds':
            a['index'] = 1
    for k, (cx, cy) in enumerate([(102, 28), (104, 40), (77, 37)]):
        areas.append({'id': 'pop:cliff_birds', 'index': k + 2, 'kind': 'encounter', 'count': 1, 'slot': 2,
                      'circle': {'at': [cx, cy], 'r': 1}})
    views = copy.deepcopy(L1S['views'])
    structures = []
    S = structures.append
    # ---------------------------------------------------------------- the Great Pyramid (DD-15)
    x0, y0, x1, y1 = PYR
    side = int((x1 - x0) * 512)                  # 6,144 at the foot
    band = 256                                   # the foot course (egybiga as the porch; no frieze: D-49 allows one, none)
    pitch = round(math.degrees(math.atan2(3600 - band, side / 2)), 1)
    cap = 704                                    # the gilded capstone's foot, proud of the faces
    cap_bottom = band + round((side / 2 - cap / 2) * math.tan(math.radians(pitch))) - 24
    porch_d = 768
    # the faces: six stacked battered courses (each 600 high drawing in 459 a side: the slope about 52.6 degrees, no
    # steps), each bay one egybigb picture stretched over it (fit): large blocks, a few dozen courses up the whole height
    STEPS, RISE, DRAW = 6, 600, 459
    big = {'texture': 'egybigb', 'fit': True, 'size': [256, 256]}
    pyr_parts = []
    for k in range(STEPS):
        L = side - 2 * DRAW * k
        n = max(2, math.ceil(L / 512))
        bays = [['wall', L / n] for _ in range(n)]
        p = {'id': 'course_%d' % (k + 1), 'at': [DRAW * k, porch_d - 128 + DRAW * k], 'size': [L, L],
             'wall_height': RISE, 'batter': DRAW, 'roof': 'flat' if k < STEPS - 1 else 'hip', 'windows': 'none',
             'walls': {w_: list(bays) for w_ in 'nesw'}, 'textures': {'wall': big, 'roof': 'egybigb'}}
        if k:
            p['bottom'] = RISE * k
        else:
            p.pop('bottom', None)
        pyr_parts.append(p)
    top = side - 2 * DRAW * STEPS          # the cap's foot (about 636), gilded, on the last course's flat top
    pyr_parts[-1]['roof'] = 'flat'
    pyr_parts.append({'id': 'cap', 'at': [DRAW * STEPS, porch_d - 128 + DRAW * STEPS], 'size': [top, top],
                      'bottom': RISE * STEPS, 'wall_height': 16, 'roof': 'hip', 'roof_pitch': 53, 'windows': 'none',
                      'textures': {'wall': 'xngold6', 'roof': 'xngold6'}})
    pyr_parts.append({'id': 'porch', 'at': [side // 2 - 448, 0], 'size': [896, porch_d + 256], 'wall_height': 512,
                      'roof': 'flat', 'windows': 'none', 'door_height': 384,
                      'walls': {'n': [['wall', 224], ['door', 448], ['wall', 224]],
                                'e': [['wall', 512], ['wall', 512]], 'w': [['wall', 512], ['wall', 512]]},
                      'textures': {'wall': {'texture': 'egybiga', 'fit': True, 'size': [256, 256]},
                                   'roof': 'egybiga'}})
    pyr = {'id': 'thing:great_pyramid', 'kind': 'building', 'at': [x0, y0 - porch_d / 512.0 + 0.25],
           'size': [x1 - x0, y1 - y0 + porch_d / 512.0 - 0.25], 'kit': 'grey', 'facing': 'n', 'floor': PYR_H,
           'title': 'The Great Pyramid',
           'textures': {'wall': 'egybiga', 'roof': 'egybigb', 'trim': 'egybiga', 'door': 'xdpyrdor',
                        'post_left': 'egybiga', 'post_right': 'egybiga', 'window': 'egybiga'},
           'parts': pyr_parts,
           'door': {'part': 'porch', 'wall': 'n', 'leaves': 2},
           'condition': {'lua': hcall('m28.door')},
           'notes': ("DD-15 (A8): m28.door with the Key to the Ancient Pyramid (12348); two leaves of A6's xdpyrdor "
                     "(the wing, mirrored on the pair). 12 x 12 cells, about 3,600 high, smooth-faced courses of MM6's "
                     "egybigb under a gilded cap (xngold5), one egytrma band round the foot (D-49 Q6, change 7).")}
    if DUNGEON['dd15']:
        pyr['into'] = {'map': 'xeen_dd15.blv', 'arrival': ENTRANCE['dd15']}
    else:
        pyr['effects'] = [msg('The green doors do not move. ' + SEALED)]
    S(pyr)
    # the tomb robbers' camp at the south-east corner: a torn tent, a dead robber's loot box
    S({'id': 'thing:robbers_tent', 'kind': 'tent', 'at': [71.6, 94.2], 'height': 288, 'size': [512, 640],
       'turn': 20, 'title': "A tomb robber's tent"})
    S({'id': 'thing:robbers_chest', 'kind': 'chest', 'at': [72.0, 93.2], 'title': "A tomb robber's loot box",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:robbers_bones', 'dec05', (72.7, 93.0)))
    # ---------------------------------------------------------------- the broken travel pyramid and its capstone
    bx, by = BROKEN
    S({'id': 'thing:broken_pyramid', 'kind': 'building', 'at': [bx - 1.0, by - 1.0], 'size': [2.0, 2.0],
       'kit': 'grey', 'door': 'none', 'floor': 1600, 'title': 'A broken pyramid',
       'textures': {'wall': 'xahull', 'trim': 'gn_mtl01', 'window': 'xahull', 'roof': 'gn_mtl01'},
       'parts': [{'id': 'body', 'at': [64, 64], 'size': [896, 896], 'wall_height': 576, 'batter': 352,
                  'roof': 'flat', 'windows': 'none', 'title': 'A broken pyramid',
                  'effects': hook('obelisks.dark_hoard')},
                 {'id': 'apex', 'at': [352, 352], 'size': [320, 320], 'bottom': 576, 'wall_height': 288,
                  'roof': 'none', 'windows': 'none', 'ruin': {'height': [48, 288], 'gaps': 0.45, 'thickness': 48,
                                                              'seed': 11}}],
       'notes': "The broken travel pyramid (aaze0013:12): its click is obelisks.dark_hoard, as the capstone's."})
    S({'id': 'thing:capstone', 'kind': 'building', 'at': [CAPSTONE[0] - 0.4, CAPSTONE[1] - 0.4], 'size': [0.8, 0.8],
       'kit': 'grey', 'door': 'none', 'floor': 1600, 'title': 'A fallen capstone',
       'parts': [{'id': 'cap', 'at': [32, 32], 'size': [344, 344], 'wall_height': 24, 'roof': 'hip',
                  'roof_pitch': 50, 'windows': 'none', 'textures': {'wall': 'gn_mtl01', 'roof': 'xahull'},
                  'title': 'A fallen capstone', 'effects': hook('obelisks.dark_hoard')}],
       'notes': "D-49 change 2: the capstone at the pyramid's foot, within 400 of its click: one spot."})
    # ---------------------------------------------------------------- the Parabolic Barrier (no event, not a POI)
    pylons = []
    for a, b in zip(BARRIER, BARRIER[1:]):
        pylons.append(a)
        pylons.append([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2])
    pylons.append(BARRIER[-1])
    for i, (u, v) in enumerate(pylons):
        S({'id': 'thing:barrier_frame_%d' % (i + 1), 'kind': 'building', 'at': [u - 0.3, v - 0.3],
           'size': [0.6, 0.6], 'kit': 'grey', 'door': 'none',
           'parts': [{'id': 'foot', 'at': [64, 64], 'size': [180, 180], 'wall_height': 256, 'roof': 'flat',
                      'windows': 'none', 'textures': {'wall': 'gn_mtl01', 'roof': 'gn_mtl01'}},
                     {'id': 'pylon', 'at': [90, 90], 'size': [128, 128], 'bottom': 256, 'wall_height': 1280,
                      'roof': 'hip', 'roof_pitch': 70, 'windows': 'none',
                      'textures': {'wall': 'xaenergy', 'roof': 'gn_mtl01'}}]})
    S({'id': 'thing:barrier_curtain', 'kind': 'wall', 'line': pylons, 'height': 1280, 'thickness': 32,
       'textures': {'wall': 'xafield', 'top': 'xafield'}, 'translucent': True,
       'notes': "The shimmering curtain between the frames (D-49 Q4): a landmark, no event; see-through by "
                "xafield's graded alpha (merge point 23)."})
    S({'id': 'thing:barrier_block', 'kind': 'barrier', 'line': pylons, 'height': 6000,
       'notes': "The Barrier blocks walking and flying up to the fly ceiling (D-49 change 4); past its ends the rim rule."})
    # ---------------------------------------------------------------- Gurodel's hold and DD-24's great doors
    hx, hy = HOLD_FIRE
    S({'id': 'thing:hold_ring', 'kind': 'stone_ring', 'at': [hx, hy], 'radius': 1000, 'count': 9, 'lintel': False,
       'title': "Gurodel's hold"})
    S(deco('thing:hold_fire', 'dec24', (hx, hy), title="The giants' fire"))
    S(deco('thing:hold_boulders_1', 'rock16', (hx + 2.4, hy + 1.2)))
    S(deco('thing:hold_boulders_2', 'rock16', (hx + 2.8, hy + 0.6)))
    gx, gy = GIANTS_DOORS
    hall = {'id': 'thing:giants_hall_doors', 'kind': 'doorway', 'at': [gx, gy], 'width': 768, 'height': 512,
            'depth': 256, 'hood': 128, 'leaves': 2, 'title': "The Giants' Hall",
            'textures': {'door': 'xdgiantd', 'wall': 'hkm2bs'},
            'notes': "DD-24 Giants' Hall (A7): two leaves 384 x 512 of A7's xdgiantd, mirrored (D-47), in the hillside."}
    if DUNGEON['dd24']:
        hall['into'] = {'map': 'xeen_dd24.blv', 'arrival': ENTRANCE['dd24']}
    else:
        hall['effects'] = [msg('The great doors are barred. ' + SEALED)]
    S(hall)
    # ---------------------------------------------------------------- Bosco's Hall (DD-25) in its crag
    bx_, by_ = BOSCO
    bosco = {'id': 'thing:bosco_door', 'kind': 'doorway', 'at': [bx_ - 0.3, by_], 'turn': -90, 'width': 384,
             'height': 320, 'depth': 256, 'hood': 96, 'leaves': 2, 'title': "Bosco's Hall",
             'textures': {'door': 't09a03a', 'wall': 'cswl128'},
             'notes': "DD-25 Bosco's Hall (A8): a carved stone double door (shipped t09a03a, mirrored) in the crag."}
    if DUNGEON['dd25']:
        bosco['into'] = {'map': 'xeen_dd25.blv', 'arrival': ENTRANCE['dd25']}
    else:
        bosco['effects'] = [msg("Dwarf-carved doors, shut from inside. Somebody is hammering. " + SEALED)]
    S(bosco)
    for i, at in enumerate(((bx_ + 0.15, by_ - 0.95), (bx_ + 0.15, by_ + 0.95))):
        S(deco('thing:bosco_lantern_%d' % (i + 1), 'dec60', at))
    # ---------------------------------------------------------------- the Northern Tower (DD-08)
    tx, ty = TOWER
    storey = 320
    tower_parts = []
    for k in range(5):
        off = (0, 2, -2, 2, -2)[k]
        walls = {w_: ['wall'] * 8 for w_ in 'nsew'}
        for w_ in 'new':
            walls[w_][3 + off // 2] = 'window'
        if k == 0:
            walls = {w_: ['wall'] * 8 for w_ in 'new'}
            walls['s'] = ['wall', 'wall', 'wall', ['door', 256], 'wall', 'wall', 'wall']
        else:
            walls['s'][3 + off // 2] = 'window'
        part = {'id': 'storey_%d' % (k + 1), 'at': [128, 128], 'size': [1024, 1024], 'wall_height': storey,
                'roof': 'flat', 'walls': walls}
        if k:
            part['bottom'] = storey * k
        if k == 4:
            part['battlements'] = True
        if k == 0:
            part['door_height'] = 240
            part['textures'] = {'window': 'hkm1b1'}      # the strip over the door: the wall's stone
            part['signs'] = [{'wall': 's', 'bay': 3, 'texture': 'xdvowel', 'size': [256, 64], 'bottom': 252,
                              'out': 8}]
        tower_parts.append(part)
    tw = {'id': 'thing:northern_tower', 'kind': 'building', 'at': [tx - 1.25, ty - 1.25], 'size': [2.5, 2.5],
          'kit': 'grey', 'facing': 's', 'floor': 3008, 'title': 'The Northern Tower',
          'textures': {'wall': 'hkm1b1', 'door': 'hkm1dl', 'trim': 'hkm1b1', 'roof': 'hkm1b1', 'window': 'hkm1elw',
                       'post_left': 'hkm1b1', 'post_right': 'hkm1b1'},
          'parts': tower_parts,
          'door': {'part': 'storey_1', 'wall': 's', 'leaves': 2},
          'condition': {'lua': hcall('q-d17.tower_door')},
          'notes': ("DD-08 (A8): q-d17.tower_door with Bosco's key; two iron-bound leaves (hkm1dl, mirrored); A6's "
                    "xdvowel lintel once over the door (D-49 change 8).")}
    if DUNGEON['dd08']:
        tw['into'] = {'map': 'xeen_dd08.blv', 'arrival': ENTRANCE['dd08']}
    else:
        tw['effects'] = [msg('Behind the leaves the stair is dark and cold. ' + SEALED)]
    S(tw)
    # ---------------------------------------------------------------- DD-18's grate (one leaf, not a double door)
    gx2, gy2 = GRATE
    grate = {'id': 'thing:dd18_grate', 'kind': 'doorway', 'at': [gx2, gy2 - 0.4], 'turn': 180, 'width': 256,
             'height': 288, 'depth': 256, 'title': 'An iron grate',
             'textures': {'door': 'jailc08oq3', 'wall': 'cswl128'},
             'condition': {'qbit': 'd5_tunnel'},
             'else_effects': hook('dd18.d5_grate'),
             'notes': "DD-18 (A8, installed): the bolt drawn by dd18.d5_grate (116121), then the way in both ways."}
    if DUNGEON['dd18']:
        grate['into'] = {'map': 'xeen_dd18.blv', 'arrival': ENTRANCE['dd18']}
    else:
        grate['effects'] = [msg('The tunnel beyond is flooded. ' + SEALED)]
    S(grate)
    # ---------------------------------------------------------------- the Enchanted Boulders (two chained rings)
    bdeco = BOULDER_MODEL or BOULDER_STANDIN
    S(deco('thing:boulder_sign', 'dec29' if False else 'searka01', EAST_RING[0], title='A weathered sign',
           effects=hook('q-d24.sign')))
    order = [(3, EAST_RING[1]), (4, EAST_RING[2]), (5, EAST_RING[3]), (6, EAST_RING[4]), (1, WEST_RING[0]),
             (2, WEST_RING[1])]
    def bturn(n, at):
        if not BOULDER_LIVE:
            return {}
        return {'turn': outward_turn(at, EAST_RING_C if n in (3, 4, 5, 6) else WEST_RING_C)}
    for n, at in order:
        S(deco('thing:boulder_%d' % n, bdeco, at, title='An Enchanted Boulder', **bturn(n, at),
               effects=[{'lua': '%s if IsQBitSet(QBit(%d)) then HideThing("thing:boulder_%d") end'
                         % (hcall('q-d24.boulder_%d' % n), 113480 + n, n)}]))
    S(deco('thing:boulder_7', bdeco, WEST_RING[2], title='An Enchanted Boulder', **bturn(7, WEST_RING[2]),
           effects=[{'lua': (
        'if continueStep == 2 then %s HideThing("thing:boulder_7") return end '
        'if continueStep == 1 then %s return end '
        'if continueStep ~= nil then return end '
        'if IsQBitSet(QBit(113480)) then %s return end '
        '%s evt.AskQuestion(eventId, 1, 0, 2, "What am I?", {"paladin", "a paladin", "the paladin"})'
        % (hcall('q-d24.answer'), hcall('q-d24.answer_wrong'), hcall('q-d24.answer'), hcall('q-d24.boulder_7')))}]))
    for i, at in enumerate(((84.2, 83.2), (87.3, 79.6), (36.0, 71.6))):
        S(deco('thing:boulder_rock_%d' % (i + 1), 'rock14', at))
    # ---------------------------------------------------------------- devices and fountains
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': list(OBELISK), 'height': 768, 'title': 'Obelisk',
       'textures': {'wall': 'cswl128'}, 'effects': hook('obelisks.d5')})
    S({'id': 'thing:last_water', 'kind': 'fountain', 'at': list(LAST_WATER), 'title': 'The Last Water',
       'tiers': [[64, 24]], 'textures': {'wall': 'egybiga'}, 'effects': hook('d5.last_water')})
    S({'id': 'thing:fountain_energy', 'kind': 'fountain', 'at': list(FOUNTAIN_ENERGY),
       'title': 'Fountain of Energy Resistance', 'tiers': [[64, 24]], 'textures': {'wall': 'gn_mtl01'},
       'effects': hook('d5.fountain_energy')})
    S({'id': 'thing:fountain_might', 'kind': 'fountain', 'at': list(FOUNTAIN_MIGHT), 'title': 'Fountain of Might',
       'tiers': [[64, 24]], 'textures': {'wall': 'hkm2bs'}, 'effects': hook('d5.fountain_might')})
    sx, sy = SHRINE
    S({'id': 'thing:shrine_ring', 'kind': 'stone_ring', 'at': [sx, sy], 'radius': 600, 'count': 8, 'lintel': False,
       'title': 'The Shrine of Great Power'})
    S({'id': 'thing:shrine_altar', 'kind': 'platform', 'at': [sx, sy], 'size': [256, 192], 'height': 96,
       'textures': {'top': 'egybiga', 'wall': 'egybiga'}, 'title': 'The Shrine of Great Power',
       'question': {'ask': 'Shrine of Great Power. Will the party pray? (Yes/No)', 'answers': ['Yes', 'Y']},
       'effects': hook('d5.shrine')})
    S(deco('thing:lamp_hills', 'xeen_genielamp', LAMP_HILLS, title="A genie's lamp",
           effects=[{'lua': 'Xeen.genieLamp("d5_hills", eventId, continueStep)'}]))
    S(deco('thing:lamp_dune', 'xeen_genielamp', LAMP_DUNE, title="A genie's lamp",
           effects=[{'lua': 'Xeen.genieLamp("d5_dune", eventId, continueStep)'}]))
    for k in ('q-d27.d5_hills', 'q-d27.d5_dune', 'q-d27.wish_experience', 'q-d27.wish_gold', 'q-d27.wish_gems'):
        use(k)                       # called by Xeen.genieLamp (A3)
    S({'id': 'thing:hill_shrine', 'kind': 'building', 'at': [LAMP_HILLS[0] - 1.0, LAMP_HILLS[1] - 1.0],
       'size': [2.0, 2.0], 'kit': 'grey', 'door': 'none', 'title': 'A ruined hill shrine',
       'ruin': {'height': [96, 448], 'gaps': 0.4, 'thickness': 64, 'seed': 7},
       'textures': {'wall': 'egybiga', 'trim': 'egybiga', 'window': 'egybiga'},
       'parts': [{'id': 'body', 'at': [128, 128], 'size': [768, 768], 'wall_height': 448, 'roof': 'none',
                  'windows': 'none'}]})
    # the cyclopes' lair: a lean-to of whole trunks, a bone heap; "Destroy?" and the hoard
    lx, ly = LAIR
    S({'id': 'thing:lair_leanto', 'kind': 'building', 'at': [lx - 0.9, ly - 0.7], 'size': [1.8, 1.4], 'kit': 'poor',
       'door': 'none', 'title': "A Giant's lair",
       'parts': [{'id': 'leanto', 'at': [64, 64], 'size': [790, 590], 'wall_height': 320, 'posts': 48,
                  'roof': 'lean_to', 'windows': 'none',
                  'textures': {'roof': 'hhp2rf', 'post': 't06a10', 'trim': 't06a10'}, 'title': "A Giant's lair",
                  'effects': [{'lua': ('if continueStep == 2 then %s return end if continueStep ~= nil then return '
                                       'end evt.AskQuestion(eventId, 1, 0, 2, "You have found a Giant\'s lair. '
                                       'Destroy? (Yes/No)", {"yes", "y"})' % hcall('d5.lair'))}]}]})
    S({'id': 'thing:lair_hoard', 'kind': 'chest', 'at': [lx + 0.6, ly - 0.6], 'title': "The cyclopes' hoard",
       'chest': {'level': 5, 'random_items': 3}})
    S(deco('thing:lair_bones', '7dec18', (lx - 1.4, ly + 1.0)))
    # the other chests (6 in all: a reason each)
    S({'id': 'thing:eyrie_nest', 'kind': 'chest', 'at': list(EYRIE), 'title': "A griffin-hunter's satchel",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:eyrie_bones', '7dec18', (EYRIE[0] + 0.7, EYRIE[1] + 0.3)))
    S({'id': 'thing:caravan_wreck', 'kind': 'chest', 'at': [95.0, 91.0], 'title': "A caravan's strongbox",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:caravan_ribs', 'dec24x', (94.2, 91.4)))
    S({'id': 'thing:prospector', 'kind': 'chest', 'at': [28.0, 77.0], 'title': "A dead prospector's pack",
       'chest': {'level': 4, 'random_items': 2}})
    S(deco('thing:prospector_bones', 'dec05', (28.5, 77.3)))
    S({'id': 'thing:dwarf_camp', 'kind': 'chest', 'at': [102.0, 50.0], 'title': "The dwarves' strongbox",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:dwarf_fire', 'dec24x', (101.2, 49.6), title='A cold fire'))
    S({'id': 'thing:dwarf_tent', 'kind': 'tent', 'at': [102.6, 51.2], 'height': 256, 'size': [448, 576],
       'turn': 90, 'title': "An abandoned dwarves' tent"})
    # the munchies (hazards, not POIs): A3's hook on a step, an unseen plate
    for i, at in enumerate([(38, 95), (70, 99)]):
        S({'id': 'thing:munchies_%d' % (i + 1), 'kind': 'platform', 'at': list(at), 'size': [384, 384],
           'height': 0, 'invisible': True, 'trigger': 'step', 'effects': hook('d5.munchies')})
    # signposts at the three forks
    for sid, at, arms in (
            ('sign_pyramid_fork', (81.0, 76.0), [('The forest road', 'e'), ('The Great Pyramid', 's'),
                                                 ('The Forbidden Zone', 'w'), ('The highlands', 'n')]),
            ('sign_highland_fork', (77.0, 52.0), [("Gurodel's hold", 'e'), ('The Northern Tower', 'n'),
                                                  ("Bosco's Hall", 'w'), ('The desert', 's')]),
            ('sign_doom_fork', (41.0, 67.0), [('The pyramid', 'e'), ('The Forbidden Zone', 'w'),
                                              ('The Last Water', 's')])):
        S({'id': 'thing:%s' % sid, 'kind': 'sign', 'at': list(at), 'height': 256,
           'arms': [{'title': t, 'toward': d} for t, d in arms]})
    # event-less landmarks: a cairn at the cliff road's foot, boundary stones on the Gemstone spurs (seen places)
    S(deco('thing:scarp_cairn', 'searka01', (74.6, 72.2), title="A cairn at the cliff road's foot"))
    S({'id': 'thing:spur_stone_w', 'kind': 'obelisk', 'at': [36.0, 104.6], 'height': 512, 'title': 'A boundary stone',
       'textures': {'wall': 'cswl128'}})
    S({'id': 'thing:spur_stone_e', 'kind': 'obelisk', 'at': [88.5, 104.0], 'height': 512, 'title': 'A boundary stone',
       'textures': {'wall': 'cswl128'}})
    if not D6_LIVE:
        S(sign('thing:west_road_end', (20.6, 63.0), 'Sign',
               'The pass west into the Forbidden Zone is closed by a rockfall. Turn back.'))
    # ---------------------------------------------------------------- actors (the People first: indices 0-5)
    actors = []

    def place(row, at, count, spread, group, **kw):
        a = {'monster': str(row), 'at': [round(at[0], 2), round(at[1], 2)], 'count': count, 'spread': spread,
             'group': group}
        a.update(kw)
        actors.append(a)
    place(11083, (84.4, 47.2), 3, 1.2, 3, hostile=False)
    place(11084, (88.6, 47.0), 2, 0.8, 3, hostile=False)
    place(11085, (88.8, 45.2), 1, 0, 3, hostile=False)
    actors.append({'monster': '11085', 'npc': 5452, 'at': [HOLD_FIRE[0], HOLD_FIRE[1] + 0.9], 'spread': 0,
                   'group': 2, 'hostile': False})
    place(11562, EYRIE, 3, 1, 1, hostile=True)
    # ---------------------------------------------------------------- events
    people = range(0, 6)
    crumble = ' '.join('if IsQBitSet(QBit(%d)) then HideThing("thing:boulder_%d") end' % (113480 + n, n)
                       for n in range(1, 7))
    events = [
        {'id': 'evt:sky', 'trigger': 'load', 'effects': [{'lua': 'Xeen.applyDarksideSky()'}],
         'notes': "Darkside's sky by the sun's stage (A3's helper)."},
        {'id': 'evt:boulders_gone', 'trigger': 'load',
         'lua': crumble + ' if IsQBitSet(QBit(113480)) then HideThing("thing:boulder_7") end',
         'notes': "q-d24: the crumbled boulders and the answered seventh are gone (A3's crumbled_1-6, solved)."},
        {'id': 'evt:hold_struck', 'trigger': 'timer', 'every': 1,
         'condition': {'not': {'any': [{'qbit': 'giants_war'}, {'qbit': 'hall_attacked'},
                                       {'qbit': 'sardaj_hostile'}, {'qbit': 'sardaj_camp_burned'}]}},
         'lua': ('local struck = false for i = %d, %d do if evt.IsMapActorHostile(i) and not evt.IsMapActorDead(i) '
                 'then struck = true end end if struck then %s end'
                 % (people[0], people[-1], hcall('q-d16.hold_attacked'))),
         'notes': ("D-47 Q22 / D-49 Q1: a People giant struck at peace (the first six actors) calls "
                   "q-d16.hold_attacked once; A2's relations then turn the People on both maps.")},
    ]
    # ---------------------------------------------------------------- scatter and ground
    scatter = []

    def sc(sid, deco_, count, poly, clusters=None, steep=None):
        e = {'id': sid, 'decoration': deco_, 'count': count, 'polygon': poly}
        if clusters:
            e['clusters'] = clusters
        if steep:
            e['steep'] = True
        scatter.append(e)

    def stand(sid, poly, kinds_, per_100, spacing, close=0.1, close_spacing=1.0):
        n = int(round(per_100 * K.poly_area(poly) / 100.0))
        e = {'id': sid, 'count': n, 'polygon': poly, 'spacing': spacing, 'close_share': close,
             'close_spacing': close_spacing, 'spacing_group': 'trees', 'kinds': dict(kinds_)}
        scatter.append(e)
    FOREST = [[19.5, 24.8], [45, 24.8], [50, 30], [53, 40], [54, 47], [50, 50.5], [40, 52.5], [28, 55.5],
              [19.5, 56.5]]
    stand('scatter:aspens', FOREST, {'tree62c': 3, 'tree63b': 2, 'tree28': 1}, 22.0, 1.1, close=0.2,
          close_spacing=0.8)
    sc('scatter:forest_undergrowth', 'plant50', 50, FOREST, clusters=16)
    sc('scatter:forest_rocks', 'rock10', 20, FOREST, clusters=8)
    HIGH = [[50, 30], [100, 24.8], [108.5, 25], [108.5, 57], [92, 56.5], [80, 55.5], [66, 53.5], [60, 49.5],
            [55, 46.5], [53, 40]]
    sc('scatter:highland_rocks', 'rock24', 40, HIGH, clusters=14, steep=True)
    sc('scatter:highland_rocks', 'rock16', 40, HIGH, clusters=12)
    sc('scatter:highland_weeds', 'snoweed1', 90, HIGH, clusters=40)
    stand('scatter:highland_firs', HIGH, {'snotre01': 2, 'tree30': 1}, 0.8, 3.0)
    SCARP = [[19.5, 57], [28, 56], [40, 53], [50, 51], [56, 48], [62, 51.5], [70, 54.5], [80, 56], [92, 57],
             [100, 58], [100, 62], [86, 62], [72, 60.5], [56, 59.5], [42, 60], [32, 61], [19.5, 60]]
    sc('scatter:cliff_rocks', '6rock07', 70, SCARP, clusters=30, steep=True)
    sc('scatter:cliff_scrub', 'plant53', 40, SCARP, clusters=20)
    DOOM = [[19.5, 68.5], [34, 68.5], [32, 61], [42, 60.5], [55.5, 60], [55.5, 72], [51.5, 78], [53.5, 96],
            [51.5, 100.5], [19.5, 100.5]]
    sc('scatter:doom_rocks', 'rock28', 50, DOOM, clusters=16)
    sc('scatter:doom_rocks', 'rock30', 30, DOOM, clusters=10, steep=True)
    sc('scatter:doom_scrub', 'plant53', 90, DOOM, clusters=40)
    sc('scatter:doom_scrub', 'plant49', 60, DOOM, clusters=30)
    sc('scatter:sands_scrub', 'plant51', 110, SANDS, clusters=55)
    sc('scatter:sands_rocks', 'rock27', 40, SANDS, clusters=24)
    OAS = [[40.5, 75.5], [48, 75.5], [48, 81.5], [40.5, 81.5]]
    stand('scatter:palms', OAS, {'tree02': 2, 'tree03': 1}, 12.0, 1.4)
    VALLEY = [[100.5, 62.5], [108.5, 62.5], [108.5, 76.5], [101, 76.5]]
    stand('scatter:last_firs', VALLEY, {'tree60a': 2, 'tree62a': 2}, 5.0, 1.6)
    VALLEY_S = [[101, 83.5], [108.5, 83.5], [108.5, 98], [102, 98]]
    stand('scatter:last_firs_s', VALLEY_S, {'tree60a': 1, 'tree62a': 1}, 2.5, 2.0)
    HILLS = [[19.5, 101], [102, 101], [108.5, 101], [108.5, 108.5], [19.5, 108.5]]
    sc('scatter:hill_rocks', 'rock24', 30, HILLS, clusters=10, steep=True)
    sc('scatter:hill_scrub', 'plant49', 60, HILLS, clusters=30)
    ground = [
        {'material': 'sand', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'The Perishing Sands and the dunes (sand_ripples in the terrain materials).'},
        {'material': 'dirt', 'polygon': [[0, 57], [34, 57], [42, 60], [56, 59], [56, 72], [52, 78], [54, 96],
                                          [52, 101], [128, 101], [128, 128], [0, 128]],
         'notes': 'The Desert of Doom and the southern hills: cracked stony ground.'},
        {'material': 'dirt', 'polygon': [[0, 0], [128, 0], [128, 62], [100, 62], [86, 62], [72, 60.5], [56, 59.5],
                                          [42, 60], [32, 61], [0, 60]],
         'notes': 'The highlands, the forest and the cliffs.'},
        {'material': 'snow', 'polygon': [[52, 24], [104, 24], [104, 33], [90, 33.5], [76, 37], [64, 37], [56, 33]],
         'notes': "Snow on the highlands' crest along the Barrier (above 3,000)."},
        {'material': 'dirt', 'polygon': [[100, 62], [128, 62], [128, 101], [102, 101], [100, 86]],
         'notes': "The forest's end: the valley out of D4."},
        {'material': 'dirt', 'steeper_than': 560, 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'Bare rock on the steep slopes.'},
    ]
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('D5 Desert of Doom, written by output/studio_cal/d5/tools/gen.py. Cells [x, y], x east, y south. '
                  'Heights above the stars below the rim (0): the salt pan 1,000, the sands 1,100-1,700, the Desert '
                  'of Doom 1,300-2,000, the highlands 2,500-3,000, the crest 3,850, the Gemstone spurs to 2,900.'),
        'frame': frame, 'heights': heights, 'water': water, 'roads': roads, 'districts': districts,
        'points': points, 'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground,
        'structures': structures, 'actors': actors, 'events': events,
    }
    if os.path.exists(BEDS):
        sketch['sounds'] = yaml.safe_load(open(BEDS))['sounds']
    atmosphere = {'format': 0, 'sky': 'xeendark1', 'weather': {}, 'view_distance': 1.6,
                  'notes': ("Darkside's sky (continent 7: xeendark1; A3's Lua sets the failing-sun stages); no "
                            "weather. view_distance 1.6: the Great Pyramid reads from both arrivals (about 21,000).")}

    def half(v):
        return round(v * 2) / 2.0
    for r in roads:
        r['line'] = [[half(a), half(b)] for a, b in r['line']]
    for g in ground:
        g['polygon'] = [[round(a), round(b)] for a, b in g['polygon']]
    for a in areas:
        if 'polygon' in a:
            a['polygon'] = [[round(x), round(y)] for x, y in a['polygon']]
    for q in points:
        q['at'] = [round(x) for x in q['at']]
    for t in heights['terraces']:
        t['polygon'] = [[round(a, 1), round(b, 1)] for a, b in t['polygon']]
    missing = sorted(set(HOOKS) - USED)
    if missing:
        raise SystemExit('hooks with map D5 not wired: %s' % missing)

    def dump(folder, name, data):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    import house_doors as HD
    import entrance_screens as ES     # F16/D-90 (s32): each dungeon door's trans.txt row in its entrance window
    for _note in HD.double_doors_sketch(sketch) + HD.bury_mouths_sketch(sketch) + HD.blind_mouths_sketch(sketch):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sketch, 'd5'):
        print('wild:', _note)
    # The classic kits (2026-11-24): Clouds of Xeen's own walls on the map's buildings (classic_kit.yml)
    import classic_kit as CK
    for _note in CK.apply(sketch, 'd5'):
        print(_note)
    print('entrance screens:', ES.apply_sketch(sketch, 'xeen_d5'))
    for lv in ('L4', 'L3'):
        dump(os.path.join(BRIEFS, lv), 'project.yml', project)
        dump(os.path.join(BRIEFS, lv), 'plan.yml', plan)
        dump(os.path.join(BRIEFS, lv), 'sketch.yml', sketch)
        dump(os.path.join(BRIEFS, lv), 'atmosphere.yml', atmosphere)
    p2 = copy.deepcopy(plan)
    p2['level'] = 'L2'
    p2.pop('sketch', None)
    dump(os.path.join(BRIEFS, 'L2'), 'project.yml', project)
    dump(os.path.join(BRIEFS, 'L2'), 'plan.yml', p2)
    print('D4_LIVE', D4_LIVE, 'D6_LIVE', D6_LIVE, 'boulder model', BOULDER_MODEL, 'beds', os.path.exists(BEDS),
          'dungeons live', sorted(k for k, v in DUNGEON.items() if v))


if __name__ == '__main__':
    build()
