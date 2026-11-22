#!/usr/bin/env python3
"""DD-19 Wizard Quarter: the geometry (rooms, openings) shared by L2, L3 and L4.

One BLV of three floors in one frame (x east, y north, z up; z 0 the court's paving inside Sandcaster's guild gate):
- the court (0, open to the sky, preset xeen_darkside_fading) with the guild gate in its south wall, the Mirage Guild's
  double door west, the Sorceress HQ's east, three arches north into the arcade under the covered bridge, and the Guild
  Common behind the arcade (Weights and Measures east of it, the quarters stair north);
- the upper floors (640): the Mirage Guild's mirror gallery and Hall of Mirages with Xenoc's study (west), the covered
  bridge over the arcade, the Sorceress HQ's scrying room, Morgana's sanctum and wardrobe (east);
- the undercroft (-512): the potion alcoves, the wizards' quarters, the vaulted undercroft under the court and the
  Common with the guild vault south of it, the sorceresses' quarters and the alembic cellar.
Two-storey rooms carry the stairs (DD-14's way: a hanging head and one flight): the Mirage stair (0 to 640, its head
the graph's Mirage stair head), the HQ stair (0 to 640, its head the HQ stair head before Morgana's ward), the potion
alcoves (-512 to 0, entered at their head from the Mirage stair), the quarters stair (-512 to 0, its foot the graph's
stair foot) and the HQ back stair (-512 to 0). Rooms are rectangles; walls between rooms are 128 thick; the inside is
larger than the outside (D-42's general rule).
"""

UP, G0, UN = 640, 0, -512
SKY = 1536
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Castle Ironfist's hc set (the town kit's wizard-quarter stone): the court, the arcade, the bridge, the Common
HCWALL = S_('hcwall', 128, 256, scale=2)      # pink ashlar under its crenellated coping, once up a 512 wall
HCWIN = S_('hcwindo', 128, 256)               # a gothic window in the ashlar
HCTRI = S_('hctriw', 128, 256)                # the triple window
HCBUST = S_('hcuniq2', 128, 256)              # a statue niche (a bust)
HCSTATUE = S_('hcuniq3', 128, 256)            # a statue niche (a robed figure)
HCDOOR = S_('hcsmdr', 128, 256)               # an arched oak door in the ashlar
GATE = S_('hclgdr', 256, 256)                 # the guild gate's inside face (D3's picture outside)
PILASTER_L = S_('hcw1le', 128, 256)           # ashlar with a pilaster on its left edge
PILASTER_R = S_('hcw1re', 128, 256)           # ... on its right edge
MARBLE = S_('t1f1', 128, 128)                 # pale marble flags with a red star
MARBLE2 = S_('t1f2', 128, 128)                # green and red marble lozenges (the Common)
WOODCEIL = S_('cedsqrdk', 128, 128)           # red cedar boards: the hc rooms' ceilings
TRIM = S_('t1trimb', 32, 32)                  # pink marble trim: copings, the font's rim
# MM6 Icewind Keep (6d15): the Mirage Guild
ICEWALL = S_('t3wspp', 128, 256, scale=2)     # grey-blue brick
ICEBAND = S_('t3wbltd', 256, 256, scale=2)    # grey brick under its red-brick cornice: the Hall of Mirages
ICEFLOOR = S_('d2flor3', 128, 128)            # stone panels in a frame
BEAMS = S_('d2ceil1', 256, 256)               # beam ceiling
SHIMMER = S_('orair32', 32, 32, scale=4)      # the Hall of Mirages' floor, shimmering like water
WOOD = S_('cedsqrdk', 128, 128)               # dark red cedar boards: tables, benches, beds, racks
WOOD_H = S_('bemh32a', 256, 32)               # a wooden rail (frames)
WOOD_V = S_('bemsv16b', 16, 128)              # a wooden post (frames)
ICEDOOR = S_('d8dord', 128, 256)              # an iron-studded door
# MM6 Corlagon's Estate (6d11): the Sorceress HQ and the undercroft
DARKWALL = S_('d2wlbmed', 256, 256, scale=2)  # dark brick: the HQ's rooms
CELLWALL = S_('d2wlbctr', 128, 256, scale=1.5)  # dark brick: the undercroft (384 high)
STAIRWALL = S_('d2wlbctr', 128, 256, scale=2)   # the same brick in the tall stair rooms
FLAGS = S_('d2flor4', 128, 128)               # rough flags
EARTHCEIL = S_('d2ceil3', 256, 256)           # dark vault
IRONDOOR = S_('cvdor3', 128, 256)             # iron door
SKULL = S_('d2skulas', 64, 64)                # a skull relief: the scrying room's niches
BONES = S_('d2niche1', 256, 256)              # a niche of bones: the alembic cellar
# pictures and leaves
MIRROR = S_('xkmirror', 128, 128)             # silvered glass (A6's, D-37 (2))
WARD = S_('xufield', 256, 256, translucent=1)  # XD-25's field of light (reused)
IRON = S_('xwiron', 128, 128)                 # iron plate: the lamp bracket, the scales
LEAVES = [[S_('t07c03c', 128, 256), S_('t07c03d', 128, 256)]]   # the great-hall doors' two wings
SKYFACE = S_('cedsqrdk', 128, 128, sky=True)

