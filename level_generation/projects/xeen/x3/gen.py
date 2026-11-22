#!/usr/bin/env python3
"""X3 Lifeforce Lagoon: writes the L2, L3 and L4 briefs (each a whole project folder) from the approved L1 plan
(tools/gen_l1.py, run first by ../vw.sh) and the decisions D-11.1, D-11.3, D-11.4 and D-11.6 (devdocs/xeen/DECISIONS.md).
L2: the plan without a sketch; L3: the plan with the full sketch; L4: L3 and atmosphere (ids.lock.yml is the build's).
The design: devdocs/xeen/MAPS.md X3, the L1 board (output/studio_cal/x3/mockups/board_x3.png), A4's town file
(assets_dev/worlds/xeen/source/towns/x3.yml) and A3's hooks (data_tables/quest_hooks.yml, map X3).
Coordinates: terrain cells [x, y], x east, y south from the north-west corner; X = (x - 64) * 512, Y = (64 - y) * 512.
Edit here and run ../vw.sh, never the project files.
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

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import kit as K
import gen_l1 as G

ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
BRIEFS = os.path.join(ROOT, 'devdocs/xeen/briefs/x3')
STEM = 'xeen_x3'

# A3's hooks on X3 (data_tables/quest_hooks.yml); hook() refuses a name that is not there
HOOKS = yaml.safe_load(open(os.path.join(ROOT, 'assets_dev/worlds/xeen/data_tables/quest_hooks.yml')))

def hook(name):
    assert name in HOOKS, name
    return [{'lua': 'XeenQuests.hook("%s")' % name}]

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

def lua_str(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')


def daily(sid, effects, again):
    """D-70 Q2: a temporary source works once a day for the whole party (Xeen.usedToday / Xeen.markToday, every member
    by evt.ForPlayer(Players.All)); a second use the same day gives `again` and nothing else."""
    key = 'x3_' + sid.split(':', 1)[1]
    return {'condition': {'not': {'lua': 'Xeen.usedToday("%s")' % key}},
            'effects': [{'lua': 'Xeen.markToday("%s") evt.ForPlayer(Players.All)' % key}] + effects,
            'else_effects': again}

def sign(sid, at, title, effects, height=224, width=160, **kw):
    d = {'id': sid, 'kind': 'sign', 'at': [round(at[0], 3), round(at[1], 3)], 'height': height, 'width': width,
         'title': title, 'effects': effects}
    d.update(kw)
    return d

def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d

# ---------------------------------------------------------------------------------------------------------------
# Water and land
# ---------------------------------------------------------------------------------------------------------------
LAG = 860            # the Lifeforce Lagoon
RIVER_LVL = 850      # the Lagoon Water, west to X5
SHORE = 892          # the reed shores
RIM_Y = 104          # the world rim: a cliff along y 104, the stars (water at 0) below
# The lagoon in two bodies round the Tower's islet (a body's outline may not cross itself), the causeway a stone
# bridge over the water (L1 drew it as a strip of land; built as arches it is the signature view's line).
ISLE = [[61, 66], [63, 65], [66, 65], [68, 66], [69, 69], [68, 72], [65, 73], [61, 72], [60, 69]]
LAGOON_N = [[56, 65], [58, 60], [62, 58], [65, 58], [70, 56], [78, 57], [85, 59], [89, 63], [91, 70],
            [69, 70], [68, 66], [66, 65], [63, 65], [61, 66], [60, 70], [56, 70]]
LAGOON_S = [[56, 68], [60, 68], [61, 72], [65, 73], [68, 72], [69, 68], [91, 68], [90, 76],
            [88, 79], [85, 80], [84, 81], [85, 82], [88, 82], [86, 85], [82, 86], [75, 88],
            [68, 87], [62, 84], [58, 79], [56, 72]]
LAGOON_OUT = G.LAGOON            # the whole shore line (for the shore slopes)
RIVER = [[57, 69], [50, 67], [44, 66], [38, 64], [30, 63], [22, 62], [10, 62], [0, 62]]
PONDS = G.PONDS

def in_lagoon(p):
    return (K.inside(p, LAGOON_N) or K.inside(p, LAGOON_S)) and not K.inside(p, ISLE)

# calm places: no rolling ground
CALM = [(99.5, 72.5, 9), (87, 43, 5), (82.5, 33.5, 6), (64.5, 69.5, 4), (34, 84, 3), (74, 93.5, 3), (27.5, 34, 3),
        (106, 40.5, 3), (21, 59, 3), (50, 21, 3), (59.5, 30, 2), (63, 52, 3), (76.5, 99, 2), (98, 25.5, 2)]

def roll(x, y):
    w = 1.0
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 4.0))
    w = min(w, smooth((RIM_Y - 2 - y) / 4.0))
    v = (150 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.6 + 1.1) + 90 * math.sin((x + 1.2 * y) / 4.7 + 0.3)
         + 50 * math.sin((x - 1.7 * y) / 2.3))
    return w * v

def height(x, y):
    h = 960.0
    # the land rises gently north toward the savannah (X4's edge at 1,300)
    h += 360 * smooth((36 - y) / 30.0)
    # the Bogwood's broken hills (north-west), to about 1,900
    h += (bump(x, y, 30, 28, 16, 620) + bump(x, y, 25, 23, 8, 380) + bump(x, y, 37, 21, 7, 300)
          + bump(x, y, 40, 41, 6, 240) + bump(x, y, 21, 42, 6, 260) + bump(x, y, 12, 30, 11, 600)
          + bump(x, y, 10, 10, 14, 900))
    # the obelisk's knoll in the north vale
    h += bump(x, y, 59.5, 30, 4.5, 380)
    # the Crow Hills: the Crow's Crown (3,450) and its shoulders; their backs north and east of the square
    h += (bump(x, y, 102, 22, 13, 2350) + bump(x, y, 91, 20, 9, 1100) + bump(x, y, 80, 21, 10, 900)
          + bump(x, y, 70, 19, 7, 800) + bump(x, y, 111, 28, 8, 800) + bump(x, y, 96, 28, 5, 300)
          + bump(x, y, 118, 12, 14, 1500) + bump(x, y, 63, 11, 8, 500) + bump(x, y, 80, 6, 10, 900))
    # Newcastle's rise (its top a terrace at 1,750)
    h += bump(x, y, 82.5, 33.5, 7, 700)
    # the camp and the X2 road at about 1,020
    h += bump(x, y, 88, 43, 8, 60) + bump(x, y, 107, 41, 9, 70)
    # the east ridge behind Nightshadow (X2's west hills beyond the edge)
    if 46 < y < 104:
        h += 1300 * smooth((x - 109.5) / 9.0) * smooth((103 - y) / 4.0)
    # the Gloomwood's rise and the Tomb's mound
    h += 170 * smooth((y - 77) / 6.0) * smooth((60 - x) / 6.0)
    h += bump(x, y, 24, 93, 7, 160) + bump(x, y, 46, 97, 6, 140) + bump(x, y, 34, 86.5, 3.4, 240)
    # the Lifeforce Spring's knoll and the drowned shore
    h += bump(x, y, 74, 93.5, 3, 60)
    # the fen west of the lagoon lies low (X5's fen at 900)
    if 50 < y < 78:
        h -= 70 * smooth((58 - x) / 16.0)
    h += roll(x, y)
    # the Lagoon Water's banks
    d = dist_to_line(x, y, RIVER)
    if d < 5:
        h = SHORE - 8 + (h - SHORE + 8) * smooth((d - 1.6) / 3.4)
    # the ponds: their banks a little above their water
    for poly, lvl, _ in PONDS.values():
        if K.inside((x, y), poly):
            return lvl - 64
        e = poly_dist((x, y), poly)
        if e < 2.5:
            h = lvl + 24 + (h - lvl - 24) * smooth(e / 2.5)
    # the lagoon: reed shores at about 890, the land back over four cells; the islet
    if K.inside((x, y), ISLE):
        e = poly_dist((x, y), ISLE)
        return SHORE + (1000 - SHORE) * smooth(e / 1.5)
    if in_lagoon((x, y)):
        return LAG - 96
    dl = poly_dist((x, y), LAGOON_OUT)
    if dl < 4.5:
        h = SHORE + (h - SHORE) * smooth((dl - 0.4) / 4.1)
    return h

def grid_rows(step=4, unit=32):
    rows = []
    for j in range(128 // step):
        rows.append([int(round(height(step * i + step / 2, step * j + step / 2) / unit)) for i in range(128 // step)])
    return rows

# ---------------------------------------------------------------------------------------------------------------
# Roads (cells). The L1 lines, with Nightshadow's road through the square and the causeway as a bridge.
# ---------------------------------------------------------------------------------------------------------------
EAST_ROAD = [[128, 40], [116, 40], [106, 40.5], [99, 41.5], [94, 42.5]]
CAMP_ROAD = [[94, 42.5], [90, 43.5], [86, 44], [80, 45.5], [74, 47.5], [68, 49.5], [63, 52]]
NORTH_ROAD = [[63, 52], [60, 46], [57, 38], [54, 30], [51, 22], [50, 12], [50, 0]]
WEST_ROAD = [[63, 52], [58, 54], [52, 55.5], [46, 57], [40, 58], [35, 58.5], [28, 59], [20, 59], [0, 59]]
NS_ROAD = [[94, 42.5], [95.5, 48], [97, 54], [98.5, 59], [99.5, 62], [100.5, 66.5], [100.5, 70]]
SQUARE_ST = [[100.5, 70], [100.5, 75]]
SOUTH_ST = [[100.5, 75], [101, 79], [102.5, 82], [103, 84.5]]
QUAY_LANE = [[100.5, 78], [97.5, 78], [94, 78], [91, 78.5], [89, 80]]
NEWCASTLE_STAIR = [[86, 44], [84, 41.5], [82.5, 39.5], [82.5, 37.5]]
TOMB_PATH = [[35, 58.5], [36, 60.5], [37, 61.5], [37, 67], [36, 68.5], [34.5, 74], [34, 79]]
TOMB_LANE = [[34, 79], [34, 82.5]]
GLOOM_PATH = [[34, 79], [42, 84], [50, 88], [58, 90.5], [66, 92], [73, 93.5]]
SHORE_PATH = [[103, 84.5], [96, 87.5], [88, 89], [80, 91.5], [75, 93.5]]
CAUSEWAY = [[64.5, 56.5], [64.5, 66.0]]
COBBLE = [EAST_ROAD, CAMP_ROAD, NS_ROAD, SQUARE_ST]
DIRT = [NORTH_ROAD, WEST_ROAD, SOUTH_ST, QUAY_LANE, NEWCASTLE_STAIR, TOMB_PATH, TOMB_LANE]

# ---------------------------------------------------------------------------------------------------------------
# Nightshadow and Ebenezer's camp: A4's houses (towns/x3.yml). (building, index, NW corner, facing, fp, kit, shape,
# house, name, gate) gate: None open; 'opens' after q-c7.done; 'guild' 4103 until q-c7.done, then 4104.
# Nightshadow: cloudside_town's darkest grades (hhp poor, hhm3 grey, hhm1 timber), temple, manor and guild in stone.
# ---------------------------------------------------------------------------------------------------------------
LIB = 112141         # q-c7.done
# D-11.6 by the world's edge_spans table (A1, merge point 9): X3's whole north edge leads to X4's x 36 arrival on X4's
# ground, facing north (X4's DOORS.md); X4's south edge west of x 0 leads back to X3's north arrival
X4_ARRIVAL = (-14336, -22016, 992, 90)
CLOSED = {h['id']: h.get('closed_text') for h in yaml.safe_load(open(os.path.join(
    ROOT, 'assets_dev/worlds/xeen/source/towns/x3.yml')))['houses']}
NS_PLOTS = [
    ('building:moon_guild', None, (95, 65.5), 'e', [2, 2], 'stone', 'tower_house', 4103, 'The Moon Guild', 'guild'),
    ('building:du_monay_manor', None, (102, 66.5), 'w', [2.5, 2.5], 'stone', 'L2', 4105, 'Du Monay Manor', None),
    ('building:nightshadow_temple', None, (94, 70.5), 'e', [2.5, 2.5], 'stone', 'temple', 4106,
     'Temple of the Dawn', 'opens'),
    ('building:nightshadow_tavern', None, (101, 61.5), 'w', [2, 1.5], 'timber', 'jetty', 4107,
     'The Coffin and Candle', 'opens'),
    ('building:treasure_trove', None, (102.5, 70.5), 'w', [1.5, 1.5], 'grey', 'gable_porch', 4108, 'Treasure Trove',
     'opens'),
    ('building:nightshadow_alchemist', None, (102.5, 72.5), 'w', [1.5, 1.5], 'timber', 'gable_porch', 4109,
     'Garlic and Grave Goods', 'opens'),
    ('building:gnome_home', None, (95.5, 63), 'e', [1.5, 1.5], 'poor', 'cottage', 4111, 'Gnome Home', 'opens'),
] + [('building:nightshadow_houses', i + 1, tuple(at), f, fp, kit, 'cottage' if fp == [1, 1] else 'gable_porch',
      4112 + i, G.NS_HOUSE_NAMES[i], 'opens') for i, (at, f, fp, kit) in enumerate(G.NS_HOUSES)]
SIGNS = {'building:nightshadow_tavern': '7sgtvrn',
         'building:nightshadow_alchemist': '7sgalch',
         # D-92 (A4, 2026-11-22): every service hangs its kind's sign; a guild its school's
         'building:moon_guild': 'sgdark',
         'building:treasure_trove': 'sgmagi'}
CAMP_PLOTS = [
    ('building:camp_shrine', None, (88.5, 45), 'n', [1.5, 1.5], 'stone', 'gable_porch', 4102, 'The Camp Shrine', None),
]
TOWN_NIGHTSHADOW = G.TOWN_NIGHTSHADOW
SQUARE = [[97, 70], [102, 70], [102, 75], [97, 75]]
CAMP = G.CAMP

plots_by_space = {}
plan_buildings = {}
footprints = []
doors_out = []

def plot_parts(kind, facing, fp, kit, sign_tex):
    F, D = K.plot_extent(facing, fp)
    roof = {'roof': K.ROOFS.get(kit, 'hhp2rf')} if kit != 'stone' else {'roof': 'hwm2rf'}
    if kind == 'temple':
        # a stone nave with its porch to the square and a square bell tower behind (Temple of the Dawn)
        b = K.box('body', facing, fp, 160, 64, int(fp[0] * 512) - 320, int(fp[1] * 512) - 512, roof='gable',
                  ridge_along=K.ACROSS[facing], roof_pitch=52, wall_height=448,
                  porches=[{'wall': facing, 'depth': 160, 'posts': 32, 'height': 288, 'floor': 16}])
        b['textures'] = dict(roof)
        t = K.box('tower', facing, fp, int(fp[0] * 256) - 160, int(fp[1] * 512) - 400, 320, 320, roof='hip',
                  roof_pitch=64, wall_height=1024, windows='none')
        t['textures'] = dict(roof)
        return [b, t], {'part': 'body', 'wall': facing}
    if kind == 'L2':
        parts, door = K.shape('L', facing, fp, kit, roof_tex=roof['roof'])
        for p in parts:
            p['wall_height'] = 512
        return parts, door
    parts, door = K.shape(kind, facing, fp, kit, sign=sign_tex, roof_tex=roof['roof'])
    return parts, door

def add_plot(space, entry, door_to):
    bid, idx, at, facing, fp, kit, kind, house, title, gate = entry
    x, y = at
    plot = {'building': bid}
    if idx:
        plot['index'] = idx
    plot.update({'at': [x, y], 'facing': facing, 'kit': kit})
    if door_to:
        plot['door_to'] = door_to
    parts, door = plot_parts(kind, facing, fp, kit, SIGNS.get(bid))
    plot['parts'] = parts
    plot['door'] = door
    plot['house'] = house
    plot['title'] = title
    if os.environ.get('X3_TF_OPEN'):
        pass   # town_feel's variant only (doors as after q-c7.done; root.sh's notes): never installed
    elif gate == 'guild':
        # A4: 4103 (night hours) while the Count rules, 4104 (day hours) after q-c7.done (TOWNS_FORMAT 1)
        plot['condition'] = {'not': {'qbit': 'nightshadow_liberated'}}
        plot['else_effects'] = [{'lua': 'evt.EnterHouse(4104)'}]
    elif gate == 'opens':
        plot['condition'] = {'qbit': 'nightshadow_liberated'}
        plot['else_effects'] = [msg(CLOSED[house])]
    plots_by_space.setdefault(space, []).append(plot)
    pb = plan_buildings.setdefault(space, {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [],
                   'service': title if not idx else 'residence (houses 4112-4120)'}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append(fp)
    footprints.append((bid, idx, K.footprint(x, y, facing, fp, 0)))
    doors_out.append((bid, idx, K.door_cell(x, y, facing, fp, 0, 0.0), K.door_cell(x, y, facing, fp, 0, 0.9), house))

for e in NS_PLOTS:
    add_plot('town:nightshadow', e, None)
for e in CAMP_PLOTS:
    add_plot('town:ebenezer_camp', e, 'link:camp_road')
for pb in plan_buildings.values():
    for b in pb.values():
        if b['count'] == 1:
            b['footprint_cells'] = b['footprint_cells'][0]

def check_roads():
    bad = []
    for b, ix, poly in footprints:
        for line in COBBLE:
            if K.line_hits_poly(line, poly, 0.45):
                bad.append('road against %s#%s: %s' % (b, ix, line[:3]))
        for line in DIRT:
            if K.line_hits_poly(line, poly, 0.3):
                bad.append('lane against %s#%s: %s' % (b, ix, line[:3]))
    for i, (b, ix, p) in enumerate(footprints):
        for (b2, ix2, q) in footprints[i + 1:]:
            if any(K.inside(v, q) for v in p) or any(K.inside(v, p) for v in q):
                bad.append('plots overlap: %s#%s and %s#%s' % (b, ix, b2, ix2))
    if bad:
        raise SystemExit('\n'.join(bad))

# ---------------------------------------------------------------------------------------------------------------
# Places (cells)
# ---------------------------------------------------------------------------------------------------------------
TOWER_C = (64.5, 69.5)      # the Tower of High Magic on its islet; its door looks north up the causeway
TOWER_R = 768
NEWCASTLE_AT = (78.5, 30.5)  # the ruin's NW corner; the rise's top a terrace at 1,750
NC_H = 1750
GATE = (82.5, 36.4)          # the gate between the two ruined gate towers
XD13_AT = (84.5, 33.5)       # the foundation stair (a wedge hatch) in the ruin's courtyard
TOMB_AT = (34, 85)         # the Tomb's barrow; its door looks north up the tomb lane
COFFIN = (98.5, 73.0)        # Draco's coffin on Nightshadow's square, its length north-south
DIALS = [(97.75, 70.4), (98.5, 70.4), (99.25, 70.4)]   # the dial walk along the square's north side
DIAL_START = [3, 6, 12]       # what each dial reads at first
MIRABETH = (85.6, 81.0)
MIRABETH_GROUP = 4
WORKER_GROUP = 51
SPRING = (74, 93.5)
WELL_SOUND = 'evt.PlaySoundName("xeen_well_drink")'   # AU's sounds (devdocs/xeen/AUDIO.md), tenth session
SPRING_BIT = 11280           # player bit, once per character (requested of A3's registry)
MARSH_BIT = 11281
RANGER_CAMP = (27.5, 34)
RANGER_QBIT = 116040         # x3.ranger_camp's own qbit (A3)

# The coffin's click (D-11.3): the two refusals (the dials, then the hour), then A3's q-c7.coffin; the lid goes and the
# stair shows at once (ShowThing/HideThing: the calls {show}/{hide} write)
# D-89 (A5 s29): no night condition; the dials alone
COFFIN_LUA = ('if not IsQBitSet(QBit(112142)) then evt.SimpleMessage(%s) '
              'elseif XeenQuests.hook("q-c7.coffin") then HideThing("thing:coffin_closed") ShowThing("thing:coffin_open") '
              'evt.PlaySoundName("xeen_coffin_lid") '
              'end' % (
                  lua_str("The lid refuses to budge. A symbol etched on the surface of the lid flashes pale blue "
                          "whenever you try to move it: three small dials, none of them set as they should be."),))

def build():
    check_roads()
    plan = yaml.safe_load(open(os.path.join(BRIEFS, 'L1/plan.yml')))
    project = yaml.safe_load(open(os.path.join(BRIEFS, 'L1/project.yml')))
    l1_sketch = yaml.safe_load(open(os.path.join(BRIEFS, 'L1/sketch.yml')))
    # ================================ project.yml
    neighbours = []
    for n in project['neighbours']:
        n = dict(n)
        if n['id'] == 'edge:north':
            # one side, two arrivals (D-11.6): a span is no travel row; the world's edge_spans table holds it
            n['span'] = [-32768, 32768]
            n['arrival'] = list(X4_ARRIVAL[:3])
            n['direction'] = X4_ARRIVAL[3]
            n['notes'] = ("X4 Burlock Savannah (D-11.6): the whole north edge leads to X4's x 36 arrival (-14336, -22016, "
                          "992) facing north, by the world's edge_spans table; X4's south edge west of x 0 arrives here "
                          "at entrance:north_road.")
        if n['id'] == 'edge:east':
            n['notes'] = ("X2 Rivercity and Lake Darzog: arrives at X2's west start. X2's west edge is sealed by its "
                          "own flooded sign today; when it opens it arrives here at entrance:east_road (DOORS.md).")
        if n['id'] == 'edge:west':
            n['notes'] = ("X5 Winterkill Tundra: arrives at X5's east start (A6 adds it: its lagoon road at y 59). "
                          "X5's east edge, when opened, arrives here at entrance:west_road (DOORS.md).")
        if n['id'] == 'door:xd11':
            n.pop('condition', None)
            n['notes'] = ("XD-11 Tower of High Magic (installed, A8): the door on the islet at the causeway's end, "
                          "facing north; A3's m13.tower_door (the Enchanted Key 12306) lets the party in. DOORS.md.")
        if n['id'] == 'door:xd08':
            n.pop('condition', None)
            n['notes'] = ("XD-08 Tomb of a Thousand Terrors (installed, A7): the barrow door in the Gloomwood, facing "
                          "north; A3's m10.tomb_door (the Stone of a Thousand Terrors 12304) lets the party in, to "
                          "XD-08's start inside the door. DOORS.md.")
        if n['id'] == 'door:xd13':
            n['notes'] = ("XD-13 Newcastle Keep (installed, A7): the foundation stair (a pit hatch) in the ruin's "
                          "courtyard leads in to XD-13's start once the party owns the land (m8.deed, 111160); "
                          "without the deed a short refusal. DOORS.md.")
        if n['id'] == 'door:xd24':
            n['notes'] = ("XD-24 Nightshadow Crypt (installed, A7): Count Draco's coffin on Nightshadow's square opens "
                          "at night once all three sundials read 9 (q-c7.dials_set); its stair leads in to XD-24's "
                          "start (0, 704, 0) facing south. XD-24's exit arrives 512 south of the coffin. DOORS.md.")
            n.pop('listed_only', None)
            n.pop('condition', None)
        neighbours.append(n)
    project['neighbours'] = neighbours
    project['rules'] = {'weather': 'world default', 'respawn': 'entrance:camp_fire',
                        'town_portal_anchor': 'entrance:nightshadow_square'}
    project['notes'] = ("X3 Lifeforce Lagoon (lane A5), built from the approved L1 with D-11.1, D-11.3, D-11.4 and "
                        + "D-11.6. The north edge leads to X4's x 36 arrival (edge_spans); the doors to XD-08, XD-11 and XD-13 and the coffin's stair to XD-24 "
                        "lead in. Written by output/studio_cal/x3/tools/gen.py.")
    # ================================ plan.yml (L1's, level L3, with the built changes)
    plan['level'] = 'L3'
    plan.pop('totals', None)
    for s in plan['spaces']:
        if s['id'] in plan_buildings:
            s['buildings'] = list(plan_buildings[s['id']].values())
        if s['id'] == 'town:ebenezer_camp':
            s['purpose'] = s['purpose'] + (" Ebenezer's Tent (house 4101) is a tent structure, thing:ebenezer_tent "
                                           "(A4's proposed door building:ebenezer_tent renamed).")
    for key in ('pois', 'points_of_interest', 'features'):
        for q in plan.get(key) or []:
            if isinstance(q, dict) and q.get('id') == 'poi:food_trees':
                q['count'] = 3
                q['spaces'] = list(q['spaces']) + ['zone:bogwood']
    plan['links'] = [l for l in plan['links']]
    for l in plan['links']:
        if l['id'] == 'link:causeway':
            l['kind'] = 'bridge'
            l['crosses'] = ['water:lagoon']
        if l['id'] == 'link:north_road':
            l['notes'] = "The north road to X4: its edge leads to X4's x 36 arrival (D-11.6, edge_spans)."
    # the tomb path over the Lagoon Water: the fen bridge's deck is its own link between two bridge heads (A5, fifth
    # session: a road's line may not lie in water)
    plan['spaces'] += [
        {'id': 'junction:fen_bridge_n', 'name': 'Fen bridge, north head', 'kind': 'junction',
         'purpose': "The tomb path's timber bridge over the Lagoon Water, its north end."},
        {'id': 'junction:fen_bridge_s', 'name': 'Fen bridge, south head', 'kind': 'junction',
         'purpose': "The tomb path's timber bridge over the Lagoon Water, its south end."}]
    for l in plan['links']:
        if l['id'] == 'link:tomb_path':
            l['to'] = 'junction:fen_bridge_n'
            l.pop('crosses', None)
            l.pop('features', None)
    plan['links'] += [
        {'id': 'link:fen_bridge', 'from': 'junction:fen_bridge_n', 'to': 'junction:fen_bridge_s', 'kind': 'bridge',
         'crosses': ['water:river'], 'features': ['a timber bridge over the Lagoon Water (thing:fen_bridge)']},
        {'id': 'link:tomb_path_s', 'from': 'junction:fen_bridge_s', 'to': 'junction:tomb_fork', 'kind': 'path'}]
    plan['links'].append({'id': 'link:square_street', 'from': 'zone:nightshadow_square', 'to': 'link:south_street',
                          'kind': 'road', 'notes': "Nightshadow's road through the square to the south street."})
    for e in plan['entrances']:
        if e.get('neighbour') == 'door:xd24':
            e.pop('condition', None)
            e['kind'] = 'both'
            e['how'] = ("The open coffin's stair: in to XD-24 (q-c7.coffin_opened); XD-24's exit arrives here, 512 "
                        "south of the coffin, facing away from it.")
        if e.get('neighbour') in ('door:xd08', 'door:xd13'):
            e.pop('condition', None)
            e['kind'] = 'both'
            e['how'] = {'door:xd08': "The tomb door: in with the Stone of a Thousand Terrors (m10.tomb_door); XD-08's "
                                     "exit arrives here, in front of the door.",
                        'door:xd13': "The foundation stair: in with the deed (m8.deed); XD-13's gate arrives here, "
                                     "below the hatch on the courtyard."}[e['neighbour']]
        if e.get('neighbour') == 'door:xd11':
            e.pop('condition', None)
    for e in plan['entrances']:
        if e['id'] == 'entrance:north_road':
            e['how'] = "X4's south edge west of x 0 arrives here (X3's north start, -7168, 22016, facing south; edge_spans)."
    plan['notes'] = ("L3/L4 (lane A5, 2026-11-20): the approved L1 (D-11.1: two Crow Hills toad markers at the hills' "
                     "south foot; D-11.3: the coffin's two states and two refusals; D-11.4: POIs counted as shipped; "
                     "D-11.6: the north road at x 50 to X4's x 36 arrival) with the sketch. Written by "
                     "output/studio_cal/x3/tools/gen.py.")
    # ================================ sketch.yml
    sk = {'format': 0, 'grid': 512}
    sk['notes'] = ("X3 Lifeforce Lagoon, L3/L4 sketch written by output/studio_cal/x3/tools/gen.py. Cells [x, y], x "
                   "east, y south. Heights are map units above the stars below the rim (0): the lagoon at 860, the "
                   "reed shores about 890, the fens 900-1,000, Nightshadow 1,000, Ebenezer's camp 1,020, Newcastle's "
                   "rise 1,750, the Crow's Crown about 3,450, the rim cliff along y 104.")
    frame = copy.deepcopy(l1_sketch['frame'])
    sk['frame'] = frame
    terraces = [
        {'polygon': [[78, 30], [87, 30], [87, 38], [78, 38]], 'height': NC_H, 'slope': 3,
         'notes': "Newcastle's rise: the ruin's floor and the gate's apron."},
        {'polygon': [[97, 70], [102, 70], [102, 75], [97, 75]], 'height': 1000, 'slope': 2,
         'notes': "Nightshadow's square."},
        {'polygon': [[84, 40], [91, 40], [91, 46], [84, 46]], 'height': 1020, 'slope': 2,
         'notes': "Ebenezer's camp."},
        {'polygon': [[63, 67], [66, 67], [66, 71], [63, 71]], 'height': 1000, 'slope': 1,
         'notes': "The Tower's islet, level under the tower."},
    ]
    heights = {
        'points': [{'at': [102, 22], 'h': 3450, 'notes': "the Crow's Crown, the map's high point"}],
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(), 'notes': 'Written by gen.py from its height function.'},
        'terraces': terraces,
        'cliffs': [
            {'line': [[0, RIM_Y], [40, RIM_Y], [80, RIM_Y], [128, RIM_Y]], 'drop': 900, 'down': 'right',
             'notes': 'The world rim (drawn west to east, the low side south): land to the stars at 0, as X2 and X5.'},
        ],
        'rough': [
            {'polygon': [[19, 19], [46, 19], [46, 50], [19, 50]], 'amount': 0.6, 'notes': "the Bogwood's hills"},
            {'polygon': [[60, 19], [109, 19], [109, 28], [60, 28]], 'amount': 0.8, 'notes': 'the Crow Hills'},
        ],
    }
    sk['heights'] = heights
    water = {
        'bodies': [
            {'id': 'water:lagoon', 'index': 1, 'kind': 'lake', 'level': LAG, 'polygon': LAGOON_N,
             'notes': "The Lifeforce Lagoon, north half (two bodies round the Tower's islet)."},
            {'id': 'water:lagoon', 'index': 2, 'kind': 'lake', 'level': LAG, 'polygon': LAGOON_S,
             'notes': "The lagoon's south half, Mirabeth's spit left out."},
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': G.RIM_SEA,
             'notes': 'Below the rim: stands for the stars.'},
        ] + [{'id': 'water:pools', 'index': i + 1, 'kind': 'pond', 'level': lvl, 'polygon': poly, 'notes': n}
             for i, (pid, (poly, lvl, n)) in enumerate(PONDS.items())],
        'rivers': [{'id': 'water:river', 'line': RIVER, 'width_cells': 2.5, 'level': RIVER_LVL,
                    'notes': "The Lagoon Water: the lagoon's outflow to the west edge at y 62, on into X5's river."}],
    }
    sk['water'] = water
    roads = [
        {'link': 'link:east_road', 'line': EAST_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:camp_road', 'line': CAMP_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:north_road', 'line': NORTH_ROAD, 'width': 'road', 'surface': 'soil'},
        {'link': 'link:west_road', 'line': WEST_ROAD, 'width': 'road', 'surface': 'soil'},
        {'link': 'link:nightshadow_road', 'line': NS_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:square_street', 'line': SQUARE_ST, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:south_street', 'line': SOUTH_ST, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:quay_lane', 'line': QUAY_LANE, 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:newcastle_stair', 'line': NEWCASTLE_STAIR, 'width': 'lane', 'surface': 'dirt'},
        # the tomb path in three: the fen bridge's deck carries the crossing of the Lagoon Water (A5, fifth session)
        {'link': 'link:tomb_path', 'line': TOMB_PATH[:3], 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:fen_bridge', 'line': TOMB_PATH[2:4], 'width': 'lane', 'surface': 'dirt', 'bridge': True},
        {'link': 'link:tomb_path_s', 'line': TOMB_PATH[3:], 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:tomb_lane', 'line': TOMB_LANE, 'width': 'lane', 'surface': 'dirt'},
    ]
    sk['roads'] = roads
    districts = []
    for d in l1_sketch['districts']:
        d = dict(d)
        if d['space'] == 'town:nightshadow':
            d['plots'] = plots_by_space['town:nightshadow']
            d['notes'] = "A4's x3.yml: 16 doors (4103/4104-4109, 4111-4120); the mirror 4110 on the square."
        elif d['space'] == 'town:ebenezer_camp':
            d['plots'] = plots_by_space['town:ebenezer_camp']
            d['notes'] = "The Camp Shrine 4102; Ebenezer's Tent 4101 is a tent structure (thing:ebenezer_tent)."
        elif d['space'] == 'zone:nightshadow_square':
            d['polygon'] = SQUARE
        districts.append(d)
    sk['districts'] = districts
    # ---------------------------------------------------------------- points
    moved = {
        'entrance:nightshadow_square': ([100, 74], 'n'), 'entrance:newcastle_gate': ([82, 38], 'n'),
        'entrance:xd13_keep': ([85, 34], None), 'entrance:xd24_crypt': ([99, 73], None),
        'entrance:xd08_tomb': ([34, 83], None), 'entrance:camp_fire': ([87, 46], 'n'),
        'entrance:east_road': ([106, 40], 'w'), 'entrance:west_road': ([21, 59], 'e'),
    }
    pts = []
    for p in l1_sketch['points']:
        p = dict(p)
        if p['id'] in moved:
            p['at'], f = moved[p['id']]
            if f:
                p['facing'] = f
        pts.append(p)
    pts += [{'id': 'junction:fen_bridge_n', 'at': [37, 61]}, {'id': 'junction:fen_bridge_s', 'at': [37, 67]},
            {'id': 'poi:food_trees', 'at': [20, 46]}]
    sk['points'] = pts
    # ---------------------------------------------------------------- monsters: the L1 areas
    areas = []
    for pid, slot, count, key, poly, notes in G.AREAS:
        first = G.FIRST_SPOTS.get(pid, [])
        n = count - len(first)
        k = 1
        if n > 0:
            areas.append({'id': pid, 'index': k, 'count': n, 'polygon': poly,
                          'notes': '%s %s: %s' % (key, G.AREA_NAMES[key], notes)})
            k += 1
        for at in first:
            areas.append({'id': pid, 'index': k, 'count': 1, 'circle': {'at': at, 'r': 1},
                          'notes': G.SPOT_NOTES.get(pid, "An arrival's first fight (2,000-6,000 from it).")})
            k += 1
    for qid, kind, poly, notes in G.QUIET:
        if qid == 'water:lagoon':
            continue
        areas.append({'id': qid, 'kind': kind, 'polygon': poly, 'notes': notes})
    areas.append({'id': 'zone:tomb', 'kind': 'keep_clear', 'polygon': [[31, 81], [37, 81], [37, 84], [31, 84]],
                  'notes': "The tomb door's step: no marker within 2 cells of the door (L1)."})
    sk['areas'] = areas
    sk['views'] = l1_sketch['views']
    # ---------------------------------------------------------------- structures
    structures = []
    S = structures.append
    # ---- Nightshadow's square: the coffin, the rhyme, the dials, the sign, the well, the mirror (D-11.3, D-11.4)
    S({'id': 'thing:square_court', 'kind': 'platform', 'at': [99.5, 72.5], 'size': [2560, 2560], 'height': 16,
       'textures': {'top': 't3s2fl', 'wall': 't3s2b1'}, 'title': "Nightshadow's square",
       'notes': 'The paved square: the dial walk along its north side, the coffin west of the street.'})
    # The coffin, two states (D-11.3): closed, a stone sarcophagus whose click gives the two refusals (the dials, then
    # the hour) and runs A3's q-c7.coffin; open (q-c7.coffin_opened 112143), the lid gone and a stair down (a pit
    # hatch with a dark shaft) leading into XD-24 (A7).
    S({'id': 'thing:coffin_closed', 'kind': 'platform', 'at': list(COFFIN), 'size': [512, 1024], 'height': 192,
       'raise': 16, 'textures': {'top': 'cwb', 'wall': 'cnb'}, 'title': "Count Draco's coffin",
       'effects': [{'lua': COFFIN_LUA}],
       'notes': "XD-24's entrance (D-11.3), closed: q-c7.coffin with the two refusals ahead of it."})
    S({'id': 'thing:coffin_open', 'kind': 'hatch', 'form': 'pit', 'at': list(COFFIN), 'size': [512, 1024],
       'height': 208, 'hidden': True, 'textures': {'shell': 'cnb', 'door': '7solid01'},
       'title': "Count Draco's coffin",
       'mouth': {'width': 384, 'height': 896, 'depth': 160},
       # XD-24 installed (A7, 17:41): in to its start at the foot of the coffin stair, facing south (its NOTES)
       'into': {'map': 'xeen_xd24.blv', 'at': [0, 704, 0], 'facing': 1536},
       'notes': "XD-24, open: the stair down to the crypt's start (A7's point)."})
    S(sign('thing:coffin_plinth', (COFFIN[0], COFFIN[1] + 1.2), 'Plinth', hook('q-c7.sign_night'), height=128,
           width=128))
    S(sign('thing:rhyme_board', (COFFIN[0] + 0.75, COFFIN[1]), 'Signboard', hook('q-c7.rhyme'), height=224, width=192,
           notes='Within 400 of the coffin (D-11.3).'))
    S(sign('thing:count_sign', (96.9, 70.1), 'Sign', hook('q-c7.sign_nine'),
           notes="At the dial walk's west entrance."))
    for i, (at, start) in enumerate(zip(DIALS, DIAL_START)):
        k = i + 1
        var = 'x3_dial_%d' % k
        # the source's own question (aaze0029:12-23: "The sundial is set to N.  Turn?"); while all three read 9 the
        # map sets q-c7.dials_set (112142), and clears it when one is turned off 9 (A3's rule)
        check = ('if evt.GetMapVar("x3_dial_1", %d) == 9 and evt.GetMapVar("x3_dial_2", %d) == 9 and '
                 'evt.GetMapVar("x3_dial_3", %d) == 9 then SetQBit(QBit(112142)) else ClearQBit(QBit(112142)) end'
                 % tuple(DIAL_START))
        lua = ('local v = evt.GetMapVar("%s", %d) '
               'if continueStep == 2 then v = v %% 12 + 1 evt.SetMapVar("%s", v) %s '
               'evt.StatusText(tr("The sundial is set to {reading}.", {reading = v})) return end '
               'if continueStep ~= nil then return end '
               'AskChoiceWithAnswerSteps(eventId, 3, tr("The sundial is set to {reading}.  Turn?", {reading = v}), '
               '{{Answer = "Yes", Step = 2}, {Answer = "No", Step = 3}})' % (   # D-72 (A5 s30): Yes/No buttons
                   var, start, var, check))
        S(deco('thing:sundial_%d' % k, 'ped02', at, title='Sundial', effects=[{'lua': lua}]))
    S(sign('thing:dial_plinth_1', (DIALS[0][0], DIALS[0][1] - 0.4), 'Plinth', hook('q-c7.clue_stitch'), height=96,
           width=128))
    S(sign('thing:dial_plinth_2', (DIALS[1][0], DIALS[1][1] - 0.4), 'Plinth', hook('q-c7.clue_cat'), height=96,
           width=128))
    # the town well on its own (D-11.4): A3's q-c7.well text; its magic after q-c7.done (cured of disease and
    # weakness, +10 Personality until the next dawn: the map's well effect)
    w = K.well('thing:town_well', (97.3, 73.6), roofed=True, title='Well')
    w['condition'] = {'qbit': 'nightshadow_liberated'}
    # subtract clears a condition; set would inflict it (A3, eighth session)
    # D-70 Q2: the qbit opens the well; the cure is for every member each time, the +10 Personality once a day for
    # the party (x3_town_well), else the source's water line
    w['effects'] = [{'lua': WELL_SOUND}, {'lua': 'evt.ForPlayer(Players.All)'},
                    {'subtract': {'var': 'DiseasedGreen', 'value': 0}},
                    {'subtract': {'var': 'DiseasedYellow', 'value': 0}},
                    {'subtract': {'var': 'DiseasedRed', 'value': 0}}, {'subtract': {'var': 'Weak', 'value': 0}},
                    {'lua': ('if Xeen.usedToday("x3_town_well") then evt.StatusText(%s) else '
                             'Xeen.markToday("x3_town_well") AddValue(PersonalityBonus, 10) evt.StatusText(%s) end')
                            % (lua_str('The water is cool and refreshing.'),
                               lua_str('The water is clear and cold, and tastes faintly of garlic. You feel '
                                       'healthier, and somehow more likeable. (+10 Personality until you rest)'))}]
    w['else_effects'] = [{'lua': WELL_SOUND},
                         {'text': 'The water is black and tastes of iron. You decide you are not thirsty.'}]
    S(w)
    S({'id': 'thing:nightshadow_mirror', 'kind': 'portal', 'at': [101.9, 72.25], 'radius': 112, 'sides': 12,
       'turn': 90, 'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'Magic Mirror', 'effects': [{'lua': 'Xeen.useMirror(4110, eventId, continueStep)'}],
       'notes': "A4's mirror 4110 (dark until q-c7.done: mirrors.yml's opens and closed text)."})
    # ---- Nightshadow's dressing: dead trees in yards, the churchyard's graves, the sexton's shed
    for i, at in enumerate([(98.2, 64.5), (93.6, 68.6), (104.8, 74.6), (92.2, 77.5), (105.3, 64.0), (93.2, 62.0)]):
        S(deco('thing:ns_tree_%d' % (i + 1), ['tree41', 'tree42', 'tree41'][i % 3], at))
    gr = 0
    for row_y in (81.8, 82.8, 83.8):
        for col_x in (102.6, 103.7, 104.8, 105.9, 107.0):
            if (row_y, col_x) in ((83.8, 102.6),):
                continue
            gr += 1
            S(deco('thing:grave_%d' % gr, 'rock65', (col_x + (0.15 if gr % 3 else -0.1), row_y),
                   title='Grave', effects=[{'text': 'A grave. Fresh flowers on it, and a sharpened stake beside them.'}]
                   if gr in (3, 8) else [{'text': 'A grave, its name scratched out.'}]))
    S(K.shed('thing:sexton_shed', (106.0, 84.6), [1.5, 1], 0, kit='poor', title="The sexton's shed"))
    S({'id': 'thing:sexton_chest', 'kind': 'chest', 'at': [106.75, 85.85], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 2}, 'notes': "The sexton's tools and what the dead left behind."})
    for i, (d, at) in enumerate([('tree42', (101.8, 85.6)), ('tree42', (107.8, 81.2))]):
        S(deco('thing:church_tree_%d' % (i + 1), d, at))
    # ---- Mirabeth's rock off the quay (Q-C12): her actor below; black rocks on the spit
    for i, (d, at) in enumerate([('rock26', (84.7, 80.5)), ('rock12', (84.6, 81.6)), ('rock26', (86.2, 80.2)),
                                 ('7rock08', (86.6, 81.8))]):
        S(deco('thing:mirabeth_rock_%d' % (i + 1), d, at))
    # ---- Ebenezer's camp: the tent (house 4101), the fire, the rain barrel (aaze0012:12-13)
    S({'id': 'thing:ebenezer_tent', 'kind': 'tent', 'at': [87.3, 42.1], 'size': [1024, 768], 'height': 448,
       'open': True, 'house': 4101, 'title': "Ebenezer's Tent",
       'notes': "A4's house 4101 (proposed door building:ebenezer_tent; a tent structure here)."})
    S(deco('thing:camp_fire', 'cmpfyr00', (85.0, 45.3), title='Campfire'))
    S(deco('thing:rain_barrel', 'bigbarel', (86.2, 41.15), title='Rain Barrel',
           effects=[{'text': 'The barrel is empty.'}]))
    S(deco('thing:rain_barrel_pair', 'smlbarel', (86.6, 41.15)))
    for i, (d, at) in enumerate([('bigbarel', (90.1, 46.3)), ('7dec32', (90.1, 45.9)), ('dec24x', (84.6, 45.75))]):
        S(deco('thing:camp_prop_%d' % (i + 1), d, at))
    # ---- Newcastle: the ruin (stage 0), the walls (stage 1, m9.walls), the keep (stage 2, m11.keep)
    nx, ny = NEWCASTLE_AT
    S({'id': 'thing:newcastle_ruin', 'kind': 'building', 'at': [nx, ny], 'size': [8, 6], 'kit': 'castle',
       'door': 'none', 'floor': NC_H, 'title': 'Ruins of Newcastle',
       'ruin': {'height': [160, 512], 'gaps': 0.3, 'thickness': 64, 'seed': 11},
       'parts': [
           {'id': 'north_range', 'at': [128, 128], 'size': [3840, 768], 'wall_height': 704, 'roof': 'none',
            'windows': 'alternate', 'textures': {'wall': 'ch1b1'}},
           {'id': 'west_wall', 'at': [128, 960], 'size': [384, 1856], 'wall_height': 512, 'roof': 'none',
            'windows': 'none', 'textures': {'wall': 'ch1b1'}},
           {'id': 'east_wall', 'at': [3584, 960], 'size': [384, 1856], 'wall_height': 512, 'roof': 'none',
            'windows': 'none', 'textures': {'wall': 'ch1b1'}},
           {'id': 'gate_w', 'shape': 'round', 'at': [1536, 2816], 'radius': 288, 'sides': 10, 'wall_height': 768,
            'roof': 'none', 'windows': 'none', 'textures': {'wall': 'ch1b1'}},
           {'id': 'gate_e', 'shape': 'round', 'at': [2560, 2816], 'radius': 288, 'sides': 10, 'wall_height': 768,
            'roof': 'none', 'windows': 'none', 'textures': {'wall': 'ch1b1'}}],
       'notes': "Stage 0 (m8.site): broken castle stone on the rise; the gate between the two round towers."})
    nc_walls = []
    for k, line in enumerate([[[78.2, 30.2], [78.2, 36.6]], [[87.3, 30.2], [87.3, 36.6]], [[78.2, 30.0], [87.3, 30.0]],
                              [[78.2, 36.75], [81.6, 36.75]], [[83.4, 36.75], [87.3, 36.75]]]):
        wid = 'thing:newcastle_wall_%d' % (k + 1)
        nc_walls.append(wid)
        S({'id': wid, 'kind': 'wall', 'line': line, 'height': 640, 'thickness': 192, 'hidden': True,
           'textures': {'wall': 'ch1b1'}, 'title': 'Walls of Newcastle',
           'notes': "Stage 1 (m9.walls): the new curtain wall, shown when Xeen.stageOf('newcastle') >= 1."})
    S({'id': 'thing:newcastle_keep', 'kind': 'building', 'at': [79.2, 30.7], 'size': [3, 3], 'kit': 'castle',
       'door': 'none', 'floor': NC_H, 'hidden': True, 'title': 'Newcastle Keep',
       'parts': [{'id': 'keep', 'at': [96, 96], 'size': [1344, 1344], 'wall_height': 1408, 'roof': 'flat',
                  'windows': 'alternate', 'parapet': 96, 'textures': {'wall': 'ch1b1'}}],
       'notes': "Stage 2 (m11.keep): the keep, shown when Xeen.stageOf('newcastle') >= 2 (its houses are XD-13's)."})
    # the foundation stair: XD-13 (A7): in with the deed (A3's m8.deed, 111160), a short refusal without it
    S({'id': 'thing:xd13_stair', 'kind': 'hatch', 'form': 'pit', 'at': list(XD13_AT), 'size': [512, 512],
       'floor': NC_H, 'textures': {'shell': 'ch1b1', 'door': '7solid01'},
       'title': 'Stair into the foundations', 'hint': 'Newcastle Keep',
       'condition': {'qbit': 'newcastle_deed'},
       'else_effects': [msg("A board is nailed across the stair: CROWN LAND. FOR SALE. ENQUIRE AT EBENEZER'S TENT.")],
       'into': {'map': 'xeen_xd13.blv', 'at': [0, 320, 0], 'facing': 512},
       'notes': "XD-13 Newcastle Keep (installed, A7): in to its start once the land is the party's (m8.deed)."})
    S({'id': 'thing:newcastle_mirror', 'kind': 'portal', 'at': [81.0, 37.3], 'radius': 112, 'sides': 12,
       'turn': 0, 'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'Magic Mirror', 'effects': [{'lua': 'Xeen.useMirror(4121, eventId, continueStep)'}],
       'notes': "A4's mirror 4121 at the gate (opens on m11.keep: mirrors.yml)."})
    # Emerson's work yard on the rise's west shoulder: dressed stone, timber, a crate pair, the chest
    for i, (d, at) in enumerate([('rock68', (75.6, 38.0)), ('rock68', (76.2, 38.9)), ('dec24x', (77.3, 39.1)),
                                 ('7dec21', (75.7, 39.4)), ('7dec21', (76.1, 39.6)), ('haybale2', (78.2, 37.8))]):
        S(deco('thing:yard_%d' % (i + 1), d, at))
    # the masons' well at the yard's west end (A5, fifth session: town_feel's wells and fountains, 3-8 on a map)
    yw = K.well('thing:yard_well', (74.3, 37.4), title="Masons' Well")
    yw['effects'] = [{'lua': WELL_SOUND}, {'text': "The masons' well. The water is cold and tastes of stone dust."}]
    S(yw)
    S({'id': 'thing:yard_chest', 'kind': 'chest', 'at': [76.9, 38.6], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 2}, 'notes': "Emerson's work yard: the masons' pay chest."})
    # ---- the Tower of High Magic (XD-11, installed) on its islet, the causeway
    S({'id': 'thing:causeway', 'kind': 'bridge', 'line': CAUSEWAY, 'width': 640, 'height': 940, 'thickness': 96,
       'kerb': 96, 'arches': {'count': 8, 'rise': 128, 'form': 'segment', 'pier_width': 192},
       'textures': {'deck': 'cwb', 'side': 'cnb', 'pier': 'cnb'}, 'title': 'The causeway',
       'notes': "The stone causeway from the north shore to the Tower's islet (the signature view's line)."})
    tc = TOWER_C
    S({'id': 'thing:high_magic', 'kind': 'building', 'at': [tc[0] - 2, tc[1] - 2], 'size': [4, 4], 'kit': 'castle',
       'floor': 1000, 'title': 'Tower of High Magic', 'facing': 'n',
       'parts': [
           {'id': 'base', 'shape': 'round', 'at': [1024, 1024], 'radius': TOWER_R, 'sides': 12, 'wall_height': 1152,
            'roof': 'none', 'windows': 'none', 'textures': {'wall': 'hwm2wall', 'door': 'hwm2d'}},
           {'id': 'mid', 'shape': 'round', 'at': [1024, 1024], 'radius': 640, 'sides': 12, 'bottom': 1152,
            'wall_height': 1024, 'roof': 'none', 'windows': 'alternate',
            # texture fit (merge point 16): the castle kit's window is ch1b1 rubble, unlike the white plaster
            # (family_switch 113); the plaster set's framed bay with its round window instead
            'textures': {'wall': 'hwp1bwall', 'window': 'hwp1b1w'}},
           {'id': 'top', 'shape': 'round', 'at': [1024, 1024], 'radius': 512, 'sides': 12, 'bottom': 2176,
            'wall_height': 768, 'roof': 'cone', 'roof_pitch': 70, 'windows': 'all',
            'textures': {'wall': 'hwp1bwall', 'window': 'hwp1b1w', 'roof': 'hwm2rf'}}],
       'door': {'part': 'base', 'wall': '6'},
       'into': {'map': 'xeen_xd11.blv'},
       'condition': {'lua': 'XeenQuests.hook("m13.tower_door")'},
       'notes': 'XD-11 (installed, A8): the door faces north up the causeway; A3 m13.tower_door, the Enchanted Key.'})
    for i, (d, at) in enumerate([('7rock08', (61.6, 67.4)), ('7rock09', (67.6, 70.8)), ('rock26', (61.4, 71.2)),
                                 ('7rock08', (67.3, 67.6))]):
        S(deco('thing:islet_rock_%d' % (i + 1), d, at))
    # ---- the Tomb of a Thousand Terrors (XD-08, A7): the barrow and its door, in with the Stone (m10.tomb_door)
    S({'id': 'thing:tomb', 'kind': 'cave_mouth', 'at': list(TOMB_AT), 'size': [1024, 1024], 'turn': 180,
       'free': True, 'mouth': {'width': 256, 'height': 352, 'depth': 16, 'form': 'door', 'sides': 0, 'rim': 128},
       'textures': {'shell': '7dirttyl', 'door': '7solid01'}, 'roughness': 0.5, 'seed': 5,
       'title': 'Tomb of a Thousand Terrors', 'hint': 'Tomb of a Thousand Terrors',
       'condition': {'lua': 'XeenQuests.hook("m10.tomb_door")'},
       'into': {'map': 'xeen_xd08.blv', 'at': [0, 384, 0], 'facing': 512},
       'notes': "XD-08 (installed, A7): A3's m10.tomb_door (the Stone of a Thousand Terrors) lets the party in."})
    for i, (d, at) in enumerate([('sklplrev', (33.2, 83.1)), ('sklplrev', (34.8, 83.1)), ('7dec20', (32.7, 82.6)),
                                 ('7dec18', (35.4, 82.7))]):
        S(deco('thing:tomb_dress_%d' % (i + 1), d, at))
    for i, at in enumerate([(38.2, 82.3), (39.2, 82.6), (38.6, 83.4), (39.6, 83.6), (38.9, 81.6)]):
        S(deco('thing:sunken_grave_%d' % (i + 1), 'rock65', at, title='Sunken grave',
               effects=[{'text': 'A grave half sunk in the bog. Something has dug at it from below.'}]))
    # ---- the Bogwood: the evil rangers' camp (x3.ranger_camp: "You have come upon an Evil Ranger camp.  Destroy?",
    # aaze0012:3-4), two tents, the fire, the chest
    rx, ry = RANGER_CAMP
    camp_lua = ('if continueStep == 2 then evt.StatusText("You ruin their food, burn their tents, and poison their '
                'water.") XeenQuests.hook("x3.ranger_camp") HideThing("thing:ranger_tent_1") '
                'HideThing("thing:ranger_tent_2") return end '
                'if continueStep ~= nil then return end '
                'if IsQBitSet(QBit(%d)) then evt.StatusText("Only ashes and charred poles are left of the rangers\' '
                'camp.") return end '
                'AskChoiceWithAnswerSteps(eventId, 3, "You have come upon an Evil Ranger camp.  Destroy?", '
                '{{Answer = "Yes", Step = 2}, {Answer = "No", Step = 3}})' % RANGER_QBIT)   # D-72 (A5 s30): buttons
    for k, (dx, dy, turn) in enumerate([(-1.3, -0.8, 0), (1.0, -1.1, 30)]):
        S({'id': 'thing:ranger_tent_%d' % (k + 1), 'kind': 'tent', 'at': [rx + dx, ry + dy], 'size': [768, 640],
           'height': 352, 'open': True, 'turn': turn, 'title': "Evil Ranger camp", 'effects': [{'lua': camp_lua}]})
    S(deco('thing:ranger_fire', 'cmpfyr00', (rx, ry + 0.6), title='Campfire'))
    S({'id': 'thing:ranger_chest', 'kind': 'chest', 'at': [29.3, 33.3], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 3}, 'notes': "The rangers' plunder."})
    S(deco('thing:ranger_bones', 'dec05', (rx - 0.6, ry + 1.5)))
    # ---- chests with a reason, and the places of the wild
    S({'id': 'thing:punt_chest', 'kind': 'chest', 'at': [58.6, 58.2], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 2}, 'notes': 'A sunken punt in the reeds, its locker still shut.'})
    S(deco('thing:punt_hull', 'dec24x', (58.25, 58.65)))   # by its chest: one spot (D-20)
    S({'id': 'thing:coffer_chest', 'kind': 'chest', 'at': [76.5, 54.8], 'title': "Ebenezer's coffer",
       'chest': {'level': 2, 'random_items': 3},
       'notes': "The taxman's lost coffer, dropped in the reeds when the toads came."})
    S({'id': 'thing:eel_hut', 'kind': 'building', 'at': [22.6, 64.8], 'size': [1.5, 1.5], 'kit': 'poor',
       'door': 'none', 'title': "Eel-fisher's hut",
       'parts': [{'id': 'hut', 'at': [96, 96], 'size': [576, 576], 'wall_height': 256, 'roof': 'hip',
                  'roof_pitch': 40, 'textures': {'roof': 'hhp2rf'}}]})
    S({'id': 'thing:eel_chest', 'kind': 'chest', 'at': [24.6, 65.6], 'title': 'Chest',
       'chest': {'level': 1, 'random_items': 2}, 'notes': "The eel-fisher's box, by his hut."})
    S({'id': 'thing:pilgrim_pack', 'kind': 'chest', 'at': [29.3, 80.3], 'title': "Pilgrim's pack",
       'chest': {'level': 2, 'random_items': 2}, 'notes': "A drowned pilgrim's pack on the Gloomwood pool's bank."})
    S({'id': 'thing:wreck', 'kind': 'building', 'at': [75.0, 98.2], 'size': [3, 1.5], 'kit': 'timber', 'turn': 20,
       'door': 'none', 'title': 'Wreck', 'ruin': {'height': [96, 384], 'gaps': 0.35, 'thickness': 48, 'seed': 4},
       'parts': [{'id': 'hull', 'at': [96, 128], 'size': [1344, 512], 'wall_height': 384, 'roof': 'none',
                  'windows': 'none', 'textures': {'wall': 'hhm1b1'}}],
       'notes': 'A boat thrown up on the shore above the rim.'})
    S({'id': 'thing:wreck_chest', 'kind': 'chest', 'at': [78.0, 99.9], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 3}, 'notes': "The wreck's strongbox."})
    S({'id': 'thing:watchtower', 'kind': 'building', 'at': [97, 24.5], 'size': [2, 2], 'kit': 'castle',
       'door': 'none', 'title': 'Fallen watchtower', 'ruin': {'height': [256, 896], 'gaps': 0.35, 'thickness': 48,
                                                            'seed': 9},
       'parts': [{'id': 't', 'shape': 'round', 'at': [512, 512], 'radius': 352, 'sides': 10, 'wall_height': 896,
                  'roof': 'none', 'windows': 'none', 'textures': {'wall': 'ch1b1'}}]})
    S({'id': 'thing:watchtower_chest', 'kind': 'chest', 'at': [99.6, 26.4], 'title': 'Chest',
       'chest': {'level': 2, 'random_items': 2}, 'notes': "The watch's stores, left when the tower fell."})
    # the Lifeforce Spring (+2 Endurance, once per character: a player bit; MAPS X3)
    S({'id': 'thing:lifeforce_spring', 'kind': 'fountain', 'at': list(SPRING), 'title': 'Lifeforce Spring',
       'condition': {'lua': 'not IsPlayerBitSet(PlayerBit(%d))' % SPRING_BIT},
       'effects': [{'lua': 'evt.PlaySoundName("xeen_spring_drink")'},
                   {'add': {'var': 'BaseEndurance', 'value': 2}}, {'lua': 'SetPlayerBit(PlayerBit(%d))' % SPRING_BIT},
                   {'text': '+2 Endurance (permanent)'}],
       'else_effects': [{'lua': WELL_SOUND}, {'text': 'The water is cool and refreshing.'}],
       'notes': 'Once per character (player bit %d, to be registered by A3).' % SPRING_BIT})
    # the Marsh Well (MAPS: "a well of temporary resistance"): +10 to the four elements until the party rests
    mw = K.well('thing:marsh_well', (58.5, 46.5), roofed=True, title='Marsh Well')
    mw.update(daily('thing:marsh_well', [{'lua': WELL_SOUND}, {'add': {'var': 'FireResistanceBonus', 'value': 10}},
                                         {'add': {'var': 'AirResistanceBonus', 'value': 10}},
                                         {'add': {'var': 'WaterResistanceBonus', 'value': 10}},
                                         {'add': {'var': 'EarthResistanceBonus', 'value': 10}},
                                         {'text': '+10 Fire, Air, Water and Earth resistance until you rest'}],
                    [{'lua': WELL_SOUND}, {'text': 'The water is cool and refreshing.'}]))
    S(mw)
    # the garlic shrine by Nightshadow's road
    S({'id': 'thing:garlic_shrine', 'kind': 'building', 'at': [98.3, 53.0], 'size': [1, 1], 'kit': 'stone',
       'title': 'Wayside shrine', 'door': 'none',
       'parts': [{'id': 's', 'at': [96, 96], 'size': [320, 320], 'wall_height': 288, 'posts': 32, 'roof': 'hip',
                  'roof_pitch': 50, 'windows': 'none', 'title': 'Wayside shrine',
                  **daily('thing:garlic_shrine', [{'add': {'var': 'DarkResistanceBonus', 'value': 10}},
                                                  {'text': 'Garlic hangs in strings round the shrine. You each take a '
                                                           'clove: +10 Dark resistance until you rest'}],
                          [{'text': 'The strings are picked bare. More garlic will hang there tomorrow.'}])}]})
    # the swamp food trees (MAPS X3): a meal a day; "You find nothing in the tree" (aaze0029:11) when picked
    # the third in the Bogwood's west closes the 6,000 rule at cells [19-20, 46] (A5, fifth session; D-15)
    for k, at in enumerate([(27.5, 66.0), (95.3, 55.6), (20.5, 46.5)]):
        var = 'food_tree_%d' % (k + 1)
        S(deco('thing:food_tree_%d' % (k + 1), 'tree37', at, title='Tree',
               condition={'not': {'map_var': var}},
               effects=[{'set': {'var': {'map_var': var}, 'value': 1}}, {'add': {'var': 'Food', 'value': 2}},
                        {'text': 'You pick an armful of swamp figs. +2 food'}],
               else_effects=[{'text': 'You find nothing in the tree.'}]))
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [59.5, 30], 'height': 768, 'title': 'Obelisk',
       'effects': hook('obelisks.x3')})     # A3's obelisk hook: the word, its bit and the autonote
    # signposts at the forks
    S({'id': 'thing:sign_cross', 'kind': 'sign', 'at': [94.9, 41.6], 'height': 256,
       'arms': [{'title': 'Rivercity', 'toward': 'e'}, {'title': 'Nightshadow', 'toward': 's'},
                {'title': "Newcastle, Ebenezer's camp", 'toward': 'w'}]})
    S({'id': 'thing:sign_causeway', 'kind': 'sign', 'at': [62.2, 51.2], 'height': 256,
       'arms': [{'title': 'Tower of High Magic', 'toward': 's'}, {'title': 'Castle Burlock', 'toward': 'n'},
                {'title': 'Winterkill', 'toward': 'w'}, {'title': 'Newcastle', 'toward': 'e'}]})
    S({'id': 'thing:sign_fen', 'kind': 'sign', 'at': [35.8, 57.6], 'height': 256,
       'arms': [{'title': 'Winterkill', 'toward': 'w'}, {'title': 'The Gloomwood', 'toward': 's'},
                {'title': 'Lifeforce Lagoon', 'toward': 'e'}]})
    S({'id': 'thing:sign_tomb', 'kind': 'sign', 'at': [34.9, 78.3], 'height': 256,
       'arms': [{'title': 'Tomb', 'toward': 's'}, {'title': 'Drowned Shore', 'toward': 'e'},
                {'title': 'Fen road', 'toward': 'n'}]})
    # the north road's end: a sign that points the way (the edge itself leads to X4, D-11.6)
    S(sign('thing:north_road_end', (50.9, 20.8), 'Sign', [{'text': 'Burlock Savannah: north. Castle Burlock beyond.'}]))
    # the tomb path's timber bridge over the Lagoon Water
    S({'id': 'thing:fen_bridge', 'kind': 'bridge', 'line': [[37, 61.3], [37, 67.2]], 'width': 512, 'rise': 96,
       'kerb': 64, 'textures': {'deck': 'trim11_32'}, 'title': 'Fen bridge'})
    # reeds and posts along the causeway head
    for i, at in enumerate([(63.85, 56.45), (65.15, 56.45)]):
        S(deco('thing:causeway_post_%d' % (i + 1), '7dec12', at))
    sk['structures'] = structures
    # ---------------------------------------------------------------- actors
    actors = []
    for m, at, c, s, g, n in G.ACTORS:
        actors.append({'monster': m, 'at': at, 'count': c, 'spread': s, 'group': 60 + g, 'hostile': True,
                       'notes': n})
    actors.append({'monster': '350', 'npc': 4202, 'at': list(MIRABETH), 'spread': 0, 'group': MIRABETH_GROUP,
                   'notes': "Mirabeth (A4's NPC 4202) on her rock, Q-C12; hidden once q-c12.done (112240)."})
    for i, at in enumerate([(81.0, 34.6), (83.7, 31.9), (79.9, 32.4)]):
        actors.append({'monster': ['359', '362', '368'][i], 'at': list(at), 'spread': 0, 'group': WORKER_GROUP,
                       'notes': "Ebenezer's workmen at the ruin."})
    # Nightshadow's and Ebenezer's camp's people: D-96's villagers (villagers.yml, villagers_spots.yml)
    sk['actors'] = actors + V.sketch_actors('X3')
    sk['relations'] = [{'of': [350, 359, 362, 368], 'toward': 'party', 'relation': 'friendly'}] + V.relations('X3')
    sk['events'] = [
        {'id': 'evt:mirabeth', 'trigger': 'load', 'condition': {'qbit': 'mirabeth_gone'},
         'effects': [{'hide_actors': MIRABETH_GROUP}], 'else_effects': [{'show_actors': MIRABETH_GROUP}],
         'notes': 'q-c12.lagoon_rock: Mirabeth is gone once the elixir is hers (112240).'},
        {'id': 'evt:newcastle_walls', 'trigger': 'load', 'condition': {'lua': 'Xeen.stageOf("newcastle") >= 1'},
         'effects': [{'show': nc_walls}], 'else_effects': [{'hide': nc_walls}],
         'notes': 'm9.walls: the walls stand from stage 1.'},
        {'id': 'evt:newcastle_keep', 'trigger': 'load', 'condition': {'lua': 'Xeen.stageOf("newcastle") >= 2'},
         'effects': [{'show': 'thing:newcastle_keep'}], 'else_effects': [{'hide': 'thing:newcastle_keep'}],
         'notes': 'm11.keep: the keep stands from stage 2.'},
        {'id': 'evt:coffin_state', 'trigger': 'load', 'condition': {'qbit': 'nightshadow_coffin_opened'},
         'effects': [{'hide': 'thing:coffin_closed'}, {'show': 'thing:coffin_open'}],
         'else_effects': [{'show': 'thing:coffin_closed'}, {'hide': 'thing:coffin_open'}],
         'notes': "D-11.3: the coffin's two states (q-c7.coffin_opened)."},
        {'id': 'evt:food_trees', 'trigger': 'daily',
         'effects': [{'set': {'var': {'map_var': 'food_tree_1'}, 'value': 0}},
                     {'set': {'var': {'map_var': 'food_tree_2'}, 'value': 0}},
                     {'set': {'var': {'map_var': 'food_tree_3'}, 'value': 0}}],
         'notes': 'The food trees bear again each day.'},
        {'id': 'evt:ranger_camp_state', 'trigger': 'load', 'condition': {'qbit': RANGER_QBIT},
         'effects': [{'hide': ['thing:ranger_tent_1', 'thing:ranger_tent_2']}],
         'notes': 'x3.ranger_camp: the burnt camp stays burnt.'},
        # D-11.1: Nightshadow's fog lifts and an overcast stays once Count Draco is dead. Neither is saved, so the load
        # event sets them; q-c7.done is set in XD-24 (A3's q-c7.draco), never on this map, so no fade is needed here
        {'id': 'evt:nightshadow_dawn', 'trigger': 'load', 'condition': {'qbit': 'nightshadow_liberated'},
         'effects': [{'lua': 'evt.SetMist(0) evt.SetOutdoorSky("sky15")'}],
         'notes': "D-11.1: after q-c7.done (112141) the mist is gone and the sky overcast (sky15)."},
    ]
    # ---------------------------------------------------------------- scatter and ground
    sk['scatter'] = scatter()
    sk['ground'] = ground()
    plan['sketch'] = {'file': 'sketch.yml', 'grid': 512}
    atmosphere = {
        'format': 0,
        'notes': ("Cloudside's skies by the world's weather. A low swamp mist on the lagoon and the fens everywhere, "
                  "and a thick fog volume over Nightshadow's hollow (the curse). After q-c7.done the sketch's load "
                  "event evt:nightshadow_dawn lifts the whole mist (evt.SetMist(0); the script share is one for all "
                  "layers, devdocs/MIST.md) and sets the overcast sky (evt.SetOutdoorSky(\"sky15\")), D-11.1."),
        'mist': {
            'layer': {'color_rgb': [150, 160, 150], 'base_height': 900, 'falloff_height': 130, 'visibility': 5200,
                      'max_opacity': 0.7, 'noise': 0.45, 'noise_size': 2200, 'drift': [12, 5]},
            'volumes': [{'position': [W(99.5, 72)[0], W(99.5, 72)[1], 1150], 'radius': [6400, 7600, 700],
                         'color_rgb': [138, 144, 150], 'visibility': 1600, 'max_opacity': 0.8, 'noise': 0.35}],
        },
    }
    return project, plan, sk, atmosphere

def scatter():
    out = []
    def sc(sid, d, count, poly=None, clusters=None, line=None, steep=None, circle=None):
        e = {'id': sid, 'decoration': d, 'count': int(count)}
        if poly: e['polygon'] = poly
        if circle: e['circle'] = circle
        if line: e['line'] = line
        if clusters: e['clusters'] = int(clusters)
        if steep: e['steep'] = True
        out.append(e)
    def stand(sid, poly, kinds, per_100, spacing, clusters=None, steep=None, thin=True):
        e = {'id': sid, 'count': int(per_100 * K.poly_area(poly) / 100.0), 'polygon': poly, 'spacing': spacing,
             'spacing_group': 'trees', 'kinds': dict(kinds)}
        if thin:
            e['edge_thin'] = {'width': 3, 'keep': 0.4}
        if clusters: e['clusters'] = clusters
        if steep: e['steep'] = True
        out.append(e)
    # placed kinds without a 3D model swapped for bound kinds of the same use (A5, sixth session): tree43 -> tree41,
    # tree44 and tree45 -> tree42, tree46 -> tree28, rock66 -> rock65, rock67 -> rock68, mushrm06 -> mushrm05
    SWAMP = {'swptree1': 3, 'swptree2': 2, 'swptree3': 2, 'tree41': 1}
    DEAD = {'tree41': 5, 'tree42': 3, 'swptree4': 2}
    GLOOM = {'swptree1': 2, 'swptree2': 2, 'tree42': 2, 'tree28': 1, 'tree41': 2, '7tree22': 1}
    HILL = {'7tree22': 3, '7tree16': 2, 'swptree1': 1}
    MEADOW = {'7tree19': 2, '7tree28': 2, 'swptree2': 1}
    # the Bogwood (north-west): swamp trees in stands, bog bushes, rocks on its hills
    BOG = [[19, 19], [46, 19], [46, 30], [47, 48], [42, 51], [19, 51]]
    stand('scatter:bogwood', BOG, HILL | SWAMP, 11.0, 1.5)
    sc('scatter:bogwood_bushes', 'bush03', 90, BOG, clusters=24)
    sc('scatter:bogwood_rocks', '7rock09', 30, BOG, clusters=10, steep=True)
    sc('scatter:bogwood_plants', 'plant02', 40, BOG, clusters=12)
    # the north vale: open, a few trees along the road
    VALE = [[47, 19], [58, 19], [58, 22], [64, 30], [66, 42], [62, 49], [56, 52], [50, 53], [47, 48]]
    stand('scatter:vale', VALE, MEADOW, 3.0, 2.2)
    sc('scatter:vale_flowers', 'flower04', 24, VALE, clusters=8)
    # the Crow Hills: dark conifers thinning to the crown, rocks on the steep ground
    CROW = [[58, 19], [109, 19], [109, 36], [96, 37], [90, 30], [82, 26], [70, 25], [64, 30], [58, 22]]
    stand('scatter:crow_hills', CROW, HILL, 7.0, 1.8)
    sc('scatter:crow_rocks', '7rock08', 40, CROW, clusters=12, steep=True)
    sc('scatter:crow_rocks', '7rock09', 30, CROW, clusters=10, steep=True)
    # Newcastle's rise: rough grass, a few trees on its shoulders
    RISE = [[66, 30], [70, 26], [78, 27], [78, 39], [74, 42], [66, 42]]
    stand('scatter:rise', RISE, MEADOW, 3.0, 2.0)
    sc('scatter:rise_rocks', 'rock68', 8, [[72, 28], [77, 28], [77, 37], [72, 37]], clusters=4)
    # the east meadow by the X2 road
    EAST = [[93, 37], [109, 37], [109, 50], [102, 51], [94, 50], [93, 47]]
    stand('scatter:east_meadow', EAST, MEADOW, 3.0, 2.2)
    sc('scatter:east_flowers', 'flower04', 20, EAST, clusters=6)
    # the reed shores of the lagoon's north side
    REEDS = [[56, 52], [62, 49], [66, 43], [76, 43], [83, 47], [93, 48], [94, 50], [92, 58], [85, 58], [78, 56],
             [70, 55], [64, 56.5], [58, 59.5], [53, 57]]
    stand('scatter:reed_trees', REEDS, SWAMP, 2.5, 2.0)
    sc('scatter:reeds', 'plant02', 140, REEDS, clusters=30)
    sc('scatter:reeds', 'plant03', 70, REEDS, clusters=18)
    # the Black Fen (west)
    FEN = [[19, 51], [42, 51], [47, 48], [50, 53], [52, 58], [56, 63], [56, 72], [58, 79], [50, 79], [40, 77],
           [19, 77]]
    stand('scatter:fen', FEN, DEAD | {'swptree2': 2}, 6.0, 1.7)
    sc('scatter:fen_reeds', 'plant02', 130, FEN, clusters=30)
    sc('scatter:fen_bushes', 'bush03', 40, FEN, clusters=12)
    sc('scatter:fen_mushrooms', 'mushrm05', 18, FEN, clusters=6)
    # the Gloomwood (south-west): the darkest wood
    GW = [[19, 77], [40, 77], [50, 79], [58, 79], [60, 86], [56, 94], [54, 103], [19, 103]]
    stand('scatter:gloomwood', GW, GLOOM, 14.0, 1.4)
    sc('scatter:gloom_bones', '7dec18', 14, GW, clusters=6)
    sc('scatter:gloom_mushrooms', 'mushrm05', 24, GW, clusters=8)
    sc('scatter:gloom_rocks', '7rock08', 16, GW, clusters=6)
    # the Drowned Shore (south)
    DS = [[54, 103], [56, 94], [60, 86], [62, 84], [68, 87], [75, 88], [82, 86], [87, 84], [94, 85.5], [103, 86.5],
          [109, 82], [109, 103]]
    stand('scatter:drowned_shore', DS, DEAD, 4.0, 2.0)
    sc('scatter:shore_reeds', 'plant02', 70, DS, clusters=18)
    sc('scatter:shore_rocks', '7rock09', 24, DS, clusters=8)
    sc('scatter:lip_rocks', '7rock08', 30, line=[[20, 103.4], [108, 103.4]])
    # the east ridge behind Nightshadow
    ER = [[104, 51], [109, 50], [109, 82], [107, 80], [107, 60], [104, 57]]
    stand('scatter:east_ridge', ER, DEAD, 8.0, 1.6)
    # Mirabeth's spit, the islet's reeds
    sc('scatter:islet_reeds', 'plant02', 16, ISLE, clusters=5)
    # beyond the party's square (to the map's edge; the road and river valleys left open)
    RIM = [
        ('scatter:rim_nw', [[0, 0], [45, 0], [45, 18.5], [0, 18.5]], HILL | SWAMP, 6.0),
        ('scatter:rim_n', [[55, 0], [128, 0], [128, 18.5], [55, 18.5]], HILL, 5.0),
        ('scatter:rim_w', [[0, 18.5], [18.5, 18.5], [18.5, 55], [0, 55]], HILL | SWAMP, 6.0),
        ('scatter:rim_sw', [[0, 66], [18.5, 66], [18.5, 103], [0, 103]], GLOOM, 7.0),
        ('scatter:rim_en', [[109.5, 18.5], [128, 18.5], [128, 35], [109.5, 35]], HILL, 5.0),
        ('scatter:rim_e', [[109.5, 46], [128, 46], [128, 103], [109.5, 103]], DEAD | HILL, 5.0),
    ]
    for sid, poly, kinds, per in RIM:
        stand(sid, poly, kinds, per, 1.6, thin=False)
        n = max(4, int(0.8 * K.poly_area(poly) / 100.0))
        sc(sid.replace('rim', 'rimrock'), '7rock09', n, poly, clusters=max(2, n // 4), steep=True)
    return out

def ground():
    g = [
        {'material': 'grass_patchy', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'damp grass: the lagoon country'},
        {'material': 'swamp', 'polygon': [[19, 51], [56, 51], [56, 79], [19, 79]], 'notes': 'the Black Fen'},
        {'material': 'swamp', 'polygon': [[19, 79], [58, 79], [58, 103], [19, 103]], 'notes': "the Gloomwood's floor"},
        {'material': 'swamp', 'polygon': [[60, 86], [100, 86], [100, 100], [60, 100]], 'notes': 'the Drowned Shore'},
        {'material': 'swamp', 'polygon': [[54, 50], [94, 50], [94, 58], [54, 58]], 'notes': 'the reed shores'},
        {'material': 'grass_meadow', 'polygon': [[93, 37], [128, 37], [128, 50], [93, 50]],
         'notes': 'the meadow by the X2 road'},
        {'material': 'soil', 'polygon': [[86, 14], [116, 14], [116, 28], [86, 28]],
         'notes': "the Crow's Crown"},
        {'material': 'soil', 'polygon': [[78, 30], [87, 30], [87, 38], [78, 38]], 'notes': "Newcastle's courtyard"},
        {'material': 'soil', 'polygon': [[84, 40], [91, 40], [91, 47], [84, 47]], 'notes': "Ebenezer's camp"},
        {'material': 'soil', 'polygon': [[74, 37], [78, 37], [78, 40], [74, 40]], 'notes': "Emerson's work yard"},
        {'material': 'soil', 'polygon': [[25, 32], [31, 32], [31, 37], [25, 37]], 'notes': "the rangers' camp"},
        {'material': 'soil', 'polygon': [[101, 81], [108, 81], [108, 86], [101, 86]], 'notes': 'the churchyard'},
        {'material': 'soil', 'line': GLOOM_PATH, 'width': 1, 'notes': 'the Gloomwood path (a trodden track)'},
        {'material': 'soil', 'line': SHORE_PATH, 'width': 1, 'notes': 'the shore path (a trodden track)'},
        {'material': 'dirt', 'polygon': [[92, 60], [106, 60], [106, 80], [92, 80]],
         'notes': "Nightshadow's sunless yards"},
    ]
    return g

def dump(folder, name, data):
    if name == 'sketch.yml':   # AU's outdoor beds (A5, 2026-11-21; level_generation/projects/xeen/common/beds)
        sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common/beds')
        import beds as _beds
        data = _beds.with_beds(data, 'x3')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name), 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)

def main():
    project, plan, sk, atmosphere = build()
    # F2/F8 (2026-11-21) + F16 (A5 s29, 2026-11-22): wing doors as double doors, mouths as wide as their rim, the
    # entrance window's trans.txt lines
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import house_doors as HD
    import entrance as EN
    for _note in HD.double_doors_sketch(sk) + HD.bury_mouths_sketch(sk) + EN.apply(sk, 'x3'):
        print('door:', _note)
    for level in ('L3', 'L4'):
        out = os.path.join(BRIEFS, level)
        dump(out, 'project.yml', project)
        p = copy.deepcopy(plan)
        p['level'] = level if level == 'L3' else 'L3'
        dump(out, 'plan.yml', p)
        dump(out, 'sketch.yml', sk)
        dump(out, 'atmosphere.yml', atmosphere)
    p2 = copy.deepcopy(plan)
    p2['level'] = 'L2'
    p2.pop('sketch', None)
    dump(os.path.join(BRIEFS, 'L2'), 'project.yml', project)
    dump(os.path.join(BRIEFS, 'L2'), 'plan.yml', p2)
    print('written L2, L3, L4 to', BRIEFS)

if __name__ == '__main__':
    main()
