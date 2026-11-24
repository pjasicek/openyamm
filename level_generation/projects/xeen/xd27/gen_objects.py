# XD-27 Ogre Lair: objects, wiring and project (run inside gen.py, which defines rooms, openings, S, ROCK ...).

# ================================================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:mouth', 'at': [0, 448], 'facing': 90,
                    'notes': "Inside the bone-strewn mouth, facing in; daylight behind."}
objects['doors'] = [
    {'id': 'door:gate', 'opening': 'open:gate', 'kind': 'hinged', 'hinge': 'left', 'thickness': 24, 'speed': 60,
     'surface': S('t68a10a', 32, 64, uneven=True), 'back_surface': S('t68a10a', 32, 64, uneven=True),
     'edge_surface': PLANK, 'top_surface': PLANK,
     'notes': "The log gate: a leaf of d08's upright planks, hinged at its west post. Barred from the gate yard's side (mover:gate_bar)."},
    {'id': 'door:larder', 'opening': 'open:chief_larder', 'kind': 'hinged', 'hinge': 'right', 'thickness': 24, 'speed': 60,
     'surface': S('t68a13mm', 128, 128, uneven=True), 'back_surface': S('t68a13mm', 128, 128, uneven=True),
     'edge_surface': PLANK, 'top_surface': PLANK,
     'notes': "The larder's heavy plank door (the middle of d08's own nine-part door); the Chieftain carries its key."},
]
HEAP_TRAVEL = [0, -800, -64]
BOULDER = S('gcav1flr', 256, 256, scale=0.5)  # d08's grey floor rock, small: the heap's boulders against the brown walls
objects['movers'] = [
    {'id': 'mover:gate_bar', 'room': 'room:gate_yard', 'at': [0, 1148], 'size': [576, 32], 'bottom': 144, 'height': 40,
     'travel': [0, 0, 256], 'speed': 96, 'surface': BEAM, 'top_surface': BEAM, 'end_surface': PLANK,
     'notes': "The gate's bar: a log beam across the gate resting on two forked posts; lifted, it rises clear above the gate."},
    {'id': 'mover:rack_bar', 'room': 'room:river_ledge', 'at': [2752, 5632], 'size': [304, 24], 'bottom': 48, 'height': 48,
     'travel': [0, 0, -112], 'speed': 160, 'surface': BEAM, 'top_surface': BEAM, 'end_surface': PLANK,
     'notes': "The rack's cross-beam that holds the heap; knocked out, it drops."},
    {'id': 'mover:heap_1', 'room': 'room:river_ledge', 'outline': octagon(2752, 5504, 112), 'height': 112,
     'travel': HEAP_TRAVEL, 'speed': 400, 'surface': BOULDER, 'top_surface': BOULDER,
     'notes': "The boulder heap, its foot: rolls south down the slide into the rock."},
    {'id': 'mover:heap_2', 'room': 'room:river_ledge', 'outline': octagon(2744, 5496, 80), 'bottom': 112, 'height': 80,
     'travel': HEAP_TRAVEL, 'speed': 400, 'surface': BOULDER, 'top_surface': BOULDER, 'notes': "The heap, a boulder on top."},
]
objects['plates'] = [
    {'id': 'plate:chute_trap', 'room': 'room:chute', 'at': [1680, 6000], 'size': [96, 96],
     'notes': "Halfway down the chute: the boulder trap (invisible, the chute's own planks)."},
]
objects['floors'] = [{'id': 'floor:river', 'of': 'room:gorge', 'kind': 'water'}]


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [255, 160, 80]
DAY = [255, 248, 228]
SUN = [240, 225, 195]
lights = [
    light('light:mouth_day', 'room:mouth', [0, 192], 320, 1500, DAY, notes="The X2 hills' daylight through the mouth."),
    light('light:mouth_gate', 'room:mouth', [0, 900], 300, 700, FIRE, notes="The skull torches either side of the gate."),
    light('light:den_fire', 'room:bone_den', [-2176, 2560], 120, 1300, [255, 140, 70],
          pulse={'intensity': [0.7, 1.0], 'frequency': 1.1, 'phase': 0.4}),
    light('light:pit_fire', 'room:feast_cave', [PIT[0], PIT[1]], 40, 2200, [255, 150, 70],
          pulse={'intensity': [0.75, 1.0], 'frequency': 1.3, 'phase': 0.1}, notes="The fire in the cooking pit."),
    light('light:feast_rim_w', 'room:feast_cave', [-1000, 3600], 300, 1000, FIRE),
    light('light:feast_rim_e', 'room:feast_cave', [640, 2560], 300, 1000, FIRE),
    light('light:yard_fire', 'room:gate_yard', [320, 1700], 120, 1100, [255, 140, 70],
          pulse={'intensity': [0.7, 1.0], 'frequency': 1.2, 'phase': 0.7}),
    light('light:kennel', 'room:kennel', [1472, 3168], 300, 800, FIRE),
    light('light:chief_fire', 'room:chief_den', [-2272, 3840], 120, 1300, [255, 140, 70],
          pulse={'intensity': [0.7, 1.0], 'frequency': 1.0, 'phase': 0.2}),
    light('light:chief_torches', 'room:chief_den', [-2752, 3940], 300, 900, FIRE),
    light('light:larder_torch', 'room:larder', [-3300, 4000], 200, 900, FIRE),
    light('light:quarry_fire', 'room:quarry', [256, 5728], 120, 1300, [255, 140, 70],
          pulse={'intensity': [0.7, 1.0], 'frequency': 1.2, 'phase': 0.5}),
    light('light:quarry_torches', 'room:quarry', [-448, 6200], 300, 900, FIRE),
    light('light:chute_day', 'room:chute', [2000, 6080], 300, 900, DAY, notes="Daylight from the ledge ahead."),
    light('light:ledge_day', 'room:river_ledge', [3000, 6176], 450, 1300, SUN, notes="Daylight from the gorge."),
    light('light:ledge_rack', 'room:river_ledge', [2752, 5760], 260, 800, FIRE),
    light('light:gorge_day', 'room:gorge', [3680, 6176], 700, 3000, DAY, notes="The open sky over the gorge."),
]
objects['lights'] = lights

