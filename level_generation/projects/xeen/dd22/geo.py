#!/usr/bin/env python3
"""DD-22 Sheltem's Pod: the geometry (rooms, openings, lifts' holes) shared by L2, L3 and L4.

Escape Pod 2 stands upright in its crater in D6's Ancient field: three decks 448 apart round a lift spine, the hatch
in deck 1's south wall (x east, y north, z up; z 0 the airlock's floor = D6's hatch sill; the lift spine at x 0).
- Deck 1 (0, ceilings 320): the airlock (the arrival, the hatch's exit face in its south wall), the lower ring (an L
  round the shaft's foot, the maintenance hatch in its east arm), the shaft foot (lift A), the stores (a dead end, a
  chest), the drive room (the stern drive under red floor grilles, the two dormant devices, the cold stasis generator
  and its tool rack), the maintenance ladder (in the hull's thickness, up through the gun deck's floor).
- Deck 2 (448, ceilings 768): the middle ring (lift A's head through its floor, lift B's foot), the gun deck (Phaser
  and Photon Control, the ladder's hatch), the brig (two dark stasis cells, the guards' locker), the security post
  (charging alcoves, the security console).
- Deck 3 (896): the bridge landing (lift B's head through its floor, the blast door), the bridge (the domed viewport
  of dark steel ribs, Sheltem's command couch, the main and scanning consoles, the log computer).
Two lifts make the spine: A from deck 1 to deck 2, B from deck 2 to deck 3, side by side (A west, B east of x 0), each
rising through a hole in the deck above. Walls between rooms of one deck are 128 thick; decks are 128 slabs.
"""

