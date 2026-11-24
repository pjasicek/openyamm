"""DD-10A Gemstone Mines, west pocket: writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd10a/L*).

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd10a), phase 3, decider D-27.
Shared with DD-10B and DD-10C: tools/mine.py (themes, timber, carts, veins, refill, false vein, exit).
Plan frame: x east, y north, the adit's mouth at y 0 (the party comes in from D1 going north); every floor at 0 (the
sump's pool sunk 32). Graph rows: the gallery, ruby stope and cobweb drift to the north, the bone pocket, emerald
gallery and sump to the south; the loop gallery - ruby - cobweb - sump - emerald - bones - gallery.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd10a')
from mine import *  # noqa: E402,F401,F403

OUT = R + '/devdocs/xeen/briefs/dd10a'
KEY = 'dd10a'
MAP_ID = 9159

# Map qbits: provisional block 117160-117199 (A8's brief); quest bits are A3's q-d7.
QBITS = {'arrived_once': 117160, 'refill_a': QD7['refill_a'], 'dug': QD7['dug']}
ITEMS = {'ruby_rock': ROCKS['ruby'], 'emerald_rock': ROCKS['emerald']}

# D1's adit (thing:dd10a_adit, D1 event 187 on the installed xeen_d1.odm): its face at (-9728, 21470, 1600-1920), used
# from (-9728, 21214, 1600) facing north into the hill. A6's return point for event 187: (-9728, 20480, 1600) facing
# 1536 (south, studio direction 270), away from the adit.
D1_ARRIVAL = [-9728, 20480, 1600]

BONE_DAMAGE = 16    # fire, every member: about a tenth to a fifth of a level-25 member's hit points (D-27)

# ---------------------------------------------------------------------------------------------------------------------
# Rooms

ADIT_W = 192          # half width
GAL_W = 512
GAL_CEIL = 416

_adit_plats, _adit_beams = [], []
for yy in (288, 608):
    p, b = timber_set('y', yy, -ADIT_W, ADIT_W, 352)
    _adit_plats += p
    _adit_beams += b
_adit_plats += rails(0, 48, 0, 840)

_gal_plats, _gal_beams = [], []
for yy in (1280, 1664, 2048):
    p, b = timber_set('y', yy, -GAL_W // 2, GAL_W // 2, GAL_CEIL)
    _gal_plats += p
    _gal_beams += b
for xx in (448, 1344):
    p, b = timber_set('x', xx, 2432 - GAL_W // 2, 2432 + GAL_W // 2, GAL_CEIL)
    _gal_plats += p
    _gal_beams += b
_gal_plats += cart(800, 2600, 0, "An old ore cart pushed off the rails against the gallery's wall.",
                   pid='platform:cart')

# The ruby stope: the gallery's end to the west (edge 9), the cobweb drift to the east (edge 4); veins on edges 1, 2,
# 6, 7 and 8 (0-based edges from point i to i+1).
RUBY = [F(1664, 2112), F(2048, 1856), F(2816, 1792), F(3328, 2048), F(3456, 2304), F(3456, 2816), F(3328, 3072),
        F(2816, 3328), F(2176, 3328), F(1664, 2944)]
COBWEB = [F(3584, 2176), F(3968, 2048), F(4608, 2048), F(4864, 2304), F(4992, 2816), F(4736, 3200), F(4096, 3264),
          F(3584, 2944)]
SUMP = [F(3840, 1024), F(4608, 960), F(4864, 1344), F(4736, 1920), F(3840, 1920), F(3712, 1792), F(3712, 1152)]
EMERALD = [F(2048, 640), F(3072, 576), F(3584, 960), F(3584, 1600), F(2560, 1536), F(2048, 1280)]
BONES = [F(768, 1024), F(1408, 768), F(1920, 768), F(1920, 1408), F(1408, 1664), F(1280, 2080), F(768, 2080),
         F(640, 1536)]

ROOMS = [
    {'id': 'room:adit', 'name': 'West adit', 'outline': rect(-ADIT_W, 0, ADIT_W, 896), 'floor': 0, 'ceiling': 352,
     'theme': 'theme:timbered', 'ambient': 18, 'platforms': _adit_plats, 'beams': _adit_beams,
     'notes': "The timbered adit under the hill above the gemsmiths' row: the arrival. Two timber sets, the cart "
              "rails running in from the mouth (the exit, south) to the plank door into the gallery (north)."},
    {'id': 'room:gallery', 'name': 'Timbered gallery', 'path': [F(0, 1024), F(0, 2432), F(1536, 2432)],
     'width': GAL_W, 'floor': 0, 'ceiling': GAL_CEIL, 'theme': 'theme:timbered', 'ambient': 15,
     'platforms': _gal_plats, 'beams': _gal_beams,
     'notes': "A timbered gallery north from the adit's door, then east to the ruby stope: props and lagging, the rails "
              "stop at the adit door, an old cart against the north wall; the bone pocket opens off its south side."},
    {'id': 'room:ruby', 'name': 'Ruby stope', 'outline': RUBY, 'floor': 0, 'rough': {'step': 192, 'depth': 32},
     'ceiling': 576, 'ceiling_points': [F(2560, 2560, 832), F(2304, 2944, 704), F(3072, 2304, 704)],
     'theme': 'theme:rock', 'ambient': 16,
     'pillars': [{'outline': [F(2560, 2432), F(2720, 2400), F(2784, 2560), F(2688, 2688), F(2560, 2624)],
                  'surface': ROCK, 'notes': "A rock pillar the miners left to hold the stope's roof."}],
     'stalactites': [{'at': F(2240, 2240), 'radius': 64, 'length': 192}, {'at': F(3104, 2880), 'radius': 72,
                                                                          'length': 224}],
     'walls': [
         {'wall': 1, 'panels': [vein_panel('ruby', 1)]},
         {'wall': 2, 'panels': [vein_panel('ruby', 2)]},
         {'wall': 6, 'panels': [vein_panel('ruby', 3)]},
         {'wall': 7, 'panels': [vein_panel('ruby', 4)]},
         {'wall': 8, 'panels': [vein_panel('ruby', 5)]},
     ],
     'notes': "A worked-out stope about 1,800 by 1,500 round a rock pillar, its roof high in the middle: five ruby "
              "veins in its walls (q-d7.ruby_veins), one rock each."},
    {'id': 'room:cobweb', 'name': 'Cobweb drift', 'outline': COBWEB, 'floor': 0, 'rough': {'step': 192, 'depth': 32},
     'ceiling': 448, 'ceiling_points': [F(4288, 2688, 576), F(4608, 2880, 544)], 'theme': 'theme:rock',
     'ambient': 12,
     'ceiling_surfaces': [{'steeper_than': 0.25, 'surface': WEB}],
     'platforms': [
         {'id': 'platform:cocoon', 'rise': 0, 'surface': WEB, 'top_surface': WEB,
          'outline': [F(4704, 2624), F(4784, 2600), F(4856, 2656), F(4840, 2744), F(4760, 2768), F(4696, 2712)],
          'top_heights': [24, 40, 48, 44, 32, 20], 'notes': "A miner cocooned in old web by the drift's east wall."},
         {'id': 'platform:cocoon_2', 'rise': 0, 'surface': WEB, 'top_surface': WEB,
          'outline': [F(4160, 3120), F(4256, 3104), F(4320, 3152), F(4296, 3200), F(4192, 3208), F(4144, 3168)],
          'top_heights': [20, 36, 44, 40, 28, 18], 'notes': "A second web-wrapped bundle by the north wall."},
     ],
     'notes': "The queens' den: a drift choked with old web, the sump's plank door in its south wall."},
    {'id': 'room:sump', 'name': 'Sump', 'outline': SUMP, 'floor': 0, 'rough': {'step': 192, 'depth': 24},
     'ceiling': 384, 'ceiling_points': [F(4352, 1472, 448)], 'theme': 'theme:rock', 'ambient': 13,
     'levels': [{'id': 'level:sump_pool', 'outline': [F(4224, 1216), F(4608, 1152), F(4704, 1408), F(4608, 1664),
                                                       F(4288, 1664), F(4192, 1408)],
                 'floor': -32, 'edge': ROCK, 'surface': WATER, 'notes': "Standing water where the mine drains."}],
     'notes': "Where the west pocket drains: a pool of standing water and the miners' strongbox; plank doors north (the "
              "cobweb drift) and west (the emerald gallery)."},
    {'id': 'room:emerald', 'name': 'Emerald gallery', 'outline': EMERALD, 'floor': 0,
     'rough': {'step': 192, 'depth': 32}, 'ceiling': 512,
     'ceiling_points': [F(2816, 1088, 640), F(2368, 960, 576)], 'theme': 'theme:rock', 'ambient': 15,
     'stalactites': [{'at': F(3200, 1280), 'radius': 56, 'length': 176}],
     'walls': [
         {'wall': 0, 'panels': [vein_panel('emerald', 1, offset=160), vein_panel('emerald', 2, offset=640)]},
         {'wall': 1, 'panels': [vein_panel('emerald', 3)]},
         {'wall': 3, 'panels': [vein_panel('emerald', 4, offset=320)]},
         {'wall': 4, 'panels': [vein_panel('emerald', 5)]},
     ],
     'notes': "A low winding gallery with five emerald veins (q-d7.emerald_veins); the sump's door east, the bone "
              "pocket open to the west."},
    {'id': 'room:bones', 'name': 'Bone pocket', 'outline': BONES, 'floor': 0, 'rough': {'step': 192, 'depth': 32},
     'ceiling': 384, 'ceiling_points': [F(1280, 1280, 448)], 'theme': 'theme:rock', 'ambient': 13,
     'notes': "A dead end where miners died: heaps of bones (one of them explodes) and their chest; open to the "
              "gallery north and the emerald gallery east."},
]

OPENINGS = [
    {'id': 'open:adit_gallery', 'from': 'room:adit', 'to': 'room:gallery', 'link': 'link:a1', 'width': 224,
     'height': 320, 'notes': "The adit's plank door."},
    {'id': 'open:gallery_ruby', 'from': 'room:gallery', 'to': 'room:ruby', 'link': 'link:a2', 'width': 384,
     'height': 352},
    {'id': 'open:ruby_cobweb', 'from': 'room:ruby', 'to': 'room:cobweb', 'link': 'link:a3', 'from_wall': 4,
     'width': 384, 'height': 352},
    {'id': 'open:cobweb_sump', 'from': 'room:cobweb', 'to': 'room:sump', 'link': 'link:a4', 'from_wall': 1,
     'to_wall': 3, 'width': 224, 'height': 320, 'notes': "The sump's plank door."},
    {'id': 'open:sump_emerald', 'from': 'room:sump', 'to': 'room:emerald', 'link': 'link:a5', 'from_wall': 5,
     'to_wall': 2, 'width': 224, 'height': 320, 'notes': "The emerald gallery's plank door."},
    {'id': 'open:emerald_bones', 'from': 'room:emerald', 'to': 'room:bones', 'link': 'link:a6', 'from_wall': 5,
     'to_wall': 2, 'width': 384, 'height': 352},
    {'id': 'open:bones_gallery', 'from': 'room:bones', 'to': 'room:gallery', 'link': 'link:a7', 'from_wall': 5,
     'width': 384, 'height': 320},
]

# ---------------------------------------------------------------------------------------------------------------------
# Monsters (A2's rows; D-27): Arachnoid Hunter 18 (11331) x6, Arachnoid Queen 24 (11332) x4, Beholder Bat 20 (11312) x6,
# Electrapede 20 (11361) x4: 20, all placed, hostile by their rows.

HUNTER, QUEEN, BAT, PEDE = 11331, 11332, 11312, 11361
_pop = [
    ('gallery', 1, [(BAT, -160, 1500), (BAT, 160, 2240), (BAT, 960, 2380)]),
    ('ruby', 2, [(HUNTER, 2200, 2300), (HUNTER, 3000, 2800), (HUNTER, 2400, 3050), (PEDE, 3150, 2300),
                 (PEDE, 2150, 2750)]),
    ('cobweb', 3, [(QUEEN, 4500, 2700), (QUEEN, 4600, 2400), (QUEEN, 4300, 3000), (QUEEN, 4650, 2950),
                   (HUNTER, 3900, 2550), (HUNTER, 4150, 2350), (HUNTER, 4250, 2700)]),
    ('emerald', 4, [(BAT, 2560, 1060), (BAT, 3000, 1150), (BAT, 2750, 1350), (PEDE, 3300, 1250),
                    (PEDE, 2380, 860)]),
]
_names = {HUNTER: 'hunter', QUEEN: 'queen', BAT: 'bat', PEDE: 'pede'}
MONSTERS = []
n = 1
for room, group, pts in _pop:
    for row, x, y in pts:
        MONSTERS.append({'id': 'monster:m%02d_%s' % (n, _names[row]), 'room': 'room:' + room, 'monster': row,
                         'at': F(x, y), 'facing': 270 if room in ('cobweb', 'ruby') else 180, 'group': group})
        n += 1
assert len(MONSTERS) == 20, len(MONSTERS)
COUNTS = {r: sum(1 for m in MONSTERS if m['monster'] == r) for r in (HUNTER, QUEEN, BAT, PEDE)}
assert COUNTS == {HUNTER: 6, QUEEN: 4, BAT: 6, PEDE: 4}, COUNTS

# ---------------------------------------------------------------------------------------------------------------------
# Objects


def deco(i, room, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + room, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


DECORATIONS = [
    deco('adit_torch_w', 'adit', 'torch02', (-ADIT_W, 448), wall='west', notes="A miner's torch."),
    deco('gal_torch_1', 'gallery', 'torch02', (256, 1472), wall='east'),
    deco('gal_torch_2', 'gallery', 'torch02', (768, 2176), wall='south'),
    deco('ruby_torch_1', 'ruby', 'torch02', (1664, 2820), wall=9),
    deco('ruby_torch_2', 'ruby', 'torch02', (3392, 2944), wall=5),
    deco('ruby_rocks', 'ruby', '6rock01', (2240, 3240), notes="Spoil by the north wall."),
    deco('ruby_rocks_2', 'ruby', '6rock02', (3330, 2700)),
    deco('cobweb_bones', 'cobweb', 'dec29', (4480, 3160), notes="What the queens left."),
    deco('cobweb_skull', 'cobweb', '7dec20', (4834, 2400)),
    deco('sump_torch', 'sump', 'torch02', (4600, 1920), wall=3),
    deco('emerald_torch', 'emerald', 'torch02', (2304, 1408), wall=4),
    deco('emerald_rocks', 'emerald', '6rock01', (3360, 1040)),
    deco('bones_heap_a', 'bones', '7dec18', (760, 1340), notes="A heap of bones: they crumble."),
    deco('bones_heap_b', 'bones', 'dec19', (1060, 980), notes="A heap of bones: they crumble."),
    deco('bones_heap_c', 'bones', '7dec18', (880, 1120), notes="The heap that explodes (once)."),
    deco('bones_skeleton', 'bones', 'dec05', (791, 1686), notes="A miner who did not get out."),
    deco('bones_skull', 'bones', '7dec20', (1600, 900)),
]

LIGHTS = [
    {'id': 'light:adit', 'room': 'room:adit', 'at': F(0, 448), 'height': 280, 'radius': 900,
     'color': F(255, 180, 110)},
    {'id': 'light:gallery_n', 'room': 'room:gallery', 'at': F(0, 1600), 'height': 340, 'radius': 1000,
     'color': F(255, 170, 100)},
    {'id': 'light:gallery_e', 'room': 'room:gallery', 'at': F(768, 2432), 'height': 340, 'radius': 1000,
     'color': F(255, 170, 100)},
    {'id': 'light:ruby_w', 'room': 'room:ruby', 'at': F(2112, 2560), 'height': 420, 'radius': 1200,
     'color': F(255, 150, 120)},
    {'id': 'light:ruby_e', 'room': 'room:ruby', 'at': F(3072, 2560), 'height': 420, 'radius': 1200,
     'color': F(255, 150, 120)},
    {'id': 'light:cobweb', 'room': 'room:cobweb', 'at': F(4288, 2624), 'height': 320, 'radius': 1100,
     'color': F(190, 190, 210)},
    {'id': 'light:sump', 'room': 'room:sump', 'at': F(4288, 1472), 'height': 280, 'radius': 1000,
     'color': F(160, 190, 220)},
    {'id': 'light:emerald', 'room': 'room:emerald', 'at': F(2816, 1088), 'height': 380, 'radius': 1200,
     'color': F(170, 230, 170)},
    {'id': 'light:bones', 'room': 'room:bones', 'at': F(1216, 1344), 'height': 300, 'radius': 1000,
     'color': F(255, 170, 110)},
]

# A glint in front of each vein (vein, outline, edge, offset as in the rooms' panels).
_veins = [('ruby', 1, RUBY, 1, None), ('ruby', 2, RUBY, 2, None), ('ruby', 3, RUBY, 6, None),
          ('ruby', 4, RUBY, 7, None), ('ruby', 5, RUBY, 8, None),
          ('emerald', 1, EMERALD, 0, 160), ('emerald', 2, EMERALD, 0, 640), ('emerald', 3, EMERALD, 1, None),
          ('emerald', 4, EMERALD, 3, 320), ('emerald', 5, EMERALD, 4, None)]
for gem, n, outline, edge, offset in _veins:
    LIGHTS.append(dict(vein_light(gem, n, wall_point(outline, edge, offset, out=96)), room='room:' + gem))

SOUNDS = [
    {'id': 'sound:sump_drip', 'room': 'room:sump', 'at': F(4416, 1408), 'sound': 'drip01', 'radius': 1400,
     'inner_radius': 300, 'volume': 0.55, 'notes': "Water dripping into the sump."},
    {'id': 'sound:ruby_drip', 'room': 'room:ruby', 'at': F(2304, 2944), 'sound': 'drip02', 'radius': 1200,
     'inner_radius': 300, 'volume': 0.4, 'notes': "Seepage in the stope."},
    {'id': 'sound:adit_wind', 'room': 'room:adit', 'at': F(0, 96), 'sound': 'whistling wind', 'radius': 1000,
     'inner_radius': 200, 'volume': 0.35, 'notes': "Air drawn in at the adit's mouth."},
    # AU's mine bed (xeen_amb_mine, 62801: drips and knocks), two sources ~2,700 apart (session 7).
    {'id': 'sound:bed_gallery', 'room': 'room:gallery', 'at': F(512, 2432), 'sound': 'xeen_amb_mine', 'radius': 2800,
     'inner_radius': 800, 'volume': 0.4, 'pan': False, 'notes': "The mine's drips and knocks (bed, west)."},
    {'id': 'sound:bed_ruby', 'room': 'room:ruby', 'at': F(3200, 2304), 'sound': 'xeen_amb_mine', 'radius': 2800,
     'inner_radius': 800, 'volume': 0.4, 'pan': False, 'notes': "The mine's drips and knocks (bed, east)."},
]

DOORS = [
    door('adit', 'open:adit_gallery', notes="The adit's plank door into the gallery."),
    door('sump', 'open:cobweb_sump', hinge='right', notes="The sump's plank door, in the cobweb drift's south wall."),
    door('emerald', 'open:sump_emerald', notes="The plank door between the sump and the emerald gallery."),
]

CHESTS = [
    {'id': 'chest:bones', 'room': 'room:bones', 'at': F(1320, 880), 'kind': 'gt002', 'treasure_level': 3, 'random_items': 2, 'gold': 450, 'notes': "The dead miners' chest."},
    {'id': 'chest:sump', 'room': 'room:sump', 'at': F(4096, 1096), 'kind': 'ch3', 'treasure_level': 3, 'random_items': 2, 'gold': 600, 'notes': "The miners' strongbox by the sump."},
]

EXITS = [
    {'id': 'exit:d1', 'room': 'room:adit', 'wall': 'south', 'size': F(160, 320), 'surface': S('7solid01', 32, 64, scale=5),
     'to': 'exit:d1_adit', 'notes': "The adit's mouth, boarded with planks: out to D1 above the gemsmiths' row."},
]

OBJECTS = {
    'format': 0,
    'start': {'room': 'room:adit', 'at': F(0, 192), 'facing': 90,
              'notes': "Just inside the adit's mouth, facing in (north); D1's door into this map lands the party here."},
    'doors': DOORS,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'chests': CHESTS,
    'monsters': MONSTERS,
    'decorations': DECORATIONS,
    'exits': EXITS,
    'notes': "DD-10A's contents, written by output/studio_cal/dd10a/tools/gen.py: 3 plank doors, 2 chests, 20 placed "
             "monsters (Arachnoid Hunters, Queens, Beholder Bats, Electrapedes), no spawn points.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Wiring

VARIABLES = [vein_var(g, n) for g in ('ruby', 'emerald') for n in range(1, 6)] + ['bones_blown'] + [VISIT_VAR]


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


CRUMBLE = "The bones crumble to dust in your hands."   # dark/aaze0039:14
EVENTS = [
    arrival_event("THE GEMSTONE MINES. Old timber, cart rails and the smell of wet stone. The gemsmiths in the vale "
                  "make gear from five rocks of a kind, and the west pocket's veins still show red and green: one "
                  "rock to a vein. Mind the far drift. Something has been spinning there."),
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load', 'text': "Cold air, wet rock, old timber.",
     'notes': "Every entry: a status line."},
    refill_event('refill_a', ['ruby', 'emerald']),
    visit_end_event(),
    exit_event('exit:d1'),
    {'id': 'evt:door_adit', 'preset': 'door', 'source': 'door:adit', 'title': 'Door'},
    {'id': 'evt:door_sump', 'preset': 'door', 'source': 'door:sump', 'title': 'Door'},
    {'id': 'evt:door_emerald', 'preset': 'door', 'source': 'door:emerald', 'title': 'Door'},
    {'id': 'evt:chest_bones', 'preset': 'chest', 'source': 'chest:bones', 'title': 'Chest'},
    {'id': 'evt:chest_sump', 'preset': 'chest', 'source': 'chest:sump', 'title': 'Chest'},
    *vein_events('ruby'),
    *vein_events('emerald'),
    text('bones_a', 'deco:bones_heap_a', 'Bones', CRUMBLE, notes="dark/aaze0039:14."),
    text('bones_b', 'deco:bones_heap_b', 'Bones', CRUMBLE),
    {'id': 'evt:bones_c', 'preset': 'script', 'source': 'deco:bones_heap_c', 'title': 'Bones',
     'condition': {'not': {'map_var': 'bones_blown'}},
     'effects': [{'set': {'var': {'map_var': 'bones_blown'}, 'value': 1}},
                 {'damage': {'amount': BONE_DAMAGE, 'kind': 'fire'}},
                 {'message': 'The bones explode!'}],
     'else_effects': [{'text': CRUMBLE}],
     'notes': "D-27's trap (dark/aaze0039:13): the one heap that explodes, once: %d fire to every member (about a "
              "tenth to a fifth of a level-25 member's hit points); then it crumbles like the rest." % BONE_DAMAGE},
    text('skeleton', 'deco:bones_skeleton', 'Bones', "A miner, still holding the handle of a broken pick. Nothing "
         "else on him.", seconds=5),
    text('cobwebs', 'platform:cocoon_2', 'Cobwebs', "Cobwebs, thick as sailcloth. Something big spun them.",
         notes="The graph's 'Cobwebs' (dark/aaze0039)."),
    text('cocoon', 'platform:cocoon', 'Cobwebs', "A miner wrapped in old web. Whatever he carried, the spiders kept.",
         seconds=5),
    text('cart', 'platform:cart', 'Ore cart', "An ore cart, empty but for grit and one bent spike."),
]

WIRING = {'format': 0, 'variables': VARIABLES, 'events': EVENTS,
          'notes': "DD-10A's events (gen.py, mine.py): the ten veins (q-d7.ruby_veins, emerald_veins: one rock each, "
                   "a map variable each), the refill on entry (q-d7.refill_a), the exploding bone heap (D-27), the "
                   "exit to D1, doors, chests, flavour."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

PROJECT = {
    'format': 0, 'id': 'xeen_dd10a', 'name': 'Gemstone Mines, west pocket', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-10A', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(11, 8), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
        'perception_difficulty': 2, 'refill_days': 672, 'music': MUSIC, 'environment': 'cave', 'lock_difficulty': 4,
        'slots': [{'monster': 'Xeen Arachnoid', 'tier': 5, 'per_marker': F(2, 3), 'weight': 40},
                  {'monster': 'Xeen Night Bat', 'tier': 5, 'per_marker': F(2, 3), 'weight': 35},
                  {'monster': 'Xeen Crawler', 'tier': 4, 'per_marker': F(1, 2), 'weight': 25}],
    },
    'neighbours': [{
        'id': 'exit:d1_adit', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': F(*D1_ARRIVAL),
        'arrival_hint': "On D1, below the timbered adit above the gemsmiths' row (thing:dd10a_adit), at A6's return "
                        "point, facing south, away from it.",
        'direction': 270,
        'notes': "D1 installed (A6). The adit's face stands at (-9728, 21470); the party lands at A6's return point for "
                 "D1's event 187, (-9728, 20480, 1600) facing 1536 (south). D1's door into this map lands at this "
                 "map's start: (0, 192, 0), facing north (90)."}],
    'qbits': QBITS,
    'items': ITEMS,
    'notes': "Xeen design brief, DD-10A Gemstone Mines, west pocket (D1; Q-D7), class S, built from the MU-6 graph "
             "(devdocs/xeen/mockups/act3_graphs/dd10a.graph.yml) with decider D-27 (mockups/act3_a8_decisions_b.md). "
             "Party 23-27, band 16-28, 20 placed monsters on A2's rows (no spawn points: the slots are the map "
             "card's only, encounter chance 0), treasure 3, music 18. Quest bits: q-d7.refill_a 113141, q-d7.dug "
             "113144 (A3); the map's arrived_once 117160 (provisional block 117160-117199). Items: ruby rock 12357, "
             "emerald rock 12358 (the hooks' map_gives, one per vein).",
}

# ---------------------------------------------------------------------------------------------------------------------
# Plan

ROCK_T = "MM7 Nighon Tunnels (7d35): cwb1 rock walls and roofs, cfb1 underfoot"
TIMBER_T = ROCK_T + "; trim9_32 timber sets and trim9_32a lagging overhead"
SPACES = [
    sp('adit', 'West adit', 'corridor', 'S', (384, 896), 0, 352,
       "The timbered adit above the gemsmiths' row: the arrival and the exit to D1.", TIMBER_T, empty=True, safe=True),
    sp('gallery', 'Timbered gallery', 'corridor', 'M', (1792, 1920), 0, GAL_CEIL,
       "Props and lagging; cart rails; an old cart.", TIMBER_T, [placed('Beholder Bat (11312)', 3, 20)]),
    sp('ruby', 'Ruby stope', 'room', 'L', (1792, 1536), 0, F(576, 832),
       "Five ruby veins (q-d7.ruby_veins), one rock each; 'You've got all this vein has to offer.' once picked.",
       ROCK_T + "; A6's ruby vein xdvruby",
       [placed('Arachnoid Hunter (11331)', 3, 18), placed('Electrapede (11361)', 2, 20)]),
    sp('cobweb', 'Cobweb drift', 'room', 'M', (1408, 1216), 0, F(448, 576),
       "'Cobwebs' across the drift; the queens' den.", ROCK_T + "; the world's web xnweb",
       [placed('Arachnoid Queen (11332)', 4, 24), placed('Arachnoid Hunter (11331)', 3, 18)]),
    sp('sump', 'Sump', 'room', 'S', (1152, 960), 0, F(384, 448), "Standing water and a strongbox.",
       ROCK_T + "; 7wtrtyl water", treasure=[{'kind': 'chest', 'count': 1, 'tier': 3, 'items': F(2, 2),
                                              'notes': "The miners' strongbox."}], empty=True),
    sp('emerald', 'Emerald gallery', 'room', 'M', (1536, 1024), 0, F(512, 640),
       "Five emerald veins (q-d7.emerald_veins), one rock each.", ROCK_T + "; A6's emerald vein xdvemrld",
       [placed('Beholder Bat (11312)', 3, 20), placed('Electrapede (11361)', 2, 20)]),
    sp('bones', 'Bone pocket', 'room', 'S', (1280, 1312), 0, F(384, 448),
       "Miners' bones: 'The bones crumble to dust in your hands', one heap 'The bones explode!'; their chest.",
       ROCK_T, treasure=[{'kind': 'chest', 'count': 1, 'tier': 3, 'items': F(2, 2),
                          'notes': "The dead miners' chest."}], empty=True),
]

LINKS = [
    link('a1', 'adit', 'gallery', 'door', motion='swing'),
    link('a2', 'gallery', 'ruby', 'open'),
    link('a3', 'ruby', 'cobweb', 'open'),
    link('a4', 'cobweb', 'sump', 'door', motion='swing'),
    link('a5', 'sump', 'emerald', 'door', motion='swing'),
    link('a6', 'emerald', 'bones', 'open'),
    link('a7', 'bones', 'gallery', 'open'),
]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "The west pocket of the Gemstone Mines, under the hill above Castleview's gemsmiths: a timbered adit "
                 "and gallery, a high ruby stope round a rock pillar, a drift the arachnoid queens have webbed shut, a "
                 "sump of standing water, a winding emerald gallery and a dead end of miners' bones. Five ruby and "
                 "five emerald veins give one rock each until the God of Minerals (DD-10B) is paid to refill them.",
        'purpose': "Q-D7 The Gemsmiths (repeatable): rocks for Linus (ruby) and Simon (emerald) on D1. Party 23-27; "
                   "band 16-28; 20 monsters; treasure 3. About 10 minutes.",
        'mood': "A worked-out mine: dark red-brown rock, old timber, torchlight; cold web in the far drift.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'loops': [{'id': 'loop:a', 'spaces': ['room:gallery', 'room:ruby', 'room:cobweb', 'room:sump',
                                              'room:emerald', 'room:bones'],
                   'notes': "West: round the two veins."}],
        'entrances': [{'id': 'entrance:adit', 'space': 'room:adit', 'kind': 'both', 'neighbour': 'exit:d1_adit',
                       'facing': 'n', 'how': "Just inside the adit's mouth, facing in."}],
        'critical_path': ['room:adit', 'room:gallery', 'room:ruby', 'room:cobweb', 'room:sump', 'room:emerald'],
        'return_path': ['room:emerald', 'room:bones', 'room:gallery', 'room:adit'],
        'goals': [
            {'id': 'goal:ruby', 'space': 'room:ruby', 'kind': 'take',
             'what': "Five ruby rocks from the five ruby veins (q-d7.ruby_veins).", 'handed_in_at': 'D1'},
            {'id': 'goal:emerald', 'space': 'room:emerald', 'kind': 'take',
             'what': "Five emerald rocks from the five emerald veins (q-d7.emerald_veins).", 'handed_in_at': 'D1'}],
        'atmosphere': "Torchlit timber in the adit and gallery (ambient about 15-18), the caves darker (12-16), the "
                      "web drift coldest. Music 18. Sounds: air at the adit's mouth, drips in the stope and the sump.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': 2, 'doors': 3, 'fixed_actors': 20, 'loops': 1, 'monsters_about': 20, 'rooms': 7,
                   'sectors': 7, 'spawn_points': 0, 'floor_area_millions': 10},
        'notes': "Class S (MAPS, Dungeons): at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 "
                 "doors. D-27: five veins per gem, one rock each, a map variable each; refill_a on entry; one "
                 "exploding bone heap; 7d35 with A6's two vein pictures.",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    elif level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return d


DIAGRAM = """   [Timbered gallery: 3 bats, cart]---(open)---[RUBY STOPE: 5 ruby veins]---(open)---[Cobweb drift: queens]
          |                 |                                                                |
        =door=           (open)                                                           =door=
          |                 |                                                                |
   [West adit]       [Bone pocket $, bones,          [Emerald gallery:                  [Sump $, pool]
          |           one heap explodes]--(open)--    5 emerald veins]-------=door=--------/
   D1: the adit above the gemsmiths' row

 $ chest   = = plank door   Every floor at 0. Veins: one rock each until the God of Minerals (DD-10B) is paid.
