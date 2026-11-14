#!/usr/bin/env python3
"""First shell of the Mad Necromancer's Lab rebuild (MM8 d20.blv), written once from measurements of the original.

Every number below was read from `oymap export d20.blv` (faces, sectors, door records) with the helpers in
output/studio_cal/mm8_d20/tools (outline.py: a sector's floor outline; faces.py: a sector's faces; furn.py: the
furniture clusters). Run once for round one; after that the project files are the source and this is not run again.

usage: gen.py <project folder>
"""
import sys
from pathlib import Path

import yaml

out = Path(sys.argv[1])


def tex(name, w, h, **kw):
    d = {'texture': name, 'size': [w, h]}
    d.update(kw)
    return d


WALB = tex('GNecWalB', 256, 256)
WALT = tex('GNecWalT', 256, 256)
FLR = tex('GNecFlr', 128, 128)
CEIL = tex('gn_mtl03', 128, 128)
STPV = tex('GNecStpV', 64, 128)
STPT = tex('GNecStpT', 128, 64)
WAL1 = tex('GNecWal1', 256, 256)
WAL2 = tex('GNecWal2', 128, 256)
CLG2 = tex('GNecClg2', 128, 256)
SWAMP = tex('swamptyl', 128, 128)
C1FL = tex('C1FL', 128, 128)
GRAS = tex('Grastyl', 128, 128)
WATER = {'texture': 'WtrTyl', 'liquid': 'water'}
BEDS = tex('T1beds', 256, 64)
BEDS2 = tex('T1beds2', 128, 256)
BOOKS = tex('T1books', 128, 256)
BOOKS1 = tex('T1books1', 128, 128)
BUTT = tex('T1butt', 32, 32)
BUTTS = tex('T1butts', 32, 32)
TRIM9 = tex('Trim9_32', 32, 64)
TRIM9A = tex('Trim9_32a', 64, 32)
T66 = tex('T66flr2', 128, 128)
SOLID = tex('solid01', 16, 16)
BASIN = tex('T01A01A', 128, 256)
DR4L = tex('GNecDr4L', 128, 256)
DR4R = tex('GNecDr4R', 128, 256)

themes = [
    {'id': 'theme:lab', 'wall': WALT, 'bands': [{'height': 256, 'surface': WALB}], 'floor': FLR, 'ceiling': CEIL,
     'reveal': STPV, 'door': WAL2,
     'notes': 'The laboratory floors (sectors 1 to 5 and 8): GNecWalB from the floor to 256, GNecWalT above, GNecFlr '
              'floor, gn_mtl03 ceiling; doorways GNecStpV jambs (the original lintel is GNecStpT), leaves GNecWal2.'},
    {'id': 'theme:shaft', 'wall': WAL1, 'floor': FLR, 'ceiling': WAL1,
     'notes': 'The lift shaft (sector 6): GNecWal1 walls and roof.'},
    {'id': 'theme:stair', 'wall': SWAMP, 'floor': WAL1, 'ceiling': WAL1,
     'notes': 'The square stair down (sector 7): swamptyl walls, GNecWal1 treads, landings and raking roofs, '
              'GNecStpV risers.'},
    {'id': 'theme:cave', 'wall': SWAMP, 'floor': C1FL, 'ceiling': STPV,
     'notes': 'The lower level (sectors 9 to 26): swamptyl walls 512 high, C1FL floor, GNecStpV ceiling.'},
    {'id': 'theme:under', 'wall': GRAS, 'floor': C1FL, 'ceiling': CEIL,
     'notes': 'The room under the hall (the part of sector 1 at -1024): Grastyl walls, C1FL floor, gn_mtl03 ceiling.'},
]

HALL = [[-1152, -256], [-704, -256], [-256, 256], [-256, 1152], [-704, 1664], [-704, 1440], [-1152, 1440],
        [-1152, 1664], [-1664, 1152], [-1664, 256]]
WELL_IN = [[-960, 576], [-896, 576], [-832, 608], [-800, 672], [-800, 736], [-832, 800], [-896, 832], [-960, 832],
           [-1024, 800], [-1056, 736], [-1056, 672], [-1024, 608]]
KERB_S = [[-1088, 704], [-1088, 672], [-1040, 576], [-960, 544], [-896, 544], [-816, 576], [-768, 672], [-768, 704],
          [-800, 704], [-800, 672], [-832, 608], [-896, 576], [-960, 576], [-1024, 608], [-1056, 672], [-1056, 704]]
KERB_N = [[-768, 704], [-768, 736], [-816, 832], [-896, 864], [-960, 864], [-1040, 832], [-1088, 736], [-1088, 704],
          [-1056, 704], [-1056, 736], [-1024, 800], [-960, 832], [-896, 832], [-832, 800], [-800, 736], [-800, 704]]


def shelf_unit(along, lo, hi, wall_lo, wall_hi, name):
    """A three-shelf rack 416 long and 64 deep against a wall: posts 16 wide at both ends to +304, a base to +64 and
    boards at +128..144, +208..224, +288..304 (T1beds), as the original's racks (29 faces each)."""
    def box(a0, a1, rise, base=0, note=''):
        if along == 'x':
            at = [(a0 + a1) / 2, (wall_lo + wall_hi) / 2]
            size = [a1 - a0, wall_hi - wall_lo]
        else:
            at = [(wall_lo + wall_hi) / 2, (a0 + a1) / 2]
            size = [wall_hi - wall_lo, a1 - a0]
        at = [int(v) if v == int(v) else v for v in at]
        p = {'at': at, 'size': size, 'rise': rise, 'surface': BEDS, 'top_surface': BEDS}
        if base:
            p['base'] = base
            p['bottom_surface'] = BEDS
        p['notes'] = f'{name}: {note}'
        return p
    return [
        box(lo, lo + 16, 304, note='post'),
        box(hi - 16, hi, 304, note='post'),
        box(lo + 16, hi - 16, 64, note='base to +64'),
        box(lo + 16, hi - 16, 16, 128, 'board +128 to +144'),
        box(lo + 16, hi - 16, 16, 208, 'board +208 to +224'),
        box(lo + 16, hi - 16, 16, 288, 'board +288 to +304'),
    ]


def room(rid, name, outline, floor, ceiling, theme, **kw):
    r = {'id': rid, 'name': name, 'outline': outline, 'floor': floor, 'ceiling': ceiling, 'theme': theme}
    r.update(kw)
    return r


