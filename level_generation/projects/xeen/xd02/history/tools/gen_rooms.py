# XD-02 Red Dwarf Mines, L4: the shell (rooms.yml). Written once by this script from L3's sketch and the L4 design in
# NOTES.md; numbers are design numbers (there is no original). Run: python3 gen_rooms.py <L4 folder>.
import sys
import math
import yaml
from geom import *

L4 = sys.argv[1]


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# Surfaces
ROCK = S('cwb1', 128, 256)          # red-brown rock
DEEP = S('c2b', 256, 256)           # dark deep rock
GOLD_RED = S('cwb1gold', 128, 256)  # gold-seamed red rock
GOLD_DEEP = S('c1gold', 256, 256)   # gold-seamed deep rock
DIRT = S('7dirttyl', 128, 128)      # packed red earth
REDDIRT = S('dirt', 128, 128)
CAVEFLOOR = S('cfb1', 128, 128)
LAGGING = S('7trimda', 256, 128)    # plank lagging overhead, plank walkways
PLANKS_V = S('7trimd', 128, 256)
POST = S('beamplnv', 32, 256)       # dark timber, upright
BEAM = S('beamplnh', 256, 32)       # dark timber, lying
ROTTEN = S('d6ebeam', 32, 256)
GREYWOOD = S('7trim9_32', 32, 64)
IRON = S('ironn7dmbs', 128, 128)
DRESSED = S('cwb', 128, 256)
BLOCKS = S('7cdb', 128, 256)
SLABS = S('7tfb1', 128, 128)
DARKSLABS = S('7tfb11', 128, 128)
WATER_PIC = S('orwtrlga', 256, 256)
WATER = S('7wtrtyl', 128, 128)
WEB = S('web32n735s', 128, 128)
RUNES = S('runeeyvlij', 64, 64)

themes = [
    {'id': 'theme:timbered_adit', 'wall': ROCK, 'floor': DIRT, 'ceiling': S('bmplnk', 256, 256),
     'reveal': S('beamplnv', 32, 256), 'door': S('bwooda1', 256, 256, fit=True),
     'notes': "Timbered adit: red-brown rock (cwb1), packed red earth underfoot, plank lagging overhead, dark timber "
              "reveals in every doorway (the sets' posts), plank doors."},
    {'id': 'theme:red_workings', 'wall': ROCK, 'floor': REDDIRT, 'ceiling': ROCK,
     'reveal': S('beamplnv', 32, 256),
     'notes': "Raw red workings: red rock on walls and roof, red dirt floor; gold veins are switches in cwb1gold."},
    {'id': 'theme:deep_rock', 'wall': DEEP, 'floor': CAVEFLOOR, 'ceiling': DEEP,
     'notes': "Deep rock: the dark coarse rock and the dark cave floor of the stope's depths, the chasm, the "
              "galleries and the Deep Line."},
    {'id': 'theme:dwarf_hall', 'wall': DRESSED, 'floor': SLABS, 'ceiling': LAGGING,
     'reveal': S('7trimd', 128, 256), 'door': S('bwoodb1', 256, 256, fit=True),
     'bands': [{'height': 96, 'surface': S('7cdb', 128, 256)}],
     'notes': "Dwarf hall: dressed stone over a footing of dwarf blocks, slab floors, plank ceilings on dark beams "
              "(as the dwarves' halls of Snergle's mines have them), iron-banded plank doors."},
    {'id': 'theme:dwarf_chapel', 'wall': BLOCKS, 'floor': DARKSLABS, 'ceiling': DRESSED,
     'door': S('t5d1', 128, 256, fit=True),
     'notes': "Dwarf chapel: dwarf block walls, dark slab floor, dressed stone vault, carved stone door leaves."},
    {'id': 'theme:drowned_working', 'wall': ROCK, 'floor': WATER, 'ceiling': ROCK,
     'reveal': S('beamplnv', 32, 256),
     'notes': "Drowned working: red rock over standing water (the world's moving water, marked water in objects.yml)."},
    {'id': 'theme:dwarf_vault', 'wall': DRESSED, 'floor': SLABS, 'ceiling': DRESSED,
     'bands': [{'height': 96, 'surface': S('7cdb', 128, 256)}],
     'notes': "The Red Dwarves' own vault: dressed stone and slabs, no timber (its secret wall shows no frame)."},
    {'id': 'theme:grotto', 'wall': DEEP, 'floor': CAVEFLOOR, 'ceiling': DEEP,
     'notes': "A pool grotto: deep rock round a pool lit by its colour."},
]

rooms = []
openings = []


def room(id, name, **kw):
    d = {'id': id, 'name': name}
    d.update(kw)
    rooms.append(d)
    return d


def opening(id, a, b, **kw):
    d = {'id': id, 'from': a, 'to': b}
    d.update(kw)
    openings.append(d)
    return d


def post(x, y, rise, surface=POST, size=32, base=None, notes=None):
    p = {'at': [r(x), r(y)], 'size': [size, size], 'rise': rise, 'surface': surface}
    if base:
        p['base'] = base
    if notes:
        p['notes'] = notes
    return p


def beam(p0, p1, bottom, width=32, depth=32, bottom_end=None, notes=None, surface=None):
    b = {'path': [pt(p0), pt(p1)], 'width': width, 'depth': depth, 'bottom': r(bottom), 'surface': surface or BEAM}
    if bottom_end is not None:
        b['bottom_end'] = r(bottom_end)
    if notes:
        b['notes'] = notes
    return b


def rails(x0, y0, x1, y1, gauge=112, rise=6, plats=None):
    """Two iron rails on a level floor between two points (axis-aligned or diagonal)."""
    d = unit((x1 - x0, y1 - y0))
    n = left_normal(d)
    L = length((x1 - x0, y1 - y0))
    ang = math.degrees(math.atan2(d[1], d[0]))
    out = []
    for s in (-1, 1):
        cx = (x0 + x1) / 2 + n[0] * s * gauge / 2
        cy = (y0 + y1) / 2 + n[1] * s * gauge / 2
        out.append({'outline': rect_outline(cx, cy, L, 10, ang), 'rise': rise, 'surface': IRON, 'top_surface': IRON})
    return out


def cart(cx, cy, floor_z, angle=0.0, load=S('cfb1', 128, 128), lying=False, notes='A mine cart (blocks).'):
    """A mine cart drawn with platforms: a plank box on four iron wheels, full of ore."""
    a = math.radians(angle)
    u = (math.cos(a), math.sin(a))
    v = (-u[1], u[0])
    out = []
    L, W = 224, 144
    if lying:
        # on its side: the box lies with its wheels sticking out of one long side
        out.append({'outline': rect_outline(cx, cy, L, 112, angle), 'rise': W, 'surface': PLANKS_V,
                    'top_surface': PLANKS_V, 'notes': notes})
        for su in (-1, 1):
            wx = cx + u[0] * su * 70 + v[0] * 64
            wy = cy + u[1] * su * 70 + v[1] * 64
            out.append({'outline': rect_outline(wx, wy, 48, 16, angle), 'base': 40, 'rise': 48, 'surface': IRON,
                        'top_surface': IRON})
        return out
    out.append({'outline': rect_outline(cx, cy, L, W, angle), 'base': 24, 'rise': 72, 'surface': PLANKS_V,
                'top_surface': load, 'notes': notes})
    for su in (-1, 1):
        for sv in (-1, 1):
            wx = cx + u[0] * su * 72 + v[0] * sv * (W / 2 - 10)
            wy = cy + u[1] * su * 72 + v[1] * sv * (W / 2 - 10)
            out.append({'outline': rect_outline(wx, wy, 48, 16, angle), 'rise': 30, 'surface': IRON,
                        'top_surface': IRON})
    return out


