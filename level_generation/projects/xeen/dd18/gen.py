#!/usr/bin/env python3
"""Writes DD-18 Sandcaster Sewer's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd18/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act3_graphs/dd18.graph.yml with decider D-27,
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
BR = R / 'devdocs/xeen/briefs/dd18'


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
STALKER, MATRIARCH, ASP, KCOBRA, MWARRIOR, MQUEEN = 11401, 11402, 11490, 11491, 11371, 11372
LEVEL = {STALKER: 25, MATRIARCH: 35, ASP: 30, KCOBRA: 38, MWARRIOR: 30, MQUEEN: 38}

# D3 (installed, A5): the street shaft thing:dd18_shaft at sketch cell [30, 32] = (-17408, 16384), its iron lid 512
# square against Barticus' Gym's south-east corner (the gym north-west of it, D3 DOORS.md). The arrival is measured on
# D3 (playtest_exit.yml, shots/d3arr2): south of the lid on open ground, facing south (away from it and from the gym).
SHAFT_ARRIVAL = [-17408, 15872, 1504]
SHAFT_DIR = 270

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-18 Sandcaster Sewer (the source's dark/aaze0032 sewer under Sandcaster), an "
    "optional dungeon (D-27): Barticus' members' room (a pay box, 5,000 gold once per party by A3's dd18.pay_box, "
    "gym_paid 116120; the Vitamin Brew +2 Endurance and the Protein Brew +2 Might once per character, player bits 11318 "
    "and 11319; The Art of Bodybuilding) and the long tunnel under the desert to D5, bolted on the desert side "
    "(dd18.tunnel_grate reads d5_tunnel 116121; phase 5 opens it). Size M (MAPS.md section 0): 20-45 sectors, 30-90 M "
    "units squared, 50 monsters at levels 25-38, party 28-30, treasure 3. Graph "
    "devdocs/xeen/mockups/act3_graphs/dd18.graph.yml with decider D-27 (mockups/act3_a8_decisions_b.md, which wins). "
    "Rows (A2): sewer stalkers 11400 (Sewer Stalker 11401, 16; Stalker Matriarch 11402, 4), cobras 11490 (Guardian Asp "
    "11490, 10; Killer Cobra 11491, 4), mantis ants 11370 (Mantis Warrior 11371, 12; Mantis Queen 11372, 4); no hornets. "
    "Kill XP 61,292 for the party, 15.3k per member. Map qbits 117280-117319 (provisional); map_stats 9171 "
    "(source/maps.yml: music 44, treasure 3).")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd18', 'name': 'Sandcaster Sewer', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-18', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [32, 23], 'climbs': 'n'},
        'map_stats': {
            'id': 9171, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 3, 'trap_dice': 3,
            'perception_difficulty': 3, 'refill_days': 672, 'music': 44, 'environment': 'stoneroom',
            'lock_difficulty': 3,
            'slots': [{'monster': 'Xeen Sewer Stalker', 'tier': 2, 'per_marker': [2, 3], 'weight': 40},
                      {'monster': 'Xeen Cobra', 'tier': 1, 'per_marker': [2, 3], 'weight': 30},
                      {'monster': 'Xeen Mantis', 'tier': 2, 'per_marker': [2, 3], 'weight': 30}],
        },
        'neighbours': [
            {'id': 'exit:d3_shaft', 'to': 'xeen_d3.odm', 'kind': 'door', 'arrival': SHAFT_ARRIVAL,
             'arrival_hint': "On D3 (Sandcaster), 256 south of the street shaft's iron lid against Barticus' Gym, facing south, away from it and the gym.",
             'direction': SHAFT_DIR,
             'notes': "D3 installed by A5; its street shaft (thing:dd18_shaft, sketch [30, 32] = (-17408, 16384), entrance:dd18_shaft, D3 door:dd18, 'Descend to the sewer?' as its meaning) leads here, to this map's start at the shaft ladder's foot: (0, 128, 0) facing south (270, game 1536)."},
            {'id': 'exit:d5_grate', 'to': 'xeen_d5.odm', 'kind': 'door', 'arrival': [0, 0, 0],
             'arrival_hint': "On D5 (Desert of Doom), outside the long tunnel's grate (A6, phase 5).",
             'direction': 0, 'listed_only': True,
             'notes': "SEALED until phase 5 (D-27): the grate is bolted on the desert side; this map's grate runs A3's dd18.tunnel_grate (\"Sand blows through the bars. The bolt is on the other side.\") until D5's grate sets d5_tunnel (116121). Unsealing: D5's arrival point here, and evt:desert_grate becomes the exit preset to exit:d5_grate with condition {qbit: d5_tunnel} (dress.py, one change). D5's way in should land at (-7680, -5696, -640) facing east (0), inside the grate."},
        ],
        'qbits': {'arrived_once': 117280, 'gym_paid': 116120, 'd5_tunnel': 116121},
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    'shaft': ("Street shaft", 'room', 'S', 0,
              "The ladder from Sandcaster's street ('Descend to the sewer?' on D3): the arrival, under Barticus' sign; the members' room's door and its pay box.",
              [], [], {'empty': True}),
    'gym': ("Barticus' members' room", 'room', 'M', 0,
            "The gym's members' room (D-27): pay once (5,000 gold, dd18.pay_box), then the Vitamin Brew (+2 Endurance) and the Protein Brew (+2 Might) once per character; The Art of Bodybuilding on the bench.",
            [], [], {'empty': True, 'goal': True}),
    'main_drain': ("Main drain", 'corridor', 'M', 0,
                   "Tan sandstone walls, a channel of slow water; 'Sewer Drain' grates from the street.",
                   [placed(STALKER, 4)], [], {}),
    'warren': ("Stalker warren", 'room', 'M', 0, "Where the stalkers breed, in a collapsed side vault.",
               [placed(STALKER, 4), placed(MATRIARCH, 1, 'heavy')], [], {}),
    'breeding_vault': ("Breeding vault", 'room', 'S', 0, "The warren's back vault, nests of rags.",
                       [placed(STALKER, 2), placed(MATRIARCH, 1, 'heavy')], [], {}),
    'cistern': ("The great cistern", 'room', 'L', 0,
                "A pillared cistern under the stepped-fret vaults of the city's old waterworks; a chest by its overflow.",
                [placed(STALKER, 4), placed(ASP, 2)], [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'alcoves': ("The alcoves", 'corridor', 'M', 0, "A corridor of niches ('Alcove'); one holds a chest, the rest 'Nothing here.'",
                [placed(STALKER, 2, 'light')], [], {}),
    'niche_1': ("Alcove (west)", 'room', 'S', 0, "An empty alcove: 'Nothing here.'", [], [], {'empty': True}),
    'niche_2': ("Alcove (middle)", 'room', 'S', 0, "The alcove with the chest.", [],
                [{'kind': 'chest', 'count': 1, 'tier': 3}], {'empty': True}),
    'niche_3': ("Alcove (east)", 'room', 'S', 0, "An empty alcove: 'Nothing here.'", [], [], {'empty': True}),
    'cobra_drain': ("Cobra drain", 'corridor', 'M', 0, "The drain from Venom Pond's side; snakes in the warm water.",
                    [placed(ASP, 6), placed(KCOBRA, 2, 'heavy')], [], {}),
    'collapse': ("Broken drain", 'room', 'M', 0,
                 "Where the drain's floor fell into older works: a rubble slope down to the tunnel.",
                 [placed(ASP, 2), placed(KCOBRA, 2, 'heavy'), placed(MATRIARCH, 2, 'heavy')], [], {}),
    'rubble_slope': ("Rubble slope", 'corridor', 'S', [0, -640], "The fallen floor, from the broken drain down to the tunnel head.",
                     [], [], {'empty': True}),
    'tunnel_head': ("Tunnel head", 'room', 'M', -640, "The foot of the slope: the long tunnel's start, a milestone 'To the desert'.",
                    [], [], {'empty': True}),
    'mantis_gallery': ("Mantis gallery", 'room', 'M', -640, "Ant diggings cutting across the tunnel; their walls are chewed rock.",
                       [placed(MWARRIOR, 6)], [], {}),
    'mantis_nest': ("Mantis nest", 'room', 'L', -640, "The queens' chamber; what the ants dragged in (a chest).",
                    [placed(MWARRIOR, 2), placed(MQUEEN, 3, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'egg_cells': ("Egg cells", 'room', 'S', -640, "Egg cells chewed into the rock off the nest; a queen guards them.",
                  [placed(MWARRIOR, 2), placed(MQUEEN, 1, 'heavy')], [], {}),
    'drowned': ("Drowned vault", 'room', 'M', -640, "A side vault with standing water and an old strongbox; off the nest.",
                [], [{'kind': 'chest', 'count': 1, 'tier': 3}], {'empty': True}),
    'tunnel_east': ("The long tunnel (east)", 'corridor', 'L', -640,
                    "Long, straight and dry, lamps every so often: 'There is a passage in the sewer that leads a long ways under the desert.'",
                    [placed(MWARRIOR, 2)], [], {}),
    'sand_drift': ("The long tunnel (the sand drift)", 'corridor', 'M', -640, "Sand drifting in from the desert end.",
                   [], [], {'empty': True}),
    'tunnel_west': ("The long tunnel (west)", 'corridor', 'M', -640, "The tunnel's last length, the air warmer.",
                    [], [], {'empty': True}),
    'desert_gate': ("Desert gate", 'room', 'S', -640,
                    "An iron grate with daylight and sand blowing through, bolted on the desert side (D5, phase 5); a sand-buried prospector's pack at its foot.",
                    [], [{'kind': 'chest', 'count': 1, 'tier': 3, 'notes': "the prospector's pack"}], {'empty': True}),
}

LINKS = [
    ('link:shaft_drain', 'shaft', 'main_drain', 'door', {}),
    ('link:shaft_gym', 'shaft', 'gym', 'door', {}),
    ('link:drain_warren', 'main_drain', 'warren', 'open', {}),
    ('link:warren_vault', 'warren', 'breeding_vault', 'open', {}),
    ('link:warren_cistern', 'warren', 'cistern', 'door', {}),
    ('link:drain_alcoves', 'main_drain', 'alcoves', 'door', {}),
    ('link:alcove_1', 'alcoves', 'niche_1', 'open', {}),
    ('link:alcove_2', 'alcoves', 'niche_2', 'open', {}),
    ('link:alcove_3', 'alcoves', 'niche_3', 'open', {}),
    ('link:alcoves_cobra', 'alcoves', 'cobra_drain', 'open', {}),
    ('link:cobra_cistern', 'cobra_drain', 'cistern', 'door', {}),
    ('link:cistern_collapse', 'cistern', 'collapse', 'open', {}),
    ('link:collapse_slope', 'collapse', 'rubble_slope', 'open', {}),
    ('link:slope_head', 'rubble_slope', 'tunnel_head', 'open', {}),
    ('link:head_gallery', 'tunnel_head', 'mantis_gallery', 'open', {}),
    ('link:gallery_nest', 'mantis_gallery', 'mantis_nest', 'open', {}),
    ('link:nest_eggs', 'mantis_nest', 'egg_cells', 'open', {}),
    ('link:nest_drowned', 'mantis_nest', 'drowned', 'door', {}),
    ('link:drowned_tunnel', 'drowned', 'tunnel_east', 'open', {}),
    ('link:gallery_tunnel', 'mantis_gallery', 'tunnel_east', 'open', {}),
    ('link:tunnel_drift', 'tunnel_east', 'sand_drift', 'open', {}),
    ('link:drift_west', 'sand_drift', 'tunnel_west', 'open', {}),
    ('link:tunnel_gate', 'tunnel_west', 'desert_gate', 'door', {}),
]

PITCH = ("Sandcaster's sewer: a street shaft under Barticus' sign, the gym's members' room behind a door at its foot "
         "(pay once, then a brew of each per member and the gym's one book); east, tan sandstone drains with slow water "
         "round a great pillared cistern under stepped-fret vaults, sewer stalkers breeding in a collapsed vault, the "
         "cobras of Venom Pond in the warm drain past a corridor of alcoves. South of the cistern the broken drain's "
         "floor has fallen into older works: a rubble slope down to the long tunnel, where mantis ants have dug "
         "galleries and a queens' nest across it, and the tunnel runs on a long way west under the desert to a grate "
         "with daylight through it, bolted on the other side.")
PURPOSE = ("Optional (D-27): Barticus' members' room (dd18.pay_box, dd18.members_room, the two brews, The Art of "
           "Bodybuilding) and the long tunnel to D5, bolted on the desert side until Act V (dd18.tunnel_grate). Class M, "
           "party 28-30, monsters 25-38, treasure 3.")
MOOD = ("Warm, dry and close: tan rubble and carved sandstone, stepped-fret vaults, slow water in channels and a still "
        "cistern; below, grey rock chewed by ants, and a long straight tunnel with sand drifting along it.")


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
    links = [{'id': lid, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind, **extra} for lid, a, b, kind, extra in LINKS]
    return {
        'format': 0, 'level': 'L1' if level == 'L1' else ('L2' if level == 'L2' else 'L3'), 'pitch': PITCH,
        'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:drains', 'spaces': ['room:main_drain', 'room:warren', 'room:cistern', 'room:cobra_drain',
                                             'room:alcoves'], 'notes': "Round the cistern."},
            {'id': 'loop:nest', 'spaces': ['room:mantis_gallery', 'room:mantis_nest', 'room:drowned', 'room:tunnel_east'],
             'notes': "Round the nest."},
        ],
        'entrances': [
            {'id': 'entrance:d3_shaft', 'space': 'room:shaft', 'kind': 'both', 'neighbour': 'exit:d3_shaft',
             'facing': 's', 'notes': "The arrival at the shaft ladder's foot, facing the members' room's door. The game's leave window is the way up."},
            {'id': 'entrance:d5_grate', 'space': 'room:desert_gate', 'kind': 'both', 'neighbour': 'exit:d5_grate',
             'notes': "SEALED until phase 5: the grate is bolted on the desert side (dd18.tunnel_grate)."},
        ],
        'critical_path': ['room:shaft', 'room:main_drain', 'room:warren', 'room:cistern', 'room:collapse',
                          'room:rubble_slope', 'room:tunnel_head', 'room:mantis_gallery', 'room:tunnel_east',
                          'room:sand_drift', 'room:tunnel_west', 'room:desert_gate'],
        'return_path': ['room:desert_gate', 'room:tunnel_west', 'room:sand_drift', 'room:tunnel_east', 'room:drowned',
                        'room:mantis_nest', 'room:mantis_gallery', 'room:tunnel_head', 'room:rubble_slope',
                        'room:collapse', 'room:cistern', 'room:cobra_drain', 'room:alcoves', 'room:main_drain',
                        'room:shaft'],
        'goals': [
            {'id': 'goal:gym', 'space': 'room:gym', 'kind': 'use',
             'what': "Pay Barticus' price once (dd18.pay_box, gym_paid 116120): the two brews once per character and the book."},
        ],
        'keys': [
            {'id': 'key:gym_paid', 'grants': {'qbit': 'gym_paid'}, 'found_in': 'room:shaft', 'how': 'npc',
             'notes': "The pay box by the members' room's door: 5,000 gold once per party."},
        ],
        'points_of_interest': [
            {'id': 'poi:paybox', 'space': 'room:shaft', 'kind': 'sign',
             'behaviour': "\"It costs 5,000 gold to use the gym. Pay?\" Yes: A3's dd18.pay_box (\"Enjoy the facilities.\", or the charity-gym refusal when short); No: \"Get lost!\" (dark/aaze0032:3-5, 14)."},
            {'id': 'poi:brews', 'space': 'room:gym', 'kind': 'fountain', 'count': 2,
             'behaviour': "The Vitamin Brew (+2 Endurance) and the Protein Brew (+2 Might), members only, once per character (player bits 11318, 11319)."},
            {'id': 'poi:book', 'space': 'room:gym', 'kind': 'sign',
             'behaviour': "The Art of Bodybuilding on the bench, members only (dd18.bodybuilding)."},
            {'id': 'poi:alcoves', 'spaces': ['room:niche_1', 'room:niche_3'], 'kind': 'sign', 'count': 2,
             'behaviour': "'Alcove' (dark/aaze0032:11): 'Nothing here.'"},
            {'id': 'poi:milestone', 'space': 'room:tunnel_head', 'kind': 'sign', 'behaviour': "A milestone: 'To the desert.'"},
            {'id': 'poi:grate', 'space': 'room:desert_gate', 'kind': 'sign',
             'behaviour': "The desert grate: \"Sand blows through the bars. The bolt is on the other side.\" (dd18.tunnel_grate; D5's side opens it in phase 5)."},
        ],
        'mechanisms': [
            {'kind': 'pay box, once per party (qbit)', 'count': 1},
            {'kind': 'once-per-character brew', 'count': 2},
            {'kind': 'grate bolted on the far side (sealed exit)', 'count': 1},
        ],
        'totals': {'chests': 5, 'doors': 7, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act3_graphs/dd18.graph.yml; D-27 (mockups/act3_a8_decisions_b.md) wins where they differ: optional, the members' room's pay box (5,000) and brews, the desert grate bolted on the D5 side, a prospector's pack at the grate's foot. Floors at 0 (under Sandcaster) and -640 (the long tunnel). All 50 monsters placed (exact counts). Added to the graph for the class band (20+ sectors): the warren's breeding vault, three alcove niches, the egg cells, the rubble slope and the long tunnel in three lengths.",
    }


DIAGRAM = """UNDER SANDCASTER (0)                [BREEDING VAULT]
                                           |
 D3 street ^ [STREET SHAFT] =door= [MAIN DRAIN ~~~] -- [STALKER WARREN] =door= [THE GREAT CISTERN $]
   (ladder)       |door                  |door                                  |       |door
   sign+paybox [MEMBERS' ROOM]     [THE ALCOVES] -------------- [COBRA DRAIN ~~] =door=+
               brews, book          | | |                                       |
                                   [n1][n2 $][n3]                          [BROKEN DRAIN]
                                                                                | rubble slope (0 -> -640)
THE LONG TUNNEL (-640)                                                          v
 D5 (sealed) <grate> [DESERT GATE $] =door= [TUNNEL W] -- [SAND DRIFT] -- [TUNNEL E] -- [MANTIS GALLERY] -- [TUNNEL HEAD]
                                                                             |              |
                                                                     [DROWNED VAULT $] =door= [MANTIS NEST $] -- [EGG CELLS]
 $ chest   =door= door   ~~ channel of water
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:drain', 'ambient': 12},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-18 Sandcaster Sewer: under Sandcaster at 0 and the long tunnel at -640 in one frame (x east, y north, heights from the arrival floor). Written by output/studio_cal/dd18/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
