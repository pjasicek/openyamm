# XD-04 Witch Tower, L4: the shell (rooms.yml), written from L3's rooms.yml (geometry kept) with the texture families
# of the lead's rule (Clanker's Laboratory 7d12 for the tower, the Temple of the Moon 7d06 for the coven's floor),
# wall bands, furniture, the Alacorn bridge over the shaft and the dormitory's cupboard.
# Run: python3 gen_rooms.py <L3 rooms.yml> <L4 folder>. A first-shell generator: once the project has hand edits the
# files are the source.
import copy
import sys
import yaml

L3, L4 = sys.argv[1], sys.argv[2]
src = yaml.safe_load(open(L3))


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# The tower: MM7 Clanker's Laboratory (7d12)
STONE = S('hwm2wall', 128, 256)
FRIEZE = S('hwm2b', 128, 256)
COBBLE = S('hhp2b2', 128, 128)
BEAMS = S('hwm2rf', 128, 128)
PLANKWALL = S('hwm1bwall', 128, 256)
WAINSCOT = S('hwm1b', 128, 256)
BOARDS = S('7trimd', 128, 256)
FLAGS = S('7tfb1', 128, 128)
SLATE = S('7tfb11', 128, 128)
BOOKS = S('7t1books', 128, 256)
MARBLE = S('7tws1f', 128, 128)
PLASTER = S('twb1a', 128, 256)
WOOD = S('7t1books1', 128, 128)
DARKWOOD = S('trim11_32', 32, 64)
SHEETS = S('t2bedsht', 128, 256)
BREW = {'texture': '7slimywtr'}
# The coven: MM7 Temple of the Moon (7d06)
TEMPLE = S('7tws2', 128, 256)
SKULLS = S('tws2b', 128, 256)
TFLOOR = S('7tfb11', 128, 128)
TCEIL = S('twb2', 128, 256)
TREVEAL = S('tfb2', 128, 128)
TDOOR = S('twb1', 128, 256)
TBRICK = S('wall', 128, 256)
TROCK = S('cwb1', 128, 256)
TPLASTER = S('twb1a', 128, 256)
SEAL = [S('t1d1a', 256, 256, scale=1.25), S('t1d1b', 256, 256, scale=1.25), S('t1d1c', 256, 256, scale=1.25),
        S('t1d1d', 256, 256, scale=1.25)]
SKY = S('sky_clo1', 512, 512)

themes = [
    {'id': 'theme:tower_stone', 'wall': FRIEZE, 'floor': COBBLE, 'ceiling': BEAMS, 'reveal': STONE, 'door': BOARDS,
     'notes': "Ground floor (L2 tower_stone), Clanker's Laboratory (MM7 7d12) as that map lays it: rubble-stone walls "
              "(hwm2wall) under the carved timber frieze (hwm2b, a band at the top of each wall), cobbles (hhp2b2), "
              "black-beamed plank ceilings (hwm2rf), plank door leaves (7trimd)."},
    {'id': 'theme:cauldron', 'wall': FRIEZE, 'floor': COBBLE, 'ceiling': BEAMS, 'reveal': STONE,
     'notes': "The shaft (L2 cauldron): the same rubble stone from the cauldron floor to the roof beams (7d12)."},
    {'id': 'theme:nursery', 'wall': PLASTER, 'floor': BOARDS, 'ceiling': BEAMS, 'reveal': PLANKWALL, 'door': BOARDS,
     'notes': "Second floor (L2 nursery), 7d12's wooden rooms: carved wainscot (hwm1b) as a band at the foot of the "
              "walls, cracked plaster above (twb1a), plank floors (7trimd), the black-beamed ceiling (hwm2rf)."},
    {'id': 'theme:brewery', 'wall': FRIEZE, 'floor': FLAGS, 'ceiling': BEAMS, 'reveal': PLANKWALL, 'door': BOARDS,
     'notes': "Third floor (L2 brewery), 7d12's laboratory: plank walls (hwm1bwall) under the carved frieze band "
              "(hwm2b), its flagstones (7tfb1), black beams (hwm2rf)."},
    {'id': 'theme:stair', 'wall': STONE, 'floor': COBBLE, 'ceiling': BEAMS, 'reveal': STONE,
     'notes': "The stairs inside the tower's walls (7d12): rubble stone, cobble treads, black beams."},
    {'id': 'theme:coven', 'wall': TEMPLE, 'floor': TFLOOR, 'ceiling': TCEIL, 'reveal': TREVEAL, 'door': TDOOR,
     'notes': "Fourth floor (L2 coven), the Temple of the Moon (MM7 7d06), the witches being the Moon's cult: dressed "
              "stone under a carved frieze (7tws2), the ram-skull frieze (tws2b) in the sanctum, dark flags (7tfb11), "
              "block ceilings (twb2), stone door slabs (twb1), the Moon seal (t1d1a-d)."},
    {'id': 'theme:coven_stair', 'wall': TBRICK, 'floor': TFLOOR, 'ceiling': TCEIL, 'reveal': TREVEAL, 'door': TDOOR,
     'notes': "The roof stair behind the ward (7d06's dark brick 'wall')."},
    {'id': 'theme:roof', 'wall': SKY, 'floor': SLATE, 'ceiling': SKY,
     'notes': "The roof: the tower's rubble stone as a parapet (7d12), slate (7tfb11), and a cloudy sky texture "
              "(sky_clo1) as a stand-in ceiling 2048 up: a BLV room cannot open to the sky."},
]