def timber_set_x(x, y0, y1, floor, height, post_surface=POST, beam_surface=None, size=32, skip=()):
    """A timber set across a passage that runs along x: posts at both walls (y0, y1), a cap beam under the roof."""
    plats = []
    if 'lo' not in skip:
        plats.append(post(x, y0 + size / 2, height, post_surface, size))
    if 'hi' not in skip:
        plats.append(post(x, y1 - size / 2, height, post_surface, size))
    b = beam((x, y0), (x, y1), floor + height, width=size, depth=32)
    return plats, b


def timber_set_y(y, x0, x1, floor, height, post_surface=POST, size=32, skip=()):
    plats = []
    if 'lo' not in skip:
        plats.append(post(x0 + size / 2, y, height, post_surface, size))
    if 'hi' not in skip:
        plats.append(post(x1 - size / 2, y, height, post_surface, size))
    b = beam((x0, y), (x1, y), floor + height, width=size, depth=32)
    return plats, b


# ---------------------------------------------------------------- upper workings (east)

# Adit mouth: level, timbered, the portal in the east wall; rails from the party's feet.
plats, bms = [], []
for x in (13472, 13824, 14176):
    p, b = timber_set_x(x, 3008, 3776, 0, 384)
    plats += p
    bms.append(b)
plats.append(post(14304, 3104, 400, POST, 48, notes='Portal post'))
plats.append(post(14304, 3680, 400, POST, 48, notes='Portal post'))
bms.append(beam((14304, 3008), (14304, 3776), 400, width=48, depth=48, notes='Portal lintel'))
plats += rails(13330, 3392, 14300, 3392)
plats += cart(13600, 3650, 0, 0, lying=True, notes='An ore cart off the rails by the north wall, where the clan tipped it.')
room('room:adit_mouth', 'Adit mouth', outline=[[13312, 3008], [14336, 3008], [14336, 3776], [13312, 3776]],
     floor=0, ceiling=448, theme='theme:timbered_adit', ambient=8, platforms=plats, beams=bms,
     walls=[{'wall': 'west', 'panels': [{'id': 'panel:clan_sign', 'offset': 48, 'length': 160, 'bottom': 176,
                                         'height': 80, 'surface': S('warnsign', 256, 128, fit=True),
                                         'notes': "The clan's warning: skulls daubed on a board."}]}],
     notes="The timbered portal: daylight through the east wall (the X1 exit face, sky behind it), three timber sets "
           "of dark posts and cap beams under plank lagging, rails from the party's feet west down the drift, an ore "
           "cart at the rail head. Level (L3's 64 fall is in the haul drift).")

# Haul drift: one climbing path with timber sets; the first fight round the bend.
drift_path = [[13248, 3392, 0], [12736, 3392, 0], [12736, 4064, -64], [12736, 4672, -192]]


def drift_floor(y):
    if y <= 4064:
        return 0 + (-64 - 0) * (y - 3392) / (4064 - 3392)
    return -64 + (-192 + 64) * (y - 4064) / (4672 - 4064)


plats, bms = [], []
for x in (13040,):
    p, b = timber_set_x(x, 3200, 3584, 0, 384)
    plats += p
    bms.append(b)
for y in (3760, 4120, 4480):
    f = drift_floor(y)
    p, b = timber_set_y(y, 12544, 12928, r(f), 384)
    plats += p
    bms.append(b)
room('room:main_drift', 'Haul drift', path=drift_path, width=384, floor=0, ceiling=448,
     theme='theme:timbered_adit', ambient=18, platforms=plats, beams=bms,
     notes="The haul drift: west from the adit mouth, then north and down 192 to the Top Station (L3's main drift and "
           "incline in one climbing path). Timber sets (posts and cap beam) about every 360; the first fight waits round "
           "the bend, out of sight of the mouth.")

# Top Station: rock hall, timber loading platform along the west wall, the trestle gate in it.
plats, bms = [], []
plats.append({'id': 'platform:loading_dock', 'outline': [[11712, 4800], [11904, 4800], [11904, 5568], [11712, 5568]],
              'rise': 32, 'surface': PLANKS_V, 'top_surface': LAGGING,
              'notes': 'The timber loading platform along the west wall, level with the trestle gate.'})
for x in (12096, 12480, 12864):
    plats.append(post(x, 4752, 448, POST, 32))
    plats.append(post(x, 5616, 448, POST, 32))
    bms.append(beam((x, 4736), (x, 5632), -192 + 448, width=32, depth=40))
plats += rails(11904, 5184, 12700, 5184)
plats.append({'outline': rect_outline(12880, 5000, 160, 96, 0), 'rise': 40, 'surface': PLANKS_V,
              'top_surface': LAGGING, 'notes': "A plank bench by the drift's mouth."})
room('room:top_station', 'Top Station', outline=[[11712, 4736], [12992, 4736], [12992, 5632], [11712, 5632]],
     floor=-192, ceiling=320, theme='theme:timbered_adit', ambient=16, platforms=plats, beams=bms,
     notes="Rock hall 1280 by 896, 512 high, its plank roof on three cap beams; the loading platform (32) along the west "
           "wall, the trestle gate in that wall (the car waits beyond it). Doors to the lamp room (south) and the foot "
           "drift (north-west); open to the haul drift (south-east) and the sorting floor (north-east).")

room('room:lamp_room', 'Lamp room', outline=[[11712, 4608], [11904, 3840], [12480, 3840], [12480, 4608]],
     floor=-192, ceiling=192, theme='theme:timbered_adit', ambient=18,
     platforms=[
         {'id': 'platform:lamp_rack', 'outline': [[12400, 3904], [12464, 3904], [12464, 4544], [12400, 4544]],
          'base': 120, 'rise': 12, 'surface': PLANKS_V, 'top_surface': LAGGING,
          'notes': "The lamp rack's shelf along the long east wall; the miners' lamps hang over it."},
         post(12432, 3920, 132, GREYWOOD, 24), post(12432, 4528, 132, GREYWOOD, 24),
         post(12432, 4224, 132, GREYWOOD, 24)],
     notes="The wedge: the slanted west wall is the short side, the east wall the long one with the lamp rack. 384 high; "
           "a 128 wall with a plank door to the Top Station.")

# Sorting floor and its chutes.
room('room:sorting_floor', 'Sorting floor', outline=[[12160, 5696], [13568, 5696], [13568, 6720], [12544, 6720]],
     floor=-192, ceiling=576, theme='theme:red_workings', ambient=16,
     platforms=[
         {'at': [12864, 6016], 'size': [512, 96], 'rise': 48, 'surface': PLANKS_V, 'top_surface': LAGGING,
          'notes': 'Sorting table'},
         {'at': [13056, 6400], 'size': [512, 96], 'rise': 48, 'surface': PLANKS_V, 'top_surface': LAGGING,
          'notes': 'Sorting table'},
         {'outline': [[12608, 6560], [12800, 6560], [12800, 6656], [12608, 6656]], 'rise': 24, 'surface': ROCK,
          'top_surface': S('cfb1', 128, 128), 'notes': 'Spilled ore under the first chute.'},
     ],
     beams=[beam((12544, 6720), (13568, 6720), 448, 32, 32, notes='Lintel over the three chute mouths'),
            beam((12864, 5696), (12864, 6720), 280, 32, 40, notes='Beam the first lantern hangs from'),
            beam((13056, 5696), (13056, 6720), 280, 32, 40, notes='Beam the second lantern hangs from')],
     walls=[{'wall': 1, 'panels': [{'id': 'panel:chalk_mark', 'offset': 397, 'length': 128, 'bottom': 288,
                                    'height': 64, 'surface': S('runeeyvlij', 64, 64, fit=True),
                                    'notes': 'An old Red Dwarf chalk mark over the dry-stone wall.'}]}],
     notes="Trapezoid hall 1408 by 1024, 768 high; three ore chutes open as dark square shafts 384 up its north wall; "
           "two sorting tables; a gold vein on the slanted west wall; the old chalk-marked east wall hides the "
           "strongroom.")
