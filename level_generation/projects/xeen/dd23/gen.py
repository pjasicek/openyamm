#!/usr/bin/env python3
"""DD-23 Gargoyle Lair: writes the L1-L4 project folders of devdocs/xeen/briefs/dd23 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, atmosphere.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/dd23/cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-dd23 (lane A7, phase 4, session 9) after XD-26's gen.py (level_generation/projects/xeen/xd26/gen.py).

Frame: x east, y north, z up. The mouth opens south at y 0 (D4's entrance:dd23_lair lies south of it); the cave runs
north on floor 0 (the guano slope, the perch hall, the still gallery) and climbs by the rock ramp (west) and the rock
steps (east) to floor 640 (the upper perches over the perch hall, the roost under its crack of sky, the nest). Rooms
stand 128 apart (the walls' thickness). D-39 wins over the graph: 15 placed gargoyles, one Gargoyle Overlord 45 on the
highest rock, MM7 7d07 rock, MM6 straw on the nest, snow (a floor, no weather) under the crack, no doors."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/dd23'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM7 Thunderfist Mountain (7d07): its cave rock c2b on walls, roofs, pillars and the roosting rocks (one size
# everywhere), its rock floor cfb1 (7d07's Cfb1) underfoot; MM6 straw on the nest's floor; MM7's snow (7snow) on the
# drift under the crack; XD-05's poles (t66abc10a) for the nest's rim of sticks; D-45's Darkside crag view (xdcraglt)
# in the mouth.
ROCK = S('c2b', 256, 256)
ROCKFLR = S('cfb1', 128, 128, scale=2)
STRAW = S('straw', 256, 256)
SNOW = S('7snow', 128, 128, scale=2)
POLE = S('t66abc10a', 32, 128)
DAYLIGHT = S('xdcraglt', 256, 256, fit=True, uneven=True)   # D-45 (2): D4's crags from the mouth (was xddaylt)
SKY = S('c2b', 256, 256, sky=True)

themes = [
    {'id': 'theme:rock', 'wall': ROCK, 'floor': ROCKFLR, 'ceiling': ROCK, 'reveal': ROCK,
     'notes': "The lair's caves: MM7 Thunderfist's (7d07) dark cave rock c2b on walls and roofs, its rock floor cfb1."},
    {'id': 'theme:nest', 'wall': ROCK, 'floor': STRAW, 'ceiling': ROCK, 'reveal': ROCK,
     'notes': "The nest: the same rock, the floor deep in old straw (MM6 straw)."},
]


def octo(cx, cy, r):
    c = int(r * 0.41)
    return [[cx - c, cy - r], [cx + c, cy - r], [cx + r, cy - c], [cx + r, cy + c], [cx + c, cy + r], [cx - c, cy + r],
            [cx - r, cy + c], [cx - r, cy - c]]


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


UP = 640                      # the roost level's floor
CRACK = [[1216, 4992], [1600, 5056], [1664, 5312], [1472, 5440], [1152, 5248]]   # the crack of sky over the roost
CRACK_MID = [1408, 5216]
# The roosting rocks: (key, middle, rise of the rock over its base of dust). The highest carries the Overlord.
ROCKS = [('high', (1920, 5600), 432), ('north', (900, 5600), 272), ('west', (1000, 4700), 208),
         ('east', (1950, 4950), 240), ('south', (1880, 5300), 176)]
HEAP_RISE = 16
ROCK_R, HEAP_R = 112, 144

# ------------------------------------------------------------------------------------------------ floor 0
room('room:mouth', 'Cave mouth',
     outline=[[-256, 0], [256, 0], [384, 128], [384, 640], [256, 768], [-256, 768], [-384, 640], [-384, 128]],
     floor=0, ceiling=512, theme='theme:rock', ambient=24,
     notes="The way in from D4's crags, 768 square with its corners broken off: the mouth white with droppings, the Darkside's day behind (the exit in its south wall), the cave bending north and in.")
room('room:guano_slope', 'Guano slope',
     outline=[[-256, 896], [256, 896], [320, 1152], [320, 1920], [256, 2176], [-256, 2176], [-320, 1920], [-320, 1152]],
     floor=0, ceiling=448, theme='theme:rock', ambient=18,
     stalactites=[{'at': [120, 1400], 'radius': 64, 'length': 160}, {'at': [-140, 1900], 'radius': 56, 'length': 144}],
     notes="A passage 640 wide and 1,280 long, slick with droppings and scratched by claws; the bone ledge's cleft opens off its west wall.")
room('room:bone_ledge', 'Bone ledge',
     outline=[[-1024, 1280], [-448, 1280], [-448, 1792], [-1024, 1792], [-1088, 1664], [-1088, 1408]],
     floor=0, ceiling=384, theme='theme:rock', ambient=16,
     notes="A dead-end cleft, 640 by 512, where a climber died: his bones, rope and pack.")
room('room:perch_hall', 'Perch hall',
     outline=[[-768, 2304], [640, 2304], [640, 3456], [-768, 3456]],
     floor=0, ceiling=1216, theme='theme:rock', ambient=16,
     platforms=[
         # D-89 (A7 s28): the perches are rock ledges with broken edges, not boxes
         {'id': 'platform:perch_w', 'outline': [[-768, 2880], [-640, 2904], [-584, 3008], [-600, 3200], [-560, 3320],
                                                [-648, 3392], [-768, 3392]], 'rise': 352,
          'surface': ROCK, 'top_surface': ROCKFLR, 'notes': "A rock ledge on the west wall where the young ones sit."},
         {'id': 'platform:perch_se', 'outline': [[256, 2304], [640, 2304], [640, 2496], [544, 2472], [424, 2512],
                                                 [304, 2464]], 'rise': 320,
          'surface': ROCK, 'top_surface': ROCKFLR, 'notes': "A rock ledge on the south wall."},
     ],
     stalactites=[{'at': [-200, 2900], 'radius': 96, 'length': 320}, {'at': [300, 3050], 'radius': 80, 'length': 272},
                  {'at': [-380, 2560], 'radius': 72, 'length': 240}],
     notes="A high cave, 1,408 by 1,152 and 1,216 high: perches on its walls where the young ones sit; the upper perches look down from its north side; the rock ramp climbs behind its west wall.")
room('room:rock_ramp', 'Rock ramp', path=[[-896, 2496, 0], [-1088, 2496, 0], [-1088, 3840, UP], [-896, 3840, UP]],
     width=256, floor=0, ceiling=448, theme='theme:rock', ambient=16,
     notes="A ramp of broken rock climbing 640 behind the perch hall's west wall, from the hall to the upper perches.")
room('room:still_gallery', 'Still gallery',
     outline=[[768, 2304], [1664, 2304], [1792, 2432], [1792, 3200], [768, 3200]],
     floor=0, ceiling=704, theme='theme:rock', ambient=16,
     pillars=[{'outline': octo(1024, 2560, 96), 'surface': ROCK, 'notes': "A weathered pillar like a statue."},
              {'outline': octo(1536, 2560, 88), 'surface': ROCK, 'notes': "A weathered pillar like a statue."},
              {'outline': octo(1600, 2880, 80), 'surface': ROCK, 'notes': "A weathered pillar like a statue."}],
     notes="A cave of weathered rock pillars like statues, 1,024 by 896; three of the still shapes are gargoyles. The rock steps climb north from its far end to the roost.")
room('room:rock_steps', 'Rock steps', outline=[[1376, 3328], [1696, 3328], [1696, 4352], [1376, 4352]], floor=0,
     slope={'to': UP, 'toward': 'north', 'steps': 16}, ceiling=448, ceiling_slope={'to': UP + 448, 'toward': 'north'},
     theme='theme:rock', ambient=16,
     notes="Rock steps climbing 640 north from the still gallery to the roost.")

# ------------------------------------------------------------------------------------------------ floor 1 (640)
room('room:upper_perches', 'Upper perches',
     outline=[[-768, 3584], [512, 3584], [512, 4864], [128, 4864], [128, 3968], [-768, 3968]],
     floor=UP, ceiling=1216, theme='theme:rock', ambient=16,
     notes="The top of the ramp: a ledge 384 wide along the perch hall's north side, open over the hall, then north along a ledge walk to the roost.")
room('room:roost', 'The roost',
     outline=[[640, 4480], [2176, 4480], [2176, 5760], [2048, 5888], [768, 5888], [640, 5760]],
     floor=UP, ceiling=1792, theme='theme:rock', ambient=20,
     ceiling_levels=[{'outline': CRACK, 'ceiling': 2304, 'edge': ROCK, 'surface': SKY,
                      'notes': "The crack of sky: a chimney 512 high whose top is open to the Darkside's day (2,944 at first: only a sliver of sky showed from the floor)."}],
     platforms=[{'id': 'platform:snow', 'outline': CRACK, 'rise': 8, 'surface': SNOW, 'top_surface': SNOW,
                 'notes': "Snow sifted down the crack onto the droppings (a floor, no weather indoors)."}]
     + [{'id': f'platform:heap_{k}', 'outline': octo(x, y, HEAP_R), 'rise': HEAP_RISE, 'surface': ROCK,
         'top_surface': ROCKFLR, 'notes': f"The {k} roosting rock's foot: worn rock that stays as dust when the rock is pounded."}
        for k, (x, y), _ in ROCKS]
     + [{'id': f'platform:rock_{k}', 'outline': octo(x, y, ROCK_R), 'base': HEAP_RISE, 'rise': rise, 'surface': ROCK,
         'top_surface': ROCK, 'notes': f"The {k} roosting rock, worn smooth by claws" + (" (the highest: the Overlord's)." if k == 'high' else ".")}
        for k, (x, y), rise in ROCKS],
     notes="A tall cave, 1,536 by 1,408 and 1,152 high, under a crack of sky: snow sifted onto the droppings below it, a ring of five roosting rocks worn smooth round it, the highest in the north-east where the Overlord sits. The nest opens north.")
room('room:nest', 'Nest of shiny things',
     outline=[[1088, 6016], [1728, 6016], [1728, 6400], [1600, 6528], [1216, 6528], [1088, 6400]],
     floor=UP, ceiling=960, theme='theme:nest', ambient=18,
     platforms=[{'id': 'platform:nest', 'outline': octo(1408, 6300, 144), 'rise': 32, 'surface': POLE,
                 'top_surface': STRAW, 'notes': "The nest: straw and sticks heaped with spoons, buckles, broken mirrors; Caleb's glass in the middle."}],
     notes="A hollow behind the roost, 640 by 512, lined with straw: the gargoyles' nest of shiny things.")

op('open:mouth_slope', 'room:mouth', 'room:guano_slope', link='link:mouth_slope', width=320, height=384)
op('open:slope_bones', 'room:guano_slope', 'room:bone_ledge', link='link:slope_bones', width=256, height=320,
   notes="The cleft off the slope's west wall.")
op('open:slope_perch', 'room:guano_slope', 'room:perch_hall', link='link:slope_perch', width=320, height=384)
op('open:perch_still', 'room:perch_hall', 'room:still_gallery', link='link:perch_still', width=384, height=448)
op('open:perch_ramp', 'room:perch_hall', 'room:rock_ramp', link='link:perch_up', width=224, height=320,
   from_wall=3, to_wall=7,
   notes="The foot of the rock ramp in the hall's west wall.")
op('open:ramp_upper', 'room:rock_ramp', 'room:upper_perches', link='link:perch_up', width=224, height=320,
   from_wall=3, to_wall=5,
   notes="The top of the rock ramp.")
op('open:perch_upper', 'room:perch_hall', 'room:upper_perches', link='link:upper_overlook', width='full',
   height='full', notes="The upper perches' lip, 640 over the perch hall's floor.")
op('open:still_steps', 'room:still_gallery', 'room:rock_steps', link='link:still_up', width=288, height=384)
op('open:steps_roost', 'room:rock_steps', 'room:roost', link='link:still_up', width=288, height=384)
op('open:upper_roost', 'room:upper_perches', 'room:roost', link='link:upper_roost', width=320, height=448)
op('open:roost_nest', 'room:roost', 'room:nest', link='link:roost_nest', width=288, height=288)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:rock', 'ambient': 16}, 'rooms': rooms,
             'openings': openings,
             'notes': "DD-23 Gargoyle Lair: x east, y north; the mouth (floor 0) south, the roost (floor 640) north under its crack of sky. Written by output/studio_cal/dd23/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:mouth': 0, 'room:guano_slope': 0, 'room:bone_ledge': 0, 'room:perch_hall': 0, 'room:rock_ramp': 0,
          'room:still_gallery': 0, 'room:rock_steps': 0, 'room:upper_perches': UP, 'room:roost': UP, 'room:nest': UP}
# (id, name, kind, size, purpose, [(row name, level, count)])
PLAN_SPACES = [
    ('room:mouth', 'Cave mouth', 'room', 'S', "The arrival (entrance:d4_mouth): the mouth white with droppings, daylight behind, the cave bending up and in. Quiet (D-11.3).", []),
    ('room:guano_slope', 'Guano slope', 'corridor', 'M', "A passage slick with droppings, scratched by claws; gargoyles that heard the party come down from the dark.", [('Mountain Gargoyle', 30, 3)]),
    ('room:bone_ledge', 'Bone ledge', 'room', 'S', "A dead end with a chest: a side cleft where a climber died; his bones, rope and pack (the chest).", [('Mountain Gargoyle', 30, 1)]),
    ('room:perch_hall', 'Perch hall', 'room', 'M', "A high cave with perches round its walls where the young ones sit; the upper perches look down from its north side.", [('Mountain Gargoyle', 30, 2), ('Gargoyle Sentinel', 38, 1)]),
    ('room:rock_ramp', 'Rock ramp', 'corridor', 'S', "A ramp of broken rock climbing 640 behind the hall's west wall to the upper perches.", []),
    ('room:still_gallery', 'Still gallery', 'room', 'M', "Weathered rock pillars like statues, three of the still shapes gargoyles; the rock steps climb from its end.", [('Mountain Gargoyle', 30, 3)]),
    ('room:rock_steps', 'Rock steps', 'corridor', 'S', "Rock steps climbing 640 north from the still gallery to the roost.", []),
    ('room:upper_perches', 'Upper perches', 'corridor', 'M', "The top of the ramp: a ledge walk over the perch hall to the roost.", [('Mountain Gargoyle', 30, 1)]),
    ('room:roost', 'The roost', 'room', 'L', "A tall cave under a crack of sky, snow on the droppings below it, a ring of roosting rocks worn smooth (a click breaks them); the Overlord on the highest.", [('Gargoyle Overlord', 45, 1), ('Gargoyle Sentinel', 38, 1), ('Mountain Gargoyle', 30, 2)]),
    ('room:nest', 'Nest of shiny things', 'room', 'S', "A hollow behind the roost lined with straw: spoons, buckles, broken mirrors (the chest), and Caleb's glass in the middle (q-d15.glass).", []),
]


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pop in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if pop:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [n, n], 'levels': [lv, lv],
                                'notes': f"{n} {row} {lv} (placed)."} for row, lv, n in pop]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:mouth_slope', 'from': 'room:mouth', 'to': 'room:guano_slope', 'kind': 'open'},
        {'id': 'link:slope_bones', 'from': 'room:guano_slope', 'to': 'room:bone_ledge', 'kind': 'open'},
        {'id': 'link:slope_perch', 'from': 'room:guano_slope', 'to': 'room:perch_hall', 'kind': 'open'},
        {'id': 'link:perch_still', 'from': 'room:perch_hall', 'to': 'room:still_gallery', 'kind': 'open'},
        {'id': 'link:perch_up', 'from': 'room:perch_hall', 'to': 'room:upper_perches', 'kind': 'ramp',
         'notes': "By the rock ramp (its own room)."},
        {'id': 'link:upper_overlook', 'from': 'room:upper_perches', 'to': 'room:perch_hall', 'kind': 'overlook',
         'notes': "The upper perches' lip over the hall (a drop of 640 for whoever steps off)."},
        {'id': 'link:still_up', 'from': 'room:still_gallery', 'to': 'room:roost', 'kind': 'stairs',
         'notes': "By the rock steps (their own room)."},
        {'id': 'link:upper_roost', 'from': 'room:upper_perches', 'to': 'room:roost', 'kind': 'open'},
        {'id': 'link:roost_nest', 'from': 'room:roost', 'to': 'room:nest', 'kind': 'open'},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "A cave in Magic Mountain's eastern crags, its mouth white with droppings. It climbs from the guano slope through the perch hall, where the young gargoyles sit on ledges, to the roost under a crack of sky: a ring of roosting rocks worn smooth, snow on the droppings, the Overlord on the highest rock. Behind it, the gargoyles' nest of shiny things holds Caleb's magnifying glass.",
        'purpose': "Q-D15 Caleb's Magnifying Glass (Caleb, D3): destroy the roost (q-d15.roost, a click; the source asked) and take the glass from the nest (q-d15.glass). Party 35 to 39, D4's gargoyles 30/38/45 (15 placed, D-39), treasure level 4.",
        'mood': "Wind at the mouth and down the crack, claws on rock, droppings and bones; the Darkside's grey day falling through the crack onto snow.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:climb', 'spaces': ['room:perch_hall', 'room:rock_ramp', 'room:upper_perches',
                                                  'room:roost', 'room:rock_steps', 'room:still_gallery'],
                   'notes': "Up by the ramp and the ledge walk, down by the rock steps and the still gallery (or the other way)."}],
        'entrances': [{'id': 'entrance:d4_mouth', 'space': 'room:mouth', 'kind': 'both', 'neighbour': 'exit:d4_mouth',
                       'facing': 'n',
                       'how': "From and to D4's entrance:dd23_lair, the open cave mouth in Magic Mountain's eastern crags: 256 inside the mouth, facing north up the cave; daylight behind."}],
        'critical_path': ['room:mouth', 'room:guano_slope', 'room:perch_hall', 'room:rock_ramp',
                          'room:upper_perches', 'room:roost', 'room:nest'],
        'return_path': ['room:nest', 'room:roost', 'room:rock_steps', 'room:still_gallery', 'room:perch_hall',
                        'room:guano_slope', 'room:mouth'],
        'goals': [
            {'id': 'goal:roost', 'space': 'room:roost', 'kind': 'use', 'story': 'Q-D15',
             'what': "The roosting rocks: 'Do you wish to destroy the Gargoyle Lair?' Yes pounds them to powder (A3's hook q-d15.roost).",
             'gives': {'qbit': 'lair_destroyed'}},
            {'id': 'goal:glass', 'space': 'room:nest', 'kind': 'take', 'story': 'Q-D15',
             'what': "Caleb's Magnifying Glass in the nest (A3's hook q-d15.glass).", 'gives': {'qbit': 'glass_found'}},
        ],
        'set_pieces': [
            {'id': 'set:roost', 'kind': 'scripted', 'spaces': ['room:roost'],
             'rule': "The roosting rocks stand in a ring under the crack of sky; a click on any of them breaks all five (destructibles, kept broken by the map); their worn feet stay as dust."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 10, 'sectors': 10, 'monsters_about': 15, 'chests': 2, 'doors': 0, 'loops': 1,
                   'floor_area_munits2': 9},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors; D-39 (4): no doors, a natural cave, one exception line in NOTES.md). From the MU-6 graph devdocs/xeen/mockups/act4_graphs/dd23.graph.yml and D-39 (act4_a7_decisions.md, DD-23). The graph's rock ramp and rock steps are their own rooms (10).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-23 Gargoyle Lair (not to scale; plan, north up)
  floor 640                         [NEST: Caleb's glass, chest]
                                         |
     [UPPER PERCHES ======]--ledge--[THE ROOST: rocks in a ring, crack of sky, snow; Overlord]
      ^ramp |  lip (drop 640)                  ^ rock steps
  floor 0  ramp [PERCH HALL: perches]----[STILL GALLERY: pillars]
                       |
  [bone ledge]--[GUANO SLOPE]
                       |
                  [CAVE MOUTH] =exit= (D4: entrance:dd23_lair, the crags)
"""

