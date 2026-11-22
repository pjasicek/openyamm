"""DD-12 Dungeon of Lost Souls: writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd12/L*) from one place.

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd12), phase 4, decider D-42.
Plan frame: x east, y north, z 0 on L1's floor (the ruined tower's base). Five floors going down 640 apart (L1 0,
L2 -640, L3 -1280, L4 -1920, L5 -2560); rooms 512 high (the Soul Maze 384), so every ceiling is at least 64 under the
floor above. Four flights of 20 steps, 320 wide and 1280 long, each with a plan of its own on both of its floors: L1-L2
x 2432-2752 (north-south), L2-L3 y -2208..-1888 at x -1792..-512, L3-L4 at x 2304-3584, L4-L5 y -2464..-2144 at x
x 6912-7264 (north-south). Gates 2-4 stand at the head of those flights. The lift shaft (x -2560..-2048, y 1056..1568)
is one closed room from L5 to above L1, open only to the aviary (L5) and the lift head (L1, at the hall of storage's
west end).
The entrance hall is round (radius 547, flat chords 384 wide north, south, east and west), centred on (0, 0); its
double door to D4 is the south chord (y -512), the first gate the north chord.
The Soul Maze (L5): the letters S H E L T E M in corridors 256 wide on a 256 grid, 3 cells by 5 (M 5 by 5), 256
apart, bottom at y 1792, from x -864 (S) to 6560 (M); each letter a room, joined to the next by one bridge cell. The
maze lies north of every other floor's rooms (y 1792-3072), so its walls alone are drawn there on the automap.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import sys
import yaml

R = _REPO_ROOT
OUT = R + '/devdocs/xeen/briefs/dd12'


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.add_representer(Flow, flow_rep)


def F(*a):
    return Flow(a)


def S(texture, w, h, scale=None, **kw):
    d = {'texture': texture, 'size': F(w, h)}
    if scale:
        d['scale'] = scale
    d.update(kw)
    return d


def FIT(texture, w, h):
    return {'texture': texture, 'size': F(w, h), 'fit': True}


def dump(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)


# ---------------------------------------------------------------------------------------------------------------------
# Numbers

MAP_ID = 9165
QBITS = {
    'arrived_once': 117440,      # A3's m24.yml dd12_arrived_once (the map's block 117440-117479)
    'gate1': 117441,             # the map's own: gate N answered Yes (its leaves open, kept over a refill)
    'gate2': 117442,
    'gate3': 117443,
    'gate4': 117444,
    'gate5': 117445,
    'bird_freed': 111480,        # M24 (A3): m24.songbird sets it; the lift runs
    'throne_done': 113500,       # Q-D25 (A3)
}
ITEMS = {'lost_souls_key': 12344, 'songbird_of_serenity': 12526}
MINO, GORGON, LORD = 11090, 11091, 11092

FL = [0, -640, -1280, -1920, -2560]
H = 512             # a room's height (ceiling 128 under the next floor up)
MAZE_H = 384

# D4's arrival for this map's door (installed assets_dev/worlds/xeen/maps/xeen_d4.studio.yml, A6).
D4_DOOR = [4096, -3072, 1376]

# ---------------------------------------------------------------------------------------------------------------------
# Textures (D-42 / the graph): MM7 The Maze d02 (cwb grey brick, cwb1 red rock, eswamp ivy for the Soul Maze, cfb1
# floors, ceb1sa and t5s1c ceilings, c1d1 grate doors, trim12_32); the entrance hall in D4's towers kit (hkm2b rubble
# masonry, the hkm1dl/hkm1dr door wings outside); A8's three new pictures xlsplaque, xlsgate, xlsglass; XD-04's xwcage
# bars; the Soul Waters in mm7 7wtrtyl.

BRICK = S('cwb', 128, 256)
ROCK = S('cwb1', 128, 256)
IVY = S('eswamp', 128, 128)
RFLOOR = S('cfb1', 128, 128)
FLAGS = S('t5s1fl', 128, 128)
GREEN = S('ceb1sa', 128, 256)
CARVED = S('t5s1c', 128, 128)
GRATE = FIT('c1d1', 128, 256)
TRIM = S('trim12_32', 32, 64)
RUBBLE = S('hkm2b', 128, 256)
RUBBLE_DARK = S('hkm2bs', 128, 256)
CAGE = S('xwcage', 128, 256)
CAGE_FIT = FIT('xwcage', 128, 256)
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}
PLAQUE = FIT('xlsplaque', 256, 64)
GATE = FIT('xlsgate', 128, 256)
GLASS = FIT('xlsglass', 128, 128)
NICHE = FIT('t5d1', 128, 256)            # d02's carved iron-and-stone panel: the Soul Waters' niches, once per face
DIAL = FIT('t5s1c', 128, 128)            # the carved rosette, once per dial face
WING_L = FIT('hkm1dl', 128, 256)
WING_R = FIT('hkm1dr', 128, 256)

THEMES = [
    {'id': 'theme:tower', 'wall': RUBBLE, 'floor': RFLOOR,
     'ceiling': {'texture': 'ceb1sa', 'size': F(128, 256), 'sky': True}, 'reveal': RUBBLE,
     'door': GRATE,
     'notes': "The ruined tower's base: D4's towers kit (hkm2b rubble masonry in timber frames), the red rock floor "
              "cfb1, open to the Darkside sky (sky faces)."},
    {'id': 'theme:brick', 'wall': BRICK, 'floor': RFLOOR, 'ceiling': GREEN, 'reveal': BRICK, 'door': GRATE,
     'notes': "The Maze's grey brick cwb (the hourglass niches' own stone), red rock floors cfb1, green stone "
              "ceilings ceb1sa."},
    {'id': 'theme:rock', 'wall': ROCK, 'floor': RFLOOR, 'ceiling': GREEN, 'reveal': ROCK, 'door': GRATE,
     'notes': "Rooms cut into the isle's red rock cwb1: the pool, the flooded walk, the barracks, the reserve."},
    {'id': 'theme:hall', 'wall': BRICK, 'floor': FLAGS, 'ceiling': CARVED, 'reveal': BRICK, 'door': GRATE,
     'notes': "The set-piece halls (gates, statues, the aviary): grey brick, flags t5s1fl, the carved ceiling t5s1c."},
    {'id': 'theme:maze', 'wall': IVY, 'floor': RFLOOR, 'ceiling': GREEN, 'reveal': IVY, 'door': GRATE,
     'notes': "The Soul Maze: MM7 Maze's ivy-grown walls eswamp, red rock floor, green stone ceiling."},
    {'id': 'theme:stair', 'wall': BRICK, 'floor': RFLOOR, 'ceiling': GREEN, 'reveal': BRICK, 'door': GRATE,
     'notes': "The four flights and the lift shaft: grey brick, red rock treads."},
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms


def rect(x0, y0, x1, y1):
    return [F(x0, y0), F(x1, y0), F(x1, y1), F(x0, y1)]


def panel_xy(box, wall, centre, length, surface, bottom, height, pid=None, notes=None):
    """A panel on a rectangular room's wall, centred at `centre` (x on south/north walls, y on east/west walls)."""
    x0, y0, x1, y1 = box
    start = {'south': centre - length / 2 - x0, 'east': centre - length / 2 - y0,
             'north': x1 - (centre + length / 2), 'west': y1 - (centre + length / 2)}[wall]
    d = {}
    if pid:
        d['id'] = 'panel:' + pid
    d.update({'offset': int(start), 'length': length, 'bottom': bottom, 'height': height, 'surface': surface})
    if notes:
        d['notes'] = notes
    return d


def plat(i, at, size, rise, surface, top=None, **kw):
    d = {}
    if i:
        d['id'] = 'platform:' + i
    d.update({'at': F(*at), 'size': F(*size), 'rise': rise, 'surface': surface, 'top_surface': top or surface})
    d.update(kw)
    return d


def polyomino(cells, x0, y0, c=256):
    """The counter-clockwise outline of a set of grid cells (col, row) with cell (0, 0) at (x0, y0)."""
    edges = {}
    for (i, j) in cells:
        a, b, cc, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
        for e in ((a, b), (b, cc), (cc, d), (d, a)):
            if (e[1], e[0]) in edges:
                del edges[(e[1], e[0])]
            else:
                edges[e] = True
    nxt = {}
    for (p, q) in edges:
        assert p not in nxt, ('pinch', p)
        nxt[p] = q
    start = min(nxt)
    pts = [start]
    p = nxt[start]
    while p != start:
        pts.append(p)
        p = nxt[p]
    out = []
    n = len(pts)
    for k in range(n):
        a, b, cc = pts[k - 1], pts[k], pts[(k + 1) % n]
        if (b[0] - a[0]) * (cc[1] - b[1]) - (b[1] - a[1]) * (cc[0] - b[0]) != 0:
            out.append(b)
    return [F(x0 + i * c, y0 + j * c) for (i, j) in out]


# Boxes of the rectangular rooms (x0, y0, x1, y1)
B = {
    # L1 (0)
    'gallery1': (-2048, 544, 2304, 1024),
    'vault1': (-640, 1056, -128, 1568),
    'store_a': (384, 1056, 1344, 1664),
    'store_b': (1376, 1056, 2304, 1664),
    'store_c': (768, -128, 1536, 512),
    'store_d': (1568, -128, 2304, 512),
    'stair1': (2336, -128, 2880, 1664),
    'lift_head': (-2560, 544, -2080, 1024),
    'shaft': (-2560, 1056, -2048, 1568),
    # L2 (-640)
    'statue_hall2': (1984, -2560, 3200, -1408),
    'north_walk2': (384, -1920, 1984, -1536),
    'south_walk2': (384, -2560, 1984, -2176),
    'cell1': (512, -3072, 896, -2592),
    'cell2': (1024, -3072, 1408, -2592),
    'cell3': (1536, -3072, 1920, -2592),
    'gate_hall2': (-480, -2560, 384, -1536),
    # L3 (-1280)
    'pool3': (-3072, -2816, -1792, -1280),
    'dials3': (-1760, -1856, 256, -1344),
    'soul3': (288, -2048, 1248, -1024),
    'flooded3': (-1792, -3072, 256, -2560),
    'negative3': (288, -3328, 1280, -2304),
    'gate_hall3': (1280, -2560, 2272, -1536),
    # L4 (-1920)
    'plaque4': (3584, -2816, 4608, -1280),
    'levers4': (4640, -2816, 6400, -1280),
    'barracks4': (4096, -1248, 5632, -512),
    'reserve4': (4864, -3840, 6144, -2848),
    'gate_hall4': (6432, -2816, 7392, -1792),
    # L5 (-2560)
    'statues5': (6560, -480, 7584, 2048),
    'maze_dead': (4256, 1248, 5024, 1760),
    'gate_hall5': (-1888, 1600, -864, 2624),
    'aviary': (-3424, 1600, -1920, 3008),
}
# Flights (x0, y0, x1, y1, lower floor, toward the upper end)
FLIGHTS = {
    'flight1': ((2432, -1408, 2784, -128), FL[1], 'north'),
    'flight2': ((-1792, -2224, -512, -1872), FL[2], 'east'),
    'flight3': ((2304, -2224, 3584, -1872), FL[3], 'west'),
    'flight4': ((6912, -1760, 7264, -480), FL[4], 'south'),
}

# The entrance hall: a 16-sided round room, radius 547, with flat chords 384 wide at the four compass points.
ENTRY = [(-192, -512), (192, -512), (329, -437), (437, -329), (512, -192), (512, 192), (437, 329), (329, 437),
         (192, 512), (-192, 512), (-329, 437), (-437, 329), (-512, 192), (-512, -192), (-437, -329), (-329, -437)]
E_SOUTH, E_EAST, E_NORTH, E_WEST = 0, 4, 8, 12

# The Soul Maze: letter cells (col, row), the bridge cell to the letter before it (col -1) included.
MAZE_Y0 = 1792
C = 256
LETTERS = [
    ('maze_s', 'S', -864, [(0, 4), (1, 4), (2, 4), (0, 3), (0, 2), (1, 2), (2, 2), (2, 1), (0, 0), (1, 0), (2, 0)]),
    ('maze_h', 'H', 160, [(0, r) for r in range(5)] + [(2, r) for r in range(5)] + [(1, 2), (-1, 4)]),
    ('maze_e', 'E', 1184, [(0, r) for r in range(5)] + [(1, 4), (2, 4), (1, 2), (2, 2), (1, 0), (2, 0), (-1, 1)]),
    ('maze_l', 'L', 2208, [(0, r) for r in range(5)] + [(1, 0), (1, 1), (2, 0), (-1, 4)]),
    ('maze_t', 'T', 3232, [(0, 4), (1, 4), (2, 4)] + [(1, r) for r in range(4)] + [(0, 0), (-1, 0)]),
    ('maze_e2', 'E', 4256, [(0, r) for r in range(5)] + [(1, 4), (2, 4), (1, 2), (2, 2), (1, 0), (2, 0), (-1, 4)]),
    ('maze_m', 'M', 5280, [(c, 4) for c in range(5)] + [(c, r) for c in (0, 2, 4) for r in range(4)] + [(-1, 2)]),
]
LX = {k: x for k, _, x, _ in LETTERS}
BRIDGE_ROW = [None, 4, 1, 4, 0, 4, 2]   # the row of each letter's bridge to the letter before it