"""

# D-89 identity (lane A8 s28): crystals frame every vein (mine.py), the rails run on along the timbered gallery to the
# ruby stope, the stopes' floors slope (square shards stand on a slope; a turned one's faces are not flat).
vein_crystals(ROOMS)
_RA = {r['id'].split(':')[1]: r for r in ROOMS}
_RA['gallery']['platforms'] += rails(0, 1040, 0, 2370) + rails(62, 2432, 1500, 2432)
_RA['gallery']['notes'] = _RA['gallery']['notes'].replace("the rails stop at the adit door", "the rails run on to the ruby stope")
_RA['ruby']['floor_points'] = [F(2560, 2880, 48), F(3200, 2560, 32), F(2240, 2560, 24)]
_RA['emerald']['floor_points'] = [F(2816, 1216, 40), F(2368, 1088, 24)]
_RA['bones']['floor_points'] = [F(880, 1300, 64), F(1024, 1856, 40)]
_POOL = [(4224, 1216), (4608, 1152), (4704, 1408), (4608, 1664), (4288, 1664), (4192, 1408)]
_RA['sump']['floor_points'] = [F(3904, 1472, 32), F(4096, 1824, 24)] + [F(x, y, 0) for x, y in _POOL]
_RA['sump']['floor_lines'] = [[F(x, y) for x, y in _POOL + _POOL[:1]]]
_RA['cobweb']['floor_points'] = [F(4352, 2496, 40), F(3840, 2816, -24), F(4608, 3008, 24)]
IDENTITY = {'shape': 'mine', 'family': '7d35',
            'seen': ["a timbered adit and gallery: timber sets, lagging, rails running in to the stopes, an old ore cart",
                     "irregular stopes round rock pillars, their floors sloping, their roofs high in the middle",
                     "ruby and emerald veins in the walls, each framed by crystal growing out of the rock"]}

ROOMS_DOC = {'format': 0, 'themes': THEMES, 'defaults': {'theme': 'theme:rock', 'ambient': 15}, 'rooms': ROOMS,
             'openings': OPENINGS,
             'notes': "DD-10A at L3/L4: seven rooms in the plan's frame (x east, y north, the adit's mouth at y 0). "
                      "Written by output/studio_cal/dd10a/tools/gen.py with tools/mine.py."}

if __name__ == '__main__':
    write_levels(OUT, sys.argv[1:] or ['L1', 'L2', 'L3', 'L4'], PROJECT, plan, DIAGRAM, ROOMS_DOC, OBJECTS, WIRING, IDENTITY)
