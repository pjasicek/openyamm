#!/usr/bin/env python3
"""DD-11A Troll Holes, first pocket: writes the L1-L4 project folders of devdocs/xeen/briefs/dd11a.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt, atmosphere.yml
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (output/studio_cal/dd11a/cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-dd11 after XD-23's gen.py; shared helpers in level_generation/projects/xeen/dd11/lib.py.

Frame: x east, y north, z up. The pit (where D2's first troll hole drops the party) is at the origin; the root tunnel
runs east to the bone midden, the dead thief's crawl lies up the midden's bone slope in its north wall, the sleeping
hollow south of the tunnel, the burrow up west from the hollow. The lower warren (-384) lies south of the midden."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd11')
from lib import (R, S, DIRT, DIRTFLR, HIDE, STRAW, BARK, BONES, POLES, DAYLIGHT, WATER, SKY, THEMES, ROUGH, rect,  # noqa
                 octo, blob, nest, heap, write, chest, light, TROLL_LIGHT, DAY_LIGHT, map_stats, ATMOSPHERE)

BRIEF = R / 'devdocs/xeen/briefs/dd11a'
ROCK = S('t66cave', 128, 256)

themes = THEMES + [
    {'id': 'theme:bones', 'wall': DIRT, 'floor': BONES, 'ceiling': DIRT, 'door': HIDE, 'reveal': DIRT,
     'notes': "The bone slope down to the larder: gnawed bones underfoot (xobones)."},
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


# ------------------------------------------------------------------------------------------------ floor 0
room('room:pit', 'Pit bottom', outline=octo(0, 0, 384), floor=0, ceiling=448, theme='theme:dirt', ambient=30,
     rough=ROUGH,
     ceiling_levels=[{'outline': octo(0, 0, 224), 'ceiling': 768, 'edge': DIRT, 'surface': SKY,
                      'notes': "The troll hole's shaft, 768 up to D2's sky."}],
     platforms=[heap('platform:mound', [-170, 130], 130, 100,
                     "A mound of earth and old bones under the hole, where everything that falls in lands.",
                     rise=24)],
     notes="Where the party lands, under a shaft of daylight 768 up; its roots are too thin to climb. The root tunnel runs east.")
room('room:root_tunnel', 'Root tunnel', path=[[512, 0], [1792, 0]], width=320, floor=0, ceiling=320,
     theme='theme:dirt', ambient=20,
     notes="A tunnel dug under the forest, roots hanging from its roof; the sleeping hollow opens off its south side.")
room('room:midden', 'Bone midden', outline=rect(1920, -640, 3200, 640), floor=0, ceiling=480,
     ceiling_points=[[2560, 0, 640]], theme='theme:dirt', ambient=18, rough=ROUGH,
     platforms=[
         {'id': 'platform:bone_slope', 'at': [2656, 448], 'size': [320, 384], 'rise': 0,
          'top_slope': {'to': 192, 'toward': 'north'}, 'surface': BONES, 'top_surface': BONES,
          'notes': "Everything the trolls have eaten, heaped up the north wall: a slope of bones to the crawl's boulder."},
         heap(None, [2150, 420], 150, 110, "Gnawed bones, dented helms, a boot.", rise=40),
         heap(None, [3020, 380], 140, 120, "Gnawed bones.", rise=32),
         heap(None, [3050, -480], 120, 90, "Gnawed bones.", rise=24),
     ],
     notes="Everything the trolls have eaten, heaped up a slope against the north wall to the crawl; the bone slope down to the larder leaves the south wall.")
room('room:crawl', "Dead thief's crawl", outline=rect(2368, 768, 2944, 1216), floor=192, ceiling=448,
     theme='theme:dirt', ambient=14, rough=ROUGH,
     notes="A low crawl behind the boulder: a thief who crawled in to hide and never came out.")
room('room:hollow', 'Sleeping hollow', outline=rect(640, -1536, 1664, -288), floor=0, ceiling=384,
     ceiling_points=[[1152, -912, 480]], theme='theme:straw', ambient=16, rough=ROUGH,
     platforms=[
         nest('platform:nest_1', [880, -480], 140, 100, "A nest of straw and pulled-up bracken."),
         nest('platform:nest_2', [1440, -470], 140, 100, "A nest of straw and bracken."),
         nest('platform:nest_3', [1450, -1330], 140, 100, "A nest of straw and bracken."),
     ],
     notes="Nests of straw and pulled-up bracken; snoring. The burrow up leaves its west wall, the root stair comes up its south wall.")
room('room:burrow', 'The burrow up', path=[[512, -1088], [-768, -1088]], width=224, floor=0, slope={'to': 384},
     ceiling=288, theme='theme:roots', ambient=22,
     notes="The trolls' own way out: a steep burrow of packed earth and root steps up to a sod hatch in the forest floor.")
# ------------------------------------------------------------------------------------------------ floor -384
room('room:bone_slope', 'Bone slope', path=[[2560, -768], [2560, -2304]], width=256, floor=0, slope={'to': -384},
     ceiling=320, theme='theme:bones', ambient=16,
     notes="The midden's bones spill down a tunnel to the larder, 384 below.")
room('room:larder', 'Troll larder', outline=rect(2048, -3584, 3072, -2432), floor=-384, ceiling=0,
     theme='theme:dirt', ambient=16, rough=ROUGH,
     # Two single hides with dirt between (texture fit: a hide is a picture meant once, merge point 16).
     walls=[{'wall': 'south', 'panels': [{'id': 'panel:hides_s', 'offset': 288, 'length': 128, 'bottom': 64,
                                          'height': 256, 'surface': HIDE,
                                          'notes': "Hides and carcasses hung on root hooks."},
                                         {'id': 'panel:hides_s2', 'offset': 608, 'length': 128, 'bottom': 64,
                                          'height': 256, 'surface': HIDE,
                                          'notes': "A second hide on its root hook."}]}],
     notes="Carcasses on root hooks behind a wicker gate: deer, a wolf, something with too many legs.")
room('room:guard_den', 'Guard den', outline=rect(3200, -3456, 4032, -2560), floor=-384, ceiling=-32,
     theme='theme:straw', ambient=14, rough=ROUGH,
     platforms=[nest('platform:den_nest', [3620, -2780], 180, 110, "The guards' bedding.")],
     notes="The guards' den behind a log door; their pile of shiny things.")
room('room:seep', 'Dripping seep', outline=rect(1024, -3584, 1920, -2560), floor=-384, ceiling=0,
     ceiling_points=[[1472, -3072, 96]], theme='theme:dirt', ambient=16, rough=ROUGH,
     levels=[{'id': 'level:seep_pool', 'outline': octo(1400, -3200, 200, 170), 'floor': -432, 'edge': DIRT,
              'surface': WATER, 'notes': "The pool the trolls drink from."}],
     notes="Water seeps through the roof into a pool; the root stair climbs from its north wall to the sleeping hollow.")
room('room:root_stair', 'Root stair', outline=rect(1152, -2432, 1536, -1664), floor=-384,
     slope={'to': 0, 'toward': 'north', 'steps': 12}, ceiling=320, theme='theme:roots', ambient=16,
     notes="A stair of roots from the seep up to the sleeping hollow, 384.")
# ------------------------------------------------------------------------------------------------ openings
op('open:pit_tunnel', 'room:pit', 'room:root_tunnel', link='link:pit_tunnel', width=256, height=288)
op('open:tunnel_midden', 'room:root_tunnel', 'room:midden', link='link:tunnel_midden', width=288, height=288)
op('open:tunnel_hollow', 'room:root_tunnel', 'room:hollow', link='link:hollow_tunnel', width=256, height=288,
   along=0.35)
op('open:midden_crawl', 'room:midden', 'room:crawl', link='link:midden_crawl', width=192, height=224,
   notes="The crawl's mouth at the top of the bone slope, 192 up; the boulder rolls across it.")
op('open:midden_slope', 'room:midden', 'room:bone_slope', link='link:midden_larder', width=224, height=288)
op('open:slope_larder', 'room:bone_slope', 'room:larder', link='link:midden_larder', width=224, height=288)
op('open:larder_den', 'room:larder', 'room:guard_den', link='link:larder_den', width=192, height=256,
   notes="The guard den's log door.")
op('open:larder_seep', 'room:larder', 'room:seep', link='link:larder_seep', width=224, height=256,
   notes="The larder's wicker gate.")
op('open:seep_stair', 'room:seep', 'room:root_stair', link='link:seep_hollow', width=256, height=288)
op('open:stair_hollow', 'room:root_stair', 'room:hollow', link='link:seep_hollow', width=256, height=288)
op('open:hollow_burrow', 'room:hollow', 'room:burrow', link='link:hollow_burrow', width=192, height=256)
rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:dirt', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "DD-11A Troll Holes, first pocket: floor 0 (the pocket) and -384 (the lower warren); x east, y north. Written by output/studio_cal/dd11a/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:pit': 0, 'room:root_tunnel': 0, 'room:midden': 0, 'room:crawl': 192, 'room:hollow': 0,
          'room:burrow': 0, 'room:bone_slope': 0, 'room:larder': -384, 'room:guard_den': -384, 'room:seep': -384,
          'room:root_stair': -384}
TROLL, GUARD = 11690, 11691
PLAN_SPACES = [
    ('room:pit', 'Pit bottom', 'room', 'S', "Where the party lands: a mound of earth and old bones under a shaft of daylight 768 up; too sheer to climb.", [], None),
    ('room:root_tunnel', 'Root tunnel', 'corridor', 'M', "A tunnel dug under the forest, roots hanging from its roof; the first trolls come to see what fell in.", [('a', 3)], None),
    ('room:midden', 'Bone midden', 'room', 'M', "Everything the trolls have eaten, heaped up a slope to a crawl high in the wall; the bone slope down to the larder.", [('a', 3)], None),
    ('room:crawl', "Dead thief's crawl", 'room', 'S', "Behind a boulder: a thief who crawled in to hide and never came out. His pack and the guild's letter (Q-D13 starts).", [], 3),
    ('room:hollow', 'Sleeping hollow', 'room', 'M', "Nests of straw and bracken; snoring. The burrow up starts at its west wall.", [('a', 4)], None),
    ('room:burrow', 'The burrow up', 'corridor', 'S', "The trolls' own way out: root steps up a steep burrow to a sod hatch on D2.", [], None),
    ('room:bone_slope', 'Bone slope', 'corridor', 'S', "The midden's bones spill down to the larder.", [], None),
    ('room:larder', 'Troll larder', 'room', 'M', "Carcasses on root hooks behind a wicker gate; two guards keep the cooks off the meat.", [('a', 2), ('b', 2)], None),
    ('room:guard_den', 'Guard den', 'room', 'M', "The guards' den behind a log door; their pile of shiny things.", [('b', 3)], 3),
    ('room:seep', 'Dripping seep', 'room', 'M', "Water seeps through the roof into a pool the trolls drink from.", [('a', 2), ('b', 1)], None),
    ('room:root_stair', 'Root stair', 'corridor', 'S', "A stair of roots from the seep up to the sleeping hollow.", [], None),
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
        {'id': 'link:pit_tunnel', 'from': 'room:pit', 'to': 'room:root_tunnel', 'kind': 'open'},
        {'id': 'link:tunnel_midden', 'from': 'room:root_tunnel', 'to': 'room:midden', 'kind': 'open'},
        {'id': 'link:midden_crawl', 'from': 'room:midden', 'to': 'room:crawl', 'kind': 'door', 'motion': 'slide',
         'notes': "The boulder across the crawl's mouth at the top of the bone slope: it rolls aside when pushed (a door)."},
        {'id': 'link:midden_larder', 'from': 'room:midden', 'to': 'room:larder', 'kind': 'ramp',
         'notes': "By the bone slope (its own room)."},
        {'id': 'link:larder_den', 'from': 'room:larder', 'to': 'room:guard_den', 'kind': 'door', 'motion': 'slide',
         'notes': "The guard den's log door."},
        {'id': 'link:larder_seep', 'from': 'room:larder', 'to': 'room:seep', 'kind': 'door', 'motion': 'slide',
         'notes': "The larder's wicker gate."},
        {'id': 'link:seep_hollow', 'from': 'room:seep', 'to': 'room:hollow', 'kind': 'stairs',
         'notes': "By the root stair (its own room)."},
        {'id': 'link:hollow_tunnel', 'from': 'room:hollow', 'to': 'room:root_tunnel', 'kind': 'open'},
        {'id': 'link:hollow_burrow', 'from': 'room:hollow', 'to': 'room:burrow', 'kind': 'open'},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "The first of three pockets under D2's troll holes: the party falls in, lands on a mound of bones under the shaft, and finds a warren of trolls dug under the forest. Up a slope of everything the trolls have eaten lies a crawl behind a boulder, and in it a dead thief with the Thieves' Guild's letter: the trolls have stolen the guild's gold. The only way out is the trolls' own burrow, two rooms from the landing.",
        'purpose': "Q-D13 starts here: A3's hook q-d13.thieves_letter on the dead thief (started 113260, the autonote). Party 23 to 27; Trolls 18 and Troll Guards 28 (A2's Xeen Warren Troll rows 11690, 11691: friendly once Hobstadt has his tribute or trial), 20 placed; treasure level 3.",
        'mood': "Dirt and roots under the forest, a shaft of daylight at the landing, the smell of the larder; snoring from the hollow.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:warren', 'spaces': ['room:root_tunnel', 'room:midden', 'room:bone_slope', 'room:larder',
                                                   'room:seep', 'room:root_stair', 'room:hollow'],
                   'notes': "Down the bone slope, through the larder and the seep, up the root stair to the hollow."}],
        'entrances': [
            {'id': 'entrance:d2_hole', 'space': 'room:pit', 'kind': 'arrival', 'facing': 'e',
             'how': "D2's first troll hole (thing:dd11a_hole, event 32, 'Troll Hole. Descend?'): the party falls in and lands at the pit's bottom, facing the root tunnel (east). No way back up the shaft."},
            {'id': 'entrance:d2_burrow', 'space': 'room:burrow', 'kind': 'exit', 'neighbour': 'exit:d2_return',
             'how': "The burrow's sod hatch: out to D2 beside the first hole (A6's return point), the game's leave window."},
        ],
        'critical_path': ['room:pit', 'room:root_tunnel', 'room:midden', 'room:crawl'],
        'return_path': ['room:crawl', 'room:midden', 'room:root_tunnel', 'room:hollow', 'room:burrow'],
        'goals': [{'id': 'goal:letter', 'space': 'room:crawl', 'kind': 'use', 'story': 'Q-D13',
                   'what': "The dead thief's letter (A3's q-d13.thieves_letter: started, the autonote).",
                   'gives': {'qbit': 113260}}],
        'set_pieces': [{'id': 'set:midden', 'kind': 'vista', 'spaces': ['room:midden'],
                        'rule': "The bone midden: a slope of gnawed bones and adventurers' gear climbing to the dead thief's crawl high in the north wall."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(PLAN_SPACES), 'sectors': len(PLAN_SPACES), 'monsters_about': 20, 'chests': 2,
                   'doors': 3, 'loops': 1, 'floor_area_munits2': 8},
        'notes': "Size S (at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/dd11a.graph.yml and D-25 (mockups/act3_a7_decisions.md: the burrow's top is the exit preset, no question). The bone slope and the root stair are rooms of their own.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-11A Troll Holes, first pocket (not to scale; plan, north up)

                                      [DEAD THIEF'S CRAWL: letter, T3]  (192 up the bone slope)
                                              =boulder=
   (D2: hole, fall in) v                         |
   [PIT BOTTOM: start] -- [ROOT TUNNEL] -- [BONE MIDDEN]
                              |                  | bone slope (0 -> -384)
   (D2) =exit= [BURROW UP] -- [SLEEPING HOLLOW]  |
                                   | root stair  |
                          -384  [DRIPPING SEEP] =wicker= [TROLL LARDER] =log door= [GUARD DEN, T3]
"""

