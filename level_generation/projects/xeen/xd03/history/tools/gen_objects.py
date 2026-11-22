# XD-03 Deep Mine, L4: objects.yml and wiring.yml. A first-pass generator kept in the scratch folder (see NOTES.md);
# numbers are design numbers. Run: python3 gen_objects.py <L4 folder>.
import sys
import yaml

L4 = sys.argv[1]


def S(t, w=None, h=None, **kw):
    d = {'texture': t}
    if w:
        d['size'] = [w, h]
    d.update(kw)
    return d


PLANKS = S('7trimd', 128, 256)
PLANKFLOOR = S('7trimda', 256, 128)
IRON = S('ch004i', 64, 64)
SKULLDOOR = S('d2lgdor', 256, 256, fit=True)
PLANKDOOR = S('bemvwal', 128, 256, fit=True)
CRYSTAL = S('crflr3', 128, 128)
CHEST_IRON = S('ch1frntb', 64, 64)
DARKIRON = S('vlcgnrc3', 256, 256)
GEMDOOR = S('d3ystlwl', 256, 256, fit=True)

DWARF, LIEUTENANT, INFERNO_BAT = 229, 230, 207
G_KING, G_SENTRY, G_BARRACKS, G_GUARD, G_FARBANK, G_GATE, G_BATS = 1, 2, 3, 4, 5, 6, 7

start = {'room': 'room:deep_line', 'at': [8192, 1088], 'facing': 180,
         'notes': "Off the Deep Line cart at the line's foot, facing the mouth and the landing below."}

doors = [
    {'id': 'door:sentry', 'opening': 'open:sentry_door', 'kind': 'hinged', 'hinge': 'left', 'surface': PLANKDOOR,
     'notes': "The plank door from the cut into the gallery."},
    {'id': 'door:barracks_e', 'opening': 'open:barracks_doors_e', 'kind': 'hinged', 'hinge': 'right',
     'surface': SKULLDOOR, 'notes': "The barracks' heavy double door, east leaf (flung open by the alarm)."},
    {'id': 'door:barracks_w', 'opening': 'open:barracks_doors_w', 'kind': 'hinged', 'hinge': 'left',
     'surface': SKULLDOOR, 'notes': "West leaf."},
    {'id': 'door:back_stair', 'opening': 'open:back_stair_foot', 'kind': 'hinged', 'surface': PLANKDOOR,
     'notes': "The door at the back stair's foot (opened by the alarm)."},
    {'id': 'door:armoury', 'opening': 'open:armoury_door', 'kind': 'hinged', 'surface': PLANKDOOR},
    {'id': 'door:tower', 'opening': 'open:tower_door', 'kind': 'hinged', 'surface': PLANKDOOR,
     'notes': "The tower door at the top of its stair."},
    {'id': 'door:gate_e', 'opening': 'open:gate_e', 'kind': 'hinged', 'hinge': 'right', 'surface': SKULLDOOR,
     'speed': 40, 'notes': "The King's Gate, east leaf."},
    {'id': 'door:gate_w', 'opening': 'open:gate_w', 'kind': 'hinged', 'hinge': 'left', 'surface': SKULLDOOR,
     'speed': 40, 'notes': "The King's Gate, west leaf."},
    {'id': 'door:hoard', 'opening': 'open:hall_hoard', 'kind': 'hinged', 'surface': SKULLDOOR,
     'notes': "The small door behind the throne: the King's key."},
    {'id': 'door:crystal_wall', 'opening': 'open:crystal_wall', 'kind': 'slide_down', 'secret': True,
     'surface': GEMDOOR, 'speed': 48, 'notes': "The singing crystal wall: a secret wall that sinks."},
]

cart_parts = [
    {'outline': [[7072, 1000], [7088, 1000], [7088, 1176], [7072, 1176]], 'height': 56, 'notes': 'Front board'},
    {'outline': [[7088, 1000], [7296, 1000], [7296, 1016], [7088, 1016]], 'height': 40, 'notes': 'Side board'},
    {'outline': [[7088, 1160], [7296, 1160], [7296, 1176], [7088, 1176]], 'height': 40, 'notes': 'Side board'},
]
for x0 in (7096, 7232):
    for y0, y1 in ((988, 1000), (1176, 1188)):
        cart_parts.append({'outline': [[x0, y0], [x0 + 44, y0], [x0 + 44, y1], [x0, y1]], 'bottom': 372, 'height': 36,
                           'surface': IRON, 'notes': 'Wheel'})
cage_parts = []
for cx, cy in ((3688, 6952), (4120, 6952), (4120, 7384), (3688, 7384)):
    cage_parts.append({'at': [cx, cy], 'size': [16, 16], 'height': 320, 'surface': IRON, 'notes': 'Cage post'})
cage_parts += [
    {'outline': [[3680, 6944], [4128, 6944], [4128, 6960], [3680, 6960]], 'bottom': 336, 'height': 16, 'surface': IRON},
    {'outline': [[3680, 7376], [4128, 7376], [4128, 7392], [3680, 7392]], 'bottom': 336, 'height': 16, 'surface': IRON},
    {'outline': [[3680, 6960], [3696, 6960], [3696, 7376], [3680, 7376]], 'bottom': 336, 'height': 16, 'surface': IRON},
    {'outline': [[4112, 6960], [4128, 6960], [4128, 7376], [4112, 7376]], 'bottom': 336, 'height': 16, 'surface': IRON},
    {'at': [3904, 7168], 'size': [8, 448], 'bottom': 336, 'height': 16, 'surface': IRON, 'notes': 'Hanger bar'},
    {'at': [3904, 7168], 'size': [8, 8], 'bottom': 352, 'height': 1100, 'surface': IRON, 'notes': 'Chain'},
]
movers = [
    {'id': 'mover:deep_cart', 'room': 'room:deep_landing', 'at': [7184, 1088], 'size': [224, 176], 'bottom': 388,
     'height': 24, 'travel': [-768, 0, -384], 'speed': 128, 'surface': PLANKS, 'top_surface': PLANKFLOOR,
     'parts': cart_parts,
     'notes': "The Deep Line cart: a plank wagon on iron wheels at the top of the line's last pitch; stepping onto it "
              "sends it down the trestle to the buffer stop (and back up), with the party on it."},
    {'id': 'mover:gate_bar_low', 'room': 'room:kings_antechamber', 'at': [3200, 4588], 'size': [448, 24],
     'bottom': 112, 'height': 32, 'travel': [0, 0, 240], 'speed': 48, 'surface': DARKIRON, 'top_surface': DARKIRON,
     'notes': "The King's Gate's lower bar; lever A lifts it."},
    {'id': 'mover:gate_bar_high', 'room': 'room:kings_antechamber', 'at': [3200, 4588], 'size': [448, 24],
     'bottom': 240, 'height': 32, 'travel': [0, 0, 176], 'speed': 48, 'surface': DARKIRON, 'top_surface': DARKIRON,
     'notes': "The King's Gate's upper bar; lever B lifts it."},
    {'id': 'mover:cage', 'room': 'room:escape_shaft', 'at': [3904, 7168], 'size': [448, 448], 'bottom': 0,
     'height': 16, 'travel': [0, 0, 1536], 'speed': 160, 'surface': IRON, 'top_surface': PLANKFLOOR,
     'parts': cage_parts,
     'notes': "The counterweight cage: an iron frame on a plank floor that rides 1536 up to the shaft head."},
]

