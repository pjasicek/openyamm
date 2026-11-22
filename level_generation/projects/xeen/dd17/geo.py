#!/usr/bin/env python3
"""DD-17 Castle Alamar: the geometry (rooms, openings) shared by L2, L3 and L4.

One BLV of three floors 640 apart in the castle's own frame (x east, y north, z up), the gate on the south wall:
- L1, the works (0): the gatehall, the pillared Hall of Order, the two wards, the four conveyor belts north to the four
  Lava Heads, the two maintenance galleries behind them, the barracks, the moat watch, the parts store; the stair hall
  (0 to 640) and the sump (under the dial hall's chasm, reached by falling);
- L2, the dial floor (640): the outer walk round the dial hall (south walk, four corner bays, west/north/east walks), the
  four sundial alcoves behind their fields, the watchers' post, the lift core behind the true-name gate;
- the dial hall itself, from the chasm floor (0) to under the deck (1216): four concentric ring chasms in U shapes round
  the gate island on the hall's east wall; the ring walls and the island are platforms 640 high, the outer lip along the
  west wall; one bridge slab (a lift) per chasm on the west line (y 0); a radial cut through the ring walls' south arms
  lets a fallen party walk out to the sump;
- L3, the deck (1280): the trapdoor deck over the dial hall, the lift head, the robot bay, the screen room, the Hall of
  Vengeance, the Power Juice, the hatch room, the antechamber, the strongroom, Command Central.
Rooms are rectangles; walls between rooms are 128 thick.
"""

