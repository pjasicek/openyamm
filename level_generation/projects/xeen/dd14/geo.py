#!/usr/bin/env python3
"""DD-14 Castle Blackfang: the geometry (rooms, openings) shared by L2, L3 and L4.

One BLV of four floors in one frame (x east, y north, z up; z 0 the castle's ground floor on the crag top):
- L1, the walls (1280): the wall walks round the courtyard open to the sky (preset xeen_darkside_fading), the griffin's
  landing on the south walk, the four corner towers' top storeys and the keep's top chamber (the bat roost);
- L2, the upper floor (640): the long gallery and the black chapel (south), the library (east), the keep's upper hall
  and the Count's study (north), the Countess's rooms and the sleeping hall (west);
- L3, the ground floor (0): the courtyard open to the sky, the kitchen and the cask cellar (west), the great hall and
  the grand stair hall (north), the Count's hall behind them and the family crypt behind it;
- the dungeon (-640) cut into the crag: the gaolers' stair, the question room, the cells and the ladder shaft, the
  Queen's cell, the pillared undercroft and the black cistern.
The two-storey rooms carry the stairs (DD-07's and XD-12's way: a hanging head platform at the upper floor and one
flight up to it): the south-west and south-east towers (640 to 1280; their head is the tower's top storey), the grand
stair hall and the servants' back stair (0 to 640), the dungeon stair (-640 to 0). The courtyard stair climbs the
courtyard's south wall to a head at 1280 in its south-west corner, where the yard gate opens onto the landing.
Rooms are rectangles; walls between rooms are 128 thick; the inside is larger than the outside (D-42 DD-05 (6)).
"""

L3, L2, L1, DUN = 0, 640, 1280, -640
SKY = 1792             # the walks' and the courtyard's sky
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM7 Castle Navan (7d32): the halls
HALLWALL = S_('ceb1sa', 128, 256)      # green dressed stone
BROWN = S_('twb2', 128, 256)           # brown block: towers, library, the dungeon (7d13 too)
REDSTONE = S_('cwb1', 128, 256)        # dark red stone: the black chapel
MARBLE = S_('t3s2fl1', 128, 128)       # bordered marble flags: the halls' floors
ROCKFLOOR = S_('cfb1', 128, 128)       # dark rough stone: the dungeon's vaults, the walks
COFFER = S_('t5s1c2', 128, 128)        # coffered ceilings
PILLAR = S_('cwb', 128, 256)           # pillar stone, reveals
SLABDOOR = S_('twb1a', 128, 256)       # Navan's plain slab doors
DARKBRICK = S_('wall', 128, 256)       # dark brick: the courtyard, the kitchen and cellar
# MM7 Zokarr's Tomb (7d13): the crypt, the coffin niches, the dungeon, the cistern
DRESSED = S_('7tws2', 128, 256, scale=2)   # dressed stone under its frieze, once up a 512 wall (the crypt)
SLAB = S_('twb1', 128, 256)            # pale slab: the cistern, coffin ends
FLAGS = S_('7tfb1', 128, 128)          # big worn flags
PALEFLAGS = S_('tfb2', 128, 128)       # pale worn flags: kitchen, cellar, hearths
IRONDOOR = S_('t5d1', 128, 256)        # iron-bound doors
NICHE_R = S_('7twb2vr', 128, 256)      # the niches' trim (right edge)
NICHE_L = S_('7twb2vl', 128, 256)      # (left edge)
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}
# D4's towers kit (the outside of the castle): the walks
WALKWALL = S_('hkm3b', 128, 256, scale=2)  # slate-blue stone under the skull frieze, once up the walk's 512
SKULLFRAME = S_('hkm2bs', 128, 256)    # black rubble in a skull frame (the walks' reveals and the gate's jambs)
WINDOW = S_('hkm3elw', 128, 256)       # a shuttered window under a ram skull (D4's tower windows)
SLATE = S_('xtslate', 128, 128)        # slate: the tower cones' soffits
SKYFACE = S_('t5s1c2', 128, 128, sky=True)
# doors and pictures
OAK = [[S_('chb1dl', 128, 256), S_('chb1dr', 128, 256)]]   # the arched oak pair (DD-03's)
CREST = S_('xbfcrest', 128, 128)       # Blackfang's arms (new, A8 phase 4)
GONG = S_('xngong', 128, 128)          # XD-03's bronze gong
GRILLE = S_('xwcage', 128, 256)        # cage bars (D-22.1)
IRON = S_('xwiron', 128, 128)          # iron plate: the bar, cage tops
COFFINWOOD = S_('7trimd', 128, 256)    # weathered dark planks: coffins
LID = S_('7gt003a', 64, 64)            # planks: coffin lids
BOOKS = S_('7t1books', 128, 256)       # bookshelves
BEDTOP = S_('7t1beds2', 128, 256)
BEDSIDE = S_('7t1beds1', 256, 32)
TABLE = S_('7trimda', 256, 128)        # tables, the desk
BOOKTOP = S_('xnpbook', 128, 128, fit=True)   # an open book once over the lectern's top (F12d, A8 session 26)
DESKTOP = S_('desktop', 128, 64, fit=True)    # papers once over the desk's top (F12d)
HATCH = S_('7gt002c', 64, 64, scale=4) # a framed plank hatch, 256 square
TRAPDOOR = S_('7gt003b', 64, 64, scale=4)  # iron-banded planks, 256 square: the roof trapdoor
PORTRAIT_A = S_('cwbport-1', 128, 256)   # a portrait in a dark frame on cwb stone (MM7)
PORTRAIT_B = S_('cwbport-3', 128, 256)   # a dark hooded portrait in a frame on cwb stone (MM7)

