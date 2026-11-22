#!/usr/bin/env python3
"""DD-08 Northern Tower: the geometry (rooms, openings) shared by L2, L3 and L4.

One BLV of four floors 448 apart (x east, y north, z up; the tower's centre at 0, 0), stacked round a split stair core
(D-61 Q29):
- L1, the gate floor (0): the porch behind the gate (never entered: the gate's click is the exit), the gatehouse, the
  Hall of Arms across the south, the great stair in the core (two storeys, its head the L2 landing), the west and east
  galleries either side of the core, the west lectern room, the dormitory, the refectory;
- L2, the armouries (448): the core's head, the west armoury (helms), the east armoury (mail), the north gallery behind
  the core, the quartermaster's store, the two wall stairs (two storeys each, up to L3) in the west and east walls;
- L3, the drill floor (896): the Stair of Silence in the core (two storeys, its head the L4 landing), the drill hall's
  west, south and east arms round it, the two wall stairs' heads, the west and east studies and their niches behind
  sliding walls;
- L4, the sanctum (1344): the chapter hall west of the core, the antechamber of the voice north, the chalice room
  behind the iron door, the Hall of Thrones east with the Dunce's alcove, the knights' cells either side, the ladder
  loft with the roof trapdoor.
The two-storey rooms carry the stairs (DD-15's way: a hanging head platform at the upper floor and one flight up to
it). Rooms are rectangles; walls between rooms are 128 thick. The inside is independent of the outside (D-49 Q6).
"""

L1, L2, L3, L4 = 0, 448, 896, 1344
H = 384            # a room's height on L1-L3 (64 of floor between it and the next floor)
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM8 Castle of Air d27 (the Towers of Mok family, as DD-05, DD-06, DD-07)
STONE = S_('gston1wl', 128, 256)     # green-grey tiled ashlar
SKIRT = S_('gstntilev', 64, 128)     # green marble skirting
FLAGS = S_('gston1fl', 128, 128)     # scale-pattern flags
CEIL = S_('gstn1cl', 128, 128)       # panelled stone ceiling
BOT = S_('gstn1bot', 128, 256)       # ashlar over a scale frieze: plinths, stands
COBBLE = S_('gcstflor', 128, 256)    # grey cobbles: the core and the stairs
GDOOR = S_('gcstdoor', 128, 256)     # the stone door
# MM7 Castle Gryphonheart 7d33: the knights' rooms (D-61, A6's accent)
DARK = S_('dchb1', 128, 256)         # dark rough stone
DFLOOR = S_('7tfb1', 128, 128)       # brown flags
DCEIL = S_('tfb2', 128, 128)         # plaster ceiling
PLANK = S_('7trimd', 128, 256)       # dark planks: beds, tables, lecterns, the trapdoor
DSQ = S_('7tfb11', 128, 128)         # dark stone squares: the niches' backs
CDOORL = S_('chb1dl', 128, 256)      # the chapter hall's left leaf (7d33)
CDOORR = S_('chb1dr', 128, 256)      # its right leaf
# The gate (D-49: the Northern Tower's pair, mirrored inside)
GATEL = S_('hkm1dl', 128, 256)
GATER = S_('hkm1dr', 128, 256)
# Pictures and signs
MIRROR = S_('xkmirror', 128, 128)    # A6's dead mirror (D-37), a seamless tile
VOWEL = S_('xdvowel', 256, 64)       # A6's "GRND RDR F VWLSS KNGHTS" over the chapter hall's doors inside
BANNER = S_('xvkban', 128, 256)      # the Voweless banner (new, A8 phase 5)
MASK = S_('xvkmask', 128, 128)       # the voice's mask (new, A8 phase 5)
PLAQUE = S_('sign22', 256, 64)       # the order's bronze plaque in the chapter hall (the oath)
WINDOW = S_('t19b04c', 128, 256)     # the Mok tower window: arrow slits on the outer walls
BOOK = S_('xnpbook', 128, 128)       # an open book: the lecterns' tops
SHEET = S_('t2bedsht', 128, 256)     # bedding
HELM_A = S_('armormid', 64, 64)      # a winged helm on boards (hung pieces)
HELM_B = S_('armorpor', 64, 64)      # a green helm on boards
HELM_C = S_('armorrch', 64, 64)      # a horned helm on boards
HELM_D = S_('7sgarm', 64, 64)        # a ram-horned helm on a shield

