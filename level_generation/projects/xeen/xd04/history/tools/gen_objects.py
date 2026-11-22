# XD-04 Witch Tower, L4: objects.yml and wiring.yml (first written by this script; numbers are design numbers).
# Run: python3 gen_objects.py <L4 folder>. Once the project has hand edits the files are the source.
import sys
import yaml

L4 = sys.argv[1]


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


BOARDS = S('7trimd', 128, 256)
WAINSCOT = S('hwm1b', 128, 256)
BOOKS = S('7t1books', 128, 256)
DARKWOOD = S('trim11_32', 32, 64)
LIGHTWOOD = S('trim9_32', 32, 64)
TDOOR = S('twb1', 128, 256)
WARD = S('tws1a', 128, 256)
CAB = S('7t1cab', 128, 256)
FRONT_DOOR = S('hwm2d', 128, 256)
SKY = S('sky_clo1', 512, 512)
SEAL = [[{'texture': 't1d1a', 'size': [256, 256]}, {'texture': 't1d1b', 'size': [256, 256]}],
        [{'texture': 't1d1c', 'size': [256, 256]}, {'texture': 't1d1d', 'size': [256, 256]}]]

WARM = [255, 170, 90]
CANDLE = [255, 200, 130]
GREEN = [90, 255, 110]
GREENFLAME = [120, 255, 120]
WHITE = [235, 245, 255]
VIOLET = [170, 90, 255]
DAY = [200, 215, 255]

o = {'format': 0}
o['start'] = {'room': 'room:gate_hall', 'at': [0, -2900], 'facing': 90,
              'notes': "Inside the tower door, facing into the gate hall and the gallery beyond."}

# ---------------------------------------------------------------------------------------------------- doors
def plank_door(i, opening, note):
    return {'id': i, 'opening': opening, 'kind': 'slide_left', 'leaves': 2, 'fold': True, 'tile': True, 'surface': BOARDS,
            'notes': note}


o['doors'] = [
    plank_door('door:warden', 'open:ring_warden_lodge', "Gallery to the warden's lodge: two plank leaves that fold "
               "into the jambs, as Clanker's Laboratory's doors do."),
    plank_door('door:larder', 'open:ring_toad_larder', 'Gallery to the toad larder.'),
    plank_door('door:pens', 'open:ring_goblin_pens', 'Gallery to the goblin pens.'),
    plank_door('door:dormitory', 'open:landing_f2_dormitory', 'Landing to the dormitory.'),
    plank_door('door:mistress', 'open:dormitory_schoolroom', "The mistress's door, dormitory to schoolroom."),
    plank_door('door:schoolroom', 'open:balcony_schoolroom', 'The double door from the balcony into the schoolroom.'),
    {'id': 'door:cupboard', 'opening': 'open:dormitory_cupboard', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'surface': WAINSCOT, 'secret': True,
     'notes': "The loose panel: a secret leaf in the wainscot's picture that slides up into the lintel."},
    {'id': 'door:bookcase', 'opening': 'open:vat_hall_hidden_cage', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'surface': BOOKS, 'secret': True,
     'notes': "The bookcase in the vat hall's west wall: a secret leaf of shelves that rises on a click."},
    {'id': 'door:bedchamber', 'opening': 'open:sanctum_bedchamber', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'surface': TDOOR, 'notes': "A stone slab that folds up into the lintel, as the Temple of the Moon's doors do."},
    {'id': 'door:rosebud', 'opening': 'open:rosebud_door', 'kind': 'slide_left', 'leaves': 2, 'fold': True, 'tile': True,
     'pictures': SEAL,
     'notes': "The Rosebud door: the Temple of the Moon's seal door (four quarters of the Moon seal on two leaves that "
              "part sideways), standing for the brief's carved sleeping face."},
    {'id': 'door:ward', 'opening': 'open:sanctum_roof_stair', 'kind': 'slide_down', 'fold': True, 'tile': True, 'surface': WARD,
     'notes': "The coven's ward across the roof stair: a carved sigil slab that sinks into the floor once the party "
              "are Crusaders (stand-in for a translucent shimmering leaf)."},
    {'id': 'door:hatch', 'opening': 'open:roof_stair_roof', 'kind': 'slide_up', 'fold': True, 'tile': True, 'surface': TDOOR,
     'notes': 'The roof hatch at the head of the stair.'},
    {'id': 'door:gate_top', 'opening': 'open:hoist_room_slot', 'kind': 'slide_up', 'fold': True, 'tile': True, 'surface': BOARDS,
     'state': 'open', 'notes': "The hoist gate across the hoist room's door to the slot: shut whenever the cage is "
                               "down (a 1920 drop otherwise)."},
    {'id': 'door:gate_bottom', 'opening': 'open:hoist_slot_cauldron', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'surface': BOARDS, 'notes': "The lower hoist gate (L4): shut whenever the cage is up, so nobody stands under "
                                 "it when it comes down."},
]

