#!/usr/bin/env python3
"""DD-18 Sandcaster Sewer: the geometry (rooms, openings) shared by L2, L3 and L4.

Two levels in one frame (x east, y north, heights from the arrival floor at the shaft ladder's foot):
- under Sandcaster (0): the street shaft (the arrival; Barticus' members' room behind a door south of it under the
  gym's sign), the main drain east to the stalker warren (its breeding vault north) and the great cistern; south of
  the main drain the alcoves (three niches), the cobra drain east of them into the cistern; the broken drain south of
  the cistern, its rubble slope down to
- the long tunnel (-640): the tunnel head, the mantis gallery west of it, the mantis nest south (its egg cells east),
  the drowned vault west of the nest, and the long tunnel west in three lengths (the sand drift in the middle) to the
  desert gate, bolted on the D5 side.
Rooms are chamfered rectangles (caves with `rough` walls) whose axis-aligned sides carry the openings; walls between
rooms are 128 thick.
"""

U0, U1 = 0, -640


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Shadow Guild (6d08): the sandstone drains under a sandstone city (dungeon_families.yml `sewers`).
CARVED = S_('d5walba', 256, 256)          # sandstone with a carved course along its top: the members' room, the cistern
RUBBLE = S_('d5walc', 256, 256)           # tan rubble brick: the drains, the shaft, the warren
JAMB_R = S_('d5walbre', 128, 256)         # carved pillar jambs (doorway reveals)
JAMB_L = S_('d5walble', 128, 256)
FLAGS = S_('d5florc', 128, 128)           # big sandstone flags: the drains
FLAGS2 = S_('d5florb', 128, 128)          # framed flags: the members' room, the cistern, the vault
FRET = S_('d5ceila', 128, 128)            # the stepped-fret ceilings
FRET2 = S_('d5ceild', 128, 128)           # the great cistern's and the members' room's vaults
DOOR = S_('d5dorsma', 128, 256)           # 6d08's lattice door
TRIM = S_('d5smtrb', 32, 32)              # a carved glyph: the pay box, the bench and shelf edges
WATER = {'texture': 'orwtrtyl', 'liquid': 'water'}
GRATE = S_('d1lggrt', 256, 256)           # MM6 sewer grate: the drains' outlets
STREETGRATE = S_('d1lggrt', 256, 256, scale=2.5, offset=[102, 102])  # own size, scaled (merge point 17)   # one round street grate over the shaft, its centre moved onto the shaft's
LADDER = S_('d1ladder', 128, 256)         # the shaft's iron ladder
SIGN = {'texture': 'xstraining', 'size': [128, 64], 'fit': True}   # A6's Barticus' sign
# MM8 Passage Under Regna (d33): its rock for the long tunnel and the mantis diggings.
ROCK = S_('t68a02b', 512, 512)          # laid at twice its size: the rock reads calmer
ROCKFLOOR = S_('t68a03b', 128, 128)
ROCKFLOOR2 = S_('t68a03a', 128, 128)

