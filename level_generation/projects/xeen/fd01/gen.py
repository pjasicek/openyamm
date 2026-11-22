#!/usr/bin/env python3
"""Writes FD-01 Alamar Depths' project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/fd01/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act6_graphs/fd01.graph.yml with decider D-69,
mockups/act6_fd01_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
objects.yml, wiring.yml, atmosphere.yml (dress.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/fd01'


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


# Rows (assets_dev/worlds/xeen/source/monsters.yml, A2; D-69 Q63)
ANNIHILATOR, AUTOBOT = 11611, 11612
LEVEL = {ANNIHILATOR: 62, AUTOBOT: 75}

# Neighbours' named points (installed, A6): D6 xeen_d6.studio.yml, D7 xeen_d7.studio.yml
D6_STAIR = 'entrance:fd01_stair'      # (-6656, 4608, 2208) facing 1536
D7_ROOF = 'entrance:fd01_roof'        # (-18688, 8448, 1536) facing 1024 (D-69 Q67, A6)

QBITS = {
    # map qbits (D-69: 117840-117879; 117847-117879 free), A3's names in m39.yml
    'statue_spoken': 117840, 'slab_west': 117841, 'slab_east': 117842, 'grate_bolt': 117843, 'key_box': 117844,
    'skull_door_open': 117845, 'arrived_from_d7': 117846,
    # quest bits read
    'm39_darkstone_key': 111780, 'm39_done': 111781, 'q_d26_roof_unlocked': 113521,
}

NOTES_PROJECT = (
    "Xeen design brief for a new map: FD-01 Alamar Depths (the source's dark maze0052, aaze0052: Castle Alamar's "
    "dungeon) as one BLV under the ruin of Castle Alamar on D6, the main level at z 0 and Roland's stasis vault a lift "
    "(768) below. Story M39 Prince Roland (A3's m39 hooks), Q-F1's Key to the Dragon Tower (12376, the map's find) and "
    "Q-D26's way up to D7 (q-d26.depths_hatch). Class M: 20-45 sectors, 30-90 M units squared, 6-16 doors, 3-7 "
    "chests; party 58-61. Graph devdocs/xeen/mockups/act6_graphs/fd01.graph.yml with decider D-69 "
    "(mockups/act6_fd01_decisions.md, which wins): Annihilator 11611 62 x28 and Autobot 11612 75 x6, 34, kill XP "
    "163,242 for the party, 40.81k per member (D-57 Q7's exception: 34 under M's 45). Rest encounters 0 (Q71: A2's "
    "row 9179, encounter 0, treasure 6; no slots). Map qbits 117840-117846; map_stats 9179, music 50.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_fd01', 'name': 'Alamar Depths', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'FD-01', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [21, 17], 'climbs': 'n'},
        'map_stats': {
            'id': 9179, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 10,
            'perception_difficulty': 20, 'refill_days': 672, 'music': 50, 'environment': 'stoneroom',
            'lock_difficulty': 20,
        },
        'neighbours': [
            {'id': 'exit:d6_stair', 'to': 'xeen_d6.odm', 'kind': 'door', 'arrival': D6_STAIR,
             'arrival_hint': "On D6 before the ruin of Castle Alamar, facing south down the ramp (A6's entrance:fd01_stair, (-6656, 4608, 2208) facing 1536).",
             'notes': "D6's thing:fd01_stair (a pit hatch in the broken gatehouse's floor, m39.depths_door) names this map's entrance:d6_stair once A6 lifts DUNGEON['fd01'] = False. The way out is the exit preset at the stair's head (the leave window, D-24)."},
            {'id': 'exit:d7_roof', 'to': 'xeen_d7.blv', 'kind': 'door', 'arrival': D7_ROOF,
             'arrival_hint': "On Castle Alamar's roof on D7's Skyroads, by the hatch (A6's entrance:fd01_roof, (-18688, 8448, 1536) facing 1024).",
             'notes': "Q-D26 (D-69 change 5): the ladder's foot in the rubble shaft asks the map's own Yes/No 'Climb up through the hatch?'; Yes calls q-d26.depths_hatch ('Bolted from above.' until roof_unlocked 113521); true leaves at once to D7's entrance:fd01_roof. D7's hatch (q-d26.hatch, after m33.done) names this map's entrance:d7_roof."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack'):
    return {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}


A, AU = ANNIHILATOR, AUTOBOT
# id: (name, kind, size, purpose, population, treasure, extra)
SP = {
    'stair': ("Ruin stair", 'stair', 'S',
              "The arrival (entrance:d6_stair) at the stair's foot (0, 0, 0) facing west into the undercroft hall; the stair climbs east 640 to the gatehouse hatch's underside, where the exit preset takes the party up to D6 (D-24). Quiet (D-11.3).",
              [], [], {'empty': True}),
    'stairhall': ("Undercroft hall", 'hall', 'S',
                  "The first hall: Alamar's teal statue by the north wall speaks when the party first comes near (m39.statue, once, 117840; hover 'Statue'). The gallery door west. Quiet.",
                  [], [], {'empty': True}),
    'south': ("South gallery", 'corridor', 'M',
              "West from the gallery door (two rooms); the bolted grate in its north wall opens from the workshop's side (m39.grate_bolt, 117843); the guard door at its west end.",
              [placed(A, 3)], [], {}),
    'west': ("West gallery", 'corridor', 'M', "North from the guard door (two rooms) to the north gallery.",
             [placed(A, 3)], [], {}),
    'shaft': ("Rubble shaft", 'shaft', 'S',
              "Where the castle came down: a round shaft of scorched plating (xahullbn) and rubble open to the sky far above (xeen_darkside_day); the arrival from D7 (entrance:d7_roof) at its foot facing east to the shaft door; the ladder up the west wall: 'Climb up through the hatch?' (q-d26.depths_hatch). Quiet.",
              [], [], {'empty': True}),
    'north': ("North gallery", 'corridor', 'M', "East from the shaft door and the west gallery to the north door (two rooms).",
              [placed(A, 2)], [], {}),
    'column': ("Long gallery", 'corridor', 'M',
               "South from the north door to the Hall of Nine (the juice niches left out, D-69 change 9).",
               [placed(A, 2)], [], {}),
    'hub': ("Hall of Nine", 'hall', 'M',
            "A pillared hall; the plaque 'Nine is the time.' on its east wall (m39.plaque_nine). The lever hall south, the sealed passage west.",
            [placed(A, 2), placed(AU, 2, 'heavy')], [], {}),
    'levers': ("Lever hall", 'room', 'S',
               "Two levers, west and east walls, hover 'Lever' (aaze0052:15): the first pull grinds and calls m39.lever_west/east (the status line, 117841/117842); the slab drops for good, out of sight; then 'The lever won't budge.' (the hook's else line). Quiet.",
               [], [], {'empty': True}),
    'spur': ("Sealed passage", 'corridor', 'S',
             "West and south from the Hall of Nine to lever A's slab (a shut swdoora bulkhead) into the workshop. Quiet.",
             [], [], {'empty': True}),
    'workshop': ("Long workshop", 'hall', 'M',
                 "Machine benches by the walls; the bolted grate in its south wall (the bolt on this side); the pyramid nook west, the west passage north, the east spur east.",
                 [placed(A, 3)], [], {}),
    'pyramid': ("Pyramid nook", 'room', 'S',
                "Dead end: a small dark Ancient pyramid in geometry (hover 'Pyramid', m39.pyramid) and a T6 chest beside it. Quiet.",
                [], [{'kind': 'chest', 'count': 1, 'tier': 6}], {}),
    'wpass': ("West passage", 'corridor', 'M', "North from the workshop to the assembly hall's works door.",
              [placed(A, 2)], [], {}),
    'assembly': ("Assembly hall", 'hall', 'M',
                 "Dead end: Alamar's robot works, stalls of half-built frames, the FEWAEE plaque (aaze0052:14), a T6 chest in the foreman's corner.",
                 [placed(A, 3), placed(AU, 2, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 6}], {}),
    'espur': ("East spur", 'corridor', 'S', "A short spur off the workshop's east end ending in lever B's slab. Quiet.",
              [], [], {'empty': True}),
    'keyvault': ("Key vault", 'room', 'M',
                 "Alamar's strongroom: racks of sealed boxes; on the south wall the box, hover 'Box' (aaze0052:2): the Key to the Dragon Tower (12376) once (117844), then 'Nothing here.' (:16). The warden's door north.",
                 [placed(A, 3)], [], {}),
    'warden': ("Warden's room", 'room', 'M',
               "Consoles (swor2, trekscrn); the warden's chest on the west wall (T6, m39.darkstone_key); the skull door north.",
               [placed(A, 2), placed(AU, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 6}], {}),
    'skull': ("Skull door", 'stair', 'S',
              "Behind the skull door (swtrpnl/swtrdk; m39.skull_door, the Cube, 117845): the lift head, the cage down 768. Quiet.",
              [], [], {'empty': True}),
    'liftfoot': ("Lift foot", 'stair', 'S', "The cage's foot; the stasis vault's pair east. Quiet.", [], [],
                 {'empty': True}),
    'stasis': ("Stasis vault", 'hall', 'M',
               "The set piece: a round chamber, Alamar's machine ring round a dais; on it Roland's steel coffin under the stasis field (xafield), hover 'Coffin' (aaze0052:7); m39.roland drops the field and slides the lid back (both stay so with 111781); a T6 chest by the wall. The goal.",
               [placed(A, 3), placed(AU, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 6}], {'goal': True}),
}
REALISED_BY = {'south': ['south', 'south2'], 'west': ['west', 'west2'], 'north': ['north', 'north2']}

LINKS = [
    ('link:1', 'stair', 'stairhall', 'open', {}),
    ('link:2', 'stairhall', 'south', 'door', {'purpose': "The gallery door."}),
    ('link:3', 'south', 'west', 'door', {'purpose': "The guard door."}),
    ('link:4', 'west', 'north', 'open', {}),
    ('link:5', 'shaft', 'north', 'door', {'purpose': "The shaft door."}),
    ('link:6', 'north', 'column', 'door', {'purpose': "The north door."}),
    ('link:7', 'column', 'hub', 'open', {}),
    ('link:8', 'hub', 'levers', 'open', {}),
    ('link:9', 'hub', 'spur', 'open', {}),
    ('link:10', 'spur', 'workshop', 'door', {'opened_by': 'key:lever_west', 'purpose': "The west slab."}),
    ('link:11', 'workshop', 'pyramid', 'open', {}),
    ('link:12', 'workshop', 'wpass', 'open', {}),
    ('link:13', 'wpass', 'assembly', 'door', {'purpose': "The works door."}),
    ('link:14', 'workshop', 'espur', 'open', {}),
    ('link:15', 'espur', 'keyvault', 'door', {'opened_by': 'key:lever_east', 'purpose': "The east slab."}),
    ('link:16', 'keyvault', 'warden', 'door', {'purpose': "The warden's door."}),
    ('link:17', 'warden', 'skull', 'door', {'opened_by': 'key:cube', 'purpose': "The skull door (the Cube)."}),
    ('link:18', 'skull', 'liftfoot', 'lift', {'purpose': "The lift, 768 down."}),
    ('link:19', 'liftfoot', 'stasis', 'door', {'purpose': "The stasis vault's pair."}),
    ('link:20', 'workshop', 'south', 'door', {'opened_by': 'key:bolt', 'purpose': "The bolted grate."}),
]

PITCH = ("The bottom of Castle Alamar under its ruin: burnt, buckled sw steel round the west maze, two levers that drop "
         "two bulkheads out of sight, Alamar's strongroom with the Dragon Tower's key, the warden's Darkstone key, a "
         "skull door that reads the Cube, and a lift down to the cold round vault where the true Prince Roland lies in "
         "stasis.")
PURPOSE = ("M39 Prince Roland (A3's m39 hooks: statue, plaque_nine, lever_west/east, grate_bolt/grate_bolted, pyramid, "
           "shaft_arrival, darkstone_key, skull_door, roland); Q-F1's key (12376, the map's find); Q-D26's way up "
           "(q-d26.depths_hatch). Class M, party 58-61, monsters 62-75, treasure 6.")
MOOD = ("The castle's machine hum, fainter, and the groan of settling metal; teal plate floors under rust and scorch; "
        "teal pilot lights; the vault cold and blue under the field.")


def space_extent(sid):
    rooms = REALISED_BY.get(sid, [sid])
    xs, ys = [], []
    for r in rooms:
        x0, y0, x1, y1 = geo.bounds(r)
        xs += [x0, x1]
        ys += [y0, y1]
    return [max(xs) - min(xs), max(ys) - min(ys)], [(min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2]


def plan(level):
    spaces = []
    for sid, (name, kind, size, purpose, pop, tre, extra) in SP.items():
        s = {'id': 'room:' + sid, 'name': name, 'kind': {'stair': 'room', 'hall': 'room', 'shaft': 'room'}.get(kind, kind), 'size': size, 'floor': geo.R[sid][2],
             'purpose': purpose}
        if level != 'L1':
            s['extent'], s['at'] = space_extent(sid)
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
            {'id': 'loop:ring', 'spaces': ['room:south', 'room:west', 'room:north', 'room:column', 'room:hub',
                                           'room:spur', 'room:workshop'],
             'notes': "The galleries round the west maze, closed by the bolted grate once its bolt is drawn from the workshop's side (D-69 Q66)."},
        ],
        'entrances': [
            {'id': 'entrance:d6_stair', 'space': 'room:stair', 'kind': 'both', 'neighbour': 'exit:d6_stair',
             'facing': 'w',
             'how': "D6's thing:fd01_stair (the pit hatch in the broken gatehouse, m39.depths_door) brings the party down to the stair's foot facing west; the exit preset at the stair's head is the way back to D6's entrance:fd01_stair."},
            {'id': 'entrance:d7_roof', 'space': 'room:shaft', 'kind': 'both', 'neighbour': 'exit:d7_roof',
             'facing': 'e',
             'how': "D7's roof hatch (q-d26.hatch, after m33.done) sets the party down at the shaft's foot facing east to the shaft door; up by the ladder's Yes/No and q-d26.depths_hatch to D7's entrance:fd01_roof."},
        ],
        'critical_path': ['room:stair', 'room:stairhall', 'room:south', 'room:west', 'room:north', 'room:column',
                          'room:hub', 'room:levers', 'room:hub', 'room:spur', 'room:workshop', 'room:espur',
                          'room:keyvault', 'room:warden', 'room:skull', 'room:liftfoot', 'room:stasis'],
        'return_path': ['room:stasis', 'room:liftfoot', 'room:skull', 'room:warden', 'room:keyvault', 'room:espur',
                        'room:workshop', 'room:south', 'room:stairhall', 'room:stair'],
        'goals': [
            {'id': 'goal:roland', 'space': 'room:stasis', 'kind': 'use',
             'what': "Roland's stasis coffin: m39.roland (done 111781, the Amulet of the Southern Sphinx 12372)."},
        ],
        'keys': [
            {'id': 'key:lever_west', 'grants': {'qbit': 'slab_west'}, 'found_in': 'room:levers', 'how': 'lever',
             'notes': "The west lever: the sealed passage's slab drops for good (m39.lever_west)."},
            {'id': 'key:lever_east', 'grants': {'qbit': 'slab_east'}, 'found_in': 'room:levers', 'how': 'lever',
             'notes': "The east lever: the east spur's slab drops for good (m39.lever_east)."},
            {'id': 'key:bolt', 'grants': {'qbit': 'grate_bolt'}, 'found_in': 'room:workshop', 'how': 'lever',
             'notes': "The grate's bolt, drawn from the workshop's face (m39.grate_bolt)."},
            {'id': 'key:cube', 'grants': {'qbit': 'skull_door_open'}, 'found_in': 'room:warden', 'how': 'item',
             'notes': "The Cube of Power (12365, M33's): every party here carries it (D6's stair asks it; D7's hatch opens only after m33.done)."},
        ],
        'points_of_interest': [
            {'id': 'poi:statue', 'space': 'room:stairhall', 'kind': 'sign',
             'behaviour': "Alamar's statue boasts as the party first comes near (m39.statue, aaze0052:13)."},
            {'id': 'poi:plaque_nine', 'space': 'room:hub', 'kind': 'sign',
             'behaviour': "'Nine is the time.' (m39.plaque_nine, aaze0052:12)."},
            {'id': 'poi:plaque_fewaee', 'space': 'room:assembly', 'kind': 'sign',
             'behaviour': "FEWAEEFFWAEFAWEEWWEFAW / Remember: A = Air, E = Earth, F = Fire, W = Water. (aaze0052:14)."},
            {'id': 'poi:pyramid', 'space': 'room:pyramid', 'kind': 'sign',
             'behaviour': "'Its light is out. Its twin stands outside the gate.' (m39.pyramid)."},
            {'id': 'poi:keybox', 'space': 'room:keyvault', 'kind': 'treasure',
             'behaviour': "The Key to the Dragon Tower once (117844), then 'Nothing here.'"},
            {'id': 'poi:ladder', 'space': 'room:shaft', 'kind': 'exit',
             'behaviour': "'Climb up through the hatch?' then q-d26.depths_hatch."},
        ],
        'mechanisms': [
            {'kind': 'lever drops an unseen slab for good (the status line says where)', 'count': 2},
            {'kind': 'one-way bolted door by side', 'count': 1},
            {'kind': 'hook-checked door (the Cube)', 'count': 1},
            {'kind': 'lift', 'count': 1},
            {'kind': 'field and lid movers on the coffin', 'count': 1},
            {'kind': 'a find once (the key box)', 'count': 1},
        ],
        'totals': {'chests': 4, 'doors': 11, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act6_graphs/fd01.graph.yml; D-69 (mockups/act6_fd01_decisions.md) wins where they differ: lever tells and bulkhead slabs (change 1), the coffin with a sliding lid under the field (2), the vault pair as one swdoorb split (3), the solid swdoorc grate by side (4), q-d26.depths_hatch up to D7's entrance:fd01_roof (5, Q67), the teal statue (8), the niches left out (9), swall4/swall2 walls (Q72 b). The south, west and north galleries are two rooms each (rooms.yml `space`).",
    }


DIAGRAM = """ALAMAR DEPTHS (main level z 0; the stasis vault and the lift foot -768)

 (SHAFT: D7 arrival, ladder up)=shaft door=[NORTH GALLERY 2 ........ 2]=north door=
        |                                                                    [LONG GALLERY 2]
 [WEST GALLERY 3]   [ASSEMBLY 3+2AU $ plaque]          [HALL OF NINE 2+2AU, plaque 9]
        |                 =works door=          [SEALED PASSAGE]-'   |
        |              [WEST PASSAGE 2]              =west slab=   [LEVER HALL: W lever, E lever]
 [PYRAMID $]-----[LONG WORKSHOP 3 ---------------------]--[EAST SPUR]=east slab=[KEY VAULT 3, box]
        |                    =bolted grate=                              =warden's door=
 =guard door=[SOUTH GALLERY 3 .....................]=gallery door=[UNDERCROFT HALL, statue]--[RUIN STAIR -> D6]
                                       [WARDEN 2+AU $]=skull door=[LIFT HEAD] |lift 768| [LIFT FOOT]=pair=[STASIS VAULT 3+AU $ coffin]
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
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:gallery', 'ambient': 16},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "FD-01 Alamar Depths: the main level at z 0, the lift foot and the stasis vault at -768; x east, y north, z up. Written by output/studio_cal/fd01/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