THEMES = [
    {'id': 'theme:court', 'wall': HCWALL, 'floor': MARBLE, 'ceiling': SKYFACE, 'door': HCDOOR, 'reveal': dict(HCWALL),
     'notes': "The guild court, open to the sky: the town kit's pink ashlar (hcwall, once per 512 storey), pale marble flags (t1f1)."},
    {'id': 'theme:hc', 'wall': HCWALL, 'floor': MARBLE2, 'ceiling': WOODCEIL, 'door': HCDOOR, 'reveal': dict(HCWALL),
     'notes': "The guilds' shared rooms in the court's stone: pink ashlar, marble lozenges (t1f2), cedar ceilings (cedsqrdk)."},
    {'id': 'theme:bridge', 'wall': HCWALL, 'floor': MARBLE, 'ceiling': WOODCEIL, 'door': HCDOOR, 'reveal': dict(HCWALL),
     'notes': "The arcade and the covered bridge over it: pink ashlar, marble flags, cedar."},
    {'id': 'theme:mirage', 'wall': ICEWALL, 'floor': ICEFLOOR, 'ceiling': BEAMS, 'door': ICEDOOR, 'reveal': dict(ICEWALL),
     'notes': "The Mirage Guild (MM6 Icewind Keep 6d15): grey-blue brick (t3wspp), framed stone panels (d2flor3), beams (d2ceil1)."},
    {'id': 'theme:mirage_hall', 'wall': ICEBAND, 'floor': SHIMMER, 'ceiling': BEAMS, 'door': ICEDOOR, 'reveal': dict(ICEWALL),
     'notes': "Xenoc's Hall of Mirages: grey brick under a red cornice (t3wbltd), a floor of orair32 shimmering like water."},
    {'id': 'theme:mirage_stair', 'wall': ICEWALL, 'floor': ICEFLOOR, 'ceiling': BEAMS, 'door': ICEDOOR, 'reveal': dict(ICEWALL),
     'notes': "The Mirage stair: Icewind brick two storeys high."},
    {'id': 'theme:hq', 'wall': DARKWALL, 'floor': FLAGS, 'ceiling': EARTHCEIL, 'door': IRONDOOR, 'reveal': dict(STAIRWALL),
     'notes': "The Sorceress HQ (MM6 Corlagon's Estate 6d11): dark brick (d2wlbmed), rough flags (d2flor4), dark vaults (d2ceil3)."},
    {'id': 'theme:hq_stair', 'wall': STAIRWALL, 'floor': FLAGS, 'ceiling': EARTHCEIL, 'door': IRONDOOR, 'reveal': dict(STAIRWALL),
     'notes': "The HQ's stairs: Corlagon's dark brick two storeys high (d2wlbctr)."},
    {'id': 'theme:under', 'wall': CELLWALL, 'floor': FLAGS, 'ceiling': EARTHCEIL, 'door': IRONDOOR, 'reveal': dict(CELLWALL),
     'notes': "The undercroft (6d11): dark brick (d2wlbctr) under low dark vaults, rough flags."},
]

