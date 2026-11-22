"""D3 Sandcaster and the Aging Forest, L3/L4: the land (height grid, height points, terraces, cliffs, water, roads,
ground). A5, 2026-11-20 (seventh session), after X4's land.py.

Used by gen.py. Places and roads come from gen_l1.py (the approved L1 with D-28). Cells [x, y], x east, y south;
X = (x - 64) * 512, Y = (64 - y) * 512. Heights in map units above the stars below the rim (0). D-28 (7): the broken
Wrath crest (3,100-3,400) east of the river, the Lakeside saddle (<= 1,900) on the D4 road, the river's source a gorge,
the west-bank hills (2,400), the Howling ridge (1,900-2,200) meeting D2's east-edge heights.
"""
import math

import gen_l1 as L1
import kit as K

RIM_X, RIM_Y = L1.RIM_X, L1.RIM_Y      # 104, 104: the world rim (D-23), the stars below
RIVER_LVL = 992        # the River of Wrath (L1: 1,000; heights go in 32s)
POND_LVL = 864         # Venom Pond (D-28: the low end of the relief)
TOWN_H = 1504          # Sandcaster's terrace
QUARTER_H = 1728       # the wizard quarter, a walled terrace over the city (D-28)
YARD_H = 1312          # the caravan yard outside the south gate
CROSS_H = 1248         # the Crossroads' ring
KNOLL_H = 1952         # the Eastern Tower's knoll
CELIA_H = 1248
THAD_H = 960           # Thaddeus's yard
GLADE_H = 1120         # Cornelius's glade


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def bump(x, y, cx, cy, r, h):
    d = math.hypot(x - cx, y - cy)
    return h * (1 - smooth(d / r)) if d < r else 0.0


def peak(h, x, y, cx, cy, r, top):
    """Raise h toward `top` at (cx, cy), fading to nothing at r (never lowers)."""
    d = math.hypot(x - cx, y - cy)
    if d >= r or top <= h:
        return h
    return h + (top - h) * (1 - smooth(d / r))


def dist_to_line(px, py, line):
    return min(K.seg_dist((px, py), a, b) for a, b in zip(line, line[1:]))


def along(px, py, line):
    """(distance to the line, the profile parameter: cells along the line from its first point to the nearest)."""
    best = (1e9, 0.0)
    run = 0.0
    for a, b in zip(line, line[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        t = 0 if L == 0 else max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / (L * L)))
        d = math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)
        if d < best[0]:
            best = (d, run + t * L)
        run += L
    return best


def interp(table, v):
    if v <= table[0][0]:
        return table[0][1]
    for (a, ha), (b, hb) in zip(table, table[1:]):
        if v <= b:
            return ha + (hb - ha) * (v - a) / float(b - a)
    return table[-1][1]


# ---------------------------------------------------------------- the river, its gorge and the pond
RIVER_LINE = [[81, 22], [80, 26], [79, 32], [78, 38], [77, 42], [76, 46], [77, 50], [79, 53], [82, 57], [88, 60],
              [94, 62], [100, 63], [104, 64]]     # L1's line on whole cells, the gorge walls two cells either side
GORGE_END_Y = 38            # the gorge's cliffs run from the spring to here; below, the cut opens to meadows
POND = [list(p) for p in L1.VENOM_POND['polygon']]

# ---------------------------------------------------------------- the Wrath crest (D-28): broken, 3,100-3,400
# eighth session (the lane review: the crest read as smooth bare-dirt cones): the massif keeps its knobs (3,100-3,400)
# and is broken by rock needles beside the knobs (SPIRES: sheer sides), shelves on its flanks (crest_cliffs: steps
# of 256-384) and rough ground between them; its steep faces take the slope layer's rock (D3's slope band in the
# terrain materials' world.yml) and rocks line the ridge (scatter.py)
CREST = [(92, 27, 5.0, 3300), (96, 24, 5.0, 3400), (100, 30, 4.5, 3200), (94, 34, 4.0, 3100), (99, 37, 4.0, 3150),
         (98, 27, 3.0, 2600)]
