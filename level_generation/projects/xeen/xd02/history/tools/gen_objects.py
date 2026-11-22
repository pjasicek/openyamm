# XD-02 Red Dwarf Mines, L4: objects.yml and wiring.yml. Run after gen_rooms.py: python3 gen_objects.py <L4 folder>.
import sys
import math
import yaml
from geom import *

L4 = sys.argv[1]


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


PLANKS_V = S('7trimd', 128, 256)
LAGGING = S('7trimda', 256, 128)
IRON = S('ironn7dmbs', 128, 128)
GATE = S('tdoora', 256, 256, fit=True)
ROCK = S('cwb1', 128, 256)
DEEP = S('c2b', 256, 256)
SKY = S('sky_clo1', 512, 512)
FLOOR = -1152

P = [(7328, 2656), (7328, 3104), (7158, 3512), (6840, 3830), (6432, 4000), (5984, 4000), (5576, 3830), (5258, 3512),
     (5088, 3104), (5088, 2656), (5258, 2248), (5576, 1930), (5984, 1760), (6432, 1760), (6840, 1930), (7158, 2248)]
C = (6208, 2880)
Q = inset_polygon(P, 320)


def bench_mid(side, inset=160):
    a, b = P[side], P[(side + 1) % 16]
    m = lerp(a, b, 0.5)
    return pt(add(m, mul(unit(sub(C, m)), inset)))


obj = {'format': 0}
obj['start'] = {'room': 'room:adit_mouth', 'at': [14120, 3392], 'facing': 'w',
                'notes': 'Just inside the timbered portal, facing into the mine; the daylight is behind the party.'}

# ---------------------------------------------------------------- doors
doors = []


def door(id, opening, kind, **kw):
    d = {'id': id, 'opening': opening, 'kind': kind}
    d.update(kw)
    doors.append(d)


door('door:lamp_room', 'open:station_lamp', 'hinged', state='closed', notes='Plank door to the lamp room.')
door('door:foot_drift', 'open:station_foot', 'hinged', hinge='right', state='closed',
     notes="Plank door across the foot drift's mouth.")
door('door:bunk', 'open:mess_bunk', 'hinged', state='closed', notes='Iron-banded door to the bunk cut.')
door('door:tally', 'open:tally_door', 'hinged', state='closed', notes='Iron-banded door at the top of the tally steps.')
door('door:vent_1', 'open:landing_upper', 'hinged', state='closed', surface=S('bwooda2', 256, 256, fit=True),
     notes='The first ventilation door, its grille rusted open.')
door('door:vent_2', 'open:upper_adit', 'hinged', state='closed', surface=S('bwooda2', 256, 256, fit=True),
     notes='The second ventilation door, into the collapsed adit.')
door('door:chapel', 'open:turntable_chapel', 'slide_left', leaves=2, fold=True, state='closed', speed=96,
     pictures=[[S('t5d1', 128, 256), S('t5d1', 128, 256)]],
     notes="The chapel's carved stone doors: two leaves that fold into their jambs (a hinged door has one leaf).")
door('door:strongroom', 'open:sorting_strongroom', 'slide_down', state='closed', secret=True, speed=64,
     surface=S('cwb1', 128, 256), notes='The dry-stone wall under the chalk mark: it slumps into the floor.')
door('door:web_wall', 'open:galleries_blue', 'slide_up', state='closed', secret=True, speed=64,
     surface=S('web32n735s', 128, 128),
     notes='A wall of thick old web over a thin rock screen: cut, it lifts away.')
door('door:gate_station', 'open:station_trestle', 'slide_down', state='open', speed=192, surface=GATE,
     notes="The trestle gate at the Top Station: down while the car stands here, up (barring the drop) while it is away.")
door('door:gate_turntable', 'open:turntable_trestle', 'slide_down', state='closed', speed=192, surface=GATE,
     notes="The trestle gate at the Turntable: up until the car comes.")
door('door:gate_east', 'open:turntable_east', 'slide_down', state='open', speed=192, surface=GATE,
     notes="The east line's gate at the Turntable (the cart waits behind it).")
door('door:gate_landing', 'open:east_landing', 'slide_down', state='closed', speed=192, surface=GATE,
     notes="The buffer gate at the east line's end.")
door('door:hoist_gate', 'open:rim_hoist', 'slide_up', state='closed', speed=128, surface=S('ironrig04z', 128, 128),
     back_surface=S('ironrig04z', 128, 128),
     notes='The iron grille of the hoist gate on the rim: up only while the cage stands at the rim.')
door('door:mole_rock', 'open:stope_pocket', 'slide_down', state='closed', speed=160, surface=DEEP,
     notes="The rock between the stope and the moles' burrow: it caves in when the rich vein is mined.")
obj['doors'] = doors

# ---------------------------------------------------------------- movers
movers = []
# The trestle car: from the Top Station's gate (its top level with the loading platform, -160) to the Turntable's
# (-384), on the deck. Bed 24 thick 16 over the deck, wheels to 2 over it, plank sides.
car_bottom = -184 + 1792
movers.append({
    'id': 'mover:trestle_car', 'room': 'room:chasm', 'at': [11416, 5184], 'size': [320, 224],
    'floor_height': -1792, 'bottom': car_bottom, 'height': 24, 'travel': [-1584, 0, -224], 'speed': 160,
    'surface': PLANKS_V, 'top_surface': LAGGING,
    'parts': [
        {'at': [11416, 5080], 'size': [320, 16], 'height': 40, 'surface': PLANKS_V, 'top_surface': PLANKS_V},
        {'at': [11416, 5288], 'size': [320, 16], 'height': 40, 'surface': PLANKS_V, 'top_surface': PLANKS_V},
        {'at': [11316, 5096], 'size': [48, 16], 'bottom': car_bottom - 14, 'height': 30, 'surface': IRON},
        {'at': [11516, 5096], 'size': [48, 16], 'bottom': car_bottom - 14, 'height': 30, 'surface': IRON},
        {'at': [11316, 5272], 'size': [48, 16], 'bottom': car_bottom - 14, 'height': 30, 'surface': IRON},
        {'at': [11516, 5272], 'size': [48, 16], 'bottom': car_bottom - 14, 'height': 30, 'surface': IRON},
    ],
    'notes': "The trestle car: a plank flatcar with low sides on iron wheels. It waits at the Top Station's gate, its "
             "deck level with the loading platform, and runs 1600 west and 224 down the trestle to the Turntable's "
             "gate in ten seconds, carrying whoever stands on it (wiring evt:trestle_car)."})