for i, x0 in enumerate((12640, 12960, 13280)):
    room(f'room:chute_{i + 1}', f'Ore chute {i + 1}', space='room:sorting_floor',
         outline=[[x0, 6784], [x0 + 256, 6784], [x0 + 256, 7040], [x0, 7040]], floor=192, ceiling=960,
         theme='theme:red_workings', ambient=28,
         notes='The mouth of an ore chute, a black shaft 384 up the wall; bats roost in it.')
room('room:forgotten_strongroom', 'Forgotten strongroom', outline=[[13696, 5952], [14208, 5952], [14208, 6464], [13696, 6464]],
     floor=-160, ceiling=224, theme='theme:dwarf_vault', ambient=22,
     platforms=[{'at': [13800, 6400], 'size': [96, 96], 'rise': 40, 'surface': PLANKS_V, 'top_surface': PLANKS_V,
                 'notes': 'A stool fallen against the wall'},
                {'at': [14150, 6000], 'size': [96, 64], 'rise': 192, 'surface': PLANKS_V, 'top_surface': PLANKS_V,
                 'notes': 'An empty pay rack'}],
     notes="512 square vault one 32 step up from the sorting floor, behind a dry-stone wall that sinks (a secret door).")

# Foot drift: the old walking way round the north of the chasm, rotten props, the rockfall.
plats, bms = [], []
for x, kind in ((11520, 'sound'), (11180, 'rotten'), (10560, 'sound')):
    surf = ROTTEN if kind == 'rotten' else POST
    p, b = timber_set_x(x, 5824, 6144, -192, 352, post_surface=surf)
    plats += p
    bms.append(b)
plats.append(post(10880, 6128, 352, ROTTEN, 32, notes='A rotten prop with no cap left'))
room('room:foot_drift', 'Foot drift', path=[[11872, 5696], [11872, 5984], [10240, 5984]], width=320, floor=-192,
     ceiling=192, theme='theme:timbered_adit', ambient=22, platforms=plats, beams=bms,
     notes="The old walking drift: north from the Top Station's plank door, then west along the chasm's north side. A "
           "ragged gap in its south wall (a 192 rock wall) looks down at the trestle. Rotten props in the middle of the "
           "west leg, where the roof comes down (the rockfall: a mover of rubble and a plate, objects.yml).")
room('room:foot_incline', 'Foot drift, incline', space='room:foot_drift',
     outline=[[9664, 5824], [10176, 5824], [10176, 6144], [9664, 6144]], floor=-192,
     slope={'to': -384, 'toward': 'west'}, ceiling=192, ceiling_slope={'to': 0, 'toward': 'west'},
     theme='theme:timbered_adit', ambient=22,
     beams=[beam((9920, 5824), (9920, 6144), -288 + 320, notes='A cap beam half way down')],
     notes='Falls 192 west over 512 (0.375), its lagging falling with it.')
room('room:foot_bend', 'Foot drift, bend', space='room:foot_drift',
     outline=[[9381, 5757], [9600, 5757], [9600, 6144], [9085, 6144], [9085, 6053]], floor=-384, ceiling=0,
     theme='theme:timbered_adit', ambient=20,
     notes="The drift's foot, turning south-west into the Turntable's north-east side at the Turntable's level.")

# The chasm and the trestle.
TRESTLE_Y = 5184
DECK_E, DECK_W = -176, -448          # deck top at the east (x 11584) and west (x 9664) walls


def deck_top(x):
    return DECK_W + (DECK_E - DECK_W) * (x - 9664) / (11584 - 9664)


plats, bms = [], []
plats.append({'id': 'platform:trestle_deck', 'at': [10624, TRESTLE_Y], 'size': [1920, 256], 'base': 1792 - 520,
              'rise': r(DECK_W + 520), 'top_slope': {'to': r(DECK_E + 520), 'toward': 'east'}, 'thickness': 32,
              'surface': BEAM, 'top_surface': LAGGING, 'bottom_surface': BEAM,
              'notes': "The trestle's deck: planks on stringers, rising 272 from the Turntable's gate (west) to the Top "
                       "Station's (east), 16 under the car's wheels all the way."})
for x in (9888, 10272, 10656, 11040, 11424):
    top = deck_top(x) - 32
    for dy in (-112, 112):
        plats.append(post(x, TRESTLE_Y + dy, r(top + 1792), POST, 40, notes='Trestle leg'))
    bms.append(beam((x, TRESTLE_Y - 132), (x, TRESTLE_Y + 132), top - 40, width=24, depth=40))
    bms.append(beam((x, TRESTLE_Y - 132), (x, TRESTLE_Y + 132), top - 560, width=24, depth=32))
    # X braces between the legs of the bent (two raking beams)
    bms.append(beam((x - 14, TRESTLE_Y - 100), (x - 14, TRESTLE_Y + 100), top - 520, width=16, depth=24,
                    bottom_end=top - 80))
    bms.append(beam((x + 14, TRESTLE_Y + 100), (x + 14, TRESTLE_Y - 100), top - 520, width=16, depth=24,
                    bottom_end=top - 80))
# hand rails along the deck: raking beams from wall to wall
for dy in (-124, 124):
    bms.append(beam((9664, TRESTLE_Y + dy), (11584, TRESTLE_Y + dy), DECK_W + 44, width=8, depth=20,
                    bottom_end=DECK_E + 44, notes='Hand rail along the deck'))
chasm_ceiling = [[9900, 4800, 300], [10400, 5300, 540], [10900, 4900, 420], [11300, 5400, 360], [10200, 4700, 200],
                 [11000, 5550, 480], [10600, 5000, 576]]
room('room:chasm', 'The chasm', space='void:chasm', outline=[[9664, 4608], [11584, 4608], [11584, 5632], [9664, 5632]],
     floor=-1792, ceiling=160, ceiling_points=chasm_ceiling, theme='theme:deep_rock', ambient=31,
     platforms=plats, beams=bms,
     notes="The black cleft, 1920 by 1024, its floor 1600 under the Top Station (never reached; unlit). The trestle: "
           "five bents of two dark legs with X braces and caps, a plank deck rising from the Turntable's gate to the "
           "Top Station's, hand rails on both sides; the car runs on the deck (objects.yml mover:trestle_car).")

# ---------------------------------------------------------------- the Turntable and the east workings

TT = [[9472, 4960], [9472, 5408], [9352, 5696], [9024, 6024], [8736, 6144], [8288, 6144], [8000, 6024], [7672, 5696],
      [7552, 5408], [7552, 4960], [7672, 4672], [8000, 4344], [8288, 4224], [8736, 4224], [9024, 4344], [9352, 4672]]
tt_ceiling = [[8512, 5184, 352]]
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    rad = 520 + (k % 3) * 60
    tt_ceiling.append([r(8512 + rad * math.cos(a)), r(5184 + rad * math.sin(a)), 230 + (k * 37) % 70])
disc = ngon(8512, 5184, 224, 12, 15)
plats = [{'id': 'platform:turntable_disc', 'outline': disc, 'rise': 16, 'surface': IRON, 'top_surface': LAGGING,
          'notes': 'The timber turntable disc on its iron ring, 448 across.'}]
for dy in (-56, 56):
    plats.append({'outline': rect_outline(8512, 5184 + dy, 430, 10, 0), 'base': 16, 'rise': 6, 'surface': IRON,
                  'top_surface': IRON})