THEMES = [
    {'id': 'theme:tower', 'wall': STONE, 'bands': [{'height': 32, 'surface': SKIRT}], 'floor': FLAGS,
     'ceiling': CEIL, 'reveal': STONE, 'door': GDOOR,
     'notes': "The Mok tower's own rooms (MM8 Castle of Air d27, as DD-05): green-grey ashlar gston1wl over a green marble skirting gstntilev, scale-pattern flags gston1fl, panelled stone ceilings gstn1cl, the stone doors gcstdoor."},
    {'id': 'theme:stair', 'wall': STONE, 'bands': [{'height': 32, 'surface': SKIRT}], 'floor': COBBLE,
     'ceiling': CEIL, 'reveal': STONE, 'door': GDOOR,
     'notes': "The core, the wall stairs and the gatehouse: the same ashlar, grey cobbles gcstflor."},
    {'id': 'theme:knights', 'wall': DARK, 'floor': DFLOOR, 'ceiling': DCEIL, 'reveal': PLANK, 'door': GDOOR,
     'notes': "The knights' own rooms (D-61, A6's accent: MM7 Castle Gryphonheart 7d33): dark rough stone dchb1, brown flags 7tfb1, plaster ceilings tfb2, dark plank jambs 7trimd."},
]

# id: (name, box, floor, ceiling, theme)
R = {
    # L1, the gate floor (0)
    'porch': ("Porch", (-320, -1792, 320, -1536), L1, L1 + H, 'theme:stair'),
    'gatehouse': ("Gatehouse", (-512, -1408, 512, -896), L1, L1 + H, 'theme:stair'),
    'hall': ("Hall of Arms", (-1664, -768, 1664, -256), L1, L1 + H, 'theme:tower'),
    'core': ("Great stair", (-640, -128, 640, 1152), L1, L2 + H, 'theme:stair'),
    'wgal': ("West gallery", (-1664, -128, -768, 1152), L1, L1 + H, 'theme:tower'),
    'lectern_w0': ("West lectern room", (-1664, 1280, -768, 1920), L1, L1 + H, 'theme:tower'),
    'egal': ("East gallery", (768, -128, 1664, 1152), L1, L1 + H, 'theme:tower'),
    'dormitory0': ("Dormitory", (768, 1280, 1920, 2048), L1, L1 + H, 'theme:tower'),
    'refectory': ("Refectory", (1792, -768, 2688, 1024), L1, L1 + H, 'theme:tower'),
    # L2, the armouries (448)
    'helms': ("West armoury", (-1664, -128, -768, 1152), L2, L2 + H, 'theme:tower'),
    'mail': ("East armoury", (768, -128, 1664, 1152), L2, L2 + H, 'theme:tower'),
    'north_gallery1': ("North gallery", (-1664, 1280, 1664, 1920), L2, L2 + H, 'theme:tower'),
    'quartermaster': ("Quartermaster's store", (768, -768, 1664, -256), L2, L2 + H, 'theme:tower'),
    'wstair': ("West wall stair", (-2176, -512, -1792, 1280), L2, L3 + H, 'theme:stair'),
    'estair': ("East wall stair", (1792, -512, 2176, 1280), L2, L3 + H, 'theme:stair'),
    # L3, the drill floor (896)
    'core2': ("Stair of Silence", (-640, -128, 640, 1152), L3, L4 + H, 'theme:stair'),
    'drill_w': ("Drill hall (west)", (-1664, -128, -768, 1152), L3, L3 + H, 'theme:tower'),
    'drill_s': ("Drill yard (south)", (-1664, -1152, 1664, -256), L3, L3 + H, 'theme:tower'),
    'drill_e': ("Drill hall (east)", (768, -128, 1664, 1152), L3, L3 + H, 'theme:tower'),
    'west_study': ("West study", (-2176, 1408, -1408, 2048), L3, L3 + H, 'theme:tower'),
    'niche_w': ("West niche", (-2816, 1536, -2304, 1920), L3, L3 + 352, 'theme:tower'),
    'east_study': ("East study", (1408, 1408, 2176, 2048), L3, L3 + H, 'theme:tower'),
    'niche_e': ("East niche", (2304, 1536, 2816, 1920), L3, L3 + 352, 'theme:tower'),
    # L4, the sanctum (1344)
    'chapter_hall': ("Chapter hall", (-2304, -128, -768, 1152), L4, L4 + 512, 'theme:knights'),
    'antechamber': ("Antechamber of the voice", (-1664, 1280, 1664, 1920), L4, L4 + H, 'theme:tower'),
    'chalice_room': ("Chalice room", (-640, 2048, 640, 2688), L4, L4 + H, 'theme:tower'),
    'thrones': ("Hall of Thrones", (768, -128, 2304, 1152), L4, L4 + 512, 'theme:knights'),
    'dunce': ("Alcove of the Dunce", (1280, -768, 1920, -256), L4, L4 + H, 'theme:knights'),
    'east_dorm': ("Knights' cells (east)", (2432, -128, 3200, 1152), L4, L4 + H, 'theme:knights'),
    'roof_loft': ("Ladder loft", (2432, 1280, 2944, 1792), L4, L4 + 448, 'theme:tower'),
    'west_dorm': ("Knights' cells (west)", (-3072, -128, -2432, 1152), L4, L4 + H, 'theme:knights'),
}
FLOOR_NAME = {L1: 'L1', L2: 'L2', L3: 'L3', L4: 'L4'}
ORDER = sorted(R)