# The east cart: a level run down the drowned line, 1960 south-east.
d = unit((1, -1))
cs = (9234 + d[0] * 152, 4464 + d[1] * 152)
ec_parts = []
for s in (-1, 1):
    side_c = add(cs, mul(left_normal(d), s * 96))
    ec_parts.append({'outline': rect_outline(side_c[0], side_c[1], 288, 16, -45), 'height': 40, 'surface': PLANKS_V,
                     'top_surface': PLANKS_V})
    for t in (-1, 1):
        wc = add(add(cs, mul(d, t * 96)), mul(left_normal(d), s * 80))
        ec_parts.append({'outline': rect_outline(wc[0], wc[1], 48, 16, -45), 'bottom': 2, 'height': 30,
                         'surface': IRON})
movers.append({
    'id': 'mover:east_cart', 'room': 'room:east_line', 'outline': rect_outline(cs[0], cs[1], 288, 208, -45),
    'bottom': 16, 'height': 24, 'travel': [1386, -1386, 0], 'speed': 160, 'surface': PLANKS_V,
    'top_surface': LAGGING, 'parts': ec_parts,
    'notes': "The east line's cart: it waits at the Turntable's gate, its deck level with the Turntable's floor, and "
             "runs 1960 down the drowned line to the buffer landing, a level slide that carries its riders (the build "
             "gives a mover `carry`). It runs only while the turntable points east (wiring evt:east_cart)."})
# The hoist cage at the stope's north-east wall (e2), riding 768 up to the rim's hoist gate.
e2a, e2b = P[2], P[3]
e2m = lerp(e2a, e2b, 0.5)
inw = unit(sub(C, e2m))
alg = unit(sub(e2b, e2a))
cc = add(e2m, mul(inw, 8 + 104))
cage = rect_outline(cc[0], cc[1], 208, 208, math.degrees(math.atan2(alg[1], alg[0])))
parts = []
for su in (-1, 1):
    for sv in (-1, 1):
        c = add(add(cc, mul(alg, su * 96)), mul(inw, sv * 96))
        parts.append({'outline': rect_outline(c[0], c[1], 16, 16, 45), 'height': 240, 'surface': IRON,
                      'top_surface': IRON})
ang = math.degrees(math.atan2(alg[1], alg[0]))
for sv in (-1, 1):  # top frame bars parallel to the wall
    c = add(cc, mul(inw, sv * 96))
    parts.append({'outline': rect_outline(c[0], c[1], 208, 12, ang), 'bottom': 242 - 14, 'height': 14,
                  'surface': IRON, 'top_surface': IRON})
for su in (-1, 1):  # the two closed sides: a top bar and two rails
    c = add(cc, mul(alg, su * 96))
    for b0 in (60, 140, 228):
        parts.append({'outline': rect_outline(c[0], c[1], 12, 184, ang), 'bottom': b0 - 14, 'height': 12,
                      'surface': IRON, 'top_surface': IRON})
movers.append({
    'id': 'mover:hoist', 'room': 'room:stope_floor', 'outline': cage, 'bottom': -14, 'height': 16,
    'travel': [0, 0, 768], 'speed': 96, 'surface': IRON, 'top_surface': S('7trimda', 256, 128), 'parts': parts,
    'notes': "The hoist cage: an iron cage 208 square, open toward the pit and toward the rim's gate, that rides 768 "
             "from the stope floor to the rim in eight seconds (wiring evt:hoist_cage). Waits at the bottom."})
movers.append({
    'id': 'mover:rubble', 'room': 'room:foot_drift', 'at': [11000, 6064], 'size': [384, 136], 'bottom': 386,
    'height': 96, 'travel': [0, 0, -386], 'speed': 640, 'surface': ROCK, 'top_surface': S('cfb1', 128, 128),
    'notes': "The rockfall: rubble hanging in the rotten roof over the drift's north half; it crashes down when the party "
             "first passes (wiring evt:rockfall) and stays as a heap to walk round."})
fall_parts = [
    {'at': [2808, 5040], 'size': [64, 120], 'bottom': 0, 'height': 120, 'surface': ROCK, 'top_surface': ROCK},
    {'at': [2800, 5300], 'size': [48, 96], 'bottom': 0, 'height': 180, 'surface': ROCK, 'top_surface': ROCK},
    {'at': [2830, 5150], 'size': [32, 32], 'bottom': 0, 'height': 360, 'surface': S('d6ebeam', 32, 256)},
    {'at': [2830, 5250], 'size': [32, 32], 'bottom': 0, 'height': 360, 'surface': S('d6ebeam', 32, 256)},
    {'at': [2830, 5200], 'size': [24, 140], 'bottom': 330, 'height': 30, 'surface': S('beamplnh', 256, 32)},
]
movers.append({
    'id': 'mover:fall', 'room': 'room:collapsed_adit', 'at': [2608, 5184], 'size': [336, 448], 'bottom': 0,
    'height': 446, 'travel': [0, 0, -450], 'speed': 48, 'surface': ROCK, 'top_surface': ROCK, 'parts': fall_parts,
    'notes': "The fall: rock to the roof across the adit's west end, two boulders before it and the braced props the "
             "winch pulls; it slides away down the old ore chute under the floor (wiring evt:winch)."})
movers.append({
    'id': 'mover:chain', 'room': 'room:deep_station', 'at': [4240, 4448], 'size': [96, 12], 'bottom': 36,
    'height': 12, 'travel': [0, 0, -52], 'speed': 48, 'surface': IRON, 'top_surface': IRON,
    'notes': 'The chain from the cart to the brake: it drops into the rail bed when the brake key is used.'})
obj['movers'] = movers

# ---------------------------------------------------------------- plates, floors
obj['plates'] = [{'id': 'plate:rockfall', 'room': 'room:foot_drift', 'at': [11360, 5984], 'size': [96, 288],
                  'notes': "Under the rotten props: the rockfall's trigger (the drift's own floor)."}]
obj['floors'] = [
    {'id': 'floor:flooded', 'of': 'room:flooded_working', 'kind': 'water'},
    {'id': 'floor:east_line', 'of': 'room:east_line', 'kind': 'water'},
    {'id': 'floor:green_pool', 'of': 'platform:green_pool', 'kind': 'water'},
    {'id': 'floor:blue_pool', 'of': 'platform:blue_pool', 'kind': 'water'},
]

# ---------------------------------------------------------------- lights
lights = []


def light(id, room, at, height, radius, color, **kw):
    d = {'id': id, 'room': room, 'at': [r(at[0]), r(at[1])], 'height': height, 'radius': radius, 'color': color}
    d.update(kw)
    lights.append(d)


light('light:portal_day', 'room:adit_mouth', (14250, 3392), 300, 1100, [210, 225, 255],
      notes='Daylight through the portal.')
light('light:chasm_lamp', 'room:chasm', (10656, 5184), 120, 520, [255, 160, 80],
      pulse={'intensity': [0.7, 1], 'frequency': 0.6}, notes="A lamp hung on the trestle's middle bent, swaying.")
