#!/usr/bin/env python3
"""Writes DD-19 Wizard Quarter's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd19/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act4_graphs/dd19.graph.yml with decider D-42,
mockups/act4_a8_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
objects.yml, wiring.yml and atmosphere.yml (dress.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/dd19'


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
WIZARD, SORCERER, XENOC = 11190, 11191, 11196
ENCHANTRESS, GRAND, MORGANA = 11181, 11182, 11183
HAND, GOLEM = 11602, 11582
LEVEL = {WIZARD: 36, SORCERER: 45, XENOC: 60, ENCHANTRESS: 40, GRAND: 55, MORGANA: 60, HAND: 35, GOLEM: 40}

# D3 (installed, A5): the guild gate's arrival outside (assets_dev/worlds/xeen/maps/xeen_d3.studio.yml).
D3_GATE = 'entrance:dd19_gate'          # (-10752, 22016, 1728) facing 512

QBITS = {'dd19_arrived_once': 117520,
         # A3's bits read here (the hooks set them)
         'started': 113280, 'done': 113281, 'xenoc_slain': 113283, 'morgana_slain': 113284,
         'blastem_angered': 113286}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-19 Wizard Quarter, the precinct behind Sandcaster's guild gate (D3; the "
    "source's wizard corner of dark maze0031), as one BLV of three floors: an open-sky guild court between Xenoc's "
    "Mirage Guild (west) and Morgana's Sorceress HQ (east), a covered bridge between their upper floors, the Guild "
    "Common behind the arcade, and the guilds' quarters, alembic cellar and vault in an undercroft. Side quest Q-D14 "
    "(Astra; A3's hooks q-d14.xenoc, q-d14.morgana, q-d14.orange_potion, q-d14.purple_potion, q-d14.blastem; "
    "q-d14.quarter_gate is D3's), Promo Spy. Size M (MAPS.md section 0, D-42): 20-45 sectors, 30-90 M units squared, "
    "levels 32-55, Xenoc 60, Morgana 60, party 38-41, treasure 4 (hoard 5), music 34. Graph "
    "devdocs/xeen/mockups/act4_graphs/dd19.graph.yml with decider D-42 (mockups/act4_a8_decisions.md, which wins): "
    "Morgana 60; casters with Carnage Hands and four Iron Golems in the vault, no fighting among the families; the "
    "court under open sky (xeen_darkside_fading); Blastem (NPC 5248) a talking actor in the Common, 'The lesson' "
    "swaps him for Sorcerer 11191, hostile; the ward fed by two lamps that names them; the font refills spell points, "
    "repeatable; nothing changes inside after q-d14.done; the Orange and Purple Potions once per character. Rows (A2): "
    "wizards 11190 (Wizard 36 x16, Sorcerer 11191 45 x4, Xenoc 11196 60), sorceresses (Enchantress 11181 40 x10, "
    "Grand Sorceress 11182 55 x2, Morgana 11183 60), magic constructs (Carnage Hand 11602 35 x12), material golems "
    "(Iron Golem 11582 40 x4). Kill XP 98,846 for the party, 24.71k per member. Rest encounters 10 %: the sorceresses "
    "only (D-42). Map qbits 117520-117559 (dd19_arrived_once 117520, A3's); map_stats 9172.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd19', 'name': 'Wizard Quarter', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-19', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [20, 12], 'climbs': 'n'},
        'map_stats': {
            'id': 9172, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 3,
            'perception_difficulty': 4, 'refill_days': 672, 'music': 34, 'environment': 'stoneroom',
            'lock_difficulty': 6,
            'slots': [{'monster': 'Xeen Sorceress', 'tier': 0, 'per_marker': [2, 3], 'weight': 75},
                      {'monster': 'Xeen Sorceress', 'tier': 1, 'per_marker': [1, 2], 'weight': 25}],
        },
        'neighbours': [
            {'id': 'exit:d3_gate', 'to': 'xeen_d3.odm', 'kind': 'door', 'arrival': D3_GATE,
             'arrival_hint': "On D3 inside Sandcaster's wizard quarter, south of the guild gate (A5's entrance:dd19_gate, (-10752, 22016, 1728) facing 512; D-42 (4) asks about (-10496, 22150, 1728) facing south).",
             'notes': "The guild gate both ways: D3's thing:dd19_gate (A3's q-d14.quarter_gate 'Enter?', A5) moves the party to entrance:d3_guild_gate, the court's south side facing north; the gate's inside face (the exit preset, D-24) leads back to D3's entrance:dd19_gate."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


W, S, E, GS, CH, IG = WIZARD, SORCERER, ENCHANTRESS, GRAND, HAND, GOLEM
# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    'court': ("Guild court", 'room', 'L', 'court',
              "Open sky over pink ashlar: the guild gate behind the arrival (entrance:d3_guild_gate), the Mirage Guild's double door west, the Sorceress HQ's east, the arcade's three arches north under the covered bridge. No monster (D-11.3).",
              [], [], {'empty': True, 'goal': True}),
    'arcade': ("The arcade", 'corridor', 'M', 'court',
               "The covered walk under the guild bridge, the Guild Common's door in its back wall.", [], [], {'empty': True}),
    'common': ("Guild Common", 'room', 'M', 'court',
               "The guilds' refectory: long tables, the hearth, the font of spell points ('+2000 spell points.', repeatable, D-42 (7)); Blastem the Wizard (NPC 5248) at his own table, a talking actor (D-42 (5)).",
               [], [], {'empty': True}),
    'weights': ("Weights and Measures", 'room', 'S', 'court', "The quarter's tax office: scales, ledgers, the wizards' tax chest.",
                [placed(CH, 2)], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
    'mirage_foyer': ("Mirage Guild", 'room', 'M', 'court', "Behind the guild's double door: Icewind's grey brick.",
                     [placed(W, 4)], [], {}),
    'illusions': ("Hall of illusions", 'room', 'M', 'court',
                  "The lecture hall: benches, a lectern, a painted false door ('A painted door').",
                  [placed(W, 3), placed(S, 1, 'heavy')], [], {}),
    'mirage_stair': ("Mirage stair", 'room', 'S', ['court', 'upper'],
                     "Two storeys: from the hall of illusions up to its head (the graph's mirage_landing) and the mirror gallery; the alcoves' head through its west wall.",
                     [], [], {'empty': True}),
    'mirror_gallery': ("Mirror gallery", 'corridor', 'M', 'upper',
                       "A tall mirror on the west wall facing a blank wall that is not there (the mirage, passable): 'In the mirror, the blank wall behind you has a door in it.'",
                       [placed(W, 3), placed(CH, 2)], [], {}),
    'mirage_hall': ("Hall of Mirages", 'room', 'L', 'upper',
                    "Xenoc's hall: his raised chair under the triple window, the floor shimmering like water; the bridge door's bolt. Xenoc's death: q-d14.xenoc.",
                    [placed(XENOC, 1, 'boss', role='boss'), placed(S, 2, 'heavy')], [], {'goal': True}),
    'xenoc_study': ("Xenoc's study", 'room', 'S', 'upper', "A desk, a chest, the lever under the guild's seal that opens the vault ('Far below, iron grinds.').",
                    [], [{'kind': 'chest', 'count': 1, 'tier': 4}], {'empty': True}),
    'bridge': ("Guild bridge", 'corridor', 'M', 'upper',
               "The covered bridge over the arcade, windows down into the court; its west door bolted on Xenoc's side.",
               [placed(CH, 2)], [], {}),
    'scrying': ("Scrying room", 'room', 'M', 'upper',
                "A crystal on a stand, skull niches; ward lamp 1, a floor brazier ('A ward lamp. Snuff it?').",
                [placed(E, 3)], [], {}),
    'hq_foyer': ("Sorceress HQ", 'room', 'M', 'court', "Behind the double door: Corlagon's dark brick.",
                 [placed(E, 3), placed(CH, 2)], [], {}),
    'hq_stair': ("HQ stair", 'room', 'S', ['court', 'upper'],
                 "Two storeys: up to its head (the graph's hq_landing) before Morgana's door, the ward of light fed by two lamps; the robing room's door.",
                 [], [], {'empty': True}),
    'robing': ("Robing room", 'room', 'M', 'court', "Robe racks; ward lamp 2 on a wall bracket; the back stair down.",
               [placed(E, 2)], [], {}),
    'morgana_sanctum': ("Morgana's sanctum", 'room', 'L', 'upper',
                        "Morgana on her dais between her two Grand Sorceresses. Her death: q-d14.morgana.",
                        [placed(MORGANA, 1, 'boss', role='boss'), placed(GS, 2, 'heavy')], [], {'goal': True}),
    'wardrobe': ("Morgana's wardrobe", 'room', 'S', 'upper', "Robes on racks and a chest.",
                 [], [{'kind': 'chest', 'count': 1, 'tier': 4}], {'empty': True}),
    'alcoves': ("Potion alcoves", 'room', 'M', ['under', 'court'],
                "Two storeys: from the head (0) down to two alcoves: the Orange Potion (+2 Intellect) and the Purple Potion (+2 Speed), once per character.",
                [placed(W, 2)], [], {}),
    'quarters_w': ("Guild Quarters (wizards)", 'room', 'M', 'under',
                   "Cells of beds and a chest: opening it, 'Ambush!' and four wizards are shown (D-18).",
                   [placed(W, 4, notes='hidden, shown when the chest is opened')], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
    'undercroft': ("Undercroft", 'corridor', 'M', 'under',
                   "The vaulted passage under the court and the Common joining both guilds' quarters; the vault's iron door south.",
                   [placed(CH, 2), placed(S, 1, 'heavy')], [], {}),
    'quarters_stair': ("Quarters stair", 'room', 'S', ['under', 'court'],
                       "Two storeys: down from the Common to its foot (the graph's stair_foot) on the undercroft.",
                       [], [], {'empty': True}),
    'quarters_e': ("Guild Quarters (sorceresses)", 'room', 'M', 'under', "The sorceresses' cells; a chest.",
                   [placed(CH, 2)], [{'kind': 'chest', 'count': 1, 'tier': 4}], {}),
    'alembic': ("Alembic cellar", 'room', 'M', 'under', "Retorts and a still against the walls; shelves of empty bottles.",
                [placed(E, 2)], [], {}),
    'back_stair': ("HQ back stair", 'room', 'S', ['under', 'court'], "Up from the alembic cellar to the robing room.",
                   [], [], {'empty': True}),
    'vault': ("Guild vault", 'room', 'M', 'under', "Four iron wardens and the guilds' hoard, behind the iron door the study's lever opens.",
              [placed(IG, 4, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
}
FLOORS = {'upper': geo.UP, 'court': geo.G0, 'under': geo.UN}

LINKS = [
    ('link:court_mirage', 'court', 'mirage_foyer', 'double_door', {'purpose': "Great-hall doors: two leaves (t07c03c, t07c03d) opening apart."}),
    ('link:court_hq', 'court', 'hq_foyer', 'double_door', {'purpose': "Two leaves, as the Mirage Guild's."}),
    ('link:court_arcade', 'court', 'arcade', 'colonnade', {'purpose': "Three arches under the bridge."}),
    ('link:court_common', 'arcade', 'common', 'door', {}),
    ('link:mirage_illusions', 'mirage_foyer', 'illusions', 'open', {}),
    ('link:illusions_stair', 'illusions', 'mirage_stair', 'open', {}),
    ('link:hq_stair', 'hq_foyer', 'hq_stair', 'open', {}),
    ('link:stair_robing', 'hq_stair', 'robing', 'door', {}),
    ('link:common_weights', 'common', 'weights', 'door', {}),
    ('link:common_qstair', 'common', 'quarters_stair', 'stairs', {}),
    ('link:mirage_up', 'mirage_stair', 'mirror_gallery', 'stairs', {}),
    ('link:mirage_down', 'mirage_stair', 'alcoves', 'stairs', {}),
    ('link:back_up', 'back_stair', 'robing', 'stairs', {}),
    ('link:mirage_wall', 'mirror_gallery', 'mirage_hall', 'secret_door', {'purpose': "The mirage wall: a wall that is not there."}),
    ('link:hall_study', 'mirage_hall', 'xenoc_study', 'door', {}),
    ('link:hall_bridge', 'mirage_hall', 'bridge', 'door', {'opened_by': 'key:bolt', 'purpose': "Bolted on Xenoc's side."}),
    ('link:bridge_scry', 'bridge', 'scrying', 'open', {}),
    ('link:scry_landing', 'scrying', 'hq_stair', 'open', {'purpose': "Onto the HQ stair's head."}),
    ('link:ward', 'hq_stair', 'morgana_sanctum', 'door', {'opened_by': 'key:lamps', 'purpose': "The ward: two lamps."}),
    ('link:sanctum_wardrobe', 'morgana_sanctum', 'wardrobe', 'door', {}),
    ('link:alcoves_qw', 'alcoves', 'quarters_w', 'open', {}),
    ('link:qw_undercroft', 'quarters_w', 'undercroft', 'door', {}),
    ('link:undercroft_foot', 'undercroft', 'quarters_stair', 'open', {}),
    ('link:foot_qe', 'undercroft', 'quarters_e', 'door', {}),
    ('link:qe_alembic', 'quarters_e', 'alembic', 'open', {}),
    ('link:alembic_back', 'alembic', 'back_stair', 'door', {}),
    ('link:vault_door', 'undercroft', 'vault', 'door', {'opened_by': 'key:vault_lever', 'purpose': "Iron door: the study's lever."}),
]

PITCH = ("Behind Sandcaster's guild gate, a precinct of pink ashlar under the Darkside's fading sun: two guild halls "
         "face each other across an open court, Xenoc's Mirage Guild and Morgana's Sorceress HQ, joined above by a "
         "covered bridge and below by an undercroft of quarters and a vault. Xenoc hides his hall behind a wall that "
         "is not there; Morgana sits behind a ward fed by two lamps. Both must die for Astra.")
PURPOSE = ("Side quest Q-D14 (Astra, Act IV, level 39): kill Xenoc (q-d14.xenoc) and Morgana (q-d14.morgana); Astra's "
           "hand-in opens the quarter's houses on D3 and names the party's Rogues Spies. Class M, party 38-41, "
           "monsters 32-55, Xenoc 60, Morgana 60.")
MOOD = ("Rosy ashlar and marble in the court under a dimming sky; Icewind's cold grey brick and beams in the Mirage "
        "Guild; Corlagon's dark brick, skulls and violet flames in the Sorceress HQ; a low dark vault below.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, pop, tre, extra) in SP.items():
        floor = [FLOORS[f] for f in fl] if isinstance(fl, list) else FLOORS[fl]
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': floor, 'purpose': purpose}
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
            {'id': 'loop:bridge', 'spaces': ['room:court', 'room:mirage_foyer', 'room:illusions', 'room:mirage_stair',
                                             'room:mirror_gallery', 'room:mirage_hall', 'room:bridge', 'room:scrying',
                                             'room:hq_stair', 'room:hq_foyer'],
             'notes': "Over the arcade by the bridge, once Xenoc's bolt is drawn."},
            {'id': 'loop:undercroft', 'spaces': ['room:court', 'room:arcade', 'room:common', 'room:quarters_stair',
                                                 'room:undercroft', 'room:quarters_e', 'room:alembic', 'room:back_stair',
                                                 'room:robing', 'room:hq_stair', 'room:hq_foyer'],
             'notes': "Under the court into the Sorceress HQ by its back stair."},
            {'id': 'loop:mirage_cellar', 'spaces': ['room:court', 'room:arcade', 'room:common', 'room:quarters_stair',
                                                    'room:undercroft', 'room:quarters_w', 'room:alcoves',
                                                    'room:mirage_stair', 'room:illusions', 'room:mirage_foyer'],
             'notes': "Under the court into the Mirage Guild by the alcoves' stair."},
        ],
        'entrances': [
            {'id': 'entrance:d3_guild_gate', 'space': 'room:court', 'kind': 'both', 'neighbour': 'exit:d3_gate',
             'facing': 'n', 'how': "D3's guild gate (thing:dd19_gate, q-d14.quarter_gate 'Enter?', A5) sets the party on the court's south side, 384 inside the gate, facing north; the gate's inside face is the way out (the exit preset)."},
        ],
        'critical_path': ['room:court', 'room:mirage_foyer', 'room:illusions', 'room:mirage_stair',
                          'room:mirror_gallery', 'room:mirage_hall', 'room:bridge', 'room:scrying', 'room:hq_stair',
                          'room:robing', 'room:hq_stair', 'room:morgana_sanctum'],
        'return_path': ['room:morgana_sanctum', 'room:hq_stair', 'room:hq_foyer', 'room:court'],
        'goals': [
            {'id': 'goal:xenoc', 'space': 'room:mirage_hall', 'kind': 'kill', 'what': "Xenoc (11196): q-d14.xenoc (xenoc_slain 113283)."},
            {'id': 'goal:morgana', 'space': 'room:morgana_sanctum', 'kind': 'kill', 'what': "Morgana (11183): q-d14.morgana (morgana_slain 113284)."},
        ],
        'keys': [
            {'id': 'key:bolt', 'grants': {'map_var': 'bolt_drawn'}, 'found_in': 'room:mirage_hall', 'how': 'lever',
             'notes': "The bridge door's bolt, drawn from Xenoc's side."},
            {'id': 'key:lamps', 'grants': {'map_var': 'ward_down'}, 'found_in': 'room:scrying', 'how': 'lever',
             'notes': "The two ward lamps (scrying room and robing room): both out, the ward goes out."},
            {'id': 'key:vault_lever', 'grants': {'map_var': 'vault_open'}, 'found_in': 'room:xenoc_study', 'how': 'lever',
             'notes': "The lever under the guild's seal: the vault's iron door."},
        ],
        'points_of_interest': [
            {'id': 'poi:mirror', 'space': 'room:mirror_gallery', 'kind': 'sign', 'behaviour': "'In the mirror, the blank wall behind you has a door in it.'"},
            {'id': 'poi:blastem', 'space': 'room:common', 'kind': 'npc',
             'behaviour': "Blastem the Wizard (NPC 5248): his greeting (aaze0031:51), 'The lesson' (blastem_angered: the swap to Sorcerer 11191, hostile) or 'Boots licked' (aaze0031:112, the mirror's hint)."},
            {'id': 'poi:font', 'space': 'room:common', 'kind': 'fountain', 'behaviour': "'+2000 spell points.': every member's spell points refilled, repeatable."},
            {'id': 'poi:potions', 'space': 'room:alcoves', 'kind': 'fountain', 'count': 2,
             'behaviour': "The Orange (+2 Intellect) and Purple (+2 Speed) Potions: q-d14.orange_potion / q-d14.purple_potion, once per character."},
            {'id': 'poi:lamps', 'space': 'room:scrying', 'kind': 'lever', 'count': 2, 'behaviour': "'A ward lamp. Snuff it?'"},
            {'id': 'poi:ambush', 'space': 'room:quarters_w', 'kind': 'trap', 'behaviour': "The chest: 'Ambush!' (aaze0031:56), four hidden wizards shown."},
            {'id': 'poi:painted_door', 'space': 'room:illusions', 'kind': 'sign', 'behaviour': "'A painted door'."},
        ],
        'mechanisms': [
            {'kind': 'illusory wall shown by a mirror', 'count': 1}, {'kind': 'bolt drawn from one side', 'count': 1},
            {'kind': 'ward fed by two lamps', 'count': 1}, {'kind': 'lever opens a far door', 'count': 1},
            {'kind': 'hidden group shown by a chest', 'count': 1}, {'kind': 'talking actor swapped for a monster', 'count': 1},
            {'kind': 'boss death hook', 'count': 2},
        ],
        'totals': {'chests': 6, 'doors': 13, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act4_graphs/dd19.graph.yml; D-42 (mockups/act4_a8_decisions.md) wins where they differ: Morgana 60; the two-lamp ward names its lamps; Blastem a talking actor. Changes from the graph (A8 L2): the stair heads (mirage_landing, hq_landing) and the quarters stair's foot (stair_foot) are the two-storey stair rooms' own heads and feet; the Mirage stair's way down is through the potion alcoves' own stair (entered at their head); the arcade under the bridge is its own room (the bridge crosses the court's north end); the sorceresses' quarters open off the undercroft. All 50 monsters placed.",
    }


DIAGRAM = """UPPER FLOORS (640)
  [MIRROR GALLERY: mirror] ~mirage~ [HALL OF MIRAGES: Xenoc, bolt] =bolted= [BRIDGE] -- [SCRYING: lamp 1] -- [HQ STAIR head] =ward= [MORGANA'S SANCTUM] = [WARDROBE $]
        |head                              |door                                                                  (the HQ stair's head)
  (Mirage stair head)                [XENOC'S STUDY $, vault lever]
COURT LEVEL (0)
  [ALCOVES head] -- [MIRAGE STAIR] -- [HALL OF ILLUSIONS] -- [MIRAGE GUILD] ==double== [COURT (sky)] ==double== [SORCERESS HQ] -- [HQ STAIR] = [ROBING: lamp 2]
                                                                                         ||| arches                                       |
                                                                                       [ARCADE] = [GUILD COMMON: font, Blastem] = [WEIGHTS $]  [back stair head]
                                                                                                        |
                                                                                                 [QUARTERS STAIR head]
UNDERCROFT (-512)
  [ALCOVES: 2 potions] -- [QUARTERS (wizards) $ ambush] = [UNDERCROFT] = [QUARTERS (sorceresses) $] -- [ALEMBIC] = [BACK STAIR]
                                                            || iron door   \\-- [QUARTERS STAIR foot]
                                                         [GUILD VAULT $$: 4 golems]
 $ chest   = door   ~ the mirage (passable)   the guild gate (exit) in the court's south wall
"""


# D-89 identity (lane A8 s29): what the party must see. Family: no shipped BLV is assigned to DD-19 in
# dungeon_families.yml; its HQ and undercroft (most of the map) are MM6 Corlagon's Estate 6d11 (DECIDE).
IDENTITY = {'shape': 'hall', 'family': '6d11',
            'seen': ["the guild court open to the sky: pink ashlar over a grey base course under a cornice and "
                     "crenellated coping, the two guilds' great doors facing each other",
                     "the Mirage Guild's hall: bookcase walls, a magic circle in the floor and the guild's crystal "
                     "on its stand",
                     "the Sorceress HQ's hall: violet braziers, shelves of skulls, purple-flamed torches"]}

def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', dict(project(level), identity=IDENTITY) if level == 'L4' else project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:hc', 'ambient': 12},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-19 Wizard Quarter: the undercroft at -512, the court level at 0, the upper floors at 640, in one frame (x east, y north, z up). Written by output/studio_cal/dd19/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