def outline(rid):
    x0, y0, x1, y1 = R[rid][1]
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def bbox(rid):
    return R[rid][1]


def walls_of(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


SIDE4 = {0: 's', 1: 'e', 2: 'n', 3: 'w'}


def shared(a, b):
    """The facing walls of rooms a and b: (gap, wall in a, wall in b, lo, hi, axis, p0, p1)."""
    best = None
    for i, (p0, p1) in enumerate(walls_of(a)):
        for j, (q0, q1) in enumerate(walls_of(b)):
            if p0[0] == p1[0] and q0[0] == q1[0]:
                gap = abs(p0[0] - q0[0])
                lo = max(min(p0[1], p1[1]), min(q0[1], q1[1]))
                hi = min(max(p0[1], p1[1]), max(q0[1], q1[1]))
                ax = 1
            elif p0[1] == p1[1] and q0[1] == q1[1]:
                gap = abs(p0[1] - q0[1])
                lo = max(min(p0[0], p1[0]), min(q0[0], q1[0]))
                hi = min(max(p0[0], p1[0]), max(q0[0], q1[0]))
                ax = 0
            else:
                continue
            if hi - lo <= 0 or gap > 512 or gap == 0:
                continue
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            nx, ny = dy, -dx      # the outward normal of a counter-clockwise outline
            if ax == 1 and (q0[0] - p0[0]) * nx <= 0:
                continue
            if ax == 0 and (q0[1] - p0[1]) * ny <= 0:
                continue
            cand = (gap, i, j, lo, hi, ax, p0, p1)
            if best is None or gap < best[0]:
                best = cand
    if best is None:
        raise SystemExit(f'no facing walls between {a} and {b}')
    return best


def opening(oid, a, b, at=None, width=256, height=320, link=None, **kw):
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b}
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
    if at is None:
        at = (lo + hi) / 2
    if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
        raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
    forward = (p1[ax] - p0[ax]) > 0
    along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
    if along != 0.5:
        d['along'] = along
    d['from_wall'] = SIDE4[i]
    d['to_wall'] = SIDE4[j]
    if link:
        d['link'] = link
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


DOOR_W, DOOR_H = 160, 320          # single doors (128 x 256 pictures at 1.25)
DOUBLE_W = 320                     # two leaves of 160 x 320
ARCH_W = 384
FLIGHT_W = 320

