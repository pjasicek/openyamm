#!/usr/bin/env python3
"""D6 The Forbidden Zone: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml) and the L2 and L3
briefs beside it (L1 is the approved mock-up with D-49's and D-50's changes, written by
level_generation/xeen_art/phase5/d6_brief.py, and stays as it is).

Castle Alamar on its mesa in a horseshoe moat of lava (Ancient kit: xahull plating, gn_mtl03 trim, xaenergy lit
panels as its windows once per storey face, xafield curtains between the four pylons on the approach ramp), whole
until m33.done and a ruin after it (set:alamar, swapped by a load event); FD-01's stair in the broken gatehouse's floor
(ruin only, sealed); Corak's pod nose-up in the lava lake with its round hatch toward the south-east tongue, the crust
(a pier of cooled rock over the lava) shown on lava_cooled; Sheltem's pod sealed in its crater; Necropolis (A4's
d6.yml) walled with one gate (two leaves outside on d6.necropolis_gate, two inside always open); Ambrose and the
tethered griffin at Griffin Pass until m25.done; the robots placed in groups hidden after m33.done (D-49 change 7);
the D-50 travel pyramid outside the moat; the lava falls over both rims (xeen_lavafall). World: xeen. Hooks: A3's
(data_tables/quest_hooks.yml, `map: D6`). Rows: A2's. The project files are this script's output: edit here and run
../v.sh, never the files.
Coordinates: terrain cells [x, y], x east, y south from the north-west corner; X = (x - 64) * 512, Y = (64 - y) * 512.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import json
import math
import os
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kit as K  # noqa: E402

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/d6'
OUT = os.path.join(BRIEFS, 'L4')
STEM = 'xeen_d6'
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
WORLD = os.path.join(REPO, 'assets_dev/worlds/xeen')
XEEN_SOURCE = os.path.join(WORLD, 'source')
HERE = os.path.dirname(os.path.realpath(__file__))


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
            out[a.get('id') or a.get('name')] = a
    return out


D1_LIVE = live('xeen_d1.odm', 'D6_D1_LIVE')
D5_LIVE = live('xeen_d5.odm', 'D6_D5_LIVE')
# a dungeon door opens when its BLV is installed, A2's map_stats row names it and its studio sidecar lists the
# entrance the door names (D-37: entrance:d6_*); until then the door shows a short sealed line (D4's rule)
ENTRANCE = {'dd16': 'entrance:d6_hatch', 'dd17': 'entrance:d6_gate', 'dd21': 'entrance:d6_stair',
            'dd10c': 'entrance:d6_adit', 'dd22': 'entrance:d6_hatch', 'fd01': 'entrance:d6_stair'}


def dungeon_live(key):
    blv = 'xeen_%s.blv' % key
    env = os.environ.get('D6_%s_LIVE' % key.upper())
    if env is not None:
        return env == '1'
    return (live(blv, '_') and ('\t%s\t' % blv in _STATS) and ENTRANCE[key] in studio_entrances(blv))


DUNGEON = {k: dungeon_live(k) for k in ENTRANCE}
# FD-01 live by name since its install (D-69 change 6, session 23); DD-22 live by name (session 19)
TOWN = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'towns/d6.yml')))
HOUSE = {h['door']: (h['id'], h['name']) for h in TOWN['houses']}
_DECOS = open(os.path.join(WORLD, 'models/decorations.yml')).read()
LAVAFALL_LIVE = 'name: xeen_lavafall' in _DECOS
LAMP = 'xeen_genielamp' if 'name: xeen_genielamp' in _DECOS else '7dec41'

# ---------------------------------------------------------------------------------------------------------------
# A3's hooks with map D6 (the generated table); every one must be used (checked at the end)
HOOKS = {k: v for k, v in (yaml.safe_load(open(os.path.join(WORLD, 'data_tables/quest_hooks.yml'))) or {}).items()
         if isinstance(v, dict) and v.get('map') == 'D6'}
USED = set()
CASTLE_DOOR_TEXT = yaml.safe_load(open(os.path.join(WORLD, 'source/quests/m33.yml')))['hooks']['castle_door']['text']


def use(name):
    assert name in HOOKS, name
    USED.add(name)
    return name


def hook(name):
    return [{'lua': 'XeenQuests.hook("%s")' % use(name)}]


def hcall(name):
    return 'XeenQuests.hook("%s")' % use(name)


# A2's rows (data_tables/monster_data.txt)
ROW = {'lesser_elemental': 11620, 'elemental': 11621, 'archer': 11104, 'archer_chief': 11105, 'griffin': 11913,
       'patrol': 11610, 'annihilator': 11611, 'ambrose': 11917}
# D-52: Ambrose on A2's row 11917 (until it lands in monster_data, the King's Guard 11143 for validation only; the
# build prints it and the map is not called done with it)
AMBROSE_ROW_LIVE = '\n11917\t' in open(os.path.join(WORLD, 'data_tables/monster_data.txt')).read()
if not AMBROSE_ROW_LIVE:
    ROW['ambrose'] = 11143
QBIT = {'alamar_destroyed': 111662, 'alamar_inside': 111660, 'lava_cooled': 111564, 'm25_done': 111503,
        'mirror_necropolis': 119011, 'obelisk_dark_6': 115055, 'archers_burned': 116200}
ITEMS = {'necropolis_pass': 12336}
NPC = {'ambrose': 5512}
G_AMBROSE = 6
G_ARCHERS = 5
G_ELEMENTALS = (1, 2, 3, 4)
G_ROBOTS = tuple(range(11, 20))
HOUSE_MIRROR = HOUSE['thing:np_mirror'][0]
SEALED = '(Not yet open: this place comes in a later part of the world.)'


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def dist_to_line(px, py, line):
    return min(K.seg_dist((px, py), a, b) for a, b in zip(line, line[1:]))


def poly_dist(p, poly):
    return min(K.seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def inside(p, poly):
    return K.inside(p, poly)


def msg(text):
    return {'lua': 'evt.SimpleMessage(%s)' % lstr(text)}


def lstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')


def yes_no_before(text):
    """D-72 rule 3: a structure's `lua_before` that asks with Yes/No buttons whose own text is the question (no
    SetMessage before it) and lets the studio's `into` move run only on Yes (step 1; No 2, Escape 3)."""
    return ('if continueStep == nil then AskChoiceWithAnswerSteps(eventId, 3, %s, {{Answer = "Yes", Step = 1}, '
            '{Answer = "No", Step = 2}}) return end\nif continueStep ~= 1 then return end' % lstr(text))


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
    out = [word] * n
    if window_at is not None:
        out[window_at] = 'window'
    return out


# ---------------------------------------------------------------------------------------------------------------
# Land. Heights are map units above the stars below the rims (0).
# ---------------------------------------------------------------------------------------------------------------
RIM_N = 24
RIM_W = 24
BORDER = 109
MOAT_LEVEL = 1550
LAKE_LEVEL = 1450
MESA_TOP = 2304
TOWN_H = 1664
PASS_H = 2464
CASTLE_BOX = (45.5, 40.5, 56.5, 51.5)
GATEHOUSE = (49.5, 50.5, 52.5, 53.5)      # the gatehouse block in the south wall; its gate face at y 53.5
MOAT = [[40, 58], [35, 50], [36, 41], [42, 35], [51, 32], [60, 35], [65, 42], [65, 51], [62, 58], [59, 56], [61, 50],
        [60, 43], [56, 38], [51, 36], [45, 38], [40, 43], [39, 50], [43, 56]]
MESA = [[43, 56], [39, 50], [40, 43], [45, 38], [51, 36], [56, 38], [60, 43], [61, 50], [59, 56], [56, 58], [46, 58]]
RAMP = [[47, 53], [55, 53], [55.5, 58], [55, 63], [48, 63], [47.5, 58]]
# Corak's lava lake in two bodies round the genie islet ([65, 67] x [62, 64], whole cells), the south-east tongue of
# black rock reaching to the pod's hatch (whole cells; the studio's water outlines are drawn on whole cells)
ISLET = [[65, 62], [67, 62], [67, 64], [65, 64]]
LAKE_N = [[62, 64], [64, 59], [70, 57], [77, 59], [80, 64], [67, 64], [67, 62], [65, 62], [65, 64]]
LAKE_S = [[63, 62], [65, 62], [65, 64], [67, 64], [67, 62], [79, 62], [80, 64], [80, 70], [77, 71], [75, 69],
          [73, 69], [73, 71], [74, 73], [72, 75], [69, 75], [63, 72], [61, 66]]
LAKE = [[64, 59], [70, 57], [77, 59], [80, 64], [80, 70], [77, 71], [75, 69], [73, 69], [73, 71], [74, 73], [72, 75],
        [69, 75], [63, 72], [61, 66]]
BURNING = [[63, 54], [64, 56], [66, 59]]
SLAG = [[36, 49], [31, 50], [27, 51], [23, 51]]
NORTH_FALLS = [[46, 35], [45, 30], [44, 26], [44, 23]]
NECRO = [[82, 74], [100, 74], [100, 90], [82, 90]]
POD = (72.5, 67.5)
POD_R = 640
HATCH_DIR = (math.sqrt(0.5), math.sqrt(0.5))     # south-east
HATCH = (POD[0] + HATCH_DIR[0] * POD_R / 512, POD[1] + HATCH_DIR[1] * POD_R / 512)
HATCH_OUT = (HATCH[0] + HATCH_DIR[0] * 0.75, HATCH[1] + HATCH_DIR[1] * 0.75)   # DD-16's way out, 384 before it
CRUST_H = LAKE_LEVEL + 16
SHELTEM = (78.0, 38.0)

L1S = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'sketch.yml')))
CONTROL = [(p['at'][0], p['at'][1], p['h']) for p in L1S['heights']['points']]
CONTROL += [(70, 40, 1950), (90, 38, 2250), (60, 28, 1750), (34, 46, 1750), (28, 56, 1750), (68, 88, 1850),
            (74, 86, 1800), (80, 84, 1750), (56, 84, 1850), (44, 86, 1900), (102, 58, 2300), (100, 40, 2600),
            (66, 50, 1800), (70, 52, 1750), (84, 60, 1850), (88, 64, 1780), (92, 66, 1740), (106, 60, 2200),
            (106, 70, 2200), (60, 62, 1750), (60, 68, 1720)]
TERRACES = [  # (polygon, height, slope, note)
    ([[47.5, 39.5], [54.5, 39.5], [57.5, 42], [57.5, 52.5], [44.5, 52.5], [44.5, 42]], MESA_TOP, 2,
     "Castle Alamar's floor on the mesa."),
    (NECRO, TOWN_H, 3, "Necropolis inside its walls."),
    ([[61, 93], [67, 93], [67, 98], [61, 98]], PASS_H, 3, "Griffin Pass: Ambrose's camp."),
    ([[28, 28], [33, 28], [33, 33], [28, 33]], 1792, 2, 'The hot spring.'),
    ([[28, 60], [32, 60], [32, 64], [28, 64]], 2048, 2, 'Obelisk Knoll.'),
    ([[31, 84], [38, 84], [38, 88.5], [31, 88.5]], 1952, 3, "The archers' camp."),
    ([[42, 94], [50, 94], [50, 97], [42, 97]], 2688, 2, "The ledge before DD-10C's adit and the mines."),
    ([[42, 98], [50, 98], [50, 102], [42, 102]], 3584, 2,
     "The crag over the adit: the mines are cut into its face (session 14: from y 98 and 3,584, so no sky shows behind "
     "the mouth from the north)."),
    ([[76, 36], [80, 36], [80, 40], [76, 40]], 1920, 2, "Sheltem's crater."),
    ([[99, 29], [103, 29], [103, 33], [99, 33]], 2688, 2, 'The Well of Warding.'),
    ([[98, 67], [102, 67], [102, 71], [98, 71]], 1792, 2, "The climbers' camp."),
    ([[54.5, 60.5], [58.5, 60.5], [58.5, 63.5], [54.5, 63.5]], 1856, 2, 'The travel pyramid outside the moat.'),
    ([[73, 69], [75, 69], [76, 71], [74, 72]], 1488, 1, "The tongue of black rock before Corak's hatch."),
    (ISLET, 1520, 0, 'The genie islet in the lava.'),
    ([[64, 84], [68, 84], [68, 87], [64, 87]], 1792, 2, 'Ash Fork.'),
    ([[103, 62], [109, 62], [109, 66], [103, 66]], 1696, 2, "The border pass (edge_d5_d6.json's 1,700)."),
]


