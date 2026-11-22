#!/usr/bin/env python3
"""DD-09 Temple of Bark: the geometry (rooms, openings) shared by L2, L3 and L4.

Four floors in one frame (x east, y north, heights from the arrival floor at the trunk door):
- the trunk base at 0: the trunk door (arrival, the exit to D2), the Hall of the Trunk, the orc barracks east of it,
  the Chapel of Sap north, the guardroom between them (the orcs' back stair leaves it east);
- the roots at -512, west: the root stair from the hall down to the root cellar, the west and east root alcoves, the
  sap store south, the pens west of the store;
- the upper trunk at 640, east: the ring stair from the hall winds south and east up to the ring landing; Shaalth's
  hall, the cell row north of it (the back stair's top), the shaman's tea room, the Chapel of Ascension and the
  Disciples' vault in a row east;
- the limbs at 1280, south-east: the limb climb from the ring landing to the limb stair, the limb walk, the fruit
  rooms and the crown east, Barkman's hollow and the treasure room south.
Rooms are chamfered rectangles whose axis-aligned sides carry the openings; walls between rooms are 128 thick.
"""

B0, R1, U1, L2 = 0, -512, 640, 1280


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM7 The Hall under the Hill (7d22) with D2's bark (D-23: xdbark, the treehouse trunks' bark).
BARK = S_('xdbark', 128, 256)            # the trunk's and the limbs' walls (D2's bark)
HEART = S_('7t1books1', 128, 128)       # plank floors: the heartwood halls inside the trunk
EARTH = S_('c2b', 256, 256)             # the roots' earth walls
EARTH2 = S_('c2b1', 256, 256)           # the pens' darker earth
SAPWALL = S_('c2bb', 256, 256)          # earth veined with amber sap: the sap store; the alcoves' mouths
SOIL = S_('cfb1', 128, 128)             # dark soil floors of the roots
DIRTCEIL = S_('7dirttyl', 128, 128)     # earthen ceilings
DIRT = S_('7dirt1', 128, 128)           # the orcs' trodden floors
GREEN = S_('ceb1sa', 128, 256)          # the old temple's green stone (the chapels)
GREEN_IVY = S_('ceb2sa', 128, 256)      # green stone overgrown (Shaalth's hall, the sanctuary)
GREEN_SMALL = S_('ceb3s', 128, 256)     # small green brick (the priests' cells, now barracks)
GREEN_END = S_('ceb1el', 128, 256)      # a pilaster strip (corners of the chapels)
FLAGS = S_('7tfb1', 128, 128)           # pale flags (the Chapel of Sap)
MOSSFLAGS = S_('7tfb10', 128, 128)      # mossy green flags (the sanctuary, the Chapel of Ascension)
DARKFLAGS = S_('7tfb11', 128, 128)      # dark flags (the tea room, the cells)
ROUGH = S_('t2bs', 128, 256)            # rough grey stone (the cells)
GRASS = S_('7grastyl', 128, 128)        # the crown's grass and its canopy of leaves
SHELVES = S_('7t1books', 128, 256)      # the priests' bookcases
CABINET = S_('7t1cab', 128, 256)        # the shaman's cabinet
DOOR = S_('beemdorc', 128, 256)         # plank doors
VAULTDOOR = S_('ceb1dl', 128, 256)      # the Disciples' arched door under ivy: its left wing
VAULTDOOR_R = S_('ceb1dr', 128, 256)    # and its right wing (a hinged pair, session 6)
DIAL = S_('7gt002c', 64, 64)            # the chapel's three iron dials
CRATE = S_('7gt002b', 64, 64)           # crates and the ledger's box
BOOK_TOP = S_('xnpbook', 128, 128, fit=True)  # F12d: an open book over a lectern/stump/crate top (the picture's own size, fit)
# texture fit (merge point 16): xngrille is a picture meant once (XD-02's hoist gate) and showed 3 times across each
# 384-wide side of bars; XD-04's see-through xwcage is the bars band that repeats across (D-22.1: reuse first for any
# bars or cages). The cage tops' xwiron (its edges do not meet up and down) is laid at a third of its density (scale 3, a level face ignores fit): once over
# the 384 tops.
GRILLE = S_('xwcage', 128, 256)         # cage bars
IRON = S_('xwiron', 128, 128)           # cage tops
CRYSTAL = {'texture': '7wtrtyl', 'liquid': 'water'}     # the Crystal Water
DARKWATER = {'texture': 'tartyl', 'liquid': 'water'}    # the Dark Water
SAP = {'texture': 'xjuiceorg', 'liquid': 'water'}       # the vats of sap

