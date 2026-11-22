#!/usr/bin/env python3
"""Writes DD-17 Castle Alamar's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd17/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act5_graphs/dd17.graph.yml with decider D-61,
mockups/act5_a8_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
objects.yml, wiring.yml and atmosphere.yml (dress.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/dd17'


class D(yaml.SafeDumper):
    pass


def _flow_list(dumper, data):
    flow = all(not isinstance(x, (dict, list)) for x in data) or all(
        isinstance(x, list) and all(not isinstance(y, (dict, list)) for y in x) for x in data)
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=flow)


D.add_representer(list, _flow_list)


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, Dumper=D, sort_keys=False, allow_unicode=True, width=120)


# Rows (assets_dev/worlds/xeen/source/monsters.yml, A2)
PATROL, ANNIHILATOR, AUTOBOT = 11610, 11611, 11612
FIRE_EL, AIR_EL, WATER_EL, EARTH_EL = 11620, 11624, 11625, 11626
GAZER = 11572
SHELTEM, CORAK = 11924, 11912
LEVEL = {PATROL: 50, ANNIHILATOR: 62, AUTOBOT: 75, FIRE_EL: 55, AIR_EL: 55, WATER_EL: 55, EARTH_EL: 55, GAZER: 65,
         SHELTEM: 90, CORAK: 50}

# D6 (installed, A6): entrance:dd17_gate (-6656, 4608, 2208) facing 1536 (assets_dev/worlds/xeen/maps/xeen_d6.studio.yml).
D6_GATE = 'entrance:dd17_gate'
D6_SETDOWN = (-6656, 4608, 2208, 1536)
# D7 (installed by A6 04:53): entrance:dd17_roof (-18688, 8448, 1536) facing 1024 (xeen_d7.studio.yml).
D7_ROOF = 'entrance:dd17_roof'
D7_SETDOWN = (-18688, 8448, 1536, 1024)

QBITS = {
    # the map's own (block 117600-117639, A3 registers)
    'dd17_arrived_once': 117600, 'head_fire_off': 117601, 'head_air_off': 117602, 'head_water_off': 117603,
    'head_earth_off': 117604, 'vault_open': 117605, 'come_to_me': 117606,
    # A3's M33 and Q-D26 bits read here (the hooks set them)
    'm33_inside': 111660, 'm33_gate_open': 111661, 'm33_done': 111662, 'm33_sundial_nine': 111663,
    'm33_refused_once': 111664, 'q_d26_roof_unlocked': 113521,
    # A3's helper's per-dial bits (m33.sundials, the map reads them for the slabs)
    'dial_fire_nine': 117611, 'dial_air_nine': 117612, 'dial_water_nine': 117613, 'dial_earth_nine': 117614,
}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-17 Castle Alamar (the source's dark maze0049-0051: Castle Alamar Levels 1-3) "
    "as one BLV of three floors 640 apart on D6's mesa. Story M33 (A3's hooks m33.arrival, m33.sundials through "
    "Xeen.alamarSundial, m33.true_name_gate, m33.true_name_wrong, m33.sheltem) and Q-D26's roof hatch "
    "(q-d26.alamar_hatch). Class L: 50-75 sectors, 120-200 M units squared, four set pieces (the conveyor works, the "
    "dial hall, the trapdoor deck, Command Central), doors up to 25 (24; the four bridge slabs are mechanisms). Party "
    "52-55, monsters 50-75, no boss. Graph devdocs/xeen/mockups/act5_graphs/dd17.graph.yml with decider D-61 "
    "(mockups/act5_a8_decisions.md, which wins): plate rides on the belts (Q11), four xafield leaves dropped by the "
    "Lava Heads (Q12), one two-state bridge slab per ring at nine with the dial's line (Q13), the hatch both ways "
    "while the castle stands (Q14), Sheltem 11924 and Corak 11912 placed hidden and shown by the cinematic (Q15), the "
    "dais plate asks first (Q16), the leave to D6's entrance:dd17_gate (Q17), six trapdoors to the chasm floor (Q18), "
    "the Power Juice +2 Might (Q19, A3's hook pending), 70 monsters (Q20): Patrol 11610 50 x30, Annihilator 11611 62 "
    "x20, Autobot 11612 75 x6, Lesser Fire 11620 / Air 11624 / Water 11625 / Earth 11626 Elemental 55 x2 each, Gamma "
    "Gazer 11572 65 x6; kill XP 275,380 for the party, 68.85k per member. Rest encounters 10 % robots Dif 2 (Q21, = "
    "A2's row 9170). Treasure 5 (the strongroom's hoard 6). Map qbits 117600-117639 (117600-117606 used); map_stats "
    "9170, music 50.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd17', 'name': 'Castle Alamar', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-17', 'new': False, 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [16, 16], 'climbs': 'n'},
        'map_stats': {
            'id': 9170, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 5, 'trap_dice': 8,
            'perception_difficulty': 15, 'refill_days': 672, 'music': 50, 'environment': 'stoneroom',
            'lock_difficulty': 15,
            # D-61 Q21: one slot, the robots at Dif 2 (= A2's row 9170: Xeen Robot, Dif 2, 1-2)
            'slots': [{'monster': 'Xeen Robot', 'tier': 2, 'per_marker': [1, 2], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d6_gate', 'to': 'xeen_d6.odm', 'kind': 'door', 'arrival': D6_GATE,
             'arrival_hint': "On D6's approach before Castle Alamar's gate, facing south away from it (A6's entrance:dd17_gate, (-6656, 4608, 2208) facing 1536).",
             'notes': "D6's door:dd17 (A6) names this map's entrance:d6_gate. The exit preset, m33.arrival's refusal and the leave after the cinematic all land at entrance:dd17_gate (D-61 Q17)."},
            {'id': 'exit:d7_roof', 'to': 'xeen_d7.blv', 'kind': 'door', 'arrival': D7_ROOF,
             'arrival_hint': "On Castle Alamar's roof on D7's Skyroads, beside the hatch (A6's entrance:dd17_roof, (-18688, 8448, 1536) facing 1024).",
             'notes': "Q-D26's roof hatch (D-58, D-61 Q14): q-d26.alamar_hatch first ('Bolted from above.' until roof_unlocked 113521), then the exit preset. D7 installed 04:53 (A6); its door:dd17 names this map's entrance:d7_roof."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


P, A, AU, G = PATROL, ANNIHILATOR, AUTOBOT, GAZER
# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    # L1
    'gatehall': ("Gatehall", 'room', 'M', 'L1',
                 "The arrival (entrance:d6_gate) behind the gate; m33.arrival on every entry until m33.done: false moves the party back to D6. Quiet (D-11.3).",
                 [], [], {'empty': True}),
    'hall_order': ("Hall of Order", 'room', 'L', 'L1',
                   "Pillared hall: the first propaganda statue against the north wall (aaze0049:2, a step plate before it); the wards west and east, the stair hall's leaves north.",
                   [placed(P, 3), placed(A, 1, 'heavy')], [], {}),
    'west_ward': ("West ward", 'corridor', 'M', 'L1', "Junction of the fire and water belts' mouths, the barracks and the west return.",
                  [placed(P, 2), placed(A, 1, 'heavy')], [], {}),
    'east_ward': ("East ward", 'corridor', 'M', 'L1', "The air and earth belts, the moat watch, the parts store, the east return.",
                  [placed(P, 2), placed(A, 1, 'heavy')], [], {}),
    'barracks': ("Robot barracks", 'room', 'M', 'L1', "Dead end with a chest: charging racks along the walls.",
                 [placed(P, 2), placed(A, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
    'watch_se': ("Moat watch", 'room', 'S', 'L1', "Dead end with a chest: a Gazer at the slit over the gate road.",
                 [placed(P, 2), placed(G, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
    'store_ne': ("Parts store", 'room', 'S', 'L1', "Dead end with a chest: crates of plates and rollers (a storeroom).",
                 [placed(A, 2, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {'store': True}),
    'belt_fire': ("Fire belt", 'corridor', 'M', 'L1', "Conveyor hall: the mouth plate carries the party to the far end (D-61 Q11); walking back carries it forward again.",
                  [], [], {'empty': True}),
    'head_fire': ("Fire Head", 'room', 'M', 'L1', "The belt's end: the Fire Lava Head ('Fire power field operational.', aaze0049:7; 'Shut the field down?'); the maintenance door to the west return opens from this side.",
                  [placed(FIRE_EL, 2, 'heavy')], [], {'goal': True}),
    'belt_fire_end': ("Fire belt's end", 'corridor', 'S', 'L1', "The fire belt's last stretch before the Head, where the ride sets the party down.", [], [], {'empty': True}),
    'belt_water': ("Water belt", 'corridor', 'M', 'L1', "Conveyor hall, as the fire belt.", [], [], {'empty': True}),
    'belt_water_end': ("Water belt's end", 'corridor', 'S', 'L1', "The water belt's last stretch.", [], [], {'empty': True}),
    'head_water': ("Water Head", 'room', 'M', 'L1', "The Water Lava Head (aaze0049:9).", [placed(WATER_EL, 2, 'heavy')], [],
                   {'goal': True}),
    'return_w': ("West return", 'corridor', 'M', 'L1', "Maintenance gallery behind the two west Heads, back to the west ward; its doors into the Head rooms are bolted on the Heads' side.",
                 [placed(P, 2)], [], {}),
    'belt_air': ("Air belt", 'corridor', 'M', 'L1', "Conveyor hall.", [], [], {'empty': True}),
    'belt_air_end': ("Air belt's end", 'corridor', 'S', 'L1', "The air belt's last stretch.", [], [], {'empty': True}),
    'head_air': ("Air Head", 'room', 'M', 'L1', "The Air Lava Head (aaze0049:8).", [placed(AIR_EL, 2, 'heavy')], [],
                 {'goal': True}),
    'belt_earth': ("Earth belt", 'corridor', 'M', 'L1', "Conveyor hall.", [], [], {'empty': True}),
    'belt_earth_end': ("Earth belt's end", 'corridor', 'S', 'L1', "The earth belt's last stretch.", [], [], {'empty': True}),
    'head_earth': ("Earth Head", 'room', 'M', 'L1', "The Earth Lava Head (aaze0049:10).", [placed(EARTH_EL, 2, 'heavy')], [],
                   {'goal': True}),
    'return_e': ("East return", 'corridor', 'M', 'L1', "The east maintenance gallery, as the west.", [placed(P, 2)], [], {}),
    'stair_hall': ("Stair hall", 'room', 'M', ['L1', 'L2'], "Behind the Hall of Order's leaves: the stair up to the south walk; the sump's door opens into it from the sump's side.",
                   [placed(A, 2, 'heavy'), placed(AU, 1, 'heavy')], [], {}),
    'sump': ("The sump", 'room', 'M', 'L1', "Beside the dial hall's chasm floor: bent plates, the bones of earlier callers and a find; its door to the stair hall opens from inside (a lever by it).",
             [], [], {'empty': True}),
    # L2
    'landing_w': ("South walk, west", 'corridor', 'M', 'L2', "The outer walk's south side toward the south-west bay.", [placed(P, 1)], [], {}),
    'landing': ("South walk", 'room', 'M', 'L2', "The stair head from L1, on the outer walk's south side.", [placed(P, 1)], [], {}),
    'bay_sw': ("South-west bay", 'room', 'S', 'L2', "Corner of the outer walk; the water field closes the sundial alcove.",
               [placed(P, 2)], [], {}),
    'dial_water': ("Water Time", 'room', 'S', 'L2', "Sundial alcove behind the water field (dropped by the Water Head): Xeen.alamarSundial(\"water\", ...), starts 7.",
                   [], [], {'empty': True, 'goal': True}),
    'west_walk': ("West walk", 'corridor', 'M', 'L2', "The outer walk's west side: the dial hall's lip, the bridge line east across the four chasms to the island.",
                  [placed(P, 1), placed(A, 2, 'heavy')], [], {}),
    'bay_nw': ("North-west bay", 'room', 'S', 'L2', "Corner; the fire field closes its sundial.", [placed(P, 2)], [], {}),
    'dial_fire': ("Fire Time", 'room', 'S', 'L2', "Sundial behind the fire field, starts 3.", [], [], {'empty': True, 'goal': True}),
    'north_walk': ("North walk", 'corridor', 'M', 'L2', "The second propaganda statue (aaze0049:3).",
                   [placed(A, 2, 'heavy'), placed(G, 1, 'heavy')], [], {}),
    'bay_ne': ("North-east bay", 'room', 'S', 'L2', "Corner; the air field closes its sundial.", [placed(P, 2)], [], {}),
    'dial_air': ("Air Time", 'room', 'S', 'L2', "Sundial behind the air field, starts 6.", [], [], {'empty': True, 'goal': True}),
    'east_walk': ("East walk", 'corridor', 'M', 'L2', "The outer walk's east side; the watchers' post opens off it.",
                  [placed(P, 2), placed(A, 1, 'heavy')], [], {}),
    'gazer_post': ("Watchers' post", 'room', 'S', 'L2', "Dead end with a chest.", [placed(G, 2, 'heavy'), placed(A, 1, 'heavy')],
                   [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
    'bay_se': ("South-east bay", 'room', 'S', 'L2', "Corner; the earth field closes its sundial.", [placed(P, 2)], [], {}),
    'dial_earth': ("Earth Time", 'room', 'S', 'L2', "Sundial behind the earth field, starts 12.", [], [], {'empty': True, 'goal': True}),
    'rings': ("Dial hall", 'room', 'L', ['L1', 'L2'], "Four ring chasms round the gate island (the island merged in: the crackling statue and the true-name gate on it, two Autobots); one bridge slab per chasm on the west line, level only while its dial reads nine; the chasm floor runs out to the sump.",
              [placed(AU, 2, 'heavy', notes='on the gate island')], [], {'goal': True}),
    'lift_core': ("Lift core", 'room', 'S', 'L2', "Behind the gate: the lift up to the deck; it runs only once gate_open is set.",
                  [], [], {'empty': True}),
    # L3
    'lift_top': ("Deck lift head", 'room', 'S', 'L3', "The lift's top on the deck's east edge.", [], [], {'empty': True}),
    'deck': ("Command deck", 'room', 'L', 'L3', "Over the dial hall: six hatched plates (xatrapplt) are trapdoors to the chasm floor (1,280); the first by the lift head has a hover.",
             [placed(P, 2), placed(A, 2, 'heavy'), placed(AU, 1, 'heavy')], [], {}),
    'robot_bay': ("Robot bay", 'room', 'M', 'L3', "Dead end with a chest and the vault release lever (one-way, 117605).",
                  [placed(A, 2, 'heavy'), placed(AU, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
    'gazer_watch': ("Screen room", 'room', 'S', 'L3', "Wall screens showing the Forbidden Zone; a chest; a back door to the hatch room.",
                    [placed(G, 2, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
    'west_hall': ("Hall of Vengeance", 'room', 'M', 'L3', "The third propaganda statue (aaze0049:4); a step plate once: 'A voice bellows, \"Come to ME!\"' (aaze0051:2; 117606).",
                  [placed(A, 2, 'heavy'), placed(AU, 1, 'heavy')], [], {}),
    'juice': ("Power juice", 'room', 'S', 'L3', "Dead end: the dispenser labelled 'XEEN Power Juice' (aaze0051:0); +2 Might once per character (D-61 Q19), A3's hook pending.",
              [], [], {'empty': True}),
    'hatch_room': ("Hatch room", 'room', 'S', 'L3', "The ladder up the shaft to the roof hatch (q-d26.alamar_hatch); the arrival from D7 (entrance:d7_roof) at the ladder's foot; quiet.",
                   [], [], {'empty': True}),
    'antechamber': ("Antechamber", 'room', 'S', 'L3', "Before Command Central's two leaves (hover 'Command Central', aaze0051:3); the strongroom's door.",
                    [], [], {'empty': True}),
    'vault': ("Strongroom", 'room', 'S', 'L3', "The hoard (T6), opened by the robot bay's lever.", [],
              [{'kind': 'chest', 'count': 1, 'tier': 6}], {'empty': True}),
    'command': ("Command Central", 'room', 'L', 'L3', "Sheltem's throne on a dais under the screens; the dais plate asks 'Before the throne. Open the Soul Box?' first; Yes: m33.sheltem, the cinematic (Sheltem and Corak shown), the leave to D6.",
                [], [], {'empty': True, 'goal': True}),
    'command_apse': ("Command Central, the throne apse", 'room', 'S', 'L3', "Sheltem's throne on its dais under the bank of machines; Sheltem and Corak placed hidden.", [], [], {'empty': True}),
    'command_bay': ("Command Central, the machine bay", 'room', 'S', 'L3', "Consoles and screens at Command Central's east end.", [], [], {'empty': True}),
}
FLOORS = {'L1': geo.L1, 'L2': geo.L2, 'L3': geo.L3}

LINKS = [
    ('link:gate_hall', 'gatehall', 'hall_order', 'door', {'purpose': "The inner leaves (two)."}),
    ('link:hall_ww', 'hall_order', 'west_ward', 'open', {}),
    ('link:hall_ew', 'hall_order', 'east_ward', 'open', {}),
    ('link:hall_stair', 'hall_order', 'stair_hall', 'door', {'purpose': "Two leaves."}),
    ('link:ww_barracks', 'west_ward', 'barracks', 'door', {}),
    ('link:ew_watch', 'east_ward', 'watch_se', 'door', {}),
    ('link:ew_store', 'east_ward', 'store_ne', 'door', {}),
    ('link:ww_bfire', 'west_ward', 'belt_fire', 'open', {}),
    ('link:ww_bwater', 'west_ward', 'belt_water', 'open', {}),
    ('link:ew_bair', 'east_ward', 'belt_air', 'open', {}),
    ('link:ew_bearth', 'east_ward', 'belt_earth', 'open', {}),
    ('link:bfire_end', 'belt_fire', 'belt_fire_end', 'open', {}),
    ('link:bwater_end', 'belt_water', 'belt_water_end', 'open', {}),
    ('link:bair_end', 'belt_air', 'belt_air_end', 'open', {}),
    ('link:bearth_end', 'belt_earth', 'belt_earth_end', 'open', {}),
    ('link:land_w', 'landing_w', 'landing', 'open', {}),
    ('link:command_apse', 'command', 'command_apse', 'open', {}),
    ('link:command_bay', 'command', 'command_bay', 'open', {}),
    ('link:bfire_head', 'belt_fire_end', 'head_fire', 'open', {'purpose': "The belt carries the party one way (plate rides)."}),
    ('link:bwater_head', 'belt_water_end', 'head_water', 'open', {'purpose': "The belt (plate rides)."}),
    ('link:bair_head', 'belt_air_end', 'head_air', 'open', {'purpose': "The belt (plate rides)."}),
    ('link:bearth_head', 'belt_earth_end', 'head_earth', 'open', {'purpose': "The belt (plate rides)."}),
    ('link:hfire_ret', 'head_fire', 'return_w', 'door', {'purpose': "Bolted on the Head's side."}),
    ('link:hwater_ret', 'head_water', 'return_w', 'door', {'purpose': "Bolted on the Head's side."}),
    ('link:hair_ret', 'head_air', 'return_e', 'door', {'purpose': "Bolted on the Head's side."}),
    ('link:hearth_ret', 'head_earth', 'return_e', 'door', {'purpose': "Bolted on the Head's side."}),
    ('link:retw_ww', 'return_w', 'west_ward', 'open', {}),
    ('link:rete_ew', 'return_e', 'east_ward', 'open', {}),
    ('link:sump_stair', 'sump', 'stair_hall', 'door', {'purpose': "Opens from the sump's side (a lever by it)."}),
    ('link:stair_up', 'stair_hall', 'landing', 'stairs', {}),
    ('link:land_sw', 'landing_w', 'bay_sw', 'open', {}),
    ('link:land_se', 'landing', 'bay_se', 'open', {}),
    ('link:sw_ww', 'bay_sw', 'west_walk', 'open', {}),
    ('link:ww_nw', 'west_walk', 'bay_nw', 'open', {}),
    ('link:nw_nwalk', 'bay_nw', 'north_walk', 'open', {}),
    ('link:nwalk_ne', 'north_walk', 'bay_ne', 'open', {}),
    ('link:ne_ewalk', 'bay_ne', 'east_walk', 'open', {}),
    ('link:ewalk_se', 'east_walk', 'bay_se', 'open', {}),
    ('link:ewalk_post', 'east_walk', 'gazer_post', 'door', {}),
    ('link:sw_dial', 'bay_sw', 'dial_water', 'door', {'opened_by': 'key:head_water', 'purpose': "The water field."}),
    ('link:nw_dial', 'bay_nw', 'dial_fire', 'door', {'opened_by': 'key:head_fire', 'purpose': "The fire field."}),
    ('link:ne_dial', 'bay_ne', 'dial_air', 'door', {'opened_by': 'key:head_air', 'purpose': "The air field."}),
    ('link:se_dial', 'bay_se', 'dial_earth', 'door', {'opened_by': 'key:head_earth', 'purpose': "The earth field."}),
    ('link:ww_rings', 'west_walk', 'rings', 'open', {'purpose': "Onto the dial hall's lip; the bridges east (dials at nine) to the island."}),
    ('link:rings_sump', 'rings', 'sump', 'open', {'purpose': "The chasm floor runs out into the sump."}),
    ('link:island_lift', 'rings', 'lift_core', 'door', {'opened_by': 'goal:gate', 'purpose': "The true-name gate (two leaves)."}),
    ('link:lift_up', 'lift_core', 'lift_top', 'lift', {}),
    ('link:lift_deck', 'lift_top', 'deck', 'open', {}),
    ('link:deck_bay', 'deck', 'robot_bay', 'door', {}),
    ('link:deck_screen', 'deck', 'gazer_watch', 'door', {}),
    ('link:deck_west', 'deck', 'west_hall', 'open', {}),
    ('link:deck_drop', 'deck', 'rings', 'drop', {'purpose': "The trapdoors."}),
    ('link:west_juice', 'west_hall', 'juice', 'door', {}),
    ('link:west_ante', 'west_hall', 'antechamber', 'door', {}),
    ('link:west_hatch', 'west_hall', 'hatch_room', 'door', {}),
    ('link:screen_hatch', 'gazer_watch', 'hatch_room', 'door', {}),
    ('link:ante_vault', 'antechamber', 'vault', 'door', {'opened_by': 'key:vault', 'purpose': "The strongroom."}),
    ('link:ante_command', 'antechamber', 'command', 'door', {'purpose': "Two leaves (hover 'Command Central')."}),
]

PITCH = ("Sheltem's fortress of teal Ancient steel on its mesa. Four conveyor belts carry the party one way to four "
         "Lava Heads, each powering an energy field on the floor above; behind the fields four element sundials, set "
         "to nine, raise four bridges over the ring chasms to the true-name gate; behind the gate a lift rises to the "
         "trapdoor deck and Command Central, where Corak comes out of the Soul Box to face Sheltem.")
PURPOSE = ("Story M33 (QUESTS.md): the arrival needs Corak's Soul Box (m33.arrival); the four Heads, the four sundials "
           "(Xeen.alamarSundial), the true-name gate (Sheltem), the lift, the dais (m33.sheltem), the self-destruct "
           "cinematic and the leave to D6. Q-D26's roof hatch to D7. Class L, party 52-55, monsters 50-75.")
MOOD = ("Machine hum, green grids and teal steel lit from within; the dial hall's chasms glow in their elements' "
        "colours; every window looks at you.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, pop, tre, extra) in SP.items():
        floor = [FLOORS[f] for f in fl] if isinstance(fl, list) else FLOORS[fl]
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': floor, 'purpose': purpose}
        if level != 'L1':
            s['extent'], s['at'] = geo.extent(sid)
            s['clear_height'] = geo.R[sid][3] - geo.R[sid][2]
            th = geo.R[sid][4]
            s['theme'] = next(t['notes'] for t in geo.THEMES if t['id'] == th)
        if extra.get('empty'):
            s['empty'] = True
        if pop:
            s['population'] = pop
        if tre:
            s['treasure'] = tre
        spaces.append(s)
    links = []
    for lid, a, b, kind, extra in LINKS:
        d = {'id': lid, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
        d.update(extra)
        links.append(d)
    return {
        'format': 0, 'level': level if level in ('L1', 'L2') else 'L3', 'pitch': PITCH,
        'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:fire_belt', 'spaces': ['room:west_ward', 'room:belt_fire', 'room:belt_fire_end', 'room:head_fire', 'room:return_w'],
             'notes': "One way round: the belt in, the bolted door out (then both ways)."},
            {'id': 'loop:water_belt', 'spaces': ['room:west_ward', 'room:belt_water', 'room:belt_water_end', 'room:head_water', 'room:return_w']},
            {'id': 'loop:air_belt', 'spaces': ['room:east_ward', 'room:belt_air', 'room:belt_air_end', 'room:head_air', 'room:return_e']},
            {'id': 'loop:earth_belt', 'spaces': ['room:east_ward', 'room:belt_earth', 'room:belt_earth_end', 'room:head_earth', 'room:return_e']},
            {'id': 'loop:outer_walk', 'spaces': ['room:landing', 'room:landing_w', 'room:bay_sw', 'room:west_walk', 'room:bay_nw',
                                                 'room:north_walk', 'room:bay_ne', 'room:east_walk', 'room:bay_se'],
             'notes': "The dial floor's ring walk round the dial hall."},
            {'id': 'loop:chasm', 'spaces': ['room:west_walk', 'room:rings', 'room:sump', 'room:stair_hall',
                                            'room:landing', 'room:landing_w', 'room:bay_sw'],
             'notes': "A fall from a bridge or a trapdoor comes back up by the sump and the stair hall."},
            {'id': 'loop:deck', 'spaces': ['room:deck', 'room:west_hall', 'room:hatch_room', 'room:gazer_watch'],
             'notes': "Round the deck's west end by the hatch room."},
        ],
        'entrances': [
            {'id': 'entrance:d6_gate', 'space': 'room:gatehall', 'kind': 'both', 'neighbour': 'exit:d6_gate',
             'facing': 'n', 'how': "D6's door:dd17 (A6): in the gatehall a step inside the gate, facing the Hall of Order; out by the exit preset to D6's entrance:dd17_gate."},
            {'id': 'entrance:d7_roof', 'space': 'room:hatch_room', 'kind': 'both', 'neighbour': 'exit:d7_roof',
             'facing': 'e', 'how': "D7's door:dd17 (A6, q-d26.hatch) sets the party down at the ladder's foot; up by q-d26.alamar_hatch and the exit preset to D7's entrance:dd17_roof."},
        ],
        'critical_path': ['room:gatehall', 'room:hall_order', 'room:west_ward', 'room:belt_fire', 'room:belt_fire_end', 'room:head_fire',
                          'room:return_w', 'room:west_ward', 'room:belt_water', 'room:belt_water_end', 'room:head_water', 'room:return_w',
                          'room:west_ward', 'room:hall_order', 'room:east_ward', 'room:belt_air', 'room:belt_air_end', 'room:head_air',
                          'room:return_e', 'room:east_ward', 'room:belt_earth', 'room:belt_earth_end', 'room:head_earth', 'room:return_e',
                          'room:east_ward', 'room:hall_order', 'room:stair_hall', 'room:landing', 'room:landing_w', 'room:bay_sw',
                          'room:dial_water', 'room:bay_sw', 'room:west_walk', 'room:bay_nw', 'room:dial_fire',
                          'room:bay_nw', 'room:north_walk', 'room:bay_ne', 'room:dial_air', 'room:bay_ne',
                          'room:east_walk', 'room:bay_se', 'room:dial_earth', 'room:bay_se', 'room:landing',
                          'room:landing_w', 'room:bay_sw', 'room:west_walk', 'room:rings', 'room:lift_core', 'room:lift_top',
                          'room:deck', 'room:west_hall', 'room:antechamber', 'room:command'],
        'return_path': ['room:command', 'room:antechamber', 'room:west_hall', 'room:deck', 'room:lift_top',
                        'room:lift_core', 'room:rings', 'room:west_walk', 'room:bay_sw', 'room:landing_w', 'room:landing',
                        'room:stair_hall', 'room:hall_order', 'room:gatehall'],
        'goals': [
            {'id': 'goal:gate', 'space': 'room:rings', 'kind': 'use',
             'what': "The true-name gate on the island: with the four dials at nine, 'Sheltem' (m33.true_name_gate, gate_open 111661)."},
            {'id': 'goal:sheltem', 'space': 'room:command', 'kind': 'use',
             'what': "The dais plate's Yes: m33.sheltem (done 111662), the cinematic, the leave to D6."},
        ],
        'keys': [
            {'id': f'key:head_{el}', 'grants': {'qbit': QBITS[f'head_{el}_off']}, 'found_in': f'room:head_{el}',
             'how': 'lever', 'notes': f"The {el} Lava Head shut down: its field on L2 drops."}
            for el in ('fire', 'air', 'water', 'earth')] + [
            {'id': 'key:vault', 'grants': {'qbit': QBITS['vault_open']}, 'found_in': 'room:robot_bay', 'how': 'lever',
             'notes': "The vault release (one-way)."}],
        'points_of_interest': [
            {'id': 'poi:heads', 'space': 'room:head_fire', 'kind': 'lever', 'count': 4,
             'behaviour': "Each Lava Head: 'The Head speaks: \"<Element> power field operational.\"' then 'Shut the field down?'."},
            {'id': 'poi:dials', 'space': 'room:dial_fire', 'kind': 'lever', 'count': 4,
             'behaviour': "Xeen.alamarSundial: '<Element> Time. The sundial reads N. Turn?'; at nine its bridge slab rises."},
            {'id': 'poi:statues', 'space': 'room:hall_order', 'kind': 'sign', 'count': 3,
             'behaviour': "The propaganda statues (aaze0049:2-4), one per floor."},
            {'id': 'poi:true_name_statue', 'space': 'room:rings', 'kind': 'sign',
             'behaviour': "The crackling statue on the island (aaze0049:5)."},
            {'id': 'poi:juice', 'space': 'room:juice', 'kind': 'sign', 'behaviour': "XEEN Power Juice (aaze0051:0)."},
            {'id': 'poi:hatch', 'space': 'room:hatch_room', 'kind': 'exit', 'behaviour': "q-d26.alamar_hatch."},
            {'id': 'poi:traps', 'space': 'room:deck', 'kind': 'trap', 'count': 6,
             'behaviour': "Hatched plates that drop the party 1,280 to the chasm floor."},
        ],
        'mechanisms': [
            {'kind': 'plate ride along a conveyor belt', 'count': 8},
            {'kind': 'Lava Head drops an energy field', 'count': 4},
            {'kind': 'sundial raises a bridge slab at nine', 'count': 4},
            {'kind': 'true-name gate (typed answer)', 'count': 1},
            {'kind': 'lift after a qbit', 'count': 1}, {'kind': 'trapdoor', 'count': 6},
            {'kind': 'one-way vault lever', 'count': 1}, {'kind': 'cinematic and leave', 'count': 1},
        ],
        'totals': {'chests': 7, 'doors': 24, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act5_graphs/dd17.graph.yml; D-61 (mockups/act5_a8_decisions.md) wins. Changes from the graph (A8 L2): the gate island is a platform inside the dial hall (one room, the graph's room:island merged), the chasms are U-shaped round the island on the hall's east wall so the lift core lies beyond the gate in the east wall; the chasm floor (0) runs out to the sump (the graph's 'chasm, 640' to the sump); the trapdoors drop 1,280 to the chasm floor, which is the sump's.",
    }


DIAGRAM = """L3 THE DECK (1280)
  [HATCH ROOM: ladder, D7] =door= [SCREEN ROOM $] =door= [DECK: 6 trapdoors] =door= [ROBOT BAY $, vault lever]
       |door                                         |            |
  [HALL OF VENGEANCE: statue, Come to ME] ---------+     [LIFT HEAD]
  |door [POWER JUICE]   |door
  [ANTECHAMBER] =door= [STRONGROOM $$]
       ||two leaves
  [COMMAND CENTRAL: dais, throne, Sheltem and Corak hidden]