# ================================================================================================ objects.yml
objects = {
    'format': 0,
    'start': {'room': 'room:pit', 'at': [80, -208], 'facing': 'e',
              'notes': "Where D2's first troll hole drops the party: the pit's bottom beside the bone mound, facing the root tunnel (east); out of the tunnel trolls' sight (F45, 2026-11-24; was [96, -32])."},
    'doors': [
        {'id': 'door:boulder', 'opening': 'open:midden_crawl', 'kind': 'slide_left', 'thickness': 32, 'speed': 96,
         'surface': ROCK, 'tile': True,
         'notes': "A boulder the trolls rolled across the crawl's mouth; it rolls aside when pushed."},
        {'id': 'door:wicker', 'opening': 'open:larder_seep', 'kind': 'slide_up', 'thickness': 16, 'speed': 192,
         'surface': POLES, 'tile': True, 'notes': "The larder's wicker gate."},
        {'id': 'door:den', 'opening': 'open:larder_den', 'kind': 'slide_right', 'thickness': 24, 'speed': 160,
         'surface': BARK, 'tile': True, 'notes': "The guard den's door of lashed logs."},
    ],
    'floors': [{'id': 'floor:seep_pool', 'of': 'level:seep_pool', 'kind': 'water',
                'notes': "The seep's pool (wtrtyl, the fluid bit)."}],
    'sounds': [
        {'id': 'sound:drip', 'room': 'room:seep', 'at': [1400, -3200], 'sound': 'drip01', 'radius': 1400,
         'inner_radius': 400, 'volume': 0.6, 'loop': False, 'wait': [2, 6], 'notes': "Water dripping into the pool."},
        {'id': 'sound:wind', 'room': 'room:pit', 'at': [0, 0], 'sound': 'whistling wind', 'radius': 1100,
         'inner_radius': 300, 'volume': 0.35, 'notes': "Wind over the hole far above."},
    ],
    'lights': [
        # Lamp rule (the user, 2026-11-20; lane A7 sixth session): every light's height is over the floor under it
        # and inside its room (lampcheck.py); the old negative heights put five lights under the floor.
        light('light:pit_day', 'room:pit', [0, 0], 700, 1100, DAY_LIGHT, notes="Daylight down the shaft."),
        light('light:tunnel', 'room:root_tunnel', [1150, 0], 280, 900, TROLL_LIGHT),
        light('light:midden', 'room:midden', [2560, 0], 440, 1300, [150, 130, 105]),
        light('light:crawl', 'room:crawl', [2656, 1000], 180, 700, [140, 120, 100]),
        light('light:hollow', 'room:hollow', [1152, -912], 340, 1100, TROLL_LIGHT),
        light('light:burrow_top', 'room:burrow', [-640, -1088], 200, 900, DAY_LIGHT,
              notes="Daylight round the sod hatch."),
        light('light:slope', 'room:bone_slope', [2560, -1536], 100, 800, [140, 120, 100]),
        light('light:larder', 'room:larder', [2560, -3008], 270, 1100, [150, 145, 160]),
        light('light:den', 'room:guard_den', [3616, -3008], 250, 900, TROLL_LIGHT),
        light('light:seep', 'room:seep', [1472, -3072], 360, 1000, [140, 155, 175]),
        light('light:stair', 'room:root_stair', [1344, -2048], 160, 800, [140, 120, 100]),
    ],
    'chests': [
        chest('chest:thief_pack', 'room:crawl', [2870, 1110], 'w', 3, 300,
              "The dead thief's pack: what he had not spent before he crawled in here."),
        chest('chest:den_hoard', 'room:guard_den', [3950, -3360], None, 3, 450,
              "The guards' pile of shiny things."),
    ],
    'monsters': [],
    'decorations': [],
    'exits': [
        {'id': 'exit:hatch', 'room': 'room:burrow', 'at': [-768, -1088], 'size': [192, 224], 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
         'to': 'exit:d2_return', 'notes': "The sod hatch at the burrow's top: daylight through the roots (D2)."},
    ],
}

