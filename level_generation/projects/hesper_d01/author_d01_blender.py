"""Author D1 Starport Terminal (hes_d01.blv) in Blender, with the Hesper indoor kit (hesper_stage/blv_kit.py).

Run headless:  blender --background --factory-startup --python author_d01_blender.py
Rooms, links, markers and lights are the d1 plan of design/kreegan_world/zone1/dungeons/make_dungeon_plans.py (the
rooms are their interiors, 64 apart: the walls' thickness); this script adds the walls and their openings, the doors,
the freight lift, the Power Plant's pit and catwalks, the stairs, the counters and consoles, and the decorations.
Writes source/hes_d01.glb, hes_d01.geometry.yml, hes_d01.semantic.json and hes_d01.blend.
"""
import importlib.util
import os
import math
import sys
from pathlib import Path

ROOT = Path('/home/pjasicek/github/OpenYAMM')
sys.path.insert(0, str(ROOT / 'level_generation/projects/hesper_stage'))
import blv_kit  # noqa: E402
from blv_kit import (Wall, box, ceiling, flight, floor, plaque, prism, rect_minus, chamfer_rect, clip_to,
                     hip_ceiling, ramp, flight_along)  # noqa: E402

PROJECT = ROOT / 'level_generation/projects/hesper_d01'
PLANS = ROOT / 'design/kreegan_world/zone1/dungeons/make_dungeon_plans.py'
spec = importlib.util.spec_from_file_location('plans', PLANS)
plans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plans)
PLAN = plans.d1
R = {r['id']: r for r in PLAN.rooms}
PLAN_ROOMS = dict(R)                                    # R below loses the halls it splits into sectors

ROLE = {'wall': 'hcpanel', 'recess': 'hcrecess', 'hazard': 'hchazard', 'trim': 'hctrim', 'gold': 'hogold',
        'girder': 'hcgirder', 'strip': 'hcstripd', 'strip_red': 'hcstripr', 'floor': 'hcfloor', 'grille': 'hcgrille',
        'ceiling': 'hcceiling', 'door': 'hcdoor', 'shutter': 'hcshutter', 'console': 'hcconsole', 'sign': 'hcsign',
        'board': 'hcboard', 'counter': 'hccounter', 'convey': 'hcconvey', 'catwalk': 'hccatwalk',
        'bagside': 'hcbagside', 'luggage': 'hcluggage', 'tools': 'hitools',
        'pitwall': 'hcpitwall', 'machine': 'hcmachine', 'gener': 'hcgener', 'window': 'hcwindow',
        'scorch': 'hcscorch', 'ash': 'hashdrift', 'glassdoor': 'hodoorgl', 'marker': 'hcconsole',
        'patch': 'hcpatch'}
b = blv_kit.Builder('hes_d01.blv', ROLE, PROJECT / 'source',
                    role_scale={'wall': 1.5, 'floor': 1.5, 'ceiling': 2.0, 'pitwall': 1.5})
T = blv_kit.THICK

SMALL = [(0, 16, 'trim'), (16, 224, 'wall'), (224, 256, 'strip')]
TALL = [(0, 16, 'trim'), (16, 352, 'wall'), (352, 384, 'strip')]
VEST = [(0, 16, 'trim'), (16, 480, 'wall'), (480, 512, 'strip')]
HALL = [(0, 16, 'trim'), (16, 480, 'wall'), (480, 512, 'gold'), (512, 736, 'recess'), (736, 768, 'strip')]
STAIR = [(0, 16, 'trim'), (16, 1068, 'wall'), (1068, 1100, 'strip')]
SHAFT = [(0, 32, 'hazard'), (32, 1056, 'girder'), (1056, 1088, 'strip')]
PIT = [(0, 480, 'pitwall'), (480, 512, 'hazard'), (512, 1184, 'pitwall'), (1184, 1216, 'strip')]
PLANT = [(0, 32, 'hazard'), (32, 672, 'pitwall'), (672, 704, 'strip')]
DRONE = [(0, 16, 'trim'), (16, 576, 'wall'), (576, 640, 'girder')]

