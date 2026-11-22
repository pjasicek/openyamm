"""X6 Desert of the Sphinx: palms, cacti, scrub, rocks and bones (A5, 2026-11-20, after D3's scatter.py).

Date palms thick round the oasis pond and in Sphinx Wells' yards, a green ring at the Summer Druid's spring; cacti,
desert scrub and tumbleweed thin on the dunes and the steppe (not "ultra empty": every view has something in its
middle distance, HANDOFF_LEAD 5); red rock on the mesas, the Basenji heights and the Barbaric Mountains; bones in the
bone fields. Stands run on beyond the party's square to the map's edge east and south (no trees cut off at the edge);
the rims (x 24, y 24) end the land west and north. The signature view from [38, 96] north-west along the rim is kept
low (scrub and rocks only between the crest and the Southern Sphinx).
"""
import kit as K

PALM = {'tree01': 2, 'tree02': 2, 'tree03': 2, 'tree05': 1, 'tree07': 1, 'tree08': 1}
CACTI = {'cac3': 1, 'cac5': 1, 'cac7': 1, 'cac8': 1, 'cac10': 1, 'cac15': 1, 'cac17': 1, 'cac23': 1, 'cac25': 1,
         'plant50': 1, 'plant51': 1, 'plant53': 1}
SCRUB = {'bush03': 3, 'bush10': 1, 'bush12': 1, 'plant49': 2, 'plant28': 1}
DEAD = {'tree28': 3, 'plant43': 1}
OLIVE = {'7tree19': 3, 'tree02': 1, 'tree05': 1}
RED_ROCK = ['rock24', 'rock25', 'rock27', 'rock28', 'rock30', 'rock33']
GREY_ROCK = ['7rock08', '7rock09', '6rock07']


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

    def ground_cover(sid, poly, scrub=0.05, cacti=0.025, rocks=0.03, rock_kinds=None, steep_rocks=True):
        a = K.poly_area(poly)
        e('scatter:%s_scrub' % sid, poly, a * scrub, kinds=SCRUB, clusters=a * scrub / 3.5)
        e('scatter:%s_cacti' % sid, poly, a * cacti, kinds=CACTI, clusters=a * cacti / 2.5)
        for k, r in enumerate(rock_kinds or RED_ROCK[:3]):
            e('scatter:%s_rocks' % sid, poly, a * rocks / len(rock_kinds or RED_ROCK[:3]), deco=r,
              clusters=a * rocks / 8.0, steep=steep_rocks)

    # ---- the oasis: palms thick round the pond (not on the track or the fountain)
    OASIS = [[36, 58.5], [41.5, 57.8], [47, 59], [47.5, 60.2], [44.2, 60.3], [44.8, 64.4], [43.4, 66.2],
             [39.6, 66.8], [36, 66.2], [35.4, 62.5]]
    trees('scatter:oasis_palms', OASIS, 30, PALM, 1.0, 9)
    e('scatter:oasis_reeds', [[37.6, 59.8], [44.6, 59.8], [44.6, 65.4], [37.6, 65.4]], 14, deco='plant02',
      clusters=8)
    # ---- Sphinx Wells: palms in the yards behind the houses and round the camel pen
    for sid, poly in (('n', [[56.2, 55.2], [61.2, 55.2], [61.2, 57.6], [56.2, 57.6]]),
                      ('s', [[56.5, 64.0], [66.5, 64.0], [66.5, 66.5], [56.5, 66.5]]),
                      ('e', [[66.2, 56.0], [68.5, 56.0], [68.5, 64.5], [66.2, 64.5]])):
        trees('scatter:wells_palms_' + sid, poly, 14, PALM, 1.4)
    # ---- the Summer Druid's grove: olives and palms round the spring
    GROVE = [[67.6, 86.6], [73.6, 86.6], [74.0, 92.4], [67.4, 92.4]]
    trees('scatter:druid_grove', GROVE, 22, OLIVE, 1.3)
    e('scatter:grove_flowers', GROVE, 14, deco='plant21', clusters=5)
    # ---- the north-east dunes round the Sphinx and the mesas: sparse cacti, scrub, rocks; the forecourt kept clear
    NE = [[58, 31], [76, 30], [77.5, 33], [77.5, 46.8], [88, 46.8], [88, 33], [99, 30], [100, 50], [90, 53],
          [76, 53], [62, 52], [59, 44]]
    trees('scatter:ne_dead', NE, 0.5, DEAD, 3.0)
    ground_cover('ne', NE, scrub=0.05, cacti=0.03, rocks=0.03)
    e('scatter:mesa_rocks', [[62, 30], [75, 30], [75, 45], [62, 45]], 50, kinds={k: 1 for k in RED_ROCK},
      clusters=14, steep=True)
    # ---- the pan: thin scrub and tumbleweed, a few dead trees (quiet but not empty)
    PAN = [[46, 53.5], [100, 51.5], [104, 56], [104, 65.5], [88, 64], [72, 68], [56, 70], [46, 68]]
    trees('scatter:pan_dead', PAN, 0.25, DEAD, 3.5)
    a = K.poly_area(PAN)
    e('scatter:pan_scrub', PAN, a * 0.06, kinds=SCRUB, clusters=a * 0.018)
    e('scatter:pan_cacti', PAN, a * 0.025, kinds=CACTI, clusters=a * 0.008)
    e('scatter:pan_rocks', PAN, a * 0.02, kinds={'rock28': 1, 'rock30': 1, '7rock09': 1}, clusters=a * 0.006)
    trees('scatter:road_palms', [[66, 58.6], [80, 58.6], [80, 63.6], [66, 63.6]], 1.6, PALM, 2.6)
    # ---- the cliff foot under Basenji and the west to the shrine
    FOOT = [[25, 43], [36, 39.2], [44, 39.2], [44, 47], [50, 49], [52, 53.5], [46, 57], [36, 57.5], [25, 57]]
    ground_cover('foot', FOOT, scrub=0.05, cacti=0.03, rocks=0.05, rock_kinds=RED_ROCK)
    trees('scatter:foot_palms', [[25, 49], [32, 49], [32, 57], [25, 57]], 2.0, PALM, 2.4)
    # ---- the Basenji heights: rock, a few dead trees and scrub (the castle's crag clear)
    HEIGHTS = [[24.5, 24.5], [58, 24.5], [58, 31], [55.5, 36], [46, 37.4], [44.6, 37.4], [44.6, 33.4],
               [32.4, 33.4], [32.4, 37.6], [24.5, 41.5]]
    e('scatter:heights_rocks', HEIGHTS, 90, kinds={k: 1 for k in RED_ROCK + GREY_ROCK}, clusters=24, steep=True)
    e('scatter:heights_scrub', HEIGHTS, 40, kinds=SCRUB, clusters=12)
    trees('scatter:heights_dead', HEIGHTS, 0.6, DEAD, 3.0)
    # ---- the west rim dunes: cacti and scrub; the signature view's foreground kept low; Saul's palms
    WD = [[24.5, 68], [40, 70], [56, 70], [56, 88], [48, 100], [45, 110], [25.6, 110], [25.6, 76], [24.5, 76]]
    ground_cover('west', WD, scrub=0.045, cacti=0.03, rocks=0.02)
    trees('scatter:west_dead', [[40, 70], [56, 70], [56, 88], [46, 88], [42, 80]], 0.6, DEAD, 3.0)
    trees('scatter:saul_palms', [[27, 66.5], [33.8, 66.5], [33.8, 68.4], [27, 68.4]], 30, PALM, 1.2)
    # ---- the bone fields and the ruin fields
    RF = [[56, 70], [72, 68], [88, 64.5], [88, 80], [96, 88], [90, 90], [80, 90], [66, 92], [56, 88]]
    ground_cover('ruin', RF, scrub=0.05, cacti=0.025, rocks=0.03, rock_kinds=['rock28', 'rock30', '7rock09'])
    trees('scatter:ruin_dead', RF, 0.5, DEAD, 3.0)
    # ---- the dry downs toward X4: scrub, cacti, a few palms in the hollows
    DOWNS = [[88, 65.5], [104, 66], [128, 66], [128, 87], [108, 86], [96, 88], [88, 80]]
    ground_cover('downs', DOWNS, scrub=0.06, cacti=0.03, rocks=0.035)
    trees('scatter:downs_dead', DOWNS, 0.7, DEAD, 3.0)
    trees('scatter:downs_palms', [[100, 68], [110, 68], [110, 74], [100, 74]], 2.5, PALM, 2.2)
    # ---- the south steppe: dry grass, scrub; the coach track and the druid's grove kept clear by spacing
    ST = [[44, 88], [56, 88], [66, 92], [80, 90], [82, 91.5], [82, 99.5], [89, 99.5], [90, 128], [44, 128]]
    ground_cover('steppe', ST, scrub=0.07, cacti=0.025, rocks=0.025)
    a = K.poly_area(ST)
    e('scatter:steppe_grass', ST, a * 0.06, deco='plant28', clusters=a * 0.02)
    trees('scatter:steppe_dead', ST, 0.5, DEAD, 3.0)
    # ---- the Barbaric Mountains and the Gargoyle foothills: red rock and scree
    for sid, poly in (('barbaric', [[89.6, 86], [128, 85], [128, 128], [90, 128], [89.6, 99.5]]),
                      ('gargoyle', [[100, 24.5], [128, 24.5], [128, 54], [110, 54], [100, 50]]),
                      ('north_ridge', [[58, 24.5], [100, 24.5], [100, 30], [77, 30.5], [58, 30.5]])):
        a = K.poly_area(poly)
        e('scatter:%s_rocks' % sid, poly, a * 0.09, kinds={k: 1 for k in RED_ROCK + GREY_ROCK},
          clusters=a * 0.025, steep=True)
        e('scatter:%s_scrub' % sid, poly, a * 0.03, kinds=SCRUB, clusters=a * 0.01)
        trees('scatter:%s_dead' % sid, poly, 0.5, DEAD, 3.0, steep=True)
    # ---- the stony rises in the south-west corner, beyond the square to the edges
    SW = [[24.5, 110], [45, 110], [44, 128], [24.5, 128]]
    ground_cover('sw', SW, scrub=0.05, cacti=0.02, rocks=0.06, rock_kinds=GREY_ROCK)
    # the coach yard's rock shoulders and the cliff at its back
    e('scatter:yard_rocks', [[80, 88], [93, 88], [93, 91.6], [80, 91.6]], 26, kinds={k: 1 for k in RED_ROCK},
      clusters=8, steep=True)
    e('scatter:yard_rocks', [[80, 98.4], [93, 98.4], [93, 102], [80, 102]], 24, kinds={k: 1 for k in RED_ROCK},
      clusters=8, steep=True)
    # the rims' lip: rocks along it (not in the signature view's sand-fall spots)
    e('scatter:lip_rocks', None, 26, deco='7rock08', line=[[24.6, 26], [24.6, 74], [24.6, 82.5]])
    e('scatter:lip_rocks', None, 34, deco='7rock08', line=[[27, 24.6], [100, 24.6], [126, 24.6]])
    return out