THEMES = [
    {'id': 'theme:trunk', 'wall': BARK, 'floor': HEART, 'ceiling': BARK, 'door': DOOR,
     'notes': "Inside the great tree: D2's bark (xdbark, D-23) on walls and vault, a heartwood floor of planks (7t1books1)."},
    {'id': 'theme:barracks', 'wall': GREEN_SMALL, 'floor': DIRT, 'ceiling': DIRTCEIL, 'door': DOOR,
     'notes': "The priests' cells made orc barracks: 7d22's small green brick (ceb3s) over trodden dirt (7dirt1)."},
    {'id': 'theme:chapel', 'wall': GREEN, 'floor': FLAGS, 'ceiling': MOSSFLAGS, 'door': DOOR, 'ends': {'length': 64, 'surface': GREEN_END},
     'notes': "The old temple's chapels: 7d22's green stone (ceb1sa) with pilaster corners (ceb1el), pale flags (7tfb1)."},
    {'id': 'theme:sanctuary', 'wall': GREEN_IVY, 'floor': MOSSFLAGS, 'ceiling': BARK, 'door': DOOR, 'ends': {'length': 64, 'surface': GREEN_END},
     'notes': "The sanctuary made Shaalth's hall, and the Chapel of Ascension: green stone under ivy (ceb2sa), mossy flags (7tfb10), the bark overhead."},
    {'id': 'theme:orc', 'wall': ROUGH, 'floor': DARKFLAGS, 'ceiling': DIRTCEIL, 'door': DOOR,
     'notes': "The tea room and the cell row: rough grey stone (t2bs) over dark flags (7tfb11)."},
    {'id': 'theme:roots', 'wall': EARTH, 'floor': SOIL, 'ceiling': DIRTCEIL, 'door': DOOR,
     'notes': "Under the trunk: 7d22's root earth (c2b), dark soil (cfb1), an earthen roof."},
    {'id': 'theme:pens', 'wall': EARTH2, 'floor': DIRT, 'ceiling': DIRTCEIL, 'door': DOOR,
     'notes': "The orcs' pens: darker earth (c2b1) over trodden dirt."},
    {'id': 'theme:sap', 'wall': SAPWALL, 'floor': SOIL, 'ceiling': DIRTCEIL, 'door': DOOR,
     'notes': "The sap store: earth veined with amber sap (c2bb)."},
    {'id': 'theme:limb', 'wall': BARK, 'floor': HEART, 'ceiling': BARK, 'door': DOOR,
     'notes': "Hollowed along the great limbs: bark (xdbark) and heartwood planks."},
    {'id': 'theme:crown', 'wall': BARK, 'floor': GRASS, 'ceiling': GRASS, 'door': DOOR,
     'notes': "The crown: bark walls, grass underfoot and a canopy of leaves overhead (7grastyl)."},
]


def cave(x0, y0, x1, y1, c=256):
    """A chamfered rectangle, counter-clockwise from the south-west; c is one chamfer or (sw, se, ne, nw)."""
    sw, se, ne, nw = (c, c, c, c) if isinstance(c, int) else c
    pts = []
    for p in ([x0 + sw, y0], [x1 - se, y0], [x1, y0 + se], [x1, y1 - ne], [x1 - ne, y1], [x0 + nw, y1],
              [x0, y1 - nw], [x0, y0 + sw]):
        if not pts or pts[-1] != p:
            pts.append(p)
    if pts[0] == pts[-1]:
        pts.pop()
    return pts


RUFF = {'step': 192, 'depth': 40}

# id: (name, box, floor, ceiling, theme)
R = {
    # the trunk base (0)
    'trunk_door': ("Trunk door", (-320, -2304, 320, -1536), B0, 448, 'theme:trunk'),
    'first_hall': ("Hall of the Trunk", (-1280, -1408, 1280, 1152), B0, 896, 'theme:trunk'),
    'barracks': ("Orc barracks", (1408, -1152, 3328, 640), B0, 512, 'theme:barracks'),
    'guardroom': ("Guardroom", (1408, 768, 3328, 2944), B0, 512, 'theme:barracks'),
    'chapel': ("Chapel of Sap", (-896, 1280, 1280, 2944), B0, 640, 'theme:chapel'),
    # the upper trunk (640)
    'ring1': ("Ring landing", (4480, -1408, 5504, -384), U1, U1 + 704, 'theme:trunk'),
    'shaalth': ("Shaalth's hall", (5632, -1408, 8704, 1536), U1, U1 + 896, 'theme:sanctuary'),
    'cells': ("Cell row", (5632, 1664, 7424, 3072), U1, U1 + 448, 'theme:orc'),
    'shaman': ("The shaman's tea room", (8832, -768, 10368, 768), U1, U1 + 448, 'theme:orc'),
    'ascension': ("Chapel of Ascension", (10496, -1152, 12288, 1152), U1, U1 + 640, 'theme:sanctuary'),
    'vault': ("Disciples' vault", (12416, -384, 13184, 384), U1, U1 + 448, 'theme:chapel'),
    # the limbs (1280)
    'limb_stair': ("Limb stair", (4544, -4480, 5440, -3712), L2, L2 + 512, 'theme:limb'),
    'limb_walk': ("The limb walk", (5568, -4416, 9472, -3776), L2, L2 + 448, 'theme:limb'),
    'fruit': ("Fruit rooms", (9600, -4736, 11136, -3392), L2, L2 + 512, 'theme:limb'),
    'crown': ("The crown", (11264, -5376, 13568, -2816), L2, L2 + 1024, 'theme:crown'),
    'barkman': ("Barkman's hollow", (7168, -6144, 9472, -4544), L2, L2 + 640, 'theme:limb'),
    'treasure': ("Treasure room", (9600, -6016, 11136, -4864), L2, L2 + 448, 'theme:limb'),
    # the roots (-512)
    'root_hall': ("The root cellar", (-5504, -1152, -3584, 1024), R1, R1 + 640, 'theme:roots'),
    'root_west': ("West root alcove", (-6912, -512, -5632, 512), R1, R1 + 384, 'theme:roots'),
    'root_east': ("East root alcove", (-4864, 1152, -4096, 1920), R1, R1 + 384, 'theme:roots'),
    'sap_vats': ("Sap store", (-5504, -2816, -3584, -1280), R1, R1 + 512, 'theme:sap'),
    'pens': ("The pens", (-7296, -2560, -5632, -640), R1, R1 + 448, 'theme:pens'),
}
# Climbing tunnels: (name, path, floor, to, height above the floor, theme)
P = {
    'ring_stair': ("Ring stair", [[640, -1536], [640, -2048], [3968, -2048], [3968, -896], [4352, -896]], B0, U1, 448,
                   'theme:trunk'),
    'back_stair': ("The orcs' back stair", [[3456, 2304], [5504, 2304]], B0, U1, 384, 'theme:barracks'),
    'limb_climb': ("Limb climb", [[4992, -1536], [4992, -3584]], U1, L2, 448, 'theme:limb'),
    'root_stair': ("Root stair", [[-1408, -128], [-3456, -128]], B0, R1, 448, 'theme:roots'),
}
PATH_WIDTH = 320

