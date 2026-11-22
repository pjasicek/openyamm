#!/usr/bin/env python3
"""DD-15 Great Pyramid: the geometry (rooms, openings) shared by L2, L3 and L4.

One BLV of four stepped floors 768 apart (x east, y north, z up), each smaller than the one below:
- L1, the Royal Pyramid (0): the entrance hall inside the green doors (north), Reception and Information either side,
  the four torch chapels in the corners, the Visitor's Atrium in the middle (four sectors), the ring round it (the
  west gallery, the south gallery, the number hall), the Overseer's Office and vault, the grand stair behind the torch
  door and the Pharaoh's lift shaft beside it;
- L2, the registry level (768): the stair head, the processional of the four verse statues (three sectors) to the
  registry door, the west and east tombs, the north cloister, the embalmers' room, the registry stair up;
- L3, the pad maze (1536, the Ancient kit): the maze landing, the pad hall (three sectors) with four pads, the five
  sealed cells (sun, eye, scarab, bird, far), the apex stair up from the far cell;
- L4, the Pharaoh's apartments (2304): the apex landing, the antechamber (two sectors, the lift's top), the throne
  hall under the apex (three sectors), the bedchamber, the sky corridor behind the throne.
The two-storey rooms carry the stairs (DD-14's way: a hanging head platform at the upper floor and one flight up to
it). Rooms are rectangles (the sky corridor an L); walls between rooms are 128 thick; split halls touch (no wall) and
open on their whole length. The inside is independent of the outside (D-49 Q6).
"""

L1, L2, L3, L4 = 0, 768, 1536, 2304
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Tomb of VARN (pyramid.blv)
BIGA = S_('egybiga', 256, 256)      # big sandstone blocks: the public halls
BIGB = S_('egybigb', 256, 256)      # big blocks, darker: stairs, benches, plinths
WLA = S_('egywla', 256, 256)        # small blocks: the number hall
WLC = S_('egywlc', 128, 256)        # gold plaster: the Pharaoh's rooms
WLD = S_('egywld', 256, 256)        # orange hieroglyph wall: the torch chapels
WLE = S_('egywle', 128, 128)        # orange hieroglyph tiles: the tombs
WLF = S_('egywlf', 256, 256)        # gold hieroglyph columns: the atrium
WLH = S_('egywlh', 256, 256, scale=2)   # plaster between two hieroglyph friezes, once up a 512 wall: the processional
WLJ = S_('egywlj', 256, 256)        # cracked plaster: the Overseer's rooms, the embalmers
WALG1 = S_('egywalg1', 256, 256)    # coursed blocks: Reception and Information
MEDA = S_('egymeda', 256, 256)      # dressed blocks: the galleries
FLORA = S_('egyflora', 128, 128)    # blue tiles in white: the Pharaoh's floors
FLORB = S_('egyflorb', 128, 128)    # a winged relief: sarcophagus lids, the bird pads
FLORC = S_('egyflorc', 128, 128)    # pale flags: the chapels
FLORD = S_('egyflord', 256, 256)    # sand-coloured slabs: the halls
FLORE = S_('egyflore', 256, 256)    # pale slabs: the atrium, the processional
FLORF = S_('egyflorf', 256, 256)    # marbled slabs: the offices, the tombs
CEILA = S_('egyceila', 128, 128)    # inlaid wood: desks, the bed
CEILB = S_('egyceilb', 128, 128)    # block ceiling
CEILD = S_('egyceild', 128, 128)    # a coffered ceiling of blocks in beams
WALGM = S_('egywalgm', 128, 128)    # smooth sand plaster: sarcophagi, tables, stands
TRMC = S_('egytrmc', 64, 64)        # hieroglyph trim: doorway reveals
COL64 = S_('egycol64', 64, 256)     # a carved column
DRSMC = S_('egydrsmc', 128, 256)    # a relief door: single doors
DRSMD = S_('egydrsmd', 128, 256)    # a carved slab door: the registry's bronze door
DRSML = S_('egydrsml', 128, 256)    # Horus, left wing
DRSMR = S_('egydrsmr', 128, 256)    # Horus, right wing
DRLGL = S_('egydrlgl', 256, 256)    # the seated Pharaoh: the throne hall's left leaf
DRLGR = S_('egydrlgr', 256, 256)    # the queen: its right leaf
NICHE_A = S_('egywlspa', 256, 256)  # a niche of two jackal-headed figures
NICHE_B = S_('egywlspb', 256, 256)  # a niche of three figures
NICHE_C = S_('egyspca', 256, 256)   # a niche of three figures, columns either side
TAPESTRY = S_('egywlspc', 256, 256) # a painted tableau: the tapestry
PLAQUE = S_('egywlhle', 128, 256)   # a hieroglyph-framed tablet: the torch plaque
SWOFF = S_('egyswbof', 32, 32)      # the torch lever's eye, dark
SWON = S_('egyswbon', 32, 32)       # lit
PYRDOR = S_('xdpyrdor', 128, 256)   # A6's green pyramid door (one wing; mirrored on the right leaf)
REGPLQ = S_('xdregplq', 128, 64)    # the brass registry plaque (new, A8 phase 5)
GOLD = S_('xngold5', 256, 256)      # gilding: the throne, the dais
GRILLE = S_('xwcage', 128, 256)     # cage bars (D-22.1): the cage's gate
# The Ancient kit (sw set): L3 and the sky corridor
SWWALL = S_('swll4dk', 128, 256)
SWFLOOR = S_('swfloor2b', 128, 128)
SWCEIL = S_('swceilf', 256, 256)
SWDOOR = S_('swdoorc', 128, 256)
SWJAMB = S_('swankdk', 128, 128)
SWSKY = S_('swdoora', 256, 256)     # the sky door
SWPANEL = S_('swpnl', 128, 256)     # a wall console: the weapon rack's frame
SCREEN = S_('trekscrn', 128, 64)    # a screen: the Overseer's lost map
PAD_SUN = S_('swcirc1', 256, 256)
PAD_SCARAB = S_('swfloor6', 256, 256)
PAD_BACK = S_('swcirc2', 256, 256)
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}

