#!/usr/bin/env python3
"""XD-02 second pass, step 1: bigger main rooms (adit mouth, Top Station, sorting floor, chapel, tally room) with
their contents moved with them, and the build's and audit's findings the project causes. Run once on the project as
it stood after the generated-texture pass (pass2_backup/); its whole diff was read. Not to be run again."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math
import sys

sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio

L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
O = yio.load(L + 'objects.yml')
W = yio.load(L + 'wiring.yml')


def room(rid):
    return next(r for r in R['rooms'] if r['id'] == rid)


def obj(col, oid):
    return next(o for o in O[col] if o['id'] == oid)


def evt(eid):
    return next(e for e in W['events'] if e['id'] == eid)


def in_room(col, rid):
    return [o for o in O.get(col, []) if o.get('room') == rid]


def r2(v):
    return int(round(v))


# ---------------------------------------------------------------- adit mouth: 1024 x 768 -> 1280 x 1280
a = room('room:adit_mouth')
a['outline'] = [[13312, 2752], [14592, 2752], [14592, 4032], [13312, 4032]]
sx = lambda x: r2(13312 + (x - 13312) * 1.25)
for p in a['platforms']:
    if 'at' in p and p['size'] == [32, 32]:
        p['at'] = [sx(p['at'][0]), 2768 if p['at'][1] < 3392 else 4016]
    elif 'at' in p and p['size'] == [48, 48]:
        p['at'] = [14560, p['at'][1]]
    elif p.get('notes', '').startswith('An ore cart'):
        p['outline'] = [[x, y + 256] for x, y in p['outline']]
    elif p.get('rise') == 48:
        p['outline'] = [[x, y + 256] for x, y in p['outline']]
    elif p.get('rise') == 6:
        p['outline'] = [[x if x < 14000 else 14556, y] for x, y in p['outline']]
for b in a['beams']:
    x = b['path'][0][0]
    nx = 14560 if x == 14304 else sx(x)
    b['path'] = [[nx, 2752], [nx, 4032]]
a['walls'][0]['panels'][0].update({'offset': 176, 'length': 256, 'bottom': 160, 'height': 128})
a['notes'] = ("The timbered portal hall, 1280 square: daylight through the east wall (the X1 exit face, sky behind it), "
              "three timber sets of dark posts and cap beams under plank lagging, rails from the party's feet west to "
              "the drift, an ore cart tipped against the north wall. Level (L3's 64 fall is in the haul drift).")
O['start']['at'] = [14376, 3392]
for d in in_room('decorations', 'room:adit_mouth'):
    if d['id'] == 'deco:adit_mouth_1':
        d['along'] = 0.3
    elif d['id'] == 'deco:adit_mouth_2':
        d['at'] = [13400, 3780]
    elif d['id'] == 'deco:adit_mouth_3':
        d['at'] = [13470, 3700]
    elif d['id'] == 'deco:adit_mouth_4':
        d['at'] = [14340, 2880]
    elif d['id'] == 'deco:adit_mouth_5':
        d['at'] = [13900, 3960]
obj('lights', 'light:portal_day')['at'] = [14506, 3392]

# ---------------------------------------------------------------- Top Station: 1280 x 896 -> 1664 x 896 (east)
t = room('room:top_station')
t['outline'] = [[11712, 4736], [13376, 4736], [13376, 5632], [11712, 5632]]
t['platforms'][7:7] = [
    {'at': [13248, 4752], 'size': [32, 32], 'rise': 448, 'surface': {'texture': 't3d2abs', 'size': [32, 256]}},
    {'at': [13248, 5616], 'size': [32, 32], 'rise': 448, 'surface': {'texture': 't3d2abs', 'size': [32, 256]}},
]
t['beams'].append({'path': [[13248, 4736], [13248, 5632]], 'width': 32, 'depth': 40, 'bottom': 256,
                   'surface': {'texture': 't3d2abe', 'size': [256, 32]}})
t['notes'] = ("Rock hall 1664 by 896, 512 high, its plank roof on four cap beams; the loading platform (32) along the "
              "west wall, the trestle gate in that wall (the car waits beyond it). Doors to the lamp room (south) and "
              "the foot drift (north-west); open to the haul drift (south) and the sorting floor (north-east).")
for d in in_room('decorations', 'room:top_station'):
    if d['id'] in ('deco:top_station_14', 'deco:top_station_15', 'deco:top_station_16'):
        d['at'] = [d['at'][0] + 384, d['at'][1]]
    elif d['id'] == 'deco:top_station_11':
        d['along'] = round((11866 - 11712) / 1664, 3)
    elif d['id'] == 'deco:top_station_12':
        d['along'] = round((13376 - 12416) / 1664, 3)

# ---------------------------------------------------------------- sorting floor: 192 further north
s = room('room:sorting_floor')
s['outline'] = [[12160, 5696], [13568, 5696], [13568, 6912], [12616, 6912]]
for p in s['platforms']:
    if 'outline' in p:
        p['outline'] = [[x, y + 192] for x, y in p['outline']]
s['beams'][0]['path'] = [[12616, 6896], [13568, 6896]]
s['beams'][1]['path'] = [[12864, 5696], [12864, 6912]]
s['beams'][2]['path'] = [[13056, 5696], [13056, 6912]]
s['notes'] = ("Trapezoid hall 1408 by 1216, 768 high; three ore chutes open as dark square shafts 384 up its north "
              "wall; two sorting tables under two lanterns hung from beams; a gold vein on the slanted west wall; the "
              "old chalk-marked east wall hides the strongroom.")
for c in ('room:chute_1', 'room:chute_2', 'room:chute_3'):
    room(c)['outline'] = [[x, y + 192] for x, y in room(c)['outline']]
obj('spawns', 'spawn:chute_2')['at'][1] += 192
obj('spawns', 'spawn:ore_heap_item')['at'][1] += 192
for did in ('deco:sorting_floor_29', 'deco:sorting_floor_30'):
    obj('decorations', did)['at'][1] += 192
for did in ('deco:sorting_floor_27', 'deco:sorting_floor_28'):
    d = obj('decorations', did)
    d['height'] = 386  # the lantern's top (88 tall) 2 into the beam's underside at 280
for lid in ('light:sorting_lamp_1', 'light:sorting_lamp_2'):
    obj('lights', lid)['height'] = 420
obj('lights', 'light:glint_sorting')['at'] = [12444, 6283]

# ---------------------------------------------------------------- chapel: x 1.1, y 1.25 about its door, 64 east
CX, CY = 8512, 3776


def ct(x, y):
    return [r2(CX + (x - CX) * 1.1 + 64), r2(CY + (y - CY) * 1.25)]


DX, DY = 64, -160  # the pool's centre (8512, 3136) -> (8576, 2976)
c = room('room:dwarf_shrine')
c['outline'] = [ct(x, y) for x, y in c['outline']]
c['ceiling'] = 128
for p in c['pillars']:
    p['at'] = ct(*p['at'])
for p in c['platforms']:
    if 'outline' in p:
        p['outline'] = [[x + DX, y + DY] for x, y in p['outline']]
south = CY - 1280 * 1.25  # 2176
for p in c['platforms']:
    if 'at' in p:
        p['at'] = [p['at'][0] + 64, r2(south + (p['at'][1] - 2496))]
for lv in c['levels']:
    lv['outline'] = [[x + DX, y + DY] for x, y in lv['outline']]
for cl in c['ceiling_levels']:
    cl['outline'] = [[x + DX, y + DY] for x, y in cl['outline']]
    cl['ceiling'] = 416
for pa in c['parapets']:
    pa['path'] = [[x + DX, y + DY] for x, y in pa['path']]
c['notes'] = ("Octagon 1408 by 1600, 576 high to its flat ring, a stone lantern over the pool rising to 864; eight "
              "dressed pillars on a ring round the pool; the green pool sunk 32 in the middle behind a kerb (its water "
              "a platform 4 under the floor, clicked); the tablet against the south wall facing the door.")
for d in in_room('decorations', 'room:dwarf_shrine'):
    if d['decoration'] == 'brzier00':
        d['at'] = [d['at'][0] + 64, 2300]
    else:
        d['at'] = ct(*d['at'])
obj('lights', 'light:green_pool')['at'] = [8576, 2976]

# ---------------------------------------------------------------- tally room: 1.6 about its door wall
TX, TY, TS = 6528, 7200, 1.6


def tt(x, y):
    return [r2(TX + (x - TX) * TS), r2(TY + (y - TY) * TS)]


ta = room('room:tally_room')
ta['outline'] = [tt(x, y) for x, y in ta['outline']]
ta['ceiling'] = 288
for w in ta['walls']:
    w['panels'][0]['length'] = 512
ta['platforms'][0]['at'] = [5600, 7200]
ta['notes'] = ("Hexagon 1434 across the flats, 576 high; the clan's tallies of stolen ore chalked on slabs on four "
               "walls; the tallymaster's table facing the door, the tallymaster behind it, the strongbox behind him "
               "against the west wall.")
obj('decorations', 'deco:tally_room_70')['at'] = [5600, 7200]
obj('chests', 'chest:strongbox')['at'] = [5180, 7200]
obj('monsters', 'monster:tallymaster')['at'] = [5360, 7200]
for mid in ('monster:tally_guard_1', 'monster:tally_guard_2', 'monster:tally_guard_3'):
    m = obj('monsters', mid)
    m['at'] = tt(*m['at'])
O['decorations'].insert(O['decorations'].index(obj('decorations', 'deco:tally_room_71')) + 1,
                        {'id': 'deco:tally_room_72', 'room': 'room:tally_room', 'decoration': 'torch02', 'wall': 1,
                         'along': 0.1, 'height': 240})
O['decorations'].insert(O['decorations'].index(obj('decorations', 'deco:tally_room_72')) + 1,
                        {'id': 'deco:tally_room_73', 'room': 'room:tally_room', 'decoration': 'torch02', 'wall': 5,
                         'along': 0.9, 'height': 240})

yio.save(L + 'rooms.yml', R)
yio.save(L + 'objects.yml', O)
yio.save(L + 'wiring.yml', W)
print('edited')