# id: (name, box, floor, ceiling, theme)
R = {
    # the court level (0)
    'court': ("Guild court", (-1024, 0, 1024, 1536), G0, SKY, 'theme:court'),
    'arcade': ("The arcade", (-1024, 1664, 1024, 2048), G0, G0 + 512, 'theme:bridge'),
    'common': ("Guild Common", (-1024, 2176, 1024, 3456), G0, G0 + 512, 'theme:hc'),
    'weights': ("Weights and Measures", (1152, 2176, 2048, 2944), G0, G0 + 448, 'theme:hc'),
    'mirage_foyer': ("Mirage Guild", (-2304, 256, -1152, 2048), G0, G0 + 512, 'theme:mirage'),
    'illusions': ("Hall of illusions", (-3584, 256, -2432, 1536), G0, G0 + 512, 'theme:mirage'),
    'hq_foyer': ("Sorceress HQ", (1152, 256, 2304, 2048), G0, G0 + 512, 'theme:hq'),
    'robing': ("Robing room", (3712, 256, 4864, 1536), G0, G0 + 512, 'theme:hq'),
    # two storeys, 0 to 640: the stairs up (their heads the graph's stair heads)
    'mirage_stair': ("Mirage stair", (-3584, 1664, -2432, 2944), G0, UP + 512, 'theme:mirage_stair'),
    'hq_stair': ("HQ stair", (2432, 256, 3584, 1536), G0, UP + 512, 'theme:hq_stair'),
    # the upper floors (640)
    'mirror_gallery': ("Mirror gallery", (-3200, 256, -2432, 1536), UP, UP + 512, 'theme:mirage'),
    'mirage_hall': ("Hall of Mirages", (-2304, 256, -1152, 2048), UP, UP + 512, 'theme:mirage_hall'),
    'xenoc_study': ("Xenoc's study", (-2304, -768, -1408, 128), UP, UP + 448, 'theme:mirage'),
    'bridge': ("Guild bridge", (-1024, 1664, 1024, 2048), UP, UP + 448, 'theme:bridge'),
    'scrying': ("Scrying room", (1152, 256, 2304, 2048), UP, UP + 512, 'theme:hq'),
    'morgana_sanctum': ("Morgana's sanctum", (2432, 1664, 4224, 3456), UP, UP + 512, 'theme:hq'),
    'wardrobe': ("Morgana's wardrobe", (4352, 1664, 5120, 2560), UP, UP + 448, 'theme:hq'),
    # two storeys, -512 to 0: the stairs down
    'alcoves': ("Potion alcoves", (-4992, 1664, -3712, 2944), UN, G0 + 512, 'theme:hq_stair'),
    'quarters_stair': ("Quarters stair", (-384, 3584, 384, 4864), UN, G0 + 512, 'theme:hq_stair'),
    'back_stair': ("HQ back stair", (3712, 1664, 4864, 2944), UN, G0 + 512, 'theme:hq_stair'),
    # the undercroft (-512)
    'quarters_w': ("Guild Quarters (wizards)", (-3584, 1664, -896, 2816), UN, UN + 384, 'theme:under'),
    'undercroft': ("Undercroft", (-768, 512, 768, 3456), UN, UN + 384, 'theme:under'),
    'quarters_e': ("Guild Quarters (sorceresses)", (896, 1664, 2304, 2944), UN, UN + 384, 'theme:under'),
    'alembic': ("Alembic cellar", (2432, 1664, 3584, 2944), UN, UN + 384, 'theme:under'),
    'vault': ("Guild vault", (-640, -896, 640, 384), UN, UN + 384, 'theme:under'),
}
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
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


DOOR_W, DOOR_H = 224, 384          # single doors (hcsmdr, d8dord, cvdor3 at 1.75 x 1.5)
DOUBLE_W, DOUBLE_H = 448, 448      # the great-hall doors: two leaves 224 x 448 (the wing pictures' 1:2)
PASS_W = 384
HEAD_D = 384


def strip(box, side, depth=HEAD_D):
    x0, y0, x1, y1 = box
    if side == 'n':
        return [[x0, y1 - depth], [x1, y1 - depth], [x1, y1], [x0, y1]]
    if side == 's':
        return [[x0, y0], [x1, y0], [x1, y0 + depth], [x0, y0 + depth]]
    if side == 'e':
        return [[x1 - depth, y0], [x1, y0], [x1, y1], [x1 - depth, y1]]
    return [[x0, y0], [x0 + depth, y0], [x0 + depth, y1], [x0, y1]]


def head(pid, outline_, floor, top, surface, notes, top_surface=None, bottom=None):
    return {'id': pid, 'rise': 32, 'base': top - floor - 32, 'outline': outline_, 'surface': dict(surface),
            'top_surface': dict(top_surface or FLAGS), 'bottom_surface': dict(bottom or EARTHCEIL), 'notes': notes}


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


def box(rid):
    return R[rid][1]


def wall_offset(rid, wall, centre, length):
    """The offset of a panel `length` long centred at `centre` (x on s/n walls, y on e/w walls) from the wall's start
    (walls run counter-clockwise: s east, e north, n west, w south)."""
    x0, y0, x1, y1 = box(rid)
    if wall == 's':
        return centre - length / 2 - x0
    if wall == 'n':
        return x1 - centre - length / 2
    if wall == 'e':
        return centre - length / 2 - y0
    return y1 - centre - length / 2


