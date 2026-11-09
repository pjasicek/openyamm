"""Author D0 Hangar Nine (hes_d00.blv) in Blender, with the Hesper indoor kit (hesper_stage/blv_kit.py).

Run headless:  blender --background --factory-startup --python author_d00_blender.py
Rooms, links, markers and lights are the d0 plan of design/kreegan_world/zone1/dungeons/make_dungeon_plans.py (the
redesign of 2026-10-22: the derelict lander the party repairs). The rooms are their interiors, 64 apart (the walls'
thickness); this script adds the walls and openings, the doors, the roof hatch, the stair to Hangar Control and its
gallery windows, the derelict lander (hull, pods, nozzles, cradle, the flight deck inside it and its five sockets), the
reactor, the fuel tanks and the coolant leak, the furniture, the decorations, the light fixtures and the monsters.
Writes source/hes_d00.glb, hes_d00.geometry.yml, hes_d00.semantic.json and hes_d00.blend.
"""
import importlib.util
import os
import math
import sys
from pathlib import Path

ROOT = Path('/home/pjasicek/github/OpenYAMM')
sys.path.insert(0, str(ROOT / 'level_generation/projects/hesper_stage'))
import blv_kit  # noqa: E402
from blv_kit import Fit, Wall, beam, box, ceiling, flight_along, floor, pipe, plaque, prism, rect_minus, chamfer_rect, clip_to, hip_ceiling  # noqa: E402

PROJECT = ROOT / 'level_generation/projects/hesper_d00'
PLANS = ROOT / 'design/kreegan_world/zone1/dungeons/make_dungeon_plans.py'
spec = importlib.util.spec_from_file_location('plans', PLANS)
plans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plans)
PLAN = plans.d0
R = {r['id']: dict(r) for r in PLAN.rooms}

ROLE = {'wall': 'hcpanel', 'recess': 'hcrecess', 'hazard': 'hchazard', 'trim': 'hctrim', 'gold': 'hogold',
        'girder': 'hcgirder', 'strip': 'hcstripd', 'strip_white': 'hcstripw', 'strip_red': 'hcstripr',
        'floor': 'hcfloor', 'grille': 'hcgrille', 'ceiling': 'hcceiling', 'door': 'hcdoor', 'shutter': 'hcshutter',
        'console': 'hcconsole', 'sign': 'hcsign', 'crate': 'hcrate', 'hull': 'hlhull', 'hull_torn': 'hlhulltorn',
        'glass': 'hlglass', 'scorch': 'hcscorch', 'ash': 'hashdrift', 'sky': 'hskyhatch', 'pitwall': 'hcpitwall',
        'machine': 'hcmachine', 'gener': 'hcgener', 'pipe': 'hipipe', 'pipes': 'hipipes', 'tank': 'hitank',
        'iwall': 'hiwall', 'ifloor': 'hifloor', 'brine': 'hibrine', 'catwalk': 'hccatwalk', 'tools': 'hitools',
        'container': 'hcontainer', 'marker': 'hcconsole'}
b = blv_kit.Builder('hes_d00.blv', ROLE, PROJECT / 'source',
                    role_scale={'wall': 1.5, 'floor': 1.5, 'ceiling': 2.0, 'pitwall': 1.5, 'iwall': 1.5,
                                'ifloor': 1.5, 'hull': 1.5, 'girder': 1.5})
T = blv_kit.THICK
COG = plans.FIXTURE_COG

holes = {}                # room -> side -> [(a0, a1, z0, z1)] (z relative to the room's floor)
openings = []             # (owner, other, axis, plane, a0, a1, z0, z1, toward)
DOORS = {}                # name -> door id
door_specs = []           # (name, owner, axis, plane, a0, a1, z0, z1, toward, role, event)


def connect(owner, owner_side, other, centre, width, height, z=None, door=None, event=0, role='door', reveal=True):
    """An opening `width` x `height` from owner's `owner_side` wall into `other` (the reveal owned by owner); a door
    leaf in it when `door` names one; reveal=False cuts the holes only (an opening built by hand)."""
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
    if reveal:
        openings.append((owner, other, axis, plane, a0, a1, z, z + height, toward))
    if door:
        DOORS[door] = len(DOORS) + 1
        door_specs.append((door, owner, axis, plane, a0, a1, z, z + height, toward, role, event))


def sub(rid, x0, y0, x1, y1, base):
    R[rid] = dict(R[base], id=rid, x=x0, y=y0, w=x1 - x0, h=y1 - y0)


# --- Rooms: the plan's, the bay, the aisle and the ramp split into sectors --------------------------------------------
for rid, x0, x1 in (('bay_w', 0, 1200), ('bay_c', 1200, 2400), ('bay_e', 2400, 3600)):
    sub(rid, x0, 0, x1, 3000, 'bay')
sub('aisle_w', 3664, 1100, 5400, 1900, 'aisle')
sub('aisle_e', 5400, 1100, 7136, 1900, 'aisle')
sub('ramp_foot', 7200, 1100, 8000, 1900, 'ramp')
RAMP = dict(x0=7200, x1=8000, y0=1900, y1=3900, rise=512, headroom=R['ramp']['ceiling'])
for rid in ('bay', 'aisle', 'ramp'):
    del R[rid]