THEMES = [
    {'id': 'theme:walk', 'wall': WALKWALL, 'floor': ROCKFLOOR, 'ceiling': SKYFACE, 'door': IRONDOOR, 'reveal': SKULLFRAME,
     'notes': "The wall walks and the landing, open to the sky: D4's towers kit outside (hkm3b slate-blue stone under its skull frieze, once up the 512 parapet), dark stone underfoot (cfb1)."},
    {'id': 'theme:yard', 'wall': DARKBRICK, 'floor': FLAGS, 'ceiling': SKYFACE, 'door': SLABDOOR, 'reveal': PILLAR,
     'notes': "The courtyard, open to the sky: dark brick walls (wall), big worn flags (7tfb1)."},
    {'id': 'theme:tower', 'wall': BROWN, 'floor': FLAGS, 'ceiling': SLATE, 'door': IRONDOOR, 'reveal': PILLAR,
     'notes': "The corner towers: brown block (twb2), flags, the cone's slate soffit (xtslate)."},
    {'id': 'theme:hall', 'wall': HALLWALL, 'floor': MARBLE, 'ceiling': COFFER, 'door': SLABDOOR, 'reveal': PILLAR,
     'notes': "Castle Navan's halls (7d32): green dressed stone (ceb1sa), bordered marble flags (t3s2fl1), coffered ceilings (t5s1c2)."},
    {'id': 'theme:chapel', 'wall': REDSTONE, 'floor': MARBLE, 'ceiling': COFFER, 'door': SLABDOOR, 'reveal': PILLAR,
     'notes': "The black chapel: dark red stone (cwb1) round Navan's marble."},
    {'id': 'theme:library', 'wall': BROWN, 'floor': MARBLE, 'ceiling': COFFER, 'door': SLABDOOR, 'reveal': PILLAR,
     'notes': "The library and the study: brown block (twb2), marble, coffers."},
    {'id': 'theme:service', 'wall': DARKBRICK, 'floor': PALEFLAGS, 'ceiling': BROWN, 'door': SLABDOOR, 'reveal': PILLAR,
     'notes': "Kitchen, cellar and the back stair: dark brick (wall), pale worn flags (tfb2), block ceilings (twb2)."},
    {'id': 'theme:crypt', 'wall': DRESSED, 'floor': FLAGS, 'ceiling': ROCKFLOOR, 'door': IRONDOOR, 'reveal': SLAB,
     'notes': "Zokarr's Tomb (7d13): dressed stone under its frieze (7tws2), big flags (7tfb1), dark vaults (cfb1); the family crypt and the sleeping hall."},
    {'id': 'theme:dungeon', 'wall': BROWN, 'floor': FLAGS, 'ceiling': ROCKFLOOR, 'door': IRONDOOR, 'reveal': SLAB,
     'notes': "The dungeon (7d13): brown block (twb2), big flags (7tfb1), dark rough vaults (cfb1), iron doors (t5d1)."},
    {'id': 'theme:gallery', 'wall': PILLAR, 'floor': MARBLE, 'ceiling': COFFER, 'door': SLABDOOR, 'reveal': PILLAR,
     'notes': "The long gallery: Navan's grey block (cwb), the stone its portraits (cwbport) are painted on; marble, coffers."},
    {'id': 'theme:cistern', 'wall': dict(SLAB, scale=2), 'floor': ROCKFLOOR, 'ceiling': ROCKFLOOR, 'door': IRONDOOR, 'reveal': SLAB,
     'notes': "The black cistern (7d13): pale slab walls (twb1) over black water (7wtrtyl), dark rock."},
]

# id: (name, box, floor, ceiling, theme)
R = {
    # L1, the walls (1280)
    'landing': ("Griffin's landing", (-1280, -2176, 1280, -1056), L1, SKY, 'theme:walk'),
    'west_walk': ("West wall walk", (-2432, -1024, -1312, 1024), L1, SKY, 'theme:walk'),
    'nw_tower': ("North-west tower", (-2432, 1152, -1408, 2176), L1, L1 + 512, 'theme:tower'),
    'north_walk': ("North wall walk", (-1280, 1056, 1280, 1664), L1, SKY, 'theme:walk'),
    'keep_top': ("The bat roost", (-1280, 1792, 1280, 2944), L1, L1 + 768, 'theme:tower'),
    'ne_tower': ("North-east tower", (1408, 1152, 2432, 2176), L1, L1 + 512, 'theme:tower'),
    'east_walk': ("East wall walk", (1312, -1024, 2432, 1024), L1, SKY, 'theme:walk'),
    # L2 and L1: the stair towers (the head is the top storey)
    'sw_tower': ("South-west tower", (-2688, -2432, -1408, -1152), L2, SKY, 'theme:tower'),
    'se_tower': ("South-east tower", (1408, -2432, 2688, -1152), L2, SKY, 'theme:tower'),
    # L2, the upper floor (640)
    'south_gallery': ("Long gallery", (-1280, -2176, -128, -1152), L2, L2 + 512, 'theme:gallery'),
    'chapel2': ("The black chapel", (0, -2176, 1280, -1152), L2, L2 + 512, 'theme:chapel'),
    'library': ("Library", (1408, -1024, 2432, 2432), L2, L2 + 512, 'theme:library'),
    'keep_hall2': ("The keep's upper hall", (-2432, 1152, -128, 2432), L2, L2 + 512, 'theme:hall'),
    'study': ("The Count's study", (-1280, 2560, -384, 3328), L2, L2 + 448, 'theme:library'),
    'countess': ("The Countess's rooms", (-2432, 128, -1408, 1024), L2, L2 + 512, 'theme:hall'),
    'coffin_dorm': ("Sleeping hall", (-2688, -1024, -1408, 0), L2, L2 + 512, 'theme:crypt'),
    # L3 and L2: the grand stair hall and the back stair
    'stair_hall3': ("Grand stair hall", (0, 1152, 1280, 2432), L3, L2 + 512, 'theme:hall'),
    'back_stair': ("Servants' back stair", (-4352, 256, -2560, 1024), L3, L2 + 512, 'theme:service'),
    # L3, the ground floor (0)
    'courtyard': ("The courtyard", (-1280, -1024, 1280, 1024), L3, SKY, 'theme:yard'),
    'kitchen': ("Kitchen", (-2432, -256, -1408, 1024), L3, L3 + 512, 'theme:service'),
    'cellar': ("Cask cellar", (-2432, -1024, -1408, -384), L3, L3 + 448, 'theme:service'),
    'great_hall': ("Great hall", (-2432, 1152, -128, 2432), L3, L3 + 512, 'theme:hall'),
    'throne': ("The Count's hall", (-1280, 2560, 1280, 3840), L3, L3 + 512, 'theme:hall'),
    'crypt': ("The family crypt", (-1280, 3968, 0, 4992), L3, L3 + 512, 'theme:crypt'),
    # the dungeon stair (-640 to 0)
    'dstair': ("Dungeon stair", (-2432, 2560, -1408, 3968), DUN, L3 + 512, 'theme:dungeon'),
    # the dungeon (-640)
    'question': ("Question room", (-2432, 1408, -1408, 2432), DUN, DUN + 448, 'theme:dungeon'),
    'cells': ("The cells", (-2432, -256, -1408, 1280), DUN, DUN + 448, 'theme:dungeon'),
    'shaft': ("Ladder shaft", (-2432, -1024, -1408, -384), DUN, -128, 'theme:dungeon'),
    'queen_cell': ("The Queen's cell", (-1280, -640, -640, 256), DUN, DUN + 384, 'theme:dungeon'),
    'undercroft': ("Pillared undercroft", (-1280, 384, 1024, 3328), DUN, DUN + 384, 'theme:dungeon'),
    'cistern': ("The black cistern", (1152, 384, 2944, 3328), DUN, DUN + 512, 'theme:cistern'),
}
FLOOR_NAME = {L1: 'L1', L2: 'L2', L3: 'L3', DUN: 'dungeon'}
ORDER = sorted(R)


