#!/usr/bin/env python3
"""DD-11C Troll Holes, third pocket (Hobstadt's hall): writes the L1-L4 project folders of devdocs/xeen/briefs/dd11c.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt, atmosphere.yml
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/dd11/cycle.sh dd11c); never hand-edit the written files.
Written by agent:xeen-a7-dd11 after DD-11A's gen.py; shared helpers in level_generation/projects/xeen/dd11/lib.py.

Frame: x east, y north, z up. The pit (D2's third, widest hole) is at the origin; the hall gate and Hobstadt's hall run
straight east from it, the guild's gold behind the throne at the hall's east end; the trolls' stair (the way out)
leaves the pit's west side; the wild warren lies behind a hide flap in the pit's south side: the gnawed tunnel, the
trophy cave, the cold slope down to the frost seep and the ice trolls' den (-512), and the bone run back up."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys

sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/dd11')
from lib import (R, S, DIRT, DIRTFLR, HIDE, STRAW, BARK, BONES, POLES, DAYLIGHT, WATER, SKY, THEMES, ROUGH, rect,  # noqa
                 octo, blob, nest, heap, write, chest, light, TROLL_LIGHT, DAY_LIGHT, map_stats, ATMOSPHERE)

BRIEF = R / 'devdocs/xeen/briefs/dd11c'
ROCK = S('t66cave', 128, 256)

themes = THEMES + [
    {'id': 'theme:roots', 'wall': DIRT, 'floor': BARK, 'ceiling': DIRT, 'door': HIDE, 'reveal': DIRT,
     'notes': "Root steps (xdbark, D2's bark) in the dirt: the trolls' stair."},
    {'id': 'theme:bones', 'wall': DIRT, 'floor': BONES, 'ceiling': DIRT, 'door': HIDE, 'reveal': DIRT,
     'notes': "The bone run: a passage paved with gnawed bones (xobones)."},
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


THRONE = (3250, 320)
# ------------------------------------------------------------------------------------------------ floor 0
room('room:pit', 'Pit bottom', outline=octo(0, 0, 512), floor=0, ceiling=512, theme='theme:dirt', ambient=30,
     rough=ROUGH,
     ceiling_levels=[{'outline': octo(0, 0, 320), 'ceiling': 896, 'edge': DIRT, 'surface': SKY,
                      'notes': "The widest troll hole's shaft, 896 up to D2's sky."}],
     platforms=[heap('platform:mound', [-200, 260], 150, 110, "Earth and old bones under the hole.", rise=24)],
     notes="The widest of the three pits, daylight 896 up; the hall's carved log doors straight ahead (east), the trolls' stair west, a hide flap south.")
room('room:hall_gate', 'Hall gate', outline=rect(640, -384, 1280, 384), floor=0, ceiling=448, theme='theme:dirt',
     ambient=22,
     notes="Before the two great log doors carved with troll faces; two of the court lean on their clubs here.")
room('room:hall', "Hobstadt's hall", outline=rect(1408, -768, 3456, 768), floor=0, ceiling=576,
     ceiling_points=[[1920, 0, 704], [2432, 0, 768], [2944, 0, 704]], theme='theme:hall', ambient=20,
     platforms=[
         {'id': 'platform:throne', 'at': list(THRONE), 'size': [192, 256], 'rise': 72, 'surface': ROCK,
          'top_surface': ROCK, 'notes': "Hobstadt's throne of stacked boulders: its seat."},
         {'at': [THRONE[0] + 136, THRONE[1]], 'size': [80, 320], 'rise': 320, 'surface': ROCK, 'top_surface': ROCK,
          'notes': "The throne's back, boulders stacked against the east wall."},
         # D-89 (A7 s28): a shaped throne: arms of boulders either side of the seat, the back taller than the arms
         {'at': [THRONE[0] + 16, THRONE[1] + 152], 'size': [160, 48], 'rise': 176, 'surface': ROCK, 'top_surface': ROCK,
          'notes': "The throne's left arm, a boulder on a boulder."},
         {'at': [THRONE[0] + 16, THRONE[1] - 152], 'size': [160, 48], 'rise': 176, 'surface': ROCK, 'top_surface': ROCK,
          'notes': "The throne's right arm."},
     ],
     notes="An old cut-stone hall of the ancient trolls (MM8 d43's stone and carved slabs) under a vaulted roof, the court in two rows, Hobstadt's throne of stacked boulders with arms and a tall back at the east end; the guild's gold behind it, through the east wall south of the throne.")
room('room:hoard', "The guild's gold", outline=rect(3584, -640, 4224, 0), floor=0, ceiling=384,
     theme='theme:dirt', ambient=16, rough=ROUGH,
     platforms=[heap('platform:sacks', [3980, -300], 130, 110,
                     "Sacks stamped THIEVES' GUILD, heaped behind the throne.", rise=48, surface=STRAW)],
     notes="Behind the throne: the Thieves' Guild's sacks (A3's q-d13.hoard) and the trolls' strongbox.")
room('room:kings_stair', "The trolls' stair", path=[[-640, 0], [-1792, 0]], width=256, floor=0, slope={'to': 384},
     ceiling=320, theme='theme:roots', ambient=22,
     notes="The trolls' own way in and out, beside the pit: root steps up a steep burrow to a sod hatch.")
room('room:side_tunnel', 'Gnawed tunnel', path=[[0, -640], [0, -1536], [1536, -1536]], width=320, floor=0,
     ceiling=320, theme='theme:dirt', ambient=16, rough=ROUGH,
     notes="A tunnel away from the hall into the wild trolls' warren; the bone run comes up its south side.")
room('room:trophy', 'Trophy cave', outline=rect(1664, -2048, 2688, -1024), floor=0, ceiling=448,
     ceiling_points=[[2176, -1536, 544]], theme='theme:dirt', ambient=16, rough=ROUGH,
     # Two single hides with dirt between (texture fit: a hide is a picture meant once, merge point 16).
     walls=[{'wall': 'north', 'panels': [{'id': 'panel:trophies', 'offset': 288, 'length': 128, 'bottom': 96,
                                          'height': 256, 'surface': HIDE,
                                          'notes': "Hides of the fallen nailed to the roots."},
                                         {'id': 'panel:trophies_2', 'offset': 608, 'length': 128, 'bottom': 96,
                                          'height': 256, 'surface': HIDE,
                                          'notes': "Another hide nailed to the roots."}]}],
     notes="Shields, helms and hides of the fallen nailed to the roots; a chest among them; the cold slope down leaves the south wall.")
room('room:cold_slope', 'Cold slope', path=[[2176, -2176], [2176, -3328]], width=256, floor=0, slope={'to': -512},
     ceiling=320, theme='theme:dirt', ambient=16,
     notes="A slope down 512 to where the air turns cold.")
# ------------------------------------------------------------------------------------------------ floor -512
room('room:frost_seep', 'Frost seep', outline=rect(1664, -4480, 2688, -3456), floor=-512, ceiling=-96,
     ceiling_points=[[2176, -3968, 0]], theme='theme:dirt', ambient=14, rough=ROUGH,
     notes="Where the pocket reaches under the world's rim: cold seeps in through cracks lit faintly by the stars below.")
room('room:ice_den', "Ice trolls' den", outline=rect(512, -4480, 1536, -3456), floor=-512, ceiling=-96,
     theme='theme:dirt', ambient=14, rough=ROUGH,
     notes="Frost on the roots, breath steaming: the den of the pale trolls who like it cold; their cache.")
room('room:bone_run', 'Bone run', path=[[1024, -3328], [1024, -1824]], width=256, floor=-512, slope={'to': 0},
     ceiling=-224, theme='theme:bones', ambient=14,
     notes="A low passage paved with bones, climbing from the ice den to the gnawed tunnel (the bone stair).")
# ------------------------------------------------------------------------------------------------ openings
op('open:pit_gate', 'room:pit', 'room:hall_gate', link='link:pit_gate', width=352, height=384)
op('open:gate_hall', 'room:hall_gate', 'room:hall', link='link:gate_hall', width=320, height=384,
   notes="The carved log doors, open.")
op('open:hall_hoard', 'room:hall', 'room:hoard', link='link:hall_hoard', width=256, height=320,
   notes="Open ground behind the throne, south of it.")
op('open:pit_stair', 'room:pit', 'room:kings_stair', link='link:pit_stair', width=224, height=288)
op('open:pit_tunnel', 'room:pit', 'room:side_tunnel', link='link:pit_tunnel', width=128, height=256,
   notes="A hide flap: the warren beyond is not the court's.")
op('open:tunnel_trophy', 'room:side_tunnel', 'room:trophy', link='link:tunnel_trophy', width=288, height=288)
op('open:trophy_slope', 'room:trophy', 'room:cold_slope', link='link:trophy_seep', width=224, height=288)
op('open:slope_seep', 'room:cold_slope', 'room:frost_seep', link='link:trophy_seep', width=224, height=288)
op('open:seep_den', 'room:frost_seep', 'room:ice_den', link='link:seep_den', width=384, height=320)
op('open:den_run', 'room:ice_den', 'room:bone_run', link='link:den_run', width=192, height=256,
   notes="A door of lashed antlers and hide.")
op('open:run_tunnel', 'room:bone_run', 'room:side_tunnel', link='link:run_tunnel', width=192, height=256)
rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:dirt', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "DD-11C Troll Holes, third pocket (Hobstadt's hall): floor 0 and the cold warren at -512; x east, y north. Written by output/studio_cal/dd11c/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:pit': 0, 'room:hall_gate': 0, 'room:hall': 0, 'room:hoard': 0, 'room:kings_stair': 0,
          'room:side_tunnel': 0, 'room:trophy': 0, 'room:cold_slope': 0, 'room:frost_seep': -512,
          'room:ice_den': -512, 'room:bone_run': -512}
TROLL, ICE, COURT, HOBSTADT = 11690, 11692, 11075, 11073
PLAN_SPACES = [
    ('room:pit', 'Pit bottom', 'room', 'S', "The widest of the three pits, daylight 896 up; the hall's carved log doors straight ahead.", [], None),
    ('room:hall_gate', 'Hall gate', 'room', 'S', "Two great log doors carved with troll faces; two court guards lean on clubs and let the party through.", [(COURT, 2, 28, "Hobstadt's court (Hobstadt's Guard 11075, faction hobstadt): peaceful until q-d13.hostile.")], None),
    ('room:hall', "Hobstadt's hall", 'room', 'L', "The court in two rows under root vaults; Hobstadt on a throne of stacked boulders: gold, one of your number, or a fight.", [(COURT, 6, 28, "Hobstadt's court: peaceful until q-d13.hostile; then they fight beside him.")], None),
    ('room:hoard', "The guild's gold", 'room', 'S', "Behind the throne: sacks stamped THIEVES' GUILD (q-d13.hoard) and the strongbox (tier 4); Hobstadt's friends or his killers only.", [], 4),
    ('room:kings_stair', "The trolls' stair", 'corridor', 'S', "The trolls' own way in and out, beside the pit: root steps up to a sod hatch on D2.", [], None),
    ('room:side_tunnel', 'Gnawed tunnel', 'corridor', 'M', "A tunnel into the wild trolls' warren behind a hide flap; the bone run comes up here.", [(TROLL, 3, 18, "Wild trolls (Xeen Warren Troll A), not the court: hostile at load.")], None),
    ('room:trophy', 'Trophy cave', 'room', 'M', "Shields and helms of the fallen nailed to the roots; a chest among them; a slope down to the cold.", [(TROLL, 3, 18, "Wild trolls.")], 3),
    ('room:cold_slope', 'Cold slope', 'corridor', 'S', "Down 512 to where the air turns cold.", [], None),
    ('room:frost_seep', 'Frost seep', 'room', 'M', "Where the pocket reaches under the world's rim: cold through cracks lit by the stars below.", [(ICE, 2, 38, "Ice Trolls (Xeen Warren Troll C).")], None),
    ('room:ice_den', "Ice trolls' den", 'room', 'M', "Frost on the roots, breath steaming: the pale trolls' den and their cache.", [(ICE, 2, 38, "Ice Trolls.")], 3),
    ('room:bone_run', 'Bone run', 'corridor', 'M', "A low passage paved with bones, climbing to the gnawed tunnel.", [(TROLL, 2, 18, "Wild trolls.")], None),
]


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pop, ch in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if pop:
            s['population'] = [{'actor': a, 'groups': n, 'levels': [lv, lv], 'notes': f"{n} placed. {note}"}
                               for a, n, lv, note in pop]
        elif sid != 'room:hall':
            s['empty'] = True
        if sid == 'room:hall':
            s['population'].append({'actor': HOBSTADT, 'role': 'boss', 'groups': 1, 'levels': [42, 42],
                                    'notes': "Hobstadt 11073 (boss row, faction hobstadt, friendly at load; frenzy below half health); he is NPC 5110 (clicked while at peace, he talks)."})
        spaces.append(s)
    links = [
        {'id': 'link:pit_gate', 'from': 'room:pit', 'to': 'room:hall_gate', 'kind': 'open'},
        {'id': 'link:gate_hall', 'from': 'room:hall_gate', 'to': 'room:hall', 'kind': 'double_door',
         'notes': "The carved log doors, open at load."},
        {'id': 'link:hall_hoard', 'from': 'room:hall', 'to': 'room:hoard', 'kind': 'open',
         'notes': "Open ground behind the throne; q-d13.hoard gates the sacks and the strongbox: tribute, trial or Hobstadt's death (else its fail text)."},
        {'id': 'link:pit_stair', 'from': 'room:pit', 'to': 'room:kings_stair', 'kind': 'open'},
        {'id': 'link:pit_tunnel', 'from': 'room:pit', 'to': 'room:side_tunnel', 'kind': 'door', 'motion': 'slide',
         'notes': "A hide flap: the warren beyond is not the court's."},
        {'id': 'link:tunnel_trophy', 'from': 'room:side_tunnel', 'to': 'room:trophy', 'kind': 'open'},
        {'id': 'link:trophy_seep', 'from': 'room:trophy', 'to': 'room:frost_seep', 'kind': 'ramp',
         'notes': "By the cold slope (its own room)."},
        {'id': 'link:seep_den', 'from': 'room:frost_seep', 'to': 'room:ice_den', 'kind': 'open'},
        {'id': 'link:den_run', 'from': 'room:ice_den', 'to': 'room:bone_run', 'kind': 'door', 'motion': 'slide',
         'notes': "A door of lashed antlers and hide."},
        {'id': 'link:run_tunnel', 'from': 'room:bone_run', 'to': 'room:side_tunnel', 'kind': 'ramp',
         'notes': "The bone run climbs 512 to the gnawed tunnel (the bone stair)."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "The third and widest troll hole drops the party straight before the carved log doors of Hobstadt's hall. His court of eight stands in two rows under the root vaults and lets the party through; the Troll King on his throne of boulders names his price: all your gold, one of your number, or a fight to the death. Behind the throne lie the Thieves' Guild's sacks. A hide flap off the pit leads into the wild trolls' warren, down to the frost seep under the world's rim, where the ice trolls live.",
        'purpose': "Q-D13 Hobstadt's Trolls: NPC 5110's topics (A3: tribute 113261, trial 113262 with the War Troll promotion, hostile 113263), q-d13.hobstadt on his death (hobstadt_slain 113264), q-d13.throne (the vacant throne promotes a Troll member), q-d13.hoard (done 113266). Party 23 to 27: the court Hobstadt's Guard 11075 (28) x8, Hobstadt 11073 (42); wild trolls Troll 11690 (18) x8, Ice Troll 11692 (38) x4; treasure 3, the hoard 4.",
        'mood': "A long earthen hall under root vaults, lit by the court's fires; outside the court, gnawed tunnels and a cold that steams the breath.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:warren', 'spaces': ['room:side_tunnel', 'room:trophy', 'room:cold_slope',
                                                   'room:frost_seep', 'room:ice_den', 'room:bone_run'],
                   'notes': "The wild warren: down the cold slope, along the rim, up the bone run."}],
        'entrances': [
            {'id': 'entrance:d2_hole', 'space': 'room:pit', 'kind': 'arrival', 'facing': 'e',
             'how': "D2's third, widest troll hole (thing:dd11c_hole, event 34, near the rim): the party falls in and lands at the pit's bottom, facing the hall's log doors (east)."},
            {'id': 'entrance:d2_stair', 'space': 'room:kings_stair', 'kind': 'exit', 'neighbour': 'exit:d2_return',
             'how': "The trolls' stair's sod hatch: out to D2 beside the third hole (A6's return point), the game's leave window."},
        ],
        'critical_path': ['room:pit', 'room:hall_gate', 'room:hall', 'room:hoard'],
        'return_path': ['room:hoard', 'room:hall', 'room:hall_gate', 'room:pit', 'room:kings_stair'],
        'goals': [
            {'id': 'goal:deal', 'space': 'room:hall', 'kind': 'use', 'story': 'Q-D13',
             'what': "Hobstadt's topics (NPC 5110, A3): give gold (tribute), sacrifice one (trial: a Troll member becomes a War Troll), or fight (hostile)."},
            {'id': 'goal:hoard', 'space': 'room:hoard', 'kind': 'take', 'story': 'Q-D13',
             'what': "The guild's gold (A3's q-d13.hoard): open to Hobstadt's friends or after his death.",
             'gives': {'qbit': 113266}},
        ],
        'set_pieces': [{'id': 'set:hall', 'kind': 'boss', 'spaces': ['room:hall'],
                        'rule': "Hobstadt's hall: the court in two rows, peaceful until the fight (q-d13.hostile, or a court troll killed); the fight turns every troll of the holes."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(PLAN_SPACES), 'sectors': len(PLAN_SPACES), 'monsters_about': 21, 'chests': 3,
                   'doors': 3, 'loops': 1, 'floor_area_munits2': 12},
        'notes': "Size S (at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/dd11c.graph.yml and D-25 (Hobstadt's court a peaceful row of its own, 11075, faction hobstadt; the trolls' stair's exit preset). The cold slope is a room of its own; the bone run is the bone stair.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-11C Troll Holes, third pocket: Hobstadt's hall (not to scale; plan, north up)

                     (D2: the widest hole, fall in) v
   (D2) =exit= [TROLLS' STAIR] -- [PIT BOTTOM: start] -- [HALL GATE: 2 court] =log doors (open)= [HOBSTADT'S HALL: 6 court, Hobstadt, throne] -- [GUILD'S GOLD: sacks, T4]
                                        =hide flap=
                                     [GNAWED TUNNEL] -------------- [TROPHY CAVE, T3]
                                          | bone run (climbs 512)       | cold slope (0 -> -512)
                              -512  [ICE TROLLS' DEN, T3] -------- [FROST SEEP]
                                     =antler door= (to the bone run)
"""

