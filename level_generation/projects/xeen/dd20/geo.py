#!/usr/bin/env python3
"""DD-20 Lakeside Coven and Sewer: the geometry (rooms, openings) shared by L2, L3 and L4.

Three levels in one frame (x east, y north as D4; origin under the Guild's centre; z 0 the coven's floor, about 640
under D4's square):
- the coven at 0 (MM7 Temple of the Moon 7d06 dressed stone): the Guild's back stair comes down from its landing (640)
  northward into the coven hall; the double doors (the Moon seal, two leaves) north to the witches' walk, the
  antechamber and the Head Witch's room in the north-west corner, the brewery between the walk and her private door;
  east of the hall the gaoler's room (its stair down to the cells) and the dormitory with the coven store south of it;
- the cells at -256 (MM7 Tidewater Caverns 7d17 wet rock): one corridor east of the gaol, four cages on its north
  side, the drain stair from its east end down to the sewer;
- the sewer at -512 (7d17): the slop pit at the drain stair's foot, the drain cross south of it (the ambush), the
  main drain west to the trapdoor's sump, the cistern under the coven store (its hatch above), the pump room, the
  hideout, the warren and the east drain east to the lake outfall, the Dragon's niche and the jetty shaft.
Rooms are rectangles (caves chamfered, `rough`) whose axis-aligned sides carry the openings; walls between rooms are
128 thick. The cistern lies under the store (the hatch); nothing else is stacked.
"""

COVEN, CELLS, SEWER = 0, -256, -512
GUILD = 640


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# The coven: MM7 Temple of the Moon (7d06) dressed stone. 7tws2 and tws2b are one storey high with their frieze at the
# top (they do not meet themselves up and down), so the coven's rooms are 512 high and lay them at scale 2: once up.
COVENWALL = S_('7tws2', 128, 256, scale=2)    # dressed stone under its frieze
SKULLWALL = S_('tws2b', 128, 256, scale=2)    # the ram-skull frieze (the Head Witch's room)
BLOCK = S_('twb2', 128, 256)                  # block ceilings
DARKFLAGS = S_('7tfb11', 128, 128)            # dark flags
FLAGS = S_('tfb2', 128, 128)                  # pale worn flags: reveals, the stair, hearths
BRICK = S_('wall', 128, 256)                  # the store's dark brick
SLAB = S_('twb1', 128, 256)                   # slab (the themes' door default)
TEMPLEDOOR = S_('t1d1', 256, 256)             # the coven's doors: MM6's temple door (2026-11-22, was the slab twb1)
SIGIL = S_('tws1a', 128, 256)                 # the coven's carved sigil
SEAL = [[S_('t1d1a', 256, 256), S_('t1d1b', 256, 256)], [S_('t1d1c', 256, 256), S_('t1d1d', 256, 256)]]  # the Moon seal
BEDTOP = S_('7t1beds2', 128, 256)             # blankets
BEDSIDE = S_('7t1beds1', 256, 32)             # a bed's frame (beds 32 high: once up)
CABS = S_('7t1cabs', 64, 128)                 # the store's shelves of jars
BOOKS = S_('7t1books', 128, 256)              # the Head Witch's shelf
# the Guild's back stair: D4's t09 ashlar (the Guild outside, A6's town kit) over its plinth
ASHLAR = S_('t09a01', 128, 256)
ASHLAR_TRIM = S_('t09b11b', 128, 32)
# the cells and the sewer: MM7 The Tidewater Caverns (7d17)
ROCK = S_('c2b', 256, 256)                    # wet dark rock: walls and roofs
WETFLOOR = S_('cfb1', 128, 128)               # wet rock floors
PLANKS = S_('7trimd', 128, 256)               # weathered plank walks
SEWERDOOR = S_('td1', 512, 512)               # the skull-ring door
TRIM = S_('trim9_32a', 64, 32)                # a timber kerb along the drains' feet
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}
NICHE = S_('cws1', 128, 256)                  # a narrow alcove in the rock (the Dragon's)
WALLGRATE = S_('cws1d', 128, 256)             # a grille set in the rock: drain mouths, the lake bars
GRATE = S_('d1lggrt', 256, 256)               # the round street grates overhead (DD-01's, MM6)
HATCH = S_('7gt002c', 64, 64, scale=4)        # a framed plank hatch (the trapdoor, the store's hatch): 256 square
TABLE = S_('7trimda', 256, 128)               # weathered planks: table tops, the pump's box
LADDER = S_('d1ladder', 128, 256)             # the jetty shaft's iron ladder (DD-01's)
GRILLE = S_('xwcage', 128, 256)               # cage bars (XD-04's see-through bars, D-22.1)
IRON = S_('xwiron', 128, 128)                 # cage tops
MIRROR = S_('xmirror', 128, 128)             # A6's silvered glass (D-37)