PLACED = [
    ('room:root_tunnel', 10, [(TROLL, [1100, 60], 180), (TROLL, [1400, -60], 180), (TROLL, [1650, 40], 180)]),
    ('room:midden', 11, [(TROLL, [2250, -300], 180), (TROLL, [2900, -350], 180), (TROLL, [2350, 150], 180)]),
    ('room:hollow', 12, [(TROLL, [900, -1250], 90), (TROLL, [1350, -1050], 90), (TROLL, [900, -750], 90),
                         (TROLL, [1350, -700], 90)]),
    ('room:seep', 13, [(TROLL, [1250, -2800], 90), (TROLL, [1750, -3400], 90), (GUARD, [1700, -2800], 0)]),
    ('room:larder', 14, [(TROLL, [2300, -2700], 270), (TROLL, [2800, -2700], 270), (GUARD, [2300, -3250], 0),
                         (GUARD, [2800, -3250], 180)]),
    ('room:guard_den', 15, [(GUARD, [3450, -3000], 180), (GUARD, [3750, -3200], 180), (GUARD, [3700, -2850], 180)]),
]
for room_id, group, ms in PLACED:
    key = room_id.split(':')[1]
    for n, (mon, at, facing) in enumerate(ms, 1):
        objects['monsters'].append({'id': f'monster:{key}_{n}', 'room': room_id, 'monster': mon, 'at': at,
                                    'facing': facing, 'group': group})