rooms = []
rooms.append(room(
    'room:hall', 'Hall of the well', HALL, 0, 512, 'theme:lab',
    walls=[{'wall': 5, 'panels': [{'offset': 0, 'length': 32, 'surface': WAL1},
                                  {'from': 'end', 'offset': 0, 'length': 32, 'surface': WAL1}],
            'notes': 'The lift shaft frame either side of the shaft (faces 1260, 1261, 1349 to 1358: GNecWal1).'}],
    platforms=[
        {'id': 'platform:kerb_s', 'outline': KERB_S, 'rise': 64, 'surface': STPT, 'top_surface': STPT,
         'notes': 'The well kerb, south half: a ring of twelve sides 32 wide and 64 high (faces 8 to 43, GNecStpT).'},
        {'id': 'platform:kerb_n', 'outline': KERB_N, 'rise': 64, 'surface': STPT, 'top_surface': STPT,
         'notes': 'The well kerb, north half.'},
        {'id': 'platform:button_low', 'at': [-1136, 1436], 'size': [24, 8], 'base': 160, 'rise': 24,
         'surface': CLG2, 'top_surface': CLG2, 'bottom_surface': CLG2,
         'notes': "The lift's call button beside the shaft (door record 2, faces 1353 to 1357: a block 24 by 8 by 24 "
                  "on the wall at 160 to 184; its record's direction is 0, so it does not move)."},
    ],
    notes='Sector 1 above the floor: the octagonal hall with the well, the lift shaft in its north side, the exit in '
          'its south wall, double doors west and east.'))
rooms.append(room(
    'room:upper', 'Necromancer\'s quarters', HALL, 545, 1057, 'theme:lab',
    walls=[{'wall': 5, 'panels': [{'offset': 0, 'length': 32, 'surface': WAL1},
                                  {'from': 'end', 'offset': 0, 'length': 32, 'surface': WAL1}],
            'notes': 'The lift shaft frame (faces 1359 to 1368: GNecWal1).'},
           {'wall': 8, 'panels': [{'id': 'panel:cell_door', 'offset': 384, 'length': 130, 'height': 256,
                                   'surface': DR4R}],
            'notes': 'The cell door (face 1283, GNecDr4R 130 by 256, event 131).'}],
    platforms=[
        {'id': 'platform:button_high', 'at': [-1136, 1436], 'size': [24, 8], 'base': 160, 'rise': 24,
         'surface': CLG2, 'top_surface': CLG2, 'bottom_surface': CLG2,
         'notes': "The lift's call button on the upper floor (faces 1363 to 1367, 705 to 729)."},
        {'at': [-994, -240], 'size': [128, 32], 'rise': 112, 'top_slope': {'to': 192, 'toward': 'east'},
         'surface': BOOKS1, 'top_surface': BOOKS1,
         'notes': 'The bed (faces 1135 to 1212): its headboard, west half, rising from 657 at the side to 737 in the '
                  'middle (the original curves in four facets, T1books1).'},
        {'at': [-866, -240], 'size': [128, 32], 'rise': 112, 'top_slope': {'to': 192, 'toward': 'west'},
         'surface': BOOKS1, 'top_surface': BOOKS1, 'notes': 'The headboard, east half.'},
        {'at': [-930, -64], 'size': [256, 320], 'base': 32, 'rise': 16, 'surface': BEDS, 'top_surface': BEDS2,
         'bottom_surface': BOOKS1, 'notes': 'The bed frame, its side rails T1beds from 577 to 593.'},
        {'at': [-930, -64], 'size': [240, 320], 'base': 48, 'rise': 32, 'surface': BEDS2, 'top_surface': BEDS2,
         'notes': 'The mattress, 593 to 625.'},
        {'at': [-930, -188], 'size': [192, 56], 'base': 80, 'rise': 24, 'surface': BEDS2, 'top_surface': BEDS2,
         'notes': 'The pillow, 625 to 649 (rounded in the original).'},
        {'at': [-930, 108], 'size': [256, 24], 'rise': 64, 'surface': BEDS, 'top_surface': BEDS,
         'notes': 'The footboard, 545 to 609.'},
        {'at': [-1046, 108], 'size': [24, 24], 'base': 64, 'rise': 64, 'surface': BEDS, 'top_surface': BEDS,
         'notes': 'A knob of the footboard (to 673).'},
        {'at': [-814, 108], 'size': [24, 24], 'base': 64, 'rise': 64, 'surface': BEDS, 'top_surface': BEDS,
         'notes': 'A knob of the footboard (to 673).'},
    ] + shelf_unit('y', 256, 672, -320, -256, 'Rack (faces 1226 to 1254)'),
    notes='Sector 5: the floor over the hall, at 545 under a roof at 1057; the bed against the south wall, a rack '
          'against the east wall, the cell door in the west wall.'))
rooms.append(room(
    'room:lift', 'Lift shaft', [[-1120, 1440], [-736, 1440], [-736, 1632], [-1120, 1632]], 0, 1057, 'theme:shaft',
    notes='Sector 6: the shaft of the lift (door record 1), open to the hall below and the quarters above.'))
rooms.append(room(
    'room:west', 'West store', [[-2976, 256], [-1696, 256], [-1696, 1152], [-2336, 1152]], 0, 512, 'theme:lab',
    platforms=[
        {'id': 'platform:shelf_w', 'at': [-2016, 1120], 'size': [640, 64], 'rise': 256, 'surface': BOOKS,
         'end_surface': dict(TRIM9A, fit=False), 'top_surface': TRIM9A,
         'notes': 'The bookcase on the north wall (face 582 T1books, 583, 584 Trim9_32a; event 452).'},
    ] + shelf_unit('x', -2908, -2492, 256, 320, 'Rack (faces 614 to 642)')
      + shelf_unit('x', -2144, -1728, 256, 320, 'Rack (faces 585 to 613)'),
    notes='Sector 2.'))
rooms.append(room(
    'room:east', 'East store', [[-224, 256], [1056, 256], [416, 1152], [-224, 1152]], 0, 512, 'theme:lab',
    platforms=[
        {'id': 'platform:shelf_e', 'at': [96, 1120], 'size': [640, 64], 'rise': 256, 'surface': BOOKS,
         'end_surface': dict(TRIM9A, fit=False), 'top_surface': TRIM9A,
         'notes': 'The bookcase on the north wall (faces 674 to 676; event 453).'},
    ],
    notes='Sector 8.'))
