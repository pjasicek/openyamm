#!/usr/bin/env python3
"""Writes DD-08 Northern Tower's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd08/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act5_graphs/dd08.graph.yml with decider D-61,
mockups/act5_a8_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
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
BR = R / 'devdocs/xeen/briefs/dd08'


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


# Rows (assets_dev/worlds/xeen/source/monsters.yml, A2): the dark knights' A and B tiers in the Voweless faction
# (relations.yml xeen_voweless_knights, friendly after the oath 113344); the four oath figures (D-61 Q28)
SLAYER, DEATH = 11150, 11151
FIGURE = 11925
LEVEL = {SLAYER: 45, DEATH: 55}

D5_DOOR = 'entrance:dd08_door'   # (2560, 11776, 3008) facing 1536 (assets_dev/worlds/xeen/maps/xeen_d5.studio.yml)
D7_ROOF = 'entrance:dd08_roof'   # (5632, 15104, 1158) facing 512 (assets_dev/worlds/xeen/maps/xeen_d7.studio.yml)

QBITS = {
    # map qbits 117640-117679 (A3 registers); 117641-117647 freed by D-61 Q25 (the books pay by player bits)
    'arrived_once': 117640,
    'wall_w': 117652, 'wall_e': 117653,
    'shield_find': 117654, 'helm_find': 117655, 'mail_find': 117656,
    # A3's Q-D17 and M30 bits read here (the hooks set them)
    'voice_answered': 113342, 'oath': 113344, 'chalice_taken': 113345, 'm30_done': 111600,
}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-08 Northern Tower (the source's dark maze0069-0072: the Voweless Knights' "
    "tower) as one BLV of four floors 448 apart round a split stair core on D5, entered by the tower's south door "
    "(q-d17.tower_door, A6). Quest Q-D17 The Chalice of Protection (A3's hooks q-d17.voice, voice_wrong, voice_other, "
    "chalice, oath, oath_again, the seven book_* hooks through Xeen.vowelessBook, the thrones through "
    "Xeen.vowelessThrone); D-58's roof trapdoor one way up to D7 after m30.done (d7.roof_dd08). Class M: 20-45 "
    "sectors, 30-90 M units squared, levels 45-55, no boss, party 49-52, treasure 5, music 43. Graph "
    "devdocs/xeen/mockups/act5_graphs/dd08.graph.yml with decider D-61 (mockups/act5_a8_decisions.md, which wins): 45 "
    "knights (Slayer Knight 11150 45 x33, Death Knight 11151 55 x12; a Death Knight in the Doom Knight's place), "
    "31.14k per member, in A2's faction xeen_voweless_knights (hostile, friendly after the oath 113344); four Voweless "
    "Knight figures 11925 hidden in the chapter hall's niches, shown by the oath and on every later load; seven books "
    "(+1 to one statistic each, once per character, A3's player bits 11370-11376); the thrones (four lows, the "
    "Euphoria Throne 11377, the Dunce); the voice takes Chlc or aie. Rest encounters 10 %: dark knights Dif 0 [1, 2] "
    "w100 (D-61 Q31, A2's row 9157). Map qbits 117640, 117652-117656; map_stats 9157.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd08', 'name': 'Northern Tower', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-08', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [13, 10], 'climbs': 'n'},
        'map_stats': {
            'id': 9157, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 5, 'trap_dice': 8,
            'perception_difficulty': 15, 'refill_days': 672, 'music': 43, 'environment': 'stoneroom',
            'lock_difficulty': 15,
            # D-61 Q31: one slot, Dif 0 (A2's row 9157: Slayer Knights only, friendly after the oath)
            'slots': [{'monster': 'Xeen Dark Knight', 'tier': 0, 'per_marker': [1, 2], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d5_door', 'to': 'xeen_d5.odm', 'kind': 'door', 'arrival': D5_DOOR,
             'arrival_hint': "Before the Northern Tower's south door on D5, facing south away from it (A6's entrance:dd08_door, (2560, 11776, 3008) facing 1536).",
             'notes': "The tower's door (D5's door:dd08, q-d17.tower_door with Bosco's key) arrives at entrance:d5_tower in the gatehouse; out by the gate's exit preset ('Exit the Knight's Tower?', aaze0069:0, D-24)."},
            {'id': 'exit:d7_roof', 'to': 'xeen_d7.blv', 'kind': 'roof', 'arrival': D7_ROOF, 'one_way': True,
             'arrival_hint': "D7 The Skyroads, by the Northern Tower's hatch (A6's entrance:dd08_roof, (5632, 15104, 1158) facing 512).",
             'notes': "D-58: the ladder loft's roof trapdoor, one way up after m30.done ('Climb up through the trapdoor?', d7.roof_dd08); before it 'The trapdoor is shut fast.'. D7's hatch refuses from above."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


S, DK = SLAYER, DEATH
# space id: (name, kind, size, floor, purpose, population, treasure, extra, rooms)
SP = {
    # L1
    'porch': ("Porch", 'room', 'S', geo.L1, "Behind the gate's leaves: never entered (the gate's click is the exit).",
              [], [], {'empty': True}, ['porch']),
    'gatehouse': ("Gatehouse", 'room', 'S', geo.L1,
                  "The arrival (entrance:d5_tower): the gate's two leaves behind (hkm1dl/hkm1dr mirrored, the exit preset 'Exit the Knight's Tower?', aaze0069:0), an arch ahead into the Hall of Arms. Quiet (D-11.3); first arrival 117640.",
                  [], [], {'empty': True}, ['gatehouse']),
    'hall_of_arms': ("Hall of Arms", 'room', 'L', geo.L1,
                     "The founder's statue (its plaque 'In honor of the Grand Order of Voweless Knights', aaze0069:2); banners (xvkban) and two hung pieces on the south wall: one a find (a T5 shield, 117654). The core's south arch and the west gallery open off it.",
                     [placed(S, 3)], [], {}, ['hall']),
    'west_gallery': ("West gallery", 'corridor', 'M', geo.L1,
                     "West of the core: the dead mirror on its outer wall (xkmirror: 'Where to?' then 'The mirror does not respond.', aaze0069:3, :5); the lectern room's door.",
                     [], [], {'empty': True}, ['wgal']),
    'lectern_w0': ("West lectern room", 'room', 'S', geo.L1, "Dead end with a find: the first book on its lectern, 'Lt slpng dgs l' (aaze0069:8).",
                   [], [], {'empty': True}, ['lectern_w0']),
    'core0': ("Great stair", 'room', 'M', [geo.L1, geo.L2],
              "The central core: arches south (Hall of Arms), west and east (the galleries); the great stair up the middle to its head, the L2 landing (the graph's core1), with the armouries' doors west and east.",
              [], [], {'empty': True}, ['core']),
    'east_gallery': ("East gallery", 'corridor', 'M', geo.L1, "East of the core, to the refectory and the dormitory.",
                     [], [], {'empty': True}, ['egal']),
    'dormitory0': ("Dormitory", 'room', 'M', geo.L1,
                   "Dead end with a find: four beds (one with the note 'In life, to appreciate the highs one must experience the lows.', aaze0069:15, the thrones' answer-giver); the second book, 'H wh lghs lst, lghs bst' (aaze0069:11).",
                   [placed(S, 2)], [], {}, ['dormitory0']),
    'refectory': ("Refectory", 'room', 'M', geo.L1, "Long tables and benches, a silent reader's pulpit with no book; between the Hall of Arms and the east gallery.",
                  [placed(S, 3)], [], {}, ['refectory']),
    # L2
    'helms': ("West armoury", 'room', 'M', geo.L2, "Helms on pegs on the west wall: one a find (a T5 helm, 117655).",
              [placed(S, 3)], [], {}, ['helms']),
    'north_gallery1': ("North gallery", 'corridor', 'M', geo.L2, "Behind the core between the two armouries: arrow slits in the outer wall.",
                       [placed(S, 2), placed(DK, 1, 'heavy')], [], {}, ['north_gallery1']),
    'mail': ("East armoury", 'room', 'M', geo.L2, "Black plate on the east wall: one a find (a T5 cuirass, 117656).",
             [placed(S, 2), placed(DK, 1, 'heavy')], [], {}, ['mail']),
    'wstair1': ("West wall stair", 'room', 'S', [geo.L2, geo.L3],
                "The stair in the west wall's thickness from L2 up to L3 (the graph's wstair1 and wstair2): the third book on its landing, 'Th nds f th mny twgh th nds f th fw' (aaze0070:2); its head opens on the drill hall and the west study.",
                [], [], {'empty': True}, ['wstair']),
    'estair1': ("East wall stair", 'room', 'S', [geo.L2, geo.L3],
                "The east twin (the graph's estair1 and estair2): the fourth book on its landing, 'Lv f mny s th rt f ll vl' (aaze0070:5); on its head by the slit the seventh, 'F wshs wr hrss, bggrs wld rd' (aaze0071:7), and three knights.",
                [placed(S, 1), placed(DK, 2, 'heavy')], [], {}, ['estair']),
    'quartermaster': ("Quartermaster's store", 'room', 'S', geo.L2, "Dead end with a chest (the source's cabinet): crates and paired barrels by the walls.",
                      [placed(S, 2), placed(DK, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}, ['quartermaster']),
    # L3
    'west_study': ("West study", 'room', 'S', geo.L3,
                   "Dead end with a find: the fifth book, 'Dn't lk gft hrs n th mth' (aaze0071:2). A step plate before the west wall: the wall slides open with a grind onto the niche (117652).",
                   [], [], {'empty': True}, ['west_study']),
    'niche_w': ("West niche", 'room', 'S', geo.L3, "Dead end with a chest behind the sliding wall.",
                [], [{'kind': 'chest', 'count': 1, 'tier': 5}], {'empty': True}, ['niche_w']),
    'drill_w': ("Drill hall (west)", 'room', 'M', geo.L3, "The drill hall's west arm round the core.",
                [placed(S, 3)], [], {}, ['drill_w']),
    'drill_s': ("Drill yard (south)", 'room', 'L', geo.L3, "The widest arm: two groups at drill, arrow slits.",
                [placed(S, 3), placed(S, 2), placed(DK, 1, 'heavy')], [], {}, ['drill_s']),
    'core2': ("Stair of Silence", 'room', 'M', [geo.L3, geo.L4],
              "The core above the great stair's vault: arcades west and east onto the drill hall; the upper flight to its head, the L4 landing (the graph's core3): the chapter hall's two-leaf doors west (xdvowel over them inside), an arch east to the Hall of Thrones.",
              [], [], {'empty': True}, ['core2']),
    'drill_e': ("Drill hall (east)", 'room', 'M', geo.L3, "The east arm; the east stair head beyond it.",
                [placed(S, 2), placed(DK, 1, 'heavy')], [], {}, ['drill_e']),
    'east_study': ("East study", 'room', 'S', geo.L3,
                   "Dead end with a find: the sixth book, 'Fl nd hs mny r sn prtd' (aaze0071:5). A step plate before the east wall opens the east niche (117653).",
                   [], [], {'empty': True}, ['east_study']),
    'niche_e': ("East niche", 'room', 'S', geo.L3, "Dead end with a chest behind the sliding wall.",
                [], [{'kind': 'chest', 'count': 1, 'tier': 5}], {'empty': True}, ['niche_e']),
    # L4
    'chapter_hall': ("Chapter hall", 'room', 'L', geo.L4,
                     "The order's hall in dark stone under banners (xvkban): the plaque of the Grand Order on the north wall ('Swear the Voweless oath?', q-d17.oath; q-d17.oath_again after); four niches where four Voweless Knights (11925) stand hidden until the oath, and on every later load.",
                     [placed(S, 2), placed(DK, 1, 'heavy')], [], {'goal': True}, ['chapter_hall']),
    'antechamber': ("Antechamber of the voice", 'room', 'M', geo.L4,
                    "A bare stone room: the voice's mask (xvkmask) in the north wall, the chalice room's iron door beside it: aaze0072:2 and the prompt 'Wht d y sk?' (Chlc or aie: q-d17.voice; Chalice: voice_wrong; else voice_other). Quiet.",
                    [], [], {'empty': True}, ['antechamber']),
    'chalice_room': ("Chalice room", 'room', 'S', geo.L4, "Dead end with the goal: the Chalice of Protection on its stand (q-d17.chalice); 'An empty stand.' after.",
                     [], [], {'empty': True, 'goal': True}, ['chalice_room']),
    'thrones': ("Hall of Thrones", 'room', 'L', geo.L4,
                "Four Emotion Thrones round the raised Euphoria Throne (aaze0072:8-9, :21-25); a Death Knight stands in the Doom Knight's place (D-61 Q23).",
                [placed(DK, 2, 'heavy'), placed(S, 1)], [], {'set_piece': True}, ['thrones']),
    'dunce': ("Alcove of the Dunce", 'room', 'S', geo.L4, "The Throne of the Dunce alone (aaze0072:10, :12): 50 damage.",
              [], [], {'empty': True}, ['dunce']),
    'west_dorm': ("Knights' cells (west)", 'room', 'M', geo.L4,
                  "Dead end with a chest (the order's strongbox): three beds with the Cliff Notes, lessons 5-7 (aaze0072:18-20).",
                  [placed(S, 1), placed(DK, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}, ['west_dorm']),
    'east_dorm': ("Knights' cells (east)", 'room', 'M', geo.L4, "Four beds, Cliff Notes lessons 1-4 (aaze0072:14-17); the ladder loft north.",
                  [placed(S, 1), placed(DK, 1, 'heavy')], [], {}, ['east_dorm']),
    'roof_loft': ("Ladder loft", 'room', 'S', geo.L4,
                  "The roof trapdoor in the ceiling: d7.roof_dd08, 'Climb up through the trapdoor?' after m30.done, 'The trapdoor is shut fast.' before (D-58). Quiet.",
                  [], [], {'empty': True}, ['roof_loft']),
}

LINKS = [
    # L1
    ('link:gate', 'gatehouse', 'porch', 'double_door', {'purpose': "The gate (two leaves, hkm1dl|hkm1dr): clicked, 'Exit the Knight's Tower?'."}),
    ('link:gate_hall', 'gatehouse', 'hall_of_arms', 'open', {}),
    ('link:hall_core0', 'hall_of_arms', 'core0', 'open', {}),
    ('link:hall_wgal', 'hall_of_arms', 'west_gallery', 'open', {}),
    ('link:wgal_lect', 'west_gallery', 'lectern_w0', 'door', {}),
    ('link:wgal_core0', 'west_gallery', 'core0', 'open', {}),
    ('link:core0_egal', 'core0', 'east_gallery', 'open', {}),
    ('link:egal_dorm', 'east_gallery', 'dormitory0', 'open', {}),
    ('link:egal_refec', 'east_gallery', 'refectory', 'open', {}),
    ('link:refec_hall', 'refectory', 'hall_of_arms', 'door', {}),
    # L2 (off the great stair's head)
    ('link:core1_helms', 'core0', 'helms', 'door', {}),
    ('link:core1_mail', 'core0', 'mail', 'door', {}),
    ('link:helms_north', 'helms', 'north_gallery1', 'open', {}),
    ('link:north_mail', 'north_gallery1', 'mail', 'open', {}),
    ('link:helms_wstair', 'helms', 'wstair1', 'open', {}),
    ('link:mail_estair', 'mail', 'estair1', 'open', {}),
    ('link:mail_qm', 'mail', 'quartermaster', 'door', {}),
    # L3 (the wall stairs' heads)
    ('link:wstair_study', 'wstair1', 'west_study', 'door', {}),
    ('link:wstudy_niche', 'west_study', 'niche_w', 'secret_door', {'opened_by': 'poi:wall_w', 'purpose': "The sliding wall."}),
    ('link:wstair_drill', 'wstair1', 'drill_w', 'open', {}),
    ('link:drillw_core2', 'drill_w', 'core2', 'open', {}),
    ('link:drillw_s', 'drill_w', 'drill_s', 'open', {}),
    ('link:drills_e', 'drill_s', 'drill_e', 'open', {}),
    ('link:core2_drille', 'core2', 'drill_e', 'open', {}),
    ('link:drille_estair', 'drill_e', 'estair1', 'open', {}),
    ('link:estair_study', 'estair1', 'east_study', 'door', {}),
    ('link:estudy_niche', 'east_study', 'niche_e', 'secret_door', {'opened_by': 'poi:wall_e', 'purpose': "The sliding wall."}),
    # L4 (off the Stair of Silence's head)
    ('link:core3_chapter', 'core2', 'chapter_hall', 'double_door', {'purpose': "Two leaves (chb1dl|chb1dr)."}),
    ('link:chapter_ante', 'chapter_hall', 'antechamber', 'open', {}),
    ('link:ante_chalice', 'antechamber', 'chalice_room', 'door', {'opened_by': 'poi:voice', 'purpose': "The iron door: the voice's answer."}),
    ('link:ante_thrones', 'antechamber', 'thrones', 'open', {}),
    ('link:core3_thrones', 'core2', 'thrones', 'open', {}),
    ('link:thrones_dunce', 'thrones', 'dunce', 'open', {}),
    ('link:chapter_wdorm', 'chapter_hall', 'west_dorm', 'door', {}),
    ('link:thrones_edorm', 'thrones', 'east_dorm', 'door', {}),
    ('link:edorm_loft', 'east_dorm', 'roof_loft', 'open', {}),
]

PITCH = ("The Voweless Knights' tower in the Desert of Doom: four floors of green-grey Mok ashlar round a split stair "
         "core, books on lecterns that ask for proverbs with their vowels taken out, armouries and a drill hall full "
         "of black knights; at the top the order's dark sanctum, where a stone mask asks what you seek, the Chalice "
         "waits behind an iron door, and five thrones teach the highs and the lows.")
PURPOSE = ("Q-D17 The Chalice of Protection (QUESTS.md): climb to the voice and answer it the knights' way (Chlc or "
           "aie, q-d17.voice), take the Chalice (q-d17.chalice); the light route takes it to Bosco (DD-25), the dark "
           "route swears the oath at the chapter hall's plaque (q-d17.oath: the knights turn friendly, four come out "
           "of the walls). Seven books (+1 to one statistic each, once per character), the thrones (+1 to all after "
           "the four lows). After M30 the roof trapdoor leads one way up to D7 (D-58). Class M, party 49-52, monsters "
           "45-55, no boss.")
MOOD = ("Cold green-grey ashlar and scale-pattern flags (the Towers of Mok), grey cobbles in the core; at the top the "
        "knights' rooms in dark rough stone under black-and-red banners; silence, armour and books with no vowels.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, pop, tre, extra, rooms) in SP.items():
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': fl, 'purpose': purpose}
        if level != 'L1':
            xs, ys = [], []
            for r in rooms:
                x0, y0, x1, y1 = geo.bbox(r)
                xs += [x0, x1]
                ys += [y0, y1]
            s['extent'] = [max(xs) - min(xs), max(ys) - min(ys)]
            s['at'] = [(min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2]
            s['clear_height'] = geo.R[rooms[0]][3] - geo.R[rooms[0]][2]
            th = geo.R[rooms[0]][4]
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
            {'id': 'loop:ring_l1', 'spaces': ['room:hall_of_arms', 'room:west_gallery', 'room:core0', 'room:east_gallery', 'room:refectory'],
             'notes': "L1's ring round the core: the galleries pass through the core's west and east arches."},
            {'id': 'loop:ring_l2', 'spaces': ['room:core0', 'room:helms', 'room:north_gallery1', 'room:mail'],
             'notes': "L2: the two armouries joined by the great stair's head and the north gallery."},
            {'id': 'loop:wall_stairs', 'spaces': ['room:helms', 'room:wstair1', 'room:drill_w', 'room:core2', 'room:drill_e', 'room:estair1', 'room:mail', 'room:core0'],
             'notes': "Up one wall stair and down the other (the source's alternating stairs, D-61 Q29)."},
            {'id': 'loop:drill', 'spaces': ['room:drill_w', 'room:drill_s', 'room:drill_e', 'room:core2'],
             'notes': "The drill hall's three arms round the core."},
            {'id': 'loop:sanctum', 'spaces': ['room:core2', 'room:chapter_hall', 'room:antechamber', 'room:thrones'],
             'notes': "L4's ring: chapter hall, antechamber and Hall of Thrones round the Stair of Silence's head."},
        ],
        'entrances': [
            {'id': 'entrance:d5_tower', 'space': 'room:gatehouse', 'kind': 'both', 'neighbour': 'exit:d5_door', 'facing': 'n',
             'how': "D5's tower door (A6's door:dd08, q-d17.tower_door with Bosco's key) into the gatehouse, 256 inside the gate, facing north; out by the gate's exit preset to D5's entrance:dd08_door."},
        ],
        'critical_path': ['room:gatehouse', 'room:hall_of_arms', 'room:core0', 'room:helms', 'room:wstair1',
                          'room:drill_w', 'room:core2', 'room:chapter_hall', 'room:antechamber', 'room:chalice_room'],
        'return_path': ['room:chalice_room', 'room:antechamber', 'room:chapter_hall', 'room:core2', 'room:drill_e',
                        'room:estair1', 'room:mail', 'room:core0', 'room:hall_of_arms', 'room:gatehouse'],
        'goals': [
            {'id': 'goal:chalice', 'space': 'room:chalice_room', 'kind': 'take',
             'what': "The Chalice of Protection (12525, q-d17.chalice), behind the iron door the voice opens."},
            {'id': 'goal:oath', 'space': 'room:chapter_hall', 'kind': 'use',
             'what': "The dark route: the oath at the order's plaque (q-d17.oath)."},
        ],
        'keys': [
            {'id': 'key:voice', 'grants': {'qbit': 113342}, 'found_in': 'room:antechamber', 'how': 'lever',
             'notes': "The voice's answer (Chlc or aie): q-d17.voice; the iron door opens."},
            {'id': 'key:wall_w', 'grants': {'qbit': 117652}, 'found_in': 'room:west_study', 'how': 'lever',
             'notes': "The step plate before the west study's west wall: the wall slides open."},
            {'id': 'key:wall_e', 'grants': {'qbit': 117653}, 'found_in': 'room:east_study', 'how': 'lever',
             'notes': "The step plate before the east study's east wall."},
        ],
        'points_of_interest': [
            {'id': 'poi:voice', 'space': 'room:antechamber', 'kind': 'lever',
             'behaviour': "The mask: aaze0072:2, 'Wht d y sk?': Chlc or aie calls q-d17.voice (the iron door opens); Chalice q-d17.voice_wrong; else q-d17.voice_other (aaze0072:7)."},
            {'id': 'poi:wall_w', 'space': 'room:west_study', 'kind': 'lever', 'behaviour': "A step plate: the west wall slides open with a grind (117652)."},
            {'id': 'poi:wall_e', 'space': 'room:east_study', 'kind': 'lever', 'behaviour': "A step plate: the east wall slides open (117653)."},
            {'id': 'poi:books', 'space': 'room:lectern_w0', 'kind': 'sign', 'count': 7,
             'behaviour': "Seven lecterns (Xeen.vowelessBook): the proverb or its vowels gives +1 to one statistic to every member present, once per character; a wrong answer slams the book, and it may be tried again."},
            {'id': 'poi:thrones', 'space': 'room:thrones', 'kind': 'trap', 'count': 6,
             'behaviour': "Four Emotion Thrones (Weak, Drunk, Afraid, Insane), the Euphoria Throne after them (+1 to all seven, once per character), the Throne of the Dunce (50 damage)."},
            {'id': 'poi:oath', 'space': 'room:chapter_hall', 'kind': 'sign',
             'behaviour': "The plaque: 'Swear the Voweless oath?' (q-d17.oath, q-d17.oath_again); the four figures shown."},
            {'id': 'poi:chalice', 'space': 'room:chalice_room', 'kind': 'sign', 'behaviour': "The Chalice on its stand (q-d17.chalice)."},
            {'id': 'poi:mirror', 'space': 'room:west_gallery', 'kind': 'sign', 'behaviour': "The dead mirror: 'Where to?' then 'The mirror does not respond.' (aaze0069:3, :5)."},
            {'id': 'poi:statue', 'space': 'room:hall_of_arms', 'kind': 'sign', 'behaviour': "The founder's statue: 'A plaque reads: In honor of the Grand Order of Voweless Knights' (aaze0069:2)."},
            {'id': 'poi:finds', 'space': 'room:hall_of_arms', 'kind': 'sign', 'count': 3,
             'behaviour': "Three hung pieces taken once (117654-117656): a T5 shield, helm and cuirass; 'Nothing here.' after."},
            {'id': 'poi:notes', 'space': 'room:east_dorm', 'kind': 'sign', 'count': 8,
             'behaviour': "The pillow note (L1) and the seven Cliff Notes (L4's cells, aaze0072:14-20)."},
            {'id': 'poi:roof', 'space': 'room:roof_loft', 'kind': 'sign',
             'behaviour': "The roof trapdoor (d7.roof_dd08): shut before m30.done; after it 'Climb up through the trapdoor?' and up to D7."},
        ],
        'mechanisms': [
            {'kind': 'typed-answer book (player bits)', 'count': 7}, {'kind': 'typed-answer voice', 'count': 1},
            {'kind': 'condition throne', 'count': 6}, {'kind': 'sliding wall by a step plate', 'count': 2},
            {'kind': 'hidden peaceful figures shown by a qbit', 'count': 4}, {'kind': 'one-way exit by a trapdoor', 'count': 1},
        ],
        'totals': {'chests': 4, 'doors': 14, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act5_graphs/dd08.graph.yml; D-61 (mockups/act5_a8_decisions.md) wins where they differ: the books +1 to one statistic each (A3's player bits 11370-11376), the Euphoria Throne 11377, the voice also takes 'aie', the faction xeen_voweless_knights (friendly after the oath), four figures 11925, no Doom Knight (a Death Knight in his place), rest encounters at Dif 0. Changes from the graph (A8 L1): the stair rooms carry both floors (core0 with the graph's core1 as its head, core2 with core3, wstair1 with wstair2, estair1 with estair2); the porch behind the gate (the gate's click is the exit); the Dunce's alcove is a room of its own. Floors 448 apart: L1 0, L2 448, L3 896, L4 1344. All 45 monsters placed.",
    }


DIAGRAM = """L4 THE SANCTUM (1344)
                                  [CHALICE ROOM: the Chalice on its stand]
                                         |iron door (the voice)
  [W CELLS $: notes 5-7] =door= [CHAPTER HALL: plaque, 4 niches] -- [ANTECHAMBER: the mask] -- [HALL OF THRONES: 4 lows, Euphoria] =door= [E CELLS: notes 1-4] -- [LADDER LOFT: trapdoor up to D7]
                                         ||double                                    |   |
                                  [STAIR OF SILENCE head] ---------------------------+   [DUNCE'S ALCOVE]
L3 THE DRILL FLOOR (896)
  [W NICHE $]==sliding==[W STUDY: book 5]   [E STUDY: book 6]==sliding==[E NICHE $]
                     |door                         |door
  [W WALL STAIR head] -- [DRILL W] -- [STAIR OF SILENCE foot] -- [DRILL E] -- [E WALL STAIR head: book 7]
                          \\---------- [DRILL YARD S] ----------//
L2 THE ARMOURIES (448)
                     [NORTH GALLERY: slits]
                    /                      \\
  [W WALL STAIR: book 3] -- [W ARMOURY: helm find] =door= [GREAT STAIR head] =door= [E ARMOURY: plate find] -- [E WALL STAIR: book 4]
                                                                               |door
                                                                      [QUARTERMASTER $]
L1 THE GATE FLOOR (0)
  [W LECTERN: book 1]                       [DORMITORY: book 2, pillow note]
         |door                                    |
  [W GALLERY: mirror] -- [GREAT STAIR foot] -- [E GALLERY] -- [REFECTORY]
         |                     |                                   |door
  [HALL OF ARMS: statue, banners, shield find] --------------------+
         |
  [GATEHOUSE] ==gate== (exit to D5)
 $ chest   =door= door
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        rooms = []
        for r in geo.ORDER:
            doc = geo.room_doc(r)
            sp = next(s for s, v in SP.items() if r in v[8])
            if sp != r:
                doc['space'] = 'room:' + sp
            rooms.append(doc)
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:tower', 'ambient': 12},
            'rooms': rooms, 'openings': geo.OPENINGS,
            'notes': "DD-08 Northern Tower: L1 at 0, L2 at 448, L3 at 896, L4 at 1344, in one frame (x east, y north, z up). Written by output/studio_cal/dd08/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