objects['chests'] = [
    {'id': 'chest:bundle', 'room': 'room:bone_den', 'at': [-2752, 2880], 'kind': 'gt002',
     'treasure_level': 2, 'random_items': 2, 'gold': 150, 'notes': "A bundle of plunder in the far sleeping heap."},
    {'id': 'chest:chief', 'room': 'room:chief_den', 'at': [-2336, 4288], 'kind': 'gt002',
     'treasure_level': 2, 'random_items': 3, 'notes': "The Chieftain's own chest by the north wall."},
    {'id': 'chest:strongbox', 'room': 'room:larder', 'at': [-3808, 3696], 'kind': 'gt002',
     'treasure_level': 3, 'random_items': 3, 'gold': 800,
     'notes': "A ship's strongbox from Nystor's sunk boats: the map's hoard, one treasure level up."},
    {'id': 'chest:cargo', 'room': 'room:larder', 'at': [-3968, 4128], 'kind': 'gt002',
     'treasure_level': 2, 'random_items': 2, 'gold': 300, 'notes': "A cargo chest from the boats."},
]

objects['spawns'] = [
    {'id': 'spawn:midden', 'room': 'room:midden', 'at': [-1780, 1040], 'slot': 2, 'tier': 'a', 'group': 51,
     'notes': "Dogs gnawing bones at the bend (Dark Wolves)."},
    {'id': 'spawn:den_w', 'room': 'room:bone_den', 'at': [-2560, 2304], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "Asleep on their heaps."},
    {'id': 'spawn:feast_e', 'room': 'room:feast_cave', 'at': [576, 3008], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "Round the pit, east."},
    {'id': 'spawn:feast_pit', 'room': 'room:feast_cave', 'at': [128, 3424], 'slot': 3, 'tier': 'b', 'group': 51,
     'notes': "The shamans by the cauldron (Ogre Brutes)."},
    {'id': 'spawn:yard', 'room': 'room:gate_yard', 'at': [32, 1700], 'slot': 2, 'tier': 'a', 'group': 51,
     'notes': "The gate's guard dogs round the fire."},
    {'id': 'spawn:kennel', 'room': 'room:kennel', 'at': [1536, 3168], 'slot': 2, 'tier': 'a', 'group': 51,
     'notes': "The dogs."},
    {'id': 'spawn:quarry', 'room': 'room:quarry', 'at': [64, 6016], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "Ogres at work in the quarry."},
    {'id': 'spawn:chief', 'room': 'room:chief_den', 'at': [-2176, 3712], 'slot': 3, 'tier': 'b', 'group': 51,
     'notes': "The Chieftain's shamans (Ogre Brutes)."},
]
# No `relations`: the world's relations.yml (ogres long, wolves medium toward the party, no feud) is what the game and,
# since A1's merge point 3, the studio's hostility check read.
objects['monsters'] = [
    {'id': 'monster:chieftain', 'room': 'room:river_ledge', 'monster': 11063, 'at': [2752, 6400], 'facing': 180, 'hostile': True,
     'group': 2, 'name': 'Ogre Chieftain', 'carries': 'larder_key',
     'notes': "The Ogre Chieftain: the Ogres family's boss row (11063, level 24); he carries the larder key."},
    {'id': 'monster:thrower_1', 'room': 'room:river_ledge', 'monster': 11060, 'at': [2960, 5952], 'facing': 0, 'hostile': True,
     'group': 3, 'name': 'Boulder Thrower', 'notes': "A thrower at the parapet (an Ogre, 11060, level 18)."},
    {'id': 'monster:thrower_2', 'room': 'room:river_ledge', 'monster': 11060, 'at': [2960, 6560], 'facing': 0, 'hostile': True,
     'group': 3, 'name': 'Boulder Thrower'},
    {'id': 'monster:thrower_3', 'room': 'room:river_ledge', 'monster': 11060, 'at': [2752, 6848], 'facing': 0, 'hostile': True,
     'group': 3, 'name': 'Boulder Thrower'},
]