rooms.append(room(
    'room:sw', 'South-west workroom', [[-2976, -1440], [-1888, -1440], [-1888, 160], [-2976, 160]], 0, 512,
    'theme:lab',
    platforms=[
        {'outline': [[-2976, -880], [-2712, -880], [-2712, -744], [-2840, -744], [-2840, -232], [-2712, -232],
                     [-2712, -104], [-2976, -104]],
         'rise': 88, 'surface': BEDS2, 'top_surface': BEDS2,
         'notes': 'The bench against the west wall, its body (faces 547 to 549, 557, 563, 566, 567: T1beds2 to 88).'},
        {'outline': [[-2976, -888], [-2704, -888], [-2704, -736], [-2832, -736], [-2832, -240], [-2704, -240],
                     [-2704, -96], [-2976, -96]],
         'base': 88, 'rise': 8, 'surface': BUTTS, 'top_surface': BEDS2, 'bottom_surface': BEDS2,
         'notes': 'Its top, 8 thick and standing 8 out over the body (T1butts edge 550 to 568, T1beds2 top at 96).'},
        {'id': 'platform:basin', 'outline': [[-2971, 0], [-2956, -15], [-2936, -20], [-2916, -15], [-2901, 0],
                                             [-2896, 20], [-2901, 40], [-2916, 55], [-2936, 60], [-2956, 55],
                                             [-2971, 40], [-2976, 20]],
         'rise': 80, 'surface': BUTT, 'top_surface': WATER,
         'notes': 'The basin in the north-west corner (faces 416 to 488, event 451): a bowl on a stem with water at 80 '
                  'and a Trim9_32a rim at 88; here one block to 80 with the water on top.'},
    ] + shelf_unit('y', -1288, -872, -1952, -1888, 'Rack (faces 496 to 524)')
      + shelf_unit('y', -472, -56, -1952, -1888, 'Rack (faces 489 to 517)'),
    notes='Sector 4.'))
rooms.append(room(
    'room:se', 'South-east laboratory', [[-32, -1504], [512, -2016], [1056, -1504], [1056, 160], [-32, 160]], 0,
    512, 'theme:lab',
    platforms=[
        {'outline': [[-32, -1000], [264, -1000], [264, -864], [104, -864], [104, -352], [232, -352], [232, -224],
                     [-32, -224]],
         'rise': 88, 'surface': BEDS2, 'top_surface': BEDS2,
         'notes': 'The laboratory bench against the west wall, its body (faces 188 to 191, 336, 1603 to 1607: '
                  'T1beds2 to 88).'},
        {'outline': [[-32, -1008], [272, -1008], [272, -856], [112, -856], [112, -360], [240, -360], [240, -216],
                     [-32, -216]],
         'base': 88, 'rise': 8, 'surface': BUTTS, 'top_surface': BEDS2, 'bottom_surface': BEDS2,
         'notes': 'Its top, 8 thick and 8 out over the body (T1butts edge 192 to 195, 330, 334, 337; top at 96).'},
        {'at': [192, -928], 'size': [88, 72], 'base': 96, 'rise': 6, 'surface': BASIN, 'top_surface': WATER,
         'notes': "The basin in the bench (faces 200 to 203, 1369 to 1373): water at 86 under a T01A01A rim that "
                  "rises to 102; here a slab of water from 96 to 102."},
        {'id': 'platform:shelf_se_w', 'outline': [[-32, -1504], [512, -2016], [512, -1892], [32, -1440]],
         'rise': 256, 'surface': BOOKS, 'top_surface': TRIM9,
         'notes': 'The bookcase on the south-west wall (faces 398, 402, 403; event 455).'},
        {'id': 'platform:shelf_se_e', 'outline': [[512, -2016], [1056, -1504], [992, -1440], [512, -1892]],
         'rise': 256, 'surface': BOOKS, 'top_surface': TRIM9,
         'notes': 'The bookcase on the south-east wall (faces 399 to 401; event 454).'},
    ] + [{'at': [x, y], 'size': [16, 16], 'base': 96, 'rise': 120, 'surface': BEDS2, 'top_surface': BEDS2,
          'notes': 'A post of the shelves on the bench (faces 207 to 330).'}
         for y in (-840, -680, -536, -376) for x in (0, 80)]
      + [{'at': [40, -608], 'size': [112, 496], 'base': 152, 'rise': 8, 'surface': BEDS2, 'top_surface': BEDS2,
          'bottom_surface': BEDS2, 'notes': 'The lower board of the shelves on the bench (152 to 160).'},
         {'at': [40, -608], 'size': [112, 496], 'base': 216, 'rise': 8, 'surface': BEDS2, 'top_surface': BEDS2,
          'bottom_surface': BEDS2, 'notes': 'The upper board (216 to 224).'}]
      + shelf_unit('y', -1256, -840, 992, 1056, 'Rack (faces 369 to 397)')
      + shelf_unit('y', -440, -24, 992, 1056, 'Rack (faces 340 to 368)'),
    notes='Sector 3: an arrow-ended room, bookcases along its two south walls.'))

# The square stair (sector 7): four flights of 16 per 32 round a solid core, three landings.
rooms.append(room('room:flight1', 'Stair, first flight', [[-2624, -1920], [-2240, -1920], [-2240, -1440],
                                                          [-2624, -1440]], -240, 256, 'theme:stair',
                  slope={'to': 0, 'toward': 'north', 'steps': 15, 'riser': STPV},
                  ceiling_slope={'to': 512, 'toward': 'north'},
                  notes='Treads -240 to -16, 32 deep (faces 1445 to 1473); the roof rakes 256 to 512 (face 1577).'))
rooms.append(room('room:land1', 'Stair, first landing', [[-2656, -2304], [-2240, -2304], [-2240, -1920],
                                                         [-2656, -1920]], -256, 256, 'theme:stair',
                  notes='Faces 1475, 1477 at -256, roof 1574 at 256.'))
rooms.append(room('room:flight2', 'Stair, second flight', [[-2976, -2304], [-2656, -2304], [-2656, -1920],
                                                           [-2976, -1920]], -416, 80, 'theme:stair',
                  slope={'to': -256, 'toward': 'east', 'steps': 10, 'riser': STPV},
                  ceiling_slope={'to': 240, 'toward': 'east'},
                  notes='Treads -416 to -272 (faces 1478 to 1496); the roof rakes from 80 (face 1580).'))
