"""X4 Burlock Savannah, L3/L4: the land (height grid, terraces, cliffs, water, roads, ground). A5, 2026-11-20.

Used by gen.py. The plan's places and roads come from gen_l1.py (the approved L1, with D-11.2/5/6). Cells [x, y], x
east, y south; X = (x - 64) * 512, Y = (64 - y) * 512. Heights in map units above the stars below the north rim (0).
"""
import math

import gen_l1 as L1
import kit as K

RIVER_LVL = 640        # the Great River (L1: 650; ODM heights go in 32s)
BANK = 704
CASTLE_H = 1888        # Castle Burlock's rise (D-11.2: 1,900)
VILLAGE_H = 1312       # the walled village before the gate
LISTS_H = 1088         # the jousting lists
ASP_H = 1056           # Asp's terrace
TARN_H = 1536          # the tarn above the falls
RIM_Y = L1.RIM_Y       # 24


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def interp(table, v):
    if v <= table[0][0]:
        return table[0][1]
    for (a, ha), (b, hb) in zip(table, table[1:]):
        if v <= b:
            return ha + (hb - ha) * (v - a) / float(b - a)
    return table[-1][1]


def bump(x, y, cx, cy, r, h):
    d = math.hypot(x - cx, y - cy)
    return h * (1 - smooth(d / r)) if d < r else 0.0


def dist_to_line(px, py, line):
    return min(K.seg_dist((px, py), a, b) for a, b in zip(line, line[1:]))


# ---------------------------------------------------------------- the Gargoyle Range
CREST = [(0, 2900), (14, 2900), (26, 3300), (38, 3600), (50, 3900), (62, 3400), (72, 3700), (84, 3400), (94, 3000),
         (102, 2400), (110, 2100), (128, 2000)]
FOOT_Y = [(0, 49), (18, 49), (28, 47), (36, 46), (44, 45), (52, 44), (56, 43), (60, 42.5), (68, 43), (74, 44),
          (78, 41), (83, 41), (86, 44), (94, 42), (100, 37), (106, 33), (128, 33)]


def crest_y(x):
    return 30.0 + 1.2 * math.sin(x / 6.3)


# ---------------------------------------------------------------- level places: (polygon, height, blend cells)
# Applied in order (the later wins); inside a polygon the land is the place's height, outside it runs back over the
# blend. The terraces of the sketch (slope 0) hold them exactly; the grid only brings the land round them near.
PADS = [
    # D-142 (2026-11-25): the camp 4 cells east and 2 north, its fighters 4,096+ from the X6 arrival (20, 60)
    ([[23, 49], [34, 49], [34, 57], [23, 57]], 1344, 3),            # the barbarian camp's flat
    ([[37, 50], [44, 50], [44, 56], [37, 56]], 1376, 3),            # Carlawna's yard
    ([[21, 65], [31, 65], [31, 75], [21, 75]], 1120, 3),            # the Autumn Druid's grove
    ([[46, 65], [50, 65], [50, 68], [46, 68]], 1376, 3),            # the obelisk's knoll
    ([[33, 78], [52, 78], [52, 92], [33, 92]], ASP_H, 4),           # Asp
    ([[64, 63], [75, 63], [75, 73], [64, 73]], LISTS_H, 3),         # the jousting lists
    ([[58, 73], [66, 73], [66, 79], [58, 79]], 1056, 3),            # Burlock Cross
    ([[53, 100], [60, 100], [60, 106], [53, 106]], 1024, 3),        # the renegade knights' camp
    ([[96, 57], [104, 57], [104, 65], [96, 65]], 1408, 3),          # Falagar's lava shoulder
    ([[103, 83], [109, 83], [109, 89], [103, 89]], 1760, 2),        # the ogres' hollow
    ([[105, 92], [109, 92], [109, 99], [105, 99]], 2144, 3),        # the hill the west adit runs into (640 over its pad)
    ([[100, 93], [104, 93], [104, 98], [100, 98]], 1504, 2),        # before the west adit
    ([[101, 43], [107, 43], [107, 49], [101, 49]], 1760, 2),        # the Shrine of Fire
    ([[73, 46.5], [76.5, 46.5], [76.5, 50], [73, 50]], 1088, 2),   # the Olympian Fountain's ledge (off the pool)
    ([[55, 50], [69, 50], [69, 62], [55, 62]], VILLAGE_H, 3),       # the walled village
    ([[56, 43], [68, 43], [68, 50], [56, 50]], CASTLE_H, 2),        # Castle Burlock's rise
]
# quiet ground: no rolling inside these (x0, y0, x1, y1) boxes and circles (x, y, r)
CALM_BOXES = [(52, 42, 76, 80), (32, 77, 53, 93)]
CALM = [(28, 53, 4), (40.5, 53, 3), (26, 70, 4), (48, 66.5, 3), (87, 87, 3), (82, 101, 4), (96, 107, 4),
        (36, 107, 4), (20, 60, 3), (107, 66.5, 3), (100, 61, 3), (106, 86, 3), (102, 95.5, 3), (104, 46, 3),
        (77, 77, 3), (93, 50, 3), (21, 83, 2), (69, 106, 2), (56, 103, 4), (60, 93, 3), (27, 96, 3), (70, 86, 3),
        (88, 37, 2)]


