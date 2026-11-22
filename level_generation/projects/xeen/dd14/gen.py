#!/usr/bin/env python3
"""Writes DD-14 Castle Blackfang's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd14/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act4_graphs/dd14.graph.yml with decider D-42,
mockups/act4_a8_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
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
BR = R / 'devdocs/xeen/briefs/dd14'


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
VAMPIRE, LORD, ROYAL, COUNT = 11291, 11292, 11295, 11294
SENTINEL, OVERLORD, OCTOPOD = 11551, 11552, 11473
LEVEL = {VAMPIRE: 40, LORD: 50, ROYAL: 58, COUNT: 70, SENTINEL: 38, OVERLORD: 45, OCTOPOD: 50}

# D4 (installed, A6): its arrival for Ambrose's flight out (assets_dev/worlds/xeen/maps/xeen_d4.studio.yml).
D4_GRIFFIN = 'entrance:dd14_griffin'    # (6144, 5120, 1216) facing 1024 (west, beside the sealed gatehouse)

QBITS = {'dd14_arrived_once': 117480,
         # A3's bits read here (the hooks set them)
         'm25_done': 111503, 'blackfang_slain': 111540, 'crown': 111541, 'done': 111542, 'queen_found': 111543,
         'queen_seen': 111544}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-14 Castle Blackfang (the source's dark maze0045-0048: the castle's three "
    "levels and its dungeon) as one BLV of four floors on D4's crag, entered only by Ambrose's griffin (D-36). Story "
    "M27 (A3's hooks m27.landing, m27.blackfang, m27.dungeon_stair, m27.queen_cell, m27.ambrose_return, m27.fly_out; "
    "M25's flight ends here). Size M (large: 70 monsters; MAPS.md section 0, D-42): 20-45 sectors, 30-90 M units "
    "squared, levels 38-58, Count Blackfang 70, party 39-42, treasure 4 (hoard 5), music 3. Graph "
    "devdocs/xeen/mockups/act4_graphs/dd14.graph.yml with decider D-42 (mockups/act4_a8_decisions.md, which wins): "
    "the griffin both ways (entrance:d4_griffin from D4's gate, entrance:d6_griffin from D6's m25.flight, one spot on "
    "the landing; Ambrose 5512 on the landing from m25.done, the question aaze0045:1 and m27.fly_out to D4's "
    "entrance:dd14_griffin); Royal Vampire 58 (11295) as the Count's three guards; the gargoyles on the walls; "
    "octopods stationary in the cistern; sleepers still rise after the Count's death; the source's refusal at the "
    "dungeon stair (aaze0047:0); the roof trapdoor drawn and bolted. Rows (A2): vampires 11290 (Vampire 11291 40 x39, "
    "Vampire Lord 11292 50 x10, Royal Vampire 11295 58 x3, Count Blackfang 11294 70), gargoyles_mm 11550 (Gargoyle "
    "Sentinel 11551 38 x10, Gargoyle Overlord 11552 45 x2), octopods 11473 (Octopod D 50 x5, A2's indoor row without the swimmer AI, D-52); Ambrose 11917 (npc 5512) and Queen Kalindra 11918 (npc 5001), peaceful, placed only, not counted, taking no damage (D-52). Kill XP 163,622 for the "
    "party, 40.91k per member. Rest encounters 10 %: vampires Dif 5 [2, 3] w100 only (D-42, D-52). Map qbits 117480-117519 (dd14_arrived_once "
    "117480, A3's); map_stats 9167.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd14', 'name': 'Castle Blackfang', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-14', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [16, 16], 'climbs': 'n'},
        'map_stats': {
            'id': 9167, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 3,
            'perception_difficulty': 4, 'refill_days': 672, 'music': 3, 'environment': 'stoneroom',
            'lock_difficulty': 6,
            # D-52 (1): one slot, as A2's row 9167 (the Gnome Vampire 32 in ~10 % of rests accepted)
            'slots': [{'monster': 'Xeen Vampire', 'tier': 5, 'per_marker': [2, 3], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d4_griffin', 'to': 'xeen_d4.odm', 'kind': 'door', 'arrival': D4_GRIFFIN,
             'arrival_hint': "On D4's north-shore track beside Castle Blackfang's sealed gatehouse, facing west (A6's entrance:dd14_griffin, (6144, 5120, 1216) facing 1024, D-42 Q1).",
             'notes': "Ambrose's griffin both ways (D-42 Q1): D4's gate (m25.gate_flight, A6) sets the party down at entrance:d4_griffin on the landing; Ambrose on the landing (m27.fly_out) flies it back to D4's entrance:dd14_griffin. D6's m25.flight (phase 5) arrives at entrance:d6_griffin, the same spot. No door: the castle is griffin-only (D-36)."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
        **({'identity': IDENTITY} if level == 'L4' else {}),
    }


# D-89 identity (reviews/DESIGN_GATING_AND_IDENTITY.md 2.2; lane A8 s27): what the party must see
IDENTITY = {'shape': 'castle', 'family': '7d32',
            'seen': ["the griffin's landing on the battlements, coffins in a row along the parapet under the sky",
                     "dark castle halls of grey block and dark flags under pointed ribs, the Count's hall and its throne",
                     "the family crypt under its pointed vault, and the Queen's cell in the dungeon below"]}


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


V, VL, GS, GO = VAMPIRE, LORD, SENTINEL, OVERLORD
# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    # L1
    'landing': ("Griffin's landing", 'room', 'M', 'L1',
                "The south wall walk's middle stretch, open to the sky: the griffin's arrival, m27.landing's text; coffins in a row against the outer parapet; the dead adventurer's notes (aaze0045:5); Ambrose and his griffin (D-42 Q1); the yard gate at the courtyard stair's head.",
                [], [], {'empty': True, 'goal': True}),
    'sw_tower': ("South-west tower", 'room', 'M', ['L2', 'L1'],
                 "Two storeys under the cone: the first fight on the top storey, the second adventurer's diary (aaze0045:4); the stair down to L2 (the gallery, the sleeping hall).",
                 [placed(V, 2)], [], {}),
    'west_walk': ("West wall walk", 'corridor', 'M', 'L1', "Open walk over the courtyard; the gargoyles on it.",
                  [placed(GS, 3)], [], {}),
    'nw_tower': ("North-west tower", 'room', 'M', 'L1',
                 "The gong (aaze0045:6-7): sounding it slides open the panel into the Count's study on L2.",
                 [placed(V, 2)], [], {}),
    'north_walk': ("North wall walk", 'corridor', 'M', 'L1', "Along the foot of the keep's top storey; the keep's iron-bound door.",
                   [placed(GS, 2), placed(GO, 1, 'heavy')], [], {}),
    'keep_top': ("The bat roost", 'room', 'M', 'L1',
                 "The keep's top chamber: a strongbox under the droppings; the roof trapdoor, bolted (D-42 (7)).",
                 [placed(V, 2)], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
    'ne_tower': ("North-east tower", 'room', 'M', 'L1', "Shuttered; two coffins by the wall (one find, one empty).",
                 [placed(V, 2)], [], {}),
    'east_walk': ("East wall walk", 'corridor', 'M', 'L1',
                  "The trapped walk: four fire plates in darker slabs, a clear line along the inner parapet.",
                  [placed(GS, 2), placed(GO, 1, 'heavy')], [], {}),
    'se_tower': ("South-east tower", 'room', 'M', ['L2', 'L1'],
                 "Two storeys: a quiet top storey with a coffin of loot; the stair down to L2 (the chapel, the library).",
                 [], [], {'empty': True}),
    # L2
    'south_gallery': ("Long gallery", 'room', 'L', 'L2', "Portraits of the Blackfangs, none with a reflection.",
                      [placed(V, 3)], [], {}),
    'chapel2': ("The black chapel", 'room', 'M', 'L2', "The altar with its bat-embroidered cloth; candelabra either side; double doors from the gallery.",
                [placed(V, 2), placed(VL, 2, 'heavy')], [], {}),
    'library': ("Library", 'room', 'M', 'L2', "Shelves of genealogy and sermons against garlic; The Blackfang Lineage (a find).",
                [placed(V, 2)], [], {}),
    'keep_hall2': ("The keep's upper hall", 'room', 'L', 'L2',
                   "Two chandeliers; the grand stair's head gallery east; the panel the gong opens in the north wall.",
                   [placed(V, 3), placed(VL, 1, 'heavy')], [], {}),
    'study': ("The Count's study", 'room', 'S', 'L2', "Behind the panel: a desk, the ledger (a find), the Count's strongbox.",
              [], [{'kind': 'chest', 'count': 1, 'tier': 4}], {'empty': True}),
    'countess': ("The Countess's rooms", 'room', 'M', 'L2',
                 "Bedchamber and dressing room, no mirror anywhere; a jewel box (a find); the back stair down to the kitchen.",
                 [placed(VL, 2, 'heavy')], [], {}),
    'coffin_dorm': ("Sleeping hall", 'room', 'M', 'L2',
                    "Six coffins against the walls, two vampires on watch; three coffins hold a sleeper who rises when opened (D-18), three only a find.",
                    [placed(V, 2), placed(V, 3, notes='hidden, one in each of three coffins, shown when it is opened')],
                    [], {}),
    # L3
    'stair_hall3': ("Grand stair hall", 'room', 'M', ['L3', 'L2'],
                    "The keep's double door on the courtyard; the grand stair up to its head gallery; the Count's hall's double doors north.",
                    [placed(V, 2)], [], {}),
    'back_stair': ("Servants' back stair", 'corridor', 'S', ['L3', 'L2'], "From the kitchen up to the Countess's rooms.",
                   [], [], {'empty': True}),
    'courtyard': ("The courtyard", 'room', 'L', 'L3',
                  "Open to the sky: the dry fountain and three gargoyles on its plinths; the courtyard stair up the south wall to the yard gate (its bar on the stair's side).",
                  [placed(GS, 3)], [], {}),
    'kitchen': ("Kitchen", 'room', 'M', 'L3', "Cold for a century; barrels in pairs, the hearth; the back stair.",
                [placed(V, 2)], [], {}),
    'cellar': ("Cask cellar", 'room', 'M', 'L3',
               "A storeroom of casks; a find in one cask; the trapdoor in the floor, bolted from below.",
               [placed(V, 2)], [], {'store': True}),
    'great_hall': ("Great hall", 'room', 'L', 'L3',
                   "A long table beside the line between the doors; Blackfang's arms (xbfcrest) on the end wall; two chandeliers; the screens passage north.",
                   [placed(V, 3), placed(VL, 1, 'heavy')], [], {}),
    'throne': ("The Count's hall", 'room', 'L', 'L3',
               "The black throne on its dais under xbfcrest: Count Blackfang (m27.blackfang at his death) and his three Royal Vampires; the bar of the dungeon stair and the crypt's door behind the dais.",
               [placed(COUNT, 1, 'boss', role='boss'), placed(ROYAL, 3, 'heavy')], [], {'goal': True}),
    'crypt': ("The family crypt", 'room', 'M', 'L3',
              "Four named stone coffins (aaze0047:6-9): the Dutchess and the Lady rise when opened, the Countess's is empty, the Count's holds the hoard.",
              [placed(VL, 2, 'heavy', notes='hidden in the Dutchess\'s and the Lady\'s coffins, shown when each is opened')],
              [{'kind': 'chest', 'count': 1, 'tier': 5, 'notes': "The Count's own coffin: the hoard."}], {}),
    'dstair': ("Dungeon stair", 'corridor', 'M', ['dungeon', 'L3'],
               "Behind the black iron bar (m27.dungeon_stair until the Count is dead): the stair down into the crag, the gaolers' post at its foot.",
               [placed(V, 2)], [], {}),
    # the dungeon
    'question': ("Question room", 'room', 'M', 'dungeon', "The gaolers' instruments, racks by the walls; their strongbox.",
                 [], [{'kind': 'chest', 'count': 1, 'tier': 4}], {'empty': True}),
    'cells': ("The cells", 'corridor', 'M', 'dungeon', "A row of barred cells, empty but for straw and chains; the Queen's at the far end.",
              [placed(V, 2)], [], {}),
    'shaft': ("Ladder shaft", 'room', 'S', 'dungeon',
              "The ladder up to the cellar's trapdoor, its bolt drawn from here; Zarkon's diary in the bones (aaze0047:4) and a rat-eaten one (aaze0047:5).",
              [], [], {'empty': True}),
    'queen_cell': ("The Queen's cell", 'room', 'S', 'dungeon',
                   "Queen Kalindra (5001), a vampire who will not come out: the crown (m27.queen_cell); hidden on done.",
                   [], [], {'empty': True, 'goal': True}),
    'undercroft': ("Pillared undercroft", 'room', 'L', 'dungeon', "Twelve square pillars in four rows of three under a low vault.",
                   [placed(V, 3), placed(VL, 2, 'heavy')], [], {}),
    'cistern': ("The black cistern", 'room', 'L', 'dungeon',
                "Black water, five octopods stationary in it (D-42 (4)); the chest on the far ledge.",
                [placed(OCTOPOD, 5, 'heavy', notes='stationary in the water')], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
}
FLOORS = {'L1': geo.L1, 'L2': geo.L2, 'L3': geo.L3, 'dungeon': geo.DUN}

LINKS = [
    ('link:landing_sw', 'landing', 'sw_tower', 'open', {}),
    ('link:sw_west', 'sw_tower', 'west_walk', 'open', {}),
    ('link:west_nw', 'west_walk', 'nw_tower', 'open', {}),
    ('link:nw_north', 'nw_tower', 'north_walk', 'open', {}),
    ('link:north_keep', 'north_walk', 'keep_top', 'door', {'purpose': "The keep's iron-bound door."}),
    ('link:north_ne', 'north_walk', 'ne_tower', 'open', {}),
    ('link:ne_east', 'ne_tower', 'east_walk', 'open', {}),
    ('link:east_se', 'east_walk', 'se_tower', 'open', {}),
    ('link:se_landing', 'se_tower', 'landing', 'open', {}),
    ('link:sw2_gallery', 'sw_tower', 'south_gallery', 'open', {'purpose': "The tower's foot on L2."}),
    ('link:gallery_chapel', 'south_gallery', 'chapel2', 'door', {'purpose': "Double doors (two leaves)."}),
    ('link:chapel_se2', 'chapel2', 'se_tower', 'open', {}),
    ('link:se2_library', 'se_tower', 'library', 'open', {}),
    ('link:library_keep', 'library', 'stair_hall3', 'open', {'purpose': "Onto the grand stair's head gallery."}),
    ('link:keep_study', 'keep_hall2', 'study', 'door', {'opened_by': 'poi:gong', 'purpose': "The panel the gong opens."}),
    ('link:keep_countess', 'keep_hall2', 'countess', 'open', {}),
    ('link:countess_dorm', 'countess', 'coffin_dorm', 'door', {}),
    ('link:dorm_sw2', 'coffin_dorm', 'sw_tower', 'open', {}),
    ('link:grand_stair', 'keep_hall2', 'stair_hall3', 'stairs', {'purpose': "The grand stair's head gallery."}),
    ('link:back_stair', 'countess', 'kitchen', 'stairs', {'via': "the servants' back stair"}),
    ('link:yard_stair', 'landing', 'courtyard', 'door',
     {'opened_by': 'poi:yard_bar', 'purpose': "The yard gate at the courtyard stair's head: its bar on the stair's side."}),
    ('link:cellar_kitchen', 'cellar', 'kitchen', 'door', {}),
    ('link:kitchen_yard', 'kitchen', 'courtyard', 'open', {}),
    ('link:yard_stairhall', 'courtyard', 'stair_hall3', 'door', {'purpose': "The keep door (double)."}),
    ('link:yard_great', 'courtyard', 'great_hall', 'door', {'purpose': "Double doors."}),
    ('link:stairhall_throne', 'stair_hall3', 'throne', 'door', {'purpose': "Double doors."}),
    ('link:great_throne', 'great_hall', 'throne', 'open', {'purpose': "The screens passage."}),
    ('link:throne_crypt', 'throne', 'crypt', 'door', {}),
    ('link:dstair_down', 'throne', 'dstair', 'door',
     {'opened_by': 'goal:count', 'purpose': "The black iron bar: lifts at the Count's death (m27.blackfang)."}),
    ('link:hatch', 'shaft', 'cellar', 'door',
     {'opened_by': 'poi:hatch_bolt', 'purpose': "The cellar's trapdoor: the ladder; its bolt drawn from the shaft."}),
    ('link:foot_question', 'dstair', 'question', 'door', {}),
    ('link:question_cells', 'question', 'cells', 'open', {}),
    ('link:cells_shaft', 'cells', 'shaft', 'open', {}),
    ('link:cells_queen', 'cells', 'queen_cell', 'open', {'purpose': "The cell's grille door, standing open."}),
    ('link:foot_undercroft', 'dstair', 'undercroft', 'open', {}),
    ('link:undercroft_cells', 'undercroft', 'cells', 'open', {}),
    ('link:undercroft_cistern', 'undercroft', 'cistern', 'open', {}),
]
PATH_ROOMS = {'link:back_stair': 'back_stair'}

PITCH = ("A black castle on a crag in a storm of bats, entered from the sky: Ambrose's griffin sets the party down on "
         "the south wall walk, where coffins stand in a row with their lids ajar. The party fights down through the "
         "towers and the upper floor (the sleeping hall's coffins open on sleepers) to the Count's hall, and his death "
         "lifts the bar on the stair into the crag, where the Queen of the Darkside, made a vampire, waits in a cell "
         "she will not leave. Ambrose waits on the walls to fly the party out.")
PURPOSE = ("Story M27 (QUESTS.md): kill Count Blackfang (m27.blackfang) to open the dungeon stair "
           "(m27.dungeon_stair), find the Queen (m27.queen_cell: 3-31-62), fetch her crown from DD-03 and bring it back "
           "(m27.ambrose_return flies everyone to D1). Ambrose flies the party in and out (m25.gate_flight, "
           "m27.fly_out). Class M (large: 70 monsters), party 39-42, monsters 38-58, Count Blackfang 70.")
MOOD = ("Wind and bats over black battlements; inside, Castle Navan's green stone and coffered ceilings gone cold and "
        "unlit but for candles nobody living needs; below, Zokarr's dressed stone, iron doors and black water.")


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
        extra = dict(extra)
        via = extra.pop('via', None)
        if via:
            d['notes'] = f"Through {via} (room:{PATH_ROOMS[lid]})."
        d.update(extra)
        links.append(d)
    return {
        'format': 0, 'level': level if level in ('L1', 'L2') else 'L3', 'pitch': PITCH,
        'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:walls', 'spaces': ['room:landing', 'room:sw_tower', 'room:west_walk', 'room:nw_tower',
                                            'room:north_walk', 'room:ne_tower', 'room:east_walk', 'room:se_tower'],
             'notes': "The wall walk round the courtyard."},
            {'id': 'loop:upper', 'spaces': ['room:sw_tower', 'room:south_gallery', 'room:chapel2', 'room:se_tower',
                                            'room:library', 'room:stair_hall3', 'room:keep_hall2', 'room:countess',
                                            'room:coffin_dorm'],
             'notes': "L2's ranges round the courtyard (the grand stair's head gallery joins the library and the keep's upper hall)."},
            {'id': 'loop:ground', 'spaces': ['room:courtyard', 'room:stair_hall3', 'room:throne', 'room:great_hall'],
             'notes': "The keep door and the great hall's doors both lead to the Count."},
            {'id': 'loop:stairs', 'spaces': ['room:keep_hall2', 'room:stair_hall3', 'room:courtyard', 'room:kitchen',
                                             'room:back_stair', 'room:countess'],
             'notes': "The grand stair and the back stair."},
            {'id': 'loop:dungeon', 'spaces': ['room:dstair', 'room:question', 'room:cells', 'room:undercroft'],
             'notes': "Through the question room or the undercroft."},
            {'id': 'loop:yard', 'spaces': ['room:landing', 'room:courtyard', 'room:stair_hall3', 'room:library',
                                           'room:se_tower'],
             'notes': "Once the yard gate's bar is lifted from the stair: the courtyard stair closes the walls onto the ground floor."},
            {'id': 'loop:out', 'spaces': ['room:cells', 'room:shaft', 'room:cellar', 'room:kitchen', 'room:courtyard',
                                          'room:great_hall', 'room:throne', 'room:dstair'],
             'notes': "Once the trapdoor is unbolted from below: the ladder closes the dungeon onto the ground floor."},
        ],
        'entrances': [
            {'id': 'entrance:d4_griffin', 'space': 'room:landing', 'kind': 'both', 'neighbour': 'exit:d4_griffin',
             'facing': 'n', 'how': "Ambrose's griffin from D4's gate (m25.gate_flight, A6) sets the party down on the landing; Ambrose flies it back out (m27.fly_out) to D4's entrance:dd14_griffin."},
            {'id': 'entrance:d6_griffin', 'space': 'room:landing', 'kind': 'arrival', 'facing': 'n',
             'how': "Ambrose's flight from D6's Griffin Pass (m25.flight; D6 is phase 5): the same spot on the landing."},
        ],
        'critical_path': ['room:landing', 'room:sw_tower', 'room:coffin_dorm', 'room:countess', 'room:keep_hall2',
                          'room:stair_hall3', 'room:throne', 'room:dstair', 'room:undercroft', 'room:cells',
                          'room:queen_cell'],
        'return_path': ['room:queen_cell', 'room:cells', 'room:shaft', 'room:cellar', 'room:kitchen', 'room:courtyard',
                        'room:landing'],
        'goals': [
            {'id': 'goal:count', 'space': 'room:throne', 'kind': 'kill',
             'what': "Count Blackfang (m27.blackfang at his death: blackfang_slain 111540; the bar lifts)."},
            {'id': 'goal:queen', 'space': 'room:queen_cell', 'kind': 'use',
             'what': "Queen Kalindra (5001): the crown topic (queen_found 111543, then done 111542 with the crown)."},
        ],
        'keys': [
            {'id': 'key:hatch', 'grants': {'map_var': 'hatch_open'}, 'found_in': 'room:shaft', 'how': 'lever',
             'notes': "The trapdoor's bolt, drawn from the shaft: the ladder up into the cellar."},
            {'id': 'key:yard_gate', 'grants': {'map_var': 'yard_gate_open'}, 'found_in': 'room:courtyard', 'how': 'lever',
             'notes': "The yard gate's bar, lifted from the courtyard stair's head."},
            {'id': 'key:gong', 'grants': {'map_var': 'study_open'}, 'found_in': 'room:nw_tower', 'how': 'lever',
             'notes': "The gong: the study's panel slides open."},
        ],
        'points_of_interest': [
            {'id': 'poi:ambrose', 'space': 'room:landing', 'kind': 'npc',
             'behaviour': "Ambrose (5512) by his griffin: 'Are you ready to leave this awful place, friends?' (aaze0045:1); Yes: m27.fly_out and the flight to D4."},
            {'id': 'poi:notes', 'space': 'room:landing', 'kind': 'sign',
             'behaviour': "The dead adventurer's notes (aaze0045:5): coffins, floor traps, the Count's magic."},
            {'id': 'poi:diary', 'space': 'room:sw_tower', 'kind': 'sign', 'behaviour': "The second adventurer's diary (aaze0045:4)."},
            {'id': 'poi:gong', 'space': 'room:nw_tower', 'kind': 'lever',
             'behaviour': "'Gong' / 'You hear a rumbling in the distance.' (aaze0045:6-7): the study's panel opens."},
            {'id': 'poi:coffins', 'space': 'room:coffin_dorm', 'kind': 'trap', 'count': 6,
             'behaviour': "Three sleepers rise when their coffins are opened (D-18); three finds."},
            {'id': 'poi:crypt', 'space': 'room:crypt', 'kind': 'trap', 'count': 4,
             'behaviour': "The four named coffins: two sleepers, one empty, the Count's hoard."},
            {'id': 'poi:fire_plates', 'space': 'room:east_walk', 'kind': 'trap', 'count': 4,
             'behaviour': "Fire from the merlons on each plate."},
            {'id': 'poi:yard_bar', 'space': 'room:courtyard', 'kind': 'lever',
             'behaviour': "The yard gate's bar, on the courtyard stair's side."},
            {'id': 'poi:hatch_bolt', 'space': 'room:shaft', 'kind': 'lever',
             'behaviour': "The trapdoor's bolt, drawn from the shaft."},
            {'id': 'poi:roof_trapdoor', 'space': 'room:keep_top', 'kind': 'sign',
             'behaviour': "'A trapdoor in the roof, bolted from above. Wind howls over it.' (D-42 (7))."},
            {'id': 'poi:shaft_bones', 'space': 'room:shaft', 'kind': 'sign', 'count': 2,
             'behaviour': "Zarkon's diary (aaze0047:4); the rat-eaten diary (aaze0047:5)."},
        ],
        'mechanisms': [
            {'kind': 'hidden sleeper shown when its coffin is opened', 'count': 5},
            {'kind': 'boss death lifts a bar', 'count': 1}, {'kind': 'gong opens a secret panel', 'count': 1},
            {'kind': 'trapdoor with a bolt and a ladder', 'count': 1}, {'kind': 'gate with a bar', 'count': 1},
            {'kind': 'fire plate', 'count': 4}, {'kind': 'talking figure (Ambrose, the Queen)', 'count': 2},
        ],
        'totals': {'chests': 5, 'doors': 13, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act4_graphs/dd14.graph.yml; D-42 (mockups/act4_a8_decisions.md) wins where they differ: both griffin arrivals on one spot of the landing, Ambrose waits there; the Royal Vampires; the gargoyles on the walls; the octopods stationary; the source's refusal at the stair; the roof trapdoor bolted. Changes from the graph (A8 L2): the towers' stair feet (sw_stair2, se_stair2) are the lower storeys of the two-storey stair towers, the dungeon stair's foot (dstair_foot) the lower floor of the dungeon stair, and the courtyard stair has its gate at its head (the bar on the stair's side). Floors 640 apart: the dungeon -640, the ground floor 0, the upper floor 640, the walls 1280. All 70 monsters placed.",
    }


DIAGRAM = """L1 THE WALLS (1280, open sky)
  [NW TOWER: gong] -- [NORTH WALK] =door= [BAT ROOST $, roof trapdoor]   [NE TOWER: 2 coffins]
        |                                                                       |
  [WEST WALK]           ( the courtyard below )                          [EAST WALK: fire plates]
        |                                                                       |
  [SW TOWER top] -- [LANDING: arrival, coffins, Ambrose, yard gate] -- [SE TOWER top: coffin of loot]