rooms = []
by_id = {}
for r in src['rooms']:
    r = copy.deepcopy(r)
    by_id[r['id']] = r
    rooms.append(r)

# Themes per room (L3's ids stay); the roof stair is the coven's, the loft steps a stair.
for r in rooms:
    if r['id'] == 'room:roof_stair':
        r['theme'] = 'theme:coven_stair'
    if r['id'] == 'room:loft_steps':
        r['theme'] = 'theme:stair'

# Wall bands on level rooms: the ground floor's stone and the brewery's planks under the frieze, which hangs in the
# top 256 of each wall (the theme's wall); the nursery's carved wainscot at the foot under plaster.
for r in rooms:
    if 'slope' in r:
        continue
    t = r.get('theme')
    h = r['ceiling'] - r['floor']
    if t == 'theme:tower_stone' and h > 300:
        r['bands'] = [{'height': h - 256, 'surface': STONE}]
    elif t == 'theme:brewery' and h > 300:
        r['bands'] = [{'height': h - 256, 'surface': PLANKWALL}]
    elif t == 'theme:nursery':
        r['bands'] = [{'height': 256, 'surface': WAINSCOT}]

# --- Cauldron chamber: the cauldron, its firing pits, the bridge to the Alacorn over the shaft -----------------------
cc = by_id['room:cauldron_chamber']
cc['platforms'] = [
    {'id': 'platform:cauldron', 'outline': [[384, -160], [384, 160], [160, 384], [-160, 384], [-384, 160],
                                            [-384, -160], [-160, -384], [160, -384]],
     'rise': 96, 'surface': DARKWOOD, 'top_surface': BREW,
     'notes': "The great cauldron: a stone-rimmed tub 768 square turned 45 degrees, brimming with the green brew "
              "(7slimywtr, a liquid of 7d12's own); 96 high, a ledge not stepped onto; it hurts whoever lands in it."},
    {'id': 'platform:bridge', 'at': [-440, -128], 'size': [400, 192], 'base': 1888, 'rise': 32, 'surface': DARKWOOD, 'top_surface': BOARDS,
     'bottom_surface': BOARDS,
     'notes': "The Alacorn bridge: a plank walk 192 wide hanging over the shaft from the Witches' Finger to the "
              "pedestal landing over the cauldron (L1's bridge; L3 had only the pier)."},
    {'id': 'platform:landing', 'outline': [[-192, -272], [0, -272], [48, -224], [48, -32], [0, 16], [-192, 16], [-240, -32], [-240, -224]],
     'base': 1888, 'rise': 32, 'surface': DARKWOOD, 'top_surface': BOARDS, 'bottom_surface': BOARDS,
     'notes': "The landing at the bridge's end, over the middle of the cauldron."},
    {'at': [-440, -216], 'size': [400, 16], 'base': 1920, 'rise': 24, 'surface': DARKWOOD,
     'notes': "Kerb, south side of the bridge."},
    {'at': [-440, -40], 'size': [400, 16], 'base': 1920, 'rise': 24, 'surface': DARKWOOD,
     'notes': "Kerb, north side of the bridge."},
    {'id': 'platform:pedestal', 'at': [-96, -128], 'size': [96, 96], 'base': 1920, 'rise': 64, 'surface': MARBLE,
     'top_surface': MARBLE, 'notes': "The Alacorn's pedestal on the landing."},
]
cc['bands'] = [{'height': 256, 'surface': FRIEZE}]
cc['notes'] = (cc['notes'] + " L4: the Alacorn stands on a plank bridge hanging over the cauldron at 1920, reached from "
               "the pier on the Witches' Finger (L1's bridge, which a hanging platform can say).")