L1, L2, L3 = 0, 640, 1280
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Control Center (sci-fi.blv), the main sw set (A6's ancient kit)
TEAL = S_('swll4dk', 128, 256)        # dark teal panel wall with conduits: the main wall
REDPILOT = S_('swll5dk', 128, 256)    # dark panel with a red pilot light: the Head rooms, Command Central
FRAMED = S_('swall1', 128, 256)       # teal panel in a frame: the wards, the Hall of Order
DIAMOND = S_('swall2', 128, 256)      # diamond-brace panel: the corner bays
GRILLE = S_('swall3', 128, 256, scale=1.75)   # once up a 448 wall (a band)       # grille panel: barracks, store, robot bay
BRACED = S_('swall4', 128, 256)       # crossed-brace panel, red grime: the sump
TILED = S_('swall5', 128, 256)        # blue-teal tiled panel: the L2 walks
TUBES = S_('swll3dk', 128, 256)       # green glowing tubes: the belt halls
COLUMN = S_('swaled', 128, 256)       # machine column with blue light: the Hall of Order's pillars
MACHINE = S_('swor2', 256, 256)       # machine panel with pipes and dials: Command Central, the screen room
CABINET = S_('swpnl', 128, 256)       # computer cabinet: the screen room, the antechamber
SCREEN = S_('trekscrn', 128, 64)      # grey console face
METALFLOOR = S_('swfloor2b', 128, 128)  # dark grey metal floor
LATTICE = S_('swflora', 256, 256)     # glowing green lattice: the dial hall's chasm floor, the alcoves
TEALPLATE = S_('swankdk', 128, 128)   # teal plate floor: the deck, the L2 walks
CEIL = S_('swceilf', 256, 256)        # rust ceiling panel
BELT = S_('swr2dk', 64, 64, scale=2)  # diagonal-striped trim: the belt beds
SPIKE = S_('swr4dk', 64, 64)          # spiked trim: the lips' edges
GIRDER = S_('swgirder', 64, 64)       # riveted plate: reveals, plinths
STRIP = S_('swhorzad', 32, 32)        # blue panel strip
HULL = S_('xahull', 256, 256, scale=2.25)   # once up the hatch room's 576         # Ancient hull plating: the hatch room's shaft
ENERGY = S_('xaenergy', 128, 256)     # Ancient energy panel
FIELD = S_('xafield', 128, 256, translucent=0.5)  # the energy fields (D-51)
BLAST = S_('swdoora', 256, 256)       # heavy riveted blast door
BRACEDOOR = S_('swdoorb', 256, 256)   # cross-braced door
SEALED = S_('swtrpnl', 128, 256)      # skull-mask panel: the maintenance doors
LADDER = S_('bemv', 32, 256, uneven=True)
# the five new DD-17 textures (A8 phase 5, the lane lead's)
HEAD = S_('xalavahd', 128, 128)
HEAD_DARK = 'xalavahdx'
DIAL = S_('xasundial', 128, 128)
GLYPH = S_('xaglyph', 128, 256)
TRAPPLATE = S_('xatrapplt', 128, 128)

THEMES = [
    {'id': 'theme:works', 'wall': FRAMED, 'floor': METALFLOOR, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "L1's halls and wards: framed teal panels (swall1), dark metal floor (swfloor2b), rust ceiling panels (swceilf)."},
    {'id': 'theme:main', 'wall': TEAL, 'floor': METALFLOOR, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The main wall of the castle: dark teal panels with conduits (swll4dk)."},
    {'id': 'theme:belt', 'wall': TUBES, 'floor': BELT, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The conveyor halls: green glowing tubes along the walls (swll3dk), a striped belt bed (swr2dk)."},
    {'id': 'theme:head', 'wall': REDPILOT, 'floor': METALFLOOR, 'ceiling': CEIL, 'door': SEALED, 'reveal': GIRDER,
     'notes': "The Lava Heads' rooms: dark panels with red pilot lights (swll5dk)."},
    {'id': 'theme:store', 'wall': GRILLE, 'floor': METALFLOOR, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "Barracks, stores and bays: grille panels (swall3)."},
    {'id': 'theme:sump', 'wall': BRACED, 'floor': METALFLOOR, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The sump: crossed-brace panels with red grime (swall4)."},
    {'id': 'theme:walk', 'wall': TILED, 'floor': TEALPLATE, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The dial floor's outer walk: blue-teal tiled panels (swall5), teal plate floor (swankdk)."},
    {'id': 'theme:bay', 'wall': DIAMOND, 'floor': TEALPLATE, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The corner bays: diamond-brace panels (swall2)."},
    {'id': 'theme:dial', 'wall': TEAL, 'floor': LATTICE, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The sundial alcoves: teal walls, the glowing green lattice underfoot (swflora), an energy panel behind the dial."},
    {'id': 'theme:rings', 'wall': TEAL, 'floor': LATTICE, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The dial hall: teal walls from the chasm floor (the green lattice, swflora) to under the deck."},
    {'id': 'theme:deck', 'wall': TEAL, 'floor': TEALPLATE, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The deck and L3's halls: teal walls, teal plates underfoot."},
    {'id': 'theme:command', 'wall': REDPILOT, 'floor': METALFLOOR, 'ceiling': CEIL, 'door': BLAST, 'reveal': GIRDER,
     'notes': "Command Central and its antechamber: dark panels with red pilot lights, machine panels and screens."},
    {'id': 'theme:hull', 'wall': HULL, 'floor': METALFLOOR, 'ceiling': CEIL, 'door': BRACEDOOR, 'reveal': GIRDER,
     'notes': "The hatch room: the castle's hull plating (xahull) where the shaft rises to the roof."},
]

# id: (name, box (x0, y0, x1, y1), floor, ceiling, theme)
R = {
    # L1, the works (0)
    'gatehall': ("Gatehall", (-768, -3904, 768, -3392), L1, 448, 'theme:main'),
    'hall_order': ("Hall of Order", (-1536, -3264, 1536, -2624), L1, 512, 'theme:works'),
    'west_ward': ("West ward", (-3712, -3264, -1664, -2624), L1, 448, 'theme:works'),
    'east_ward': ("East ward", (1664, -3264, 3712, -2624), L1, 448, 'theme:works'),
    'barracks': ("Robot barracks", (-3712, -3904, -2560, -3392), L1, 448, 'theme:store'),
    'store_ne': ("Parts store", (1664, -3904, 2560, -3392), L1, 448, 'theme:store'),
    'watch_se': ("Moat watch", (2688, -3904, 3712, -3392), L1, 448, 'theme:store'),
    'belt_fire': ("Fire belt", (-2176, -2496, -1664, 768), L1, 448, 'theme:belt'),
    'belt_fire_end': ("Fire belt's end", (-2176, 896, -1664, 1664), L1, 448, 'theme:belt'),
    'head_fire': ("Fire Head", (-2944, 1792, -1664, 2560), L1, 448, 'theme:head'),
    'return_w': ("West return", (-2944, -2496, -2304, 1664), L1, 448, 'theme:main'),
    'belt_water': ("Water belt", (-3712, -2496, -3072, -896), L1, 448, 'theme:belt'),
    'belt_water_end': ("Water belt's end", (-3712, -768, -3072, 0), L1, 448, 'theme:belt'),
    'head_water': ("Water Head", (-3712, 128, -3072, 896), L1, 448, 'theme:head'),
    'belt_air': ("Air belt", (1664, -2496, 2176, 768), L1, 448, 'theme:belt'),
    'belt_air_end': ("Air belt's end", (1664, 896, 2176, 1664), L1, 448, 'theme:belt'),
    'head_air': ("Air Head", (1664, 1792, 2944, 2560), L1, 448, 'theme:head'),
    'return_e': ("East return", (2304, -2496, 2944, 1664), L1, 448, 'theme:main'),
    'belt_earth': ("Earth belt", (3072, -2496, 3712, -896), L1, 448, 'theme:belt'),
    'belt_earth_end': ("Earth belt's end", (3072, -768, 3712, 0), L1, 448, 'theme:belt'),
    'head_earth': ("Earth Head", (3072, 128, 3712, 896), L1, 448, 'theme:head'),
    'sump': ("The sump", (-1216, -2496, -256, -1984), L1, 448, 'theme:sump'),
    'stair_hall': ("Stair hall", (-128, -2496, 1152, -1984), L1, 1152, 'theme:main'),
    # L2, the dial floor (640)
    'landing_w': ("South walk, west", (-1216, -3264, 256, -2624), L2, 1152, 'theme:walk'),
    'landing': ("South walk", (384, -3264, 1920, -2624), L2, 1152, 'theme:walk'),
    'bay_sw': ("South-west bay", (-2240, -3264, -1344, -1408), L2, 1152, 'theme:bay'),
    'dial_water': ("Water Time", (-3136, -2560, -2368, -1792), L2, 1088, 'theme:dial'),
    'west_walk': ("West walk", (-2240, -1280, -1344, 1280), L2, 1152, 'theme:walk'),
    'bay_nw': ("North-west bay", (-2240, 1408, -1344, 2688), L2, 1152, 'theme:bay'),
    'dial_fire': ("Fire Time", (-3136, 1664, -2368, 2432), L2, 1088, 'theme:dial'),
    'north_walk': ("North walk", (-1216, 1984, 1920, 2688), L2, 1152, 'theme:walk'),
    'bay_ne': ("North-east bay", (2048, 1408, 2944, 2688), L2, 1152, 'theme:bay'),
    'dial_air': ("Air Time", (3072, 1664, 3840, 2432), L2, 1088, 'theme:dial'),
    'east_walk': ("East walk", (2048, -1280, 2944, 1280), L2, 1152, 'theme:walk'),
    'gazer_post': ("Watchers' post", (3072, -512, 3840, 512), L2, 1088, 'theme:store'),
    'bay_se': ("South-east bay", (2048, -3264, 2944, -1408), L2, 1152, 'theme:bay'),
    'dial_earth': ("Earth Time", (3072, -2560, 3840, -1792), L2, 1088, 'theme:dial'),
    'rings': ("Dial hall", (-1216, -1856, 1152, 1856), L1, 1216, 'theme:rings'),
    'lift_core': ("Lift core", (1280, -256, 1792, 256), L2, 1152, 'theme:main'),
    # L3, the deck (1280)
    'deck': ("Command deck", (-1216, -1856, 1152, 1856), L3, 1792, 'theme:deck'),
    'lift_top': ("Deck lift head", (1280, -256, 1792, 256), L3, 1792, 'theme:deck'),
    'robot_bay': ("Robot bay", (0, 1984, 1152, 2816), L3, 1728, 'theme:store'),
    'gazer_watch': ("Screen room", (-1216, 1984, -128, 2816), L3, 1728, 'theme:command'),
    'west_hall': ("Hall of Vengeance", (-2496, -1152, -1344, 1152), L3, 1792, 'theme:deck'),
    'juice': ("Power juice", (-3456, -512, -2624, 512), L3, 1728, 'theme:store'),
    'hatch_room': ("Hatch room", (-2496, 1280, -1344, 2304), L3, 1856, 'theme:hull'),
    'antechamber': ("Antechamber", (-2496, -2304, -1344, -1280), L3, 1728, 'theme:command'),
    'vault': ("Strongroom", (-3456, -2176, -2624, -1408), L3, 1664, 'theme:command'),
    'command': ("Command Central", (-2432, -3712, -1408, -2432), L3, 1856, 'theme:command'),
    'command_apse': ("Command Central, the throne apse", (-3072, -3456, -2560, -2688), L3, 1856, 'theme:command'),
    'command_bay': ("Command Central, the machine bay", (-1280, -3712, -704, -2432), L3, 1856, 'theme:command'),
}
FLOOR_NAME = {L1: 'L1', L2: 'L2', L3: 'L3'}
ORDER = sorted(R)

# ---------------------------------------------------------------------------------------------------- the dial hall
H_X0, H_Y0, H_X1, H_Y1 = R['rings'][1]
E = H_X1                      # the hall's east wall: the island stands against it
ISLAND = (640, -256, 1152, 256)
# offsets from the island's rectangle (west, north and south): chasm 4 (earth, innermost), ring 3, chasm 3 (fire),
# ring 2, chasm 2 (air), ring 1, chasm 1 (water, outermost); the lip along the hall's west wall beyond it
CH = {'earth': (0, 256), 'fire': (448, 704), 'air': (896, 1152), 'water': (1344, 1600)}
RINGS = [(256, 448), (704, 896), (1152, 1344)]
LIP_X = (H_X0, H_X0 + 256)    # the outer lip along the west wall (x -1216..-960)
RIM = 640                     # the ring walls', the island's and the lip's top
CUT_X = (368, 528)            # the radial cut through the ring walls' south arms (a fallen party's way out)
SUMP_MOUTH_X = -640           # the chasm 1 south arm's mouth into the sump (floor 0)


def ch_west(el):
    a, b = CH[el]
    return (ISLAND[0] - b, ISLAND[0] - a)   # x range of the chasm's west arm


def area_sign(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))


def ccw(pts):
    return pts if area_sign(pts) > 0 else pts[::-1]


def ring_pieces(a, b):
    """A ring wall between offsets a and b: a U round the island open to the east wall, cut on its south arm."""
    xi, xo = ISLAND[0] - a, ISLAND[0] - b
    yi, yo = 256 + a, 256 + b
    big = [[CUT_X[0], -yo], [CUT_X[0], -yi], [xi, -yi], [xi, yi], [E, yi], [E, yo], [xo, yo], [xo, -yo]]
    stub = [[CUT_X[1], -yo], [E, -yo], [E, -yi], [CUT_X[1], -yi]]
    return ccw(big), ccw(stub)


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
    if kw.get('in') != 'floor' and width == 'full':
        gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
        d['from_wall'] = SIDE[i]
        d['to_wall'] = SIDE[j]
    elif kw.get('in') != 'floor':
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


DOOR_W, DOOR_H = 320, 320          # single doors: swdoorb / swdoora once over a square leaf
PAIR_W, PAIR_H = 448, 448          # the blast-door pairs: one swdoora over both halves, parting in the middle
GLYPH_W, GLYPH_H = 384, 384        # the true-name gate: two hinged leaves 192 x 384 (xaglyph's 1:2)
MAINT_W, MAINT_H = 192, 384        # the maintenance doors (swtrpnl 1:2)
FIELD_W, FIELD_H = 256, 448        # the fields across the dial alcoves
PASS_W = 384
STAIR_W = 320
HEAD_D = 384

OPENINGS = [
    # L1
    opening('open:gate_hall', 'gatehall', 'hall_order', at=0, width=PAIR_W, height=PAIR_H, link='link:gate_hall'),
    opening('open:hall_ww', 'hall_order', 'west_ward', at=-2944, width=PASS_W, height=384, link='link:hall_ww'),
    opening('open:hall_ew', 'hall_order', 'east_ward', at=-2944, width=PASS_W, height=384, link='link:hall_ew'),
    opening('open:hall_stair', 'hall_order', 'stair_hall', at=128, width=PAIR_W, height=PAIR_H, link='link:hall_stair'),
    opening('open:ww_barracks', 'west_ward', 'barracks', at=-3136, width=DOOR_W, height=DOOR_H, link='link:ww_barracks'),
    opening('open:ew_store', 'east_ward', 'store_ne', at=2112, width=DOOR_W, height=DOOR_H, link='link:ew_store'),
    opening('open:ew_watch', 'east_ward', 'watch_se', at=3200, width=DOOR_W, height=DOOR_H, link='link:ew_watch'),
    opening('open:ww_bfire', 'west_ward', 'belt_fire', at=-1920, width=PASS_W, height=384, link='link:ww_bfire'),
    opening('open:ww_bwater', 'west_ward', 'belt_water', at=-3392, width=PASS_W, height=384, link='link:ww_bwater'),
    opening('open:ww_retw', 'west_ward', 'return_w', at=-2624, width=PASS_W, height=384, link='link:retw_ww'),
    opening('open:ew_bair', 'east_ward', 'belt_air', at=1920, width=PASS_W, height=384, link='link:ew_bair'),
    opening('open:ew_bearth', 'east_ward', 'belt_earth', at=3392, width=PASS_W, height=384, link='link:ew_bearth'),
    opening('open:ew_rete', 'east_ward', 'return_e', at=2624, width=PASS_W, height=384, link='link:rete_ew'),
    opening('open:bfire_end', 'belt_fire', 'belt_fire_end', width='full', height='full', link='link:bfire_end'),
    opening('open:bfire_head', 'belt_fire_end', 'head_fire', at=-1920, width=PASS_W, height=384, link='link:bfire_head'),
    opening('open:bwater_end', 'belt_water', 'belt_water_end', width='full', height='full', link='link:bwater_end'),
    opening('open:bwater_head', 'belt_water_end', 'head_water', at=-3392, width=PASS_W, height=384, link='link:bwater_head'),
    opening('open:bair_end', 'belt_air', 'belt_air_end', width='full', height='full', link='link:bair_end'),
    opening('open:bair_head', 'belt_air_end', 'head_air', at=1920, width=PASS_W, height=384, link='link:bair_head'),
    opening('open:bearth_end', 'belt_earth', 'belt_earth_end', width='full', height='full', link='link:bearth_end'),
    opening('open:bearth_head', 'belt_earth_end', 'head_earth', at=3392, width=PASS_W, height=384, link='link:bearth_head'),
    opening('open:hfire_ret', 'head_fire', 'return_w', at=-2624, width=MAINT_W, height=MAINT_H, link='link:hfire_ret'),
    opening('open:hwater_ret', 'head_water', 'return_w', at=512, width=MAINT_W, height=MAINT_H, link='link:hwater_ret'),
    opening('open:hair_ret', 'head_air', 'return_e', at=2624, width=MAINT_W, height=MAINT_H, link='link:hair_ret'),
    opening('open:hearth_ret', 'head_earth', 'return_e', at=512, width=MAINT_W, height=MAINT_H, link='link:hearth_ret'),
    opening('open:sump_stair', 'sump', 'stair_hall', at=-2240, width=DOOR_W, height=DOOR_H, link='link:sump_stair'),
    # the stair hall's head (640) onto the south walk
    opening('open:stair_up', 'stair_hall', 'landing', at=960, width=256, height=384, link='link:stair_up'),
    # the dial hall: the west walk onto the lip (640), the chasm's mouth into the sump (0), the gate (640)
    opening('open:ww_rings', 'west_walk', 'rings', at=0, width=PASS_W, height=384, link='link:ww_rings'),
    opening('open:rings_sump', 'rings', 'sump', at=SUMP_MOUTH_X, width=256, height=384, link='link:rings_sump',
            notes="The chasm's floor runs on into the sump: a fallen party walks out here."),
    opening('open:gate', 'rings', 'lift_core', at=0, width=GLYPH_W, height=GLYPH_H, link='link:island_lift',
            notes="The true-name gate from the island's top (640) into the lift core."),
    # L2's outer walk
    opening('open:land_w', 'landing_w', 'landing', width='full', height='full', link='link:land_w'),
    opening('open:land_sw', 'landing_w', 'bay_sw', at=-2944, width=PASS_W, height=384, link='link:land_sw'),
    opening('open:land_se', 'landing', 'bay_se', at=-2944, width=PASS_W, height=384, link='link:land_se'),
    opening('open:sw_ww', 'bay_sw', 'west_walk', at=-1792, width=PASS_W, height=384, link='link:sw_ww'),
    opening('open:ww_nw', 'west_walk', 'bay_nw', at=-1792, width=PASS_W, height=384, link='link:ww_nw'),
    opening('open:nw_nwalk', 'bay_nw', 'north_walk', at=2336, width=PASS_W, height=384, link='link:nw_nwalk'),
    opening('open:nwalk_ne', 'north_walk', 'bay_ne', at=2336, width=PASS_W, height=384, link='link:nwalk_ne'),
    opening('open:ne_ewalk', 'bay_ne', 'east_walk', at=2496, width=PASS_W, height=384, link='link:ne_ewalk'),
    opening('open:ewalk_se', 'east_walk', 'bay_se', at=2496, width=PASS_W, height=384, link='link:ewalk_se'),
    opening('open:ewalk_post', 'east_walk', 'gazer_post', at=0, width=DOOR_W, height=DOOR_H, link='link:ewalk_post'),
    opening('open:sw_dial', 'bay_sw', 'dial_water', at=-2176, width=FIELD_W, height=FIELD_H, link='link:sw_dial'),
    opening('open:nw_dial', 'bay_nw', 'dial_fire', at=2048, width=FIELD_W, height=FIELD_H, link='link:nw_dial'),
    opening('open:ne_dial', 'bay_ne', 'dial_air', at=2048, width=FIELD_W, height=FIELD_H, link='link:ne_dial'),
    opening('open:se_dial', 'bay_se', 'dial_earth', at=-2176, width=FIELD_W, height=FIELD_H, link='link:se_dial'),
    # L3
    opening('open:lift_deck', 'lift_top', 'deck', at=0, width=PASS_W, height=384, link='link:lift_deck'),
    opening('open:deck_bay', 'deck', 'robot_bay', at=576, width=DOOR_W, height=DOOR_H, link='link:deck_bay'),
    opening('open:deck_screen', 'deck', 'gazer_watch', at=-672, width=DOOR_W, height=DOOR_H, link='link:deck_screen'),
    opening('open:deck_west', 'deck', 'west_hall', at=0, width=768, height=448, link='link:deck_west'),
    opening('open:west_juice', 'west_hall', 'juice', at=0, width=DOOR_W, height=DOOR_H, link='link:west_juice'),
    opening('open:west_ante', 'west_hall', 'antechamber', at=-1920, width=DOOR_W, height=DOOR_H, link='link:west_ante'),
    opening('open:west_hatch', 'west_hall', 'hatch_room', at=-1920, width=DOOR_W, height=DOOR_H, link='link:west_hatch'),
    opening('open:screen_hatch', 'gazer_watch', 'hatch_room', at=2144, width=224, height=DOOR_H, link='link:screen_hatch'),
    opening('open:ante_vault', 'antechamber', 'vault', at=-1792, width=DOOR_W, height=DOOR_H, link='link:ante_vault'),
    opening('open:ante_command', 'antechamber', 'command', at=-1920, width=PAIR_W, height=PAIR_H, link='link:ante_command'),
    opening('open:command_apse', 'command', 'command_apse', width='full', height='full', link='link:command_apse'),
    opening('open:command_bay', 'command', 'command_bay', width='full', height='full', link='link:command_bay'),
]

# The lift: a floor 320 square in the lift core that rises through a hole in the lift head's floor (640 to 1280).
LIFT_AT, LIFT_SIZE = [1600, 0], [320, 320]
OPENINGS.append(opening('open:lift_shaft', 'lift_top', 'lift_core', link='link:lift_up', **{'in': 'floor'},
                        at=LIFT_AT, size=LIFT_SIZE, notes="The hole the lift rises through into the deck's lift head."))
# The deck's six trapdoors: holes over the dial hall's chasms (never over a ring wall, the island or a bridge slab).
TRAP_SIZE = 192
TRAPS = [('t1', [512, 352]), ('t2', [64, -352]), ('t3', [64, 544]), ('t4', [-384, 352]), ('t5', [-832, -352]),
         ('t6', [448, 1280])]
for key, at in TRAPS:
    OPENINGS.append(opening(f'open:trap_{key}', 'deck', 'rings', link='link:deck_drop', **{'in': 'floor'}, at=at,
                            size=[TRAP_SIZE, TRAP_SIZE], reveal=dict(GIRDER),
                            notes="A trapdoor's hole in the deck over a chasm of the dial hall (1,280 to its floor)."))
# The bridge slabs on the west line (y 0), one per chasm: lifts lying on the chasm floor, level with the rims when up.
SLAB_Y = 160
SLABS = {el: [sum(ch_west(el)) // 2, 0] for el in CH}


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


def strip(box, side, depth=HEAD_D):
    x0, y0, x1, y1 = box
    if side == 'n':
        return [[x0, y1 - depth], [x1, y1 - depth], [x1, y1], [x0, y1]]
    if side == 's':
        return [[x0, y0], [x1, y0], [x1, y0 + depth], [x0, y0 + depth]]
    if side == 'e':
        return [[x1 - depth, y0], [x1, y0], [x1, y1], [x1 - depth, y1]]
    return [[x0, y0], [x0 + depth, y0], [x0 + depth, y1], [x0, y1]]


def panel(pid, length, bottom, height, surface, notes=None, offset=None):
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


SH_BOX = R['stair_hall'][1]
HALL_PILLARS = [(x, y) for x in (-768, 768) for y in (-3136, -2752)]
# Each Head's wall: (room, wall) - the end wall opposite the belt's mouth.
HEAD_WALL = {'fire': ('head_fire', 'n'), 'water': ('head_water', 'n'), 'air': ('head_air', 'n'),
             'earth': ('head_earth', 'n')}
# The sundials: plinth centres on the 128 grid (so the dial face lies once on the plinth's top).
DIAL_AT = {'water': (-2880, -2176), 'fire': (-2880, 2048), 'air': (3328, 2048), 'earth': (3328, -2176)}
DIAL_ROOM = {'water': 'dial_water', 'fire': 'dial_fire', 'air': 'dial_air', 'earth': 'dial_earth'}
# Command Central: the dais at the west end, the throne on it.
U = 1 / 1.3     # the apse's furniture is placed in the written (enlarged) frame: dais 32 from the west wall (-4000)
DAIS = (-3712 * U, -3072)
THRONE_AT = (-3840 * U, -3072)
THRONE_BACK_X = -3920 * U
HATCH_AT = (-2240, 1792)


def rings_room():
    pl = []
    for a, b in RINGS:
        big, stub = ring_pieces(a, b)
        pl.append({'outline': big, 'rise': RIM, 'surface': dict(TEAL), 'top_surface': dict(TEALPLATE),
                   'notes': f"A ring wall between two chasms (offset {a}-{b} from the island), its top at 640."})
        pl.append({'outline': stub, 'rise': RIM, 'surface': dict(TEAL), 'top_surface': dict(TEALPLATE),
                   'notes': "The ring wall's south stub beyond the radial cut."})
    x0, y0, x1, y1 = ISLAND
    pl.append({'id': 'platform:island', 'outline': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], 'rise': RIM,
               'surface': dict(TEAL), 'top_surface': dict(METALFLOOR),
               'notes': "The gate island against the hall's east wall: the true-name gate and the crackling statue."})
    lx0, lx1 = LIP_X
    pl.append({'outline': [[lx0, H_Y0], [lx1, H_Y0], [lx1, H_Y1], [lx0, H_Y1]], 'rise': RIM, 'surface': dict(TEAL),
               'top_surface': dict(TEALPLATE), 'notes': "The outer lip along the west wall: the west walk comes in onto it."})
    return {'platforms': pl,
            'notes': "Four ring chasms round the gate island, open to the floor (0, the lattice) and up to under the deck (1216); the ring walls, the island and the lip stand 640 high; the bridge slabs (lifts) lie on the chasm floor on the west line until their dials read nine."}


EXTRA = {
    'rings': rings_room(),
    'hall_order': {'pillars': [{'at': [x, y], 'size': [128, 128], 'surface': dict(COLUMN)} for x, y in HALL_PILLARS],
                   'notes': "The pillared Hall of Order: four machine columns either side of the way from the gate to the stair hall's leaves; the wards west and east."},
    'stair_hall': {
        'platforms': [{'id': 'platform:stair_head', 'rise': 32, 'base': L2 - L1 - 32, 'outline': strip(SH_BOX, 'e'),
                       'surface': dict(TEAL), 'top_surface': dict(TEALPLATE), 'bottom_surface': dict(METALFLOOR),
                       'notes': "The stair's head (640) along the east wall: the south walk through its south wall."}],
        'flights': [{'from': [64, -2208], 'to': [768, -2208], 'to_height': L2, 'width': STAIR_W, 'steps': 20,
                     'open_below': 32, 'sides': {'height': 48, 'thickness': 16, 'surface': dict(GIRDER)},
                     'notes': "Twenty steps of 32 up the north wall, rising east to the head."}],
        'notes': "Two storeys behind the Hall of Order's leaves: the stair up the north wall to the head (640) and the south walk; the sump's door in the west wall.",
    },
    'lift_core': {'notes': "Behind the true-name gate: the lift up to the deck (it runs once the gate is open)."},
    'lift_top': {'notes': "The lift's head on the deck's east side."},
}


# session 17: the propaganda statues' girder plinths gone: xeen_statue_teal stands on its own steel plinth
FURNISH = {
    'command': {'platforms': [
        plat(None, [-1920, -3648], [512, 64], 128, dict(SCREEN, scale=2), dict(GIRDER), "A console of screens.",
             end_surface=dict(GIRDER, fit=False))]},
    'command_bay': {'platforms': [
        plat(None, [-768, -3072], [64, 512], 128, dict(SCREEN, scale=2), dict(GIRDER), "A console of screens.",
             end_surface=dict(GIRDER, fit=False))]},
    'command_apse': {'platforms': [
        plat('platform:dais', [DAIS[0], DAIS[1]], [512, 640], 32, dict(GIRDER), dict(METALFLOOR),
             "The dais at Command Central's west end."),
        # session 17: the girder seat and back gone; Sheltem's throne is S's xeen_throne_steel (dress.py DECOS)
        ],
        'walls': [{'wall': 'w', 'panels': [panel('panel:screens', 256, 448, 256, dict(MACHINE, fit=True),
                                                 "The bank of machines over the throne.")]}]},
    'gazer_watch': {'platforms': [
        plat('platform:console_screen', [-672, 2752], [512, 64], 128, dict(SCREEN, scale=2), dict(GIRDER),
             "A console of screens against the north wall, showing the Forbidden Zone.", end_surface=dict(GIRDER, fit=False)),
        plat(None, [-1152, 2400], [64, 512], 128, dict(SCREEN, scale=2), dict(GIRDER), "A console of screens.",
             end_surface=dict(GIRDER, fit=False))]},
    'antechamber': {'walls': [{'wall': 'e', 'panels': [panel(None, 128, 64, 256, dict(CABINET, fit=True), "A cabinet.")]}]},
    'juice': {'platforms': [plat('platform:juice', [-3328, 0], [128, 256], 160, dict(CABINET, fit=False), dict(GIRDER),
                                 "The dispenser labelled XEEN Power Juice.", end_surface=dict(GIRDER, fit=False))]},
    'hatch_room': {
        'platforms': [plat('platform:hatch', [HATCH_AT[0], HATCH_AT[1]], [256, 256], 16, dict(HULL), dict(HULL),
                           "The roof hatch in the shaft's ceiling, over the ladder's top.", base=1856 - 1280 - 16,
                           bottom_surface=dict(HULL))],
        'walls': [{'wall': 'w', 'panels': [panel('panel:ladder', 64, 0, 576, dict(LADDER),
                                                 "The ladder up the shaft to the roof hatch.")]}]},
}
for el, (x, y) in DIAL_AT.items():
    FURNISH.setdefault(DIAL_ROOM[el], {})['platforms'] = [
        plat(f'platform:dial_{el}', [x, y], [128, 128], 96, dict(GIRDER), dict(DIAL),
             f"The {el} sundial on its plinth (xasundial, once on the top).", end_surface=dict(GIRDER, fit=False))]
    room = DIAL_ROOM[el]
    wall = 'w' if el in ('water', 'fire') else 'e'
    FURNISH[room]['walls'] = [{'wall': wall, 'panels': [panel(None, 256, 64, 512, dict(ENERGY, fit=True),
                                                             "The energy panel behind the dial.")]}]
for el, (room, wall) in HEAD_WALL.items():
    FURNISH.setdefault(room, {})['walls'] = [{'wall': wall, 'panels': [
        panel(None, 128, 32, 256, dict(ENERGY, fit=True), "An energy panel.", offset=None if False else 160),
        panel(f'panel:head_{el}', 256, 64, 256, dict(HEAD, fit=True), f"The {el} Lava Head."),
    ]}]


def _fix_head_panels():
    # the head panel in the middle of the end wall, an energy panel either side
    for el, (room, wall) in HEAD_WALL.items():
        x0, y0, x1, y1 = R[room][1]
        length = (x1 - x0) if wall in ('n', 's') else (y1 - y0)
        mid = length // 2
        FURNISH[room]['walls'] = [{'wall': wall, 'panels': [
            panel(None, 128, 32, 256, dict(ENERGY, fit=True), "An energy panel.", offset=mid - 128 - 64 - 128),
            panel(f'panel:head_{el}', 256, 64, 256, dict(HEAD, fit=True), f"The {el} Lava Head.", offset=mid - 128),
            panel(None, 128, 32, 256, dict(ENERGY, fit=True), "An energy panel.", offset=mid + 128 + 64),
        ]}]


_fix_head_panels()


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
