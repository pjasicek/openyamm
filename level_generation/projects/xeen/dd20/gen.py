#!/usr/bin/env python3
"""Writes DD-20 Lakeside Coven and Sewer's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd20/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act4_graphs/dd20.graph.yml with decider D-42,
mockups/act4_a8_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
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
BR = R / 'devdocs/xeen/briefs/dd20'


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
WITCH, COVEN_WITCH, HEAD_WITCH, STALKER, MATRIARCH = 11170, 11171, 11173, 11401, 11402
LEVEL = {WITCH: 32, COVEN_WITCH: 40, HEAD_WITCH: 45, STALKER: 25, MATRIARCH: 35}

# D4 (installed, A6): its named arrivals for this map's two ways out (assets_dev/worlds/xeen/maps/xeen_d4.studio.yml).
D4_GUILD = 'entrance:dd20_guild'      # (-1024, -13312, 1120) facing 1024 (west, beside the Guild's cellar hatch)
D4_SHAFT = 'entrance:dd20_shaft'      # (3072, -9728, 1120) facing 512 (north, by the jetty's grate)

QBITS = {'arrived_once': 117400,
         # A3's Q-D22 and Q-D20 bits read here (the hooks set them)
         'riddle_answered': 113442, 'camilla_freed': 113443, 'aretha_freed': 113444, 'isabella_freed': 113445,
         'rhett_freed': 113446, 'head_witch_slain': 113447, 'pass_found': 113448, 'joined': 113449}
# dragon_found (113402) dropped 2026-11-22 (A3 35th): the Golden Dragon is a ground item (D-90), A3 deletes the bit.

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-20 Lakeside Coven and Sewer (the source's dark Lakeside town maze0033: the "
    "coven, its prisoners and cauldrons; and Lakeside Sewer maze0034: the stalkers, the statuette, two dead men's "
    "journals) as one BLV under D4's Lakeside. Side quest Q-D22 The Coven (A3's hooks q-d22.initiation, head_witch, "
    "witch_chest, camilla, aretha, isabella, rhett, cauldron_personality, cauldron_endurance, cauldron_speed; the "
    "Warlock promotion) and Q-D20's Golden Dragon (q-d20.dragon). Size M (MAPS.md section 0, D-42): 20-45 sectors, "
    "30-90 M units squared, 45 monsters at levels 25-45, the Head Witch 45, party 35-39, treasure 4 (hoard 5), music "
    "28. Graph devdocs/xeen/mockups/act4_graphs/dd20.graph.yml with decider D-42 (mockups/act4_a8_decisions.md, which "
    "wins): the Guild's back cellar door (entrance:d4_guild), the trapdoor (entrance:d4_trapdoor, one way) and the "
    "jetty shaft (entrance:d4_shaft); the Head Witch 11173 with her own skin, her group of three; the prisoners "
    "11906-11909 named peaceful rows, hidden by their freed bits; the three brewery cauldrons +2 once per character "
    "(A3's player bits 11345-11347); the drain cross's ambush of five shown on the first step (D-18); Joseph left out. "
    "Rows (A2): coven 11170 (Witch 11170 32 x13, Coven Witch 11171 40 x4; peaceful to members, joined 113449, until "
    "the Head Witch dies, 113447), Head Witch 11173; sewer stalkers 11400 (Sewer Stalker 11401 25 x24, Stalker "
    "Matriarch 11402 35 x3). Kill XP 53,672 for the party, 13.42k per member. Rest encounters 10 %: sewer stalkers "
    "at Dif 5 only (D-42, D-46). Map qbits 117400-117439 (provisional); map_stats 9173.")


# D-89 identity (lane A8 s28): what the party must see
IDENTITY = {'shape': 'sewer', 'family': '7d06',
            'seen': ["the coven hall in 7d06's dressed stone: the arcade, the five-pointed star in the floor, the "
                     "initiation cauldron, shelves of jars",
                     "the brewery's three cauldrons with their talking skulls, and the cages in the wet rock below",
                     "the sewer in 7d17's wet rock over dark brick, plank walks by the drains, the lake outfall"]}


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd20', 'name': 'Lakeside Coven and Sewer', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-20', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [40, 18], 'climbs': 'n'},
        'map_stats': {
            'id': 9173, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 3,
            'perception_difficulty': 3, 'refill_days': 672, 'music': 28, 'environment': 'stoneroom',
            'lock_difficulty': 6,
            'slots': [{'monster': 'Xeen Sewer Stalker', 'tier': 5, 'per_marker': [2, 3], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d4_guild', 'to': 'xeen_d4.odm', 'kind': 'door', 'arrival': D4_GUILD,
             'arrival_hint': "On D4 (Lakeside), beside the Guild's west-wall cellar hatch, facing west (A6's entrance:dd20_guild, (-1024, -13312, 1120) facing 1024, D-42 (4)).",
             'notes': "D4 installed by A6; its door:dd20_guild (the Guild's back cellar hatch, open once riddle_answered 113442) leads in to entrance:d4_guild at the foot of the Guild's back stair. The way out is the exit preset at the stair's top landing."},
            {'id': 'exit:d4_shaft', 'to': 'xeen_d4.odm', 'kind': 'door', 'arrival': D4_SHAFT,
             'arrival_hint': "On D4, by the grate at the jetty's foot, facing north (A6's entrance:dd20_shaft, (3072, -9728, 1120) facing 512).",
             'notes': "D4's door:dd20_sewer ('Climb down to the sewer?', aaze0033:3; open from day one, D-36 (4)) leads in to entrance:d4_shaft at the ladder's foot. The way out is the exit preset up the ladder."},
        ],
        'qbits': dict(QBITS),
        'items': {'golden_dragon': 12350},
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    'guild_landing': ("Guild's back landing", 'room', 'S', geo.GUILD,
                      "The top of the Guild's back stair under the Guild's back room: the cellar door up to D4.",
                      [], [], {'empty': True}),
    'guild_stair': ("Guild's back stair", 'corridor', 'M', [geo.GUILD, 0],
                    "D4's t09 ashlar, down northward into the coven hall.", [], [], {'empty': True}),
    'coven_hall': ("Coven hall", 'room', 'L', 0,
                   "The initiation cauldron two steps from the stair's foot ('Drink?', q-d22.initiation); the Moon seal's double doors north.",
                   [placed(WITCH, 2)], [], {'goal': True}),
    'witches_walk': ("Witches' walk", 'corridor', 'M', 0, "Behind the double doors, towards the Head Witch.",
                     [placed(WITCH, 2), placed(COVEN_WITCH, 1)], [], {}),
    'antechamber': ("Antechamber", 'room', 'S', 0, "Her door-wardens.", [placed(COVEN_WITCH, 2)], [], {}),
    'head_witch': ("Head Witch's room", 'room', 'M', 0,
                   "The coven's north-west corner: the Head Witch (q-d22.head_witch at her death), her chest (q-d22.witch_chest: the Necropolis pass), her mirror.",
                   [placed(HEAD_WITCH, 1, 'boss', role='boss'), placed(COVEN_WITCH, 1), placed(WITCH, 1)],
                   [{'kind': 'chest', 'count': 1, 'tier': 5, 'notes': "Her chest (the hoard)."}], {'goal': True}),
    'brewery': ("Brewery", 'room', 'M', 0,
                "Three cauldrons, +2 Personality, Endurance, Speed once per character (A3's player bits 11345-11347); talking skulls with the recipes.",
                [placed(WITCH, 3)], [], {}),
    'dormitory': ("Witches' dormitory", 'room', 'M', 0, "Beds ('Bed': one find), the senior witch's chest.",
                  [placed(WITCH, 3)], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
    'store': ("Coven store", 'room', 'S', 0, "A storeroom; the floor hatch to the cistern, bolted from this side.",
              [], [], {'empty': True, 'store': True}),
    'gaol': ("Gaoler's room", 'room', 'S', 0, "The gaolers' table; the prisoners' confiscated things in a chest.",
             [placed(WITCH, 2)], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
    'gaol_stair': ("Cell stair", 'corridor', 'S', [0, geo.CELLS], "Down from the gaol to the cells.", [], [], {'empty': True}),
    'cells': ("The cells", 'corridor', 'M', geo.CELLS,
              "Four cages: Camilla, Aretha, Isabella asleep, Rhett at the sewer end (q-d22.camilla .. rhett).",
              [], [], {'empty': True, 'goal': True}),
    'drain_stair': ("Drain stair", 'corridor', 'S', [geo.CELLS, geo.SEWER], "Where the witches tip their slops: down to the sewer.",
                    [], [], {'empty': True}),
    'slop_pit': ("Slop pit", 'room', 'S', geo.SEWER, "The drain stair's foot.", [placed(STALKER, 2)], [], {}),
    'cross': ("Drain cross", 'room', 'M', geo.SEWER,
              "Five drains meet; three stalkers in sight, five more climb out of the side drains on the first step (D-18).",
              [placed(STALKER, 3), placed(STALKER, 4, notes='hidden, shown on the first step'),
               placed(MATRIARCH, 1, 'heavy', notes='hidden, shown on the first step')], [], {}),
    'main_drain': ("Main drain", 'corridor', 'M', geo.SEWER, "East under the square, a street grate overhead.",
                   [placed(STALKER, 3)], [], {}),
    'sump': ("Trapdoor sump", 'room', 'S', geo.SEWER,
             "The arrival of a wrong answer: the trapdoor shut fast above; bones of earlier wrong answers.",
             [], [], {'empty': True}),
    'cistern': ("Cistern", 'room', 'M', geo.SEWER, "Under the coven store: pillars, still water, the ladder to the hatch.",
                [placed(STALKER, 2)], [], {}),
    'pump_room': ("Old pump room", 'room', 'S', geo.SEWER, "The town's broken pump, a chest.", [],
                  [{'kind': 'chest', 'count': 1, 'tier': 4}], {'empty': True}),
    'hideout': ("Dead man's hideout", 'room', 'S', geo.SEWER, "Bones, his journal (aaze0034:8) and his pack.", [], [], {'empty': True}),
    'warren': ("Stalker warren", 'room', 'M', geo.SEWER, "The stalkers' nest; a chest in their midden.",
               [placed(STALKER, 4), placed(MATRIARCH, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
    'east_drain': ("East drain", 'corridor', 'M', geo.SEWER, "From the cross east to the jetty shaft.",
                   [placed(STALKER, 2)], [], {}),
    'outfall': ("Lake outfall", 'room', 'L', geo.SEWER, "The tidal pool and the barred mouth to the lake.",
                [placed(STALKER, 4), placed(MATRIARCH, 1, 'heavy')], [], {}),
    'niche': ("The Dragon's niche", 'room', 'S', geo.SEWER,
              "The dead man's bones two steps short of the alcove (aaze0034:7); the Golden Dragon (q-d20.dragon).",
              [], [], {'empty': True, 'goal': True}),
    'jetty_shaft': ("Jetty shaft", 'room', 'S', geo.SEWER, "The ladder up to D4's grate by the jetty.", [], [], {'empty': True}),
}

LINKS = [
    ('link:stair_hall', 'guild_landing', 'coven_hall', 'stairs', {'via': "the Guild's back stair"}),
    ('link:hall_walk', 'coven_hall', 'witches_walk', 'door', {'purpose': "The Moon seal's double doors (two leaves)."}),
    ('link:walk_ante', 'witches_walk', 'antechamber', 'door', {}),
    ('link:ante_head', 'antechamber', 'head_witch', 'door', {}),
    ('link:walk_brewery', 'witches_walk', 'brewery', 'door', {}),
    ('link:brewery_head', 'brewery', 'head_witch', 'door', {'purpose': "Her private door."}),
    ('link:hall_dorm', 'coven_hall', 'dormitory', 'door', {}),
    ('link:dorm_store', 'dormitory', 'store', 'door', {}),
    ('link:hall_gaol', 'coven_hall', 'gaol', 'door', {}),
    ('link:gaol_cells', 'gaol', 'cells', 'stairs', {'via': 'the cell stair'}),
    ('link:cells_slop', 'cells', 'slop_pit', 'stairs', {'via': 'the drain stair'}),
    ('link:store_cistern', 'store', 'cistern', 'door', {'opened_by': 'poi:hatch_bolt',
                                                        'purpose': "The store's floor hatch, bolted from above: the ladder down to the cistern."}),
    ('link:cistern_sump', 'cistern', 'sump', 'open', {}),
    ('link:sump_main', 'sump', 'main_drain', 'open', {}),
    ('link:main_pump', 'main_drain', 'pump_room', 'door', {}),
    ('link:main_cross', 'main_drain', 'cross', 'open', {}),
    ('link:cross_slop', 'cross', 'slop_pit', 'open', {}),
    ('link:cross_hideout', 'cross', 'hideout', 'open', {}),
    ('link:cross_warren', 'cross', 'warren', 'open', {}),
    ('link:cross_east', 'cross', 'east_drain', 'open', {}),
    ('link:warren_outfall', 'warren', 'outfall', 'open', {}),
    ('link:outfall_niche', 'outfall', 'niche', 'open', {'purpose': "The ledge."}),
    ('link:outfall_shaft', 'outfall', 'jetty_shaft', 'open', {}),
    ('link:shaft_east', 'jetty_shaft', 'east_drain', 'open', {}),
]
PATH_ROOMS = {'link:stair_hall': 'guild_stair', 'link:gaol_cells': 'gaol_stair', 'link:cells_slop': 'drain_stair'}

PITCH = ("Under the Lakeside Guild the coven keeps house: the Guild's back stair comes down into its hall, where the "
         "initiation cauldron stands two steps from the foot ('Drink?'). The Moon seal's double doors lead to the "
         "witches' walk, the brewery's three cauldrons and the Head Witch in the north-west corner, her chest and her "
         "mirror. Half a storey down, four prisoners in cages; below them the tide-wet sewer runs east under the "
         "square to the lake outfall, where the stalkers nest and the Golden Dragon sits in a niche two steps past a "
         "dead man's bones. A wrong answer at the Guild's door drops the party into the sump under the square instead.")
PURPOSE = ("Side quest Q-D22 The Coven (QUESTS.md): free the four prisoners (q-d22.camilla, aretha, isabella, rhett), "
           "kill the Head Witch (q-d22.head_witch) and take her chest's Necropolis pass (q-d22.witch_chest); or join at "
           "the initiation cauldron (q-d22.initiation: Great Druid to Warlock). Q-D20: the Golden Dragon in the sewer "
           "niche (q-d20.dragon). Class M, party 35-39, monsters 25-45, the Head Witch 45.")
MOOD = ("A witches' house under a guild: dressed temple stone, dark flags, cauldron smoke and candles; half a storey "
        "down the wet rock of the cells, and below them the dripping, tide-wet sewer with its plank walks and pale lake "
        "light through the bars.")


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
        'format': 0, 'level': level if level in ('L1', 'L2') else 'L3', 'pitch': PITCH,
        'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:halves', 'spaces': ['room:coven_hall', 'room:gaol', 'room:cells', 'room:slop_pit', 'room:cross',
                                             'room:main_drain', 'room:sump', 'room:cistern', 'room:store', 'room:dormitory'],
             'notes': "Coven and sewer by the cells' drain stair and by the store's hatch, once its bolt is drawn from above."},
            {'id': 'loop:witches', 'spaces': ['room:witches_walk', 'room:antechamber', 'room:head_witch', 'room:brewery'],
             'notes': "To the Head Witch through her wardens or through the brewery and her private door."},
            {'id': 'loop:outfall', 'spaces': ['room:cross', 'room:warren', 'room:outfall', 'room:jetty_shaft', 'room:east_drain'],
             'notes': "The cross to the lake by the warren or by the east drain past the jetty shaft."},
        ],
        'entrances': [
            {'id': 'entrance:d4_guild', 'space': 'room:coven_hall', 'kind': 'both', 'neighbour': 'exit:d4_guild',
             'facing': 'n', 'how': "At the foot of the Guild's back stair (D4's cellar hatch, after the right answer); the way out up the stair to its landing's door."},
            {'id': 'entrance:d4_trapdoor', 'space': 'room:sump', 'kind': 'arrival', 'facing': 'e',
             'how': "A wrong answer at the Guild's door (D4's q-d22.guild_wrong): the trapdoor drops the party into the sump; one way, the trapdoor stays shut above."},
            {'id': 'entrance:d4_shaft', 'space': 'room:jetty_shaft', 'kind': 'both', 'neighbour': 'exit:d4_shaft',
             'facing': 'w', 'how': "The ladder's foot under D4's grate by the jetty (door:dd20_sewer); the way out up the ladder."},
        ],
        'critical_path': ['room:coven_hall', 'room:witches_walk', 'room:antechamber', 'room:head_witch', 'room:brewery',
                          'room:witches_walk', 'room:coven_hall', 'room:gaol', 'room:gaol_stair', 'room:cells',
                          'room:drain_stair', 'room:slop_pit', 'room:cross', 'room:warren', 'room:outfall', 'room:niche',
                          'room:outfall', 'room:jetty_shaft'],
        'return_path': ['room:jetty_shaft'],
        'goals': [
            {'id': 'goal:head_witch', 'space': 'room:head_witch', 'kind': 'kill',
             'what': "The Head Witch (q-d22.head_witch at her death: head_witch_slain 113447)."},
            {'id': 'goal:pass', 'space': 'room:head_witch', 'kind': 'take',
             'what': "Her chest: the Necropolis pass (q-d22.witch_chest, needs joined or her death)."},
            {'id': 'goal:prisoners', 'space': 'room:cells', 'kind': 'use',
             'what': "The four cages (q-d22.camilla, aretha, isabella, rhett)."},
            {'id': 'goal:dragon', 'space': 'room:niche', 'kind': 'take', 'what': "The Golden Dragon (q-d20.dragon)."},
        ],
        'keys': [
            {'id': 'key:hatch', 'grants': {'map_var': 'hatch_open'}, 'found_in': 'room:store', 'how': 'lever',
             'notes': "The store's hatch bolt, drawn from above: the cistern's ladder up."},
        ],
        'points_of_interest': [
            {'id': 'poi:initiation', 'space': 'room:coven_hall', 'kind': 'fountain',
             'behaviour': "The initiation cauldron: 'Drink?' (q-d22.initiation; joined, the Warlock promotion)."},
            {'id': 'poi:mirror', 'space': 'room:head_witch', 'kind': 'sign',
             'behaviour': "'A bodiless voice murmurs: \"You are the most beautiful one of all.\"' (aaze0033:9)."},
            {'id': 'poi:cauldrons', 'space': 'room:brewery', 'kind': 'fountain', 'count': 3,
             'behaviour': "+2 Personality, Endurance, Speed, once per character (A3's hooks)."},
            {'id': 'poi:skulls', 'space': 'room:brewery', 'kind': 'sign', 'count': 3,
             'behaviour': "The talking skulls' recipes (aaze0033:12-14)."},
            {'id': 'poi:cages', 'space': 'room:cells', 'kind': 'npc', 'count': 4,
             'behaviour': "'Cage': the prisoner's line, the front opens, the prisoner gone (A3's hooks)."},
            {'id': 'poi:hatch_bolt', 'space': 'room:store', 'kind': 'lever',
             'behaviour': "The hatch's bolt: the floor hatch opens onto the cistern's ladder."},
            {'id': 'poi:ambush', 'space': 'room:cross', 'kind': 'trap',
             'behaviour': "Five stalkers climb out of the side drains on the first step (D-18)."},
            {'id': 'poi:journals', 'spaces': ['room:hideout', 'room:niche'], 'kind': 'sign', 'count': 2,
             'behaviour': "'Bones': the two dead men's journal pages (aaze0034:7, 8)."},
            {'id': 'poi:dragon', 'space': 'room:niche', 'kind': 'altar',
             'behaviour': "'Alcove': the Golden Dragon (q-d20.dragon); then 'The niche is empty.'"},
        ],
        'mechanisms': [
            {'kind': 'initiation cauldron (promotion)', 'count': 1}, {'kind': 'once-per-character cauldron', 'count': 3},
            {'kind': 'cage front opened by its hook', 'count': 4}, {'kind': 'floor hatch with a bolt and a ladder', 'count': 1},
            {'kind': 'hidden group shown on a step', 'count': 1}, {'kind': 'factions turned by quest bits', 'count': 1},
        ],
        'totals': {'chests': 5, 'doors': 9, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act4_graphs/dd20.graph.yml; D-42 (mockups/act4_a8_decisions.md) wins where they differ: 45 monsters; the Head Witch 11173 at 45 with her own skin; the prisoners 11906-11909 named peaceful rows; the Guild by the back cellar hatch; the three cauldrons +2 once per character; the ambush of five; Joseph left out. Levels at 0 (the coven), -256 (the cells) and -512 (the sewer); the cistern lies under the coven store (its hatch). All 45 monsters placed.",
    }


DIAGRAM = """THE COVEN (0)
  [HEAD WITCH'S ROOM $$ boss, mirror] =her door= [BREWERY: 3 cauldrons, skulls]
        |door                                        |door
  [ANTECHAMBER] =door= [WITCHES' WALK] ==============+
                              || Moon seal (two leaves)
  [COVEN HALL: initiation cauldron] =door= [GAOL $] -> cell stair (0 -> -256)
        ^ Guild's back stair (640 -> 0)  =door= [DORMITORY $] =door= [STORE: hatch bolt]
  [GUILD LANDING: exit to D4]                                           | hatch (ladder)
THE CELLS (-256)
  [CELLS: cages Camilla, Aretha, Isabella, Rhett] -> drain stair (-256 -> -512)
THE SEWER (-512)
  [CISTERN] -- [SUMP: trapdoor arrival] -- [MAIN DRAIN] =door [PUMP ROOM $] -- [CROSS: ambush] -- [SLOP PIT]
                                                                               |        |        \\
                                                                        [HIDEOUT] [EAST DRAIN] [WARREN $]
                                                                                       |           |
                                                                              [JETTY SHAFT: exit] [OUTFALL] -- [NICHE: Dragon]
 $ chest   =door= door
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', dict(project(level), identity=IDENTITY) if level == 'L4' else project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:coven', 'ambient': 12},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-20 Lakeside Coven and Sewer: the coven at 0, the cells at -256, the sewer at -512, in one frame (x east, y north as D4, origin under the Guild's centre). Written by output/studio_cal/dd20/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