holes = {}                # room -> side -> [(a0, a1, z0, z1)] (z relative to the room's floor)
openings = []             # (owner, other, axis, plane, a0, a1, z0, z1, toward)
DOORS = {}                # name -> door id
door_specs = []           # (name, owner, axis, plane, a0, a1, z0, z1, toward, role, event, flags)


def connect(owner, owner_side, other, centre, width, height, z=None, door=None, event=0, flags=(), role='door'):
    """An opening `width` x `height` from owner's `owner_side` wall into `other`, the reveal owned by owner; a door
    leaf in it when `door` names one."""
    o, t = R[owner], R[other]
    z = o['z'] if z is None else z
    a0, a1 = centre - width / 2, centre + width / 2
    side_of_other = {'south': 'north', 'north': 'south', 'west': 'east', 'east': 'west'}[owner_side]
    if owner_side in ('south', 'north'):
        plane = o['y'] if owner_side == 'south' else o['y'] + o['h']
        axis, toward = 'y', (-1 if owner_side == 'south' else 1)
    else:
        plane = o['x'] if owner_side == 'west' else o['x'] + o['w']
        axis, toward = 'x', (-1 if owner_side == 'west' else 1)
    holes.setdefault(owner, {}).setdefault(owner_side, []).append((a0, a1, z - o['z'], z - o['z'] + height))
    holes.setdefault(other, {}).setdefault(side_of_other, []).append((a0, a1, z - t['z'], z - t['z'] + height))
    openings.append((owner, other, axis, plane, a0, a1, z, z + height, toward))
    if door:
        DOORS[door] = len(DOORS) + 1
        door_specs.append((door, owner, axis, plane, a0, a1, z, z + height, toward, role, event, list(flags)))


# --- Rooms: the plan's, the halls split into sectors --------------------------------------------------------------
def sub(rid, x0, y0, x1, y1, base=None, **extra):
    src = R[base or rid]
    R[rid] = dict(src, id=rid, x=x0, y=y0, w=x1 - x0, h=y1 - y0, **extra)


c = R['concourse']
for rid, x0, x1 in (('concourse_w', 1200, 3045), ('concourse_c', 3045, 4891), ('concourse_e', 4891, 6736)):
    sub(rid, x0, c['y'], x1, c['y'] + c['h'], 'concourse')
p = R['plant']
sub('plant_s', 2900, 300, 5136, 800, 'plant')
sub('plant_n', 2900, 2700, 5136, 3300, 'plant')
sub('plant_e', 5136, 300, 5636, 3300, 'plant')
sub('plant_pit', 2900, 800, 5136, 2700, 'plant', z=-1280, ceiling=1216)
dc = R['dronecontrol']
sub('dc_s', 600, 2200, 2836, 2700, 'dronecontrol')
sub('dc_n', 600, 2700, 2836, 3800, 'dronecontrol')
del R['concourse'], R['plant'], R['dronecontrol'], R['freight_bottom']

# --- The connections (the plan's links) -----------------------------------------------------------------------------
connect('vestibule', 'east', 'concourse_w', 4100, 384, 448)                       # the inner glass doors, jammed open
connect('customs', 'west', 'concourse_e', 4100, 384, 320)                         # the security gate
connect('security', 'west', 'customs', 4300, 256, 256, door='security', event=31)
connect('claim', 'north', 'concourse_c', 3600, 384, 256, door='shutter', role='shutter')
connect('belts', 'west', 'claim', 2124, 384, 256)
connect('sorting', 'west', 'belts', 2124, 256, 256, door='sorting', event=30)
connect('lost', 'east', 'claim', 1950, 256, 256, door='lost', event=13, flags=('secret',), role='wall')
connect('sorting', 'east', 'freight', 1900, 384, 320, z=0)                        # the lift gate, jammed open
connect('service', 'east', 'freight', 1950, 384, 320)
connect('plant_e', 'east', 'service', 1950, 384, 320)
connect('plant_n', 'west', 'dc_n', 3000, 384, 384, door='seal', role='shutter')
connect('maintenance', 'south', 'concourse_w', 2600, 256, 256, door='maintenance', event=29)
connect('stairhall', 'south', 'concourse_c', 4000, 512, 448)
connect('stairhall', 'north', 'tower', 4000, 384, 320, z=768)