def calm_weight(x, y):
    w = 1.0
    for (x0, y0, x1, y1) in CALM_BOXES:
        dx = max(x0 - x, 0, x - x1)
        dy = max(y0 - y, 0, y - y1)
        w = min(w, smooth(math.hypot(dx, dy) / 4.0))
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 3.0))
    return w


def roll(x, y):
    v = (150 * math.sin(x / 3.1 + 0.7) * math.sin(y / 3.7 + 1.1) + 110 * math.sin((x + 1.4 * y) / 4.6 + 0.3)
         + 60 * math.sin((x - 1.7 * y) / 2.3))
    return calm_weight(x, y) * max(v, -200.0)


def savannah(x, y):
    h = 992 + 352 * smooth((70 - y) / 24.0)
    # west downs rise toward the desert; the south-west downs
    h += 220 * smooth((30 - x) / 14.0) * smooth((y - 60) / 8.0)
    # the east bank falls toward the river and Nystor's landing; the south-east climbs to the red hills
    h -= 120 * smooth((y - 80) / 20.0) * smooth(1 - abs(x - 84) / 10.0)
    # the red dwarf hills
    h += (bump(x, y, 107, 82, 6, 650) + bump(x, y, 112, 90, 8, 1100) + bump(x, y, 114, 98, 7, 1200)
          + bump(x, y, 111, 105, 7, 900) + bump(x, y, 104, 102, 5, 500) + bump(x, y, 98, 99, 4, 300)
          + bump(x, y, 101, 89, 4, 420) + bump(x, y, 118, 84, 8, 700))
    # the lava fields climb toward Mount Firestone; the shoulder under Falagar
    if x > 92 and y < 66:
        h += 520 * smooth((x - 94) / 10.0) * smooth((66 - y) / 10.0)
    # downs and knolls of the south fields and the west
    h += (bump(x, y, 28, 88, 6, 260) + bump(x, y, 24, 102, 6, 300) + bump(x, y, 46, 98, 5, 200)
          + bump(x, y, 66, 98, 6, 240) + bump(x, y, 74, 90, 4, 160) + bump(x, y, 50, 58, 5, 180)
          + bump(x, y, 32, 56, 5, 160) + bump(x, y, 94, 64, 4, 140))
    # the south edge west of x 64 (D-11.6: the way south there is the Asp road alone, to X3): low downs along y 106
    if x < 66 and not (32 <= x <= 40):
        h += 380 * smooth((y - 102) / 5.0) * smooth((66 - x) / 2.0)
    return h


def range_height(x, y):
    """The Gargoyle Range from its foot north to the rim: None south of the foot's blend."""
    fy = interp(FOOT_Y, x)
    cy = crest_y(x)
    if y > fy + 2:
        return None
    ch = interp(CREST, x)
    fh = savannah(x, fy) + 80
    if y >= cy:
        t = (fy + 2 - y) / (fy + 2 - cy)
        h = fh + (ch - fh) * (smooth(t) ** 0.85)
    else:
        h = ch - 70 * (cy - y)
    # crags on the slopes
    h += 160 * math.sin(x / 2.2 + y / 1.7) * math.sin(y / 2.9 - x / 4.1) * smooth((fy - y) / 3.0)
    return h


RIVER_LINE = [list(p) for p in L1.RIVER['line']]
TARN = [[77, 36], [84, 36], [84, 40], [77, 40]]
# F67 p4 (2026-11-25): the pool reaches the falls' foot (node row 41; from row 42 before, the sheet's foot stood on the
# cut land at 640 with the foot water lying on it)
POOL = [[78, 41], [84, 41], [84, 47], [78, 47]]


def raw_height(x, y):
    if y < RIM_Y - 0.6:
        return 0
    h = savannah(x, y) + roll(x, y)
    r = range_height(x, y)
    if r is not None:
        fy = interp(FOOT_Y, x)
        w = smooth((fy + 2 - y) / 2.5)
        h = h * (1 - w) + r * w
    # the falls: a tarn high in the range, the pool and gorge below it
    dt = math.hypot(max(TARN[0][0] - x, 0, x - TARN[1][0]), max(TARN[0][1] - y, 0, y - TARN[2][1]))
    if dt < 4 and y < 41.2:
        h = TARN_H + 64 + (h - TARN_H - 64) * smooth((dt - 0.5) / 3.5)
    # the river valley: banks at 704, the sides back to the land over four cells; the gorge below the falls
    d = dist_to_line(x, y, RIVER_LINE)
    if y >= 41.2 and d < 6.5:
        h = BANK + (h - BANK) * smooth((d - 2.0) / 4.5)
    dp = math.hypot(max(POOL[0][0] - x, 0, x - POOL[2][0]), max(POOL[0][1] - y, 0, y - POOL[3][1]))
    if y >= 41.2 and dp < 4:
        h = BANK + (h - BANK) * smooth((dp - 0.5) / 3.5)
    for poly, ph, blend in PADS:
        if K.inside((x, y), poly):
            h = ph
        else:
            e = K.edge_dist((x, y), poly)
            if e < blend:
                h = ph + (h - ph) * smooth(e / blend)
    return h


