"""X7 Mount Firestone, L3/L4: the land (height grid, height points, terraces, cliffs, water, roads, ground).
A5, 2026-11-20, after X6's land.py.

Used by gen.py. Places and roads come from gen_l1.py (the approved L1 with D-40). Cells [x, y], x east, y south;
X = (x - 64) * 512, Y = (64 - y) * 512. Heights in map units above the stars below the rims (0).

The south slopes (1,650 at X1's edge to 2,200 under the range) rise to the Red Dwarf Range: bare peaks to 3,200, the
Firestone Gap a saddle at 2,300 seen from the X1 road (D-40 change 7). North of it the ash flats (2,000-2,250) and the
lava basin (1,600-1,800 round the lava lake at 1,500) under Mount Firestone, a cone to 4,900 with its crater pool at
4,600. The north rim (y 24) and the east rim (x 104) are cliffs over the stars; the lava cove (x 68-79) bites five
cells into the north rim, its south wall the lip of the three lava falls (D-40 change 7, the signature from [67, 25]).
Lava is the world's lava tile set (`tile_set: lavtyl`, D-40 change 3), never water.
"""
import math

import gen_l1 as L1
import kit as K

RIM_X, RIM_Y = L1.RIM_X, L1.RIM_Y      # 104, 24: the world rim (east and north), the stars below
LAVA = 'lavtyl'        # D-40 change 3: the lake, the crater and the rivers (A1's lava tile set)
LAKE_LVL = 1500
CRATER_LVL = 4600
CONE = (88.0, 40.0)    # Mount Firestone's crater
GAP_H = 2300
WATCH_H = 2100
SABLE_H = 2050
OUTPOST_H = 2000
SHRINE_H = 2080
WELL_H = 1820
SPRING_H = 2150
GATE_H = 2000          # XD-05's back gate
MOUTH_H = 2250         # XD-16's mouth
CLEFT_H = 2500         # XD-17's cleft
CRAG_FOOT_H = 2150     # before XD-18's mouth
TOWER_H = 2600         # FD-04's crag top
CORNER_H = 2900        # the Fire corner
ISLAND_H = 1568
SOUTH_EDGE_H = 1856    # X1's north road at its edge
WEST_EDGE_H = 1312     # X4's east edge (its road 1,152)

# the lava cove (D-40 change 7): wider than L1's (x 70-76) so three falls stand 1,536 apart on its south wall
COVE = [[79, RIM_Y], [78, 29], [69, 29], [68, RIM_Y]]
COVE_LIP_Y = 29
LIP_H = 2350           # the falls' lip on the cove's south wall
RIM_SEA_POLY = [[0, 0], [128, 0], [128, 128], [RIM_X, 128], [RIM_X, RIM_Y]] + COVE + [[0, RIM_Y]]

LAKE = [list(p) for p in L1.LAVA_LAKE['polygon']]
ISLAND = [[37, 54], [37, 48], [39, 47], [39, 42], [36, 40], [32, 41], [30, 44], [32, 47], [34, 48], [34, 54]]
CRATER = [list(p) for p in L1.CRATER['polygon']]

# the lava river from the crater's west notch to the lake, and its north arm to the falls' lip (profiles: cells along
# the line, height)
RIVER = [[84, 40], [78, 37], [72, 38], [66, 40], [61, 43], [54, 45], [47, 46]]
RIVER_H = [(0.0, 4650), (6.7, 3500), (12.8, 2500), (19.1, 2150), (24.9, 1950), (32.2, 1750), (39.3, 1500)]
ARM = [[78, 37], [76, 33], [75, 31], [74, 30]]
ARM_H = [(0.0, 3500), (4.5, 2900), (6.7, 2500), (8.1, LIP_H)]

# roads and lanes with their profiles (the land is cut to them)
NORTH_ROAD = [[69, 128], [69, 107], [68, 100], [66, 94], [64, 88], [63, 82], [62, 76], [62, 70], [62, 66]]
NORTH_ROAD_H = [(0.0, SOUTH_EDGE_H), (21.0, 1860), (28.1, 1920), (34.4, 1960), (40.7, 2040), (46.8, WATCH_H),
                (52.9, 2180), (58.9, 2260), (62.9, GAP_H)]
