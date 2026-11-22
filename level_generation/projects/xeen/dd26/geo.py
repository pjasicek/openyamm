#!/usr/bin/env python3
"""DD-26 Olympus Sewer: the geometry (rooms, openings) shared by L2, L3 and L4.

One level at z 0 under D7's Olympus (x east, y north, z up; the arrival (0, 0, 0) at the marble stair's foot):
- the marble stair (the arrival at its foot; the stair climbs south 448 to the grate's underside, the way out);
- the ring of channels round Cyrano's den: the south conduit (marble, its channel down the middle in two runs with a
  dry crossing at the stair and the den's door), the west and east culverts (d01's stone, their channels along the
  outer walls, broken where the grates open), the gods' cistern (marble, a clear basin sunk 256 between walkways);
- the dead ends: the west spillway and the outfall behind grates, the tribble door's landing off the cistern and the
  offering vault behind the bronze pair (MM8 Temple of the Sun's marble).
Rooms are rectangles; walls between rooms are 128 thick. Channels and pools along a wall stop 16 short of it (the least
the studio cuts): no ledge there that a body could walk along. The spillway's and the outfall's walls are 32 thick, so
their grates leave no recess that a chasing body (radius 60) can wedge into (D-67's reach step). D-65 change 3: walkways at least 256 wide, ceilings over
them at least 320, every opening on a walking line at least 256 wide and 320 high (the Water Elemental: radius 100,
202 high).
"""

FLOOR = 0
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM7 Erathian Sewers (d01): its stone-channel face (XD-21 has its brick culverts)
STONE = S_('wall', 128, 256)            # dark grey sewer blocks: the culverts, the spillway, the outfall
ROUGH = S_('cfb1', 128, 128)            # rough red-brown rock: the culverts' vaults
FLAGS = S_('tfb07', 128, 128)           # big grey flags: the walkways
DRESSED = S_('cwb', 128, 256)           # dressed light stone: Cyrano's den
# The royal kit's t3s2 marble (the town shafts): the stair, the conduit, the cistern, the tribble door's landing
MARBLE = S_('t3s2b1', 128, 256)         # pale marble panels
MARBLE_BASE = S_('t3s2b', 128, 256)     # marble with a carved knot band at its foot (a dado 256 high)
# MM8 Temple of the Sun (d28): the offering vault
TEMPLE = S_('gtempw1', 128, 256)        # pale veined temple marble
TEMPLE_FLOOR = S_('gtempflr', 128, 128)
GILT = S_('gtemprf', 128, 128)          # temple coffers with gold knotwork: the vault's ceiling, the ledge
# Shipped pieces
GRATE = S_('xwcage', 128, 256)          # iron bars (Xeen's cage bars, D-22.1): the two grates, the grille mouth, the exit
DRAIN = S_('d1lggrt', 256, 256)         # a round drain grate in a stone frame (MM6 sewer)
PLANK_DOOR = S_('hhm1d', 128, 256)      # the den's plank door (d01's Hhm1d), left leaf
PLANK_DOOR2 = S_('hhm1d2', 128, 256)    # its twin, right leaf
LEAF_L = S_('gcs05a', 128, 256)         # the tribble door: a riveted bronze leaf with a ring
LEAF_R = S_('gcs05b', 128, 256)
PLANK = S_('7trimd', 128, 256)          # the counter's and the bed's planks
BLANKET = S_('t2bedsht', 128, 256)      # the bed's cover (as DD-05's beds)
SCROLL = S_('scroll', 64, 64)           # the pinned scroll on the stair's wall
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}   # clear sky-water (MM7 water)

THEMES = [
    {'id': 'theme:marble', 'wall': MARBLE, 'floor': FLAGS, 'ceiling': MARBLE, 'door': PLANK_DOOR,
     'bands': [{'height': 256, 'surface': dict(MARBLE_BASE)}],
     'notes': "The gods' marble (the royal kit's t3s2: knot-band dado t3s2b, pale panels t3s2b1 above and over the vault) over d01's grey flags (tfb07): the stair, the south conduit, the cistern, the tribble door's landing."},
    {'id': 'theme:culvert', 'wall': STONE, 'floor': FLAGS, 'ceiling': ROUGH, 'door': GRATE,
     'notes': "MM7 Erathian Sewers' stone-channel face: dark grey blocks (wall) under rough rock (cfb1), grey flag walkways (tfb07)."},
    {'id': 'theme:den', 'wall': DRESSED, 'floor': FLAGS, 'ceiling': ROUGH, 'door': PLANK_DOOR,
     'notes': "Cyrano's den: d01's dressed light stone (cwb), the flags, the rough vault."},
    {'id': 'theme:temple', 'wall': TEMPLE, 'floor': TEMPLE_FLOOR, 'ceiling': GILT, 'door': LEAF_L,
     'notes': "The offering vault: MM8 Temple of the Sun's pale marble (gtempw1, gtempflr) under gold-knotted coffers (gtemprf)."},
]