def outline(rid):
    x0, y0, x1, y1 = R[rid][1]
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def walls_of(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % 4]) for i in range(4)]


SIDE = {0: 's', 1: 'e', 2: 'n', 3: 'w'}


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
            nx, ny = dy, -dx
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


def opening(oid, a, b, at=None, width=256, height=384, link=None, **kw):
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b}
    if kw.get('in') != 'floor':
        gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
        if at is None:
            at = (lo + hi) / 2
        if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
            raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
        forward = (p1[ax] - p0[ax]) > 0
        along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
        d['from_wall'] = SIDE[i]
        d['to_wall'] = SIDE[j]
        if along != 0.5:
            d['along'] = along
    if link:
        d['link'] = link
    if kw.get('in') == 'floor':
        d['at'] = at
    else:
        d['width'] = width
        d['height'] = height
    d.update(kw)
    return d


DOOR_W, DOOR_H = 224, 384          # single doors (t5d1 / twb1a at 1.75 x 1.5)
DOUBLE_W, DOUBLE_H = 448, 448      # double doors: the oak pair, each leaf 224 x 448 (the picture's 1:2)
PASS_W = 384                       # open passages
PARAPET_SILL = 224                 # the inner parapet over the courtyard

# The towers' stair heads (hanging at 1280) and the stair halls' heads; the flights up to them.
HEAD_D = 384


def L_head(box, along_x, along_y):
    """An L-shaped head along two walls of a box: along_x 's'/'n' (the strip along that wall), along_y 'w'/'e'."""
    x0, y0, x1, y1 = box
    ys = (y0, y0 + HEAD_D) if along_x == 's' else (y1 - HEAD_D, y1)
    xs = (x0, x0 + HEAD_D) if along_y == 'w' else (x1 - HEAD_D, x1)
    # the union of the strip [x0, x1] x ys and the strip xs x [y0, y1], counter-clockwise
    pts = {(x0, ys[0]), (x1, ys[0]), (x1, ys[1]), (x0, ys[1]), (xs[0], y0), (xs[1], y0), (xs[1], y1), (xs[0], y1)}
    # build the outline by walking the union's boundary
    from itertools import product  # noqa: F401
    if along_x == 'n' and along_y == 'e':
        o = [[xs[0], y0], [x1, y0], [x1, y1], [x0, y1], [x0, ys[0]], [xs[0], ys[0]]]
    elif along_x == 'n' and along_y == 'w':
        o = [[x0, y0], [xs[1], y0], [xs[1], ys[0]], [x1, ys[0]], [x1, y1], [x0, y1]]
    elif along_x == 's' and along_y == 'e':
        o = [[x0, y0], [x1, y0], [x1, y1], [xs[0], y1], [xs[0], ys[1]], [x0, ys[1]]]
    else:
        o = [[x0, y0], [x1, y0], [x1, ys[1]], [xs[1], ys[1]], [xs[1], y1], [x0, y1]]
    del pts
    return o


def strip(box, side, depth=HEAD_D):
    x0, y0, x1, y1 = box
    if side == 'n':
        return [[x0, y1 - depth], [x1, y1 - depth], [x1, y1], [x0, y1]]
    if side == 's':
        return [[x0, y0], [x1, y0], [x1, y0 + depth], [x0, y0 + depth]]
    if side == 'e':
        return [[x1 - depth, y0], [x1, y0], [x1, y1], [x1 - depth, y1]]
    return [[x0, y0], [x0 + depth, y0], [x0 + depth, y1], [x0, y1]]


def head(pid, outline_, floor, top, surface, notes):
    return {'id': pid, 'rise': 32, 'base': top - floor - 32, 'outline': outline_, 'surface': dict(surface),
            'top_surface': dict(FLAGS), 'bottom_surface': dict(BROWN), 'notes': notes}


def plat(pid, at, size, rise, surface, top=None, notes=None, **kw):
    d = {'id': pid, 'at': at, 'size': size, 'rise': rise, 'surface': surface}
    if pid is None:
        del d['id']
    if top:
        d['top_surface'] = top
    d.update(kw)
    if notes:
        d['notes'] = notes
    return d