FIRESTONE_ROAD = [[0, 66], [21, 66], [30, 66.5], [40, 67], [50, 67.5], [56, 67], [62, 66]]
FIRESTONE_ROAD_H = [(0.0, WEST_EDGE_H), (21.0, 1420), (30.0, 1560), (40.0, 1800), (50.0, 2000), (56.0, 2150),
                    (62.1, GAP_H)]
NORTH_TRACK = [[62, 66], [61.5, 60], [61, 52], [61, 47], [61, 44.6], [61, 41.4], [59.5, 39], [58, 35], [56.5, 31]]
NORTH_TRACK_H = [(0.0, GAP_H), (6.0, 2200), (14.0, 2060), (19.0, 2000), (21.4, 1990), (24.6, 1990), (27.4, 2040),
                 (31.7, 2120), (35.9, CRAG_FOOT_H)]
VOLCANO_PATH = [[61, 47], [63.5, 46], [65.4, 45]]
VOLCANO_PATH_H = [(0.0, 2000), (2.7, 2150), (4.8, MOUTH_H)]
CLEFT_PATH = [[64.2, 46.3], [67, 47.8], [70, 48.6], [72.4, 48.0]]
CLEFT_PATH_H = [(0.0, MOUTH_H), (2.8, 2330), (5.9, 2440), (8.5, CLEFT_H)]
LAKE_TRACK = [[61, 52], [54, 54], [46, 56], [40, 56.5], [35.5, 55], [35.5, 49]]
LAKE_TRACK_H = [(0.0, 2060), (7.3, 1900), (15.5, 1720), (21.5, 1680), (26.2, 1620), (32.2, ISLAND_H)]
TOWER_PATH = [[40, 56.5], [30, 57], [22, 52], [19.5, 45], [21, 38], [23, 35.6], [25.2, 34.2], [27.4, 33.4],
              [29, 33.2]]
TOWER_PATH_H = [(0.0, 1680), (10.0, 1700), (19.4, 1760), (26.8, 1800), (34.0, 1850), (37.1, 2100), (39.7, 2350),
                (42.0, TOWER_H), (43.6, TOWER_H)]
FIRESTONE_PATH = [[72.4, 48.6], [73, 51], [78, 53], [84, 54.6], [90, 54], [95, 50.5], [98.5, 44], [100, 37],
                  [101, 31], [101, 27.6]]
FIRESTONE_PATH_H = [(0.0, CLEFT_H), (2.5, 2540), (7.9, 2650), (14.1, 2750), (20.1, 2850), (26.2, 2950),
                    (33.6, 3000), (40.8, 2950), (46.8, CORNER_H), (50.2, CORNER_H)]
PROFILED = [(NORTH_ROAD, NORTH_ROAD_H, 1.2, 2.8), (FIRESTONE_ROAD, FIRESTONE_ROAD_H, 1.2, 2.8),
            (NORTH_TRACK, NORTH_TRACK_H, 0.9, 1.8), (VOLCANO_PATH, VOLCANO_PATH_H, 0.9, 1.4),
            (CLEFT_PATH, CLEFT_PATH_H, 0.8, 1.4), (LAKE_TRACK, LAKE_TRACK_H, 0.9, 1.6),
            (TOWER_PATH, TOWER_PATH_H, 0.9, 1.6), (FIRESTONE_PATH, FIRESTONE_PATH_H, 0.9, 1.6)]


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def peak(h, x, y, cx, cy, r, top):
    """Raise h toward `top` at (cx, cy), fading to nothing at r (never lowers)."""
    d = math.hypot(x - cx, y - cy)
    if d >= r or top <= h:
        return h
    return h + (top - h) * (1 - smooth(d / r))


def mesa(h, x, y, cx, cy, r, top, skirt=1.6):
    d = math.hypot(x - cx, y - cy)
    if d >= r + skirt or top <= h:
        return h
    if d <= r:
        return top
    return h + (top - h) * (1 - smooth((d - r) / skirt))


