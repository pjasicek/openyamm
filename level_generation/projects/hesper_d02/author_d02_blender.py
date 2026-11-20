"""Author D2 Pumping Station (hes_d02.blv) in Blender, with the Hesper indoor kit (hesper_stage/blv_kit.py).

Run headless:  blender --background --factory-startup --python author_d02_blender.py
Rooms, links, markers and lights are the d2 plan of design/kreegan_world/zone1/dungeons/make_dungeon_plans.py. The
cistern is one sector from its floor (z -768) to the galleries' ceiling, open to the ring of galleries above z 0
behind their railings, held up by four pillars round an intake sump; its brine is three stacked water planes (z -256,
-512, -640, flagged lava so the party burns standing in it, cog numbers 201-203) that the three valves hide one by
one (evt.SetFacetBit). The Pump Hall is a machine hall built the MM way, from prisms with their own textures: three
pumps in a row (plinth, ribbed casing, flange, motor housing, outlet pipe to the ceiling), each piped north to a
manifold along the wall.
Writes source/hes_d02.glb, hes_d02.geometry.yml, hes_d02.semantic.json and hes_d02.blend.
"""
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path('/home/pjasicek/github/OpenYAMM')
sys.path.insert(0, str(ROOT / 'level_generation/projects/hesper_stage'))
import blv_kit  # noqa: E402
from blv_kit import Wall, banded, box, ceiling, flight, floor, pipe, plaque, prism  # noqa: E402

PROJECT = ROOT / 'level_generation/projects/hesper_d02'
PLANS = ROOT / 'design/kreegan_world/zone1/dungeons/make_dungeon_plans.py'
spec = importlib.util.spec_from_file_location('plans', PLANS)
plans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plans)
PLAN = plans.d2
R = {r['id']: r for r in PLAN.rooms}

ROLE = {'wall': 'hiwall', 'pipe': 'hipipe', 'scale': 'hiscale', 'grate': 'higrate', 'floor': 'hifloor',
        'tank': 'hitank', 'filter': 'hifilter', 'brine': 'hibrine', 'canyon': 'hicanyon', 'pump': 'hipump',
        'motor': 'himotor', 'pipes': 'hipipes', 'tools': 'hitools', 'trim': 'hctrim', 'hazard': 'hchazard',
        'console': 'hcconsole', 'door': 'hcdoor', 'hatch': 'hohatch', 'gold': 'hogold', 'rail': 'hfrail',
        'marker': 'hcconsole'}
b = blv_kit.Builder('hes_d02.blv', ROLE, PROJECT / 'source',
                    role_scale={'wall': 1.5, 'floor': 1.5, 'scale': 1.5, 'canyon': 1.5, 'pump': 1.2,
                                'motor': 2.34})

GALLERY = [(0, 32, 'hazard'), (32, 224, 'pipe'), (224, 256, 'trim')]
GATE = [(0, 224, 'canyon'), (224, 256, 'trim')]
HALL = [(0, 32, 'hazard'), (32, 416, 'wall'), (416, 480, 'pipe'), (480, 864, 'wall'), (864, 896, 'trim')]
BEDS = [(0, 32, 'hazard'), (32, 480, 'wall'), (480, 512, 'trim')]
SMALL = [(0, 32, 'hazard'), (32, 224, 'wall'), (224, 256, 'trim')]
CISTERN = [(0, 256, 'scale'), (256, 448, 'wall'), (448, 512, 'scale'), (512, 704, 'wall'), (704, 768, 'scale')]

holes = {}
openings = []


def connect(owner, owner_side, other, centre, width, height, z=None):
    o, t = R[owner], R[other]
    z = o['z'] if z is None else z
    a0, a1 = centre - width / 2, centre + width / 2
    side_of_other = {'south': 'north', 'north': 'south', 'west': 'east', 'east': 'west'}[owner_side]
    if owner_side in ('south', 'north'):
        plane, axis, toward = (o['y'], 'y', -1) if owner_side == 'south' else (o['y'] + o['h'], 'y', 1)
    else:
        plane, axis, toward = (o['x'], 'x', -1) if owner_side == 'west' else (o['x'] + o['w'], 'x', 1)
    holes.setdefault(owner, {}).setdefault(owner_side, []).append((a0, a1, z - o['z'], z - o['z'] + height))
    holes.setdefault(other, {}).setdefault(side_of_other, []).append((a0, a1, z - t['z'], z - t['z'] + height))
    openings.append((owner, other, axis, plane, a0, a1, z, z + height, toward))