# ---------------------------------------------------------------------------------------------------- the hoist
HX, HY = -1312, -608
o['movers'] = [{
    'id': 'mover:hoist', 'room': 'room:hoist_slot', 'at': [HX, HY], 'size': [440, 440], 'bottom': -14, 'height': 16,
    'travel': [0, 0, 1920], 'speed': 192, 'state': 'end', 'surface': DARKWOOD, 'top_surface': BOARDS,
    'parts': [
        {'at': [HX - 212, HY - 212], 'size': [16, 16], 'height': 320, 'surface': DARKWOOD, 'notes': 'Cage post'},
        {'at': [HX + 212, HY - 212], 'size': [16, 16], 'height': 320, 'surface': DARKWOOD, 'notes': 'Cage post'},
        {'at': [HX + 212, HY + 212], 'size': [16, 16], 'height': 320, 'surface': DARKWOOD, 'notes': 'Cage post'},
        {'at': [HX - 212, HY + 212], 'size': [16, 16], 'height': 320, 'surface': DARKWOOD, 'notes': 'Cage post'},
        {'at': [HX, HY - 212], 'size': [440, 16], 'bottom': 336, 'height': 16, 'surface': DARKWOOD},
        {'at': [HX, HY + 212], 'size': [440, 16], 'bottom': 336, 'height': 16, 'surface': DARKWOOD},
        {'at': [HX - 212, HY], 'size': [16, 408], 'bottom': 336, 'height': 16, 'surface': DARKWOOD},
        {'at': [HX + 212, HY], 'size': [16, 408], 'bottom': 336, 'height': 16, 'surface': DARKWOOD},
        {'at': [HX, HY], 'size': [8, 408], 'bottom': 336, 'height': 16, 'surface': DARKWOOD, 'notes': 'Hanger bar'},
        {'at': [HX, HY], 'size': [8, 8], 'bottom': 352, 'height': 1900, 'surface': DARKWOOD,
         'notes': 'The hoist rope, up into the winch'},
    ],
    'notes': "The witches' ingredient hoist: a plank cage that fills the slot, standing at the top (1920) when the "
             "map is first entered; the brake lever sends it down, then it is ridden and called from either end."}]

# ---------------------------------------------------------------------------------------------------- lights
def L(i, room, at, h, r, c, **kw):
    d = {'id': i, 'room': room, 'at': at, 'height': h, 'radius': r, 'color': c}
    d.update(kw)
    return d