# ================================================================================================ objects.yml
objects = {
    'format': 0,
    'start': {'room': 'room:pit', 'at': [128, -64], 'facing': 'e',
              'notes': "Where D2's third troll hole drops the party: the pit's bottom, facing the hall gate (east)."},
    'doors': [
        {'id': 'door:hall', 'opening': 'open:gate_hall', 'kind': 'slide_left', 'leaves': 2, 'state': 'open',
         'thickness': 32, 'speed': 160, 'surface': BARK, 'tile': True,
         'notes': "The two great log doors carved with troll faces: open at load."},
        {'id': 'door:flap', 'opening': 'open:pit_tunnel', 'kind': 'slide_up', 'fold': True, 'thickness': 16,
         'speed': 192, 'surface': HIDE, 'tile': True, 'notes': "A hide flap: the warren beyond is not the court's."},
        {'id': 'door:antler', 'opening': 'open:den_run', 'kind': 'slide_right', 'thickness': 24, 'speed': 160,
         'surface': POLES, 'tile': True, 'notes': "A door of lashed antlers and hide."},
    ],
    'plates': [
        {'id': 'plate:before_throne', 'room': 'room:hall', 'at': [2688, 0], 'size': [192, 1280],
         'notes': "The floor across the hall before the throne: Hobstadt speaks the first time the party crosses it."},
    ],
    'sounds': [
        {'id': 'sound:wind', 'room': 'room:pit', 'at': [0, 0], 'sound': 'whistling wind', 'radius': 1300,
         'inner_radius': 300, 'volume': 0.35, 'notes': "Wind over the hole far above."},
        {'id': 'sound:hall_fire', 'room': 'room:hall', 'at': [2432, 0], 'sound': 'campfire', 'radius': 2000,
         'inner_radius': 600, 'volume': 0.5, 'notes': "The court's fires."},
        {'id': 'sound:cold', 'room': 'room:frost_seep', 'at': [2176, -3968], 'sound': 'whistling wind',
         'radius': 1600, 'inner_radius': 400, 'volume': 0.5, 'notes': "Cold air through the cracks under the rim."},
    ],
    'lights': [
        # Lamp rule (the user, 2026-11-20; lane A7 sixth session): every light's height is over the floor under it
        # and inside its room (lampcheck.py); the old negative heights put five lights under the floor.
        light('light:pit_day', 'room:pit', [0, 0], 820, 1300, DAY_LIGHT, notes="Daylight down the shaft."),
        light('light:gate', 'room:hall_gate', [960, 0], 400, 900, [180, 130, 90]),
        light('light:hall_w', 'room:hall', [1920, 0], 520, 1400, [190, 135, 90]),
        light('light:hall_e', 'room:hall', [2944, 0], 520, 1400, [190, 135, 90]),
        light('light:hoard', 'room:hoard', [3904, -320], 320, 800, [180, 150, 90]),
        light('light:stair_top', 'room:kings_stair', [-1650, 0], 220, 900, DAY_LIGHT,
              notes="Daylight round the sod hatch."),
        light('light:tunnel', 'room:side_tunnel', [600, -1536], 280, 1000, TROLL_LIGHT),
        light('light:trophy', 'room:trophy', [2176, -1536], 400, 1100, TROLL_LIGHT),
        light('light:slope', 'room:cold_slope', [2176, -2900], 220, 800, [140, 150, 170]),
        light('light:seep', 'room:frost_seep', [2176, -3968], 360, 1200, [150, 175, 215],
              notes="Faint cold light through the cracks: the stars below the rim."),
        light('light:den', 'room:ice_den', [1024, -3968], 290, 1100, [150, 175, 215]),
        light('light:run', 'room:bone_run', [1024, -2600], 200, 900, [140, 130, 120]),
    ],
    'chests': [
        chest('chest:hoard', 'room:hoard', [4150, -560], 'e', 4, 800,
              "The trolls' strongbox behind the throne (the map's hoard, a level up).", trap=3),
        chest('chest:trophy', 'room:trophy', [2600, -1960], 'e', 3, 400, "A chest among the trophies."),
        chest('chest:ice', 'room:ice_den', [600, -4380], 'e', 3, 450, "The ice trolls' cache."),
    ],
    'monsters': [],
    'decorations': [],
    'exits': [
        {'id': 'exit:hatch', 'room': 'room:kings_stair', 'at': [-1792, 0], 'size': [224, 256], 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
         'to': 'exit:d2_return', 'notes': "The sod hatch at the trolls' stair's top: daylight through the roots (D2)."},
    ],
}