switches = [
    {'id': 'switch:lever_a', 'room': 'room:lever_alcove', 'wall': 'north', 'height': 112, 'size': [32, 64],
     'notes': "Lever A of the King's Gate."},
    {'id': 'switch:lever_b', 'room': 'room:furnace_tower', 'wall': 'west', 'height': 112, 'size': [32, 64],
     'notes': "Lever B of the King's Gate."},
    {'id': 'switch:shaft_lever', 'room': 'room:king_hoard', 'at': [3480, 7296], 'height': 112, 'size': [32, 64],
     'notes': "The shaft lever: releases the counterweight."},
    {'id': 'switch:cage_call', 'room': 'room:escape_shaft', 'wall': 'south', 'along': 0.6, 'height': 112,
     'notes': "Bell-pull at the shaft's foot: calls the cage down."},
    {'id': 'switch:cage_call_top', 'room': 'room:escape_shaft', 'wall': 'north', 'along': 0.1, 'height': 112,
     'floor_height': 1216, 'notes': "Bell-pull at the shaft head: calls the cage up."},
]

chests = [
    {'id': 'chest:armoury', 'room': 'room:armoury', 'at': [6100, 4650], 'treasure_level': 3,
     'random_items': 2, 'items': [72], 'gold': 60, 'notes': "Clan arms: a field hammer and two rolls."},
    {'id': 'chest:prospector', 'room': 'room:mole_warren', 'at': [4790, 520], 'size': [56, 40, 32], 'facing': 'e',
     'surface': S('7trimd', 128, 256), 'treasure_level': 2, 'random_items': 1, 'items': [222], 'gold': 100,
     'notes': "The dead prospector's pack."},
    {'id': 'chest:vault', 'room': 'room:red_dwarf_vault', 'at': [-560, 120], 'treasure_level': 3,
     'random_items': 2, 'items': [180, 178], 'gold': 150, 'notes': "Red Dwarf work: amber, iolite and two rolls."},
    {'id': 'chest:hoard_1', 'room': 'room:king_hoard', 'at': [2960, 7200], 'treasure_level': 4,
     'random_items': 3, 'items': [185], 'gold': 450, 'trap_level': 1,
     'notes': "The King's first chest: a ruby, 450 gold and three rolls; trapped."},
    {'id': 'chest:hoard_2', 'room': 'room:king_hoard', 'at': [3300, 7200], 'treasure_level': 4,
     'random_items': 4, 'gold': 350, 'trap_level': 1, 'notes': "The King's second chest: 350 gold and four rolls."},
]

spawns = [
    {'id': 'spawn:lookout', 'room': 'room:sentry_lookout', 'slot': 1, 'tier': 'a', 'notes': "Lookouts in the niche."},
    {'id': 'spawn:gallery', 'room': 'room:furnace_hall', 'at': [4900, 2900], 'floor_height': -128, 'slot': 1,
     'tier': 'a', 'notes': "Clan dwarves on the gallery."},
    {'id': 'spawn:near_bank_1', 'room': 'room:furnace_hall', 'at': [3600, 1900], 'slot': 1, 'tier': 'a',
     'notes': "Near bank, between the smelter and the channel."},
    {'id': 'spawn:near_bank_2', 'room': 'room:furnace_hall', 'at': [4500, 3000], 'slot': 1, 'tier': 'a',
     'notes': "Near bank, under the gallery."},
    {'id': 'spawn:tower', 'room': 'room:furnace_tower', 'at': [1520, 3500], 'slot': 1, 'tier': 'a',
     'notes': "Sergeants at the lever."},
    {'id': 'spawn:geode_upper', 'room': 'room:geode_grotto', 'at': [600, 2000], 'slot': 2, 'tier': 'b'},
    {'id': 'spawn:geode_lower', 'room': 'room:geode_lower', 'at': [700, 320], 'slot': 2, 'tier': 'c'},
    {'id': 'spawn:warren_west', 'room': 'room:mole_warren', 'at': [3420, 480], 'slot': 3, 'tier': 'a'},
    {'id': 'spawn:warren_east', 'room': 'room:mole_warren', 'at': [4600, 700], 'slot': 3, 'tier': 'a'},
    {'id': 'spawn:item_bunk', 'room': 'room:barracks', 'at': [5150, 4700], 'kind': 'item', 'treasure_level': 2,
     'notes': "A sergeant's purse on a bunk."},
    {'id': 'spawn:item_spoil', 'room': 'room:furnace_hall', 'at': [4560, 1700], 'kind': 'item', 'treasure_level': 2,
     'notes': "Something in the spoil by the smelter."},
    {'id': 'spawn:item_geode', 'room': 'room:geode_lower', 'at': [1100, 200], 'kind': 'item', 'treasure_level': 3,
     'notes': "Among the crystals of the lower terrace."},
]


def M(id, room, monster, at, group, **kw):
    d = {'id': id, 'room': room, 'monster': monster, 'at': at, 'hostile': True, 'group': group}
    d.update(kw)
    return d