def framed(rid, pid, wall, centre, bottom, length, height, surface, notes, frame_h=WOOD_H, frame_v=WOOD_V, wh=32, wv=48):
    """A picture in a wooden frame (the mirror), so it never meets the brick bare (texture fit's feature_border): rails
    of bemh32a (8:1) top and bottom, posts of bemsv16b (1:8) at the sides, each at its picture's proportions."""
    o = wall_offset(rid, wall, centre, length)
    return [panel(pid, length, bottom, height, surface, notes, offset=o),
            panel(None, length + 2 * wv, bottom + height, wh, dict(frame_h, fit=True), offset=o - wv),
            panel(None, length + 2 * wv, bottom - wh, wh, dict(frame_h, fit=True), offset=o - wv),
            panel(None, wv, bottom, height, dict(frame_v, fit=True), offset=o - wv),
            panel(None, wv, bottom, height, dict(frame_v, fit=True), offset=o + length)]


MS_BOX, HS_BOX, AL_BOX = box('mirage_stair'), box('hq_stair'), box('alcoves')
QS_BOX, BS_BOX = box('quarters_stair'), box('back_stair')
STAIR_W = 320

OPENINGS = [
    # the court
    opening('open:court_mirage', 'court', 'mirage_foyer', at=768, width=DOUBLE_W, height=DOUBLE_H, link='link:court_mirage'),
    opening('open:court_hq', 'court', 'hq_foyer', at=768, width=DOUBLE_W, height=DOUBLE_H, link='link:court_hq'),
    opening('open:arch_w', 'court', 'arcade', at=-640, width=384, height=448, link='link:court_arcade',
            notes="The arcade's west arch."),
    opening('open:arch_c', 'court', 'arcade', at=0, width=384, height=448, link='link:court_arcade',
            notes="The arcade's middle arch."),
    opening('open:arch_e', 'court', 'arcade', at=640, width=384, height=448, link='link:court_arcade',
            notes="The arcade's east arch."),
    opening('open:arcade_common', 'arcade', 'common', at=0, width=DOOR_W, height=DOOR_H, link='link:court_common'),
    opening('open:common_weights', 'common', 'weights', at=2560, width=DOOR_W, height=DOOR_H, link='link:common_weights'),
    opening('open:common_qstair', 'common', 'quarters_stair', at=-192, width=256, height=384, link='link:common_qstair'),
    # the bridge's windows down into the court
    opening('open:bridge_win_w', 'bridge', 'court', at=-512, width=256, height=192, sill=128,
            notes="A window of the bridge down into the court."),
    opening('open:bridge_win_c', 'bridge', 'court', at=0, width=256, height=192, sill=128,
            notes="A window of the bridge down into the court."),
    opening('open:bridge_win_e', 'bridge', 'court', at=512, width=256, height=192, sill=128,
            notes="A window of the bridge down into the court."),
    # the Mirage Guild
    opening('open:mirage_illusions', 'mirage_foyer', 'illusions', at=896, width=PASS_W, height=384, link='link:mirage_illusions'),
    opening('open:illusions_stair', 'illusions', 'mirage_stair', at=-3264, width=256, height=384, link='link:illusions_stair'),
    opening('open:mirage_up', 'mirage_stair', 'mirror_gallery', at=-2752, width=320, height=384, link='link:mirage_up',
            notes="The Mirage stair's head onto the mirror gallery."),
    opening('open:mirage_down', 'mirage_stair', 'alcoves', at=2432, width=256, height=384, link='link:mirage_down',
            notes="From the Mirage stair's floor onto the alcoves' head (0)."),
    opening('open:mirage_wall', 'mirror_gallery', 'mirage_hall', at=896, width=256, height=384, link='link:mirage_wall',
            notes="The mirage: a wall that is not there (door:mirage, passable)."),
    opening('open:hall_study', 'mirage_hall', 'xenoc_study', at=-1664, width=DOOR_W, height=DOOR_H, link='link:hall_study'),
    opening('open:hall_bridge', 'mirage_hall', 'bridge', at=1856, width=DOOR_W, height=DOOR_H, link='link:hall_bridge'),
    opening('open:bridge_scry', 'bridge', 'scrying', at=1856, width=320, height=384, link='link:bridge_scry'),
    # the Sorceress HQ
    opening('open:hq_stair', 'hq_foyer', 'hq_stair', at=640, width=256, height=384, link='link:hq_stair'),
    opening('open:stair_robing', 'hq_stair', 'robing', at=640, width=DOOR_W, height=DOOR_H, link='link:stair_robing'),
    opening('open:scry_landing', 'scrying', 'hq_stair', at=1344, width=256, height=384, link='link:scry_landing'),
    opening('open:ward', 'hq_stair', 'morgana_sanctum', at=3008, width=256, height=384, link='link:ward',
            notes="Morgana's door at the HQ stair's head: the ward of light (door:ward)."),
    opening('open:sanctum_wardrobe', 'morgana_sanctum', 'wardrobe', at=2112, width=DOOR_W, height=DOOR_H,
            link='link:sanctum_wardrobe'),
    opening('open:robing_back', 'robing', 'back_stair', at=4160, width=256, height=384, link='link:back_up',
            notes="The robing room onto the back stair's head (0)."),
    # the undercroft
    opening('open:alcoves_qw', 'alcoves', 'quarters_w', at=1920, width=320, height=320, link='link:alcoves_qw'),
    opening('open:qw_undercroft', 'quarters_w', 'undercroft', at=2240, width=DOOR_W, height=320, link='link:qw_undercroft'),
    opening('open:undercroft_foot', 'undercroft', 'quarters_stair', at=160, width=288, height=320, link='link:undercroft_foot'),
    opening('open:undercroft_qe', 'undercroft', 'quarters_e', at=2240, width=DOOR_W, height=320, link='link:foot_qe'),
    opening('open:qe_alembic', 'quarters_e', 'alembic', at=2304, width=PASS_W, height=320, link='link:qe_alembic'),
    opening('open:alembic_back', 'alembic', 'back_stair', at=2752, width=DOOR_W, height=320, link='link:alembic_back'),
    opening('open:vault', 'undercroft', 'vault', at=0, width=256, height=320, link='link:vault_door'),
]

