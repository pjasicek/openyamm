#!/usr/bin/env python3
"""Writes DD-21 Necropolis Sewer's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd21/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act5_graphs/dd21.graph.yml with decider D-62,
mockups/act5_a8_decisions_b.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
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
BR = R / 'devdocs/xeen/briefs/dd21'


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


# Rows (assets_dev/worlds/xeen/source/monsters.yml, A2; D-62)
ROACH, LICH, MUMMY, SANDRO, RISEN = 11363, 11281, 11273, 11283, 11926
LEVEL = {ROACH: 40, LICH: 50, MUMMY: 62, SANDRO: 65, RISEN: 65}

# D6 (installed, A6): its arrival by the crypt's door (assets_dev/worlds/xeen/maps/xeen_d6.studio.yml).
D6_STAIR = 'entrance:dd21_stair'      # (17408, -11776, 1664) facing 512

QBITS = {
    # map qbits (D-62: 117720-117727; 117728 unused)
    'dd21_arrived_once': 117720, 'sluice_open': 117721, 'sandro_met': 117722, 'dead_food_pried': 117723,
    'drain_1': 117724, 'drain_2': 117725, 'drain_3': 117726, 'sandro_fell': 117727,
    # A3's Q-D23 bits read here (the hooks set them)
    'beaten': 113460, 'heart_found': 113461, 'released': 113462, 'taught': 113463,
}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-21 Necropolis Sewer (the source's dark maze0036 under the Necropolis, "
    "aaze0035:25-29 and aaze0036) as one BLV of three floors under D6's Necropolis: Sandro's crypt at 0, the sewer at "
    "-512, the lowest culvert at -896. Side quest Q-D23 Sandro's Heart (A3's hooks q-d23.sandro, q-d23.heart, "
    "q-d23.release, q-d23.ritual; Promo Lich / Priest of Dark). Size S (MAPS.md section 0, D-62): at most 15 sectors "
    "and 20 M units squared, doors 3-8, levels 40-62, Sandro 65, party 49-52, treasure 5, music 11. Graph "
    "devdocs/xeen/mockups/act5_graphs/dd21.graph.yml with decider D-62 (mockups/act5_a8_decisions_b.md, which wins): "
    "15 + Sandro (Cinder Roach 11363 40 x10, two hidden in the Dead Food barrel; Greater Lich 11281 50 x3; Ghost "
    "Mummy 11273 62 x2; Sandro 11283 65 once), kill XP 42,803 for the party, 10.70k per member; Sandro falls once "
    "and rises as the peaceful, unkillable row 11926 by his bier (map qbit 117727 sandro_fell), released with his "
    "heart; the Dead Food barrel (Might 30, +2 Endurance once per character); the sluice wheel opens the culvert gate "
    "(one way, D-43); the reliquary grille opens with the release. Rest encounters 10 %: the pyramid mummies at Dif 0 "
    "(Tomb Mummy 42) only (D-62 Q47, A2's row 9174). Map qbits 117720-117727; map_stats 9174.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd21', 'name': 'Necropolis Sewer', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-21', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [14, 14], 'climbs': 'n'},
        'map_stats': {
            'id': 9174, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 5, 'trap_dice': 8,
            'perception_difficulty': 15, 'refill_days': 672, 'music': 11, 'environment': 'stoneroom',
            'lock_difficulty': 15,
            # D-62 Q47: the pyramid mummies at Dif 0 (Tomb Mummy 42 only), as A2's row 9174 (groups of 1-2)
            'slots': [{'monster': 'Xeen Mummy', 'tier': 0, 'per_marker': [1, 2], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d6_stair', 'to': 'xeen_d6.odm', 'kind': 'door', 'arrival': D6_STAIR,
             'arrival_hint': "On D6 (the Forbidden Zone) in the Necropolis, about 280 north of the crypt's door, facing away from it (A6's entrance:dd21_stair, (17408, -11776, 1664) facing 512).",
             'notes': "D6 installed by A6: its door:dd21 (thing:dd21_crypt, the grille pair gkp103a in the Necropolis's south-east corner) is to arrive at this map's entrance:d6_stair, the stair's foot (0, 0, 0) facing south (1536); it stays sealed with a line until A6 unseals it. The way out is the exit preset on the grille pair's inner face at the stair's top. 'Climb up to the Necropolis?' is the exit's meaning (A3, a map-local line)."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


FLOORS = {'crypts': geo.CRYPT, 'sewer': geo.SEWER, 'culvert': geo.LOW}
# id: (name, kind, size, floor, purpose, population, treasure, extra)
SP = {
    'stair_foot': ("Crypt stair", 'stair', 'S', 'crypts',
                   "The arrival (entrance:d6_stair) at the foot of a straight stair that climbs north 448 to the grille pair (gkp103a, two leaves, the exit preset). Quiet (D-11.3); map qbit 117720 dd21_arrived_once.",
                   [], [], {'empty': True}),
    'crypt_hall': ("Hall of Biers", 'hall', 'M', 'crypts',
                   "A long vault of burial niches (d2niche) with stone biers against both walls. Sandro's seal (xdsandro, once) over the two-leaf crypt doors at the south end; in the west wall the head of the railed stair down to the sewer.",
                   [placed(LICH, 2, 'heavy')], [], {}),
    'sandro_crypt': ("Sandro's crypt", 'hall', 'M', 'crypts',
                     "A square vault on posts, the dais with Sandro's bier, the reliquary's grille in the east wall. First entry: his name and 'And now my hunger for the living compels me to attack you.' (aaze0035:25, :26; 117722). His fall: q-d23.sandro, sandro_fell 117727, the risen Sandro (11926) by the bier. The dais's step and the bier's click are where he talks; with the heart the two prompts (q-d23.release, q-d23.ritual).",
                     [placed(SANDRO, 1, 'boss', role='boss')], [], {'goal': True}),
    'reliquary': ("Sandro's reliquary", 'room', 'S', 'crypts',
                  "Behind the iron grille (opened by the release): Sandro's chest (T5) and his statuette on its plinth (dressing; aaze0035:29 at the grille before the release).",
                  [], [{'kind': 'chest', 'count': 1, 'tier': 5}], {'empty': True}),
    'landing': ("Stair landing", 'stair', 'S', ['sewer', 'crypts'],
                "The railed stair's foot on a stone platform where the main channel's two arms meet. Quiet.",
                [], [], {'empty': True}),
    'main_west': ("Main channel (west)", 'corridor', 'M', 'sewer',
                  "The long sewage channel's west arm, walkways both sides; sewer drains in the walls (one holds a find); at its west end the old tomb wall's stone door ('Mummy's Secret Treasure', aaze0036:10); the west culvert south.",
                  [placed(ROACH, 3)], [], {}),
    'main_east': ("Main channel (east)", 'corridor', 'M', 'sewer',
                  "The channel's east arm, drains in the walls (one find); signed barrels by the north wall ('Food for the dead, keep warm.', aaze0036:5); the cellar's door at its east end; the east culvert south.",
                  [placed(ROACH, 2)], [], {}),
    'dead_food': ("Dead-food cellar", 'room', 'S', 'sewer',
                  "The Necropolis's store of Dead Food, barrels in pairs by the walls (aaze0036:4, :5). One barrel's lid can be pried (Might 30, else aaze0036:7): two hidden roaches come out (117723), then the food is eaten once per character (+2 Endurance).",
                  [placed(ROACH, 2, notes='hidden in the Dead Food barrel, shown once by the pry (D-62 Q43)')], [],
                  {}),
    'west_culvert': ("West culvert", 'corridor', 'M', 'sewer',
                     "A culvert from the main channel south, then east to the outfall; a sewer drain with a find; the sluice room's door in its west wall.",
                     [], [], {'empty': True}),
    'sluice': ("Sluice room", 'room', 'S', 'sewer',
               "Dead end with the sluice wheel (117721): it lifts the culvert gate below the outfall, one way (D-43). Quiet.",
               [], [], {'empty': True}),
    'mummy_vault': ("Mummy's vault", 'room', 'S', 'sewer',
                    "A sealed tomb the main channel cut into, two Ghost Mummies standing in it; the source's 'Mummy's Secret Treasure' (T5).",
                    [placed(MUMMY, 2, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
    'outfall': ("Outfall", 'hall', 'M', 'sewer',
                "Both culverts pour into a round basin; at its south side the sluice gate over the steps down. The source's alcove (aaze0036:0) as dressing. Quiet.",
                [], [], {'empty': True}),
    'east_culvert': ("East culvert", 'corridor', 'M', 'sewer',
                     "The east twin of the west culvert, back up to the main channel; in a side niche the source's trapped 'Box' (aaze0036:2, T5).",
                     [placed(ROACH, 2)], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}),
    'heart_culvert': ("Heart culvert", 'cave', 'M', ['culvert', 'sewer'],
                      "The sewer's lowest culvert, falling into a black cistern. On a ledge above the water the jar of green glass (q-d23.heart), a green light in it. A Greater Lich keeps it.",
                      [placed(LICH, 1, 'heavy'), placed(ROACH, 1)], [], {'goal': True}),
}

LINKS = [
    ('link:foot_hall', 'stair_foot', 'crypt_hall', 'open', {}),
    ('link:hall_crypt', 'crypt_hall', 'sandro_crypt', 'door', {'purpose': "The crypt's double doors (two leaves)."}),
    ('link:crypt_reliquary', 'sandro_crypt', 'reliquary', 'door',
     {'opened_by': 'goal:release', 'purpose': "The iron grille: it opens with Sandro's release."}),
    ('link:hall_landing', 'crypt_hall', 'landing', 'stairs', {'purpose': "The railed stair down to the sewer."}),
    ('link:landing_west', 'landing', 'main_west', 'open', {}),
    ('link:landing_east', 'landing', 'main_east', 'open', {}),
    ('link:east_cellar', 'main_east', 'dead_food', 'door', {}),
    ('link:west_culvert', 'main_west', 'west_culvert', 'open', {}),
    ('link:west_vault', 'main_west', 'mummy_vault', 'door', {'purpose': "The old tomb wall's stone door."}),
    ('link:culvert_sluice', 'west_culvert', 'sluice', 'door', {}),
    ('link:wculvert_outfall', 'west_culvert', 'outfall', 'open', {}),
    ('link:outfall_eculvert', 'outfall', 'east_culvert', 'open', {}),
    ('link:eculvert_east', 'east_culvert', 'main_east', 'open', {}),
    ('link:outfall_heart', 'outfall', 'heart_culvert', 'door',
     {'opened_by': 'key:sluice', 'purpose': "The sluice gate over the steps down; the wheel upstream lifts it."}),
]

PITCH = ("A lich's crypt over a sewer. The crypt stair under D6's Necropolis comes down into Sandro's Hall of Biers; "
         "Sandro himself waits in his crypt, fights, falls and rises again, unable to die. Below, the Necropolis's "
         "sewer runs in a ring of channels round an outfall; a wheel upstream lifts the gate to the lowest culvert, "
         "where his heart beats in a jar of green glass over a black cistern. Bring it back and he is released.")
PURPOSE = ("Side quest Q-D23 Sandro's Heart (QUESTS.md; Master Morbius 5506 sends the party): Sandro's first fall "
           "(q-d23.sandro), the heart (q-d23.heart), the release with the Key to the Dungeon of Death (q-d23.release), "
           "the ritual for Priests and Wizards first (q-d23.ritual: Priest of Dark, Lich). Class S, party 49-52, "
           "monsters 40-62, Sandro 65.")
MOOD = ("Tomb of Ethric's dark block stone and burial niches by candlelight above; below, Free Haven's wet sewer "
        "stone, ankle-deep sewage and the drip of the city's dead; at the bottom a green glow over black water.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, pop, tre, extra) in SP.items():
        floor = [FLOORS[f] for f in fl] if isinstance(fl, list) else FLOORS[fl]
        s = {'id': 'room:' + sid, 'name': name, 'kind': {'stair': 'room', 'hall': 'room', 'cave': 'room'}.get(kind, kind), 'size': size, 'floor': floor, 'purpose': purpose}
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
            {'id': 'loop:sewer_ring', 'spaces': ['room:landing', 'room:main_west', 'room:west_culvert', 'room:outfall',
                                                 'room:east_culvert', 'room:main_east'],
             'notes': "The sewer's ring: out along one arm of the main channel, down a culvert to the outfall, back up the other."},
        ],
        'entrances': [
            {'id': 'entrance:d6_stair', 'space': 'room:stair_foot', 'kind': 'both', 'neighbour': 'exit:d6_stair',
             'facing': 's',
             'how': "D6's crypt door in the Necropolis (A6's door:dd21) brings the party to the stair's foot facing south into the Hall of Biers; the grille pair at the stair's top is the way back to D6's entrance:dd21_stair."},
        ],
        'critical_path': ['room:stair_foot', 'room:crypt_hall', 'room:sandro_crypt', 'room:crypt_hall', 'room:landing',
                          'room:main_west', 'room:west_culvert', 'room:sluice', 'room:west_culvert', 'room:outfall',
                          'room:heart_culvert', 'room:outfall', 'room:east_culvert', 'room:main_east', 'room:landing',
                          'room:crypt_hall', 'room:sandro_crypt', 'room:reliquary'],
        'return_path': ['room:reliquary', 'room:sandro_crypt', 'room:crypt_hall', 'room:stair_foot'],
        'goals': [
            {'id': 'goal:sandro', 'space': 'room:sandro_crypt', 'kind': 'kill',
             'what': "Sandro's first fall (q-d23.sandro; sandro_fell 117727): the risen Sandro by his bier."},
            {'id': 'goal:heart', 'space': 'room:heart_culvert', 'kind': 'use',
             'what': "The jar of green glass (q-d23.heart: Sandro's Heart 12353)."},
            {'id': 'goal:release', 'space': 'room:sandro_crypt', 'kind': 'use',
             'what': "'Give Sandro his heart?' (q-d23.release: the Key to the Dungeon of Death 12354; the grille opens)."},
        ],
        'keys': [
            {'id': 'key:sluice', 'grants': {'qbit': 'sluice_open'}, 'found_in': 'room:sluice', 'how': 'lever',
             'notes': "The sluice wheel lifts the culvert gate below the outfall, one way (D-43)."},
        ],
        'points_of_interest': [
            {'id': 'poi:seal', 'space': 'room:crypt_hall', 'kind': 'sign',
             'behaviour': "Sandro's seal over the crypt's doors (xdsandro)."},
            {'id': 'poi:dais', 'space': 'room:sandro_crypt', 'kind': 'npc',
             'behaviour': "The dais's step and the bier's click: the risen Sandro speaks (q-d23.sandro), and with the heart asks for it (q-d23.release, q-d23.ritual)."},
            {'id': 'poi:grille', 'space': 'room:sandro_crypt', 'kind': 'sign',
             'behaviour': "'Don't even THINK about taking my statuette!' (aaze0035:29) before the release."},
            {'id': 'poi:dead_food', 'space': 'room:dead_food', 'kind': 'trap',
             'behaviour': "The Dead Food barrel: Might 30 to pry; two roaches; then +2 Endurance once per character."},
            {'id': 'poi:drains', 'space': 'room:main_west', 'kind': 'sign', 'count': 6,
             'behaviour': "Sewer drains (aaze0036:3, :1): three hold a find once (117724-117726)."},
            {'id': 'poi:barrels', 'space': 'room:main_east', 'kind': 'sign', 'count': 7,
             'behaviour': "'A sign on the barrel says: Food for the dead, keep warm.' (aaze0036:4, :5)."},
            {'id': 'poi:gate', 'space': 'room:outfall', 'kind': 'sign',
             'behaviour': "The sluice gate: 'A sluice gate. Its wheel must be upstream.' until the wheel turns."},
        ],
        'mechanisms': [
            {'kind': 'boss falls once and rises as a peaceful figure', 'count': 1},
            {'kind': 'talking bier and dais with two prompts', 'count': 1},
            {'kind': 'one-way wheel opens a gate', 'count': 1},
            {'kind': 'grille opened by a quest bit', 'count': 1},
            {'kind': 'barrel pried by Might shows hidden monsters, then a gift once per character', 'count': 1},
        ],
        'totals': {'chests': 3, 'doors': 8, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act5_graphs/dd21.graph.yml; D-62 (mockups/act5_a8_decisions_b.md) wins where they differ: Cinder Roach 11363 (placed only); the risen Sandro row 11926 keyed on sandro_fell 117727; the Dead Food roaches shown once by the pry; rests from the pyramid mummies at Dif 0. Changes from the graph (A8 L2): the landing and the heart culvert are two-storey rooms that carry the stairs (their heads at 0 and -512); the culverts are L-shaped (south, then in to the outfall). All 15 monsters and Sandro placed; doors: the crypt's pair (two leaves), the grille, the vault's stone door, the cellar's and the sluice room's iron doors, the sluice gate; the grille pair at the stair's top is two exit faces.",
    }


DIAGRAM = """THE CRYPTS (0)
                     [CRYPT STAIR: arrival at the foot; up north to the grille pair = exit to D6]
                                   |
  [LANDING head] <=railed stair== [HALL OF BIERS: 2 liches, niches, biers]
                                   ||double doors (Sandro's seal over)
                     [SANDRO'S CRYPT: Sandro, dais, bier, posts] =grille= [RELIQUARY $, statuette]
THE SEWER (-512)
  [MUMMY'S VAULT $] =stone door= [MAIN WEST: 3 roaches, drains] -- [LANDING foot] -- [MAIN EAST: 2, drains, barrels] =door= [DEAD-FOOD CELLAR: the barrel]
                                      |                                                   |
  [SLUICE: wheel] =door= [WEST CULVERT: drain] ---- [OUTFALL: basin] ---- [EAST CULVERT: 2, Box $ in its niche]
                                                       ||sluice gate (the wheel lifts it)
THE LOWEST CULVERT (-896)
                                        [HEART CULVERT: steps down, black cistern, the jar; lich + roach]
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
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:crypt', 'ambient': 12},
            'rooms': [geo.room_doc(r) for r in geo.ORDER], 'openings': geo.OPENINGS,
            'notes': "DD-21 Necropolis Sewer: the crypts at 0, the sewer at -512, the lowest culvert at -896, in one frame (x east, y north, z up). Written by output/studio_cal/dd21/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
