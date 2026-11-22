#!/usr/bin/env python3
"""DD-07 Eastern Tower: writes the project files of devdocs/xeen/briefs/dd07/L1..L4 (lane A7 phase 4, ninth session,
sub-agent agent:xeen-a7-dd07). Route after level_generation/projects/xeen/xd15/gen.py (phase 4) and
level_generation/projects/xeen/dd06/gen.py (the same Towers of Mok family, two-storey stair halls).

    python3 level_generation/projects/xeen/dd07/gen.py            all four levels
    python3 level_generation/projects/xeen/dd07/gen.py L4         one level

Rerun after every change here (level_generation/projects/xeen/dd07/cycle.sh); never hand-edit the written files. The playtests are
written by tools/gen_tests.py from the built ids.lock.yml.

Frame: x east, y north, z up. Four floors 640 apart (L1 0, L2 640, L3 1280, L4 1920), each 512 high (L4 640).
The well: an octagon (apothem 448) in the middle, open from the ground floor to a slate cone (2,944 at its walls, a
point at 3,584). Round it on every floor a gallery shaped like a U (north, east and south of the well, its outer walls
at 960), open on the west, where the floor's landing hall runs from the well's west wall (railed windows above L1, an
open arch on L1) out to the stair halls. The stair: three two-storey halls west of the landings, alternating south and
north (L1->L2 south, L2->L3 north, L3->L4 south over the first), each a flight of 20 steps along its length to a
gallery at the next floor, so the climb winds round and round as it rises (the spiral stair, built as a dog-leg). The
D3 door is in the ground floor's landing hall (the door hall), in its west wall. Walls between rooms are 128 thick; the
well's wall 64. The floating disc is a lift in the well against its east wall: up at L4 at load, the party rides it
down to the well's foot.
"""
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / 'devdocs/xeen/briefs/dd07'


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
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------------------------------------------------------------------------------------------------------------------
# Numbers
MAP_STATS_ID = 9156
MUSIC = 43                       # source/maps.yml DD-07
ADEPT, MAGUS, MYSTIC, EYE = 11203, 11204, 11200, 11570
NAMES = {ADEPT: 'Floating Adept', MAGUS: 'Floating Magus', MYSTIC: 'Mystic Mage', EYE: 'Floating Eye'}
LEVEL = {ADEPT: 28, MAGUS: 38, MYSTIC: 45, EYE: 40}
QBITS = {
    'started': 113360,           # A3's q-d18.started (D3's door sets it)
    'tower_disks': 113362,       # A3's (q-d18.l3_disks)
    'letter_found': 113363,      # A3's (q-d18.letter)
    'griffin_found': 113403,     # A3's (q-d20.griffin)
}
ITEMS = {'jewel_of_ages': 12527, 'energy_disk': 12334, 'ellingers_letter': 12361, 'golden_griffin': 12351}
D3_ENTRANCE = 'entrance:dd07_door'   # D3's published arrival before the tower's door: (15360, 9216, 1888) facing west
Z = {1: 0, 2: 640, 3: 1280, 4: 1920}
H = {1: 512, 2: 512, 3: 512, 4: 640}

# ---------------------------------------------------------------------------------------------------------------------
# Textures: the Towers of Mok (MM8 Castle of Air d27, dungeon_families towers), DD-07's accent MM7 School of Sorcery
# 7d14 in the laboratory and the study (D-39 Q6), XD-04's ward texture on the vault's door of light (D-39 Q4), D-37's
# dead mirror (D-39 Q5).
ASHLAR = S('gston1wl', 128, 256)        # green-grey ashlar, the tower
SKIRT = S('gstntilev', 64, 128)         # green marble skirting
SLAB = S('gstntileh', 128, 64)          # marble band at each floor's slab in the well
FLAGS = S('gston1fl', 128, 128)         # scale-pattern flags
CEIL = S('gstn1cl', 128, 128)           # panelled stone ceilings
COBBLE = S('gcstflor', 128, 256)        # grey cobbles, the galleries and stair halls
STONEDOOR = S('gcstdoor', 128, 256)     # the tower's stone doors
BLACK = S('gstyl', 128, 128)            # black stone: the disc, the vault's stand, the pylons' pillars
LABWALL = S('twb2', 128, 256)           # 7d14's brown stone
LABFLOOR = S('7tfb1', 128, 128)         # 7d14's flags
LABCEIL = S('tfb2', 128, 128)           # 7d14's ceiling
TRIM = S('trim5_32', 32, 64)            # 7d14's wooden trim
SHELVES = S('7t1books', 128, 256)       # 7d14's bookshelves
WOOD = S('7t1books1', 128, 128)         # 7d14's shelf wood
CABS = S('7t1cabs', 64, 128)            # 7d14's cabinets
BOARDS = S('7trimd', 128, 256)          # boards: beds' frames, the commons' table
SHEET = S('t2bedsht', 128, 256)         # bed linen
WATER = S('wtrtyl', 128, 128, liquid='water')           # the fountains' water
STARS = S('sgstars', 64, 64)            # the scrying pool: black water with stars in it
WARD = S('xwward', 256, 512, translucent=1)   # XD-04's ward: the door of light
MIRROR = S('xkmirror', 128, 128)        # D-37's dead mirror
DESKSIDE = S('deskside', 64, 64, scale=1.25)
DESKTOP = S('desktop', 128, 64, scale=2)
LECTERN_TOP = S('desktop', 128, 64, offset=Flow([96, 40]))

THEMES = [
    dict(id='theme:tower', wall=ASHLAR, floor=FLAGS, ceiling=CEIL, reveal=ASHLAR, door=STONEDOOR,
         bands=Flow([FlowDict(height=32, surface=SKIRT)]),
         notes="The Mok tower's rooms: green-grey ashlar (MM8 gston1wl) over a green marble skirting (gstntilev), "
               "scale-pattern flags (gston1fl), panelled stone ceilings (gstn1cl), the tower's stone doors (gcstdoor)."),
    dict(id='theme:gallery', wall=ASHLAR, floor=COBBLE, ceiling=CEIL, reveal=ASHLAR, door=STONEDOOR,
         bands=Flow([FlowDict(height=32, surface=SKIRT)]),
         notes="The galleries round the well and the landing halls: the ashlar, grey cobbles (gcstflor) underfoot."),
    dict(id='theme:stair', wall=ASHLAR, floor=COBBLE, ceiling=CEIL, reveal=ASHLAR, door=STONEDOOR,
         notes="The stair halls: the same ashlar and cobbles, no skirting (the flights run along the walls)."),
    dict(id='theme:well', wall=ASHLAR, floor=FLAGS, ceiling=CEIL, reveal=ASHLAR, door=STONEDOOR,
         notes="The levitation well: the ashlar from the foot to the cone, a marble band (gstntileh) at each floor's "
               "slab, the flags at its foot, the cone's panels."),
    dict(id='theme:lab', wall=LABWALL, floor=LABFLOOR, ceiling=LABCEIL, reveal=LABWALL, door=STONEDOOR,
         bands=Flow([FlowDict(height=32, surface=TRIM)]),
         notes="The mages' own rooms on the top floor (D-39 Q6): MM7's School of Sorcery (7d14), brown stone (twb2) "
               "over a wooden skirting (trim5_32), its flags (7tfb1) and ceiling (tfb2)."),
]

# ---------------------------------------------------------------------------------------------------------------------
# Geometry
WELL = [(192, -448), (448, -192), (448, 192), (192, 448), (-192, 448), (-448, 192), (-448, -192), (-192, -448)]
# well edges: 0 SE, 1 E, 2 NE, 3 N, 4 NW, 5 W, 6 SW, 7 S
RING = [(-960, -960), (960, -960), (960, 960), (-960, 960), (-960, 384), (-347, 384), (-219, 512), (219, 512),
        (512, 219), (512, -219), (219, -512), (-219, -512), (-347, -384), (-960, -384)]
# ring edges: 0 S outer, 1 E outer, 2 N outer, 3 W outer (north arm's end), 4 cut north, 5 inner NW (part),
# 6 inner N, 7 inner NE, 8 inner E, 9 inner SE, 10 inner S, 11 inner SW (part), 12 cut south, 13 W outer (south arm)
RING_TO_WELL = {'n': (6, 3), 'ne': (7, 2), 'e': (8, 1), 'se': (9, 0), 's': (10, 7)}
LANDING = (-2752, -256, -512, 256)
# D-58 (decider, 2026-11-21, seventeenth session): a roof stair from the top floor to a trapdoor up to D7's
# entrance:dd07_roof, one way up, open after m30.done (A3's hook d7.roof_dd07). A stair hall south of the top gallery
# (through its south outer wall): one flight of 16 steps of 32 rising east to a head at 2,432, and over the head a hatch
# in the ceiling, a frame of black beams round a plank trapdoor.
ROOF_STAIR = (-256, -1472, 1536, -1088)
ROOF_HEAD = 1920 + 512            # the head's floor
ROOF_CEIL = ROOF_HEAD + 288       # the stair hall's ceiling
ROOF_HATCH = (1216, -1376, 1408, -1184)
STAIR_S = (-2752, -1024, -1216, -384)
STAIR_N = (-2752, 384, -1216, 1024)

ROOMS = {}


def room(rid, name, outline, floor, ceiling, theme, **extra):
    ROOMS[rid] = dict(name=name, outline=outline, floor=floor, ceiling=ceiling, theme=theme, **extra)


def rroom(rid, name, r, floor, ceiling, theme, **extra):
    room(rid, name, rect(*r), floor, ceiling, theme, rect=r, **extra)