light('light:signal_trestle', 'room:turntable', (9400, 5184), 360, 260, [80, 255, 90],
      notes='Green lamp over the trestle gate: lit while the points are set for the trestle.')
light('light:signal_east', 'room:turntable', (9110, 4510), 360, 260, [80, 255, 90], on=False,
      notes="Green lamp over the east line's gate: lit while the points are set east.")
light('light:green_pool', 'room:dwarf_shrine', (8512, 3136), 40, 620, [70, 255, 110],
      pulse={'intensity': [0.55, 1], 'radius': [520, 640], 'frequency': 0.35}, notes="The green pool's glow.")
light('light:red_pool', 'room:red_pool_grotto', (6208, 4590), 40, 640, [255, 50, 40],
      pulse={'intensity': [0.55, 1], 'radius': [540, 660], 'frequency': 0.3}, notes="The red pool's glow.")
light('light:gold_pool', 'room:gold_hump', (13008, 1408), 40, 620, [255, 200, 60],
      pulse={'intensity': [0.55, 1], 'radius': [520, 640], 'frequency': 0.4}, notes="The gold pool's glow.")
light('light:blue_pool', 'room:blue_grotto', (2440, 990), 40, 760, [60, 120, 255],
      pulse={'intensity': [0.55, 1], 'radius': [640, 780], 'frequency': 0.25}, notes="The blue pool's glow.")
light('light:west_daylight', 'room:collapsed_adit', (2520, 5184), 260, 900, [210, 225, 255], on=False,
      notes='Daylight at the far end of the west adit once the fall is gone.')
light('light:sorting_lamp_1', 'room:sorting_floor', (12864, 6016), 380, 640, [255, 170, 90],
      pulse={'intensity': [0.85, 1], 'frequency': 1.6}, notes='A lantern hung over the first sorting table.')
light('light:sorting_lamp_2', 'room:sorting_floor', (13056, 6400), 380, 640, [255, 170, 90],
      pulse={'intensity': [0.85, 1], 'frequency': 1.6, 'phase': 0.4}, notes='A lantern over the second table.')
light('light:hoist_lamp', 'room:stope_floor', bench_mid(2, 300), 220, 700, [255, 170, 90],
      notes='The hoist lantern at the foot of the cage.')
for k, (side, fh) in enumerate(((1, -384), (15, -544), (13, -704), (11, -864), (9, -1024))):
    light(f'light:ledge_{side}', 'room:stope_floor', bench_mid(side, 200), 170, 950, [255, 165, 85],
          pulse={'intensity': [0.85, 1], 'frequency': 1.5, 'phase': 0.2 * k},
          notes='A miners\' lantern hung on the ledge rail: the spiral is lit ledge by ledge, the ramps between dark.')
light('light:floor_east', 'room:stope_floor', (6700, 2700), 220, 800, [255, 160, 80],
      pulse={'intensity': [0.8, 1], 'frequency': 1.1, 'phase': 0.5}, notes='A lantern on a prop by the spoil heaps.')
light('light:pit_high', 'room:stope_floor', (6208, 2880), 1150, 1300, [255, 150, 90],
      notes="Lamplight from the rim and the upper ledges caught in the pit's dust: a broad, dim fill high in the void.")
light('light:floor_west', 'room:stope_floor', (5500, 3300), 200, 800, [255, 160, 80],
      pulse={'intensity': [0.8, 1], 'frequency': 1.3}, notes='A lantern on a prop at the spiral\'s foot.')
light('light:west_line_lamp', 'room:west_line', (6500, 5100), 200, 650, [255, 160, 80],
      pulse={'intensity': [0.7, 1], 'frequency': 0.9}, notes='A guttering lamp by the derailed cart.')
light('light:line_head', 'room:east_line', (9400, 4300), 200, 600, [255, 165, 85],
      notes="A lantern at the east line's head, over the waiting cart.")
light('light:line_mid', 'room:east_line', (10050, 3650), 200, 520, [255, 150, 80],
      pulse={'intensity': [0.6, 1], 'frequency': 0.8}, notes='A lamp left on a prop half way down the drowned line.')
light('light:planks', 'room:flooded_working', (10912, 1424), 160, 700, [255, 160, 80],
      notes='A lantern on the walkway junction.')
for k, at in enumerate(((4300, 650), (5200, 1100), (3700, 1350), (4600, 1250), (3500, 600))):
    light(f'light:fungus_{k}', 'room:spider_galleries', at, 60, 720, [150, 230, 140],
          pulse={'intensity': [0.4, 0.9], 'frequency': 0.3, 'phase': 0.33 * k},
          notes='The faint glow of cave fungus in the galleries.')
light('light:car_station', 'room:chasm', (11450, 5184), 180, 460, [255, 165, 85],
      notes='The lantern hung over the car at the Top Station\'s gate.')
light('light:car_turntable', 'room:chasm', (9780, 5184), 180, 460, [255, 165, 85],
      notes='The lantern hung over the car stop at the Turntable\'s gate.')
# gold glints: small yellow pulsing lights in front of each vein
veins = {}
lights_glint = [
    ('light:glint_sorting', 'room:sorting_floor', (12408, 6187), 120, None),
    ('light:glint_rim', 'room:stope_rim', (7602, 3457), 120, None),
    ('light:glint_se', 'room:stope_floor', bench_mid(14, 60), 120, None),
    ('light:glint_sw', 'room:stope_floor', bench_mid(10, 60), 120, None),
    ('light:glint_rich', 'room:stope_floor', add(lerp(P[3], P[4], 0.78), mul(unit(sub(C, lerp(P[3], P[4], 0.78))), 60)),
     120, None),
    ('light:glint_flooded', 'room:flooded_working', (12470, 906), 120, None),
]
for k, (id, room, at, h, fh) in enumerate(lights_glint):
    kw = {'pulse': {'intensity': [0.2, 1], 'radius': [120, 200], 'frequency': 0.9, 'phase': 0.17 * k},
          'notes': 'The glint of a gold seam (dark once the seam is chipped out).'}
    if fh is not None:
        kw['floor_height'] = fh
    light(id, room, at, h, 200, [255, 215, 90], **kw)
obj['lights'] = lights

# ---------------------------------------------------------------- switches
sw = []


def switch(id, room, **kw):
    d = {'id': id, 'room': room}
    d.update(kw)
    sw.append(d)


LEVER = S('7trim9_32', 32, 64)
switch('switch:trestle_station', 'room:top_station', wall=3, along=0.22, floor_height=-160, height=96, size=[32, 64],
       off=LEVER, notes="The car lever on the loading platform beside the gate.")