def dist_to_line(px, py, line):
    return min(K.seg_dist((px, py), a, b) for a, b in zip(line, line[1:]))


def along(px, py, line):
    """(distance to the line, cells along the line from its first point to the nearest)."""
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


def line_len(line):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(line, line[1:]))


# ---------------------------------------------------------------- the Red Dwarf Range (D-40: bare peaks, the Gap a
# saddle seen from the X1 road)
RIDGES = [  # (line, top, flat half-width, fall in cells)
    ([[6, 60], [22, 60], [38, 59.5], [52, 60]], 2950, 1.0, 3.0),     # the north wall over the Firestone road
    ([[4, 74], [20, 73], [38, 72], [54, 72.5]], 2700, 1.0, 3.0),     # the southern crest above the west slopes
    ([[71, 63.5], [80, 66], [92, 66], [102, 64]], 2900, 1.0, 3.2),   # the range east of the Gap
]
PEAKS = [  # (x, y, radius, top): the bare peaks along the ridges; the two either side of the Gap frame its saddle
    (36, 61, 3.2, 3050), (50, 61, 3.4, 3200), (56.5, 62.6, 2.8, 2950), (70.5, 63.2, 3.0, 3050),
    (78, 66, 3.4, 3100), (92, 65, 3.6, 3150), (100, 70, 3.2, 2850), (30, 73, 2.8, 2750), (46, 73, 2.8, 2850),
    (13, 60, 2.8, 2900), (24, 59.6, 2.6, 2950), (86, 66.5, 2.6, 2950),
]
# the south: Sablewing's red crag, the hill over the back gate, the south-east hills, the west hills, the den's knoll
SOUTH_HILLS = [(78.8, 90.0, 3.4, 2750), (89.6, 100.0, 3.0, 2650), (98, 104, 4.5, 2350), (20, 92, 5.0, 2150),
               (83.0, 105.8, 3.0, 2500), (102, 92, 4, 2400), (94, 78, 3, 2450), (38, 82, 3, 2200),
               (46, 112, 4, 2000), (24, 112, 5, 2050), (44, 71.6, 2.2, 2750)]
# the north: XD-18's crag at the rim, the black knob behind XD-16, the rock behind the cleft
NORTH_ROCKS = [(56.5, 27.0, 4.0, 3250), (68.0, 45.0, 3.0, 3250), (75.4, 48.0, 3.2, 3550), (46, 27, 3.0, 2050),
               (40, 30, 3.0, 1950), (20, 44, 3, 1850)]
TOWER_CRAG = (29.0, 30.0, 2.7)       # the mesa top (centre, radius) of FD-04's crag

# ---------------------------------------------------------------- level places: (polygon, height, blend cells)
PADS = [
    ([[59.6, 62.6], [65.4, 62.6], [65.4, 67.6], [59.6, 67.6]], GAP_H, 2.0),               # the Gap and the obelisk
    ([[64.0, 79.0], [71.0, 79.0], [71.0, 86.0], [64.0, 86.0]], WATCH_H, 2.5),             # the dwarves' watch
    ([[73.4, 88.6], [76.8, 88.6], [76.8, 91.6], [73.4, 91.6]], SABLE_H, 1.6),             # Sablewing's cave mouth
    ([[28.0, 83.4], [34.0, 83.4], [34.0, 89.0], [28.0, 89.0]], OUTPOST_H, 2.0),           # the orc outpost
    ([[50.8, 96.8], [53.6, 96.8], [53.6, 99.6], [50.8, 99.6]], SHRINE_H, 2.4),            # the Shrine of Fire's knoll
    ([[26.8, 100.8], [29.4, 100.8], [29.4, 103.4], [26.8, 103.4]], WELL_H, 2.0),          # the Well of Speed
    ([[92.6, 82.8], [95.4, 82.8], [95.4, 85.4], [92.6, 85.4]], SPRING_H, 2.0),            # the hot spring
    ([[85.0, 98.8], [87.5, 98.8], [87.5, 101.2], [85.0, 101.2]], GATE_H, 1.2),            # before XD-05's back gate
    ([[62.6, 43.6], [66.0, 43.6], [66.0, 46.6], [62.6, 46.6]], MOUTH_H, 1.6),             # before XD-16's mouth
    ([[54.6, 30.0], [58.4, 30.0], [58.4, 32.4], [54.6, 32.4]], CRAG_FOOT_H, 1.6),         # before XD-18's mouth
    ([[99.4, 25.6], [102.6, 25.6], [102.6, 28.6], [99.4, 28.6]], CORNER_H, 1.6),          # the Fire corner
    ([[41.4, 68.4], [46.6, 68.4], [46.6, 69.8], [41.4, 69.8]], 2050, 1.0),                # the miner's adit
    ([[38.6, 63.8], [41.6, 63.8], [41.6, 66.2], [38.6, 66.2]], 1800, 1.6),                # the cairn
]