# --- The connections (the plan's links) ---------------------------------------------------------------------------
connect('aisle_e', 'east', 'ramp_foot', 1500, 512, 384)                    # the ramp foot
connect('aisle_w', 'west', 'bay_e', 1500, 512, 448)                        # the cargo doors, jammed half open
connect('aisle_w', 'north', 'tech', 4800, 256, 256, door='tech', event=40)
connect('aisle_w', 'south', 'parts', 4800, 256, 256, door='parts', event=44)
connect('aisle_e', 'north', 'militia', 6600, 256, 256, door='militia', event=41)
connect('aisle_e', 'south', 'range', 6400, 512, 320, door='range', role='shutter')
connect('bay_w', 'west', 'reactor', 1500, 384, 320, door='reactor', event=42)
connect('bay_c', 'south', 'fuel', 1800, 256, 256, door='fuel', event=43)
connect('reactor', 'north', 'stair', -1204, 256, 320)
connect('stair', 'east', 'control', 3382, 256, 256, z=640, door='control', role='shutter', event=60)
# Hangar Control's gallery windows over the bay, one to each bay sector, above a parapet 112 high (no jumping out).
WINDOWS = [('bay_w', 450, 1100), ('bay_c', 1300, 2300), ('bay_e', 2450, 2650)]
for rid, a0, a1 in WINDOWS:
    connect('control', 'south', rid, (a0 + a1) / 2, a1 - a0, 272, z=752)

AMBIENT = {'bay_w': 24, 'bay_c': 24, 'bay_e': 24, 'aisle_w': 25, 'aisle_e': 25, 'tech': 18, 'parts': 26,
           'militia': 18, 'range': 26, 'ramp_foot': 24, 'reactor': 24, 'fuel': 25, 'stair': 25, 'control': 22}
SMALL = [(0, 16, 'trim'), (16, 416, 'wall'), (416, 448, 'strip')]
SAFE = [(0, 16, 'trim'), (16, 416, 'wall'), (416, 448, 'strip_white')]
BAY = [(0, 96, 'hazard'), (96, 128, 'trim'), (128, 640, 'wall'), (640, 672, 'gold'), (672, 1536, 'girder')]
RANGE = [(0, 96, 'hazard'), (96, 416, 'wall'), (416, 448, 'strip')]
REACTOR = [(0, 32, 'hazard'), (32, 704, 'pitwall'), (704, 736, 'strip_red'), (736, 768, 'trim')]
FUEL = [(0, 32, 'hazard'), (32, 608, 'iwall'), (608, 640, 'trim')]
STAIR = [(0, 16, 'trim'), (16, 1056, 'wall'), (1056, 1088, 'strip')]
CONTROL = [(0, 16, 'trim'), (16, 416, 'wall'), (416, 448, 'gold')]
BANDS = {'bay_w': BAY, 'bay_c': BAY, 'bay_e': BAY, 'tech': SAFE, 'militia': SAFE, 'range': RANGE,
         'reactor': REACTOR, 'fuel': FUEL, 'stair': STAIR, 'control': CONTROL}
FLOORS = {'tech': 'grille', 'militia': 'grille', 'reactor': 'grille', 'fuel': 'ifloor', 'control': 'grille',
          'range': 'floor'}
CEILINGS = {'reactor': 'pipes', 'fuel': 'pipes'}
OPEN = {'bay_w': ('east',), 'bay_c': ('west', 'east'), 'bay_e': ('west',), 'aisle_w': ('east',),
        'aisle_e': ('west',), 'ramp_foot': ('north',)}
CHAMFER = {'bay_w':{'sw':300,'nw':300}, 'bay_e':{'se':300,'ne':300},
           'tech':64, 'parts':96, 'militia':128, 'range':128, 'reactor':200, 'fuel':128,
           'control':{'sw':64,'se':48,'nw':64,'ne':64}, 'ramp_foot':{'sw':128,'se':128,'nw':128}}
HIPS = {'tech':64,'parts':64,'militia':64,'range':64,'control':64}
FOOTPRINTS = {rid:chamfer_rect(r['x'],r['y'],r['x']+r['w'],r['y']+r['h'],CHAMFER.get(rid,0))
              for rid,r in R.items()}
for rid, r in R.items():
    if rid == 'cockpit':
        continue
    x0, y0, x1, y1 = r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']
    height=r['ceiling']-HIPS.get(rid,0)
    bands=[(lo,min(hi,height),role)for lo,hi,role in BANDS.get(rid,SMALL) if lo<height]
    b.box_room(rid, x0, y0, x1, y1, r['z'], height, bands, holes.get(rid, {}),
               floor_role=FLOORS.get(rid, 'floor'), ceiling_role=None if rid in HIPS else CEILINGS.get(rid, 'ceiling'),
               ambient=AMBIENT[rid], open_sides=OPEN.get(rid, ()),chamfer=CHAMFER.get(rid))
    if rid in HIPS:
        b.rooms[rid]+=hip_ceiling(FOOTPRINTS[rid],r['z']+height,r['z']+r['ceiling'],'ceiling')
        b.bounds[rid]=(*b.bounds[rid][:5],r['z']+r['ceiling'])


def drop(rid, normal, z):
    """Remove the box room's floor or ceiling (normal (0, 0, 1) or (0, 0, -1)) at height z, to lay it by hand."""
    b.rooms[rid][:] = [pn for pn in b.rooms[rid] if not (pn[2] == normal and abs(pn[0][0][2] - z) < 1)]


def portal_x(front, back, x, y0, y1, z0, z1):
    b.portal(front, back, [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)])


def portal_y(front, back, y, x0, x1, z0, z1):
    b.portal(front, back, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)])


portal_x('bay_w', 'bay_c', 1200, 0, 3000, 0, 1536)
portal_x('bay_c', 'bay_e', 2400, 0, 3000, 0, 1536)
portal_x('aisle_w', 'aisle_e', 5400, 1100, 1900, 0, 512)

