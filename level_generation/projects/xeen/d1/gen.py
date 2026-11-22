#!/usr/bin/env python3
"""D1 Castleview Vale: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml) and the L2 and L3
briefs beside it (L1 is the approved mock-up of 2026-11-20 and stays as it is).

The design is the approved L1 (devdocs/xeen/briefs/d1/L1, board level_generation/xeen_art/phase3/d1/) with the
decider's changes of D-23: POIs by the D-15/D-20 census at or under 55 (the heretic's pack at the rope, the reed bottle
in the wreck, Lyle's bench by the mirror, the falls a view with no click); two gates on m14.gate / m14.gate_open (the
north gatehouse and the small Queen's Gate in the south-west wall onto the Kalindra road); from inside, before
m14.entered, each inner leaf puts the party outside its gate (D-30, m14.let_out), after it opens the gate; Castle
Kalindra in parts by stage (D-30: xkshimmer at load, the royal kit's white stone from Xeen.stageOf("kalindra") >= n);
S's great-tree crown on the Dark Grove's trunk; the Vale Water D1's own (rises at the Sardaj spring, falls off the south rim at y 104, touches no map edge); the Dark
Grove rope on m30.grove_rope; the Western Tower's front door on q-d6.front_door_outside. D-5.3 (Lucio's Jetty on the
west wall's top), D-9.3 (the heretics' rope on the tower's north wall).
World: xeen. Houses: A4's source/towns/d1.yml. Hooks: A3's quest files (every hook with `map: D1` is used: asserted).
Rows: A2's (map_stats 9108; Gremlins 11020-11022, Arachnoids 11330-11332, Crawlers 11360-11362, Barbarians
11100-11103). The project files are this script's output: edit here and run ../v.sh, never the files.
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

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/d1'
OUT = os.path.join(BRIEFS, 'L4')
STEM = 'xeen_d1'
XEEN = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/worlds/xeen')
XEEN_SOURCE = os.path.join(XEEN, 'source')

def live(stem, env):
    """A neighbour is live when its map is installed in the world (X5's X3_LIVE), or forced by an env variable."""
    if os.environ.get(env) == '0':
        return False
    return os.path.exists(os.path.join(XEEN, 'maps', stem)) or os.environ.get(env) == '1'

D2_LIVE = live('xeen_d2.odm', 'D1_D2_LIVE')        # the east edge (D2, built in parallel by another sub-agent)
D6_LIVE = live('xeen_d6.odm', 'D1_D6_LIVE')        # the north edge (D6, phase 5): live once D6 is installed
# D7 The Skyroads (phase 6, D-58): the grove rope climbs to D7's entrance:d1_rope once D7 is installed and names it
D7_LIVE = live('xeen_d7.blv', 'D1_D7_LIVE')
# the dungeons (A8's and A7's): each door shows its hook or refusal and then a sealed message until its map exists
DUNGEON = {k: live('xeen_%s.blv' % k, 'D1_%s_LIVE' % k.upper()) for k in ('dd01', 'dd02', 'dd03', 'dd04', 'dd05',
                                                                         'dd10a')}
# DD-05's inside arrivals (A8): the front door lands at entrance:d1_door, the rope at the top floor's entrance:d1_rope
DD05_ARRIVAL = {'door:dd05_front': 'entrance:d1_door', 'door:dd05_rope': 'entrance:d1_rope'}


def dd05_rope_move():
    """evt.MoveToMap to DD-05's entrance:d1_rope (coordinates and facing from DD-05's studio sidecar)."""
    side = yaml.safe_load(open(os.path.join(XEEN, 'maps', 'xeen_dd05.studio.yml')))
    a = next(a for a in side['arrivals'] if a.get('name', a.get('id')) == 'entrance:d1_rope')
    return 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, 5033, 1, "xeen_dd05.blv")' % (*a['at'], int(a['facing']))


def d7_rope_move():
    """evt.MoveToMap to D7's entrance:d1_rope (from D7's studio sidecar), or None while D7 does not name it."""
    path = os.path.join(XEEN, 'maps', 'xeen_d7.studio.yml')
    if not D7_LIVE or not os.path.exists(path):
        return None
    side = yaml.safe_load(open(path))
    a = next((a for a in side.get('arrivals', []) if a.get('name', a.get('id')) == 'entrance:d1_rope'), None)
    if a is None:
        return None
    return 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, 0, 1, "xeen_d7.blv")' % (*a['at'], int(a['facing']))
# AU's bed (a6/beds/d1.yml): the scene numbers the sketch's sounds from 1 in order; the castle hill's shimmer loop
# (sound:kalindra_shimmer) is switched off by its map variable AmbientSound<key> at Kalindra's stage 4
SHIMMER_KEY = 1 + [b['id'] for b in yaml.safe_load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                     '../common/beds/d1.yml')))['sounds']].index(
    'sound:kalindra_shimmer')
EAST_START = (106.0, 60.0)       # the east start on the east road (D2's edge:west arrives here), looking west

# ---------------------------------------------------------------------------------------------------------------
# A3's hooks on D1 (quest files' `hooks` with `map: D1`); every one must be used (asserted at the end)
HOOKS = {}
for _f in sorted(os.listdir(os.path.join(XEEN_SOURCE, 'quests'))):
    try:
        _q = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'quests', _f)))
    except yaml.YAMLError as _e:      # another lane mid-edit: a D1 file must parse (its hooks are asserted below)
        sys.stderr.write('warning: %s does not parse (%s)\n' % (_f, str(_e).splitlines()[0]))
        continue
    for _k, _v in (_q.get('hooks') or {}).items():
        if _v.get('map') == 'D1':
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

# A4's houses (source/towns/d1.yml): door -> house id and name
TOWN = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'towns/d1.yml')))
HOUSE = {h['door']: (h['id'], h['name']) for h in TOWN['houses']}
OPENS = {'m30.done': 'lucio_open'}
GATED = {h['id']: (OPENS[h['opens']], h['closed_text']) for h in TOWN['houses']
         if h.get('opens') and not h['door'].startswith('thing:')}
HOUSE_MIRROR = HOUSE['thing:cv_mirror'][0]

ROW = {
    'gremlin': 11020, 'saboteur': 11021, 'gremlin_guard': 11022,
    'barbarian': 11100, 'sardaj': 11101, 'barbarian_chief': 11102, 'yog': 11103,
    'arachnoid': 11330, 'hunter': 11331, 'queen': 11332,
    'scorpion': 11360, 'electrapede': 11361, 'roach': 11362,
}
QBIT = {'pass_entered': 111281, 'kalindra_stage1': 111381, 'lucio_open': 111600, 'court_won': 113021,
        'sardaj_hostile': 113242, 'sardaj_camp_burned': 113244, 'chest_still': 111343, 'west_tower_opened': 113125}
ITEMS = {'castleview_pass': 12330, 'ellinger_key': 12333, 'west_tower_key': 12338, 'monga_melon': 12343}
SARDAJ_GROUP = 60

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

def lstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')

def sign(sid, at, title, text=None, height=224, width=160, effects=None, **kw):
    d = {'id': sid, 'kind': 'sign', 'at': list(at), 'height': height, 'width': width, 'title': title,
         'effects': effects if effects is not None else [msg(text)]}
    d.update(kw)
    return d


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

def sealed(what):
    return msg('%s is not open to you yet.' % what)

# ---------------------------------------------------------------------------------------------------------------
# Land and water. Heights are map units above the stars below the rim (water at 0).
# ---------------------------------------------------------------------------------------------------------------
RIM_X = 24          # the world rim, west: the land ends in a cliff along x 24
RIM_Y = 104         # the world rim, south: along y 104 (D-23)
TOWN_H = 1150       # Castleview
WALL_H = 600        # the town walls: their walk at 1,750
RIVER = 830         # the Vale Water
KAL_H = 1750        # Castle Kalindra's rise
FORECOURT_H = 1650
SHELF_H = 1600      # the gemsmiths' shelf
TOWER_H = 1600      # the Western Tower's knoll
CAMP_H = 1550       # the Sardaj camp
# The Vale Water (D-23: D1's own): from the Sardaj spring under the north hills south through the mill gorge east of
# the walls, west under Kalindra's rise and over the south rim into the stars at x 31 (inside the map; no edge)
RIVER_LINE = [[84, 20], [83, 26], [82, 34], [81, 40], [81, 46], [81, 52], [81, 60], [80, 66], [76, 71],
              [70, 75], [64, 78], [57, 80], [50, 82], [45, 81], [41, 83], [37, 87], [34, 92], [32, 98], [31, 103]]
GORGE = (79.5, 38, 84.5, 52)     # the mill gorge: the river 270 under the vale (x0, y0, x1, y1)
ACID = [[68, 28], [73, 27], [76, 29], [75, 33], [70, 34], [67, 31]]
ACID_H = 1080
# the town wall (a ring of stretches; the gates and the jetty bastion are gaps filled by their own things)
WALL = [[50, 47], [53, 44], [73, 44], [76, 47], [76, 61], [73, 64.5], [54.5, 64.5], [50, 60.5]]
TOWN_TERRACE = [[47.5, 46], [52.5, 41.5], [73.5, 41.5], [78.2, 46], [78.2, 62], [74, 66.8], [53.5, 66.8],
                [47.5, 61.5]]
NORTH_GATE = (63.0, 44.0)
QUEEN_A, QUEEN_B = (50, 60.5), (54.5, 64.5)
QUEEN_GATE = ((QUEEN_A[0] + QUEEN_B[0]) / 2, (QUEEN_A[1] + QUEEN_B[1]) / 2)
JETTY_Y = (52.8, 55.6)          # the jetty bastion's stretch of the west wall
# D-30: where an inner leaf puts a party that has not yet entered (the gates' outside arrivals, map units)
NORTH_OUT = (-512, 10752, 1152)    # [63, 43], faced 270 (1536)
QUEEN_OUT = (-6656, 0, 1152)       # [51, 64], faced 45 (256)

CALM = [(63, 54, 14), (60, 36, 3), (31, 33, 4), (40, 70, 8), (52, 90, 3), (88, 25, 4), (93, 36, 3), (30, 62, 3),
        (27, 76, 3), (100, 93, 2.5), (106, 60, 4), (64, 68, 5), (47, 35, 3), (39, 23, 6)]

def roll(x, y):
    w = 1.0
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 4.0))
    w = min(w, smooth((x - RIM_X - 2) / 4.0), smooth((RIM_Y - 2 - y) / 4.0))
    v = (90 * math.sin(x / 3.3 + 0.4) * math.sin(y / 3.9 + 1.3) + 70 * math.sin((x + 1.3 * y) / 5.1 + 0.9)
         + 40 * math.sin((x - 1.6 * y) / 2.7))
    return w * v