plats += rails(8740, 5184, 9460, 5184)                     # to the trestle gate
plats += rails(8670, 5026, 9180, 4516, gauge=112)           # to the east line gate (south-east)
plats.append({'id': 'platform:lever_post', 'at': [8880, 4860], 'size': [48, 48], 'rise': 120, 'surface': POST,
              'top_surface': POST, 'notes': "The points lever's post beside the disc."})
room('room:turntable', 'The Turntable', outline=TT, floor=-384, ceiling=128, ceiling_points=tt_ceiling,
     theme='theme:red_workings', ambient=14, platforms=plats,
     notes="Round cavern 1920 across under a low uneven roof (512 at the walls, 736 at the crown); the timber turntable "
           "disc in the middle with rails to the trestle gate (east) and the east line's gate (south-east); the points "
           "lever on a post beside the disc. Exits: trestle (east), foot drift (north-east), mess hall (north), west "
           "line (west), stope gallery (south-west), chapel doors (south), east line (south-east).")

# Chapel
room('room:chapel_steps', 'Chapel steps', space='room:dwarf_shrine',
     outline=[[8352, 3840], [8672, 3840], [8672, 4096], [8352, 4096]], floor=-384,
     slope={'to': -448, 'toward': 'south', 'steps': 2, 'tread': DARKSLABS, 'riser': BLOCKS}, ceiling=128,
     theme='theme:dwarf_chapel', ambient=18, notes='Two steps of 32 down from the carved double door.')
CH = [[9152, 2871], [9152, 3401], [8777, 3776], [8247, 3776], [7872, 3401], [7872, 2871], [8247, 2496], [8777, 2496]]
pillars = []
for k in range(8):
    a = 22.5 + 45 * k
    pillars.append({'at': [r(8512 + 400 * math.cos(math.radians(a))), r(3136 + 400 * math.sin(math.radians(a)))],
                    'size': [96, 96], 'facing': a, 'surface': DRESSED})
lantern = [[r(8512 + 300 * math.cos(math.radians(22.5 + 45 * k))), r(3136 + 300 * math.sin(math.radians(22.5 + 45 * k)))]
           for k in range(8)]
room('room:dwarf_shrine', 'Red Dwarf chapel', outline=CH, floor=-448, ceiling=64, theme='theme:dwarf_chapel', ambient=12,
     pillars=pillars,
     ceiling_levels=[{'outline': lantern, 'ceiling': 352, 'top_scale': 0.35, 'surface': DRESSED, 'edge': BLOCKS}],
     levels=[{'id': 'level:green_pool', 'outline': ngon(8512, 3136, 176, 8, 22.5), 'floor': -480, 'edge': BLOCKS,
              'surface': BLOCKS}],
     platforms=[
         {'id': 'platform:green_pool', 'outline': ngon(8512, 3136, 168, 8, 22.5), 'rise': 28,
          'surface': BLOCKS, 'top_surface': S('7slimywtr', 128, 128), 'notes': "The green pool's water (clicked to drink)."},
         {'at': [8512, 2544], 'size': [288, 48], 'rise': 112, 'surface': BLOCKS, 'end_surface': BLOCKS,
          'top_surface': DRESSED, 'notes': "The tablet's plinth"},
         {'id': 'platform:chapel_tablet', 'at': [8512, 2540], 'size': [256, 32], 'base': 112, 'rise': 128,
          'surface': S('sign128', 256, 128, fit=True), 'end_surface': DRESSED, 'top_surface': DRESSED,
          'notes': "The Red Dwarves' tablet on its plinth against the south wall: a bronze plaque of runes."},
         {'at': [8512, 2600], 'size': [320, 72], 'rise': 16, 'surface': BLOCKS, 'top_surface': DARKSLABS,
          'notes': "The tablet's step"},
     ],
     parapets=[{'path': ngon(8512, 3136, 196, 8, 22.5) + [ngon(8512, 3136, 196, 8, 22.5)[0]], 'height': 24,
                'thickness': 20, 'surface': BLOCKS}],
     notes="Octagon 1280 across, 512 high to its flat ring, a stone lantern over the pool rising to 800; eight dressed "
           "pillars on a ring 400 out; the green pool sunk 32 in the middle behind a kerb (its water a platform 4 under "
           "the floor, clicked); the tablet against the south wall facing the door.")

# East line: one straight drowned line at 45 degrees, the cart's room.
room('room:east_line', 'East line', path=[[9234, 4464], [10834, 2864]], width=320, floor=-424, ceiling=-40,
     theme='theme:drowned_working', ambient=22,
     platforms=rails(9250, 4448, 10818, 2880, gauge=112, rise=8),
     notes="The east line: a straight drowned rail tunnel 2260 long running south-east from the Turntable's gate to the "
           "buffer landing, its floor black water 40 under the gate sills with the rails just showing; the cart runs it "
           "(objects.yml mover:east_cart). L3's incline and drowned stretch in one straight room: a mover runs in one "
           "straight line.")
room('room:east_landing', 'Buffer landing', space='room:east_line',
     outline=[[10560, 2048], [11232, 2048], [11232, 2931], [11112, 3051], [10720, 2659], [10560, 2659]],
     floor=-640, floor_points=[[11232, 2931, -384], [11112, 3051, -384], [10720, 2659, -384], [10560, 2659, -384],
                               [10900, 2600, -400], [10900, 2200, -600]],
     ceiling=0, theme='theme:timbered_adit', ambient=22,
     notes="The buffer landing at the line's end: level with the cart at the line's mouth (-384), then down a rough "
           "ramp 256 to the flooded working's edge.")
FW = [[10240, 1984], [10112, 1600], [10368, 896], [10880, 576], [11648, 512], [12352, 704], [12672, 1024],
      [12672, 1792], [12032, 2112], [11264, 1984]]
fw_ceiling = [[10500, 1700, -240], [11000, 1100, -280], [11600, 900, -220], [12100, 1300, -260], [11500, 1700, -200],
              [10900, 1500, -300], [12300, 1000, -240], [10600, 1000, -260]]
plats = [
    {'at': [10912, 1648], 'size': [128, 608], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING,
     'notes': 'Plank walkway on trestles'},
    {'at': [11744, 1408], 'size': [1696, 128], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING,
     'notes': 'Plank walkway to the dry hump'},
    {'at': [10912, 1072], 'size': [128, 544], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING,
     'notes': 'Plank walkway south'},
    {'at': [11400, 864], 'size': [848, 128], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING,
     'notes': 'Plank walkway along the south shore'},
]
room('room:flooded_working', 'Flooded working', outline=FW, floor=-640, ceiling=-192, ceiling_points=fw_ceiling,
     theme='theme:drowned_working', ambient=22, rough={'step': 192, 'depth': 40}, platforms=plats,
     pillars=[{'outline': [[11280, 1080], [11560, 1060], [11620, 1220], [11440, 1300], [11260, 1220]], 'surface': ROCK},
              {'outline': [[11880, 1640], [12160, 1600], [12220, 1760], [12000, 1850], [11860, 1760]],
               'surface': ROCK}],
     notes="Irregular low cavern flooded knee-deep (the water is walked), plank walkways on trestles from the landing "
           "south and east to the dry hump with the gold pool, two rock islands; a gold vein on the south-east wall.")
