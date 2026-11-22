#!/usr/bin/env python3
"""Pass 3, step 2 (after shift.py): the main rooms enlarged and re-dressed, and the user's walk's faults.
One-off edit of the project in place; read its whole diff."""
import math, sys, yio
L = sys.argv[1]
rooms = yio.load(f'{L}/rooms.yml'); objects = yio.load(f'{L}/objects.yml'); wiring = yio.load(f'{L}/wiring.yml')
R = {r['id']: r for r in rooms['rooms']}
def tex(t, w, h, **k):
    d = {'texture': t, 'size': [w, h]}; d.update(k); return d
GT = tex('gt001a', 64, 64, fit=True); CH = tex('ch002a', 64, 64, fit=True)
def crate(at, size, rise, t=GT, base=None, notes=None):
    p = {'at': at, 'size': size, 'rise': rise, 'surface': t, 'top_surface': t}
    if base: p['base'] = base
    if notes: p['notes'] = notes
    return p
def objs(kind, room):
    return [o for o in objects[kind] if o.get('room') == room]
def obj(kind, oid):
    return next(o for o in objects[kind] if o['id'] == oid)
def evt(eid):
    return next(e for e in wiring['events'] if e['id'] == eid)

# ---------------- Loading bay: 1,664 by 1,280 (was 1,280 by 1,024), roof 640, higher stacks, wide aisles.
bay = R['room:loading_bay']
bay['outline'] = [[256, 0], [1664, 0], [1792, 128], [1792, 1152], [1664, 1280], [128, 1280], [128, 128]]
bay['ceiling'] = 640
bay['platforms'] = [
    {'at': [1744, 704], 'size': [96, 256], 'rise': 72, 'surface': tex('t1books1', 128, 128), 'top_surface': tex('t1books1', 128, 128), 'notes': 'A packing bench along the east wall.'},
    {'at': [1000, 700], 'size': [192, 160], 'rise': 16, 'surface': tex('gt003a', 64, 64, scale=2), 'top_surface': tex('t66floor', 128, 128), 'notes': 'A pallet of sacks waiting to go in, in the middle of the bay with room all round.'},
    crate([480, 1050], [256, 192], 192, notes='West stack by the barn doors, three crates high (416), each standing whole on the one under it.'),
    crate([480, 1050], [128, 128], 128, base=192),
    crate([480, 1050], [96, 96], 96, base=320),
    crate([560, 520], [192, 192], 256, CH, notes='A big studded crate (the Pirate Outpost\'s) off the office steps, room to pass on every side.'),
    crate([1344, 384], [192, 256], 256, CH, notes='East stack: a big studded crate with a crate on it (416).'),
    crate([1344, 384], [160, 160], 160, base=256),
    crate([1408, 960], [256, 192], 192, notes='North-east stack (320).'),
    crate([1408, 960], [128, 128], 128, base=192),
]
bay['beams'] = [
    {'path': [[128, 400], [1792, 400]], 'width': 48, 'depth': 48, 'bottom': 576, 'surface': tex('t66abc10a', 32, 128)},
    {'path': [[128, 860], [1792, 860]], 'width': 48, 'depth': 48, 'bottom': 576, 'surface': tex('t66abc10a', 32, 128)},
]
bay['notes'] = ("Long bay with chamfered corners, 1,664 by 1,280 under a roof 640 high (pass 3: it was 1,280 by 1,024 under "
                "512, too cramped for a warehouse): upright planks over a panelled wainscot, flagstones underfoot. Four "
                "crate stacks stand apart with aisles of 256 and more between them and the walls, two of them three "
                "crates high, every upper crate whole on the one under it; the cart way from the ramp to the barn doors "
                "runs clear down the middle past a pallet of sacks. A packing bench and barrels on the east wall. Two "
                "dark joists cross under the boards. The office's counter window looks in through the west wall, its "
                "steps beside it; the rolling barn doors to the grain hall are in the north wall under Joe's sign.")
for d in objects['decorations']:
    if d['room'] != 'room:loading_bay': continue
    moves = {'deco:bay_barrels_1': [1730, 900], 'deco:bay_barrels_2': [1740, 990], 'deco:bay_cask': [220, 1190],
             'deco:bay_pallet_sacks_1': [960, 680], 'deco:bay_pallet_sacks_2': [1045, 735],
             'deco:bay_sacks_1': [1180, 1210], 'deco:bay_sacks_2': [1270, 1215]}
    if d['id'] in moves: d['at'] = moves[d['id']]
    if d['id'] == 'deco:bay_lantern_w': d['along'] = 0.6
