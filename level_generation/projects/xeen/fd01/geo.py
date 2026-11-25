#!/usr/bin/env python3
"""FD-01 Alamar Depths: the geometry (rooms, openings) shared by L2, L3 and L4.

The castle's undercroft under the ruin of Castle Alamar (x east, y north, z up). The main level at z 0; the arrival from
D6 (entrance:d6_stair) at the ruin stair's foot (0, 0, 0) facing west into the undercroft hall; the stair climbs east to
the gatehouse hatch's underside (640). The C of galleries runs round the west maze: the south gallery west from the
gallery door, the west gallery north through the guard door, the north gallery east past the rubble shaft (the arrival
from D7, entrance:d7_roof, in the north-west corner) to the north door, the long gallery south to the Hall of Nine and
the lever hall. The west maze: the sealed passage (the west slab) into the long workshop (the pyramid nook at its west
end, the west passage north to the assembly hall, the bolted grate into the south gallery, the east spur and the east
slab). The east wing: the key vault, the warden's room, the skull door and the lift head; the lift goes down 768 to the
lift foot and the stasis vault (a round chamber).
Rooms are rectangles or polygons; walls between rooms are 128 thick (DD-17's frame). Walking lines 512 wide, ceilings
448 or more, doors 384 high (the robots: 188 and 228 high, radius 60).
"""
import math

FLOOR = 0
LOW = -768          # the stasis vault and the lift foot
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Control Center's sw set, braced and burnt (D-69 change 7, Q72 (b)); A6's ancient kit per_site line
BRACED = 'swall4'       # crossed braces with rust: galleries and passages
DIAMOND = 'swall2'      # diamond braces: the halls and rooms


def wall(t, height):
    """A 128 x 256 panel laid once up a wall `height` high (scale), one declared size per texture."""
    s = round(height / 256, 4)
    return S_(t, 128, 256, scale=s) if s != 1 else S_(t, 128, 256)


PLATE = S_('swankdk', 128, 128)         # teal plate floor
CEIL = S_('swceilf', 256, 256)          # rust ceiling panel
GIRDER = S_('swgirder', 64, 64)         # riveted plate: reveals, plinths, boxes, frames
COLUMN = S_('swaled', 128, 256, scale=2)    # machine column with blue light, once up a 512 pillar face 256 wide
HULL = S_('xahullbn', 256, 256)         # scorched, buckled plating: where the castle came down
SKULL_L = S_('swtrpnl', 128, 256)       # skull-mask panels: the skull door
SKULL_R = S_('swtrdk', 128, 256)
MACHINE = S_('swor2', 256, 256)         # machine panel with pipes and dials
SCREEN = S_('trekscrn', 128, 64)        # grey console face
FIELD = S_('xafield', 128, 256, translucent=0.5)    # the stasis field (D-51)
LATTICE = S_('swflora', 256, 256)       # glowing green lattice under the coffin's dais
BLAST = S_('swdoora', 256, 256)         # heavy riveted blast door: the two lever slabs, the hatch's underside
DOOR = S_('swdoorb', 256, 256)          # cross-braced door: the plain doors, the vault pair (one picture split)
GRATE = S_('swdoorc', 128, 256)         # lattice door: the bolted grate (a solid leaf)
RUBBLE = S_('gn_mtl03', 128, 128)       # fallen slabs (the D6 pyramid's wall cladding)
# Session 23 (A8, review row 39): the dead pyramid was a plain grey placeholder in gn_mtl03; now MM6's black marble
# with glassy blue-grey veins (mystrya): a dark obsidian-like stone (D-71's tone: its light is out).
PYRAMID = S_('mystrya', 128, 128)
PLAQUE9 = S_('sign22', 256, 64)         # bronze plaque: "Nine is the time."
PLAQUE_F = S_('sign128', 256, 128)      # bronze plaque: FEWAEE...
RUNG = S_('gn_mtl02', 128, 128)         # the ladder's rungs: mid brushed steel, pale against the scorched hull
STEEL_DK = S_('gn_mtl03', 128, 128)     # dark steel (no longer on the levers: session 23)
# Session 23 (A8, review row 39): the levers were flat grey bars (gn_mtl02/03). Now the arm is a slice of swpipes'
# teal banded pipe (its 256 texels once up the 176 arm: scale 176/256; u offset centres the pipe on the 32 face),
# the grip a slice of its red pipe with a collar, capped with swhz2dk's red disc; the boss's face is swildk's riveted
# plate with its domed bolt (once, whole), its other faces riveted girder plate.
LEVER_ARM_S = S_('swpipes', 256, 256, scale=0.6875, offset=[52, 0], uneven=True)
LEVER_GRIP_S = S_('swpipes', 256, 256, offset=[186, 64], uneven=True)
LEVER_CAP = S_('swhz2dk', 128, 128, scale=0.375)
LEVER_BOSS_FACE = S_('swildk', 128, 128, fit=True)

