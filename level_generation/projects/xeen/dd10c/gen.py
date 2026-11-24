"""DD-10C Gemstone Mines, north pocket: writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd10c/L*).

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd10c), phase 3, decider D-27.
Shared with DD-10A and DD-10B: level_generation/projects/xeen/dd10a/mine.py (themes, timber, carts, veins, refill, false vein,
exit), imported, not copied, so one change reaches all three pockets.

D-27 moved this pocket to Act V (D6's lower band, 38-50, treasure 5, D6's own families picked by A2): the geometry,
veins, refill, false vein, lava seam, lights, sounds and dressing are built now and kept in scratch; phase 5 adds the
monsters (MONSTER_SPOTS below, rows from A2: set PHASE5_MONSTERS), the live exit to D6 (D6_LIVE and D6_ARRIVAL, A6's
adit) and the install.

Plan frame: x east, y north, the adit's mouth at y 0 (the party comes in from D6 going north). One level, floors at 0
(the lava seam sunk 48): the adit, the lava gallery running east, the diamond cavern at its east end, the crystal
grotto behind a door east of that; the collapse behind a door north of the gallery, the roach nest east of the
collapse, opening south into the diamond cavern: one loop (lava gallery, diamond cavern, nest, collapse).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd10a')
from mine import *  # noqa: E402,F401,F403

OUT = R + '/devdocs/xeen/briefs/dd10c'
KEY = 'dd10c'
MAP_ID = 9161

# Map qbits: provisional block 117240-117279 (A8's brief); quest bits are A3's q-d7.
QBITS = {'arrived_once': 117240, 'refill_c': QD7['refill_c'], 'dug': QD7['dug']}
ITEMS = {'diamond_rock': ROCKS['diamond']}

# Phase 5 switches (D-27): the exit onto D6 (A6 plans D6's adit; its arrival point measured on the installed D6) and the
# monsters (A2 picks D6's families: no Lava Roach, Arachnoid Queen or Sand Golem; 20 at 38-50).
D6_LIVE = True                  # phase 5 (D-62): D6 installed, its door:dd10c lands at this map's entrance:d6_adit
D6_ARRIVAL = 'entrance:dd10c_adit'   # D6's named arrival (-9216, -16384, 2688) facing 512, outside the north adit
PHASE5_MONSTERS = True

GEM_DAMAGE = 28     # fire, every member: the false vein (D-27), scaled to Act V: 10-24 % of a level-48 member (NOTES)

# The seam: the engine's lava (the liquid shader's lavatyl, MM6's lava face; no picture). 6d18's own floor 6voltyl is
# its volcanic tile, drawn as grey stone by the engine (NOTES, DECIDE).
SEAM_LAVA = {'texture': 'lavatyl', 'liquid': 'lava'}
ROCK_BLACK = LAVA_ROCK                   # MM6 Gharik's Forge 6d18 vlcwl3a: black, glittering cooled lava rock
THEMES_C = THEMES + [
    {'id': 'theme:lava', 'wall': ROCK_BLACK, 'floor': FLOOR, 'ceiling': ROCK_BLACK, 'reveal': ROCK_BLACK,
     'door': DOOR_PLANKS,
     'notes': "The lava gallery: 6d18's black cooled-lava rock (vlcwl3a) on walls and roof, 7d35's cfb1 underfoot."},
    # Session 23 (A8, review row 52): the cold nest read as warm as the rest of the mine. Its own theme: MM6's blue-grey
    # broken volcanic stone (vlcflord, 6d18's family) on walls and roof, hoarfrost underfoot (MM7's 7snow), under a pale
    # blue light, with ice (the white crystal clusters) in its corners: the heat has gone out of this pocket.
    {'id': 'theme:cold', 'wall': S('vlcflord', 128, 128, scale=2), 'floor': S('7snow', 128, 128),
     'ceiling': S('vlcflord', 128, 128, scale=2), 'reveal': S('vlcflord', 128, 128, scale=2), 'door': DOOR_PLANKS,
     'notes': "The cold nest: 6d18's blue-grey broken stone (vlcflord) on walls and roof, frost (7snow) underfoot."},
    {'id': 'theme:black', 'wall': ROCK, 'floor': FLOOR, 'ceiling': ROCK_BLACK, 'reveal': ROCK, 'door': DOOR_PLANKS,
     'notes': "The diamond cavern: 7d35's cwb1 walls (the veins' own ground: xdvdiam is painted on cwb1) under a roof "
              "of 6d18's black vlcwl3a."},
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms (outlines counter-clockwise; 0-based edges from point i to i+1)

ADIT_W = 192

_adit_plats, _adit_beams = [], []
for yy in (288, 608):
    p, b = timber_set('y', yy, -ADIT_W, ADIT_W, 352)
    _adit_plats += p
    _adit_beams += b
_adit_plats += rails(0, 48, 0, 840)

# The lava gallery: the adit's door in edge 0 (south), the diamond cavern in edge 4 (east), the collapse's door in
# edge 6 (north). The seam lies in a bay of the south wall east of the adit's door (edges 1-3), off the walking lines.
LAVA_G = [F(-512, 960), F(512, 960), F(640, 768), F(1856, 704), F(2176, 1024), F(2176, 1664), F(1152, 1728),
          F(-512, 1728)]
SEAM = [F(736, 832), F(1792, 784), F(1984, 976), F(1920, 1056), F(1536, 1024), F(1088, 1008), F(704, 976)]

# The diamond cavern: the lava gallery opens in edge 9 (west), the grotto's door in edge 4 (east), the nest opens in
# edge 7 (north). Veins on edges 0, 1, 2, 3, 5; the false vein on edge 8 (north-west, nearest the lava).
DIAM = [F(2304, 896), F(2560, 448), F(3328, 256), F(4096, 448), F(4416, 960), F(4416, 1728), F(4032, 2176),
        F(3392, 2304), F(2752, 2304), F(2304, 1856)]
VEIN_EDGES = [0, 1, 2, 3, 5]
FALSE_EDGE = 8

# The crystal grotto: a geode, its door in edge 7 (west).
GROTTO = [F(4544, 1088), F(4736, 960), F(5120, 960), F(5312, 1152), F(5312, 1536), F(5120, 1728), F(4736, 1728),
          F(4544, 1600)]

# The collapse: the gallery's door in edge 0 (south), the nest opens in edge 2 (east). The fallen roof lies in its
# north-west half.
COLLAPSE = [F(-384, 1856), F(1024, 1856), F(1280, 2112), F(1280, 2816), F(896, 3072), F(-128, 3072), F(-512, 2688),
            F(-512, 2112)]

# The roach nest: the collapse in edge 7 (west), the diamond cavern in edge 2 (south).
NEST = [F(1408, 2240), F(2048, 2240), F(2624, 2432), F(3456, 2432), F(3584, 2816), F(3200, 3264), F(2176, 3264),
        F(1408, 3008)]


def _prism(cx, cy, r, heights, surface, pid=None, notes=None, base=0):
    """A pointed prism standing on the floor (DD-10B's crystals): a hexagon of half width r round (cx, cy), its top
    slanted by the six corner heights."""
    pts = [F(round(cx + r * math.cos(math.radians(a))), round(cy + r * math.sin(math.radians(a))))
           for a in (0, 60, 120, 180, 240, 300)]
    d = {'rise': 0, 'surface': surface, 'top_surface': surface, 'outline': pts, 'top_heights': list(heights)}
    if base:
        d['base'] = base
    if pid:
        d = {'id': pid, **d}
    if notes:
        d['notes'] = notes
    return d


CRYSTAL = S('gcrysc3', 256, 512)        # MM8 d37's crystal, as DD-10B's throne and God: the grotto's geode

# The geode: crystals grown from the grotto's walls (none in front of the door, edge 7, or the chest, east).
_grotto = [
    _prism(4800, 1040, 56, (210, 240, 200, 160, 150, 170), CRYSTAL, notes="Crystal"),
    _prism(5040, 1030, 64, (300, 250, 210, 230, 280, 320), CRYSTAL, notes="Crystal"),
    _prism(5240, 1180, 48, (180, 160, 120, 110, 140, 170), CRYSTAL, notes="Crystal"),
    _prism(5160, 1600, 56, (240, 280, 230, 180, 170, 200), CRYSTAL, notes="Crystal"),
    _prism(4980, 1660, 64, (320, 300, 260, 250, 270, 310), CRYSTAL, notes="Crystal"),
    _prism(4780, 1660, 44, (150, 170, 130, 110, 120, 140), CRYSTAL, notes="Crystal"),
]

# The collapse: a heap of fallen roof (clicked: 'Rubble'): broken slabs tipped every way, in the north-west half, off
# the line from the door (south, x 320) to the nest (east, y 2528); loose boulders among them are decorations.
def _slab(at, size, rise, facing, pid=None, notes="A slab off the roof"):
    d = {'at': F(*at), 'size': F(*size), 'rise': rise, 'facing': facing, 'surface': ROCK, 'top_surface': ROCK,
         'notes': notes}
    if pid:
        d = {'id': pid, **d}
    return d


_rubble = [
    _slab((16, 2688), (224, 160), 136, 20, pid='platform:rubble',
          notes="The fallen roof: the biggest slab of a heap of broken rock ('Rubble')."),
    _slab((-208, 2600), (176, 112), 72, -35),
    _slab((224, 2800), (160, 128), 104, 55),
    _slab((-144, 2848), (144, 96), 48, 10),
    _slab((-16, 2464), (128, 80), 40, -15),
    _slab((288, 2560), (112, 80), 56, 30),
    _slab((-400, 2240), (176, 112), 56, 25),
    _slab((672, 2912), (176, 96), 40, -20),
]

# The cold nest (D-62 Q49): egg cases in clutches along its north wall (black, leathery: 6d18's vlcwl3a), split and
# cold; the middle clutch's first case is the clicked one ('Empty egg cases', evt:eggs).
_eggs = []
for cx, cy, k in ((1760, 3010, 3), (2560, 3150, 4), (3250, 3050, 3)):
    for i in range(k):
        a = math.radians(40 + i * 360 / k)
        _eggs.append(_prism(round(cx + 70 * math.cos(a)), round(cy + 50 * math.sin(a)), 30,
                            (64, 80, 96, 80, 64, 56), ROCK_BLACK, notes="An empty egg case",
                            pid='platform:eggs' if (cx, i) == (2560, 0) else None))

ROOMS = [
    {'id': 'room:adit', 'name': 'North adit', 'outline': rect(-ADIT_W, 0, ADIT_W, 896), 'floor': 0, 'ceiling': 352,
     'theme': 'theme:timbered', 'ambient': 16, 'platforms': _adit_plats, 'beams': _adit_beams,
     'walls': [{'wall': 0, 'panels': [{'id': 'panel:adit_mouth', 'at': 'centre', 'length': 160, 'bottom': 0,
                                       'height': 320, 'surface': S('trim9_32', 32, 64, scale=5),
                                       'notes': "The adit's mouth onto the Forbidden Zone, boarded (sealed until "
                                                "phase 5)."}]}],
     'notes': "The timbered adit under the Forbidden Zone's mountains: the arrival. Two timber sets, the cart rails "
              "running in from the boarded mouth (south) to the plank door into the lava gallery (north)."},
    {'id': 'room:lava', 'name': 'Lava gallery', 'outline': LAVA_G, 'floor': 0, 'rough': {'step': 192, 'depth': 32},
     'ceiling': 448, 'ceiling_points': [F(704, 1344, 576), F(1728, 1344, 544)], 'theme': 'theme:lava', 'ambient': 13,
     'levels': [{'id': 'level:seam', 'outline': SEAM, 'floor': -48, 'edge': ROCK_BLACK, 'surface': SEAM_LAVA,
                 'notes': "The seam of cooling lava along the gallery's south side (6d18's lava)."}],
     'notes': "A drift of black cooled-lava rock along a seam of lava still cooling in its floor; the diamond cavern "
              "at its east end, the collapse behind a door in its north side."},
    {'id': 'room:diamond', 'name': 'Diamond cavern', 'outline': DIAM, 'floor': 0,
     'rough': {'step': 192, 'depth': 32}, 'ceiling': 640,
     'ceiling_points': [F(3328, 1344, 960), F(2816, 1024, 768), F(3840, 1792, 768)], 'theme': 'theme:black',
     'ambient': 13,
     'pillars': [{'outline': [F(3584, 1024), F(3776, 992), F(3840, 1152), F(3712, 1280), F(3584, 1216)],
                  'surface': ROCK_BLACK, 'notes': "A pillar of black rock left standing."},
                 {'outline': [F(2880, 1664), F(3040, 1632), F(3104, 1792), F(2976, 1888), F(2880, 1824)],
                  'surface': ROCK_BLACK, 'notes': "A pillar of black rock left standing."}],
     'stalactites': [{'at': F(2816, 1216), 'radius': 64, 'length': 224},
                     {'at': F(3904, 1792), 'radius': 72, 'length': 256}],
     'walls': [{'wall': e, 'panels': [vein_panel('diamond', n)]} for n, e in enumerate(VEIN_EDGES, 1)] + [
         {'wall': FALSE_EDGE, 'panels': [dict(vein_panel('diamond', 6), id='panel:false_vein',
                                              notes="The false vein (D-27): it explodes once ('A gem exploded!').")]}],
     'notes': "A high cavern under a roof of black rock, two black pillars holding it: five diamond veins in its walls "
              "(q-d7.diamond_veins), one rock each, and a sixth by the lava that is not a vein at all."},
    {'id': 'room:grotto', 'name': 'Crystal grotto', 'outline': GROTTO, 'floor': 0, 'steep_floor': True, 'ceiling': 384,
     'ceiling_points': [F(4928, 1344, 576)], 'theme': 'theme:rock', 'ambient': 14, 'platforms': _grotto,
     'notes': "A geode behind a plank door: crystal grown out of every wall, and a miner who did not get out."},
    {'id': 'room:collapse', 'name': 'The collapse', 'outline': COLLAPSE, 'floor': 0,
     'rough': {'step': 192, 'depth': 32}, 'ceiling': 480,
     'ceiling_points': [F(64, 2688, 704), F(960, 2240, 416)], 'theme': 'theme:rock', 'ambient': 12,
     'platforms': _rubble,
     'notes': "Where the roof came down: a heap of rubble under the hole it left, slabs round it; the nest opens east."},
    {'id': 'room:nest', 'name': 'Cold nest', 'outline': NEST, 'floor': 0, 'rough': {'step': 192, 'depth': 32},
     'ceiling': 448, 'ceiling_points': [F(2496, 2816, 576)], 'theme': 'theme:cold', 'ambient': 14,
     'platforms': _eggs,
     'notes': "A frost-cold cave of dead ash and split egg cases between the collapse and the diamond cavern (D-62 "
              "Q49): blue-grey stone, hoarfrost underfoot, ice in its corners, a pale blue light (session 23)."},
]

OPENINGS = [
    {'id': 'open:adit_lava', 'from': 'room:adit', 'to': 'room:lava', 'link': 'link:c1', 'from_wall': 2, 'to_wall': 0,
     'width': 224, 'height': 320, 'notes': "The adit's plank door."},
    {'id': 'open:lava_diamond', 'from': 'room:lava', 'to': 'room:diamond', 'link': 'link:c2', 'from_wall': 4,
     'to_wall': 9, 'width': 448, 'height': 400},
    {'id': 'open:diamond_grotto', 'from': 'room:diamond', 'to': 'room:grotto', 'link': 'link:c3', 'from_wall': 4,
     'to_wall': 7, 'width': 224, 'height': 320, 'notes': "The grotto's plank door."},
    {'id': 'open:lava_collapse', 'from': 'room:lava', 'to': 'room:collapse', 'link': 'link:c4', 'from_wall': 6,
     'to_wall': 0, 'width': 224, 'height': 320, 'notes': "The collapse's plank door."},
    {'id': 'open:collapse_nest', 'from': 'room:collapse', 'to': 'room:nest', 'link': 'link:c5', 'from_wall': 2,
     'to_wall': 7, 'width': 384, 'height': 352},
    {'id': 'open:nest_diamond', 'from': 'room:nest', 'to': 'room:diamond', 'link': 'link:c6', 'from_wall': 2,
     'to_wall': 7, 'width': 448, 'height': 384},
]

# ---------------------------------------------------------------------------------------------------------------------
# Monster spots (phase 5, D-27): 20 at D6's lower band 38-50, D6's own families (A2 picks; no Lava Roach, Arachnoid Queen
# or Sand Golem). The graph's split per room is kept: lava 4, diamond 6, grotto 2, collapse 4, nest 4; groups 1-5.
# Each spot is (room, group, x, y, slot): slot 'a' the commoner kind, 'b' the heavier one, 'c' (D-62 Q48) a Patrol in
# each of the two drifts nearest the adit (the lava gallery and the collapse).

MONSTER_SPOTS = [
    ('lava', 1, 400, 1450, 'a'), ('lava', 1, 1000, 1500, 'a'), ('lava', 1, 1500, 1450, 'c'),
    ('lava', 1, 1900, 1400, 'a'),
    ('diamond', 2, 2700, 1100, 'a'), ('diamond', 2, 3300, 700, 'a'), ('diamond', 2, 3900, 900, 'b'),
    ('diamond', 2, 4000, 1600, 'a'), ('diamond', 2, 3400, 2000, 'b'), ('diamond', 2, 2700, 1900, 'a'),
    ('grotto', 3, 4800, 1344, 'b'), ('grotto', 3, 5050, 1300, 'a'),
    ('collapse', 4, 0, 2100, 'a'), ('collapse', 4, 600, 2300, 'a'), ('collapse', 4, 900, 2600, 'c'),
    ('collapse', 4, 500, 2950, 'a'),
    ('nest', 5, 1800, 2600, 'a'), ('nest', 5, 2400, 2700, 'a'), ('nest', 5, 3000, 2700, 'b'),
    ('nest', 5, 2800, 3000, 'a'),
]
assert len(MONSTER_SPOTS) == 20
# D-62 Q48: Floating Eye 40 x14, Terrible Eye 50 x4, Patrol 50 x2: 46,000 kill XP, 11.50k per member (MAPS 0 11.5k).
PHASE5_ROWS = {'a': 11570, 'b': 11571, 'c': 11610}
assert [sum(1 for s in MONSTER_SPOTS if s[4] == k) for k in 'abc'] == [14, 4, 2]

MONSTERS = []
if PHASE5_MONSTERS:
    assert all(PHASE5_ROWS.values()), "phase 5: set PHASE5_ROWS from A2's D6 families first"
    for n, (room, group, x, y, slot) in enumerate(MONSTER_SPOTS, 1):
        MONSTERS.append({'id': 'monster:m%02d' % n, 'room': 'room:' + room, 'monster': PHASE5_ROWS[slot],
                         'at': F(x, y), 'facing': 270, 'group': group})

# ---------------------------------------------------------------------------------------------------------------------
# Objects


def deco(i, room, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + room, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


DECORATIONS = [
    deco('adit_torch_w', 'adit', 'torch02', (-ADIT_W, 448), wall='west', notes="A miner's torch."),
    deco('lava_rock_w', 'lava', 'Brnrock0', (690, 900), notes="A rock still glowing at the seam's west end."),
    deco('lava_rock_e', 'lava', 'Brnrock0', (2040, 1150), notes="A glowing rock at the seam's east end."),
    deco('lava_spoil', 'lava', '6rock01', (-400, 1600), notes="Spoil in the gallery's north-west corner."),
    deco('diam_crystal_s', 'diamond', 'crclstr', (3330, 400), notes="Raw crystal under the south veins."),
    deco('diam_crystal_e', 'diamond', 'crys5', (4310, 1680)),
    deco('diam_spoil', 'diamond', '6rock02', (2380, 1760), notes="Spoil by the false vein."),
    deco('diam_skull', 'diamond', '7dec20', (3700, 2150)),
    deco('grotto_miner', 'grotto', 'dec05', (5163, 1494), notes="The dead miner, by his chest."),
    deco('grotto_crystal', 'grotto', 'crys6', (4660, 1180)),
    deco('collapse_torch', 'collapse', 'torch02', (-512, 2400), wall=6, notes="A torch the roof missed."),
    deco('collapse_boulder', 'collapse', 'rock10', (-400, 2700), notes="A boulder off the roof."),
    deco('collapse_boulder_2', 'collapse', 'rock03', (176, 2960), notes="A boulder off the roof."),
    deco('collapse_rocks_2', 'collapse', '6rock02', (-96, 2352)),
    deco('collapse_rocks', 'collapse', '6rock03', (967, 2917)),
    deco('nest_ash_w', 'nest', '7dec11', (1880, 2320), notes="Cold ash."),
    deco('nest_ash_e', 'nest', '7dec11', (3350, 2600), notes="Cold ash."),
    deco('nest_coals', 'nest', '6rock03', (2250, 3120), notes="Cinders gone cold (D-62 Q49: no embers)."),
    deco('nest_bones', 'nest', 'dec29', (2900, 3150), notes="What the brood was fed."),
    # Session 23: ice in the nest's corners and by its north wall (white crystal clusters under the blue light),
    # clear of the ways in from the collapse (west, y 2432-2816) and to the diamond cavern (south, x 2816-3264).
    deco('nest_ice_sw', 'nest', 'crys6', (1560, 2320), notes="Ice."),
    deco('nest_ice_e', 'nest', 'crclstr', (3440, 2830), notes="Ice."),
    deco('nest_ice_nw', 'nest', 'crys5', (2000, 3150), notes="Ice."),
]

LIGHTS = [
    {'id': 'light:adit', 'room': 'room:adit', 'at': F(0, 448), 'height': 280, 'radius': 900,
     'color': F(255, 180, 110)},
    {'id': 'light:lava_w', 'room': 'room:lava', 'at': F(1024, 880), 'height': 112, 'radius': 900,
     'color': F(255, 110, 40), 'notes': "The seam's glow."},
    {'id': 'light:lava_e', 'room': 'room:lava', 'at': F(1664, 864), 'height': 112, 'radius': 900,
     'color': F(255, 110, 40), 'notes': "The seam's glow."},
    {'id': 'light:lava_room', 'room': 'room:lava', 'at': F(256, 1472), 'height': 360, 'radius': 900,
     'color': F(220, 150, 110)},
    {'id': 'light:diam_w', 'room': 'room:diamond', 'at': F(2880, 1280), 'height': 520, 'radius': 1300,
     'color': F(210, 220, 255)},
    {'id': 'light:diam_e', 'room': 'room:diamond', 'at': F(3840, 1408), 'height': 520, 'radius': 1300,
     'color': F(210, 220, 255)},
    {'id': 'light:diam_lava', 'room': 'room:diamond', 'at': F(2496, 1344), 'height': 200, 'radius': 700,
     'color': F(255, 120, 50), 'notes': "The lava's glow spilling in from the gallery."},
    {'id': 'light:grotto', 'room': 'room:grotto', 'at': F(4928, 1344), 'height': 320, 'radius': 800,
     'color': F(170, 230, 255), 'notes': "The geode's cold glow."},
    {'id': 'light:collapse', 'room': 'room:collapse', 'at': F(448, 2304), 'height': 380, 'radius': 1100,
     'color': F(220, 190, 150)},
    {'id': 'light:nest', 'room': 'room:nest', 'at': F(2496, 2752), 'height': 300, 'radius': 1400,
     'color': F(160, 200, 255), 'notes': "The cold nest: a pale blue light on frost and dead ash (D-62 Q49, session 23)."},
]
for n, e in enumerate(VEIN_EDGES, 1):
    LIGHTS.append(dict(vein_light('diamond', n, wall_point(DIAM, e, None, out=96)), room='room:diamond'))
LIGHTS.append(dict(vein_light('diamond', 6, wall_point(DIAM, FALSE_EDGE, None, out=96)), id='light:false_vein',
                   room='room:diamond', notes="The false vein glints like the rest."))

SOUNDS = [
    {'id': 'sound:adit_wind', 'room': 'room:adit', 'at': F(0, 96), 'sound': 'whistling wind', 'radius': 1000,
     'inner_radius': 200, 'volume': 0.35, 'notes': "Air drawn in at the boarded mouth."},
    {'id': 'sound:lava', 'room': 'room:lava', 'at': F(1280, 880), 'sound': 'lava loop', 'radius': 1400,
     'inner_radius': 400, 'volume': 0.45, 'notes': "The seam bubbling as it cools."},
    {'id': 'sound:diam_drip', 'room': 'room:diamond', 'at': F(3712, 1920), 'sound': 'drip02', 'radius': 1300,
     'inner_radius': 300, 'volume': 0.4, 'notes': "Seepage in the cavern."},
    {'id': 'sound:collapse_rumble', 'room': 'room:collapse', 'at': F(64, 2688), 'sound': 'rumble', 'radius': 1200,
     'inner_radius': 300, 'volume': 0.3, 'notes': "The roof settling."},
    {'id': 'sound:grotto_hum', 'room': 'room:grotto', 'at': F(4928, 1344), 'sound': 'humming', 'radius': 800,
     'inner_radius': 200, 'volume': 0.3, 'notes': "The geode hums."},
]

DOORS = [
    door('adit', 'open:adit_lava', notes="The adit's plank door into the lava gallery."),
    door('grotto', 'open:diamond_grotto', notes="The plank door from the diamond cavern into the crystal grotto."),
    door('collapse', 'open:lava_collapse', hinge='right', notes="The plank door from the lava gallery into the collapse."),
]

CHESTS = [
    {'id': 'chest:grotto', 'room': 'room:grotto', 'at': F(5240, 1344), 'kind': 'ch3', 'treasure_level': 5, 'random_items': 2, 'gold': 1500,
     'notes': "The dead miner's chest in the geode (treasure 5, Act V: D-27)."},
]

EXITS = []
if D6_LIVE:
    EXITS = [{'id': 'exit:d6', 'room': 'room:adit', 'wall': 'south', 'size': F(160, 320),
              'surface': S('7solid01', 32, 64, scale=5), 'to': 'exit:d6_adit',
              'notes': "The adit's mouth, boarded: out to D6 below the north adit."}]
    ROOMS[0].pop('walls')

OBJECTS = {
    'format': 0,
    'start': {'room': 'room:adit', 'at': F(0, 192), 'facing': 90,
              'notes': "Just inside the adit's mouth, facing in (north); D6's door into this map (phase 5, A6) lands "
                       "the party here."},
    'doors': DOORS,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'chests': CHESTS,
    'decorations': DECORATIONS,
    'notes': "DD-10C's contents, written by output/studio_cal/dd10c/tools/gen.py: 3 plank doors, 1 chest, the exit to D6, "
             "20 monsters (D-62: Floating Eye 11570 x14, Terrible Eye 11571 x4, Patrol 11610 x2 on MONSTER_SPOTS).",
}
if MONSTERS:
    OBJECTS['monsters'] = MONSTERS
if EXITS:
    OBJECTS['exits'] = EXITS

# ---------------------------------------------------------------------------------------------------------------------
# Wiring

VARIABLES = [vein_var('diamond', n) for n in range(1, 6)] + ['false_vein'] + [VISIT_VAR]


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


SEALED_LINE = "Boards and fallen rock close the adit's mouth from outside. There is no way out here yet."
EVENTS = [
    arrival_event("THE GEMSTONE MINES, NORTH POCKET. Heat breathes out of the rock, and somewhere ahead lava ticks as "
                  "it cools. Hector the diamond smith wants five diamond rocks; the veins give one each. Few who come "
                  "here go back, they say."),
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load', 'text': "Hot air, black rock, the tick of cooling lava.",
     'notes': "Every entry: a status line."},
    refill_event('refill_c', ['diamond']),
    visit_end_event(),
    {'id': 'evt:door_adit', 'preset': 'door', 'source': 'door:adit', 'title': 'Door'},
    {'id': 'evt:door_grotto', 'preset': 'door', 'source': 'door:grotto', 'title': 'Door'},
    {'id': 'evt:door_collapse', 'preset': 'door', 'source': 'door:collapse', 'title': 'Door'},
    {'id': 'evt:chest_grotto', 'preset': 'chest', 'source': 'chest:grotto', 'title': 'Chest'},
    *vein_events('diamond'),
    false_vein_event('diamond', 'panel:false_vein', GEM_DAMAGE),
    text('rubble', 'platform:rubble', 'Rubble', "Rubble from a fallen roof. Nothing under it but more rock.",
         notes="The graph's 'Rubble' (the collapse)."),
    text('eggs', 'platform:eggs', 'Empty egg cases',
         "Split and cold. Whatever hatched here was eaten by whatever lives here now.",
         notes="The cold nest (D-62 Q49): map-local line for A3."),
]
if D6_LIVE:
    EVENTS.append(exit_event('exit:d6'))
else:
    EVENTS.append(text('adit_mouth', 'panel:adit_mouth', 'Adit', SEALED_LINE,
                       notes="Sealed until phase 5 (D-27; D6 not built): becomes the exit preset to exit:d6_adit "
                             "(gen.py D6_LIVE)."))

WIRING = {'format': 0, 'variables': VARIABLES, 'events': EVENTS,
          'notes': "DD-10C's events (gen.py, mine.py): the five diamond veins (q-d7.diamond_veins: one rock each, a map "
                   "variable each) and the false vein (D-27), the refill on entry (q-d7.refill_c), the rubble, the "
                   "cold nest's egg cases, the exit to D6, doors, the chest."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

PROJECT = {
    'format': 0, 'id': 'xeen_dd10c', 'name': 'Gemstone Mines, north pocket', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-10C', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(12, 7), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 5, 'trap_dice': 5,
        'perception_difficulty': 8, 'refill_days': 672, 'music': MUSIC, 'environment': 'cave', 'lock_difficulty': 10,
        # D-62 Q50: one slot, eyes at Dif 0 (Floating Eye 40 only; Dif 1+ can roll the Gamma Gazer 65, a robot slot
        # the Autobot 75); the Patrols are placed by row id only.
        'slots': [{'monster': 'Xeen Eye', 'tier': 0, 'per_marker': F(2, 3), 'weight': 100}],
    },
    'neighbours': [{
        'id': 'exit:d6_adit', 'to': 'xeen_d6.odm', 'kind': 'door', 'arrival': D6_ARRIVAL,
        'arrival_hint': "On D6 (the Forbidden Zone), outside the Gemstone Mines' north adit, facing away from it "
                        "(A6's entrance:dd10c_adit, (-9216, -16384, 2688) facing 512).",
        'direction': 90,                 # facing north on D6, away from the adit (entrance:dd10c_adit's 512)
        'notes': "Live since phase 5 (D-62; D6 installed): the adit's mouth is the exits object exit:d6 with the exit "
                 "preset. D6's door:dd10c lands at this map's entrance:d6_adit (the start): (0, 192, 0), facing north "
                 "(90, game 512)."}],
    'qbits': QBITS,
    'items': ITEMS,
    'notes': "Xeen design brief, DD-10C Gemstone Mines, north pocket (D6; Q-D7), class S, built from the MU-6 graph "
             "(devdocs/xeen/mockups/act3_graphs/dd10c.graph.yml) with decider D-27 (mockups/act3_a8_decisions_b.md): "
             "Act V, party 48-51, 40-50, 20 monsters (D-62: Floating Eye 14, Terrible Eye 4, Patrol 2), treasure 5, "
             "music 18. Geometry, veins, refill, false vein, lava seam, lights, sounds and dressing built in phase 3 "
             "; monsters, the exit to D6 and the install in phase 5 (D-62). Quest bits: q-d7.refill_c "
             "113143, q-d7.dug 113144 (A3); the map's arrived_once 117240 (provisional block 117240-117279). Items: "
             "diamond rock 12360 (the hook's map_gives, one per vein). Map card (D-62 Q50): encounter 10, Floating Eye at Dif 0 only (A2's 9161).",
}

if not D6_LIVE:
    PROJECT['neighbours'][0]['listed_only'] = True

# ---------------------------------------------------------------------------------------------------------------------
# Plan

PHASE5_NAMES = {'a': 'Floating Eye', 'b': 'Terrible Eye', 'c': 'Patrol'}
PHASE5_LEVELS = {'a': 40, 'b': 50, 'c': 50}


def _pop(room):
    """The placed monsters of one room (MONSTER_SPOTS) as plan population entries."""
    out = []
    for k in 'abc':
        n = sum(1 for s in MONSTER_SPOTS if s[0] == room and s[4] == k)
        if n:
            out.append(placed('%s (%d)' % (PHASE5_NAMES[k], PHASE5_ROWS[k]), n, PHASE5_LEVELS[k]))
    return out


ROCK_T = "MM7 Nighon Tunnels (7d35): cwb1 rock walls and roofs, cfb1 underfoot"
TIMBER_T = ROCK_T + "; trim9_32 timber sets and trim9_32a lagging overhead"
LAVA_T = "MM6 Gharik's Forge (6d18): black vlcwl3a rock, 6voltyl lava in the seam; 7d35's cfb1 underfoot"
SPACES = [
    sp('adit', 'North adit', 'corridor', 'S', (384, 896), 0, 352,
       "The timbered adit under the Forbidden Zone's mountains: the arrival and the exit to D6.", TIMBER_T,
       empty=True, safe=True),
    sp('lava', 'Lava gallery', 'room', 'M', (2688, 768), 0, F(448, 576),
       "A drift along a seam of cooling lava; heat shimmer. 3 Floating Eyes and a Patrol.", LAVA_T, pop=_pop('lava')),
    sp('diamond', 'Diamond cavern', 'room', 'L', (2112, 2048), 0, F(640, 960),
       "Five diamond veins in black rock (q-d7.diamond_veins), one rock each; one false vein ('A gem exploded!'). "
       "4 Floating Eyes, 2 Terrible Eyes.", "7d35's cwb1 walls, 6d18's black vlcwl3a roof and pillars; A6's diamond vein xdvdiam",
       pop=_pop('diamond')),
    sp('grotto', 'Crystal grotto', 'room', 'S', (768, 768), 0, F(384, 576),
       "A geode; a dead miner's chest. A Floating Eye and a Terrible Eye.", ROCK_T + "; MM8 d37's crystal gcrysc3",
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 5, 'items': F(2, 2), 'notes': "The dead miner's chest."}],
       pop=_pop('grotto')),
    sp('collapse', 'The collapse', 'room', 'M', (1792, 1216), 0, F(416, 704),
       "Rubble from a fallen roof ('Rubble'). 3 Floating Eyes and a Patrol.", ROCK_T, pop=_pop('collapse')),
    sp('nest', 'Cold nest', 'room', 'M', (2176, 1024), 0, F(448, 576),
       "Cold ash and split egg cases ('Empty egg cases', D-62 Q49). 3 Floating Eyes, a Terrible Eye.",
       ROCK_T + "; 6d18's black vlcwl3a egg cases", pop=_pop('nest')),
]

LINKS = [
    link('c1', 'adit', 'lava', 'door', motion='swing'),
    link('c2', 'lava', 'diamond', 'open'),
    link('c3', 'diamond', 'grotto', 'door', motion='swing'),
    link('c4', 'lava', 'collapse', 'door', motion='swing'),
    link('c5', 'collapse', 'nest', 'open'),
    link('c6', 'nest', 'diamond', 'open'),
]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "The north pocket of the Gemstone Mines, under the Forbidden Zone's mountains: a timbered adit, a "
                 "gallery of black rock along a seam of cooling lava, and at its end a high cavern with five diamond "
                 "veins (and one that explodes); a geode behind a door; round the other way a collapse and a cold nest "
                 "of dead ash and split egg cases.",
        'purpose': "Q-D7 The Gemsmiths (repeatable): diamond rocks for Hector on D1 (D-27: Act V, the only diamonds). "
                   "Party 48-51; 40-50; 20 monsters (Floating Eye 14, Terrible Eye 4, Patrol 2, D-62); treasure 5. About 10 minutes.",
        'mood': "Heat and black rock: lava light in the gallery, cold white glints in the diamond cavern.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'loops': [{'id': 'loop:c', 'spaces': ['room:lava', 'room:diamond', 'room:nest', 'room:collapse'],
                   'notes': "North: round the diamond cavern."}],
        'entrances': [{'id': 'entrance:d6_adit', 'space': 'room:adit', 'kind': 'both', 'neighbour': 'exit:d6_adit',
                       'facing': 'n', 'how': "Just inside the adit's mouth, facing in (D6's door:dd10c, D-37)."}],
        'critical_path': ['room:adit', 'room:lava', 'room:diamond'],
        'return_path': ['room:diamond', 'room:nest', 'room:collapse', 'room:lava', 'room:adit'],
        'goals': [
            {'id': 'goal:diamond', 'space': 'room:diamond', 'kind': 'take',
             'what': "Five diamond rocks from the five diamond veins (q-d7.diamond_veins).", 'handed_in_at': 'D1'}],
        'atmosphere': "Torchlit timber in the adit (ambient 16), the caves dark (12-14): lava light along the seam, "
                      "white glints at the veins, a cold glow in the geode, cold grey light on the dead ash of the nest. Music 18. Sounds: air "
                      "at the boarded mouth, the lava, seepage in the cavern, the collapse settling, the geode's hum.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': 1, 'doors': 3, 'fixed_actors': 20, 'loops': 1, 'monsters_about': 20, 'rooms': 6,
                   'sectors': 6, 'spawn_points': 0, 'floor_area_millions': 11},
        'notes': "Class S (MAPS, Dungeons): at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 "
                 "doors. D-27/D-62: Act V; 20 monsters (Floating Eye 14, Terrible Eye 4, Patrol 2); the exit to D6; five "
                 "veins, one rock each, a map variable each; refill_c on entry; one false vein; 7d35 with A6's "
                 "diamond vein and 6d18's lava.",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    elif level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return d


DIAGRAM = """   [The collapse: rubble]---(open)---[Cold nest: dead ash, split egg cases]
          |                                  |
        =door=                             (open)
          |                                  |
   [Lava gallery: the seam]------(open)------[DIAMOND CAVERN: 5 veins + 1 false]--=door=--[Crystal grotto $]
          |
        =door=
          |
   [North adit]---exit---D6: the north adit (entrance:dd10c_adit)

 $ chest   = = plank door   One level at 0, the lava seam sunk 48. Veins: one rock each until the God (DD-10B) is paid.
 Monsters 20 (D-62): Floating Eye 14, Terrible Eye 4, Patrol 2 (lava 4, cavern 6, grotto 2, collapse 4, nest 4).
"""

# D-89 identity (lane A8 s28): crystals frame every vein, the false one too (mine.py); timber sets, rails and an
# abandoned cart carried into the lava gallery's west end; the cold nest's floor slopes.
vein_crystals(ROOMS)
_RC = {r['id'].split(':')[1]: r for r in ROOMS}
_lp, _lb = [], []
for _x in (-256, 192):
    _p, _b = timber_set('x', _x, 960, 1728, 448)
    _lp += _p
    _lb += _b
_RC['lava'].setdefault('platforms', []).extend(_lp + rails(0, 1000, 0, 1400) +
                                               cart(-320, 1296, 90, "A cart the miners left when the lava came."))
_RC['lava']['beams'] = _RC['lava'].get('beams', []) + _lb
_RC['lava']['notes'] += " Its west end still timbered, the rails running in from the adit to an abandoned cart."
_RC['collapse']['floor_points'] = [F(64, 2624, 48), F(896, 2304, 16), F(512, 2880, 32)]
_RC['diamond']['floor_points'] = [F(3328, 1344, 48), F(2816, 1088, 24), F(3904, 1664, 32), F(3328, 768, 16)]
_RC['nest']['floor_points'] = [F(2048, 2688, 40), F(3072, 2688, 24), F(2496, 3008, 56)]
IDENTITY = {'shape': 'mine', 'family': '7d35',
            'seen': ["a timbered adit and the lava gallery's timbered west end: rails, an abandoned cart, lava cooling "
                     "in the seam",
                     "the diamond cavern under its black roof, every vein framed by crystal growing out of the rock",
                     "the crystal grotto's geode, the collapse's heap of fallen roof, the cold nest's split egg cases"]}

ROOMS_DOC = {'format': 0, 'themes': THEMES_C, 'defaults': {'theme': 'theme:rock', 'ambient': 14}, 'rooms': ROOMS,
             'openings': OPENINGS,
             'notes': "DD-10C at L3/L4: six rooms in the plan's frame (x east, y north, the adit's mouth at y 0). "
                      "Written by output/studio_cal/dd10c/tools/gen.py with output/studio_cal/dd10a/tools/mine.py."}

if __name__ == '__main__':
    write_levels(OUT, sys.argv[1:] or ['L1', 'L2', 'L3', 'L4'], PROJECT, plan, DIAGRAM, ROOMS_DOC, OBJECTS, WIRING, IDENTITY)
