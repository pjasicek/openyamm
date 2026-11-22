import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# STALE (lane A7, 2026-11-20, seventh session): do NOT run. XD-05's L4 (devdocs/xeen/briefs/xd05/L4) has been
# edited directly since the second session (A3's hooks, the lamp rule, merge point 15's gate pair): this generator
# would undo them. Edit L4 and use `oymap fmt`; the recorded states are in L4/.oymap/history.
import sys
if __name__ == "__main__" and "--i-know-it-is-stale" not in sys.argv:
    sys.exit("gen.py is stale: edit L4 directly (see the header)")
"""XD-05 Orc Caves, L4: writes rooms.yml, objects.yml, wiring.yml and project.yml of
devdocs/xeen/briefs/xd05/L4 from the plan below (L3's topology, rooms enlarged to the shipped median, the drum hall
and the bat chimney each one room). Rerun after every change here; never hand-edit the written files while this
generator is in use (NOTES.md says when it was retired)."""
import math
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
L4 = R / 'devdocs/xeen/briefs/xd05/L4'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


ROCK = S('gcav1flr', 256, 256)          # Ogre Fortress cave walls and roofs
FLOOR = S('gcav2flr', 128, 128, scale=2)  # its dark cave floor
WET = S('gcav2flr', 128, 128, scale=2)    # the deep caves' walls: the same blue-black rock
STRAW = S('gkp1flr', 128, 128)          # the keep's straw bedding
PLANK = S('gkp1ceil', 128, 128)         # the keep's planked, beamed boards
POST = S('t66abc10a', 32, 128)          # the keep's timber posts
STONE = S('gkp1-bs1', 128, 256)         # the keep's block masonry
PALIS = S('xopalis', 128, 256)          # generated: palisade logs
DRUMSIDE = S('xodrumsd', 128, 128)
DRUMTOP = S('xodrumtp', 128, 128, fit=True)

