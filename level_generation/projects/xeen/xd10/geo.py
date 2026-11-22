#!/usr/bin/env python3
"""XD-10 Cave of Illusion: the geometry (rooms, openings) shared by L2, L3 and L4.

Three levels: the upper caves at 0 (a north-south spine from the north mouth at y 10,000 to the south mouth at y
1,150, the phantom safe, cache and skull alcoves west, the sluice east), the drowned galleries at -640 (under the
upper caves: the ledge, mirror maze, guardian post, echo cave, deep skulls, drowned gallery) and the reservoir bed at
-1280 (the reservoir east of everything, a tall cavern from -1280 to about +450 seen from the sluice's window and the
ledge; the wreck and sump south, the grotto and phantom vault east). Rooms are chamfered rectangles (caves with
`rough` walls and ceilings by points) whose axis-aligned sides carry the openings; walls between rooms are 128 thick.
Three stair tunnels (path rooms) join the levels.
"""

U0, U1, U2 = 0, -640, -1280


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM8 Passage Under Regna (d33): wet grey rock, granite floors, the sluice's bricks and flags, timber.
ROCK = S_('t68a02b', 256, 256)
GRANITE = S_('t68a03b', 128, 128)
GRANITE_LO = S_('t68a03a', 128, 128)
BRICK = S_('t09a01', 128, 256)
FLAGS = S_('t09a02b', 128, 128)
TRIM = S_('t09b11b', 128, 32)
SLUICE_DOOR = S_('t09a03c', 128, 256)
TIMBER = S_('t06a10', 32, 32, scale=2)
PLANKS = S_('t09a05b', 128, 128)
# Ice and snow where d33 has none: MM6 Icewind Keep's ice orair32, MM8's snow.
ICE = S_('orair32', 128, 128)
SNOW = S_('snow', 128, 128)
# The world's own (A6): bronze for the plug, riveted iron for its chain and the phantom safe, the notice board.
BRONZE = S_('xngong', 128, 128)
# The plug (224 x 224, 144 high), texture fit (session 7): the gong's face once on its top (scale 1.75, offset to the
# plug's corner: a mover's top takes no `fit`), its sides
# the gong's ringed edge slab xngong6 (seamless both ways).
PLUG_TOP = S_('xngong', 128, 128, scale=1.75, offset=[46, -46])  # whole on the plug's top (measured)
PLUG_SIDE = S_('xngong6', 128, 32, scale=2)
IRON = S_('xnrustirn', 64, 64)
SAFE_IRON = S_('xwiron', 128, 128)
ICICLE = S_('snow', 128, 128)
NOTICE = S_('xnnotice', 128, 128)
WATER = {'texture': 'wtrtyl', 'liquid': 'water', 'flow': 'down'}
# A mirage: the cave rock with the engine's fluid bit (rippling and swirling slowly).
MIRAGE = S_('t68a02b', 256, 256, liquid='liquid')