THEMES = [
    {'id': 'theme:shaft', 'wall': RUBBLE, 'floor': FLAGS, 'ceiling': STREETGRATE, 'door': DOOR, 'reveal': JAMB_R,
     'notes': "The street shaft: 6d08's tan rubble brick d5walc up to a round street grate (MM6 d1lggrt); flags d5florc."},
    {'id': 'theme:gym', 'wall': CARVED, 'floor': FLAGS2, 'ceiling': FRET2, 'door': DOOR, 'reveal': JAMB_R,
     'notes': "Barticus' members' room: carved sandstone d5walba, framed flags d5florb, the stepped-fret vault d5ceild."},
    {'id': 'theme:drain', 'wall': RUBBLE, 'floor': FLAGS, 'ceiling': FRET, 'door': DOOR, 'reveal': JAMB_L,
     'notes': "The drains: rubble brick d5walc, flags d5florc, the stepped-fret ceiling d5ceila, a channel of slow water."},
    {'id': 'theme:cistern', 'wall': CARVED, 'floor': FLAGS2, 'ceiling': FRET2, 'door': DOOR, 'reveal': JAMB_R,
     'notes': "The great cistern: the city's old waterworks, carved sandstone d5walba under stepped-fret vaults d5ceild."},
    {'id': 'theme:warren', 'wall': RUBBLE, 'floor': FLAGS, 'ceiling': RUBBLE, 'door': DOOR,
     'notes': "The stalker warren and its vault: collapsed rubble brick d5walc in broken walls over the old flags."},
    {'id': 'theme:tunnel', 'wall': ROCK, 'floor': ROCKFLOOR, 'ceiling': ROCK, 'door': DOOR,
     'notes': "The long tunnel: MM8 d33's rock t68a02b over its floor t68a03b."},
    {'id': 'theme:nest', 'wall': ROCK, 'floor': ROCKFLOOR2, 'ceiling': ROCK, 'door': DOOR,
     'notes': "The mantis diggings: d33's rock chewed into galleries, its darker floor t68a03a."},
    {'id': 'theme:vault', 'wall': CARVED, 'floor': FLAGS2, 'ceiling': FRET, 'door': DOOR, 'reveal': JAMB_L,
     'notes': "The drowned vault: an older sandstone vault the tunnel broke into, d5walba over framed flags."},
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

# id: (name, box, floor, ceiling, theme)
R = {
    # under Sandcaster (0)
    'shaft': ("Street shaft", (-320, -320, 320, 320), U0, 1280, 'theme:shaft'),
    'gym': ("Barticus' members' room", (-896, -1792, 896, -448), U0, 512, 'theme:gym'),
    'main_drain': ("Main drain", (512, -384, 3456, 384), U0, 512, 'theme:drain'),
    'warren': ("Stalker warren", (3584, -896, 5120, 896), U0, 448, 'theme:warren'),
    'breeding_vault': ("Breeding vault", (3840, 1024, 4864, 1920), U0, 384, 'theme:warren'),
    'cistern': ("The great cistern", (5248, -1536, 7808, 1408), U0, 896, 'theme:cistern'),
    'alcoves': ("The alcoves", (1024, -1408, 3456, -512), U0, 448, 'theme:drain'),
    'niche_1': ("Alcove (west)", (1280, -1920, 1664, -1536), U0, 320, 'theme:drain'),
    'niche_2': ("Alcove (middle)", (2048, -2176, 2432, -1536), U0, 320, 'theme:drain'),
    'niche_3': ("Alcove (east)", (2816, -1920, 3200, -1536), U0, 320, 'theme:drain'),
    'cobra_drain': ("Cobra drain", (3584, -2048, 5120, -1024), U0, 448, 'theme:drain'),
    'collapse': ("Broken drain", (5248, -3200, 7808, -1664), U0, 576, 'theme:warren'),
    # the long tunnel (-640)
    'tunnel_head': ("Tunnel head", (5632, -6400, 7424, -5120), U1, -128, 'theme:tunnel'),
    'mantis_gallery': ("Mantis gallery", (3712, -6528, 5504, -4864), U1, -96, 'theme:nest'),
    'mantis_nest': ("Mantis nest", (3456, -9216, 5760, -6656), U1, 0, 'theme:nest'),
    'egg_cells': ("Egg cells", (5888, -8704, 6912, -7424), U1, -256, 'theme:nest'),
    'drowned': ("Drowned vault", (1408, -7552, 3328, -6144), U1, -128, 'theme:vault'),
    'tunnel_east': ("The long tunnel (east)", (-256, -6016, 3584, -5376), U1, -256, 'theme:tunnel'),
    'sand_drift': ("The long tunnel (the sand drift)", (-2944, -6144, -384, -5248), U1, -192, 'theme:tunnel'),
    'tunnel_west': ("The long tunnel (west)", (-6656, -6016, -3072, -5376), U1, -256, 'theme:tunnel'),
    'desert_gate': ("Desert gate", (-8064, -6272, -6784, -5120), U1, 0, 'theme:tunnel'),
}
# Sloping tunnels: (name, path, floor, to, ceiling, theme)
P = {
    'rubble_slope': ("Rubble slope", [[6528, -3328], [6528, -4992]], U0, U1, 448, 'theme:warren'),
}
PATH_WIDTH = 448

CHAMFER = {
    'warren': 256, 'breeding_vault': 192, 'collapse': (0, 384, 0, 0), 'mantis_gallery': 320, 'mantis_nest': 448,
    'egg_cells': 256, 'cistern': 0, 'tunnel_head': 0,
}
CAVES = ('warren', 'breeding_vault', 'collapse', 'mantis_gallery', 'mantis_nest', 'egg_cells')

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
    opening('open:shaft_drain', 'shaft', 'main_drain', at=0, width=256, height=320, link='link:shaft_drain'),
    opening('open:shaft_gym', 'shaft', 'gym', at=0, width=256, height=320, link='link:shaft_gym'),
    opening('open:drain_warren', 'main_drain', 'warren', at=0, width=384, height=384, link='link:drain_warren'),
    opening('open:warren_vault', 'warren', 'breeding_vault', at=4352, width=384, height=320, link='link:warren_vault'),
    opening('open:warren_cistern', 'warren', 'cistern', at=0, width=256, height=320, link='link:warren_cistern'),
    opening('open:drain_alcoves', 'main_drain', 'alcoves', at=1536, width=256, height=320, link='link:drain_alcoves'),
    opening('open:alcove_1', 'alcoves', 'niche_1', at=1472, width=256, height=256, link='link:alcove_1'),
    opening('open:alcove_2', 'alcoves', 'niche_2', at=2240, width=256, height=256, link='link:alcove_2'),
    opening('open:alcove_3', 'alcoves', 'niche_3', at=3008, width=256, height=256, link='link:alcove_3'),
    opening('open:alcoves_cobra', 'alcoves', 'cobra_drain', at=-1216, width=256, height=320, link='link:alcoves_cobra'),
    opening('open:cobra_cistern', 'cobra_drain', 'cistern', at=-1280, width=256, height=320, link='link:cobra_cistern'),
    opening('open:cistern_collapse', 'cistern', 'collapse', at=6528, width=512, height=448, link='link:cistern_collapse'),
    opening('open:collapse_slope', 'collapse', 'rubble_slope', width=384, height=448, link='link:collapse_slope'),
    opening('open:slope_head', 'rubble_slope', 'tunnel_head', width=384, height=448, link='link:slope_head'),
    opening('open:head_gallery', 'tunnel_head', 'mantis_gallery', at=-5760, width=384, height=384, link='link:head_gallery'),
    opening('open:gallery_nest', 'mantis_gallery', 'mantis_nest', at=4608, width=384, height=384, link='link:gallery_nest'),
    opening('open:nest_eggs', 'mantis_nest', 'egg_cells', at=-8064, width=320, height=320, link='link:nest_eggs'),
    opening('open:nest_drowned', 'mantis_nest', 'drowned', at=-7360, width=256, height=320, link='link:nest_drowned'),
    opening('open:drowned_tunnel', 'drowned', 'tunnel_east', at=2368, width=384, height=352, link='link:drowned_tunnel'),
    opening('open:gallery_tunnel', 'mantis_gallery', 'tunnel_east', at=-5696, width=384, height=384, link='link:gallery_tunnel'),
    opening('open:tunnel_drift', 'tunnel_east', 'sand_drift', at=-5696, width=448, height=384, link='link:tunnel_drift'),
    opening('open:drift_west', 'sand_drift', 'tunnel_west', at=-5696, width=448, height=384, link='link:drift_west'),
    opening('open:tunnel_gate', 'tunnel_west', 'desert_gate', at=-5696, width=256, height=320, link='link:tunnel_gate'),
]