OPENINGS = [
    # L1
    opening('open:gate', 'gatehouse', 'porch', at=0, width=DOUBLE_W, height=DOOR_H, link='link:gate',
            notes="The gate (two leaves, hkm1dl|hkm1dr mirrored) in the gatehouse's south wall: clicked, 'Exit the Knight's Tower?'."),
    opening('open:gate_hall', 'gatehouse', 'hall', at=0, width=ARCH_W, link='link:gate_hall'),
    opening('open:hall_core', 'hall', 'core', at=0, width=ARCH_W, link='link:hall_core0',
            notes="The core's south arch onto the great stair's foot."),
    opening('open:hall_wgal', 'hall', 'wgal', at=-1216, width=ARCH_W, link='link:hall_wgal'),
    opening('open:wgal_core', 'wgal', 'core', at=64, width=FLIGHT_W, link='link:wgal_core0'),
    opening('open:wgal_lect', 'wgal', 'lectern_w0', at=-1216, width=DOOR_W, height=DOOR_H, link='link:wgal_lect'),
    opening('open:core_egal', 'core', 'egal', at=64, width=FLIGHT_W, link='link:core0_egal'),
    opening('open:egal_dorm', 'egal', 'dormitory0', at=1216, width=ARCH_W, link='link:egal_dorm'),
    opening('open:egal_refec', 'egal', 'refectory', at=512, width=ARCH_W, link='link:egal_refec'),
    opening('open:refec_hall', 'refectory', 'hall', at=-512, width=DOOR_W, height=DOOR_H, link='link:refec_hall'),
    # L2: off the great stair's head (448)
    opening('open:core_helms', 'core', 'helms', at=960, width=DOOR_W, height=DOOR_H, link='link:core1_helms'),
    opening('open:core_mail', 'core', 'mail', at=960, width=DOOR_W, height=DOOR_H, link='link:core1_mail'),
    opening('open:helms_north', 'helms', 'north_gallery1', at=-1216, width=ARCH_W, link='link:helms_north'),
    opening('open:north_mail', 'north_gallery1', 'mail', at=1216, width=ARCH_W, link='link:north_mail'),
    opening('open:helms_wstair', 'helms', 'wstair', at=32, width=256, link='link:helms_wstair',
            notes="Into the west wall stair's landing (L2)."),
    opening('open:mail_estair', 'mail', 'estair', at=32, width=256, link='link:mail_estair',
            notes="Into the east wall stair's landing (L2)."),
    opening('open:mail_qm', 'mail', 'quartermaster', at=1216, width=DOOR_W, height=DOOR_H, link='link:mail_qm'),
    # L3
    opening('open:core2_drillw', 'core2', 'drill_w', at=128, width=ARCH_W, link='link:drillw_core2',
            notes="The Stair of Silence's west arcade onto the drill hall."),
    opening('open:core2_drille', 'core2', 'drill_e', at=128, width=ARCH_W, link='link:core2_drille'),
    opening('open:drillw_s', 'drill_w', 'drill_s', at=-1216, width=640, link='link:drillw_s'),
    opening('open:drills_e', 'drill_s', 'drill_e', at=1216, width=640, link='link:drills_e'),
    opening('open:wstair_drill', 'wstair', 'drill_w', at=960, width=256, link='link:wstair_drill',
            notes="The west wall stair's head (896) onto the drill hall."),
    opening('open:estair_drill', 'estair', 'drill_e', at=960, width=256, link='link:drille_estair',
            notes="The east wall stair's head (896) onto the drill hall."),
    opening('open:wstair_study', 'wstair', 'west_study', at=-1984, width=DOOR_W, height=DOOR_H, link='link:wstair_study'),
    opening('open:estair_study', 'estair', 'east_study', at=1904, width=DOOR_W, height=DOOR_H, link='link:estair_study'),
    opening('open:wstudy_niche', 'west_study', 'niche_w', at=1728, width=192, height=288, link='link:wstudy_niche',
            notes="The sliding wall (117652)."),
    opening('open:estudy_niche', 'east_study', 'niche_e', at=1728, width=192, height=288, link='link:estudy_niche',
            notes="The sliding wall (117653)."),
    # L4: off the Stair of Silence's head (1344)
    opening('open:chapter', 'core2', 'chapter_hall', at=960, width=DOUBLE_W, height=DOOR_H, link='link:core3_chapter',
            notes="The chapter hall's doors: two leaves (chb1dl|chb1dr); xdvowel over them inside."),
    opening('open:core3_thrones', 'core2', 'thrones', at=960, width=320, link='link:core3_thrones'),
    opening('open:chapter_ante', 'chapter_hall', 'antechamber', at=-1216, width=ARCH_W, link='link:chapter_ante'),
    opening('open:ante_thrones', 'antechamber', 'thrones', at=1216, width=ARCH_W, link='link:ante_thrones'),
    opening('open:iron', 'antechamber', 'chalice_room', at=256, width=DOOR_W, height=DOOR_H, link='link:ante_chalice',
            notes="The iron door to the chalice room, beside the voice's mask."),
    opening('open:thrones_dunce', 'thrones', 'dunce', at=1600, width=ARCH_W, link='link:thrones_dunce'),
    opening('open:thrones_edorm', 'thrones', 'east_dorm', at=512, width=DOOR_W, height=DOOR_H, link='link:thrones_edorm'),
    opening('open:edorm_loft', 'east_dorm', 'roof_loft', at=2688, width=320, link='link:edorm_loft'),
    opening('open:chapter_wdorm', 'chapter_hall', 'west_dorm', at=512, width=DOOR_W, height=DOOR_H, link='link:chapter_wdorm'),
]