def deco(id, rm, d, at, **kw):
    x = {'id': id, 'room': rm, 'decoration': d, 'at': at}
    if at is None:  # on a wall by `wall` and `along`
        del x['at']
    x.update(kw)
    return x


decos = [
    # mouth
    # lights audit (merge point 14): MM6's skull torch (torskul0) is a wall fixture; it stood on the floor, six of the
    # eleven away from any wall (drawn as the free model). Each now hangs on the nearest wall of its old place, 160
    # over the floor: wall = the outline edge, along its fraction (the old place projected onto the edge, moved where
    # the rough wall's face lies within 20 of the outline: the rough faces bulge in or out mid-edge).
    deco('deco:mouth_torch_w', 'room:mouth', 'torskul0', None, wall=9, along=0.386, height=160),
    deco('deco:mouth_torch_e', 'room:mouth', 'torskul0', None, wall=4, along=0.6, height=160),
    deco('deco:mouth_skulls_w', 'room:mouth', 'sklplrev', [-415, 392]),
    deco('deco:mouth_skulls_e', 'room:mouth', 'sklplrev', [352, 860]),
    deco('deco:mouth_bones_1', 'room:mouth', '7dec18', [-260, 380]),
    deco('deco:mouth_bones_2', 'room:mouth', 'dec19', [288, 576]),
    deco('deco:mouth_bones_3', 'room:mouth', 'dec29', [192, 760]),
    deco('deco:mouth_rock_w', 'room:mouth', '6rock02', [-512, 192]),
    deco('deco:mouth_rock_e', 'room:mouth', '6rock05', [544, 352]),
    deco('deco:mouth_boatman', 'room:mouth', 'Corpse04', [400, 180], facing=0,
         notes="A drowned boatman the ogres dragged up from the river."),
    # midden
    deco('deco:midden_heap_1', 'room:midden', 'trasheap', [-1120, 400]),
    deco('deco:midden_heap_2', 'room:midden', '7dec10', [-1496, 844]),
    deco('deco:midden_heap_3', 'room:midden', '7dec01', [-1986, 1488]),
    deco('deco:midden_bones_1', 'room:midden', 'dec29', [-1495, 555]),
    deco('deco:midden_bones_2', 'room:midden', '7dec18', [-1721, 1239]),
    deco('deco:midden_skull', 'room:midden', '7dec20', [-1964, 1624]),  # D-7 (2026-11-20): 49 -> about 230 off the walking line, by the west wall, clear of the bone den's opening
    # bone den
    deco('deco:den_fire', 'room:bone_den', '7dec02', [-2176, 2560]),
    deco('deco:den_bed_1', 'room:bone_den', '7dec01', [-2560, 2176]),
    deco('deco:den_bed_2', 'room:bone_den', 'trasheap', [-2816, 2528]),
    deco('deco:den_bed_3', 'room:bone_den', '7dec01', [-2432, 3072]),
    deco('deco:den_bed_4', 'room:bone_den', 'trasheap', [-1856, 3008]),
    deco('deco:den_bed_5', 'room:bone_den', '7dec01', [-1460, 2250]),
    deco('deco:den_bones_1', 'room:bone_den', '7dec18', [-2400, 2150]),
    deco('deco:den_bones_2', 'room:bone_den', 'dec19', [-2048, 2816]),
    deco('deco:den_bones_3', 'room:bone_den', 'dec29', [-2757, 2687]),
    deco('deco:den_skeleton', 'room:bone_den', 'dec05', [-1984, 2304]),
    deco('deco:den_keg', 'room:bone_den', 'smlbarel', [-1440, 2120]),
    # feast cave
    deco('deco:pit_fire', 'room:feast_cave', 'dec04', [PIT[0] - 128, PIT[1]]),
    deco('deco:pit_cookfire', 'room:feast_cave', 'ckfyr00', [PIT[0] + 96, PIT[1] + 32]),
    deco('deco:pit_cauldron', 'room:feast_cave', 'cauld00', [PIT[0] + 96, PIT[1] + 32], inside='deco:pit_cookfire'),
    deco('deco:feast_plates_1', 'room:feast_cave', 'dec37', [-160, 2528], floor_height=24),
    deco('deco:feast_plate_2', 'room:feast_cave', 'dec36', [0, 2528], floor_height=24),
    deco('deco:feast_bowls', 'room:feast_cave', 'dec32', [-128, 3744], floor_height=24),
    deco('deco:feast_plate_3', 'room:feast_cave', 'dec36', [432, 3008], floor_height=24),
    deco('deco:feast_bones_1', 'room:feast_cave', '7dec10', [704, 3520]),
    deco('deco:feast_bones_2', 'room:feast_cave', 'trasheap', [-960, 3584]),
    deco('deco:feast_bones_3', 'room:feast_cave', 'dec29', [560, 2300]),
    deco('deco:feast_skeleton', 'room:feast_cave', 'dec05', [-576, 2368]),
    deco('deco:feast_cask', 'room:feast_cave', '7dec21', [313, 3876]),
    deco('deco:feast_keg', 'room:feast_cave', 'smlbarel', [-1150, 2400]),
    deco('deco:feast_barrel', 'room:feast_cave', 'bigbarel', [480, 3880]),
    deco('deco:feast_torch_1', 'room:feast_cave', 'torskul0', None, wall=8, along=0.3, height=160),
    deco('deco:feast_torch_2', 'room:feast_cave', 'torskul0', None, wall=1, along=0.5, height=160),
    deco('deco:feast_torch_3', 'room:feast_cave', 'torskul0', None, wall=6, along=0.1, height=160),
    # gate yard
    deco('deco:yard_fire', 'room:gate_yard', '7dec02', [320, 1700]),
    deco('deco:yard_keg', 'room:gate_yard', 'smlbarel', [608, 1376]),
    deco('deco:yard_cask', 'room:gate_yard', '7dec21', [640, 1504]),
    deco('deco:yard_bones', 'room:gate_yard', 'dec29', [-384, 1536]),
    deco('deco:yard_rock', 'room:gate_yard', '6rock06', [-544, 1888]),
    # kennel
    deco('deco:kennel_straw_1', 'room:kennel', '7dec01', [1728, 2944]),
    deco('deco:kennel_straw_2', 'room:kennel', '7dec01', [1664, 3456]),
    deco('deco:kennel_bones_1', 'room:kennel', 'dec29', [1408, 3008]),
    deco('deco:kennel_bones_2', 'room:kennel', '7dec18', [1856, 3200]),
    deco('deco:kennel_bucket', 'room:kennel', 'Bucket', [1408, 3558]),
    deco('deco:kennel_bowl', 'room:kennel', 'foodbowl', [1543, 3565]),
    # chieftain's den
    deco('deco:chief_fire', 'room:chief_den', '7dec02', [-2272, 3840]),
    # the seat's two torches on the north wall behind it, either side of it (x -2880 and -2534)
    deco('deco:chief_torch_w', 'room:chief_den', 'torskul0', None, wall=5, along=0.875, height=160),
    deco('deco:chief_torch_e', 'room:chief_den', 'torskul0', None, wall=5, along=0.2, height=160),
    deco('deco:chief_rock_1', 'room:chief_den', '6rock01', [-2928, 3904], floor_height=64),
    deco('deco:chief_rock_2', 'room:chief_den', '6rock08', [-2576, 3904], floor_height=64),
    deco('deco:chief_skulls_1', 'room:chief_den', 'sklplrev', [-2200, 3462]),
    deco('deco:chief_skulls_2', 'room:chief_den', 'sklplrev', [-2560, 4250]),
    deco('deco:chief_skull', 'room:chief_den', '7dec20', [-1856, 3520]),
    deco('deco:chief_bones', 'room:chief_den', '7dec18', [-1920, 4096]),
    # larder
    deco('deco:larder_torch', 'room:larder', 'torch01', [-3168, 4040], wall='east', height=160),
    deco('deco:larder_barrel_1', 'room:larder', 'bigbarel', [-4032, 3712]),
    deco('deco:larder_barrel_2', 'room:larder', 'dec03', [-3584, 3680]),
    deco('deco:larder_barrel_3', 'room:larder', '7dec32', [-3420, 4120]),
    deco('deco:larder_cask', 'room:larder', '7dec21', [-3712, 4224]),
    deco('deco:larder_sack_1', 'room:larder', 'floursac', [-4080, 3800]),
    deco('deco:larder_sack_2', 'room:larder', 'bag01', [-3456, 4224]),
    deco('deco:larder_sack_3', 'room:larder', 'bag_A', [-3584, 4256]),
    deco('deco:larder_carcass', 'room:larder', 'Corpse02', [-3960, 3990], facing=90),
    deco('deco:larder_bones', 'room:larder', '7dec18', [-3904, 4256]),
    # quarry ramp, quarry
    deco('deco:ramp_bones', 'room:quarry_ramp', 'dec29', [-31, 4618]),
    deco('deco:ramp_rock', 'room:quarry_ramp', '6rock04', [-330, 4352]),
    deco('deco:quarry_fire', 'room:quarry', '7dec02', [256, 5728]),
    deco('deco:quarry_torch_1', 'room:quarry', 'torskul0', None, wall=6, along=0.15, height=160),  # east of the rubble slope
    deco('deco:quarry_torch_2', 'room:quarry', 'torskul0', None, wall=3, along=0.9, height=160),
    deco('deco:quarry_heap_1', 'room:quarry', '6rock01', [-384, 5664]),
    deco('deco:quarry_heap_2', 'room:quarry', '6rock03', [-256, 5600]),
    deco('deco:quarry_heap_3', 'room:quarry', '6rock09', [-320, 5760]),
    deco('deco:quarry_heap_4', 'room:quarry', '6rock12', [512, 6304]),
    deco('deco:quarry_heap_5', 'room:quarry', '6rock13', [384, 6368]),
    deco('deco:quarry_heap_6', 'room:quarry', 'rock10', [608, 5536]),
    deco('deco:quarry_heap_7', 'room:quarry', 'rock03', [720, 5560]),
    deco('deco:quarry_rubble_1', 'room:quarry', '7dec11', [-704, 6176]),
    deco('deco:quarry_rubble_2', 'room:quarry', '6rock06', [-832, 5888]),
    # ledge
    deco('deco:ledge_torch_w', 'room:river_ledge', 'torskul0', None, wall=0, along=0.5, height=160),
    deco('deco:ledge_torch_e', 'room:river_ledge', 'torskul0', None, wall=4, along=0.571, height=160),
    deco('deco:ledge_rock_1', 'room:river_ledge', '6rock02', [3040, 6880]),
    deco('deco:ledge_rock_2', 'room:river_ledge', '6rock12', [2400, 6880]),
    deco('deco:ledge_bones', 'room:river_ledge', 'dec29', [2496, 6560]),
    deco('deco:ledge_skull', 'room:river_ledge', '7dec20', [2368, 5888]),
]
objects['decorations'] = decos
objects['sounds'] = [
    {'id': 'sound:river', 'room': 'room:gorge', 'at': [3680, 6176], 'sound': 'rushing water loop', 'radius': 3600,
     'inner_radius': 1400, 'volume': 0.8, 'notes': "The river's roar in the gorge, heard on the ledge and in the chute."},
    {'id': 'sound:pit_fire', 'room': 'room:feast_cave', 'at': [PIT[0], PIT[1]], 'sound': '7campfire', 'radius': 1600,
     'inner_radius': 400, 'volume': 0.6, 'notes': "The fire in the cooking pit."},
]
objects['exits'] = [
    {'id': 'exit:x2', 'room': 'room:mouth', 'wall': 'south', 'size': [1024, 448], 'surface': S('7solid01', 256, 128, scale=4, uneven=True),
     'to': 'exit:x2_hills', 'notes': "The daylight of the X2 hills: the mouth's south wall (XD-05's generated hills view)."},
]
objects['placeholders'] = [
    {'id': 'placeholder:spits', 'room': 'room:feast_cave', 'stands_for': "Roasting spits on forked posts over the fire in the cooking pit",
     'at': [PIT[0] - 128, PIT[1]], 'size': [320, 32, 192]},
    {'id': 'placeholder:figurehead', 'room': 'room:chief_den', 'stands_for': "The carved figurehead of one of Captain Nystor's boats, propped beside the seat",
     'at': [-2528, 4160], 'size': [96, 64, 256]},
    {'id': 'placeholder:carcasses', 'room': 'room:larder', 'stands_for': "Carcasses (a deer, a boar, a cow) hanging from hooks on the meat beam",
     'at': [-3648, 4096], 'size': [640, 64, 192]},
    {'id': 'placeholder:trough', 'room': 'room:kennel', 'stands_for': "A hollowed log as the dogs' water trough",
     'at': [1344, 3456], 'size': [256, 64, 48]},
    {'id': 'placeholder:sledge', 'room': 'room:quarry', 'stands_for': "A timber sledge the ogres drag boulders on, and the levers (long beams) leaning on the rock",
     'at': [-128, 6304], 'size': [256, 128, 64]},
]

