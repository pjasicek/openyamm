#!/usr/bin/env python3
"""DD-11B Troll Holes, second pocket: writes the L1-L4 project folders of devdocs/xeen/briefs/dd11b.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt, atmosphere.yml
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/dd11/cycle.sh dd11b); never hand-edit the written files.
Written by agent:xeen-a7-dd11 after DD-11A's gen.py; shared helpers in level_generation/projects/xeen/dd11/lib.py.

Frame: x east, y north, z up. The pit (where D2's second troll hole drops the party) is at the origin; the gnawed
gallery runs east to the clay drop, the expired adventurers' crawl lies off its north side behind a fallen root, the
fungus cave south of it, the burrow up west from the fungus cave. The vats (-448) lie under the gallery's east end:
the clay drop is a hole in the gallery's floor onto the vat rim, down only; the root stair is the way back up."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd11')
from lib import (R, S, DIRT, DIRTFLR, HIDE, STRAW, BARK, BONES, POLES, DAYLIGHT, WATER, SKY, THEMES, ROUGH, rect,  # noqa
                 octo, blob, nest, heap, write, chest, light, TROLL_LIGHT, DAY_LIGHT, map_stats, ATMOSPHERE)

BRIEF = R / 'devdocs/xeen/briefs/dd11b'
JUICE = {'texture': 'wtrtyl', 'liquid': 'water'}

themes = THEMES + [
    {'id': 'theme:roots', 'wall': DIRT, 'floor': BARK, 'ceiling': DIRT, 'door': HIDE, 'reveal': DIRT,
     'notes': "Root steps (xdbark, D2's bark) in the dirt: the root stair and the burrow up."},
]

rooms = []
openings = []


def room(id, name, **kw):
    d = {'id': id, 'name': name}
    d.update(kw)
    rooms.append(d)
    return d


def op(id, frm, to, **kw):
    d = {'id': id, 'from': frm, 'to': to}
    d.update(kw)
    openings.append(d)


HOLE = (2752, 0)   # the clay drop's hole in the gallery's floor, over the vat rim
VAT = (4352, -192)
# ------------------------------------------------------------------------------------------------ floor 0
room('room:pit', 'Pit bottom', outline=octo(0, 0, 384), floor=0, ceiling=448, theme='theme:dirt', ambient=30,
     rough=ROUGH,
     ceiling_levels=[{'outline': octo(0, 0, 224), 'ceiling': 768, 'edge': DIRT, 'surface': SKY,
                      'notes': "The troll hole's shaft, 768 up to D2's sky."}],
     platforms=[heap('platform:packs', [-170, 130], 130, 100,
                     "A heap of torn packs and a snapped rope: other people fell in here first.", rise=24,
                     surface=STRAW)],
     notes="Where the party lands, on a heap of torn packs and a snapped rope; daylight 768 up. The gnawed gallery runs east.")
room('room:gallery', 'Gnawed gallery', path=[[512, 0], [2944, 0]], width=320, floor=0, ceiling=320,
     theme='theme:dirt', ambient=18,
     notes="A long tunnel with tooth marks in the roots; at its far end the floor turns to wet clay and falls away to the vats below (the clay drop).")
room('room:adventurers', 'Expired adventurers', outline=rect(1024, 288, 1792, 1024), floor=0, ceiling=320,
     theme='theme:dirt', ambient=14, rough=ROUGH,
     platforms=[heap('platform:satchel', [1180, 900], 70, 50, "A thief's satchel among the bones.", rise=20,
                     surface=STRAW)],
     notes="Under a fallen root: the party that fell in before. Four skeletons in rusted mail, their strongbox, a thief's satchel.")
room('room:fungus', 'Fungus cave', outline=rect(512, -1792, 1408, -288), floor=0, ceiling=448,
     ceiling_points=[[960, -1040, 560]], theme='theme:dirt', ambient=18, rough=ROUGH,
     notes="Pale caps as tall as a man, the trolls' crop for the vats; the root stair comes up its east wall, the burrow leaves its west wall behind a hide flap.")
room('room:burrow', 'The burrow up', path=[[384, -1152], [-768, -1152]], width=224, floor=0, slope={'to': 384},
     ceiling=288, theme='theme:roots', ambient=22,
     notes="Root steps up a steep burrow to a sod hatch in the forest floor.")
# ------------------------------------------------------------------------------------------------ floor -448
room('room:vat_rim', 'Vat rim', outline=rect(2432, -640, 3456, 384), floor=-448, ceiling=-64,
     theme='theme:dirt', ambient=16, rough=ROUGH,
     platforms=[heap('platform:clay_heap', [2752, 0], 150, 120, "Wet clay from the slide, heaped where it lands.", rise=16,
                     surface=DIRT)],
     notes="Where the clay drop lands: a ledge of wet clay round the juice pit, the smell rising from it.")
room('room:vat_cave', 'Juice pit', outline=rect(3584, -1152, 5120, 768), floor=-448, ceiling=128,
     ceiling_points=[[VAT[0], VAT[1], 320]], theme='theme:dirt', ambient=16, rough=ROUGH,
     platforms=[{'id': 'platform:vat', 'outline': octo(VAT[0], VAT[1], 300), 'rise': 56, 'surface': DIRT,
                 'top_surface': JUICE,
                 'notes': "The sunken vat of fungus, grubs and water, brewing: Troll Juice (one drink a character)."}],
     notes="A sunken vat of fungus, grubs and water in the middle; ladles and skulls for cups; the brewers' log door in the east wall.")
room('room:brewers', "Brewers' den", outline=rect(5248, -512, 5888, 256), floor=-448, ceiling=-96,
     theme='theme:straw', ambient=14, rough=ROUGH,
     platforms=[nest('platform:brewer_bed', [5560, 120], 170, 90, "The brewers' straw.")],
     notes="Behind the log door: the brewers' beds and their stash.")
room('room:pens', 'Grub pens', outline=rect(2432, -1792, 3456, -768), floor=-448, ceiling=-64,
     theme='theme:dirt', ambient=16, rough=ROUGH,
     platforms=[
         {'id': 'platform:pen_1', 'at': [2800, -1640], 'size': [512, 192], 'rise': 48, 'surface': POLES,
          'top_surface': STRAW, 'notes': "A wicker pen of fat white grubs."},
         {'id': 'platform:pen_2', 'at': [3330, -1200], 'size': [192, 448], 'rise': 48, 'surface': POLES,
          'top_surface': STRAW, 'notes': "A wicker pen of grubs."},
     ],
     notes="Wicker pens of fat white grubs for the vats; the root stair leaves its west wall.")
room('room:stair', 'Root stair', outline=rect(1536, -1536, 2304, -1152), floor=-448,
     slope={'to': 0, 'toward': 'west', 'steps': 14}, ceiling=320, theme='theme:roots', ambient=16,
     notes="A stair of roots from the grub pens up to the fungus cave, 448.")
# ------------------------------------------------------------------------------------------------ openings
op('open:pit_gallery', 'room:pit', 'room:gallery', link='link:pit_gallery', width=256, height=288)
op('open:gallery_adv', 'room:gallery', 'room:adventurers', link='link:gallery_adv', width=192, height=256,
   notes="The crawl under the fallen root.")
op('open:clay_drop', 'room:gallery', 'room:vat_rim', link='link:gallery_slide', **{'in': 'floor'},
   at=list(HOLE), size=[256, 224], notes="The clay drop: the gallery's end falls away 448 to the vat rim; down only.")
op('open:gallery_fungus', 'room:gallery', 'room:fungus', link='link:fungus_gallery', width=288, height=288)
op('open:fungus_burrow', 'room:fungus', 'room:burrow', link='link:fungus_burrow', width=128, height=256,
   notes="The hide flap over the burrow's foot.")
op('open:rim_vat', 'room:vat_rim', 'room:vat_cave', link='link:rim_vat', width=512, height=320)
op('open:vat_brewers', 'room:vat_cave', 'room:brewers', link='link:vat_brewers', width=192, height=256,
   notes="The brewers' log door.")
op('open:rim_pens', 'room:vat_rim', 'room:pens', link='link:rim_pens', width=384, height=320)
op('open:pens_stair', 'room:pens', 'room:stair', link='link:pens_fungus', width=256, height=320)
op('open:stair_fungus', 'room:stair', 'room:fungus', link='link:pens_fungus', width=256, height=288)
rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:dirt', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "DD-11B Troll Holes, second pocket: floor 0 (the pocket) and -448 (the vats, partly under the gallery); x east, y north. Written by output/studio_cal/dd11b/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:pit': 0, 'room:gallery': 0, 'room:adventurers': 0, 'room:fungus': 0, 'room:burrow': 0,
          'room:vat_rim': -448, 'room:vat_cave': -448, 'room:brewers': -448, 'room:pens': -448, 'room:stair': -448}
TROLL, GUARD = 11690, 11691
PLAN_SPACES = [
    ('room:pit', 'Pit bottom', 'room', 'S', "Where the party lands, on torn packs and a snapped rope: others fell in here first. Daylight 768 up.", [], None),
    ('room:gallery', 'Gnawed gallery', 'corridor', 'M', "A long tunnel with tooth marks in the roots; its far end falls away to the vats.", [('a', 3)], None),
    ('room:adventurers', 'Expired adventurers', 'room', 'S', "Four skeletons in rusted mail, their strongbox, a thief's satchel with the guild's second letter.", [], 3),
    ('room:fungus', 'Fungus cave', 'room', 'M', "Pale caps as tall as a man; the root stair comes up here, the burrow starts here.", [('a', 3)], None),
    ('room:burrow', 'The burrow up', 'corridor', 'S', "Root steps up a steep burrow to a sod hatch on D2.", [], None),
    ('room:vat_rim', 'Vat rim', 'room', 'M', "Where the clay drop lands: a ledge round the juice pit.", [('a', 3)], None),
    ('room:vat_cave', 'Juice pit', 'room', 'L', "A sunken vat of fungus, grubs and water: Troll Juice, poisonous, but it improves you (one drink a character).", [('b', 5)], None),
    ('room:brewers', "Brewers' den", 'room', 'S', "Behind a log door: the brewers' beds and their stash.", [('b', 3)], 3),
    ('room:pens', 'Grub pens', 'room', 'M', "Wicker pens of fat white grubs for the vats.", [('a', 3)], None),
    ('room:stair', 'Root stair', 'corridor', 'S', "A stair of roots from the grub pens up to the fungus cave.", [], None),
]
LEVELS = {'a': [18, 18], 'b': [28, 28]}


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pop, ch in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if pop:
            s['population'] = [{'actor': TROLL if r == 'a' else GUARD, 'groups': n, 'levels': LEVELS[r],
                                'notes': f"{n} placed {'Trolls' if r == 'a' else 'Troll Guards'} (Xeen Warren Troll {r.upper()})."}
                               for r, n in pop]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:pit_gallery', 'from': 'room:pit', 'to': 'room:gallery', 'kind': 'open'},
        {'id': 'link:gallery_adv', 'from': 'room:gallery', 'to': 'room:adventurers', 'kind': 'door',
         'motion': 'swing', 'notes': "A fallen root across the crawl: it swings up when pushed (a hinged door)."},
        {'id': 'link:gallery_slide', 'from': 'room:gallery', 'to': 'room:vat_rim', 'kind': 'drop',
         'notes': "The clay drop, 448: down only. The way back is the root stair."},
        {'id': 'link:rim_vat', 'from': 'room:vat_rim', 'to': 'room:vat_cave', 'kind': 'open'},
        {'id': 'link:vat_brewers', 'from': 'room:vat_cave', 'to': 'room:brewers', 'kind': 'door',
         'motion': 'slide', 'notes': "The brewers' log door."},
        {'id': 'link:rim_pens', 'from': 'room:vat_rim', 'to': 'room:pens', 'kind': 'open'},
        {'id': 'link:pens_fungus', 'from': 'room:pens', 'to': 'room:fungus', 'kind': 'stairs',
         'notes': "By the root stair (its own room)."},
        {'id': 'link:fungus_gallery', 'from': 'room:fungus', 'to': 'room:gallery', 'kind': 'open'},
        {'id': 'link:fungus_burrow', 'from': 'room:fungus', 'to': 'room:burrow', 'kind': 'door', 'motion': 'slide',
         'notes': "A hide flap over the burrow's foot."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "The second pocket under D2's troll holes: the party lands on the packs of those who fell in before. Off the gnawed gallery lie the skeletons of that earlier party, with a thief's satchel and the guild's second letter, which names the King's hole. The gallery's end falls away to the trolls' vats, where a sunken vat of fungus and grubs brews Troll Juice: poisonous, but it improves you. The root stair climbs back to the fungus cave and the burrow up.",
        'purpose': "Q-D13 side pocket: Troll Juice (A3's q-d13.troll_juice text; the map gives +2 Endurance and Poisoned once a character, player bit 11294, D-25 Q8) and the second letter (ours, a paraphrase of aaze0040:6-7). Party 23 to 27; Trolls 18 and Troll Guards 28 (A2's Xeen Warren Troll rows 11690, 11691), 20 placed; treasure level 3.",
        'mood': "Wet clay and pale fungus, the sour reek of the vat; daylight only at the landing and the hatch.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:slide', 'spaces': ['room:gallery', 'room:vat_rim', 'room:pens', 'room:stair',
                                                  'room:fungus'],
                   'notes': "Down the clay drop, up the root stair: the drop is the only one-way link."}],
        'entrances': [
            {'id': 'entrance:d2_hole', 'space': 'room:pit', 'kind': 'arrival', 'facing': 'e',
             'how': "D2's second troll hole (thing:dd11b_hole, event 33, by the dead adventurer's pack): the party falls in and lands at the pit's bottom, facing the gallery (east)."},
            {'id': 'entrance:d2_burrow', 'space': 'room:burrow', 'kind': 'exit', 'neighbour': 'exit:d2_return',
             'how': "The burrow's sod hatch: out to D2 beside the second hole (A6's return point), the game's leave window."},
        ],
        'critical_path': ['room:pit', 'room:gallery', 'room:adventurers', 'room:gallery', 'room:vat_rim',
                          'room:vat_cave'],
        'return_path': ['room:vat_cave', 'room:vat_rim', 'room:pens', 'room:stair', 'room:fungus', 'room:burrow'],
        'goals': [{'id': 'goal:juice', 'space': 'room:vat_cave', 'kind': 'use', 'story': 'Q-D13',
                   'what': "Troll Juice: +2 Endurance (base) and Poisoned, once a character (player bit 11294)."},
                  {'id': 'goal:letter', 'space': 'room:adventurers', 'kind': 'use', 'story': 'Q-D13',
                   'what': "The guild's second letter in the thief's satchel: names the King's hole (DD-11C)."}],
        'set_pieces': [{'id': 'set:juice', 'kind': 'vista', 'spaces': ['room:vat_cave'],
                        'rule': "The juice pit: a sunken vat of fermenting fungus and grubs, trolls ladling it out round the rim."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(PLAN_SPACES), 'sectors': len(PLAN_SPACES), 'monsters_about': 20, 'chests': 2,
                   'doors': 3, 'loops': 1, 'floor_area_munits2': 10},
        'notes': "Size S (at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/dd11b.graph.yml and D-25 (Troll Juice +2 Endurance, the second letter kept as a paraphrase, the burrow's exit preset). The clay slide is a drop (a hole in the gallery's floor onto the vat rim, which lies under it).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-11B Troll Holes, second pocket (not to scale; plan, north up)

                           [EXPIRED ADVENTURERS: 4 skeletons, the second letter, T3]
                                   =fallen root=
   (D2: hole, fall in) v               |
   [PIT BOTTOM: start] -- [GNAWED GALLERY] ------------ (clay drop, 448, down only)
                              |                              v
   (D2) =exit= [BURROW UP] =hide flap= [FUNGUS CAVE]   -448 [VAT RIM] -- [JUICE PIT: Troll Juice] =log door= [BREWERS' DEN, T3]
                                          | root stair          |
                                          +----------------- [GRUB PENS]
"""