GALLERY_H, HALL_H, TALL_H = 448, 512, 640

THEMES = [
    {'id': 'theme:gallery', 'wall': wall(BRACED, GALLERY_H), 'floor': PLATE, 'ceiling': CEIL, 'door': DOOR,
     'reveal': GIRDER,
     'notes': "The galleries and passages: crossed-brace panels with rust (swall4) once up the 448 wall, teal plate floors (swankdk), rust ceiling panels (swceilf)."},
    {'id': 'theme:hall', 'wall': wall(DIAMOND, HALL_H), 'floor': PLATE, 'ceiling': CEIL, 'door': DOOR,
     'reveal': GIRDER,
     'notes': "The halls and rooms: diamond-brace panels (swall2) once up the 512 wall (DD-17's bays: the castle's substructure)."},
    {'id': 'theme:tall', 'wall': wall(DIAMOND, TALL_H), 'floor': PLATE, 'ceiling': CEIL, 'door': DOOR,
     'reveal': GIRDER,
     'notes': "The lift head, the lift foot and the stasis vault: swall2 once up the 640 wall."},
    {'id': 'theme:hull', 'wall': HULL, 'floor': PLATE, 'ceiling': CEIL, 'door': DOOR, 'reveal': GIRDER,
     'notes': "Where the castle came down: scorched, buckled plating (xahullbn) over the ruin stair."},
    {'id': 'theme:shaft', 'wall': HULL, 'floor': RUBBLE, 'ceiling': dict(CEIL, sky=True), 'door': DOOR,
     'reveal': GIRDER,
     'notes': "The rubble shaft: scorched plating (xahullbn) up to the open sky (D7's roof hatch far above), fallen slabs underfoot (gn_mtl03)."},
]