monsters = [
    M('monster:clan_king', 'room:king_hall', LIEUTENANT, [3200, 6110], G_KING, facing=270, immobile=True, hp=300,
      name='Clan King', carries='clan_king_key',
      notes="The Clan King on the throne floor (a Dwarven Lieutenant, level 20, with 300 hit points of his own); "
            "he fights from the dais until his guard falls, then comes down (set:clan_king)."),
    M('monster:guard_1', 'room:king_hall', DWARF, [2800, 5560], G_GUARD, facing=270),
    M('monster:guard_2', 'room:king_hall', DWARF, [3600, 5560], G_GUARD, facing=270),
    M('monster:guard_3', 'room:king_hall', DWARF, [2960, 5380], G_GUARD, facing=270),
    M('monster:guard_4', 'room:king_hall', DWARF, [3440, 5380], G_GUARD, facing=270),
    M('monster:gong_sentry', 'room:furnace_hall', DWARF, [4900, 3480], G_SENTRY, floor_height=-128, facing=270,
      name='Gong Sentry', notes="The sentry at the gong (set:gong_alarm)."),
    M('monster:barracks_1', 'room:barracks', DWARF, [4160, 4600], G_BARRACKS, facing=270),
    M('monster:barracks_2', 'room:barracks', DWARF, [5184, 4600], G_BARRACKS, facing=270),
    M('monster:barracks_3', 'room:barracks', DWARF, [4160, 4100], G_BARRACKS, facing=270),
    M('monster:barracks_4', 'room:barracks', DWARF, [4672, 4130], G_BARRACKS, facing=90),
    M('monster:barracks_5', 'room:barracks', DWARF, [4900, 4600], G_BARRACKS, facing=270),
    M('monster:far_bank_1', 'room:furnace_hall', DWARF, [2900, 3500], G_FARBANK, facing=0),
    M('monster:far_bank_2', 'room:furnace_hall', DWARF, [3150, 3600], G_FARBANK, facing=0),
    M('monster:far_bank_3', 'room:furnace_hall', DWARF, [2750, 3250], G_FARBANK, facing=0),
    M('monster:gate_guard_1', 'room:kings_antechamber', DWARF, [3060, 4420], G_GATE, facing=270, immobile=True),
    M('monster:gate_guard_2', 'room:kings_antechamber', DWARF, [3340, 4420], G_GATE, facing=270, immobile=True),
    M('monster:bat_queen_1', 'room:geode_grotto', INFERNO_BAT, [760, 1560], G_BATS, hidden=True,
      notes="Bat queens hanging in the geode's crown, unseen until the party reaches the foot of the ramp."),
    M('monster:bat_queen_2', 'room:geode_grotto', INFERNO_BAT, [1000, 1900], G_BATS, hidden=True),
]

items = [
    {'id': 'item:rack_axe', 'room': 'room:armoury', 'item': 827, 'at': [6080, 4300],
     'notes': "An axe left by the south rack."},
    {'id': 'item:prospector_potion', 'room': 'room:mole_warren', 'item': 222, 'at': [4740, 470]},
    {'id': 'item:geode_garnet', 'room': 'room:geode_grotto', 'item': 177, 'at': [420, 1700],
     'notes': "A zircon fallen from a cluster."},
]


def D(id, room, deco, at=None, **kw):
    d = {'id': id, 'room': room, 'decoration': deco}
    if at:
        d['at'] = at
    d.update(kw)
    return d