CHAMFER = {
    'first_hall': 384, 'crown': (0, 384, 384, 384), 'root_hall': 256, 'pens': (192, 0, 0, 192), 'barkman': 320,
    'fruit': (0, 192, 192, 0), 'shaalth': 0, 'root_west': (128, 0, 0, 128), 'root_east': (0, 0, 128, 128),
}

# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s27 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-09: "a log cabin, not a temple grown in a
# tree"): the Hall of the Trunk is round (16 sides: four straight stretches where its doorways are, three-piece arcs
# between them) under a bark dome; the ring stair's bends are arcs; the roots' rooms, the barracks and the limbs' hollows
# lose their square corners (a slanted cut with a break pushed in, the same build every time); the limb walk tapers and
# lies open to the leaves and the sky; the crown is open to the sky in its middle.
import hashlib  # noqa: E402
import math  # noqa: E402


def _h(*k):
    return int(hashlib.md5(repr(k).encode()).hexdigest()[:8], 16) / 0xffffffff


def broken(x0, y0, x1, y1, c, key):
    """cave() with each cut corner broken: the cut's middle pushed into the room by 6-14 % of the cut."""
    sw, se, ne, nw = (c, c, c, c) if isinstance(c, int) else c
    pts = []
    for name, (cx, cy, sx, sy), cut in (('sw', (x0, y0, 1, 1), sw), ('se', (x1, y0, -1, 1), se),
                                       ('ne', (x1, y1, -1, -1), ne), ('nw', (x0, y1, 1, -1), nw)):
        if not cut:
            pts.append([cx, cy])
            continue
        k = 0.56 + 0.08 * _h(key, name)
        mid = [round(cx + sx * cut * k), round(cy + sy * cut * k)]
        a, b = ([cx, cy + sy * cut], [cx + sx * cut, cy]) if name in ('sw', 'ne') else ([cx + sx * cut, cy], [cx, cy + sy * cut])
        pts += [a, mid, b]
    return pts


def round_hall(box, flats, key, pieces=3):
    """A round room: straight stretches on the box's sides where flats say (side: (lo, hi)), arcs between them
    (quarter ellipses through the stretches' ends in `pieces` straight pieces, each point pulled in up to 3 %)."""
    x0, y0, x1, y1 = box
    (s0, s1), (e0, e1), (n0, n1), (w0, w1) = flats['s'], flats['e'], flats['n'], flats['w']
    pts = []

    def arc(cx, cy, rx, ry, t0, t1, name):
        for i in range(1, pieces):
            t = math.radians(t0 + (t1 - t0) * i / pieces)
            f = 1 - 0.03 * _h(key, name, i)
            pts.append([round(cx + rx * f * math.cos(t)), round(cy + ry * f * math.sin(t))])
    pts += [[s0, y0], [s1, y0]]
    arc(s1, e0, x1 - s1, e0 - y0, -90, 0, 'se')
    pts += [[x1, e0], [x1, e1]]
    arc(n1, e1, x1 - n1, y1 - e1, 0, 90, 'ne')
    pts += [[n1, y1], [n0, y1]]
    arc(n0, w1, n0 - x0, y1 - w1, 90, 180, 'nw')
    pts += [[x0, w1], [x0, w0]]
    arc(s0, w0, s0 - x0, w0 - y0, 180, 270, 'sw')
    return pts


