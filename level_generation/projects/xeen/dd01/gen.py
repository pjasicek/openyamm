#!/usr/bin/env python3
"""Writes DD-01 Castleview Sewer's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd01/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act3_graphs/dd01.graph.yml with decider D-26,
mockups/act3_a8_decisions_a.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
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
BR = R / 'devdocs/xeen/briefs/dd01'


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
DIRE, VBAT, GREM, SAB, WERE, ROOKA, VALIO = 11393, 11311, 11020, 11021, 11400, 11403, 11193
LEVEL = {DIRE: 10, VBAT: 14, GREM: 14, SAB: 18, WERE: 18, ROOKA: 24, VALIO: 45}

# D1 (installed, A6): the hatch thing:dd01_hatch at sketch cell [66.5, 57.5] = (1280, 3328); the outfall grate
# thing:dd01_outfall at [79, 48] = (7680, 8192) (OutdoorThings toWorld: (cell - 64) * 512, (64 - cell) * 512).
# A6's return points (2026-11-20): D1 event 145 (the hatch) and event 222 (the outfall), facing 0 (east).
HATCH_ARRIVAL = [1024, 3072, 1152]
HATCH_DIR = 0
OUTFALL_ARRIVAL = [8192, 8192, 832]
OUTFALL_DIR = 0

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-01 Castleview Sewer (the source's dark/aaze0030 sewer), story step M16 "
    "(Nadia's onyx necklace in the rats' nest, A3's hook m16.necklace) and side quest Q-D5 (Valio and Rooka the Rat "
    "Queen: hooks q-d5.rooka, q-d5.valio_chest, q-d5.valio_angry). Size M (MAPS.md section 0): 20-45 sectors, 30-90 M "
    "units squared, 50 monsters at levels 10-20, Rooka the Rat Queen 24, party 18-20, treasure 2 (hoard 3). Graph "
    "devdocs/xeen/mockups/act3_graphs/dd01.graph.yml with decider D-26 (mockups/act3_a8_decisions_a.md, which wins): "
    "one working hatch, four ladders to grates bolted from above, the outfall a two-way exit once its bar is lifted, "
    "the sluice's lever drains the flooded culvert (a sinking water mover), the cellar's floor grate bolted from "
    "below, Dire Rats 11393 for the Bat Queens. Rows (A2): rats 11390 (Dire Rat 11393, 21), night bats 11310 "
    "(Vampire Bat 11311, 8), gremlins 11020 (Gremlin 11020, 10; Gremlin Saboteur 11021, 3), sewer stalkers 11400 "
    "(Wererat 11400, 7; Rooka the Rat Queen 11403); Valio 11193 (45) placed hidden, shown when angered (D-1.2: not "
    "counted). Kill XP 16,104 for the party, 4.03k per member. Talking people (NPC rows of source/towns/d1.yml): "
    "Valio the Simple 4957 in his bed, Felix the Tinker 4958 at his bench. Map qbits 117000-117039 (provisional); "
    "player bits 11310, 11311 (the liquids, provisional). Map_stats 9150 (source/maps.yml: music 44, treasure 2).")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd01', 'name': 'Castleview Sewer', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-01', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [20, 16], 'climbs': 'n'},
        'map_stats': {
            'id': 9150, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 2,
            'perception_difficulty': 3, 'refill_days': 672, 'music': 44, 'environment': 'stoneroom',
            'lock_difficulty': 3,
            'slots': [{'monster': 'Xeen Rat', 'tier': 3, 'per_marker': [2, 3], 'weight': 50},
                      {'monster': 'Xeen Gremlin', 'tier': 0, 'per_marker': [2, 3], 'weight': 30},
                      {'monster': 'Xeen Sewer Stalker', 'tier': 0, 'per_marker': [1, 2], 'weight': 20}],
        },
        'neighbours': [
            {'id': 'exit:d1_hatch', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': HATCH_ARRIVAL,
             'arrival_hint': "On D1 (Castleview Vale), beside the iron hatch at the square's south-east corner, at A6's return point (facing east).",
             'direction': HATCH_DIR,
             'notes': "D1 installed by A6; its hatch (thing:dd01_hatch, sketch [66.5, 57.5] = (1280, 3328)) leads here (D1 door:dd01, the map's start at the ladder's foot). 'Exit the Sewer?' (dark/aaze0030) is the meaning of the game's leave window."},
            {'id': 'exit:d1_outfall', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': OUTFALL_ARRIVAL,
             'arrival_hint': "On D1, in the mill gorge east of the sewer's outfall grate by the burnt mill, at A6's return point, facing east, away from it.",
             'direction': OUTFALL_DIR,
             'notes': "D1's outfall grate (thing:dd01_outfall, sketch [79, 48] = (7680, 8192)) is barred from inside until this map's bar sets q-d5.outfall_unbarred (117001); D1's grate event (D1 event 222) reads it. D1's way in at the outfall should land at (4096, -4864, -512) facing west (this map's outfall, inside the grate): A6."},
        ],
        'qbits': {'arrived_once': 117000, 'outfall_unbarred': 117001, 'guard_purse': 117002,
                  'rooka_slain': 113101, 'valio_angered': 113104},
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    'shaft_square': ("Square shaft (the hatch)", 'room', 'S', 0,
                     "The iron hatch by the square's south-east corner: the ladder down, and the way in and out (D1 door:dd01).",
                     [], [], {'empty': True}),
    'cross': ("The drain cross", 'room', 'L', 0,
              "Four drains meet under the square in a vaulted cross on four piers; lamplight down the hatch shaft.",
              [], [], {'empty': True}),
    'west_drain': ("West drain", 'corridor', 'M', 0, "A walk either side of a slow channel; rats on the walks.",
                   [placed(DIRE, 4)], [], {}),
    'shaft_west': ("West shaft (guild row)", 'room', 'S', 0,
                   "A ladder up to a grate bolted from above (the guild row). On a ledge: a flask of Red Liquid (+2 Might, once per character).",
                   [], [], {'empty': True}),
    'sluice': ("The jammed sluice", 'room', 'L', 0,
               "The town's sluice house, its gate wedged half open by gremlins with stolen mill gears. The lever: closed, the gate drops, the channel stills and the deep culvert drains; opened, it floods again.",
               [placed(GREM, 4), placed(SAB, 2, 'heavy')], [], {}),
    'north_drain': ("North drain", 'corridor', 'M', 0, "Under the north street; gremlin tools and a cut rope.",
                    [placed(GREM, 3)], [], {}),
    'shaft_north': ("North shaft (the gate)", 'room', 'S', 0,
                    "A ladder up to a grate under the gatehouse, bolted from above; the bones of a gate guard who fell in, his purse still on him.",
                    [], [], {'empty': True}),
    'east_drain': ("East drain", 'corridor', 'M', 0,
                   "Under the temple and the stables; the oldest stone; the cellar's floor grate in its south walk, bolted from below.",
                   [placed(VBAT, 4)], [], {}),
    'shaft_temple': ("Temple shaft", 'room', 'S', 0,
                     "A ladder up to the temple's grate, bolted from above. A flask of Green Liquid (+2 Endurance, once per character).",
                     [], [], {'empty': True}),
    'shaft_market': ("Market shaft", 'room', 'S', 0,
                     "Under the market: a grate bolted from above, a heap of things dropped through it over the years (a chest).",
                     [placed(DIRE, 3, 'light')], [{'kind': 'chest', 'count': 1, 'tier': 2}], {}),
    'felix': ("Felix's tunnel", 'corridor', 'S', 0,
              "A neat tunnel dug by Felix the Tinker (NPC 4958), who lives at its end by his bench and sells nothing; his line is the sluice hint (D-26).",
              [], [], {'empty': True}),
    'valio': ("Valio's bed", 'room', 'S', 0,
              "A bed in a dry niche, Valio the Simple (NPC 4957) in it (Q-D5). His chest beside it: gold and a T2 item; opened before he pays, he gets out of bed (monster 11193, 45).",
              [], [{'kind': 'chest', 'count': 1, 'tier': 2}], {'goal': True}),
    'overflow': ("Overflow cistern", 'room', 'M', 0,
                 "A round cistern and its pool; the stair down to the culverts leaves from its south side.",
                 [placed(DIRE, 4)], [], {}),
    'overflow_stair': ("Overflow stair", 'corridor', 'M', [0, -512],
                       "A ramp of wet stone down from the overflow to the deep cistern.", [], [], {'empty': True}),
    'deep_cistern': ("Deep cistern", 'room', 'M', -512,
                     "The overflow stair's foot: a tall wet cistern; the outfall tunnel and the rat runs leave it east.",
                     [placed(VBAT, 4)], [], {}),
    'outfall': ("Outfall tunnel", 'corridor', 'M', -512,
                "The drain's way out under the town wall to the mill gorge: an iron grate barred on this side; lifting the bar opens it both ways.",
                [], [], {'empty': True}),
    'rat_runs': ("Rat runs", 'room', 'M', -512, "Where the brick has fallen in: burrows, gnawed bones, rat runs.",
                 [placed(WERE, 3), placed(DIRE, 3)], [], {}),
    'culvert': ("Nest culvert", 'corridor', 'M', -512,
                "A low culvert to the nest, flooded to its roof until the sluice is shut (a sinking water mover). No monster stands below its high-water line: its four rats wait on the nest side, above it.",
                [], [], {'empty': True}),
    'nest_ramp': ("Nest ramp", 'corridor', 'S', [-512, -224], "From the culvert up to the nest, above the high water.",
                  [], [], {'empty': True}),
    'rat_nest': ("The rat queen's nest", 'room', 'L', -224,
                 "A heap of rags, bottle caps and buttons in a collapsed vault; Rooka (q-d5.rooka at her death); the shiny things (m16.necklace); her hoard. The culvert's four rats wait at its mouth.",
                 [placed(ROOKA, 1, 'boss', role='boss'), placed(WERE, 4, 'heavy'), placed(DIRE, 4, 'light')],
                 [{'kind': 'chest', 'count': 1, 'tier': 3, 'notes': "the hoard"}], {'goal': True}),
    'bone_slide': ("Bone slide", 'corridor', 'S', [-224, -480], "A slope of filth from the nest down to the midden.",
                   [], [], {'empty': True}),
    'midden': ("Bone midden", 'room', 'M', -480, "Where the rats drag what they kill: bones and a sodden pack (chest).",
               [placed(DIRE, 3, 'light')], [{'kind': 'chest', 'count': 1, 'tier': 2}], {}),
    'cellar': ("Drowned cellar", 'room', 'M', -480,
               "An old house cellar the drain broke into; gremlins store stolen tools here; a ladder up to the east drain's floor grate, bolted from this side (opens once, from below).",
               [placed(GREM, 3), placed(SAB, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 2}], {}),
}

LINKS = [
    ('link:square_cross', 'shaft_square', 'cross', 'open', {}),
    ('link:cross_west', 'cross', 'west_drain', 'door', {}),
    ('link:west_shaft', 'west_drain', 'shaft_west', 'open', {}),
    ('link:west_sluice', 'west_drain', 'sluice', 'open', {}),
    ('link:sluice_north', 'sluice', 'north_drain', 'door', {}),
    ('link:north_cross', 'north_drain', 'cross', 'door', {}),
    ('link:north_shaft', 'north_drain', 'shaft_north', 'open', {}),
    ('link:cross_east', 'cross', 'east_drain', 'door', {}),
    ('link:east_temple', 'east_drain', 'shaft_temple', 'open', {}),
    ('link:east_market', 'east_drain', 'shaft_market', 'door', {}),
    ('link:west_felix', 'west_drain', 'felix', 'open', {}),
    ('link:felix_valio', 'felix', 'valio', 'open', {}),
    ('link:valio_overflow', 'valio', 'overflow', 'door', {}),
    ('link:overflow_stair', 'overflow', 'overflow_stair', 'open', {}),
    ('link:stair_deep', 'overflow_stair', 'deep_cistern', 'open', {}),
    ('link:deep_runs', 'deep_cistern', 'rat_runs', 'open', {}),
    ('link:deep_outfall', 'deep_cistern', 'outfall', 'door', {}),
    ('link:culvert', 'rat_runs', 'culvert', 'open', {'condition': {'map_var': 'sluice_shut'}, 'opened_by': 'poi:sluice',
                                                     'purpose': "Flooded to its roof until the sluice is shut (the water a sinking mover, XD-10's word)."}),
    ('link:culvert_ramp', 'culvert', 'nest_ramp', 'open', {}),
    ('link:ramp_nest', 'nest_ramp', 'rat_nest', 'open', {}),
    ('link:nest_slide', 'rat_nest', 'bone_slide', 'open', {}),
    ('link:slide_midden', 'bone_slide', 'midden', 'open', {}),
    ('link:midden_cellar', 'midden', 'cellar', 'open', {}),
    ('link:cellar_east', 'cellar', 'east_drain', 'ladder', {'condition': {'map_var': 'grate_open'}, 'opened_by': 'poi:grate_bolt',
                                                          'purpose': "A ladder up to a floor grate in the east drain, bolted from below: opened once from the cellar; from above 'The grate is bolted from below.'"}),
]

PITCH = ("Castleview's sewer: a vaulted cross under the square where four drains meet, slow sewage channels down their "
         "middles, five iron ladders up to street grates of which only the square's hatch opens. West, the town's "
         "sluice house, its gate wedged open by gremlins with the mill's stolen gears, floods an old culvert below; "
         "Felix the Tinker, who dug his own tunnel, says as much, and Valio the Simple lives in a bed beside it. Shut "
         "the sluice and the culvert drains, rats and all: beyond it the rat queen's nest, Rooka and her hoard of "
         "shiny things, Nadia's necklace among them. The way back climbs through a bone midden and a drowned cellar "
         "to a floor grate bolted from below; the outfall's barred grate opens on the mill gorge once its bar is lifted.")
PURPOSE = ("Story step M16 (QUESTS.md): Nadia's onyx necklace in the rats' nest (A3's hook m16.necklace). Side quest "
           "Q-D5: Valio wants Rooka the Queen Rat dead (q-d5.rooka at her death; his chest q-d5.valio_chest, opened "
           "early it angers him, q-d5.valio_angry). Class M, party 18-20, monsters 10-20, Rooka 24.")
MOOD = ("Damp and close: mossy cut stone with a green tide line, flags slick under sewage, lamplight falling down the "
        "shafts through round grates, the rats' caves of fallen brick, straw and filth.")


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
        for k in ('empty',):
            if extra.get(k):
                s[k] = True
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
            d['notes'] = f"Through {via}."
        d.update(extra)
        links.append(d)
    return {
        'format': 0, 'level': 'L1' if level == 'L1' else ('L2' if level == 'L2' else 'L3'), 'pitch': PITCH,
        'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:upper', 'spaces': ['room:cross', 'room:west_drain', 'room:sluice', 'room:north_drain'],
             'notes': "Round the sluice house."},
            {'id': 'loop:deep', 'spaces': ['room:cross', 'room:west_drain', 'room:felix', 'room:valio', 'room:overflow',
                                           'room:overflow_stair', 'room:deep_cistern', 'room:rat_runs', 'room:culvert',
                                           'room:nest_ramp', 'room:rat_nest', 'room:bone_slide', 'room:midden', 'room:cellar', 'room:east_drain'],
             'notes': "Down past Valio, through the nest, up through the drowned cellar's floor grate."},
        ],
        'entrances': [
            {'id': 'entrance:d1_hatch', 'space': 'room:shaft_square', 'kind': 'both', 'neighbour': 'exit:d1_hatch',
             'facing': 'n', 'notes': "The arrival at the ladder's foot. 'Exit the Sewer?' (dark/aaze0030) is the game's leave window."},
            {'id': 'entrance:d1_outfall', 'space': 'room:outfall', 'kind': 'both', 'neighbour': 'exit:d1_outfall',
             'notes': "The outfall grate: barred on this side until the bar is lifted (q-d5.outfall_unbarred), then both ways."},
        ],
        'critical_path': ['room:shaft_square', 'room:cross', 'room:west_drain', 'room:sluice', 'room:west_drain',
                          'room:felix', 'room:valio', 'room:overflow', 'room:overflow_stair', 'room:deep_cistern',
                          'room:rat_runs', 'room:culvert', 'room:nest_ramp', 'room:rat_nest'],
        'return_path': ['room:rat_nest', 'room:bone_slide', 'room:midden', 'room:cellar', 'room:east_drain', 'room:cross',
                        'room:shaft_square'],
        'goals': [
            {'id': 'goal:necklace', 'space': 'room:rat_nest', 'kind': 'take',
             'what': "Nadia's onyx necklace among the shiny things (A3's hook m16.necklace, once)."},
            {'id': 'goal:rooka', 'space': 'room:rat_nest', 'kind': 'kill',
             'what': "Rooka the Rat Queen (q-d5.rooka at her death: rooka_slain 113101, 3,000 XP)."},
            {'id': 'goal:valio', 'space': 'room:valio', 'kind': 'use',
             'what': "Valio's topic pays with his chest after rooka_slain (q-d5.valio_chest)."},
        ],
        'keys': [
            {'id': 'key:sluice', 'grants': {'map_var': 'sluice_shut'}, 'found_in': 'room:sluice', 'how': 'lever',
             'notes': "The sluice lever drains the nest culvert; open again it floods it."},
            {'id': 'key:grate', 'grants': {'map_var': 'grate_open'}, 'found_in': 'room:cellar', 'how': 'lever',
             'notes': "The cellar's bolt opens the floor grate into the east drain, once, from below."},
        ],
        'points_of_interest': [
            {'id': 'poi:sluice', 'space': 'room:sluice', 'kind': 'lever',
             'behaviour': "The sluice lever: closed, the jammed gate drops, the channel stills and the culvert's water sinks (6 s); opened, it floods again."},
            {'id': 'poi:grate_bolt', 'space': 'room:cellar', 'kind': 'lever',
             'behaviour': "The bolt under the floor grate: drawn once, the grate slides aside over the ladder."},
            {'id': 'poi:outfall_bar', 'space': 'room:outfall', 'kind': 'lever',
             'behaviour': "The outfall grate's bar: lifted (q-d5.outfall_unbarred) the grate opens both ways to the mill gorge; dropped, it bars again."},
            {'id': 'poi:shaft_ladders', 'spaces': ['room:shaft_west', 'room:shaft_north', 'room:shaft_market', 'room:shaft_temple'],
             'kind': 'sign', 'count': 4,
             'behaviour': "'Sewer Drain' (dark/aaze0030): the grate is bolted from above. You hear the town over your head."},
            {'id': 'poi:liquids', 'spaces': ['room:shaft_west', 'room:shaft_temple'], 'kind': 'fountain', 'count': 2,
             'behaviour': "Red Liquid (+2 Might) and Green Liquid (+2 Endurance), once per character (player bits 11310, 11311); the source's +5 rescaled."},
            {'id': 'poi:bones', 'space': 'room:shaft_north', 'kind': 'sign',
             'behaviour': "A gate guard's bones: his purse once (guard_purse 117002), then 'Nothing here.' (dark/aaze0030)."},
            {'id': 'poi:people', 'spaces': ['room:felix', 'room:valio'], 'kind': 'npc', 'count': 2,
             'behaviour': "Felix the Tinker (4958) at his bench; Valio the Simple (4957) in his bed (topic Rats, Q-D5)."},
            {'id': 'poi:shiny_heap', 'space': 'room:rat_nest', 'kind': 'sign',
             'behaviour': "The rats' heap of shiny things: Nadia's necklace (m16.necklace), once."},
        ],
        'mechanisms': [
            {'kind': 'sluice lever and sinking culvert water (two states)', 'count': 1},
            {'kind': 'floor grate bolted from below', 'count': 1}, {'kind': 'outfall bar (two states)', 'count': 1},
            {'kind': 'bolted shaft ladder', 'count': 4}, {'kind': 'once-per-character liquid', 'count': 2},
        ],
        'totals': {'chests': 5, 'doors': 7, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act3_graphs/dd01.graph.yml; D-26 (mockups/act3_a8_decisions_a.md) wins where they differ: Dire Rats for the Bat Queens, the cellar's way up a floor grate bolted from below, no monster below the culvert's high-water line (the culvert's four rats wait in the nest above it), Felix with the sluice hint, the outfall and the street grates on D1. Floors at 0 (the drains) and -512 (the deep culverts; the nest at -224 above the culvert's high water, the midden and cellar at -480). All 50 monsters placed (exact counts); Valio's monster (11193) placed hidden, shown when he is angered.",
    }


DIAGRAM = """THE TOWN DRAINS (0)
                [SLUICE: lever, jammed gate] =door= [NORTH DRAIN] -- [NORTH SHAFT: bones]
                     |                                   |door
 [WEST SHAFT: Red] -- [WEST DRAIN] =door= [THE DRAIN CROSS] =door= [EAST DRAIN ......#grate#......] -- [TEMPLE SHAFT: Green]
                     |                     |                   |door
              [FELIX'S TUNNEL: bench]   [SQUARE SHAFT: hatch]  [MARKET SHAFT $]
                     |                     ^ D1 (exit)
              [VALIO'S BED $] =door= [OVERFLOW CISTERN]
                                           | overflow stair (0 -> -512)
THE DEEP CULVERTS (-512)                   v
                                    [DEEP CISTERN] =door= [OUTFALL: bar | grate] -> D1 mill gorge (exit once unbarred)
                                           |
                                    [RAT RUNS] -- ~~flooded culvert~~ -- nest ramp up -- [RAT QUEEN'S NEST (-224) $$ Rooka, necklace]
                                                                                               | bone slide down
                                                                 [DROWNED CELLAR (-480) $] -- [BONE MIDDEN $]
                                                                    | ladder up to #grate# (bolted from below)
 $ chest   =door= door   ~~ ~~ water mover sunk by the sluice lever   #grate# floor grate opened from below
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
            'notes': "DD-01 Castleview Sewer: the town drains at 0 and the deep culverts at -512 (the nest at -224, the midden and cellar at -480) in one frame (x east, y north, heights from the arrival floor). Written by output/studio_cal/dd01/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