def _d1_row():
    sys.path.insert(0, os.path.join(REPO, 'util'))
    from map_export import parse_odm_file
    d = parse_odm_file(Path(os.path.join(WORLD, 'maps/xeen_d1.odm')))
    hm = d['payload']['height_map']
    return [hm[19 * 128 + x] * 32 for x in range(128)]


D1_ROW = _d1_row()
D5_COL = json.load(open(os.path.join(REPO, 'level_generation/xeen_art/phase5/edge_d5_d6.json')))['heights_by_y']


def roll(x, y):
    v = (90 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.6 + 1.1) + 60 * math.sin((x + 1.4 * y) / 4.7 + 0.3)
         + 40 * math.sin((x - 1.7 * y) / 2.6))
    w = 1.0
    for poly, _h, _s, _n in TERRACES:
        w = min(w, smooth(poly_dist((x, y), poly) / 3.0) if not inside((x, y), poly) else 0.0)
    return w * v


def land(x, y):
    if y < RIM_N or x < RIM_W:
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
    if inside(p, MESA):
        h = max(h, MESA_TOP - 40)
    if inside(p, RAMP):
        h = MESA_TOP - (MESA_TOP - 1856) * smooth((y - 53) / 10.0)
    if inside(p, MOAT):
        return MOAT_LEVEL - 160
    if inside(p, LAKE):
        return LAKE_LEVEL - 160
    if not inside(p, MESA) and not inside(p, RAMP):
        d = poly_dist(p, MOAT)
        if d < 5:
            h = min(h, MOAT_LEVEL + 40 + 130 * d)
    d = poly_dist(p, LAKE)
    if d < 6:
        h = min(h, LAKE_LEVEL + 40 + 110 * d)
    for line in (BURNING, SLAG, NORTH_FALLS):
        d = dist_to_line(x, y, line)
        if d < 3:
            h = min(h, MOAT_LEVEL + 20 + 140 * d)
    if y > 101:
        t = smooth((y - 101) / 8.0)
        h = h * (1 - t) + D1_ROW[max(0, min(127, int(round(x))))] * t
    if x > 101:
        t = smooth((x - 101) / 8.0)
        h = h * (1 - t) + D5_COL[max(0, min(127, int(round(y))))] * t
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


# ---------------------------------------------------------------------------------------------------------------
# Necropolis (A4's d6.yml): plots (building, index, at = NW corner, facing, [front, depth], kind)
# ---------------------------------------------------------------------------------------------------------------
GRADE = {
    'service': {'wall': 't09a01', 'window': 't09a04b', 'door': 't09a03a', 'post_left': 't09a06',
                'post_right': 't09a07', 'roof': 'xlslate', 'trim': 't09b11b', 'ridge': 't06a10', 'gable': 't09a01'},
    'tomb': {'wall': 'twb2', 'window': 'twb2', 'door': 't09a03c', 'post_left': 'twb2', 'post_right': 'twb2',
             'roof': 'twb1', 'trim': 'twb1', 'ridge': 'twb1', 'gable': 'twb2'},
}
PLOTS = [
    ('building:np_guild', None, (84.0, 76.0), 'e', [3, 3], 'service', 'hall'),
    ('building:np_market', None, (96.0, 76.0), 'w', [3, 2], 'service', 'cottage'),
    ('building:np_embalmer', None, (96.0, 80.0), 'w', [2, 2], 'service', 'cottage'),
    ('building:np_tavern', None, (84.0, 80.0), 'e', [3, 3], 'service', 'cottage'),
    ('building:np_temple', None, (89.0, 82.0), 'n', [4, 3], 'service', 'hall'),
    ('building:np_houses', 1, (94.0, 83.0), 'w', [3, 3], 'tomb', 'tomb'),
    ('building:np_houses', 2, (90.0, 87.0), 'n', [3, 2], 'tomb', 'tomb'),
    ('building:np_houses', 3, (84.0, 87.0), 'n', [2, 2], 'tomb', 'tomb'),
    ('building:np_houses', 4, (87.0, 87.0), 'n', [2, 2], 'tomb', 'tomb'),
    ('building:np_houses', 5, (94.0, 87.0), 'n', [2, 2], 'tomb', 'tomb'),
    ('building:np_houses', 6, (84.0, 84.0), 'e', [2, 2], 'tomb', 'tomb'),
]
# D-92 (A4, 2026-11-22): every service house hangs its kind's sign (tools/xeen/house_signs.py); the temple none (MM8)
SIGNS = {'building:np_guild': 'sgdark', 'building:np_market': 'sgmagic', 'building:np_embalmer': 'sgalch',
         'building:np_tavern': 'sgtvrn'}
plots_by_space = {}
plan_buildings = {}
footprints = []
doors_out = []


def add_plot(space, bid, index, at, facing, fp, grade, kind):
    x, y = at
    key = bid if index is None else '%s#%d' % (bid, index)
    hid, hname = HOUSE[key]
    plot = {'building': bid, 'at': [x, y], 'facing': facing, 'kit': 'grey', 'floor': TOWN_H, 'house': hid,
            'title': hname}
    if index is not None:
        plot['index'] = index
    Wp, Hp = K.plot_extent(facing, fp)
    if kind == 'hall':
        # two storeys of t09 ashlar under slate, a band at the floor beam, the carved double door as two leaves
        plot['parts'] = [{'id': 'body', 'at': [64, 64], 'size': [Wp - 128, Hp - 128], 'wall_height': 544,
                          'band': 32, 'roof': 'hip', 'roof_pitch': 40, 'eaves': 48, 'door_height': 288,
                          'textures': {'band': 't09b11b'}}]
        if SIGNS.get(bid):
            plot['parts'][0]['signs'] = [{'wall': facing, 'bay': 0, 'texture': SIGNS[bid], 'hang': True,
                                          'size': K.sign_size(SIGNS[bid]), 'out': 48, 'bottom': 192}]
        plot['door'] = {'part': 'body', 'wall': facing, 'leaves': 2, 'arch': 'round'}
    elif kind == 'tomb':
        # a mausoleum of Zokarr's Tomb stone: a flat-roofed block with a stepped top, its iron door once
        plot['parts'] = [{'id': 'body', 'at': [96, 96], 'size': [Wp - 192, Hp - 192], 'wall_height': 384,
                          'roof': 'flat', 'windows': 'none'},
                         {'id': 'cap', 'at': [160, 160], 'size': [Wp - 320, Hp - 320], 'bottom': 384,
                          'wall_height': 96, 'roof': 'flat', 'windows': 'none'}]
        plot['door'] = {'part': 'body', 'wall': facing}
    else:
        parts, door = K.shape(kind, facing, fp, 'grey', sign=SIGNS.get(bid))
        plot['parts'] = parts
        plot['door'] = door
    plot['textures'] = dict(GRADE[grade])
    plots_by_space.setdefault(space, []).append(plot)
    pb = plan_buildings.setdefault(space, {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [],
                   'service': 'residence' if bid == 'building:np_houses' else hname}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append((index or 0, fp))
    footprints.append((bid, index, K.footprint(x, y, facing, fp, 0)))
    doors_out.append((bid, index, K.door_cell(x, y, facing, fp, 0, 0.0), K.door_cell(x, y, facing, fp, 0, 0.9)))


for _p in PLOTS:
    add_plot('town:necropolis', *_p)
for _pb in plan_buildings.values():
    for _b in _pb.values():
        _b['footprint_cells'] = [fp for _, fp in sorted(_b['footprint_cells'], key=lambda t: t[0])]


def move_lua(key):
    blv = 'xeen_%s.blv' % key
    a = studio_entrances(blv)[ENTRANCE[key]]
    at = a.get('at') or a.get('position')
    face = a.get('facing', a.get('direction', 0))
    return 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, 0, 0, "%s")' % (at[0], at[1], at[2], int(face), blv)


# ---------------------------------------------------------------------------------------------------------------
# Roads and paths (L1's, the approach straightened between the pylons)
# ---------------------------------------------------------------------------------------------------------------
MOUNTAIN_ROAD = [[64, 128], [64, 109], [64, 104], [63.5, 100], [64, 96.5], [65, 92.5], [66, 88.5], [66, 85]]
ALAMAR_ROAD = [[66, 85], [62, 81], [58.5, 76.5], [56, 71], [54, 66.5], [52, 63], [51, 60], [51, 54.5]]
NECRO_ROAD = [[66, 85], [71, 82.5], [76, 80], [80.5, 78], [84, 74.5], [87.5, 71.5], [91, 71]]
PASS_ROAD = [[128, 64], [109, 64], [104, 64], [99, 65.5], [95, 68], [91, 71]]
GATE_LANE = [[91, 71], [91, 74], [91, 78]]
HATCH_PATH = [[79, 78.5], [77.5, 75], [75.5, 72], [74.5, 70]]
ADIT_TRACK = [[66, 85], [60, 87], [54, 89], [48, 91], [44, 92], [42, 90], [38.5, 89]]
ADIT_SPUR = [[44, 92], [45, 94], [46, 95.5]]
OBELISK_PATH = [[54, 66.5], [47, 65.5], [40, 64.5], [34, 63], [31, 62.5]]
SPRING_TRACK = [[40, 64.5], [35, 60], [32, 54.5], [31, 48], [30, 41], [30, 35], [30.5, 32]]
FIELD_TRACK = [[80.5, 78], [83, 70], [84.5, 63], [82, 56], [79, 49], [78, 43], [78, 40.5]]
RIM_TRACK = [[78, 40.5], [82, 36], [88, 33], [94, 31.5], [99.5, 31]]
ROADS = [MOUNTAIN_ROAD, ALAMAR_ROAD, NECRO_ROAD, PASS_ROAD, GATE_LANE]
PATHS = [HATCH_PATH, ADIT_TRACK, ADIT_SPUR, OBELISK_PATH, SPRING_TRACK, FIELD_TRACK, RIM_TRACK]


def check_roads():
    bad = []
    for b, ix, poly in footprints:
        for line in ROADS:
            if K.line_hits_poly(line, poly, 0.45):
                bad.append('road under or against %s#%s' % (b, ix))
    if bad:
        raise SystemExit('\n'.join(bad))


check_roads()

# ---------------------------------------------------------------------------------------------------------------
# Places
# ---------------------------------------------------------------------------------------------------------------
SOUTH_START = (64.0, 105.0)       # the D1 arrival on the mountain road, facing north
EAST_START = (105.0, 64.0)        # the D5 arrival at the border pass, facing west
NP_ARRIVAL = (91.0, 76.6)         # necropolis_gate: inside the gate by the mirror, facing south (the square)
NP_GATE = (91.0, 74.0)
MIRROR = (92.6, 78.0)
GATE_ARRIVAL = (51.0, 55.0)       # entrance:dd17_gate before Alamar's gate, facing south (DD-17's refusal)
PYRAMID = (56.5, 62.0)
PYRAMID_ARRIVAL = (54.5, 62.0)    # entrance:xd17_pyramid (D-50), facing north (the castle)
PYLONS = [(49.4, 56.4), (52.6, 56.4), (49.4, 59.6), (52.6, 59.6)]
ADIT = (46.0, 97.5)               # DD-10C's adit mouth (its front's middle), looking north
ADIT_ARRIVAL = (46.0, 95.8)       # entrance:dd10c_adit, facing north (away from the adit)
CRYPT = (98.0, 88.6)              # DD-21's crypt stair head, its grille door north
CRYPT_ARRIVAL = (98.0, 86.8)
AMBROSE = (61.0, 95.0)
GRIFFIN = (62.2, 95.9)
OBELISK = (30.0, 62.0)
ARCHER_CAMP = (34.5, 86.0)
ARCHER_CHEST = (35.6, 86.6)
ELEMENTAL_LEASH = 1024
SPAWN_CLEAR = 2000
# D-87.3: every outdoor arrival point (cells), for the ranged disablers' 5,888 (A6 s31; d85.py reads the built ones)
D87_ARRIVALS = {'the D1 arrival': SOUTH_START, 'the D5 arrival': EAST_START, 'the pyramid': PYRAMID_ARRIVAL,
                'the adit': ADIT_ARRIVAL, 'Ambrose': AMBROSE, 'the DD-22 hatch': (78.0, 40.0),
                'the DD-16 hatch': (74.0, 69.0), 'Castle Alamar': (51.0, 55.0), 'the Necropolis': (91.0, 77.0),
                'the Necropolis gate': (91.0, 72.0), 'the DD-21 stair': (98.0, 87.0)}