# L1 (z 0)
rroom('door_hall', 'Door hall', LANDING, 0, 512, 'gallery')
room('well_foot', 'The well', WELL, 0, 2944, 'well')
room('ring1', 'East gallery', RING, 0, 512, 'gallery')
rroom('commons', "Mages' commons", (-704, -1792, 704, -1088), 0, 512, 'tower')
rroom('store', 'Store room', (1088, -512, 1664, 512), 0, 448, 'stair', store=True)
rroom('stair12', 'First stair', STAIR_S, 0, 1152, 'stair')
# L2 (z 640)
rroom('stair2', 'Second landing', LANDING, 640, 1152, 'gallery')
room('ring2', 'Second gallery', RING, 640, 1152, 'gallery')
rroom('cabinet', 'Cabinet of curiosities', (1088, -960, 1984, 640), 640, 1152, 'tower')
rroom('dormitory', "Mages' dormitory", (-448, -1856, 1984, -1088), 640, 1152, 'tower')
rroom('mirror', 'Mirror room', (-1088, -1856, -576, -1088), 640, 1088, 'tower')
rroom('stair23', 'Second stair', STAIR_N, 640, 1824, 'stair')
# L3 (z 1280)
rroom('stair3', 'Third landing', LANDING, 1280, 1792, 'gallery')
room('ring3', 'Third gallery', RING, 1280, 1792, 'gallery')
rroom('conjury', 'Conjury', (-960, 1088, 192, 1856), 1280, 1792, 'tower')
rroom('scrying', 'Scrying room', (320, 1088, 1856, 1856), 1280, 1792, 'tower')
rroom('vault', "The mages' vault", (1088, -576, 1856, 576), 1280, 1792, 'tower')
rroom('alcoves', 'Disk alcoves', (1984, -384, 2496, 384), 1280, 1664, 'tower')
rroom('stair34', 'Third stair', STAIR_S, 1280, 2464, 'stair')
# L4 (z 1920)
rroom('stair4', 'Top landing', LANDING, 1920, 2432, 'gallery')
room('ring4', 'Gallery under the cone', RING, 1920, 2560, 'gallery')
rroom('lab', 'The laboratory', (-960, 1088, 960, 1984), 1920, 2560, 'lab')
rroom('study', "The Archmagus's study", (-2752, 384, -1088, 1728), 1920, 2560, 'lab')
rroom('roof_stair', 'Roof stair', ROOF_STAIR, 1920, ROOF_CEIL, 'stair')

FLOOR_OF = {}
for _rid in ROOMS:
    FLOOR_OF[_rid] = {0: 1, 640: 2, 1280: 3, 1920: 4}[ROOMS[_rid]['floor']]

WELL_BANDS = Flow([FlowDict(height=32, surface=SKIRT), FlowDict(height=576, surface=ASHLAR),
                   FlowDict(height=640, surface=SLAB), FlowDict(height=1216, surface=ASHLAR),
                   FlowDict(height=1280, surface=SLAB), FlowDict(height=1856, surface=ASHLAR),
                   FlowDict(height=1920, surface=SLAB)])

# Disc (the lift) against the well's east wall, and its two levers beside the east openings.
DISC = (256, 0)
DISC_SIZE = 352
LEVER_Y = 176

# ---------------------------------------------------------------------------------------------------------------------
# Openings: found by facing walls (rectangles by compass side, the well and the ring by edge number).


def edges(rid):
    o = ROOMS[rid]['outline']
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


SIDE = {'south': 0, 'east': 1, 'north': 2, 'west': 3}
OPEN_AT = {}   # opening id -> (point, width, room a, room b, z of the opening's floor)


def opening(oid, a, wa, b, wb, at=None, width=256, height=320, link=None, **kw):
    """`wa`, `wb`: the walls (compass side of a rectangle or edge number); `at`: the opening's middle as the coordinate
    along the wall (x for a wall along x, y for one along y); None: the middle of the shared stretch."""
    ia = SIDE.get(wa, wa)
    ib = SIDE.get(wb, wb)
    p0, p1 = edges(a)[ia]
    q0, q1 = edges(b)[ib]
    L = math.dist(p0, p1)
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    t = sorted([(q0[0] - p0[0]) * d[0] + (q0[1] - p0[1]) * d[1], (q1[0] - p0[0]) * d[0] + (q1[1] - p0[1]) * d[1]])
    lo, hi = max(0.0, t[0]), min(L, t[1])
    if hi - lo <= 0:
        raise SystemExit(f'{oid}: walls {wa}/{wb} of {a}/{b} share no stretch')
    if at is None:
        tc = (lo + hi) / 2
    else:
        tc = ((at - p0[0]) / d[0]) if abs(d[0]) > 0.5 else ((at - p0[1]) / d[1])
    if tc - width / 2 < lo - 0.01 or tc + width / 2 > hi + 0.01:
        raise SystemExit(f'opening {oid} ({width} at {at}) does not fit the shared stretch {lo:.0f}..{hi:.0f}')
    along = (tc - lo) / (hi - lo)
    o = {'id': f'open:{oid}', 'from': f'room:{a}', 'to': f'room:{b}', 'from_wall': ia, 'to_wall': ib}
    if link:
        o['link'] = link
    if round(along, 4) != 0.5:
        o['along'] = round(along, 4)
    o['width'] = width
    o['height'] = height
    o.update(kw)
    pt = (p0[0] + d[0] * tc, p0[1] + d[1] * tc)
    OPEN_AT[oid] = (pt, width, a, b, max(ROOMS[a]['floor'], ROOMS[b]['floor']) + kw.get('sill', 0))
    return o


OPENINGS = []


def add(*a, **kw):
    OPENINGS.append(opening(*a, **kw))


# L1: the door hall and the well's foot, the gallery's arches
add('hall_well', 'door_hall', 'east', 'well_foot', 5, width=320, height=384, link='link:hall_well',
    notes="The door hall opens on the well's foot: an arch.")
add('hall_ring1_n', 'door_hall', 'north', 'ring1', 4, at=-736, width=320, height=384, link='link:hall_ring1')
add('hall_ring1_s', 'door_hall', 'south', 'ring1', 12, at=-736, width=320, height=384, link='link:hall_ring1_s')
for side, (ir, iw) in RING_TO_WELL.items():
    if side == 'se':
        continue          # the well's south-east wall stays whole on L1 (the store room's side)
    add(f'ring1_well_{side}', 'ring1', ir, 'well_foot', iw, width=320 if side in ('n', 'e', 's') else 256, height=384,
        link='link:well_ring1' if side == 'e' else None,
        notes="An arch from the east gallery into the well's foot." if side != 'e' else
        "The east arch: the disc comes to rest at the foot of it.")
add('ring1_commons', 'ring1', 0, 'commons', 'north', at=0, width=192, height=320, link='link:ring1_commons')
add('ring1_store', 'ring1', 1, 'store', 'west', at=0, width=192, height=320, link='link:ring1_store')
add('hall_stair12', 'door_hall', 'south', 'stair12', 'north', at=-2624, width=192, height=320, link='link:stair_1_2',
    notes="The foot of the stair, beside the door: the first stair hall.")
add('stair12_top', 'stair12', 'north', 'stair2', 'south', at=-1472, width=320, height=384, link='link:stair_1_2',
    notes="The head of the first stair: its gallery opens north on to the second landing.")
# L2
for side, (ir, iw) in RING_TO_WELL.items():
    add(f'ring2_well_{side}', 'ring2', ir, 'well_foot', iw, width=320 if side in ('n', 'e', 's') else 256, height=288,
        sill=80, notes="A railed window over the well.")
add('stair2_well', 'stair2', 'east', 'well_foot', 5, width=320, height=288, sill=80,
    notes="The landing's railed window over the well.")
add('stair2_ring2_n', 'stair2', 'north', 'ring2', 4, at=-736, width=320, height=384, link='link:stair2_ring2')
add('stair2_ring2_s', 'stair2', 'south', 'ring2', 12, at=-736, width=320, height=384, link='link:stair2_ring2_s')
add('ring2_cabinet', 'ring2', 1, 'cabinet', 'west', at=320, width=192, height=320, link='link:ring2_cabinet')
add('cabinet_dorm', 'cabinet', 'south', 'dormitory', 'north', at=1536, width=192, height=320,
    link='link:cabinet_dorm')
add('dorm_mirror', 'dormitory', 'west', 'mirror', 'east', at=-1472, width=256, height=320, link='link:dorm_mirror')
add('mirror_ring2', 'mirror', 'north', 'ring2', 0, at=-768, width=256, height=320, link='link:mirror_ring2')
add('stair2_stair23', 'stair2', 'north', 'stair23', 'south', at=-1472, width=256, height=320, link='link:stair_2_3',
    notes="The foot of the second stair, at the east end of its hall.")
add('stair23_top', 'stair23', 'south', 'stair3', 'north', at=-2496, width=320, height=384, link='link:stair_2_3',
    notes="The head of the second stair: its gallery opens south on to the third landing.")
# L3
for side, (ir, iw) in RING_TO_WELL.items():
    add(f'ring3_well_{side}', 'ring3', ir, 'well_foot', iw, width=320 if side in ('n', 'e', 's') else 256, height=288,
        sill=80, notes="A railed window over the well.")
add('stair3_well', 'stair3', 'east', 'well_foot', 5, width=320, height=288, sill=80,
    notes="The landing's railed window over the well.")
add('stair3_ring3_n', 'stair3', 'north', 'ring3', 4, at=-736, width=320, height=384, link='link:stair3_ring3')
add('stair3_ring3_s', 'stair3', 'south', 'ring3', 12, at=-736, width=320, height=384, link='link:stair3_ring3_s')
add('ring3_conjury', 'ring3', 2, 'conjury', 'south', at=-384, width=192, height=320, link='link:ring3_conjury')
add('ring3_scrying', 'ring3', 2, 'scrying', 'south', at=640, width=192, height=320, link='link:ring3_scrying')
add('conjury_scrying', 'conjury', 'east', 'scrying', 'west', at=1600, width=256, height=320,
    link='link:conjury_scrying', notes="The passage in the wall between the two pylon rooms.")
add('ring3_vault', 'ring3', 1, 'vault', 'west', at=0, width=192, height=320, link='link:ward',
    notes="The vault's door of light.")
add('vault_alcoves', 'vault', 'east', 'alcoves', 'west', at=0, width=320, height=320, link='link:vault_alcoves')
add('stair3_stair34', 'stair3', 'south', 'stair34', 'north', at=-2624, width=192, height=320, link='link:stair_3_4',
    notes="The foot of the third stair, at the west end of its hall.")