decorations = [
    # arrival
    D('deco:line_lamp_1', 'room:deep_line', 'torch01', wall='north', along=0.9, height=150),
    D('deco:line_lamp_2', 'room:deep_line', 'torch01', wall='south', along=0.9, height=150),
    D('deco:buffer_lamp', 'room:deep_landing', 'torch02', wall='west', along=0.5, height=176),
    D('deco:cut_torch_1', 'room:deep_landing', 'torch01', wall='north', along=0.55, height=200),
    D('deco:ledge_lamp', 'room:deep_landing', 'torch02', wall='east', along=0.2, height=560),
    D('deco:landing_rock_1', 'room:deep_landing', '6rock01', [6400, 760]),
    D('deco:landing_rock_2', 'room:deep_landing', '6rock02', [6900, 1420]),
    D('deco:landing_bucket', 'room:deep_landing', 'Bucket', [6300, 1300]),
    D('deco:lookout_torch', 'room:sentry_lookout', 'torch01', wall='east', height=200),
    D('deco:ramp_torch', 'room:sentry_cut', 'torch01', [6200, 2860], wall='north', height=200),
    # furnace hall
    D('deco:flambeau_near_1', 'room:furnace_hall', 'flamb00', [3500, 1700]),
    D('deco:flambeau_near_2', 'room:furnace_hall', 'flamb00', [4300, 3100]),
    D('deco:flambeau_far_1', 'room:furnace_hall', 'flamb00', [2720, 2900]),
    D('deco:flambeau_far_2', 'room:furnace_hall', 'flamb00', [3500, 3700]),
    D('deco:spoil_1', 'room:furnace_hall', 'trasheap', [4500, 1780]),
    D('deco:spoil_2', 'room:furnace_hall', '7dec01', [3960, 1700]),
    D('deco:spoil_3', 'room:furnace_hall', '7dec01', [4560, 2300]),
    D('deco:hall_bucket', 'room:furnace_hall', 'Bucket', [4050, 2350]),
    D('deco:slag_lump_1', 'room:furnace_hall', '6rock01', [3300, 2000]),
    D('deco:gallery_torch_1', 'room:furnace_hall', 'TrchB00', [5120, 2800], wall='east', height=176,
      floor_height=-128),
    D('deco:gallery_torch_2', 'room:furnace_hall', 'TrchB00', [5120, 3500], wall='east', height=176,
      floor_height=-128),
    # barracks and armoury
    D('deco:barracks_torch_1', 'room:barracks', 'nwtrchnf', wall='west', height=176),
    D('deco:barracks_torch_2', 'room:barracks', 'nwtrchnf', wall='east', along=0.6, height=176),
    D('deco:barracks_torch_3', 'room:barracks', 'nwtrchnf', [4300, 4864], wall='north', height=176),
    D('deco:barracks_barrel_1', 'room:barracks', 'bigbarel', [5380, 4400]),
    D('deco:barracks_barrel_2', 'room:barracks', 'bigbarel', [3960, 4400]),
    D('deco:bowl_1', 'room:barracks', 'dec36', [4560, 4352]),
    D('deco:bowl_2', 'room:barracks', 'dec39', [4720, 4360]),
    D('deco:goblet_1', 'room:barracks', '7dec48', [4840, 4340]),
    D('deco:alcove_torch', 'room:lever_alcove', 'TrchB00', wall='east', height=176),
    D('deco:armoury_torch', 'room:armoury', 'TrchB00', wall='west', height=176),
    D('deco:armoury_barrel', 'room:armoury', 'bigbarel', [5600, 4260]),
    D('deco:armoury_cask', 'room:armoury', '7dec21', [5600, 4700]),
    # tower
    D('deco:tower_sconce_1', 'room:furnace_tower', 'scon100', wall='north', height=200),
    D('deco:tower_sconce_2', 'room:furnace_tower', 'scon100', wall='south', height=200),
    D('deco:crucible', 'room:furnace_tower', 'cauld00', [1664, 3328]),
    # antechamber and the King
    D('deco:statue_w', 'room:kings_antechamber', '7dec55', [2850, 4150], facing=0),
    D('deco:statue_e', 'room:kings_antechamber', '7dec54', [3560, 4150], facing=180),
    D('deco:gate_flambeau_w', 'room:kings_antechamber', 'flamb00', [2990, 4450]),
    D('deco:gate_flambeau_e', 'room:kings_antechamber', 'flamb00', [3410, 4450]),
    D('deco:brazier_sw', 'room:king_hall', 'brzier00', [2560, 4900]),
    D('deco:brazier_se', 'room:king_hall', 'brzier00', [3840, 4900]),
    D('deco:brazier_w1', 'room:king_hall', 'brzier00', [2180, 5800]),
    D('deco:brazier_w2', 'room:king_hall', 'brzier00', [2180, 6300]),
    D('deco:brazier_e1', 'room:king_hall', 'brzier00', [4220, 5800]),
    D('deco:brazier_e2', 'room:king_hall', 'brzier00', [4220, 6300]),
    D('deco:forge_brazier_w', 'room:king_hall', 'brzier00', [2944, 6200]),
    D('deco:forge_brazier_e', 'room:king_hall', 'brzier00', [3456, 6200]),
    D('deco:skull_pile', 'room:king_hall', 'sklplrev', [3560, 6380]),
    D('deco:king_goblets', 'room:king_hall', '7dec48', [2850, 6380]),
    D('deco:hoard_lamp', 'room:king_hoard', 'torch02', wall='west', along=0.5, height=200),
    D('deco:hoard_goblets_1', 'room:king_hoard', '7dec48', [3200, 7240]),
    D('deco:hoard_goblets_2', 'room:king_hoard', '7dec48', [3130, 7250]),
    D('deco:hoard_bowl', 'room:king_hoard', '7dec08', [2900, 6950]),
    D('deco:shaft_lamp', 'room:escape_shaft', 'torch02', [4416, 7300], wall='east', height=176, floor_height=1216),
    # caves
    D('deco:breach_rock', 'room:geode_breach', '6rock01', [2100, 1600]),
    D('deco:geode_glow_1', 'room:geode_grotto', 'crystl0', [300, 1600]),
    D('deco:geode_glow_2', 'room:geode_grotto', 'crystl0', [1200, 1500]),
    D('deco:geode_glow_3', 'room:geode_grotto', 'crystl0', [700, 2350]),
    D('deco:geode_cluster_1', 'room:geode_grotto', 'crclstr', [250, 2000]),
    D('deco:geode_cluster_2', 'room:geode_grotto', 'crys5', [1180, 2100]),
    D('deco:geode_cluster_3', 'room:geode_grotto', 'crys6', [560, 1150]),
    D('deco:stalagmite_1', 'room:geode_grotto', 'stlmite1', [1000, 1200]),
    D('deco:stalagmite_2', 'room:geode_grotto', 'stlmite2', [400, 2250]),
    D('deco:stalagmite_3', 'room:geode_grotto', 'stlmite3', [1150, 1700]),
    D('deco:geode_crystal_4', 'room:geode_grotto', 'crclstr', [220, 1560]),
    D('deco:geode_crystal_5', 'room:geode_grotto', 'crys6', [700, 2400]),
    D('deco:geode_crystal_6', 'room:geode_grotto', 'crys5', [1250, 1350]),
    D('deco:geode_glow_4', 'room:geode_grotto', 'crystl0', [180, 1800]),
    D('deco:lower_crystal_3', 'room:geode_lower', 'crys6', [250, 300]),
    D('deco:lower_crystal_4', 'room:geode_lower', 'crclstr', [1200, 350]),
    D('deco:geode_corpse', 'room:geode_grotto', 'dec05', [300, 1850]),
    D('deco:geode_bones', 'room:geode_grotto', 'dec29', [380, 1950]),
    D('deco:lower_glow', 'room:geode_lower', 'crystl0', [300, 500]),
    D('deco:lower_crystal_1', 'room:geode_lower', 'crys5', [1100, 560]),
    D('deco:lower_crystal_2', 'room:geode_lower', 'crclstr', [900, 150]),
    D('deco:memory_crystal', 'room:red_dwarf_vault', 'mcryst01', [-320, 384]),
    D('deco:prospector', 'room:mole_warren', 'dec05', [4720, 560]),
    D('deco:prospector_bones', 'room:mole_warren', '7dec18', [4640, 640]),
    D('deco:warren_dirt_1', 'room:mole_warren', '7dec01', [3500, 200]),
    D('deco:warren_dirt_2', 'room:mole_warren', '6rock02', [4300, 760]),
    D('deco:warren_rock', 'room:mole_warren', '6rock01', [4000, 700]),
]