o['lights'] = [
    # cauldron chamber and shaft
    L('light:brew', 'room:cauldron_chamber', [0, 0], 220, 1200, GREEN,
      pulse={'intensity': [0.7, 1], 'frequency': 0.3}, notes='The brew, from inside the cauldron.'),
    L('light:shaft_mid', 'room:cauldron_chamber', [0, 0], 1280, 1300, GREEN,
      pulse={'intensity': [0.5, 0.9], 'frequency': 0.2, 'phase': 0.3}, notes='Green steam halfway up the shaft.'),
    L('light:shaft_top', 'room:cauldron_chamber', [300, 300], 2400, 1000, [110, 200, 120],
      notes='Steam under the roof beams.'),
    L('light:glow_n', 'room:cauldron_chamber', [0, 700], 260, 900, GREEN, notes='Brew-light on the walls.'),
    L('light:glow_s', 'room:cauldron_chamber', [0, -700], 260, 900, GREEN),
    L('light:glow_e', 'room:cauldron_chamber', [700, 0], 260, 900, GREEN),
    L('light:glow_w', 'room:cauldron_chamber', [-500, 500], 260, 900, GREEN),
    L('light:steam_low', 'room:cauldron_chamber', [-300, 300], 800, 1100, [110, 220, 120]),
    L('light:alacorn', 'room:cauldron_chamber', [-96, -128], 2060, 1600, WHITE,
      notes="The Alacorn's own white light, seen from the cauldron floor."),
    L('light:boil', 'room:cauldron_chamber', [0, 0], 1600, 1800, [140, 255, 120], on=False,
      pulse={'intensity': [0.6, 1], 'frequency': 1.2}, notes='The boil-over: the shaft fills with green light.'),
    L('light:boil_pier', 'room:shaft_bridge', [-864, -128], 200, 700, [140, 255, 120], on=False,
      pulse={'intensity': [0.6, 1], 'frequency': 1.5}),
    # ground floor
    L('light:gate', 'room:gate_hall', [0, -2900], 300, 800, WARM),
    L('light:gate_n', 'room:gate_hall', [0, -2000], 300, 700, WARM),
    L('light:gallery_w', 'room:ring_f1', [-1100, -1300], 300, 800, WARM),
    L('light:gallery_e', 'room:ring_f1', [1000, -1300], 300, 800, WARM),
    L('light:lodge', 'room:warden_lodge', [-2100, -1500], 260, 700, WARM),
    L('light:larder', 'room:toad_larder', [-1120, -1800], 260, 600, [200, 220, 150]),
    L('light:pens', 'room:goblin_pens', [1600, -1800], 260, 900, WARM),
    L('light:hoist_foot', 'room:hoist_slot', [HX, HY], 220, 500, WARM, floor_height=0),
    L('light:stair_turn_1', 'room:stair_1_2_mid', [2560, -1312], 260, 600, WARM),
    # second floor
    L('light:balcony_s', 'room:balcony_f2', [1312, -500], 300, 700, CANDLE),
    L('light:balcony_n', 'room:balcony_f2', [1312, 1000], 300, 700, CANDLE),
    L('light:landing_f2', 'room:landing_f2', [2200, 0], 260, 600, CANDLE),
    L('light:dormitory', 'room:dormitory', [3500, 400], 260, 700, CANDLE),
    L('light:school_desk', 'room:schoolroom', [3104, 1728], 260, 800, CANDLE),
    L('light:school_door', 'room:schoolroom', [1800, 1300], 300, 600, CANDLE),
    L('light:skulls', 'room:skull_niche', [2150, 576], 260, 450, [255, 180, 110],
      pulse={'intensity': [0.7, 1], 'frequency': 0.8}, notes='Three candles by the skulls.'),
    L('light:stair_turn_2', 'room:stair_2_3_mid', [1312, 2528], 260, 600, WARM),
    # third floor
    L('light:vat_1', 'room:vat_hall', [-2048, 2880], 120, 600, [255, 140, 60],
      pulse={'intensity': [0.75, 1], 'frequency': 1.1}),
    L('light:vat_2', 'room:vat_hall', [-1536, 2880], 120, 600, [255, 140, 60],
      pulse={'intensity': [0.75, 1], 'frequency': 1.1, 'phase': 0.33}),
    L('light:vat_3', 'room:vat_hall', [-1024, 2880], 120, 600, [255, 140, 60],
      pulse={'intensity': [0.75, 1], 'frequency': 1.1, 'phase': 0.66}),
    L('light:vat_hall_e', 'room:vat_hall', [-700, 2300], 360, 700, WARM),
    L('light:landing_f3', 'room:landing_f3', [-32, 2560], 300, 600, WARM),
    L('light:loft', 'room:herb_loft', [544, 1888], 240, 600, WARM),
    L('light:hidden_cage', 'room:hidden_cage', [-2944, 2250], 120, 400, CANDLE),
    # fourth floor
    L('light:rosebud', 'room:rosebud_landing', [-3072, 1250], 280, 600, GREENFLAME),
    L('light:circle', 'room:coven_sanctum', [-2560, 288], 200, 900, VIOLET,
      pulse={'intensity': [0.5, 1], 'frequency': 0.25}, notes='Dim violet over the witch-mark circle.'),
    L('light:sanctum_w', 'room:coven_sanctum', [-3700, 288], 320, 800, CANDLE),
    L('light:pier_n', 'room:coven_sanctum', [-1200, 650], 280, 700, GREENFLAME),
    L('light:pier_s', 'room:coven_sanctum', [-1200, -150], 280, 700, GREENFLAME),
    L('light:bedchamber', 'room:witch_bedchamber', [-3300, -600], 300, 800, CANDLE),
    L('light:hoist_room', 'room:hoist_room', [-1750, -650], 300, 700, WARM),
    L('light:hoist_top', 'room:hoist_slot', [HX, HY], 2120, 500, WARM, floor_height=0),
    L('light:roof', 'room:roof', [-6400, 448], 600, 2600, DAY, notes='Daylight under the open sky.'),
]

# ---------------------------------------------------------------------------------------------------- switches
o['switches'] = [
    {'id': 'switch:brake', 'room': 'room:hoist_room', 'kind': 'lever', 'wall': 'north', 'along': 0.12,
     'base': DARKWOOD, 'off': S('trim9_32', 32, 64),
     'notes': "The hoist's brake lever on the hoist room's north wall."},
    {'id': 'switch:call_top', 'room': 'room:hoist_room', 'kind': 'button', 'wall': 'east', 'along': 0.12,
     'height': 112, 'notes': 'Call button beside the upper hoist gate.'},
    {'id': 'switch:call_bottom', 'room': 'room:cauldron_chamber', 'kind': 'button', 'at': [-960, -704],
     'height': 112, 'notes': 'Call button beside the lower hoist gate.'},
]