# ================================================================================================ objects.yml
objects = {
    'format': 0,
    'start': {'room': 'room:pit', 'at': [144, -208], 'facing': 'e',
              'notes': "Where D2's second troll hole drops the party: the pit's bottom beside the heap of packs, facing the gallery (east)."},
    'doors': [
        {'id': 'door:root', 'opening': 'open:gallery_adv', 'kind': 'hinged', 'hinge': 'left', 'swing': 90,
         'thickness': 24, 'speed': 90, 'surface': BARK,
         'notes': "A fallen root across the crawl; it swings up out of the way when pushed."},
        {'id': 'door:brewers', 'opening': 'open:vat_brewers', 'kind': 'slide_right', 'thickness': 24, 'speed': 160,
         'surface': BARK, 'tile': True, 'notes': "The brewers' door of lashed logs."},
        {'id': 'door:flap', 'opening': 'open:fungus_burrow', 'kind': 'slide_up', 'fold': True, 'thickness': 16,
         'speed': 192, 'surface': HIDE, 'tile': True, 'notes': "A hide flap over the burrow's foot."},
    ],
    'sounds': [
        {'id': 'sound:drip', 'room': 'room:pens', 'at': [2900, -1300], 'sound': 'drip01', 'radius': 1400,
         'inner_radius': 400, 'volume': 0.5, 'loop': False, 'wait': [3, 7], 'notes': "Water dripping on the pens."},
        {'id': 'sound:wind', 'room': 'room:pit', 'at': [0, 0], 'sound': 'whistling wind', 'radius': 1100,
         'inner_radius': 300, 'volume': 0.35, 'notes': "Wind over the hole far above."},
    ],
    'lights': [
        # Lamp rule (the user, 2026-11-20; lane A7 sixth session): every light's height is over the floor under it
        # and inside its room (lampcheck.py); the old negative heights put five lights under the floor.
        light('light:pit_day', 'room:pit', [0, 0], 700, 1100, DAY_LIGHT, notes="Daylight down the shaft."),
        light('light:gallery_w', 'room:gallery', [1100, 0], 280, 900, TROLL_LIGHT),
        light('light:gallery_e', 'room:gallery', [2300, 0], 280, 900, TROLL_LIGHT),
        light('light:adventurers', 'room:adventurers', [1408, 656], 280, 800, [140, 125, 110]),
        light('light:fungus', 'room:fungus', [960, -1040], 420, 1200, [150, 165, 140],
              notes="A pale light off the fungus caps."),
        light('light:burrow_top', 'room:burrow', [-640, -1152], 200, 900, DAY_LIGHT,
              notes="Daylight round the sod hatch."),
        light('light:rim', 'room:vat_rim', [2944, -128], 270, 1100, TROLL_LIGHT),
        light('light:vat', 'room:vat_cave', [VAT[0], VAT[1]], 60, 1600, [170, 160, 90],
              notes="A sickly glow off the brewing juice."),
        light('light:brewers', 'room:brewers', [5568, -128], 250, 800, TROLL_LIGHT),
        light('light:pens', 'room:pens', [2944, -1280], 270, 1100, [150, 140, 120]),
        light('light:stair', 'room:stair', [1920, -1344], 160, 800, [140, 120, 100]),
    ],
    'chests': [
        chest('chest:strongbox', 'room:adventurers', [1700, 930], 'w', 3, 350,
              "The fallen adventurers' strongbox."),
        chest('chest:brewers', 'room:brewers', [5800, -420], 'e', 3, 450, "The brewers' stash."),
    ],
    'monsters': [],
    'decorations': [],
    'exits': [
        {'id': 'exit:hatch', 'room': 'room:burrow', 'at': [-768, -1152], 'size': [192, 224], 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
         'to': 'exit:d2_return', 'notes': "The sod hatch at the burrow's top: daylight through the roots (D2)."},
    ],
}

