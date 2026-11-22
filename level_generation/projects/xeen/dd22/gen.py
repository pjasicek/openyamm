#!/usr/bin/env python3
"""Writes DD-22 Sheltem's Pod's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd22/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act5_graphs/dd22.graph.yml with decider D-62,
mockups/act5_a8_decisions_b.md, which wins, and D-65, mockups/act6_a8_decisions.md), project.yml, diagram.txt. L2 adds
positions, L3 rooms.yml, L4 objects.yml, wiring.yml (dress.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/dd22'


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


# Rows (assets_dev/worlds/xeen/source/monsters.yml, A2's robots block 11610; D-62 Q51)
PATROL, ANNIHILATOR = 11610, 11611
LEVEL = {PATROL: 50, ANNIHILATOR: 62}

# D6 (installed, A6): its arrival by the pod's hatch (assets_dev/worlds/xeen/maps/xeen_d6.studio.yml).
D6_HATCH = 'entrance:dd22_hatch'      # (7168, 12288, 1952) facing 1536

QBITS = {
    # map qbits (D-62: 117760-117762 of DD-22's block 117760-117799; A3's names in source/npcs/dd22.yml)
    'dd22_arrived_once': 117760, 'lockdown_released': 117761, 'drive_find': 117762,
}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-22 Sheltem's Pod (the source's Escape Pod 2, dark maze0088, aaze0088) as one "
    "BLV of three decks 448 apart round a lift spine, standing upright in its crater in D6's Ancient field: deck 1 "
    "(0) the airlock, the lower ring, the shaft's foot, the stores, the drive room, the maintenance ladder; deck 2 "
    "(448) the middle ring, the gun deck, the brig, the security post; deck 3 (896) the bridge landing and the bridge "
    "(the set piece). Optional lore for Act VI (A3's dd22 hooks: the security console, the blast door, the weapons, "
    "the drive rack's find, the log computer's six pages and autonote 4139 sheltem_log). Size S (MAPS.md section 0, "
    "D-62): at most 15 sectors and 20 M units squared, doors 3-8, levels 50-62 (band 48-65), party 56-60, treasure 6, "
    "music 46. Graph devdocs/xeen/mockups/act5_graphs/dd22.graph.yml with decider D-62 "
    "(mockups/act5_a8_decisions_b.md, which wins): 20 robots (Patrol 11610 50 x14, Annihilator 11611 62 x6), kill "
    "XP 68,784 for the party, 17.20k per member; three T6 chests and the drive rack's find (117762); the security "
    "console releases the bridge's blast door, one way (D-43, 117761). Rest encounters 10 %: the robots' Patrol at "
    "Dif 0 only (D-62 Q55, A2's row 9175). Map qbits 117760-117762 (block 117760-117799); map_stats 9175.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd22', 'name': "Sheltem's Pod", 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-22', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [6, 6], 'climbs': 'n'},
        'map_stats': {
            'id': 9175, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 6, 'trap_dice': 10,
            'perception_difficulty': 20, 'refill_days': 672, 'music': 46, 'environment': 'stoneroom',
            'lock_difficulty': 20,
            # D-62 Q55: the robots' Patrol only, at Dif 0 (Dif 1+ can roll the Autobot 75), as A2's row 9175
            'slots': [{'monster': 'Xeen Robot', 'tier': 0, 'per_marker': [1, 2], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d6_hatch', 'to': 'xeen_d6.odm', 'kind': 'door', 'arrival': D6_HATCH,
             'arrival_hint': "On D6 (the Forbidden Zone) in the Ancient field, 1,024 south of the pod's centre and 384 off its hull, facing away from it (A6's entrance:dd22_hatch, (7168, 12288, 1952) facing 1536).",
             'notes': "D6 installed by A6: its door:dd22 (thing:sheltem_pod, the round hatch at the hull's base, A3's d6.sheltem_hatch, open once m33.done) is to arrive at this map's entrance:d6_hatch, the airlock (0, -832, 0) facing north (512); until DD-22's install it shows only the hook's line (A6 names the arrival and drops listed_only then). The way out is the exit preset on the hatch's inner face; 'Exit Escape Pod 2?' (aaze0088:1) is its meaning."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': 'pack'}
    d.update(kw)
    return d


FLOORS = {'d1': geo.D1, 'd2': geo.D2, 'd3': geo.D3}
# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    'airlock': ("Airlock", 'room', 'S', 'd1',
                "The arrival (entrance:d6_hatch) behind the round hatch (the exit preset, 'Exit Escape Pod 2?', aaze0088:1); the inner door north. Quiet (D-11.3); map qbit 117760 dd22_arrived_once.",
                [], [], {'empty': True}),
    'ring0': ("Lower ring", 'corridor', 'M', 'd1',
              "An L-shaped corridor round the lift shaft's foot; the maintenance hatch in its east arm (the ladder up).",
              [placed(PATROL, 2)], [], {}),
    'shaft0': ("Lift shaft foot", 'room', 'S', 'd1',
               "The pod's spine: lift A's pad (deck 1 to 2) with its call button; the drive room north, the stores west. Quiet.",
               [], [], {'empty': True}),
    'drive': ("Drive room", 'room', 'M', 'd1',
              "The stern drive under red floor grilles; the two alien devices, dark ('The strange alien device seems to be dormant.', aaze0088:0, D-62 Q53); the stasis generator that carried Sheltem through the crash, cold, and its tool rack (the find: one random T6 item once, 117762, D-62 APPROVAL).",
              [placed(PATROL, 2), placed(ANNIHILATOR, 1)], [], {}),
    'stores': ("Stores", 'room', 'S', 'd1', "A dead end with the pod's stores locker (T6) and barrels by the walls.",
               [placed(PATROL, 2)], [{'kind': 'chest', 'count': 1, 'tier': 6}], {}),
    'ladder': ("Maintenance ladder", 'room', 'S', 'd1',
               "A ladder in the hull's thickness from the lower ring up through the gun deck's floor hatch: the second way between decks 1 and 2 (the loop). Quiet.",
               [], [], {'empty': True}),
    'ring1': ("Middle ring", 'corridor', 'M', 'd2',
              "Lift A's head and lift B's foot in the middle of the ring; doors to the gun deck and the brig. Quiet.",
              [], [], {'empty': True}),
    'gun_deck': ("Gun deck", 'room', 'M', 'd2',
                 "Phaser Control and Photon Control ('A status indicator on the weapon shows it to be disarmed. Fire anyway?', aaze0088:2, :3; Yes: 'Nothing happens.', A3's dd22.weapons); the ladder's hatch in the floor.",
                 [placed(PATROL, 2), placed(ANNIHILATOR, 1)], [], {}),
    'brig': ("The brig", 'room', 'M', 'd2',
             "Two empty stasis cells, their fields dark, where Sheltem shut the Ancients' two agents (log XL70I); the guards' locker (T6) by the wall.",
             [placed(PATROL, 2), placed(ANNIHILATOR, 1)], [{'kind': 'chest', 'count': 1, 'tier': 6}], {}),
    'security': ("Security post", 'room', 'S', 'd2',
                 "The machines' charging alcoves and the security console: 'Security lockdown: bridge sealed. Release?' Yes opens the bridge's blast door, one way (D-43; 117761); the alarm stops.",
                 [placed(ANNIHILATOR, 2), placed(PATROL, 1)], [], {}),
    'bridge_ante': ("Bridge landing", 'corridor', 'S', 'd3',
                    "Lift B's head; the bridge's blast door (two leaves parting in the middle), sealed ('The bridge door is sealed. Security lockdown.', A3's dd22.blast_door) until the security post releases it.",
                    [placed(PATROL, 2)], [], {}),
    'bridge': ("The bridge", 'room', 'M', 'd3',
               "The set piece: Sheltem's empty command couch under the domed viewport of dark steel ribs, the main and scanning consoles flickering red ('The computer seems to be malfunctioning.', aaze0088:5, :6), the log computer paging his six entries (A3's dd22.log_page_1..6; autonote 4139 after the sixth); his locker by the couch (T6).",
               [placed(PATROL, 1), placed(ANNIHILATOR, 1)], [{'kind': 'chest', 'count': 1, 'tier': 6}],
               {'goal': True}),
}

LINKS = [
    ('link:airlock_ring', 'airlock', 'ring0', 'door', {'purpose': "The airlock's inner door."}),
    ('link:ring_shaft', 'ring0', 'shaft0', 'open', {}),
    ('link:shaft_drive', 'shaft0', 'drive', 'open', {}),
    ('link:shaft_stores', 'shaft0', 'stores', 'door', {}),
    ('link:ring_ladder', 'ring0', 'ladder', 'door', {'purpose': "The maintenance hatch."}),
    ('link:lift_a', 'shaft0', 'ring1', 'lift', {'purpose': "Lift A, deck 1 to deck 2."}),
    ('link:ladder', 'ladder', 'gun_deck', 'ladder', {'purpose': "The maintenance ladder up through the gun deck's floor hatch."}),
    ('link:ring_gun', 'ring1', 'gun_deck', 'door', {}),
    ('link:ring_brig', 'ring1', 'brig', 'door', {}),
    ('link:brig_security', 'brig', 'security', 'door', {}),
    ('link:lift_b', 'ring1', 'bridge_ante', 'lift', {'purpose': "Lift B, deck 2 to deck 3."}),
    ('link:blast', 'bridge_ante', 'bridge', 'double_door',
     {'opened_by': 'key:lockdown', 'purpose': "The bridge's blast door: the security console releases it, one way."}),
]

PITCH = ("Sheltem's escape pod, standing upright in its crater on the Darkside: three decks round a lift spine, cold "
         "and red-lit, still kept by his guard machines. A lockdown seals the bridge until the security post below "
         "releases it; on the bridge, under a domed viewport, his empty command couch and the log computer that "
         "still pages his own account, from his break with the Ancients to the crash on Xeen.")
PURPOSE = ("Optional lore for Act VI (MAPS: 'The other ship's log (six pages); opens after M33'): D6's hatch opens once "
           "m33.done (A3's d6.sheltem_hatch). The security console (dd22.security_console) opens the blast door; the "
           "log computer pages dd22.log_page_1..6 (autonote 4139 sheltem_log); the gun deck's weapons "
           "(dd22.weapons); the drive rack's find (dd22.drive_rack). Class S, party 56-60, robots 50-62.")
MOOD = ("MM6's Control Center in its red accents: dark teal hull panels and rust ceilings in cold light, red pilot "
        "lights and red floor grids where the pod still works; the bridge's red glow under a dome of dark steel ribs.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, pop, tre, extra) in SP.items():
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[fl], 'purpose': purpose}
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
            {'id': 'loop:decks', 'spaces': ['room:ring0', 'room:shaft0', 'room:ring1', 'room:gun_deck', 'room:ladder'],
             'notes': "Up by lift A, down by the gun deck's ladder (or the other way): two ways between decks 1 and 2."},
        ],
        'entrances': [
            {'id': 'entrance:d6_hatch', 'space': 'room:airlock', 'kind': 'both', 'neighbour': 'exit:d6_hatch',
             'facing': 'n',
             'how': "D6's hatch (A6's door:dd22, A3's d6.sheltem_hatch once m33.done) brings the party into the airlock 192 inside the hatch, facing north; the hatch's inner face is the way back to D6's entrance:dd22_hatch."},
        ],
        'critical_path': ['room:airlock', 'room:ring0', 'room:shaft0', 'room:ring1', 'room:brig', 'room:security',
                          'room:brig', 'room:ring1', 'room:bridge_ante', 'room:bridge'],
        'return_path': ['room:bridge', 'room:bridge_ante', 'room:ring1', 'room:gun_deck', 'room:ladder',
                        'room:ring0', 'room:airlock'],
        'goals': [
            {'id': 'goal:lockdown', 'space': 'room:security', 'kind': 'use',
             'what': "'Security lockdown: bridge sealed. Release?' Yes (dd22.security_console: lockdown_released 117761): the blast door opens for good."},
            {'id': 'goal:log', 'space': 'room:bridge', 'kind': 'use',
             'what': "The log computer's six pages (dd22.log_page_1..6); the sixth adds autonote 4139 sheltem_log."},
        ],
        'keys': [
            {'id': 'key:lockdown', 'grants': {'qbit': 'lockdown_released'}, 'found_in': 'room:security', 'how': 'lever',
             'notes': "The security console's release opens the bridge's blast door, one way (D-43)."},
        ],
        'points_of_interest': [
            {'id': 'poi:devices', 'space': 'room:drive', 'kind': 'sign', 'count': 2,
             'behaviour': "'The strange alien device seems to be dormant.' (aaze0088:0; D-62 Q53 dressing)."},
            {'id': 'poi:rack', 'space': 'room:drive', 'kind': 'cache',
             'behaviour': "The stasis generator's tool rack: one random T6 item once (drive_find 117762, dd22.drive_rack), then 'Nothing here.'."},
            {'id': 'poi:weapons', 'space': 'room:gun_deck', 'kind': 'sign', 'count': 2,
             'behaviour': "Phaser and Photon Control: 'Fire anyway?' Yes: 'Nothing happens.' (aaze0088:2, :3; dd22.weapons)."},
            {'id': 'poi:consoles', 'space': 'room:bridge', 'kind': 'sign', 'count': 2,
             'behaviour': "Main and Scanning Console: 'The computer seems to be malfunctioning.' (aaze0088:5, :6)."},
            {'id': 'poi:cells', 'space': 'room:brig', 'kind': 'sign', 'count': 2,
             'behaviour': "Two empty stasis cells, their fields dark."},
        ],
        'mechanisms': [
            {'kind': 'one-way console releases a two-leaf blast door', 'count': 1},
            {'kind': 'paged log computer wrapping round (map variable)', 'count': 1},
            {'kind': 'two-stop lift with call buttons', 'count': 2},
            {'kind': 'ladder through a floor hatch (the loop)', 'count': 1},
        ],
        'totals': {'chests': 3, 'doors': 8, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act5_graphs/dd22.graph.yml; D-62 (mockups/act5_a8_decisions_b.md) wins where they differ: 20 robots, the drive rack's find (117762), Patrol at Dif 0. Changes from the graph (A8 L2): the lift spine is two lifts side by side (A deck 1 to 2, B deck 2 to 3; a lift has two stops), each rising through a hole in the deck above, so the middle ring and the bridge landing are the lifts' landings and the shaft's foot is the only shaft room; the drive room is one room (12 rooms, 12 sectors). Doors: the airlock's inner door, the stores', the maintenance hatch, the gun deck's, the brig's, the security post's, the blast door (two leaves); the hatch is the exit face (8 with the graph's count).",
    }


DIAGRAM = """DECK 3 (896)
              [BRIDGE: dome, couch, main + scanning consoles, log computer, Sheltem's locker $; 1 P + 1 A]
                   ||blast door (two leaves; released by the security console)
              [BRIDGE LANDING: lift B's head; 2 P]
DECK 2 (448)        ^ lift B
 [SECURITY: console, alcoves; 2 A + 1 P]
      =door=
 [BRIG: 2 dark cells, locker $; 2 P + 1 A] =door= [MIDDLE RING: lift A's head, lift B's foot] =door= [GUN DECK: phaser, photon; 2 P + 1 A]
                                                        ^ lift A                                     | ladder hatch
DECK 1 (0)                                                                                           |
              [DRIVE: grilles, 2 dormant devices, stasis generator + rack (find); 2 P + 1 A]          |
                    |                                                                                |
 [STORES $; 2 P] =door= [SHAFT FOOT: lift A]       [LOWER RING east arm] =maintenance hatch= [LADDER]
                          |                              |
                 [LOWER RING south arm: 2 P] ------------+
                          =door=
                 [AIRLOCK: arrival; the hatch = exit to D6]
 $ chest   P Patrol 11610   A Annihilator 11611
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:hull', 'ambient': 14},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-22 Sheltem's Pod: deck 1 at 0, deck 2 at 448, deck 3 at 896, in one frame (x east, y north, z up; the lift spine at x 0). Written by output/studio_cal/dd22/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)
        dump(folder / 'atmosphere.yml', {
            'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_day'},
            'notes': "The bridge's domed viewport: its oculus (the dome's flat top) is a sky face open to the Darkside's sky: the day preset (D-67: the pod opens only after M33, when the sun is whole again; never the alias xeendark1)."})


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
