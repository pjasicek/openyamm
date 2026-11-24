"""DD-05 Western Tower of Mok: writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd05/L*) from one place.

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd05), phase 4, decider D-42.
Plan frame: x east, y north; four floors 640 apart (L1 0, L2 640, L3 1280, L4 1920; the chapel rises into the cone).
The tower's inside is 3,456 square (x, y -1728..1728), larger than D1's tower (D-42 (6)). Six flights of 20 steps run
north-south in four lanes 320 wide (y -640..640): E1 x 1408-1728 (L1-L2 east stair, rising north; L3-L4 tower stair,
rising south), E2 x 1024-1344 (L2-L3 outer stair, north), W2 x -1344..-1024 (L2-L3 west stair, north), W1 x
-1728..-1408 (L1-L2 south stair, north; L3-L4 altar stair, north). Each pair of floors is joined by two stairs in
different places (the source's pairs), so every floor is crossed. Every room's ceiling stays at least 64 under the
floor of any room above it in plan (a flight's plan is its own on both of its floors).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import sys
import yaml

R = _REPO_ROOT
OUT = R + '/devdocs/xeen/briefs/dd05'


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.add_representer(Flow, flow_rep)


def F(*a):
    return Flow(a)


def S(texture, w, h, scale=None, **kw):
    d = {'texture': texture, 'size': F(w, h)}
    if scale:
        d['scale'] = scale
    d.update(kw)
    return d


def FIT(texture, w, h):
    return {'texture': texture, 'size': F(w, h), 'fit': True}


def dump(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)


# ---------------------------------------------------------------------------------------------------------------------
# Numbers

MAP_ID = 9154
QBITS = {
    'arrived_once': 117360,      # the map's own (provisional block 117360-117399)
    'humble_slain': 117361,      # the map's own: Humble cut down (the Yes answer; hides him for good)
    'pious_slain': 117362,       # the map's own: Pious cut down
    'started': 113120,           # Q-D6 (A3)
    'leader_slain': 113123,
    'humble_spared': 113124,
    'tower_opened': 113125,
    'alcove_disks': 113126,
    'pious_spared': 113128,
}
ITEMS = {'energy_disk': 12334, 'west_tower_key': 12338, 'golden_pegasus': 12349}
HERETIC, PRIEST, LORD, LEADER = 11220, 11221, 11222, 11223
STONE, IRON = 11581, 11582
HUMBLE, PIOUS = 11910, 11911
G_HUMBLE, G_PIOUS = 40, 41

FL = [0, 640, 1280, 1920]
CEIL = 512          # a room's height on L1-L3 (its ceiling 64 under the next floor at most: 576)

# D1's arrivals for this tower (installed assets_dev/worlds/xeen/maps/xeen_d1.studio.yml, A6): the rope's foot on the
# north face and the front door's step on the south face.
D1_ROPE = [-16896, 16896, 1600]
D1_DOOR = [-16896, 14848, 1600]

# ---------------------------------------------------------------------------------------------------------------------
# Textures (D-42 / the graph): the Towers of Mok family, MM8 Castle of Air d27 (gston1wl walls over a gstntilev
# skirting, gston1fl, gstn1cl, gcstflor in the stair halls and dormitories, gcstdoor); the heretics' chapel and vestry
# in MM8 Temple of the Sun d22 (gtempw1-2, gtempflr, gtemprf, gtempdor1); the windows MM8's Mok tower window t19b04c;
# the tapestries A8's xmoktap (D-42, new).

WALL = S('gston1wl', 128, 256)
SKIRT = S('gstntilev', 64, 128)
FLOOR = S('gston1fl', 128, 128)
COBBLE = S('gcstflor', 128, 256)
CEILING = S('gstn1cl', 128, 128)
DOOR = FIT('gcstdoor', 128, 256)
MARBLE = S('gtempw1', 128, 256)
NICHE = FIT('gtempw2', 128, 256)          # d22's carved marble arch: a niche's back, once per face
TFLOOR = S('gtempflr', 128, 128)
MOSAIC = S('gtemprf', 128, 128)
TDOOR = FIT('gtempdor1', 128, 256)
WINDOW = FIT('t19b04c', 128, 256)
TAPESTRY = FIT('xmoktap', 128, 256)       # A8's new texture (D-42), registered by A6
MIRROR = S('xkmirror', 128, 128)          # A6's silvered glass (D-37 (2)), a seamless tile
FRAME = S('gstntilev', 64, 128)
PLANK = S('7trimd', 128, 256)
SHEET = S('t2bedsht', 128, 256)
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}
HEARTH = S('gstyl', 128, 128)

THEMES = [
    {'id': 'theme:tower', 'wall': WALL, 'bands': [{'height': 32, 'surface': SKIRT}], 'floor': FLOOR,
     'ceiling': CEILING, 'reveal': WALL, 'door': S('gcstdoor', 128, 256),
     'notes': "The Mok tower's own rooms: MM8 Castle of Air (d27) green-grey ashlar gston1wl over a green marble "
              "skirting gstntilev, scale-pattern flags gston1fl, panelled stone ceilings gstn1cl, the stone doors."},
    {'id': 'theme:stair', 'wall': WALL, 'floor': COBBLE, 'ceiling': CEILING, 'reveal': WALL,
     'door': S('gcstdoor', 128, 256),
     'notes': "The stairs, landings and the priests' sleeping rooms: the same ashlar, grey cobbles gcstflor."},
    {'id': 'theme:temple', 'wall': MARBLE, 'floor': TFLOOR, 'ceiling': MOSAIC, 'reveal': MARBLE,
     'door': S('gtempdor1', 128, 256),
     'notes': "The heretics' chapel and vestry: MM8 Temple of the Sun (d22) pale marble gtempw1, blue flags gtempflr, "
              "the gold-blue mosaic gtemprf, the blue temple door gtempdor1."},
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms


def rect(x0, y0, x1, y1):
    return [F(x0, y0), F(x1, y0), F(x1, y1), F(x0, y1)]


def poly(*pts):
    return [F(*p) for p in pts]


E1 = (1408, 1728)
E2 = (1024, 1344)
W2 = (-1344, -1024)
W1 = (-1728, -1408)
LANE_Y = (-640, 640)


def flight(i, name, lane, f0, toward, notes):
    return {'id': 'room:' + i, 'name': name, 'outline': rect(lane[0], LANE_Y[0], lane[1], LANE_Y[1]),
            'floor': f0, 'slope': {'to': f0 + 640, 'toward': toward, 'steps': 20}, 'ceiling': f0 + 640 + 448,
            'theme': 'theme:stair', 'ambient': 14, 'notes': notes}


def panel_xy(box, wall, centre, length, surface, bottom, height, pid=None, notes=None):
    """A panel on a rectangular room's wall, centred at `centre` (x on south/north walls, y on east/west walls)."""
    x0, y0, x1, y1 = box
    start = {'south': centre - length / 2 - x0, 'east': centre - length / 2 - y0,
             'north': x1 - (centre + length / 2), 'west': y1 - (centre + length / 2)}[wall]
    d = {}
    if pid:
        d['id'] = 'panel:' + pid
    d.update({'offset': int(start), 'length': length, 'bottom': bottom, 'height': height, 'surface': surface})
    if notes:
        d['notes'] = notes
    return d


def plat(i, at, size, rise, surface, top=None, **kw):
    d = {}
    if i:
        d['id'] = 'platform:' + i
    d.update({'at': F(*at), 'size': F(*size), 'rise': rise, 'surface': surface, 'top_surface': top or surface})
    d.update(kw)
    return d


def bed(i, at, size=(192, 384)):
    return plat(i, at, size, 48, PLANK, SHEET, notes="A bed: a straw tick under a grey blanket.")


# Boxes of the rectangular rooms (x0, y0, x1, y1)
B = {
    'hoist': (1024, 1024, 1728, 1728),
    'gallery': (384, -128, 960, 1728),
    'chapel': (-1728, 704, 320, 1728),
    'vestry': (-1344, -640, -832, 640),
    'tap': (-768, -640, 320, -128),
    'landing3': (1024, 704, 1728, 1280),
    'dorm3': (-1344, 704, 960, 1664),
    'fountains3': (-640, -640, 640, 640),
    'cloister3': (-1728, -1216, 1728, -704),
    'pious': (-384, -1728, 384, -1280),
    'landing2': (-1728, -1600, -832, -704),
    'kitchen2': (832, -1600, 1728, -704),
    'refectory': (-768, -1088, 768, 640),
    'fountains2': (-1728, 704, -64, 1344),
    'dorm2': (0, 704, 1728, 1280),
    'humble': (704, 1344, 1344, 1728),
    'alcoves': (-960, -640, 960, 1216),
    'mirror': (-640, -1088, 640, -704),
    'door_hall': (-960, -1728, 960, -1152),
    'guardians': (1024, -1728, 1728, -1152),
}


def box_room(i, name, key, floor, theme, ambient, notes, ceiling=None, **kw):
    x0, y0, x1, y1 = B[key]
    d = {'id': 'room:' + i, 'name': name, 'outline': rect(x0, y0, x1, y1), 'floor': floor,
         'ceiling': ceiling or floor + CEIL, 'theme': theme, 'ambient': ambient}
    d.update(kw)
    d['notes'] = notes
    return d


def fountain_niche(box, wall, centre, pid, notes):
    return panel_xy(box, wall, centre, 192, NICHE, 0, 384, pid=pid, notes=notes)