switch('switch:trestle_turntable', 'room:turntable', wall=0, along=0.86, height=96, size=[32, 64], off=LEVER,
       notes="The call lever beside the Turntable's trestle gate.")
switch('switch:east_turntable', 'room:turntable', wall=14, along=0.86, height=96, size=[32, 64], off=LEVER,
       notes="The call lever beside the east line's gate.")
switch('switch:east_landing', 'room:east_landing', wall=1, along=0.86, height=96, size=[32, 64], off=LEVER,
       notes='The call lever on the buffer landing.')
switch('switch:points', 'room:turntable', block='platform:lever_post', side='e', height=80, size=[24, 48],
       off=S('ironn7dmbs', 128, 128), notes='The points lever on its post beside the disc.')
switch('switch:hoist_rim', 'room:stope_rim', wall=4, along=0.85, height=96, size=[32, 64], off=LEVER,
       notes="The hoist's bell-pull on the rim, beside the gate.")
switch('switch:hoist_floor', 'room:stope_floor', wall=2, along=0.1, height=96, size=[32, 64], off=LEVER,
       notes="The hoist's bell-pull at the foot of the cage.")
switch('switch:brake', 'room:deep_station', wall=2, along=0.62, height=96, size=[48, 48], off=IRON,
       notes="The Deep Line's brake wheel, the chain locked through it.")
VEIN = {'size': [192, 128]}
switch('switch:vein_sorting', 'room:sorting_floor', wall=3, along=0.5, height=112, size=[192, 128],
       off=S('cwb1gold', 128, 256), on='cwb1', notes='Gold vein in the slanted west wall.')
switch('switch:vein_rim', 'room:stope_rim', wall=1, along=0.5, height=112, size=[192, 128],
       off=S('cwb1gold', 128, 256), on='cwb1', notes="Gold vein in the rim's outer wall.")
switch('switch:vein_se', 'room:stope_floor', wall=14, along=0.5, floor_height=-624, height=112, size=[192, 128],
       off=S('cwb1gold', 128, 256), on='cwb1', notes='Gold vein over the south-east ramp.')
switch('switch:vein_sw', 'room:stope_floor', wall=10, along=0.5, floor_height=-944, height=112, size=[192, 128],
       off=S('cwb1gold', 128, 256), on='cwb1', notes='Gold vein over the south-west ramp.')
switch('switch:vein_rich', 'room:stope_floor', wall=3, along=0.78, height=96, size=[160, 160],
       off=S('c1gold', 256, 256), on='c2b',
       notes="The rich vein in the north-north-east wall of the stope floor, beside the moles' burrow.")
switch('switch:vein_flooded', 'room:flooded_working', wall=5, along=0.5, height=112, size=[192, 128],
       off=S('cwb1gold', 128, 256), on='cwb1', notes="Gold vein in the flooded working's south-east wall.")
obj['switches'] = sw

# ---------------------------------------------------------------- chests
CHEST = S('bwoodb1', 256, 256)
obj['chests'] = [
    {'id': 'chest:footlocker_1', 'room': 'room:bunk_cut', 'at': [6992, 8100], 'facing': 's', 'size': [160, 80, 64],
     'surface': CHEST, 'top_surface': PLANKS_V, 'treasure_level': 1, 'random_items': 2,
     'notes': 'Footlocker before the first bunk.'},
    {'id': 'chest:footlocker_3', 'room': 'room:bunk_cut', 'at': [7568, 8100], 'facing': 's', 'size': [160, 80, 64],
     'surface': CHEST, 'top_surface': PLANKS_V, 'treasure_level': 1, 'random_items': 1, 'gold': 40,
     'notes': 'Footlocker before the third bunk.'},
    {'id': 'chest:lamp_room', 'room': 'room:lamp_room', 'at': [12320, 4224], 'facing': 'n', 'treasure_level': 1,
     'random_items': 2, 'notes': 'The chest under the lamp racks.'},
    {'id': 'chest:strongbox', 'room': 'room:tally_room', 'at': [5760, 7200], 'facing': 'e', 'size': [128, 96, 80],
     'surface': IRON, 'top_surface': IRON, 'treasure_level': 2, 'random_items': 2, 'gold': 150,
     'items': ['brake_key'], 'notes': "The clan's strongbox behind the tallymaster's table: the brake key."},
    {'id': 'chest:payroll', 'room': 'room:forgotten_strongroom', 'at': [14100, 6208], 'facing': 'w',
     'size': [160, 112, 96], 'surface': S('bwoodb1', 256, 256), 'top_surface': IRON, 'treasure_level': 3,
     'random_items': 3,
     'gold': 400, 'items': [181], 'notes': "The Red Dwarves' payroll chest, forgotten when the clan came."},
    {'id': 'chest:cocoon', 'room': 'room:spider_galleries', 'at': [3330, 1240], 'facing': 'e', 'size': [176, 96, 96],
     'surface': S('web32n735s', 128, 128), 'top_surface': S('web32n735s', 128, 128), 'treasure_level': 2,
     'random_items': 2, 'notes': "The cocooned miner: his pack, wrapped in web with him."},
]

# ---------------------------------------------------------------- spawns
spawns = []


def spawn(id, room, at, slot, **kw):
    d = {'id': id, 'room': room, 'at': [r(at[0]), r(at[1])], 'slot': slot}
    d.update(kw)
    spawns.append(d)


spawn('spawn:drift_bend', 'room:main_drift', (12736, 4250), 3, tier='a', notes='The first fight, round the bend.')
spawn('spawn:lamp_room', 'room:lamp_room', (12150, 4250), 1, notes='The first clan dwarves.')
spawn('spawn:sorting', 'room:sorting_floor', (12600, 6200), 3, tier='a', notes='Bats off the chutes.')
spawn('spawn:chute_2', 'room:chute_2', (13088, 6912), 3, tier='a', notes='Bats roosting in the middle chute.')
spawn('spawn:foot_drift', 'room:foot_drift', (10560, 5984), 2, tier='a')
spawn('spawn:turntable_n', 'room:turntable', (8300, 5720), 1)
spawn('spawn:turntable_s', 'room:turntable', (8700, 4680), 1)
spawn('spawn:turntable_w', 'room:turntable', (7800, 5300), 2, tier='a', notes="Spiders in the roof over the west line's mouth.")
spawn('spawn:mess_east', 'room:mess_hall', (8700, 6560), 1)
spawn('spawn:mess_tables', 'room:mess_hall', (7700, 6560), 1)
spawn('spawn:mess_leg', 'room:mess_hall', (7360, 7100), 1)
spawn('spawn:bunk_cut', 'room:bunk_cut', (7300, 7870), 1, notes='Asleep at first, in the brief.')
spawn('spawn:rim', 'room:stope_rim', (7500, 3350), 3, tier='a')
spawn('spawn:ledge_sse', 'room:stope_floor', bench_mid(13), 2, tier='a', notes='Spiders lurking at the landing.')
spawn('spawn:ledge_wsw', 'room:stope_floor', bench_mid(9), 2, tier='a', notes='Spiders lurking at the landing.')
spawn('spawn:stope_floor_n', 'room:stope_floor', (6000, 3500), 1)
spawn('spawn:stope_floor_s', 'room:stope_floor', (6300, 2500), 1)
spawn('spawn:galleries_east', 'room:spider_galleries', (5300, 700), 2, tier='a')
spawn('spawn:galleries_mid', 'room:spider_galleries', (4400, 1100), 2, tier='a')
spawn('spawn:deep_station', 'room:deep_station', (4300, 4700), 1, notes='Guards of the line.')
spawn('spawn:flooded', 'room:flooded_working', (11400, 1650), 3, tier='a')
spawn('spawn:repair_niche', 'room:repair_niche', (5600, 5600), 2, tier='a')
spawn('spawn:bunk_niche_item', 'room:bunk_niche_2', (7280, 8350), None, kind='item', treasure_level=1)
spawn('spawn:ore_heap_item', 'room:sorting_floor', (12700, 6608), None, kind='item', treasure_level=1)
for s_ in spawns:
    if s_['slot'] is None:
        del s_['slot']
