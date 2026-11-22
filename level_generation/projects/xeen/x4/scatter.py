"""X4 Burlock Savannah: trees, bushes, rocks and flowers (A5, 2026-11-20). Used by gen.py.

A savannah: lone trees and small clumps over gold grass, thicker along the river and in the west downs' hollows; bare
rock on the range and the red hills, burnt rock on the lava fields; the Autumn Druid's grove a ring of trees. Trees run
on beyond the party's square to the map's edge (HANDOFF_LEAD 5: no stands "cut off" at the edge).
"""
import kit as K

SAV = {'7tree19': 3, '7tree28': 2, '7tree22': 1, 'tree29': 1}   # tree29 for 6tree12 (no 3D model; A5 lead 2026-11-20)
RIVER_T = {'7tree19': 2, '7tree25': 2, '7tree07': 1}
HILL = {'7tree22': 2, '7tree16': 1, '6tree09': 1}
AUTUMN = {'7tree07': 2, '7tree25': 2}


def scatter():
    out = []

    def e(sid, poly, count, deco=None, kinds=None, spacing=None, clusters=None, steep=False, group=None, line=None,
          circle=None):
        d = {'id': sid, 'count': int(count)}
        if deco:
            d['decoration'] = deco
        if kinds:
            d['kinds'] = dict(kinds)
        if poly:
            d['polygon'] = poly
        if line:
            d['line'] = line
        if circle:
            d['circle'] = circle
        if spacing:
            d['spacing'] = spacing
        if clusters:
            d['clusters'] = int(clusters)
        if steep:
            d['steep'] = True
        if group:
            d['spacing_group'] = group
        out.append(d)

    def trees(sid, poly, per_100, kinds, spacing=1.8, clusters=None):
        e(sid, poly, max(1, per_100 * K.poly_area(poly) / 100.0), kinds=kinds, spacing=spacing, clusters=clusters,
          group='trees')

    # ---- the savannah, in pieces round the towns (no holes in a polygon)
    trees('scatter:sav_uplands', [[19, 46], [54, 44], [54, 62], [44, 64], [32, 62], [19, 62]], 2.2, SAV, 2.2, 12)
    trees('scatter:sav_castle_fields', [[70, 50], [77, 50], [77, 63], [70, 63]], 1.5, SAV, 2.2)
    trees('scatter:sav_west_downs', [[19, 62], [33, 62], [32, 78], [33, 104], [19, 104]], 1.9, SAV, 2.0, 10)
    trees('scatter:sav_south', [[33, 93], [77, 93], [77, 106], [38, 106], [33, 104]], 2.0, SAV, 2.2, 12)
    trees('scatter:sav_mid', [[52, 79], [77, 79], [77, 93], [52, 93]], 1.6, SAV, 2.2, 8)
    trees('scatter:sav_road_w', [[33, 63], [54, 63], [58, 72], [52, 78], [33, 78]], 1.6, SAV, 2.2, 8)
    trees('scatter:sav_east', [[84, 50], [98, 50], [100, 66], [94, 80], [84, 80]], 2.0, SAV, 2.2, 10)
    trees('scatter:sav_east_s', [[84, 80], [94, 80], [92, 96], [98, 108], [86, 108], [84, 96]], 1.8, SAV, 2.2, 8)
    # ---- along the river: willows and bank plants
    trees('scatter:river_w', [[74, 52], [78, 52], [78, 108], [74, 108]], 4.0, RIVER_T, 1.6)
    trees('scatter:river_e', [[82, 50], [85, 50], [85, 96], [82, 96]], 4.0, RIVER_T, 1.6)
    e('scatter:bank_plants', [[74, 48], [86, 48], [86, 109], [74, 109]], 50, deco='plant02', clusters=16)
    # ---- the Autumn Druid's grove: a ring of red and gold trees round the stones
    e('scatter:autumn_grove', None, 14, kinds=AUTUMN,
      line=[[26 + 3.0 * c, 70 + 3.0 * s] for c, s in ((1, 0), (0.7, 0.7), (0, 1), (-0.7, 0.7), (-1, 0), (-0.7, -0.7),
                                                      (0, -1), (0.7, -0.7))])
    out[-1]['closed'] = True
    e('scatter:autumn_leaves', [[23, 67], [29, 67], [29, 73], [23, 73]], 12, deco='flower05', clusters=5)
    # ---- bushes, grass flowers and rocks on the open land
    for sid, poly in (('w', [[19, 46], [54, 44], [54, 77], [19, 77]]), ('sw', [[19, 77], [33, 77], [33, 104], [19, 104]]),
                      ('s', [[33, 93], [77, 93], [77, 108], [33, 108]]),
                      ('e', [[84, 50], [100, 50], [100, 108], [84, 108]])):
        a = K.poly_area(poly)
        e('scatter:bushes_' + sid, poly, a * 0.06, deco='bush02', clusters=a * 0.015)
        e('scatter:bushes_' + sid, poly, a * 0.04, deco='bush03', clusters=a * 0.01)   # bush03 for bush07 (no model)
        e('scatter:flowers_' + sid, poly, a * 0.04, deco='flower04', clusters=a * 0.01)
        e('scatter:rocks_' + sid, poly, a * 0.02, deco='7rock09', clusters=a * 0.006)
    # ---- the range: bare rock, a few hardy trees at its foot
    RANGE = [[19, 24], [98, 24], [98, 40], [76, 42], [56, 42], [40, 45], [19, 48]]
    e('scatter:range_rocks', RANGE, 70, deco='7rock08', clusters=24, steep=True)
    e('scatter:range_rocks', RANGE, 50, deco='rock09', clusters=18, steep=True)
    trees('scatter:range_foot', [[19, 40], [54, 38], [54, 46], [19, 49]], 1.6, HILL, 2.0, 6)
    # ---- the red dwarf hills and the lava fields
    RED = [[94, 78], [109, 76], [109, 109], [98, 109], [92, 96]]
    e('scatter:red_rocks', RED, 60, deco='7rock08', clusters=20, steep=True)
    e('scatter:red_rocks', RED, 30, deco='rock03', clusters=10, steep=True)
    trees('scatter:red_trees', RED, 1.0, HILL, 2.4)
    LAVA = [[98, 26], [109, 26], [109, 58], [104, 58], [99, 52], [96, 42]]
    e('scatter:lava_rocks', LAVA, 30, deco='Brnrock0', clusters=10, steep=True)
    e('scatter:lava_rocks', LAVA, 30, deco='7rock08', clusters=10, steep=True)
    # ---- in the villages: yard trees and flowers (TOWN_FEEL 6), off the doors' lines
    # (Burlock's yard trees and flowers are single decorations in places.py: the village wall's box keeps scatter out)
    for i, at in enumerate([(34.6, 80.0), (50.8, 90.6), (34.8, 91.2), (47.6, 79.4)]):
        e('scatter:asp_trees', None, 1, deco=['7tree22', '7tree19'][i % 2], circle={'at': list(at), 'r': 0.15})

    # ---- beyond the party's square to the map's edge (west, south, east; the north is the rim)
    EDGE = [
        ('scatter:edge_w', [[0, 47], [19, 47], [19, 128], [0, 128]], HILL, 3.0),
        ('scatter:edge_s', [[19, 109], [109, 109], [109, 128], [19, 128]], SAV, 3.0),
        ('scatter:edge_e', [[109, 58], [128, 58], [128, 128], [109, 128]], HILL, 2.4),
    ]
    for sid, poly, kinds, per in EDGE:
        trees(sid, poly, per, kinds, 1.8)
        a = K.poly_area(poly)
        e(sid.replace('edge', 'edge_rocks'), poly, a * 0.02, deco='7rock09', clusters=a * 0.006, steep=True)
        e(sid.replace('edge', 'edge_bushes'), poly, a * 0.03, deco='bush02', clusters=a * 0.008)
    e('scatter:edge_rocks_ne', [[109, 24], [128, 24], [128, 58], [109, 58]], 30, deco='Brnrock0', clusters=8,
      steep=True)
    return out