THEMES = [
    {'id': 'theme:guild', 'wall': ASHLAR, 'floor': FLAGS, 'ceiling': BLOCK, 'door': SLAB, 'reveal': FLAGS,
     'bands': [{'height': 32, 'surface': ASHLAR_TRIM}],
     'notes': "The Guild's back stair: D4's t09 ashlar (t09a01 over a t09b11b plinth), worn flags (tfb2), 7d06 block above."},
    {'id': 'theme:coven', 'wall': COVENWALL, 'floor': DARKFLAGS, 'ceiling': BLOCK, 'door': SLAB, 'reveal': FLAGS,
     'notes': "The coven: 7d06's dressed stone under its frieze (7tws2, once up a 512 wall), dark flags (7tfb11), block ceilings (twb2)."},
    {'id': 'theme:head', 'wall': SKULLWALL, 'floor': DARKFLAGS, 'ceiling': BLOCK, 'door': SLAB, 'reveal': FLAGS,
     'notes': "The Head Witch's room: 7d06's ram-skull frieze (tws2b)."},
    {'id': 'theme:store', 'wall': BRICK, 'floor': DARKFLAGS, 'ceiling': BLOCK, 'door': SLAB, 'reveal': FLAGS,
     'notes': "The coven store: 7d06's dark brick ('wall')."},
    {'id': 'theme:cells', 'wall': ROCK, 'floor': WETFLOOR, 'ceiling': ROCK, 'door': SEWERDOOR,
     'notes': "The cells: 7d17's wet rock (c2b), wet floors (cfb1)."},
    {'id': 'theme:drain', 'wall': ROCK, 'floor': PLANKS, 'ceiling': ROCK, 'door': SEWERDOOR,
     'bands': [{'height': 32, 'surface': TRIM}],
     'notes': "The drains: 7d17's wet rock over a timber kerb (trim9_32a), plank walks (7trimd) either side of the water."},
    {'id': 'theme:sewer', 'wall': ROCK, 'floor': WETFLOOR, 'ceiling': ROCK, 'door': SEWERDOOR,
     'notes': "The sewer's chambers: 7d17's wet rock and wet floors."},
    {'id': 'theme:cave', 'wall': ROCK, 'floor': WETFLOOR, 'ceiling': ROCK, 'door': SEWERDOOR,
     'notes': "Where the vault has fallen in: rough wet rock (the warren)."},
    {'id': 'theme:outfall', 'wall': ROCK, 'floor': PLANKS, 'ceiling': ROCK, 'door': SEWERDOOR,
     'notes': "The lake outfall: wet rock, plank walks round the tidal pool."},
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
    # the coven (0)
    'guild_landing': ("Guild's back landing", (-1024, -3968, -256, -3328), GUILD, GUILD + 384, 'theme:guild'),
    'coven_hall': ("Coven hall", (-1536, -640, 1024, 1920), COVEN, 512, 'theme:coven'),
    'witches_walk': ("Witches' walk", (-3328, 2048, 512, 2688), COVEN, 512, 'theme:coven'),
    'antechamber': ("Antechamber", (-3328, 2816, -2432, 3584), COVEN, 512, 'theme:coven'),
    'head_witch': ("Head Witch's room", (-4352, 3712, -2048, 5248), COVEN, 512, 'theme:head'),
    'brewery': ("Brewery", (-1920, 2816, 512, 4352), COVEN, 512, 'theme:coven'),
    'gaol': ("Gaoler's room", (1152, 768, 2688, 1920), COVEN, 512, 'theme:coven'),
    'dormitory': ("Witches' dormitory", (1152, -896, 3072, 640), COVEN, 512, 'theme:coven'),
    'store': ("Coven store", (1152, -2304, 2432, -1024), COVEN, 512, 'theme:store'),
    # the cells (-256)
    'cells': ("The cells", (4224, 768, 7680, 1920), CELLS, CELLS + 448, 'theme:cells'),
    # the sewer (-512)
    'slop_pit': ("Slop pit", (9088, 768, 10112, 1792), SEWER, SEWER + 448, 'theme:sewer'),
    'cross': ("Drain cross", (8704, -1024, 10240, 640), SEWER, SEWER + 576, 'theme:sewer'),
    'main_drain': ("Main drain", (4096, -768, 8576, 0), SEWER, SEWER + 448, 'theme:drain'),
    'sump': ("Trapdoor sump", (3200, -1920, 3968, 384), SEWER, SEWER + 512, 'theme:sewer'),
    'cistern': ("Cistern", (1024, -2560, 3072, -1152), SEWER, -128, 'theme:sewer'),
    'pump_room': ("Old pump room", (5632, -2048, 6912, -896), SEWER, SEWER + 448, 'theme:sewer'),
    'hideout': ("Dead man's hideout", (9216, -2176, 9984, -1152), SEWER, SEWER + 384, 'theme:sewer'),
    'warren': ("Stalker warren", (10368, 0, 12160, 1664), SEWER, SEWER + 512, 'theme:cave'),
    'east_drain': ("East drain", (10368, -1664, 13696, -640), SEWER, SEWER + 448, 'theme:drain'),
    'outfall': ("Lake outfall", (12288, -512, 14848, 2304), SEWER, SEWER + 768, 'theme:outfall'),
    'niche': ("The Dragon's niche", (14976, 1536, 15744, 2304), SEWER, SEWER + 384, 'theme:sewer'),
    'jetty_shaft': ("Jetty shaft", (13824, -1664, 14592, -640), SEWER, SEWER + 1152, 'theme:sewer'),
}
# Sloping stairs: (name, path, floor, to, height above the floor, theme)
P = {
    'guild_stair': ("Guild's back stair", [[-640, -3200], [-640, -768]], GUILD, COVEN, 448, 'theme:guild'),
    'gaol_stair': ("Cell stair", [[2816, 1344], [4096, 1344]], COVEN, CELLS, 448, 'theme:cells'),
    'drain_stair': ("Drain stair", [[7808, 1280], [8960, 1280]], CELLS, SEWER, 448, 'theme:sewer'),
}
PATH_WIDTH = 320