# ---------------------------------------------------------------------------------------------------- chests
o['chests'] = [
    {'id': 'chest:warden', 'room': 'room:warden_lodge', 'kind': '7gt002', 'at': [-1760, -1760], 'treasure_level': 2, 'random_items': 2, 'gold': 120, 'items': [177, 222],
     'notes': "The warden's strongbox: a zircon, a healing potion, 120 gold and two rolls."},
    {'id': 'chest:loft', 'room': 'room:herb_loft', 'kind': '7gt002', 'at': [900, 2100], 'treasure_level': 2, 'random_items': 2, 'items': [226, 224, 178],
     'notes': "The witches' stores: cure poison, cure weakness, an iolite and two rolls."},
    {'id': 'chest:coven', 'room': 'room:witch_bedchamber', 'at': [-2700, -900], 'facing': 'w', 'size': [128, 24, 256],
     'surface': CAB, 'treasure_level': 3, 'random_items': 3, 'gold': 300, 'items': [181, 179],
     'notes': "The coven's chest: a carved cabinet against the wall (the Temple of the Moon's cabinets): 300 gold, "
              "an amethyst, a citrine and three rolls."},
    {'id': 'chest:hoard', 'room': 'room:cupboard', 'at': [4720, 416], 'facing': 'n', 'size': [128, 16, 256],
     'surface': CAB, 'treasure_level': 1, 'random_items': 1, 'gold': 40, 'items': [180],
     'notes': "The goblin's hoard in the cupboard: an amber, 40 gold and one low roll."},
]

# ---------------------------------------------------------------------------------------------------- spawns
def SP(i, room, at, slot, tier, note=None, **kw):
    d = {'id': i, 'room': room, 'at': at, 'slot': slot, 'tier': tier}
    if note:
        d['notes'] = note
    d.update(kw)
    return d


o['spawns'] = [
    SP('spawn:gallery_w', 'room:ring_f1', [-1200, -1312], 1, 'a', 'The first goblins, at the west end.'),
    SP('spawn:pens_1', 'room:goblin_pens', [1050, -2300], 1, 'a', 'The densest goblin fight on the ground floor.'),
    SP('spawn:pens_2', 'room:goblin_pens', [2150, -1800], 1, 'a'),
    SP('spawn:larder_1', 'room:toad_larder', [-1400, -2600], 3, 'c', 'Familiars in the larder.'),
    SP('spawn:larder_2', 'room:toad_larder', [-850, -1750], 3, 'c'),
    SP('spawn:lodge', 'room:warden_lodge', [-1900, -1250], 1, 'a', "The warden's helpers."),
    SP('spawn:stokers_1', 'room:cauldron_chamber', [650, -350], 1, 'a', 'Stokers at the cauldron.'),
    SP('spawn:stokers_2', 'room:cauldron_chamber', [-300, 700], 1, 'a', 'Stokers at the cauldron.'),
    SP('spawn:steam', 'room:cauldron_chamber', [550, 550], 3, 'c', 'Familiars in the steam.'),
    SP('spawn:balcony', 'room:balcony_f2', [1312, 1250], 1, 'b', 'Hobgoblins at the north end, away from the landing.'),
    SP('spawn:dorm_1', 'room:dormitory', [3264, 448], 1, 'a', 'Turned children asleep.'),
    SP('spawn:dorm_2', 'room:dormitory', [3776, 448], 1, 'a'),
    SP('spawn:pupils', 'room:schoolroom', [2000, 2250], 1, 'a', "The 'pupils' who have already turned."),
    SP('spawn:broken_balcony', 'room:broken_balcony', [-1000, 1312], 1, 'a'),
    SP('spawn:vat_witch_1', 'room:vat_hall', [-2100, 2300], 2, 'a', 'Brewing witches.'),
    SP('spawn:vat_witch_2', 'room:vat_hall', [-1100, 2000], 2, 'a'),
    SP('spawn:vat_familiars_1', 'room:vat_hall', [-1700, 2550], 3, 'c'),
    SP('spawn:vat_familiars_2', 'room:vat_hall', [-800, 2700], 3, 'c'),
    SP('spawn:hoist_crew', 'room:hoist_room', [-2250, -560], 1, 'b', 'The winch crew.'),
    SP('spawn:sanctum_guards', 'room:coven_sanctum', [-1700, 600], 1, 'c', 'Goblin Lords, the coven\'s guard.'),
    SP('spawn:bedchamber', 'room:witch_bedchamber', [-3300, -500], 3, 'c', 'A familiar on the bed.'),
    {'id': 'spawn:item_pens', 'room': 'room:goblin_pens', 'at': [2300, -2700], 'kind': 'item', 'treasure_level': 2,
     'notes': 'Something in the straw.'},
    {'id': 'spawn:item_larder', 'room': 'room:toad_larder', 'at': [-1450, -1700], 'kind': 'item',
     'treasure_level': 2},
    {'id': 'spawn:item_vat', 'room': 'room:vat_hall', 'at': [-2400, 2000], 'kind': 'item', 'treasure_level': 3},
]

