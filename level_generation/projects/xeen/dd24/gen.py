#!/usr/bin/env python3
"""DD-24 Giants' Hall: writes the L1-L4 project folders of devdocs/xeen/briefs/dd24 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, atmosphere.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here; never hand-edit the written files (diff L4 against L4/.oymap/last first).
Written by the lane lead of A7 (thirteenth session, 2026-11-21) after DD-16's gen.py, on D-47 (act5_a7_decisions.md).

Frame: x east, y north, z up. Gurodel's hall in the hillside behind his hold on D5, built for giants (about 300 tall):
the great doors open north off a porch in the hillside (the way out, south) into the threshold; the longhall (floor 0)
leads north to the Great Stair, which climbs 1,024 to the landing, the throne hall under its smoke hole and the hoard
behind it. The little ones' crack (128 x 256, too low for a giant) climbs from the boulder store to the trophy gallery.
Rooms stand 128 apart (the walls' thickness)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/dd24'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM8 Cyclops Larder (d14, D-47 Q24): gcav1wal brown cave rock, gcst1bs1 sandstone blocks in the throne hall, gcst2flr
# and gston1fl floors, gkp1ceil planks and gcst2cel ceilings, gcstdoor single doors; two new textures (Codex,
# level_generation/textures_xeen/a7_dd24_giant/): xdgiantd (one wing of the giant double doors, mirrored on the
# right leaf) and xdthrone (the bloody throne's black wood).
ROCK = S('gcav1wal', 256, 256)
BLOCK = S('gcst1bs1', 128, 256)
FLOOR = S('gcst2flr', 128, 128, scale=2)
FLAGS = S('gston1fl', 128, 128, scale=2)
PLANKS = S('gkp1ceil', 128, 128, scale=2)
CEIL = S('gcst2cel', 128, 128, scale=2)
DOOR1 = S('gcstdoor', 128, 256, fit=True)
WING = S('xdgiantd', 128, 256)
THRONE = S('xdthrone', 128, 128, scale=2)
TRIM = S('trim9_32', 32, 64)
DAYLIGHT = S('xddaylt', 256, 128, fit=True)
SKY = S('gcav1wal', 256, 256, sky=True)
TABLE = S('gkp1ceil', 128, 128)
FURS = S('t1beds1', 256, 32)

themes = [
    {'id': 'theme:cave', 'wall': ROCK, 'floor': FLOOR, 'ceiling': ROCK, 'reveal': ROCK, 'door': DOOR1,
     'notes': "The People's halls cut in the hillside: MM8 Cyclops Larder's brown cave rock, its worn stone floor."},
    {'id': 'theme:hall', 'wall': ROCK, 'floor': FLAGS, 'ceiling': PLANKS, 'reveal': BLOCK, 'door': DOOR1,
     'notes': "The longhall and the landing: the same rock, flagged floors, plank roofs on beams."},
    {'id': 'theme:throne', 'wall': BLOCK, 'floor': FLAGS, 'ceiling': PLANKS, 'reveal': BLOCK, 'door': DOOR1,
     'notes': "The throne hall and the hoard: walls of great sandstone blocks."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


UP = 1024
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


def panel(pid, offset, length, bottom, height, surface, **kw):
    d = {'id': pid, 'offset': offset, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ floor 0
room('room:porch', 'Porch', outline=rect(-384, -640, 384, -128), floor=0, ceiling=640, theme='theme:cave',
     ambient=20, notes="The mouth in the hillside behind Gurodel's hold: the way out to D5 south, the great doors north.")
room('room:threshold', 'Threshold', outline=rect(-512, 0, 512, 768), floor=0, ceiling=768, theme='theme:cave',
     ambient=16, notes="Inside the great doors: a porch of rough rock 768 high. The arrival from D5.")
room('room:longhall', 'Longhall', outline=rect(-1024, 896, 1024, 1920), floor=0, ceiling=1024, theme='theme:hall',
     platforms=[
         {'id': 'platform:trench', 'at': [0, 1408], 'size': [640, 96], 'rise': 24, 'surface': ROCK,
          'top_surface': S('gcst2cel', 128, 128), 'notes': "The fire trench's stone kerb, its embers."},
         {'id': 'platform:table_w', 'at': [-704, 1408], 'size': [160, 768], 'rise': 192, 'surface': TABLE,
          'top_surface': TABLE, 'notes': "A table of whole split trunks."},
         {'id': 'platform:table_e', 'at': [704, 1408], 'size': [160, 768], 'rise': 192, 'surface': TABLE,
          'top_surface': TABLE, 'notes': "A table of whole split trunks."},
         {'id': 'platform:law_stone', 'at': [-960, 1792], 'size': [64, 192], 'rise': 352, 'surface': BLOCK,
          'top_surface': BLOCK, 'notes': "The People's law stone (q-d16.law_stone)."},
     ],
     ambient=16, notes="The feast hall, 2,048 by 1,024 and 1,024 high: two tables of whole trunks, the fire trench between them, the law stone in the north-west corner. The Great Stair rises from its north end.")
room('room:larder', 'Larder', outline=rect(-1792, 1024, -1152, 1664), floor=0, ceiling=640, theme='theme:cave',
     store=True, ambient=14, notes="A dead end: haunches on hooks, casks and the larder chest.")
room('room:sleeping', 'Sleeping hall', outline=rect(1152, 896, 2176, 1664), floor=0, ceiling=768, theme='theme:cave',
     platforms=[{'id': f'platform:furs_{i}', 'at': [x, 1560], 'size': [320, 160], 'rise': 32, 'surface': ROCK,
                 'top_surface': FURS, 'notes': "A heap of furs, a giant's bed."} for i, x in enumerate((1408, 1920), 1)]
     + [{'id': 'platform:hearth', 'at': [2080, 1152], 'size': [128, 256], 'rise': 24, 'surface': ROCK,
         'top_surface': S('gcst2cel', 128, 128), 'notes': "The sleeping hall's hearth."}],
     ambient=14, notes="Heaps of furs along the north wall, a hearth by the east wall.")
room('room:boulder_store', 'Boulder store', outline=rect(1152, 1792, 1792, 2432), floor=0, ceiling=640,
     theme='theme:cave', ambient=12,
     notes="The throwing rocks piled by the walls; in the east wall the low crack, the little ones' way up.")
CRACK = [[1920, 2112, 0], [2432, 2112, 149], [2432, 4480, 838], [1792, 4480, UP]]
room('room:crack', "The little ones' crack", path=CRACK, width=128, floor=0, ceiling=256, theme='theme:cave',
     ambient=10, notes="A natural crack 128 wide and 256 high climbing 1,024 to the trophy gallery: too low for a giant (about 300 tall, D-47 Q26).")
room('room:great_stair', 'The Great Stair', outline=rect(-320, 2048, 320, 4096), floor=0,
     slope={'to': UP, 'toward': 'north', 'steps': 26}, ceiling=1024, ceiling_slope={'to': UP + 1024, 'toward': 'north'},
     theme='theme:hall', ambient=14, notes="A straight flight 640 wide rising 1,024 north in 26 steps under 1,024 of headroom: 'The People will be waiting on the stair.'")

# ------------------------------------------------------------------------------------------------ floor 1 (1,024)
room('room:landing', 'Upper landing', outline=rect(-512, 4224, 896, 4864), floor=UP, ceiling=UP + 896,
     theme='theme:hall', ambient=14, notes="The stair head before the throne hall's double doors; the trophy gallery opens east.")
room('room:trophies', 'Trophy gallery', outline=rect(1024, 4224, 1664, 5888), floor=UP, ceiling=UP + 896,
     theme='theme:cave', ambient=14,
     notes="Skulls and bones of great beasts on the walls; the crack comes out in its east wall; a side door into the throne hall.")
HOLE = [[-192, 5888], [192, 5888], [192, 6144], [-192, 6144]]
room('room:throne_hall', 'The bloody throne', outline=rect(-768, 4992, 896, 6272), floor=UP, ceiling=UP + 1024,
     theme='theme:throne',
     ceiling_levels=[{'outline': [[-256, 5568], [256, 5568], [256, 5824], [-256, 5824]], 'ceiling': UP + 1408,
                      'edge': ROCK, 'surface': SKY,
                      'notes': "The smoke hole: a shaft 384 high whose top is open to the Darkside's sky (1,408 above the floor)."}],
     platforms=[{'id': 'platform:throne', 'at': [0, 6016], 'size': [448, 256], 'rise': 160, 'surface': THRONE,
                 'top_surface': THRONE, 'notes': "The bloody throne: a seat of black wood big enough for four."},
                {'id': 'platform:throne_back', 'at': [0, 6200], 'size': [448, 64], 'rise': 512, 'surface': THRONE,
                 'top_surface': THRONE, 'notes': "The throne's back."},
                {'id': 'platform:brazier_w', 'at': [-512, 5952], 'size': [96, 96], 'rise': 96, 'surface': BLOCK,
                 'top_surface': S('gcst2cel', 128, 128), 'notes': "A brazier's stone."},
                {'id': 'platform:brazier_e', 'at': [512, 5952], 'size': [96, 96], 'rise': 96, 'surface': BLOCK,
                 'top_surface': S('gcst2cel', 128, 128), 'notes': "A brazier's stone."}],
     ambient=18, notes="1,664 by 1,280 under a plank roof 1,024 high with a smoke hole before the throne: the bloody throne at the north wall, braziers either side; the hoard's door in the north-west corner.")
room('room:treasury', "Gurodel's hoard", outline=rect(-768, 6400, -256, 6912), floor=UP, ceiling=UP + 640,
     theme='theme:throne', ambient=12, notes="Behind the throne hall: the People's hoard chest.")

PAIR = {'pictures': [[WING, dict(WING, mirror=True)]], 'back_pictures': [[WING, dict(WING, mirror=True)]]}
op('open:great', 'room:porch', 'room:threshold', link='link:porch_threshold', width=384, height=512)
op('open:thr_long', 'room:threshold', 'room:longhall', link='link:thr_long', width=512, height=640)
op('open:long_larder', 'room:longhall', 'room:larder', link='link:long_larder', width=256, height=448)
op('open:long_sleep', 'room:longhall', 'room:sleeping', link='link:long_sleep', width=384, height=640)
op('open:sleep_boulder', 'room:sleeping', 'room:boulder_store', link='link:sleep_boulder', width=384, height=512)
op('open:boulder_crack', 'room:boulder_store', 'room:crack', link='link:boulder_crack', width='full', height=256,
   notes="The low crack: 128 wide, 256 high.")
op('open:long_stair', 'room:longhall', 'room:great_stair', link='link:long_stair', width='full', height=768)
op('open:stair_landing', 'room:great_stair', 'room:landing', link='link:stair_landing', width='full', height=768)
op('open:landing_throne', 'room:landing', 'room:throne_hall', link='link:landing_throne', width=384, height=512)
op('open:landing_trophies', 'room:landing', 'room:trophies', link='link:landing_trophies', width=384, height=640)
op('open:crack_trophies', 'room:crack', 'room:trophies', link='link:crack_trophies', width='full', height=256)
op('open:trophies_throne', 'room:trophies', 'room:throne_hall', link='link:throne_trophies', width=256, height=448)
op('open:throne_treasury', 'room:throne_hall', 'room:treasury', link='link:throne_treasury', width=256, height=448)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:cave', 'ambient': 14}, 'rooms': rooms,
             'openings': openings,
             'notes': "DD-24 Giants' Hall: x east, y north; the porch and great doors south (D5), the longhall (floor 0), the Great Stair north to the throne floor (1,024). Written by output/studio_cal/dd24/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:porch': 0, 'room:threshold': 0, 'room:longhall': 0, 'room:larder': 0, 'room:sleeping': 0,
          'room:boulder_store': 0, 'room:crack': 0, 'room:great_stair': 0, 'room:landing': UP,
          'room:trophies': UP, 'room:throne_hall': UP, 'room:treasury': UP}
C, G, E = 11083, 11084, 11085
PLACED = [  # room, group, [(row, at, facing)]
    ('longhall', 10, [(C, (-200, 1050), 90), (C, (500, 1800), 270), (C, (-500, 1800), 270),
                      (G, (250, 1050), 90), (G, (-500, 1150), 90), (G, (200, 1620), 180), (G, (-200, 1650), 0)]),
    ('larder', 11, [(C, (-1420, 1200), 90), (C, (-1450, 1450), 0)]),
    ('sleeping', 12, [(C, (1700, 1050), 90), (G, (1400, 1100), 90), (G, (1900, 1350), 180),
                      (G, (1650, 1350), 270), (G, (1300, 1350), 0)]),
    ('boulder_store', 13, [(C, (1350, 2100), 0), (C, (1600, 2250), 180)]),
    ('great_stair', 14, [(G, (-150, 3300), 270), (G, (150, 3600), 270), (C, (0, 2800), 270)]),
    ('landing', 15, [(G, (-250, 4550), 270), (G, (300, 4550), 270)]),
    ('trophies', 16, [(E, (1344, 5400), 270), (G, (1250, 4700), 180), (G, (1450, 5000), 180)]),
    ('throne_hall', 17, [(E, (-300, 5750), 270), (E, (300, 5750), 270), (G, (-500, 5300), 270),
                         (G, (500, 5300), 270), (G, (0, 5200), 270)]),
    ('treasury', 18, [(E, (-600, 6550), 270)]),
]
NAMES = {C: 'Cyclops', G: 'Giant', E: 'Elder Giant'}
LEVELS = {C: 38, G: 50, E: 58}
PLAN_SPACES = [
    ('room:porch', 'Porch', 'room', 'S', "The mouth in the hillside behind Gurodel's hold: the way out to D5, the great doors."),
    ('room:threshold', 'Threshold', 'room', 'M', "The arrival (entrance:d5_hold), inside the great doors (a hinged pair, 384 x 512). Quiet. At war, once: the People's challenge (q-d16.war_threshold)."),
    ('room:longhall', 'Longhall', 'room', 'L', "The feast hall: tables of whole trunks, the fire trench, the law stone (q-d16.law_stone). The hub."),
    ('room:larder', 'Larder', 'room', 'M', "A dead end with the larder chest (opens at peace)."),
    ('room:sleeping', 'Sleeping hall', 'room', 'M', "Heaps of furs, a hearth; the off-watch."),
    ('room:boulder_store', 'Boulder store', 'room', 'S', "The throwing rocks; the low crack in its east wall."),
    ('room:crack', "The little ones' crack", 'corridor', 'S', "128 x 256, climbing 1,024 to the trophy gallery: too low for giants (D-47 Q26)."),
    ('room:great_stair', 'The Great Stair', 'corridor', 'L', "640 wide, 26 steps up 1,024: 'The People will be waiting on the stair.'"),
    ('room:landing', 'Upper landing', 'room', 'M', "The stair head before the throne hall's double doors."),
    ('room:trophies', 'Trophy gallery', 'corridor', 'M', "Beasts' skulls and bones; the crack comes out here; a side door into the throne hall."),
    ('room:throne_hall', 'The bloody throne', 'room', 'L', "The bloody throne under a smoke hole (q-d16.throne): at war two Energy Disks and 14,000; at peace it refuses."),
    ('room:treasury', "Gurodel's hoard", 'room', 'S', "The hoard chest: refuses at peace (q-d16.hoard)."),
]


def plan_doc(level):
    pops = {}
    for rid, _, ms in PLACED:
        for mon, _, _ in ms:
            pops.setdefault(f'room:{rid}', {}).setdefault(mon, 0)
            pops[f'room:{rid}'][mon] += 1
    spaces = []
    for sid, name, kind, size, purpose in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if sid in pops:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [n, n], 'levels': [LEVELS[m], LEVELS[m]],
                                'notes': f"{n} {NAMES[m]} {LEVELS[m]} (placed, the People)."}
                               for m, n in pops[sid].items()]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:porch_threshold', 'from': 'room:porch', 'to': 'room:threshold', 'kind': 'double_door'},
        {'id': 'link:thr_long', 'from': 'room:threshold', 'to': 'room:longhall', 'kind': 'open'},
        {'id': 'link:long_larder', 'from': 'room:longhall', 'to': 'room:larder', 'kind': 'door'},
        {'id': 'link:long_sleep', 'from': 'room:longhall', 'to': 'room:sleeping', 'kind': 'open'},
        {'id': 'link:sleep_boulder', 'from': 'room:sleeping', 'to': 'room:boulder_store', 'kind': 'open'},
        {'id': 'link:boulder_crack', 'from': 'room:boulder_store', 'to': 'room:crack', 'kind': 'open'},
        {'id': 'link:crack_trophies', 'from': 'room:crack', 'to': 'room:trophies', 'kind': 'ramp'},
        {'id': 'link:long_stair', 'from': 'room:longhall', 'to': 'room:great_stair', 'kind': 'open'},
        {'id': 'link:stair_landing', 'from': 'room:great_stair', 'to': 'room:landing', 'kind': 'stairs'},
        {'id': 'link:landing_throne', 'from': 'room:landing', 'to': 'room:throne_hall', 'kind': 'double_door'},
        {'id': 'link:landing_trophies', 'from': 'room:landing', 'to': 'room:trophies', 'kind': 'open'},
        {'id': 'link:throne_trophies', 'from': 'room:trophies', 'to': 'room:throne_hall', 'kind': 'door'},
        {'id': 'link:throne_treasury', 'from': 'room:throne_hall', 'to': 'room:treasury', 'kind': 'door'},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "The People's hall in the hillside behind Gurodel's hold: a feast hall of whole-trunk tables and a fire trench, a stair built for giants, and at its top the bloody throne under a smoke hole. At peace the giants let the little ones walk through; at war 'the People will be waiting on the stair'.",
        'purpose': "Q-D16 Gurodel's Giants, the war route: the bloody throne's two Energy Disks (q-d16.throne). Party 45 to 47, the People 38/50/58 (30 placed, D-47 Q23), treasure 5.",
        'mood': "Big: doors twice a man's height, steps a giant's stride, a roof lost in smoke; the smell of meat and fur.",
        'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:crack', 'spaces': ['room:longhall', 'room:sleeping', 'room:boulder_store', 'room:crack',
                                                 'room:trophies', 'room:landing', 'room:great_stair'],
                   'notes': "Up the Great Stair or up the little ones' crack."},
                  {'id': 'loop:throne', 'spaces': ['room:landing', 'room:throne_hall', 'room:trophies'],
                   'notes': "Into the throne hall by its double doors or the gallery's side door."}],
        'entrances': [{'id': 'entrance:d5_hold', 'space': 'room:threshold', 'kind': 'both', 'facing': 'n',
                       'how': "From D5's great doors behind Gurodel's hold (A6): 384 inside the leaves, facing north into the hall."}],
        'critical_path': ['room:threshold', 'room:longhall', 'room:great_stair', 'room:landing', 'room:throne_hall'],
        'return_path': ['room:throne_hall', 'room:trophies', 'room:crack', 'room:boulder_store', 'room:sleeping',
                        'room:longhall', 'room:threshold'],
        'goals': [{'id': 'goal:throne', 'space': 'room:throne_hall', 'kind': 'use', 'story': 'Q-D16',
                   'what': "The bloody throne (q-d16.throne): at war two Energy Disks and 14,000, once, only without friends."}],
        'set_pieces': [{'id': 'set:throne', 'kind': 'scripted', 'spaces': ['room:throne_hall'],
                        'rule': "The bloody throne under the smoke hole (open sky, D-42's sun stage): refuses at peace; the People's war turns the hall."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 12, 'sectors': 12, 'monsters_about': 30, 'chests': 2, 'doors': 5, 'loops': 2,
                   'floor_area_munits2': 14},
        'notes': "Size S (at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From act5_graphs/dd24.graph.yml and D-47 (DD-24, Q22-Q26); the porch outside the great doors is its own room (the way out).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-24 Giants' Hall (not to scale; plan, north up)
  floor 1024   [HOARD]   [THE BLOODY THRONE: smoke hole]--door--[TROPHY GALLERY]
                                  || double doors                   |   ^ the crack comes out
                         [UPPER LANDING]------------------------------  |
                                  ^ the Great Stair (26 steps)          |
  floor 0      [LARDER]--door--[LONGHALL: tables, trench, law stone]--[SLEEPING HALL]
                                  |                                     |
                             [THRESHOLD]                           [BOULDER STORE]--crack 128x256 (climbs 1,024)
                                  || great doors (pair)
                             [PORCH] =exit= (D5, entrance:dd24_hold)
"""