rooms.append(room('room:land2', 'Stair, second landing', [[-3360, -2304], [-2976, -2304], [-2976, -1888],
                                                          [-3360, -1888]], -432, 80, 'theme:stair',
                  notes='Faces 184, 1498 at -432, roof 1579 at 80.'))
rooms.append(room('room:flight3', 'Stair, third flight', [[-3360, -1888], [-2976, -1888], [-2976, -1568],
                                                          [-3360, -1568]], -592, -96, 'theme:stair',
                  slope={'to': -432, 'toward': 'south', 'steps': 10, 'riser': STPV},
                  ceiling_slope={'to': 64, 'toward': 'south'},
                  notes='Treads -592 to -448 (faces 1501 to 1519); the roof rakes -96 to 80 (face 1587).'))
rooms.append(room('room:land3', 'Stair, third landing', [[-3360, -1568], [-2944, -1568], [-2944, -1136],
                                                         [-3360, -1136]], -608, -96, 'theme:stair',
                  notes='Faces 1520, 1522 at -608, roof 1585 at -96.'))
rooms.append(room('room:flight4', 'Stair, fourth flight', [[-2944, -1568], [-2144, -1568], [-2144, -1136],
                                                           [-2944, -1136]], -1008, -512, 'theme:stair',
                  slope={'to': -608, 'toward': 'west', 'steps': 25, 'riser': STPV},
                  ceiling_slope={'to': -112, 'toward': 'west'},
                  notes='Treads -1008 to -624 (faces 1524 to 1572); the roof rakes -512 to -96 (face 1591).'))

CAVE = {
    'room:c9': ('Lower passage', [[-1600, -308], [-1600, -1136], [-2144, -1136], [-2144, -1568], [-1216, -1568],
                                  [-1216, -308]]),
    'room:c10': ('Long gallery', [[-2560, -1076], [-2176, -1076], [-2176, -308], [-1024, -308], [-1024, -1076],
                                  [-640, -1076], [-640, -692], [1856, -692], [1856, -1076], [2624, -1076],
                                  [2624, -692], [2240, -692], [2240, -308], [2624, -308], [2624, 76], [1664, 76],
                                  [1664, -308], [-640, -308], [-640, 76], [-2560, 76]]),
    'room:c11': ('North bend', [[1664, 652], [1664, 1228], [704, 1228], [704, -308], [1088, -308], [1088, 652]]),
    'room:c12': ('Dead end', [[1280, 268], [1664, 268], [1664, 652], [1280, 652]]),
    'room:c13': ('East chest room', [[4544, -500], [5696, -500], [5696, -116], [4544, -116]]),
    'room:c14': ('East gallery', [[3392, 460], [3392, 76], [5696, 76], [5696, -500], [6080, -500], [6080, 460]]),
    'room:c15': ('East bend', [[2624, -1076], [3776, -1076], [3776, 76], [3392, 76], [3392, -692], [2624, -692]]),
    'room:c16': ('South-east passage', [[3200, -3572], [3200, -3956], [4352, -3956], [4352, 76], [3968, 76],
                                        [3968, -3572]]),
    'room:c17': ('South caves', [[3760, -2036], [3376, -2036], [3376, -2228], [2816, -2228], [2816, -6068],
                                 [3776, -6068], [3776, -4724], [3200, -4724], [3200, -2612], [3760, -2612]]),
    'room:c18': ('South chest room', [[4544, -4340], [4928, -4340], [4928, -2804], [4352, -2804], [4352, -3188],
                                      [4544, -3188]]),
    'room:c19': ('North-east passage', [[2624, 1228], [2624, -308], [3008, -308], [3008, 1228]]),
    'room:c20': ('North-east bend', [[3008, 844], [3392, 844], [3392, 2380], [3008, 2380]]),
    'room:c21': ('Fire corridor', [[3008, 2380], [1088, 2380], [1088, 1996], [3008, 1996]]),
    'room:c22': ('North passage', [[128, 1228], [512, 1228], [512, 1996], [1088, 1996], [1088, 2380], [512, 2380],
                                   [512, 2956], [128, 2956]]),
    'room:c24': ('Passage to the cistern', [[-572, 852], [-572, 468], [512, 468], [512, 1228], [128, 1228],
                                            [128, 852]]),
    'room:c25': ('Hall of blades', [[-640, 3916], [-1024, 3916], [-1024, 3148], [128, 3148], [128, 2956],
                                    [512, 2956], [512, 3148], [896, 3148], [896, 3532], [-640, 3532]]),
    'room:c26': ('Ebonest cave', [[-64, 3532], [-64, 3724], [896, 3724], [896, 4108], [320, 4108], [320, 4684],
                                  [512, 4684], [512, 4876], [896, 4876], [896, 5644], [-1024, 5644], [-1024, 4684],
                                  [-832, 4684], [-832, 4300], [-64, 4300], [-64, 4108], [-448, 4108],
                                  [-448, 3532]]),
}
for rid, (name, outline) in CAVE.items():
    sector = rid.split(':c')[1]
    extra = {}
    if rid == 'room:c25':
        extra['walls'] = [
            {'wall': 7, 'panels': [{'offset': 154, 'length': 86, 'bottom': 158, 'height': 8, 'surface': SOLID}],
             'notes': 'The east blade slot (faces 1291 to 1295: a slot 86 wide, 8 high and 64 deep, T66flr2 inside, '
                      'solid01 at its back): here its back as a panel in the wall.'},
            {'wall': 1, 'panels': [{'offset': 528, 'length': 86, 'bottom': 158, 'height': 8, 'surface': SOLID}],
             'notes': 'The west blade slot (faces 1303 to 1307).'}]
    if rid == 'room:c21':
        extra['ceiling_levels'] = [
            {'outline': [[x - 1498 + cx, y] for x, y in [[1498, 2178], [1504, 2190], [1518, 2196], [1504, 2200],
                                                         [1498, 2212], [1492, 2200], [1478, 2196], [1492, 2190]]],
             'ceiling': -508, 'surface': SOLID, 'edge': T66,
             'notes': 'A fire vent in the roof (faces 1316 to 1326, 1377 to 1379): a star 40 by 34, 4 deep.'}
            for cx in (1498, 2552)]
    if rid == 'room:c17':
        extra['pillars'] = [{'outline': [[3200, -5684], [3392, -5684], [3392, -5108], [3200, -5108]],
                             'notes': 'The block in the south cave (sector 17, faces at x 3200 to 3392).'}]
    rooms.append(room(rid, name, outline, -1024, -512, 'theme:cave', notes=f'Sector {sector}.', **extra))