ROOMS = [
    # ---- L4 (1920): the heretics' floor
    box_room('hoist', 'Hoist room', 'hoist', FL[3], 'theme:tower', 16,
             "The arrival from D1's rope: the open window on the north wall where the heretics' rope ends, a windlass "
             "beam beside it, the heretics' bread and candles in sacks along the walls (a storeroom).",
             store=True,
             platforms=[plat('windlass', (1632, 1568), (96, 224), 128, PLANK,
                             notes="The windlass's frame: a beam on two posts by the window.")]),
    box_room('bone_gallery', 'Bone gallery', 'gallery', FL[3], 'theme:tower', 14,
             "A long gallery inside the outer wall from the hoist room to the chapel's double doors and the cells; "
             "heaps of bones in its corners, what is left of the priests who stayed loyal."),
    {'id': 'room:chapel', 'name': "The heretics' altar", 'outline': rect(*B['chapel']), 'floor': FL[3],
     'ceiling': FL[3] + 960, 'ceiling_points': [F(-704, 1216, FL[3] + 1344)], 'theme': 'theme:temple', 'ambient': 22,
     'walls': [{'wall': 'west', 'panels': [
         panel_xy(B['chapel'], 'west', 1216, 256, TAPESTRY, 96, 512, pid='sun',
                  notes="Behind the altar: Mok's sun with the open eye, the heretics' sign daubed over it.")]}],
     'platforms': [plat('altar', (-1472, 1216), (192, 384), 96, MARBLE, TFLOOR,
                        notes="The altar of pale marble; the key lies under a heretical candle.")],
     # The cone's ring beam: four tie beams of dark timber from wall to wall, crossing round the chandelier.
     'beams': [{'path': [F(-1728, y), F(320, y)], 'width': 48, 'bottom': FL[3] + 704, 'depth': 48,
                'surface': PLANK} for y in (928, 1504)]
     + [{'path': [F(x, 704), F(x, 1728)], 'width': 48, 'bottom': FL[3] + 656, 'depth': 48, 'surface': PLANK}
        for x in (-992, -416)],
     'notes': "Behind double doors: pale marble and blue flags under the cone's gold-blue mosaic, a ring beam of dark "
              "timber round the cone, the altar at the west end under Mok's daubed sun. The Cult Leader preaches "
              "there."},
    box_room('vestry', 'Vestry', 'vestry', FL[3], 'theme:temple', 18,
             "Behind the altar: vestments in a press along the west wall, the Cult Leader's chest. A door to the "
             "chapel; a panel to the tapestry walk that the button behind the middle tapestry slides.",
             platforms=[plat('press', (-1280, 192), (64, 448), 256, PLANK, PLANK,
                             notes="A press of vestments against the west wall.")]),
    box_room('tapestry_walk', 'Tapestry walk', 'tap', FL[3], 'theme:tower', 16,
             "Three hangings of Mok's sun with the heretics' sign daubed over them; behind the middle one a button.",
             walls=[{'wall': 'north', 'panels': [
                 panel_xy(B['tap'], 'north', x, 128, TAPESTRY, 64, 256, pid=p,
                          notes="A tapestry of Mok's sun, daubed over.")
                 for x, p in ((-512, 'tap_a'), (-224, 'tap_b'), (64, 'tap_c'))]}]),
    {'id': 'room:cells', 'name': "Heretics' cells",
     'outline': poly((384, -1728), (1728, -1728), (1728, -704), (1344, -704), (1344, -192), (384, -192)),
     'floor': FL[3], 'ceiling': FL[3] + CEIL, 'theme': 'theme:stair', 'ambient': 14,
     'platforms': [bed('bed_l4_w', (480, -1504)), bed('bed_l4_e', (1632, -1504))],
     'notes': "The heretics' sleeping room off the gallery's south end; two beds with something under the blanket; "
              "the tower stair's head in the north-east corner."},
    flight('altar_stair', 'Altar stair', W1, FL[2], 'north',
           "The priests' stair: twenty steps from L3's cloister up north to the chapel, beside the altar."),
    flight('tower_stair', 'Tower stair', E1, FL[2], 'south',
           "The stair in the wall: twenty steps from L3's stair landing up south to the cells."),
    # ---- L3 (1280): Pious's floor
    box_room('landing3', 'Stair landing', 'landing3', FL[2], 'theme:stair', 16,
             "The head of the outer stair from L2 and the foot of the tower stair to L4, side by side; open to the "
             "dormitory."),
    box_room('dorm3', 'Upper dormitory', 'dorm3', FL[2], 'theme:stair', 16,
             "Beds along the north wall, the senior priest's chest beside his; the west stair's head.",
             platforms=[bed('bed_l3_%d' % i, (x, 1472)) for i, x in enumerate((-1088, -640, -192, 256), 1)]),
    box_room('fountains3', 'Fountains of cold and venom', 'fountains3', FL[2], 'theme:tower', 18,
             "Two wall fountains in carved marble niches, west and east: +5 Water and +5 Body resistance, once per "
             "character (the hooks decide).",
             walls=[{'wall': 'west', 'panels': [fountain_niche(B['fountains3'], 'west', 0, 'niche_water',
                                                               "The cold fountain's niche.")]},
                    {'wall': 'east', 'panels': [fountain_niche(B['fountains3'], 'east', 0, 'niche_body',
                                                               "The venom fountain's niche.")]}],
             platforms=[plat('fountain_water', (-576, 0), (128, 192), 96, MARBLE, WATER,
                             notes="The cold fountain's basin."),
                        plat('fountain_body', (576, 0), (128, 192), 96, MARBLE, WATER,
                             notes="The venom fountain's basin.")]),
    box_room('cloister3', 'Cloister', 'cloister3', FL[2], 'theme:tower', 16,
             "A long walk round the floor's south side, windows at its ends; the altar stair's foot at its west end, "
             "the fountains north, Pious's door south.",
             walls=[{'wall': 'west', 'panels': [panel_xy(B['cloister3'], 'west', -960, 160, WINDOW, 96, 320,
                                                         notes="A pointed window in the tower's wall.")]},
                    {'wall': 'east', 'panels': [panel_xy(B['cloister3'], 'east', -960, 160, WINDOW, 96, 320,
                                                         notes="A pointed window in the tower's wall.")]}]),
    box_room('pious', "Pious's cell", 'pious', FL[2], 'theme:stair', 16,
             "A cell behind a door off the cloister: Pious the Cleric by his bed, begging.",
             platforms=[bed('bed_pious', (-288, -1504))]),
    flight('west_stair3', 'West stair', W2, FL[1], 'north',
           "Twenty steps from L2's landing up north to the upper dormitory."),
    flight('outer_stair3', 'Outer stair', E2, FL[1], 'north',
           "Twenty steps from L2's kitchen up north to L3's stair landing."),
    # ---- L2 (640): Humble's floor (windowless)
    box_room('landing2', 'Landing', 'landing2', FL[1], 'theme:stair', 14,
             "The foot of the west stair; the refectory east."),
    box_room('kitchen2', 'Kitchen', 'kitchen2', FL[1], 'theme:stair', 18,
             "The foot of the outer stair: a hearth on the south wall, a table along the north wall, barrels in "
             "pairs and sacks in the corners (the bread hauled up the rope), a chest in the larder corner.",
             store=True,
             platforms=[plat('hearth', (1280, -1536), (384, 128), 32, HEARTH,
                             notes="The hearth's stone bed against the south wall."),
                        plat('kitchen_table', (1568, -800), (256, 96), 72, PLANK,
                             notes="A work table along the north wall.")]),
    box_room('refectory', 'Refectory', 'refectory', FL[1], 'theme:tower', 16,
             "One long table and its benches along the hall's axis in its north-east part, off the walking lines "
             "between the three doors.",
             platforms=[plat('table', (512, 320), (192, 512), 72, PLANK, notes="The refectory's long table."),
                        plat(None, (352, 320), (64, 512), 40, PLANK, notes="A bench."),
                        plat(None, (672, 320), (64, 512), 40, PLANK, notes="A bench.")]),
    box_room('fountains2', 'Fountains of fire and lightning', 'fountains2', FL[1], 'theme:tower', 18,
             "Two wall fountains in carved marble niches on the north wall: +5 Fire and +5 Air resistance, once per "
             "character (the hooks decide); two of Mok's stone guardians.",
             walls=[{'wall': 'north', 'panels': [
                 fountain_niche(B['fountains2'], 'north', -1216, 'niche_fire', "The fire fountain's niche."),
                 fountain_niche(B['fountains2'], 'north', -576, 'niche_air', "The lightning fountain's niche.")]}],
             platforms=[plat('fountain_fire', (-1216, 1280), (192, 128), 96, MARBLE, WATER,
                             notes="The fire fountain's basin."),
                        plat('fountain_air', (-576, 1280), (192, 128), 96, MARBLE, WATER,
                             notes="The lightning fountain's basin.")]),
    box_room('dorm2', 'Lower dormitory', 'dorm2', FL[1], 'theme:stair', 16,
             "Beds along the north wall; under one mattress a purse. The east stair's head; Humble's door north.",
             platforms=[bed('bed_l2_purse', (256, 1088)), bed('bed_l2_b', (640, 1088)), bed('bed_l2_c', (1632, 1088))]),
    box_room('humble', "Humble's cell", 'humble', FL[1], 'theme:stair', 16,
             "A cell behind a door off the dormitory: Humble the Cleric by his bed, begging.",
             platforms=[bed('bed_humble', (800, 1536), (192, 320))]),
    flight('east_stair2', 'East stair', E1, FL[0], 'north',
           "Twenty steps from L1's stair hall up north to the lower dormitory."),
    flight('south_stair2', 'South stair', W1, FL[0], 'north',
           "Twenty steps from L1's novices' dormitory up north to the fountains of fire and lightning."),
    # ---- L1 (0): the ground floor (windowless)
    {'id': 'room:stair_hall1', 'name': 'Stair hall',
     'outline': poly((1024, -1088), (1728, -1088), (1728, -704), (1344, -704), (1344, 640), (1024, 640)),
     'floor': FL[0], 'ceiling': CEIL, 'theme': 'theme:stair', 'ambient': 16,
     'notes': "The foot of the east stair; a passage north along the stair's side into the hall of alcoves."},
    box_room('alcoves', 'Hall of alcoves', 'alcoves', FL[0], 'theme:tower', 18,
             "Round the old stair core three alcoves in carved marble niches: west and east each a disc, north the "
             "Pegasus statuette.",
             pillars=[{'at': F(0, 576), 'size': F(512, 512), 'surface': WALL}],
             walls=[{'wall': 'west', 'panels': [panel_xy(B['alcoves'], 'west', 832, 192, NICHE, 0, 384,
                                                         pid='alcove_w', notes="The west alcove.")]},
                    {'wall': 'east', 'panels': [panel_xy(B['alcoves'], 'east', 832, 192, NICHE, 0, 384,
                                                         pid='alcove_e', notes="The east alcove.")]},
                    {'wall': 'north', 'panels': [panel_xy(B['alcoves'], 'north', 0, 192, NICHE, 0, 384,
                                                          pid='alcove_n', notes="The north alcove.")]}],
             platforms=[plat('plinth_w', (-896, 832), (128, 192), 96, MARBLE, TFLOOR,
                             notes="The west alcove's ledge."),
                        plat('plinth_e', (896, 832), (128, 192), 96, MARBLE, TFLOOR,
                             notes="The east alcove's ledge."),
                        plat('plinth_n', (0, 1152), (192, 128), 96, MARBLE, TFLOOR,
                             notes="The north alcove's ledge.")]),
    {'id': 'room:dorm1', 'name': "Novices' dormitory",
     'outline': poly((-1728, -1728), (-1024, -1728), (-1024, 640), (-1344, 640), (-1344, -704), (-1728, -704)),
     'floor': FL[0], 'ceiling': CEIL, 'theme': 'theme:stair', 'ambient': 14,
     'platforms': [bed('bed_l1_a', (-1632, -1500)), bed('bed_l1_b', (-1632, -1050))],
     'notes': "The foot of the south stair; beds along the west wall, clear of the lines to the alcoves and the door "
              "hall; a passage north beside the stair into the hall of alcoves."},
    box_room('mirror_hall', 'Mirror hall', 'mirror', FL[0], 'theme:tower', 16,
             "A short hall between the alcoves and the door hall; a dead mirror on its north wall.",
             walls=[{'wall': 'north', 'panels': [
                 panel_xy(B['mirror'], 'north', -448, 192, MIRROR, 96, 288, pid='mirror',
                          notes="The dead mirror, silvered glass in a green marble frame."),
                 panel_xy(B['mirror'], 'north', -560, 32, FRAME, 64, 352, notes="The mirror's frame."),
                 panel_xy(B['mirror'], 'north', -336, 32, FRAME, 64, 352),
                 panel_xy(B['mirror'], 'north', -448, 192, FRAME, 64, 32),
                 panel_xy(B['mirror'], 'north', -448, 192, FRAME, 384, 32)]}]),
    box_room('door_hall', 'Hall of the warded door', 'door_hall', FL[0], 'theme:tower', 16,
             "Inside the front door; its Heretic Lord and three of Mok's iron guardians wait behind the mirror hall's "
             "door (F45: not in sight of the landing)."),
    box_room('guardians', "Guardians' gallery", 'guardians', FL[0], 'theme:tower', 14,
             "Mok's stone guardians, three of them awake; the old temple's offering chest at the east end."),
]