# the needles: (cell, height over the land there); the top is held at most at Wrathtop's 3,392
SPIRE_AT = [((93, 26), 352), ((95, 25), 320), ((98, 25), 288), ((101, 28), 320), ((95, 33), 352), ((100, 36), 320),
            ((97, 33), 288), ((92, 30), 256)]
# the ridge line along the knobs (for the rocks along it and the markers kept off it)
RIDGE_LINE = [[90, 30], [92, 27], [94, 25], [96, 24], [98, 26], [100, 30], [100, 34], [99, 37]]
# a broken comb of needles along the ridge line, every other cell, alternately either side of it
RIDGE_SPIRES = [((91, 28), 320), ((94, 24), 256), ((97, 24), 224), ((99, 28), 352), ((101, 31), 288),
                ((99, 35), 320), ((101, 33), 256), ((90, 31), 288), ((93, 27), 256)]
# the crest's north shoulder (the high path, the courier's satchel) and its south foot behind the knoll
SHOULDERS = [(99, 20.5, 5.0, 2300), (95, 40.5, 3.5, 2200)]
# the west-bank hills over the gorge (D-28: about 2,400)
WEST_BANK = [(73, 23, 6.0, 2400), (70, 29, 5.0, 2100), (76, 28, 3.5, 2050)]
# the Howling ridge (D-28: 1,900-2,200), its crest height along its line
HOWL_LINE = [[24, 56], [25, 66], [23.5, 77], [24, 88], [27, 98]]
HOWL_H = [(0, 1950), (10, 2150), (21, 2200), (32, 2050), (42, 1900)]

# the Lakeside road's bed (D-28: the saddle at most 1,900): (cells along the road from the east fork, height)
LAKESIDE = [[82, 45], [84, 40], [86, 34], [87.5, 28], [88, 24], [88, 20], [88, 0]]
LAKESIDE_H = [(0, 1248), (5.4, 1376), (11.7, 1568), (17.9, 1760), (21.9, 1856), (25.9, 1760), (45.9, 1760)]
SPRING_PATH = [[87.5, 28], [85.5, 25.0], [84.0, 22.6]]
SPRING_PATH_H = [(0, 1760), (3.6, 1730), (6.4, 1700)]
HIGH_PATH = [[88, 22], [92, 21], [95.5, 20.5], [98, 21]]
HIGH_PATH_H = [(0, 1820), (4.1, 1980), (7.6, 2180), (10.1, 2280)]

# ---------------------------------------------------------------- level places: (polygon, height, blend cells)
PADS = [
    (L1.TOWNS['zone:thaddeus_yard'], THAD_H, 3),
    (L1.TOWNS['zone:cornelius_glade'], GLADE_H, 3),
    (L1.TOWNS['zone:tower_knoll'], KNOLL_H, 4),
    (L1.TOWNS['zone:celia_yard'], CELIA_H, 2),
    (L1.TOWNS['town:crossroads'], CROSS_H, 3),
    ([[33, 40], [44, 40], [44, 45], [33, 45]], YARD_H, 2),                 # the caravan yard and the gate fork
    (L1.TOWNS['town:sandcaster'], TOWN_H, 2.5),
    (L1.TOWNS['zone:wizard_quarter'], QUARTER_H, 0),                      # a stepped terrace: the cliffs below
]
CALM = [(37, 30, 13), (60, 44, 8), (97, 46, 6), (81, 76, 5), (40, 72, 5), (65, 47, 4), (38.5, 42, 5), (20, 44, 4),
        (88, 20, 3), (50.5, 27, 3), (63.5, 28.5, 2.5), (45, 47.5, 3), (101, 57, 3), (88, 65, 3), (95, 95, 3),
        (46, 101, 3), (53, 65, 3), (53, 71, 2.5), (57.5, 25.5, 2.5)]