# ================================================================================================ objects
ARRIVAL = [0, 384]
objects = {'format': 0}
objects['start'] = {'room': 'room:threshold', 'at': ARRIVAL, 'facing': 'n',
                    'notes': "entrance:d5_hold: 384 inside the great doors, facing north into the hall."}
objects['arrivals'] = [{'entrance': 'entrance:d5_hold', 'room': 'room:threshold', 'at': ARRIVAL, 'facing': 'n',
                        'notes': "384 inside the great doors, facing north (D5's great doors, A6)."}]
objects['doors'] = [
    dict({'id': 'door:great', 'opening': 'open:great', 'kind': 'hinged', 'leaves': 2, 'thickness': 32, 'speed': 45,
          'edge_surface': TRIM, 'notes': "The great doors: two leaves of giant planks (xdgiantd, the right leaf mirrored)."},
         **PAIR),
    dict({'id': 'door:throne', 'opening': 'open:landing_throne', 'kind': 'hinged', 'leaves': 2, 'thickness': 32,
          'speed': 45, 'edge_surface': TRIM, 'notes': "The throne hall's double doors."}, **PAIR),
    {'id': 'door:larder', 'opening': 'open:long_larder', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR1,
     'back_surface': DOOR1, 'edge_surface': TRIM, 'notes': "The larder's plank door."},
    {'id': 'door:side', 'opening': 'open:trophies_throne', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR1,
     'back_surface': DOOR1, 'edge_surface': TRIM, 'notes': "The trophy gallery's side door into the throne hall."},
    {'id': 'door:hoard', 'opening': 'open:throne_treasury', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR1,
     'back_surface': DOOR1, 'edge_surface': TRIM, 'notes': "The hoard's door."},
]
objects['chests'] = [
    {'id': 'chest:larder', 'room': 'room:larder', 'at': [-1700, 1560], 'treasure_level': 5,
     'random_items': 2, 'gold': 2000, 'notes': "The larder's meat chest (opens at peace)."},
    {'id': 'chest:hoard', 'room': 'room:treasury', 'at': [-512, 6820], 'treasure_level': 5,
     'random_items': 4, 'gold': 5000, 'notes': "The People's hoard (q-d16.hoard: refuses at peace)."},
]
objects['monsters'] = []
for rid, group, ms in PLACED:
    for n, (mon, at, facing) in enumerate(ms, 1):
        objects['monsters'].append({'id': f'monster:{rid}_{n}', 'room': f'room:{rid}', 'monster': mon, 'at': list(at),
                                    'facing': facing, 'hostile': False, 'group': group})


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [235, 160, 90]
DAY = [124, 118, 106]
objects['lights'] = [
    light('light:porch', 'room:porch', [0, -300], 300, 900, DAY, notes="The Darkside's day from the hillside's mouth."),
    light('light:trench', 'room:longhall', [0, 1408], 120, 1500, FIRE, brightness=26,
          pulse={'intensity': [0.7, 1.0], 'frequency': 0.6}, notes="The fire trench's embers."),
    light('light:hearth', 'room:sleeping', [2080, 1152], 100, 900, FIRE, brightness=22,
          pulse={'intensity': [0.7, 1.0], 'frequency': 0.5}),
    light('light:smoke_hole', 'room:throne_hall', [0, 5696], 1300, 1600, DAY, notes="Daylight down the smoke hole."),
    light('light:brazier_w', 'room:throne_hall', [-512, 5952], 200, 900, FIRE, brightness=22,
          pulse={'intensity': [0.7, 1.0], 'frequency': 0.7}),
    light('light:brazier_e', 'room:throne_hall', [512, 5952], 200, 900, FIRE, brightness=22,
          pulse={'intensity': [0.7, 1.0], 'frequency': 0.8}),
]
# Torches on the walls (12 out from the wall, as DD-06's), lit lamps beside them.
TORCHES = [('threshold', (-500, 400)), ('threshold', (500, 400)), ('larder', (-1780, 1180)),
           ('boulder_store', (1164, 2100)), ('great_stair', (-308, 2600)), ('great_stair', (308, 3500)),
           ('landing', (-500, 4544)), ('trophies', (1036, 5600)), ('treasury', (-268, 6656)),
           ('sleeping', (1700, 908)), ('longhall', (-1012, 1100)), ('longhall', (1012, 1700))]