PLACED = [
    ('room:gallery', 10, [(TROLL, [1000, 60], 180), (TROLL, [1700, -60], 180), (TROLL, [2250, 40], 180)]),
    ('room:fungus', 11, [(TROLL, [800, -1000], 90), (TROLL, [1150, -700], 90), (TROLL, [1100, -1500], 90)]),
    ('room:pens', 12, [(TROLL, [2700, -1100], 90), (TROLL, [3100, -1000], 90), (TROLL, [2650, -1450], 90)]),
    ('room:vat_rim', 13, [(TROLL, [2600, -450], 90), (TROLL, [3250, -450], 180), (TROLL, [3300, 250], 180)]),
    ('room:vat_cave', 14, [(GUARD, [3900, -750], 0), (GUARD, [4800, -750], 180), (GUARD, [3900, 400], 0),
                           (GUARD, [4800, 400], 180), (GUARD, [4352, 450], 270)]),
    ('room:brewers', 15, [(GUARD, [5450, -300], 180), (GUARD, [5700, -100], 180), (GUARD, [5600, -400], 180)]),
]
for room_id, group, ms in PLACED:
    key = room_id.split(':')[1]
    for n, (mon, at, facing) in enumerate(ms, 1):
        objects['monsters'].append({'id': f'monster:{key}_{n}', 'room': room_id, 'monster': mon, 'at': at,
                                    'facing': facing, 'group': group})