# The openings' reveals, portals and door leaves (they rise into the wall above).
for owner, other, axis, plane, a0, a1, z0, z1, toward in openings:
    b.opening(owner, other, axis, plane, a0, a1, z0, z1, toward=toward)
for name, owner, axis, plane, a0, a1, z0, z1, toward, role, event in door_specs:
    mid = plane + toward * (T / 2)
    lo, hi = ((a0, mid - 8, z0), (a1, mid + 8, z1)) if axis == 'y' else ((mid - 8, a0, z0), (mid + 8, a1, z1))
    b.door(name, owner, box(lo, hi, role, top='trim'), DOORS[name], int(z1 - z0), direction=(0, 0, 1), event=event)

# --- The Crew Ramp: the flat foot, then the slope up to the surface door the crash cracked ---------------------------
r = RAMP
TOP = r['rise']


def ramp_z(y):
    return r['rise'] * (min(max(y, r['y0']), r['y1']) - r['y0']) / (r['y1'] - r['y0'])


portal_y('ramp_foot', 'ramp', r['y0'], r['x0'], r['x1'], 0, r['headroom'])
b.room('ramp', (r['x0'], r['y0'], r['x1'], r['y1'], -1, TOP + r['headroom']), 24)
rp = b.rooms['ramp']
rp.append(([(r['x0'], r['y0'], 0), (r['x1'], r['y0'], 0), (r['x1'], r['y1'], TOP), (r['x0'], r['y1'], TOP)],
           'floor', (0, -0.25, 1)))
h = r['headroom']
rp.append(([(r['x0'], r['y0'], h), (r['x1'], r['y0'], h), (r['x1'], r['y1'], TOP + h), (r['x0'], r['y1'], TOP + h)],
           'ceiling', (0, 0.25, -1)))
for x, inward in ((r['x0'], (1, 0, 0)), (r['x1'], (-1, 0, 0))):           # side walls in sloped bands
    for z0, z1, role in blv_kit.stretch(SMALL, h):
        rp.append(([(x, r['y0'], z0), (x, r['y1'], TOP + z0), (x, r['y1'], TOP + z1), (x, r['y0'], z1)], role,
                   inward))
north = Wall('y', r['y1'], (0, -1, 0))
rp += blv_kit.banded(north, r['x0'], r['x1'], [(TOP + z0, TOP + z1, role) for z0, z1, role in
                                                 blv_kit.stretch(SMALL, h)], [(7408, 7792, TOP, TOP + 256)])
face, jambs = blv_kit.recessed_door(north, 7600, TOP, 384, 256, 'door', depth=16)
rp += jambs
b.trigger('surface_door', 'ramp', face, 50)
# Ash blown in through the crack, a fallen panel and the drift at the top.
rp += [([(7280, 3500, ramp_z(3500) + 1), (7920, 3500, ramp_z(3500) + 1), (7920, 3880, ramp_z(3880) + 1),
         (7280, 3880, ramp_z(3880) + 1)], 'ash', (0, -0.25, 1))]
b.decoration('hes_fallen_plates', 7350, 3300, ramp_z(3300), 200)
b.trigger('info_panel_6', 'ramp_foot', plaque(Wall('x', 8000, (-1, 0, 0)), 1500, 96, 128, 128, 'sign', out=6), 15)

# --- The Cargo Aisle: crate stacks screen the long sightline; the jammed cargo-door leaf; the practice terminal -------
for rid, lo, hi in (('aisle_w', (3800, 1120, 0), (4250, 1320, 192)), ('aisle_w', (4250, 1120, 0), (4400, 1260, 128)),
                    ('aisle_e', (5450, 1120, 0), (5600, 1320, 224)), ('aisle_e', (5700, 1700, 0), (6000, 1880, 160)),
                    ('aisle_e', (6750, 1120, 0), (7100, 1300, 192))):
    b.rooms[rid] += box(lo, hi, 'crate', top='crate')
b.rooms['bay_e'] += box((3560, 1756, 0), (3584, 2140, 448), 'door', top='trim')           # the stuck leaf
b.trigger('info_panel_2', 'aisle_w', plaque(Wall('y', 1900, (0, -1, 0)), 4000, 96, 128, 128, 'sign', out=6), 11)
b.trigger('practice_terminal', 'aisle_w', plaque(Wall('y', 1100, (0, 1, 0)), 5100, 64, 96, 128, 'console', out=10),
          25)
for x, y, f in ((5880, 1460, 30), (6150, 1560, 300)):                                  # the crates the crawlers broke
    b.decoration('hes_crate_clean', x, y, 0, f)