room('room:gold_hump', 'Dry hump', space='room:flooded_working', outline=[[12736, 1088], [13248, 1088], [13248, 1728], [12736, 1728]], floor=-608,
     ceiling=-224, theme='theme:grotto', ambient=24,
     levels=[{'id': 'level:gold_pool', 'outline': ngon(13008, 1408, 168, 10, 0), 'floor': -640, 'edge': ROCK,
              'surface': ROCK}],
     platforms=[{'id': 'platform:gold_pool', 'outline': ngon(13008, 1408, 160, 10, 0), 'rise': 28, 'surface': ROCK,
                 'top_surface': S('orertlga', 256, 256), 'notes': "The gold pool's water (clicked to drink)."}],
     notes="The dry hump: a rock shelf one step (32) out of the flood, the gold pool sunk 32 in it.")

# ---------------------------------------------------------------- the camp

plats = [
    {'at': [7968, 6400], 'size': [640, 96], 'rise': 48, 'surface': PLANKS_V, 'top_surface': LAGGING,
     'notes': 'Long table'},
    {'at': [7968, 6720], 'size': [640, 96], 'rise': 48, 'surface': PLANKS_V, 'top_surface': LAGGING,
     'notes': 'Long table'},
    {'at': [7968, 6304], 'size': [600, 40], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING},
    {'at': [7968, 6496], 'size': [600, 40], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING},
    {'at': [7968, 6624], 'size': [600, 40], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING},
    {'at': [7968, 6816], 'size': [600, 40], 'rise': 24, 'surface': PLANKS_V, 'top_surface': LAGGING},
    {'outline': [[7552, 6976], [7744, 6976], [7744, 7232], [7552, 7232]], 'rise': 32, 'surface': BLOCKS,
     'top_surface': S('cfb1', 128, 128), 'notes': 'The cold hearth in the angle of the L, against the leg\'s east wall'},
    {'outline': [[7712, 6992], [7744, 6992], [7744, 7216], [7712, 7216]], 'base': 32, 'rise': 192, 'surface': BLOCKS,
     'top_surface': BLOCKS, 'notes': 'Hearth back'},
]
bms = [beam((x, 6208), (x, 6912), 64, 40, 40) for x in (7360, 8160, 8640)]
bms += [beam((6976, y), (7744, y), 64, 40, 40) for y in (7232,)]
room('room:mess_hall', 'Mess hall', outline=[[6976, 6208], [8960, 6208], [8960, 6912], [7744, 6912], [7744, 7488],
                                             [6976, 7488]],
     floor=-384, ceiling=128, theme='theme:dwarf_hall', ambient=12,
     pillars=[{'at': [7488, 6560], 'size': [192, 192], 'facing': 15, 'surface': ROCK},
              {'at': [8448, 6560], 'size': [192, 192], 'facing': -10, 'surface': ROCK}],
     platforms=plats, beams=bms,
     notes="L-shaped hewn hall: a bar 1984 by 704 along the Turntable's north side and a leg 768 by 576 north at its "
           "west end, 512 high under a plank ceiling on dark beams; two rock pillars left standing, two long tables "
           "with benches, the cold hearth in the angle of the L. Open to the Turntable; doors to the bunk cut (north) "
           "and the tally steps (west).")
room('room:bunk_cut', 'Bunk cut',
     outline=[[6848, 7552], [7680, 7552], [7808, 7616], [7872, 7744], [7872, 8000], [7808, 8128], [7680, 8192],
              [6848, 8192]],
     floor=-352, ceiling=32, theme='theme:dwarf_hall', ambient=18,
     notes='Long narrow cut 1024 by 640, its east end rounded; one 32 step up from the mess hall; three bunks hewn into '
           'the north wall.')
for i, x0 in enumerate((6880, 7168, 7456)):
    room(f'room:bunk_niche_{i + 1}', f'Bunk niche {i + 1}', space='room:bunk_cut',
         outline=[[x0, 8256], [x0 + 224, 8256], [x0 + 224, 8448], [x0, 8448]], floor=-288, ceiling=-96,
         theme='theme:dwarf_hall', ambient=20,
         platforms=[{'at': [x0 + 112, 8380], 'size': [192, 96], 'rise': 16, 'surface': S('7trimd', 128, 256),
                     'top_surface': S('bembllg', 256, 256), 'notes': 'A straw pallet'}],
         notes='A bunk hewn into the wall: a shelf 64 above the cut, 192 deep and 192 high.')
room('room:tally_steps', 'Tally steps', space='room:tally_room',
     outline=[[6592, 7040], [6912, 7040], [6912, 7360], [6592, 7360]], floor=-384,
     slope={'to': -288, 'toward': 'west', 'steps': 3, 'tread': SLABS, 'riser': BLOCKS}, ceiling=64,
     theme='theme:dwarf_hall', ambient=16, notes='Three steps of 32 up from the mess hall to the iron-bound door.')
room('room:tally_room', 'Tally room',
     outline=[[6528, 6944], [6528, 7456], [6080, 7712], [5632, 7456], [5632, 6944], [6080, 6688]],
     floor=-288, ceiling=160, theme='theme:dwarf_hall', ambient=14,
     platforms=[{'at': [5952, 7200], 'size': [256, 128], 'rise': 40, 'surface': PLANKS_V, 'top_surface': LAGGING,
                 'notes': "The tallymaster's table"}],
     walls=[{'wall': k, 'panels': [{'at': 'centre', 'length': 256, 'bottom': 128, 'height': 128,
                                    'surface': S('sign22', 256, 64)}]} for k in (1, 2, 4, 5)],
     notes="Hexagon 896 across the flats, 448 high; the clan's tallies of stolen ore chalked on the walls (carved "
           "plaques stand for them); the tallymaster's table facing the door, the strongbox behind it.")

# ---------------------------------------------------------------- the west line

plats, bms = [], []
for x in (7200, 6600):
    f = -384 + (-64 + 384) * (7488 - x) / 1536
    plats.append(post(x, 5040, 352, POST, 32))
    plats.append(post(x, 5328, 352, POST, 32))
plats += cart(6200, 5184, -300, 8, lying=True, notes='The derailed cart, on its side.')
room('room:west_line', 'West line', outline=[[5952, 5024], [7488, 5024], [7488, 5344], [5952, 5344]], floor=-384,
     slope={'to': -64, 'toward': 'west'}, ceiling=0, ceiling_slope={'to': 320, 'toward': 'west'},
     theme='theme:timbered_adit', ambient=22, platforms=plats,
     notes="Derailed rail tunnel rising 320 west over 1536 (0.21), its lagging rising with it; a cart lies on its side.")
plats = rails(5136, 5184, 5872, 5184)
for x in (5300, 5700):
    p, b = timber_set_x(x, 4992, 5376, -64, 320)
    plats += p
    bms.append(b)
room('room:west_line_landing', 'West line, air-door landing', space='room:west_line',
     outline=[[5120, 4992], [5888, 4992], [5888, 5376], [5120, 5376]], floor=-64, ceiling=320,
     theme='theme:timbered_adit', ambient=22, platforms=plats, beams=bms,
     notes='Level stretch half way along, the first ventilation door in its west wall, the repair niche off its north '
           'side.')
room('room:repair_niche', 'Repair niche', space='room:west_line',
     outline=[[5248, 5440], [5760, 5440], [5760, 5824], [5248, 5824]], floor=-64, ceiling=320,
     theme='theme:timbered_adit', ambient=24,
     platforms=[{'at': [5504, 5720], 'size': [384, 96], 'rise': 56, 'surface': PLANKS_V, 'top_surface': LAGGING,
                 'notes': 'The wheelwright bench'}] + cart(5420, 5560, -64, 0,
                                                         notes='A cart up on blocks, one wheel off.'),
     notes="Side niche 512 by 384 where carts were mended; the spiders' den of the line.")
plats = []
for x in (4700, 4100):
    plats.append(post(x, 5040, 352, ROTTEN, 32))
    plats.append(post(x, 5328, 352, ROTTEN, 32))
