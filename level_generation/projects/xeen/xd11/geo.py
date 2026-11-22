#!/usr/bin/env python3
"""XD-11 Tower of High Magic: the geometry (rooms, openings) shared by L3 and L4.

A square tower 4,096 across inside (-2048..2048 on x and y), four floors 640 apart (0, 640, 1280, 1920; rooms 544
high, slabs 96) and a roof terrace at 2560 under the open sky. A lift core (768 by 640) stands in the same place on
every floor; three short lifts are stacked in it, alternating west and east halves (0-1 west, 1-2 east, 2-3 west).
The stairs alternate east (0-1), west (1-2), east (2-3) and are two-storey halls with a flight along the outer wall
and a gallery at the upper floor; the Stairway to Heaven climbs from the top floor's north-west to the roof.
Walls between rooms are 128 thick (the gap between their outlines).
"""

FL = [0, 640, 1280, 1920, 2560]
H = 544          # clear height of an ordinary room
ROOF = 2560
SKY = 3584


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# Celeste (MM7 7d25): pale plaster, grey rubble, pale planks, marble floors, dark beams, painted sky, carved doors.
PLASTER = S_('hwp1bwall', 128, 256)
PLASTERB = S_('hwp1b', 128, 256)
RUBBLE = S_('hwm2wall', 128, 256)
PLANKS = S_('hwr1wall', 128, 256)
MARBLE = S_('7tws1f', 128, 128)
MARBLE2 = S_('t2s1fl', 128, 128)
BEAMS = S_('hwm2rf', 128, 128)
PAINTSKY = S_('7plansky1', 256, 256)
TRIM = S_('7tws1fa', 128, 32)
FRIEZE = S_('t3s2b', 128, 256)
DOOR_BLUE = S_('hwm2d', 128, 256)
DOOR_SIGIL = S_('hwp1d', 128, 256)
PILLAR = S_('hwm2el', 128, 256)
WATER = {'texture': '7wtrtyl', 'liquid': 'water', 'flow': 'down'}
# Clanker's Laboratory (MM7 7d12, Bracada's other wizard house): books, desks, cabinets.
BOOKS = S_('7t1books', 128, 256)
DESK = S_('7t1books1', 128, 128)
CABS = S_('7t1cabs', 64, 128)
SHEET = S_('t2bedsht', 128, 256)
# Labs where Celeste has nothing: lava (Castle Gloaming's), the world's riveted iron and green brew (A6's xwiron,
# xwbrew), Icewind Keep's pale blue frost (MM6 6d15 orair32).
LAVA = {'texture': 'lava', 'size': [256, 256], 'liquid': 'lava', 'flow': 'left'}
IRON = S_('xwiron', 128, 128)
BREW = {'texture': 'xwbrew', 'size': [128, 128], 'liquid': 'liquid', 'flow': 'down'}
FROST = S_('orair32', 128, 128)
SOIL = S_('hhp2b2', 128, 128)
GRILLE = S_('xngrille', 128, 256)
SKYW = S_('xwsky', 512, 512, scale=2, sky=True)
# The steps of the Stairway to Heaven are made of cloud: X8's walkable cloud tops and cloud sides (A6's xccloud,
# xccloudsd, seamless tiles; session 7: xwcloudst, a picture of a whole stairway, was cut over every step).
CLOUD_TOP = S_('xccloud', 256, 256)
CLOUD_SIDE = S_('xccloudsd', 256, 256)