obj['spawns'] = spawns

# ---------------------------------------------------------------- placed monsters
DWARF, MOLE, SPIDER_B = 229, 412, 401
obj['monsters'] = [
    {'id': 'monster:tallymaster', 'room': 'room:tally_room', 'monster': DWARF, 'at': [5900, 7330], 'facing': 'e',
     'hostile': True, 'group': 1, 'hp': 80, 'name': 'Tallymaster', 'immobile': True,
     'notes': "The clan's tallymaster behind his table (a Dwarven Soldier; the brief's level-10 Mad Dwarf with doubled "
              "hit points)."},
    {'id': 'monster:tally_guard_1', 'room': 'room:tally_room', 'monster': DWARF, 'at': [6300, 7000], 'facing': 'e',
     'hostile': True, 'group': 1},
    {'id': 'monster:tally_guard_2', 'room': 'room:tally_room', 'monster': DWARF, 'at': [6300, 7400], 'facing': 'e',
     'hostile': True, 'group': 1},
    {'id': 'monster:tally_guard_3', 'room': 'room:tally_room', 'monster': DWARF, 'at': [5800, 6980], 'facing': 'e',
     'hostile': True, 'group': 1},
    {'id': 'monster:mole_flood_1', 'room': 'room:flooded_working', 'monster': MOLE, 'at': [11700, 1250],
     'hostile': True, 'group': 2, 'name': 'Tiger Mole', 'notes': 'Surfaced from the water beside the planks.'},
    {'id': 'monster:mole_flood_2', 'room': 'room:flooded_working', 'monster': MOLE, 'at': [12200, 1250],
     'hostile': True, 'group': 2, 'name': 'Tiger Mole'},
    {'id': 'monster:mole_burrow_1', 'room': 'room:mole_pocket', 'monster': MOLE, 'at': [6760, 4090], 'facing': 's',
     'hostile': True, 'group': 3, 'name': 'Tiger Mole',
     'notes': 'Waiting in the burrow behind the rich vein; out when the vein is mined.'},
    {'id': 'monster:mole_burrow_2', 'room': 'room:mole_pocket', 'monster': MOLE, 'at': [6840, 4200], 'facing': 's',
     'hostile': True, 'group': 3, 'name': 'Tiger Mole'},
    {'id': 'monster:cocoon_spider_1', 'room': 'room:spider_galleries', 'monster': SPIDER_B, 'at': [3560, 1120],
     'hostile': True, 'group': 4, 'notes': 'Round the cocoon in the western working (the level-10 spiders).'},
    {'id': 'monster:cocoon_spider_2', 'room': 'room:spider_galleries', 'monster': SPIDER_B, 'at': [3560, 820],
     'hostile': True, 'group': 4},
    {'id': 'monster:cocoon_spider_3', 'room': 'room:spider_galleries', 'monster': SPIDER_B, 'at': [3300, 650],
     'hostile': True, 'group': 4},
]

# ---------------------------------------------------------------- floor items
obj['items'] = [
    {'id': 'item:lamp_scroll', 'room': 'room:lamp_room', 'item': 300, 'at': [12432, 4400], 'floor_height': -60,
     'notes': 'A scroll of Torch Light on the lamp rack.'},
    {'id': 'item:repair_axe', 'room': 'room:repair_niche', 'item': 825, 'at': [5600, 5720], 'floor_height': -8,
     'notes': "The wheelwright's axe on his bench."},
    {'id': 'item:rich_ruby', 'room': 'room:stope_floor', 'item': 203, 'at': [6560, 3780],
     'notes': 'A chip of ruby by the rich vein.'},
    {'id': 'item:cocoon_potion', 'room': 'room:spider_galleries', 'item': 222, 'at': [3560, 1200],
     'notes': "A potion rolled out of the miner's pack."},
    {'id': 'item:mess_bottle', 'room': 'room:mess_hall', 'item': 220, 'at': [8100, 6400], 'floor_height': -336,
     'notes': 'An empty bottle on the long table.'},
]

# ---------------------------------------------------------------- decorations
decos = []
n = [0]


def deco(room, name, at=None, wall=None, along=None, height=None, facing=None, floor_height=None, id=None):
    n[0] += 1
    d = {'id': id or f'deco:{room.split(":")[1]}_{n[0]}', 'room': room, 'decoration': name}
    if at is not None:
        d['at'] = [r(at[0]), r(at[1])]
    if wall is not None:
        d['wall'] = wall
        d['along'] = along
    if height is not None:
        d['height'] = height
    if facing is not None:
        d['facing'] = facing
    if floor_height is not None:
        d['floor_height'] = floor_height
    decos.append(d)


T = 'torch02'
# adit mouth and drift
deco('room:adit_mouth', T, wall='north', along=0.15, height=224)
deco('room:adit_mouth', 'bigbarel', (13420, 3700))
deco('room:adit_mouth', 'smlbarel', (13500, 3720))
deco('room:adit_mouth', '7dec10', (14100, 3110))
deco('room:adit_mouth', 'Bucket', (13900, 3700))
deco('room:main_drift', T, (13040, 3216), height=224)
deco('room:main_drift', T, (12900, 4120), height=200)
deco('room:main_drift', '7dec10', (12620, 3650))
deco('room:main_drift', '6rock01', (12860, 4380))
deco('room:main_drift', '7rock03', (12600, 4500))
# station
deco('room:top_station', T, wall='south', along=0.12, height=240)
deco('room:top_station', T, wall='north', along=0.45, height=240)
deco('room:top_station', 'brzier00', (11960, 4880))
deco('room:top_station', 'bigbarel', (12900, 5540))
deco('room:top_station', 'bigbarel', (12800, 5560))
deco('room:top_station', 'smlbarel', (12880, 5450))
deco('room:top_station', 'floursac', (11800, 5480), floor_height=-160)
deco('room:top_station', 'bag01', (11790, 4880), floor_height=-160)
deco('room:top_station', 'Bucket', (12200, 4800))
# lamp room: unlit lamps on the rack
for k in range(5):
    deco('room:lamp_room', 'nwtrchnf', wall=1, along=0.15 + 0.17 * k, height=200)