COURT_GROUP, HOB_GROUP = 30, 31
PLACED = [
    ('room:side_tunnel', 10, [(TROLL, [0, -1000], 90), (TROLL, [500, -1536], 180), (TROLL, [1100, -1536], 180)]),
    ('room:trophy', 11, [(TROLL, [1900, -1300], 180), (TROLL, [2400, -1300], 180), (TROLL, [2200, -1800], 90)]),
    ('room:bone_run', 12, [(TROLL, [1024, -2300], 270), (TROLL, [1024, -2900], 90)]),
    ('room:ice_den', 13, [(ICE, [850, -3800], 90), (ICE, [1200, -4100], 90)]),
    ('room:frost_seep', 14, [(ICE, [1950, -3800], 90), (ICE, [2400, -4100], 180)]),
    ('room:hall_gate', COURT_GROUP, [(COURT, [960, -260], 90), (COURT, [960, 260], 270)]),
    ('room:hall', COURT_GROUP, [(COURT, [1900, -500], 90), (COURT, [2350, -500], 90), (COURT, [2800, -500], 90),
                                (COURT, [1900, 500], 270), (COURT, [2350, 500], 270), (COURT, [2800, 500], 270)]),
]
for room_id, group, ms in PLACED:
    key = room_id.split(':')[1]
    for n, (mon, at, facing) in enumerate(ms, 1):
        objects['monsters'].append({'id': f'monster:{key}_{n}', 'room': room_id, 'monster': mon, 'at': at,
                                    'facing': facing, 'group': group})