room('room:west_line_upper', 'West line, upper incline', space='room:west_line',
     outline=[[3520, 5024], [5056, 5024], [5056, 5344], [3520, 5344]], floor=-64, slope={'to': 256, 'toward': 'west'},
     ceiling=320, ceiling_slope={'to': 640, 'toward': 'west'}, theme='theme:timbered_adit', ambient=24, platforms=plats,
     notes='Rises 320 west over 1536 (0.21) to the second ventilation door; few lamps, rotten props.')
plats, bms = [], []
for x in (3300, 3000):
    p, b = timber_set_x(x, 4960, 5408, 256, 384)
    plats += p
    bms.append(b)
plats.append({'id': 'platform:winch', 'at': [2880, 5344], 'size': [160, 64], 'base': 48, 'rise': 64,
              'surface': S('7trimd', 128, 256), 'end_surface': IRON, 'top_surface': S('7trimd', 128, 256),
              'notes': "The winch's drum on its frame (clicked)."})
plats.append(post(2788, 5344, 128, POST, 24, notes='Winch frame'))
plats.append(post(2972, 5344, 128, POST, 24, notes='Winch frame'))
room('room:collapsed_adit', 'Collapsed west adit', outline=[[2432, 4960], [3456, 4960], [3456, 5408], [2432, 5408]],
     floor=256, ceiling=704, theme='theme:timbered_adit', ambient=22, platforms=plats, beams=bms,
     notes="The old west adit, 1024 long and 448 wide: the fall fills its west end to the roof (a mover that the winch "
           "sends down an ore chute under the floor); the winch on its frame in front of the fall; the X4 exit face "
           "is the west wall behind the fall.")

# ---------------------------------------------------------------- the Open Stope

C = (6208, 2880)
P = [(7328, 2656), (7328, 3104), (7158, 3512), (6840, 3830), (6432, 4000), (5984, 4000), (5576, 3830), (5258, 3512),
     (5088, 3104), (5088, 2656), (5258, 2248), (5576, 1930), (5984, 1760), (6432, 1760), (6840, 1930), (7158, 2248)]
FLOOR = -1152
BENCH = 320
Q = inset_polygon(P, BENCH)
# spiral sides in walking order (down): (side, kind, top at the side's start corner P[i], top at P[i+1])
SPIRAL = [(1, 'ledge', -384, -384), (0, 'ramp', -544, -384), (15, 'ledge', -544, -544), (14, 'ramp', -704, -544),
          (13, 'ledge', -704, -704), (12, 'ramp', -864, -704), (11, 'ledge', -864, -864), (10, 'ramp', -1024, -864),
          (9, 'ledge', -1024, -1024), (8, 'ramp', -1152, -1024)]
plats, bms = [], []
names = {1: 'rim ledge (east-north-east)', 0: 'ramp, east', 15: 'ledge, east-south-east', 14: 'ramp, south-east',
         13: 'ledge, south-south-east', 12: 'ramp, south', 11: 'ledge, south-south-west', 10: 'ramp, south-west',
         9: 'ledge, west-south-west', 8: 'ramp, west (to the floor)'}
corner_h = {}
for side, kind, h0, h1 in SPIRAL:
    a, b = P[side], P[(side + 1) % 16]
    qa, qb = Q[side], Q[(side + 1) % 16]
    corner_h[side] = h0
    corner_h[(side + 1) % 16] = h1
    outline = [pt(a), pt(b), pt(qb), pt(qa)]
    d = {'id': f'platform:bench_{side}', 'outline': outline, 'surface': ROCK, 'top_surface': REDDIRT,
         'notes': f'Spiral bench: {names[side]}.'}
    if kind == 'ledge':
        d['rise'] = h0 - FLOOR
    else:
        d['rise'] = min(h0, h1) - FLOOR if min(h0, h1) > FLOOR else 0
        d['top_heights'] = [h0 - FLOOR, h1 - FLOOR, h1 - FLOOR, h0 - FLOOR]
    plats.append(d)
    # the rail along the bench's open edge (qb -> qa), 56 over the bench, on posts
    rail = beam(qb, qa, h1 + 56, width=12, depth=16, bottom_end=(h0 + 56) if h0 != h1 else None)
    rail['notes'] = f'Timber rail of the {names[side]}'
    if side == 8:
        # the last ramp runs out onto the floor: its rail ends half way down
        mid = lerp(qb, qa, 0.6)
        rail = beam(qb, mid, h1 + 56, width=12, depth=16, bottom_end=h1 + (h0 - h1) * 0.6 + 56)
    bms.append(rail)
# the end of the rim ledge over the hoist side: a rail across it
bms.append(beam(Q[2], P[2], -384 + 56, width=12, depth=16, notes="Rail across the rim ledge's open north end"))
# posts at the inner corners
for k in (2, 1, 0, 15, 14, 13, 12, 11, 10, 9):
    h = corner_h[k]
    q = Q[k]
    inward = unit(sub(C, q))
    p = add(q, mul(inward, -10))
    plats.append(post(p[0], p[1], 76, POST, 16, base=h - FLOOR))
# mid posts on the ledges
for side, kind, h0, h1 in SPIRAL:
    if kind == 'ledge':
        m = lerp(Q[side], Q[(side + 1) % 16], 0.5)
        m = add(m, mul(unit(sub(C, m)), -10))
        plats.append(post(m[0], m[1], 76, POST, 16, base=h0 - FLOOR))
# two spoil heaps on the floor and the abandoned carts
plats.append({'outline': [[5900, 2700], [6160, 2620], [6300, 2760], [6220, 2930], [5960, 2950], [5860, 2830]],
              'rise': 0, 'top_heights': [40, 24, 56, 72, 96, 64], 'surface': REDDIRT, 'top_surface': REDDIRT,
              'notes': 'Spoil heap'})
plats.append({'outline': [[6500, 3150], [6720, 3100], [6820, 3260], [6700, 3400], [6520, 3360]], 'rise': 0,
              'top_heights': [32, 56, 80, 48, 64], 'surface': REDDIRT, 'top_surface': REDDIRT, 'notes': 'Spoil heap'})
plats += cart(6050, 3400, FLOOR, 30, notes='An abandoned ore cart.')
plats += cart(5720, 3000, FLOOR, -70, lying=True, notes='An abandoned cart on its side.')
# the hoist's head frame over the cage (beams from the wall over the shaft) and its cable
hm = lerp(P[2], P[3], 0.5)
hm = lerp(P[2], P[2], 0)
mid2 = lerp(P[2], P[3], 0.0)
e2mid = lerp(P[2], P[3], 0.5)
e2mid = ((P[2][0] + P[3][0]) / 2, (P[2][1] + P[3][1]) / 2)
inward2 = unit(sub(C, e2mid))
along2 = unit(sub(P[3], P[2]))
for s in (-1, 1):
    a0 = add(e2mid, mul(along2, s * 112))
    a1 = add(a0, mul(inward2, 260))
    bms.append(beam(a0, a1, -40, width=24, depth=40, bottom_end=-10, notes='Head frame arm'))
cage_c = add(e2mid, mul(inward2, 112))
bms.append(beam(add(cage_c, mul(along2, -130)), add(cage_c, mul(along2, 130)), -6, width=32, depth=40,
                notes="Head frame cross-head with the sheave's axle"))
plats.append({'outline': rect_outline(cage_c[0], cage_c[1], 12, 12, 45), 'rise': -6 - FLOOR, 'solid': False,
              'surface': IRON, 'top_surface': IRON, 'notes': 'The hoist cable, from the head frame to the floor.'})