def box(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def dodecagon(cx, cy, r):
    """A twelve-sided room with flat edges facing east (edge 0), north (3), west (6) and south (9); r is the distance
    from the centre to each flat edge."""
    rc = r / math.cos(math.radians(15))
    pts = []
    for k in range(12):
        a = math.radians(-15 + 30 * k)
        pts.append([cx + round(rc * math.cos(a)), cy + round(rc * math.sin(a))])
    # the axis edges exactly on the axis
    t = round(r * math.tan(math.radians(15)))
    pts[0], pts[1] = [cx + r, cy - t], [cx + r, cy + t]
    pts[3], pts[4] = [cx + t, cy + r], [cx - t, cy + r]
    pts[6], pts[7] = [cx - r, cy + t], [cx - r, cy - t]
    pts[9], pts[10] = [cx - t, cy - r], [cx + t, cy - r]
    return pts


SHAFT_C, SHAFT_R = (-8392, 7168), 840          # its east flat edge at x -7552
LADDER_WALL = SHAFT_C[0] - SHAFT_R               # the west flat (x -9232), 450 long
# D-71 P1: the ladder stands off the wall: rungs 24 thick from 40 to 64 off it, every 112 from 96 up; two rails 24 wide
# from 32 to 80 off it (proud of the rungs by 16), the rungs between their inner faces (88 either side of the middle).
LADDER_RUNG = (40, 64)
LADDER_RAIL = (32, 80)
LADDER_HALF = 88                                 # half the clear width between the rails (176)
LADDER_TOP = 1824
LADDER_RUNGS = list(range(96, 1800, 112))        # each rung's underside (16 rungs, the top one 1776-1800)
LADDER_X = LADDER_WALL + sum(LADDER_RUNG) // 2
STASIS_C, STASIS_R = (96, 3904), 864           # its west flat edge at x -768

# D-71 P2: each lever on the lever hall's side wall at y 2496: a pivot boss (0-40 off the wall, 96 along, 96 high,
# centred at LEVER_PIVOT), an arm 32 square (42-74 off the wall) standing 176 up from the pivot, a grip 48 square
# (42-90 off the wall, 48 high) on its top, one mover. Pulled, it swings 180 degrees about the pivot (merge point 30's
# `turn`, axis y through the arm's middle), out from the wall and down, in one second: the lever hangs thrown.
LEVER_Y, LEVER_PIVOT = 2496, 248
LEVER_WALL = {'west': -4096, 'east': -2816}
LEVER_BOSS = (0, 40, 96, 96)           # off the wall from, to; along; high
LEVER_ARM = (42, 74, 32, 176)
LEVER_GRIP = (42, 90, 48, 48)
LEVER_SWING = {'west': 180, 'east': -180}   # degrees about y: the top swings away from the wall


def lever_at(side, near, far):
    """The plan centre of a lever part standing `near` to `far` off its wall."""
    sign = 1 if side == 'west' else -1
    return [LEVER_WALL[side] + sign * (near + far) // 2, LEVER_Y]


def lever_size(side, near, far, along, *_):
    return [far - near, along]


SPUR = [[-4864, 1024], [-4352, 1024], [-4352, 3584], [-4224, 3584], [-4224, 4096], [-4864, 4096]]

# id: (name, outline, floor, ceiling, theme)
R = {
    'stair': ("Ruin stair", box(-256, -320, 1472, 320), FLOOR, 1088, 'theme:hull'),
    'stairhall': ("Undercroft hall", box(-1664, -1024, -384, 384), FLOOR, HALL_H, 'theme:hall'),
    'south': ("South gallery", box(-4224, -768, -1792, -256), FLOOR, GALLERY_H, 'theme:gallery'),
    'south2': ("South gallery, west end", box(-6784, -768, -4352, -256), FLOOR, GALLERY_H, 'theme:gallery'),
    'west': ("West gallery", box(-7424, -768, -6912, 2944), FLOOR, GALLERY_H, 'theme:gallery'),
    'west2': ("West gallery, north end", box(-7424, 3072, -6912, 6784), FLOOR, GALLERY_H, 'theme:gallery'),
    'shaft': ("Rubble shaft", dodecagon(*SHAFT_C, SHAFT_R), FLOOR, 2048, 'theme:shaft'),
    'north': ("North gallery", box(-7424, 6912, -5056, 7424), FLOOR, GALLERY_H, 'theme:gallery'),
    'north2': ("North gallery, east end", box(-4928, 6912, -2560, 7424), FLOOR, GALLERY_H, 'theme:gallery'),
    'column': ("Long gallery", box(-3072, 4736, -2560, 6784), FLOOR, GALLERY_H, 'theme:gallery'),
    'hub': ("Hall of Nine", box(-4096, 3072, -2048, 4608), FLOOR, HALL_H, 'theme:hall'),
    'levers': ("Lever hall", box(-4096, 2048, -2816, 2944), FLOOR, HALL_H, 'theme:hall'),
    'spur': ("Sealed passage", SPUR, FLOOR, GALLERY_H, 'theme:gallery'),
    'workshop': ("Long workshop", box(-6016, -128, -2560, 896), FLOOR, HALL_H, 'theme:hall'),
    'pyramid': ("Pyramid nook", box(-6784, -128, -6144, 1152), FLOOR, HALL_H, 'theme:hall'),
    'wpass': ("West passage", box(-5888, 1024, -5376, 3072), FLOOR, GALLERY_H, 'theme:gallery'),
    'assembly': ("Assembly hall", box(-6784, 3200, -5120, 5120), FLOOR, HALL_H, 'theme:hall'),
    'espur': ("East spur", box(-2432, 384, -2048, 1024), FLOOR, GALLERY_H, 'theme:gallery'),
    'keyvault': ("Key vault", box(-1920, 512, -512, 2048), FLOOR, HALL_H, 'theme:hall'),
    'warden': ("Warden's room", box(-1920, 2176, -512, 3456), FLOOR, HALL_H, 'theme:hall'),
    'skull': ("Lift head", box(-1536, 3584, -896, 4224), FLOOR, TALL_H, 'theme:tall'),
    'liftfoot': ("Lift foot", box(-1536, 3584, -896, 4224), LOW, LOW + TALL_H, 'theme:tall'),
    'stasis': ("Stasis vault", dodecagon(*STASIS_C, STASIS_R), LOW, LOW + TALL_H, 'theme:tall'),
}
ORDER = ['stair', 'stairhall', 'south', 'south2', 'west', 'west2', 'shaft', 'north', 'north2', 'column', 'hub', 'levers', 'spur', 'workshop',
         'pyramid', 'wpass', 'assembly', 'espur', 'keyvault', 'warden', 'skull', 'liftfoot', 'stasis']


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


SIDE4 = {0: 's', 1: 'e', 2: 'n', 3: 'w'}


def wall_name(rid, i):
    return SIDE4[i] if len(outline(rid)) == 4 else i


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


def opening(oid, a, b, at=None, width=384, height=384, link=None, **kw):
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
    if width == 'full':
        d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b, 'from_wall': wall_name(a, i),
             'to_wall': wall_name(b, j), 'width': 'full', 'height': 'full'}
        if link:
            d['link'] = link
        d.update(kw)
        return d
    if at is None:
        at = (lo + hi) / 2
    if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
        raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
    forward = (p1[ax] - p0[ax]) > 0
    along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b, 'from_wall': wall_name(a, i), 'to_wall': wall_name(b, j)}
    if along != 0.5:
        d['along'] = along
    if link:
        d['link'] = link
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