SW_BOX = R['sw_tower'][1]
SE_BOX = R['se_tower'][1]
SH_BOX = R['stair_hall3'][1]
BS_BOX = R['back_stair'][1]
DS_BOX = R['dstair'][1]
YARD_HEAD = [[-1280, -1024], [-640, -1024], [-640, -640], [-1280, -640]]
GATE_X = -960
STAIR_W = 320

OPENINGS = [
    # L1: the ring of walks and towers
    opening('open:landing_sw', 'sw_tower', 'landing', at=-1856, width=PASS_W, height=384, link='link:landing_sw'),
    opening('open:sw_west', 'sw_tower', 'west_walk', at=-1920, width=PASS_W, height=384, link='link:sw_west'),
    opening('open:west_nw', 'west_walk', 'nw_tower', at=-1920, width=PASS_W, height=384, link='link:west_nw'),
    opening('open:nw_north', 'nw_tower', 'north_walk', at=1408, width=PASS_W, height=384, link='link:nw_north'),
    opening('open:north_keep', 'north_walk', 'keep_top', at=0, width=DOOR_W, height=DOOR_H, link='link:north_keep'),
    opening('open:north_ne', 'north_walk', 'ne_tower', at=1408, width=PASS_W, height=384, link='link:north_ne'),
    opening('open:ne_east', 'ne_tower', 'east_walk', at=1920, width=PASS_W, height=384, link='link:ne_east'),
    opening('open:east_se', 'se_tower', 'east_walk', at=1920, width=PASS_W, height=384, link='link:east_se'),
    opening('open:se_landing', 'se_tower', 'landing', at=-1856, width=PASS_W, height=384, link='link:se_landing'),
    # L1 over the courtyard: the yard gate at the courtyard stair's head, and the inner parapets
    opening('open:yard_gate', 'courtyard', 'landing', at=GATE_X, width=256, height=384, link='link:yard_stair',
            notes="The yard gate: the courtyard stair's head (1280) onto the landing; its bar on the stair's side."),
    opening('open:landing_parapet', 'landing', 'courtyard', at=448, width=1536, height='full', sill=PARAPET_SILL,
            notes="The landing's inner parapet over the courtyard."),
    opening('open:west_parapet', 'west_walk', 'courtyard', at=0, width=1536, height='full', sill=PARAPET_SILL,
            notes="The west walk's inner parapet over the courtyard."),
    opening('open:north_parapet', 'north_walk', 'courtyard', at=0, width=2048, height='full', sill=PARAPET_SILL,
            notes="The north walk's inner parapet over the courtyard."),
    opening('open:east_parapet', 'east_walk', 'courtyard', at=0, width=1536, height='full', sill=PARAPET_SILL,
            notes="The east walk's inner parapet over the courtyard."),
    # L2: the ring of the upper floor
    opening('open:sw2_gallery', 'sw_tower', 'south_gallery', at=-1856, width=PASS_W, height=384, link='link:sw2_gallery'),
    opening('open:gallery_chapel', 'south_gallery', 'chapel2', at=-1664, width=DOUBLE_W, height=DOUBLE_H,
            link='link:gallery_chapel'),
    opening('open:chapel_se2', 'chapel2', 'se_tower', at=-1856, width=PASS_W, height=384, link='link:chapel_se2'),
    opening('open:se2_library', 'se_tower', 'library', at=1920, width=PASS_W, height=384, link='link:se2_library'),
    opening('open:library_head', 'library', 'stair_hall3', at=2240, width=320, height=384, link='link:library_keep'),
    opening('open:keep_head', 'keep_hall2', 'stair_hall3', at=2240, width=320, height=384, link='link:grand_stair'),
    opening('open:keep_study', 'keep_hall2', 'study', at=-832, width=DOOR_W, height=DOOR_H, link='link:keep_study'),
    opening('open:keep_countess', 'keep_hall2', 'countess', at=-1920, width=PASS_W, height=384, link='link:keep_countess'),
    opening('open:countess_dorm', 'countess', 'coffin_dorm', at=-1920, width=DOOR_W, height=DOOR_H,
            link='link:countess_dorm'),
    opening('open:dorm_sw2', 'coffin_dorm', 'sw_tower', at=-1920, width=PASS_W, height=384, link='link:dorm_sw2'),
    opening('open:countess_back', 'countess', 'back_stair', at=832, width=256, height=384, link='link:back_stair'),
    # L3
    opening('open:back_kitchen', 'back_stair', 'kitchen', at=448, width=256, height=384, link='link:back_stair'),
    opening('open:cellar_kitchen', 'cellar', 'kitchen', at=-1920, width=DOOR_W, height=DOOR_H, link='link:cellar_kitchen'),
    opening('open:kitchen_yard', 'kitchen', 'courtyard', at=384, width=PASS_W, height=384, link='link:kitchen_yard'),
    opening('open:yard_stairhall', 'courtyard', 'stair_hall3', at=640, width=DOUBLE_W, height=DOUBLE_H,
            link='link:yard_stairhall'),
    opening('open:yard_great', 'courtyard', 'great_hall', at=-704, width=DOUBLE_W, height=DOUBLE_H, link='link:yard_great'),
    opening('open:stairhall_throne', 'stair_hall3', 'throne', at=320, width=DOUBLE_W, height=DOUBLE_H,
            link='link:stairhall_throne'),
    opening('open:great_throne', 'great_hall', 'throne', at=-704, width=448, height=448, link='link:great_throne',
            notes="The screens passage."),
    opening('open:throne_crypt', 'throne', 'crypt', at=-896, width=DOOR_W, height=DOOR_H, link='link:throne_crypt'),
    opening('open:throne_dstair', 'throne', 'dstair', at=2752, width=256, height=384, link='link:dstair_down',
            notes="Behind the dais: the black iron bar onto the dungeon stair's head."),
    # the dungeon
    opening('open:dstair_question', 'dstair', 'question', at=-2112, width=DOOR_W, height=DOOR_H, link='link:foot_question'),
    opening('open:dstair_undercroft', 'dstair', 'undercroft', at=2752, width=320, height=384, link='link:foot_undercroft'),
    opening('open:question_cells', 'question', 'cells', at=-1920, width=PASS_W, height=384, link='link:question_cells'),
    opening('open:cells_shaft', 'cells', 'shaft', at=-1920, width=320, height=384, link='link:cells_shaft'),
    opening('open:cells_queen', 'cells', 'queen_cell', at=0, width=224, height=320, link='link:cells_queen',
            notes="The cell's grille door, standing open."),
    opening('open:undercroft_cells', 'undercroft', 'cells', at=832, width=320, height=320, link='link:undercroft_cells'),
    opening('open:undercroft_cistern', 'undercroft', 'cistern', at=1856, width=PASS_W, height=320,
            link='link:undercroft_cistern'),
]