themes = [
    {'id': 'theme:rock', 'wall': ROCK, 'floor': FLOOR, 'ceiling': ROCK,
     'notes': "The caves: MM8 Ogre Fortress (d12) rock gcav1flr on walls and roofs, its dark floor rock gcav2flr underfoot (as d12 lays them)."},
    {'id': 'theme:warren', 'wall': ROCK, 'floor': STRAW, 'ceiling': ROCK,
     'notes': "The warren's living caves: d12's rock with the keep's straw bedding (gkp1flr) on the floor."},
    {'id': 'theme:wet', 'wall': WET, 'floor': FLOOR, 'ceiling': WET,
     'notes': "The deep caves (chimney, pool, back tunnel): d12's blue-black floor rock gcav2flr on the walls too, darker and wetter than the front."},
    {'id': 'theme:palisade', 'wall': PALIS, 'floor': FLOOR, 'ceiling': ROCK, 'door': S('gkp103a', 128, 256),
     'notes': "The palisade: generated upright logs (xopalis, in d12's timber) on walls, d12's plank doors (gkp103a/b) as the gate's leaves."},
    {'id': 'theme:deck', 'wall': ROCK, 'floor': PLANK, 'ceiling': ROCK,
     'notes': "Firing steps and their stairs: d12's planked boards (gkp1ceil) as decking on the cave rock."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octagon(cx, cy, r):
    k = round(r * math.tan(math.pi / 8))
    return [[cx - k, cy - r], [cx + k, cy - r], [cx + r, cy - k], [cx + r, cy + k], [cx + k, cy + r], [cx - k, cy + r],
            [cx - r, cy + k], [cx - r, cy - k]]


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


# ------------------------------------------------------------------------------------------------ the front
room('room:cave_mouth', 'Cave mouth',
     outline=[[-640, 0], [640, 0], [704, 320], [512, 576], [384, 960], [-384, 960], [-576, 640], [-704, 256]],
     floor=0, ceiling=640, ceiling_points=[[0, 448, 768], [-256, 704, 704], [256, 704, 704]],
     theme='theme:rock', ambient=8,
     notes="A funnel 1,408 wide at the daylight (the south wall, all exit panel: the X1 hills) narrowing to 768 at the outer yard. Skull torches on poles at the inner end, bones and boulders.")
room('room:palisade_cave', 'Palisade cave, outer yard',
     outline=[[-1024, 1024], [1024, 1024], [1216, 1152], [1280, 1408], [1280, 1792], [-1280, 1792], [-1280, 1408], [-1216, 1152]],
     floor=0, ceiling=832, ceiling_points=[[0, 1344, 1024], [-640, 1344, 960], [640, 1344, 960]],
     theme='theme:rock', ambient=12,
     walls=[{'wall': 'north', 'surface': PALIS}],
     notes="The approach in front of the palisade (its north wall, upright logs). The firing steps stand behind its outer two thirds: there the palisade is a fence 256 high with the cave open above it; the gate between them.")
room('room:firing_step_w', 'Firing step, west', space='zone:firing_step', outline=rect(-1280, 1856, -448, 2240),
     floor=192, ceiling=832, theme='theme:deck', ambient=14,
     walls=[{'wall': 'south', 'surface': PALIS}, {'wall': 'east', 'surface': PALIS}],
     notes="Plank walkway 832 by 384, 192 up, behind the palisade's west third: archers shoot over the palisade and down into the gate passage through a murder hole.")
room('room:firing_step_e', 'Firing step, east', space='zone:firing_step', outline=rect(448, 1856, 1280, 2240),
     floor=192, ceiling=832, theme='theme:deck', ambient=14,
     walls=[{'wall': 'south', 'surface': PALIS}, {'wall': 'west', 'surface': PALIS}],
     notes="Mirror of the west step; the signal drum stands at its east end beside the doorway to the upper ledge.")
room('room:palisade_gate', 'Gate passage', space='room:palisade_yard', outline=rect(-384, 1856, 384, 2752),
     floor=0, ceiling=640, theme='theme:palisade', ambient=14,
     notes="The timber passage behind the palisade gate, 768 wide, between the firing steps and their stairs; the gate's two hinged leaves in its south wall, a murder hole in each side wall.")
room('room:stair_w', 'Firing step stair, west', space='room:palisade_yard', outline=rect(-1280, 2304, -832, 2752),
     floor=0, slope={'to': 192, 'toward': 'south', 'steps': 6, 'tread': PLANK, 'riser': POST}, ceiling=640,
     theme='theme:deck', ambient=14, notes="Six timber steps of 32 up from the inner yard to the west firing step (L1's ladder).")
room('room:stair_e', 'Firing step stair, east', space='room:palisade_yard', outline=rect(832, 2304, 1280, 2752),
     floor=0, slope={'to': 192, 'toward': 'south', 'steps': 6, 'tread': PLANK, 'riser': POST}, ceiling=640,
     theme='theme:deck', ambient=14, notes="Mirror of the west stair.")
room('room:palisade_yard', 'Palisade cave, inner yard',
     outline=[[-1280, 2816], [1280, 2816], [1280, 3456], [1088, 3648], [-1088, 3648], [-1280, 3456]],
     floor=0, ceiling=640, ceiling_points=[[0, 3232, 832], [-768, 3232, 768], [768, 3232, 768]],
     theme='theme:rock', ambient=14,
     notes="The cave behind the palisade: the gate passage and both stairs open off its south wall, the run leaves its north-east.")

# ------------------------------------------------------------------------------------------------ the run
room('room:twisting_run', 'Twisting run, lower ramp', outline=rect(640, 3712, 1088, 4160), floor=0,
     slope={'to': -96, 'toward': 'north'}, ceiling=448, theme='theme:rock',
     notes="The run's first leg, falling gently north out of the inner yard.")
room('room:run_bend', 'Twisting run, bend', space='room:twisting_run',
     outline=[[512, 4224], [1216, 4224], [1472, 4480], [1472, 4992], [1280, 5184], [64, 5184], [64, 4864], [256, 4480]],
     floor=-96, ceiling=512, ceiling_points=[[768, 4704, 608]], theme='theme:rock',
     notes="The S-bend's level belly swinging east under the upper ledge and back west; the ledge looks down into it through its east wall (288 down over a rock lip).")
room('room:run_upper', 'Twisting run, upper ramp', space='room:twisting_run', outline=rect(128, 5248, 640, 5696),
     floor=-96, slope={'to': -256, 'toward': 'north'}, ceiling=384, theme='theme:rock',
     notes="The last leg, falling north into the cookfire cave.")
room('room:upper_ledge', 'Upper ledge',
     path=[[2048, 7488], [2048, 6912], [1760, 6528], [1760, 2048], [1344, 2048]], width=320,
     floor=192, ceiling=576, theme='theme:rock',
     notes="A natural ledge 320 wide and about 6,000 long at 192, from the chimney's top landing south to the east firing step. Two windows in its west side over a 64 rock lip look down into the cookfire cave (448 down) and the run's bend (288 down); the party can drop, not climb back.")

# ------------------------------------------------------------------------------------------------ the warren
room('room:cookfire_cave', 'Cookfire cave',
     outline=[[-896, 5760], [1024, 5760], [1408, 6016], [1408, 7040], [1088, 7296], [-896, 7296], [-1280, 7040], [-1280, 6016]],
     floor=-256, ceiling=512, ceiling_points=[[64, 6528, 832], [64, 6144, 704], [64, 6912, 704], [-512, 6528, 704], [640, 6528, 704]],
     theme='theme:rock', ambient=16,
     platforms=[
         {'id': 'platform:hearth', 'outline': octagon(64, 6528, 192), 'rise': 40, 'surface': STONE,
          'top_surface': S('t66flr2', 128, 128), 'notes': "The stone hearth ring round the great fire, d12's masonry and flags."},
         {'at': [64, 6176], 'size': [448, 96], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench'},
         {'at': [64, 6880], 'size': [448, 96], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench'},
         {'at': [-288, 6528], 'size': [96, 384], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench'},
         {'at': [416, 6528], 'size': [96, 384], 'rise': 24, 'surface': ROCK, 'top_surface': FLOOR, 'notes': 'Rock bench'},
     ],
     notes="A round cave about 2,700 by 1,500, the hearth ring in the middle under a roof that rises to the smoke hole over the fire; four low rock benches round it. Exits: the run (south), the ramp down to the drum hall (north), the hollows and the shaman's steps (west); the ledge's window high in the east wall.")
room('room:sleeping_hollows', 'Sleeping hollows',
     outline=[[-1344, 5952], [-1344, 6400], [-1920, 6464], [-2432, 6400], [-2944, 6464], [-3456, 6400], [-3776, 6272],
              [-3776, 5760], [-3520, 5568], [-3072, 5632], [-2816, 5760], [-1984, 5760], [-1728, 5632], [-1472, 5696]],
     floor=-224, ceiling=288, theme='theme:warren', ambient=20,
     notes="A crooked passage 2,400 long running west from the cookfire, 32 above it, with sleeping hollows off it (south-east by the entrance, south-west, the west end). The pit's rim is the straight stretch of the south wall; drag marks lead to the boulder in the straight west wall.")
room('room:prisoner_pit', 'Prisoner pit',
     outline=[[-2624, 4992], [-2176, 4992], [-1984, 5184], [-1984, 5504], [-2048, 5696], [-2752, 5696], [-2816, 5504], [-2816, 5184]],
     floor=-480, ceiling=224, theme='theme:warren', ambient=22,
     notes="A round pit about 830 by 700 whose floor is 256 below the hollows; the rim is the doorway in its north wall, closed by the cage gate of lashed poles, a rope ladder down from it.")
room('room:loot_cache', 'Plunder cache',
     outline=[[-4224, 5632], [-3840, 5696], [-3840, 6208], [-4160, 6336], [-4416, 6080], [-4416, 5824]],
     floor=-224, ceiling=160, theme='theme:warren', ambient=22,
     notes="A low side cave (384 clear) behind the boulder at the hollows' west end, heaped with the farms' plunder.")
room('room:shaman_steps', "Shaman's steps", space='room:shaman_den', outline=rect(-1664, 6720, -1344, 7040),
     floor=-256, slope={'to': -192, 'toward': 'west', 'steps': 2}, ceiling=256, theme='theme:rock', ambient=18,
     notes="A short passage with two rock steps of 32 up from the cookfire to the den; the hide curtain hangs at its far end.")
room('room:shaman_den', "Shaman's den",
     outline=[[-2816, 6528], [-1984, 6528], [-1728, 6720], [-1728, 7616], [-2048, 7872], [-2816, 7872], [-3136, 7616], [-3136, 6784]],
     floor=-192, ceiling=320, ceiling_points=[[-2432, 7200, 448]], theme='theme:warren', ambient=18,
     walls=[{'wall': 'west', 'surface': S('xobones', 128, 256)}],
     platforms=[
         {'id': 'platform:dais', 'at': [-2912, 7200], 'size': [320, 512], 'rise': 32, 'surface': ROCK, 'top_surface': FLOOR,
          'notes': "The dais before the wall of bones."},
         {'id': 'platform:drum_spirit', 'outline': octagon(-2912, 7200, 96), 'base': 32, 'rise': 112,
          'surface': DRUMSIDE, 'top_surface': DRUMTOP, 'notes': "The spirit drum on the dais (the second drum)."},
         {'id': 'platform:hide_curtain', 'at': [-1744, 7200], 'size': [16, 320], 'rise': 320, 'solid': False,
          'surface': S('xohide', 128, 256, scale=1.25), 'end_surface': S('xohide', 128, 256, uneven=True), 'top_surface': S('xohide', 128, 256),
          'notes': "The hide curtain across the doorway from the steps: drawn, walked through."},
     ],
     notes="An oval den about 1,400 by 1,350 thick with smoke; the west wall is rock set with skulls and bones; the spirit drum on a rock dais before it, the shaman's chest beside it, green spirit fire in two torches and a bubbling cauldron.")

# ------------------------------------------------------------------------------------------------ the drum hall
RIM = [[-1408, 7808], [1408, 7808], [1792, 8192], [1792, 9472], [1408, 9472], [1408, 8192], [-1408, 8192],
       [-1408, 10304], [-1792, 10304], [-1792, 8192]]
DECK = (-960, 10176)
hall_platforms = [
    {'id': 'platform:rim', 'outline': RIM, 'rise': 256, 'surface': ROCK, 'top_surface': FLOOR,
     'notes': "The top terrace along the south wall, the west shelf to the scaffold's gangway and the east top terrace to the chimney: one U of rock 256 above the floor."},
    {'outline': [[-1392, 8208], [-592, 8208], [-592, 8400], [-976, 8720], [-1392, 8944]], 'rise': 704, 'surface': ROCK, 'top_surface': ROCK,
     'notes': "The south-west buttress: a rock spur between the south and west terraces, crowned with skull torches."},
    {'outline': [[592, 8208], [1392, 8208], [1392, 8624], [976, 8624], [592, 8432]], 'rise': 704, 'surface': ROCK, 'top_surface': ROCK,
     'notes': "The south-east buttress."},
    # The scaffold: a plank deck on posts, 384 over the floor, its south and east sides open over a rail.
    {'id': 'platform:deck', 'at': list(DECK), 'size': [704, 704], 'base': 368, 'rise': 16, 'surface': POST,
     'top_surface': PLANK, 'bottom_surface': PLANK, 'notes': "The drum scaffold's deck (zone:drum_scaffold)."},
    {'at': [-960, 9832], 'size': [704, 16], 'base': 384, 'rise': 48, 'surface': POST, 'top_surface': POST, 'notes': 'Rail, south'},
    {'at': [-616, 10184], 'size': [16, 688], 'base': 384, 'rise': 48, 'surface': POST, 'top_surface': POST, 'notes': 'Rail, east'},
    {'id': 'platform:drum_great', 'outline': octagon(DECK[0], DECK[1] + 128, 128), 'base': 384, 'rise': 176,
     'surface': DRUMSIDE, 'top_surface': DRUMTOP, 'notes': "The great war drum (the third drum)."},
]
for px in (-1288, -960, -632):
    for py in (9848, 10504):
        hall_platforms.append({'at': [px, py], 'size': [48, 48], 'rise': 368, 'surface': POST, 'top_surface': POST,
                               'notes': 'Scaffold post'})
room('room:drum_hall', 'Drum Hall',
     outline=[[-1408, 7808], [1408, 7808], [1792, 8192], [1792, 10304], [1408, 10688], [-1408, 10688], [-1792, 10304], [-1792, 8192]],
     floor=-640, ceiling=576,
     ceiling_points=[[0, 9216, 960], [-704, 9216, 896], [704, 9216, 896], [0, 8448, 896], [0, 9984, 896]],
     theme='theme:rock', ambient=16, platforms=hall_platforms,
     flights=[
         {'from': [0, 9088], 'to': [0, 8192], 'width': 1152, 'steps': 8, 'riser': ROCK, 'tread': FLOOR,
          'notes': "The south terraces: eight rock steps of 32 down from the top terrace to the floor."},
         {'from': [-640, 9344], 'to': [-1408, 9344], 'width': 768, 'steps': 8, 'riser': ROCK, 'tread': FLOOR,
          'notes': "The west terraces."},
         {'from': [640, 9024], 'to': [1408, 9024], 'width': 768, 'steps': 8, 'riser': ROCK, 'tread': FLOOR,
          'notes': "The east terraces."},
         {'from': [-1600, 10176], 'to': [-1312, 10176], 'from_height': -384, 'to_height': -256, 'width': 256, 'steps': 4,
          'open_below': True, 'riser': POST, 'tread': PLANK,
          'notes': "The gangway: four timber steps from the west shelf up to the scaffold."},
     ],
     notes="One natural amphitheatre 3,584 by 2,880: the top terrace along the south (the entry), a west shelf and an east top terrace (a U of rock 256 above the floor), three banks of eight rock steps down to the flat floor, two rock buttresses at the bowl's south corners, the drum scaffold standing free on posts over the floor's north-west, the back tunnel from the north wall beside it; the roof rises to 1,600 over the floor, lost in smoke.")
room('room:drum_hall_entry', 'Drum hall, entry ramp', space='room:drum_hall', outline=rect(-320, 7360, 320, 7744),
     floor=-256, slope={'to': -384, 'toward': 'north'}, ceiling=384, theme='theme:rock',
     notes="The ramp down from the cookfire's north side onto the top terrace; at its foot the whole hall opens below.")

# ------------------------------------------------------------------------------------------------ the deep caves
chim = [
    {'at': [2496, 8736], 'size': [640, 320], 'rise': 0, 'top_slope': {'to': 192, 'toward': 'east'}, 'notes': 'Gallery, north ramp'},
    {'at': [3008, 8704], 'size': [384, 384], 'rise': 192, 'notes': 'Gallery, north-east landing'},
    {'at': [3040, 8256], 'size': [320, 512], 'rise': 192, 'top_slope': {'to': 384, 'toward': 'south'}, 'notes': 'Gallery, east ramp'},
    {'at': [3008, 7776], 'size': [384, 448], 'rise': 384, 'notes': 'Gallery, south-east landing'},
    {'at': [2560, 7712], 'size': [512, 320], 'rise': 384, 'top_slope': {'to': 576, 'toward': 'west'}, 'notes': 'Gallery, south ramp'},
    {'at': [2080, 7712], 'size': [448, 320], 'rise': 576, 'notes': "Gallery, top landing (192, the upper ledge's level)"},
]
for p in chim:
    p.setdefault('surface', WET)
    p.setdefault('top_surface', FLOOR)
room('room:bat_chimney', 'Bat chimney', outline=rect(1856, 7552, 3200, 8896), floor=-384, ceiling=1216,
     ceiling_points=[[2528, 8224, 1344]], theme='theme:wet', ambient=19, platforms=chim,
     notes="A tall shaft 1,344 square and 1,600 high; a rock gallery is cut round its north, east and south walls, climbing from the shaft's foot (by the drum hall's door) to a top landing level with the upper ledge, looking back down into the shaft; bats roost in the dark top.")
room('room:snake_slope', 'Snake pool, wet slope', space='room:snake_pool', outline=rect(1856, 8960, 2240, 9472),
     floor=-384, slope={'to': -704, 'toward': 'north'}, ceiling=64, ceiling_slope={'to': -256, 'toward': 'north'},
     theme='theme:wet', ambient=18, notes="The wet slope from the chimney's foot down 320 into the snake cave.")
room('room:snake_pool', 'Snake pool',
     outline=[[1856, 9536], [2944, 9536], [3392, 9792], [3456, 10304], [3072, 10816], [2240, 10816], [1856, 10432]],
     floor=-704, ceiling=-128, ceiling_points=[[2688, 10176, 0]], theme='theme:wet', ambient=18,
     levels=[{'id': 'level:pool', 'outline': [[2560, 9792], [3072, 9728], [3264, 10048], [3136, 10432], [2688, 10496], [2496, 10176]],
              'floor': -736, 'surface': {'texture': 'wtrtyl'}, 'edge': WET,
              'notes': "The pool in the east lobe, a step below the shore: dark water (MM8's), a chest sunk in it."}],
     notes="A dripping kidney-shaped cave about 1,600 by 1,280; the east lobe is a shallow pool with a sunken chest.")
room('room:back_tunnel', 'Back tunnel',
     path=[[960, 10752, -640], [960, 11008, -544], [928, 11232, -448], [960, 11392, -384], [994, 11520, -384],
           [1088, 11614, -384], [1216, 11648, -384], [1536, 11680, -224], [1920, 11648, -128], [2048, 11682, -128],
           [2142, 11776, -128], [2176, 11904, -128], [2200, 12048, -48], [2176, 12224, 96], [2176, 12544, 320]],
     floor=-640, ceiling=-288, section={'outline': [[-128, 0], [128, 0], [192, 96], [176, 256], [96, 352], [-96, 352], [-176, 256], [-192, 96]]},
     theme='theme:wet', ambient=18,
     notes="A narrow rock tunnel climbing 960 in about 2,900: north out of the drum hall, a level bend east, a long climb east, a bend north and the last steep climb to the back gate, drying toward the daylight.")
room('room:back_gate', 'Back gate',
     outline=[[1728, 12608], [2624, 12608], [2752, 12800], [2752, 13440], [1600, 13440], [1600, 12800]],
     floor=320, ceiling=832, theme='theme:rock', ambient=16,
     walls=[{'wall': 'north', 'panels': [{'id': 'panel:back_gate', 'at': 'centre', 'length': 160, 'height': 320,
                                          'surface': S('xobackgt', 128, 256, fit=True),
                                          'notes': "The back gate to Mount Firestone, sealed until X7 exists (was exit:x7; NOTES 'Sealed exits')."}]}],
     platforms=[{'at': [2672, 13024], 'size': [96, 320], 'rise': 40, 'surface': POST, 'top_surface': PLANK, 'notes': 'Plank bench'},
                {'at': [1992, 13428], 'size': [24, 24], 'base': 160, 'rise': 64, 'surface': POST, 'top_surface': POST, 'notes': "Bar bracket: a timber chock under the bar's west end (the bar rests on it)"},
                {'at': [2360, 13428], 'size': [24, 24], 'base': 160, 'rise': 64, 'surface': POST, 'top_surface': POST, 'notes': "Bar bracket, east"}],
     notes="A rough guardroom at the tunnel's head, about 1,150 by 830, the barred gate to Mount Firestone's slopes in its north wall with daylight under it.")

# ------------------------------------------------------------------------------------------------ openings
op('open:mouth_palisade', 'room:cave_mouth', 'room:palisade_cave', link='link:mouth_palisade', width=512, height=448)
op('open:gate_w', 'room:palisade_cave', 'room:palisade_gate', link='link:palisade_gate', width=192, height=384, along=0.6667,
   reveal=POST, notes="The palisade gate's west leaf (a hinged plank door); a gate post 32 wide between the two leaves.")
op('open:gate_e', 'room:palisade_cave', 'room:palisade_gate', link='link:palisade_gate', width=192, height=384, along=0.3333,
   reveal=POST, notes="The palisade gate's east leaf.")
op('open:step_w_yard', 'room:firing_step_w', 'room:palisade_cave', link='link:firing_step_overlook', width=704, height=512, sill=64,
   notes="The west third of the palisade: a 64 parapet of logs, then open to the cave roof. Archers shoot down over it; the party can drop from the step, not climb to it.")
op('open:step_e_yard', 'room:firing_step_e', 'room:palisade_cave', link='link:firing_step_overlook', width=704, height=512, sill=64)
op('open:step_w_gate', 'room:firing_step_w', 'room:palisade_gate', width=192, height=192, sill=64, notes='Murder hole into the gate passage.')
op('open:step_e_gate', 'room:firing_step_e', 'room:palisade_gate', width=192, height=192, sill=64, notes='Murder hole into the gate passage.')
op('open:stair_w_step', 'room:stair_w', 'room:firing_step_w', width=320, height=320)
op('open:stair_e_step', 'room:stair_e', 'room:firing_step_e', width=320, height=320)
op('open:yard_stair_w', 'room:palisade_yard', 'room:stair_w', link='link:firing_step_stairs', width=320, height=320)
op('open:yard_stair_e', 'room:palisade_yard', 'room:stair_e', link='link:firing_step_stairs', width=320, height=320)
op('open:gate_yard', 'room:palisade_gate', 'room:palisade_yard', width=512, height=448)
op('open:yard_run', 'room:palisade_yard', 'room:twisting_run', link='link:yard_run', width=384, height=352)
op('open:run_bend', 'room:twisting_run', 'room:run_bend', width=384, height=352)
op('open:bend_upper', 'room:run_bend', 'room:run_upper', width=448, height=320)
op('open:run_cookfire', 'room:run_upper', 'room:cookfire_cave', link='link:run_cookfire', width=448, height=320)
op('open:ledge_run', 'room:upper_ledge', 'room:run_bend', link='link:ledge_run_overlook', width=384, height=192, sill=64,
   notes="A window over a 64 rock lip; 288 down to the bend's floor.")
op('open:ledge_cookfire', 'room:upper_ledge', 'room:cookfire_cave', link='link:ledge_cookfire_overlook', width=384, height=192, sill=64,
   from_wall=2, to_wall=2,
   notes="A window just under the cookfire cave's smoke; 448 down to its floor.")
op('open:ledge_step_e', 'room:upper_ledge', 'room:firing_step_e', link='link:firing_step_upper_ledge', width=256, height=320,
   from_wall=4, to_wall=1)
op('open:chimney_ledge', 'room:bat_chimney', 'room:upper_ledge', link='link:chimney_upper_ledge', width=256, height=320)
op('open:cookfire_hollows', 'room:cookfire_cave', 'room:sleeping_hollows', link='link:cookfire_hollows', width=320, height=320)
op('open:cookfire_shaman', 'room:cookfire_cave', 'room:shaman_steps', link='link:cookfire_shaman', width=256, height=320)
op('open:shaman_steps_den', 'room:shaman_steps', 'room:shaman_den', width=256, height=320)
op('open:hollows_pit', 'room:sleeping_hollows', 'room:prisoner_pit', link='link:hollows_prisoner_pit', width=256, height=256,
   notes="The pit's rim: the cage gate of lashed poles, the rope ladder down from it; 256 sheer on the pit side.")
op('open:hollows_loot', 'room:sleeping_hollows', 'room:loot_cache', link='link:hollows_loot_cache', width=256, height=256,
   notes="Behind the boulder (a secret door).")
op('open:cookfire_entry', 'room:cookfire_cave', 'room:drum_hall_entry', link='link:cookfire_drum_hall', width=448, height=384)
op('open:entry_hall', 'room:drum_hall_entry', 'room:drum_hall', width=576, height=512, notes="The view over the hall opens here.")
op('open:rim_chimney', 'room:drum_hall', 'room:bat_chimney', link='link:drum_hall_chimney', width=320, height=512,
   notes="From the east top terrace into the shaft's foot.")
op('open:chimney_slope', 'room:bat_chimney', 'room:snake_slope', link='link:chimney_snake_pool', width=256, height=320)
op('open:slope_pool', 'room:snake_slope', 'room:snake_pool', width=320, height=384)
op('open:hall_tunnel', 'room:back_tunnel', 'room:drum_hall', link='link:drum_hall_back_tunnel', shape='section')
op('open:tunnel_gate', 'room:back_tunnel', 'room:back_gate', link='link:back_tunnel_gate', shape='section')

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:rock', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-05 Orc Caves at L4, in the L3 sketch's frame (x east, y north, the cave mouth's daylight edge at y 0, heights from the arrival floor), rooms enlarged to the shipped median and the drum hall and bat chimney each drawn as one room (levels, flights and platforms inside). Written by output/studio_cal/xd05/tools/gen.py."}

# ================================================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:cave_mouth', 'at': [0, 448], 'facing': 90,
                    'notes': "Inside the skull-hung mouth, facing in; daylight behind."}
objects['doors'] = [
    {'id': 'door:gate_w', 'opening': 'open:gate_w', 'kind': 'hinged', 'hinge': 'left', 'thickness': 16, 'speed': 70,
     'surface': S('gkp103a', 128, 256), 'back_surface': S('gkp103b', 128, 256),
     'notes': "The palisade gate's west leaf: d12's plank door, hinged at the west post, swinging in."},
    {'id': 'door:gate_e', 'opening': 'open:gate_e', 'kind': 'hinged', 'hinge': 'right', 'thickness': 16, 'speed': 70,
     'surface': S('gkp103b', 128, 256), 'back_surface': S('gkp103a', 128, 256),
     'notes': "The east leaf, hinged at the east post."},
    {'id': 'door:cage_gate', 'opening': 'open:hollows_pit', 'kind': 'slide_up', 'fold': True, 'tile': True, 'surface': S('xopoles', 128, 128),
     'notes': "The cage gate of lashed poles over the pit's rim (generated cut-out): it folds up into the lintel."},
    {'id': 'door:boulder', 'opening': 'open:hollows_loot', 'kind': 'slide_down', 'secret': True, 'thickness': 48,
     'surface': ROCK, 'notes': "The boulder before the plunder cache: a rock leaf flagged secret that sinks into the floor (the studio has no rolling door)."},
]
objects['movers'] = [
    {'id': 'mover:gate_bar', 'room': 'room:back_gate', 'at': [2176, 13416], 'size': [320, 32], 'bottom': 176, 'height': 32,
     'travel': [0, 0, 128], 'speed': 64, 'surface': POST, 'top_surface': POST, 'end_surface': POST,
     'notes': "The back gate's bar: a timber beam across the gate in two iron brackets; lifted, it rises clear above the gate."},
]
objects['plates'] = [
    {'id': 'plate:drag_1', 'room': 'room:sleeping_hollows', 'at': [-3200, 6016], 'size': [512, 128], 'surface': S('xodrag', 128, 128)},
    {'id': 'plate:drag_2', 'room': 'room:sleeping_hollows', 'at': [-3600, 6016], 'size': [256, 128], 'surface': S('xodrag', 128, 128)},
]
objects['ladders'] = [
    {'id': 'ladder:pit', 'room': 'room:prisoner_pit', 'at': [-2400, 5672], 'facing': 'n', 'height': 256, 'width': 96,
     'exit': [-2400, 5856], 'surface': S('t66abc10a', 32, 128, uneven=True), 'notes': "The rope ladder from the rim down into the pit (rails and rungs of rope-lashed poles)."},
]
objects['floors'] = [{'id': 'floor:pool', 'of': 'level:pool', 'kind': 'water'}]


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [255, 160, 80]
lights = [
    light('light:daylight', 'room:cave_mouth', [0, 192], 320, 1500, [255, 248, 228], notes="The X1 hills' daylight through the mouth."),
    light('light:mouth_torches', 'room:cave_mouth', [0, 820], 320, 700, FIRE),
    light('light:palisade_w', 'room:palisade_cave', [-380, 1660], 320, 900, FIRE),
    light('light:palisade_e', 'room:palisade_cave', [380, 1660], 320, 900, FIRE),
    light('light:step_w', 'room:firing_step_w', [-1160, 2140], 200, 700, FIRE),
    light('light:step_e', 'room:firing_step_e', [560, 2140], 200, 700, FIRE),
    light('light:yard', 'room:palisade_yard', [0, 3300], 260, 1300, FIRE),
    light('light:hearth', 'room:cookfire_cave', [64, 6528], 160, 2000, [255, 150, 70],
          pulse={'intensity': [0.75, 1.0], 'frequency': 1.3, 'phase': 0.1}, notes="The great fire in the hearth ring."),
    light('light:cauldron', 'room:cookfire_cave', [-300, 7180], 120, 700, FIRE),
    light('light:hollows_fire', 'room:sleeping_hollows', [-2432, 6300], 100, 900, [255, 140, 70],
          pulse={'intensity': [0.7, 1.0], 'frequency': 1.1, 'phase': 0.4}),
    light('light:den_w', 'room:shaman_den', [-2700, 7700], 200, 800, [120, 255, 140]),
    light('light:den_e', 'room:shaman_den', [-2700, 6700], 200, 800, [120, 255, 140]),
    light('light:den_cauldron', 'room:shaman_den', [-2200, 7650], 100, 600, [150, 255, 120],
          pulse={'intensity': [0.6, 1.0], 'frequency': 0.7}),
    light('light:hall_rim_w', 'room:drum_hall', [-800, 7950], 320, 1400, FIRE),
    light('light:hall_rim_e', 'room:drum_hall', [800, 7950], 320, 1400, FIRE),
    light('light:hall_fire', 'room:drum_hall', [320, 9792], 160, 1600, [255, 150, 70],
          pulse={'intensity': [0.75, 1.0], 'frequency': 1.2, 'phase': 0.6}),
    light('light:hall_buttress_w', 'room:drum_hall', [-1100, 8500], 800, 1200, FIRE),
    light('light:hall_buttress_e', 'room:drum_hall', [1100, 8400], 800, 1200, FIRE),
    light('light:scaffold', 'room:drum_hall', [-960, 10176], 600, 1300, [255, 160, 80], notes="The two braziers flanking the great drum."),
    light('light:chimney_foot', 'room:bat_chimney', [1980, 8700], 200, 700, FIRE),
    light('light:chimney_mid', 'room:bat_chimney', [2528, 8224], 700, 1400, [180, 190, 230]),
    light('light:pool', 'room:snake_pool', [2700, 10100], 300, 1300, [150, 200, 220], pulse={'intensity': [0.7, 1.0], 'frequency': 0.4}),
    light('light:tunnel_1', 'room:back_tunnel', [960, 11300], 250, 900, FIRE),
    light('light:tunnel_2', 'room:back_tunnel', [2176, 12000], 250, 900, FIRE),
    light('light:gate_w', 'room:back_gate', [1950, 13350], 200, 700, FIRE),
    light('light:gate_e', 'room:back_gate', [2400, 13350], 200, 700, FIRE),
    light('light:gate_day', 'room:back_gate', [2176, 13380], 40, 500, [255, 245, 220], notes="Daylight under the gate."),
    # The drums as they burn: off until set alight, then the fire, then embers.
    light('light:burn_signal', 'room:firing_step_e', [1120, 2128], 200, 1100, [255, 140, 50], on=False,
          pulse={'intensity': [0.6, 1.0], 'frequency': 2.0}),
    light('light:burn_spirit', 'room:shaman_den', [-2912, 7200], 200, 1000, [255, 140, 50], on=False,
          pulse={'intensity': [0.6, 1.0], 'frequency': 2.0, 'phase': 0.3}),
    light('light:burn_great', 'room:drum_hall', [-960, 10304], 500, 1600, [255, 140, 50], on=False,
          pulse={'intensity': [0.6, 1.0], 'frequency': 2.0, 'phase': 0.6}),
    light('light:ember_signal', 'room:firing_step_e', [1120, 2128], 120, 400, [200, 70, 30], on=False),
    light('light:ember_spirit', 'room:shaman_den', [-2912, 7200], 150, 400, [200, 70, 30], on=False),
    light('light:ember_great', 'room:drum_hall', [-960, 10304], 260, 600, [200, 70, 30], on=False),
]
objects['lights'] = lights

objects['chests'] = [
    {'id': 'chest:cache', 'room': 'room:loot_cache', 'at': [-4160, 5952], 'facing': 'e', 'kind': 'gt002',
     'treasure_level': 2, 'random_items': 3, 'gold': 400, 'notes': "A farmer's strongbox among the plunder: the warband's hoard, the map's one chest a level up (MAPS 0: Tres 1)."},
    {'id': 'chest:shaman', 'room': 'room:shaman_den', 'at': [-2880, 7600], 'kind': 'gt002',
     'treasure_level': 1, 'random_items': 2, 'notes': "The shaman's chest beside the dais."},
    {'id': 'chest:hollows', 'room': 'room:sleeping_hollows', 'at': [-3360, 5696], 'facing': 'e', 'kind': 'gt002',
     'treasure_level': 1, 'random_items': 2, 'notes': "In the south-west hollow."},
    {'id': 'chest:pool', 'room': 'room:snake_pool', 'at': [2944, 10112], 'facing': 'w', 'kind': 'gt002',
     'treasure_level': 1, 'random_items': 3, 'notes': "Sunk in the pool, knee-deep."},
]

objects['spawns'] = [
    {'id': 'spawn:step_w', 'room': 'room:firing_step_w', 'at': [-860, 2048], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "Archers on the west firing step: they shoot over the palisade."},
    {'id': 'spawn:step_e', 'room': 'room:firing_step_e', 'at': [760, 2048], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "Archers on the east firing step."},
    {'id': 'spawn:gate', 'room': 'room:palisade_gate', 'at': [0, 2400], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "The gate group waiting in the passage."},
    {'id': 'spawn:run', 'room': 'room:run_bend', 'at': [700, 4700], 'slot': 2, 'tier': 'b', 'group': 51,
     'notes': "Bats at the bend (tier b: the map's band is 4-10)."},
    {'id': 'spawn:cookfire_w', 'room': 'room:cookfire_cave', 'at': [-700, 6400], 'slot': 1, 'tier': 'b', 'group': 51},
    {'id': 'spawn:cookfire_e', 'room': 'room:cookfire_cave', 'at': [800, 6600], 'slot': 1, 'tier': 'a', 'group': 51},
    {'id': 'spawn:hollows', 'room': 'room:sleeping_hollows', 'at': [-2900, 6200], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "Asleep in the hollows."},
    {'id': 'spawn:den', 'room': 'room:shaman_den', 'at': [-2300, 7000], 'slot': 1, 'tier': 'a', 'group': 51},
    {'id': 'spawn:hall_s', 'room': 'room:drum_hall', 'at': [0, 8700], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "On the south terraces."},
    {'id': 'spawn:hall_w', 'room': 'room:drum_hall', 'at': [-1000, 9344], 'slot': 1, 'tier': 'b', 'group': 51,
     'notes': "On the west terraces."},
    {'id': 'spawn:hall_floor', 'room': 'room:drum_hall', 'at': [300, 9600], 'slot': 1, 'tier': 'a', 'group': 51,
     'notes': "On the floor."},
    {'id': 'spawn:chimney', 'room': 'room:bat_chimney', 'at': [2500, 8200], 'slot': 2, 'tier': 'b', 'group': 51},
    {'id': 'spawn:chimney_ne', 'room': 'room:bat_chimney', 'at': [3008, 8704], 'slot': 2, 'tier': 'b', 'group': 51},
    {'id': 'spawn:pool_w', 'room': 'room:snake_pool', 'at': [2300, 9900], 'slot': 3, 'tier': 'a', 'group': 51},
    {'id': 'spawn:pool_n', 'room': 'room:snake_pool', 'at': [2600, 10650], 'slot': 3, 'tier': 'a', 'group': 51},
]
objects['monsters'] = [
    {'id': 'monster:drum_master', 'room': 'room:drum_hall', 'monster': 11033, 'at': [-960, 10000], 'floor_height': -256,
     'facing': 270, 'hostile': True, 'immobile': True, 'group': 2,
     'notes': "The Drum-Master on his scaffold: his own boss row (11033, level 12)."},
    {'id': 'monster:shaman', 'room': 'room:shaman_den', 'monster': 11032, 'at': [-2650, 7200], 'facing': 0, 'hostile': True,
     'group': 3, 'name': 'Orc Shaman', 'notes': "The shaman before his spirit drum: an Orc Guard (11032, level 10; Xeen's Orc Shaman row is the level-20 warband's)."},
    {'id': 'monster:guard_w', 'room': 'room:back_gate', 'monster': 11032, 'at': [1900, 13200], 'facing': 270, 'hostile': True,
     'immobile': True, 'group': 4, 'notes': "Gate guard (Orc Guard 11032, level 10)."},
    {'id': 'monster:guard_e', 'room': 'room:back_gate', 'monster': 11032, 'at': [2450, 13200], 'facing': 270, 'hostile': True,
     'immobile': True, 'group': 4},
    {'id': 'monster:tam', 'room': 'room:prisoner_pit', 'monster': 358, 'at': [-2400, 5250], 'facing': 90, 'hostile': False,
     'immobile': True, 'group': 20, 'name': 'Tam',
     'notes': "Tam, Oslo's son, held for ransom (a human peasant)."},
]
# Hostility pass (2026-11-16): the Goblins, Bats and Spiders are the party's foes by MMerge's hostile.txt and not set on
# each other, but the table sets all three on Tam's kind (a human peasant, 358) and him on them: his captors and the
# pit's vermin could kill him before the party comes. They are kept from him, both ways.
# World of Xeen (2026-11-20): the Xeen families' relation to the party is world data (worlds/xeen/relations.yml);
# the map keeps only Tam apart from the Orcs, Bats and Snakes.
objects['relations'] = [{'of': [11030, 11031, 11032, 11033, 11300, 11301, 11302, 11480, 11481, 11482], 'toward': 358, 'relation': 'friendly',
                         'both_ways': True}]


def deco(id, rm, d, at, **kw):
    x = {'id': id, 'room': rm, 'decoration': d, 'at': at}
    x.update(kw)
    return x


decos = [
    # mouth
    deco('deco:mouth_skulltorch_w', 'room:cave_mouth', 'torskul0', [-300, 830]),
    deco('deco:mouth_skulltorch_e', 'room:cave_mouth', 'torskul0', [300, 830]),
    deco('deco:mouth_skulls_w', 'room:cave_mouth', 'sklplrev', [-430, 780]),
    deco('deco:mouth_skulls_e', 'room:cave_mouth', 'sklplrev', [420, 700]),
    deco('deco:mouth_bones_1', 'room:cave_mouth', '7dec18', [-200, 520]),
    deco('deco:mouth_bones_2', 'room:cave_mouth', 'dec19', [250, 330]),
    deco('deco:mouth_rock_w', 'room:cave_mouth', '6rock02', [-560, 300]),
    deco('deco:mouth_rock_e', 'room:cave_mouth', '6rock03', [560, 420]),
    # outer yard
    deco('deco:palisade_skulltorch_w', 'room:palisade_cave', 'torskul0', [-320, 1700]),
    deco('deco:palisade_skulltorch_e', 'room:palisade_cave', 'torskul0', [320, 1700]),
    deco('deco:palisade_bones_1', 'room:palisade_cave', 'dec29', [-1150, 1500]),
    deco('deco:palisade_corpse', 'room:palisade_cave', 'Corpse04', [1100, 1650]),
    deco('deco:palisade_bones_2', 'room:palisade_cave', 'dec29', [1150, 1450]),
    deco('deco:palisade_rock_1', 'room:palisade_cave', '6rock01', [-560, 1300]),
    deco('deco:palisade_rock_2', 'room:palisade_cave', '6rock06', [700, 1250]),
    # firing steps
    deco('deco:step_w_brazier', 'room:firing_step_w', 'torskul0', [-1180, 2140]),
    deco('deco:step_e_brazier', 'room:firing_step_e', 'torskul0', [540, 2150]),
    # inner yard
    deco('deco:yard_brazier', 'room:palisade_yard', '7dec02', [0, 3300]),
    deco('deco:yard_barrel_1', 'room:palisade_yard', '7dec32', [-1190, 3250]),
    deco('deco:yard_keg', 'room:palisade_yard', 'smlbarel', [-1190, 3370]),
    deco('deco:yard_barrel_2', 'room:palisade_yard', 'dec03', [1200, 3250]),
    deco('deco:yard_barrel_3', 'room:palisade_yard', 'dec03', [1200, 3360]),
    # run
    deco('deco:run_rock_1', 'room:run_bend', '6rock04', [1300, 4600]),
    deco('deco:run_rock_2', 'room:run_bend', '6rock05', [250, 5050]),
    deco('deco:run_bones', 'room:run_bend', 'dec29', [900, 4400]),
    # cookfire
    deco('deco:hearth_fire', 'room:cookfire_cave', 'dec04', [64, 6528]),
    deco('deco:cookfire', 'room:cookfire_cave', 'ckfyr00', [-300, 7180]),
    deco('deco:cookpot', 'room:cookfire_cave', 'cauld00', [-300, 7180], inside='deco:cookfire'),
    deco('deco:cook_plates', 'room:cookfire_cave', 'dec37', [-120, 6880]),
    deco('deco:cook_plate', 'room:cookfire_cave', 'dec36', [240, 6880]),
    deco('deco:cook_bowls', 'room:cookfire_cave', 'dec32', [416, 6460]),
    deco('deco:cook_trash', 'room:cookfire_cave', '7dec10', [1150, 6400]),
    deco('deco:cook_keg', 'room:cookfire_cave', 'smlbarel', [-1050, 6200]),
    deco('deco:cook_cask', 'room:cookfire_cave', '7dec21', [-600, 5840]),
    # hollows
    deco('deco:hollows_fire', 'room:sleeping_hollows', '7dec02', [-2432, 6300]),
    deco('deco:hollows_bed_1', 'room:sleeping_hollows', 'trasheap', [-1700, 5780]),
    deco('deco:hollows_bed_2', 'room:sleeping_hollows', '7dec01', [-3200, 5720]),
    deco('deco:hollows_bed_3', 'room:sleeping_hollows', 'trasheap', [-3560, 6260]),
    deco('deco:hollows_dirt', 'room:sleeping_hollows', '7dec11', [-2000, 6300]),
    deco('deco:hollows_plate', 'room:sleeping_hollows', 'dec36', [-2300, 6250]),
    # pit
    deco('deco:pit_bones', 'room:prisoner_pit', 'dec29', [-2650, 5150]),
    deco('deco:pit_bowl', 'room:prisoner_pit', 'foodbowl', [-2200, 5200]),
    deco('deco:pit_bucket', 'room:prisoner_pit', 'Bucket', [-2150, 5450]),
    # cache
    deco('deco:cache_bag_1', 'room:loot_cache', 'bag_A', [-4300, 5850]),
    deco('deco:cache_bag_2', 'room:loot_cache', 'bag01', [-4200, 6180]),
    deco('deco:cache_cask', 'room:loot_cache', '7dec21', [-4230, 5730]),
    deco('deco:cache_barrel', 'room:loot_cache', 'dec03', [-4160, 5705]),
    deco('deco:cache_heap', 'room:loot_cache', 'trasheap', [-4330, 6050]),
    # den
    deco('deco:den_torch_w', 'room:shaman_den', 'torch06', [-2700, 7872], wall='north', height=160),
    deco('deco:den_torch_e', 'room:shaman_den', 'torch06', [-2700, 6528], wall='south', height=160),
    deco('deco:den_skulls_1', 'room:shaman_den', 'sklplrev', [-2912, 7000]),
    deco('deco:den_skulls_2', 'room:shaman_den', 'sklplrev', [-2912, 7400]),
    deco('deco:den_bonecage', 'room:shaman_den', 'Bonecage', [-2300, 6750]),
    deco('deco:den_fire', 'room:shaman_den', 'ckfyr00', [-2200, 7650]),
    deco('deco:den_cauldron', 'room:shaman_den', 'cauld00', [-2200, 7650], inside='deco:den_fire'),
    deco('deco:den_mushrooms_1', 'room:shaman_den', 'mushrm01', [-3000, 6800]),
    deco('deco:den_mushrooms_2', 'room:shaman_den', 'mushrm02', [-2000, 6700]),
    # drum hall
    deco('deco:rim_brazier_1', 'room:drum_hall', 'torskul0', [-1100, 7900]),
    deco('deco:rim_brazier_2', 'room:drum_hall', 'torskul0', [-560, 7900]),
    deco('deco:rim_brazier_3', 'room:drum_hall', 'torskul0', [560, 7900]),
    deco('deco:rim_brazier_4', 'room:drum_hall', 'torskul0', [1100, 7900]),
    deco('deco:buttress_torch_w', 'room:drum_hall', 'torskul0', [-1100, 8500]),
    deco('deco:buttress_torch_e', 'room:drum_hall', 'torskul0', [1100, 8400]),
    deco('deco:hall_fire', 'room:drum_hall', 'dec04', [320, 9792]),
    deco('deco:hall_skulls_s', 'room:drum_hall', 'sklplrev', [700, 9250]),
    deco('deco:hall_skulls_w', 'room:drum_hall', 'sklplrev', [-560, 9800]),
    deco('deco:hall_skeleton', 'room:drum_hall', 'dec05', [-300, 8500]),
    deco('deco:hall_bones', 'room:drum_hall', '7dec18', [400, 8600]),
    deco('deco:scaffold_brazier_w', 'room:drum_hall', 'torskul0', [-1220, 10440], floor_height=-256),
    deco('deco:scaffold_brazier_e', 'room:drum_hall', 'torskul0', [-700, 10440], floor_height=-256),
    # chimney
    deco('deco:chimney_torch', 'room:bat_chimney', 'torch01', [1856, 8700], wall='west', height=160),
    deco('deco:chimney_guano', 'room:bat_chimney', 'trasheap', [2500, 8100]),
    deco('deco:chimney_bones', 'room:bat_chimney', 'dec29', [2300, 8300]),
    # pool
    deco('deco:pool_stalagmite_1', 'room:snake_pool', 'stlmite1', [2100, 10300]),
    deco('deco:pool_stalagmite_2', 'room:snake_pool', 'stlmite2', [3300, 9900]),
    deco('deco:pool_stalagmite_3', 'room:snake_pool', 'stlmite3', [2050, 10450]),
    deco('deco:chimney_stalagmite_1', 'room:bat_chimney', 'stlmite1', [2700, 8300]),
    deco('deco:hall_stalagmite_1', 'room:drum_hall', 'stlmite2', [1500, 10200]),
    deco('deco:hall_stalagmite_2', 'room:drum_hall', 'stlmite3', [600, 10500]),
    deco('deco:pool_mushroom', 'room:snake_pool', 'mushrm05', [1980, 10150]),
    deco('deco:pool_rock', 'room:snake_pool', 'rock10', [2400, 10600]),
    # tunnel
    # back gate
    deco('deco:gate_torch_w', 'room:back_gate', 'torch01', [1880, 13440], wall='north', height=160,
         notes="Wall torch in its iron bracket beside the gate, at MM7's wall-torch height (torch01 stands 133-189 over the floor in 7d10/7d13/7d16)."),
    deco('deco:gate_torch_e', 'room:back_gate', 'torch01', [2472, 13440], wall='north', height=160),
    deco('deco:gate_keg', 'room:back_gate', 'smlbarel', [2660, 13300]),
    deco('deco:gate_plate', 'room:back_gate', 'dec36', [2672, 13024], floor_height=360),
    deco('deco:gate_bones', 'room:back_gate', '7dec18', [1800, 12800]),
]
# Stalactites: MM7 has no stalactite art at run time (stltite1-3 are MM6 sprites with no runtime picture, no model), so
# each is drawn as geometry: three stacked hanging rock octagons narrowing downward, top tucked into the roof. Only in
# the wide caverns (the user, 2026-11-13); none in passages and tunnels. Heights measured from the first pass's build
# (floor and roof at each place).
TITES = [  # room, x, y, floor, roof
    ('room:cave_mouth', -330, 640, 0, 667), ('room:cave_mouth', 330, 560, 0, 660),
    ('room:palisade_cave', -900, 1300, 0, 898), ('room:palisade_cave', 960, 1380, 0, 895),
    ('room:palisade_cave', -380, 1560, 0, 931), ('room:palisade_cave', 300, 1200, 0, 937),
    ('room:palisade_yard', -900, 3300, 0, 733), ('room:palisade_yard', 900, 3420, 0, 711),
    ('room:palisade_yard', 420, 3400, 0, 680), ('room:palisade_yard', -300, 2950, 0, 701),
    ('room:cookfire_cave', -950, 6250, -256, 594), ('room:cookfire_cave', 1050, 6950, -256, 576),
    ('room:cookfire_cave', -780, 7050, -256, 572), ('room:cookfire_cave', 980, 6080, -256, 577),
    ('room:drum_hall', -300, 9500, -640, 909), ('room:drum_hall', 450, 10300, -640, 752),
    ('room:drum_hall', 1350, 9950, -640, 693), ('room:drum_hall', 1200, 10450, -640, 642),
    ('room:bat_chimney', 2300, 7950, -384, 1291), ('room:bat_chimney', 2850, 8450, -384, 1282),
    ('room:bat_chimney', 2150, 8650, -384, 1262),
    ('room:snake_pool', 2200, 10300, -704, -75), ('room:snake_pool', 3050, 9900, -736, -78),
    ('room:snake_pool', 2750, 10620, -704, -88), ('room:snake_pool', 2550, 9700, -704, -95),
]
# The roof at each corner of a stalactite's top octagon (absolute z, read from the first pass's built roof faces),
# so its top follows the sloping roof (top_heights) instead of leaving a gap.
TOPC = {(-330, 640): [686, 703, 712, 709, 691, 673, 668, 672], (330, 560): [700, 678, 660, 658, 671, 696, 712, 712], (-900, 1300): [870, 891, 916, 930, 917, 897, 879, 865], (960, 1380): [891, 874, 870, 876, 887, 903, 915, 911], (-380, 1560): [966, 975, 950, 912, 885, 885, 912, 950], (300, 1200): [865, 865, 907, 955, 982, 992, 967, 907], (-900, 3300): [725, 745, 756, 738, 720, 709, 709, 711], (900, 3420): [738, 723, 701, 685, 681, 688, 709, 731], (420, 3400): [789, 781, 758, 731, 699, 699, 731, 777], (-300, 2950): [657, 657, 683, 720, 746, 746, 720, 683], (-950, 6250): [571, 582, 602, 619, 605, 583, 567, 567], (1050, 6950): [603, 589, 568, 551, 548, 562, 583, 601], (-780, 7050): [585, 595, 592, 577, 559, 549, 553, 568], (980, 6080): [562, 551, 555, 572, 592, 603, 599, 582], (-300, 9500): [914, 923, 924, 915, 903, 893, 892, 902], (450, 10300): [795, 788, 770, 734, 708, 708, 734, 770], (1350, 9950): [715, 692, 674, 670, 670, 683, 702, 715], (1200, 10450): [667, 651, 631, 616, 617, 629, 653, 668], (2300, 7950): [1273, 1273, 1284, 1299, 1308, 1292, 1282, 1282], (2850, 8450): [1291, 1274, 1262, 1262, 1274, 1280, 1292, 1303], (2150, 8650): [1262, 1281, 1272, 1253, 1240, 1240, 1249, 1249], (2200, 10300): [-81, -68, -60, -65, -78, -88, -89, -89], (3050, 9900): [-92, -100, -95, -84, -72, -57, -61, -75], (2750, 10620): [-64, -64, -78, -98, -112, -112, -98, -78], (2550, 9700): [-114, -114, -103, -87, -75, -75, -87, -103]}
TITE_TIERS = [(96, 96), (60, 96), (28, 80)]  # radius, height: top tier first
for n, (rm, x, y, fl, roof) in enumerate(TITES):
    rr = next(r for r in rooms if r['id'] == rm)
    corners = TOPC[(x, y)]
    top = min(corners) - fl
    for k, (rad, h) in enumerate(TITE_TIERS):
        scale = 1.0 + 0.25 * ((n + k) % 3) / 2
        tex = ROCK if rm == 'room:snake_pool' else WET  # the other rock of d12, so it stands out from the roof
        p = {'outline': octagon(x, y, round(rad * scale)), 'base': top - h, 'rise': h, 'surface': tex,
             'top_surface': tex, 'bottom_surface': tex, 'notes': 'Stalactite' if k == 0 else 'Stalactite, lower'}
        if k == 0:
            p['top_heights'] = [c - fl - (top - h) for c in corners]
        rr.setdefault('platforms', []).append(p)
        top -= h
objects['decorations'] = decos
objects['sounds'] = [
    {'id': 'sound:drum_signal', 'room': 'room:firing_step_e', 'at': [1120, 2128], 'sound': 'xodrumsg', 'radius': 14000,
     'inner_radius': 2500, 'volume': 0.6, 'notes': "The signal drum's beat: the first layer, heard over the whole map."},
    {'id': 'sound:drum_spirit', 'room': 'room:shaman_den', 'at': [-2912, 7200], 'sound': 'xodrumsp', 'radius': 14000,
     'inner_radius': 2000, 'volume': 0.5, 'notes': "The spirit drum's rattling beat."},
    {'id': 'sound:drum_great', 'room': 'room:drum_hall', 'at': [-960, 10304], 'sound': 'xodrumgr', 'radius': 16000,
     'inner_radius': 3500, 'volume': 0.9, 'notes': "The great drum's boom, heard from the mouth."},
]
objects['exits'] = [
    {'id': 'exit:x1', 'room': 'room:cave_mouth', 'wall': 'south', 'size': [1024, 512], 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
     'to': 'exit:x1_hills', 'notes': "The daylight of the X1 hills: the mouth's whole south wall."},
]
objects['placeholders'] = [
    {'id': 'placeholder:spear_rack', 'room': 'room:drum_hall', 'stands_for': "A rack of orc spears on the drum scaffold",
     'at': [-1200, 10000], 'size': [64, 192, 192]},
    {'id': 'placeholder:cart_wheel', 'room': 'room:loot_cache', 'stands_for': "A farm cart's wheel leaning on the wall",
     'at': [-4300, 6200], 'size': [32, 160, 160]},
    {'id': 'placeholder:spits', 'room': 'room:cookfire_cave', 'stands_for': "Roasting spits over the hearth fire",
     'at': [64, 6528], 'size': [320, 32, 160]},
]

# ================================================================================================ wiring
WHY = ("Vertigo has not slept for a week: war drums boom out of the north hills every night, and every night orc raiders "
       "fall on another farm. The drums are in these caves: burn all three "
       "(the signal drum on the palisade's firing step, the shaman's spirit drum in the warren, and the great drum in "
       "the Drum Hall, where the Drum-Master beats it), and look for Tam, Oslo's boy, whom they carried off from his "
       "father's farm.")
var = lambda n: {'map_var': n}
events = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'effects': [{'message': WHY}], 'notes': "Say why the party is here (a one-shot timer: a load event's window is not shown)."},
    {'id': 'evt:exit_x1', 'preset': 'exit', 'source': 'exit:x1', 'title': 'Leave the Orc Caves'},
    {'id': 'evt:gate_w', 'preset': 'door', 'source': 'door:gate_w', 'title': 'Palisade gate', 'action': 'open', 'opens': ['door:gate_e'],
     'notes': "link:palisade_gate: a plain click opens both leaves; nothing locks it."},
    {'id': 'evt:gate_e', 'preset': 'door', 'source': 'door:gate_e', 'title': 'Palisade gate', 'action': 'open', 'opens': ['door:gate_w']},
    {'id': 'evt:palisade_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:palisade_cave', 'once': True,
     'text': "A palisade of logs blocks the cave. Orc archers on its firing steps!"},
]
for key, label, platform, sound in [('signal', 'Signal drum', 'platform:drum_signal', 'sound:drum_signal'),
                                     ('spirit', 'Spirit drum', 'platform:drum_spirit', 'sound:drum_spirit'),
                                     ('great', 'Great war drum', 'platform:drum_great', 'sound:drum_great')]:
    events.append({
        'id': f'evt:drum_{key}', 'preset': 'script', 'source': platform, 'title': label,
        'condition': {'map_var': {'name': f'drum_{key}', 'equals': 0}},
        'question': {'ask': "Destroy (Yes/No)?", 'answers': ['Yes', 'Y', 'yes', 'y'],
                     'message': "You have found a war drum of the Orcs!  Destroy?",
                     'wrong_text': "You leave the drum as it is, for now."},
        'effects': [
            {'set': {'var': var(f'drum_{key}'), 'value': 1}},
            {'add': {'var': var('drums_burnt'), 'value': 1}},
            {'set_texture': {'of': platform, 'to': 'xoburn'}},
            {'lights_on': f'light:burn_{key}'},
            {'add': {'var': 'Experience', 'value': 250}},
            {'lua': f"SOUND_OFF_{key}"},
        ],
        'text': f"The dry hide catches at once: the {label.lower()} goes up in flames, and its beat drops out of the din.",
        'else_effects': [{'text': f"Nothing is left of the {label.lower()} but a charred frame."}],
        'notes': "poi:drums / set:drums_fade: a click asks the orc outposts' question (aaze0019, 'observation post' made 'war drum'); Yes sets the drum alight; its looping beat stops; the third one burnt sets the quest bit (evt:drums_all)."})
    events.append({
        'id': f'evt:drum_{key}_out', 'preset': 'script', 'trigger': 'timer', 'every': 4,
        'condition': {'map_var': {'name': f'drum_{key}', 'equals': 1}},
        'effects': [{'set': {'var': var(f'drum_{key}'), 'value': 2}},
                    {'set_texture': {'of': platform, 'to': 'xochar'}},
                    {'lights_off': f'light:burn_{key}'}, {'lights_on': f'light:ember_{key}'}],
        'text': "The drum collapses in a heap of ashes, smoke, and smoldering timber.",
        'notes': "A few seconds later the fire has burnt the drum down to a charred frame with a few embers (the outposts' line, aaze0019, 'outpost' made 'drum')."})
events += [
    {'id': 'evt:drums_all', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'map_var': {'name': 'drums_burnt', 'at_least': 3}},
     'effects': [{'qbit': 'war_drums_burned'}, {'add': {'var': 'Experience', 'value': 750}},
                 {'message': "The last drum burns, and the caves fall silent but for dripping water. Without their drums the warband's raiders will not ride out again. Oslo will want to hear of it."}],
     'notes': "goal:war_drums: all three drums burnt (war_drums_burned); a larger sum for the last."},
    {'id': 'evt:drum_master_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:drum_master'}},
     'effects': [{'set': {'var': var('dm_dead'), 'value': 1}}, {'lua': 'SOUND_OFF_great'}],
     'text': "The Drum-Master falls and the great drum's beat breaks off. The drum itself still stands on the scaffold: burn it.",
     'notes': "set:drum_master: his death stops the great drum's beat; burning the drum is still needed for the quest."},
    {'id': 'evt:hall_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:drum_hall_entry', 'once': True,
     'text': "Across the hall, on a timber scaffold, the Drum-Master pounds the great war drum. Its gangway climbs from the west shelf.",
     'seconds': 6},
    {'id': 'evt:den_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:shaman_steps', 'once': True,
     'text': "Behind a curtain of hides a smaller drum rattles: the shaman's spirit drum."},
    {'id': 'evt:hollows_voice', 'preset': 'text', 'trigger': 'step', 'source': 'room:sleeping_hollows', 'once': True,
     'text': "Crude furnishings and filthy bedding tell you that orcs have been living in this cave. From a pit by the south wall a thin voice calls: \"Help! Please, get me out of here!\"", 'seconds': 8,
     'notes': "The first sentence is the orc cave's own line (aaze0022)."},
    {'id': 'evt:cage_gate', 'preset': 'switch', 'source': 'door:cage_gate', 'title': 'Cage gate',
     'condition': {'not': {'map_var': 'ladder_down'}}, 'opens': ['door:cage_gate'], 'sets': {'map_var': 'ladder_down'},
     'text': "You cut the lashings and heave the pole gate up. A rope ladder hangs down into the pit.",
     'else_effects': [{'text': "The cage gate is up; the rope ladder hangs down into the pit."}],
     'notes': "set:captive: one click lifts the gate over the pit's rim; the ladder hangs ready (link:hollows_prisoner_pit)."},
    {'id': 'evt:tam', 'preset': 'script', 'trigger': 'step', 'source': 'room:prisoner_pit', 'once': True,
     'effects': [{'message': "A skinny farm boy scrambles to his feet. \"You came! I'm Tam, Oslo's son. They were going to sell me back to Pa for every cow he's got. I can climb out myself now - I'll run straight home and tell him!\" He swarms up the rope ladder and is gone."},
                 {'qbit': 'captive_freed'}, {'hide_actors': 20}, {'add': {'var': 'Experience', 'value': 300}}],
     'notes': "goal:captive: reaching Tam in the pit frees him; he climbs out and runs home (hidden). His father Oslo rewards the party on X1."},
    {'id': 'evt:drag_marks', 'preset': 'text', 'trigger': 'step', 'source': 'plate:drag_1', 'sources': ['plate:drag_2'], 'once': True,
     'text': "Fresh drag marks run across the straw to a big boulder by the west wall.",
     'notes': "The clue to the plunder cache: the marks lead to the boulder."},
    {'id': 'evt:boulder', 'preset': 'door', 'source': 'door:boulder', 'title': 'Boulder', 'action': 'open',
     'text': "You put your shoulders to the boulder: it grinds aside and down into a hollow, and a low cave opens behind it.",
     'notes': "link:hollows_loot_cache: the secret boulder (pulses for a party that spots secrets; clicked open by anyone)."},
    {'id': 'evt:chest_cache', 'preset': 'chest', 'source': 'chest:cache', 'title': 'Chest'},
    {'id': 'evt:chest_shaman', 'preset': 'chest', 'source': 'chest:shaman', 'title': 'Chest'},
    {'id': 'evt:chest_hollows', 'preset': 'chest', 'source': 'chest:hollows', 'title': 'Chest'},
    {'id': 'evt:chest_pool', 'preset': 'chest', 'source': 'chest:pool', 'title': 'Chest'},
    {'id': 'evt:gate_bar', 'preset': 'switch', 'source': 'mover:gate_bar', 'title': 'Gate bar',
     'condition': {'not': {'qbit': 'orc_back_gate_open'}}, 'opens': ['mover:gate_bar'],
     'effects': [{'qbit': 'orc_back_gate_open'}],
     'text': "You heave the heavy bar up out of its brackets. The back gate is free.",
     'else_effects': [{'text': "The bar is up; the back gate is free."}],
     'notes': "set:back_gate / poi:back_gate_bar: the bar lifts from the inside only; then the gate is a two-way door to X7."},
    {'id': 'evt:exit_x7', 'preset': 'script', 'source': 'panel:back_gate', 'title': 'Back gate',
     'condition': {'qbit': 'orc_back_gate_open'},
     'effects': [{'message': "The gate opens a hand's breadth and stops: a fresh rockfall has buried the path down Mount Firestone's slopes. There is no way out here for now."}],
     'else_effects': [{'message': "The gate is barred from inside: a heavy timber bar lies across it in two iron brackets. Lift the bar first."}],
     'notes': "Sealed exit (2026-11-20): X7 is not built; when it is, make panel:back_gate an exit again to X7's south slopes (NOTES 'Sealed exits')."},
]
wiring = {'format': 0, 'variables': ['drums_burnt', 'drum_signal', 'drum_spirit', 'drum_great', 'dm_dead', 'ladder_down'],
          'events': events}