objects['decorations'].append({'id': 'deco:bay_lantern_s', 'room': 'room:loading_bay', 'decoration': 'torch02', 'wall': 'south', 'along': 0.8, 'height': 256})
obj('items', 'item:bay_bottle')['at'] = [1700, 160]
obj('spawns', 'spawn:bay_far')['at'] = [1000, 1080]

# ---------------- Aisle: 896 by 2,048 (was 448 by 1,792), a lean-to from 704 down to 512; KEEP OUT in the middle of
# its north wall (the cellar moved east by 256 for it).
aisle = R['room:hall_aisle']
aisle['outline'] = [[1920, 1344], [2816, 1344], [2816, 3392], [1920, 3392]]
aisle['ceiling'] = 704
aisle['ceiling_slope'] = {'to': 512, 'toward': 'east'}
aisle['platforms'] = [
    crate([2640, 1460], [256, 192], 256, CH, notes="Crates waiting at the aisle's south end: a big studded crate with two on it (480)."),
    crate([2640, 1460], [128, 128], 128, base=256),
    crate([2340, 1450], [192, 160], 192),
    crate([2340, 1450], [96, 96], 96, base=192),
    crate([2060, 1440], [128, 128], 128),
    crate([2400, 2200], [192, 256], 256, CH, notes='A stack in the middle of the aisle to walk round, 352 clear on either side.'),
    crate([2400, 2200], [128, 128], 128, base=256),
    {'at': [2768, 2416], 'size': [96, 256], 'rise': 72, 'surface': tex('t1books1', 128, 128), 'top_surface': tex('t1books1', 128, 128), 'notes': 'A sorting bench against the east wall, sacks split open on it.'},
]
aisle['notes'] = ("The north-east aisle, 896 by 2,048 under a lean-to roof falling from 704 to 512 (pass 3: it was 448 wide), "
                  "open to the hall through a wide gap in the hall's east wall: crates waiting at its south end, a stack "
                  "in its middle, torn sacks (the bugs' nests), a sorting bench, Joe's house rules on the east wall, and "
                  "the KEEP OUT door in the middle of its north wall under his skull-and-crossbones notice.")
for d in objects['decorations']:
    moves = {'deco:aisle_sacks_1': [2740, 2000], 'deco:aisle_sacks_2': [2700, 2090], 'deco:aisle_sacks_3': [2610, 2040],
             'deco:aisle_sacks_4': [2740, 2700]}
    if d['id'] in moves: d['at'] = moves[d['id']]
objects['decorations'].append({'id': 'deco:aisle_lantern_s', 'room': 'room:hall_aisle', 'decoration': 'torch02', 'wall': 'east', 'along': 0.35, 'height': 240})
op = next(o for o in rooms['openings'] if o['id'] == 'open:hall_aisle')
op['along'] = 0.4; op['width'] = 896
op['notes'] = 'The aisle opens off the hall\'s east wall, 896 wide, south of the loft.'

# ---------------- Joe's office: 896 by 1,056 (was 640 by 864), ceiling 512.
office = R['room:joes_office']
office['outline'] = [[-832, 96], [-192, 144], [-192, 512], [64, 512], [64, 1152], [-704, 1152], [-832, 1024]]
office['ceiling'] = 512
office['platforms'] = [
    {'id': 'platform:desk', 'at': [-420, 760], 'size': [224, 112], 'rise': 72, 'surface': tex('t1books1', 128, 128), 'top_surface': tex('t1books1', 128, 128), 'notes': "Joe's desk: a plain plank table (d06's furniture wood), not a chest; papers on it (clicked: the bills)."},
    {'at': [-420, 868], 'size': [48, 48], 'rise': 40, 'surface': tex('t1books1', 128, 128), 'top_surface': tex('t1books1', 128, 128), 'notes': "Joe's stool behind the desk."},
    {'at': [-212, 344], 'size': [40, 160], 'rise': 10, 'base': 300, 'surface': tex('t66abc11a', 128, 32), 'top_surface': tex('t66floor', 128, 128), 'bottom_surface': tex('t66floor', 128, 128), 'notes': "A plank ledge over the inside of the office door, 12 over the door's top: the slime bucket stands on it."},
]
office['notes'] = ("Trapezoid, 896 by 1,056 (pass 3: it was 640 by 864): the south wall and the north-west corner are set at "
                   "an angle. The east wall's projecting part faces the bay and holds the counter window; the recessed part "
                   "behind the steps holds the door, with a plank ledge over it inside where the slime bucket waits. Cream "
                   "plaster over a carved panel wainscot (t66d01). Joe's desk is a plain table with his bills on it, his "
                   "stool behind it; his ledgers stand on a shelf on the west wall (a readable panel); against the north "
                   "wall his cabinet, the Pirate Outpost's drawer cabinet and, as there, a chest (the pen key), and a "
                   "painted notice; a small MM8 chest, his strongbox, in the south-west corner.")