def op(i, a, b, link, width, height, **kw):
    d = {'id': 'open:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'link': 'link:' + link, 'width': width,
         'height': height}
    d.update(kw)
    return d


def foot(i, room, stair, link, room_wall, stair_wall):
    return op(i, room, stair, link, 'full', 'full', from_wall=room_wall, to_wall=stair_wall)


OPENINGS = [
    # L4
    op('hoist_gallery', 'hoist', 'bone_gallery', 'hoist_gallery', 192, 320),
    op('gallery_chapel', 'bone_gallery', 'chapel', 'gallery_chapel', 256, 352, notes="The chapel's double doors."),
    op('gallery_cells', 'bone_gallery', 'cells', 'gallery_cells', 384, 384, shape='arch', apex=448),
    op('cells_tap', 'cells', 'tapestry_walk', 'cells_tap', 320, 384, from_wall=5),
    op('tap_vestry', 'tapestry_walk', 'vestry', 'tap_vestry', 192, 288, notes="The panel behind the tapestries."),
    op('chapel_vestry', 'chapel', 'vestry', 'chapel_vestry', 192, 320),
    foot('altar_head', 'chapel', 'altar_stair', 'altar_stair', 'south', 'north'),
    foot('tower_head', 'cells', 'tower_stair', 'tower_stair', 2, 'south'),
    # L3
    foot('altar_foot', 'cloister3', 'altar_stair', 'altar_stair', 'north', 'south'),
    foot('tower_foot', 'landing3', 'tower_stair', 'tower_stair', 'south', 'north'),
    op('cloister_pious', 'cloister3', 'pious', 'cloister_pious', 192, 320),
    op('cloister_fountains', 'cloister3', 'fountains3', 'cloister_fountains', 640, 384, shape='arch', apex=448),
    op('fountains_dorm3', 'fountains3', 'dorm3', 'fountains_dorm3', 192, 320),
    op('dorm3_landing', 'dorm3', 'landing3', 'dorm3_landing', 384, 384),
    foot('west_head', 'dorm3', 'west_stair3', 'west_stair', 'south', 'north'),
    foot('outer_head', 'landing3', 'outer_stair3', 'outer_stair', 'south', 'north'),
    # L2
    foot('west_foot', 'landing2', 'west_stair3', 'west_stair', 'north', 'south'),
    foot('outer_foot', 'kitchen2', 'outer_stair3', 'outer_stair', 'north', 'south'),
    op('landing_refectory', 'landing2', 'refectory', 'landing_refectory', 320, 384),
    op('kitchen_refectory', 'kitchen2', 'refectory', 'kitchen_refectory', 192, 320),
    op('refectory_fountains', 'refectory', 'fountains2', 'refectory_fountains', 192, 320),
    op('fountains_dorm2', 'fountains2', 'dorm2', 'fountains_dorm2', 384, 384, shape='arch', apex=448),
    op('dorm2_humble', 'dorm2', 'humble', 'dorm2_humble', 192, 320),
    foot('east_head', 'dorm2', 'east_stair2', 'east_stair', 'south', 'north'),
    foot('south_head', 'fountains2', 'south_stair2', 'south_stair', 'south', 'north'),
    # L1
    foot('east_foot', 'stair_hall1', 'east_stair2', 'east_stair', 2, 'south'),
    foot('south_foot', 'dorm1', 'south_stair2', 'south_stair', 4, 'south'),
    op('stair_alcoves', 'stair_hall1', 'alcoves', 'stair_alcoves', 384, 384, from_wall=5, to_wall='east'),
    op('alcoves_dorm1', 'alcoves', 'dorm1', 'alcoves_dorm1', 384, 384, from_wall='west', to_wall=1),
    op('alcoves_mirror', 'alcoves', 'mirror_hall', 'alcoves_mirror', 384, 384, shape='arch', apex=448),
    op('dorm1_door_hall', 'dorm1', 'door_hall', 'dorm1_door_hall', 192, 320, from_wall=1, to_wall='west'),
    op('mirror_door_hall', 'mirror_hall', 'door_hall', 'mirror_door_hall', 192, 320),
    op('door_hall_guardians', 'door_hall', 'guardians', 'door_hall_guardians', 192, 320),
]

# ---------------------------------------------------------------------------------------------------------------------
# Monsters (D-42 G and (2)-(4)): heretics 11220-11222 (22/11/3), the Cult Leader 11223, Mok's golems Stone 11581 (5)
# and Iron 11582 (3); Humble 11910 and Pious 11911 placed, peaceful, immobile, not counted. Strongest at the top.

POP = [
    # L4 (10)
    ('bone_gallery', 32, [(HERETIC, 672, 400), (HERETIC, 672, 800), (PRIEST, 560, 1100)]),
    ('cells', 31, [(PRIEST, 1024, -1216), (PRIEST, 768, -1024)]),
    ('chapel', 30, [(LORD, -1024, 960), (LORD, -1024, 1472), (PRIEST, -512, 960), (PRIEST, -512, 1472)]),
    # L3 (12)
    ('cloister3', 20, [(PRIEST, -1200, -960), (HERETIC, -600, -960), (HERETIC, 600, -960), (PRIEST, 1200, -960)]),
    ('fountains3', 21, [(PRIEST, -320, 320), (PRIEST, 320, 320), (HERETIC, 0, -320)]),
    ('dorm3', 22, [(PRIEST, -640, 960), (PRIEST, -192, 1056), (HERETIC, 480, 960)]),
    ('landing3', 23, [(HERETIC, 1200, 1056), (HERETIC, 1552, 1056)]),
    # L2 (10)
    ('kitchen2', 13, [(HERETIC, 1100, -1150), (HERETIC, 1400, -1250)]),
    ('refectory', 12, [(HERETIC, -300, -300), (HERETIC, 256, -512), (HERETIC, -400, 300), (HERETIC, 96, 64)]),
    ('fountains2', 11, [(STONE, -896, 1024), (STONE, -256, 960)]),
    ('dorm2', 10, [(HERETIC, 448, 784), (HERETIC, 960, 928)]),
    # L1 (13)
    ('stair_hall1', 3, [(HERETIC, 1184, -256), (HERETIC, 1500, -896)]),
    ('alcoves', 4, [(HERETIC, -512, -320), (HERETIC, 512, -320)]),
    ('dorm1', 5, [(HERETIC, -1300, -1300), (HERETIC, -1184, -320)]),
    # F45 (the player's pins 2026-11-24, arrivals in the thick of it): the front door's keepers wait behind the mirror
    # hall's door, out of sight of D1's front-door landing (tools/xeen/check_arrivals.py); ids kept.
    ('door_hall', 6, [(LORD, 0, -1024), (IRON, -416, -864), (IRON, 384, -992), (IRON, -256, -992)]),
    ('guardians', 7, [(STONE, 1216, -1600), (STONE, 1472, -1600), (STONE, 1568, -1296)]),
]
MONSTERS = []
for room, group, entries in POP:
    for n, (row, x, y) in enumerate(entries):
        MONSTERS.append({'id': 'monster:%s_%d' % (room, n + 1),
                         'room': 'room:' + ('mirror_hall' if room == 'door_hall' else room), 'monster': row,
                         'at': F(x, y), 'facing': 270, 'group': group})
# A3 35th (2026-11-22): he preaches north of the altar walk, so his body no longer falls between the walk's end
# and the key on the altar and takes its click (was (-1216, 1216), on the walk).
MONSTERS.append({'id': 'monster:cult_leader', 'room': 'room:chapel', 'monster': LEADER, 'at': F(-1152, 1600),
                 'facing': 0, 'group': 30,
                 'notes': "The Cult Leader (A2's boss row 11223, level 45, hp x3, his own skin by S) preaching at the "
                          "altar; his death runs q-d6.cult_leader."})
COUNT = {}
for m in MONSTERS:
    COUNT[m['monster']] = COUNT.get(m['monster'], 0) + 1
assert COUNT == {HERETIC: 22, PRIEST: 11, LORD: 3, LEADER: 1, STONE: 5, IRON: 3}, COUNT
MONSTERS.append({'id': 'monster:humble', 'room': 'room:humble', 'monster': HUMBLE, 'at': F(1184, 1600),
                 'facing': 270, 'group': G_HUMBLE, 'immobile': True,
                 'notes': "Humble the Cleric (A2's peaceful row 11910, faction xeen_character_humble): not counted; "
                          "hidden for good by either answer (humble_spared or humble_slain)."})
MONSTERS.append({'id': 'monster:pious', 'room': 'room:pious', 'monster': PIOUS, 'at': F(128, -1600),
                 'facing': 90, 'group': G_PIOUS, 'immobile': True,
                 'notes': "Pious the Cleric (A2's peaceful row 11911, faction xeen_character_pious): not counted; "
                          "hidden for good by either answer (pious_spared or pious_slain)."})

# ---------------------------------------------------------------------------------------------------------------------
# Objects


