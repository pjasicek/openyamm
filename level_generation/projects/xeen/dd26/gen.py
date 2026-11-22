#!/usr/bin/env python3
"""Writes DD-26 Olympus Sewer's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd26/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act6_graphs/dd26.graph.yml with decider D-65,
mockups/act6_a8_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
objects.yml, wiring.yml (dress.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/dd26'


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


# Rows (assets_dev/worlds/xeen/source/monsters.yml, A2; D-65 Q56)
LESSER, WATER = 11625, 11710
LEVEL = {LESSER: 55, WATER: 62}

# D7 (installed, A6): its arrival by the marble grate in the gods' row (assets_dev/worlds/xeen/maps/xeen_d7.studio.yml).
D7_STAIR = 'entrance:dd26_stair'      # (-8704, 8192, 1808) facing 0

QBITS = {
    # map qbits (D-65: 117800-117839; 117807-117839 free)
    'dd26_arrived_once': 117800, 'drain_tr': 117801, 'drain_ib': 117802, 'drain_bl': 117803, 'drain_es': 117804,
    'tribble_door': 117805, 'bed_searched': 117806,
}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-26 Olympus Sewer (the source's dark maze0038 under Olympus, aaze0038) as one "
    "BLV level at z 0 under D7's gods' row: a ring of marble and stone channels round Cyrano Jones's den (Pets "
    "Unlimited, A4's house 4815, npc 5614), four drains with the note's pieces TR, IB, BL, ES, and the tribble door "
    "(a typed password, TRIBBLES or TRIBBLE) into the offering vault. Side quest Q-D28 Cyrano's Tribble (A3: the sale "
    "at 25,000 gold, D-65 Q58). Size S (MAPS.md section 0, D-65): 6-15 sectors, 7-20 M units squared, doors 3-8, "
    "levels 55-62, party 56-60, treasure 6, music 44. Graph devdocs/xeen/mockups/act6_graphs/dd26.graph.yml with "
    "decider D-65 (mockups/act6_a8_decisions.md, which wins): Lesser Water Elemental 11625 55 x16 and Water Elemental "
    "11710 62 x4, kill XP 75,056 for the party, 18.76k per member; walkways at least 256 wide and ceilings at least "
    "320 over them for the Water Elemental's body (radius 100, 202 high; D-65 change 3); every door, grate, drain and "
    "the tribble door's landing on dry walkways (B2). Rest encounters 10 %: the water elementals at Dif 0 (Water "
    "Elemental 62 only; D-65 Q61, A2's row 9178). Map qbits 117800-117806; map_stats 9178.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd26', 'name': 'Olympus Sewer', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-26', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [16, 10], 'climbs': 'n'},
        'map_stats': {
            'id': 9178, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 6, 'trap_dice': 10,
            'perception_difficulty': 20, 'refill_days': 672, 'music': 44, 'environment': 'stoneroom',
            'lock_difficulty': 20,
            # D-65 Q61: the water elementals at Dif 0 (Water Elemental 62 only), as A2's row 9178 (groups of 1-2)
            'slots': [{'monster': 'Xeen Water Elemental', 'tier': 0, 'per_marker': [1, 2], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d7_stair', 'to': 'xeen_d7.blv', 'kind': 'door', 'arrival': D7_STAIR,
             'arrival_hint': "On D7 (the Skyroads) in Olympus's gods' row, 512 south of the marble grate, facing east (A6's entrance:dd26_stair, (-8704, 8192, 1808) facing 0).",
             'notes': "D7 installed by A6: its door:dd26 (platform:sewer_grate, the marble grate at (-8704, 8704)) is to ask 'Descend into the sewer?' (aaze0037:1) and arrive at this map's entrance:d7_stair, the stair's foot (0, 0, 0) facing north (512); it stays sealed with a line until DD-26 is installed. The way out is the exit preset on the grate at the stair's top; 'Climb up to Olympus?' is its meaning (A3, a map-local line)."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


# id: (name, kind, size, purpose, population, treasure, extra)
SP = {
    'stair': ("Marble stair", 'room', 'S',
              "The arrival (entrance:d7_stair) at the stair's foot facing north into the conduit; the marble stair climbs south 448 to the grate's underside, the exit preset up to D7. A scroll pinned to the wall: 'Scroll' (aaze0038:10), 'Search the drains.' (:11). Quiet (D-11.3); map qbit 117800 dd26_arrived_once.",
              [], [], {'empty': True}),
    'conduit': ("South conduit", 'corridor', 'M',
                "The main channel under the gods' row, east to west: its water down the middle, walkways on both banks, a dry crossing between the stair and the den's door.",
                [placed(LESSER, 3)], [], {}),
    'den': ("Pets Unlimited", 'room', 'S',
            "Cyrano Jones's den in the ring's middle: tribble cages by the walls, his counter with his door (A4's house 4815 'Pets Unlimited', aaze0038:19), and his bed: 'Bed' (:16), one random T6 item once (117806), then 'Nothing here.' (:17). 'Cyrano sells the password.' (:12) on the den's door. Quiet.",
            [], [], {'empty': True}),
    'west': ("West culvert", 'corridor', 'M',
             "The ring's west side, its channel along the outer wall; drain 1 (TR, 117801); the spillway's grate in its outer wall.",
             [placed(LESSER, 3)], [], {}),
    'spill': ("West spillway", 'room', 'S',
              "Dead end behind a grate: the overflow weir, drain 2 (IB, 117802) and a T6 chest on the weir's dry ledge.",
              [placed(LESSER, 2)], [{'kind': 'chest', 'count': 1, 'tier': 6}], {}),
    'cistern': ("The gods' cistern", 'room', 'M',
                "The ring's north side: a deep clear basin sunk 256 under a high marble vault, walkways round it; drain 3 (BL, 117803); the tribble door's landing off its east wall.",
                [placed(WATER, 2, 'heavy'), placed(LESSER, 2)], [], {}),
    'east': ("East culvert", 'corridor', 'M',
             "The ring's east side, back to the conduit; the outfall's grate in its outer wall.",
             [placed(LESSER, 3)], [], {}),
    'outfall': ("The outfall", 'room', 'S',
                "Dead end behind a grate: the sewer's mouth on the island's edge, the water falling away into cloud through a barred opening (no way out); drain 4 (ES, 117804).",
                [placed(LESSER, 2)], [], {}),
    'tdoor': ("Tribble door", 'corridor', 'S',
              "The landing before the bronze pair: 'A disembodied voice booms, \"What's the password?\"' (aaze0038:5) as the prompt's own text; TRIBBLES or TRIBBLE (any case): 'Correct! You may pass.' (:9), 117805, the leaves open for good; anything else 'Wrong! You may not pass!' (:8). Quiet.",
              [], [], {'empty': True}),
    'vault': ("Offering vault", 'room', 'M',
              "The set piece: the undercroft where Olympus's offerings wash down, gilded cups, coin and a gilt statue by the walls, the T6 chest on a ledge. The map's goal.",
              [placed(WATER, 2, 'heavy'), placed(LESSER, 1)], [{'kind': 'chest', 'count': 1, 'tier': 6}],
              {'goal': True}),
}

LINKS = [
    ('link:1', 'stair', 'conduit', 'open', {}),
    ('link:2', 'conduit', 'den', 'door', {'purpose': "The den's plank door: 'Cyrano sells the password.'"}),
    ('link:3', 'conduit', 'west', 'open', {}),
    ('link:4', 'west', 'spill', 'door', {'purpose': "The spillway's grate."}),
    ('link:5', 'west', 'cistern', 'open', {}),
    ('link:6', 'cistern', 'east', 'open', {}),
    ('link:7', 'east', 'conduit', 'open', {}),
    ('link:8', 'east', 'outfall', 'door', {'purpose': "The outfall's grate."}),
    ('link:9', 'cistern', 'tdoor', 'open', {}),
    ('link:10', 'tdoor', 'vault', 'door',
     {'opened_by': 'key:password', 'purpose': "The tribble door: a bronze two-leaf pair opened by the password."}),
]

PITCH = ("The gods' drains under Olympus: a ring of marble and stone channels full of clear sky-water round a closed "
         "room where Cyrano Jones sells tribbles. Four drains hold the pieces of a note; a bronze door in the "
         "cistern asks for the password, and behind it lies the undercroft where the temples' offerings wash down.")
PURPOSE = ("Side quest Q-D28 Cyrano's Tribble (QUESTS.md; A3's q-d28 file): the drains' pieces TR, IB, BL, ES and "
           "Cyrano's patter to a tribble's owner give the word TRIBBLES; the tribble door opens on it into the offering "
           "vault. Class S, party 56-60, monsters 55-62, treasure 6.")
MOOD = ("Pale marble and grey sewer stone, the sound of running water everywhere, clean and cold; a pet shop's "
        "straw and purring in the middle; gold and temple marble behind the bronze door.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, purpose, pop, tre, extra) in SP.items():
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': geo.FLOOR, 'purpose': purpose}
        if level != 'L1':
            s['extent'], s['at'] = geo.extent(sid)
            s['clear_height'] = geo.R[sid][3] - geo.R[sid][2]
            th = geo.R[sid][4]
            s['theme'] = next(t['notes'] for t in geo.THEMES if t['id'] == th)
        if extra.get('empty'):
            s['empty'] = True
        if extra.get('goal'):
            pass
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
            {'id': 'loop:ring', 'spaces': ['room:conduit', 'room:west', 'room:cistern', 'room:east'],
             'notes': "The source's ring of channels round Cyrano's den: either way round from the stair."},
        ],
        'entrances': [
            {'id': 'entrance:d7_stair', 'space': 'room:stair', 'kind': 'both', 'neighbour': 'exit:d7_stair',
             'facing': 'n',
             'how': "D7's marble grate in the gods' row (A6's door:dd26) brings the party down to the stair's foot facing north into the conduit; the grate at the stair's top is the way back to D7's entrance:dd26_stair."},
        ],
        'critical_path': ['room:stair', 'room:conduit', 'room:den', 'room:conduit', 'room:west', 'room:spill',
                          'room:west', 'room:cistern', 'room:east', 'room:outfall', 'room:east', 'room:cistern',
                          'room:tdoor', 'room:vault'],
        'return_path': ['room:vault', 'room:tdoor', 'room:cistern', 'room:west', 'room:conduit', 'room:stair'],
        'goals': [
            {'id': 'goal:vault', 'space': 'room:vault', 'kind': 'take',
             'what': "The offering vault's T6 chest behind the tribble door."},
        ],
        'keys': [
            {'id': 'key:password', 'grants': {'qbit': 'tribble_door'}, 'found_in': 'room:tdoor', 'how': 'riddle',
             'notes': "The word TRIBBLES: the four drains' pieces in the ring's order (TR, IB, BL, ES) and Cyrano's patter to a tribble's owner (A3's q-d28 topic)."},
        ],
        'points_of_interest': [
            {'id': 'poi:scroll', 'space': 'room:stair', 'kind': 'sign',
             'behaviour': "'Scroll' (aaze0038:10): 'Search the drains.' (:11)."},
            {'id': 'poi:counter', 'space': 'room:den', 'kind': 'npc',
             'behaviour': "Cyrano's counter door (house 4815, Pets Unlimited): his topics (A3)."},
            {'id': 'poi:bed', 'space': 'room:den', 'kind': 'treasure',
             'behaviour': "'Bed' (:16): one random T6 item once (117806), then 'Nothing here.' (:17)."},
            {'id': 'poi:drains', 'space': 'room:west', 'kind': 'sign', 'count': 4,
             'behaviour': "Four drains (west culvert, spillway, cistern, outfall): each its piece of the note once (:1-:4, 117801-117804), then 'Drain' (:0)."},
            {'id': 'poi:voice', 'space': 'room:tdoor', 'kind': 'sign',
             'behaviour': "The tribble door's voice: 'What's the password?' (:5)."},
        ],
        'mechanisms': [
            {'kind': 'typed password opens a two-leaf door for good', 'count': 1},
            {'kind': 'lore finds once each, then a plain line', 'count': 4},
            {'kind': 'a find once (the bed)', 'count': 1},
            {'kind': 'walk-in house door (a residence)', 'count': 1},
        ],
        'totals': {'chests': 2, 'doors': 4, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act6_graphs/dd26.graph.yml; D-65 (mockups/act6_a8_decisions.md) wins where they differ: the scroll on the stair's wall (change 1), the tribble door's prompt with no message before it (change 2), walkways >= 256 and ceilings >= 320 for the Water Elemental (change 3), Cyrano a residence in towns/dd26.yml (4815/5614, change 4). Doors: the den's plank pair, the spillway's and the outfall's grates, the tribble door's bronze pair (4; the graph's fifth, a vault grille behind the bronze pair, is left out: the pair alone keeps the vault). The channels sunk 128 slope up at their ends; the cistern's basin sinks 256.",
    }


DIAGRAM = """THE OLYMPUS SEWER (one level, z 0; channels -128, cistern -256)

                [CISTERN: 2 x 62 + 2 x 55, basin, drain BL] ---- [TRIBBLE DOOR landing] =bronze pair= [OFFERING VAULT $: 2 x 62 + 55]
                  |                                   |
  [SPILLWAY $ drain IB] =grate= [WEST CULVERT: 3, drain TR]     [PETS UNLIMITED: Cyrano's counter door, bed]    [EAST CULVERT: 3] =grate= [OUTFALL: 2, drain ES]
                  |                                   ||den door                                         |
                [SOUTH CONDUIT: 3, channel down the middle, dry crossing] ------------------------------------
                                   |
                [MARBLE STAIR: arrival at the foot (0, 0, 0) facing north; up south to the grate = exit to D7]
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
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:culvert', 'ambient': 14},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-26 Olympus Sewer: one level at z 0 (channels sunk 128, the cistern 256), x east, y north, z up. Written by output/studio_cal/dd26/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