THEMES = [
    {'id': 'theme:ground', 'wall': RUBBLE, 'floor': MARBLE, 'ceiling': BEAMS, 'reveal': PLASTERB, 'door': DOOR_BLUE,
     'notes': "The ground floor and the stair halls: Celeste's grey rubble walls (hwm2wall), its veined marble floor (7tws1f) and dark beams overhead (hwm2rf), pale plaster in the doorways (hwp1b), its carved blue doors (hwm2d)."},
    {'id': 'theme:lab', 'wall': PLASTER, 'floor': MARBLE, 'ceiling': BEAMS, 'reveal': PLASTERB, 'door': DOOR_SIGIL,
     'bands': [{'height': 32, 'surface': TRIM}],
     'notes': "The laboratories and landings: Celeste's pale plaster (hwp1bwall) over a marble skirting (7tws1fa), marble floors, beams, the plaster frames of the doorways (hwp1b), the alchemist's door with its sigil (hwp1d)."},
    {'id': 'theme:study', 'wall': PLANKS, 'floor': MARBLE2, 'ceiling': BEAMS, 'reveal': PLASTERB, 'door': DOOR_SIGIL,
     'notes': "The quarters, the library and the Archmage's study: Celeste's pale planking (hwr1wall), its pale marble (t2s1fl), beams; Clanker's Laboratory's bookcases (7t1books)."},
    {'id': 'theme:observatory', 'wall': PLASTER, 'floor': MARBLE2, 'ceiling': PAINTSKY, 'reveal': PLASTERB,
     'door': DOOR_BLUE, 'bands': [{'height': 32, 'surface': TRIM}],
     'notes': "The observatory: plaster under Celeste's painted sky ceiling (7plansky1)."},
    {'id': 'theme:core', 'wall': RUBBLE, 'floor': MARBLE, 'ceiling': BEAMS, 'reveal': PLASTERB, 'door': GRILLE,
     'notes': "The lift core: rubble walls, the cages' gates of brass grille (A6's xngrille)."},
    {'id': 'theme:roof', 'wall': SKYW, 'floor': MARBLE, 'ceiling': SKYW, 'reveal': RUBBLE,
     'bands': [{'height': 128, 'surface': RUBBLE}],
     'notes': "The roof: marble under the open sky; a parapet of rubble (the band), sky above it."},
    {'id': 'theme:skystair', 'wall': SKYW, 'floor': MARBLE, 'ceiling': SKYW, 'reveal': RUBBLE,
     'bands': [{'height': 768, 'surface': RUBBLE}],
     'notes': "The Stairway to Heaven: rubble walls up to the roof's parapet, open to the sky above."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# id: (name, (x0, y0, x1, y1), floor, ceiling, theme, plan size, kind)
R = {
    # floor 0
    'door': ("Enchanted door", (-1792, -2048, -1024, -1280), 0, H, 'theme:ground'),
    'foyer': ("Foyer", (-2048, -1152, -128, 960), 0, H, 'theme:ground'),
    'athanor': ("Athanor", (-2048, 1088, 2048, 2048), 0, H, 'theme:lab'),
    'coils': ("Lightning coils", (0, -128, 1280, 960), 0, H, 'theme:lab'),
    'core0': ("Lift core, ground floor", (256, -896, 1024, -256), 0, H, 'theme:core'),
    'east_stair': ("East stair", (1408, -2048, 2048, 960), 0, FL[1] + H, 'theme:ground'),
    # floor 1
    'landing1': ("East landing", (256, -2048, 1280, -1024), 640, 640 + H, 'theme:lab'),
    'core1': ("Lift core, first floor", (256, -896, 1024, -256), 640, 640 + H, 'theme:core'),
    'still': ("Cold still", (-1280, -2048, 128, -640), 640, 640 + H, 'theme:lab'),
    'reagents': ("Reagent store", (-2048, -2048, -1408, -1152), 640, 640 + H, 'theme:lab'),
    'poison': ("Poison garden", (-1280, -512, 128, 1408), 640, 640 + H, 'theme:lab'),
    'west_stair': ("Frost-sealed stair", (-2048, -1024, -1408, 2048), 640, FL[2] + H, 'theme:ground'),
    # floor 2
    'landing2': ("West landing", (-1280, 1408, -256, 2048), 1280, 1280 + H, 'theme:lab'),
    'energy': ("Energy lab", (-1280, -128, 384, 1280), 1280, 1280 + H, 'theme:lab'),
    'magic': ("Magic lab", (512, 640, 2048, 2048), 1280, 1280 + H, 'theme:lab'),
    'quarters': ("Sorceresses' quarters", (512, -128, 2048, 512), 1280, 1280 + H, 'theme:study'),
    'core2': ("Lift core, second floor", (256, -896, 1024, -256), 1280, 1280 + H, 'theme:core'),
    'high_stair': ("Library stair", (1408, -2048, 2048, -256), 1280, FL[3] + H, 'theme:ground'),
    # floor 3
    'landing3': ("Top landing", (256, -2048, 1280, -1024), 1920, 1920 + H, 'theme:lab'),
    'core3': ("Lift core, top floor", (256, -896, 1024, -256), 1920, 1920 + H, 'theme:core'),
    'library': ("Library of High Magic", (-1152, -2048, 128, 1280), 1920, 1920 + H, 'theme:study'),
    'study': ("Archmage's study", (-2048, -2048, -1280, -640), 1920, 1920 + H, 'theme:study'),
    'observatory': ("Observatory", (-2048, -512, -1280, 1280), 1920, 1920 + H, 'theme:observatory'),
    'stairway': ("Stairway to Heaven", (-2048, 1408, 128, 2048), 1920, SKY - 256, 'theme:skystair'),
    # roof
    'roof': ("Roof", None, ROOF, SKY, 'theme:roof'),
}
ROOF_OUTLINE = [[-2048, -2048], [2048, -2048], [2048, 2048], [256, 2048], [256, 1280], [-2048, 1280]]

ORDER = sorted(R)

# Lifts in the core (x 256..1024, y -896..-256): west half and east half.
LIFT_W = [448, -576]
LIFT_E = [832, -576]
LIFT_SIZE = [256, 256]


# ---------------------------------------------------------------------------------------- D-89 identity (session 29)
# The tower is an octagon (DESIGN_GATING_AND_IDENTITY 2.2, XD-11; 2.3 "Towers are towers"): the square's four corners
# are cut at 45 degrees, 512 along each side (CH), on every floor and the roof, so every corner room has a slanted
# outer wall; the outer walls carry windows to the sky; the lift shaft's cores are octagons too (CORE_CH).
CH = 512
CORE_CH = 96
OCT = [(1, 1, CH - 4096), (-1, 1, CH - 4096), (-1, -1, CH - 4096), (1, -1, CH - 4096)]   # a*x + b*y >= c


def clip(poly, planes):
    """Sutherland-Hodgman: the polygon cut by half-planes a*x + b*y >= c (45-degree cuts of axis-aligned outlines
    meet them on whole units)."""
    for a, b, c in planes:
        out = []
        n = len(poly)
        for i in range(n):
            p, q = poly[i], poly[(i + 1) % n]
            fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
            if fp >= 0:
                out.append(p)
            if (fp >= 0) != (fq >= 0):
                t = fp / (fp - fq)
                out.append([round(p[0] + t * (q[0] - p[0])), round(p[1] + t * (q[1] - p[1]))])
        poly = [pt for i, pt in enumerate(out) if pt != out[i - 1]]
    return [list(map(int, pt)) for pt in poly]


def octo(poly):
    return clip(poly, OCT)


def core_planes():
    x0, y0, x1, y1 = R['core0'][1]
    k = CORE_CH
    return [(1, 1, x0 + y0 + k), (-1, 1, -x1 + y0 + k), (-1, -1, -x1 - y1 + k), (1, -1, x0 - y1 + k)]


def on_octagon(p, q):
    """True when the edge p-q lies on the tower's outer wall (a side of the square or a cut corner)."""
    for i in (0, 1):
        if p[i] == q[i] and abs(p[i]) == 2048:
            return True
    return any(a * p[0] + b * p[1] == c and a * q[0] + b * q[1] == c for a, b, c in OCT)


def outline(rid):
    b = R[rid][1]
    o = ROOF_OUTLINE if b is None else rect(*b)
    if rid.startswith('core'):
        o = clip(o, core_planes())
    return octo(o)


def edge_index(rid, p0):
    """The outline edge that starts at p0."""
    return [list(p) for p in outline(rid)].index(list(p0))


def walls_of(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def shared(a, b, walls=None):
    """The facing wall pair of rooms a and b: (wall index in a, wall index in b, start, end along a's wall)."""
    best = None
    for i, (p0, p1) in enumerate(walls_of(a)):
        for j, (q0, q1) in enumerate(walls_of(b)):
            if walls and (i, j) != walls:
                continue
            if p0[0] == p1[0] and q0[0] == q1[0]:          # both vertical
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
            if hi - lo <= 0 or gap > 512:
                continue
            # facing: a's wall outward normal points toward b
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            nx, ny = dy, -dx   # outward for a counter-clockwise outline
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


def opening(oid, a, b, at=None, width=256, height=320, link=None, walls=None, **kw):
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b, walls)
    if at is None:
        along = 0.5
    else:
        # along runs counter-clockwise along a's wall over the shared stretch
        forward = (p1[ax] - p0[ax]) > 0
        along = (at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo)
        along = round(along, 4)
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b, 'from_wall': i, 'to_wall': j}
    if link:
        d['link'] = link
    if along != 0.5:
        d['along'] = along
    d['width'] = width
    d['height'] = height
    d.update(kw)
    if d.get('shape') == 'arch':
        d['height'] = height - 64
        d['apex'] = height + 32
    return d


OPENINGS = [
    # floor 0
    opening('open:door_foyer', 'door', 'foyer', width=384, height=384, shape='arch', link='link:door_foyer'),
    opening('open:foyer_athanor', 'foyer', 'athanor', at=-1088, width=256, height=320, link='link:foyer_athanor'),
    opening('open:athanor_coils', 'coils', 'athanor', at=640, width=512, height=416, shape='arch',
            link='link:athanor_coils'),
    opening('open:coils_core0', 'coils', 'core0', at=640, width=224, height=320, link='link:coils_core0'),
    opening('open:coils_estair', 'coils', 'east_stair', at=704, width=320, height=384, shape='arch',
            link='link:coils_l1'),
    # floor 1
    opening('open:estair_landing1', 'landing1', 'east_stair', at=-1760, width=320, height=384, shape='arch',
            link='link:coils_l1'),
    opening('open:landing1_core1', 'landing1', 'core1', at=640, width=224, height=320, link='link:l1_core1'),
    opening('open:landing1_still', 'landing1', 'still', at=-1536, width=384, height=384, shape='arch',
            link='link:l1_still'),
    opening('open:still_reagents', 'still', 'reagents', at=-1600, width=224, height=320, link='link:still_reagents'),
    opening('open:still_poison', 'still', 'poison', at=-256, width=512, height=416, shape='arch',
            link='link:still_poison'),
    opening('open:poison_wstair', 'poison', 'west_stair', at=-320, width=224, height=320, link='link:poison_l1w'),
    # floor 2
    opening('open:wstair_landing2', 'landing2', 'west_stair', at=1728, width=320, height=384, shape='arch',
            link='link:l1w_l2'),
    opening('open:landing2_energy', 'landing2', 'energy', at=-768, width=512, height=416, shape='arch',
            link='link:l2_energy'),
    opening('open:energy_magic', 'energy', 'magic', at=960, width=224, height=320, link='link:energy_magic'),
    opening('open:magic_quarters', 'magic', 'quarters', at=896, width=512, height=416, shape='arch',
            link='link:magic_quarters'),
    opening('open:quarters_core2', 'quarters', 'core2', at=640, width=224, height=320, link='link:quarters_core2'),
    opening('open:quarters_hstair', 'quarters', 'high_stair', at=1728, width=256, height=320,
            link='link:quarters_l3'),
    # floor 3
    opening('open:hstair_landing3', 'landing3', 'high_stair', at=-1856, width=320, height=384, shape='arch',
            link='link:quarters_l3'),
    opening('open:landing3_core3', 'landing3', 'core3', at=640, width=224, height=320, link='link:l3_core3'),
    opening('open:landing3_library', 'landing3', 'library', at=-1536, width=512, height=416, shape='arch',
            link='link:l3_library'),
    opening('open:library_study', 'library', 'study', at=-1344, width=224, height=320, link='link:library_study'),
    opening('open:study_obs', 'study', 'observatory', at=-1664, width=448, height=416, shape='arch',
            link='link:study_obs'),
    opening('open:obs_stairway', 'observatory', 'stairway', at=-1856, width=384, height=416, shape='arch',
            link='link:obs_stairway'),
    opening('open:stairway_roof', 'stairway', 'roof', at=1728, walls=(1, edge_index('roof', [256, 2048])), width=448, height=448, link='link:stairway_roof'),
    # the lift shaft: holes in the cores' floors over the lift below
    {'id': 'open:shaft_a', 'from': 'room:core1', 'to': 'room:core0', 'in': 'floor', 'at': LIFT_W, 'size': LIFT_SIZE,
     'reveal': RUBBLE, 'link': 'link:core_01'},
    {'id': 'open:shaft_b', 'from': 'room:core2', 'to': 'room:core1', 'in': 'floor', 'at': LIFT_E, 'size': LIFT_SIZE,
     'reveal': RUBBLE, 'link': 'link:core_12'},
    {'id': 'open:shaft_c', 'from': 'room:core3', 'to': 'room:core2', 'in': 'floor', 'at': LIFT_W, 'size': LIFT_SIZE,
     'reveal': RUBBLE, 'link': 'link:core_23'},
]


def plat(at, size, rise, surface, top=None, **kw):
    d = {'at': at, 'size': size, 'rise': rise, 'surface': surface}
    if top:
        d['top_surface'] = top
    d.update(kw)
    return d


def gallery(x0, y0, x1, y1, base):
    return {'id': None, 'rise': 32, 'outline': rect(x0, y0, x1, y1), 'base': base,
            'surface': RUBBLE, 'top_surface': MARBLE, 'bottom_surface': BEAMS}


def room_doc(rid):
    name, b, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
    extra = EXTRA.get(rid)
    if extra:
        d.update(extra)
    return d


def _pipe_x(x, y0, y1, base):
    """A steam pipe of riveted iron along a wall (x fixed), 32 thick, hung at `base`."""
    return plat([x, (y0 + y1) / 2], [32, abs(y1 - y0)], 32, IRON, IRON, base=base,
                notes="A steam pipe of riveted iron along the wall, from the valve to the frozen door.")


def _pipe_y(y, x0, x1, base):
    return plat([(x0 + x1) / 2, y], [abs(x1 - x0), 32], 32, IRON, IRON, base=base,
                notes="A steam pipe of riveted iron along the wall, from the valve to the frozen door.")


def _case_post(x, y):
    """A wooden post (the cabinets' wood, 7t1cabs) at each end of a wall of bookcases, between them and the planks."""
    return plat([x, y], [64, 64], 512, CABS, CABS, notes="A post of the cabinets' wood at the end of the bookcases.")


EXTRA = {
    'door': {
        'notes': "Inside the enchanted door: the arrival. The door (a panel of Celeste's carved blue door) asks to leave and opens on X3's islet.",
    },
    'foyer': {
        'pillars': [{'at': [x, y], 'size': [96, 96], 'surface': PILLAR} for x in (-1536, -640) for y in (-512, 384)],
        'notes': "The foyer: four carved pillars (hwm2el) down a hall of grey rubble; the arch to the door south, the door to the athanor north.",
    },
    'athanor': {
        'platforms': [
            plat([0, 1920], [1024, 192], 480, IRON, IRON, notes="The athanor's iron stack against the north wall."),
            plat([-1344, 1888], [384, 256], 96, IRON, notes="A bench of iron crucibles."),
            plat([1344, 1888], [384, 256], 96, IRON, notes="A bench of iron crucibles."),
        ],
        'levels': [{'id': 'level:hearth', 'outline': rect(-448, 1472, 448, 1792), 'floor': -48,
                    'edge': IRON, 'surface': LAVA, 'notes': "The athanor's hearth: a bed of glowing coals a step down before the stack (48: the party steps back out, F14)."}],
        'notes': "The athanor: the great furnace of the tower, an iron stack against the north wall over a hearth of live coals; Fire Brew bubbles beside it.",
    },
    'coils': {
        'pillars': [{'at': [x, y], 'size': [128, 128], 'surface': IRON} for x, y in
                    ((320, 192), (960, 192), (320, 640), (960, 640))],
        'notes': "The lightning coils: four iron columns, each crowned with a crackling blue light.",
    },
    'still': {
        'platforms': [
            plat([-1024, -1856], [384, 256], 128, IRON, FROST, notes="The cold still's tank, furred with frost."),
            _pipe_y(-2032, -1216, -704, 288),
            _pipe_x(-1264, -2048, -704, 288),
        ],
        'notes': "The cold still: a frosted tank in the south-west corner; the steam pipe from the reagent store runs along the south and west walls toward the garden.",
    },
    'reagents': {
        'platforms': [_pipe_x(-1424, -2048, -1280, 320)],
        'store': True,
        'notes': "The reagent store: shelves of jars and sacks; the steam valve on its north wall with its pipe.",
    },
    'poison': {
        'platforms': [plat([x, y], [384, 256], 48, PLANKS, SOIL, notes="A planting bed of nightshade.")
                      for x, y in ((-768, 0), (-768, 768), (-128, 384), (-128, 1152))]
        + [_pipe_x(-1264, -512, -416, 288)],
        'notes': "The poison garden: raised beds of nightshade and hemlock; the steam pipe comes along the west wall to the frozen door.",
    },
    'east_stair': {
        'platforms': [{'id': 'platform:east_gallery', 'rise': 32, 'outline': octo(rect(1408, -2048, 2048, -1472)), 'base': 608,
                       'surface': RUBBLE, 'top_surface': MARBLE, 'bottom_surface': BEAMS,
                       'notes': "The gallery at the first floor (640), across the south end."}],
        'flights': [{'from': [1792, 576], 'to': [1792, -1472], 'open_below': 32, 'to_height': 640, 'width': 384,
                     'steps': 20, 'notes': "One long flight up the east wall, 20 steps of 32, open underneath."}],
        'notes': "Ground floor to the first (0 to 640), two storeys high: the flight up the east wall rises south to a gallery at the east landing.",
    },
    'west_stair': {
        'platforms': [{'id': 'platform:west_gallery', 'rise': 32, 'outline': octo(rect(-2048, 1408, -1408, 2048)), 'base': 608,
                       'surface': RUBBLE, 'top_surface': MARBLE, 'bottom_surface': BEAMS,
                       'notes': "The gallery at the second floor (1280), across the north end."}],
        'flights': [{'from': [-1728, -128], 'to': [-1728, 1408], 'open_below': 32, 'to_height': 1280, 'width': 384,
                     'steps': 20, 'notes': "One long flight up the west wall, 20 steps of 32, open underneath."}],
        'notes': "The first floor to the second (640 to 1280), behind the frozen door: the flight up the west wall rises north to a gallery at the west landing.",
    },
    'high_stair': {
        'platforms': [{'id': 'platform:high_gallery', 'rise': 32, 'outline': octo(rect(1408, -2048, 2048, -1664)), 'base': 608,
                       'surface': RUBBLE, 'top_surface': MARBLE, 'bottom_surface': BEAMS,
                       'notes': "The gallery at the top floor (1920), across the south end."}],
        'flights': [{'from': [1728, -448], 'to': [1728, -1664], 'open_below': 32, 'to_height': 1920, 'width': 320,
                     'steps': 20, 'notes': "One flight up the east wall, 20 steps of 32 (320 wide: its head clears the cut corner)."}],
        'notes': "The second floor to the top (1280 to 1920), behind the Librarian's door: the flight rises south to a gallery at the top landing.",
    },
    'stairway': {
        'platforms': [{'id': 'platform:roof_gallery', 'rise': 32, 'outline': rect(-192, 1408, 128, 2048), 'base': 608,
                       'surface': RUBBLE, 'top_surface': MARBLE, 'bottom_surface': BEAMS,
                       'notes': "The head of the stair, level with the roof (2560)."}],
        'flights': [{'from': [-1536, 1792], 'to': [-192, 1792], 'open_below': 32, 'to_height': 2560, 'width': 384,
                     'steps': 20, 'notes': "The Stairway to Heaven: one flight up the north wall into the open sky."}],
        'notes': "The top floor to the roof (1920 to 2560), open to the sky.",
    },
    'library': {
        'walls': [{'wall': 'w', 'panels': [{'at': 'centre', 'length': 1536, 'height': 512, 'surface': BOOKS,
                                             'notes': "Bookcases along the west wall."}]}],
        'platforms': [plat([x, y], [96, 512], 288, BOOKS, DESK, end_surface=CABS,
                           notes="A free-standing bookcase.") for x, y in ((-768, 448), (-256, 448), (-768, -640), (-256, -640))]
        + [_case_post(-1120, y) for y in (-1152, 384)]
        + [{'id': 'platform:art_of_magic', 'at': [-512, -1408], 'size': [96, 64], 'rise': 96, 'surface': DESK,
            'top_surface': {'texture': 'xnpbook', 'size': [128, 128], 'fit': True},
            'notes': "A lectern with The Art of Magic open on it (F12d: the open book xnpbook on its top)."}],
        'notes': "The Library of High Magic: bookcases along the west wall and in two rows; a lectern with The Art of Magic; the cabinet of Mysteries of Light.",
    },
    'study': {
        'walls': [{'wall': 4, 'surface': BOOKS, 'notes': "The Archmage's own books, across the tower's cut corner."}],
        'platforms': [plat([-1664, -1600], [384, 192], 80, DESK, DESK, notes="The Archmage's desk.")],
        'notes': "The Archmage's study: his desk and books, and his chest.",
    },
    'quarters': {
        'platforms': [{'id': f'platform:bed_{i}', 'at': [x, 384], 'size': [192, 256], 'rise': 48, 'surface': PLANKS,
                       'top_surface': SHEET, 'notes': "A narrow bed."} for i, x in enumerate((704, 1088))],
        'notes': "The Sorceresses' quarters: narrow beds along the north wall, a chest; the lever of the cage's gate on the south wall, the Librarian's door to the stair east.",
    },
    'observatory': {
        'platforms': [plat([-1440, 384], [192, 192], 64, IRON, IRON, notes="The orrery's iron plinth.")],
        'notes': "The observatory: an orrery on its plinth under the painted sky; a Pandorian box.",
    },
    'magic': {
        'levels': [{'id': 'level:magic_dais', 'outline': rect(1024, 1280, 1664, 1792), 'floor': 1312,
                    'edge': FRIEZE, 'notes': "A low dais for the Magic Brew's cauldron."}],
        'notes': "The magic lab: the Magic Brew's cauldron on a low dais; the Head Sorceress keeps it.",
    },
    'energy': {
        'notes': "The energy lab: crystals and the Energy Brew under a yellow glow.",
    },
    'roof': {
        'platforms': [plat([1536, 1088 + 128 * i], [384, 128], 32 * (i + 1), CLOUD_SIDE, CLOUD_TOP,
                           notes="A step of cloud.") for i in range(4)]
        + [{'id': 'platform:cloud_top', 'at': [1536, 1600], 'size': [384, 128], 'rise': 160, 'surface': CLOUD_SIDE,
            'top_surface': CLOUD_TOP, 'notes': "The Stairway to Heaven: steps of cloud climbing toward the sky."}],
        'notes': "The roof terrace under the open sky; a rubble parapet; the stair of cloud toward the High Magic clouds (X8).",
    },
}

for r in ('core0', 'core1', 'core2', 'core3'):
    EXTRA.setdefault(r, {})['notes'] = "The lift core: the brass cages' shaft through all four floors."


# ---------------------------------------------------------------------------------------- D-89 identity (session 29)
# Torches and sconces on the walls (room, compass wall, along): dress.py places them; the windows keep clear of them.
TORCHES = [('door', 'w', 0.5), ('door', 'e', 0.5), ('foyer', 'w', 0.3), ('foyer', 'w', 0.7), ('foyer', 'e', 0.3),
           ('foyer', 'e', 0.7), ('athanor', 's', 0.2), ('athanor', 's', 0.8), ('coils', 'e', 0.3),
           ('core0', 'n', 0.15), ('core1', 's', 0.15), ('core2', 'n', 0.15), ('core3', 's', 0.15),
           ('east_stair', 'w', 0.5), ('west_stair', 'e', 0.75), ('high_stair', 'w', 0.5),
           ('landing1', 'w', 0.8), ('landing2', 'n', 0.5), ('landing3', 'w', 0.8),
           ('still', 'n', 0.8), ('reagents', 'w', 0.5), ('poison', 'e', 0.3), ('poison', 'e', 0.8),
           ('energy', 'w', 0.4), ('energy', 'e', 0.3), ('magic', 'e', 0.3), ('magic', 'n', 0.3),
           ('quarters', 'w', 0.5), ('library', 'e', 0.3), ('library', 'e', 0.7), ('study', 'w', 0.3),
           ('observatory', 'w', 0.3), ('observatory', 'w', 0.7)]

LABS = {'athanor': [255, 150, 90], 'coils': [160, 190, 255], 'still': [190, 230, 255], 'poison': [150, 230, 120],
        'energy': [255, 225, 120], 'magic': [200, 140, 255]}
WIN_LEN, WIN_H, WIN_BOTTOM = 128, 256, 176


def _bench(at, size, notes="A laboratory bench of Clanker's cabinets' wood (7t1cabs) with retorts and bottles."):
    return plat(at, size, 96, CABS, DESK, notes=notes)


# Laboratory benches (MM7 Clanker's Laboratory and School of Sorcery: cabinets' wood, bottles and goblets on top).
BENCHES = {
    'coils': [_bench([56, 704], [80, 320]), _bench([1224, 128], [80, 320])],
    'still': [_bench([-1024, -704], [384, 80])],
    'energy': [_bench([-200, 1216], [384, 80])],
    'magic': [_bench([896, 1984], [384, 80])],
}
for _r, _b in BENCHES.items():
    EXTRA.setdefault(_r, {}).setdefault('platforms', []).extend(_b)


def _compass(o, i):
    p, q = o[i], o[(i + 1) % len(o)]
    xs = [pt[0] for pt in o]
    ys = [pt[1] for pt in o]
    if p[0] == q[0]:
        return 'w' if p[0] == min(xs) else ('e' if p[0] == max(xs) else None)
    if p[1] == q[1]:
        return 's' if p[1] == min(ys) else ('n' if p[1] == max(ys) else None)
    return None


def _footprints(rid, bottom):
    """Platforms of the room that reach the windows' height (above the room's floor) as their corner points."""
    out = []
    for pl in EXTRA.get(rid, {}).get('platforms', []):
        lo = pl.get('base', 0)
        if lo + pl['rise'] < bottom - 16 or lo > bottom + WIN_H:
            continue
        if 'outline' in pl:
            out.append([tuple(pt) for pt in pl['outline']])
        else:
            (x, y), (w, h) = pl['at'], pl['size']
            out.append([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)])
    return out