rooms.append(room('room:under', 'Cistern under the well', [[-1264, 372], [-572, 372], [-572, 1052], [-1264, 1052]],
                  -1024, -512, 'theme:under',
                  ceiling_levels=[{'outline': WELL_IN, 'ceiling': 0, 'surface': WATER, 'edge': GRAS,
                                   'notes': 'The well shaft up to the underside of the water (faces 155 to 166, '
                                            'Grastyl; the water face 7 seen from below).'}],
                  notes='The part of sector 1 at -1024: a cistern under the hall, its roof opening into the well.'))

openings = []


def opening(oid, frm, to, **kw):
    o = {'id': oid, 'from': frm, 'to': to}
    o.update(kw)
    openings.append(o)


opening('open:hall_west', 'room:hall', 'room:west', width=256, height=256, threshold=FLR,
        notes='Faces 153 (portal at x -1672) and the doorway of door records 51 and 52.')
opening('open:hall_east', 'room:hall', 'room:east', width=256, height=256, threshold=FLR,
        notes='Portal 672 and door records 53, 54.')
opening('open:west_sw', 'room:west', 'room:sw', width=256, height=256, along=0.588235294, threshold=FLR,
        notes='Portal 187 and door records 57, 58: x -2464 to -2208 through the 96 between the rooms.')
opening('open:east_se', 'room:east', 'room:se', width=256, height=256, along=0.382352941, threshold=FLR,
        notes='Portal 673 and door records 55, 56: x 256 to 512.')
opening('open:hall_lift', 'room:hall', 'room:lift', from_wall=5, to_wall=0, width='full', height='full',
        notes='Portal 1347.')
opening('open:upper_lift', 'room:upper', 'room:lift', from_wall=5, to_wall=0, width='full', height='full',
        notes='Portal 1348.')
opening('open:sw_flight1', 'room:sw', 'room:flight1', width='full', height='full', notes='Portal 1594.')
opening('open:flight1_land1', 'room:flight1', 'room:land1', width='full', height='full')
opening('open:land1_flight2', 'room:land1', 'room:flight2', width='full', height='full')
opening('open:flight2_land2', 'room:flight2', 'room:land2', width='full', height='full')
opening('open:land2_flight3', 'room:land2', 'room:flight3', width='full', height='full')
opening('open:flight3_land3', 'room:flight3', 'room:land3', width='full', height='full')
opening('open:land3_flight4', 'room:land3', 'room:flight4', width='full', height='full')
opening('open:flight4_c9', 'room:flight4', 'room:c9', width='full', height='full', notes='Portal 1595.')
for a, b, n in [('c9', 'c10', 707), ('c10', 'c11', 779), ('c11', 'c12', 801), ('c10', 'c15', 776),
                ('c10', 'c19', 778), ('c15', 'c14', 825), ('c14', 'c13', 812), ('c14', 'c16', 959),
                ('c16', 'c17', 936), ('c16', 'c18', 859), ('c19', 'c20', 973), ('c20', 'c21', 974),
                ('c21', 'c22', 996), ('c22', 'c24', 1026), ('c22', 'c25', 1032), ('c25', 'c26', 1063)]:
    walls = {'c9_c10': (5, 2), 'c25_c26': (8, 17), 'c16_c18': (2, 3), 'c16_c17': (0, 7), 'c14_c13': (2, 1),
             'c11_c12': (5, 2)}.get(f'{a}_{b}')
    kw = {'from_wall': walls[0], 'to_wall': walls[1]} if walls else {}
    opening(f'open:{a}_{b}', f'room:{a}', f'room:{b}', width='full', height='full', notes=f'Portal {n}.', **kw)
opening('open:c24_under', 'room:c24', 'room:under', width='full', height='full', notes='Portal 1285.')

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:lab', 'ambient': 22}, 'rooms': rooms,
             'openings': openings}


class Flow(yaml.SafeDumper):
    pass


def represent_list(dumper, data):
    flow = all(not isinstance(x, (dict, list)) for x in data) or all(
        isinstance(x, list) and all(not isinstance(y, (dict, list)) for y in x) for x in data)
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=flow)


Flow.add_representer(list, represent_list)


def dump(name, doc):
    (out / name).write_text(yaml.dump(doc, Dumper=Flow, sort_keys=False, width=1000, allow_unicode=True))


dump('rooms.yml', rooms_doc)

# ---------------------------------------------------------------- objects.yml
SECTOR_ROOM = {1: 'room:hall', 2: 'room:west', 3: 'room:se', 4: 'room:sw', 5: 'room:upper', 8: 'room:east'}


def cave_room(x, y):
    """The cave room an [x, y] at -1024 lies in (point in polygon)."""
    for rid, (_, poly) in CAVE.items():
        inside = False
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if inside:
            return rid
    if -1264 <= x <= -572 and 372 <= y <= 1052:
        return 'room:under'
    return None


def upper_room(x, y, z):
    if z >= 545:
        return 'room:upper'
    for rid, poly in [('room:hall', HALL), ('room:west', [[-2976, 256], [-1696, 256], [-1696, 1152], [-2336, 1152]]),
                      ('room:east', [[-224, 256], [1056, 256], [416, 1152], [-224, 1152]]),
                      ('room:sw', [[-2976, -1440], [-1888, -1440], [-1888, 160], [-2976, 160]]),
                      ('room:se', [[-32, -1504], [512, -2016], [1056, -1504], [1056, 160], [-32, 160]])]:
        inside = False
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if inside:
            return rid
    return None


def room_at(x, y, z):
    return cave_room(x, y) if z < -500 else upper_room(x, y, z)


objects = {'format': 0}
objects['start'] = {'room': 'room:hall', 'at': [-900, -127], 'facing': 90,
                    'notes': "Shadowspire's door event moves the party to (-900, -127, 1) facing north (520 of "
                             "2048); the map's own Party Start stands at (-896, -128)."}