L2 THE DIAL FLOOR (640)
  [FIRE TIME]~field~[NW BAY] -- [NORTH WALK: statue] -- [NE BAY]~field~[AIR TIME]
                       |                                     |
                  [WEST WALK] -> lip  (DIAL HALL: 4 chasms, 4 slabs, island, gate) =gate= [LIFT CORE]  [EAST WALK] =door= [WATCHERS' POST $]
                       |                                     |
  [WATER TIME]~field~[SW BAY] -- [SOUTH WALK: stair head] -- [SE BAY]~field~[EARTH TIME]
L1 THE WORKS (0)
  [FIRE HEAD] =bolt= [WEST RETURN]     (dial hall's chasm floor)      [EAST RETURN] =bolt= [AIR HEAD]
  [FIRE BELT ^]  [WATER HEAD]=bolt=      |                              =bolt=[EARTH HEAD]  [AIR BELT ^]
  [WATER BELT ^]                     [SUMP] =door= [STAIR HALL]          [EARTH BELT ^]
  [WEST WARD] ------------------ [HALL OF ORDER: statue] ---------------- [EAST WARD]
  [BARRACKS $]                   ||two leaves                [PARTS STORE $] [MOAT WATCH $]
                                 [GATEHALL: arrival, exit to D6]
 $ chest   =door= door   ~field~ xafield leaf   ^ belt (one way north)
"""


# The whole plan is drawn at the graph's sizes and enlarged by SCALE in x and y when written (heights, door, plate,
# lift and furniture sizes stay): the L band's 120-200 M units squared (MAPS.md dungeon classes).
SCALE = 1.3
POINT_KEYS = {'at', 'from', 'to', 'look_at', 'outline'}


def sc(v):
    return int(round(v * SCALE / 16.0)) * 16


def sc_point(p):
    if isinstance(p, list) and len(p) in (2, 3) and all(isinstance(x, (int, float)) for x in p):
        return [sc(p[0]), sc(p[1])] + ([p[2]] if len(p) == 3 else [])
    return p


def scale_doc(node, parent_key=None):
    """Enlarge every plan position of a written document (points, outlines, wall offsets, plan extents)."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in ('at', 'from', 'to', 'look_at') and isinstance(v, list):
                out[k] = sc_point(v)
            elif k == 'outline' and isinstance(v, list):
                out[k] = [sc_point(p) for p in v]
            elif k == 'offset' and isinstance(v, (int, float)) and parent_key == 'panels':
                out[k] = sc(v)
            elif k == 'extent' and isinstance(v, list):
                out[k] = [sc(v[0]), sc(v[1])]
            elif k == 'radius' and isinstance(v, (int, float)) and parent_key in ('lights', 'sounds'):
                out[k] = sc(v)
            elif k == 'inner_radius' and isinstance(v, (int, float)):
                out[k] = sc(v)
            else:
                out[k] = scale_doc(v, k if isinstance(v, list) else parent_key)
        if str(out.get('id', '')).startswith('platform:dial_'):
            x, y = out['at']
            out['at'] = [(x // 128) * 128 + 64, (y // 128) * 128 + 64]
        return out
    if isinstance(node, list):
        return [scale_doc(x, parent_key) for x in node]
    return node


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', scale_doc(plan(level)) if level != 'L1' else plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', scale_doc({
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:main', 'ambient': 14},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-17 Castle Alamar: L1 at 0, L2 at 640, L3 at 1280, the dial hall from 0 to 1216, in one frame (x east, y north, z up). Written by output/studio_cal/dd17/tools/gen.py (geo.py).",
        }))
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