SKELETONS = [('skeleton_1', [1110, 380]), ('skeleton_2', [1110, 640]), ('skeleton_3', [1450, 867]),
             ('skeleton_4', [1700, 450])]
DECOS = [(k, 'room:adventurers', 'dec05', at) for k, at in SKELETONS] + [
    ('pit_bones', 'room:pit', 'dec29', [-250, -230]),
    ('pit_corpse', 'room:pit', 'Corpse01', [230, 250]),
    ('mush_1', 'room:fungus', 'mushrm01', [600, -400]),
    ('mush_2', 'room:fungus', 'mushrm02', [600, -1700]),
    ('mush_3', 'room:fungus', 'mushrm03', [1320, -1700]),
    ('mush_4', 'room:fungus', 'mushrm05', [1320, -380]),
    ('mush_6', 'room:fungus', 'mushrm01', [960, -1700]),
    # rim_skull (3370, -560) dropped (A7 s28): it stood 103 from the walking line between the rim's openings (MP42's
    # audit wants 116); the vat cave's skulls stay.
    ('vat_skull_1', 'room:vat_cave', '7dec20', [3680, -1060]),
    ('vat_skull_2', 'room:vat_cave', 'sklplrev', [5030, -1060]),
    ('vat_bones', 'room:vat_cave', 'dec29', [5030, 680]),
    ('vat_mush', 'room:vat_cave', 'mushrm03', [3680, 680]),
    ('brewers_bones', 'room:brewers', '7dec18', [5330, -430]),
    ('pens_bones', 'room:pens', 'dec29', [2520, -1700]),
]
for key, room_id, deco, at in DECOS:
    objects['decorations'].append({'id': f'deco:{key}', 'room': room_id, 'decoration': deco, 'at': at,
                                   'floor_height': FLOORS[room_id]})