deco('room:lamp_room', T, wall='south', along=0.5, height=224)
deco('room:lamp_room', 'smlbarel', (11980, 4500))
# sorting floor
deco('room:sorting_floor', 'dec27', (12864, 6016), height=300, floor_height=-192)
deco('room:sorting_floor', 'dec27', (13056, 6400), height=300, floor_height=-192)
deco('room:sorting_floor', '7dec10', (12720, 6600))
deco('room:sorting_floor', '7dec11', (13400, 6600))
deco('room:sorting_floor', '7dec10', (13450, 5850))
deco('room:sorting_floor', 'Bucket', (12650, 6050))
deco('room:sorting_floor', 'Bucket', (13300, 6300))
# foot drift
deco('room:foot_drift', T, wall=None, at=(11800, 5730), height=200)
deco('room:foot_drift', 'nwtrchnf', (11180, 5840), height=200)
deco('room:foot_bend', T, (9500, 6120), height=200)
deco('room:foot_drift', '6rock02', (10300, 6100))
# turntable
for a in (40, 140, 200, 320):
    deco('room:turntable', T, (8512 + 900 * math.cos(math.radians(a)), 5184 + 900 * math.sin(math.radians(a))),
         height=256)
deco('room:turntable', 'brzier00', (8800, 4760))
deco('room:turntable', 'brzier00', (8960, 4980))
deco('room:turntable', 'nwtrchnf', (9440, 5184), height=330)
deco('room:turntable', 'nwtrchnf', (9120, 4500), height=330)
deco('room:turntable', 'bigbarel', (7800, 4850))
deco('room:turntable', 'bigbarel', (7720, 4960))
deco('room:turntable', '7dec10', (8100, 5900))
# chapel
deco('room:dwarf_shrine', 'brzier00', (8280, 2620))
deco('room:dwarf_shrine', 'brzier00', (8744, 2620))
deco('room:dwarf_shrine', '6rock02', (8900, 3420))
deco('room:dwarf_shrine', '7rock03', (8100, 3380))
deco('room:dwarf_shrine', '6rock02', (8150, 2850))
# mess hall
deco('room:mess_hall', 'brzier00', (8300, 6560))
deco('room:mess_hall', 'brzier00', (7650, 6560))
deco('room:mess_hall', T, wall=0, along=0.85, height=256)
deco('room:mess_hall', T, wall=5, along=0.6, height=256)
deco('room:mess_hall', 'cauld00', (7630, 7100), floor_height=-352)
for (x, y, nm) in ((7800, 6400, 'foodbowl'), (8100, 6720, 'dec32'), (7900, 6720, 'dec36'), (8200, 6400, '7dec48'),
                   (7760, 6720, 'dec37')):
    deco('room:mess_hall', nm, (x, y), floor_height=-336)
deco('room:mess_hall', 'bigbarel', (8880, 6820))
deco('room:mess_hall', 'bigbarel', (8780, 6840))
deco('room:mess_hall', 'trasheap', (7100, 7380))
deco('room:bunk_cut', T, wall=0, along=0.5, height=224)
deco('room:bunk_cut', 'bag_A', (7780, 7900))
deco('room:bunk_cut', 'trasheap', (6950, 7650))
deco('room:tally_room', 'dec02', (5952, 7200), floor_height=-248)
deco('room:tally_room', T, wall=3, along=0.5, height=240)
# west line
deco('room:west_line_landing', T, wall='west', along=0.25, height=224)
deco('room:repair_niche', T, wall='north', along=0.2, height=224)
deco('room:repair_niche', 'Bucket', (5320, 5700))
deco('room:west_line', 'Bucket', (6900, 5300))
deco('room:west_line', '6rock01', (6500, 5080))
deco('room:west_line_upper', 'nwtrchnf', (4700, 5050), height=200)
deco('room:west_line_upper', '7dec11', (4200, 5250))
deco('room:collapsed_adit', T, wall='north', along=0.62, height=224)
deco('room:collapsed_adit', '7rock03', (3100, 5050))
deco('room:collapsed_adit', 'rock10', (3150, 5330))
# rim and stope
deco('room:stope_rim', T, wall=0, along=0.5, height=240)
deco('room:stope_rim', T, wall=3, along=0.4, height=240)
for side, fh in ((15, -544), (13, -704), (11, -864), (9, -1024)):
    deco('room:stope_floor', T, wall=side, along=0.3, height=200, floor_height=fh)
deco('room:stope_floor', T, wall=1, along=0.6, height=200, floor_height=-384)
deco('room:stope_floor', T, wall=2, along=0.85, height=180)
deco('room:stope_floor', '7dec10', (6500, 2300))
deco('room:stope_floor', '7dec11', (5700, 2600))
deco('room:stope_floor', 'rock10', (6650, 2650))
deco('room:stope_floor', '6rock01', (5900, 3700))
deco('room:stope_floor', 'stlmite2', (5600, 3500))
deco('room:stope_floor', 'stlmite2', (6900, 3000))
deco('room:red_pool_grotto', 'stlmite1', (6100, 4250))
deco('room:red_pool_grotto', 'stlmite3', (6450, 4400))
deco('room:deep_station', T, wall=2, along=0.45, height=224)
deco('room:deep_station', T, wall=2, along=0.8, height=224)
deco('room:deep_station', 'smlbarel', (4600, 4800))
deco('room:deep_station', 'smlbarel', (4520, 4820))
deco('room:spider_galleries', 'Corpse08', (3460, 1250))
deco('room:spider_galleries', 'dec29', (4300, 600))
deco('room:spider_galleries', 'dec05', (5000, 1150))
deco('room:spider_galleries', 'mushrm02', (4150, 1350))
deco('room:spider_galleries', 'mushrm05', (3700, 500))
deco('room:spider_galleries', 'mushrm02', (5400, 600))
deco('room:blue_grotto', 'mcryst01', (2860, 1100))
deco('room:blue_grotto', 'mcryst01', (2250, 700))
deco('room:blue_grotto', 'mcryst01', (2100, 1250))
# flooded working
deco('room:east_landing', T, wall=1, along=0.5, height=200)
deco('room:flooded_working', 'mushrm01', (10300, 1700))
deco('room:flooded_working', 'mushrm03', (10450, 1100))
deco('room:flooded_working', 'stlmite1', (12400, 900))
deco('room:flooded_working', 'stlmite3', (10800, 700))
deco('room:gold_hump', 'mushrm03', (13150, 1650))
obj['decorations'] = decos