obj('decorations', 'deco:office_bucket').update({'at': [-212, 344], 'height': 310, 'notes': 'The slime bucket on its ledge over the inside of the door.'})
obj('decorations', 'deco:office_bucket_2')['at'] = [-640, 700]
obj('decorations', 'deco:office_candle').update({'at': [-480, 770], 'height': 72})
obj('lights', 'light:office_candle')['at'] = [-450, 760]
objects['decorations'].append({'id': 'deco:office_lantern_n', 'room': 'room:joes_office', 'decoration': 'torch02', 'wall': 'north', 'along': 0.75, 'height': 256})
objects['chests'] = [c for c in objects['chests'] if c['id'] != 'chest:desk']
objects['chests'] += [
    {'id': 'chest:cabinet', 'room': 'room:joes_office', 'at': [-480, 1112], 'size': [128, 64, 256],
     'surface': tex('t1cab', 128, 256, fit=True), 'end_surface': tex('t1books1', 128, 128), 'top_surface': tex('t1books1', 128, 128),
     'treasure_level': 1, 'random_items': 1, 'gold': 50, 'items': ['pen_key'],
     'notes': "Joe's cabinet against the north wall, 128 by 64 and 256 high with the drawer front (t1cab) one picture tall and wide, as the Pirate Outpost's cabinets are built and are chests: the pen key in its drawers, about 50 gold and one low item."},
    {'id': 'chest:strongbox', 'room': 'room:joes_office', 'at': [-704, 232], 'kind': 'gt002', 'treasure_level': 1, 'random_items': 0, 'gold': 12,
     'notes': "Joe's strongbox: an MM8 chest (the pirate maps' kind), nearly empty (the money is in the stash)."},
]
ev = evt('evt:desk')
ev.clear(); ev.update({'id': 'evt:desk', 'preset': 'text', 'source': 'platform:desk', 'title': "Joe's desk",
    'effects': [{'message': "Bills, piled by customer. 'Mayor's cellar: doom bugs removed, 400 gold.' 'Mayor's cellar: doom bugs removed again, 400 gold.' 'Mayor's cellar: slimes, 400 gold.' Under them a list headed SUPPLIERS, with every line scratched out."}]})
ev = evt('evt:cabinet')
ev.clear(); ev.update({'id': 'evt:cabinet', 'preset': 'chest', 'source': 'chest:cabinet', 'title': 'Cabinet'})
wiring['events'].append({'id': 'evt:strongbox', 'preset': 'chest', 'source': 'chest:strongbox', 'title': 'Chest'})

# ---------------- Feed store: an L of 1,440 by 1,312 off the neck (was 672 by 608), ceiling 192.
fs = R['room:feed_store']
fs['outline'] = [[-320, 4768], [1120, 4768], [1120, 5312], [1504, 5312], [1504, 5632], [1120, 5632], [1120, 6080], [-96, 6080], [-320, 5856]]
fs['ceiling'] = 192
fs['beams'] = [{'path': p, 'width': 48, 'depth': 48, 'bottom': 120, 'surface': tex('cbeam5', 32, 256)} for p in
               ([[-320, 5120], [1120, 5120]], [[-320, 5456], [1120, 5456]], [[-320, 5792], [1120, 5792]], [[400, 4768], [400, 6080]])]