objects['decorations'] = []
for i, (rid, at) in enumerate(TORCHES, 1):
    objects['decorations'].append({'id': f'deco:torch_{i:02d}', 'room': f'room:{rid}', 'decoration': 'torch01',
                                   'at': list(at), 'height': 224})
    objects['lights'].append(light(f'light:torch_{i:02d}', f'room:{rid}', list(at), 256, 800, FIRE))
objects['decorations'] += [
    {'id': 'deco:trench_fire_1', 'room': 'room:longhall', 'decoration': 'ckfyr00', 'at': [-160, 1408], 'floor_height': 24},
    {'id': 'deco:trench_fire_2', 'room': 'room:longhall', 'decoration': 'ckfyr00', 'at': [160, 1408], 'floor_height': 24},
    {'id': 'deco:hearth_fire', 'room': 'room:sleeping', 'decoration': 'ckfyr00', 'at': [2080, 1152], 'floor_height': 24},
    {'id': 'deco:brazier_w', 'room': 'room:throne_hall', 'decoration': 'ckfyr00', 'at': [-512, 5952], 'floor_height': UP + 96},
    {'id': 'deco:brazier_e', 'room': 'room:throne_hall', 'decoration': 'ckfyr00', 'at': [512, 5952], 'floor_height': UP + 96},
    {'id': 'deco:cask_1', 'room': 'room:larder', 'decoration': 'bigbarel', 'at': [-1700, 1100]},
    {'id': 'deco:cask_2', 'room': 'room:larder', 'decoration': 'bigbarel', 'at': [-1600, 1100]},
    {'id': 'deco:cask_3', 'room': 'room:larder', 'decoration': 'smlbarel', 'at': [-1700, 1200]},
    {'id': 'deco:sack_1', 'room': 'room:larder', 'decoration': 'floursac', 'at': [-1740, 1300]},
    {'id': 'deco:sack_2', 'room': 'room:larder', 'decoration': 'bag01', 'at': [-1740, 1400]},
    {'id': 'deco:bones_1', 'room': 'room:longhall', 'decoration': 'dec29', 'at': [-950, 960]},
    {'id': 'deco:bones_2', 'room': 'room:trophies', 'decoration': '7dec18', 'at': [1600, 5800], 'floor_height': UP},
    {'id': 'deco:skulls_1', 'room': 'room:trophies', 'decoration': 'sklplrev', 'at': [1600, 5500], 'floor_height': UP},
    {'id': 'deco:skulls_2', 'room': 'room:trophies', 'decoration': 'sklplrev', 'at': [1600, 4900], 'floor_height': UP},
    {'id': 'deco:rock_1', 'room': 'room:boulder_store', 'decoration': '6rock02', 'at': [1250, 2350]},
    {'id': 'deco:rock_2', 'room': 'room:boulder_store', 'decoration': '6rock02', 'at': [1250, 1900]},
]
objects['exits'] = [
    {'id': 'exit:mouth', 'room': 'room:porch', 'wall': 's', 'size': [512, 256], 'surface': S('7solid01', 256, 128, fit=True),
     'to': 'exit:d5_hold', 'notes': "The hillside's mouth onto D5 behind Gurodel's hold."},
]
objects['sounds'] = [
    {'id': 'sound:trench', 'room': 'room:longhall', 'at': [0, 1408], 'sound': 'campfire', 'radius': 1600,
     'inner_radius': 400, 'volume': 0.6, 'notes': "The fire trench."},
    {'id': 'sound:smoke_hole', 'room': 'room:throne_hall', 'at': [0, 5696], 'sound': 'whistling wind', 'radius': 1800,
     'inner_radius': 500, 'volume': 0.4, 'notes': "Wind down the smoke hole."},
]

