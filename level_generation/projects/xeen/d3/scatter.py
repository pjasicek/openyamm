"""D3 Sandcaster and the Aging Forest: trees, bushes, rocks and plants (A5, 2026-11-20, after X4's scatter.py).

The Aging Forest thick with red and gold crowns; the Howling Woods dark and old on its ridge; date palms by the city,
the Crossroads and the river; thorn scrub and rock on the dunes; scree on the Wrath crest; reeds and swamp trees in the
fen. Trees run on beyond the party's square to the map's edge (HANDOFF_LEAD 5: no stands "cut off" at the edge); the
rims (x 104, y 104) end the land.
"""
import kit as K
import land as LD

AUTUMN = {'7tree14': 3, '7tree17': 3, '7tree20': 2, '7tree08': 2, 'tree26': 1}   # MM7's autumn twins (red, gold)
HOWL = {'tree29': 3, 'tree30': 2, '7tree22': 2, '6tree09': 1, 'tree42': 1}   # dark pines and old broad trees
PALM = {'tree01': 2, 'tree02': 2, 'tree03': 1, 'tree05': 1, 'tree07': 1}
SCRUB = {'tree29': 1, '7tree22': 1, 'tree42': 1}
MEADOW = {'7tree19': 3, '7tree28': 2, 'tree02': 1}
FEN = {'swptree1': 3, 'swptree2': 2, 'swptree3': 2, 'tree41': 1}
CREST = {'7tree22': 2, 'tree29': 2, 'tree30': 1}