# --- Technician's Office, Parts Store, Militia Post, Firing Range -----------------------------------------------------
b.rooms['tech'] += box((4900, 2700, 0), (5250, 2930, 96), 'crate', top='console')           # the workbench
b.rooms['tech'] += plaque(Wall('y', 2964, (0, -1, 0)), 4600, 96, 384, 192, 'console', out=8)  # dead screens
b.trigger('info_panel_3', 'tech', plaque(Wall('y', 2964, (0, -1, 0)), 5050, 96, 128, 128, 'sign', out=6), 12)
b.decoration('hes_shelf_rack_tools', 5210, 2250, 0, 90)
b.decoration('hes_bench', 4500, 2200, 0, 270)
b.decoration('hes_shelf_rack', 4400, 300, 0, 270)
b.decoration('hes_shelf_rack', 4400, 750, 0, 270)
b.decoration('hes_shelf_rack_tools', 5200, 300, 0, 90)
b.decoration('hes_colonial_locker', 4800, 150, 0, 0, event=31)                              # chest 1
b.rooms['militia'] += box((6150, 2700, 0), (6550, 2900, 96), 'crate', top='console')        # the duty desk
b.rooms['militia'] += plaque(Wall('x', 6000, (1, 0, 0)), 2500, 0, 512, 320, 'tools', out=64)  # the weapon rack
b.trigger('info_panel_4', 'militia', plaque(Wall('y', 2964, (0, -1, 0)), 6400, 96, 128, 128, 'sign', out=6), 13)
b.trigger('range_lever', 'militia', plaque(Wall('x', 7136, (-1, 0, 0)), 2550, 96, 96, 128, 'console', out=10), 26)
b.decoration('hes_colonial_locker', 6900, 2100, 0, 90, event=32)                             # chest 2, the arms locker
b.rooms['range'] += box((6500, 200, 0), (6560, 880, 96), 'hazard', top='trim')               # the firing-lane wall
b.rooms['range'] += box((5900, 600, 0), (6500, 640, 64), 'hazard', top='trim')               # the lane divider
b.trigger('info_panel_5', 'range', plaque(Wall('x', 5600, (1, 0, 0)), 400, 96, 128, 128, 'sign', out=6), 14)
for y in (300, 800):                                       # the Starport Turrets' colony pedestals (ring at 0.599 m)
    b.decoration('hes_starport_turret_mount', 6950, y, 0, 90)

# --- The Hangar Bay: the roof hatch, the walls' furniture, the crew locker --------------------------------------------
HATCH = (1300, 900, 2300, 2300)
hx0, hy0, hx1, hy1 = HATCH
drop('bay_c', (0, 0, -1), 1536)
for a0, a1, z0, z1 in rect_minus(1200, 2400, 0, 3000, [(hx0, hx1, hy0, hy1)]):
    b.rooms['bay_c'] += ceiling(a0, z0, a1, z1, 1536, 'ceiling')
SHAFT = 1680
for wall, a0, a1 in ((Wall('x', hx0, (1, 0, 0)), hy0, hy1), (Wall('x', hx1, (-1, 0, 0)), hy0, hy1),
                     (Wall('y', hy0, (0, 1, 0)), hx0, hx1), (Wall('y', hy1, (0, -1, 0)), hx0, hx1)):
    b.rooms['bay_c'] += wall.quad(a0, a1, 1536, SHAFT, 'girder')
b.rooms['bay_c'] += ceiling(hx0, hy0, hx1, hy1, SHAFT, 'sky')
# The roof doors: two leaves that part along x over the bay's ceiling (the finale's launch; nothing opens them yet).
# They have no top faces: unseen, and floor-type faces over the flight deck would crowd it out of the engine's search
# for the sector under a point (findIndoorSectorForPoint takes the first five floors it meets, the bay's first).
for name, x0, x1, direction in (('roof_w', hx0, (hx0 + hx1) / 2, (-1, 0, 0)), ('roof_e', (hx0 + hx1) / 2, hx1,
                                                                                (1, 0, 0))):
    DOORS[name] = len(DOORS) + 1
    b.door(name, 'bay_c', box((x0, hy0, 1600), (x1, hy1, 1616), 'hazard', bottom='shutter'),
           DOORS[name], 520, direction=direction, open_speed=96, close_speed=96)
b.trigger('info_panel_1', 'bay_e', plaque(Wall('x', 3600, (-1, 0, 0)), 2500, 96, 128, 128, 'sign', out=6), 10)
b.decoration('hes_colonial_locker', 300, 2780, 0, 180, event=30)                            # chest 0, the crew locker
for x, y, f, name in ((350, 500, 90, 'hes_container'), (350, 830, 90, 'hes_container'), (3150, 2650, 200,
                       'hes_loader_mech'), (3250, 420, 0, 'hes_fuel_tank'), (600, 2700, 0, 'hes_shelf_rack_tools'),
                      (2950, 150, 0, 'hes_shelf_rack'), (3300, 1000, 40, 'hes_drum'), (3380, 1080, 110, 'hes_drum'),
                      (500, 1950, 60, 'hes_drone_wreck'), (2700, 2500, 0, 'hes_crate_clean')):
    b.decoration(name, x, y, 0, f)

# --- The derelict lander ----------------------------------------------------------------------------------------------
# A small rounded colony craft, nose north, in a docking cradle: a hull lofted along y from an eight-sided section (flat
# bottom on the cradle, vertical sides, a rounded roof), constant from the stern (y 650) to the canopy's end (y 1850),
# then tapering in three steps to a lifted wedge nose at y 2550. Two drive pods on the stern's flanks, two nozzles in its
# face, a gold ventral shield band round the hull's foot. The flight deck is a room inside, through the side hatch.
CX, CRADLE = 1800, 32
PROFILE = [(-350, 0), (350, 0), (350, 234), (310, 351), (220, 432), (100, 475), (-100, 475), (-220, 432),
           (-310, 351), (-350, 234)]
STERN = 650
STATIONS = [(STERN, 1.0, 1.0, 0), (1350, 1.0, 1.0, 0), (1850, 1.0, 1.0, 0), (2150, 0.8, 0.7, 8),
            (2400, 0.55, 0.42, 24), (2550, 0.3, 0.2, 40)]          # (y, width scale, height scale, chin lift)