# Decorations against the walls (D-7: nothing on a walking line). deco:thief and deco:expired are clicked.
DECOS = [
    ('thief', 'room:crawl', 'Corpse05', [2470, 1120]),
    ('expired', 'room:midden', 'dec05', [3110, 0]),
    ('pit_bones', 'room:pit', 'dec29', [-250, -230]),
    ('pit_skull', 'room:pit', '7dec20', [230, 250]),
    ('midden_skulls', 'room:midden', 'sklplrev', [2080, -490]),
    ('midden_bones', 'room:midden', '7dec18', [2010, -330]),
    ('midden_skull', 'room:midden', '7dec20', [3110, -250]),
    ('crawl_bones', 'room:crawl', 'dec29', [2450, 830]),
    ('hollow_bones', 'room:hollow', '7dec18', [720, -1460]),
    ('hollow_skull', 'room:hollow', '7dec20', [1590, -900]),
    ('larder_carcass_1', 'room:larder', 'Corpse02', [2150, -3500]),
    ('larder_carcass_2', 'room:larder', 'Corpse03', [2980, -3500]),
    ('larder_bones', 'room:larder', 'dec29', [2140, -2520]),
    ('den_skulls', 'room:guard_den', 'sklplrev', [3290, -3370]),
    ('den_bones', 'room:guard_den', '7dec18', [3950, -2650]),
    ('seep_mite', 'room:seep', 'stlmite1', [1110, -2650]),
    ('seep_mite_2', 'room:seep', 'stlmite2', [1840, -3500]),
    ('seep_bones', 'room:seep', 'dec29', [1840, -2650]),
]
for key, room_id, deco, at in DECOS:
    objects['decorations'].append({'id': f'deco:{key}', 'room': room_id, 'decoration': deco, 'at': at,
                                   'floor_height': FLOORS[room_id]})