add('stair34_top', 'stair34', 'north', 'stair4', 'south', at=-1472, width=320, height=384, link='link:stair_3_4',
    notes="The head of the third stair: its gallery opens north on to the top landing.")
# L4
for side, (ir, iw) in RING_TO_WELL.items():
    if side == 'e':
        add('ring4_disc', 'ring4', ir, 'well_foot', iw, width=320, height=384, link='link:disc_ring4',
            notes="The disc's landing: an opening in the gallery's rail over the well, where the floating disc rests.")
    else:
        add(f'ring4_well_{side}', 'ring4', ir, 'well_foot', iw, width=320 if side in ('n', 's') else 256, height=352,
            sill=80, notes="A railed window over the well.")
add('stair4_well', 'stair4', 'east', 'well_foot', 5, width=320, height=288, sill=80,
    notes="The landing's railed window over the well.")
add('stair4_ring4_n', 'stair4', 'north', 'ring4', 4, at=-736, width=320, height=384, link='link:stair4_ring4')
add('stair4_ring4_s', 'stair4', 'south', 'ring4', 12, at=-736, width=320, height=384, link='link:stair4_ring4_s')
add('ring4_lab', 'ring4', 2, 'lab', 'south', at=0, width=192, height=320, link='link:ring4_lab')
add('lab_study', 'lab', 'west', 'study', 'east', at=1344, width=192, height=320, link='link:lab_study')
add('study_stair4', 'study', 'south', 'stair4', 'north', at=-1920, width=192, height=320, link='link:study_stair4')
add('ring4_roof', 'ring4', 0, 'roof_stair', 'north', at=0, width=256, height=320, link='link:ring4_roof',
    notes="From the gallery's south arm into the roof stair (D-58).")

# ---------------------------------------------------------------------------------------------------------------------
# Walls: panels (the mirror)
WALLS = {}

# ---------------------------------------------------------------------------------------------------------------------
# Platforms, levels, flights


def block(at, size, rise, surface, top=None, notes=None, pid=None, base=None, end=None, bottom=None):
    d = FlowDict()
    if pid:
        d['id'] = pid
    d['at'] = F(*at)
    d['size'] = F(*size)
    d['rise'] = rise
    d['surface'] = surface
    if end:
        d['end_surface'] = end
    if top:
        d['top_surface'] = top
    if bottom:
        d['bottom_surface'] = bottom
    if base is not None:
        d['base'] = base
    if notes:
        d['notes'] = notes
    return d


def stair_gallery(r, side, pid, notes):
    """The head of a stair hall: a gallery 512 deep across the hall's `side` end, hanging 608 over its floor."""
    x0, y0, x1, y1 = r
    gx0, gx1 = (x1 - 512, x1) if side == 'east' else (x0, x0 + 512)
    return FlowDict(id=pid, outline=Flow([F(gx0, y0), F(gx1, y0), F(gx1, y1), F(gx0, y1)]), rise=32,
                    surface=ASHLAR, top_surface=COBBLE, bottom_surface=CEIL, base=608, notes=notes)


def hatch_frame(b):
    """The four beams of a hatch's frame, centred on the rectangle's edges (the trapdoor leaf hangs inside them)."""
    x0, y0, x1, y1 = b
    return [Flow([F(x0 - 16, y0), F(x1 + 16, y0)]), Flow([F(x0 - 16, y1), F(x1 + 16, y1)]),
            Flow([F(x0, y0 + 16), F(x0, y1 - 16)]), Flow([F(x1, y0 + 16), F(x1, y1 - 16)])]


BEAMS_BLACK = S('hwm2rf', 128, 128)     # black beams (DD-06's cone beams): the roof hatch's frame
BEAMS = {
    'roof_stair': [FlowDict(path=path, width=32, bottom=ROOF_CEIL - 40, depth=40, surface=BEAMS_BLACK,
                            notes="The roof hatch's frame: black beams round the trapdoor under the ceiling.")
                   for path in hatch_frame(ROOF_HATCH)],
}

PLATFORMS = {
    'stair12': Flow([stair_gallery(STAIR_S, 'east', 'platform:head12',
                                   "The head of the first stair at the second floor (640), across the east end.")]),
    'stair23': Flow([stair_gallery(STAIR_N, 'west', 'platform:head23',
                                   "The head of the second stair at the third floor (1280), across the west end.")]),
    'stair34': Flow([stair_gallery(STAIR_S, 'east', 'platform:head34',
                                   "The head of the third stair at the top floor (1920), across the east end.")]),
    'commons': Flow([
        block((0, -1664), (768, 128), 72, BOARDS, WOOD, "The long refectory table along the south wall's line.",
              pid='platform:table'),
        block((-448, -1752), (384, 64), 256, SHELVES, WOOD, "Lore books on shelves along the south wall.",
              pid='platform:lore'),
    ]),
    'cabinet': Flow([
        block((1928, -704), (96, 320), 160, CABS, WOOD, "A cabinet of labelled oddities.",
              pid='platform:case_1'),
        block((1928, -192), (96, 320), 160, CABS, WOOD, "A cabinet of labelled oddities.", pid='platform:case_2'),
        block((1928, 320), (96, 320), 160, CABS, WOOD,
              "The last case: the Golden Griffin in a box on it (chest:case_griffin, D-90).", pid='platform:case_griffin'),
    ]),
    'mirror': Flow([
        block((-1056, -1472), (32, 224), 352, MIRROR, BLACK, "The tall dead mirror (D-37's xkmirror) in a frame of "
              "black stone, standing against the end wall.", pid='platform:mirror', end=S('gstyl', 128, 128, fit=False)),
    ]),
    'dormitory': Flow([block((x, -1640), (192, 384), 48, BOARDS, SHEET, "A narrow bed.", pid=f'platform:bed_{i}')
                       for i, x in enumerate((-192, 192, 576, 960), 1)]),
    'conjury': Flow([
        block((-576, 1600), (96, 96), 128, BLACK, BLACK, "The west ward pylon's pillar (its crystal on top).",
              pid='platform:pylon_w'),
    ]),
    'scrying': Flow([
        block((1472, 1600), (96, 96), 128, BLACK, BLACK, "The east ward pylon's pillar (its crystal on top).",
              pid='platform:pylon_e'),
        block((576, 1792), (64, 64), 96, BLACK, BLACK, "A stand with a crystal ball.", pid='platform:ball_1'),
        block((896, 1792), (64, 64), 96, BLACK, BLACK, "A stand with a crystal ball.", pid='platform:ball_2'),
        block((1216, 1792), (64, 64), 96, BLACK, BLACK, "A stand with a crystal ball.", pid='platform:ball_3'),
    ]),
    'roof_stair': Flow([
        FlowDict(id='platform:roof_head', outline=Flow([F(1088, -1472), F(1536, -1472), F(1536, -1088),
                                                         F(1088, -1088)]),
                 rise=ROOF_HEAD - 1920, surface=ASHLAR, top_surface=COBBLE,
                 notes="The roof stair's head (2,432), across the east end under the hatch."),
        FlowDict(id='platform:roof_hatch',
                 outline=Flow([F(ROOF_HATCH[0] + 16, ROOF_HATCH[1] + 16), F(ROOF_HATCH[2] - 16, ROOF_HATCH[1] + 16),
                               F(ROOF_HATCH[2] - 16, ROOF_HATCH[3] - 16), F(ROOF_HATCH[0] + 16, ROOF_HATCH[3] - 16)]),
                 base=ROOF_CEIL - 16 - 1920, rise=16, surface=BOARDS, top_surface=BOARDS, bottom_surface=BOARDS,
                 notes="The roof trapdoor: a plank leaf hung shut in its frame of beams (D-58: up to D7 after "
                       "m30.done)."),
    ]),
    'vault': Flow([
        block((1664, 0), (96, 96), 112, BLACK, BLACK, "The stand of black glass where the Jewel of Ages lies.",
              pid='platform:jewel_stand'),
    ]),
    'alcoves': Flow([
        block((2432, 0), (64, 384), 128, CABS, WOOD, "A mage's experiment of wires on a bench: the two Energy Disks.",
              pid='platform:experiment'),
    ]),
    'lab': Flow([
        block((-576, 1536), (256, 256), 64, ASHLAR, WATER,
              "The Fountain of Minimal Abilities: a marble basin (q-d18.minimal_fountain).",
              pid='platform:fountain_min'),
        block((576, 1536), (256, 256), 64, ASHLAR, WATER, "The Fountain of Life: a marble basin; it heals.",
              pid='platform:fountain_life'),
        block((0, 1888), (192, 96), 88, CABS, WOOD, "The Bubbling Vat's bench (the vat a dressing).",
              pid='platform:vat'),
        block((-608, 1928), (448, 96), 96, CABS, WOOD, "A bench of glass and brass along the north wall."),
        block((608, 1928), (448, 96), 96, CABS, WOOD, "A bench of glass and brass along the north wall."),
    ]),
    'study': Flow([
        block((-1920, 1344), (256, 128), 80, DESKSIDE, DESKTOP,
              "The Archmagus's desk: Ellinger's sealed letter in the writing box on it (chest:desk, D-90).", pid='platform:desk'),
        block((-2560, 1344), (64, 48), 80, DESKSIDE, LECTERN_TOP,
              "A lectern: the Book of Fantastic Knowledge (q-d18.fantastic_book).", pid='platform:book_fantastic'),
        block((-2560, 896), (64, 48), 80, DESKSIDE, LECTERN_TOP,
              "A lectern: the Book of Great Power (q-d18.great_power_book).", pid='platform:book_power'),
        block((-2176, 1688), (512, 64), 288, SHELVES, WOOD, "Shelves along the north wall."),
        block((-1408, 1688), (384, 64), 288, SHELVES, WOOD, "Shelves along the north wall."),
    ]),
}

LEVELS = {
    'scrying': Flow([
        FlowDict(id='level:pool', outline=Flow([F(704, 1344), F(1088, 1344), F(1088, 1600), F(704, 1600)]),
                 floor=1280 - 16, surface=STARS, notes="The black scrying pool: stars in the water."),
    ]),
}