fs['platforms'] = [
    {'at': [160, 5320], 'size': [256, 192], 'rise': 16, 'surface': tex('gt003a', 64, 64, scale=2), 'top_surface': tex('d1ceil1', 256, 256), 'notes': 'A pallet of Slime Chow sacks.'},
    crate([-150, 5940], [256, 192], 192, notes='Crates of feed in the north-west corner (320).'),
    crate([-150, 5940], [128, 128], 128, base=192),
    crate([720, 5980], [192, 128], 128),
]
fs['notes'] = ("A neck from the cistern's west arch between two pens, opening into the store: 1,440 by 1,312 under plank "
               "joists, 576 high (pass 3: it was 672 by 608 under 448). Sacks of JOE'S PREMIUM SLIME CHOW line its south "
               "wall round the stash's sliding door; a pallet of sacks, crates of feed, the mash cauldron.")
for d in objects['decorations']:
    moves = {'deco:feed_bucket': [380, 5660], 'deco:feed_mash': [300, 5600], 'deco:feed_sacks_1': [540, 4830],
             'deco:feed_sacks_2': [630, 4830], 'deco:feed_sacks_3': [700, 4880], 'deco:feed_sacks_4': [100, 5300],
             'deco:feed_sacks_5': [1050, 4835], 'deco:feed_sacks_6': [1060, 4930]}
    if d['id'] in moves: d['at'] = moves[d['id']]
    if d['id'] == 'deco:feed_lantern': d['wall'] = 6; d['along'] = 0.5
objects['decorations'] += [
    {'id': 'deco:feed_lantern_w', 'room': 'room:feed_store', 'decoration': 'torch02', 'wall': 8, 'along': 0.5, 'height': 224},
    {'id': 'deco:feed_sacks_7', 'room': 'room:feed_store', 'decoration': 'floursac', 'at': [220, 5300]},
]
obj('spawns', 'spawn:feed_store')['at'] = [500, 5450]
st = R['room:joes_stash']
st['outline'] = [[448, 4320], [896, 4320], [960, 4384], [960, 4704], [448, 4704]]
obj('chests', 'chest:stash')['at'] = [688, 4556]
obj('decorations', 'deco:stash_barrel')['at'] = [876, 4636]

# ---------------- Shipping room: 1,514 by 1,250 (was 1,002 by 802), ceiling 192; the chute in the new north-east corner.
sh = R['room:shipping_room']
sh['outline'] = [[3091, 5970], [4380, 5970], [4380, 7220], [2866, 7220], [2866, 6195]]
sh['ceiling'] = 192
sh['ceiling_levels'][0]['outline'] = [[4124, 6964], [4316, 6964], [4316, 7156], [4124, 7156]]
sh['ceiling_levels'][0]['ceiling'] = 704
slide, table = sh['platforms'][0], sh['platforms'][3]
slide['at'] = [4220, 7028]
table['at'] = [3350, 6400]
sh['platforms'] = [slide,
    crate([3900, 6250], [256, 256], 256, notes="Crates addressed to Vertigo homes ('Mayor's cellar - Tuesday'), three high (480)."),
    crate([3900, 6250], [128, 128], 128, base=256),
    crate([3900, 6250], [96, 96], 96, base=384),
    crate([3300, 6950], [256, 192], 192, notes='A second stack by the west wall.'),
    crate([3300, 6950], [128, 128], 128, base=192),
    crate([3600, 7120], [128, 128], 128),
    table]
wall = sh['walls'][0]['panels']
wall.append({'offset': 432, 'length': 256, 'bottom': 32, 'height': 288, 'surface': tex('xntonics', 128, 256), 'notes': 'More racks of bottled stock.'})
sh['notes'] = ("Five-sided, 1,514 by 1,250 and 576 high (pass 3: it was 1,002 by 802 under 448): the slanted south-west wall "
               "faces the cistern's north-east wall and holds the door. Joe works here: two crate stacks, a packing table, "
               "racks of bottled stock on the east wall, and the delivery chute rising to the street in the north-east "
               "corner with its slide coming down out of it. The invoice crate stands under the chute.")