def cell(letter, col, row):
    """The centre of a maze cell."""
    return (LX[letter] + C * col + C // 2, MAZE_Y0 + C * row + C // 2)


def flight(i, name, notes):
    (x0, y0, x1, y1), f0, toward = FLIGHTS[i]
    return {'id': 'room:' + i, 'name': name, 'outline': rect(x0, y0, x1, y1), 'floor': f0,
            'slope': {'to': f0 + 640, 'toward': toward, 'steps': 20}, 'ceiling': f0 + 640 + 448,
            'theme': 'theme:stair', 'ambient': 12, 'notes': notes}


def box_room(i, name, floor, theme, ambient, notes, ceiling=None, **kw):
    x0, y0, x1, y1 = B[i]
    d = {'id': 'room:' + i, 'name': name, 'outline': rect(x0, y0, x1, y1), 'floor': floor,
         'ceiling': ceiling or floor + H, 'theme': theme, 'ambient': ambient}
    d.update(kw)
    d['notes'] = notes
    return d


def glass_wall(key, wall, centre, pid):
    return {'wall': wall, 'panels': [panel_xy(B[key], wall, centre, 192, GLASS, 128, 192, pid=pid,
                                              notes="An hourglass in a niche of grey brick (xlsglass).")]}


def lever_post(i, at):
    return plat('post_' + i, at, (48, 48), 96, TRIM, TRIM, notes="A lever post of dark timber.")


STATUE_Y = (-64, 512, 1088, 1664)
LEVER_COLS = (5120, 5504, 5888)
LEVER_ROWS = (-1600, -1920, -2240, -2560)      # north to south

# Alamar's four statues on plinths (L5), the speaking statue (L2), the dial statue (L3), the plaque's statue (L4).
ROOMS = [
    # ---- L1 (0): the ruined tower's base and Minotaur Storage
    {'id': 'room:entry', 'name': 'Entrance hall', 'outline': [F(*p) for p in ENTRY], 'floor': FL[0], 'ceiling': 768,
     'theme': 'theme:tower', 'ambient': 18,
     'walls': [{'wall': E_NORTH, 'panels': [{'id': 'panel:plaque', 'offset': 0, 'length': 384, 'bottom': 384,
                                             'height': 96, 'surface': PLAQUE,
                                             'notes': "The carved plaque over the first gate (xlsplaque)."}]}],
     'notes': "The ruined tower's base, round, 1,094 across, open to the Darkside sky; the double door to the Isle "
              "in the south chord, the first gate under the carved plaque in the north chord."},
    box_room('gallery1', 'Hall of storage', FL[0], 'theme:brick', 16,
             "A long hall in grey brick from the first gate east to the storerooms' doors; the hourglass vault's "
             "panel in its west end."),
    box_room('vault1', 'Hourglass vault', FL[0], 'theme:brick', 14,
             "The minotaurs' strongbox behind the panel that grinds open once all four hourglasses are turned."),
    box_room('store_a', 'Minotaur Storage (north-west)', FL[0], 'theme:brick', 14,
             "A storeroom: sacks and barrels along the walls, an hourglass in a niche on the north wall.",
             store=True, walls=[glass_wall('store_a', 'north', 640, 'glass_a')]),
    box_room('store_b', 'Minotaur Storage (north-east)', FL[0], 'theme:brick', 14,
             "Barrels in pairs and racks of salted meat; an hourglass in a niche on the north wall.",
             store=True, walls=[glass_wall('store_b', 'north', 1824, 'glass_b')]),
    box_room('store_c', 'Minotaur Storage (south-west)', FL[0], 'theme:brick', 14,
             "Straw and fodder in the corners; an hourglass in a niche on the south wall.",
             store=True, walls=[glass_wall('store_c', 'south', 1152, 'glass_c')]),
    box_room('store_d', 'Minotaur Storage (south-east)', FL[0], 'theme:brick', 14,
             "A heap of bones and broken crates; an hourglass in a niche on the south wall.",
             store=True, walls=[glass_wall('store_d', 'south', 1920, 'glass_d')]),
    box_room('stair1', 'Stair head', FL[0], 'theme:brick', 14,
             "The head of the stair down to L2 in its south wall; doors from the north storerooms, an arch from the "
             "south-east one."),
    box_room('lift_head', 'Lift head', FL[0], 'theme:brick', 14,
             "At the hall of storage's west end: the iron cage's upper stop at the top of a closed shaft (its gate "
             "in the north wall)."),
    {'id': 'room:shaft', 'name': 'Lift shaft', 'outline': rect(*B['shaft']), 'floor': FL[4], 'ceiling': 448,
     'theme': 'theme:stair', 'ambient': 10,
     'notes': "A closed shaft 512 square from the aviary (L5) to the lift head (L1): no opening on L2-L4."},
    flight('flight1', 'Stair to the cells', "Twenty steps from the stair head (L1) down south to the hall of the "
                                            "statue (L2)."),
    # ---- L2 (-640): the cells
    box_room('statue_hall2', 'Hall of the statue', FL[1], 'theme:hall', 16,
             "The stair's foot; the speaking statue on its plinth in the middle; the stuck lever by it.",
             platforms=[plat('plinth2', (2592, -2048), (192, 192), 64, BRICK, FLAGS,
                             notes="The speaking statue's plinth.")]),
    box_room('north_walk2', 'North walk', FL[1], 'theme:brick', 14,
             "A walk round the cell block's north side; the first cell's lever on its north wall."),
    box_room('south_walk2', 'South walk', FL[1], 'theme:brick', 14,
             "The cell row: three barred cells off its south side; the second cell's lever on its north wall."),
    box_room('cell1', 'First cell', FL[1], 'theme:rock', 10,
             "A cell behind bars: the bones of an adventurer who answered No."),
    box_room('cell2', 'Second cell', FL[1], 'theme:rock', 10,
             "A cell behind bars: more bones."),
    box_room('cell3', 'Third cell', FL[1], 'theme:rock', 10,
             "A cell behind bars: a chest the minotaurs took from the last ones."),
    box_room('gate_hall2', 'Second gate', FL[1], 'theme:hall', 16,
             "The second gate (two leaves, xlsgate) in the west wall at the stair's head; the third cell's lever."),
    flight('flight2', 'Stair to the pool', "Twenty steps behind the second gate, down west to L3's pool."),
    # ---- L3 (-1280): the Soul Waters
    box_room('pool3', 'Stagnant pool', FL[2], 'theme:rock', 14,
             "A sunken pool of stagnant water in a stone kerb; the stair's foot in the east wall.",
             platforms=[plat('pool', (-2560, -2048), (640, 768), 48, ROCK, WATER,
                             notes="The pool's kerb round the stagnant water.")]),
    box_room('dials3', 'Gallery of dials', FL[2], 'theme:hall', 16,
             "Four dials in the north wall, a statue at the west end that tells what to do with them.",
             walls=[{'wall': 'north', 'panels': [
                 panel_xy(B['dials3'], 'north', x, 128, DIAL, 160, 128, pid='dial%d' % n,
                          notes="A carved dial, 1 to 4 and round.")
                 for n, x in enumerate((-1152, -768, -384, 0), 1)]}],
             platforms=[plat('plinth3', (-1500, -1760), (192, 192), 64, BRICK, FLAGS,
                             notes="The dial statue's plinth.")]),
    box_room('soul3', 'Soul Waters', FL[2], 'theme:hall', 18,
             "A wall fountain in a carved niche on the north wall and its lever beside it.",
             walls=[{'wall': 'north', 'panels': [panel_xy(B['soul3'], 'north', 768, 192, NICHE, 0, 384,
                                                          pid='niche3', notes="The Soul Waters' niche.")]}],
             platforms=[plat('soul_basin3', (768, -1152), (256, 192), 64, BRICK, WATER,
                             notes="The Soul Waters' basin.")]),
    box_room('flooded3', 'Flooded walk', FL[2], 'theme:rock', 12,
             "A long walk round the pool's south side; seep water in a channel along its south wall.",
             platforms=[plat(None, (-768, -2992), (1792, 128), 16, ROCK, WATER,
                             notes="A channel of seep water along the south wall.")]),
    box_room('negative3', 'Negative Soul Waters', FL[2], 'theme:rock', 14,
             "A second fountain of black water in a niche on the south wall; a chest by the east wall.",
             walls=[{'wall': 'south', 'panels': [panel_xy(B['negative3'], 'south', 640, 192, NICHE, 0, 384,
                                                          pid='niche_neg', notes="The black waters' niche.")]}],
             platforms=[plat('neg_basin', (640, -3200), (256, 192), 64, ROCK, WATER,
                             notes="The Negative Soul Waters' basin.")]),
    box_room('gate_hall3', 'Third gate', FL[2], 'theme:hall', 16,
             "The third gate (two leaves) in the east wall at the stair's head."),
    flight('flight3', 'Stair to the Reserve', "Twenty steps behind the third gate, down east to L4."),
    # ---- L4 (-1920): the Reserve
    box_room('plaque4', 'Hall of the plaque', FL[3], 'theme:hall', 16,
             "The stair's foot; a statue on a plinth with the lever riddle's plaque.",
             platforms=[plat('plinth4', (4096, -1920), (256, 192), 64, BRICK, FLAGS,
                             notes="The statue's plinth with its plaque.")]),
    box_room('levers4', 'Hall of levers', FL[3], 'theme:hall', 18,
             "Twelve lever posts in four rows of three, north to south, with clear aisles between the rows.",
             platforms=[lever_post('%d%d' % (r + 1, c + 1), (x, y))
                        for r, y in enumerate(LEVER_ROWS) for c, x in enumerate(LEVER_COLS)]),
    box_room('barracks4', "Minotaurs' barracks", FL[3], 'theme:rock', 14,
             "Straw pallets along the walls and a trough; a purse under the straw.",
             platforms=[plat('trough', (4864, -608), (512, 96), 48, ROCK, WATER, notes="A stone trough.")]),
    box_room('reserve4', "The Minotaur's Private Reserve", FL[3], 'theme:rock', 18,
             "Casks in pairs by the walls, the hoard chest, the second Soul Waters in a niche on the south wall.",
             walls=[{'wall': 'south', 'panels': [panel_xy(B['reserve4'], 'south', 5504, 192, NICHE, 0, 384,
                                                          pid='niche4', notes="The Reserve's Soul Waters.")]}],
             platforms=[plat('soul_basin4', (5504, -3712), (256, 192), 64, BRICK, WATER,
                             notes="The Reserve's Soul Waters' basin.")]),
    box_room('gate_hall4', 'Fourth gate', FL[3], 'theme:hall', 16,
             "The fourth gate (two leaves) in the east wall at the stair's head."),
    flight('flight4', 'Stair to the Soul Maze', "Twenty steps behind the fourth gate, down east to L5."),
    # ---- L5 (-2560): Alamar's statues, the Soul Maze, the aviary
    box_room('statues5', "Alamar's statues", FL[4], 'theme:hall', 16,
             "The stair's foot and the Soul Maze's mouth (west wall, north end): four statues of one tall figure on "
             "plinths along the east wall, braziers between them.",
             platforms=[plat('statue5_%d' % n, (7392, y), (192, 192), 64, BRICK, FLAGS,
                             notes="A plinth under one of Alamar's statues.")
                        for n, y in enumerate(STATUE_Y, 1)]),
]
for key, letter, x0, cells in LETTERS:
    r = {'id': 'room:' + key, 'name': 'Soul Maze: the %s' % ('second E' if key == 'maze_e2' else letter),
         'outline': polyomino(cells, x0, MAZE_Y0), 'floor': FL[4], 'ceiling': FL[4] + MAZE_H, 'theme': 'theme:maze',
         'ambient': 8,
         'notes': "The Soul Maze's corridors tracing the letter %s (256 wide), joined to the letter before it by one "
                  "bridge." % letter}
    if key == 'maze_l':
        r['name'] = 'Heart of the maze (the L)'
        r['ambient'] = 14
        L0, Y0 = LX['maze_l'], MAZE_Y0
        r['platforms'] = [
            plat('dais', (L0 + 128, Y0 + 128), (192, 192), 24, RUBBLE_DARK, RFLOOR, notes="The throne's dais."),
            plat('throne', (L0 + 128, Y0 + 112), (128, 96), 56, RUBBLE_DARK, RUBBLE_DARK, base=24,
                 notes="The horned throne's seat of black stone."),
            plat(None, (L0 + 128, Y0 + 48), (128, 32), 200, RUBBLE_DARK, RUBBLE_DARK, base=24,
                 notes="The throne's back."),
            plat(None, (L0 + 44, Y0 + 48), (24, 24), 280, TRIM, TRIM, base=24, notes="A horn spur."),
            plat(None, (L0 + 212, Y0 + 48), (24, 24), 280, TRIM, TRIM, base=24, notes="A horn spur."),
        ]
        r['notes'] = ("The L, the maze's heart: its corner widened to two cells square; the horned throne on a dais "
                      "in the corner where both halves meet.")
    ROOMS.append(r)
ROOMS += [
    box_room('maze_dead', 'Maze dead end', FL[4], 'theme:maze', 10,
             "Behind an illusory wall under the second E: a lost adventurer's camp, bones and a chest.",
             ceiling=FL[4] + MAZE_H),
    box_room('gate_hall5', 'Fifth gate', FL[4], 'theme:hall', 16,
             "Where the maze's S ends: a Minotaur Lord before the fifth gate (west wall)."),
    box_room('aviary', 'The aviary', FL[4], 'theme:hall', 20,
             "Eight cages set in the walls; the lift's cage in the south wall.",
             walls=[
                 {'wall': 'north', 'panels': [panel_xy(B['aviary'], 'north', x, 160, CAGE_FIT, 64, 320,
                                                       pid='cage%d' % n, notes="A cage set in the wall (xwcage).")
                                              for n, x in ((1, -3168), (2, -2784), (3, -2400), (4, -2016))]},
                 {'wall': 'west', 'panels': [panel_xy(B['aviary'], 'west', y, 160, CAGE_FIT, 64, 320,
                                                      pid='cage%d' % n, notes="A cage set in the wall (xwcage).")
                                             for n, y in ((5, 2624), (6, 2240))]},
                 {'wall': 'south', 'panels': [panel_xy(B['aviary'], 'south', x, 160, CAGE_FIT, 64, 320,
                                                       pid='cage%d' % n, notes="A cage set in the wall (xwcage).")
                                              for n, x in ((7, -3168), (8, -2784))]}]),
]


def edge(room, axis, coord, lo, hi):
    """The number of the outline edge of `room` that lies on x (or y) = coord and covers lo..hi."""
    for r in ROOMS:
        if r['id'] == 'room:' + room:
            pts = r['outline']
            for k in range(len(pts)):
                a, b = pts[k], pts[(k + 1) % len(pts)]
                i = 0 if axis == 'x' else 1
                if a[i] == coord and b[i] == coord:
                    e0, e1 = sorted((a[1 - i], b[1 - i]))
                    if e0 <= lo and hi <= e1:
                        return k
    raise KeyError((room, axis, coord, lo, hi))


def op(i, a, b, link, width, height, **kw):
    d = {'id': 'open:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'link': 'link:' + link, 'width': width,
         'height': height}
    d.update(kw)
    return d


def full(i, a, b, link, **kw):
    return op(i, a, b, link, 'full', 'full', **kw)


OPENINGS = [
    # L1
    op('gate1', 'entry', 'gallery1', 'gate1', 320, 320, from_wall=E_NORTH, notes="The first gate (two leaves)."),
    op('vault', 'gallery1', 'vault1', 'vault', 256, 320, notes="The hourglass panel."),
    op('gallery_store_a', 'gallery1', 'store_a', 'gallery_store_a', 192, 384),
    op('gallery_store_c', 'gallery1', 'store_c', 'gallery_store_c', 192, 384),
    op('store_a_b', 'store_a', 'store_b', 'store_a_b', 384, 384),
    op('store_c_d', 'store_c', 'store_d', 'store_c_d', 384, 384),
    op('store_b_stair', 'store_b', 'stair1', 'store_b_stair', 192, 384),
    op('store_d_stair', 'store_d', 'stair1', 'store_d_stair', 384, 384),
    op('gallery_lift', 'gallery1', 'lift_head', 'gallery_lift', 320, 352, from_wall='west', to_wall='east',
       notes="The lift head's arch at the hall's west end."),
    op('lift_top', 'shaft', 'lift_head', 'lift', 384, 320, notes="The cage's gate at the top (L1)."),
    full('flight1_head', 'stair1', 'flight1', 'stair1', from_wall='south', to_wall='north'),
    full('flight1_foot', 'statue_hall2', 'flight1', 'stair1', from_wall='north', to_wall='south'),
    # L2
    full('statue_north', 'statue_hall2', 'north_walk2', 'statue_north', from_wall='west', to_wall='east'),
    full('statue_south', 'statue_hall2', 'south_walk2', 'statue_south', from_wall='west', to_wall='east'),
    op('cell1', 'south_walk2', 'cell1', 'cell1', 256, 320, notes="The first cell's bars."),
    op('cell2', 'south_walk2', 'cell2', 'cell2', 256, 320, notes="The second cell's bars."),
    op('cell3', 'south_walk2', 'cell3', 'cell3', 256, 320, notes="The third cell's bars."),
    full('north_gate', 'north_walk2', 'gate_hall2', 'north_gate', from_wall='west', to_wall='east'),
    full('south_gate', 'south_walk2', 'gate_hall2', 'south_gate', from_wall='west', to_wall='east'),
    op('gate2', 'gate_hall2', 'flight2', 'gate2', 320, 320, from_wall='west', to_wall='east',
       notes="The second gate (two leaves) at the stair's head."),
    full('flight2_foot', 'pool3', 'flight2', 'stair2', from_wall='east', to_wall='west'),
    # L3
    op('pool_dials', 'pool3', 'dials3', 'pool_dials', 384, 384),
    full('pool_flooded', 'pool3', 'flooded3', 'pool_flooded', from_wall='east', to_wall='west'),
    op('dials_soul', 'dials3', 'soul3', 'dials_soul', 384, 384),
    op('flooded_negative', 'flooded3', 'negative3', 'flooded_negative', 384, 384),
    op('soul_gate', 'soul3', 'gate_hall3', 'soul_gate', 384, 384),
    full('negative_gate', 'negative3', 'gate_hall3', 'negative_gate', from_wall='east', to_wall='west'),
    op('gate3', 'gate_hall3', 'flight3', 'gate3', 320, 320, from_wall='east', to_wall='west',
       notes="The third gate (two leaves) at the stair's head."),
    full('flight3_foot', 'plaque4', 'flight3', 'stair3', from_wall='west', to_wall='east'),
    # L4
    op('plaque_levers', 'plaque4', 'levers4', 'plaque_levers', 512, 384),
    op('plaque_barracks', 'plaque4', 'barracks4', 'plaque_barracks', 192, 384),
    op('barracks_levers', 'barracks4', 'levers4', 'barracks_levers', 384, 384),
    op('levers_reserve', 'levers4', 'reserve4', 'levers_reserve', 256, 320, notes="The Reserve's portcullis."),
    op('levers_gate', 'levers4', 'gate_hall4', 'levers_gate', 512, 384),
    op('gate4', 'gate_hall4', 'flight4', 'gate4', 320, 320, from_wall='north', to_wall='south',
       notes="The fourth gate (two leaves) at the stair's head."),
    full('flight4_foot', 'statues5', 'flight4', 'stair4', from_wall='south', to_wall='north'),
    # L5
    full('statues_maze', 'statues5', 'maze_m', 'statues_maze', from_wall='west',
         to_wall=edge('maze_m', 'x', 6560, MAZE_Y0, MAZE_Y0 + C)),
] + [full('%s_%s' % (LETTERS[k][0], LETTERS[k - 1][0].split('_')[1]), LETTERS[k][0], LETTERS[k - 1][0],
          '%s_%s' % (LETTERS[k][0], LETTERS[k - 1][0].split('_')[1]),
          from_wall=edge(LETTERS[k][0], 'x', LETTERS[k][2] - C, MAZE_Y0 + C * BRIDGE_ROW[k], MAZE_Y0 + C * BRIDGE_ROW[k] + C),
          to_wall=edge(LETTERS[k - 1][0], 'x', LETTERS[k][2] - C, MAZE_Y0 + C * BRIDGE_ROW[k],
                       MAZE_Y0 + C * BRIDGE_ROW[k] + C)) for k in range(6, 0, -1)] + [
    full('maze_s_gate', 'maze_s', 'gate_hall5', 'maze_s_gate', from_wall=edge('maze_s', 'x', -864, MAZE_Y0, MAZE_Y0 + C),
         to_wall='east'),
    op('illusion', 'maze_e2', 'maze_dead', 'illusion', 256, 320,
       from_wall=edge('maze_e2', 'y', MAZE_Y0, LX['maze_e2'] + C, LX['maze_e2'] + 2 * C),
       to_wall='north', notes="The illusory wall."),
    op('gate5', 'gate_hall5', 'aviary', 'gate5', 320, 320, notes="The fifth gate (two leaves)."),
    op('aviary_shaft', 'aviary', 'shaft', 'aviary_shaft', 384, 320, notes="The cage's mouth at the bottom (L5)."),
]

# ---------------------------------------------------------------------------------------------------------------------
# Monsters (D-42 (1)): Minotaur 11090 (38) x30, Gorgon 11091 (45) x12, Minotaur Lord 11092 (55) x3; strongest at the
# bottom (L1 8, L2 9, L3 9, L4 9, L5 10); the entrance hall and the third and fourth gate halls quiet.

POP = [
    # L1 (8)
    ('gallery1', 1, [(MINO, 1100, 768), (MINO, 1600, 700), (MINO, 1950, 840)]),
    ('store_a', 2, [(MINO, 700, 1340), (MINO, 1000, 1280), (MINO, 1150, 1400)]),
    ('store_c', 3, [(MINO, 1000, 160), (MINO, 1320, 260)]),
    # L2 (9)
    ('statue_hall2', 4, [(MINO, 2280, -1760), (MINO, 2880, -1760), (MINO, 2800, -2300)]),
    ('north_walk2', 5, [(MINO, 900, -1728), (MINO, 1500, -1728)]),
    ('south_walk2', 6, [(GORGON, 800, -2368), (GORGON, 1500, -2368)]),
    ('gate_hall2', 7, [(MINO, -100, -1800), (MINO, 100, -2300)]),
    # L3 (9)
    ('pool3', 8, [(MINO, -2880, -1500), (MINO, -2200, -1500), (MINO, -2200, -2600)]),
    ('dials3', 9, [(MINO, -1100, -1600), (MINO, -600, -1600), (MINO, -100, -1600)]),
    ('flooded3', 10, [(GORGON, -1300, -2760), (GORGON, -600, -2760), (GORGON, 0, -2760)]),
    # L4 (9)
    ('plaque4', 11, [(MINO, 3900, -1500), (MINO, 4350, -1500), (MINO, 4300, -2500)]),
    ('barracks4', 12, [(GORGON, 5100, -900)]),
    ('levers4', 13, [(MINO, 4800, -1700), (MINO, 4800, -2500), (GORGON, 6200, -1700), (GORGON, 6200, -2500)]),
    ('reserve4', 14, [(LORD, 5504, -3300)]),
    # L5 (10)
    ('statues5', 15, [(GORGON, 7000, 400), (GORGON, 7000, 1200)]),
    ('maze_m', 16, [(MINO,) + cell('maze_m', 2, 2)]),
    ('maze_e2', 17, [(MINO,) + cell('maze_e2', 0, 2)]),
    ('maze_t', 18, [(GORGON,) + cell('maze_t', 1, 2)]),
    ('maze_l', 19, [(LORD, LX['maze_l'] + 384, MAZE_Y0 + 384)]),
    ('maze_e', 20, [(MINO,) + cell('maze_e', 0, 2)]),
    ('maze_h', 21, [(GORGON,) + cell('maze_h', 1, 2)]),
    ('maze_s', 22, [(MINO,) + cell('maze_s', 1, 2)]),
    ('gate_hall5', 23, [(LORD, -1376, 2112)]),
]
MONSTERS = []
for room, group, entries in POP:
    for n, (row, x, y) in enumerate(entries):
        MONSTERS.append({'id': 'monster:%s_%d' % (room, n + 1), 'room': 'room:' + room, 'monster': row,
                         'at': F(x, y), 'facing': 270, 'group': group})
COUNT = {}
for m in MONSTERS:
    COUNT[m['monster']] = COUNT.get(m['monster'], 0) + 1
assert COUNT == {MINO: 30, GORGON: 12, LORD: 3}, COUNT
for m in MONSTERS:
    if m['monster'] == LORD:
        m['notes'] = "A Minotaur Lord (A2's 11092, level 55)."

# ---------------------------------------------------------------------------------------------------------------------
# Objects


def deco(i, room, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + room, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


def sconce(i, room, at, wall, **kw):
    return deco(i, room, 'scon100', at, wall=wall, **kw)


def msconce(i, room, at):
    """A wall torch in the maze on the outline edge nearest to `at`."""
    for r in ROOMS:
        if r['id'] == 'room:' + room:
            pts = r['outline']
            best = None
            for k in range(len(pts)):
                (ax, ay), (bx, by) = pts[k], pts[(k + 1) % len(pts)]
                if ax == bx and min(ay, by) <= at[1] <= max(ay, by):
                    dd = abs(at[0] - ax)
                elif ay == by and min(ax, bx) <= at[0] <= max(ax, bx):
                    dd = abs(at[1] - ay)
                else:
                    continue
                if best is None or dd < best[0]:
                    best = (dd, k)
            return deco(i, room, 'scon100', at, wall=best[1])
    raise KeyError(room)


DECORATIONS = [
    # L1
    sconce('entry_sw', 'entry', (-260, -474), 15, notes="A wall torch beside the door."),
    sconce('entry_se', 'entry', (260, -474), 1, notes="A wall torch beside the door."),
    sconce('entry_ne', 'entry', (474, 260), 5),
    sconce('entry_nw', 'entry', (-474, 260), 11),
    deco('entry_rubble_1', 'entry', 'trasheap', (330, 320), notes="Fallen masonry from the broken roof."),
    deco('entry_rubble_2', 'entry', 'trasheap', (-330, -300), notes="Fallen masonry."),
    sconce('gallery_n1', 'gallery1', (0, 1024), 'north'),
    sconce('gallery_n2', 'gallery1', (1344, 1024), 'north'),
    sconce('gallery_s1', 'gallery1', (640, 512), 'south'),
    sconce('gallery_s2', 'gallery1', (1984, 512), 'south'),
    sconce('vault', 'vault1', (-384, 1568), 'north'),
    sconce('gallery_w', 'gallery1', (-1280, 1024), 'north'),
    sconce('store_a', 'store_a', (384, 1344), 'west'),
    sconce('store_b', 'store_b', (2304, 1536), 'east'),
    sconce('store_c', 'store_c', (768, 192), 'west'),
    sconce('store_d', 'store_d', (2304, -32), 'east'),
    sconce('stair1_e', 'stair1', (2880, 768), 'east'),
    sconce('stair1_w', 'stair1', (2336, 800), 'west'),
    sconce('lift_head', 'lift_head', (-2560, 768), 'west'),
    # the storerooms (store: true): clumps along the walls, clear of the lines between the doors
    deco('store_a_sack_1', 'store_a', 'bag01', (448, 1600)),
    deco('store_a_sack_2', 'store_a', 'floursac', (560, 1600)),
    deco('store_a_sack_3', 'store_a', 'bag01', (448, 1488)),
    deco('store_a_barrel_1', 'store_a', 'bigbarel', (800, 1600)),
    deco('store_a_barrel_2', 'store_a', 'bigbarel', (912, 1600)),
    deco('store_b_barrel_1', 'store_b', 'bigbarel', (1760, 1600)),
    deco('store_b_barrel_2', 'store_b', 'bigbarel', (1872, 1600)),
    deco('store_b_barrel_3', 'store_b', 'bigbarel', (1760, 1120)),
    deco('store_b_barrel_4', 'store_b', 'bigbarel', (1872, 1120)),
    deco('store_b_sack_1', 'store_b', 'floursac', (1960, 1600)),
    deco('store_b_sack_2', 'store_b', 'bag01', (1960, 1120)),
    deco('store_c_straw_1', 'store_c', '7dec11', (880, -32), notes="Fodder straw."),
    deco('store_c_hay', 'store_c', '7dec11', (832, 384), notes="Fodder straw."),
    deco('store_c_sack', 'store_c', 'bag01', (1120, -48)),
    deco('store_d_bones', 'store_d', '7dec18', (1648, 416), notes="A heap of bones ('Bones', a find)."),
    deco('store_d_barrel_1', 'store_d', 'smlbarel', (1912, 448)),
    deco('store_d_barrel_2', 'store_d', 'smlbarel', (1968, 448)),
    # L2
    deco('statue2', 'statue_hall2', '7dec55', (2592, -2048), floor_height=FL[1] + 64,
         notes="The speaking statue on its plinth."),
    sconce('statue2_e', 'statue_hall2', (3200, -1984), 'east'),
    sconce('statue2_s', 'statue_hall2', (2592, -2560), 'south'),
    sconce('north_walk', 'north_walk2', (1184, -1920), 'south'),
    sconce('south_walk', 'south_walk2', (896, -2176), 'north'),
    sconce('gate2_n', 'gate_hall2', (-64, -1536), 'north'),
    sconce('gate2_s', 'gate_hall2', (-64, -2560), 'south'),
    deco('cell1_bones', 'cell1', '7dec18', (704, -2880), notes="An adventurer's bones ('Bones', a find)."),
    deco('cell2_bones', 'cell2', 'dec19', (1216, -2880), notes="An adventurer's bones ('Bones', a find)."),
    # L3
    sconce('pool_w', 'pool3', (-3072, -2048), 'west'),
    sconce('pool_n', 'pool3', (-2432, -1280), 'north'),
    deco('statue3', 'dials3', '7dec55', (-1500, -1760), floor_height=FL[2] + 64,
         notes="The dial statue on its plinth."),
    sconce('dials_s1', 'dials3', (-960, -1856), 'south'),
    sconce('dials_s2', 'dials3', (-192, -1856), 'south'),
    sconce('soul_w', 'soul3', (288, -1152), 'west'),
    sconce('soul_e', 'soul3', (1280, -1280), 'east'),
    sconce('flooded_n', 'flooded3', (-768, -2560), 'north'),
    sconce('negative_e', 'negative3', (1280, -2944), 'east'),
    sconce('gate3_n', 'gate_hall3', (1792, -1536), 'north'),
    sconce('gate3_s', 'gate_hall3', (1792, -2560), 'south'),
    # L4
    deco('statue4', 'plaque4', '7dec55', (4096, -1920), floor_height=FL[3] + 64,
         notes="The statue over the riddle's plaque."),
    sconce('plaque_w', 'plaque4', (3584, -1536), 'west'),
    sconce('plaque_e', 'plaque4', (4608, -2560), 'east'),
    sconce('levers_n1', 'levers4', (6144, -1280), 'north'),
    sconce('levers_s1', 'levers4', (4800, -2816), 'south'),
    sconce('levers_s2', 'levers4', (6272, -2816), 'south'),
    sconce('barracks', 'barracks4', (5632, -896), 'east'),
    deco('barracks_straw_1', 'barracks4', '7dec11', (4352, -640), notes="Old bedding straw."),
    deco('barracks_straw_2', 'barracks4', 'trasheap', (5440, -640), notes="A heap of straw and rubbish (the purse under it)."),
    deco('reserve_cask_1', 'reserve4', 'bigbarel', (4960, -3744)),
    deco('reserve_cask_2', 'reserve4', 'bigbarel', (4960, -3632)),
    deco('reserve_cask_3', 'reserve4', 'bigbarel', (6048, -3744)),
    deco('reserve_cask_4', 'reserve4', 'bigbarel', (6048, -3632)),
    sconce('reserve_w', 'reserve4', (4864, -3328), 'west'),
    sconce('reserve_e', 'reserve4', (6144, -3328), 'east'),
    sconce('gate4_n', 'gate_hall4', (6912, -1792), 'north'),
    sconce('gate4_s', 'gate_hall4', (6912, -2816), 'south'),
    # L5
] + [deco('alamar_%d' % n, 'statues5', '7dec55', (7392, y), floor_height=FL[4] + 64,
          notes="Alamar's statue on its plinth, verse %d." % n) for n, y in enumerate(STATUE_Y, 1)] + [
    deco('statues_brazier_1', 'statues5', 'brzier00', (7440, 224), hangs=True, height=352, notes="A brazier hung between the statues."),
    deco('statues_brazier_2', 'statues5', 'brzier00', (7440, 1376), hangs=True, height=352, notes="A brazier hung between the statues."),
    sconce('statues_w', 'statues5', (6560, 640), 'west'),
    msconce('maze_s1', 'maze_s', (LX['maze_s'], MAZE_Y0 + 896)),
    msconce('maze_h1', 'maze_h', (LX['maze_h'] + 384, MAZE_Y0 + 512)),
    msconce('maze_e1', 'maze_e', (LX['maze_e'], MAZE_Y0 + 896)),
    msconce('maze_t1', 'maze_t', (LX['maze_t'] + 384, MAZE_Y0 + 1280)),
    msconce('maze_e2_1', 'maze_e2', (LX['maze_e2'], MAZE_Y0 + 896)),
    msconce('maze_m1', 'maze_m', (LX['maze_m'] + 640, MAZE_Y0 + 1280)),
    deco('throne_brazier_1', 'maze_l', 'brzier00', (LX['maze_l'] + 384, MAZE_Y0 + 64), hangs=True, height=224,
         notes="A brazier hung over the dais's side."),
    deco('throne_brazier_2', 'maze_l', 'brzier00', (LX['maze_l'] + 64, MAZE_Y0 + 384), hangs=True, height=224,
         notes="A brazier hung over the dais's side."),
    deco('dead_bones', 'maze_dead', 'dec29', (4352, 1344), notes="A lost adventurer's bones."),
    sconce('dead', 'maze_dead', (5024, 1504), 'east'),
    sconce('gate5_n', 'gate_hall5', (-1376, 2624), 'north'),
    sconce('gate5_s', 'gate_hall5', (-1376, 1600), 'south'),
    deco('aviary_lamp_1', 'aviary', 'chndlir0', (-2976, 2304), hangs=True),
    deco('aviary_lamp_2', 'aviary', 'chndlir0', (-2368, 2304), hangs=True),
] + [deco('cagebird_%d' % n, 'aviary', 'xeen_cagebird', at, height=64, hangs=True, facing=f,
          notes="S's cage bird (row 4015, its perch idle) in cage %d: 1 in from the wall line (the build's inside test) at the panel's bottom, facing out." % n)
     for n, at, f in ((1, (-3168, 3007), 270), (2, (-2784, 3007), 270), (3, (-2400, 3007), 270), (4, (-2016, 3007), 270),
                      (5, (-3423, 2624), 0), (6, (-3423, 2240), 0), (7, (-3168, 1601), 90), (8, (-2784, 1601), 90))]

LIGHTS = []


def light(room, at, height, radius, color, **kw):
    d = {'id': 'light:' + room, 'room': 'room:' + room, 'at': F(*at), 'height': height, 'radius': radius,
         'color': F(*color)}
    d.update(kw)
    LIGHTS.append(d)


WARM = (255, 200, 150)
DIM = (220, 170, 130)
WATERY = (190, 215, 255)
light('entry', (0, 0), 560, 1500, (235, 205, 175), notes="Failing Darkside daylight through the broken roof.")
for k in ('gallery1', 'store_a', 'store_b', 'store_c', 'store_d', 'stair1', 'lift_head', 'statue_hall2',
          'north_walk2', 'south_walk2', 'gate_hall2', 'dials3', 'gate_hall3', 'plaque4', 'levers4', 'barracks4',
          'reserve4', 'gate_hall4', 'statues5', 'gate_hall5'):
    x0, y0, x1, y1 = B[k]
    light(k, ((x0 + x1) // 2, (y0 + y1) // 2), 400, int(max(x1 - x0, y1 - y0) * 0.9 + 400), WARM)
for k in ('vault1', 'cell1', 'cell2', 'cell3', 'flooded3', 'negative3', 'maze_dead'):
    x0, y0, x1, y1 = B[k]
    light(k, ((x0 + x1) // 2, (y0 + y1) // 2), 300, int(max(x1 - x0, y1 - y0) * 0.9 + 300), DIM)
light('pool3', (-2560, -1700), 400, 1700, WATERY)
light('soul3', (768, -1400), 400, 1300, WATERY)
light('aviary', (-2672, 2304), 420, 1700, (255, 225, 190))
light('shaft', (-2304, 1312), 300, 900, DIM)
light('maze_l', (LX['maze_l'] + 256, MAZE_Y0 + 256), 300, 900, (255, 170, 110), notes="The braziers by the throne.")
for key, letter, x0, cells in LETTERS:
    if key != 'maze_l':
        light(key, (x0 + C * cells[0][0] + 128, MAZE_Y0 + C * cells[0][1] + 128), 300, 1100, DIM)

# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s28 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-12: "good bone-and-rubble entrance, then
# tan brick storerooms on every floor"): floors 3-5 cut into d02's dark wet rock (c2b) with grey-brick footings and
# quoins, rock pillars, low brick arches over the long galleries and three side cells; uneven rock ceilings in the rock
# rooms; the brick floors (L1-L2) get a dark base course and cornice, the hall of storage a barrel vault; the maze's
# ivy grows over a broken grey-brick footing with fallen masonry in its dead ends.
WETROCK = S('c2b', 256, 256)
FOOTING = [{'height': 96, 'surface': dict(BRICK)}]
BRICK_BANDS = [{'height': 64, 'surface': dict(WETROCK)}, {'height': 448, 'surface': dict(BRICK)},
               {'height': 480, 'surface': dict(WETROCK)}]
for _t in THEMES:
    if _t['id'] == 'theme:rock':
        _t.update({'wall': WETROCK, 'ceiling': WETROCK, 'reveal': WETROCK, 'bands': [dict(b) for b in FOOTING]})
        _t['notes'] = ("Rooms cut into the isle's dark wet rock (d02's c2b) over a grey-brick footing (cwb): the cells, "
                       "the pool, the flooded walk, the barracks, the reserve.")
    if _t['id'] in ('theme:brick', 'theme:hall'):
        _t['bands'] = [dict(b) for b in BRICK_BANDS]
        _t['notes'] += " A dark rock base course and cornice (c2b)."
    if _t['id'] == 'theme:maze':
        _t['bands'] = [dict(b) for b in FOOTING]
        _t['notes'] = ("The Soul Maze: MM7 Maze's ivy (eswamp) grown over a broken grey-brick footing (cwb), red rock "
                       "floor, green stone ceiling.")
THEMES += [
    {'id': 'theme:deep', 'wall': WETROCK, 'floor': FLAGS, 'ceiling': WETROCK, 'reveal': BRICK, 'door': GRATE,
     'bands': [dict(b) for b in FOOTING],
     'notes': "The set-piece halls of floors 3-5 (gates, dials, the Soul Waters, the plaque, the levers, the statues, "
              "the aviary): halls cut into d02's dark wet rock (c2b) with grey-brick footings, quoins and reveals "
              "(cwb), flags t5s1fl."},
    {'id': 'theme:deepstair', 'wall': WETROCK, 'floor': RFLOOR, 'ceiling': WETROCK, 'reveal': BRICK, 'door': GRATE,
     'notes': "The flights down to floors 3-5: dark wet rock (c2b), red rock treads."},
]
_DEEP = ('dials3', 'soul3', 'gate_hall3', 'plaque4', 'levers4', 'gate_hall4', 'statues5', 'gate_hall5', 'aviary')
_RM = {r['id'].split(':')[1]: r for r in ROOMS}
for _k in _DEEP:
    _RM[_k]['theme'] = 'theme:deep'
    if _k != 'aviary':      # the aviary's cages reach its corners
        _RM[_k]['ends'] = {'length': 64, 'surface': dict(BRICK)}
for _k in ('flight2', 'flight3', 'flight4'):
    _RM[_k]['theme'] = 'theme:deepstair'


def rock_pillar(cx, cy, r, seed):
    """An irregular seven-sided rock pillar about 2r across."""
    out = []
    for k in range(7):
        a = 2 * 3.141592653589793 * k / 7 + seed * 0.37
        rr = r * (0.8 + 0.2 * (((k + 1) * (seed + 3) * 7) % 5) / 4)
        out.append(F(int(round(cx + rr * __import__('math').cos(a))), int(round(cy + rr * __import__('math').sin(a)))))
    return {'outline': out, 'surface': dict(WETROCK), 'notes': "A pillar of the living rock left standing."}


def pier(cx, cy, size=128):
    return {'at': F(cx, cy), 'size': F(size, size), 'surface': dict(BRICK), 'notes': "A grey-brick pier."}


_PILLARS = {
    'pool3': [rock_pillar(-2560, -1472, 72, 1), rock_pillar(-2560, -2624, 80, 2)],
    'soul3': [pier(480, -1344), pier(1056, -1344)],
    'negative3': [rock_pillar(608, -2496, 80, 3), rock_pillar(928, -2976, 88, 4)],
    'barracks4': [rock_pillar(4736, -880, 80, 5), rock_pillar(5376, -880, 72, 6)],
    'reserve4': [rock_pillar(5120, -3360, 88, 7), rock_pillar(5888, -3360, 88, 8)],
    'statues5': [pier(6816, 96), pier(6816, 1248)],
}
for _k, _p in _PILLARS.items():
    _RM[_k]['pillars'] = _RM[_k].get('pillars', []) + _p


def arch(x0, y0, x1, y1, at, floor, along='y', spring=320, crown=464, width=64):
    """A low grey-brick arch across a room at x (along='y': from the south wall to the north) or y = at."""
    if along == 'y':
        mid = (y0 + y1) // 2
        halves = [(F(at, y0), F(at, mid)), (F(at, y1), F(at, mid))]
    else:
        mid = (x0 + x1) // 2
        halves = [(F(x0, at), F(mid, at)), (F(x1, at), F(mid, at))]
    return [{'path': [a, b], 'width': width, 'depth': 48, 'bottom': floor + spring, 'bottom_end': floor + crown,
             'surface': dict(BRICK), 'notes': "Half of a low brick arch."} for a, b in halves]


_ARCHES = {'dials3': ('y', (-1280, -576)), 'flooded3': ('y', (-1088, -448)), 'plaque4': ('x', (-2464, -1408))}
for _k, (_al, _ats) in _ARCHES.items():
    _x0, _y0, _x1, _y1 = B[_k]
    _RM[_k]['beams'] = [b for _a in _ats for b in arch(_x0, _y0, _x1, _y1, _a, _RM[_k]['floor'], _al)]


def rock_ceiling(k, pts):
    """Uneven rock ceiling: points inside the room (dx, dy as fractions of the box, height above the floor)."""
    x0, y0, x1, y1 = B[k]
    fl = _RM[k]['floor']
    _RM[k]['ceiling_points'] = [F(int(x0 + fx * (x1 - x0)), int(y0 + fy * (y1 - y0)), fl + h) for fx, fy, h in pts]


rock_ceiling('pool3', [(0.3, 0.3, 576), (0.7, 0.55, 560), (0.5, 0.8, 480), (0.25, 0.65, 528)])
rock_ceiling('negative3', [(0.5, 0.5, 576), (0.25, 0.75, 480), (0.75, 0.3, 536)])
rock_ceiling('barracks4', [(0.25, 0.5, 560), (0.6, 0.35, 480), (0.85, 0.6, 544)])
rock_ceiling('reserve4', [(0.3, 0.6, 568), (0.7, 0.6, 568), (0.5, 0.25, 496)])
for _k in ('cell1', 'cell2', 'cell3'):
    _RM[_k]['rough'] = {'step': 128, 'depth': 32}
# the hall of storage: a barrel vault (nothing stands above L1)
_gx0, _gy0, _gx1, _gy1 = B['gallery1']
_RM['gallery1']['ceiling_points'] = [F(_gx0, (_gy0 + _gy1) // 2, 640), F(_gx1, (_gy0 + _gy1) // 2, 640)]
_RM['gallery1']['notes'] += " A barrel vault over its length."

# three side cells cut into the rock (L3)
B.update({'side3a': (-1600, -2528, -1280, -2304), 'side3b': (-416, -2528, -96, -2304),
          'side3c': (-3328, -2720, -3104, -2400)})
_SIDE = [('side3a', 'flooded3', "A side cell off the flooded walk: chains and an old prisoner's bones."),
         ('side3b', 'flooded3', "A side cell off the flooded walk: bones in the wet."),
         ('side3c', 'pool3', "A side cell off the pool: a skull on a ledge of rock.")]
for _k, _from, _n in _SIDE:
    ROOMS.append(box_room(_k, 'Side cell', FL[2], 'theme:rock', 8, _n, ceiling=FL[2] + 384,
                          rough={'step': 128, 'depth': 32}))
    OPENINGS.append(op(_k, _from, _k, _k, 192, 288, notes="A low arch into a side cell."))
_RM = {r['id'].split(':')[1]: r for r in ROOMS}
DECORATIONS += [
    deco('side3a_bones', 'side3a', '7dec18', (-1552, -2368), notes="A prisoner's bones."),
    deco('side3b_bones', 'side3b', 'dec19', (-160, -2368), notes="Bones."),
    deco('side3c_skull', 'side3c', 'dec29', (-3280, -2464), notes="A skull."),
]
for _k in ('side3a', 'side3b', 'side3c'):
    _x0, _y0, _x1, _y1 = B[_k]
    light(_k, ((_x0 + _x1) // 2, (_y0 + _y1) // 2), 240, 600, DIM)
# fallen masonry in the maze's dead ends
for _n, (_l, _c, _r, _dx, _dy) in enumerate((('maze_h', 0, 0, 0, -64), ('maze_h', 2, 4, 0, 64), ('maze_e', 2, 0, 64, 0),
                                              ('maze_m', 0, 0, 0, -64), ('maze_m', 2, 0, 0, -64)), 1):
    _x, _y = cell(_l, _c, _r)
    DECORATIONS.append(deco('maze_rubble_%d' % _n, _l, 'trasheap', (_x + _dx, _y + _dy),
                            notes="Fallen masonry from the maze's broken walls."))

IDENTITY = {'shape': 'hall', 'family': 'd02',
            'seen': ["the ruined tower's round base open to the Darkside sky, bones and fallen masonry by the gate",
                     "floors 3-5 cut into dark wet rock: rock pillars, low brick arches, side cells, the Soul Waters",
                     "the Soul Maze's ivy over broken masonry spelling SHELTEM, Alamar's statues and the aviary"]}

SOUNDS = [
    {'id': 'sound:bed_upper', 'room': 'room:statue_hall2', 'at': F(2592, -1600), 'height': 0, 'sound': 'xeen_amb_mine',
     'radius': 3800, 'inner_radius': 1800, 'volume': 0.3, 'pan': False,
     'notes': "The dungeon's bed (AUDIO.md xeen_amb_mine, drips and knocks): one source between L1 and L3, quiet."},
    {'id': 'sound:bed_lower', 'room': 'room:levers4', 'at': F(5504, -2048), 'sound': 'xeen_amb_mine',
     'radius': 4200, 'inner_radius': 1800, 'volume': 0.3, 'pan': False, 'notes': "The bed for L4 and the maze's east half."},
    {'id': 'sound:bed_maze', 'room': 'room:maze_l', 'at': F(2336, 2560), 'sound': 'xeen_amb_mine',
     'radius': 3600, 'inner_radius': 1500, 'volume': 0.3, 'pan': False,
     'notes': "The bed for the maze's west half and the aviary."},
    {'id': 'sound:entry_wind', 'room': 'room:entry', 'at': F(0, 0), 'height': 640, 'sound': 'whistling wind',
     'radius': 1200, 'inner_radius': 400, 'volume': 0.35, 'notes': "Wind over the broken roof."},
    {'id': 'sound:pool', 'room': 'room:pool3', 'at': F(-2560, -2048), 'sound': 'water lapping loop',
     'radius': 1300, 'inner_radius': 300, 'volume': 0.3, 'notes': "The stagnant pool."},
    {'id': 'sound:soul3', 'room': 'room:soul3', 'at': F(768, -1152), 'sound': 'water lapping loop',
     'radius': 1000, 'inner_radius': 250, 'volume': 0.3, 'notes': "The Soul Waters."},
    {'id': 'sound:throne', 'room': 'room:maze_l', 'at': F(2400, 1984), 'sound': 'campfire', 'radius': 900,
     'inner_radius': 200, 'volume': 0.35, 'notes': "The braziers by the horned throne."},
    {'id': 'sound:statues', 'room': 'room:statues5', 'at': F(7440, 800), 'sound': 'campfire', 'radius': 1000,
     'inner_radius': 200, 'volume': 0.3, 'notes': "The braziers between Alamar's statues."},
]


def door(i, opening, kind='hinged', **kw):
    d = {'id': 'door:' + i, 'opening': 'open:' + opening, 'kind': kind}
    if kind == 'hinged' and 'leaves' not in kw:
        d.update({'hinge': 'left', 'thickness': 16, 'speed': 80})
    elif kind == 'hinged':
        d.update({'thickness': 16, 'speed': 80})
    d.update(kw)
    return d


GATE_NOTE = ("A 'think positive' gate: two hinged leaves of iron bars over a bronze half-sun (xlsgate), the right "
             "leaf mirrored, so the closed pair makes one smiling sun; they swing apart.")
DOORS = [door('gate%d' % n, 'gate%d' % n, leaves=2, surface=GATE, back_surface=GATE, notes=GATE_NOTE)
         for n in range(1, 6)] + [
    door('vault', 'vault', kind='slide_up', secret=True, thickness=16, speed=64, surface=BRICK, back_surface=BRICK,
         tile=True, notes="The hourglass panel in the hall's west end: it grinds up once all four hourglasses are "
                          "turned; from inside the vault it opens by hand."),
    door('store_a', 'gallery_store_a', surface=GRATE, back_surface=GRATE, edge_surface=TRIM,
         notes="A storeroom door: 'Minotaur Storage'."),
    door('store_c', 'gallery_store_c', surface=GRATE, back_surface=GRATE, edge_surface=TRIM,
         notes="A storeroom door: 'Minotaur Storage'."),
    door('store_b', 'store_b_stair', surface=GRATE, back_surface=GRATE, edge_surface=TRIM,
         notes="The north-east storeroom's door to the stair head."),
    door('cell1', 'cell1', kind='slide_up', thickness=8, speed=96, surface=CAGE, tile=True,
         notes="The first cell's bars (xwcage), raised by the north walk's lever."),
    door('cell2', 'cell2', kind='slide_up', thickness=8, speed=96, surface=CAGE, tile=True,
         notes="The second cell's bars, raised by the south walk's lever."),
    door('cell3', 'cell3', kind='slide_up', thickness=8, speed=96, surface=CAGE, tile=True,
         notes="The third cell's bars, raised by the second gate's lever."),
    door('barracks', 'plaque_barracks', surface=GRATE, back_surface=GRATE, edge_surface=TRIM,
         notes="The barracks door."),
    door('reserve', 'levers_reserve', kind='slide_up', thickness=16, speed=64, surface=S('c1d1', 128, 256),
         tile=True, notes="The Reserve's iron portcullis (c1d1): raised by the riddle's lever, and stays up."),
    door('illusion', 'illusion', kind='slide_down', secret=True, thickness=8, speed=256, surface=IVY,
         back_surface=IVY, tile=True, notes="The illusory wall: 'An illusion!' and it is gone."),
    door('gate_top', 'lift_top', kind='slide_up', thickness=8, speed=60, surface=CAGE, tile=True,
         notes="The cage's gate at the lift head: shut while the cage is down (a 2,560 drop), opened with the cage's "
               "climb."),
]

LIFTS = [
    {'id': 'lift:cage', 'room': 'room:shaft', 'at': F(-2304, 1312), 'size': F(448, 448), 'travel': 2560,
     'thickness': 16, 'speed': 480, 'surface': RFLOOR,
     'notes': "The iron cage: a floor 448 square riding the shaft between the aviary (down, L5) and the lift head "
              "(up, L1). D-42 (2): it runs only once m24.bird_freed is set."},
]

SWITCHES = [
    {'id': 'switch:call_foot', 'room': 'room:aviary', 'kind': 'button', 'at': F(-2016, 1600), 'height': 112,
     'notes': "Call button beside the cage's mouth in the aviary."},
    {'id': 'switch:ride_up', 'room': 'room:shaft', 'kind': 'button', 'at': F(-2560, 1312), 'floor_height': FL[4],
     'height': 112, 'notes': "Inside the shaft at the foot: sends the cage up."},
    {'id': 'switch:call_top', 'room': 'room:lift_head', 'kind': 'button', 'at': F(-2560, 896), 'height': 112,
     'notes': "Call button beside the cage's gate at the lift head."},
    {'id': 'switch:ride_down', 'room': 'room:shaft', 'kind': 'button', 'at': F(-2560, 1312), 'floor_height': FL[4],
     'height': 2560 + 112, 'notes': "Inside the shaft at the top, in reach of a rider on the raised cage."},
    {'id': 'switch:lever1', 'room': 'room:north_walk2', 'kind': 'lever', 'at': F(768, -1536),
     'notes': "The first cell's lever."},
    {'id': 'switch:lever2', 'room': 'room:south_walk2', 'kind': 'lever', 'at': F(1600, -2176),
     'notes': "The second cell's lever."},
    {'id': 'switch:lever3', 'room': 'room:gate_hall2', 'kind': 'lever', 'at': F(-480, -1664),
     'notes': "The third cell's lever, on the west wall beside the gate."},
    {'id': 'switch:lever4', 'room': 'room:statue_hall2', 'kind': 'lever', 'at': F(3200, -2304),
     'notes': "The fourth lever, by the statue: stuck."},
    {'id': 'switch:soul_lever', 'room': 'room:soul3', 'kind': 'lever', 'at': F(1088, -1024),
     'notes': "The Soul Waters' lever beside the niche."},
] + [{'id': 'switch:post_%d%d' % (r + 1, c + 1), 'room': 'room:levers4', 'kind': 'lever',
      'block': 'platform:post_%d%d' % (r + 1, c + 1), 'side': 's', 'height': 80, 'reach': 24,
      'notes': "Lever %d of row %d (rows north to south, levers west to east)." % (c + 1, r + 1)}
     for r in range(4) for c in range(3)]

CHESTS = [
    {'id': 'chest:vault', 'room': 'room:vault1', 'at': F(-384, 1488), 'treasure_level': 4,
     'random_items': 2, 'gold': 1500, 'notes': "The minotaurs' strongbox behind the hourglass panel."},
    {'id': 'chest:cell3', 'room': 'room:cell3', 'at': F(1728, -2992), 'treasure_level': 4,
     'random_items': 2, 'gold': 900, 'notes': "Taken from the last ones who answered No."},
    {'id': 'chest:negative', 'room': 'room:negative3', 'at': F(1200, -2560), 'treasure_level': 4,
     'random_items': 2, 'gold': 1200, 'notes': "By the black waters."},
    {'id': 'chest:reserve', 'room': 'room:reserve4', 'at': F(5504, -2976), 'treasure_level': 5,
     'random_items': 3, 'gold': 3000, 'notes': "The Minotaur's hoard (T5)."},
    {'id': 'chest:dead', 'room': 'room:maze_dead', 'at': F(4944, 1344), 'treasure_level': 4,
     'random_items': 2, 'gold': 1000, 'notes': "The lost adventurer's chest."},
]

EXITS = [
    {'id': 'exit:door_left', 'room': 'room:entry', 'at': F(80, -512), 'size': F(160, 320), 'surface': FIT('7solid01', 128, 256),
     'to': 'exit:d4_door',
     'notes': "The tower door's left wing seen from inside (hkm1dl, as D4's leaves): out to the Isle."},
    {'id': 'exit:door_right', 'room': 'room:entry', 'at': F(-80, -512), 'size': F(160, 320), 'surface': FIT('7solid01', 128, 256),
     'to': 'exit:d4_door',
     'notes': "The tower door's right wing seen from inside (hkm1dr): out to the Isle."},
]

START = {'room': 'room:entry', 'at': F(0, -352), 'facing': 'n',
         'notes': "A step inside the tower's double door, facing north to the first gate (entrance:d4_isle)."}
ARRIVALS = [
    {'entrance': 'entrance:d4_isle', 'room': 'room:entry', 'at': F(0, -352), 'facing': 'n',
     'notes': "D4's door:dd12 (m24.isle_door with the lost_souls_key): inside the double door, facing north."},
]

OBJECTS = {
    'format': 0,
    'start': START,
    'arrivals': ARRIVALS,
    'doors': DOORS,
    'lifts': LIFTS,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'switches': SWITCHES,
    'chests': CHESTS,
    'monsters': MONSTERS,
    'decorations': DECORATIONS,
    'exits': EXITS,
    'notes': "DD-12's contents, written by output/studio_cal/dd12/tools/gen.py: 16 doors (the five gates pairs of "
             "leaves), the lift, 16 levers, 5 chests, 45 placed monsters, no spawn points.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Wiring


def lock():
    p = OUT + '/L4/ids.lock.yml'
    if os.path.exists(p):
        return yaml.safe_load(open(p)) or {}
    return {}


LOCK = lock()
MV = (LOCK.get('map_vars') or {})


def mv(name):
    return MV.get(name, 0)


VARIABLES = ['glass_a', 'glass_b', 'glass_c', 'glass_d', 'dial1', 'dial2', 'dial3', 'dial4', 'waters3', 'riddle',
             'bones_c1', 'bones_c2', 'bones_d', 'purse', 'dead_bones', 'statue2_spoke',
             'bird_luck', 'bird_end', 'bird_speed', 'bird_pers', 'bird_might', 'bird_acc', 'parrot']


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


def find(i, source, title, var, gift, notes, empty="Nothing here."):
    return {'id': 'evt:' + i, 'preset': 'script', 'source': source, 'title': title,
            'condition': {'not': {'map_var': var}},
            'effects': gift + [{'set': {'var': {'map_var': var}, 'value': 1}}],
            'else_effects': [{'text': empty}], 'notes': notes}


QUESTIONS = {1: "Will you find what you came for?", 2: "Is the glass half full?",
             3: "Will tomorrow be better than today?", 4: "Are your friends glad you came?",
             5: "Is the Songbird waiting for you?"}


def gate_ask(n):
    return ("if continueStep == 1 then\n"
            "    XeenQuests.hook(\"m24.gate_open\")\n"
            "    SetQBit(QBit(%d))\n"
            "    return\n"
            "end\n"
            "if continueStep == 2 then\n"
            "    XeenQuests.hook(\"m24.gate_shut\")\n"
            "    return\n"
            "end\n"
            "if continueStep ~= nil then\n"
            "    return\n"
            "end\n"
            "XeenQuests.hook(\"m24.gate%d\")\n"
            "AskChoiceWithAnswerSteps(eventId, 3, \"%s\", {{Answer = \"Yes\", Step = 1}, {Answer = \"No\", Step = 2}})"
            ) % (QBITS['gate%d' % n], n, QUESTIONS[n])


GATE_SIDES = {1: ('entry', 'gallery1'), 2: ('gate_hall2', 'flight2'), 3: ('gate_hall3', 'flight3'),
              4: ('gate_hall4', 'flight4'), 5: ('gate_hall5', 'aviary')}


def gate_events(n):
    front, back = GATE_SIDES[n]
    return [
        {'id': 'evt:gate%d' % n, 'preset': 'door', 'source': 'door:gate%d' % n, 'side': 'room:' + front,
         'title': 'Gate', 'condition': {'qbit': 'gate%d' % n},
         'else_effects': [{'lua': gate_ask(n)}],
         'notes': "m24.gate%d asks '%s' (A3's text); Yes: m24.gate_open and the map's gate%d qbit (%d), and "
                  "evt:gate%d_open swings the leaves apart; No: m24.gate_shut, the gate stays shut and asks again "
                  "(D-42 (6): no wave). Once answered, a plain double door." % (
                      n, QUESTIONS[n], n, QBITS['gate%d' % n], n)},
        {'id': 'evt:gate%d_back' % n, 'preset': 'door', 'source': 'door:gate%d' % n, 'side': 'room:' + back,
         'title': 'Gate', 'notes': "From beyond, the gate opens by hand."},
        {'id': 'evt:gate%d_open' % n, 'preset': 'switch', 'trigger': 'timer', 'every': 1,
         'condition': {'qbit': 'gate%d' % n}, 'opens': ['door:gate%d' % n], 'once': True,
         'notes': "The gate's leaves swing apart once it was answered Yes (also after a refill)."},
    ]


def hourglass(letter):
    var = 'glass_' + letter
    return {'id': 'evt:glass_' + letter, 'preset': 'script', 'source': 'panel:glass_' + letter,
            'title': 'Hour Glass', 'condition': {'not': {'map_var': var}},
            'effects': [{'set': {'var': {'map_var': var}, 'value': 1}},
                        {'text': "You turn the hour glass over. The sand begins to run."}],
            'else_effects': [{'set': {'var': {'map_var': var}, 'value': 0}},
                             {'text': "You turn the hour glass back."}],
            'notes': "'Flip the Hour Glass over?' (aaze0078:6): a map variable that flips back and forth."}


def dial(n):
    lines = ["local v = MapVar(dial%d)" % n,
             "if IsAtLeast(v, 4) then",
             "    SetValue(v, 1)",
             "    evt.StatusText(\"The dial turns. It is set at 1.\")",
             "elseif IsAtLeast(v, 3) then",
             "    SetValue(v, 4)",
             "    evt.StatusText(\"The dial turns. It is set at 4.\")",
             "elseif IsAtLeast(v, 2) then",
             "    SetValue(v, 3)",
             "    evt.StatusText(\"The dial turns. It is set at 3.\")",
             "else",
             "    SetValue(v, 2)",
             "    evt.StatusText(\"The dial turns. It is set at 2.\")",
             "end"]
    return {'id': 'evt:dial%d' % n, 'preset': 'script', 'source': 'panel:dial%d' % n, 'title': 'Dial',
            'lua': '\n'.join(lines),
            'notes': "'The dial is set at N. Turn?' (aaze0080:6-9): 1 to 4 and round (map variable dial%d; 0 reads "
                     "as 1)." % n}


DIALS_UP = ' and '.join('IsAtLeast(MapVar(dial%d), 4)' % n for n in range(1, 5))

BIRDS = [  # (cage, var, name, stat selector, stat word)
    (1, 'bird_luck', 'Lark of Luck', 'BaseLuck', 'Luck'),
    (2, 'bird_end', 'Eagle of Endurance', 'BaseEndurance', 'Endurance'),
    (3, 'bird_speed', 'Sparrow of Speed', 'BaseSpeed', 'Speed'),
    (5, 'bird_pers', 'Parakeet of Personality', 'BasePersonality', 'Personality'),
    (6, 'bird_might', 'Magpie of Might', 'BaseMight', 'Might'),
    (7, 'bird_acc', 'Albatross of Accuracy', 'BaseAccuracy', 'Accuracy'),
]


def bird(cage, var, name, stat, word):
    return {'id': 'evt:cage%d' % cage, 'preset': 'script', 'source': 'panel:cage%d' % cage, 'title': name,
            'condition': {'not': {'map_var': var}},
            'effects': [{'lua': "evt.ForPlayer(Players.All)\nAddValue(%s, 2)" % stat},
                        {'set': {'var': {'map_var': var}, 'value': 1}},
                        {'text': "%s. You set it free. In gratitude, the bird flutters around the party and sings "
                                 "its magic song. +2 %s (permanent)." % (name, word)}],  # F13: a status line
            'else_effects': [{'text': "An empty cage, door open."}],
            'notes': "D-42 (4): '%s. Set it free?' (aaze0082:2-13), +2 %s to every member present, once (map "
                     "variable %s)." % (name, word, var)}


PARROT = ("Parrot of Prophecy. You set it free, and it sings from the rafters: His nights were filled with evil "
          "dreams, his days were spent in wicked schemes. You must destroy that wicked fiend before he controls all "
          "of XEEN!")
VERSES = {1: "This dungeon stand as tribute to me, my name in walls for all to see.",
          2: "The Soul Maze inside is dark, dreary, and vast. The name found within is the clue to my past.",
          3: "Long have I traveled through deep, dark space, only to land and take over this place.",
          4: "I am saying this now for all to hear: none from this world shall I ever fear."}
STATUE2 = ("The statue speaks: All of the lost souls in this dungeon have become lost because they did not think "
           "positively. If you wish to stay found... Think Positive!")
RIDDLE = ("A plaque on the plinth reads: Start from the North and go to the South; third from the top and far to the "
          "East pull the lever you suspected least.")
DIAL_STATUE = "The statue's plinth reads: Turn all dials up, pull lever & drink the souls of adventurers past!"
LIFT_OK = {'qbit': 'bird_freed'}
LIFT_SOUND = [{'lua': "evt.PlaySoundName(\"xeen_lift\", -2304, 1312, -1280)"}]

EVENTS = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'not': {'qbit': 'arrived_once'}}, 'once': True,
     'effects': [{'lua': "XeenQuests.hook(\"m24.arrival\")"}, {'qbit': 'arrived_once'}],
     'notes': "The first entry: A3's m24.arrival (the carving's words) once (dd12_arrived_once 117440)."},
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load', 'text': "The Dungeon of Lost Souls.",
     'notes': "Every entry: a status line."},
    {'id': 'evt:plaque', 'preset': 'script', 'source': 'panel:plaque', 'title': 'Plaque',
     'lua': "XeenQuests.hook(\"m24.arrival\")",
     'notes': "The carved plaque over the first gate: A3's m24.arrival again (the answer-giver for the gates)."},
    {'id': 'evt:exit_left', 'preset': 'exit', 'source': 'exit:door_left', 'title': "Doors to the Isle",
     'notes': "Out to D4's Isle of Lost Souls a step south of the tower's door (entrance:dd12_door): the game's "
              "leave window (D-24)."},
    {'id': 'evt:exit_right', 'preset': 'exit', 'source': 'exit:door_right', 'title': "Doors to the Isle",
     'notes': "The door's other wing: the same way out."},
]
for n in range(1, 6):
    EVENTS += gate_events(n)
EVENTS += [
    # L1: Minotaur Storage and the hourglasses
    {'id': 'evt:door_store_a', 'preset': 'door', 'source': 'door:store_a', 'title': 'Minotaur Storage'},
    {'id': 'evt:door_store_c', 'preset': 'door', 'source': 'door:store_c', 'title': 'Minotaur Storage'},
    {'id': 'evt:door_store_b', 'preset': 'door', 'source': 'door:store_b', 'title': 'Door'},
    hourglass('a'), hourglass('b'), hourglass('c'), hourglass('d'),
    {'id': 'evt:vault_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
     'condition': {'not': {'any': [{'not': {'map_var': 'glass_%s' % x}} for x in 'abcd']}},
     'opens': ['door:vault'], 'once': True, 'text': "Somewhere a panel grinds open.",
     'notes': "All four hourglasses turned: the hall's west panel grinds up and stays open."},
    {'id': 'evt:vault_back', 'preset': 'door', 'source': 'door:vault', 'side': 'room:vault1', 'title': 'Panel',
     'notes': "From inside the vault the panel opens by hand."},
    {'id': 'evt:chest_vault', 'preset': 'chest', 'source': 'chest:vault', 'title': 'Chest'},
    find('bones_d', 'deco:store_d_bones', 'Bones', 'bones_d', [{'gold': 350}],
         "A heap of bones in the south-east storeroom: a find, then 'Nothing here.'"),
    # the lift (D-42 (2))
    {'id': 'evt:call_top', 'preset': 'switch', 'source': 'switch:call_top', 'title': 'Call the lift',
     'condition': LIFT_OK, 'else_effects': [{'text': "The cage does not move. Far below, something sings."}],
     'opens': ['lift:cage', 'door:gate_top'], 'text': "The cage climbs the long shaft to you.", 'effects': LIFT_SOUND},
    {'id': 'evt:ride_down', 'preset': 'switch', 'source': 'switch:ride_down', 'title': 'Lift: down',
     'condition': LIFT_OK, 'else_effects': [{'text': "The cage does not move."}],
     'closes': ['lift:cage', 'door:gate_top'], 'text': "The cage sinks into the dark.", 'effects': LIFT_SOUND},
    {'id': 'evt:call_foot', 'preset': 'switch', 'source': 'switch:call_foot', 'title': 'Call the lift',
     'condition': LIFT_OK, 'else_effects': [{'text': "The cage does not move. The Songbird is still caged."}],
     'closes': ['lift:cage', 'door:gate_top'], 'text': "The cage rattles down the shaft.", 'effects': LIFT_SOUND},
    {'id': 'evt:ride_up', 'preset': 'switch', 'source': 'switch:ride_up', 'title': 'Lift: up',
     'condition': LIFT_OK, 'else_effects': [{'text': "The cage does not move. The Songbird is still caged."}],
     'opens': ['lift:cage', 'door:gate_top'], 'text': "The cage climbs the long shaft to the tower.",
     'effects': LIFT_SOUND},
    # L2: the statue, the levers, the cells
    {'id': 'evt:statue2_step', 'preset': 'script', 'trigger': 'step', 'source': 'room:statue_hall2',
     'condition': {'not': {'map_var': 'statue2_spoke'}},
     'effects': [{'set': {'var': {'map_var': 'statue2_spoke'}, 'value': 1}}, {'message': STATUE2}],
     'notes': "The statue speaks as you come down the stair (aaze0079:1), once a visit; its click says it again."},
    text('statue2', 'deco:statue2', 'Statue', STATUE2, window=True),
    {'id': 'evt:lever1', 'preset': 'switch', 'source': 'switch:lever1', 'title': 'Lever',
     'toggles': ['door:cell1'], 'text': "Clank! Bars grind somewhere along the cell row.",
     'notes': "'Pull lever?' (aaze0079:2): the first cell's bars, up and down."},
    {'id': 'evt:lever2', 'preset': 'switch', 'source': 'switch:lever2', 'title': 'Lever',
     'toggles': ['door:cell2'], 'text': "Clank! Bars grind somewhere along the cell row."},
    {'id': 'evt:lever3', 'preset': 'switch', 'source': 'switch:lever3', 'title': 'Lever',
     'toggles': ['door:cell3'], 'text': "Clank! Bars grind somewhere along the cell row."},
    text('lever4', 'switch:lever4', 'Lever', "The lever is stuck.", notes="aaze0079:9."),
    find('bones_c1', 'deco:cell1_bones', 'Bones', 'bones_c1', [{'gold': 400}],
         "An adventurer who answered No: a find, then 'Nothing here.'"),
    find('bones_c2', 'deco:cell2_bones', 'Bones', 'bones_c2', [{'give_item': {'level': 4}}],
         "More bones: a find, then 'Nothing here.'"),
    {'id': 'evt:chest_cell3', 'preset': 'chest', 'source': 'chest:cell3', 'title': 'Chest'},
    # L3: the pool, the dials, the Soul Waters
    text('pool', 'platform:pool', 'Pool', "The water is stagnant.", notes="aaze0080:0."),
    text('statue3', 'deco:statue3', 'Statue', DIAL_STATUE, window=True, notes="aaze0080:3-4."),
    dial(1), dial(2), dial(3), dial(4),
    {'id': 'evt:soul_lever', 'preset': 'switch', 'source': 'switch:soul_lever', 'title': 'Lever',
     'condition': {'lua': DIALS_UP}, 'else_effects': [{'text': "The lever is stuck."}],
     'effects': [{'set': {'var': {'map_var': 'waters3'}, 'value': 1}}],
     'text': "The lever moves! Water gushes into the basin.",
     'notes': "With all four dials at 4 the lever moves and the Soul Waters run (waters3); otherwise stuck."},
    {'id': 'evt:soul3', 'preset': 'script', 'source': 'platform:soul_basin3', 'title': 'Soul Waters',
     'condition': {'map_var': 'waters3'},
     'effects': [{'lua': "evt.ForPlayer(Players.Current)\nXeenQuests.hook(\"m24.soul_waters_l3\")\n"
                         "evt.PlaySoundName(\"xeen_spring_drink\", 0, 0, 0)"}],
     'else_effects': [{'text': "The water is stagnant."}],
     'notes': "D-42 (5): A3's m24.soul_waters_l3 for the drinking member (player bit 11348: 1,000 experience once; "
              "then 'Refreshing.')."},
    text('niche3', 'panel:niche3', 'Soul Waters', "Soul Waters.", notes="aaze0080:1."),
    {'id': 'evt:negative', 'preset': 'script', 'source': 'platform:neg_basin', 'title': 'Negative Soul Waters',
     'lua': "evt.ForPlayer(Players.Current)\n"
            "if IsAtLeast(HP, 60) then\n    SubtractValue(HP, 25)\nend\n"
            "if IsAtLeast(SP, 30) then\n    SubtractValue(SP, 10)\nend\n"
            "evt.StatusText(\"Negative Soul Waters. You feel emptier.\")",
     'notes': "aaze0080:10: a draught that takes a little HP and SP from the drinking member and never kills."},
    {'id': 'evt:chest_negative', 'preset': 'chest', 'source': 'chest:negative', 'title': 'Chest'},
    # L4: the riddle, the levers, the Reserve
    text('statue4', 'platform:plinth4', 'Plaque', RIDDLE, window=True, notes="aaze0081:1-2."),
    text('statue4_deco', 'deco:statue4', 'Plaque', RIDDLE, window=True),
    {'id': 'evt:door_barracks', 'preset': 'door', 'source': 'door:barracks', 'title': 'Door'},
    find('purse', 'deco:barracks_straw_2', 'Straw', 'purse', [{'gold': 800}],
         "A purse under the straw: a find, then 'Nothing here.'"),
    {'id': 'evt:reserve_door', 'preset': 'door', 'source': 'door:reserve', 'title': "Minotaur's Private Reserve",
     'condition': {'map_var': 'riddle'}, 'locked_text': "The portcullis does not budge.",
     'notes': "The Reserve's portcullis (hover 'Minotaur's Private Reserve', aaze0081:3): the riddle's lever lifts it."},
    {'id': 'evt:chest_reserve', 'preset': 'chest', 'source': 'chest:reserve', 'title': 'Chest'},
    {'id': 'evt:soul4', 'preset': 'script', 'source': 'platform:soul_basin4', 'title': 'Soul Waters',
     'lua': "evt.ForPlayer(Players.Current)\nXeenQuests.hook(\"m24.soul_waters_l4\")\n"
            "evt.PlaySoundName(\"xeen_spring_drink\", 0, 0, 0)",
     'notes': "D-42 (5): A3's m24.soul_waters_l4 (player bit 11349: 2,000 experience once; then 'Refreshing.')."},
    text('niche4', 'panel:niche4', 'Soul Waters', "Minotaur's Private Reserve. Soul Waters."),
]
for r in range(4):
    for c in range(3):
        sid = 'switch:post_%d%d' % (r + 1, c + 1)
        if (r, c) == (2, 2):
            EVENTS.append({'id': 'evt:post_33', 'preset': 'switch', 'source': sid, 'title': 'Lever',
                           'opens': ['door:reserve'], 'effects': [{'set': {'var': {'map_var': 'riddle'}, 'value': 1}}],
                           'text': "The lever moves. Iron grinds: the Reserve's portcullis rises.",
                           'notes': "The riddle's lever: third row from the north, the east one (aaze0081:2). It "
                                    "raises the Reserve's portcullis for good."})
        else:
            EVENTS.append({'id': 'evt:post_%d%d' % (r + 1, c + 1), 'preset': 'text', 'source': sid,
                           'title': 'Lever', 'text': "The lever is stuck.", 'notes': "aaze0081:15."})
EVENTS += [
    # L5: the statues, the maze, the throne, the aviary
] + [text('alamar_%d' % n, 'deco:alamar_%d' % n, 'Statue', "The statue reads: " + VERSES[n], window=True,
          notes="aaze0082:18-22.") for n in range(1, 5)] + [
    {'id': 'evt:illusion', 'preset': 'door', 'source': 'door:illusion', 'title': 'Hedge', 'action': 'open',
     'text': "An illusion!", 'notes': "aaze0082:23: the wall under the second E is not there."},
    {'id': 'evt:chest_dead', 'preset': 'chest', 'source': 'chest:dead', 'title': 'Chest'},
    find('dead_bones', 'deco:dead_bones', 'Bones', 'dead_bones', [{'give_item': {'level': 4}}],
         "The lost adventurer's bones: a find, then 'Nothing here.'"),
    {'id': 'evt:throne', 'preset': 'script', 'source': 'platform:throne', 'title': 'Horned throne',
     'lua': "if not XeenQuests.hook(\"q-d25.throne\") then\n    XeenQuests.hook(\"q-d25.throne_again\")\nend",
     'notes': "Q-D25: q-d25.throne once (3,000, Minotaurs promoted, done 113500); later q-d25.throne_again."},
    {'id': 'evt:dais', 'preset': 'script', 'source': 'platform:dais', 'title': 'Horned throne',
     'lua': "if not XeenQuests.hook(\"q-d25.throne\") then\n    XeenQuests.hook(\"q-d25.throne_again\")\nend",
     'notes': "The dais: as the throne."},
] + [bird(*b) for b in BIRDS] + [
    {'id': 'evt:cage4', 'preset': 'script', 'source': 'panel:cage4', 'title': 'Parrot of Prophecy',
     'condition': {'not': {'map_var': 'parrot'}},
     'effects': [{'set': {'var': {'map_var': 'parrot'}, 'value': 1}}, {'message': PARROT}],
     'else_effects': [{'text': "An empty cage, door open."}], 'notes': "aaze0082:16-17."},
    {'id': 'evt:cage8', 'preset': 'script', 'source': 'panel:cage8', 'title': 'Songbird of Serenity',
     'lua': "XeenQuests.hook(\"m24.songbird\")",
     'notes': "The last cage: A3's m24.songbird (bird_freed 111480, the Songbird 12526, once; then 'An empty cage, "
              "door open.'). The lift runs from then on."},
]

WIRING = {'format': 0, 'variables': VARIABLES, 'events': EVENTS,
          'notes': "DD-12's events (gen.py): M24's hooks (the arrival and the plaque, the five gates' questions with "
                   "gate_open and gate_shut, the Soul Waters on L3 and L4, the Songbird), Q-D25's throne, the "
                   "hourglasses and the vault, the cell levers, the dials, the riddle's levers, the illusion, the "
                   "birds, the lift, the finds, the exit to D4."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

PROJECT = {
    'format': 0, 'id': 'xeen_dd12', 'name': 'Dungeon of Lost Souls', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-12', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(26, 11), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 3,
        'perception_difficulty': 3, 'refill_days': 672, 'music': 20, 'environment': 'cave',
        'lock_difficulty': 6,
        'slots': [{'monster': 'Xeen Minotaur', 'tier': 0, 'per_marker': F(2, 3), 'weight': 75},
                  {'monster': 'Xeen Minotaur', 'tier': 1, 'per_marker': F(1, 2), 'weight': 25}],
    },
    'neighbours': [
        {'id': 'exit:d4_door', 'to': 'xeen_d4.odm', 'kind': 'door', 'arrival': 'entrance:dd12_door',
         'arrival_hint': "On D4's Isle of Lost Souls, a step south of the ruined tower's door, facing south down the "
                         "path to the jetty (A6's entrance:dd12_door, (4096, -3072, 1376), facing 1536).",
         'notes': "D4 installed (A6). D4's door:dd12 (m24.isle_door, lost_souls_key) is to land at this map's "
                  "entrance:d4_isle in the entrance hall: (0, -352, 0) facing north (512)."}],
    'qbits': QBITS,
    'items': ITEMS,
    'notes': "Xeen design brief, DD-12 Dungeon of Lost Souls (D4's Isle of Lost Souls; Story M24 The Songbird of "
             "Serenity, Q-D25 The Minotaur's Labyrinth), class M, built from the MU-6 graph "
             "(devdocs/xeen/mockups/act4_graphs/dd12.graph.yml) with decider D-42 (mockups/act4_a8_decisions.md), "
             "which wins. Party 37-39; 45 placed monsters of the minotaur family (D-42 (1)): 11090 Minotaur 38 (30), "
             "11091 Gorgon 45 (12), 11092 Minotaur Lord 55 (3). Kill XP 95,145 for the party, 23.79k per member. "
             "Rest encounters 10 % from the minotaurs only (D-42). Treasure 4 (the Reserve's hoard 5), music 20. "
             "M24's and Q-D25's bits through A3's hooks; the map's qbits 117440 (arrived_once, A3's) and "
             "117441-117445 (the five gates answered Yes), block 117440-117479. Player bits 11348-11349 (the Soul "
             "Waters) are A3's, set by the hooks. Map card 9165.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Plan (L1 words; L2 adds extents, floors and heights)

T_TOWER = "D4's towers kit: hkm2b rubble masonry, red rock floor cfb1, open to the sky"
T_BRICK = "MM7 The Maze (d02): grey brick cwb, red rock floor cfb1, green stone ceiling ceb1sa"
T_ROCK = "d02's red rock cwb1, cfb1, ceb1sa"
T_HALL = "d02's grey brick cwb, flags t5s1fl, the carved ceiling t5s1c"
T_MAZE = "d02's ivy walls eswamp, cfb1, ceb1sa"


def placed(actor, count, level, notes=None):
    d = {'actor': actor, 'groups': 1, 'per_marker': F(count, count), 'levels': F(level, level), 'placed': True}
    if notes:
        d['notes'] = notes
    return d


def room_box(i):
    for r in ROOMS:
        if r['id'] == 'room:' + i:
            xs = [p[0] for p in r['outline']]
            ys = [p[1] for p in r['outline']]
            f0 = r['floor']
            f1 = r['slope']['to'] if 'slope' in r else f0
            return (max(xs) - min(xs), max(ys) - min(ys)), (f0 if f0 == f1 else F(min(f0, f1), max(f0, f1))), \
                r['ceiling'] - max(f0, f1)
    raise KeyError(i)


def sp(i, name, kind, size, purpose, theme, pop=None, treasure=None, **kw):
    ext, floor, clear = room_box(i)
    d = {'id': 'room:' + i, 'name': name, 'kind': kind, 'size': size, 'extent': F(*ext), 'floor': floor,
         'clear_height': clear, 'purpose': purpose, 'theme': theme}
    if pop:
        d['population'] = pop
    if treasure:
        d['treasure'] = treasure
    d.update(kw)
    return d


def chest(tier, notes):
    return [{'kind': 'chest', 'count': 1, 'tier': tier, 'items': F(2, 3), 'notes': notes}]


MN, GO, ML = 'Minotaur (11090)', 'Gorgon (11091)', 'Minotaur Lord (11092)'
SPACES = [
    # L1
    sp('entry', 'Entrance hall', 'room', 'M', "The ruined tower's base, open to the sky: the arrival from D4 and the "
       "way out (the double door), the carved plaque and the first gate (m24.arrival, m24.gate1); the lift head's "
       "arch. Quiet.", T_TOWER, safe=True, empty=True),
    sp('gallery1', 'Hall of storage', 'room', 'L', "Four 'Minotaur Storage' doors and arches; the hourglass panel in "
       "its west end.", T_BRICK, [placed(MN, 3, 38)]),
    sp('vault1', 'Hourglass vault', 'room', 'S', "Behind the panel that opens when all four hourglasses are turned: "
       "a chest.", T_BRICK, treasure=chest(4, "The minotaurs' strongbox."), empty=True),
    sp('store_a', 'Minotaur Storage (north-west)', 'room', 'M', "A storeroom; an hourglass.", T_BRICK,
       [placed(MN, 3, 38)]),
    sp('store_b', 'Minotaur Storage (north-east)', 'room', 'M', "A storeroom; an hourglass; the door to the stair "
       "head.", T_BRICK, empty=True),
    sp('store_c', 'Minotaur Storage (south-west)', 'room', 'M', "A storeroom; an hourglass.", T_BRICK,
       [placed(MN, 2, 38)]),
    sp('store_d', 'Minotaur Storage (south-east)', 'room', 'M', "A storeroom; an hourglass; bones (a find); the arch "
       "to the stair head.", T_BRICK, empty=True),
    sp('stair1', 'Stair head', 'room', 'S', "The stair down to L2.", T_BRICK, empty=True),
    sp('lift_head', 'Lift head', 'room', 'S', "The cage's upper stop beside the entrance hall: before the Songbird "
       "'The cage does not move. Far below, something sings.'", T_BRICK, empty=True),
    sp('shaft', 'Lift shaft', 'corridor', 'S', "The closed shaft from the aviary to the lift head.", T_BRICK,
       empty=True),
    sp('flight1', 'Stair to the cells', 'corridor', 'S', "L1 to L2.", T_BRICK, empty=True),
    # L2
    sp('statue_hall2', 'Hall of the statue', 'room', 'M', "The speaking statue (aaze0079:1); the stuck lever.",
       T_HALL, [placed(MN, 3, 38)]),
    sp('north_walk2', 'North walk', 'corridor', 'M', "The first cell's lever.", T_BRICK, [placed(MN, 2, 38)]),
    sp('south_walk2', 'South walk', 'corridor', 'M', "The cell row; the second cell's lever.", T_BRICK,
       [placed(GO, 2, 45)]),
    sp('cell1', 'First cell', 'room', 'S', "Bones (a find).", T_ROCK, empty=True),
    sp('cell2', 'Second cell', 'room', 'S', "Bones (a find).", T_ROCK, empty=True),
    sp('cell3', 'Third cell', 'room', 'S', "A chest.", T_ROCK, treasure=chest(4, "The third cell's chest."),
       empty=True),
    sp('gate_hall2', 'Second gate', 'room', 'M', "The second gate (m24.gate2); the third cell's lever.", T_HALL,
       [placed(MN, 2, 38)]),
    sp('flight2', 'Stair to the pool', 'corridor', 'S', "L2 to L3.", T_BRICK, empty=True),
    # L3
    sp('pool3', 'Stagnant pool', 'room', 'M', "'The water is stagnant' (aaze0080:0).", T_ROCK, [placed(MN, 3, 38)]),
    sp('dials3', 'Gallery of dials', 'corridor', 'M', "Four dials and the statue that says to turn them all up.",
       T_HALL, [placed(MN, 3, 38)]),
    sp('soul3', 'Soul Waters', 'room', 'M', "The fountain and its lever: all dials at 4, then the lever, then drink "
       "(m24.soul_waters_l3).", T_HALL, empty=True),
    sp('flooded3', 'Flooded walk', 'corridor', 'M', "The wet way round.", T_ROCK, [placed(GO, 3, 45)]),
    sp('negative3', 'Negative Soul Waters', 'room', 'M', "Black waters (you feel emptier); a chest.", T_ROCK,
       treasure=chest(4, "By the black waters."), empty=True),
    sp('gate_hall3', 'Third gate', 'room', 'M', "The third gate (m24.gate3). Quiet.", T_HALL, empty=True),
    sp('flight3', 'Stair to the Reserve', 'corridor', 'S', "L3 to L4.", T_BRICK, empty=True),
    # L4
    sp('plaque4', 'Hall of the plaque', 'room', 'M', "The riddle's plaque (aaze0081:2).", T_HALL,
       [placed(MN, 3, 38)]),
    sp('levers4', 'Hall of levers', 'room', 'L', "Twelve levers in four rows of three; the third row's east one "
       "lifts the Reserve's portcullis, the others are stuck.", T_HALL, [placed(MN, 2, 38), placed(GO, 2, 45)]),
    sp('barracks4', "Minotaurs' barracks", 'room', 'M', "Straw pallets, a trough; a purse (a find).", T_ROCK,
       [placed(GO, 1, 45)]),
    sp('reserve4', "The Minotaur's Private Reserve", 'room', 'M', "The hoard, casks, the second Soul Waters "
       "(m24.soul_waters_l4); a Minotaur Lord keeps it.", T_ROCK, [placed(ML, 1, 55, "the Reserve's keeper")],
       chest(5, "The hoard.")),
    sp('gate_hall4', 'Fourth gate', 'room', 'M', "The fourth gate (m24.gate4). Quiet.", T_HALL, empty=True),
    sp('flight4', 'Stair to the Soul Maze', 'corridor', 'S', "L4 to L5.", T_BRICK, empty=True),
    # L5
    sp('statues5', "Alamar's statues", 'room', 'M', "Four statues, one verse each (aaze0082:18-22); the maze's mouth.",
       T_HALL, [placed(GO, 2, 45)]),
    sp('maze_m', 'Soul Maze: the M', 'corridor', 'M', "The east half's first letter.", T_MAZE, [placed(MN, 1, 38)]),
    sp('maze_e2', 'Soul Maze: the second E', 'corridor', 'M', "The illusory wall under it.", T_MAZE,
       [placed(MN, 1, 38)]),
    sp('maze_t', 'Soul Maze: the T', 'corridor', 'M', "Down its stem to the heart.", T_MAZE, [placed(GO, 1, 45)]),
    sp('maze_l', 'Heart of the maze (the L)', 'room', 'M', "The horned throne (q-d25.throne) where both halves "
       "meet; a Minotaur Lord.", T_MAZE, [placed(ML, 1, 55, "the throne's keeper")]),
    sp('maze_e', 'Soul Maze: the E', 'corridor', 'M', "The west half.", T_MAZE, [placed(MN, 1, 38)]),
    sp('maze_h', 'Soul Maze: the H', 'corridor', 'M', "The west half.", T_MAZE, [placed(GO, 1, 45)]),
    sp('maze_s', 'Soul Maze: the S', 'corridor', 'M', "The west half's last letter, to the fifth gate.", T_MAZE,
       [placed(MN, 1, 38)]),
    sp('maze_dead', 'Maze dead end', 'room', 'S', "Behind the illusion: bones and a chest.", T_MAZE,
       treasure=chest(4, "The lost adventurer's chest."), empty=True),
    sp('gate_hall5', 'Fifth gate', 'room', 'M', "The fifth gate (m24.gate5) and a Minotaur Lord.", T_HALL,
       [placed(ML, 1, 55, "the gate's keeper")]),
    sp('aviary', 'The aviary', 'room', 'M', "Six stat birds (+2 each, once), the Parrot of Prophecy, the Songbird "
       "(m24.songbird); the lift.", T_HALL, empty=True),
]
for s in SPACES:
    if s.get('empty') and 'population' in s:
        del s['empty']


def link(i, a, b, kind, **kw):
    d = {'id': 'link:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
    d.update(kw)
    return d


LINKS = [
    link('gate1', 'entry', 'gallery1', 'door', motion='swing', notes="The first gate (two leaves): m24.gate1."),
    link('vault', 'gallery1', 'vault1', 'secret_door', notes="The hourglass panel."),
    link('gallery_store_a', 'gallery1', 'store_a', 'door', motion='swing'),
    link('gallery_store_c', 'gallery1', 'store_c', 'door', motion='swing'),
    link('store_a_b', 'store_a', 'store_b', 'open'),
    link('store_c_d', 'store_c', 'store_d', 'open'),
    link('store_b_stair', 'store_b', 'stair1', 'door', motion='swing'),
    link('store_d_stair', 'store_d', 'stair1', 'open'),
    link('gallery_lift', 'gallery1', 'lift_head', 'open'),
    link('lift', 'shaft', 'lift_head', 'lift', rise=2560, notes="The cage: after m24.bird_freed (D-42 (2))."),
    link('aviary_shaft', 'aviary', 'shaft', 'open'),
    link('stair1', 'statue_hall2', 'stair1', 'stairs', rise=640, notes="L1-L2 (flight1)."),
    link('statue_north', 'statue_hall2', 'north_walk2', 'open'),
    link('statue_south', 'statue_hall2', 'south_walk2', 'open'),
    link('cell1', 'south_walk2', 'cell1', 'door', motion='slide', notes="Bars: the north walk's lever."),
    link('cell2', 'south_walk2', 'cell2', 'door', motion='slide', notes="Bars: the south walk's lever."),
    link('cell3', 'south_walk2', 'cell3', 'door', motion='slide', notes="Bars: the gate hall's lever."),
    link('north_gate', 'north_walk2', 'gate_hall2', 'open'),
    link('south_gate', 'south_walk2', 'gate_hall2', 'open'),
    link('gate2', 'gate_hall2', 'flight2', 'door', motion='swing', notes="The second gate: m24.gate2."),
    link('stair2', 'pool3', 'flight2', 'stairs', rise=640, notes="L2-L3 (flight2)."),
    link('pool_dials', 'pool3', 'dials3', 'open'),
    link('pool_flooded', 'pool3', 'flooded3', 'open'),
    link('dials_soul', 'dials3', 'soul3', 'open'),
    link('flooded_negative', 'flooded3', 'negative3', 'open'),
    link('soul_gate', 'soul3', 'gate_hall3', 'open'),
    link('negative_gate', 'negative3', 'gate_hall3', 'open'),
    link('gate3', 'gate_hall3', 'flight3', 'door', motion='swing', notes="The third gate: m24.gate3."),
    link('stair3', 'plaque4', 'flight3', 'stairs', rise=640, notes="L3-L4 (flight3)."),
    link('plaque_levers', 'plaque4', 'levers4', 'open'),
    link('plaque_barracks', 'plaque4', 'barracks4', 'door', motion='swing'),
    link('barracks_levers', 'barracks4', 'levers4', 'open'),
    link('levers_reserve', 'levers4', 'reserve4', 'door', motion='slide', notes="The riddle's lever."),
    link('levers_gate', 'levers4', 'gate_hall4', 'open'),
    link('gate4', 'gate_hall4', 'flight4', 'door', motion='swing', notes="The fourth gate: m24.gate4."),
    link('stair4', 'statues5', 'flight4', 'stairs', rise=640, notes="L4-L5 (flight4)."),
    link('statues_maze', 'statues5', 'maze_m', 'open'),
    link('maze_m_e2', 'maze_m', 'maze_e2', 'open'),
    link('maze_e2_t', 'maze_e2', 'maze_t', 'open'),
    link('maze_t_l', 'maze_t', 'maze_l', 'open'),
    link('maze_l_e', 'maze_l', 'maze_e', 'open'),
    link('maze_e_h', 'maze_e', 'maze_h', 'open'),
    link('maze_h_s', 'maze_h', 'maze_s', 'open'),
    link('maze_s_gate', 'maze_s', 'gate_hall5', 'open'),
    link('illusion', 'maze_e2', 'maze_dead', 'secret_door', notes="'An illusion!'"),
    link('gate5', 'gate_hall5', 'aviary', 'door', motion='swing', notes="The fifth gate: m24.gate5."),
]
# D-89 identity (A8 s28): the three side cells cut into the rock of L3
SPACES += [sp(_k, 'Side cell', 'room', 'S', _n, T_ROCK, empty=True) for _k, _f, _n in _SIDE]
LINKS += [link(_k, _f, _k, 'open', notes="A low arch into a side cell.") for _k, _f, _n in _SIDE]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "Under the ruined tower on the Isle of Lost Souls, five floors go down, each shut by a cheerful gate "
                 "that asks a question and opens to a glad Yes. The minotaurs the coven threw out keep the "
                 "storerooms, the cells, the Soul Waters and their Private Reserve; at the bottom the Soul Maze spells "
                 "its maker's name in its walls, the horned throne at its heart, and beyond the fifth gate the aviary "
                 "of magic birds with the Songbird of Serenity in the last cage. A lift brings the party back up.",
        'purpose': "Story M24 (the carving, five yes-gates, the Songbird on L5); Q-D25 The Minotaur's Labyrinth (the "
                   "horned throne); the source's puzzles (hourglasses, cell levers, dials and the Soul Waters, the "
                   "lever riddle, the birds). Party 37-39; band 35-55; 45 monsters; treasure 4, the Reserve 5. About "
                   "40 minutes.",
        'mood': "A ruin open to the failing Darkside sun over grey brick storerooms; dark wet rock below; the ivy-grown "
                "Soul Maze, torchlit at its turns; the bright aviary at the bottom.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'loops': [
            {'id': 'loop:storage', 'spaces': ['room:gallery1', 'room:store_a', 'room:store_b', 'room:stair1',
                                              'room:store_d', 'room:store_c'],
             'notes': "Two ways through Minotaur Storage to the stair head."},
            {'id': 'loop:cells', 'spaces': ['room:statue_hall2', 'room:north_walk2', 'room:gate_hall2',
                                            'room:south_walk2'],
             'notes': "North and south walks round the cell block to the second gate."},
            {'id': 'loop:waters', 'spaces': ['room:pool3', 'room:dials3', 'room:soul3', 'room:gate_hall3',
                                             'room:negative3', 'room:flooded3'],
             'notes': "The dry way by the dials and the Soul Waters, the wet way by the Negative Soul Waters."},
            {'id': 'loop:barracks', 'spaces': ['room:plaque4', 'room:levers4', 'room:barracks4'],
             'notes': "Through the barracks or straight into the lever hall."},
            {'id': 'loop:lift', 'spaces': ['room:aviary', 'room:shaft', 'room:lift_head', 'room:gallery1'],
             'notes': "After the Songbird the lift closes the whole descent into a ring (D-42 (2))."}],
        'entrances': [
            {'id': 'entrance:d4_isle', 'space': 'room:entry', 'kind': 'both', 'neighbour': 'exit:d4_door',
             'facing': 'n', 'how': "D4's door:dd12 (m24.isle_door): inside the double door; out by it (the exit "
                                   "preset)."}],
        'critical_path': ['room:entry', 'room:gallery1', 'room:store_a', 'room:store_b', 'room:stair1',
                          'room:flight1', 'room:statue_hall2', 'room:north_walk2', 'room:gate_hall2', 'room:flight2',
                          'room:pool3', 'room:dials3', 'room:soul3', 'room:gate_hall3', 'room:flight3',
                          'room:plaque4', 'room:levers4', 'room:gate_hall4', 'room:flight4', 'room:statues5',
                          'room:maze_m', 'room:maze_e2', 'room:maze_t', 'room:maze_l', 'room:maze_e', 'room:maze_h',
                          'room:maze_s', 'room:gate_hall5', 'room:aviary'],
        'return_path': ['room:aviary', 'room:shaft', 'room:lift_head', 'room:gallery1', 'room:entry'],
        'goals': [
            {'id': 'goal:songbird', 'space': 'room:aviary', 'kind': 'take',
             'what': "The Songbird of Serenity from the last cage (m24.songbird, bird_freed)."},
            {'id': 'goal:throne', 'space': 'room:maze_l', 'kind': 'set',
             'what': "The horned throne at the maze's heart (q-d25.throne)."},
            {'id': 'goal:waters', 'space': 'room:soul3', 'kind': 'set',
             'what': "The Soul Waters (m24.soul_waters_l3, _l4): experience once per member."}],
        'atmosphere': "The entrance hall open to the failing sun (preset xeen_darkside_fading); torchlit brick and "
                      "rock (ambient 12-18), the maze dark (8), the aviary bright (20). Music 20. Sounds: drips "
                      "(xeen_amb_mine), wind over the broken roof, water at the pool and the Soul Waters, braziers.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': len(CHESTS), 'doors': len(DOORS), 'fixed_actors': len(MONSTERS), 'loops': 5,
                   'monsters_about': 45, 'rooms': len(ROOMS), 'sectors': len(ROOMS), 'spawn_points': 0,
                   'floor_area_millions': 38},
        'notes': "Class M (MAPS, Dungeons): 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors. "
                 "The graph's spaces as rooms, the stairs and the lift shaft rooms of their own; the Soul Maze's two "
                 "halves (maze_w, maze_e) and its heart become the seven letters SHELTEM (D-42 (3)), the heart the "
                 "L; the cells of the lost three cells off the south walk.",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    elif level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return d


DIAGRAM = """ L1 (0)     [Lift head]--[ENTRANCE HALL: plaque, door to D4]==gate 1==[Hall of storage]##[Hourglass vault $]
                                                          |door        |door
                                         [Storage NW, NE: hourglasses]  [Storage SW, SE: hourglasses]
                                                          \\door        /
                                                         [Stair head]
 L2 (-640)  [Hall of the statue]--[North walk: lever]--[Second gate]==gate 2==> stair
                  \\--[South walk: lever]=bars=[3 cells $]--/
 L3 (-1280) [Stagnant pool]--[Gallery of dials]--[SOUL WATERS: lever]--[Third gate]==gate 3==> stair
                  \\--[Flooded walk]--[Negative Soul Waters $]--/
 L4 (-1920) [Hall of the plaque]--[HALL OF LEVERS: 12]--[Fourth gate]==gate 4==> stair
                  \\door [Barracks]--/      ||portcullis
                                     [Reserve: Lord, Soul Waters $$]
 L5 (-2560) [Alamar's statues]--[M]--[E]--[T]--[L: HORNED THRONE, Lord]--[E]--[H]--[S]--[Fifth gate: Lord]
                                      ##illusion                                  ==gate 5==[AVIARY: birds, Songbird]
                                     [Dead end $]                                        ||lift up to the lift head

 $ chest   == door   ## secret   -- open   || lift / portcullis
"""


def write(level):
    d = OUT + '/' + level
    os.makedirs(d, exist_ok=True)
    dump(d + '/project.yml', dict(PROJECT, identity=IDENTITY) if level == 'L4' else PROJECT)
    dump(d + '/plan.yml', plan(level))
    open(d + '/diagram.txt', 'w').write(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(d + '/rooms.yml', {'format': 0, 'themes': THEMES, 'defaults': {'theme': 'theme:brick', 'ambient': 14},
                                'rooms': ROOMS, 'openings': OPENINGS,
                                'notes': "DD-12 at L3/L4: %d rooms on five floors in the plan's frame (x east, y "
                                         "north). Written by output/studio_cal/dd12/tools/gen.py." % len(ROOMS)})
    if level == 'L4':
        dump(d + '/objects.yml', OBJECTS)
        dump(d + '/wiring.yml', WIRING)
        dump(d + '/atmosphere.yml', {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_fading'},
                                     'notes': "The entrance hall is the ruined tower's roofless base (sky faces): "
                                              "the failing sun of Act IV before M27 (D-42)."})


if __name__ == '__main__':
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
