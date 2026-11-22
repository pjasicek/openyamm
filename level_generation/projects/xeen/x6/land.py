"""X6 Desert of the Sphinx, L3/L4: the land (height grid, height points, terraces, cliffs, water, roads, ground).
A5, 2026-11-20, after D3's land.py.

Used by gen.py. Places and roads come from gen_l1.py (the approved L1 with D-31). Cells [x, y], x east, y south;
X = (x - 64) * 512, Y = (64 - y) * 512. Heights in map units above the stars below the rims (0). D-31: the height range
inside the box at least 2,500 (the oasis pond 1,000 to the Barbaric peak 3,700); the Basenji crag at the north rim
never moved nearer; rolling dry downs; no rim cliff or stars behind the Northern Sphinx in the arrival view (a red
ridge along the north rim east of the Basenji heights).
"""
import math

import gen_l1 as L1
import kit as K

RIM_X, RIM_Y = L1.RIM_X, L1.RIM_Y      # 24, 24: the world rim (west and north), the stars below
POND_LVL = 1000        # the oasis pond (L1: the map's lowest point and only water)
OASIS_H = 1088         # the oasis shore
PAN_H = 1248           # the pan and Sphinx Wells
WELLS_H = 1248
FORE_H = 1408          # the Northern Sphinx's forecourt
ARIE_H = 1472          # Arie's camp at the cliff foot
TERRACE_H = 2592       # Castle Basenji's gate terrace (A7: the sill on the terrace at about 2,600)
CRAG_H = 2752          # the crag's top behind the castle
PLATEAU_H = 2464       # the Basenji heights
YARD_H = 1504          # the Warzone coach yard (D-8.1)
SAUL_H = 1408
DRUID_H = 1440
SPHINX2_H = 1536       # the Southern Sphinx's dune
SHRINE_H = 1440
SERAI_H = 1504         # the ruined caravanserai
EAST_EDGE_H = 1152     # X4's west road (its level span 54-66 at 1,150)
SOUTH_EDGE_H = 1472    # X5's steppe road (its level span 45-56 at 1,460)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def peak(h, x, y, cx, cy, r, top):
    """Raise h toward `top` at (cx, cy), fading to nothing at r (never lowers)."""
    d = math.hypot(x - cx, y - cy)
    if d >= r or top <= h:
        return h
    return h + (top - h) * (1 - smooth(d / r))


def mesa(h, x, y, cx, cy, r, top, skirt=1.2):
    """A flat-topped mesa: level `top` inside r, steep sides over `skirt` cells (never lowers)."""
    d = math.hypot((x - cx) * 0.85, y - cy)
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


# ---------------------------------------------------------------- the Basenji escarpment
# the cliff top's line, west to east (L1's Basenji cliff): north of it the heights, south of it the desert
ESCARP = [[RIM_X, 42], [36, 38], [46, 38], [54, 37], [57, 33], [59, 31]]
ESCARP_H = [(24, 2400), (36, 2464), (46, 2464), (54, 2400), (57, 2240), (59, 2000)]
# the cliff path from Arie's camp up the escarpment to the castle's gate terrace (L1 link:cliff_path, one switchback)
CLIFF_PATH = [[47.6, 44.6], [50.5, 42.6], [53.4, 41.0], [50.4, 39.4], [46.8, 38.0], [42.6, 37.2], [39.6, 36.6]]
CLIFF_PATH_H = [(0.0, ARIE_H), (3.5, 1520), (6.8, 1700), (10.2, 2000), (14.0, 2300), (18.3, TERRACE_H),
                (21.4, TERRACE_H)]
CLIFF_GAP = (43.6, 55.2)    # the Basenji cliff is broken here (x), where the path climbs the slope

# ---------------------------------------------------------------- the mesas and the crack up the big one
MESAS = [(66, 34, 2.4, 2240), (70.5, 41.5, 1.8, 2048), (97, 74, 2.0, 1888)]
NEST_CRACK = [[72.4, 38.2], [70.0, 37.0], [67.6, 35.4]]          # a crack up the big mesa's east side
NEST_CRACK_H = [(0.0, 1536), (2.7, 1880), (5.6, 2240)]