# the hall's straight stretches: the trunk door and the ring stair (south), the barracks door (east), the Chapel of
# Sap (north), the root stair (west)
HALL_FLATS = {'s': (-320, 864), 'e': (-576, -192), 'n': (-288, 288), 'w': (-352, 96)}
# The limb walk tapers from 640 at the limb stair to 448 at the fruit rooms; its south side runs straight where
# Barkman's hollow opens off it.
LIMB_WALK = [[5568, -4416], [8064, -4352], [8576, -4352], [9472, -4320], [9472, -3872], [5568, -3776]]
SHAPES = {'first_hall': round_hall(R['first_hall'][1], HALL_FLATS, 'hall'), 'limb_walk': LIMB_WALK}
# corners cut and broken (sw, se, ne, nw), each kept clear of the room's doorways and of what stands in it
BROKEN = {
    'root_hall': (256, 448, 256, 448), 'root_west': (192, 192, 256, 192), 'root_east': (128, 128, 192, 192),
    'pens': (128, 192, 192, 384), 'sap_vats': (0, 0, 0, 384), 'barracks': (128, 256, 128, 128),
    'guardroom': (320, 320, 128, 320), 'fruit': (320, 384, 320, 320), 'barkman': (384, 320, 448, 384),
    'treasure': (128, 128, 0, 256), 'limb_stair': (256, 128, 128, 192), 'crown': (0, 640, 640, 640),
}

ORDER = sorted(list(R) + list(P))


def outline(rid):
    if rid in SHAPES:
        return [list(p) for p in SHAPES[rid]]
    b = R[rid][1]
    if rid in BROKEN:
        return broken(*b, BROKEN[rid], rid)
    return cave(*b, CHAMFER.get(rid, 0))


def walls_of(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def shared(a, b):
    """The facing axis-aligned walls of rooms a and b: (gap, wall in a, wall in b, lo, hi, axis, p0, p1)."""
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


def opening(oid, a, b, at=None, width=256, height=320, link=None, **kw):
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b}
    if a not in P and b not in P:
        gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
        if at is None:
            at = (lo + hi) / 2
        if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
            raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
        forward = (p1[ax] - p0[ax]) > 0
        along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
        d['from_wall'] = i
        d['to_wall'] = j
        if along != 0.5:
            d['along'] = along
    if link:
        d['link'] = link
    d['width'] = 'full' if (a in P or b in P) else width
    d['height'] = height
    d.update(kw)
    return d


OPENINGS = [
    opening('open:door_hall', 'trunk_door', 'first_hall', at=0, width=384, height=384, link='link:door_hall'),
    opening('open:hall_barracks', 'first_hall', 'barracks', at=-384, width=256, height=320, link='link:hall_barracks'),
    opening('open:hall_chapel', 'first_hall', 'chapel', at=0, width=384, height=384, link='link:hall_chapel'),
    opening('open:barracks_guard', 'barracks', 'guardroom', at=2368, width=384, height=352, link='link:barracks_guard'),
    opening('open:guard_chapel', 'guardroom', 'chapel', at=2112, width=256, height=320, link='link:guard_chapel'),
    opening('open:hall_roots', 'first_hall', 'root_stair', width=320, height=384, link='link:hall_roots'),
    opening('open:stair_roots', 'root_stair', 'root_hall', width=320, height=384, link='link:hall_roots'),
    opening('open:roots_west', 'root_hall', 'root_west', at=0, width=320, height=320, link='link:roots_west'),
    opening('open:roots_east', 'root_hall', 'root_east', at=-4480, width=320, height=320, link='link:roots_east'),
    opening('open:roots_vats', 'root_hall', 'sap_vats', at=-4544, width=256, height=320, link='link:roots_vats'),
    opening('open:vats_pens', 'sap_vats', 'pens', at=-1920, width=320, height=352, link='link:vats_pens'),
    opening('open:pens_west', 'pens', 'root_west', at=-6272, width=320, height=320, link='link:pens_west'),
    opening('open:hall_ring', 'first_hall', 'ring_stair', width=320, height=384, link='link:hall_ring'),
    # from_wall 20: the ring stair's end, counted with its bends rounded (bend_radius 512; was 7 with square bends)
    opening('open:ring_landing', 'ring_stair', 'ring1', width=320, height=384, link='link:hall_ring', from_wall=20, to_wall='w'),
    opening('open:ring_shaalth', 'ring1', 'shaalth', at=-896, width=256, height=352, link='link:ring_shaalth'),
    opening('open:shaalth_cells', 'shaalth', 'cells', at=6528, width=384, height=384, link='link:shaalth_cells'),
    opening('open:guard_back', 'guardroom', 'back_stair', width=320, height=352, link='link:guard_cells'),
    opening('open:back_cells', 'back_stair', 'cells', width=320, height=352, link='link:guard_cells'),
    opening('open:shaalth_shaman', 'shaalth', 'shaman', at=0, width=256, height=352, link='link:shaalth_shaman'),
    opening('open:shaman_asc', 'shaman', 'ascension', at=0, width=256, height=352, link='link:shaman_asc'),
    opening('open:asc_vault', 'ascension', 'vault', at=0, width=256, height=352, link='link:asc_vault'),
    opening('open:ring_climb', 'ring1', 'limb_climb', width=320, height=384, link='link:ring_limbs'),
    opening('open:climb_limbs', 'limb_climb', 'limb_stair', width=320, height=384, link='link:ring_limbs'),
    opening('open:limbs_walk', 'limb_stair', 'limb_walk', at=-4096, width=384, height=384, link='link:limbs_walk'),
    opening('open:walk_fruit', 'limb_walk', 'fruit', at=-4096, width=384, height=384, link='link:walk_fruit'),
    opening('open:fruit_crown', 'fruit', 'crown', at=-4064, width=448, height=448, link='link:fruit_crown'),
    opening('open:walk_barkman', 'limb_walk', 'barkman', at=8320, width=384, height=384, link='link:walk_barkman'),
    opening('open:barkman_treasure', 'barkman', 'treasure', at=-5440, width=320, height=352, link='link:barkman_treasure'),
    opening('open:treasure_crown', 'treasure', 'crown', at=-5120, width=256, height=352, link='link:treasure_crown'),
]


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