def strip_n(box, depth):
    x0, y0, x1, y1 = box
    return [[x0, y1 - depth], [x1, y1 - depth], [x1, y1], [x0, y1]]


def head(pid, outline_, floor, top, surface, top_surface, notes):
    return {'id': pid, 'rise': 32, 'base': top - floor - 32, 'outline': outline_, 'surface': dict(surface),
            'top_surface': dict(top_surface), 'bottom_surface': dict(surface), 'notes': notes}


def plat(pid, at, size, rise, surface, top=None, notes=None, **kw):
    d = {'id': pid, 'at': list(at), 'size': list(size), 'rise': rise, 'surface': dict(surface)}
    if pid is None:
        del d['id']
    if top:
        d['top_surface'] = dict(top)
    d.update(kw)
    if notes:
        d['notes'] = notes
    return d


def panel(pid, length, bottom, height, surface, notes=None, offset=None):
    d = {'length': length, 'bottom': bottom, 'height': height, 'surface': dict(surface)}
    if pid:
        d['id'] = pid
    if offset is None:
        d['at'] = 'centre'
    else:
        d['offset'] = offset
    if notes:
        d['notes'] = notes
    return d


def flight(x, y0, y1, to_height, width=FLIGHT_W, notes=None):
    return {'from': [x, y0], 'to': [x, y1], 'to_height': to_height, 'width': width, 'steps': 14, 'open_below': 32,
            'sides': {'height': 48, 'thickness': 16, 'surface': dict(STONE)}, 'notes': notes}


# Lecterns (128 square, on the 128 grid so the book's picture lies once on the top): room, centre
LECTERNS = {
    'sleeping_dogs': ('lectern_w0', (-1216, 1728)),
    'laughs_last': ('dormitory0', (1728, 1472)),
    'needs_of_many': ('wstair', (-1984, -320)),
    'love_of_money': ('estair', (1984, -320)),
    'gift_horse': ('west_study', (-1728, 1856)),
    'fool_and_money': ('east_study', (1728, 1856)),
    'wishes_horses': ('estair', (2112, 1088)),
}
BOOK_ORDER = ['sleeping_dogs', 'laughs_last', 'needs_of_many', 'love_of_money', 'gift_horse', 'fool_and_money',
              'wishes_horses']