# ================================================================================================ wiring.yml
LETTER = ("A message on thieves' guild letterhead reads: To all members: Troll holes located by the Forbidden Fruit "
          "hut, by the dead adventurer's pack, and the wide one near the rim. The wide one is the King's.")
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'text': "You land on a heap of torn packs and a snapped rope. Others fell in here before you.", 'seconds': 6,
     'notes': "The landing (a one-shot timer: the party arrives standing at the pit's bottom)."},
    {'id': 'evt:satchel', 'preset': 'text', 'source': 'platform:satchel', 'title': "Thief's satchel",
     'window': True, 'text': LETTER,
     'notes': "The guild's second letter (D-25: ours, a paraphrase of aaze0040:6-7, the source's grid squares become D2's three holes; A3's ORIGINAL_LINES row marks it). It names the King's hole (DD-11C)."},
    {'id': 'evt:gallery_end', 'preset': 'text', 'trigger': 'step', 'source': 'room:gallery', 'once': True,
     'text': "Tooth marks score the roots. Far ahead the floor turns to wet clay and falls away into the dark.",
     'seconds': 5},
    {'id': 'evt:landed', 'preset': 'text', 'trigger': 'step', 'source': 'room:vat_rim',
     'sources': ['platform:clay_heap'], 'once': True,
     'text': "You slide down the wet clay onto a ledge. There is no climbing back up that way.", 'seconds': 5},
    {'id': 'evt:vat_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:vat_cave', 'once': True,
     'text': "A sunken vat of fungus, grubs and water bubbles in the cave. Skulls lie about for cups.", 'seconds': 5},
    {'id': 'evt:juice', 'preset': 'script', 'source': 'platform:vat', 'title': 'Troll Juice',
     'condition': {'not': {'player_bit': 11294}},
     'effects': [{'lua': 'XeenQuests.hook("q-d13.troll_juice")'},
                 {'add': {'var': 'BaseEndurance', 'value': 2}},
                 {'set': {'var': 'PoisonedGreen', 'value': 1}},
                 {'player_bit': 11294}],
     'text': "+2 Endurance (permanent). You are poisoned.", 'seconds': 4,
     'else_effects': [{'lua': 'XeenQuests.hook("q-d13.troll_juice_again")'}],
     'notes': "goal:juice, D-25 Q8 (aaze0040:1-2, the source's +1 to all rescaled): A3's text hook; the map gives the drinking member +2 Endurance (base) and the weakest poison (PoisonedGreen) once, player bit 11294 (A3's q-d13.troll_juice); a member who has drunk gets troll_juice_again."},
    {'id': 'evt:root', 'preset': 'door', 'source': 'door:root', 'title': 'Fallen root', 'action': 'open',
     'text': "You heave the fallen root up out of the way.", 'seconds': 4},
    {'id': 'evt:brewers_door', 'preset': 'door', 'source': 'door:brewers', 'title': 'Log door'},
    {'id': 'evt:flap', 'preset': 'door', 'source': 'door:flap', 'title': 'Hide flap'},
    {'id': 'evt:chest_strongbox', 'preset': 'chest', 'source': 'chest:strongbox', 'title': 'Chest'},
    {'id': 'evt:chest_brewers', 'preset': 'chest', 'source': 'chest:brewers', 'title': 'Chest'},
    {'id': 'evt:hatch', 'preset': 'exit', 'source': 'exit:hatch', 'title': 'Sod hatch',
     'notes': "D-24/D-25: the burrow's top, the exit preset (the game's leave window, no 'Exit the Troll Hole?' question: aaze0040:12 stays in the ledger) to D2 beside the second hole (exit:d2_return, A6's return point)."},
]
for k, _ in SKELETONS:
    events.append({'id': f'evt:{k}', 'preset': 'text', 'source': f'deco:{k}', 'title': 'Expired Adventurer',
                   'text': "Nothing here.", 'notes': "aaze0040:3-4 (\"Expired Adventurer\" / \"Nothing here.\")."})