def south_base(x, y):
    h = interp([(74, 2280), (80, 2180), (92, 2020), (104, 1920), (116, 1800), (128, 1660)], y)
    h += 300 * smooth((24 - x) / 20.0)                     # X4's red dwarf hills go on east as the west slopes
    h += 70 * math.sin(x / 3.7 + 0.4) * math.sin(y / 4.1 + 1.3) + 35 * math.sin((x + y) / 2.3)
    return h


def north_base(x, y):
    # the lava basin (west): 1,750 falling to the lake; the ash flats (east of x 50): 2,000-2,250
    basin = 1760 + 60 * math.sin(x / 3.1) * math.sin(y / 2.7)
    flats = 2050 + 180 * smooth((x - 58) / 16.0) + 50 * math.sin(x / 2.1 + 0.5) * math.sin(y / 2.6)
    t = smooth((x - 46) / 8.0)
    h = basin * (1 - t) + flats * t
    # the lake's hollow: the shore falls to 1,560-1,620
    e = K.edge_dist((x, y), LAKE)
    if not K.inside((x, y), LAKE) and e < 6:
        h = 1580 + (h - 1580) * smooth((e - 0.6) / 5.4)
    # the range's north foot rises a little toward it
    h += 220 * smooth((y - 54) / 6.0)
    return h


def cone(x, y):
    """Mount Firestone: a cone to 4,900, its rim round the crater, falling to the flats; the west notch lower."""
    r = math.hypot(x - CONE[0], y - CONE[1])
    h = interp([(0.0, CRATER_LVL - 64), (2.4, CRATER_LVL - 64), (3.0, 4800), (3.6, 4900), (6.0, 4300), (9.0, 3600),
                (12.0, 3050), (15.0, 2650), (19.0, 2300), (24.0, 2050)], r)
    if 2.0 < r < 6.0:
        ang = math.atan2(y - CONE[1], x - CONE[0])
        dw = abs((ang - math.pi + math.pi) % (2 * math.pi) - math.pi)   # angle from due west
        if dw < 0.6:
            h -= 260 * (1 - dw / 0.6) * (1 - smooth((r - 3.6) / 2.4))
    h += 120 * math.sin(x / 1.4 + y / 1.1) * math.sin(y / 1.9 - x / 2.7) * smooth((r - 4) / 3.0)
    return h


def base(x, y):
    w = smooth((y - 60) / 14.0)                   # 0 north of y 60, 1 south of y 74
    h = north_base(x, y) * (1 - w) + south_base(x, y) * w
    h = max(h, cone(x, y)) if math.hypot(x - CONE[0], y - CONE[1]) < 24 else h
    for line, top, half, fall in RIDGES:
        d = dist_to_line(x, y, line)
        if d < half + fall and top > h:
            h = h + (top - h) * (1 - smooth((d - half) / fall))
    for cx, cy, r, top in PEAKS + SOUTH_HILLS + NORTH_ROCKS:
        h = peak(h, x, y, cx, cy, r, top)
    h = mesa(h, x, y, TOWER_CRAG[0], TOWER_CRAG[1], TOWER_CRAG[2], TOWER_H)
    h = mesa(h, x, y, 56.5, 27.0, 2.0, 3050, skirt=2.2)     # XD-18's crag: rock all along the mouth's back
    # bare peaks: broken rock on the high ground
    h += 140 * math.sin(x / 1.6 + y / 1.3) * math.sin(y / 2.2 - x / 3.1) * smooth((h - 2450) / 600.0)
    return h


