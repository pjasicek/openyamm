#!/usr/bin/env python3
"""Writes DD-25 Bosco's Hall's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd25/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act5_graphs/dd25.graph.yml with decider D-62,
mockups/act5_a8_decisions_b.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml (geo.py), L4
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
BR = R / 'devdocs/xeen/briefs/dd25'


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


# D5 (installed, A6): entrance:dd25_door (-512, 9216, 2688) facing 0 (east), on the terrace at the end of
# link:bosco_lane, about 1,050 east of the leaves (assets_dev/worlds/xeen/maps/xeen_d5.studio.yml).
D5_ARRIVAL = [-512, 9216, 2688]
D5_DIR = 0

QBITS = {'arrived_once': 117680,
         # A3's Q-D17 bit read here
         'chalice_done': 113343}

NOTES_PROJECT = (
    "Xeen design brief for a new town BLV: DD-25 Bosco's Hall, the dwarf king's hall dug into the Desert of Doom's "
    "highlands (D5; WORLD_DESIGN 5.2; the source's Bosco stands on dark maze0013, his lines aaze0013:13-17). Graph "
    "devdocs/xeen/mockups/act5_graphs/dd25.graph.yml with decider D-62 (mockups/act5_a8_decisions_b.md, which wins): "
    "a small town BLV (S figures: 6-15 sectors, 7-20 M units squared, 3-8 doors), about 12 sectors and 9.9 M units "
    "squared, one loop (gate hall, great hall, smiths' gallery), a walk-in throne hall at z 128 and the Deep Guild one "
    "stair down at z -384. A4's houses (source/towns/dd25.yml): Bosco's Forge 4701, the Alehall 4702, the Deep Guild "
    "of Earth 4703, the King's Hall 4704 (Bosco, Q-D17), the Mailwright's Burrow 4705, the Tinker's Burrow 4706. No "
    "counted monsters, no chests, no finds: eight peaceful dwarves (four of A2's Bosco's Guard 11054, faction "
    "xeen_bosco_hall; four MM7 Peasant Dwarves), uncounted. Map qbit 117680 arrived_once (block 117680-117719); the "
    "goblet on the tasting table shown from q-d17.done 113343. Map card 9122: encounter 0, no slots, music 31.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd25', 'name': "Bosco's Hall", 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-25', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [13, 7], 'climbs': 'n'},
        'map_stats': {
            'id': 9122, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 0, 'trap_dice': 0,
            'perception_difficulty': 0, 'refill_days': 672, 'music': 31, 'environment': 'stone hall',
            'lock_difficulty': 0, 'slots': [],
        },
        'neighbours': [
            {'id': 'exit:d5_gate', 'to': 'xeen_d5.odm', 'kind': 'door', 'arrival': D5_ARRIVAL,
             'arrival_hint': "On D5 (the Desert of Doom), on Bosco's terrace at the end of the lane, about 1,050 east of the crag's gate, facing east, away from it (entrance:dd25_door).",
             'direction': D5_DIR,
             'notes': "D5 installed by A6; its door:dd25 (thing:bosco_door, two t09a03a leaves in the crag) gets into: {map: xeen_dd25.blv, arrival: entrance:d5_bosco} (D-62 relay to A6): this map's start in the gate passage, (2048, 0, 0) facing west (1024)."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


TOWNSFOLK = "Peaceful dwarves standing, uncounted (D-62 Q34)"

# id: (name, kind, size, floor, purpose, extra)
SP = {
    'gate_passage': ("Gate passage", 'corridor', 'S', 0,
                     "The arrival (entrance:d5_bosco) 256 inside the gate's two leaves (the way out to D5); two of Bosco's guards in its corners by the gate.",
                     {}),
    'gate_hall': ("Gate hall", 'room', 'M', 0,
                  "The Alehall's door first on the south wall (the tavern nearest the arrival), a pair of ale barrels beside it; the wide arch west into the great hall and the arch north to the smiths' gallery.",
                  {}),
    'great_hall': ("Great hall", 'room', 'L', 0,
                   "The town's square under the rock vault: the round hearth in the middle, the plain well against the south wall, benches by the walls, two chandeliers; two townsfolk.",
                   {}),
    'smiths_gallery': ("Smiths' gallery", 'corridor', 'M', 0,
                       "Along the north side, open at both ends (great hall, gate hall): Bosco's Forge and the Mailwright's Burrow side by side, 768 apart, the forge bay between them, an anvil by the wall; one townsfolk.",
                       {}),
    'forge_bay': ("Forge bay", 'room', 'S', 0, "The Forge's lit hearth in a low bay behind the gallery's wall.", {}),
    'burrow_lane': ("Burrow lane", 'corridor', 'S', 0,
                    "Off the great hall's south side: the Tinker's Burrow on its south wall, the guild stair from its west end; one townsfolk.",
                    {}),
    'kings_steps': ("King's steps", 'corridor', 'S', [0, 128],
                    "Four steps up (128) from the great hall to the throne hall's two leaves.", {}),
    'throne_hall': ("Throne hall", 'room', 'L', 128,
                    "Bosco's empty throne on a three-step dais under his banner, the King's Hall door behind the dais, the long tasting table with its cups and the taster's stool, braziers by the dais; two guards inside the doors. From q-d17.done the Chalice stands on the table.",
                    {'goal': True}),
    'guild_stair': ("Guild stair", 'corridor', 'M', [0, -384], "From the burrow lane down one stair to the Deep Guild.", {}),
    'guild_hall': ("Deep Guild hall", 'room', 'M', -384,
                   "A raw-rock hall at the guild stair's foot: a vein of crystal by the wall, floor lamps, the Deep Guild of Earth's door under its sign.",
                   {}),
}

LINKS = [
    ('link:gate_hall', 'gate_passage', 'gate_hall', 'open', {}),
    ('link:gatehall_great', 'gate_hall', 'great_hall', 'open', {}),
    ('link:gatehall_gallery', 'gate_hall', 'smiths_gallery', 'open', {}),
    ('link:great_gallery', 'great_hall', 'smiths_gallery', 'open', {}),
    ('link:forge_bay', 'smiths_gallery', 'forge_bay', 'open', {}),
    ('link:great_burrow', 'great_hall', 'burrow_lane', 'open', {}),
    ('link:great_steps', 'great_hall', 'kings_steps', 'open', {}),
    ('link:steps_throne', 'kings_steps', 'throne_hall', 'door', {'purpose': "The throne hall's two leaves (hdr1dl, hdr1dr), opening apart."}),
    ('link:guild_stair', 'burrow_lane', 'guild_hall', 'stairs', {'via': 'the guild stair'}),
]
PATH_ROOMS = {'link:guild_stair': 'guild_stair'}

HOUSES = [
    # door, house, name, room, kind
    ('door:alehall', 4702, "The Alehall", 'gate_hall', 'tavern'),
    ('door:forge', 4701, "Bosco's Forge", 'smiths_gallery', 'weapon shop'),
    ('door:mailwright', 4705, "The Mailwright's Burrow", 'smiths_gallery', 'residence'),
    ('door:tinker', 4706, "The Tinker's Burrow", 'burrow_lane', 'residence'),
    ('door:kings_hall', 4704, "The King's Hall", 'throne_hall', 'residence'),
    ('door:guild_earth', 4703, "The Deep Guild of Earth", 'guild_hall', 'Earth guild'),
]

PITCH = ("Bosco's Hall: the dwarf king's town dug into the crag over his terrace on the Desert of Doom. The gate opens "
         "on a passage and a gate hall where the Alehall is the first door; round the great hall's hearth and well the "
         "smiths' gallery holds the Forge and the Mailwright, a lane the Tinker's burrow and the stair down to the Deep "
         "Guild of Earth. Up four steps, through two carved leaves, Bosco's throne stands empty under his banner: the "
         "King keeps to his chambers behind the dais, where the cups can be watched.")
PURPOSE = ("A town BLV (WORLD_DESIGN 5.2): three services (Bosco's Forge 4701, the Alehall 4702, the Deep Guild of Earth "
           "4703) and three residences (the King's Hall 4704, the Mailwright's Burrow 4705, the Tinker's Burrow 4706); "
           "Q-D17 The Chalice of Protection in Bosco's topics (the King's Hall); teachers Axe, Chain, Earth Magic and "
           "Repair Item Grandmaster. No monsters, no chests, no finds (D-62).")
MOOD = ("A dwarf hall: dressed stone under raw rock vaults, timber house fronts with shingle eaves, the ring of hammers "
        "from the forge bay, the hearth's glow, guards at the gate and the throne hall.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, extra) in SP.items():
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': fl, 'purpose': purpose}
        if level != 'L1':
            s['extent'], s['at'] = geo.extent(sid)
            if sid in geo.P:
                s['clear_height'] = geo.P[sid][4]
            else:
                s['clear_height'] = geo.R[sid][3] - geo.R[sid][2]
            th = geo.P[sid][5] if sid in geo.P else geo.R[sid][4]
            s['theme'] = next(t['notes'] for t in geo.THEMES if t['id'] == th)
        s['empty'] = True
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
            {'id': 'loop:smiths', 'spaces': ['room:gate_hall', 'room:great_hall', 'room:smiths_gallery'],
             'notes': "The smiths' gallery opens at both ends: in by the wide arch, out past the Forge and the Mailwright to the gate hall."},
        ],
        'entrances': [
            {'id': 'entrance:d5_bosco', 'space': 'room:gate_passage', 'kind': 'both', 'neighbour': 'exit:d5_gate',
             'facing': 'w', 'notes': "In the gate passage 256 inside the gate's two leaves, facing west into the hall; the gate behind (the game's leave window)."},
        ],
        'critical_path': ['room:gate_passage', 'room:gate_hall', 'room:great_hall', 'room:kings_steps', 'room:throne_hall'],
        'return_path': ['room:throne_hall', 'room:kings_steps', 'room:great_hall', 'room:smiths_gallery', 'room:gate_hall',
                        'room:gate_passage'],
        'goals': [
            {'id': 'goal:bosco', 'space': 'room:throne_hall', 'kind': 'use',
             'what': "The King's Hall door behind the dais (house 4704): Bosco's Q-D17 topics (A3), the key to the Northern Tower and the Chalice's hand-in."},
        ],
        'points_of_interest': [
            {'id': 'poi:houses', 'spaces': ['room:gate_hall', 'room:smiths_gallery', 'room:burrow_lane', 'room:throne_hall',
                                            'room:guild_hall'], 'kind': 'door', 'count': 6,
             'behaviour': "Six house doors (clicked faces, house screens): " + "; ".join(f"{d} {h} {n}" for d, h, n, _, _ in HOUSES) + "."},
            {'id': 'poi:throne', 'space': 'room:throne_hall', 'kind': 'sign',
             'behaviour': "Bosco's throne (hover): \"The King's throne, empty. He takes his meals in his chambers, where the cups can be watched.\""},
            {'id': 'poi:goblet', 'space': 'room:throne_hall', 'kind': 'sign',
             'behaviour': "From q-d17.done (113343) the Chalice stands on the tasting table (a shipped goblet shown by the load event)."},
            {'id': 'poi:well', 'space': 'room:great_hall', 'kind': 'fountain',
             'behaviour': "A plain well: \"Cold and clean. The King had it tasted this morning.\" No boon (D-62 Q39)."},
        ],
        'mechanisms': [{'kind': 'house door (clicked face)', 'count': 6}, {'kind': 'hinged double door', 'count': 1},
                       {'kind': 'decoration shown by qbit on load', 'count': 1}],
        'totals': {'chests': 0, 'doors': 8, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act5_graphs/dd25.graph.yml; D-62 (mockups/act5_a8_decisions_b.md) wins: a walk-in throne hall with the empty throne (Q33), eight peaceful dwarves uncounted (Q34: four of A2's Bosco's Guard 11054, four MM7 Peasant Dwarves), 7d24's town quarter and one new texture xdbosban (Q35), the goblet on show from q-d17.done (Q37), no change after the oath (Q38), a plain well (Q39). Doors: the gate (two leaves, the exit to D5), the throne hall's two hinged leaves, and six house doors.",
    }


DIAGRAM = """BOSCO'S HALL (x east, y north; z 0 = the gate's sill)

            [FORGE 4701]   (bay)   [MAILWRIGHT 4705]
   +--------------------- SMITHS' GALLERY ---------------------+
   |  anvil                                                    |
   +----arch----+                                     +--arch--+
                |                                     |
 [THRONE HALL]=leaves=[KING'S STEPS]--[GREAT HALL: hearth, well]--arch--[GATE HALL]--[GATE PASSAGE]=gate= D5
  dais, throne,   (0 -> 128)              |                        [ALEHALL 4702]   arrival, 2 guards
  banner, table                           |
  [KING'S HALL 4704]               [BURROW LANE]
  2 guards                          [TINKER 4706]
                                         | guild stair (0 -> -384)
                                  [DEEP GUILD HALL (-384)]
                                  [DEEP GUILD OF EARTH 4703]
 =leaves= hinged pair (hdr1dl|hdr1dr)   =gate= two leaves, the exit (t09a03a|t09a03b)
"""


# D-89 identity (lane A8 s28): what the party must see
IDENTITY = {'shape': 'hall', 'family': '7d24',
            'seen': ["the great hall cut in the crag's raw rock, high under a rock vault on rock-cut pillars, its round "
                     "hearth burning",
                     "the house fronts of dressed stone and timber along the halls and the burrow lane",
                     "the smiths' gallery: the forge bay's glow on the anvils, Bosco's Forge and the Mailwright's Burrow"]}


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', dict(project(level), identity=IDENTITY) if level == 'L4' else project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:hall', 'ambient': 16},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-25 Bosco's Hall: the hall at z 0, the throne hall at 128, the Deep Guild at -384, in one frame (x east, y north, heights from the gate's sill). Written by output/studio_cal/dd25/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
