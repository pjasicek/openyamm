#!/usr/bin/env python3
"""DD-21 Necropolis Sewer: the geometry (rooms, openings) shared by L2, L3 and L4.

One BLV of three floors in one frame (x east, y north, z up; z 0 the stair foot under D6's Necropolis):
- the crypts (0): the crypt stair (the arrival at its foot, the grille pair at its top, 448 up), the Hall of Biers,
  Sandro's crypt (posts, the dais and his bier) and his reliquary behind a grille;
- the sewer (-512): the stair landing (two storeys: its head at 0 opens off the Hall of Biers' west wall), the main
  channel's west and east arms, the mummy's vault, the sluice room, the west and east culverts (L-shaped: south, then
  in towards the middle) and the outfall where both pour into a round basin;
- the lowest culvert (-896): the heart culvert under the outfall (two storeys: the steps down from the sluice gate),
  the black cistern and the jar's ledge.
Rooms are rectangles or L-shaped outlines; walls between rooms are 128 thick. The sewer and culvert rooms lie under
the crypts in plan, their ceilings at most -64.
"""

CRYPT, SEWER, LOW = 0, -512, -896
WALL = 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Tomb of Ethric the Mad (6d14): Sandro's crypts
CRYPTWALL = S_('d2wlbctr', 128, 256)     # dark block stone
POST = S_('d2wlbpos', 128, 256)          # block stone with a carved post (reveals)
CRYPTFLOOR = S_('d2flor4', 128, 128)     # purple-grey flagstones
CRYPTCEIL = S_('d2ceil3', 256, 256)      # dark rough vault
NICHE1 = S_('d2niche1', 256, 256)        # a burial niche with a skeleton
NICHE4 = S_('d2niche4', 256, 256)        # a walled-up niche
CRYPTDOOR = S_('d2lgdor', 256, 256)      # the crypt's iron-bound plank doors (6d14's own, 256 square)
VAULTDOOR = S_('crsmdr1', 128, 256)      # the vault's iron door (6d14's)
SEAL = S_('xdsandro', 128, 128)          # Sandro's seal (new, A8 phase 5)
# MM6 Free Haven Sewer (sewer.blv): the sewer
WETWALL = S_('d1wldle2', 256, 256)       # sewer stone with a wet green tide line: the channels
WETWALL2 = S_('d1wldle3', 256, 256)      # sewer stone, damp: the culverts, the outfall
OLDWALL = S_('d1wle', 256, 256)          # sewer stone, dry: the rooms off the channel
MOSSWALL = S_('d1medbw', 128, 128)       # the old tomb wall, mossy blocks: the mummy's vault, the cistern
WALK = S_('d7flor4', 128, 128)           # the walkways' tiles
SEWERCEIL = S_('d1ceil1', 256, 256)      # the sewer's plank vault
GRATE = S_('d1lggrt', 256, 256)          # a round drain grate in a stone frame (the drains)
BEAM = S_('d1mbea', 64, 64)              # big stone blocks: kerbs, the stair's rails, the ledge
LADDERTEX = S_('d1ladder', 128, 256)
IRONDOOR = S_('d8dora', 256, 256)        # the sewer's iron doors (sewer.blv's D8dorA)
GRILLE = S_('xwcage', 128, 256)          # iron bars (Xeen's cage bars, D-22.1): the reliquary grille, the sluice gate
SEWAGE = {'texture': 'swprrf3', 'liquid': 'water'}   # MM6 sewage (the engine's sewage liquid), as DD-01
# D6's crypt door seen from inside: the plank wings (MM8 gkp103a/gkp103b)
WING_L = S_('gkp103a', 128, 256)
WING_R = S_('gkp103b', 128, 256)