def windows(rid):
    """Windows to the sky (sky panels, as the roof's walls) on the room's outer walls: about one in every 640 of wall,
    clear of torches, the exit, platforms against the wall and the wall's ends; in a two-storey stair hall one row at
    the gallery's height."""
    o = outline(rid)
    name, b, fl, ce, theme = R[rid]
    if theme in ('theme:roof', 'theme:skystair') or rid.startswith('core'):
        return []
    bottom = WIN_BOTTOM + (640 if ce - fl > 640 else 0)
    walls = []
    for i in range(len(o)):
        p, q = o[i], o[(i + 1) % len(o)]
        if not on_octagon(p, q):
            continue
        L = ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** 0.5
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        keep = []          # stretches (from p) kept clear
        comp = _compass(o, i)
        for tr, tw, ta in TORCHES:
            if tr == rid and tw == comp:
                for a in (ta, 1 - ta):
                    keep.append((a * L - 112, a * L + 112))
        if rid == 'door' and comp == 's':
            c = (-1408 - p[0]) * ux + (-2048 - p[1]) * uy
            keep.append((c - 192, c + 192))
        for corners in _footprints(rid, bottom):
            # the corners near the wall line (inward normal = (-uy, ux) for a counter-clockwise outline)
            near = [(cx, cy) for cx, cy in corners if (cx - p[0]) * -uy + (cy - p[1]) * ux < 160]
            if near:
                al = [(cx - p[0]) * ux + (cy - p[1]) * uy for cx, cy in near]
                keep.append((min(al) - 48, max(al) + 48))
        n = max(1, round(L / 640)) if L >= 320 else 0
        panels = []
        for k in range(n):
            ideal = (k + 0.5) * L / n
            best = None
            for step in range(0, int(L / n / 2), 16):
                for c in (ideal - step, ideal + step):
                    lo, hi = c - WIN_LEN / 2, c + WIN_LEN / 2
                    if lo < 96 or hi > L - 96:
                        continue
                    if any(lo < b1 and hi > a1 for a1, b1 in keep):
                        continue
                    if any(abs(c - pc) < 384 for pc in panels):
                        continue
                    best = c
                    break
                if best is not None:
                    break
            if best is not None:
                panels.append(best)
        if panels:
            walls.append({'wall': i, 'panels': [
                {'offset': int(round(c - WIN_LEN / 2)), 'length': WIN_LEN, 'bottom': bottom, 'height': WIN_H,
                 'surface': SKYW, 'notes': "A window to the sky in the tower's outer wall."} for c in sorted(panels)]})
    return walls


