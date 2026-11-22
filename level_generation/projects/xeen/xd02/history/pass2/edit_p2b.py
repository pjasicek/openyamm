#!/usr/bin/env python3
"""XD-02 second pass, step 2 (after edit_p2.py): the Deep Line station made a hall, and the build's and audit's
findings the project causes (faces in one plane, things floating or inside each other, squashed pictures), chests of
the shipped kinds named Chest, levers of the shipped form. Run once; its whole diff was read. Not to be run again."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
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


def insert_after(col, after_id, item):
    lst = O[col]
    lst.insert(lst.index(obj(col, after_id)) + 1, item)


TIMBER = {'texture': 't3d2abe', 'size': [256, 32]}
POST = {'texture': 't3d2abs', 'size': [32, 256]}
IRON = {'texture': 'xnrustirn', 'size': [64, 64]}

# ---------------------------------------------------------------- Deep Line station: a marshalling hall
d = room('room:deep_station')
d['outline'] = [[4422, 4214], [4874, 4666], [4682, 4896], [3968, 4896], [3776, 4608], [3840, 4288], [3648, 3760],
                [3776, 3216], [4320, 3040], [4776, 3296], [4840, 3860]]
d['notes'] = ("Rock-cut station 1230 by 1860, 448 high: rails run west along its north side to the buffer stop before "
              "the Deep Line's mouth (the XD-03 exit face behind it), the chained cart on them, the brake lever on the "
              "north wall; south of the rails the old marshalling bay with a spur of rails, a cart and spoil.")
d['platforms'] += [
    {'rise': 6, 'surface': IRON, 'top_surface': IRON,
     'outline': [[4000, 3420], [4010, 3420], [4380, 4330], [4370, 4330]], 'notes': 'Spur rail into the bay'},
    {'rise': 6, 'surface': IRON, 'top_surface': IRON,
     'outline': [[4104, 3378], [4114, 3378], [4484, 4288], [4474, 4288]], 'notes': 'Spur rail into the bay'},
    {'rise': 0, 'surface': {'texture': 'crdrf1', 'size': [128, 128]}, 'top_surface': {'texture': 'crdrf1', 'size': [128, 128]},
     'outline': [[4380, 3200], [4640, 3330], [4700, 3560], [4520, 3600], [4330, 3420]], 'top_heights': [24, 40, 64, 48, 32],
     'notes': 'Spoil heap in the bay'},
]
O['lights'].append({'id': 'light:station_bay', 'room': 'room:deep_station', 'at': [4200, 3640], 'height': 220,
                    'radius': 760, 'color': [255, 160, 80], 'pulse': {'intensity': [0.8, 1], 'frequency': 0.9},
                    'notes': 'A lantern on a prop in the marshalling bay.'})
O['decorations'] += [
    {'id': 'deco:deep_station_117', 'room': 'room:deep_station', 'decoration': 'torch02', 'wall': 7, 'along': 0.5,
     'height': 224},
    {'id': 'deco:deep_station_118', 'room': 'room:deep_station', 'decoration': 'bigbarel', 'at': [3820, 3380]},
    {'id': 'deco:deep_station_119', 'room': 'room:deep_station', 'decoration': 'smlbarel', 'at': [3900, 3320]},
    {'id': 'deco:deep_station_120', 'room': 'room:deep_station', 'decoration': '7dec10', 'at': [4650, 3800]},
]
O['spawns'].insert(O['spawns'].index(obj('spawns', 'spawn:deep_station')) + 1,
                   {'id': 'spawn:deep_station_bay', 'room': 'room:deep_station', 'at': [4150, 3550], 'slot': 2,
                    'tier': 'a', 'notes': 'Spiders in the dark bay.'})

# ---------------------------------------------------------------- faces in one plane
ch = room('room:chasm')
for p in ch['platforms']:
    if p.get('notes') == 'Trestle leg':
        p['rise'] -= 2  # the leg's top inside its cap beam, not level with the cap's top
for b in ch['beams']:
    if b['path'][0][1] == 5052 and b['path'][1][1] == 5316:
        b['path'] = [[b['path'][0][0], 5048], [b['path'][1][0], 5320]]  # caps and ties stand past the legs' faces

ca = room('room:collapsed_adit')
for p in ca['platforms']:
    if p.get('id') == 'platform:winch':
        p['at'] = [2888, 5344]
    elif p.get('notes') == 'Winch frame':
        p['at'] = [p['at'][0] + 8, p['at'][1]]
fall = obj('movers', 'mover:fall')
fall['parts'][3]['at'] = [2830, 5220]  # the second prop clear of the boulder's foot
fall['parts'][4]['height'] = 32  # the brace's top above the props' tops

fw = room('room:flooded_working')
fw['platforms'][1]['at'] = [11784, 1408]
fw['platforms'][1]['size'] = [1616, 128]  # meets the north walkway instead of lying over it

lr = room('room:lamp_room')
lr['platforms'][0]['outline'] = [[12400, 3904], [12480, 3904], [12480, 4544], [12400, 4544]]  # the shelf on the wall
for p in lr['platforms'][1:]:
    p['rise'] = 120  # the posts under the shelf, not through it

md = room('room:main_drift')
for p in md['platforms']:
    if p['at'][1] in (3760, 4120, 4480) or p['at'][0] == 13040:
        p['size'] = [36, 36]  # posts a little wider than the cap beam on them

st = room('room:stope_floor')
for b in st['beams']:
    if b.get('notes') == "Rail across the rim ledge's open north end":
        b['bottom'] = -326

# ---------------------------------------------------------------- wall torches of the spiral stand on their ledges
for n in (84, 85, 86, 87, 88):
    dd = obj('decorations', f'deco:stope_floor_{n}')
    dd.pop('floor_height', None)

# ---------------------------------------------------------------- the lamp room's lamps over the rack (east wall)
for i, n in enumerate((20, 21, 22, 23, 24)):
    dd = obj('decorations', f'deco:lamp_room_{n}')
    dd['wall'] = 2
    dd['along'] = round(0.12 + 0.19 * i, 2)
    dd['height'] = 230

# ---------------------------------------------------------------- the chapel's tablet and plinth ends
for p in room('room:dwarf_shrine')['platforms']:
    if 'end_surface' in p:
        p['end_surface']['uneven'] = True  # 48 and 32 wide ends of stone: stretched stone does not show

# ---------------------------------------------------------------- the chalk mark at its square picture
sp = room('room:sorting_floor')['walls'][0]['panels'][0]
sp.update({'length': 112, 'height': 112, 'bottom': 256})

# ---------------------------------------------------------------- chests: the shipped kind, named Chest
for cid in ('chest:footlocker_1', 'chest:footlocker_3', 'chest:payroll', 'chest:strongbox'):
    c = obj('chests', cid)
    for k in ('surface', 'end_surface', 'top_surface'):
        c.pop(k, None)
    c['kind'] = 'ch1'
obj('chests', 'chest:footlocker_1')['size'] = [160, 80, 64]
obj('chests', 'chest:footlocker_3')['size'] = [160, 80, 64]
obj('chests', 'chest:payroll')['size'] = [160, 96, 64]
obj('chests', 'chest:strongbox').pop('size', None)
for eid in ('evt:chest_footlocker_1', 'evt:chest_footlocker_3', 'evt:chest_payroll', 'evt:chest_strongbox'):
    evt(eid)['title'] = 'Chest'
evt('evt:chest_strongbox')['text'] = "Under the tally slates: a heavy key stamped with a cart wheel."

# ---------------------------------------------------------------- levers of the shipped form
for sid in ('switch:trestle_station', 'switch:trestle_turntable', 'switch:east_landing', 'switch:east_turntable',
            'switch:hoist_floor', 'switch:hoist_rim'):
    s = obj('switches', sid)
    s['kind'] = 'lever'
    s['size'] = [12, 40]
    s['reach'] = 48
    s['off'] = TIMBER
    s['base'] = POST
    s['height'] = 112
pts = obj('switches', 'switch:points')
pts.update({'kind': 'lever', 'size': [12, 40], 'reach': 56, 'off': IRON, 'base': IRON, 'height': 96})
br = obj('switches', 'switch:brake')
br.update({'kind': 'lever', 'size': [16, 48], 'reach': 56, 'off': IRON, 'base': IRON, 'height': 112})
br['notes'] = "The Deep Line's brake lever, the chain padlocked through it."

yio.save(L + 'rooms.yml', R)
yio.save(L + 'objects.yml', O)
yio.save(L + 'wiring.yml', W)
print('edited')