MID = 1848                                              # the line through the gate, the galleries and the halls
connect('gate', 'east', 'gal_w', MID, 384, 256)
connect('gal_e', 'east', 'pump', MID, 512, 256)
connect('pump', 'east', 'filters', MID, 512, 320)
connect('works', 'north', 'pump', 6000, 384, 256)
holes.setdefault('gate', {})['west'] = [(MID - 128, MID + 128, 0, 256)]   # the canyon hatch
holes.setdefault('works', {})['south'] = [(5872, 6128, 0, 256)]           # the Water Works door

AMBIENT = {'gate': 20, 'gal_w': 23, 'gal_n': 23, 'gal_s': 23, 'gal_e': 23, 'pump': 23, 'filters': 25, 'works': 21,
           'cistern': 26}
BANDS = {'gate': GATE, 'pump': HALL, 'filters': BEDS, 'works': SMALL}
FLOORS = {'gate': 'canyon', 'gal_w': 'grate', 'gal_n': 'grate', 'gal_s': 'grate', 'gal_e': 'grate'}
CEILINGS = {'gate': 'canyon', 'gal_w': 'pipe', 'gal_n': 'pipe', 'gal_s': 'pipe', 'gal_e': 'pipe', 'pump': 'pipe'}
# The galleries: one space in four sectors, open to the cistern on their inner edges.
OPEN = {'gal_w': ('east',), 'gal_n': ('south', 'west', 'east'), 'gal_s': ('north', 'west', 'east'),
        'gal_e': ('west',)}
for rid in ('gate', 'gal_w', 'gal_n', 'gal_s', 'gal_e', 'pump', 'filters', 'works'):
    r = R[rid]
    b.box_room(rid, r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'], r['z'], r['ceiling'],
               BANDS.get(rid, GALLERY), holes.get(rid, {}), floor_role=FLOORS.get(rid, 'floor'),
               ceiling_role=CEILINGS.get(rid, 'wall'), ambient=AMBIENT[rid], open_sides=OPEN.get(rid, ()))
c = R['cistern']
cx0, cy0, cx1, cy1 = c['x'], c['y'], c['x'] + c['w'], c['y'] + c['h']
# The side galleries' ends meet the north and south galleries; their middles look over the cistern.
G = R['gal_w']['ceiling']                              # the galleries' ceiling, which the cistern's open top shares
gw, ge = R['gal_w'], R['gal_e']
for front, back, x, y0, y1 in (('gal_w', 'gal_s', cx0, gw['y'], cy0), ('gal_w', 'gal_n', cx0, cy1, gw['y'] + gw['h']),
                               ('gal_s', 'gal_e', cx1, ge['y'], cy0), ('gal_n', 'gal_e', cx1, cy1, ge['y'] + ge['h'])):
    b.portal(front, back, [(x, y0, 0), (x, y1, 0), (x, y1, G), (x, y0, G)])

# --- The cistern: walls up to the galleries' floor (open above), four pillars, the intake sump, the stair, the brine
b.room('cistern', (cx0, cy0, cx1, cy1, -769, G), AMBIENT['cistern'])
SUMP = (2648 - 256, MID - 256, 2648 + 256, MID + 256)  # the intake grate in the middle of the floor
sx0, sy0, sx1, sy1 = SUMP
for rect in ((cx0, cy0, cx1, sy0), (cx0, sy1, cx1, cy1), (cx0, sy0, sx0, sy1), (sx1, sy0, cx1, sy1)):
    b.rooms['cistern'] += floor(*rect, -768, 'floor')