D1, D2, D3 = 0, 448, 896
C1, C2 = 320, 768                    # deck 1 and deck 2 ceilings (128 slabs under the next deck)
C3 = 1344                            # deck 3's ceilings (the bridge's dome rises above)
DOME_TOP = 1856


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Control Center (sci-fi.blv) in its red accents (A6's dungeon_families pods assign for DD-22)
HULL = S_('swll4dk', 128, 256)        # dark teal panel wall with conduits: the hull (D6's outside is swll4dk)
REDPANEL = S_('swll5dk', 128, 256)    # dark panel with a red pilot light: the bridge, the security post, the brig
METAL = S_('swfloor2b', 128, 128)     # dark grey metal floor
REDFLOOR = S_('swfloor5a', 128, 128)  # red floor grid: the bridge, the security post, the lift pads
RUST = S_('swceilf', 256, 256)        # rust ceiling panel
TEALCEIL = S_('swankdk', 128, 128)    # teal plate: deck 2's ceilings, the dome's leaning sides
STRIPE = S_('swr2dk', 64, 64)         # hazard stripes (tiles along x only): the drive grilles' kerb
STRIP = S_('swhorzad', 32, 32)        # blue panel strip: console edges
HATCH = S_('swdoora', 256, 256)       # heavy riveted door with a round boss: the hatch, the blast door
DOOR = S_('swdoorb', 256, 256)        # cross-braced door
GIRDER = S_('swgirder', 64, 64)       # riveted plate: reveals, plinths, the dome's ribs
SCREEN = S_('trekscrn', 128, 64)      # grey console face: consoles' tops, the log computer
MACHINE = S_('swor2', 256, 256)       # machine panel with pipes and dials: consoles' sides, the stasis generator
REDGRILLE = S_('swrdk2', 128, 128)    # bars over red light: the drive grilles, the dark stasis cells
REDMACHINE = S_('swared', 128, 256)   # machine panel with a red pilot (tiles along x only): charging alcoves
MAINT = S_('swtrpnl', 128, 256)       # skull-mask panel: the maintenance hatch
COLUMN = S_('swaled', 128, 256)       # machine column: the alien devices
LADDERTEX = S_('bemv', 32, 256, uneven=True)   # DD-17's ladder picture

THEMES = [
    {'id': 'theme:hull', 'wall': REDPANEL, 'floor': METAL, 'ceiling': RUST, 'door': DOOR, 'reveal': REDPANEL,
     'notes': "The pod's corridors and deck 1 (MM6 Control Center in its red accents, D-67 change 6): dark panels with red pilot lights (swll5dk), grey metal floors (swfloor2b), rust ceiling panels (swceilf), dark reveals."},
    {'id': 'theme:airlock', 'wall': HULL, 'floor': METAL, 'ceiling': RUST, 'door': DOOR, 'reveal': REDPANEL,
     'notes': "The airlock: the hull's inner skin (swll4dk, the hull D6 shows outside), the only teal room (D-67)."},
    {'id': 'theme:deck2', 'wall': REDPANEL, 'floor': METAL, 'ceiling': RUST, 'door': DOOR, 'reveal': REDPANEL,
     'notes': "Deck 2 and the bridge landing: the red-pilot panels under rust ceiling panels (D-67: no teal ceilings)."},
    {'id': 'theme:red', 'wall': REDPANEL, 'floor': REDFLOOR, 'ceiling': RUST, 'door': DOOR, 'reveal': REDPANEL,
     'notes': "The red accents (A6's assign): dark panels with red pilot lights (swll5dk) over the red floor grid (swfloor5a): the bridge and the security post."},
    {'id': 'theme:dark', 'wall': REDPANEL, 'floor': METAL, 'ceiling': RUST, 'door': DOOR, 'reveal': REDPANEL,
     'notes': "The drive room and the brig: the red-pilot panels (swll5dk) over grey metal."},
]


def box(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# Rooms: id: (name, outline, floor, ceiling, theme)
AIRLOCK = (-256, -1024, 256, -640)
SHAFT = (-320, -128, 320, 448)
RING1 = (-448, -384, 448, 448)
ANTE = (-576, -128, 448, 448)
BRIDGE = (-960, 576, 960, 1600)
LADDER_BOX = (832, -128, 1088, 256)
GUN = (576, -512, 1216, 768)
BRIG = (-1216, -512, -576, 448)
SECURITY = (-1216, 576, -576, 1088)
STORES = (-832, -128, -448, 448)
DRIVE = (-832, 576, 832, 1280)

R = {
    # deck 1 (0)
    'airlock': ("Airlock", box(*AIRLOCK), D1, C1, 'theme:airlock'),
    'ring0': ("Lower ring", [[-704, -512], [576, -512], [704, -384], [704, 448], [448, 448], [448, -256],
                             [-704, -256]], D1, C1, 'theme:hull'),
    'shaft0': ("Lift shaft foot", box(*SHAFT), D1, C1, 'theme:hull'),
    'stores': ("Stores", box(*STORES), D1, C1, 'theme:hull'),
    'drive': ("Drive room", [[-704, 576], [704, 576], [832, 704], [832, 1152], [704, 1280], [-704, 1280],
                             [-832, 1152], [-832, 704]], D1, C1, 'theme:dark'),
    'ladder': ("Maintenance ladder", box(*LADDER_BOX), D1, C1, 'theme:hull'),
    # deck 2 (448)
    'ring1': ("Middle ring", box(*RING1), D2, C2, 'theme:deck2'),
    'gun_deck': ("Gun deck", [[576, -512], [1088, -512], [1216, -384], [1216, 640], [1088, 768], [576, 768]],
                 D2, C2, 'theme:deck2'),
    'brig': ("The brig", [[-1088, -512], [-576, -512], [-576, 448], [-1216, 448], [-1216, -384]], D2, C2,
             'theme:dark'),
    'security': ("Security post", box(*SECURITY), D2, C2, 'theme:red'),
    # deck 3 (896)
    'bridge_ante': ("Bridge landing", box(*ANTE), D3, C3, 'theme:deck2'),
    'bridge': ("The bridge", [[-960, 576], [960, 576], [960, 1216], [576, 1600], [-576, 1600], [-960, 1216]],
               D3, C3, 'theme:red'),
}
DECK = {D1: 'deck1', D2: 'deck2', D3: 'deck3'}
ORDER = sorted(R)


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


def shared(a, b, walls=None):
    """The facing walls of rooms a and b (axis-aligned edges, gap 1-512): (gap, i, j, lo, hi, axis, p0, p1)."""
    best = None
    for i, (p0, p1) in enumerate(edges(a)):
        for j, (q0, q1) in enumerate(edges(b)):
            if walls and (i, j) != walls:
                continue
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
            if best is None or gap < best[0] or (gap == best[0] and hi - lo > best[4] - best[3]):
                best = cand
    if best is None:
        raise SystemExit(f'no facing walls between {a} and {b}')
    return best


def opening(oid, a, b, at=None, width=256, height=256, link=None, walls=None, **kw):
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b, walls)
    if at is None:
        at = (lo + hi) / 2
    if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
        raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
    forward = (p1[ax] - p0[ax]) > 0
    along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b}
    d['from_wall'] = SIDE[i] if len(outline(a)) == 4 else i
    d['to_wall'] = SIDE[j] if len(outline(b)) == 4 else j
    if along != 0.5:
        d['along'] = along
    if link:
        d['link'] = link
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