def bars(at, size, notes):
    """A static side of a cage: an 8-thick wall of bars 256 high."""
    return {'at': at, 'size': size, 'rise': 256, 'surface': dict(GRILLE), 'end_surface': dict(IRON, fit=False),
            'top_surface': dict(IRON, scale=3), 'notes': notes}


def pillar(at, size, surface=BARK):
    return {'at': at, 'size': size, 'surface': dict(surface)}


# Cages (D-27: Nathan and Sky in the pens, Snog and Alicia in the cells, Sheewana in Shaalth's hall). Each cage is
# 384 square inside: two static sides of bars and a gate (objects.yml movers) on its open side.
PEN_CAGES = {'nathan': -1344, 'sky': -2176}           # pens: y centres, against the west wall (x -7296 .. -6912)
CELL_CAGES = {'snog': 5952, 'alicia': 7104}           # cells: x centres, against the north wall (y 2688 .. 3072)
SHEEWANA_CAGE = (8320, 1152, 8704, 1536)              # Shaalth's hall, its north-east corner

EXTRA = {
    'trunk_door': {
        'notes': "Inside the great tree's round door, at the foot of the temple's first stair: the arrival; the door out (D2) in the south wall.",
    },
    'first_hall': {
        'ceiling_points': [[0, -128, 1216]],
        'pillars': [pillar([-640, -768], [160, 160]), pillar([640, -768], [160, 160]),
                    pillar([640, 512], [160, 160]), pillar([-640, 512], [160, 160])],
        'notes': "The hollow trunk's first hall under a dome of bark, four root columns; a voice from the wood. The root stair west, the ring stair south-east, the barracks east, the Chapel of Sap north.",
    },
    'barracks': {
        'notes': "The priests' cells knocked into one: orc bedrolls along the walls, a cookfire scorch.",
    },
    'guardroom': {
        'notes': "The orcs' guard post: the back stair up to the cell row leaves its east wall.",
    },
    'chapel': {
        'walls': [{'wall': 'w', 'panels': [
            {'id': 'panel:book_history', 'offset': 256, 'length': 256, 'bottom': 0, 'height': 384, 'surface': dict(SHELVES, fit=True)},
            {'id': 'panel:book_sap', 'offset': 704, 'length': 256, 'bottom': 0, 'height': 384, 'surface': dict(SHELVES, fit=True)},
            {'id': 'panel:book_ceremonies', 'offset': 1152, 'length': 256, 'bottom': 0, 'height': 384, 'surface': dict(SHELVES, fit=True)}]}],
        'platforms': [plat('platform:ledge_red', [-384, 2864], [192, 96], 96, GREEN, MOSSFLAGS, "The red flask's alcove ledge."),
                      plat('platform:ledge_blue', [768, 2864], [192, 96], 96, GREEN, MOSSFLAGS, "The blue flask's alcove ledge.")],
        'notes': "The priests' chapel: three bookcases (History of Bark, Book of Sap, Morning Ceremonies), two flasks on alcove ledges in the north wall.",
    },
    'ring1': {
        'notes': "The ring stair's landing inside the trunk's wall: the door to Shaalth's hall east, the limb climb south.",
    },
    'shaalth': {
        'ceiling_points': [[7168, 64, U1 + 1152]],
        'levels': [{'id': 'level:dais', 'outline': [[7552, -1280], [8576, -1280], [8576, -576], [7552, -576]], 'floor': U1 + 32,
                    'edge': GREEN_END, 'surface': dict(MOSSFLAGS), 'notes': "Shaalth's dais, where the altar stood."}],
        'pillars': [pillar([6400, -512], [192, 192], GREEN_IVY), pillar([6400, 640], [192, 192], GREEN_IVY),
                    pillar([7936, 1088], [192, 192], GREEN_IVY)],
        'platforms': [bars([8324, 1344], [8, 384], "Sheewana's cage: its west side of bars.")],
        'notes': "The temple's sanctuary made an orc king's hall: ivy on the green stone, the dais in the south-east, Sheewana's cage in the north-east corner; his hoard by the dais.",
    },
    'cells': {
        'platforms': [bars([x - 188, 2880], [8, 384], f"{k.title()}'s cell: its west side of bars.") for k, x in CELL_CAGES.items()]
        + [bars([x + 188, 2880], [8, 384], f"{k.title()}'s cell: its east side of bars.") for k, x in CELL_CAGES.items()],
        'notes': "Root cages along the north wall: Snog the Orc and Alicia the Just.",
    },
    'shaman': {
        'levels': [{'id': 'level:rug', 'outline': [[9152, -448], [10048, -448], [10048, 448], [9152, 448]], 'floor': U1 + 4,
                    'edge': HEART, 'surface': dict(S_('7t1beds', 256, 64), fit=False), 'notes': "The shamans' rugs."}],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:cabinet', 'offset': 640, 'length': 256, 'bottom': 0, 'height': 384,
                                            'surface': dict(CABINET, fit=True)}]}],
        'notes': "Rugs, a cabinet and a kettle: the shaman's tea room.",
    },
    'ascension': {
        'ceiling_points': [[11392, 0, U1 + 896]],
        'walls': [{'wall': 'w', 'panels': [{'id': 'panel:dial_west', 'offset': 384, 'length': 128, 'bottom': 128, 'height': 128,
                                            'surface': dict(DIAL, fit=True)}]},
                  {'wall': 'n', 'panels': [{'id': 'panel:dial_north', 'at': 'centre', 'length': 128, 'bottom': 128, 'height': 128,
                                            'surface': dict(DIAL, fit=True)}]},
                  {'wall': 'e', 'panels': [{'id': 'panel:dial_east', 'offset': 384, 'length': 128, 'bottom': 128, 'height': 128,
                                            'surface': dict(DIAL, fit=True)}]}],
        'platforms': [plat('platform:dark_water', [10944, -704], [320, 320], 64, GREEN, DARKWATER, "The basin of Dark Water."),
                      plat('platform:crystal_water', [11840, -704], [320, 320], 64, GREEN, CRYSTAL, "The basin of Crystal Water."),
                      plat('platform:lectern', [11392, 704], [128, 96], 112, HEART, BOOK_TOP, "The lectern of the Book of Ascension.")],
        'notes': "The Disciples' chapel: three dials (west, north, east), a lever in the south wall, two basins (Dark Water, Crystal Water), the Book of Ascension on its lectern; the vault's arched door east.",
    },
    'vault': {'notes': "'Disciples of Bark ONLY!': the old priests' vault."},
    'limb_stair': {'notes': "The limb climb's head, where the trunk forks."},
    'limb_walk': {
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:limb_1', 'offset': 512, 'length': 192, 'bottom': 64, 'height': 224,
                                            'surface': dict(SAPWALL, fit=True)},
                                           {'id': 'panel:limb_3', 'offset': 2816, 'length': 192, 'bottom': 64, 'height': 224,
                                            'surface': dict(SAPWALL, fit=True)}]},
                  {'wall': 's', 'panels': [{'id': 'panel:limb_2', 'offset': 640, 'length': 192, 'bottom': 64, 'height': 224,
                                            'surface': dict(SAPWALL, fit=True)}]}],
        'notes': "A walk hollowed along a great limb; three limb alcoves: 'Feed me! Give gem?'",
    },
    'fruit': {'notes': "Hollows where the tree hangs its fruit."},
    'crown': {
        'ceiling_points': [[12416, -4096, L2 + 1280]],
        'levels': [{'id': f'level:pool_{k}', 'outline': cave(x - 160, y - 160, x + 160, y + 160, 64), 'floor': L2 - 48,
                    'edge': BARK, 'surface': dict(CRYSTAL), 'notes': f"The {k} fountain's pool."}
                   for k, (x, y) in {'fire': (11904, -3456), 'air': (12928, -3456), 'water': (12928, -4736), 'body': (11904, -4736)}.items()],
        'platforms': [plat(f'platform:fountain_{k}', [x, y], [128, 128], 112, BARK, CRYSTAL, f"The {k} fountain: a bark spout over its pool.", base=0)
                      for k, (x, y) in {'fire': (11904, -3456), 'air': (12928, -3456), 'water': (12928, -4736), 'body': (11904, -4736)}.items()],
        'notes': "Light through the leaves: grass underfoot, a canopy overhead, four fountains.",
    },
    'barkman': {
        'platforms': [plat('platform:diary', [9216, -5888], [160, 128], 96, BARK, BOOK_TOP, "A stump with Barkman's diary on it.")],
        'notes': "Barkman's hollow: his diary on a stump, his bound chest; Barkman stands here hidden until a limb is fed.",
    },
    'treasure': {'notes': "The temple's offerings, which the shamans are sorting."},
    'root_hall': {
        'rough': RUFF, 'ceiling_points': [[-4544, -64, R1 + 768]],
        'pillars': [pillar([-4992, -512], [192, 192]), pillar([-4096, 448], [192, 192]), pillar([-4160, -640], [128, 128])],
        'notes': "Under the trunk: roots as pillars, damp earth, webs. The alcoves west and north, the sap store's door south.",
    },
    'root_west': {
        'walls': [{'wall': 'w', 'panels': [{'id': 'panel:root_west', 'at': 'centre', 'length': 256, 'bottom': 32, 'height': 256,
                                            'surface': dict(SAPWALL, fit=True)}]}],
        'notes': "'Feed me! Give gem?' A knot in the root wall round a hollow.",
    },
    'root_east': {
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:root_east', 'at': 'centre', 'length': 256, 'bottom': 32, 'height': 256,
                                            'surface': dict(SAPWALL, fit=True)}]}],
        'notes': "As the west: a knot in the root wall round a hollow.",
    },
    'sap_vats': {
        'platforms': [plat('platform:vat_1', [-4096, -2432], [384, 384], 128, HEART, SAP, "A vat of the tree's sap."),
                      plat('platform:vat_2', [-4096, -1792], [384, 384], 128, HEART, SAP, "A vat of the tree's sap."),
                      plat('platform:ledger', [-5248, -2560], [128, 96], 64, HEART, BOOK_TOP, "The orcs' ledger on a crate.")],
        'walls': [{'wall': 's', 'panels': [{'id': 'panel:danger', 'offset': 928, 'length': 128, 'bottom': 160, 'height': 128,
                                            'surface': dict(S_('7gt002a', 64, 64), fit=True)}]}],
        'notes': "Vats of sap, the orcs' ledger, the black barrel and its sign, a chest.",
    },
    'pens': {
        'rough': RUFF,
        'platforms': [bars([-7104, y - 188], [384, 8], f"{k.title()}'s pen: its south side of bars.") for k, y in PEN_CAGES.items()]
        + [bars([-7104, y + 188], [384, 8], f"{k.title()}'s pen: its north side of bars.") for k, y in PEN_CAGES.items()],
        'notes': "Cages for prisoners against the west wall (Nathan, Sky); the pen lever on the south wall.",
    },
}