# ================================================================================================ objects
ARRIVAL = [0, 256]
objects = {'format': 0}
objects['start'] = {'room': 'room:mouth', 'at': ARRIVAL, 'facing': 'n',
                    'notes': "entrance:d4_mouth: 256 inside the cave mouth, facing north up the cave (D4's door:dd23 arrives here)."}
objects['arrivals'] = [{'entrance': 'entrance:d4_mouth', 'room': 'room:mouth', 'at': ARRIVAL, 'facing': 'n',
                        'notes': "256 inside the mouth, facing north up the cave; daylight behind (D4's door:dd23)."}]


def light(id, rm, at, h, r, col, **kw):
    # `h` absolute; a light's `height` is over its room's floor (XD-26's lamp rule note).
    floor = next(x.get('floor', 0) for x in rooms if x['id'] == rm)
    d = {'id': id, 'room': rm, 'at': at, 'height': h - floor, 'radius': r, 'color': col}
    d.update(kw)
    return d


DAY = [124, 118, 106]     # the Darkside's dim amber day (DD-13's gateway daylight, a little brighter)
CAVE = [92, 92, 104]
objects['lights'] = [
    light('light:mouth', 'room:mouth', [0, 160], 260, 1000, DAY, notes="The Darkside's day from the mouth."),
    light('light:slope', 'room:guano_slope', [0, 1536], 300, 1000, CAVE),
    light('light:bones', 'room:bone_ledge', [-760, 1536], 260, 600, CAVE),
    light('light:perch', 'room:perch_hall', [-64, 2752], 640, 1500, CAVE),
    light('light:ramp', 'room:rock_ramp', [-1088, 3168], 560, 800, CAVE),
    light('light:gallery', 'room:still_gallery', [1280, 2880], 420, 1100, CAVE),
    light('light:steps', 'room:rock_steps', [1536, 3840], 560, 800, CAVE),
    light('light:upper', 'room:upper_perches', [-128, 3776], 1000, 1000, CAVE),
    light('light:ledge_walk', 'room:upper_perches', [320, 4500], 1000, 800, CAVE),
    light('light:crack', 'room:roost', CRACK_MID, 1700, 1700, [140, 134, 124],
          notes="The Darkside's day falling through the crack onto the snow."),
    light('light:roost', 'room:roost', [1408, 4720], 1150, 1100, CAVE),
    light('light:nest', 'room:nest', [1408, 6200], 880, 650, [112, 106, 98]),
]
objects['sounds'] = [
    {'id': 'sound:wind_mouth', 'room': 'room:mouth', 'at': [0, 300], 'sound': 'whistling wind', 'radius': 1400,
     'inner_radius': 500, 'volume': 0.5, 'notes': "Wind in the mouth."},
    {'id': 'sound:wind_crack', 'room': 'room:roost', 'at': CRACK_MID, 'sound': 'whistling wind', 'radius': 2200,
     'inner_radius': 700, 'volume': 0.6, 'notes': "Wind down the crack of sky."},
]
objects['exits'] = [
    {'id': 'exit:mouth', 'room': 'room:mouth', 'wall': 'south', 'size': [384, 320], 'surface': S('7solid01', 256, 256, fit=True, uneven=True),
     'to': 'exit:d4_mouth', 'notes': "The cave mouth onto D4's crags (the Darkside's day)."},
]
objects['chests'] = [
    {'id': 'chest:climber', 'room': 'room:bone_ledge', 'at': [-990, 1700], 'facing': 'w', 'treasure_level': 4,
     'random_items': 1, 'gold': 600, 'notes': "A dead climber's pack."},
    {'id': 'chest:nest', 'room': 'room:nest', 'at': [1660, 6250], 'treasure_level': 4,
     'random_items': 2, 'gold': 1000, 'trap_level': 3,
     'notes': "The gargoyles' hoard in the nest: spoons, buckles, broken mirrors, a lady's comb."},
]
objects['destructibles'] = [
    {'id': f'destructible:rock_{k}', 'of': f'platform:rock_{k}', 'hp': 500, 'trigger_only': True,
     'material': 'stone', 'sound': 'xeen/xeen_sphinx_stir.wav',
     'notes': f"The {k} roosting rock: pounded to powder by a click (the world's stone grinding; MM9's stonecrumble is not Xeen's)."}
    for k, _, _ in ROCKS]