# The undercroft's pillars: two rows of four under its vault.
UNDERCROFT_PILLARS = [(x, y) for x in (-320, 320) for y in (1152, 1792, 2432, 3072)]
ARRIVAL_AT = [0, 384]
GATE_AT = 0                      # the guild gate's centre on the court's south wall


def chair(pid, at, facing, notes, base=0):
    """A carved chair: a seat block and a back beside it on the side away from `facing` ('n', 's', 'e', 'w')."""
    x, y = at
    back = {'n': (0, -64, [96, 32]), 's': (0, 64, [96, 32]), 'e': (-64, 0, [32, 96]), 'w': (64, 0, [32, 96])}[facing]
    kw = {'base': base} if base else {}
    return [plat(pid, [x, y], [96, 96], 48, dict(WOOD), dict(WOOD), notes, **kw),
            plat(None, [x + back[0], y + back[1]], back[2], 160, dict(WOOD), dict(WOOD), "The chair's back.", **kw)]


EXTRA = {
    'court': {
        'notes': "The guild court, open to Darkside's sky: the guild gate behind the arrival (south), the Mirage Guild's double door west, the Sorceress HQ's east, three arches north under the covered bridge into the arcade. Statue niches flank the gate; windows over the double doors. No monster (D-11.3).",
    },
    'mirage_stair': {
        'platforms': [head('platform:mirage_head', strip(MS_BOX, 's'), G0, UP, ICEWALL,
                           "The Mirage stair's head (640, the graph's mirage_landing) along its south wall: the mirror gallery south.",
                           top_surface=ICEFLOOR, bottom=BEAMS)],
        'flights': [{'from': [-3008, 2752], 'to': [-3008, 2048], 'to_height': UP, 'width': STAIR_W, 'steps': 20,
                     'open_below': 32, 'notes': "Twenty steps of 32 up south to the head."}],
        'notes': "The Mirage Guild's stair, two storeys: in from the hall of illusions under the head, north along the west wall to the foot, twenty steps up south to the head and the mirror gallery; the alcoves' head through the west wall.",
    },
    'hq_stair': {
        'platforms': [head('platform:hq_head', strip(HS_BOX, 'n'), G0, UP, STAIRWALL,
                           "The HQ stair's head (640, the graph's hq_landing) along its north wall: the scrying room west, Morgana's ward north.")],
        'flights': [{'from': [3008, 448], 'to': [3008, 1152], 'to_height': UP, 'width': STAIR_W, 'steps': 20,
                     'open_below': 32, 'notes': "Twenty steps of 32 up north to the head, facing Morgana's door."}],
        'notes': "The Sorceress HQ's stair, two storeys: the foyer west, the robing room's door east; twenty steps up north to the head before Morgana's ward.",
    },
    'alcoves': {
        'platforms': [head('platform:alcoves_head', strip(AL_BOX, 'e'), UN, G0, STAIRWALL,
                           "The alcoves' head (0) along the east wall: the Mirage stair through it.")]
        + [plat('platform:alcove_orange', [-4480, 1728], [256, 96], 96, dict(WOOD), dict(WOOD),
                "The south alcove's shelf: the Orange Potion."),
           plat('platform:alcove_purple', [-4480, 2880], [256, 96], 96, dict(WOOD), dict(WOOD),
                "The north alcove's shelf: the Purple Potion.")],
        'flights': [{'from': [-4800, 2496], 'to': [-4096, 2496], 'to_height': G0, 'width': STAIR_W, 'steps': 16,
                     'open_below': 32, 'notes': "Sixteen steps of 32 down west from the head."}],
        'notes': "The potion alcoves at the foot of the Mirage Guild's cellar stair: from the head (0) sixteen steps down west; two alcoves' shelves (the Orange and the Purple Potions); the wizards' quarters east under the head.",
    },
    'quarters_stair': {
        'platforms': [head('platform:qstair_head', strip(QS_BOX, 's'), UN, G0, STAIRWALL,
                           "The quarters stair's head (0) along its south wall: the Guild Common through it.",
                           top_surface=MARBLE2)],
        'flights': [{'from': [192, 4672], 'to': [192, 3968], 'to_height': G0, 'width': STAIR_W, 'steps': 16,
                     'open_below': 32, 'notes': "Sixteen steps of 32 down north from the head."}],
        'notes': "Down from the Common to the guild quarters: the head (0), sixteen steps down north, the foot (-512, the graph's stair_foot) under the head opening onto the undercroft.",
    },
    'back_stair': {
        'platforms': [head('platform:back_head', strip(BS_BOX, 's'), UN, G0, STAIRWALL,
                           "The back stair's head (0) along its south wall: the robing room through it.")],
        'flights': [{'from': [4544, 2752], 'to': [4544, 2048], 'to_height': G0, 'width': STAIR_W, 'steps': 16,
                     'open_below': 32, 'notes': "Sixteen steps of 32 down north from the head."}],
        'notes': "The Sorceress HQ's back stair from the robing room down to the alembic cellar.",
    },
    'undercroft': {
        'pillars': [{'outline': [[x - 96, y - 96], [x + 96, y - 96], [x + 96, y + 96], [x - 96, y + 96]],
                     'surface': dict(CELLWALL)} for x, y in UNDERCROFT_PILLARS],
        'notes': "A vaulted passage under the court and the Common, two rows of pillars: the wizards' quarters west, the sorceresses' east, the stair foot north, the vault's iron door south.",
    },
}

