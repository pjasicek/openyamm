#!/usr/bin/env python3
"""X5 Winterkill Tundra: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml) and the L2 and L3
briefs beside it (L1 is the approved mock-up of 2026-11-20 and stays as it is).

The design is the approved L1 (devdocs/xeen/briefs/x5/L1, board level_generation/xeen_art/phase2/x5/) with the
decider's changes: D-6.1 (the Frostspine carried south as a cliffed spur to the rim, no crossing; XD-10's south mouth
on its west face; no Thickbark bridge; the river open through the gorge and 1,000 past it; no barbarian marker near the
pass descent or the monastery foot; the crest broken into peaks with the pass notch at 1,700), D-6.3 (the frozen mere
and the frozen river below the gorge are land at 800 painted with the `ice` material), D-6.5 (the signature view at the
Waters of Great Magic, the Edge Watch, the glacier seen from the south track, Glom's fork and the Shrine of Cold) and
D-4 (XD-09's door and XD-10's north mouth near the east edge with only Act II monsters near them).
World: xeen. Houses: A4's source/towns/x5.yml. Hooks: A3's quest files (q-c6, q-c16, q-c18, m10). Rows: A2's.
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

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/x5'
OUT = os.path.join(BRIEFS, 'L4')
STEM = 'xeen_x5'
XEEN_SOURCE = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/worlds/xeen/source')
# X3 Lifeforce Lagoon (A5): X5's east edge leads to X3's west start once X3 is installed in the world; until then the
# lagoon road ends at a sign and X5 has no east start (an edge to a map that is not there cannot be travelled)
X3_LIVE = os.path.exists(os.path.join(XEEN_SOURCE, '../maps/xeen_x3.odm')) or os.environ.get('X5_X3_LIVE') == '1'
# X6 Desert of the Sphinx (A5): X5's north edge leads to X6's south start once X6 is installed (2026-11-20); X6's south
# edge lands on X5's north start on the steppe road (50, 20) = (-7168, 22528, 1280) facing south (1536)
X6_LIVE = os.path.exists(os.path.join(XEEN_SOURCE, '../maps/xeen_x6.odm')) or os.environ.get('X5_X6_LIVE') == '1'
NORTH_START = (50, 20)
XD23_LIVE = os.path.exists(os.path.join(XEEN_SOURCE, '../maps/xeen_xd23.blv')) or os.environ.get('X5_XD23_LIVE') == '1'
GONG_SOUNDS = ['xeen_gong', 'xeen_gong_low']   # AU (2026-11-20): the second of the northern pair is the low gong
GONG_Z = 992 + 16 + 160                        # Winterkill square: ground 992 (the build), paving 16, the board's middle 160
XD23_START = (0, -256, 0)           # A7's XD-23 start, facing south (1536); its exits land by explicit points
# XD-22 Ninja Pagoda (A7): live once its BLV is installed AND its map_stats row exists (the game loads no map
# without its row; A2's row was missing on 2026-11-20). Inside (0, -256, 0) facing south; its exit lands at (320, 9872,
# 1000) facing north (A7, by explicit point).
XD22_LIVE = ((os.path.exists(os.path.join(XEEN_SOURCE, '../maps/xeen_xd22.blv'))
              and 'Ninja Pagoda' in open(os.path.join(XEEN_SOURCE, '../data_tables/map_stats.txt')).read())
             or os.environ.get('X5_XD22_LIVE') == '1')
XD22_START = (0, -256, 0)
# FD-03 Darkstone Tower (A7, Act VI, D-57): live once its BLV is installed and its sidecar names entrance:x5_door; its
# exit lands at X5's entrance:fd03_door on the rock top (A6 s16: the whole cell (55, 59), beside entrance:p5_fall)
_FD03_SIDE = os.path.join(XEEN_SOURCE, '../maps/xeen_fd03.studio.yml')
FD03_LIVE = ((os.path.exists(_FD03_SIDE) and 'entrance:x5_door' in open(_FD03_SIDE).read())
             or os.environ.get('X5_FD03_LIVE') == '1')
EAST_START = (107, 58)        # the east start on the lagoon road's meadow, looking west up the river

# ---------------------------------------------------------------------------------------------------------------
# A3's hooks on X5 (quest files' `hooks` with `map: X5`)
HOOKS = {}
for _f in sorted(os.listdir(os.path.join(XEEN_SOURCE, 'quests'))):
    _q = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'quests', _f)))
    for _k, _v in (_q.get('hooks') or {}).items():
        if _v.get('map') == 'X5':
            HOOKS['%s.%s' % (_f[:-4], _k)] = _v

def hook(name):
    assert name in HOOKS, name
    return [{'lua': 'XeenQuests.hook("%s")' % name}]

# Q-C16's outpost burnt (A6 s27): what goes and what shows (MM8's stumps and D2's charred embers, as D2's forts)
# D-152: the bones round the tents go with them
OUTPOST_GONE = ['thing:outpost_tent', 'thing:outpost_tent2', 'thing:outpost_fire'] + [
    'thing:outpost_bones_%d' % (i + 1) for i in range(3)]
OUTPOST_CHAR = [('dec24x', (42.2, 91.8)), ('stump5a', (42.9, 92.5)), ('dec24x', (45.1, 93.3)),
                ('stump5a', (44.6, 93.9)), ('dec24x', (44.2, 91.6))]
OUTPOST_BURN = ' '.join(['HideThing("%s")' % t for t in OUTPOST_GONE]
                        + ['ShowThing("thing:outpost_char_%d")' % (i + 1) for i in range(len(OUTPOST_CHAR))])

# A4's houses (source/towns/x5.yml): door -> house id and name
TOWN = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'towns/x5.yml')))
HOUSE = {h['door']: (h['id'], h['name']) for h in TOWN['houses']}
# A cursed-town house (`opens: q-c6.done`) shows its closed_text until the town is liberated (TOWNS_FORMAT 1)
OPENS = {'q-c6.done': 'winterkill_liberated'}
GATED = {h['id']: (OPENS[h['opens']], h['closed_text']) for h in TOWN['houses']
         if h.get('opens') and not h['door'].startswith('thing:')}
HOUSE_MIRROR = HOUSE.get('thing:mirror', HOUSE.get('thing:winterkill_mirror'))[0]

# A2's rows (source/monsters.yml): Act II's pocket and Act III's west
ROW = {
    'dark_wolf': 11410, 'sabertooth': 11411, 'snow_beast': 11412,
    'barbarian': 11100, 'sardaj': 11101, 'barbarian_chief': 11102,
    'troll': 11070,
    'cyclops': 11080, 'giant': 11081,
    'ogre': 11060, 'ogre_brute': 11061,
    'evil_archer': 11130,
    'spirit_bones': 11241, 'polter_fool': 11260,
    # Q-C6's third wave, the Ghost Riders: A2's row (spirits tier D, level 27; D-13)
    'ghost_rider': 11263,
}
SLOT = {'wolves': 'Xeen Wolf', 'barbarians': 'Xeen Barbarian', 'trolls': 'Xeen Troll'}
# NPCs the map places outdoors (A4's ids; their talk is A3's): (npc, actor kind, at, group)
NPC_ACTORS = [
    (4502, '361', (36.6, 43.0)),     # Mayor Randon by the gongs (MM7 Peasant Human1 MaleB)
    (4527, '377', (82.8, 45.0)),     # Freeda the Mountaineer at her camp on the pass crest (Human2 FemaleA)
    (4528, '451', (73.6, 69.6)),     # Thickbark the Civilized, a talking tree (MM7's Treant) at the forest's edge
    (4529, '11928', (30.2, 61.3)),   # the Winter Druid in his grove (D-91: S's Elder Druid, a robed old man);
                                     # F63: (30.4, 61.6) stood 80 from a stone of his ring
]
QBIT = {'liberated': 112121, 'wave1': 112122, 'wave2': 112123, 'wave3': 112124, 'reported1': 112126,
        'reported2': 112127}
ITEMS = {'golem_stone': 12305, 'holy_book': 12524}
HOLY_BOOK_AT = (68.85, 92.4)   # s33: on the ground beside the torn pack (thing:holy_book at 68.6, 92.4)
# F63 (X5 p7): the outpost's eight Cyclopes on open ground inside its fence, clear of the tents by a body and 32
OUTPOST_CYCLOPES = [(41.9, 93.8), (43.0, 94.2), (42.3, 94.85), (43.9, 93.2), (43.9, 92.2), (44.6, 94.9), (45.6, 94.9),
                    (46.25, 93.5)]
WAVE = 16              # ghosts in each of Q-C6's three waves (D-13: 16, the source's 20 scaled to kill XP)

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

def poly_dist(p, poly):
    return min(K.seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))

def msg(text):
    return {'lua': 'evt.SimpleMessage("%s")' % text.replace('\\', '\\\\').replace('"', '\\"')}

def sign(sid, at, title, text=None, height=224, width=160, effects=None):
    return {'id': sid, 'kind': 'sign', 'at': list(at), 'height': height, 'width': width, 'title': title,
            'effects': effects if effects is not None else [msg(text)]}

def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d

# ---------------------------------------------------------------------------------------------------------------
# Land and water. Heights are map units above the stars below the rim (water at 0).
# ---------------------------------------------------------------------------------------------------------------
RIM_X = 24          # the world rim, west: the land ends in a cliff along x 24
RIM_Y = 104         # the world rim, south: along y 104
ICE = 800           # the frozen mere and the frozen river below the gorge (land painted ice, D-6.3)
# The icefall (D-6.5, session 6): the ice field spills north off the plateau between the west crag and the Giants'
# Stones (36-38, 84-85), a broken front from the head to 1,600, then a low tongue to its snout on the snowfield, so the
# glacier shows from the south track, Glom's fork and the Shrine of Cold. A ridge word: the 4-cell grid cannot hold it.
ICEFALL = [[32.5, 87], [32.5, 86], [32.5, 85], [32.5, 84], [32.5, 83], [32, 82], [32, 80.5], [32, 79], [32, 78]]
ICEFALL_H = [2900, 2700, 2450, 2100, 1750, 1550, 1400, 1270, 1190]
RIVER = 840         # the Lagoon Water, open, from the east edge through the gorge to 1,000 past it (D-6.1)
TOWN_H = 1000       # Winterkill
MERE = [[40, 53], [47, 50], [56, 50], [63, 52], [68, 56], [70, 61], [67, 66], [60, 70], [50, 71], [43, 68], [39, 61]]
ISLE = (55, 61)     # Darkstone's rock in the ice
RIVER_OPEN = [[128, 62], [118, 62], [110, 63], [103, 63], [97, 63], [91, 63], [86, 62], [82, 61], [78, 61], [76, 61]]
RIVER_ICE = [[76, 61], [72.5, 61], [69, 61]]
# The Frostspine crest north of the gorge: [y, height] along x about 82, the pass notch at y 46 (D-6.1: peaks 3,400 to
# 4,000, the notch at 1,700 seen from the X3 arrival)
CREST = [(0, 3000), (4, 3400), (8, 3000), (12, 3700), (16, 3200), (20, 3500), (24, 4000), (28, 3300), (32, 3600),
         (36, 3800), (39, 3200), (42, 2500), (44, 1950), (46, 1700), (48, 1950), (50, 2700), (53, 3400), (56, 3100),
         (58.5, 2800)]
CREST_X = {0: 82, 12: 82, 24: 83, 36: 82, 46: 82, 53: 82, 58.5: 81}
# The spur (D-6.1): from the gorge's south shoulder (81, 66) to the rim near (84, 104), crest about 2,800, cliffed
SPUR = [[81, 65.5], [81.5, 70], [82, 76], [82.5, 82], [83, 88], [83.5, 94], [84, 99], [84, 103.5]]
SPUR_H = [2400, 2800, 3000, 2700, 2900, 2600, 2800, 2500]

def crest_at(y):
    for (y0, h0), (y1, h1) in zip(CREST, CREST[1:]):
        if y0 <= y <= y1:
            return h0 + (h1 - h0) * (y - y0) / (y1 - y0)
    return CREST[-1][1]

def crest_x(y):
    ks = sorted(CREST_X)
    for a, b in zip(ks, ks[1:]):
        if a <= y <= b:
            return CREST_X[a] + (CREST_X[b] - CREST_X[a]) * (y - a) / (b - a)
    return CREST_X[ks[-1]]

CALM = [(37, 42, 9), (69, 31, 6), (96, 50, 4), (100, 72, 3), (96, 44, 3), (64, 48, 3), (58, 42, 2.5), (73, 40, 3),
        (106, 58, 5), (30, 61, 3), (44, 81, 3), (53, 75, 2.5), (26, 41, 2.5), (30, 29, 3), (47, 100, 2.5),
        (42, 25, 3), (66, 22, 2.5), (60, 30, 2), (101, 37, 3), (104, 86, 3), (92, 90, 2), (50, 35, 2.5)]

def roll(x, y):
    w = 1.0
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 4.0))
    w = min(w, smooth((x - RIM_X - 2) / 4.0), smooth((RIM_Y - 2 - y) / 4.0))
    v = (180 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.6 + 1.1) + 120 * math.sin((x + 1.4 * y) / 4.7 + 0.3)
         + 70 * math.sin((x - 1.7 * y) / 2.6))
    return w * v

def d142_enforce(areas):
    """D-142's moves for the encounter circles (common/d142.py), keeping the checks of build()'s marker loop."""
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import d142
    sys.path.pop(0)
    l4 = _REPO_ROOT + '/devdocs/xeen/briefs/x5/L4/sketch.yml'
    keep = [[[25, 30], [52, 30], [52, 50], [37, 54], [25, 52]], [[62, 25], [78, 25], [78, 44], [62, 44]],
            [[27, 58], [33, 58], [33, 64], [27, 64]], [[40, 78], [50, 78], [50, 85], [40, 85]],
            [[78, 40], [88, 40], [88, 52], [78, 52]], [[100, 54], [112, 54], [112, 62], [100, 62]],
            [[51, 56], [59, 56], [59, 65], [51, 65]]]   # build()'s keep_clear areas
    base = d142.standard_ok(l4, land, keep_off=keep)
    wk = [d[2] for d in doors_out if d[0].startswith('building:winterkill') or d[0] == 'building:mindmeld_guild']

    def ok(x, y, r):
        lo, hi = 64 - 23106 / 512, 64 + 23106 / 512
        return (base(x, y, r) and min(x - max(lo, RIM_X), hi - x, y - lo, min(hi, RIM_Y) - y) - r >= 1.5
                and (math.hypot(x - 55, y - 59) - r) * 512 >= 6000
                and min(math.hypot(x - q[0], y - q[1]) for q in wk) * 512 >= 4500)
    trolls = lambda x, y, r: ok(x, y, r) and math.hypot(x - XD10_SOUTH[0], y - XD10_SOUTH[1]) >= 6
    steppe = lambda x, y, r: ok(x, y, r) and all(math.hypot(x - q[0], y - q[1]) * 512 >= 4000 for q in PASS_DESCENT)
    roads = d142.road_cells(l4)   # the last sketch's lines (the roads are fixed in this file)
    for pop, slot, fit in (('pop:snow_beasts', 1, ok), ('pop:barbarians', 2, steppe), ('pop:trolls', 3, trolls)):
        d142.enforce('xeen_x5', areas, roads, {pop: slot}, fit, giver_range=5120)


def land(x, y):
    """The land before the water, the town and the words that the build lays over it."""
    # the west: Winterkill's shore and the snowfields round the mere about 1,000; the steppe rising north to 1,450;
    # the rim plateau 1,450-1,550; the Troll Forest 1,100-1,300; the giants' plateau 2,000-2,300 and its crags
    h = 1020.0
    h += 430 * smooth((48 - y) / 26.0) * smooth((x - 30) / 4.0)            # the steppe rises north
    h += 480 * smooth((40 - y) / 12.0) * smooth((36 - x) / 6.0)            # the rim plateau
    h += 180 * smooth((y - 72) / 10.0) * smooth((80 - x) / 8.0)            # the forest's floor rises south
    # the giants' corner: a plateau with two crags and the glacier between them
    g = smooth((y - 84) / 4.0) * smooth((54 - x) / 4.0)
    h += g * 1000
    h += bump(x, y, 28, 89, 6, 1400) + bump(x, y, 50, 94, 5, 1500) + bump(x, y, 45, 88, 4, 300)
    # the glacier (D-6.5, the signature view): a crowned tongue of ice from its head between the crags (2,950) down
    # to its lip over the rim (2,050, the Reflector's ledge), its sides easing into the plateau over three cells so
    # the ledge sees the whole tilted ice surface rise to the head, with low transverse ridges (seracs)
    t = max(0.0, min(1.0, (y - 85.5) / 18.0))
    gc = 35.0 - 1.0 * t
    hw = 3.0 + 2.0 * t
    gd = abs(x - gc)
    if gd < hw + 3.0 and 84.0 < y:
        top = 2950 - 900 * t + 120 * max(0.0, 1 - (gd / hw) ** 2) + 50 * math.sin(y * 2.4) * smooth((hw - gd) / 2)
        w = smooth((hw + 3.0 - gd) / 3.0) * smooth((y - 84.0) / 2.0)
        h = h * (1 - w) + top * w
    # Kai Wu's crag (its terrace and cliff are words)
    h += bump(x, y, 69, 32, 7, 700)
    # the pocket, east of the Frostspine: the Ogre Hills north, the river valley and the fen south
    if x > 84:
        e = smooth((x - 84) / 3.0)
        p = 920.0
        p += 900 * smooth((52 - y) / 14.0)
        p += (bump(x, y, 92, 28, 9, 700) + bump(x, y, 104, 24, 10, 600) + bump(x, y, 117, 33, 9, 500)
              + bump(x, y, 110, 43, 6, 350) + bump(x, y, 122, 14, 12, 500) + bump(x, y, 97, 12, 9, 600))
        p -= bump(x, y, 101, 37, 4.5, 450)                                   # the ogres' hollow
        p += bump(x, y, 101, 75.5, 3.2, 520) + bump(x, y, 104, 86, 3, 120)   # the Golem Rocks, the archers' rise
        h = h * (1 - e) + p * e
    # the Frostspine: a broad base under the crest words
    if y < 60:
        d = abs(x - crest_x(y))
        top = crest_at(y) * 0.8
        if d < 7:
            h = max(h, top - (top - h) * smooth(d / 7.0))
    h += roll(x, y)
    # the open river's valley: banks at 900, the valley side back to the land over 4 cells
    d = dist_to_line(x, y, RIVER_OPEN)
    if d < 6:
        h = 900 + (h - 900) * smooth((d - 1.8) / 4.2)
    # the mere and the frozen river: ice at 800, shores back over three cells
    if K.inside((x, y), MERE):
        h = ICE
    else:
        dm = min(poly_dist((x, y), MERE), dist_to_line(x, y, RIVER_ICE) - 1.2)
        if dm < 3.5:
            h = ICE + (h - ICE) * smooth(dm / 3.5)
    # the rim: the land runs level to the cliff's lip
    if x < RIM_X or y > RIM_Y:
        return 0.0
    return h

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
# Winterkill (A4's 17 doors and the mirror). Plots: (building, title, house door key, at = NW corner, facing,
# [front, depth], kit, kind, extra). The square [34, 40] x [38, 45]; the road from the Steppe Cross enters it from the
# east along y 41.5, the south track leaves it south at x 37, the rim walk west at y 41.5.
# ---------------------------------------------------------------------------------------------------------------
SQUARE = [[34, 38], [40, 38], [40, 45], [34, 45]]
TOWN_POLY = [[28, 33], [48, 33], [48.5, 40], [46, 48.5], [37, 50], [29.5, 48.5], [28, 41]]
WINTERKILL_ROAD = [[50, 35], [48.5, 37.5], [48.5, 41.5], [40, 41.5]]
SOUTH_TRACK = [[37, 45], [37, 50], [36, 55], [35.5, 60], [37, 66], [40, 72], [42, 77]]
RIM_WALK = [[34, 41.5], [30, 41.5], [27.4, 41.3]]
# Final cloud round (2026-11-24, town_fit_check `houses.jammed`, F49): three pairs stood 72-104 apart, under the
# 128 a lane needs (and over the 32 of a flush pair). Plots keep the half-cell grid: house #12 and the tavern half a
# cell west (the tavern from the temple's side), house #3 half a cell south (from #2), house #8 half a cell east (from
# #7).
PLOTS = [
    # north side, facing south onto the square
    ('building:winterkill_houses', None, 12, (31.5, 36.5), 's', [1, 1], 'poor', 'cottage', {}),
    ('building:winterkill_tavern', 'The Frozen Flagon', None, (33.0, 36.0), 's', [2, 1.5], 'timber', 'gable_porch',
     {'sign': '7sgtvrn'}),
    ('building:winterkill_temple', 'Temple of the Thaw', None, (35.5, 35.0), 's', [2.5, 2.5], 'stone', 'temple', {}),
    ('building:winterkill_houses', None, 1, (38.5, 36.0), 's', [1, 1.5], 'plaster', 'gable_porch', {}),
    ('building:winterkill_armour', 'Furs and Fittings', None, (40.0, 36.0), 's', [1.5, 1.5], 'plaster', 'jetty',
     {'sign': '7sgarm'}),
    ('building:winterkill_houses', None, 9, (41.5, 39.0), 's', [1, 1], 'grey', 'cottage', {}),
    # west side, facing east onto the square
    ('building:mindmeld_guild', 'The Mindmeld Guild', None, (31.5, 38.5), 'e', [2, 2], 'stone', 'tower_house', {'sign': 'sgmind'}),   # D-92
    ('building:winterkill_houses', None, 2, (32.5, 42.5), 'e', [1.5, 1], 'plaster', 'cottage', {}),
    ('building:winterkill_houses', None, 3, (32.0, 44.5), 'e', [1.5, 1.5], 'timber', 'gable_porch', {}),
    # south side, facing north onto the square
    ('building:winterkill_houses', None, 5, (34.0, 45.5), 'n', [1, 1], 'grey', 'cottage', {}),
    ('building:winterkill_houses', None, 6, (35.0, 45.5), 'n', [1, 1], 'poor', 'cottage', {}),
    ('building:winterkill_houses', None, 7, (38.0, 45.5), 'n', [1.5, 1.5], 'plaster', 'L', {}),
    ('building:winterkill_houses', None, 8, (40.0, 45.5), 'n', [1, 1], 'poor', 'cottage', {}),
    # east side, facing west onto the square, south of the road
    ('building:winterkill_guild_dark', 'The Guild of Shadows', None, (40.5, 42.5), 'w', [2, 2], 'stone', 'L',
     {'sign': 'sgdark'}),   # D-92: every guild hangs its school's sign
    # the outskirts
    ('building:winterkill_houses', None, 4, (29.5, 44.0), 'e', [1, 1], 'poor', 'cottage', {}),
    ('building:winterkill_houses', None, 10, (43.0, 45.0), 's', [1, 1.5], 'poor', 'gable_porch', {}),
    ('building:winterkill_houses', None, 11, (45.5, 36.0), 's', [1.5, 1.5], 'timber', 'barn', {}),
]
# Kai Wu's monastery on its crag (terrace 1,900) and the other houses of the tundra
MONASTERY_H = 1900
MONASTERY = [[64, 27], [75, 27], [75, 37], [64, 37]]
WILD_PLOTS = [
    ('town:monastery', 'building:monastery_training', "Kai Wu's Monastery", None, (65.0, 28.5), 's', [3, 2.5],
     'stone', 'cloister', {'sign': '7sgtrain'}),
    ('town:monastery', 'building:monastery_temple', 'Hall of Stillness', None, (70.5, 28.5), 'w', [2.5, 2.5],
     'stone', 'temple', {}),
    ('town:glom', 'building:glom_burrow', "Glom's Burrow", 1, (43.0, 80.0), 'n', [1, 1], 'poor', 'round_hut', {}),
    ('town:glom', 'building:glom_burrow', "The Steward's Burrow", 2, (45.5, 80.5), 'n', [1, 1], 'poor', 'round_hut',
     {}),
    ('zone:halon_yard', 'building:halon_workshop', "Halon's Workshop", None, (93.0, 48.5), 's', [2, 1.5], 'timber',
     'forge', {}),
]
SLATE = 'xtslate'          # A6's towers kit: the slate roof (kit_textures/landmarks)

def house_of(bid, index):
    key = bid if index is None else '%s#%d' % (bid, index)
    return HOUSE[key]

plots_by_space = {}
plan_buildings = {}
footprints = []
doors_out = []

def add_plot(space, bid, title, index, at, facing, fp, kit, kind, extra, door_to=None, floor=None):
    x, y = at
    turn = 0
    want = facing
    if kind == 'round_hut':
        facing, turn = 's', K.TURN_OF[want]
        if turn > 180:
            turn -= 360
    plot = {'building': bid, 'at': [x, y], 'facing': facing, 'kit': kit}
    if index is not None:
        plot['index'] = index
    if turn:
        plot['turn'] = turn
    if door_to:
        plot['door_to'] = door_to
    if floor:
        plot['floor'] = floor
    hid, hname = house_of(bid, index)
    plot['house'] = hid
    plot['title'] = hname
    if hid in GATED:
        qname, closed = GATED[hid]
        plot['condition'] = {'qbit': qname}
        plot['else_effects'] = [msg(closed)]
    Wp, Hp = K.plot_extent(facing, fp)
    if kind == 'temple':
        # a nave with its door to the square and a squat bell tower at its back, under the slate roofs
        if facing in ('s', 'n'):
            nave = {'id': 'nave', 'at': [64, 64 + 256 if facing == 's' else 64], 'size': [Wp - 128, Hp - 128 - 256],
                    'wall_height': 416, 'roof': 'gable', 'roof_pitch': 50, 'ridge_along': 'ns',
                    'textures': {'roof': SLATE}}
            tower = {'id': 'tower', 'at': [Wp // 2 - 144, 64 if facing == 's' else Hp - 352], 'size': [288, 288],
                     'wall_height': 832, 'roof': 'hip', 'roof_pitch': 62, 'windows': 'none',
                     'textures': {'roof': SLATE}}
        else:
            nave = {'id': 'nave', 'at': [64 if facing == 'w' else 64 + 256, 64], 'size': [Wp - 128 - 256, Hp - 128],
                    'wall_height': 416, 'roof': 'gable', 'roof_pitch': 50, 'ridge_along': 'ew',
                    'textures': {'roof': SLATE}}
            tower = {'id': 'tower', 'at': [Wp - 352 if facing == 'w' else 64, Hp // 2 - 144], 'size': [288, 288],
                     'wall_height': 832, 'roof': 'hip', 'roof_pitch': 62, 'windows': 'none',
                     'textures': {'roof': SLATE}}
        plot['parts'] = [nave, tower]
        plot['door'] = {'part': 'nave', 'wall': facing}
    elif kind == 'cloister':
        # Kai Wu's hall: a long fieldstone hall under slate with a lower wing (the source's monastery, WORLD_DESIGN 5.1)
        b = K.box('body', facing, fp, 64, 64, int(Wp - 128), int(Hp * 0.55), roof='gable',
                  ridge_along=K.ALONG[facing], roof_pitch=40, wall_height=448, textures={'roof': SLATE})
        if extra.get('sign'):
            # the board at its picture's own size (64; merge point 18 lays a sign's picture at its texel size)
            b['signs'] = [{'wall': facing, 'bay': 0, 'texture': extra['sign'], 'hang': True, 'size': [64, 64],
                           'out': 48, 'bottom': 120}]
        w = K.box('wing', facing, fp, 96, int(Hp * 0.55) + 32, int(Wp * 0.45), int(Hp * 0.45) - 96, roof='lean_to',
                  wall_height=320, windows='none', textures={'roof': SLATE})
        plot['parts'] = [b, w]
        plot['door'] = {'part': 'body', 'wall': facing}
    else:
        roof = extra.get('roof') or K.ROOFS.get(kit)
        if kit == 'stone':
            roof = SLATE
        parts, door = K.shape(kind, facing, fp, kit, sign=extra.get('sign'), roof_tex=roof)
        if kind == 'round_hut':
            for p in parts:
                p['wall_height'] = 192
        plot['parts'] = parts
        plot['door'] = door
    plots_by_space.setdefault(space, []).append(plot)
    pb = plan_buildings.setdefault(space, {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [],
                   'service': title or 'residence'}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append((index or 0, fp))
    poly = K.footprint(x, y, facing, fp, turn)
    footprints.append((bid, index, poly))
    if kind == 'round_hut':
        dc = K.door_cell(x, y, 's', fp, turn, -0.08)
        out = K.door_cell(x, y, 's', fp, turn, 0.9)
    else:
        dc = K.door_cell(x, y, facing, fp, turn, 0.0)
        out = K.door_cell(x, y, facing, fp, turn, 0.9)
    doors_out.append((bid, index, dc, out))

for (bid, title, index, at, facing, fp, kit, kind, extra) in PLOTS:
    add_plot('town:winterkill', bid, title, index, at, facing, fp, kit, kind, extra)
for (space, bid, title, index, at, facing, fp, kit, kind, extra) in WILD_PLOTS:
    add_plot(space, bid, title, index, at, facing, fp, kit, kind, extra)
for _pb in plan_buildings.values():
    for _b in _pb.values():
        _b['footprint_cells'] = [fp for _, fp in sorted(_b['footprint_cells'], key=lambda t: t[0])]

# ---------------------------------------------------------------------------------------------------------------
# Roads and paths (D-6.1: no Thickbark bridge; the pocket's ways west are the pass road and XD-10)
# ---------------------------------------------------------------------------------------------------------------
LAGOON_ROAD = [[128, 59], [118, 59], [110, 59], [104, 59.5], [98, 60]]
PASS_ROAD = [[98, 60], [93, 58], [89, 55], [86, 51], [83.5, 47.5], [82, 46]]
PASS_DESCENT = [[82, 46], [80, 44], [77, 41.5], [73, 40]]
SHORE_ROAD = [[73, 40], [66, 41.5], [60, 39.5], [54, 37], [50, 35]]
STEPPE_ROAD = [[50, 0], [50, 10], [50, 21], [50, 35]]
HILL_TRACK = [[98, 60], [99, 56], [100.5, 52.5], [100.5, 48], [98.5, 46], [96, 45]]
GOLEM_LANE = [[98, 60], [97.5, 61], [97.5, 65], [98.5, 67], [100.5, 70.5]]
PAGODA_PATH = [[73, 40], [70, 43], [67, 45.5], [64.5, 46.6]]
DRUID_PATH = [[35.5, 60], [32, 61]]
GLOM_LANE = [[42, 77], [43.5, 79], [45.5, 79.5]]
GIANTS_PATH = [[42, 77], [40, 82], [39.5, 86], [41.5, 90.5], [43.5, 92]]
FOREST_TRACK = [[42, 77], [48, 77], [53, 75.5], [58, 81], [63, 88], [65.5, 93.8]]
THICKBARK_PATH = [[53, 75.5], [60, 73.5], [67, 71.5], [72.6, 70.0]]
CAVE_SOUTH_PATH = [[63, 88], [70, 85.5], [75, 83], [77, 82]]
ROADS = [LAGOON_ROAD, PASS_ROAD, PASS_DESCENT, SHORE_ROAD, STEPPE_ROAD, WINTERKILL_ROAD]
PATHS = [HILL_TRACK, GOLEM_LANE, PAGODA_PATH, SOUTH_TRACK, DRUID_PATH, GLOM_LANE, GIANTS_PATH, FOREST_TRACK,
         RIM_WALK, THICKBARK_PATH, CAVE_SOUTH_PATH]

def check_roads():
    bad = []
    for b, ix, poly in footprints:
        for line in ROADS:
            if K.line_hits_poly(line, poly, 0.45):
                bad.append('road under or against %s#%s: %s' % (b, ix, line[:3]))
        for line in PATHS:
            if K.line_hits_poly(line, poly, 0.5):
                bad.append('path under %s#%s: %s' % (b, ix, line[:3]))
    for i, (b, ix, p) in enumerate(footprints):
        for (b2, ix2, q) in footprints[i + 1:]:
            cx = sum(v[0] for v in p) / 4; cy = sum(v[1] for v in p) / 4
            p_ = [(cx + (v[0] - cx) * 0.98, cy + (v[1] - cy) * 0.98) for v in p]
            cx = sum(v[0] for v in q) / 4; cy = sum(v[1] for v in q) / 4
            q_ = [(cx + (v[0] - cx) * 0.98, cy + (v[1] - cy) * 0.98) for v in q]
            if any(K.inside(v, q_) for v in p_) or any(K.inside(v, p_) for v in q_):
                bad.append('plots overlap: %s#%s and %s#%s' % (b, ix, b2, ix2))
    if bad:
        raise SystemExit('\n'.join(bad))
check_roads()

# ---------------------------------------------------------------------------------------------------------------
# Ways in (the dungeons' exits arrive in front of these; the build's doors are measured by tools/doors.py)
# ---------------------------------------------------------------------------------------------------------------
XD09_DOOR = (100.5, 71.85)          # the slab door in the Golem Rocks' north face, looking north
XD10_NORTH = (96.5, 44.0)           # the cave's north mouth in the Ogre Hills, looking south (XD-10's arrival)
XD10_SOUTH = (78.0, 82.5)           # the south mouth in the spur's west face, looking west (D-6.1)
PAGODA_AT = (62.5, 45.0)            # the Ninja Pagoda's plot (NW corner), 4 x 3 cells, its door looking north
WARREN_AT = (65.5, 95.5)            # the Troll Warren's mound (its middle), its mouth looking north
DARKSTONE_C = (55.0, 61.0)          # Darkstone Tower's middle on its rock
ISLE_H = 1500

def build():
    os.makedirs(OUT, exist_ok=True)
    # ================================ project.yml
    neighbours = [
        {'id': 'door:xd09', 'to': 'xeen_xd09.blv', 'kind': 'door', 'condition': {'item': 'golem_stone'},
         'arrival_hint': 'At the foot of the entry stair inside the Golem Rocks.',
         'notes': 'XD-09 Golem Dungeon (A8). The slab door in the Golem Rocks\' north face, by the lagoon border (D-4).'},
        {'id': 'door:xd10_north', 'to': 'xeen_xd10.blv', 'kind': 'door',
         'arrival_hint': "In the north mouth, ice at the lip (XD-10's arrival).",
         'notes': "XD-10 Cave of Illusion (A8): the north mouth in the Ogre Hills above Halon's yard (D-4)."},
        {'id': 'door:xd10_south', 'to': 'xeen_xd10.blv', 'kind': 'door',
         'arrival_hint': 'In the south mouth, facing in.',
         'notes': ("XD-10's south mouth in the spur's west face (D-6.1), the pocket's second way west. The studio says "
                   "one arrival per dungeon: XD-10's exit by this mouth lands by explicit coordinates (D-4).")},
    ]
    if XD22_LIVE:
        neighbours.append({'id': 'door:xd22', 'to': 'xeen_xd22.blv', 'kind': 'door',
                           'arrival_hint': "On the pagoda shore in front of its door (XD-22's exit point).",
                           'notes': "XD-22 Ninja Pagoda (Q-C4, D-25): the door on the pagoda's north side."})
    if XD23_LIVE:
        neighbours.append({'id': 'door:xd23', 'to': 'xeen_xd23.blv', 'kind': 'door',
                           'arrival_hint': "On the warren's beaten snow, in front of the mouth (XD-23's exit point).",
                           'notes': "XD-23 Troll Warren (Q-C15, D-25): the mouth in the mound under the firs."})
    if X3_LIVE:
        neighbours.insert(0, {
            'id': 'edge:east', 'to': 'xeen_x3.odm', 'kind': 'edge', 'side': 'east', 'days': 7, 'arrival_side': 'west',
            'approach': 'The lagoon road along the river, east out of the pocket at y 59.',
            'notes': ("X3 Lifeforce Lagoon (A5): arrives at X3's west start (-22016, 2560, 864) facing east; X3's own "
                      "edge:west arrives at X5's east start on the lagoon road's meadow (107, 58) facing west.")})
    if X6_LIVE:
        neighbours.insert(0, {
            'id': 'edge:north', 'to': 'xeen_x6.odm', 'kind': 'edge', 'side': 'north', 'days': 7,
            'arrival_side': 'south',
            'approach': 'The steppe road, north out of the stony valley at x 50.',
            'notes': ("X6 Desert of the Sphinx (A5): arrives at X6's south start (-7168, -22016, 1472) facing north; "
                      "X6's own edge:south arrives at X5's north start on the steppe road (50, 20) facing south.")})
    project = {
        'format': 0, 'id': STEM, 'name': 'Winterkill Tundra', 'world': 'xeen', 'kind': 'outdoor', 'profile': 'odm',
        'map_code': 'X5', 'units': {'plan_grid': 512}, 'extent': {'terrain_cells': 128},
        'map_stats': {
            'id': 9103, 'continent': 6, 'encounter_chance': 10, 'treasure_level': 3, 'trap_dice': 3,
            'perception_difficulty': 3, 'refill_days': 672, 'music': 47, 'environment': 'plains',
            'lock_difficulty': 6,
            # A2's slot families (map_rows.yml): wolves only Dark Wolves (Dif 0: the pocket's Act II band and the
            # snowfields' packs; Sabertooths and Snow Beasts are placed), barbarians and trolls mixed (Dif 3, 2)
            'slots': [
                {'monster': SLOT['wolves'], 'tier': 0, 'per_marker': [1, 3], 'weight': 30},
                {'monster': SLOT['barbarians'], 'tier': 3, 'per_marker': [1, 3], 'weight': 30},
                {'monster': SLOT['trolls'], 'tier': 2, 'per_marker': [1, 3], 'weight': 40},
            ]},
        'neighbours': neighbours,
        'qbits': {'winterkill_liberated': QBIT['liberated'], 'wave1_laid': QBIT['wave1'], 'wave2_laid': QBIT['wave2'],
                  'wave3_laid': QBIT['wave3'], 'reported1': QBIT['reported1'], 'reported2': QBIT['reported2']},
        'items': dict(ITEMS),
        'rules': {'weather': 'snow', 'respawn': 'entrance:winterkill_square',
                  'town_portal_anchor': 'entrance:winterkill_square'},
        'notes': ("X5 Winterkill Tundra (A6, 2026-11-20), built from the approved L1 with D-6.1, D-6.3, D-6.5 and "
                  "D-4. The north edge (X6) is sealed with a sign until X6 is installed (X6_LIVE); the east edge "
                  "(X3) too until X3 is installed (X3_LIVE). "
                  "Written by output/studio_cal/x5/tools/gen.py."),
    }
    # ================================ plan.yml (L1's spaces with the decisions applied)
    L1 = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'plan.yml')))
    plan = copy.deepcopy(L1)
    plan['level'] = 'L3'
    for s in plan['spaces']:
        if s['id'] in plan_buildings:
            s['buildings'] = list(plan_buildings[s['id']].values())
        if s['id'] == 'zone:frostspine':
            s['purpose'] = ("The ridge between the pocket and the west: bare rock and snow, crossed by one pass; the "
                            "river cuts through it in a gorge; south of the gorge a cliffed spur runs on to the rim "
                            "(D-6.1), no crossing.")
        if s['id'] == 'zone:ogre_hills':
            s['population'] = [
                {'id': 'pop:pocket_hills', 'actor': str(ROW['dark_wolf']), 'groups': 5, 'placed': True, 'hostile': True,
                 'notes': 'Act II: Dark Wolves 16 (the A tier only, D-4), placed in packs of two and three.'},
                {'id': 'pop:ogre_camp', 'actor': str(ROW['ogre']), 'groups': 1, 'placed': True, 'hostile': True,
                 'notes': 'Six at the camp: four Ogres (18), two Ogre Brutes (22).'}]
        if s['id'] == 'zone:lagoon_marches':
            s['population'] = [
                {'id': 'pop:pocket_marsh', 'actor': str(ROW['dark_wolf']), 'groups': 6, 'placed': True, 'hostile': True,
                 'notes': 'Act II: Dark Wolves 16 by the river and in the fen; the first fight about 2,500 from the '
                          'X3 arrival.'},
                {'id': 'pop:archer_camp', 'actor': str(ROW['evil_archer']), 'groups': 1, 'placed': True,
                 'hostile': True, 'notes': 'Seven Evil Archers (8) at their camp (D-4: A tier only).'}]
        if s['id'] == 'zone:snowfields':
            s['population'] = [
                {'id': 'pop:snow_beasts', 'slot': 1, 'groups': 11, 'per_marker': [2, 3], 'levels': [16, 16],
                 'notes': 'Encounter area 5: Dark Wolves in packs round the west and south shores.'},
                {'id': 'pop:snow_packs', 'actor': str(ROW['sabertooth']), 'groups': 4, 'placed': True, 'hostile': True,
                 'notes': 'Two packs of Sabertooths (22) and two of Snow Beasts (28).'}]
        if s['id'] == 'zone:steppe':
            s['population'] = [
                {'id': 'pop:barbarians', 'slot': 2, 'groups': 10, 'per_marker': [2, 3], 'levels': [14, 28],
                 'notes': 'Encounter area 4; none within 2,000 of the pass descent or the monastery foot (D-6.1).'},
                {'id': 'pop:barbarian_camp', 'actor': str(ROW['barbarian']), 'groups': 2, 'placed': True,
                 'hostile': True, 'notes': 'The camp (six round the fire and the chief) and the hunting camp (three).'}]
        if s['id'] == 'zone:giants':
            s['population'] = [
                {'id': 'pop:cyclopes', 'actor': str(ROW['cyclops']), 'groups': 4, 'placed': True, 'hostile': True,
                 'notes': 'Encounter area 6: three pairs of Cyclopes (36) and one Giant (50) on the east crag.'},
                {'id': 'pop:cyclops_outpost', 'actor': str(ROW['cyclops']), 'groups': 1, 'placed': True,
                 'hostile': True, 'notes': "The outpost Glom wants burnt: eight Cyclopes."}]
        if s['id'] == 'zone:troll_forest':
            s['purpose'] = ("Snowy firs from the mere's south shore to the rim: trolls, the Troll Warren, the Holy "
                            "Book of Elvenkind by it; Thickbark on its north-east edge by the frozen river; XD-10's "
                            "south mouth in the spur's west face (D-6.1).")
        if s['id'] == 'town:winterkill':
            s['population'] = [
                {'id': 'pop:winterkill_ghosts', 'actor': str(ROW['spirit_bones']), 'groups': 3, 'placed': True,
                 'hostile': True, 'notes': ('Q-C6: the Spirit Bones haunt the town at load (%d); the Polter-Fools and '
                                            'the Ghost Riders (%d each) show when Randon has heard of the wave before.'
                                            % (WAVE, WAVE))},
                {'id': 'pop:townsfolk', 'actor': '361', 'groups': 1, 'placed': True, 'hostile': False,
                 'notes': 'Ten townsfolk, shown when Winterkill is liberated (112121).'}]
    plan['links'] = [l for l in plan['links'] if l['id'] != 'link:thickbark_bridge']
    plan['links'] += [
        {'id': 'link:thickbark_path', 'from': 'link:forest_track', 'to': 'zone:troll_forest', 'kind': 'path',
         'notes': "From the Shrine of Cold along the forest's north edge to Thickbark by the frozen river (D-6.1)."},
        {'id': 'link:cave_south_path', 'from': 'link:forest_track', 'to': 'zone:troll_forest', 'kind': 'path',
         'notes': "To XD-10's south mouth in the spur's west face (D-6.1)."},
    ]
    for l in plan['links']:
        if l['id'] == 'link:golem_lane':
            l['features'] = ['a plank footbridge over the river at (97.5, 63)']
    # the edges are sealed until X3 and X6 exist: their ways in go (lanes/README; X2 did the same)
    sealed = (() if X3_LIVE else ('edge:east',)) + (() if X6_LIVE else ('edge:north',))
    plan['entrances'] = [e for e in plan['entrances'] if e.get('neighbour') not in sealed]
    plan['entrances'] = [e for e in plan['entrances'] if e['id'] not in ('entrance:xd22_pagoda', 'entrance:xd23_warren',
                                                                           'entrance:fd03_tower')]
    if FD03_LIVE:     # D-57: the tower door into FD-03 and its way back out (named after FD-03, lanes/README)
        plan['entrances'].append({'id': 'entrance:fd03_door', 'space': 'zone:darkstone_isle', 'kind': 'both',
                                  'facing': 'n',
                                  'how': "Darkstone Tower's door (FD-03, A7): A3's m41.tower_door opens it; FD-03's "
                                         "way out lands here on the rock top, facing north toward Winterkill."})
    # D-56: P5 Clouds of the Ancients falls to Darkstone's rock (A3's Xeen.skyFall), facing the tower door
    if not any(e['id'] == 'entrance:p5_fall' for e in plan['entrances']):
        plan['entrances'].append({'id': 'entrance:p5_fall', 'space': 'zone:darkstone_isle', 'kind': 'both',
                                  'facing': 's',
                                  'how': "P5's fall (D-56): on Darkstone's rock top (1,500) before the tower door, "
                                         "256 and more of flat rock to every edge; off by the door (FD-03, after "
                                         "M41) or the 700 drop to the ice."})
    for e in plan['entrances']:
        if e['id'] == 'entrance:xd10_south':
            e['how'] = ("A low mouth in the spur's west face among the firs (D-6.1): the pocket's second way west; "
                        "only A-tier trolls within 6 cells.")
            e['facing'] = 'w'
        if e['id'] == 'entrance:winterkill_square':
            e['how'] = 'Town Portal, the mirror (house 4256, opens with q-c6.done), the respawn; tests start here.'
    for v in plan['sightlines']:
        if v['from'] == 'entrance:east_road':
            v['from'] = 'zone:arrival_meadow'
    plan['critical_path'] = ['entrance:winterkill_square', 'zone:golem_rocks', 'zone:cave_north']
    for g in plan['goals']:
        pass
    plan['pitch'] = plan['pitch'].replace('the Frostspine walls off a gentler pocket',
                                          'the Frostspine and its cliffed spur wall off a gentler pocket')
    plan.pop('totals', None)
    plan['sketch'] = {'file': 'sketch.yml', 'grid': 512}
    plan['notes'] = ('L3/L4 written by output/studio_cal/x5/tools/gen.py from the approved L1 and D-6.1, D-6.3, D-6.5. '
                     'The plan keeps the L1 spaces; the pocket\'s wolves are placed actors (Act II), the west\'s are '
                     'slot 1 markers.')
    # ================================ sketch.yml
    rim = [
        {'side': 'west', 'form': 'level', 'height': 0, 'meet': 1,
         'notes': 'The world rim: the land ends in a cliff at x 24; below, water at 0 stands for the stars.'},
        {'side': 'south', 'form': 'level', 'height': 0, 'meet': 1,
         'notes': 'The world rim: the cliff at y 104; the glacier breaks off over it at x 28-40.'},
        {'side': 'north', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1},
        {'side': 'north', 'span': [24, 45], 'form': 'ridge', 'height': [1900, 2700], 'floor': 1500, 'crest': 10,
         'roughness': 100, 'notes': 'Stony rises toward the desert.'},
        {'side': 'north', 'span': [45, 56], 'form': 'level', 'height': 1460, 'meet': 6,
         'notes': ("The steppe road's valley runs out to the edge (X6's south edge [45, 56], level, the same x)."
                   if X6_LIVE else "The steppe road's valley runs out to the edge (X6, sealed).")},
        {'side': 'north', 'span': [56, 128], 'form': 'ridge', 'height': [2000, 3200], 'floor': 1600, 'crest': 10,
         'roughness': 100, 'notes': "The Frostspine's north end and the Ogre Hills' backs."},
        {'side': 'east', 'span': [0, 52], 'form': 'ridge', 'height': [1800, 2600], 'floor': 1400, 'crest': 10,
         'roughness': 100, 'notes': 'The Ogre Hills go on.'},
        {'side': 'east', 'span': [52, 104], 'form': 'level', 'height': 900, 'meet': 6,
         'notes': "The river valley and the fen run on to X3's lagoon (sealed)."},
        {'side': 'east', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1},
    ]
    # the rim cliffs, in stretches by the height of the land at the lip
    def rim_cliffs():
        out = [{'line': [[RIM_X, 0], [RIM_X, 33]], 'drop': 1450, 'down': 'right', 'notes': 'The rim, west: the plateau.'},
               {'line': [[RIM_X, 33], [RIM_X, 50]], 'drop': 1150, 'down': 'right',
                'notes': 'The rim, west: by Winterkill and the Edge Watch.'},
               {'line': [[RIM_X, 50], [RIM_X, 84]], 'drop': 1000, 'down': 'right', 'notes': 'The rim, west: the snowfields.'},
               {'line': [[RIM_X, 84], [RIM_X, RIM_Y]], 'drop': 2000, 'down': 'right',
                'notes': "The rim, west: the giants' crag."},
               {'line': [[RIM_X, RIM_Y], [28, RIM_Y]], 'drop': 2000, 'down': 'right'},
               {'line': [[28, RIM_Y], [41, RIM_Y]], 'drop': 1900, 'down': 'right',
                'notes': "The glacier's lip: the ice breaks off over the stars (the signature view)."},
               {'line': [[41, RIM_Y], [54, RIM_Y]], 'drop': 2000, 'down': 'right'},
               {'line': [[54, RIM_Y], [80, RIM_Y]], 'drop': 1250, 'down': 'right', 'notes': "The forest's lip."},
               {'line': [[80, RIM_Y], [87, RIM_Y]], 'drop': 2200, 'down': 'right', 'notes': "The spur's end."},
               {'line': [[87, RIM_Y], [128, RIM_Y]], 'drop': 950, 'down': 'right', 'notes': "The fen's lip."}]
        return out
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its land function.'},
        'points': [
            {'at': [82, 46], 'h': 1700, 'notes': "The pass crest, Freeda's camp (D-6.1: the notch at 1,700)."},
            {'at': [83, 24], 'h': 4000, 'notes': 'The Frostspine high peak.'},
            {'at': [82, 12], 'h': 3700}, {'at': [82, 36], 'h': 3800}, {'at': [82, 53], 'h': 3400},
            {'at': [28, 89], 'h': 3400, 'notes': 'The west crag.'},
            {'at': [50, 94], 'h': 3600, 'notes': 'The east crag.'},
            {'at': [35, 87], 'h': 2900, 'notes': "The glacier's head (D-6.5)."},
        ],
        'ridges': [
            {'line': [[82, 0], [82, 6], [82, 12], [82.5, 18], [83, 24], [82.5, 30], [82, 36], [82, 40], [82, 43]],
             'height': [3000, 3300, 3700, 3200, 4000, 3300, 3800, 3000, 2300], 'width': 2, 'slope': 4,
             'notes': 'The Frostspine crest north of the pass, broken into peaks (D-6.1).'},
            {'line': [[82, 49], [82, 51], [82, 53], [81.5, 56], [81, 59]], 'height': [2200, 2800, 3400, 3100, 2900],
             'width': 2, 'slope': 4, 'notes': 'The Frostspine south of the pass, down to the gorge.'},
            {'line': SPUR, 'height': SPUR_H, 'width': 3, 'slope': 2,
             'notes': ('D-6.1: the spur from the gorge\'s south shoulder to the rim, crest about 2,800, its sides '
                       'sheer (no crossing; the pocket\'s ways west are the pass road and XD-10).')},
            {'line': ICEFALL, 'height': ICEFALL_H, 'width': 7, 'slope': 2,
             'notes': ("The icefall (D-6.5): the glacier's north lobe off the plateau to its snout on the snowfield, "
                       "seen from the south track, Glom's fork and the Shrine of Cold.")},
            {'line': [[69, 61], [72.5, 61], [76, 61]], 'height': ICE, 'width': 3, 'slope': 2,
             'notes': 'The frozen river below the gorge: land at 800 painted ice (D-6.3).'},
            {'line': [[94, 41], [99, 41]], 'height': 2000, 'width': 3, 'slope': 3,
             'notes': "The hill the cave's north mouth is cut into."},
            {'line': [[79.5, 60.0], [85, 60.2]], 'height': 2400, 'width': 1, 'slope': 2,
             'notes': "The gorge's north wall."},
            {'line': [[79.5, 63.4], [85, 63.6]], 'height': 2000, 'width': 1, 'slope': 2,
             'notes': "The gorge's south wall, running into the spur."},
        ],
        'terraces': [
            {'polygon': [[29, 34.5], [46, 34.5], [46, 48], [29, 48]], 'height': TOWN_H, 'slope': 3,
             'notes': 'Winterkill.'},
            # F60 (X5 p4, 2026-11-25): east of x 110 the fen's land fell from 900 to 300-450 over its last four cells
            # to the rim while west of it the land ran level (928) to the lip, a 640 step under hull_049 (x 107-111):
            # the void showed under the piece. The fen runs level to its lip all the way to the east edge.
            {'polygon': [[106, 100], [128, 100], [128, 104], [106, 104]], 'height': 928, 'slope': 2,
             'notes': "The fen's lip east of the spur: level to the rim's hull (F60)."},
            {'polygon': MONASTERY, 'height': MONASTERY_H, 'slope': 3, 'notes': "Kai Wu's crag top."},
            {'polygon': [[92, 47], [100, 47], [100, 52.5], [92, 52.5]], 'height': 1350, 'slope': 3,
             'notes': "Halon's yard on its shoulder."},
            {'polygon': [[61, 44], [67.5, 44], [67.5, 49], [61, 49]], 'height': 1000, 'slope': 2,
             'notes': 'The pagoda shore.'},
            {'polygon': [[94, 44], [99, 44], [99, 47], [94, 47]], 'height': 1400, 'slope': 2,
             'notes': "The cave's north mouth: its floor."},
            {'polygon': [[98, 68], [103, 68], [103, 71], [98, 71]], 'height': 960, 'slope': 2,
             'notes': "The ground before the Golem Rocks' north face."},
            {'polygon': [[40.5, 98.5], [50, 98.5], [50, 103.2], [40.5, 103.2]], 'height': 2050, 'slope': 2,
             'notes': "The Reflector's ledge by the Waters of Great Magic: the signature view's floor."},
            {'polygon': [[42.5, 98.8], [44.5, 98.8], [44.5, 100.6], [42.5, 100.6]], 'height': 2350, 'slope': 2,
             'notes': ("The lookout on the ledge (D-6.5, session 6): a knoll 300 over the Waters' ledge, so the "
                       'signature view looks down the glacier rather than along its edge.')},
            {'polygon': [[103, 55], [110, 55], [110, 60], [103, 60]], 'height': 900, 'slope': 2,
             'notes': 'The lagoon road\'s end: the X3 arrival meadow.'},
            {'polygon': [[98, 72], [103, 72], [103, 74], [98, 74]], 'height': 1420, 'slope': 0,
             'notes': "The Golem Rocks' north face over the slab door."},
            {'polygon': [[71, 39], [75, 39], [75, 42], [71, 42]], 'height': 1200, 'slope': 2,
             'notes': "The monastery's foot."},
        ],
        'cliffs': rim_cliffs() + [
            {'line': [[64, 37], [75, 37]], 'drop': 700, 'down': 'right',
             'notes': "Kai Wu's crag, its south face over the road (the stair climbs it)."},
            {'line': [[98, 72], [103, 72]], 'drop': 450, 'down': 'left',
             'notes': "The Golem Rocks' north face with the slab door."},
        ],
        'peaks': [
            {'polygon': [[97, 73], [105, 73], [105, 79], [97, 79]], 'count': 5, 'height': [1450, 1800],
             'radius': [1.5, 2.5], 'profile': 'cone', 'spacing': 2, 'seed': 3,
             'notes': 'The Golem Rocks: a knot of grey stone behind the face.'},
            {'polygon': [[80, 67], [85, 67], [86, 102], [82, 102]], 'count': 9, 'height': [2900, 3400],
             'radius': [1.5, 2.5], 'profile': 'cone', 'spacing': 3, 'seed': 5,
             'notes': "The spur's crest broken into tops (D-6.1)."},
            {'polygon': [[79, 2], [85, 2], [85, 41], [79, 41]], 'count': 10, 'height': [3300, 4000],
             'radius': [2, 3.5], 'profile': 'cone', 'spacing': 3, 'seed': 7,
             'notes': 'The Frostspine crest broken into peaks (D-6.1).'},
            {'polygon': [[79, 50], [85, 50], [85, 57], [79, 57]], 'count': 3, 'height': [3100, 3500],
             'radius': [2, 3], 'profile': 'cone', 'spacing': 3, 'seed': 9},
            {'polygon': [[25, 85], [33, 85], [32, 96], [25, 96]], 'count': 4, 'height': [2900, 3500],
             'radius': [2, 3], 'profile': 'cone', 'spacing': 3, 'seed': 11, 'notes': "The giants' west crags."},
            # F59 (X5 p8/p9, 2026-11-25): the field began at x 45, so its cones (raised after the terraces) climbed
            # through the outpost's level pad and its east fence: now from x 49.5, the bases reaching x 47 at most
            {'polygon': [[49.5, 86], [54, 86], [54, 97], [49.5, 97]], 'count': 4, 'height': [2900, 3600],
             'radius': [1.5, 2.5], 'profile': 'cone', 'spacing': 3, 'seed': 13, 'notes': "The giants' east crags."},
        ],
        'nodes': [
            # D-56 (session 15): the top widened to x 53-57, y 58-63, so P5's fall lands on flat rock (a terrace
            # 1,000 deep before the tower door, 256 and more to every edge) and the way off is the door or the drop
            {'at': [52, 57], 'unit': 32,
             'rows': [[28, 34, 36, 36, 36, 34, 28], [34, 47, 47, 47, 47, 47, 34], [36, 47, 47, 47, 47, 47, 36],
                      [36, 47, 47, 47, 47, 47, 36], [36, 47, 47, 47, 47, 47, 36], [36, 47, 47, 47, 47, 47, 36],
                      [34, 47, 47, 47, 47, 47, 34], [28, 34, 36, 36, 36, 34, 28]],
             'notes': "Darkstone's black rock in the ice: its top at 1,500 (x 53-57, y 58-63), sheer to the ice (800)."},
        ],
    }
    water = {
        'rivers': [
            {'id': 'water:river', 'line': RIVER_OPEN, 'width_cells': 2.5, 'level': RIVER,
             'notes': ('The Lagoon Water from X3: open and fast in the pocket, through the Frostspine gorge and 1,000 '
                       'past it (D-6.1); then frozen (a ridge of land at 800 painted ice) to the mere.')},
        ],
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0,
             'polygon': [[0, 0], [RIM_X - 1, 0], [RIM_X - 1, RIM_Y + 1], [128, RIM_Y + 1], [128, 128], [0, 128]],
             'notes': 'Below the rim: stands for the stars (the game draws no void).'},
        ],
    }
    roads = [
        {'link': 'link:lagoon_road', 'line': LAGOON_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:pass_road', 'line': PASS_ROAD, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:pass_descent', 'line': PASS_DESCENT, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:shore_road', 'line': SHORE_ROAD, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:steppe_road', 'line': STEPPE_ROAD, 'width': 'road', 'surface': 'soil_stony'},
        {'link': 'link:winterkill_road', 'line': WINTERKILL_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:hill_track', 'line': HILL_TRACK, 'width': 'lane'},
        {'link': 'link:golem_lane', 'line': GOLEM_LANE, 'width': 'lane',
         'notes': 'Over the river by the plank footbridge (thing:golem_bridge); no tiles in the water.'},
        {'link': 'link:pagoda_path', 'line': PAGODA_PATH, 'width': 'lane'},
        {'link': 'link:south_track', 'line': SOUTH_TRACK, 'width': 'lane'},
        {'link': 'link:druid_path', 'line': DRUID_PATH, 'width': 'lane'},
        {'link': 'link:glom_lane', 'line': GLOM_LANE, 'width': 'lane'},
        {'link': 'link:giants_path', 'line': GIANTS_PATH, 'width': 'lane'},
        {'link': 'link:forest_track', 'line': FOREST_TRACK, 'width': 'lane'},
        {'link': 'link:rim_walk', 'line': RIM_WALK, 'width': 'lane'},
        {'link': 'link:thickbark_path', 'line': THICKBARK_PATH, 'width': 'lane'},
        {'link': 'link:cave_south_path', 'line': CAVE_SOUTH_PATH, 'width': 'lane'},
    ]
    POCKET = [[86, 19], [109, 19], [109, 104], [85, 104], [85, 66], [86, 60]]
    districts = [
        {'space': 'town:winterkill', 'polygon': TOWN_POLY, 'plots': plots_by_space['town:winterkill']},
        {'space': 'zone:winterkill_square', 'polygon': SQUARE},
        {'space': 'town:monastery', 'polygon': MONASTERY, 'plots': plots_by_space['town:monastery']},
        {'space': 'town:glom', 'polygon': [[42, 78.5], [48, 78.5], [48, 83], [42, 83]],
         'plots': plots_by_space['town:glom']},
        {'space': 'zone:halon_yard', 'polygon': [[92, 47], [100, 47], [100, 52.5], [92, 52.5]],
         'plots': plots_by_space['zone:halon_yard']},
        {'space': 'zone:pocket', 'polygon': POCKET},
        {'space': 'zone:ogre_hills', 'polygon': [[87, 19], [109, 19], [109, 53], [100, 54], [92, 55], [87, 52]]},
        {'space': 'zone:lagoon_marches', 'polygon': [[86, 66], [109, 66], [109, 104], [86, 104]]},
        {'space': 'zone:arrival_meadow', 'polygon': [[100, 54], [109, 54], [109, 61], [100, 61]]},
        {'space': 'zone:golem_rocks', 'polygon': [[96, 70], [105, 70], [105, 79], [96, 79]]},
        {'space': 'zone:cave_north', 'polygon': [[93, 41], [99, 41], [99, 46.5], [93, 46.5]]},
        {'space': 'zone:frostspine', 'polygon': [[77, 0], [87, 0], [87, 104], [79, 104], [78, 64], [77, 58]]},
        {'space': 'zone:pass', 'polygon': [[79, 43], [85, 43], [85, 49], [79, 49]]},
        {'space': 'zone:steppe', 'polygon': [[36, 19], [77, 19], [77, 58], [70, 60], [68, 56], [63, 52], [56, 50],
                                             [47, 50], [48, 40], [48, 33], [36, 32]]},
        {'space': 'zone:west_plateau', 'polygon': [[24, 19], [36, 19], [36, 32], [28, 33], [28, 48.5], [24, 50]]},
        {'space': 'zone:snowfields', 'polygon': [[24, 50], [29.5, 48.5], [37, 50], [40, 53], [39, 61], [43, 68],
                                                 [50, 71], [60, 70], [67, 66], [70, 61], [77, 60], [78, 64], [54, 76],
                                                 [52, 84], [24, 84]]},
        {'space': 'zone:druid_grove', 'polygon': [[27, 58], [33, 58], [33, 64], [27, 64]]},
        {'space': 'zone:darkstone_isle', 'polygon': [[52, 57], [58, 57], [58, 64], [52, 64]]},
        {'space': 'zone:pagoda_shore', 'polygon': [[61, 44], [67.5, 44], [67.5, 49], [61, 49]]},
        {'space': 'zone:troll_forest', 'polygon': [[54, 76], [78, 65], [79, 66], [80, 104], [52, 104], [52, 86]]},
        {'space': 'zone:giants', 'polygon': [[24, 84], [52, 84], [52, 104], [24, 104]]},
        {'space': 'zone:glacier', 'polygon': [[31, 85], [40, 85], [41, 92], [40, 104], [28, 104], [29, 94]]},
        {'space': 'zone:rim', 'polygon': [[0, 0], [RIM_X, 0], [RIM_X, RIM_Y], [128, RIM_Y], [128, 128], [0, 128]]},
    ]
    points = [
        {'id': 'entrance:winterkill_square', 'at': [37, 41.5], 'facing': 's'},
        {'id': 'entrance:p5_fall', 'at': [55, 59], 'facing': 's'},   # whole cells: (55, 60) is inside the tower's base
        *([{'id': 'entrance:fd03_door', 'at': [55, 59], 'facing': 'n'}] if FD03_LIVE else []),
    ] + ([{'id': 'entrance:east_road', 'at': list(EAST_START), 'facing': 'w'}] if X3_LIVE else []) + (
        [{'id': 'entrance:north_road', 'at': list(NORTH_START), 'facing': 's'}] if X6_LIVE else []) + [
        {'id': 'entrance:xd09_door', 'at': [XD09_DOOR[0], XD09_DOOR[1] - 0.8], 'facing': 's'},
        {'id': 'entrance:xd10_north', 'at': [XD10_NORTH[0], XD10_NORTH[1] + 0.9], 'facing': 'n'},
        {'id': 'entrance:xd10_south', 'at': [XD10_SOUTH[0] - 0.9, XD10_SOUTH[1]], 'facing': 'e'},
        {'id': 'junction:lagoon_fork', 'at': [98, 60]}, {'id': 'junction:pass_crest', 'at': [82, 46]},
        {'id': 'junction:monastery_foot', 'at': [73, 40]}, {'id': 'junction:steppe_cross', 'at': [50, 35]},
        {'id': 'junction:glom_fork', 'at': [42, 77]},
        {'id': 'landmark:frostspine', 'at': [83, 24]}, {'id': 'landmark:darkstone', 'at': [55, 61]},
        {'id': 'landmark:monastery', 'at': [69, 31]}, {'id': 'landmark:pagoda', 'at': [64.5, 46.5]},
        {'id': 'landmark:halon_clock', 'at': [96, 48]}, {'id': 'landmark:glacier', 'at': [34, 100]},
    ]
    for p in L1['spaces']:
        pass
    POI_AT = {
        'poi:obelisk': (58.5, 42.5), 'poi:fountain_great_protection': (30, 29), 'poi:waters_great_magic': (46.5, 100.5),
        'poi:shrine_cold': (53, 74.4), 'poi:well_intellect': (105.5, 56.5), 'poi:well_accuracy': (60, 30),
        'poi:hot_spring': (104, 66.6), 'poi:winterkill_well': (39.0, 43.6), 'poi:randon': (36.6, 43.0),
        'poi:thickbark': (73.6, 69.6), 'poi:winter_druid': (30.4, 61.6), 'poi:freeda': (82.8, 45.0),
        'poi:holy_book': (68.6, 92.4), 'poi:earth_reflector': (40.0, 102.6), 'poi:cyclops_outpost': (44, 93),
        'poi:barbarian_camp': (42, 25), 'poi:hunting_camp': (66, 22), 'poi:ogre_camp': (101, 37),
        'poi:archer_camp': (104, 86), 'poi:frozen_sledge': (89.6, 53.4), 'poi:trapper': (92, 90),
        'poi:frozen_pack': (60.6, 65.6), 'poi:giants_cairn': (50, 87), 'poi:giant_stones': (37, 85),
        'poi:ice_fishing': (47, 58), 'poi:edge_watch': (26, 41)}
    for k, at in POI_AT.items():
        points.append({'id': k, 'at': list(at)})
    for i, at in enumerate([(35.8, 39.5), (38.2, 39.5), (35.4, 44.2)]):
        points.append({'id': 'poi:gongs', 'index': i + 1, 'at': list(at)})
    for i, at in enumerate([(98, 60), (82, 46), (73, 40), (50, 35), (42, 77)]):
        points.append({'id': 'poi:signposts', 'index': i + 1, 'at': list(at)})
    # ---------------------------------------------------------------- encounter areas
    areas = []
    def markers(pop, spots, slot=None):
        for (cx, cy, n, r) in spots:
            k = sum(1 for a in areas if a['id'] == pop) + 1
            a = {'id': pop, 'index': k, 'kind': 'encounter', 'count': n, 'circle': {'at': [cx, cy], 'r': r}}
            if slot:
                a['slot'] = slot
            areas.append(a)
    # the snowfields (slot 1, Dark Wolves): packs round the west and south shores, the shrine, the fishing hole's
    # shore; none in the town buffer. D-85 (A6 s30): the three packs by the druid's grove moved south, every circle
    # at least 5,888 from the Winter Druid (was (28, 55), (27, 68), (34, 70): 3,250-5,011)
    # F10 (s32): the lone wolf at (41, 72) moved to the empty east-centre below the pass (80, 57)
    markers('pop:snow_beasts', [(28, 78, 2, 1.5), (56, 73, 2, 1.5), (80, 57, 1, 1), (45, 74, 2, 1.5),
                                (36, 80, 2, 1.5), (68, 52, 2, 1.5)])   # s32 F10: (60, 71) to the centre
    # s33 (A5's P5 relay): the centre pack from (63, 55) to (68, 52): its edge was ~3,800 from P5's fall landing
    # (entrance:p5_fall (55, 59)) and the wolves killed the party inside P5's 20 s fall checks; now 6,800 (D-15's
    # 6,000 from a dungeon-exit arrival), checked below
    # the steppe (slot 2): west of the road round the camp, east of it round the hunting camp; D-6.1: nothing within
    # 2,000 of the pass descent or the monastery foot (and only tier A within 4,000: none at all there)
    # F63 (2026-11-25): (39, 21) and (63, 20) put their spawns 578 and 226 from the map's north bound: in to 22.5, 22
    markers('pop:barbarians', [(39, 22.5, 2, 1.5), (39, 27, 1, 1), (45, 22, 2, 1.5), (57, 24, 2, 1.5),
                               (63, 22, 1, 1), (69, 26, 2, 1.5)])
    # the Troll Forest (slot 3): none within 6 cells of XD-10's south mouth (D-6.1)
    markers('pop:trolls', [(58, 79, 2, 1.5), (67, 80, 2, 1.5), (61, 88, 2, 1.5), (56, 96, 2, 1.5),
                           (64, 100, 2, 1.5), (71, 93, 3, 1.5), (73, 99, 1, 1)])
    # D-142 (2026-11-25, F64): 4,096 from the edge arrivals and (X5 rebuilt under the rule) the dungeon exits, the
    # circle's edge; centres 1,024 from the roads and lanes. A failing circle moves to the nearest passing spot that
    # also keeps this map's rules below (common/d142.py; the moves print as `D-142:`)
    d142_enforce(areas)
    for a in areas:
        c = a['circle']['at']
        # F63 (X6 p4): a circle's edge at least 768 (1.5 cells) from the map's bounds (+-23,106) and the rim's hull
        lo, hi = 64 - 23106 / 512, 64 + 23106 / 512
        if min(c[0] - max(lo, RIM_X), hi - c[0], c[1] - lo, min(hi, RIM_Y) - c[1]) - a['circle']['r'] < 1.5:
            raise SystemExit('a marker circle within 768 of the bounds or the hull: %s %s' % (a['id'], c))
        if (math.hypot(c[0] - 55, c[1] - 59) - a['circle']['r']) * 512 < 6000:
            raise SystemExit('a marker within 6,000 of P5\'s fall landing (55, 59): %s %s' % (a['id'], c))
        if a['id'] == 'pop:trolls' and math.hypot(c[0] - XD10_SOUTH[0], c[1] - XD10_SOUTH[1]) < 6:
            raise SystemExit('troll marker within 6 cells of XD-10 south: %s' % c)
        if a['id'] == 'pop:barbarians':
            for q in PASS_DESCENT:
                if math.hypot(c[0] - q[0], c[1] - q[1]) * 512 < 4000:
                    raise SystemExit('barbarian marker within 4,000 of the pass descent: %s' % c)
        # D-85: no marker circle within missile range (5,120) of an outdoor talking giver outside Winterkill's fight
        # (output/studio_cal/a6/s30/d85.py measures the built markers and placed packs against 5,120 and 5,888)
        for who, g in (('the Winter Druid', POI_AT['poi:winter_druid']), ('Freeda', POI_AT['poi:freeda']),
                       ('Thickbark', POI_AT['poi:thickbark'])):
            if (math.hypot(c[0] - g[0], c[1] - g[1]) - a['circle']['r']) * 512 < 5120:
                raise SystemExit('D-85: a marker within 5,120 of %s: %s %s' % (who, a['id'], c))
        near = min(math.hypot(c[0] - d[2][0], c[1] - d[2][1]) for d in doors_out
                   if d[0].startswith('building:winterkill') or d[0] == 'building:mindmeld_guild')
        if near * 512 < 4500:
            raise SystemExit('monsters within 4,500 of a Winterkill door: %s %s' % (a['id'], c))
    areas += [
        {'id': 'town:winterkill', 'kind': 'keep_clear', 'polygon': [[25, 30], [52, 30], [52, 50], [37, 54], [25, 52]]},
        {'id': 'town:monastery', 'kind': 'keep_clear', 'polygon': [[62, 25], [78, 25], [78, 44], [62, 44]]},
        {'id': 'zone:druid_grove', 'kind': 'keep_clear', 'polygon': [[27, 58], [33, 58], [33, 64], [27, 64]]},
        {'id': 'town:glom', 'kind': 'keep_clear', 'polygon': [[40, 78], [50, 78], [50, 85], [40, 85]]},
        {'id': 'zone:pass', 'kind': 'keep_clear', 'polygon': [[78, 40], [88, 40], [88, 52], [78, 52]]},
        {'id': 'zone:arrival_meadow', 'kind': 'keep_clear', 'polygon': [[100, 54], [112, 54], [112, 62], [100, 62]]},
        # D-56: P5's fall lands on Darkstone's rock (entrance:p5_fall); nothing hostile on or round it
        {'id': 'zone:darkstone_isle', 'kind': 'keep_clear', 'polygon': [[51, 56], [59, 56], [59, 65], [51, 65]]},
        {'id': 'zone:west_plateau', 'kind': 'open', 'polygon': [[24, 19], [36, 19], [36, 30], [24, 30]]},
        {'id': 'water:mere', 'kind': 'open', 'polygon': MERE},
    ]
    views = [
        {'id': 'view:arrival', 'at': [106, 59], 'height': 180, 'look': [84, 54],
         'purpose': "From the X3 arrival: the river west into the gorge, the pass notch, Halon's clock on the right."},
        {'id': 'view:glacier', 'at': [43.5, 99.7], 'height': 200, 'look': [31, 102],
         'purpose': "The signature view (D-6.5): the glacier breaking off the rim, the Reflector on its spur."},
        {'id': 'view:mere', 'at': [58, 43], 'height': 180, 'look': [55, 61], 'purpose': 'Darkstone across the ice.'},
    ]
    structures = []
    S = structures.append
    # ---------------------------------------------------------------- Winterkill square
    S({'id': 'thing:square_court', 'kind': 'platform', 'at': [37.0, 41.5], 'size': [3072, 3584], 'height': 16,
       'textures': {'top': 'cnb', 'wall': 'cnb'}, 'title': 'Winterkill square',
       'notes': "The square's paving under the snow."})
    def ring(at, sound):
        # AU's gongs (devdocs/xeen/AUDIO.md), at the gong board's centre: the square's paving + 160
        x, y = (at[0] - 64) * 512, (64 - at[1]) * 512
        return {'lua': 'evt.PlaySoundName("%s", %d, %d, %d)' % (sound, x, y, GONG_Z)}
    def gong(gid, at, effects, title, condition=None, else_effects=None):
        # texture fit: the gong picture once on a square board (a 224 x 96 board cut it in half)
        g = {'id': gid, 'kind': 'sign', 'at': list(at), 'height': 352, 'width': 192, 'board_height': 192,
             'title': title,
             'textures': {'wall': 'trim11_32', 'board': 'xngong'}, 'effects': effects}
        if condition:
            g['condition'] = condition
            g['else_effects'] = else_effects
        return g
    for i, at in enumerate([(35.8, 39.5), (38.2, 39.5)]):
        S(gong('thing:north_gong_%d' % (i + 1), at,
               [ring(at, GONG_SOUNDS[i]),
                {'set': {'var': {'map_var': 'north_gong_%d_twice' % (i + 1)}, 'value': 1}}, {'text': 'BONG!'}],
               'Northern gong', condition={'map_var': 'north_gong_%d' % (i + 1)},
               else_effects=[ring(at, GONG_SOUNDS[i]), {'set': {'var': {'map_var': 'north_gong_%d' % (i + 1)},
                                                                 'value': 1}},
                             {'text': 'BONG!'}]))
    S(gong('thing:south_gong', (35.4, 44.2), [ring((35.4, 44.2), 'xeen_gong')] + hook('q-c6.gong'),
           'Southern gong'))
    S(sign('thing:gong_plaque', (37.0, 39.3), 'Plaque', effects=hook('q-c6.north_gongs_verse'), height=160,
           width=128))
    S(sign('thing:randon_board', (34.6, 44.3), 'Signboard', effects=hook('q-c6.signboard')))
    # the old strength well: frozen until the town is free; then +Might for those who rang each northern gong twice
    S(K.well('thing:strength_well', (39.0, 43.6), roofed=True, title='The old well'))
    structures[-1]['condition'] = {'all': [{'qbit': 'winterkill_liberated'},
                                           {'map_var': 'north_gong_1_twice'}, {'map_var': 'north_gong_2_twice'}]}
    structures[-1]['effects'] = [{'set': {'var': 'MightBonus', 'value': 25}}, {'text': '+25 Might (temporary)'}]
    structures[-1]['else_effects'] = [{'text': 'The well is frozen solid.'}]
    S({'id': 'thing:mirror', 'kind': 'portal', 'at': [34.8, 42.6], 'radius': 112, 'sides': 12, 'turn': 90,
       'textures': {'membrane': {'texture': 'xmirror'}}, 'title': 'Magic Mirror',
       'effects': [{'lua': 'Xeen.useMirror(%d, eventId, continueStep)' % HOUSE_MIRROR}],
       'notes': "Winterkill's mirror (A4's 4256, opens with q-c6.done)."})
    # the Acme Ghost Visualization System: a lens-and-crank machine on a stand by the temple (q-c6.acme_sign)
    S({'id': 'thing:acme_machine', 'kind': 'building', 'at': [39.2, 38.3], 'size': [0.75, 0.5], 'kit': 'grey',
       'door': 'none', 'title': 'A strange machine', 'floor': TOWN_H + 16,
       'parts': [{'id': 'stand', 'at': [96, 64], 'size': [192, 128], 'wall_height': 160, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 'trim11_32', 'roof': 'trim11_32'}},
                 {'id': 'lens', 'shape': 'round', 'at': [192, 128], 'radius': 56, 'sides': 8, 'bottom': 160,
                  'wall_height': 112, 'roof': 'flat', 'windows': 'none',
                  'textures': {'wall': 'xngong', 'roof': 'xngong'}, 'title': 'Acme Ghost Visualization System',
                  'effects': hook('q-c6.acme_sign')}]})
    # the cursed chest by the temple: shut until the town is free (q-c6.ghost_verse)
    S({'id': 'thing:ghost_chest', 'kind': 'chest', 'at': [35.95, 37.95], 'title': 'Cursed chest',
       'chest': {'level': 4, 'random_items': 3}, 'condition': {'qbit': 'winterkill_liberated'},
       'else_effects': hook('q-c6.ghost_verse')})
    # the broken palisade round the town (gaps where the ways go out and where it fell)
    for i, line in enumerate([[[28.5, 34], [33, 33.6]], [[34.5, 33.6], [40, 33.8]], [[42, 34], [44.5, 34.2]],
                              [[48.2, 36.5], [48.4, 37.6]], [[47.6, 43], [47, 46.5]], [[45, 48.5], [39.8, 49.6]],
                              [[34.2, 49.6], [30.5, 48.7]], [[28.4, 47], [28.3, 43.2]], [[28.4, 39.8], [28.6, 35.5]]]):
        S(K.fence('thing:palisade_%d' % (i + 1), line))
    # dressing (DRESSING.md): pairs against walls, none before a door; snowed-up woodpiles and casks
    # final cloud round: the tavern's pair half a cell west with the tavern (33.3 -> 32.8)
    for i, (d, at) in enumerate([('bigbarel', (32.8, 36.15)), ('bigbarel', (32.8, 36.5)),     # the tavern's west wall
                                 ('7dec32', (41.7, 36.6)), ('7dec32', (41.7, 36.95)),         # the furrier's east wall (MM7's barrel; 7dec24 is a campfire)
                                 ('haybale2', (47.2, 36.2)), ('haybale2', (47.2, 36.55)),    # the woodcutter's barn
                                 ('7dec32', (31.3, 39.0)), ('7dec32', (31.3, 39.35))]):     # the guild's back wall
        S(deco('thing:prop_%d' % (i + 1), d, at))
    # the town's trees: a few snowy firs in yards
    # ---------------------------------------------------------------- the Edge Watch and the rim plateau
    S({'id': 'thing:edge_watch', 'kind': 'building', 'at': [25.2, 40.2], 'size': [1.6, 1.6], 'kit': 'castle',
       'door': 'none', 'title': 'The Edge Watch', 'ruin': {'height': [192, 640], 'gaps': 0.35, 'thickness': 48, 'seed': 4},
       'parts': [{'id': 't', 'shape': 'round', 'at': [410, 410], 'radius': 288, 'sides': 10, 'wall_height': 640,
                  'roof': 'none', 'windows': 'none', 'textures': {'wall': 'cnb'}}]})
    S(sign('thing:edge_note', (26.9, 42.3), 'An old note',
           "Nailed to the post, in a soldier's hand: \"Day nine hundred. Still no sign of the edge getting any "
           "closer. Or any further. Watch relieved by nobody.\""))
    S({'id': 'thing:fountain_protection', 'kind': 'fountain', 'at': [30, 29], 'title': 'Fountain of Great Protection',
       'tiers': [[96, 48]], 'textures': {'wall': 'cnb'},
       'effects': [{'set': {'var': 'ArmorClassBonus', 'value': 20}}, {'text': '+20 Armor class (temporary)'}]})
    # ---------------------------------------------------------------- the steppe
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [58.5, 42.5], 'height': 768, 'title': 'Obelisk',
       'effects': hook('obelisks.x5')})          # A3: the word FOR, the bit cloud_5, the autonote
    S(K.well('thing:well_accuracy', (60, 30), title='Well of Accuracy'))
    structures[-1]['effects'] = [{'set': {'var': 'AccuracyBonus', 'value': 20}}, {'text': '+20 Accuracy (temporary)'}]
    for cid, (x, y), n in (('camp', (42, 25), 2), ('hunt', (66, 22), 1)):
        S({'id': 'thing:%s_tent' % cid, 'kind': 'tent', 'at': [x - 1.6, y - 1.0], 'size': [896, 704], 'height': 384,
           'open': True, 'title': 'Barbarian tent'})
        if n == 2:
            S({'id': 'thing:%s_tent2' % cid, 'kind': 'tent', 'at': [x + 0.9, y - 1.3], 'size': [768, 640],
               'height': 352, 'open': True, 'title': "The chief's tent",
               'condition': {'not': {'map_var': 'barbarian_camp_burnt'}},
               'effects': [{'set': {'var': {'map_var': 'barbarian_camp_burnt'}, 'value': 1}},
                           {'add': {'var': 'Experience', 'value': 3000}},
                           {'text': 'You set the barbarians\' tents alight. The furs go up like tinder. (+3,000 experience)'}],
               'else_effects': [{'text': 'Charred poles and wet ash.'}]})
        S(deco('thing:%s_fire' % cid, 'cmpfyr00', (x + 0.2, y + 0.8), title='Campfire'))
        S(deco('thing:%s_bones' % cid, '7dec18', (x - 1.0, y + 1.5)))
    S({'id': 'thing:camp_chest', 'kind': 'chest', 'at': [44.6, 23.9], 'title': "The chief's chest",
       'chest': {'level': 3, 'random_items': 3}})
    # the steppe road's end: sealed with a sign until X6 is installed; then a waymark beside the road (off its line)
    if X6_LIVE:
        S(sign('thing:north_road_end', (52.2, 21.6), 'Waymark', 'North: the Desert of the Sphinx.'))
    else:
        S(sign('thing:north_road_end', (50.9, 20.4), 'Sign',
               'The road north to the Desert of the Sphinx is buried under drifts. Turn back.'))
    # ---------------------------------------------------------------- the monastery
    S({'id': 'thing:monastery_stair', 'kind': 'stairs', 'line': [[70.6, 39.6], [70.6, 36.5]], 'width': 448,
       'rise': MONASTERY_H - 1200, 'textures': {'wall': 'cnb'}, 'notes': "The stair up Kai Wu's crag."})
    S({'id': 'thing:cloister_wall', 'kind': 'wall',
       'line': [[69.9, 36.3], [64.3, 36.3], [64.3, 27.3], [74.2, 27.3], [74.2, 36.3], [71.3, 36.3]],
       'height': 192, 'thickness': 96, 'textures': {'wall': 'cnb'}, 'title': 'Cloister wall',
       'notes': 'One wall round the court, open at the stair head.'})
    S({'id': 'thing:bell_frame', 'kind': 'building', 'at': [67.6, 33.4], 'size': [1, 1], 'kit': 'timber',
       'door': 'none', 'title': 'The monastery bell', 'floor': MONASTERY_H,
       'parts': [{'id': 'frame', 'at': [128, 128], 'size': [256, 256], 'wall_height': 416, 'posts': 32,
                  'roof': 'hip', 'roof_pitch': 45, 'windows': 'none', 'textures': {'roof': SLATE},
                  'title': 'The monastery bell', 'effects': [{'text': 'A deep, slow note rolls out over the tundra.'}]}]})
    # ---------------------------------------------------------------- the pass and the pocket
    S({'id': 'thing:freeda_tent', 'kind': 'tent', 'at': [83.4, 43.6], 'size': [640, 576], 'height': 320, 'open': True,
       'title': "Freeda's tent"})
    S(deco('thing:freeda_fire', 'cmpfyr00', (81.4, 44.6), title='Campfire'))
    # D-29 (session 7): the sledge's provisions, 6 food once (map variable `sledge_food`), and the chest as before.
    # The guard needs the variable's number, which the build gives the name (ids.lock.yml): run v.sh twice when new.
    _lock = os.path.join(OUT, 'ids.lock.yml')
    _mv = (yaml.safe_load(open(_lock)).get('map_vars') or {}).get('sledge_food') if os.path.exists(_lock) else None
    sledge_fx = [{'set': {'var': {'map_var': 'sledge_food'}, 'value': 1}}]
    if _mv is not None:
        sledge_fx.insert(0, {'lua': 'if not IsAtLeast(MapVar(%d), 1) then AddValue(Food, 6) '
                                    'evt.StatusText("Frozen provisions are still lashed to the runners. (+6 food)", 4) end'
                                    % _mv})
    else:
        print('X5: sledge_food has no number yet: run v.sh again', file=sys.stderr)
    S({'id': 'thing:frozen_sledge', 'kind': 'chest', 'at': [89.6, 53.4], 'title': "A trader's sledge",
       'chest': {'level': 2, 'random_items': 2}, 'effects': sledge_fx})
    S(deco('thing:sledge_bones', '7dec18', (90.2, 53.9)))
    S({'id': 'thing:halon_clock', 'kind': 'building', 'at': [95.6, 47.6], 'size': [1, 1], 'kit': 'timber',
       'door': 'none', 'title': "Halon's water clock", 'floor': 1350,
       # texture fit (the user, session 8): one row of windows in the belfry, a seamless rubble shaft below it
       'parts': [{'id': 'belfry', 'shape': 'round', 'at': [256, 256], 'radius': 208, 'sides': 10, 'bottom': 704,
                  'wall_height': 256, 'roof': 'cone', 'roof_pitch': 64, 'windows': 'alternate',
                  'textures': {'roof': SLATE, 'wall': 'hwm2b', 'window': 'hwm2bw', 'post_left': 'hwm2b',
                               'post_right': 'hwm2b'}},
                 {'id': 'tower', 'shape': 'round', 'at': [256, 256], 'radius': 208, 'sides': 10, 'wall_height': 704,
                  'roof': 'none', 'windows': 'none',
                  'textures': {'wall': 'hwm2wall', 'post_left': 'hwm2wall', 'post_right': 'hwm2wall'},
                  'title': "Halon's water clock",
                  'effects': [{'text': 'The water clock is stopped. Ice hangs from its wheel.'}]}]})
    S({'id': 'thing:halon_pond', 'kind': 'platform', 'at': [98.6, 50.5], 'size': [1024, 768], 'height': 8,
       'textures': {'top': '7snow', 'wall': 'cnb'}, 'title': "Halon's millpond",
       'effects': [{'text': 'The millpond is frozen to the bottom. No wonder the clock has stopped.'}],
       'notes': 'The frozen millpond (a slab of ice; the ice material is ground only).'})
    S({'id': 'thing:xd10_north', 'kind': 'cave_mouth', 'at': [XD10_NORTH[0], XD10_NORTH[1] - 1.5],
       'size': [1536, 1536], 'floor': 1400, 'mouth': {'width': 448, 'height': 384, 'depth': 75},
       'textures': {'shell': '7snow', 'door': '7solid01'}, 'roughness': 0.7, 'seed': 11,
       'title': 'Enter the Cave of Illusion', 'hint': 'Cave of Illusion',
       'into': {'map': 'xeen_xd10.blv', 'arrival': 'entrance:x5_north'},
       'crest': 480, 'notes': "XD-10's north mouth (D-4): warm, wet breath from it, ice at its lip."})
    S({'id': 'thing:xd09_door', 'kind': 'doorway', 'at': [XD09_DOOR[0], XD09_DOOR[1] - 0.25], 'turn': 180,
       'floor': 960,
       'height': 352, 'width': 256, 'depth': 384, 'hood': 64, 'arch': 'segment',
       'textures': {'door': '7solid01', 'wall': 'cwb1'}, 'title': 'Enter the Golem Dungeon',
       'into': {'map': 'xeen_xd09.blv', 'arrival': 'entrance:x5'}, 'condition': {'lua': 'XeenQuests.hook("m10.golem_door")'},
       'notes': "XD-09 (D-4): the slab door in the Golem Rocks' north face; opens with the Golem Stone."})
    S({'id': 'thing:golem_bridge', 'kind': 'bridge', 'line': [[97.5, 61.0], [97.5, 65.0]], 'width': 384, 'rise': 64,
       'kerb': 48, 'textures': {'deck': 'trim11_32'}, 'title': 'Footbridge'})
    S(K.well('thing:well_intellect', (105.5, 56.5), title='Well of Intellect'))
    structures[-1]['effects'] = [{'set': {'var': 'IntellectBonus', 'value': 20}}, {'text': '+20 Intellect (temporary)'}]
    S({'id': 'thing:hot_spring', 'kind': 'fountain', 'at': [104, 66.6], 'title': 'Hot spring', 'tiers': [[64, 24]],
       'textures': {'wall': 'cnb'},
       'effects': [{'add': {'var': 'HP', 'value': 100}}, {'text': 'Steam and warmth: +100 Hit points'}]})
    if not X3_LIVE:
        S(sign('thing:east_road_end', (108.6, 58.2), 'Sign',
               'The lagoon road east is under the flood. Turn back.'))
    for cid, (x, y), title in (('ogre', (101, 37), "The ogres' camp"), ('archer', (104, 86), "The archers' camp")):
        S({'id': 'thing:%s_tent' % cid, 'kind': 'tent', 'at': [x - 1.4, y - 1.2], 'size': [832, 640], 'height': 352,
           'open': True, 'title': title, 'condition': {'not': {'map_var': '%s_camp_burnt' % cid}},
           'effects': [{'set': {'var': {'map_var': '%s_camp_burnt' % cid}, 'value': 1}},
                       {'add': {'var': 'Experience', 'value': 1500}},
                       {'text': 'You burn the camp. (+1,500 experience)'}],    # F13: a touch's XP, the status line
           'else_effects': [{'text': 'Ash and a few charred bones.'}]})
        S(deco('thing:%s_fire' % cid, 'cmpfyr00', (x + 0.4, y + 0.9), title='Campfire'))
        S({'id': 'thing:%s_chest' % cid, 'kind': 'chest', 'at': [x + 1.6, y - 0.6], 'title': 'Chest',
           'chest': {'level': 2, 'random_items': 2}})
    S({'id': 'thing:trapper_shed', 'kind': 'building', 'at': [91.0, 89.0], 'size': [1.5, 1], 'kit': 'poor',
       'door': 'none', 'title': "A trapper's lean-to",
       'parts': [{'id': 'shed', 'at': [48, 48], 'size': [672, 416], 'wall_height': 224, 'roof': 'lean_to',
                  'posts': 24, 'windows': 'none'}]})
    S({'id': 'thing:trapper_chest', 'kind': 'chest', 'at': [92.3, 90.6], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 1}})
    S(deco('thing:trapper_fire', 'dec24x', (91.4, 90.8), title='A dead fire'))
    # ---------------------------------------------------------------- the mere
    S({'id': 'thing:darkstone', 'kind': 'building', 'at': [DARKSTONE_C[0] - 1.25, DARKSTONE_C[1] - 1.25],
       'size': [2.5, 2.5], 'kit': 'castle', 'floor': ISLE_H, 'title': 'Darkstone Tower', 'facing': 'n',
       'parts': [
           # texture fit (the user, session 8): hkm3b's frieze once per band, seamless gtrlwal1 between
           {'id': 'base', 'shape': 'round', 'at': [640, 640], 'radius': 544, 'sides': 10, 'wall_height': 896,
            'roof': 'none', 'windows': 'none',
            'textures': {'wall': 'gtrlwal1', 'door': '7solid01', 'post_left': 'gtrlwal1', 'post_right': 'gtrlwal1',
                         'window': 'gtrlwal1', 'trim': 'gtrlwal1'}},
           {'id': 'base_band', 'shape': 'round', 'at': [640, 640], 'radius': 544, 'sides': 10, 'bottom': 896,
            'wall_height': 256, 'roof': 'none', 'windows': 'none',
            'textures': {'wall': 'hkm3b', 'post_left': 'hkm3b', 'post_right': 'hkm3b', 'roof': 'gtrlwal1',
                         'trim': 'gtrlwal1', 'window': 'hkm3b'}},
           {'id': 'top', 'shape': 'round', 'at': [640, 640], 'radius': 448, 'sides': 10, 'bottom': 1152,
            'wall_height': 512, 'roof': 'none', 'windows': 'none',
            'textures': {'wall': 'gtrlwal1', 'post_left': 'gtrlwal1', 'post_right': 'gtrlwal1'}},
           {'id': 'top_band', 'shape': 'round', 'at': [640, 640], 'radius': 448, 'sides': 10, 'bottom': 1664,
            'wall_height': 256, 'roof': 'cone', 'roof_pitch': 74, 'windows': 'alternate',
            'textures': {'wall': 'hkm3b', 'window': 'hkm3elw', 'post_left': 'hkm3b', 'post_right': 'hkm3b',
                         'roof': SLATE}}],
       'door': {'part': 'base', 'wall': '5'},   # D-56 (session 15): the door on the north face, before P5's fall point
       # A3's m41.tower_door (session 7): the keyhole's refusal, or the black key's text; FD-03 is not built yet, so
       # the opened door then shows a sealed line (no exit to an unbuilt map)
       'condition': {'lua': 'XeenQuests.hook("m41.tower_door")'},
       **({'into': {'map': 'xeen_fd03.blv', 'arrival': 'entrance:x5_door'},
           'notes': 'FD-03 Darkstone Tower (A7): A3 m41.tower_door, then into FD-03 at entrance:x5_door.'}
          if FD03_LIVE else
          {'effects': [msg('Darkstone Tower is not open to you yet.')],
           'notes': 'FD-03 Darkstone Tower: A3 m41.tower_door; sealed until FD-03 is built (Act VI).'})})
    S({'id': 'thing:frozen_pack', 'kind': 'chest', 'at': [60.6, 65.6], 'title': 'A pack frozen into the ice',
       'chest': {'level': 3, 'random_items': 2}})
    S(deco('thing:fishing_stool', 'stump5a', (47.3, 58.4), title="Old Knut's fishing hole", once=True,
           effects=[{'add': {'var': 'Food', 'value': 3}},
                    {'text': "A line through a hole in the ice, and a fish on it. Old Knut won't mind. (+3 food)"}]))
    # the Ninja Pagoda: five storeys of dark timber and slate on the shore; XD-22 is built in phase 3: sealed
    PAG = []
    # texture fit (the user, session 8): each storey one 256 row, so the window bays are not stacked
    _storeys = [(0, 256), (96, 256), (192, 256), (288, 256), (352, 256)]
    for k, (inset, h) in enumerate(_storeys):
        bottom = sum(hh for _, hh in _storeys[:k])
        p = {'id': 'storey_%d' % (k + 1), 'at': [256 + inset, 256 + inset], 'size': [1536 - 2 * inset,
                                                                                      1024 - 2 * inset],
             'wall_height': h, 'roof': 'hip', 'roof_pitch': 24 if k < 4 else 50,
             'textures': {'wall': 'hkm2b', 'window': 'hkm2bw', 'post_left': 'hkm2b', 'post_right': 'hkm2b',
                          'roof': SLATE}, 'windows': 'alternate'}
        if k:
            p['bottom'] = bottom
        PAG.append(p)
    PAG[0]['textures']['door'] = 'hkm2d'
    S({'id': 'thing:pagoda', 'kind': 'building', 'at': list(PAGODA_AT), 'size': [4, 3], 'kit': 'timber',
       'facing': 'n', 'floor': 1000, 'title': 'The Ninja Pagoda', 'parts': PAG,
       'door': {'part': 'storey_1', 'wall': 'n'},
       **({'into': {'map': 'xeen_xd22.blv', 'arrival': 'entrance:x5_door'},
           'notes': ("XD-22 Ninja Pagoda (A7, D-25): into XD-22's start (0, -256, 0) facing south; its exit lands at "
                     "(320, 9872, 1000) N by an explicit point (A7).")} if XD22_LIVE else
          {'effects': [msg('The pagoda\'s door is barred from within. Black-clad shapes watch you from the upper '
                           'storeys and do not come down.')],
           'notes': 'XD-22 Ninja Pagoda (A7, phase 3): sealed with a message until its BLV and row are in.'})})
    # ---------------------------------------------------------------- the snowfields and the forest
    S({'id': 'thing:druid_ring', 'kind': 'stone_ring', 'at': [30, 61], 'radius': 448, 'count': 7, 'lintel': False,
       'title': "The Winter Druid's stones"})
    S({'id': 'thing:shrine_cold', 'kind': 'building', 'at': [52.2, 73.6], 'size': [1.6, 1.6], 'kit': 'stone',
       'title': 'Shrine of Cold', 'door': 'none',
       'parts': [{'id': 's', 'at': [205, 205], 'size': [410, 410], 'wall_height': 320, 'posts': 40, 'roof': 'cone',
                  'roof_pitch': 52, 'windows': 'none', 'textures': {'roof': SLATE}, 'title': 'Shrine of Cold',
                  'condition': {'not': {'map_var': 'shrine_cold_used'}},
                  'effects': [{'set': {'var': {'map_var': 'shrine_cold_used'}, 'value': 1}},
                              {'add': {'var': 'WaterResistance', 'value': 5}},
                              {'text': '+5 Water resistance (permanent)'}],
                  'else_effects': [{'text': 'Frost on the altar, and silence.'}]}]})
    # s33 (D-90, merge point 42): the Holy Book lies on the snow beside the torn pack as a ground item (sketch items
    # below), taken as any item; the pack is dressing only (A3's q-c18.book becomes a map_gives record)
    # D-93 (A3 s39 for A6, 2026-11-22): the torn pack gives the Holy Book onto the cursor (quest hook q-c18.book)
    S(deco('thing:holy_book', '7dec41', (68.6, 92.4), title='A torn pack',
           effects=[{'lua': 'XeenQuests.hook("q-c18.book")'}]))
    S({'id': 'thing:warren', 'kind': 'cave_mouth', 'at': [WARREN_AT[0], WARREN_AT[1] - 1.0], 'size': [1536, 1536],
       'free': True, 'mouth': {'width': 384, 'height': 320, 'depth': 75}, 'turn': 180,
       # F60 X5 p10 (2026-11-25): wild.free_mouths' cwb1 is a dark brown rubble that reads as a plain dirt mound on
       # the snow ("missing texture"); the warren is built of the grey stone of Winterkill's monastery (cnb)
       'textures': {'shell': 'cnb', 'door': '7solid01'}, 'roughness': 0.8, 'seed': 23,
       'title': 'Troll Warren', 'hint': 'Troll Warren',
       **({'into': {'map': 'xeen_xd23.blv', 'arrival': 'entrance:x5_mouth'},
           'effects': [{'lua': 'evt.StatusText("You drag the frozen hides aside.", 5)'}],
           'notes': ("XD-23 Troll Warren (A7, D-25): the hides dragged aside, into XD-23's start (0, -256, 0) facing "
                     "south. Its mouth exit lands at (768, -14595, 1210) N, its chimney on the mound's crown at "
                     "(768, -15616, 1631) S, both by explicit points (A7).")} if XD23_LIVE else
          {'effects': [msg('A mound of earth and bones, smoke rising from holes in it. The mouth is choked with bones '
                           'and frozen hides from within: the trolls have shut it.')],
           'notes': 'XD-23 Troll Warren (A7, phase 3): sealed with a message until it is built.'})})
    for i, (d, at) in enumerate([('7dec18', (64.4, 93.8)), ('dec05', (66.7, 93.6)), ('7dec20', (63.9, 95.2)),
                                 ('7dec18', (67.4, 95.6))]):
        S(deco('thing:warren_bones_%d' % (i + 1), d, at))
    S({'id': 'thing:xd10_south', 'kind': 'cave_mouth', 'at': [XD10_SOUTH[0] + 1.5, XD10_SOUTH[1]], 'turn': 90,
       'size': [1536, 1536], 'floor': 1200, 'mouth': {'width': 448, 'height': 384, 'depth': 75},
       'textures': {'shell': '7snow', 'door': '7solid01'}, 'roughness': 0.7, 'seed': 13,
       'title': 'Enter the Cave of Illusion', 'hint': 'Cave of Illusion',
       'into': {'map': 'xeen_xd10.blv', 'arrival': 'entrance:x5_south'},
       'crest': 520, 'notes': "XD-10's south mouth in the spur's west face (D-6.1)."})
    # ---------------------------------------------------------------- Glom and the giants
    S({'id': 'thing:glom_knoll_sign', 'kind': 'sign', 'at': [42.7, 78.2], 'height': 224, 'width': 160,
       'title': "Glom's burrows", 'effects': [{'text': 'By order of His Majesty Glom: wipe your feet.'}]})
    S({'id': 'thing:outpost_fence', 'kind': 'fence', 'line': [[41.4, 90.8], [46.6, 90.8], [46.8, 95.4],
                                                              [41.2, 95.2]],
       'notes': "The cyclopes' stockade, open on the north-west."})
    # D-144 (F69b): a click burns the outpost (the tents and the fire go, char and embers show) and calls A3's
    # q-c16.outpost (its line on the status line); the source's "You have found the Cyclops' outpost! Burn?"
    # (aaze0004:8) was a free Yes/No whose No changed nothing. evt:outpost_burnt keeps it burnt on every load.
    S({'id': 'thing:outpost_tent', 'kind': 'tent', 'at': [42.4, 92.0], 'size': [1280, 960], 'height': 576,
       'open': True, 'title': "The Cyclops' outpost",
       'effects': [{'lua': 'if Xeen.isSet("q-c16.outpost_burnt") then return end'},
                   {'lua': OUTPOST_BURN}, hook('q-c16.outpost')[0]]})
    S({'id': 'thing:outpost_tent2', 'kind': 'tent', 'at': [45.0, 93.4], 'size': [896, 768], 'height': 512,
       'open': True, 'title': "The Cyclops' outpost"})
    S(deco('thing:outpost_fire', 'cmpfyr00', (44.2, 91.6), title='Campfire'))
    for i, (d, at) in enumerate(OUTPOST_CHAR):
        S(deco('thing:outpost_char_%d' % (i + 1), d, at, hidden=True))
    S({'id': 'thing:outpost_chest', 'kind': 'chest', 'at': [46.0, 92.1], 'title': "The cyclopes' hoard",
       'chest': {'level': 4, 'random_items': 3}})
    # final cloud round (town_fit_check `props.in_wall`): the first bones stood through the tent's west wall (41.6)
    for i, at in enumerate([(40.8, 91.4), (43.4, 94.8), (46.2, 94.6)]):
        S(deco('thing:outpost_bones_%d' % (i + 1), '7dec18', at))
    S({'id': 'thing:giants_cairn', 'kind': 'chest', 'at': [51.2, 88.05], 'title': "A giant's grave goods",
       'chest': {'level': 3, 'random_items': 3}})
    for i, (d, at) in enumerate([('rock26', (49.4, 86.6)), ('rock12', (51.3, 86.7)), ('rock26', (50.2, 88.4))]):
        S(deco('thing:cairn_%d' % (i + 1), d, at))
    S(deco('thing:giant_stone', 'rock67', (37.0, 85.0), title="The Giants' Stones",
           condition={'all': [{'stat': {'name': 'BaseMight', 'at_least': 40}},
                              {'not': {'map_var': 'giant_stone_lifted'}}]},
           effects=[{'set': {'var': {'map_var': 'giant_stone_lifted'}, 'value': 1}},
                    {'add': {'var': 'BaseMight', 'value': 2}},
                    {'text': 'You heave the smallest of the giants\' stones off the ground. +2 Might (permanent)'}],
           else_effects=[{'text': "The smallest of the giants' stones will not budge. (Might 40)"}]))
    for i, (d, at) in enumerate([('rock26', (36.1, 84.4)), ('rock26', (38.0, 84.2))]):
        S(deco('thing:giant_stones_%d' % (i + 1), d, at))
    S({'id': 'thing:waters_great_magic', 'kind': 'fountain', 'at': [46.5, 100.5], 'title': 'Waters of Great Magic',
       'tiers': [[96, 48]], 'textures': {'wall': 'cnb'},
       'effects': [{'add': {'var': 'SP', 'value': 200}}, {'text': '+200 Spell points'}]})
    S({'id': 'thing:earth_reflector', 'kind': 'portal', 'at': [40.0, 102.6], 'radius': 256, 'sides': 16, 'turn': 0,
       'textures': {'membrane': {'texture': 'xngong5'}}, 'title': 'The Earth Reflector',  # a bronze tile (fit)
       # A3's m37.reflector_earth (before M36 its fail text, then once its experience). D-144 (F69b): a click, the
       # hook's line on the status line (`status: true`); the source's "Reflector. Activate?" was a free Yes/No whose
       # No changed nothing. As X1's and X6's Reflectors.
       'effects': [{'lua': 'XeenQuests.hook("m37.reflector_earth")'}],
       'notes': 'M37: A3 m37.reflector_earth (requires m36.started, sets m37.earth once).'})
    # ---------------------------------------------------------------- signposts
    for sid, at, arms in (
            ('sign_lagoon', (98.8, 59.0), [('Lifeforce Lagoon', 'e'), ('The pass', 'w'), ('Golem Rocks', 's'),
                                           ("Halon's", 'n')]),
            ('sign_pass', (81.0, 46.8), [('Winterkill', 'w'), ('Lifeforce Lagoon', 'e')]),
            ('sign_monastery', (74.0, 39.0), [("Kai Wu's", 'n'), ('Winterkill', 'w'), ('The pass', 'e'),
                                              ('The pagoda', 's')]),
            ('sign_steppe', (51.0, 34.0), [('Desert of the Sphinx', 'n'), ('Winterkill', 'w'),
                                           ('Kai Wu\'s monastery', 'e')]),
            ('sign_glom', (43.0, 76.0), [("Glom's", 's'), ('Winterkill', 'n'), ('Troll Forest', 'e')])):
        S({'id': 'thing:%s' % sid, 'kind': 'sign', 'at': list(at), 'height': 256,
           'arms': [{'title': t, 'toward': d} for t, d in arms]})
    S(sign('thing:giants_bones', (40.3, 83.4), 'Bones',
           'The bones of something big, cracked open for the marrow. The path goes on up.'))
    # ---------------------------------------------------------------- actors
    actors = []
    def place(row, at, count, spread, group, **kw):
        a = {'monster': str(row), 'at': list(at), 'count': count, 'spread': spread, 'group': group, 'hostile': True}
        a.update(kw)
        actors.append(a)
    # the pocket (Act II, D-4: A tier only): Dark Wolves in packs, the ogres' camp, the archers' camp
    # F63 (2026-11-25): the packs at (108, 46) and (108, 67) stood 373 from the east bound: in to x 106
    # D-142 (2026-11-25): placed groups 4,096 from XD-09's door and XD-10's north mouth (X5 rebuilt under the rule):
    # wolves (95, 71) -> (91, 72) (2,355 -> about 4,500), (106, 67) -> (104, 80) (3,341 -> about 4,600); the ogres
    # round their fire from (101.2, 38.4), (100.4, 36.4) to the camp's north-east side (3,570 -> about 5,300)
    for i, (at, n) in enumerate([((93, 26), 2), ((103, 29), 3), ((106, 46), 2), ((105, 21), 2),
                                 ((91, 72), 2), ((90, 80), 2), ((99, 96), 3), ((104, 80), 2), ((96, 85), 2)]):
        place(ROW['dark_wolf'], at, n, 0.8, 1 + i)
    place(ROW['ogre'], (103.0, 35.0), 4, 1.2, 20)
    place(ROW['ogre_brute'], (101.5, 33.5), 2, 0.8, 20)
    place(ROW['evil_archer'], (104.2, 87.4), 5, 1.2, 21)
    # the west (Act III): the barbarian camps, the snowfields' packs, the giants' corner
    place(ROW['barbarian'], (42.6, 26.4), 3, 1.0, 22)
    place(ROW['sardaj'], (41.0, 26.0), 2, 0.8, 22)
    # F63: (43.6, 24) was in his tent's wall; D-142: (44.1, 24.0) -> (43.8, 26.0) by the fire, 3,650 -> 4,400 from the
    # north road's arrival
    place(ROW['barbarian_chief'], (43.8, 26.0), 1, 0, 22)
    place(ROW['barbarian'], (66.4, 23.3), 3, 0.9, 23)
    for i, (row, at, n) in enumerate([(ROW['sabertooth'], (26.5, 71), 2), (ROW['sabertooth'], (48, 82), 3),
                                      (ROW['snow_beast'], (30, 80.5), 1), (ROW['snow_beast'], (62, 73.5), 1)]):
        place(row, at, n, 0.9, 24 + i)
    # the outpost (Q-C16). F63 (X5 p7, 2026-11-25): eight spread 1.6 round (44.2, 93.4) stood in and against the two
    # tents; now each on open ground inside the fence, clear of the tents (check_spawn_clear.py)
    for at in OUTPOST_CYCLOPES:
        place(ROW['cyclops'], at, 1, 0, 30)
    for i, at in enumerate([(33, 92), (40, 87.6), (29.5, 97)]):              # pairs on the plateau
        place(ROW['cyclops'], at, 2, 0.8, 31 + i)
    # one Giant at the east crag's north foot (2026-11-25: the crag's top at (50.5, 92) is cut off by the
    # outpost's level pad, F59; check_reach)
    place(ROW['giant'], (46.0, 88.5), 1, 0, 34)
    # Q-C6's three waves in Winterkill: the Spirit Bones at load; the Polter-Fools and the Ghost Riders hidden until
    # Randon has heard of the wave before (reported1, reported2; events below)
    spots = [(35, 39.2), (36.6, 40.6), (38.6, 40.2), (35.4, 42.2), (38.2, 42.4), (37, 43.8), (34.8, 37.8),
             (39.6, 44.6), (42.8, 40.6), (31.2, 41.6), (37, 47.8), (44.5, 43.5),
             (36.0, 41.4), (39.6, 39.4), (46.4, 41.6), (34.6, 43.8)]          # D-13: 16 spots for 16 a wave
    # F63 (X5 p13, 2026-11-25): (39.2, 38.8) put a ghost in the Acme machine, (34.6, 44.2) one in Randon's board
    for w, (row, group) in enumerate([(ROW['spirit_bones'], 40), (ROW['polter_fool'], 41), (ROW['ghost_rider'], 42)]):
        for i in range(WAVE):
            at = spots[(i + 3 * w) % len(spots)]
            a = {'monster': str(row), 'at': [at[0] + 0.15 * w, at[1] - 0.1 * w], 'spread': 0, 'group': group,
                 'hostile': True}
            if w:
                a['hidden'] = True
            actors.append(a)
    # townsfolk, shown when the town is free
    for i, at in enumerate([(35.2, 40.8), (38.8, 41.0), (36.2, 44.6), (33.0, 41.6), (41.5, 41.9), (37.2, 46.8),
                            (43.0, 38.2), (30.8, 43.0), (40.1, 38.6), (45.2, 40.6)]):   # F63: (39.6, 38.6) in the machine
        actors.append({'monster': ['361', '377', '350', '368'][i % 4], 'at': list(at), 'spread': 0, 'group': 50,
                       'hidden': True})
    for npc, kind, at in NPC_ACTORS:
        actors.append({'monster': kind, 'npc': npc, 'at': list(at), 'spread': 0, 'group': 52})
    # Kai Wu's monks and Winterkill's people: D-96's villagers (villagers.yml, villagers_spots.yml; the monks replace
    # the two placed novices of session 7)
    actors += V.slots(2)      # the two novices' places in the list (actor indices stay); gen fills them
    # D-87.1: the scene's actor index of Mayor Randon (placements expand by their counts, in this list's order)
    _ri = [k for k, a in enumerate(actors) if a.get('npc') == 4502][0]
    RANDON_ACTOR = sum(a.get('count', 1) for a in actors[:_ri])
    relations = [{'of': [451, 452, 453], 'toward': 'party', 'relation': 'friendly'},
                 {'of': [517, 518, 519], 'toward': 'party', 'relation': 'friendly'},
                 {'of': [583, 584, 585], 'toward': 'party', 'relation': 'friendly'}]
    events = [
        {'id': 'evt:wave1_laid', 'trigger': 'timer', 'every': 5, 'once': True, 'condition': {'kills': {'group': 40}},
         'effects': [{'qbit': 'wave1_laid'}, {'text': 'The last of the Spirit Bones falls apart in the snow.'}],
         'notes': 'Q-C6: the first wave laid (112122).'},
        {'id': 'evt:wave2_show', 'trigger': 'timer', 'every': 3, 'once': True, 'condition': {'qbit': 'reported1'},
         'effects': [{'show_actors': 41}], 'notes': 'Q-C6: Randon heard of the first wave: the Polter-Fools come.'},
        {'id': 'evt:wave2_laid', 'trigger': 'timer', 'every': 5, 'once': True,
         'condition': {'all': [{'qbit': 'reported1'}, {'kills': {'group': 41}}]},
         'effects': [{'qbit': 'wave2_laid'}, {'text': 'The Polter-Fools are gone. The town is very quiet.'}]},
        {'id': 'evt:wave3_show', 'trigger': 'timer', 'every': 3, 'once': True, 'condition': {'qbit': 'reported2'},
         'effects': [{'show_actors': 42}], 'notes': 'Q-C6: the Ghost Riders come.'},
        {'id': 'evt:wave3_laid', 'trigger': 'timer', 'every': 5, 'once': True,
         'condition': {'all': [{'qbit': 'reported2'}, {'kills': {'group': 42}}]},
         'effects': [{'qbit': 'wave3_laid'}, {'text': 'The last ghost rides off into the snow and does not come back.'}]},
        {'id': 'evt:townsfolk', 'trigger': 'timer', 'every': 3, 'once': True,
         'condition': {'qbit': 'winterkill_liberated'}, 'effects': [{'show_actors': 50}],
         'notes': 'Winterkill liberated: the townsfolk come back.'},
        {'id': 'evt:randon_load', 'trigger': 'load',
         'effects': [{'lua': 'evt.SetMm9ActorCanReceiveDamage(%d, false)' % RANDON_ACTOR}],
         'notes': ('D-87.1: Mayor Randon (actor %d, npc 4502) stands in the haunted square and takes no damage, '
                   'as Corak (D-51): no stray hit or Fireball kills him or turns him hostile.' % RANDON_ACTOR)},
        {'id': 'evt:outpost_burnt', 'trigger': 'load', 'condition': {'lua': 'Xeen.isSet("q-c16.outpost_burnt")'},
         'effects': [{'hide': t} for t in OUTPOST_GONE]
                    + [{'show': 'thing:outpost_char_%d' % (i + 1)} for i in range(len(OUTPOST_CHAR))],
         'notes': 'Q-C16: the outpost stays burnt (A6 s27).'},
    ]
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
    def stand(sid, poly, kinds_, per_100, spacing, close=0.1, edge=True):
        e = {'id': sid, 'count': max(1, int(per_100 * K.poly_area(poly) / 100.0)), 'polygon': poly,
             'spacing': spacing, 'close_share': close, 'close_spacing': 1.0, 'spacing_group': 'trees'}
        if edge:
            e['edge_thin'] = {'width': 3, 'keep': 0.35}
        if len(kinds_) == 1:
            e['decoration'] = list(kinds_)[0]
        else:
            e['kinds'] = dict(kinds_)
        scatter.append(e)
    FIRS = {'tree33': 3, 'tree36': 3, 'snotre03': 1}
    SNOWFIRS = {'snotre01': 2, 'snotre03': 2, 'tree36': 1}
    FOREST = [[54, 77], [78, 66], [79, 70], [79.5, 103], [53, 103], [52.5, 87]]
    stand('scatter:troll_forest', FOREST, FIRS, 13.0, 1.4)
    sc('scatter:forest_rocks', '6rock03', 30, FOREST, clusters=10)
    sc('scatter:forest_bones', '7dec18', 14, FOREST, clusters=6)
    POCKET_FIRS = [[87, 64], [109, 64], [109, 103], [87, 103]]
    stand('scatter:fen_firs', POCKET_FIRS, FIRS, 5.0, 1.8)
    sc('scatter:fen_sedge', 'plant02', 60, POCKET_FIRS, clusters=18)
    sc('scatter:fen_weeds', 'snoweed1', 40, POCKET_FIRS, clusters=14)
    HILLS = [[88, 19], [109, 19], [109, 53], [100, 54], [92, 55], [88, 52]]
    stand('scatter:hill_firs', HILLS, SNOWFIRS, 4.5, 1.8)
    sc('scatter:hill_rocks', '6rock07', 30, HILLS, clusters=10, steep=True)
    STEPPE = [[36, 19], [77, 19], [77, 40], [72, 38], [62, 38], [52, 36], [48, 33], [36, 32]]
    stand('scatter:steppe_trees', STEPPE, SNOWFIRS, 1.6, 2.6)
    sc('scatter:steppe_rocks', '6rock03', 40, STEPPE, clusters=14)
    sc('scatter:steppe_rocks', '6rock07', 25, STEPPE, clusters=9)
    sc('scatter:steppe_weeds', 'snoweed1', 40, STEPPE, clusters=12)
    SNOW_W = [[24.5, 50], [37, 51], [39, 61], [43, 68], [50, 71], [56, 72], [52, 84], [24.5, 84]]
    stand('scatter:snowfield_firs', SNOW_W, {'tree36': 2, 'tree33': 2, 'snotre01': 1}, 3.2, 2.2)
    sc('scatter:snowfield_rocks', '6rock03', 22, SNOW_W, clusters=8)
    sc('scatter:snowfield_weeds', 'snoweed1', 30, SNOW_W, clusters=10)
    stand('scatter:grove_firs', [[27, 57.5], [33, 57.5], [33, 64.5], [27, 64.5]], {'tree36': 2, 'tree33': 1}, 30.0,
          1.2, edge=False)
    PLATEAU = [[24.5, 19], [36, 19], [36, 32], [28.5, 33], [28.5, 34], [24.5, 34]]
    stand('scatter:plateau_firs', PLATEAU, SNOWFIRS, 2.5, 2.4)
    sc('scatter:plateau_rocks', '6rock07', 16, PLATEAU, clusters=6)
    GIANTS = [[24.5, 85], [52, 85], [52, 103.5], [24.5, 103.5]]
    sc('scatter:giants_rocks', '6rock07', 40, GIANTS, clusters=12, steep=True)
    sc('scatter:giants_rocks', 'rock26', 18, GIANTS, clusters=8)
    sc('scatter:giants_bones', '7dec18', 10, GIANTS, clusters=4)
    SPINE = [[77, 0], [87, 0], [87, 58], [77, 58]]
    sc('scatter:spine_rocks', '6rock07', 40, SPINE, clusters=12, steep=True)
    sc('scatter:spur_rocks', '6rock07', 20, [[79, 66], [86, 66], [86, 103], [80, 103]], clusters=8, steep=True)
    # the town's firs in yards and by the palisade; the mere's shore reeds
    for i, at in enumerate([(30.0, 36.0), (44.6, 35.2), (46.6, 44.5), (30.6, 47.8), (40.6, 48.6), (29.4, 38.4),
                            (27.0, 35.0), (26.4, 46.0), (33.0, 50.6), (45.0, 50.0), (49.6, 44.0), (50.6, 39.0),
                            (42.0, 32.0), (35.0, 31.6), (28.6, 31.0), (47.6, 47.6)]):
        scatter.append({'id': 'scatter:town_firs', 'decoration': ['tree36', 'tree33'][i % 2], 'count': 1,
                        'circle': {'at': list(at), 'r': 0.2}})
    # the land past the party's square to the map's edge (north and east; west and south is the rim)
    for sid, poly, per in (('scatter:edge_n', [[24.5, 0], [128, 0], [128, 18.5], [24.5, 18.5]], 3.0),
                           ('scatter:edge_e', [[109.5, 18.5], [128, 18.5], [128, 103.5], [109.5, 103.5]], 3.5)):
        scatter.append({'id': sid, 'count': int(per * K.poly_area(poly) / 100.0), 'polygon': poly, 'spacing': 1.6,
                        'spacing_group': 'trees', 'kinds': dict(SNOWFIRS)})
        scatter.append({'id': sid.replace('edge', 'edge_rocks'), 'decoration': '6rock07',
                        'count': int(0.8 * K.poly_area(poly) / 100.0), 'polygon': poly, 'clusters': 10, 'steep': True})
    # rocks along the rim's lip, sea stacks below it
    sc('scatter:lip_rocks', '6rock03', 30, line=[[24.6, 20], [24.6, 103.4]])
    sc('scatter:lip_rocks', '6rock03', 30, line=[[25, 103.4], [108, 103.4]])
    scatter.append({'id': 'scatter:sea_stacks', 'decoration': 'rock26', 'count': 14, 'on': 'water',
                    'polygon': [[4, 20], [21, 20], [21, 110], [4, 110]]})
    scatter.append({'id': 'scatter:sea_stacks', 'decoration': 'rock12', 'count': 10, 'on': 'water',
                    'polygon': [[24, 106], [120, 106], [120, 112], [24, 112]]})
    ground = [
        {'material': 'snow', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'Snow everywhere but the scoured patches, the tracks and the ice.'},
        # the ice (D-6.3): the mere, the frozen river below the gorge, the glacier, painted with the sand tiles that
        # this map's terrain materials draw as `ice`
        {'material': 'sand', 'polygon': MERE, 'notes': 'The Winterkill Mere: ice (D-6.3).'},
        {'material': 'sand', 'line': RIVER_ICE, 'width': 3, 'notes': 'The frozen river below the gorge: ice.'},
        {'material': 'dirt', 'polygon': [[40, 19], [47, 19], [47, 24], [40, 24]], 'notes': 'Scoured stony ground.'},
        {'material': 'dirt', 'polygon': [[57, 23], [63, 23], [63, 27], [57, 27]], 'notes': 'Scoured stony ground.'},
        {'material': 'dirt', 'polygon': [[68, 44], [74, 44], [74, 47], [68, 47]], 'notes': 'Scoured stony ground.'},
        {'material': 'dirt', 'polygon': SQUARE, 'notes': 'Winterkill square.'},
        {'material': 'dirt', 'polygon': [[52, 57], [58, 57], [58, 64], [52, 64]], 'notes': "Darkstone's black rock."},
        {'material': 'dirt', 'polygon': [[97, 72], [105, 72], [105, 79], [97, 79]], 'notes': 'The Golem Rocks: bare stone.'},
        {'material': 'dirt', 'steeper_than': 640, 'polygon': [[0, 0], [128, 0], [128, 104], [0, 104]],
         'notes': 'Bare rock on the sheer crags, the ridge and the spur (the gentler snow slopes stay white).'},
        # the glacier after the bare-rock rule, so its steep fronts read as ice (D-6.5, session 6)
        {'material': 'sand', 'polygon': [[32, 86], [39, 86], [39.5, 93], [39, 103.5], [30, 103.5], [30.5, 94]],
         'notes': "The glacier's tongue: ice."},
        {'material': 'sand', 'polygon': [[31, 84.6], [38.6, 84.6], [39, 86.2], [31, 86.2]],
         'notes': "The glacier's head: its north front over the Giants' Stones, ice."},
        {'material': 'sand', 'polygon': [[28.6, 86.8], [37.6, 86.8], [37.8, 83], [37.6, 79.5], [36.4, 76.6],
                                         [27.6, 76.6], [26.6, 79], [27.0, 83]],
         'notes': 'The icefall north off the plateau and its snout on the snowfield, its steep margins too: ice.'},
        {'material': 'dirt', 'polygon': [[95, 85], [102, 85], [102, 92], [95, 92]], 'notes': 'The fen: black mud.'},
        {'material': 'dirt', 'polygon': [[89, 70], [94, 70], [94, 76], [89, 76]], 'notes': 'The fen: black mud.'},
        {'material': 'dirt', 'polygon': [[103, 68], [108, 68], [108, 72], [103, 72]], 'notes': 'The fen: black mud.'},
    ]
    for line in PATHS:
        ground.append({'material': 'dirt', 'line': line, 'width': 2, 'notes': 'a track in the snow'})
    # Winterkill's back lanes to the doors off the square (town_feel: every door near a road or lane)
    for line in ([[37, 45], [37, 47.5], [33, 47.5], [30.5, 46.5], [30.5, 45]],
                 [[40, 45], [42.5, 45], [42.5, 47], [43.5, 47]],
                 [[33.5, 41.5], [33.5, 43], [34, 43]], [[40, 41.5], [40.5, 39.5], [42, 40]]):
        ground.append({'material': 'dirt', 'line': line, 'width': 2, 'notes': "a lane in Winterkill"})
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('X5 Winterkill Tundra, written by output/studio_cal/x5/tools/gen.py. Cells [x, y], x east, y south. '
                  'Heights are map units above the stars below the rim (0): the ice at 800, Winterkill at 1,000, '
                  'the steppe 1,100-1,500, the Frostspine to 4,000 and its spur about 2,800, the giants\' crags to '
                  '3,600, the pocket 900-2,200.'),
        'frame': {'playable': [19, 19, 90, 90],
                  'edges': ([{'side': 'east', 'span': [55, 62], 'neighbour': 'edge:east'}] if X3_LIVE else [])
                  + ([{'side': 'north', 'span': [45, 56], 'neighbour': 'edge:north'}] if X6_LIVE else []),
                  'edge': {'height': 1500, 'west': 0, 'south': 0, 'east': 900}, 'rim': rim},
        'heights': heights, 'water': water, 'roads': roads, 'districts': districts, 'points': points,
        'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground, 'structures': structures,
        'actors': V.fill(actors, 'X5'), 'relations': relations + V.relations('X5'), 'events': events,
        'items': [],   # D-93 (A3 s39): the book is in the torn pack (thing:holy_book), no ground item
    }
    atmosphere = {'format': 0, 'weather': {'snow': True},
                  'notes': ("Cloudside's skies by the hour and the weather (the shipped presets; snow weather draws "
                            "winter_overcast); snow by the world's chances.")}

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

    def dump(folder, name, data):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)
    dump(OUT, 'project.yml', project)
    dump(OUT, 'plan.yml', plan)
    # AU's outdoor bed (E9, merge point 20; devdocs/xeen/AUDIO.md "Outdoor beds"): the scene's ambient_sounds
    sketch['sounds'] = (sketch.get('sounds') or []) + yaml.safe_load(open(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '../common/beds/x5.yml')))['sounds']
    # F2/F8 (s32): cave mouths into hills as wide as their mouth + rim; F16/D-90: each dungeon door's trans row
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    import house_doors as HD
    import entrance_screens as ES
    for _note in HD.double_doors_sketch(sketch) + HD.bury_mouths_sketch(sketch) + HD.blind_mouths_sketch(sketch):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sketch, 'x5'):
        print('wild:', _note)
    # The classic Clouds kit (2026-11-24): Clouds of Xeen's own half-timbered walls on the map's houses
    import classic_kit as CK
    for _note in CK.apply(sketch, 'x5'):
        print(_note)
    # D-174: the level pads PADS lists by hand for this map (Freeda's tent; common/level_pads.py)
    import level_pads as LP
    for _note in LP.apply(sketch, 'x5'):
        print(_note)
    print('entrance screens:', ES.apply_sketch(sketch, 'xeen_x5'))
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


if __name__ == '__main__':
    build()
