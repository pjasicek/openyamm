#!/usr/bin/env python3
"""Writes XD-10 Cave of Illusion's project folders: `gen.py L1` writes devdocs/xeen/briefs/xd10/L1.

L1: plan.yml (the graph devdocs/xeen/mockups/act2_graphs/xd10.graph.yml and decider D-4), project.yml, diagram.txt.
L2-L4 (positions, rooms.yml, objects/wiring) are the next steps (L4/NOTES.md, "Next steps").
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/xd10'


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


FF, G, WG = 11600, 11601, 11591

NOTES_PROJECT = (
    "Xeen design brief for a new map (no original): XD-10 Cave of Illusion, story step M12 (QUESTS.md; "
    "source/quests/m12.yml): a talking skull at the cave's bottom sells the Enchanted Key to the Tower of High Magic "
    "for gems. Size M (MAPS.md section 0): 20-45 sectors, 30-90 M units squared, 50 monsters at levels 18-28, party "
    "17-19, treasure 3. Graph devdocs/xeen/mockups/act2_graphs/xd10.graph.yml with decider D-4's decisions "
    "(mockups/act2_dungeon_decisions.md, which wins). Rows (A2): slot 1 Magic constructs (Xeen Construct: tier a "
    "Flying Feet 11600, tier b Guardian 11601), slot 2 Elemental golems (Xeen Elemental Golem: tier b Water Golem "
    "11591); every monster is placed (30 Flying Feet, 12 Guardians, 8 Water Golems, 33,424 kill XP, 8.36k per "
    "member). Items: Enchanted Key 12306 (A3's hook m12.skull), Might Boost 240 (the fixed potion behind the "
    "mirage, given by event at power 10, D-22.2), gems (Xeen.GemItems). Map qbits 110640-110679 (plug_pulled 110640); player bits 11236-11240 (the "
    "skulls). Map_stats 9126 (source/maps.yml: music 2, treasure 3). Both mouths lead to X5 (installed by A6).")


# D-89 identity (lane A8 s28): what the party must see
IDENTITY = {'shape': 'cave', 'family': 'd33',
            'seen': ["ice and snow at the two mouths, then broken grey caves with uneven floors and icicles",
                     "cave walls that are not there: the mirages wear the rock of the cave round them",
                     "the drained reservoir bed under its tall cavern, weed and silt on the bed, the plug and the wreck"]}


def project(level):
    return {
        'format': 0, 'id': 'xeen_xd10', 'name': 'Cave of Illusion', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'XD-10', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [27, 20], 'climbs': 'n'},
        'map_stats': {
            'id': 9126, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 3, 'trap_dice': 3,
            'perception_difficulty': 5, 'refill_days': 672, 'music': 2, 'environment': 'cave',
            'lock_difficulty': 5,
            'slots': [{'monster': 'Xeen Construct', 'tier': 0, 'per_marker': [2, 3], 'weight': 75},
                      {'monster': 'Xeen Elemental Golem', 'tier': 1, 'per_marker': [2, 3], 'weight': 25}],
        },
        'neighbours': [
            {'id': 'exit:x5_north', 'to': 'xeen_x5.odm', 'kind': 'door', 'arrival': [16640, 9987, 1408],
             'arrival_hint': "On X5 (Winterkill Tundra), before the cave's north mouth by the frozen lake in the Ogre Hills, facing south.",
             'direction': 270,
             'notes': "X5 installed by A6; arrival given by the orchestrator (16640, 9987, 1408), facing south (1536). The north mouth asks 'Leave the Cave of Illusion?' (aaze0042:49). The arrival of the whole map (X5's door into XD-10) is this map's start in the north mouth."},
            {'id': 'exit:x5_south', 'to': 'xeen_x5.odm', 'kind': 'door', 'arrival': [6915, -9472, 1216],
             'arrival_hint': "On X5 (Winterkill Tundra), before the cave's south mouth on the Troll Forest side, facing west.",
             'direction': 180,
             'notes': "X5 installed by A6; arrival given by the orchestrator (6915, -9472, 1216), facing west (1024). The south mouth asks 'Leave the Cave of Illusion?' (aaze0042:49). X5's south-mouth door enters by explicit coordinates (D-4 item 5) until A1 adds more than one arrival per dungeon."},
        ],
        'qbits': {'plug_pulled': 110640, 'arrived_once': 110641, 'cache_potion': 110642, 'key_bought': 111240},
        'items': {'enchanted_key': 12306, 'might_boost': 240},
        'notes': NOTES_PROJECT,
    }


# id: (name, kind, size, floor, purpose, population, treasure, extra)
def placed(actor, n, level, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [level, level], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


SP = {
    # upper caves, floor 0
    'north_mouth': ("North mouth", 'room', 'S', 0,
                    "The arrival from X5: ice at the lip, snow blown in; the cave's breath is warm and wet. A shimmering wall on the west is a mirage into the cache.",
                    [placed(FF, 2, 18, 'light', rank='a')], [], {}),
    'icicle_hall': ("Icicle hall", 'room', 'M', 0, "Hanging ice; a side passage west ends in a safe.",
                    [placed(FF, 4, 18, rank='a')], [], {}),
    'false_passage': ("Phantom safe", 'room', 'M', 0,
                      "A safe at the end that is not there: 'Your hand passes through the safe as though it were not there.' (aaze0042:72). The shimmering wall beside it is a mirage into the cache.",
                      [placed(FF, 2, 18, 'light', rank='a')], [], {}),
    'mirage_cache': ("Behind the mirage", 'room', 'S', 0,
                     "The real treasure behind the phantom safe's wall: a chest with a Potion of Might (Might Boost 240) for the plug.",
                     [], [{'kind': 'chest', 'count': 1, 'tier': 3, 'item': 'might_boost'}], {'secret': True}),
    'mirage_hall': ("Hall of Mirages", 'room', 'L', 0,
                    "Walls that shimmer like heat; the passage down to the ledge over the reservoir.",
                    [placed(FF, 3, 18, rank='a'), placed(G, 2, 24, rank='b')], [], {}),
    'frost_cavern': ("Frost cavern", 'room', 'M', 0, "Between the hall and the south mouth; the sluice door east, the skull alcoves west.",
                     [placed(FF, 2, 18, rank='a'), placed(G, 2, 24, rank='b')], [], {}),
    'south_mouth': ("South mouth", 'room', 'S', 0, "Out into the Troll Forest side of X5.",
                    [placed(FF, 2, 18, 'light', rank='a')], [], {}),
    'skulls_1': ("Skull alcoves", 'room', 'S', 0,
                 "Two talking skulls on rock shelves: +2 Luck or +2 Personality for 3 gems, once per character (player bits 11236, 11237; hooks m12.skull_upper, _sold, _poor).",
                 [], [], {'empty': True}),
    'sluice': ("Sluice", 'room', 'M', 0,
               "A brick chamber over the reservoir: a great bronze plug on a chain in its pool; pull it (Might 30, potions counting): the water drains. A railed window looks down on the reservoir.",
               [placed(G, 3, 24, 'heavy', rank='b')], [], {}),
    # drowned galleries, floor -640
    'ledge': ("Ledge over the water", 'corridor', 'M', -640,
              "Railed overlook: the flooded reservoir below; the sluice gates of the drowned gallery and of the steps down open with the plug. A notice points to the gems of the echo cave.",
              [], [], {'empty': True}),
    'drowned': ("Drowned gallery", 'room', 'L', -640,
                "Behind its sluice gate until the plug is pulled; then a wet gallery, water golems left in its pools.",
                [placed(WG, 3, 28, 'heavy', rank='b')], [], {}),
    'mirror_maze': ("Mirror maze", 'room', 'M', -640, "Ice walls round rock islands; one wall is a mirage into the deep skull alcoves.",
                    [placed(FF, 4, 18, rank='a'), placed(G, 1, 24, rank='b')], [], {}),
    'guard_post': ("Guardian post", 'room', 'M', -640, "Guardians round a chest.",
                   [placed(G, 4, 24, 'heavy', rank='b')], [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'echo_cave': ("Echo cave", 'room', 'S', -640,
                  "The cave answers in the party's own voices; a cache of 15 gems for the skulls (D-1.6: before the great skull).",
                  [placed(FF, 2, 18, 'light', rank='a')], [{'kind': 'chest', 'count': 1, 'tier': 3, 'notes': "15 fixed gems"}], {}),
    'skulls_2': ("Deep skull alcoves", 'room', 'S', -640,
                 "Behind the maze's mirage: +3 Intellect or +3 Speed for 5 gems, once per character (player bits 11238, 11239; hooks m12.skull_deep, _sold, _poor).",
                 [], [], {'empty': True, 'secret': True}),
    # reservoir bed, floor -1280
    'reservoir': ("Reservoir bed", 'room', 'L', -1280,
                  "Under the water until the plug is pulled (one water mover sinking 640 in about 6 s); then the drained floor: weed, shells, stranded water golems (placed hidden, shown when the party first walks onto the bed).",
                  [placed(WG, 2, 28, rank='b', hidden_until={'qbit': 'plug_pulled'}),
                   placed(FF, 4, 18, rank='a', hidden_until={'qbit': 'plug_pulled'})], [], {}),
    'sump': ("Sump", 'room', 'M', -1280, "Where the water went: a roaring hole and the last water golems.",
             [placed(WG, 2, 28, rank='b'), placed(FF, 1, 18, rank='a')], [], {}),
    'wreck': ("Sunken boat", 'room', 'S', -1280, "A boat on the drained floor, its strongbox intact.",
              [placed(FF, 2, 18, 'light', rank='a')], [{'kind': 'chest', 'count': 1, 'tier': 3}], {}),
    'grotto': ("Grotto of the great skull", 'room', 'M', -1280,
               "The great skull: the Enchanted Key for 10 gems (hook m12.skull); after it, +5 Might, Endurance or Accuracy for 10 gems, once per character (bit 11240; hooks m12.skull_grotto, _sold, _poor). A mirage east into the phantom vault.",
               [], [], {'empty': True, 'goal': True}),
    'phantom_vault': ("Phantom vault", 'room', 'S', -1280, "Behind a mirage in the grotto: the cave's hoard.",
                      [placed(WG, 1, 28, 'heavy', rank='b'), placed(FF, 2, 18, rank='a')],
                      [{'kind': 'chest', 'count': 1, 'tier': [3, 5], 'notes': "the hoard"}], {'secret': True}),
    # connectors
    'ice_stair': ("Ice stair", 'corridor', 'M', [0, -640], "The winding ramp from the Hall of Mirages down to the ledge.", [], [], {'empty': True}),
    'steps': ("Reservoir steps", 'corridor', 'M', [-640, -1280], "Steps from the ledge down to the reservoir bed, behind a sluice gate.", [], [], {'empty': True}),
    'wreck_stair': ("Gallery stair", 'corridor', 'M', [-640, -1280], "Steps from the drowned gallery down to the wreck, behind a sluice gate.", [], [], {'empty': True}),
}

LINKS = [
    ('link:n_icicle', 'north_mouth', 'icicle_hall', 'open', {}),
    ('link:icicle_mirage', 'icicle_hall', 'mirage_hall', 'open', {}),
    ('link:mirage_frost', 'mirage_hall', 'frost_cavern', 'open', {}),
    ('link:frost_s', 'frost_cavern', 'south_mouth', 'open', {}),
    ('link:icicle_false', 'icicle_hall', 'false_passage', 'open', {}),
    ('link:false_cache', 'false_passage', 'mirage_cache', 'secret_door', {'purpose': "A mirage: a click or walking into it: 'The mirage dissipates with your touch.' (aaze0042:24)."}),
    ('link:cache_n', 'mirage_cache', 'north_mouth', 'secret_door', {'purpose': "A mirage (as above)."}),
    ('link:frost_skulls', 'frost_cavern', 'skulls_1', 'open', {}),
    ('link:frost_sluice', 'frost_cavern', 'sluice', 'door', {}),
    ('link:mirage_ledge', 'mirage_hall', 'ice_stair', 'open', {}),
    ('link:stair_ledge', 'ice_stair', 'ledge', 'open', {}),
    ('link:ledge_maze', 'ledge', 'mirror_maze', 'open', {}),
    ('link:maze_post', 'mirror_maze', 'guard_post', 'open', {}),
    ('link:post_echo', 'guard_post', 'echo_cave', 'open', {}),
    ('link:maze_skulls', 'mirror_maze', 'skulls_2', 'secret_door', {'purpose': "A mirage (as above)."}),
    ('link:ledge_drowned', 'ledge', 'drowned', 'door', {'condition': {'qbit': 'plug_pulled'}, 'opened_by': 'poi:plug',
                                                        'purpose': "A stone sluice gate, opened by the plug."}),
    ('link:ledge_steps', 'ledge', 'steps', 'door', {'condition': {'qbit': 'plug_pulled'}, 'opened_by': 'poi:plug',
                                                    'purpose': "A stone sluice gate, opened by the plug."}),
    ('link:steps_reservoir', 'steps', 'reservoir', 'open', {'condition': {'qbit': 'plug_pulled'},
                                                            'purpose': "Under the water until the plug is pulled."}),
    ('link:drowned_wstair', 'drowned', 'wreck_stair', 'door', {'condition': {'qbit': 'plug_pulled'}, 'opened_by': 'poi:plug',
                                                               'purpose': "A stone sluice gate, opened by the plug."}),
    ('link:wstair_wreck', 'wreck_stair', 'wreck', 'open', {}),
    ('link:wreck_sump', 'wreck', 'sump', 'open', {}),
    ('link:wreck_reservoir', 'wreck', 'reservoir', 'open', {'condition': {'qbit': 'plug_pulled'}}),
    ('link:reservoir_grotto', 'reservoir', 'grotto', 'open', {'condition': {'qbit': 'plug_pulled'}}),
    ('link:grotto_vault', 'grotto', 'phantom_vault', 'secret_door', {'purpose': "A mirage (as above)."}),
]

PITCH = ("A cold cave under the Winterkill Tundra that breathes warm and wet: ice at its two mouths, grey wet rock "
         "below, and walls that are not there. A great bronze plug in a brick sluice holds back the reservoir that "
         "drowns the lower caves; pulled (by a strong arm, or one helped by the Potion of Might behind the phantom "
         "safe's mirage) the water sinks away in a few seconds, seen from the railed ledge and the sluice's window, "
         "and the stone sluice gates open on the drowned gallery and the steps to the reservoir bed. At the bottom a "
         "great talking skull sells the Enchanted Key to the Tower of High Magic for ten gems; smaller skulls sell "
         "stat rises; the echo cave keeps fifteen gems on the way down.")
PURPOSE = ("Story step M12 (QUESTS.md): the Enchanted Key from the great skull (A3's hook m12.skull: 10 gems, the key "
           "12306, qbit 111240, 1,500 XP). Once-per-character stat rises for gems (D-4 item 4). Class M, party 17-19, "
           "monsters 18-28.")
MOOD = "Cold and wet: grey-blue rock, ice and snow at the mouths, dripping water, mirages that ripple like heat haze; the reservoir a black water far below the railing, later a bed of weed and silt."


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
        if extra.get('secret'):
            s['secret'] = True
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
        'format': 0, 'level': 'L1' if level == 'L1' else ('L2' if level == 'L2' else 'L3'), 'pitch': PITCH, 'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:mirages', 'spaces': ['room:north_mouth', 'room:icicle_hall', 'room:false_passage', 'room:mirage_cache'],
             'notes': "Through the phantom safe's mirage and back to the mouth through the second."},
            {'id': 'loop:drained', 'spaces': ['room:ledge', 'room:steps', 'room:reservoir', 'room:wreck', 'room:wreck_stair', 'room:drowned'],
             'notes': "Down the steps, up through the drowned gallery; closed until the plug is pulled."},
            {'id': 'loop:through', 'spaces': ['room:north_mouth', 'room:icicle_hall', 'room:mirage_hall', 'room:frost_cavern', 'room:south_mouth'],
             'notes': "In at one mouth, out at the other, back over X5."},
        ],
        'entrances': [
            {'id': 'entrance:x5_north', 'space': 'room:north_mouth', 'kind': 'both', 'neighbour': 'exit:x5_north', 'facing': 's',
             'notes': "The arrival (D-4 item 5). 'Leave the Cave of Illusion?' (aaze0042:49)."},
            {'id': 'entrance:x5_south', 'space': 'room:south_mouth', 'kind': 'both', 'neighbour': 'exit:x5_south',
             'notes': "To the Troll Forest side of X5. 'Leave the Cave of Illusion?' (aaze0042:49)."},
        ],
        'critical_path': ['room:north_mouth', 'room:icicle_hall', 'room:mirage_hall', 'room:frost_cavern', 'room:sluice',
                          'room:frost_cavern', 'room:mirage_hall', 'room:ice_stair', 'room:ledge', 'room:mirror_maze',
                          'room:guard_post', 'room:echo_cave', 'room:guard_post', 'room:mirror_maze', 'room:ledge',
                          'room:steps', 'room:reservoir', 'room:grotto'],
        'return_path': ['room:grotto', 'room:reservoir', 'room:wreck', 'room:wreck_stair', 'room:drowned', 'room:ledge',
                        'room:ice_stair', 'room:mirage_hall', 'room:frost_cavern', 'room:south_mouth'],
        'goals': [{'id': 'goal:enchanted_key', 'space': 'room:grotto', 'kind': 'use',
                   'what': "Give the great skull ten gems: the Enchanted Key (A3's hook m12.skull)."}],
        'keys': [
            {'id': 'key:plug', 'grants': {'qbit': 'plug_pulled'}, 'found_in': 'room:sluice', 'how': 'lever',
             'notes': "Might 30 on the pulling member, potions counting; the Potion of Might behind the mirage helps."},
            {'id': 'key:gems', 'grants': {'item': 'enchanted_key'}, 'found_in': 'room:echo_cave', 'how': 'chest',
             'notes': "Fifteen fixed gems in the echo cave pay the great skull's ten."},
        ],
        'points_of_interest': [
            {'id': 'poi:plug', 'space': 'room:sluice', 'kind': 'lever',
             'behaviour': "The bronze plug: 'You aren't strong enough to pull the plug.' (aaze0042:23) below Might 30; pulled once it sets plug_pulled, sinks the water and opens the three sluice gates."},
            {'id': 'poi:safe', 'space': 'room:false_passage', 'kind': 'sign',
             'behaviour': "'Your hand passes through the safe as though it were not there.' (aaze0042:72); hover name Safe."},
            {'id': 'poi:mirages', 'spaces': ['room:false_passage', 'room:north_mouth', 'room:mirror_maze', 'room:grotto'],
             'kind': 'sign', 'count': 4,
             'behaviour': "Rippling rock walls: a click or walking into one: 'The mirage dissipates with your touch.' (aaze0042:24) and it opens at once."},
            {'id': 'poi:skulls', 'spaces': ['room:skulls_1', 'room:skulls_2', 'room:grotto'], 'kind': 'fountain', 'count': 5,
             'behaviour': "Talking skulls selling stat rises for gems, once per character (Yes/No; the great skull a choice of three)."},
            {'id': 'poi:notice', 'space': 'room:ledge', 'kind': 'sign',
             'behaviour': "A scratched notice: the skulls take gems, and the echo cave past the Guardians' post keeps some."},
        ],
        'mechanisms': [
            {'kind': 'mirage wall (click or step)', 'count': 4}, {'kind': 'plug (Might check)', 'count': 1},
            {'kind': 'water mover sinking 640', 'count': 1}, {'kind': 'sluice gate', 'count': 3},
            {'kind': 'once-per-character skull', 'count': 5},
        ],
        'totals': {'chests': 5, 'doors': 8, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act2_graphs/xd10.graph.yml; D-4 (mockups/act2_dungeon_decisions.md) wins where they differ: mirages as door faces opened by a click or a step, the drain as one water mover with stone sluice gates, Might 30 with potions, D-4's gem prices. Floors at 0, -640, -1280. Three connectors (the ice stair, the reservoir steps, the gallery stair) carry the stair links. All 50 monsters placed (exact counts); the reservoir's six start hidden under the water and show when the party first walks onto the drained bed.",
    }


DIAGRAM = """UPPER CAVES (0)
  X5 <== [NORTH MOUTH: arrival, snow] ~mirage~ [CACHE: chest $ Potion of Might] ~mirage~ [PHANTOM SAFE: 'Safe']
              |                                                                               |
         [ICICLE HALL] ------------------------------------------------------------------------+
              |
         [HALL OF MIRAGES] -- ice stair down (0 -> -640) --> LEDGE
              |
  [SKULL ALCOVES: Luck, Personality +2/3 gems] -- [FROST CAVERN] -- door -- [SLUICE: BRONZE PLUG, window over the reservoir]
              |
  X5 <== [SOUTH MOUTH]
DROWNED GALLERIES (-640)
  [DROWNED GALLERY] =gate= [LEDGE (railed) over the RESERVOIR; notice] -- [MIRROR MAZE] -- [GUARDIAN POST $] -- [ECHO CAVE $ 15 gems]
        | gate                    | gate                                  ~mirage~
  gallery stair             reservoir steps                     [DEEP SKULLS: Intellect, Speed +3/5 gems]
RESERVOIR BED (-1280)
  [SUMP] -- [SUNKEN BOAT $] -- [RESERVOIR BED: water mover sinks 640] -- [GROTTO: GREAT SKULL, key 10 gems] ~mirage~ [PHANTOM VAULT $ hoard]
 $ chest   =gate= stone sluice gate opened by the plug   ~mirage~ rippling wall opened by a click or a step
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', dict(project(level), identity=IDENTITY) if level == 'L4' else project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:cave', 'ambient': 14},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "XD-10 Cave of Illusion: three levels (upper caves 0, drowned galleries -640, reservoir bed -1280) in the plan's frame (x east, y north, heights from the arrival floor); the reservoir a tall cavern east of everything. Written by output/studio_cal/xd10/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