# D4's gargoyles (A2's Gargoyles (Magic Mountain), block 11550): Mountain Gargoyle 30 (11550) x 12, Gargoyle Sentinel
# 38 (11551) x 2, Gargoyle Overlord 45 (11552) x 1 on the highest rock. All placed (D-39 (1)-(2)); groups by room.
MG, GS, GO = 11550, 11551, 11552
objects['monsters'] = []


def mon(id, rm, kind, at, group, facing=270, **kw):
    d = {'id': id, 'room': rm, 'monster': kind, 'at': at, 'facing': facing, 'hostile': True, 'group': group}
    d.update(kw)
    objects['monsters'].append(d)


mon('monster:slope_1', 'room:guano_slope', MG, [-240, 1204], 10)
mon('monster:slope_2', 'room:guano_slope', MG, [230, 1172], 10)
mon('monster:slope_3', 'room:guano_slope', MG, [-198, 1008], 10)
mon('monster:bones', 'room:bone_ledge', MG, [-640, 1600], 11, facing=0)
mon('monster:perch_w', 'room:perch_hall', MG, [-672, 3136], 12, facing=0, floor_height=352,
    notes="On the west wall's perch.")
mon('monster:perch_se', 'room:perch_hall', MG, [448, 2400], 12, facing=90, floor_height=320,
    notes="On the south wall's perch.")