stope_ceiling = [[6208, 2880, 512], [6800, 2400, 440], [5600, 3300, 470], [5700, 2300, 420], [6700, 3400, 480],
                 [6208, 2100, 400], [6208, 3650, 430], [7000, 2880, 400], [5400, 2880, 450]]
room('room:stope_floor', 'Open Stope', outline=[pt(p) for p in P], floor=FLOOR, ceiling=384,
     ceiling_points=stope_ceiling, theme='theme:red_workings', ambient=18, platforms=plats, beams=bms,
     bands=[{'height': 640, 'surface': DEEP}],
     notes="The Open Stope: a sixteen-sided pit 2240 across and about 1600 high from its floor to a ragged roof. A "
           "spiral of rock benches 320 wide runs 0.6 of a turn clockwise down its walls from the rim ledge (-384, "
           "east-north-east) round the east, south and west to the floor (-1152, west-north-west): five ramps (160 or "
           "128 down over 437) alternating with five level ledges, all open to the pit behind a timber rail on posts. "
           "The floor is deep rock up to 640, red rock above; two spoil heaps, two abandoned carts, the hoist at the "
           "north-east side under its head frame.")

# Rim and gallery
room('room:stope_gallery', 'Stope gallery', space='room:stope_rim', path=[[7791, 4463], [7361, 4033]], floor=-384,
     ceiling=-64, theme='theme:red_workings', ambient=27,
     section={'outline': [[-128, 0], [128, 0], [176, 96], [168, 224], [96, 320], [-96, 320], [-168, 224],
                          [-176, 96]],
              'floor': REDDIRT, 'lower': ROCK, 'wall': ROCK, 'upper': ROCK, 'ceiling': ROCK,
              'start': {'width': 288, 'length': 96}, 'end': {'width': 288, 'length': 96}},
     notes="The short, low, dark gallery from the Turntable's south-west side: a rock tunnel 320 high; at its end the "
           "Open Stope opens all at once.")
room('room:stope_rim', 'Stope rim',
     outline=[[7776, 3177], [7742, 3276], [7572, 3684], [7475, 3829], [7157, 4147], [6885, 3875], [7203, 3557],
              [7217, 3537], [7367, 3177]],
     floor=-384, ceiling=256, theme='theme:red_workings', ambient=20,
     platforms=[post(7300, 3640, 400, POST, 32), post(7020, 3940, 400, POST, 32)],
     beams=[beam((7300, 3640), (7020, 3940), 16, 32, 40, notes="The rim's timber cap over the hoist landing")],
     notes="The rim behind the pit's wall: a ledge 384 wide round the north-east, open to the stope over the whole "
           "east-north-east wall onto the spiral's first ledge (the reveal), the hoist gate in its north-east wall.")

# Floor-side rooms of the stope
room('room:red_pool_grotto', 'Red pool grotto',
     outline=[[6048, 4064], [6368, 4064], [6560, 4352], [6496, 4640], [6208, 4800], [5920, 4640], [5928, 4352]],
     floor=-1184, ceiling=-640, theme='theme:grotto', ambient=26, rough={'step': 160, 'depth': 32},
     levels=[{'id': 'level:red_pool', 'outline': [[6080, 4480], [6336, 4480], [6400, 4580], [6208, 4700],
                                                   [6016, 4580]], 'floor': -1216, 'edge': DEEP, 'surface': DEEP}],
     platforms=[{'id': 'platform:red_pool', 'outline': [[6088, 4488], [6328, 4488], [6390, 4580], [6208, 4692],
                                                         [6026, 4580]],
                 'rise': 28, 'surface': DEEP, 'top_surface': S('lavatyl', 128, 128),
                 'notes': "The red pool's water (clicked): drawn by the lava shader, without the lava flag."}],
     notes="Teardrop grotto one step (32) below the stope floor off its north side; the red pool sunk 32 in its point.")
# The moles' pocket behind the rich vein (north-north-east wall, e3)
e3a, e3b = P[3], P[4]
t0, t1 = 0.16, 0.44
nrm3 = unit(left_normal(sub(e3b, e3a)))
nrm3 = (-nrm3[0], -nrm3[1])  # outward
b0 = add(lerp(e3a, e3b, t0), mul(nrm3, 65))
b1 = add(lerp(e3a, e3b, t1), mul(nrm3, 65))
f0 = add(b0, mul(nrm3, 260))
f1 = add(b1, mul(nrm3, 260))
pocket = [[6625, 3990], [6841, 3900], [6991, 4260], [6775, 4350]]  # exact 5:12 multiples of the e3 wall
room('room:mole_pocket', "Moles' burrow", space='room:stope_floor', outline=pocket, floor=-1152, ceiling=-832, theme='theme:deep_rock',
     ambient=30, notes="A burrow behind the rich vein; the rock between it and the stope breaks open when the vein is "
                      "mined (a door with the wall's surface).")
room('room:deep_ramp', 'Deep Line approach', space='room:deep_station',
     outline=[[5485, 3829], [4806, 4508], [4580, 4282], [5259, 3603]], floor=-1152,
     slope={'to': -1216, 'toward': 1}, ceiling=-768, ceiling_slope={'to': -832, 'toward': 1},
     theme='theme:deep_rock', ambient=24,
     notes='A rock-cut way 960 long falling 64 north-west from the stope floor to the Deep Line station.')
room('room:deep_station', 'Deep Line station',
     outline=[[4422, 4214], [4874, 4666], [4682, 4896], [3968, 4896], [3776, 4608], [3840, 4288], [4160, 4160]],
     floor=-1216, ceiling=-768, theme='theme:deep_rock', ambient=20,
     platforms=rails(3860, 4448, 4560, 4448) + [
         {'at': [3928, 4448], 'size': [48, 288], 'rise': 56, 'surface': IRON, 'top_surface': IRON,
          'notes': 'The buffer stop before the Deep Line'}] + cart(4060, 4448, -1216, 0,
                                                                   notes='The Deep Line cart, chained to its brake.'),
     notes="Rock-cut station about 1100 by 736, 448 high; rails run west to the buffer stop before the Deep Line's mouth "
           "(the XD-03 exit face in the west wall); the chained cart on them, the brake wheel on the north wall.")
room('room:deep_mouth', "The Deep Line's mouth", space='room:deep_station',
     outline=[[3712, 4595], [3272, 4507], [3336, 4187], [3776, 4275]], floor=-1216,
     slope={'to': -1408, 'toward': 1}, ceiling=-832, ceiling_slope={'to': -1024, 'toward': 1},
     theme='theme:deep_rock', ambient=30,
     notes="The Deep Line's mouth: the rails' cutting drops away steeply west from the buffer stop into the dark (192 "
           "over 448); its far end is the exit to the Deep Mine (XD-03).")
# The crawl and the spider galleries
room('room:crawl', 'Low crawl', space='room:spider_galleries', path=[[5755, 1785], [5535, 1257]], width=260,
     floor=-864, ceiling=-512, theme='theme:deep_rock', ambient=28,
     notes="The low crawl off the south-south-west ledge, 572 long and 352 high, through the rock to the galleries.")
SG = [[5713, 1110], [5305, 1280], [4800, 1344], [4416, 1472], [4032, 1664], [3584, 1600], [3264, 1408], [3072, 1216],
      [3072, 768], [3264, 448], [3712, 320], [4160, 512], [4544, 384], [5056, 320], [5504, 448], [5888, 704]]
sg_ceiling = [[3500, 1000, -400], [4100, 1000, -360], [4700, 900, -420], [5300, 800, -380], [3800, 600, -440],
              [5000, 600, -460], [3400, 1300, -480]]