ROOF = CRADLE + 475
SIDES = len(PROFILE)
CANOPY = {4, 5, 6}                       # the roof edges (profile points 4-5, 5-6, 6-7), glazed from y 1350 to 2100
WINDOWS_SIDE = {3, 7}                    # the upper shoulders, glazed over the flight deck (its side windows)
HATCH_Y, HATCH_Z = (1450, 1706), (64, 250)
bc = b.rooms['bay_c']
bc += box((1230, 540, 0), (2370, 2640, CRADLE), 'hazard', top='grille')                    # the docking cradle


def section(y, su, sz, lift=0):
    return [(CX + u * su, y, CRADLE + lift + z * sz) for u, z in PROFILE]


def outward(points, y):
    cx, cz = CX, CRADLE + 260
    mx = sum(p[0] for p in points) / len(points)
    mz = sum(p[2] for p in points) / len(points)
    return (mx - cx, 0, mz - cz)


for (y0, su0, sz0, l0), (y1, su1, sz1, l1) in zip(STATIONS, STATIONS[1:]):
    s0, s1 = section(y0, su0, sz0, l0), section(y1, su1, sz1, l1)
    for k in range(0 if l1 else 1, SIDES):  # edge 0 is the bottom: on the cradle, except under the lifted chin
        a, c = k, (k + 1) % SIDES
        quad = [s0[a], s0[c], s1[c], s1[a]]
        glazed = k in CANOPY and 1350 <= y0 and y1 <= 2100 or k in WINDOWS_SIDE and y0 == 1350
        role = 'glass' if glazed else 'hull'
        if k == 1 and y0 == STERN:
            role = 'hull_torn'           # the derelict's one scar, on the pod side
        if k == 1 and y0 == 1350:        # the east side with the hatch (vertical, x = CX + 350)
            east = Wall('x', CX + 350, (1, 0, 0))
            for p in rect_minus(1350, 1850, CRADLE, CRADLE + 234, [(*HATCH_Y, *HATCH_Z)]):
                bc += east.quad(*p, 'hull')
            continue
        n = outward(quad, y0) if k else (0, 0, -1)
        if su0 == su1 and sz0 == sz1 and l0 == l1:
            bc.append((quad, role, n))
        else:                            # a tapering step: two triangles (the quad is not planar)
            bc.append(([quad[0], quad[1], quad[2]], role, n))
            bc.append(([quad[0], quad[2], quad[3]], role, n))
bc.append((section(STERN, 1, 1), 'hull', (0, -1, 0)))                                     # the stern
bc.append((section(*STATIONS[-1]), 'hull', (0, 1, 0)))                                   # the blunt nose
for side in (-1, 1):                     # stub wings above the side hatch, swept back, a little anhedral
    root, tip = CX + side * 325, CX + side * 560
    plan = [(root, 1350), (root, 1800), (tip, 1560), (tip, 1400)]
    top = [(x, y, 345 if x == root else 315) for x, y in plan]
    under = [(x, y, z - 30) for x, y, z in top]
    bc.append((top, 'hull', (0, 0, 1)))
    bc.append((under, 'hull', (0, 0, -1)))
    for i in (1, 2, 3):
        j = (i + 1) % 4
        edge = [top[i], top[j], under[j], under[i]]
        mx, my = (plan[i][0] + plan[j][0]) / 2 - CX, (plan[i][1] + plan[j][1]) / 2 - 1575
        bc.append((edge, 'gold' if i == 2 else 'hull', (mx, my, 0)))
FIN = [(STERN, ROOF), (STERN + 320, ROOF), (STERN + 110, ROOF + 230), (STERN + 20, ROOF + 230)]                                  # the tail fin
for x, nx in ((CX - 12, -1), (CX + 12, 1)):
    bc.append(([(x, y, z) for y, z in FIN], 'hull', (nx, 0, 0)))
for i in (1, 2, 3):
    (ya, za), (yb, zb) = FIN[i], FIN[(i + 1) % 4]
    bc.append(([(CX - 12, ya, za), (CX - 12, yb, zb), (CX + 12, yb, zb), (CX + 12, ya, za)],
               'gold' if i == 2 else 'hull',
               (0, (ya + yb) / 2 - STERN - 150, (za + zb) / 2 - ROOF)))
def ring(x, y, z, radius):
    """An octagon across y (a nozzle's dark throat), matching blv_kit.pipe's sides."""
    angles = [math.pi / 8 + k * math.pi / 4 for k in range(8)]
    return [(x + radius * math.cos(a), y, z + radius * math.sin(a)) for a in angles]


for x in (CX - 170, CX + 170):                                                            # the main nozzles
    bc += pipe((x, STERN, 290), (x, STERN - 80, 290), 100, 'gold')
    bc.append((ring(x, STERN - 74, 290, 92), 'glass', (0, -1, 0)))
for x in (CX - 420, CX + 420):                                                            # the drive pods
    bc += pipe((x, STERN - 50, 230), (x, STERN + 450, 230), 110, 'hull', caps=('start', 'end'))
    bc += box((x - 30, STERN + 100, CRADLE), (x + 30, STERN + 300, 124), 'gold')             # their struts
    bc.append((ring(x, STERN - 54, 230, 80), 'glass', (0, -1, 0)))
for x0, x1 in ((CX - 358, CX - 350), (CX + 350, CX + 358)):                               # the ventral shield band
    side = -1 if x0 < CX else 1
    bc += box((x0, STERN, CRADLE + 4), (x1, 1850, CRADLE + 28), 'gold', top='gold',
              skip=('east',) if side < 0 else ('west',))