# --- Second floor ---------------------------------------------------------------------------------------------------
dorm = by_id['room:dormitory']
for p in dorm['platforms']:
    p['surface'] = WOOD
    p['top_surface'] = SHEETS
    p['notes'] = 'A small bed.'
dorm['notes'] = dorm['notes'] + " L4: the cupboard is a closet behind a secret panel in the east wall (room:cupboard)."

for p in list(dorm['platforms']):
    x, y = p['at']
    py = y - 84 if y < 400 else y + 84
    dorm['platforms'].append({'at': [x, py], 'size': [96, 40], 'base': 48, 'rise': 12, 'surface': SHEETS,
                              'top_surface': SHEETS, 'notes': 'A pillow.'})

# L4: the main rooms sized up to the shipped dungeons' median (scale_bands.py; the user found XD-01 cramped).
dorm['outline'] = [[2880, -192], [4288, -192], [4544, 64], [4544, 768], [4288, 1024], [2880, 1024]]
cup = {'id': 'room:cupboard', 'name': 'Cupboard', 'space': 'room:dormitory',
       'outline': rect(4608, 336, 4736, 496), 'floor': 640, 'ceiling': 896, 'theme': 'theme:nursery', 'ambient': 22,
       'walls': [{'wall': 'east', 'surface': PLANKWALL}],
       'notes': "The goblin's hoard: a shallow cupboard behind a loose panel in the dormitory's end wall."}
rooms.append(cup)

school = by_id['room:schoolroom']
school['walls'] = [{'wall': 'east', 'panels': [
    {'id': 'panel:slate', 'at': 'centre', 'length': 512, 'bottom': 96, 'height': 256, 'surface': SLATE,
     'notes': "The slate: a board of dark slate (7d12's 7tfb11) where the lesson is chalked."}]}]
for p in school['platforms']:
    p['surface'] = WOOD
    p['top_surface'] = BOARDS
    p['notes'] = 'A bench row, one step up.'
school['platforms'].append({'at': [3104, 1728], 'size': [96, 256], 'rise': 72, 'surface': WOOD, 'top_surface': WOOD,
                            'notes': "The teacher's desk, before the slate."})

niche = by_id['room:skull_niche']
niche['walls'] = [{'wall': 'east', 'panels': [{'at': 'centre', 'length': 384, 'surface': BOOKS,
                                               'notes': 'The bookcase wall, floor to ceiling.'}]}]
niche['platforms'] = [{'at': [2272, 576], 'size': [64, 352], 'rise': 112, 'surface': WOOD, 'top_surface': WOOD,
                       'notes': 'The low shelf the three skulls sit on.'}]

by_id['room:gate_hall']['outline'] = [[-640, -3200], [640, -3200], [640, -2496], [384, -1600], [-384, -1600],
                                      [-640, -2496]]
by_id['room:goblin_pens']['outline'] = [[704, -2880], [2496, -2880], [2496, -1600], [704, -1600]]
by_id['room:toad_larder']['outline'] = [[-1536, -2880], [-704, -2880], [-704, -1600], [-1536, -1600]]
by_id['room:warden_lodge']['outline'] = [[-3008, -2368], [-1600, -2368], [-1600, -1024], [-2240, -1024], [-3008, -1600]]

# --- Ground floor ---------------------------------------------------------------------------------------------------
pens = by_id['room:goblin_pens']
pens['platforms'] = [{'at': [1600, -2048], 'size': [1024, 128], 'rise': 48, 'surface': DARKWOOD,
                      'top_surface': BREW, 'notes': "The feeding trough: a plank trough of green slop."}]
larder = by_id['room:toad_larder']
larder['platforms'] = [{'at': [-1120, -2048], 'size': [384, 384], 'rise': 32, 'surface': STONE, 'top_surface': BREW,
                        'notes': "The toad trough: a raised stone trough of green water."}]
lodge = by_id['room:warden_lodge']
lodge['platforms'] = [{'at': [-2048, -1600], 'size': [224, 128], 'rise': 64, 'surface': WOOD, 'top_surface': WOOD,
                       'notes': "The warden's table."}]

# --- Third floor ----------------------------------------------------------------------------------------------------
vat = by_id['room:vat_hall']
vat['walls'] = [{'wall': 5, 'panels': [{'at': 'centre', 'length': 1024, 'surface': BOOKS,
                                         'notes': 'The bookcase wall, floor to ceiling (the secret door is in it).'}]}]
for p in vat['platforms']:
    p['surface'] = FLAGS
    p['top_surface'] = FLAGS
    p['notes'] = 'A vat plinth.'

