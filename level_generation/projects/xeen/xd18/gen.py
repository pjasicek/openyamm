#!/usr/bin/env python3
"""XD-18 Dragon Cave: writes the L1-L4 project folders of devdocs/xeen/briefs/xd18 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, atmosphere.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here; never hand-edit the written files (diff L4 against L4/.oymap/last first).
Written by lane A7's sub-agent for XD-18 (seventeenth session, 2026-11-21) after FD-02's gen.py, on D-57
(devdocs/xeen/mockups/act6_a7_decisions.md), which wins over act6_graphs/xd18.graph.yml.

Frame: x east, y north, z up; z 0 is X7's mouth floor (2,150 on X7). Floor 0 (the mouth and the upper halls) lies in
the south band: the mouth at the west end, the tax office, the scorched passage, the bone hall, the hollows and vents,
the fire crossing, the egg cave and the stair head in the east. The walked stair runs north from the stair head down
1,024 to the stair foot (floor -1, z -1,024). Floor -1 lies in the north band: the great roost (z -1,024 to 1,024,
the floor-0 ledge along its south wall), the steaming pools, the east den and the old roost east and north of it, the
ember gallery, the library, the King's door, the Dragon King's hall and the hoard west of it, the starwell, the frost
den and the rime cave north of them. Rooms stand 128 apart (the walls' thickness); no room of one floor lies over a
room of the other.

D-32: the dragons are 487 high (radius 238). Every party passage between dragon halls is 288 high; the dragon roads
(768) join only the bone hall, the roost (its ledge), the ember gallery and the starwell."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd18'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM8 Dragon Cave d17 (three textures: t68a02b walls, roofs and floors; t68a02a worn floors and the dragon roads;
# solid01 not used) and MM8 Dragon Hunter's Camp d16 for the worked rooms (D-57 Q6); Xeen's xodaylt (the mouth's
# daylight), xkportc (the hoard's grate), xncoins (the King's gold); wtrtyl for the pools.
ROCK = S('t68a02b', 256, 256)
WORN = S('t68a02a', 256, 256)
WALL = S('gtrlwal3', 128, 256)
FLAG = S('gtrlflr', 128, 128)
SLAB = S('tfb11', 128, 128)
ROOF2 = S('gtrlrf2', 128, 128)
ROOF3 = S('gtrlrf3', 128, 128)
TRIM = S('gtrltrm2', 64, 32)
BOOKS = S('t1books', 128, 256)
WOOD = S('gtrlrf3', 128, 128)
TRIM9 = S('trim9_32', 32, 64)
LEAF_L = S('gkp103a', 128, 256)
LEAF_R = S('gkp103b', 128, 256)
DAYLIGHT = S('xodaylt', 256, 128, fit=True, uneven=True)
GRATE = S('xkportc', 256, 256)
COINS = S('xncoins', 128, 128)
WATER = {'texture': 'wtrtyl', 'liquid': 'water'}
STARS = S('t68a02b', 256, 256, sky=True)

themes = [
    {'id': 'theme:cave', 'wall': ROCK, 'floor': ROCK, 'ceiling': ROCK, 'reveal': ROCK, 'door': LEAF_L,
     'notes': "The Dragon Cave's rock (MM8 d17 t68a02b) on walls, roofs and floors."},
    {'id': 'theme:road', 'wall': ROCK, 'floor': WORN, 'ceiling': ROCK, 'reveal': ROCK, 'door': LEAF_L,
     'notes': "Where the dragons go: the floor worn smooth (t68a02a)."},
    {'id': 'theme:office', 'wall': ROCK, 'bands': [{'height': 32, 'surface': TRIM}], 'floor': WORN,
     'ceiling': ROCK, 'reveal': WOOD, 'door': LEAF_L,
     'notes': "The Dragon Tax Office and its waiting room, carved into the cave's rock (D-89 identity, 2026-11-22): d17 rock (t68a02b) on walls and roof over a timber skirting, the floor worn smooth (t68a02a); the counter, benches, urn and Scaldrith's door are the plank fittings."},
    {'id': 'theme:library', 'wall': ROCK,
     'bands': [{'height': 32, 'surface': TRIM}, {'height': 288, 'surface': BOOKS}], 'floor': WORN,
     'ceiling': ROCK, 'reveal': WOOD, 'door': LEAF_L,
     'notes': "The library of Dragon Lore and the King's door, cut into the rock (D-89 identity): a course of bookshelves round the walls (t1books) with rock above them and over the roof (t68a02b), the floor worn smooth."},
    {'id': 'theme:scorch', 'wall': S('xochar', 128, 128), 'floor': WORN, 'ceiling': S('xochar', 128, 128),
     'reveal': ROCK, 'door': LEAF_L,
     'notes': "Rock blackened by breath (xochar) behind the inner door: the dragons' side starts here."},
    {'id': 'theme:hoard', 'wall': ROCK, 'floor': COINS, 'ceiling': ROCK, 'reveal': ROCK, 'door': LEAF_L,
     'notes': "The King's hoard: gold underfoot (xncoins) under the cave's rock."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


F0 = 0          # the mouth and the upper halls
F1 = -1024      # the deep roosts
ROUGH = {'step': 192, 'depth': 40}
rooms = []
openings = []
ROOMS = {}


def room(id, name, outline, floor, ceiling, theme, **kw):
    d = {'id': id, 'name': name, 'outline': outline, 'floor': floor, 'ceiling': ceiling, 'theme': theme}
    d.update(kw)
    rooms.append(d)
    ROOMS[id] = d
    return d


def op(id, frm, to, **kw):
    d = {'id': id, 'from': frm, 'to': to}
    d.update(kw)
    openings.append(d)


def panel(pid, offset, length, bottom, height, surface, **kw):
    d = {'offset': offset, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    if pid:
        d['id'] = pid
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ floor 0
room('room:mouth', 'Cave mouth', rect(0, -3456, 1024, -2688), F0, 640, 'theme:road', ambient=20,
     notes="The arrival (entrance:x7_mouth): X7's daylight behind (west), scorched rock and gnawed bones, the office's front ahead (east). Quiet (D-11.3).")
room('room:tax_hall', 'Tax office hall', rect(1152, -3712, 2688, -2432), F0, 384, 'theme:office',
     walls=[{'wall': 's', 'panels': [
         panel('door:tax_office', 640, 128, 0, 256, dict(LEAF_L, fit=True),
               notes="The Dragon Tax Office's door (house 4852, Scaldrith; the left wing)."),
         panel('panel:tax_office_r', 768, 128, 0, 256, dict(LEAF_R, fit=True), notes="The office door's right wing.")]}],
     platforms=[
         {'id': 'platform:counter', 'at': [1536, -3632], 'size': [384, 96], 'rise': 104, 'surface': WOOD,
          'top_surface': SLAB, 'notes': "The counter by the office door, the brass urn on its sill (q-c25.urn)."},
         {'at': [2368, -3632], 'size': [384, 64], 'rise': 48, 'surface': WOOD, 'top_surface': WOOD,
          'notes': "A bench by the south wall."},
         {'at': [1408, -2512], 'size': [384, 64], 'rise': 48, 'surface': WOOD, 'top_surface': WOOD,
          'notes': "A bench by the north wall."},
     ],
     ambient=18, notes="D-5.2: the Dragon Tax Office's public hall in d16's stone, 384 high: Scaldrith's door (house 4852) and the urn on the counter in the south wall, benches, the waiting room's door north, the inner door east. Quiet.")
room('room:waiting', 'Waiting room', rect(1408, -2304, 2432, -1664), F0, 320, 'theme:office',
     platforms=[
         {'id': 'platform:lectern', 'at': [1920, -1792], 'size': [128, 128], 'rise': 112, 'surface': WOOD,
          'top_surface': {'texture': 'xnpbook', 'size': [128, 128], 'offset': [64, 64]}, 'notes': "The lectern: Dragon Lore, volume 1 (q-c25.volume1)."},
         {'at': [1472, -1984], 'size': [64, 384], 'rise': 48, 'surface': WOOD, 'top_surface': WOOD,
          'notes': "A bench by the west wall."},
         {'at': [2368, -1984], 'size': [64, 384], 'rise': 48, 'surface': WOOD, 'top_surface': WOOD,
          'notes': "A bench by the east wall."},
     ],
     ambient=18, notes="Off the hall behind a door: benches by the walls, a lamp, the lectern with Dragon Lore, volume 1. A dead end with a goal. Quiet.")
room('room:scorch', 'Scorched passage', rect(2816, -3264, 3840, -2880), F0, 288, 'theme:scorch', ambient=10,
     notes="Behind the inner door: a low passage (384 wide, 288 high) of rock blackened by breath. Its far opening is D-32's first low opening: the bone hall's dragons cannot follow into the office. Quiet.")
room('room:bone_hall', 'Bone hall', rect(3968, -3840, 6016, -2304), F0, 1280, 'theme:road', ambient=10,
     notes="The first dragons: a hall 2,048 by 1,536 and 1,280 high, floored with gnawed bones and broken armour. A low opening to the hollows (south); the dragon road (768) up to the roost ledge (north).")
room('room:hollows', 'Acid hollows', rect(3968, -5376, 5504, -3968), F0, 1024, 'theme:cave', rough=ROUGH,
     ambient=8, notes="Hollows eaten into the rock, 1,024 high: three young Acid Dragons. Low crawls west to the last taxpayer and east to the sulphur vents.")
room('room:last', 'The last taxpayer', rect(2560, -5120, 3840, -4352), F0, 512, 'theme:cave', rough=ROUGH,
     platforms=[{'id': 'platform:knight', 'at': [2720, -4736], 'size': [192, 288], 'rise': 24, 'surface': WORN,
                 'top_surface': WORN, 'notes': "A knight's remains in good armour, his strongbox by them: the receipt (q-c25.receipt)."}],
     ambient=8, notes="A dead end with a chest: the knight's remains, his strongbox, and under it a receipt from the tax office.")
room('room:vents', 'Sulphur vents', rect(5632, -5248, 9600, -3968), F0, 1024, 'theme:cave', rough=ROUGH,
     ambient=10, notes="Yellow steam hissing from cracks along the floor (smoke, no damage), 1,024 high; two Acid Dragons. A low opening east to the stair head (the floor-0 loop).")
room('room:crossing', 'Fire crossing', rect(8320, -2304, 9600, -1152), F0, 1024, 'theme:cave', rough=ROUGH,
     ambient=12, notes="A cave 1,024 high where the roost's warm air rises through cracks; a Fire Dragon pair. Low openings west onto the roost ledge, south to the egg cave, east to the stair head.")
room('room:egg', 'Egg cave', rect(8320, -3584, 9600, -2432), F0, 896, 'theme:cave', rough=ROUGH,
     levels=[{'id': 'level:nest', 'outline': rect(8704, -3200, 9216, -2816), 'floor': F0 - 48, 'surface': WORN,
              'bank': 64, 'notes': "The scraped hollow of the nest."}],
     ambient=12, notes="A warm dead end, 896 high: a scraped hollow (the eggs: S's decoration), the mother on guard, a chest of her hoard by the wall.")
room('room:head', 'Stair head', rect(9728, -4480, 10368, -1664), F0, 384, 'theme:road', ambient=10,
     notes="A low tunnel (384 high: no dragon uses it) joining the fire crossing and the sulphur vents; the walked stair goes down from its north end.")
room('room:stair', 'The walked stair', rect(9856, -1536, 10240, 512), F0, 384, 'theme:road',
     slope={'to': F1, 'toward': 'north', 'steps': 32}, ceiling_slope={'to': F1 + 384, 'toward': 'north'},
     ambient=10, notes="Rough steps, 32 of 32, down 1,024 north in a tunnel 384 high: no dragon uses it, so the two floors keep their own dragons. Walked (D-47).")
# ------------------------------------------------------------------------------------------------ floor -1
LEDGE_Y = -1792
LIP = 128
room('room:roost', 'The great roost', rect(5120, -2176, 8192, 512), F1, 1024, 'theme:road',
     levels=[{'id': 'level:ledge', 'outline': rect(5120, -2176, 8192, LEDGE_Y), 'floor': F0, 'surface': WORN,
              'edge': ROCK, 'notes': "The roost ledge (floor 0), 384 wide along the south wall."}],
     platforms=[{'id': 'platform:lip', 'at': [6656, LEDGE_Y - 24], 'size': [3040, 16], 'base': F0 - F1, 'rise': LIP,
                 'surface': ROCK, 'top_surface': ROCK,
                 'notes': "The ledge's rock lip on its edge (D-57: it stops a walking party; 192 if it does not)."}],
     ambient=8, notes="Set piece: a cavern 3,072 by 2,688 and 2,048 high through both floors, the floor-0 ledge along its south wall behind a rock lip, scales on the floor. Three pairs of dragons. The party comes in by low openings (the stair foot east, the old roost north); the dragon roads to the bone hall (the ledge), the ember gallery (west) and the starwell (north) are 768.")
room('room:foot', 'Stair foot',
     [[8320, -896], [8832, -896], [8832, 640], [10368, 640], [10368, 1152], [8320, 1152]], F1, F1 + 384,
     'theme:road', ambient=10,
     notes="The steps' foot: a low tunnel bent round from the stair to the roost's east wall; low openings west into the great roost and north to the steaming pools.")
room('room:pools', 'Steaming pools', rect(8320, 1280, 10624, 2304), F1, F1 + 1024, 'theme:cave', rough=ROUGH,
     levels=[{'id': 'level:pool', 'outline': rect(9088, 1536, 10112, 2048), 'floor': F1 - 64, 'surface': WATER,
              'edge': ROCK, 'notes': "The hot pool (wtrtyl: water, not lava, no damage)."}],
     ambient=10, notes="Hot pools steaming in a cave 1,024 high; three Fire Dragons bathing. Low openings south to the stair foot, east to the den, west to the old roost.")
room('room:den', 'East den', rect(10752, 1280, 11776, 2304), F1, F1 + 1024, 'theme:cave', rough=ROUGH, ambient=8,
     notes="A dead end with a chest: a den 1,024 high off the pools, its pair asleep on a scatter of coins; a low opening only.")
room('room:old_roost', 'Old roost', rect(6400, 640, 8192, 2176), F1, F1 + 1280, 'theme:road', rough=ROUGH, ambient=8,
     notes="An older roost 1,280 high, its floor worn smooth; three Fire Dragons. Low openings to the pools (east) and into the great roost (south).")
room('room:ember', 'Ember gallery', rect(3072, -768, 4992, 0), F1, F1 + 768, 'theme:road', ambient=12,
     notes="A dragon road 768 wide and high from the roost (east) to the library's east leaves, embers in the cracks; a Fire pair. The leaves are low (288), so nothing big follows inside.")
room('room:library', 'Library of Dragon Lore', rect(896, -1152, 2944, 384), F1, F1 + 1280, 'theme:library',
     platforms=[
         {'id': 'platform:shelf2', 'at': [1408, -1088], 'size': [384, 96], 'rise': 256, 'surface': BOOKS,
          'top_surface': WOOD, 'end_surface': dict(WOOD, fit=False), 'notes': "Shelf 2: Dragon Lore, volume 2."},
         {'id': 'platform:shelf3', 'at': [1920, -1088], 'size': [384, 96], 'rise': 256, 'surface': BOOKS,
          'top_surface': WOOD, 'end_surface': dict(WOOD, fit=False), 'notes': "Shelf 3: Dragon Lore, volume 3."},
         {'id': 'platform:shelf4', 'at': [2432, -1088], 'size': [384, 96], 'rise': 256, 'surface': BOOKS,
          'top_surface': WOOD, 'end_surface': dict(WOOD, fit=False), 'notes': "Shelf 4: Dragon Lore, volume 4."},
         {'id': 'platform:ledger', 'at': [1152, 0], 'size': [128, 128], 'rise': 128, 'surface': WOOD,
          'top_surface': {'texture': 'xnpbook', 'size': [128, 128], 'offset': [64, 64]}, 'notes': "The ledger stand: The Art of Taxation."},
     ],
     ambient=16, notes="Set piece and goal: a worked hall 2,048 by 1,536 and 1,280 high, shelves cut into the walls to a dragon's reach, books the size of doors on three great shelves; two Frost Dragons live here. Two pairs of leaves (east to the ember gallery, north to the frost den), low (288); the King's door antechamber west.")
room('room:kings_door', "The King's door", rect(-384, -640, 768, 128), F1, F1 + 384, 'theme:library',
     bands=[{'height': 32, 'surface': TRIM}],
     platforms=[{'id': 'platform:shelf5', 'at': [192, 80], 'size': [384, 64], 'rise': 256, 'surface': BOOKS,
                 'top_surface': WOOD, 'end_surface': dict(WOOD, fit=False),
                 'notes': "Shelf 5, by the Dragon King's door."}],
     ambient=14, notes="An antechamber off the library's west end, 384 high: shelf 5 by the King's door, two bronze leaves 384 wide and only 288 high (D-32 keeps the King in). Quiet.")
room('room:throne', "The Dragon King's hall", rect(-3200, -1280, -512, 768), F1, F1 + 1536, 'theme:hoard',
     ambient=10, notes="The boss: a hall 2,688 by 2,048 and 1,536 high, the Dragon King on a dais of heaped gold, two Frost Dragons at its feet. The only openings: the King's low door (east) and the hoard's grate behind the dais (west), which rises at his death.")
room('room:hoard', "The King's hoard", rect(-4352, -512, -3328, 256), F1, F1 + 384, 'theme:hoard', ambient=12,
     notes="Behind the dais: the hoard cave, gold on the floor (xncoins), the King's chest. Reached when the grate rises at his death.")
room('room:starwell', 'The starwell', rect(3456, 640, 6016, 2688), F1, F1 + 1536, 'theme:road',
     walls=[{'wall': 'n', 'panels': [panel('panel:slot', 256, 2048, 640, 640, STARS,
                                           notes="The slot of stars: the north wall broken open onto the void beyond X7's rim (sky: true, X7's preset; the faces stay solid).")]}],
     ambient=8, notes="Set piece: a cold hall 2,560 by 2,048 and 1,536 high whose north wall breaks open onto the void beyond X7's rim: a slot of stars 2,048 wide, its sill 640 above the floor (no one walks out). Three Frost Dragons. The dragon road from the roost (south, 768); a low opening west to the frost den.")
room('room:frost', 'Frost den', rect(1152, 512, 3328, 1792), F1, F1 + 1024, 'theme:cave', ambient=8,
     notes="White rock, 1,024 high, a Frost pair; low openings east to the starwell and west to the rime cave, and the library's north leaves (the library loop).")
room('room:rime', 'Rime cave', rect(-256, 640, 1024, 1664), F1, F1 + 1024, 'theme:cave', rough=ROUGH, ambient=8,
     notes="A dead end with a chest: icicles from a 1,024 roof, a frozen hoard, three Frost Dragons.")


LOW = 288
# floor 0
op('open:mouth_hall', 'room:mouth', 'room:tax_hall', link='link:mouth_hall', width=448, height=320,
   notes="The office front: a wide doorway in the office's stone front.")
op('open:hall_waiting', 'room:tax_hall', 'room:waiting', link='link:hall_waiting', width=256, height=256)
op('open:hall_scorch', 'room:tax_hall', 'room:scorch', link='link:hall_scorch', width=256, height=LOW,
   notes="The inner door (q-c25.inner_door).")
op('open:scorch_bone', 'room:scorch', 'room:bone_hall', link='link:scorch_bone', width=224, height=LOW,
   notes="D-32's first low opening: the bone hall's dragons stay out of the passage.")
op('open:bone_hollows', 'room:bone_hall', 'room:hollows', link='link:bone_hollows', width=256, height=LOW)
op('open:hollows_last', 'room:hollows', 'room:last', link='link:hollows_last', width=224, height=256,
   notes="The crawl to the last taxpayer.")
op('open:hollows_vents', 'room:hollows', 'room:vents', link='link:hollows_vents', width=256, height=LOW)
op('open:bone_ledge', 'room:bone_hall', 'room:roost', link='link:bone_ledge', width=768, height=768,
   along=0.5, notes="The dragon road from the bone hall onto the roost ledge (768: D-32).")
# the crossing's west wall runs from y -1152 down to -2304 (counter-clockwise); the shared stretch from -1152 to -2176
op('open:ledge_crossing', 'room:crossing', 'room:roost', link='link:ledge_crossing', width=256, height=LOW,
   along=round((-1152 - (-1984)) / 1024, 4), notes="From the ledge's east end into the fire crossing: low (288).")
op('open:crossing_egg', 'room:crossing', 'room:egg', link='link:crossing_egg', width=256, height=LOW,
   from_wall='s', to_wall='n')
op('open:crossing_head', 'room:crossing', 'room:head', link='link:crossing_head', width=256, height=LOW)
op('open:vents_head', 'room:vents', 'room:head', link='link:vents_head', width=256, height=LOW)
op('open:head_stair', 'room:head', 'room:stair', link='link:stair_down', width=320, height=LOW)
op('open:stair_foot', 'room:stair', 'room:foot', link='link:stair_foot', width=320, height=LOW)
# floor -1
op('open:foot_roost', 'room:foot', 'room:roost', link='link:foot_roost', width=256, height=LOW)
op('open:foot_pools', 'room:foot', 'room:pools', link='link:foot_pools', width=256, height=LOW)
op('open:pools_den', 'room:pools', 'room:den', link='link:pools_den', width=256, height=LOW)
op('open:pools_old', 'room:pools', 'room:old_roost', link='link:pools_old', width=256, height=LOW)
op('open:old_roost', 'room:old_roost', 'room:roost', link='link:old_roost', width=256, height=LOW)
op('open:roost_ember', 'room:roost', 'room:ember', link='link:roost_ember', width='full', height='full',
   notes="The dragon road west (768).")
op('open:roost_starwell', 'room:roost', 'room:starwell', link='link:roost_starwell', width=768, height=768,
   notes="The dragon road north (768).")
op('open:ember_library', 'room:ember', 'room:library', link='link:ember_library', width=384, height=LOW,
   notes="The library's east leaves (low, D-32).")
op('open:starwell_frost', 'room:starwell', 'room:frost', link='link:starwell_frost', width=256, height=LOW)
op('open:frost_rime', 'room:frost', 'room:rime', link='link:frost_rime', width=256, height=LOW)
op('open:frost_library', 'room:frost', 'room:library', link='link:frost_library', width=384, height=LOW,
   notes="The library's north leaves (low).")
op('open:library_kings', 'room:library', 'room:kings_door', link='link:library_kings', width=320, height=LOW)
op('open:kings_throne', 'room:kings_door', 'room:throne', link='link:kings_throne', width=384, height=LOW,
   notes="The King's door: two bronze leaves 384 wide and 288 high (D-32).")
op('open:throne_hoard', 'room:throne', 'room:hoard', link='link:throne_hoard', width=256, height=LOW,
   notes="The hoard's grate behind the dais.")

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:cave', 'ambient': 10}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-18 Dragon Cave: x east, y north; floor 0 (z 0) in the south band from the mouth (west) to the stair head (east), floor -1 (z -1,024) north of it, the great roost through both. Written by output/studio_cal/xd18/tools/gen.py."}

# ================================================================================================ plan.yml
ACID, FIRE, FROST, KING = 11641, 11642, 11643, 11645
PLACED = [  # room, [(group, row, (x, y), facing)]
    ('bone_hall', [(10, ACID, (4464, -3436), 90), (10, ACID, (4900, -3100), 90),
                   (14, ACID, (5400, -2560), 90), (14, ACID, (5770, -2900), 90)]),
    ('hollows', [(11, ACID, (4400, -4500), 0), (11, ACID, (4900, -4900), 0), (12, ACID, (5100, -4492), 180)]),
    ('vents', [(13, ACID, (7200, -4600), 180), (13, ACID, (7900, -4500), 180)]),
    ('crossing', [(15, FIRE, (8800, -1600), 180), (15, FIRE, (9200, -1900), 180)]),
    ('egg', [(16, FIRE, (8960, -3008), 90)]),
    ('roost', [(17, FIRE, (5800, -1000), 0), (17, FIRE, (6300, -300), 0), (18, FIRE, (7400, -800), 180),
               (18, FIRE, (6936, 36), 180), (19, FROST, (6000, 200), 270), (19, FROST, (6800, -1100), 90)]),
    ('pools', [(20, FIRE, (8764, 1624), 0), (20, FIRE, (8800, 2120), 0), (21, FIRE, (10208, 1800), 180)]),
    ('den', [(22, FIRE, (11320, 1550), 180), (22, FIRE, (11450, 2050), 180)]),
    ('old_roost', [(23, FIRE, (6900, 1100), 0), (23, FIRE, (7400, 1700), 0), (24, FIRE, (6800, 1800), 0)]),
    ('ember', [(25, FIRE, (3700, -400), 0), (25, FIRE, (4300, -380), 0)]),
    ('starwell', [(26, FROST, (4200, 1500), 90), (26, FROST, (5000, 2000), 90), (27, FROST, (5300, 1200), 90)]),
    ('frost', [(28, FROST, (1800, 1200), 0), (28, FROST, (2600, 1100), 0)]),
    ('rime', [(29, FROST, (100, 1400), 0), (29, FROST, (46, 952), 0), (30, FROST, (450, 900), 0)]),
    ('library', [(31, FROST, (1500, -300), 270), (31, FROST, (2400, -200), 270)]),
    ('throne', [(32, FROST, (-1700, 300), 0), (32, FROST, (-1700, -800), 0)]),
]
KING_AT = (-2624, -128)
# F75 (reviews/PLAYER_FEEDBACK_20261126.md, XD-18 p1 "dragon gets stuck", p2 "they get stuck"; 2026-11-26): a dragon
# (487 high, radius 238) that chases the party to one of D-32's low openings (288) stops with its middle 60 from the
# opening (the level radius limit) and its body sunk into the frame. Every dragon is leashed (2D about its post, as
# D-154 on XD-07) so that its body stays 64 clear of every opening it cannot pass; seven posts moved deeper into their
# rooms so the leash is at least 224 (bone hall 1, hollows 3, den 1, pools 1 and 3, rime 2, roost 4). Measured and
# kept by tools/xeen/check_monster_fit.py (fit.stuck); the leash is the largest that keeps clear, at most 1,536.
LEASH = {  # post -> leash
    (-1700, -800): 928, (-1700, 300): 928, (46, 952): 672, (100, 1400): 608, (450, 900): 256, (1500, -300): 416,
    (1800, 1200): 448, (2400, -200): 224, (2600, 1100): 416, (3700, -400): 448, (4200, 1500): 576,
    (4300, -380): 1024, (4400, -4500): 256, (4464, -3436): 224, (4900, -4900): 448, (4900, -3100): 544,
    (5000, 2000): 1472, (5100, -4492): 224, (5300, 1200): 1536, (5400, -2560): 1184, (5770, -2900): 1088,
    (5800, -1000): 1536, (6000, 200): 896, (6300, -300): 864, (6800, -1100): 1280, (6800, 1800): 1024,
    (6900, 1100): 320, (6936, 36): 224, (7200, -4600): 1248, (7400, -800): 608, (7400, 1700): 480,
    (7900, -4500): 1504, (8764, 1624): 224, (8800, -1600): 352, (8800, 2120): 448, (8960, -3008): 256,
    (9200, -1900): 224, (10208, 1800): 224, (11320, 1550): 256, (11450, 2050): 384,
}
KING_LEASH = 384
NAMES = {ACID: 'Acid Dragon', FIRE: 'Fire Dragon', FROST: 'Frost Dragon', KING: 'Dragon King'}
LEVELS = {ACID: 66, FIRE: 75, FROST: 85, KING: 110}
PLAN_SPACES = [  # id, name, kind, size, floor, purpose
    ('room:mouth', 'Cave mouth', 'cave', 'M', F0, "The arrival (entrance:x7_mouth), X7's daylight behind; the office's front ahead. Quiet (D-11.3)."),
    ('room:tax_hall', 'Tax office hall', 'room', 'M', F0, "Scaldrith's door (house 4852: the tax, Great Wyrm, the Dragon Grandmaster), the urn on the counter (q-c25.urn), the inner door (q-c25.inner_door: tax_paid opens it for good, 118100; else the throw to X7). Quiet."),
    ('room:waiting', 'Waiting room', 'room', 'S', F0, "Dragon Lore, volume 1 on the lectern (q-c25.volume1). Quiet."),
    ('room:scorch', 'Scorched passage', 'corridor', 'S', F0, "A low passage (288) behind the inner door. Quiet."),
    ('room:bone_hall', 'Bone hall', 'hall', 'L', F0, "Four Acid Dragons (a pair by the road that flies onto the ledge); the dragon road up onto the roost ledge."),
    ('room:hollows', 'Acid hollows', 'cave', 'M', F0, "Three Acid Dragons."),
    ('room:last', 'The last taxpayer', 'cave', 'S', F0, "A knight's remains and his strongbox (T6), the receipt (q-c25.receipt)."),
    ('room:vents', 'Sulphur vents', 'cave', 'M', F0, "Two Acid Dragons in the steam (the floor-0 loop)."),
    ('room:crossing', 'Fire crossing', 'cave', 'M', F0, "A Fire Dragon pair."),
    ('room:egg', 'Egg cave', 'cave', 'S', F0, "The nest, the mother, a chest (T6)."),
    ('room:head', 'Stair head', 'stair', 'S', F0, "The low tunnel to the walked stair."),
    ('room:stair', 'The walked stair', 'stair', 'S', F0, "32 steps down 1,024 (D-47)."),
    ('room:foot', 'Stair foot', 'stair', 'S', F1, "Low openings into the roost and to the pools."),
    ('room:roost', 'The great roost', 'hall', 'L', F1, "Set piece: 2,048 high through both floors, the floor-0 ledge and its lip; four Fire and two Frost Dragons below; the bone hall's road pair flies onto the ledge."),
    ('room:pools', 'Steaming pools', 'cave', 'M', F1, "Three Fire Dragons."),
    ('room:den', 'East den', 'cave', 'M', F1, "Two Fire Dragons, a chest (T6)."),
    ('room:old_roost', 'Old roost', 'cave', 'M', F1, "Three Fire Dragons (the floor -1 east loop)."),
    ('room:ember', 'Ember gallery', 'corridor', 'M', F1, "A dragon road to the library's east leaves; a Fire pair."),
    ('room:library', 'Library of Dragon Lore', 'hall', 'L', F1, "Set piece and goal: shelves 2-4 (q-c25.volume2-4) and the ledger stand (q-c25.taxation); two Frost Dragons."),
    ('room:kings_door', "The King's door", 'room', 'S', F1, "Shelf 5 (q-c25.volume5) by the King's low door. Quiet."),
    ('room:throne', "The Dragon King's hall", 'hall', 'L', F1, "The Dragon King 110 on his dais of gold, two Frost Dragons."),
    ('room:hoard', "The King's hoard", 'cave', 'S', F1, "Behind the grate, open at the King's death (118101): the King's chest (T6)."),
    ('room:starwell', 'The starwell', 'hall', 'L', F1, "Set piece: the slot of stars (sky: true); three Frost Dragons."),
    ('room:frost', 'Frost den', 'cave', 'M', F1, "A Frost pair (the library loop)."),
    ('room:rime', 'Rime cave', 'cave', 'S', F1, "Three Frost Dragons, a chest (T6)."),
]
LINKS = [
    ('link:mouth_hall', 'room:mouth', 'room:tax_hall', 'open'),
    ('link:hall_waiting', 'room:tax_hall', 'room:waiting', 'double_door'),
    ('link:hall_scorch', 'room:tax_hall', 'room:scorch', 'double_door'),
    ('link:scorch_bone', 'room:scorch', 'room:bone_hall', 'open'),
    ('link:bone_hollows', 'room:bone_hall', 'room:hollows', 'open'),
    ('link:hollows_last', 'room:hollows', 'room:last', 'open'),
    ('link:hollows_vents', 'room:hollows', 'room:vents', 'open'),
    ('link:bone_ledge', 'room:bone_hall', 'room:roost', 'open'),
    ('link:ledge_crossing', 'room:roost', 'room:crossing', 'open'),
    ('link:crossing_egg', 'room:crossing', 'room:egg', 'open'),
    ('link:crossing_head', 'room:crossing', 'room:head', 'open'),
    ('link:vents_head', 'room:vents', 'room:head', 'open'),
    ('link:stair_down', 'room:head', 'room:stair', 'stairs'),
    ('link:stair_foot', 'room:stair', 'room:foot', 'stairs'),
    ('link:foot_roost', 'room:foot', 'room:roost', 'open'),
    ('link:foot_pools', 'room:foot', 'room:pools', 'open'),
    ('link:pools_den', 'room:pools', 'room:den', 'open'),
    ('link:pools_old', 'room:pools', 'room:old_roost', 'open'),
    ('link:old_roost', 'room:old_roost', 'room:roost', 'open'),
    ('link:roost_ember', 'room:roost', 'room:ember', 'open'),
    ('link:roost_starwell', 'room:roost', 'room:starwell', 'open'),
    ('link:ember_library', 'room:ember', 'room:library', 'double_door'),
    ('link:starwell_frost', 'room:starwell', 'room:frost', 'open'),
    ('link:frost_rime', 'room:frost', 'room:rime', 'open'),
    ('link:frost_library', 'room:frost', 'room:library', 'double_door'),
    ('link:library_kings', 'room:library', 'room:kings_door', 'open'),
    ('link:kings_throne', 'room:kings_door', 'room:throne', 'double_door'),
    ('link:throne_hoard', 'room:throne', 'room:hoard', 'door'),
]


def plan_doc(level):
    pops = {}
    for rid, ms in PLACED:
        for _, mon, _, _ in ms:
            pops.setdefault(f'room:{rid}', {}).setdefault(mon, 0)
            pops[f'room:{rid}'][mon] += 1
    pops.setdefault('room:throne', {})[KING] = 1
    spaces = []
    for sid, name, kind, size, floor, purpose in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind if kind in ('room', 'corridor') else 'room', 'size': size, 'floor': floor, 'purpose': purpose}
        if sid in pops:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [n, n], 'levels': [LEVELS[m], LEVELS[m]],
                                'notes': f"{n} {NAMES[m]} {LEVELS[m]} (placed)."} for m, n in pops[sid].items()]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [{'id': i, 'from': f, 'to': t, 'kind': k} for i, f, t, k in LINKS]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "The dragons' cave in Mount Firestone's black crag, behind the tax road: a tax office in its mouth whose inner door throws out anyone who has not paid, the upper halls, a roost through both floors, a hall broken open on the stars at the world's rim, and the library of Dragon Lore before the Dragon King's door.",
        'purpose': "Q-C25 The Dragon Tax (optional): Scaldrith's tax (house 4852, tax_paid 112500) or the throw (q-c25.inner_door); Dragon Lore 1-5 and The Art of Taxation (q-c25.volume1-5, taxation); the Dragon King 110 (optional boss). Party 60 to 64, monsters 66-85 (40 placed, D-57 Q1), treasure 6.",
        'mood': "Sulphur, old smoke and the smell of something very large; the clerks' cold stone at the mouth, then rock blackened by breath, wings moving in the dark below the ledge, starlight through a broken wall.",
        'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:upper', 'spaces': ['room:bone_hall', 'room:hollows', 'room:vents', 'room:head', 'room:crossing',
                                            'room:roost'],
             'notes': "Floor 0: from the bone hall to the stair head by the ledge and the fire crossing, or by the hollows and the vents."},
            {'id': 'loop:pools', 'spaces': ['room:foot', 'room:roost', 'room:old_roost', 'room:pools'],
             'notes': "Floor -1 east: into the roost directly, or round by the pools and the old roost."},
            {'id': 'loop:library', 'spaces': ['room:roost', 'room:ember', 'room:library', 'room:frost',
                                              'room:starwell'],
             'notes': "To the library by the ember gallery's leaves, or by the starwell and the frost den's leaves."}],
        'entrances': [{'id': 'entrance:x7_mouth', 'space': 'room:mouth', 'kind': 'both', 'facing': 'e',
                       'how': "From X7's door:xd18 (A5) in the rim crag: 384 inside the mouth, facing east toward the office's front."}],
        'critical_path': ['room:mouth', 'room:tax_hall', 'room:scorch', 'room:bone_hall', 'room:roost',
                          'room:crossing', 'room:head', 'room:stair', 'room:foot', 'room:roost', 'room:ember',
                          'room:library', 'room:kings_door', 'room:throne'],
        'return_path': ['room:throne', 'room:kings_door', 'room:library', 'room:ember', 'room:roost', 'room:foot',
                        'room:stair', 'room:head', 'room:crossing', 'room:roost', 'room:bone_hall', 'room:scorch',
                        'room:tax_hall', 'room:mouth'],
        'goals': [{'id': 'goal:tax', 'space': 'room:tax_hall', 'kind': 'use', 'story': 'Q-C25',
                   'what': "Scaldrith's topic 'The tax' (tax_paid), then the inner door (q-c25.inner_door)."},
                  {'id': 'goal:lore', 'space': 'room:library', 'kind': 'use', 'story': 'Q-C25',
                   'what': "Dragon Lore 2-5 and The Art of Taxation."},
                  {'id': 'goal:king', 'space': 'room:throne', 'kind': 'kill', 'story': 'Q-C25',
                   'what': "The Dragon King (optional boss); the grate rises (118101)."}],
        'set_pieces': [{'id': 'set:roost', 'kind': 'scripted', 'spaces': ['room:roost'],
                        'rule': "Through both floors: the ledge and its lip over the roost (D-57)."},
                       {'id': 'set:starwell', 'kind': 'scripted', 'spaces': ['room:starwell'],
                        'rule': "The slot of stars over the void (sky: true); the dragons cannot leave by it (D-57)."},
                       {'id': 'set:library', 'kind': 'scripted', 'spaces': ['room:library', 'room:throne'],
                        'rule': "The library of Dragon Lore and the King's hall behind it."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 25, 'sectors': 25, 'monsters_about': 41, 'chests': 5, 'doors': 7, 'loops': 3,
                   'floor_area_munits2': 55},
        'notes': "Size M (20-45 sectors, 30-90 M units², 45-75 monsters (40 here, D-57 Q1), 3-7 chests, 6-16 doors). From act6_graphs/xd18.graph.yml and D-57 (XD-18 APPROVAL, Q1-Q6).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """XD-18 Dragon Cave (not to scale; plan, north up)
  floor -1 (z -1024):
   [RIME]--[FROST DEN]--[STARWELL: slot of stars N]      [OLD ROOST]--[POOLS]--[EAST DEN]
               |leaves        \\road 768                    |          |
  [HOARD]=grate=[KING'S HALL]=door=[KING'S DOOR]--[LIBRARY]=leaves=[EMBER]=road=[GREAT ROOST]--[STAIR FOOT]
                                                                 (ledge, floor 0)    | stair up
  floor 0 (z 0):                                                  road 768|  low     |
   =exit= X7 [MOUTH]--[TAX HALL: office 4852, urn]--inner door--[SCORCH]--[BONE HALL]   [CROSSING]--[STAIR HEAD]
                  |door                                                  |              |        |
               [WAITING: vol. 1]                [LAST TAXPAYER]--[HOLLOWS]--[VENTS]---[EGG]------/