# ---------------------------------------------------------------------------------------------------- monsters
o['monsters'] = [
    {'id': 'monster:warden', 'room': 'room:warden_lodge', 'monster': 273, 'at': [-2250, -1500], 'facing': 0,
     'hostile': True, 'group': 2, 'carries': 'warden_ring', 'name': 'Goblin Warden', 'immobile': True,
     'notes': "The Goblin Warden (a Goblin Lord, level 10) with the ring of keys that opens every cage."},
    {'id': 'monster:child_1', 'room': 'room:warden_lodge', 'monster': 439, 'at': [-2880, -1850], 'facing': 0,
     'hostile': False, 'group': 11, 'immobile': True,
     'notes': "Child 1, the half-turned boy, in cage 1 (a Goblin peasant: the children are half turned)."},
    {'id': 'monster:child_2', 'room': 'room:schoolroom', 'monster': 430, 'at': [2752, 2260], 'facing': 270,
     'hostile': False, 'group': 12, 'immobile': True, 'notes': "Child 2, who knows the word, in cage 2."},
    {'id': 'monster:child_3', 'room': 'room:hidden_cage', 'monster': 433, 'at': [-2944, 2420], 'facing': 0,
     'hostile': False, 'group': 13, 'immobile': True, 'notes': 'Child 3, hidden behind the bookcase.'},
    {'id': 'monster:child_4', 'room': 'room:witch_bedchamber', 'monster': 442, 'at': [-3950, -500], 'facing': 0,
     'hostile': False, 'group': 14, 'immobile': True, 'notes': "Child 4, in the witches' bedchamber."},
    {'id': 'monster:schoolmistress', 'room': 'room:schoolroom', 'monster': 214, 'at': [3200, 1728], 'facing': 180,
     'hostile': True, 'group': 3, 'name': 'Schoolmistress',
     'notes': "The schoolmistress at her desk (an Acolyte of the Moon, level 10)."},
    {'id': 'monster:head_witch', 'room': 'room:coven_sanctum', 'monster': 215, 'at': [-1500, 300], 'facing': 180,
     'hostile': True, 'group': 4, 'hp': 300, 'name': 'Head Witch',
     'notes': "The Head Witch (a Cleric of the Moon, level 20, with 300 hit points of her own) at the window over "
              "the shaft, between the Rosebud door and the bridge (set:head_witch)."},
    {'id': 'monster:sister_1', 'room': 'room:coven_sanctum', 'monster': 214, 'at': [-3500, -150], 'facing': 0,
     'hostile': True, 'group': 6, 'notes': "One of the Head Witch's two sisters (Acolytes of the Moon)."},
    {'id': 'monster:sister_2', 'room': 'room:coven_sanctum', 'monster': 214, 'at': [-3500, 750], 'facing': 0,
     'hostile': True, 'group': 6},
    {'id': 'monster:familiar_1', 'room': 'room:coven_sanctum', 'monster': 207, 'at': [-2560, 480], 'hostile': True,
     'group': 5, 'hidden': True, 'notes': "A familiar called up from the witch-marks (set:head_witch)."},
    {'id': 'monster:familiar_2', 'room': 'room:coven_sanctum', 'monster': 207, 'at': [-2560, 96], 'hostile': True,
     'group': 5, 'hidden': True},
]

o['items'] = [
    {'id': 'item:alacorn', 'room': 'room:cauldron_chamber', 'item': 'alacorn', 'at': [-96, -128],
     'floor_height': 1984, 'notes': "The Alacorn of Falista on its pedestal at the bridge's end (goal:alacorn)."},
]

# ---------------------------------------------------------------------------------------------------- decorations
D = []


def deco(i, room, name, at=None, **kw):
    d = {'id': i, 'room': room, 'decoration': name}
    if at:
        d['at'] = at
    d.update(kw)
    D.append(d)