def grid_rows(step=4, unit=32):
    rows = []
    for j in range(128 // step):
        row = []
        for i in range(128 // step):
            x, y = step * i + step / 2, step * j + step / 2
            row.append(int(round(raw_height(x, y) / unit)))
        rows.append(row)
    return rows


def terraces():
    out = []
    for poly, h, _ in PADS:
        out.append({'polygon': [list(p) for p in poly], 'height': h, 'slope': 0})
    out[-2]['notes'] = 'The walled village, level before the castle gate.'
    out[-1]['notes'] = "Castle Burlock's rise (D-11.2: 1,900): a step of 576 over the village, the range behind."
    return out


def cliffs():
    return [
        {'line': [[0, RIM_Y], [64, RIM_Y], [128, RIM_Y]], 'drop': 2400, 'down': 'left',
         'notes': 'The world rim (drawn west to east, the low side north, on the left): the range ends in a cliff '
                  'above the stars.'},
        {'line': [[56, 50], [68, 50]], 'drop': CASTLE_H - VILLAGE_H, 'down': 'right',
         'notes': "The castle rise's south face over the village (the gate's ramp climbs it)."},
    ]


def heights():
    return {'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(),
                     'notes': 'Written by output/studio_cal/x4/tools/land.py from its height function.'},
            'terraces': terraces(), 'cliffs': cliffs()}


def water():
    return {
        'rivers': [{'id': 'water:river', 'line': [[round(a), round(b)] for a, b in RIVER_LINE[1:]], 'width_cells': 3, 'level': RIVER_LVL,
                    'notes': "The Great River's upper reach: from the falls pool south past the castle and the lists, "
                             "under the King's Bridge, past Nystor's landing, out at x 79 to X2."}],
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0,
             'polygon': [[0, 0], [128, 0], [128, RIM_Y - 1], [0, RIM_Y - 1]],
             'notes': 'Below the rim: stands for the stars.'},
            {'id': 'water:falls_pool', 'kind': 'pond', 'level': RIVER_LVL, 'polygon': [list(p) for p in POOL],
             'notes': 'The pool under the falls.'},
            {'id': 'water:tarn', 'kind': 'pond', 'level': TARN_H, 'polygon': [list(p) for p in TARN],
             'notes': 'The tarn in the range that spills over the falls.'},
        ],
    }


def roads():
    out = []
    for link, line, width, surface in L1.ROADS:
        if link == 'link:castle_lane':
            continue                     # the castle's ramp (a structure)
        line = [[round(a * 2) / 2, round(b * 2) / 2] for a, b in line]
        # the King's Bridge carries link:bridge_road over the river (a structure): the road's 4 water cells carry no
        # road tiles (a build warning; a crossing of its own would need a link of its own between two junctions)
        parts = [(line, False)]
        for ln, br in parts:
            e = {'link': link, 'line': ln, 'width': width, 'surface': surface if surface else 'dirt'}
            if br:
                e['bridge'] = True
            out.append(e)
    return out


def ground():
    g = [
        {'material': 'grass_meadow', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'the savannah: gold grass (the world meadow tint dries the crests)'},
        {'material': 'soil', 'polygon': [[0, RIM_Y], [100, RIM_Y], [100, 38], [76, 40], [58, 41], [40, 44],
                                         [18, 47], [0, 47]], 'notes': "the Gargoyle Range's slopes"},
        {'material': 'wasteland', 'polygon': [[98, RIM_Y], [128, RIM_Y], [128, 58], [112, 60], [104, 58],
                                                [99, 52], [96, 42]], 'notes': 'the lava fields'},
        {'material': 'soil', 'polygon': [[96, 80], [128, 80], [128, 128], [100, 128], [97, 104], [92, 95]],
         'notes': 'the red dwarf hills'},
        {'material': 'soil', 'polygon': [[0, 78], [33, 78], [32, 128], [0, 128]], 'notes': 'the dry west downs'},
        {'material': 'soil', 'polygon': [[57, 53], [68, 53], [68, 60], [63, 60], [63, 62], [61, 62], [61, 59],
                                         [57, 59]], 'notes': "Burlock's square and its lanes to the doors and the south gate"},
        {'material': 'soil', 'polygon': [[38, 82], [46, 82], [46, 88], [38, 88]], 'notes': "Asp's square"},
        {'material': 'soil', 'polygon': [[65, 63], [74, 63], [74, 72], [65, 72]], 'notes': 'the lists'},
        {'material': 'soil', 'polygon': [[25, 50], [31, 50], [31, 56], [25, 56]], 'notes': 'the barbarian camp'},
        {'material': 'soil', 'polygon': [[54, 101], [59, 101], [59, 105], [54, 105]], 'notes': "the knights' camp"},
        {'material': 'soil', 'polygon': [[104, 84], [108, 84], [108, 88], [104, 88]], 'notes': "the ogres' hollow"},
    ]
    return g