b.rooms['cistern'] += floor(*SUMP, -768, 'grate')
b.rooms['cistern'] += ceiling(cx0, cy0, cx1, cy1, G, 'pipe')
for wall, a0, a1 in ((Wall('y', cy0, (0, 1, 0)), cx0, cx1), (Wall('y', cy1, (0, -1, 0)), cx0, cx1),
                     (Wall('x', cx0, (1, 0, 0)), cy0, cy1), (Wall('x', cx1, (-1, 0, 0)), cy0, cy1)):
    b.rooms['cistern'] += banded(wall, a0, a1, [(-768 + z0, -768 + z1, role) for z0, z1, role in CISTERN], [])
# Four square pillars hold up the gallery ring's ceiling, scaled where the brine stood.
for x in (cx0 + 650, cx1 - 650):
    for y in (cy0 + 450, cy1 - 450):
        lo, hi = (x - 64, y - 64), (x + 64, y + 64)
        b.rooms['cistern'] += box((*lo, -768), (*hi, -256), 'scale')
        b.rooms['cistern'] += box((*lo, -256), (*hi, G), 'wall')
b.portal('cistern', 'gal_w', [(cx0, cy0, 0), (cx0, cy1, 0), (cx0, cy1, G), (cx0, cy0, G)])
b.portal('cistern', 'gal_e', [(cx1, cy0, 0), (cx1, cy1, 0), (cx1, cy1, G), (cx1, cy0, G)])
b.portal('cistern', 'gal_s', [(cx0, cy0, 0), (cx1, cy0, 0), (cx1, cy0, G), (cx0, cy0, G)])
b.portal('cistern', 'gal_n', [(cx0, cy1, 0), (cx1, cy1, 0), (cx1, cy1, G), (cx0, cy1, G)])
# The stair down the cistern's west wall, from the north gallery's corner: 24 steps of 32, its open side a stringer.
STAIR_Y0 = cy1 - 24 * 64
b.rooms['cistern'] += flight(cx0, STAIR_Y0, cx0 + 256, cy1, -768, 24, 'north', tread='grate', riser='hazard')
for k in range(24):
    ya, yb, z = STAIR_Y0 + 64 * k, STAIR_Y0 + 64 * (k + 1), -768 + 32 * (k + 1)
    b.rooms['cistern'] += Wall('x', cx0 + 256, (1, 0, 0)).quad(ya, yb, -768, z, 'wall')
# The galleries' railings along the cistern: a ceramic balustrade 96 high (Lowhold's), open at the stair's top.
RAIL = 24
for rid, lo, hi in (('gal_w', (cx0 - RAIL, cy0, 0), (cx0, cy1, 96)), ('gal_e', (cx1, cy0, 0), (cx1 + RAIL, cy1, 96)),
                    ('gal_s', (cx0, cy0 - RAIL, 0), (cx1, cy0, 96)),
                    ('gal_n', (cx0 + 256, cy1, 0), (cx1, cy1 + RAIL, 96))):
    b.rooms[rid] += box(lo, hi, 'rail', top='gold')
# The brine: three water planes, the top one first to drain.
for k, z in enumerate((-256, -512, -640)):
    b.surface(f'brine_{k + 1}', 'cistern', floor(cx0, cy0, cx1, cy1, z, 'brine'), flags=('lava',), cog=201 + k)

# --- The valves: 3D on the galleries' outer walls, a fixed body and a wheel that turns when used ---------------------
# The wheel is clicked through its event, which also keys its swap to hes_valve_wheel_turned (it turns into place,
# turn_in); the body's cog 30 + valve swaps its lamp from red to green. Both mount on the wall.
VALVES = [(1, 900, 2700, 270), (2, 3200, R['gal_n']['y'] + R['gal_n']['h'], 180), (3, ge['x'] + ge['w'], 900, 90)]
for valve, x, y, facing in VALVES:
    b.decoration('hes_valve_body', x, y, 0, facing, cog=30 + valve)
    b.decoration('hes_valve_wheel', x, y, 107, facing, event=2 + valve, cog=2 + valve)