room('room:spider_galleries', 'Spider galleries', outline=SG, floor=-864, ceiling=-480, ceiling_points=sg_ceiling,
     theme='theme:deep_rock', ambient=17, rough={'step': 192, 'depth': 40},
     pillars=[{'outline': [[3820, 760], [3980, 720], [4060, 1000], [3940, 1180], [3800, 1060]], 'surface': DEEP},
              {'outline': [[4720, 640], [4880, 600], [4960, 820], [4860, 1040], [4700, 960]], 'surface': DEEP}],
     notes="Three old side workings run together into one web-hung warren about 2800 by 1350, split by two rock "
           "islands; the crawl comes in at the east; the cocoon in the western working; the web wall to the blue "
           "grotto is the straight west wall.")
room('room:blue_grotto', 'Blue grotto',
     outline=[[2944, 768], [2944, 1216], [2688, 1408], [2304, 1408], [2048, 1216], [1984, 960], [2112, 704],
              [2432, 576], [2752, 576]],
     floor=-864, ceiling=-320, theme='theme:grotto', ambient=24, rough={'step': 160, 'depth': 32},
     levels=[{'id': 'level:blue_pool', 'outline': [[2752, 800], [2752, 1160], [2560, 1280], [2304, 1280],
                                                    [2144, 1150], [2112, 960], [2208, 780], [2432, 700], [2640, 700]],
              'floor': -896, 'edge': DEEP, 'surface': DEEP}],
     platforms=[{'id': 'platform:blue_pool', 'outline': [[2744, 808], [2744, 1155], [2556, 1272], [2308, 1272],
                                                          [2152, 1146], [2120, 960], [2214, 788], [2434, 708],
                                                          [2636, 708]],
                 'rise': 28, 'surface': DEEP, 'top_surface': WATER, 'notes': "The blue pool's water (clicked)."}],
     notes="Round grotto behind the web wall, its floor nearly all a shallow pool of glowing blue water (sunk 32), a "
           "rim of rock at the web wall.")

# ---------------------------------------------------------------- openings

def O(id, a, b, w, h, **kw):
    return opening(id, a, b, width=w, height=h, **kw)


O('open:adit_drift', 'room:adit_mouth', 'room:main_drift', 320, 352, from_wall=3, to_wall=7)
O('open:drift_station', 'room:main_drift', 'room:top_station', 320, 352)
O('open:station_lamp', 'room:top_station', 'room:lamp_room', 192, 256, along=0.75)
O('open:station_sorting', 'room:top_station', 'room:sorting_floor', 448, 384)
O('open:station_foot', 'room:top_station', 'room:foot_drift', 192, 256)
O('open:station_trestle', 'room:top_station', 'room:chasm', 256, 320, sill=32,
  notes="The trestle gate in the loading platform's wall: the car's top is level with the platform here.")
for i in range(3):
    O(f'open:chute_{i + 1}', 'room:sorting_floor', f'room:chute_{i + 1}', 192, 256)
O('open:sorting_strongroom', 'room:forgotten_strongroom', 'room:sorting_floor', 192, 256, along=0.55,
  notes='The chalk-marked dry-stone wall that sinks (a secret door in a 128 wall).')
O('open:foot_incline', 'room:foot_drift', 'room:foot_incline', 288, 320)
O('open:foot_window', 'room:foot_drift', 'room:chasm', 640, 224, sill=64,
  notes='The ragged gap over the chasm, looking down at the trestle.')
O('open:incline_bend', 'room:foot_incline', 'room:foot_bend', 288, 320)
O('open:bend_turntable', 'room:foot_bend', 'room:turntable', 320, 320)
O('open:turntable_trestle', 'room:turntable', 'room:chasm', 256, 320, notes="The trestle's Turntable gate.")
O('open:turntable_east', 'room:turntable', 'room:east_line', 256, 320, notes="The east line's gate.")
O('open:east_landing', 'room:east_line', 'room:east_landing', 256, 320, notes='The buffer gate at the line\'s end.')
O('open:landing_flooded', 'room:east_landing', 'room:flooded_working', 384, 320, along=0.5)
O('open:flooded_hump', 'room:flooded_working', 'room:gold_hump', 448, 352)
O('open:turntable_chapel', 'room:chapel_steps', 'room:turntable', 256, 256,
  notes='The carved double door in a 128 wall.')
O('open:steps_shrine', 'room:chapel_steps', 'room:dwarf_shrine', 256, 320)
O('open:turntable_mess', 'room:turntable', 'room:mess_hall', 384, 384)
O('open:mess_bunk', 'room:mess_hall', 'room:bunk_cut', 192, 256)
for i in range(3):
    O(f'open:bunk_niche_{i + 1}', 'room:bunk_cut', f'room:bunk_niche_{i + 1}', 192, 160)
O('open:mess_tally', 'room:mess_hall', 'room:tally_steps', 256, 320)
O('open:tally_door', 'room:tally_steps', 'room:tally_room', 192, 256)
O('open:turntable_west', 'room:turntable', 'room:west_line', 256, 320)
O('open:west_landing', 'room:west_line', 'room:west_line_landing', 256, 320)
O('open:landing_niche', 'room:west_line_landing', 'room:repair_niche', 320, 320)
O('open:landing_upper', 'room:west_line_landing', 'room:west_line_upper', 256, 320, notes='The first ventilation door.')
O('open:upper_adit', 'room:west_line_upper', 'room:collapsed_adit', 256, 320, notes='The second ventilation door.')
opening('open:turntable_gallery', 'room:turntable', 'room:stope_gallery', width='full', height='full')
opening('open:gallery_rim', 'room:stope_gallery', 'room:stope_rim', width='full', height='full')
opening('open:rim_mouth', 'room:stope_rim', 'room:stope_floor', width='full', height='full', from_wall=7, to_wall=1,
        notes="The rim opens over the whole east-north-east wall onto the spiral's first ledge: the reveal.")
O('open:rim_hoist', 'room:stope_rim', 'room:stope_floor', 192, 320, from_wall=5, to_wall=2,
  notes='The hoist gate: the cage stops level with the rim here.')
O('open:stope_red', 'room:stope_floor', 'room:red_pool_grotto', 288, 384)
O('open:stope_pocket', 'room:mole_pocket', 'room:stope_floor', 176, 256,
  notes="The burrow's mouth behind the rich vein (shut by a door with the wall's surface).")
O('open:stope_deep_ramp', 'room:stope_floor', 'room:deep_ramp', 256, 320)
O('open:deep_ramp_station', 'room:deep_ramp', 'room:deep_station', 256, 320)
O('open:station_mouth', 'room:deep_station', 'room:deep_mouth', 255, 320, notes="Behind the buffer stop: the Deep Line's mouth.")
O('open:stope_crawl', 'room:stope_floor', 'room:crawl', 224, 320, notes="The crawl's mouth off the south-south-west ledge.")
O('open:crawl_galleries', 'room:crawl', 'room:spider_galleries', 224, 320)
O('open:galleries_blue', 'room:spider_galleries', 'room:blue_grotto', 256, 320,
  notes='The web wall over a thin rock screen (a secret door that rises), 128 thick.')

doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:red_workings', 'ambient': 20}, 'rooms': rooms,
       'openings': openings,
       'notes': "XD-02 L4: L3's rooms redrawn with the studio's words of 2026-11-13 (written by "
                "output/studio_cal/xd02/tools/gen_rooms.py; NOTES.md). Whole map units, x east, y north, heights from "
                "the arrival (0). The Open Stope is one room with its spiral of benches inside it; the cart lines are "
                "straight rooms with movers; timber sets are posts and cap beams."}
with open(f'{L4}/rooms.yml', 'w') as f:
    yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=None, width=120, allow_unicode=True)
print('rooms', len(rooms), 'openings', len(openings))