# ---------------------------------------------------------------- the Barbaric Mountains and the prospector's notch
BARBARIC = [(98, 98, 7.5, 3712), (104, 92, 6.0, 3296), (94, 106, 5.5, 3200), (106, 104, 7.0, 3488),
            (113, 112, 9.0, 3300), (110, 96, 6.0, 3000), (101, 112, 6.0, 2900), (92, 95, 3.0, 2560),
            (91, 91, 3.0, 2300), (92, 100, 3.0, 2500)]
PROSPECTOR = (99.4, 101.6)
PROSPECTOR_H = 2688
PROSPECT_PATH = [[86.0, 104.0], [90.5, 104.6], [94.4, 103.0], [97.4, 102.8], [99.4, 101.6]]
PROSPECT_PATH_H = [(0.0, 1536), (4.5, 1820), (8.7, 2200), (11.7, 2470), (14.0, PROSPECTOR_H)]
YARD_CLIFF_X = 89.0          # the cliff at the yard's back (east), the arena gate cut in it
# the yard's rock shoulders north and south (D-8.1: a pocket in the Barbaric cliffs), and the west shoulders either
# side of the short wall with the desert gate (x 83, y 94-98)
YARD_ROCKS = [(86, 89.6, 3.2, 2112), (86, 100.4, 3.2, 2016), (82.0, 91.8, 2.6, 2112), (82.0, 99.6, 2.6, 2048),
              (90.5, 90.0, 2.5, 2400), (90.5, 100.0, 2.5, 2300)]
# the sand-fall cove cut into the west rim before the dune crest (D-31's signature view from [38, 96])
COVE = [[RIM_X, 84], [33, 84], [33, 92], [RIM_X, 92]]
CREST = (38, 96)
CREST_H = 2304

# ---------------------------------------------------------------- the north ridge behind the Sphinx, the Gargoyle foothills
NORTH_RIDGE = [(64, 27, 5.5, 2000), (72, 27.5, 5.0, 2150), (80, 27, 5.5, 2050), (88, 27.5, 5.0, 2200),
               (95, 28, 5.0, 2300)]
GARGOYLE = [(104, 32, 7.0, 2624), (112, 36, 9.0, 3008), (120, 44, 9.0, 2900), (110, 46, 6.0, 2400),
            (124, 30, 8.0, 2800)]

# ---------------------------------------------------------------- level places: (polygon, height, blend cells)
PADS = [
    (L1.TOWNS['town:sphinx_wells'], WELLS_H, 3),
    (L1.TOWNS['zone:coach_yard'], YARD_H, 0),
    (L1.TOWNS['zone:arie_camp'], ARIE_H, 2),
    ([[32.6, 33.6], [44.4, 33.6], [44.4, 37.4], [32.6, 37.4]], TERRACE_H, 0),     # the gate terrace
    ([[78, 33], [87, 33], [87, 46.6], [78, 46.6]], FORE_H, 3),                       # the Sphinx's forecourt
    ([[28, 68], [33, 68], [33, 73], [28, 73]], SAUL_H, 2.5),
    ([[68, 87], [73, 87], [73, 92], [68, 92]], DRUID_H, 2.5),
    ([[76, 74], [80.5, 74], [80.5, 78.5], [76, 78.5]], SERAI_H, 2.5),              # the caravanserai
    ([[26.5, 52.5], [29.5, 52.5], [29.5, 55.5], [26.5, 55.5]], SHRINE_H, 2),
    ([[34, 81], [40.5, 81], [40.5, 87.5], [34, 87.5]], SPHINX2_H, 2.5),              # the Southern Sphinx
]
OASIS_C = (41.2, 62.6)
POND = [list(p) for p in L1.OASIS_POND['polygon']]