# gate hall
deco('deco:gate_torch_w', 'room:gate_hall', 'torch07', wall='south', along=0.2, height=256)
deco('deco:gate_torch_e', 'room:gate_hall', 'torch07', wall='south', along=0.8, height=256)
deco('deco:gate_torch_west', 'room:gate_hall', 'torch07', at=[-640, -2800], wall='west', height=256)
deco('deco:gate_torch_east', 'room:gate_hall', 'torch07', at=[640, -2800], wall='east', height=256)
deco('deco:gate_cask', 'room:gate_hall', '7dec21', [520, -3100])
deco('deco:gate_sacks', 'room:gate_hall', 'bag01', [-540, -3100])
# gallery
for n, a in enumerate([0.12, 0.38, 0.62, 0.88]):
    deco(f'deco:gallery_torch_{n + 1}', 'room:ring_f1', 'torch01', wall='south', along=a, height=256)
deco('deco:gallery_cask', 'room:ring_f1', '7dec21', [1400, -1450])
deco('deco:gallery_cask_2', 'room:ring_f1', '7dec21', [-1450, -1180])
# cauldron chamber
for n, (x, y) in enumerate([(560, 0), (-480, 300), (0, -560), (0, 560)]):
    deco(f'deco:brazier_{n + 1}', 'room:cauldron_chamber', 'brzier00', [x, y])
for n, (x, y) in enumerate([(700, 400), (650, -650), (-350, -750), (-700, 700)]):
    deco(f'deco:stoking_pot_{n + 1}', 'room:cauldron_chamber', 'ckfyr00', [x, y])
deco('deco:sacks_1', 'room:cauldron_chamber', 'bag01', [850, -150])
deco('deco:sacks_2', 'room:cauldron_chamber', 'floursac', [800, 100])
deco('deco:cask_1', 'room:cauldron_chamber', '7dec21', [-250, -900])
deco('deco:bucket', 'room:cauldron_chamber', 'Bucket', [400, -820])
deco('deco:foodbowl', 'room:cauldron_chamber', 'foodbowl', [-820, 350])
for n, (x, y, h) in enumerate([(500, -300, 2420), (-300, 500, 2400), (350, 450, 2440)]):
    deco(f'deco:hanging_cage_{n + 1}', 'room:cauldron_chamber', f'7dec0{5 + n}', [x, y], height=h,
         notes='A hanging cage on its chain from the roof beams.')
# warden's lodge
deco('deco:cage_1', 'room:warden_lodge', 'bonecage', [-2880, -1850], notes='Cage 1: the half-turned boy.')
deco('deco:lodge_torch', 'room:warden_lodge', 'torch01', wall='north', along=0.5, height=256)
deco('deco:lodge_candle', 'room:warden_lodge', 'cndlab0', [-2000, -1600], notes='On the table.')
deco('deco:lodge_plates', 'room:warden_lodge', 'dec37', [-2100, -1600])
# larder
deco('deco:larder_torch', 'room:toad_larder', 'torch01', wall='west', along=0.5, height=256)
deco('deco:larder_cask', 'room:toad_larder', '7dec21', [-1450, -2800])
deco('deco:larder_bucket', 'room:toad_larder', 'Bucket', [-800, -2800])
deco('deco:larder_mushrooms_1', 'room:toad_larder', 'mushrm01', [-1450, -1950])
deco('deco:larder_mushrooms_2', 'room:toad_larder', 'mushrm03', [-800, -2050])
# pens
deco('deco:pens_torch_1', 'room:goblin_pens', 'torch01', wall='north', along=0.2, height=256)
deco('deco:pens_torch_2', 'room:goblin_pens', 'torch01', wall='north', along=0.8, height=256)
deco('deco:pens_trash_1', 'room:goblin_pens', 'trasheap', [900, -2780])
deco('deco:pens_trash_2', 'room:goblin_pens', '7dec01', [1500, -2800])
deco('deco:pens_bones', 'room:goblin_pens', '7dec18', [2000, -2780])
deco('deco:pens_bones_2', 'room:goblin_pens', 'dec29', [2350, -2200])
deco('deco:pens_sacks', 'room:goblin_pens', 'floursac', [2380, -1720])
deco('deco:pens_bowl', 'room:goblin_pens', 'foodbowl', [1000, -1900])
# stairs
deco('deco:stair_lantern_1', 'room:stair_1_2_mid', 'torch02', wall='south', along=0.5, height=256)
deco('deco:stair_lantern_2', 'room:stair_2_3_mid', 'torch02', wall='north', along=0.5, height=256)
# second floor
deco('deco:balcony_sconce_1', 'room:balcony_f2', 'scon100', wall='east', along=0.15, height=200)
deco('deco:balcony_sconce_2', 'room:balcony_f2', 'scon100', wall='east', along=0.8, height=200)
deco('deco:landing_sconce', 'room:landing_f2', 'scon100', wall='south', along=0.5, height=200)
deco('deco:dorm_sconce', 'room:dormitory', 'scon100', wall='west', along=0.25, height=200)
deco('deco:dorm_plates', 'room:dormitory', 'dec36', [3450, 400])
deco('deco:dorm_bucket', 'room:dormitory', 'Bucket', [3000, 900])
deco('deco:dorm_trash', 'room:dormitory', '7dec01', [4000, -50])
deco('deco:dorm_bowl', 'room:dormitory', 'foodbowl', [3200, 450])
deco('deco:cupboard_candle', 'room:cupboard', 'cndlab0', [4644, 360])
deco('deco:skull_1', 'room:skull_niche', '7dec20', [2272, 460], floor_height=752, notes='The skull of the Mind.')
deco('deco:skull_2', 'room:skull_niche', '7dec20', [2272, 576], floor_height=752, notes='The skull of the Body.')
deco('deco:skull_3', 'room:skull_niche', '7dec20', [2272, 692], floor_height=752, notes='The skull of the Air.')
for n, y in enumerate([418, 518, 634, 734]):
    deco(f'deco:skull_candle_{n + 1}', 'room:skull_niche', 'cndlab0', [2280, y], floor_height=752)
