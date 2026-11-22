#!/usr/bin/env python3
"""Writes XD-11's project folders: `gen.py L1|L2|L3|L4` writes devdocs/xeen/briefs/xd11/<level>.

L1: plan.yml (the graph, D-4's decisions), project.yml, diagram.txt. L2: the plan with positions, extents and floor
heights. L3: + rooms.yml (geo.py). L4: + objects.yml, wiring.yml, atmosphere.yml (dress.py). The playtests and
NOTES.md are written by hand in L4.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/xd11'


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


NOTES_PROJECT = (
    "Xeen design brief for a new map (no original): XD-11 Tower of High Magic, story step M13 (QUESTS.md; "
    "source/quests/m13.yml): the Skeleton Key to Darzog's Tower lies in the Archmage's study at the top. Size M "
    "(MAPS.md section 0 and Dungeons): 20-45 sectors, 30-90 M units squared, about 50 monsters at levels 18-32, "
    "party 18-20, Tres 3; graph devdocs/xeen/mockups/act2_graphs/xd11.graph.yml with decider D-4's decisions "
    "(mockups/act2_dungeon_decisions.md). Rows (A2): slot 1 Magic constructs (Xeen Construct; markers tier a, "
    "Flying Feet 11600, on the ground and first floors; tier b, Guardian 11601, above); placed Sorceresses 11180 and "
    "the Head Sorceress 11185 (carries the Librarian's Key 12260). Items: Librarian's Key 12260, Skeleton Key 12100 "
    "(given by A3's hook m13.skeleton_key), the Prismatic Light spellbook (engine 483). Player bits 11246-11251 (the "
    "six brews, +5 resistance once per character). Map_stats 9127 (source/maps.yml: music 34, treasure 3). Both "
    "neighbours are linked: the enchanted door to X3's islet, the cloud stair to X8 (NOTES.md, Exits).")


# D-89 identity (A8 s29): an octagonal tower in Celeste's pale set (MM7 7d25), laboratories furnished from MM7's
# wizard houses.
IDENTITY = {'shape': 'tower', 'family': '7d25',
            'seen': ["an octagonal tower: slanted corner walls and windows to the sky on every floor, a crenellated roof",
                     "six laboratories, each under its own coloured light, with benches of glassware and a brew",
                     "the Library of High Magic and the Archmage's study with his books across the tower's corner"]}


def project(level):
    return {
        'format': 0, 'id': 'xeen_xd11', 'name': 'Tower of High Magic', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'XD-11', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [8, 8], 'climbs': 'n'},
        'map_stats': {
            'id': 9127, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 3, 'trap_dice': 3,
            'perception_difficulty': 6, 'refill_days': 672, 'music': 34, 'environment': 'stone hall',
            'lock_difficulty': 6,
            'slots': [{'monster': 'Xeen Construct', 'tier': 0, 'per_marker': [2, 3], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:x3_door', 'to': 'xeen_x3.odm', 'kind': 'door', 'arrival': [256, -1674, 992],
             'arrival_hint': "On X3 (Lifeforce Lagoon), in front of the Tower of High Magic's enchanted door in the swamp, facing away from it.",
             'direction': 90,
             'notes': "X3 installed (A5, 2026-11-20): the enchanted door asks 'Leave the Tower of High Magic?' and on Yes leaves for X3's islet in front of the door (briefs/x3/DOORS.md, thing:high_magic: 256, -1674, 992 facing north). X3's door needs the Enchanted Key 12306 (A3's m13.tower_door); leaving needs nothing."},
            {'id': 'exit:x8_clouds', 'to': 'xeen_x8.blv', 'kind': 'roof', 'arrival': [-10752, -4337, 0],
             'arrival_hint': "On X8 (Cloudreach), the High Magic clouds' landing at the head of the Stairway to Heaven.",
             'direction': 90,
             'notes': "X8 installed (A6, 2026-11-20): the roof's cloud stair asks 'Stairway to Heaven. Climb?' and on Yes leaves for X8's High Magic clouds at -10752, -4337, 0 facing north (the orchestrator's explicit arrival). X8's falls land on X3 (X2 until X3 exists)."},
        ],
        'qbits': {'skeleton_key_found': 111260, 'arrived_once': 110680},
        'items': {'enchanted_key': 12306, 'librarian_key': 12260, 'prismatic_light': 483, 'skeleton_key': 12100},
        'notes': NOTES_PROJECT,
    } | ({'identity': IDENTITY} if level == 'L4' else {})


# ------------------------------------------------------------------------------------------------- the plan
SP = {
    # id: (kind, size, floor index, purpose, population, treasure, extra)
    'door': ('room', 'S', 0, "Inside the enchanted door the Enchanted Key opened: the arrival, and the way out to X3's islet.", [], [], {}),
    'foyer': ('room', 'M', 0, "Flying feet hop about the tiles between the pillars.",
              [{'slot': 1, 'groups': 2, 'per_marker': [2, 3], 'levels': [18, 18], 'strength': 'pack', 'rank': 'a'}], [], {}),
    'athanor': ('room', 'L', 0, "The great furnace over its hearth of coals; the Fire Brew (+5 Fire resistance once per character).",
                [{'slot': 1, 'groups': 2, 'per_marker': [2, 3], 'levels': [18, 18], 'strength': 'pack', 'rank': 'a'}], [], {}),
    'coils': ('room', 'M', 0, "Crackling coils; the Electric Brew (+5 Air resistance); the east stair; the lift core's door.",
              [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [18, 18], 'strength': 'pack', 'rank': 'a'}], [], {}),
    'core0': ('corridor', 'S', 0, "The foot of the lift shaft: the cage to the first floor (lift 0-1) stops here.", [], [], {'empty': True}),
    'east_stair': ('corridor', 'M', [0, 640], "The east stair, ground floor to the first.", [], [], {'empty': True}),
    'landing1': ('corridor', 'S', 1, "Up from the ground floor; the lever of the first-floor lift gate (state:gate1).",
                 [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [18, 18], 'strength': 'light', 'rank': 'a'}], [], {}),
    'core1': ('corridor', 'S', 1, "The lift shaft at the first floor: lift 0-1's top, lift 1-2's foot.", [], [], {'empty': True}),
    'still': ('room', 'M', 1, "A frosted still; the Cold Brew (+5 Water resistance); the steam pipe runs through.",
              [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [18, 18], 'strength': 'pack', 'rank': 'a'}], [], {}),
    'reagents': ('room', 'S', 1, "Jars and sacks; the steam valve that thaws the frost seal; a Pandorian Box ('The box is empty.').",
                 [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [18, 18], 'strength': 'light', 'rank': 'a'}],
                 [{'kind': 'chest', 'count': 1, 'tier': 0}], {}),
    'poison': ('room', 'M', 1, "Nightshade in raised beds; the Poison Brew (+5 Body resistance); the frozen door west.",
               [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [18, 18], 'strength': 'pack', 'rank': 'a'}], [], {}),
    'west_stair': ('corridor', 'M', [640, 1280], "The west stair behind the frost-sealed door, first floor to the second.", [], [], {'empty': True}),
    'landing2': ('corridor', 'S', 2, "Up from the cold floor.",
                 [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [24, 24], 'strength': 'light', 'rank': 'b'}], [], {}),
    'energy': ('room', 'M', 2, "Crystals under a yellow glow; the Energy Brew (+5 Earth resistance).",
               [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [24, 24], 'strength': 'pack', 'rank': 'b'}], [], {}),
    'magic': ('room', 'M', 2, "The Magic Brew (+5 Mind resistance) on its dais; the Head Sorceress, who carries the Librarian's Key.",
              [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [24, 24], 'strength': 'light', 'rank': 'b'},
               {'actor': 'Sorceress', 'groups': 2, 'levels': [30, 30], 'placed': True, 'strength': 'heavy'},
               {'actor': 'Head Sorceress', 'role': 'carries the Librarian\'s Key', 'groups': 1, 'levels': [32, 32], 'placed': True, 'strength': 'boss'}], [], {}),
    'quarters': ('room', 'M', 2, "Beds ('There is nothing on, in, or under the bed.'), a chest; the second lift gate's lever; the Librarian's door up.",
                 [{'actor': 'Sorceress', 'groups': 2, 'levels': [30, 30], 'placed': True, 'strength': 'heavy'}],
                 [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'core2': ('corridor', 'S', 2, "The lift shaft at the second floor: lift 1-2's top, lift 2-3's foot.", [], [], {'empty': True}),
    'high_stair': ('corridor', 'M', [1280, 1920], "The stair from the quarters to the top floor, behind the Librarian's door.", [], [], {'empty': True}),
    'landing3': ('corridor', 'S', 3, "The library's arch; the top lift gate and its lever.",
                 [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [24, 24], 'strength': 'light', 'rank': 'b'}], [], {}),
    'core3': ('corridor', 'S', 3, "The lift shaft's top stop: from here the cages go straight down to the door.", [], [], {'empty': True}),
    'library': ('room', 'L', 3, "Bookcases; The Art of Magic to read on its lectern; the cabinet of Mysteries of Light holds the Prismatic Light spellbook.",
                [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [24, 24], 'strength': 'light', 'rank': 'b'},
                 {'actor': 'Sorceress', 'groups': 2, 'levels': [30, 30], 'placed': True, 'strength': 'heavy'}],
                [{'kind': 'chest', 'count': 1, 'tier': 3, 'item': 'prismatic_light'}], {}),
    'study': ('room', 'M', 3, "The Archmage's chest: 'You found a skeleton key in the chest.' (M13, A3's hook).",
              [{'actor': 'Sorceress', 'groups': 2, 'levels': [30, 30], 'placed': True, 'strength': 'heavy'}],
              [{'kind': 'chest', 'count': 1, 'tier': 3, 'item': 'skeleton_key'}], {'goal': True}),
    'observatory': ('room', 'M', 3, "An orrery under a painted sky; a Pandorian Box (a trapped chest).",
                    [{'actor': 'Sorceress', 'groups': 2, 'levels': [30, 30], 'placed': True, 'strength': 'heavy'}],
                    [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'stairway': ('corridor', 'M', [1920, 2560], "'Stairway to Heaven.' One flight from the top floor up into the open sky.", [], [], {'empty': True}),
    'roof': ('room', 'L', 4, "Open sky over the lagoon; the stair of cloud climbs on toward the High Magic clouds (X8).",
             [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [24, 24], 'strength': 'light', 'rank': 'b'}], [], {}),
}

LINKS = [
    ('link:door_foyer', 'door', 'foyer', 'open', {}),
    ('link:foyer_athanor', 'foyer', 'athanor', 'door', {}),
    ('link:athanor_coils', 'athanor', 'coils', 'open', {}),
    ('link:coils_core0', 'coils', 'core0', 'door', {}),
    ('link:coils_l1', 'coils', 'landing1', 'stairs', {'purpose': "The east stair (room:east_stair)."}),
    ('link:l1_still', 'landing1', 'still', 'open', {}),
    ('link:still_reagents', 'still', 'reagents', 'door', {}),
    ('link:still_poison', 'still', 'poison', 'open', {}),
    ('link:poison_l1w', 'poison', 'west_stair', 'door', {'condition': {'map_var': 'frost_thawed'}, 'opened_by': 'poi:steam_valve',
                                                          'purpose': "The frost seal: frozen shut until the steam valve in the reagent store is opened."}),
    ('link:l1_core1', 'landing1', 'core1', 'door', {'condition': {'map_var': 'gate1_open'}, 'opened_by': 'poi:gate1_lever'}),
    ('link:l1w_l2', 'west_stair', 'landing2', 'stairs', {'purpose': "The west stair."}),
    ('link:l2_energy', 'landing2', 'energy', 'open', {}),
    ('link:energy_magic', 'energy', 'magic', 'door', {}),
    ('link:magic_quarters', 'magic', 'quarters', 'open', {}),
    ('link:quarters_core2', 'quarters', 'core2', 'door', {'condition': {'map_var': 'gate2_open'}, 'opened_by': 'poi:gate2_lever'}),
    ('link:quarters_l3', 'quarters', 'landing3', 'door', {'condition': {'item': 'librarian_key'},
                                                             'purpose': "The Librarian's door, then the stair up (room:high_stair)."}),
    ('link:l3_library', 'landing3', 'library', 'open', {}),
    ('link:library_study', 'library', 'study', 'door', {}),
    ('link:study_obs', 'study', 'observatory', 'open', {}),
    ('link:obs_stairway', 'observatory', 'stairway', 'open', {}),
    ('link:l3_core3', 'landing3', 'core3', 'door', {'condition': {'map_var': 'gate3_open'}, 'opened_by': 'poi:gate3_lever'}),
    ('link:stairway_roof', 'stairway', 'roof', 'stairs', {}),
    ('link:core_01', 'core0', 'core1', 'lift', {'condition': {'map_var': 'gate1_open'}, 'purpose': "Lift 0-1 runs once gate 1 is open."}),
    ('link:core_12', 'core1', 'core2', 'lift', {'condition': {'map_var': 'gate2_open'}, 'purpose': "Lift 1-2 runs once gate 2 is open."}),
    ('link:core_23', 'core2', 'core3', 'lift', {'condition': {'map_var': 'gate3_open'}, 'purpose': "Lift 2-3 runs once gate 3 is open."}),
]

PITCH = ("The Tower of High Magic stands in the swamp of Lifeforce Lagoon: a pale plaster tower of four alchemy floors "
         "round a lift shaft, built by an Archmage who kept six brews, one to a laboratory, that harden whoever drinks "
         "them against the elements. Flying feet and guardian constructs keep the lower floors; sorceresses the upper. "
         "The stairs climb the east, west and east sides in turn so that every floor is crossed; a steam valve thaws "
         "the frozen door of the west stair; the Head Sorceress carries the Librarian's Key to the top floor; at each "
         "landing a lever unbolts the lift gate so the brass cages become a quick way down. At the top the Archmage's "
         "study holds the Skeleton Key to Darzog's Tower, and the Stairway to Heaven climbs out onto the roof under "
         "the open sky, where a stair of cloud goes on toward the High Magic clouds.")
PURPOSE = ("Story step M13 (QUESTS.md): the Skeleton Key to Darzog's Tower, from the Archmage's chest (A3's hook "
           "m13.skeleton_key). Six permanent rewards (+5 to one resistance per brew, once per character, D-4) and the "
           "Prismatic Light spellbook. Class M, party 18-20, monsters 18-32.")
MOOD = "Pale, bright and strange: plaster and marble lit warm by sconces, each laboratory in its own glow (furnace red, coil blue, frost white, poison green, energy yellow, magic violet); wind and open sky on the roof."


def plan(level):
    spaces = []
    for sid in sorted(SP):
        kind, size, fl, purpose, pop, tre, extra = SP[sid]
        name, b, flz, ce, theme = geo.R[sid]
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size}
        if level != 'L1':
            o = geo.outline(sid)
            xs = [p[0] for p in o]
            ys = [p[1] for p in o]
            s['extent'] = [max(xs) - min(xs), max(ys) - min(ys)]
            s['at'] = [(max(xs) + min(xs)) // 2, (max(ys) + min(ys)) // 2]
        if isinstance(fl, list):
            s['floor'] = fl
        else:
            s['floor'] = geo.FL[fl]
        s['clear_height'] = ce - flz if level != 'L1' else (geo.H if sid not in ('roof',) else 1024)
        s['purpose'] = purpose
        if level != 'L1':
            s['theme'] = {'theme:ground': "Celeste (7d25): rubble hwm2wall, marble 7tws1f, beams hwm2rf, doors hwm2d",
                          'theme:lab': "Celeste (7d25): plaster hwp1bwall, marble 7tws1f, beams hwm2rf, sigil door hwp1d",
                          'theme:study': "Celeste (7d25) planks hwr1wall, marble t2s1fl; Clanker's Laboratory (7d12) bookcases 7t1books",
                          'theme:observatory': "Celeste (7d25): plaster, the painted sky 7plansky1",
                          'theme:core': "Celeste (7d25) rubble; the world's brass grille xngrille on the gates",
                          'theme:roof': "Celeste (7d25) marble and rubble parapet under the open sky",
                          'theme:skystair': "Celeste (7d25) rubble, open to the sky"}[theme]
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
        'format': 0, 'level': 'L1' if level == 'L1' else ('L2' if level == 'L2' else 'L3'),
        'pitch': PITCH, 'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:core', 'spaces': ['room:coils', 'room:east_stair', 'room:landing1', 'room:core1', 'room:core0'],
             'notes': "Up the east stair, down in the cage once gate 1 is open; likewise for each floor."},
            {'id': 'loop:tower', 'spaces': ['room:landing1', 'room:still', 'room:poison', 'room:west_stair', 'room:landing2',
                                            'room:energy', 'room:magic', 'room:quarters', 'room:core2', 'room:core1'],
             'notes': "Up the stairs, back down the core."},
        ],
        'entrances': [
            {'id': 'entrance:x3_door', 'space': 'room:door', 'kind': 'both', 'neighbour': 'exit:x3_door', 'facing': 'n',
             'notes': "The enchanted door asks 'Leave the Tower of High Magic?' and leaves for X3's islet on Yes."},
            {'id': 'entrance:x8_clouds', 'space': 'room:roof', 'kind': 'both', 'neighbour': 'exit:x8_clouds',
             'notes': "Sealed until X8 is built: the stair of cloud asks 'Stairway to Heaven. Climb?' and will not bear the party yet."},
        ],
        'critical_path': ['room:door', 'room:foyer', 'room:athanor', 'room:coils', 'room:east_stair', 'room:landing1',
                          'room:still', 'room:reagents', 'room:still', 'room:poison', 'room:west_stair', 'room:landing2',
                          'room:energy', 'room:magic', 'room:quarters', 'room:high_stair', 'room:landing3',
                          'room:library', 'room:study'],
        'return_path': ['room:study', 'room:library', 'room:landing3', 'room:core3', 'room:core2', 'room:core1',
                        'room:core0', 'room:coils', 'room:athanor', 'room:foyer', 'room:door'],
        'goals': [{'id': 'goal:skeleton_key', 'space': 'room:study', 'kind': 'use',
                   'what': "Open the Archmage's chest: the Skeleton Key (A3's hook m13.skeleton_key: the key, qbit 111260, 6,000 experience)."}],
        'keys': [
            {'id': 'key:steam_valve', 'grants': {'map_var': 'frost_thawed'}, 'found_in': 'room:reagents', 'how': 'lever'},
            {'id': 'key:librarian_key', 'grants': {'item': 'librarian_key'}, 'found_in': 'room:magic', 'how': 'carried',
             'notes': "The Head Sorceress carries it; her corpse holds it."},
            {'id': 'key:gate1', 'grants': {'map_var': 'gate1_open'}, 'found_in': 'room:landing1', 'how': 'lever'},
            {'id': 'key:gate2', 'grants': {'map_var': 'gate2_open'}, 'found_in': 'room:quarters', 'how': 'lever'},
            {'id': 'key:gate3', 'grants': {'map_var': 'gate3_open'}, 'found_in': 'room:landing3', 'how': 'lever'},
        ],
        'points_of_interest': [
            {'id': 'poi:steam_valve', 'space': 'room:reagents', 'kind': 'lever',
             'behaviour': "The steam valve: the pipes hiss along the walls to the garden and the frozen door thaws and opens (two states)."},
            {'id': 'poi:gate1_lever', 'space': 'room:landing1', 'kind': 'lever', 'behaviour': "Unbolts the first-floor lift gate; lift 0-1 runs from now on."},
            {'id': 'poi:gate2_lever', 'space': 'room:quarters', 'kind': 'lever', 'behaviour': "Unbolts the second-floor lift gate; lift 1-2 runs."},
            {'id': 'poi:gate3_lever', 'space': 'room:landing3', 'kind': 'lever', 'behaviour': "Unbolts the top lift gate; lift 2-3 runs: straight down to the door."},
            {'id': 'poi:brews', 'spaces': ['room:athanor', 'room:coils', 'room:still', 'room:poison', 'room:energy', 'room:magic'],
             'kind': 'fountain', 'count': 6,
             'behaviour': "Fire, Electric, Cold, Poison, Energy and Magic Brew: +5 to Fire, Air, Water, Body, Earth, Mind resistance, once per character (player bits 11246-11251)."},
            {'id': 'poi:art_of_magic', 'space': 'room:library', 'kind': 'sign', 'behaviour': "The Art of Magic: a book to read (lore only, D-4)."},
            {'id': 'poi:beds', 'space': 'room:quarters', 'kind': 'sign', 'behaviour': "'There is nothing on, in, or under the bed.'"},
        ],
        'mechanisms': [
            {'kind': 'click door', 'count': 4}, {'kind': 'lever-operated lift gate', 'count': 3},
            {'kind': 'stacked lift', 'count': 3}, {'kind': 'frozen door thawed by a valve', 'count': 1},
            {'kind': 'keyed door', 'count': 1}, {'kind': 'once-per-character brew', 'count': 6},
        ],
        'totals': {'chests': 5, 'doors': 10, 'rooms': len(SP), 'spawn_points': 15},
        'notes': "Graph: devdocs/xeen/mockups/act2_graphs/xd11.graph.yml; D-4 (mockups/act2_dungeon_decisions.md) wins where they differ: stacked lifts, brews +5 resistance once per character, the Art of Magic lore only, a Prismatic Light spellbook in a chest, no fire dragon or Carnage Hands. Floors at 0, 640, 1280, 1920, the roof at 2560.",
    }


DIAGRAM = """ROOF (+2560)  [roof terrace, open sky] -- stair of cloud ==> X8 High Magic clouds
                ^ Stairway to Heaven (NW, open to the sky)