bc += box((CX - 350, STERN - 8, CRADLE + 4), (CX + 350, STERN, CRADLE + 28), 'gold', top='gold', skip=('north',))
for x in (CX - 360, CX + 360):                                                            # cradle clamps
    for y in (1000, 1750):
        bc += box((x - 14, y - 40, CRADLE), (x + 14, y + 40, 150), 'gold', top='trim')

# The flight deck: a room inside the hull behind the side hatch (its reveal runs through the hull's side).
cp = R['cockpit']
DX0, DY0, DX1, DY1, DZ = cp['x'], cp['y'], cp['x'] + cp['w'], cp['y'] + cp['h'], cp['z']
DZ1 = DZ + cp['ceiling']
b.room('cockpit', (DX0, DY0, DX1, DY1, DZ - 1, DZ1), 20)
ck = b.rooms['cockpit']
ck += floor(DX0, DY0, DX1, DY1, DZ, 'grille')
ck += ceiling(DX0, DY0, DX1, DY1, DZ1, 'glass')
DECK = [(DZ, DZ + 16, 'trim'), (DZ + 16, DZ1 - 32, 'recess'), (DZ1 - 32, DZ1, 'gold')]
ck += blv_kit.banded(Wall('x', DX0, (1, 0, 0)), DY0, DY1, DECK, [])
ck += blv_kit.banded(Wall('x', DX1, (-1, 0, 0)), DY0, DY1, DECK, [(*HATCH_Y, *HATCH_Z)])
ck += blv_kit.banded(Wall('y', DY0, (0, 1, 0)), DX0, DX1, DECK, [])
ck += blv_kit.banded(Wall('y', DY1, (0, -1, 0)), DX0, DX1,
                     [(DZ, DZ + 16, 'trim'), (DZ + 16, DZ + 240, 'console'), (DZ + 240, DZ1, 'glass')], [])
b.opening('cockpit', 'bay_c', 'x', DX1, *HATCH_Y, *HATCH_Z, depth=CX + 350 - DX1, toward=1, floor_role='grille')
ck += box((1660, 1700, DZ), (1940, DY1, DZ + 96), 'hull', top='console')                  # the main console
ck += box((1740, 1520, DZ), (1860, 1600, DZ + 32), 'hull', top='hull')                    # the pilot's seat
ck += box((1740, 1490, DZ), (1860, 1520, DZ + 130), 'hull', top='trim')
b.trigger('lander_console', 'cockpit', plaque(Wall('x', DX0, (1, 0, 0)), 1600, DZ + 64, 160, 128, 'console', out=8),
          19)
# The cell charger (event 70, CR-P4-15): a machine panel on the south wall beside the hatch, seen on stepping in.
b.trigger('cell_charger', 'cockpit', plaque(Wall('y', DY0, (0, 1, 0)), DX1 - 90, DZ + 48, 120, 144, 'machine', out=12),
          70)

# The five sockets (MM6's Oracle alcoves): a decoration each, clicked through its event (20-24), swapped by its cog
# (31-35) between hes_sock_<socket>_dead, _ready (the power is on) and _lit (the part is in). Facing: front = 90 + f.
SOCKETS = [('cockpit', 20, 31, CX, 1750, DZ + 96, 180), ('coil', 21, 32, CX + 420 + 102, STERN + 210, 185, 270),
           ('nav', 22, 33, CX, 2550, 88, 0), ('engine', 23, 34, CX, STERN, CRADLE + 28, 180),
           ('ring', 24, 35, CX - 358, 1650, CRADLE + 28, 90)]
for socket, event, cog, x, y, z, facing in SOCKETS:
    b.decoration(f'hes_sock_{socket}_dead', x, y, z, facing, event=event, cog=cog)

# --- The Reactor Room: the core, its coolant stack and pipes, the breakers, the drones' charging cradles ------------
rc = R['reactor']
RX, RY = -1164, 2000
rr = b.rooms['reactor']
rr += prism(RX, RY, 420, 0, 32, 'hazard', top='grille')                                    # the plinth
rr += prism(RX, RY, 330, 32, 200, 'pitwall', top='trim')
corners = [(RX + 300 * math.cos(math.pi / 8 + k * math.pi / 4), RY + 300 * math.sin(math.pi / 8 + k * math.pi / 4))
           for k in range(8)]
for k in range(8):                                                                         # the core's eight ports
    (ax, ay), (bx2, by2) = corners[k], corners[(k + 1) % 8]
    mx, my = (ax + bx2) / 2 - RX, (ay + by2) / 2 - RY
    length = math.hypot(bx2 - ax, by2 - ay)
    right = ((bx2 - ax) / length, (by2 - ay) / length, 0)
    quad = [(ax, ay, 200), (bx2, by2, 200), (bx2, by2, 430), (ax, ay, 430)]
    rr.append((quad, 'gener', (mx, my, 0), Fit((ax, ay, 200), right, (0, 0, 1), length, 230)))
rr += prism(RX, RY, 330, 430, 560, 'pitwall', top='grille', bottom='trim')
rr += prism(RX, RY, 330, 200, 212, 'gold', bottom='trim')
rr += prism(RX, RY, 120, 560, 768, 'pipe')                                                 # the coolant stack
rr += pipe((RX + 330, 2350, 600), (-64, 2350, 600), 60, 'pipes', caps=('start',))
rr += pipe((-2264, 2650, 620), (RX - 330, 2650, 620), 60, 'pipes', caps=('end',))
west = Wall('x', -2264, (1, 0, 0))
for k, y in enumerate((1700, 2300)):
    cabinet = plaque(west, y, 0, 256, 384, 'machine', out=24)
    b.trigger(f'breaker_{"ab"[k]}', 'reactor', cabinet[:1], 27 + k, cog=101 + k)
    rr += cabinet[1:]