CHAMFER = {
    'warren': (256, 384, 320, 0), 'outfall': (384, 0, 384, 0), 'slop_pit': 192, 'cistern': 0, 'cross': 0,
    'hideout': (0, 128, 128, 0), 'niche': (0, 0, 128, 0),
}

ORDER = sorted(list(R) + list(P))


def outline(rid):
    b = R[rid][1]
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
    if a not in P and b not in P and kw.get('in') != 'floor':
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
    if kw.get('in') == 'floor':
        d['at'] = at
    elif a in P or b in P:
        d['width'] = 'full'
        d['height'] = height
    else:
        d['width'] = width
        d['height'] = height
    d.update(kw)
    return d


# The store's floor hatch over the cistern (the ladder's way up), clear of the store's door.
HATCH_AT = [2176, -1920]          # its corners on the 256 grid: the hatch picture (256 square) lies once
HATCH_HOLE = [224, 224]
DOOR_W, DOOR_H = 224, 448          # coven slab doors: twb1 at 1.75 both ways
SEAL_W, SEAL_H = 448, 448          # the double doors: the Moon seal's four quarters at 0.875 both ways
SEWER_DOOR = 320                   # td1 at 0.625 both ways

OPENINGS = [
    opening('open:landing_stair', 'guild_landing', 'guild_stair', height=384, link='link:stair_hall'),
    opening('open:stair_hall', 'guild_stair', 'coven_hall', height=448, link='link:stair_hall'),
    opening('open:hall_walk', 'coven_hall', 'witches_walk', at=-640, width=SEAL_W, height=SEAL_H, link='link:hall_walk'),
    opening('open:walk_ante', 'witches_walk', 'antechamber', at=-2880, width=DOOR_W, height=DOOR_H, link='link:walk_ante'),
    opening('open:ante_head', 'antechamber', 'head_witch', at=-2880, width=DOOR_W, height=DOOR_H, link='link:ante_head'),
    opening('open:walk_brewery', 'witches_walk', 'brewery', at=-320, width=DOOR_W, height=DOOR_H, link='link:walk_brewery'),
    opening('open:brewery_head', 'brewery', 'head_witch', at=4032, width=DOOR_W, height=DOOR_H, link='link:brewery_head'),
    opening('open:hall_dorm', 'coven_hall', 'dormitory', at=0, width=DOOR_W, height=DOOR_H, link='link:hall_dorm'),
    opening('open:hall_gaol', 'coven_hall', 'gaol', at=1344, width=DOOR_W, height=DOOR_H, link='link:hall_gaol'),
    opening('open:dorm_store', 'dormitory', 'store', at=1536, width=DOOR_W, height=DOOR_H, link='link:dorm_store'),
    opening('open:gaol_stair', 'gaol', 'gaol_stair', height=384, link='link:gaol_cells'),
    opening('open:stair_cells', 'gaol_stair', 'cells', height=384, link='link:gaol_cells'),
    opening('open:cells_drain', 'cells', 'drain_stair', height=384, link='link:cells_slop'),
    opening('open:drain_slop', 'drain_stair', 'slop_pit', height=384, link='link:cells_slop'),
    opening('open:store_hatch', 'store', 'cistern', link='link:store_cistern', **{'in': 'floor'}, at=HATCH_AT,
            size=HATCH_HOLE, notes="The hole under the store's floor hatch: the cistern ladder's way up."),
    opening('open:cistern_sump', 'cistern', 'sump', at=-1536, width=320, height=352, link='link:cistern_sump'),
    opening('open:sump_main', 'sump', 'main_drain', at=-384, width=320, height=352, link='link:sump_main'),
    opening('open:main_pump', 'main_drain', 'pump_room', at=6272, width=SEWER_DOOR, height=SEWER_DOOR, link='link:main_pump'),
    opening('open:main_cross', 'main_drain', 'cross', at=-384, width=320, height=384, link='link:main_cross'),
    opening('open:cross_slop', 'cross', 'slop_pit', at=9600, width=320, height=384, link='link:cross_slop'),
    opening('open:cross_hideout', 'cross', 'hideout', at=9600, width=256, height=320, link='link:cross_hideout'),
    opening('open:cross_warren', 'cross', 'warren', at=448, width=256, height=352, link='link:cross_warren'),
    opening('open:cross_east', 'cross', 'east_drain', at=-832, width=256, height=352, link='link:cross_east'),
    opening('open:warren_outfall', 'warren', 'outfall', at=832, width=384, height=448, link='link:warren_outfall'),
    opening('open:outfall_niche', 'outfall', 'niche', at=1728, width=256, height=320, link='link:outfall_niche'),
    opening('open:outfall_shaft', 'outfall', 'jetty_shaft', at=14208, width=320, height=384, link='link:outfall_shaft'),
    opening('open:east_shaft', 'east_drain', 'jetty_shaft', at=-1152, width=320, height=384, link='link:shaft_east'),
]