# --- The gate's hatch -----------------------------------------------------------------------------------------------
face, jambs = blv_kit.recessed_door(Wall('x', 0, (1, 0, 0)), MID, 0, 256, 256, 'hatch', depth=16)
b.rooms['gate'] += jambs
b.trigger('canyon_hatch', 'gate', face, 2)

# --- The Pump Hall: 8 steps down from the east gallery, three pumps, their pipes and the manifold ---------------------
p = R['pump']
px0, py0, px1, py1, pz = p['x'], p['y'], p['x'] + p['w'], p['y'] + p['h'], p['z']
b.rooms['pump'] += flight(px0, MID - 256, px0 + 512, MID + 256, pz, 8, 'west', tread='grate', riser='hazard')
for y, inward in ((MID - 256, (0, -1, 0)), (MID + 256, (0, 1, 0))):
    for k in range(8):
        xa, xb, z = px0 + 512 - 64 * (k + 1), px0 + 512 - 64 * k, pz + 32 * (k + 1)
        b.rooms['pump'] += Wall('y', y, inward).quad(xa, xb, pz, z, 'wall')
PUMP_Y = 2250                                          # the row stands north of the walk from the steps to the beds
MANIFOLD_Y, MANIFOLD_Z = py1 - 80, pz + 300
for x in (5250, 5900, 6550):
    b.rooms['pump'] += prism(x, PUMP_Y, 260, pz, pz + 32, 'trim', top='floor')          # the stepped plinth
    b.rooms['pump'] += prism(x, PUMP_Y, 230, pz + 32, pz + 64, 'wall', top='floor')
    b.rooms['pump'] += prism(x, PUMP_Y, 200, pz + 64, pz + 416, 'pump')                  # the ribbed casing
    b.rooms['pump'] += prism(x, PUMP_Y, 226, pz + 416, pz + 448, 'gold', top='gold', bottom='gold')    # flange
    b.rooms['pump'] += box((x - 150, PUMP_Y - 150, pz + 448), (x + 150, PUMP_Y + 150, pz + 640), 'motor',
                           top='pipes')                                                  # the motor housing
    b.rooms['pump'] += prism(x, PUMP_Y, 56, pz + 640, pz + p['ceiling'], 'pipes')        # outlet to the ceiling
    b.rooms['pump'] += pipe((x, PUMP_Y + 190, MANIFOLD_Z), (x, MANIFOLD_Y - 60, MANIFOLD_Z), 44, 'pipes')
b.rooms['pump'] += pipe((px0, MANIFOLD_Y, MANIFOLD_Z), (px1, MANIFOLD_Y, MANIFOLD_Z), 70, 'pipes')
for x in (px0 + 300, 5575, 6225, px1 - 300):                                             # the manifold's brackets
    b.rooms['pump'] += box((x - 16, MANIFOLD_Y - 40, pz), (x + 16, py1, MANIFOLD_Z - 70), 'trim', top='trim')
# Against the south wall: the maintenance tool wall (a cabinet) and the tool locker.
b.rooms['pump'] += plaque(Wall('y', py0, (0, 1, 0)), 5400, pz, 512, 320, 'tools', out=64)

# --- The Filter Beds: three beds of crushed glass, the filter console on the north wall ------------------------------
f = R['filters']
fx0, fy0, fx1, fy1, fz = f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'], f['z']
for y0, y1 in ((fy0 + 200, fy0 + 700), (fy0 + 900, fy0 + 1100), (fy0 + 1300, fy0 + 1800)):
    b.rooms['filters'] += box((fx0 + 450, y0, fz), (fx1 - 300, y1, fz + 32), 'wall', top='filter')
b.trigger('filter_console', 'filters', plaque(Wall('y', fy1, (0, -1, 0)), 7924, fz + 64, 320, 224, 'console',
                                              out=48), 7)

# --- The Water Works passage and its door to Lowhold ----------------------------------------------------------------
w = R['works']
face, jambs = blv_kit.recessed_door(Wall('y', w['y'], (0, 1, 0)), 6000, w['z'], 256, 256, 'door', depth=16)
b.rooms['works'] += jambs
b.trigger('works_door', 'works', face, 8)