AMBIENT = {'vestibule': 20, 'concourse_w': 25, 'concourse_c': 25, 'concourse_e': 25, 'customs': 25, 'security': 20,
           'claim': 27, 'belts': 26, 'lost': 29, 'sorting': 26, 'freight': 25,
           'maintenance': 18, 'stairhall': 25, 'service': 26, 'plant_s': 26, 'plant_n': 26, 'plant_e': 26,
           'plant_pit': 26, 'dc_s': 25, 'dc_n': 25, 'tower': 20}
BANDS = {'vestibule': VEST, 'customs': TALL, 'sorting': TALL, 'stairhall': STAIR,
         'freight': SHAFT, 'plant_pit': PIT, 'plant_s': PLANT, 'plant_n': PLANT, 'plant_e': PLANT,
         'dc_s': DRONE, 'dc_n': DRONE,
         'concourse_w': HALL, 'concourse_c': HALL, 'concourse_e': HALL}
FLOORS = {'vestibule': 'ash', 'maintenance': 'grille', 'freight': 'hazard', 'plant_s': 'catwalk',
          'plant_n': 'catwalk', 'plant_e': 'catwalk', 'dc_s': 'grille', 'dc_n': 'grille', 'security': 'grille'}
# Sides open to a sibling sector of the same hall (no wall: a portal stands there).
OPEN = {'concourse_w': ('east',), 'concourse_c': ('west', 'east'), 'concourse_e': ('west',),
        'plant_s': ('north', 'east'), 'plant_n': ('south', 'east'), 'plant_e': ('west',),
        'plant_pit': ('north', 'south', 'east'),
        'dc_s': ('north',), 'dc_n': ('south',)}
CHAMFER = {'vestibule': 220, 'customs': 180, 'security': 200, 'claim': 280, 'sorting': 160,
           'maintenance': 180, 'concourse_w': {'sw': 240, 'nw': 240},
           'concourse_e': {'se': 200, 'ne': 200}}
HIPS = {'vestibule': 448, 'customs': 320, 'claim': 480,
        'concourse_w': 576, 'concourse_c': 576, 'concourse_e': 576}
CUSTOM_FLOOR = {'sorting', 'stairhall', 'plant_pit', 'tower', 'freight'}
R['stairhall']['ceiling'] = 1280
for rid, r in R.items():
    if rid in ('tower',):
        continue
    x0, y0, x1, y1 = r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']
    b.box_room(rid, x0, y0, x1, y1, r['z'], r['ceiling'], BANDS.get(rid, SMALL), holes.get(rid, {}),
               floor_role=FLOORS.get(rid, 'floor'), ambient=AMBIENT[rid], open_sides=OPEN.get(rid, ()),
               chamfer=CHAMFER.get(rid))
    if rid in HIPS:
        spring = HIPS[rid]
        b.rooms[rid] = clip_to([pn for pn in b.rooms[rid] if pn[2][2] >= 0], None,
                              below=((0, 0, spring), (0, 0, 1)))
        footprint = chamfer_rect(x0, y0, x1, y1, CHAMFER.get(rid, 0))
        b.rooms[rid] += hip_ceiling(footprint, spring, r['z'] + r['ceiling'], 'ceiling')
    if rid in CUSTOM_FLOOR:                     # these lay their own floors below
        b.rooms[rid][:] = [pn for pn in b.rooms[rid] if not (pn[2] == (0, 0, 1) and abs(pn[0][0][2] - r['z']) < 1)]

# A 45-degree service-corridor dogleg retains both original door mouths.
service_shape = [(5700, 1700), (6100, 1700), (6260, 1860), (7060, 1860),
                 (7220, 1700), (7664, 1700), (7664, 2200), (5700, 2200)]
b.poly_room('service', service_shape, -768, 384, TALL,
            {5: [(58, 442, 0, 320)], 7: [(58, 442, 0, 320)]}, ambient=AMBIENT['service'])