def box(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# id: (name, outline, floor, ceiling, theme)
R = {
    'stair': ("Marble stair", box(-320, -1216, 320, 64), FLOOR, 896, 'theme:marble'),
    'conduit': ("South conduit", box(-1792, 192, 1792, 832), FLOOR, 512, 'theme:marble'),
    'den': ("Pets Unlimited", box(-640, 960, 640, 1856), FLOOR, 448, 'theme:den'),
    'west': ("West culvert", box(-2432, 192, -1920, 1856), FLOOR, 448, 'theme:culvert'),
    'spill': ("West spillway", box(-3104, 704, -2464, 1472), FLOOR, 448, 'theme:culvert'),
    'east': ("East culvert", box(1920, 192, 2432, 1856), FLOOR, 448, 'theme:culvert'),
    'outfall': ("The outfall", box(2464, 704, 3104, 1472), FLOOR, 448, 'theme:culvert'),
    'cistern': ("The gods' cistern", box(-2432, 1984, 2432, 3008), FLOOR, 768, 'theme:marble'),
    'tdoor': ("Tribble door", box(2560, 2304, 3072, 2816), FLOOR, 640, 'theme:marble'),
    'vault': ("Offering vault", box(3200, 2048, 4352, 3072), FLOOR, 512, 'theme:temple'),
}
ORDER = ['stair', 'conduit', 'den', 'west', 'spill', 'cistern', 'east', 'outfall', 'tdoor', 'vault']


def outline(rid):
    return R[rid][1]


def bounds(rid):
    o = outline(rid)
    xs = [p[0] for p in o]
    ys = [p[1] for p in o]
    return min(xs), min(ys), max(xs), max(ys)


def edges(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def area(rid):
    o = outline(rid)
    return abs(sum(o[i][0] * o[(i + 1) % len(o)][1] - o[(i + 1) % len(o)][0] * o[i][1] for i in range(len(o)))) / 2


SIDE = {0: 's', 1: 'e', 2: 'n', 3: 'w'}


def shared(a, b):
    """The facing walls of rooms a and b (axis-aligned edges, gap 1-512): (gap, i, j, lo, hi, axis, p0, p1)."""
    best = None
    for i, (p0, p1) in enumerate(edges(a)):
        for j, (q0, q1) in enumerate(edges(b)):
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
            nx, ny = dy, -dx        # outward normal of a counter-clockwise outline
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


def opening(oid, a, b, at=None, width=320, height=320, link=None, **kw):
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
    if at is None:
        at = (lo + hi) / 2
    if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
        raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
    forward = (p1[ax] - p0[ax]) > 0
    along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b, 'from_wall': SIDE[i], 'to_wall': SIDE[j]}
    if along != 0.5:
        d['along'] = along
    if link:
        d['link'] = link
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


DEN_DOOR_W, DEN_DOOR_H = 256, 320       # two plank leaves 128 x 320 (hhm1d | hhm1d2)
GRATE_W, GRATE_H = 256, 384             # the spillway's and the outfall's grates
TRIBBLE_W, TRIBBLE_H = 384, 384         # the bronze pair: two leaves 192 x 384 (gcs05a | gcs05b)

OPENINGS = [
    opening('open:stair_conduit', 'stair', 'conduit', at=0, width=320, height=384, link='link:1',
            notes="The stair's foot opens north onto the conduit's south walkway, at the dry crossing."),
    opening('open:conduit_den', 'conduit', 'den', at=0, width=DEN_DOOR_W, height=DEN_DOOR_H, link='link:2',
            notes="The den's plank door in the conduit's north wall, at the dry crossing: 'Cyrano sells the password.'"),
    opening('open:conduit_west', 'conduit', 'west', at=512, width=320, height=320, link='link:3'),
    opening('open:west_spill', 'west', 'spill', at=1088, width=GRATE_W, height=GRATE_H, link='link:4',
            notes="The spillway's grate in the west culvert's outer wall, where its channel breaks."),
    opening('open:west_cistern', 'west', 'cistern', at=-2176, width=320, height=320, link='link:5'),
    opening('open:cistern_east', 'cistern', 'east', at=2176, width=320, height=320, link='link:6'),
    opening('open:east_conduit', 'east', 'conduit', at=512, width=320, height=320, link='link:7'),
    opening('open:east_outfall', 'east', 'outfall', at=1088, width=GRATE_W, height=GRATE_H, link='link:8',
            notes="The outfall's grate in the east culvert's outer wall, where its channel breaks."),
    opening('open:cistern_tdoor', 'cistern', 'tdoor', at=2560, width=320, height=384, link='link:9'),
    opening('open:tdoor_vault', 'tdoor', 'vault', at=2560, width=TRIBBLE_W, height=TRIBBLE_H, link='link:10',
            notes="The tribble door: a bronze two-leaf pair under a marble lintel, the voice's grille above."),
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


def strip(b, side, depth):
    x0, y0, x1, y1 = b
    if side == 'n':
        return [[x0, y1 - depth], [x1, y1 - depth], [x1, y1], [x0, y1]]
    if side == 's':
        return [[x0, y0], [x1, y0], [x1, y0 + depth], [x0, y0 + depth]]
    if side == 'e':
        return [[x1 - depth, y0], [x1, y0], [x1, y1], [x1 - depth, y1]]
    return [[x0, y0], [x0 + depth, y0], [x0 + depth, y1], [x0, y1]]


def head(pid, outline_, floor, top, surface, top_surface, notes):
    """A hanging head 32 thick whose top is at `top` (a stair's upper floor inside a two-storey room)."""
    return {'id': pid, 'rise': 32, 'base': top - floor - 32, 'outline': outline_, 'surface': dict(surface),
            'top_surface': dict(top_surface), 'bottom_surface': dict(surface), 'notes': notes}


CHANNEL_DEPTH = 128       # the channels sunk 128 (the graph); the cistern 256
CISTERN_DEPTH = 256
BANK = 160                # a channel's ends slope up (0.8 a unit): whoever falls in walks out at an end


def channel(cid, x0, y0, x1, y1, axis, edge, notes):
    """A channel sunk 128: its flat bed is the outline; the two ends (along `axis`) slope up over BANK."""
    bank = [0, BANK, 0, BANK] if axis == 'x' else [BANK, 0, BANK, 0]
    if axis == 'x':
        o = box(x0 + BANK, y0, x1 - BANK, y1)
    else:
        o = box(x0, y0 + BANK, x1, y1 - BANK)
    return {'id': cid, 'outline': o, 'floor': FLOOR - CHANNEL_DEPTH, 'bank': bank, 'edge': dict(edge),
            'surface': dict(WATER), 'notes': notes}


# The stair: the arrival at its foot (0, 0); fourteen steps of 32 up south to the head (448) under the grate.
STAIR_TOP = 448
STAIR_BOX = (-320, -1216, 320, 64)
HEAD_D = 192
# Cyrano's den: the counter along the north wall either side of the house door; the bed in the north-east corner.
COUNTER_RISE = 96
COUNTERS = [([-400, 1808], [352, 96]), ([400, 1808], [352, 96])]
HOUSE_DOOR_W, HOUSE_DOOR_H = 160, 320
BED = ([464, 1216], [288, 160], 64)            # its head against the east wall
HEADBOARD = ([624, 1216], [32, 160], 64 + 128)  # planks 32 thick, 128 over the sheet (D-67 item 9)
# The spillway's weir ledge (the chest) and pool; the vault's ledge (the chest).
WEIR = ([-2624, 1408], [256, 128], 64)
VAULT_LEDGE = ([4288, 2560], [128, 384], 64)

EXTRA = {
    'stair': {
        'platforms': [head('platform:stair_head', strip(STAIR_BOX, 's', HEAD_D), FLOOR, STAIR_TOP, MARBLE, FLAGS,
                           "The stair's head (448) under the grate up to Olympus.")],
        'flights': [{'from': [0, -256], 'to': [0, -1024], 'to_height': STAIR_TOP, 'width': 320, 'steps': 14,
                     'open_below': 32, 'notes': "Fourteen marble steps of 32 up south from the foot to the head."}],
        'walls': [{'wall': 'w', 'panels': [
            {'id': 'panel:scroll', 'offset': 208, 'length': 96, 'bottom': 112, 'height': 96,
             'surface': dict(SCROLL, fit=True),
             'notes': "A scroll pinned to the stair's wall by the foot: hover 'Scroll' (aaze0038:10), click 'Search the drains.' (:11)."}]}],
        'notes': "The marble stair under D7's grate in the gods' row: the arrival at its foot facing north into the conduit; the stair climbs south to the grate (the way out).",
    },
    'conduit': {
        'levels': [channel('level:conduit_west', -1600, 448, -192, 576, 'x', MARBLE,
                           "The conduit's channel, west run: sky-water sunk 128 down the middle, walkways both sides."),
                   channel('level:conduit_east', 192, 448, 1600, 576, 'x', MARBLE,
                           "The conduit's channel, east run.")],
        'notes': "The main channel under the gods' row, east to west: its water down the middle in two runs, walkways 256 wide on both banks, a dry crossing between the stair and the den's door.",
    },
    'den': {
        'platforms': [plat(f'platform:counter_{i + 1}', at, size, COUNTER_RISE, dict(DRESSED), dict(PLANK),
                           "Cyrano's counter along the north wall (cages on it), either side of his door.")
                      for i, (at, size) in enumerate(COUNTERS)]
                     + [plat('platform:bed', BED[0], BED[1], BED[2], dict(PLANK), dict(BLANKET, fit=True),
                             "Cyrano's bed, its head against the east wall: hover 'Bed' (aaze0038:16).",
                             end_surface=dict(PLANK, fit=False)),
                        plat(None, HEADBOARD[0], HEADBOARD[1], HEADBOARD[2], dict(PLANK, fit=False), dict(PLANK),
                             "The bed's plank headboard against the east wall.", end_surface=dict(PLANK, fit=False))],
        'walls': [{'wall': 'n', 'panels': [
            {'id': 'door:pets_unlimited', 'at': 'centre', 'length': HOUSE_DOOR_W, 'bottom': 0,
             'height': HOUSE_DOOR_H, 'surface': dict(PLANK_DOOR, fit=True),
             'notes': "Cyrano's counter door (A4's house 4815 'Pets Unlimited'): the residence's door between the counter's two halves."}]}],
        'notes': "Cyrano Jones's den in the ring's middle: his counter and door on the north wall (tribble cages on it and by the walls), his bed in the east corner.",
    },
    'west': {
        'levels': [channel('level:west_south', -2416, 320, -2240, 896, 'y', STONE,
                           "The west culvert's channel along its outer wall, south run."),
                   channel('level:west_north', -2416, 1280, -2240, 1728, 'y', STONE,
                           "The west culvert's channel, north run (it breaks at the spillway's grate).")],
        'walls': [{'wall': 'e', 'panels': [
            {'id': 'panel:drain_1', 'offset': 1264, 'length': 160, 'bottom': 16, 'height': 160,
             'surface': dict(DRAIN, fit=True), 'notes': "Drain 1: TR (aaze0038:1, 117801)."}]}],
        'notes': "The ring's west side: its channel along the outer wall, broken at the spillway's grate; the walkway 320 wide along the inner wall; drain 1 in the inner wall.",
    },
    'spill': {
        'levels': [{'id': 'level:weir_pool', 'outline': box(-3088, 768, -2912, 1408), 'floor': FLOOR - CHANNEL_DEPTH,
                    'bank': [0, BANK, 0, 0], 'edge': dict(STONE), 'surface': dict(WATER),
                    'notes': "The overflow pool below the weir along the west wall, its east side sloping up."}],
        'platforms': [plat('platform:weir', WEIR[0], WEIR[1], WEIR[2], dict(STONE), dict(FLAGS),
                           "The weir's dry ledge in the north-east corner: the chest on it.")],
        'walls': [{'wall': 's', 'panels': [
            {'id': 'panel:drain_2', 'offset': 400, 'length': 160, 'bottom': 16, 'height': 160,
             'surface': dict(DRAIN, fit=True), 'notes': "Drain 2: IB (aaze0038:2, 117802)."}]}],
        'notes': "The overflow weir behind its grate: a pool along the west wall, a dry ledge with a T6 chest, drain 2.",
    },
    'east': {
        'levels': [channel('level:east_south', 2240, 320, 2416, 896, 'y', STONE,
                           "The east culvert's channel along its outer wall, south run."),
                   channel('level:east_north', 2240, 1280, 2416, 1728, 'y', STONE,
                           "The east culvert's channel, north run (it breaks at the outfall's grate).")],
        'notes': "The ring's east side, its channel along the outer wall; the outfall's grate where it breaks.",
    },
    'outfall': {
        'levels': [{'id': 'level:outfall_pool', 'outline': box(2912, 768, 3088, 1408), 'floor': FLOOR - CHANNEL_DEPTH,
                    'bank': [0, 0, 0, BANK], 'edge': dict(STONE), 'surface': dict(WATER),
                    'notes': "The pool along the east wall that the sewer falls through, out of the island's edge."}],
        'walls': [{'wall': 'e', 'panels': [
            {'id': 'panel:outfall_bars', 'at': 'centre', 'length': 160, 'bottom': 32, 'height': 320,
             'surface': dict(GRATE, fit=True),
             'notes': "The barred mouth: the water falls away into cloud beyond it (no way out)."}]},
            {'wall': 'n', 'panels': [
                {'id': 'panel:drain_4', 'offset': 400, 'length': 160, 'bottom': 16, 'height': 160,
                 'surface': dict(DRAIN, fit=True), 'notes': "Drain 4: ES (aaze0038:4, 117804)."}]}],
        'notes': "The sewer's mouth on the island's edge behind its grate: a pool, the barred mouth, drain 4.",
    },
    'cistern': {
        'levels': [{'id': 'level:basin', 'outline': box(-1408, 2304, 1408, 2688), 'floor': FLOOR - CISTERN_DEPTH,
                    'bank': [0, 288, 0, 288], 'edge': dict(MARBLE), 'surface': dict(WATER),
                    'notes': "The gods' cistern: clear water sunk 256, its ends sloping up to the walkways."}],
        'walls': [{'wall': 'n', 'panels': [
            {'id': 'panel:drain_3', 'at': 'centre', 'length': 160, 'bottom': 16, 'height': 160,
             'surface': dict(DRAIN, fit=True), 'notes': "Drain 3: BL (aaze0038:3, 117803)."}]}],
        'notes': "The ring's north side: a deep clear basin under a high marble vault, walkways 320 wide round it; drain 3 in the north wall; the tribble door's landing off the east wall.",
    },
    'tdoor': {
        'walls': [{'wall': 'e', 'panels': [
            {'id': 'panel:voice', 'at': 'centre', 'length': 64, 'bottom': 464, 'height': 128,
             'surface': dict(GRATE, fit=True),
             'notes': "The grille mouth over the bronze pair, where the voice comes from."}]}],
        'notes': "The landing before the bronze pair under its marble lintel; the voice's grille above.",
    },
    'vault': {
        'platforms': [plat('platform:vault_ledge', VAULT_LEDGE[0], VAULT_LEDGE[1], VAULT_LEDGE[2], dict(TEMPLE),
                           dict(GILT), "The ledge on the east wall where the offerings' chest stands.",
                           end_surface=dict(TEMPLE, fit=False))],
        'notes': "The undercroft where Olympus's offerings wash down: gilded cups and bags of coin by the walls, a gilt statue, the T6 chest on its ledge.",
    },
}


def room_doc(rid):
    name, o, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': o, 'floor': fl, 'ceiling': ce, 'theme': theme}
    d.update(EXTRA.get(rid, {}))
    return d


def extent(rid):
    x0, y0, x1, y1 = bounds(rid)
    return [x1 - x0, y1 - y0], [(x0 + x1) // 2, (y0 + y1) // 2]


if __name__ == '__main__':
    tot = 0
    for r in ORDER:
        a = area(r)
        tot += a
        print(f'{r:16s} {a / 1e6:6.2f}')
    print('total', tot / 1e6, 'rooms', len(ORDER))
