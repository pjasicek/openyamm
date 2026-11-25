#!/usr/bin/env python3
"""XD-09 Golem Dungeon: writes the whole brief, L1 to L4, of devdocs/xeen/briefs/xd09/ (lane A8, phase 2).

L1: plan.yml (spaces without places), project.yml, diagram.txt. L2: plan.yml with places (`at`, `extent`), heights,
mechanisms and totals. L3: L2 plus rooms.yml (the shell, no doors). L4: L3 plus objects.yml, wiring.yml, the
playtests stay hand-written beside them. Rerun after every change here, then `oymap fmt` and `oymap record`; never
hand-edit the written files. x east, y north; the hub floor is 0, the stone level 256-512, the diamond level -640.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import math
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
B = R / 'devdocs/xeen/briefs/xd09'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# ================================================================ families (one shipped map per area)
# Stone (hub, entry, stone level): MM7 Stone City (7d24), the dwarves' city cut in the mountain: block brick cwb,
# rough rock cwb1, rough floor cfb1, tan flags 7tfb1, its doors hdr1dl/hdr1dr.
CWB = S('cwb', 128, 256)
CWB1 = S('cwb1', 128, 256)
CFB1 = S('cfb1', 128, 128)
TFB = S('7tfb1', 128, 128)
SDOOR = S('hdr1dl', 128, 256)
# merge point 15 (the double-door rule): Stone City's door is two wings, hdr1dl left and hdr1dr right, one per leaf.
SDOOR_PAIR = [[S('hdr1dl', 128, 256), S('hdr1dr', 128, 256)]]
# Wood (trunk, branches, crown, heartwood): MM6 Warlord's Fortress (6d16), its timber: wood grain cbeam5 and bemdk4,
# beam planks bemstrt1, the earth ceiling d8ceild, the plank door d2smldor.
GRAIN = S('cbeam5', 64, 512)
BARK = S('bemdk4', 32, 256)
PLANK = S('bemstrt1', 256, 32)
EARTH = S('d8ceild', 256, 256)
WDOOR = S('d2smldor', 128, 256)
# Iron (forge, tumblers, furnace, lock hall): MM6 Gharik's Forge (6d18): soot brick d2wlactr, dark iron rock vlcwl3a,
# volcanic tile 6voltyl, beam ceiling d2ceil1, the iron-bound stone door cvdor1, lava orfyrlga, veined rock vlcwl1.
SOOT = S('d2wlactr', 128, 256)
IRON = S('vlcwl3a', 128, 256)
VTILE = S('6voltyl', 128, 128)
BEAMS = S('d2ceil1', 256, 256)
IDOOR = S('cvdor1', 128, 256)
LAVA = S('orfyrlga', 256, 256)
VEIN = S('vlcwl1', 128, 256, scale=2)  # each texture at its own size, scaled (merge point 17)
# The great lock's lid and its three bolts: A6's dark iron xwiron (XD-04's riveted plates, 128 square: riveted bands every
# 64 texels, image rows 62-70 and 127-6, columns 17-24 and 81-88). Offsets put the bands where the eye reads them: on
# each bolt a band round it 48 up (the middle of what shows over the lid), across its end face between two upright
# straps; on its top straps across it 12 in from the lock end and every 64 back, two along it 16 in from its sides;
# the lid's top bands 32 in from its long sides and 40 from its short ones, its edge a band at half height.
IRONPL = 'xwiron'
BOLT_SIDE = S(IRONPL, 128, 128, offset=[-8, 42])
BOLT_END = S(IRONPL, 128, 128, offset=[4, 42])
LID_SIDE = S(IRONPL, 128, 128, offset=[0, 54])
LID_TOP = S(IRONPL, 128, 128, offset=[52, 26])
# Diamond (diamond stair, hall, vault, vault stair): MM8 Prison of the Lord of Fire (d37): pale ice marble gtempw3 and
# gtempw1, blue brick floor gtempflr, the gold mosaic ceiling gtemprf, the rune door gtempdor1, cyan crystal gcrysc3.
ICE = S('gtempw3', 128, 256)
ICE1 = S('gtempw1', 128, 256)
BLUEFL = S('gtempflr', 128, 128)
MOSAIC = S('gtemprf', 128, 128)
DDOOR = S('gtempdor1', 128, 256)
CRYS = S('gcrysc3', 32, 64)

themes = [
    {'id': 'theme:stone_hall', 'wall': CWB, 'floor': TFB, 'ceiling': CWB1, 'door': SDOOR, 'reveal': CWB,
     'notes': "The Hall of the Plaque, the entry and the stone galleries: MM7 Stone City (7d24): block brick cwb on walls, tan flags 7tfb1 underfoot, the mountain's rough rock cwb1 overhead."},
    {'id': 'theme:quarry', 'wall': CWB1, 'floor': CFB1, 'ceiling': CWB1, 'door': SDOOR, 'reveal': CWB,
     'notes': "The block field and the masons' store: Stone City's rough rock cwb1 on walls and roof, its rough floor cfb1."},
    {'id': 'theme:wood', 'wall': GRAIN, 'floor': PLANK, 'ceiling': EARTH, 'door': WDOOR, 'reveal': BARK,
     'notes': "Home of the Wood: MM6 Warlord's Fortress (6d16): its wood grain cbeam5 on the walls (a hollow trunk's grain), its beam planks bemstrt1 underfoot, its earth ceiling d8ceild, dark bark-red wood bemdk4 in the doorways."},
    {'id': 'theme:forge', 'wall': SOOT, 'floor': VTILE, 'ceiling': BEAMS, 'door': IDOOR, 'reveal': IRON,
     'notes': "Home of the Iron: MM6 Gharik's Forge (6d18): soot brick d2wlactr, volcanic tile 6voltyl, the beam ceiling d2ceil1, the dark iron rock vlcwl3a in the doorways, the iron-bound door cvdor1."},
    {'id': 'theme:diamond', 'wall': ICE, 'floor': BLUEFL, 'ceiling': MOSAIC, 'door': DDOOR, 'reveal': ICE1,
     'notes': "Home of the Diamond: MM8 Prison of the Lord of Fire (d37): pale ice marble gtempw3, blue brick gtempflr underfoot, the gold mosaic ceiling gtemprf, the rune door gtempdor1."},
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


# ================================================================ the hub and the entry (floor 0)
# Six lamps over the Iron door (hub east wall; the door's middle at y 384): panels 96 square, 160 apart, bottom 512.
LAMP_Y = [384 - 400 + 160 * i for i in range(6)]
lamp_panels = []
for i, y in enumerate(LAMP_Y, start=1):
    # the east wall runs counter-clockwise south to north from (1280, -1280): offset is y + 1280 - 48
    lamp_panels.append({'id': f'panel:lamp_{i}', 'offset': y + 1280 - 48, 'length': 96, 'bottom': 528, 'height': 96,
                        'surface': S('vlcwl3a', 128, 256, scale=0.75),
                        'notes': f"Lamp {i} of six over the Iron door: dark iron until a glowing rock of the block field is bared (then lava-bright orfyrlga and a light)."})
room('room:hub', 'Hall of the Plaque', outline=rect(-1280, -1280, 1280, 1280), floor=0, ceiling=1152,
     theme='theme:stone_hall', ambient=26,
     pillars=[{'at': [x, y], 'size': [192, 192], 'surface': CWB} for x in (-704, 704) for y in (-704, 704)],
     platforms=[
         {'id': 'platform:statue_dais', 'at': [0, 0], 'size': [512, 512], 'rise': 32, 'surface': CWB, 'top_surface': TFB,
          'notes': "The statue's dais, one step up."},
         {'id': 'platform:plaque', 'at': [0, 0], 'size': [224, 224], 'base': 32, 'rise': 128, 'surface': S('7tfb1', 128, 128),
          'top_surface': CWB, 'notes': "The statue's plinth with the plaque (m10.golem_plaque): clicked, it shows the rhyme; with the four boughs cut, touching it opens the Stone door."},
     ],
     walls=[{'wall': 'east', 'panels': lamp_panels}],
     notes="The hub, 2,560 square and 1,152 high: four pillars round a golem-maker's statue on a dais, its plinth carrying the rhyme. Four plaque doors: Home of the Wood (west), Home of the Stone (north), Home of the Iron (east, six dark lamps over it), Home of the Diamond (by the entry). A window high in the north wall from the lamp gallery.")
room('room:entry', 'Entry stair', outline=rect(0, -2368, 768, -1344), floor=0, ceiling=768,
     theme='theme:stone_hall', ambient=20,
     levels=[{'id': 'level:landing', 'outline': rect(0, -2368, 768, -1920), 'floor': 192, 'edge': CWB,
              'notes': "The landing inside the tundra door."}],
     flights=[{'from': [384, -1600], 'to': [384, -1920], 'width': 448, 'steps': 6, 'riser': CWB, 'tread': TFB,
               'notes': "Six steps down from the landing to the entry floor."}],
     notes="Down from X5's slab door: a landing and six steps, the hub north through a wide arch, the Diamond door east (opened from below).")

# ================================================================ the diamond level (-640) and the vault stair
room('room:vault_stair', 'Vault stair', outline=rect(832, -1888, 2432, -1376), floor=0,
     slope={'to': -640, 'toward': 'east', 'steps': 20, 'tread': BLUEFL, 'riser': ICE1}, ceiling=448,
     ceiling_slope={'to': -192, 'toward': 'east'}, theme='theme:diamond', ambient=22,
     notes="The way out: 20 steps up from the Diamond vault to the Diamond door by the entry, which opens from this side only.")
room('room:diamond_vault', 'Diamond vault', outline=rect(2496, -2112, 3264, -1152), floor=-640, ceiling=-128,
     theme='theme:diamond', ambient=24,
     notes="The golems' hoard behind the Diamond hall: the vault chest (five King's Megacredits, a level-4 hoard and the plaque 'Master of Golems'). Sealed until the Diamond Golem falls.")
dpillars = [{'at': [x, y], 'size': [128, 128], 'surface': S('gcrysc3', 64, 128)} for x in (3840, 4608) for y in (-2624, -1536)]
room('room:diamond_hall', 'Diamond hall', outline=rect(3328, -3072, 5120, -1088), floor=-640, ceiling=192,
     theme='theme:diamond', ambient=20, pillars=dpillars,
     platforms=[{'id': 'platform:diamond_dais', 'at': [4224, -2496], 'size': [768, 512], 'rise': 32, 'surface': ICE1,
                 'top_surface': BLUEFL, 'notes': "A low dais where the Diamond Golem stands."}],
     notes="A cold hall 1,792 by 1,984 and 832 high under the lock hall's south end: four crystal pillars, the Diamond Golem on its dais; the vault door in the west wall.")
room('room:diamond_stair', 'Diamond stair', outline=rect(4032, -960, 4416, 960), floor=-640,
     slope={'to': -32, 'toward': 'north', 'steps': 19, 'tread': BLUEFL, 'riser': ICE1}, ceiling=-16,
     theme='theme:diamond', ambient=22,
     notes="Below the great lock: a stairwell in the lock hall's floor, 19 steps down south to the Diamond hall; its upper half opens to the hall above through the lock's hole.")

# ================================================================ the iron level (floor 0, east)
room('room:forge', 'Iron forge', outline=rect(1344, -768, 3136, 1280), floor=0, ceiling=768, theme='theme:forge',
     ambient=26,
     platforms=[
         {'id': 'platform:hearth', 'at': [1792, 1120], 'size': [384, 192], 'rise': 96, 'surface': IRON, 'top_surface': LAVA,
          'notes': "The forge's hearth against the north wall, its coals lava-bright (orfyrlga)."},
         {'id': 'platform:anvil_1', 'at': [1920, -448], 'size': [128, 64], 'rise': 80, 'surface': IRON, 'top_surface': IRON,
          'notes': "An anvil block."},
         {'id': 'platform:anvil_2', 'at': [2560, -448], 'size': [128, 64], 'rise': 80, 'surface': IRON, 'top_surface': IRON,
          'notes': "An anvil block."},
         {'id': 'platform:trough', 'at': [2240, -704], 'size': [512, 96], 'rise': 56, 'surface': IRON,
          'top_surface': {'texture': '6voltyl', 'size': [128, 128]},
          'notes': "The cooling trough along the south wall."},
     ],
     notes="Home of the Iron: a soot-black forge 1,792 by 2,048, its hearth along the north wall, two anvils, a cooling trough; the forge chest holds the Iron Key.")
room('room:furnace', 'Furnace passage', path=[[2560, 1344], [2560, 1920], [3456, 1920]], width=384, floor=0,
     ceiling=512, theme='theme:forge', ambient=20,
     walls=[{'wall': 1, 'panels': [{'at': 'centre', 'length': 512, 'bottom': 64, 'height': 128, 'surface': S('orfyrlga', 256, 256, scale=0.5),
                                    'notes': "A furnace mouth in the passage's wall, its fire showing."}]}],
     notes="Hot passage behind the lock hall from the forge to the north tumbler, a furnace mouth glowing in its wall.")
room('room:tumbler_n', 'North tumbler', outline=rect(3520, 1344, 4416, 2240), floor=0, ceiling=576, theme='theme:forge',
     ambient=26, walls=[{'wall': 'south', 'panels': [{'offset': 416, 'length': 128, 'bottom': 58, 'height': 128, 'surface': S('vlcwl1', 128, 256), 'notes': "A plate of veined rock behind the lever, so that it shows on the soot brick."}]}],
     notes="Tumbler lever 1; through a slot in the south wall its bolt is seen at the great lock.")
room('room:lock_hall', 'Hall of the Great Lock', outline=rect(3200, -1024, 5248, 1280), floor=0, ceiling=896,
     theme='theme:forge', ambient=26,
     platforms=[{'id': 'platform:lock_hearth', 'at': [5136, -704], 'size': [224, 448], 'rise': 96, 'surface': IRON,
                 'top_surface': LAVA,
                 'notes': "The golem forge: a casting hearth against the east wall in the south-east corner, its coals lava-bright, the iron pot on them."}],
     walls=[{'wall': 'south', 'panels': [{'offset': 960, 'length': 128, 'bottom': 58, 'height': 128, 'surface': S('vlcwl1', 128, 256), 'notes': "A plate of veined rock behind the lever, so that it shows on the soot brick."}]}],
     notes="A hall 2,048 by 2,304: a lock as big as a door in the floor over the diamond stair, three bolts holding it; tumbler lever 2 on the south wall; the golem forge (a casting hearth, its pot and a brazier) in the south-east corner.")
room('room:tumbler_e', 'East tumbler', outline=rect(5312, -128, 6080, 896), floor=0, ceiling=576, theme='theme:forge',
     ambient=26, walls=[{'wall': 'west', 'panels': [{'offset': 736, 'length': 128, 'bottom': 58, 'height': 128, 'surface': S('vlcwl1', 128, 256), 'notes': "A plate of veined rock behind the lever, so that it shows on the soot brick."}]}],
     notes="Tumbler lever 3; its bolt seen through a slot in the west wall.")

# ================================================================ the stone level (256-512, north)
room('room:stone_stair', 'Stone stair', outline=rect(128, 1344, 640, 2880), floor=0,
     slope={'to': 512, 'toward': 'north', 'steps': 16, 'tread': TFB, 'riser': CWB}, ceiling=448,
     ceiling_slope={'to': 960, 'toward': 'north'}, theme='theme:stone_hall', ambient=22,
     notes="Up 512 from the Stone door to the galleries.")
room('room:quarry_s', 'South gallery', outline=rect(-1856, 2944, 1856, 3456), floor=512, ceiling=1024,
     theme='theme:stone_hall', ambient=22,
     notes="A gallery across the block field's south side, looking down at the nine blocks over a rail; the galleries west and east and the lamp gallery leave it.")
room('room:lamp_gallery', 'Lamp gallery', path=[[-448, 2880], [-448, 1344]], width=384, floor=512, ceiling=896,
     theme='theme:stone_hall', ambient=22,
     notes="A passage from the south gallery to a window high in the hub's north wall: from it the six lamps over the Iron door are seen.")
room('room:quarry', 'The block field', outline=rect(-1280, 3520, 1280, 5568), floor=256, ceiling=1280,
     theme='theme:quarry', ambient=28,
     flights=[{'from': [-448, 5376], 'to': [-1280, 5376], 'to_height': 512, 'width': 256, 'steps': 8, 'riser': CWB, 'tread': TFB,
               'notes': "Steps up along the north wall to the west gallery's doorway."},
              {'from': [448, 5376], 'to': [1280, 5376], 'to_height': 512, 'width': 256, 'steps': 8, 'riser': CWB, 'tread': TFB,
               'notes': "Steps up to the east gallery's doorway."}],
     notes="Home of the Stone: a quarry floor 2,560 by 2,048, 256 below the galleries and open to them over rails; nine stone blocks in three rows, each beside its own empty recess.")
room('room:quarry_w', 'West quarry gallery', outline=rect(-1856, 3520, -1344, 5568), floor=512, ceiling=1024,
     theme='theme:stone_hall', ambient=22, notes="A gallery above the block field; from it you see which blocks are pushed.")
room('room:quarry_e', 'East quarry gallery', outline=rect(1344, 3520, 1856, 5568), floor=512, ceiling=1024,
     theme='theme:stone_hall', ambient=22, notes="The other side of the field; the masons' store east.")
room('room:mason', "Masons' store", outline=rect(1920, 4352, 2944, 5376), floor=512, ceiling=896, theme='theme:quarry',
     ambient=22,
     platforms=[{'id': 'platform:bench', 'at': [2432, 5280], 'size': [512, 128], 'rise': 72, 'surface': PLANK,
                 'top_surface': PLANK, 'notes': "A masons' bench along the north wall."}],
     notes="The golem-masons' store: a bench, cut stone, a chest.")

# ================================================================ the wood level (floor 0 and 256, west)
room('room:trunk', 'The trunk', outline=rect(-4864, -640, -1344, 640), floor=0, ceiling=896, theme='theme:wood',
     ambient=22,
     pillars=[{'at': [x, y], 'size': [160, 160], 'surface': BARK} for x in (-4224, -3712, -2176) for y in (-384, 384)],
     notes="Home of the Wood: a long hall 3,520 by 1,280 carved like the inside of a trunk, its posts like roots; branches off both sides, the crown at the west end.")
room('room:branch_ln', 'Low branch, north', outline=rect(-3456, 704, -2432, 1728), floor=0, ceiling=640,
     theme='theme:wood', ambient=22, notes="A branch-end: a living bough grows across the north wall. The north canopy walk leaves west.")
room('room:branch_ls', 'Low branch, south', outline=rect(-3456, -1728, -2432, -704), floor=0, ceiling=640,
     theme='theme:wood', ambient=22, notes="A branch-end with its bough; the south canopy walk leaves west.")
room('room:crown', 'The crown', outline=rect(-6400, -1024, -4928, 1024), floor=0, ceiling=1024, theme='theme:wood',
     ambient=22,
     flights=[{'from': [-5632, 384], 'to': [-5632, 1024], 'to_height': 256, 'width': 256, 'steps': 8, 'riser': BARK, 'tread': PLANK,
               'notes': "Steps up to the high branch, north."},
              {'from': [-5632, -384], 'to': [-5632, -1024], 'to_height': 256, 'width': 256, 'steps': 8, 'riser': BARK, 'tread': PLANK,
               'notes': "Steps up to the high branch, south."}],
     notes="Where the trunk splits: a hall 1,472 by 2,048, steps up to the two high branches, the heartwood west.")
room('room:branch_hn', 'High branch, north', outline=rect(-6144, 1088, -5120, 2112), floor=256, ceiling=896,
     theme='theme:wood', ambient=22, notes="A high branch-end with its bough; the north canopy walk leaves east.")
room('room:branch_hs', 'High branch, south', outline=rect(-6144, -2112, -5120, -1088), floor=256, ceiling=896,
     theme='theme:wood', ambient=22, notes="A high branch-end with its bough; the south canopy walk leaves east.")
room('room:canopy_n', 'North canopy walk', path=[[-3520, 1408], [-5056, 1408]], width=384, floor=0,
     slope={'to': 256}, ceiling=512, theme='theme:wood', ambient=24,
     notes="A walk climbing 256 from the low branch to the high branch, north.")
room('room:canopy_s', 'South canopy walk', path=[[-3520, -1408], [-5056, -1408]], width=384, floor=0,
     slope={'to': 256}, ceiling=512, theme='theme:wood', ambient=24,
     notes="The south walk.")
room('room:heartwood', 'Heartwood', outline=rect(-7424, -384, -6464, 384), floor=0, ceiling=512, theme='theme:wood',
     ambient=24, notes="The tree's heart: a seed chest.")

# Boughs: one log along the outer wall of each branch-end (destructible platforms, clicked to cut).
BOUGHS = {
    'ln': ('room:branch_ln', [-2816, 1680], [512, 96]),
    'ls': ('room:branch_ls', [-2816, -1680], [512, 96]),
    'hn': ('room:branch_hn', [-5632, 2064], [640, 96]),
    'hs': ('room:branch_hs', [-5632, -2064], [640, 96]),
}
for k, (rm, at, size) in BOUGHS.items():
    for r in rooms:
        if r['id'] == rm:
            r.setdefault('platforms', []).append(
                {'id': f'platform:bough_{k}', 'at': at, 'size': size, 'base': 96, 'rise': 128, 'surface': BARK, 'bottom_surface': BARK,
                 'top_surface': BARK,
                 'notes': "A living bough grown out of the wall: cut it (click, or blows)."})

# ================================================================ D-89 identity (A8 session 29)
# DESIGN_GATING_AND_IDENTITY 2.2, XD-09: the Wood a round trunk with 6d16 bough beams, the Iron a forge with anvils,
# bellows and its glow (6d18), the Diamond crystal pillars and clusters as geometry (d37 gcrysc3).
def _room(rid):
    return next(r for r in rooms if r['id'] == rid)


def rounded(x0, y0, x1, y1, rad, pieces=3):
    """A rectangle with its corners rounded (radius rad, each corner in `pieces` straight pieces), counter-clockwise."""
    pts = []
    for cx, cy, a0 in ((x1 - rad, y0 + rad, -90), (x1 - rad, y1 - rad, 0), (x0 + rad, y1 - rad, 90),
                       (x0 + rad, y0 + rad, 180)):
        for k in range(pieces + 1):
            a = math.radians(a0 + 90 * k / pieces)
            pts.append([round(cx + rad * math.cos(a)), round(cy + rad * math.sin(a))])
    return [pt for i, pt in enumerate(pts) if pt != pts[i - 1]]


# The trunk: round ends, a barrel vault of grain from 576 at the walls to 1,024 along its middle (the hollow trunk's
# inside), crossed by bough beams of the fortress's bark-red wood (bemdk4) every 512.
TR = _room('room:trunk')
TR['outline'] = rounded(-4864, -640, -1344, 640, 256)
TR['ceiling'] = 576


def _vault_h(y):
    return round(576 + 448 * math.sqrt(max(0.0, 1 - (y / 640) ** 2)))


_cp = [[x, y, _vault_h(y)] for x, y in TR['outline']]
_cp += [[x, y, _vault_h(y)] for x in (-4608, -4096, -3584, -3072, -2560, -2048, -1600)
        for y in (-480, -320, -160, 0, 160, 320, 480)]
TR['ceiling_points'] = _cp
TR['beams'] = [{'path': [[x, -640], [x, 640]], 'width': 64, 'depth': 64, 'bottom': 448, 'surface': BARK,
                'notes': "A bough beam across the trunk (the fortress's bark-red wood)."}
               for x in (-4480, -3968, -3200, -2688, -1920)]
TR['notes'] = ("Home of the Wood: a long round-ended hall 3,520 by 1,280, the inside of a hollow trunk: wood grain under a "
               "barrel vault rising to 1,024, bough beams across it every 512, root posts; branches off both sides, the "
               "crown at the west end.")

# The forge: real anvils (a waist and a wide face), a pair of bellows by the hearth, an iron hood over it, the fire on
# the coals and the forge's glow over the room.
FG = _room('room:forge')
FG['platforms'] = [pl for pl in FG['platforms'] if not pl['id'].startswith('platform:anvil')]
for i, x in enumerate((1920, 2560), start=1):
    FG['platforms'] += [
        {'id': f'platform:anvil_{i}', 'at': [x, -448], 'size': [160, 72], 'rise': 56, 'surface': IRON, 'top_surface': IRON,
         'notes': "An anvil's waist."},
        {'at': [x, -448], 'size': [208, 80], 'base': 56, 'rise': 32, 'surface': IRON, 'top_surface': IRON,
         'bottom_surface': IRON, 'notes': "The anvil's face."},
    ]
FG['platforms'] += [
    {'at': [1472, 960], 'size': [160, 128], 'top_size': [96, 112], 'rise': 72, 'surface': BARK, 'top_surface': BARK,
     'notes': "The forge's bellows, a leather wedge on its frame beside the hearth."},
    {'at': [1792, 1152], 'size': [512, 256], 'base': 384, 'rise': 352, 'surface': SOOT, 'bottom_surface': IRON,
     'top_surface': SOOT, 'notes': "The iron hood over the hearth, its chimney up into the roof."},
]

# The Diamond hall: hexagonal pillars of crystal and clusters of tapering shards at their feet and along the walls.
DH = _room('room:diamond_hall')
CRYSTAL = S('gcrysc3', 64, 128)


def _hexagon(cx, cy, r):
    return [[round(cx + r * math.cos(math.radians(60 * k + 30))), round(cy + r * math.sin(math.radians(60 * k + 30)))]
            for k in range(6)]


DH['pillars'] = [{'outline': _hexagon(x, y, 96), 'surface': CRYSTAL} for x in (3840, 4608) for y in (-2624, -1536)]
SHARDS = ((0, 0, 64, 288), (72, -40, 44, 176), (-56, 56, 36, 120), (48, 72, 28, 88))


def _cluster(cx, cy, flip=1):
    return [{'at': [cx + flip * dx, cy + dy], 'size': [sz, sz], 'top_size': [8, 8], 'rise': rise, 'surface': CRYSTAL,
             'top_surface': CRYSTAL, 'notes': "A crystal shard of the diamond hall."} for dx, dy, sz, rise in SHARDS]


for cx, cy, f in ((3456, -2304, 1), (4992, -2304, -1), (3456, -1216, 1), (4736, -1232, -1), (3712, -1712, 1),
                  (4736, -1712, -1), (3968, -2960, 1), (4480, -2960, -1)):
    DH.setdefault('platforms', []).extend(_cluster(cx, cy, f))

# ================================================================ openings
op('open:hub_entry', 'room:hub', 'room:entry', link='link:entry_hub', width=448, height=576, shape='arch', apex=704,
   along=(640 + 896 - 1280) / 768 if False else None)
op('open:hub_trunk', 'room:hub', 'room:trunk', link='link:hub_trunk', width=256, height=384)
op('open:hub_stone', 'room:hub', 'room:stone_stair', link='link:hub_stone', width=256, height=384)
op('open:hub_forge', 'room:hub', 'room:forge', link='link:hub_forge', width=256, height=384, along=(384 + 768) / 2048)
op('open:hub_window', 'room:lamp_gallery', 'room:hub', link='link:lamp_window', width=256, height=256, sill=64,
   notes="A window from the lamp gallery high in the hub's north wall (576 to 832 over the hub floor).")
op('open:entry_vstair', 'room:vault_stair', 'room:entry', link='link:vault_entry', width=256, height=384)
op('open:vstair_vault', 'room:vault_stair', 'room:diamond_vault', link='link:vault_stair_vault', width=384, height=384)
op('open:dhall_vault', 'room:diamond_hall', 'room:diamond_vault', link='link:dhall_vault', width=256, height=384)
op('open:dstair_dhall', 'room:diamond_stair', 'room:diamond_hall', link='link:dstair_dhall', width=320, height=448)
op('open:great_lock', 'room:lock_hall', 'room:diamond_stair', link='link:great_lock', **{'in': 'floor'},
   at=[4224, 376], size=[352, 1136],
   notes="The great lock's hole over the upper half of the diamond stair (the lid mover lies over it).")
op('open:forge_furnace', 'room:forge', 'room:furnace', link='link:forge_furnace', width=320, height=448, from_wall='north', to_wall=5)
op('open:furnace_tn', 'room:furnace', 'room:tumbler_n', link='link:furnace_tn', width=320, height=448)
op('open:tn_lock', 'room:tumbler_n', 'room:lock_hall', link='link:tn_lock', width=256, height=448, along=(3776 - 3520) / 896)
op('open:tn_slot', 'room:tumbler_n', 'room:lock_hall', link='link:tn_slot', width=256, height=112, sill=16,
   along=(4224 - 3520) / 896, notes="The north tumbler's slot: a low gap in the wall through which its bolt is seen.")
op('open:forge_lock', 'room:forge', 'room:lock_hall', link='link:forge_lock', width=256, height=384, along=(-256 + 768) / 2048)
op('open:lock_te', 'room:lock_hall', 'room:tumbler_e', link='link:lock_te', width=192, height=448, along=(704 + 128) / 1024)
op('open:te_slot', 'room:lock_hall', 'room:tumbler_e', link='link:te_slot', width=256, height=112, sill=16,
   along=(376 + 128) / 1024, notes="The east tumbler's slot.")
op('open:stair_south', 'room:stone_stair', 'room:quarry_s', link='link:sstair_landing', width=448, height=384)
op('open:lamp_gallery', 'room:lamp_gallery', 'room:quarry_s', link='link:landing_lamp', width=320, height=384)
op('open:rail_s', 'room:quarry_s', 'room:quarry', link='link:rail_s', width=1792, height=352, sill=72,
   notes="The south gallery's rail over the block field.")
op('open:landing_qw', 'room:quarry_s', 'room:quarry_w', link='link:sstair_qw', width=384, height=448)
op('open:landing_qe', 'room:quarry_s', 'room:quarry_e', link='link:sstair_qe', width=384, height=448)
op('open:rail_w', 'room:quarry_w', 'room:quarry', link='link:rail_w', width=1280, height=352, sill=72, along=0.4,
   notes="The west gallery's rail.")
op('open:qw_quarry', 'room:quarry_w', 'room:quarry', link='link:qw_quarry', width=256, height=384, along=(5376 - 3520) / 2048)
op('open:rail_e', 'room:quarry_e', 'room:quarry', link='link:rail_e', width=1280, height=352, sill=72, along=0.6)
op('open:qe_quarry', 'room:quarry_e', 'room:quarry', link='link:quarry_qe', width=256, height=384, along=(5568 - 5376) / 2048)
op('open:qe_mason', 'room:quarry_e', 'room:mason', link='link:qe_mason', width=256, height=384)
op('open:trunk_ln', 'room:trunk', 'room:branch_ln', link='link:trunk_ln', width=384, height=512)
op('open:trunk_ls', 'room:trunk', 'room:branch_ls', link='link:trunk_ls', width=384, height=512)
op('open:trunk_crown', 'room:trunk', 'room:crown', link='link:trunk_crown', width=640, height=704, shape='arch', apex=832)
op('open:crown_hn', 'room:crown', 'room:branch_hn', link='link:crown_hn', width=256, height=384, along=None)
op('open:crown_hs', 'room:crown', 'room:branch_hs', link='link:crown_hs', width=256, height=384, along=None)
op('open:crown_heart', 'room:crown', 'room:heartwood', link='link:crown_heart', width=320, height=384)
op('open:canopy_n_low', 'room:branch_ln', 'room:canopy_n', link='link:canopy_n', width=320, height=384)
op('open:canopy_n_high', 'room:canopy_n', 'room:branch_hn', link='link:canopy_n', width=320, height=384)
op('open:canopy_s_low', 'room:branch_ls', 'room:canopy_s', link='link:canopy_s', width=320, height=384)
op('open:canopy_s_high', 'room:canopy_s', 'room:branch_hs', link='link:canopy_s', width=320, height=384)
for o in openings:
    if o.get('along') is None:
        o.pop('along', None)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:stone_hall', 'ambient': 22}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-09 Golem Dungeon at L4 (x east, y north; the hub floor 0, the stone level 256 to 512, the diamond level -640). Four families, one per area: MM7 Stone City (7d24) for the hub, the entry and the stone level; MM6 Warlord's Fortress (6d16) for the wood; MM6 Gharik's Forge (6d18) for the iron; MM8 Prison of the Lord of Fire (d37) for the diamond. Written by output/studio_cal/xd09/tools/gen.py."}

# ================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:entry', 'at': [384, -2176], 'facing': 90,
                    'notes': "On the landing inside the tundra door, facing in (north)."}
objects['doors'] = [
    {'id': 'door:wood', 'opening': 'open:hub_trunk', 'kind': 'slide_up', 'surface': WDOOR,
     'notes': "Home of the Wood: the fortress's plank door (d2smldor); opens."},
    {'id': 'door:stone', 'opening': 'open:hub_stone', 'kind': 'hinged', 'leaves': 2, 'pictures': SDOOR_PAIR, 'back_pictures': SDOOR_PAIR,
     'notes': "Home of the Stone: Stone City's double door (hdr1dl, hdr1dr, a hinged pair); opened by touching the statue once the four boughs are cut."},
    {'id': 'door:iron', 'opening': 'open:hub_forge', 'kind': 'slide_up', 'surface': IDOOR,
     'notes': "Home of the Iron: the forge's iron-bound door (cvdor1); opens when the six lamps over it burn."},
    {'id': 'door:diamond', 'opening': 'open:entry_vstair', 'kind': 'slide_up', 'surface': DDOOR,
     'notes': "Home of the Diamond: the rune door (gtempdor1) by the entry; opens from the vault stair only."},
    {'id': 'door:mason', 'opening': 'open:qe_mason', 'kind': 'hinged', 'leaves': 2, 'pictures': SDOOR_PAIR, 'back_pictures': SDOOR_PAIR,
     'notes': "Stone City's double door (hdr1dl, hdr1dr): a hinged pair (the user's double-door rule, merge point 15)."},
    {'id': 'door:forge_lock', 'opening': 'open:forge_lock', 'kind': 'slide_up', 'surface': IDOOR},
    {'id': 'door:vault', 'opening': 'open:dhall_vault', 'kind': 'slide_up', 'surface': DDOOR,
     'notes': "The vault door: rises when the Diamond Golem falls."},
]

# The block field: nine blocks (256 square, 192 high) each sliding 256 east into its own recess.
COLS = [-896, -128, 640]
ROWS = [3904, 4416, 4928]
ROCKS = {'11': 1, '12': 2, '21': 3, '23': 4, '32': 5, '33': 6}   # row, col (south to north, west to east) -> lamp
objects['movers'] = []
plates = []
lights = []
for r, cy in enumerate(ROWS, start=1):
    for c, cx in enumerate(COLS, start=1):
        k = f'{r}{c}'
        rock = k in ROCKS
        objects['movers'].append(
            {'id': f'mover:block_{k}', 'room': 'room:quarry', 'at': [cx, cy], 'size': [256, 256], 'height': 192,
             'travel': [256, 0, 0], 'speed': 128, 'surface': CWB, 'top_surface': CWB1,
             'notes': f"Stone block {k} (row {r} from the south, column {c} from the west): pushed, it slides 256 east into its recess and stays. " + ("It hides a glowing rock." if rock else "Bare stone under it.")})
        if rock:
            plates.append({'id': f'plate:rock_{k}', 'room': 'room:quarry', 'at': [cx, cy], 'size': [192, 192],
                           'surface': S('vlcwl1', 128, 256, scale=1.5), 'notes': "A glowing rock under the block (veined rock vlcwl1)."})
            lights.append({'id': f'light:rock_{k}', 'room': 'room:quarry', 'at': [cx, cy], 'height': 64, 'radius': 640,
                           'color': [255, 150, 60], 'on': False, 'pulse': {'intensity': [0.7, 1.0], 'frequency': 0.4},
                           'notes': "The bared rock's glow."})
# The great lock: a lid of dark iron over the stairwell hole; three bolts hold it.
objects['movers'] += [
    {'id': 'mover:lid', 'room': 'room:lock_hall', 'at': [4224, 376], 'size': [384, 1168], 'floor_height': 0, 'height': 24,
     'travel': [-512, 0, 0], 'speed': 96, 'surface': LID_SIDE, 'top_surface': LID_TOP,
     'notes': "The great lock: a plate of dark riveted iron (xwiron) 384 by 1,168 lying over the stairwell; it slides 512 west when the Iron Key turns with the three bolts drawn."},
    {'id': 'mover:bolt_n', 'room': 'room:lock_hall', 'at': [4224, 1040], 'size': [96, 160], 'height': 72,
     'travel': [0, 128, 0], 'speed': 96, 'surface': BOLT_SIDE, 'end_surface': BOLT_END,
     'top_surface': S(IRONPL, 128, 128, offset=[52, 14]),
     'notes': "The north bolt (dark riveted iron, a band across its end), shot into the lock; drawn back 128 north by the north tumbler's lever (seen through its slot)."},
    {'id': 'mover:bolt_e', 'room': 'room:lock_hall', 'at': [4496, 376], 'size': [160, 96], 'height': 72,
     'travel': [128, 0, 0], 'speed': 96, 'surface': BOLT_SIDE, 'end_surface': BOLT_END,
     'top_surface': S(IRONPL, 128, 128, offset=[8, 90]),
     'notes': "The east bolt (dark riveted iron, a band across its end); drawn back by the east tumbler's lever."},
    {'id': 'mover:bolt_s', 'room': 'room:lock_hall', 'at': [4224, -288], 'size': [96, 160], 'height': 72,
     'travel': [0, -128, 0], 'speed': 96, 'surface': BOLT_SIDE, 'end_surface': BOLT_END,
     'top_surface': S(IRONPL, 128, 128, offset=[52, 38]),
     'notes': "The south bolt (dark riveted iron, a band across its end); drawn back by the lever on the lock hall's south wall."},
]
objects['plates'] = plates
objects['switches'] = [
    {'id': 'switch:lever_n', 'room': 'room:tumbler_n', 'kind': 'lever', 'at': [4000, 1344], 'reach': 48,
     'notes': "Tumbler lever 1 (north tumbler): two-way; it draws or shoots the north bolt, seen through the slot beside it."},
    {'id': 'switch:lever_s', 'room': 'room:lock_hall', 'kind': 'lever', 'at': [4224, -1024], 'reach': 48,
     'notes': "Tumbler lever 2 (lock hall, south wall): two-way; the south bolt."},
    {'id': 'switch:lever_e', 'room': 'room:tumbler_e', 'kind': 'lever', 'at': [5312, 96], 'reach': 48,
     'notes': "Tumbler lever 3 (east tumbler, west wall): two-way; the east bolt, seen through the slot."},
]
objects['floors'] = []


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


for i, y in enumerate(LAMP_Y, start=1):
    lights.append(light(f'light:lamp_{i}', 'room:hub', [1216, y], 576, 700, [255, 140, 60], on=False,
                        notes=f"Lamp {i} over the Iron door, dark until its rock is bared."))
lights += [
    light('light:statue', 'room:hub', [0, 0], 520, 1200, [200, 210, 255], notes="A cold light on the statue."),
    light('light:lock', 'room:lock_hall', [4224, 376], 640, 1500, [255, 170, 110], notes="Light over the great lock (the room's torches gathered)."),
    light('light:bolt_n', 'room:lock_hall', [4224, 1150], 160, 600, [255, 160, 90]),
    light('light:bolt_e', 'room:lock_hall', [4640, 376], 160, 600, [255, 160, 90]),
    light('light:bolt_s', 'room:lock_hall', [4224, -420], 160, 600, [255, 160, 90]),
    light('light:lever_s', 'room:lock_hall', [4224, -880], 220, 520, [255, 150, 80], notes="A glow on tumbler lever 2's plate."),
    light('light:lever_n', 'room:tumbler_n', [4000, 1480], 220, 520, [255, 150, 80]),
    light('light:lever_e', 'room:tumbler_e', [5450, 96], 220, 520, [255, 150, 80]),
    light('light:field_w', 'room:quarry', [-640, 4416], 900, 1700, [255, 220, 170]),
    light('light:field_e', 'room:quarry', [640, 4416], 900, 1700, [255, 220, 170]),
    light('light:hearth', 'room:forge', [1792, 980], 220, 1400, [255, 120, 50], pulse={'intensity': [0.7, 1.0], 'frequency': 0.7},
          notes="The forge's coals."),
    light('light:forge_glow', 'room:forge', [2240, 448], 360, 1700, [255, 140, 70],
          pulse={'intensity': [0.75, 1.0], 'frequency': 0.5}, notes="D-89: the forge's red glow over the anvils (6d18)."),
    light('light:lock_forge', 'room:lock_hall', [5040, -704], 200, 1300, [255, 120, 50], pulse={'intensity': [0.7, 1.0], 'frequency': 0.6},
          notes="The golem forge's coals in the lock hall."),
    light('light:furnace', 'room:furnace', [2560, 1700], 160, 900, [255, 110, 40], pulse={'intensity': [0.6, 1.0], 'frequency': 0.5}),
    light('light:diamond', 'room:diamond_hall', [4224, -2080], 600, 1800, [170, 220, 255],
          notes="The diamond hall's cold glow."),
    light('light:vault', 'room:diamond_vault', [2880, -1632], 320, 800, [190, 230, 255]),
    light('light:heart', 'room:heartwood', [-6944, 0], 300, 700, [190, 255, 150], pulse={'intensity': [0.6, 1.0], 'frequency': 0.3},
          notes="A green glow in the tree's heart."),
]
objects['lights'] = lights
objects['sounds'] = [
    {'id': 'sound:forge', 'room': 'room:forge', 'at': [1792, 960], 'sound': 'raging fire loop', 'radius': 1800,
     'inner_radius': 500, 'volume': 0.5, 'notes': "The forge's fire."},
    {'id': 'sound:furnace', 'room': 'room:furnace', 'at': [2560, 1700], 'sound': 'raging fire loop', 'radius': 1100,
     'inner_radius': 300, 'volume': 0.4},
    {'id': 'sound:lock_forge', 'room': 'room:lock_hall', 'at': [5136, -704], 'sound': 'raging fire loop', 'radius': 1300,
     'inner_radius': 400, 'volume': 0.4, 'notes': "The golem forge's coals."},
    {'id': 'sound:quarry_drip', 'room': 'room:quarry', 'at': [0, 4416], 'sound': 'drip02', 'radius': 1800,
     'volume': 0.5, 'wait': [4, 10], 'notes': "Water dripping in the quarry."},
    {'id': 'sound:heart_drip', 'room': 'room:heartwood', 'at': [-6944, 0], 'sound': 'drip03', 'radius': 1000,
     'volume': 0.4, 'wait': [5, 12]},
]
objects['chests'] = [
    {'id': 'chest:mason', 'room': 'room:mason', 'at': [2816, 4480], 'facing': 'n', 'kind': '7gt002',
     'treasure_level': 3, 'random_items': 3, 'gold': 600, 'notes': "The masons' chest (Stone City's chest)."},
    {'id': 'chest:heart', 'room': 'room:heartwood', 'at': [-7296, 0], 'facing': 'n', 'kind': 'ch3',
     'treasure_level': 3, 'random_items': 3, 'notes': "The seed chest in the tree's heart."},
    {'id': 'chest:forge', 'room': 'room:forge', 'at': [1472, 1152], 'facing': 'e', 'kind': 'ch3',
     'items': ['iron_key'], 'treasure_level': 3, 'random_items': 2,
     'notes': "The forge chest: the Iron Key and two rolls of level 3."},
    {'id': 'chest:vault', 'room': 'room:diamond_vault', 'at': [2880, -1248], 'kind': '7gt002',
     'items': ['megacredit'] * 5, 'gold': 3000, 'treasure_level': 4, 'random_items': 4,
     'notes': "The vault chest: five King's Megacredits (m10.golem_vault's map_gives) and a level-4 hoard."},
]
# Spawn markers: slot 1 Material golems (Xeen Golem): tier a Wood Golem 11580, b Stone Golem 11581, c Iron Golem
# 11582, one or two each (expected 1.5): wood 15 markers, stone 11, iron 3, plus the placed Iron Golem and the boss.
SP = []


def sp(id, rm, at, tier, **kw):
    d = {'id': f'spawn:{id}', 'room': rm, 'at': at, 'slot': 1, 'tier': tier, 'group': 51}
    d.update(kw)
    SP.append(d)


sp('hub', 'room:hub', [-640, 0], 'a', notes="Wood golems standing guard in the hall.")
sp('trunk_e', 'room:trunk', [-2944, 0], 'a')
sp('trunk_w', 'room:trunk', [-4480, 0], 'a')
sp('ln_1', 'room:branch_ln', [-3200, 1088], 'a')
sp('ln_2', 'room:branch_ln', [-2688, 1216], 'a')
sp('ls_1', 'room:branch_ls', [-3200, -1088], 'a')
sp('ls_2', 'room:branch_ls', [-2688, -1216], 'a')
sp('crown_n', 'room:crown', [-5248, 512], 'a')
sp('crown_s', 'room:crown', [-5248, -512], 'a')
sp('hn_1', 'room:branch_hn', [-5888, 1472], 'a')
sp('hn_2', 'room:branch_hn', [-5376, 1600], 'a')
sp('hs_1', 'room:branch_hs', [-5888, -1472], 'a')
sp('hs_2', 'room:branch_hs', [-5376, -1600], 'a')
sp('heart', 'room:heartwood', [-6784, -128], 'a')
sp('canopy_n', 'room:canopy_n', [-4288, 1408], 'a', radius=64)
sp('stone_stair', 'room:stone_stair', [384, 2560], 'b', radius=96)
sp('landing', 'room:quarry_s', [1024, 3200], 'b')
sp('qw_1', 'room:quarry_w', [-1600, 3968], 'b', radius=96)
sp('qw_2', 'room:quarry_w', [-1600, 4864], 'b', radius=96)
sp('qe_1', 'room:quarry_e', [1600, 3968], 'b', radius=96)
sp('qe_2', 'room:quarry_e', [1600, 4864], 'b', radius=96)
sp('field_1', 'room:quarry', [-384, 3648], 'b', radius=64)
sp('field_2', 'room:quarry', [384, 4672], 'b', radius=64)
sp('field_3', 'room:quarry', [-1152, 5120], 'b', radius=64)
sp('mason_1', 'room:mason', [2176, 4608], 'b', radius=96)
sp('mason_2', 'room:mason', [2688, 4864], 'b', radius=96)
sp('forge', 'room:forge', [2240, -256], 'c')
sp('furnace', 'room:furnace', [3072, 1920], 'c', radius=64)
sp('lock', 'room:lock_hall', [3584, 768], 'c')
objects['spawns'] = SP
objects['monsters'] = [
    {'id': 'monster:diamond', 'room': 'room:diamond_hall', 'monster': 11583, 'at': [4224, -2496], 'facing': 90,
     'hostile': True, 'group': 2,
     'notes': "The Diamond Golem: the world's boss row 11583 (level 50, 1,200 hit points); its death opens the vault."},
    {'id': 'monster:iron_guard', 'room': 'room:diamond_hall', 'monster': 11582, 'at': [3712, -1408], 'facing': 0,
     'hostile': True, 'group': 2, 'notes': "An Iron Golem at the vault door."},
]
decos = []
n = [0]


def torch(rm, wall, along, kind='torch01', h=None):
    n[0] += 1
    d = {'id': f'deco:torch_{n[0]}', 'room': rm, 'decoration': kind, 'wall': wall, 'along': along}
    if h is not None:
        d['height'] = h
    decos.append(d)


for rm, walls in [('room:hub', [('north', 0.1), ('north', 0.9), ('south', 0.1), ('south', 0.9), ('west', 0.2), ('west', 0.8),
                                ('east', 0.15)]),
                  ('room:entry', [('west', 0.3), ('east', 0.25, 320)]),
                  ('room:trunk', [('north', 0.1), ('north', 0.6), ('south', 0.1), ('south', 0.6), ('north', 0.9), ('south', 0.9)]),
                  ('room:branch_ln', [('west', 0.85), ('east', 0.5)]), ('room:branch_ls', [('west', 0.15), ('east', 0.5)]),
                  ('room:branch_hn', [('west', 0.5), ('east', 0.75)]), ('room:branch_hs', [('west', 0.5), ('east', 0.25)]),
                  ('room:crown', [('west', 0.2), ('west', 0.8), ('north', 0.85), ('south', 0.15)]),
                  ('room:heartwood', [('north', 0.5), ('south', 0.5)]),
                  ('room:stone_stair', [('west', 0.3, 486), ('east', 0.7, 486)]),
                  ('room:quarry_s', [('south', 0.1), ('south', 0.9), ('south', 0.25)]),
                  ('room:quarry_w', [('west', 0.2), ('west', 0.5), ('west', 0.8)]),
                  ('room:quarry_e', [('east', 0.2), ('east', 0.8)]),
                  ('room:quarry', [('south', 0.1), ('south', 0.9), ('north', 0.5)]),
                  ('room:mason', [('south', 0.5), ('east', 0.5)]),
                  ('room:forge', [('south', 0.2), ('south', 0.8), ('west', 0.15)]),
                  ('room:lock_hall', [('west', 0.6), ('west', 0.2), ('east', 0.85), ('south', 0.2), ('south', 0.8), ('north', 0.85), ('north', 0.1)]),
                  ('room:tumbler_n', [('north', 0.25), ('north', 0.75), ('east', 0.5)]), ('room:tumbler_e', [('east', 0.25), ('east', 0.75), ('north', 0.5)])]:
    # lights audit (merge point 14): the branches' torches out of the canopy paths' mouths (low west, high east), the
    # south gallery's out of the lamp gallery's, the entry's off the diamond door onto the landing (its floor 192);
    # a third number is the torch's height over the room's base floor: the stone stair's climb 512 northward, so its
    # torches (y 2419, the step's floor 358) hang 128 over their step, not under it
    for w, a, *h in walls:
        torch(rm, w, a, h=h[0] if h else None)
decos += [
    {'id': 'deco:statue', 'room': 'room:hub', 'decoration': '7dec54', 'at': [0, 0], 'floor_height': 160, 'facing': 270,
     'notes': "The statue over the plaque (MM7's large statue: the golem-maker); clicked, it runs the plaque's event."},
    {'id': 'deco:forge_fire', 'room': 'room:forge', 'decoration': 'ckfyr00', 'at': [1792, 1120], 'floor_height': 96,
     'notes': "D-89: the fire on the forge's coals, under the hood."},
    {'id': 'deco:forge_pot', 'room': 'room:lock_hall', 'decoration': 'cauld00', 'at': [5136, -704], 'floor_height': 96,
     'notes': "The golem forge's casting pot on the hearth's coals (MM6's bubbling cauldron)."},
    # lights audit (merge point 14): MM6's brazier hangs on chains: from the hall's ceiling (896), its top 2 into it
    {'id': 'deco:forge_brazier', 'room': 'room:lock_hall', 'decoration': 'brzier00', 'at': [5152, -320], 'height': 748,
     'hangs': True, 'notes': "A lit brazier hung on its chains over the hearth's north end, by the east wall."},
    {'id': 'deco:mason_rock', 'room': 'room:mason', 'decoration': '6rock02', 'at': [2816, 4864]},
    {'id': 'deco:mason_rock_2', 'room': 'room:mason', 'decoration': '6rock04', 'at': [2816, 5248]},
    {'id': 'deco:crys_1', 'room': 'room:diamond_hall', 'decoration': 'crclstr', 'at': [3456, -2944]},
    {'id': 'deco:crys_2', 'room': 'room:diamond_hall', 'decoration': 'crys5', 'at': [4992, -2944]},
    {'id': 'deco:crys_3', 'room': 'room:diamond_hall', 'decoration': 'crclstr', 'at': [4992, -1216]},
]
objects['decorations'] = decos
objects['destructibles'] = [
    {'id': f'destructible:bough_{k}', 'of': f'platform:bough_{k}', 'hp': 30, 'material': 'wood', 'effect_scale': 1.5,
     'sound': 'Events/shatterwood02.wav', 'on_destroyed': f'evt:bough_{k}_cut',
     'notes': "A living bough: blows, missiles or a click (a cut) break it; its breaking counts on the plaque."}
    for k in BOUGHS]
objects['exits'] = [
    {'id': 'exit:x5', 'room': 'room:entry', 'wall': 'south', 'floor_height': 192, 'size': [224, 384],
     'surface': S('7solid01', 128, 256, fit=True), 'to': 'door:x5',
     'notes': "The stone door to Winterkill Tundra (X5) on the landing: out to the Golem Rocks' slab door."},
]

# ================================================================ wiring
var = lambda name: {'map_var': name}
COUNT_BOUGHS = (
    "local s\n"
    "if IsAtLeast(MapVar(boughs), 4) then s = tr('The last branch falls. Return to the statue.')\n"
    "elseif IsAtLeast(MapVar(boughs), 3) then s = tr('One branch remains.')\n"
    "elseif IsAtLeast(MapVar(boughs), 2) then s = tr('Two branches remain.')\n"
    "elseif IsAtLeast(MapVar(boughs), 1) then s = tr('Three branches remain.')\n"
    "else s = tr('Four branches remain.') end\n")
COUNT_ROCKS = (
    "local n = 0\n"
    "for i = 1, 6 do if IsAtLeast(MapVar(rocks), i) then n = i end end\n")
events = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'not': {'qbit': 'arrived_once'}},
     'effects': [{'qbit': 'arrived_once'}, {'message': "The slab door grinds open at a push, and shut again behind you. Emerson's King's Megacredits for Newcastle lie somewhere below, the golems' hoard; the golems that keep this place were never told to stop."}],
     'notes': "Why the party is here (M10: the five Megacredits for Newcastle's keep; no arrival hook exists for XD-09); first arrival only (arrived_once 110601)."},
    {'id': 'evt:exit_x5', 'preset': 'exit', 'source': 'exit:x5', 'title': 'Exit Golem Dungeon',
     'notes': "Out to X5 (installed): the original 'Exit Golem Dungeon?' (aaze0081:10) as the hint; the game's window asks 'Do you wish to leave Golem Dungeon?'."},
    {'id': 'evt:wood_door', 'preset': 'door', 'source': 'door:wood', 'title': 'Home of the Wood', 'action': 'open',
     'text': "A plaque over the door reads: Home of the Wood", 'seconds': 4},
    {'id': 'evt:stone_door', 'preset': 'script', 'source': 'door:stone', 'title': 'Home of the Stone',
     'condition': {'not': var('stone_open')},
     'effects': [{'text': "A plaque over the door reads: Home of the Stone. The door is shut fast; there is no ring or keyhole."}],
     'else_effects': [{'text': "A plaque over the door reads: Home of the Stone"}]},
    {'id': 'evt:iron_door', 'preset': 'script', 'source': 'door:iron', 'title': 'Home of the Iron',
     'condition': {'not': {'map_var': {'name': 'rocks', 'at_least': 6}}},
     'effects': [{'lua': COUNT_ROCKS + "evt.SimpleMessage(tr('A plaque over the door reads: Home of the Iron. The door is shut fast. Six lamps are set in the stone above it; {count} of them burn.', {count = n}))"}],
     'else_effects': [{'text': "A plaque over the door reads: Home of the Iron"}]},
    {'id': 'evt:diamond_front', 'preset': 'script', 'source': 'door:diamond', 'side': 'room:entry', 'title': 'Home of the Diamond',
     'condition': {'not': var('diamond_open')},
     'effects': [{'text': "A plaque over the door reads: Home of the Diamond. The door has no ring or keyhole on this side."}],
     'else_effects': [{'text': "A plaque over the door reads: Home of the Diamond"}]},
    {'id': 'evt:diamond_back', 'preset': 'door', 'source': 'door:diamond', 'side': 'room:vault_stair', 'title': 'Door',
     'action': 'open', 'sets': var('diamond_open'),
     'text': "The Diamond door swings up: beyond it is the entry stair, by the Hall of the Plaque.", 'seconds': 5},
    {'id': 'evt:mason_door', 'preset': 'door', 'source': 'door:mason', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:forge_lock_door', 'preset': 'door', 'source': 'door:forge_lock', 'title': 'Door', 'action': 'open'},
    # The wood: the statue and the four boughs.
    {'id': 'evt:statue', 'preset': 'script', 'source': 'deco:statue', 'title': 'Statue',
     'condition': {'all': [{'map_var': {'name': 'boughs', 'at_least': 4}}, {'not': var('stone_open')}]},
     'opens': ['door:stone'], 'sets': var('stone_open'),
     'effects': [{'message': "You touch the statue. Deep in the north wall a bar draws back, and the Stone door grinds open."}],
     'else_effects': [{'lua': 'XeenQuests.hook("m10.golem_plaque")\n' + COUNT_BOUGHS + "if not IsAtLeast(MapVar(stone_open), 1) then evt.StatusText(s, 5) end"}],
     'notes': "set:wood: m10.golem_plaque shows the rhyme and the count of boughs left; with all four cut, a touch opens the Stone door."},
]
for k, (rm, at, size) in BOUGHS.items():
    events.append({'id': f'evt:bough_{k}', 'preset': 'script', 'source': f'platform:bough_{k}', 'title': 'Bough',
                   'condition': {'not': var(f'cut_{k}')}, 'sets': var(f'cut_{k}'),
                   'effects': [{'add': {'var': var('boughs'), 'value': 1}}, {'destroy': f'destructible:bough_{k}'},
                               {'lua': COUNT_BOUGHS + "evt.StatusText(tr('You hack through the living bough, and it falls. {remaining}', {remaining = s}), 6)"}],
                   'locked_text': "The bough lies cut.",
                   'notes': "Clicked, the party cuts the bough (its breaking runs the count)."})
    events.append({'id': f'evt:bough_{k}_cut', 'preset': 'script', 'trigger': 'call',
                   'condition': {'not': var(f'cut_{k}')}, 'sets': var(f'cut_{k}'),
                   'effects': [{'add': {'var': var('boughs'), 'value': 1}},
                               {'lua': COUNT_BOUGHS + "evt.StatusText(tr('The bough falls. {remaining}', {remaining = s}), 6)"}],
                   'notes': "The bough's on_destroyed (broken by blows or missiles): counts down on the plaque; a cut by click has counted already."})
# The stone: nine blocks; six bare a glowing rock and light a lamp over the Iron door.
for r, cy in enumerate(ROWS, start=1):
    for c, cx in enumerate(COLS, start=1):
        k = f'{r}{c}'
        ev = {'id': f'evt:block_{k}', 'preset': 'script', 'source': f'mover:block_{k}', 'title': 'Stone Block',
              'condition': {'not': var(f'block_{k}')}, 'opens': [f'mover:block_{k}'], 'sets': var(f'block_{k}'),
              'else_effects': [{'text': "The block sits in its recess."}]}
        if k in ROCKS:
            i = ROCKS[k]
            ev['effects'] = [{'add': {'var': var('rocks'), 'value': 1}},
                             {'lights_on': [f'light:rock_{k}', f'light:lamp_{i}']},
                             {'set_texture': {'of': f'panel:lamp_{i}', 'to': 'orfyrlga'}},
                             {'lua': COUNT_ROCKS + "evt.StatusText(tr('Stone Block - Glowing Rock! Far off, a lamp kindles over the Iron door ({count} of six).', {count = n}), 6)"}]
            ev['notes'] = f"Bares glowing rock {i} (aaze0081:12) and lights lamp {i}."
        else:
            ev['effects'] = [{'text': "The block grinds into its recess. Bare stone beneath it."}]
            ev['seconds'] = 4
        events.append(ev)
for k in ROCKS:
    events.append({'id': f'evt:rock_step_{k}', 'preset': 'text', 'trigger': 'step', 'source': f'plate:rock_{k}',
                   'text': "The glowing rock is warm under your feet.", 'seconds': 3})
events += [
    {'id': 'evt:iron_open', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'map_var': {'name': 'rocks', 'at_least': 6}}, 'opens': ['door:iron'],
     'effects': [{'text': "Six rocks glow. Far below, the Iron door grinds open."}], 'seconds': 6,
     'notes': "set:stone: six lamps open the Iron door."},
    {'id': 'evt:field_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:quarry_s', 'once': True,
     'text': "Below the rail, nine great stone blocks stand on the quarry floor, each beside an empty recess.", 'seconds': 6},
    {'id': 'evt:lamps_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:lamp_gallery', 'once': True,
     'text': "Through the window ahead: the Hall of the Plaque, and six lamps over the Iron door.", 'seconds': 5},
    # The iron: three two-way tumbler levers, the Iron Key, the great lock.
]
# The bolts' door numbers from the lock (kept by every build), for the levers' way back (no `closes` in a branch).
LOCK = B / 'L4' / 'ids.lock.yml'
DOOR_NO = yaml.safe_load(LOCK.read_text())['doors'] if LOCK.exists() else {}
for b, name in (('n', 'north'), ('s', 'south'), ('e', 'east')):
    events.append({'id': f'evt:lever_{b}', 'preset': 'switch', 'source': f'switch:lever_{b}', 'title': 'Lever',
                   'condition': {'not': var(f'bolt_{b}')}, 'opens': [f'mover:bolt_{b}'], 'sets': var(f'bolt_{b}'),
                   'effects': [{'text': f"Iron grinds on iron: the {name} bolt draws back from the great lock."}],
                   'else_effects': [{'set': {'var': var(f'bolt_{b}'), 'value': 0}},
                                    {'lua': f"evt.SetDoorState({DOOR_NO.get(f'mover:bolt_{b}', 0)}, DoorAction.Close)"},
                                    {'text': f"Iron grinds on iron: the {name} bolt shoots home into the great lock."}],
                   'seconds': 5, 'notes': f"Tumbler lever ({name}): two-way; the {name} bolt follows it."})
events += [
    {'id': 'evt:great_lock', 'preset': 'script', 'source': 'mover:lid', 'title': 'Great lock',
     'condition': {'all': [{'item': 'iron_key'}, var('bolt_n'), var('bolt_e'), var('bolt_s'), {'not': var('lid_open')}]},
     'opens': ['mover:lid'], 'sets': var('lid_open'),
     'effects': [{'message': "The Iron Key turns. All is set: the great lock slides aside, and a stair goes down into a cold light."}],
     'else_effects': [{'lua': "if not HasItem(12261) then\n"
                              "    evt.SimpleMessage('A lock as big as a door is set in the floor, held by three bolts. Its keyhole is cut for a great iron key.')\nelse\n"
                              "    local n = 0\n    if not IsAtLeast(MapVar(bolt_n), 1) then n = n + 1 end\n"
                              "    if not IsAtLeast(MapVar(bolt_e), 1) then n = n + 1 end\n    if not IsAtLeast(MapVar(bolt_s), 1) then n = n + 1 end\n"
                              "    if n == 0 then evt.StatusText('The great lock lies open.', 4) else\n"
                              "    evt.SimpleMessage(tr('The Iron Key will not turn: {count} of the three bolts still hold the lock. Their levers are in this hall and in the rooms north and east.', {count = n})) end\nend"}],
     'notes': "set:iron: the Iron Key (forge chest) and the three drawn bolts open the great lock."},
    {'id': 'evt:lock_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:lock_hall', 'once': True,
     'text': "A lock as big as a door lies in the floor, three iron bolts shot into it.", 'seconds': 5},
    # The diamond.
    {'id': 'evt:diamond_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:diamond_hall', 'once': True,
     'text': "A golem of living diamond turns its head. Behind it, the vault door.", 'seconds': 5},
    {'id': 'evt:diamond_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:diamond'}}, 'opens': ['door:vault'],
     'effects': [{'qbit': 'diamond_slain'}],
     'text': "The Diamond Golem shatters, and the vault door grinds up.", 'seconds': 6,
     'notes': "set:diamond: its death opens the vault."},
    {'id': 'evt:vault_door', 'preset': 'script', 'source': 'door:vault', 'title': 'Vault door',
     'condition': {'not': {'qbit': 'diamond_slain'}},
     'effects': [{'text': "The vault door is sealed. It will not move while the Diamond Golem stands."}],
     'else_effects': [{'text': "The vault stands open."}]},
    # Chests.
    {'id': 'evt:chest_mason', 'preset': 'chest', 'source': 'chest:mason', 'title': 'Chest'},
    {'id': 'evt:chest_heart', 'preset': 'chest', 'source': 'chest:heart', 'title': 'Chest'},
    {'id': 'evt:chest_forge', 'preset': 'chest', 'source': 'chest:forge', 'title': 'Chest'},
    {'id': 'evt:chest_vault', 'preset': 'chest', 'source': 'chest:vault', 'title': 'Chest',
     'effects': [{'lua': 'XeenQuests.hook("m10.golem_vault")'}],
     'notes': "m10.golem_vault (once): sets golem_credits, the Master of Golems award and 3,000 experience, and the plaque's lines; the chest holds the five Megacredits."},
    {'id': 'evt:bench', 'preset': 'text', 'source': 'platform:bench', 'title': 'Bench',
     'text': "Chisels, mallets and stone dust: the golem-makers' bench."},
    {'id': 'evt:lock_hearth', 'preset': 'text', 'source': 'platform:lock_hearth', 'title': 'Golem forge',
     'text': "An iron pot simmers on the coals. Here the golem-makers poured the iron limbs of their golems."},
    {'id': 'evt:hearth', 'preset': 'text', 'source': 'platform:hearth', 'title': 'Forge',
     'text': "The forge's coals still glow, though no smith has worked them in an age."},
    # F65 (2026-11-25): the fire and the pot on these hearths are MMerge's self-acting camp fire (food, then it goes
    # out) and stat cauldron; their first click acted instead of the hearth's (tools/xeen/check_self_acting_decos.py).
    {'id': 'evt:forge_fire', 'preset': 'text', 'source': 'deco:forge_fire', 'title': 'Forge',
     'text': "The forge's coals still glow, though no smith has worked them in an age."},
    {'id': 'evt:forge_pot', 'preset': 'text', 'source': 'deco:forge_pot', 'title': 'Golem forge',
     'text': "An iron pot simmers on the coals. Here the golem-makers poured the iron limbs of their golems."},
]
VARIABLES = ['boughs', 'cut_ln', 'cut_ls', 'cut_hn', 'cut_hs', 'stone_open', 'rocks', 'bolt_n', 'bolt_e', 'bolt_s', 'lid_open', 'diamond_open'] + \
    [f'block_{r}{c}' for r in (1, 2, 3) for c in (1, 2, 3)]
wiring = {'format': 0, 'variables': VARIABLES, 'events': events}


project = {
    'format': 0, 'id': 'xeen_xd09', 'name': 'Golem Dungeon', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-09', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [27, 18], 'climbs': 'n'},
    'map_stats': {'id': 9125, 'encounter_chance': 10, 'treasure_level': 3, 'trap_dice': 4, 'perception_difficulty': 6,
                  'refill_days': 672, 'music': 43, 'environment': 'stone hall', 'lock_difficulty': 6, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Golem', 'tier': 2, 'per_marker': [1, 2], 'weight': 100}]},
    'neighbours': [
        {'id': 'door:x5', 'to': 'xeen_x5.odm', 'kind': 'door', 'arrival': [18688, -3457, 960], 'direction': 90,
         'arrival_hint': "On X5 (Winterkill Tundra) 120 north of the Golem Rocks' slab door (thing:xd09_door, near the east edge, by X3), facing away from it, north.",
         'notes': "X5 installed (A6): the lane's arrival 18688, -3457, 960 facing north. X5's door (event 92, m10.golem_door, open since D-89: no Golem Stone) brings the party to this map's start on the landing."},
    ],
    'qbits': {'golem_credits': 111202, 'diamond_slain': 110600, 'arrived_once': 110601},
    'items': {'megacredit': 12192, 'iron_key': 12261, 'golem_stone': 12305},
    'notes': "Xeen design brief, level L4: the Golem Dungeon (XD-09, class M, on X5 near its east edge), story step M10 (the last five King's Megacredits for Newcastle) and the title Master of Golems. Four halls round the Hall of the Plaque, each a two-state puzzle (D-4): four boughs to cut, nine blocks to push (six glowing rocks), the Iron Key and three tumblers, the Diamond Golem. Monsters: slot 1 Material golems (Xeen Golem: Wood Golem 11580 at tier a, Stone Golem 11581 at b, Iron Golem 11582 at c), one or two per marker; placed the Diamond Golem 11583 (boss row) and an Iron Golem. Treasure level 3, the vault a level-4 hoard. Map stats row 9125 (to come from A2's map_rows.yml). Music 43. Items: King's Megacredit 12192, the Iron Key 12261 (requested from A2), the Golem Stone 12305 (X5's door). Qbits: golem_credits 111202 (M10), diamond_slain 110600 (the map's).",
}

# ================================================================ plan (L1, L2)
SPACE_META = {
    # id: (kind, size, purpose, population [(tier, markers)], treasure)
    'room:hub': ('room', 'L', "The statue and its rhyme; four plaque doors: Wood (open), Stone, Iron, Diamond.", [('a', 1)], None),
    'room:entry': ('room', 'S', "Down from X5's slab door; the Diamond door's stair arrives here.", [], None),
    'room:trunk': ('room', 'L', "Home of the Wood: the round, vaulted inside of a hollow trunk crossed by bough beams; branches off both sides.", [('a', 2)], None),
    'room:branch_ln': ('room', 'M', "A branch-end: a living bough to cut.", [('a', 2)], None),
    'room:branch_ls': ('room', 'M', "A branch-end: a living bough to cut.", [('a', 2)], None),
    'room:crown': ('room', 'M', "Where the trunk splits into the high branches.", [('a', 2)], None),
    'room:branch_hn': ('room', 'M', "A high branch-end: a bough to cut.", [('a', 2)], None),
    'room:branch_hs': ('room', 'M', "A high branch-end: a bough to cut.", [('a', 2)], None),
    'room:canopy_n': ('corridor', 'S', "Canopy walk from the low branch up to the high branch.", [('a', 1)], None),
    'room:canopy_s': ('corridor', 'S', "Canopy walk, south.", [], None),
    'room:heartwood': ('room', 'S', "The tree's heart: a seed chest.", [('a', 1)], 3),
    'room:stone_stair': ('corridor', 'S', "Up 512 from the plaque hall's Stone door.", [('b', 1)], None),
    'room:quarry_s': ('corridor', 'M', "A gallery over the block field's south side; the lamp gallery leaves it.", [('b', 1)], None),
    'room:lamp_gallery': ('corridor', 'S', "A window high in the hub's north wall: the six lamps over the Iron door seen from the stone level.", [], None),
    'room:quarry': ('room', 'L', "Nine stone blocks, each sliding into its own recess when pushed; six hide glowing rocks.", [('b', 3)], None),
    'room:quarry_w': ('corridor', 'M', "A gallery above the block field; you see which blocks are pushed.", [('b', 2)], None),
    'room:quarry_e': ('corridor', 'M', "The other side of the field.", [('b', 2)], None),
    'room:mason': ('room', 'S', "Chisels and a chest.", [('b', 2)], 3),
    'room:forge': ('room', 'L', "Home of the Iron: hearth, anvils and a cooling trough; the Iron Key in the forge chest.", [('c', 1)], 3),
    'room:furnace': ('corridor', 'M', "Hot passage from the forge to the north tumbler.", [('c', 1)], None),
    'room:tumbler_n': ('room', 'S', "Tumbler lever 1; through a slot you see its bolt in the great lock.", [], None),
    'room:lock_hall': ('room', 'L', "A lock as big as a door in the floor, three bolts in view; tumbler lever 2 here.", [('c', 1)], None),
    'room:tumbler_e': ('room', 'S', "Tumbler lever 3.", [], None),
    'room:diamond_stair': ('corridor', 'S', "Below the great lock.", [], None),
    'room:diamond_hall': ('room', 'L', "Crystal pillars; the Diamond Golem; its death opens the vault.", [], None),
    'room:diamond_vault': ('room', 'S', "The hoard (tier 4) with the Megacredits; the plaque 'Master of Golems I now dub thee.'", [], 4),
    'room:vault_stair': ('corridor', 'S', "The way out: up to the Diamond door by the entry, opened from below.", [], None),
}
TIER_ROW = {'a': 'Wood Golem 11580', 'b': 'Stone Golem 11581', 'c': 'Iron Golem 11582'}


def bbox(r):
    if 'outline' in r:
        xs = [p[0] for p in r['outline']]; ys = [p[1] for p in r['outline']]
        return min(xs), min(ys), max(xs), max(ys)
    xs = [p[0] for p in r['path']]; ys = [p[1] for p in r['path']]; w = r['width'] / 2
    return min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w


def plan_doc(level):
    spaces = []
    for r in rooms:
        kind, size, purpose, pop, tres = SPACE_META[r['id']]
        x0, y0, x1, y1 = bbox(r)
        floor = r['floor'] if 'slope' not in r else [min(r['floor'], r['slope']['to']), max(r['floor'], r['slope']['to'])]
        s = {'id': r['id'], 'name': r['name'], 'kind': kind, 'size': size, 'extent': [int(x1 - x0), int(y1 - y0)], 'floor': floor,
             'clear_height': r['ceiling'] - r['floor'], 'purpose': purpose}
        if level >= 2:
            s['at'] = [int((x0 + x1) / 2), int((y0 + y1) / 2)]
        if pop:
            s['population'] = [{'slot': 1, 'groups': g, 'per_marker': [1, 2], 'rank': t, 'notes': TIER_ROW[t]} for t, g in pop]
        if r['id'] == 'room:diamond_hall':
            s['population'] = [{'actor': 'Diamond Golem 11583 (boss row)', 'groups': 1, 'notes': 'placed, boss'},
                               {'actor': 'Iron Golem 11582', 'groups': 1, 'notes': 'placed'}]
        if tres:
            s['treasure'] = [{'kind': 'chest', 'count': 1, 'tier': tres}]
        spaces.append(s)
    links = []
    seen = set()
    for o in openings:
        if o['link'] in seen:
            continue
        seen.add(o['link'])
        kind = 'open'
        for d in objects['doors']:
            if d['opening'] == o['id']:
                kind = 'door'
        if o.get('sill', 0) >= 40:
            kind = 'overlook'
        if o.get('in') == 'floor':
            kind = 'stairs'
        links.append({'id': o['link'], 'from': o['from'], 'to': o['to'], 'kind': kind})
    for l in links:
        if l['id'] == 'link:hub_stone':
            l['opened_by'] = 'set:wood'
        if l['id'] == 'link:hub_forge':
            l['opened_by'] = 'set:stone'
        if l['id'] == 'link:great_lock':
            l['condition'] = {'all': [{'item': 12261}, {'map_var': 'bolt_n'}, {'map_var': 'bolt_e'}, {'map_var': 'bolt_s'}]}
            l['opened_by'] = 'set:iron'
        if l['id'] == 'link:dhall_vault':
            l['opened_by'] = 'set:diamond'
        if l['id'] == 'link:vault_entry':
            l['one_way'] = True
            l['opens_from'] = 'room:vault_stair'
    doc = {'format': 0, 'level': f'L{level}',
           'pitch': "Under Winterkill Tundra, behind a slab door in the Golem Rocks, the golem-makers' house: a hall with a statue and a rhyme, and four homes round it. The Wood is a hollow trunk with four living boughs to cut; the Stone a quarry of nine blocks, six over glowing rocks that light the lamps over the Iron door; the Iron a forge, its key, and three tumblers that draw the bolts of a great lock in the floor; below it the Diamond Golem and its vault, where the last five King's Megacredits wait, and a stair back up to the entry.",
           'purpose': "Story step M10 (the last five King's Megacredits for Newcastle's keep) and the title Master of Golems (party award and 3,000 experience). Party 16 to 18 (MAPS section 0): 45 golems in groups of one or two (23 wood 18, 16 stone 26, 5 iron 40) and the Diamond Golem 50; treasure level 3, the vault a level-4 hoard. Three material puzzles in order, two-state mechanisms only (D-4).",
           'mood': "A workshop of stone that still works: lamplit block brick round the statue, the warm grain of the wood hall, the quarry's dust and dripping water, the forge's red coals, then the cold blue of the diamond level.",
           'datum': 'hub floor', 'spaces': spaces, 'links': links,
           'loops': [{'id': 'loop:canopy_n', 'spaces': ['room:trunk', 'room:branch_ln', 'room:canopy_n', 'room:branch_hn', 'room:crown']},
                     {'id': 'loop:canopy_s', 'spaces': ['room:trunk', 'room:branch_ls', 'room:canopy_s', 'room:branch_hs', 'room:crown']},
                     {'id': 'loop:quarry', 'spaces': ['room:quarry_s', 'room:quarry_w', 'room:quarry', 'room:quarry_e']},
                     {'id': 'loop:iron', 'spaces': ['room:forge', 'room:furnace', 'room:tumbler_n', 'room:lock_hall'],
                      'notes': "Round the forge (the graph's order forge, north tumbler, furnace becomes forge, furnace, north tumbler)."}],
           'entrances': [{'id': 'entrance:x5', 'space': 'room:entry', 'kind': 'both', 'neighbour': 'door:x5', 'notes': "From X5's Golem Dungeon door (m10.golem_door, open since D-89) and back out by the same door (exit:x5)."}],
           'critical_path': ['room:entry', 'room:hub', 'room:trunk', 'room:branch_ln', 'room:branch_ls', 'room:crown', 'room:branch_hn',
                             'room:branch_hs', 'room:crown', 'room:trunk', 'room:hub', 'room:stone_stair', 'room:quarry_s', 'room:quarry_w',
                             'room:quarry', 'room:quarry_e', 'room:quarry_s', 'room:stone_stair', 'room:hub', 'room:forge', 'room:furnace',
                             'room:tumbler_n', 'room:lock_hall', 'room:tumbler_e', 'room:lock_hall', 'room:diamond_stair', 'room:diamond_hall',
                             'room:diamond_vault'],
           'return_path': ['room:diamond_vault', 'room:vault_stair', 'room:entry'],
           'goals': [{'id': 'goal:credits', 'space': 'room:diamond_vault', 'notes': "Five King's Megacredits (m10.golem_vault) and Master of Golems."}],
           'keys': [{'id': 'key:iron', 'grants': {'item': 12261}, 'found_in': 'room:forge', 'how': 'chest', 'notes': "The Iron Key 12261 in the forge chest."}],
           'states': [
               {'id': 'set:wood', 'condition': {'map_var': 'stone_open'}, 'opens': ['link:hub_stone'], 'notes': "Four boughs cut (destructibles; the plaque counts them), then the statue touched."},
               {'id': 'set:stone', 'condition': {'map_var': {'name': 'rocks', 'at_least': 6}}, 'opens': ['link:hub_forge'], 'notes': "Six glowing rocks bared (six of nine blocks pushed): six lamps lit."},
               {'id': 'set:iron', 'condition': {'map_var': 'lid_open'}, 'opens': ['link:great_lock'], 'notes': "The Iron Key and the three tumbler levers drawn."},
               {'id': 'set:diamond', 'condition': {'qbit': 110600}, 'opens': ['link:dhall_vault'], 'notes': "The Diamond Golem slain."},
               {'id': 'set:return', 'condition': {'map_var': 'diamond_open'}, 'opens': ['link:vault_entry'], 'notes': "The Diamond door opened from the vault stair."},
           ],
           'diagram': {'file': 'diagram.txt'},
           'notes': "Class M (MAPS: 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors). From the MU-6 graph devdocs/xeen/mockups/act2_graphs/xd09.graph.yml and decider D-4. Rooms added to the graph: the south gallery (the stair's landing over the field), the lamp gallery (the window onto the lamps), two canopy walks, the vault stair. Original lines (aaze0081): the plaque rhyme (:0, m10.golem_plaque), Home of the Wood/Stone/Iron/Diamond (:2-5) over the four doors, 'Stone Block - Glowing Rock' (:12), 'All is set ... Master of Golems I now dub thee.' (:1) and 'King's Megacredit!' (:11) in m10.golem_vault, 'Exit Golem Dungeon?' (:10) at the tundra door out to X5."}
    if level >= 2:
        doc['set_pieces'] = [
            {'id': 'set:wood', 'kind': 'puzzle', 'spaces': ['room:hub', 'room:branch_ln', 'room:branch_ls', 'room:branch_hn', 'room:branch_hs'],
             'rule': "Each branch-end holds a living bough (a destructible block): cut by a click or broken by blows; each break says how many remain; with four cut, touching the statue opens the Stone door."},
            {'id': 'set:stone', 'kind': 'puzzle', 'spaces': ['room:quarry'],
             'rule': "Nine two-state blocks, each sliding 256 east into its own recess when clicked and staying there; six bare a glowing rock and light one of six lamps over the Iron door (seen from the lamp gallery's window); six lamps open it."},
            {'id': 'set:iron', 'kind': 'puzzle', 'spaces': ['room:forge', 'room:tumbler_n', 'room:lock_hall', 'room:tumbler_e'],
             'rule': "Three two-way levers each draw or shoot one bolt of the great lock (seen from the lever); the Iron Key from the forge chest turns only with all three drawn, and the lid slides aside over the diamond stair."},
            {'id': 'set:diamond', 'kind': 'boss', 'spaces': ['room:diamond_hall'], 'rule': "The Diamond Golem's death raises the vault door."},
        ]
        doc['atmosphere'] = "Torch-lit stone (MM6's torch01) in the hub, the wood and the iron; the forge's red hearth and the furnace's glow; dark lamps over the Iron door that light one by one; the quarry's glowing rocks; the diamond level cold and blue with no torches. Music 43; the forge's fire, drips in the quarry and the heartwood."
        doc['totals'] = {'spaces': len(rooms), 'monsters': 45.5, 'chests': 4, 'doors': len(objects['doors'])}
    return doc


DIAGRAM = r"""
                         [Masons' store $]
                                |door
 [W gallery]==rail==[ THE BLOCK FIELD: 9 blocks, 6 rocks ]==rail==[E gallery]
      \_________________[South gallery]___________________/
                      |                 |
                [Stone stair +512]  [Lamp gallery] -> window into the hub, the six lamps
                      |
 [High N]-canopy-[Low N]                     |
   |               |          (Stone door)   |                  [N tumbler: lever 1]--slot--
 [CROWN]--[ TRUNK: Home of the Wood ]--door--[ HALL OF THE PLAQUE ]--door--[ FORGE $ key ]--[furnace]
   |  \            |                         statue, plaque      (Iron door,   |door      [ HALL OF THE GREAT LOCK ]--[E tumbler: lever 3]
 [Heart $]         |                              |               six lamps)    \_________ lever 2, lid over the stair
 [High S]-canopy-[Low S]                     [Entry stair]==Diamond door (from below)==[Vault stair]
                                              X5 door (out)                                 |
                                                                       [VAULT $ Megacredits]--door--[ DIAMOND HALL: Diamond Golem ]
                                                                                                     | (diamond stair, up to the lock)
 $ chest   == one-way   Boughs: the four branch-ends.  Loops: two canopies, round the field, round the forge.
"""


def write(folder, docs):
    folder.mkdir(parents=True, exist_ok=True)
    for name, doc in docs.items():
        if isinstance(doc, str):
            (folder / name).write_text(doc)
        else:
            (folder / name).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))


if __name__ == '__main__':
    l1_project = copy.deepcopy(project)
    l1_project['notes'] = project['notes'].replace('level L4', 'level L1')
    project['identity'] = {
        'shape': 'hall', 'family': '7d24',
        'seen': ["the Hall of the Plaque in Stone City's block brick, the golem-maker's statue and the six lamps",
                 "the Wood: the round, vaulted inside of a hollow trunk crossed by bough beams, branches and crown",
                 "the Iron forge's hearth, hood, bellows and anvils in its glow; the Diamond hall's crystal pillars"]}
    write(B / 'L1', {'plan.yml': plan_doc(1), 'project.yml': l1_project, 'diagram.txt': DIAGRAM})
    write(B / 'L2', {'plan.yml': plan_doc(2), 'project.yml': l1_project, 'diagram.txt': DIAGRAM})
    shell = copy.deepcopy(rooms_doc)
    write(B / 'L3', {'plan.yml': plan_doc(2), 'project.yml': l1_project, 'diagram.txt': DIAGRAM, 'rooms.yml': shell})
    write(B / 'L4', {'plan.yml': plan_doc(2), 'project.yml': project, 'diagram.txt': DIAGRAM, 'rooms.yml': rooms_doc,
                     'objects.yml': objects, 'wiring.yml': wiring})
    print('written')