# ------------------------------------------------------------------------------------------------ D-89 identity (rooms)
LEAVES = S_('eswamp', 128, 128)         # leaves: the limb walk's sides above the branch, the crown's canopy (DD-12's hedge)
ROOT_BASE = [{'height': 64, 'surface': dict(EARTH)}]          # roots rising round the foot of the trunk's walls
STONE_BASE = [{'height': 48, 'surface': dict(DARKFLAGS)}]     # a dark plinth under the old temple's green stone
for _t in THEMES:
    if _t['id'] in ('theme:trunk', 'theme:limb', 'theme:barracks'):
        _t['bands'] = [dict(b) for b in ROOT_BASE]
    if _t['id'] in ('theme:chapel', 'theme:sanctuary'):
        _t['bands'] = [dict(b) for b in STONE_BASE]
    if _t['id'] == 'theme:barracks':
        # the priests' cells were rooms hollowed in the trunk (was the small green brick ceb3s: "brick barracks")
        _t['wall'], _t['ceiling'] = BARK, HEART
        _t['notes'] = ("The priests' cells made orc barracks, hollowed in the trunk: bark walls over a foot of root "
                       "earth (c2b), trodden dirt (7dirt1), the heartwood floor above for a roof (7t1books1).")
    if _t['id'] == 'theme:crown':
        _t['ceiling'] = LEAVES
        _t['notes'] = "The crown: bark walls, grass underfoot and a canopy of leaves overhead (eswamp), open to the sky in the middle."