# Gem clusters: tapering crystal points (platforms with ids, so they can be hidden once prised out)
clusters = {
    1: ('room:geode_grotto', (360, 1300)),
    2: ('room:geode_grotto', (1180, 1850)),
    3: ('room:geode_grotto', (900, 2300)),
    4: ('room:geode_lower', (500, 160)),
}
cluster_platforms = {}
for n, (room_id, (cx, cy)) in clusters.items():
    plats = []
    for k, (dx, dy, w, h) in enumerate([(0, 0, 40, 112), (36, 20, 28, 80), (-30, 24, 24, 64)]):
        plats.append({'id': f'platform:cluster_{n}_{k}', 'at': [cx + dx, cy + dy], 'size': [w, w],
                      'top_size': [4, 4], 'rise': h, 'surface': CRYSTAL, 'top_surface': CRYSTAL,
                      'notes': f"Gem cluster {n}" + (" (clicked)" if k == 0 else "")})
    cluster_platforms[n] = (room_id, plats)


def light(id, room, at, height, radius, color, **kw):
    d = {'id': id, 'room': room, 'at': at, 'height': height, 'radius': radius, 'color': color}
    d.update(kw)
    return d


ORANGE, SLAG, GOLDEN, BLUE, PALE = [255, 150, 70], [255, 90, 25], [255, 190, 110], [90, 150, 255], [200, 220, 255]
lights = [
    light('light:ledge', 'room:deep_landing', [7480, 1088], 192, 700, GOLDEN),
    light('light:buffer', 'room:deep_landing', [6380, 1088], 200, 700, GOLDEN),
    light('light:landing_mid', 'room:deep_landing', [6900, 900], 300, 600, [200, 150, 110]),
    light('light:smelter_mouth', 'room:furnace_hall', [4224, 2300], 96, 900, SLAG,
          pulse={'intensity': [0.6, 1.0], 'radius': [760, 900], 'frequency': 0.4}),
]
slag_points = [(2720, 2200), (3050, 2530), (3400, 2880), (3700, 3180), (4000, 3480), (4220, 3640)]
for i, (x, y) in enumerate(slag_points):
    lights.append(light(f'light:slag_{i + 1}', 'room:furnace_hall', [x, y], 48, 800, SLAG,
                        pulse={'intensity': [0.55, 1.0], 'frequency': 0.3, 'phase': round(i * 0.17, 2)},
                        notes="Slag glow low over the channel, no visible source."))
for i, (x, y) in enumerate([(3500, 1700), (4300, 3100), (2720, 2900), (3500, 3700)]):
    lights.append(light(f'light:flambeau_{i + 1}', 'room:furnace_hall', [x, y], 112, 600, ORANGE,
                        pulse={'intensity': [0.8, 1.0], 'frequency': 1.3, 'phase': round(i * 0.3, 2)}))
lights += [
    light('light:gallery', 'room:furnace_hall', [4920, 3100], 200, 600, GOLDEN, floor_height=-128),
    light('light:barracks_1', 'room:barracks', [4100, 4352], 300, 700, GOLDEN, on=False),
    light('light:barracks_2', 'room:barracks', [5200, 4352], 300, 700, GOLDEN, on=False),
    light('light:barracks_3', 'room:barracks', [4672, 4700], 300, 700, GOLDEN, on=False),
    light('light:alcove', 'room:lever_alcove', [4672, 5040], 200, 400, GOLDEN),
    light('light:armoury', 'room:armoury', [5800, 4480], 260, 700, GOLDEN),
    light('light:tower_1', 'room:furnace_tower', [1664, 3600], 220, 600, ORANGE),
    light('light:tower_2', 'room:furnace_tower', [1664, 3060], 220, 600, ORANGE),
    light('light:crucible', 'room:furnace_tower', [1664, 3328], 64, 400, SLAG,
          pulse={'intensity': [0.4, 0.9], 'frequency': 0.25}),
    light('light:gate_w', 'room:kings_antechamber', [2990, 4450], 112, 650, ORANGE,
          pulse={'intensity': [0.8, 1.0], 'frequency': 1.2}),
    light('light:gate_e', 'room:kings_antechamber', [3410, 4450], 112, 650, ORANGE,
          pulse={'intensity': [0.8, 1.0], 'frequency': 1.2, 'phase': 0.4}),
    light('light:statues', 'room:kings_antechamber', [3200, 4000], 300, 600, [180, 140, 110]),
    light('light:dome', 'room:king_hall', [3200, 5728], 1000, 1100, PALE,
          pulse={'intensity': [0.5, 0.9], 'radius': [900, 1100], 'frequency': 0.15},
          notes="Glitter in the crystal dome."),
    light('light:hall_south', 'room:king_hall', [3200, 5000], 400, 900, GOLDEN),
    light('light:forge_w', 'room:king_hall', [2944, 6200], 120, 600, ORANGE,
          pulse={'intensity': [0.8, 1.0], 'frequency': 1.1}, notes="The west forge brazier's fire."),
    light('light:forge_e', 'room:king_hall', [3456, 6200], 120, 600, ORANGE,
          pulse={'intensity': [0.8, 1.0], 'frequency': 1.1, 'phase': 0.5}, notes="The east forge brazier's fire."),
    light('light:gutter_w', 'room:king_hall', [1984, 6032], 48, 800, SLAG, on=False,
          pulse={'intensity': [0.6, 1.0], 'frequency': 0.35}, notes="Slag in the west gutter (the King's wrath)."),
    light('light:gutter_e', 'room:king_hall', [4416, 6032], 48, 800, SLAG, on=False,
          pulse={'intensity': [0.6, 1.0], 'frequency': 0.35, 'phase': 0.5}),
    light('light:wrath', 'room:king_hall', [3200, 5728], 300, 1300, [255, 60, 20], on=False,
          pulse={'intensity': [0.5, 0.9], 'frequency': 0.5}, notes="The hall turns slag red in the second phase."),
    light('light:hoard', 'room:king_hoard', [3200, 6900], 260, 700, GOLDEN),
    light('light:shaft_head', 'room:escape_shaft', [4288, 7168], 160, 700, PALE, floor_height=1216,
          notes="Daylight at the shaft head."),
    light('light:shaft_foot', 'room:escape_shaft', [3904, 7168], 200, 500, [160, 140, 120]),
    light('light:geode_1', 'room:geode_grotto', [300, 1600], 96, 700, BLUE,
          pulse={'intensity': [0.4, 1.0], 'frequency': 0.2}),
    light('light:geode_2', 'room:geode_grotto', [1200, 1500], 96, 700, BLUE,
          pulse={'intensity': [0.4, 1.0], 'frequency': 0.2, 'phase': 0.33}),
    light('light:geode_3', 'room:geode_grotto', [700, 2350], 96, 700, BLUE,
          pulse={'intensity': [0.4, 1.0], 'frequency': 0.2, 'phase': 0.66}),
    light('light:geode_crown', 'room:geode_grotto', [768, 1760], 700, 900, [120, 200, 255],
          pulse={'intensity': [0.3, 0.7], 'frequency': 0.1}),
    light('light:geode_lower', 'room:geode_lower', [300, 500], 96, 700, BLUE,
          pulse={'intensity': [0.4, 1.0], 'frequency': 0.25}),
    light('light:breach', 'room:geode_breach', [2300, 1700], 200, 500, [170, 130, 100]),
    light('light:vault', 'room:red_dwarf_vault', [-320, 384], 160, 700, [120, 255, 170],
          pulse={'intensity': [0.5, 1.0], 'frequency': 0.3}, notes="The memory crystal over the rune ring."),
    light('light:warren', 'room:mole_warren', [4720, 560], 120, 380, [130, 110, 90], notes="A dim glow by the corpse."),
]