# The floor below the lift is recessed by the platform's thickness; both stops meet their landing exactly.
b.rooms['freight'] += floor(7728, 1400, 8728, 2400, -800, 'hazard')
b.bounds['freight'] = (7728, 1400, 8728, 2400, -801, 320)
# A ceiling following the tower flights keeps a full party-height gap over every tread.
plane = ((0, 5164, 512), (0, -768 / 2236, 1))
b.rooms['stairhall'] = clip_to([pn for pn in b.rooms['stairhall'] if pn[2][2] >= 0], None, below=plane)
b.rooms['stairhall'].append(([(3500, 5164, 512), (4500, 5164, 512),
                              (4500, 7400, 1280), (3500, 7400, 1280)], 'ceiling', (0, 768 / 2236, -1)))


def portal_x(front, back, x, y0, y1, z0, z1):
    b.portal(front, back, [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)])


def portal_y(front, back, y, x0, x1, z0, z1):
    b.portal(front, back, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)])


portal_x('concourse_w', 'concourse_c', 3045, 3100, 5100, 0, PLAN_ROOMS['concourse']['ceiling'])
portal_x('concourse_c', 'concourse_e', 4891, 3100, 5100, 0, PLAN_ROOMS['concourse']['ceiling'])
portal_y('dc_s', 'dc_n', 2700, 600, 2836, -768, -128)
portal_y('plant_s', 'plant_pit', 800, 2900, 5136, -768, -64)
portal_y('plant_pit', 'plant_n', 2700, 2900, 5136, -768, -64)
portal_x('plant_s', 'plant_e', 5136, 300, 800, -768, -64)
portal_x('plant_pit', 'plant_e', 5136, 800, 2700, -768, -64)
portal_x('plant_n', 'plant_e', 5136, 2700, 3300, -768, -64)

# The openings' reveals, portals and door leaves.
for owner, other, axis, plane, a0, a1, z0, z1, toward in openings:
    b.opening(owner, other, axis, plane, a0, a1, z0, z1, toward=toward)
for name, owner, axis, plane, a0, a1, z0, z1, toward, role, event, flags in door_specs:
    mid = plane + toward * (T / 2)
    lo, hi = (a0, mid - 8, z0), (a1, mid + 8, z1)
    if axis == 'x':
        lo, hi = (mid - 8, a0, z0), (mid + 8, a1, z1)
    panels = box(lo, hi, role, top='trim')
    b.door(name, owner, panels, DOORS[name], int(z1 - z0), direction=(0, 0, 1), event=event, flags=flags)

# --- Vestibule: the exit's glass doors, the relay post ------------------------------------------------------------
v = R['vestibule']
west = Wall('x', 0, (1, 0, 0))
b.rooms['vestibule'][:] = [pn for pn in b.rooms['vestibule'] if not (pn[2] == (1, 0, 0))]
b.rooms['vestibule'] += blv_kit.banded(west, v['y'] + 220, v['y'] + v['h'] - 220, [(0, 16, 'trim'), (16, 416, 'wall'), (416, 448, 'strip')], [(3908, 4292, 0, 448)])
face, jambs = blv_kit.recessed_door(west, 4100, 0, 384, 448, 'glassdoor', depth=16)
b.rooms['vestibule'] += jambs
b.trigger('exit_doors', 'vestibule', face, 2)
b.decoration('hes_relay_post', 900, 3600, 0, 0, event=3)
b.decoration('hes_fallen_plates', 500, 4500, 0, 30)

# --- Concourse: the departure board, check-in counters, arch-row pillars, the shutter lever ---------------------------
north = Wall('y', 5100, (0, -1, 0))
board = plaque(north, 4200, 300, 512, 256, 'board', out=8)
b.trigger('departure_board', 'concourse_c', board[:1], 5, cog=110)
b.rooms['concourse_c'] += board[1:]
for x0, x1, rid in ((1700, 2900, 'concourse_w'), (5100, 6400, 'concourse_e')):
    b.rooms[rid] += box((x0, 4860, 0), (x1, 4960, 110), 'counter', top='trim')
for x, rid in ((2981, 'concourse_w'), (4827, 'concourse_c')):
    for y in (3164, 4908):
        b.rooms[rid] += box((x - 64, y, 0), (x + 64, y + 128, 768), 'recess')