objects['monsters'].append({'id': 'monster:hobstadt', 'room': 'room:hall', 'monster': HOBSTADT,
                            'at': [THRONE[0] - 200, THRONE[1]], 'facing': 180, 'group': HOB_GROUP, 'npc': 5110,
                            'notes': "Hobstadt 42 (A2's boss row 11073, faction hobstadt, friendly at load), before his throne. He is NPC 5110 (merge point 22, monsters[].npc): clicked while at peace he talks; plate:before_throne greets once on approach, as the source does."})

DECOS = [
    ('pit_bones', 'room:pit', 'dec29', [-300, -330]),
    ('pit_skull', 'room:pit', '7dec20', [330, 320]),
    ('gate_skulls_n', 'room:hall_gate', 'sklplrev', [720, 320]),
    ('gate_skulls_s', 'room:hall_gate', 'sklplrev', [720, -320]),
    ('hall_skulls_1', 'room:hall', 'sklplrev', [1500, 690]),
    ('hall_skulls_2', 'room:hall', 'sklplrev', [1500, -690]),
    ('hall_bones_1', 'room:hall', '7dec18', [3380, -690]),
    ('hall_bones_2', 'room:hall', 'dec29', [2432, 700]),
    ('hall_bones_3', 'room:hall', 'dec29', [2432, -700]),
    ('hoard_bones', 'room:hoard', '7dec20', [3660, -80]),
    ('trophy_skulls', 'room:trophy', 'sklplrev', [1740, -1960]),
    ('trophy_bones', 'room:trophy', '7dec18', [2610, -1110]),
    ('trophy_skull', 'room:trophy', '7dec20', [1740, -1110]),
    ('seep_mite_2', 'room:frost_seep', 'stlmite2', [2600, -3550]),
    ('seep_mite', 'room:frost_seep', 'stlmite1', [1750, -4400]),
    ('den_mite', 'room:ice_den', 'stlmite2', [600, -3550]),
    ('den_bones', 'room:ice_den', 'dec29', [1450, -4400]),
]
for key, room_id, deco, at in DECOS:
    objects['decorations'].append({'id': f'deco:{key}', 'room': room_id, 'decoration': deco, 'at': at,
                                   'floor_height': FLOORS[room_id]})