def _dome(cx, cy, top, rings):
    """ceiling_points of a dome: its top over (cx, cy), then rings of eight points (radius, height)."""
    pts = [[cx, cy, top]]
    for i, (r, z) in enumerate(rings):
        for k in range(8):
            a = math.radians(22.5 * (i % 2) + 45 * k)
            pts.append([round(cx + r * math.cos(a)), round(cy + r * math.sin(a)), z])
    return pts


def _bumps(rid, amp, step=448, margin=384, keep=()):
    """floor_points: rises and dips (|dz| <= amp) on a grid inside the room, level within `keep` boxes."""
    x0, y0, x1, y1 = R[rid][1]
    fl = R[rid][2]
    pts = []
    x = x0 + margin
    while x <= x1 - margin:
        y = y0 + margin
        while y <= y1 - margin:
            dz = round((_h(rid, 'f', x, y) * 2 - 1) * amp / 16) * 16
            if abs(dz) >= 16 and not any(a <= x <= c and b <= y <= d for a, b, c, d in keep):
                pts.append([x, y, fl + dz])
            y += step
        x += step
    return pts


def _vault(rid, rise, step=576, margin=384):
    x0, y0, x1, y1 = R[rid][1]
    ce = R[rid][3]
    pts = []
    x = x0 + margin
    while x <= x1 - margin:
        y = y0 + margin
        while y <= y1 - margin:
            pts.append([x, y, ce + round((0.4 + 0.6 * _h(rid, 'c', x, y)) * rise / 16) * 16])
            y += step
        x += step
    return pts


def _roots(rid, spots, length=256):
    """Roots hanging through the earthen roof (six-sided narrowing blocks)."""
    return [{'at': list(a), 'radius': 56, 'length': length, 'sides': 6, 'surface': dict(EARTH)} for a in spots]


