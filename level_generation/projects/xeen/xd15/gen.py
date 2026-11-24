#!/usr/bin/env python3
"""XD-15 The Sphinx: writes the project files of devdocs/xeen/briefs/xd15/L1..L4 (lane A7 phase 4, sub-agent
agent:xeen-a7-xd15). Route after level_generation/projects/xeen/xd08/gen.py and level_generation/projects/xeen/dd06/gen.py.

    python3 level_generation/projects/xeen/xd15/gen.py            all four levels
    python3 level_generation/projects/xeen/xd15/gen.py L4         one level

Rerun after every change here (level_generation/projects/xeen/xd15/cycle.sh); never hand-edit the written files. The playtests are
written by tools/gen_tests.py from the built ids.lock.yml.

Frame: x east, y north, z up. The Sphinx faces south (X6's door between the forelegs faces south): the breast gate's
south wall (y 0) holds the two-faced way out. The body at z 0 runs north from the gate: the paw hall, the two
sarcophagus galleries on the flanks, the belly hall with its two throne doors (crown west, veil east), the haunch vault
and the dungeon stair. The throat stair climbs 1,280 southward from the paw hall's south wall to the head (z 1280) in
front of the body: the neck landing, the two lappets and the riddle chamber behind the face (south), the throne of
legends west of it. The hieroglyph dungeon (z -640) lies north of the haunches, down the dungeon stair. No room stands
over another; one room is one rectangle; walls between rooms are 128 thick.
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / 'devdocs/xeen/briefs/xd15'


class Flow(list):
    pass


class FlowDict(dict):
    pass


yaml.add_representer(Flow, lambda d, v: d.represent_sequence('tag:yaml.org,2002:seq', v, flow_style=True))
yaml.add_representer(FlowDict, lambda d, v: d.represent_mapping('tag:yaml.org,2002:map', v, flow_style=True))


def F(*v):
    return Flow(v)


def S(texture, w, h, **kw):
    d = FlowDict(texture=texture, size=Flow([w, h]))
    d.update(kw)
    return d


def rect(x0, y0, x1, y1):
    return Flow([Flow([x0, y0]), Flow([x1, y0]), Flow([x1, y1]), Flow([x0, y1])])


# ---------------------------------------------------------------------------------------------------------------------
# Numbers
MAP_STATS_ID = 9141
MUSIC = 46                       # source/maps.yml XD-15
SAND, STONE, IRON, MUMMY = 11590, 11581, 11582, 11270
NAMES = {SAND: 'Sand Golem', STONE: 'Stone Golem', IRON: 'Iron Golem', MUMMY: 'Tomb Mummy'}
LEVEL = {SAND: 22, STONE: 26, IRON: 40, MUMMY: 42}
QBITS = {
    'entered': 112180,           # A3's q-c9.entered (X6's door sets it)
    'named': 112181,             # A3's q-c9.done (q-c9.name_right sets it)
    'vault_potions': 118010,     # map: the haunch vault chest's two Might Boosts given (D-39 Q4, D-22's pattern)
}
ITEMS = {'might_boost': 240, 'starburst_book': 421, 'divine_intervention_book': 487,
         'sunstone': 2063, 'sapphire': 2065, 'emerald': 2061, 'amethyst': 2060}
X6_ARRIVAL = (9216, 9728, 1408)  # the way out lands here on X6, facing south

# ---------------------------------------------------------------------------------------------------------------------
# Textures: MM6's Tomb of VARN (pyramid.blv) upper levels (dungeon_families temples names it for XD-15).
BIGA = S('egybiga', 256, 256)          # sandstone blocks, the body
BIGB = S('egybigb', 256, 256)          # the darker blocks, the head
FLORE = S('egyflore', 256, 256)        # sandstone flags
FLORC = S('egyflorc', 128, 128)        # pale flags, head and stairs
FLORA = S('egyflora', 128, 128)        # blue glazed tiles, the throne rooms
SANDF = S('egyflord', 256, 256)        # drifted sand, the dungeon
CEILB = S('egyceilb', 128, 128)        # carved stone ceiling panels
CEILA = S('egyceila', 128, 128)        # inlaid star ceiling, the throne rooms
CEILD = S('egyceild', 128, 128)        # framed ceiling, the head
STRIPES = S('egytrmb', 64, 64)         # the nemes' stripes as a frieze (band)
LOTUS = S('egytrmd', 64, 64)           # lotus frieze, the throne rooms
GLYPHBAND = S('egytrmc', 64, 64)       # small hieroglyphs
BRICK = S('egymeda', 256, 256)         # the throne rooms' brick
GLYPHS = S('egywld', 256, 256)         # carved hieroglyph walls, the dungeon
GOLDGLYPH = S('egywlf', 256, 256)      # gilded hieroglyphs, the library and the legend throne
ROUGH = S('egywalhb', 256, 256)        # rough sandstone, the drop cell
CARVED = S('egywle', 128, 128)         # orange relief, door slabs and sarcophagus sides
GOLD = S('egywlc', 128, 256)           # gold leaf: sarcophagus lids, throne seats
TABLET = 'egytrmc'                     # black hieroglyphs on gold: plaques, clue walls, signs, once per face
SCENE = S('egywlspc', 256, 256, fit=True)  # a painted scene with columns of hieroglyphs: the library's summary
MASK = S('egywlspa', 256, 256, fit=True)      # jackal masks in relief: the Queen's loose panel
NICHE = S('egyspca', 256, 256, fit=True)      # a niche of statues: the vault's grave goods
EYE = S('egyswbof', 32, 32, scale=4)          # an eye: the Sphinx's eyes from inside
SCARAB = S('egyswaon', 32, 32, scale=12)        # the sun disc's top: one scarab over 384
COL_PAW = S('egycol64', 64, 256, scale=2.75)    # striped column, 704 high (the paw hall)
COL_BELLY = S('egycol64', 64, 256, scale=3.25)  # striped column, 832 high (the belly hall)


def plaque(w, h):
    return S(TABLET, 64, 64, fit=True, uneven=True)   # the 64-texel tablet stretched once over the panel


THEMES = [
    dict(id='theme:body', wall=BIGA, floor=FLORE, ceiling=CEILB, reveal=BIGA, door=CARVED,
         notes="The body: the Tomb of VARN's sandstone blocks (egybiga), its flags (egyflore), carved ceiling panels "
               "(egyceilb)."),
    dict(id='theme:throne', wall=BRICK, floor=FLORA, ceiling=CEILA, reveal=BIGA, door=CARVED,
         bands=Flow([FlowDict(height=576, surface=BRICK), FlowDict(height=640, surface=LOTUS)]),
         notes="The throne rooms: fine brick (egymeda) under a lotus frieze (egytrmd), blue glazed tiles (egyflora), "
               "the inlaid star ceiling (egyceila)."),
    dict(id='theme:head', wall=BIGB, floor=FLORC, ceiling=CEILD, reveal=BIGB, door=CARVED,
         notes="The head: the darker blocks (egybigb), pale flags (egyflorc), framed ceilings (egyceild)."),
    dict(id='theme:stair', wall=BIGA, floor=FLORC, ceiling=CEILB, reveal=BIGA, door=CARVED,
         notes="The throat and dungeon stairs: the body's blocks, pale flags on the treads."),
    dict(id='theme:dungeon', wall=GLYPHS, floor=SANDF, ceiling=CEILB, reveal=BIGA, door=CARVED,
         notes="The hieroglyph dungeon: carved hieroglyph walls (egywld), drifted sand underfoot (egyflord)."),
    dict(id='theme:library', wall=GOLDGLYPH, floor=SANDF, ceiling=CEILB, reveal=BIGA, door=CARVED,
         notes="The scribes' library: gilded hieroglyphs (egywlf)."),
    dict(id='theme:cell', wall=ROUGH, floor=SANDF, ceiling=ROUGH, reveal=ROUGH, door=CARVED,
         notes="The drop cell: rough sandstone (egywalhb), a sand heap."),
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms: id -> (name, (x0, y0, x1, y1), floor, ceiling, theme, extra)
ROOMS = {}


def room(rid, name, r, floor, ceiling, theme, **extra):
    ROOMS[rid] = dict(name=name, rect=r, floor=floor, ceiling=ceiling, theme=theme, **extra)


# The body (z 0)
room('breast_gate', 'Breast gate', (-448, 0, 448, 704), 0, 512, 'body')
room('paw_hall', 'Hall of the paws', (-1280, 832, 1280, 2048), 0, 704, 'body')
room('throat_stair', 'Throat stair', (640, -1920, 1024, 704), 0, 512, 'stair',
     slope={'to': 1280, 'toward': 'south', 'steps': 40}, ceiling_slope={'to': 1792, 'toward': 'south'})
room('gallery_w', 'West sarcophagus gallery', (-2176, 832, -1408, 3328), 0, 576, 'body')
room('gallery_e', 'East sarcophagus gallery', (1408, 832, 2176, 3328), 0, 576, 'body')
room('belly_hall', 'The belly hall', (-1280, 2176, 1280, 5120), 0, 832, 'body')
room('king_throne', "King's throne", (-2432, 3712, -1408, 4864), 0, 640, 'throne')
room('queen_throne', "Queen's throne", (1408, 3712, 2432, 4864), 0, 640, 'throne')
room('thieves_throne', "Thieves' throne", (2560, 4032, 3200, 4544), 0, 448, 'throne')
room('haunch_vault', 'Vault of the haunches', (-896, 5248, 896, 6144), 0, 576, 'body')
room('dungeon_stair', 'Dungeon stair', (-192, 6272, 192, 7296), 0, 448, 'stair',
     slope={'to': -640, 'toward': 'north', 'steps': 20}, ceiling_slope={'to': -192, 'toward': 'north'})
# The head (z 1280)
room('neck_landing', 'Neck landing', (448, -2816, 1216, -2048), 1280, 1856, 'head')
room('west_lappet', 'West lappet', (-448, -3328, 320, -2176), 1280, 1792, 'head')
room('east_lappet', 'East lappet', (1344, -3328, 2112, -2176), 1280, 1792, 'head')
room('riddle', 'The riddle chamber', (-448, -4864, 2112, -3456), 1280, 2048, 'head')
room('legend_throne', 'Throne of legends', (-1472, -4608, -576, -3712), 1280, 1920, 'throne')
# The hieroglyph dungeon (z -640)
room('stair_foot', 'Stair foot', (-512, 7424, 512, 8192), -640, -192, 'dungeon')
room('glyph_w', 'West hieroglyph hall', (-2304, 8320, -128, 9088), -640, -192, 'dungeon')
room('glyph_e', 'East hieroglyph hall', (0, 8320, 2176, 9088), -640, -192, 'dungeon')
room('library', "Scribes' library", (-1280, 9216, 1152, 10624), -640, -64, 'library')
room('drop_cell', 'Drop cell', (2304, 8320, 3072, 9088), -640, -128, 'cell')

DISC = (832, -4160)              # the sun disc's middle in the riddle chamber
DISC_HALF = 192
PIT_FLOOR = 1280 - 192           # the shaft under the disc
DROP_LAND = (2688, 8640, -600)   # where a wrong name lands the party (the drop cell's sand heap's foot)


def cx(rid):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return (x0 + x1) // 2


def cy(rid):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return (y0 + y1) // 2


def frieze(height, wall, band, band_h=64):
    return Flow([FlowDict(height=height - band_h, surface=wall), FlowDict(height=height, surface=band)])


BANDS = {
    'paw_hall': frieze(704, BIGA, STRIPES),
    'belly_hall': frieze(832, BIGA, STRIPES),
    'thieves_throne': frieze(448, BRICK, LOTUS),
    'legend_throne': frieze(640, BRICK, LOTUS),
    'riddle': frieze(768, BIGB, GLYPHBAND),
}

# ---------------------------------------------------------------------------------------------------------------------
# Openings: absolute centre on the shared wall; the helper finds the walls and the `along`.


def walls_of(rid):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    o = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [(o[i], o[(i + 1) % 4]) for i in range(4)]


OPEN_AT = {}   # opening id -> (x, y, width, axis) for the dressing checks


def opening(oid, a, b, at, width, height, link=None, **kw):
    best = None
    for i, (p0, p1) in enumerate(walls_of(a)):
        for j, (q0, q1) in enumerate(walls_of(b)):
            if p0[0] == p1[0] and q0[0] == q1[0]:
                ax = 1
            elif p0[1] == p1[1] and q0[1] == q1[1]:
                ax = 0
            else:
                continue
            o = 1 - ax
            gap = abs(p0[o] - q0[o])
            lo = max(min(p0[ax], p1[ax]), min(q0[ax], q1[ax]))
            hi = min(max(p0[ax], p1[ax]), max(q0[ax], q1[ax]))
            if hi - lo <= 0 or gap > 256 or not (lo <= at <= hi):
                continue
            if best is None or gap < best[0]:
                best = (gap, i, j, lo, hi, ax, p0, p1)
    if best is None:
        raise SystemExit(f'no facing walls between {a} and {b} at {at}')
    gap, i, j, lo, hi, ax, p0, p1 = best
    if at - width / 2 < lo or at + width / 2 > hi:
        raise SystemExit(f'opening {oid} ({width} at {at}) does not fit the shared wall {lo}..{hi}')
    forward = (p1[ax] - p0[ax]) > 0
    along = (at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo)
    d = {'id': f'open:{oid}', 'from': f'room:{a}', 'to': f'room:{b}', 'from_wall': i, 'to_wall': j}
    if link:
        d['link'] = link
    if round(along, 4) != 0.5:
        d['along'] = round(along, 4)
    d['width'] = width
    d['height'] = height
    d.update(kw)
    pt = (at, p0[1]) if ax == 0 else (p0[0], at)
    OPEN_AT[oid] = (pt, width, ax, a, b)
    return d


OPENINGS = [
    # the body
    opening('gate_paws', 'breast_gate', 'paw_hall', 0, 512, 448, 'link:gate_paws'),
    opening('paws_throat', 'paw_hall', 'throat_stair', 832, 320, 384, 'link:paws_throat'),
    opening('paws_gw', 'paw_hall', 'gallery_w', 1440, 384, 448, 'link:paws_gw'),
    opening('paws_ge', 'paw_hall', 'gallery_e', 1440, 384, 448, 'link:paws_ge'),
    opening('gw_belly', 'gallery_w', 'belly_hall', 2752, 384, 448, 'link:gw_belly'),
    opening('ge_belly', 'gallery_e', 'belly_hall', 2752, 384, 448, 'link:ge_belly'),
    opening('belly_king', 'belly_hall', 'king_throne', 4288, 384, 384, 'link:belly_king',
            notes="The crown door: two carved leaves (egydrsml, egydrsmr: Horus in the double crown)."),
    opening('belly_queen', 'belly_hall', 'queen_throne', 4288, 192, 384, 'link:belly_queen',
            notes="The veil door: one carved leaf (egydrsmc: veiled women in relief)."),
    opening('queen_thieves', 'queen_throne', 'thieves_throne', 4288, 256, 320, 'link:queen_thieves',
            notes="The loose panel: the mask carved on it (egywlspa); a secret door."),
    opening('belly_haunch', 'belly_hall', 'haunch_vault', 0, 256, 320, 'link:belly_haunch'),
    opening('haunch_dstair', 'haunch_vault', 'dungeon_stair', 0, 320, 384, 'link:haunch_dstair'),
    # body to head
    opening('throat_neck', 'throat_stair', 'neck_landing', 832, 320, 384, 'link:throat_up',
            notes="The head of the throat stair, 1,280 over the paw hall."),
    # the head
    opening('neck_wl', 'neck_landing', 'west_lappet', -2496, 320, 384, 'link:neck_wl'),
    opening('neck_el', 'neck_landing', 'east_lappet', -2496, 320, 384, 'link:neck_el'),
    opening('wl_riddle', 'west_lappet', 'riddle', -64, 384, 448, 'link:wl_riddle'),
    opening('el_riddle', 'east_lappet', 'riddle', 1728, 384, 448, 'link:el_riddle'),
    opening('riddle_legend', 'riddle', 'legend_throne', -4160, 512, 256, 'link:riddle_legend',
            notes="The legend door: two leaves (egydrlgl, egydrlgr: the pharaoh enthroned under the sun)."),
    # body to the dungeon
    opening('dstair_foot', 'dungeon_stair', 'stair_foot', 0, 320, 384, 'link:dstair_down'),
    # the dungeon
    opening('foot_gw', 'stair_foot', 'glyph_w', -320, 320, 384, 'link:foot_gw'),
    opening('gw_ge', 'glyph_w', 'glyph_e', 8704, 384, 384, 'link:gw_ge'),
    opening('gw_library', 'glyph_w', 'library', -704, 256, 320, 'link:gw_library'),
    opening('ge_library', 'glyph_e', 'library', 640, 384, 384, 'link:library_ge'),
    opening('drop_ge', 'drop_cell', 'glyph_e', 8704, 256, 320, 'link:drop_out',
            notes="The drop cell's door: it opens from inside and stays open (D-39)."),
]

# ---------------------------------------------------------------------------------------------------------------------
# Walls: panels (plaques, clue walls, signs, eyes, the mask's frame side)


def panel(pid, offset, length, bottom, height, surface, notes=None):
    d = FlowDict()
    if pid:
        d['id'] = pid
    d.update(offset=offset, length=length, bottom=bottom, height=height, surface=surface)
    if notes:
        d['notes'] = notes
    return d


def woff(rid, wall, coord):
    """Offset along a wall of a rectangle room (walls counter-clockwise from the outline's first point: south runs
    west->east from x0, east south->north from y0, north east->west from x1, west north->south from y1)."""
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return {'south': coord - x0, 'east': coord - y0, 'north': x1 - coord, 'west': y1 - coord}[wall]


def pan(rid, wall, centre, length, bottom, height, surface, pid=None, notes=None):
    return panel(pid, woff(rid, wall, centre) - length // 2 if wall in ('south', 'east') else
                 woff(rid, wall, centre) - length // 2, length, bottom, height, surface, notes)


WALLS = {
    'paw_hall': [{'wall': 'south', 'panels': Flow([
        pan('paw_hall', 'south', 1152, 160, 160, 160, plaque(160, 160), 'panel:sign_up',
            "'Stairs up.' over the throat stair's mouth (aaze0082:13)."),
    ])}],
    'haunch_vault': [
        {'wall': 'north', 'panels': Flow([
            pan('haunch_vault', 'north', 448, 160, 160, 160, plaque(160, 160), 'panel:sign_down',
                "'Stairs down.' beside the dungeon stair (aaze0084:9)."),
        ])},
        {'wall': 'west', 'panels': Flow([
            pan('haunch_vault', 'west', 5696, 320, 64, 320, NICHE, None, "Grave goods: statues in a niche."),
        ])},
        {'wall': 'east', 'panels': Flow([
            pan('haunch_vault', 'east', 5696, 320, 64, 320, NICHE, None, "Grave goods: statues in a niche."),
        ])},
    ],
    'riddle': [
        {'wall': 'north', 'panels': Flow([
            pan('riddle', 'north', 448, 256, 160, 256, plaque(256, 256), 'panel:plaque_1',
                "The first hieroglyph plaque (aaze0082:2)."),
            pan('riddle', 'north', 1216, 256, 160, 256, plaque(256, 256), 'panel:plaque_2',
                "The second hieroglyph plaque (aaze0082:3)."),
        ])},
        {'wall': 'south', 'panels': Flow([
            pan('riddle', 'south', 576, 128, 448, 128, EYE, None, "The west eye: a slit of light from outside."),
            pan('riddle', 'south', 1088, 128, 448, 128, EYE, None, "The east eye."),
        ])},
    ],
    'drop_cell': [{'wall': 'north', 'panels': Flow([
        pan('drop_cell', 'north', 2688, 256, 128, 256, plaque(256, 256), 'panel:clue_1',
            "The first clue (aaze0084:2)."),
    ])}],
    'glyph_w': [{'wall': 'north', 'panels': Flow([
        pan('glyph_w', 'north', -1600, 256, 96, 256, plaque(256, 256), 'panel:clue_2', "The second clue (aaze0084:3)."),
    ])}],
    'glyph_e': [
        {'wall': 'south', 'panels': Flow([
            pan('glyph_e', 'south', 1088, 256, 96, 256, plaque(256, 256), 'panel:clue_3',
                "The third clue (aaze0084:4)."),
        ])},
        {'wall': 'north', 'panels': Flow([
            pan('glyph_e', 'north', 1664, 256, 96, 256, plaque(256, 256), 'panel:clue_4',
                "The fourth clue (aaze0084:5)."),
        ])},
    ],
    'library': [
        {'wall': 'west', 'panels': Flow([
            pan('library', 'west', 10304, 256, 128, 256, plaque(256, 256), 'panel:clue_5',
                "The fifth clue (aaze0084:6)."),
        ])},
        {'wall': 'north', 'panels': Flow([
            pan('library', 'north', -64, 384, 128, 384, SCENE, 'panel:hieroglyphs',
                "The end wall: the scribes' summary, the whole riddle (A3's q-c9.hieroglyphs)."),
        ])},
    ],
}

PILLARS = {
    'paw_hall': Flow([FlowDict(at=F(x, y), size=F(176, 176), surface=COL_PAW)
                      for x in (-640, 640) for y in (1184, 1696)]),
    'belly_hall': Flow([FlowDict(at=F(x, y), size=F(208, 208), surface=COL_BELLY)
                        for x in (-768, 768) for y in (2944, 3712, 4480)]),
}


def block(at, size, rise, surface, top=None, notes=None, pid=None, base=None):
    d = FlowDict()
    if pid:
        d['id'] = pid
    d['at'] = F(*at)
    d['size'] = F(*size)
    d['rise'] = rise
    d['surface'] = surface
    if top:
        d['top_surface'] = top
    if base is not None:
        d['base'] = base
    if notes:
        d['notes'] = notes
    return d


def throne(prefix, wall, w, a, notes, seat_id):
    """A throne on a dais with its back to a wall (`wall` its side, `w` its coordinate, `a` the throne's middle along
    it): the dais (8 clear of the wall, 384 deep), the seat (clicked) and its tall carved back; the seat and the back
    rise from the floor through the dais (XD-08's throne)."""
    d = {'west': 1, 'south': 1, 'east': -1, 'north': -1}[wall]

    def piece(near, far, length, rise, surface, top, note, pid=None):
        mid = w + d * (near + far) / 2
        depth = far - near
        at, size = ((mid, a), (depth, length)) if wall in ('west', 'east') else ((a, mid), (length, depth))
        return block((int(at[0]), int(at[1])), size, rise, surface, top, note, pid=pid)

    return [piece(8, 392, 576, 48, GOLD, FLORA, f"The {prefix} dais."),
            piece(64, 240, 224, 128, CARVED, GOLD, f"The {prefix} seat: {notes}", seat_id),
            piece(16, 64, 288, 448, GOLDGLYPH, GOLD, f"The {prefix} throne's carved back.")]


def sarcophagus(at, horizontal, pid=None, notes="A sarcophagus in its niche."):
    size = (320, 128) if horizontal else (128, 320)
    return block(at, size, 112, CARVED, GOLD, notes, pid=pid)


PLATFORMS = {
    'gallery_w': Flow([
        sarcophagus((-2048, 1280), False, 'platform:sarc_w1', "A sarcophagus (clicked: empty)."),
        sarcophagus((-2048, 2944), False, 'platform:sarc_w2', "A sarcophagus (clicked: empty)."),
    ]),
    'gallery_e': Flow([
        sarcophagus((2048, 1280), False, 'platform:sarc_e1', "A sarcophagus (clicked: empty)."),
        sarcophagus((2048, 2112), False, 'platform:sarc_e2', "A sarcophagus (clicked: empty)."),
        sarcophagus((2048, 2944), False, 'platform:sarc_e3', "The last sarcophagus: a cache of gems in it."),
    ]),
    'king_throne': Flow(throne('King', 'west', -2432, 4288, "the King's throne (q-c9.throne_king)",
                               'platform:throne_king')),
    'queen_throne': Flow(throne('Queen', 'north', 4864, 1920, "the Queen's throne (q-c9.throne_queen)",
                                'platform:throne_queen')),
    'thieves_throne': Flow([
        block((3104, 4288), (128, 192), 112, CARVED, GOLD, "The Thieves' throne: a plain seat in a closet "
              "(q-c9.throne_thieves).", pid='platform:throne_thieves'),
        block((3168, 4288), (32, 224), 384, GOLDGLYPH, GOLD, "Its back."),
    ]),
    'legend_throne': Flow(throne('legend', 'north', -3712, -1024, "the throne of legends, the old names "
                                 "Human, Elf, Gnome, Orc and Dwarf carved in it (q-c9.throne_legend)",
                                 'platform:throne_legend') + [
        block((-1344, -4352), (96, 64), 96, CARVED, S('egyflorb', 128, 128),
              "A lectern: the Book of the Heavens (Starburst).", pid='platform:book_heavens'),
        block((-704, -4352), (96, 64), 96, CARVED, S('egyflorb', 128, 128),
              "A lectern: the Book of the Sun (Divine Intervention).", pid='platform:book_sun'),
    ]),
    'east_lappet': Flow([
        block((2048, -2752), (64, 192), 96, CARVED, GOLD, "The offering niche's ledge: gems.",
              pid='platform:offering'),
    ]),
    'library': Flow([
        block((-1088, 9760), (96, 576), 320, CARVED, CARVED, "Shelves of clay tablets along the west wall."),
        block((960, 9760), (96, 576), 320, CARVED, CARVED, "Shelves of clay tablets along the east wall.",
              pid='platform:tablets'),
        block((-256, 10368), (96, 64), 96, CARVED, S('egyflorb', 128, 128),
              "The scribes' lectern, where the books were: a gem left on it.", pid='platform:lectern'),
    ]),
    'drop_cell': Flow([
        FlowDict(id='platform:sand_heap', outline=Flow([F(2448, 8432), F(2752, 8400), F(2944, 8480), F(2960, 8640),
                                                         F(2816, 8752), F(2512, 8720)]),
                 rise=24, surface=SANDF, top_surface=SANDF,
                 notes="The sand heap under the closed shaft, where the wrong name lands the party."),
    ]),
}

LEVELS = {
    'riddle': Flow([
        FlowDict(id='level:pit', outline=rect(DISC[0] - DISC_HALF, DISC[1] - DISC_HALF, DISC[0] + DISC_HALF,
                                              DISC[1] + DISC_HALF), floor=PIT_FLOOR,
                 notes="The shaft under the sun disc, 192 deep: the disc fills it and sinks into it."),
    ]),
}

STORE = set()
AMBIENT = {'breast_gate': 18, 'paw_hall': 16, 'belly_hall': 14, 'riddle': 12, 'drop_cell': 8, 'throat_stair': 10,
           'dungeon_stair': 10}

ROOM_NOTES = {
    'breast_gate': "Inside the breast between the paws: the arrival (entrance:x6_paws); the two-faced way out in the "
                   "south wall; the paw hall ahead.",
    'paw_hall': "Under the chest: two rows of striped columns, braziers between them, the throat stair's mouth in the "
                "south-east, the galleries west and east.",
    'throat_stair': "A straight stair of 40 steps up the throat, 1,280 to the head.",
    'gallery_w': "Sarcophagi in niches along the west flank; the great sarcophagus in the middle is a chest (Might 40).",
    'gallery_e': "Sarcophagi along the east flank: 'There is nothing in the sarcophagus.'; gems in the last one.",
    'belly_hall': "Under the vaulted back: six striped columns, the stripes' frieze; the crown door west, the veil door "
                  "east (they open when the Sphinx is named); the haunch vault's door north.",
    'king_throne': "The King's throne on its dais against the west wall.",
    'queen_throne': "The Queen's throne against the east wall; the loose panel with the carved mask beside it.",
    'thieves_throne': "A closet behind the loose panel: the Prince of Thieves' throne.",
    'haunch_vault': "Grave goods in niches, the vault's chest; the dungeon stair north.",
    'dungeon_stair': "Twenty steps down to the hieroglyph dungeon.",
    'neck_landing': "The top of the throat stair; passages west and east into the lappets.",
    'west_lappet': "Inside the striped lappet before the west shoulder: a priest's chest.",
    'east_lappet': "The east lappet: an offering niche with gems.",
    'riddle': "Behind the face: the eyes' two bars of light, two plaques, the sun disc over its shaft; two iron "
              "guardians. The legend door west.",
    'legend_throne': "In the nemes' crown: the throne of legends and two lecterns (Starburst, Divine Intervention).",
    'stair_foot': "The foot of the dungeon stair.",
    'glyph_w': "A low hall of hieroglyph walls; the second clue; sand drifted in; the library's door north.",
    'glyph_e': "Two more clue walls; the drop cell's door at its east end; the library open north.",
    'library': "Shelves of clay tablets, the scribes' lectern, a chest; the fifth clue and the summary.",
    'drop_cell': "Where the wrong name lands: a sand heap, the first clue, a door that opens from inside.",
}


def rooms_yml():
    rooms = []
    for rid, r in ROOMS.items():
        d = {'id': f'room:{rid}', 'name': r['name'], 'outline': rect(*r['rect']), 'floor': r['floor']}
        if 'slope' in r:
            d['slope'] = FlowDict(r['slope'])
        d['ceiling'] = r['ceiling']
        if 'ceiling_slope' in r:
            d['ceiling_slope'] = FlowDict(r['ceiling_slope'])
        d['theme'] = f"theme:{r['theme']}"
        if rid in BANDS:
            d['bands'] = BANDS[rid]
        if rid in STORE:
            d['store'] = True
        if rid in WALLS:
            d['walls'] = WALLS[rid]
        if rid in PILLARS:
            d['pillars'] = PILLARS[rid]
        if rid in PLATFORMS:
            d['platforms'] = PLATFORMS[rid]
        if rid in LEVELS:
            d['levels'] = LEVELS[rid]
        d['ambient'] = AMBIENT.get(rid, 12)
        d['notes'] = ROOM_NOTES[rid]
        rooms.append(d)
    return {'format': 0, 'themes': THEMES, 'defaults': FlowDict(theme='theme:body', ambient=12), 'rooms': rooms,
            'openings': OPENINGS,
            'notes': "XD-15 The Sphinx at L4: the body at 0 (breast gate, paw hall, the two sarcophagus galleries, the "
                     "belly hall with the crown and veil doors, the King's, Queen's and Thieves' thrones, the haunch "
                     "vault), the head at 1,280 up the throat stair (neck landing, lappets, the riddle chamber, the "
                     "throne of legends), the hieroglyph dungeon at -640 down the dungeon stair (stair foot, two halls, "
                     "the scribes' library, the drop cell). x east, y north; the Sphinx faces south. Written by "
                     "output/studio_cal/xd15/tools/gen.py."}


# ---------------------------------------------------------------------------------------------------------------------
# objects.yml

# Placed monsters: room -> group, [(row, (x, y), facing)]
PLACED = [
    ('paw_hall', 10, [(SAND, (-960, 1440), 0), (SAND, (960, 1440), 180), (SAND, (-960, 1888), 0),
                      (STONE, (960, 1824), 270)]),
    ('gallery_w', 11, [(MUMMY, (-1792, 1856), 270), (MUMMY, (-1792, 2560), 270), (SAND, (-1664, 1216), 270),
                       (SAND, (-1664, 3072), 270)]),
    ('gallery_e', 12, [(MUMMY, (1792, 1856), 270), (MUMMY, (1792, 2560), 270), (SAND, (1664, 1216), 270),
                       (SAND, (1664, 3072), 270)]),
    ('belly_hall', 13, [(STONE, (-384, 2944), 270), (STONE, (384, 2944), 270), (STONE, (-384, 4096), 270),
                        (STONE, (384, 4096), 270), (STONE, (0, 3520), 270), (IRON, (0, 4736), 270)]),
    ('haunch_vault', 14, [(STONE, (-512, 5504), 270), (STONE, (512, 5504), 270), (STONE, (0, 5824), 270),
                          (IRON, (-512, 5888), 270)]),
    ('neck_landing', 15, [(STONE, (640, -2304), 90), (STONE, (1024, -2304), 90), (STONE, (832, -2496), 90)]),
    ('west_lappet', 16, [(MUMMY, (-64, -2560), 0), (STONE, (-64, -3008), 0)]),
    ('east_lappet', 17, [(STONE, (1728, -2560), 180), (STONE, (1728, -3008), 180)]),
    ('riddle', 18, [(IRON, (DISC[0] - 448, DISC[1]), 90), (IRON, (DISC[0] + 448, DISC[1]), 90)]),
    ('stair_foot', 19, [(SAND, (-256, 7808), 270), (SAND, (256, 7808), 270)]),
    ('glyph_w', 20, [(SAND, (-1856, 8704), 0), (SAND, (-1216, 8512), 0), (SAND, (-1216, 8896), 0),
                     (MUMMY, (-704, 8704), 0)]),
    ('glyph_e', 21, [(SAND, (896, 8704), 180), (SAND, (1408, 8512), 180), (STONE, (1856, 8704), 180)]),
    ('library', 22, [(SAND, (-640, 9600), 270), (SAND, (512, 9600), 270), (STONE, (-640, 10240), 270),
                     (STONE, (512, 10240), 270), (MUMMY, (0, 9984), 270)]),
]

START = (0, 256)


def objects_yml():
    doors = [
        {'id': 'door:king', 'opening': 'open:belly_king', 'kind': 'hinged', 'leaves': 2, 'thickness': 24,
         'pictures': Flow([Flow([S('egydrsml', 128, 256), S('egydrsmr', 128, 256)])]),
         'back_pictures': Flow([Flow([S('egydrsml', 128, 256), S('egydrsmr', 128, 256)])]),
         'edge_surface': S('egywle', 128, 128),
         'notes': "The crown door: two carved leaves, Horus in the double crown (egydrsml/egydrsmr, a pair of wings), "
                  "sealed until the Sphinx is named."},
        {'id': 'door:queen', 'opening': 'open:belly_queen', 'kind': 'slide_up', 'thickness': 24, 'speed': 192,
         'surface': S('egydrsmc', 128, 256, fit=True), 'back_surface': S('egydrsmc', 128, 256, fit=True),
         'notes': "The veil door: one carved leaf of veiled women in relief (egydrsmc), sealed until the Sphinx is "
                  "named; it rises into the wall."},
        {'id': 'door:legend', 'opening': 'open:riddle_legend', 'kind': 'hinged', 'leaves': 2, 'thickness': 24,
         'pictures': Flow([Flow([S('egydrlgl', 256, 256), S('egydrlgr', 256, 256)])]),
         'back_pictures': Flow([Flow([S('egydrlgl', 256, 256), S('egydrlgr', 256, 256)])]),
         'edge_surface': S('egywle', 128, 128),
         'notes': "The legend door into the nemes' crown: the pharaoh enthroned under the sun on two leaves "
                  "(egydrlgl/egydrlgr), sealed until the Sphinx is named."},
        {'id': 'door:panel', 'opening': 'open:queen_thieves', 'kind': 'slide_up', 'secret': True, 'thickness': 24, 'speed': 192,
         'surface': MASK, 'back_surface': S('egymeda', 256, 256, fit=True, uneven=True),
         'notes': "The loose panel with the carved jackal mask (egywlspa): a secret door that slides up on a click."},
        {'id': 'door:haunch', 'opening': 'open:belly_haunch', 'kind': 'slide_up', 'fold': True, 'thickness': 24,
         'surface': CARVED, 'tile': True, 'notes': "A carved stone slab into the haunch vault."},
        {'id': 'door:library', 'opening': 'open:gw_library', 'kind': 'slide_up', 'fold': True, 'thickness': 24,
         'surface': CARVED, 'tile': True, 'notes': "The library's carved slab."},
        {'id': 'door:drop', 'opening': 'open:drop_ge', 'kind': 'slide_up', 'fold': True, 'thickness': 24,
         'surface': CARVED, 'tile': True,
         'notes': "The drop cell's slab: it opens from inside and stays open (D-39)."},
    ]
    movers = [{
        'id': 'mover:disc', 'room': 'room:riddle', 'at': F(*DISC), 'size': F(2 * DISC_HALF - 8, 2 * DISC_HALF - 8),
        'floor_height': PIT_FLOOR, 'bottom': 0, 'height': 200, 'travel': F(0, 0, -176), 'speed': 256,
        'auto_return_seconds': 3, 'surface': S('egywle', 128, 128), 'top_surface': SCARAB,
        'notes': "The sun disc (a scarab on its face) over its shaft, 8 over the floor: stepping on it asks the name; "
                 "a wrong name sinks it 176 into the shaft with the party on it, the party is moved to the drop cell, "
                 "and the disc rises again by itself (D-39 Q5)."}]
    chests = [
        {'id': 'chest:sarcophagus', 'room': 'room:gallery_w', 'at': F(-2048, 2112), 'size': F(160, 384, 128),
         'surface': CARVED, 'top_surface': GOLD, 'treasure_level': 4, 'random_items': 3, 'gold': 1500,
         'notes': "The great sarcophagus in the middle of the west gallery: it opens only for a member of Might 40 "
                  "(D-39 Q4)."},
        {'id': 'chest:vault', 'room': 'room:haunch_vault', 'at': F(384, 6104), 'kind': '7gt002', 'treasure_level': 4, 'random_items': 3, 'gold': 1200,
         'notes': "The vault's chest: its first opening hands over two Might Boosts of power 10 (D-39 Q4, D-22's "
                  "pattern, map qbit vault_potions 118010); no random Might Boost in it."},
        {'id': 'chest:lappet', 'room': 'room:west_lappet', 'at': F(-384, -2752), 'kind': 'ch1', 'treasure_level': 4, 'random_items': 2, 'gold': 900, 'notes': "A priest's chest in the west lappet."},
        {'id': 'chest:library', 'room': 'room:library', 'at': F(960, 10560), 'kind': 'ch1', 'treasure_level': 4, 'random_items': 2, 'gold': 1000, 'notes': "The scribe's chest."},
    ]
    monsters = []
    for rid, group, ms in PLACED:
        for n, (mon, at, facing) in enumerate(ms, 1):
            monsters.append({'id': f'monster:{rid}_{n}', 'room': f'room:{rid}', 'monster': mon, 'at': F(*at),
                             'facing': facing, 'hostile': True, 'group': group})

    decos = []

    def deco(name, rid, d, at, **kw):
        e = {'id': f'deco:{name}', 'room': f'room:{rid}', 'decoration': d, 'at': F(*at)}
        e.update(kw)
        decos.append(e)

    # Wall torches (MM6's pyramid torch 6torch01), set on their wall, clear of the openings.
    for i, (rid, at) in enumerate(TORCHES, 1):
        deco(f'torch_{i:02d}', rid, '6torch01', on_wall(rid, at), height=176)
    # Floor braziers (flambeaux) between the paw hall's columns and in the belly hall
    for i, at in enumerate([(-640, 1440), (640, 1440)], 1):
        deco(f'brazier_paw_{i}', 'paw_hall', 'flamb00', at)
    for i, at in enumerate([(-768, 3328), (768, 3328), (-768, 4096), (768, 4096)], 1):
        deco(f'brazier_belly_{i}', 'belly_hall', 'flamb00', at)
    # Vases and urns
    for i, (rid, at) in enumerate([('breast_gate', (-384, 640)), ('breast_gate', (384, 640)),
                                   ('king_throne', (-1488, 3792)), ('king_throne', (-1488, 4784)),
                                   ('queen_throne', (1488, 3792)), ('queen_throne', (1488, 4784)),
                                   ('legend_throne', (-1408, -3776)), ('legend_throne', (-640, -3776)),
                                   ('haunch_vault', (-832, 5312)), ('haunch_vault', (832, 5312))], 1):
        deco(f'vase_{i:02d}', rid, 'dec97', at)
    # The galleries: bones by the sarcophagi; the vault's grave goods
    deco('bones_w', 'gallery_w', '7dec18', (-2096, 1632))
    deco('bones_e', 'gallery_e', 'dec19', (2096, 2528))
    deco('skull_w', 'gallery_w', '7dec20', (-2096, 2560))
    deco('goods_1', 'haunch_vault', 'bag01', (-832, 6080))
    deco('goods_2', 'haunch_vault', 'bag_A', (-736, 6080))
    deco('goods_3', 'haunch_vault', '7dec46', (832, 6080))
    deco('goods_4', 'haunch_vault', '7dec48', (736, 6080))
    # The dungeon: sand, bones, a scribe's crockery
    deco('dungeon_bones_1', 'glyph_w', 'dec29', (-2240, 8384))
    deco('dungeon_bones_2', 'glyph_e', 'dec29', (2112, 9024))
    deco('dungeon_dirt_1', 'glyph_w', '7dec11', (-1600, 9024))
    deco('dungeon_dirt_2', 'glyph_e', '7dec11', (448, 8384))
    deco('cell_bones', 'drop_cell', '7dec18', (3008, 8384))
    deco('library_bowls', 'library', 'dec32', (-256, 10368), floor_height=-640 + 96)
    deco('library_candle_1', 'library', 'cndlab0', (-1216, 10560))
    deco('library_candle_2', 'library', 'cndlab0', (1088, 10560))
    deco('statue_neck', 'neck_landing', '7dec55', (832, -2752))

    lights = []

    def light(name, rid, at, height, radius, color, **kw):
        d = {'id': f'light:{name}', 'room': f'room:{rid}', 'at': F(*at), 'height': height, 'radius': radius,
             'color': F(*color)}
        d.update(kw)
        lights.append(d)

    warm = (255, 196, 128)
    for rid, r in ROOMS.items():
        if 'slope' in r:
            continue
        x0, y0, x1, y1 = r['rect']
        w, d = x1 - x0, y1 - y0
        pts = [(cx(rid), cy(rid))]
        if max(w, d) > 2000:
            pts = ([(x0 + w // 4, cy(rid)), (x1 - w // 4, cy(rid))] if w >= d else
                   [(cx(rid), y0 + d // 4), (cx(rid), y1 - d // 4)])
        if rid == 'riddle':
            pts = [(cx(rid) - 640, cy(rid) + 320), (cx(rid) + 640, cy(rid) + 320)]
        h = min(r['ceiling'] - r['floor'] - 96, 560)
        col = warm if r['floor'] >= 0 else (210, 170, 120)
        if rid == 'drop_cell':
            col = (170, 150, 120)
        for i, at in enumerate(pts, 1):
            light(f'{rid}_{i}' if len(pts) > 1 else rid, rid, at, h, 1500 if max(w, d) > 1400 else 1000, col)
    # The stairs: two lamps each, over the steps (the light's height is over the floor it stands over)
    for name, at in (('throat_low', (832, 256)), ('throat_mid', (832, -608)), ('throat_high', (832, -1472))):
        light(name, 'throat_stair', at, 320, 900, warm)
    light('dstair', 'dungeon_stair', (0, 6784), 280, 900, (210, 170, 120))
    # The Sphinx's eyes: two bars of light from the slits in the face
    for name, x in (('eye_w', 576), ('eye_e', 1088)):
        light(name, 'riddle', (x, -4800), 512, 900, (255, 236, 190), brightness=31)
    # The legend throne glows a little gold
    light('legend_glow', 'legend_throne', (-1024, -3968), 400, 700, (255, 210, 110))

    sounds = [
        {'id': 'sound:dungeon_hum_w', 'room': 'room:glyph_w', 'at': F(-1216, 8704), 'sound': 'humming',
         'radius': 2400, 'inner_radius': 700, 'volume': 0.45, 'pan': False,
         'notes': "The hieroglyph dungeon's hum (AUDIO.md: the shipped humming as the dungeon bed; a room-filling bed "
                  "heard centred, D-48)."},
        {'id': 'sound:dungeon_hum_lib', 'room': 'room:library', 'at': F(-64, 9920), 'sound': 'humming',
         'radius': 2400, 'inner_radius': 700, 'volume': 0.4, 'pan': False,
         'notes': "The library's hum: the dungeon bed, heard centred (D-48)."},
        {'id': 'sound:braziers', 'room': 'room:belly_hall', 'at': F(0, 3712), 'sound': 'torch loop',
         'radius': 1800, 'inner_radius': 600, 'volume': 0.4, 'notes': "The belly hall's braziers."},
        {'id': 'sound:eyes_wind', 'room': 'room:riddle', 'at': F(832, -4800), 'sound': 'whistling wind',
         'radius': 1800, 'inner_radius': 500, 'volume': 0.3, 'notes': "Desert wind through the eye slits."},
    ]

    exits = [
        {'id': 'exit:gate_w', 'room': 'room:breast_gate', 'at': F(-128, 0), 'size': F(256, 320),
         'surface': S('7solid01', 128, 256, fit=True, uneven=True), 'to': 'exit:x6_paws',
         'notes': "The west leaf of the door between the paws (X6's two leaves), from inside."},
        {'id': 'exit:gate_e', 'room': 'room:breast_gate', 'at': F(128, 0), 'size': F(256, 320),
         'surface': S('7solid01', 128, 256, fit=True, uneven=True), 'to': 'exit:x6_paws',
         'notes': "The east leaf, from inside: the same way out."},
    ]

    plates = []

    return {'format': 0,
            'start': {'room': 'room:breast_gate', 'at': F(*START), 'facing': 'n',
                      'notes': "In the breast gate about 256 inside the leaves, facing north into the paw hall."},
            'arrivals': [FlowDict(entrance='entrance:x6_paws', room='room:breast_gate', at=F(*START), facing='n',
                                  notes="In the breast gate about 256 inside the leaves, facing north (X6's door "
                                        "between the paws arrives here).")],
            'doors': doors, 'movers': movers, 'plates': plates, 'sounds': sounds, 'lights': lights,
            'chests': chests, 'monsters': monsters, 'decorations': decos, 'exits': exits, 'relations': []}


def on_wall(rid, at, inset=12):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    x, y = at
    side = min((x - x0, 'w'), (x1 - x, 'e'), (y - y0, 's'), (y1 - y, 'n'))[1]
    return {'w': (x0 + inset, y), 'e': (x1 - inset, y), 's': (x, y0 + inset), 'n': (x, y1 - inset)}[side]


# Torches: (room, a point near the wall); checked against the openings below.
TORCHES = [
    ('breast_gate', (-448, 384)), ('breast_gate', (448, 384)),
    ('paw_hall', (-1280, 1024)), ('paw_hall', (1280, 1024)), ('paw_hall', (-1280, 1856)), ('paw_hall', (1280, 1856)),
    ('paw_hall', (-640, 2048)), ('paw_hall', (640, 2048)),
    ('gallery_w', (-1408, 1024)), ('gallery_w', (-1408, 2240)), ('gallery_w', (-1792, 3328)),
    ('gallery_e', (1408, 1024)), ('gallery_e', (1408, 2240)), ('gallery_e', (1792, 3328)),
    ('belly_hall', (-1280, 3520)), ('belly_hall', (1280, 3520)), ('belly_hall', (-1280, 4864)),
    ('belly_hall', (1280, 4864)), ('belly_hall', (-768, 5120)), ('belly_hall', (768, 5120)),
    ('belly_hall', (-768, 2176)), ('belly_hall', (768, 2176)),
    ('king_throne', (-1920, 3712)), ('king_throne', (-1920, 4864)),
    ('queen_throne', (1920, 3712)), ('queen_throne', (1920, 4864)),
    ('thieves_throne', (2880, 4544)),
    ('haunch_vault', (-512, 6144)), ('haunch_vault', (512, 5248)), ('haunch_vault', (-512, 5248)),
    ('neck_landing', (640, -2816)), ('neck_landing', (1024, -2816)),
    ('west_lappet', (-448, -2560)), ('east_lappet', (2112, -3008)),
    ('riddle', (-448, -3712)), ('riddle', (2112, -3712)), ('riddle', (-448, -4608)), ('riddle', (2112, -4608)),
    ('legend_throne', (-1472, -4160)), ('legend_throne', (-1024, -4608)),
    ('stair_foot', (-512, 7808)), ('stair_foot', (512, 7808)),
    ('glyph_w', (-2304, 8704)), ('glyph_w', (-1216, 8320)),
    ('glyph_e', (192, 9088)), ('glyph_e', (2176, 8448)),
    ('library', (1152, 10368)), ('library', (-768, 10624)), ('library', (640, 10624)),
    ('drop_cell', (3072, 8704)),
]


def check_torches():
    for rid, at in TORCHES:
        p = on_wall(rid, at)
        for oid, (pt, width, ax, a, b) in OPEN_AT.items():
            if rid not in (a, b):
                continue
            dx, dy = abs(p[0] - pt[0]), abs(p[1] - pt[1])
            along, across = (dx, dy) if ax == 0 else (dy, dx)
            if across < 200 and along < width / 2 + 96:
                raise SystemExit(f'torch in {rid} at {p} too near opening {oid}')


# ---------------------------------------------------------------------------------------------------------------------
# wiring.yml


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def sound_at(x, y, z):
    return {'lua': f'evt.PlaySoundName("xeen_sphinx_stir", {x}, {y}, {z})'}


CLUES = [
    ('clue_1', "The message reads: My first is in giant but not in defiant.", "aaze0084:2"),
    ('clue_2', "The message reads: My second is in mole but not in mule.", "aaze0084:3"),
    ('clue_3', "The message reads: My third is in lich but not in stitch.", "aaze0084:4"),
    ('clue_4', "The message reads: My fourth is in guard but not in Girard.", "aaze0084:5"),
    ('clue_5', "The message reads: My fifth is in XEEN but not in Queen.", "aaze0084:6"),
]
THRONE_DOORS = ['door:king', 'door:queen', 'door:legend']


def wiring_yml():
    ev = []

    def e(**kw):
        ev.append(kw)

    e(id='evt:arrive', preset='text', trigger='timer', every=1, once=True, seconds=6,
      text="Cool air, and the smell of old stone. Somewhere above, something very large breathes once and is still.",
      notes="Say where the party is (a one-shot timer: the party arrives standing in the breast gate).")
    for side in ('w', 'e'):
        e(id=f'evt:exit_{side}', preset='exit', source=f'exit:gate_{side}', title='Leave the Sphinx',
          notes="Out to X6 between the paws (installed; A5's point (9216, 9728, 1408) facing south): the game's own "
                "leave window (D-24); 'Leave the Sphinx?' (aaze0082:12) is its meaning.")
    # Doors: the three plain doors are sliding stone slabs (egywle), as MM6's pyramid has them; titled "Stone slab"
    # (the orchestrator, 2026-11-22: they stay slabs).
    e(id='evt:door_haunch', preset='door', source='door:haunch', title='Stone slab')
    e(id='evt:door_library', preset='door', source='door:library', title='Stone slab')
    e(id='evt:door_drop', preset='door', source='door:drop', side='room:drop_cell', title='Stone slab', action='open',
      text="The slab grinds up. On this side there is a handle; on the other, none.",
      notes="D-39: the drop cell's door opens from inside and stays open.")
    e(id='evt:door_drop_shut', preset='text', source='door:drop', side='room:glyph_e', title='Stone slab',
      text="A carved slab with no handle on this side. It does not move.",
      notes="From the east hall the slab does not open (it is opened from the drop cell).")
    for did, carving in (('king', 'a crown'), ('queen', 'a veil'), ('legend', 'a sun over a throne')):
        e(id=f'evt:door_{did}', preset='door', source=f'door:{did}', action='open',
          title={'king': 'Crown door', 'queen': 'Veil door', 'legend': 'Door of legends'}[did],
          condition={'qbit': 'named'},
          locked_text=f"A sealed door carved with {carving}. It does not move for you.",
          notes="Sealed until the Sphinx is named (q-c9.done); opened by the name, and on every later load.")
    e(id='evt:panel', preset='door', source='door:panel', title='Loose panel', action='open',
      text="The panel with the carved mask gives under your hand and slides up. Behind it, a closet and a throne.",
      notes="link:queen_thieves: the secret way to the Thieves' throne (D-39: the mask is carved on the panel).")
    e(id='evt:named_load', preset='switch', trigger='load', condition={'qbit': 'named'}, opens=THRONE_DOORS,
      notes="The throne doors stay open on every later load once the Sphinx is named (after a refill too).")
    # The riddle
    e(id='evt:riddle_voice', preset='script', trigger='step', source='room:riddle', once=True,
      condition={'not': {'qbit': 'named'}}, effects=[hook('q-c9.riddle')],
      notes="Entering the riddle chamber the first time: A3's q-c9.riddle (the plaques' words and the voice).")
    disc = (DISC[0], DISC[1], 1300)
    e(id='evt:disc', preset='script', trigger='step', source='mover:disc',
      condition={'all': [{'not': {'qbit': 'named'}}, {'map_var': {'name': 'drop', 'equals': 0}}]},
      question={'ask': "What is my name?", 'answers': ['golux'],
                'wrong_effects': [sound_at(*disc),
                                  {'damage': {'amount': 30, 'kind': 'physical', 'who': 'all'}},
                                  {'set': {'var': {'map_var': 'drop'}, 'value': 1}}]},
      opens=THRONE_DOORS,
      effects=[sound_at(*disc), {'shake': {'strength': 1, 'seconds': 2}}, hook('q-c9.name_right')],
      else_effects=[{'lua': 'if IsQBitSet(QBit(112181)) then XeenQuests.hook("q-c9.name_right") end'}],
      notes="state:riddle and state:named (aaze0082:4-6): the sun disc asks on every step until named. GOLUX "
            "(any case): xeen_sphinx_stir, the stone shakes, A3's q-c9.name_right (done 112181, award 419, 6,000), the "
            "crown, veil and legend doors open. Anything else: A3's q-c9.name_wrong, the Sphinx stirs, 30 damage to "
            "each member (D-39 Q5: about 10 % of a level-31 knight's HP, 15-20 % of a sorcerer's, never lethal to a "
            "healthy party), drop = 1: the disc sinks into its shaft with the party on it, then the party is "
            "moved to the drop cell's sand heap (evt:drop_sink, evt:drop_move). Once named: \"Golux. Yes. Still me.\" (the hook's else text). The question asks only while drop is 0 (the "
            "wrong name's ride on the disc must not ask again); the else branch calls the hook only once named "
            "(q-c9.done 112181).")
    # The wrong name's fall (D-39 Q5's order): drop 1 → the disc sinks with the party on it (evt:drop_sink), 2 → 3
    # (evt:drop_ride), 3 → the party is moved to the drop cell's sand heap (evt:drop_move), 4 → the landing's words.
    # The game runs the timers in event-number order (sink 45, move 47, ride 48), so the ride step runs in the sink's
    # own tick and the fall comes one tick (1 s) after the sink began: the party rides the disc down (0.7 s) first.
    e(id='evt:drop_landing', preset='script', trigger='step', source='platform:sand_heap',
      condition={'map_var': {'name': 'drop', 'equals': 4}},
      effects=[{'set': {'var': {'map_var': 'drop'}, 'value': 0}}, hook('q-c9.name_wrong')],
      notes="The party lands on the drop cell's sand heap after a wrong name: A3's q-c9.name_wrong here.")
    e(id='evt:drop_move', preset='script', trigger='timer', every=1,
      condition={'map_var': {'name': 'drop', 'equals': 3}},
      effects=[{'set': {'var': {'map_var': 'drop'}, 'value': 4}},
               {'teleport': {'to': F(*DROP_LAND), 'direction': 180}}],
      notes="A second after the disc began to sink with the party on it, the party falls to the drop cell's sand "
            "heap (an in-map move from a timer applies since merge point 18).")
    e(id='evt:drop_ride', preset='script', trigger='timer', every=1,
      condition={'map_var': {'name': 'drop', 'equals': 2}},
      effects=[{'set': {'var': {'map_var': 'drop'}, 'value': 3}}],
      notes="The step between the sink and the fall: it runs in the sink's own tick (timers run by event number), so "
            "the fall (evt:drop_move) comes one tick after the sink.")
    e(id='evt:drop_sink', preset='script', trigger='timer', every=1,
      condition={'map_var': {'name': 'drop', 'equals': 1}}, opens=['mover:disc'],
      effects=[{'set': {'var': {'map_var': 'drop'}, 'value': 2}},
               {'teleport': {'to': F(DISC[0], DISC[1], 1288), 'direction': 270}}],
      notes="The wrong name's floor: the party is set on the disc's middle (the question comes as soon as its edge is "
            "on the disc), and the disc sinks 176 into its shaft with the party on it; it rises again by itself 3 s "
            "later (its auto_return_seconds), after the party has fallen.")
    e(id='evt:plaque_1', preset='text', source='panel:plaque_1', title='Plaque', window=True,
      text="Hieroglyphics. The message reads: You're looking for my name, it's five letters long.",
      notes="aaze0082:1-2.")
    e(id='evt:plaque_2', preset='text', source='panel:plaque_2', title='Plaque', window=True,
      text="Hieroglyphics. The message reads: I think you'll like my name. Try not to get it wrong.",
      notes="aaze0082:1, :3.")
    # The thrones
    for t, title in (('king', "King's throne"), ('queen', "Queen's throne"), ('thieves', "Thieves' throne"),
                     ('legend', 'Throne of legends')):
        e(id=f'evt:throne_{t}', preset='script', source=f'platform:throne_{t}', title=title,
          effects=[hook(f'q-c9.throne_{t}')],
          notes=f"A3's q-c9.throne_{t}: +2 once per character by its player bit (D-39 Q1); aaze0082:8-10, "
                "aaze0083:0-4.")
    # The legend throne's lecterns (D-39 Q3)
    e(id='evt:book_heavens', preset='script', source='platform:book_heavens', title='Book of the Heavens',
      condition={'not': {'map_var': 'book_heavens'}},
      effects=[{'set': {'var': {'map_var': 'book_heavens'}, 'value': 1}}, {'give_item': ITEMS['starburst_book']},
               {'text': "Book of the Heavens: a spellbook of Air magic, Starburst. You take it."}],
      else_effects=[{'text': "The lectern is bare."}],
      notes="aaze0083:15, :6: the Starburst spellbook (Air, D-39), engine 421, once.")
    e(id='evt:book_sun', preset='script', source='platform:book_sun', title='Book of the Sun',
      condition={'not': {'map_var': 'book_sun'}},
      effects=[{'set': {'var': {'map_var': 'book_sun'}, 'value': 1}}, {'give_item': ITEMS['divine_intervention_book']},
               {'text': "Book of the Sun: a spellbook of Light magic, Divine Intervention. You take it."}],
      else_effects=[{'text': "The lectern is bare."}],
      notes="aaze0083:16, :5: the Divine Intervention spellbook (Light), engine 487, once.")
    # Clues and the summary
    for cid, text, ref in CLUES:
        e(id=f'evt:{cid}', preset='text', source=f'panel:{cid}', title='Hieroglyphs', window=True,
          text=f"Hieroglyphs. {text}", notes=f"{ref}: one clue per wall (D-39 Q2).")
    e(id='evt:hieroglyphs', preset='script', source='panel:hieroglyphs', title='Hieroglyphs',
      effects=[hook('q-c9.hieroglyphs')],
      notes="A3's q-c9.hieroglyphs: the whole riddle on the library's end wall, the scribes' summary (D-39 Q2).")
    e(id='evt:sign_up', preset='text', source='panel:sign_up', title='Sign', window=False, text="Stairs up.",
      notes="aaze0082:13 (the source's question dropped: the stairs are walked).")
    e(id='evt:sign_down', preset='text', source='panel:sign_down', title='Sign', window=False, text="Stairs down.",
      notes="aaze0084:9.")
    # Sarcophagi
    for s in ('w1', 'w2', 'e1', 'e2'):
        e(id=f'evt:sarc_{s}', preset='text', source=f'platform:sarc_{s}', title='Sarcophagus',
          text="There is nothing in the sarcophagus.", notes="aaze0082:7, :15.")
    e(id='evt:sarc_e3', preset='script', source='platform:sarc_e3', title='Sarcophagus',
      condition={'not': {'map_var': 'gems_gallery'}},
      effects=[{'set': {'var': {'map_var': 'gems_gallery'}, 'value': 1}}, {'give_item': ITEMS['amethyst']},
               {'text': "Gems! Somebody hid an amethyst under the wrappings."}],
      else_effects=[{'text': "There is nothing in the sarcophagus."}],
      notes="The east gallery's cache (aaze0084:12 'Gems'), once.")
    e(id='evt:chest_sarcophagus', preset='chest', source='chest:sarcophagus', title='Sarcophagus',
      condition={'stat': {'name': 'ActualMight', 'at_least': 40}},
      else_effects=[{'message': "You aren't strong enough to open the sarcophagus."}],
      notes="D-39 Q4 (aaze0082:11): Might 40 on the clicking member, potions and spells counting (ActualMight).")
    vp = QBITS['vault_potions']
    e(id='evt:chest_vault', preset='chest', source='chest:vault', title='Chest',
      effects=[{'lua': f'if not IsQBitSet(QBit({vp})) then SetQBit(QBit({vp})) '
                       'evt.SetHeldItem(240, {bonus = 10}) evt.SetHeldItem(240, {bonus = 10}) '
                       'evt.StatusText("Two flasks of red draught lie on top of the grave goods.") end'}],
      notes=f"D-39 Q4, D-22's pattern: two Might Boosts of a fixed power 10 once per game on the first opening (map "
            f"qbit vault_potions {vp}); the chest holds no random Might Boost.")
    e(id='evt:chest_lappet', preset='chest', source='chest:lappet', title='Chest')
    e(id='evt:chest_library', preset='chest', source='chest:library', title='Chest')
    # Gem finds
    e(id='evt:offering', preset='script', source='platform:offering', title='Gems',
      condition={'not': {'map_var': 'gems_lappet'}},
      effects=[{'set': {'var': {'map_var': 'gems_lappet'}, 'value': 1}}, {'give_item': ITEMS['emerald']},
               {'text': "Gems: an emerald among the offerings."}],
      else_effects=[{'text': "An empty offering niche."}], notes="aaze0083:14 'Gems', once.")
    e(id='evt:lectern', preset='script', source='platform:lectern', title='Gems',
      condition={'not': {'map_var': 'gems_lectern'}},
      effects=[{'set': {'var': {'map_var': 'gems_lectern'}, 'value': 1}}, {'give_item': ITEMS['sunstone']},
               {'text': "Gems: a sunstone on the scribes' lectern, where a book once lay."}],
      else_effects=[{'text': "The scribes' lectern is bare."}],
      notes="D-39 Q3: one of the library's two fixed T4 gem finds (for the dropped Book of Teleport).")
    e(id='evt:tablets', preset='script', source='platform:tablets', title='Clay tablets',
      condition={'not': {'map_var': 'gems_tablets'}},
      effects=[{'set': {'var': {'map_var': 'gems_tablets'}, 'value': 1}}, {'give_item': ITEMS['sapphire']},
               {'text': "Gems: a sapphire tucked behind the tablets."}],
      else_effects=[{'text': "Clay tablets, row on row. None of them is about you."}],
      notes="D-39 Q3: the library's second fixed T4 gem find (for the dropped Book of Alchemy).")
    ev.sort(key=lambda x: x['id'])
    return {'format': 0,
            'variables': ['drop', 'book_heavens', 'book_sun', 'gems_gallery', 'gems_lappet', 'gems_lectern',
                          'gems_tablets'],
            'events': ev}


# ---------------------------------------------------------------------------------------------------------------------
# project.yml


def project_yml(level):
    return {
        'format': 0, 'id': 'xeen_xd15', 'name': 'The Sphinx', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'XD-15', 'units': FlowDict(plan_grid=512),
        'extent': FlowDict(footprint_cells=F(12, 31), climbs='n'),
        'map_stats': {
            'id': MAP_STATS_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 4,
            'trap_dice': 4, 'perception_difficulty': 8, 'refill_days': 672, 'music': MUSIC, 'environment': 'stone',
            'lock_difficulty': 8,
            'slots': [
                FlowDict(monster='Xeen Elemental Golem', tier=0, per_marker=F(2, 3), weight=70),
                FlowDict(monster='Xeen Mummy', tier=0, per_marker=F(1, 2), weight=30),
            ],
        },
        'neighbours': [{
            'id': 'exit:x6_paws', 'to': 'xeen_x6.odm', 'kind': 'door', 'arrival': F(*X6_ARRIVAL),
            'arrival_hint': "On X6 between the paws' tips of the Northern Sphinx, in front of its door "
                            "(thing:northern_sphinx at (9216, 10240, 1408)), facing away from it (south).",
            'direction': 270,
            'notes': "X6 installed (A5). The way out lands at (9216, 9728, 1408) facing south, clear of the obelisks' "
                     "hoard mound by the east foreleg. X6's door (q-c9.door, Arie's amulet 12317) names this map's "
                     "arrival entrance:x6_paws: in the breast gate (0, 256, 0) facing north."}],
        'qbits': dict(sorted(QBITS.items())),
        'items': dict(ITEMS),
        'notes': f"Xeen design brief, level {level}: XD-15 The Sphinx, on X6 (Desert of the Sphinx), Act IV, class M "
                 "(MU-6 graph devdocs/xeen/mockups/act4_graphs/xd15.graph.yml, decider D-39 in "
                 "mockups/act4_a7_decisions.md). Q-C9: the riddle in the head (GOLUX: q-c9.name_right; anything else "
                 "the drop to the hieroglyph dungeon), the four thrones (+2 once per character, A3's hooks). "
                 "Monsters, all placed and hostile in groups 10-22 by room: 16 Sand Golem 11590 (22), 18 Stone Golem "
                 "11581 (26), 4 Iron Golem 11582 (40), 7 Tomb Mummy 11270 (42): 45. Rest encounters 10 % from the "
                 "map's own hostile rows: slot 1 Xeen Elemental Golem tier 0 (Sand Golem only), slot 2 Xeen Mummy "
                 "tier 0 (Tomb Mummy only). Map card 9141, music 46, treasure 4. Map qbits 118010-118019: "
                 "vault_potions 118010. A3's bits named: entered 112180, named (q-c9.done) 112181. Items: Might "
                 "Boost 240, the Starburst (421) and Divine Intervention (487) spellbooks, fixed gems 2060, 2061, "
                 "2063, 2065. The way out to X6 (installed) is live.",
    }


# ---------------------------------------------------------------------------------------------------------------------
# plan.yml

PLAN_SPACES = [
    ('breast_gate', 'room', 'S', "The arrival (entrance:x6_paws): inside the breast between the paws, the two leaves "
                                 "behind. Quiet (D-11.3).", None),
    ('paw_hall', 'room', 'M', "Under the chest: two rows of striped columns, braziers between them; the throat "
                              "stair's mouth; the galleries west and east.", None),
    ('throat_stair', 'corridor', 'S', "A straight stair in the throat up to the head ('Stairs up.' on a sign).",
     None),
    ('gallery_w', 'corridor', 'M', "Sarcophagi in niches, their sleepers up and about; the great sarcophagus is the "
                                   "chest: 'You aren't strong enough to open the sarcophagus.' below Might 40.", 4),
    ('gallery_e', 'corridor', 'M', "The same niches: 'There is nothing in the sarcophagus.'; gems in the last one.",
     None),
    ('belly_hall', 'room', 'L', "A long hall of striped columns; the crown door and the veil door, sealed until the "
                                "Sphinx is named.", None),
    ('king_throne', 'room', 'M', "The King's throne on a dais (q-c9.throne_king: +2 Might once per character).",
     None),
    ('queen_throne', 'room', 'M', "The Queen's throne (q-c9.throne_queen: +2 Personality); the loose panel with the "
                                  "carved mask.", None),
    ('thieves_throne', 'room', 'S', "The Prince of Thieves' throne in a closet (q-c9.throne_thieves: +2 Accuracy; "
                                    "player bit 11302).", None),
    ('haunch_vault', 'room', 'M', "Grave goods in niches and the vault's chest (two Might Boosts on its first "
                                  "opening); the dungeon stair beside it.", 4),
    ('dungeon_stair', 'corridor', 'S', "Steps down into the hieroglyph dungeon ('Stairs down.' on a sign): the "
                                       "dungeon is open without the drop.", None),
    ('neck_landing', 'room', 'S', "The top of the throat stair; passages into the lappets.", None),
    ('west_lappet', 'room', 'S', "Inside the striped lappet before the west shoulder: a priest's chest.", 4),
    ('east_lappet', 'room', 'S', "The east lappet: an offering niche with gems.", None),
    ('riddle', 'room', 'M', "Behind the face: two bars of light from the eyes, two plaques, the sun disc that asks "
                            "'What is my name?' and sinks on a wrong answer; two iron guardians.", None),
    ('legend_throne', 'room', 'M', "The throne of legends (+2 Endurance) and two lecterns: the Book of the Heavens "
                                   "(Starburst, Air) and the Book of the Sun (Divine Intervention, Light).", None),
    ('stair_foot', 'room', 'S', "The foot of the dungeon stair.", None),
    ('glyph_w', 'corridor', 'M', "A low hall of hieroglyph walls, the second clue; sand drifted in.", None),
    ('glyph_e', 'corridor', 'M', "Two more clue walls; the drop cell's door at its end.", None),
    ('library', 'room', 'M', "Shelves of clay tablets, the scribes' lectern (two gem finds), a chest; the fifth clue "
                             "and the whole riddle on the end wall.", 4),
    ('drop_cell', 'room', 'S', "Where the wrong name lands the party (fall damage): a sand heap, the first clue, a "
                               "door that opens from inside and stays open.", None),
]


def plan_yml(level):
    pop = {}
    for rid, group, ms in PLACED:
        for mon, _, _ in ms:
            pop.setdefault(rid, {}).setdefault(mon, 0)
            pop[rid][mon] += 1
    spaces = []
    for sid, kind, size, purpose, chest in PLAN_SPACES:
        r = ROOMS[sid]
        x0, y0, x1, y1 = r['rect']
        s = {'id': f'room:{sid}', 'name': r['name'], 'kind': kind, 'size': size, 'extent': F(x1 - x0, y1 - y0)}
        s['floor'] = r['floor'] if 'slope' not in r else F(min(r['floor'], r['slope']['to']),
                                                            max(r['floor'], r['slope']['to']))
        s['purpose'] = purpose
        if sid in pop:
            s['population'] = [{'actor': m, 'groups': 1, 'levels': F(LEVEL[m], LEVEL[m]),
                                'notes': f"{n} placed {NAMES[m]}{'s' if n > 1 else ''}."} for m, n in pop[sid].items()]
        else:
            s['empty'] = True
        if chest:
            s['treasure'] = [FlowDict(kind='chest', count=1, tier=chest)]
        spaces.append(s)

    def L(lid, a, b, kind, **kw):
        return {'id': f'link:{lid}', 'from': f'room:{a}', 'to': f'room:{b}', 'kind': kind, **kw}

    named = {'qbit': 112181}
    links = [
        L('gate_paws', 'breast_gate', 'paw_hall', 'open'),
        L('paws_throat', 'paw_hall', 'throat_stair', 'open'),
        L('paws_gw', 'paw_hall', 'gallery_w', 'open'),
        L('paws_ge', 'paw_hall', 'gallery_e', 'open'),
        L('gw_belly', 'gallery_w', 'belly_hall', 'open'),
        L('ge_belly', 'gallery_e', 'belly_hall', 'open'),
        L('belly_king', 'belly_hall', 'king_throne', 'double_door', condition=named,
          notes="The crown door: opens when the Sphinx is named (q-c9.done)."),
        L('belly_queen', 'belly_hall', 'queen_throne', 'door', condition=named,
          notes="The veil door: opens when the Sphinx is named."),
        L('queen_thieves', 'queen_throne', 'thieves_throne', 'secret_door',
          notes="The loose panel with the carved mask."),
        L('belly_haunch', 'belly_hall', 'haunch_vault', 'door'),
        L('haunch_dstair', 'haunch_vault', 'dungeon_stair', 'open'),
        L('throat_up', 'throat_stair', 'neck_landing', 'stairs', rise=1280),
        L('neck_wl', 'neck_landing', 'west_lappet', 'open'),
        L('neck_el', 'neck_landing', 'east_lappet', 'open'),
        L('wl_riddle', 'west_lappet', 'riddle', 'open'),
        L('el_riddle', 'east_lappet', 'riddle', 'open'),
        L('riddle_legend', 'riddle', 'legend_throne', 'double_door', condition=named,
          notes="The legend door: opens with the name."),
        L('riddle_drop', 'riddle', 'drop_cell', 'drop', one_way=True,
          notes="A wrong name: the sun disc sinks and the party lands in the drop cell (moved inside the map, the "
                "event's damage)."),
        L('dstair_down', 'dungeon_stair', 'stair_foot', 'stairs', rise=-640),
        L('foot_gw', 'stair_foot', 'glyph_w', 'open'),
        L('gw_ge', 'glyph_w', 'glyph_e', 'open'),
        L('gw_library', 'glyph_w', 'library', 'door'),
        L('library_ge', 'library', 'glyph_e', 'open'),
        L('drop_out', 'drop_cell', 'glyph_e', 'door', opens_from='room:drop_cell',
          notes="Opens from inside and stays open (D-39)."),
    ]
    plan = {
        'format': 0, 'level': min(level, 'L3'),
        'pitch': "The Northern Sphinx from inside: the breast between the paws, a hall of striped columns under its "
                 "chest, sarcophagus galleries along its flanks, the belly hall where two carved throne doors wait for "
                 "the Sphinx's name, the vault in its haunches. Up the throat, the head: two lappets and, behind the "
                 "face, the riddle chamber, lit by the eyes, where a sun disc in the floor asks 'What is my name?'. "
                 "GOLUX opens the thrones; anything else drops the party into the hieroglyph dungeon below, whose "
                 "walls spell the name and whose stair climbs back to the body.",
        'purpose': "Q-C9 The Sphinx (Act IV, party 31-34): the name (q-c9.riddle, name_right, name_wrong), the "
                   "hieroglyph clues (q-c9.hieroglyphs), the four thrones (+2 once per character), the Starburst and "
                   "Divine Intervention spellbooks. 45 monsters at 22-42 (Sand, Stone and Iron Golems, Tomb Mummies), "
                   "treasure 4.",
        'mood': "Warm sandstone lit by torches and braziers; gold and blue in the throne rooms; two bright bars of "
                "desert light behind the face; carved orange hieroglyphs and drifted sand below.",
        'datum': 'arrival',
        'spaces': spaces,
        'links': links,
        'loops': [
            {'id': 'loop:flanks', 'spaces': [f'room:{x}' for x in ('paw_hall', 'gallery_w', 'belly_hall',
                                                                   'gallery_e')],
             'notes': "Round the body by the two sarcophagus galleries."},
            {'id': 'loop:head', 'spaces': [f'room:{x}' for x in ('neck_landing', 'west_lappet', 'riddle',
                                                                 'east_lappet')],
             'notes': "Round the head through both lappets."},
            {'id': 'loop:glyphs', 'spaces': [f'room:{x}' for x in ('glyph_w', 'library', 'glyph_e')],
             'notes': "Round the dungeon's halls through the library."},
            {'id': 'loop:drop', 'spaces': [f'room:{x}' for x in ('riddle', 'drop_cell', 'glyph_e', 'glyph_w',
                                                                 'stair_foot', 'dungeon_stair', 'haunch_vault',
                                                                 'belly_hall', 'gallery_w', 'paw_hall',
                                                                 'throat_stair', 'neck_landing', 'west_lappet')],
             'notes': "The wrong name's way: down by the floor, up by the dungeon stair, back to the head."},
        ],
        'entrances': [
            {'id': 'entrance:x6_paws', 'space': 'room:breast_gate', 'kind': 'both', 'neighbour': 'exit:x6_paws',
             'facing': 'n',
             'how': "From X6's door between the Northern Sphinx's paws (q-c9.door, Arie's amulet): in the breast gate "
                    "about 256 inside the leaves, facing north; the same leaves lead back out (the exit preset)."},
        ],
        'critical_path': [f'room:{x}' for x in ('breast_gate', 'paw_hall', 'throat_stair', 'neck_landing',
                                                'west_lappet', 'riddle', 'legend_throne')],
        'return_path': [f'room:{x}' for x in ('legend_throne', 'riddle', 'east_lappet', 'neck_landing',
                                              'throat_stair', 'paw_hall', 'gallery_w', 'belly_hall', 'king_throne',
                                              'belly_hall', 'queen_throne', 'thieves_throne', 'queen_throne',
                                              'belly_hall', 'gallery_e', 'paw_hall', 'breast_gate')],
        'goals': [
            {'id': 'goal:name', 'space': 'room:riddle', 'kind': 'use', 'story': 'Q-C9',
             'what': "Name the Sphinx on the sun disc: GOLUX (q-c9.name_right: done 112181, award 419, 6,000).",
             'gives': {'qbit': 112181}},
            {'id': 'goal:thrones', 'space': 'room:king_throne', 'kind': 'use', 'story': 'Q-C9',
             'what': "Sit on the four thrones (King, Queen, Thieves, legend): +2 Might, Personality, Accuracy, "
                     "Endurance once per character (player bits 11300-11303)."},
        ],
        'set_pieces': [
            {'id': 'set:riddle', 'kind': 'scripted', 'spaces': ['room:riddle', 'room:drop_cell'],
             'rule': "The sun disc asks 'What is my name?' on every step until named: GOLUX opens the crown, veil and "
                     "legend doors with the Sphinx's stir; anything else sinks the disc and drops the party, hurt, "
                     "into the drop cell; the disc rises again."},
            {'id': 'set:clues', 'kind': 'scripted', 'spaces': ['room:drop_cell', 'room:glyph_w', 'room:glyph_e',
                                                               'room:library'],
             'rule': "Five clue walls, one letter each, and the whole riddle on the library's end wall."},
        ],
        'diagram': FlowDict(file='diagram.txt'),
        'totals': {'rooms': len(ROOMS), 'sectors': len(ROOMS), 'monsters_about': 45, 'chests': 4, 'loops': 4,
                   'doors': 7, 'fixed_actors': 0, 'floor_area_munits2': 35},
        'notes': "Class M (MAPS: 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors). From the MU-6 "
                 "graph devdocs/xeen/mockups/act4_graphs/xd15.graph.yml and D-39 (two carved throne doors in the "
                 "belly hall, the mask on the loose panel; the drop cell's door opens from inside and stays open; the "
                 "drop's damage by event; Starburst (Air) and Divine Intervention books; two Might Boosts by event; "
                 "levels 22-45). 21 rooms, one rectangle each; the stairs are stepped rooms of 32 risers.",
    }
    if level in ('L3', 'L4'):
        plan['sketch'] = FlowDict(file='rooms.yml', grid=512)
    return plan


DIAGRAM = r"""XD-15 The Sphinx (x east, y north; the Sphinx faces south; floors 1280 / 0 / -640)

  -640 (north of the haunches)
        [Scribes' library: tablets, lectern GEMS x2, T4 chest, clue 5, the whole riddle]
              | door                         | open
        [West glyph hall: clue 2]--open--[East glyph hall: clues 3, 4]==door (opens from inside)==[DROP CELL: clue 1]
              | open                                                                                ^
        [Stair foot]                                                                                | wrong name
              | 20 steps down                                                                       |
     0  [Dungeon stair] -- [HAUNCH VAULT: T4 chest, 2 Might Boosts]                                 |
                                 | door                                                             |
   [KING'S THRONE]=crown door=[BELLY HALL: six striped columns]=veil door=[QUEEN'S THRONE]=panel=[Thieves'] |
                       |                                  |                                          |
   [West gallery: great sarcophagus T4, Might 40]   [East gallery: gems]                             |
                       |                                  |                                          |
                     [HALL OF THE PAWS: columns, braziers]                                           |
                       | open                  | throat stair (40 steps up, south)                   |
                     [BREAST GATE: arrival; two leaves out to X6]                                    |
  1280 (south, in front)          [Neck landing]                                                     |
                            /                          \                                             |
                 [West lappet: T4 chest]         [East lappet: gems]                                 |
                            \                          /                                             |
   [THRONE OF LEGENDS: two books]=legend door=[RIDDLE CHAMBER: plaques, eyes, SUN DISC] ------------+
"""


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, width=120, allow_unicode=True)


def write(level):
    d = BRIEFS / level
    d.mkdir(parents=True, exist_ok=True)
    dump(d / 'project.yml', project_yml(level))
    dump(d / 'plan.yml', plan_yml(level))
    (d / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(d / 'rooms.yml', rooms_yml())
    if level == 'L4':
        dump(d / 'objects.yml', objects_yml())
        dump(d / 'wiring.yml', wiring_yml())
        (d / 'atmosphere.yml').unlink(missing_ok=True)


if __name__ == '__main__':
    check_torches()
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
    print('written', sys.argv[1:] or 'L1-L4')