L2 THE UPPER FLOOR (640)
  [COUNTESS] -- [KEEP'S UPPER HALL] =gong panel= [STUDY $]   [grand stair head] -- [LIBRARY]
     |door  \\ back stair                                                                |
  [SLEEPING HALL: 6 coffins]                                                            |
     |                                                                                   |
  [SW TOWER foot] -- [LONG GALLERY] ==double== [BLACK CHAPEL] -- [SE TOWER foot] --------+
L3 THE GROUND FLOOR (0)
  [CRYPT: 4 named coffins $$] =door= [COUNT'S HALL: the Count] =bar= [DUNGEON STAIR] (0 -> -640)
  [GREAT HALL] ---- screens ----/   \\==double== [GRAND STAIR HALL]
     ||double                                     ||keep door
  [KITCHEN] ---- [COURTYARD (sky): fountain, courtyard stair up to the yard gate]
     |door
  [CASK CELLAR: trapdoor]
THE DUNGEON (-640)
  [DUNGEON STAIR foot] =door= [QUESTION ROOM $] -- [CELLS] -- [LADDER SHAFT: bolt, ladder up]
          \\-- [UNDERCROFT: 12 pillars] -- [CELLS] -- [QUEEN'S CELL]
                     \\-- [BLACK CISTERN: octopods, $]
 $ chest   =door= door
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:hall', 'ambient': 12},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-14 Castle Blackfang: the dungeon at -640, the ground floor at 0, the upper floor at 640, the walls at 1280, in one frame (x east, y north, z up). Written by output/studio_cal/dd14/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
