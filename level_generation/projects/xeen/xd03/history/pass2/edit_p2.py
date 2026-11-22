#!/usr/bin/env python3
"""XD-03 second pass: bigger main rooms, legibility fixes, faces in one plane. Run once on the pass-1 project
(output/studio_cal/xd03/pass2_backup is the project before it); then oymap fmt. Not to be rerun on edited files."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd03/pass2')
import yio

L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4/'
rooms = yio.load(L + 'rooms.yml')
objects = yio.load(L + 'objects.yml')
wiring = yio.load(L + 'wiring.yml')


def room(rid):
    return next(r for r in rooms['rooms'] if r['id'] == rid)


def opening(oid):
    return next(o for o in rooms['openings'] if o['id'] == oid)


def obj(kind, oid):
    return next(o for o in objects[kind] if o['id'] == oid)


def event(eid):
    return next(e for e in wiring['events'] if e['id'] == eid)


def deco(did):
    return obj('decorations', did)


# ---------------------------------------------------------------- themes
for t in rooms['themes']:
    if t['id'] == 'theme:king_hall':
        t['ends']['surface'].pop('fit', None)

# ---------------------------------------------------------------- the landing: 256 longer to the south
r = room('room:deep_landing')
r['outline'] = [[6144, 512], [6272, 384], [7552, 384], [7680, 512], [7680, 1408], [7552, 1536], [6272, 1536],
                [6144, 1408]]
r['ceiling_points'] = [[7680, 768, 896], [7680, 1408, 896], [7552, 384, 768], [7552, 1536, 832], [7104, 1088, 1024],
                       [6464, 1088, 768], [6144, 768, 576], [6144, 1408, 576], [6912, 512, 704]]
r['notes'] = r['notes'].replace('1536 x 896', '1536 x 1152')
# Trestle posts end under their caps (they ran through them: faces in one plane), a little narrower than the caps.
caps = {7168: 256, 6976: 160, 6784: 64}
for p in r['platforms']:
    if p.get('notes') == 'Trestle post':
        p['size'] = [20, 20]
        p['rise'] = caps[p['at'][0]]
for b in r['beams']:
    if b.get('notes') == 'Cap of a trestle bent':
        b['width'] = 28
        b['path'] = [[b['path'][0][0], 1020], [b['path'][1][0], 1156]]

# ---------------------------------------------------------------- the Deep Line head: 320 wide, its mouth 256
r = room('room:deep_line')
r['outline'] = [[7744, 928], [8320, 928], [8320, 1248], [7744, 1248]]
for b in r['beams']:
    b['path'] = [[b['path'][0][0], 928], [b['path'][1][0], 1248]]
opening('open:head_ledge')['width'] = 256
obj('exits', 'exit:deep_cart')['size'] = [256, 256]

# ---------------------------------------------------------------- the sentry cut: 320 wide, doorways 256
r = room('room:sentry_cut')
r['width'] = 320
for p in r['platforms']:
    x, y = p['at']
    if p.get('notes') == 'Timber set post':
        if x in (6420, 6636):
            p['at'] = [6388 if x == 6420 else 6668, y]
            p['rise'] = 340
        else:
            p['at'] = [x, 2612 if y == 2644 else 2892]
            p['rise'] = 330
        p['size'] = [20, 20]
for b in r['beams']:
    (x0, y0), (x1, y1) = b['path']
    if y0 == y1:
        b['path'] = [[6368, y0], [6688, y0]]
        b['width'] = 28
    else:
        b['path'] = [[5600, 2596], [5600, 2908]]
        b['bottom'] = 244
        b['width'] = 28
r = room('room:sentry_lookout')
r['outline'] = [[6464, 2400], [6784, 2400], [6784, 2720], [6464, 2720]]
for o in ('open:landing_cut', 'open:sentry_door', 'open:cut_lookout'):
    opening(o)['width'] = 256
    opening(o)['height'] = 256 if o == 'open:sentry_door' else 320

# ---------------------------------------------------------------- the furnace hall
r = room('room:furnace_hall')
for pp in r['parapets']:
    if pp.get('notes') == "The gallery's parapet":
        # Its outer face stood in the gallery level's edge (faces in one plane); now 8 inside it.
        pp['path'] = [[4900, 2456], [4724, 2456], [4724, 3764]]
plats = r['platforms']
# The furnace mouth's ends were its slag picture stretched over 16 x 144.
mouth = next(p for p in plats if p.get('id') == 'platform:furnace_mouth')
mouth['end_surface'] = {'texture': 'vlcwl3a', 'size': [128, 256], 'fit': False}
# The gong: one picture (xngong at 1.5, 192 across) over eight slabs of 24, each showing its own window of it by an
# offset (the six strips xngong1-6 were cut only because offsets were refused then); all eight are clicked.
plats[:] = [p for p in plats if not str(p.get('surface', {}).get('texture', '')).startswith('xngong')]
half = [45, 75, 87, 96, 96, 87, 75, 45]
for k, h in enumerate(half):
    face = {'texture': 'xngong', 'size': [128, 128], 'scale': 1.5, 'offset': [(96 - h) * 2 // 3, 16 * k]}
    plats.append({'id': f'platform:gong_{k + 1}', 'at': [4912, 3640], 'size': [2 * h, 12], 'rise': 24,
                  'surface': face, 'end_surface': {'texture': 'vlcgnrc1', 'size': [256, 256]},
                  'top_surface': {'texture': 'vlcgnrc1', 'size': [256, 256]}, 'base': 648 - 24 * k,
                  'notes': 'The great gong (clicked): one of its eight bronze slabs.' if k == 0 else None})
    if plats[-1]['notes'] is None:
        del plats[-1]['notes']
# Two short chains from the gong's top to the frame's beam (it hung 64 under the beam on nothing).
for x in (4872, 4952):
    plats.append({'at': [x, 3640], 'size': [8, 8], 'rise': 64, 'base': 672,
                  'surface': {'texture': 'ch004i', 'size': [64, 64]}, 'notes': 'Gong chain'})
# Bridges stand on stone piers in the slag (they rested on nothing over most of their footprint).
pier = {'texture': 'vlcwl3a', 'size': [128, 256]}
for outline, note in (
        ([[2847, 2465], [2983, 2601], [2937, 2647], [2801, 2511]], "South bridge's pier"),
        ([[2960, 2352], [3096, 2488], [3048, 2536], [2912, 2400]], "South bridge's abutment"),
        ([[2688, 2624], [2736, 2576], [2872, 2712], [2824, 2760]], "South bridge's abutment"),
        ([[3920, 3312], [4352, 3744], [4256, 3744], [3872, 3360]], "North span's abutment"),
        ([[3648, 3584], [3696, 3536], [3904, 3744], [3808, 3744]], "North span's abutment")):
    plats.append({'rise': 80, 'outline': outline, 'surface': dict(pier), 'notes': note})
# Pilasters of dressed granite against the walls, the roof timbers resting on two of them: the walls were large plain
# planes. 128 wide, 48 deep, up to the timbers' foot (160).
for x in (3008, 3584, 4352, 4736):
    plats.append({'at': [x, 1560], 'size': [128, 48], 'rise': 672, 'surface': {'texture': 'vlcwl3a', 'size': [128, 256]},
                  'top_surface': {'texture': 'vlcwl3a', 'size': [128, 256]}, 'notes': 'Pilaster'})
for x in (2688, 4592):
    plats.append({'at': [x, 3752], 'size': [128, 48], 'rise': 672, 'surface': {'texture': 'vlcwl3a', 'size': [128, 256]},
                  'top_surface': {'texture': 'vlcwl3a', 'size': [128, 256]}, 'notes': 'Pilaster'})
for y in (2816, 3584):
    plats.append({'at': [2584, y], 'size': [48, 128], 'rise': 672, 'surface': {'texture': 'vlcwl3a', 'size': [128, 256]},
                  'top_surface': {'texture': 'vlcwl3a', 'size': [128, 256]}, 'notes': 'Pilaster'})
for b in r['beams']:
    if b.get('notes') == 'Gong frame beam':
        b['path'] = [[4776, 3640], [5048, 3640]]
r['notes'] += (" Pass two: pilasters of dressed granite against the south, west and north walls (the roof timbers rest"
               " on two), stone piers under the bridges, the gong of eight slabs under one picture.")
# The barracks' double door: two leaves of 128 x 256 (the skull door's halves), a 32 mullion between.
o = opening('open:barracks_doors_e')
o.update({'along': 0.5724, 'width': 128, 'height': 256})
o = opening('open:barracks_doors_w')
o.update({'along': 0.7039, 'width': 128, 'height': 256})

# ---------------------------------------------------------------- the barracks: 576 high
r = room('room:barracks')
r['ceiling'] = 64
for b in r['beams']:
    b['bottom'] = 32
r['notes'] = r['notes'].replace('448 high', '576 high')
opening('open:armoury_door').update({'width': 256, 'height': 256})

# ---------------------------------------------------------------- the tower stair and door: 256
r = room('room:tower_stair')
r['outline'] = [[2112, 3168], [2496, 3168], [2496, 3488], [2112, 3488]]
opening('open:tower_stair_foot')['width'] = 256
opening('open:tower_door').update({'width': 256, 'height': 256})

# ---------------------------------------------------------------- the antechamber and the King's Gate
r = room('room:kings_antechamber')
r['outline'] = [[2560, 3840], [3840, 3840], [3584, 4608], [2816, 4608]]
r['platforms'] = [
    {'at': [2880, 4560], 'size': [32, 48], 'rise': 448, 'surface': {'texture': 'vlcgnrc3', 'size': [256, 256]},
     'notes': 'Bar bracket'},
    {'at': [3520, 4560], 'size': [32, 48], 'rise': 448, 'surface': {'texture': 'vlcgnrc3', 'size': [256, 256]},
     'notes': 'Bar bracket'}]
r['notes'] = ("A wedge 1280 wide at the hall narrowing to 768 at the King's Gate under a pointed vault: the two hacked"
              " statues against its slanting walls, two flambeaux, the gate's two iron bars (movers).")
opening('open:gate_e').update({'along': 0.2917, 'width': 256, 'height': 256})
opening('open:gate_w').update({'along': 0.7083, 'width': 256, 'height': 256})

# ---------------------------------------------------------------- the King's hall: throne and stands apart
r = room('room:king_hall')
for p in r['platforms']:
    n = p.get('notes', '')
    if n == "The throne's plinth":
        p['at'] = [3200, 6216]
        p['size'] = [448, 272]
    elif p.get('id') == 'platform:throne':
        p['at'] = [3200, 6240]
    elif n == "The throne's back.":
        p['at'] = [3200, 6328]
    elif n.startswith("The throne's crest"):
        p['at'] = [3200, 6328]
        p['end_surface'] = {'texture': 'vlcwl3a', 'size': [128, 256], 'fit': False}
    elif n == 'Forge brazier stand':
        p['at'] = [2880 if p['at'][0] < 3200 else 3520, 6216]

# ---------------------------------------------------------------- the geode: bigger grotto and lower terrace
r = room('room:geode_grotto')
r['outline'] = [[1088, 1024], [1344, 1280], [1344, 1920], [1152, 2368], [704, 2624], [192, 2560], [-192, 2240],
                [-320, 1664], [-128, 1216], [192, 1024]]
r['ceiling'] = -64
r['ceiling_points'] = [[640, 1792, 384], [448, 1408, 256], [1024, 1984, 256], [960, 1344, 192], [256, 2176, 256],
                       [-96, 1728, 192], [0, 2176, 128], [-64, 1344, 128]]
r['notes'] = ("The upper terrace: the hollow of the geode, its crown 1024 over the floor, two crystal columns, the bat"
              " queens in its crown.")
r = room('room:geode_lower')
r['outline'] = [[192, -384], [704, -640], [1344, -576], [1664, -192], [1600, 320], [1344, 640], [1088, 704],
                [320, 704], [128, 576], [128, 192]]
r['ceiling'] = -128
r['ceiling_points'] = [[800, 0, 64], [400, 320, -32], [1200, 256, 0], [800, -400, -32], [1300, -200, -32]]
r['pillars'] = [{'surface': {'texture': 'xnquartz', 'size': [256, 256]},
                 'outline': [[1104, -240], [1168, -192], [1152, -96], [1072, -64], [1008, -128], [1024, -208]],
                 'notes': 'Crystal column'}]
r = room('room:geode_descent')
r['outline'] = [[1408, 1504], [1856, 1504], [1856, 1792], [1408, 1792]]
opening('open:breach_descent')['width'] = 256
opening('open:descent_geode')['width'] = 256
opening('open:crystal_wall').update({'width': 256, 'height': 256})

# ---------------------------------------------------------------- the mole warren: bigger, higher, a third and fourth core
r = room('room:mole_warren')
r['outline'] = [[2944, 128], [3392, -384], [4352, -512], [4992, -256], [5312, 320], [4992, 768], [4608, 896],
                [4224, 896], [3712, 896], [3200, 768]]
r['floor_points'] = [[3584, 0, -800], [4864, 256, -784], [3400, 500, -736], [4600, 500, -800], [3800, -300, -800],
                     [4600, -300, -784], [5100, 300, -776]]
r['ceiling'] = -224
r['ceiling_points'] = [[3968, 160, -176], [4352, 704, -224], [3500, 640, -240], [4800, 450, -200], [4096, 448, -160],
                       [3900, -250, -192], [4700, -200, -208], [3250, 200, -256]]
r['pillars'].append({'surface': {'texture': 'c2b', 'size': [256, 256]},
                     'outline': [[3200, 256], [3360, 192], [3424, 320], [3328, 448], [3184, 400]], 'notes': 'Rock core'})
r['pillars'].append({'surface': {'texture': 'c2b', 'size': [256, 256]},
                     'outline': [[4096, -256], [4288, -320], [4384, -160], [4256, -32], [4064, -96]],
                     'notes': 'Rock core'})
r['notes'] = "A knot of burrows round four rock cores, uneven and dark; the dead prospector in the east burrow."
r = room('room:warren_mouth')
r['outline'] = [[3808, 960], [4128, 960], [4128, 1472], [3808, 1472]]
opening('open:hall_warren')['width'] = 256
opening('open:warren_mouth')['width'] = 256

# ================================================================= objects
doors = objects['doors']
plank = {'texture': 'bemvwal', 'size': [128, 256]}
for d in doors:
    if d['id'] in ('door:armoury', 'door:sentry', 'door:tower'):
        d['surface'] = dict(plank)
        d['tile'] = True
    if d['id'] in ('door:barracks_e', 'door:barracks_w'):
        d['surface'] = {'texture': 'd2lgdor', 'size': [256, 256], 'offset': [128 if d['id'] == 'door:barracks_e' else 0, 0]}
        d['tile'] = True
        d['edge_surface'] = {'texture': 'vlctrm3', 'size': [128, 128]}
    if d['id'] in ('door:gate_e', 'door:gate_w'):
        d['surface'] = {'texture': 'd2lgdor', 'size': [256, 256], 'fit': True}
        d['edge_surface'] = {'texture': 'bemv16a', 'size': [16, 256]}
    if d['id'] == 'door:hoard':
        d['surface'] = {'texture': 'cvdor1', 'size': [128, 256], 'fit': True}
        d['notes'] = "The King's stone door behind the throne (the Forge's slab door): the King's key."
    if d['id'] == 'door:back_stair':
        d['surface'] = {'texture': 'bemvwal', 'size': [128, 256], 'fit': True}
opening('open:back_stair_foot').update({'width': 128, 'height': 256})

for m in objects['movers']:
    if m['id'] == 'mover:cage':
        for p in m['parts']:
            if p.get('notes') == 'Hanger bar':
                p['size'] = [8, 416]   # met the top ring's sides in one plane
    if m['id'] == 'mover:gate_bar_low':
        m.update({'size': [640, 24], 'bottom': 96, 'travel': [0, 0, 256]})
    if m['id'] == 'mover:gate_bar_high':
        m.update({'size': [640, 24], 'bottom': 192, 'travel': [0, 0, 224]})

# Levers of the Forge's kind (a post and an arm that sinks), above the brick's footing band.
sw = {s['id']: s for s in objects['switches']}
for sid in ('switch:lever_a', 'switch:lever_b', 'switch:shaft_lever', 'switch:cage_call', 'switch:cage_call_top'):
    s = sw[sid]
    s['kind'] = 'lever'
    s.pop('size', None)
    s['height'] = 160
s = sw['switch:cage_call']
for k in ('wall', 'along'):
    s.pop(k, None)
s['at'] = [3648, 7330]
s['reach'] = 24   # clear of the cage, which passes 32 from the wall
sw['switch:cage_call']['notes'] ="The cage lever at the shaft's foot: calls the cage down (a bell rings above)."
sw['switch:cage_call_top']['notes'] = "The cage lever at the shaft head: calls the cage up."

# Chests: the shipped families' kinds; the prospector's pack becomes a small chest beside his bones.
ch = {c['id']: c for c in objects['chests']}
ch['chest:armoury'].update({'kind': 'ch2'})
ch['chest:hoard_1'].update({'kind': 'ch3', 'lid': 'v'})
ch['chest:hoard_2'].update({'kind': 'ch3', 'lid': 'v'})
ch['chest:vault'].update({'kind': '7gt002'})
c = ch['chest:prospector']
for k in ('size', 'surface'):
    c.pop(k, None)
c.update({'kind': '7gt002', 'at': [4800, 520], 'facing': 'n', 'notes': "The dead prospector's chest."})

# Monsters: the King is the Dwarf family's top rank (the game ignores `hp`), on his plinth in front of the seat.
mon = {m['id']: m for m in objects['monsters']}
k = mon['monster:clan_king']
k['monster'] = 231
k['at'] = [3200, 6130]
k['notes'] = ("The Clan King on the throne floor: a Dwarven Commander (231, level 30, 180 hit points, armour-breaking"
              " blows, never flees), the Dwarf family's top rank, a colour of his own among his Soldiers; `hp: 300`"
              " waits for the game to honour it. He fights from the dais until his guard falls (set:clan_king).")
mon['monster:barracks_1']['at'] = [4160, 4560]
mon['monster:barracks_2']['at'] = [5184, 4560]
mon['monster:barracks_3']['at'] = [4160, 4140]
mon['monster:gate_guard_1']['at'] = [3040, 4380]
mon['monster:gate_guard_2']['at'] = [3360, 4380]

# Lights and decorations that moved with their things.
li = {l['id']: l for l in objects['lights']}
li['light:gate_w']['at'] = [2850, 4470]
li['light:gate_e']['at'] = [3550, 4470]
li['light:forge_w']['at'] = [2880, 6216]
li['light:forge_e']['at'] = [3520, 6216]
deco('deco:gate_flambeau_w')['at'] = [2850, 4470]
deco('deco:gate_flambeau_e')['at'] = [3550, 4470]
deco('deco:statue_w')['at'] = [2760, 4150]
deco('deco:statue_e')['at'] = [3640, 4150]
deco('deco:forge_brazier_w')['at'] = [2880, 6216]
deco('deco:forge_brazier_e')['at'] = [3520, 6216]
deco('deco:king_goblets')['at'] = [2800, 6400]
deco('deco:skull_pile')['at'] = [3600, 6400]
deco('deco:hall_bucket')['at'] = [4600, 2150]
for did, along in (('deco:gallery_torch_1', 0.523), ('deco:gallery_torch_2', 0.865)):
    d = deco(did)
    d.pop('at', None)
    d['along'] = along
d = deco('deco:shaft_lamp')
d.pop('at', None)
d['along'] = 0.2
deco('deco:geode_crystal_4')['at'] = [-100, 1700]
deco('deco:geode_crystal_5')['at'] = [560, 2480]
newdeco = [
    ('deco:geode_stalagmite_4', 'room:geode_grotto', 'stlmite1', [-160, 1480]),
    ('deco:geode_crystal_7', 'room:geode_grotto', 'crys5', [0, 2240]),
    ('deco:geode_crystal_8', 'room:geode_grotto', 'crclstr', [-220, 1960]),
    ('deco:geode_glow_5', 'room:geode_grotto', 'crystl0', [-60, 1840]),
    ('deco:lower_crystal_5', 'room:geode_lower', 'crys6', [1450, -200]),
    ('deco:lower_crystal_6', 'room:geode_lower', 'crclstr', [700, -480]),
    ('deco:lower_stalagmite_1', 'room:geode_lower', 'stlmite2', [1300, 380]),
    ('deco:lower_stalagmite_2', 'room:geode_lower', 'stlmite3', [400, -250]),
    ('deco:lower_glow_2', 'room:geode_lower', 'crystl0', [1200, -380]),
    ('deco:warren_bones', 'room:mole_warren', 'dec29', [3700, -200]),
    ('deco:warren_dirt_3', 'room:mole_warren', '7dec01', [4800, -100]),
    ('deco:warren_rock_2', 'room:mole_warren', '6rock02', [3000, 300]),
    ('deco:warren_skull', 'room:mole_warren', '7dec20', [4500, 100]),
    ('deco:landing_rock_3', 'room:deep_landing', '6rock01', [7300, 520]),
    ('deco:landing_barrel', 'room:deep_landing', 'bigbarel', [6700, 480]),
]
for did, rid, name, at in newdeco:
    objects['decorations'].append({'id': did, 'room': rid, 'decoration': name, 'at': at})
# Torches on the furnace hall's walls between the pilasters.
for did, wall, along in (('deco:hall_torch_s1', 'south', 0.30), ('deco:hall_torch_s2', 'south', 0.70),
                         ('deco:hall_torch_w', 'west', 0.33)):
    objects['decorations'].append({'id': did, 'room': 'room:furnace_hall', 'decoration': 'TrchB00', 'wall': wall,
                                   'along': along, 'height': 224})
objects['lights'].append({'id': 'light:geode_4', 'room': 'room:geode_grotto', 'at': [-60, 1840], 'height': 96,
                          'radius': 700, 'color': [90, 150, 255], 'pulse': {'intensity': [0.4, 1], 'frequency': 0.2,
                                                                             'phase': 0.5}})
objects['lights'].append({'id': 'light:geode_lower_2', 'room': 'room:geode_lower', 'at': [1200, -380], 'height': 96,
                          'radius': 700, 'color': [90, 150, 255], 'pulse': {'intensity': [0.4, 1], 'frequency': 0.25,
                                                                             'phase': 0.5}})
objects['lights'].append({'id': 'light:warren_2', 'room': 'room:mole_warren', 'at': [3700, -100], 'height': 160,
                          'radius': 600, 'color': [130, 110, 90]})
objects['lights'].append({'id': 'light:landing_south', 'room': 'room:deep_landing', 'at': [6900, 560], 'height': 300,
                          'radius': 600, 'color': [200, 150, 110]})
# Spawns and items in the new ground.
sp = {s['id']: s for s in objects['spawns']}
sp['spawn:warren_west']['at'] = [3550, 100]
sp['spawn:item_geode']['at'] = [1300, -300]
objects['spawns'].append({'id': 'spawn:warren_south', 'room': 'room:mole_warren', 'at': [4700, -150], 'slot': 3,
                          'tier': 'a'})
for it in objects['items']:
    if it['id'] == 'item:prospector_potion':
        it['at'] = [4720, 440]
# The King's hoard reads as a hoard: heaps of gold on the floor round the chests.
for n, (x, y, item) in enumerate([(3080, 7180, 1001), (3200, 7120, 1000), (2880, 7020, 1001), (3420, 7060, 1000),
                                  (3300, 6980, 999)]):
    objects['items'].append({'id': f'item:hoard_gold_{n + 1}', 'room': 'room:king_hoard', 'item': item, 'at': [x, y],
                             'notes': 'A heap of the King\'s gold.'})

# ================================================================= wiring
ev = {e['id']: e for e in wiring['events']}
for cid in ('evt:chest_armoury', 'evt:chest_hoard_1', 'evt:chest_hoard_2', 'evt:chest_prospector', 'evt:chest_vault'):
    ev[cid]['title'] = 'Chest'
ev['evt:door_hoard']['title'] = "The King's door"
ev['evt:door_hoard'].pop('locked_text', None)
ev['evt:door_hoard']['else_effects'] = [{'message': "A stone door behind the throne with the King's own lock in it. It"
                                         " will not move. The Clan King carries its key on him."}]
for gid in ('evt:gate_e', 'evt:gate_w'):
    e = ev[gid]
    e.pop('locked_text', None)
    e['else_effects'] = [{'message': "The King's Gate is barred from within: two iron bars lie across its leaves in"
                          " their brackets. The clan lifts them with levers, one for each bar: one hangs in the"
                          " barracks behind the bunks, the other in the furnace tower beyond the far bank."}]
for lid, var, bar, msg_done in (
        ('evt:lever_a', 'gate_bar_a', 'mover:gate_bar_low', "The lever is down; the King's Gate's lower bar stays up."),
        ('evt:lever_b', 'gate_bar_b', 'mover:gate_bar_high', "The lever is down; the King's Gate's upper bar stays up.")):
    e = ev[lid]
    e.pop('once', None)
    e.pop('sets', None)
    e.pop('text', None)
    which = 'lower' if var == 'gate_bar_a' else 'upper'
    e['effects'] = [
        {'lua': (f"if IsAtLeast(MapVar({var}), 1) then\n    evt.StatusText(\"{msg_done}\")\nelse\n"
                 f"    evt.StatusText(\"The lever drops with a clank; far off, the King's Gate's {which} bar grinds"
                 f" upward.\")\nend")},
        {'set': {'var': {'map_var': var}, 'value': 1}}]
e = ev['evt:shaft_lever']
e.pop('once', None)
e.pop('text', None)
e['effects'] = [
    {'lua': ("if QBit(110031) then\n    evt.StatusText(\"The lever is over; the cage in the shaft runs free.\")\n"
             "else\n    evt.StatusText(\"The lever comes over: a chain runs out with a roar somewhere above. The cage"
             " in the shaft is free.\")\n    evt.CameraShake(0.5, 1.0)\nend")},
    {'qbit': 'escape_shaft_open'}]
ev['evt:cage']['locked_text'] = ("The cage will not move: its counterweight is chained fast. The chain's lever must be"
                                 " near, in the King's hoard.")
for cid, title in (('evt:cage_call', 'Cage lever'), ('evt:cage_call_top', 'Cage lever')):
    ev[cid]['title'] = title
    ev[cid]['locked_text'] = "A bell rings far above, but the cage does not come: its counterweight is chained fast."
ev['evt:exit_x1']['locked_text'] = "The hatch is barred from outside until the shaft's counterweight runs free."
g = ev['evt:gong']
g['source'] = 'platform:gong_1'
g['sources'] = [f'platform:gong_{k}' for k in range(2, 9)]

yio.save(L + 'rooms.yml', rooms)
yio.save(L + 'objects.yml', objects)
yio.save(L + 'wiring.yml', wiring)
print('written')