THEMES = [
    {'id': 'theme:crypt', 'wall': CRYPTWALL, 'floor': CRYPTFLOOR, 'ceiling': CRYPTCEIL, 'door': CRYPTDOOR,
     'reveal': POST,
     'notes': "Sandro's crypts in MM6 Tomb of Ethric the Mad (6d14): dark block stone (d2wlbctr), purple-grey flags (d2flor4), a rough dark vault (d2ceil3), carved posts in the doorways (d2wlbpos)."},
    {'id': 'theme:channel', 'wall': WETWALL, 'floor': WALK, 'ceiling': SEWERCEIL, 'door': IRONDOOR, 'reveal': OLDWALL,
     'notes': "The sewer's main channel and its landing (MM6 Free Haven Sewer): stone with a wet green tide line (d1wldle2), tiled walkways (d7flor4), the plank vault (d1ceil1)."},
    {'id': 'theme:culvert', 'wall': WETWALL2, 'floor': WALK, 'ceiling': SEWERCEIL, 'door': IRONDOOR, 'reveal': OLDWALL,
     'notes': "The culverts and the outfall: damp sewer stone (d1wldle3)."},
    {'id': 'theme:room', 'wall': OLDWALL, 'floor': WALK, 'ceiling': SEWERCEIL, 'door': IRONDOOR, 'reveal': OLDWALL,
     'notes': "The rooms off the channel (the sluice room, the dead-food cellar): dry sewer stone (d1wle)."},
    {'id': 'theme:tomb', 'wall': MOSSWALL, 'floor': CRYPTFLOOR, 'ceiling': CRYPTCEIL, 'door': VAULTDOOR, 'reveal': POST,
     'notes': "The old tomb the channel cut into (the mummy's vault): mossy blocks (d1medbw) over the crypts' flags and vault."},
    {'id': 'theme:cistern', 'wall': MOSSWALL, 'floor': WALK, 'ceiling': SEWERCEIL, 'door': GRILLE, 'reveal': OLDWALL,
     'notes': "The heart culvert: mossy blocks (d1medbw) round the black cistern."},
]

# Rooms: id: (name, outline, floor, ceiling, theme)


def box(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


R = {
    # the crypts (0)
    'stair_foot': ("Crypt stair", box(-320, -128, 320, 1216), CRYPT, 896, 'theme:crypt'),
    'crypt_hall': ("Hall of Biers", box(-512, -2048, 512, -256), CRYPT, 640, 'theme:crypt'),
    'sandro_crypt': ("Sandro's crypt", box(-768, -3456, 768, -2176), CRYPT, 640, 'theme:crypt'),
    'reliquary': ("Sandro's reliquary", box(896, -3136, 1408, -2496), CRYPT, 448, 'theme:crypt'),
    # the sewer (-512)
    'landing': ("Stair landing", box(-1664, -1920, -640, -896), SEWER, 512, 'theme:channel'),
    'main_west': ("Main channel (west)", box(-3584, -1664, -1792, -1152), SEWER, -64, 'theme:channel'),
    'main_east': ("Main channel (east)", box(-512, -1664, 1280, -1152), SEWER, -64, 'theme:channel'),
    'mummy_vault': ("Mummy's vault", box(-4352, -1792, -3712, -1024), SEWER, -128, 'theme:tomb'),
    'dead_food': ("Dead-food cellar", box(1408, -1792, 2176, -1024), SEWER, -128, 'theme:room'),
    'sluice': ("Sluice room", box(-2560, -2560, -1920, -1920), SEWER, -128, 'theme:room'),
    'west_culvert': ("West culvert", [[-3200, -3200], [-1856, -3200], [-1856, -2688], [-2688, -2688], [-2688, -1792],
                                      [-3200, -1792]], SEWER, -128, 'theme:culvert'),
    'east_culvert': ("East culvert", [[-384, -3200], [640, -3200], [640, -1792], [128, -1792], [128, -2304],
                                      [-128, -2304], [-128, -2560], [128, -2560], [128, -2688], [-384, -2688]],
                     SEWER, -128, 'theme:culvert'),
    'outfall': ("Outfall", box(-1728, -3456, -512, -2432), SEWER, -64, 'theme:culvert'),
    # the lowest culvert (-896)
    'heart_culvert': ("Heart culvert", box(-1856, -4864, -384, -3584), LOW, -64, 'theme:cistern'),
}
FLOOR_NAME = {CRYPT: 'crypts', SEWER: 'sewer', LOW: 'culvert'}
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


def opening(oid, a, b, at=None, width=256, height=384, link=None, walls=None, **kw):
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b, walls)
    if at is None:
        at = (lo + hi) / 2
    if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
        raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
    forward = (p1[ax] - p0[ax]) > 0
    along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b}
    if (len(outline(a)) == 4 and len(outline(b)) == 4) or walls:
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


DOUBLE_W, DOUBLE_H = 512, 256      # the crypt's doors: two leaves of d2lgdor, each 256 square (6d14's own)
PASS_W = 384