THEMES = [
    {'id': 'theme:ice', 'wall': ROCK, 'floor': SNOW, 'ceiling': ROCK, 'door': ROCK,
     'notes': "The two mouths: d33's grey rock, snow blown in over the floor (MM8 snow), icicles of snow-white ice."},
    {'id': 'theme:cave', 'wall': ROCK, 'floor': GRANITE, 'ceiling': ROCK, 'door': ROCK,
     'notes': "The upper caves: MM8 Passage Under Regna (d33): wet grey rock t68a02b on walls and roofs, its granite floor t68a03b."},
    {'id': 'theme:deep', 'wall': ROCK, 'floor': GRANITE_LO, 'ceiling': ROCK, 'door': BRICK,
     'notes': "The drowned galleries and the reservoir bed: d33's rock over its darker granite t68a03a; the stone sluice gates of d33's bricks t09a01."},
    {'id': 'theme:sluice', 'wall': BRICK, 'floor': FLAGS, 'ceiling': ROCK, 'door': SLUICE_DOOR, 'reveal': BRICK,
     'bands': [{'height': 32, 'surface': TRIM}],
     'notes': "The sluice: d33's bricks t09a01 over a trim t09b11b, its flags t09a02b, its door t09a03c, rock overhead."},
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


ROUGH = {'step': 192, 'depth': 40}

# id: (name, box or path, floor, ceiling, theme, extra)
R = {
    # upper caves (0)
    'north_mouth': ("North mouth", (-640, 8960, 640, 9984), U0, 576, 'theme:ice'),
    'mirage_cache': ("Behind the mirage", (-1792, 9088, -768, 9856), U0, 384, 'theme:cave'),
    'false_passage': ("Phantom safe", (-2048, 7296, -896, 8960), U0, 448, 'theme:cave'),
    'icicle_hall': ("Icicle hall", (-768, 6912, 1024, 8832), U0, 640, 'theme:cave'),
    'mirage_hall': ("Hall of Mirages", (-1024, 4224, 1536, 6784), U0, 768, 'theme:cave'),
    'frost_cavern': ("Frost cavern", (-768, 2304, 1280, 4096), U0, 576, 'theme:cave'),
    'south_mouth': ("South mouth", (-512, 1152, 640, 2176), U0, 512, 'theme:ice'),
    'skulls_1': ("Skull alcoves", (-1920, 2688, -896, 3712), U0, 384, 'theme:cave'),
    'sluice': ("Sluice", (1408, 2432, 2688, 3712), U0, 512, 'theme:sluice'),
    # drowned galleries (-640)
    'ledge': ("Ledge over the water", (1792, 3840, 2688, 6272), U1, -64, 'theme:deep'),
    'mirror_maze': ("Mirror maze", (256, 4992, 1664, 6272), U1, -224, 'theme:deep'),
    'skulls_2': ("Deep skull alcoves", (256, 6400, 1024, 7168), U1, -288, 'theme:deep'),
    'guard_post': ("Guardian post", (-1280, 4864, 128, 6400), U1, -192, 'theme:deep'),
    'echo_cave': ("Echo cave", (-1152, 3584, 0, 4736), U1, -224, 'theme:deep'),
    'drowned': ("Drowned gallery", (256, 3584, 1664, 4864), U1, -192, 'theme:deep'),
    # reservoir bed (-1280)
    'reservoir': ("Reservoir bed", (2816, 1024, 6016, 6400), U2, 448, 'theme:deep'),
    'wreck': ("Sunken boat", (1088, 1024, 2688, 2176), U2, -768, 'theme:deep'),
    'sump': ("Sump", (-256, 768, 960, 2048), U2, -832, 'theme:deep'),
    'grotto': ("Grotto of the great skull", (6144, 2560, 7424, 4096), U2, -640, 'theme:deep'),
    'phantom_vault': ("Phantom vault", (6272, 4224, 7296, 5120), U2, -768, 'theme:deep'),
}
# The stair tunnels: (name, path, floor, to, height, theme)
P = {
    'ice_stair': ("Ice stair", [[1344, 6912], [1344, 7296], [2432, 7296], [2432, 6400]], U0, U1, 384, 'theme:cave'),
    'steps': ("Reservoir steps", [[2240, 3712], [2240, 2496], [2688, 2496]], U1, U2, 384, 'theme:deep'),
    'wreck_stair': ("Gallery stair", [[1408, 3456], [1408, 2304]], U1, U2, 384, 'theme:deep'),
}
PATH_WIDTH = 384

CHAMFER = {
    'mirage_hall': (384, 384, 0, 384), 'reservoir': (384, 0, 384, 384), 'ledge': (192, 0, 0, 192),
    'sluice': 0, 'wreck': (256, 0, 0, 0), 'drowned': (256, 0, 256, 256), 'north_mouth': (192, 192, 256, 256), 'south_mouth': (256, 256, 192, 192),
    'mirage_cache': 192, 'skulls_1': 192, 'skulls_2': 160, 'phantom_vault': 192, 'echo_cave': 224,
    'grotto': (320, 320, 320, 0),
}

ORDER = sorted(list(R) + list(P))


def outline(rid):
    if rid in P:
        return None
    b = R[rid][1]
    return cave(*b, CHAMFER.get(rid, 256))


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
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


OPENINGS = [
    opening('open:n_icicle', 'north_mouth', 'icicle_hall', at=0, width=512, height=448, link='link:n_icicle'),
    opening('open:icicle_mirage', 'icicle_hall', 'mirage_hall', at=64, width=640, height=512, link='link:icicle_mirage'),
    opening('open:mirage_frost', 'mirage_hall', 'frost_cavern', at=256, width=640, height=480, link='link:mirage_frost'),
    opening('open:frost_s', 'frost_cavern', 'south_mouth', at=64, width=512, height=416, link='link:frost_s'),
    opening('open:icicle_false', 'icicle_hall', 'false_passage', at=8064, width=384, height=384, link='link:icicle_false'),
    opening('open:false_cache', 'false_passage', 'mirage_cache', at=-1344, width=256, height=320, link='link:false_cache'),
    opening('open:cache_n', 'mirage_cache', 'north_mouth', at=9472, width=256, height=320, link='link:cache_n'),
    opening('open:frost_skulls', 'frost_cavern', 'skulls_1', at=3200, width=384, height=352, link='link:frost_skulls'),
    opening('open:frost_sluice', 'frost_cavern', 'sluice', at=3072, width=256, height=352, link='link:frost_sluice'),
    opening('open:sluice_window', 'sluice', 'reservoir', at=3072, width=640, height=256, sill=128,
            notes="The sluice's railed window over the reservoir (sill 128): the water far below, later the bed."),
    opening('open:mirage_icestair', 'mirage_hall', 'ice_stair', width=320, height=352, link='link:mirage_ledge'),
    opening('open:icestair_ledge', 'ice_stair', 'ledge', width=320, height=352, link='link:stair_ledge'),
    opening('open:ledge_maze', 'ledge', 'mirror_maze', at=5760, width=384, height=352, link='link:ledge_maze'),
    opening('open:maze_post', 'mirror_maze', 'guard_post', at=5632, width=384, height=352, link='link:maze_post'),
    opening('open:post_echo', 'guard_post', 'echo_cave', at=-576, width=384, height=352, link='link:post_echo'),
    opening('open:maze_skulls', 'mirror_maze', 'skulls_2', at=704, width=256, height=320, link='link:maze_skulls'),
    opening('open:ledge_drowned', 'ledge', 'drowned', at=4352, width=320, height=352, link='link:ledge_drowned'),
    opening('open:ledge_steps', 'ledge', 'steps', width=320, height=352, link='link:ledge_steps'),
    opening('open:ledge_reservoir', 'ledge', 'reservoir', at=5056, width=1664, height=448, sill=128,
            notes="The ledge's railed overlook (sill 128) over the reservoir."),
    opening('open:drowned_wstair', 'drowned', 'wreck_stair', width=320, height=352, link='link:drowned_wstair'),
    opening('open:wstair_wreck', 'wreck_stair', 'wreck', width=320, height=352, link='link:wstair_wreck'),
    opening('open:wreck_sump', 'wreck', 'sump', at=1536, width=384, height=384, link='link:wreck_sump'),
    opening('open:wreck_reservoir', 'wreck', 'reservoir', at=1792, width=512, height=448, link='link:wreck_reservoir'),
    opening('open:steps_reservoir', 'steps', 'reservoir', width=320, height=352, link='link:steps_reservoir', from_wall=3,
            to_wall=5),
    opening('open:reservoir_grotto', 'reservoir', 'grotto', at=3328, width=512, height=448, link='link:reservoir_grotto'),
    opening('open:grotto_vault', 'grotto', 'phantom_vault', at=6784, width=256, height=320, link='link:grotto_vault'),
]


def plat(at, size, rise, surface, top=None, **kw):
    d = {'at': at, 'size': size, 'rise': rise, 'surface': surface}
    if top:
        d['top_surface'] = top
    d.update(kw)
    return d


def stal(at, radius=96, length=256, surface=None):
    d = {'at': at, 'radius': radius, 'length': length}
    if surface:
        d['surface'] = surface
    return d


# Rock islands of the mirror maze: ice-faced pillars (orair32).
MAZE_ISLANDS = [
    [[512, 5248], [768, 5248], [832, 5440], [640, 5568], [480, 5440]],
    [[960, 5696], [1216, 5696], [1280, 5888], [1088, 6016], [928, 5888]],
    [[1152, 5184], [1408, 5184], [1408, 5376], [1216, 5440]],
    [[448, 5824], [640, 5824], [704, 5952], [512, 6016]],
]

# The water: one mover filling the reservoir's outline from the bed to -660, sinking 640 (20 under the bed).
WATER_TOP = -660
WATER_OUTLINE = cave(2848, 1056, 5984, 6368, (352, 0, 352, 352))

EXTRA = {
    'north_mouth': {
        'ceiling_points': [[0, 9472, 704], [-320, 9600, 640], [320, 9600, 640]],
        'stalactites': [stal([-384, 9216], 64, 192, ICICLE), stal([416, 9280], 72, 224, ICICLE), stal([256, 9792], 56, 160, ICICLE)],
        'notes': "The arrival: a funnel of grey rock under icicles, snow blown in over the floor; the daylight of the tundra in its north wall (the exit to X5); a shimmering wall on the west is a mirage into the cache.",
    },
    'mirage_cache': {'rough': ROUGH, 'notes': "A small dry pocket between the two mirages: the chest with the Potion of Might."},
    'false_passage': {
        'rough': ROUGH, 'ceiling_points': [[-1472, 8128, 544]],
        'platforms': [{'id': 'platform:safe', 'at': [-1856, 7616], 'size': [160, 128], 'rise': 160,
                       'surface': dict(SAFE_IRON, liquid='liquid'), 'top_surface': dict(SAFE_IRON, liquid='liquid'),
                       'notes': "The phantom safe: an iron safe that ripples like the mirages (click: your hand passes through it)."}],
        'notes': "A side cave off the icicle hall ending at a safe that is not there; its north wall shimmers (the mirage into the cache).",
    },
    'icicle_hall': {
        'rough': ROUGH, 'ceiling_points': [[128, 7872, 800], [-384, 7424, 704], [640, 8320, 704]],
        'stalactites': [stal([-384, 7360], 96, 320, ICICLE), stal([576, 7424], 88, 288, ICICLE), stal([640, 8256], 96, 320, ICICLE),
                        stal([-320, 8384], 80, 256, ICICLE), stal([192, 7616], 72, 224, ICICLE), stal([832, 7872], 64, 192, ICICLE)],
        'notes': "A long cave hung with ice: icicles (stalactites of Icewind Keep's ice) down both sides; the phantom safe's cave west.",
    },
    'mirage_hall': {
        'rough': ROUGH, 'ceiling_points': [[256, 5504, 1024], [-512, 5376, 896], [1024, 5632, 896], [256, 4736, 896],
                                           [256, 6272, 896]],
        'stalactites': [stal([-576, 4800], 112, 320), stal([1088, 4864], 96, 288), stal([-640, 6080], 104, 320),
                        stal([960, 6144], 96, 256), stal([448, 5248], 112, 320), stal([-256, 5888], 80, 224)],
        'pillars': [{'outline': [[-704, 5248], [-512, 5248], [-448, 5440], [-640, 5568], [-768, 5440]], 'surface': ROCK,
                     'notes': "A rock column that shimmers in the heat haze of the mirages."}],
        'notes': "The great hall: walls that seem to waver, a roof that rises to 1,024; the ice stair down to the ledge in its north-east corner.",
    },
    'frost_cavern': {
        'rough': ROUGH, 'ceiling_points': [[256, 3200, 704]],
        'stalactites': [stal([-384, 2752], 80, 256), stal([896, 3712], 88, 256), stal([-384, 3712], 72, 224)],
        'notes': "Between the hall and the south mouth: the sluice's door east, the skull alcoves west.",
    },
    'south_mouth': {
        'ceiling_points': [[64, 1600, 640]],
        'stalactites': [stal([-256, 1472], 64, 192, ICICLE), stal([384, 1792], 64, 192, ICICLE)],
        'notes': "The way out to the Troll Forest side of X5: ice at the lip, snow on the floor, daylight in the south wall.",
    },
    'skulls_1': {
        'rough': ROUGH,
        'platforms': [{'id': 'platform:shelf_luck', 'at': [-1728, 3456], 'size': [192, 128], 'rise': 96, 'surface': ROCK,
                       'top_surface': ROCK, 'notes': "A rock shelf: the skull of Luck."},
                      {'id': 'platform:shelf_pers', 'at': [-1728, 2944], 'size': [192, 128], 'rise': 96, 'surface': ROCK,
                       'top_surface': ROCK, 'notes': "A rock shelf: the skull of Personality."}],
        'notes': "Two talking skulls on rock shelves along the west wall.",
    },
    'sluice': {
        'levels': [{'id': 'level:pool', 'outline': [[1792, 2688], [2304, 2688], [2304, 3200], [1792, 3200]], 'floor': -64,
                    'edge': BRICK, 'surface': WATER, 'notes': "The plug's pool, a step down in the flags."}],
        'notes': "A brick chamber over the reservoir: the great bronze plug on its chain in a pool; the railed window east looks down on the water.",
    },
    'ledge': {
        'walls': [{'wall': 'w', 'panels': [{'id': 'panel:notice', 'at': 'centre', 'length': 192, 'bottom': 96, 'height': 160,
                                            'surface': dict(PLANKS, fit=True),
                                            'notes': "A scratched notice by the way down."}]}],
        'notes': "A railed shelf over the reservoir, high and open: the water below, the sluice gates of the drowned gallery and of the steps.",
    },
    'mirror_maze': {
        'rough': ROUGH,
        'pillars': [{'outline': o, 'surface': dict(ICE, scale=4), 'notes': "A rock island faced with ice: the maze's mirrors."}
                    for o in MAZE_ISLANDS],
        'notes': "Ice walls round rock islands that throw back the party's reflections; one wall is a mirage into the deep skulls.",
    },
    'skulls_2': {
        'rough': ROUGH,
        'platforms': [{'id': 'platform:shelf_int', 'at': [448, 6976], 'size': [192, 128], 'rise': 96, 'surface': ROCK,
                       'top_surface': ROCK, 'notes': "The skull of Intellect."},
                      {'id': 'platform:shelf_speed', 'at': [832, 6976], 'size': [192, 128], 'rise': 96, 'surface': ROCK,
                       'top_surface': ROCK, 'notes': "The skull of Speed."}],
        'notes': "Behind the maze's mirage: two skulls on shelves along the north wall.",
    },
    'guard_post': {'rough': ROUGH, 'ceiling_points': [[-576, 5632, -64]], 'notes': "The Guardians' post round a chest."},
    'echo_cave': {'rough': ROUGH, 'ceiling_points': [[-576, 4160, -96]],
                  'notes': "A round cave that answers in the party's own voices; the gem cache."},
    'drowned': {
        'rough': ROUGH,
        'levels': [{'id': 'level:pool_1', 'outline': cave(512, 3840, 960, 4288, 96), 'floor': -704, 'bank': 96,
                    'surface': WATER, 'notes': "A pool left in the gallery."},
                   {'id': 'level:pool_2', 'outline': cave(1216, 4096, 1472, 4416, 96), 'floor': -704, 'bank': 96,
                    'surface': WATER, 'notes': "A pool left in the gallery."}],
        'notes': "Behind its sluice gate until the plug is pulled: a wet gallery with pools; water golems.",
    },
    'reservoir': {
        'ceiling_points': [[4416, 3712, 704], [3584, 2304, 576], [5248, 5120, 576]],
        'stalactites': [stal([4992, 2048], 128, 448), stal([3840, 5248], 112, 384), stal([5376, 4160], 120, 448)],
        'notes': "A tall cavern from the bed (-1280) to a roof above the upper caves: drowned to -660 until the plug is pulled, then a bed of silt, weed and shells; the ledge and the sluice look down on it from the west, the grotto opens east.",
    },
    'wreck': {
        'rough': ROUGH,
        'platforms': [{'id': 'platform:hull', 'outline': [[1664, 1408], [2240, 1408], [2432, 1536], [2240, 1664], [1664, 1664]],
                       'rise': 64, 'surface': PLANKS, 'top_surface': PLANKS,
                       'notes': "The sunken boat's hull, keel-up in the silt."}],
        'notes': "A boat stranded on the drained floor, its strongbox intact.",
    },
    'sump': {'rough': ROUGH,
             'levels': [{'id': 'level:sump_hole', 'outline': cave(64, 1088, 512, 1536, 128), 'floor': -1344, 'bank': 96,
                         'surface': WATER, 'notes': "The sump's hole, where the water went."}],
             'notes': "Where the water went: a roaring hole in the floor; the last water golems."},
    'grotto': {
        'rough': ROUGH, 'ceiling_points': [[6784, 3328, -448]],
        'platforms': [{'id': 'platform:great_shelf', 'at': [7200, 3328], 'size': [256, 256], 'rise': 128, 'surface': ROCK,
                       'top_surface': ROCK, 'notes': "The great skull's rock seat by the east wall."}],
        'notes': "The great skull on its rock seat; a mirage north into the phantom vault.",
    },
    'phantom_vault': {'rough': ROUGH, 'notes': "Behind the grotto's mirage: the cave's hoard."},
}


# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s28 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (XD-10: "boxy caves in one grey rock with flat
# floors"): the drowned galleries, the reservoir bed, the wreck, the sump and the grotto in d33's darker granite t68a03a
# (the upper caves keep t68a02b), the mirages there wearing it too (dress.py); uneven floors in the upper caves and
# the dry galleries. Weed on the reservoir bed cannot be placed: the bed lies inside the water mover at the map's
# start (objects there are refused); its dark granite t68a03a stands for the silt.
# A8 s29: t68a02a turned out to be MM8 d17's rock, not d33's (check_identity.py: family share 44 %); the deep walls
# take d33's own dark granite t68a03a instead, the ceilings keep d33's wet rock t68a02b.
ROCK_DEEP = S_('t68a03a', 128, 128)
MIRAGE_DEEP = S_('t68a03a', 128, 128, liquid='liquid')
for _t in THEMES:
    if _t['id'] == 'theme:deep':
        _t.update({'wall': dict(ROCK_DEEP)})
        _t['notes'] = _t['notes'].replace("d33's rock over", "d33's dark granite t68a03a on the walls, its wet rock above, over")


def _uneven(rid, pts):
    x0, y0, x1, y1 = R[rid][1]
    fl = R[rid][2]
    EXTRA.setdefault(rid, {})['floor_points'] = [[round(x0 + fx * (x1 - x0)), round(y0 + fy * (y1 - y0)), fl + h]
                                                 for fx, fy, h in pts]


_uneven('icicle_hall', [(0.3, 0.3, 32), (0.7, 0.6, -24), (0.45, 0.8, 40)])
_uneven('mirage_hall', [(0.3, 0.3, -24), (0.7, 0.4, 40), (0.4, 0.75, 32)])
_uneven('frost_cavern', [(0.3, 0.4, 40), (0.7, 0.7, -16), (0.6, 0.3, 24)])
_uneven('guard_post', [(0.3, 0.3, 24), (0.7, 0.7, 40)])
_uneven('echo_cave', [(0.35, 0.6, 40), (0.65, 0.35, -16)])
_uneven('mirage_cache', [(0.5, 0.5, 32)])
_uneven('phantom_vault', [(0.5, 0.45, 32)])


def room_doc(rid):
    if rid in P:
        name, path, fl, to, h, theme = P[rid]
        return {'id': 'room:' + rid, 'name': name, 'path': path, 'width': PATH_WIDTH, 'smooth': 1, 'floor': fl,
                'slope': {'to': to}, 'ceiling': fl + h, 'theme': theme,
                'notes': {'ice_stair': "A winding ramp of rock down from the Hall of Mirages to the ledge (0 to -640).",
                          'steps': "Steps of rock from the ledge down to the reservoir bed, behind a stone sluice gate (-640 to -1280).",
                          'wreck_stair': "A ramp from the drowned gallery down to the wreck, behind a stone sluice gate (-640 to -1280)."}[rid]}
    name, b, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
    d.update(EXTRA.get(rid, {}))
    return d


def extent(rid):
    if rid in P:
        pts = P[rid][1]
    else:
        pts = outline(rid)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs) + (PATH_WIDTH if rid in P else 0)
    h = max(ys) - min(ys) + (PATH_WIDTH if rid in P else 0)
    return [w, h], [(max(xs) + min(xs)) // 2, (max(ys) + min(ys)) // 2]