# Beds: (room, centre, size); the cells' beds carry the Cliff Notes (aaze0072:14-20)
BEDS = {
    'dorm0_1': ('dormitory0', (896, 1856), (192, 384)), 'dorm0_2': ('dormitory0', (1120, 1856), (192, 384)),
    'dorm0_3': ('dormitory0', (1344, 1856), (192, 384)), 'dorm0_4': ('dormitory0', (1568, 1856), (192, 384)),
    'lesson_1': ('east_dorm', (3008, 64), (384, 192)), 'lesson_2': ('east_dorm', (3008, 320), (384, 192)),
    'lesson_3': ('east_dorm', (3008, 704), (384, 192)), 'lesson_4': ('east_dorm', (3008, 960), (384, 192)),
    'lesson_5': ('west_dorm', (-2880, 64), (384, 192)), 'lesson_6': ('west_dorm', (-2880, 384), (384, 192)),
    'lesson_7': ('west_dorm', (-2880, 896), (384, 192)),
}
# The thrones: (centre of the seat, side of its back)
THRONES = {
    # session 17: S's thrones by the side walls (62 from the wall), clear of the walking lines between the four
    # openings (the west arch 800-1120, the east door 432-592: the lows were at x 1088/1984, y 0/768)
    'depressed': ((896, 0), 'w'), 'confused': ((2176, 0), 'e'),
    'heartbroken': ((896, 512), 'w'), 'insane': ((2176, 960), 'e'),
    'euphoria': ((1536, 384), 'n'), 'dunce': ((1600, -576), 's'),
}
DAIS = (1536, 384)
STAND = (0, 2496)          # the chalice's stand
HATCH = (2688, 1536)       # the roof trapdoor in the loft's ceiling
STATUE = (-768, -416)      # the founder's statue's plinth in the Hall of Arms
NICHES = {                 # the chapter hall's four niches: (wall, offset) and where the hidden figure stands
    1: ('w', 160, (-2176, 864)), 2: ('w', 800, (-2176, 224)),
    3: ('s', 192, (-1984, 0)), 4: ('s', 1088, (-1088, 0)),
}


def bed(bid, room, at, size):
    return plat(f'platform:bed_{bid}', at, size, 48, PLANK, SHEET, "A bed: a straw tick under a grey blanket.")


def throne(key):
    """The seat blocks are gone (D-66 item 7): each throne is S's model, placed by dress.py at THRONES' seat centre."""
    return []