# The cellar's trapdoor over the ladder shaft (corners on the 256 grid, so the hatch picture lies once).
HATCH_AT = [-1664, -768]
HATCH_HOLE = [224, 224]
OPENINGS.append(opening('open:hatch', 'cellar', 'shaft', link='link:hatch', **{'in': 'floor'}, at=HATCH_AT,
                        size=HATCH_HOLE, notes="The hole under the cellar's trapdoor: the shaft's ladder comes up through it."))

# The undercroft's twelve pillars: four rows of three (east-west), aisles about 384 wide.
UNDERCROFT_PILLARS = [(x, y) for x in (-640, 0, 512) for y in (1024, 1664, 2304, 2880)]
# The courtyard's dry fountain and the gargoyles' plinths.
FOUNTAIN = (128, 128)
PLINTHS = [(-384, 512), (640, 512), (128, -320)]
# The cistern's pool (sunken 96, banked) inside a ledge 256 wide on three sides; the entrance ledge west.
POOL = [[1664, 640], [2688, 640], [2688, 3072], [1664, 3072]]
POOL_DEPTH = 96

# Coffins: (key, room, centre, along-axis 'x' or 'y', notes); each 160 wide and 448 long, lids ajar.
COFFIN_LEN, COFFIN_W, COFFIN_H = 416, 160, 96
LANDING_COFFINS = [(f'landing_{i}', 'landing', (x, -1904), 'y') for i, x in enumerate((-1088, -832, -576, 576, 832, 1088), 1)]
NE_COFFINS = [('ne_1', 'ne_tower', (2208, 1536), 'x'), ('ne_2', 'ne_tower', (2208, 1856), 'x')]
SE_COFFIN = [('se_loot', 'se_tower', (2432, -1312), 'x')]
# The sleeping hall's six coffins in wall niches: west wall three, east wall three (heads to the wall).
DORM_COFFINS = [(f'dorm_{s}{i}', 'coffin_dorm', ((-2464 if s == 'w' else -1632), y), 'x')
                for s in ('w', 'e') for i, y in enumerate((-832, -512, -192), 1)]
# The crypt's four named coffins on biers, heads north (aaze0047:6-9).
CRYPT_COFFINS = [('crypt_dutchess', 'crypt', (-1088, 4608), 'y'), ('crypt_countess', 'crypt', (-768, 4608), 'y'),
                 ('crypt_count', 'crypt', (-448, 4608), 'y'), ('crypt_lady', 'crypt', (-192, 4608), 'y')]
COFFINS = LANDING_COFFINS + NE_COFFINS + SE_COFFIN + DORM_COFFINS + CRYPT_COFFINS


def coffin_outline(c, axis, head_low=True):
    """A coffin's six-sided outline: the head end (narrow), the shoulders (widest), the foot (narrower)."""
    L = COFFIN_LEN // 2
    uv = [(-L, -56), (-L + 128, -80), (L, -48), (L, 48), (-L + 128, 80), (-L, 56)]
    if not head_low:
        uv = [(-u, -v) for u, v in uv]
    pts = [[c[0] + v, c[1] + u] if axis == 'y' else [c[0] + u, c[1] + v] for u, v in uv]
    area = sum(pts[i][0] * pts[(i + 1) % 6][1] - pts[(i + 1) % 6][0] * pts[i][1] for i in range(6))
    return pts if area > 0 else pts[::-1]


def coffin_plat(key, room, c, axis):
    # D-89 identity (A8 s27): every coffin is a lidded six-sided stone coffin on a bier (were plank boxes outside the
    # crypt); the south-east tower's loot coffin stands on the tower's top storey without one.
    stone = True
    base = 64
    head_low = not (key.startswith('dorm_e') or key in ('ne_1', 'ne_2', 'se_loot'))
    if key.startswith('crypt'):
        head_low = False
    d = {'id': f'platform:coffin_{key}', 'outline': coffin_outline(c, axis, head_low), 'rise': COFFIN_H,
         'surface': dict(SLAB if stone else COFFINWOOD), 'top_surface': dict(SLAB if stone else LID),
         'notes': "A stone coffin on its bier." if key != 'se_loot' else "A stone coffin, its lid ajar."}
    d['base'] = base
    if key == 'se_loot':
        d['base'] = L1 - L2
    return d


def biers(room='crypt'):
    out = []
    for k, rm, c, ax in COFFINS:
        if rm != room or k == 'se_loot':
            continue
        pad = 64 if rm == 'crypt' else 24      # outside the crypt the coffins stand close to a wall
        size = [COFFIN_W + pad, COFFIN_LEN + pad] if ax == 'y' else [COFFIN_LEN + pad, COFFIN_W + pad]
        out.append(plat(None, [c[0], c[1]], size, 64, dict(PILLAR), dict(PILLAR), "The bier."))
    return out


def coffins_in(room):
    return [coffin_plat(*c) for c in COFFINS if c[1] == room]