deco('deco:cage_2', 'room:schoolroom', 'bonecage', [2752, 2260], notes='Cage 2: the girl who knows the word.')
deco('deco:desk_candle_1', 'room:schoolroom', 'dec02', [3104, 1500])
deco('deco:desk_candle_2', 'room:schoolroom', 'dec02', [3104, 1960])
deco('deco:school_sconce', 'room:schoolroom', 'scon100', wall='west', along=0.15, height=200)
# third floor
deco('deco:vat_toad', 'room:vat_hall', 'bigbarel', [-2048, 2880], notes="The vat with the toad on its lid.")
deco('deco:vat_bubbling', 'room:vat_hall', 'cauld00', [-1536, 2880], notes='The bubbling vat (Agnes).')
deco('deco:vat_green', 'room:vat_hall', '7dec32', [-1024, 2880], notes='The green vat.')
for n, x in enumerate([-2048, -1536, -1024]):
    deco(f'deco:vat_fire_{n + 1}', 'room:vat_hall', 'brzier00', [x, 2620], notes='The fire under a vat.')
deco('deco:vat_hall_lantern', 'room:vat_hall', 'torch02', wall='east', along=0.75, height=256)
deco('deco:vat_hall_cask', 'room:vat_hall', '7dec21', [-600, 3000])
deco('deco:vat_hall_sacks', 'room:vat_hall', 'bag01', [-700, 1750])
deco('deco:vat_hall_sacks_2', 'room:vat_hall', 'floursac', [-2300, 1800])
deco('deco:vat_hall_mushrooms', 'room:vat_hall', 'mushrm02', [-2450, 2800])
deco('deco:vat_hall_pot', 'room:vat_hall', 'cauld00', [-650, 1950])
deco('deco:landing_f3_lantern', 'room:landing_f3', 'torch02', wall='north', along=0.5, height=256)
deco('deco:loft_lantern', 'room:herb_loft', 'torch02', wall='north', along=0.5, height=230)
deco('deco:loft_sacks', 'room:herb_loft', 'bag01', [150, 2100])
deco('deco:loft_sacks_2', 'room:herb_loft', 'floursac', [300, 1680])
deco('deco:loft_mushrooms', 'room:herb_loft', 'mushrm04', [950, 1680])
deco('deco:cage_3', 'room:hidden_cage', 'bonecage', [-2944, 2420], notes='Cage 3: the hidden child.')
deco('deco:hidden_candle', 'room:hidden_cage', 'cndlab0', [-2780, 2250])
deco('deco:broken_balcony_bones', 'room:broken_balcony', 'dec29', [-1200, 1450])
# fourth floor
deco('deco:rosebud_torch', 'room:rosebud_landing', 'torch06', wall='south', along=0.12, height=256)
for n, (x, y) in enumerate([(-2560, 700), (-2970, 520), (-2970, 56), (-2560, -120), (-2150, 56), (-2150, 520)]):
    deco(f'deco:circle_candle_{n + 1}', 'room:coven_sanctum', 'dec02', [x, y])