FLIGHTS = {
    'stair12': Flow([FlowDict(**{'from': F(-2560, -768), 'to': F(-1728, -768), 'to_height': 640, 'width': 320,
                                 'steps': 20, 'notes': "Twenty steps of 32 along the hall, rising east."})]),
    'stair23': Flow([FlowDict(**{'from': F(-1408, 704), 'to': F(-2240, 704), 'to_height': 1280, 'width': 320,
                                 'steps': 20, 'notes': "Twenty steps of 32 along the hall, rising west."})]),
    'stair34': Flow([FlowDict(**{'from': F(-2560, -768), 'to': F(-1728, -768), 'to_height': 1920, 'width': 320,
                                 'steps': 20, 'notes': "Twenty steps of 32 along the hall, rising east."})]),
    'roof_stair': Flow([FlowDict(**{'from': F(256, -1280), 'to': F(1088, -1280), 'width': 320, 'steps': 16,
                                    'notes': "Sixteen steps of 32 along the hall, rising east to the head."})]),
}

AMBIENT = {'roof_stair': 16, 'well_foot': 18, 'door_hall': 20, 'stair12': 16, 'stair23': 16, 'stair34': 16, 'store': 12,
           'mirror': 14, 'alcoves': 14, 'vault': 16}

ROOM_NOTES = {
    'door_hall': "Inside the west door from D3 (the arrival entrance:d3_door, quiet): sconces, the first stair's foot "
                 "in the south wall beside the door, the well's foot east through an arch, the gallery north and south.",
    'well_foot': "The levitation well, an octagon open from the ground floor to the slate cone (2,944 at the walls, "
                 "3,584 at the point): the galleries' railed windows on every floor, a marble band at each floor's "
                 "slab, the floating disc resting against its east wall at the top floor.",
    'ring1': "The ground floor's gallery round the well's north, east and south sides: arches into the well; doors "
             "to the commons and the store room.",
    'commons': "A refectory and reading room: the long table, lore books on shelves.",
    'store': "A dead end with a chest: reagents in jars, sacks and barrels in clumps (a storeroom).",
    'stair12': "The first stair hall, two storeys: twenty steps along it to its head at the second floor.",
    'stair2': "The second floor's landing hall: the window over the well, the gallery north and south, the second "
              "stair's foot.",
    'ring2': "The second gallery: railed windows on the well; the cabinet east, the mirror room south-west.",
    'cabinet': "Cabinets of labelled oddities; the Golden Griffin in the last.",
    'dormitory': "Narrow beds in a row, the mages' chest.",
    'mirror': "A tall dead mirror in the end wall: 'The mirror does not respond.'",
    'stair23': "The second stair hall: twenty steps to its head at the third floor.",
    'stair3': "The third floor's landing hall: the window over the well, the gallery, the third stair's foot.",
    'ring3': "The third gallery: the vault's door of light in its east wall, humming; the conjury and the scrying "
             "room north.",
    'conjury': "A summoning room: the west ward pylon, a crystal on a black pillar; the passage east.",
    'scrying': "Crystal balls on stands, the black scrying pool, the east ward pylon.",
    'vault': "Behind the door of light: the Jewel of Ages on its stand of black glass; the vault's keeper.",
    'alcoves': "Alcoves off the vault: a mage's experiment of wires and the two Energy Disks.",
    'stair34': "The third stair hall, over the first: twenty steps to its head at the top floor.",
    'stair4': "The top floor's landing hall: the window over the well, the gallery, the study's door.",
    'ring4': "The gallery under the cone, 640 high: the disc's landing in its east rail, the laboratory north.",
    'lab': "The mages' laboratory (MM7's School of Sorcery): benches, the Bubbling Vat, the Fountain of Minimal "
           "Abilities and the Fountain of Life, floor braziers under the retorts.",
    'study': "The Archmagus's study: the desk with Ellinger's letter, the two book lecterns, shelves, the master's "
             "chest.",
    'roof_stair': "The roof stair (D-58), off the top gallery's south arm: one flight east along the hall to a head "
                  "under the roof trapdoor (to D7 after m30.done).",
}


def rooms_yml():
    rooms = []
    for rid, r in ROOMS.items():
        d = {'id': f'room:{rid}', 'name': r['name'], 'outline': Flow([F(*p) for p in r['outline']]),
             'floor': r['floor'], 'ceiling': r['ceiling'], 'theme': f"theme:{r['theme']}"}
        if rid == 'well_foot':
            d['ceiling_levels'] = [FlowDict(ceiling=3584, top_scale=0, notes="The slate cone over the well.")]
            d['bands'] = WELL_BANDS
        if r.get('store'):
            d['store'] = True
        if rid in WALLS:
            d['walls'] = WALLS[rid]
        if rid in PLATFORMS:
            d['platforms'] = PLATFORMS[rid]
        if rid in LEVELS:
            d['levels'] = LEVELS[rid]
        if rid in BEAMS:
            d['beams'] = BEAMS[rid]
        if rid in FLIGHTS:
            d['flights'] = FLIGHTS[rid]
        d['ambient'] = AMBIENT.get(rid, 20)
        d['notes'] = ROOM_NOTES[rid]
        rooms.append(d)
    return {'format': 0, 'themes': THEMES, 'defaults': FlowDict(theme='theme:tower', ambient=20), 'rooms': rooms,
            'openings': OPENINGS,
            'notes': "DD-07 Eastern Tower at L4: four floors 640 apart round the levitation well (an octagon open "
                     "from the ground floor to the slate cone), each with its gallery (a U round the well's north, "
                     "east and south) and its landing hall west of the well; three two-storey stair halls west of "
                     "the landings, alternating south, north, south. L1: the door hall (the D3 door), the commons, "
                     "the store room. L2: the cabinet of curiosities, the dormitory, the mirror room. L3: the conjury "
                     "and the scrying room (the two ward pylons), the vault behind its door of light, the disk "
                     "alcoves. L4: the laboratory and the study (MM7 7d14). x east, y north. Written by "
                     "output/studio_cal/dd07/tools/gen.py."}


# ---------------------------------------------------------------------------------------------------------------------
# objects.yml

# Placed monsters: room -> group, [(row, (x, y), facing)]; 30 (D-9.3, D-39 Q2).
PLACED = [
    ('well_foot', 10, [(ADEPT, (-256, 0), 180), (ADEPT, (0, 256), 180), (ADEPT, (0, -256), 180)]),
    ('ring1', 11, [(ADEPT, (640, 640), 180), (ADEPT, (640, -640), 180)]),
    ('commons', 12, [(ADEPT, (-384, -1400), 90), (ADEPT, (384, -1400), 90)]),
    ('ring2', 13, [(ADEPT, (0, -736), 180), (ADEPT, (736, 320), 180), (MAGUS, (-640, 704), 0)]),
    ('cabinet', 14, [(MAGUS, (1408, -384), 180), (MAGUS, (1408, 256), 180)]),
    ('dormitory', 15, [(ADEPT, (384, -1300), 90), (ADEPT, (1344, -1300), 90)]),
    ('ring3', 16, [(EYE, (0, 736), 270), (ADEPT, (736, -320), 180)]),
    ('conjury', 17, [(MAGUS, (-704, 1280), 270), (MAGUS, (-192, 1344), 270), (ADEPT, (0, 1664), 270)]),
    ('scrying', 18, [(MAGUS, (512, 1216), 270), (MAGUS, (1664, 1280), 270), (ADEPT, (1216, 1216), 270)]),
    ('vault', 19, [(MYSTIC, (1344, -256), 180)]),
    ('ring4', 20, [(MAGUS, (640, 640), 180), (MAGUS, (-640, 704), 0), (ADEPT, (640, -640), 180)]),
    ('lab', 21, [(MYSTIC, (0, 1344), 270)]),
    ('study', 22, [(MYSTIC, (-2304, 704), 0), (MYSTIC, (-1536, 704), 180), (EYE, (-1920, 1024), 270)]),
]

START = (-2496, 0)


def on_wall(rid, at, inset=12):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    x, y = at
    side = min((x - x0, 'w'), (x1 - x, 'e'), (y - y0, 's'), (y1 - y, 'n'))[1]
    return {'w': (x0 + inset, y), 'e': (x1 - inset, y), 's': (x, y0 + inset), 'n': (x, y1 - inset)}[side]


# Sconces (scon100, wall-mounted) on rectangle rooms' walls, and on the galleries' outer walls.
SCONCES = [
    ('door_hall', (-2752, 160)), ('door_hall', (-2304, 256)), ('door_hall', (-1600, 256)),
    ('door_hall', (-1600, -256)),
    ('stair2', (-2752, 0)), ('stair2', (-2048, -256)), ('stair2', (-2048, 256)),
    ('stair3', (-2752, 0)), ('stair3', (-1600, -256)), ('stair3', (-1600, 256)),
    ('stair4', (-2752, 0)), ('stair4', (-2240, -256)), ('stair4', (-1408, 256)),
    ('commons', (-704, -1440)), ('commons', (704, -1440)),
    ('store', (1664, 256)),
    ('cabinet', (1088, -640)), ('cabinet', (1088, -160)), ('cabinet', (1536, 640)),
    ('dormitory', (-448, -1184)), ('dormitory', (1984, -1300)), ('dormitory', (768, -1088)),
    ('mirror', (-832, -1856)),
    ('conjury', (-960, 1472)), ('conjury', (-384, 1856)),
    ('scrying', (1856, 1472)), ('scrying', (1088, 1088)),
    ('vault', (1472, 576)), ('vault', (1472, -576)),
    ('alcoves', (2240, 384)),
    ('stair12', (-2752, -704)), ('stair12', (-1216, -896)),
    ('stair23', (-1216, 896)), ('stair23', (-2752, 512)),
    ('stair34', (-2752, -704)), ('stair34', (-1216, -896)),
    ('roof_stair', (-256, -1280)),
]
# The galleries: sconces on the outer walls (y = +-960, x = 960) between the doors.
RING_SCONCES = [(-864, 960, 'n'), (864, 960, 'n'), (960, 640, 'e'), (960, -640, 'e'), (-416, -960, 's'),
                (640, -960, 's')]