# calm places: the dune ripple and the downs' roll fade out near them (cx, cy, r)
CALM = [(61.5, 61, 9), (41, 62.5, 6), (82, 41, 7), (45.5, 45.5, 4), (30.5, 70.5, 4), (70.5, 89.5, 4),
        (78, 76, 4), (35, 84.5, 5), (51, 92, 3), (69, 103, 3), (96, 57, 3), (75, 51, 3), (28, 54, 3),
        (86, 95, 5), (107, 60, 4), (50, 107, 4)]


def calm_weight(x, y):
    w = 1.0
    for (cx, cy, r) in CALM:
        w = min(w, smooth((math.hypot(x - cx, y - cy) - r) / 3.0))
    return w


def cliff_top_y(x):
    """The escarpment's top edge at column x (y south of it falls to the desert)."""
    return interp([(a[0], a[1]) for a in ESCARP], x)


def dunes(x, y):
    """Dune ridges running north-west to south-east, sharp crests and long windward slopes."""
    u = (x * 0.62 + y * 0.78) / 2.6
    v = (x * 0.78 - y * 0.62) / 7.0
    crest = 0.5 + 0.5 * math.sin(u + 0.8 * math.sin(v))
    crest = crest ** 1.6
    return crest + 0.25 * math.sin(x / 3.1 + 1.2) * math.sin(y / 2.7 + 0.4)


def downs(x, y):
    return (0.55 * math.sin(x / 3.4 + 0.3) * math.sin(y / 2.9 + 1.1) + 0.3 * math.sin((x + 1.4 * y) / 4.6)
            + 0.15 * math.sin((x - y) / 1.9))


def base(x, y):
    w = calm_weight(x, y)
    # the desert floor: 1,380 in the middle, falling east to the X4 road (1,150) and rising south to the steppe
    h = 1380.0
    h -= 120 * smooth((x - 96) / 30.0) * smooth(1 - abs(y - 60) / 14.0)
    h += 60 * smooth((y - 86) / 20.0)
    # the pan along the caravan road: hard sand at 1,250
    d_road, _ = along(x, y, L1.ROADS[0][1])
    pan = 1 - smooth((d_road - 3.0) / 6.0)
    h = h * (1 - pan) + PAN_H * pan
    # the north-east dunes round the Sphinx and the mesas (1,300-1,700)
    ne = smooth((52 - y) / 5.0) * smooth((x - 58) / 3.0) * smooth((101 - x) / 4.0) * smooth((y - 26) / 3.0)
    h += ne * w * (60 + 300 * dunes(x, y))
    # the western rim dunes (1,350-1,750), highest toward the rim; the dune crest of the signature view at (38, 96)
    wd = smooth((x - 22) / 2.0) * smooth((57 - x) / 6.0) * smooth((y - 68) / 4.0) * smooth((112 - y) / 4.0)
    h += wd * w * (60 + 240 * dunes(x + 3, y)) + wd * 220 * smooth((x - 27) / 13.0) - wd * 120 * smooth((31 - x) / 6.0)
    h = peak(h, x, y, CREST[0], CREST[1], 5.5, CREST_H)
    # the bone fields and ruin fields: cracked, slightly broken ground
    h += 40 * w * math.sin(x / 1.7 + y / 2.3) * smooth((y - 66) / 4.0) * smooth((92 - y) / 4.0) \
        * smooth((x - 56) / 4.0) * smooth((90 - x) / 4.0)
    # the dry downs toward X4 (rolling, 1,450-1,900)
    dn = smooth((x - 86) / 4.0) * smooth((y - 65) / 3.0) * smooth((90 - y) / 4.0)
    h += dn * (140 + 300 * w * downs(x, y)) + dn * 160 * smooth((x - 100) / 20.0)
    # the south steppe: low swells (1,400-1,500)
    st = smooth((y - 88) / 4.0) * smooth((90 - x) / 4.0) * smooth((x - 44) / 4.0)
    h += st * w * 50 * math.sin(x / 2.6 + 0.7) * math.sin(y / 3.3)
    # the stony rises in the south-west corner (beyond the box)
    h = peak(h, x, y, 34, 116, 9.0, 2200)
    # the Basenji heights: the escarpment along ESCARP; the plateau north of it
    if x < 61:
        top = interp(ESCARP_H, x)
        cy = cliff_top_y(x)
        t = smooth((cy - y + 1.0) / 1.6)            # 1 on the plateau, 0 at the cliff foot (1.6 cells of fall)
        plateau = top + 70 * math.sin(x / 2.3) * math.sin(y / 1.9) * smooth((cy - y - 1.0) / 2.0)
        h = h * (1 - t) + plateau * t
    for cx, cy, r, top in [(38, 30, 4.5, CRAG_H), (30, 34, 3.0, 2496), (50, 29, 4.0, 2528), (26, 26, 2.5, 2368),
                           (52, 31, 2.5, 2336)]:
        h = peak(h, x, y, cx, cy, r, top)
    # the north ridge behind the Sphinx and the Gargoyle foothills (no rim and no stars behind the Sphinx)
    for cx, cy, r, top in NORTH_RIDGE + GARGOYLE:
        h = peak(h, x, y, cx, cy, r, top)
    # the mesas (flat tops, steep red sides)
    for cx, cy, r, top in MESAS:
        h = mesa(h, x, y, cx, cy, r, top)
    # the Barbaric Mountains (to 3,700 inside the box)
    for cx, cy, r, top in BARBARIC + YARD_ROCKS:
        h = peak(h, x, y, cx, cy, r, top)
    h += 150 * math.sin(x / 1.6 + y / 1.3) * math.sin(y / 2.2 - x / 3.1) * smooth((h - 2300) / 700.0)
    # the obelisk's red rock knoll and the sun stones' rise
    h = peak(h, x, y, 75, 51, 2.6, 1632)
    h = peak(h, x, y, 69, 103, 3.0, 1536)
    return h