# the signal drum stands on the east firing step: add it there
for r in rooms:
    if r['id'] == 'room:firing_step_e':
        r['platforms'] = [{'id': 'platform:drum_signal', 'outline': octagon(1120, 2128, 96), 'rise': 128,
                           'surface': DRUMSIDE, 'top_surface': DRUMTOP,
                           'notes': "The signal drum at the step's east end (the first drum)."}]

project = {
    'format': 0, 'id': 'xeen_xd05', 'name': 'Orc Caves', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-05', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [12, 27], 'climbs': 'n'},
    'map_stats': {'id': 9135, 'encounter_chance': 10, 'treasure_level': 1, 'trap_dice': 1, 'perception_difficulty': 1,
                  'refill_days': 672, 'music': 18, 'environment': 'cave', 'lock_difficulty': 1,
                  'slots': [{'monster': 'Xeen Orc', 'tier': 2, 'per_marker': [2, 3], 'weight': 60},
                            {'monster': 'Xeen Bat', 'tier': 1, 'per_marker': [2, 3], 'weight': 25},
                            {'monster': 'Xeen Snake', 'tier': 1, 'per_marker': [1, 2], 'weight': 15}]},
    'neighbours': [
        {'id': 'exit:x1_hills', 'to': 'xeen_x1.odm', 'kind': 'door', 'arrival': [9216, 16643, 1376],
         'arrival_hint': "In the north hills of X1, in front of the orc caves' mouth (X1 thing:orc_cave_mouth, face at y 17043), facing away from it, downhill.", 'direction': 270,
         'notes': "X1 (Vertigo Meadows): arrival 400 south of the cave mouth's face (ground 1376)."},
    ],
    'migrated': ['platform_in_sunken_level'],
    'qbits': {'captive_freed': 110052, 'orc_back_gate_open': 110051, 'war_drums_burned': 110050},
    'notes': "Xeen design brief, level L4: L3's orc caves built with the studio's words of 2026-11-13, a playable map (NOTES.md). Optional Act I dungeon ('Burn the war-drums', x1-tam.yml's hooks). World of Xeen since 2026-11-20 (lane A7): slot 1 Xeen Orc (Orc 5, Orc Archer 7, Orc Guard 10: the spawn points fix the tier), slot 2 Xeen Bat at tier b (Cave Bat 6), slot 3 Xeen Snake (Giant Snake 5); the Drum-Master is his boss row 11033 (12), the shaman and the two gate guards Orc Guards 11032 (10), Tam an MM7 peasant (358). Quest bits 110050-110052 (A3's x1-tam.yml). The map card (map_stats 9135, music, treasure) is A2's row from source/map_rows.yml: the block below is the studio's copy for its checks. exit:x1_hills leads to X1 (xeen_x1.odm); the back gate is sealed by a rockfall until X7 exists (it opened on Emerald Island as a stand-in before).",
}

L4.mkdir(parents=True, exist_ok=True)
lock = yaml.safe_load((L4 / 'ids.lock.yml').read_text()) if (L4 / 'ids.lock.yml').exists() else {}
snd = lock.get('sounds', {})
for e in events:
    for eff in e.get('effects', []):
        if 'lua' in eff and eff['lua'].startswith('SOUND_OFF_'):
            key = eff['lua'][len('SOUND_OFF_'):]
            n = snd.get(f'sound:drum_{key}')
            eff['lua'] = f"evt.SetMapVar('AmbientSound{n}', 2)" if n else "-- sound number not yet in the lock"
for name, doc in [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring), ('project.yml', project)]:
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    (L4 / name).write_text(text)
print('written')