doors = []
for did, op, kind, thick, note in [
        ('door:hall_west', 'open:hall_west', 'slide_left', 16, 'Door records 51 and 52 (event 61)'),
        ('door:hall_east', 'open:hall_east', 'slide_left', 16, 'Door records 53 and 54 (event 62)'),
        ('door:east_se', 'open:east_se', 'slide_left', 80, 'Door records 55 and 56 (event 63)'),
        ('door:west_sw', 'open:west_sw', 'slide_left', 80, 'Door records 57 and 58 (event 64)')]:
    doors.append({'id': did, 'opening': op, 'kind': kind, 'leaves': 2, 'fold': True, 'state': 'closed',
                  'thickness': thick, 'speed': 100, 'surface': WAL2, 'tile': True,
                  'notes': f'{note}: two GNecWal2 leaves 128 wide and {thick} thick that part in the middle and fold '
                           f'124 against the jambs at 100 a second, closed at the start (state 2 in the scene).'})
objects['doors'] = doors

objects['movers'] = [{
    'id': 'mover:lift', 'room': 'room:lift', 'at': [-928, 1538], 'size': [384, 188], 'bottom': 16, 'height': 16,
    'travel': [0, 0, 513], 'speed': 50, 'surface': CLG2, 'top_surface': CLG2,
    'notes': 'Door record 1: the lift, a slab 16 thick from 16 to 32 over the shaft floor (faces 128, 129, 154), '
             'rising 513 to the quarters floor at 545, speed 50; down at the start (state 0).'}]

LIGHTS = [(-936, 1248, 8, 512, 255), (-1440, 704, 8, 512, 255), (-448, 712, 8, 512, 255), (-1224, 136, 8, 512, 255),
          (-656, 136, 8, 512, 255), (-936, 264, 8, 512, 255), (-1440, 704, 553, 512, 255),
          (-936, 1248, 553, 512, 255), (-448, 712, 553, 512, 255), (-656, 136, 553, 512, 255),
          (-936, 264, 553, 512, 255), (-1224, 136, 553, 512, 255), (832, -168, 8, 256, 192),
          (824, -952, 8, 256, 192), (388, -504, 8, 256, 192), (172, 88, 8, 256, 192), (180, -1128, 8, 256, 192),
          (-2100, -248, 8, 512, 255), (-2356, -536, 8, 512, 255), (-2088, -1080, 8, 512, 255),
          (-2780, -988, 8, 512, 255), (-2792, 40, 8, 512, 255)]
lights = []
for i, (x, y, z, r, c) in enumerate(LIGHTS):
    rid = room_at(x, y, z)
    floor = 545 if rid == 'room:upper' else 0
    lights.append({'id': f'light:l{i:02d}', 'room': rid, 'at': [x, y], 'height': z - floor, 'radius': r,
                   'color': [c, c, c], 'brightness': 31, 'notes': f'Light record {i}.'})
objects['lights'] = lights

CHESTS = [('chest:c1', 'room:c26', [864, 5380], 'n', [613, 628, 628], [3, 4], 82),
          ('chest:c2', 'room:c26', [864, 5196], 'n', [628, 'ebonest', 628], [3, 5], 83),
          ('chest:c3', 'room:c13', [4576, -308], 's', [628, 628], [3, 4], 84),
          ('chest:c4', 'room:c18', [4736, -4308], 'e', [628], [4, 5, 5, 5, 5, 5], 85)]
objects['chests'] = [{'id': cid, 'room': rid, 'at': at, 'facing': f, 'kind': 'gt002', 'items': items,
                      'random_levels': lv, 'trap_level': 6,
                      'notes': f'Chest record {cid[-1]} (event {ev}): the MM8 chest gt002 (96 by 64, 80 high, '
                               f'faces of event {ev}), trapped (flags 1); contents as the scene holds them.'}
                     for cid, rid, at, f, items, lv, ev in CHESTS]

SPAWNS = [(-2288, -192, 0, 1), (-2272, -944, 0, 1), (648, -200, 0, 2), (544, -1224, 0, 2), (-544, 728, 545, 2),
          (-1312, 256, 545, 2), (-2088, 672, 0, 1), (-1400, 512, 0, 1), (-456, 464, 0, 2), (-704, 5360, -1024, 1),
          (-216, 5384, -1024, 2), (-408, 4960, -1024, 2), (328, 2584, -1024, 1), (-224, 608, -1024, 2),
          (1128, 848, -1024, 2), (-2368, -304, -1024, 2), (3400, -2496, -1024, 2), (3544, -5296, -1024, 1),
          (4720, -3856, -1024, 1), (4984, -320, -1024, 1), (4096, 264, -1024, 2), (3195, 1952, -1024, 3),
          (5384, 148, -1024, 3), (2955, -3699, -1024, 3), (44, 5103, -1024, 3), (357, 1712, -1024, 3)]
objects['spawns'] = [{'id': f'spawn:s{i:02d}', 'room': room_at(x, y, z), 'at': [x, y], 'slot': s, 'radius': 32,
                      'group': 10, 'notes': f'Spawn record {i}: slot {s}, group 10.'}
                     for i, (x, y, z, s) in enumerate(SPAWNS)]

ITEMS = [(185, -1930, 286, 144), (220, -1818, 294, 64), (220, -2842, 294, 64), (220, -2730, 286, 144),
         (209, -1924, -148, 64), (211, -1920, -272, 64), (212, -1920, -376, 64), (213, -1924, -148, 144),
         (214, -1920, -272, 144), (215, -1920, -376, 144), (217, -1924, -148, 224), (220, -1920, -272, 224),
         (220, -1920, -376, 224), (217, -1924, -1188, 224), (220, -1920, -1064, 224), (220, -1920, -960, 224),
         (215, -1920, -960, 144), (214, -1920, -1064, 144), (213, -1924, -1188, 144), (209, -1924, -1188, 64),
         (211, -1920, -1064, 64), (212, -1920, -960, 64), (220, 1032, -1096, 224), (220, 1028, -972, 224),
         (220, 1028, -868, 224), (216, 1028, -868, 144), (216, 1028, -972, 144), (216, 1032, -1096, 144),
         (209, 1032, -1096, 64), (211, 1028, -972, 64), (212, 1028, -868, 64), (239, 1032, -56, 64),
         (239, 1028, -180, 64), (239, 1028, -284, 64), (251, 1032, -56, 144), (251, 1028, -180, 144),
         (251, 1028, -284, 144), (220, 1032, -56, 224), (220, 1028, -180, 224), (220, 1028, -284, 224),
         (233, -288, 564, 769), (241, -288, 460, 689), (234, -288, 460, 769), (235, -292, 336, 769),
         (264, -292, 336, 689), (241, -292, 336, 609), (241, -288, 564, 609), (241, -288, 460, 609),
         (236, -288, 564, 689)]