def in_cove(x, y):
    return RIM_X - 0.2 <= x < COVE[1][0] + 0.1 and COVE[0][1] - 0.1 < y < COVE[2][1] + 0.1


def raw_height(x, y):
    if x < RIM_X - 0.2 or y < RIM_Y - 0.2 or in_cove(x, y):
        return 0
    h = base(x, y)
    # the roads' beds: the X4 road from its edge (1,150) up to the pan; the X5 road from its edge (1,470)
    d, s = along(x, y, [[128, 60], [104, 60], [96, 60.5]])
    if d < 4.0:
        target = EAST_EDGE_H + (PAN_H - EAST_EDGE_H) * smooth((128 - x) / 28.0)
        wgt = 1 - smooth((d - 1.2) / 2.8)
        h = h * (1 - wgt) + target * wgt
    d, s = along(x, y, [[50, 128], [50, 100]])
    if d < 4.0:
        target = SOUTH_EDGE_H - 40 * smooth((128 - y) / 28.0)
        wgt = 1 - smooth((d - 1.2) / 2.8)
        h = h * (1 - wgt) + target * wgt
    # paths cut up the slopes: the cliff path, the crack up the mesa, the prospector's notch
    for line, prof, half, blend in ((CLIFF_PATH, CLIFF_PATH_H, 0.9, 1.4), (NEST_CRACK, NEST_CRACK_H, 0.7, 1.2),
                                    (PROSPECT_PATH, PROSPECT_PATH_H, 0.9, 1.6)):
        dd, ss = along(x, y, line)
        if dd < half + blend:
            target = interp(prof, ss)
            wgt = 1 - smooth((dd - half) / blend)
            h = h * (1 - wgt) + target * wgt
    if math.hypot(x - PROSPECTOR[0], y - PROSPECTOR[1]) < 2.2:
        h = h + (PROSPECTOR_H - h) * (1 - smooth((math.hypot(x - PROSPECTOR[0], y - PROSPECTOR[1]) - 1.0) / 1.2))
    # the oasis: a hollow round the pond
    d = math.hypot(x - OASIS_C[0], y - OASIS_C[1])
    if d < 7:
        h = OASIS_H + (h - OASIS_H) * smooth((d - 3.2) / 3.8)
    if K.inside((x, y), POND):
        return POND_LVL - 64
    e = K.edge_dist((x, y), POND)
    if e < 1.5 and d < 5:
        h = POND_LVL + 40 + (h - POND_LVL - 40) * smooth(e / 1.5)
    # the level places
    for poly, ph, blend in PADS:
        if K.inside((x, y), poly):
            h = ph
        elif blend:
            e = K.edge_dist((x, y), poly)
            if e < blend:
                h = ph + (h - ph) * smooth(e / blend)
    # the yard's back: the cliff rises east of it
    if 90.5 < y < 98.5 and YARD_CLIFF_X <= x < YARD_CLIFF_X + 3.5:
        h = max(h, 2496 + 40 * (x - YARD_CLIFF_X))
    # the rims' lip: the land ends in a cliff well above the stars
    lip = min(x - RIM_X, y - RIM_Y)
    if COVE[0][1] - 2.5 < y < COVE[2][1] + 2.5 and x < COVE[1][0] + 2.5:
        lip = min(lip, max(COVE[0][1] - y, y - COVE[2][1], x - COVE[1][0]))
    if lip < 2.5:
        h = max(h, 1200 + 60 * lip)
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