mon('monster:perch_sentinel', 'room:perch_hall', GS, [-224, 3000], 12, notes="A Gargoyle Sentinel (38).")
mon('monster:still_1', 'room:still_gallery', MG, [1250, 2450], 13, facing=180)
mon('monster:still_2', 'room:still_gallery', MG, [1750, 2700], 13, facing=180)
mon('monster:still_3', 'room:still_gallery', MG, [1300, 2950], 13, facing=180)
mon('monster:upper', 'room:upper_perches', MG, [320, 4300], 14)
mon('monster:overlord', 'room:roost', GO, [1920, 5600], 15, floor_height=UP + HEAP_RISE + 432,
    notes="The roost's elder: a Gargoyle Overlord (45) on the highest rock (D-39 (2), no boss row).")
mon('monster:roost_sentinel', 'room:roost', GS, [1408, 4800], 15, notes="A Gargoyle Sentinel (38).")
mon('monster:roost_1', 'room:roost', MG, [950, 5300], 15)
mon('monster:roost_2', 'room:roost', MG, [1650, 4800], 15)

objects['decorations'] = [
    {'id': 'deco:mouth_bones', 'room': 'room:mouth', 'decoration': 'dec29', 'at': [-300, 560]},
    {'id': 'deco:mouth_rock', 'room': 'room:mouth', 'decoration': '6rock02', 'at': [300, 600]},
    {'id': 'deco:slope_bones', 'room': 'room:guano_slope', 'decoration': '7dec18', 'at': [250, 1500]},
    {'id': 'deco:climber', 'room': 'room:bone_ledge', 'decoration': 'Corpse05', 'at': [-900, 1420],
     'notes': "The climber, long dead, still roped to his pack."},
    {'id': 'deco:perch_mite_1', 'room': 'room:perch_hall', 'decoration': 'stlmite1', 'at': [-680, 2780]},
    {'id': 'deco:perch_mite_2', 'room': 'room:perch_hall', 'decoration': 'stlmite2', 'at': [520, 3340]},
    {'id': 'deco:perch_skulls', 'room': 'room:perch_hall', 'decoration': 'sklplrev', 'at': [-480, 3360]},
    {'id': 'deco:gallery_mite', 'room': 'room:still_gallery', 'decoration': 'stlmite1', 'at': [1700, 3100]},
    {'id': 'deco:upper_bones', 'room': 'room:upper_perches', 'decoration': 'dec29', 'at': [-620, 3880],
     'floor_height': UP},
    {'id': 'deco:roost_bones', 'room': 'room:roost', 'decoration': '7dec18', 'at': [2080, 4580], 'floor_height': UP},
    {'id': 'deco:roost_skulls', 'room': 'room:roost', 'decoration': 'sklplrev', 'at': [792, 5738],
     'floor_height': UP},
    {'id': 'deco:nest_skull', 'room': 'room:nest', 'decoration': '7dec20', 'at': [1200, 6420], 'floor_height': UP},
]