def in_void(x, y):
    return x > RIM_X + 0.2 or y < RIM_Y - 0.2 or K.inside((x, y), COVE)


def raw_height(x, y):
    if in_void(x, y):
        return 0
    h = base(x, y)
    # roads, tracks and paths cut to their profiles
    for line, prof, half, blend in PROFILED:
        dd, ss = along(x, y, line)
        if dd < half + blend:
            target = interp(prof, ss)
            wgt = 1 - smooth((dd - half) / blend)
            h = h * (1 - wgt) + target * wgt
    # the level places
    for poly, ph, blend in PADS:
        if K.inside((x, y), poly):
            h = ph
        elif blend:
            e = K.edge_dist((x, y), poly)
            if e < blend:
                h = ph + (h - ph) * smooth(e / blend)
    # the lava river's bed and its arm (the lava a little under the banks)
    for line, prof, half in ((RIVER, RIVER_H, 1.0), (ARM, ARM_H, 0.75)):
        dd, ss = along(x, y, line)
        if dd < half + 1.2:
            target = interp(prof, ss) - 48
            wgt = 1 - smooth((dd - half) / 1.2)
            h = h * (1 - wgt) + target * wgt
    # the lava lake, its island and causeway, the crater pool
    if K.inside((x, y), LAKE):
        return LAKE_LVL - 64
    if K.inside((x, y), ISLAND):
        return ISLAND_H + 24 * math.sin(x * 1.7) * math.sin(y * 1.3)
    e = K.edge_dist((x, y), LAKE)
    if e < 1.4:
        h = min(h, LAKE_LVL + 60 + (h - LAKE_LVL - 60) * smooth(e / 1.4))
    if K.inside((x, y), CRATER):
        return CRATER_LVL - 64
    # the rims' lip: the land ends in a cliff well above the stars
    lip = min(RIM_X - x, y - RIM_Y)
    if y < COVE_LIP_Y + 3 and 66 < x < 81:
        lip = min(lip, K.edge_dist((x, y), COVE))
    if lip < 2.5:
        h = max(h, 1300 + 60 * lip)
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


def q32(h):
    return int(round(h / 32.0)) * 32


POINTS = [
    ([69, 107], 1856, "the X1 arrival (X1's north road meets its edge at 1,856)"),
    ([21, 66], 1408, "the X4 arrival (X4's edge 1,312, its road 1,152)"),
    ([62, 66], GAP_H, 'the Firestone Gap: the saddle where both roads meet (D-40: seen from the X1 road)'),
    ([64, 63], GAP_H, "the obelisk on the Gap's north lip"),
    ([50, 61], 3200, 'the Red Dwarf Range: its highest bare peak'),
    ([56, 62], 2944, 'the peak west of the Gap'), ([70, 63], 3040, 'the peak east of the Gap'),
    ([92, 65], 3136, None), ([78, 66], 3104, None), ([36, 61], 3040, None),
    ([67, 82], WATCH_H, "the dwarves' watch"),
    ([75, 90], SABLE_H, "Sablewing's cave mouth under the red crag"),
    ([79, 89], 2592, "Sablewing's red crag"),
    ([31, 86], OUTPOST_H, 'the orc outpost'),
    ([52, 98], SHRINE_H, "the Shrine of Fire's knoll"),
    ([28, 102], WELL_H, 'the Well of Speed'),
    ([94, 84], SPRING_H, 'the hot spring'),
    ([87, 100], GATE_H, "before XD-05's back gate"),
    ([64, 45], MOUTH_H, "before XD-16's mouth"),
    ([72, 48], CLEFT_H, "before XD-17's cleft"),
    ([56, 31], CRAG_FOOT_H, "before XD-18's mouth"),
    ([56, 27], 3136, "XD-18's crag over the north rim"),
    ([29, 30], TOWER_H, "FD-04's crag top (the Dragon Tower)"),
    ([88, 36], 4896, 'Mount Firestone: the crater rim'), ([92, 40], 4896, None), ([88, 44], 4800, None),
    ([84, 40], 4640, "the crater's west notch, where the lava river leaves"),
    ([101, 26], CORNER_H, 'the Fire corner'),
    ([35, 44], ISLAND_H, "the Ever-Hot Lava Rock's island (a cooled flow)"),
    ([73, 30], LIP_H, "the lava falls' lip on the cove's south wall"),
    ([67, 25], 2304, "the lava cove's west lip (the signature camera)"),
]