# ================================================================================================ wiring
BARRED = ("The log gate does not move: it is barred on the inside. A reek of old bones and rotten meat blows from a "
          "crack in the west wall of the mouth: the ogres throw their scraps down there, and what they throw down, "
          "you can climb up.")
var = lambda n: {'map_var': n}
events = [
    # Hooks and dressing, D-7 (2026-11-20): the arrival window on the first arrival only (qbit arrived_once 110342)
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'not': {'qbit': 'arrived_once'}},
     'effects': [{'lua': 'XeenQuests.hook("q-c23.arrival")'}, {'qbit': 'arrived_once'}],
     'notes': "Say why the party is here: A3's hook q-c23.arrival (its window text; a one-shot timer: a load event's window is not shown), on the first arrival only (arrived_once)."},
    {'id': 'evt:exit_x2', 'preset': 'exit', 'source': 'exit:x2', 'title': 'Leave the Ogre Lair'},
    {'id': 'evt:gate_out', 'preset': 'door', 'source': 'door:gate', 'side': 'room:mouth', 'title': 'Log gate', 'action': 'open',
     'condition': var('gate_unbarred'), 'else_effects': [{'message': BARRED}],
     'notes': "set:gate_bar: from the mouth the gate opens only once the bar is lifted inside; until then it points at the midden crack."},
    {'id': 'evt:gate_in', 'preset': 'door', 'source': 'door:gate', 'side': 'room:gate_yard', 'title': 'Log gate', 'action': 'open',
     'condition': var('gate_unbarred'),
     'else_effects': [{'text': "The bar lies across the gate in its forked posts. Lift the bar first."}]},
    {'id': 'evt:gate_bar', 'preset': 'switch', 'source': 'mover:gate_bar', 'title': 'Gate bar',
     'condition': {'not': var('gate_unbarred')}, 'opens': ['mover:gate_bar'], 'sets': var('gate_unbarred'),
     'text': "You heave the log up out of its forked posts. The gate is free: the short way out to the mouth.",
     'else_effects': [{'text': "The bar is up; the gate opens on the mouth."}],
     'notes': "poi:gate_bar: lifted from inside only; the gate is then a door both ways (loop:gate)."},
    {'id': 'evt:midden_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:midden', 'once': True,
     'text': "Bones and refuse slither under your feet: the ogres throw their scraps down this crack. Something growls above."},
    {'id': 'evt:feast_seen', 'preset': 'text', 'trigger': 'step', 'source': 'platform:terrace', 'once': True,
     'text': "Below, a great cauldron bubbles over the fire in the cooking pit: the ogres' supper. Best not to look in.",
     'seconds': 5},
    {'id': 'evt:larder_door', 'preset': 'door', 'source': 'door:larder', 'title': 'Larder door', 'action': 'open',
     'condition': {'item': 'larder_key'},
     'else_effects': [{'message': "A heavy plank door with an iron lock. The Ogre Chieftain keeps its key on his belt; he directs the boulder throwing on the ledge beyond the quarry."}],
     'notes': "link:chief_den_larder: the Chieftain's larder key (12170) opens it."},
    {'id': 'evt:chute_trap', 'preset': 'script', 'trigger': 'step', 'source': 'plate:chute_trap', 'once': True,
     'effects': [{'shake': {'strength': 1.2, 'seconds': 1.5}}, {'damage': {'amount': 30, 'kind': 'physical'}}],
     'text': "A boulder comes bounding down the chute behind you!", 'seconds': 4,
     'notes': "set:chute_boulder: once; the trap's boulder is not drawn (a step trap as the shipped maps' are)."},
    {'id': 'evt:ledge_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:river_ledge', 'once': True,
     'text': "Daylight and the roar of the river! The ledge hangs over the gorge. At its south end a heap of boulders waits on a timber rack, and the Ogre Chieftain bellows at his throwers.",
     'seconds': 7},
    {'id': 'evt:rack', 'preset': 'switch', 'source': 'mover:rack_bar', 'title': 'Boulder rack',
     'condition': {'not': {'qbit': 'ogre_boulders_dumped'}},
     'opens': ['mover:rack_bar', 'mover:heap_1', 'mover:heap_2'],
     'effects': [{'shake': {'strength': 1.5, 'seconds': 2.5}}, {'add': {'var': 'Experience', 'value': 1000}},
                 {'lua': 'XeenQuests.hook("q-c23.rack")'}],
     'else_effects': [{'lua': 'XeenQuests.hook("q-c23.rack")'}],
     'notes': "set:boulder_heap / goal:boulders: the heap rolls into the slide (two movers); A3's hook q-c23.rack sets the quest's second bit (ogre_boulders_dumped) and says it (once; again: its else text)."},
    {'id': 'evt:chief_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:chieftain'}},
     'effects': [{'add': {'var': 'Experience', 'value': 500}}],
     'text': "The Ogre Chieftain crashes down. A heavy iron key hangs from his belt.", 'seconds': 5,
     'notes': "goal:chieftain: says plainly that he carries the larder key."},
    {'id': 'evt:lair', 'preset': 'script', 'source': 'platform:seat', 'title': 'Ogre lair',
     'condition': {'kills': {'monster': 'monster:chieftain'}},
     'locked_text': "The Chieftain's seat of boulders, hung with the trophies of Nystor's boats. Break it now and his band will only pile it up again: the Chieftain throws from the ledge beyond the quarry.",
     'effects': [{'add': {'var': 'Experience', 'value': 2000}},
                 {'hide': 'platform:seat'}, {'passable': 'platform:seat'},
                 {'hide': 'platform:oar_1'}, {'passable': 'platform:oar_1'},
                 {'hide': 'platform:oar_2'}, {'passable': 'platform:oar_2'},
                 {'hide': 'panel:sail'},
                 {'lua': 'XeenQuests.hook("q-c23.chieftain")'}],
     'notes': "goal:lair / set:lair: the click breaks the lair (F47, the player's pins 2026-11-24: no Yes/No for a quest goal; the source asked aaze0010:0); A3's hook q-c23.chieftain sets Q-C23's bit (ogre_lair_destroyed) and gives the answer (aaze0010:1). The seat, the oars and the sail come down."},
    {'id': 'evt:fall', 'preset': 'script', 'trigger': 'step', 'source': 'room:gorge',
     'effects': [{'set': {'var': var('fell'), 'value': 1}}, {'damage': {'amount': 20, 'kind': 'physical'}},
                 {'teleport': {'to': [0, 640, 0], 'direction': 90}}],
     'notes': "set:fall: a party that goes over the parapet is washed out at the mouth (its message comes from evt:fall_told: a window opened before an in-map move is lost with the move)."},
    {'id': 'evt:fall_told', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'map_var': {'name': 'fell', 'equals': 1}},
     'effects': [{'set': {'var': var('fell'), 'value': 0}}, {'add': {'var': var('falls'), 'value': 1}},
                 {'message': "You went over the parapet and fell into the river below. The current tumbled you down the gorge and cast you up, half drowned, at the foot of the bluff, and you have climbed back up to the lair's mouth."}],
     'notes': "set:fall: says what happened, once the party stands at the mouth."},
    {'id': 'evt:chest_bundle', 'preset': 'chest', 'source': 'chest:bundle', 'title': 'Chest'},
    {'id': 'evt:chest_chief', 'preset': 'chest', 'source': 'chest:chief', 'title': 'Chest'},
    {'id': 'evt:chest_strongbox', 'preset': 'chest', 'source': 'chest:strongbox', 'title': 'Chest'},
    {'id': 'evt:chest_cargo', 'preset': 'chest', 'source': 'chest:cargo', 'title': 'Chest'},
]
wiring = {'format': 0, 'variables': ['gate_unbarred', 'fell', 'falls'], 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd27', 'name': 'Ogre Lair', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-27', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [17, 15], 'climbs': 'n'},
    'map_stats': {'id': 9138, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 2, 'perception_difficulty': 2,
                  'refill_days': 672, 'music': 18, 'environment': 'cave', 'lock_difficulty': 4, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Ogre', 'tier': 0, 'per_marker': [2, 3], 'weight': 60},
                            {'monster': 'Xeen Wolf', 'tier': 0, 'per_marker': [2, 3], 'weight': 25},
                            {'monster': 'Xeen Ogre', 'tier': 2, 'per_marker': [1, 2], 'weight': 15}]},
    'neighbours': [
        {'id': 'exit:x2_hills', 'to': 'xeen_x2.odm', 'kind': 'door', 'arrival': [-20992, 17155, 1248], 'direction': 270,
         'arrival_hint': "On X2, in front of the ogre lair's cave mouth in the bluff west of the north river (X2 door:xd27 at (-20992, 17555, 1216), cells [23, 29.71]), facing south, away from it.",
         'notes': "X2's final outside arrival for door:xd27 (devdocs/xeen/briefs/x2/DOORS.md, X2 finished). X2's door:xd27 lands at this map's start: (0, 448, 0), facing north."},
    ],
    'qbits': {'ogre_lair_destroyed': 110340, 'ogre_boulders_dumped': 110341, 'arrived_once': 110342},
    'items': {'larder_key': 12170},
    'notes': "Xeen design brief, level L4: L3's ogre lair built with the studio's words, a playable map (NOTES.md). Side quest Q-C23 The Ogre Boulders (Captain Nystor, X2). A map of the Xeen world: its map_stats, bolster and slot rows are the world's (source/map_rows.yml, A2), the slots here repeat them. Slot 1 Ogres (Xeen Ogre, tier a Ogre 18, 11060), slot 2 the ogres' dogs (Xeen Wolf, tier a Dark Wolf 16, 11410), slot 3 the shamans as the Ogres' tier b (Ogre Brute 22, 11061). The Ogre Chieftain is the boss row 11063 (level 24), the three Boulder Throwers Ogres (11060). The larder key is the world's item 12170. Quest bits 110340-110341 (Q-C23). Music: track 18 (caves). exit:x2_hills leads to X2 (xeen_x2.odm) at X2's final arrival for door:xd27.",
}

L4.mkdir(parents=True, exist_ok=True)
for name, doc in [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring), ('project.yml', project)]:
    (L4 / name).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))
print('written')