# Furniture
FONT_AT = (-512, 2816)
BLASTEM_TABLE = (512, 3072)
BLASTEM_CHAIR = (512, 2880)
XENOC_CHAIR = (-1984, 448)
MORGANA_DAIS = (3328, 3264)

FURNISH = {
    'court': {'walls': [
        {'wall': 's', 'panels': [
            panel('panel:niche_w', 256, 0, 512, dict(HCBUST, fit=True), "A statue niche: a wizard's bust.",
                  offset=wall_offset('court', 's', -512, 256)),
            panel('panel:niche_e', 256, 0, 512, dict(HCSTATUE, fit=True), "A statue niche: a robed sorceress.",
                  offset=wall_offset('court', 's', 512, 256))]},
        {'wall': 'w', 'panels': [
            panel(None, 256, 640, 512, dict(HCWIN, fit=True), "A window of the Hall of Mirages over the court.",
                  offset=wall_offset('court', 'w', 384, 256)),
            panel(None, 256, 640, 512, dict(HCWIN, fit=True), "A window of the Hall of Mirages over the court.",
                  offset=wall_offset('court', 'w', 1152, 256))]},
        {'wall': 'e', 'panels': [
            panel(None, 256, 640, 512, dict(HCWIN, fit=True), "A window of the scrying room over the court.",
                  offset=wall_offset('court', 'e', 384, 256)),
            panel(None, 256, 640, 512, dict(HCWIN, fit=True), "A window of the scrying room over the court.",
                  offset=wall_offset('court', 'e', 1152, 256))]},
    ]},
    'common': {
        'platforms': [plat('platform:font', list(FONT_AT), [384, 384], 96, dict(TRIM, scale=2), dict(SHIMMER),
                           "The font of spell points: a marble basin of shimmering water."),
                      plat(None, [-832, 2816], [128, 768], 80, dict(WOOD), dict(WOOD), "A long table by the west wall."),
                      plat('platform:hearth', [-768, 3392], [384, 128], 48, dict(FLAGS), dict(FLAGS),
                           "The hearth on the north wall."),
                      plat('platform:blastem_table', list(BLASTEM_TABLE), [384, 192], 80, dict(WOOD), dict(WOOD),
                           "Blastem's own table, apart from the others.")]
        + chair('platform:blastem_chair', list(BLASTEM_CHAIR), 'n', "Blastem the Wizard's chair."),
    },
    'weights': {'platforms': [
        plat('platform:scales', [1600, 2816], [384, 128], 96, dict(WOOD), dict(IRON, fit=True),
             "The quarter's scales and ledgers on the north wall's bench.")]},
    'illusions': {
        'platforms': [plat(None, [-3456, y], [128, 384], 48, dict(WOOD), dict(WOOD), "A bench by the west wall.")
                      for y in (512, 1024)]
        + [plat('platform:lectern', [-2624, 480], [96, 128], 112, dict(WOOD), dict(WOOD), "The lectern.")],
        'walls': [{'wall': 'n', 'panels': [panel('panel:painted_door', 192, 0, 384, dict(ICEDOOR, fit=True),
                                                 "A painted door: only a picture on the brick.",
                                                 offset=wall_offset('illusions', 'n', -2752, 192))]}],
    },
    'mirror_gallery': {'walls': [{'wall': 'w', 'panels': framed(
        'mirror_gallery', 'panel:mirror', 'w', 896, 96, 160, 384, dict(MIRROR),
        "The tall mirror, facing the blank wall that is not there.")}]},
    'mirage_hall': {
        'platforms': [plat('platform:xenoc_dais', [-1984, 448], [512, 384], 32, dict(ICEWALL, fit=False),
                           dict(ICEFLOOR), "The dais under the triple window.")]
        + chair('platform:xenoc_chair', list(XENOC_CHAIR), 'n', "Xenoc's raised chair.", base=32),
        'walls': [{'wall': 's', 'panels': [panel('panel:triple_window', 256, 160, 384, dict(HCTRI, fit=True),
                                                 "The triple window over Xenoc's chair.",
                                                 offset=wall_offset('mirage_hall', 's', -1984, 256))]}],
    },
    'xenoc_study': {'platforms': [plat('platform:xenoc_desk', [-1856, -448], [384, 160], 80, dict(WOOD), dict(WOOD),
                                       "Xenoc's desk.")]},
    'scrying': {
        'platforms': [plat('platform:crystal', [1728, 1536], [64, 64], 112, dict(WOOD), dict(MIRROR, fit=True),
                           "The scrying crystal on its stand."),
                      plat('platform:lamp_scry', [1728, 704], [128, 128], 48, dict(IRON), dict(IRON, fit=True),
                           "Ward lamp 1: a floor brazier with a cold violet flame.")],
        'walls': [{'wall': 'e', 'panels': [panel(None, 96, 256, 96, dict(SKULL, fit=True), "A skull niche.",
                                                 offset=wall_offset('scrying', 'e', y, 96)) for y in (640, 1024, 1664)]}],
    },
    'robing': {
        'platforms': [plat(None, [4736, y], [96, 384], 160, dict(WOOD), dict(WOOD), "A robe rack by the east wall.")
                      for y in (512, 1024)],
        'walls': [{'wall': 'n', 'panels': [panel('panel:lamp_robe', 96, 192, 96, dict(IRON, fit=True),
                                                 "Ward lamp 2: an iron bracket with a cold violet flame.",
                                                 offset=wall_offset('robing', 'n', 4544, 96))]}],
    },
    'morgana_sanctum': {'platforms': [plat('platform:morgana_dais', list(MORGANA_DAIS), [768, 256], 32, dict(DARKWALL, fit=False),
                                           dict(FLAGS), "Morgana's dais at the sanctum's north end.")]},
    'wardrobe': {'platforms': [plat(None, [5024, y], [96, 256], 160, dict(WOOD), dict(WOOD), "A robe rack.")
                               for y in (1920, 2304)]},
    'quarters_w': {'platforms': [plat(f'platform:bed_w{i}', [x, 2688], [192, 128], 48, dict(WOOD), dict(WOOD), "A bed.")
                                 for i, x in enumerate((-3328, -2944, -2560, -2176, -1792), 1)]},
    'quarters_e': {'platforms': [plat(f'platform:bed_e{i}', [x, 2816], [192, 128], 48, dict(WOOD), dict(WOOD), "A bed.")
                                 for i, x in enumerate((1152, 1536, 1920), 1)]},
    'alembic': {
        'platforms': [plat('platform:still', [3456, 2432], [256, 256], 160, dict(WOOD), dict(IRON, scale=2),
                           "The still against the east wall."),
                      plat(None, [2944, 2880], [512, 96], 128, dict(WOOD), dict(WOOD), "A shelf of empty bottles.")],
        'walls': [{'wall': 's', 'panels': [panel(None, 256, 0, 256, dict(BONES, fit=True), "An old niche of bones.",
                                                 offset=wall_offset('alembic', 's', 2816, 256))]}],
    },
}


# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s29 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-19: "a walled precinct of one pink brick;
# two rival guilds don't read") and 2.3 "Walls have structure":
# - the court: a grey base course (cstr128) under the ashlar, a pink marble cornice (t1trimb) at 992-1024 and the
#   crenellated coping (hcw1ctr) on the wall's top storey under the sky, where hcwall alone ran floor to sky; the
#   bridge's windows over the court are pointed arches in an ashlar reveal (were flat red slabs);
# - the Mirage Guild's hall: bookcase walls north and south (6d19's bookcas1, floor to ceiling), a magic circle in the
#   floor (td1) and on it the guild's crystal on a marble stand (crystl0, dress.py);
# - the Sorceress HQ's hall: two lit braziers in violet light (brzier00, dress.py) either side of skull shelves on the
#   north wall (two planks of skulls, 7dec20), skull reliefs (d2skulas) on the south wall, purple-flame torches;
# - the red-slab furniture: tables, desks, the lectern and the scales' bench take 6d19's brass-edged deskside sides.
COURSE = S_('cstr128', 128, 32, scale=3)       # a course of large grey blocks: the base course (96)
CRENEL = S_('hcw1ctr', 128, 256, scale=2)      # the ashlar under its crenellated coping: the court's top storey
for _t in THEMES:
    if _t['id'] == 'theme:court':
        _t['wall'] = CRENEL
        _t['bands'] = [{'height': 96, 'surface': dict(COURSE)}, {'height': 992, 'surface': dict(HCWALL)},
                       {'height': 1024, 'surface': dict(TRIM, scale=1)}]
        _t['notes'] = ("The guild court, open to the sky: a grey base course (cstr128), the town kit's pink ashlar "
                       "(hcwall), a pink marble cornice (t1trimb) and the crenellated top storey (hcw1ctr) under the "
                       "sky; pale marble flags (t1f1).")