obj('chests', 'chest:invoice')['at'] = [4012, 7084]
obj('items', 'item:packed_potion')['at'] = [3300, 6400]
obj('items', 'item:packed_gloves')['at'] = [3400, 6390]
for d in objects['decorations']:
    moves = {'deco:ship_barrel': [2960, 7110], 'deco:ship_small_barrel': [3050, 7140], 'deco:ship_cask': [4300, 6800]}
    if d['id'] in moves: d['at'] = moves[d['id']]
objects['decorations'].append({'id': 'deco:ship_lantern_s', 'room': 'room:shipping_room', 'decoration': 'torch02', 'wall': 0, 'along': 0.6, 'height': 224})
obj('spawns', 'spawn:shipping')['at'] = [3600, 6650]
evt('evt:invoice_crate')['title'] = 'Crate'

# ---------------- The honeymoon pen: a kidney of 1,520 by 1,280 past its neck (was 960 by 672), ceiling 128, dome 320.
hm = R['room:mated_pair_pen']
hm['outline'] = [[2192, 6336], [2544, 6336], [2544, 6688], [2720, 6784], [2800, 6976], [2800, 7424], [2720, 7712], [2528, 7904], [2304, 7968], [2112, 7872], [1984, 7744], [1824, 7840], [1536, 7840], [1344, 7616], [1280, 7264], [1344, 6976], [1600, 6784], [1920, 6720], [2192, 6688]]
hm['ceiling'] = 128
hm['ceiling_levels'][0]['outline'] = [[1472, 7008], [2656, 7008], [2720, 7264], [2656, 7584], [1472, 7584], [1408, 7296]]
hm['ceiling_levels'][0]['ceiling'] = 320
bed, trough = hm['platforms']
bed['at'] = [2050, 7420]
dx, dy = 2050 - 2368, 7130 - 6990
trough['outline'] = [[x + dx, y + dy] for x, y in trough['outline']]
hm['notes'] = ("Kidney-shaped, one step (32) below the cistern, 1,520 by 1,280 past its neck under a brick dome (pass 3: the "
               "boss's room was 960 by 672; now there is room to fight the pair and their splits): a narrow neck from the "
               "heart-painted gate, then the bean with its hollow to the north. The pair's bed and nest in the middle, "
               "their heart-shaped trough before it, the rival exterminator's body by the east wall.")
for d in objects['decorations']:
    moves = {'deco:honeymoon_bones': [1500, 7300], 'deco:honeymoon_bones_2': [2700, 7100], 'deco:honeymoon_bowl_2': [2260, 7060],
             'deco:honeymoon_candle_1': [1874, 7360], 'deco:honeymoon_candle_2': [2226, 7360], 'deco:honeymoon_candle_3': [1874, 7480],
             'deco:honeymoon_candle_4': [2226, 7480], 'deco:honeymoon_corpse': [2620, 7460], 'deco:honeymoon_nest': [2050, 7420]}
    if d['id'] in moves: d['at'] = moves[d['id']]
    if d['id'] == 'deco:honeymoon_torch_w': d['wall'] = 13
    if d['id'] == 'deco:honeymoon_torch_e': d['wall'] = 4
obj('lights', 'light:honeymoon_candles')['at'] = [2050, 7420]
obj('items', 'item:rival_boots')['at'] = [2660, 7540]
obj('items', 'item:rival_scroll').update({'at': [2150, 7440], 'floor_height': -392, 'notes': "His Torch Light scroll, carried off to the pair's bed: it lies on the straw beside their nest."})
obj('monsters', 'monster:mr_wobbles')['at'] = [1850, 7050]
obj('monsters', 'monster:mrs_wobbles')['at'] = [2560, 7050]
evt('evt:mr_splits')['effects'][0]['summon']['at'] = [1850, 7050, -416]
evt('evt:mrs_splits')['effects'][0]['summon']['at'] = [2560, 7050, -416]
obj('decorations', 'deco:honeymoon_nest')['notes'] = "The pair's nest of mash and muck on their bed: searched on a click (evt:nest)."
wiring['events'].append({'id': 'evt:nest', 'preset': 'text', 'source': 'deco:honeymoon_nest', 'title': 'Nest', 'once': True,
    'effects': [{'gold': 75}], 'text': "You dig through the pair's nest of slime and straw and find the rival exterminator's purse: 75 gold.",
    'notes': "The nest is searched (the user's walk: nothing said it could be clicked). Its hover name says Nest, the scroll on the straw beside it draws the eye, and it gives the rival's purse once."})