# ================================================================================================ wiring.yml
HOARD_OPEN = "IsQBitSet(QBit(113261)) or IsQBitSet(QBit(113262)) or IsQBitSet(QBit(113264))"
THRONE_LUA = """if IsQBitSet(QBit(113264)) then
    XeenQuests.hook("q-d13.throne")
elseif IsQBitSet(QBit(113263)) then
    evt.StatusText("Hobstadt stands before his throne with his club raised. He is done talking.", 4)
else
    evt.StatusText("A throne of stacked boulders. Hobstadt stands before it and watches you.", 4)
end"""
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'text': "You land in the widest of the pits. Ahead, two great log doors carved with troll faces stand open.",
     'seconds': 6, 'notes': "The landing (a one-shot timer: the party arrives standing at the pit's bottom)."},
    {'id': 'evt:gate_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:hall_gate', 'once': True,
     'condition': {'not': {'qbit': 113263}},
     'text': "The two trolls at the doors lean on their clubs and watch you pass. Nobody stops you.", 'seconds': 5},
    {'id': 'evt:approach', 'preset': 'script', 'trigger': 'step', 'source': 'plate:before_throne', 'once': True,
     'condition': {'lua': "not IsQBitSet(QBit(113263)) and not IsQBitSet(QBit(113264))"},
     'lua': 'evt.SpeakNPC(5110)',
     'notes': "state:deal: the first time the party comes before the throne, Hobstadt speaks unasked (NPC 5110, A3's topics: Give gold, Sacrifice one, Fight to the death), as the source's step event before his throne does (aaze0040:10-11). Later talks: click Hobstadt himself (monsters[].npc)."},
    {'id': 'evt:throne', 'preset': 'script', 'source': 'platform:throne', 'title': 'Throne', 'lua': THRONE_LUA,
     'notes': "Hobstadt's throne: while he lives a line (talk to him by clicking him), while he fights 'done talking'; after his death A3's q-d13.throne (a Troll member is promoted; others read 'The throne is vacant.', aaze0040:8-9)."},
    {'id': 'evt:court_fight', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'any': [{'kills': {'group': COURT_GROUP, 'at_least': 1}}, {'kills': {'group': HOB_GROUP}}],
                   'not': {'qbit': 113263}},
     'effects': [{'qbit': 113263}],
     'text': "The court roars. Every troll under the forest is your enemy now.", 'seconds': 5,
     'notes': "D-25 Q7, 'a fight turns all': a court troll or Hobstadt killed without his 'Fight to the death' sets q-d13.hostile (113263), which turns the court and the holes' trolls (A2's relation rules)."},
    {'id': 'evt:hobstadt_slain', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:hobstadt'}},
     'effects': [{'lua': 'XeenQuests.hook("q-d13.hobstadt")'}],
     'text': "Hobstadt falls across the foot of his throne. The throne is vacant.", 'seconds': 5,
     'notes': "state:fight: his death runs A3's q-d13.hobstadt (hobstadt_slain 113264), which opens the hoard and the throne."},
    {'id': 'evt:hobstadt_gone', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 113264},
     'effects': [{'hide_actors': HOB_GROUP}],
     'notes': "A slain Hobstadt stays dead after a refill: his group is hidden on entry once hobstadt_slain is set."},
    {'id': 'evt:sacks', 'preset': 'script', 'source': 'platform:sacks', 'title': 'Sacks',
     'lua': 'XeenQuests.hook("q-d13.hoard")',
     'notes': "goal:hoard: A3's q-d13.hoard (done 113266, its gold and experience; until a deal or his death its fail text, after its else text)."},
    {'id': 'evt:chest_hoard', 'preset': 'chest', 'source': 'chest:hoard', 'title': 'Chest',
     'condition': {'lua': HOARD_OPEN}, 'else_effects': [{'lua': 'XeenQuests.hook("q-d13.hoard")'}],
     'notes': "The trolls' strongbox (tier 4) behind the throne, gated as the sacks: until tribute, trial or his death the hook's fail text."},
    {'id': 'evt:chest_trophy', 'preset': 'chest', 'source': 'chest:trophy', 'title': 'Chest'},
    {'id': 'evt:chest_ice', 'preset': 'chest', 'source': 'chest:ice', 'title': 'Chest'},
    {'id': 'evt:hall_doors', 'preset': 'door', 'source': 'door:hall', 'title': 'Log doors'},
    {'id': 'evt:flap', 'preset': 'door', 'source': 'door:flap', 'title': 'Hide flap'},
    {'id': 'evt:antler', 'preset': 'door', 'source': 'door:antler', 'title': 'Antler door'},
    {'id': 'evt:trophies', 'preset': 'text', 'source': 'panel:trophies', 'title': 'Trophies',
     'text': "Hides, dented shields and helms of the fallen, nailed to the roots.", 'seconds': 4},
    {'id': 'evt:cold', 'preset': 'text', 'trigger': 'step', 'source': 'room:frost_seep', 'once': True,
     'text': "The air turns bitter. Through cracks in the floor you see stars, far below.", 'seconds': 5},
    {'id': 'evt:hatch', 'preset': 'exit', 'source': 'exit:hatch', 'title': 'Sod hatch',
     'notes': "D-24/D-25: the trolls' stair's top, the exit preset (the game's leave window, no 'Exit the Troll Hole?' question: aaze0040:12 stays in the ledger) to D2 beside the third hole (exit:d2_return, A6's return point)."},
]
wiring = {'format': 0, 'events': events}