# The bridge (over the arcade) under dark beams: through its windows the court sees beams, not red cedar boards.
THEMES.append({'id': 'theme:bridge_up', 'wall': HCWALL, 'floor': MARBLE, 'ceiling': BEAMS, 'door': HCDOOR,
               'reveal': dict(HCWALL), 'notes': "The covered bridge: pink ashlar, marble flags, dark beams (d2ceil1)."})
R['bridge'] = R['bridge'][:4] + ('theme:bridge_up',)
for _o in OPENINGS:
    if _o['id'].startswith('open:bridge_win_'):
        _o.update({'height': 160, 'shape': 'arch', 'apex': 256, 'reveal': dict(HCWALL)})
BOOKS = S_('bookcas1', 256, 256, scale=2)       # one case 512 high, the guild hall's height
CIRCLE = S_('td1', 512, 512, fit=True)
CIRCLE_AT = (-1728, 1344)
CRYSTAL_TOP = 2 + 96                            # the crystal stand's top (dress.py stands the crystal on it)
SKULL_SHELVES = [(1728, 1944, 192), (1728, 1944, 320)]   # (x, y, base): two planks on the HQ hall's north wall
HQ_BRAZIERS = [(1344, 1920), (2112, 1920)]
DESKSIDE = S_('deskside', 64, 64)


def desk_side(rise):
    return dict(DESKSIDE, scale=round(rise / 64.0, 4))


FURNISH.setdefault('mirage_foyer', {})
FURNISH['mirage_foyer']['walls'] = [
    {'wall': w, 'surface': dict(BOOKS), 'bands': False, 'notes': "A bookcase wall of the Mirage Guild."}
    for w in ('s', 'n')]
FURNISH['mirage_foyer']['platforms'] = [
    plat('platform:magic_circle', list(CIRCLE_AT), [640, 640], 2, dict(TRIM), dict(CIRCLE),
         "A magic circle set into the floor."),
    plat('platform:crystal_stand', list(CIRCLE_AT), [96, 96], 96, dict(TRIM, scale=2), dict(TRIM, scale=2),
         "The guild's crystal on its marble stand, in the middle of the circle.", base=2)]
FURNISH['hq_foyer'] = {
    'platforms': [plat(None, [x, y], [512, 208], 16, dict(STAIRWALL), dict(FLAGS), "A stone ledge of skulls.",
                       base=b)
                  for x, y, b in SKULL_SHELVES],
    'walls': [{'wall': 's', 'panels': [panel(None, 96, 256, 96, dict(SKULL, fit=True), "A skull relief.",
                                             offset=wall_offset('hq_foyer', 's', x, 96)) for x in (1472, 1984)]}]}
_DESKS = {'platform:blastem_table', 'platform:xenoc_desk', 'platform:lectern', 'platform:scales'}
for _rid, _f in FURNISH.items():
    for _p in _f.get('platforms', []):
        if _p.get('id') in _DESKS or _p.get('notes') == "A long table by the west wall.":
            _p['surface'] = desk_side(_p['rise'])
        if _p.get('id') == 'platform:scales':      # its iron top tiled, not one picture stretched 3:1
            _p['top_surface'] = dict(IRON)


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