# height points (each corrects the grid where it stands, fading over a grid step): peaks, pads, paths
POINTS = [
    ([38, 30], CRAG_H, "Castle Basenji's crag at the north rim (D-31: never moved nearer)"),
    ([38, 36], TERRACE_H, "the castle's gate terrace (A7: the sill at about 2,600)"),
    ([98, 98], 3712, "the Barbaric Mountains' highest peak inside the box (D-31: the range >= 2,500)"),
    ([104, 92], 3296, None), ([94, 106], 3200, None), ([106, 104], 3488, None),
    ([66, 34], 2240, 'a red mesa (the nest on its top)'), ([71, 41], 2048, 'a red mesa'),
    ([97, 74], 1888, 'the lone mesa in the dry downs'),
    ([75, 51], 1632, "the obelisk's red knoll"),
    ([41, 62], OASIS_H, 'the oasis shore (the pond 1,000)'),
    ([61, 61], WELLS_H, 'Sphinx Wells'),
    ([82, 40], FORE_H, "the Northern Sphinx's forecourt"),
    ([86, 95], YARD_H, 'the Warzone coach yard (D-8.1)'),
    ([45, 45], ARIE_H, "Arie's camp at the cliff foot"),
    ([107, 60], 1184, "the X4 arrival (X4's edge 1,150)"),
    ([50, 107], 1472, "the X5 arrival (X5's edge 1,460)"),
    ([38, 96], CREST_H, "the dune crest of the signature view (raised for the cove's falls)"),
    ([99, 102], PROSPECTOR_H, "the prospector's notch"),
    ([112, 36], 3008, 'the Gargoyle foothills (X4 goes on east)'),
    ([80, 27], 2048, "the red ridge behind the Sphinx (D-31: no rim or stars behind it)"),
] + [([90, y], 2528, None) for y in range(91, 99)] + [([91, y], 2560, None) for y in range(91, 99)] + [([x, 90], 2048, None) for x in (84, 86, 88)] + \
    [([x, 100], 1984, None) for x in (84, 86, 88)] + [([82, 92], 2080, None), ([82, 93], 1984, None), ([82, 99], 2016, None), ([82, 98], 1952, None)] + [([92, y], 2560, None) for y in (92, 94, 96, 98)]