def scatter():
    out = []

    def e(sid, poly, count, deco=None, kinds=None, spacing=None, clusters=None, steep=False, group=None, line=None):
        d = {'id': sid, 'count': max(1, int(count))}
        if deco:
            d['decoration'] = deco
        if kinds:
            d['kinds'] = dict(kinds)
        if poly:
            d['polygon'] = poly
        if line:
            d['line'] = line
        if spacing:
            d['spacing'] = spacing
        if clusters:
            d['clusters'] = max(1, int(clusters))
        if steep:
            d['steep'] = True
        if group:
            d['spacing_group'] = group
        out.append(d)

    def trees(sid, poly, per_100, kinds, spacing=1.8, clusters=None, steep=False):
        e(sid, poly, per_100 * K.poly_area(poly) / 100.0, kinds=kinds, spacing=spacing, clusters=clusters,
          group='trees', steep=steep)

    # ---- the Aging Forest: old broad trees in red and gold, dense (pieces round the glade and the oak)
    AF_N = [[38, 50], [50, 48], [54, 52], [60, 56], [62, 64], [56, 64], [50, 62], [44, 66], [38, 66]]
    AF_S = [[38, 76], [44, 76], [50, 74], [56, 70], [63, 70], [64, 74], [62, 86], [60, 103.4], [33, 103.4], [34, 92],
            [36, 80]]
    AF_W = [[36, 54], [38, 50], [38, 76], [36, 80], [36, 68]]
    AF_MID = [[44, 66], [50, 62], [56, 64], [62, 64], [63, 70], [56, 70], [50, 74], [44, 76]]
    trees('scatter:aging_n', AF_N, 15, AUTUMN, 1.25, 14)
    trees('scatter:aging_s', AF_S, 15, AUTUMN, 1.25, 20)
    trees('scatter:aging_w', AF_W, 14, AUTUMN, 1.3)
    trees('scatter:aging_mid', AF_MID, 14, AUTUMN, 1.6)
    for sid, poly in (('n', AF_N), ('s', AF_S)):
        a = K.poly_area(poly)
        e('scatter:leaves_' + sid, poly, a * 0.12, deco='flower05', clusters=a * 0.03)
        e('scatter:forest_bush_' + sid, poly, a * 0.06, deco='bush02', clusters=a * 0.015)
        e('scatter:forest_mush_' + sid, poly, a * 0.02, deco='mushrm05', clusters=a * 0.006)
    # ---- the Howling Woods on its ridge: dark old trees
    HW = [[19, 52], [30, 50], [36, 54], [36, 68], [36, 80], [34, 92], [33, 103.4], [19, 103.4]]
    trees('scatter:howling', HW, 22, HOWL, 1.15, 26, steep=True)
    a = K.poly_area(HW)
    e('scatter:howling_rocks', HW, a * 0.03, deco='7rock09', clusters=a * 0.01, steep=True)
    e('scatter:howling_bush', HW, a * 0.05, deco='bush03', clusters=a * 0.012)
    # ---- the caravan valley and the desert edge: thorn scrub, rocks, a few hardy trees; palms by the wells
    VAL = [[19, 33], [27, 33], [27, 40], [33, 45.5], [44, 45.5], [50, 46], [44, 49.5], [30, 50], [19, 52]]
    trees('scatter:valley', VAL, 1.6, SCRUB, 2.4)
    DES = [[47, 19], [80, 19], [80, 24], [77, 34], [72, 39], [65, 37.5], [56, 37], [52, 37.5], [47, 39]]
    trees('scatter:dunes', DES, 1.2, SCRUB, 2.6)
    for sid, poly in (('valley', VAL), ('dunes', DES)):
        a = K.poly_area(poly)
        e('scatter:scrub_' + sid, poly, a * 0.07, deco='bush03', clusters=a * 0.02)
        e('scatter:rocks_' + sid, poly, a * 0.035, deco='7rock09', clusters=a * 0.01, steep=True)
        e('scatter:plants_' + sid, poly, a * 0.03, deco='plant02', clusters=a * 0.01)
    e('scatter:well_palms', None, 4, kinds=PALM, line=[[62.3, 27.4], [64.8, 27.6], [64.6, 29.8]])
    # date palms round the city's walls (town_feel: trees in the ring round the town)
    for sid, poly in (('w', [[21, 19], [26.4, 19], [26.4, 39], [21, 41]]), ('e', [[47.6, 19], [53, 19], [53, 36],
                                                                                 [47.6, 38.4]]),
                      ('s', [[27, 39.6], [33, 39.6], [33, 45.5], [27, 46]])):
        trees('scatter:town_palms_' + sid, poly, 9, PALM, 1.6)
    # ---- the Crossroads plain: palms along the roads, a little scrub
    XP = [[47, 39], [52, 37.5], [56, 37], [65, 37.5], [72, 40], [73, 44], [62.5, 44.5], [62.5, 50.5], [70, 52],
          [66, 56], [60, 56], [54, 52], [50, 48], [50, 45.5]]       # Celia and Derek's yard left out (its door)
    trees('scatter:cross_plain', XP, 2.2, PALM | {'7tree19': 1}, 2.2)
    a = K.poly_area(XP)
    e('scatter:cross_scrub', XP, a * 0.04, deco='bush02', clusters=a * 0.012)
    # ---- the Wrath hills: hardy trees on the shoulders, scree and rock on the crest
    WH = [[80, 19], [104, 19], [104, 54], [92, 56], [88, 50], [84, 44], [80, 40], [79, 36], [82, 26], [82, 19]]
    trees('scatter:wrath_hills', WH, 2.6, CREST, 2.0, 10, steep=True)
    a = K.poly_area(WH)
    e('scatter:crest_rocks', WH, a * 0.06, deco='7rock08', clusters=a * 0.02, steep=True)
    e('scatter:crest_rocks', WH, a * 0.04, deco='rock09', clusters=a * 0.012, steep=True)
    # eighth session (the lane review): big rocks along the crest's ridge line and on the gorge's rims
    CRAG = {'rock65': 3, 'rock68': 2, '7rock08': 2, 'rock12': 1}
    west, east = LD.gorge_walls()
    spots = ([(p, 1.4, 4) for p in LD.RIDGE_LINE] + [((x - 0.8, y), 0.8, 2) for x, y in west]
             + [((x + 0.8, y), 0.8, 2) for x, y in east[1:]])
    for k, (p, r, n) in enumerate(spots):
        out.append({'id': 'scatter:crag_rocks', 'count': n, 'kinds': dict(CRAG), 'steep': True,
                    'circle': {'at': [round(p[0], 2), round(p[1], 2)], 'r': r}})
    # scrub on the crest's grass between the rock (ninth pass)
    CR = [[89, 20], [103, 20], [103, 40], [90, 40], [89, 30]]
    e('scatter:crest_scrub', CR, 70, deco='bush03', clusters=18, steep=True)
    # the gorge's lips: rocks
    e('scatter:gorge_rocks', [[74, 20], [84, 20], [82, 36], [74, 36]], 30, deco='7rock08', clusters=10, steep=True)
    WB = [[66, 19], [79, 19], [78, 34], [70, 34], [66, 28]]
    trees('scatter:west_bank', WB, 2.0, CREST, 2.2, 6, steep=True)
    # ---- the river meadows: palms and broad trees on the banks, reeds
    RM = [[70, 52], [73, 44], [77, 36], [80, 40], [84, 44], [88, 50], [92, 56], [103.4, 54], [103.4, 72], [90, 72],
          [80, 70], [72, 66], [66, 56]]
    # the signature view (D-28) down the river to the falls: no trees on the banks east of x 80 between y 57 and 67
    trees('scatter:meadows', [[70, 52], [73, 44], [77, 36], [80, 40], [84, 44], [88, 50], [92, 56], [103.4, 54],
                              [103.4, 57], [80, 57], [80, 67], [103.4, 67], [103.4, 72], [90, 72], [80, 70], [72, 66],
                              [66, 56]], 3.0, MEADOW | PALM, 2.0, 12)
    a = K.poly_area(RM)
    e('scatter:meadow_flowers', RM, a * 0.05, deco='flower04', clusters=a * 0.015)
    e('scatter:bank_reeds', [[72, 44], [82, 56], [100, 62], [100, 66], [82, 60], [72, 48]], 60, deco='plant02',
      clusters=18)
    # ---- Venom Pond and the fen
    FENP = [[60, 56], [66, 56], [72, 66], [80, 70], [90, 72], [103.4, 72], [103.4, 103.4], [60, 103.4], [62, 86],
            [64, 74], [62, 64]]
    trees('scatter:fen', FENP, 5.0, FEN, 1.8, 16)
    a = K.poly_area(FENP)
    e('scatter:fen_reeds', FENP, a * 0.12, deco='plant02', clusters=a * 0.03)
    e('scatter:fen_reeds', FENP, a * 0.05, deco='plant03', clusters=a * 0.015)
    e('scatter:fen_mush', FENP, a * 0.02, deco='mushrm05', clusters=a * 0.006)
    # the lip of the world: rocks along both rims
    e('scatter:lip_rocks', None, 40, deco='7rock08', line=[[103.4, 20], [103.4, 103.4], [20, 103.4]])
    # ---- beyond the party's square to the map's edge (north and west; east and south are the rims)
    EDGE = [
        ('scatter:edge_nw', [[0, 0], [27, 0], [27, 18.5], [0, 18.5]], CREST | SCRUB, 2.0),
        ('scatter:edge_n', [[47, 0], [104, 0], [104, 18.5], [47, 18.5]], SCRUB | CREST, 1.6),
        ('scatter:edge_w', [[0, 18.5], [18.5, 18.5], [18.5, 52], [0, 52]], SCRUB, 1.4),
        ('scatter:edge_sw', [[0, 52], [18.5, 52], [18.5, 103.4], [0, 103.4]], HOWL, 14.0),
    ]
    for sid, poly, kinds, per in EDGE:
        trees(sid, poly, per, kinds, 1.6, steep=True)
        a = K.poly_area(poly)
        e(sid.replace('edge', 'edge_rocks'), poly, a * 0.02, deco='7rock09', clusters=a * 0.006, steep=True)
    return out