# ================================================================================================ wiring
QB = {'friends': 113320, 'war': 113321, 'throne_searched': 113322, 'hall_attacked': 113323, 'war_announced': 113324,
      'd12_hostile': 113242, 'd12_camp_burned': 113244}
AT_WAR = {'any': [{'qbit': 'war'}, {'qbit': 'hall_attacked'}, {'qbit': 'd12_hostile'}, {'qbit': 'd12_camp_burned'}]}


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


N_ACTORS = sum(len(ms) for _, _, ms in PLACED)
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 7,
     'text': "The People's hall. Everything is twice too big: the doors, the steps, the smell of meat and smoke."},
    {'id': 'evt:way_out', 'preset': 'exit', 'source': 'exit:mouth', 'title': "Leave the Giants' Hall",
     'notes': "Out to D5 (installed, A6) at its named arrival entrance:dd24_hold (11264, 10752, 2688) facing south "
              "(1536), before the great doors behind Gurodel's hold: the game's own leave window (D-24)."},
    {'id': 'evt:door_great', 'preset': 'door', 'source': 'door:great', 'title': 'Great doors'},
    {'id': 'evt:door_throne', 'preset': 'door', 'source': 'door:throne', 'title': 'Doors'},
    {'id': 'evt:door_larder', 'preset': 'door', 'source': 'door:larder', 'title': 'Door'},
    {'id': 'evt:door_side', 'preset': 'door', 'source': 'door:side', 'title': 'Door'},
    {'id': 'evt:door_hoard', 'preset': 'door', 'source': 'door:hoard', 'title': 'Door'},
    {'id': 'evt:war_line', 'preset': 'script', 'trigger': 'step', 'source': 'room:threshold',
     'condition': AT_WAR, 'effects': [hook('q-d16.war_threshold')],
     'notes': "At war the People's challenge (dark/aaze0013:33), once per war: A3's q-d16.war_threshold decides (war_announced 113324)."},
    {'id': 'evt:war_arrival', 'preset': 'script', 'trigger': 'load', 'condition': AT_WAR,
     'effects': [{'set': {'var': {'map_var': 'war_arrived'}, 'value': 1}}],
     'notes': "The arrival (0, 384) stands inside room:threshold, so evt:war_line's step does not run on the way in "
              "(A3's q-d16 scenario, 2026-11-21), and a message from a load event is lost with the map's loading: "
              "entering at war marks war_arrived, and evt:war_arrival_say shows the People's challenge a moment later."},
    {'id': 'evt:war_arrival_say', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'map_var': 'war_arrived'},
     'effects': [{'set': {'var': {'map_var': 'war_arrived'}, 'value': 0}},
                 {'lua': 'local x, y = evt.GetPartyPosition()\n'
                         'if x >= -512 and x <= 512 and y >= 0 and y <= 768 then\n'
                         '    XeenQuests.hook("q-d16.war_threshold")\n'
                         'end'}],
     'notes': "The first tick after a map load at war, if the party stands in room:threshold (the arrival from D5; a "
              "save loaded elsewhere in the hall shows nothing): A3's q-d16.war_threshold (once per war by "
              "war_announced 113324)."},
    {'id': 'evt:law_stone', 'preset': 'script', 'source': 'platform:law_stone', 'title': 'Law stone',
     'effects': [hook('q-d16.law_stone')], 'notes': "dark/aaze0013:26 (close), A3's text."},
    {'id': 'evt:throne', 'preset': 'script', 'source': 'platform:throne', 'title': 'The bloody throne',
     'effects': [hook('q-d16.throne')],
     'notes': "goal:throne: A3's q-d16.throne decides: at peace 'Gurodel would notice.'; at war two Energy Disks and 14,000 once, but not for a party with friends 113320 (D-47 Q22)."},
    {'id': 'evt:throne_back', 'preset': 'script', 'source': 'platform:throne_back', 'title': 'The bloody throne',
     'effects': [hook('q-d16.throne')]},
    {'id': 'evt:chest_larder', 'preset': 'chest', 'source': 'chest:larder', 'title': 'Chest',
     'notes': "The larder chest opens at peace (D-47 Q22)."},
    {'id': 'evt:chest_hoard', 'preset': 'chest', 'source': 'chest:hoard', 'title': 'Chest',
     'condition': {'lua': 'XeenQuests.can("q-d16.hoard")'}, 'else_effects': [hook('q-d16.hoard')],
     'notes': "The hoard refuses at peace (A3's q-d16.hoard fail text 'Gurodel would notice.'); at war it opens."},
    {'id': 'evt:hall_struck', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'not': AT_WAR},
     'lua': ('local struck = false\n'
             f'for i = 0, {N_ACTORS - 1} do\n'
             '    if evt.IsMapActorHostile(i) and not evt.IsMapActorDead(i) then struck = true end\n'
             'end\n'
             'if struck then XeenQuests.hook("q-d16.hall_attacked") end'),
     'notes': "D-47 Q22, D-37's timer pattern: a People giant struck at peace turns on the party; the timer sees it and calls A3's q-d16.hall_attacked (113323), which A2's relations read: the whole People turn, here and on D5. Every placed actor of the map is one of the People."},
    {'id': 'evt:throne_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:throne_hall', 'once': True,
     'seconds': 6, 'text': "A throne of black wood, big enough for four of you, stands under the smoke hole. The wood is stained darker than it was cut."},
]
wiring = {'format': 0, 'variables': ['war_arrived'], 'events': events}

atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_failing'},
              'notes': "The smoke hole (its ceiling level's top, sky: true) shows the Darkside's failing sun of Act V (D-47, D-42), by the preset's own name (never the texture alias xeendark1). After M33 xeen_darkside_day if A3's stage switch reaches indoor maps."}

project = {
    'format': 0, 'id': 'xeen_dd24', 'name': "Giants' Hall", 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'DD-24', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [9, 16], 'climbs': 'n'},
    'map_stats': {'id': 9177, 'encounter_chance': 0, 'treasure_level': 5, 'trap_dice': 4,
                  'perception_difficulty': 8, 'refill_days': 672, 'music': 31, 'environment': 'cave',
                  'lock_difficulty': 8, 'bolster': 'LowerToEqual', 'slots': []},
    'neighbours': [{
        'id': 'exit:d5_hold', 'to': 'xeen_d5.odm', 'kind': 'door', 'arrival': 'entrance:dd24_hold',
        'arrival_hint': "On D5 before the Giants' Hall's great doors behind Gurodel's hold, facing south (A6's "
                        "entrance:dd24_hold, (11264, 10752, 2688) facing 1536).",
        'notes': "D5 installed (A6). D5's door:dd24 (thing:giants_hall_doors) names this map's arrival "
                 "entrance:d5_hold: (0, 384, 0) facing north."}],
    'qbits': QB,
    'notes': "Xeen design brief, level L4: DD-24 Giants' Hall behind Gurodel's hold on D5 (Q-D16). D-47: the People 11083 Cyclops 38 x 9, 11084 Giant 50 x 17, 11085 Elder Giant 58 x 4 (A2's rows, faction xeen_giants_people, friendly at load, hostile on 113321/113242/113244/113323); 20.80k per member. Rest encounters 0 (D-47 Q25). Hooks q-d16.throne, hall_attacked, war_threshold, hoard, law_stone (A3). No map qbits (118090-118099 unused). Music 31. The way out leads to D5's entrance:dd24_hold (A6); D5's great doors arrive at entrance:d5_hold.",
}


def write(folder, docs):
    folder.mkdir(parents=True, exist_ok=True)
    for name, doc in docs:
        if isinstance(doc, str):
            (folder / name).write_text(doc)
        else:
            (folder / name).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))


if '--levels' in sys.argv:
    p = dict(project)
    for lv in ('L1', 'L2'):
        p['notes'] = f"Xeen design brief, level {lv}: DD-24 Giants' Hall (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-24 Giants' Hall, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('atmosphere.yml', atmosphere),
                     ('diagram.txt', DIAGRAM)])
print('written L4')