def path_points():
    """Height points along every profiled path: every cell they cross keeps the profile's height."""
    out = []
    seen = set()
    for line, prof, _half, _blend in PROFILED:
        L = line_len(line)
        n = int(L * 2) + 1
        for k in range(n + 1):
            s = L * k / n
            run = 0.0
            for a, b in zip(line, line[1:]):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                if s <= run + seg or (a, b) == (line[-2], line[-1]):
                    t = 0 if seg == 0 else (s - run) / seg
                    px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    break
                run += seg
            c = (int(round(px)), int(round(py)))
            if c in seen or not (1 <= c[0] <= 127 and 1 <= c[1] <= 127) or in_void(*c):
                continue
            seen.add(c)
            out.append(([c[0], c[1]], q32(raw_height(c[0], c[1])), None))
    return out


def feature_points():
    """Height points on every node of the small features (peaks, crags, the rocks behind the cave mouths, the tower's
    crag): the step-4 grid alone smooths a feature of a few cells away."""
    out = []
    feats = [(cx, cy, r) for cx, cy, r, _top in PEAKS + SOUTH_HILLS + NORTH_ROCKS] + [
        (TOWER_CRAG[0], TOWER_CRAG[1], TOWER_CRAG[2] + 1.6)]
    seen = set()
    for cx, cy, r in feats:
        for x in range(int(cx - r), int(cx + r) + 2):
            for y in range(int(cy - r), int(cy + r) + 2):
                if (x, y) in seen or math.hypot(x - cx, y - cy) > r or not (1 <= x <= 127 and 1 <= y <= 127):
                    continue
                if in_void(x, y) or min(RIM_X - x, y - RIM_Y) < 1 or K.edge_dist((x, y), LAKE) < 1.5:
                    continue
                if K.inside((x, y), LAKE) or K.inside((x, y), ISLAND):
                    continue
                seen.add((x, y))
                out.append(([x, y], q32(raw_height(x, y)), None))
    return out


def heights():
    taken = [p[0] for p in POINTS]
    pts = POINTS + [p for p in path_points() if p[0] not in taken]
    taken = [p[0] for p in pts]
    pts += [p for p in feature_points() if p[0] not in taken]
    return {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(),
                 'notes': 'Written by output/studio_cal/x7/tools/land.py from its height function.'},
        'points': [dict({'at': at, 'h': h}, **({'notes': n} if n else {})) for at, h, n in pts],
        'rough': [{'polygon': [[0, 58], [104, 56], [104, 76], [84, 78], [70, 74], [58, 76], [44, 74], [24, 76],
                               [0, 74]], 'amount': 1.4,
                   'notes': 'The Red Dwarf Range: bare broken peaks (D-40 change 7)'},
                  {'polygon': [[76, RIM_Y], [RIM_X, RIM_Y], [RIM_X, 58], [88, 60], [78, 52], [78, 34]],
                   'amount': 0.8, 'notes': "Mount Firestone's flanks: cooled flows"}],
        'terraces': terraces(),
        'cliffs': cliffs(),
    }