def calm_weight(x, y):
    w = 1.0
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 3.0))
    return w


def roll(x, y):
    v = (120 * math.sin(x / 3.3 + 0.4) * math.sin(y / 3.9 + 1.3) + 80 * math.sin((x + 1.3 * y) / 4.4 + 0.9)
         + 45 * math.sin((x - 1.6 * y) / 2.2))
    return calm_weight(x, y) * v


def base(x, y):
    h = 1260.0
    # the land falls gently south toward the forest and the fen, east of the forest road toward the river meadows
    h -= 120 * smooth((y - 48) / 22.0)
    h -= 170 * smooth((y - 64) / 16.0) * smooth((x - 56) / 10.0)
    h -= 90 * smooth((x - 80) / 20.0) * smooth((y - 50) / 8.0)
    # the desert edge: dunes north of the Crossroads to the river's gorge
    dune = smooth((40 - y) / 12.0) * smooth((x - 45) / 4.0) * smooth((84 - x) / 4.0)
    h += 330 * dune + 110 * dune * math.sin(x / 2.3 + y / 3.1) * math.sin(y / 2.7 - x / 5.0)
    # the caravan valley (1,300, D2's edge level) under the city's terrace
    h += 50 * smooth((30 - x) / 10.0) * smooth(1 - abs(y - 44) / 12.0)
    # the last Gemstone crags (north-west, beyond the box)
    h += bump(x, y, 6, 12, 16, 2200) + bump(x, y, 15, 4, 12, 1400) + bump(x, y, 2, 26, 10, 1200)
    # the Howling ridge: its crest along HOWL_LINE, flanks of about 140 a cell
    d, s = along(x, y, HOWL_LINE)
    if y > 50:
        top = interp(HOWL_H, s) + 50 * math.sin(s / 1.7)
        h = max(h, h + (top - 95 * d - h) * smooth((y - 50) / 4.0))
    for (cx, cy, r, top) in WEST_BANK + SHOULDERS + CREST:
        h = peak(h, x, y, cx, cy, r, top)
    # crags on the crest
    h += 140 * math.sin(x / 1.9 + y / 1.4) * math.sin(y / 2.6 - x / 3.7) * smooth((h - 2300) / 600.0)
    h += roll(x, y)
    return h


def raw_height(x, y):
    if x > RIM_X + 0.2 or y > RIM_Y + 0.2:
        return 0
    h = base(x, y)
    # the Lakeside road: the D4 road over its saddle (D-28: <= 1,900), level across, a shelf under the crest
    for line, prof, half, blend in ((LAKESIDE, LAKESIDE_H, 1.6, 3.0), (SPRING_PATH, SPRING_PATH_H, 1.0, 2.0),
                                    (HIGH_PATH, HIGH_PATH_H, 1.0, 2.5)):
        d, s = along(x, y, line)
        if d < half + blend:
            target = interp(prof, s)
            w = 1 - smooth((d - half) / blend)
            h = h * (1 - w) + target * w
    # the river: the gorge (cliffs, gen's CLIFFS) from the spring to y 36, then a cut opening to the meadows
    d = dist_to_line(x, y, RIVER_LINE)
    bank = RIVER_LVL + 64
    if y < GORGE_END_Y:
        pass                                   # the gorge is a cut (gorge_cut): its rims keep the land's height
    elif d < 6:
        h = bank + (h - bank) * smooth((d - 1.4) / 4.6)
    # Venom Pond and its fen shore
    if K.inside((x, y), POND):
        return POND_LVL - 64
    e = K.edge_dist((x, y), POND)
    if e < 4:
        h = POND_LVL + 40 + (h - POND_LVL - 40) * smooth((e - 0.3) / 3.7)
    # the level places
    for poly, ph, blend in PADS:
        if K.inside((x, y), poly):
            h = ph
        elif blend:
            e = K.edge_dist((x, y), poly)
            if e < blend:
                h = ph + (h - ph) * smooth(e / blend)
    # the rim's lip: the land ends in a cliff a little above 1,000
    lip = min(RIM_X - x, RIM_Y - y)
    if lip < 3:
        h = max(h, 1000 + 40 * lip)
    return h


