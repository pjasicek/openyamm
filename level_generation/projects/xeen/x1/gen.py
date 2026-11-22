#!/usr/bin/env python3
"""X1 Vertigo Meadows: writes the L4 project (project.yml, plan.yml, sketch.yml, atmosphere.yml, playtest.yml).

The design is devdocs/xeen/MAPS.md "X1 Vertigo Meadows" (sheet and layout sketch), WORLD_DESIGN.md 5.1 and
QUESTS.md Act I. Every number here is a design value (no original exists). The project files are written by this
script and are its output: edit here and run ../v.sh, never the files.
Coordinates: terrain cells [x, y], x east, y south from the north-west corner; world X = (x - 64) * 512,
Y = (64 - y) * 512.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import os
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml
import yaml

OUT = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/x1/L4'
STEM = 'xeen_x1'

def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))

# ---------------------------------------------------------------------------------------------------------------
# Rebase (A5, 2026-11-20): Xeen families and A3's hooks, named in one place
# ---------------------------------------------------------------------------------------------------------------
# The X1 sheet's five families (MAPS X1, MONSTERS_AND_ITEMS 2). Slots: orcs, toads, skeletons; snakes and zombies
# are placed groups (a map has three slots). The values are the MM7 stand-ins the map is built with until A2's rows
# exist ("Rows for the map lanes" in devdocs/xeen/lanes/A2.md); swapping a value is the whole change.
FAMILY = {
    'orcs': 'Goblin',                  # Orcs 5 / 7 / 10 (Orc, Orc Archer, Orc Guard); MM7 Goblin 271-273
    'toads': 'Dragonfly',              # Toads 5 / 8 / 11 (Giant, Bog, Swamp Toad); MM7 Dragonfly 226-228
    'snakes': 'Dragonfly',             # Serpents 5 / 8 / 12 (Giant Snake, Viper, Constrictor); no MM7 snake
    'skeletons': 'Skeleton Warrior',   # Skeletons 6 / 12 / 16; MM7 Skeleton Warrior 397-399
    'zombies': 'Ghast',                # Rotting dead 8 / 12 / 18 (Zombie, Ghoul, Grave Ghoul); MM7 Ghoul 454-456
}
# The move into the Xeen world (A5 step 2) is one switch: IN_WORLD = True with `world: xeen`, FAMILY set to A2's rows
# and the items to A2's numbers. Until then the map is the MM7 stand-in (`world: mm7`): hooks show their texts by a
# message, doors open MM7 rows. With IN_WORLD every hook calls A3's XeenQuests.hook (events/common/xeen_quests.lua)
# and every door opens A4's house (devdocs/xeen/lanes/A4.md, "House ids for the map lanes").
IN_WORLD = True      # the Xeen world (step 2, 2026-11-20); False rebuilds the MM7 stand-in
# A2's rows (devdocs/xeen/lanes/A2.md, "Rows for the map lanes"): slot names for the spawn slots, row ids for placed
# groups; A2's item ids.
XEEN_SLOT = {'orcs': 'Xeen Orc', 'toads': 'Xeen Toad', 'skeletons': 'Xeen Skeleton'}
XEEN_ROW = {'orcs': 11030, 'snakes': 11480, 'skeletons': 11240, 'zombies': 11250}
XEEN_ITEMS = {'warehouse_key': 12001, 'crystal_key': 12031}
SLOT = XEEN_SLOT if IN_WORLD else FAMILY
# D-1.3 (xeen-o, 2026-11-20): the fuller X1, installed (A5, fifth session; X1_FULLER=0 rebuilds the 133 version).
# About 175 at load: 55 markers of 2-3 at Dif 1 (90/8/2), the new ones in pairs near the wild roads outside the town
# buffer; the level 2-4 band filled by placed pests and bats. A2's map_stats row 9130 carries the slots.
FULLER = IN_WORLD and os.environ.get('X1_FULLER', '1') != '0'
# X7 Mount Firestone (D-40): the north edge opens once X7 is installed (A5, tenth session); X1_X7=0/1 forces it.
_X7_MAP = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/worlds/xeen/maps/xeen_x7.odm')
X7_LIVE = IN_WORLD and (os.environ.get('X1_X7') == '1' or (os.environ.get('X1_X7') != '0' and os.path.exists(_X7_MAP)))
ROAD_CAMPS = {   # pop: [(x, y, markers, radius)], beside the wild roads (within 1,500 of one where the buffers allow)
    'pop:hill_orcs': [(8, 49, 2, 1), (3, 43, 1, 0.5), (46, 24, 2, 1)],                    # west road, mine lane
    'pop:road_orcs': [(66, 5, 2, 1), (73, 3, 1, 0.5), (65, 17, 1, 0.5), (71, 27, 2, 1),
                      (77, 27, 1, 0.5)],                                                   # north road, orc lane
    # D-85 (A5, 2026-11-21): 5,888 from every talking NPC: the toad lane's (68, 72) -> (70, 76) (Orothin 4,650 ->
    # about 6,400), the forest path's (45, 80) pair -> (37, 91) (Derek 1,976 and Celia 1,268 -> over 6,000)
    'pop:toads': [(60, 77, 2, 1), (66, 77, 1, 0.5), (70, 76, 1, 0.5), (86, 74, 2, 1)],      # south road, toad lane
    'pop:dead': [(54, 81, 2, 1), (37, 91, 2, 1), (40, 90, 2, 1)],                        # forest path
} if FULLER else {}
ROAD_PESTS = [   # (row, (x, y), count, spread): M1's pests and the bats, level 2-4 (A2's rows), placed, never refill
    (11340, (53, 72), 3, 1.0),    # doom bugs on the south road below the warehouse yard (D-85: were (56, 69), 4,245 from Orothin)
    (11380, (80, 50), 2, 0.8),    # slimes in the orchard's ditch (the orchard road)
    (11340, (92, 44), 2, 0.8),    # doom bugs at the pyramid knoll's foot (the rim path)
    (11390, (62, 79), 3, 1.0),    # rats by the toad lane
    (11300, (30, 88), 3, 1.0),    # giant bats in the dead wood by the forest path
    (11300, (38, 22), 2, 0.8),    # giant bats over the hills by the mine lane
] if FULLER else []
PLACED = XEEN_ROW if IN_WORLD else FAMILY
ITEMS = XEEN_ITEMS if IN_WORLD else {'warehouse_key': 2176, 'crystal_key': 2110}
XEEN_SOURCE = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/worlds/xeen/source')
QBITS, HOOKS = {}, {}
for _f in sorted(os.listdir(os.path.join(XEEN_SOURCE, 'quests'))) + ['../npcs/x1.yml']:
    _q = yaml.safe_load(open(os.path.join(XEEN_SOURCE, 'quests', _f)))
    _stem = os.path.basename(_f)[:-4]
    for _k, _v in (_q.get('qbits') or {}).items():
        QBITS['%s.%s' % (_stem, _k)] = _v['id']
    for _k, _v in (_q.get('hooks') or {}).items():
        if _v.get('map') == 'X1':
            HOOKS['%s.%s' % (_stem, _k)] = _v
HOOK_QBITS = {'m1.crodo_bottle_creek': QBITS['m1.bottle_creek'], 'm2.done': QBITS['m2.done']}

PM_ORC = [2, 3] if FULLER else [3, 5]
PM_OTHER = [2, 3] if FULLER else [2, 4]

def n_road(pop):
    return sum(n for (_x, _y, n, _r) in ROAD_CAMPS.get(pop, []))

def lua_text(text):
    return 'evt.SimpleMessage("%s")' % text.replace('\\', '\\\\').replace('"', '\\"')

def hook(name, window=False):
    """The effects of A3's hook `name` (a source quest file's hook on X1): in the world its call; on the MM7 stand-in
    its text as a message (`window`: a message window, else the status text)."""
    h = HOOKS[name]
    if IN_WORLD:
        return [{'lua': 'XeenQuests.hook("%s")' % name}]
    text = h.get('text') or (h.get('states') or [{}])[-1].get('text')
    return [{'lua': lua_text(text)}] if window else [{'text': text}]

# A4's house per door (Xeen house ids 4001-4050), by (building id, index); applied with IN_WORLD.
HOUSE_XEEN = {
    ('building:weapon_shop', None): 4001, ('building:armour_shop', None): 4002, ('building:town_hall', None): 4003,
    ('building:magic_shop', None): 4004, ('building:tavern', None): 4005, ('building:bank', None): 4006,
    ('building:inn', None): 4007, ('building:alchemist', None): 4008, ('building:temple', None): 4009,
    ('building:guild_fire', None): 4011, ('building:guild_air', None): 4012, ('building:guild_water', None): 4013,
    ('building:guild_earth', None): 4014, ('building:training', None): 4015, ('building:stables', None): 4016,
    ('building:core_houses', 1): 4018, ('building:core_houses', 2): 4019, ('building:core_houses', 3): 4020,
    ('building:core_houses', 4): 4021, ('building:core_houses', 5): 4022, ('building:core_houses', 6): 4023,
    ('building:core_houses', 7): 4024, ('building:core_houses', 8): 4025, ('building:core_houses', 9): 4026,
    ('building:bank_houses', 1): 4027, ('building:bank_houses', 2): 4028, ('building:bank_houses', 3): 4029,
    ('building:west_houses', 1): 4030, ('building:west_houses', 2): 4031, ('building:west_houses', 3): 4032,
    ('building:east_houses', 1): 4033, ('building:east_houses', 2): 4034, ('building:east_houses', 3): 4035,
    ('building:oslo_hut', None): 4036, ('building:celia_hut', None): 4037, ('building:myra_hut', None): 4038,
    ('building:hamlet_houses', 1): 4039, ('building:valia_cottage', None): 4040, ('building:joes_shop', None): 4041,
}
HOUSE_MIRROR = 4017                 # thing:mirror
CELIA_GROUP = 53                    # actor group celia_at_fire (q-c22.derek_camp)
DEREK_GROUP = 54                    # Derek alone (q-c22.on_darkside hides him once he lives on Darkside)
TEMPLE_AFTER_M2 = 4010              # the temple's door after M2 (hook m2.temple_name)
# NPCs without a house that the map places (A4): Derek at his camp, Orothin by his statues, the Spring Druid at his
# stone, four Plague Cult members in the streets (with IN_WORLD; their topics are A3's).
NPC_ACTORS = [(4046, (41.2, 77.6)), (4047, (63.6, 64.6)), (4048, (27.2, 60.8)), (4049, (53.6, 44.6)),
              (4050, (57.4, 44.4)), (4051, (49.0, 45.4)), (4052, (58.6, 47.6))]

# ---------------------------------------------------------------------------------------------------------------
# Land
# ---------------------------------------------------------------------------------------------------------------
MEADOW = 640       # the meadow floor and Vertigo's streets
RIVER = 576        # Pitchfork Creek's water
RIM_X = 104        # the world rim's cliff edge (east)
RIVER_LINE = [[0, 51], [30, 51], [40, 52], [46, 52], [58, 52], [64, 52], [67, 55], [67, 62]]
# pass four (REVIEW_PASS3 2): the outflow meanders to the rim (was four straight runs, a ruler-straight canal)
OUTFLOW = [[73, 65], [76, 63], [79, 64], [81, 64], [84, 62], [87, 63], [90, 61], [93, 62], [95, 61], [97, 59],
           [100, 61], [103, 60]]
LAKE = [[63, 62], [68, 61], [73, 63], [74, 67], [69, 71], [64, 70], [61, 67]]
ISLES = [(65, 67), (70, 66)]

def dist_to_line(px, py, line):
    best = 1e9
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / float(dx * dx + dy * dy)))
        best = min(best, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    return best

def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def bump(x, y, cx, cy, r, h):
    d = math.hypot(x - cx, y - cy)
    return h * (1 - smooth(d / r)) if d < r else 0.0

CALM = [(44, 31, 5), (62, 29, 5), (82, 30, 5), (30, 96, 5), (88, 85, 7), (84, 46, 6), (74, 34, 3), (46, 70, 3),
        (92, 50, 3), (94, 92, 3), (26, 82, 4), (26, 60, 3), (42, 78, 3), (34, 59, 3), (44, 86, 3), (30, 29, 4),
        (56, 23, 4), (97, 31, 4), (102, 96, 3), (102, 24, 2), (96, 96, 2)]
CALM_BOXES = [(26, 31, 76, 68), (68, 66, 84, 81)]

def roll(x, y):
    """Swells of up to about 1,000 high and 14-22 cells long, faded out in the calm places (town, hamlet, doors, shrines)."""
    if x > 100 or x < 3 or y < 3 or y > 125:
        return 0.0
    w = 1.0
    for (x0, y0, x1, y1) in CALM_BOXES:
        dx = max(x0 - x, 0, x - x1)
        dy = max(y0 - y, 0, y - y1)
        w = min(w, smooth(math.hypot(dx, dy) / 6.0))
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 5.0))
    w = min(w, smooth((100 - x) / 6.0))
    v = (520 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.6 + 1.9) + 340 * math.sin((x + y) / 5.3 + 0.4)
         + 200 * math.sin((x - 1.7 * y) / 2.6))
    v = max(v, -420.0)        # hollows, never below the creek's banks
    return w * v

def height(x, y):
    h = MEADOW
    # The northern hills: up from y 40 to about 2,300 on the crests at y 20; the mines and the orc caves in them.
    h += 1650 * smooth((40 - y) / 20.0)
    h += bump(x, y, 44, 24, 7, 350) + bump(x, y, 82, 22, 8, 450) + bump(x, y, 62, 25, 5, 250) + bump(x, y, 28, 26, 7, 300)
    h += bump(x, y, 98, 28, 7, 300)
    # The east meadow rises gently to the rim (1,024 at the edge), except in the creek's valley.
    rv = dist_to_line(x, y, OUTFLOW)
    if x > 76 and y > 36:
        h += 384 * smooth((x - 76) / 28.0) * smooth((rv - 2) / 6.0)
    # The dead forest in the south-west: a low rise; Toad Meadow: a damp hollow.
    h += bump(x, y, 32, 92, 14, 224)
    h -= bump(x, y, 79, 75, 8, 48)
    # The pyramid knoll east of town and the witch tower's rise.
    h += bump(x, y, 84, 46, 4, 480) + bump(x, y, 88, 84, 4, 256)
    # Banks the dungeon doorways are cut into (mine portal, shaft head, orc mouth, Temple of Yak).
    h += bump(x, y, 44, 29.6, 2.6, 420) + bump(x, y, 82, 28.6, 2.6, 420) + bump(x, y, 62, 27, 2.2, 300)
    # rebase: the Temple of Yak's bank (bump 30.5, 94.5) dropped: the ruined shrine stands in front of the ridge
    # Rolling ground over the wilds (wild land density pass): shipped maps' 8 x 8-cell windows stand 130-560 apart in
    # height (standard deviation, median) where X1's meadow floor stood 45. Long swells, none in the town, the hamlet,
    # at the doorways and places, or near the rim's cliff.
    h += roll(x, y)
    # The creek's valley is the meadow's floor.
    d = min(dist_to_line(x, y, RIVER_LINE), rv)
    if d < 5:
        h = MEADOW + (h - MEADOW) * smooth((d - 1.5) / 3.5)
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
# Buildings and services (MM7 house rows as stand-ins until the Xeen world has its own)
# ---------------------------------------------------------------------------------------------------------------
# The town's plots are in town.py (second pass); the hamlet and the huts in the wild stay here.
from town import CORE as TOWN, SOUTH, SUBURB_W, SUBURB_E
import town as T
import kit_pieces as KIT   # D-94/D-95 (town.py puts tools/xeen on the path)
# D-95 (the user 2026-11-22): the culvert's sunken entrance (tools/xeen/kit_pieces.py). The creek's bank nodes (row
# 54) keep the water's level and the guild lane's end holds node 60, so the ditch's floor is row 55, x 61-62, 224 under
# the bank: the mouth's headwall, the ditch's end face, stands on it looking south, its top (the quay's) 608, 32 over
# the bank; the ramp rises from the arch's foot to the lane at row 56. XD-01's arrival (61, 54.43, z 620) lands on the
# quay over the arch.
CULVERT = KIT.SunkenEntrance('culvert', 61, 62, face_y=55, floor_to=55, ramp_to=56, ground=576, top=608,
                             depth=224, back_to=54.0, revet_to=55.4, texture=T.RUN_TEX,
                             land=lambda i, j: 576 if j <= 54 else 640)
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import house_doors as HD   # F2: double doors from wing pictures
DOOR_NOTES = []
# Residences: MM7 residence rows (Harmondale's and their neighbours') under Vertigo's names
RES_IDS = [1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1121, 1122, 1123, 1126, 1127, 1109, 1128, 1129, 1130,
           1131, 1132, 1124, 1125]
RES_NAMES = ['Gunther House', 'Weaver Residence', 'Pike Residence', 'Thorne House', 'Ashby Residence',
             'Miller House', 'Cobb Residence', 'Bramble House', 'Fenwick Residence', 'Holt House', 'Reed Residence',
             'Tanner House', 'Lark Residence', 'Cooper House', 'Fletcher Residence', 'Wren House',
             'Marsh Residence', 'Hollis House', 'Dunne Residence', "Oslo's Hut", 'Myra the Herbalist']

HAMLET = [
    ('building:myra_hut', 'Myra the Herbalist', 1125, 74, 72, 's', [1, 1], 'poor', 'round_hut', 0, {}),
    ('building:valia_cottage', "Old Valia's Cottage", None, 78, 71, 's', [1.5, 1], 'poor', 'cottage', 0,
     {'valia': True, 'roof': T.THATCH}),
    ('building:hamlet_houses', None, None, 76, 76.5, 'n', [1, 1], 'poor', 'gable_porch', 12, {'index': 1}),
]
WILD = [
    ('building:oslo_hut', "Oslo's Hut", 1124, 34, 59, 'e', [1, 1], 'poor', 'round_hut', 10, {}),
    ('building:celia_hut', "Celia's Hut", 1126, 44, 86, 'n', [1, 1], 'poor', 'cottage', -8, {'roof': T.THATCH}),
]

def door_point(at, facing, fp):
    x, y = at
    f, d = fp
    if facing in ('n', 's'):
        w, dp = f, d
    else:
        w, dp = d, f
    if facing == 's':
        return (x + w / 2.0, y + dp)
    if facing == 'n':
        return (x + w / 2.0, y)
    if facing == 'e':
        return (x + w, y + dp / 2.0)
    return (x, y + dp / 2.0)

res_iter = iter(zip(RES_IDS[:19], RES_NAMES[:19]))
plots_by_space = {}
plan_buildings = {}
house_doors = []          # (title, house, door cell, facing) for the walk
footprints = []           # (building id, index, polygon in cells) for the road check, aprons and gardens
doors_out = []            # (building id, index, door cell, the cell 0.9 out in front, facing after turn)

def add_plot(space, entry, door_to):
    bid, title, house, x, y, facing, fp, kit, kind, turn, extra = entry
    want = facing
    if kind == 'round_hut':
        # a round part's first wall looks south: the hut faces south and is turned to its road
        facing, turn = 's', (T.TURN_OF[want] + turn) % 360
        if turn > 180:
            turn -= 360
    plot = {'building': bid, 'at': [x, y], 'facing': facing, 'kit': kit}
    if extra.get('against'):
        plot['against'] = 'slope'      # pass three: backs onto the upper town's terrace (TOWN_FEEL 8)
    if extra.get('floor'):
        plot['floor'] = extra['floor']
    if turn:
        plot['turn'] = turn
    if door_to:
        plot['door_to'] = door_to
    if 'index' in extra:
        plot['index'] = extra['index']
        if not extra.get('plain'):
            house, title = next(res_iter)
    xeen_house = HOUSE_XEEN.get((bid, plot.get('index')))
    if IN_WORLD and xeen_house:
        # A4's house; Valia's key and lines are her topics (A3); Joe's shop shows the closed sign after M2 (hook
        # m2.out_of_business); the temple is the Slime Temple before M2, the Temple of Vertigo after (m2.temple_name)
        plot['house'] = xeen_house
        plot['title'] = title
        if bid == 'building:joes_shop':
            plot['condition'] = {'not': {'qbit': QBITS['m2.done']}}
            plot['else_effects'] = hook('m2.out_of_business')
        elif bid == 'building:temple':
            plot['condition'] = {'not': {'qbit': QBITS['m2.done']}}
            plot['else_effects'] = [{'lua': 'evt.EnterHouse(%d)' % TEMPLE_AFTER_M2}]
    elif extra.get('valia'):
        plot['title'] = title
        plot['condition'] = {'not': {'map_var': 'valia_key_given'}}
        plot['effects'] = [{'set': {'var': {'map_var': 'valia_key_given'}, 'value': 1}},
                           {'give_item': 'crystal_key'}, {'lua': VALIA_GIVE}]
        plot['else_effects'] = [{'lua': VALIA_AGAIN}]
    elif house:
        plot['house'] = house
        plot['title'] = title
    elif bid == 'building:joes_shop':
        # CHANGES X1-13, hook m2.out_of_business: Joe's line before M2 (his topic in the world), the sign after
        plot['title'] = title
        plot['condition'] = {'not': {'qbit': QBITS['m2.done']}}
        plot['effects'] = [{'lua': lua_text("Joe the Exterminator, behind a counter of traps: \"I've just about got "
                                            "the situation under control.\"")}]
        plot['else_effects'] = hook('m2.out_of_business')
    f, d = fp
    if kind == 'town_hall':
        # the town hall: a hall with a square clock tower over its door
        plot['parts'] = [{'id': 'hall', 'wall_height': 384, 'roof': 'gable', 'roof_pitch': 45},
                         {'id': 'tower', 'at': [f * 512 / 2 - 192, d * 512 - 256], 'size': [384, 384],
                          'wall_height': 896, 'roof': 'hip', 'roof_pitch': 55, 'windows': 'none',
                          'textures': {'roof': '7hhr1rf'}}]
        plot['door'] = {'part': 'tower', 'wall': 's'}
    elif kind == 'temple':
        plot['parts'] = [{'id': 'nave', 'at': [64, 384], 'size': [f * 512 - 128, d * 512 - 448], 'wall_height': 448,
                          'roof': 'gable', 'roof_pitch': 52, 'ridge_along': 'ns',
                          'porches': [{'wall': 'n', 'depth': 160, 'posts': 32, 'height': 288, 'floor': 16}]},
                         {'id': 'spire', 'shape': 'round', 'at': [f * 512 / 2, d * 512 - 232], 'radius': 208,
                          'sides': 8, 'wall_height': 1152, 'roof': 'cone', 'roof_pitch': 74, 'windows': 'none',
                          'textures': {'roof': '7hhr1rf'}}]
        plot['door'] = {'part': 'nave', 'wall': 'n'}
        if extra.get('sign'):
            # A4 2026-11-22: the temple's caduceus over its door (MM7's temples; it was asked for and dropped)
            plot['parts'][0]['signs'] = [{'wall': 'n', 'bay': 0, 'texture': extra['sign'], 'hang': True,
                                          'size': T.sign_size(extra['sign']), 'out': 48, 'bottom': 120}]
    else:
        parts, door = T.shape(kind, facing, fp, kit, sign=extra.get('sign'),
                              roof_tex=extra.get('roof') or (T.ROOFS.get(kit) if kit != 'rich' else None))
        storeys = extra.get('storeys', 1)
        if storeys > 1:
            for p in parts:
                if 'bottom' not in p and p.get('shape') != 'round':
                    p['wall_height'] = 512
        if extra.get('big'):
            for p in parts:
                p['wall_height'] = 384
        plot['parts'] = parts
        plot['door'] = door
    # F2 (2026-11-21): a wing picture (the rich kit's 7hhr1d2) is hung as a double door, never alone
    DOOR_NOTES.extend(HD.double_doors(plot, T.plot_extent(facing, fp)))
    plots_by_space.setdefault(space, []).append(plot)
    pb = plan_buildings.setdefault(space, {})
    if bid not in pb:
        pb[bid] = {'id': bid, 'type': 'house', 'count': 0, 'doors': 1, 'footprint_cells': [], 'service': 'residence'}
    pb[bid]['count'] += 1
    pb[bid]['footprint_cells'].append(fp)
    if house and 'index' not in extra:
        pb[bid]['service'] = title
    poly = T.footprint(x, y, facing, fp, turn)
    footprints.append((bid, plot.get('index'), poly))
    dc = T.door_cell(x, y, want if kind != 'round_hut' else 's', fp, turn if kind != 'round_hut' else turn, 0.0)
    if kind == 'round_hut':
        dc = T.door_cell(x, y, 's', fp, turn, -0.08)
        out = T.door_cell(x, y, 's', fp, turn, 0.9)
    else:
        out = T.door_cell(x, y, facing, fp, turn, 0.9)
    doors_out.append((bid, plot.get('index'), dc, out))
    house_doors.append((plot.get('title'), plot.get('house'), list(dc), facing, bid, plot.get('index')))

VALIA_GIVE = ('evt.SimpleMessage("Old Valia of Toad Meadow takes your hands. \\"The witches of the tower turn our '
              'children into goblins. Take this Crystal Key: it opens the tower door, south-east past the marsh. '
              'Bring back the Alacorn of Falista and the children, and the realm will call you Crusaders.\\" (You '
              'receive the Crystal Key.)")')
VALIA_AGAIN = ('if IsQBitSet(QBit(110047)) then evt.SimpleMessage("Old Valia beams at you. \\"Crusaders! The '
               'children are home and the realm knows your name.\\"") else evt.SimpleMessage("Old Valia: \\"The '
               'Crystal Key opens the Witch Tower, south-east past the marsh. Bring back the Alacorn of Falista, '
               'and the children.\\"") end')

for e in TOWN:
    add_plot('district:vertigo_core', e, 'link:main_street')
for e in SOUTH:
    add_plot('district:vertigo_south', e, 'link:guild_lane')
for e in SUBURB_W:
    add_plot('district:vertigo_outer', e, 'link:west_road')
for e in SUBURB_E:
    add_plot('district:vertigo_east', e, 'link:orchard_road')
# Town density pass (measured against six shipped towns): fourteen more plain homes on the fringe, by the roads
# out of the gates and on the south bank, so the town's footprint coverage and building gaps come into range.
_fringe_n = {}
for e in T.FRINGE:
    sp = T.fringe_space(e)
    bid = 'building:fringe_' + sp.split(':')[1]
    _fringe_n[bid] = _fringe_n.get(bid, 0) + 1
    ex = dict(e[10], index=_fringe_n[bid])
    add_plot(sp, (bid,) + e[1:10] + (ex,), None)
res_iter = iter([(1122, 'Bog House'), (1123, 'Reed Cottage')])
for e in HAMLET:
    add_plot('town:toad_meadow', e, 'link:toad_lane')
for e in WILD:
    add_plot('zone:meadows', e, None)

# ---------------------------------------------------------------------------------------------------------------
# Second pass: the town's small things (wells, stalls, sheds, fences, props) and its ground (dress.py)
# ---------------------------------------------------------------------------------------------------------------
import dress as DR
TOWN_THINGS = [
    T.well('thing:well_northwest', (43.55, 40.4)),
    T.well('thing:well_northeast', (60.7, 40.55), roofed=True),
    T.well('thing:well_south', (50.6, 46.9), roofed=True),
    T.well('thing:well_bank', (51.0, 57.4)),
    T.well('thing:well_farm', (31.7, 43.0)),
    T.stall('thing:stall_1', (55.6, 44.8), 90, roof_tex='hhm2rf'),
    T.stall('thing:stall_2', (55.6, 46.05), 90, kit='plaster', roof_tex='7hhr1rf'),
    T.stall('thing:stall_3', (52.7, 48.0), 90, kit='timber'),
    T.shed('thing:shed_ne', (60.4, 38.95), [1, 0.75], 0, kit='poor', title='Woodshed'),
    T.shed('thing:shed_south', (48.2, 48.2), [1, 0.75], 0, kit='timber', open_=True, title='Cart shed'),
    T.shed('thing:shed_west', (33.6, 38.4), [1.5, 1], 0, kit='timber', roof='gable', title='Barn'),
    # pass six: the east barn (69.3, 38.6) dropped with the fringe homes beyond the stables (town spread)
    T.shed('thing:shed_bank', (44.5, 59.2), [1, 0.75], 0, kit='poor', title='Shed'),
    T.fence('thing:garden_north', [[52.7, 39.2], [54.6, 39.2], [54.6, 40.95], [52.7, 40.95]], closed=True),
    T.fence('thing:garden_south', [[49.8, 47.9], [51.3, 47.9], [51.3, 48.85], [49.8, 48.85]], closed=True),
    T.fence('thing:pen_stables', [[64.4, 48.9], [67.6, 48.9], [67.6, 50.4], [64.4, 50.4]], closed=True),
    T.fence('thing:pen_west', [[37.1, 47.2], [39.6, 47.2], [39.6, 47.9]]),
]
# The user's dressing rule (devdocs/xeen/formats/DRESSING.md, 2026-11-20): barrels in pairs against a wall, nothing
# before a door (tools/dress_check.py). The inn's wood pile moved off its door's front; each lone barrel got its
# partner; the lone barrel in Joe's yard joined the rain barrel, the pair against the warehouse's south wall (the
# rain barrel stood out in the yard). Fifth session (D-14's audit): the town hall's, the alchemist's, the west houses'
# wood pile and the warehouse's pair moved within 240 of their walls. F3 (2026-11-21): the town hall's pair off the
# terrace's south lip to the hall's west wall; the dirt heap off the terrace's east slope.
for i, (deco, at) in enumerate([('bigbarel', (47.27, 40.3)), ('7dec21', (47.27, 39.95)), ('7dec12', (42.85, 44.8)),
                                ('bigbarel', (49.1, 46.0)), ('7dec32', (42.6, 47.6)), ('7dec21', (49.6, 48.4)),
                                ('haybale2', (65.2, 49.6)), ('haybale2', (66.6, 49.3)), ('7dec21', (63.9, 48.3)),
                                ('7dec12', (35.5, 42.8)), ('bigbarel', (62.15, 59.65)), ('7dec32', (63.68, 58.0)),
                                ('7dec21', (58.0, 49.12)), ('7dec11', (60.3, 39.6)),
                                ('smlbarel', (49.1, 46.4)), ('bigbarel', (42.6, 47.95)), ('smlbarel', (49.6, 48.75)),
                                ('smlbarel', (63.9, 48.0)), ('7dec21', (63.68, 58.4)), ('smlbarel', (58.35, 49.12))]):
    TOWN_THINGS.append({'id': 'thing:prop_%d' % (i + 1), 'kind': 'decoration', 'decoration': deco, 'at': list(at)})

def _poly_of(s):
    if s['kind'] == 'building':
        x, y = s['at']; w, h = s['size']
        cx, cy = x + w / 2, y + h / 2
        return [T.rot(px, py, cx, cy, s.get('turn', 0)) for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
    if s['kind'] == 'well':
        x, y = s['at']
        return [(x - 0.3, y - 0.3), (x + 0.3, y - 0.3), (x + 0.3, y + 0.3), (x - 0.3, y + 0.3)]
    if s['kind'] == 'wall':
        pts = s['line'] + ([s['line'][0]] if s.get('closed') else [])
        return [tuple(p) for p in pts] + [tuple(p) for p in reversed(pts)]
    return None
_extra = [p for p in (_poly_of(s) for s in TOWN_THINGS) if p]
for s in TOWN_THINGS:
    p = _poly_of(s)
    if p and s['kind'] != 'wall':
        for line in DR.COBBLE + T.LANES:
            if T.line_hits_poly(line, p, 0.5):
                raise SystemExit('road under ' + s['id'])
town_ground, town_scatter, spur_report = DR.dress(footprints, doors_out, _extra + DR.wall_polys())
for b, ix, d in spur_report:
    print('path to %s%s: %.1f cells' % (b, '#%d' % ix if ix else '', d))

# ---------------------------------------------------------------------------------------------------------------
# Dungeon entrances and points of interest
# ---------------------------------------------------------------------------------------------------------------
ENTRANCES = [
    # id, cell, turn (door looks south when 0), title, map, arrival, facing (game units), condition, locked text
    # In the world the warehouse door and the tower door ask A3's hooks (m2.warehouse_door, m4.tower_door): the key,
    # else the hook's own text (found by A3's playthrough segment 01: the door let the party in without the key). Since
    # A1's merge point 4 HasItem counts a key held on the cursor, so the hooks alone decide (the held-key half is gone).
    ('thing:warehouse_door', (61.08, 58.3), 90, "Joe's Warehouse", 'xeen_xd01.blv', [768, -900, 128], 512,
     {'lua': 'XeenQuests.hook("m2.warehouse_door")'} if IN_WORLD else None, None, 'entrance:xd01_warehouse'),
    ('thing:culvert_grate', (61.0, 53.6), 0, 'Culvert grate', 'xeen_xd01.blv', [4832, 4000, -640], 1024,
     {'qbit': 110012}, 'The culvert grate is barred fast from the inside.', 'entrance:xd01_culvert'),
    ('thing:mine_portal', (44, 31.4), 0, 'Red Dwarf Mines', 'xeen_xd02.blv', [14376, 3392, 0], 1024, None, None,
     'entrance:xd02_portal'),
    ('thing:shaft_head', (62, 28.6), 0, "The Clan King's shaft", 'xeen_xd03.blv', [4288, 7168, 1216], 1024,
     {'qbit': 110031}, None, 'entrance:xd03_shaft'),
    ('thing:witch_tower_door', (88, 82.4), 180, 'Witch Tower', 'xeen_xd04.blv', [0, -2900, 0], 512,
     {'lua': 'XeenQuests.hook("m4.tower_door")'} if IN_WORLD else
     {'any': [{'item': ITEMS['crystal_key']}, {'lua': 'evt.GetHeldItemId() == %d' % ITEMS['crystal_key']}]}, None,
     'entrance:xd04_tower'),
    ('thing:orc_cave_mouth', (82, 30.4), 0, 'Orc Caves', 'xeen_xd05.blv', [0, 448, 0], 512, None, None,
     'entrance:xd05_mouth'),
]
SHAFT_ELSE = ('evt.SimpleMessage("An iron hatch over a shaft, barred from below. Dwarf-work: the Clan King\'s '
              'escape shaft. It can only be opened from the Deep Mine, under the Red Dwarf Mines north-west of '
              'here.")')
TOWER_ELSE = ('evt.SimpleMessage("The tower door is sealed with a lock of green crystal. Old Valia of Toad Meadow, '
              'in the cottage north of the pond, keeps its key.")')

def wall_cell(cell, turn, off):
    """The cell in front of a doorway, `off` cells out (a doorway looks south when not turned; turn clockwise)."""
    a = math.radians(turn)
    # south is +y in cells; turning clockwise seen from above: south -> west at 90
    dx, dy = -math.sin(a), math.cos(a)
    return (cell[0] + dx * off, cell[1] + dy * off)

def build():
    os.makedirs(OUT, exist_ok=True)
    # -------------------------------- project.yml
    project = {
        'format': 0, 'id': STEM, 'name': 'Vertigo Meadows', 'world': 'xeen' if IN_WORLD else 'mm7', 'kind': 'outdoor', 'profile': 'odm',
        'map_code': 'X1', 'units': {'plan_grid': 512}, 'extent': {'terrain_cells': 128},
        'map_stats': {
            'id': 9130, 'encounter_chance': 10, 'treasure_level': 1, 'trap_dice': 1, 'perception_difficulty': 1,
            'refill_days': 672, 'music': 19, 'environment': 'plains', 'lock_difficulty': 0,
            # Cloudside's continent (worlds/xeen continent_settings 6), read by the studio since A1's merge point 3.
            **({'continent': 6} if IN_WORLD else {}),
            'slots': [
                # Rebase (A5, 2026-11-20; CHANGES_FOR_BUILT_MAPS X1-4, MAPS 0 "groups 2-4 (orcs 3-5)"): orcs 3-5,
                # toads 2-4, skeletons 2-4 a marker (pass six had 2-4, 2-4, 2-5). The families are Xeen's (FAMILY
                # below); the monster names are the MM7 stand-ins until A2's rows exist. In the world all three at Dif
                # 0 (A tier only: Orc 5, Giant Toad 5, Skeleton 6): X1's kill XP was 1.23 of its budget with Dif 1
                # (tools/xeen/balance.py, 2026-11-20); the count stays 133.
                {'monster': SLOT['orcs'], 'tier': 0 if IN_WORLD and not FULLER else 1,
                 'per_marker': [2, 3] if FULLER else [3, 5], 'weight': 50},
                {'monster': SLOT['toads'], 'tier': 0 if IN_WORLD and not FULLER else 1,
                 'per_marker': [2, 3] if FULLER else [2, 4], 'weight': 25},
                {'monster': SLOT['skeletons'], 'tier': 0 if IN_WORLD and not FULLER else 1,
                 'per_marker': [2, 3] if FULLER else [2, 4], 'weight': 25},
            ]},
        'neighbours': [
            # 2026-11-15 (the X2 agent, ACT2_BUILD.md): the west road leads to X2 Rivercity (CHANGES X1-1)
            # 2026-11-16 (S8g): the studio writes the arrival words as the game reads them (east arrival "left"), so
            # the way is two-way again and arrives on X2's east side; 3 days, as X2's edge:east says.
            {'id': 'edge:west', 'to': 'xeen_x2.odm', 'kind': 'edge', 'side': 'west', 'days': 3,
             'arrival_side': 'east',
             'approach': 'The west road along the creek to the west edge, at y 46.', 'screened': True,
             'notes': "X2 Rivercity and Lake Darzog, the hub (the river road): arrives at X2's east start."},
            {'id': 'edge:north', 'to': 'xeen_x7.odm' if X7_LIVE else '7out04.odm', 'kind': 'edge', 'side': 'north',
             'days': 5,
             'arrival_side': 'south', 'approach': 'The north road over the hills to the north edge at x 69.',
             'screened': True,
             **({'arrival': [2560, -22016, 1856], 'direction': 90} if X7_LIVE else {}),
             'notes': ("X7 Mount Firestone (installed 21:39, D-40): arrives at X7's entrance:south_road; X7's south "
                       "edge arrives here at entrance:north_road (69, 21)." if X7_LIVE else
                       'X7 (Mount Firestone) in the design. Stand-in until X7 exists: the Tularean Forest (MM7).')},
            {'id': 'stable:rivercity', 'to': 'xeen_x2.odm' if IN_WORLD else '7out03.odm', 'kind': 'stable', 'days': 2,
             'schedule': {'weekdays': ['monday', 'thursday']}, 'service': 'Vertigo Stables',
             'notes': 'Rivercity (X2) in the design; the stable opens The J.V.C Corral (MM7) as its stand-in, '
                      'whose own routes it keeps.'},
            {'id': 'door:xd01', 'to': 'xeen_xd01.blv', 'kind': 'door',
             'arrival_hint': "On Joe's loading dock inside the warehouse doors.",
             'notes': "XD-01 Joe's Warehouse (built). Its own exits still lead to Emerald Island (XD-01's project)."},
            {'id': 'door:xd01_culvert', 'to': 'xeen_xd01.blv', 'kind': 'door',
             'condition': {'qbit': 'culvert_grate_open'},
             'arrival_hint': "On the sill behind the culvert grate, under Joe's cellar."},
            {'id': 'door:xd02', 'to': 'xeen_xd02.blv', 'kind': 'door',
             'arrival_hint': 'Just inside the timbered portal, facing into the mine.'},
            {'id': 'door:xd03', 'to': 'xeen_xd03.blv', 'kind': 'door', 'condition': {'qbit': 'escape_shaft_open'},
             'arrival_hint': "At the head of the Clan King's escape shaft, over the cage."},
            {'id': 'door:xd04', 'to': 'xeen_xd04.blv', 'kind': 'door', 'condition': {'item': 'crystal_key'},
             'arrival_hint': 'Inside the tower door, in the gate hall.'},
            {'id': 'door:xd05', 'to': 'xeen_xd05.blv', 'kind': 'door',
             'arrival_hint': "Inside the skull-hung mouth, facing in."},
            {'id': 'pyramid:castleview', 'to': 'xeen_d1.odm', 'kind': 'pyramid', 'condition': {'qbit': 'm7_sigil'},
             'listed_only': True,
             # m7_sigil is A3's m7.sigil (110100, xeen_quests.lua); the pyramid's click runs Xeen.travelPyramid,
             # which checks it and moves the party to D1 (installed)
             'notes': "D1 Castleview (installed): the pyramid's click (Xeen.travelPyramid('vertigo')) opens on "
                      "A3's m7.sigil (110100) and arrives at D1's pyramid. D1's pyramid arrives on the orchard "
                      "road's end west of the knoll: (8832, 9472, 800) facing west (1024)."},
        ],
        'qbits': {'culvert_grate_open': 110012, 'escape_shaft_open': 110031, 'm4_crusaders': 110047,
                  'war_drums_burned': 110050, 'captive_freed': 110052, 'clan_king_slain': 110030,
                  'joe_invoice_found': 110010, 'm7_sigil': 110100, 'yak_stone': 110101, 'tam_reward': 110102,
                  'gunther_errand': 110103, 'crodo_bottle_creek': HOOK_QBITS['m1.crodo_bottle_creek']},
        'items': dict(ITEMS),
        'rules': {'weather': 'world default', 'home_town': 'Vertigo', 'respawn': 'entrance:party_start',
                  'town_portal_anchor': 'entrance:party_start'},
        'notes': ("X1 Vertigo Meadows, Xeen's starting outdoor map, a new map with no original (devdocs/xeen/MAPS.md). "
                  "Built and played as an MM7 map (world: mm7) until worlds/xeen exists, as XD-01 to XD-05 are. "
                  "Stand-ins: slot 1 Orcs is MM7's Goblin family (Goblin 4), slot 2 Toads the Dragonfly family "
                  "(MM7 has no toad or snake; the placed snakes are Dragonflies too), slot 3 Skeletons the Skeleton "
                  "Warrior family, the placed zombies MM7's Ghoul family (Ghast 9); houses open MM7 house rows under "
                  "Vertigo's names; the Crystal Key is the plain Key 2110 (as XD-04 says). Rebase of 2026-11-20 "
                  "(A5): 130 hostiles in four encounter areas, 12 chests, about 45 points of interest, at most 800 "
                  "decorations (CHANGES_FOR_BUILT_MAPS X1-2 to X1-8). Written by output/studio_cal/x1/tools/gen.py."),
    }
    if IN_WORLD and not X7_LIVE:
        # X7 Mount Firestone is not built: the north edge leads nowhere until it is (A5 lane file, step 2); its way in
        # is dropped too (an arrival without a neighbour became the party start)
        project['neighbours'] = [n for n in project['neighbours'] if n['id'] != 'edge:north']
    # -------------------------------- plan.yml
    spaces = []
    def space(sid, kind, name, purpose, **kw):
        d = {'id': sid, 'kind': kind, 'name': name, 'purpose': purpose}
        d.update(kw)
        if sid in plan_buildings:
            d['buildings'] = list(plan_buildings[sid].values())
        spaces.append(d)
    space('zone:meadows', 'wild', 'Vertigo Meadows',
          'The open green meadow round the town: wells, shrines, camps and ruins, and no monsters (rebase: the '
          'quiet quarters of MONSTERS_AND_ITEMS 3).',
          floor=MEADOW, density='sparse')
    space('district:vertigo_core', 'district', 'Vertigo (walled core)',
          'The start: the square, the shops, the town hall, the tavern, the inn and the temple inside the walls.',
          part_of='town:vertigo', floor=MEADOW, safe=True, keep_clear=['spawns'],
          theme="Harmondale's house kits (MM7 home town), stone town wall.",
          population=[{'id': 'pop:townsfolk', 'actor': 'Peasant', 'groups': 12, 'placed': True, 'hostile': False}])
    space('district:vertigo_south', 'district', 'Vertigo (south bank)',
          "The guild row and Joe's yard across the bridge, between the creek and the meadow.",
          part_of='town:vertigo', floor=MEADOW, safe=True, keep_clear=['spawns'])
    space('district:vertigo_outer', 'district', 'Vertigo (outside the gates)',
          'Training by the west gate, the stables by the east gate, a few houses.', part_of='town:vertigo',
          floor=MEADOW, safe=True, keep_clear=['spawns'])
    space('district:vertigo_east', 'district', 'Vertigo (outside the east gate)',
          'The stables and a few houses by the east gate.', part_of='town:vertigo', floor=MEADOW, safe=True,
          keep_clear=['spawns'])
    space('town:vertigo', 'town', 'Vertigo', 'The start town with full services, on the creek, walled.',
          floor=MEADOW, safe=True)
    space('zone:square', 'zone', 'Vertigo Square', 'Where the party starts: the money tree and the fountain.',
          part_of='district:vertigo_core', floor=MEADOW, empty=True, safe=True)
    space('zone:north_hills', 'wild', 'The northern hills',
          'The Red Dwarf Mines, the orc caves, the Clan King\'s shaft head and two orc outposts.',
          floor=[1200, 2400], relief='uneven', density='sparse',
          population=[
              {'id': 'pop:hill_orcs', 'slot': 1, 'groups': 7 + n_road('pop:hill_orcs'), 'per_marker': PM_ORC, 'levels': [5, 10],
               'notes': "Encounter area 1, the northern hills' orc country (west): the west road's camp, the first "
                        'outpost, the mine (rebase, CHANGES X1-4).'},
              {'id': 'pop:road_orcs', 'slot': 1, 'groups': 9 + n_road('pop:road_orcs'), 'per_marker': PM_ORC, 'levels': [5, 10],
               'notes': "Encounter area 2, the orc outposts' road: the north road's camp, the shaft head, the orc "
                        "caves, the hill cache and the east outpost."},
              {'id': 'pop:outpost_orcs', 'actor': FAMILY['orcs'], 'groups': 3, 'placed': True, 'hostile': True,
               'notes': 'Four orcs at each outpost (to burn in phase 1; XD-05\'s drums stop them refilling).'},
              {'id': 'pop:orc_scout', 'actor': FAMILY['orcs'], 'groups': 1, 'placed': True, 'hostile': True,
               'notes': 'A lone orc scout on the hill path.'}])
    space('zone:orchard', 'zone', 'The orchard road',
          'The signature view: the orchard road east of Vertigo ending at the rim, the stars below.',
          floor=[700, 1024], density='sparse', safe=True, keep_clear=['spawns'])
    space('zone:pyramid_knoll', 'zone', 'Pyramid knoll', 'The travel pyramid to Castleview (sealed until M7).',
          floor=1100)
    space('zone:rim', 'wild', 'The world rim', 'The white cliffs where the world ends, the water far below.',
          floor=0, empty=True)
    space('town:toad_meadow', 'town', 'Toad Meadow', "The hamlet: Myra the Herbalist and Old Valia's cottage.",
          floor=600, safe=True, keep_clear=['spawns'])
    space('zone:toad_marsh', 'wild', 'Toad Meadow marsh',
          'Wet ground round the hamlet and the witch rise; the Witch Tower beyond.', floor=600, density='medium',
          population=[{'id': 'pop:toads', 'slot': 2, 'groups': 8 + n_road('pop:toads'), 'per_marker': PM_OTHER, 'levels': [5, 11],
                       'notes': 'Encounter area 3, Toad Meadow: giant toads (Dragonflies as stand-ins).'},
                      {'id': 'pop:marsh_snakes', 'actor': FAMILY['snakes'], 'groups': 2, 'placed': True,
                       'hostile': True, 'notes': 'Snakes by the outflow and in the south marsh (Serpents 5-12; '
                                                 'placed: the map has three slots).'}])
    space('zone:witch_rise', 'zone', 'The witch rise', 'The Witch Tower, visible from town.', floor=900)
    space('zone:dead_forest', 'wild', 'Forest of the Walking Dead',
          "The dead wood in the south-west: skeletons and zombies, Celia's hut, the ruined shrine where the Temple "
          "of Yak's door was.", floor=[700, 900], density='dense',
          population=[{'id': 'pop:dead', 'slot': 3, 'groups': 7 + n_road('pop:dead'), 'per_marker': PM_OTHER, 'levels': [6, 16],
                       'notes': 'Encounter area 4, the dead forest: skeletons.'},
                      {'id': 'pop:zombies', 'actor': FAMILY['zombies'], 'groups': 2, 'placed': True, 'hostile': True,
                       'notes': 'Zombies round the ruined shrine (Rotting dead 8-18; placed).'},
                      {'id': 'pop:lone_skeleton', 'actor': FAMILY['skeletons'], 'groups': 1, 'placed': True,
                       'hostile': True, 'notes': 'A lone skeleton among the dead trees.'}])
    space('water:creek', 'water', 'Pitchfork Creek', 'The creek through Vertigo to the delta and over the rim.')
    space('water:delta', 'water', 'The delta pond', "Orothin's isles with their statues.")
    space('water:sky', 'water', 'Below the rim', 'Stand-in for the stars below the world rim: water far below.')
    for sid in ('junction:west_gate', 'junction:north_gate', 'junction:east_gate', 'junction:south_gate',
                'junction:hill_fork', 'junction:south_fork'):
        space(sid, 'junction', sid.split(':')[1].replace('_', ' ').title(), 'A road junction.',
              part_of='zone:meadows', signpost=sid in ('junction:hill_fork', 'junction:south_fork'))
    space('edge:west_end', 'road', 'West edge', 'Where the west road leaves for X3.', part_of='zone:meadows')
    space('edge:north_end', 'road', 'North edge', 'Where the north road leaves for X7.', part_of='zone:north_hills')
    for sid in ('zone:mine_head', 'zone:orc_mouth', 'zone:shaft_head', 'zone:yak_glade'):
        space(sid, 'zone', sid.split(':')[1].replace('_', ' ').title(), 'A dungeon entrance.',
              part_of='zone:north_hills' if sid != 'zone:yak_glade' else 'zone:dead_forest')
    space('zone:warehouse_yard', 'zone', "Joe's yard", "Joe's warehouse door and the rain barrel.",
          part_of='district:vertigo_south')

    links = [
        {'id': 'link:main_street', 'from': 'junction:west_gate', 'to': 'junction:east_gate', 'kind': 'road'},
        {'id': 'link:north_street', 'from': 'zone:square', 'to': 'junction:north_gate', 'kind': 'road'},
        {'id': 'link:smith_lane', 'from': 'link:main_street', 'to': 'district:vertigo_core', 'kind': 'road',
         'notes': 'Pass three: the lane behind the ironworks up to the upper town, cobbled.'},
        {'id': 'link:bank_lane', 'from': 'link:main_street', 'to': 'district:vertigo_core', 'kind': 'road',
         'notes': 'Pass three: the lane by the bank up to the upper town, cobbled.'},
        {'id': 'link:inn_lane', 'from': 'link:main_street', 'to': 'district:vertigo_core', 'kind': 'road',
         'notes': 'Pass three: the lane by the inn to the homes by the south wall, cobbled.'},
        {'id': 'link:south_street', 'from': 'zone:square', 'to': 'junction:south_gate', 'kind': 'road'},
        {'id': 'link:town_bridge', 'from': 'junction:south_gate', 'to': 'district:vertigo_south', 'kind': 'bridge',
         'crosses': ['water:creek']},
        {'id': 'link:guild_lane', 'from': 'district:vertigo_south', 'to': 'zone:warehouse_yard', 'kind': 'road'},
        {'id': 'link:west_road', 'from': 'junction:west_gate', 'to': 'edge:west_end', 'kind': 'road'},
        {'id': 'link:north_road', 'from': 'junction:north_gate', 'to': 'edge:north_end', 'kind': 'road'},
        {'id': 'link:mine_lane', 'from': 'junction:hill_fork', 'to': 'zone:mine_head', 'kind': 'path'},
        {'id': 'link:orc_lane', 'from': 'junction:hill_fork', 'to': 'zone:orc_mouth', 'kind': 'path'},
        {'id': 'link:orchard_road', 'from': 'junction:east_gate', 'to': 'zone:pyramid_knoll', 'kind': 'road'},
        {'id': 'link:rim_path', 'from': 'zone:pyramid_knoll', 'to': 'zone:rim', 'kind': 'path'},
        {'id': 'link:south_road', 'from': 'district:vertigo_south', 'to': 'junction:south_fork', 'kind': 'road'},
        {'id': 'link:toad_lane', 'from': 'junction:south_fork', 'to': 'town:toad_meadow', 'kind': 'road'},
        {'id': 'link:tower_path', 'from': 'town:toad_meadow', 'to': 'zone:witch_rise', 'kind': 'path'},
        {'id': 'link:forest_path', 'from': 'junction:south_fork', 'to': 'zone:yak_glade', 'kind': 'path'},
    ]
    entrances = [
        {'id': 'entrance:party_start', 'space': 'zone:square', 'kind': 'arrival', 'how': 'The new game start.'},
        {'id': 'entrance:west_road', 'space': 'edge:west_end', 'kind': 'both', 'neighbour': 'edge:west'},
        {'id': 'entrance:north_road', 'space': 'edge:north_end', 'kind': 'both', 'neighbour': 'edge:north'},
        {'id': 'entrance:stable_yard', 'space': 'district:vertigo_outer', 'kind': 'arrival',
         'neighbour': 'stable:rivercity'},
        {'id': 'entrance:xd01_warehouse', 'space': 'zone:warehouse_yard', 'kind': 'both', 'neighbour': 'door:xd01'},
        {'id': 'entrance:xd01_culvert', 'space': 'district:vertigo_south', 'kind': 'both',
         'neighbour': 'door:xd01_culvert', 'condition': {'qbit': 'culvert_grate_open'}},
        {'id': 'entrance:xd02_portal', 'space': 'zone:mine_head', 'kind': 'both', 'neighbour': 'door:xd02'},
        {'id': 'entrance:xd03_shaft', 'space': 'zone:shaft_head', 'kind': 'both', 'neighbour': 'door:xd03',
         'condition': {'qbit': 'escape_shaft_open'}},
        {'id': 'entrance:xd04_tower', 'space': 'zone:witch_rise', 'kind': 'both', 'neighbour': 'door:xd04',
         'condition': {'item': 'crystal_key'}},
        {'id': 'entrance:xd05_mouth', 'space': 'zone:orc_mouth', 'kind': 'both', 'neighbour': 'door:xd05'},
        {'id': 'entrance:pyramid', 'space': 'zone:pyramid_knoll', 'kind': 'exit', 'neighbour': 'pyramid:castleview',
         'condition': {'qbit': 'm7_sigil'}},
    ]
    pois = [
        {'id': 'poi:obelisk', 'space': 'zone:north_hills', 'kind': 'obelisk',
         'behaviour': 'One word of the Cloudside obelisk riddle (an autonote stand-in: a message).'},
        {'id': 'poi:fountain_ability', 'space': 'zone:meadows', 'kind': 'fountain',
         'behaviour': '+2 Luck, permanent, once per character (here: once per party, a map variable).'},
        {'id': 'poi:waters_of_power', 'space': 'zone:orchard', 'kind': 'well',
         'behaviour': 'Temporary hit points (+25 HP).'},
        {'id': 'poi:wishing_well', 'space': 'zone:toad_marsh', 'kind': 'well',
         'behaviour': 'Throw a coin: 1 gold for a wish; a small chance of a small gift.'},
        {'id': 'poi:shrine_poison', 'space': 'zone:dead_forest', 'kind': 'shrine',
         'behaviour': '+5 Body resistance, permanent, once.'},
        {'id': 'poi:money_tree', 'space': 'zone:square', 'kind': 'tree', 'behaviour': 'Shake it once: 50 gold.'},
        {'id': 'poi:rain_barrel', 'space': 'zone:warehouse_yard', 'kind': 'barrel',
         'behaviour': "Joe's warehouse key lies under it (M2), once."},
        {'id': 'poi:water_reflector', 'space': 'zone:rim', 'kind': 'story_device',
         'behaviour': 'The Water Reflector (M37): a dark mirror that says it waits for a later day.'},
        {'id': 'poi:gunther_notice', 'space': 'zone:square', 'kind': 'sign',
         'behaviour': "Mayor Gunther's notice: the pest errand (M1) and Joe's warehouse (M2)."},
        {'id': 'poi:orc_outposts', 'space': 'zone:north_hills', 'kind': 'camp', 'count': 3,
         'behaviour': 'Orc camps with a fire, a crate and three orcs each.'},
        {'id': 'poi:orothin_statues', 'space': 'water:delta', 'kind': 'statue', 'count': 2,
         'behaviour': "Orothin's statues on the isles: a readable line each."},
        {'id': 'poi:druid_grove', 'space': 'zone:meadows', 'kind': 'grove',
         'behaviour': "The Spring Druid's ring of stones: a word of advice (message)."},
        {'id': 'poi:derek_camp', 'space': 'zone:dead_forest', 'kind': 'camp',
         'behaviour': "Derek's camp: a fire and a crate."},
        {'id': 'poi:signs', 'space': 'zone:meadows', 'kind': 'sign', 'count': 3, 'behaviour': 'Signposts at forks.'},
    ]
    landmarks = [
        {'id': 'landmark:witch_tower', 'space': 'zone:witch_rise', 'what': 'The crooked Witch Tower',
         'seen_from': ['zone:square', 'zone:orchard']},
        {'id': 'landmark:temple_spire', 'space': 'district:vertigo_core', 'what': "The temple's spire over the walls"},
        {'id': 'landmark:pyramid', 'space': 'zone:pyramid_knoll', 'what': 'The travel pyramid on its knoll'},
        {'id': 'landmark:rim', 'space': 'zone:rim', 'what': 'The white cliffs of the world rim'},
    ]
    plan = {
        'format': 0, 'level': 'L3',
        'pitch': ("Start pocket. A walled river town in green meadows; the east edge is the world rim, where the "
                  "creek falls off the world. The Witch Tower is visible from town from day one. Orcs hold the "
                  "northern hills round the dwarves' mines and their own caves; toads and snakes the marsh of "
                  "Toad Meadow; the dead walk in the south-west forest."),
        'purpose': 'The first map: full services, five Act I dungeons, d1 fights, wells and shrines.',
        'mood': 'Bright, green and homely; a hint of menace in the hills, the marsh and the dead wood.',
        'datum': 'water:sky',
        'spaces': [s for s in spaces if s],
        'links': links, 'entrances': entrances, 'points_of_interest': pois, 'landmarks': landmarks,
        'height_bands': [
            {'id': 'band:meadow', 'range': [560, 1100],
             'spaces': ['zone:meadows', 'town:vertigo', 'zone:orchard', 'town:toad_meadow']},
            {'id': 'band:hills', 'range': [1100, 2600], 'spaces': ['zone:north_hills']},
            {'id': 'band:below_rim', 'range': [0, 64], 'spaces': ['zone:rim']},
        ],
        'atmosphere': 'Fair sky, light rain by the world chances; MM7 home-town music (19) as a stand-in.',
        'sketch': {'file': 'sketch.yml', 'grid': 512},
        'notes': 'Written by output/studio_cal/x1/tools/gen.py from MAPS.md X1.',
    }
    # -------------------------------- sketch.yml
    rim = [
        {'side': 'north', 'form': 'ridge', 'height': [2200, 3400], 'floor': 2000, 'crest': 10, 'roughness': 100},
        {'side': 'west', 'span': [0, 42], 'form': 'ridge', 'height': [1800, 3000], 'floor': 1200, 'crest': 10,
         'roughness': 100},
        {'side': 'west', 'span': [42, 58], 'form': 'level', 'height': 640, 'meet': 6,
         'notes': 'The west road and the creek run out to the edge (to X3).'},
        {'side': 'west', 'span': [58, 128], 'form': 'ridge', 'height': [1600, 2800], 'floor': 900, 'crest': 10,
         'roughness': 100},
        {'side': 'south', 'form': 'ridge', 'height': [1600, 2800], 'floor': 900, 'crest': 10, 'roughness': 100},
        {'side': 'east', 'form': 'level', 'height': 0, 'meet': 1,
         'notes': 'The world rim: the land ends in a cliff at x 104; below it, water at 0 stands for the stars.'},
    ]
    heights = {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(),
                 'notes': 'Written by gen.py from its height function (design values).'},
        'nodes': [CULVERT.nodes()],      # D-95: the culvert's ditch (after the land words: the creek's banks)
        'points': [
            {'at': [84, 46], 'h': 1120, 'notes': 'pyramid knoll'},
            {'at': [88, 84], 'h': 900, 'notes': 'witch rise'},
            {'at': [65, 67], 'h': 704, 'notes': "Orothin's west isle"},
            {'at': [70, 66], 'h': 704, 'notes': "Orothin's east isle"},
        ],
        'terraces': [
            {'polygon': T.UPPER, 'height': T.UPPER_H, 'slope': T.UPPER_SLOPE,
             'ramps': [{'line': [[51, 43], [51, 41], [51, 40], [52, 39], [52, 38.5]],
                        'height': [640, T.UPPER_H, T.UPPER_H, T.UPPER_H, T.UPPER_H],
                        'width': 1, 'notes': 'the north street climbs to the upper town'}],
             'notes': ('Pass four: the upper town, 512 over the main street, a step at its front held by a '
                       'retaining wall; the north row of shops stands in front of the wall; the north street climbs '
                       'on a ramp, two lanes and the town hall by flights of steps.')},
        ],
        'ridges': [
            {'line': [[27, 94], [33, 94]], 'height': 1664, 'width': 2, 'slope': 2,
             'notes': "Pass three: the rise the Temple of Yak's mouth is built into (crest 1600)."},
            {'line': [[41, 29.5], [47, 29.5]], 'height': 1700, 'width': 2, 'slope': 2,
             'notes': "Pass four: the hillside the Red Dwarf Mines' mouth is cut into (crest 1600): its shoulders "
                      'stand over the shell, which stood as a mound on a gentle slope.'},
            {'line': [[79, 28.5], [85, 28.5]], 'height': 1880, 'width': 2, 'slope': 2,
             'notes': "Pass four: the hillside the orc caves' mouth is cut into (crest 1824)."},
        ],
        'cliffs': [
            {'line': [[RIM_X, 19], [RIM_X, 58], [RIM_X, 62], [RIM_X, 110]], 'drop': 900, 'down': 'left',
             'notes': 'The world rim: white cliffs (drawn from north to south, the low side east).'},
        ],
    }
    # the cliff runs north to south; walking it from its first point the low side (east) is on the left.
    water = {
        'rivers': [
            {'id': 'water:creek', 'line': RIVER_LINE, 'width_cells': 3, 'level': RIVER,
             'notes': 'Pitchfork Creek from the west edge through Vertigo into the delta pond.'},
            {'id': 'water:creek', 'line': OUTFLOW, 'width_cells': 2, 'level': RIVER,
             'notes': 'The outflow east to the rim, where it falls off the world.'},
        ],
        'bodies': [
            {'id': 'water:delta', 'kind': 'pond', 'level': RIVER, 'polygon': LAKE},
            {'id': 'water:sky', 'kind': 'sea', 'level': 0,
             'polygon': [[RIM_X + 1, 0], [128, 0], [128, 128], [RIM_X + 1, 128]],
             'notes': 'Below the rim: stands for the stars (gap: the game draws no void).'},
        ],
    }
    roads = [
        {'link': 'link:main_street', 'line': T.MAIN, 'width': 'road', 'surface': 'road_pebbles',
         'notes': 'Bends twice between the gates; straight runs and 45-degree steps only (second pass).'},
        {'link': 'link:north_street', 'line': T.NORTH_ST, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:smith_lane', 'line': T.SMITH_LANE, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:bank_lane', 'line': T.BANK_LANE, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:inn_lane', 'line': T.INN_LANE, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:south_street', 'line': T.SOUTH_ST, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:guild_lane', 'line': T.GUILD_LANE, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:west_road', 'line': T.WEST_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:north_road', 'line': T.NORTH_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:mine_lane', 'line': [[60, 32], [52, 33], [44, 32.5]], 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:orc_lane', 'line': [[60, 32], [66, 31], [74, 31], [82, 31.5]], 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:orchard_road', 'line': T.ORCHARD_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:rim_path', 'line': [[87, 46], [96, 47], [103, 47]], 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:south_road', 'line': T.SOUTH_ROAD, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:toad_lane', 'line': T.TOAD_LANE, 'width': 'road', 'surface': 'road_pebbles'},
        {'link': 'link:tower_path', 'line': [[80, 74.5], [86, 79], [88, 81.5]], 'width': 'lane', 'surface': 'dirt'},
        {'link': 'link:forest_path', 'line': [[62, 73], [52, 78], [42, 84], [34, 92], [34.5, 97.5], [32.5, 97.5]], 'width': 'lane',
         'surface': 'dirt'},
    ]
    districts = [
        {'space': 'zone:meadows', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]], 'rest': True,
         'plots': plots_by_space['zone:meadows']},
        {'space': 'town:vertigo', 'polygon': [[31, 37], [71, 37], [71, 62], [31, 62]]},
        {'space': 'district:vertigo_core', 'polygon': [[42, 38], [62, 38], [62, 50], [42, 50]],
         'plots': plots_by_space['district:vertigo_core']},
        {'space': 'district:vertigo_south', 'polygon': [[42, 53], [63, 53], [63, 62], [42, 62]],
         'plots': plots_by_space['district:vertigo_south']},
        {'space': 'district:vertigo_outer', 'polygon': [[31, 38], [41, 38], [41, 50], [31, 50]],
         'plots': plots_by_space['district:vertigo_outer']},
        {'space': 'district:vertigo_east', 'polygon': [[63, 38], [71, 38], [71, 50], [63, 50]],
         'plots': plots_by_space['district:vertigo_east']},
        {'space': 'zone:square', 'polygon': [[53, 45], [57, 45], [57, 49], [53, 49]]},
        {'space': 'zone:north_hills', 'polygon': [[19, 19], [109, 19], [109, 36], [19, 36]]},
        {'space': 'zone:orchard', 'polygon': [[70, 40], [104, 40], [104, 52], [70, 52]]},
        {'space': 'zone:pyramid_knoll', 'polygon': [[81, 43], [87, 43], [87, 49], [81, 49]]},
        {'space': 'zone:rim', 'polygon': [[104, 0], [128, 0], [128, 128], [104, 128]]},
        {'space': 'town:toad_meadow', 'polygon': [[72, 69], [82, 69], [82, 79], [72, 79]],
         'plots': plots_by_space['town:toad_meadow']},
        {'space': 'zone:toad_marsh', 'polygon': [[66, 66], [100, 66], [100, 98], [66, 98]]},
        {'space': 'zone:witch_rise', 'polygon': [[84, 80], [93, 80], [93, 90], [84, 90]]},
        {'space': 'zone:dead_forest', 'polygon': [[19, 74], [50, 74], [50, 109], [19, 109]]},
        {'space': 'zone:warehouse_yard', 'polygon': [[59, 57], [63, 57], [63, 61], [59, 61]]},
    ]
    points = [
        {'id': 'entrance:party_start', 'at': [54, 47], 'facing': 'n'},
        {'id': 'entrance:west_road', 'at': [21, 46], 'facing': 'e'},
        {'id': 'entrance:north_road', 'at': [69, 21], 'facing': 's'},
        {'id': 'entrance:stable_yard', 'at': [65, 45], 'facing': 'w'},
        {'id': 'entrance:xd01_warehouse', 'at': [61, 58]},
        {'id': 'entrance:xd01_culvert', 'at': [61, 54]},
        # A5 s18 (merge point 25): the cave-mouth arrivals off their mounds (lifted +188/+148), 512 in front of the
        # footprint's front edge on the open ground, facing out of the dungeon (south)
        {'id': 'entrance:xd02_portal', 'at': [44, 33], 'facing': 's'},
        {'id': 'entrance:xd03_shaft', 'at': [62, 29]},
        {'id': 'entrance:xd04_tower', 'at': [88, 81]},
        {'id': 'entrance:xd05_mouth', 'at': [82, 32], 'facing': 's'},
        {'id': 'entrance:pyramid', 'at': [84, 46]},
        {'id': 'poi:obelisk', 'at': [74, 34]},
        {'id': 'poi:fountain_ability', 'at': [46, 70]},
        {'id': 'poi:waters_of_power', 'at': [92, 50]},
        {'id': 'poi:wishing_well', 'at': [94, 92]},
        {'id': 'poi:shrine_poison', 'at': [26, 82]},
        {'id': 'poi:money_tree', 'at': [55, 47]},
        {'id': 'poi:rain_barrel', 'at': [60, 59]},
        {'id': 'poi:water_reflector', 'at': [102, 96]},
        {'id': 'poi:gunther_notice', 'at': [53, 45]},
        {'id': 'poi:orc_outposts', 'index': 1, 'at': [30, 29]},
        {'id': 'poi:orc_outposts', 'index': 2, 'at': [56, 23]},
        {'id': 'poi:orc_outposts', 'index': 3, 'at': [97, 31]},
        {'id': 'poi:orothin_statues', 'index': 1, 'at': [65, 67]},
        {'id': 'poi:orothin_statues', 'index': 2, 'at': [70, 66]},
        {'id': 'poi:druid_grove', 'at': [26, 60]},
        {'id': 'poi:derek_camp', 'at': [42, 78]},
        {'id': 'poi:signs', 'index': 1, 'at': [59, 33]},
        {'id': 'poi:signs', 'index': 2, 'at': [63, 72]},
        {'id': 'poi:signs', 'index': 3, 'at': [38, 45]},
        {'id': 'junction:west_gate', 'at': [41, 44]},
        {'id': 'junction:north_gate', 'at': [52, 38]},
        {'id': 'junction:east_gate', 'at': [62, 46]},
        {'id': 'junction:south_gate', 'at': [52, 50]},
        {'id': 'junction:hill_fork', 'at': [60, 32]},
        {'id': 'junction:south_fork', 'at': [62, 73]},
        {'id': 'landmark:witch_tower', 'at': [88, 84]},
        {'id': 'landmark:temple_spire', 'at': [58, 46]},
        {'id': 'landmark:pyramid', 'at': [84, 46]},
        {'id': 'landmark:rim', 'at': [104, 47]},
    ]
    def circ(cx, cy, r):
        return {'at': [cx, cy], 'r': r}
    areas = []
    # Second pass (REVIEW 8): about a third fewer markers, gathered at camps of 2-4 markers with empty walks
    # between; nothing within 6 cells (3,000) of a gate.
    def camp(pop, spots, r):
        for (cx, cy, n) in spots:
            k = sum(1 for a in areas if a['id'] == pop) + 1
            areas.append({'id': pop, 'index': k, 'kind': 'encounter', 'count': n, 'circle': circ(cx, cy, r)})
    # Pass three (TOWN_FEEL 5): groups of 2-3 (the slots' dice), clustered unevenly with empty stretches between;
    # about one in five guards something: two by each wild chest, one by each dungeon door; the town and 4,500
    # round every house door kept clear (checked below). Spots (x, y, markers, radius).
    def camps(pop, spots):
        for (cx, cy, n, r) in spots:
            k = sum(1 for a in areas if a['id'] == pop) + 1
            areas.append({'id': pop, 'index': k, 'kind': 'encounter', 'count': n, 'circle': circ(cx, cy, r)})
    # Rebase (A5, 2026-11-20; CHANGES_FOR_BUILT_MAPS X1-4, MONSTERS_AND_ITEMS 3): 130 hostiles at load (MAPS 0) in
    # four encounter areas: the northern hills' orc country (west), the orc outposts' road (the north road and the
    # east hills), Toad Meadow, the dead forest. The meadows, the orchard, the pond and the south-central land are
    # quiet. Each kind where it lives (pass five): orcs at camps and in the hills, toads and snakes in the marsh, the
    # dead in the dead wood. Pass six's meadow and creek groups and the lone wanderers by the roads are gone; the first
    # fight from each arrival is 2,000-6,000 away (checked below). Spots (x, y, markers, radius).
    # Markers in pairs and threes a few cells apart, the pairs far apart (TOWN_FEEL 5: wild group to nearest group
    # 403-2,433, spacing variation 0.46-2.08).
    # F10 (A5 s29): the Spring Druid's west meadows (tile [31, 58]) lay 12,731 from every monster; the lone hill-orc
    # marker moves from (17, 38) to (44, 66) (output/studio_cal/a5/s29/x1_spot.py: deepest 10,700 after), 8,700 from the druid, 6,000 from Derek (move only)
    camps('pop:hill_orcs', [(12, 43, 2, 1.5), (44, 66, 1, 0.25), (25, 26, 1, 1), (27, 23, 1, 1), (36, 25, 1, 1),
                            (40, 28, 1, 0.5)])
    camps('pop:road_orcs', [(72, 10, 2, 1.5), (67, 13, 1, 1), (77, 19, 1, 1), (79, 23, 1, 1), (62, 24, 1, 0.5),
                            (86, 25, 1, 1), (94, 25, 1, 1), (100, 26, 1, 0.5)])
    camps('pop:toads', [(95, 78, 1, 1), (98, 82, 1, 1), (84, 90, 1, 1), (80, 93, 1, 1), (71, 86, 1, 1),
                        (70, 82, 1, 1), (92, 97, 1, 1), (96, 95, 1, 0.5)])
    camps('pop:dead', [(26, 86, 1, 1), (30, 84, 1, 1), (28, 100, 2, 1.5), (23, 103, 1, 1), (36, 100, 1, 1),
                       (38, 96, 1, 1)])
    for _pop, _spots in ROAD_CAMPS.items():
        camps(_pop, _spots)
    # The arrivals (edges, the dungeons' exits onto X1): no group within 2,000 (MAPS: the first fight 2,000-6,000
    # from each arrival; the town's start is held 4,500 clear by the town rule below).
    ARRIVALS = {'west road': (21, 46), 'north road': (69, 21), 'xd02 exit': (44, 32.5), 'xd03 exit': (62, 29.7),
                'xd04 exit': (88, 81.55), 'xd05 exit': (82, 31.5)}
    for a in areas:
        if a['kind'] == 'encounter':
            c = a['circle']
            for name, (ax, ay) in ARRIVALS.items():
                d = (math.hypot(c['at'][0] - ax, c['at'][1] - ay) - c['r']) * 512
                if d < 2000:
                    raise SystemExit('monsters within 2,000 of the %s arrival: %s %s (%.0f)' % (name, a['id'],
                                                                                              c['at'], d))
    _vdoors = [d[2] for d in doors_out if not d[0].startswith(('building:myra', 'building:valia', 'building:hamlet',
                                                                'building:oslo', 'building:celia'))]
    nearest_group = None
    for a in areas:
        if a['kind'] == 'encounter':
            c = a['circle']
            near = min(math.hypot(c['at'][0] - p[0], c['at'][1] - p[1]) for p in _vdoors) - c['r']
            if near * 512 < 4500:
                _bad = [(b['id'], b['circle']['at'], round((min(math.hypot(b['circle']['at'][0] - p[0],
                         b['circle']['at'][1] - p[1]) for p in _vdoors) - b['circle']['r']) * 512))
                        for b in areas if b['kind'] == 'encounter']
                raise SystemExit('monsters within 4,500 of a Vertigo door: %s' % [b for b in _bad if b[2] < 4500])
            if nearest_group is None or near < nearest_group[0]:
                nearest_group = (near, a['id'], c['at'])
    # the town's first fight: the nearest group to a Vertigo door stays within the shipped towns' 6,796 (TOWN_FEEL 5)
    print('nearest group to a Vertigo door: %.0f (%s %s)' % (nearest_group[0] * 512, nearest_group[1],
                                                             nearest_group[2]))
    if nearest_group[0] * 512 > 6796:
        raise SystemExit('no group within 6,796 of a Vertigo door (TOWN_FEEL 5)')
    areas.append({'id': 'town:vertigo', 'kind': 'keep_clear', 'polygon': [[28, 33], [74, 33], [74, 66], [28, 66]]})
    views = [
        {'id': 'entrance:party_start', 'at': [54, 48], 'height': 200, 'look': [54, 38], 'purpose': 'The square.'},
        {'id': 'landmark:witch_tower', 'at': [56, 50], 'height': 600, 'look': [88, 84],
         'purpose': 'The Witch Tower from the town wall.'},
        {'id': 'landmark:rim', 'at': [76, 45], 'height': 200, 'look': [104, 47],
         'purpose': 'The signature view: the orchard road to the rim.'},
    ]
    scatter = []
    ground_extra = []
    def sc(sid, deco, count, poly=None, circle=None, clusters=None, spacing=None, line=None):
        e = {'id': sid, 'decoration': deco, 'count': count}
        if poly: e['polygon'] = poly
        if circle: e['circle'] = circle
        if line: e['line'] = line
        if clusters: e['clusters'] = clusters
        if spacing: e['spacing'] = spacing
        scatter.append(e)
    meadow_w = [[19, 37], [41, 37], [41, 74], [19, 74]]
    meadow_c = [[30, 62], [66, 62], [66, 74], [30, 74]]
    meadow_e = [[70, 36], [103, 36], [103, 66], [70, 66]]
    # Trees (tree spacing pass, measured): every stand by one even dart throw over its kinds (dress.even_stand);
    # the counts of pass two, spread instead of clumped.
    ALL_WAYS = DR.COBBLE + DR.DIRT + T.LANES + [l['line'] for l in roads] + [
        [[66, 42.5], [80, 43.5]], [[66, 46.5], [80, 47.5]], [[88, 44.5], [100, 45.5]], [[88, 48.5], [100, 49.5]]]
    POIS = [p['at'] for p in points] + [d[2] for d in doors_out]
    def wild_avoid(extra_d=1.2):
        on_way = DR.near_lines(ALL_WAYS, 1.0)
        on_water = DR.near_lines([RIVER_LINE, OUTFLOW], 2.6)
        def f(p):
            if on_way(p) or on_water(p) or T.inside(p, LAKE):
                return True
            if any(math.hypot(p[0] - q[0], p[1] - q[1]) < extra_d for q in POIS):
                return True
            return any(T.inside(p, fp) or DR.edge_dist(p, fp) < 0.6 for _, _, fp in footprints)
        return f
    TAKEN = []
    AV = wild_avoid()
    # Pass three: the stands are the studio's even scatter (batch O-A: `kinds`, `spacing`, `close_share`,
    # `edge_thin`, `spacing_group`) instead of one entry per tree. dress.even_stand still runs, only to give the wild
    # fill below the stands' approximate places to keep clear of.
    def stand(sid, poly, kinds, count, spacing, close, close_at):
        e = {'id': sid, 'count': count, 'polygon': poly, 'spacing': spacing, 'close_share': close,
             'close_spacing': close_at, 'edge_thin': {'width': 3, 'keep': 0.35}, 'spacing_group': 'trees'}
        if len(kinds) == 1:
            e['decoration'] = list(kinds)[0]
        else:
            e['kinds'] = dict(kinds)
        scatter.append(e)
    # Rebase (A5, 2026-11-20; CHANGES X1-8, review SCALE_AND_DENSITY 6): at most 800 decorations and at least 40
    # central land cells (of 4,096) with fewer than 3, as open meadow (shipped median 57; X1 had 16-23). The meadows'
    # even stands (55, 15 and 18 trees over the whole meadow) became groves and copses with open grass between them:
    # the Spring Druid's grove, a copse by the west road, the woodcutters' wood, a strip by the pond, two copses on the
    # east meadow. Flowers in a few patches. What fills the eye is the rolling ground and the grass (terrain materials).
    GROVES = [('scatter:broadleaf', [[23, 56], [30, 56], [30, 64], [23, 64]], {'7tree13': 3, '7tree16': 2}, 12),
              ('scatter:broadleaf', [[20, 37], [28, 37], [28, 43], [20, 43]], {'7tree13': 1, '7tree16': 1}, 10),
              ('scatter:broadleaf', [[30, 64], [40, 64], [40, 73], [30, 73]], {'7tree13': 2, '7tree16': 3}, 14),
              ('scatter:broadleaf', [[40, 64], [50, 64], [50, 69], [40, 69]], {'7tree16': 1}, 7),
              ('scatter:broadleaf', [[74, 50], [80, 50], [80, 55], [74, 55]], {'7tree13': 1}, 6),
              ('scatter:broadleaf', [[94, 53], [102, 53], [102, 60], [94, 60]], {'7tree13': 1, '7tree16': 1}, 7)]
    for sid, poly, kinds, n in GROVES:
        stand(sid, poly, kinds, n, 1.3, 0.15, 0.8)
    sc('scatter:flowers', 'flower01', 6, [[24, 47], [34, 47], [34, 52], [24, 52]], clusters=2)
    sc('scatter:flowers', 'flower01', 5, [[30, 74], [38, 74], [38, 78], [30, 78]], clusters=2)
    sc('scatter:flowers', 'flower06', 6, [[44, 70], [50, 70], [50, 74], [44, 74]], clusters=2)
    sc('scatter:flowers', 'flower02', 6, [[86, 51], [92, 51], [92, 55], [86, 55]], clusters=2)
    sc('scatter:rocks', '7rock09', 8, [[19, 19], [109, 19], [109, 36], [19, 36]], clusters=5)
    sc('scatter:rocks', '7rock08', 6, [[19, 19], [109, 19], [109, 36], [19, 36]], clusters=4)
    DR.even_stand('scatter:hill_trees', [[19, 19], [103, 19], [103, 36], [19, 36]],
                  {'7tree22': 18, '7tree16': 25}, 0, 2.2, 1.2, 0.1, avoid=AV, taken=TAKEN, seed=14, count=43)
    stand('scatter:hill_trees', [[19, 19], [103, 19], [103, 36], [19, 36]], {'7tree22': 18, '7tree16': 25}, 32,
          2.2, 0.1, 1.2)
    # The orchard: fruit trees in rows along the orchard road, both sides (pass three: the road jogs round the east
    # houses, the rows follow its last run).
    sc('scatter:orchard', 'tree37', 5, line=[[75.5, 43.3], [81, 43.3]])
    sc('scatter:orchard', 'tree37', 8, line=[[72.5, 46.8], [81, 46.8]])
    sc('scatter:orchard', 'tree37', 6, line=[[88, 44.5], [100, 45.5]])
    sc('scatter:orchard', 'tree37', 6, line=[[88, 48.5], [100, 49.5]])
    # The dead forest
    dead = [[19, 74], [50, 74], [50, 109], [19, 109]]
    # Deyja's dead forest measured: nearest tree 1.97 cells (median), 1.35 (10th percentile), 0.97 least; 0.116 trees
    # a cell where it stands; tree41 and tree42 mixed (0.51 of nearest pairs unlike); the rim's gaps 2.5 against 1.7.
    DR.even_stand('scatter:dead_trees', dead, {'tree41': 2, 'tree42': 1}, 0.125, 1.4, 1.0, 0.08,
                  edge=3.0, edge_keep=0.35, avoid=AV, taken=TAKEN, seed=15)
    stand('scatter:dead_trees', dead, {'tree41': 2, 'tree42': 1}, int(round(0.105 * DR.poly_area(dead))), 1.6, 0.08,
          1.0)
    sc('scatter:dead_bushes', '7dec11', 10, dead, clusters=5)
    sc('scatter:bones', '7dec18', 16, dead, clusters=7)
    sc('scatter:bones', '7dec20', 5, dead, clusters=3)
    sc('scatter:dead_rocks', '7rock08', 10, dead, clusters=5)
    sc('scatter:dead_rocks', '7rock09', 8, dead, clusters=4)
    # Toad Meadow
    marsh = [[66, 78], [100, 78], [100, 100], [66, 100]]
    DR.even_stand('scatter:swamp_trees', marsh, {'swptree1': 3, 'swptree2': 2}, 0, 1.7, 1.0, 0.1,
                  avoid=AV, taken=TAKEN, seed=16, count=50)
    stand('scatter:swamp_trees', marsh, {'swptree1': 3, 'swptree2': 2}, 42, 1.7, 0.1, 1.0)
    DENSE = [meadow_w, meadow_c, [[19, 19], [103, 19], [103, 36], [19, 36]], dead, marsh]
    sc('scatter:flowers', 'flower06', 8, [[70, 66], [100, 66], [100, 78], [70, 78]], clusters=3)
    # Wild land density pass (measured): the bare stretches of the wilds (south band, east meadow, the marsh's east,
    # the land outside the play bounds that the party sees) get one thing every 2.6 cells or so where nothing stands
    # within 2.4: shipped wilds hold 3.5-8.3 decorations per 100 land cells and leave 28-60 % of their land more than
    # 3 cells from anything, the largest bare stretch 13-26 cells across. Kinds by the land: bones and rocks by the dead
    # forest, swamp trees and reeds in the marsh, groves, bushes, rocks and flowers on the meadow.
    def wild_kinds(p):
        x, y = p
        if 17 <= x <= 52 and 72 <= y <= 112:
            return {'7dec18': 3, '7rock08': 2, '7rock09': 1, 'tree42': 2, 'tree41': 2}
        if 64 <= x <= 102 and 64 <= y <= 100:
            return {'swptree2': 3, 'swptree1': 2, 'flower06': 3, '7rock09': 1}
        if y < 37:
            return {'7rock09': 3, '7rock08': 2, '7tree22': 2, '7tree16': 2, 'bush03': 1}
        return {'7tree13': 3, '7tree16': 3, 'bush03': 2, '7rock09': 2, '7rock01': 1, 'flower01': 2, 'flower02': 2}
    # Rebase: the wild fill stays only beyond the play bounds (the trees to the map's edge) and in the marsh's east
    # strip; inside, the open meadows are open on purpose (CHANGES X1-8).
    FILL = [[[100, 64], [103, 64], [103, 100], [100, 100]], [[6, 6], [19, 6], [19, 122], [6, 122]],
            [[19, 6], [103, 6], [103, 19], [19, 19]], [[19, 109], [50, 109], [50, 122], [19, 122]],
            [[50, 109], [103, 109], [103, 122], [50, 122]]]
    rnd = __import__('random').Random(21)
    AVF = wild_avoid(2.0)
    for i, poly in enumerate(FILL):
        pts = []
        DR.even_stand('scatter:wild', poly, {'x': 1}, 0.045, 4.0, None, 0, edge=0.01, edge_keep=1, avoid=AVF,
                      taken=pts, seed=31 + i)
        for p in pts:
            if any(T.inside(p, d) for d in DENSE):
                continue      # pass three: the stands are the studio's scatter now; their places are not known here
            if any(math.hypot(p[0] - q[0], p[1] - q[1]) < 3.2 for q in TAKEN):
                continue
            TAKEN.append(p)
            k = wild_kinds(p)
            name = rnd.choices(list(k), list(k.values()))[0]
            sid = 'scatter:dead_trees' if name.startswith('tree4') else 'scatter:wild'
            scatter.append({'id': sid, 'decoration': name, 'count': 1,
                            'circle': {'at': [round(p[0], 3), round(p[1], 3)], 'r': 0.1}})
    # Small places along the views where shipped maps have one: an old campfire with bones, a fallen stone ring,
    # a lone grave cairn, a wrecked camp by the south band.
    for (deco, at) in (('dec24x', (66, 107)), ('7dec18', (66.8, 107.6)), ('7dec20', (65.3, 106.4)),
                       ('7dec18', (88.5, 110.4)), ('7rock08', (88, 109.6)), ('7rock09', (89.1, 109.8))):
        scatter.append({'id': 'scatter:wild_places', 'decoration': deco, 'count': 1,
                        'circle': {'at': [at[0], at[1]], 'r': 0.1}})
    sc('scatter:wild_places', '7rock09', 7, line=[[78, 58], [80, 56], [82.5, 56.5], [83, 59], [80.5, 60.5]],
       )
    for (cx, cy) in ((58, 112), (95, 58), (76, 104), (24, 66), (98, 112), (60, 90), (12, 40), (40, 112)):
        ground_extra.append({'material': 'soil', 'polygon': [[cx - 1, cy - 1], [cx + 2, cy - 1], [cx + 2, cy + 1],
                                                            [cx - 1, cy + 1]], 'notes': 'a bare patch in the meadow'})
    # The farm belt outside the walls (REVIEW 7): orchards, hedged fields, garden rows, tree clumps to the wall
    sc('scatter:town_trees', '7tree13', 6, [[31, 37.5], [40.5, 37.5], [40.5, 40], [31, 40]], clusters=2)
    sc('scatter:town_trees', '7tree16', 5, [[63.5, 37.5], [71, 37.5], [71, 41.5], [63.5, 41.5]], clusters=2)
    sc('scatter:town_trees', '7tree16', 5, [[42, 51.5], [62, 51.5], [62, 53.5], [42, 53.5]], clusters=3)
    sc('scatter:orchard', 'tree37', 5, line=[[34.5, 48.5], [39.5, 48.5]])
    sc('scatter:orchard', 'tree37', 6, line=[[31.5, 49.8], [39.5, 49.8]])
    for (x0, y0, x1, y1) in ((42.5, 61, 47.5, 63.5), (48.5, 61, 51, 63.5), (24, 42, 31, 45), (24, 47, 31, 50)):
        sc('scatter:hedges', 'bush02', max(4, int((x1 - x0) * 0.9)), line=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
           )
        sc('scatter:crops', 'flower02', int((x1 - x0) * (y1 - y0) * 0.15), [[x0 + 0.4, y0 + 0.4], [x1 - 0.4, y0 + 0.4],
                                                                          [x1 - 0.4, y1 - 0.4], [x0 + 0.4, y1 - 0.4]])
    sc('scatter:town_flowers', 'flower06', 6, circle={'at': [54.9, 46.4], 'r': 1.4})
    sc('scatter:town_flowers', 'flower02', 5, line=[[53, 49.0], [55.5, 49.0]])
    sc('scatter:verge', 'flower02', 10, [[42.6, 38.9], [61.6, 38.9], [61.6, 49.2], [42.6, 49.2]], clusters=5)
    scatter.extend(town_scatter)
    ground = [
        {'material': 'grass_meadow', 'polygon': [[0, 0], [104, 0], [104, 128], [0, 128]],
         'notes': 'meadow; the town floor is grass too (second pass): dirt only on roads, lanes, door aprons, the square'},
        {'material': 'swamp', 'polygon': [[66, 78], [100, 78], [100, 100], [70, 100], [66, 92]],
         'notes': 'Toad Meadow marsh'},
        {'material': 'soil', 'polygon': [[20, 76], [48, 76], [48, 108], [20, 108]],
         'notes': 'the dead forest floor: bare dark soil'},
        {'material': 'soil', 'polygon': [[53, 45], [56, 45], [56, 48], [53, 48]],
         'notes': 'the market square round the fountain (pass four: 3 x 3, was 4 x 4)'},
        {'material': 'soil', 'polygon': [[59, 57], [62, 57], [62, 61], [59, 61]],
         'notes': "Joe's yard"},
    ] + ground_extra + town_ground
    structures = []
    # Town wall (second pass): crenellated runs on a footing, round towers, two-tower gatehouses
    structures.extend(T.wall_structures())
    structures.extend(TOWN_THINGS)
    # Pass four (REVIEW_PASS3 1): the steps climb the whole 512 (`rise`; they climbed the default 256 and stood as a
    # loose block at the slope's foot), through gaps in the retaining wall, whose ends flank the upper flight.
    RISE = T.UPPER_H - 640
    structures.append({'id': 'thing:town_hall_steps', 'kind': 'stairs', 'line': [[48.75, 43.0], [48.75, 41.3]],
                       'width': 384, 'rise': RISE, 'textures': {'wall': T.RETAIN_TEX},
                       'notes': 'The town hall stands on the upper terrace; a flight of steps down to the main street.'})
    for sid, x in (('thing:smith_lane_steps', 44.5), ('thing:bank_lane_steps', 56.5)):
        structures.append({'id': sid, 'kind': 'stairs', 'line': [[x, 43.2], [x, 41.0]], 'width': 384, 'rise': RISE,
                           'textures': {'wall': T.RETAIN_TEX},
                           'notes': 'The lane climbs to the upper town by steps between the shops.'})
    structures.extend(T.retaining_walls())
    structures.append({'id': 'thing:town_bridge', 'kind': 'bridge', 'line': [[52, 50.3], [52, 54.6]],
                       'width': 512, 'rise': 48, 'kerb': 48, 'title': 'Vertigo Bridge',
                       'notes': 'The stone bridge from the south gate over Pitchfork Creek.'})
    structures.append({'id': 'thing:fountain_square', 'kind': 'fountain', 'at': [54.5, 46.2],
                       'title': 'Fountain',
                       'effects': [{'text': 'Refreshing!'}]})
    structures.append({'id': 'thing:money_tree', 'kind': 'decoration', 'decoration': 'tree37', 'at': [55.8, 47.6],
                       'title': 'Money Tree', **(
                           {'effects': hook('x1.money_tree')} if IN_WORLD else
                           {'condition': {'not': {'qbit': QBITS['x1.money_tree']}},
                            'effects': [{'qbit': QBITS['x1.money_tree']}, {'gold': 100},
                                        {'text': HOOKS['x1.money_tree']['text']}],
                            'else_effects': [{'text': HOOKS['x1.money_tree']['else_text']}]})})
    structures.append({'id': 'thing:gunther_notice', 'kind': 'sign', 'at': [53.2, 45.2], 'height': 192,
                       'width': 128, 'title': "Mayor Gunther's notice",
                       'effects': [{'lua': 'evt.SimpleMessage("NOTICE. By order of Mayor Gunther: slimes and doom '
                                    'bugs plague Vertigo. Any who clear them will be paid at the Town Hall. Joe the '
                                    'Exterminator (south bank, by the creek) is not to be paid in advance. Joe\'s '
                                    'warehouse stands at the end of the guild lane.")'}]})
    # D-93 (A3 s39 for A5, 2026-11-22; was D-90's ground item at the barrel's foot): a click on the rain barrel puts the
    # warehouse key onto the cursor, the find on the status line (the quest hook m2.rain_barrel, once)
    structures.append({'id': 'thing:rain_barrel', 'kind': 'decoration', 'decoration': 'bigbarel', 'at': [61.8, 59.65],
                       'title': 'Rain barrel', **({'effects': [{'lua': 'XeenQuests.hook("m2.rain_barrel")'}]} if IN_WORLD else {
                       'condition': {'not': {'map_var': 'barrel_key_taken'}},
                       'effects': [{'set': {'var': {'map_var': 'barrel_key_taken'}, 'value': 1}}, {'give_item': 'warehouse_key'},
                                   {'lua': 'evt.SimpleMessage("Under the rain barrel by Joe\'s warehouse, wrapped in '
                                           'oilcloth: a store-room key. Joe keeps his spare where everyone keeps '
                                           'theirs. (You receive the warehouse key.)")'}],
                       'else_effects': [{'text': 'Only wet stones under the barrel now.'}]})})
    # Pass three: the ways in as the shipped maps build them (OUTDOOR_REBUILD_PROCEDURE.md "Buildings built into the
    # terrain"; batch O-B/O-C words). Each click face stays where the doorway's was, so the dungeons' exits (400 in
    # front of it, facing out) still land in front of it: the mine's at y 31.713, the shaft's 28.912, the orc mouth's
    # 30.713, the culvert's 53.666 (from the dungeons' arrival points). Measured on the build (`oymap things`): a cave
    # mouth's dark face lies `depth` + 72 behind its footprint's front edge, a wedge hatch's `depth` behind its front,
    # a culvert's `depth` + 64 behind its headwall's front.
    WAYS_IN = {
        'thing:mine_portal': {'kind': 'cave_mouth', 'at': [44, 31.0], 'size': [1024, 1024], 'floor': 1184,
                              'mouth': {'width': 448, 'height': 352, 'depth': 75},
                              'textures': {'shell': 't2bs', 'door': '7solid01'}, 'hint': 'Red Dwarf Mines',
                              'roughness': 0.6, 'seed': 3},
        'thing:orc_cave_mouth': {'kind': 'cave_mouth', 'at': [82, 30.0], 'size': [1024, 1024], 'floor': 1376,
                                 'mouth': {'width': 512, 'height': 384, 'depth': 75},
                                 'textures': {'shell': 'cwb1', 'door': '7solid01'}, 'hint': 'Orc Caves',
                                 'roughness': 0.7, 'seed': 5},
        'thing:shaft_head': {'kind': 'hatch', 'form': 'wedge', 'at': [62, 28], 'size': [1024, 1024], 'floor': 1472,
                             'mouth': {'width': 384, 'height': 192, 'depth': 45},
                             'textures': {'shell': 'cnb', 'door': '7solid01'}, 'hint': "The Clan King's shaft"},
        # pass four (REVIEW_PASS3 3): lower and wider, in the town wall's stone, set into a quay wall along the bank
        # F19 (the user 2026-11-22, "slits/steps"): one headwall the quay's whole length (58.5 to 63.5) instead of a
        # 960 headwall between two separate quay walls proud of it; 112 thick + depth 16 keeps the dark face 128
        # behind the front (XD-01's arrival)
        # D-95 (the user 2026-11-22: "sloped down terrain a bit and there the entrance ... embedded in the terrain"):
        # the kit's sunken entrance: the mouth in the end face of a ditch cut a party height into the south bank, its
        # crown under the land's level, no water on the land, a stone quay behind it (CULVERT)
        'thing:culvert_grate': {'kind': 'culvert', 'outflow': 0, 'height': 176, 'width': 320,
                                'textures': {'wall': T.RUN_TEX}, 'water_level': 8, 'hint': 'Culvert'},
        # pass five (the user's walk): the door on the tower's north side, the side the party comes from (was south,
        # round the back); in the tower's own grey stone with a dark door (it was a dirt frame)
        'thing:witch_tower_door': {'kind': 'doorway', 'at': [88, 82.4], 'turn': 180, 'height': 352, 'width': 192,
                                   'depth': 384, 'hood': 128, 'arch': 'pointed',
                                   'textures': {'door': '7solid01', 'wall': 'cnb'}},
    }
    for tid, cell, turn, title, mp, at, facing, cond, locked, entr in ENTRANCES:
        if tid in WAYS_IN:
            st = dict(id=tid, **WAYS_IN[tid])
            if tid == 'thing:culvert_grate':
                st = CULVERT.structures(st)[0]          # D-95: at, thickness, depth and headwall from the kit
            st['title'] = 'Enter ' + title if not cond else title
            st['into'] = {'map': mp, 'at': at, 'facing': facing}
        else:
            # pass five: the warehouse's loading door, set in the warehouse's west wall (it stood free in the yard);
            # a dark opening (7solid01, as Erathia's sewer house and every MM7 dungeon door) in a stone frame
            st = {'id': tid, 'kind': 'doorway', 'at': list(cell), 'turn': turn, 'height': 352, 'width': 256,
                  'depth': 384, 'hood': 96, 'title': "Enter Joe's Warehouse",
                  'textures': {'door': '7solid01', 'wall': 'cwb'},
                  'into': {'map': mp, 'at': at, 'facing': facing}}
        if cond:
            st['condition'] = cond
            if tid == 'thing:shaft_head':
                st['else_effects'] = [{'lua': SHAFT_ELSE}]
            elif tid == 'thing:witch_tower_door' and not IN_WORLD:
                st['else_effects'] = [{'lua': TOWER_ELSE}]
            elif locked:
                st['locked_text'] = locked
        structures.append(st)
    # D-95: the culvert's ditch lined by revetments, the quay over the cut behind its end face, and on the creek's edge
    # the outfall: a low barred arch at the waterline in a small block of the quay's stone (a drain, not a second door)
    structures += CULVERT.structures({'kind': 'culvert', 'height': 176}, outfall_y=52.97)[1:]
    # Pass four (REVIEW_PASS3 6): the mine and the orc cave told apart and set in their hills: the mine's shell grey rock
    # (t2bs) with timber stacks, a spoil heap, a cask and two torches at its mouth; the orc mouth red-brown rock (cwb1,
    # the dragon cave's) with skulls on spears, stakes, bones and a fire; the shaft head a stone hatch (cnb) with
    # timber and a cask. Rocks on the shoulders of each. Nothing within 0.8 cell of a mouth's middle (the walk's click).
    DRESS = [
        # the mine (front y 32, mouth x 44): only decorations drawn as 3D models (the sprites read as specks)
        ('7dec16', 42.5, 32.6), ('7dec16', 45.6, 32.9), ('stump5a', 42.2, 33.3), ('smlbarel', 45.3, 32.4),
        ('bigbarel', 45.55, 32.25), ('7dec01', 46.3, 32.5), ('dec23', 46.7, 31.9), ('dec06', 43.15, 32.12),
        ('dec06', 44.85, 32.12), ('rock10', 42.5, 31.2), ('rock12', 45.5, 31.0), ('7rock04', 42.8, 30.3),
        ('rock26', 45.2, 30.2), ('7rock09', 44.1, 29.6), ('7rock05', 41.8, 31.6), ('rock10', 46.3, 31.3),
        # the orc caves (front y 31, mouth x 82)
        ('fla3__01', 81.05, 31.3), ('fla3__01', 82.95, 31.3), ('sklplrev', 80.6, 31.6), ('sklplrev', 83.5, 31.7),
        ('dec19', 81.5, 32.0), ('dec21', 82.7, 32.3), ('dec05', 83.4, 32.2), ('dec29', 80.8, 32.4),
        ('cmpfyr00', 84.4, 32.6), ('dec22', 84.9, 32.0), ('corpse04', 80.2, 32.8), ('7rock08', 80.4, 30.1),
        ('rock12', 83.6, 30.2), ('7rock04', 82.2, 29.0), ('rock26', 79.8, 30.9),
        # the shaft head (front y 29, hatch x 62)
        ('7dec16', 60.5, 29.3), ('7dec16', 60.65, 28.8), ('smlbarel', 64.3, 29.1), ('bigbarel', 63.7, 29.6), ('stump5a', 60.6, 28.4),
        ('rock10', 60.7, 27.8), ('rock12', 63.3, 27.4), ('7rock04', 62.0, 26.6)]
    for i, (deco, x, y) in enumerate(DRESS):
        structures.append({'id': 'thing:way_in_dress_%d' % (i + 1), 'kind': 'decoration', 'decoration': deco,
                           'at': [x, y]})
    # Pass five (the user's walk: "this one is a dungeon - I wouldn't know"): Joe's warehouse, a long timber store
    # (7t1butts over a stone base, as Erathia's sewer house MTSewer: planks, CWB stone, a black 7solid01 door) round
    # the loading door, which keeps its place (XD-01's arrival); torches either side of the door, crates and casks.
    structures.append({'id': 'thing:joes_warehouse', 'kind': 'building', 'at': [61.0, 57.0], 'size': [2.5, 2.5],
                       'kit': 'timber', 'door': 'none', 'title': "Joe's Warehouse",
                       'parts': [{'id': 'store', 'at': [32, 32], 'size': [1184, 1216], 'wall_height': 512,
                                  'roof': 'gable', 'ridge_along': 'ns', 'roof_pitch': 35, 'windows': 'none',
                                  'textures': {'base': 'cwb', 'roof': 'hhp2rf'}}],
                       'notes': "Pass five: the store round XD-01's loading door (the door is the doorway thing)."})
    # Every way in marked as shipped dungeon doors are: standing torches either side (dec06, the MM8 standing torch
    # model; the mine had them), skulls at the Temple of Yak; nothing within 0.8 cell of a click face's middle.
    for i, (d, x, y) in enumerate([('dec06', 60.75, 57.65), ('dec06', 60.75, 58.95), ('bigbarel', 60.75, 59.45),
                                   ('smlbarel', 61.0, 59.7), ('7dec21', 60.6, 57.15),
                                   ('dec06', 61.1, 29.3), ('dec06', 62.9, 29.3),
                                   ('dec06', 87.1, 81.95), ('dec06', 88.9, 81.95), ('7rock08', 86.6, 81.2)]):
        # 2026-11-15: the Temple of Yak's torches and skull piles went with its door (XD-06 moved to X2)
        structures.append({'id': 'thing:door_mark_%d' % (i + 1), 'kind': 'decoration', 'decoration': d, 'at': [x, y]})
    # The quay wall the culvert's headwall is set into: the south bank held by the town wall's stone either side of
    # the headwall (960 wide, its front 128 proud of the quay), its top level with the headwall's.
    # F19: the quay walls are the culvert's own headwall now (one piece, no joints; see WAYS_IN)
    # The Witch Tower: a tall crooked round tower (the doorway stands in its foot)
    structures.append({'id': 'thing:witch_tower', 'kind': 'building', 'at': [86, 82], 'size': [4, 4],
                       'kit': 'stone', 'door': 'none', 'title': 'The Witch Tower', 'facing': 's',
                       'parts': [
                           {'id': 'base', 'shape': 'round', 'at': [1024, 1024], 'radius': 640, 'sides': 10,
                            'wall_height': 768, 'roof': 'none', 'windows': 'none'},
                           {'id': 'mid', 'shape': 'round', 'at': [1088, 960], 'radius': 544, 'sides': 10,
                            'bottom': 768, 'wall_height': 768, 'roof': 'none', 'windows': 'all'},
                           {'id': 'top', 'shape': 'round', 'at': [1152, 896], 'radius': 480, 'sides': 10,
                            'bottom': 1536, 'wall_height': 640, 'roof': 'cone', 'roof_pitch': 70,
                            'windows': 'all'}],
                       'notes': 'Each storey set a little further north-east: the crooked tower of XD-04.'})
    # Travel pyramid (sealed)
    structures.append({'id': 'thing:pyramid', 'kind': 'building', 'at': [82.5, 44.5], 'size': [3, 3], 'kit': 'stone',
                       'title': 'Travel Pyramid', 'door': 'none',
                       'parts': [{'id': 'p', 'at': [128, 128], 'size': [1280, 1280], 'wall_height': 64,
                                  'roof': 'hip', 'roof_pitch': 52, 'windows': 'none', 'title': 'Travel Pyramid',
                       'effects': ([{'lua': 'Xeen.travelPyramid("vertigo")'}] if IN_WORLD else
                                   [{'lua': lua_text('A pyramid of old stone, warm to the touch. The moons are not '
                                                     'aligned.')}])}],
                       'notes': 'Sealed until M7 (Act II): says so.'})
    # The rim falls. Passes two to five built them from sheets and buildings (a sloping slab, a fan of three sheets,
    # then a block in the water whose east wall was the fall, between leaning rock buildings): the user saw a water box
    # with a dirt strip between the creek and its top, between blocky rock boxes. Now the studio's `waterfall` word
    # (as Alvar's WaterfallC1test on out03): a level water face over the creek's last cells joining its water to the
    # lip, an upright sheet from the lip to the water below the rim, the land cut under it, a faceted crag of grey
    # rock (t2bs, Alvar's grey faces) at each edge. The creek is 576 at the lip, the water below 0.
    structures.append({'id': 'thing:rim_falls', 'kind': 'waterfall', 'line': [[104, 60], [106, 60]], 'top': RIVER,
                       'foot': 0, 'lean': 220, 'spread': 1.7, 'back': 768, 'pool': 768, 'rock_size': 400, 'rise': 64,
                       'textures': {'rock': 't2bs'}, 'title': 'Pitchfork Falls',
                       'notes': "The creek's fall off the world rim (the studio's waterfall word)."})
    for i, (x, y, d) in enumerate([(104.4, 57.6, '7rock09'), (104.6, 62.4, '7rock09'), (103.6, 57.9, '7rock08'),
                                   (103.7, 62.1, '7rock08'), (105.6, 58.4, '7rock09'), (105.7, 61.7, '7rock08'),
                                   (106.5, 59.0, '7rock09'), (106.5, 61.0, '7rock04')]):
        structures.append({'id': 'thing:falls_rock_%d' % (i + 1), 'kind': 'decoration', 'decoration': d, 'at': [x, y]})
    structures.append({'id': 'thing:falls_sound', 'kind': 'decoration', 'decoration': 'Snd_Brook', 'at': [104, 60]})
    # The obelisk
    structures.append({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [74, 34], 'height': 768, 'title': 'Obelisk',
                       'effects': hook('obelisks.x1', window=True) if IN_WORLD else
                       [{'lua': 'evt.SimpleMessage("Carved into the obelisk: the first word of a riddle '
                             'that runs across Cloudside: \\"SEEK\\". (The other obelisks are not built yet.)")'}]})
    # Wells, fountain, shrine
    structures.append({'id': 'thing:fountain_ability', 'kind': 'fountain', 'at': [46, 70],
                       'title': 'Fountain of Ability', 'condition': {'not': {'map_var': 'ability_drunk'}},
                       'effects': [{'set': {'var': {'map_var': 'ability_drunk'}, 'value': 1}}, {'add': {'var': 'BaseLuck', 'value': 2}},
                                   {'text': '+2 Luck (permanent)'}],
                       'else_effects': [{'text': 'The fountain has run dry for you.'}]})
    structures.append({'id': 'thing:waters_of_power', 'kind': 'well', 'at': [92, 50], 'roofed': True,
                       'title': 'Waters of Power',
                       'effects': [{'add': {'var': 'HP', 'value': 25}}, {'text': '+25 Hit points (temporary)'}]})
    structures.append({'id': 'thing:wishing_well', 'kind': 'well', 'at': [94, 92], 'title': 'Wishing Well',
                       'condition': {'gold': {'at_least': 1}},
                       'effects': [{'gold': -1},
                                   {'lua': 'if math.random(1, 10) == 1 then evt.Add("Gold", 25) '
                                           'evt.StatusText("Your wish comes true: 25 gold glitters in the bucket.") '
                                           'else evt.StatusText("You make a wish.") end'}],
                       'locked_text': 'You have no coin to throw.'})
    structures.append({'id': 'thing:shrine_poison', 'kind': 'building', 'at': [25, 81], 'size': [2, 2],
                       'kit': 'stone', 'title': 'Shrine of Poison', 'door': 'none',
                       'parts': [{'id': 's', 'at': [256, 256], 'size': [512, 512], 'wall_height': 320,
                                  'posts': 48, 'roof': 'hip', 'roof_pitch': 40, 'title': 'Shrine of Poison',
                       'condition': {'not': {'map_var': 'shrine_used'}},
                       'effects': [{'set': {'var': {'map_var': 'shrine_used'}, 'value': 1}}, {'add': {'var': 'BodyResistance', 'value': 5}},
                                   {'text': '+5 Body resistance (permanent)'}],
                       'else_effects': [{'text': 'The shrine is silent.'}]}]})
    structures.append({'id': 'thing:water_reflector', 'kind': 'obelisk', 'at': [102, 96], 'height': 384,
                       'sides': 8, 'title': 'Water Reflector',
                       # A3's M37 hook (2026-11-20, seventh session): the source's prompt, Yes calls the hook; before
                       # M36 (111720) the hook answers with its own fail text ("cold and silent"), after it once
                       # One Yes/No prompt with buttons, the look and the question joined (D-65 B1, D-66 item 6).
                       **({'effects': [
                           {'lua': 'if continueStep == 1 then XeenQuests.hook("m37.reflector_water") return end'},
                           {'lua': 'if continueStep ~= nil then return end'},
                           {'lua': 'AskChoiceWithAnswerSteps(eventId, 3, "A disc of dark crystal on a stone stem, '
                                   'turned toward the stars below the rim. Reflector. Activate?", {{Answer = "Yes", '
                                   'Step = 1}, {Answer = "No", Step = 2}})'}]} if IN_WORLD else
                          {'effects': [{'lua': 'evt.SimpleMessage("A disc of dark crystal on a stone stem, turned '
                                        'toward the stars below the rim. It hums faintly. Whatever it is for, its '
                                        'day has not come.")'}]})})
    # Orothin's statues on the isles: hooks q-c20.statue_disease (south isle) and q-c20.statue_poison (north isle)
    STATUE_HOOKS = ['q-c20.statue_disease', 'q-c20.statue_poison']
    for i, (x, y) in enumerate(ISLES):
        structures.append({'id': 'thing:orothin_%d' % (i + 1), 'kind': 'decoration', 'decoration': 'ped02',
                           'at': [x, y], 'title': "Orothin's statue",
                           'effects': (hook(STATUE_HOOKS[i]) if IN_WORLD else
                                       [{'text': HOOKS[STATUE_HOOKS[i]]['else_text']}])})
    # Druid grove: a ring of rune stones
    structures.append({'id': 'thing:druid_stone', 'kind': 'decoration', 'decoration': 'rock65', 'at': [26, 60],
                       'title': "The Spring Druid's stone",
                       'effects': [{'lua': 'evt.SimpleMessage("Words cut in the rune stone: Drink at the Fountain '
                                    'of Ability south of town once, and luck will follow you. The Waters of Power '
                                    'by the orchard give strength for a day.")'}]})
    # Orc outposts: a fire, a crate, three orcs (actors)
    for i, (x, y) in enumerate([(30, 29), (56, 23), (97, 31)]):
        structures.append({'id': 'thing:outpost_fire_%d' % (i + 1), 'kind': 'decoration', 'decoration': 'dec24',
                           'at': [x, y], 'title': 'Orc campfire'})
        structures.append({'id': 'thing:outpost_crate_%d' % (i + 1), 'kind': 'crate', 'at': [x + 0.8, y + 0.4],
                           'title': 'Orc supplies'})
    # Rebase (A5, 2026-11-20): pass five's west orc camp in the quiet west meadow is a hunters' camp now (CHANGES
    # X1-7 camps, X1-6 a chest in plain sight); the road camps stay orc camps, their crates casks (X1-6: twelve chests).
    structures.append({'id': 'thing:hunters_tent', 'kind': 'tent', 'at': [21.8, 61.2], 'size': [768, 640],
                       'height': 352, 'open': True, 'title': "Hunters' tent"})
    structures.append({'id': 'thing:west_camp_fire', 'kind': 'decoration', 'decoration': 'cmpfyr00', 'at': [23.9, 62.6],
                       'title': 'Campfire'})
    structures.append({'id': 'thing:hunters_chest', 'kind': 'chest', 'at': [24.9, 61.6], 'title': "Hunters' chest",
                       'chest': {'level': 1, 'random_items': 2}})
    structures.append({'id': 'thing:west_camp_bones', 'kind': 'decoration', 'decoration': 'dec05', 'at': [22.8, 63.4]})
    # pass six: the road camps (west road, north road)
    for cid, (x, y) in (('west_road', (11.5, 41.8)), ('north_road', (72.8, 9.2))):
        structures.append({'id': 'thing:%s_fire' % cid, 'kind': 'decoration', 'decoration': 'dec24', 'at': [x, y],
                           'title': 'Orc campfire'})
        structures.append({'id': 'thing:%s_crate' % cid, 'kind': 'decoration', 'decoration': 'bigbarel',
                           'at': [x + 0.8, y + 0.4]})
        structures.append({'id': 'thing:%s_keg' % cid, 'kind': 'decoration', 'decoration': 'smlbarel',
                           'at': [x + 1.15, y + 0.4]})
        structures.append({'id': 'thing:%s_bones' % cid, 'kind': 'decoration', 'decoration': 'dec05',
                           'at': [x - 0.7, y + 0.5]})
    structures.append({'id': 'thing:derek_fire', 'kind': 'decoration', 'decoration': 'dec24', 'at': [42, 78],
                       'title': "Derek's campfire"})
    structures.append({'id': 'thing:derek_chest', 'kind': 'chest', 'at': [42.8, 78.4], 'title': "Derek's chest"})
    # Signposts (rebase: the arms name the neighbours, not their codes)
    structures.append({'id': 'thing:sign_hills', 'kind': 'sign', 'at': [59.2, 33.2], 'height': 256,
                       'arms': [{'title': 'Red Dwarf Mines', 'toward': 'w'},
                                {'title': 'Orc Caves, Mount Firestone', 'toward': 'ne'},
                                {'title': 'Vertigo', 'toward': 's'}]})
    structures.append({'id': 'thing:sign_south', 'kind': 'sign', 'at': [63, 72], 'height': 256,
                       'arms': [{'title': 'Toad Meadow, Witch Tower', 'toward': 'e'},
                                {'title': 'Forest of the Walking Dead', 'toward': 'w'},
                                {'title': 'Vertigo', 'toward': 'n'}]})
    structures.append({'id': 'thing:sign_west', 'kind': 'sign', 'at': [37.6, 45.2], 'height': 256,
                       'arms': [{'title': 'Rivercity', 'toward': 'w'}, {'title': 'Vertigo', 'toward': 'e'}]})
    structures.append({'id': 'thing:sign_tower', 'kind': 'sign', 'at': [80.6, 73.4], 'height': 256,
                       'arms': [{'title': 'Witch Tower', 'toward': 'se'}, {'title': 'Toad Meadow', 'toward': 'w'}]})
    structures.append({'id': 'thing:sign_forest', 'kind': 'sign', 'at': [43.2, 82.8], 'height': 256,
                       'arms': [{'title': 'Ruined shrine', 'toward': 'w'}, {'title': "Celia's hut", 'toward': 's'},
                                {'title': 'Vertigo', 'toward': 'ne'}]})
    structures.append({'id': 'thing:sign_orchard', 'kind': 'sign', 'at': [81.6, 44.2], 'height': 256,
                       'arms': [{'title': 'Travel pyramid, the rim', 'toward': 'e'}, {'title': 'Vertigo', 'toward': 'w'}]})
    # Chests with a reason (CHANGES X1-6: 8-12, half in plain sight for a level-1 party). Guarded: the three outposts'
    # crates, the hills' cache (orcs of area 2), the marsh chest (toads), the ruined shrine (the dead). In the quiet
    # land: Derek's camp, the hunters' camp, the ruined cottage, the grave field, the old watchtower, the stone ring.
    structures.append({'id': 'thing:hill_cache', 'kind': 'chest', 'at': [102, 24], 'title': "Smugglers' cache"})
    structures.append({'id': 'thing:marsh_chest', 'kind': 'chest', 'at': [96, 96], 'title': "A drowned peddler's chest"})
    # CHANGES X1-2: where the Temple of Yak's door was, a ruined shrine against the rise, with a chest (the dead).
    structures.append({'id': 'thing:ruined_shrine', 'kind': 'building', 'at': [29.5, 96.5], 'size': [2, 2],
                       'kit': 'stone', 'door': 'none', 'title': 'Ruined shrine',
                       'ruin': {'height': [256, 704], 'gaps': 0.3, 'thickness': 48, 'seed': 7},
                       'parts': [{'id': 's', 'at': [128, 128], 'size': [768, 768], 'wall_height': 704,
                                  'roof': 'none', 'windows': 'none', 'textures': {'wall': 'cnb'}}],
                       'notes': "Rebase (CHANGES X1-2): the Temple of Yak's door moved to X2; its rise keeps a ruin."})
    structures.append({'id': 'thing:shrine_chest', 'kind': 'chest', 'at': [30.5, 97.6], 'title': 'Chest',
                       'chest': {'level': 1, 'random_items': 3}})
    for i, (d, at) in enumerate([('7dec20', (28.9, 99.1)), ('7dec18', (32.2, 99.3)), ('dec06', (29.2, 99.4)),
                                 ('7rock08', (32.6, 96.6))]):
        structures.append({'id': 'thing:shrine_dress_%d' % (i + 1), 'kind': 'decoration', 'decoration': d,
                           'at': list(at)})
    # the ruined cottage in the south meadow, the grave field below it, the watchtower by the orchard road's end
    structures.append({'id': 'thing:ruined_cottage', 'kind': 'building', 'at': [54.5, 82.5], 'size': [2, 1.5],
                       'kit': 'stone', 'door': 'none', 'title': 'Ruined cottage',
                       'ruin': {'height': [96, 320], 'gaps': 0.35, 'thickness': 32, 'seed': 5},
                       'parts': [{'id': 'r', 'at': [64, 64], 'size': [896, 640], 'wall_height': 320, 'roof': 'none',
                                  'windows': 'alternate'}]})
    structures.append({'id': 'thing:cottage_chest', 'kind': 'chest', 'at': [55.4, 83.2], 'title': 'Chest',
                       'chest': {'level': 1, 'random_items': 2}})
    for i, at in enumerate([(59.2, 97.4), (60.4, 97.0), (61.6, 97.6), (59.6, 98.8), (61.0, 99.2)]):
        structures.append({'id': 'thing:grave_%d' % (i + 1), 'kind': 'decoration',
                           'decoration': 'rock65', 'at': list(at), 'title': 'Grave',
                           'effects': [{'text': 'An old grave. The name is worn away.'}]})
    structures.append({'id': 'thing:grave_chest', 'kind': 'chest', 'at': [62.6, 98.4], 'title': 'Grave goods',
                       'chest': {'level': 1, 'random_items': 2}})
    structures.append({'id': 'thing:watchtower', 'kind': 'building', 'at': [96.5, 38.5], 'size': [2, 2],
                       'kit': 'castle', 'door': 'none', 'title': 'Ruined watchtower',
                       'ruin': {'height': [256, 768], 'gaps': 0.3, 'thickness': 48, 'seed': 4},
                       'parts': [{'id': 't', 'shape': 'round', 'at': [512, 512], 'radius': 352, 'sides': 10,
                                  'wall_height': 768, 'roof': 'none', 'windows': 'none', 'textures': {'wall': 'cnb'}}]})
    structures.append({'id': 'thing:watchtower_chest', 'kind': 'chest', 'at': [99.0, 40.0], 'title': 'Chest',
                       'chest': {'level': 1, 'random_items': 2}})
    structures.append({'id': 'thing:ring_chest', 'kind': 'chest', 'at': [80.6, 58.2], 'title': 'Offerings',
                       'chest': {'level': 1, 'random_items': 2}})
    # Wells (CHANGES X1-7 asks 4 more; TOWN_FEEL's wells and fountains on the map are 3-8 and the town has 5 and the
    # land 3: one more, the shepherd's spring in the hills, making 9 with the square's fountain; town_feel counts 8)
    structures.append(T.well('thing:well_spring', (66.0, 16.0)))
    structures[-1]['title'] = "Shepherd's spring"
    structures[-1]['effects'] = [{'add': {'var': 'SP', 'value': 10}}, {'text': '+10 Spell points'}]
    # Camps with a fire (CHANGES X1-7: 4): the hunters' (above), travellers by the orchard road, woodcutters in the
    # west meadow, the old campfire in the south (wild places); the orc camps are fights, not counted.
    for i, (d, at) in enumerate([('cmpfyr00', (92.0, 41.6)), ('bigbarel', (93.0, 41.0)), ('smlbarel', (93.25, 41.25)),
                                 ('7dec21', (91.0, 40.9))]):
        structures.append({'id': 'thing:travellers_camp_%d' % (i + 1), 'kind': 'decoration', 'decoration': d,
                           'at': list(at), 'title': "Travellers' campfire" if i == 0 else None})
        if i:
            del structures[-1]['title']
    structures.append({'id': 'thing:travellers_tent', 'kind': 'tent', 'at': [89.6, 40.2], 'size': [768, 640],
                       'height': 352, 'open': True, 'title': "Travellers' tent"})
    for i, (d, at) in enumerate([('cmpfyr00', (34.0, 68.0)), ('stump5a', (35.2, 67.4)), ('stump5a', (33.0, 69.0)),
                                 ('7dec16', (35.0, 68.8)), ('7dec16', (35.6, 69.2))]):
        structures.append({'id': 'thing:woodcutters_camp_%d' % (i + 1), 'kind': 'decoration', 'decoration': d,
                           'at': list(at)})
    structures[-5]['title'] = "Woodcutters' campfire"
    # Small places where the land ran more than 6,000 without a place or a fight (CHANGES X1-7; measure.py's map of
    # the gaps): a wayside shrine on the west hills' foot, a cairn by the north road, a fisherman's shelter on the
    # pond, the rim lookout (the signature view's end), a sheepfold in the south meadow, a burned farmstead.
    structures.append({'id': 'thing:wayside_shrine', 'kind': 'decoration', 'decoration': 'ped01', 'at': [28.0, 41.6],
                       'title': 'Wayside shrine',
                       'effects': [{'text': 'A wayside shrine to the Spring Druid. Travellers leave flowers here.'}]})
    structures.append({'id': 'thing:north_cairn', 'kind': 'decoration', 'decoration': '7rock04', 'at': [71.6, 28.6],
                       'title': 'Cairn', 'effects': [{'text': 'A cairn of piled stones. Scratched on the top one: '
                                                             '"Orcs past here."'}]})
    structures.append(T.shed('thing:fisher_shelter', (70.5, 55.5), [1, 1], 0, kit='poor', open_=True, roof='hip',
                             title="Fisherman's shelter"))
    for i, (d, at) in enumerate([('smlbarel', (71.65, 56.65)), ('7dec21', (71.35, 56.7))]):
        structures.append({'id': 'thing:fisher_dress_%d' % (i + 1), 'kind': 'decoration', 'decoration': d,
                           'at': list(at)})
    structures.append({'id': 'thing:rim_lookout', 'kind': 'decoration', 'decoration': '7rock04', 'at': [101.6, 53.0],
                       'title': 'The edge of the world',
                       'effects': [{'text': 'The meadow ends in a white cliff. Far below, stars turn in the dark.'}]})
    structures.append(T.fence('thing:sheepfold', [[49.0, 73.5], [52.0, 73.5], [52.0, 75.5], [49.0, 75.5]],
                              closed=True))
    structures.append({'id': 'thing:sheepfold_hay', 'kind': 'decoration', 'decoration': 'haybale2', 'at': [50.4, 74.4],
                       'title': 'Sheepfold', 'effects': [{'text': 'An empty sheepfold. The sheep went to Vertigo when '
                                                                 'the orcs came down.'}]})
    structures.append({'id': 'thing:burned_farm', 'kind': 'building', 'at': [50.5, 100.5], 'size': [2, 1.5],
                       'kit': 'timber', 'door': 'none', 'title': 'Burned farmstead',
                       'ruin': {'height': [64, 256], 'gaps': 0.45, 'thickness': 32, 'seed': 9},
                       'parts': [{'id': 'r', 'at': [64, 64], 'size': [896, 640], 'wall_height': 256, 'roof': 'none',
                                  'windows': 'alternate'}]})
    structures.append({'id': 'thing:eel_traps', 'kind': 'decoration', 'decoration': '7dec21', 'at': [90.6, 64.6],
                       'title': 'Eel traps', 'effects': [{'text': 'Wicker eel traps, staked in the stream. Empty.'}]})
    structures.append({'id': 'thing:bog_bones', 'kind': 'decoration', 'decoration': '7dec18', 'at': [95.0, 104.4],
                       'title': 'Bones in the bog', 'effects': [{'text': "A mule's bones, half sunk in the bog. Its "
                                                                        "packs are long gone."}]})
    # A3's hooks that need things of their own (CHANGES X1-10, X1-11; QUESTS Q-C20, Q-C21): the bone whistle in the
    # creek mud upstream of the bridge, four Phirna plants in Toad Meadow, the gate sign at the west gate, the two
    # boards of X1-11. On the stand-in they show their texts; in the world they call the hooks.
    structures.append({'id': 'thing:creek_whistle', 'kind': 'decoration', 'decoration': '7rock01', 'at': [36.0, 49.6],
                       'title': 'Something in the mud', **({'effects': hook('q-c20.whistle')} if IN_WORLD else {
                           'condition': {'not': {'qbit': QBITS['q-c20.whistle_found']}},
                           'effects': [{'qbit': QBITS['q-c20.whistle_found']}] + hook('q-c20.whistle'),
                           'else_effects': [{'text': 'Only mud.'}]})})
    for i, at in enumerate([(76.0, 84.5), (90.5, 78.5), (82.5, 96.5), (97.5, 88.5)]):
        structures.append({'id': 'thing:phirna_%d' % (i + 1), 'kind': 'decoration', 'decoration': 'plant02',
                           'at': list(at), 'title': 'Phirna plant', 'effects': hook('q-c21.phirna_plant')})
    structures.append({'id': 'thing:gate_sign', 'kind': 'sign', 'at': [40.2, 46.6], 'height': 224, 'width': 160,
                       'title': 'Sign', **({'effects': hook('m2.gate_sign')} if IN_WORLD else {
                           'condition': {'not': {'qbit': QBITS['m2.done']}},
                           'effects': [{'text': HOOKS['m2.gate_sign']['states'][-1]['text']}],
                           'else_effects': [{'text': HOOKS['m2.gate_sign']['states'][0]['text']}]})})
    structures.append({'id': 'thing:sign_rent', 'kind': 'sign', 'at': [47.6, 45.4], 'height': 192, 'width': 128,
                       'title': 'Sign board', 'effects': hook('x1.sign_rent')})
    structures.append({'id': 'thing:sign_joe', 'kind': 'sign', 'at': [59.4, 57.6], 'height': 192, 'width': 128,
                       'title': 'Sign board', 'effects': hook('x1.sign_joe')})
    if IN_WORLD and not X7_LIVE:
        structures.append({'id': 'thing:north_road_end', 'kind': 'sign', 'at': [70.4, 3.0], 'height': 224, 'width': 160,
                           'title': 'Sign', 'effects': [{'text': 'Rockfall. The road to Mount Firestone is closed.'}],
                           'notes': 'X7 is not built: the north edge has no travel until it is.'})
    # One stat challenge (CHANGES X1-7)
    structures.append({'id': 'thing:great_boulder', 'kind': 'decoration', 'decoration': 'rock68', 'at': [58.6, 88.4],
                       'title': 'A great boulder', 'condition': {'stat': {'name': 'BaseMight', 'at_least': 15}},
                       'once': True,
                       'effects': [{'gold': 150}, {'text': 'You heave the boulder over: a pouch of coins lies under '
                                                           'it. +150 gold'}],
                       'else_effects': [{'text': 'The boulder does not budge (Might 15).'}]})
    # Crodo's bottle in Pitchfork Creek (QUESTS M1, CHANGES X1-10; hook m1.crodo_bottle_creek)
    structures.append({'id': 'thing:crodo_bottle', 'kind': 'decoration', 'decoration': '7dec41', 'at': [26.0, 48.8],
                       'title': 'Bottle', **({'effects': hook('m1.crodo_bottle_creek')} if IN_WORLD else {
                       'condition': {'not': {'qbit': 'crodo_bottle_creek'}},
                       'effects': [{'qbit': 'crodo_bottle_creek'}] + hook('m1.crodo_bottle_creek', window=True),
                       'else_effects': [{'text': HOOKS['m1.crodo_bottle_creek']['else_text']}]}),
                       'notes': 'Hook m1.crodo_bottle_creek (A3): the text is the original line (QUESTS M1).'})
    # Vertigo's mirror (WORLD_DESIGN 3.3, 5.1; hook mirror.vertigo: A4's mirror network, A3's lines)
    structures.append({'id': 'thing:mirror', 'kind': 'portal', 'at': [56.5, 48.3], 'radius': 112, 'sides': 12,
                       'turn': 90, 'title': 'Magic Mirror', 'textures': {'membrane': {'texture': 'xmirror'}},
                       **({'effects': [{'lua': 'Xeen.useMirror(%d, eventId, continueStep)' % HOUSE_MIRROR}]} if IN_WORLD else
                          {'effects': [{'text': 'The mirror shows the square, and you in it. (The mirrors of '
                                                'Cloudside are not joined yet.)'}]}),
                       'notes': 'Hook mirror.vertigo: the town mirror (A4 makes it a free transport house).'})
    actors = []
    # Townsfolk: D-96's villagers (villagers.yml, villagers_spots.yml), in the 23 places of the second pass's
    # townsfolk in the list (actor indices stay); several stood by doors and Mylo
    actors += V.slots(23)
    # Guards (pass five, the user's walk: "have some guards inside the walls?"). Measured on the shipped towns' actors
    # (output/studio_cal/x1/pass5/guards/measure.txt): Harmondale 7 guards to 30 townsfolk, New Sorpigal 5 to 38,
    # Tatalia 8 to 33, Ravenshore 20 to 45; about half walk the streets alone (300-2,000 from a house door, 2,000-4,700
    # apart), the rest stand in pairs 350-850 apart at gates and bridges. Here: a pair at each gate (were singles) and
    # five alone on the streets inside the walls, 13 to 23 townsfolk.
    for (x, y) in [(52, 36.9), (53.1, 36.9), (52, 51.0), (53.0, 50.7), (40.4, 44.6), (40.4, 43.5), (63.6, 45.6),
                   (63.6, 46.7), (47.2, 44.4), (56.4, 47.6), (59.8, 44.9), (50.6, 55.4), (45.8, 40.6)]:
        actors.append({'monster': '404', 'at': [x, y], 'spread': 0, 'group': 51})
    # The orc outposts: four orcs each (rebase: the per-map total; pass six had 4, 6, 4). Placed, so they do not
    # refill; the burnable camps and XD-05's drums are phase 1 (QUESTS 4.3).
    for i, (x, y) in enumerate([(30, 29), (56, 23), (97, 31)]):
        actors.append({'monster': PLACED['orcs'], 'at': [x, y], 'count': 4, 'spread': 1.2, 'group': 60 + i,
                       'hostile': True})
    # Placed groups of the families the three slots cannot carry (rebase): snakes in the marsh, zombies round the
    # ruined shrine; and two lone wanderers (an orc scout on the hill path, a skeleton among the dead trees).
    for i, (fam, (x, y), n, spread) in enumerate([('snakes', (97, 68), 3, 1.0), ('snakes', (76, 101), 2, 0.8),
                                                   ('zombies', (40, 99), 3, 1.0), ('zombies', (21, 95), 2, 0.8),
                                                   ('orcs', (47, 17), 1, 0), ('skeletons', (35, 89), 1, 0)]):
        actors.append({'monster': PLACED[fam], 'at': [x, y], 'count': n, 'spread': spread, 'group': 70 + i,
                       'hostile': True})
    for i, (row, (x, y), n, spread) in enumerate(ROAD_PESTS):
        actors.append({'monster': str(row), 'at': [x, y], 'count': n, 'spread': spread, 'group': 90 + i,
                       'hostile': True})
    # Hostility pass (2026-11-16): MMerge's hostile.txt sets MM7's Dragonflies on the Goblins and the Skeletons (3 one
    # way, 2 the other), so the swarms and the orcs or the dead fought wherever they met. All three families are the
    # party's foes by the table already; they are kept from each other, both ways, every tier.
    if IN_WORLD:
        for i, (npc, (x, y)) in enumerate(NPC_ACTORS):
            # an explicit peasant row: the name 'Peasant' finds row 49, MM7's vampire peasant
            # D-91 (A5 s29): the Spring Druid (4048) on lane S's robed old man, Xeen Elder Druid (11928)
            actors.append({'monster': '11928' if npc == 4048 else '371', 'npc': npc, 'at': [x, y], 'spread': 0,
                           'group': DEREK_GROUP if npc == 4046 else 52})
        # q-c22.derek_camp (A3): Celia (4041) sits at Derek's fire once Q-C22 is done (qbit 112442): a hidden figure in
        # a group of its own (53, "celia_at_fire"), shown by evt:celia_at_fire on entering the map.
        actors.append({'monster': '350', 'npc': 4041, 'at': [42.4, 78.3], 'spread': 0, 'group': CELIA_GROUP,
                       'hidden': True})
    # Rebase: the placed zombies' stand-in (MM7 Ghoul 454-456) is set on the Dragonflies too (3 and 2): kept apart.
    flies, goblins, skeletons, ghouls = [226, 227, 228], [271, 272, 273], [397, 398, 399], [454, 455, 456]
    relations = [{'of': flies, 'toward': kind, 'relation': 'friendly', 'both_ways': True}
                 for kind in goblins + skeletons + ghouls]
    if IN_WORLD:
        relations = []      # the world's relations.yml (A2) holds the families' hostility
    events = ([{'id': 'evt:celia_at_fire', 'trigger': 'load',
                'condition': {'lua': 'XeenQuests.can("q-c22.derek_camp")'},
                'effects': [{'show_actors': CELIA_GROUP}], 'else_effects': [{'hide_actors': CELIA_GROUP}],
                'notes': "Hook q-c22.derek_camp (A3): Celia at Derek's fire after Q-C22, gone once they moved "
                         "(the hook's own condition)."},
               {'id': 'evt:derek_moved', 'trigger': 'load', 'condition': {'qbit': QBITS['q-c22.moved']},
                'effects': [{'hide_actors': DEREK_GROUP}], 'else_effects': [{'show_actors': DEREK_GROUP}],
                'notes': "Hook q-c22.on_darkside (A3): Derek leaves his camp for the Darkside cottage (reads "
                         "q-c22.moved)."}] if IN_WORLD else []) + [
        {'id': 'evt:gunther_errand', 'trigger': 'timer', 'every': 2, 'once': True,
         'effects': hook('m1.opening', window=True),
         'notes': "Hook m1.opening (A3, QUESTS M1; CHANGES X1-9): Crodo's dreams and Gunther's request; once."},
    ]
    sketch = {
        'format': 0, 'grid': 512,
        'notes': ('X1 Vertigo Meadows, L3 sketch written by output/studio_cal/x1/tools/gen.py. Cells [x, y], x '
                  'east, y south. Heights are map units above the water below the rim (0); the meadow and the '
                  'town stand at 640, the creek at 576, the northern hills to about 2,300, the rim cliff at x 104.'),
        'frame': {'playable': [19, 19, 90, 90],
                  'edges': [{'side': 'west', 'span': [42, 50], 'neighbour': 'edge:west'},
                            {'side': 'north', 'span': [66, 72], 'neighbour': 'edge:north'}][:1 if IN_WORLD and not X7_LIVE else 2],
                  'edge': {'height': 1600, 'west': 640, 'east': 0},
                  'rim': rim},
        'heights': heights, 'water': water, 'roads': roads, 'districts': districts, 'points': points,
        'areas': areas, 'views': views, 'scatter': scatter, 'ground': ground, 'structures': structures,
        'actors': V.fill(actors, 'X1'), 'relations': relations + V.relations('X1'), 'events': events,
    }
    # D-93 (A3 s39): no ground item; the rain barrel gives the key (thing:rain_barrel above)
    atmosphere = {'format': 0, 'notes': "World default sky and weather ('fair', light rain by the world chances)."}

    def dump(name, data):
        if name == 'sketch.yml':   # AU's outdoor beds (A5, 2026-11-21; level_generation/projects/xeen/common/beds)
            sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common/beds')
            import beds as _beds
            data = _beds.with_beds(data, 'x1')
        with open(os.path.join(OUT, name), 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)
    dump('project.yml', project)
    if IN_WORLD and not X7_LIVE:
        plan['entrances'] = [e for e in plan['entrances'] if e['id'] != 'entrance:north_road']
        sketch['points'] = [q for q in sketch['points'] if q['id'] != 'entrance:north_road']
    dump('plan.yml', plan)
    # Texture fit (merge point 16): the base course goes down `foundation` (128) in the `base` role, which falls back
    # to the wall; the plaster kit's half-timber panel (hhm2b2, a storey module) then shows 1.5 times up a wall of one
    # storey. A dark seamless stone footing (cwb1) instead.
    for district in sketch['districts']:
        for plot in district.get('plots', []):
            if plot.get('kit') == 'plaster':
                plot.setdefault('textures', {}).setdefault('base', 'cwb1')
    for thing in sketch['structures']:
        if thing.get('kind') == 'building' and thing.get('kit') == 'plaster':
            thing.setdefault('textures', {}).setdefault('base', 'cwb1')
    # F8 (2026-11-21) + F16 (A5 s29, 2026-11-22): the two cave mouths as wide as their rim, the entrance window's
    # trans.txt lines (the shortcuts opened from inside keep the standard window)
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import entrance as EN
    for _note in HD.bury_mouths_sketch(sketch) + EN.apply(sketch, 'x1'):
        print('door:', _note)
    dump('sketch.yml', sketch)
    dump('atmosphere.yml', atmosphere)
    # Points of interest out in the land (CHANGES X1-7: 40-50; the town's own things are listed apart). Written to
    # tools/pois.yml for measure.py (the 6,000 rule: no stretch of road or open land that long without one or a fight).
    POI_REGISTER = [
        ("Joe's warehouse doors", (61, 58)), ('Culvert grate', (61, 54)), ('Red Dwarf Mines', (44, 31)),
        ("The Clan King's shaft", (62, 28)), ('Witch Tower door', (88, 82.4)), ('Orc Caves', (82, 30)),
        ('Travel pyramid', (84, 46)), ('Obelisk', (74, 34)), ('Fountain of Ability', (46, 70)),
        ('Waters of Power', (92, 50)), ('Wishing Well', (94, 92)), ('Shrine of Poison', (26, 82)),
        ('Water Reflector', (102, 96)), ("Orothin's statues", (67.5, 66.5)), ("The Spring Druid's stone", (26, 60)),
        ("Derek's camp", (42, 78)), ("Celia's hut", (44, 86)), ("Oslo's hut", (34, 59)),
        ('Toad Meadow (Myra, Valia)', (76, 72)), ('Orc outpost west', (30, 29)), ('Orc outpost north', (56, 23)),
        ('Orc outpost east', (97, 31)), ('Pitchfork Falls', (104, 60)), ('Signpost, hill fork', (59.2, 33.2)),
        ('Signpost, south fork', (63, 72)), ('Signpost, tower path', (80.6, 73.4)),
        ('Signpost, forest path', (43.2, 82.8)), ('Signpost, orchard road', (81.6, 44.2)), ('Old campfire', (66, 107)),
        ('Fallen stone ring (offerings)', (80.6, 58.2)), ("West road orc camp", (11.5, 41.8)),
        ('North road orc camp', (72.8, 9.2)), ("Smugglers' cache", (102, 24)), ("Drowned peddler's chest", (96, 96)),
        ('Ruined shrine', (30.5, 97.5)), ('Ruined cottage', (55.5, 83.2)), ('Grave field', (60.5, 98)),
        ('Ruined watchtower', (97.5, 39.5)), ("Hunters' camp", (23.5, 62)), ("Travellers' camp", (91, 41)),
        ("Woodcutters' camp", (34, 68)), ("Shepherd's spring", (66, 16)),
        ('A great boulder', (58.6, 88.4)), ("Crodo's bottle", (26, 48.8)),
        ('Wayside shrine', (28, 41.6)), ('Cairn by the north road', (71.6, 28.6)), ("Fisherman's shelter", (71, 56)),
        ('The edge of the world', (101.6, 53)), ('Sheepfold', (50.5, 74.5)), ('Burned farmstead', (51.5, 101.2)),
        ('Eel traps', (90.6, 64.6)), ('Bones in the bog', (95, 104.4))]
    TOWN_POIS = [('Signpost, west gate', (37.6, 45.2)), ('Money tree', (55.8, 47.6)), ('Magic Mirror', (56.5, 48.3)), ("Mayor Gunther's notice", (53.2, 45.2)),
                 ('Rain barrel', (61.8, 59.65))]
    print('points of interest out in the land: %d (CHANGES X1-7: 40-50); in town %d' % (len(POI_REGISTER),
                                                                                          len(TOWN_POIS)))
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pois.yml'), 'w') as f:
        yaml.safe_dump([{'name': n, 'at': list(a)} for n, a in POI_REGISTER + TOWN_POIS], f, sort_keys=False)
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'house_doors.yml'), 'w') as f:
        yaml.safe_dump([{'title': t, 'house': h, 'door': list(d), 'facing': fc, 'building': b, 'index': ix}
                        for t, h, d, fc, b, ix in house_doors], f, sort_keys=False)

if __name__ == '__main__':
    build()