objects['items'] = [{'id': f'item:i{i:02d}', 'room': room_at(x, y, z), 'item': it, 'at': [x, y], 'floor_height': z,
                     'notes': f'Sprite object {i}: item {it} on a rack at {z}.'}
                    for i, (it, x, y, z) in enumerate(ITEMS)]

DECOS = [(-1656, 864, 256), (-1656, 544, 256), (-264, 544, 256), (-264, 864, 256), (-1136, 1432, 256),
         (-720, 1432, 256), (-720, 1432, 801), (-1136, 1432, 801), (-720, -248, 801), (-1136, -248, 801),
         (-1136, -248, 256), (-720, -248, 256), (-1656, 864, 801), (-1656, 544, 801), (-264, 864, 801)]
BONES = [(-2058, 286, 64), (-1834, 286, 144), (-2034, 286, 224), (-2602, 286, 64), (-2826, 286, 144),
         (-2626, 286, 224)]
DECOS2 = [(-20, -868, 256), (-20, -220, 256), (1044, -568, 256), (-2964, -160, 256), (-2964, -808, 256),
          (-1900, -672, 256)]
decos = []
for i, (x, y, z) in enumerate(DECOS + DECOS2):
    rid = room_at(x, y, z)
    floor = 545 if rid == 'room:upper' else 0
    decos.append({'id': f'deco:torch_{i:02d}', 'room': rid, 'decoration': 'dec56', 'at': [x, y],
                  'height': z - floor, 'notes': 'A wall torch (dec56) as the original places it, 8 off the wall.'})
for i, (x, y, z) in enumerate(BONES):
    decos.append({'id': f'deco:bones_{i}', 'room': 'room:west', 'decoration': 'dec29', 'at': [x, y],
                  'floor_height': z, 'notes': 'Bones (dec29) on a rack shelf.'})
objects['decorations'] = decos

WELL_PLATE = WELL_IN
objects['plates'] = [
    {'id': 'plate:well_water', 'room': 'room:hall', 'outline': WELL_PLATE, 'surface': WATER,
     'notes': 'The water inside the well kerb (face 7, WtrTyl at 0, fluid).'},
    {'id': 'plate:blades', 'room': 'room:c25', 'outline': [[-424, 3264], [-92, 3264], [-92, 3422], [-424, 3422]],
     'notes': 'Face 1286 (C1FL, event 102): stepping on it throws the blades across the hall.'},
    {'id': 'plate:fire_w', 'room': 'room:c21', 'outline': [[1302, 2106], [1676, 2106], [1676, 2274], [1302, 2274]],
     'notes': 'Face 1310 (event 103).'},
    {'id': 'plate:fire_e', 'room': 'room:c21', 'outline': [[2356, 2106], [2730, 2106], [2730, 2274], [2356, 2274]],
     'notes': 'Face 1309 (event 103).'}]
objects['floors'] = [{'id': 'floor:well', 'of': 'plate:well_water', 'kind': 'water'}]
objects['exits'] = [
    {'id': 'exit:front_l', 'room': 'room:hall', 'at': [-992, -256], 'size': [128, 256], 'surface': DR4R,
     'to': 'exit:front', 'notes': 'The west half of the front door (face 5, GNecDr4R; event 501).'},
    {'id': 'exit:front_r', 'room': 'room:hall', 'at': [-864, -256], 'size': [128, 256], 'surface': DR4L,
     'to': 'exit:front', 'notes': 'The east half (face 52, GNecDr4L; event 501).'}]
dump('objects.yml', objects)

# ---------------------------------------------------------------- wiring.yml
SHELF_W = """if not IsAtLeast(MapVar(shelf_w), 3) then
  local r = PickRandomOption(452, 2, {3, 5, 7, 9, 11, 14})
  if r == 3 then evt.GiveItem(5, ItemType.Scroll_, 368)
  elseif r == 5 then evt.GiveItem(5, ItemType.Scroll_, 357)
  elseif r == 7 then evt.GiveItem(5, ItemType.Scroll_, 346)
  elseif r == 9 then evt.GiveItem(5, ItemType.Scroll_, 335)
  elseif r == 11 then evt.GiveItem(5, ItemType.Scroll_, 302)
  end
end
AddValue(MapVar(shelf_w), 1)"""
SHELF_E = """if not IsAtLeast(MapVar(shelf_e), 3) then
  local r = PickRandomOption(453, 2, {3, 5, 7, 9, 11, 14})
  if r == 3 then evt.GiveItem(5, ItemType.Scroll_, 334)
  elseif r == 5 then evt.GiveItem(5, ItemType.Scroll_, 355)
  elseif r == 7 then evt.GiveItem(5, ItemType.Scroll_, 356)
  elseif r == 9 then evt.GiveItem(5, ItemType.Scroll_, 357)
  elseif r == 11 then evt.GiveItem(5, ItemType.Scroll_, 367)
  end
end
AddValue(MapVar(shelf_e), 1)"""
SHELF_SE_E = """if not IsAtLeast(MapVar(shelf_se_e), 1) then
  local r = PickRandomOption(454, 2, {3, 5, 7, 9, 11, 14})
  if r == 3 then AddValue(InventoryItem(424), 424)
  elseif r == 5 then AddValue(InventoryItem(435), 435)
  elseif r == 7 then AddValue(InventoryItem(446), 446)
  elseif r == 9 then AddValue(InventoryItem(457), 457)
  elseif r == 11 then AddValue(InventoryItem(468), 468)
  end
end
AddValue(MapVar(shelf_se_e), 1)"""
SHELF_SE_W = """if not IsAtLeast(MapVar(shelf_se_w), 1) then
  local r = PickRandomOption(455, 2, {3, 5, 7, 9, 11, 14})
  if r == 3 then AddValue(InventoryItem(401), 401)
  elseif r == 5 then AddValue(InventoryItem(412), 412)
  elseif r == 7 then AddValue(InventoryItem(411), 411)
  elseif r == 9 then AddValue(InventoryItem(423), 423)
  elseif r == 11 then AddValue(InventoryItem(434), 434)
  end
end
AddValue(MapVar(shelf_se_w), 1)"""