loft = by_id['room:herb_loft']
loft['walls'] = [{'wall': 'north', 'panels': [
    {'id': 'panel:recipe', 'offset': 160, 'length': 64, 'bottom': 144, 'height': 128,
     'surface': S('t2bedsht', 128, 256, scale=0.5),
     'notes': "The recipe card pinned to the wall (a pale cloth picture of 7d12's for a card)."}]}]

# --- Fourth floor ---------------------------------------------------------------------------------------------------
san = by_id['room:coven_sanctum']
cx, cy = -2560, 288
san['platforms'] = [
    {'id': 'platform:circle_nw', 'at': [cx - 160, cy + 160], 'size': [320, 320], 'rise': 8, 'surface': TREVEAL, 'top_surface': SEAL[0]},
    {'id': 'platform:circle_ne', 'at': [cx + 160, cy + 160], 'size': [320, 320], 'rise': 8, 'surface': TREVEAL, 'top_surface': SEAL[1]},
    {'id': 'platform:circle_sw', 'at': [cx - 160, cy - 160], 'size': [320, 320], 'rise': 8, 'surface': TREVEAL, 'top_surface': SEAL[2]},
    {'id': 'platform:circle_se', 'at': [cx + 160, cy - 160], 'size': [320, 320], 'rise': 8, 'surface': TREVEAL, 'top_surface': SEAL[3]},
    {'at': [-3200, 288], 'size': [128, 256], 'rise': 72, 'surface': TROCK, 'top_surface': TFLOOR,
     'notes': "The low altar by the circle."},
]
for p in san['platforms'][:4]:
    p['notes'] = "A quarter of the witch-mark circle: the Moon seal of 7d06 laid in the floor."
san['pillars'] = [{'at': [-3584, -64], 'size': [96, 96], 'surface': SKULLS, 'notes': 'Carved roof post.'},
                  {'at': [-3584, 640], 'size': [96, 96], 'surface': SKULLS, 'notes': 'Carved roof post.'}]
san['walls'] = [{'wall': 'south', 'surface': SKULLS}, {'wall': 'north', 'surface': SKULLS}]

bed = by_id['room:witch_bedchamber']
for p in bed['platforms']:
    p['surface'] = WOOD
    p['top_surface'] = S('7t1beds2', 128, 256)
    p['notes'] = 'A bed.'

for p in list(bed['platforms']):
    x, y = p['at']
    bed['platforms'].append({'at': [x, y - 120], 'size': [192, 48], 'base': 48, 'rise': 16, 'surface': SHEETS,
                             'top_surface': SHEETS, 'notes': 'A pillow.'})

hoist = by_id['room:hoist_room']
hoist['platforms'] = [{'id': 'platform:winch', 'at': [-2048, -864], 'size': [320, 128], 'rise': 128, 'surface': DARKWOOD,
                       'top_surface': DARKWOOD, 'notes': 'The winch drum (a block until a model exists).'}]

gate = by_id['room:gate_hall']
gate['walls'] = [{'wall': 'south', 'panels': [{'at': 'centre', 'length': 128, 'height': 256,
                                                'surface': S('hwm2d', 128, 256),
                                                'notes': "Behind the exit face of the tower door (one face under it)."}]}]
roof = by_id['room:roof']
roof['bands'] = [{'height': 112, 'surface': STONE}]
roof['walls'] = [{'wall': 'west', 'panels': [{'at': 'centre', 'length': 512, 'height': 512,
                                               'surface': S('sky_clo1', 512, 512),
                                               'notes': 'Behind the exit face of the cloud stair.'}]}]
roof.pop('pillars', None)
roof['platforms'] = [{'at': [-6400, 448], 'size': [384, 384], 'rise': 448, 'surface': STONE, 'top_surface': COBBLE,
                      'notes': "The chimney stack of the tower's crown."}]
roof['notes'] = ("The crown of the crooked tower's westmost storey: an eight-sided terrace round the chimney stack. Open sky "
                 "is not drawable in a BLV: the parapet is a band of stone 112 high and the walls above it and the "
                 "ceiling 2048 up wear the cloudy sky (sky_clo1). The cloud stair to X8 is an exit on its west wall.")

# Pitched ceilings over the long rooms, as Clanker's Laboratory's corridors and the Temple's halls are roofed: a ridge
# along the room's long axis (L3's flat ceilings: R3-K5 had no sloped ceilings).
RIDGES = {'room:ring_f1': (512, 704, [1, 0]), 'room:vat_hall': (1792, 2176, [1, 0]),
          'room:schoolroom': (1152, 1344, [1, 0]), 'room:dormitory': (1088, 1280, [1, 0]),
          'room:coven_sanctum': (2560, 3008, [1, 0]), 'room:witch_bedchamber': (2432, 2624, [1, 0]),
          'room:goblin_pens': (448, 640, [1, 0]), 'room:herb_loft': (1856, 1984, [1, 0])}