def deco(i, room, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + room, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


# The discs first: their numbers (0, 1 in ids.lock.yml `decorations`) are what the alcoves' events hide
# (evt.SetSprite). The Golden Pegasus is a ground item since D-90 (ITEMS_PLACED).
DECORATIONS = [
    deco('disc_w', 'alcoves', 'crysdisc', (-896, 832), floor_height=96, notes="A disc on the west alcove's ledge."),
    deco('disc_e', 'alcoves', 'crysdisc', (896, 832), floor_height=96, notes="A disc on the east alcove's ledge."),
    # L4
    deco('hoist_sconce', 'hoist', 'scon100', (1024, 1136), wall='west'),
    deco('hoist_sack_1', 'hoist', 'bag01', (1664, 1088)),
    deco('hoist_sack_2', 'hoist', 'floursac', (1552, 1088)),
    deco('hoist_sack_3', 'hoist', 'bag01', (1440, 1088)),
    deco('hoist_sack_4', 'hoist', 'floursac', (1664, 1200)),
    deco('hoist_sack_5', 'hoist', 'bag01', (1664, 1312)),
    deco('hoist_barrel_1', 'hoist', 'bigbarel', (1088, 1088)),
    deco('hoist_barrel_2', 'hoist', 'bigbarel', (1200, 1088)),
    deco('gallery_bones_1', 'bone_gallery', '7dec18', (464, 1648), notes="A heap of bones."),
    deco('gallery_bones_2', 'bone_gallery', '7dec18', (880, 1648), notes="A heap of bones."),
    deco('gallery_bones_3', 'bone_gallery', 'dec29', (896, 160), notes="A heap of bones."),
    deco('gallery_sconce_e', 'bone_gallery', 'scon100', (960, 448), wall='east'),
    deco('gallery_sconce_w', 'bone_gallery', 'scon100', (384, 640), wall='west'),
    deco('chapel_chandelier', 'chapel', 'chndlir0', (-704, 1216), hangs=True),
    deco('chapel_brazier_s', 'chapel', 'dec02', (-1408, 864), notes="A standing candelabrum beside the altar."),
    deco('chapel_brazier_n', 'chapel', 'dec02', (-1408, 1568), notes="A standing candelabrum beside the altar."),
    deco('altar_candle', 'chapel', 'cndlab0', (-1440, 1216), floor_height=FL[3] + 96,
         notes="The heretical candle on the altar."),
    deco('vestry_sconce', 'vestry', 'scon100', (-832, 256), wall='east'),
    deco('tap_sconce', 'tapestry_walk', 'scon100', (-224, -640), wall='south'),
    deco('cells_sconce_s', 'cells', 'scon100', (1056, -1728), wall='south'),
    deco('cells_sconce_w', 'cells', 'scon100', (384, -960), wall='west'),
    # L3
    deco('landing3_sconce', 'landing3', 'scon100', (1376, 1280), wall='north'),
    deco('dorm3_sconce_w', 'dorm3', 'scon100', (-1344, 1088), wall='west'),
    deco('dorm3_sconce_e', 'dorm3', 'scon100', (960, 1472), wall='east'),
    deco('fount3_sconce_1', 'fountains3', 'scon100', (-640, -224), wall='west'),
    deco('fount3_sconce_2', 'fountains3', 'scon100', (-640, 224), wall='west'),
    deco('fount3_sconce_3', 'fountains3', 'scon100', (640, -224), wall='east'),
    deco('fount3_sconce_4', 'fountains3', 'scon100', (640, 224), wall='east'),
    deco('cloister_sconce_1', 'cloister3', 'scon100', (-960, -704), wall='north'),
    deco('cloister_sconce_2', 'cloister3', 'scon100', (960, -704), wall='north'),
    deco('cloister_sconce_3', 'cloister3', 'scon100', (-1088, -1216), wall='south'),
    deco('cloister_sconce_4', 'cloister3', 'scon100', (1088, -1216), wall='south'),
    deco('pious_sconce', 'pious', 'scon100', (384, -1504), wall='east'),
    # L2
    deco('landing2_sconce', 'landing2', 'scon100', (-1728, -1152), wall='west'),
    deco('kitchen_fire', 'kitchen2', 'ckfyr00', (1280, -1536), floor_height=FL[1] + 32,
         notes="The fire on the hearth."),
    deco('kitchen_lamp', 'kitchen2', 'chndlir0', (1280, -1344), hangs=True, notes="A lamp over the hearth."),
    deco('kitchen_barrel_1', 'kitchen2', 'bigbarel', (1664, -1088)),
    deco('kitchen_barrel_2', 'kitchen2', 'bigbarel', (1664, -1200)),
    deco('kitchen_barrel_3', 'kitchen2', 'bigbarel', (896, -1216)),
    deco('kitchen_barrel_4', 'kitchen2', 'bigbarel', (896, -1328)),
    deco('kitchen_sack_1', 'kitchen2', 'bag01', (896, -1536)),
    deco('kitchen_sack_2', 'kitchen2', 'floursac', (1008, -1536)),
    deco('refectory_lamp_1', 'refectory', 'chndlir0', (512, 192), hangs=True),
    deco('refectory_lamp_2', 'refectory', 'chndlir0', (512, 448), hangs=True),
    deco('refectory_sconce', 'refectory', 'scon100', (-768, -256), wall='west'),
    deco('fount2_sconce_1', 'fountains2', 'scon100', (-1408, 1344), wall='north'),
    deco('fount2_sconce_2', 'fountains2', 'scon100', (-1024, 1344), wall='north'),
    deco('fount2_sconce_3', 'fountains2', 'scon100', (-768, 1344), wall='north'),
    deco('fount2_sconce_4', 'fountains2', 'scon100', (-384, 1344), wall='north'),
    deco('dorm2_sconce', 'dorm2', 'scon100', (1728, 896), wall='east'),
    deco('humble_sconce', 'humble', 'scon100', (1344, 1536), wall='east'),
    # L1
    deco('stair_hall_sconce_1', 'stair_hall1', 'scon100', (1344, 192), wall=3),
    deco('stair_hall_sconce_2', 'stair_hall1', 'scon100', (1376, -1088), wall=0),
    deco('alcove_sconce_w', 'alcoves', 'scon100', (-960, 832), wall='west', height=432),
    deco('alcove_sconce_e', 'alcoves', 'scon100', (960, 832), wall='east', height=432),
    deco('alcove_sconce_n', 'alcoves', 'scon100', (0, 1216), wall='north', height=432),
    deco('dorm1_sconce', 'dorm1', 'scon100', (-1728, -1280), wall=5),
    deco('mirror_sconce', 'mirror_hall', 'scon100', (640, -896), wall='east'),
    deco('door_hall_sconce_w', 'door_hall', 'scon100', (-384, -1728), wall='south'),
    deco('door_hall_sconce_e', 'door_hall', 'scon100', (384, -1728), wall='south'),
    deco('guardians_sconce', 'guardians', 'scon100', (1376, -1152), wall='north'),
]

LIGHTS = []


def light(room, at, height, radius, color, **kw):
    d = {'id': 'light:' + room, 'room': 'room:' + room, 'at': F(*at), 'height': height, 'radius': radius,
         'color': F(*color)}
    d.update(kw)
    LIGHTS.append(d)


WARM = (255, 205, 160)
COOL = (210, 220, 240)
light('hoist', (1376, 1376), 360, 1100, COOL, notes="Daylight from the rope window, failing.")
light('bone_gallery', (672, 800), 360, 1600, WARM)
light('chapel', (-704, 1216), 640, 2200, (255, 225, 180))
light('vestry', (-1088, 0), 360, 1000, WARM)
light('tapestry_walk', (-224, -384), 360, 1100, WARM)
light('cells', (1024, -1216), 360, 1300, WARM)
light('landing3', (1376, 992), 360, 900, WARM)
light('dorm3', (-192, 1184), 360, 1500, WARM)
light('fountains3', (0, 0), 400, 1300, (200, 220, 255))
light('cloister3', (0, -960), 360, 2000, WARM)
light('pious', (0, -1504), 340, 700, WARM)
light('landing2', (-1280, -1152), 360, 900, WARM)
light('kitchen2', (1280, -1152), 360, 1100, (255, 180, 120))
light('refectory', (0, -224), 400, 1700, WARM)
light('fountains2', (-896, 1024), 400, 1300, (255, 200, 170))
light('dorm2', (864, 992), 360, 1300, WARM)
light('humble', (1024, 1536), 340, 700, WARM)
light('stair_hall1', (1184, -704), 360, 1100, WARM)
light('alcoves', (0, -64), 400, 1700, WARM)
light('dorm1', (-1376, -1216), 360, 1100, WARM)
light('mirror_hall', (0, -896), 360, 800, WARM)
light('door_hall', (0, -1440), 400, 1400, (255, 190, 150))
light('guardians', (1376, -1440), 360, 900, WARM)

SOUNDS = [
    {'id': 'sound:tower_bed', 'room': 'room:fountains3', 'at': F(0, 0), 'height': 64, 'sound': 'xeen_amb_tower',
     'radius': 4200, 'inner_radius': 2400, 'volume': 0.3, 'pan': False,
     'notes': "The tower of Mok's bed (AUDIO.md xeen_amb_tower, quiet): one source in the middle of the tower on L3, "
              "heard on every floor (no stacking); a bed, not panned (D-48)."},
    {'id': 'sound:hoist_wind', 'room': 'room:hoist', 'at': F(1376, 1664), 'sound': 'whistling wind', 'radius': 1300,
     'inner_radius': 300, 'volume': 0.4, 'notes': "Wind at the open rope window."},
    {'id': 'sound:fountains3', 'room': 'room:fountains3', 'at': F(0, 0), 'sound': 'water lapping loop',
     'radius': 1100, 'inner_radius': 300, 'volume': 0.3, 'notes': "The cold and venom fountains."},
    {'id': 'sound:fountains2', 'room': 'room:fountains2', 'at': F(-896, 1216), 'sound': 'water lapping loop',
     'radius': 1100, 'inner_radius': 300, 'volume': 0.3, 'notes': "The fire and lightning fountains."},
    {'id': 'sound:hearth', 'room': 'room:kitchen2', 'at': F(1280, -1472), 'sound': 'campfire', 'radius': 1100,
     'inner_radius': 250, 'volume': 0.45, 'notes': "The kitchen's hearth."},
    {'id': 'sound:chapel', 'room': 'room:chapel', 'at': F(-1408, 1216), 'sound': 'campfire', 'radius': 1000,
     'inner_radius': 250, 'volume': 0.25, 'notes': "The braziers by the altar."},
]


def door(i, opening, kind='hinged', **kw):
    d = {'id': 'door:' + i, 'opening': opening, 'kind': kind}
    if kind == 'hinged' and 'leaves' not in kw:
        d.update({'hinge': 'left', 'thickness': 16, 'speed': 80})
    elif kind == 'hinged':
        d.update({'thickness': 16, 'speed': 80})
    d.update(kw)
    return d


DOORS = [
    door('hoist', 'open:hoist_gallery', surface=DOOR, back_surface=DOOR),
    door('chapel', 'open:gallery_chapel', leaves=2, surface=TDOOR, back_surface=TDOOR,
         notes="The chapel's double doors: two leaves of d22's blue temple door, the right one mirrored, opening "
               "apart."),
    door('vestry', 'open:chapel_vestry', surface=TDOOR, back_surface=TDOOR),
    door('tap_panel', 'open:tap_vestry', kind='slide_up', secret=True, thickness=16, speed=80, surface=WALL,
         back_surface=MARBLE, tile=True,
         notes="The panel between the tapestry walk and the vestry: the button behind the middle tapestry slides it; "
               "from the vestry it opens by hand."),
    door('pious', 'open:cloister_pious', surface=DOOR, back_surface=DOOR, notes="Pious's cell door."),
    door('dorm3', 'open:fountains_dorm3', surface=DOOR, back_surface=DOOR),
    door('kitchen', 'open:kitchen_refectory', surface=DOOR, back_surface=DOOR),
    door('refectory', 'open:refectory_fountains', surface=DOOR, back_surface=DOOR),
    door('humble', 'open:dorm2_humble', surface=DOOR, back_surface=DOOR, notes="Humble's cell door."),
    door('dorm1', 'open:dorm1_door_hall', surface=DOOR, back_surface=DOOR),
    door('mirror', 'open:mirror_door_hall', surface=DOOR, back_surface=DOOR),
    door('guardians', 'open:door_hall_guardians', surface=DOOR, back_surface=DOOR),
]

CHESTS = [
    {'id': 'chest:vestry', 'room': 'room:vestry', 'at': F(-1088, -560), 'treasure_level': 5,
     'random_items': 3, 'gold': 2500, 'notes': "The Cult Leader's chest (the hoard, one level up)."},
    {'id': 'chest:dorm3', 'room': 'room:dorm3', 'at': F(544, 1600), 'treasure_level': 4,
     'random_items': 2, 'gold': 1200, 'notes': "The senior priest's locked chest beside his bed."},
    {'id': 'chest:kitchen', 'room': 'room:kitchen2', 'at': F(1648, -1520), 'treasure_level': 4,
     'random_items': 2, 'gold': 800, 'notes': "The larder corner's chest."},
    {'id': 'chest:guardians', 'room': 'room:guardians', 'at': F(1648, -1648), 'treasure_level': 4,
     'random_items': 2, 'gold': 1500,
     'notes': "The old temple's offering chest: the heretics never found the key (locked and trapped)."},
]

EXITS = [
    {'id': 'exit:d1_rope', 'room': 'room:hoist', 'at': F(1376, 1728), 'size': F(160, 320),
     'surface': FIT('7solid01', 128, 256), 'to': 'exit:d1_rope',
     'notes': "The open window where the heretics' rope ends: out and down the rope to D1."},
    {'id': 'exit:d1_door', 'room': 'room:door_hall', 'at': F(0, -1728), 'size': F(160, 320),
     'surface': FIT('7solid01', 128, 256), 'to': 'exit:d1_door',
     'notes': "The tower's front door (one leaf, D1's 110-wide hkm3dr outside): warded until q-d6.front_door."},
]

START = {'room': 'room:hoist', 'at': F(1376, 1472), 'facing': 's',
         'notes': "A step inside the rope window, facing into the hoist room (south); D1's rope (entrance:d1_rope)."}
ARRIVALS = [
    {'entrance': 'entrance:d1_rope', 'room': 'room:hoist', 'at': F(1376, 1472), 'facing': 's',
     'notes': "D1's rope (q-d6.tower_rope): a step inside the window, facing into the room."},
    {'entrance': 'entrance:d1_door', 'room': 'room:door_hall', 'at': F(0, -1536), 'facing': 'n',
     'notes': "D1's front door (once tower_opened): inside the door, facing north into the hall."},
]

# D-90 (c, 2026-11-22): the Golden Pegasus on the north alcove's ledge and the key to the Western Tower under the
# heretical candle on the altar lie as 3D ground items (were clicks that gave them through q-d20.pegasus and
# q-d6.tower_key; A3's hooks become `map_gives`). The Pegasus ends the stand-in goblet (S's xeen_pegasus row wait).
ITEMS_PLACED = [
    {'id': 'item:golden_pegasus', 'room': 'room:alcoves', 'item': 'golden_pegasus', 'at': F(0, 1152),
     'floor_height': 96, 'notes': "The Golden Pegasus on the north alcove's ledge (Q-D20)."},
    {'id': 'item:west_tower_key', 'room': 'room:chapel', 'item': 'west_tower_key', 'at': F(-1472, 1216),
     'floor_height': 2016, 'notes': "The key to the Western Tower beside the candle on the altar (Q-D6)."},
]

OBJECTS = {
    'format': 0,
    'start': START,
    'arrivals': ARRIVALS,
    'doors': DOORS,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'chests': CHESTS,
    'monsters': MONSTERS,
    'decorations': DECORATIONS,
    'items': ITEMS_PLACED,
    'exits': EXITS,
    'notes': "DD-05's contents, written by output/studio_cal/dd05/tools/gen.py: 12 doors (the chapel's a pair, one "
             "secret panel), 4 chests, 45 placed monsters and Humble and Pious, no spawn points.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Wiring


def lock_numbers():
    """The decorations' numbers from ids.lock.yml (written by the first build); the discs and the statuette come first."""
    p = OUT + '/L4/ids.lock.yml'
    nums = {'deco:disc_w': 0, 'deco:disc_e': 1}
    if os.path.exists(p):
        lock = yaml.safe_load(open(p)) or {}
        for k in nums:
            if k in (lock.get('decorations') or {}):
                nums[k] = lock['decorations'][k]
    return nums


DN = lock_numbers()
HIDE_DISCS = "evt.SetSprite(%d, 0)\nevt.SetSprite(%d, 0)" % (DN['deco:disc_w'], DN['deco:disc_e'])


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


def find(i, source, title, var, gift, notes, empty="Nothing here."):
    """A find (a bed, a heap of bones): the first click gives `gift`, then the source's 'Nothing here.'."""
    return {'id': 'evt:' + i, 'preset': 'script', 'source': source, 'title': title,
            'condition': {'not': {'map_var': var}},
            'effects': gift + [{'set': {'var': {'map_var': var}, 'value': 1}}],
            'else_effects': [{'text': empty}], 'notes': notes}


PLEA = ("Oh, please don't kill me! I'm not like the others! I didn't want to mutiny against the High Priest! "
        "Slay him anyway?")
KILL_LINE = "The screams of the unarmed cleric fill the tower as you quickly and efficiently dispatch him."
BODY_LINE = ("The only thing in the bed is the lifeless body of a cleric who you mercilessly slew in cold blood.")


def cleric_ask(name, spared, slain, group):
    """The cleric's plea and the map's question (aaze0058:6-10 / aaze0059:6-10): Yes, the source's kill line, the
    map's slain bit; No, A3's hook (the spared bit, his thanks). Either answer hides him for good."""
    return ("if continueStep == 1 then\n"
            "    SetQBit(QBit(%d))\n"
            "    evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1)\n"
            "    evt.SimpleMessage(\"%s\")\n"
            "    return\n"
            "end\n"
            "if continueStep == 2 then\n"
            "    XeenQuests.hook(\"q-d6.%s\")\n"
            "    evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1)\n"
            "    return\n"
            "end\n"
            "if continueStep ~= nil then\n"
            "    return\n"
            "end\n"
            "if IsQBitSet(QBit(%d)) or IsQBitSet(QBit(%d)) then\n"
            "    return\n"
            "end\n"
            "AskChoiceWithAnswerSteps(eventId, 3, \"%s\", {{Answer = \"Yes\", Step = 1}, {Answer = \"No\", Step = 2}})"
            ) % (slain, group, KILL_LINE, name, group, spared, slain, PLEA)


def cleric_bed(name, spared, slain, group):
    return ("if IsQBitSet(QBit(%d)) then\n"
            "    evt.StatusText(\"%s\")\n"
            "    return\n"
            "end\n"
            "if IsQBitSet(QBit(%d)) then\n"
            "    XeenQuests.hook(\"q-d6.%s\")\n"
            "    return\n"
            "end\n" % (slain, BODY_LINE, spared, name)) + cleric_ask(name, spared, slain, group)


def fountain(i, hook, source, notes):
    return {'id': 'evt:' + i, 'preset': 'script', 'source': source, 'title': 'Fountain',
            'lua': "evt.ForPlayer(Players.Current)\nXeenQuests.hook(\"%s\")\n"
                   "evt.PlaySoundName(\"xeen_spring_drink\", 0, 0, 0)" % hook,
            'notes': notes}


ON_LOAD = ("if IsQBitSet(QBit(%d)) then\n%s\nend\n"
           "if IsQBitSet(QBit(%d)) or IsQBitSet(QBit(%d)) then\n"
           "    evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1)\nend\n"
           "if IsQBitSet(QBit(%d)) or IsQBitSet(QBit(%d)) then\n"
           "    evt.SetMonGroupBit(%d, MonsterBits.Invisible, 1)\nend") % (
    QBITS['alcove_disks'], '\n'.join('    ' + s for s in HIDE_DISCS.split('\n')),
    QBITS['humble_spared'], QBITS['humble_slain'], G_HUMBLE,
    QBITS['pious_spared'], QBITS['pious_slain'], G_PIOUS)

FIND_ITEM = [{'give_item': {'level': 4}}]

EVENTS = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'not': {'qbit': 'arrived_once'}}, 'once': True,
     'effects': [{'message': "THE WESTERN TOWER OF MOK. You climb in over the sill. Sacks of bread, a windlass, the "
                             "heretics' candles: they trust their wards, not their windows. Somewhere below them, "
                             "Dreyfus says, the Cult Leader preaches by the altar where the key to the front door "
                             "lies."},
                 {'qbit': 'arrived_once'}],
     'notes': "Why the party is here (Q-D6), on the first arrival only (arrived_once 117360)."},
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load', 'text': "The Western Tower of Mok.",
     'notes': "Every entry: a status line."},
    {'id': 'evt:restore', 'preset': 'script', 'trigger': 'load', 'lua': ON_LOAD,
     'notes': "On every load: the discs gone once alcove_disks, Humble and "
              "Pious hidden once either answer was given."},
    {'id': 'evt:exit_rope', 'preset': 'exit', 'source': 'exit:d1_rope', 'title': "Exit the Great Western Tower",
     'notes': "Out by the rope to D1's foot of the north wall (entrance:dd05_rope): the game's window (D-24); the "
              "source's 'Exit the Great Western Tower?' (aaze0057:8) is the title."},
    {'id': 'evt:exit_door', 'preset': 'exit', 'source': 'exit:d1_door', 'title': "Exit the Great Western Tower",
     'condition': {'qbit': 'tower_opened'},
     'else_effects': [{'lua': "XeenQuests.hook(\"q-d6.front_door\")"}],
     'notes': "The front door: before tower_opened A3's q-d6.front_door (with the key: the wards die, tower_opened "
              "and the door autonote; without: 'Locked, and warded from both sides.'); after it the game's leave "
              "window to D1's step (entrance:dd05_door)."},
    # doors and chests
    {'id': 'evt:door_hoist', 'preset': 'door', 'source': 'door:hoist', 'title': 'Door'},
    {'id': 'evt:door_chapel', 'preset': 'door', 'source': 'door:chapel', 'title': 'Double doors'},
    {'id': 'evt:door_vestry', 'preset': 'door', 'source': 'door:vestry', 'title': 'Door'},
    {'id': 'evt:tap_panel_back', 'preset': 'door', 'source': 'door:tap_panel', 'side': 'room:vestry',
     'title': 'Panel', 'notes': "From the vestry the panel slides by hand; from the walk only the button moves it."},
    {'id': 'evt:door_pious', 'preset': 'door', 'source': 'door:pious', 'title': 'Door'},
    {'id': 'evt:door_dorm3', 'preset': 'door', 'source': 'door:dorm3', 'title': 'Door'},
    {'id': 'evt:door_kitchen', 'preset': 'door', 'source': 'door:kitchen', 'title': 'Door'},
    {'id': 'evt:door_refectory', 'preset': 'door', 'source': 'door:refectory', 'title': 'Door'},
    {'id': 'evt:door_humble', 'preset': 'door', 'source': 'door:humble', 'title': 'Door'},
    {'id': 'evt:door_dorm1', 'preset': 'door', 'source': 'door:dorm1', 'title': 'Door'},
    {'id': 'evt:door_mirror', 'preset': 'door', 'source': 'door:mirror', 'title': 'Door'},
    {'id': 'evt:door_guardians', 'preset': 'door', 'source': 'door:guardians', 'title': 'Door'},
    {'id': 'evt:chest_vestry', 'preset': 'chest', 'source': 'chest:vestry', 'title': 'Chest'},
    {'id': 'evt:chest_dorm3', 'preset': 'chest', 'source': 'chest:dorm3', 'title': 'Chest'},
    {'id': 'evt:chest_kitchen', 'preset': 'chest', 'source': 'chest:kitchen', 'title': 'Chest'},
    {'id': 'evt:chest_guardians', 'preset': 'chest', 'source': 'chest:guardians', 'title': 'Chest'},
    # L4: the chapel, the key, the Cult Leader
    {'id': 'evt:leader_slain', 'preset': 'script', 'trigger': 'timer', 'every': 2,
     'condition': {'kills': {'monster': 'monster:cult_leader'}}, 'once': True,
     'lua': "XeenQuests.hook(\"q-d6.cult_leader\")",
     'notes': "The Cult Leader's death runs A3's q-d6.cult_leader (leader_slain 113123)."},
    text('sun', 'panel:sun', 'Tapestry', "Mok's sun with the open eye, a red daub of the heretics' sign over it.",
         window=False),
    # The tapestry walk (aaze0060:0-2)
    {'id': 'evt:tap_button', 'preset': 'switch', 'source': 'panel:tap_b', 'title': 'Tapestry',
     'opens': ['door:tap_panel'], 'text': "Button. Click.",
     'notes': "The button behind the middle tapestry: the panel into the vestry slides up (aaze0060:0-2)."},
    text('tap_a', 'panel:tap_a', 'Tapestry', "Nothing here."),
    text('tap_c', 'panel:tap_c', 'Tapestry', "Nothing here."),
    # finds (aaze0057:6-7, aaze0060:3-6)
    find('bones_1', 'deco:gallery_bones_1', 'Bones', 'bones_1', [{'gold': 300}],
         "A heap of bones: a find (aaze0060:5-6), then 'Nothing here.'"),
    find('bones_2', 'deco:gallery_bones_2', 'Bones', 'bones_2', FIND_ITEM,
         "A heap of bones: a find, then 'Nothing here.'"),
    find('bones_3', 'deco:gallery_bones_3', 'Bones', 'bones_3', [{'gold': 450}],
         "A heap of bones: a find, then 'Nothing here.'"),
    find('bed_l4_w', 'platform:bed_l4_w', 'Bed', 'bed_l4_w', FIND_ITEM,
         "Something under the blanket (aaze0060:3-4), then 'Nothing here.'"),
    find('bed_l4_e', 'platform:bed_l4_e', 'Bed', 'bed_l4_e', [{'gold': 600}],
         "Something under the blanket, then 'Nothing here.'"),
    find('bed_l3', 'platform:bed_l3_3', 'Bed', 'bed_l3', FIND_ITEM, "One bed's find, then 'Nothing here.'"),
    text('bed_l3_1', 'platform:bed_l3_1', 'Bed', "Nothing here."),
    text('bed_l3_2', 'platform:bed_l3_2', 'Bed', "Nothing here."),
    text('bed_l3_4', 'platform:bed_l3_4', 'Bed', "Nothing here."),
    find('bed_l2_purse', 'platform:bed_l2_purse', 'Bed', 'bed_l2_purse', [{'gold': 750}],
         "Under the mattress a purse (the source's L2 gold), then 'Nothing here.'"),
    text('bed_l2_b', 'platform:bed_l2_b', 'Bed', "Nothing here."),
    text('bed_l2_c', 'platform:bed_l2_c', 'Bed', "Nothing here."),
    find('bed_l1_a', 'platform:bed_l1_a', 'Bed', 'bed_l1_a', [{'gold': 400}],
         "The source's (3,8) bed: a find (aaze0057:6-7), then 'Nothing here.'"),
    find('bed_l1_b', 'platform:bed_l1_b', 'Bed', 'bed_l1_b', FIND_ITEM,
         "The source's (7,4) bed: a find, then 'Nothing here.'"),
    # Humble (L2) and Pious (L3): the plea on entering the cell; the bed after
    {'id': 'evt:humble_ask', 'preset': 'script', 'trigger': 'step', 'source': 'room:humble',
     'title': 'Humble the Cleric',
     'lua': cleric_ask('humble', QBITS['humble_spared'], QBITS['humble_slain'], G_HUMBLE),
     'notes': "Coming into Humble's cell: his plea and 'Slay him anyway?' (aaze0058:6-7). No: A3's q-d6.humble "
              "(humble_spared, 'Thank you for sparing my life...'); Yes: the source's kill line (aaze0058:9), the "
              "map's humble_slain 117361. Either way he is hidden for good, with no XP."},
    {'id': 'evt:humble_bed', 'preset': 'script', 'source': 'platform:bed_humble', 'title': 'Bed',
     'lua': cleric_bed('humble', QBITS['humble_spared'], QBITS['humble_slain'], G_HUMBLE),
     'notes': "Humble's bed: the plea again while he waits; after Yes the source's 'lifeless body' line "
              "(aaze0058:10), after No the hook's 'Nothing here.'"},
    {'id': 'evt:pious_ask', 'preset': 'script', 'trigger': 'step', 'source': 'room:pious',
     'title': 'Pious the Cleric',
     'lua': cleric_ask('pious', QBITS['pious_spared'], QBITS['pious_slain'], G_PIOUS),
     'notes': "Coming into Pious's cell: as Humble's (aaze0059:6-10; pious_spared by A3's q-d6.pious, the map's "
              "pious_slain 117362)."},
    {'id': 'evt:pious_bed', 'preset': 'script', 'source': 'platform:bed_pious', 'title': 'Bed',
     'lua': cleric_bed('pious', QBITS['pious_spared'], QBITS['pious_slain'], G_PIOUS),
     'notes': "Pious's bed, as Humble's (aaze0059:10)."},
    # The fountains: once per character, the hooks decide (A3's player bits 11341-11344)
    fountain('fountain_water', 'q-d6.fountain_water', 'platform:fountain_water',
             "A3's q-d6.fountain_water: +5 Water resistance for the drinking member once (player bit 11343)."),
    fountain('fountain_body', 'q-d6.fountain_body', 'platform:fountain_body',
             "A3's q-d6.fountain_body: +5 Body resistance once per character (player bit 11344)."),
    fountain('fountain_fire', 'q-d6.fountain_fire', 'platform:fountain_fire',
             "A3's q-d6.fountain_fire: +5 Fire resistance once per character (player bit 11341)."),
    fountain('fountain_air', 'q-d6.fountain_air', 'platform:fountain_air',
             "A3's q-d6.fountain_air: +5 Air resistance once per character (player bit 11342)."),
    # L1: the alcoves (D-42 (5)) and the Pegasus
    {'id': 'evt:disc_w', 'preset': 'script', 'source': 'deco:disc_w', 'title': 'Disc',
     'condition': {'not': {'qbit': 'alcove_disks'}},
     'effects': [{'give_item': ITEMS['energy_disk']}, {'give_item': ITEMS['energy_disk']},
                 {'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")\n" + HIDE_DISCS}],
     'else_effects': [{'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")"}],
     'notes': "D-42 (5): the first disc alcove clicked runs q-d6.l1_alcoves, whose map_gives the map hands over "
              "(2 Energy Disks 12334); both discs go; then 'The alcove is empty.' ('Disc', aaze0057:4-5)."},
    {'id': 'evt:disc_e', 'preset': 'script', 'source': 'deco:disc_e', 'title': 'Disc',
     'condition': {'not': {'qbit': 'alcove_disks'}},
     'effects': [{'give_item': ITEMS['energy_disk']}, {'give_item': ITEMS['energy_disk']},
                 {'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")\n" + HIDE_DISCS}],
     'else_effects': [{'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")"}],
     'notes': "The east disc: as the west (one hook for both)."},
    {'id': 'evt:ledge_w', 'preset': 'script', 'source': 'platform:plinth_w', 'title': 'Alcove',
     'condition': {'not': {'qbit': 'alcove_disks'}},
     'effects': [{'give_item': ITEMS['energy_disk']}, {'give_item': ITEMS['energy_disk']},
                 {'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")\n" + HIDE_DISCS}],
     'else_effects': [{'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")"}],
     'notes': "The west alcove's ledge: as its disc."},
    {'id': 'evt:ledge_e', 'preset': 'script', 'source': 'platform:plinth_e', 'title': 'Alcove',
     'condition': {'not': {'qbit': 'alcove_disks'}},
     'effects': [{'give_item': ITEMS['energy_disk']}, {'give_item': ITEMS['energy_disk']},
                 {'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")\n" + HIDE_DISCS}],
     'else_effects': [{'lua': "XeenQuests.hook(\"q-d6.l1_alcoves\")"}],
     'notes': "The east alcove's ledge: as its disc."},
    text('mirror', 'panel:mirror', 'Mirror', "The mirror does not respond.",
         notes="The dead mirror (aaze0057:2): flavour only (D-26's rule, as DD-02's)."),
    text('window', 'panel:niche_water', 'Fountain', "The niche is cold to the touch.", window=False),
]
EVENTS = [e for e in EVENTS if e['id'] != 'evt:window']

WIRING = {'format': 0,
          'variables': ['bones_1', 'bones_2', 'bones_3', 'bed_l4_w', 'bed_l4_e', 'bed_l3', 'bed_l2_purse',
                        'bed_l1_a', 'bed_l1_b'],
          'events': EVENTS,
          'notes': "DD-05's events (gen.py): Q-D6's hooks (the key, the Cult Leader, Humble and Pious, the alcoves, the "
                   "front door, the four fountains), Q-D20's Pegasus, the tapestry button, the finds in the beds and "
                   "the bones, the dead mirror, the two exits to D1, the doors and chests."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

PROJECT = {
    'format': 0, 'id': 'xeen_dd05', 'name': 'Western Tower of Mok', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-05', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(7, 7), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 3,
        'perception_difficulty': 3, 'refill_days': 672, 'music': 34, 'environment': 'stoneroom',
        'lock_difficulty': 6,
        'slots': [{'monster': 'Xeen Heretic', 'tier': 0, 'per_marker': F(2, 3), 'weight': 75},
                  {'monster': 'Xeen Heretic', 'tier': 1, 'per_marker': F(1, 2), 'weight': 25}],
    },
    'neighbours': [
        {'id': 'exit:d1_rope', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': 'entrance:dd05_rope',
         'arrival_hint': "On D1 at the foot of the Western Tower's north wall, by the heretics' rope (A6's "
                         "entrance:dd05_rope, (-16896, 16896, 1600)).",
         'notes': "D1 installed (A6). D1's rope (door:dd05_rope, event 121, q-d6.tower_rope) lands at this map's "
                  "entrance:d1_rope in the hoist room: (1376, 1472, 1920) facing south."},
        {'id': 'exit:d1_door', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': 'entrance:dd05_door',
         'arrival_hint': "On D1 before the Western Tower's front door (A6's entrance:dd05_door, (-16896, 14848, "
                         "1600)).",
         'notes': "D1's front door (door:dd05_front, event 118: tower_opened or q-d6.front_door_outside) lands at "
                  "this map's entrance:d1_door in the door hall: (0, -1536, 0) facing north."}],
    'qbits': QBITS,
    'items': ITEMS,
    'notes': "Xeen design brief, DD-05 Western Tower of Mok (D1; Q-D6 The Heretics of Mok, Q-D20's Pegasus), class "
             "M, built from the MU-6 graph (devdocs/xeen/mockups/act4_graphs/dd05.graph.yml) with decider D-42 "
             "(mockups/act4_a8_decisions.md), which wins. Party 35-39, band 25-45, 45 placed monsters: heretics "
             "11220 Mok Heretic 25 (22), 11221 Heretic Priest 35 (11), 11222 Heretic Lord 45 (3), the Cult Leader "
             "11223 (45, hp x3); Mok's golems 11581 Stone Golem 26 (5), 11582 Iron Golem 40 (3); Humble 11910 and "
             "Pious 11911 peaceful, placed, not counted. Kill XP 57,155 for the party, 14.29k per member. Rest "
             "encounters 10 % from the heretics only (D-42). Treasure 4 (the vestry's hoard 5), music 34. Q-D6's "
             "bits 113120-113128 through A3's hooks; the map's arrived_once 117360, humble_slain 117361, "
             "pious_slain 117362 (provisional block 117360-117399). Player bits 11341-11344 (the fountains) are "
             "A3's, set by the hooks. Map card 9154.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Plan (L1 words; L2 adds extents, floors and heights)

TOWER_T = "MM8 Castle of Air (d27): green-grey ashlar gston1wl over gstntilev, gston1fl flags, gstn1cl ceilings"
STAIR_T = "d27's ashlar, grey cobbles gcstflor"
TEMPLE_T = "MM8 Temple of the Sun (d22): pale marble gtempw1, gtempflr, the gold-blue mosaic gtemprf"


def placed(actor, count, level, notes=None):
    d = {'actor': actor, 'groups': 1, 'per_marker': F(count, count), 'levels': F(level, level), 'placed': True}
    if notes:
        d['notes'] = notes
    return d


def room_box(i):
    for r in ROOMS:
        if r['id'] == 'room:' + i:
            xs = [p[0] for p in r['outline']]
            ys = [p[1] for p in r['outline']]
            f0 = r['floor']
            f1 = r['slope']['to'] if 'slope' in r else f0
            return (max(xs) - min(xs), max(ys) - min(ys)), (f0 if f0 == f1 else F(f0, f1)), r['ceiling'] - max(f0, f1)
    raise KeyError(i)


def sp(i, name, kind, size, purpose, theme, pop=None, treasure=None, **kw):
    ext, floor, clear = room_box(i)
    d = {'id': 'room:' + i, 'name': name, 'kind': kind, 'size': size, 'extent': F(*ext), 'floor': floor,
         'clear_height': clear, 'purpose': purpose, 'theme': theme}
    if pop:
        d['population'] = pop
    if treasure:
        d['treasure'] = treasure
    d.update(kw)
    return d


def chest(tier, notes):
    return [{'kind': 'chest', 'count': 1, 'tier': tier, 'items': F(2, 3), 'notes': notes}]


MH, HP, HL, CL, SG, IG = ('Mok Heretic (11220)', 'Heretic Priest (11221)', 'Heretic Lord (11222)',
                          'Cult Leader (11223)', 'Stone Golem (11581)', 'Iron Golem (11582)')
SPACES = [
    # L4
    sp('hoist', 'Hoist room', 'room', 'S', "Arrival from D1's rope and the way back down it: the open window, the "
       "windlass, the heretics' bread and candles (a storeroom). Quiet.", TOWER_T, safe=True, empty=True),
    sp('bone_gallery', 'Bone gallery', 'corridor', 'M', "The gallery to the chapel's double doors and the cells; "
       "three heaps of bones ('Bones', a find each).", TOWER_T, [placed(MH, 2, 25), placed(HP, 1, 35)]),
    sp('chapel', "The heretics' altar", 'room', 'L', "The set piece: pale marble under the cone's mosaic, Mok's "
       "daubed sun behind the altar. The Cult Leader preaches (q-d6.cult_leader on his death); on the altar the key "
       "(q-d6.tower_key).", TEMPLE_T, [placed(CL, 1, 45, "the boss"), placed(HL, 2, 45), placed(HP, 2, 35)]),
    sp('vestry', 'Vestry', 'room', 'S', "Behind the altar: the Cult Leader's chest (the hoard).", TEMPLE_T,
       treasure=chest(5, "The Cult Leader's chest."), empty=True),
    sp('tapestry_walk', 'Tapestry walk', 'corridor', 'S', "Three hangings of Mok's sun (xmoktap); behind the middle "
       "one a button slides the panel into the vestry.", TOWER_T, empty=True),
    sp('cells', "Heretics' cells", 'room', 'M', "Beds with something under the blanket; the tower stair's head.",
       STAIR_T, [placed(HP, 2, 35)]),
    sp('altar_stair', 'Altar stair', 'corridor', 'S', "From beside the altar down to L3's cloister.", STAIR_T,
       empty=True),
    sp('tower_stair', 'Tower stair', 'corridor', 'S', "From the cells down to L3's stair landing.", STAIR_T,
       empty=True),
    # L3
    sp('landing3', 'Stair landing', 'room', 'S', "The tower stair's foot and the outer stair's head; open to the "
       "dormitory.", STAIR_T, [placed(MH, 2, 25)]),
    sp('dorm3', 'Upper dormitory', 'room', 'M', "Beds ('Bed', one find), the senior priest's chest.", STAIR_T,
       [placed(HP, 2, 35), placed(MH, 1, 25)], chest(4, "The senior priest's chest.")),
    sp('fountains3', 'Fountains of cold and venom', 'room', 'M', "Two wall fountains: +5 Water, +5 Body resistance "
       "once per character (q-d6.fountain_water, fountain_body).", TOWER_T, [placed(HP, 2, 35), placed(MH, 1, 25)]),
    sp('cloister3', 'Cloister', 'corridor', 'M', "A long walk on the south side, windows at its ends.", TOWER_T,
       [placed(HP, 2, 35), placed(MH, 2, 25)]),
    sp('pious', "Pious's cell", 'room', 'S', "Behind a door: Pious the Cleric begs; 'Slay him anyway?' No: "
       "q-d6.pious, he is gone; Yes: the source's kill line; the bed's line after.", STAIR_T, empty=True),
    sp('west_stair3', 'West stair', 'corridor', 'S', "From the dormitory down to L2's landing.", STAIR_T, empty=True),
    sp('outer_stair3', 'Outer stair', 'corridor', 'S', "From the stair landing down to L2's kitchen.", STAIR_T,
       empty=True),
    # L2
    sp('landing2', 'Landing', 'room', 'S', "The foot of the west stair.", STAIR_T, empty=True),
    sp('kitchen2', 'Kitchen', 'room', 'S', "A hearth, a table, barrels and sacks (a store), a chest.", STAIR_T,
       [placed(MH, 2, 25)], chest(4, "The larder corner's chest.")),
    sp('refectory', 'Refectory', 'room', 'M', "One long table and its benches, beside the walking lines.", TOWER_T,
       [placed(MH, 4, 25)]),
    sp('fountains2', 'Fountains of fire and lightning', 'room', 'M', "Two wall fountains: +5 Fire, +5 Air resistance "
       "once per character (q-d6.fountain_fire, fountain_air); two stone guardians.", TOWER_T, [placed(SG, 2, 26)]),
    sp('dorm2', 'Lower dormitory', 'room', 'M', "Beds; under one mattress a purse.", STAIR_T, [placed(MH, 2, 25)]),
    sp('humble', "Humble's cell", 'room', 'S', "Behind a door: Humble the Cleric's plea and question as Pious's "
       "(q-d6.humble).", STAIR_T, empty=True),
    sp('east_stair2', 'East stair', 'corridor', 'S', "From the dormitory down to L1's stair hall.", STAIR_T,
       empty=True),
    sp('south_stair2', 'South stair', 'corridor', 'S', "From the fountain room down to L1's novices' dormitory.",
       STAIR_T, empty=True),
    # L1
    sp('stair_hall1', 'Stair hall', 'room', 'M', "The foot of the east stair.", STAIR_T, [placed(MH, 2, 25)]),
    sp('alcoves', 'Hall of alcoves', 'room', 'M', "Round the old stair core three alcoves: the first disc clicked "
       "gives both Energy Disks (q-d6.l1_alcoves), the north one the Pegasus (q-d20.pegasus).", TOWER_T,
       [placed(MH, 2, 25)]),
    sp('dorm1', "Novices' dormitory", 'room', 'M', "The foot of the south stair; beds ('Bed', two finds).", STAIR_T,
       [placed(MH, 2, 25)]),
    sp('mirror_hall', 'Mirror hall', 'room', 'S', "The dead mirror ('The mirror does not respond.').", TOWER_T,
       empty=True),
    sp('door_hall', 'Hall of the warded door', 'room', 'M', "The front door (q-d6.front_door with the key; then the "
       "exit to D1); a Heretic Lord and three iron guardians.", TOWER_T, [placed(HL, 1, 45), placed(IG, 3, 40)]),
    sp('guardians', "Guardians' gallery", 'room', 'S', "Three stone guardians; the old temple's offering chest.",
       TOWER_T, [placed(SG, 3, 26)], chest(4, "The offering chest.")),
]
for s in SPACES:
    if s.get('empty') and 'population' in s:
        del s['empty']


def link(i, a, b, kind, **kw):
    d = {'id': 'link:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
    d.update(kw)
    return d


LINKS = [
    link('hoist_gallery', 'hoist', 'bone_gallery', 'door', motion='swing'),
    link('gallery_chapel', 'bone_gallery', 'chapel', 'door', motion='swing', notes="Double doors."),
    link('gallery_cells', 'bone_gallery', 'cells', 'open'),
    link('cells_tap', 'cells', 'tapestry_walk', 'open'),
    link('tap_vestry', 'tapestry_walk', 'vestry', 'secret_door', notes="The button behind the middle tapestry."),
    link('chapel_vestry', 'chapel', 'vestry', 'door', motion='swing'),
    link('altar_stair', 'cloister3', 'chapel', 'stairs', rise=640, notes="The altar stair (altar_stair)."),
    link('tower_stair', 'landing3', 'cells', 'stairs', rise=640, notes="The tower stair (tower_stair)."),
    link('cloister_pious', 'cloister3', 'pious', 'door', motion='swing'),
    link('cloister_fountains', 'cloister3', 'fountains3', 'open'),
    link('fountains_dorm3', 'fountains3', 'dorm3', 'door', motion='swing'),
    link('dorm3_landing', 'dorm3', 'landing3', 'open'),
    link('west_stair', 'landing2', 'dorm3', 'stairs', rise=640, notes="The west stair (west_stair3)."),
    link('outer_stair', 'kitchen2', 'landing3', 'stairs', rise=640, notes="The outer stair (outer_stair3)."),
    link('landing_refectory', 'landing2', 'refectory', 'open'),
    link('kitchen_refectory', 'kitchen2', 'refectory', 'door', motion='swing'),
    link('refectory_fountains', 'refectory', 'fountains2', 'door', motion='swing'),
    link('fountains_dorm2', 'fountains2', 'dorm2', 'open'),
    link('dorm2_humble', 'dorm2', 'humble', 'door', motion='swing'),
    link('east_stair', 'stair_hall1', 'dorm2', 'stairs', rise=640, notes="The east stair (east_stair2)."),
    link('south_stair', 'dorm1', 'fountains2', 'stairs', rise=640, notes="The south stair (south_stair2)."),
    link('stair_alcoves', 'stair_hall1', 'alcoves', 'open'),
    link('alcoves_dorm1', 'alcoves', 'dorm1', 'open'),
    link('alcoves_mirror', 'alcoves', 'mirror_hall', 'open'),
    link('dorm1_door_hall', 'dorm1', 'door_hall', 'door', motion='swing'),
    link('mirror_door_hall', 'mirror_hall', 'door_hall', 'door', motion='swing'),
    link('door_hall_guardians', 'door_hall', 'guardians', 'door', motion='swing'),
]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "Heretics in Mok's priesthood threw Dreyfus out of his Western Tower and warded its door. They still "
                 "haul their bread up a rope to a window near the top, so the party climbs in at the top and fights "
                 "down four floors: the heretics' chapel and its Cult Leader with the key, the floors of the two "
                 "penitent clerics Pious and Humble, fountains that toughen the skin, and on the ground floor the "
                 "alcoves with two Energy Disks and Luna's Pegasus, Mok's iron guardians at the warded door, and the "
                 "door itself opened from inside.",
        'purpose': "Q-D6 The Heretics of Mok (D1, Dreyfus): the Cult Leader, the key, the front door; Humble and Pious "
                   "spared or not; M18's two Energy Disks; Q-D20's Pegasus statuette. Party 35-39; band 25-45; 45 "
                   "monsters; treasure 4, the vestry 5. About 30 minutes.",
        'mood': "A cold green-grey tower of the Mok order, lamplit; the heretics' pale chapel under the cone; wind at "
                "the rope window.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'loops': [
            {'id': 'loop:top', 'spaces': ['room:bone_gallery', 'room:chapel', 'room:vestry', 'room:tapestry_walk',
                                          'room:cells'],
             'notes': "Round the top floor once the tapestry's panel is open."},
            {'id': 'loop:l4_l3', 'spaces': ['room:chapel', 'room:altar_stair', 'room:cloister3', 'room:fountains3',
                                            'room:dorm3', 'room:landing3', 'room:tower_stair', 'room:cells',
                                            'room:bone_gallery'],
             'notes': "The two stairs between L4 and L3."},
            {'id': 'loop:l3_l2', 'spaces': ['room:dorm3', 'room:west_stair3', 'room:landing2', 'room:refectory',
                                            'room:kitchen2', 'room:outer_stair3', 'room:landing3'],
             'notes': "The two stairs between L3 and L2."},
            {'id': 'loop:l2_l1', 'spaces': ['room:fountains2', 'room:dorm2', 'room:east_stair2', 'room:stair_hall1',
                                            'room:alcoves', 'room:dorm1', 'room:south_stair2'],
             'notes': "The two stairs between L2 and L1."},
            {'id': 'loop:ground', 'spaces': ['room:alcoves', 'room:dorm1', 'room:door_hall', 'room:mirror_hall'],
             'notes': "Two ways from the alcoves to the warded door."}],
        'entrances': [
            {'id': 'entrance:d1_rope', 'space': 'room:hoist', 'kind': 'both', 'neighbour': 'exit:d1_rope',
             'facing': 's', 'how': "D1's rope (q-d6.tower_rope): a step inside the hoist room's window; out by the "
                                   "window (the exit preset)."},
            {'id': 'entrance:d1_door', 'space': 'room:door_hall', 'kind': 'both', 'neighbour': 'exit:d1_door',
             'facing': 'n', 'how': "D1's front door once tower_opened; out by it after q-d6.front_door."}],
        'critical_path': ['room:hoist', 'room:bone_gallery', 'room:chapel', 'room:altar_stair', 'room:cloister3',
                          'room:fountains3', 'room:dorm3', 'room:west_stair3', 'room:landing2', 'room:refectory',
                          'room:fountains2', 'room:dorm2', 'room:east_stair2', 'room:stair_hall1', 'room:alcoves',
                          'room:dorm1', 'room:door_hall'],
        'return_path': ['room:door_hall'],
        'goals': [
            {'id': 'goal:leader', 'space': 'room:chapel', 'kind': 'kill',
             'what': "The Cult Leader (q-d6.cult_leader) and the key on the altar (q-d6.tower_key)."},
            {'id': 'goal:door', 'space': 'room:door_hall', 'kind': 'set',
             'what': "The front door opened from inside with the key (q-d6.front_door, tower_opened)."},
            {'id': 'goal:disks', 'space': 'room:alcoves', 'kind': 'take',
             'what': "Two Energy Disks (q-d6.l1_alcoves) and the Golden Pegasus (q-d20.pegasus)."}],
        'atmosphere': "Lamplit green-grey stone (ambient 14-18), the chapel bright (22). Music 34. Sounds: the tower's "
                      "chimes bed, wind at the rope window, water in the fountain rooms, the hearth.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': 4, 'doors': 12, 'fixed_actors': 47, 'loops': 5, 'monsters_about': 45,
                   'rooms': len(ROOMS), 'sectors': len(ROOMS), 'spawn_points': 0, 'floor_area_millions': 30},
        'notes': "Class M (MAPS, Dungeons): 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors. "
                 "The graph's 29 review spaces as 29 rooms; the six stairs are rooms of their own (flights of 20 "
                 "steps). D-42: 45 monsters with Mok's golems, the Cult Leader's own row, Humble and Pious named "
                 "peaceful rows in cells, the discs (a), the inside larger than the outside.",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    elif level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return d


DIAGRAM = """ L4 (1920)  [Hoist room: D1 rope window]--door--[Bone gallery: bones]==double doors==[CHAPEL: Cult Leader, key]
                                              |               \\                      |door      |altar stair
                                        [Heretics' cells]--[Tapestry walk: 3 tapestries]##[Vestry $$]
                                              |tower stair
 L3 (1280)  [Stair landing]--[Upper dormitory $]==door==[Fountains: Water, Body]--[Cloister]==door==[Pious]
                 |outer stair        |west stair                                      |(altar stair foot)
 L2 (640)   [Kitchen $]==door==[Refectory]--[Landing]
                               |door
                       [Fountains: Fire, Air; golems]--[Lower dormitory]==door==[Humble]
                               |south stair                 |east stair
 L1 (0)     [Novices' dormitory]--[Hall of alcoves: 2 discs, Pegasus]--[Stair hall]
                  |door                  |
            [Hall of the warded door: front door to D1]==door==[Mirror hall]
                  |door
            [Guardians' gallery $]

 $ chest   == door   ## secret panel behind the middle tapestry   -- open
"""


def write(level):
    d = OUT + '/' + level
    os.makedirs(d, exist_ok=True)
    dump(d + '/project.yml', PROJECT)
    dump(d + '/plan.yml', plan(level))
    open(d + '/diagram.txt', 'w').write(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(d + '/rooms.yml', {'format': 0, 'themes': THEMES, 'defaults': {'theme': 'theme:tower', 'ambient': 16},
                                'rooms': ROOMS, 'openings': OPENINGS,
                                'notes': "DD-05 at L3/L4: 29 rooms on four floors in the plan's frame (x east, y "
                                         "north). Written by output/studio_cal/dd05/tools/gen.py."})
    if level == 'L4':
        dump(d + '/objects.yml', OBJECTS)
        dump(d + '/wiring.yml', WIRING)


if __name__ == '__main__':
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