# ================================================================================================ wiring.yml
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'text': "You land on a mound of earth and old bones. Daylight is far above, and the pit's walls are too sheer to climb.",
     'seconds': 6, 'notes': "The landing (a one-shot timer: the party arrives standing at the pit's bottom)."},
    {'id': 'evt:thief', 'preset': 'script', 'source': 'deco:thief', 'title': 'Dead thief',
     'lua': 'XeenQuests.hook("q-d13.thieves_letter")',
     'notes': "goal:letter: A3's q-d13.thieves_letter (started 113260, the autonote; aaze0040:5's letter; its else_text after)."},
    {'id': 'evt:expired', 'preset': 'text', 'source': 'deco:expired', 'title': 'Expired Adventurer',
     'text': "Nothing here.", 'notes': "aaze0040:3-4 (\"Expired Adventurer\" / \"Nothing here.\"): one who fell in before."},
    {'id': 'evt:midden_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:midden', 'once': True,
     'text': "Bones, dented helms, a single boot: everything the trolls have eaten, heaped up the wall.", 'seconds': 5},
    {'id': 'evt:larder_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:larder', 'once': True,
     'text': "Carcasses hang from root hooks: a deer, a wolf, and something with too many legs.", 'seconds': 5},
    {'id': 'evt:boulder', 'preset': 'door', 'source': 'door:boulder', 'title': 'Boulder', 'action': 'open',
     'text': "You put your shoulders to the boulder, and it rolls aside.", 'seconds': 4},
    {'id': 'evt:wicker', 'preset': 'door', 'source': 'door:wicker', 'title': 'Wicker gate'},
    {'id': 'evt:den_door', 'preset': 'door', 'source': 'door:den', 'title': 'Log door'},
    {'id': 'evt:chest_thief', 'preset': 'chest', 'source': 'chest:thief_pack', 'title': 'Bag'},
    {'id': 'evt:chest_den', 'preset': 'chest', 'source': 'chest:den_hoard', 'title': 'Chest'},
    {'id': 'evt:hatch', 'preset': 'exit', 'source': 'exit:hatch', 'title': 'Sod hatch',
     'notes': "D-24/D-25: the burrow's top, the exit preset (the game's leave window, no 'Exit the Troll Hole?' question: aaze0040:12 stays in the ledger) to D2 beside the first hole (exit:d2_return, A6's return point)."},
]
wiring = {'format': 0, 'events': events}