lever = plaque(Wall('y', 3100, (0, 1, 0)), 3300, 96, 96, 128, 'console', out=10)
b.trigger('shutter_lever', 'concourse_c', lever, 4)
for x, y, f, name in ((2200, 3700, 20, 'hes_baggage_cart'), (3700, 4400, 200, 'hes_baggage_cart_over'),
                      (5600, 3500, 70, 'hes_baggage_cart'), (6200, 4500, 140, 'hes_baggage_cart_over'),
                      (4300, 3600, 0, 'hes_drone_wreck'), (2000, 4400, 90, 'hes_drone_wreck')):
    b.decoration(name, x, y, 0, f)
for k in range(6):
    b.decoration('hes_bench', 2300 + (k % 3) * 1500, 3900 if k < 3 else 4300, 0, 0)

# --- Customs: the counter, the scanner arch, the console --------------------------------------------------------------
b.rooms['customs'] += box((7450, 3500, 0), (7550, 4700, 110), 'counter', top='trim')
for y in (3940, 4260):
    b.rooms['customs'] += box((7050, y - 24, 0), (7110, y + 24, 320), 'gold')
b.rooms['customs'] += box((7050, 3916, 296), (7110, 4284, 320), 'gold', top='gold', bottom='gold')
console = plaque(Wall('y', 3400, (0, 1, 0)), 7200, 64, 128, 128, 'console', out=10)
b.trigger('customs_console', 'customs', console, 6)
b.decoration('hes_fallen_plates', 7900, 4600, 0, 60)
b.decoration('hes_colonial_locker', 9300, 4500, 0, 180, event=7)                        # chest A

# --- Baggage Claim, the Belt Tunnel and Lost Luggage ----------------------------------------------------------------
# Two claim carousels (octagonal belts round a ceramic island), bags heaped where the belts stopped, the lockers on the
# south wall; a conveyor along the tunnel to sorting; shelves of unclaimed luggage in the secret room.
cl = R['claim']
CY = cl['y'] + cl['h'] / 2
for x in (cl['x'] + 700, cl['x'] + cl['w'] - 700):
    b.rooms['claim'] += prism(x, CY, 420, 0, 72, 'bagside', top='convey')
    b.rooms['claim'] += prism(x, CY, 240, 72, 136, 'counter', top='trim')
for x, y in ((2620, 1620), (2380, 2500), (3060, 2650), (3780, 1560), (4040, 2600), (3480, 2560)):
    b.decoration('hes_luggage_pile', x, y, 0, (x * 7) % 360)
b.decoration('hes_baggage_cart', 3200, 1500, 0, 90)
b.decoration('hes_baggage_cart_over', 3300, 2850, 0, 200)
b.decoration('hes_colonial_locker', 2300, 1340, 0, 0, event=9)
b.decoration('hes_colonial_locker', 4100, 1340, 0, 0, event=10)
bt = R['belts']
b.rooms['belts'] += box((bt['x'], 2024, 0), (bt['x'] + bt['w'], 2224, 32), 'bagside', top='convey')
lo = R['lost']
for wall, a in ((Wall('y', lo['y'] + lo['h'], (0, -1, 0)), lo['x'] + 518), (Wall('x', lo['x'], (1, 0, 0)), 1950)):
    b.rooms['lost'] += plaque(wall, a, 0, 640, 320, 'luggage', out=96)
b.decoration('hes_luggage_pile', 1500, 1650, 0, 40)
b.decoration('hes_colonial_locker', 1400, 1950, 0, 90, event=11)

# --- Sorting Floor: two conveyor pits, the arcing plate ---------------------------------------------------------------
so = R['sorting']
PITS = [(5900, 1450, 7464, 1850), (5900, 2400, 7464, 2800)]
PLATE = (6536, 1100, 6792, 1400)
sx0, sx1, sy0, sy1 = so['x'], so['x'] + so['w'], so['y'], so['y'] + so['h']
for piece in rect_minus(sx0, sx1, sy0, sy1, [(px0, px1, py0, py1) for px0, py0, px1, py1 in PITS + [PLATE]]):
    b.rooms['sorting'] += clip_to(floor(piece[0], piece[2], piece[1], piece[3], 0, 'floor'),
                                  b.footprints['sorting'])