b.trigger('reactor_terminal', 'reactor', plaque(west, 2000, 96, 96, 128, 'console', out=10), 29)
b.trigger('reactor_placard', 'reactor', plaque(west, 1400, 96, 256, 128, 'sign', out=6), 17)
for x in (-2000, -1600, -1200, -800, -400):                                                # the charging cradles
    rr += box((x - 90, 1000, 0), (x + 90, 1136, 72), 'machine', top='grille', skip=('south',))
    rr += box((x - 20, 1000, 72), (x + 20, 1036, 200), 'gold', top='trim', skip=('south',))
b.decoration('hes_drone_wreck', -1900, 1500, 0, 70)
b.decoration('hes_drum', -300, 2800, 0, 20)
b.decoration('hes_drum', -420, 2850, 0, 80)

# --- The Control Stair and Hangar Control -----------------------------------------------------------------------------
st = R['stair']
drop('stair', (0, 0, 1), 0)
b.rooms['stair'] += floor(st['x'], st['y'], -1044, st['y'] + st['h'], 0, 'floor')
b.rooms['stair'] += flight_along((-1044,3382),(236,3382),636,0,40,tread='grille',riser='hazard',rise=16)
drop('stair',(0,0,-1),1088)
b.rooms['stair'] += ceiling(st['x'],st['y'],-1044,st['y']+st['h'],448,'ceiling')
soffit=([(-1044,st['y'],448),(236,st['y'],1088),(236,st['y']+st['h'],1088),
         (-1044,st['y']+st['h'],448)],'ceiling',(0.5,0,-1))
b.rooms['stair'].append(soffit)
# Trim the side walls to the pitched soffit, leaving the original lower doorway clear.
b.rooms['stair']=clip_to(b.rooms['stair'],None,below=((-1044,3382,448),(-.5,0,1)))
co = R['control']
CZ = co['z']
for rid, a0, a1 in WINDOWS:                                                                # mullions in the windows
    count = max(1, round((a1 - a0) / 260))
    for k in range(1, count):
        x = a0 + (a1 - a0) * k / count
        b.rooms['control'] += box((x - 8, 3000, 752), (x + 8, 3064, 1024), 'gold')
cn = Wall('y', 3700, (0, -1, 0))
b.trigger('pilot_link', 'control', plaque(cn, 1000, CZ + 64, 256, 192, 'console', out=10), 34)
b.trigger('info_panel_7', 'control', plaque(cn, 1600, CZ + 96, 192, 160, 'sign', out=6), 16)
b.trigger('roof_controls', 'control', plaque(cn, 2200, CZ + 64, 256, 192, 'machine', out=24), 35)
b.decoration('hes_bench', 700, 3550, CZ, 180)
b.decoration('hes_starport_turret_mount', 2550, 3480, CZ, 90)   # the Starport Turret's colony pedestal

# --- The Fuel Depot: two tanks on saddles, their stand pipes, the coolant leak, the locker ---------------------------
fu = R['fuel']
fr = b.rooms['fuel']
for y in (-700, -1400):
    fr += pipe((800, y, 240), (2300, y, 240), 200, 'tank', caps=('start', 'end'))
    for x in (1000, 1550, 2100):
        fr += box((x - 40, y - 180, 0), (x + 40, y + 180, 70), 'gold', top='trim')
    for x in (1100, 2000):
        fr += prism(x, y, 40, 436, 640, 'pipe')
LEAK = (340, -1800, 700, -300)
drop('fuel', (0, 0, 1), 0)
for a0, a1, z0, z1 in rect_minus(fu['x'], fu['x'] + fu['w'], fu['y'], fu['y'] + fu['h'], [(LEAK[0], LEAK[2],
                                                                                         LEAK[1], LEAK[3])]):
    fr += clip_to(floor(a0, z0, a1, z1, 0, 'ifloor'),FOOTPRINTS['fuel'])
lx0, ly0, lx1, ly1 = LEAK
for wall, a0, a1 in ((Wall('x', lx0, (1, 0, 0)), ly0, ly1), (Wall('x', lx1, (-1, 0, 0)), ly0, ly1),
                     (Wall('y', ly0, (0, 1, 0)), lx0, lx1), (Wall('y', ly1, (0, -1, 0)), lx0, lx1)):
    fr += wall.quad(a0, a1, -24, 0, 'hazard')
b.surface('coolant_leak', 'fuel', floor(lx0, ly0, lx1, ly1, -24, 'brine'), flags=('lava',))
b.trigger('hazard_sign', 'fuel', plaque(Wall('y', -64, (0, -1, 0)), 900, 96, 128, 128, 'sign', out=6), 18)
b.decoration('hes_colonial_locker', 2500, -1850, 0, 0, event=33)                            # chest 3
for x, y, f in ((560, -250, 30), (420, -1880, 110), (2550, -150, 200)):
    b.decoration('hes_drum', x, y, 0, f)

# --- Lights: the plan's (fixtures on the ramp ride its slope) ---------------------------------------------------------
for light in PLAN.lights:
    light = dict(light)
    if light['fixture'] and r['x0'] <= light['x'] <= r['x1'] and light['y'] > r['y0'] and light['z'] < TOP:
        light['z'] += ramp_z(light['y'])
    if light['id']=='F25':light['z']=708
    if light['id'] in ('F26','F27','F28'):light['z']=1030
    b.plan_light(light, COG)