deco('deco:pier_torch_n', 'room:coven_sanctum', 'torch06', wall='east', at=[-1088, 160], height=256)
deco('deco:pier_torch_s', 'room:coven_sanctum', 'torch06', wall='east', at=[-1088, -280], height=256)
deco('deco:sanctum_torch_w', 'room:coven_sanctum', 'torch05', wall='west', along=0.2, height=256)
deco('deco:sanctum_torch_w2', 'room:coven_sanctum', 'torch05', wall='west', along=0.8, height=256)
deco('deco:altar_pot', 'room:coven_sanctum', 'cauld00', [-3330, 288])
deco('deco:altar_skull', 'room:coven_sanctum', '7dec20', [-3200, 200], floor_height=1992)
deco('deco:altar_goblet', 'room:coven_sanctum', '7dec48', [-3200, 380], floor_height=1992)
deco('deco:skull_pile', 'room:coven_sanctum', 'sklplrev', [-3950, 800])
deco('deco:cage_4', 'room:witch_bedchamber', 'bonecage', [-3950, -500], notes="Cage 4, in the witches' bedchamber.")
deco('deco:bed_candle_1', 'room:witch_bedchamber', 'dec02', [-3520, -900])
deco('deco:bed_candle_2', 'room:witch_bedchamber', 'dec02', [-3136, -900])
deco('deco:bed_goblet', 'room:witch_bedchamber', '7dec48', [-2780, -500])
deco('deco:bed_hanging_cage', 'room:witch_bedchamber', '7dec07', [-2750, -672], height=470)
deco('deco:hoist_lantern', 'room:hoist_room', 'torch02', wall='east', along=0.85, height=256)
deco('deco:hoist_cask', 'room:hoist_room', '7dec21', [-2380, -900])
deco('deco:hoist_sacks', 'room:hoist_room', 'bag01', [-2380, -480])
o['decorations'] = D

o['placeholders'] = [
    {'id': 'placeholder:cloaks', 'room': 'room:gate_hall', 'at': [-480, -2000], 'size': [32, 512, 160],
     'stands_for': "A row of iron hooks along the west wall with small children's cloaks hanging on them"},
    {'id': 'placeholder:straw_pens', 'room': 'room:goblin_pens', 'at': [1600, -2780], 'size': [1600, 160, 96],
     'stands_for': 'Straw pens with wattle hurdles along the south wall'},
    {'id': 'placeholder:dried_toads', 'room': 'room:toad_larder', 'at': [-1120, -2048], 'size': [384, 384, 64],
     'stands_for': 'Dried toads hanging in strings from the beams over the trough; live toads in the trough'},
    {'id': 'placeholder:herb_racks', 'room': 'room:herb_loft', 'at': [544, 1900], 'size': [640, 64, 256],
     'stands_for': 'Drying racks of herbs and toad skins'},
    {'id': 'placeholder:toad_lid', 'room': 'room:vat_hall', 'at': [-2048, 2880], 'size': [96, 96, 48],
     'stands_for': 'A carved wooden toad on the good vat\'s lid'},
    {'id': 'placeholder:mirror', 'room': 'room:witch_bedchamber', 'at': [-4050, -700], 'size': [16, 128, 256],
     'stands_for': "A tall black-framed mirror on the bedchamber's west wall"},
    {'id': 'placeholder:winch', 'room': 'room:hoist_room', 'at': [-2048, -864], 'size': [320, 128, 160],
     'stands_for': 'The great winch drum of the hoist with its rope (a block of planks stands there)'},
]

o['plates'] = [{'id': 'plate:crying', 'room': 'room:vat_hall', 'at': [-2400, 2368], 'size': [256, 384],
                'notes': 'In front of the bookcase: the child crying behind it is heard here.'}]

o['exits'] = [
    {'id': 'exit:tower_door', 'room': 'room:gate_hall', 'wall': 'south', 'size': [128, 256], 'surface': FRONT_DOOR,
     'to': 'exit:toad_meadow', 'notes': "The tower door (Clanker's Laboratory's carved double door), out to Toad Meadow."},
    {'id': 'exit:cloud_stair', 'room': 'room:roof', 'wall': 'west', 'size': [512, 512], 'surface': S('sky_clo1', 512, 512),
     'to': 'exit:cloudreach', 'notes': 'The cloud stair at the roof\'s west edge, up into the clouds.'},
]
o['notes'] = ("Objects of the L4 brief (first written by output/studio_cal/xd04/tools/gen_objects.py). Stand-ins: "
              "goblins MM7's Goblin family, the witches Moon clerics, the familiars bats; the Head Witch a Cleric of the "
              "Moon with 300 hit points and a name, the warden a Goblin Lord, the children Goblin peasants.")
yaml.safe_dump(o, open(L4 + '/objects.yml', 'w'), sort_keys=False, width=1000)