def terraces():
    out = []
    for poly, h, _ in PADS:
        out.append({'polygon': [list(p) for p in poly], 'height': h, 'slope': 0})
    out[0]['notes'] = 'The Firestone Gap: the obelisk and the signpost.'
    out[1]['notes'] = "The dwarves' watch."
    return out


def cliffs():
    return [
        {'line': [[RIM_X, RIM_Y]] + COVE + [[0, RIM_Y]], 'drop': 1500, 'down': 'right',
         'notes': "The north rim at y 24 (as X4's), drawn east to west, the low side north; the lava cove bites five "
                  "cells into it (x 68-79), the three lava falls on its south wall pour north into the stars, their "
                  "faces toward the signature camera on the cove's west lip [67, 25] (D-40 change 7)."},
        {'line': [[RIM_X, RIM_Y], [RIM_X, 70], [RIM_X, 128]], 'drop': 1500, 'down': 'left',
         'notes': "The east rim at x 104 (as X1's), drawn north to south, the low side east."},
    ]


def water():
    return {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': [list(p) for p in RIM_SEA_POLY],
             'notes': 'Below the rims and in the lava cove: stands for the stars.'},
            {'id': 'water:lava_lake', 'kind': 'lake', 'level': LAKE_LVL, 'polygon': LAKE, 'tile_set': LAVA,
             'notes': "D1's lava lake under the north rim (D-40 change 3: the lava tile set, never water): the "
                      'cooled-flow island with the Ever-Hot Lava Rock, joined to the south shore by its causeway.'},
            {'id': 'water:crater', 'kind': 'pond', 'level': CRATER_LVL, 'polygon': CRATER, 'tile_set': LAVA,
             'notes': "Mount Firestone's crater: a lava pool under the rim."},
        ],
        'rivers': [
            {'id': 'water:lava_river', 'line': [list(p) for p in RIVER], 'width_cells': 2, 'tile_set': LAVA,
             'notes': 'The lava river from the crater\'s notch down the west flank to the lava lake; the black '
                      'bridge crosses it at [61, 43].'},
            {'id': 'water:lava_falls', 'line': [list(p) for p in ARM], 'width_cells': 2, 'tile_set': LAVA,
             'notes': "The river's north arm to the cove's south wall, where the three lava falls pour over."},
        ],
    }


LANES = {  # the L1 lanes that are cut by a profile here take its line
    'link:north_track': NORTH_TRACK, 'link:volcano_path': VOLCANO_PATH, 'link:cleft_path': CLEFT_PATH,
    'link:lake_track': LAKE_TRACK, 'link:tower_path': TOWER_PATH, 'link:firestone_path': FIRESTONE_PATH,
}


# Lanes whose dirt stops short of their profile's end (A5, twelfth session; A6's basalt): the tower path's climb up
# the Dragon Tower crag's south flank (from (21, 38), rows 32-35) lays no dirt, so the flank keeps the ash tile and
# its steep ground takes A6's black basalt instead of the red rock of dirt. The profile still cuts the whole climb.
PAINTED_POINTS = {'link:tower_path': 5}


def roads():
    out = []
    for link, line, width, surface in L1.ROADS:
        line = LANES.get(link, line)
        line = line[:PAINTED_POINTS.get(link, len(line))]
        line = [[round(a * 2) / 2, round(b * 2) / 2] for a, b in line]
        out.append({'link': link, 'line': line, 'width': width, 'surface': surface or 'dirt'})
    return out


def ground():
    """Two kinds beside the lava (the world's limit): dirt (red stony ground and bare rock: the south slopes, the
    range) and wasteland (grey ash and cooled flows: the north)."""
    return [
        {'material': 'dirt', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'red stony ground and bare rock first: the south slopes and the Red Dwarf Range'},
        {'material': 'wasteland', 'polygon': [[0, RIM_Y], [RIM_X, RIM_Y], [RIM_X, 57], [90, 59], [76, 55],
                                              [62, 58], [44, 57], [30, 58], [0, 58]],
         'notes': 'grey ash and cooled flows: the ash flats, the lava basin, Mount Firestone'},
    ]