# --- Monsters (build_d00.py writes them into the scene: hesper_stage/monsters.yml rows) -------------------------------
# (monster id, x, y, z, yaw in degrees (0 east, counter-clockwise), group, posted, name). Groups: 1 the ramp, 2 the
# aisle, 3 the range turrets, 4 the bay guard, 5 the nest, 6 the control turret, 7 the depot.
SEEKER, TURRET, CRAWLER = 10050, 10054, 10090
ACTORS = [(SEEKER, 7450, 2700, ramp_z(2700), 270, 1, False, ''), (SEEKER, 7750, 3150, ramp_z(3150), 270, 1, False, ''),
          (CRAWLER, 6050, 1350, 0, 200, 2, False, ''), (CRAWLER, 6300, 1600, 0, 160, 2, False, ''),
          (TURRET, 6950, 300, 0, 180, 3, True, ''), (TURRET, 6950, 800, 0, 180, 3, True, ''),
          (SEEKER, 900, 2300, 0, 0, 4, False, ''), (SEEKER, 2900, 2200, 0, 180, 4, False, ''),
          (SEEKER, 2900, 700, 0, 180, 4, False, ''), (SEEKER, 900, 600, 0, 0, 4, False, '')]
ACTORS += [(SEEKER, x, 1300, 0, 90, 5, False, '') for x in (-2000, -1600, -1200, -800, -400)]
ACTORS += [(SEEKER, -1600, 2700, 0, 270, 5, False, ''), (TURRET, 2550, 3480, CZ, 180, 6, True, '')]
ACTORS += [(CRAWLER, x, y, 0, (x + y) % 360, 7, False, '') for x, y in
           ((1000, -280), (1300, -1050), (1900, -1050), (2500, -1050), (1100, -1750))]
sectors = list(b.rooms)
actors = []
for monster, x, y, z, yaw, group, posted, name in ACTORS:
    rid = b.room_at(x, y, z + 10)
    actors.append({'monster': monster, 'position': [round(x), round(y), round(z)], 'yaw_degrees': yaw,
                   'group': group, 'posted': posted, 'name': name, 'sector': sectors.index(rid) + 1})

start = next(m for m in PLAN.marks if m['kind'] == 'start')
# PICKUPS.md: 2300 faces give 18 satchels, beside supplies and off the walking lanes.
SATCHELS = [
    ('parts', 751, 5050, 850, 0, 240),
    ('parts', 752, 4700, 250, 0, 30),
    ('tech', 753, 4400, 2800, 0, 135),
    ('tech', 754, 5120, 2050, 0, 20),
    ('militia', 755, 6750, 2800, 0, 180),
    ('range', 756, 5750, 300, 0, 45),
    ('aisle_w', 757, 4000, 1750, 0, 200),
    ('aisle_e', 758, 6250, 1200, 0, 70),
    ('bay_w', 759, 400, 1300, 0, 15),
    ('bay_e', 760, 3000, 2100, 0, 160),
    ('bay_e', 761, 3000, 550, 0, 30),
    ('reactor', 762, -2100, 2700, 0, 110),
    ('reactor', 763, -500, 1300, 0, 250),
    ('fuel', 764, 2450, -1100, 0, 210),
    ('fuel', 765, 1300, -1800, 0, 10),
    ('control', 766, 450, 3450, 640, 100),
    ('control', 767, 2300, 3550, 640, 240),
    ('ramp_foot', 768, 7800, 1250, 0, 30),
]
assert len(SATCHELS) == 18 and {p[1] for p in SATCHELS} == set(range(751, 769))
for room, event, x, y, z, facing in SATCHELS:
    assert b.room_at(x, y, z + 1) == room, (room, event)
    b.decoration('hes_colony_satchel', x, y, z, facing, event=event, cog=event)

def inside(rid,x,y):
    points=FOOTPRINTS[rid]
    return all((bx-ax)*(y-ay)-(by-ay)*(x-ax)>=-.1
               for (ax,ay),(bx,by) in zip(points,points[1:]+points[:1]))

for owner,other,axis,plane,a0,a1,z0,z1,toward in openings:
    for rid,edge in ((owner,plane),(other,plane+toward*T)):
        assert all(inside(rid,edge,a) if axis=='x' else inside(rid,a,edge)for a in (a0,a1)),(rid,a0,a1)
for rid,event,x,y,z,facing in SATCHELS:
    assert inside(rid,x,y),(rid,event)

for name,rid,panels,*_ in b.triggers:
    if rid in FOOTPRINTS:
        assert all(inside(rid,v[0],v[1])for panel in panels for v in panel[0]),(name,rid)
for name,x,y,z,*_ in b.decorations+b.lights:
    candidates=[rid for rid,(x0,y0,x1,y1,z0,z1) in b.bounds.items()
                if x0-1<=x<=x1+1 and y0-1<=y<=y1+1 and z0<=z<=z1]
    assert any(rid not in FOOTPRINTS or inside(rid,x,y)for rid in candidates),(name,x,y,z)

b.export({'room_footprints':FOOTPRINTS,'pickups': SATCHELS, 'arrivals': {'surface_door': {'position': [7600, 3650, 482], 'direction_degrees': 270},
                       'bay': {'position': [3300, 1500, 0], 'direction_degrees': 180}},
          'actors': actors, 'door_ids': DOORS, 'chest_events': {30: 0, 31: 1, 32: 2, 33: 3},
          'sockets': {s[0]: {'event': s[1], 'cog': s[2]} for s in SOCKETS}})

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