"""

# ================================================================================================ objects
ARRIVAL = [384, -3072]
objects = {'format': 0}
objects['start'] = {'room': 'room:mouth', 'at': ARRIVAL, 'facing': 'e',
                    'notes': "entrance:x7_mouth: 384 inside the mouth, facing east toward the office's front."}
objects['arrivals'] = [{'entrance': 'entrance:x7_mouth', 'room': 'room:mouth', 'at': ARRIVAL, 'facing': 'e',
                        'notes': "384 inside X7's mouth, facing east toward the office's front and its doorway (X7's door:xd18, A5)."}]
PAIR = {'pictures': [[LEAF_L, LEAF_R]], 'back_pictures': [[LEAF_L, LEAF_R]]}


def pair(id, opening, notes, **kw):
    d = {'id': id, 'opening': opening, 'kind': 'hinged', 'leaves': 2, 'thickness': 24, 'edge_surface': WOOD,
         'notes': notes}
    d.update(PAIR)
    d.update(kw)
    return d


objects['doors'] = [
    pair('door:waiting', 'open:hall_waiting', "The waiting room's doors (gkp103a/gkp103b)."),
    pair('door:inner', 'open:hall_scorch',
         "The inner door: it opens to everyone (D-89; q-c25.inner_door, 118100 keeps it open); from the passage it always opens."),
    pair('door:library_e', 'open:ember_library', "The library's east leaves (288 high, D-32)."),
    pair('door:library_n', 'open:frost_library', "The library's north leaves (288 high)."),
    pair('door:king', 'open:kings_throne', "The King's door: two bronze leaves 384 wide in all, 288 high (D-32)."),
    {'id': 'door:grate', 'opening': 'open:throne_hoard', 'kind': 'slide_up', 'thickness': 16, 'speed': 48,
     'surface': GRATE, 'tile': True,
     'notes': "The hoard's grate behind the dais: it rises at the Dragon King's death (118101) and stays up on every load."},
]
# F6 feedback fix (2026-11-21): every Xeen chest is the shipped chest (MM8's gt002, its own size) in place of a plank
# box, its back 16 from the wall it stands against; a chest's `facing` is its long axis, the front 90 degrees
# anticlockwise of it (e -> north, n -> west, w -> south, s -> east)
CHEST = {'kind': 'gt002'}
objects['chests'] = [
    dict({'id': 'chest:strongbox', 'room': 'room:last', 'at': [2720, -5072], 'facing': 'e',
          'treasure_level': 6, 'random_items': 3, 'gold': 4000, 'notes': "The knight's strongbox (T6)."}, **CHEST),
    dict({'id': 'chest:egg', 'room': 'room:egg', 'at': [9472, -3536], 'facing': 'e',
          'treasure_level': 6, 'random_items': 3, 'gold': 4000, 'notes': "The mother's hoard by the wall (T6)."}, **CHEST),
    dict({'id': 'chest:den', 'room': 'room:den', 'at': [11728, 1792], 'facing': 'n',
          'treasure_level': 6, 'random_items': 3, 'gold': 4000, 'notes': "The east den's chest (T6)."}, **CHEST),
    dict({'id': 'chest:rime', 'room': 'room:rime', 'at': [-208, 768], 'facing': 's',
          'treasure_level': 6, 'random_items': 3, 'gold': 4000, 'notes': "The frozen hoard (T6)."}, **CHEST),
    dict({'id': 'chest:hoard', 'room': 'room:hoard', 'at': [-4304, -128], 'facing': 's',
          'treasure_level': 6, 'random_items': 5, 'gold': 8000, 'notes': "The King's chest (T6)."}, **CHEST),
]
objects['monsters'] = []
for rid, ms in PLACED:
    for n, (group, mon, at, facing) in enumerate(ms, 1):
        m = {'id': f'monster:{rid}_{n}', 'room': f'room:{rid}', 'monster': mon, 'at': list(at), 'facing': facing,
             'group': group, 'leash': LEASH[tuple(at)]}
        objects['monsters'].append(m)
objects['monsters'].append({'id': 'monster:king', 'room': 'room:throne', 'monster': KING, 'at': list(KING_AT),
                            'facing': 0, 'group': 33, 'leash': KING_LEASH,
                            'notes': "The Dragon King (11645, 110; S's skin xcdr_king to come) on top of his mound of gold."})


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE_C = [235, 170, 100]
EMBER = [255, 120, 60]
DAY = [255, 236, 200]
SULPHUR = [230, 220, 120]
COLD = [170, 200, 255]
objects['lights'] = [
    light('light:daylight', 'room:mouth', [96, -3072], 320, 1400, DAY, brightness=30, notes="Daylight from X7 through the mouth."),
    light('light:slot', 'room:starwell', [4736, 2500], 900, 2600, COLD, brightness=28, notes="Starlight and cold through the slot."),
    light('light:pool', 'room:pools', [9600, 1792], 160, 1400, EMBER, brightness=16, notes="The hot pool's glow."),
    light('light:vent_1', 'room:vents', [6600, -4600], 96, 1200, SULPHUR, brightness=14, notes="Steam glowing over a vent."),
    light('light:vent_2', 'room:vents', [8600, -4400], 96, 1200, SULPHUR, brightness=14, notes="Steam glowing over a vent."),
    light('light:ember_1', 'room:ember', [3600, -384], 64, 900, EMBER, brightness=16, notes="Embers in the cracks."),
    light('light:ember_2', 'room:ember', [4500, -384], 64, 900, EMBER, brightness=16, notes="Embers in the cracks."),
    light('light:roost_1', 'room:roost', [6000, -600], 300, 1800, EMBER, brightness=14, notes="Embers on the roost's floor."),
    light('light:roost_2', 'room:roost', [7400, 0], 300, 1800, EMBER, brightness=14, notes="Embers on the roost's floor."),
    light('light:crossing', 'room:crossing', [8960, -1728], 96, 1100, EMBER, brightness=14, notes="Warm air through the cracks."),
    light('light:egg', 'room:egg', [8960, -3008], 96, 900, EMBER, brightness=14, notes="The nest's warmth."),
    light('light:throne', 'room:throne', [-2624, -128], 400, 2200, FIRE_C, brightness=18, notes="The gold's glow round the dais."),
    light('light:hoard', 'room:hoard', [-3840, -128], 160, 900, FIRE_C, brightness=18, notes="Gold in the dark."),
]
# Torches on the walls of the worked rooms (12 out from the wall, as FD-02's).
TORCHES = [('tax_hall', (1164, -3584)), ('tax_hall', (2676, -2800)), ('waiting', (1600, -2292)),
           ('library', (908, -600)), ('library', (2932, -600)), ('library', (1408, 372)), ('library', (2432, 372)),
           ('kings_door', (-256, 116)), ('kings_door', (512, -628)), ('mouth', (512, -2700))]
objects['decorations'] = []
for i, (rid, at) in enumerate(TORCHES, 1):
    floor = F1 if rid in ('library', 'kings_door') else F0
    d = {'id': f'deco:torch_{i:02d}', 'room': f'room:{rid}', 'decoration': 'torch01', 'at': list(at), 'height': 224}
    objects['decorations'].append(d)
    objects['lights'].append(light(f'light:torch_{i:02d}', f'room:{rid}', list(at), 256, 800, FIRE_C))
objects['decorations'] += [
    {'id': 'deco:urn', 'room': 'room:tax_hall', 'decoration': 'dec97', 'at': [1536, -3632], 'floor_height': F0 + 104,
     'notes': "The brass urn on the counter's sill."},
    {'id': 'deco:knight', 'room': 'room:last', 'decoration': 'dec05', 'at': [2720, -4736], 'floor_height': F0 + 24,
     'notes': "The knight's remains."},
    {'id': 'deco:bones_1', 'room': 'room:bone_hall', 'decoration': 'dec29', 'at': [4150, -3700]},
    {'id': 'deco:bones_2', 'room': 'room:bone_hall', 'decoration': '7dec18', 'at': [5700, -3650]},
    {'id': 'deco:bones_3', 'room': 'room:bone_hall', 'decoration': 'dec19', 'at': [4200, -2500]},
    {'id': 'deco:skull_1', 'room': 'room:bone_hall', 'decoration': '7dec20', 'at': [5100, -3700]},
    {'id': 'deco:bones_4', 'room': 'room:mouth', 'decoration': 'dec29', 'at': [700, -3350]},
    {'id': 'deco:bones_5', 'room': 'room:hollows', 'decoration': 'dec29', 'at': [4200, -5200]},
    {'id': 'deco:bones_6', 'room': 'room:roost', 'decoration': 'dec19', 'at': [5400, 300]},
    {'id': 'deco:bones_7', 'room': 'room:throne', 'decoration': '7dec18', 'at': [-1000, 600]},
    {'id': 'deco:goblet_1', 'room': 'room:throne', 'decoration': '7dec46', 'at': [-2300, 420]},
    {'id': 'deco:goblet_2', 'room': 'room:throne', 'decoration': '7dec48', 'at': [-2300, -560]},
    {'id': 'deco:bowls_1', 'room': 'room:throne', 'decoration': 'dec32', 'at': [-2250, 150]},
    {'id': 'deco:goblet_3', 'room': 'room:hoard', 'decoration': '7dec46', 'at': [-3700, 160]},
    {'id': 'deco:bowls_2', 'room': 'room:hoard', 'decoration': 'dec32', 'at': [-3700, -420]},
] + [{'id': f'deco:steam_{i}', 'room': f'room:{rid}', 'decoration': 'smoke', 'at': list(at),
      **({'floor_height': fh} if fh is not None else {}), 'notes': note}
     for i, (rid, at, fh, note) in enumerate([
         ('vents', (6600, -4600), None, "Yellow steam from a vent."),
         ('vents', (7600, -5000), None, "Yellow steam from a vent."),
         ('vents', (8600, -4400), None, "Yellow steam from a vent."),
         ('pools', (9400, 1792), F1 - 64, "Steam off the hot pool."),
         ('pools', (9850, 1800), F1 - 64, "Steam off the hot pool."),
     ], 1)] + [
    {'id': f'deco:ember_{i}', 'room': 'room:ember', 'decoration': 'Brnrock0', 'at': list(at),
     'notes': "Embers in the cracks of the dragon road."}
    for i, at in enumerate([(3600, -700), (4500, -60)], 1)]
# F14 (feedback 2026-11-21): rungs out of the steaming pool, so a party that steps in climbs back.
objects['ladders'] = [
    {'id': 'ladder:pool', 'room': 'room:pools', 'at': [9600, 1552], 'facing': 's', 'height': 64, 'exit': [9600, 1472],
     'grab_at_top': True, 'surface': {'texture': 'bemv', 'size': [32, 256], 'uneven': True},
     'notes': "F14: rungs out of the steaming pool onto its south bank."},
]
objects['exits'] = [
    {'id': 'exit:mouth', 'room': 'room:mouth', 'wall': 'west', 'size': [512, 448], 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
     'to': 'exit:x7_mouth', 'notes': "The cave mouth: X7's daylight on the rim crag."},
]
objects['sounds'] = [
    {'id': 'sound:bed', 'room': 'room:roost', 'at': [6656, -832], 'sound': 'humming',
     'radius': 9000, 'inner_radius': 4000, 'volume': 0.35, 'pan': False,
     'notes': "The cave's hum under both floors (D-48)."},
    {'id': 'sound:wind', 'room': 'room:starwell', 'at': [4736, 2300], 'sound': 'whistling wind', 'radius': 2600,
     'inner_radius': 900, 'volume': 0.45, 'pan': False, 'notes': "The wind over the rim through the slot."},
    {'id': 'sound:mouth', 'room': 'room:mouth', 'at': [200, -3072], 'sound': 'whistling wind', 'radius': 1400,
     'inner_radius': 300, 'volume': 0.3, 'pan': False, 'notes': "X7's wind at the mouth."},
]

# ------------------------------------------------------------------------------------------------ D-89 identity
# The dragon spaces as caves (D-89, reviews/DESIGN_GATING_AND_IDENTITY.md 2.2; lane A7 s26, 2026-11-22), as MM8's d17
# is built: each cave room's rectangle loses its corners (cut on a slant with a break pushed in: up to 12 sides) and
# keeps its rough walls; its floor rises and falls between points inside it (floor_points; the walls' feet, and so
# every opening's sill, stay at the room's floor) and its roof vaults up between points (ceiling_points); hanging rock
# (stalactites) in the high caves. The King's hall and the hoard are floored with gold heaped into a mound, the King
# on its top. The party's tunnels (288) and the worked rooms keep their square shape (D-32). Corners are cut only as
# far as every chest, decoration, platform, ladder and placed dragon of the room keeps clear of the cut.
import hashlib


def _h(*k):
    return int(hashlib.md5(repr(k).encode()).hexdigest()[:8], 16) / 0xffffffff


OBST = {}


def _ob(rid, at, r):
    OBST.setdefault(rid, []).append((at[0], at[1], r))


for _c in objects['chests']:
    _ob(_c['room'], _c['at'], 128)
for _d in objects['decorations']:
    _ob(_d['room'], _d['at'], 96)
for _m in objects['monsters']:
    _ob(_m['room'], _m['at'], 300 if _m['monster'] == KING else 250)
for _l in objects['ladders']:
    _ob(_l['room'], _l['at'], 128)
for _r in rooms:
    for _p in _r.get('platforms', []):
        if 'at' in _p:
            _ob(_r['id'], _p['at'], max(_p['size']) / 2 + 64)
    for _lv in _r.get('levels', []):
        xs = [q[0] for q in _lv['outline']]; ys = [q[1] for q in _lv['outline']]
        _ob(_r['id'], [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2],
            max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 96)


def cave_outline(rid, cmax, skip=()):
    """The room's rectangle with each corner (sw, se, ne, nw) cut on a slant up to cmax, a break pushed in halfway."""
    r = ROOMS[rid]
    xs = [q[0] for q in r['outline']]; ys = [q[1] for q in r['outline']]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    corners = {'sw': (x0, y0, 1, 1), 'se': (x1, y0, -1, 1), 'ne': (x1, y1, -1, -1), 'nw': (x0, y1, 1, -1)}
    cut = {}
    for name, (cx, cy, sx, sy) in corners.items():
        c = 0 if name in skip else min(cmax, (x1 - x0) // 3, (y1 - y0) // 3)
        for ox, oy, orad in OBST.get(rid, []):
            c = min(c, abs(ox - cx) + abs(oy - cy) - int(orad * 1.42) - 32)
        c = max(0, c) // 32 * 32
        cut[name] = c if c >= 96 else 0
    pts = []

    def corner(name):
        cx, cy, sx, sy = corners[name]
        c = cut[name]
        if not c:
            return [[cx, cy]]
        k = 0.12 + 0.14 * _h(rid, name)
        mid = [round(cx + sx * c * (0.5 + k)), round(cy + sy * c * (0.5 + k))]
        a = [cx + sx * c, cy] if name in ('sw', 'ne') else [cx, cy + sy * c]
        b = [cx, cy + sy * c] if name in ('sw', 'ne') else [cx + sx * c, cy]
        # counter-clockwise: sw: from the west wall's foot to the south wall; se: south wall to east wall ...
        if name == 'sw':
            return [[cx, cy + c], mid, [cx + c, cy]]
        if name == 'se':
            return [[cx - c, cy], mid, [cx, cy + c]]
        if name == 'ne':
            return [[cx, cy - c], mid, [cx - c, cy]]
        return [[cx + c, cy], mid, [cx, cy - c]]
    for name in ('sw', 'se', 'ne', 'nw'):
        pts += corner(name)
    r['outline'] = pts
    return cut


def inside(rid, x, y, margin):
    xs = [q[0] for q in ROOMS[rid]['outline']]; ys = [q[1] for q in ROOMS[rid]['outline']]
    if not (min(xs) + margin <= x <= max(xs) - margin and min(ys) + margin <= y <= max(ys) - margin):
        return False
    # away from the cut corners too
    for q in ROOMS[rid]['outline']:
        pass
    return True


def floor_bumps(rid, amp, step=512, margin=448, clear=0, extra=()):
    """Heights between points inside the room: a deterministic field of rises and dips, |dz| <= amp."""
    r = ROOMS[rid]
    xs = [q[0] for q in r['outline']]; ys = [q[1] for q in r['outline']]
    pts = []
    x = min(xs) + margin
    while x <= max(xs) - margin:
        y = min(ys) + margin
        while y <= max(ys) - margin:
            jx = round((_h(rid, 'fx', x, y) - 0.5) * step * 0); jy = round((_h(rid, 'fy', x, y) - 0.5) * step * 0)
            px, py = x + jx, y + jy
            if inside(rid, px, py, margin - 64):
                dz = round((_h(rid, 'fz', x, y) * 2 - 1) * amp / 16) * 16
                if clear and any(abs(px - ox) + abs(py - oy) < orad + clear for ox, oy, orad in OBST.get(rid, [])):
                    dz = min(dz, 0)
                if abs(dz) >= 16:
                    pts.append([px, py, r['floor'] + dz])
            y += step
        x += step
    pts += [[px, py, r['floor'] + dz] for px, py, dz in extra]
    if pts:
        r['floor_points'] = pts
    return pts


def vault(rid, amp, step=640, margin=448):
    r = ROOMS[rid]
    xs = [q[0] for q in r['outline']]; ys = [q[1] for q in r['outline']]
    pts = []
    x = min(xs) + margin
    while x <= max(xs) - margin:
        y = min(ys) + margin
        while y <= max(ys) - margin:
            dz = round((0.45 + 0.55 * _h(rid, 'cz', x, y)) * amp / 16) * 16
            pts.append([x, y, r['ceiling'] + dz])
            y += step
        x += step
    if pts:
        r['ceiling_points'] = pts


def stalactites(rid, n, length, radius=72):
    r = ROOMS[rid]
    xs = [q[0] for q in r['outline']]; ys = [q[1] for q in r['outline']]
    out = []
    for i in range(n):
        x = round(min(xs) + 320 + _h(rid, 'sx', i) * (max(xs) - min(xs) - 640))
        y = round(min(ys) + 320 + _h(rid, 'sy', i) * (max(ys) - min(ys) - 640))
        if any(abs(x - ox) + abs(y - oy) < orad + 160 for ox, oy, orad in OBST.get(rid, [])):
            continue
        out.append({'at': [x, y], 'radius': radius, 'length': length, 'surface': ROCK})
    if out:
        r['stalactites'] = out


CAVES = {  # room: (corner cut, corners kept square, floor amplitude (0: none), roof rise, stalactites (count, length))
    'room:mouth': (128, (), 48, 0, None),
    'room:bone_hall': (384, ('ne',), 96, 384, None),
    'room:hollows': (320, (), 80, 256, (4, 224)),
    'room:last': (192, (), 48, 0, None),
    'room:vents': (320, ('ne',), 64, 256, (3, 224)),
    'room:crossing': (256, ('sw', 'nw'), 64, 256, None),
    'room:egg': (256, (), 0, 192, None),
    'room:pools': (320, ('sw', 'nw'), 0, 256, (3, 192)),
    'room:den': (256, (), 64, 256, None),
    'room:old_roost': (384, (), 96, 320, (3, 256)),
    'room:starwell': (384, ('ne', 'nw', 'se'), 80, 384, None),
    'room:frost': (320, (), 64, 256, (4, 224)),
    'room:rime': (256, (), 48, 256, (6, 288)),
    'room:throne': (320, (), 0, 384, None),
    'room:hoard': (128, (), 0, 0, None),
}
CUTS = {}
for _rid, (_c, _skip, _amp, _roof, _st) in CAVES.items():
    ROOMS[_rid]['rough'] = ROUGH
    CUTS[_rid] = cave_outline(_rid, _c, _skip)
    if _amp:
        floor_bumps(_rid, _amp, step=448, clear=160)
    if _roof:
        vault(_rid, _roof)
    if _st:
        stalactites(_rid, *_st)
# The roost keeps its ledge and lip (a level and a platform): rough walls and a vaulted roof only.
ROOMS['room:roost']['rough'] = ROUGH
vault('room:roost', 384)
# the roost's floor below the ledge rises and falls too (points north of the ledge's lip, away from its wall)
_rp = []
for _x in range(5632, 7700, 512):
    for _y in range(-1152, 160, 448):
        _dz = round((_h('roost', _x, _y) * 2 - 1) * 96 / 16) * 16
        if abs(_dz) >= 16:
            _rp.append([_x, _y, F1 + _dz])
ROOMS['room:roost']['floor_points'] = _rp
stalactites('room:roost', 4, 288)
# The King's mound of gold: from the hall's floor up to 192 under the King, its slopes falling to the walls.
_kx, _ky = KING_AT
ROOMS['room:throne']['floor_points'] = [[_kx, _ky, F1 + 192], [_kx, _ky + 576, F1 + 112], [_kx, _ky - 576, F1 + 112],
                                        [_kx + 640, _ky, F1 + 96], [_kx - 320, _ky, F1 + 128],
                                        [_kx + 640, _ky + 576, F1 + 32], [_kx + 640, _ky - 576, F1 + 32],
                                        [-1280, _ky + 448, F1 + 16], [-1280, _ky - 448, F1 + 16]]
ROOMS['room:throne']['notes'] = ("The boss: a cave 2,688 by 2,048 and 1,536 high floored with the King's gold, heaped "
                                 "into a mound 192 high under the Dragon King, two Frost Dragons at its feet. The only "
                                 "openings: the King's low door (east) and the hoard's grate in the west wall behind the "
                                 "mound, which rises at his death.")
ROOMS['room:hoard']['floor_points'] = [[-3840, -128, F1 + 96], [-3584, 128, F1 + 48], [-4096, -384, F1 + 48]]
# ================================================================================================ wiring
QB = {'inner_door_open': 118100, 'king_slain': 118101, 'tax_paid': 112500}


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 7,
     'text': "Sulphur and old smoke on the air. Somewhere far in, something very large is breathing."},
    {'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:mouth', 'title': 'Exit Dragon Cave',
     'notes': "Out to X7 (installed, A5) by the game's own leave window (D-24); 'Exit Dragon Cave?' (aaze0050:17) is its meaning."},
    {'id': 'evt:office', 'preset': 'script', 'source': 'door:tax_office', 'title': 'The Dragon Tax Office',
     'effects': [{'lua': 'evt.EnterHouse(4852)'}],
     'notes': "A4's house 4852 (Scaldrith 5702): the tax, Great Wyrm (A3's Q-C25 topics), the Dragon Grandmaster."},
    {'id': 'evt:office_r', 'preset': 'script', 'source': 'panel:tax_office_r', 'title': 'The Dragon Tax Office',
     'effects': [{'lua': 'evt.EnterHouse(4852)'}], 'notes': "The right wing of house 4852's door."},
    {'id': 'evt:urn', 'preset': 'script', 'source': 'platform:counter', 'title': 'Urn',
     'effects': [hook('q-c25.urn')],
     'notes': "A3's q-c25.urn: before the tax its waiting line; after it aaze0050:1 'The urn is empty and powerless.'"},
    {'id': 'evt:inner_door', 'preset': 'script', 'source': 'door:inner', 'side': 'room:tax_hall',
     'title': 'Inner door', 'opens': ['door:inner'], 'sets': {'qbit': QB['inner_door_open']},
     'effects': [hook('q-c25.inner_door')],
     'notes': "D-89 (2026-11-22): the inner door opens to everyone and stays open (118100); A3's q-c25.inner_door runs. The tax now guards only the Dragon King's door (evt:door_king) and the Great Wyrm promotion; no refusal moves the party (the old throw to X7 is gone)."},
    {'id': 'evt:inner_back', 'preset': 'door', 'source': 'door:inner', 'side': 'room:scorch', 'title': 'Door',
     'action': 'open', 'notes': "From the passage the inner door always opens."},
    {'id': 'evt:inner_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': QB['inner_door_open']},
     'opens': ['door:inner'], 'notes': "Once opened (118100) the inner door stands open on every load."},
    {'id': 'evt:door_waiting', 'preset': 'door', 'source': 'door:waiting', 'title': 'Doors'},
    {'id': 'evt:door_library_e', 'preset': 'door', 'source': 'door:library_e', 'title': 'Doors'},
    {'id': 'evt:door_library_n', 'preset': 'door', 'source': 'door:library_n', 'title': 'Doors'},
    {'id': 'evt:door_king', 'preset': 'script', 'source': 'door:king', 'title': "The Dragon King's door",
     'condition': {'lua': 'XeenQuests.hook("q-c25.king_door")'}, 'opens': ['door:king'],
     'effects': [{'lua': "-- the leaves open (the hook has run)"}],
     'notes': "D-89 INWARD (2026-11-22): A3's q-c25.king_door needs tax_paid (112500); true opens the leaves for good, false has shown \"Tax first,\" on the status line and nobody moves."},
    {'id': 'evt:grate', 'preset': 'switch', 'source': 'door:grate', 'title': 'Grate',
     'condition': {'qbit': QB['king_slain']}, 'opens': ['door:grate'],
     'locked_text': "A heavy grate, set deep in the rock behind the dais. It does not move.",
     'notes': "The grate rises only at the King's death."},
    {'id': 'evt:king_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2,
     'condition': {'kills': {'monster': 'monster:king'}}, 'once': True, 'opens': ['door:grate'],
     'sets': {'qbit': QB['king_slain']},
     'effects': [{'text': "The Dragon King is dead. Behind the dais the grate grinds up into the rock."}],
     'notes': "The kill timer (XD-05's drum method): king_slain 118101, the grate rises in the same visit."},
    {'id': 'evt:king_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': QB['king_slain']},
     'opens': ['door:grate'], 'notes': "With king_slain the grate stands up on every load."},
    # ---- Dragon Lore (A3's hooks; the hovers are aaze0050:5-10)
    {'id': 'evt:volume1', 'preset': 'script', 'source': 'platform:lectern', 'title': 'Dragon Lore Volume 1',
     'effects': [hook('q-c25.volume1')], 'notes': "aaze0050:5 as the hover; A3's q-c25.volume1."},
    {'id': 'evt:volume2', 'preset': 'script', 'source': 'platform:shelf2', 'title': 'Dragon Lore Volume 2',
     'effects': [hook('q-c25.volume2')], 'notes': "aaze0050:6."},
    {'id': 'evt:volume3', 'preset': 'script', 'source': 'platform:shelf3', 'title': 'Dragon Lore Volume 3',
     'effects': [hook('q-c25.volume3')], 'notes': "aaze0050:7."},
    {'id': 'evt:volume4', 'preset': 'script', 'source': 'platform:shelf4', 'title': 'Dragon Lore Volume 4',
     'effects': [hook('q-c25.volume4')], 'notes': "aaze0050:8."},
    {'id': 'evt:volume5', 'preset': 'script', 'source': 'platform:shelf5', 'title': 'Dragon Lore Volume 5',
     'effects': [hook('q-c25.volume5')], 'notes': "aaze0050:9, by the King's door."},
    {'id': 'evt:taxation', 'preset': 'script', 'source': 'platform:ledger', 'title': 'The Art of Taxation',
     'effects': [hook('q-c25.taxation')], 'notes': "aaze0050:10; A3's hook needs the five volumes read."},
    {'id': 'evt:receipt', 'preset': 'script', 'source': 'platform:knight', 'title': 'Remains',
     'effects': [hook('q-c25.receipt')], 'notes': "A3's q-c25.receipt: the knight's receipt."},
    {'id': 'evt:chest_strongbox', 'preset': 'chest', 'source': 'chest:strongbox', 'title': 'Chest'},
    {'id': 'evt:chest_egg', 'preset': 'chest', 'source': 'chest:egg', 'title': 'Chest'},
    {'id': 'evt:chest_den', 'preset': 'chest', 'source': 'chest:den', 'title': 'Chest'},
    {'id': 'evt:chest_rime', 'preset': 'chest', 'source': 'chest:rime', 'title': 'Chest'},
    {'id': 'evt:chest_hoard', 'preset': 'chest', 'source': 'chest:hoard', 'title': 'Chest'},
    # ---- first looks (map lines)
    {'id': 'evt:see_ledge', 'preset': 'text', 'trigger': 'step', 'source': 'level:ledge', 'once': True,
     'seconds': 4, 'text': "Past the lip the rock drops away into the dark. Down there, wings."},
    {'id': 'evt:see_starwell', 'preset': 'text', 'trigger': 'step', 'source': 'room:starwell', 'once': True,
     'seconds': 4, 'text': "Cold pours in through a gap in the north wall: stars, and nothing under them."},
    {'id': 'evt:see_library', 'preset': 'text', 'trigger': 'step', 'source': 'room:library', 'once': True,
     'seconds': 4, 'text': "Shelves cut to a dragon's reach, and books the size of doors."},
]
wiring = {'format': 0, 'variables': [], 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd18', 'name': 'Dragon Cave', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-18', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [32, 16], 'climbs': 'n'},
    'map_stats': {'id': 9143, 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 10,
                  'perception_difficulty': 20, 'refill_days': 672, 'music': 13, 'environment': 'cave',
                  'lock_difficulty': 20, 'bolster': 'LowerToEqual', 'slots': []},
    'neighbours': [{
        'id': 'exit:x7_mouth', 'to': 'xeen_x7.odm', 'kind': 'door', 'arrival': 'entrance:xd18_mouth',
        'arrival_hint': "On X7 before the Dragon Cave's mouth in the rim crag (A5's entrance:xd18_mouth, (-4096, 16896, 2144) facing south).",
        'notes': "X7 installed (A5). The way out (and the inner door's throw, D-57 Q2) names X7's named arrival entrance:xd18_mouth. X7's door:xd18 (thing:xd18_mouth, 'The Dragon Cave smells pretty bad. Are you sure you wish to enter?', aaze0017:0) names this map's arrival entrance:x7_mouth: (384, -3072, 0) facing east."}],
    'qbits': QB,
    'identity': {'shape': 'cave', 'family': 'd17',
                 'seen': ["a cave mouth of scorched rock opening on the Dragon Tax Office cut into the rock",
                          "dragon halls with broken outlines, rising and falling floors and vaulted roofs",
                          "the Dragon King on top of his mound of gold, the starwell open on the stars"]},
    'notes': "Xeen design brief, level L4: XD-18 Dragon Cave on X7 (Q-C25, optional). D-57: Acid Dragon 11641 x 9, Fire Dragon 11642 x 17, Frost Dragon 11643 x 14 (40, 66.64k per member) and the Dragon King 11645 (69.94k with him). Rest encounters 0 (Q5). Hooks q-c25.inner_door, urn, receipt, volume1-5, taxation; Scaldrith's house 4852. Map qbits 118100-118101. Music 13.",
}

atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'night_stars'},
              'notes': "The starwell's slot (its sky faces) shows the stars at the world's rim (the engine's night_stars preset, D-89 identity 2026-11-22; was X7's day sky); the rest of the cave is lit by its own lights."}


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
        p['notes'] = f"Xeen design brief, level {lv}: XD-18 Dragon Cave (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-18 Dragon Cave, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

# A rough wall keeps flat behind an exit on it (the Discord report of 2026-11-23: the mouth's black exit lay behind
# the rough rock and no click reached it): tools/xeen/cave_shape.py flat_behind_panels.
sys.path.insert(0, str(R / 'tools' / 'xeen'))
import cave_shape  # noqa: E402
for rid, n in cave_shape.flat_behind_panels(rooms_doc, objects).items():
    print(f'cave_shape {rid}: flat behind {n} exit/switch')

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('atmosphere.yml', atmosphere),
                     ('diagram.txt', DIAGRAM)])
print('written L4')