exits = [
    {'id': 'exit:deep_cart', 'room': 'room:deep_line', 'wall': 'east', 'size': [224, 256], 'to': 'exit:deep_cart',
     'surface': S('c2b', 256, 256), 'notes': "The Deep Line runs on up into the dark: back to the Red Dwarf Mines."},
    {'id': 'exit:x1', 'room': 'room:escape_shaft', 'wall': 'east', 'floor_height': 1216, 'size': [192, 256],
     'to': 'exit:x1_shaft', 'surface': S('c2b', 256, 256),
     'notes': "The shaft head's hatch: up to the hills north of Vertigo."},
]

floors = [{'id': 'floor:slag', 'of': 'level:slag', 'kind': 'lava'}]
placeholders = [
    {'id': 'placeholder:rack_south', 'room': 'room:armoury', 'at': [6120, 4288], 'size': [192, 32, 224],
     'stands_for': "A dwarven weapon rack with axes and hammers hanging on it (the two rails are built; the weapons are missing)"},
    {'id': 'placeholder:rack_north', 'room': 'room:armoury', 'at': [6120, 4672], 'size': [192, 32, 224],
     'stands_for': "A dwarven weapon rack with axes and hammers hanging on it"},
    {'id': 'placeholder:gong_model', 'room': 'room:furnace_hall', 'at': [4912, 3640], 'size': [240, 32, 320],
     'stands_for': "A great bronze gong in a timber frame with a swing clip (built of six copper slabs until a model exists)"},
    {'id': 'placeholder:cart_model', 'room': 'room:deep_landing', 'at': [7184, 1088], 'size': [224, 176, 96],
     'stands_for': "A dwarven ore cart riding the mover (built of planks until a model can ride a mover)"},
]

objects = {'format': 0, 'start': start, 'doors': doors, 'movers': movers, 'switches': switches, 'chests': chests,
           'spawns': spawns, 'monsters': monsters, 'items': items, 'decorations': decorations, 'lights': lights,
           'exits': exits, 'floors': floors, 'placeholders': placeholders,
           'notes': "Objects of the L4 brief (first written by output/studio_cal/xd03/tools/gen_objects.py). "
                    "Stand-ins: Mad Dwarves and Clan Sergeants are MM7 Dwarven Soldiers (229, level 10), the Clan King "
                    "a Dwarven Lieutenant (230, level 20) with 300 hit points and a name, the Bat Queens Inferno Bats "
                    "(207, level 9); slots 1 Dwarf, 2 Spider (tier 3), 3 Troglodyte (the tiger moles)."}