project = {
    'format': 0, 'id': 'xeen_dd11c', 'name': 'Troll Holes, third pocket', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon',
    'identity': {'shape': 'cave', 'family': 'd43', 'seen': ["the widest troll hole's pit and the hall's carved log doors", "Hobstadt's hall in the ancient trolls' cut stone and carved slabs, his throne of stacked boulders with arms and a tall back", "the guild's gold behind the throne, the ice trolls' den and the frost seep in broken caves"]},  # D-89 (A7 s28)
    'map_code': 'DD-11C', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [12, 10], 'climbs': 'n'},
    'map_stats': map_stats(9164),
    'neighbours': [
        {'id': 'exit:d2_return', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': [1536, -17408, 928],
         'direction': 180,
         'arrival_hint': "A6's return point for the third hole (D2 event 34, thing:dd11c_hole, the widest, near the rim): on the forest floor about 300 from the pit's lip, facing west, clear of D2's troll spawns.",
         'notes': "The trolls' stair's sod hatch out to D2 (D-25: one way in by the hole, one way out by the stair)."},
    ],
    'notes': "Xeen design brief, level L4: DD-11C Troll Holes, third pocket: Hobstadt's hall, under D2 Sprite Forest (Q-D13 Hobstadt's Trolls). Monsters, all placed: the court 8 Hobstadt's Guard 11075 (28, faction hobstadt, friendly at load; group 30) and Hobstadt 11073 (42, boss row; group 31), hostile on q-d13.hostile 113263; the wild trolls 8 Troll 11690 (18) and 4 Ice Troll 11692 (38) in groups 10-14, hostile by the world's relations until tribute or trial. Slot 1 Xeen Warren Troll for the map card, rest encounters 10 % (D-33: the warren trolls follow relations.yml, hostile before tribute, friendly after). Map qbits 110980-110989: none used; A3's Q-D13 bits read by number (113261-113266). Hooks: NPC 5110 (evt.SpeakNPC), q-d13.hobstadt, q-d13.throne, q-d13.hoard. Music 8. One way in (D2's third hole drops the party at the pit's bottom, the start) and one way out (the trolls' stair's sod hatch, exit:d2_return, A6's point).",
}


if '--levels' in sys.argv:
    p = dict(project)
    for lv in ('L1', 'L2'):
        p['notes'] = f"Xeen design brief, level {lv}: DD-11C Troll Holes, third pocket (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-11C Troll Holes, third pocket: the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

CAVES = {  # D-89 cave shape (A7 s28): room -> cut, floor rise/fall, roof rise, stalactites; Hobstadt's hall is
    # cut stone and keeps its square corners and level floor (the court stands in two rows)
    'room:frost_seep': {'cut': 256, 'floor': 80, 'stalactites': (2, 128)},
    'room:hall_gate': {'cut': 160, 'floor': 48, 'roof': 128},
    'room:hoard': {'cut': 160, 'floor': 48, 'roof': 128},
    'room:ice_den': {'cut': 256, 'floor': 80, 'roof': 192, 'stalactites': (2, 128)},
    'room:pit': {'floor': 0},  # the party lands here: the floor stays level under the hole
    'room:trophy': {'floor': 80},
}
write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', ATMOSPHERE)])
from lib import shape_caves  # noqa
shape_caves(BRIEF / 'L4', CAVES)
print('written L4')