def path_points():
    """Height points along the cliff path, the crack and the prospector's path: every cell they cross keeps the
    profile's height (the step-4 grid alone smooths a ramp cut into a steep slope away)."""
    out = []
    seen = set()
    for line, prof in ((CLIFF_PATH, CLIFF_PATH_H), (NEST_CRACK, NEST_CRACK_H), (PROSPECT_PATH, PROSPECT_PATH_H)):
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
            if c in seen:
                continue
            seen.add(c)
            out.append(([c[0], c[1]], q32(raw_height(c[0], c[1])), None))
    return out


def heights():
    pts = POINTS + [p for p in path_points() if p[0] not in [q[0] for q in POINTS]]
    return {
        'grid': {'step': 4, 'unit': 32, 'rows': grid_rows(),
                 'notes': 'Written by output/studio_cal/x6/tools/land.py from its height function.'},
        'points': [dict({'at': at, 'h': h}, **({'notes': n} if n else {})) for at, h, n in pts],
        'rough': [{'polygon': [[88, 86], [128, 86], [128, 128], [86, 128], [86, 100]], 'amount': 1.6,
                   'notes': 'The Barbaric Mountains: broken red-brown peaks'},
                  {'polygon': [[RIM_X, RIM_Y], [58, RIM_Y], [58, 33], [46, 37], [36, 37], [RIM_X, 41]],
                   'amount': 0.5, 'notes': 'the Basenji heights: weathered rock'},
                  {'polygon': [[100, RIM_Y], [128, RIM_Y], [128, 54], [100, 50]], 'amount': 1.2,
                   'notes': 'the Gargoyle foothills'}],
        'terraces': terraces(),
        'cliffs': cliffs(),
    }


def terraces():
    out = []
    for poly, h, _ in PADS:
        out.append({'polygon': [list(p) for p in poly], 'height': h, 'slope': 0})
    out[0]['notes'] = 'Sphinx Wells on the pan.'
    out[1]['notes'] = 'The Warzone coach yard (D-8.1), its floor level with the arena gate.'
    out[3]['notes'] = "Castle Basenji's gate terrace on the crag (A7: XD-14's sill)."
    return out


def cliffs():
    return [
        {'line': [[RIM_X, RIM_Y], [RIM_X, 42], [RIM_X, 70], [RIM_X, 84]], 'drop': 1400, 'down': 'right',
         'notes': 'The west rim north of the cove (drawn north to south, the low side west): a cliff above the stars.'},
        {'line': [[RIM_X, 84], [33, 84], [33, 92], [RIM_X, 92]], 'drop': 1300, 'down': 'right',
         'notes': "The sand-fall cove cut into the rim before the dune crest (D-31's signature view): its north, east "
                  'and south walls, the void inside.'},
        {'line': [[RIM_X, 92], [RIM_X, 110], [RIM_X, 128]], 'drop': 1400, 'down': 'right',
         'notes': 'The west rim south of the cove.'},
        {'line': [[128, RIM_Y], [60, RIM_Y], [RIM_X, RIM_Y]], 'drop': 1500, 'down': 'right',
         'notes': "The north rim at y 24 (as X4's), drawn east to west, the low side north."},
        {'line': [[RIM_X, 42], [36, 38], [44, 38]], 'drop': 900, 'down': 'right',
         'notes': "Basenji's cliff, west of the cliff path (drawn west to east, the low side south)."},
        {'line': [[55, 36], [57, 33], [59, 31]], 'drop': 700, 'down': 'right',
         'notes': "Basenji's cliff, east of the cliff path."},
        {'line': [[83, 92], [89, 92]], 'drop': 560, 'down': 'right',
         'notes': "The coach yard's north shoulder (D-8.1), the low side the yard."},
        {'line': [[89, 92], [89, 98]], 'drop': 960, 'down': 'right',
         'notes': "The Barbaric cliff at the yard's back: the arena gate's portal is sunk in it."},
        {'line': [[89, 98], [83, 98]], 'drop': 560, 'down': 'right',
         'notes': "The coach yard's south shoulder, the low side the yard."},
    ]