HATCH_CLEAR = 2500


def build():
    os.makedirs(OUT, exist_ok=True)
    L1P = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'project.yml')))
    # ================================ project.yml
    neighbours = []
    for n in L1P['neighbours']:
        n = copy.deepcopy(n)
        nid = n['id']
        if nid == 'edge:east' and not D5_LIVE:
            continue
        if nid == 'mirror:darkside':
            continue
        if nid.startswith('door:'):
            key = nid.split(':')[1]
            if DUNGEON.get(key):
                n.pop('listed_only', None)
                n['arrival'] = ENTRANCE[key]
            else:
                n['listed_only'] = True
                n.pop('arrival', None)
            n.pop('condition', None)
        if nid == 'scripted:griffin':
            n['notes'] = ("M25: Ambrose's topic calls A3's m25.flight, which moves the party to DD-14's "
                          "entrance:d6_griffin itself (A3, 2026-11-21).")
        neighbours.append(n)
    ms = copy.deepcopy(L1P['map_stats'])
    ms['continent'] = 7
    project = {
        'format': 0, 'id': STEM, 'name': 'The Forbidden Zone', 'world': 'xeen', 'kind': 'outdoor',
        'profile': 'odm', 'map_code': 'D6', 'units': {'plan_grid': 512}, 'extent': {'terrain_cells': 128},
        'map_stats': ms, 'neighbours': neighbours, 'qbits': dict(QBIT), 'items': dict(ITEMS),
        'rules': {'respawn': 'entrance:necropolis_gate', 'town_portal_anchor': 'entrance:necropolis_gate',
                  'rim': {'cliff_x': RIM_W, 'cliff_y': RIM_N, 'fall': 'death', 'sides': ['north', 'west']}},
        'notes': ("D6 The Forbidden Zone (A6, 2026-11-21), built from the approved L1 with D-49 and D-50. The south "
                  "edge (D1) is live; the east edge (D5) is sealed by a sign until D5 is installed; each dungeon door "
                  "shows its hook and a sealed line until its BLV is installed and lists the door's entrance. "
                  "Written by output/studio_cal/d6/tools/gen.py."),
    }
    # ================================ plan.yml
    L1 = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'plan.yml')))
    plan = copy.deepcopy(L1)
    plan['level'] = 'L3'
    for s in plan['spaces']:
        if s['id'] in plan_buildings:
            s['buildings'] = list(plan_buildings[s['id']].values())
    ents = []
    for e in plan['entrances']:
        e = copy.deepcopy(e)
        if e.get('neighbour') == 'edge:east' and not D5_LIVE:
            e = {'id': e['id'], 'space': e['space'], 'kind': 'arrival', 'facing': 'w',
                 'how': "The border pass from D5: sealed by a sign until D5 is installed (then D5's arrival)."}
        if e.get('neighbour') == 'mirror:darkside':
            e = {k: v for k, v in e.items() if k != 'neighbour'}
            e['facing'] = 's'
        nb = e.get('neighbour', '')
        if nb.startswith('door:') and not DUNGEON.get(nb.split(':')[1]):
            e.pop('neighbour', None)
            e['kind'] = 'arrival'
        if e['id'] == 'entrance:dd16_hatch':
            e['facing'] = 'se'
            e['how'] = ("DD-16's way out: on the crust 384 before Corak's hatch, facing south-east toward the shore "
                        "(D-47, D-49). The hatch itself (m29.pod_door) leads into DD-16's entrance:d6_hatch.")
        e.pop('condition', None)
        ents.append(e)
    ents.sort(key=lambda e: (e['id'] != 'entrance:necropolis_gate', e['id'] != 'entrance:south_road'))
    plan['entrances'] = ents
    # D-58 Q10 (A6 s16): a fall from D7's zone A1-B2 lands here (Xeen.SkyFalls.d7_d6); whole flat cell, 256 clear
    plan['entrances'].append({'id': 'entrance:d7_fall', 'space': next(e['space'] for e in ents if e['id'] == 'entrance:necropolis_gate'),
                              'kind': 'both', 'facing': 's',   # 'arrival' would make it the party start
                              'how': "D-58 Q10: a fall from D7 lands here, on the Necropolis square, 740 from the mirror (back to Olympus)."})
    plan.pop('totals', None)
    plan['sketch'] = {'file': 'sketch.yml', 'grid': 512}
    plan['notes'] = ('L3/L4 written by output/studio_cal/d6/tools/gen.py from the approved L1 with D-49 and D-50. '
                     'The lava dwellers, the archers and the robots (D-49 change 7: hidden on load after m33.done) '
                     'are placed actors; the gazers and the birds are slot markers.')
    # ================================ sketch.yml
    frame = copy.deepcopy(L1S['frame'])
    frame['edges'] = [e for e in frame['edges'] if (e['side'] == 'south' and D1_LIVE) or (e['side'] == 'east'
                                                                                          and D5_LIVE)]
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its land function.'},
        'points': [{'at': [x, y], 'h': int(h)} for x, y, h in CONTROL
                   if (x >= BORDER or y >= BORDER) and x >= RIM_W and y >= RIM_N] + [
            {'at': [64, 106], 'h': 1800, 'notes': 'the D1 arrival, climbing'},
            {'at': [51, 57], 'h': 2150, 'notes': "the approach ramp below Alamar's gate"},
            {'at': [51, 60], 'h': 1980}, {'at': [52, 62], 'h': 1880},
            {'at': [50, 100], 'h': 3650, 'notes': 'the western peaks'}, {'at': [78, 101], 'h': 3800},
            {'at': [88, 101], 'h': 3500, 'notes': 'the genie crag'}, {'at': [36, 40], 'h': 2240,
                                                                       'notes': 'the genie pinnacle'},
            {'at': [49, 80], 'h': 2300, 'notes': 'the cinder cone'},
            {'at': [46, 100], 'h': 3700, 'notes': "the crag over DD-10C's adit"}, {'at': [43, 100], 'h': 3600},
            {'at': [49, 100], 'h': 3200}],
        'terraces': [{'polygon': poly, 'height': h, 'slope': s, 'notes': n} for poly, h, s, n in TERRACES],
        'cliffs': [
            {'line': [[128, RIM_N], [RIM_W, RIM_N], [RIM_W, 128]], 'drop': 1600, 'down': 'right',
             'notes': "The world rim, north then west; the lava falls over it at (44, 24) and (24, 51)."},
            {'line': [[79, 107], [84, 106], [89, 107]], 'drop': 1300, 'down': 'right',
             'notes': "The Sardaj cliff: the peaks' south face down to D1's spring pool at the border."},
            {'line': [[43, 56], [39, 50], [40, 43], [45, 38], [51, 36], [56, 38], [60, 43], [61, 50], [59, 56]],
             'drop': 600, 'down': 'left', 'notes': "Alamar's mesa: its cliffs into the moat."},
        ],
        'ridges': copy.deepcopy(L1S['heights']['ridges']),
    }
    water = {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0,
             'polygon': [[0, 0], [128, 0], [128, RIM_N], [RIM_W, RIM_N], [RIM_W, 128], [0, 128]],
             'notes': 'Below the rim: stands for the stars.'},
            {'id': 'water:pod_lake', 'index': 1, 'kind': 'lake', 'level': LAKE_LEVEL, 'polygon': LAKE_N,
             'tile_set': 'lavtyl', 'notes': "Corak's lava lake north of y 64 (D-40: lavtyl, never water)."},
            {'id': 'water:pod_lake', 'index': 2, 'kind': 'lake', 'level': LAKE_LEVEL, 'polygon': LAKE_S,
             'tile_set': 'lavtyl', 'notes': "Corak's lava lake south of y 62, round the islet and the tongue."},
            {'id': 'water:alamar_moat', 'kind': 'lake', 'level': MOAT_LEVEL, 'polygon': MOAT, 'tile_set': 'lavtyl',
             'notes': "Alamar's moat: a horseshoe of lava round the mesa, open to the south (the approach)."},
        ],
        'rivers': [
            {'id': 'water:burning_channel', 'line': BURNING, 'width_cells': 2, 'tile_set': 'lavtyl',
             'notes': "Lava from the moat's east arm down into Corak's lake."},
            {'id': 'water:slag_run', 'line': SLAG, 'width_cells': 2, 'tile_set': 'lavtyl',
             'notes': "Lava from the moat's west arm over the west rim."},
            {'id': 'water:north_falls', 'line': NORTH_FALLS, 'width_cells': 2, 'tile_set': 'lavtyl',
             'notes': "Lava from the moat's north arm over the north rim."},
        ],
    }
    roads = [
        {'link': 'link:mountain_road', 'line': MOUNTAIN_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:alamar_road', 'line': ALAMAR_ROAD, 'width': 'road', 'surface': 'road_flagstone'},
        {'link': 'link:necropolis_road', 'line': NECRO_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:pass_road', 'line': PASS_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:gate_lane', 'line': GATE_LANE, 'width': 'road', 'surface': 'road_flagstone'},
        {'link': 'link:hatch_path', 'line': HATCH_PATH, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:adit_track', 'line': ADIT_TRACK + ADIT_SPUR[1:], 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:obelisk_path', 'line': OBELISK_PATH, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:spring_track', 'line': SPRING_TRACK, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:field_track', 'line': FIELD_TRACK, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:rim_track', 'line': RIM_TRACK, 'width': 'lane', 'surface': 'dirt'},
    ]
    districts = []
    for d in L1S['districts']:
        d = copy.deepcopy(d)
        if d['space'] in plots_by_space:
            d['plots'] = plots_by_space[d['space']]
        districts.append(d)
    points = [{'id': 'entrance:south_road', 'at': list(SOUTH_START), 'facing': 'n'},
              {'id': 'entrance:east_pass', 'at': list(EAST_START), 'facing': 'w'},
              {'id': 'entrance:necropolis_gate', 'at': list(NP_ARRIVAL), 'facing': 's'},
              {'id': 'entrance:np_gate', 'at': [NP_GATE[0], NP_GATE[1] - 1.6], 'facing': 'n'},
              {'id': 'entrance:dd17_gate', 'at': list(GATE_ARRIVAL), 'facing': 's'},
              {'id': 'entrance:fd01_stair', 'at': list(GATE_ARRIVAL), 'facing': 's'},
              {'id': 'entrance:dd16_hatch', 'at': [round(HATCH_OUT[0], 2), round(HATCH_OUT[1], 2)], 'facing': 'se'},
              {'id': 'entrance:dd22_hatch', 'at': [SHELTEM[0], SHELTEM[1] + 2.0], 'facing': 's'},
              {'id': 'entrance:dd21_stair', 'at': list(CRYPT_ARRIVAL), 'facing': 'n'},
              {'id': 'entrance:dd10c_adit', 'at': list(ADIT_ARRIVAL), 'facing': 'n'},
              {'id': 'entrance:xd17_pyramid', 'at': list(PYRAMID_ARRIVAL), 'facing': 'n'},
              {'id': 'junction:ash_fork', 'at': [66, 85]}, {'id': 'junction:bone_fork', 'at': [91, 71]}]
    points.append({'id': 'entrance:d7_fall', 'at': [91, 79], 'facing': 's'})   # D-58 Q10 (A6 s16)
    POI_AT = {'poi:obelisk': OBELISK, 'poi:fountain_resilience': (30.4, 30.4), 'poi:warding_well': (101, 31),
              'poi:books': (88.7, 79.0), 'poi:skull': (MIRROR[0] + 0.5, MIRROR[1] + 0.3), 'poi:mirror': MIRROR,
              'poi:barrel': (87.25, 82.6), 'poi:genie_pinnacle': (36, 40), 'poi:genie_islet': (66, 63),
              'poi:genie_crag': (88, 101), 'poi:archers_chest': ARCHER_CHEST, 'poi:griffin_nest': (76, 94),
              'poi:prospector': (40, 96), 'poi:ancient_locker': (88, 44), 'poi:pilgrim_cart': (86, 69),
              'poi:spring_pilgrim': (32, 32), 'poi:fork_signpost': (66.5, 85.5), 'poi:zone_sign': (102, 65.2),
              'poi:ambrose': AMBROSE, 'poi:climbers_camp': (100, 69), 'poi:travel_pyramid': PYRAMID}
    for k, at in POI_AT.items():
        points.append({'id': k, 'at': [round(at[0], 2), round(at[1], 2)]})
    for i, at in enumerate([(43.5, 97.5), (48.5, 97.5)]):
        points.append({'id': 'poi:mine_mouths', 'index': i + 1, 'at': list(at)})
    points += [{'id': 'landmark:alamar', 'at': [51, 46]}, {'id': 'landmark:corak_pod', 'at': list(POD)},
               {'id': 'landmark:sheltem_pod', 'at': list(SHELTEM)}, {'id': 'landmark:necropolis', 'at': [91, 82]},
               {'id': 'landmark:north_falls', 'at': [44, 24]}, {'id': 'landmark:west_falls', 'at': [24, 51]},
               {'id': 'landmark:broken_pyramid', 'at': [84, 98]}, {'id': 'landmark:cinder_cone', 'at': [49, 80]},
               {'id': 'landmark:ridge_tower', 'at': [104, 81]}]
    # ---------------------------------------------------------------- encounter areas (33 markers)
    areas = []

    def markers(pop, spots, slot):
        for (cx, cy) in spots:
            k = sum(1 for a in areas if a['id'] == pop) + 1
            areas.append({'id': pop, 'index': k, 'kind': 'encounter', 'count': 1, 'slot': slot,
                          'circle': {'at': [cx, cy], 'r': 1}})
    # E1: the Ancient field's eyes (slot 1)
    # D-87.3 (A6 s31): the eyes are ranged disablers (Floating Eye: Paralyze by missile; Terrible Eye: Insane), so
    # none within 5,888 of an arrival: the five round Sheltem's pod moved to the field's rim, off DD-22's hatch
    # (were (70, 34), (84, 32), (72, 42), (84, 40), (76, 49): 3,024-5,370 from entrance:dd22_hatch), and the last a cell in from the D5 arrival (was (100, 53))
    # F10 (s32): the eye at (74, 27) moved to the empty north-west corner (28, 28)
    markers('pop:field_gazers', [(68, 28), (28, 28), (81, 27), (88, 27), (95, 27), (103, 27), (66, 31), (92, 31),
                                 (92, 36), (100, 37), (70, 53), (91, 46), (95, 44), (103, 46), (80, 54), (88, 50),
                                 (99, 52)], 1)
    # E4a / E4b: griffins and rocs on the southern peaks (slot 2); the pass, the adit and the D1 road clear
    # D-85 (A6 s30): the seventh west pair moved off Ambrose's camp (was (55, 101): 4,433)
    markers('pop:west_griffins', [(28, 94), (34, 93.5), (40, 92.5), (30, 100), (37, 101), (52, 92.5), (47, 102),
                                  (28, 106)], 2)
    markers('pop:east_griffins', [(73, 92), (79, 92), (85, 94), (92, 95), (99, 96), (75, 101), (95, 103),
                                  (104, 100)], 2)
    town_doors = [d[2] for d in doors_out]
    clear = {'the adit': (ADIT_ARRIVAL, SPAWN_CLEAR), 'the pyramid': (PYRAMID_ARRIVAL, SPAWN_CLEAR),
             'the D1 arrival': (SOUTH_START, SPAWN_CLEAR), 'the D5 arrival': (EAST_START, SPAWN_CLEAR),
             'Ambrose': (AMBROSE, SPAWN_CLEAR)}
    for a in areas:
        c = a['circle']['at']
        if min(math.hypot(c[0] - d[0], c[1] - d[1]) for d in town_doors) * 512 < 2500:
            raise SystemExit('monsters within 2,500 of a town door: %s %s' % (a['id'], c))
        # D-85: no marker circle within missile range (5,120) of Ambrose, the outdoor talking giver; the sixth west
        # circle reaches 4,345 but its built marker stands at 5,201 (a warning, A6 s30's d85.py)
        if (math.hypot(c[0] - AMBROSE[0], c[1] - AMBROSE[1]) - a['circle']['r']) * 512 < 5120 and \
                (a['id'], a['index']) != ('pop:west_griffins', 6):
            raise SystemExit('D-85: a marker within 5,120 of Ambrose: %s %s' % (a['id'], c))
        for k, (u, r) in clear.items():
            if math.hypot(c[0] - u[0], c[1] - u[1]) * 512 < r:
                raise SystemExit('a marker within %d of %s: %s' % (r, k, c))
        # D-87.3: slot 1's eyes are ranged disablers: the whole circle at least 5,888 from every arrival point
        if a['slot'] == 1:
            for k, u in D87_ARRIVALS.items():
                if (math.hypot(c[0] - u[0], c[1] - u[1]) - a['circle']['r']) * 512 < 5888:
                    raise SystemExit('D-87: an eye marker within 5,888 of %s: %s %s' % (k, a['id'], c))
    areas += [
        {'id': 'zone:mountain_road', 'kind': 'keep_clear', 'polygon': [[59, 92], [69, 92], [69, 109], [59, 109]],
         'notes': "The D1 arrival and Ambrose's camp at Griffin Pass."},
        {'id': 'zone:pass_east', 'kind': 'keep_clear', 'polygon': [[96, 59], [109, 59], [109, 73], [96, 73]],
         'notes': "The D5 arrival and the climbers' camp."},
        {'id': 'town:necropolis', 'kind': 'keep_clear', 'polygon': [[77, 69], [105, 69], [105, 95], [77, 95]],
         'notes': 'Necropolis and its buffer (2,500 round the doors).'},
        {'id': 'zone:south_peaks', 'kind': 'keep_clear', 'polygon': [[42, 92], [50, 92], [50, 100], [42, 100]],
         'notes': "D-49 change 3: no marker within 2,000 of DD-10C's return point outside the adit."},
        {'id': 'zone:alamar_approach', 'kind': 'keep_clear', 'polygon': [[50, 58], [59, 58], [59, 66], [50, 66]],
         'notes': "D-50 Q9: no marker within 2,000 of the travel pyramid's arrival."},
        {'id': 'zone:pod_crust', 'kind': 'keep_clear', 'polygon': [[70, 66], [79, 66], [79, 75], [70, 75]],
         'notes': "The hatch's crust and DD-16's way out."},
    ]
    views = [
        {'id': 'view:arrival', 'at': [64, 96], 'height': 180, 'look': [56, 50],
         'purpose': ("From Griffin Pass looking north: the road down to Ash Fork, Corak's lake and pod right of "
                     "centre, Castle Alamar far north on its mesa ringed by lava (about 26,500).")},
        {'id': 'view:signature', 'at': [82, 72], 'height': 400, 'look': [51, 47],
         'purpose': ("From the lake's east shore by the Necropolis road, looking west: Corak's pod nose-up in the "
                     "lava, its hatch toward the shore, and beyond the moat Castle Alamar's lit walls (about 20,700); "
                     "the camera raised so the moat's glow reads as a line under the walls (D-49 change 10).")},
    ]
    structures = []
    S = structures.append
    alamar(S)
    pods(S)
    necropolis(S)
    wilds(S)
    # ---------------------------------------------------------------- actors
    actors = []

    def place(row, at, count, spread, group, **kw):
        a = {'monster': str(row), 'at': [round(at[0], 2), round(at[1], 2)], 'count': count, 'spread': spread,
             'group': group}
        a.update(kw)
        actors.append(a)
    # the lava dwellers (D-49 Q2): 14 placed fire elementals over the lake and its shores, each on a home radius;
    # none whose home plus radius comes within 2,500 of DD-16's way out on the crust (change 4)
    LAVA = [(ROW['lesser_elemental'], (64.0, 56.5), 3, 1.2, 1), (ROW['lesser_elemental'], (63.0, 67.5), 3, 1.2, 2),
            (ROW['elemental'], (63.5, 70.0), 1, 0, 2), (ROW['lesser_elemental'], (74.0, 59.5), 3, 1.2, 3),
            (ROW['elemental'], (77.5, 61.0), 1, 0, 3), (ROW['lesser_elemental'], (67.5, 60.0), 2, 0.8, 4),
            (ROW['elemental'], (66.0, 72.5), 1, 0, 4)]
    for row, at, n, spread, g in LAVA:
        d = math.hypot(at[0] - HATCH_OUT[0], at[1] - HATCH_OUT[1]) * 512 - spread * 512 - ELEMENTAL_LEASH
        if d < HATCH_CLEAR:
            raise SystemExit('a lava dweller within %d of the hatch: %s (%d)' % (HATCH_CLEAR, at, d))
        place(row, at, n, spread, g, hostile=True, leash=ELEMENTAL_LEASH)
    # the archers' camp (D-49 Q3): 9 + 3 placed, hostile
    place(ROW['archer'], (ARCHER_CAMP[0] - 0.6, ARCHER_CAMP[1] - 0.4), 9, 1.6, G_ARCHERS, hostile=True)
    place(ROW['archer_chief'], (ARCHER_CAMP[0] + 0.6, ARCHER_CAMP[1] - 0.2), 3, 0.8, G_ARCHERS, hostile=True)
    # the robots (D-49 change 7, D-36's coven pattern): placed in nine groups on the mesa and the approach, hidden on
    # load after m33.done; MM7's Dif 1 odds give 16 Patrols and 2 Annihilators at load (the slot's mean of 18)
    ROBOT_SPOTS = [(44.0, 40.0), (51.0, 38.5), (58.0, 40.0), (59.0, 47.0), (58.5, 53.5), (43.0, 47.0), (43.5, 53.5),
                   (47.0, 55.0), (55.0, 55.5)]
    for i, (at, g) in enumerate(zip(ROBOT_SPOTS, G_ROBOTS)):
        row = ROW['annihilator'] if i == 4 else ROW['patrol']
        for k, (u, r) in clear.items():
            if math.hypot(at[0] - u[0], at[1] - u[1]) * 512 < r:
                raise SystemExit('robots within %d of %s: %s' % (r, k, at))
        place(row, at, 2, 0.6, g, hostile=True)
    # Ambrose and the Tethered Griffin (D-49 change 6), hidden on load after m25.done (m25.camp_gone)
    actors.append({'monster': str(ROW['ambrose']), 'npc': NPC['ambrose'], 'at': list(AMBROSE), 'spread': 0,
                   'group': G_AMBROSE, 'hostile': False})
    place(ROW['griffin'], GRIFFIN, 1, 0, G_AMBROSE, hostile=False)
    # ---------------------------------------------------------------- events
    use('m25.flight')        # Ambrose's topic calls it (A3): the move to DD-14 is the hook's own
    beds = os.path.join(REPO, 'level_generation/projects/xeen/common/beds/xeen_d6.yml')
    bed_sounds = (yaml.safe_load(open(beds)) or {}).get('sounds') or [] if os.path.exists(beds) else []
    # the scene numbers the sketch's sounds from 1 in the order of their ids (checked on the build: sorted)
    HUM_KEY = 1 + sorted(b['id'] for b in bed_sounds).index('sound:alamar_hum')
    robots_hide = ' '.join('evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1)' % g for g in G_ROBOTS)
    whole_ids, ruin_ids = alamar_ids()
    events = [
        {'id': 'evt:sky', 'trigger': 'load', 'effects': [{'lua': 'Xeen.applyDarksideSky()'}],
         'notes': "Darkside's sky by the sun's stage (A3's helper)."},
        {'id': 'evt:camp_gone', 'trigger': 'load', 'condition': {'lua': 'XeenQuests.can("%s")' % use('m25.camp_gone')},
         'lua': 'evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1)' % G_AMBROSE,
         'notes': "m25.camp_gone (D-49 change 6): Ambrose and the griffin gone after m25.done; the tent and the cold "
                  "fire stay."},
        {'id': 'evt:robots_gone', 'trigger': 'load',
         'condition': {'lua': 'XeenQuests.can("%s")' % use('m33.robots_gone')}, 'lua': robots_hide,
         'notes': "m33.robots_gone (D-49 change 7): the robots' nine groups hidden after m33.done (no refill)."},
        {'id': 'evt:alamar_ruin', 'trigger': 'load', 'condition': {'qbit': 'alamar_destroyed'},
         'effects': [{'hide': i} for i in whole_ids] + [{'show': i} for i in ruin_ids],
         'notes': "set:alamar: the whole castle until m33.done, then the ruin (xahullbn, fallen towers, dark fields) "
                  "with FD-01's stair in the broken gatehouse's floor."},
        {'id': 'evt:alamar_hum', 'trigger': 'load', 'condition': {'qbit': 'alamar_destroyed'},
         'effects': [{'lua': 'evt.SetMapVar("AmbientSound%d", 2)' % HUM_KEY}],
         'else_effects': [{'lua': 'evt.SetMapVar("AmbientSound%d", 1)' % HUM_KEY}],
         'notes': "AU: sound:alamar_hum off after m33.done (its map variable AmbientSound<key>, D1's pattern)."},
        {'id': 'evt:crust', 'trigger': 'load', 'condition': {'qbit': 'lava_cooled'},
         'effects': [{'show': 'thing:pod_crust'}],
         'notes': "set:pod_lava (D-49 Q4): the crust over the lava round the hatch on lava_cooled (111564)."},
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
    WASTE = [[25, 25], [64, 25], [64, 31], [60, 34], [51, 31], [42, 34], [35, 40], [34, 50], [39, 58], [35, 62],
             [25, 62]]
    CINDER = [[25, 63], [36, 63], [40, 59], [46, 63], [52, 66], [56, 74], [59, 80], [55, 88], [44, 89], [25, 89]]
    FIELD = [[65, 25], [108, 25], [108, 55], [100, 57], [88, 57], [80, 55], [70, 52], [66, 50], [66, 42], [61, 34],
             [65, 31]]
    PEAKS = [[25, 90], [58, 90], [60, 92], [60, 108], [25, 108]]
    PEAKS_E = [[70, 92], [100, 92], [108, 90], [108, 108], [70, 108]]
    FLATS = [[57, 75], [64, 80], [74, 79], [81, 76], [81, 90], [70, 91], [59, 91], [60, 81]]
    for sid, poly, n in (('waste', WASTE, 40), ('cinder', CINDER, 40), ('field', FIELD, 50), ('peaks_w', PEAKS, 40),
                         ('peaks_e', PEAKS_E, 40), ('flats', FLATS, 14)):
        sc('scatter:rocks_%s' % sid, '6rock07', n, poly, clusters=max(4, n // 4), steep=True)
        sc('scatter:stones_%s' % sid, 'rock16', n // 2, poly, clusters=max(3, n // 6))
    for sid, poly, n in (('waste', WASTE, 10), ('cinder', CINDER, 10), ('flats', FLATS, 6)):
        sc('scatter:dead_trees_%s' % sid, 'swptree4', n, poly, clusters=max(2, n // 3))
    ground = [
        {'material': 'wasteland', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'Grey ash and cooled flows: the waste, the cinder plains, the flats, the field.'},
        {'material': 'dirt', 'steeper_than': 560, 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'Bare black rock on the steep slopes (the peaks, the mesa, the rims).'},
        {'material': 'dirt', 'polygon': [[82, 74], [100, 74], [100, 90], [82, 90]],
         'notes': "Necropolis's trodden yards."},
    ]
    for line in PATHS:
        ground.append({'material': 'dirt', 'line': line, 'width': 1, 'notes': 'a track'})
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('D6 The Forbidden Zone, written by output/studio_cal/d6/tools/gen.py. Cells [x, y], x east, y '
                  "south. Heights above the stars below the rims (0): Corak's lava lake 1,450, Alamar's moat 1,550 "
                  "and its mesa 2,304, the waste 1,600-2,100, the Ancient field to 2,700, Necropolis 1,664, the "
                  'border pass 1,700, the southern peaks to 3,800 with Griffin Pass 2,464. Lava is lavtyl (D-40).'),
        'frame': frame, 'heights': heights, 'water': water, 'roads': roads, 'districts': districts,
        'points': points, 'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground,
        'structures': structures, 'actors': actors + V.sketch_actors('D6'), 'events': events,
        'relations': V.relations('D6'),
    }
    atmosphere = {'format': 0, 'sky': 'xeendark1', 'weather': {}, 'ash': 40, 'view_distance': 1.8,
                  'notes': ("Darkside's amber day (xeendark1; A3's Lua sets the sun's stage on load). Ash fall on 40 % "
                            "of days (D-40 (9), A1's word). view_distance 1.8: Castle Alamar reads at 20,700 in the "
                            "signature view and about 26,500 from Griffin Pass (D-49 change 10, as D-36's Blackfang); "
                            "the distance is tuned, never the castle's place.")}

    def half(v):
        return round(v * 2) / 2.0
    for r in roads:
        r['line'] = [[half(a), half(b)] for a, b in r['line']]
    for g in ground:
        if 'line' in g:
            g['line'] = [[half(a), half(b)] for a, b in g['line']]
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
    for st in structures:
        if st.get('kind') == 'building':
            t = st.setdefault('textures', {})
            w = t.get('wall') or ((st.get('parts') or [{}])[0].get('textures') or {}).get('wall') or 't09a01'
            t.setdefault('post_left', w)
            t.setdefault('post_right', w)
    missing = sorted(set(HOOKS) - USED)
    if missing:
        raise SystemExit('hooks with map D6 not wired: %s' % missing)
    # AU's beds (none written for D6 yet): level_generation/projects/xeen/common/beds/xeen_d6.yml when it exists
    if bed_sounds:
        sketch['sounds'] = bed_sounds

    def dump(folder, name, data):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)
    # F2 (2026-11-21): wing door pictures (t06a03/t06b03, t09a03a) hung as double doors, never alone
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    import house_doors as HD
    for _note in HD.double_doors_sketch(sketch) + HD.bury_mouths_sketch(sketch) + HD.blind_mouths_sketch(sketch):
        print('door:', _note)   # F8 too: cave mouths as wide as their rim, no dark mouth that leads nowhere
    import entrance_screens as ES     # F16/D-90 (s32): each dungeon door's trans.txt row in its entrance window
    print('entrance screens:', ES.apply_sketch(sketch, 'xeen_d6'))
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
    print('AMBROSE_ROW_LIVE', AMBROSE_ROW_LIVE, 'D1_LIVE', D1_LIVE, 'D5_LIVE', D5_LIVE, 'lavafall', LAVAFALL_LIVE, 'lamp', LAMP,
          'dungeons live', sorted(k for k, v in DUNGEON.items() if v))
    print('hatch', [round(v, 2) for v in HATCH], 'way out', [round(v, 2) for v in HATCH_OUT],
          'world', W(*HATCH_OUT))


# ---------------------------------------------------------------------------------------------------------------
# Castle Alamar (Ancient kit), whole and ruin; the pylons; FD-01's stair; the travel pyramid
# ---------------------------------------------------------------------------------------------------------------
ALAMAR_TEX = {'wall': 'swll4dk', 'window': 'xaenergy', 'trim': 'gn_mtl03', 'roof': 'gn_mtl03', 'door': 'swdoora',
              'post_left': 'swll4dk', 'post_right': 'swll4dk', 'gable': 'swll4dk', 'ridge': 'gn_mtl03',
              'band': 'gn_mtl03'}
RUIN_TEX = {'wall': 'xahullbn', 'window': 'xahullbn', 'trim': 'xahullbn', 'roof': 'xahullbn',
            'post_left': 'xahullbn', 'post_right': 'xahullbn'}
_IDS = {'whole': [], 'ruin': []}


def alamar_ids():
    return list(_IDS['whole']), list(_IDS['ruin'])


def square_tower(tid, at, size, storeys, ruin=False):
    """A square tower of xahull plating, `storeys` of 256, one lit xaenergy panel in each face's middle bay a storey
    (texture fit: once per storey face); flat gn_mtl roof. The ruin: xahullbn stubs of uneven height."""
    n = size // 128
    parts = []
    for k in range(storeys):
        off = 0 if k % 2 else (1 if n > 2 else 0)
        walls = {s: bays(n, n // 2 - off) for s in ('n', 's', 'e', 'w')}
        p = {'id': 'storey_%d' % (k + 1), 'at': [64, 64], 'size': [size, size], 'wall_height': 256,
             'roof': 'none', 'walls': walls}
        if k:
            p['bottom'] = 256 * k
        parts.append(p)
    parts.append({'id': 'crown', 'at': [64, 64], 'size': [size, size], 'bottom': 256 * storeys, 'wall_height': 256,
                  'roof': 'flat', 'windows': 'none', 'textures': {'wall': 'xahull', 'roof': 'gn_mtl03'}})
    st = {'id': tid, 'kind': 'building', 'at': [round(at[0] - (size + 128) / 1024, 3),
                                                round(at[1] - (size + 128) / 1024, 3)],
          'size': [(size + 128) / 512, (size + 128) / 512], 'kit': 'grey', 'door': 'none', 'floor': MESA_TOP,
          'title': 'Castle Alamar', 'textures': dict(ALAMAR_TEX), 'parts': parts}
    if ruin:
        st['textures'] = dict(RUIN_TEX)
        st['parts'] = [{'id': 'stub', 'at': [64, 64], 'size': [size, size], 'wall_height': 256 * max(2, storeys // 2),
                        'roof': 'none', 'windows': 'none'}]
        st['ruin'] = {'height': [128, 256 * max(2, storeys // 2)], 'gaps': 0.3, 'thickness': 64, 'seed': len(tid)}
        st['hidden'] = True
        _IDS['ruin'].append(tid)
    else:
        _IDS['whole'].append(tid)
    return st


def alamar(S):
    x0, y0, x1, y1 = CASTLE_BOX
    gx0, gy0, gx1, gy1 = GATEHOUSE
    # the curtain wall of plating (two stretches each side of the gatehouse on the south)
    wall_tex = {'wall': 'swll4dk', 'top': 'gn_mtl03'}
    # F19 (the user 2026-11-22, wall pieces meet flush): the ring's ends run 0.25 into the gatehouse (they stopped
    # at its plot's edge, 64 short of its body: a slit each side)
    lines = {'ring': [[gx0 + 0.25, y1], [x0, y1], [x0, y0], [x1, y0], [x1, y1], [gx1 - 0.25, y1]]}
    for key, line in lines.items():
        S({'id': 'thing:alamar_wall_%s' % key, 'kind': 'wall', 'line': line, 'height': 768, 'thickness': 128,
           'textures': dict(wall_tex), 'title': 'Castle Alamar'})
        _IDS['whole'].append('thing:alamar_wall_%s' % key)
        S({'id': 'thing:alamar_ruin_wall_%s' % key, 'kind': 'wall', 'line': line, 'height': 384, 'thickness': 128,
           'textures': {'wall': 'xahullbn', 'top': 'xahullbn'}, 'title': 'The ruin of Castle Alamar',
           'hidden': True})
        _IDS['ruin'].append('thing:alamar_ruin_wall_%s' % key)
    for k, (u, v) in (('nw', (x0, y0)), ('ne', (x1, y0)), ('sw', (x0, y1)), ('se', (x1, y1))):
        S(square_tower('thing:alamar_tower_%s' % k, (u, v), 768, 7))
        S(square_tower('thing:alamar_ruin_tower_%s' % k, (u, v), 768, 7, ruin=True))
    # the keep: 1,536 square, nine storeys, a panel a storey face
    S(square_tower('thing:alamar_keep', (51.0, 45.5), 1536, 9))
    S(square_tower('thing:alamar_ruin_keep', (51.0, 45.5), 1536, 9, ruin=True))
    # the gatehouse: a block over the gate, the gate a hinged pair of shipped Control Center leaves (swdoora, the
    # second mirrored), m33.castle_door; sealed until DD-17 exists
    gate_effects = hook('m33.castle_door')
    gh = {'id': 'thing:alamar_gatehouse', 'kind': 'building', 'at': [gx0, gy0], 'size': [gx1 - gx0, gy1 - gy0],
          'kit': 'grey', 'facing': 's', 'floor': MESA_TOP, 'title': "Castle Alamar's gate",
          'textures': dict(ALAMAR_TEX),
          'parts': [{'id': 'gate', 'at': [64, 64], 'size': [1408, 1408], 'wall_height': 768, 'roof': 'none',
                     'windows': 'none', 'door_height': 256,
                     'walls': {'s': [['wall', 448], ['door', 512], ['wall', 448]]}},
                    {'id': 'crown', 'at': [64, 64], 'size': [1408, 1408], 'bottom': 768, 'wall_height': 256,
                     'roof': 'flat', 'windows': 'none', 'textures': {'wall': 'xahull', 'roof': 'gn_mtl03'}}],
          'door': {'part': 'gate', 'wall': 's', 'leaves': 2},
          'notes': "DD-17 Castle Alamar (A8): m33.castle_door's question; DD-17's arrival hook refuses a party "
                   "without the Soul Box and moves it back to entrance:dd17_gate."}
    if DUNGEON['dd17']:
        # A3's m33.castle_door is a message ending "Enter?": shown before a move it never asks. Session 18: its text is
        # the question (read from the quest file, so A3's wording flows in on a rebuild); Yes moves. Session 24 (D-72
        # rule 3): one Yes/No button prompt whose own text is that line, no SetMessage before it.
        use('m33.castle_door')
        # s32 (F16, D-89, A3/A8's request): no Yes/No (the entrance window asks, trans row 5049); the Soul Box is
        # checked here, before the move (DD-17 no longer throws a party out on arrival): without it m33.arrival's
        # refusal on the status line and no move. A3's `m33.arrival_gate` hook replaces the `can` when it exists.
        _arr = yaml.safe_load(open(os.path.join(WORLD, 'source/quests/m33.yml')))['hooks']
        gh['lua_before'] = ('if not %s then return end' % hcall('m33.arrival_gate') if 'arrival_gate' in _arr else
                            'if not XeenQuests.can("m33.arrival") then evt.StatusText(%s) return end'
                            % lstr(_arr['arrival']['fail_text']))
        gh['into'] = {'map': 'xeen_dd17.blv', 'arrival': ENTRANCE['dd17']}
    else:
        gh['effects'] = gate_effects + [{'text': 'The gate does not move. %s' % SEALED}]
    S(gh)
    _IDS['whole'].append('thing:alamar_gatehouse')
    S({'id': 'thing:alamar_ruin_gatehouse', 'kind': 'building', 'at': [gx0, gy0], 'size': [gx1 - gx0, gy1 - gy0],
       'kit': 'grey', 'door': 'none', 'floor': MESA_TOP, 'title': "Castle Alamar's broken gatehouse",
       'textures': dict(RUIN_TEX), 'hidden': True,
       'ruin': {'height': [96, 640], 'gaps': 0.45, 'thickness': 96, 'seed': 9},
       'parts': [{'id': 'gate', 'at': [64, 64], 'size': [1408, 1408], 'wall_height': 640, 'roof': 'none',
                  'windows': 'none'}]})
    _IDS['ruin'].append('thing:alamar_ruin_gatehouse')
    # FD-01's stair in the broken gatehouse's floor (D-49 Q5): ruin state only, m39.depths_door, sealed until FD-01
    stair = {'id': 'thing:fd01_stair', 'kind': 'hatch', 'form': 'pit', 'at': [51.0, 52.0], 'height': 48,
             'size': [512, 512], 'textures': {'wall': 'xahullbn', 'door': 'gn_mtl03'}, 'hidden': True,
             'title': 'A stair under the ruin', 'hint': 'A stair under the ruin',
             'condition': {'lua': hcall('m39.depths_door')}}
    if DUNGEON['fd01']:
        stair['into'] = {'map': 'xeen_fd01.blv', 'arrival': ENTRANCE['fd01']}
    else:
        stair['effects'] = [{'text': 'The stair goes down into the dark under the ruin. %s' % SEALED}]
    S(stair)
    _IDS['ruin'].append('thing:fd01_stair')
    # the four energy pylons on the approach ramp only (D-49 change 10), the conduit once per pylon face, xafield
    # curtains between the two pylons of each side (along the ramp, never across it)
    for i, (u, v) in enumerate(PYLONS):
        tid = 'thing:alamar_pylon_%d' % (i + 1)
        S({'id': tid, 'kind': 'building', 'at': [round(u - 0.375, 3), round(v - 0.375, 3)], 'size': [0.75, 0.75],
           'kit': 'grey', 'door': 'none', 'title': 'An energy pylon',
           'textures': {'wall': 'xaenergy', 'roof': 'gn_mtl03', 'trim': 'gn_mtl03', 'window': 'xaenergy'},
           'parts': [{'id': 'pylon', 'at': [128, 128], 'size': [128, 128], 'wall_height': 256, 'roof': 'flat',
                      'windows': 'none'},
                     {'id': 'cap', 'at': [96, 96], 'size': [192, 192], 'bottom': 256, 'wall_height': 64,
                      'roof': 'flat', 'windows': 'none', 'textures': {'wall': 'gn_mtl03', 'roof': 'gn_mtl03'}}]})
    for side, (a, b) in (('w', (PYLONS[0], PYLONS[2])), ('e', (PYLONS[1], PYLONS[3]))):
        fid = 'thing:alamar_field_%s' % side
        # F19: the field runs into both pylons' bodies (it stopped 40 short of them)
        S({'id': fid, 'kind': 'wall', 'line': [[a[0], a[1] + 0.1], [b[0], b[1] - 0.1]], 'height': 256,
           'thickness': 32, 'textures': {'wall': 'xafield', 'top': 'xafield'}, 'title': 'An energy field'})
        _IDS['whole'].append(fid)
    # D-50 Q9: the working travel pyramid outside the moat (Ancient cladding), its click Xeen.travelPyramid
    px, py = PYRAMID
    S({'id': 'thing:travel_pyramid', 'kind': 'building', 'at': [px - 1.25, py - 1.25], 'size': [2.5, 2.5],
       'kit': 'stone', 'title': 'Travel Pyramid', 'door': 'none', 'floor': 1856,
       'textures': {'wall': 'gn_mtl03', 'roof': 'gn_mtl02', 'trim': 'gn_mtl03'},
       'parts': [{'id': 'p', 'at': [256, 256], 'size': [768, 768], 'wall_height': 64, 'roof': 'hip',
                  'roof_pitch': 50, 'windows': 'none', 'title': 'Travel Pyramid',
                  'effects': [{'lua': 'Xeen.travelPyramid("alamar_gate")'}]},
                 {'id': 'cap', 'at': [576, 576], 'size': [128, 128], 'bottom': 400, 'wall_height': 128,
                  'roof': 'hip', 'roof_pitch': 60, 'windows': 'none', 'title': 'Travel Pyramid',
                  'textures': {'wall': 'xaenergy', 'roof': 'xaenergy'},
                  'effects': [{'lua': 'Xeen.travelPyramid("alamar_gate")'}]}],
       'notes': "D-50 Q9: Xeen.travelPyramid('alamar_gate') reads m30.done and sets the party down in XD-17 "
                "(PyramidArrivals.shangrila, A3); XD-17's pyramid lands at entrance:xd17_pyramid."})


# ---------------------------------------------------------------------------------------------------------------
# The pods, the crust, the lava falls
# ---------------------------------------------------------------------------------------------------------------
def pod(pid, at, floor, title, door_effects=None, into=None, condition=None, hull='xahullbn', turn=0, band='xahullbn'):
    r = POD_R
    c = [r + 320, r + 320]
    parts = [{'id': 'skirt', 'shape': 'round', 'at': c, 'radius': r, 'sides': 12, 'wall_height': 96,
              'roof': 'none', 'windows': 'none'},
             {'id': 'hull', 'shape': 'round', 'at': c, 'radius': r, 'sides': 12, 'bottom': 96,
              'wall_height': 1024, 'roof': 'none', 'windows': 'none', 'door_height': 256,
              'walls': {'0': [['wall', 37], ['door', 256], ['wall', 38]]}},
             {'id': 'band', 'shape': 'round', 'at': c, 'radius': r, 'sides': 12, 'bottom': 1120, 'wall_height': 256,
              'roof': 'none', 'windows': 'none', 'textures': {'wall': band}}]
    # the nose: rings narrowing to a point (an ogive, no eaves)
    z = 1376
    for k, (rr, hh) in enumerate(((576, 192), (480, 160), (352, 128), (208, 96))):
        parts.append({'id': 'nose_%d' % (k + 1), 'shape': 'round', 'at': c, 'radius': rr, 'sides': 12, 'bottom': z,
                      'wall_height': hh, 'roof': 'cone' if k == 3 else 'flat', 'roof_pitch': 60, 'eaves': 0,
                      'windows': 'none', 'textures': {'wall': 'gn_mtl03', 'roof': 'gn_mtl03'}})
        z += hh
    # four fins at the foot, between the hatch's bearings
    for k, (fx, fy, fw, fd) in enumerate(((c[0] - 48, c[1] - r - 256, 96, 288), (c[0] - 48, c[1] + r - 32, 96, 288),
                                          (c[0] - r - 256, c[1] - 48, 288, 96), (c[0] + r - 32, c[1] - 48, 288, 96))):
        if k == 1:
            continue          # the hatch's side (south before the turn) stays clear
        parts.append({'id': 'fin_%d' % (k + 1), 'at': [fx, fy], 'size': [fw, fd], 'wall_height': 640,
                      'roof': 'flat', 'windows': 'none', 'textures': {'wall': 'gn_mtl03', 'roof': 'gn_mtl03'}})
    size = (2 * r + 640) / 512
    b = {'id': pid, 'kind': 'building', 'at': [round(at[0] - size / 2, 3), round(at[1] - size / 2, 3)],
         'size': [size, size], 'kit': 'grey', 'facing': 's', 'floor': floor, 'title': title, 'turn': turn,
         'textures': {'wall': hull, 'roof': 'gn_mtl03', 'trim': 'gn_mtl03', 'door': 'a2c', 'window': hull,
                      'post_left': hull, 'post_right': hull},
         'parts': parts, 'door': {'part': 'hull', 'wall': '0'}}
    if condition:
        b['condition'] = condition
    if into:
        b['into'] = into
    if door_effects:
        b['effects'] = door_effects
    return b


def pods(S):
    # Corak's pod nose-up in the lava, its round hatch (one leaf, a2c) toward the south-east tongue (turn -45)
    corak = pod('thing:corak_pod', POD, LAKE_LEVEL - 64, "Escape Pod 1", turn=-45,
                condition={'lua': hcall('m29.pod_door')},
                into={'map': 'xeen_dd16.blv', 'arrival': ENTRANCE['dd16']} if DUNGEON['dd16'] else None,
                door_effects=None if DUNGEON['dd16'] else [{'text': 'The hatch will not open. %s' % SEALED}])
    corak['notes'] = ("DD-16 Corak's Pod (A7): m29.pod_door (lava_cooled) into entrance:d6_hatch; DD-16's way out "
                      "lands at entrance:dd16_hatch on the crust 384 before the hatch, facing south-east.")
    S(corak)
    # the crust (D-49 Q4): a pier of cooled black rock over the lava from the hatch to the tongue, shown on
    # lava_cooled (MM8's volcanic floor voltyl, X7's cooled flow; MM6's vlcwl1lg sides)
    a = (HATCH[0] - HATCH_DIR[0] * 0.15, HATCH[1] - HATCH_DIR[1] * 0.15)
    b = (74.6, 69.9)
    S({'id': 'thing:pod_crust', 'kind': 'bridge', 'line': [[round(a[0], 3), round(a[1], 3)], [b[0], b[1]]],
       'width': 768, 'height': CRUST_H, 'piers': 0, 'kerb': 0, 'hidden': True,
       'textures': {'deck': 'voltyl', 'side': 'vlcwl1lg'}, 'title': 'Black crust',
       'notes': "set:pod_lava: shown on lava_cooled (evt:crust)."})
    # Sheltem's pod upright in its crater (DD-22, D-62 Q52): A3's d6.sheltem_hatch (sealed before m33.done; after it
    # the status line) into DD-22's entrance:d6_hatch once DD-22 is installed
    if DUNGEON['dd22']:
        sheltem = pod('thing:sheltem_pod', SHELTEM, 1920, 'Escape Pod 2', hull='gn_mtl02', band='xahull',
                      condition={'lua': hcall('d6.sheltem_hatch')},
                      into={'map': 'xeen_dd22.blv', 'arrival': ENTRANCE['dd22']})
        sheltem['notes'] = ("DD-22 Sheltem's Pod (A8): d6.sheltem_hatch (m33.done) into entrance:d6_hatch; DD-22's way "
                            "out lands at entrance:dd22_hatch before the hatch, facing south.")
    else:
        sheltem = pod('thing:sheltem_pod', SHELTEM, 1920, 'Escape Pod 2', hull='gn_mtl02', band='xahull',
                      door_effects=hook('d6.sheltem_hatch'))
    S(sheltem)
    if LAVAFALL_LIVE:
        for i, (at, turn) in enumerate((((44.0, 24.3), 0), ((24.3, 51.0), -90))):
            S(deco('thing:lavafall_%d' % (i + 1), 'xeen_lavafall', at, turn=turn,
                   notes="Lane S's lava fall (as X7's) where the lava pours over the rim into the stars."))


# ---------------------------------------------------------------------------------------------------------------
# Necropolis: walls, the gate (two leaves out, two in), the square, the mirror, the skull, the books, the barrel,
# DD-21's crypt stair
# ---------------------------------------------------------------------------------------------------------------
NP_WALL_H = 704


def necropolis(S):
    wt = {'wall': 't09a01', 'top': 't09a02a'}
    gx, gy = NP_GATE
    for key, line in (('w', [[gx - 1.2, 74], [82, 74], [82, 90], [91, 90]]),
                      ('e', [[gx + 1.2, 74], [100, 74], [100, 90], [91, 90]])):
        S({'id': 'thing:np_wall_%s' % key, 'kind': 'wall', 'line': line, 'height': NP_WALL_H, 'thickness': 192,
           'battlements': True, 'textures': dict(wt), 'title': "Necropolis's walls"})
    for k, (u, v) in (('nw', (82, 74)), ('ne', (100, 74)), ('sw', (82, 90)), ('se', (100, 90))):
        S({'id': 'thing:np_tower_%s' % k, 'kind': 'building', 'at': [u - 0.875, v - 0.875], 'size': [1.75, 1.75],
           'kit': 'grey', 'door': 'none', 'floor': TOWN_H, 'title': "Necropolis's walls",
           'textures': {'wall': 't09a01', 'roof': 't09a02a', 'trim': 't09b11b'},
           'parts': [{'id': 'tower', 'at': [64, 64], 'size': [768, 768], 'wall_height': 960, 'roof': 'flat',
                      'battlements': True, 'windows': 'none'}]})
    # the gatehouse: two towers either side of the passage, an arch over it, the crest (xnpgate) once over the gate
    S({'id': 'thing:np_gatehouse', 'kind': 'building', 'at': [gx - 2.2, gy - 0.8], 'size': [4.4, 1.6],
       'kit': 'grey', 'door': 'none', 'floor': TOWN_H, 'title': "Necropolis's gate",
       'textures': {'wall': 't09a01', 'roof': 't09a02a', 'trim': 't09b11b', 'window': 'xnpgate'},
       'parts': [{'id': 'tower_w', 'at': [0, 0], 'size': [768, 768], 'wall_height': 1024, 'roof': 'flat',
                  'battlements': True, 'windows': 'none'},
                 {'id': 'tower_e', 'at': [1484, 0], 'size': [768, 768], 'wall_height': 1024, 'roof': 'flat',
                  'battlements': True, 'windows': 'none'},
                 {'id': 'arch', 'at': [768, 128], 'size': [716, 512], 'bottom': 448, 'wall_height': 384,
                  'roof': 'flat', 'battlements': True, 'windows': 'none'},
                 {'id': 'crest', 'at': [1062, 112], 'size': [128, 32], 'bottom': 544, 'wall_height': 128,
                  'roof': 'flat', 'walls': {'n': ['window'], 's': ['wall']}}]})
    # the leaves: chb1dl / chb1dr (iron-bound, one wing each), 192 x 384, an outer pair asking d6.necropolis_gate and
    # an inner pair always open from inside (D-49 change 8); either hides all four
    # the gate: a 384 x 384 opening in a wall across the passage; outside and inside it a pair of iron-bound leaves
    # (chb1dl, the second mirrored, 192 each: the studio lays a door picture once over its leaf); the outer pair asks
    # d6.necropolis_gate (item 12336; else A3's refusal), the inner pair is always open (D-49 change 8); either opens
    # (hides) both pairs
    S({'id': 'thing:np_gate_wall', 'kind': 'wall', 'line': [[gx - 0.7, gy], [gx + 0.7, gy]], 'height': 448,
       'thickness': 64, 'textures': dict(wt), 'title': "Necropolis's gate",
       'gates': [{'at': [gx, gy], 'width': 384, 'height': 384}]})
    ids = ('thing:np_gate_outer', 'thing:np_gate_inner')
    for gid, off, wall in ((ids[0], -0.16, 'n'), (ids[1], 0.16, 's')):
        g = {'id': gid, 'kind': 'building', 'at': [round(gx - 0.375, 3), round(gy + off - 0.03125, 4)],
             'size': [0.75, 0.0625], 'kit': 'grey', 'floor': TOWN_H, 'title': "Necropolis's gate",
             'textures': {'wall': 't09b11b', 'door': 'chb1dl', 'roof': 't09b11b', 'trim': 't09b11b',
                          'post_left': 't09b11b', 'post_right': 't09b11b'},
             'parts': [{'id': 'leaves', 'at': [0, 0], 'size': [384, 32], 'wall_height': 384, 'roof': 'flat',
                        'windows': 'none', 'door_height': 384, 'walls': {wall: [['door', 384]]}}],
             'door': {'part': 'leaves', 'wall': wall, 'leaves': 2},
             'effects': [{'hide': ids[0]}, {'hide': ids[1]}]}
        if gid == ids[0]:
            g['condition'] = {'lua': hcall('d6.necropolis_gate')}
        S(g)
    # the square: paving, the mirror (A4's thing:np_mirror, 4756) on its plinth with the talking skull (one spot)
    S({'id': 'thing:np_square_paving', 'kind': 'platform', 'at': [91.5, 78.5], 'size': [3584, 3072], 'height': 8,
       'textures': {'top': 't09a02a', 'wall': 't09a02a'}, 'title': 'The Square of Mourning'})
    S({'id': 'thing:np_mirror', 'kind': 'portal', 'at': list(MIRROR), 'radius': 112, 'sides': 12, 'turn': 0,
       'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'The Mirror of Necropolis',
       'effects': [{'lua': 'Xeen.useMirror(%d, eventId, continueStep)' % HOUSE_MIRROR}],
       'notes': "A4's 4756 (qbit 119011, arrival necropolis_gate)."})
    S(deco('thing:np_skull', '7dec20', (MIRROR[0] + 0.5, MIRROR[1] + 0.3), title='A skull on the plinth',
           effects=hook('d6.skull')))
    # the Books of the Dead: three lecterns at the square's west edge, the book (xnpbook) once on each top
    for i in range(3):
        y = 78.0 + i * 1.0
        S({'id': 'thing:np_book_%d' % (i + 1), 'kind': 'building', 'at': [88.55, round(y - 0.15, 3)],
           'size': [0.3, 0.3], 'kit': 'grey', 'door': 'none', 'floor': TOWN_H + 8,
           'title': 'A Book of the Dead',
           'parts': [{'id': 'lectern', 'at': [12, 12], 'size': [128, 128], 'wall_height': 128, 'roof': 'flat',
                      'windows': 'none', 'textures': {'wall': 't09b11b', 'roof': 'xnpbook'},
                      'title': 'A Book of the Dead', 'effects': hook('d6.book_dead_%d' % (i + 1))}]})
    # the Warm Barrel's barrel beside (never before) its door
    S(deco('thing:np_barrel', 'bigbarel', (87.25, 82.6), title='A barrel',
           effects=[msg('Food for the dead, keep warm.')]))
    # DD-21's crypt stair head in the south-east corner: two grille leaves (gkp103a / gkp103b)
    cx, cy = CRYPT
    crypt = {'id': 'thing:dd21_crypt', 'kind': 'building', 'at': [cx - 0.75, cy - 0.5], 'size': [1.5, 1.25],
             'kit': 'grey', 'facing': 'n', 'floor': TOWN_H, 'title': 'A crypt stair',
             'textures': {'wall': 'twb2', 'roof': 'twb1', 'trim': 'twb1', 'door': 'gkp103a', 'window': 'twb2',
                          'post_left': 'twb2', 'post_right': 'twb2'},
             'parts': [{'id': 'crypt', 'at': [64, 64], 'size': [640, 512], 'wall_height': 384, 'roof': 'flat',
                        'windows': 'none', 'door_height': 256,
                        'walls': {'n': [['wall', 192], ['door', 256], ['wall', 192]]}}],
             'door': {'part': 'crypt', 'wall': 'n', 'leaves': 2}}
    if DUNGEON['dd21']:
        crypt['into'] = {'map': 'xeen_dd21.blv', 'arrival': ENTRANCE['dd21']}
    else:
        crypt['effects'] = [{'text': 'Behind the grilles a stair goes down into the sewers. %s' % SEALED}]
    S(crypt)
    # props by walls in pairs (the lane's dressing rule): barrels at the tavern's and the market's back walls
    for i, at in enumerate(((84.25, 82.6), (84.25, 82.95), (98.05, 77.0), (98.05, 77.35))):
        S(deco('thing:np_prop_%d' % (i + 1), 'bigbarel', at))


# ---------------------------------------------------------------------------------------------------------------
# The wilds: the pass, the archers, the mines, the field, the waste
# ---------------------------------------------------------------------------------------------------------------
def tent(tid, at, facing, floor, title, hide=False):
    w, r = ('tentwal1', 'tentrf1')     # plain grey canvas (xohide is a picture meant once)
    return {'id': tid, 'kind': 'building', 'at': list(at), 'size': [1.4, 1.4], 'kit': 'grey', 'door': 'none',
            'facing': facing, 'floor': floor, 'title': title,
            'textures': {'wall': w, 'gable': w, 'roof': r, 'trim': w, 'ridge': w, 'post_left': w, 'post_right': w,
                         'window': w, 'door': w},
            'parts': [{'id': 'tent', 'at': [80, 80], 'size': [556, 556], 'wall_height': 128, 'roof': 'gable',
                       'roof_pitch': 58, 'windows': 'none'}]}


def lamp(lid, at, key, **kw):
    use('q-d27.%s' % key)
    use('q-d27.greed')
    use('q-d27.share')
    return deco(lid, LAMP, at, title="A genie's lamp",
                effects=[{'lua': 'Xeen.genieLamp("%s", eventId, continueStep)' % key}], **kw)


def wilds(S):
    # Griffin Pass: Ambrose's tent and the fire (they stay after m25.done)
    S(tent('thing:ambrose_tent', (58.9, 93.6), 'e', PASS_H, "Ambrose's tent"))
    S(deco('thing:ambrose_fire', 'cmpfyr00', (60.6, 96.2), title='A camp fire'))
    # the obelisk, the hot spring's fountain and the pilgrim's pack
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': list(OBELISK), 'height': 768, 'title': 'Obelisk',
       'textures': {'wall': 'vlcwl1lg'}, 'effects': hook('obelisks.d6')})
    S({'id': 'thing:resilience_fountain', 'kind': 'fountain', 'at': [30.4, 30.4],
       'title': 'Fountain of Super Resilience', 'tiers': [[64, 24]], 'textures': {'wall': 'vlcwl1lg'},
       **daily('d6_resilience_fountain', [{'add': {'var': 'HP', 'value': 100}},
                                          {'text': 'The water is hot and tastes of iron. +100 Hit points'}],
               'The spring has gone still. Come back tomorrow.')})
    S({'id': 'thing:spring_pilgrim', 'kind': 'chest', 'at': [32.0, 32.0], 'title': "A burned pilgrim's pack",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:spring_bones', 'dec05', (32.5, 32.4)))
    # the genie lamps (Q-D27): the basalt pinnacle, the islet, the crag
    S({'id': 'thing:pinnacle', 'kind': 'platform', 'at': [36.0, 40.0], 'size': [384, 384], 'height': 96,
       'textures': {'top': 'vlcwl1lg', 'wall': 'vlcwl1lg'}, 'title': 'A basalt pinnacle'})
    S(lamp('thing:lamp_pinnacle', (36.0, 40.0), 'd6_pinnacle', **{'raise': 96}))
    S(lamp('thing:lamp_islet', (66.0, 63.0), 'd6_islet'))
    S(lamp('thing:lamp_crag', (88.0, 101.0), 'd6_crag'))
    # the archers' camp: tents, a fire, the strongbox and the burn question on its spot (D-49 change 5)
    for i, (at, f) in enumerate((((32.0, 84.6), 's'), ((36.6, 84.4), 's'), ((32.4, 87.0), 'e'))):
        S(tent('thing:archer_tent_%d' % (i + 1), at, f, 1952, "A barbarian's tent", hide=True))
    S(deco('thing:archer_fire', 'cmpfyr00', (34.6, 86.2), title='A camp fire'))
    S({'id': 'thing:archers_chest', 'kind': 'chest', 'at': list(ARCHER_CHEST), 'title': "The archers' strongbox",
       'chest': {'level': 5, 'random_items': 3}})
    burn = ('if continueStep == 2 then %s return end if continueStep ~= nil then return end '
            'if Xeen.isSet("d6.archers_burned") then %s return end '
            'evt.AskQuestion(eventId, 1, 0, 2, "You have discovered a barbarian camp. Destroy? (Yes/No)", '
            '{"Yes", "Y"})' % (hcall('d6.archers_camp'), hcall('d6.archers_camp')))
    S(deco('thing:archers_standard', '7dec20', (ARCHER_CHEST[0] + 0.5, ARCHER_CHEST[1] - 0.2),
           title="The archers' standard", effects=[{'lua': burn}]))
    # the mines: DD-10C's adit (an open timbered mouth, no leaves), two boarded mouths, the prospector
    # `at` is the footprint's middle: the mouth centred in the timber frame (session 14; it stood a cell west of it), its
    # shell in the crag's cooled rock rather than the studio's default dirt.
    adit = {'id': 'thing:dd10c_adit', 'kind': 'cave_mouth', 'at': [ADIT[0], ADIT[1] - 0.5], 'size': [1024, 1024],
            'turn': 180, 'title': 'A mine adit', 'hint': 'A mine adit', 'textures': {'shell': 'vlcwl1lg'}}
    if DUNGEON['dd10c']:
        # the source's question (aaze0006:1) as one Yes/No button prompt with the adit's look (D-72 rule 3)
        # s32 (F16): no Yes/No; the entrance window with trans row 5040 (the adit's look) asks
        adit['into'] = {'map': 'xeen_dd10c.blv', 'arrival': ENTRANCE['dd10c']}
    else:
        adit['effects'] = [{'text': 'The timbers have come down twenty steps in. %s' % SEALED}]
    S(adit)
    S({'id': 'thing:adit_frame', 'kind': 'building', 'at': [ADIT[0] - 0.75, ADIT[1] - 1.6], 'size': [1.5, 0.5],
       'kit': 'grey', 'door': 'none', 'floor': 2688, 'title': 'A mine adit',
       'textures': {'wall': 't06a10', 'roof': 't06a10', 'trim': 't06a10'},
       'parts': [{'id': 'post_w', 'at': [96, 96], 'size': [64, 64], 'wall_height': 384, 'roof': 'flat',
                  'windows': 'none'},
                 {'id': 'post_e', 'at': [608, 96], 'size': [64, 64], 'wall_height': 384, 'roof': 'flat',
                  'windows': 'none'},
                 {'id': 'lintel', 'at': [64, 96], 'size': [640, 64], 'bottom': 384, 'wall_height': 64,
                  'roof': 'flat', 'windows': 'none'}]})
    for i, at in enumerate(((43.5, 97.0), (48.5, 97.0))):  # at the crag's foot (session 14; the crag starts at y 98)
        S({'id': 'thing:mine_mouth_%d' % (i + 1), 'kind': 'doorway', 'at': list(at), 'turn': 180, 'height': 256,
           'width': 192, 'depth': 128, 'textures': {'door': '7trimda', 'wall': 'vlcwl1lg'},
           'title': 'A boarded mine', 'effects': [{'text': 'Boarded up, and nailed twice.'}]})
    S({'id': 'thing:prospector', 'kind': 'chest', 'at': [40.0, 95.6], 'title': "A dead prospector's pack",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:prospector_bones', 'dec05', (40.5, 95.3)))
    # the east peaks: the griffin's nest, the broken travel pyramid (landmark, no click)
    S({'id': 'thing:griffin_nest', 'kind': 'chest', 'at': [76.0, 94.0], 'title': "A griffin's nest",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:nest_bones', '7dec18', (76.6, 94.4)))
    S({'id': 'thing:broken_pyramid', 'kind': 'building', 'at': [82.75, 96.75], 'size': [2.5, 2.5], 'kit': 'stone',
       'door': 'none', 'title': 'A broken pyramid', 'textures': {'wall': 'xahullbn', 'roof': 'xahullbn'},
       'ruin': {'height': [128, 640], 'gaps': 0.3, 'thickness': 96, 'seed': 3},
       'parts': [{'id': 'p', 'at': [128, 128], 'size': [1024, 1024], 'wall_height': 640, 'roof': 'none',
                  'windows': 'none'}]})
    # the Ancient field: the Well of Warding, the locker
    S({'id': 'thing:warding_well', 'kind': 'well', 'at': [101.0, 31.0], 'title': 'The Well of Warding',
       'frame': {'height': 224},
       **daily('d6_warding_well', [{'add': {'var': v, 'value': 20}} for v in
                                   ('FireResistanceBonus', 'AirResistanceBonus', 'WaterResistanceBonus',
                                    'EarthResistanceBonus')] +
                                  [{'text': '+20 Fire, Air, Water and Earth resistance until you rest.'}],
               'The well is dry today.')})
    S({'id': 'thing:ancient_locker', 'kind': 'chest', 'at': [88.0, 44.0], 'title': 'An Ancient locker',
       'chest': {'level': 5, 'random_items': 3}})
    # the Bone Road: the pilgrim's cart, the zone sign, the climbers' camp (dressing), the ridge tower
    S({'id': 'thing:pilgrim_cart', 'kind': 'chest', 'at': [86.0, 69.0], 'title': "A pilgrim's coffin-cart",
       'chest': {'level': 5, 'random_items': 2}})
    S(deco('thing:cart_wreck', 'dec24x', (86.7, 69.4)))
    S(sign('thing:zone_sign', (102.0, 65.2), 'The Forbidden Zone', effects=hook('d6.zone_sign')))
    S(tent('thing:climbers_tent', (99.3, 68.3), 's', 1792, 'An empty tent'))
    S({'id': 'thing:ridge_tower', 'kind': 'building', 'at': [103.0, 80.0], 'size': [2.0, 2.0], 'kit': 'grey',
       'door': 'none', 'title': 'A watchtower of the dead', 'textures': {'wall': 't09a01', 'trim': 't09a01'},
       'ruin': {'height': [256, 896], 'gaps': 0.25, 'thickness': 96, 'seed': 7},
       'parts': [{'id': 'tower', 'at': [128, 128], 'size': [768, 768], 'wall_height': 896, 'roof': 'none',
                  'windows': 'none'}]})
    # the cinder plains' landmarks (no click): the cinder cone's smoking vent by the Alamar road, a spar of Ancient
    # metal heaved up through the cinders, a wyrm's bones; a cairn at the north rim
    S({'id': 'thing:cinder_vent', 'kind': 'platform', 'at': [49.0, 80.0], 'size': [512, 512], 'height': 64,
       'textures': {'top': 'voltyl', 'wall': 'vlcwl1lg'}, 'title': 'A smoking vent'})
    S(deco('thing:cinder_smoke', 'cmpfyr00', (49.0, 80.0), title='A smoking vent', **{'raise': 64}))
    S({'id': 'thing:ancient_spar', 'kind': 'building', 'at': [37.5, 70.5], 'size': [1.5, 1.0], 'kit': 'grey',
       'door': 'none', 'turn': 25, 'title': 'A spar of Ancient metal', 'textures': {'wall': 'xahullbn',
                                                                                    'roof': 'gn_mtl03'},
       'parts': [{'id': 'spar', 'at': [64, 128], 'size': [640, 256], 'wall_height': 512, 'roof': 'lean_to',
                  'windows': 'none'}]})
    for i, (d, at) in enumerate((('7dec18', (27.0, 75.0)), ('dec05', (27.6, 75.4)), ('7dec18', (44.0, 74.0)),
                                 ('dec05', (44.5, 73.6)))):
        S(deco('thing:wyrm_bones_%d' % (i + 1), d, at, title="A wyrm's bones"))
    S(deco('thing:rim_cairn', 'searka01', (55.0, 27.0), title='A cairn at the rim'))
    # Ash Fork's signpost
    S({'id': 'thing:fork_signpost', 'kind': 'sign', 'at': [66.5, 85.5], 'height': 256,
       'arms': [{'title': 'Castle Alamar', 'toward': 'nw'}, {'title': 'Necropolis', 'toward': 'e'},
                {'title': 'Griffin Pass, Castleview', 'toward': 's'}]})
    if not D5_LIVE:
        S(sign('thing:east_road_end', (106.6, 64.6), 'Sign',
               'The road east to the Desert of Doom is closed by a rockfall. Turn back.'))


if __name__ == '__main__':
    build()