THEMES = [
    {'id': 'theme:hall', 'wall': BIGA, 'floor': FLORD, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The Royal Pyramid's public halls (MM6's Tomb of VARN): big sandstone blocks (egybiga), sand slabs (egyflord), block ceilings (egyceilb), hieroglyph trim in the doorways (egytrmc)."},
    {'id': 'theme:reception', 'wall': WALG1, 'floor': FLORD, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "Reception and Information: coursed blocks (egywalg1)."},
    {'id': 'theme:atrium', 'wall': WLF, 'floor': FLORE, 'ceiling': CEILD, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The Visitor's Atrium: gold hieroglyph columns (egywlf), pale slabs (egyflore), a coffered ceiling (egyceild)."},
    {'id': 'theme:chapel', 'wall': WLD, 'floor': FLORC, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The four torch chapels: orange hieroglyph walls (egywld), pale flags (egyflorc); the niches (egywlspa/egywlspb)."},
    {'id': 'theme:gallery', 'wall': MEDA, 'floor': FLORD, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The galleries round the atrium: dressed blocks (egymeda)."},
    {'id': 'theme:numbers', 'wall': WLA, 'floor': FLORD, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The number hall: small blocks (egywla); the eight niches (egyspca)."},
    {'id': 'theme:office', 'wall': WLJ, 'floor': FLORF, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The Overseer's Office and vault, the embalmers' room: cracked plaster (egywlj), marbled slabs (egyflorf)."},
    {'id': 'theme:stair', 'wall': BIGB, 'floor': FLORD, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The stairs, the porch and the lift shaft: big blocks (egybigb)."},
    {'id': 'theme:processional', 'wall': WLH, 'floor': FLORE, 'ceiling': CEILD, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The processional and the registry: plaster between two hieroglyph friezes (egywlh, once up the wall), pale slabs, coffers."},
    {'id': 'theme:tomb', 'wall': WLE, 'floor': FLORF, 'ceiling': CEILB, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The tombs and the cloister: orange hieroglyph tiles (egywle), marbled slabs."},
    {'id': 'theme:ancient', 'wall': SWWALL, 'floor': SWFLOOR, 'ceiling': SWCEIL, 'door': SWDOOR, 'reveal': SWJAMB,
     'notes': "The Ancients' levels (A6's assign: the lower Ancient levels in the sw set): steel panels (swll4dk), worn grey floor (swfloor2b), a grated ceiling (swceilf); L3's pad maze, the apex stair and the sky corridor."},
    {'id': 'theme:royal', 'wall': WLC, 'floor': FLORA, 'ceiling': CEILD, 'door': DRSMC, 'reveal': TRMC,
     'notes': "The Pharaoh's apartments: gold plaster (egywlc), blue tiles in white (egyflora), coffers; xngold5 gilding on the dais and the throne."},
]

# id: (name, box or outline, floor, ceiling, theme)
R = {
    # L1, the Royal Pyramid (0)
    'porch': ("Porch", (-384, 5248, 384, 5504), L1, L1 + 512, 'theme:stair'),
    'entry': ("Entrance hall", (-1280, 2944, 1280, 5120), L1, L1 + 640, 'theme:hall'),
    'reception': ("Reception", (-4608, 1152, -1408, 3456), L1, L1 + 512, 'theme:reception'),
    'information': ("Information", (1408, 1152, 4608, 3456), L1, L1 + 512, 'theme:reception'),
    'chapel_nw': ("North-west chapel", (-4608, 3584, -3072, 5120), L1, L1 + 512, 'theme:chapel'),
    'chapel_ne': ("North-east chapel", (3072, 3584, 4608, 5120), L1, L1 + 512, 'theme:chapel'),
    'atrium_nw': ("Visitor's Atrium", (-1280, 768, 0, 2816), L1, L1 + 640, 'theme:atrium'),
    'atrium_ne': ("Visitor's Atrium", (0, 768, 1280, 2816), L1, L1 + 640, 'theme:atrium'),
    'atrium_sw': ("Visitor's Atrium", (-1280, -1280, 0, 768), L1, L1 + 640, 'theme:atrium'),
    'atrium_se': ("Visitor's Atrium", (0, -1280, 1280, 768), L1, L1 + 640, 'theme:atrium'),
    'west_gal_n': ("West gallery", (-3584, -640, -2048, 1024), L1, L1 + 512, 'theme:gallery'),
    'west_gal_s': ("West gallery", (-3584, -2304, -2048, -640), L1, L1 + 512, 'theme:gallery'),
    'chapel_sw': ("South-west chapel", (-3584, -3712, -2048, -2432), L1, L1 + 512, 'theme:chapel'),
    'south_gal_w': ("South gallery", (-1920, -3200, 0, -1408), L1, L1 + 512, 'theme:gallery'),
    'south_gal_e': ("South gallery", (0, -3200, 1920, -1408), L1, L1 + 512, 'theme:gallery'),
    'chapel_se': ("South-east chapel", (2048, -3712, 3584, -2432), L1, L1 + 512, 'theme:chapel'),
    'number_s': ("Number hall", (2048, -2304, 3584, -640), L1, L1 + 512, 'theme:numbers'),
    'number_n': ("Number hall", (2048, -640, 3584, 1024), L1, L1 + 512, 'theme:numbers'),
    'overseer': ("Overseer's Office", (3712, -3712, 4736, -2560), L1, L1 + 512, 'theme:office'),
    'vault': ("Overseer's vault", (3712, -4864, 4736, -3840), L1, L1 + 448, 'theme:office'),
    'stair_foot': ("Grand stair", (-1920, -4864, -128, -3328), L1, L2 + 512, 'theme:stair'),
    'shaft': ("Pharaoh's lift", (0, -3840, 512, -3328), L1, L4 + 512, 'theme:stair'),
    # L2, the registry level (768)
    'landing': ("Stair head", (-1920, -3200, -128, -2176), L2, L2 + 512, 'theme:processional'),
    'proc_1': ("Processional", (-1536, -2048, -256, -512), L2, L2 + 512, 'theme:processional'),
    'proc_2': ("Processional", (-1536, -512, -256, 1024), L2, L2 + 512, 'theme:processional'),
    'proc_3': ("Processional", (-1536, 1024, -256, 2560), L2, L2 + 512, 'theme:processional'),
    'registry': ("Registry door", (-1536, 2688, -256, 3712), L2, L2 + 512, 'theme:processional'),
    'registry_stair': ("Registry stair", (-3072, 1280, -1664, 3712), L2, L3 + 512, 'theme:stair'),
    'tomb_w': ("West tomb", (-3712, -1792, -1664, 1152), L2, L2 + 512, 'theme:tomb'),
    'tomb_e': ("East tomb", (-128, -512, 1792, 1536), L2, L2 + 512, 'theme:tomb'),
    'cloister_s': ("North cloister", (-128, 1664, 1792, 2688), L2, L2 + 512, 'theme:tomb'),
    'cloister_n': ("North cloister", (-128, 2688, 1792, 3712), L2, L2 + 512, 'theme:tomb'),
    'embalmers': ("Embalmers' room", (-3584, -3200, -2048, -2048), L2, L2 + 448, 'theme:office'),
    # L3, the pad maze (1536)
    'maze_landing': ("Maze landing", (-1536, 1280, -256, 2304), L3, L3 + 512, 'theme:ancient'),
    'pad_w': ("Pad hall", (-1536, -1280, -384, 1152), L3, L3 + 512, 'theme:ancient'),
    'pad_c': ("Pad hall", (-384, -1280, 768, 1152), L3, L3 + 512, 'theme:ancient'),
    'pad_e': ("Pad hall", (768, -1280, 1920, 1152), L3, L3 + 512, 'theme:ancient'),
    'cell_a': ("Cell of the sun", (-2944, -1280, -1920, -256), L3, L3 + 448, 'theme:ancient'),
    'cell_b': ("Cell of the eye", (2176, -1280, 3200, -256), L3, L3 + 448, 'theme:ancient'),
    'cell_c': ("Cell of the scarab", (2176, 128, 3200, 1152), L3, L3 + 448, 'theme:ancient'),
    'cell_d': ("Cell of the bird", (-384, -2688, 640, -1664), L3, L3 + 448, 'theme:ancient'),
    'cell_e': ("Far cell", (1024, -2688, 2048, -1664), L3, L3 + 448, 'theme:ancient'),
    'apex_stair': ("Apex stair", (2176, -2688, 3072, -1408), L3, L4 + 512, 'theme:ancient'),
    # L4, the Pharaoh's apartments (2304)
    'apex_landing': ("Apex landing", (2176, -1280, 3072, -256), L4, L4 + 512, 'theme:royal'),
    'ante_s': ("Antechamber", (-640, -3200, 2048, -1984), L4, L4 + 640, 'theme:royal'),
    'ante_n': ("Antechamber", (-640, -1984, 2048, -768), L4, L4 + 640, 'theme:royal'),
    'throne_s': ("Throne hall", (-1536, -640, 1536, 256), L4, L4 + 896, 'theme:royal'),
    'throne_c': ("Throne hall", (-1536, 256, 1536, 1152), L4, L4 + 896, 'theme:royal'),
    'throne_n': ("Throne hall", (-1536, 1152, 1536, 2048), L4, L4 + 896, 'theme:royal'),
    'bedchamber': ("Bedchamber", (1664, 1152, 2944, 2688), L4, L4 + 512, 'theme:royal'),
    'sky_corridor': ("Sky door", [[-384, 2176], [1536, 2176], [1536, 2688], [384, 2688], [384, 3200], [-384, 3200]],
                     L4, L4 + 448, 'theme:ancient'),
}
FLOOR_NAME = {L1: 'L1', L2: 'L2', L3: 'L3', L4: 'L4'}
ORDER = sorted(R)


def outline(rid):
    b = R[rid][1]
    if isinstance(b, list):
        return [list(p) for p in b]
    x0, y0, x1, y1 = b
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def bbox(rid):
    o = outline(rid)
    xs, ys = [p[0] for p in o], [p[1] for p in o]
    return min(xs), min(ys), max(xs), max(ys)


def walls_of(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


SIDE4 = {0: 's', 1: 'e', 2: 'n', 3: 'w'}


def side_name(rid, i):
    return SIDE4[i] if len(outline(rid)) == 4 else i


def shared(a, b, touching=False):
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
            if hi - lo <= 0 or gap > 512 or (gap == 0) != touching:
                continue
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            nx, ny = dy, -dx      # the outward normal of a counter-clockwise outline
            if not touching:
                if ax == 1 and (q0[0] - p0[0]) * nx <= 0:
                    continue
                if ax == 0 and (q0[1] - p0[1]) * ny <= 0:
                    continue
            else:
                # touching: b must lie on the outer side of a's wall
                cb = bbox(b)
                mid = ((cb[0] + cb[2]) / 2 - p0[0], (cb[1] + cb[3]) / 2 - p0[1])
                if mid[0] * nx + mid[1] * ny <= 0:
                    continue
            cand = (gap, i, j, lo, hi, ax, p0, p1)
            if best is None or gap < best[0]:
                best = cand
    if best is None:
        raise SystemExit(f'no facing walls between {a} and {b}')
    return best


def opening(oid, a, b, at=None, width=256, height=384, link=None, **kw):
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b}
    full = width == 'full'
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b, touching=full)
    if not full:
        if at is None:
            at = (lo + hi) / 2
        if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
            raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
        forward = (p1[ax] - p0[ax]) > 0
        along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
        if along != 0.5:
            d['along'] = along
    d['from_wall'] = side_name(a, i)
    d['to_wall'] = side_name(b, j)
    if link:
        d['link'] = link
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


DOOR_W, DOOR_H = 192, 384          # single doors (128 x 256 pictures at 1.5)
DOUBLE_W, DOUBLE_H = 448, 448      # double doors: each leaf 224 x 448 (the 128 x 256 wing's 1:2)
GREAT_W, GREAT_H = 768, 384        # the throne hall's great doors: each leaf 384 square (egydrlgl/egydrlgr)
PASS_W = 512                       # open passages
HEAD_D = 384                       # a stair head's depth
STAIR_W = 320

OPENINGS = [
    # L1
    opening('open:green', 'entry', 'porch', at=0, width=DOUBLE_W, height=DOUBLE_H, link='link:green',
            notes="The green doors (two leaves of A6's xdpyrdor) on the entrance hall's north wall."),
    opening('open:entry_reception', 'entry', 'reception', at=3200, width=DOOR_W, height=DOOR_H,
            link='link:entry_reception'),
    opening('open:entry_information', 'entry', 'information', at=3200, width=DOOR_W, height=DOOR_H,
            link='link:entry_information'),
    opening('open:entry_atrium_w', 'entry', 'atrium_nw', at=-576, width=640, height=448, link='link:entry_atrium',
            notes="Into the atrium, west of the middle pier."),
    opening('open:entry_atrium_e', 'entry', 'atrium_ne', at=576, width=640, height=448, link='link:entry_atrium',
            notes="Into the atrium, east of the middle pier."),
    opening('open:atrium_n', 'atrium_nw', 'atrium_ne', width='full', height='full'),
    opening('open:atrium_s', 'atrium_sw', 'atrium_se', width='full', height='full'),
    opening('open:atrium_w', 'atrium_nw', 'atrium_sw', width='full', height='full'),
    opening('open:atrium_e', 'atrium_ne', 'atrium_se', width='full', height='full'),
    opening('open:chapel_nw', 'reception', 'chapel_nw', at=-3840, width=DOUBLE_W, height=DOUBLE_H,
            link='link:reception_chapel_nw'),
    opening('open:chapel_ne', 'information', 'chapel_ne', at=3840, width=DOUBLE_W, height=DOUBLE_H,
            link='link:information_chapel_ne'),
    opening('open:reception_west', 'reception', 'west_gal_n', at=-2816, width=PASS_W, height=384,
            link='link:reception_west'),
    opening('open:west_gal', 'west_gal_n', 'west_gal_s', width='full', height='full'),
    opening('open:west_chapel_sw', 'west_gal_s', 'chapel_sw', at=-2816, width=PASS_W, height=384,
            link='link:west_chapel_sw'),
    opening('open:chapel_sw_south', 'chapel_sw', 'south_gal_w', at=-2816, width=384, height=384,
            link='link:chapel_sw_south'),
    opening('open:south_gal', 'south_gal_w', 'south_gal_e', width='full', height='full'),
    opening('open:south_chapel_se', 'south_gal_e', 'chapel_se', at=-2816, width=384, height=384,
            link='link:south_chapel_se'),
    opening('open:south_atrium', 'south_gal_w', 'atrium_sw', at=-640, width=DOUBLE_W, height=DOUBLE_H,
            link='link:south_atrium'),
    opening('open:stair', 'south_gal_w', 'stair_foot', at=-1024, width=DOUBLE_W, height=DOUBLE_H,
            link='link:atrium_stair', notes="The stair door: two leaves of xdpyrdor, shut until the four torches burn."),
    opening('open:chapel_se_numbers', 'chapel_se', 'number_s', at=2816, width=PASS_W, height=384,
            link='link:chapel_se_numbers'),
    opening('open:numbers', 'number_s', 'number_n', width='full', height='full'),
    opening('open:numbers_information', 'number_n', 'information', at=2496, width=DOOR_W, height=DOOR_H,
            link='link:numbers_information'),
    opening('open:overseer', 'chapel_se', 'overseer', at=-3136, width=DOOR_W, height=DOOR_H, link='link:west_overseer'),
    opening('open:vault', 'overseer', 'vault', at=4224, width=DOOR_W, height=DOOR_H, link='link:overseer_vault'),
    # the grand stair (0 to 768) and the lift
    opening('open:lift_foot', 'stair_foot', 'shaft', at=-3584, width=384, height=384, link='link:stair_liftfoot',
            notes="The gilded cage's mouth at the foot (L1)."),
    opening('open:stair_head', 'stair_foot', 'landing', at=-640, width=384, height=384, link='link:stair_l2',
            notes="The grand stair's head (768) onto L2's stair head."),
    opening('open:lift_top', 'shaft', 'ante_s', at=256, width=384, height=384, link='link:lift',
            notes="The cage's gate at the top (L4): shut while the cage is down."),
    # L2
    opening('open:landing_proc', 'landing', 'proc_1', at=-896, width=PASS_W, height=384, link='link:landing_processional'),
    opening('open:proc_12', 'proc_1', 'proc_2', width='full', height='full'),
    opening('open:proc_23', 'proc_2', 'proc_3', width='full', height='full'),
    opening('open:proc_registry', 'proc_3', 'registry', at=-896, width=PASS_W, height=384,
            link='link:processional_registry'),
    opening('open:registry', 'registry', 'registry_stair', at=3200, width=DOOR_W, height=DOOR_H,
            link='link:registry_door', notes="The bronze registry door: its lock asks 'Registry?'."),
    opening('open:tomb_w', 'proc_2', 'tomb_w', at=256, width=DOUBLE_W, height=DOUBLE_H, link='link:processional_tomb_w'),
    opening('open:tomb_e', 'proc_2', 'tomb_e', at=256, width=DOUBLE_W, height=DOUBLE_H, link='link:processional_tomb_e'),
    opening('open:tomb_e_cloister', 'tomb_e', 'cloister_s', at=832, width=PASS_W, height=384, link='link:tomb_e_cloister'),
    opening('open:cloister', 'cloister_s', 'cloister_n', width='full', height='full'),
    opening('open:cloister_registry', 'cloister_n', 'registry', at=3200, width=DOOR_W, height=DOOR_H,
            link='link:cloister_registry'),
    opening('open:embalmers', 'landing', 'embalmers', at=-2688, width=DOOR_W, height=DOOR_H, link='link:landing_embalmers'),
    # the registry stair (768 to 1536)
    opening('open:registry_head', 'registry_stair', 'maze_landing', at=1472, width=256, height=384,
            link='link:registry_up', notes="The registry stair's head (1536) onto the maze landing."),
    # L3
    opening('open:landing_pads', 'maze_landing', 'pad_w', at=-960, width=PASS_W, height=384, link='link:landing_pads'),
    opening('open:pad_wc', 'pad_w', 'pad_c', width='full', height='full'),
    opening('open:pad_ce', 'pad_c', 'pad_e', width='full', height='full'),
    opening('open:apex', 'cell_e', 'apex_stair', at=-2432, width=DOOR_W, height=DOOR_H, link='link:apex_door',
            notes="The apex stair's door from the far cell."),
    opening('open:apex_head', 'apex_stair', 'apex_landing', at=2624, width=384, height=384, link='link:stair_l4',
            notes="The apex stair's head (2304) onto the apex landing."),
    # L4
    opening('open:ante', 'apex_landing', 'ante_n', at=-1024, width=DOOR_W, height=DOOR_H, link='link:apex_ante'),
    opening('open:ante_sn', 'ante_s', 'ante_n', width='full', height='full'),
    opening('open:throne', 'ante_n', 'throne_s', at=448, width=GREAT_W, height=GREAT_H, link='link:ante_throne',
            notes="The throne hall's great doors: two leaves, the seated Pharaoh (egydrlgl) and his queen (egydrlgr)."),
    opening('open:throne_sc', 'throne_s', 'throne_c', width='full', height='full'),
    opening('open:throne_cn', 'throne_c', 'throne_n', width='full', height='full'),
    opening('open:bedchamber', 'throne_n', 'bedchamber', at=1600, width=DOOR_W, height=DOOR_H, link='link:throne_bed'),
    opening('open:throne_sky', 'throne_n', 'sky_corridor', at=1024, width=384, height=384, link='link:throne_sky',
            notes="Behind the throne, east of the dais: the sky corridor."),
    opening('open:bed_sky', 'bedchamber', 'sky_corridor', at=2432, width=DOOR_W, height=DOOR_H, link='link:bed_sky',
            notes="The secret way from the bedchamber, opened by the carved button."),
]


def strip(box, side, depth=HEAD_D):
    x0, y0, x1, y1 = box
    if side == 'n':
        return [[x0, y1 - depth], [x1, y1 - depth], [x1, y1], [x0, y1]]
    if side == 's':
        return [[x0, y0], [x1, y0], [x1, y0 + depth], [x0, y0 + depth]]
    if side == 'e':
        return [[x1 - depth, y0], [x1, y0], [x1, y1], [x1 - depth, y1]]
    return [[x0, y0], [x0 + depth, y0], [x0 + depth, y1], [x0, y1]]


def head(pid, outline_, floor, top, surface, top_surface, notes):
    return {'id': pid, 'rise': 32, 'base': top - floor - 32, 'outline': outline_, 'surface': dict(surface),
            'top_surface': dict(top_surface), 'bottom_surface': dict(surface), 'notes': notes}


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


def pillar(x, y, s, surface):
    h = s // 2
    return {'outline': [[x - h, y - h], [x + h, y - h], [x + h, y + h], [x - h, y + h]], 'surface': dict(surface)}


SF_BOX = R['stair_foot'][1]
RS_BOX = R['registry_stair'][1]
AS_BOX = R['apex_stair'][1]

# The Pharaoh's throne on its dais at the throne hall's north end, the Brew of Pure Power beside it.
THRONE_AT = (-384, 1856)
DAIS = [-384, 1728]
VAT_AT = [512, 1664]
# The atrium's four braziers (cold until their torch is lit).
BRAZIERS = {'ne': [896, 2432], 'nw': [-896, 2432], 'sw': [-896, -896], 'se': [896, -896]}
# The processional's four verse statues (aaze0084:1-4), on plinths by the walls.
VERSES = [('verse_1', 'proc_1', [-1408, -1280]), ('verse_2', 'proc_2', [-384, -128]),
          ('verse_3', 'proc_3', [-1408, 1408]), ('verse_4', 'proc_3', [-384, 2176])]
# The pads (256 square plates): in the hall and in the cells.
PADS = {
    'sun': ('pad_w', [-960, -640], PAD_SUN),
    'eye': ('pad_c', [128, -640], dict(SWOFF, scale=8)),
    'scarab': ('pad_e', [1344, -640], PAD_SCARAB),
    'bird': ('pad_c', [128, 640], dict(FLORB, scale=2)),
}

EXTRA = {
    'entry': {'notes': "Inside the green doors: a hall of big sandstone blocks, the welcome statue in its niche on the west wall, two arches south into the atrium; Reception west, Information east."},
    'reception': {'platforms': [
                                plat(None, [-4480, 1856], [96, 512], 48, dict(BIGB), dict(BIGB), "A visitors' bench."),
                                plat(None, [-4480, 2752], [96, 512], 48, dict(BIGB), dict(BIGB), "A visitors' bench.")],
                  'notes': "Visitors' benches by the west wall, the history statue in the middle."},
    'information': {'platforms': [plat('platform:counter', [3072, 2944], [768, 128], 96, dict(WALG1, fit=False),
                                       dict(CEILA), "The information counter.")],
                    'notes': "The information counter, the visitors' strongbox behind it."},
    'atrium_nw': {'platforms': [plat('platform:brazier_nw', BRAZIERS['nw'], [160, 160], 64, dict(WALGM), dict(WALGM),
                                     "A cold brazier's stand (lit with the north-west torch).")]},
    'atrium_ne': {'platforms': [plat('platform:brazier_ne', BRAZIERS['ne'], [160, 160], 64, dict(WALGM), dict(WALGM),
                                     "A cold brazier's stand (lit with the north-east torch).")]},
    'atrium_sw': {'platforms': [plat('platform:brazier_sw', BRAZIERS['sw'], [160, 160], 64, dict(WALGM), dict(WALGM),
                                     "A cold brazier's stand (lit with the south-west torch).")]},
    'atrium_se': {'platforms': [plat('platform:brazier_se', BRAZIERS['se'], [160, 160], 64, dict(WALGM), dict(WALGM),
                                     "A cold brazier's stand (lit with the south-east torch).")]},
    'overseer': {'platforms': [plat('platform:desk', [4224, -2816], [384, 160], 80, dict(CEILA), S_('desktop', 128, 64, fit=True),
                                    "The Overseer's desk and his note.", end_surface=dict(CEILA, fit=False))]},
    'stair_foot': {
        'platforms': [head('platform:grand_head', strip(SF_BOX, 'n'), L1, L2, BIGB, FLORD,
                           "The grand stair's head (768) across the room's north end: L2's stair head north.")],
        'flights': [{'from': [-1696, -4736], 'to': [-1696, -3712], 'to_height': L2, 'width': STAIR_W, 'steps': 24,
                     'open_below': 32, 'sides': {'height': 48, 'thickness': 16, 'surface': dict(BIGB)},
                     'notes': "The grand stair: twenty-four steps of 32 up the west wall, rising north to the head."}],
        'notes': "Behind the torch door: the grand stair up the west wall to its head (L2); the Pharaoh's lift's cage east, under the head.",
    },
    'registry_stair': {
        'platforms': [head('platform:registry_head', strip(RS_BOX, 's'), L2, L3, BIGB, SWFLOOR,
                           "The registry stair's head (1536) across the south end: the maze landing east.")],
        'flights': [{'from': [-2720, 3520], 'to': [-2720, 1664], 'to_height': L3, 'width': STAIR_W, 'steps': 24,
                     'open_below': 32, 'sides': {'height': 48, 'thickness': 16, 'surface': dict(BIGB)},
                     'notes': "Twenty-four steps up the west side, rising south to the head."}],
        'notes': "Behind the bronze registry door: the stair up to the Ancients' level.",
    },
    'apex_stair': {
        'platforms': [head('platform:apex_head', strip(AS_BOX, 'n'), L3, L4, SWWALL, FLORA,
                           "The apex stair's head (2304) across the north end: the apex landing north.")],
        'flights': [{'from': [2880, -2560], 'to': [2880, -1792], 'to_height': L4, 'width': STAIR_W, 'steps': 24,
                     'open_below': 32, 'sides': {'height': 48, 'thickness': 16, 'surface': dict(SWWALL)},
                     'notes': "Twenty-four steps up the east side, rising north to the head."}],
        'notes': "From the far cell's door up to the Pharaoh's apartments.",
    },
    'tomb_w': {'platforms': [plat(None, [x, y], [160, 416], 96, dict(WALGM), dict(FLORB), "A sarcophagus.")
                             for x, y in ((-3552, -1280), (-3552, -320), (-3552, 640))]
               + [plat(None, [x, y], [416, 160], 96, dict(WALGM), dict(FLORB), "A sarcophagus.")
                  for x, y in ((-3200, 992), (-2176, 992), (-3200, -1632))],
               'notes': "A burial chamber: six sarcophagi by the walls, the grave goods' chest."},
    'tomb_e': {'platforms': [plat('platform:gilded_sarcophagus', [1056, 512], [416, 192], 112, dict(GOLD, fit=False),
                                  dict(FLORB), "The royal sarcophagus, gilded.")],
               'notes': "A royal tomb: one gilded sarcophagus; north, the cloister."},
    'cloister_s': {'pillars': [pillar(x, y, 128, dict(COL64, scale=2)) for x, y in ((320, 2176), (1344, 2176))]},
    'cloister_n': {'pillars': [pillar(x, y, 128, dict(COL64, scale=2)) for x, y in ((320, 3200), (1344, 3200))]},
    'embalmers': {'platforms': [plat('platform:embalming_table', [-2816, -2624], [512, 192], 80, dict(WALGM),
                                     dict(FLORF), "An embalming table.")],
                  'notes': "Tables, jars and linen; the jar of salts is a find."},
    'cell_c': {'platforms': [plat('platform:weapon_rack', [3136, 640], [64, 384], 192, dict(SWPANEL, fit=False),
                                  dict(SWJAMB), "The guard post's weapon rack.", end_surface=dict(SWJAMB, fit=False))]},
    'ante_s': {'pillars': [pillar(x, y, 160, dict(COL64, scale=2.5)) for x, y in ((-256, -2560), (1664, -2560))]},
    'ante_n': {'pillars': [pillar(x, y, 160, dict(COL64, scale=2.5)) for x, y in ((-256, -1408), (1664, -1408))],
               'platforms': [plat('platform:book_stand', [1408, -1088], [96, 96], 112, dict(TRMC), S_('xnpbook', 128, 128, fit=True),
                                  "The book stand: The Prime Directive.", end_surface=dict(TRMC, fit=False))]},
    'throne_n': {'platforms': [plat('platform:dais', DAIS, [1024, 512], 48, dict(GOLD), dict(FLORA),
                                    "The stepped dais at the hall's north end."),
                               plat('platform:throne', [THRONE_AT[0], THRONE_AT[1]], [192, 128], 112, dict(GOLD),
                                    dict(GOLD), "The Pharaoh's throne.", base=48),
                               plat(None, [THRONE_AT[0], THRONE_AT[1] + 80], [192, 32], 352, dict(GOLD), dict(GOLD),
                                    "The throne's back.", base=48),
                               plat('platform:vat', VAT_AT, [192, 192], 96, dict(GOLD, fit=False), dict(WATER),
                                    "The Brew of Pure Power, bubbling in its vat beside the dais.")],
                 'notes': "Under the apex: the throne on its gilded dais, the Dragon Pharaoh at it, the Brew of Pure Power beside it; behind the dais to the east the way to the sky corridor."},
    'bedchamber': {'platforms': [plat('platform:bed', [2624, 2304], [384, 448], 64, dict(CEILA), dict(CEILA),
                                      "The ornate bed against the east wall.")],
                   'notes': "The ornate bed, the tapestry, the wall safe; the carved button by the west wall."},
    'cell_b': {'notes': "A dead end: the Overseer's lost map of the pads glows on the north wall."},
}

FURNISH = {
    'chapel_nw': {'walls': [{'wall': 'w', 'panels': [panel('panel:niche_nw_1', 256, 0, 256, dict(NICHE_A, fit=True), "A niche.", offset=320),
                                                      panel('panel:niche_nw_2', 256, 0, 256, dict(NICHE_B, fit=True), "A niche.", offset=960)]}]},
    'chapel_ne': {'walls': [{'wall': 'e', 'panels': [panel('panel:niche_ne_1', 256, 0, 256, dict(NICHE_A, fit=True), "A niche.", offset=320),
                                                      panel('panel:niche_ne_2', 256, 0, 256, dict(NICHE_B, fit=True), "A niche.", offset=960)]},
                            {'wall': 'n', 'panels': [panel('panel:torch_plaque', 128, 96, 256, dict(PLAQUE, fit=True),
                                                           "The plaque by the torch (m28.torch_plaque).", offset=1088)]}]},
    'chapel_sw': {'walls': [{'wall': 'w', 'panels': [panel('panel:niche_sw_1', 256, 0, 256, dict(NICHE_A, fit=True), "A niche.", offset=256),
                                                      panel('panel:niche_sw_2', 256, 0, 256, dict(NICHE_B, fit=True), "A niche.", offset=768)]}]},
    'chapel_se': {'walls': [{'wall': 's', 'panels': [panel('panel:niche_se_1', 256, 0, 256, dict(NICHE_A, fit=True), "A niche.", offset=320),
                                                      panel('panel:niche_se_2', 256, 0, 256, dict(NICHE_B, fit=True), "A niche.", offset=960)]}]},
    # the number hall's eight niches on its east wall (counter-clockwise: south to north)
    'number_s': {'walls': [{'wall': 'e', 'panels': [panel(f'panel:niche_{n}', 256, 64, 256, dict(NICHE_C, fit=True),
                                                          f"Niche {n}.", offset=off)
                                                    for n, off in ((3, 192), (4, 576), (5, 960), (6, 1344))]}]},
    'number_n': {'walls': [{'wall': 'e', 'panels': [panel(f'panel:niche_{n}', 256, 64, 256, dict(NICHE_C, fit=True),
                                                          f"Niche {n}.", offset=off)
                                                    for n, off in ((7, 192), (8, 576), (9, 960), (10, 1344))]}]},
    'registry': {'walls': [{'wall': 'w', 'panels': [panel('panel:registry_plaque', 256, 128, 128, dict(REGPLQ, fit=True),
                                                          "The brass registry plaque (xdregplq) beside the door.",
                                                          offset=768)]}]},
    'cell_b': {'walls': [{'wall': 'n', 'panels': [panel('panel:pad_map', 256, 128, 128, dict(SCREEN, fit=True),
                                                        "The Overseer's lost map of the pads.")]}]},
    'bedchamber': {'walls': [{'wall': 'n', 'panels': [panel('panel:tapestry', 384, 64, 384, dict(TAPESTRY, fit=True),
                                                            "The tapestry: the safe's numbers in its border.", offset=192)]}]},
    'sky_corridor': {'walls': [{'wall': 4, 'panels': [panel('panel:sky_door', 384, 0, 384, dict(SWSKY, fit=True),
                                                            "The sky door in the pyramid's face near the apex.")]}]},
}

# The talking statues: figures in a niche (egywlspb) on a wall, the step plate before each (dress.py).
STATUE_PANELS = {
    'welcome': ('entry', 'w', 640), 'history': ('reception', 's', 400), 'torch_statue': ('atrium_se', 's', 480),
    'rule_s': ('number_s', 'w', 512), 'rule_n': ('number_n', 'w', 512),
    'verse_1': ('proc_1', 'w', 448), 'verse_2': ('proc_2', 'e', 1120), 'verse_3': ('proc_3', 'w', 640),
    'verse_4': ('proc_3', 'e', 960),
}
for _k, (_room, _wall, _off) in STATUE_PANELS.items():
    FURNISH.setdefault(_room, {}).setdefault('walls', []).append(
        {'wall': _wall, 'panels': [panel(f'panel:statue_{_k}', 320, 64, 320, dict(NICHE_B, fit=True),
                                         "A statue in its niche: it speaks as the party approaches.", offset=_off)]})


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
    o = outline(rid)
    return abs(sum(o[i][0] * o[(i + 1) % len(o)][1] - o[(i + 1) % len(o)][0] * o[i][1] for i in range(len(o)))) / 2


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