def check_sconces():
    for rid, at in SCONCES:
        p = on_wall(rid, at)
        for oid, (pt, width, a, b, z) in OPEN_AT.items():
            if rid not in (a, b) or abs(z - ROOMS[rid]['floor']) > 400:
                continue
            if math.dist(p, pt) < width / 2 + 96:
                raise SystemExit(f'sconce in {rid} at {p} too near opening {oid}')


def objects_yml():
    doors = []

    def door(did, op, notes, **kw):
        d = {'id': did, 'opening': op, 'kind': 'slide_up', 'thickness': 24,
             'surface': S('gcstdoor', 128, 256, fit=True), 'back_surface': S('gcstdoor', 128, 256, fit=True),
             'speed': 192, 'notes': notes}
        d.update(kw)
        doors.append(d)

    door('door:commons', 'open:ring1_commons', "The commons' stone door.")
    door('door:store', 'open:ring1_store', "The store room's stone door.")
    door('door:cabinet', 'open:ring2_cabinet', "The cabinet's stone door.")
    door('door:dormitory', 'open:cabinet_dorm', "The dormitory's door.")
    door('door:conjury', 'open:ring3_conjury', "The conjury's door.")
    door('door:scrying', 'open:ring3_scrying', "The scrying room's door.")
    door('door:lab', 'open:ring4_lab', "The laboratory's door.")
    door('door:study', 'open:lab_study', "The study's door from the laboratory.")
    door('door:study_landing', 'open:study_stair4', "The study's door on the top landing.")
    doors.append({'id': 'door:ward', 'opening': 'open:ring3_vault', 'kind': 'slide_down', 'fold': True,
                  'surface': WARD, 'tile': True, 'speed': 192,
                  'notes': "The vault's door of light (D-39 Q4): XD-04's ward (xwward, translucent), fed by the two "
                           "pylons' beams; it fades into the floor when both pylons are broken and stays open."})

    lifts = [{'id': 'lift:disc', 'room': 'room:well_foot', 'at': F(*DISC), 'size': F(DISC_SIZE, DISC_SIZE),
              'travel': 1920, 'thickness': 16, 'speed': 240, 'state': 'up', 'surface': BLACK,
              'notes': "The floating disc: a slab of black stone 16 thick riding the well between the top floor (up, "
                       "1,920, where it rests at load, level with the gallery's opening) and the well's foot (down). "
                       "Its two levers stand beside the east openings, at the top and at the foot."}]
    switches = [
        {'id': 'switch:disc_top', 'room': 'room:well_foot', 'kind': 'lever', 'at': F(448, LEVER_Y), 'height': 2040,
         'notes': "The disc's lever on the rail post beside the top floor's opening (from the disc or the gallery)."},
        {'id': 'switch:disc_foot', 'room': 'room:well_foot', 'kind': 'lever', 'at': F(448, LEVER_Y), 'height': 120,
         'notes': "The call lever at the well's foot, beside the east arch."},
    ]

    chests = [
        {'id': 'chest:store', 'room': 'room:store', 'at': F(1600, -256), 'kind': 'ch1', 'treasure_level': 4, 'random_items': 3, 'gold': 1200, 'notes': "The store room's chest of reagents."},
        {'id': 'chest:dormitory', 'room': 'room:dormitory', 'at': F(1920, -1600), 'kind': 'ch1', 'treasure_level': 4, 'random_items': 2, 'gold': 1400, 'notes': "The mages' chest at the dormitory's end."},
        {'id': 'chest:study', 'room': 'room:study', 'at': F(-2688, 576), 'kind': '7gt002', 'treasure_level': 4, 'random_items': 3, 'gold': 2400, 'notes': "The Archmagus's chest."},
        {'id': 'chest:desk', 'room': 'room:study', 'at': F(-1920, 1344), 'floor_height': 1920 + 80, 'kind': 'gt002',
         'facing': 'w', 'size': Flow([96, 64, 48]), 'random_items': 0, 'gold': 0, 'items': ['ellingers_letter'],
         'notes': "The Archmagus's writing box on his desk, its front to the room (south): Ellinger's sealed letter is "
                  "its item (D-90, 2026-11-22; A3's q-d18.letter sets letter_found and the autonote)."},
        {'id': 'chest:case_griffin', 'room': 'room:cabinet', 'at': F(1928, 320), 'floor_height': 640 + 160,
         'kind': 'gt002', 'facing': 'n', 'size': Flow([96, 64, 56]),
         'random_items': 0, 'gold': 0, 'items': ['golden_griffin'],
         'notes': "The last case's lidded box on top, its front to the room (west): the Golden Griffin is its item "
                  "(D-90, 2026-11-22; A3's q-d20.griffin sets griffin_found)."},
    ]
    ground_items = [
        {'id': 'item:jewel', 'room': 'room:vault', 'item': 'jewel_of_ages', 'at': F(1664, 0), 'floor_height': 1280 + 112,
         'notes': "The Jewel of Ages on its stand of black glass, a ground item to pick up (D-90, 2026-11-22)."},
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

    for i, (rid, at) in enumerate(SCONCES, 1):
        deco(f'sconce_{i:02d}', rid, 'scon100', on_wall(rid, at), height=176)
    deco('roof_sconce_head', 'roof_stair', 'scon100', on_wall('roof_stair', (1472, -1088)), height=176,
         floor_height=ROOF_HEAD, notes="A sconce on the head's north wall, beside the hatch.")
    for f in (1, 2, 3, 4):
        for j, (x, y, side) in enumerate(RING_SCONCES, 1):
            p = {'n': (x, y - 12), 's': (x, y + 12), 'e': (x - 12, y)}[side]
            deco(f'ring{f}_sconce_{j}', f'ring{f}', 'scon100', p, height=176)
    # The ward pylons' crystals (destructibles) on their black pillars.
    deco('pylon_w', 'conjury', 'crystl0', (-576, 1600), floor_height=1280 + 128,
         notes="The west pylon's crystal: it feeds a beam to the vault's door of light.")
    deco('pylon_e', 'scrying', 'crystl0', (1472, 1600), floor_height=1280 + 128,
         notes="The east pylon's crystal.")
    for i, x in enumerate((576, 896, 1216), 1):
        deco(f'ball_{i}', 'scrying', 'mcryst01', (x, 1792), floor_height=1280 + 96, notes="A crystal ball.")
    # The laboratory: the vat, floor braziers under the retorts, chandelier; the study's chandelier and candles.
    deco('vat', 'lab', 'cauld00', (0, 1888), floor_height=1920 + 88, notes="The Bubbling Vat on its bench.")
    deco('lab_brazier_w', 'lab', 'flamb00', (-896, 1856))
    deco('lab_brazier_e', 'lab', 'flamb00', (896, 1856))
    deco('lab_chandelier', 'lab', 'dec27', (0, 1536))
    deco('study_chandelier', 'study', 'dec27', (-1920, 960))
    deco('study_candle', 'study', 'cndlab0', (-1824, 1344), floor_height=1920 + 80)
    # The jewel's vault and the alcoves: grave goods of mages (gold, goblets).
    deco('vault_goblet_1', 'vault', '7dec48', (1792, 512))
    deco('vault_goblet_2', 'vault', '7dec46', (1792, -512))
    # The commons: plates and a goblet on the table; a pair of casks by the wall.
    deco('commons_plates', 'commons', 'dec36', (-160, -1664), floor_height=72)
    deco('commons_goblet', 'commons', '7dec48', (160, -1664), floor_height=72)
    deco('commons_cask_1', 'commons', '7dec21', (640, -1728))
    deco('commons_cask_2', 'commons', '7dec21', (544, -1728))
    # The store room (store: true): barrels, sacks and jars in clumps along the walls.
    for i, (d, at) in enumerate([('bigbarel', (1152, 448)), ('bigbarel', (1248, 448)), ('smlbarel', (1344, 448)),
                                 ('floursac', (1152, -448)), ('bag01', (1248, -448)), ('bag_A', (1344, -448)),
                                 ('bigbarel', (1600, 448)), ('smlbarel', (1600, 352))], 1):
        deco(f'store_{i}', 'store', d, at)
    # The dormitory: a pair of sacks (robes in a bundle) by the beds' ends.
    deco('dorm_sack_1', 'dormitory', 'bag01', (-384, -1792))
    deco('dorm_sack_2', 'dormitory', 'bag01', (-384, -1696))

    lights = []

    def light(name, rid, at, height, radius, color, **kw):
        d = {'id': f'light:{name}', 'room': f'room:{rid}', 'at': F(*at), 'height': height, 'radius': radius,
             'color': F(*color)}
        d.update(kw)
        lights.append(d)

    warm = (230, 190, 140)
    cool = (180, 190, 210)
    for rid, r in ROOMS.items():
        if rid in ('well_foot',) or rid.startswith('ring'):
            continue
        if rid == 'roof_stair':
            # A lamp over the foot beside the flight and one over the head under the hatch (each measured from the
            # floor under it: the hall's middle is over the steps).
            light('roof_stair_1', rid, (0, -1280), 420, 1200, warm, floor_height=1920)
            light('roof_stair_2', rid, (1184, -1180), 200, 900, warm, floor_height=ROOF_HEAD)
            continue
        x0, y0, x1, y1 = r['rect']
        w, d = x1 - x0, y1 - y0
        pts = [((x0 + x1) // 2, (y0 + y1) // 2)]
        if max(w, d) > 1400:
            pts = ([(x0 + w // 4, (y0 + y1) // 2), (x1 - w // 4, (y0 + y1) // 2)] if w >= d else
                   [((x0 + x1) // 2, y0 + d // 4), ((x0 + x1) // 2, y1 - d // 4)])
        h = min(r['ceiling'] - r['floor'] - 96, 420)
        col = cool if rid.startswith('stair') else warm
        if rid.startswith('stair') and rid[-2:].isdigit():
            pts = [((x0 + x1) // 2, (y0 + y1) // 2)]
            h = 520
        for i, at in enumerate(pts, 1):
            light(f'{rid}_{i}' if len(pts) > 1 else rid, rid, at, h, 1500 if max(w, d) > 1400 else 1000, col)
    for f in (1, 2, 3, 4):
        for j, at in enumerate([(-640, 704), (704, 704), (736, 0), (704, -704), (-640, -704)], 1):
            light(f'ring{f}_{j}', f'ring{f}', at, H[f] - 112, 1100, warm)
    # The well: pale light falling from the cone, and a lamp at each floor.
    light('cone', 'well_foot', (0, 0), 2880, 2400, (200, 215, 240), brightness=28,
          notes="The pale light from the cone, four floors up.")
    for f in (1, 2, 3, 4):
        light(f'well_{f}', 'well_foot', (-160, 0), Z[f] + 400, 1200, (190, 200, 225))
    # The pylons' beams (cool blue), each put out with its pylon; the door of light's glow.
    light('beam_w', 'conjury', (-576, 1600), 320, 900, (140, 170, 255), brightness=26)
    light('beam_e', 'scrying', (1472, 1600), 320, 900, (140, 170, 255), brightness=26)
    light('ward', 'ring3', (736, 0), 300, 700, (200, 140, 220), brightness=24,
          notes="The door of light's glow on the gallery.")
    light('fountains', 'lab', (0, 1536), 200, 900, (150, 200, 230))

    sounds = [
        {'id': 'sound:tower_bed', 'room': 'room:well_foot', 'at': F(-128, -128), 'height': 1472,
         'sound': 'xeen_amb_tower', 'radius': 5120, 'inner_radius': 2560, 'volume': 0.35, 'pan': False,
         'notes': "The tower's bed (AU, 'the towers of Mok'): chimes up the well, one source heard on every floor, centred (D-48)."},
    ]
    exits = [
        {'id': 'exit:d3_door', 'room': 'room:door_hall', 'at': F(-2752, 0), 'size': F(192, 320),
         'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:d3_door',
         'notes': "The tower's west door, from inside: out to D3's knoll before it."},
    ]
    destructibles = [
        {'id': 'destructible:pylon_w', 'of': 'deco:pylon_w', 'hp': 40, 'material': 'glass',
         'notes': "The west ward pylon's crystal: a blow or a click breaks it."},
        {'id': 'destructible:pylon_e', 'of': 'deco:pylon_e', 'hp': 40, 'material': 'glass',
         'notes': "The east ward pylon's crystal."},
    ]

    return {'format': 0,
            'start': {'room': 'room:door_hall', 'at': F(*START), 'facing': 'e',
                      'notes': "In the door hall 256 inside the west door, at the first stair's foot, facing east "
                               "toward the well."},
            'arrivals': [FlowDict(entrance='entrance:d3_door', room='room:door_hall', at=F(*START), facing='e',
                                  notes="In the door hall about 256 inside the door at the stair's foot, facing east "
                                        "(D3's tower door arrives here).")],
            'doors': doors, 'lifts': lifts, 'switches': switches, 'sounds': sounds, 'lights': lights,
            'chests': chests, 'monsters': monsters, 'items': ground_items, 'decorations': decos, 'exits': exits,
            'destructibles': destructibles, 'relations': []}


# ---------------------------------------------------------------------------------------------------------------------
# wiring.yml


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def snd(name, x, y, z):
    return {'lua': f'evt.PlaySoundName("{name}", {x}, {y}, {z})'}


WARD_TEXT = "A wall of light hums in the doorway. Two beams feed it, from the west and from the east."


def wiring_yml():
    ev = []

    def e(**kw):
        ev.append(kw)

    e(id='evt:arrive', preset='text', trigger='timer', every=1, once=True, seconds=6,
      text="The Great Eastern Tower. Far above, light falls down an open well; something hums up there.",
      notes="Say where the party is (a one-shot timer: the party arrives standing in the door hall).")
    e(id='evt:exit', preset='exit', source='exit:d3_door', title='Tower door',
      notes="Out to D3 (A5's entrance:dd07_door (15360, 9216, 1888) facing west, before the tower's door): the game's "
            "own leave window (D-24); 'Exit the Great Eastern Tower?' (dark/aaze0065:0) is its meaning.")
    for did, title in (('commons', 'Door'), ('store', 'Door'), ('cabinet', 'Door'), ('dormitory', 'Door'),
                       ('conjury', 'Door'), ('scrying', 'Door'), ('lab', 'Door'), ('study', 'Door'),
                       ('study_landing', 'Door')):
        e(id=f'evt:door_{did}', preset='door', source=f'door:{did}', title=title)
    # The ward and its two pylons (D-39 Q4)
    e(id='evt:ward', preset='door', source='door:ward', title='Door of light', action='open',
      condition={'map_var': {'name': 'pylons', 'equals': 2}}, locked_text=WARD_TEXT,
      notes="state:pylon_w, state:pylon_e: the door's click explains both beams; once both pylons are broken it "
            "has faded (evt:ward_fade) and stays open.")
    for side, name in (('w', 'west'), ('e', 'east')):
        e(id=f'evt:pylon_{side}', preset='script', source=f'platform:pylon_{side}', title='Ward pylon',
          condition={'not': {'destroyed': f'destructible:pylon_{side}'}},
          effects=[{'text': "You strike the crystal with all your strength."},
                   {'destroy': f'destructible:pylon_{side}'}],
          else_effects=[{'text': f"The {name} pylon's crystal lies in shards."}],
          notes=f"The {name} ward pylon: a crystal on a black pillar, its beam running to the vault. A click (or a "
                "blow, or a missile) breaks it; a timer counts it.")
        e(id=f'evt:pylon_{side}_out', preset='script', trigger='timer', every=1, once=True,
          condition={'destroyed': f'destructible:pylon_{side}'},
          effects=[{'add': {'var': {'map_var': 'pylons'}, 'value': 1}}, {'lights_off': f'light:beam_{side}'},
                   {'text': f"The {name} pylon shatters. Its beam goes out."}],
          notes=f"The {name} pylon broken (a timer sees its destructible broken, by a click, a blow or a missile): "
                "one beam fewer.")
    e(id='evt:ward_fade', preset='script', trigger='timer', every=1, once=True,
      condition={'map_var': {'name': 'pylons', 'equals': 2}}, opens=['door:ward'],
      effects=[{'lights_off': 'light:ward'},
               {'text': "In the vault's doorway the wall of light flickers and fades."}],
      notes="Both beams out: the door of light sinks away and stays open.")
    e(id='evt:ward_load', preset='script', trigger='load', condition={'map_var': {'name': 'pylons', 'equals': 2}},
      opens=['door:ward'], effects=[{'lights_off': 'light:ward'}],
      notes="On every later load the door of light stays gone.")
    # The vault and the alcoves
    e(id='evt:disks', preset='script', source='platform:experiment', title='Disc',
      condition={'not': {'qbit': 'tower_disks'}},
      effects=[{'give_item': ITEMS['energy_disk']}, {'give_item': ITEMS['energy_disk']}, hook('q-d18.l3_disks')],
      else_effects=[hook('q-d18.l3_disks')],
      notes="A3's q-d18.l3_disks: the hook's map_gives says the map hands over the 2 Energy Disks 12334 (here, once, "
            "until tower_disks 113362 is set); the hook sets the bit and says 'Disc. Two Energy Disks ...', after "
            "that 'Loose wires where the disks were.'; 'Disc' is dark/aaze0067:1.")
    # The study
    e(id='evt:letter', preset='chest', source='chest:desk', title='Chest', effects=[hook('q-d18.letter')],
      notes="D-90: Ellinger's letter 12361 is the writing box's item; A3's q-d18.letter (once) sets letter_found "
            "113363 and autonote 4581 on the status line.")
    e(id='evt:book_fantastic', preset='script', source='platform:book_fantastic', title='Book of Fantastic Knowledge',
      effects=[hook('q-d18.fantastic_book')],
      notes="A3's q-d18.fantastic_book decides for the reading member (+2 Intellect once, player bit 11337; after: "
            "'Your intellect is already fantastic!', dark/aaze0068:6).")
    e(id='evt:book_power', preset='script', source='platform:book_power', title='Book of Great Power',
      effects=[hook('q-d18.great_power_book')],
      notes="A3's q-d18.great_power_book: the final refusal, every member, every time (D-39 Q3; dark/aaze0068:7).")
    e(id='evt:chest_study', preset='chest', source='chest:study', title='Chest')
    # The laboratory
    e(id='evt:fountain_min', preset='script', source='platform:fountain_min', title='Fountain of Minimal Abilities',
      effects=[snd('xeen_spring_drink', -576, 1536, 1984), hook('q-d18.minimal_fountain')],
      notes="A3's q-d18.minimal_fountain decides for the drinking member (+1 to every statistic once, player bit "
            "11336; after: 'The water is cool and refreshing.'; dark/aaze0068:1-3). AU's xeen_spring_drink.")
    e(id='evt:fountain_life', preset='script', source='platform:fountain_life', title='Fountain of Life',
      lua='AddValue(CurrentHealth, 1000)\nevt.StatusText("Fountain of Life. The water closes your wounds.", 3)',
      notes="dark/aaze0068:4: the Fountain of Life heals the drinking member (any time).")
    e(id='evt:vat', preset='text', source='platform:vat', title='Bubbling Vat',
      text="The Bubbling Vat. It smells of copper and burnt sugar. Nobody is drinking from it.",
      notes="dark/aaze0068:0: the vat is dressing (D-39 Q3); the source's ageing water is not given.")
    # The disc (state:disc_lever)
    disc_sound = snd('xeen_lift', DISC[0], DISC[1], 960)
    e(id='evt:disc_top', preset='switch', source='switch:disc_top', title='Lever', toggles=['lift:disc'],
      effects=[{'set': {'var': {'map_var': 'disc_sent'}, 'value': 1}}, disc_sound],
      text="The disc hums and drifts along the well.",
      notes="state:disc_lever: the lever on the rail post at the top sends the disc down (with whoever stands on it) "
            "or calls it back up; once used, the foot's lever answers too.")
    e(id='evt:disc_foot', preset='switch', source='switch:disc_foot', title='Lever', toggles=['lift:disc'],
      condition={'map_var': 'disc_sent'}, locked_text="The disc does not answer from below.",
      effects=[disc_sound], text="The disc hums and drifts along the well.",
      notes="The call lever at the well's foot: it works once the disc has been sent from the top (a map variable).")
    # L2
    e(id='evt:griffin', preset='chest', source='chest:case_griffin', title='Cabinet',
      effects=[hook('q-d20.griffin')],
      notes="D-90: the Golden Griffin 12351 is the curio box's item; A3's q-d20.griffin (once) sets griffin_found "
            "113403 on the status line.")
    for i in (1, 2):
        e(id=f'evt:case_{i}', preset='text', source=f'platform:case_{i}', title='Case',
          text=["Labels in a neat hand: 'Toad, two-headed. Thaumic value: considerable.' The toad is long gone.",
                "Labels: 'Feather, phoenix (doubtful).' 'Tooth, unknown.' 'Rock.' Nothing worth taking."][i - 1])
    e(id='evt:mirror', preset='text', source='platform:mirror', title='Mirror', text="The mirror does not respond.",
      notes="dark/aaze0066:1 (D-39 Q5: flavour only; the source's 'Where to?' / 'Destination Unknown' dropped).")
    for i in range(1, 5):
        e(id=f'evt:bed_{i}', preset='text', source=f'platform:bed_{i}', title='Bed', text="Nothing here.",
          notes="dark/aaze0067:2.")
    e(id='evt:chest_dormitory', preset='chest', source='chest:dormitory', title='Chest')
    # L1
    e(id='evt:lore', preset='text', source='platform:lore', title='Books',
      text="Lore books: 'On the Floating of Persons', 'Wells and their Uses', 'Against Stairs'.")
    e(id='evt:chest_store', preset='chest', source='chest:store', title='Chest')
    # The roof stair (D-58)
    e(id='evt:roof_trapdoor', preset='script', source='platform:roof_hatch', title='Roof trapdoor',
      lua=('if not XeenQuests.hook("d7.roof_dd07") then\n'
           '    return\n'
           'end\n'
           'evt.MoveToMap(27136, -6144, 1024, 1024, 0, 0, 0, 1, "xeen_d7.blv")'),
      notes="D-58: A3's d7.roof_dd07 checked first (needs m30.done; else its 'The trapdoor is shut fast.'), then "
            "the game's standard entrance window (F16, 2026-11-22; was D-66's Yes/No) in place of the old "
            "question; OK goes one way up to D7's entrance:dd07_roof (27136, -6144, "
            "1024) facing 1024 at once (D7 is indoor: no leave window; the coordinates are D7's named arrival, "
            "written out because the move waits on the answer).")
    # L3: the scrying room's balls
    for i in (1, 2, 3):
        e(id=f'evt:ball_{i}', preset='text', source=f'platform:ball_{i}', title='Crystal ball',
          text=["Clouds, and under them a desert going on for ever.", "A dark sun over a dark land.",
                "Your own faces, looking back, a little older."][i - 1])
    ev.sort(key=lambda x: x['id'])
    return {'format': 0, 'variables': ['pylons', 'disc_sent'], 'events': ev}


# ---------------------------------------------------------------------------------------------------------------------
# project.yml


def project_yml(level):
    return {
        'format': 0, 'id': 'xeen_dd07', 'name': 'Eastern Tower', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-07', 'units': FlowDict(plan_grid=512),
        'extent': FlowDict(footprint_cells=F(11, 8), climbs='e'),
        'map_stats': {
            'id': MAP_STATS_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 4,
            'trap_dice': 4, 'perception_difficulty': 8, 'refill_days': 672, 'music': MUSIC, 'environment': 'stone',
            'lock_difficulty': 8,
            'slots': [
                FlowDict(monster='Xeen Floating Mage', tier=0, per_marker=F(1, 2), weight=70),
                FlowDict(monster='Xeen Eye', tier=0, per_marker=F(1, 1), weight=30),
            ],
        },
        'neighbours': [{
            'id': 'exit:d3_door', 'to': 'xeen_d3.odm', 'kind': 'door', 'arrival': D3_ENTRANCE,
            'arrival_hint': "On D3's knoll in front of the Great Eastern Tower's west door (A5's entrance:dd07_door, "
                            "(15360, 9216, 1888) facing west).",
            'notes': "D3 installed (A5). The way out names D3's named arrival entrance:dd07_door; the facing comes with "
                     "it. D3's door (q-d18.tower_door, the Key to the Eastern Tower 12340) names this map's arrival "
                     "entrance:d3_door: in the door hall (-2496, 0, 0) facing east."},
            {'id': 'exit:d7_roof', 'to': 'xeen_d7.blv', 'kind': 'roof', 'one_way': True, 'arrival': 'entrance:dd07_roof',
             'arrival_hint': "D7 The Skyroads, by the Eastern Tower's hatch at the East Rest Stop (A6's "
                             "entrance:dd07_roof (27136, -6144, 1024) facing 1024).",
             'notes': "D-58: the roof trapdoor (evt:roof_trapdoor), one way up after m30.done; D7 installed (A6), "
                      "live."}],
        'qbits': dict(sorted(QBITS.items())),
        'items': dict(ITEMS),
        'notes': f"Xeen design brief, level {level}: DD-07 the Great Eastern Tower, on D3 (Sandcaster and the Aging "
                 "Forest), Act IV, class M (MU-6 graph devdocs/xeen/mockups/act4_graphs/dd07.graph.yml, decider D-39 "
                 "in mockups/act4_a7_decisions.md). Q-D18 The Jewel of Ages (the vault on L3 behind the door of "
                 "light: q-d18.jewel, q-d18.l3_disks; Ellinger's letter in the top floor's study: q-d18.letter), "
                 "Q-D20's Golden Griffin in the cabinet on L2 (q-d20.griffin); L4's gifts by A3's hooks "
                 "(q-d18.minimal_fountain, q-d18.fantastic_book, q-d18.great_power_book). Monsters, all placed and "
                 "hostile in groups 10-22 by room: 15 Floating Adept 11203 (28), 9 Floating Magus 11204 (38), 4 Mystic "
                 "Mage 11200 (45), 2 Floating Eye 11570 (40): 30 (D-9.3). Rest encounters 10 % from the map's own "
                 "hostile rows: slot 1 Xeen Floating Mage tier 0 (Mystic Mage only: the Adept and Magus tiers are "
                 "placed only), slot 2 Xeen Eye tier 0 (Floating Eye only). Map card 9156, music 43, treasure 4. Map "
                 "qbits 118030-118039: none used (map variables do the pylons and the disc). A3's bits named. The way "
                 "out to D3 (installed) is live by its named arrival entrance:dd07_door.",
    }


# ---------------------------------------------------------------------------------------------------------------------
# plan.yml

PLAN_SPACES = [
    ('door_hall', 'room', 'M', "The arrival (entrance:d3_door) inside the west door, at the foot of the first stair. "
                               "Quiet (D-11.3). Wall sconces; the well's foot through an arch.", None),
    ('well_foot', 'room', 'M', "The levitation well: an open shaft from the ground floor to the slate cone, railed "
                                "windows on every floor, light falling from the cone; the floating disc rides it from "
                                "the top floor to the foot. Three adepts float in the light.", None),
    ('ring1', 'corridor', 'M', "The ground floor's gallery round the well's north, east and south sides.", None),
    ('commons', 'room', 'M', "A refectory and reading room: the long table, lore books on shelves.", None),
    ('store', 'room', 'S', "A dead end with a chest: reagents in jars, sacks and barrels in clumps (a storeroom).",
     4),
    ('stair12', 'room', 'M', "The first stair hall: twenty steps from the door hall to the second landing.", None),
    ('stair2', 'room', 'S', "The second floor's landing hall.", None),
    ('ring2', 'corridor', 'M', "The second gallery; mages float out over the well to cast from the far side.", None),
    ('cabinet', 'room', 'M', "Glass cases of labelled oddities; the Golden Griffin in the last (q-d20.griffin).",
     None),
    ('dormitory', 'room', 'M', "Narrow beds in a row; the mages' chest.", 4),
    ('mirror', 'room', 'S', "A tall dead mirror (xkmirror): 'The mirror does not respond.'", None),
    ('stair23', 'room', 'M', "The second stair hall: twenty steps to the third landing.", None),
    ('stair3', 'room', 'S', "The third floor's landing hall.", None),
    ('ring3', 'corridor', 'M', "The third gallery; the vault's door of light on its east side, humming.", None),
    ('conjury', 'room', 'M', "A summoning room; the west ward pylon (a destructible crystal on a pillar).", None),
    ('scrying', 'room', 'M', "Crystal balls on stands round a black pool; the east ward pylon.", None),
    ('vault', 'room', 'M', "Behind the door of light: the Jewel of Ages on a stand of black glass (q-d18.jewel).",
     None),
    ('alcoves', 'room', 'S', "A mage's experiment of wires and two Energy Disks (q-d18.l3_disks).", None),
    ('stair34', 'room', 'M', "The third stair hall: twenty steps to the top landing.", None),
    ('stair4', 'room', 'S', "The top landing hall; doors to the gallery and the study.", None),
    ('ring4', 'corridor', 'M', "The gallery under the cone; the disc's landing in its east rail (the floating disc "
                               "rests there at load; its lever sends it down).", None),
    ('lab', 'room', 'M', "Benches, the Bubbling Vat, the Fountain of Minimal Abilities (+1 to every statistic once "
                         "per character) and the Fountain of Life (heals).", None),
    ('study', 'room', 'M', "The Archmagus's study: Ellinger's letter on the desk (q-d18.letter), the Book of "
                           "Fantastic Knowledge and the Book of Great Power, the master's chest.", 4),
    ('roof_stair', 'corridor', 'S', "The roof stair (D-58): one flight up to a trapdoor in the ceiling, one way up to "
                                    "D7's entrance:dd07_roof after m30.done (A3's d7.roof_dd07: 'The trapdoor is shut "
                                    "fast.' before); live since D7's install.", None),
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
        xs = [p[0] for p in r['outline']]
        ys = [p[1] for p in r['outline']]
        s = {'id': f'room:{sid}', 'name': r['name'], 'kind': kind, 'size': size,
             'extent': F(max(xs) - min(xs), max(ys) - min(ys))}
        s['floor'] = r['floor']
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

    links = [
        L('hall_well', 'door_hall', 'well_foot', 'open'),
        L('hall_ring1', 'door_hall', 'ring1', 'open'),
        L('hall_ring1_s', 'door_hall', 'ring1', 'open'),
        L('well_ring1', 'well_foot', 'ring1', 'open'),
        L('ring1_commons', 'ring1', 'commons', 'door'),
        L('ring1_store', 'ring1', 'store', 'door'),
        L('stair_1_2', 'door_hall', 'stair2', 'stairs', rise=640,
          notes="The first stair hall (room:stair12): its foot beside the door, its head on the second landing."),
        L('stair2_ring2', 'stair2', 'ring2', 'open'),
        L('stair2_ring2_s', 'stair2', 'ring2', 'open'),
        L('ring2_cabinet', 'ring2', 'cabinet', 'door'),
        L('cabinet_dorm', 'cabinet', 'dormitory', 'door'),
        L('dorm_mirror', 'dormitory', 'mirror', 'open'),
        L('mirror_ring2', 'mirror', 'ring2', 'open'),
        L('stair_2_3', 'stair2', 'stair3', 'stairs', rise=640, notes="The second stair hall (room:stair23)."),
        L('stair3_ring3', 'stair3', 'ring3', 'open'),
        L('stair3_ring3_s', 'stair3', 'ring3', 'open'),
        L('ring3_conjury', 'ring3', 'conjury', 'door'),
        L('ring3_scrying', 'ring3', 'scrying', 'door'),
        L('conjury_scrying', 'conjury', 'scrying', 'open'),
        L('ward', 'ring3', 'vault', 'door', condition={'map_var': 'pylons'},
          notes="The door of light: it fades when both ward pylons are broken (state:pylon_w, state:pylon_e)."),
        L('vault_alcoves', 'vault', 'alcoves', 'open'),
        L('stair_3_4', 'stair3', 'stair4', 'stairs', rise=640, notes="The third stair hall (room:stair34)."),
        L('stair4_ring4', 'stair4', 'ring4', 'open'),
        L('stair4_ring4_s', 'stair4', 'ring4', 'open'),
        L('ring4_lab', 'ring4', 'lab', 'door'),
        L('lab_study', 'lab', 'study', 'door'),
        L('study_stair4', 'study', 'stair4', 'door'),
        L('ring4_roof', 'ring4', 'roof_stair', 'open',
          notes="The roof stair (D-58); its trapdoor leads one way up to D7 (exit:d7_roof), live to D7 after "
                "m30.done."),
        L('disc_ring4', 'ring4', 'well_foot', 'open',
          notes="The disc's landing: the opening in the gallery's east rail onto the floating disc."),
        L('disc', 'well_foot', 'ring4', 'lift', rise=1920,
          notes="The floating disc (lift:disc): up at load; its lever at the top sends it down, then the foot's "
                "lever answers too."),
    ]
    plan = {
        'format': 0, 'level': min(level, 'L3'),
        'pitch': "The Great Eastern Tower: four floors of galleries round an open well that rises from the ground "
                 "floor to the slate cone, the mages floating across it. One stair winds up the west side; from the "
                 "top a floating disc rides the well back down. On the third floor the mages' vault hides behind a "
                 "door of light fed by two crystal pylons; on the top floor the Archmagus's study and laboratory.",
        'purpose': "Q-D18 The Jewel of Ages (the vault: the jewel and two Energy Disks; Ellinger's letter in the "
                   "study, the Archmage promotion through Nasir), Q-D20's Golden Griffin, L4's fountain (+1 all) and "
                   "book (+2 Intellect). 30 monsters at 28-45 (Floating Adepts, Floating Magi, Mystic Mages, Floating "
                   "Eyes), treasure 4.",
        'mood': "Cool green-grey stone and grey cobbles, pale light falling down the well, the hum of the pylons; warm "
                "brown stone and wood in the mages' own rooms at the top.",
        'datum': 'arrival',
        'spaces': spaces,
        'links': links,
        'loops': [
            {'id': 'loop:l1', 'spaces': ['room:door_hall', 'room:well_foot', 'room:ring1'],
             'notes': "Round the ground floor's well: the arch and the gallery."},
            {'id': 'loop:l2', 'spaces': ['room:ring2', 'room:cabinet', 'room:dormitory', 'room:mirror'],
             'notes': "Round L2: the gallery, the cabinet, the dormitory, the mirror room."},
            {'id': 'loop:l3', 'spaces': ['room:ring3', 'room:conjury', 'room:scrying'],
             'notes': "The two pylon rooms joined by the passage in the wall."},
            {'id': 'loop:l4', 'spaces': ['room:ring4', 'room:lab', 'room:study', 'room:stair4'],
             'notes': "Round the top floor through the laboratory and the study."},
            {'id': 'loop:disc', 'spaces': ['room:door_hall', 'room:stair2', 'room:stair3', 'room:stair4',
                                           'room:ring4', 'room:well_foot'],
             'notes': "Up the stair, down on the floating disc."},
        ],
        'entrances': [
            {'id': 'entrance:d3_door', 'space': 'room:door_hall', 'kind': 'both', 'neighbour': 'exit:d3_door',
             'facing': 'e',
             'how': "From D3's tower door (q-d18.tower_door, the Key to the Eastern Tower): in the door hall about 256 "
                    "inside the door at the stair's foot, facing east; the same door leads back out (the exit preset)."},
        ],
        'critical_path': [f'room:{x}' for x in ('door_hall', 'stair2', 'stair3', 'ring3', 'conjury', 'scrying',
                                                'ring3', 'vault', 'alcoves', 'ring3', 'stair3', 'stair4', 'study')],
        'return_path': [f'room:{x}' for x in ('study', 'lab', 'ring4', 'well_foot', 'door_hall')],
        'goals': [
            {'id': 'goal:jewel', 'space': 'room:vault', 'kind': 'take', 'story': 'Q-D18',
             'what': "The Jewel of Ages on its stand, a ground item (D-90; its bit jewel_found 113361 dropped, A3 35th)."},
            {'id': 'goal:disks', 'space': 'room:alcoves', 'kind': 'take', 'story': 'Q-D18',
             'what': "Two Energy Disks in the experiment (q-d18.l3_disks).", 'gives': {'qbit': 113362}},
            {'id': 'goal:letter', 'space': 'room:study', 'kind': 'take', 'story': 'Q-D18',
             'what': "Ellinger's sealed letter on the desk (q-d18.letter).", 'gives': {'qbit': 113363}},
            {'id': 'goal:griffin', 'space': 'room:cabinet', 'kind': 'take', 'story': 'Q-D20',
             'what': "The Golden Griffin in the last case (q-d20.griffin).", 'gives': {'qbit': 113403}},
        ],
        'set_pieces': [
            {'id': 'set:well', 'kind': 'scripted', 'spaces': ['room:well_foot', 'room:ring4'],
             'rule': "The levitation well: four floors of galleries round the open shaft, the mages floating across "
                     "it; the floating disc rests at the top and rides the well down when its lever is pulled."},
            {'id': 'set:ward', 'kind': 'scripted', 'spaces': ['room:conjury', 'room:scrying', 'room:ring3'],
             'rule': "The door of light hums until both ward pylons are broken; its click says so."},
        ],
        'diagram': FlowDict(file='diagram.txt'),
        'totals': {'rooms': len(ROOMS), 'sectors': len(ROOMS), 'monsters_about': 30, 'chests': 3, 'loops': 5,
                   'doors': 10, 'fixed_actors': 0, 'floor_area_munits2': round(AREA / 1e6, 1)},
        'notes': "Class M by size with D-9.3's 30 monsters (D-39 Q2; MAPS: 20-45 sectors, 30-90 M units², 3-7 chests, "
                 "6-16 doors). From the MU-6 graph devdocs/xeen/mockups/act4_graphs/dd07.graph.yml and D-39 (the "
                 "floating-mage tiers, the fountain +1 all and the book +2 Intellect once per character, the Book of "
                 "Great Power's final refusal, the door of light fed by two destructible pylons, the dead mirror, "
                 "MM7 7d14 for the laboratory and the study, the interior larger than the shell). The graph's three "
                 "stair landings are the landing halls, its spiral stair three two-storey stair halls, its disc "
                 "landing an opening in the top gallery's rail. The roof stair (D-58, L4 only) up to D7's "
                 "entrance:dd07_roof.",
    }
    if level in ('L3', 'L4'):
        plan['sketch'] = FlowDict(file='rooms.yml', grid=512)
    return plan


def polygon_area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                   for i in range(len(pts)))) / 2


AREA = sum(polygon_area(r['outline']) for r in ROOMS.values())

DIAGRAM = r"""DD-07 Eastern Tower (x east, y north; four floors 640 apart round the open well)

 L4 1920  [STUDY: desk LETTER, two books, T4 chest]==door==[LABORATORY: fountains, vat]
              | door                                          | door
          [Top landing]--window--( WELL: disc rests here )=[Gallery under the cone]  (disc's landing, east rail)
                                                                | open (south arm)
                                                           [ROOF STAIR] ==trapdoor, one way up (D-58)==> D7
              ^ third stair (south hall, over the first)
 L3 1280  [Third landing]--window--( WELL )--[Third gallery]==LIGHT DOOR==[VAULT: JEWEL]--[alcoves: DISKS]
              ^ second stair (north hall)        | door      | door
                                           [CONJURY: pylon W]-open-[SCRYING: pylon E, pool]
 L2  640  [Second landing]--window--( WELL )--[Second gallery]==door==[CABINET: GRIFFIN]
              ^ first stair (south hall)         | open                   | door
                                           [MIRROR]-----open-----[DORMITORY: T4 chest]
 L1    0  =D3 door= [DOOR HALL: arrival]--arch--( WELL FOOT: the disc lands here )--[East gallery]
                                                            | door           | door
                                                       [COMMONS]        [STORE: T4 chest]
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


if __name__ == '__main__':
    check_sconces()
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
    print('written', sys.argv[1:] or 'L1-L4', f'area {AREA / 1e6:.1f} M units², rooms {len(ROOMS)}')