# ---------------- The cistern: the bug tanks framed in iron on stone plinths; the FEEDING TIME lever.
cis = R['room:breeding_pens']
new = []
tanks = 0
for p in cis['platforms']:
    s = p['surface']['texture']
    if s == 'cbeam5':
        p.update({'base': 0, 'rise': 128, 'surface': tex('d1medbw', 128, 128), 'top_surface': tex('d1medbw', 128, 128)})
        p.pop('base')
        p['notes'] = 'A stone plinth against the wall, 128 high, under a row of bug tanks.'
        new.append(p)
    elif s == 'xnbugtank':
        q = p['outline']; cracked = p['rise'] == 48
        c = [sum(v[0] for v in q) / 4, sum(v[1] for v in q) / 4]
        u = [q[1][0] - q[0][0], q[1][1] - q[0][1]]; lu = math.hypot(*u); u = [u[0] / lu, u[1] / lu]
        v = [q[2][0] - q[1][0], q[2][1] - q[1][1]]; lv = math.hypot(*v); v = [v[0] / lv, v[1] / lv]
        def rect(cx, cy, hl, hd):
            return [[round(cx + a * hl * u[0] + b * hd * v[0]), round(cy + a * hl * u[1] + b * hd * v[1])] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        tanks += 1
        iron = tex('d8dorf', 128, 256)
        new.append({'rise': 6, 'surface': iron, 'top_surface': iron, 'outline': rect(c[0], c[1], lu / 2 + 3, lv / 2 + 3), 'base': 128,
                    'notes': 'Bug tank: its iron foot.' if not cracked else 'The cracked tank: its iron foot.'})
        body = {'id': 'platform:tank_%d' % tanks, 'rise': 42 if cracked else 58, 'surface': p['surface'],
                'top_surface': tex('7slimywtr', 128, 128) if cracked else iron, 'outline': rect(c[0], c[1], lu / 2, lv / 2), 'base': 134,
                'notes': ('The cracked tank: no lid, its glass broken low, the slime open to the air (where the doom bugs get out).' if cracked
                          else 'Bug tank: glass sides (xnbugtank) between four iron corner posts, under an iron lid.')}
        new.append(body)
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            new.append({'rise': 42 if cracked else 58, 'surface': iron, 'top_surface': iron, 'base': 134,
                        'outline': rect(c[0] + a * lu / 2 * u[0] + b * lv / 2 * v[0], c[1] + a * lu / 2 * u[1] + b * lv / 2 * v[1], 3.5, 3.5)})
        if not cracked:
            new.append({'rise': 6, 'surface': iron, 'top_surface': iron, 'outline': rect(c[0], c[1], lu / 2 + 3, lv / 2 + 3), 'base': 192})
        wiring['events'].append({'id': 'evt:tank_%d' % tanks, 'preset': 'text', 'source': 'platform:tank_%d' % tanks, 'title': 'Bug tank',
            'text': ("The glass of this tank is cracked low down, and it is empty but for slime. Whatever was in it is out." if cracked else
                     "Doom bugs crawl over each other in green slime behind the dirty glass. A label: BREEDING STOCK. DO NOT TAP THE GLASS.")})
    else:
        new.append(p)
cis['platforms'] = new
for w in cis['walls']:
    for pn in w['panels']:
        if pn['id'] == 'panel:feeding_time': pn['bottom'] = 200
sw = obj('switches', 'switch:feeding_time')
sw.clear(); sw.update({'id': 'switch:feeding_time', 'room': 'room:breeding_pens', 'kind': 'lever', 'wall': 3, 'along': 0.5, 'height': 150,
    'size': [12, 40], 'reach': 48, 'base': tex('d8dorf', 128, 256),
    'notes': "The FEEDING TIME lever: the shipped maps' lever kind (a post and an arm that sinks when pulled, MM6's, as in Gharik's Forge and Castle Darkmoor, the cellar's family) on the plain wall facing the stair, under its painted label; it replaced the studio's default red plate (t1swdd), which came from another set."})

yio.save(f'{L}/rooms.yml', rooms); yio.save(f'{L}/objects.yml', objects); yio.save(f'{L}/wiring.yml', wiring)
print('tanks', tanks)
