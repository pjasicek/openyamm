"""X7 Mount Firestone: scrub, dead trees, rocks and bones (A5, 2026-11-20, after X6's scatter.py).

The south slopes: dry scrub, thorn bushes, a few dead trees and red rock (not "ultra empty": every view has something
in its middle distance, HANDOFF_LEAD 5); the Red Dwarf Range: bare rock and scree on its peaks (D-40: bare peaks, no
forest); the north: grey and black rock on the ash, dead trees by the lake, bones; Mount Firestone: black rock on its
flanks. Stands run beyond the party's square west and south to the map's edge; the rims (x 104, y 24) end the land.
The arrival view up the X1 road and the signature view across the lava cove are kept low near the camera.
"""
import kit as K
import land as LD

SCRUB = {'bush03': 3, 'bush10': 1, 'bush12': 1, 'plant49': 2, 'plant28': 1}
DEAD = {'tree28': 3, 'plant43': 1}
RED_ROCK = ['rock24', 'rock25', 'rock27', 'rock28', 'rock30', 'rock33']
GREY_ROCK = ['7rock08', '7rock09', '6rock07']
BONES = {'dec29': 1, '7dec18': 1, 'dec19': 1}


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
            d['clusters'] = max(1, min(64, int(clusters)))
        if steep:
            d['steep'] = True
        if group:
            d['spacing_group'] = group
        out.append(d)

    def trees(sid, poly, per_100, kinds, spacing=2.5, steep=False):
        e(sid, poly, per_100 * K.poly_area(poly) / 100.0, kinds=kinds, spacing=spacing, group='trees', steep=steep)

    def cover(sid, poly, scrub=0.05, rocks=0.03, rock_kinds=None, steep_rocks=True):
        a = K.poly_area(poly)
        if scrub:
            e('scatter:%s_scrub' % sid, poly, a * scrub, kinds=SCRUB, clusters=a * scrub / 3.5)
        kinds = rock_kinds or RED_ROCK[:3]
        e('scatter:%s_rocks' % sid, poly, a * rocks, kinds={k: 1 for k in kinds}, clusters=a * rocks / 6.0,
          steep=steep_rocks)

    # ---- the south slopes (E2, F2): red stony ground, dry scrub, a few dead trees; west hills beyond the square
    SW = [[0, 76], [24, 76], [44, 74], [56, 76], [58, 128], [0, 128]]
    cover('southwest', SW, scrub=0.09, rocks=0.05)
    trees('scatter:southwest_dead', SW, 0.6, DEAD)
    SE = [[58, 76], [70, 74], [84, 78], [103.4, 76], [103.4, 128], [58, 128]]
    cover('southeast', SE, scrub=0.09, rocks=0.05)
    trees('scatter:southeast_dead', SE, 0.5, DEAD)
    e('scatter:south_grass', [[0, 78], [103.4, 78], [103.4, 128], [0, 128]], 220, deco='plant28', clusters=60)
    # ---- the Red Dwarf Range: bare rock and scree, almost no plants (D-40: bare peaks)
    RANGE = [[0, 58.5], [30, 58.5], [44, 57.5], [62, 59], [76, 55.5], [88, 60], [103.4, 57.5], [103.4, 76],
             [84, 78], [70, 74], [58, 76], [44, 74], [24, 76], [0, 74]]
    a = K.poly_area(RANGE)
    e('scatter:range_rocks', RANGE, a * 0.07, kinds={k: 1 for k in RED_ROCK + GREY_ROCK}, clusters=a * 0.02,
      steep=True)
    e('scatter:range_scrub', RANGE, a * 0.02, kinds=SCRUB, clusters=a * 0.006)
    # ---- the ash flats and the lava basin: grey rock, dead trees, bones (the lake, its island and the river clear)
    BASIN = [[0, 24.6], [52, 24.6], [52, 56], [44, 58], [30, 58.5], [0, 58.5]]
    a = K.poly_area(BASIN)
    e('scatter:basin_rocks', BASIN, a * 0.045, kinds={k: 1 for k in GREY_ROCK}, clusters=a * 0.01, steep=True)
    trees('scatter:basin_dead', BASIN, 0.5, DEAD, 3.0)
    e('scatter:basin_bones', BASIN, 16, kinds=BONES, clusters=6)
    FLATS = [[52, 29.6], [66, 29.6], [70, 33], [75, 42], [74, 55], [62, 59], [52, 56]]
    a = K.poly_area(FLATS)
    e('scatter:flats_rocks', FLATS, a * 0.05, kinds={k: 1 for k in GREY_ROCK}, clusters=a * 0.012, steep=True)
    trees('scatter:flats_dead', FLATS, 0.35, DEAD, 3.5)
    e('scatter:flats_bones', FLATS, 10, kinds=BONES, clusters=4)
    # ---- Mount Firestone: black rock on its flanks (no plants above the foot)
    CONE = [[79.5, 24.6], [103.4, 24.6], [103.4, 57], [88, 59.5], [77, 54], [76, 36], [78.5, 30]]
    a = K.poly_area(CONE)
    e('scatter:cone_rocks', CONE, a * 0.04, kinds={'7rock08': 1, '7rock09': 1, '6rock07': 1}, clusters=a * 0.012,
      steep=True)
    # ---- the rims' lip: rocks along it (the cove and its lip kept clear for the falls and the signature camera)
    e('scatter:lip_rocks', None, 40, deco='7rock08', line=[[1, 24.7], [66.4, 24.7]])
    e('scatter:lip_rocks', None, 14, deco='7rock08', line=[[80.6, 24.7], [103.3, 24.7]])
    e('scatter:lip_rocks', None, 28, deco='7rock09', line=[[103.3, 26], [103.3, 126]])
    return out