# ------------------------------------------------------------------------------------------------------- wiring
alarm_effects = [
    {'lights_on': ['light:barracks_1', 'light:barracks_2', 'light:barracks_3']},
    {'lua': 'evt.CameraShake(0.4, 0.8)'},
]
alarm_doors = ['door:barracks_e', 'door:barracks_w', 'door:back_stair']
events = [
    {'id': 'evt:clan_hostile', 'preset': 'script', 'trigger': 'load',
     'effects': [{'lua': 'evt.SetMonsterRelation(229, 0, 4); evt.SetMonsterRelation(230, 0, 4); '
                         'evt.SetMonsterRelation(231, 0, 4)'}],
     'notes': "The Mad Dwarf Clan is hostile: MM7's Dwarf family (the stand-in) is the party's ally in hostile.txt, "
              "and no word says a map's own relations (XD-02's gap 1), so a load event sets the three Dwarf rows "
              "hostile. Gone with a real Mad Dwarf row."},
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'load', 'once': True,
     'text': "Hot air rises up the Deep Line: below, the Mad Dwarf Clan's hold glows red."},
    # the Deep Line cart and the way back
    {'id': 'evt:deep_cart', 'preset': 'switch', 'trigger': 'step', 'source': 'mover:deep_cart',
     'toggles': ['mover:deep_cart'], 'text': "The cart lurches over the lip and rumbles along the Deep Line's last pitch.",
     'notes': "Stepping onto the cart sends it down the trestle to the buffer stop, or back up to the line's foot."},
    {'id': 'evt:exit_cart', 'preset': 'exit', 'source': 'exit:deep_cart', 'title': "The Deep Line: up to the Red Dwarf Mines",
     'text': "You climb into a cart and haul on the brake rope: the Deep Line carries you back up to the Red Dwarf Mines."},
    # doors
    {'id': 'evt:door_sentry', 'preset': 'door', 'source': 'door:sentry', 'title': 'Plank door'},
    {'id': 'evt:door_barracks_e', 'preset': 'door', 'source': 'door:barracks_e', 'title': 'Heavy doors',
     'toggles': ['door:barracks_w']},
    {'id': 'evt:door_barracks_w', 'preset': 'door', 'source': 'door:barracks_w', 'title': 'Heavy doors',
     'toggles': ['door:barracks_e']},
    {'id': 'evt:door_back_stair', 'preset': 'door', 'source': 'door:back_stair', 'title': 'Plank door'},
    {'id': 'evt:door_armoury', 'preset': 'door', 'source': 'door:armoury', 'title': 'Armoury door'},
    {'id': 'evt:door_tower', 'preset': 'door', 'source': 'door:tower', 'title': 'Tower door'},
    {'id': 'evt:gate_e', 'preset': 'door', 'source': 'door:gate_e', 'title': "The King's Gate", 'action': 'open',
     'condition': {'all': [{'map_var': 'gate_bar_a'}, {'map_var': 'gate_bar_b'}]},
     'locked_text': "The gate is barred from within.", 'opens': ['door:gate_w'],
     'text': "The King's Gate swings open."},
    {'id': 'evt:gate_w', 'preset': 'door', 'source': 'door:gate_w', 'title': "The King's Gate", 'action': 'open',
     'condition': {'all': [{'map_var': 'gate_bar_a'}, {'map_var': 'gate_bar_b'}]},
     'locked_text': "The gate is barred from within.", 'opens': ['door:gate_e'],
     'text': "The King's Gate swings open."},
    {'id': 'evt:door_hoard', 'preset': 'door', 'source': 'door:hoard', 'title': 'Small iron door', 'action': 'open',
     'condition': {'item': 'clan_king_key'}, 'locked_text': "A small iron door with the King's own lock."},
    {'id': 'evt:crystal_wall', 'preset': 'door', 'source': 'door:crystal_wall', 'title': 'Crystal wall',
     'action': 'open', 'text': "The crystal wall hums under your hand, rings like a bell, and sinks into the floor."},
    # the King's Gate puzzle
    {'id': 'evt:lever_a', 'preset': 'switch', 'source': 'switch:lever_a', 'title': 'Lever', 'once': True,
     'opens': ['mover:gate_bar_low'], 'sets': {'map_var': 'gate_bar_a'},
     'text': "The lever drops with a clank; far off, something heavy grinds upward."},
    {'id': 'evt:lever_b', 'preset': 'switch', 'source': 'switch:lever_b', 'title': 'Lever', 'once': True,
     'opens': ['mover:gate_bar_high'], 'sets': {'map_var': 'gate_bar_b'},
     'text': "The lever drops with a clank; far off, something heavy grinds upward."},
    # the gong alarm
    {'id': 'evt:gong', 'preset': 'script', 'source': 'platform:gong', 'title': 'The great gong',
     'condition': {'not': {'map_var': 'alarm_rung'}}, 'opens': alarm_doors,
     'effects': [{'set': {'var': {'map_var': 'alarm_rung'}, 'value': 1}}] + alarm_effects,
     'else_effects': [{'text': "The gong still hums."}],
     'text': "BOOM! The great gong rolls through the hold. Doors crash open in the barracks.",
     'notes': "poi:gong / set:gong_alarm: rung by the party, the barracks doors burst open and its torches are lit."},
    {'id': 'evt:sentry_seen', 'preset': 'script', 'trigger': 'step', 'source': 'level:gallery', 'once': True,
     'effects': [{'set': {'var': {'map_var': 'sentry_alert'}, 'value': 1}}],
     'notes': "The party comes onto the gallery: the gong sentry has seen it."},
    {'id': 'evt:sentry_count', 'preset': 'script', 'trigger': 'timer', 'every': 2,
     'condition': {'all': [{'map_var': 'sentry_alert'}, {'not': {'kills': {'monster': 'monster:gong_sentry'}}},
                           {'not': {'map_var': 'alarm_rung'}}]},
     'effects': [{'add': {'var': {'map_var': 'sentry_count'}, 'value': 1}}],
     'notes': "Counts the seconds the sentry lives after seeing the party."},
    {'id': 'evt:sentry_rings', 'preset': 'script', 'trigger': 'timer', 'every': 2,
     'condition': {'all': [{'map_var': {'name': 'sentry_count', 'at_least': 3}},
                           {'not': {'kills': {'monster': 'monster:gong_sentry'}}},
                           {'not': {'map_var': 'alarm_rung'}}]},
     'opens': alarm_doors,
     'effects': [{'set': {'var': {'map_var': 'alarm_rung'}, 'value': 1}}] + alarm_effects,
     'text': "The sentry hammers the great gong! Doors crash open in the barracks.",
     'notes': "set:gong_alarm: about six seconds after seeing the party, if still alive, the sentry rings the gong."},
    # the slag channel burns by its lava flag (objects.yml floors); the King
    {'id': 'evt:kings_wrath', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'all': [{'kills': {'group': G_GUARD}}, {'not': {'kills': {'monster': 'monster:clan_king'}}}]},
     'effects': [
         {'set': {'var': {'map_var': 'kings_wrath'}, 'value': 1}},
         {'set_texture': {'of': 'platform:gutter_w', 'to': 'orfyrlga'}},
         {'set_texture': {'of': 'platform:gutter_e', 'to': 'orfyrlga'}},
         {'lights_off': ['light:forge_w', 'light:forge_e', 'light:hall_south']},
         {'lights_on': ['light:gutter_w', 'light:gutter_e', 'light:wrath']},
         {'lua': 'evt.CameraShake(1.0, 1.5)'},
     ],
     'text': "The Clan King roars and kicks over the forge braziers: slag pours hissing into the gutters!",
     'notes': "set:clan_king, state:kings_wrath: when his guard has fallen (the brief: at half his health, which no "
              "word can test) the forge braziers go dark, the gutters fill with slag (harmful floor by the timer below) "
              "and the King leaves the dais."},
    {'id': 'evt:gutter_in', 'preset': 'script', 'trigger': 'step', 'source': 'platform:gutter_w',
     'sources': ['platform:gutter_e'], 'effects': [{'set': {'var': {'map_var': 'in_gutter'}, 'value': 1}}]},
    {'id': 'evt:gutter_out', 'preset': 'script', 'trigger': 'step', 'source': 'room:king_hall',
     'sources': ['level:dais'], 'effects': [{'set': {'var': {'map_var': 'in_gutter'}, 'value': 0}}]},
    {'id': 'evt:gutter_burn', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'all': [{'map_var': 'kings_wrath'}, {'map_var': 'in_gutter'}]},
     'effects': [{'damage': {'amount': 8, 'kind': 'fire'}}], 'text': "The slag in the gutter burns!"},
    {'id': 'evt:king_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:clan_king'}},
     'effects': [{'qbit': 'clan_king_slain'}],
     'text': "The Clan King falls across his anvil. The Mad Dwarf Clan is broken.",
     'notes': "goal:clan_king: his death sets the quest bit; Mayor Gunther in Vertigo rewards it."},
    # the hoard and the shaft
    {'id': 'evt:shaft_lever', 'preset': 'switch', 'source': 'switch:shaft_lever', 'title': 'Shaft lever', 'once': True,
     'effects': [{'qbit': 'escape_shaft_open'}, {'lua': 'evt.CameraShake(0.5, 1.0)'}],
     'text': "The lever comes over: a chain runs out with a roar somewhere above. The cage in the shaft is free.",
     'notes': "goal:escape_shaft / poi:shaft_lever."},
    {'id': 'evt:cage', 'preset': 'switch', 'source': 'mover:cage', 'title': 'Counterweight cage',
     'condition': {'qbit': 'escape_shaft_open'},
     'locked_text': "The cage will not move: its counterweight is chained fast.", 'toggles': ['mover:cage'],
     'text': "The counterweight drops past you in the dark and the cage creaks up the shaft."},
    {'id': 'evt:cage_call', 'preset': 'switch', 'source': 'switch:cage_call', 'title': 'Bell-pull',
     'condition': {'qbit': 'escape_shaft_open'}, 'locked_text': "The bell rings; the cage does not come.",
     'closes': ['mover:cage'], 'text': "The cage comes down the shaft."},
    {'id': 'evt:cage_call_top', 'preset': 'switch', 'source': 'switch:cage_call_top', 'title': 'Bell-pull',
     'condition': {'qbit': 'escape_shaft_open'}, 'locked_text': "The bell rings; the cage does not come.",
     'opens': ['mover:cage'], 'text': "The cage comes up the shaft."},
    {'id': 'evt:exit_x1', 'preset': 'exit', 'source': 'exit:x1', 'title': "The shaft head: the hills north of Vertigo",
     'condition': {'qbit': 'escape_shaft_open'}, 'locked_text': "The hatch is barred from outside.",
     'text': "You push up the hatch: daylight, wind and the hills north of Vertigo."},
    # the caves
    {'id': 'evt:bats_drop', 'preset': 'script', 'trigger': 'step', 'source': 'room:geode_descent', 'once': True,
     'effects': [{'show_actors': G_BATS}], 'text': "Leathery wings unfold in the geode's crown!",
     'notes': "The bat queens drop on the party at the foot of the ramp."},
    {'id': 'evt:lectern', 'preset': 'script', 'source': 'platform:lectern', 'title': 'Stone lectern',
     'effects': [{'message': "Cut in the old runes of the Red Dwarves: HERE BRAKKA THE FIRST CUT THE DEEP GALLERY AND "
                              "FOUND THE RED SEAM UNDER THE SINGING STONE. THE SEAM RUNS NORTH UNDER THE HILLS TO THE "
                              "FALL OF WATER. KEEP THE FIRE, KEEP THE SEAM, KEEP FAITH."},
                 {'set': {'var': {'map_var': 'history_read'}, 'value': 1}}],
     'notes': "poi:history_tablet: the history of the mine (an autonote when the Xeen world has one)."},
    {'id': 'evt:statue_w', 'preset': 'text', 'source': 'deco:statue_w', 'title': 'Statue of a Red Dwarf king',
     'text': "A Red Dwarf king in stone. The clan has hacked his face away."},
    {'id': 'evt:statue_e', 'preset': 'text', 'source': 'deco:statue_e', 'title': 'Statue of a Red Dwarf king',
     'text': "A Red Dwarf king in stone. The clan has hacked his face away."},
]
gems = [177, 178, 179, 180]
for n, (room_id, plats) in cluster_platforms.items():
    events.append({'id': f'evt:cluster_{n}', 'preset': 'script', 'source': plats[0]['id'], 'title': 'Crystal cluster',
                   'once': True,
                   'effects': [{'give_item': {'one_of': gems}}] + [{'hide': p['id']} for p in plats] +
                              [{'passable': p['id']} for p in plats],
                   'text': "You prise a gem out of the cluster; the rest crumbles to glittering dust.",
                   'notes': "poi:gem_clusters: one low gem each, once; the cluster is gone afterwards."})
