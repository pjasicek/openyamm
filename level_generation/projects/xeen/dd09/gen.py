#!/usr/bin/env python3
"""Writes DD-09 Temple of Bark's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd09/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act3_graphs/dd09.graph.yml with decider D-27,
mockups/act3_a8_decisions_b.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
objects.yml and wiring.yml (dress.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/dd09'


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
ELITE, SHAMAN, CAPTAIN, SHAALTH, SNOG, ARACH, HUNTER, BARKMAN = 11040, 11041, 11042, 11043, 11044, 11330, 11331, 11633
LEVEL = {ELITE: 16, SHAMAN: 20, CAPTAIN: 26, SHAALTH: 30, ARACH: 14, HUNTER: 18, BARKMAN: 60}

# D2 (installed, A6): the great tree's door (D2 event 13) faces north at (-11190, -6935, 1120); A6's return point for
# it is (-11264, -6656, 992) facing north (game 512, studio 90).
D2_ARRIVAL = [-11264, -6656, 992]
D2_DIR = 90

QBITS = {'arrived_once': 117120, 'prisoners_freed': 117121,
         # A3's Q-D10 bits read or set here
         'root_west': 113210, 'root_east': 113211, 'shaalth_slain': 113204, 'cage_opened': 113205, 'sheewana_freed': 113206, 'disciples': 113216}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-09 Temple of Bark (the source's dark/aaze0073-0077 temple in the great tree), "
    "side quest Q-D10 (Princess Sheewana, held by Shaalth's orcs; A3's hooks q-d10.voice, root_west, root_east, "
    "limb_alcoves, shaalth, cage, book_of_ascension, crystal_water, dark_water, kettle, kettle_drunk) and M18 (two "
    "Energy Disks in the root alcoves). Size M (MAPS.md section 0): 20-45 sectors, 30-90 M units squared, 50 monsters at "
    "levels 14-30, Shaalth 30, Barkman 60 optional (D-1.2: counted in Act IV), party 22-26, treasure 3 (hoard 4), music "
    "12. Graph devdocs/xeen/mockups/act3_graphs/dd09.graph.yml with decider D-27 (mockups/act3_a8_decisions_b.md, which "
    "wins): no seven-potion room; red and blue flasks once per character (player bits 11315, 11316); the black barrel "
    "once per character (11317: +1 to all seven stats and one year of age); the Disciples' dials, lever and two waters; "
    "four prisoners freed by the pens' lever, hidden on the next entry; the orcs' tea; Barkman hidden until a limb "
    "alcove takes a gem. Rows (A2): orc warband 11040 (Orc Elite 11040 16; Orc Shaman 11041 10; Orc Captain 11042 5; "
    "Shaalth 11043), arachnoids 11330 (Arachnoid 11330 10; Arachnoid Hunter 11331 8), Barkman 11633 (hidden), Snog "
    "11044 (peaceful), Nathan 11902, Sky 11903, Alicia the Just 11904, Princess Sheewana 11905 (peaceful, each its own "
    "faction); the crown's four fountains +5 resistance once per character (player bits 11306-11309, D-37). Kill XP "
    "25,928 for the party, 6.48k per member. Map qbits 117120-117159 (provisional); map_stats 9158.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd09', 'name': 'Temple of Bark', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-09', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [42, 20], 'climbs': 'n'},
        'map_stats': {
            'id': 9158, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
            'perception_difficulty': 3, 'refill_days': 672, 'music': 12, 'environment': 'cave',
            'lock_difficulty': 4,
            'slots': [{'monster': 'Xeen Orc Warband', 'tier': 0, 'per_marker': [2, 3], 'weight': 60},
                      {'monster': 'Xeen Arachnoid', 'tier': 0, 'per_marker': [2, 3], 'weight': 40}],
        },
        'neighbours': [
            {'id': 'exit:d2_trunk', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': D2_ARRIVAL,
             'arrival_hint': "On D2 (Sprite Forest), in the bark glade just outside the great tree's round door, facing north, away from it (A6's return point for D2 event 13).",
             'direction': D2_DIR,
             'notes': "D2 installed by A6; its door:dd09 (entrance:dd09_door, the trunk's round door, q-d9.bark_door with Nibbler's key) leads here, to this map's start at the foot of the temple's first stair: (0, -1920, 0) facing north (90)."},
        ],
        'qbits': dict(QBITS),
        'items': {'energy_disk': 12334},
        'notes': NOTES_PROJECT,
        **({'identity': IDENTITY} if level == 'L4' else {}),
    }


# D-89 identity (reviews/DESIGN_GATING_AND_IDENTITY.md 2.2; lane A8 s27): what the party must see
IDENTITY = {'shape': 'temple', 'family': '7d22',
            'seen': ["a round hall of bark under a bark dome, the first thing past the trunk's door",
                     "roots: sloping earth floors, broken earthen walls and roots hanging through the roof",
                     "the limbs open to the leaves and the sky, and the crown's fountains under the open sky"]}
ATMOSPHERE = {'format': 0, 'open_sky': {'mode': 'open', 'sky_texture': 'xeendark1'},
              'notes': ("The limb walk and the crown's middle are open to D2's sky (the darkside's xeendark1, which the "
                        "world's sky.yml resolves) through their sky faces; the rest of the tree is lit by its own lights.")}


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    'trunk_door': ("Trunk door", 'room', 'S', 0,
                   "Inside the great tree's door, at the foot of the temple's first stair: the arrival, and the way out to D2.",
                   [], [], {'empty': True}),
    'first_hall': ("Hall of the Trunk", 'room', 'L', 0,
                   "The hollow trunk's first hall; a voice from the wood (q-d10.voice). Stairs down to the roots and up the trunk's wall.",
                   [], [], {'empty': True}),
    'barracks': ("Orc barracks", 'room', 'M', 0, "Where the priests' cells were: orc bedrolls and a cookfire.",
                 [placed(ELITE, 6), placed(CAPTAIN, 1, 'heavy')], [], {}),
    'chapel': ("Chapel of Sap", 'room', 'M', 0,
               "The priests' books (History of Bark, Book of Sap, Morning Ceremonies: Yak and Moo); two alcove flasks, red +2 Might and blue +2 Personality, once per character (player bits 11315, 11316).",
               [placed(SHAMAN, 2)], [], {}),
    'guardroom': ("Guardroom", 'room', 'M', 0, "The orcs' guard post at the back stair up to the cells.",
                  [placed(ELITE, 4)], [], {}),
    'root_hall': ("The root cellar", 'room', 'M', -512, "Under the trunk: roots as pillars, damp earth.",
                  [placed(ARACH, 4)], [], {}),
    'root_west': ("West root alcove", 'room', 'S', -512,
                  "Root alcove: 'Feed me! Give gem?' One gem: an Energy Disk (q-d10.root_west).", [], [], {'empty': True}),
    'root_east': ("East root alcove", 'room', 'S', -512,
                  "Root alcove, as the west: one gem, one Energy Disk (q-d10.root_east).", [], [], {'empty': True}),
    'pens': ("The pens", 'room', 'M', -512,
             "Cages for prisoners: Nathan and Sky; the pen lever ('You hear a rumbling in the distance.') opens these and the cell row's, two states.",
             [placed(ELITE, 3)], [], {}),
    'sap_vats': ("Sap store", 'room', 'M', -512,
                 "Vats of the tree's sap, the orcs' ledger, the black barrel (once per character: +1 to all seven stats and a year of age, player bit 11317), a chest.",
                 [placed(ELITE, 3)], [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'ring1': ("Ring landing", 'room', 'S', 640, "The ring stair's landing inside the trunk's wall.", [], [], {'empty': True}),
    'shaalth': ("Shaalth's hall", 'room', 'L', 640,
                "The temple's sanctuary made an orc king's hall; Sheewana in a cage (NPC 5107, q-d10.cage once Shaalth is dead, q-d10.shaalth); his hoard.",
                [placed(SHAALTH, 1, 'boss', role='boss'), placed(CAPTAIN, 3, 'heavy'), placed(SHAMAN, 2)],
                [{'kind': 'chest', 'count': 1, 'tier': 4, 'notes': "Shaalth's hoard"}], {'goal': True}),
    'cells': ("Cell row", 'room', 'M', 640,
              "Cages: Snog the Orc ('imprisoned for refusing to do evil') and Alicia the Just (the tea warning); opened by the pens' lever.",
              [placed(CAPTAIN, 1, 'heavy')], [], {}),
    'shaman': ("The shaman's tea room", 'room', 'M', 640,
               "Rugs, a kettle: the source's invitation, then 'Drink?'; Yes poisons the drinker (q-d10.kettle).",
               [placed(SHAMAN, 4)], [], {}),
    'ascension': ("Chapel of Ascension", 'room', 'M', 640,
                  "Three dials (map variables, 'Dial reads N. Turn?'), a lever, the Dark Water and the Crystal Water; the Book of Ascension (q-d10.book_of_ascension) gives west 1, north 2, east 3.",
                  [], [], {'empty': True}),
    'vault': ("Disciples' vault", 'room', 'S', 640, "'Disciples of Bark ONLY!': opened to a Disciple (q-d10.crystal_water).",
              [], [{'kind': 'chest', 'count': 1, 'tier': 3}], {'empty': True}),
    'limb_stair': ("Limb stair", 'room', 'S', 1280, "The limb climb's head, where the trunk forks.", [], [], {'empty': True}),
    'limb_walk': ("The limb walk", 'corridor', 'L', 1280,
                  "Walks hollowed along the great limbs; three limb alcoves: 'Feed me! Give gem?' A gem here wakes Barkman (q-d10.limb_alcoves).",
                  [placed(ARACH, 4), placed(HUNTER, 2)], [], {}),
    'fruit': ("Fruit rooms", 'room', 'M', 1280, "Hollows where the tree hangs its fruit.",
              [placed(ARACH, 2), placed(HUNTER, 2)], [], {}),
    'crown': ("The crown", 'room', 'L', 1280,
              "Light through the leaves; four fountains: +5 Fire, Air, Water, Body resistance, once per character ('The water is cool, clear and refreshing.'; D-37).",
              [placed(HUNTER, 4)], [], {}),
    'barkman': ("Barkman's hollow", 'room', 'M', 1280,
                "His diary ('SQUEEZED branch feeders today.') and a chest his life force binds shut (hoard); Barkman stands here hidden until a limb is fed.",
                [placed(BARKMAN, 1, 'boss', role='boss', notes='Placed hidden, shown when a limb alcove takes its first gem.')],
                [{'kind': 'chest', 'count': 1, 'tier': 4, 'notes': "Barkman's hoard, opens once he is dead"}], {}),
    'treasure': ("Treasure room", 'room', 'S', 1280, "The temple's offerings, which the shamans are sorting.",
                 [placed(SHAMAN, 2)], [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'ring_stair': ("Ring stair", 'corridor', 'L', [0, 640], "A stair winding up inside the trunk's wall from the hall to the ring landing.",
                   [], [], {'empty': True}),
    'back_stair': ("The orcs' back stair", 'corridor', 'M', [0, 640], "From the guardroom up to the cell row.", [], [], {'empty': True}),
    'limb_climb': ("Limb climb", 'corridor', 'M', [640, 1280], "From the ring landing up into the limbs.", [], [], {'empty': True}),
    'root_stair': ("Root stair", 'corridor', 'M', [0, -512], "From the hall down into the roots.", [], [], {'empty': True}),
}

LINKS = [
    ('link:door_hall', 'trunk_door', 'first_hall', 'open', {}),
    ('link:hall_barracks', 'first_hall', 'barracks', 'door', {}),
    ('link:hall_chapel', 'first_hall', 'chapel', 'open', {}),
    ('link:barracks_guard', 'barracks', 'guardroom', 'open', {}),
    ('link:guard_chapel', 'guardroom', 'chapel', 'door', {}),
    ('link:hall_roots', 'first_hall', 'root_hall', 'stairs', {'via': 'the root stair'}),
    ('link:roots_west', 'root_hall', 'root_west', 'open', {}),
    ('link:roots_east', 'root_hall', 'root_east', 'open', {}),
    ('link:roots_vats', 'root_hall', 'sap_vats', 'door', {}),
    ('link:vats_pens', 'sap_vats', 'pens', 'open', {}),
    ('link:pens_west', 'pens', 'root_west', 'open', {}),
    ('link:hall_ring', 'first_hall', 'ring1', 'stairs', {'via': 'the ring stair'}),
    ('link:ring_shaalth', 'ring1', 'shaalth', 'door', {}),
    ('link:shaalth_cells', 'shaalth', 'cells', 'open', {}),
    ('link:guard_cells', 'guardroom', 'cells', 'stairs', {'via': "the orcs' back stair"}),
    ('link:shaalth_shaman', 'shaalth', 'shaman', 'door', {}),
    ('link:shaman_asc', 'shaman', 'ascension', 'door', {}),
    ('link:asc_vault', 'ascension', 'vault', 'door', {'condition': {'qbit': 'disciples'}, 'opened_by': 'poi:crystal_water',
                                                         'purpose': "'Disciples of Bark ONLY!': the vault opens to a Disciple of Bark."}),
    ('link:ring_limbs', 'ring1', 'limb_stair', 'stairs', {'via': 'the limb climb'}),
    ('link:limbs_walk', 'limb_stair', 'limb_walk', 'open', {}),
    ('link:walk_fruit', 'limb_walk', 'fruit', 'open', {}),
    ('link:fruit_crown', 'fruit', 'crown', 'open', {}),
    ('link:walk_barkman', 'limb_walk', 'barkman', 'open', {}),
    ('link:barkman_treasure', 'barkman', 'treasure', 'open', {}),
    ('link:treasure_crown', 'treasure', 'crown', 'door', {}),
]
PATH_ROOMS = {'link:hall_roots': 'root_stair', 'link:hall_ring': 'ring_stair', 'link:guard_cells': 'back_stair',
              'link:ring_limbs': 'limb_climb'}

PITCH = ("A temple grown inside the great tree of Sprite Forest, taken by Shaalth's orcs. The trunk's round door opens "
         "on a hall of bark where a voice warns: feed the roots, not the limbs. Down among the roots two alcoves take a "
         "gem each for an Energy Disk; the orcs keep prisoners in the pens beside their sap store and its black barrel. "
         "Up the ring stair the old sanctuary is Shaalth's hall, Princess Sheewana caged in its corner; past the "
         "shaman's tea (poisoned) lies the Disciples' chapel of dials and two waters, and their vault. Above, the limbs: "
         "alcoves that wake Barkman, the fruit rooms and the crown's four fountains.")
PURPOSE = ("Side quest Q-D10 (QUESTS.md): free Princess Sheewana from Shaalth's orcs (q-d10.shaalth at his death, "
           "q-d10.cage, her topic Home); M18: two Energy Disks from the root alcoves (q-d10.root_west, root_east). "
           "Class M, party 22-26, monsters 14-30, Shaalth 30, Barkman 60 optional.")
MOOD = ("Living wood: bark walls and heartwood floors in the trunk, the old temple's green stone under ivy in its "
        "chapels, damp earth and roots below, leaves and daylight in the crown; orc squalor over all of it.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, pop, tre, extra) in SP.items():
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': fl, 'purpose': purpose}
        if level != 'L1':
            s['extent'], s['at'] = geo.extent(sid)
            if sid in geo.P:
                s['clear_height'] = geo.P[sid][4]
            else:
                s['clear_height'] = geo.R[sid][3] - geo.R[sid][2]
            th = geo.P[sid][5] if sid in geo.P else geo.R[sid][4]
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
        'format': 0, 'level': 'L1' if level == 'L1' else ('L2' if level == 'L2' else 'L3'), 'pitch': PITCH,
        'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:base', 'spaces': ['room:first_hall', 'room:barracks', 'room:guardroom', 'room:chapel'],
             'notes': "Round the trunk's base."},
            {'id': 'loop:roots', 'spaces': ['room:root_hall', 'room:sap_vats', 'room:pens', 'room:root_west'],
             'notes': "Through the pens."},
            {'id': 'loop:back_stair', 'spaces': ['room:first_hall', 'room:ring_stair', 'room:ring1', 'room:shaalth', 'room:cells',
                                                 'room:back_stair', 'room:guardroom', 'room:barracks'],
             'notes': "Up the ring stair, down the orcs' back stair."},
            {'id': 'loop:limbs', 'spaces': ['room:limb_walk', 'room:fruit', 'room:crown', 'room:treasure', 'room:barkman'],
             'notes': "Round the crown."},
        ],
        'entrances': [
            {'id': 'entrance:d2_trunk', 'space': 'room:trunk_door', 'kind': 'both', 'neighbour': 'exit:d2_trunk',
             'facing': 'n', 'notes': "The arrival at the foot of the first stair; the trunk's round door behind (the game's leave window)."},
        ],
        'critical_path': ['room:trunk_door', 'room:first_hall', 'room:root_stair', 'room:root_hall', 'room:root_west',
                          'room:root_hall', 'room:root_east', 'room:root_hall', 'room:root_stair', 'room:first_hall',
                          'room:ring_stair', 'room:ring1', 'room:shaalth'],
        'return_path': ['room:shaalth', 'room:ring1', 'room:ring_stair', 'room:first_hall', 'room:trunk_door'],
        'goals': [
            {'id': 'goal:shaalth', 'space': 'room:shaalth', 'kind': 'kill',
             'what': "Shaalth the Orc King (q-d10.shaalth at his death: shaalth_slain 113204)."},
            {'id': 'goal:sheewana', 'space': 'room:shaalth', 'kind': 'use',
             'what': "Sheewana's cage opens with Shaalth's key (q-d10.cage: cage_opened 113205); her topic Home frees her (sheewana_freed 113206)."},
            {'id': 'goal:disks', 'space': 'room:root_hall', 'kind': 'take',
             'what': "Two Energy Disks, one gem each in the root alcoves (q-d10.root_west, root_east; M18)."},
        ],
        'keys': [
            {'id': 'key:disciple', 'grants': {'qbit': 'disciples'}, 'found_in': 'room:ascension', 'how': 'puzzle',
             'notes': "Dials west 1, north 2, east 3, the lever, the Crystal Water: the vault opens to a Disciple."},
            {'id': 'key:pens', 'grants': {'map_var': 'pens_open'}, 'found_in': 'room:pens', 'how': 'lever',
             'notes': "The pen lever opens the pens' and the cell row's cages (two states)."},
        ],
        'points_of_interest': [
            {'id': 'poi:voice', 'space': 'room:first_hall', 'kind': 'sign',
             'behaviour': "On coming into the hall (once per visit): A3's q-d10.voice."},
            {'id': 'poi:root_alcoves', 'spaces': ['room:root_west', 'room:root_east'], 'kind': 'altar', 'count': 2,
             'behaviour': "'Root alcove': 'Feed me! Give gem?' One gem, one Energy Disk each (A3's once-hooks)."},
            {'id': 'poi:limb_alcoves', 'space': 'room:limb_walk', 'kind': 'altar', 'count': 3,
             'behaviour': "'Limb alcove': 'Feed me! Give gem?' A gem each (q-d10.limb_alcoves); the first shows Barkman."},
            {'id': 'poi:flasks', 'space': 'room:chapel', 'kind': 'fountain', 'count': 2,
             'behaviour': "Red flask +2 Might, blue flask +2 Personality, once per character (player bits 11315, 11316)."},
            {'id': 'poi:books', 'space': 'room:chapel', 'kind': 'sign', 'count': 3,
             'behaviour': "History of Bark, Book of Sap, Morning Ceremonies (dark/aaze0073)."},
            {'id': 'poi:black_barrel', 'space': 'room:sap_vats', 'kind': 'fountain',
             'behaviour': "Once per character (player bit 11317): +1 to all seven stats and one year of age; 'Danger: Unpredictable Effects.'"},
            {'id': 'poi:ledger', 'space': 'room:sap_vats', 'kind': 'sign', 'behaviour': "The orcs' ledger (dark/aaze0073)."},
            {'id': 'poi:pen_lever', 'space': 'room:pens', 'kind': 'lever',
             'behaviour': "'You hear a rumbling in the distance.': the four cages open (two states)."},
            {'id': 'poi:prisoners', 'spaces': ['room:pens', 'room:cells'], 'kind': 'npc', 'count': 4,
             'behaviour': "Nathan, Sky, Snog, Alicia: peaceful, talk through their opened cages (A3's topics, 500 XP each), gone on the next entry."},
            {'id': 'poi:kettle', 'space': 'room:shaman', 'kind': 'fountain',
             'behaviour': "The shaman's kettle: the invitation, 'Drink?'; Yes poisons the drinker (q-d10.kettle, kettle_drunk); repeatable."},
            {'id': 'poi:dials', 'space': 'room:ascension', 'kind': 'lever', 'count': 3,
             'behaviour': "'Dial reads N. Turn?' (map variables, 1 to 4)."},
            {'id': 'poi:asc_lever', 'space': 'room:ascension', 'kind': 'lever',
             'behaviour': "Right dials: the Crystal Water clears; wrong: 'Nothing happens.'"},
            {'id': 'poi:crystal_water', 'space': 'room:ascension', 'kind': 'fountain',
             'behaviour': "After the lever: q-d10.crystal_water (Disciple of Bark, award 418 for every member); the vault opens. Before: 'The water is stagnant.'"},
            {'id': 'poi:dark_water', 'space': 'room:ascension', 'kind': 'fountain',
             'behaviour': "q-d10.dark_water: poisons the drinker and takes about a tenth of HP, never a death."},
            {'id': 'poi:book_ascension', 'space': 'room:ascension', 'kind': 'sign',
             'behaviour': "The Book of Ascension (q-d10.book_of_ascension): west 1, north 2, east 3."},
            {'id': 'poi:cage', 'space': 'room:shaalth', 'kind': 'npc',
             'behaviour': "Sheewana's cage (q-d10.cage after Shaalth's death); then her topic Home; gone once freed."},
            {'id': 'poi:diary', 'space': 'room:barkman', 'kind': 'sign', 'behaviour': "Barkman's diary (dark/aaze0077:19)."},
            {'id': 'poi:fountains', 'space': 'room:crown', 'kind': 'fountain', 'count': 4,
             'behaviour': "+5 Fire, Air, Water, Body resistance to the drinker, each once per character (player bits 11306-11309, D-37)."},
        ],
        'mechanisms': [
            {'kind': 'gem alcove', 'count': 5}, {'kind': 'pen lever and five cage gates (two states)', 'count': 1},
            {'kind': 'dials, lever and two waters', 'count': 1}, {'kind': 'once-per-character flask or barrel', 'count': 3},
            {'kind': 'hidden boss shown by a limb alcove', 'count': 1},
        ],
        'totals': {'chests': 5, 'doors': 8, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act3_graphs/dd09.graph.yml; D-27 (mockups/act3_a8_decisions_b.md) wins where they differ: no seven-potion room, the flasks +2 once per character, the black barrel, the dials as map variables and the Crystal Water named by the Book, the Dark Water poisons and hurts (no death), the prisoners peaceful and freed by the pens' lever, the kettle, Barkman hidden until a limb is fed. Floors at 0 (trunk base), -512 (roots), 640 (upper trunk) and 1280 (limbs); each floor in its own part of the frame, joined by climbing tunnels. All 50 monsters placed; Barkman placed hidden.",
    }


DIAGRAM = """THE LIMBS (1280)
  [LIMB STAIR] -- [LIMB WALK: 3 limb alcoves] -- [FRUIT ROOMS] -- [THE CROWN: 4 fountains]
                          |                                              |door
                  [BARKMAN'S HOLLOW (hidden) $$] -- [TREASURE ROOM $] ---+
        ^ limb climb (640 -> 1280)
THE UPPER TRUNK (640)
                         [CELL ROW: Snog, Alicia] <- back stair (0 -> 640) from the guardroom
                                |
  [RING LANDING] =door= [SHAALTH'S HALL $$ Shaalth, Sheewana's cage] =door= [TEA ROOM: kettle] =door= [CHAPEL OF ASCENSION: dials, lever, waters] =locked= [VAULT $]
        ^ ring stair (0 -> 640)
THE TRUNK BASE (0)
  [CHAPEL OF SAP: flasks, books] =door= [GUARDROOM] -> back stair
        |                                   |
  [HALL OF THE TRUNK: the voice] =door= [ORC BARRACKS]
        |                     \\ ring stair
  [TRUNK DOOR: arrival] -> D2 (exit)
        root stair (0 -> -512) from the hall's west side
THE ROOTS (-512)
  [WEST ROOT ALCOVE: gem] -- [ROOT CELLAR] -- [EAST ROOT ALCOVE: gem]
        |                        |door
  [THE PENS: Nathan, Sky, lever] -- [SAP STORE $: barrel, ledger, vats]
 $ chest   =door= door   =locked= opened by the Crystal Water (Disciples)
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:trunk', 'ambient': 12},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-09 Temple of Bark: the trunk base at 0, the roots at -512 (west), the upper trunk at 640 (east), the limbs at 1280 (south-east), in one frame (x east, y north, heights from the arrival floor). Written by output/studio_cal/dd09/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        dump(folder / 'atmosphere.yml', ATMOSPHERE)
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
