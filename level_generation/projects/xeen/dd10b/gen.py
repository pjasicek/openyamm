"""DD-10B Gemstone Mines, east pocket: writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd10b/L*).

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd10b), phase 3, decider D-27.
Shared with DD-10A and DD-10C: level_generation/projects/xeen/dd10a/mine.py (themes, timber, carts, veins, refill, false vein,
exit), imported, not copied, so one change reaches all three pockets.
Plan frame: x east, y north, the adit's mouth at y 0 (the party comes in from D2 going north). Upper level at 0 (adit,
upper drift, side cut, sapphire hall, throne hall); the deep level at -480 (flooded drift, the God of Minerals' hall),
reached by the spiral ramp off the drift (down) and the stair behind the throne (up): one loop, as the graph draws it.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd10a')
from mine import *  # noqa: E402,F401,F403

OUT = R + '/devdocs/xeen/briefs/dd10b'
KEY = 'dd10b'
MAP_ID = 9160

# Map qbits: provisional block 117200-117239 (A8's brief); quest bits are A3's q-d7.
QBITS = {'arrived_once': 117200, 'refill_b': QD7['refill_b'], 'dug': QD7['dug']}
ITEMS = {'sapphire_rock': ROCKS['sapphire']}

# D2's adit (thing:dd10b_adit, D2 event 44 on the installed xeen_d2.odm), in the Gemstone foothills' rock face about
# (-15360, 17300, 1700). A6's return point for event 44: (-15360, 16384, 1696) facing 1536 (south, studio direction
# 270), away from the adit.
D2_ARRIVAL = [-15360, 16384, 1696]

GEM_DAMAGE = 16     # fire, every member: the false vein (D-27), as DD-10A's bones (same band)
DEEP = -480         # the deep level's floor

# MM8 d37's crystal (XD-09's diamond level) for the God's crystals and the throne's inlay: its native 64 x 128 laid at
# scale 4 (one picture over a crystal's height, no visible repeat), drawn see-through and tinted a deep sapphire blue so
# it reads as crystal in 7d35's dark rock rather than a saturated cyan block.
CRYSTAL = S('gcrysc3', 64, 128, scale=4, translucent={'opacity': 0.8, 'tint': F(0.38, 0.52, 0.85)})
CUT_STONE = S('cwb', 128, 256)          # 7d35's dressed stone: the throne's body
GOLD_ROCK = S('cwb1gold', 128, 256)     # 7d35's gold-veined rock: the God of Minerals' hall

THEMES_B = THEMES + [
    {'id': 'theme:gold', 'wall': GOLD_ROCK, 'floor': FLOOR, 'ceiling': ROCK, 'reveal': ROCK, 'door': DOOR_PLANKS,
     'notes': "The God of Minerals' hall: 7d35's gold-veined cwb1gold walls under cwb1 rock, cfb1 underfoot."},
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms

ADIT_W = 192
DRIFT_W = 448
DRIFT_CEIL = 416

_adit_plats, _adit_beams = [], []
for yy in (288, 608):
    p, b = timber_set('y', yy, -ADIT_W, ADIT_W, 352)
    _adit_plats += p
    _adit_beams += b
_adit_plats += rails(0, 48, 0, 840)

_drift_plats, _drift_beams = [], []
for yy in (1408, 1856):
    p, b = timber_set('y', yy, -DRIFT_W // 2, DRIFT_W // 2, DRIFT_CEIL)
    _drift_plats += p
    _drift_beams += b
for xx in (640, 1664):
    p, b = timber_set('x', xx, 2304 - DRIFT_W // 2, 2304 + DRIFT_W // 2, DRIFT_CEIL)
    _drift_plats += p
    _drift_beams += b

_cut_plats = cart(1152, 2980, 0, "An ore cart full of spoil, left in the side cut.", pid='platform:cart')

# The sapphire hall (counter-clockwise; 0-based edges from point i to i+1): the drift opens in edge 8 (west), the
# throne hall's door in edge 3 (east); veins on edges 0, 1, 4, 5, 6; the false vein on edge 7.
SAPH = [F(2048, 1664), F(2816, 1600), F(3584, 1728), F(3840, 2048), F(3840, 2816), F(3456, 3200), F(2688, 3264),
        F(2176, 3072), F(1920, 2688), F(1920, 2048)]
# The throne hall: a worked octagon; the stair down in edge 0 (south), the sapphire hall's door in edge 6 (west).
THRONE = [F(4096, 1920), F(4864, 1920), F(4992, 2048), F(4992, 2816), F(4864, 2944), F(4096, 2944), F(3968, 2816),
          F(3968, 2048)]
# The flooded drift (floor DEEP): the ramp comes in at edge 4 (west), the God's hall opens off edge 1 (east).
FLOOD = [F(2304, -256), F(3712, -192), F(3712, 832), F(3200, 896), F(2304, 768)]
# The God of Minerals' hall (floor DEEP): the stair in edge 4 (north), the flooded drift in edge 6 (west), the God in
# edge 2 (east).
GOD = [F(3840, -256), F(4864, -256), F(5120, 0), F(5120, 704), F(4864, 960), F(4096, 960), F(3840, 704)]

# The throne: crystal (gcrysc3), facing west at the hall's east side, beside the stair down (D-27: flavour only).
_throne = [
    {'id': 'platform:throne_dais', 'at': F(4800, 2432), 'size': F(256, 384), 'rise': 32, 'surface': CUT_STONE,
     'top_surface': FLOOR, 'notes': "The throne's dais, one step of dressed stone."},
    {'id': 'platform:throne', 'at': F(4832, 2432), 'size': F(128, 176), 'rise': 80, 'base': 32, 'surface': CUT_STONE,
     'top_surface': CUT_STONE, 'notes': "The Gem maker's throne: a seat of dressed stone."},
    {'id': 'platform:throne_back', 'at': F(4912, 2432), 'size': F(32, 208), 'rise': 400, 'base': 32,
     'surface': CUT_STONE, 'top_surface': CUT_STONE, 'notes': "The throne's back, a slab of dressed stone."},
    {'at': F(4890, 2432), 'size': F(12, 112), 'rise': 224, 'base': 176,
     'surface': CRYSTAL, 'end_surface': dict(CUT_STONE, uneven=True), 'top_surface': dict(CUT_STONE, uneven=True),
     'notes': "A great sapphire-blue crystal set in the throne's back."},
    {'at': F(4832, 2324), 'size': F(128, 24), 'rise': 160, 'base': 32, 'surface': CUT_STONE,
     'top_surface': CUT_STONE, 'notes': "The throne's arm"},
    {'at': F(4832, 2540), 'size': F(128, 24), 'rise': 160, 'base': 32, 'surface': CUT_STONE,
     'top_surface': CUT_STONE, 'notes': "The throne's arm"},
]

def _prism(cx, cy, r, heights, pid=None, notes=None):
    """A crystal prism standing on the floor: a hexagon of half width r round (cx, cy), its top slanted by the six
    corner heights."""
    import math
    pts = [F(round(cx + r * math.cos(math.radians(a))), round(cy + r * math.sin(math.radians(a))))
           for a in (0, 60, 120, 180, 240, 300)]
    d = {'rise': 0, 'surface': CRYSTAL, 'top_surface': CRYSTAL, 'outline': pts, 'top_heights': list(heights)}
    if pid:
        d = {'id': pid, **d}
    if notes:
        d['notes'] = notes
    return d


# The God of Minerals (q-d7.god_of_minerals): a great crystal grown out of the east wall of his hall, with lesser
# crystals round it; the great one is clicked. D-37 (4), session 7: the crystals stand below his face (xdgodface on the
# east wall), the great one at his chin, so his eyes and brow show over them.
_god = [
    _prism(4976, 352, 96, (230, 260, 250, 215, 205, 220), pid='platform:god',
           notes="The God of Minerals: a great crystal grown out of the rock, humming."),
    _prism(4992, 176, 64, (150, 170, 140, 120, 125, 135), notes="A lesser crystal"),
    _prism(4992, 536, 64, (170, 145, 130, 140, 160, 180), notes="A lesser crystal"),
    _prism(4864, 256, 40, (140, 160, 120, 100, 110, 130), notes="A lesser crystal"),
    _prism(4872, 456, 48, (180, 150, 130, 150, 190, 200), notes="A lesser crystal"),
]

ROOMS = [
    {'id': 'room:adit', 'name': 'East adit', 'outline': rect(-ADIT_W, 0, ADIT_W, 896), 'floor': 0, 'ceiling': 352,
     'theme': 'theme:timbered', 'ambient': 18, 'platforms': _adit_plats, 'beams': _adit_beams,
     'notes': "The timbered adit in the Gemstone foothills: the arrival. Two timber sets, the cart rails running in "
              "from the mouth (the exit, south) to the plank door into the upper drift (north)."},
    {'id': 'room:upper', 'name': 'Upper drift', 'path': [F(0, 1024), F(0, 2304), F(1792, 2304)], 'width': DRIFT_W,
     'floor': 0, 'ceiling': DRIFT_CEIL, 'theme': 'theme:timbered', 'ambient': 15, 'platforms': _drift_plats,
     'beams': _drift_beams,
     'notes': "A long timbered drift north from the adit's door, then east to the sapphire hall; a side cut off its "
              "north side, the spiral ramp down off its south side."},
    {'id': 'room:cut', 'name': 'Side cut', 'outline': rect(896, 2656, 1408, 3136), 'floor': 0, 'ceiling': 352,
     'theme': 'theme:timbered', 'ambient': 14, 'platforms': _cut_plats,
     'notes': "A side cut off the drift where the miners stopped: a cart of spoil and their chest."},
    {'id': 'room:sapphire', 'name': 'Sapphire hall', 'outline': SAPH, 'floor': 0,
     'rough': {'step': 192, 'depth': 32}, 'ceiling': 576,
     'ceiling_points': [F(2880, 2432, 832), F(2432, 2816, 704), F(3328, 2048, 704)], 'theme': 'theme:rock',
     'ambient': 15,
     'pillars': [{'outline': [F(2752, 2304), F(2944, 2272), F(3008, 2432), F(2912, 2560), F(2752, 2496)],
                  'surface': ROCK, 'notes': "A rock pillar left to hold the hall's roof."}],
     'stalactites': [{'at': F(2368, 2240), 'radius': 64, 'length': 192},
                     {'at': F(3392, 2880), 'radius': 72, 'length': 224}],
     'walls': [
         {'wall': 0, 'panels': [vein_panel('sapphire', 1)]},
         {'wall': 1, 'panels': [vein_panel('sapphire', 2)]},
         {'wall': 4, 'panels': [vein_panel('sapphire', 3)]},
         {'wall': 5, 'panels': [vein_panel('sapphire', 4)]},
         {'wall': 6, 'panels': [vein_panel('sapphire', 5)]},
         {'wall': 7, 'panels': [dict(vein_panel('sapphire', 6), id='panel:false_vein',
                                     notes="The false vein (D-27): it explodes once ('A gem exploded!').")]},
     ],
     'notes': "A high cave round a rock pillar: five sapphire veins in its walls (q-d7.sapphire_veins), one rock each, "
              "and a sixth that is not a vein at all."},
    {'id': 'room:throne', 'name': "Gem maker's throne", 'outline': THRONE, 'floor': 0, 'ceiling': 512,
     'ceiling_levels': [{'ceiling': 704, 'top_scale': 0.5}], 'theme': 'theme:rock', 'ambient': 16,
     'platforms': _throne,
     'notes': "A hall cut square in the rock: a throne of dressed stone with a crystal in its back at its east side ('Gem maker's throne'), the "
              "stair down to the God of Minerals behind it in the south wall."},
    {'id': 'room:stair', 'name': 'Throne stair', 'outline': rect(4416, 1088, 4800, 1792), 'floor': 0,
     'slope': {'to': DEEP, 'toward': 'south', 'steps': 12, 'tread': FLOOR, 'riser': TIMBER_H}, 'ceiling': 384,
     'ceiling_slope': {'to': DEEP + 384, 'toward': 'south'}, 'theme': 'theme:rock', 'ambient': 14,
     'notes': "Twelve steps cut in the rock, down from the throne hall to the God of Minerals."},
    {'id': 'room:ramp', 'name': 'Spiral ramp',
     'path': [[1280, 1952, 0], [1280, 1280, -128], [704, 1280, -224], [704, 384, -352], [2240, 384, DEEP]],
     'width': 320, 'floor': 0, 'ceiling': 320, 'theme': 'theme:rock', 'ambient': 13,
     'notes': "A ramp that winds down round the rock core, south, west, south and east, from the drift to the deep "
              "level's flooded drift."},
    {'id': 'room:flooded', 'name': 'Flooded drift', 'outline': FLOOD, 'floor': DEEP,
     'rough': {'step': 192, 'depth': 24}, 'ceiling': DEEP + 448, 'ceiling_points': [F(3008, 384, DEEP + 576)],
     'theme': 'theme:rock', 'ambient': 12,
     'levels': [{'id': 'level:flood_pool', 'outline': [F(2560, 512), F(3392, 480), F(3584, 608), F(3456, 768),
                                                        F(2560, 704)],
                 'floor': DEEP - 48, 'edge': ROCK, 'surface': WATER,
                 'notes': "Knee-deep water along the drift's north side."}],
     'notes': "The deep level's drift, its north side under knee-deep water: lava roaches, and a chest the water "
              "has not reached."},
    {'id': 'room:god', 'name': 'The God of Minerals', 'outline': GOD, 'floor': DEEP, 'steep_floor': True,
     'rough': {'step': 192, 'depth': 24}, 'ceiling': DEEP + 576,
     'ceiling_points': [F(4544, 352, DEEP + 768)], 'theme': 'theme:gold', 'ambient': 16,
     'platforms': _god,
     # D-37 (4): the God's face (A6's xdgodface) once on the east wall behind his crystal, hover "God of Minerals".
     'walls': [{'wall': 2, 'panels': [{'id': 'panel:god_face', 'at': 'centre', 'length': 448, 'bottom': 96,
                                       'height': 448, 'surface': S('xdgodface', 256, 256, fit=True),
                                       'notes': "The God of Minerals: a great bearded face in the gold-veined rock, "
                                                "sapphire eyes, his crystal grown out of the rock below his chin."}]}],
     'notes': "The pocket's bottom: gold-veined rock and, in the east wall, the God of Minerals, a face of crystal "
              "(q-d7.god_of_minerals)."},
]

OPENINGS = [
    {'id': 'open:adit_upper', 'from': 'room:adit', 'to': 'room:upper', 'link': 'link:b1', 'width': 224,
     'height': 320, 'notes': "The adit's plank door."},
    {'id': 'open:upper_sapphire', 'from': 'room:upper', 'to': 'room:sapphire', 'link': 'link:b2', 'to_wall': 8,
     'width': 384, 'height': 352},
    {'id': 'open:upper_cut', 'from': 'room:upper', 'to': 'room:cut', 'link': 'link:b8', 'to_wall': 'south',
     'width': 320, 'height': 320},
    {'id': 'open:sapphire_throne', 'from': 'room:sapphire', 'to': 'room:throne', 'link': 'link:b3', 'from_wall': 3,
     'to_wall': 6, 'width': 224, 'height': 320, 'notes': "The throne hall's plank door."},
    {'id': 'open:upper_ramp', 'from': 'room:upper', 'to': 'room:ramp', 'link': 'link:b4', 'from_wall': 1, 'to_wall': 9, 'width': 256,
     'height': 288},
    {'id': 'open:ramp_flooded', 'from': 'room:ramp', 'to': 'room:flooded', 'link': 'link:b5', 'to_wall': 4,
     'width': 224, 'height': 288, 'notes': "The plank door at the ramp's foot."},
    {'id': 'open:flooded_god', 'from': 'room:flooded', 'to': 'room:god', 'link': 'link:b6', 'from_wall': 1,
     'to_wall': 6, 'width': 384, 'height': 352},
    {'id': 'open:throne_stair', 'from': 'room:throne', 'to': 'room:stair', 'link': 'link:b7', 'from_wall': 0,
     'to_wall': 'north', 'width': 320, 'height': 320},
    {'id': 'open:stair_god', 'from': 'room:stair', 'to': 'room:god', 'link': 'link:b9', 'from_wall': 'south',
     'to_wall': 4, 'width': 320, 'height': 320},
]

# ---------------------------------------------------------------------------------------------------------------------
# Monsters (A2's rows; D-27): Electrapede 20 (11361) x6, Lava Roach 26 (11362) x4, Beholder Bat 20 (11312) x6, Stone
# Golem 26 (11581) x4 instead of the graph's Sand Golem: 20, all placed, hostile by their rows.

PEDE, ROACH, BAT, GOLEM = 11361, 11362, 11312, 11581
_pop = [
    ('upper', 1, [(PEDE, 1300, 2400), (PEDE, 380, 2380), (PEDE, 1000, 2180), (BAT, -170, 1250), (BAT, 500, 2170),
                  (BAT, 1400, 2180)]),
    ('sapphire', 2, [(PEDE, 2400, 2000), (PEDE, 3300, 2500), (PEDE, 2500, 2900), (GOLEM, 3200, 2000),
                     (GOLEM, 3100, 2900)]),
    ('throne', 3, [(ROACH, 4300, 2200), (ROACH, 4300, 2700), (GOLEM, 4600, 2150), (GOLEM, 4600, 2750)]),
    ('ramp', 4, [(BAT, 1280, 1500), (BAT, 704, 900), (BAT, 1400, 384)]),
    ('flooded', 5, [(ROACH, 3000, 200), (ROACH, 3400, 0)]),
]
_names = {PEDE: 'pede', ROACH: 'roach', BAT: 'bat', GOLEM: 'golem'}
MONSTERS = []
n = 1
for room, group, pts in _pop:
    for row, x, y in pts:
        MONSTERS.append({'id': 'monster:m%02d_%s' % (n, _names[row]), 'room': 'room:' + room, 'monster': row,
                         'at': F(x, y), 'facing': 180 if room in ('sapphire', 'throne', 'flooded') else 270,
                         'group': group})
        n += 1
assert len(MONSTERS) == 20, len(MONSTERS)
COUNTS = {r: sum(1 for m in MONSTERS if m['monster'] == r) for r in (PEDE, ROACH, BAT, GOLEM)}
assert COUNTS == {PEDE: 6, ROACH: 4, BAT: 6, GOLEM: 4}, COUNTS

# ---------------------------------------------------------------------------------------------------------------------
# Objects


def deco(i, room, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + room, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


DECORATIONS = [
    deco('adit_torch_w', 'adit', 'torch02', (-ADIT_W, 448), wall='west', notes="A miner's torch."),
    deco('upper_torch_1', 'upper', 'torch02', (-224, 1632), wall='west'),
    deco('upper_torch_2', 'upper', 'torch02', (960, 2080), wall='south'),
    deco('cut_torch', 'cut', 'torch02', (1408, 2880), wall='east'),
    deco('cut_rocks', 'cut', '6rock01', (960, 3040), notes="Spoil."),
    deco('saph_torch_1', 'sapphire', 'torch02', (1920, 2620), wall=8),
    deco('saph_torch_2', 'sapphire', 'torch02', (3840, 2240), wall=3),
    deco('saph_rocks', 'sapphire', '6rock02', (3600, 1850), notes="Spoil by the south-east wall."),
    deco('saph_crystal', 'sapphire', 'crclstr', (3376, 2896), notes="Raw crystal (moved off the vein's new crystals, A8 s28)."),
    deco('throne_crystal_n', 'throne', 'crys5', (4880, 2800)),
    deco('throne_crystal_s', 'throne', 'crys6', (4880, 2080)),
    deco('throne_torch', 'throne', 'torch02', (4480, 2944), wall=4),
    deco('ramp_skull', 'ramp', '7dec20', (800, 1200)),
    deco('flood_torch', 'flooded', 'torch02', (2944, -224), wall=0),
    deco('flood_bones', 'flooded', 'dec29', (3600, -100), notes="What the roaches left."),
    deco('god_crystal_n', 'god', 'crclstr', (4950, 634), notes="Crystal grows round the God."),
    deco('god_crystal_s', 'god', 'crclstr', (5028, 72)),
    deco('god_crystal_c', 'god', 'crys6', (4180, 820)),
]

# Light heights are over the room's floor at the light's place (LIGHTS.md), not absolute.
LIGHTS = [
    {'id': 'light:adit', 'room': 'room:adit', 'at': F(0, 448), 'height': 280, 'radius': 900,
     'color': F(255, 180, 110)},
    {'id': 'light:upper_n', 'room': 'room:upper', 'at': F(0, 1600), 'height': 340, 'radius': 1000,
     'color': F(255, 170, 100)},
    {'id': 'light:upper_e', 'room': 'room:upper', 'at': F(1024, 2304), 'height': 340, 'radius': 1000,
     'color': F(255, 170, 100)},
    {'id': 'light:cut', 'room': 'room:cut', 'at': F(1152, 2880), 'height': 280, 'radius': 700,
     'color': F(255, 170, 100)},
    {'id': 'light:saph_w', 'room': 'room:sapphire', 'at': F(2368, 2496), 'height': 420, 'radius': 1200,
     'color': F(190, 190, 255)},
    {'id': 'light:saph_e', 'room': 'room:sapphire', 'at': F(3392, 2432), 'height': 420, 'radius': 1200,
     'color': F(190, 190, 255)},
    {'id': 'light:throne', 'room': 'room:throne', 'at': F(4480, 2432), 'height': 420, 'radius': 1100,
     'color': F(200, 240, 255)},
    {'id': 'light:throne_glow', 'room': 'room:throne', 'at': F(4720, 2432), 'height': 200, 'radius': 500,
     'color': F(170, 200, 255), 'notes': "The throne's crystal glows."},
    {'id': 'light:stair', 'room': 'room:stair', 'at': F(4608, 1440), 'height': 200, 'radius': 700,
     'color': F(200, 190, 160)},
    {'id': 'light:ramp_1', 'room': 'room:ramp', 'at': F(1280, 1600), 'height': 200, 'radius': 800,
     'color': F(200, 180, 150)},
    {'id': 'light:ramp_2', 'room': 'room:ramp', 'at': F(704, 832), 'height': 200, 'radius': 800,
     'color': F(200, 180, 150)},
    {'id': 'light:ramp_3', 'room': 'room:ramp', 'at': F(1600, 384), 'height': 200, 'radius': 800,
     'color': F(200, 180, 150)},
    {'id': 'light:flooded', 'room': 'room:flooded', 'at': F(3008, 256), 'height': 320, 'radius': 1100,
     'color': F(160, 190, 220)},
    {'id': 'light:god', 'room': 'room:god', 'at': F(4352, 352), 'height': 400, 'radius': 1200,
     'color': F(255, 220, 140)},
    {'id': 'light:god_face', 'room': 'room:god', 'at': F(4800, 352), 'height': 320, 'radius': 700,
     'color': F(190, 210, 255), 'notes': "The God's crystal glows."},
]

# A glint in front of each vein (vein, outline, edge, offset as in the rooms' panels); none for the false vein (it
# glints like the others: same panel, its own light).
_veins = [('sapphire', 1, SAPH, 0, None), ('sapphire', 2, SAPH, 1, None), ('sapphire', 3, SAPH, 4, None),
          ('sapphire', 4, SAPH, 5, None), ('sapphire', 5, SAPH, 6, None)]
for gem, n, outline, edge, offset in _veins:
    LIGHTS.append(dict(vein_light(gem, n, wall_point(outline, edge, offset, out=96)), room='room:sapphire'))
LIGHTS.append(dict(vein_light('sapphire', 6, wall_point(SAPH, 7, None, out=96)), id='light:false_vein',
                   room='room:sapphire', notes="The false vein glints like the rest."))

SOUNDS = [
    {'id': 'sound:adit_wind', 'room': 'room:adit', 'at': F(0, 96), 'sound': 'whistling wind', 'radius': 1000,
     'inner_radius': 200, 'volume': 0.35, 'notes': "Air drawn in at the adit's mouth."},
    {'id': 'sound:saph_drip', 'room': 'room:sapphire', 'at': F(2560, 2880), 'sound': 'drip02', 'radius': 1200,
     'inner_radius': 300, 'volume': 0.4, 'notes': "Seepage in the hall."},
    {'id': 'sound:flood_water', 'room': 'room:flooded', 'at': F(3008, 640), 'sound': 'water lapping loop',
     'radius': 1200, 'inner_radius': 300, 'volume': 0.4, 'notes': "Water in the flooded drift."},
    {'id': 'sound:god_hum', 'room': 'room:god', 'at': F(4960, 352), 'sound': 'humming', 'radius': 1300,
     'inner_radius': 300, 'volume': 0.45, 'notes': "The God of Minerals hums in the rock."},
    # AU's mine bed (xeen_amb_mine, 62801: drips and knocks), three sources ~2,000 apart (session 7).
    {'id': 'sound:bed_upper', 'room': 'room:upper', 'at': F(512, 2304), 'sound': 'xeen_amb_mine', 'radius': 2600,
     'inner_radius': 800, 'volume': 0.4, 'pan': False, 'notes': "The mine's drips and knocks (bed, upper drift)."},
    {'id': 'sound:bed_sapphire', 'room': 'room:sapphire', 'at': F(2880, 2432), 'sound': 'xeen_amb_mine',
     'radius': 2600, 'inner_radius': 800, 'volume': 0.4, 'pan': False,
     'notes': "The mine's drips and knocks (bed, sapphire hall)."},
    {'id': 'sound:bed_flooded', 'room': 'room:flooded', 'at': F(3200, 320), 'sound': 'xeen_amb_mine', 'radius': 2600,
     'inner_radius': 800, 'volume': 0.35, 'pan': False, 'notes': "The mine's drips and knocks (bed, deep level)."},
]

DOORS = [
    door('adit', 'open:adit_upper', notes="The adit's plank door into the upper drift."),
    door('throne', 'open:sapphire_throne', notes="The plank door from the sapphire hall into the throne hall."),
    door('ramp', 'open:ramp_flooded', hinge='right', notes="The plank door at the spiral ramp's foot."),
]

CHESTS = [
    {'id': 'chest:cut', 'room': 'room:cut', 'at': F(1340, 3060), 'kind': 'gt002', 'facing': 'w',
     'treasure_level': 3, 'random_items': 2, 'gold': 450, 'notes': "The miners' chest in the side cut."},
    {'id': 'chest:flooded', 'room': 'room:flooded', 'at': F(2400, -150), 'kind': 'ch3', 'facing': 'e',
     'treasure_level': 3, 'random_items': 2, 'gold': 600, 'notes': "A chest the water has not reached (the graph's "
                                                                    "sunken chest, kept dry)."},
]

EXITS = [
    {'id': 'exit:d2', 'room': 'room:adit', 'wall': 'south', 'size': F(160, 320), 'surface': S('7solid01', 32, 64, scale=5),
     'to': 'exit:d2_adit', 'notes': "The adit's mouth, boarded with planks: out to D2 in the Gemstone foothills."},
]

OBJECTS = {
    'format': 0,
    'start': {'room': 'room:adit', 'at': F(0, 192), 'facing': 90,
              'notes': "Just inside the adit's mouth, facing in (north); D2's door into this map lands the party here."},
    'doors': DOORS,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'chests': CHESTS,
    'monsters': MONSTERS,
    'decorations': DECORATIONS,
    'exits': EXITS,
    'notes': "DD-10B's contents, written by output/studio_cal/dd10b/tools/gen.py: 3 plank doors, 2 chests, 20 placed "
             "monsters (Electrapedes, Lava Roaches, Beholder Bats, Stone Golems), no spawn points.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Wiring

VARIABLES = [vein_var('sapphire', n) for n in range(1, 6)] + ['false_vein'] + [VISIT_VAR]


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


THRONE_LINE = "The throne hums. It was not made for you."
GOD_SPEECH = ("A voice like grinding stone: \"I am the god of these mountains. If you give me 10,000 of your gold "
              "pieces, I will use them to replenish the gems inside the mountains.\"")
EVENTS = [
    arrival_event("THE GEMSTONE MINES, EAST POCKET. Timber, rails and, somewhere deep down, a hum in the rock. "
                  "Toby the sapphire smith wants five rocks; the veins give one each. They say the God of Minerals "
                  "lives at the bottom, and that he likes gold."),
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load', 'text': "Cold air, old timber, a hum in the rock.",
     'notes': "Every entry: a status line."},
    refill_event('refill_b', ['sapphire']),
    visit_end_event(),
    exit_event('exit:d2'),
    {'id': 'evt:door_adit', 'preset': 'door', 'source': 'door:adit', 'title': 'Door'},
    {'id': 'evt:door_throne', 'preset': 'door', 'source': 'door:throne', 'title': 'Door'},
    {'id': 'evt:door_ramp', 'preset': 'door', 'source': 'door:ramp', 'title': 'Door'},
    {'id': 'evt:chest_cut', 'preset': 'chest', 'source': 'chest:cut', 'title': 'Chest'},
    {'id': 'evt:chest_flooded', 'preset': 'chest', 'source': 'chest:flooded', 'title': 'Chest'},
    *vein_events('sapphire'),
    false_vein_event('sapphire', 'panel:false_vein', GEM_DAMAGE),
    text('throne', 'platform:throne', "Gem maker's throne", THRONE_LINE,
         notes="D-27: flavour. dark/aaze0039:8 the hover."),
    text('throne_back', 'platform:throne_back', "Gem maker's throne", THRONE_LINE),
    text('throne_dais', 'platform:throne_dais', "Gem maker's throne", THRONE_LINE),
    {'id': 'evt:god_face', 'preset': 'script', 'source': 'panel:god_face', 'title': 'God of Minerals',
     'effects': [{'lua': 'XeenQuests.hook("q-d7.god_of_minerals")'}],
     'notes': "D-37 (4): the God's face behind his crystal does as the crystal does (evt:god)."},
    {'id': 'evt:god', 'preset': 'script', 'source': 'platform:god', 'title': 'God of Minerals',
     'effects': [{'lua': 'XeenQuests.hook("q-d7.god_of_minerals")'}],
     'notes': "A3's q-d7.god_of_minerals (D-27): refuses while q-d7.dug (113144) is clear ('The mountains are full. "
              "Empty them first.'); without 10,000 gold says the price; else takes it, sets refill_a/b/c "
              "(113141-113143) and clears dug. Each pocket's entry then refills its veins."},
    {'id': 'evt:god_speaks', 'preset': 'script', 'trigger': 'step', 'source': 'room:god', 'once': True,
     'effects': [{'message': GOD_SPEECH}],
     'notes': "The God's own line (dark/aaze0039:16, the price rescaled to 10,000), the first time the party "
              "comes into his hall."},
    text('cart', 'platform:cart', 'Ore cart', "An ore cart heaped with spoil. Somebody meant to come back for it."),
]

WIRING = {'format': 0, 'variables': VARIABLES, 'events': EVENTS,
          'notes': "DD-10B's events (gen.py, mine.py): the five sapphire veins (q-d7.sapphire_veins: one rock each, a "
                   "map variable each) and the false vein (D-27), the refill on entry (q-d7.refill_b), the God of "
                   "Minerals (q-d7.god_of_minerals), the Gem maker's throne, the exit to D2, doors, chests."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

PROJECT = {
    'format': 0, 'id': 'xeen_dd10b', 'name': 'Gemstone Mines, east pocket', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-10B', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(11, 8), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
        'perception_difficulty': 2, 'refill_days': 672, 'music': MUSIC, 'environment': 'cave', 'lock_difficulty': 4,
        'slots': [{'monster': 'Xeen Crawler', 'tier': 5, 'per_marker': F(2, 3), 'weight': 35},
                  {'monster': 'Xeen Night Bat', 'tier': 5, 'per_marker': F(2, 3), 'weight': 35},
                  {'monster': 'Xeen Golem', 'tier': 4, 'per_marker': F(1, 2), 'weight': 30}],
    },
    'neighbours': [{
        'id': 'exit:d2_adit', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': F(*D2_ARRIVAL),
        'arrival_hint': "On D2, below the timbered adit in the Gemstone foothills (thing:dd10b_adit), at A6's return "
                        "point, facing south, away from it.",
        'direction': 270,
        'notes': "D2 installed (A6). The party lands at A6's return point for D2's event 44, (-15360, 16384, 1696) "
                 "facing 1536 (south). D2's door into this map lands at this map's start: (0, 192, 0), facing north "
                 "(90)."}],
    'qbits': QBITS,
    'items': ITEMS,
    'notes': "Xeen design brief, DD-10B Gemstone Mines, east pocket (D2; Q-D7), class S, built from the MU-6 graph "
             "(devdocs/xeen/mockups/act3_graphs/dd10b.graph.yml) with decider D-27 (mockups/act3_a8_decisions_b.md). "
             "Party 23-27, band 16-28, 20 placed monsters on A2's rows (no spawn points: the slots are the map "
             "card's only, encounter chance 0), treasure 3, music 18. Quest bits: q-d7.refill_b 113142, q-d7.dug "
             "113144 (A3; the God's hook sets refill_a/b/c and clears dug); the map's arrived_once 117200 "
             "(provisional block 117200-117239). Items: sapphire rock 12359 (the hook's map_gives, one per vein).",
}

# ---------------------------------------------------------------------------------------------------------------------
# Plan

ROCK_T = "MM7 Nighon Tunnels (7d35): cwb1 rock walls and roofs, cfb1 underfoot"
TIMBER_T = ROCK_T + "; trim9_32 timber sets and trim9_32a lagging overhead"
SPACES = [
    sp('adit', 'East adit', 'corridor', 'S', (384, 896), 0, 352,
       "The timbered adit in the Gemstone foothills: the arrival and the exit to D2.", TIMBER_T, empty=True,
       safe=True),
    sp('upper', 'Upper drift', 'corridor', 'M', (2240, 1728), 0, DRIFT_CEIL, "A long drift with side cuts.",
       TIMBER_T, [placed('Electrapede (11361)', 3, 20), placed('Beholder Bat (11312)', 3, 20)]),
    sp('cut', 'Side cut', 'room', 'S', (512, 480), 0, 352, "Where the miners stopped: a cart of spoil, their chest.",
       TIMBER_T, treasure=[{'kind': 'chest', 'count': 1, 'tier': 3, 'items': F(2, 2),
                            'notes': "The miners' chest."}], empty=True),
    sp('sapphire', 'Sapphire hall', 'room', 'L', (1920, 1664), 0, F(576, 832),
       "Five sapphire veins (q-d7.sapphire_veins), one rock each; one false vein ('A gem exploded!').",
       ROCK_T + "; A6's sapphire vein xdvsaph",
       [placed('Electrapede (11361)', 3, 20), placed('Stone Golem (11581)', 2, 26)]),
    sp('throne', "Gem maker's throne", 'room', 'M', (1024, 1024), 0, F(512, 704),
       "A throne of dressed stone with a great crystal in its back ('Gem maker's throne'); a stair down behind it.",
       ROCK_T + "; 7d35's dressed stone cwb and MM8 d37's crystal gcrysc3 for the throne",
       [placed('Lava Roach (11362)', 2, 26), placed('Stone Golem (11581)', 2, 26)]),
    sp('stair', 'Throne stair', 'corridor', 'S', (384, 704), F(0, DEEP), 384,
       "Twelve steps down from the throne to the God of Minerals.", ROCK_T, empty=True),
    sp('ramp', 'Spiral ramp', 'corridor', 'M', (1856, 1888), F(0, DEEP), 320,
       "A ramp round the rock core, down to the deep level.", ROCK_T, [placed('Beholder Bat (11312)', 3, 20)]),
    sp('flooded', 'Flooded drift', 'room', 'M', (1408, 1152), DEEP, F(448, 576), "Knee-deep water; a chest.",
       ROCK_T + "; 7wtrtyl water", [placed('Lava Roach (11362)', 2, 26)],
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 3, 'items': F(2, 2), 'notes': "The flooded drift's chest."}]),
    sp('god', 'The God of Minerals', 'room', 'M', (1280, 1216), DEEP, F(576, 768),
       "At the pocket's bottom: the God of Minerals, a face in the rock ('I am the god of these mountains.'): pay to "
       "refill the veins (q-d7.god_of_minerals).", "7d35's gold-veined cwb1gold; the God of crystal gcrysc3",
       empty=True),
]

LINKS = [
    link('b1', 'adit', 'upper', 'door', motion='swing'),
    link('b2', 'upper', 'sapphire', 'open'),
    link('b3', 'sapphire', 'throne', 'door', motion='swing'),
    link('b4', 'upper', 'ramp', 'open'),
    link('b5', 'ramp', 'flooded', 'door', motion='swing'),
    link('b6', 'flooded', 'god', 'open'),
    link('b7', 'throne', 'stair', 'open'),
    link('b8', 'upper', 'cut', 'open'),
    link('b9', 'stair', 'god', 'open'),
]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "The east pocket of the Gemstone Mines, in the Gemstone foothills of Sprite Forest: a timbered adit "
                 "and a long drift, a high sapphire hall round a rock pillar, the Gem maker's crystal throne, and at "
                 "the bottom, down a spiral ramp or the stair behind the throne, the God of Minerals, who refills "
                 "every pocket's veins for gold once something has been dug.",
        'purpose': "Q-D7 The Gemsmiths (repeatable): sapphire rocks for Toby on D1; the God of Minerals' refill for "
                   "all three pockets. Party 23-27; band 16-28; 20 monsters; treasure 3. About 10 minutes.",
        'mood': "A worked mine going deeper: dark rock, old timber and torchlight above; crystal and gold below.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'loops': [{'id': 'loop:b', 'spaces': ['room:upper', 'room:sapphire', 'room:throne', 'room:stair', 'room:god',
                                              'room:flooded', 'room:ramp'],
                   'notes': "East: down by the ramp, up by the throne's stair."}],
        'entrances': [{'id': 'entrance:adit', 'space': 'room:adit', 'kind': 'both', 'neighbour': 'exit:d2_adit',
                       'facing': 'n', 'how': "Just inside the adit's mouth, facing in."}],
        'critical_path': ['room:adit', 'room:upper', 'room:sapphire', 'room:throne', 'room:stair', 'room:god'],
        'return_path': ['room:god', 'room:flooded', 'room:ramp', 'room:upper', 'room:adit'],
        'goals': [
            {'id': 'goal:sapphire', 'space': 'room:sapphire', 'kind': 'take',
             'what': "Five sapphire rocks from the five sapphire veins (q-d7.sapphire_veins).", 'handed_in_at': 'D1'},
            {'id': 'goal:god', 'space': 'room:god', 'kind': 'use',
             'what': "Pay the God of Minerals 10,000 gold to refill the veins (q-d7.god_of_minerals)."}],
        'atmosphere': "Torchlit timber in the adit and drift (ambient about 15-18), the caves darker (12-16), blue "
                      "glints in the sapphire hall, a cold crystal glow at the throne and the God. Music 18. Sounds: "
                      "air at the adit's mouth, seepage in the hall, water in the flooded drift, the God's hum.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': 2, 'doors': 3, 'fixed_actors': 20, 'loops': 1, 'monsters_about': 20, 'rooms': 9,
                   'sectors': 9, 'spawn_points': 0, 'floor_area_millions': 11},
        'notes': "Class S (MAPS, Dungeons): at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 "
                 "doors. D-27: five veins, one rock each, a map variable each; refill_b on entry; one false vein; "
                 "Stone Golem 26 for the graph's Sand Golem; the God refuses while nothing is dug; 7d35 with A6's "
                 "sapphire vein.",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    elif level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return d


DIAGRAM = """                    [Side cut $, cart]
                           |
   [Upper drift: pedes, bats]--------(open)--------[SAPPHIRE HALL: 5 veins + 1 false]--=door=--[GEM MAKER'S THRONE]
          |         \\                                                                                 |
        =door=     (open) spiral ramp down (bats)                                                 stair down
          |            \\                                                                              |
   [East adit]          `---=door=---[Flooded drift $, water, roaches]---(open)---[THE GOD OF MINERALS]
   D2: the adit in the Gemstone foothills

 $ chest   = = plank door   Upper level at 0, deep level at -480. Veins: one rock each until the God is paid.
"""

# D-89 identity (lane A8 s28): crystals frame every vein (mine.py), the rails run on along the timbered drift to its
# bend, the sapphire hall's and the flooded drift's floors slope.
vein_crystals(ROOMS)
_RB = {r['id'].split(':')[1]: r for r in ROOMS}
_RB['upper']['platforms'] += rails(0, 1040, 0, 2242)
_RB['upper']['notes'] += " The rails run on from the adit to the drift's bend."
_RB['sapphire']['floor_points'] = [F(2432, 2432, 40), F(3264, 2816, 24), F(3392, 2176, 48)]
_RB['cut']['rough'] = {'step': 160, 'depth': 32}
_FPOOL = [(2560, 512), (3392, 480), (3584, 608), (3456, 768), (2560, 704)]
_RB['flooded']['floor_points'] = [F(2816, 64, DEEP + 40), F(3328, 0, DEEP + 24)] + [F(x, y, DEEP) for x, y in _FPOOL]
_RB['flooded']['floor_lines'] = [[F(x, y) for x, y in _FPOOL + _FPOOL[:1]]]
IDENTITY = {'shape': 'mine', 'family': '7d35',
            'seen': ["a timbered adit and drift: timber sets, lagging, rails running in to the drift's bend, a cart of "
                     "spoil in the side cut",
                     "the sapphire hall round its rock pillar, every vein framed by blue crystal growing out of the rock",
                     "the deep level: the flooded drift and the God of Minerals' face of crystal in the gold-veined rock"]}

ROOMS_DOC = {'format': 0, 'themes': THEMES_B, 'defaults': {'theme': 'theme:rock', 'ambient': 15}, 'rooms': ROOMS,
             'openings': OPENINGS,
             'notes': "DD-10B at L3/L4: nine rooms in the plan's frame (x east, y north, the adit's mouth at y 0). "
                      "Written by output/studio_cal/dd10b/tools/gen.py with output/studio_cal/dd10a/tools/mine.py."}

if __name__ == '__main__':
    write_levels(OUT, sys.argv[1:] or ['L1', 'L2', 'L3', 'L4'], PROJECT, plan, DIAGRAM, ROOMS_DOC, OBJECTS, WIRING, IDENTITY)