EXTRA = {
    'landing': {
        'platforms': coffins_in('landing') + [
            plat('platform:perch', [256, -1600], [256, 256], 24, dict(SLAB), dict(PALEFLAGS),
                 "The griffin's perch: a low block by the parapet where Ambrose's griffin waits (D-42 Q1)."),
        ],
        'notes': "The south wall walk's middle stretch, open to the sky: coffins in a row against the outer parapet, lids ajar; the clear walk down the middle; the inner parapet over the courtyard and the yard gate at the courtyard stair's head; the griffin's perch; the towers west and east.",
    },
    'sw_tower': {
        'platforms': [head('platform:sw_head', L_head(SW_BOX, 'n', 'e'), L2, L1, BROWN,
                           "The tower's top storey (1280): a floor along its north and east walls over the stair.")],
        'flights': [{'from': [-2496, -2240], 'to': [-1792, -2240], 'to_height': L1, 'width': STAIR_W, 'steps': 20,
                     'open_below': 32, 'notes': "Twenty steps of 32 up the south wall, rising east to the top storey."}],
        'notes': "The south-west tower, two storeys under its cone: its foot on L2 (the long gallery east, the sleeping hall north), the stair up the south wall to its top storey on L1 (the landing east, the west walk north).",
    },
    'se_tower': {
        'platforms': [head('platform:se_head', L_head(SE_BOX, 'n', 'w'), L2, L1, BROWN,
                           "The tower's top storey (1280): a floor along its north and west walls over the stair.")]
        + coffins_in('se_tower'),
        'flights': [{'from': [2496, -2240], 'to': [1792, -2240], 'to_height': L1, 'width': STAIR_W, 'steps': 20,
                     'open_below': 32, 'notes': "Twenty steps of 32 up the south wall, rising west to the top storey."}],
        'notes': "The south-east tower, two storeys under its cone: its foot on L2 (the chapel west, the library north), the stair up the south wall to its top storey on L1 (the landing west, the east walk north).",
    },
    'stair_hall3': {
        'platforms': [head('platform:grand_head', strip(SH_BOX, 'n'), L3, L2, HALLWALL,
                           "The grand stair's head gallery (640) across the hall's north end: the keep's upper hall west, the library east.")],
        'flights': [{'from': [640, 1344], 'to': [640, 2048], 'to_height': L2, 'width': 384, 'steps': 20, 'open_below': 32,
                     'sides': {'height': 48, 'thickness': 16, 'surface': dict(PILLAR)},
                     'notes': "The grand stair: twenty steps of 32 from the keep door up north to the head gallery."}],
        'notes': "The keep's ground floor, two storeys: the keep's double door from the courtyard, the grand stair up to its head gallery (L2), the Count's hall's double doors north under the gallery.",
    },
    'back_stair': {
        'platforms': [head('platform:back_head', strip(BS_BOX, 'e'), L3, L2, DARKBRICK,
                           "The back stair's head (640) along its east wall: the Countess's rooms through it.")],
        'flights': [{'from': [-4224, 832], 'to': [-2944, 832], 'to_height': L2, 'width': STAIR_W, 'steps': 20,
                     'open_below': 32, 'notes': "The servants' stair, twenty steps up east along the north wall."}],
        'notes': "The servants' back stair, two storeys, behind the kitchen and the Countess's rooms: in from the kitchen under the head, west along the south side to the foot, up the north wall to the head.",
    },
    'dstair': {
        'platforms': [head('platform:dstair_head', strip(DS_BOX, 's'), DUN, L3, BROWN,
                           "The dungeon stair's head (0) behind the bar: the Count's hall east.")],
        'flights': [{'from': [-1600, 3840], 'to': [-1600, 2944], 'to_height': L3, 'width': STAIR_W, 'steps': 20,
                     'open_below': 32, 'notes': "Twenty steps of 32 down north into the crag from the head."}],
        'notes': "The stair down into the crag, two storeys: the head behind the black iron bar (the Count's hall); down north along the east wall to the gaolers' post at the foot; under the head the doors into the question room and the undercroft.",
    },
    'courtyard': {
        'platforms': [head('platform:yard_head', YARD_HEAD, L3, L1, DARKBRICK,
                           "The courtyard stair's head (1280) in the south-west corner, before the yard gate."),
                      plat('platform:fountain', list(FOUNTAIN), [512, 512], 64, dict(SLAB), dict(FLAGS),
                           "The dry fountain's basin."),
                      plat(None, list(FOUNTAIN), [128, 128], 192, dict(SLAB), dict(SLAB), "The fountain's dry spout.",
                           base=64)]
        + [plat(None, list(p), [192, 192], 96, dict(PILLAR), dict(PILLAR), "A gargoyle's plinth.") for p in PLINTHS],
        'flights': [{'from': [1152, -832], 'to': [-640, -832], 'to_height': L1, 'width': STAIR_W, 'steps': 40,
                     'sides': {'height': 48, 'thickness': 16, 'surface': dict(DARKBRICK)},
                     'notes': "The courtyard stair: forty steps of 32 up the south wall, rising west to its head."}],
        'notes': "The castle's courtyard, open to the sky: the dry fountain with the gargoyles' plinths, the courtyard stair up the south wall to the yard gate, the kitchen west, the great hall's and the keep's double doors north.",
    },
    'undercroft': {
        'pillars': [{'outline': [[x - 96, y - 96], [x + 96, y - 96], [x + 96, y + 96], [x - 96, y + 96]],
                     'surface': dict(PILLAR)} for x, y in UNDERCROFT_PILLARS],
        'notes': "The source's dungeon hall: twelve square pillars in four rows of three under a low vault.",
    },
    'cistern': {
        'levels': [{'id': 'level:pool', 'outline': POOL, 'floor': DUN - POOL_DEPTH, 'bank': 128, 'surface': dict(WATER),
                    'notes': "The black water, banked so a party can wade out."}],
        'notes': "The castle's rain cistern: black water in the middle, a ledge 256 wide round it, the entrance ledge west; the chest on the far ledge.",
    },
    'crypt': {
        'platforms': biers() + coffins_in('crypt'),
        'notes': "The Blackfangs' family crypt: four stone coffins on biers, heads north; braziers in the corners.",
    },
    'coffin_dorm': {
        'platforms': coffins_in('coffin_dorm'),
        'notes': "The household's coffins in two rows against the walls (west and east), six in all.",
    },
    'ne_tower': {'platforms': coffins_in('ne_tower'), 'notes': "A shuttered top storey; two coffins by the east wall."},
}