DOOR_W = DOOR_H = 384            # plain doors and slabs: one square picture once over a square leaf
GRATE_W, GRATE_H = 192, 384      # the bolted grate: swdoorc's 1:2 once
OPEN_W = 384                     # open ways between rooms
LIFT_AT, LIFT_SIZE = [-1216, 3904], [320, 320]
LIFT_TRAVEL = FLOOR - LOW

OPENINGS = [
    opening('open:stair_hall', 'stair', 'stairhall', at=0, width=OPEN_W, height=448, link='link:1',
            notes="The stair's foot opens west into the undercroft hall."),
    opening('open:gallery_door', 'stairhall', 'south', at=-512, link='link:2', notes="The gallery door."),
    opening('open:south_mouth', 'south', 'south2', width='full', height='full'),
    opening('open:guard_door', 'south2', 'west', at=-512, link='link:3', notes="The guard door."),
    opening('open:west_mouth', 'west', 'west2', width='full', height='full'),
    opening('open:west_north', 'west2', 'north', at=-7168, width=OPEN_W, link='link:4'),
    opening('open:north_mouth', 'north', 'north2', width='full', height='full'),
    opening('open:shaft_door', 'shaft', 'north', at=7168, width=DOOR_W, height=DOOR_H, link='link:5',
            notes="The shaft door in the shaft's east flat."),
    opening('open:north_door', 'north2', 'column', at=-2816, link='link:6', notes="The north door."),
    opening('open:column_hub', 'column', 'hub', at=-2816, width=OPEN_W, link='link:7'),
    opening('open:hub_levers', 'hub', 'levers', at=-3456, width=OPEN_W, link='link:8'),
    opening('open:hub_spur', 'hub', 'spur', at=3840, width=OPEN_W, link='link:9'),
    opening('open:west_slab', 'spur', 'workshop', at=-4608, link='link:10',
            notes="Lever A's slab: a shut bulkhead at the sealed passage's end."),
    opening('open:workshop_nook', 'workshop', 'pyramid', at=128, width=OPEN_W, link='link:11'),
    opening('open:workshop_wpass', 'workshop', 'wpass', at=-5632, width=OPEN_W, link='link:12'),
    opening('open:works_door', 'wpass', 'assembly', at=-5632, link='link:13', notes="The assembly hall's works door."),
    opening('open:workshop_espur', 'workshop', 'espur', at=640, width=OPEN_W, link='link:14'),
    opening('open:east_slab', 'espur', 'keyvault', at=768, link='link:15',
            notes="Lever B's slab: a shut bulkhead at the east spur's end."),
    opening('open:warden_door', 'keyvault', 'warden', at=-1216, link='link:16', notes="The warden's door."),
    opening('open:skull_door', 'warden', 'skull', at=-1216, link='link:17', notes="The skull door."),
    opening('open:vault_pair', 'liftfoot', 'stasis', at=3904, link='link:19', notes="The stasis vault's pair."),
    opening('open:grate', 'workshop', 'south', at=-3328, width=GRATE_W, height=GRATE_H, link='link:20',
            notes="The bolted grate in the workshop's south wall."),
    {'id': 'open:lift_shaft', 'from': 'room:skull', 'to': 'room:liftfoot', 'in': 'floor', 'at': LIFT_AT,
     'size': LIFT_SIZE, 'link': 'link:18', 'notes': "The lift's hole in the lift head's floor (768 down)."},
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


def panel(pid, length, bottom, height, surface, notes=None, offset=None, **kw):
    d = {'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    if pid:
        d['id'] = pid
    if offset is None:
        d['at'] = 'centre'
    else:
        d['offset'] = offset
    d.update(kw)
    if notes:
        d['notes'] = notes
    return d


STAIR_FROM, STAIR_TO, STAIR_TOP = 256, 1280, 640
HEAD_D = 192
STATUE_AT = [-1216, 272]                 # the statue's plinth centre by the undercroft hall's north wall
PYR_AT, PYR_BASE, PYR_H, PLINTH = [-6464, 768], 384, 352, 448
DAIS_AT, DAIS_SIZE, DAIS_RISE = [STASIS_C[0], STASIS_C[1]], [576, 384], 48
COFFIN_SIZE, COFFIN_RISE = [256, 96], 80
COFFIN_TOP = LOW + DAIS_RISE + COFFIN_RISE
KEYBOX_AT = [-1216, 560]
ROUND_WALLS = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11]   # the stasis vault's walls round the ring (6 is the pair's)

EXTRA = {
    'stair': {
        'platforms': [{'id': 'platform:stair_head', 'rise': 32, 'base': STAIR_TOP - 32,
                       'outline': [[1472 - HEAD_D, -320], [1472, -320], [1472, 320], [1472 - HEAD_D, 320]],
                       'surface': dict(GIRDER), 'top_surface': dict(PLATE), 'bottom_surface': dict(GIRDER),
                       'notes': "The stair's head (640) under the gatehouse hatch: the way up to D6."}],
        'flights': [{'from': [STAIR_FROM, 0], 'to': [STAIR_TO, 0], 'to_height': STAIR_TOP, 'width': 384, 'steps': 20,
                     'open_below': 32, 'sides': {'height': 48, 'thickness': 16, 'surface': dict(GIRDER)},
                     'notes': "Twenty steps of 32 up east from the foot to the head under the hatch."}],
        'notes': "The ruin stair under the gatehouse's floor: the arrival from D6 at its foot (0, 0, 0) facing west into the undercroft hall; the stair climbs east 640 to the hatch's underside (the exit to D6). Quiet.",
    },
    'stairhall': {
        'notes': "The first hall: cracked teal plates; Alamar's statue by the north wall speaks when the party first comes near (m39.statue). The gallery door west. Quiet.",
    },
    'south': {'space': 'room:south',
              'notes': "The south gallery, west from the gallery door; the bolted grate in its north wall."},
    'south2': {'space': 'room:south', 'notes': "The south gallery's west end: the guard door."},
    'west2': {'space': 'room:west', 'notes': "The west gallery's north end."},
    'north2': {'space': 'room:north', 'notes': "The north gallery's east end: the north door; its broken end wall.",
               'walls': [{'wall': 'e', 'surface': dict(HULL),
                          'notes': "The gallery's broken east end: a rubble fall of scorched plating."}]},
    'west': {
        'walls': [{'wall': 's', 'surface': dict(HULL),
                   'notes': "The gallery's broken south end: the castle came down here."}],
        'notes': "The west gallery, north from the guard door to the north gallery.",
    },
    'shaft': {
        'walls': [{'wall': 6, 'panels': [panel('panel:ladder', 450, 0, 2048, dict(HULL),
                                               "The shaft's own scorched plating behind the ladder, the whole west flat (D-71 P1: no backplate; the click strip, 'Climb up through the hatch?').")]}],
        'platforms': [plat(f'platform:ladder_rail_{n}', [LADDER_WALL + sum(LADDER_RAIL) // 2, SHAFT_C[1] + dy],
                           [LADDER_RAIL[1] - LADDER_RAIL[0], 24], LADDER_TOP, dict(GIRDER), dict(GIRDER),
                           "A rail of the steel ladder, riveted, standing 32 off the wall and 16 proud of the rungs.")
                      for n, dy in (('s', -LADDER_HALF - 12), ('n', LADDER_HALF + 12))]
                     + [plat(f'platform:ladder_rung_{k + 1:02d}', [LADDER_X, SHAFT_C[1]],
                             [LADDER_RUNG[1] - LADDER_RUNG[0], 2 * LADDER_HALF], 24, dict(RUNG), dict(RUNG),
                             "A rung of the steel ladder (D-71 P1: a bar 24 thick, 40 off the wall).", base=z,
                             bottom_surface=dict(RUNG), end_surface=dict(RUNG, fit=False))
                        for k, z in enumerate(LADDER_RUNGS)]
                     + [plat(None, [-8700, 6600], [320, 192], 32, dict(RUBBLE), dict(RUBBLE),
                             "A fallen slab of the castle above, by the wall."),
                        plat(None, [-8100, 7750], [256, 160], 48, dict(RUBBLE), dict(RUBBLE),
                             "A fallen slab, by the wall.")],
        'notes': "Where the castle above came down: a round shaft of scorched plating and rubble rising out of sight to D7's roof hatch, grey light far above (open sky). The arrival from D7 at its foot facing east to the shaft door. Quiet.",
    },
    'north': {'notes': "The north gallery, east from the shaft door and the west gallery's end."},
    'column': {'notes': "The long gallery, south from the north door to the Hall of Nine (its niches left out, D-69 change 9)."},
    'hub': {
        'pillars': [{'at': [x, y], 'size': [256, 256], 'surface': dict(COLUMN)} for x in (-3712, -2432)
                    for y in (3456, 4224)],
        'walls': [{'wall': 'e', 'panels': [
            panel(None, 320, 160, 128, dict(GIRDER), "The plaque's riveted frame."),
            panel('panel:plaque_nine', 256, 192, 64, dict(PLAQUE9, fit=True),
                  "The plaque: 'Nine is the time.' (m39.plaque_nine).", cover=True)]}],
        'notes': "The Hall of Nine: four machine columns, the plaque on its east wall; the lever hall south, the sealed passage west.",
    },
    'levers': {'walls': [{'wall': w, 'panels': [panel(None, 160, 16, 464, dict(GIRDER),
                                                      "The lever's riveted backplate (D-71 P2).")]} for w in ('w', 'e')],
               'platforms': [plat(f'platform:lever_{side}_boss', lever_at(side, *LEVER_BOSS[:2]),
                                  lever_size(side, *LEVER_BOSS), LEVER_BOSS[3], dict(LEVER_BOSS_FACE), dict(GIRDER),
                                  "The lever's pivot boss on its plate (D-71 P2): a riveted plate with a domed bolt.",
                                  base=LEVER_PIVOT - 48, bottom_surface=dict(GIRDER), end_surface=dict(GIRDER, fit=False))
                             for side in ('west', 'east')],
               'notes': "The lever hall: the west and the east lever on their walls (a pivot boss and a steel arm with a grip on a riveted plate, D-71 P2); neither slab can be seen from here."},
    'spur': {'notes': "The sealed passage: west and south from the Hall of Nine to lever A's slab."},
    'workshop': {
        'platforms': [plat(None, [x, 832], [384, 96], 96, dict(GIRDER), dict(SCREEN, fit=True),
                           "A machine bench against the north wall.", end_surface=dict(GIRDER, fit=False))
                      for x in (-5120, -3840)]
                     + [plat(None, [-2688, 0], [96, 256], 96, dict(GIRDER), dict(GIRDER),
                             "A bench against the east wall.", end_surface=dict(GIRDER, fit=False))],
        'notes': "The long workshop: machine benches by the walls; the sealed passage's slab and the west passage north, the pyramid nook west, the east spur east, the bolted grate south.",
    },
    'pyramid': {
        'platforms': [plat('platform:plinth', PYR_AT, [PLINTH, PLINTH], 32, dict(GIRDER), dict(GIRDER),
                           "The dead pyramid's plinth: riveted plate."),
                      # F62's lid rule (xeen-fb4-dungeon5, 2026-11-25): sunk 8 into the plinth, its top where it was
                      # (its bottom lay on the plinth's top: XD-17's pyramid so wedged a party walking into its foot)
                      plat('platform:pyramid', PYR_AT, [PYR_BASE, PYR_BASE], PYR_H + 8, dict(PYRAMID), dict(PYRAMID),
                           "A small dark Ancient pyramid (four sloped faces of black veined marble, mystrya, D-71's tone, session 23): hover 'Pyramid' (m39.pyramid).",
                           base=24, top_size=[16, 16])],
        'notes': "Dead end: the dark Ancient pyramid on its plinth and a T6 chest beside it.",
    },
    'wpass': {'notes': "The west passage north from the workshop to the assembly hall's works door."},
    'assembly': {
        'platforms': [plat(None, [x, 5040], [256, 96], 224, dict(GIRDER), dict(GIRDER),
                           "A stall of a half-built frame against the north wall.", end_surface=dict(GIRDER, fit=False))
                      for x in (-6400, -5504)]
                     + [plat(None, [-6704, y], [96, 256], 224, dict(GIRDER), dict(GIRDER),
                             "A stall against the west wall.", end_surface=dict(GIRDER, fit=False))
                        for y in (3840, 4480)],
        'walls': [{'wall': 'n', 'panels': [panel('panel:plaque_fewaee', 256, 256, 128, dict(PLAQUE_F, fit=True),
                                                 "The plaque FEWAEEFFWAEF... (aaze0052:14).", offset=704)]}],
        'notes': "Alamar's robot works: stalls of half-built frames along the walls, the plaque on the north wall, a T6 chest in the foreman's corner.",
    },
    'espur': {'notes': "The east spur: a short spur off the workshop's east end, ending in lever B's slab."},
    'keyvault': {
        'platforms': [plat(None, [-560, y], [96, 256], 192, dict(GIRDER), dict(GIRDER),
                           "A rack of sealed boxes against the east wall.", end_surface=dict(GIRDER, fit=False))
                      for y in (1088, 1600)]
                     + [plat(None, [-1872, y], [96, 256], 192, dict(GIRDER), dict(GIRDER),
                             "A rack of sealed boxes against the west wall (untitled, D-71; clear of the slab's way in).",
                             end_surface=dict(GIRDER, fit=False))
                        for y in (1344, 1856)]
                     + [plat('platform:keybox', KEYBOX_AT, [128, 96], 96, dict(GIRDER), dict(GIRDER),
                             "The box on the south wall: hover 'Box' (aaze0052:2), the Key to the Dragon Tower once.",
                             end_surface=dict(GIRDER, fit=False))],
        'notes': "Alamar's strongroom: racks of sealed boxes; the box with the Dragon Tower key on the south wall; the warden's door north.",
    },
    'warden': {
        'platforms': [plat(None, [-576, y], [128, 384], 128, dict(MACHINE, fit=False), dict(SCREEN, fit=True),
                           "A console against the east wall.", end_surface=dict(GIRDER, fit=False))
                      for y in (2560, 3072)],
        'walls': [{'wall': 'e', 'panels': [panel(None, 256, 192, 256, dict(MACHINE, fit=True), "A machine panel.",
                                                 offset=512)]}],
        'notes': "The warden's room: consoles and a machine panel on the east wall, the warden's chest on the west wall, the skull door north.",
    },
    'skull': {'notes': "The lift head behind the skull door: the cage goes down 768."},
    'liftfoot': {'notes': "The lift's foot: a short cold passage; the stasis vault's pair east."},
    'stasis': {
        'platforms': [plat('platform:dais', DAIS_AT, DAIS_SIZE, DAIS_RISE, dict(GIRDER), dict(LATTICE),
                           "The dais: the glowing lattice (swflora) under the coffin."),
                      plat('platform:coffin', DAIS_AT, COFFIN_SIZE, COFFIN_RISE, dict(GIRDER), dict(GIRDER),
                           "Roland's stasis coffin, a long steel box (hover 'Coffin', aaze0052:7).", base=DAIS_RISE,
                           end_surface=dict(GIRDER, fit=False))],
        'walls': [{'wall': w, 'panels': [panel(None, 256, 128, 256, dict(MACHINE, fit=True),
                                               "Alamar's machine ring.")]} for w in ROUND_WALLS],
        'notes': "The set piece: a round chamber, Alamar's machine ring round the dais; on the dais the stasis coffin under the field; a T6 chest by the wall.",
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
    for o in OPENINGS:
        print(o['id'], o.get('from_wall'), o.get('to_wall'), o.get('along'))