CHANNEL_W = 192


def channel(rid, axis, inset=128, cid=None, centre=None):
    """A water channel down the middle of a drain: a level 48 down, inset from the end walls."""
    x0, y0, x1, y1 = R[rid][1]
    if axis == 'x':
        cy = centre if centre is not None else (y0 + y1) // 2
        o = [[x0 + inset, cy - CHANNEL_W // 2], [x1 - inset, cy - CHANNEL_W // 2], [x1 - inset, cy + CHANNEL_W // 2],
             [x0 + inset, cy + CHANNEL_W // 2]]
    else:
        cx = centre if centre is not None else (x0 + x1) // 2
        o = [[cx - CHANNEL_W // 2, y0 + inset], [cx + CHANNEL_W // 2, y0 + inset], [cx + CHANNEL_W // 2, y1 - inset],
             [cx - CHANNEL_W // 2, y1 - inset]]
    return {'id': cid or f'level:{rid}_channel', 'outline': o, 'floor': R[rid][2] - 48, 'edge': dict(ROCK),
            'surface': dict(WATER), 'notes': "Slow water down the drain, a plank walk either side."}


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


def grate_level(x, y, top, notes):
    """A round street grate in the roof: a 256 square shaft rising to `top`; off the 256 grid the picture slides by the
    remainder (a ceiling's texture starts at the map's x = 0, y = 0), so it lies once."""
    surf = dict(GRATE)
    if x % 256 or y % 256:
        surf['offset'] = [-(x % 256), (y % 256)]
    return {'outline': [[x, y], [x + 256, y], [x + 256, y + 256], [x, y + 256]], 'ceiling': top,
            'edge': dict(ROCK), 'surface': surf, 'notes': notes}


# The four cages in the cells' north side (x centres; each 384 square inside, y 1536 .. 1920 against the north wall):
# 1 Camilla, 2 Aretha, 3 Isabella asleep, 4 Rhett at the sewer end (by the drain stair, east).
CAGES = {'camilla': 4864, 'aretha': 5632, 'isabella': 6400, 'rhett': 7168}
CAGE_Y = 1728
CAGE_FRONT_Y = 1540

# The brewery's three cauldrons along its north wall (Personality, Endurance, Speed), each with its recipe skull on a
# ledge beside it.
CAULDRONS = {'personality': -1344, 'endurance': -640, 'speed': 64}
CAULDRON_Y = 4032
INIT_CAULDRON = [-128, -320]       # two steps east of the stair's foot, beside the line to the double doors

TRAPDOOR = (3328, -768)            # the sump's trapdoor, a 256 square in the roof on the grid
EXTRA = {
    'guild_landing': {
        'notes': "The top of the Guild's back stair, under the Guild's back room: the cellar door up to the square (D4) in the south wall.",
    },
    'coven_hall': {
        'platforms': [plat('platform:init_hearth', INIT_CAULDRON, [256, 256], 24, dict(FLAGS), dict(FLAGS),
                           "The initiation cauldron's low hearth, two steps from the stair's foot."),
                      plat('platform:hall_bench_s', [-1472, 128], [96, 512], 64, dict(FLAGS), dict(FLAGS),
                           "A stone bench along the west wall, south of the sigil (the coven sits for the rites)."),
                      plat('platform:hall_bench_n', [-1472, 1152], [96, 512], 64, dict(FLAGS), dict(FLAGS),
                           "A stone bench along the west wall, north of the sigil.")],
        'walls': [{'wall': 'w', 'panels': [{'id': 'panel:sigil', 'at': 'centre', 'length': 256, 'bottom': 0,
                                            'height': 512, 'surface': dict(SIGIL, fit=True),
                                            'notes': "The coven's sigil carved in the west wall."}]}],
        'notes': "Dressed 7d06 stone under block ceilings: the Guild's stair comes in from the south, the initiation cauldron on its hearth two steps east of its foot; the Moon seal's double doors north, the dormitory and the gaol east.",
    },
    'witches_walk': {'notes': "A long walk behind the double doors: the antechamber west, the brewery north."},
    'antechamber': {
        'platforms': [plat('platform:bench', [-3264, 3200], [96, 512], 64, dict(FLAGS), dict(FLAGS),
                           "A stone bench along the west wall, clear of her door.")],
        'notes': "Her door-wardens' room: a bench along the west wall; her door north.",
    },
    'head_witch': {
        'platforms': [plat('platform:witch_bed', [-3904, 4800], [384, 640], 32, dict(BEDSIDE), dict(BEDTOP),
                           "The Head Witch's bed against the west wall."),
                      plat('platform:dresser', [-2560, 5120], [384, 128], 96, dict(TABLE), dict(TABLE),
                           "Her dresser, candles on it, beside the mirror.")],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:mirror', 'offset': 1344, 'length': 192, 'bottom': 128,
                                            'height': 192, 'surface': dict(MIRROR, fit=True),
                                            'notes': "Her mirror (A6's silvered glass) in a frame of worn flags."},
                                           {'offset': 1312, 'length': 256, 'bottom': 320, 'height': 32, 'surface': dict(FLAGS)},
                                           {'offset': 1312, 'length': 256, 'bottom': 96, 'height': 32, 'surface': dict(FLAGS)},
                                           {'offset': 1312, 'length': 32, 'bottom': 128, 'height': 192, 'surface': dict(FLAGS)},
                                           {'offset': 1536, 'length': 32, 'bottom': 128, 'height': 192, 'surface': dict(FLAGS)},
                                           {'id': 'panel:witch_shelf', 'offset': 384, 'length': 256, 'bottom': 0,
                                            'height': 384, 'surface': dict(CABS),
                                            'notes': "Her shelf of books and jars."}]}],
        'notes': "The coven's north-west corner, above the cells as Naomi says: the ram-skull frieze, her bed and her chest at its foot, her mirror and dresser on the north wall; the antechamber's door south, her private door to the brewery east.",
    },
    'brewery': {
        'platforms': [plat(f'platform:hearth_{k}', [x, CAULDRON_Y], [256, 256], 24, dict(FLAGS), dict(FLAGS),
                           f"The {k} cauldron's hearth.") for k, x in CAULDRONS.items()]
        + [plat(f'platform:skull_{k}', [x + 256, 4272], [128, 96], 96, dict(FLAGS), dict(FLAGS),
                f"A ledge by the {k} cauldron with a skull on it (its recipe).") for k, x in CAULDRONS.items()],
        'notes': "Three brewing cauldrons on their hearths along the north wall, each with a talking skull on a ledge (the recipes); the walk's door south, her private door west.",
    },
    'gaol': {
        'platforms': [plat('platform:gaol_table', [1920, 1792], [512, 128], 80, dict(TABLE), dict(TABLE),
                           "The gaolers' table along the north wall.")],
        'notes': "Off the hall's east side: the gaolers' table, the prisoners' confiscated things in a locked chest; the stair down to the cells east.",
    },
    'dormitory': {
        'platforms': [plat(f'platform:bed_{i}', at, [384, 192], 32, dict(BEDSIDE), dict(BEDTOP),
                           f"A witch's bed by the wall ({i}).")
                      for i, at in enumerate([[1664, 512], [2560, 512], [2752, -768], [2112, -768]], 1)],
        'notes': "Four beds along the north and south walls; the senior witch's chest by hers; the store's door south.",
    },
    'store': {
        'store': True,
        'walls': [{'wall': 'w', 'panels': [{'id': 'panel:shelf', 'at': 'centre', 'length': 256, 'bottom': 0,
                                            'height': 384, 'surface': dict(CABS),
                                            'notes': "Shelves of jars and herbs."}]}],
        'notes': "A storeroom in dark brick: jars, sacks and a barrel pair along the walls, a shelf on the west wall; the floor hatch to the cistern in its south-east corner, bolted from this side.",
    },
    'cells': {
        'platforms': [bars([x - 188, CAGE_Y], [8, 384], f"{k.title()}'s cage: its west side of bars.") for k, x in CAGES.items()]
        + [bars([x + 188, CAGE_Y], [8, 384], f"{k.title()}'s cage: its east side of bars.") for k, x in CAGES.items()],
        'notes': "A wet rock corridor half a storey under the coven: four cages on the north side, lanterns on the south wall; the drain stair down to the sewer at the east end, past Rhett's cage.",
    },
    'slop_pit': {
        'rough': RUFF,
        'notes': "The drain stair's foot, where the coven's slops land: heaps of filth.",
    },
    'cross': {
        'pillars': [{'outline': cave(x - 64, y - 64, x + 64, y + 64, 16), 'surface': dict(ROCK)}
                    for x, y in ((9152, -576), (9792, -576), (9792, 192), (9152, 192))],
        'ceiling_levels': [grate_level(9344, -256, SEWER + 960, "The street grate over the cross.")],
        'levels': [{'id': 'level:cross_sump', 'outline': cave(9312, -352, 9632, -32, 64), 'floor': SEWER - 48,
                    'edge': dict(ROCK), 'surface': dict(WATER), 'notes': "Where the drains meet: a sump of slow water."}],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:sidedrain_n', 'offset': 1088, 'length': 128, 'bottom': 0,
                                            'height': 256, 'surface': dict(WALLGRATE, fit=True)}]},
                  {'wall': 's', 'panels': [{'id': 'panel:sidedrain_s', 'offset': 256, 'length': 128, 'bottom': 0,
                                            'height': 256, 'surface': dict(WALLGRATE, fit=True)}]}],
        'notes': "Five drains meet under the square on four piers; side drains grilled in the walls (the source's spawn points); a street grate overhead; the sump of slow water.",
    },
    'main_drain': {
        'levels': [channel('main_drain', 'x', centre=-160)],
        'ceiling_levels': [grate_level(6400, -512, SEWER + 832, "A street grate over the main drain.")],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:drain_mouth', 'offset': 1152, 'length': 128, 'bottom': 0,
                                            'height': 256, 'surface': dict(WALLGRATE, fit=True)}]}],
        'notes': "East under the square: slow water between two plank walks; a street grate overhead; the pump room's door south.",
    },
    'sump': {
        'ceiling_levels': [{'outline': [[TRAPDOOR[0], TRAPDOOR[1]], [TRAPDOOR[0] + 256, TRAPDOOR[1]],
                                        [TRAPDOOR[0] + 256, TRAPDOOR[1] + 256], [TRAPDOOR[0], TRAPDOOR[1] + 256]],
                            'ceiling': SEWER + 576, 'edge': dict(ROCK), 'surface': dict(HATCH),
                            'notes': "The trapdoor, shut fast above."}],
        'levels': [{'id': 'level:sump_puddle', 'outline': cave(3328, -1792, 3840, -1280, 96), 'floor': SEWER - 32,
                    'edge': dict(ROCK), 'surface': dict(WATER), 'notes': "Standing water at the sump's south end."}],
        'notes': "Under the square before the Guild's door: the trapdoor shut in the roof, bones of earlier wrong answers; the main drain east, the cistern west.",
    },
    'cistern': {
        'pillars': [{'outline': cave(x - 80, y - 80, x + 80, y + 80, 24), 'surface': dict(ROCK)}
                    for x, y in ((1536, -2048), (2560, -2048), (1536, -1536))],
        'levels': [{'id': 'level:cistern_water', 'outline': cave(1664, -2432, 2432, -2176, 64), 'floor': SEWER - 48,
                    'edge': dict(ROCK), 'surface': dict(WATER), 'notes': "Still water between the pillars."}],
        'notes': "The old cistern under the coven store: pillars, still water; the ladder up to the store's hatch.",
    },
    'pump_room': {
        'platforms': [plat('platform:pump', [6272, -1856], [256, 192], 192, dict(TABLE), dict(TABLE),
                           "The town's broken pump, a box of rotten planks against the south wall.")],
        'notes': "Dry behind its door: the town's broken pump and a chest left by whoever last hid here.",
    },
    'hideout': {
        'ceiling_levels': [grate_level(9472, -1792, SEWER + 832, "The second street grate, over the hideout.")],
        'notes': "A dead end under a street grate: the bones of a man who hid from the witches.",
    },
    'warren': {'rough': RUFF, 'notes': "A collapsed side vault the stalkers nest in; a chest half-sunk in their midden."},
    'east_drain': {
        'levels': [channel('east_drain', 'x', centre=-1472)],
        'notes': "From the cross east to the jetty shaft under the waterfront: slow water, plank walks.",
    },
    'outfall': {
        'rough': RUFF,
        'levels': [{'id': 'level:outfall_pool', 'outline': cave(12928, 128, 14208, 1664, 192), 'floor': SEWER - 48,
                    'edge': dict(ROCK), 'surface': dict(WATER), 'notes': "The tidal pool."}],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:lake_bars', 'offset': 1024, 'length': 256, 'bottom': 0,
                                            'height': 512, 'surface': dict(WALLGRATE, fit=True),
                                            'notes': "The barred mouth to the lake."}]}],
        'notes': "Under the jetty's root: the drains fall into a tidal pool, plank walks round it, the barred mouth to the lake north; the ledge east to the Dragon's niche, the jetty shaft south.",
    },
    'niche': {
        'walls': [{'wall': 'e', 'panels': [{'id': 'panel:alcove', 'at': 'centre', 'length': 192, 'bottom': 0,
                                            'height': 384, 'surface': dict(NICHE, fit=True),
                                            'notes': "The alcove in the rock."}]}],
        'notes': "A ledge out of sight of the walks: a dead adventurer's bones two steps short of the alcove.",
    },
    'jetty_shaft': {
        'ceiling_levels': [grate_level(14080, -1280, SEWER + 1408, "The jetty grate at the shaft's top.")],
        'walls': [{'wall': 'e', 'panels': [{'at': 'centre', 'length': 128, 'bottom': 256, 'height': 896,
                                            'surface': dict(LADDER),
                                            'notes': "The iron ladder above the exit's face, up to the jetty grate."}]}],
        'notes': "The ladder's foot in the east wall, up to D4's grate by the jetty; the outfall north, the east drain west.",
    },
}


# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s28 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-20: "huge empty brown-brick halls with a few
# cauldrons; one rock throughout the sewer"): the coven hall split by an arcade of four dressed-stone piers into the
# rite hall and an east aisle, a five-pointed star of pale flags in the rite hall's floor, shelves of jars in the hall
# and the brewery; the sewer's chambers and the cells lined with dark brick to 160 under the wet rock.
import math as _m


def _star(cx, cy, r_out=384, r_in=148):
    pts = []
    for k in range(10):
        a = _m.radians(90 + 36 * k)
        r = r_out if k % 2 == 0 else r_in
        pts.append([round(cx + r * _m.cos(a)), round(cy + r * _m.sin(a))])
    return pts


def _pier(x, y):
    return {'at': [x, y], 'size': [160, 160], 'surface': dict(COVENWALL),
            'notes': "A pier of the arcade between the rite hall and the east aisle."}


def _shelf(at, size, notes="Shelves of jars and dried herbs."):
    return plat(None, at, size, 288, dict(CABS), dict(FLAGS), notes)


EXTRA['coven_hall']['pillars'] = [_pier(320, y) for y in (-256, 384, 1024, 1664)]
EXTRA['coven_hall']['platforms'] += [
    {'id': 'platform:star', 'outline': _star(-640, 640), 'rise': 2, 'surface': dict(FLAGS), 'top_surface': dict(FLAGS),
     'notes': "The coven's five-pointed star in pale flags, in the middle of the rite hall."},
    _shelf([640, 1856], [384, 96]), _shelf([960, 640], [96, 384])]