def merlons():
    """The roof's crenellation: merlons of rubble, 192 long and 256 high, every 384 along the tower's outer edge
    (crenels of sky between), standing 40 in from the wall."""
    o = outline('roof')
    out = []
    for i in range(len(o)):
        p, q = o[i], o[(i + 1) % len(o)]
        if not on_octagon(p, q):
            continue
        L = ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** 0.5
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        nx, ny = -uy, ux
        k = int((L - 192) // 384) + 1
        start = (L - (k - 1) * 384) / 2
        for j in range(k):
            c = start + j * 384
            pts = [[round(p[0] + ux * (c + s) + nx * 72), round(p[1] + uy * (c + s) + ny * 72)] for s in (-96, 96)]
            out.append({'path': pts, 'height': 256, 'thickness': 64, 'surface': RUBBLE,
                        'notes': "A merlon of the roof's crenellation."})
    return out


for _r in R:
    _o = outline(_r)
    _taken = {w['wall'] for w in EXTRA.get(_r, {}).get('walls', [])}
    _taken |= {_compass(_o, w['wall']) for w in EXTRA.get(_r, {}).get('walls', []) if isinstance(w['wall'], int)}
    _w = [w for w in windows(_r) if w['wall'] not in _taken and _compass(_o, w['wall']) not in _taken - {None}]
    if _w:
        EXTRA.setdefault(_r, {}).setdefault('walls', []).extend(_w)
EXTRA['roof']['parapets'] = merlons()