# The spine: lift A (deck 1 to 2) west of x 0, lift B (deck 2 to 3) east of it; each a 224 x 256 pad.
LIFT_SIZE = [224, 256]
LIFT_A = [-160, 256]
LIFT_B = [160, 256]
LIFT_TRAVEL = 448
# The ladder: against the ladder room's north wall, up through the gun deck's floor (DD-16's crawlway pattern).
LADDER_AT = [960, 230]
LADDER_HOLE = ([960, 168], [192, 144])
LADDER_EXIT = [960, 320]
# The blast door on the bridge landing's north wall.
BLAST_X, BLAST_W, BLAST_H = -256, 384, 320

OPENINGS = [
    # deck 1
    opening('open:airlock_ring', 'airlock', 'ring0', at=0, width=256, height=256, link='link:airlock_ring',
            notes="The airlock's inner door, north into the lower ring."),
    opening('open:ring_shaft', 'ring0', 'shaft0', at=0, width=384, height=288, link='link:ring_shaft',
            notes="The lower ring into the shaft's foot."),
    opening('open:shaft_drive', 'shaft0', 'drive', at=144, width=256, height=288, link='link:shaft_drive',
            notes="The shaft's foot north into the drive room."),
    opening('open:shaft_stores', 'shaft0', 'stores', at=96, width=256, height=256, link='link:shaft_stores',
            notes="The stores' door in the shaft's west wall."),
    opening('open:ring_ladder', 'ring0', 'ladder', at=64, width=192, height=256, link='link:ring_ladder',
            notes="The maintenance hatch in the lower ring's east arm."),
    # deck 2
    opening('open:ring_gun', 'ring1', 'gun_deck', at=0, width=256, height=256, link='link:ring_gun',
            notes="The gun deck's door in the middle ring's east wall."),
    opening('open:ring_brig', 'ring1', 'brig', at=0, width=256, height=256, link='link:ring_brig',
            notes="The brig's door in the middle ring's west wall."),
    opening('open:brig_security', 'brig', 'security', at=-896, width=256, height=256, link='link:brig_security',
            notes="The security post's door in the brig's north wall."),
    # deck 3
    opening('open:blast', 'bridge_ante', 'bridge', at=BLAST_X, width=BLAST_W, height=BLAST_H, link='link:blast',
            notes="The bridge's blast door (two leaves parting in the middle)."),
    # the holes the lifts and the ladder rise through
    {'id': 'open:lift_a', 'from': 'room:ring1', 'to': 'room:shaft0', 'in': 'floor', 'at': LIFT_A, 'size': LIFT_SIZE,
     'link': 'link:lift_a', 'notes': "Lift A's well in the middle ring's floor: the lift rises through it from the shaft's foot."},
    {'id': 'open:lift_b', 'from': 'room:bridge_ante', 'to': 'room:ring1', 'in': 'floor', 'at': LIFT_B,
     'size': LIFT_SIZE, 'link': 'link:lift_b',
     'notes': "Lift B's well in the bridge landing's floor: the lift rises through it from the middle ring."},
    {'id': 'open:ladder_hatch', 'from': 'room:gun_deck', 'to': 'room:ladder', 'in': 'floor', 'at': LADDER_HOLE[0],
     'size': LADDER_HOLE[1], 'link': 'link:ladder',
     'notes': "The maintenance hatch in the gun deck's floor over the ladder."},
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


# Furniture (centres, sizes, rises)
DEVICES = [([-448, 1200], [128, 96]), ([448, 1200], [128, 96])]       # against the drive room's north wall
DEVICE_RISE = 192
GENERATOR = ([744, 896], [144, 256], 224)       # the stasis generator against the drive room's east wall
RACK = ([752, 1088], [128, 96], 112)            # its tool rack, north of it by the wall
GRILLE = [[-448, 704], [448, 704], [448, 1088], [-448, 1088]]   # the drive grilles in the floor (a level 24 down)
WEAPONS = [('phaser', [1152, 96]), ('photon', [1152, 416])]       # against the gun deck's east wall
WEAPON_SIZE, WEAPON_RISE = [96, 192], 112
CELLS = [(-1152, -192), (-1152, 192)]           # the brig's two stasis cells on its west wall (centre y)
CELL_LEN = 256
SEC_CONSOLE = ([-896, 1040], [256, 80], 112)    # against the security post's north wall
COUCH_DAIS = ([0, 1024], [448, 384], 32)
COUCH_SEAT = ([0, 1040], [192, 160], 72)
COUCH_BACK = ([0, 944], [264, 32], 192)     # as wide as the seat and its arms
COUCH_ARM_TOP = 128                         # 56 above the seat (72)
CONSOLES = [('main_console', [-320, 1528], [320, 96]), ('scan_console', [320, 1528], [320, 96])]
CONSOLE_RISE = 112
LOG_PANEL = (1, 0.5)                            # the bridge's east wall (outline edge 1), its middle
DOME = [[-704, 768], [704, 768], [704, 1120], [480, 1344], [-480, 1344], [-704, 1120]]


def dome_ribs():
    """Rings of dark steel hanging under the dome's leaning sides (each ring a contour of the dome, so it keeps one
    height under the slope): the viewport's ribs. Raking ribs drew squashed undersides (the build's warning)."""
    out = []
    top_scale = 0.35
    cx = (min(p[0] for p in DOME) + max(p[0] for p in DOME)) / 2
    cy = (min(p[1] for p in DOME) + max(p[1] for p in DOME)) / 2

    def height(sc):
        return C3 + (DOME_TOP - C3) * (1 - sc) / (1 - top_scale)
    for sc in (0.85, 0.6):
        ring = [[round(cx + (x - cx) * sc), round(cy + (y - cy) * sc)] for x, y in DOME]
        outer = min(1.0, sc + 0.06)
        bottom = int(height(outer) - 24 - 16)
        out.append({'path': ring, 'width': 32, 'depth': 24, 'bottom': bottom, 'surface': dict(REDPANEL),
                    'notes': "A ring of dark steel under the domed viewport (five of its six sides)."})
        p, q = ring[-1], ring[0]
        ln = ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** 0.5
        ux, uy = (q[0] - p[0]) / ln, (q[1] - p[1]) / ln
        out.append({'path': [[round(p[0] + 16 * ux), round(p[1] + 16 * uy)], [round(q[0] - 16 * ux), round(q[1] - 16 * uy)]],
                    'width': 32, 'depth': 24, 'bottom': bottom, 'surface': dict(REDPANEL),
                    'notes': "The ring's sixth side."})
    return out


def accent(offset):
    """A red-pilot machine panel (swared) once, whole, on a ring's long wall (D-67 change 6)."""
    return {'offset': offset, 'length': 128, 'bottom': 0, 'height': 256, 'surface': dict(REDMACHINE, fit=True),
            'notes': "A red-pilot machine panel set into the ring's wall."}


EXTRA = {
    'airlock': {
        'notes': "Behind the round hatch (the exit's face in the south wall): the arrival, cold and red-lit; the inner door north. Quiet.",
    },
    'ring0': {
        'walls': [{'wall': 0, 'panels': [accent(192), accent(1024)]}],
        'notes': "An L-shaped corridor round the shaft's foot, its outer corner cut; the maintenance hatch in its east arm.",
    },
    'shaft0': {
        'notes': "The spine's foot: lift A's pad against the north wall (its call button above it), the drive room north, the stores west.",
    },
    'stores': {
        'notes': "A dead end: the pod's stores locker and a few barrels by the walls.",
    },
    'drive': {
        'levels': [{'id': 'level:grilles', 'outline': GRILLE, 'floor': D1 - 24, 'edge': dict(STRIPE),
                    'surface': dict(REDGRILLE),
                    'notes': "The stern drive under red floor grilles (a step of 24 down)."}],
        'platforms': [plat(f'platform:device_{i + 1}', at, size, DEVICE_RISE, dict(COLUMN, fit=True), dict(GIRDER),
                           "A strange alien device, dark (aaze0088:0).") for i, (at, size) in enumerate(DEVICES)] + [
            plat('platform:generator', GENERATOR[0], GENERATOR[1], GENERATOR[2], dict(MACHINE, fit=True),
                 dict(GIRDER), "The stasis generator that carried Sheltem through the crash, cold.",
                 end_surface=dict(MACHINE, fit=True)),
            plat('platform:rack', RACK[0], RACK[1], RACK[2], dict(GIRDER), dict(REDGRILLE),
                 "The stasis generator's tool rack (the find, D-62 APPROVAL)."),
        ],
        'walls': [{'wall': 6, 'panels': [{'at': 'centre', 'length': 384, 'bottom': 0, 'height': 256,
                                          'surface': dict(REDMACHINE, fit=False)}]}],
        'notes': "The stern drive under red floor grilles; the two alien devices dark against the north wall; the stasis generator and its tool rack on the east wall.",
    },
    'ladder': {
        'notes': "A narrow space in the hull's thickness: the ladder up through the gun deck's floor hatch.",
    },
    'ring1': {
        'walls': [{'wall': 's', 'panels': [accent(128), accent(640)]}],
        'notes': "The middle ring round the spine: lift A's well in its floor (west), lift B's pad (east), both call buttons on the north wall; the gun deck east, the brig west. Quiet.",
    },
    'gun_deck': {
        'platforms': [plat(f'platform:{k}', at, WEAPON_SIZE, WEAPON_RISE, dict(MACHINE), dict(SCREEN, fit=True),
                           f"{'Phaser' if k == 'phaser' else 'Photon'} Control: a weapon console against the hull.",
                           end_surface=dict(GIRDER, fit=False)) for k, at in WEAPONS],
        'notes': "Phaser and Photon Control against the hull (east wall); the maintenance hatch in the floor by the north-west.",
    },
    'brig': {
        'walls': [{'wall': 3, 'panels': [
            {'id': f'panel:cell_{i + 1}', 'offset': round(448 - (c + CELL_LEN / 2)), 'length': CELL_LEN, 'bottom': 0,
             'height': 256, 'surface': dict(REDGRILLE, fit=True),
             'notes': "An empty stasis cell, its field dark."} for i, (_, c) in enumerate(CELLS)]}],
        'notes': "Two empty stasis cells in the west wall where Sheltem shut the Ancients' agents (log XL70I), their fields dark; the guards' locker by the south wall.",
    },
    'security': {
        'platforms': [plat('platform:sec_console', SEC_CONSOLE[0], SEC_CONSOLE[1], SEC_CONSOLE[2],
                           dict(MACHINE), dict(SCREEN, fit=True),
                           "The security console: 'Security lockdown: bridge sealed. Release?'",
                           end_surface=dict(GIRDER, fit=False))],
        'walls': [{'wall': 'w', 'panels': [{'at': 'centre', 'length': 384, 'bottom': 0, 'height': 256,
                                            'surface': dict(REDMACHINE)}]},
                  {'wall': 'e', 'panels': [{'at': 'centre', 'length': 256, 'bottom': 0, 'height': 256,
                                            'surface': dict(REDMACHINE)}]}],
        'notes': "The machines' charging alcoves (red-pilot machine panels, swared) along the walls; the security console against the north wall.",
    },
    'bridge_ante': {
        'notes': "Lift B's head through the floor; the bridge's blast door in the north wall; the lift's call button beside it.",
    },
    'bridge': {
        'ceiling_levels': [{'outline': DOME, 'ceiling': DOME_TOP, 'top_scale': 0.35, 'edge': dict(REDPANEL),
                            'surface': dict(RUST, sky=True),
                            'notes': "The domed viewport: dark panels leaning in to an oculus open to the Darkside's sky."}],
        'beams': None,   # filled below
        'platforms': [
            plat('platform:couch_dais', COUCH_DAIS[0], COUCH_DAIS[1], COUCH_DAIS[2], dict(GIRDER), dict(REDFLOOR),
                 "The dais of Sheltem's command couch."),
            plat('platform:couch', COUCH_SEAT[0], COUCH_SEAT[1], COUCH_SEAT[2] - COUCH_DAIS[2], dict(MACHINE),
                 dict(GIRDER), "Sheltem's command couch, empty, facing the viewport.", base=COUCH_DAIS[2],
                 end_surface=dict(MACHINE, fit=False)),
            plat(None, [-116, COUCH_SEAT[0][1]], [32, COUCH_SEAT[1][1]], COUCH_ARM_TOP - COUCH_DAIS[2], dict(GIRDER),
                 dict(GIRDER), "The couch's left arm.", base=COUCH_DAIS[2], end_surface=dict(GIRDER, fit=False)),
            plat(None, [116, COUCH_SEAT[0][1]], [32, COUCH_SEAT[1][1]], COUCH_ARM_TOP - COUCH_DAIS[2], dict(GIRDER),
                 dict(GIRDER), "The couch's right arm.", base=COUCH_DAIS[2], end_surface=dict(GIRDER, fit=False)),
            plat('platform:couch_back', COUCH_BACK[0], COUCH_BACK[1], COUCH_BACK[2] - COUCH_DAIS[2], dict(MACHINE),
                 dict(GIRDER), "The couch's high back.", base=COUCH_DAIS[2], end_surface=dict(GIRDER, fit=False)),
        ] + [plat(f'platform:{k}', at, size, CONSOLE_RISE, dict(MACHINE), dict(SCREEN, fit=True),
                  f"The {'Main' if k == 'main_console' else 'Scanning'} Console, flickering red (aaze0088:{5 if k == 'main_console' else 6}).",
                  end_surface=dict(GIRDER, fit=False)) for k, at, size in CONSOLES],
        'walls': [{'wall': LOG_PANEL[0], 'panels': [
            {'at': 'centre', 'length': 320, 'bottom': 64, 'height': 192, 'surface': dict(GIRDER),
             'notes': "The log computer's riveted frame."},
            {'id': 'panel:log', 'cover': True, 'at': 'centre', 'length': 256, 'bottom': 96, 'height': 128,
             'surface': dict(SCREEN, fit=True), 'notes': "The log computer, still paging Sheltem's entries."}]}],
        'notes': "The set piece in the pod's nose: a domed viewport of dark steel ribs over Sheltem's empty command couch; the main and scanning consoles against the nose (north), the log computer on the east wall; red light.",
    },
}
EXTRA['bridge']['beams'] = dome_ribs()


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
