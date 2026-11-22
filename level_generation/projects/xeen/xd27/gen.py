#!/usr/bin/env python3
"""XD-27 Ogre Lair: writes rooms.yml, objects.yml, wiring.yml and project.yml of devdocs/xeen/briefs/xd27/L4 (and,
with --l3, the same rooms.yml into L3). The project files are generated: edit this script and rerun v.sh, never the
YAML. North up, x east, y north, heights from the arrival floor (0)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
L4 = R / 'devdocs/xeen/briefs/xd27/L4'
L3 = R / 'devdocs/xeen/briefs/xd27/L3'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# One family: MM8's Dire Wolf Den (d08), a small brown beast cave, and its own timber.
ROCK = S('gcav1wal', 256, 256)            # d08's brown cave rock: walls and roofs
FLOOR = S('gcav1flr', 256, 256)           # d08's grey-brown floor rock
PLANK = S('t68a10a', 32, 64, scale=2)     # d08's plank and post timber
BEAM = S('t68a11', 64, 32, scale=2)       # d08's beam
IRON = S('t68a10c', 32, 32)               # d08's iron band with rivets
CANVAS = S('t68a13a', 64, 64, scale=2)    # d08's canvas (the torn sail)
SKY = S('7plansky1', 256, 256, scale=4)   # MM7's sky with clouds, as Celeste (7d25) lays it indoors
HILLS = S('xogorge', 512, 256, fit=True, uneven=True)  # A6's river-gorge panorama (session 8): once across the gorge's far wall panel (1600 x 600), stretched to it
WATER = {'texture': 'wtrtyl', 'liquid': 'water', 'flow': 'down'}
DARK = S('solid01', 64, 64)

themes = [
    {'id': 'theme:den', 'wall': ROCK, 'floor': FLOOR, 'ceiling': ROCK, 'door': PLANK,
     'notes': "The den and the works: MM8 Dire Wolf Den (d08) brown rock gcav1wal on walls and roofs, its floor rock gcav1flr underfoot, as d08 lays them."},
    {'id': 'theme:chute', 'wall': ROCK, 'floor': PLANK, 'ceiling': ROCK,
     'notes': "The boulder chute: d08's rock round a trough floored with d08's planks."},
    {'id': 'theme:gorge', 'wall': ROCK, 'floor': WATER, 'ceiling': SKY,
     'notes': "The river gorge outside the throwing ledge: d08's rock as the cliffs, MM8's flowing water far below, MM7's sky (7plansky1, laid indoors in Celeste) as the roof."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octagon(cx, cy, r):
    k = round(r * math.tan(math.pi / 8))
    return [[cx - k, cy - r], [cx + k, cy - r], [cx + r, cy - k], [cx + r, cy + k], [cx + k, cy + r], [cx - k, cy + r],
            [cx - r, cy + k], [cx - r, cy - k]]


def area(pts):
    a = 0
    for i in range(len(pts)):
        x0, y0 = pts[i][:2]
        x1, y1 = pts[(i + 1) % len(pts)][:2]
        a += x0 * y1 - x1 * y0
    return a / 2


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


ROUGH = {'step': 192, 'depth': 40}

# ------------------------------------------------------------------------------------------------ the den
room('room:mouth', 'Cave mouth',
     outline=[[-576, 0], [576, 0], [640, 320], [576, 640], [448, 896], [192, 1088], [-192, 1088], [-448, 896],
              [-640, 704], [-640, 384]],
     floor=0, ceiling=576, ceiling_points=[[0, 512, 704], [-384, 576, 640], [384, 576, 640]],
     theme='theme:den', ambient=8,
     notes="A funnel 1,152 wide at the daylight (the south wall, the exit panel: the X2 hills) narrowing to the log gate in its north wall; the midden crack opens in its west wall.")
room('room:midden', 'Midden crack',
     path=[[-672, 544], [-1280, 544], [-1664, 800], [-1856, 1280], [-1856, 1856]], width=384, smooth=1,
     floor=0, slope={'to': 192}, ceiling=384, theme='theme:den', ambient=20,
     notes="A narrow fissure climbing 192 north-west from the mouth to the bone den, floored with the ogres' refuse; a bend halfway.")
room('room:bone_den', 'Bone den',
     outline=[[-2112, 1888], [-1600, 1888], [-1376, 2112], [-1376, 3008], [-1664, 3200], [-2240, 3264], [-2688, 3136],
              [-2944, 2752], [-2944, 2304], [-2688, 2016]],
     floor=192, ceiling=640, ceiling_points=[[-2176, 2560, 800], [-2624, 2560, 704], [-1792, 2560, 704]],
     theme='theme:den', ambient=19, rough=ROUGH,
     platforms=[
         {'outline': octagon(-2624, 2560, 112), 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Sleeping hollow rim'},
     ],
     notes="A low rounded cave about 1,550 by 1,350, 192 above the feast cave; sleeping heaps along its walls; the midden crack comes up into its south corner, a terrace and steps lead down east into the feast cave.")
FEAST = [[-640, 2176], [640, 2176], [896, 2432], [896, 3584], [640, 3904], [64, 4032], [-448, 4032], [-1024, 3968],
         [-1344, 3776], [-1344, 2496], [-1024, 2240]]
PIT = (-192, 3136)
room('room:feast_cave', 'Feast cave', outline=FEAST, floor=0, ceiling=768,
     ceiling_points=[[PIT[0], PIT[1], 1024], [PIT[0] - 640, PIT[1], 864], [PIT[0] + 640, PIT[1], 864],
                     [PIT[0], PIT[1] - 640, 864], [PIT[0], PIT[1] + 640, 864]],
     theme='theme:den', ambient=17, rough=ROUGH,
     levels=[{'id': 'level:pit', 'outline': octagon(PIT[0], PIT[1], 352), 'floor': -128, 'bank': 192,
              'surface': FLOOR, 'notes': "The cooking pit: a hollow 128 deep with sloping sides; the fire and the cauldron in it."}],
     platforms=[
         {'id': 'platform:terrace', 'outline': [[-1344, 2560], [-1024, 2560], [-1024, 3008], [-1344, 3008]], 'rise': 192,
          'surface': ROCK, 'top_surface': FLOOR, 'notes': "The rock terrace under the bone den's mouth, 192 up."},
         {'at': [-64, 2528], 'size': [320, 96], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench (clear of the line from the gate yard to the Chieftain\'s den)'},
         {'at': [-48, 3744], 'size': [320, 96], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench (clear of the lines from the steps and the kennel to the ramp)'},
         {'at': [-848, 3264], 'size': [96, 384], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench'},
         {'at': [432, 3136], 'size': [96, 448], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench'},
     ],
     flights=[{'from': [-672, 2752], 'to': [-1024, 2752], 'width': 320, 'steps': 6, 'riser': ROCK, 'tread': FLOOR,
               'notes': "Six rock steps of 32 down from the terrace to the cave's floor."}],
     notes="A round cave about 2,240 by 1,860, the cooking pit sunk in its middle under a roof that rises to a smoke hole, four rock benches round the pit; the bone den's terrace and steps on the west, the Chieftain's den up one step on the north-west, the kennel through its hurdle on the east, the gate yard on the south, the quarry ramp on the north.")
room('room:gate_yard', 'Gate yard',
     outline=[[-512, 1120], [576, 1120], [736, 1376], [736, 1792], [576, 2048], [-512, 2048], [-672, 1792], [-672, 1376]],
     floor=0, ceiling=640, ceiling_points=[[32, 1616, 736]], theme='theme:den', ambient=16,
     platforms=[
         {'at': [-260, 1148], 'size': [24, 24], 'rise': 144, 'surface': PLANK, 'top_surface': PLANK, 'notes': "Forked post under the bar's west end"},
         {'at': [260, 1148], 'size': [24, 24], 'rise': 144, 'surface': PLANK, 'top_surface': PLANK, 'notes': "Forked post under the bar's east end"},
     ],
     notes="The cave behind the log gate, about 1,400 by 930: the gate in its south wall with the bar across it on two posts, the guards' fire, the feast cave open to the north.")
room('room:kennel', 'Kennel',
     outline=[[928, 2752], [1536, 2688], [1920, 2880], [1984, 3328], [1728, 3648], [928, 3584]],
     floor=0, ceiling=448, ceiling_points=[[1472, 3168, 544]], theme='theme:den', ambient=20, rough=ROUGH,
     platforms=[{'at': [968, y], 'size': [24, 24], 'rise': 192, 'surface': PLANK, 'top_surface': PLANK,
                 'notes': 'Stake of the hurdle'} for y in (2864, 2928, 2992, 3344, 3408, 3472)],
     notes="A side cave off the feast cave, fenced from it by a hurdle of stakes with a gap; straw, bones and a trough.")
room('room:chief_den', "Chieftain's den",
     outline=[[-2688, 3328], [-1728, 3328], [-1376, 3456], [-1376, 3968], [-1664, 4288], [-2432, 4416], [-2944, 4224],
              [-3136, 3968], [-3136, 3584]],
     floor=32, ceiling=576, ceiling_points=[[-2272, 3840, 704]], theme='theme:den', ambient=17, rough=ROUGH,
     platforms=[
         {'id': 'platform:dais', 'at': [-2752, 3968], 'size': [448, 320], 'rise': 32, 'surface': ROCK, 'top_surface': FLOOR,
          'notes': "The rock dais of the Chieftain's seat."},
         {'id': 'platform:seat', 'outline': [[-2896, 4032], [-2608, 4032], [-2640, 4112], [-2864, 4112]], 'base': 32, 'rise': 112,
          'surface': ROCK, 'top_surface': ROCK, 'notes': "The Chieftain's seat of piled boulders (the lair's heart: click to break it)."},
         {'id': 'platform:oar_1', 'at': [-2272, 4336], 'size': [32, 16], 'rise': 352, 'surface': PLANK, 'top_surface': PLANK,
          'notes': "An oar of Nystor's boats stood against the north wall as a trophy."},
         {'id': 'platform:oar_2', 'at': [-2080, 4304], 'size': [32, 16], 'rise': 352, 'surface': PLANK, 'top_surface': PLANK,
          'notes': 'A second oar.'},
     ],
     walls=[{'wall': 'south', 'panels': [{'offset': 256, 'length': 448, 'bottom': 96, 'height': 288, 'surface': CANVAS,
                                          'id': 'panel:sail', 'notes': "The torn sail of a sunk boat, hung as a trophy."}]}],
     notes="A cave about 1,750 by 1,100 one step up from the feast cave: the Chieftain's seat of boulders on a dais by the west wall, oars and a torn sail of Captain Nystor's boats as trophies, the larder's plank door in the west wall.")
room('room:larder', "Chieftain's larder",
     outline=[[-4096, 3584], [-3168, 3584], [-3168, 4224], [-3392, 4352], [-3968, 4352], [-4160, 4096], [-4160, 3776]],
     floor=32, ceiling=416, theme='theme:den', ambient=21,
     store=True,  # D-7 (2026-11-20): the Chieftain's larder is a storeroom (its casks, barrels and sacks may stand together)
     beams=[{'path': [[-4160, 4096], [-3168, 4096]], 'width': 32, 'bottom': 352, 'depth': 32, 'surface': BEAM,
             'notes': "The meat beam with its hooks."}],
     notes="A cold low cave behind the plank door, about 1,000 by 770: the meat beam, casks and sacks, and the cargo of Nystor's sunk boats.")

# ------------------------------------------------------------------------------------------------ the works
room('room:quarry_ramp', 'Quarry ramp',
     path=[[-192, 4064], [-192, 4544], [-64, 4928], [-64, 5120]], width=448, smooth=1,
     floor=0, slope={'to': 384}, ceiling=448, theme='theme:den', ambient=19,
     notes="A rough ramp climbing 384 north out of the feast cave, scored by dragged boulders.")
QUARRY = [[-576, 5152], [320, 5152], [704, 5344], [832, 5696], [832, 6144], [576, 6400], [0, 6496], [-512, 6432],
          [-896, 6176], [-960, 5728], [-800, 5344]]
room('room:quarry', 'Boulder quarry', outline=QUARRY, floor=384, ceiling=1088,
     ceiling_points=[[-64, 5856, 1216], [-640, 5856, 1120], [448, 5856, 1120]],
     theme='theme:den', ambient=18, rough=ROUGH,
     platforms=[
         {'outline': [[-848, 5936], [-480, 6176], [-288, 6336], [-544, 6352], [-816, 6128]], 'rise': 96,
          'top_slope': {'to': 224, 'toward': 'north'}, 'surface': ROCK, 'top_surface': FLOOR,
          'notes': "A rubble slope against the north-west wall where the ogres break the rock."},
         {'outline': octagon(-640, 5504, 128), 'rise': 64, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Broken rock'},
     ],
     notes="A cave about 1,800 by 1,350 whose walls the ogres break up for boulders: a rubble slope, heaps of rounded boulders, timber levers; the ramp comes up in the south, the chute leaves east.")
room('room:chute', 'Boulder chute',
     path=[[864, 5920], [1472, 5920], [1888, 6080], [2176, 6080]], width=448, smooth=1,
     floor=384, slope={'to': 128}, ceiling=832, theme='theme:chute', ambient=14,
     parapets=[{'path': [[880, 5744], [1472, 5744], [1888, 5904], [2160, 5904]], 'height': 32, 'thickness': 24, 'surface': BEAM,
                'notes': 'Timber kerb of the trough, north side'},
               {'path': [[880, 6096], [1472, 6096], [1888, 6256], [2160, 6256]], 'height': 32, 'thickness': 24, 'surface': BEAM,
                'notes': 'Timber kerb of the trough, south side'}],
     notes="A timber-floored trough falling 256 east from the quarry to the throwing ledge, worn smooth by boulders, daylight ahead.")
LEDGE = [[2336, 5376], [2592, 5376], [2592, 4928], [2912, 4928], [2912, 5376], [3136, 5376], [3136, 6976], [2528, 7104],
         [2208, 6784], [2208, 5760]]
room('room:river_ledge', 'Throwing ledge', outline=LEDGE, floor=128, ceiling=832,
     ceiling_points=[[2672, 6176, 896], [3136, 6176, 1024]],
     theme='theme:den', ambient=12,
     platforms=[
         {'id': 'platform:rack_post_w', 'at': [2616, 5584], 'size': [32, 32], 'rise': 224, 'surface': PLANK, 'top_surface': PLANK,
          'notes': "The rack's west post."},
         {'id': 'platform:rack_post_e', 'at': [2888, 5584], 'size': [32, 32], 'rise': 224, 'surface': PLANK, 'top_surface': PLANK,
          'notes': "The rack's east post."},
     ],
     notes="A shelf about 900 by 1,600 in the bluff, its east side open over the river gorge above a parapet of rock 80 high; the boulder heap on its timber rack at the south end, at the head of the slide (a slot 320 wide cut 448 into the rock to the south, unlit); the chute comes in from the west.")
room('room:gorge', 'River gorge', outline=rect(3168, 5376, 4128, 6976), floor=-320, ceiling=832,
     theme='theme:gorge', ambient=2,
     walls=[{'wall': 'east', 'panels': [{'offset': 0, 'length': 1600, 'bottom': 552, 'height': 600, 'surface': HILLS,
                                         'notes': "The hills beyond the river, the picture once across the far wall above the far cliff, up to the sky."}]}],
     notes="The river gorge below the throwing ledge: flowing water 448 below the ledge, rock cliffs north, south and west (the bluff), the far cliff on the east rising to just under the ledge, the far bank and the river bending away as one picture (1600 x 600, A6's xogorge laid once), the sky as the roof.")

# ------------------------------------------------------------------------------------------------ openings
op('open:gate', 'room:mouth', 'room:gate_yard', link='link:mouth_gate', width=320, height=384,
   notes="The log gate, barred from inside.")
op('open:mouth_midden', 'room:mouth', 'room:midden', link='link:mouth_midden', width=288, height=320,
   notes="The midden crack's foot: a dark crack in the mouth's west wall.")
op('open:midden_den', 'room:midden', 'room:bone_den', link='link:midden_bone_den', width=320, height=320)
op('open:den_feast', 'room:bone_den', 'room:feast_cave', link='link:bone_den_feast', width=320, height=352,
   notes="The bone den's mouth onto the feast cave's terrace.")
op('open:feast_gate_yard', 'room:feast_cave', 'room:gate_yard', link='link:feast_gate_yard', width=896, height=512)
op('open:feast_kennel', 'room:feast_cave', 'room:kennel', link='link:feast_kennel', width=640, height=384,
   notes="The kennel's mouth; the hurdle of stakes stands in it, a gap in its middle.")
op('open:feast_chief', 'room:feast_cave', 'room:chief_den', link='link:feast_chief_den', width=288, height=416,
   notes="One step of 32 up into the Chieftain's den.")
op('open:chief_larder', 'room:chief_den', 'room:larder', link='link:chief_den_larder', width=224, height=288,
   notes="The larder's plank door.")
op('open:feast_ramp', 'room:feast_cave', 'room:quarry_ramp', link='link:feast_quarry_ramp', width=384, height=416)
op('open:ramp_quarry', 'room:quarry_ramp', 'room:quarry', link='link:quarry_ramp_quarry', width=384, height=416)
op('open:quarry_chute', 'room:quarry', 'room:chute', link='link:quarry_chute', width=384, height=416)
op('open:chute_ledge', 'room:chute', 'room:river_ledge', link='link:chute_ledge', width=384, height=416)
op('open:ledge_gorge', 'room:river_ledge', 'room:gorge', link='link:ledge_gorge', width=1408, height=600, sill=80,
   notes="The ledge's open east side over the gorge, above a parapet of rock 80 high.")

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:den', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-27 Ogre Lair at L3/L4: the plan's thirteen spaces as thirteen rooms in the plan's frame (x east, y north, the mouth's daylight edge at y 0, heights from the arrival floor). Written by output/studio_cal/xd27/tools/gen.py."}

if '--areas' in sys.argv:
    tot = 0
    for r in rooms:
        if 'outline' in r:
            a = area(r['outline'])
        else:
            p = r['path']
            ln = sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))
            a = ln * r['width']
        tot += a
        print(f"{r['id']:22s} {a / 1e6:6.2f}")
    print('total', round(tot / 1e6, 2))
    sys.exit(0)

if '--l3' in sys.argv:
    L3.mkdir(parents=True, exist_ok=True)
    (L3 / 'rooms.yml').write_text(yaml.safe_dump(rooms_doc, sort_keys=False, allow_unicode=True, width=120))
    print('L3 rooms written')
    sys.exit(0)

exec(open(Path(__file__).with_name('gen_objects.py')).read())