for r in rooms:
    if r['id'] in RIDGES:
        c, top, sc = RIDGES[r['id']]
        r['ceiling'] = c
        r['ceiling_levels'] = [{'ceiling': top, 'top_scale': sc, 'notes': 'A pitched roof of black planks.'}]
        h = c - r['floor']
        if r.get('bands') and r['bands'][0]['surface'] in (STONE, PLANKWALL):
            r['bands'] = [{'height': h - 256, 'surface': r['bands'][0]['surface']}]
san.pop('pillars', None)
san['platforms'] += [{'at': [-3584, -64], 'size': [96, 96], 'rise': 640, 'surface': SKULLS, 'notes': 'Carved roof post.'},
                     {'at': [-3584, 640], 'size': [96, 96], 'rise': 640, 'surface': SKULLS, 'notes': 'Carved roof post.'}]
# The shaft: a timber frieze ring at each storey's height (the frieze picture's top at 640, 1280, 1920 and the roof).
cc['bands'] = [{'height': 384, 'surface': STONE}, {'height': 640, 'surface': FRIEZE},
               {'height': 1024, 'surface': STONE}, {'height': 1280, 'surface': FRIEZE},
               {'height': 1664, 'surface': STONE}, {'height': 1920, 'surface': FRIEZE},
               {'height': 2432, 'surface': STONE}]

AMB = {'room:gate_hall': 18, 'room:ring_f1': 18, 'room:warden_lodge': 20, 'room:toad_larder': 22,
       'room:goblin_pens': 18, 'room:cauldron_chamber': 12, 'room:hoist_slot': 20, 'room:stair_1_2_a': 22,
       'room:stair_1_2_b': 22, 'room:stair_1_2_mid': 20, 'room:landing_f2': 22, 'room:balcony_f2': 20,
       'room:dormitory': 24, 'room:cupboard': 26, 'room:schoolroom': 22, 'room:skull_niche': 24,
       'room:stair_2_3_a': 22, 'room:stair_2_3_b': 22, 'room:stair_2_3_mid': 20, 'room:landing_f3': 20,
       'room:vat_hall': 20, 'room:loft_steps': 22, 'room:herb_loft': 22, 'room:hidden_cage': 26,
       'room:broken_balcony': 22, 'room:stair_3_4': 28, 'room:rosebud_landing': 24, 'room:coven_sanctum': 24,
       'room:shaft_bridge': 18, 'room:witch_bedchamber': 24, 'room:hoist_room': 22, 'room:roof_stair': 26,
       'room:roof': 4}
for r in rooms:
    if r['id'] in AMB:
        r['ambient'] = AMB[r['id']]

out = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:tower_stone', 'ambient': 16}, 'rooms': rooms}

# Openings: L3's, with the pier's tip made the bridge's mouth and the cupboard's door.
opens = copy.deepcopy(src['openings'])
for o in opens:
    if o['id'] == 'open:bridge_tip':
        o['width'] = 192
        o['height'] = 384
        o.pop('sill', None)
        o['notes'] = "The pier's tip opens onto the plank bridge over the shaft (L3: a 64 lip over the drop)."
        o['from_wall'] = 1
        o['to_wall'] = 8
    if o['id'] == 'open:hoist_slot_cauldron':
        o['from_wall'] = 1
        o['to_wall'] = 10
    if o['id'] == 'open:sanctum_window':
        o['from_wall'] = 3
        o['to_wall'] = 6
    if o['id'] == 'open:rosebud_door':
        o['width'] = 320
        o['height'] = 320
    if o['id'] == 'open:balcony_schoolroom':
        o['width'] = 256
        o['height'] = 320
opens.append({'id': 'open:dormitory_cupboard', 'from': 'room:dormitory', 'to': 'room:cupboard', 'width': 128,
              'height': 224, 'notes': "The loose panel in the dormitory's end wall."})
out['openings'] = opens
out['notes'] = ("XD-04 Witch Tower, L4: L3's crooked tower (each storey a quarter turn round the shaft) with the texture "
                "families of the lead's rule (Clanker's Laboratory for the tower, the Temple of the Moon for the "
                "coven's floor), the Alacorn's bridge over the shaft and furniture. First written by "
                "output/studio_cal/xd04/tools/gen_rooms.py from L3's rooms.yml.")
yaml.safe_dump(out, open(L4 + '/rooms.yml', 'w'), sort_keys=False, width=1000)