for px0, py0, px1, py1 in PITS:
    b.rooms['sorting'] += floor(px0 + 256, py0, px1, py1, -128, 'convey')
    for y, normal in ((py0, (0, 1, 0)), (py1, (0, -1, 0))):
        b.rooms['sorting'] += Wall('y', y, normal).quad(px0, px0 + 256, -128, 64, 'hazard')
        b.rooms['sorting'] += Wall('y', y, normal).quad(px0 + 256, px1, -128, 0, 'hazard')
    b.rooms['sorting'] += Wall('x', px1, (-1, 0, 0)).quad(py0, py1, -128, 0, 'hazard')
    b.rooms['sorting'] += flight_along((px0 + 256, (py0 + py1) / 2), (px0, (py0 + py1) / 2),
                                           py1 - py0, -128, 8, rise=16, tread='grille',
                                           riser='hazard', sides='hazard')
b.trigger('arcing_plate', 'sorting', floor(PLATE[0], PLATE[1], PLATE[2], PLATE[3], 0, 'scorch'), 20,
          kind='pressure_plate')
for x, y, name in ((5850, 2930, 'hes_container'), (7450, 2930, 'hes_container'), (7400, 1150, 'hes_fallen_plates'),
                   (7000, 2120, 'hes_drone_wreck'), (6300, 2120, 'hes_drone_wreck')):
    b.decoration(name, x, y, 0, (x // 10) % 360)

# --- The freight lift: a platform riding 768 between the ground (top) and the basement --------------------------------
fx0, fy0, fx1, fy1 = R['freight']['x'], R['freight']['y'], R['freight']['x'] + 1000, R['freight']['y'] + 1000
platform = box((fx0, fy0, -32), (fx1, fy1, 0), 'hazard', top='grille', bottom='girder')
b.door('lift', 'freight', platform, len(DOORS) + 1, 768, direction=(0, 0, -1), open_speed=160, close_speed=160)
DOORS['lift'] = len(DOORS) + 1
east = Wall('x', fx1, (-1, 0, 0))
b.trigger('lift_controls_top', 'freight', plaque(east, 1900, 96, 96, 128, 'console', out=10), 21)
b.trigger('lift_controls_bottom', 'freight', plaque(east, 1900, -672, 96, 128, 'console', out=10), 21)

# --- Maintenance and the Tower Stair Hall -----------------------------------------------------------------------------
placard = plaque(Wall('y', 6364, (0, -1, 0)), 2300, 96, 256, 128, 'sign', out=6)
b.trigger('breaker_placard', 'maintenance', placard, 14)
b.decoration('hes_colonial_locker', 3000, 6100, 0, 180, event=12)
b.rooms['maintenance'] += plaque(Wall('x', 1900, (1, 0, 0)), 5800, 0, 512, 320, 'tools', out=64)  # tool wall
b.decoration('hes_bench', 2700, 5400, 0, 0)
sh = R['stairhall']
b.rooms['stairhall'] += floor(sh['x'], 5164, sh['x'] + sh['w'], 5300, 0, 'floor')
b.rooms['stairhall'] += flight(sh['x'], 5300, sh['x'] + sh['w'], 6068, 0, 24, 'north', rise=16)
b.rooms['stairhall'] += floor(sh['x'], 6068, sh['x'] + sh['w'], 6400, 384, 'floor')
b.rooms['stairhall'] += flight(sh['x'], 6400, sh['x'] + sh['w'], 7168, 384, 24, 'north', rise=16)
b.rooms['stairhall'] += floor(sh['x'], 7168, sh['x'] + sh['w'], 7400, 768, 'floor')

# --- The Control Tower: an octagon with windows over the apron --------------------------------------------------------
tw = R['tower']
cx, cy, radius = tw['x'] + tw['w'] / 2, tw['y'] + tw['h'] / 2, tw['w'] / 2
TOP = 768 + tw['ceiling']
b.room('tower', (tw['x'], tw['y'], tw['x'] + tw['w'], tw['y'] + tw['h'], 767, TOP), AMBIENT['tower'])
corners = [(cx + radius * math.cos(math.pi / 8 + k * math.pi / 4),
            cy + radius * math.sin(math.pi / 8 + k * math.pi / 4))
           for k in range(8)]
b.rooms['tower'].append(([(x, y, 768) for x, y in corners], 'floor', (0, 0, 1)))
b.rooms['tower'] += hip_ceiling(corners, TOP - 160, TOP, 'ceiling')
TOP -= 160
WINDOWS = {0, 1, 2, 3, 7}
for k in range(8):
    (ax, ay), (bx, by) = corners[k], corners[(k + 1) % 8]
    inward = (cx - (ax + bx) / 2, cy - (ay + by) / 2, 0)
    if k == 5:                                          # the south side, with the arch from the stair hall
        b.rooms['tower'] += blv_kit.banded(Wall('y', ay, (0, 1, 0)), min(ax, bx), max(ax, bx),
                                           [(768, 784, 'trim'), (784, TOP - 32, 'wall'), (TOP - 32, TOP, 'gold')],
                                           [(3808, 4192, 768, 1088)])
        continue
    for z0, z1, role in ((768, 832, 'trim'), (832, TOP - 128, 'window' if k in WINDOWS else 'wall'),
                         (TOP - 128, TOP - 32, 'wall'), (TOP - 32, TOP, 'gold')):
        quad = [(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)]
        if role == 'window':
            length = math.hypot(bx - ax, by - ay)
            right = ((ax - bx) / length, (ay - by) / length, 0)
            b.rooms['tower'].append((quad, role, inward, blv_kit.Fit((bx, by, z0), right, (0, 0, 1), length, z1 - z0)))
        else:
            b.rooms['tower'].append((quad, role, inward))
b.trigger('tower_console', 'tower', box((3900, 8800, 768), (4100, 8920, 880), 'console', top='console'), 25)
b.decoration('hes_colonial_locker', 4000, 8500, 768, 0, event=8)                     # chest B
# The cache before Drone Control (the integrator's follow-up 28: 2 Shield Cells, a Stim), on the Power Plant's north
# catwalk past the breakers, in the corner away from the seal.
b.decoration('hes_colonial_locker', 5050, 3200, -768, 180, event=15)

# --- Basement: the service corridor, the Power Plant's pit, catwalks and breakers, Drone Control ----------------------
pit = R['plant_pit']
pz = pit['z']
b.rooms['plant_pit'] += floor(3100, 800, 5136, 2700, pz, 'pitwall')
b.rooms['plant_pit'] += floor(2900, 800, 3100, 1676, pz, 'pitwall')
b.rooms['plant_pit'] += ramp(2900, 1676, 3100, 2700, pz, -768, 'north',
                                  top='catwalk', skirt='pitwall', rail=32)
for y, inward in ((800, (0, 1, 0)), (2700, (0, -1, 0))):        # the pit's walls below the ledges
    b.rooms['plant_pit'] += Wall('y', y, inward).quad(2900, 5136, pz, -768, 'pitwall')
b.rooms['plant_pit'] += Wall('x', 5136, (-1, 0, 0)).quad(800, 2700, pz, -768, 'pitwall')
for x in (3300, 4100, 4900):                            # the catwalks across the pit
    b.rooms['plant_pit'] += box((x - 80, 800, -800), (x + 80, 2700, -768), 'hazard', top='catwalk', bottom='catwalk',
                                skip=('south', 'north'))
b.rooms['plant_pit'] += box((3700, 1300, pz), (4500, 2100, pz + 160), 'machine', top='gener')
pn = Wall('y', 3300, (0, -1, 0))
for k, x in enumerate((3300, 4100, 4900)):
    cabinet = plaque(pn, x, -768, 256, 384, 'machine', out=24)
    b.trigger(f'breaker_{k + 1}', 'plant_n', cabinet[:1], 16 + k, cog=101 + k)
    b.rooms['plant_n'] += cabinet[1:]
    b.trigger(f'terminal_{k + 1}', 'plant_n', plaque(pn, x + 220, -660, 96, 128, 'console', out=10), 26 + k)
dn = Wall('y', 3800, (0, -1, 0))
b.trigger('drone_console', 'dc_n', plaque(dn, 1100, -704, 256, 192, 'console', out=12), 23)
b.rooms['dc_s'] += box((1500, 2400, -768), (1900, 2800, -600), 'machine', top='trim')             # the cradle

# --- Lights and the arrival -------------------------------------------------------------------------------------------
for light in PLAN.lights:
    if light['id'] in ('F34', 'F36'):
        light['z'] = 864
    if light['id'] in ('F38', 'F39'):
        light['x'] = 6000 if light['id'] == 'F38' else 7350
    b.plan_light(light, plans.FIXTURE_COG)
start = next(m for m in PLAN.marks if m['kind'] == 'start')
packs = [{'label': m['label'], 'floor': m['floor'], 'position': [m['x'], m['y']], 'count': m['count']}
         for m in PLAN.marks if m['kind'] in ('monster', 'boss')]
# Five canisters in Customs' bonded supply corner; the Concourse kiosks hold three and two.
# 1826 faces give 15 satchels; none in Drone Control, the conveyor or the narrow catwalks.
CANISTERS = [
    ('customs', 701, 7750, 4840, 0, 270),
    ('customs', 702, 7900, 4840, 0, 270),
    ('customs', 703, 8050, 4840, 0, 270),
    ('customs', 704, 8200, 4840, 0, 270),
    ('customs', 705, 8350, 4840, 0, 270),
    ('concourse_w', 706, 1850, 4720, 0, 270),
    ('concourse_w', 707, 2050, 4720, 0, 270),
    ('concourse_w', 708, 2250, 4720, 0, 270),
    ('concourse_e', 709, 5550, 4720, 0, 270),
    ('concourse_e', 710, 5750, 4720, 0, 270),
]
assert len(CANISTERS) == 10 and {p[1] for p in CANISTERS} == set(range(701, 711))
SATCHELS = [
    ('concourse_w', 751, 1450, 3400, 0, 25),
    ('concourse_w', 752, 1450, 4920, 0, 200),
    ('concourse_e', 753, 6500, 3250, 0, 110),
    ('concourse_c', 754, 4700, 4950, 0, 250),
    ('customs', 755, 8200, 3550, 0, 45),
    ('security', 756, 8800, 4580, 0, 120),
    ('claim', 757, 2150, 2800, 0, 60),
    ('claim', 758, 4200, 1650, 0, 140),
    ('lost', 759, 1100, 1650, 0, 15),
    ('maintenance', 760, 2100, 5300, 0, 110),
    ('maintenance', 761, 3200, 5700, 0, 230),
    ('tower', 762, 3500, 8200, 768, 15),
    ('sorting', 763, 5850, 1200, 0, 45),
    ('sorting', 764, 7550, 2050, 0, 160),
    ('plant_s', 765, 3100, 450, -768, 25),
]
assert len(SATCHELS) == 15 and {p[1] for p in SATCHELS} == set(range(751, 766))
for name, placements in (('hes_stim_canister', CANISTERS), ('hes_colony_satchel', SATCHELS)):
    for room, event, x, y, z, facing in placements:
        assert b.room_at(x, y, z + 1) == room, (room, event)
        b.decoration(name, x, y, z, facing, event=event, cog=event)

# Keep every original door mouth and decoration centre inside its chamfered room.
for rid in CHAMFER:
    r, footprint = R[rid], b.footprints[rid]
    for side, spans in holes.get(rid, {}).items():
        for a0, a1, *_ in spans:
            for a in (a0, a1):
                x = r['x'] + (r['w'] if side == 'east' else 0) if side in ('west', 'east') else a
                y = r['y'] + (r['h'] if side == 'north' else 0) if side in ('north', 'south') else a
                assert blv_kit._inside(footprint, x, y), (rid, side, a)
    for name, x, y, z, *_ in b.decorations:
        if r['x'] <= x <= r['x'] + r['w'] and r['y'] <= y <= r['y'] + r['h'] and r['z'] <= z < r['z'] + r['ceiling']:
            assert blv_kit._inside(footprint, x, y), (rid, name, x, y)

b.export({'pickups': CANISTERS + SATCHELS, 'arrivals': {'apron_doors': {'position': [start['x'], start['y'], 0], 'direction_degrees': 0}},
          'monster_packs': packs, 'door_ids': DOORS,
          'chest_events': {7: 0, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5, 15: 6}})

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