def cell_bars(at, size, notes):
    """A static run of cell bars, 256 high (XD-04's see-through bars, D-22.1)."""
    return {'at': at, 'size': size, 'rise': 256, 'surface': dict(GRILLE), 'end_surface': dict(IRON, fit=False),
            'top_surface': dict(IRON, scale=3), 'notes': notes}


THRONE_AT = (-1152, 3264)
DAIS = plat('platform:dais', [-1024, 3264], [384, 640], 32, dict(PILLAR), dict(REDSTONE), "The dais at the hall's west end: dark red stone (D-89, was marble).")


def panel(pid, at, length, bottom, height, surface, notes=None, offset=None):
    d = {'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    if pid:
        d['id'] = pid
    if offset is None:
        d['at'] = 'centre'
    else:
        d['offset'] = offset
    if notes:
        d['notes'] = notes
    return d


FURNISH = {
    'nw_tower': {'walls': [{'wall': 'w', 'panels': [panel('panel:gong', None, 192, 96, 192, dict(GONG, fit=True),
                                                         "The bronze gong on the tower's west wall (aaze0045:6).")]}]},
    'keep_top': {'platforms': [plat('platform:roof_trapdoor', [128, 2432], [256, 256], 16, dict(TRAPDOOR), dict(TRAPDOOR),
                                    "The roof trapdoor, bolted from above (D-42 (7)), flush with the ceiling.", base=752,
                                    bottom_surface=dict(TRAPDOOR))]},
    'south_gallery': {'walls': [{'wall': 's', 'panels': [
        panel('panel:portraits', None, 192, 96, 384, dict(PORTRAIT_A, fit=True), "A Blackfang (a portrait: the find).",
              offset=96),
        panel(None, None, 192, 96, 384, dict(PORTRAIT_B, fit=True), "A Blackfang.", offset=384),
        panel(None, None, 192, 96, 384, dict(PORTRAIT_A, fit=True), "A Blackfang.", offset=672),
        panel(None, None, 192, 96, 384, dict(PORTRAIT_B, fit=True), "A Blackfang.", offset=896)]}]},
    'chapel2': {'platforms': [plat('platform:altar', [640, -2048], [512, 160], 96, dict(REDSTONE, fit=False),
                                   dict(SLAB), "The altar against the south wall, its cloth embroidered with a bat.")]},
    'library': {'platforms': [plat(None, [2368, y], [96, 512], 256, dict(BOOKS), dict(BROWN), "A bookcase.",
                                   end_surface=dict(BROWN, fit=False)) for y in (-640, 0, 640, 1280)]
                + [plat('platform:lectern', [1792, 640], [96, 96], 112, dict(TABLE), dict(BOOKTOP),
                        "A lectern with The Blackfang Lineage.", end_surface=dict(TABLE, fit=False))]},
    'study': {'platforms': [plat('platform:desk', [-832, 3072], [384, 160], 80, dict(TABLE), dict(DESKTOP),
                                 "The Count's desk and his ledger.", end_surface=dict(TABLE, fit=False))]},
    'countess': {'platforms': [plat('platform:bed', [-2272, 768], [256, 384], 32, dict(BEDSIDE), dict(BEDTOP),
                                    "The Countess's bed against the west wall.", end_surface=dict(BEDSIDE, fit=False)),
                               plat('platform:dressing_table', [-1600, 960], [256, 96], 96, dict(TABLE), dict(TABLE),
                                    "Her dressing table, and no mirror.", end_surface=dict(TABLE, fit=False))]},
    'kitchen': {'platforms': [plat('platform:hearth', [-1920, 960], [384, 96], 48, dict(PALEFLAGS), dict(PALEFLAGS),
                                   "The cold hearth on the north wall (a set piece)."),
                              plat('platform:kitchen_table', [-1920, 704], [384, 192], 80, dict(TABLE), dict(TABLE),
                                   "The kitchen table.", end_surface=dict(TABLE, fit=False))]},
    'great_hall': {'platforms': [plat('platform:long_table', [-1728, 1792], [1024, 256], 80, dict(TABLE), dict(TABLE),
                                      "The long table, beside the line between the doors.",
                                      end_surface=dict(TABLE, fit=False))],
                   'walls': [{'wall': 'w', 'panels': [panel('panel:crest_great', None, 256, 160, 256, dict(CREST, fit=True),
                                                            "Blackfang's arms (xbfcrest) on the end wall.")]}]},
    'throne': {'platforms': [DAIS,
                             plat('platform:throne', [THRONE_AT[0], THRONE_AT[1]], [128, 192], 96, dict(PILLAR),
                                  dict(PILLAR), "The black throne's seat.", base=32),
                             plat(None, [THRONE_AT[0] - 80, THRONE_AT[1]], [32, 192], 288, dict(PILLAR), dict(PILLAR),
                                  "The throne's back.", base=32)],
               'walls': [{'wall': 'w', 'panels': [panel('panel:crest_throne', None, 256, 224, 256, dict(CREST, fit=True),
                                                        "Blackfang's arms over the throne.",
                                                        offset=3840 - THRONE_AT[1] - 128)]}]},
    'question': {'platforms': [plat(None, [-2368, 1792], [64, 384], 192, dict(TABLE), dict(TABLE), "A rack.",
                                    end_surface=dict(TABLE, fit=False)),
                               plat(None, [-1472, 1920], [64, 384], 192, dict(TABLE), dict(TABLE), "A rack.",
                                    end_surface=dict(TABLE, fit=False))]},
    'cells': {'platforms': [cell_bars([-2112, 544], [8, 1216], "The cells' front: iron bars from the corridor's south end to its north end.")]
              + [cell_bars([-2276, y], [312, 8], "Bars between two cells.") for y in (384, 768)]},
    'queen_cell': {'platforms': [plat('platform:queen_bench', [-736, -192], [96, 384], 64, dict(SLAB), dict(SLAB),
                                      "A stone bench in the Queen's cell.", end_surface=dict(SLAB, fit=False))]},
}


def merge_extra():
    for rid, extra in FURNISH.items():
        e = EXTRA.setdefault(rid, {})
        for k, v in extra.items():
            e[k] = e.get(k, []) + v


# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s27 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-14: "a manor"): the halls in Navan's grey
# block over a dark base course and dark flags (were green stone and pale yellow marble), the towers in dark brick
# (were tan block), pointed ribs across every hall's ceiling, the crypt under a pointed vault and the two corner
# towers' top storeys under pointed cones, the coffins stone on biers.
DARKFLAGS = S_('7tfb11', 128, 128)                  # dark flags (MM7)
TOWERSTONE = DARKBRICK                              # dark brick inside the towers (hkm3b is a footing panel)
BASE = [{'height': 48, 'surface': dict(ROCKFLOOR)}]   # a dark base course under the halls' walls
for _t in THEMES:
    if _t['floor'] == MARBLE:
        _t['floor'] = DARKFLAGS
    if _t['id'] == 'theme:hall':
        _t['wall'] = PILLAR
        _t['notes'] = "The castle's halls: Navan's grey block (cwb) over a dark base course (cfb1), dark flags (7tfb11), coffered ceilings under pointed ribs (t5s1c2)."
    if _t['id'] == 'theme:tower':
        _t['wall'] = TOWERSTONE
        _t['notes'] = "The corner towers: dark brick (wall), flags, the cone's slate soffit (xtslate)."
    if _t['id'] in ('theme:hall', 'theme:chapel', 'theme:library', 'theme:gallery'):
        _t['bands'] = [dict(b) for b in BASE]
        if _t['id'] != 'theme:hall':
            _t['notes'] = _t['notes'].replace('marble', 'dark flags (7tfb11)').replace("Navan's dark flags (7tfb11)", 'dark flags (7tfb11)')

HANGING = {'keep_hall2': [-1792, -768], 'great_hall': [-1792, -768], 'throne': [0]}   # chandeliers (dress.py PROPS)


def ribs(rid, spacing=512, rise=176, width=48):
    """Pointed ribs across the room's short span every `spacing`: two raking halves meeting under the ceiling's middle,
    each 48 deep, cut off under the ceiling; none within 256 of a chandelier."""
    x0, y0, x1, y1 = R[rid][1]
    ce = R[rid][3]
    along_x = (x1 - x0) >= (y1 - y0)
    lo, hi = (x0, x1) if along_x else (y0, y1)
    out = []
    p = lo + spacing // 2 + 128
    while p <= hi - spacing // 2 - 64:
        if all(abs(p - h) >= 256 for h in HANGING.get(rid, [])):
            if along_x:
                halves = [([p, y0], [p, (y0 + y1) // 2]), ([p, y1], [p, (y0 + y1) // 2])]
            else:
                halves = [([x0, p], [(x0 + x1) // 2, p]), ([x1, p], [(x0 + x1) // 2, p])]
            for a, b in halves:
                out.append({'path': [a, b], 'width': width, 'bottom': ce - rise, 'bottom_end': ce - 40, 'depth': 48,
                            'surface': dict(PILLAR)})
        p += spacing
    return out


for _r in ('great_hall', 'keep_hall2', 'throne', 'chapel2', 'south_gallery', 'countess', 'coffin_dorm', 'library',
           'study'):
    EXTRA.setdefault(_r, {})['beams'] = EXTRA.get(_r, {}).get('beams', []) + ribs(_r)
# the crypt: a pointed vault along its length (nothing stands above it)
_cx0, _cy0, _cx1, _cy1 = R['crypt'][1]
EXTRA['crypt']['ceiling_points'] = [[(_cx0 + _cx1) // 2, _cy0, L3 + 832], [(_cx0 + _cx1) // 2, _cy1, L3 + 832]]
# the corner towers' top storeys: a pointed cone (their roofs are open above)
for _r in ('nw_tower', 'ne_tower'):
    _x0, _y0, _x1, _y1 = R[_r][1]
    EXTRA.setdefault(_r, {})['ceiling_points'] = [[(_x0 + _x1) // 2, (_y0 + _y1) // 2, R[_r][3] + 384]]
EXTRA['ne_tower']['platforms'] = biers('ne_tower') + EXTRA['ne_tower']['platforms']
EXTRA['landing']['platforms'] = biers('landing') + EXTRA['landing']['platforms']
EXTRA['coffin_dorm']['platforms'] = biers('coffin_dorm') + EXTRA['coffin_dorm'].get('platforms', [])


def room_doc(rid):
    name, b, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
    d.update(EXTRA.get(rid, {}))
    return d


def extent(rid):
    x0, y0, x1, y1 = R[rid][1]
    return [x1 - x0, y1 - y0], [(x0 + x1) // 2, (y0 + y1) // 2]


def area(rid):
    x0, y0, x1, y1 = R[rid][1]
    return (x1 - x0) * (y1 - y0)


merge_extra()

if __name__ == '__main__':
    tot = 0
    for r in ORDER:
        a = area(r)
        tot += a
        print(f'{r:16s} {a / 1e6:6.2f}')
    print('total', tot / 1e6, 'rooms', len(ORDER))