# ================================================================================================ wiring
roost_effects = [{'lua': 'XeenQuests.hook("q-d15.roost")'}] + [
    {'destroy': f'destructible:rock_{k}'} for k, _, _ in ROCKS]
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'text': "The cave in the crag runs up into the mountain, its floor white with droppings. Somewhere above, claws scrape on rock.",
     'seconds': 7},
    {'id': 'evt:mouth', 'preset': 'exit', 'source': 'exit:mouth', 'title': 'Leave the Gargoyle Lair',
     'notes': "To D4's entrance:dd23_lair before the lair's mouth (exit:d4_mouth)."},
    {'id': 'evt:bones_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:bone_ledge', 'once': True,
     'text': "A climber's bones lie in the cleft, still roped to his pack.", 'seconds': 5},
    {'id': 'evt:perch_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:perch_hall', 'once': True,
     'text': "Perches worn smooth by claws stand out from the walls of a high cave. Ledges look down from the dark above.",
     'seconds': 6},
    {'id': 'evt:gallery_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:still_gallery', 'once': True,
     'text': "Weathered pillars of rock stand about the gallery like statues. Some of the statues have wings.",
     'seconds': 6},
    {'id': 'evt:roost_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:roost', 'once': True,
     'text': "The roost: a tall cave under a crack of sky, snow sifted onto the droppings. Roosting rocks stand round it in a ring, worn smooth by claws.",
     'seconds': 7},
    {'id': 'evt:nest_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:nest', 'once': True,
     'text': "Straw, and in it everything that glitters: spoons, buckles, broken mirrors. Gargoyles like shiny things.",
     'seconds': 6},
    {'id': 'evt:nest', 'preset': 'script', 'source': 'platform:nest', 'title': 'Nest',
     'effects': [{'lua': 'XeenQuests.hook("q-d15.glass")'}],
     'notes': "goal:glass: A3's hook q-d15.glass gives its text and Caleb's Magnifying Glass (12352) once (glass_found 113302); later clicks its else text \"Spoons, buckles, broken mirrors.\""},
    {'id': 'evt:chest_climber', 'preset': 'chest', 'source': 'chest:climber', 'title': 'Chest'},
    {'id': 'evt:chest_nest', 'preset': 'chest', 'source': 'chest:nest', 'title': 'Chest'},
]
for k, _, _ in ROCKS:
    for part in ('rock', 'heap'):
        events.append({
            'id': f'evt:{part}_{k}', 'preset': 'script', 'source': f'platform:{part}_{k}', 'title': 'Roosting rock',
            'condition': {'not': {'qbit': 'lair_destroyed'}},
            'effects': list(roost_effects),
            'else_effects': [{'lua': 'XeenQuests.hook("q-d15.roost")'}],
            'notes': ("goal:roost: a click calls A3's q-d15.roost (aaze0021:7, lair_destroyed 113301) and pounds all five rocks to powder (they stay broken); F47, the player's pins 2026-11-24: no Yes/No for a quest goal (the source asked \"Do you wish to destroy the Gargoyle Lair?\", dark/aaze0021:6). "
                      if part == 'rock' else "The rock's worn foot: the same click while the rock stands; after, A3's else text \"Rock dust. The gargoyles will have to sit somewhere else.\"")})