for c in chests:
    titles = {'chest:armoury': 'Weapon chest', 'chest:prospector': "Prospector's pack", 'chest:vault': 'Red Dwarf chest',
              'chest:hoard_1': "The King's chest", 'chest:hoard_2': "The King's chest"}
    events.append({'id': 'evt:' + c['id'].replace(':', '_'), 'preset': 'chest', 'source': c['id'],
                   'title': titles[c['id']]})

wiring = {'format': 0,
          'variables': ['gate_bar_a', 'gate_bar_b', 'alarm_rung', 'sentry_alert', 'sentry_count', 'kings_wrath',
                        'in_gutter', 'history_read'],
          'events': events,
          'notes': "Every mechanism is a preset with conditions and effects. Lua only where no word fits: the clan's "
                   "hostility (evt.SetMonsterRelation on load) and the camera shakes (evt.CameraShake)."}

for room_id, plats in cluster_platforms.values():
    pass

with open(L4 + '/objects.yml', 'w') as f:
    yaml.safe_dump(objects, f, sort_keys=False, width=120, default_flow_style=None)
with open(L4 + '/wiring.yml', 'w') as f:
    yaml.safe_dump(wiring, f, sort_keys=False, width=120, default_flow_style=None)

# the cluster platforms belong in rooms.yml: append them to their rooms
with open(L4 + '/rooms.yml') as f:
    rooms_doc = yaml.safe_load(f)
for r in rooms_doc['rooms']:
    if 'platforms' in r:
        r['platforms'] = [p for p in r['platforms'] if not str(p.get('id', '')).startswith('platform:cluster_')]
for room_id, plats in cluster_platforms.values():
    for r in rooms_doc['rooms']:
        if r['id'] == room_id:
            r['platforms'] = r.get('platforms', []) + plats
with open(L4 + '/rooms.yml', 'w') as f:
    yaml.safe_dump(rooms_doc, f, sort_keys=False, width=120, default_flow_style=None)