obj['exits'] = [
    {'id': 'exit:x1', 'room': 'room:adit_mouth', 'wall': 'east', 'size': [512, 352], 'surface': SKY,
     'to': 'exit:x1_adit', 'notes': 'The portal: daylight and the hills north of Vertigo.'},
    {'id': 'exit:x4', 'room': 'room:collapsed_adit', 'wall': 'west', 'size': [320, 352], 'surface': SKY,
     'to': 'exit:x4_adit', 'notes': 'The far end of the west adit, open to the sky once the fall is gone.'},
    {'id': 'exit:deep', 'room': 'room:deep_mouth', 'wall': 1, 'size': [256, 288],
     'surface': S('c2b', 256, 256), 'to': 'exit:deep_mine',
     'notes': "The Deep Line's mouth: the cart's way down to the Deep Mine."},
]
obj['notes'] = ("Objects of the L4 brief (written by output/studio_cal/xd02/tools/gen_objects.py). Stand-ins: "
                "Mad Dwarves are MM7 Dwarves (Dwarven Soldier, level 10), the Tallymaster one of them with hp 80 and a "
                "name; Tiger Moles are Troglodyte Drones (412, level 9); the cocoon's level-10 spiders are Venomous "
                "Spiders (401, level 8); slots: 1 Dwarf, 2 Spider, 3 Bat. The brake key is the plain Key 2111.")
with open(f'{L4}/objects.yml', 'w') as f:
    yaml.safe_dump(obj, f, sort_keys=False, default_flow_style=None, width=120, allow_unicode=True)

# ---------------------------------------------------------------- wiring
ev = []


def event(id, **kw):
    d = {'id': id}
    d.update(kw)
    ev.append(d)


for dn, title in (('lamp_room', 'Plank door'), ('foot_drift', 'Plank door'), ('bunk', 'Iron-banded door'),
                  ('tally', 'Iron-banded door'), ('vent_1', 'Ventilation door'), ('vent_2', 'Ventilation door'),
                  ('chapel', 'Carved stone doors')):
    event(f'evt:door_{dn}', preset='door', source=f'door:{dn}', title=title)
event('evt:strongroom_wall', preset='door', source='door:strongroom', title='Dry-stone wall', action='open',
      text='The old dry-stone wall slumps into the floor: a vault behind it.')
event('evt:web_wall', preset='door', source='door:web_wall', title='Thick old web', action='open',
      text='You cut the old web away; the thin rock screen behind it lifts. Blue light beyond.')
TRESTLE = ['mover:trestle_car', 'door:gate_station', 'door:gate_turntable']
not_east = {'not': {'map_var': 'turntable_east'}}
locked_trestle = 'The points at the Turntable are set for the east line: the car will not run the trestle.'
event('evt:trestle_car', preset='switch', source='mover:trestle_car', title='Trestle car', condition=not_east,
      toggles=TRESTLE, locked_text=locked_trestle, text='The car rolls out over the chasm.')
event('evt:trestle_station', preset='switch', source='switch:trestle_station', title='Car lever',
      condition=not_east, toggles=TRESTLE, locked_text=locked_trestle, text='The car rumbles along the trestle.')
event('evt:trestle_turntable', preset='switch', source='switch:trestle_turntable', title='Car lever',
      condition=not_east, toggles=TRESTLE, locked_text=locked_trestle, text='The car rumbles along the trestle.')
EAST = ['mover:east_cart', 'door:gate_east', 'door:gate_landing']
is_east = {'map_var': 'turntable_east'}
locked_east = 'The points at the Turntable are set for the trestle: the cart will not run the east line.'
event('evt:east_cart', preset='switch', source='mover:east_cart', title='Mine cart', condition=is_east,
      toggles=EAST, locked_text=locked_east, text='The cart splashes off down the drowned line.')
event('evt:east_turntable', preset='switch', source='switch:east_turntable', title='Cart lever', condition=is_east,
      toggles=EAST, locked_text=locked_east, text='The cart rumbles along the east line.')
event('evt:east_landing', preset='switch', source='switch:east_landing', title='Cart lever', condition=is_east,
      toggles=EAST, locked_text=locked_east, text='The cart rumbles along the east line.')
event('evt:points', preset='script', source='switch:points', title='Points lever', condition=is_east,
      effects=[{'set': {'var': {'map_var': 'turntable_east'}, 'value': 0}}, {'lights_on': 'light:signal_trestle'},
               {'lights_off': 'light:signal_east'}],
      text='The turntable grinds round: the points are set for the trestle. A green lamp lights over its gate.',
      else_effects=[{'set': {'var': {'map_var': 'turntable_east'}, 'value': 1}}, {'lights_on': 'light:signal_east'},
                    {'lights_off': 'light:signal_trestle'},
                    {'text': "The turntable grinds round: the points are set for the east line. A green lamp lights "
                             "over its gate."}],
      notes='set:turntable: toggles turntable_east (the trestle by default); the green lamps show which line is live.')
HOIST = ['mover:hoist', 'door:hoist_gate']
event('evt:hoist_cage', preset='switch', source='mover:hoist', title='Hoist cage', toggles=HOIST,
      sets={'map_var': 'hoist_used'}, text='The cage jerks and rides up the shaft on its creaking cable.')
event('evt:hoist_rim', preset='switch', source='switch:hoist_rim', title="Hoist bell-pull",
      condition={'map_var': 'hoist_used'}, toggles=HOIST,
      locked_text='The bell rings far below; nobody answers. The cage is braked at the bottom.',
      text='The hoist cable sings.')
event('evt:hoist_floor', preset='switch', source='switch:hoist_floor', title="Hoist bell-pull",
      condition={'map_var': 'hoist_used'}, toggles=HOIST,
      locked_text='The cage is here; climb in and work its lever.', text='The hoist cable sings.')
VEINS = [('sorting', 120, 'A glinting seam of gold: you chip out a handful of nuggets.'),
         ('rim', 90, 'A thin seam of gold over the drop: you chip it out.'),
         ('se', 110, 'Gold glints in the ramp wall: you chip out the seam.'),
         ('sw', 80, 'A seam of gold in the ramp wall: you chip it out.'),
         ('flooded', 110, 'A seam of gold above the water line: you chip it out.')]