wiring = {'format': 0, 'events': events}

atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_day'},
              'notes': "The roost's crack (its ceiling level's top, sky: true) shows the Darkside's day, D4's preset by its own name (never the texture alias xeendark1, the lanes' rule). No weather indoors: the snow is the drift's floor texture under the crack (D-39)."}

QBITS = {'lair_destroyed': 113301, 'glass_found': 113302}
project = {
    'format': 0, 'id': 'xeen_dd23', 'name': 'Gargoyle Lair', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon',
    'identity': {'shape': 'cave', 'family': '7d07', 'seen': [  # D-89 (A7 s28)
        "a cave mouth white with droppings opening on the Darkside's crags",
        "dark Thunderfist rock with broken walls, floors that rise and fall and young gargoyles on rock ledges",
        "the ring of roosting rocks round the snow under the crack of sky, the Overlord on the highest"]},
    'map_code': 'DD-23', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [7, 13], 'climbs': 'n'},
    'map_stats': {'id': 9176, 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 3,
                  'perception_difficulty': 6, 'refill_days': 672, 'music': 31, 'environment': 'cave',
                  'lock_difficulty': 6, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Mountain Gargoyle', 'tier': 1, 'per_marker': [2, 3], 'weight': 100}]},
    'neighbours': [
        {'id': 'exit:d4_mouth', 'to': 'xeen_d4.odm', 'kind': 'door', 'arrival': 'entrance:dd23_lair',
         'arrival_hint': "D4's named arrival before the lair's mouth in Magic Mountain's eastern crags, (-9216, 10752, 2304) facing south (1536), at the goat path's end.",
         'notes': "D4 Lakeside and Blackfang (A6, installed): its door:dd23 (thing:dd23_lair) leads in to entrance:d4_mouth."},
    ],
    'qbits': QBITS,
    'notes': "Xeen design brief, level L4: DD-23 Gargoyle Lair in Magic Mountain's eastern crags on D4 (Q-D15 Caleb's Magnifying Glass). Monsters: A2's Gargoyles (Magic Mountain), all placed (D-39): 12 Mountain Gargoyle 11550 (30), 2 Gargoyle Sentinel 11551 (38), 1 Gargoyle Overlord 11552 (45) on the highest rock; slot 1 Xeen Mountain Gargoyle for the 10 % rest encounters (D-39, D-33/D-34). Hooks q-d15.roost (a click on the roosting rocks) and q-d15.glass (the nest); A3's player bits lair_destroyed 113301 and glass_found 113302 named; map qbits 118040-118049: none used. Music 31. No doors (D-39 (4)). The way out is live to D4's entrance:dd23_lair; D4's door:dd23 arrives at entrance:d4_mouth (the map's start).",
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
        p['notes'] = f"Xeen design brief, level {lv}: DD-23 Gargoyle Lair (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-23 Gargoyle Lair, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

CAVES = {  # D-89 cave shape (A7 s28, tools/xeen/cave_shape.py): rough walls everywhere, floors that rise and fall,
    # vaulted roofs; the perch hall's corners stay (its ramp's openings name its walls by number)
    'room:mouth': {'floor': 48, 'roof': 160},
    'room:guano_slope': {'floor': 64, 'roof': 128},
    'room:bone_ledge': {'floor': 48, 'roof': 96},
    'room:perch_hall': {'floor': 96, 'roof': 256},
    'room:still_gallery': {'floor': 64, 'roof': 192},
    'room:upper_perches': {'floor': 32, 'roof': 192},
    'room:roost': {'floor': 64},
    'room:nest': {'floor': 32, 'roof': 96},
}
write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('atmosphere.yml', atmosphere),
                     ('diagram.txt', DIAGRAM)])
sys.path.insert(0, str(R / 'tools' / 'xeen'))
import cave_shape  # noqa: E402
cave_shape.shape_l4(BRIEF / 'L4', CAVES)
print('written L4')