def grid_rows(step=4, unit=32):
    rows = []
    for j in range(128 // step):
        row = []
        for i in range(128 // step):
            cx, cy = step * i + step / 2, step * j + step / 2
            row.append(int(round(raw_height(cx, cy) / unit)))
        rows.append(row)
    return rows


# height points (each corrects the grid where it stands, fading over a grid step): the peaks and the passes
POINTS = [
    ([88, 24], 1856, 'the Lakeside saddle on the D4 road (D-28: at most 1,900)'),
    ([88, 20], 1760, 'the D4 arrival'), ([86, 34], 1568, None), ([84, 40], 1376, None),
    ([73, 23], 2400, 'the west-bank hills over the gorge'), ([70, 29], 2112, None),
    ([25, 66], 2144, 'the Howling ridge'), ([24, 77], 2208, 'the howling stone'), ([24, 88], 2048, None),
    ([24, 57], 1952, None), ([27, 97], 1888, None),
    ([99, 21], 2272, "the crest's north shoulder: the courier's satchel"),
    ([92, 27], 3232, 'the Wrath crest (D-28)'), ([96, 24], 3392, "Wrathtop, the crest's high point"),
    ([100, 30], 3200, None), ([94, 34], 3104, None), ([99, 37], 3136, None), ([98, 27], 2592, 'the crest broken'),
    # the crest broken into knobs, notches and scree shoulders (A5: the grid alone drew smooth cones)
    ([90, 30], 2688, None), ([93, 30], 2912, None), ([95, 28], 3040, None), ([97, 31], 2720, None),
    ([101, 26], 2880, None), ([94, 37], 2592, None), ([91, 33], 2464, None), ([100, 34], 2944, None),
    ([97, 35], 2496, None), ([102, 37], 2656, None), ([95, 21], 2560, None), ([93, 24], 2976, None),
    ([98, 24], 3168, None), ([90, 26], 2400, None), ([103, 31], 2752, None), ([96, 39], 2304, None),
    ([20, 44], 1312, "the D2 arrival (D2's east edge 1,300)"),
    # the spring's rock face: the land over the gorge head stands high, so the fall comes out of the face
    ([81, 18], 1856, "over the gorge head: the spring's rock face"), ([79, 19], 1824, None), ([83, 19], 1792, None),
]


def gorge_points():
    """Height points on the gorge's two cliff lines (whole cells, every cell from the head to y 36): the rims stand at
    the land's height there, so the cliffs break down to the river (the grid alone rounds the gorge into a valley)."""
    out = []
    west, east = gorge_walls()
    for line, low in ((west, 1700), (east, 1600)):
        for a, b in zip(line, line[1:]):
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
            for k in range(n):
                x = round(a[0] + (b[0] - a[0]) * k / n)
                y = round(a[1] + (b[1] - a[1]) * k / n)
                h = max(low, base(x, y))
                if (x, y) not in [tuple(q[0]) for q in out]:
                    out.append(([x, y], int(round(h / 32.0)) * 32, None))
    return out


def LD_dist(x, y):
    return dist_to_line(x, y, RIVER_LINE)


def heights():
    return {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(),
                 'notes': 'Written by output/studio_cal/d3/tools/land.py from its height function.'},
        'points': [dict({'at': at, 'h': h}, **({'notes': n} if n else {})) for at, h, n in POINTS + gorge_points()],
        'spires': spires(),
        'peaks': [{'polygon': [[90.5, 24], [101.5, 22.5], [102, 38], [94, 39], [90.5, 32]], 'count': 14,
                   'height': [2880, 3328], 'radius': [0.8, 1.4], 'profile': 'cone', 'width': 2, 'spacing': 2,
                   'seed': 5, 'notes': 'The Wrath crest broken into crags (eighth session, the lane review)'}],
        'rough': [{'polygon': [[91, 23], [102, 23], [102.5, 39], [92, 39.5], [90.5, 33]], 'amount': 24,
                   'notes': 'The Wrath crest: broken, crags and scree between the combs (D-28)'},
                  {'polygon': [[67, 19], [79, 19], [77, 33], [68, 33]], 'amount': 0.6,
                   'notes': 'the west-bank hills'}],
        'terraces': terraces(),
        'cuts': [gorge_cut()],
        'cliffs': cliffs(),
    }


def spires():
    """The crest's rock needles: 2 x 2 nodes standing sheer over the land of the knobs' flanks."""
    pts = dict((tuple(at), h) for at, h, _n in POINTS)
    out = []
    for (x, y), over in SPIRE_AT + RIDGE_SPIRES:
        land = pts.get((x, y), raw_height(x, y))
        out.append({'at': [x, y], 'height': int(min(3392, land + over)) // 32 * 32, 'width': 2,
                    'notes': 'a rock needle on the Wrath crest'})
    return out


def terraces():
    out = []
    for poly, h, _ in PADS:
        out.append({'polygon': [list(p) for p in poly], 'height': h, 'slope': 0})
    out[-2]['notes'] = "Sandcaster's terrace, 200 over the caravan valley; the city wall stands on its edge."
    out[-1]['notes'] = 'The wizard quarter (D-28): a walled terrace 224 over the city, its retaining wall below.'
    return out


def gorge_walls():
    """The gorge's two cliff lines, two cells either side of the river's (rounded) line from the spring to y 36."""
    west = [[80, 21], [79, 26], [78, 32], [77, 38]]
    east = [[83, 21], [82, 26], [81, 32], [80, 38]]
    return west, east


CREST_SHELVES = [
        {'line': [[93, 22], [92, 24], [91, 26]], 'drop': 320, 'down': 'right',
         'notes': "A shelf on the Wrath crest's west face (eighth session: the crest broken, D-28)."},
        {'line': [[96, 30], [97, 32], [97, 35]], 'drop': 288, 'down': 'right',
         'notes': "A shelf under the crest's middle knob."},
        {'line': [[91, 35], [93, 36], [95, 38]], 'drop': 256, 'down': 'right',
         'notes': "A shelf on the crest's south face."},
]


def gorge_cut():
    """The gorge (eighth session, the lane review: it read as a shallow hollow with pools): a cut whose outline is the
    two walls and the head, sheer one-node walls as high as the rims (600-800 at the head, about 400 where it opens),
    its floor under the river's level, open to the south where the river runs out to the meadows. The spring's fall
    comes out of the head wall."""
    west, east = gorge_walls()
    poly = [list(p) for p in west] + [list(p) for p in reversed(east)]
    return {'polygon': poly, 'floor': RIVER_LVL - 32, 'open': [len(west) - 1], 'slope': 3,
            'notes': "The gorge of the River of Wrath below the spring (D-28: the river's source a gorge)."}


def cliffs():
    return [
        {'line': [[RIM_X, 0], [RIM_X, 64], [RIM_X, RIM_Y]], 'drop': 1000, 'down': 'left',
         'notes': "The east rim (north to south, the low side east): the land ends above the stars; the Wrath Falls "
                  "go over it at y 64."},
        {'line': [[RIM_X, RIM_Y], [52, RIM_Y], [0, RIM_Y]], 'drop': 1000, 'down': 'left',
         'notes': 'The south rim at y 104 (D-23), east to west, the low side south.'},
        *CREST_SHELVES,
        {'line': [[40, 20], [40, 27], [47, 27]], 'drop': QUARTER_H - TOWN_H, 'down': 'right',
         'notes': "The wizard quarter's step (west then south face, the low side outside); its retaining wall "
                  'stands in front of it.'},
    ]


def water():
    return {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': L1.RIM_SEA['polygon'],
             'notes': 'Below the rim: stands for the stars.'},
            {'id': 'water:venom_pond', 'kind': 'pond', 'level': POND_LVL, 'polygon': POND,
             'notes': 'Venom Pond: green, still, reeds; it seeps into the fen.'},
        ],
        'rivers': [{'id': 'water:wrath', 'line': RIVER_LINE,
                    'width_cells': 2, 'level': RIVER_LVL,
                    'notes': 'The River of Wrath (D-23, D-28): from the cave at the gorge head south between the '
                             'west-bank hills and the Lakeside shelf, under Wrath Bridge, east through the meadows '
                             'and over the east rim at the Wrath Falls; it touches no map edge.'}],
    }