OPENINGS = [
    # the crypts
    opening('open:foot_hall', 'stair_foot', 'crypt_hall', at=0, width=PASS_W, height=384, link='link:foot_hall'),
    opening('open:hall_crypt', 'crypt_hall', 'sandro_crypt', at=0, width=DOUBLE_W, height=DOUBLE_H,
            link='link:hall_crypt', notes="The crypt's double doors under Sandro's seal."),
    opening('open:crypt_reliquary', 'sandro_crypt', 'reliquary', at=-2816, width=192, height=384,
            link='link:crypt_reliquary', notes="The reliquary's iron grille in the crypt's east wall."),
    # down to the sewer: the railed stair's head (0) off the hall's west wall
    opening('open:hall_landing', 'crypt_hall', 'landing', at=-1408, width=320, height=320, link='link:hall_landing',
            notes="The railed stair's head: from the Hall of Biers onto the landing's head (0), the stair down west."),
    # the sewer ring and its dead ends
    opening('open:landing_west', 'landing', 'main_west', at=-1440, width=320, height=320, link='link:landing_west'),
    opening('open:landing_east', 'landing', 'main_east', at=-1408, width=PASS_W, height=320, link='link:landing_east'),
    opening('open:west_vault', 'main_west', 'mummy_vault', at=-1408, width=160, height=320, link='link:west_vault',
            notes="The old tomb wall's stone door: Mummy's Secret Treasure (aaze0036:10)."),
    opening('open:east_cellar', 'main_east', 'dead_food', at=-1408, width=256, height=256, link='link:east_cellar'),
    opening('open:west_culvert', 'main_west', 'west_culvert', at=-2944, width=PASS_W, height=320,
            link='link:west_culvert'),
    opening('open:culvert_sluice', 'west_culvert', 'sluice', at=-2240, width=256, height=256, walls=(3, 3),
            link='link:culvert_sluice'),
    opening('open:wculvert_outfall', 'west_culvert', 'outfall', at=-2848, width=256, height=320,
            link='link:wculvert_outfall'),
    opening('open:outfall_eculvert', 'outfall', 'east_culvert', at=-2848, width=256, height=320, walls=(1, 9),
            link='link:outfall_eculvert'),
    opening('open:eculvert_east', 'east_culvert', 'main_east', at=384, width=PASS_W, height=320,
            link='link:eculvert_east'),
    # down to the lowest culvert: the sluice gate onto the steps' head (-512)
    opening('open:outfall_heart', 'outfall', 'heart_culvert', at=-704, width=192, height=384,
            link='link:outfall_heart', notes="The sluice gate in the outfall's south wall, over the steps down."),
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


CHANNEL_W = 160


def north_channel(rid, inset=128):
    """The main channel's sewage along an arm's north wall (64 from it, 128 wide): the south walk stays dry for the
    doorways and the culverts' mouths in the south wall."""
    x0, y0, x1, y1 = bounds(rid)
    return {'id': f'level:{rid}_channel', 'outline': box(x0 + inset, y1 - 64 - 128, x1 - inset, y1 - 64),
            'floor': R[rid][2] - 48, 'edge': dict(BEAM), 'surface': dict(SEWAGE),
            'notes': "Sewage, ankle deep, along the north wall; the walkway south of it."}


def channel(rid, axis, inset=192, cid=None, span=None):
    """A sewage channel down the middle of a straight run: a sunken level 48 down, inset from the ends."""
    x0, y0, x1, y1 = span or bounds(rid)
    if axis == 'x':
        cy = (y0 + y1) // 2
        o = box(x0 + inset, cy - CHANNEL_W // 2, x1 - inset, cy + CHANNEL_W // 2)
    else:
        cx = (x0 + x1) // 2
        o = box(cx - CHANNEL_W // 2, y0 + inset, cx + CHANNEL_W // 2, y1 - inset)
    return {'id': cid or f'level:{rid}_channel', 'outline': o, 'floor': R[rid][2] - 48, 'edge': dict(BEAM),
            'surface': dict(SEWAGE), 'notes': "Sewage, ankle deep, down the middle between the walkways."}


# The stair foot: the arrival at (0, 0), the stair north up to the head (448) before the grille pair.
STAIR_TOP = 448
FOOT_BOX = (-320, -128, 320, 1216)
HEAD_D = 320
# The landing: two storeys; its head (0) along the east wall off the hall, the railed stair down west along the north.
LANDING_BOX = (-1664, -1920, -640, -896)
LANDING_HEAD_D = 384
# The heart culvert: two storeys; the steps' head (-512) along the north wall behind the sluice gate.
HEART_BOX = (-1856, -4864, -384, -3584)
HEART_HEAD_D = 384
POOL = box(-1664, -4672, -1152, -4288)
POOL_DEPTH = 96
JAR_LEDGE = ([-832, -4704], [256, 256], 96)      # at, size, rise: by the pool's east edge against the south wall
# Sandro's crypt
DAIS = ([0, -3200], [896, 384], 32)
BIER = ([0, -3264], [448, 128], 64)
POSTS = [(-384, -2496), (384, -2496), (-384, -2880), (384, -2880)]
# The Hall of Biers: biers against the long walls between the niches.
STATUETTE_PLINTH = ([1280, -2816], [128, 192], 64)
HALL_BIERS = [(-416, -896), (416, -832), (416, -1472)]   # centre; 192 x 384, along y, between the niches

EXTRA = {
    'stair_foot': {
        'platforms': [head('platform:stair_head', strip(FOOT_BOX, 'n', HEAD_D), CRYPT, STAIR_TOP, CRYPTWALL,
                           CRYPTFLOOR, "The stair's head (448) before the grille pair: D6's crypt door above.")],
        'flights': [{'from': [0, 256], 'to': [0, 896], 'to_height': STAIR_TOP, 'width': 320, 'steps': 14,
                     'open_below': 32,
                     'notes': "Fourteen steps of 32 up north from the foot to the head before the grille pair."}],
        'notes': "The foot of the crypt stair under D6's Necropolis (the arrival); the stair climbs north to the grille pair (the way out); the Hall of Biers south.",
    },
    'crypt_hall': {
        'platforms': [plat(None, [x, y], [192, 384], 64, dict(CRYPTWALL), dict(CRYPTFLOOR), "A stone bier against the wall.",
                           end_surface=dict(CRYPTWALL, fit=False)) for x, y in HALL_BIERS],
        'walls': [
            {'wall': 'e', 'panels': [
                {'offset': 128, 'length': 256, 'bottom': 0, 'height': 256, 'surface': dict(NICHE1, fit=True)},
                {'offset': 768, 'length': 256, 'bottom': 0, 'height': 256, 'surface': dict(NICHE4, fit=True)},
                {'offset': 1408, 'length': 256, 'bottom': 0, 'height': 256, 'surface': dict(NICHE1, fit=True)}]},
            {'wall': 'w', 'panels': [
                {'offset': 128, 'length': 256, 'bottom': 0, 'height': 256, 'surface': dict(NICHE4, fit=True)},
                {'offset': 1408, 'length': 256, 'bottom': 0, 'height': 256, 'surface': dict(NICHE1, fit=True)}]},
            {'wall': 's', 'panels': [
                {'id': 'panel:seal', 'at': 'centre', 'length': 128, 'bottom': 352, 'height': 128,
                 'surface': dict(SEAL, fit=True), 'notes': "Sandro's seal (xdsandro), once, over the crypt's doors."}]},
        ],
        'notes': "A long vault of burial niches (d2niche) with stone biers against both walls; Sandro's seal over the double doors at the south end; the railed stair's head in the west wall.",
    },
    'sandro_crypt': {
        'pillars': [{'at': [x, y], 'size': [128, 128], 'surface': dict(POST)} for x, y in POSTS],
        'platforms': [
            plat('platform:dais', DAIS[0], DAIS[1], DAIS[2], dict(CRYPTWALL), dict(CRYPTFLOOR),
                 "The dais at the crypt's south end; stepping onto it, Sandro speaks."),
            plat('platform:bier', BIER[0], BIER[1], BIER[2], dict(CRYPTWALL), dict(CRYPTFLOOR),
                 "Sandro's bier on the dais.", base=DAIS[2], end_surface=dict(CRYPTWALL, fit=False)),
        ],
        'notes': "A square vault on four dark posts; the dais and Sandro's bier at the south end; the reliquary's grille in the east wall.",
    },
    'reliquary': {
        'platforms': [plat('platform:plinth', STATUETTE_PLINTH[0], STATUETTE_PLINTH[1], STATUETTE_PLINTH[2],
                           dict(CRYPTWALL), dict(CRYPTFLOOR), "The statuette's plinth.",
                           end_surface=dict(CRYPTWALL, fit=False))],
        'notes': "The alcove behind the grille: Sandro's chest and his statuette on its plinth.",
    },
    'landing': {
        'platforms': [head('platform:landing_head', strip(LANDING_BOX, 'e', LANDING_HEAD_D), SEWER, CRYPT, OLDWALL,
                           WALK, "The railed stair's head (0) along the landing's east wall, off the Hall of Biers.")],
        'flights': [{'from': [-1600, -1088], 'to': [-1024, -1088], 'to_height': CRYPT, 'width': 320, 'steps': 16,
                     'open_below': 32, 'sides': {'height': 48, 'thickness': 16, 'surface': dict(BEAM)},
                     'notes': "Sixteen steps of 32 with stone rails, up east along the north wall to the head."}],
        'notes': "The railed stair's foot on a stone platform where the main channel's two arms meet; the head overhead east, the stair along the north wall.",
    },
    'main_west': {
        'levels': [north_channel('main_west')],
        'notes': "The long channel's west arm: sewage down the middle, walkways both sides, drains in the walls; the old tomb wall at its west end, the west culvert south.",
    },
    'main_east': {
        'levels': [north_channel('main_east')],
        'notes': "The channel's east arm, drains in the walls; signed barrels by the north wall; the cellar's door at its east end, the east culvert south.",
    },
    'west_culvert': {
        'levels': [{'id': 'level:west_culvert_channel',
                    'outline': [[-3136, -3136], [-1920, -3136], [-1920, -3008], [-3008, -3008], [-3008, -1952],
                                [-3136, -1952]],
                    'floor': SEWER - 48, 'edge': dict(BEAM), 'surface': dict(SEWAGE),
                    'notes': "Sewage down the culvert, south and then east towards the outfall."}],
        'notes': "A culvert from the main channel south, then east to the outfall, its sewage along the outer wall; the sluice room's door in its inner (east) wall.",
    },
    'east_culvert': {
        'levels': [{'id': 'level:east_culvert_channel',
                    'outline': [[-320, -3136], [576, -3136], [576, -1952], [448, -1952], [448, -3008],
                                [-320, -3008]],
                    'floor': SEWER - 48, 'edge': dict(BEAM), 'surface': dict(SEWAGE),
                    'notes': "Sewage down the culvert from the main channel, south and then west towards the outfall."}],
        'notes': "The east twin of the west culvert, from the outfall east and up to the main channel; a side niche in its inner (west) wall holds the source's trapped Box.",
    },
    'outfall': {
        'levels': [{'id': 'level:basin', 'outline': [[-1344, -3200], [-896, -3200], [-768, -3072], [-768, -2816],
                                                     [-896, -2688], [-1344, -2688], [-1472, -2816], [-1472, -3072]],
                    'floor': SEWER - 96, 'edge': dict(BEAM), 'surface': dict(SEWAGE),
                    'notes': "The round basin both culverts pour into."}],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:alcove', 'at': 'centre', 'length': 192, 'bottom': 32,
                                             'height': 192, 'surface': dict(GRATE, fit=True),
                                             'notes': "The source's alcove (aaze0036:0): a grated outlet, nothing in it."}]}],
        'notes': "Both culverts pour into a round basin; the sluice gate in the south wall over the steps down.",
    },
    'heart_culvert': {
        'platforms': [head('platform:heart_head', strip(HEART_BOX, 'n', HEART_HEAD_D), LOW, SEWER, MOSSWALL, WALK,
                           "The steps' head (-512) behind the sluice gate."),
                      plat('platform:jar_ledge', JAR_LEDGE[0], JAR_LEDGE[1], JAR_LEDGE[2], dict(MOSSWALL),
                           dict(BEAM, scale=2), "The ledge over the cistern where the jar of green glass stands.")],
        'flights': [{'from': [-704, -4416], 'to': [-704, -3968], 'to_height': SEWER, 'width': 320, 'steps': 12,
                     'open_below': 32, 'sides': {'height': 48, 'thickness': 16, 'surface': dict(BEAM)},
                     'notes': "Twelve steps of 32 down south from the gate's head to the culvert's floor."}],
        'levels': [{'id': 'level:cistern', 'outline': POOL, 'floor': LOW - POOL_DEPTH, 'bank': 128,
                    'surface': dict(SEWAGE), 'notes': "The black cistern the sewer falls into."}],
        'notes': "The sewer's lowest culvert falling into a black cistern; the jar of green glass on its ledge.",
    },
}


def drain(pid, offset, notes):
    return {'id': pid, 'offset': offset, 'length': 160, 'bottom': 16, 'height': 160, 'surface': dict(GRATE, fit=True),
            'notes': notes}


DRAIN_WALLS = {
    'main_west': [{'wall': 's', 'panels': [drain('panel:drain_1', 1280, "A sewer drain (a find)."),
                                           drain('panel:drain_2', 128, "A sewer drain.")]}],
    'main_east': [{'wall': 's', 'panels': [drain('panel:drain_3', 256, "A sewer drain (a find)."),
                                           drain('panel:drain_4', 1536, "A sewer drain.")]}],
    'west_culvert': [{'wall': 3, 'panels': [drain('panel:drain_5', 128, "A sewer drain (a find).")]},
                     {'wall': 2, 'panels': [drain('panel:drain_6', 384, "A sewer drain.")]}],
}
for _rid, _walls in DRAIN_WALLS.items():
    EXTRA[_rid]['walls'] = EXTRA[_rid].get('walls', []) + _walls


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