EXTRA['coven_hall']['notes'] += (" An arcade of four piers parts the rite hall (the star in its floor, the benches, "
                                 "the sigil) from the east aisle (shelves of jars, the doors to the dormitory and gaol).")
EXTRA['brewery']['platforms'] += [_shelf([-1600, 2880], [384, 96]), _shelf([192, 2880], [384, 96])]
EXTRA['brewery']['notes'] += " Shelves of jars and herbs along the south wall."
LINING = [{'height': 160, 'surface': dict(BRICK)}]
for _t in THEMES:
    if _t['id'] in ('theme:cells', 'theme:sewer', 'theme:cave'):
        _t['bands'] = [dict(b) for b in LINING]
        _t['notes'] += " Lined with dark brick ('wall') to 160."


def room_doc(rid):
    if rid in P:
        name, path, fl, to, h, theme = P[rid]
        return {'id': 'room:' + rid, 'name': name, 'path': path, 'width': PATH_WIDTH, 'smooth': 1, 'floor': fl,
                'slope': {'to': to}, 'ceiling': max(fl, to) + h, 'ceiling_slope': {'to': to + h}, 'theme': theme,
                'notes': {'guild_stair': "The Guild's back stair, from its landing under the Guild's back room down northward into the coven hall (640 to 0).",
                          'gaol_stair': "From the gaoler's room down east to the cells (0 to -256).",
                          'drain_stair': "The drain stair from the cells' east end down to the slop pit (-256 to -512)."}[rid]}
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
    print('total', tot / 1e6, 'rooms', len(ORDER))
