#!/usr/bin/env python3
"""XD-21 Robbers' Den: writes the brief's plan.yml, diagram.txt and (L1-L3) project.yml for L1, L2, L3 and L4.
L1 is the plan (spaces, links, goals, set pieces); L2 adds each space's theme, light, palette and furniture; L3 adds
the sketch (rooms.yml, written by gen.py --l3); L4's plan is L3's. Rerun after a change, then v.sh."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd21'

DIAGRAM = r"""                                   (river)
                       ||||  river grate  ||||
 [Bunk room $]--door--[ SLUICE: catwalk over the race ]--door(LOCK)--[Fence's store $]
       |                  |  race  |         \ arch
     door                 |  ~~~~  |          \
       |              =grate=====grate=        \
 [Dicing room]--arch--[ UNDERCROFT of the great bridge ]--arch--[Boss's stair]--door--[ROBBER BOSS $]
       |               west bank | ~race~ | east bank                                  |  catch lever
     door                        |<=plank bridge (winch, east)                  [Strongroom passage: 3 dart slabs]
       |                         =grate (out)=                                         |
 [Robbers' crawl: tripwire]                                                      =IRON DOOR (boss's keys)=
       |                                                                          [VAULT: the tiara $$]
     #secret block (wet footprints)
       |
 [Quay cellar ~drain grate]
       |
   quay door -> X2 south quay, under the great bridge

 # secret   $ chest   ~ water   Loop: dicing - undercroft (west) - plank bridge - undercroft (east) - sluice - bunks.
"""

project_l1 = {
    'format': 0, 'id': 'xeen_xd21', 'name': "Robbers' Den", 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-21', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [16, 14], 'climbs': 's'},
    'map_stats': {'id': 9137, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 3, 'perception_difficulty': 5,
                  'refill_days': 672, 'music': 'dungeon_dark', 'environment': 'stone hall', 'lock_difficulty': 5,
                  'slots': [{'monster': 'Outlaws', 'tier': 2, 'per_marker': [2, 3], 'weight': 60},
                            {'monster': 'Robbers', 'tier': 2, 'per_marker': [2, 3], 'weight': 40}]},
    'neighbours': [
        {'id': 'door:xd21', 'to': 'X2', 'kind': 'door',
         'arrival_hint': "On Rivercity's south quay under the great bridge's south end, in front of the den's door in the quay wall, facing the river.",
         'notes': "X2 owns the door (devdocs/xeen/briefs/x2/DOORS.md): a dark door in the south quay's retaining wall beside the bridge's south abutment."},
    ],
    'qbits': {'tiara_recovered': 110300, 'robber_boss_slain': 110301, 'robbers_den_found': 110302,
              'robbers_vault_opened': 110303},
    'items': {'roxannes_tiara': 12150, 'ring_of_keys': 12151},
    'notes': "Xeen design brief, level L1, for a new map. Side quest Q-C3 (Princess Roxanne's tiara, given at Castle Burlock) and the first-tier promotion T1-E (Thief to Rogue, given by Roxanne when the tiara comes back). MAPS.md: class S, monsters 10-18 in groups of 2-3, treasure level 2, 28 monsters; party 9 to 11. Encounter slots are Xeen families (MONSTERS_AND_ITEMS.md): 1 Outlaws (Rogue 12, Thief 18), 2 Robbers (Xeen's Robber, a brawler at 14, a split of the Outlaws for the den). Ids: map_stats 9137, qbits 110300-110339, items 12150-12169 (devdocs/xeen/ACT2_BUILD.md).",
}


def sp(id, name, size, extent, shape, where, floor, clear, relief, purpose, **kw):
    d = {'id': id, 'name': name, 'kind': 'room', 'size': size, 'extent': extent, 'shape': shape, 'where': where,
         'floor': floor, 'clear_height': clear, 'relief': relief, 'purpose': purpose}
    d.update(kw)
    return d


spaces = [
    sp('room:quay_cellar', 'Quay cellar', 'M', [1280, 1024],
       "A low barrel-vaulted cellar behind the quay wall: the quay door in its south wall, a drain basin in one corner where the river laps in under a low grate. Apparently a dead end.",
       "South edge, behind Rivercity's south quay.", 0, [448, 576], 'flat',
       "Arrival and the X2 exit. The hidden way in: wet footprints lead to a worn block in the north wall (a secret door).",
       empty=True, safe=True),
    sp('room:crawl', "Robbers' crawl", 'S', [256, 2300],
       "A narrow brick passage behind the secret block, straight north, low.", "North of the cellar.", 0, 288, 'flat',
       "The hidden way to the den; a tripwire with a crossbow halfway along.", empty=True,
       features=[{'kind': 'trap', 'where': 'Halfway along', 'notes': 'A tripwire fires a bolt once (secret: a perceptive party sees it).'}]),
    sp('room:dicing_room', 'Dicing room', 'M', [1536, 1280],
       "The robbers' common room under a brick vault: a dicing table with benches in the middle, kegs along the walls, the gang's dues box on the west wall.",
       "West of the undercroft.", 0, [448, 576], 'flat',
       "The first fight: rogues at their dice. Arches east onto the undercroft's west bank; a door north to the bunks.",
       population=[{'slot': 1, 'groups': 2, 'per_marker': [2, 3], 'rank': 'a', 'levels': [12, 12], 'strength': 'pack',
                    'notes': 'Rogues at the dicing table.'}]),
    sp('room:bunk_room', 'Bunk room', 'M', [1536, 1024],
       "Plank bunks round the walls; a loose brick behind one hides a purse.", "North of the dicing room.", 0, 416, 'flat',
       "Robbers asleep; a small find (the loose brick); the way on to the sluice chamber.",
       population=[{'slot': 1, 'groups': 2, 'per_marker': [2, 3], 'rank': 'a', 'levels': [12, 12], 'strength': 'light', 'notes': 'Asleep until disturbed.'}],
       treasure=[{'kind': 'secret_container', 'count': 1, 'tier': 2, 'notes': 'A purse of 150 gold behind a loose brick (a secret panel).'}]),
    sp('room:undercroft', 'Undercroft of the great bridge', 'XL', [2816, 1792],
       "The hollow inside the great bridge's south abutment under one tall barrel arch, four pier buttresses in its corners; the race (a mill race taken off the river) cuts it north to south, 512 wide and 224 down, between iron grates; the robbers' plank bridge is drawn back to the east bank.",
       "Centre of the map.", 0, [640, 1088], 'pit',
       "The set piece: the den under the bridge. The race splits the hall; the party reaches the east bank by the sluice chamber's catwalk and runs the plank bridge out by its winch (the loop back west). Carts rumble overhead; the river is heard through the grates.",
       features=[{'kind': 'channel', 'rise': -224, 'where': 'North to south through the middle', 'notes': 'The race, flowing; seven water stairs up onto the west bank at its south end.'},
                 {'kind': 'drawbridge', 'where': 'Across the race at the middle', 'notes': 'A plank bridge on rollers, run out by a winch on the east bank.'}],
       population=[{'slot': 2, 'groups': 1, 'per_marker': [2, 3], 'rank': 'b', 'levels': [14, 14], 'strength': 'pack', 'notes': 'Raiders on the west bank.'},
                   {'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'rank': 'a', 'levels': [12, 12], 'strength': 'pack', 'notes': 'Rogues on the east bank, out of reach until the party crosses.'}]),
    sp('room:sluice', 'Sluice chamber', 'L', [2176, 1024],
       "A vaulted chamber where the race comes in through a tall river grate; the old sluice wall across the race is planked over as a catwalk.",
       "North of the undercroft.", 0, [512, 704], 'pit',
       "The way across the race; the river's roar and daylight through the grate. The bunk room's door on the west bank; an arch south into the undercroft's east half and the fence's locked door on the east bank.",
       population=[{'slot': 2, 'groups': 1, 'per_marker': [2, 3], 'rank': 'b', 'levels': [14, 14], 'strength': 'pack', 'notes': 'Raiders guarding the catwalk.'}]),
    sp('room:fence_store', "Fence's store", 'M', [1024, 1024],
       "A brick store behind a good lock: crates and sacks of goods stolen in Rivercity, a counting table, the fence's chest.",
       "North-east, off the sluice chamber.", 0, 384, 'flat',
       "Optional: the fence's men and his chest. The lock opens to the boss's keys or to a thief's skill.",
       population=[{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'rank': 'a', 'levels': [12, 12], 'strength': 'pack'}],
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 2, 'items': [2, 2], 'notes': 'Trapped; 350 gold.'}]),
    sp('room:boss_stair', "Boss's stair", 'S', [1280, 512], "Eight steps up east from the undercroft to the boss's door.",
       "East of the undercroft.", [0, 256], 448, 'steps', "The approach to the boss; voices behind the door.",
       population=[{'slot': 2, 'groups': 1, 'per_marker': [2, 3], 'rank': 'b', 'levels': [14, 14], 'strength': 'pack', 'notes': 'At the foot of the stair.'}]),
    sp('room:boss_quarters', "Robber Boss's quarters", 'M', [1408, 1280],
       "The boss's rooms under a brick vault, 256 up: desk with his ledger, bed, supper table, a hearth on the north wall with the strongroom catch beside it.",
       "East edge.", 256, [576, 704], 'flat',
       "The Robber Boss, his two bodyguards and his lieutenants; his chest; the ledger that tells of the strongroom's darts and the catch.",
       population=[{'actor': 'Robber Boss', 'role': 'boss', 'groups': 1, 'levels': [18, 18], 'placed': True, 'strength': 'boss',
                    'notes': "Carries the vault's ring of keys. A boss row (Thief 18, three times the hit points)."},
                   {'actor': 'Robber', 'role': 'bodyguard', 'groups': 2, 'levels': [14, 14], 'placed': True, 'strength': 'heavy'},
                   {'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'rank': 'b', 'levels': [18, 18], 'strength': 'heavy', 'notes': "Thieves, the boss's lieutenants."}],
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 2, 'items': [2, 2], 'notes': 'Trapped; 400 gold.'}]),
    sp('room:strongroom_walk', 'Strongroom passage', 'S', [320, 1280], "A straight stone passage north to the vault; three slabs in its floor.",
       "North of the boss's quarters.", 256, 320, 'flat',
       "A trap the game explains: each slab fires darts from the walls until the catch in the boss's room is thrown (his ledger says so).",
       empty=True),
    sp('room:vault', 'Vault', 'S', [896, 768], "The gang's strongroom behind an iron door with three locks: the strongbox on a plinth, sacks of takings.",
       "North-east corner.", 256, [448, 544], 'flat', "The goal: Princess Roxanne's tiara in the strongbox (the map's hoard).",
       empty=True, treasure=[{'kind': 'chest', 'count': 1, 'tier': 3, 'items': [2, 2], 'notes': "The tiara, 800 gold; trapped."}]),
]

L2_LOOK = {
    'room:quay_cellar': ("stone: the bridge's dressed blocks (d01 twb2) on the walls, flagstones (cfb1), a rough stone vault (cwb)",
                         "grey daylight round the quay door; light off the water in the drain basin; one wall torch",
                         ["bigbarel: a barrel", "7dec10: washed-up rubbish", "Bucket: a bucket by the drain", "torch01: wall torch"],
                         ["the drain basin's stone kerb", "the low river grate (xngrille) standing in the basin"]),
    'room:crawl': ("brick: d01's small dark brick (wall)", "one wall torch at the far end; dark", ["dec29: bones"], []),
    'room:dicing_room': ("brick, with plank furniture (MM7's chest planks 7gt002)", "candles on the table, a lamp on a side table, two wall torches",
                         ["cndlab0: candles", "7dec46, 7dec48: goblets", "dec36: wood plate", "smlbarel: kegs", "7dec21: cask", "7dec32: barrel"],
                         ["dicing table and two benches", "a side table", "the dues box on the west wall"]),
    'room:bunk_room': ("brick, plank bunks", "one candle stick; dim", ["bag01: sack", "foodbowl: bowl", "trasheap: rubbish", "dec02: candle stick"],
                       ["four plank bunks", "the loose brick (secret)"]),
    'room:undercroft': ("stone: twb2 blocks, the race's slime water (7slimywtr, d01's)", "two torch pools on the banks, light off the water; carts' rumble",
                        ["torch01: four wall torches", "bigbarel, 7dec32: barrels", "floursac, bag_A: sacks", "7dec01: rubbish", "7dec21: cask"],
                        ["four pier buttresses", "the plank bridge and its winch post", "iron grates where the race comes in and goes out", "water stairs"]),
    'room:sluice': ("stone, the race", "daylight through the river grate; one torch a side", ["torch01: wall torches", "7dec10: rubbish"],
                    ["the river grate", "the sluice wall's planked catwalk with a rail"]),
    'room:fence_store': ("brick, plank crates", "a candle on the counting table", ["floursac, bag01, bag_A: sacks", "bigbarel: barrel", "cndlab0: candle", "dec39: metal plates"],
                         ["crates", "counting table"]),
    'room:boss_stair': ("brick, stone steps", "one wall torch", [], []),
    'room:boss_quarters': ("brick, plank furniture", "the hearth's fire, a chandelier, a candle on the desk, two torches",
                           ["ckfyr00: hearth fire", "dec27: chandelier", "cndlab0: candle", "7dec46: goblet", "7dec08: fruit bowl", "7dec21: cask"],
                           ["desk with the ledger", "bed", "supper table", "hearth", "the catch lever"]),
    'room:strongroom_walk': ("stone, three darker slabs (d01 tfb07)", "one torch", ["Corpse03: a robber who forgot the catch"], ["three dart slabs"]),
    'room:vault': ("stone", "a lamp over the strongbox, two torches", ["bag01, bag_A: sacks of takings", "7dec32: barrel"], ["the plinth"]),
}

regions = [
    {'id': 'region:way_in', 'name': 'The way in', 'spaces': ['room:quay_cellar', 'room:crawl'], 'theme': "Wet dressed stone behind the quay; a hidden brick passage"},
    {'id': 'region:den', 'name': "The robbers' den", 'spaces': ['room:dicing_room', 'room:bunk_room', 'room:fence_store'], 'theme': "Damp brick, plank furniture, candlelight"},
    {'id': 'region:bridge', 'name': 'Under the bridge', 'spaces': ['room:undercroft', 'room:sluice'], 'theme': "The bridge's masonry, the race, grates, the river's roar"},
    {'id': 'region:boss', 'name': "The boss's wing", 'spaces': ['room:boss_stair', 'room:boss_quarters', 'room:strongroom_walk', 'room:vault'], 'theme': "Brick and stone, firelight, the strongroom"},
]


def lk(id, a, b, kind, **kw):
    d = {'id': id, 'from': a, 'to': b, 'kind': kind}
    d.update(kw)
    return d


links = [
    lk('link:cellar_crawl', 'room:quay_cellar', 'room:crawl', 'secret_door', motion='slide',
       notes="A worn block of the cellar's north wall slides aside; wet footprints lead to it."),
    lk('link:crawl_dicing', 'room:crawl', 'room:dicing_room', 'door', motion='swing'),
    lk('link:dicing_undercroft', 'room:dicing_room', 'room:undercroft', 'open', notes="An arch onto the race's west bank."),
    lk('link:dicing_bunks', 'room:dicing_room', 'room:bunk_room', 'door', motion='swing'),
    lk('link:bunks_sluice', 'room:bunk_room', 'room:sluice', 'door', motion='swing', notes="Onto the sluice chamber's west bank."),
    lk('link:sluice_undercroft', 'room:sluice', 'room:undercroft', 'open', notes="East of the race: an arch down into the undercroft's east half."),
    lk('link:sluice_fence', 'room:sluice', 'room:fence_store', 'door', motion='swing',
       condition={'any': [{'item': 'ring_of_keys'}, {'stat': {'name': 'DisarmTrapSkill', 'at_least': 3}}]},
       notes="Locked: the boss's keys, or a thief's skill picks it."),
    lk('link:undercroft_stair', 'room:undercroft', 'room:boss_stair', 'open'),
    lk('link:stair_boss', 'room:boss_stair', 'room:boss_quarters', 'door', motion='swing'),
    lk('link:boss_strongroom', 'room:boss_quarters', 'room:strongroom_walk', 'open'),
    lk('link:strongroom_vault', 'room:strongroom_walk', 'room:vault', 'door', motion='slide',
       condition={'item': 'ring_of_keys'}, notes="The iron door with three locks: the Robber Boss's ring of keys."),
]

plan_l1 = {
    'format': 0, 'level': 'L1',
    'pitch': "Rivercity's robber gang lives inside the great bridge. A dark door in the south quay's wall opens on a cellar that seems a dead end until wet footprints lead to a worn block that slides aside. A hidden passage, a tripwire, and then the den: a dicing room, bunks, and the undercroft of the bridge's south abutment under one tall arch, split by a mill race that runs between iron grates, the river roaring in through them and carts rumbling overhead. The robbers keep their plank bridge drawn back to the far bank; the way across is the old sluice wall in the chamber where the race comes in. On the far side the Robber Boss keeps his rooms and his strongroom: a passage of dart slabs, an iron door with three locks, and in the strongbox Princess Roxanne's diamond tiara.",
    'purpose': "Side quest Q-C3: recover Princess Roxanne's tiara (given at Castle Burlock; she rewards the party and promotes its Thieves to Rogues, T1-E). Kill the Robber Boss for the vault's keys. Monster levels 10 to 18 (Outlaws, Robbers), 28 monsters, treasure level 2 with a hoard at 3 in the vault. A party of about level 9 to 11; 15 to 20 minutes.",
    'mood': "Damp stone and the river: water lapping, dripping, the race's rush; the robbers' candlelight in the brick rooms; daylight through the river grate; the bridge's weight overhead.",
    'datum': 'arrival',
    'spaces': spaces,
    'regions': regions,
    'links': links,
    'loops': [{'id': 'loop:bridge', 'spaces': ['room:dicing_room', 'room:undercroft', 'room:sluice', 'room:bunk_room'],
               'closed_until': {'map_var': 'bridge_out'},
               'notes': "Across by the sluice catwalk, back by the plank bridge once its winch is worked: the short way back west to the cellar."}],
    'entrances': [{'id': 'entrance:quay', 'space': 'room:quay_cellar', 'kind': 'both', 'neighbour': 'door:xd21', 'facing': 'n',
                   'how': "Inside the quay door, facing in; the river's light behind."}],
    'critical_path': ['room:quay_cellar', 'room:crawl', 'room:dicing_room', 'room:bunk_room', 'room:sluice', 'room:undercroft',
                      'room:boss_stair', 'room:boss_quarters', 'room:strongroom_walk', 'room:vault'],
    'return_path': ['room:vault', 'room:strongroom_walk', 'room:boss_quarters', 'room:boss_stair', 'room:undercroft',
                    'room:dicing_room', 'room:crawl', 'room:quay_cellar'],
    'goals': [
        {'id': 'goal:tiara', 'space': 'room:vault', 'kind': 'take', 'what': "Princess Roxanne's diamond tiara, in the gang's strongbox.",
         'story': 'Q-C3', 'handed_in_at': 'XD-07', 'gives': {'qbit': 'tiara_recovered'},
         'notes': "Roxanne (Castle Burlock) takes it, pays (item T3) and promotes the party's Thieves to Rogues (T1-E); she gives a copy of the tiara back as thanks (MONSTERS_AND_ITEMS 4.2)."},
        {'id': 'goal:robber_boss', 'space': 'room:boss_quarters', 'kind': 'kill', 'what': 'The Robber Boss, who carries the keys of the vault.',
         'gives': {'qbit': 'robber_boss_slain'}},
    ],
    'keys': [{'id': 'key:ring_of_keys', 'grants': {'item': 'ring_of_keys'}, 'found_in': 'room:boss_quarters',
              'how': "Carried by the Robber Boss; left in his corpse."}],
    'containers': [{'id': 'container:strongbox', 'kind': 'chest', 'tier': 3, 'items': [2, 2], 'notes': "Princess Roxanne's tiara (roxannes_tiara), 800 gold and two items of level 3."}],
    'points_of_interest': [
        {'id': 'poi:footprints', 'space': 'room:quay_cellar', 'kind': 'clue', 'behaviour': "Stepping to the north wall: 'Wet footprints lead from the drain to the north wall and stop dead at the stones.'"},
        {'id': 'poi:winch', 'space': 'room:undercroft', 'kind': 'winch', 'behaviour': 'Runs the plank bridge out across the race (once; it stays out).',
         'uses': {'times': 1, 'per': 'party', 'reset': 'never'}, 'gives': {'map_var': 'bridge_out'}},
        {'id': 'poi:ledger', 'space': 'room:boss_quarters', 'kind': 'book', 'behaviour': "The boss's ledger: the tiara 'not to be fenced', and the strongroom's catch."},
        {'id': 'poi:catch', 'space': 'room:boss_quarters', 'kind': 'lever', 'behaviour': "Locks the strongroom passage's darts.",
         'uses': {'times': 1, 'per': 'party', 'reset': 'never'}, 'gives': {'map_var': 'catch_thrown'}},
        {'id': 'poi:loose_brick', 'space': 'room:bunk_room', 'kind': 'cache', 'behaviour': 'A purse of 150 gold behind a loose brick (secret).'},
        {'id': 'poi:dues_box', 'space': 'room:dicing_room', 'kind': 'joke', 'behaviour': "Empty: 'What did you expect, money?'"},
    ],
    'landmarks': [{'id': 'landmark:race', 'space': 'room:undercroft', 'what': "The race running dark under the bridge's great arch between its grates, the plank bridge drawn back.",
                   'seen_from': ['room:dicing_room', 'room:sluice']}],
    'sightlines': [{'id': 'sightline:undercroft', 'from': 'room:dicing_room', 'to': ['landmark:race'],
                    'what': "Through the arch: the race, the far bank with the boss's stair, the plank bridge drawn back out of reach."}],
    'set_pieces': [
        {'id': 'set:drawbridge', 'kind': 'scripted', 'spaces': ['room:undercroft'],
         'rule': "The plank bridge is drawn back to the east bank. Its winch is on the east bank; once run out it stays.",
         'inputs': ['the winch'], 'states': ['drawn back', 'out'], 'gives': {'map_var': 'bridge_out'}},
        {'id': 'set:strongroom_traps', 'kind': 'trap', 'spaces': ['room:strongroom_walk', 'room:boss_quarters'],
         'rule': "Each of three slabs in the passage fires darts at the whole party, every time, until the catch by the hearth is thrown. The ledger on the boss's desk says so.",
         'inputs': ['the catch'], 'states': ['armed', 'locked'], 'solution': 'Read the ledger; throw the catch.'},
        {'id': 'set:tripwire', 'kind': 'trap', 'spaces': ['room:crawl'], 'rule': 'A tripwire fires a bolt once.'},
        {'id': 'set:robber_boss', 'kind': 'boss', 'spaces': ['room:boss_quarters'],
         'rule': "The Robber Boss and his two bodyguards hold his rooms; his lieutenants come from the far end. He carries the ring of keys.",
         'population': [{'actor': 'Robber Boss', 'role': 'boss', 'groups': 1, 'levels': [18, 18], 'placed': True, 'strength': 'boss'}]},
    ],
    'mechanisms': [
        {'kind': 'secret sliding block', 'count': 1}, {'kind': 'tripwire', 'count': 1},
        {'kind': 'plank bridge on a winch (stretching mover)', 'count': 1}, {'kind': 'dart slabs disarmed by a catch lever', 'count': 3},
        {'kind': 'locked door (key or a thief)', 'count': 1}, {'kind': 'iron door with the boss\'s keys', 'count': 1},
        {'kind': 'trapped chest', 'count': 3},
    ],
    'height_bands': [
        {'id': 'band:race', 'range': [-224, -224], 'spaces': [], 'partly': ['room:undercroft', 'room:sluice']},
        {'id': 'band:den', 'range': [0, 0], 'spaces': ['room:quay_cellar', 'room:crawl', 'room:dicing_room', 'room:bunk_room', 'room:fence_store'],
         'partly': ['room:undercroft', 'room:sluice', 'room:boss_stair']},
        {'id': 'band:boss', 'range': [256, 256], 'spaces': ['room:boss_quarters', 'room:strongroom_walk', 'room:vault'], 'partly': ['room:boss_stair']},
    ],
    'diagram': {'file': 'diagram.txt'},
    'totals': {'chests': 3, 'critical_path_length': 9000, 'doors': 7, 'fixed_actors': 3, 'floor_area_munits2': 17,
               'height_range': 480, 'loops': 1, 'monsters_about': 28, 'rooms': 11, 'secret_faces': 5, 'sectors': 12,
               'spawn_points': 10, 'traps': 4},
    'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters): 11 rooms, about 17 M units², 28 monsters (10 spawn points of 2-3 and the boss with two bodyguards). Shipped S comparators: MM7's Erathian Sewers is the thieves' set (texture family), Zokarr's Tomb 12 sectors / 7 M / 18 monsters, the Wine Cellar 10 / 7 / 23; MM7 S medians 8 sectors, 12 M, 22 monsters, 2 chests, 6 doors. Traps and locks MM6-MM8 style: a secret door found by its clue or by Perception, a tripwire, dart slabs whose catch the boss's ledger names, a lock a thief can pick, an iron door for the boss's keys, trapped chests. No riddles.",
}


def plan_for(level):
    p = copy.deepcopy(plan_l1)
    p['level'] = 'L3' if level == 'L4' else level
    if level != 'L1':
        for s in p['spaces']:
            theme, light, palette, furniture = L2_LOOK[s['id']]
            s['theme'] = theme
            s['light'] = light
            if palette:
                s['palette'] = palette
            if furniture:
                s['furniture'] = furniture
    if level in ('L3', 'L4'):
        p['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return p


for level in ('L1', 'L2', 'L3', 'L4'):
    d = BRIEF / level
    d.mkdir(parents=True, exist_ok=True)
    (d / 'plan.yml').write_text(yaml.safe_dump(plan_for(level), sort_keys=False, allow_unicode=True, width=120))
    (d / 'diagram.txt').write_text(DIAGRAM)
    if level != 'L4':
        pj = copy.deepcopy(project_l1)
        pj['notes'] = pj['notes'].replace('level L1', f'level {level}')
        (d / 'project.yml').write_text(yaml.safe_dump(pj, sort_keys=False, allow_unicode=True, width=120))
print('plans written')