EXTRA = {
    'porch': {'notes': "Behind the gate's leaves: never entered (the gate's click is the exit)."},
    'gatehouse': {'notes': "Inside the gate: the arrival (entrance:d5_tower), the arch north into the Hall of Arms."},
    'hall': {'platforms': [plat('platform:statue', STATUE, (192, 192), 64, BOT, FLAGS,
                                "The founder's statue's plinth (its plaque, aaze0069:2).")],
             'notes': "The Hall of Arms across the tower's south side: the founder's statue by the north wall, banners and hung pieces on the south wall either side of the gate's arch."},
    'core': {'platforms': [head('platform:great_head', strip_n(R['core'][1], 384), L1, L2, STONE, COBBLE,
                                "The great stair's head (448) across the core's north end: the L2 landing, the armouries' doors west and east.")],
             'flights': [flight(0, 128, 768, L2, notes="The great stair: fourteen steps of 32 up the middle of the core, rising north to its head.")],
             'notes': "The central core's foot: arches south (the Hall of Arms), west and east (the galleries); the great stair up the middle to its head (L2)."},
    'core2': {'platforms': [head('platform:silence_head', strip_n(R['core2'][1], 384), L3, L4, STONE, DFLOOR,
                                 "The Stair of Silence's head (1344) across the core's north end: the chapter hall's doors west, the Hall of Thrones' arch east.")],
              'flights': [flight(0, 128, 768, L4, notes="The Stair of Silence: fourteen steps up the middle of the core to the sanctum.")],
              'notes': "The core again, above the great stair's vault: arcades west and east onto the drill hall, the upper flight to L4."},
    'wstair': {'platforms': [head('platform:wstair_head', strip_n(R['wstair'][1], 512), L2, L3, STONE, COBBLE,
                                  "The west wall stair's head (896): the drill hall east, the west study north.")],
               'flights': [flight(-1984, 128, 768, L3, width=256, notes="Fourteen steps in the west wall's thickness, rising north.")],
               'notes': "The stair in the west wall's thickness from L2 to L3; the third book on its landing."},
    'estair': {'platforms': [head('platform:estair_head', strip_n(R['estair'][1], 512), L2, L3, STONE, COBBLE,
                                  "The east wall stair's head (896): the drill hall west, the east study north, the seventh book by the slit.")],
               'flights': [flight(1984, 128, 768, L3, width=256, notes="Fourteen steps in the east wall's thickness, rising north.")],
               'notes': "The east twin from L2 to L3; the fourth book on its landing, the seventh on its head."},
    'refectory': {'platforms': [plat(None, (2368, -128), (512, 128), 80, PLANK, PLANK, "A long table."),
                                plat(None, (2368, 832), (512, 128), 80, PLANK, PLANK, "A long table."),
                                plat(None, (2368, -288), (512, 64), 40, PLANK, PLANK, "A bench."),
                                plat(None, (2368, 672), (512, 64), 40, PLANK, PLANK, "A bench."),
                                plat('platform:pulpit', (2560, -640), (128, 128), 144, PLANK, PLANK,
                                     "The silent reader's pulpit: no book on it.")],
                  'notes': "Long tables and benches pushed in; the silent reader's pulpit without a book."},
    'thrones': {'platforms': [plat('platform:dais', DAIS, (512, 512), 48, DARK, DFLOOR, "The Euphoria Throne's dais.")]
                + throne('depressed') + throne('confused') + throne('heartbroken') + throne('insane') + throne('euphoria'),
                'notes': "Four Emotion Thrones round the raised Euphoria Throne (aaze0072:8-9); the Dunce's alcove south."},
    'dunce': {'notes': "The Throne of the Dunce alone in its alcove (aaze0072:10): S's throne model (dress.py)."},
    'chalice_room': {'platforms': [plat('platform:stand', STAND, (128, 128), 112, BOT, FLAGS,
                                        "The Chalice's stand (q-d17.chalice).")],
                     'notes': "Behind the iron door: the Chalice of Protection on its stand under one lamp."},
    'roof_loft': {'platforms': [plat('platform:roof_hatch', HATCH, (160, 160), 32, PLANK, PLANK,
                                     "The roof trapdoor: a plank leaf shut in the ceiling (D-58: up to D7 after m30.done).",
                                     base=416, bottom_surface=dict(PLANK))],
                  'notes': "A small room under the roof trapdoor (d7.roof_dd08)."},
    'quartermaster': {'notes': "The store: crates, sacks and paired barrels by the walls, the strongbox in the corner."},
}
for _b in BOOK_ORDER:
    _room, (_x, _y) = LECTERNS[_b]
    EXTRA.setdefault(_room, {}).setdefault('platforms', []).extend([
        plat(None, (_x, _y), (96, 96), 96, PLANK, PLANK, "The lectern's post."),
        plat(f'platform:book_{_b}', (_x, _y), (128, 128), 16, PLANK, BOOK, "A lectern: a book of the Voweless Knights.",
             base=96, bottom_surface=dict(PLANK))])
for _k, (_room, _at, _sz) in BEDS.items():
    EXTRA.setdefault(_room, {}).setdefault('platforms', []).append(bed(_k, _room, _at, _sz))


def ban(pid, offset, notes="A Voweless banner (xvkban)."):
    return panel(pid, 128, 64, 256, dict(BANNER, fit=True), notes, offset=offset)