for name, gold, text in VEINS:
    event(f'evt:vein_{name}', preset='switch', source=f'switch:vein_{name}', title='Gold vein', once=True,
          effects=[{'gold': gold}, {'lights_off': f'light:glint_{name}'}], text=text)
event('evt:vein_rich', preset='switch', source='switch:vein_rich', title='Rich gold vein', once=True,
      opens=['door:mole_rock'],
      effects=[{'gold': 200}, {'lights_off': 'light:glint_rich'}, {'lua': 'evt.CameraShake(0.7, 1.5)'}],
      text='You chip out a fat seam of gold - and the rock beside it caves in. Something was digging toward you.',
      notes="set:rich_vein: the richest seam; the burrow behind it opens and the two tiger moles come out.")
POOLS = [('red', 'BaseMight', 'Might', 11021, 'The red water burns going down. (+2 Might, permanent)'),
         ('green', 'BaseEndurance', 'Endurance', 11022, 'The green water is cold as the deep rock. (+2 Endurance, permanent)'),
         ('gold', 'BaseAccuracy', 'Accuracy', 11023, 'The golden water tastes of metal. (+2 Accuracy, permanent)'),
         ('blue', 'BaseIntellect', 'Intellect', 11024, 'The blue water is sweet and very clear. (+2 Intellect, permanent)')]
for colour, var, stat, bit, text in POOLS:
    event(f'evt:pool_{colour}', preset='script', source=f'platform:{colour}_pool',
          title=f'Drink from the {colour} pool', condition={'lua': f'not IsPlayerBitSet(PlayerBit({bit}))'},
          effects=[{'add': {'var': var, 'value': 2}}, {'lua': f'SetPlayerBit(PlayerBit({bit}))'}], text=text,
          else_effects=[{'text': 'The water tastes of nothing.'}],
          notes=f"poi:{colour}_pool: +2 {stat} once for each character (a per-character bit, {bit}, set by Lua: no "
                "word says a player bit).")
event('evt:tablet', preset='script', source='platform:chapel_tablet', title="The Red Dwarves' tablet",
      effects=[{'message': "Carved in the old runes, the faces smashed above them: RED FOR THE ARM. GREEN FOR THE BACK. "
                           "GOLD FOR THE EYE. BLUE FOR THE MIND. THE BLUE SLEEPS BEHIND THE SILK."}])
for c in ('footlocker_1', 'footlocker_3', 'lamp_room', 'strongbox', 'payroll', 'cocoon'):
    titles = {'footlocker_1': 'Footlocker', 'footlocker_3': 'Footlocker', 'lamp_room': 'Chest',
              'strongbox': "The clan's strongbox", 'payroll': 'Payroll chest', 'cocoon': 'Web-wrapped bundle'}
    e = {'preset': 'chest', 'source': f'chest:{c}', 'title': titles[c]}
    if c == 'strongbox':
        e['text'] = 'Under the tally slates: a heavy iron key stamped with a cart wheel. The brake key of the Deep Line.'
    event(f'evt:chest_{c}', **e)
event('evt:rockfall', preset='script', trigger='step', source='plate:rockfall', once=True, opens=['mover:rubble'],
      effects=[{'damage': {'amount': 7, 'kind': 'physical'}}, {'lua': 'evt.CameraShake(1.0, 1.2)'}],
      text='The rotten props give way: rock thunders down from the roof!',
      notes='set:rockfall: once; about 2d6 to the whole party (7), the rubble heap left in the drift.')
event('evt:winch', preset='switch', source='platform:winch', title='Winch', once=True, opens=['mover:fall'],
      effects=[{'qbit': 'x4_adit_open'}, {'lights_on': 'light:west_daylight'}, {'lua': 'evt.CameraShake(1.2, 2.5)'}],
      text='You crank the winch: the props come out, and with a long roar the whole fall slides away down the old ore '
           'chute. Daylight shows at the end of the adit.',
      notes='set:west_adit_winch: once; the fall goes, the X4 exit opens for good (qbit x4_adit_open).')
event('evt:brake', preset='switch', source='switch:brake', title='Brake wheel',
      condition={'item': 'brake_key', 'consume': True}, once=True,
      opens=['mover:chain'], sets={'qbit': 'deep_line_unchained'},
      text='The brake key turns: the chain falls away from the Deep Line cart. It is free to run.',
      locked_text='The cart is chained to its brake; the chain is locked through the wheel.',
      notes='set:unchain_deep_cart: the brake key (consumed) frees the cart; the qbit opens the Deep Line exit.')
event('evt:exit_x1', preset='exit', source='exit:x1', title='Daylight: the hills north of Vertigo')
event('evt:exit_x4', preset='exit', source='exit:x4', title='The west adit', condition={'qbit': 'x4_adit_open'},
      locked_text='Rock fills the adit to the roof.')
event('evt:exit_deep', preset='exit', source='exit:deep', title='The Deep Line',
      condition={'qbit': 'deep_line_unchained'},
      locked_text='The Deep Line drops away into the dark; the cart that runs it is chained to its brake.',
      text='You release the brake: the cart runs down the Deep Line into the dark.')
event('evt:clan_sign', preset='text', source='panel:clan_sign', title='Painted warning',
      text='Skulls daubed on a board: MAD DWARF CLAN. DIG ELSEWHERE.')
event('evt:chalk_mark', preset='text', source='panel:chalk_mark', title='Chalk mark',
      text='An old Red Dwarf mark in chalk: a strongbox, and an arrow pointing into the wall.')
event('evt:clan_hostile', preset='script', trigger='load',
      effects=[{'lua': 'evt.SetMonsterRelation(229, 0, 4); evt.SetMonsterRelation(230, 0, 4); '
                       'evt.SetMonsterRelation(231, 0, 4)'}],
      notes="The Mad Dwarf Clan is hostile: MM7's Dwarf family (the stand-in) is the party's ally in hostile.txt, and no "
            "word says a map's own relations or a spawn's hostility, so a load event sets the three Dwarf rows hostile "
            "to the party (evt.SetMonsterRelation). Gone with a real Mad Dwarf row.")
wiring = {'format': 0, 'variables': ['turntable_east', 'hoist_used'], 'events': ev,
          'notes': "Every mechanism is a preset with conditions and effects. Lua only for what no word says: the pools' "
                   "per-character bits (IsPlayerBitSet / SetPlayerBit), the camera shakes (evt.CameraShake) and the "
                   "clan's hostility (evt.SetMonsterRelation on load)."}
with open(f'{L4}/wiring.yml', 'w') as f:
    yaml.safe_dump(wiring, f, sort_keys=False, default_flow_style=None, width=120, allow_unicode=True)
print('objects and wiring written:', len(doors), 'doors', len(movers), 'movers', len(lights), 'lights', len(decos),
      'decorations', len(ev), 'events')