def land(x, y):
    """The land before the water, the town and the words that the build lays over it."""
    h = 1100.0
    # the north hills: the mine hills west of the mountain road, the Sardaj Horn east of it
    hills = 2000 * smooth((20 - y) / 11.0)
    hills += bump(x, y, 44, 7, 10, 800) + bump(x, y, 30, 9, 8, 500) + bump(x, y, 78, 7, 9, 1300)
    hills += bump(x, y, 96, 8, 10, 700) + bump(x, y, 114, 11, 12, 800)
    hills *= smooth((20.5 - y) / 3.0) if y > 17.5 else 1.0
    # the mountain road's valley (x 64): its floor from 1,550 at y 19 to 2,000 at the edge
    v = smooth(1 - abs(x - 64.5) / 6.0)
    floor = 1550 + max(0.0, 19 - y) * 24
    h += hills
    if y < 22:
        h = h * (1 - v) + max(floor, 1100 + 450 * smooth((22 - y) / 3.0)) * v
    # the siege lines rise north to the hills
    h += 300 * smooth((40 - y) / 16.0) * smooth((x - 56) / 4.0) * smooth((84 - x) / 4.0)
    # the Gemstone foothills (north-east)
    h += 900 * smooth((x - 97) / 9.0) * smooth((47 - y) / 12.0) + bump(x, y, 120, 30, 10, 500)
    # knolls and rises
    h += bump(x, y, 39, 23, 11, 500)                       # the gemsmiths' shelf and the mine's hill
    h += bump(x, y, 45, 21, 4, 250)
    h += bump(x, y, 31, 33, 6, 520)                        # the Western Tower's knoll
    h += bump(x, y, 60, 36, 5, 150)                        # the pyramid's knoll
    h += bump(x, y, 88, 25, 7, 450)                        # the Sardaj camp's shoulder
    h += bump(x, y, 93, 36, 4, 250)                        # Vespar's knoll
    h += bump(x, y, 41, 70, 9, 650)                        # Castle Kalindra's rise
    h += bump(x, y, 27, 76, 5, 250)                        # the obelisk's headland
    h += bump(x, y, 52, 90, 4, 200)                        # the prayer shrine's knoll
    h += bump(x, y, 100, 93, 3, 120)                       # the Well of Might's mound
    h -= 100 * smooth((y - 74) / 8.0) * smooth((x - 58) / 4.0)   # the southern meadows lie low (1,000)
    h += roll(x, y)
    # the river's valley: banks at 900 over two cells, the vale back over three more; the mill gorge steep
    d = dist_to_line(x, y, RIVER_LINE)
    g = GORGE[0] <= x <= GORGE[2] and GORGE[1] <= y <= GORGE[3]
    if g:
        if d < 3.0:
            h = 880 + (h - 880) * smooth((d - 1.8) / 1.2)
    elif d < 5:
        h = 900 + (h - 900) * smooth((d - 1.6) / 3.4)
    # the acid pond in its cracked rim
    if K.inside((x, y), ACID):
        h = ACID_H - 50
    else:
        da = poly_dist((x, y), ACID)
        if da < 2:
            h = (ACID_H + 20) + (h - ACID_H - 20) * smooth(da / 2.0)
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
# Castleview (A4's 50 houses and the mirror). Plots: (building, index, at = NW corner, facing, [front, depth], grade,
# kind, extra). grade: poor (t06 under mossy slate), middle (t06 with the frieze under t06a05), rich (t09 ashlar under
# slate), service (t09 with the carved door). Gate Street runs south from the north gate (x 63) to the square
# [59, 51]-[67, 57]; the Guild Row along y 58; the west lane along y 56 to the stair up to Lucio's Jetty; the back lane
# along y 61; the yard lane from Gate Street east along y 47.6 and south down the coach yard (x 71.3).
# ---------------------------------------------------------------------------------------------------------------
SQUARE = [[59, 51], [67, 51], [67, 57], [59, 57]]
PLOTS = [
    # Gate Street: the tavern and the inn first inside the gate, the smiths across from them
    ('building:cv_tavern', None, (59.5, 45.5), 'e', [2, 2], 'service', 'gable_porch', {'sign': 'sgtvrn'}),
    # the Adventurer's Inn hangs MM6-MM8's key and heart (Ravenshore's sgINN; A4 2026-11-22, house_signs.py)
    ('building:cv_inn', None, (59.5, 48.0), 'e', [2, 2], 'service', 'L', {'sign': 'sginn'}),
    ('building:cv_weapons', None, (65.0, 45.0), 'w', [2, 1.5], 'middle', 'forge', {'sign': 'sgweap'}),
    ('building:cv_armour', None, (64.5, 48.5), 'w', [2, 1.5], 'middle', 'jetty', {'sign': 'sgarm'}),
    ('building:cv_jail', None, (66.5, 45.0), 's', [2.5, 1.5], 'rich', 'cottage', {'sign': 'xljail'}),
    ('building:cv_houses', 11, (66.5, 48.5), 's', [2, 1], 'poor', 'cottage', {}),
    # the square
    ('building:cv_magic', None, (57.0, 50.5), 'e', [2, 2], 'rich', 'tower_house', {'sign': 'sgmagic'}),
    ('building:cv_alchemist', None, (57.0, 53.5), 'e', [1.5, 1.5], 'middle', 'gable_porch', {'sign': 'sgalch'}),
    ('building:cv_town_hall', None, (67.5, 51.0), 'w', [3, 2.5], 'service', 'L', {}),
    ('building:cv_bank', None, (67.5, 54.5), 'w', [2, 2], 'service', 'cottage', {'sign': 'sgbank'}),
    # the Guild Row (y 58), the temple at its east end
    ('building:cv_guild_fire', None, (52.5, 58.5), 'n', [2, 2], 'rich', 'L', {'sign': 'sgfire'}),   # D-92 (b)
    ('building:cv_guild_air', None, (55.0, 58.5), 'n', [2, 2], 'rich', 'tower_house', {'sign': 'sgair'}),
    ('building:cv_guild_water', None, (57.5, 58.5), 'n', [2, 2], 'rich', 'gable_porch', {'sign': 'sgwater'}),
    ('building:cv_guild_earth', None, (60.0, 58.5), 'n', [2, 2], 'rich', 'L', {'sign': 'sgearth'}),
    ('building:cv_guild_body', None, (62.5, 58.5), 'n', [2, 2], 'rich', 'cottage', {'sign': 'sgbody'}),
    ('building:cv_temple', None, (70.5, 58.5), 'w', [3, 3], 'rich', 'temple', {}),
    # the coach yard inside the east wall
    ('building:cv_training', None, (72.0, 48.5), 'w', [2.5, 2.5], 'middle', 'barn', {'sign': 'sgtrain'}),
    ('building:cv_stables', None, (72.0, 52.0), 'w', [3, 2.5], 'middle', 'barn', {'sign': 'sgstabl'}),
    ('building:cv_houses', 17, (73.0, 56.0), 'w', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_houses', 15, (69.0, 49.5), 'w', [1, 1], 'poor', 'cottage', {}),
    # the north-west quarter
    ('building:cv_houses', 6, (55.0, 45.0), 's', [1.5, 1], 'middle', 'cottage', {}),
    ('building:cv_houses', 8, (57.0, 45.0), 's', [1.5, 1], 'rich', 'gable_porch', {}),
    ('building:cv_houses', 20, (56.5, 47.0), 'e', [1.5, 1], 'poor', 'cottage', {}),
    ('building:cv_houses', 4, (54.5, 47.5), 's', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_houses', 7, (52.5, 48.0), 'e', [3, 1], 'middle', 'barn', {}),
    ('building:cv_houses', 1, (54.5, 49.5), 's', [1.5, 1], 'middle', 'gable_porch', {}),
    ('building:cv_houses', 2, (57.5, 49.0), 's', [1.5, 1], 'poor', 'cottage', {}),
    ('building:cv_library', None, (53.5, 51.5), 'e', [2.5, 2], 'rich', 'L', {}),
    ('building:cv_houses', 5, (52.0, 52.0), 'e', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_houses', 14, (52.0, 54.0), 'e', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_houses', 3, (53.5, 54.5), 's', [1.5, 1], 'middle', 'gable_porch', {}),
    ('building:cv_houses', 16, (55.5, 54.5), 's', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_houses', 19, (52.5, 56.5), 's', [1.5, 1], 'rich', 'cottage', {}),
    ('building:cv_houses', 10, (54.5, 56.5), 's', [1.5, 1], 'middle', 'gable_porch', {}),
    ('building:cv_houses', 13, (56.5, 56.5), 's', [1.5, 1], 'poor', 'cottage', {}),
    # the back lane (y 61): the Drawkcab cells, Public Storage, the south-east houses
    ('building:cv_drawkcab', 1, (56.5, 61.5), 'n', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_drawkcab', 2, (57.5, 61.5), 'n', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_drawkcab', 3, (58.5, 61.5), 'n', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_drawkcab', 4, (59.5, 61.5), 'n', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_public_storage', None, (63.5, 61.5), 'n', [1.5, 1], 'rich', 'cottage', {'sign': 'xlstorage'}),
    ('building:cv_houses', 9, (68.0, 61.5), 'n', [1, 1], 'poor', 'cottage', {}),
    ('building:cv_houses', 12, (69.5, 62.0), 'n', [1, 1], 'middle', 'cottage', {}),
    ('building:cv_houses', 18, (71.5, 62.0), 'e', [1.5, 1], 'poor', 'cottage', {}),
]
# Lucio's Jetty (D-5.3) stands on the deck over the west wall's bastion; the vale's houses
JETTY_PLOT = ('building:cv_lucio_jetty', None, (49.0, 53.5), 'e', [1, 1], 'rich', 'cottage', {'sign': 'sgdock'})
WILD_PLOTS = [
    ('zone:gemsmiths_row', 'building:gemsmith', 1, (31.5, 23.5), 's', [2, 1.5], 'middle', 'forge', {}),
    ('zone:gemsmiths_row', 'building:gemsmith', 2, (34.5, 23.5), 's', [2, 1.5], 'middle', 'forge', {}),
    ('zone:gemsmiths_row', 'building:gemsmith', 3, (37.5, 23.5), 's', [2, 1.5], 'middle', 'forge', {}),
    ('zone:gemsmiths_row', 'building:gemsmith', 4, (40.5, 23.5), 's', [2, 1.5], 'rich', 'forge', {}),
    ('zone:vespar_knoll', 'building:vespar_house', None, (91.5, 34.5), 'w', [2, 2], 'rich', 'tower_house', {}),
    ('wild:south_bank', 'building:reger_cell', None, (57.0, 95.5), 'n', [1, 1], 'rich', 'cottage', {}),
]
SERVICE_DOOR = {'gable_porch', 'L', 'jetty', 'cottage', 'tower_house', 'barn', 'forge'}
GRADE = {
    'poor': {'wall': 't06a01', 'window': 't06a04', 'door': 't06a03', 'post_left': 't06a07', 'post_right': 't06a07',
             'roof': 'xlslatemos', 'trim': 't06a10', 'ridge': 't06a10', 'gable': 't06a01'},
    'middle': {'wall': 't06b01', 'window': 't06c04', 'door': 't06b03', 'post_left': 't06b07', 'post_right': 't06b06',
               'roof': 't06a05', 'trim': 't06a10', 'ridge': 't06a10', 'gable': 't06b01'},   # trim: soffits, fascias,
    # porches and posts in plain timber (texture fit, 2026-11-20: the frieze band t06b11 tiled up porch posts, floors
    # and workshop soffits)
    'rich': {'wall': 't09a01', 'window': 't09a04b', 'door': 't09a03c', 'post_left': 't09a06', 'post_right': 't09a07',
             'roof': 'xlslate', 'trim': 't09b11b', 'ridge': 't06a10', 'gable': 't09a01'},
    'service': {'wall': 't09c01', 'window': 't09c04b', 'door': 't09a03a', 'post_left': 't09c06',
                'post_right': 't09c07', 'roof': 'xlslate', 'trim': 't09b11b', 'ridge': 't06a10', 'gable': 't09c01'},
}

def house_of(bid, index):
    key = bid if index is None else '%s#%d' % (bid, index)
    return HOUSE[key]

plots_by_space = {}
plan_buildings = {}
footprints = []
doors_out = []

def add_plot(space, bid, index, at, facing, fp, grade, kind, extra, on=None):
    x, y = at
    plot = {'building': bid, 'at': [x, y], 'facing': facing, 'kit': 'grey'}
    if index is not None:
        plot['index'] = index
    if on:
        plot['on'] = on
    hid, hname = house_of(bid, index)
    plot['house'] = hid
    plot['title'] = hname
    tex = dict(GRADE[grade])
    if hid in GATED:
        qname, closed = GATED[hid]
        plot['condition'] = {'qbit': qname}
        plot['else_effects'] = [msg(closed)]
    Wp, Hp = K.plot_extent(facing, fp)
    if kind == 'temple':
        # a nave with its door to the street and a squat bell tower at its back, under slate (as X5's)
        if facing in ('s', 'n'):
            nave = {'id': 'nave', 'at': [64, 64 + 256 if facing == 's' else 64], 'size': [Wp - 128, Hp - 128 - 256],
                    'wall_height': 416, 'roof': 'gable', 'roof_pitch': 50, 'ridge_along': 'ns'}
            tower = {'id': 'tower', 'at': [Wp // 2 - 144, 64 if facing == 's' else Hp - 352], 'size': [288, 288],
                     'wall_height': 832, 'roof': 'hip', 'roof_pitch': 62, 'windows': 'none'}
        else:
            nave = {'id': 'nave', 'at': [64 if facing == 'w' else 64 + 256, 64], 'size': [Wp - 128 - 256, Hp - 128],
                    'wall_height': 416, 'roof': 'gable', 'roof_pitch': 50, 'ridge_along': 'ew'}
            tower = {'id': 'tower', 'at': [Wp - 352 if facing == 'w' else 64, Hp // 2 - 144], 'size': [288, 288],
                     'wall_height': 832, 'roof': 'hip', 'roof_pitch': 62, 'windows': 'none'}
        plot['parts'] = [nave, tower]
        plot['door'] = {'part': 'nave', 'wall': facing}
    else:
        parts, door = K.shape(kind, facing, fp, 'grey', sign=extra.get('sign'))
        plot['parts'] = parts
        plot['door'] = door
    plot['textures'] = tex
    plots_by_space.setdefault(space, []).append(plot)
    pb = plan_buildings.setdefault(space, {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [],
                   'service': hname if not bid.startswith(('building:cv_houses', 'building:cv_drawkcab',
                                                           'building:gemsmith')) else 'residence'}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append((index or 0, fp))
    poly = K.footprint(x, y, facing, fp, 0)
    footprints.append((bid, index, poly))
    dc = K.door_cell(x, y, facing, fp, 0, 0.0)
    out = K.door_cell(x, y, facing, fp, 0, 0.9)
    doors_out.append((bid, index, dc, out))
    return plot

for (bid, index, at, facing, fp, grade, kind, extra) in PLOTS:
    add_plot('town:castleview', bid, index, at, facing, fp, grade, kind, extra)
_jp = add_plot('zone:cv_wall_top', *JETTY_PLOT, on='thing:jetty_deck')
for (space, bid, index, at, facing, fp, grade, kind, extra) in WILD_PLOTS:
    add_plot(space, bid, index, at, facing, fp, grade, kind, extra)
for _pb in plan_buildings.values():
    for _b in _pb.values():
        _b['footprint_cells'] = [fp for _, fp in sorted(_b['footprint_cells'], key=lambda t: t[0])]
        if _b['service'] in ('residence',) or _b['id'] in ('building:cv_jail', 'building:cv_public_storage',
                                                          'building:cv_library', 'building:vespar_house',
                                                          'building:reger_cell'):
            _b['service'] = 'residence'

# Brother Reger's door (q-d3): the cell opens once the word is said; before that the Drawkcab test
for _p in plots_by_space['wild:south_bank']:
    if _p['building'] == 'building:reger_cell':
        _p['condition'] = {'lua': 'Xeen.isSet("q-d3.word_said")'}
        _p['else_effects'] = [{'lua': (
            'if continueStep == 2 then %s return end '
            'if continueStep == 1 then %s return end '
            'if continueStep ~= nil then return end '
            'if not %s then return end '
            'evt.AskQuestion(eventId, 1, 0, 2, "What\'s the word?", {"palindrome", "palindromes"})'
            % (hcall('q-d3.reger_word'), hcall('q-d3.reger_wrong'), hcall('q-d3.reger_door')))}]

# ---------------------------------------------------------------------------------------------------------------
# Roads and paths (L1's sketch, the town's lanes redrawn for the plots)
# ---------------------------------------------------------------------------------------------------------------
NORTH_ROAD = [[64, 0], [64, 10], [64, 19], [64.5, 26], [64, 33], [63, 40]]
GATE_LANE = [[63, 40], [63, 44], [63, 51]]
EAST_ROAD = [[128, 60], [106, 60], [100, 60], [90, 60], [84, 60], [78, 60]]
WALL_ROAD = [[78, 60], [77.5, 56], [77, 50], [77, 44.5], [73, 41.5], [66, 40.2], [63, 40]]
EAST_BANK_LANE = [[84.5, 60], [84.5, 52], [85, 46], [85.5, 42.5], [88, 38]]
SARDAJ_LANE = [[88, 38], [88, 32], [88, 28.5]]
VESPAR_LANE = [[88, 38], [90, 36.2], [90.8, 35.6]]
POND_LANE = [[66, 40.2], [68.5, 37], [70, 34.5]]
WEST_ROAD = [[63, 40], [58, 41.5], [53, 41.5], [48, 44], [47.5, 47]]
HEATH_LANE = [[47.5, 47], [42, 45.5], [38, 44]]
TOWER_LANE = [[38, 44], [35, 40.5], [32, 37.5]]
MINE_LANE = [[38, 44], [36, 37], [36, 30], [37, 26.2], [44, 26.2], [45.5, 24]]
GROVE_PATH = [[36, 31], [41, 32.5], [44.5, 36.0], [47.5, 36.5]]   # round the great tree's south side to the rope
EDGE_PATH = [[38, 44], [31, 45.5], [26.5, 46]]
KALINDRA_ROAD = [[47.5, 47], [47.5, 54], [47.5, 62], [48, 67], [47.5, 70]]
QUEEN_LANE = [[51.0, 63.6], [49.5, 64.0], [48.0, 64.6]]
LUNA_LANE = [[47.5, 58], [40, 60], [33.5, 62]]
OBELISK_PATH = [[33.5, 62], [30, 68], [28, 75]]
SOUTH_LANE = [[90, 60], [90.5, 68], [88, 76], [84, 82], [76, 84], [68, 85.5], [60, 87.5], [53, 90]]
REGER_PATH = [[53, 90], [56, 93], [57.5, 94.6]]
FALISTA_PATH = [[53, 90], [49, 93], [46.5, 95]]
WRECK_PATH = [[55, 88.4], [54, 85]]
WELL_PATH = [[84, 82], [92, 88], [99, 92.5]]
MELON_PATH = [[79, 84.5], [82, 90]]
# the town's lanes
GUILD_ROW = [[51, 58], [71.5, 58]]
WEST_LANE = [[59, 56], [51.6, 56]]
BACK_LANE = [[55, 61], [62, 61]]
BACK_LANE_E = [[65.5, 61], [69.5, 61]]
YARD_LANE = [[63, 48], [71.5, 48], [71.5, 58]]
# A6 fix (2026-11-20): the walking line in from the Queen's Gate to the back lane, kept clear like the gate lanes
QUEEN_IN_LANE = [[53.0, 61.9], [55, 61]]
ROADS = [NORTH_ROAD, GATE_LANE, EAST_ROAD, WALL_ROAD, WEST_ROAD, KALINDRA_ROAD]
PATHS = [EAST_BANK_LANE, SARDAJ_LANE, VESPAR_LANE, POND_LANE, HEATH_LANE, TOWER_LANE, MINE_LANE, GROVE_PATH,
         EDGE_PATH, QUEEN_LANE, LUNA_LANE, OBELISK_PATH, SOUTH_LANE, REGER_PATH, FALISTA_PATH, WRECK_PATH,
         WELL_PATH, MELON_PATH]
TOWN_LANES = [GUILD_ROW, WEST_LANE, BACK_LANE, BACK_LANE_E, YARD_LANE, QUEEN_IN_LANE]

def wall_stretches():
    """The ring as stretches: the north wall west and east of the gatehouse, the west wall north and south of the
    jetty bastion (the Queen's Gate is a gate in the south-west stretch)."""
    gx = NORTH_GATE[0]
    # F19 (the user 2026-11-22, wall pieces meet flush): the north corners (53, 44) and (73, 44) joined two separate
    # walls whose ends stood proud of each other; each corner is now inside one line, so the studio mitres it
    return [
        ('ne', [[gx + 1.75, 44], [73, 44], [76, 47], [76, 61], [73, 64.5], [54.5, 64.5], [50, 60.5],
                [50, JETTY_Y[1]]]),
        ('nw', [[50, JETTY_Y[0]], [50, 47], [53, 44], [gx - 1.75, 44]]),
    ]

def check_roads():
    bad = []
    wall_lines = [l for _, l in wall_stretches()]
    for b, ix, poly in footprints:
        for line in ROADS:
            if K.line_hits_poly(line, poly, 0.45):
                bad.append('road under or against %s#%s: %s' % (b, ix, line[:3]))
        for line in PATHS + TOWN_LANES:
            if K.line_hits_poly(line, poly, 0.5):
                bad.append('path under %s#%s: %s' % (b, ix, line[:3]))
        if b != 'building:cv_lucio_jetty':
            for line in wall_lines:
                if K.line_hits_poly(line, poly, 0.7):
                    bad.append('wall against %s#%s' % (b, ix))
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
# The gate lanes (A6 fix, 2026-11-20: a tree stood before the Queen's Gate's portcullis inside). In front of each gate,
# inside and out, GATE_LANE_LEN cells along the walking line through it: no prop within the gate's half width plus its
# own radius plus 64 (D-14: a door's clearance; the walking line's 64), no tree within the half width plus
# GATE_TREE_MARGIN (a crown that reads as blocking the gate). Checked on the plan (structures, scatter) by gen.py
# and on the built scene by tools/gate_check.py.
# ---------------------------------------------------------------------------------------------------------------
GATE_LANE_LEN = 4.0
GATE_TREE_MARGIN = 0.75
_qa = (QUEEN_B[0] - QUEEN_A[0], QUEEN_B[1] - QUEEN_A[1])
_ql = math.hypot(*_qa)
_qalong = (_qa[0] / _ql, _qa[1] / _ql)
GATES = [("the north gate", NORTH_GATE, (1.0, 0.0), (0.0, -1.0), 384),
         ("the Queen's Gate", QUEEN_GATE, _qalong, (-_qalong[1], _qalong[0]), 320)]
TREE_WORDS = ('tree', 'swptree', 'bush')

def in_gate_lane(p, margin):
    """The gate whose lane holds p (cells) with `margin` cells beyond the opening's half width, else None."""
    for name, mid, along, normal, width in GATES:
        rx, ry = p[0] - mid[0], p[1] - mid[1]
        a = rx * along[0] + ry * along[1]
        n = rx * normal[0] + ry * normal[1]
        if abs(a) <= width / 1024.0 + margin and abs(n) <= GATE_LANE_LEN:
            return name
    return None

def prop_margin(name):
    return GATE_TREE_MARGIN if name and name.lower().startswith(TREE_WORDS) else 0.125 + 0.1

def check_gate_lanes(structures, scatter):
    bad = []
    skip = ('thing:wall_', 'thing:north_gate_', 'thing:queens_gate_', 'thing:gatehouse', 'thing:street_grate_')
    for s in structures:
        if s['id'].startswith(skip) or s.get('kind') in ('wall', 'platform') or 'at' not in s:
            continue
        x, y = s['at']
        pts = [(x, y)]
        if 'size' in s and s.get('kind') == 'building':
            w, h = s['size']
            pts = [(x, y), (x + w, y), (x, y + h), (x + w, y + h), (x + w / 2, y + h / 2)]
        for p in pts:
            g = in_gate_lane(p, prop_margin(s.get('decoration')))
            if g:
                bad.append('%s stands in the lane of %s at %s' % (s['id'], g, [round(v, 2) for v in p]))
                break
    for e in scatter:
        names = [e['decoration']] if e.get('decoration') else list(e.get('kinds') or [])
        margin = max(prop_margin(n) for n in names)
        if 'circle' in e:
            g = in_gate_lane(e['circle']['at'], margin + e['circle']['r'])
            if g:
                bad.append('%s (%s) stands in the lane of %s' % (e['id'], e['circle']['at'], g))
        elif 'polygon' in e:
            for name, mid, along, normal, width in GATES:
                hw = width / 1024.0 + margin
                for i in range(-8, 9):
                    for j in range(-8, 9):
                        a, n = hw * i / 8.0, GATE_LANE_LEN * j / 8.0
                        p = (mid[0] + along[0] * a + normal[0] * n, mid[1] + along[1] * a + normal[1] * n)
                        if K.inside(p, e['polygon']):
                            bad.append('%s may scatter into the lane of %s' % (e['id'], name))
                            break
                    else:
                        continue
                    break
    if bad:
        raise SystemExit('gate lanes (A6 fix):\n' + '\n'.join(bad))

# ---------------------------------------------------------------------------------------------------------------
# Ways in and the dungeon doors
# ---------------------------------------------------------------------------------------------------------------
PYRAMID_C = (60.0, 36.0)
PYRAMID_ARRIVAL = (61.6, 38.4)
ELLINGER_C = (71.2, 45.9)          # Ellinger's round tower in the north-east quarter, its door to the west
DD01_AT = (66.5, 57.5)             # the iron hatch by the square's south-east corner
DD04_AT = (68.5, 43.62)            # the gremlins' burrow under the north wall, east of the gate (outside)
KAL_GATE = (43.2, 70.0)            # Castle Kalindra's gate in its east front (DD-03)
KAL_HILL = (-12800, -3072, KAL_H + 800)   # the castle's middle (cells 39, 70), its keep's height: phase sound
KAL_SHOWN_VAR = 'kalindra_stage_shown'  # named map variable: the stage last shown on D1
KAL_ARRIVAL = (46.4, 70.0)
WT_C = (31.0, 33.0)                # the Western Tower's middle
WT_R = 1.4
ADIT_AT = (45.0, 22.2)             # DD-10's west adit in the mine hill over the gemsmiths
# The Dark Grove's great tree (A6 fix, 2026-11-20; MAPS: "a forest whose tallest tree carries a rope into the sky"):
# a tapered 16-sided BModel trunk in xdbark with root buttresses (D2's route), shipped crowns on its top, the rope
# hanging from the crown to a foot one can reach; the rope's D7 return point stays at (-8192, 14336, 1088) facing 768
GREAT_C = (46.2, 34.0)             # the trunk's middle
GREAT_R = 760                      # the trunk's radius at its foot (map units; D2's proportions, A6 2026-11-20)
GREAT_FOOT = 384                   # the buttressed foot's height
GREAT_H = 2800                     # the tapered trunk above the foot
GREAT_TAPER = 0.72                 # 760 -> 547 at the top, under the crown's 539 stub (S's crown is built for 547)
GREAT_FLOOR = 1088                 # the grove's floor there (the land is level at 1,088)
GREAT_TOP = GREAT_FOOT + GREAT_H   # the trunk's top over its floor (3,184)
# The crown: S's great-tree crown (decoration xeen_greatcrown, row 4001, D-23), one model on the trunk's top. Its stub is
# a 16-gon of radius 539 sunk 200 into the trunk (raise = trunk top - 200); its corners stand at 0, 22.5, ... degrees,
# the trunk's at 11.25 + k * 22.5 (measured in the build), so the crown turns 11.25 to line them up.
GREAT_CROWN = 'xeen_greatcrown'
GREAT_CROWN_RAISE = GREAT_TOP - 200
GREAT_CROWN_TURN = 11.25
# the electrapedes' three clearings round the great tree, clear of the trunk and of D7's return point (A6 fix: they
# stood in the new trunk; the nearest pack is now about 1,350 from the rope's foot, was 512)
# D-85 (A6 s30): the second pack moved to the tree's west side, off Justine's camp (was (50.4, 37.4): 3,745)
ELECTRAPEDES = [(49.8, 32.6), (40.5, 35.5), (43.2, 33.2)]
GROVE_ROPE_ARRIVAL = (48.0, 36.0)  # D7's return point (-8192, 14336, 1088), facing the tree (768)
_ga = math.atan2(GROVE_ROPE_ARRIVAL[1] - GREAT_C[1], GROVE_ROPE_ARRIVAL[0] - GREAT_C[0])
ROPE_AT = (round(GREAT_C[0] + math.cos(_ga) * 1000 / 512.0, 3), round(GREAT_C[1] + math.sin(_ga) * 1000 / 512.0, 3))
# the trunk's wall facing the rope carries no buttress (a round part's wall 0 looks south, the walls run
# anticlockwise, 22.5 degrees apart): the rope's foot stands clear
ROPE_WALL = round((math.degrees(_ga * -1) + 90) / 22.5) % 16
ROPE_H = 3900                      # from the foot up into the crown's leaves (their underside ~3,560 there)
GREAT_TREE = ROPE_AT               # the POI (the rope's click)
# D-26/D-27 (A6's relay, act3_a8_decisions_a.md): DD-01's outfall grate in the gorge's west wall by the burnt mill,
# barred from inside until A3's hook m16.outfall (qbit outfall_unbarred 111323, lifted from inside in DD-01) holds
OUTFALL_AT = (79.0, 48.0)          # the headwall's front middle, looking east over the river
OUTFALL_ARRIVAL = (79.7, 48.0)     # in front of the grate on the gorge floor, facing away from it (east)
# the ghost castle's shimmer (D-27): xkshimmer, shared with DD-03's phase walls, once A6 has installed it
GHOST_TEX = 'xkshimmer' if os.path.exists(os.path.join(XEEN, 'textures_x4', 'xkshimmer.oytex')) else 'hcwall'
# an arms panel (128 x 256, once, whole) on a slab's front, coping on its back and ends (texture fit)
CREST_WALLS_N = {'n': ['xkkalcrst'], 's': ['cstr128']}
CREST_WALLS_E = {'e': ['xkkalcrst'], 'w': ['cstr128']}
DD02_WALL = '9'                    # the round tower's west wall (12 sides; checked in build.json)
WT_WALL = '0'                      # the Western Tower's south wall

def build():
    os.makedirs(OUT, exist_ok=True)
    # ================================ project.yml
    L1P = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'project.yml')))
    neighbours = []
    for n in L1P['neighbours']:
        n = copy.deepcopy(n)
        if n['id'] == 'edge:east':
            if not D2_LIVE:
                continue
            n['notes'] = ("D2 Sprite Forest and Ogre Pass (A6): the road crosses the edge at y 60 on both maps; "
                          "D2's edge:west arrives at D1's east start %s facing west." % (list(EAST_START),))
        if n['id'] == 'edge:north' and not D6_LIVE:
            continue
        if n['id'] == 'scripted:kalindra_griffin':
            continue
        if n['id'] == 'mirror:darkside':
            continue
        if n['id'] == 'pyramid:vertigo':
            n['listed_only'] = True
            n.pop('arrival', None)
            n['notes'] = ("The travel pyramid outside the north gate: A3's m7.pyramid_d1 (Xeen.travelPyramid"
                          "('castleview'), the Pyramid Sigil). X1's pyramid sets the party down at castleview_pyramid.")
        if n['id'] == 'stable:kramer':
            n['listed_only'] = True
            n.pop('schedule', None)
        if n['id'] == 'boat:lucio':
            n['listed_only'] = True
            n.pop('schedule', None)
            n.pop('arrival', None)
            n.pop('condition', None)
        if n['id'] == 'rope:dark_grove':
            n['listed_only'] = True
            n['notes'] = ("The rope from the sky into the Dark Grove's great tree: A3's m30.grove_rope (m30.done); "
                          "D7 is built in phase 6, until then its yes branch says so.")
        if n['id'].startswith('door:dd'):
            key = n['id'][5:9] if not n['id'].startswith('door:dd10a') else 'dd10a'
            key = 'dd05' if n['id'].startswith('door:dd05') else key
            n.pop('condition', None)
            n.pop('arrival', None)
            if not DUNGEON[key]:
                n['listed_only'] = True
                n['notes'] = n.get('notes', '') + ' Not installed yet: the door shows its hook and a sealed message.'
            elif n['id'] in DD05_ARRIVAL:
                n['arrival'] = DD05_ARRIVAL[n['id']]       # DD-05's named inside arrivals (A8, installed 2026-11-20)
        neighbours.append(n)
    if D2_LIVE:
        for n in neighbours:
            if n['id'] == 'edge:east':
                n['days'] = 5          # A2's travel row (outdoor_travels: D1-D2 5 days) and D2's own edge
    project = {
        'format': 0, 'id': STEM, 'name': 'Castleview Vale', 'world': 'xeen', 'kind': 'outdoor', 'profile': 'odm',
        'map_code': 'D1', 'units': {'plan_grid': 512}, 'extent': {'terrain_cells': 128},
        'map_stats': {
            'id': 9108, 'continent': 6, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 2,
            'perception_difficulty': 2, 'refill_days': 672, 'music': 37, 'environment': 'plains',
            'lock_difficulty': 4,
            'slots': [
                # A2's recount (relayed 2026-11-20): kill XP 0.81 of the 18.3k target at Dif 1; Dif 3, 3, 2 (tier
                # mixes 50/30/20, 50/30/20, 70/20/10) bring it to about 1.0 with the same 135 hostiles
                {'monster': 'Xeen Gremlin', 'tier': 3, 'per_marker': [2, 3], 'weight': 40},
                {'monster': 'Xeen Arachnoid', 'tier': 3, 'per_marker': [2, 4], 'weight': 30},
                {'monster': 'Xeen Crawler', 'tier': 2, 'per_marker': [2, 3], 'weight': 30},
            ]},
        'neighbours': neighbours,
        'qbits': dict(QBIT),
        'items': {k: v for k, v in ITEMS.items()},
        'rules': {'weather': 'none', 'respawn': 'entrance:castleview_temple',
                  'town_portal_anchor': 'entrance:castleview_square'},
        'notes': ("D1 Castleview Vale (A6, 2026-11-20), built from the approved L1 with D-23, D-5.3 and D-9.3. The "
                  "north edge (D6) is sealed with a sign until D6 exists; the east edge (D2) too until D2 is installed "
                  "(D2_LIVE); every dungeon door shows its hook and a sealed message until its map is installed. "
                  "Written by output/studio_cal/d1/tools/gen.py."),
    }
    # ================================ plan.yml (L1's spaces with the decisions applied)
    L1 = yaml.safe_load(open(os.path.join(BRIEFS, 'L1', 'plan.yml')))
    plan = copy.deepcopy(L1)
    plan['level'] = 'L3'
    for s in plan['spaces']:
        if s['id'] in plan_buildings:
            s['buildings'] = list(plan_buildings[s['id']].values())
        elif 'buildings' in s:
            s.pop('buildings')
        if s['id'] == 'town:castleview':
            s['theme'] = s['theme'].replace('a gatehouse with Castleview\'s banner',
                                            "a gatehouse with Castleview's banner in the north wall and the small "
                                            "Queen's Gate in the south-west wall onto the Kalindra road (D-23)")
        if s['id'] == 'zone:cv_square':
            s['purpose'] = ("The mirror and Lyle's reserved bench beside it (one spot, D-23), the magic shop, the "
                            "alchemist, the town hall and the bank open onto it; the sewer hatch in its south-east "
                            "corner. Town Portal arrival.")
        if s['id'] == 'water:vale_water':
            s['purpose'] = ("D1's own river (D-23): from the Sardaj spring under the north hills south through the mill "
                            "gorge east of the walls, west under Kalindra's rise, over the south rim (y 104) into the "
                            "stars. It touches no map edge.")
    # F10 (2026-11-21): the moved markers' populations (counts and slots kept; see the encounter areas)
    _f10 = {'pop:west_heath': 4, 'pop:siege_north': 7, 'pop:foothills': 3}
    _f10_new = {
        'zone:rim_headland': {'id': 'pop:rim_headland', 'slot': 2, 'groups': 2, 'per_marker': [2, 4],
                              'levels': [14, 24], 'notes': "F10: arachnoids on the headland's south slope along the "
                                                           "rim (two of the west heath's groups)."},
        'wild:south_bank': {'id': 'pop:south_bank', 'slot': 3, 'groups': 2, 'per_marker': [2, 3],
                            'levels': [16, 26], 'notes': "F10: crawlers west of Falista's hut (two of the foothills' "
                                                         "groups)."},
        'zone:kalindra_rise': {'id': 'pop:north_bank', 'slot': 1, 'groups': 2, 'per_marker': [2, 3],
                               'levels': [14, 22], 'notes': "F10: the siege's south line, gremlins on the river's north "
                                                            "bank below the south wall, east of the rise (two of the "
                                                            "siege lines' groups)."},
    }
    for s in plan['spaces']:
        for g in s.get('population') or []:
            if g['id'] in _f10:
                g['groups'] = _f10[g['id']]
        if s['id'] in _f10_new:
            s.setdefault('population', []).append(_f10_new[s['id']])
            if s.get('safe'):
                s['safe'] = False   # F10: no longer monster-free (the user's empty-land feedback)
    sealed_edges = []
    if not D2_LIVE:
        sealed_edges.append('edge:east')
    if not D6_LIVE:
        sealed_edges.append('edge:north')
    plan['entrances'] = [e for e in plan['entrances'] if e.get('neighbour') not in sealed_edges]
    for e in plan['entrances']:
        e.pop('condition', None)
        if e['id'] == 'entrance:north_gate':
            e['how'] = ("The gatehouse in the north wall: outside, A3's m14.gate (the pass or court_won) then "
                        "m14.gate_open; inside it always opens. The Queen's Gate in the south-west wall does the same "
                        "(D-23).")
        if e.get('neighbour') == 'scripted:kalindra_griffin' or e.get('neighbour') == 'mirror:darkside':
            e.pop('neighbour')
        if e['id'] == 'entrance:grove_rope':
            # D-58 Q10 and the entrance-name rule: D7's rope comes down here, so it is named after D7
            e['id'] = 'entrance:d7_rope'
            e['kind'] = 'both'
            e['how'] = ("The rope from the sky at the great tree's foot: up to D7's rope head (entrance:d1_rope) "
                        "after m30.done, and D7's 'Descend to the Darkness Below?' lands here.")
        if e['id'] == 'entrance:dd05_rope':
            # D-42: the rope's foot is also the way back (DD-05's top by the rope): a named arrival facing 512, away
            # from the wall
            e['kind'] = 'both'
            e['facing'] = 'n'
    plan['entrances'].append({'id': 'entrance:d7_fall', 'space': 'town:castleview', 'kind': 'arrival', 'facing': 's',
                              'how': ("D-58 Q10: a fall from D7's zone A3-B4 lands here, 1,024 north of Lucio's Jetty "
                                      "(Xeen.SkyFalls.d7_d1; Lucio's boats sail up to Olympus after m30.done).")})
    plan['entrances'].append({'id': 'entrance:queens_gate', 'space': 'town:castleview', 'kind': 'both', 'facing': 'ne',
                              'how': ("The Queen's Gate (D-23), a small gate in the south-west wall onto the Kalindra "
                                      "road: m14.gate / m14.gate_open from outside, open from inside.")})
    plan['entrances'].append({'id': 'entrance:dd01_outfall', 'space': 'zone:mill_gorge', 'kind': 'both',
                              'neighbour': 'door:dd01', 'facing': 'e',
                              'how': ("DD-01's outfall grate in the gorge's west wall by the burnt mill (D-26): "
                                      "barred from inside until A8's bar is lifted (A3's qbit).")})
    plan['links'].append({'id': 'link:queen_lane', 'from': 'entrance:queens_gate', 'to': 'link:kalindra_road',
                          'kind': 'path', 'notes': "From the Queen's Gate to the Kalindra road (D-23)."})
    plan['links'].append({'id': 'link:yard_lane', 'from': 'link:gate_lane', 'to': 'zone:cv_coach_yard',
                          'kind': 'road', 'notes': "From Gate Street east past the jail and down the coach yard."})
    for l in plan['links']:
        if l['id'] == 'link:rope_bridge':
            l['notes'] = "Cut until q-d1.court_won (A3's q-d1.sabotage): the map shows the mended bridge then."
    # the POI list after D-23's merges
    for p in plan['points_of_interest']:
        if p['id'] == 'poi:falls':
            p['behaviour'] = "Where the Vale Water goes over the edge: a view, no click (D-23)."
        if p['id'] == 'poi:bottle':
            p['behaviour'] = "A bottle with a message, in the wreck's hull (one spot with the wreck, D-23)."
        if p['id'] == 'poi:heretic_pack':
            p['behaviour'] = "The heretic's pack where he fell, at the rope's foot (one spot with the rope, D-23)."
        if p['id'] == 'poi:lyle_bench':
            p['behaviour'] = "Lyle's bench beside the mirror (one spot with the mirror, D-23)."
        if p['id'] == 'poi:great_tree':
            p['behaviour'] = "The great tree and the rope from the sky (A3's m30.grove_rope; D7 in phase 6)."
    plan['pitch'] = plan['pitch'].replace('and one gate in its north wall', 'a gatehouse in its north wall and the '
                                          "small Queen's Gate in its south-west wall")
    plan.pop('totals', None)
    plan['sketch'] = {'file': 'sketch.yml', 'grid': 512}
    plan['notes'] = ('L3/L4 written by output/studio_cal/d1/tools/gen.py from the approved L1 with D-23, D-5.3, D-9.3. '
                     'The plan keeps the L1 spaces.')
    plan['critical_path'] = ['entrance:castleview_pyramid', 'zone:gate_yard', 'entrance:north_gate', 'zone:cv_square',
                             'entrance:dd02_tower', 'zone:kalindra_gate']
    plan['states'] = [{'id': 'state:jetty_closed', 'condition': {'not': {'qbit': 'lucio_open'}},
                       'locks': ['building:cv_lucio_jetty'],
                       'atmosphere': "A jetty that ends in thin air (A4's closed text)."},
                      {'id': 'state:jetty_open', 'condition': {'qbit': 'lucio_open'},
                       'opens': ['building:cv_lucio_jetty']}]
    # ================================ sketch.yml
    rim = [
        {'side': 'west', 'form': 'level', 'height': 0, 'meet': 1,
         'notes': 'The world rim: the land ends in a cliff at x 24; below, water at 0 stands for the stars.'},
        {'side': 'south', 'form': 'level', 'height': 0, 'meet': 1,
         'notes': 'The world rim: the cliff at y 104 (D-23); the Vale Water falls over it at x 31.'},
        {'side': 'north', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1},
        {'side': 'north', 'span': [24, 59], 'form': 'ridge', 'height': [2600, 3400], 'floor': 2000, 'crest': 10,
         'roughness': 120, 'notes': "The mine hills and the Forbidden Zone's southern border."},
        {'side': 'north', 'span': [59, 70], 'form': 'level', 'height': 2000, 'meet': 6,
         'notes': "The mountain road's valley, open to the edge (D6, sealed)."},
        {'side': 'north', 'span': [70, 128], 'form': 'ridge', 'height': [2800, 3600], 'floor': 2200, 'crest': 10,
         'roughness': 120, 'notes': "The Sardaj Horn and the Gemstone Range's western foothills."},
        {'side': 'east', 'span': [0, 46], 'form': 'ridge', 'height': [2200, 3000], 'floor': 1800, 'crest': 10,
         'roughness': 120, 'notes': 'The Gemstone foothills run on into D2.'},
        {'side': 'east', 'span': [46, 104], 'form': 'level', 'height': 1100, 'meet': 6,
         'notes': "The vale opens east into D2's woods; the road at y 60."},
        {'side': 'east', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1},
    ]
    cliffs = [
        {'line': [[RIM_X, 0], [RIM_X, 22]], 'drop': 1800, 'down': 'right', 'notes': 'The rim, west: the crag.'},
        {'line': [[RIM_X, 22], [RIM_X, 40]], 'drop': 1500, 'down': 'right',
         'notes': "The rim, west: by the Western Tower's knoll."},
        {'line': [[RIM_X, 40], [RIM_X, 70]], 'drop': 1100, 'down': 'right', 'notes': 'The rim, west: the heath.'},
        {'line': [[RIM_X, 70], [RIM_X, 84]], 'drop': 1300, 'down': 'right', 'notes': "The rim, west: the headland."},
        {'line': [[RIM_X, 84], [RIM_X, RIM_Y]], 'drop': 1000, 'down': 'right'},
        {'line': [[RIM_X, RIM_Y], [30, RIM_Y]], 'drop': 1000, 'down': 'right'},
        {'line': [[33, RIM_Y], [60, RIM_Y]], 'drop': 1000, 'down': 'right', 'notes': 'The rim, south: the bank.'},
        {'line': [[60, RIM_Y], [128, RIM_Y]], 'drop': 950, 'down': 'right', 'notes': 'The rim, south: the meadows.'},
        {'line': [[36, 78], [46, 80]], 'drop': 450, 'down': 'right',
         'notes': "Kalindra's rise, its south face over the Vale Water."},
    ]
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its land function.'},
        'points': [
            {'at': [64, 19], 'h': 1550, 'notes': 'the D6 road at the foot of the mountain valley'},
            {'at': [78, 8], 'h': 3600, 'notes': 'the Sardaj Horn'},
            {'at': [44, 8], 'h': 3300, 'notes': "the mine hills' crest"},
            {'at': [84, 17], 'h': 2100, 'notes': 'the cliff over the Sardaj spring'},
        ],
        'ridges': [
            {'line': [[70, 4], [78, 8], [84, 14]], 'height': [3000, 3600, 2800], 'width': 2, 'slope': 3,
             'notes': "The Sardaj Horn's ridge, east of the mountain road."},
            {'line': [[34, 6], [44, 8], [54, 12]], 'height': [2900, 3300, 2600], 'width': 2, 'slope': 3,
             'notes': "The mine hills' crest, west of the mountain road."},
        ],
        'terraces': [
            {'polygon': TOWN_TERRACE, 'height': TOWN_H, 'slope': 3, 'notes': 'Castleview and its walls.'},
            {'polygon': [[30, 22.8], [47, 22.8], [47, 27], [30, 27]], 'height': SHELF_H, 'slope': 3,
             'notes': "The gemsmiths' row on its shelf."},
            {'polygon': [[29, 31], [33, 31], [33, 35.5], [29, 35.5]], 'height': TOWER_H, 'slope': 3,
             'notes': "The Western Tower's knoll top."},
            {'polygon': [[57.5, 33.5], [62.8, 33.5], [62.8, 39], [57.5, 39]], 'height': 1250, 'slope': 3,
             'notes': "The travel pyramid's knoll."},
            {'polygon': [[84.5, 21.5], [92.5, 21.5], [92.5, 29], [84.5, 29]], 'height': CAMP_H, 'slope': 3,
             'notes': 'The Sardaj camp.'},
            {'polygon': [[90, 33], [95, 33], [95, 38], [90, 38]], 'height': 1350, 'slope': 3,
             'notes': "Vespar's knoll."},
            {'polygon': [[34.5, 63], [43.5, 63], [43.5, 77], [34.5, 77]], 'height': KAL_H, 'slope': 3,
             'notes': "Castle Kalindra's rise."},
            {'polygon': [[43.5, 67.5], [48.5, 67.5], [48.5, 72.5], [43.5, 72.5]], 'height': FORECOURT_H, 'slope': 3,
             'notes': "Kalindra's forecourt at the ramp's top."},
            {'polygon': [[49.5, 88], [54.5, 88], [54.5, 92], [49.5, 92]], 'height': 1250, 'slope': 2,
             'notes': "The prayer shrine's knoll (the signature view)."},
            {'polygon': [[57.5, 66], [71, 66], [71, 71], [57.5, 71]], 'height': 1100, 'slope': 2,
             'notes': "Pip Melonby's field."},
            {'polygon': [[102, 56], [110, 56], [110, 64], [102, 64]], 'height': 1100, 'slope': 2,
             'notes': "The east road's end: the D2 arrival."},
            {'polygon': [[43.2, 21], [46.8, 21], [46.8, 22.8], [43.2, 22.8]], 'height': SHELF_H, 'slope': 0,
             'notes': "The adit's floor."},
        ],
        'cliffs': cliffs + [
            {'line': [[43, 21], [47, 21]], 'drop': 300, 'down': 'right', 'notes': "The adit's face in the mine hill."},
        ],
    }
    water = {
        'rivers': [
            {'id': 'water:vale_water', 'line': RIVER_LINE, 'width_cells': 2.5, 'level': RIVER,
             'notes': ('The Vale Water (D-23: D1\'s own): from the Sardaj spring south through the mill gorge, west '
                       'under Kalindra\'s rise, over the south rim at x 31.')},
        ],
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0,
             'polygon': [[0, 0], [RIM_X - 1, 0], [RIM_X - 1, RIM_Y + 1], [128, RIM_Y + 1], [128, 128], [0, 128]],
             'notes': 'Below the rim: stands for the stars (the game draws no void).'},
            {'id': 'water:acid_pond', 'kind': 'pond', 'level': ACID_H, 'polygon': ACID,
             'notes': 'The acid pond: green, no fish, a cracked mud rim.'},
            {'id': 'water:vale_water', 'kind': 'pond', 'level': RIVER,
             'polygon': [[82, 17], [86, 17], [87, 21], [83, 21], [81, 19]],
             'notes': 'The Sardaj spring: the Vale Water rises in a pool at the cliff foot.'},
        ],
    }
    roads = [
        {'link': 'link:north_road', 'line': NORTH_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:gate_lane', 'line': GATE_LANE, 'width': 'road', 'surface': 'road_flagstone'},
        {'link': 'link:east_road', 'line': EAST_ROAD, 'width': 'road', 'surface': 'road_pebbles',
         'notes': 'Over the Vale Water by the East Bridge (thing:east_bridge); no tiles in the water.'},
        {'link': 'link:wall_road', 'line': WALL_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:west_road', 'line': WEST_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:kalindra_road', 'line': KALINDRA_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:east_bank_lane', 'line': EAST_BANK_LANE, 'width': 'lane'},
        {'link': 'link:sardaj_lane', 'line': SARDAJ_LANE, 'width': 'lane'},
        {'link': 'link:vespar_lane', 'line': VESPAR_LANE, 'width': 'lane'},
        {'link': 'link:pond_lane', 'line': POND_LANE, 'width': 'lane'},
        {'link': 'link:heath_lane', 'line': HEATH_LANE, 'width': 'lane'},
        {'link': 'link:tower_lane', 'line': TOWER_LANE, 'width': 'lane'},
        {'link': 'link:mine_lane', 'line': MINE_LANE, 'width': 'lane'},
        {'link': 'link:grove_path', 'line': GROVE_PATH, 'width': 'lane'},
        {'link': 'link:edge_path', 'line': EDGE_PATH, 'width': 'lane'},
        {'link': 'link:queen_lane', 'line': QUEEN_LANE, 'width': 'lane'},
        {'link': 'link:luna_lane', 'line': LUNA_LANE, 'width': 'lane'},
        {'link': 'link:obelisk_path', 'line': OBELISK_PATH, 'width': 'lane'},
        {'link': 'link:south_lane', 'line': SOUTH_LANE, 'width': 'lane'},
        {'link': 'link:reger_path', 'line': REGER_PATH, 'width': 'lane'},
        {'link': 'link:falista_path', 'line': FALISTA_PATH, 'width': 'lane'},
        {'link': 'link:wreck_path', 'line': WRECK_PATH, 'width': 'lane'},
        {'link': 'link:well_path', 'line': WELL_PATH, 'width': 'lane'},
        {'link': 'link:melon_path', 'line': MELON_PATH, 'width': 'lane'},
        {'link': 'link:guild_row', 'line': GUILD_ROW, 'width': 'lane', 'surface': 'road_flagstone'},
        {'link': 'link:west_lane', 'line': WEST_LANE, 'width': 'lane', 'surface': 'road_flagstone'},
        {'link': 'link:back_lane', 'line': BACK_LANE, 'width': 'lane', 'surface': 'road_flagstone'},
        {'link': 'link:back_lane', 'line': BACK_LANE_E, 'width': 'lane', 'surface': 'road_flagstone'},
        {'link': 'link:yard_lane', 'line': YARD_LANE, 'width': 'lane', 'surface': 'road_flagstone'},
        {'link': 'link:queen_lane', 'line': QUEEN_IN_LANE, 'width': 'lane', 'surface': 'road_flagstone'},
    ]
    TOWN_POLY = WALL
    districts = [
        {'space': 'town:castleview', 'polygon': TOWN_POLY, 'plots': plots_by_space['town:castleview']},
        {'space': 'zone:cv_square', 'polygon': SQUARE},
        {'space': 'zone:cv_coach_yard', 'polygon': [[70.5, 47], [72, 47], [72, 58], [70.5, 58]]},
        {'space': 'zone:cv_wall_top', 'polygon': [[47, 52.5], [52, 52.5], [52, 56], [47, 56]],
         'plots': plots_by_space['zone:cv_wall_top']},
        {'space': 'zone:gate_yard', 'polygon': [[55, 39], [71, 39], [71, 43.5], [55, 43.5]]},
        {'space': 'zone:pyramid_knoll', 'polygon': [[57, 33], [63, 33], [63, 39], [57, 39]]},
        {'space': 'wild:siege_lines', 'polygon': [[56, 22], [80, 22], [80, 39], [71, 39], [66, 37], [63, 32],
                                                 [56, 30]]},
        {'space': 'zone:mill_gorge', 'polygon': [[77, 41], [86, 41], [86, 49], [77, 49]]},
        {'space': 'wild:sardaj_lands', 'polygon': [[84, 19], [100, 19], [100, 30], [96, 42], [96, 50], [86, 50],
                                                   [85, 42], [83, 30]]},
        {'space': 'zone:sardaj_camp', 'polygon': [[84, 21], [93, 21], [93, 30], [84, 30]]},
        {'space': 'zone:vespar_knoll', 'polygon': [[90, 33], [96, 33], [96, 39], [90, 39]],
         'plots': plots_by_space['zone:vespar_knoll']},
        {'space': 'wild:gemstone_foothills', 'polygon': [[96, 19], [110, 19], [110, 51], [100, 51], [96, 44]]},
        {'space': 'wild:east_road_camp', 'polygon': [[86, 52], [101, 52], [101, 78], [90, 79], [86, 70]]},
        {'space': 'zone:east_arrival', 'polygon': [[102, 56], [110, 56], [110, 64], [102, 64]]},
        {'space': 'wild:dark_grove', 'polygon': [[38, 28], [56, 28], [57, 33], [53, 38], [44, 42], [38, 38]]},
        {'space': 'zone:great_tree', 'polygon': [[45, 32], [50, 32], [50, 37], [45, 37]]},
        {'space': 'wild:west_heath', 'polygon': [[25, 28], [37, 28], [38, 46], [45, 57], [25, 57]]},
        {'space': 'zone:western_tower', 'polygon': [[27, 29], [35, 29], [35, 37], [27, 37]]},
        {'space': 'zone:gemsmiths_row', 'polygon': [[30, 19], [48, 19], [48, 27], [30, 27]],
         'plots': plots_by_space['zone:gemsmiths_row']},
        {'space': 'zone:kalindra_rise', 'polygon': [[34, 63], [46, 62], [50, 68], [47, 78], [40, 80], [34, 77]]},
        {'space': 'zone:kalindra_gate', 'polygon': [[44, 68], [49, 68], [49, 73], [44, 73]]},
        {'space': 'zone:luna_grove', 'polygon': [[27, 58], [35, 58], [35, 66], [27, 66]]},
        {'space': 'zone:rim_headland', 'polygon': [[24, 70], [31, 70], [31, 80], [24, 80]]},
        {'space': 'zone:melon_field', 'polygon': [[57, 66], [71, 66], [71, 71], [57, 71]]},
        {'space': 'wild:south_meadows', 'polygon': [[60, 84], [80, 76], [90, 74], [110, 74], [110, 104], [60, 104]]},
        {'space': 'zone:melon_patch', 'polygon': [[79, 89], [85, 89], [85, 94], [79, 94]]},
        {'space': 'zone:might_well', 'polygon': [[96, 90], [103, 90], [103, 97], [96, 97]]},
        {'space': 'wild:south_bank', 'polygon': [[38, 88], [44, 84], [52, 84], [60, 84], [60, 104], [33, 104],
                                                 [33, 100]],
         'plots': plots_by_space['wild:south_bank']},
        {'space': 'zone:shrine_knoll', 'polygon': [[49, 88], [55, 88], [55, 93], [49, 93]]},
        {'space': 'wild:north_hills', 'polygon': [[24, 0], [128, 0], [128, 18], [110, 19], [100, 17], [86, 16],
                                                  [72, 16], [67, 14], [61, 14], [56, 17], [46, 16], [36, 18],
                                                  [24, 19]]},
        {'space': 'zone:rim', 'polygon': [[0, 0], [RIM_X, 0], [RIM_X, RIM_Y], [128, RIM_Y], [128, 128], [0, 128]]},
    ]
    points = [
        {'id': 'entrance:castleview_square', 'at': [63, 55.5], 'facing': 'n'},
        {'id': 'entrance:castleview_pyramid', 'at': list(PYRAMID_ARRIVAL), 'facing': 'se'},
        {'id': 'entrance:castleview_temple', 'at': [69.4, 60], 'facing': 'e'},
        {'id': 'entrance:castleview_stables', 'at': [71.3, 54.5], 'facing': 'e'},
        {'id': 'entrance:kalindra_gate', 'at': list(KAL_ARRIVAL), 'facing': 'w'},
        {'id': 'entrance:north_gate', 'at': [63, 42.6], 'facing': 's'},
        {'id': 'entrance:queens_gate', 'at': [51.3, 63.6], 'facing': 'ne'},
        {'id': 'entrance:dd01_hatch', 'at': [DD01_AT[0] - 0.9, DD01_AT[1]], 'facing': 'e'},
        {'id': 'entrance:dd01_outfall', 'at': list(OUTFALL_ARRIVAL), 'facing': 'e'},
        {'id': 'entrance:dd02_tower', 'at': [ELLINGER_C[0] - 1.9, ELLINGER_C[1]], 'facing': 'e'},
        {'id': 'entrance:dd03_gate', 'at': [KAL_GATE[0] + 1.6, KAL_GATE[1]], 'facing': 'w'},
        {'id': 'entrance:dd04_burrow', 'at': [DD04_AT[0], DD04_AT[1] - 1.2], 'facing': 's'},
        {'id': 'entrance:dd05_rope', 'at': [WT_C[0], WT_C[1] - WT_R - 0.9], 'facing': 'n'},   # D-42: 512, off the wall
        {'id': 'entrance:dd05_door', 'at': [WT_C[0], WT_C[1] + WT_R + 0.9], 'facing': 's'},  # A8: 1536, away from the door
        {'id': 'entrance:dd10a_adit', 'at': [ADIT_AT[0], ADIT_AT[1] + 1.4], 'facing': 'n'},
        {'id': 'entrance:d7_rope', 'at': list(GROVE_ROPE_ARRIVAL), 'facing': 'nw'},    # D-58: D7's rope comes down here
        # D-58 Q10: a fall from D7's zone A3-B4 lands here, 1,024 north of Lucio's Jetty (whole flat cell, s16 check)
        {'id': 'entrance:d7_fall', 'at': [51, 52], 'facing': 's'},
        {'id': 'entrance:lucio_jetty', 'at': [50.8, 53.8], 'facing': 'w'},
        {'id': 'junction:gate_fork', 'at': [63, 40]}, {'id': 'junction:mill_fork', 'at': [77.4, 44.5]},
        {'id': 'junction:east_bridge', 'at': [78, 60]}, {'id': 'junction:east_fork', 'at': [90, 60]},
        {'id': 'junction:pond_fork', 'at': [88, 38]}, {'id': 'junction:west_fork', 'at': [47.5, 47]},
        {'id': 'junction:heath_fork', 'at': [38, 44]}, {'id': 'junction:south_fork', 'at': [84, 82]},
        {'id': 'junction:shrine_fork', 'at': [53, 90]},
        {'id': 'landmark:castleview_walls', 'at': [63, 44]}, {'id': 'landmark:ellinger_tower', 'at': list(ELLINGER_C)},
        {'id': 'landmark:pyramid', 'at': list(PYRAMID_C)}, {'id': 'landmark:grove_tree', 'at': list(GREAT_C)},
        {'id': 'landmark:western_tower', 'at': list(WT_C)}, {'id': 'landmark:kalindra', 'at': [39, 70]},
        {'id': 'landmark:broken_bridge', 'at': [81, 43]}, {'id': 'landmark:falls', 'at': [31, 104]},
        {'id': 'landmark:sardaj_horn', 'at': [78, 8]},
    ]
    POI_AT = {'poi:pyramid': PYRAMID_C, 'poi:gate_notice': (62.3, 43.25), 'poi:joe_stall': (66, 41),
              'poi:justine_camp': (57, 41), 'poi:broken_bridge': (81, 43), 'poi:burned_mill': (79, 46),
              'poi:acid_pond': (70, 34), 'poi:sardaj_camp': (88, 25), 'poi:yog': (89, 24),
              'poi:great_tree': GREAT_TREE, 'poi:luna': (30.6, 62.6), 'poi:obelisk': (27, 76),
              'poi:falista_hut': (46, 95), 'poi:prayer_shrine': (52, 90), 'poi:might_well': (100, 93),
              'poi:melon_patch': (82, 91), 'poi:melon_field': (64, 67.4), 'poi:shipwreck': (53, 83),
              'poi:besiegers_camp': (96, 63), 'poi:heretic_pack': (31.5, 31), 'poi:webbed_pack': (43, 38),
              'poi:wayside_shrine': (103, 58), 'poi:edge_stone': (26, 46), 'poi:west_well': (46.4, 47.8),
              'poi:bottle': (53, 83), 'poi:falls': (31, 104), 'poi:mirror': (63, 53.6), 'poi:lyle_bench': (63.7, 54.3),
              'poi:drawkcab_sign': (55.9, 61.35), 'poi:jail_window': (67.6, 45), 'poi:storage_numbers': (62, 63.5),
              'poi:storage_letters': (66.5, 63.5), 'poi:runaway_chest': (54, 62.6)}
    for k, at in POI_AT.items():
        points.append({'id': k, 'at': list(at)})
    for i, at in enumerate([(62.2, 39.3), (77.0, 61.0), (48.6, 46.4), (84.8, 81.2)]):
        points.append({'id': 'poi:signposts', 'index': i + 1, 'at': list(at)})
    if D2_LIVE:
        points.insert(1, {'id': 'entrance:east_road', 'at': list(EAST_START), 'facing': 'w'})
    if D6_LIVE:
        points.insert(1, {'id': 'entrance:north_road', 'at': [64, 21], 'facing': 's'})  # y 19 lies past the travel line (A6 s15)
    # ---------------------------------------------------------------- encounter areas (135 hostiles, D-23)
    areas = []
    def markers(pop, spots, slot):
        for (cx, cy) in spots:
            r = 1.5
            k = sum(1 for a in areas if a['id'] == pop) + 1
            areas.append({'id': pop, 'index': k, 'kind': 'encounter', 'count': 1, 'slot': slot,
                          'circle': {'at': [cx, cy], 'r': r}})
    # E1 the siege lines (gremlins): the first fight from the pyramid about 5,650 (D-85; was 2,600 at (64.5, 33.5))
    # D-85 (A6 s30): the two lines nearest the gate road moved off Joe's stall (were (64, 34), (66, 32): 4,086, 4,845)
    # F10: (60, 25) and (71, 26) (each the second of a pair) moved to the siege's south line (pop:north_bank)
    markers('pop:siege_north', [(63, 28), (80, 36), (58, 27), (69, 24), (77, 30), (78, 32),
                                (53, 24)], 1)
    # E2 the east road and the besiegers' camp (gremlins; seven placed round the trebuchet)
    markers('pop:east_road_camp', [(93, 56), (95, 57), (97, 68), (99, 70), (91, 73), (92, 75), (100, 54)], 1)
    # E3 the Dark Grove and the west heath (arachnoids)
    markers('pop:grove_arachnoids', [(40, 30), (42, 31), (52, 30), (54, 31), (44, 40), (42, 39), (49, 29)], 2)
    # F10 (2026-11-21): (29, 42) and (26, 34) moved to the rim headland's south slope; the pair nearest Luna (were
    # (29, 51), (33, 52): 5,503 / 5,578 from her, inside D-85's 5,888) moved north-west to (28.5, 49), (35, 50)
    markers('pop:west_heath', [(28, 40), (27, 50), (28.5, 49), (35, 50)], 2)
    # E4 the southern meadows (crawlers)
    markers('pop:centipede_meadows', [(66, 92), (66, 84), (79, 96), (81, 97), (86, 92), (87, 94), (97, 86),
                                      (99, 87), (107, 88), (77, 79)], 3)
    # E5 the Gemstone foothills (crawlers)
    # F10: the pair (106, 32), (107, 34) moved to the south bank (pop:south_bank)
    markers('pop:foothills', [(100, 26), (102, 28), (104, 44)], 3)
    # F10 (2026-11-21, the user: outdoor land "ultra empty, no mobs in radius"; tools/xeen/empty_zones.py): the
    # south-west quarter held no monster within 22,000 (1,417 tiles past 6,000). Six markers moved there, counts and
    # slots kept (kill XP unchanged): arachnoids on the headland's south slope along the rim, crawlers on the south
    # bank west of Falista's hut, gremlins of the siege on the north bank below the south wall; all beyond Luna's
    # 5,888 (D-85), off Kalindra's forecourt (keep clear) and 2,500 from the town's doors. Luna's disc and the
    # forecourt's Town Portal buffer are the exemptions in tools/xeen/empty_zones.yml.
    markers('pop:rim_headland', [(27, 84), (28, 86)], 2)
    markers('pop:south_bank', [(39, 94), (41, 95.5)], 3)
    markers('pop:north_bank', [(56, 75), (58, 77)], 1)
    town_doors = [d for d in doors_out if d[0].startswith('building:cv_')]
    # D-85: no encounter circle's middle or placed pack within missile range (5,120) of an outdoor talking giver
    # (output/studio_cal/a6/s30/d85.py measures the built markers against 5,120 and 5,888)
    givers = {'Joe': (66, 41.9), 'Justine': (57, 41.2), 'Luna': (30.6, 62.6), 'Yog': (89.2, 24)}
    for who, g in givers.items():
        for c in [a['circle']['at'] for a in areas] + list(ELECTRAPEDES):
            if math.hypot(c[0] - g[0], c[1] - g[1]) * 512 < 5120:
                raise SystemExit('D-85: monsters within 5,120 of %s: %s' % (who, c))
    for a in areas:
        c = a['circle']['at']
        near = min(math.hypot(c[0] - d[2][0], c[1] - d[2][1]) for d in town_doors)
        if near * 512 < 2500:
            raise SystemExit('monsters within 2,500 of a Castleview door: %s %s' % (a['id'], c))
    areas += [
        {'id': 'town:castleview', 'kind': 'keep_clear', 'polygon': [[45, 40], [53, 38.5], [74, 38.5], [80, 43],
                                                                     [80.5, 56], [79, 65], [73, 69], [53, 69],
                                                                     [45, 63]]},
        {'id': 'zone:gate_yard', 'kind': 'keep_clear', 'polygon': [[55, 39], [71, 39], [71, 44], [55, 44]]},
        {'id': 'zone:kalindra_gate', 'kind': 'keep_clear', 'polygon': [[34, 62], [52, 62], [52, 79], [34, 79]]},
        {'id': 'zone:luna_grove', 'kind': 'keep_clear', 'polygon': [[26, 57], [36, 57], [36, 67], [26, 67]]},
        {'id': 'zone:sardaj_camp', 'kind': 'keep_clear', 'polygon': [[82, 19], [96, 19], [96, 31], [82, 31]]},
        {'id': 'zone:gemsmiths_row', 'kind': 'keep_clear', 'polygon': [[29, 19], [48, 19], [48, 27.5], [29, 27.5]]},
        {'id': 'zone:east_arrival', 'kind': 'keep_clear', 'polygon': [[102, 55], [112, 55], [112, 65], [102, 65]]},
        {'id': 'wild:sardaj_lands', 'kind': 'open', 'polygon': [[84, 31], [96, 31], [96, 50], [85, 50], [84, 42]]},
        {'id': 'wild:south_bank', 'kind': 'open', 'polygon': [[38, 88], [44, 84], [52, 84], [60, 84], [60, 104],
                                                               [33, 104], [33, 100]]},
        {'id': 'zone:rim_headland', 'kind': 'open', 'polygon': [[24, 66], [34, 66], [34, 82], [24, 82]]},
    ]
    views = [
        {'id': 'view:arrival', 'at': list(PYRAMID_ARRIVAL), 'height': 180, 'look': [69, 46],
         'purpose': "From beside the travel pyramid: the walls and the gatehouse, the gorge with the cut bridge."},
        {'id': 'view:signature', 'at': [52, 90], 'height': 200, 'look': [46, 62],
         'purpose': "From the prayer shrine: Castle Kalindra on its rise, the great tree's rope, the walls."},
    ]
    structures = []
    S = structures.append
    # ---------------------------------------------------------------- the walls and the gates (D-23)
    wall_tex = {'wall': 'cswl128', 'top': 'csbr128'}
    for key, line in wall_stretches():
        w = {'id': 'thing:wall_%s' % key, 'kind': 'wall', 'line': line, 'height': WALL_H, 'thickness': 256,
             'battlements': True, 'textures': dict(wall_tex), 'title': "Castleview's walls"}
        if key == 'ne':
            w['gates'] = [{'at': list(QUEEN_GATE), 'width': 320, 'height': 320, 'arch': 'round', 'sides': 6,
                           'notes': "The Queen's Gate (D-23)."}]
        S(w)
    # the gatehouse: two square towers and a block over the gate passage
    gx, gy = NORTH_GATE
    # Texture fit (lane rule, 2026-11-20): each motif once per face, set in matching stone. The towers are plain
    # castle stone below and carry one row of arrow slits (MM6's grey `csaro128`, the wall's own stone) in their top
    # 256: one slit on the north and south faces, two on the outer side, none into the passage. Kalindra's arms are
    # one whole panel (128 x 256, the picture's own shape) in a coping frame over the arch.
    def slit_tower(tid, x, passage):
        lower = {'id': tid, 'at': [x, 64], 'size': [640, 896], 'wall_height': 576, 'roof': 'none', 'windows': 'none'}
        slits = {'n': ['wall', 'wall', 'window', 'wall', 'wall'], 's': ['wall', 'wall', 'window', 'wall', 'wall'],
                 'e': ['wall'] * 7, 'w': ['wall'] * 7}
        slits['w' if passage == 'e' else 'e'] = ['wall', 'wall', 'window', 'wall', 'window', 'wall', 'wall']
        upper = {'id': tid + '_top', 'at': [x, 64], 'size': [640, 896], 'bottom': 576, 'wall_height': 256,
                 'roof': 'flat', 'battlements': True, 'walls': slits}
        return [lower, upper]
    S({'id': 'thing:gatehouse', 'kind': 'building', 'at': [gx - 1.75, gy - 1.0], 'size': [3.5, 2.0], 'kit': 'grey',
       'door': 'none', 'title': 'The north gatehouse', 'floor': TOWN_H,
       'textures': {'wall': 'cswl128', 'window': 'csaro128', 'roof': 'csbr128', 'trim': 'cstr128', 'post_left': 'cswl128',
                    'post_right': 'cswl128'},
       'parts': slit_tower('tower_w', 0, 'e') + slit_tower('tower_e', 1152, 'w') + [
           {'id': 'arch', 'at': [640, 128], 'size': [512, 768], 'bottom': 384, 'wall_height': 320, 'roof': 'flat',
            'battlements': True, 'windows': 'none'},
           {'id': 'crest_frame', 'at': [816, 136], 'size': [160, 32], 'bottom': 400, 'wall_height': 288,
            'roof': 'flat', 'windows': 'none', 'textures': {'wall': 'cstr128', 'roof': 'cstr128'}},
           {'id': 'crest', 'at': [832, 120], 'size': [128, 32], 'bottom': 416, 'wall_height': 256, 'roof': 'none',
            'windows': 'none', 'walls': CREST_WALLS_N},
       ]})
    def gate_leaves(tag, title, mid, along, normal, width, opening, out_at, out_dir):
        """Two leaves in a gate's passage (D-23): the outer one asks A3's m14 hooks; either hides both leaves (the gate
        stands open; evt:gates_open opens both gates on load once the party has entered). The inner one (D-30): before
        m14.entered it moves the party just outside the gate (`out_at` map units, `out_dir` degrees, 0 east, 90 north)
        and then shows A3's m14.let_out; after it, it opens the gate (m14.gate_open). `along` the wall's direction,
        `normal` pointing out of the town (cells). Texture fit: `xkportc` is one whole portcullis (spikes at its foot)
        256 high, so each leaf is 256 high (its picture once top to bottom, the spikes on the ground) and a fixed stone
        lintel at the passage's middle fills the `opening` above it."""
        half = width / 512.0 / 2
        lw, ld = width / 512.0, 64 / 512.0
        S({'id': 'thing:%s_lintel' % tag, 'kind': 'building', 'at': [round(mid[0] - lw / 2, 3), round(mid[1] - ld / 2, 3)],
           'size': [round(lw, 4), ld], 'turn': round(math.degrees(math.atan2(along[1], along[0])), 2), 'kit': 'grey',
           'door': 'none', 'floor': TOWN_H, 'title': title,
           'textures': {'wall': 'cswl128', 'roof': 'csbr128', 'trim': 'cstr128', 'post_left': 'cswl128',
                        'post_right': 'cswl128'},
           'parts': [{'id': 'lintel', 'at': [0, 0], 'size': [width, 64], 'bottom': 256, 'wall_height': opening - 256,
                      'roof': 'flat', 'windows': 'none'}]})
        for side, off in (('outer', 0.32), ('inner', -0.32)):
            c = (mid[0] + normal[0] * off, mid[1] + normal[1] * off)
            line = [[round(c[0] - along[0] * half, 3), round(c[1] - along[1] * half, 3)],
                    [round(c[0] + along[0] * half, 3), round(c[1] + along[1] * half, 3)]]
            inside = (mid[0] - normal[0] * 1.4, mid[1] - normal[1] * 1.4)
            outside = (mid[0] + normal[0] * 1.4, mid[1] + normal[1] * 1.4)
            leaf = {'id': 'thing:%s_%s' % (tag, side), 'kind': 'wall', 'line': line, 'height': 256, 'thickness': 32,
                    'textures': {'wall': 'xkportc', 'top': 'cstr128'}, 'title': title}
            opened = [{'hide': 'thing:%s_outer' % tag}, {'hide': 'thing:%s_inner' % tag},
                      {'text': 'The gate swings open.'}]
            if side == 'outer':
                # outside: A3's m14 hooks (the pass or court_won the first time, then gate_open); the gate opens
                leaf['condition'] = {'lua': 'XeenQuests.can("%s") or %s' % (use('m14.gate_open'), hcall('m14.gate'))}
            else:
                # inside (D-30): out is free before the first entry (the guard lets the party out), open after it
                leaf['condition'] = {'lua': 'XeenQuests.can("%s")' % use('m14.gate_open')}
                leaf['else_effects'] = [{'teleport': {'to': list(out_at), 'direction': out_dir}}] + hook('m14.let_out')
            leaf['effects'] = opened
            S(leaf)
    # F19: the leaves fill the gatehouse's 512 passage (at 384 they left a 64 slit at each tower)
    gate_leaves('north_gate', 'The north gate', NORTH_GATE, (1, 0), (0, -1), 512, 384, NORTH_OUT, 270)
    ax, ay = QUEEN_B[0] - QUEEN_A[0], QUEEN_B[1] - QUEEN_A[1]
    L = math.hypot(ax, ay)
    along = (ax / L, ay / L)
    normal = (-along[1], along[0])          # out of the town: south-west
    gate_leaves('queens_gate', "The Queen's Gate", QUEEN_GATE, along, normal, 320, 320, QUEEN_OUT, 45)
    # the jetty bastion: the west wall made thick between JETTY_Y, the deck over it, Lucio's booth on the deck
    S({'id': 'thing:jetty_bastion', 'kind': 'wall', 'line': [[50, JETTY_Y[0]], [50, JETTY_Y[1]]], 'height': WALL_H,
       'thickness': 768, 'textures': dict(wall_tex), 'title': "Castleview's walls"})
    S({'id': 'thing:jetty_deck', 'kind': 'deck', 'outline': [[48.4, 52.6], [51.7, 52.6], [51.7, 55.8], [48.4, 55.8]],
       'level': TOWN_H + WALL_H + 16, 'kerb': 64, 'posts': 32, 'textures': {'deck': '7trimda'},
       'title': "Lucio's Jetty"})
    S({'id': 'thing:jetty_pier', 'kind': 'bridge', 'line': [[48.5, 54.9], [45.9, 54.9]], 'width': 320,
       'height': TOWN_H + WALL_H + 16, 'piers': 2, 'kerb': 48, 'textures': {'deck': '7trimda'},
       'title': "Lucio's Jetty", 'notes': "D-5.3: the jetty that ends in thin air, the celestial boats' mooring."})
    S({'id': 'thing:jetty_stair', 'kind': 'stairs', 'line': [[51.15, 58.9], [51.15, 55.8]], 'width': 256,
       'rise': WALL_H + 16, 'textures': {'wall': 'cswl128'}, 'title': 'The wall stair'})
    S({'id': 'thing:jetty_sign', 'kind': 'sign', 'at': [51.45, 58.95], 'height': 224, 'width': 160,
       'title': "Lucio's Jetty", 'arms': [{'title': "Lucio's Jetty", 'toward': 'n'}]})
    # Ellinger's Tower (DD-02): a round tower of dark stone, conical slate roof, the tallest thing in town
    # Ellinger's Tower (D-27): five storeys of 384 (1,920 to the eaves), a string course between each two, a slate cone:
    # the tallest thing in Castleview
    ELLINGER_PARTS = []
    for k in range(5):
        p = {'id': 'base' if k == 0 else 'storey_%d' % (k + 1), 'shape': 'round', 'at': [512, 512], 'radius': 416,
             'sides': 12, 'wall_height': 384, 'roof': 'cone' if k == 4 else 'none', 'windows': 'alternate'}
        if k:
            p['bottom'] = 384 * k
        if k == 4:
            p['roof_pitch'] = 70
        ELLINGER_PARTS.append(p)
        if k < 4:
            ELLINGER_PARTS.append({'id': 'course_%d' % (k + 1), 'shape': 'round', 'at': [512, 512], 'radius': 448,
                                   'sides': 12, 'bottom': 384 * (k + 1) - 16, 'wall_height': 32, 'roof': 'flat',
                                   'windows': 'none', 'textures': {'wall': 'hkm3b', 'roof': 'csbr128'}})
    dd02 = {'id': 'thing:ellinger_tower', 'kind': 'building', 'at': [ELLINGER_C[0] - 1.0, ELLINGER_C[1] - 1.0],
            'size': [2.0, 2.0], 'kit': 'grey', 'facing': 'w', 'floor': TOWN_H, 'title': "Ellinger's Tower",
            'textures': {'wall': 'hkm1b1', 'window': 'hkm1bw', 'door': 'hkm1d', 'roof': 'xtslatew'},
            'parts': ELLINGER_PARTS,
            'door': {'part': 'base', 'wall': DD02_WALL},
            'condition': {'lua': hcall('m17.tower_door')}}
    if DUNGEON['dd02']:
        dd02['into'] = {'map': 'xeen_dd02.blv', 'arrival': 'entrance:front_door'}    # DD-02's entrance (A8, D-37)
    else:
        dd02['effects'] = [sealed("Ellinger's Tower (DD-02)")]
    S(dd02)
    # the square: the mirror and Lyle's bench beside it (one spot, D-23); the sewer hatch (DD-01)
    S({'id': 'thing:square_paving', 'kind': 'platform', 'at': [63.0, 54.0], 'size': [4096, 3072], 'height': 8,
       'textures': {'top': 't09a02a', 'wall': 't09a02a'}, 'title': 'Castleview square'})
    S({'id': 'thing:cv_mirror', 'kind': 'portal', 'at': [63.0, 53.6], 'radius': 112, 'sides': 12, 'turn': 0,
       'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'The Mirror of Castleview',
       'effects': [{'lua': 'Xeen.useMirror(%d, eventId, continueStep)' % HOUSE_MIRROR}],
       'notes': "A4's 4467; asleep until Kalindra's stage 4 (A3's mirror helper)."})
    S({'id': 'thing:lyle_bench', 'kind': 'building', 'at': [63.4, 54.15], 'size': [0.75, 0.3], 'kit': 'grey',
       'door': 'none', 'title': "Lyle's bench", 'floor': TOWN_H + 8,
       'parts': [{'id': 'bench', 'at': [32, 24], 'size': [320, 96], 'wall_height': 64, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 't06a10', 'roof': '7trimda'},
                  'title': "Lyle's bench",
                  'effects': [{'text': 'A brass plate: "This bench reserved for Lyle the Pigeon Feeder."'}]}]})
    hatch = {'id': 'thing:dd01_hatch', 'kind': 'hatch', 'at': list(DD01_AT), 'form': 'wedge', 'height': 96,
             'turn': 90, 'title': 'An iron hatch', 'hint': 'Castleview Sewer'}
    if DUNGEON['dd01']:
        hatch['into'] = {'map': 'xeen_dd01.blv', 'arrival': 'entrance:d1_hatch'}   # the ladder's foot (A8, D-37)
    else:
        hatch['effects'] = [msg('An iron hatch in the paving, a ladder going down into the dark and the smell of the '
                                'sewer. The Castleview Sewer (DD-01) is not open to you yet.')]
    S(hatch)
    # the Drawkcab sign, the jail's back window, Public Storage's chest yards, the runaway chest
    S(sign('thing:drawkcab_sign', (55.9, 61.35), 'Sign', effects=hook('q-d3.drawkcab_sign')))
    S({'id': 'thing:jail_window', 'kind': 'building', 'at': [67.4, 44.95], 'size': [0.5, 0.25], 'kit': 'grey',
       'door': 'none', 'title': 'A barred window', 'floor': TOWN_H,
       'parts': [{'id': 'bars', 'at': [64, 40], 'size': [128, 32], 'bottom': 96, 'wall_height': 128, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 't09a04a', 'roof': 't09b11b'},
                  'title': 'A barred window', 'effects': hook('q-d2.jail_window')}]})
    def lidded(sid, at, title, lua):
        """A storage chest whose lid the map toggles (q-d4): a small box with the click on it, no chest window."""
        return {'id': sid, 'kind': 'building', 'at': [round(at[0] - 0.1, 3), round(at[1] - 0.1, 3)],
                'size': [0.2, 0.2], 'kit': 'grey', 'door': 'none', 'floor': TOWN_H,
                'parts': [{'id': 'lid', 'at': [8, 18], 'size': [96, 64], 'wall_height': 80, 'roof': 'flat',
                           'windows': 'none', 'textures': {'wall': 't06a10', 'roof': '7trimda'}, 'title': title,
                           'effects': [{'lua': lua}]}]}
    num_order = [3, 7, 1, 9, 5, 2, 8, 4, 6]            # the numbers along the row, west to east
    for i, n in enumerate(num_order):
        lua = ('if Xeen.isSet("q-d4.numbers_closed") then %s return end '
               'local k = evt.GetMapVar("d1_numbers", 1) '
               'if k == %d then k = k + 1 evt.SetMapVar("d1_numbers", k) '
               'evt.StatusText("Chest %d: the lid drops shut.") '
               'if k == 10 then %s end '
               'elseif k > %d then evt.StatusText("Chest %d is shut.") '
               'else evt.SetMapVar("d1_numbers", 1) '
               'evt.StatusText("Chest %d will not shut. All nine lids spring open again.") end'
               % (hcall('q-d4.number_chests'), n, n, hcall('q-d4.number_chests'), n, n, n))
        S(lidded('thing:number_chest_%d' % (i + 1), (60.75 + 0.33 * i, 63.55), 'A chest with a %d on its lid' % n, lua))
    letters = 'PITCHFORK'
    let_order = [5, 2, 8, 0, 6, 3, 7, 1, 4]          # indexes into PITCHFORK, west to east
    for i, n in enumerate(let_order):
        ch = letters[n]
        lua = ('if Xeen.isSet("q-d4.letters_closed") then %s return end '
               'local k = evt.GetMapVar("d1_letters", 0) '
               'if k == %d then k = k + 1 evt.SetMapVar("d1_letters", k) '
               'evt.StatusText("A letter on the lid reads: %s. The lid drops shut.") '
               'if k == 9 then %s end '
               'elseif k > %d then evt.StatusText("The %s chest is shut.") '
               'else evt.SetMapVar("d1_letters", 0) '
               'evt.StatusText("A letter on the lid reads: %s. It will not shut. All nine lids spring open again.") end'
               % (hcall('q-d4.letter_chests'), n, ch, hcall('q-d4.letter_chests'), n, ch, ch))
        S(lidded('thing:letter_chest_%d' % (i + 1), (65.25 + 0.33 * i, 63.55), 'A chest with a letter on its lid', lua))
    S({'id': 'thing:runaway_chest', 'kind': 'chest', 'at': [54.0, 62.6], 'title': 'A chest on little brass feet',
       'chest': {'level': 3, 'random_items': 3}, 'condition': {'lua': hcall('m17.runaway_chest')}})
    # dressing in town (DRESSING.md: pairs against walls, none before a door)
    props = [('bigbarel', (59.3, 45.9)), ('bigbarel', (59.3, 46.25)),        # the tavern's back (west) wall
             ('7dec32', (66.75, 46.0)), ('7dec32', (66.75, 46.35)),            # the smithy's back wall (MM7's barrel; 7dec24 is a campfire)
             ('bigbarel', (74.7, 52.4)), ('bigbarel', (74.7, 52.75)),        # the stables' back wall
             ('haybale2', (74.7, 49.0)), ('haybale2', (74.7, 49.35))]        # the barracks' back wall
    for i, (d, at) in enumerate(props):
        S(deco('thing:prop_%d' % (i + 1), d, at))
    # ---------------------------------------------------------------- outside the north gate
    S({'id': 'thing:pyramid', 'kind': 'building', 'at': [PYRAMID_C[0] - 1.5, PYRAMID_C[1] - 1.5], 'size': [3, 3],
       'kit': 'stone', 'title': 'Travel Pyramid', 'door': 'none', 'floor': 1250,
       'textures': {'wall': 'csbr128', 'roof': 'csbr128'},
       'parts': [{'id': 'p', 'at': [128, 128], 'size': [1280, 1280], 'wall_height': 64, 'roof': 'hip',
                  'roof_pitch': 52, 'windows': 'none', 'title': 'Travel Pyramid',
                  'effects': [{'lua': 'Xeen.travelPyramid("castleview")'}]}],
       'notes': ("hook: m7.pyramid_d1 (A3): Xeen.travelPyramid('castleview') reads the Pyramid Sigil (m7.sigil) and "
                 "sets the party down at castleview_pyramid.")})
    use('m7.pyramid_d1')
    S(sign('thing:gate_notice', (62.3, 43.25), "The Mayor's notice", effects=hook('q-d1.gate_notice')))
    S(K.stall('thing:joe_stall', (65.6, 40.7), 0))
    S(sign('thing:joe_sign', (66.75, 40.55), "Joe's sign", effects=hook('q-c24.joes_sign'), height=256, width=192))
    S({'id': 'thing:justine_tent', 'kind': 'tent', 'at': [56.0, 40.0], 'size': [640, 512], 'height': 288,
       'open': True, 'title': "Justine's lean-to"})
    S(deco('thing:justine_fire', 'cmpfyr00', (57.6, 41.9), title='Campfire'))
    burrow = {'id': 'thing:dd04_burrow', 'kind': 'doorway', 'at': list(DD04_AT), 'turn': 180, 'floor': TOWN_H,
              'height': 192, 'width': 128, 'depth': 96, 'textures': {'door': 'hhp1d', 'wall': 't06a02'},   # F2: t06a03 is one wing
              'title': 'A burrow under the wall', 'effects': hook('q-d1.court_entrance')}
    if DUNGEON['dd04']:
        # s32 (F16): the entrance window shows the burrow's line (trans row 5031, the hook's text); the hook's own
        # message after the move replaced the window, so the party never went in
        burrow['effects'] = []
        burrow['into'] = {'map': 'xeen_dd04.blv'}
    else:
        burrow['effects'] = burrow['effects'] + [{'text': 'The Gremlin Court (DD-04) is not open to you yet.'}]
    S(burrow)
    # ---------------------------------------------------------------- the siege lines, the gorge, the acid pond
    for side, x in (('w', 78.4), ('e', 83.3)):
        post = {'id': 'thing:rope_bridge_cut_%s' % side, 'kind': 'building', 'at': [x, 42.6], 'size': [0.4, 0.8],
                'kit': 'poor', 'door': 'none', 'floor': 1100,
                'parts': [{'id': 'post_n', 'at': [64, 64], 'size': [48, 48], 'wall_height': 416, 'roof': 'flat',
                           'windows': 'none', 'textures': {'wall': 't06a10', 'roof': 't06a10'}},
                          {'id': 'post_s', 'at': [64, 296], 'size': [48, 48], 'wall_height': 416, 'roof': 'flat',
                           'windows': 'none', 'textures': {'wall': 't06a10', 'roof': 't06a10'}}]}
        post['parts'][0]['title'] = 'The rope bridge'
        post['parts'][0]['effects'] = [msg('The rope bridge hangs in two halves into the gorge, its ropes sawn clean '
                                           'through. Small teeth, by the look of it.')]
        S(post)
    S({'id': 'thing:rope_bridge', 'kind': 'bridge', 'line': [[78.6, 43.0], [83.4, 43.0]], 'width': 256,
       'rise': -96, 'piers': 0, 'railing': 'rope', 'towers': [96, 96, 352], 'kerb_invisible': 352,
       'textures': {'deck': '7trimda'}, 'title': 'The rope bridge', 'hidden': True,
       'notes': "Mended once q-d1.court_won (A3's q-d1.sabotage): shown by evt:sabotage."})
    S({'id': 'thing:mill_burnt', 'kind': 'building', 'at': [77.8, 45.2], 'size': [1.4, 1.6], 'kit': 'grey',
       'door': 'none', 'title': "Miller Dunn's mill", 'floor': 1100,
       'ruin': {'height': [96, 384], 'gaps': 0.4, 'thickness': 48, 'seed': 7},
       'parts': [{'id': 'm', 'at': [64, 64], 'size': [589, 692], 'wall_height': 384, 'roof': 'none',
                  'windows': 'none', 'textures': {'wall': 't06a01'}}]})
    S({'id': 'thing:mill', 'kind': 'building', 'at': [77.8, 45.2], 'size': [1.4, 1.6], 'kit': 'grey',
       'door': 'none', 'title': "Miller Dunn's mill", 'floor': 1100, 'hidden': True,
       'parts': [{'id': 'm', 'at': [64, 64], 'size': [589, 692], 'wall_height': 448, 'roof': 'gable',
                  'roof_pitch': 45, 'windows': 'alternate',
                  'textures': {'wall': 't06a01', 'window': 't06a04', 'roof': 'xlslatemos'}}]})
    S({'id': 'thing:mill_chest', 'kind': 'chest', 'at': [78.6, 47.3], 'title': "The miller's strongbox",
       'chest': {'level': 2, 'random_items': 2}})
    S(deco('thing:mill_beam', '7dec18', (78.0, 47.4)))
    outfall = {'id': 'thing:dd01_outfall', 'kind': 'culvert', 'at': list(OUTFALL_AT), 'turn': -90,
               'title': 'An iron grate', 'hint': "The sewer's outfall", 'condition': {'lua': hcall('m16.outfall')},
               'notes': ("DD-01's outfall (D-26): a two-way exit once A8's bar is lifted from inside (A3's m16.outfall, "
                         "its fail text 'An iron grate, barred from inside.').")}
    if DUNGEON['dd01']:
        outfall['into'] = {'map': 'xeen_dd01.blv', 'arrival': 'entrance:d1_outfall'}  # inside the grate (A8, D-37)
    else:
        outfall['effects'] = [msg('The grate swings open on a dark culvert. The Castleview Sewer (DD-01) is not open '
                                  'to you yet.')]
    S(outfall)
    # four plain street grates over the sewer (D-26): no event, not POIs
    for i, at in enumerate([(57.5, 58.0), (63.0, 45.5), (69.5, 58.0), (60.5, 56.5)]):
        S({'id': 'thing:street_grate_%d' % (i + 1), 'kind': 'platform', 'at': list(at), 'size': [192, 128],
           'height': 8, 'textures': {'top': 'xkportc', 'wall': 't09a02a'},
           'notes': ['the guild row', 'the gate passage', 'by the temple', 'the market (the square)'][i]})
    S({'id': 'thing:acid_pond', 'kind': 'sign', 'at': [69.6, 35.0], 'height': 160, 'width': 128, 'title': 'The acid pond',
       'effects': [{'damage': {'amount': 20, 'kind': 'body'}},
                   msg('The acid pond is not water. It bites through boot leather.')]})
    S(deco('thing:acid_skeleton', 'dec05', (70.8, 34.7)))
    # ---------------------------------------------------------------- east of the river
    S({'id': 'thing:east_bridge', 'kind': 'bridge', 'line': [[78.8, 60], [83.3, 60]], 'width': 448, 'rise': 96,
       'kerb': 96, 'textures': {'deck': 'csbr128', 'side': 'cswl128', 'pier': 'cswl128'}, 'title': 'The East Bridge'})
    for i, (x, y) in enumerate([(86.5, 23.0), (90.0, 22.8)]):
        S({'id': 'thing:sardaj_tent_%d' % (i + 1), 'kind': 'tent', 'at': [x, y], 'size': [896, 704], 'height': 384,
           'open': True, 'title': 'A Sardaj tent',
           # A6 s27 (D-72 rule 3): the source's question on Yes/No buttons, no message before it
           'effects': [{'lua': 'if continueStep == 1 then if %s then evt.SetMonGroupBit(%d, MonsterBits.Hostile, '
                               'true) end return end' % (hcall('q-d12.camp'), SARDAJ_GROUP)},
                       {'lua': 'if continueStep ~= nil then return end'},
                       {'lua': 'AskChoiceWithAnswerSteps(eventId, 3, "You have found a Barbarian camp. Destroy?", '
                               '{{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})'}]}
          | ({'same_event_as': 'thing:sardaj_tent_1'}
                                                                    if i else {}))
    structures[-1].pop('effects', None)
    structures[-1].pop('title', None)
    S(deco('thing:sardaj_fire', 'cmpfyr00', (88.6, 25.6), title='Campfire'))
    S(deco('thing:sardaj_totem', '7dec18', (87.0, 26.6)))
    S({'id': 'thing:trebuchet', 'kind': 'building', 'at': [95.0, 62.0], 'size': [1.5, 1.0], 'kit': 'poor',
       'door': 'none', 'title': 'A wrecked trebuchet', 'ruin': {'height': [96, 448], 'gaps': 0.5, 'thickness': 48,
                                                                'seed': 3},
       'parts': [{'id': 'frame', 'at': [64, 64], 'size': [640, 384], 'wall_height': 448,
                  'roof': 'none', 'windows': 'none', 'textures': {'wall': 't06a10'}}]})
    S(sign('thing:trebuchet_sign', (96.4, 62.4), 'Sign', 'Property of Castleview. Do not touch.'))
    S({'id': 'thing:camp_chest', 'kind': 'chest', 'at': [96.9, 62.9], 'title': "The gremlins' loot",
       'chest': {'level': 2, 'random_items': 3}})
    S({'id': 'thing:wayside_shrine', 'kind': 'building', 'at': [102.4, 57.3], 'size': [1.2, 1.2], 'kit': 'stone',
       'title': 'A wayside shrine of Mok', 'door': 'none',
       'parts': [{'id': 's', 'at': [154, 154], 'size': [307, 307], 'wall_height': 288, 'posts': 32, 'roof': 'hip',
                  'roof_pitch': 50, 'windows': 'none', 'textures': {'roof': 'xlslate', 'wall': 't09a01'},
                  'title': 'A wayside shrine of Mok',
                  **daily('d1_wayside_shrine', [{'add': {'var': 'LuckBonus', 'value': 10}},
                                                {'text': 'Mok bless your road. +10 Luck until you rest.'}],
                          'The shrine is quiet. Come back tomorrow.')}]})
    if not D2_LIVE:
        S(sign('thing:east_road_end', (108.5, 59.0), 'Sign',
               'The road east into the Sprite Forest is closed by fallen trees. Turn back.'))
    S(sign('thing:north_road_end', (64.9, 20.5), 'Sign',
           'North: Griffin Pass and the Forbidden Zone.' if D6_LIVE else
           'The mountain road north to the Forbidden Zone is closed by a rockfall. Turn back.'))
    # ---------------------------------------------------------------- the Dark Grove and the great tree
    # D-72 rule 3: one Yes/No button prompt whose own text is the look and the question, no SetMessage before it
    # F16 (s32): no Yes/No before a move into a .blv; the hook's line (fail or go) on the status line, then the
    # standard entrance window (picture 1, no trans row: D7 is the Skyroads, not a dungeon) asks
    rope_q = ('if %s then evt.StatusText("%s") end'
              % (hcall('m30.grove_rope'), 'The Skyroads (D7) are not open to you yet.'))
    if d7_rope_move():      # D-58 Q10: up to D7's rope head; back down lands at entrance:d7_rope
        rope_q = rope_q.replace('evt.StatusText("The Skyroads (D7) are not open to you yet.")', d7_rope_move())
    # the great tree: a 16-sided buttressed foot and a tapered trunk in xdbark (D2's route, xdbark registered for D1)
    gx, gy = GREAT_C
    gfp = 4.5                                  # the plot (cells): the trunk and its buttresses (760 + 320 < 1152)
    gmid = int(gfp * 256)
    S({'id': 'thing:great_tree', 'kind': 'building', 'at': [round(gx - gfp / 2, 3), round(gy - gfp / 2, 3)],
       'size': [gfp, gfp], 'kit': 'timber', 'door': 'none', 'floor': GREAT_FLOOR, 'title': 'The great tree',
       'parts': [{'id': 'foot', 'shape': 'round', 'at': [gmid, gmid], 'radius': GREAT_R, 'sides': 16,
                  'wall_height': GREAT_FOOT, 'roof': 'flat', 'windows': 'none',
                  'buttresses': {'count': 1, 'width': 176, 'depth': 320, 'height': GREAT_FOOT - 32,
                                 'walls': [k for k in range(16) if k != ROPE_WALL]},
                  'textures': {'wall': 'xdbark', 'roof': 'xdbark', 'trim': 'xdbark'}},
                 {'id': 'trunk', 'shape': 'round', 'at': [gmid, gmid], 'radius': GREAT_R, 'sides': 16,
                  'bottom': GREAT_FOOT, 'wall_height': GREAT_H, 'taper': GREAT_TAPER, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 'xdbark', 'roof': 'xdbark'}}],
       'notes': "The Dark Grove's great tree (MAPS): the tallest thing round it, the rope hanging from its crown."})
    S(deco('thing:great_crown', GREAT_CROWN, (gx, gy), turn=GREAT_CROWN_TURN, **{'raise': GREAT_CROWN_RAISE}))
    # the rope: from the crown's leaves down to a foot one can reach, beside the trunk toward D7's return point
    S({'id': 'thing:grove_rope', 'kind': 'building', 'at': [round(ROPE_AT[0] - 0.15, 3), round(ROPE_AT[1] - 0.15, 3)],
       'size': [0.3, 0.3], 'kit': 'grey', 'door': 'none', 'title': 'A rope from the sky', 'floor': GREAT_FLOOR,
       'parts': [{'id': 'rope', 'at': [57, 57], 'size': [40, 40], 'wall_height': ROPE_H, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 't06a10', 'roof': 't06a10'}, 'title': 'A rope from the sky',
                  'effects': [{'lua': rope_q}]}]})
    S({'id': 'thing:webbed_pack', 'kind': 'chest', 'at': [43.2, 38.3], 'title': 'A pack wrapped in web',
       'chest': {'level': 2, 'random_items': 2}})
    # ---------------------------------------------------------------- the Western Tower (DD-05), the heath
    # D-41 (texture fit): seamless ashlar, the skull frieze hkm3b once, in the top storey under the eaves, with the
    # hkm3elw windows only there; the door in the base. D-42: the shaft in Castleview's castle stone cswl128 so that
    # MM6's arrow slit csaro128 (the wall's own stone, as on the north gatehouse) sits in it: one slit per storey up the
    # north face (wall 6: a round part's wall 0 looks south, anticlockwise) where the heretics' rope climbs, and a
    # window (hkm3elw) in the top storey right above the rope's top
    ASHLAR = {'wall': 'cswl128', 'window': 'cswl128', 'post_left': 'cswl128', 'post_right': 'cswl128',
              'trim': 'cswl128', 'slit': 'csaro128'}
    def wt_bays(r, role):
        side = 2 * r * math.sin(math.pi / 12)
        return [['wall', round((side - 128) / 2, 3)], [role, 128], ['wall', round((side - 128) / 2, 3)]]
    WT_NORTH = '6'
    wt = {'id': 'thing:western_tower', 'kind': 'building', 'at': [WT_C[0] - WT_R - 0.1, WT_C[1] - WT_R - 0.1],
          'size': [2 * WT_R + 0.2, 2 * WT_R + 0.2], 'kit': 'grey', 'facing': 's', 'floor': TOWER_H,
          'title': 'The Western Tower', 'textures': {'wall': 'hkm3b', 'window': 'hkm3elw', 'door': 'hkm3dr',
                                                     'roof': 'xtslate'},
          'parts': [{'id': 'base', 'shape': 'round', 'at': [768, 768], 'radius': 640, 'sides': 12,
                     'wall_height': 1280, 'roof': 'none', 'windows': 'none', 'textures': dict(ASHLAR),
                     'upper_walls': {WT_NORTH: wt_bays(640, 'slit')}},
                    {'id': 'mid', 'shape': 'round', 'at': [768, 768], 'radius': 576, 'sides': 12, 'bottom': 1280,
                     'wall_height': 1024, 'roof': 'none', 'windows': 'none',
                     'textures': dict(ASHLAR, roof='cswl128'),
                     'walls': {WT_NORTH: wt_bays(576, 'slit')}, 'upper_walls': {WT_NORTH: wt_bays(576, 'slit')}},
                    {'id': 'top', 'shape': 'round', 'at': [768, 768], 'radius': 640, 'sides': 12, 'bottom': 2304,
                     'wall_height': 256, 'roof': 'cone', 'roof_pitch': 68, 'windows': 'none',
                     'walls': {str(k): (wt_bays(640, 'window') if k % 2 == 0 else ['wall', 'wall']) for k in range(12)},
                     'textures': {'post_left': 'hkm3b', 'post_right': 'hkm3b', 'trim': 'cswl128'}}],
          'door': {'part': 'base', 'wall': WT_WALL},
          'condition': {'lua': 'Xeen.isSet("q-d6.tower_opened") or %s' % hcall('q-d6.front_door_outside')}}
    if DUNGEON['dd05']:
        # the first opening only opens (A3's text "... a small, sulky pop." would be lost under the move); the next
        # click goes in
        wt['condition'] = {'lua': 'Xeen.isSet("q-d6.tower_opened")'}
        wt['else_effects'] = [{'lua': hcall('q-d6.front_door_outside')}]
        wt['into'] = {'map': 'xeen_dd05.blv', 'arrival': 'entrance:d1_door'}
    else:
        wt['effects'] = [{'text': 'The Western Tower (DD-05) is not open to you yet.'}]
    S(wt)
    # yes: A3's hook (its text, the rope_climbed bit), then up to DD-05's top floor (entrance:d1_rope) once DD-05 is
    # installed; before that a sealed line
    rope_yes = (dd05_rope_move() if DUNGEON['dd05']
                else 'evt.StatusText("The top of the Western Tower (DD-05) is not open to you yet.")')
    # F16 (s32): the hook's status line, then the entrance window with trans row 5033 (the rope's look)
    tower_q = 'if %s then %s end' % (hcall('q-d6.tower_rope'), rope_yes)
    # D-42: the rope hangs 24 off the north face (the top storey's flat face 618 out), its top in the window, 40 to
    # the west of the slits' column so that it climbs past them, under the window's glass (TOWER_ROPE_SIDE)
    TOWER_ROPE_SIDE = -40
    S({'id': 'thing:tower_rope', 'kind': 'building', 'at': [round(WT_C[0] - 0.15 + TOWER_ROPE_SIDE / 512, 4),
                                                           WT_C[1] - 1.441],
       'size': [0.3, 0.3], 'kit': 'grey', 'door': 'none', 'title': 'A rope down the north wall', 'floor': TOWER_H,
       'parts': [{'id': 'rope', 'at': [64, 64], 'size': [32, 32], 'wall_height': 2432, 'roof': 'flat',
                  'windows': 'none', 'textures': {'wall': 't06a10', 'roof': 't06a10'},
                  'title': 'A rope down the north wall', 'effects': [{'lua': tower_q}]}]})
    S({'id': 'thing:heretic_pack', 'kind': 'chest', 'at': [WT_C[0] + 0.55, WT_C[1] - WT_R - 0.75],
       'title': "A heretic's pack", 'chest': {'level': 3, 'random_items': 2},
       'notes': "Where he fell from the rope: one spot with the rope (D-23)."})
    S({'id': 'thing:edge_stone', 'kind': 'obelisk', 'at': [26.2, 46.3], 'height': 320, 'width': 96,
       'textures': {'wall': 'cswl128'}, 'title': 'The Edge Stone',
       'effects': [{'text': 'Cut into the stone, one word: DON\'T.'}]})
    w = K.well('thing:west_well', (46.4, 47.8), title='The old west well')
    w.update(daily('d1_west_well', [{'add': {'var': 'PersonalityBonus', 'value': 10}},
                                    {'text': '+10 Personality until you rest.'}],
                   'The water is cool and refreshing.'))
    S(w)
    # the gemsmiths' row and the adit (DD-10, west pocket)
    adit = {'id': 'thing:dd10a_adit', 'kind': 'doorway', 'at': [ADIT_AT[0], ADIT_AT[1] - 0.2], 'floor': SHELF_H,
            'height': 320, 'width': 256, 'depth': 384, 'hood': 64, 'textures': {'door': '7solid01', 'wall': 't06a02'},
            'title': 'A timbered adit', 'hint': 'Gemstone Mines'}
    if DUNGEON['dd10a']:
        adit['into'] = {'map': 'xeen_dd10a.blv', 'at': [0, 192, 0], 'facing': 512}   # DD-10A's start (A8)
    else:
        adit['effects'] = [msg('Cart rails run into the hill. The Gemstone Mines (DD-10) are not open to you yet.')]
    S(adit)
    # ---------------------------------------------------------------- Castle Kalindra (out of phase), Luna, the obelisk
    # D-30 (A8's table in briefs/dd03/NOTES.md): the castle in parts by stage, each part twice, the out-of-phase one in
    # xkshimmer shown at load and the restored one in the royal kit's white stone hidden at load; evt:kalindra_<n>
    # swap them on Xeen.stageOf("kalindra") >= n (X3's Newcastle). Stage 1 the gatehouse and gate, the curtain walls,
    # the keep's ground storey; 2 the keep's second storey and the observatory turret; 3 the two south towers over the
    # dungeon and the cell block (the dungeon stair is off the south wing); 4 the keep's third storey, the bell tower,
    # the north towers and their cones, the banner, the stable yard's gate (north curtain).
    # Texture fit (lane rule, 2026-11-20): windows once per face, a few per wall (the restored hc set's lancet `hcwindo`
    # on its own white stone; the out-of-phase version shows no window motif on the shimmer), the towers' windows in a
    # row at their tops, the observatory's lantern and the belfry each one window per face; arms and banner one
    # whole panel each.
    ghost_tex = {'wall': GHOST_TEX, 'window': GHOST_TEX, 'roof': 'xtslate', 'trim': 'cstr128', 'post_left': GHOST_TEX,
                 'post_right': GHOST_TEX, 'door': 'xkportc'}
    royal_tex = {'wall': 'hcwall', 'window': 'hcwindo', 'roof': 'xtslate', 'trim': 'cstr128', 'post_left': 'hcw1le',
                 'post_right': 'hcw1re', 'door': 'xkportc'}
    def spaced(n, at):
        return ['window' if i in at else 'wall' for i in range(n)]
    def storey(k):
        p = {'id': 'keep_%d' % k, 'at': [1024, 1536], 'size': [2048, 2560], 'bottom': 384 * (k - 1),
             'wall_height': 384, 'roof': 'flat' if k == 3 else 'none', 'battlements': k == 3}
        if k == 1:                      # behind the curtain walls
            p['windows'] = 'none'
        else:
            p['walls'] = {'n': spaced(16, (2, 8, 13)), 's': spaced(16, (2, 8, 13)), 'e': spaced(20, (3, 9, 15)),
                          'w': spaced(20, (3, 9, 15))}
            p['upper_walls'] = {'n': ['wall'] * 16, 's': ['wall'] * 16, 'e': ['wall'] * 20, 'w': ['wall'] * 20}
        return p
    def round_top(pid, at, r, sides, bottom, h, windowed, bays_win, bays_plain, **kw):
        walls = {str(k): (bays_win if k in windowed else bays_plain) for k in range(sides)}
        p = {'id': pid, 'shape': 'round', 'at': at, 'radius': r, 'sides': sides, 'bottom': bottom, 'wall_height': h,
             'walls': walls}
        if h > 256:
            p['upper_walls'] = {str(k): bays_plain for k in range(sides)}
        p.update(kw)
        return p
    side = 2 * 352 * math.sin(math.pi / 10)          # a tower side, 217.5
    LANTERN_R = round(128 / (2 * math.sin(math.pi / 10)), 2)   # sides of 128: one whole window each
    # a bay shows as many texels as it is wide: a window bay is the picture's own 128
    TOWER_WIN = [['wall', round((side - 128) / 2, 3)], ['window', 128], ['wall', round((side - 128) / 2, 3)]]
    def tower(tid, at):
        return [{'id': tid, 'shape': 'round', 'at': at, 'radius': 352, 'sides': 10, 'wall_height': 640,
                 'roof': 'none', 'windows': 'none'},
                round_top(tid + '_top', at, 352, 10, 640, 384, (1, 3, 6, 8), TOWER_WIN,
                          ['wall', 'wall'], roof='cone', roof_pitch=66)]
    def curtain(cid, at, size):
        return {'id': cid, 'at': at, 'size': size, 'wall_height': 640, 'roof': 'flat', 'battlements': True,
                'windows': 'none'}
    KAL_STAGE_PARTS = {
        1: [curtain('curtain_n', [512, 256], [3072, 256]), curtain('curtain_s', [512, 5632], [3072, 256]),
            curtain('curtain_w', [256, 512], [256, 5120]), curtain('curtain_e', [3584, 512], [256, 5120]),
            storey(1)],
        2: [storey(2),
            {'id': 'observatory', 'shape': 'round', 'at': [2784, 1824], 'radius': 224, 'sides': 10, 'bottom': 416,
             'wall_height': 736, 'roof': 'none', 'windows': 'none'},
            round_top('observatory_lantern', [2784, 1824], LANTERN_R, 10, 1152, 256, (0, 2, 4, 6, 8), ['window'],
                      ['wall'],
                      roof='cone', roof_pitch=66)],
        3: tower('tower_sw', [384, 5760]) + tower('tower_se', [3712, 5760]),
        4: [storey(3),
            {'id': 'bell_tower', 'at': [1792, 2560], 'size': [512, 512], 'bottom': 1152, 'wall_height': 512,
             'roof': 'none', 'windows': 'none'},
            {'id': 'belfry', 'at': [1792, 2560], 'size': [512, 512], 'bottom': 1664, 'wall_height': 256,
             'roof': 'hip', 'roof_pitch': 55,
             'walls': {w: ['wall', ['window', 128], 'wall'] for w in ('n', 'e', 's', 'w')}}]
           + tower('tower_nw', [384, 384]) + tower('tower_ne', [3712, 384]) +
           [{'id': 'stable_gate', 'at': [2112, 160], 'size': [640, 448], 'wall_height': 768, 'roof': 'flat',
             'battlements': True, 'windows': 'none'}],
    }
    # restored only at stage 4: the banner (one whole panel on the keep's third storey, north face); the stable yard's
    # gate (below) a double door
    KAL_RESTORED_ONLY = {4: [
        {'id': 'banner', 'at': [1664, 1504], 'size': [128, 32], 'bottom': 832, 'wall_height': 256, 'roof': 'none',
         'windows': 'none', 'walls': {'n': ['xkkalban'], 's': ['wall']}}]}
    # the stable yard's gate: a double door 256 wide (the lane rule of 2026-11-20; the studio's `leaves: 2` since merge
    # point 15 shows the wing once on each 128 leaf, the second mirrored): MM7's arched oak wing `chb1dl` in its
    # stone arch, the warm stone nearest the royal kit's
    STABLE_DOOR = {'part': 'stable_gate', 'wall': 'n', 'leaves': 2}
    STABLE_WING = 'chb1dl'
    for n in range(1, 5):
        for restored in (False, True):
            parts = copy.deepcopy(KAL_STAGE_PARTS[n]) + (copy.deepcopy(KAL_RESTORED_ONLY.get(n, [])) if restored else [])
            kal = {'id': 'thing:kalindra_%d%s' % (n, '' if restored else '_ghost'), 'kind': 'building',
                   'at': [35.0, 64.0], 'size': [8.0, 12.0], 'kit': 'grey', 'door': 'none', 'floor': KAL_H,
                   'title': 'Castle Kalindra', 'textures': dict(royal_tex if restored else ghost_tex), 'parts': parts,
                   'hidden': restored,
                   'notes': ("Stage %d's part, %s (D-30): %s at load, swapped by evt:kalindra_%d."
                             % (n, 'restored in white stone' if restored else 'out of phase',
                                'hidden' if restored else 'shown', n))}
            if n == 4 and restored:
                kal['door'] = dict(STABLE_DOOR)
                kal['textures']['door'] = STABLE_WING
                gate = next(p for p in parts if p['id'] == 'stable_gate')
                gate['walls'] = {'n': [['wall', 192], ['door', 256], ['wall', 192]]}
                gate['upper_walls'] = {'n': [['wall', 192], ['wall', 256], ['wall', 192]]}
                kal['effects'] = [{'text': "The stable yard's gate is barred from inside."}]
            S(kal)
    for restored in (False, True):
        kgate = {'id': 'thing:kalindra_gate' + ('_restored' if restored else ''), 'kind': 'building',
                 'at': [KAL_GATE[0] - 0.9, KAL_GATE[1] - 1.0], 'size': [1.4, 2.0], 'kit': 'grey', 'facing': 'e',
                 'floor': KAL_H, 'title': 'Castle Kalindra', 'hidden': restored,
                 'textures': dict(royal_tex if restored else ghost_tex, roof='csbr128'),
                 # the gate a 256 x 256 portcullis (the picture's own size) in the middle of the east front, the arms
                 # one whole panel above it in a coping frame (texture fit)
                 'parts': [{'id': 'gatehouse', 'at': [64, 64], 'size': [589, 896], 'wall_height': 896, 'roof': 'flat',
                            'battlements': True, 'windows': 'none',
                            'walls': {'e': [['wall', 320], ['door', 256], ['wall', 320]]},
                            'upper_walls': {'e': [['wall', 320], ['wall', 256], ['wall', 320]]}},
                           {'id': 'crest_frame', 'at': [653, 432], 'size': [32, 160], 'bottom': 304,
                            'wall_height': 288, 'roof': 'flat', 'windows': 'none',
                            'textures': {'wall': 'cstr128', 'roof': 'cstr128'}},
                           {'id': 'crest', 'at': [669, 448], 'size': [48, 128], 'bottom': 320, 'wall_height': 256,
                            'roof': 'none', 'windows': 'none', 'walls': CREST_WALLS_E}],
                 'door': {'part': 'gatehouse', 'wall': 'e'},
                 'condition': {'lua': hcall('m19.ghost_castle')},
                 'notes': "Stage 1's gate (D-30), %s at load." % ('restored, hidden' if restored else 'out of phase, shown')}
        if DUNGEON['dd03']:
            kgate['into'] = {'map': 'xeen_dd03.blv', 'arrival': 'entrance:gate'}   # DD-03's entrance (A8)
        else:
            kgate['effects'] = [msg('The gate is solid now, but Castle Kalindra (DD-03) is not open to you yet.')]
        S(kgate)
    for i, (d, at) in enumerate([('rock26', (40.4, 83.8)), ('rock12', (41.6, 84.4)), ('rock26', (39.2, 84.6))]):
        S(deco('thing:kalindra_rubble_%d' % (i + 1), d, at,
               title='Fallen white stone' if i == 0 else None) if i == 0 else deco('thing:kalindra_rubble_%d' % (i + 1),
                                                                                   d, at))
    S({'id': 'thing:kalindra_ramp', 'kind': 'stairs', 'line': [[47.6, 67.4], [46.6, 69.0]], 'width': 512,
       'ramp': True, 'rise': 120, 'textures': {'wall': 'cswl128', 'top': 'csbr128'}, 'title': "Kalindra's ramp"})
    S({'id': 'thing:luna_ring', 'kind': 'stone_ring', 'at': [30, 62], 'radius': 448, 'count': 7, 'lintel': False,
       'title': "Luna's stones"})
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [27.0, 76.0], 'height': 768, 'title': 'Obelisk',
       'effects': hook('obelisks.d1')})
    # ---------------------------------------------------------------- the south bank and the meadows
    S({'id': 'thing:prayer_shrine', 'kind': 'building', 'at': [51.2, 89.2], 'size': [1.6, 1.6], 'kit': 'stone',
       'title': 'The prayer shrine', 'door': 'none',
       'parts': [{'id': 's', 'at': [205, 205], 'size': [410, 410], 'wall_height': 320, 'posts': 40, 'roof': 'cone',
                  'roof_pitch': 52, 'windows': 'none', 'textures': {'roof': 'xlslate', 'wall': 't09a01'},
                  'title': 'The prayer shrine',
                  **daily('d1_prayer_shrine',
                          [{'add': {'var': v, 'value': 10}} for v in
                           ('MightBonus', 'IntellectBonus', 'PersonalityBonus', 'EnduranceBonus', 'AccuracyBonus',
                            'SpeedBonus', 'LuckBonus')] +
                          [{'text': 'You pray. +10 to every stat until you rest.'}],
                          'You pray, and the shrine is silent. Come back tomorrow.')}]})
    S({'id': 'thing:falista_hut', 'kind': 'building', 'at': [45.5, 94.5], 'size': [1.5, 1.0], 'kit': 'poor',
       'door': 'none', 'title': "Falista's hut",
       'textures': GRADE['poor'],
       'parts': [{'id': 'hut', 'at': [64, 64], 'size': [640, 384], 'wall_height': 256, 'roof': 'gable',
                  'roof_pitch': 40, 'windows': 'alternate', 'title': "Falista's hut",
                  'effects': [msg("Falista's hut is empty. A note on the table: \"Gone to the Clouds. Back when I am "
                                  "restored.\"")]}]})
    S({'id': 'thing:shipwreck', 'kind': 'building', 'at': [52.6, 82.4], 'size': [2.0, 1.0], 'kit': 'poor',
       'door': 'none', 'title': "A castaway's wreck", 'floor': 900, 'turn': 20,
       'ruin': {'height': [64, 256], 'gaps': 0.45, 'thickness': 32, 'seed': 5},
       'parts': [{'id': 'hull', 'at': [96, 64], 'size': [832, 384], 'wall_height': 256, 'roof': 'none',
                  'windows': 'none', 'textures': {'wall': '7trimd'}}]})
    S({'id': 'thing:castaway_camp', 'kind': 'tent', 'at': [30.2, 89.4], 'size': [576, 448], 'height': 256,
       'open': True, 'title': "The castaway's lean-to",
       'effects': [{'text': 'A cold fire, fish bones, and a calendar scratched into a plank: forty days, then nothing.'}],
       'notes': "The wreck's castaway camped here, under Kalindra's cliff (a place for the 6,000 rule)."})
    S(deco('thing:castaway_fire', 'dec24x', (31.6, 90.6), title='A dead fire'))
    S({'id': 'thing:wreck_chest', 'kind': 'chest', 'at': [53.6, 82.9], 'title': "A castaway's sea chest",
       'chest': {'level': 2, 'random_items': 3}})
    S(deco('thing:wreck_bottle', 'dec05', (53.0, 83.3), title='A bottle in the reeds',
           effects=[{'text': 'A message in the bottle: "Day 40. Still no boat. The sky is the wrong colour here."'}],
           once=True))
    S(K.well('thing:might_well', (100.0, 93.0), title='The Well of Might'))
    structures[-1]['condition'] = {'not': {'player_bit': 11290}}
    structures[-1]['effects'] = [{'player_bit': 11290}, {'add': {'var': 'BaseMight', 'value': 2}},
                                 {'text': '+2 Might (permanent)'}]
    structures[-1]['else_effects'] = [{'text': 'Cool water.'}]
    S(deco('thing:melon_patch', 'plant02', (82.0, 91.0), title='Melon vines',
           effects=[{'lua': 'if %s then for i = 1, 3 do evt.GiveItem(0, 0, %d) end end'
                     % (hcall('q-d9.melons_south'), ITEMS['monga_melon'])}]))
    S(deco('thing:melon_field', 'plant02', (64.0, 67.4), title="Pip Melonby's field", once=True,
           effects=[{'lua': '%s evt.GiveItem(0, 0, %d)' % (hcall('q-d9.melon_field'), ITEMS['monga_melon'])},
                    {'text': 'A Monga melon at the field\'s edge, ripe.'}]))
    S({'id': 'thing:rim_falls', 'kind': 'waterfall', 'line': [[31, 103.5], [31, 105.5]], 'top': RIVER,
       'foot': 0, 'lean': 220, 'spread': 1.7, 'back': 768, 'pool': 768, 'rock_size': 400, 'rise': 64,
       'textures': {'rock': 't2bs'}, 'title': 'The Vale Falls',
       'notes': "The Vale Water's fall off the world rim: a view, no click (D-23)."})
    S(deco('thing:falls_sound', 'Snd_Brook', (31.2, 103.0)))
    # ---------------------------------------------------------------- signposts (the four of L1)
    for sid, at, arms in (
            ('sign_gate_fork', (62.2, 39.3), [('Castleview', 's'), ('The Forbidden Zone', 'n'),
                                              ('The Dark Grove, Kalindra', 'w'), ('The East Bridge', 'e')]),
            ('sign_east_bridge', (77.0, 61.0), [('Castleview', 'n'), ('Sprite Forest', 'e')]),
            ('sign_west_fork', (48.6, 46.4), [('Castle Kalindra', 's'), ('The Western Tower', 'w'),
                                              ('Castleview', 'e')]),
            ('sign_south_fork', (84.8, 81.2), [('The Well of Might', 'e'), ('The prayer shrine', 'w'),
                                               ('The east road', 'n')])):
        S({'id': 'thing:%s' % sid, 'kind': 'sign', 'at': list(at), 'height': 256,
           'arms': [{'title': t, 'toward': d} for t, d in arms]})
    # ---------------------------------------------------------------- actors
    actors = []
    def place(row, at, count, spread, group, **kw):
        a = {'monster': str(row), 'at': list(at), 'count': count, 'spread': spread, 'group': group, 'hostile': True}
        a.update(kw)
        actors.append(a)
    place(ROW['saboteur'], (77.6, 42.0), 4, 0.6, 1)                      # at the cut rope bridge's west end
    place(ROW['gremlin'], (96.0, 64.4), 4, 1.2, 2)                       # round the trebuchet
    place(ROW['gremlin_guard'], (97.6, 63.6), 2, 0.6, 2)
    place(ROW['saboteur'], (94.6, 61.4), 1, 0, 2)
    for i, at in enumerate(ELECTRAPEDES):                                # electrapedes round the great tree
        place(ROW['electrapede'], at, 3 if i == 0 else 2, 0.7, 3 + i)
    # the Sardaj (Q-D12): peaceful until q-d12.hostile or camp_burned (evt:sardaj)
    for row, at, n in ((ROW['barbarian'], (88.0, 25.0), 7), (ROW['sardaj'], (89.4, 26.2), 3),
                       (ROW['barbarian_chief'], (87.2, 24.0), 1)):
        actors.append({'monster': str(row), 'at': list(at), 'count': n, 'spread': 1.4 if n > 1 else 0,
                       'group': SARDAJ_GROUP, 'hostile': False})
    actors.append({'monster': str(ROW['yog']), 'npc': 4953, 'at': [89.2, 24.0], 'spread': 0, 'group': SARDAJ_GROUP,
                   'hostile': False})
    use('q-d12.sardaj')
    for npc, kind, at in ((4956, '361', (66.0, 41.9)), (4951, '377', (57.0, 41.2)), (4952, '517', (30.6, 62.6))):
        actors.append({'monster': kind, 'npc': npc, 'at': list(at), 'spread': 0, 'group': 52})
    relations = [{'of': [517, 518, 519], 'toward': 'party', 'relation': 'friendly'}]
    events = [
        {'id': 'evt:sky', 'trigger': 'load', 'effects': [{'lua': 'Xeen.applyDarksideSky()'}],
         'notes': "Darkside's sky by the sun's stage (A3's helper)."},
        {'id': 'evt:arrival', 'trigger': 'timer', 'every': 2, 'once': True, 'effects': hook('m14.arrival'),
         'notes': "M14: the first arrival's text (A3's hook runs once)."},
        {'id': 'evt:gates_open', 'trigger': 'load', 'condition': {'qbit': 'pass_entered'},
         'effects': [{'hide': 'thing:%s_%s' % (g, sd)} for g in ('north_gate', 'queens_gate') for sd in ('outer', 'inner')],
         'notes': "m14.gate_open (A3): after the first entry both gates stand open."},
    ] + [
        {'id': 'evt:kalindra_%d' % n, 'trigger': 'load', 'condition': {'lua': 'Xeen.stageOf("kalindra") >= %d' % n},
         'effects': [{'hide': ghost}, {'show': solid}] + ([{'lua': 'evt.SetMapVar("AmbientSound%d", 2)' % SHIMMER_KEY}]
                                                         if n == 4 else []),
         'else_effects': [{'show': ghost}, {'hide': solid}] + ([{'lua': 'evt.SetMapVar("AmbientSound%d", 1)'
                                                                 % SHIMMER_KEY}] if n == 4 else []),
         'notes': "D-30: Castle Kalindra's stage %d parts restored (Xeen.stageOf, A3)." % n
                  + (" Stage 4: the castle wholly in phase, AU's shimmer loop (sound:kalindra_shimmer) off." if n == 4
                     else '')}
        for n in range(1, 5)
        for ghost, solid in [(['thing:kalindra_%d_ghost' % n] + (['thing:kalindra_gate'] if n == 1 else []),
                              ['thing:kalindra_%d' % n] + (['thing:kalindra_gate_restored'] if n == 1 else []))]
    ] + [
        {'id': 'evt:kalindra_phase', 'trigger': 'load',
         'effects': [{'lua': 'local s = Xeen.stageOf("kalindra") if s ~= evt.GetMapVar("%s", 0) then '
                             'evt.SetMapVar("%s", s) evt.PlaySoundName("xeen_phase_shift", %d, %d, %d) end'
                             % (KAL_SHOWN_VAR, KAL_SHOWN_VAR, KAL_HILL[0], KAL_HILL[1], KAL_HILL[2])}],
         'notes': "AU (2026-11-20): xeen_phase_shift on the castle hill when the stage shown differs from the last one "
                  "shown on this map (the named map variable %s), not on every load." % KAL_SHOWN_VAR},
        {'id': 'evt:sabotage', 'trigger': 'load', 'condition': {'qbit': 'court_won'},
         'effects': [{'hide': 'thing:rope_bridge_cut_w'}, {'hide': 'thing:rope_bridge_cut_e'},
                     {'show': 'thing:rope_bridge'}, {'hide': 'thing:mill_burnt'}, {'show': 'thing:mill'}],
         'notes': "q-d1.sabotage (A3): the bridge and the mill mended once the court is won."},
        {'id': 'evt:sardaj', 'trigger': 'load',
         'condition': {'any': [{'qbit': 'sardaj_hostile'}, {'qbit': 'sardaj_camp_burned'}]},
         'effects': [{'lua': 'evt.SetMonGroupBit(%d, MonsterBits.Hostile, true)' % SARDAJ_GROUP}],
         'notes': 'hook: q-d12.sardaj (A3): the Sardaj hostile on hostile or camp_burned.'},
        # A6 s27: Yog's "Battle!" (A3's dialogue sets q-d12.hostile) turns the camp at once, not at the next load
        {'id': 'evt:sardaj_war', 'trigger': 'timer', 'every': 1,
         'condition': {'all': [{'any': [{'qbit': 'sardaj_hostile'}, {'qbit': 'sardaj_camp_burned'}]},
                               {'not': {'map_var': 'sardaj_turned'}}]},
         'effects': [{'set': {'var': {'map_var': 'sardaj_turned'}, 'value': 1}},
                     {'lua': 'evt.SetMonGroupBit(%d, MonsterBits.Hostile, true)' % SARDAJ_GROUP}],
         'notes': "hook: q-d12.sardaj (A3): the Sardaj turn within a second of Yog's Battle! (the dialogue sets the "
                  "bit); evt:sardaj keeps them hostile on every later load."},
    ]
    use('q-d1.sabotage')
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
    VALE = {'tree12': 2, 'tree20': 2, 'tree13': 1}
    GROVE = [[38.5, 28.5], [55.5, 28.5], [56.5, 33], [53, 37.5], [44, 41.5], [38.5, 37.5]]
    # A6 fix (2026-11-20): a dense dark wood, not saplings on dirt: close-spaced darker shipped trees (MM7's dark
    # broadleaf 7tree04 and 7tree10, the tall conifer tree60, MM8's dead tree28, a few of MM6's swamp trees), all
    # about 1,000-1,400 high under the great tree's 3,200 trunk; kept clear of the arachnoids' and electrapedes'
    # clearings, a glade round the great tree, the webbed pack and the grove path
    DARK_WOOD = {'7tree04': 5, '7tree10': 3, 'tree28': 2, 'swptree2': 1, 'swptree4': 1, 'tree60': 1}
    clearings = [tuple(a['circle']['at']) for a in areas if a['id'] == 'pop:grove_arachnoids']

    def off_grove(p):
        return (any(math.hypot(p[0] - c[0], p[1] - c[1]) < 1.6 for c in clearings)
                or any(math.hypot(p[0] - c[0], p[1] - c[1]) < 1.5 for c in ELECTRAPEDES)
                or math.hypot(p[0] - GREAT_C[0], p[1] - GREAT_C[1]) < 3.0
                or math.hypot(p[0] - GROVE_ROPE_ARRIVAL[0], p[1] - GROVE_ROPE_ARRIVAL[1]) < 2.1
                or math.hypot(p[0] - ROPE_AT[0], p[1] - ROPE_AT[1]) < 1.8
                or math.hypot(p[0] - 43.2, p[1] - 38.3) < 1.0
                or dist_to_line(p[0], p[1], GROVE_PATH) < 0.8)
    scatter.extend(K.even_stand('scatter:dark_grove', GROVE, DARK_WOOD, 0.7, 0.8, d_pair=0.6, pair_share=0.3,
                                edge=1.5, edge_keep=0.7, avoid=off_grove, seed=23))
    scatter.append({'id': 'scatter:grove_undergrowth', 'kinds': {'bush02': 3, 'bush03': 3, 'plant05': 2, 'plant32': 2},
                    'count': 70, 'polygon': GROVE, 'clusters': 26})
    sc('scatter:grove_bones', '7dec18', 12, GROVE, clusters=5)
    sc('scatter:grove_rocks', '6rock03', 14, GROVE, clusters=6)
    HEATH = [[25, 37], [37, 37], [38.5, 46], [44.5, 56.5], [25, 56.5]]
    stand('scatter:heath_trees', HEATH, VALE, 2.0, 2.4)
    sc('scatter:heath_rocks', '6rock03', 30, HEATH, clusters=10)
    sc('scatter:heath_plants', 'plant02', 40, HEATH, clusters=12)
    SIEGE = [[56, 23], [80, 23], [80, 38.5], [71, 38.5], [66, 36.5], [63, 32], [56, 30]]
    stand('scatter:siege_trees', SIEGE, VALE, 1.0, 3.0)
    sc('scatter:siege_rocks', '6rock07', 25, SIEGE, clusters=8)
    sc('scatter:siege_bones', '7dec18', 10, SIEGE, clusters=4)
    SARDAJ = [[84, 30], [96, 30], [96, 50], [86, 50], [85, 42]]
    stand('scatter:sardaj_trees', SARDAJ, VALE, 2.0, 2.4)
    sc('scatter:sardaj_rocks', '6rock03', 18, SARDAJ, clusters=6)
    FOOT = [[96, 19], [110, 19], [110, 51], [100, 51], [96, 44]]
    stand('scatter:foothill_trees', FOOT, VALE, 2.5, 2.2)
    sc('scatter:foothill_rocks', '6rock07', 30, FOOT, clusters=10, steep=True)
    EASTC = [[86, 52], [101, 52], [101, 78], [90, 79], [86, 70]]
    stand('scatter:camp_trees', EASTC, VALE, 1.5, 2.6)
    sc('scatter:camp_bones', '7dec18', 8, EASTC, clusters=3)
    MEAD = [[60, 85], [80, 77], [90, 75], [109.5, 75], [109.5, 103.5], [60, 103.5]]
    stand('scatter:meadow_trees', MEAD, VALE, 1.6, 2.6)
    sc('scatter:meadow_plants', 'plant02', 70, MEAD, clusters=20)
    sc('scatter:meadow_rocks', '6rock03', 20, MEAD, clusters=8)
    BANK = [[38, 88], [44, 84], [52, 84], [60, 84.5], [60, 103.5], [33, 103.5], [33, 100]]
    stand('scatter:bank_trees', BANK, VALE, 2.5, 2.2)
    sc('scatter:bank_plants', 'plant02', 30, BANK, clusters=10)
    stand('scatter:luna_birches', [[27, 58.5], [34.5, 58.5], [34.5, 65.5], [27, 65.5]], {'tree13': 2, 'tree12': 1},
          22.0, 1.3, edge=False)
    WEST_VALE = [[38, 46.5], [46, 49], [46, 60], [33, 61], [33, 56], [44, 56]]
    for sid, poly, per in (('scatter:edge_n', [[24.5, 0], [128, 0], [128, 18.5], [24.5, 18.5]], 2.0),
                           ('scatter:edge_e', [[110.5, 18.5], [128, 18.5], [128, 103.5], [110.5, 103.5]], 3.0)):
        scatter.append({'id': sid, 'count': int(per * K.poly_area(poly) / 100.0), 'polygon': poly, 'spacing': 1.6,
                        'spacing_group': 'trees', 'kinds': dict(VALE)})
        scatter.append({'id': sid.replace('edge', 'edge_rocks'), 'decoration': '6rock07',
                        'count': int(0.8 * K.poly_area(poly) / 100.0), 'polygon': poly, 'clusters': 10, 'steep': True})
    sc('scatter:lip_rocks', '6rock03', 30, line=[[24.6, 20], [24.6, 103.4]])
    sc('scatter:lip_rocks', '6rock03', 30, line=[[25, 103.4], [108, 103.4]])
    scatter.append({'id': 'scatter:sea_stacks', 'decoration': 'rock26', 'count': 12, 'on': 'water',
                    'polygon': [[4, 20], [21, 20], [21, 110], [4, 110]]})
    for i, at in enumerate([(53.6, 45.6), (69.8, 63.6), (55.4, 63.7), (74.6, 58.6), (57.9, 63.6), (51.2, 50.2)]):
        S(deco('thing:town_tree_%d' % (i + 1), ['tree12', 'tree20'][i % 2], at))
    # trees round the walls (town_feel: the shipped towns stand among trees), clear of the gates and the roads
    RING = [[46, 40], [80, 40], [80, 67], [46, 67]]
    def off_ring(p):
        return K.inside(p, TOWN_TERRACE) or any(K.seg_dist(p, a, b) < 1.5 for l in ROADS + PATHS for a, b in
                                                 zip(l, l[1:])) or math.hypot(p[0] - 63, p[1] - 42) < 4 or \
            math.hypot(p[0] - QUEEN_GATE[0], p[1] - QUEEN_GATE[1]) < 3 or dist_to_line(p[0], p[1], RIVER_LINE) < 2.5
    scatter.extend(K.even_stand('scatter:ring_trees', RING, dict(VALE), 0.03, 2.2, avoid=off_ring, seed=11))
    ground = [
        {'material': 'grass', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'Grass everywhere but the town, the tracks, the bare hills and the grove floor.'},
        {'material': 'dirt', 'polygon': GROVE, 'notes': 'The Dark Grove: a dark leaf-litter floor.'},
        {'material': 'dirt', 'polygon': [[66, 26], [78, 26], [78, 30], [66, 30]], 'notes': 'The siege trenches.'},
        {'material': 'dirt', 'polygon': [[67, 27], [77, 27], [77, 35], [67, 35]], 'notes': "The acid pond's rim."},
        {'material': 'dirt', 'polygon': [[93, 60], [100, 60], [100, 66], [93, 66]],
         'notes': "The besiegers' trampled camp."},
        {'material': 'dirt', 'polygon': [[84.5, 21.5], [92.5, 21.5], [92.5, 29], [84.5, 29]],
         'notes': 'The Sardaj camp.'},
        {'material': 'dirt', 'polygon': [[57.5, 66.5], [70.5, 66.5], [70.5, 70.5], [57.5, 70.5]],
         'notes': "Pip Melonby's melon rows."},
        {'material': 'dirt', 'steeper_than': 640, 'polygon': [[0, 0], [128, 0], [128, 104], [0, 104]],
         'notes': 'Bare rock on the steep hills, the gorge walls and the cliffs.'},
        {'material': 'dirt', 'polygon': WALL, 'notes': 'Castleview inside its walls: packed earth and paving.'},
    ]
    for line in PATHS:
        ground.append({'material': 'dirt', 'line': line, 'width': 2, 'notes': 'a track'})
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('D1 Castleview Vale, written by output/studio_cal/d1/tools/gen.py. Cells [x, y], x east, y south. '
                  'Heights are map units above the stars below the rim (0): the Vale Water 830, the vale 1,000-1,250, '
                  'Castleview 1,150 (its walls 600 high), Kalindra\'s rise 1,750, the north hills to 3,600.'),
        'frame': {'playable': [19, 19, 90, 90],
                  'edges': ([{'side': 'east', 'span': [56, 64], 'neighbour': 'edge:east'}] if D2_LIVE else []),
                  'edge': {'height': 2000, 'west': 0, 'south': 0, 'east': 1100}, 'rim': rim},
        'heights': heights, 'water': water, 'roads': roads, 'districts': districts, 'points': points,
        'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground, 'structures': structures,
        'actors': actors + V.sketch_actors('D1'), 'relations': relations + V.relations('D1'),
        'events': events,
    }
    atmosphere = {'format': 0, 'sky': 'xeendark1', 'weather': {},
                  'notes': ("Darkside's amber day (xeendark1; A3's Lua switches xeendark2/3 by the sun's stage on "
                            "load). No weather.")}
    check_gate_lanes(structures, scatter)
    missing = sorted(set(HOOKS) - USED)
    if missing:
        raise SystemExit('A3 hooks on D1 not used: %s' % missing)

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
        os.path.realpath(__file__)), '../common/beds/d1.yml')))['sounds']
    # F2 (2026-11-21): wing door pictures (t06a03/t06b03, t09a03a) hung as double doors, never alone
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    import house_doors as HD
    for _note in HD.double_doors_sketch(sketch) + HD.bury_mouths_sketch(sketch) + HD.blind_mouths_sketch(sketch):
        print('door:', _note)   # F8 too: cave mouths as wide as their rim, no dark mouth that leads nowhere
    # F16/D-90 (s32): every door into a dungeon shows its trans.txt row (A3's source/entrances.yml) in the window
    import entrance_screens as ES
    print('entrance screens:', ES.apply_sketch(sketch, 'xeen_d1'))
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
    print('D2_LIVE', D2_LIVE, 'dungeons', {k: v for k, v in DUNGEON.items() if v}, 'hooks', len(USED))


if __name__ == '__main__':
    build()