FURNISH = {
    'hall': {'walls': [
        {'wall': 's', 'panels': [ban('panel:banner_hall_1', 320), ban('panel:banner_hall_2', 2880),
                                 panel('panel:shield_find', 128, 160, 128, dict(HELM_D, fit=True), "A shield and helm hung on the wall: a find (117654).", offset=1024),
                                 panel(None, 128, 160, 128, dict(HELM_A, fit=True), "A helm hung on the wall.", offset=2176)]}]},
    'wgal': {'walls': [{'wall': 'w', 'panels': [panel('panel:mirror', 128, 32, 288, MIRROR, "The dead mirror (xkmirror, D-37).")]}]},
    'helms': {'walls': [{'wall': 'w', 'panels': [panel('panel:helm_find', 128, 160, 128, dict(HELM_C, fit=True), "A helm on a peg: a find (117655).", offset=384),
                                                  panel(None, 128, 160, 128, dict(HELM_B, fit=True), "A helm on a peg.", offset=768)]}]},
    'mail': {'walls': [{'wall': 'e', 'panels': [panel('panel:mail_find', 128, 160, 128, dict(HELM_A, fit=True), "Black plate on its stand: a find (117656).", offset=384),
                                                 panel(None, 128, 160, 128, dict(HELM_B, fit=True), "Black plate on its stand.", offset=896)]}]},
    'north_gallery1': {'walls': [{'wall': 'n', 'panels': [panel(None, 128, 64, 256, dict(WINDOW, fit=True), "An arrow slit.", offset=off) for off in (896, 2304)]}]},
    'drill_s': {'walls': [{'wall': 's', 'panels': [panel(None, 128, 64, 256, dict(WINDOW, fit=True), "An arrow slit.", offset=off) for off in (768, 1600, 2432)]}]},
    'estair': {'walls': [{'wall': 'e', 'panels': [panel(None, 128, 512, 256, dict(WINDOW, fit=True), "The slit by the seventh book.", offset=1536)]}]},
    'chapter_hall': {'walls': [
        {'wall': 'n', 'panels': [panel('panel:plaque', 256, 160, 64, dict(PLAQUE, fit=True), "The order's plaque (q-d17.oath).", offset=896),
                                 ban(None, 704), ban(None, 1280)]},
        {'wall': 'e', 'panels': [panel(None, 256, 336, 64, dict(VOWEL, fit=True), "Over the doors inside: GRND RDR F VWLSS KNGHTS (xdvowel).", offset=960)]},
    ]},
    'thrones': {'walls': [{'wall': 'e', 'panels': [ban(None, 160), ban(None, 1088)]}]},
    'antechamber': {'walls': [{'wall': 'n', 'panels': [panel('panel:mask', 192, 96, 192, dict(MASK, fit=True), "The voice's mask (xvkmask).", offset=1824)]}]},
}
for _n, (_wall, _off, _at) in NICHES.items():
    _w = next((w for w in FURNISH['chapter_hall']['walls'] if w['wall'] == _wall), None)
    if _w is None:
        _w = {'wall': _wall, 'panels': []}
        FURNISH['chapter_hall']['walls'].append(_w)
    _w['panels'].append(panel(f'panel:niche_{_n}', 256, 0, 384, DSQ, "A niche of dark stone: a knight of the order stands here after the oath.", offset=_off))


def merge_extra():
    for rid, extra in FURNISH.items():
        e = EXTRA.setdefault(rid, {})
        for k, v in extra.items():
            e[k] = e.get(k, []) + v


def room_doc(rid):
    name, b, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
    d.update(EXTRA.get(rid, {}))
    return d


def extent(rid):
    x0, y0, x1, y1 = bbox(rid)
    return [x1 - x0, y1 - y0], [(x0 + x1) // 2, (y0 + y1) // 2]


def area(rid):
    x0, y0, x1, y1 = bbox(rid)
    return (x1 - x0) * (y1 - y0)


merge_extra()

if __name__ == '__main__':
    tot = 0
    by = {}
    for r in ORDER:
        a = area(r)
        tot += a
        by[R[r][2]] = by.get(R[r][2], 0) + a
        print(f'{r:16s} {a / 1e6:6.2f}')
    print('total', tot / 1e6, 'rooms', len(ORDER), {FLOOR_NAME[k]: round(v / 1e6, 1) for k, v in by.items()})