for owner, other, axis, plane, a0, a1, z0, z1, toward in openings:
    b.opening(owner, other, axis, plane, a0, a1, z0, z1, toward=toward)

# --- Decorations: each where its job is (DUNGEON_PLAYBOOK.md) --------------------------------------------------------
b.decoration('hes_fallen_plates', 300, 1600, 0, 40)                          # the gate: plates fallen from the lock
b.decoration('hes_drum', 1100, 620, 0, 20)                                   # spent filter drums in a gallery corner
b.decoration('hes_drum', 1200, 700, 0, 75)
b.decoration('hes_drum', 1060, 760, 0, 140)
b.decoration('hes_colonial_locker', 2000, 1300, -768, 30, event=9)          # sunk with the cistern
b.decoration('hes_corpse_colonist', 3400, 2300, -768, 120, event=13)
b.decoration('hes_colonial_locker', 6700, 1030, pz, 0, event=10)            # beside the tool wall
b.decoration('hes_colonial_locker', 6650, 2600, pz, 180, event=14)          # the cache before the Filter Beds
for x, y, yaw in ((5800, 1030, 0), (5930, 1020, 20), (5860, 1120, 80)):      # spares stacked by the tools
    b.decoration('hes_crate_clean', x, y, pz, yaw)
for x, y, name in ((7500, 1000, 'hes_glass_boulder_blue'), (8100, 1100, 'hes_glass_shards_blue'),
                   (8600, 1500, 'hes_glass_shards_blue'), (7700, 1950, 'hes_glass_boulder_blue'),
                   (8500, 2050, 'hes_glass_shards_blue'), (7300, 2500, 'hes_glass_shards_blue'),
                   (8200, 2500, 'hes_glass_boulder_blue')):
    on_bed = fx0 + 450 <= x <= fx1 - 300 and any(y0 <= y <= y1 for y0, y1 in ((fy0 + 200, fy0 + 700),
                                                                                (fy0 + 900, fy0 + 1100),
                                                                                (fy0 + 1300, fy0 + 1800)))
    b.decoration(name, x, y, fz + 32 if on_bed else fz, (x + y) % 360)
b.decoration('hes_colonial_locker', 8800, 2600, fz, 270, event=11)

for light in PLAN.lights:
    b.plan_light(light, plans.FIXTURE_COG)
start = next(m for m in PLAN.marks if m['kind'] == 'start')
packs = [{'label': m['label'], 'floor': m['floor'], 'position': [m['x'], m['y']], 'count': m['count']}
         for m in PLAN.marks if m['kind'] in ('monster', 'boss')]
# PICKUPS.md: 1242 faces give 10 satchels, clear of the Queen's Filter Beds and walkway centres.
SATCHELS = [
    ('gate', 751, 650, 2150, 0, 220),
    ('gal_w', 752, 1010, 1200, 0, 20),
    ('gal_w', 753, 1010, 3000, 0, 150),
    ('gal_n', 754, 1800, 3080, 0, 200),
    ('gal_n', 755, 3550, 3080, 0, 270),
    ('gal_s', 756, 2000, 620, 0, 45),
    ('gal_s', 757, 3700, 620, 0, 110),
    ('gal_e', 758, 4270, 2500, 0, 230),
    ('pump', 759, 4800, 1100, -256, 25),
    ('pump', 760, 6350, 1080, -256, 80),
]
assert len(SATCHELS) == 10 and {p[1] for p in SATCHELS} == set(range(751, 761))
for room, event, x, y, z, facing in SATCHELS:
    assert b.room_at(x, y, z + 1) == room, (room, event)
    b.decoration('hes_colony_satchel', x, y, z, facing, event=event, cog=event)

b.export({'pickups': SATCHELS, 'arrivals': {'canyon_gate': {'position': [start['x'], start['y'], 0], 'direction_degrees': 0},
                       'water_works': {'position': [6000, -100, w['z']], 'direction_degrees': 90}},
          'monster_packs': packs, 'door_ids': {}, 'chest_events': {9: 0, 10: 1, 11: 2, 13: 3, 14: 4}})

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