events = [
    {'id': 'evt:load_hostile', 'preset': 'script', 'trigger': 'load',
     'lua': 'evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)',
     'notes': 'Original event 5 (on load): every monster of the lab (group 10) hostile.'},
    {'id': 'evt:leave_ebonest', 'preset': 'script', 'trigger': 'leave', 'condition': {'item': 'ebonest'},
     'effects': [{'qbit': 'ebonest_lost'}],
     'notes': 'Original event 6 (on leave): with Ebonest in the packs, quest bit 199.'},
    {'id': 'evt:leave_blazen', 'preset': 'script', 'trigger': 'leave', 'condition': {'qbit': 'blazen_found'},
     'effects': [{'hide_actors': 10}],
     'notes': "Original event 10 (on leave): once Blazen is found (quest bit 71) the lab's monsters are hidden."},
    {'id': 'evt:lift', 'preset': 'switch', 'source': 'mover:lift', 'title': 'Door', 'toggles': ['mover:lift'],
     'notes': "Original event 11, on the lift's top: door record 1 toggles."},
    {'id': 'evt:button_low', 'preset': 'switch', 'source': 'platform:button_low', 'title': 'Button',
     'toggles': ['mover:lift'], 'notes': 'Original event 12: door records 2 (the button, which does not move) and 1.'},
    {'id': 'evt:button_high', 'preset': 'switch', 'source': 'platform:button_high', 'title': 'Button',
     'toggles': ['mover:lift'], 'notes': 'Original event 13: door records 3 (no faces) and 1.'},
    {'id': 'evt:door_hall_west', 'preset': 'door', 'source': 'door:hall_west', 'action': 'open', 'title': 'Door',
     'notes': 'Original event 61.'},
    {'id': 'evt:door_hall_east', 'preset': 'door', 'source': 'door:hall_east', 'action': 'open', 'title': 'Door',
     'notes': 'Original event 62.'},
    {'id': 'evt:door_east_se', 'preset': 'door', 'source': 'door:east_se', 'action': 'open', 'title': 'Door',
     'notes': 'Original event 63.'},
    {'id': 'evt:door_west_sw', 'preset': 'door', 'source': 'door:west_sw', 'action': 'open', 'title': 'Door',
     'notes': 'Original event 64.'},
] + [{'id': f'evt:{cid[6:]}', 'preset': 'chest', 'source': cid, 'title': 'Chest',
      'notes': f'Original event {ev}: OpenChest({cid[-1]}).'} for cid, _, _, _, _, _, ev in CHESTS] + [
    {'id': 'evt:blades', 'preset': 'script', 'trigger': 'step', 'source': 'plate:blades',
     'effects': [{'cast': {'spell': 39, 'from': [-1018, 3344, -862], 'to': [890, 3344, -862],
                           'mastery': 'grandmaster', 'level': 20}},
                 {'cast': {'spell': 39, 'from': [890, 3344, -862], 'to': [-1018, 3344, -862],
                           'mastery': 'grandmaster', 'level': 20}}],
     'notes': 'Original event 102 (face 1286): Blades from each wall slot across the hall.'},
    {'id': 'evt:fireballs', 'preset': 'script', 'trigger': 'step', 'source': 'plate:fire_w',
     'sources': ['plate:fire_e'],
     'effects': [{'cast': {'spell': 6, 'from': [1498, 2195, -560], 'to': [1498, 2195, -1024],
                           'mastery': 'grandmaster', 'level': 20}},
                 {'cast': {'spell': 6, 'from': [2552, 2195, -560], 'to': [2552, 2195, -1024],
                           'mastery': 'grandmaster', 'level': 20}}],
     'notes': 'Original event 103 (faces 1309, 1310): a Fireball down from each of the two vents in the roof.'},
    {'id': 'evt:blazen', 'preset': 'script', 'source': 'panel:cell_door',
     'condition': {'not': {'qbit': 'blazen_in_party'}}, 'lua': 'evt.SpeakNPC(107)',
     'else_effects': [{'lua': 'evt.FaceAnimation(FaceAnimation.DoorLocked)'}],
     'notes': "Original event 131 (face 1283, no hover name): Blazen Stormlance speaks through the cell door, unless "
              "he is in the party (quest bit 435)."},
] + [{'id': f'evt:drink_{n}', 'preset': 'text', 'source': src, 'title': 'Take a Drink', 'text': 'Refreshing !',
      'notes': f'Original event 451 ({w}).'}
     for n, src, w in [('well_s', 'platform:kerb_s', 'the well kerb, south half'),
                       ('well_n', 'platform:kerb_n', 'the well kerb, north half'),
                       ('basin', 'platform:basin', 'the basin in the south-west workroom')]] + [
    {'id': 'evt:shelf_w', 'preset': 'script', 'source': 'platform:shelf_w', 'title': 'Bookshelf', 'lua': SHELF_W,
     'notes': 'Original event 452: three tries at a scroll (one of six: five scrolls or nothing).'},
    {'id': 'evt:shelf_e', 'preset': 'script', 'source': 'platform:shelf_e', 'title': 'Bookshelf', 'lua': SHELF_E,
     'notes': 'Original event 453.'},
    {'id': 'evt:shelf_se_e', 'preset': 'script', 'source': 'platform:shelf_se_e', 'title': 'Bookshelf',
     'lua': SHELF_SE_E, 'notes': 'Original event 454: one try at a book (one of six).'},
    {'id': 'evt:shelf_se_w', 'preset': 'script', 'source': 'platform:shelf_se_w', 'title': 'Bookshelf',
     'lua': SHELF_SE_W, 'notes': 'Original event 455.'},
    {'id': 'evt:exit_l', 'preset': 'exit', 'source': 'exit:front_l', 'title': "Leave the Mad Necromancer's Lab",
     'notes': 'Original event 501, left leaf.'},
    {'id': 'evt:exit_r', 'preset': 'exit', 'source': 'exit:front_r', 'title': "Leave the Mad Necromancer's Lab",
     'notes': 'Original event 501, right leaf.'},
]
dump('wiring.yml', {'format': 0, 'variables': ['shelf_w', 'shelf_e', 'shelf_se_e', 'shelf_se_w'],
                    'events': events})