wiring = {'format': 0, 'events': events}

project = {
    'format': 0, 'id': 'xeen_dd11b', 'name': 'Troll Holes, second pocket', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon',
    'identity': {'shape': 'cave', 'family': 'd43', 'seen': ["a pit of earth and old bones under daylight from the troll hole", "the juice pit's vats in a broken-walled cave, the floor rising and falling round them", "grub pens and a fungus cave hung with earth"]},  # D-89 (A7 s28)
    'map_code': 'DD-11B', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [14, 8], 'climbs': 'n'},
    'map_stats': map_stats(9163),
    'neighbours': [
        {'id': 'exit:d2_return', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': [3072, -10240, 960],
         'direction': 180,
         'arrival_hint': "A6's return point for the second hole (D2 event 33, thing:dd11b_hole, by the dead adventurer's pack): on the forest floor about 300 from the pit's lip, facing west, clear of D2's troll spawns.",
         'notes': "The burrow's sod hatch out to D2 (D-25: one way in by the hole, one way out by the burrow)."},
    ],
    'notes': "Xeen design brief, level L4: DD-11B Troll Holes, second pocket, under D2 Sprite Forest (Q-D13 Hobstadt's Trolls). Monsters: A2's Troll Holes trolls, all placed: 12 Troll 11690 (18) and 8 Troll Guard 11691 (28) in groups 10-15 by room, hostile by the world's relations until Hobstadt's tribute or trial (113261/113262). Slot 1 Xeen Warren Troll for the map card, rest encounters 10 % (D-33: the warren trolls follow relations.yml, hostile before tribute, friendly after). Map qbits 110970-110979: none used; A3's player bit 11294 (troll_juice) read and set by number. Hooks q-d13.troll_juice and q-d13.troll_juice_again on the vat. Music 8. One way in (D2's second hole drops the party at the pit's bottom, the start) and one way out (the burrow's sod hatch, exit:d2_return, A6's point).",
}


if '--levels' in sys.argv:
    p = dict(project)
    for lv in ('L1', 'L2'):
        p['notes'] = f"Xeen design brief, level {lv}: DD-11B Troll Holes, second pocket (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-11B Troll Holes, second pocket: the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

CAVES = {  # D-89 cave shape (A7 s28): room -> cut, floor rise/fall, roof rise, stalactites
    'room:adventurers': {'cut': 192, 'floor': 48, 'roof': 128},
    'room:brewers': {'cut': 192, 'floor': 48, 'roof': 128},
    'room:fungus': {'cut': 256, 'floor': 64, 'stalactites': (3, 160)},
    'room:pens': {'cut': 256, 'floor': 64, 'roof': 160, 'step': 256},
    'room:pit': {'floor': 0},  # the party lands here: the floor stays level under the hole
    'room:vat_cave': {'cut': 384, 'floor': 64, 'stalactites': (4, 192), 'step': 256},
    'room:vat_rim': {'cut': 0, 'floor': 48, 'roof': 160},  # square: its skulls stand by the walking line
}
write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', ATMOSPHERE)])
from lib import shape_caves  # noqa
shape_caves(BRIEF / 'L4', CAVES)
print('written L4')
