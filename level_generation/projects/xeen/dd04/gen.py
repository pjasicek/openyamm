"""DD-04 The Gremlin Court: writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd04/L*) from one place.

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd04), phase 3, decider D-26.
Plan frame: x east, y north, the tiny door's sill at y 0; heights from the arrival floor (0). The upper floor (the
court side, the wall cellar and the larder) at 0; the burrows below (barracks, sappers' tunnel) at -384. No room of
one floor lies over a room of the other.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import sys
import yaml

R = _REPO_ROOT
OUT = R + '/devdocs/xeen/briefs/dd04'


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.add_representer(Flow, flow_rep)


def F(*a):
    return Flow(a)


def S(texture, w, h, scale=None, **kw):
    d = {'texture': texture, 'size': F(w, h)}
    if scale:
        d['scale'] = scale
    d.update(kw)
    return d


def dump(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)


# ---------------------------------------------------------------------------------------------------------------------
# Numbers

MAP_ID = 9153
QBITS = {
    'arrived_once': 117040,
    'court_won': 113021,
    'court_hostile': 113024,
    'guards_beaten': 113025,
    'court_peace': 113026,
    'gettlewaithe_slain': 113027,
    'throne_searched': 113028,
}
ENERGY_DISK = 12334
GETTLEWAITHE_NPC = 4955

# D1's burrow (thing:dd04_burrow, event 170 on the installed xeen_d1.odm): its face at (2304, 10467, 1086-1366),
# the place a player uses it from (2304, 10723, 1152), facing south into the wall. Leaving DD-04 the party stands
# just outside it, facing north, away from it (measured with playtest_exit.yml).
D1_ARRIVAL = [2048, 11264, 1152]  # A6's return point for D1 event 170 (2026-11-20, facing 1536)

# ---------------------------------------------------------------------------------------------------------------------
# Textures (D-26): the court side's built rooms in D1's own t09 grey ashlar (MM8's Darkside town kit) with shipped
# floors and ceilings; the burrows in MM7 Tularean Caves 7d08 earth (cwb1 walls and roofs, cfb1 floors).

CAVE_WALL = S('cwb1', 128, 256)
CAVE_FLOOR = S('cfb1', 128, 128)
ASHLAR = S('t09a01', 128, 256)
ASHLAR_TRIM = S('t09b11b', 128, 32)
FLAGS = S('t09a02b', 128, 128)
PLASTER = S('t09a02a', 128, 128)
# The court's roof: MM8's beamed plank ceiling gkp1ceil (a tile), not the carved panel t09a10a (a picture meant once,
# shown 12-28 times on each roof face; session 7, merge point 16). Its own size, enlarged by scale (merge point 17).
BEAMS = S('gkp1ceil', 128, 128, 2)
PLANK = S('t09b10a', 32, 128)
PLANK_LEAF = S('t09b10a', 32, 128, uneven=True)
RUG = S('carpt01', 512, 256, 1.5)
PARQUET = S('t09a05b', 128, 128)
DOOR = S('t09a03c', 128, 256, 1.5)
ROOTS = S('7t1butts', 32, 32, 4)

THEMES = [
    {'id': 'theme:burrow', 'wall': CAVE_WALL, 'floor': CAVE_FLOOR, 'ceiling': CAVE_WALL,
     'door': PLANK,
     'notes': "The burrows: MM7 Tularean Caves (7d08) red-brown earth cwb1 on walls and roofs, its floor cfb1."},
    {'id': 'theme:ashlar', 'wall': ASHLAR, 'bands': [{'height': 32, 'surface': ASHLAR_TRIM}], 'floor': FLAGS,
     'ceiling': PLASTER, 'reveal': ASHLAR, 'door': DOOR,
     'notes': "The wall's footings: D1's t09 grey ashlar (t09a01 over its base course t09b11b), the town's flags "
              "t09a02b underfoot, the smooth grey t09a02a overhead, the arched plank door t09a03c."},
    {'id': 'theme:court', 'wall': ASHLAR, 'bands': [{'height': 32, 'surface': ASHLAR_TRIM}], 'floor': FLAGS,
     'ceiling': BEAMS, 'reveal': ASHLAR, 'door': DOOR,
     'notes': "The court: D1's t09 ashlar under a beamed plank roof (gkp1ceil), the town's flags underfoot."},
    {'id': 'theme:waiting', 'wall': ASHLAR, 'bands': [{'height': 32, 'surface': ASHLAR_TRIM}], 'floor': PARQUET,
     'ceiling': PLASTER, 'reveal': ASHLAR, 'door': DOOR,
     'notes': "The waiting room: t09 ashlar over a herringbone plank floor (t09a05b, stolen from a town house)."},
    {'id': 'theme:mud', 'wall': CAVE_WALL, 'floor': S('wtrtyl', 128, 128, liquid='water', flow='down'),
     'ceiling': CAVE_WALL,
     'notes': "The sappers' last dig: 7d08 earth round a pool of seeping water (MM8 wtrtyl, the fluid bit)."},
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms


def rect(x0, y0, x1, y1):
    return [F(x0, y0), F(x1, y0), F(x1, y1), F(x0, y1)]


ROOMS = [
    {'id': 'room:door', 'name': 'The tiny door', 'outline': rect(-160, 0, 160, 640), 'floor': 0, 'ceiling': 240,
     'theme': 'theme:burrow', 'ambient': 14,
     'notes': "Just inside the tiny door: a low earthen passage 320 wide and 240 high (the party stoops, by the look "
              "of it; 240 clears its 192), opening into the burrow after 640."},
    {'id': 'room:burrow', 'name': 'The burrow',
     'outline': [F(-192, 640), F(192, 640), F(192, 1088), F(448, 1344), F(448, 2048), F(192, 2304), F(-192, 2304),
                 F(-192, 1984), F(64, 1728), F(64, 1472), F(-192, 1216)],
     'floor': 0, 'rough': {'step': 192, 'depth': 32}, 'ceiling': 416,
     'ceiling_points': [F(256, 1700, 480), F(0, 1000, 448)],
     'theme': 'theme:burrow', 'ambient': 16,
     'notes': "A crooked passage dug through the wall's rubble core, 384 to 640 wide, lit by stolen lanterns; the "
              "bolt-hole drops away east, the hall of pranks opens north."},
    {'id': 'room:plunder', 'name': 'Hall of pranks', 'outline': rect(-640, 2304, 640, 3328), 'floor': 0,
     'rough': {'step': 192, 'depth': 32}, 'ceiling': 544, 'ceiling_points': [F(0, 2816, 640)],
     'theme': 'theme:burrow', 'ambient': 18,
     'platforms': [
         {'id': 'platform:gears', 'outline': [F(-424, 3104), F(-336, 3104), F(-272, 3168), F(-272, 3256),
                                              F(-336, 3304), F(-424, 3304), F(-488, 3256), F(-488, 3168)],
          'rise': 40, 'surface': PLANK, 'top_surface': PLANK,
          'notes': "The mill's great gear wheel, laid flat by the north wall with the smaller gears on it."},
         {'id': 'platform:wheel', 'outline': [F(-536, 2392), F(-472, 2392), F(-432, 2432), F(-432, 2496),
                                              F(-472, 2536), F(-536, 2536), F(-576, 2496), F(-576, 2432)],
          'rise': 24, 'surface': PLANK, 'top_surface': PLANK,
          'notes': "A wheel off Cole's cart, in the south-west corner."},
     ],
     'notes': "A dug hall about 1,280 by 1,024 heaped with Castleview's missing things: the mill's gears, bell "
              "clappers, a bucket of Ingrid's chain rings, a wheel off Cole's cart; the waiting room's door north, "
              "the wall's old cellar through an arch east."},
    {'id': 'room:waiting', 'name': 'The waiting room', 'outline': rect(-384, 3456, 384, 4096), 'floor': 0,
     'ceiling': 416, 'theme': 'theme:waiting', 'ambient': 22,
     'walls': [{'wall': 'west', 'panels': [{'id': 'panel:sign', 'at': 'centre', 'length': 192, 'bottom': 176,
                                            'height': 96, 'surface': S('t09b11a', 128, 64, 1.5),
                                            'notes': "The sign: 'Wait here. Forever.'"}]}],
     'platforms': [
         {'id': 'platform:bench_w', 'at': F(-336, 3712), 'size': F(64, 320), 'rise': 40, 'surface': PLANK,
          'top_surface': PLANK, 'notes': "A petitioners' bench along the west wall, much too small."},
         {'id': 'platform:bench_e', 'at': F(336, 3776), 'size': F(64, 384), 'rise': 40, 'surface': PLANK,
          'top_surface': PLANK, 'notes': "A petitioners' bench along the east wall, much too small."},
     ],
     'notes': "A square room in the wall's footings, 768 by 640: two benches built for gremlins, a sign, heralds; "
              "the plank door south to the hall of pranks, the court's door north."},
    {'id': 'room:court', 'name': 'The Gremlin Court', 'outline': rect(-896, 4224, 896, 5760), 'floor': 0,
     'ceiling': 704, 'ceiling_points': [F(0, 4992, 832)], 'theme': 'theme:court', 'ambient': 24,
     'walls': [{'wall': 'north', 'panels': [{'id': 'panel:portrait', 'at': 'centre', 'length': 256, 'bottom': 320,
                                             'height': 256, 'surface': S('xdmayor', 128, 128, 2),
                                             'notes': "Mayor Snarfblad's portrait with a moustache added (A6's "
                                                      "xdmayor), hung behind the throne."}]}],
     'platforms': [
         {'id': 'platform:rug', 'at': F(0, 5184), 'size': F(768, 384), 'rise': 2, 'surface': RUG,
          'top_surface': RUG, 'notes': "A rug from some Castleview parlour, before the dais."},
         {'id': 'platform:dais', 'at': F(0, 5560), 'size': F(768, 352), 'rise': 32, 'surface': PLANK,
          'top_surface': PLANK, 'notes': "The dais, planks from the bridge."},
         {'id': 'platform:throne', 'at': F(0, 5640), 'size': F(192, 128), 'rise': 72, 'base': 32,
          'surface': PLANK, 'top_surface': PLANK, 'notes': "The throne: a seat of chairs stacked three high."},
         {'id': 'platform:throne_back', 'at': F(0, 5716), 'size': F(192, 24), 'rise': 216, 'base': 32,
          'surface': PLANK, 'top_surface': PLANK, 'notes': "The throne's back, a fourth chair on end."},
         {'id': 'platform:chair_1', 'at': F(-208, 5672), 'size': F(64, 64), 'rise': 56, 'base': 32,
          'surface': PLANK, 'top_surface': PLANK, 'notes': "A spare chair of the throne's pile."},
         {'id': 'platform:chair_2', 'at': F(-208, 5672), 'size': F(56, 56), 'rise': 56, 'base': 88,
          'surface': PLANK, 'top_surface': PLANK, 'notes': "A chair on the chair."},
     ],
     'notes': "The hall of the court in the wall's footings, 1,792 by 1,536 under a beamed roof: a carpet of the "
              "rug from a town parlour to a dais, Gettlewaithe's throne of stacked chairs, the Mayor's improved portrait above "
              "it; the waiting room's door south, the servants' hatch in the east wall by the dais."},
    {'id': 'room:cellar', 'name': "The wall's old cellar",
     'outline': [F(896, 2304), F(1920, 2304), F(1920, 3584), F(1664, 3584), F(1664, 4608), F(1152, 4608),
                 F(1152, 3584), F(896, 3584)],
     'floor': 0, 'ceiling': 448, 'ceiling_points': [F(1408, 2944, 544), F(1408, 4096, 512)],
     'theme': 'theme:ashlar', 'ambient': 18,
     'notes': "A store in the wall's footings forgotten by the town and found by the gremlins: a hall 1,024 by "
              "1,280 and a vaulted arm north to the larder's door; the hall of pranks through an arch west."},
    {'id': 'room:larder', 'name': 'The larder', 'outline': rect(1024, 4864, 1664, 5632), 'floor': 0,
     'ceiling': 384, 'theme': 'theme:ashlar', 'ambient': 20,
     'platforms': [
         {'id': 'platform:table', 'at': F(1560, 5056), 'size': F(128, 256), 'rise': 64, 'surface': PLANK,
          'top_surface': PLANK, 'notes': "The larder table: Pip's melons, a ham, the Mayor's cheese."},
     ],
     'notes': "A cool room 640 by 768: the gremlins' larder. The cellar's door south, the trapdoor stair down to "
              "the sappers' tunnel east, the servants' hatch into the court west."},
    {'id': 'room:bolt_hole', 'name': 'Bolt-hole', 'path': [F(576, 1664), F(1408, 1664)], 'width': 320, 'floor': 0,
     'slope': {'to': -384}, 'ceiling': 288, 'theme': 'theme:burrow', 'ambient': 12,
     'notes': "A steep earthen ramp 832 long, dropping 384 east from the burrow to the army's barracks."},
    {'id': 'room:barracks', 'name': 'The mighty army',
     'outline': [F(1792, 896), F(2816, 896), F(3072, 1152), F(3072, 1920), F(2816, 2176), F(1792, 2176),
                 F(1536, 1920), F(1536, 1152)],
     'floor': -384, 'rough': {'step': 192, 'depth': 32}, 'ceiling': 96, 'ceiling_points': [F(2304, 1536, 192)],
     'theme': 'theme:burrow', 'ambient': 15,
     'notes': "Gettlewaithe's 'mighty army' in a cave 1,536 by 1,280 under the burrow: straw for beds, toy "
              "catapults, the pay chest; the bolt-hole comes down west, the sappers' tunnel leaves north."},
    {'id': 'room:sap', 'name': "Sappers' tunnel",
     'path': [F(2560, 2304), F(2560, 3072), F(2848, 3520), F(2848, 4416), F(2720, 4864), F(2720, 6144)],
     'width': 320, 'smooth': 1, 'floor': -384, 'ceiling': -32, 'theme': 'theme:burrow', 'ambient': 10,
     'notes': "A tunnel shored with stakes, dug north under the town towards the sewers and given up where it met "
              "water; the trapdoor stair to the larder leaves its west side."},
    {'id': 'room:sap_stair', 'name': 'Trapdoor stair', 'outline': rect(1792, 5184, 2432, 5504), 'floor': -384,
     'slope': {'to': 0, 'toward': 'west', 'steps': 12}, 'ceiling': 352, 'theme': 'theme:burrow', 'ambient': 12,
     'notes': "Twelve earthen steps up west from the sappers' tunnel to the larder's trapdoor."},
    {'id': 'room:mud', 'name': "The sappers' last dig",
     'outline': [F(2496, 6272), F(2944, 6272), F(3072, 6528), F(2880, 6784), F(2560, 6784), F(2368, 6528)],
     'floor': -400, 'ceiling': -48, 'theme': 'theme:mud', 'ambient': 9,
     'notes': "Where the sappers gave up: the tunnel's end, its floor a pool of seeping water; the drains beyond."},
]

OPENINGS = [
    {'id': 'open:door_burrow', 'from': 'room:door', 'to': 'room:burrow', 'link': 'link:door_burrow',
     'width': 'full', 'height': 240},
    {'id': 'open:burrow_plunder', 'from': 'room:burrow', 'to': 'room:plunder', 'link': 'link:burrow_plunder',
     'width': 'full', 'height': 384},
    {'id': 'open:burrow_bolt', 'from': 'room:burrow', 'to': 'room:bolt_hole', 'link': 'link:burrow_bolt',
     'width': 'full', 'height': 288, 'notes': "The bolt-hole's mouth in the burrow's east wall."},
    {'id': 'open:plunder_waiting', 'from': 'room:plunder', 'to': 'room:waiting', 'link': 'link:plunder_waiting',
     'width': 192, 'height': 352, 'notes': "The waiting room's plank door."},
    {'id': 'open:waiting_court', 'from': 'room:waiting', 'to': 'room:court', 'link': 'link:waiting_court',
     'width': 192, 'height': 352, 'notes': "The court's door."},
    {'id': 'open:plunder_cellar', 'from': 'room:plunder', 'to': 'room:cellar', 'link': 'link:plunder_cellar',
     'width': 512, 'height': 384, 'notes': "A broken arch from the dug hall into the wall's old cellar."},
    {'id': 'open:cellar_larder', 'from': 'room:cellar', 'to': 'room:larder', 'link': 'link:cellar_larder',
     'width': 192, 'height': 352, 'notes': "The larder's door."},
    {'id': 'open:larder_court', 'from': 'room:larder', 'to': 'room:court', 'link': 'link:larder_court',
     'width': 160, 'height': 224, 'notes': "The servants' hatch, a low secret door."},
    {'id': 'open:bolt_barracks', 'from': 'room:bolt_hole', 'to': 'room:barracks', 'link': 'link:bolt_barracks',
     'width': 'full', 'height': 288},
    {'id': 'open:barracks_sap', 'from': 'room:barracks', 'to': 'room:sap', 'link': 'link:barracks_sap',
     'width': 'full', 'height': 320},
    {'id': 'open:sap_stair', 'from': 'room:sap', 'to': 'room:sap_stair', 'link': 'link:sap_larder',
     'width': 288, 'height': 320},
    {'id': 'open:stair_larder', 'from': 'room:sap_stair', 'to': 'room:larder', 'link': 'link:sap_larder',
     'width': 224, 'height': 288, 'notes': "The trapdoor (a plank door) at the stair's head."},
    {'id': 'open:sap_mud', 'from': 'room:sap', 'to': 'room:mud', 'link': 'link:sap_mud', 'width': 'full',
     'height': 320},
]

# ---------------------------------------------------------------------------------------------------------------------
# Monsters (A2's rows, D-26, D-37): court side 11024 Gremlin 14, 11025 Gremlin Saboteur 18 and 11026 Gremlin Guard 22
# in xeen_gremlins_court (friendly at load, hostile on court_hostile, friendly on court_peace); Gettlewaithe 11023
# (24) in his own xeen_gremlins_king (D-37: friendly at load and after court_peace, no rule on court_hostile: he turns
# only when struck himself, and the timer then rouses the court); cellar, larder and army 11027 Gremlin 14 in
# xeen_gremlins_army (hostile until court_peace). The world's relations.yml says it all: no map relations, no
# `hostile` here. Ids sort court first (c..), army after (x..): the build writes placed monsters in id order, so the
# court's actor indices are 0-16 (evt:court_roused).

COURT_GROUPS = {'burrow': 3, 'plunder': 4, 'waiting': 5}
MONSTERS = [
    {'id': 'monster:c00_gettlewaithe', 'room': 'room:court', 'monster': 11023, 'at': F(0, 5480),
     'floor_height': 32, 'facing': 270, 'group': 2, 'immobile': True,
     'notes': "Gettlewaithe, Imperator Primus of the Gremlins (A2's boss row 11023, level 24), on the dais before "
              "his throne; NPC 4955 talks through the throne (evt:throne)."},
    {'id': 'monster:c01_guard', 'room': 'room:court', 'monster': 11026, 'at': F(-320, 5280), 'facing': 270,
     'group': 1, 'notes': 'A court guard (Gremlin Guard 22).'},
    {'id': 'monster:c02_guard', 'room': 'room:court', 'monster': 11026, 'at': F(320, 5280), 'facing': 270,
     'group': 1},
    {'id': 'monster:c03_guard', 'room': 'room:court', 'monster': 11026, 'at': F(0, 5120), 'facing': 270,
     'group': 1},
]
_court = [('burrow', 11024, [(0, 960), (288, 1600), (288, 1900), (0, 2150)]),
          ('plunder', 11024, [(-384, 2560), (384, 2560), (-160, 2900), (320, 3100)]),
          ('plunder', 11025, [(0, 3000), (128, 2700)]),
          ('waiting', 11024, [(-200, 3700), (200, 3900), (0, 3600)])]
n = 4
for room, row, points in _court:
    for (x, y) in points:
        MONSTERS.append({'id': 'monster:c%02d_%s' % (n, room), 'room': 'room:' + room, 'monster': row,
                         'at': F(x, y), 'facing': 270 if room != 'burrow' else 90, 'group': COURT_GROUPS[room]})
        n += 1
_army = [('cellar', 10, [(1408, 2560), (1664, 2816), (1216, 3200), (1408, 4096)]),
         ('larder', 11, [(1216, 5248), (1408, 5440)]),
         ('barracks', 12, [(1920, 1280), (2304, 1408), (2688, 1280), (2176, 1856), (2560, 1856)])]
n = 1
for room, group, points in _army:
    for (x, y) in points:
        MONSTERS.append({'id': 'monster:x%02d_%s' % (n, room), 'room': 'room:' + room, 'monster': 11027,
                         'at': F(x, y), 'facing': 90, 'group': group})
        n += 1
COURT_ACTORS = [m for m in MONSTERS if m['id'].startswith('monster:c')]
ARMY_ACTORS = [m for m in MONSTERS if m['id'].startswith('monster:x')]
assert len(MONSTERS) == 28, len(MONSTERS)

# ---------------------------------------------------------------------------------------------------------------------
# Objects

LANTERN = 'dec07'


def deco(i, room, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + room, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


DECORATIONS = [
    deco('burrow_sconce_1', 'burrow', 'scon100', (192, 864), wall=1, notes="A stolen lantern on a peg."),
    deco('burrow_sconce_2', 'burrow', 'scon100', (-192, 928), wall=10),
    deco('plunder_sconce_w', 'plunder', 'scon200', (-640, 2560), wall='west'),
    deco('plunder_sconce_n', 'plunder', 'scon200', (384, 3328), wall='north'),
    deco('plunder_bucket_1', 'plunder', 'Bucket', (-584, 2752), notes="Ingrid's chain rings, by the bucket."),
    deco('plunder_bucket_2', 'plunder', 'Bucket', (-584, 2832)),
    deco('plunder_dirt', 'plunder', '7dec11', (560, 2400), notes="Spoil from the digging."),
    deco('waiting_sconce_e', 'waiting', 'scon100', (384, 3600), wall='east'),
    deco('court_chandelier', 'court', 'chndlir0', (0, 4800), hangs=True,
         notes="A chandelier from the town hall, hung from the court's roof."),
    deco('court_sconce_w', 'court', 'scon100', (-896, 4800), wall='west'),
    deco('court_sconce_e', 'court', 'scon100', (896, 4700), wall='east'),
    deco('court_goblet', 'court', '7dec46', (-208, 5672), floor_height=144, notes="A goblet on the spare chair."),
    deco('cellar_barrel_1', 'cellar', 'bigbarel', (1840, 2392)),
    deco('cellar_barrel_2', 'cellar', 'bigbarel', (1840, 2504)),
    deco('cellar_cask_1', 'cellar', '7dec21', (1600, 3712)),
    deco('cellar_cask_2', 'cellar', '7dec21', (1600, 3808)),
    deco('cellar_sack_1', 'cellar', 'floursac', (1848, 3488)),
    deco('cellar_sack_2', 'cellar', 'floursac', (1752, 3512)),
    deco('cellar_sconce', 'cellar', 'scon100', (1920, 2944), wall='east'),
    deco('larder_bowl', 'larder', '7dec08', (1560, 5000), floor_height=64, notes="Pip's melons."),
    deco('larder_plate', 'larder', 'dec36', (1560, 5112), floor_height=64, notes="The ham."),
    deco('larder_barrel_1', 'larder', 'smlbarel', (1096, 5560)),
    deco('larder_barrel_2', 'larder', 'smlbarel', (1192, 5576)),
    deco('barracks_fire', 'barracks', '7dec02', (2304, 1152), notes="The army's cooking fire."),
    deco('barracks_straw_1', 'barracks', '7dec01', (1664, 1280), notes="Straw bedding."),
    deco('barracks_straw_2', 'barracks', '7dec01', (2944, 1344)),
    deco('barracks_bones', 'barracks', 'dec29', (2880, 1856)),
    deco('sap_dirt_1', 'sap', '7dec11', (2848, 5568)),
    ]

# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s28 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-04: "the town's stolen things (the
# dungeon's joke) barely visible"): the court heaped in both south corners with Castleview's missing things (stacked
# crates, cart wheels, barrels, kegs, sacks; baskets and crockery have no model in Xeen's dungeons) and a third heap
# of crates in the hall of pranks' north-east corner; the tiny door
# and the low burrows stay as built (240 and 416 high, the party's 192 clears them).
import math as _m
CRATE = S('crate_w64', 64, 64, fit=True)       # a crate's face once per side


def _crate(at, size, rise, base=0, facing=0):
    d = {'at': F(*at), 'size': F(size, size), 'rise': rise, 'surface': dict(CRATE), 'top_surface': dict(CRATE),
         'notes': "A crate from Castleview's docks."}
    if base:
        d['base'] = base
    if facing:
        d['facing'] = facing
    return d


def _wheel(cx, cy, base=0, r=72):
    d = {'outline': [F(round(cx + r * _m.cos(_m.radians(22.5 + 45 * k))), round(cy + r * _m.sin(_m.radians(22.5 + 45 * k))))
                     for k in range(8)], 'rise': 16, 'surface': dict(PLANK), 'top_surface': dict(PLANK),
         'notes': "A cart wheel off some Castleview cart."}
    if base:
        d['base'] = base
    return d


def _heap(sx):
    """A heap of stolen things in a south corner of the court (sx -1 west, 1 east)."""
    x = lambda v: sx * v
    return [_crate((x(800), 4352), 128, 128), _crate((x(800), 4352), 96, 96, base=128, facing=15),
            _crate((x(672), 4336), 96, 96), _crate((x(800), 4496), 112, 112, facing=-10),
            _wheel(x(600), 4480), _wheel(x(608), 4488, base=16)]


_RD = {r['id'].split(':')[1]: r for r in ROOMS}
_RD['court']['platforms'] += _heap(-1) + _heap(1)
_RD['court']['notes'] += (" Both south corners heaped with the town's missing things: crates, cart wheels, barrels, "
                          "kegs, sacks.")
_RD['plunder']['platforms'] += [_crate((520, 3184), 112, 112), _crate((520, 3184), 80, 80, base=112, facing=20),
                                _crate((400, 3232), 80, 80)]
for _sx, _side in ((-1, 'w'), (1, 'e')):
    DECORATIONS += [
        deco('court_heap_%s_barrel' % _side, 'court', 'bigbarel', (_sx * 560, 4320), notes="A barrel from the inn."),
        deco('court_heap_%s_keg' % _side, 'court', 'smlbarel', (_sx * 640, 4608)),
        deco('court_heap_%s_sack' % _side, 'court', 'floursac', (_sx * 840, 4656), notes="A sack of the mill's flour."),
        deco('court_heap_%s_bag' % _side, 'court', 'bag01', (_sx * 680, 4776)),
    ]

LIGHTS = [
    {'id': 'light:burrow_1', 'room': 'room:burrow', 'at': F(0, 980), 'height': 300, 'radius': 900,
     'color': F(255, 170, 90)},
    {'id': 'light:burrow_2', 'room': 'room:burrow', 'at': F(256, 1760), 'height': 300, 'radius': 900,
     'color': F(255, 170, 90)},
    {'id': 'light:plunder', 'room': 'room:plunder', 'at': F(0, 2816), 'height': 380, 'radius': 1300,
     'color': F(255, 170, 90)},
    {'id': 'light:waiting', 'room': 'room:waiting', 'at': F(0, 3776), 'height': 300, 'radius': 1000,
     'color': F(255, 200, 140)},
    {'id': 'light:court', 'room': 'room:court', 'at': F(0, 4800), 'height': 500, 'radius': 1600,
     'color': F(255, 200, 140)},
    {'id': 'light:throne', 'room': 'room:court', 'at': F(0, 5400), 'height': 400, 'radius': 1100,
     'color': F(255, 190, 120)},
    {'id': 'light:cellar', 'room': 'room:cellar', 'at': F(1408, 2944), 'height': 320, 'radius': 1200,
     'color': F(255, 170, 90)},
    {'id': 'light:cellar_arm', 'room': 'room:cellar', 'at': F(1408, 4224), 'height': 320, 'radius': 800,
     'color': F(255, 170, 90)},
    {'id': 'light:larder', 'room': 'room:larder', 'at': F(1344, 5248), 'height': 300, 'radius': 900,
     'color': F(255, 180, 110)},
    {'id': 'light:barracks', 'room': 'room:barracks', 'at': F(2304, 1152), 'height': 100, 'radius': 1400,
     'color': F(255, 140, 70), 'pulse': {'intensity': F(0.7, 1), 'frequency': 1, 'phase': 0.3}},
    {'id': 'light:sap', 'room': 'room:sap', 'at': F(2848, 3968), 'height': 200, 'radius': 900,
     'color': F(255, 160, 80)},
    {'id': 'light:mud', 'room': 'room:mud', 'at': F(2720, 6528), 'height': 200, 'radius': 700,
     'color': F(170, 190, 210)},
]

SOUNDS = [
    {'id': 'sound:barracks_fire', 'room': 'room:barracks', 'at': F(2304, 1152), 'sound': '7campfire',
     'radius': 1600, 'inner_radius': 400, 'volume': 0.6, 'notes': "The army's fire."},
    {'id': 'sound:drains', 'room': 'room:mud', 'at': F(2720, 6656), 'sound': 'rushing water loop', 'radius': 2400,
     'inner_radius': 600, 'volume': 0.35, 'notes': "Water running beyond the mud: the town's drains."},
    {'id': 'sound:drip', 'room': 'room:sap', 'at': F(2848, 4000), 'sound': 'drip01', 'radius': 1400,
     'inner_radius': 300, 'volume': 0.5, 'notes': "Water seeping into the tunnel."},
]


def door(i, opening, kind='hinged', **kw):
    d = {'id': 'door:' + i, 'opening': opening, 'kind': kind}
    if kind == 'hinged':
        d.update({'hinge': 'left', 'thickness': 16, 'speed': 80})
    d.update(kw)
    return d


DOORS = [
    door('waiting', 'open:plunder_waiting', surface=DOOR, back_surface=DOOR, edge_surface=PLANK, top_surface=PLANK,
         notes="The waiting room's arched plank door (t09a03c)."),
    door('court', 'open:waiting_court', hinge='right', surface=DOOR, back_surface=DOOR, edge_surface=PLANK,
         top_surface=PLANK, notes="The court's door."),
    door('larder', 'open:cellar_larder', surface=DOOR, back_surface=DOOR, edge_surface=PLANK, top_surface=PLANK,
         notes="The larder's door."),
    door('hatch', 'open:larder_court', kind='slide_up', secret=True, speed=60, thickness=16, surface=ASHLAR,
         back_surface=ASHLAR, notes="The servants' hatch: a low secret door of ashlar between the larder and the "
                                    "court, by the dais; opened from either side."),
    door('trapdoor', 'open:stair_larder', surface=PLANK_LEAF, back_surface=PLANK_LEAF, edge_surface=PLANK, top_surface=PLANK,
         notes="The trapdoor at the head of the sappers' stair: a plank door into the larder."),
]

CHESTS = [
    {'id': 'chest:plunder', 'room': 'room:plunder', 'at': F(-568, 2992), 'kind': 'gt002', 'treasure_level': 2, 'random_items': 2, 'gold': 250, 'notes': "The pranksters' plunder chest."},
    {'id': 'chest:pay', 'room': 'room:barracks', 'at': F(2960, 1536), 'kind': 'gt002', 'treasure_level': 2, 'random_items': 2, 'gold': 400, 'notes': "The mighty army's pay chest."},
    {'id': 'chest:throne', 'room': 'room:court', 'at': F(208, 5648), 'floor_height': 32, 'kind': 'gt002',
     'treasure_level': 3, 'random_items': 2, 'gold': 600,
     'items': ['energy_disk', 'energy_disk', 'energy_disk'],
     'notes': "The royal treasury beside the throne: the map's hoard (one level up) and the 3 Energy Disks of "
              "q-d1.throne's map_gives; it opens only after Gettlewaithe's death, never after a peace."},
]

EXITS = [
    {'id': 'exit:d1', 'room': 'room:door', 'wall': 'south', 'size': F(96, 192), 'surface': S('7solid01', 128, 256, 0.75),
     'to': 'exit:d1_burrow', 'notes': "The tiny door out to D1, a gremlin-sized arched door."},
]

OBJECTS = {
    'format': 0,
    'start': {'room': 'room:door', 'at': F(0, 256), 'facing': 90,
              'notes': "Just inside the tiny door, facing in (north); D1's door:dd04 lands the party here."},
    'doors': DOORS,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'chests': CHESTS,
    'monsters': MONSTERS,
    'decorations': DECORATIONS,
    'exits': EXITS,
    'notes': "DD-04's contents, written by output/studio_cal/dd04/tools/gen.py: 5 doors (one secret), 3 chests, 28 "
             "placed gremlins (17 of the court, peaceful until court_hostile; 11 of the army, hostile until "
             "court_peace), no spawn points.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Wiring

COURT_INDICES = list(range(len(COURT_ACTORS)))   # checked against the built scene by check_indices.py
ROUSED = ("local roused = false\n"
          "for _, i in ipairs({%s}) do\n"
          "    if evt.IsMapActorHostile(i) and not evt.IsMapActorDead(i) then roused = true end\n"
          "end\n"
          "if roused then\n"
          "    SetQBit(QBit(113024))\n"
          "    evt.StatusText(\"The court shrieks for its guards!\", 4)\n"
          "end") % ', '.join(str(i) for i in COURT_INDICES)
THRONE = ("if IsQBitSet(QBit(113027)) then\n"
          "    if IsQBitSet(QBit(113028)) then\n"
          "        XeenQuests.hook(\"q-d1.throne\")\n"
          "    else\n"
          "        evt.StatusText(\"The throne of chairs is empty. The royal treasury stands beside it.\", 4)\n"
          "    end\n"
          "else\n"
          "    evt.SpeakNPC(%d)\n"
          "end") % GETTLEWAITHE_NPC


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


EVENTS = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'not': {'qbit': 'arrived_once'}}, 'once': True,
     'effects': [{'message': "THE GREMLIN COURT. A burrow under Castleview's wall, built for folk half your size. "
                             "Mayor Snarfblad wants the gremlins' pranks stopped, and their king, Gettlewaithe, "
                             "holds court at the far end. His courtiers watch you pass. Nobody has drawn a sword. "
                             "Yet."},
                 {'qbit': 'arrived_once'}],
     'notes': "Why the party is here (Q-D1), on the first arrival only (arrived_once 117040)."},
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load',
     'text': "Under Castleview's wall: mind your heads.",
     'notes': "Every entry: a status line."},
    {'id': 'evt:king_gone', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'gettlewaithe_slain'},
     'effects': [{'hide_actors': 2}],
     'notes': "A slain Gettlewaithe stays dead after a refill: his group is hidden on entry once gettlewaithe_slain "
              "is set."},
    {'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:d1', 'title': 'The tiny door',
     'notes': "Out to D1 in front of the burrow (exit:d1_burrow): the game's own window (D-24)."},
    {'id': 'evt:door_waiting', 'preset': 'door', 'source': 'door:waiting', 'title': 'Door'},
    {'id': 'evt:door_court', 'preset': 'door', 'source': 'door:court', 'title': 'Door'},
    {'id': 'evt:door_larder', 'preset': 'door', 'source': 'door:larder', 'title': 'Door'},
    {'id': 'evt:hatch', 'preset': 'door', 'source': 'door:hatch', 'title': 'Loose stones',
     'notes': "The servants' hatch, secret, opened from either side."},
    {'id': 'evt:trapdoor', 'preset': 'door', 'source': 'door:trapdoor', 'title': 'Trapdoor'},
    {'id': 'evt:chest_plunder', 'preset': 'chest', 'source': 'chest:plunder', 'title': 'Chest'},
    {'id': 'evt:chest_pay', 'preset': 'chest', 'source': 'chest:pay', 'title': 'Chest'},
    {'id': 'evt:chest_throne', 'preset': 'chest', 'source': 'chest:throne', 'title': 'Chest',
     'condition': {'any': [{'qbit': 'throne_searched'}, {'lua': "XeenQuests.can(\"q-d1.throne\")"}]},
     'else_effects': [{'lua': "XeenQuests.hook(\"q-d1.throne\")"}],
     'effects': [{'lua': "if not IsQBitSet(QBit(113028)) then XeenQuests.hook(\"q-d1.throne\") end"}],
     'notes': "q-d1.throne: opens after Gettlewaithe's death (gettlewaithe_slain) and never after a peace; its "
              "fail text otherwise. The first opening runs the hook (throne_searched, its line); the chest holds "
              "the 3 Energy Disks (map_gives) and the hoard."},
    {'id': 'evt:throne', 'preset': 'script', 'source': 'platform:throne', 'title': "Gettlewaithe's throne",
     'lua': THRONE,
     'notes': "Talking to Gettlewaithe (NPC 4955): the studio has no word to give a placed indoor monster its NPC "
              "(Words needed), so the throne he stands before speaks for him. After his death: the hook's "
              "else_text once the treasury is searched."},
    {'id': 'evt:dais', 'preset': 'script', 'source': 'platform:dais', 'title': "Gettlewaithe's throne",
     'lua': THRONE, 'notes': "The dais does what the throne does (a bigger thing to click)."},
    {'id': 'evt:court_roused', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'all': [{'not': {'qbit': 'court_hostile'}}, {'not': {'qbit': 'court_peace'}}]},
     'lua': ROUSED,
     'notes': "Attacking Gettlewaithe or any court-side gremlin sets court_hostile: the engine has no 'attacked' "
              "event (Words needed), so a timer asks each court actor (indices 0-16, the c.. ids) whether it has "
              "turned on the party; A2's relations then turn the whole court (Gettlewaithe, in a faction of his "
              "own, only when struck himself: D-37)."},
    {'id': 'evt:guards_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'group': 1}}, 'lua': "XeenQuests.hook(\"q-d1.guards_beaten\")",
     'notes': "q-d1.guards_beaten when the three court guards (group 1) are dead."},
    {'id': 'evt:king_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:c00_gettlewaithe'}},
     'lua': "XeenQuests.hook(\"q-d1.gettlewaithe\")",
     'text': "Gettlewaithe, Imperator Primus of the Gremlins, topples off his throne of chairs.", 'seconds': 5,
     'notes': "q-d1.gettlewaithe: gettlewaithe_slain and court_won; the treasury opens."},
    text('sign', 'panel:sign', 'Sign', "WAIT HERE. FOREVER.", window=True,
         notes="The graph's sign in the waiting room."),
    text('portrait', 'panel:portrait', "The Mayor's portrait",
         "Mayor Snarfblad in oils, gold chain and all. Someone has given him a magnificent charcoal moustache."),
    text('gears', 'platform:gears', 'Plunder',
         "Castleview's missing things: the mill's gears, two bell clappers, a bucket of chain rings, and the "
         "bridge's rope cut into neat little lengths.", seconds=6),
    text('wheel', 'platform:wheel', 'A cart wheel', "A wheel off Cole's cart. Somebody has painted a face on it."),
    text('table', 'platform:table', 'Larder table',
         "Pip's melons, a ham, and the Mayor's cheese, with small bites out of all three."),
    text('bench', 'platform:bench_e', 'Bench', "Nothing here.",
         notes="Original line (dark/aaze0029:2, 'Nothing here.')."),
    {'id': 'evt:drains', 'preset': 'text', 'trigger': 'step', 'source': 'room:mud',
     'text': "Beyond the mud you hear water running: the town's drains.", 'seconds': 5,
     'notes': "D-26: the sappers' tunnel ends at water; no link to DD-01."},
]

WIRING = {'format': 0, 'events': EVENTS,
          'notes': "DD-04's events (gen.py): Q-D1's hooks (court_guards through the world's relations and "
                   "evt:court_roused, guards_beaten, gettlewaithe, throne), Gettlewaithe's talk by the throne, the "
                   "exit to D1, the doors and chests, flavour."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

# D-89 identity (lane A8 s28): what the party must see
IDENTITY = {'shape': 'hall', 'family': '7d08',
            'seen': ["the tiny door and the crooked burrows dug through the town wall's rubble core",
                     "the hall of pranks and the court heaped with Castleview's missing things: gears, wheels, crates, "
                     "barrels, sacks",
                     "Gettlewaithe's throne of stacked chairs under the Mayor's improved portrait"]}
PROJECT = {
    'format': 0, 'id': 'xeen_dd04', 'name': 'The Gremlin Court', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-04', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(10, 14), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 2, 'trap_dice': 2,
        'perception_difficulty': 2, 'refill_days': 672, 'music': 2, 'environment': 'cave', 'lock_difficulty': 4,
        'slots': [{'monster': 'Xeen Gremlin', 'tier': 0, 'per_marker': F(2, 3), 'weight': 100}],
    },
    'neighbours': [{
        'id': 'exit:d1_burrow', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': F(*D1_ARRIVAL),
        'arrival_hint': "On D1, just outside the gremlins' burrow under the town wall east of the north gate "
                        "(thing:dd04_burrow), at A6's return point.",
        'direction': 270,
        'notes': "D1 installed (A6). The burrow's face stands at (2304, 10467); the party lands at A6's return point "
                 "for D1's event 170, (2048, 11264, 1152) facing 1536 (south). D1's door into this map (A6's door:dd04) lands at this map's start: (0, 256, 0), "
                 "facing north (90)."}],
    'qbits': QBITS,
    'items': {'energy_disk': ENERGY_DISK},
    'notes': "Xeen design brief, DD-04 The Gremlin Court (D1; Q-D1), class S, built from the MU-6 graph "
             "(devdocs/xeen/mockups/act3_graphs/dd04.graph.yml) with decider D-26 (mockups/act3_a8_decisions_a.md). "
             "Party 19-20, band 14-22, Gettlewaithe 24 (A2's boss row 11023), 28 placed monsters on A2's rows "
             "11023-11027 (no spawn points: the slot repeats D1's family for the map card only, encounter chance "
             "0), treasure 2 (the court's treasury one level up), music 2. Quest bits: Q-D1's (113021, "
             "113024-113028) and the map's arrived_once 117040 (provisional block 117040-117079). Item: Energy "
             "Disk 12334 (q-d1.throne's map_gives).",
}

# ---------------------------------------------------------------------------------------------------------------------
# Plan (L1 words; L2 adds extents, floors and heights)


def sp(i, name, kind, size, extent, floor, clear, purpose, theme, pop=None, treasure=None, **kw):
    d = {'id': 'room:' + i, 'name': name, 'kind': kind, 'size': size, 'extent': F(*extent), 'floor': floor,
         'clear_height': clear, 'purpose': purpose, 'theme': theme}
    if pop:
        d['population'] = pop
    if treasure:
        d['treasure'] = treasure
    d.update(kw)
    return d


def placed(actor, count, level, notes=None):
    d = {'actor': actor, 'groups': 1, 'per_marker': F(count, count), 'levels': F(level, level), 'placed': True}
    if notes:
        d['notes'] = notes
    return d


ASHLAR_T = "D1's t09 grey ashlar (t09a01 over t09b11b), the town's flags t09a02b, t09a02a overhead"
CAVE_T = "MM7 Tularean Caves (7d08): red-brown earth cwb1 on walls and roofs, cfb1 underfoot"
SPACES = [
    sp('door', 'The tiny door', 'corridor', 'S', (320, 640), 0, 240,
       "Arrival and the exit to D1: just inside the burrow's tiny door, the party stooping (a 240-high passage, "
       "which clears the party; the stoop is a look).", CAVE_T, empty=True, safe=True),
    sp('burrow', 'The burrow', 'corridor', 'M', (640, 1664), 0, F(416, 480),
       "A crooked passage dug through the wall's rubble core; stolen lanterns; court gremlins come and go.",
       CAVE_T, [placed('Gremlin (court, 11024)', 4, 14, "Peaceful until court_hostile.")]),
    sp('plunder', 'Hall of pranks', 'room', 'M', (1280, 1024), 0, F(544, 640),
       "Castleview's missing things: mill gears, bell clappers, Ingrid's chain rings by the bucket, a wheel off "
       "Cole's cart; the pranksters' chest.", CAVE_T,
       [placed('Gremlin (court, 11024)', 4, 14), placed('Gremlin Saboteur (court, 11025)', 2, 18)],
       [{'kind': 'chest', 'count': 1, 'tier': 2, 'items': F(2, 2), 'notes': "The pranksters' plunder."}]),
    sp('waiting', 'The waiting room', 'room', 'S', (768, 640), 0, 416,
       "Petitioners' benches, much too small; a sign 'Wait here. Forever.'; gremlin heralds.", ASHLAR_T,
       [placed('Gremlin (court, 11024)', 3, 14)]),
    sp('court', 'The Gremlin Court', 'room', 'L', (1792, 1536), 0, F(704, 832),
       "Signature room and goal: Gettlewaithe on his throne of stacked chairs (NPC 4955, boss row 11023), three "
       "court guards, the Mayor's portrait with a moustache, the treasury with 3 Energy Disks (q-d1.throne).",
       ASHLAR_T + "; a beamed plank roof (gkp1ceil); a stolen rug (carpt01) before the dais",
       [placed('Gettlewaithe (11023)', 1, 24, "Boss row; immobile on his dais."),
        placed('Gremlin Guard (court, 11026)', 3, 22, "The court guards (group 1).")],
       [{'kind': 'chest', 'count': 1, 'tier': 3, 'items': F(2, 2),
         'notes': "The royal treasury: the hoard and 3 Energy Disks, after Gettlewaithe's death."}]),
    sp('cellar', "The wall's old cellar", 'room', 'M', (1024, 2304), 0, F(448, 544),
       "A vaulted store in the wall's footings, forgotten by the town and found by the gremlins.", ASHLAR_T,
       [placed('Gremlin (army, 11027)', 4, 14, "Hostile until court_peace.")]),
    sp('larder', 'The larder', 'room', 'S', (640, 768), 0, 384,
       "Pip's melons, a ham, the Mayor's cheese; the trapdoor stair down to the sappers' tunnel; the servants' "
       "hatch into the court.", ASHLAR_T, [placed('Gremlin (army, 11027)', 2, 14)]),
    sp('bolt_hole', 'Bolt-hole', 'corridor', 'S', (832, 320), F(0, -384), 288,
       "A steep earthen ramp down from the burrow to the army.", CAVE_T, empty=True),
    sp('barracks', 'The mighty army', 'room', 'M', (1536, 1280), -384, F(480, 576),
       "Gettlewaithe's 'mighty army': straw beds, a fire, toy catapults, the pay chest.", CAVE_T,
       [placed('Gremlin (army, 11027)', 5, 14)],
       [{'kind': 'chest', 'count': 1, 'tier': 2, 'items': F(2, 2), 'notes': "The army's pay chest."}]),
    sp('sap', "Sappers' tunnel", 'corridor', 'M', (320, 3840), -384, 352,
       "A tunnel under the town towards the sewers, given up where it met water.", CAVE_T, empty=True),
    sp('sap_stair', 'Trapdoor stair', 'corridor', 'S', (640, 320), F(-384, 0), F(352, 736),
       "Twelve earthen steps up to the larder's trapdoor.", CAVE_T, empty=True),
    sp('mud', "The sappers' last dig", 'room', 'S', (704, 512), -400, 352,
       "The tunnel's end in a pool of seeping water: 'Beyond the mud you hear water running: the town's drains.'",
       CAVE_T + "; MM8's water wtrtyl in the pool", empty=True),
]


def link(i, a, b, kind, **kw):
    d = {'id': 'link:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
    d.update(kw)
    return d


LINKS = [
    link('door_burrow', 'door', 'burrow', 'open'),
    link('burrow_plunder', 'burrow', 'plunder', 'open'),
    link('plunder_waiting', 'plunder', 'waiting', 'door', motion='swing'),
    link('waiting_court', 'waiting', 'court', 'door', motion='swing'),
    link('plunder_cellar', 'plunder', 'cellar', 'open', notes="A broken arch into the wall's old cellar."),
    link('cellar_larder', 'cellar', 'larder', 'door', motion='swing'),
    link('larder_court', 'larder', 'court', 'secret_door', notes="The servants' hatch, opened from either side."),
    link('burrow_bolt', 'burrow', 'bolt_hole', 'open'),
    link('bolt_barracks', 'bolt_hole', 'barracks', 'ramp', rise=-384),
    link('barracks_sap', 'barracks', 'sap', 'open'),
    link('sap_larder', 'sap', 'larder', 'stairs', rise=384, notes="Up the trapdoor stair (sap_stair) into the "
                                                                    "larder; a plank trapdoor at its head."),
    link('sap_mud', 'sap', 'mud', 'open'),
]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "Castleview is falling to pieces: the mill's gears gone, the bridge's ropes cut, the bells without "
                 "clappers. The gremlins did it, and their king Gettlewaithe holds court in a burrow under the town "
                 "wall. Behind a tiny door a crooked burrow leads to a hall heaped with the town's missing things, "
                 "a waiting room with benches built for gremlins, and the court itself: a throne of stacked chairs "
                 "on a dais of the bridge's planks, a parlour rug, the Mayor's portrait with a "
                 "moustache added. The court lets the party walk in and talk; the gremlin army in the wall's old "
                 "cellar, the larder and the barracks below does not. Talk Gettlewaithe round in three rounds (and "
                 "beat his guards), or kill him and take the three Energy Disks from his treasury.",
        'purpose': "Q-D1 The Gremlin Court (Mayor Snarfblad, D1): a dialogue first, or a fight. Party 19-20; band "
                   "14-22, Gettlewaithe 24; 28 monsters; treasure 2, the treasury 3. About 15 minutes.",
        'mood': "A comic court: low earthen burrows, then the town's own grey stone, firelight, stolen finery.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'loops': [
            {'id': 'loop:court', 'spaces': ['room:plunder', 'room:waiting', 'room:court', 'room:larder',
                                            'room:cellar'],
             'notes': "Round the court through the cellar and the servants' hatch."},
            {'id': 'loop:army', 'spaces': ['room:burrow', 'room:bolt_hole', 'room:barracks', 'room:sap',
                                           'room:sap_stair', 'room:larder', 'room:cellar', 'room:plunder'],
             'notes': "Down through the army, up the trapdoor stair into the larder."}],
        'entrances': [{'id': 'entrance:tiny_door', 'space': 'room:door', 'kind': 'both',
                       'neighbour': 'exit:d1_burrow', 'facing': 'n',
                       'how': "Just inside the tiny door, facing in."}],
        'critical_path': ['room:door', 'room:burrow', 'room:plunder', 'room:waiting', 'room:court'],
        'return_path': ['room:court', 'room:waiting', 'room:plunder', 'room:burrow', 'room:door'],
        'goals': [
            {'id': 'goal:court', 'space': 'room:court', 'kind': 'set',
             'what': "Win the court: three rounds of talk with Gettlewaithe and his guards beaten (court_peace), or "
                     "his death (gettlewaithe_slain); either sets court_won.", 'handed_in_at': 'D1'}],
        'atmosphere': "Burrows dim and warm (ambient about 12-16), the court side lit by stolen chandeliers (about "
                      "22-24). Music 2. Sounds: the army's fire, water seeping in the sappers' tunnel, the drains "
                      "beyond the mud.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': 3, 'doors': 5, 'fixed_actors': 28, 'loops': 2, 'monsters_about': 28, 'rooms': 12,
                   'sectors': 12, 'spawn_points': 0, 'floor_area_millions': 12},
        'notes': "Class S (MAPS, Dungeons): at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 "
                 "doors. The graph's ten review rooms as twelve rooms (the trapdoor stair and the tunnel's end of "
                 "their own). D-26: the court side peaceful until court_hostile, the army hostile; the challenge "
                 "is Gettlewaithe's first greeting; one new picture (xdmayor, A6's, installed).",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    else:
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512} if level in ('L3', 'L4') else None
        if d['sketch'] is None:
            d.pop('sketch')
    return d


DIAGRAM = """                    [THE GREMLIN COURT: Gettlewaithe on his throne of chairs, 3 guards, TREASURY $$]
                         |   (portrait of the Mayor, moustache added)            ## servants' hatch (secret)
                       =door=                                                 [Larder: melons, ham, cheese]
                         |                                                     |=door=        \\=trapdoor=
                [Waiting room: benches, 'Wait here. Forever.']                [Cellar arm]   [Trapdoor stair, up]
                       =door=                                                  |                 |
  [Hall of pranks: gears, clappers, chain rings $]--- broken arch ---[The wall's old cellar: army]   |
                         |                                                                       [Sappers' tunnel]--[last dig: water]
                  [The burrow: lanterns]----[Bolt-hole, down 384]----[THE MIGHTY ARMY $ (below)]----+
                         |
                  [The tiny door]
                         |
                    D1: the burrow under the town wall

 Court side (burrow, hall of pranks, waiting room, court) peaceful until court_hostile; cellar, larder, army hostile.
 $ chest   = = door   ## secret door   Upper floor 0; the army, the tunnel and the stair at -384.
"""


def write(level):
    d = OUT + '/' + level
    os.makedirs(d, exist_ok=True)
    dump(d + '/project.yml', dict(PROJECT, identity=IDENTITY) if level == 'L4' else PROJECT)
    dump(d + '/plan.yml', plan(level))
    open(d + '/diagram.txt', 'w').write(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(d + '/rooms.yml', {'format': 0, 'themes': THEMES, 'defaults': {'theme': 'theme:burrow', 'ambient': 16},
                                'rooms': ROOMS, 'openings': OPENINGS,
                                'notes': "DD-04 at L3/L4: twelve rooms in the plan's frame (x east, y north, the "
                                         "tiny door's sill at y 0). Written by output/studio_cal/dd04/tools/gen.py."})
    if level == 'L4':
        dump(d + '/objects.yml', OBJECTS)
        dump(d + '/wiring.yml', WIRING)


if __name__ == '__main__':
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