project = {
    'format': 0, 'id': 'xeen_dd11a', 'name': 'Troll Holes, first pocket', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon',
    'identity': {'shape': 'cave', 'family': 'd43', 'seen': ["a pit of earth and old bones under daylight from the troll hole", "burrows of red-brown dirt with broken outlines, floors that rise and fall and low vaulted roofs", "the bone midden and the dead thief in his crawl"]},  # D-89 (A7 s28)
    'map_code': 'DD-11A', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [10, 10], 'climbs': 'n'},
    'map_stats': map_stats(9162),
    'neighbours': [
        {'id': 'exit:d2_return', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': [-2048, -6144, 992],
         'direction': 180,
         'arrival_hint': "A6's return point for the first hole (D2 event 32, thing:dd11a_hole): on the forest floor about 300 from the pit's lip, facing west, clear of D2's troll spawns.",
         'notes': "The burrow's sod hatch out to D2 (D-25: one way in by the hole, one way out by the burrow)."},
    ],
    'notes': "Xeen design brief, level L4: DD-11A Troll Holes, first pocket, under D2 Sprite Forest (Q-D13 Hobstadt's Trolls). Monsters: A2's Troll Holes trolls, all placed: 14 Troll 11690 (18) and 6 Troll Guard 11691 (28) in groups 10-15 by room, hostile by the world's relations until Hobstadt's tribute or trial (113261/113262). Slot 1 Xeen Warren Troll for the map card, rest encounters 10 % (D-33: the warren trolls follow relations.yml, hostile before tribute, friendly after). Map qbits 110960-110969: none used. Hook q-d13.thieves_letter on the dead thief. Music 8. One way in (D2's first hole drops the party at the pit's bottom, the start) and one way out (the burrow's sod hatch, exit:d2_return, A6's point).",
}


if '--levels' in sys.argv:
    p = dict(project)
    for lv in ('L1', 'L2'):
        p['notes'] = f"Xeen design brief, level {lv}: DD-11A Troll Holes, first pocket (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-11A Troll Holes, first pocket: the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

CAVES = {  # D-89 cave shape (A7 s28): room -> cut, floor rise/fall, roof rise, stalactites
    'room:crawl': {'cut': 128, 'floor': 32, 'roof': 96},
    'room:guard_den': {'cut': 192, 'floor': 48, 'roof': 128},
    'room:hollow': {'cut': 256, 'floor': 64},
    'room:larder': {'floor': 64, 'roof': 160},
    'room:midden': {'cut': 320, 'floor': 80, 'stalactites': (3, 160)},
    'room:pit': {'floor': 0},  # the party lands here: the floor stays level under the hole
    'room:root_tunnel': {'path_rough': True},  # s29: the tunnel out of the pit, rough walls (it read as a box)
    'room:seep': {'cut': 256, 'floor': 48},
}
write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', ATMOSPHERE)])
from lib import shape_caves  # noqa
shape_caves(BRIEF / 'L4', CAVES)
print('written L4')