# Sandcaster's streets (town_feel: doors by a road or lane, the town's cells of road or dirt): sandstone setts
TOWN_STREETS = [
    ('link:gate_street', [[36.5, 39], [36.5, 34]], 'road'),
    ('link:bazaar_street', [[41, 31.5], [47, 31.5]], 'road'),
    ('link:west_lane', [[31.5, 26], [31.5, 36.5]], 'lane'),
    ('link:guild_row', [[29.5, 24], [39.5, 24]], 'lane'),
]


def roads():
    out = [{'link': link, 'line': line, 'width': w, 'surface': 'road_flagstone'} for link, line, w in TOWN_STREETS]
    for link, line, width, surface in L1.ROADS:
        line = [[round(a * 2) / 2, round(b * 2) / 2] for a, b in line]
        out.append({'link': link, 'line': line, 'width': width, 'surface': surface or 'dirt'})
    return out


def ground():
    return [
        {'material': 'grass', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'dry olive grass and scrub (the meadow tint dries the crests)'},
        {'material': 'sand', 'polygon': [[0, 0], [82, 0], [82, 18], [80, 26], [77, 36], [72, 40], [64, 36],
                                           [52, 37], [44, 44], [36, 45], [28, 47], [0, 50]],
         'notes': 'the desert edge, the caravan valley and Sandcaster: sand'},
        {'material': 'dirt', 'steeper_than': 800,
         'polygon': [[84, 0], [RIM_X, 0], [RIM_X, 41], [92, 41], [89, 30], [86, 18]],
         'notes': "the Wrath crest: bare scree on its steep faces only; dry grass and scrub between (ninth pass)"},
        {'material': 'dirt', 'polygon': [[30, 50], [40, 49], [50, 48], [54, 52], [60, 56], [62, 64], [64, 74],
                                         [62, 86], [60, RIM_Y], [32, RIM_Y], [34, 92], [36, 80], [38, 64], [36, 54]],
         'notes': "the Aging Forest's floor of fallen leaves"},
        {'material': 'dirt', 'polygon': [[19, 54], [30, 52], [33, 60], [31, 80], [30, RIM_Y], [19, RIM_Y]],
         'notes': "the Howling ridge's stony crown under the old wood"},
        {'material': 'dirt', 'polygon': [[55, 39], [65, 39], [65, 49], [55, 49]], 'notes': "the Crossroads' ring"},
        {'material': 'dirt', 'polygon': [[27, 20], [47, 20], [47, 39], [27, 39]],
         'notes': "Sandcaster's beaten lanes and yards inside the walls"},
        {'material': 'dirt', 'polygon': [[34, 40], [43, 40], [43, 44], [34, 44]], 'notes': 'the caravan yard'},
        {'material': 'dirt', 'polygon': [[78, 73], [84, 73], [84, 79], [78, 79]], 'notes': "Thaddeus's yard"},
    ]