TOP (+1920)   [observatory: Pandorian Box $]-[ARCHMAGE'S STUDY: chest $ SKELETON KEY]-door-[LIBRARY: Art of Magic, cabinet $ Prismatic Light]
                                                                   |
                                    [top landing: GATE 3 lever]-arch    [CORE 3] <- gate 3
                ^ east stair, behind the LIBRARIAN'S DOOR
2ND (+1280)   [west landing]-arch-[ENERGY LAB: Energy Brew]-door-[MAGIC LAB: Magic Brew, HEAD SORCERESS (Librarian's Key)]
                                                                   |
                                         [CORE 2] <- gate 2 -[QUARTERS: beds, chest $, GATE 2 lever]
                ^ west stair, behind the FROZEN DOOR
1ST (+640)    [reagents: STEAM VALVE, Pandorian Box (empty)]-door-[COLD STILL: Cold Brew]-arch-[east landing: GATE 1 lever]
                                    [POISON GARDEN: Poison Brew]-FROZEN DOOR-> west stair            [CORE 1] <- gate 1
                ^ east stair
GROUND (0)    [ENCHANTED DOOR] (X3)         -arch-[FOYER]-door-[ATHANOR: Fire Brew]-arch-[LIGHTNING COILS: Electric Brew]-door-[CORE 0]
LIFT CORE: three stacked short lifts in one shaft (0-1 west half, 1-2 east, 2-3 west), each runs once its upper gate's lever is pulled.
 $ chest   stairs alternate E / W / E, so every floor is crossed.
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        rooms = [geo.room_doc(r) for r in geo.ORDER]
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:lab', 'ambient': 16}, 'rooms': rooms,
            'openings': geo.OPENINGS,
            'notes': "XD-11 Tower of High Magic: a square tower 4,096 across inside, four floors 640 apart (0, 640, 1280, 1920) round a lift core, and a roof terrace at 2560 under the open sky. Stairs alternate east (0-640), west (640-1280), east (1280-1920); the Stairway to Heaven climbs to the roof. Written by output/studio_cal/xd11/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