def channel(rid, axis, cid=None, inset=128, width=192, depth=48, centre=None):
    """A channel of slow water down a drain: a level sunk `depth`, inset from the end walls."""
    x0, y0, x1, y1 = R[rid][1]
    if axis == 'x':
        cy = (y0 + y1) // 2 if centre is None else centre
        o = [[x0 + inset, cy - width // 2], [x1 - inset, cy - width // 2], [x1 - inset, cy + width // 2],
             [x0 + inset, cy + width // 2]]
    else:
        cx = (x0 + x1) // 2 if centre is None else centre
        o = [[cx - width // 2, y0 + inset], [cx + width // 2, y0 + inset], [cx + width // 2, y1 - inset],
             [cx - width // 2, y1 - inset]]
    return {'id': cid or f'level:{rid}_channel', 'outline': o, 'floor': R[rid][2] - depth, 'edge': FLAGS,
            'surface': dict(WATER), 'notes': "A channel of slow water down the drain."}


def plat(pid, at, size, rise, surface, top=None, notes=None, **kw):
    d = {'id': pid, 'at': at, 'size': size, 'rise': rise, 'surface': surface}
    if top:
        d['top_surface'] = top
    d.update(kw)
    if notes:
        d['notes'] = notes
    return d


def outlet(pid, offset, notes="A grated outlet from the street above ('Sewer Drain')."):
    return {'id': pid, 'offset': offset, 'length': 256, 'bottom': 64, 'height': 256, 'surface': dict(GRATE, fit=True),
            'notes': notes}


# The members' room: the bench with the book, the brews' shelf, a lifting block and the weights' rack.
BENCH_AT, BENCH_SIZE, BENCH_RISE = [-576, -1088], [128, 448], 64
SHELF_AT, SHELF_SIZE, SHELF_RISE = [0, -1712], [512, 96], 128

EXTRA = {
    'shaft': {
        'walls': [
            {'wall': 'n', 'panels': [{'at': 'centre', 'length': 128, 'bottom': 256, 'height': 896, 'surface': dict(LADDER),
                                      'notes': "The iron ladder above the exit's face, up to the street's iron lid."}]},
            {'wall': 's', 'panels': [
                {'id': 'panel:gym_sign', 'at': 'centre', 'length': 128, 'bottom': 352, 'height': 64, 'surface': dict(SIGN),
                 'notes': "Barticus' sign over the members' room's door (A6's xstraining)."},
                {'id': 'panel:paybox', 'offset': 512, 'length': 64, 'bottom': 96, 'height': 96,
                 'surface': dict(TRIM, fit=True),
                 'notes': "The pay box beside the members' room's door: a carved slot in the wall."}]},
        ],
        'notes': "Sandcaster's street shaft under Barticus' sign: an iron ladder on the north wall up to the street's lid (the way in and out), the members' room's door south under the sign with the pay box beside it, the main drain's door east.",
    },
    'gym': {
        'platforms': [
            plat('platform:bench', BENCH_AT, BENCH_SIZE, BENCH_RISE, FLAGS2, FLAGS,
                 "A stone bench along the west wall; The Art of Bodybuilding lies open on it."),
            plat('platform:shelf', SHELF_AT, SHELF_SIZE, SHELF_RISE, CARVED, FLAGS,
                 "The brews' shelf against the south wall: the Vitamin Brew and the Protein Brew."),
            plat('platform:block', [512, -960], [256, 256], 96, CARVED, FLAGS,
                 "A lifting block, worn smooth by members."),
        ],
        'bands': [{'height': 32, 'surface': TRIM}],
        'notes': "Barticus' members' room: lamplit carved sandstone, a stone bench with the book, the brews' shelf, a lifting block and the weights.",
    },
    'main_drain': {
        'levels': [channel('main_drain', 'x')],
        'walls': [{'wall': 'n', 'panels': [outlet('panel:outlet_main', 1344)]}],
        'notes': "Tan sandstone walls, a channel of slow water, grated outlets from the streets ('Sewer Drain').",
    },
    'warren': {'rough': ROUGH, 'notes': "Where the stalkers breed: a collapsed side vault of the drains."},
    'breeding_vault': {'rough': ROUGH, 'notes': "The warren's back vault: nests of rags."},
    'cistern': {
        'pillars': [{'outline': cave(x, y, x + 192, y + 192, 32), 'surface': CARVED}
                    for x in (5888, 6912) for y in (-896, 128)],
        'levels': [{'id': 'level:cistern_pool', 'outline': cave(6208, -576, 6848, 0, 96), 'floor': -96,
                    'edge': FLAGS2, 'surface': dict(WATER), 'notes': "The cistern's pool between the four pillars."}],
        'walls': [{'wall': 'e', 'panels': [outlet('panel:outlet_cistern', 1344,
                                                   "The overflow's grated mouth high in the east wall ('Sewer Drain').")]}],
        'notes': "A pillared cistern under stepped-fret vaults, the city's old waterworks; its pool between four pillars.",
    },
    'alcoves': {'notes': "A corridor of niches ('Alcove'); one holds a chest."},
    'niche_1': {'walls': [{'wall': 's', 'panels': [{'id': 'panel:alcove_1', 'at': 'centre', 'length': 128, 'bottom': 32,
                                                    'height': 256, 'surface': dict(JAMB_L, fit=True)}]}],
                'notes': "An empty alcove."},
    'niche_2': {'notes': "The alcove with the chest."},
    'niche_3': {'walls': [{'wall': 's', 'panels': [{'id': 'panel:alcove_3', 'at': 'centre', 'length': 128, 'bottom': 32,
                                                    'height': 256, 'surface': dict(JAMB_R, fit=True)}]}],
                'notes': "An empty alcove."},
    'cobra_drain': {
        'levels': [channel('cobra_drain', 'x', width=320)],
        'walls': [{'wall': 's', 'panels': [outlet('panel:outlet_cobra', 640,
                                                   "The warm drain from Venom Pond's side ('Sewer Drain').")]}],
        'notes': "The drain from Venom Pond's side; snakes in the warm water.",
    },
    'collapse': {'rough': ROUGH,
                 'notes': "Where the drain's floor fell into older works: rubble, and a slope down to the long tunnel."},
    'tunnel_head': {'notes': "The foot of the slope: the long tunnel's start, a milestone 'To the desert'."},
    'mantis_gallery': {'rough': ROUGH, 'notes': "Ant diggings cutting across the tunnel, chewed rock."},
    'mantis_nest': {'rough': ROUGH, 'ceiling_points': [[4608, -7936, 192]],
                    'notes': "The queens' chamber; what the ants dragged in (a chest)."},
    'egg_cells': {'rough': ROUGH, 'notes': "Egg cells chewed into the rock off the nest."},
    'drowned': {
        'levels': [{'id': 'level:drowned_water', 'outline': [[1664, -7296], [2560, -7296], [2560, -6528], [1664, -6528]],
                    'floor': U1 - 48, 'edge': FLAGS2, 'surface': dict(WATER),
                    'notes': "Standing water in the vault's sunken floor."}],
        'notes': "A side vault with standing water and an old strongbox; off the nest.",
    },
    'tunnel_east': {'notes': "Long, straight and dry, lamps every so often."},
    'sand_drift': {'notes': "Sand drifting in down the long tunnel from the desert end."},
    'tunnel_west': {'notes': "The long tunnel's west length, the air warmer, sand underfoot."},
    'desert_gate': {
        'walls': [{'wall': 'w', 'panels': [{'id': 'panel:desert_grate', 'at': 'centre', 'length': 384, 'bottom': 0,
                                            'height': 384, 'surface': dict(GRATE, fit=True),
                                            'notes': "The iron grate onto the Desert of Doom, bolted on the desert side."}]}],
        'notes': "The tunnel's end: an iron grate with daylight and sand blowing through, bolted on the desert side (D5).",
    },
}


def room_doc(rid):
    if rid in P:
        name, path, fl, to, h, theme = P[rid]
        return {'id': 'room:' + rid, 'name': name, 'path': path, 'width': PATH_WIDTH, 'smooth': 1, 'floor': fl,
                'slope': {'to': to}, 'ceiling': fl + h, 'theme': theme,
                'notes': "The rubble slope: the broken drain's floor fallen into older works, down to the long tunnel (0 to -640)."}
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
    print('total', tot / 1e6)