# the Hall of the Trunk: round, under a bark dome 448 over its walls
EXTRA['first_hall']['ceiling_points'] = _dome(0, -128, 1344, [(560, 1216), (1000, 1056)])
EXTRA['first_hall']['notes'] = ("The hollow trunk's first hall: round (16 sides), under a dome of bark 1,344 high, four "
                                "root columns; a voice from the wood. The root stair west, the ring stair south-east, the "
                                "barracks east, the Chapel of Sap north.")
# the roots: 7d22's earth, broken and sloping, roots hanging through the roof
EXTRA['root_hall'].update({
    'floor_points': _bumps('root_hall', 64), 'ceiling_points': _vault('root_hall', 192),
    'stalactites': _roots('root_hall', [(-4800, 256), (-4352, -512), (-5184, -320), (-3904, 512)]),
})
EXTRA['root_west'].update({'floor_points': _bumps('root_west', 48, step=384, margin=320),
                           'ceiling_points': _vault('root_west', 128, step=512, margin=320)})
EXTRA['root_east'].update({'ceiling_points': [[-4480, 1536, R1 + 384 + 128]]})
EXTRA['pens'].update({'floor_points': _bumps('pens', 48, keep=[(-7296, -2560, -6720, -640)]),
                      'ceiling_points': _vault('pens', 128),
                      'stalactites': _roots('pens', [(-6016, -1408), (-6400, -2240)], 224)})
EXTRA['sap_vats']['ceiling_points'] = _vault('sap_vats', 128)
# the limbs: knotted bark walls in the hollows; the walk open to leaves and the sky
for _r in ('fruit', 'barkman', 'limb_stair'):
    EXTRA.setdefault(_r, {})['rough'] = dict(RUFF)
THEMES.append({'id': 'theme:branch', 'wall': LEAVES, 'floor': HEART, 'ceiling': dict(LEAVES, sky=True), 'door': DOOR,
               'bands': [{'height': 256, 'surface': dict(BARK)}],
               'notes': "Along the top of a great limb: the branch's bark to 256 (xdbark), leaves above (eswamp), the sky overhead."})
R['limb_walk'] = R['limb_walk'][:3] + (L2 + 768, 'theme:branch')
EXTRA['limb_walk'].update({
    # the tapering outline's edges: 4 the north side (from the east end), 0 the south side's western stretch
    'walls': [{'wall': 4, 'panels': EXTRA['limb_walk']['walls'][0]['panels']},
              {'wall': 0, 'panels': EXTRA['limb_walk']['walls'][1]['panels']}],
    'notes': ("A walk along the top of a great limb, tapering toward the fruit rooms: the branch's bark to 256, leaves "
              "above, the sky overhead; three limb alcoves: 'Feed me! Give gem?'"),
})
EXTRA['crown'].pop('ceiling_points', None)
EXTRA['crown'].update({
    'bands': [{'height': 384, 'surface': dict(BARK)}],
    'ceiling_levels': [{'outline': broken(11840, -4672, 12992, -3520, 320, 'crown_sky'), 'ceiling': L2 + 1536,
                        'edge': dict(LEAVES), 'surface': dict(LEAVES, sky=True),
                        'notes': "The crown's middle, open to the sky through the leaves."}],
    'notes': "The crown: grass underfoot, bark walls rising into leaves, the sky open over the four fountains.",
})


def room_doc(rid):
    if rid in P:
        name, path, fl, to, h, theme = P[rid]
        return {'id': 'room:' + rid, 'name': name, 'path': path, 'width': PATH_WIDTH, 'smooth': 1, 'floor': fl,
                'slope': {'to': to}, 'ceiling': max(fl, to) + h, 'ceiling_slope': {'to': to + h}, 'theme': theme,
                **({'bend_radius': 512} if rid == 'ring_stair' else {}),
                'notes': {'ring_stair': "The ring stair, winding inside the trunk's wall from the hall up to the ring landing (0 to 640).",
                          'back_stair': "The orcs' back stair from the guardroom up to the cell row (0 to 640).",
                          'limb_climb': "From the ring landing up into the limbs (640 to 1280).",
                          'root_stair': "Down from the hall into the roots (0 to -512)."}[rid]}
    name, b, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
    d.update(EXTRA.get(rid, {}))
    return d


def extent(rid):
    pts = P[rid][1] if rid in P else outline(rid)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs) + (PATH_WIDTH if rid in P else 0)
    h = max(ys) - min(ys) + (PATH_WIDTH if rid in P else 0)
    return [w, h], [(max(xs) + min(xs)) // 2, (max(ys) + min(ys)) // 2]


def area(rid):
    if rid in P:
        pts = P[rid][1]
        return sum(abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)) * PATH_WIDTH
    o = outline(rid)
    return abs(sum(o[i][0] * o[(i + 1) % len(o)][1] - o[(i + 1) % len(o)][0] * o[i][1] for i in range(len(o)))) / 2


if __name__ == '__main__':
    tot = 0
    for r in ORDER:
        a = area(r)
        tot += a
        print(f'{r:16s} {a / 1e6:6.2f}')
    print('total', tot / 1e6)