def water():
    return {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': L1.RIM_SEA['polygon'],
             'notes': 'Below the rims: stands for the stars.'},
            {'id': 'water:cove', 'kind': 'sea', 'level': 0, 'polygon': [list(p) for p in COVE],
             'notes': 'The cove in the west rim: below it, the stars.'},
            {'id': 'water:oasis_pond', 'kind': 'pond', 'level': POND_LVL, 'polygon': POND,
             'notes': 'The oasis pond: clear water under palms; the only water on X6.'},
        ],
    }


# the oasis track and the shrine path go round the pond's south and north shores (L1's lines crossed the water)
TRACKS = {
    'link:oasis_track': [[55.5, 61.5], [50, 62], [46.5, 63], [45, 65.5], [42, 66.5], [38, 66.5], [35, 68],
                         [33, 69], [31.5, 70.5]],
    'link:shrine_path': [[46.5, 60], [44, 58.5], [40, 58], [36, 57.5], [32, 56], [29, 55]],
}


# Sphinx Wells' street (town_feel: doors by a road or lane): the caravan road itself runs through the hamlet
def roads():
    out = []
    for link, line, width, surface in L1.ROADS:
        line = [[round(a * 2) / 2, round(b * 2) / 2] for a, b in line]
        if link == 'link:cliff_path':
            line = [[round(a * 2) / 2, round(b * 2) / 2] for a, b in CLIFF_PATH]
        if link in TRACKS:
            line = TRACKS[link]
        out.append({'link': link, 'line': line, 'width': width, 'surface': surface or 'dirt'})
    out.append({'link': 'link:prospector_path', 'line': [[round(a * 2) / 2, round(b * 2) / 2] for a, b in
                                                          PROSPECT_PATH], 'width': 'lane', 'surface': 'dirt'})
    return out


def ground():
    """Three kinds (the world's limit): sand (the world's desert tile: the dunes, the pan, the steppe, the downs),
    wasteland (cracked ground: the bone fields and a crust round the ruins), dirt (bare red-brown rock: the Basenji
    heights and their escarpment, the mesas, the Barbaric Mountains, the Gargoyle foothills; the yards)."""
    out = [
        {'material': 'sand', 'polygon': [[0, 0], [128, 0], [128, 128], [0, 128]],
         'notes': 'desert sand everywhere first: dunes, pan, steppe and downs'},
        {'material': 'wasteland', 'polygon': [[57, 75], [70, 72], [84, 72], [86, 80], [80, 84], [66, 86], [58, 84]],
         'notes': 'the bone fields and the ruin fields: cracked crust'},
        {'material': 'dirt', 'polygon': [[RIM_X, RIM_Y], [61, RIM_Y], [61, 31], [57, 37], [50, 40], [46, 41],
                                         [36, 41], [RIM_X, 45]],
         'notes': 'the Basenji heights and their escarpment: bare red-brown rock'},
        {'material': 'dirt', 'polygon': [[88, 87], [128, 84], [128, 128], [86, 128], [86, 104], [88, 99], [88, 90]],
         'notes': 'the Barbaric Mountains: bare rock'},
        {'material': 'dirt', 'polygon': [[61, RIM_Y], [128, RIM_Y], [128, 54], [110, 52], [100, 46], [100, 31],
                                         [76, 31], [61, 31]],
         'notes': 'the red ridge along the north rim and the Gargoyle foothills: bare rock'},
        {'material': 'dirt', 'polygon': [[80, 88], [93, 88], [93, 102], [80, 102]],
         'notes': "the coach yard and its rock shoulders: bare rock"},
    ]
    for cx, cy, r, top in MESAS:
        x0, y0 = int(cx - r - 2), int(cy - r - 1)
        w, d = int(2 * r) + 4, int(2 * r) + 2
        out.append({'material': 'dirt', 'polygon': [[x0, y0], [x0 + w, y0], [x0 + w, y0 + d], [x0, y0 + d]],
                    'notes': 'a red mesa: bare rock'})
    return out
