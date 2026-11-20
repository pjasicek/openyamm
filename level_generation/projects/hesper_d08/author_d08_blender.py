"""D8 Foundry: plan-owned rooms, links, marks and lights, compiled with the Hesper indoor kit."""
import copy
import importlib.util
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
from blv_kit import (Wall, banded, box, ceiling, chamfer_rect, clip_half, clip_to, flight, floor, hip_ceiling, pipe,
                     plaque, prism, ramp, rect_minus, rect_walls, vault)

spec = importlib.util.spec_from_file_location('zone2', ROOT / 'design/kreegan_world/zone2/dungeons/plans_zone2.py')
zone2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone2)
PLAN = copy.deepcopy(zone2.d8)
assert not zone2.plans.ceiling_problems(PLAN)
assert zone2.plans.max_light_overlap(PLAN)[0] <= 4
R = {r['id']: r for r in PLAN.rooms}
# Integrator's 2026-10-23 fixes: open reward spots, clear of the production row and north-wall racks.
FIXED_CHESTS = {}
for event, rid, light_id in ((30, 'fabA', 'F10'), (32, 'fabB', 'F12'), (33, 'plate', 'F22')):
    r = R[rid]
    # Walkability pass (2026-10-24): the plinths are one 32 step, not a 64 ledge.
    x, y, z = r['x'] + r['w'] - 300, r['y'] + r['h'] - 400, r['z'] + 32
    FIXED_CHESTS[event] = (rid, x, y, z)
    light = next(l for l in PLAN.lights if l['id'] == light_id)
    light.update(x=r['x'] + r['w'], y=y, z=r['z'] + 260, facing=180)
    assert math.dist((x, y, z), (light['x'], light['y'], light['z'])) <= 400
kit.FOLDERS += [ROOT / f'design/kreegan_world/art/textures_{name}/masters'
                for name in ('k6_foundry', 'k5_grafted')]
KEYS = ('hmwall hmwallht hmslag hmtarget hmplate hmplatehot hmgrate hmchan hmchanx hmbelt hmbeltsd hmceil '
        'hmgantry hmpipe hkrib hmgate hmdoor hmfab hmfabpnl hmmould hmrack hmcrate hmglow hkglyph').split()
b = kit.Builder('hes_d08.blv', {**{k: k for k in KEYS}, 'marker': 'hkglyph', 'trim': 'hkrib'},
                PROJECT / 'source', role_scale={'hmwall': 2, 'hmwallht': 2, 'hmceil': 2, 'hmslag': 2})
SPLITS = {'smelt': ([4067, 5733], [3264]), 'furnace': ([], [3264]), 'coolant': ([], [3264]),
          'hall': ([], [10700, 11700]), 'sump': ([2150], []), 'plant': ([8664], []), 'maze': ([4200], []),
          'fabA': ([7564], []), 'fabB': ([7564], []), 'mould': ([], [6860]), 'arming': ([], [9156]),
          'range': ([4200], [])}
AMBIENT = {'smelt': 10, 'hall': 10, 'fabA': 12, 'fabB': 12, 'maze': 12, 'range': 12,
           'mould': 12, 'arming': 12, 'coolant': 14, 'plant': 12, 'furnace': 12, 'sump': 14, 'niche': 14,
           'beltstair': 15, 'hallstair': 15, 'sumpstair': 15, 'plantstair': 15}
cells = {}
for rid, r in R.items():
    xs, ys = SPLITS.get(rid, ([], []))
    xs, ys = [r['x'], *xs, r['x'] + r['w']], [r['y'], *ys, r['y'] + r['h']]
    cells[rid] = []
    low = r['z'] - (129 if rid in ('smelt', 'hall') else 1)
    for j, (y0, y1) in enumerate(zip(ys, ys[1:])):
        for i, (x0, x1) in enumerate(zip(xs, xs[1:])):
            name = f'{rid.lower()}_{i}_{j}'
            cells[rid].append(name)
            b.room(name, (x0, y0, x1, y1, low, r['z'] + r['ceiling']), AMBIENT.get(rid, 12))
            if i:
                b.portal(f'{rid.lower()}_{i-1}_{j}', name,
                         [(x0, y0, low), (x0, y1, low), (x0, y1, r['z'] + r['ceiling']),
                          (x0, y0, r['z'] + r['ceiling'])])
            if j:
                b.portal(f'{rid.lower()}_{i}_{j-1}', name,
                         [(x0, y0, low), (x1, y0, low), (x1, y0, r['z'] + r['ceiling']),
                          (x0, y0, r['z'] + r['ceiling'])])
assert len(b.rooms) == 36

# Room shapes (DUNGEON_PLAYBOOK, 2026-10-24): chamfered corners (rect_walls), clear of every opening, port and fixture.
CHAMFER = {'smelt': 560, 'gate': {'nw': 360, 'ne': 360}, 'niche': 150, 'plant': {'nw': 300, 'ne': 300},
           'mould': {'sw': 300}}
FOOTPRINTS = {rid: chamfer_rect(R[rid]['x'], R[rid]['y'], R[rid]['x'] + R[rid]['w'], R[rid]['y'] + R[rid]['h'], cut)
              for rid, cut in CHAMFER.items()}
SMELT_TOP = 1280          # the Smelting Floor's walls; a hipped ceiling rises from them to its 1536
HALL_SPRING = 768         # the Forgemaster's Hall's walls; a barrel vault rises from them to its 1024


def stair_plane(rid):
    """The sloped ceiling over a stair room: (a point, the upward normal) of its plane, at least 384 over the flight
    and over every opening, rising toward the flight's top."""
    r = R[rid]
    top = r['z'] + r['ceiling']
    return {'beltstair': ((4000, 0, top), (512 / 1152, 0, 1)), 'hallstair': ((0, 8848, top), (0, 0.2, 1)),
            'sumpstair': ((1952, 0, top), (-0.4, 0, 1)), 'plantstair': ((0, 2680, top), (0, -0.4, 1))}[rid]


SLOPED = ('beltstair', 'hallstair', 'sumpstair', 'plantstair')


def clipped(panel, bounds):
    """Split authored polygons at the design's sector planes, preserving fitted UVs."""
    points = [tuple(p) for p in panel[0]]
    for axis, edge, sign in ((0, bounds[0], 1), (0, bounds[2], -1),
                             (1, bounds[1], 1), (1, bounds[3], -1)):
        result = []
        for a, c in zip(points, points[1:] + points[:1]):
            da, dc = sign * (a[axis] - edge), sign * (c[axis] - edge)
            if da >= 0:
                result.append(a)
            if (da < 0) != (dc < 0):
                t = da / (da - dc)
                result.append(tuple(a[k] + t * (c[k] - a[k]) for k in range(3)))
        points = result
        if len(points) < 3:
            return None
    # A polygon lying on a split plane belongs to one sector, never two coincident walls.
    return (points, *panel[1:])


def add(rid, panels, *, name=None, cog=0, flags=(), event=0, kind='click'):
    if rid in FOOTPRINTS:
        panels = clip_to(panels, FOOTPRINTS[rid])
    for cell in cells[rid]:
        cut = [p for panel in panels if (p := clipped(panel, b.bounds[cell]))]
        if not cut:
            continue
        if name:
            b.trigger(f'{name}_{cell}', cell, cut, event, kind=kind, flags=flags, cog=cog)
        else:
            b.rooms[cell] += cut


def cell_at(rid, x, y):
    return next(c for c in cells[rid] if b.bounds[c][0] <= x <= b.bounds[c][2]
                and b.bounds[c][1] <= y <= b.bounds[c][3])


def control_glow(rid, wall, along, z, lid):
    add(rid, plaque(wall, along, z - 16, 96, 32, 'hmglow', out=8, edge='hmgantry'))
    x, y, z = wall.point(along, z, out=24)
    PLAN.light(lid, R[rid]['floor'], x, y, z, 320, (255, 140, 60))


# Each tuple names the two rooms of the corresponding plan link; positions and widths remain plan-owned.
LINK_ROOMS = {1: ('gate', 'north', 'smelt', 60, 768), 2: ('furnace', 'east', 'smelt', 61, 512),
              3: ('smelt', 'east', 'coolant', 65, 512), 4: ('smelt', 'north', 'beltstair', 0, 384),
              5: ('coolant', 'east', 'plantstair', 68, 384), 6: ('plant', 'north', 'plantstair', 0, 384),
              7: ('sumpstair', 'north', 'furnace', 69, 384), 8: ('sump', 'north', 'sumpstair', 0, 384),
              9: ('sump', 'east', 'niche', 66, 384), 10: ('beltstair', 'north', 'maze', 0, 384),
              11: ('maze', 'east', 'fabA', 0, 640), 15: ('fabA', 'north', 'fabB', 90, 512),
              16: ('fabA', 'east', 'mould', 91, 512), 17: ('mould', 'north', 'arming', 92, 448),
              18: ('range', 'east', 'fabB', 93, 512), 19: ('range', 'east', 'hallstair', 94, 384),
              20: ('hall', 'east', 'hallstair', 95, 768), 21: ('hall', 'east', 'plate', 67, 448)}
holes, openings, DOORS = {}, [], {}
for index, (owner, side, other, door, height) in LINK_ROOMS.items():
    link = PLAN.links[index]
    axis = 'y' if side == 'north' else 'x'
    centre = link['x'] if axis == 'y' else link['y']
    plane = R[owner][axis] + R[owner]['h' if axis == 'y' else 'w']
    z = PLAN.floors[link['floor']]
    if index == 11:
        # The main belt's mouth lies at the belt's top (896), so the lowered crates and the belt run flush into Fab
        # Line A's stair; a 768 reveal left a 128 hole between them that monsters could not cross.
        z, height = z + 128, height - 128
    a0, a1 = centre - link['width'] / 2, centre + link['width'] / 2
    holes.setdefault(owner, {}).setdefault(side, []).append((a0, a1, z, z + height))
    holes.setdefault(other, {}).setdefault('south' if axis == 'y' else 'west', []).append((a0, a1, z, z + height))
    openings.append((owner, other, axis, plane, a0, a1, z, z + height, door))
holes.setdefault('gate', {})['south'] = [(4516, 5284, 0, 640)]
ports = []
for lid, rid, side in (('F2', 'furnace', 'west'), ('F3', 'furnace', 'west'),
                       ('F13', 'mould', 'east'), ('F_hall1', 'hall', 'north'), ('F_hall2', 'hall', 'north')):
    light = next(l for l in PLAN.lights if l['id'] == lid)
    axis = 'y' if side == 'north' else 'x'
    inward = (0, -1, 0) if side == 'north' else (1, 0, 0) if side == 'west' else (-1, 0, 0)
    wall = Wall(axis, light[axis], inward)
    along = light['x'] if axis == 'y' else light['y']
    holes.setdefault(rid, {}).setdefault(side, []).append((along-192, along+192, light['z']-128, light['z']+128))
    ports.append((rid, wall, along, light['z']))
    light.update(fixture=None, x=light['x']+inward[0]*16, y=light['y']+inward[1]*16)
CUSTOM = {'smelt', 'hall', 'beltstair', 'hallstair', 'sumpstair', 'plantstair'}
for rid, r in R.items():
    x, y, z, w, h, height = (r[k] for k in ('x', 'y', 'z', 'w', 'h', 'ceiling'))
    wall = 'hmslag' if rid in ('sump', 'sumpstair', 'niche') else 'hmtarget' if rid == 'range' else 'hmwall'
    bands = [(z, z + height - 64, wall), (z + height - 64, z + height, 'hmgantry')]
    if rid == 'smelt':
        bands = [(0, 768, 'hmwall'), (768, SMELT_TOP - 64, 'hmwallht'), (SMELT_TOP - 64, SMELT_TOP, 'hmgantry')]
    elif rid == 'hall':
        bands = [(z, HALL_SPRING - 64, 'hmwallht'), (HALL_SPRING - 64, HALL_SPRING, 'hmgantry')]
    if rid in CHAMFER:
        add(rid, rect_walls(x, y, x + w, y + h, bands, holes.get(rid), CHAMFER[rid]))
    else:
        walls = []
        for side, plane, a0, a1 in (
                ('south', Wall('y', y, (0, 1, 0)), x, x + w),
                ('north', Wall('y', y + h, (0, -1, 0)), x, x + w),
                ('west', Wall('x', x, (1, 0, 0)), y, y + h),
                ('east', Wall('x', x + w, (-1, 0, 0)), y, y + h)):
            walls += banded(plane, a0, a1, bands, holes.get(rid, {}).get(side, []))
        add(rid, clip_to(walls, None, below=stair_plane(rid)) if rid in SLOPED else walls)
    if rid == 'smelt':
        add(rid, hip_ceiling(FOOTPRINTS[rid], SMELT_TOP, z + height, 'hmceil', top=0.55))
    elif rid == 'hall':
        add(rid, vault(x, y, x + w, y + h, HALL_SPRING, z + height - HALL_SPRING, 'x', 'hmceil', segments=8,
                       ends='hmwallht'))
    elif rid in SLOPED:
        # A sloped ceiling over the flight; the flat ceiling stays only where the slope would rise above it.
        (qx, qy, qz), (nx, ny, _) = stair_plane(rid)
        slope = [(px, py, qz - nx * (px - qx) - ny * (py - qy)) for px, py in
                 ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
        add(rid, clip_to([(slope, 'hmceil', (0, 0, -1))], None, below=((0, 0, z + height), (0, 0, 1))))
        (point, normal), flat = stair_plane(rid), ceiling(x, y, x + w, y + h, z + height, 'hmceil')
        add(rid, [p for p in (clip_half(c, point, normal) for c in flat) if p])
    else:
        add(rid, ceiling(x, y, x + w, y + h, z + height, 'hmceil'))
    if rid not in CUSTOM:
        role = 'hmchanx' if rid in ('sump', 'niche') else 'hmgrate' if rid in ('furnace', 'coolant', 'plant', 'maze') else 'hmplate'
        add(rid, floor(x, y, x + w, y + h, z, role))

for rid, wall, along, z in ports:
    face, jambs = kit.recessed_door(wall, along, z-128, 384, 256, 'hmglow', depth=32, trim='hmgantry')
    sill = ([wall.point(along-192, z-128), wall.point(along+192, z-128),
             wall.point(along+192, z-128, out=-32), wall.point(along-192, z-128, out=-32)],
            'hmgantry', (0, 0, 1))
    for cell in cells[rid]:
        bounds = list(b.bounds[cell])
        # Keep the 32-unit recess inside the wall, while still splitting the Mould Shop's port at its sector seam.
        axis = 0 if wall.axis == 'x' else 1
        bounds[axis] -= 32
        bounds[axis+2] += 32
        b.rooms[cell] += [p for panel in face+jambs+[sill] if (p := clipped(panel, bounds))]

for owner, other, axis, plane, a0, a1, z0, z1, door in openings:
    centre = (a0 + a1) / 2
    p0 = (centre, plane) if axis == 'y' else (plane, centre)
    p1 = (centre, plane + 64) if axis == 'y' else (plane + 64, centre)
    oc, tc = cell_at(owner, *p0), cell_at(other, *p1)
    b.opening(oc, tc, axis, plane, a0, a1, z0, z1, floor_role='hmplate')
    if door:
        name = f'door_{door}'
        DOORS[name] = door
        lo, hi = (a0, plane + 24, z0), (a1, plane + 40, z1)
        if axis == 'x':
            lo, hi = (plane + 24, a0, z0), (plane + 40, a1, z1)
        role = 'hmslag' if door == 66 else 'hmgate' if door == 95 else 'hmdoor'
        seconds = 3 if door in (60, 95) else 2 if door in (66, 67) else 1.5
        b.door(name, oc, box(lo, hi, role, top='hkrib', bottom='hkrib'), door, z1-z0,
               direction=(0, 0, -1 if door == 66 else 1), open_speed=(z1-z0)/seconds,
               event=door + 100 if door in (60, 61, 65, 66, 67, 68, 69, 90, 91, 92, 93, 94) else 0,
               flags=('secret',) if door == 66 else ())
        if door == 60:
            add('gate', box((a0, plane-12, 0), (a1, plane, 16), 'hmglow', top='hmglow'))
            PLAN.light('L_shutter_lip', R['gate']['floor'], centre, plane-24, 80, 384, (255, 120, 40))

# The five independently switchable beds have no lava-prefixed texture (the native name test is permanent).
channels = [m for m in PLAN.marks if m['kind'] == 'trap']
# The Forgemaster's seal opens onto a plate at floor level (the hall's east edge is no longer raised).
SEAL_PLATE = (5808, 6000, 10026, 10474)
# The ramps down from the raised west edge (x from, x to, y centre); the floor is cut away under them, or monsters
# keep the floor as their support at a ramp's foot and walk in under it.
WEST_RAMPS = [(2800, 3056, y) for y in (11200, 12310)]
BANK = 160                # each channel's sloped banks (39 degrees): monsters and the party walk in and out anywhere
for rid, indices, width in (('smelt', range(3), 400), ('hall', range(3, 5), 500)):
    r = R[rid]
    cuts = []
    x0, x1 = r['x'], r['x'] + r['w']
    if rid == 'hall':
        x1 -= 400
        cuts += [(a, c, y - 160, y + 160) for a, c, y in WEST_RAMPS]
    cuts = [(x0, x1, channels[i]['y']-width/2, channels[i]['y']+width/2) for i in indices] + cuts
    if rid == 'hall':
        # The east walkway (where the raised east edge stood) is grating the stoking never reaches, like the west edge.
        cuts.append((x1, r['x'] + r['w'], r['y'], r['y'] + r['h']))
        for a, c, d, e in rect_minus(x1, r['x'] + r['w'], r['y'], r['y'] + r['h'], [SEAL_PLATE]):
            add(rid, floor(a, d, c, e, 0, 'hmgrate'))
    for a, c, d, e in rect_minus(r['x'], r['x'] + r['w'], r['y'], r['y']+r['h'], cuts):
        panels = floor(a, d, c, e, 0, 'hmplate')
        add(rid, panels, name='stoking' if rid == 'hall' else None, cog=185 if rid == 'hall' else 0)
    for i in indices:
        y0, y1 = channels[i]['y']-width/2, channels[i]['y']+width/2
        if rid == 'smelt':
            assert y0 - r['y'] > CHAMFER['smelt'] and r['y'] + r['h'] - y1 > CHAMFER['smelt']
        add(rid, floor(x0, y0 + BANK, x1, y1 - BANK, -128, 'hmchan'), name=f'channel_{i}', cog=180+i, flags=('lava',))
        for y, direction in ((y0, 'south'), (y1 - BANK, 'north')):
            add(rid, ramp(x0, y, x1, y + BANK, -128, 0, direction, top='hmchan'),
                name=f'channel_steps_{i}_{direction}', cog=180+i, flags=('lava',))
        add(rid, Wall('x', x0, (1, 0, 0)).quad(y0, y1, -128, 0, 'hmwall'))
        add(rid, Wall('x', x1, (-1, 0, 0)).quad(y0, y1, -128, 0, 'hmwall'))
        if rid == 'hall':
            add(rid, box((x1, y0, 0), (x1+16, y1, 64), 'hmgantry', top='hmgantry'))   # a rail where it ends

# Gantry bridges lie flush with the floor across each channel, railed on both sides.
for x, y in ((3400, 2300), (6400, 3200), (3400, 4100)):
    add('smelt', floor(x-200, y-200, x+200, y+200, 0, 'hmgantry'))
    add('smelt', Wall('x', x-200, (-1, 0, 0)).quad(y-200, y+200, -32, 0, 'hmgantry'))
    add('smelt', Wall('x', x+200, (1, 0, 0)).quad(y-200, y+200, -32, 0, 'hmgantry'))
    for rx in (x-200, x+184):
        add('smelt', box((rx, y-232, 0), (rx+16, y+232, 56), 'hmgantry', top='hmgantry'))
# The raised west edge (its valves): two railed ramps down to the floor between the channels, so monsters follow the
# party up; its old south flight climbed from the wall and was reached only from its sheer side.
add('hall', box((2400, 9992, -128), (2800, 12600, 128), 'hmgantry', top='hmgrate'))
for a, c, y in WEST_RAMPS:
    add('hall', ramp(a, y - 160, c, y + 160, 0, 128, 'west', top='hmgrate', skirt='hmgantry', rail=48,
                     rail_role='hmgantry'))
add('hall', floor(*SEAL_PLATE[::2], *SEAL_PLATE[1::2], 0, 'hmgrate'), name='fight_start', event=150,
    kind='pressure_plate')

# The design's landings and flights; no lower duplicate floor under a stair.
for rid, rect, direction, low, landing_a, landing_b in (
        ('beltstair', (4000, 5128, 5152, 6028), 'west', 0,
         (5152, 5128, 5600, 6028, 0), (3600, 5128, 4000, 6028, 768)),
        ('sumpstair', (800, 500, 1952, 1400), 'east', -768,
         (400, 500, 800, 1400, -768), (1952, 500, 2400, 1400, 0)),
        # 42-deep treads end the flight south of the Coolant Gallery's door (it opened half over the top treads).
        ('plantstair', (8728, 1672, 9628, 2680), 'north', -768,
         (8728, 1464, 9628, 1672, -768), (8728, 2680, 9628, 3064, 0)),
        ('hallstair', (6064, 8848, 7064, 10000), 'south', 0,
         (6064, 10000, 7064, 10500, 0), (6064, 8400, 7064, 8848, 768))):
    add(rid, flight(*rect, low, 24, direction, tread='hmplate', riser='hmgantry'))
    add(rid, floor(*landing_a, 'hmplate'), name='landing_pause' if rid == 'hallstair' else None,
        event=153 if rid == 'hallstair' else 0, kind='pressure_plate')
    add(rid, floor(*landing_b, 'hmplate'))

CRATE_XS = [PLAN.links[12+i]['x'] for i in range(3)]
for i, y in enumerate((6400, 6900, 7400)):
    # Belt 1 runs into the mouth: its end face is the maze wall's, its top leaves the holes the crates drop into.
    # Each belt's railed stair climbs from the floor west of it (its foot was against the wall, reached only from
    # its open sides).
    add('maze', box((2784, y-150, 768), (6000, y+150, 896), 'hmbeltsd', skip=('east',) if i == 0 else ()))
    top = [(2784, 6000)] if i else [(a, c) for a, c, _, _ in
                                    rect_minus(2784, 6000, 0, 1, [(x-84, x+84, 0, 1) for x in CRATE_XS])]
    for a, c in top:
        add('maze', floor(a, y-150, c, y+150, 896, 'hmbelt'))
    add('maze', flight(2592, y-150, 2784, y+150, 768, 4, 'east', tread='hmbelt', riser='hmbeltsd'))
    for ry in (y-150, y+134):
        add('maze', box((2592, ry, 768), (2784, ry+16, 960), 'hmbeltsd', top='hmbeltsd'))
for i, x in enumerate(CRATE_XS):
    name = f'crate_{i+1}'
    DOORS[name] = 62+i
    # Each crate fills the belt's width; lowered, its top is the belt's (it fills exactly the hole it leaves).
    crate = box((x-84, 6250, 896), (x+84, 6550, 1280), 'hmcrate', top='hmcrate', bottom='hmcrate', skip=('west',))
    crate += banded(Wall('x', x-84, (-1, 0, 0)), 6250, 6550,
                    [(896, 1088, 'hmcrate'), (1088, 1152, 'hmglow'), (1152, 1280, 'hmcrate')], [])
    crate += floor(x-60, 6314, x+60, 6486, 1281, 'hmglow')
    b.door(name, cell_at('maze', x, 6420), crate, 62+i, 384, direction=(0, 0, -1), open_speed=256)

add('range', box((2400, 7756, 768), (3000, 9356, 1024), 'hmgantry', top='hmgrate'))
add('range', flight(3000, 7756, 3384, 8056, 768, 8, 'west', tread='hmgrate', riser='hmgantry'))
add('range', box((3000, 8040, 768), (3384, 8056, 1072), 'hmgantry', top='hmgantry'))
add('fabA', flight(6064, 6100, 6256, 6740, 768, 4, 'west', tread='hmbelt', riser='hmbeltsd'))
for ry in (6100, 6724):
    add('fabA', box((6064, ry, 768), (6256, ry+16, 944), 'hmbeltsd', top='hmbeltsd'))
face, jambs = kit.recessed_door(Wall('y', 0, (0, 1, 0)), 4900, 0, 768, 640, 'hmgate', trim='hkrib')
b.rooms[cells['gate'][0]] += jambs
b.trigger('slag_gate', cells['gate'][0], face, 50)

interacts = [m for m in PLAN.marks if m['kind'] == 'interact']
for i, m in enumerate(interacts[:7]):
    x, y = m['x'], m['y']
    z = 128 if i in (3, 4) else 0           # W1, W2 on the raised west edge; E1, E2 on the floor of the east side
    if i == 6:
        y = 12200                           # E2 stood in the Plate Stores' doorway
    facing = 270 if x == 2400 else 90
    event = 70+i if i < 3 else 80+i-3
    b.decoration('hes_valve_body', x, y, z, facing, cog=260+i)
    b.decoration('hes_valve_sooted', x, y, z+107, facing, event=event, cog=160+i)
    control_glow('coolant' if i < 3 else 'hall', Wall('x', x, (1, 0, 0) if x == 2400 else (-1, 0, 0)),
                 y, z+280, f'valve_{event}')
    if i < 3:
        add('coolant', pipe((7464, y, -80), (8664, y, -80), 80, 'hmpipe'))
        add('coolant', prism(8584, y, 80, -80, 128, 'hmpipe'))
for i, m in enumerate(interacts[7:10]):
    b.decoration('hes_diverter', m['x'], m['y'], 896, 0, event=74+i, cog=170+i)
    x, y = m['x'], m['y']
    add('maze', box((x-24, y+48, 896), (x+24, y+64, 1184), 'hmgantry', top='hmgantry'))
    control_glow('maze', Wall('y', y+48, (0, -1, 0)), x, 1168, f'diverter_{74+i}')
m = interacts[11]
add('range', plaque(Wall('y', 7756, (0, 1, 0)), m['x'], 1088, 160, 160, 'hkglyph'),
    name='range_console', event=77)
control_glow('range', Wall('y', 7756, (0, 1, 0)), m['x'], 1296, 'range_console')
add('smelt', plaque(Wall('y', 1464, (0, 1, 0)), interacts[12]['x'], 800, 320, 200, 'hkglyph'),
    name='shutter_glyph', event=10)
add('maze', plaque(Wall('x', 6000, (-1, 0, 0)), 6420, 1300, 320, 180, 'hkglyph'), name='jam_glyph', event=11)

chest_events = {}
for kind, events in (('chest_fixed', [30, 32, 33]), ('chest_random', [31, 35, 38, 39, 34])):
    for m, event in zip([m for m in PLAN.marks if m['kind'] == kind], events):
        locker = event in (38, 39)
        x, y, z = m['x'], m['y'], PLAN.floors[m['floor']]
        if event in FIXED_CHESTS:
            rid, x, y, z = FIXED_CHESTS[event]
            add(rid, box((x-160, y-160, z-32), (x+160, y+160, z), 'hmgantry', top='hmplate'))
        b.decoration('hes_colonial_locker' if locker else 'hes_kreegan_pod_chest', x, y, z, event=event)
        chest_events[event] = {30: 1, 32: 2, 33: 3, 31: 4, 34: 5, 35: 6, 38: 7, 39: 8}[event]
for m, event in zip([m for m in PLAN.marks if m['kind'] == 'item' and 'cache' in m['label']], (36, 37)):
    z = 768 if event == 37 else 0
    b.decoration('hes_goods_cells', m['x'], m['y'], z, event=event)

# Furnishings are derived from the named walls/centrelines in section 7; the plan has no furnishing markers.
for x in (3400, 6400):
    add('smelt', box((x-300, R['smelt']['y'], 768), (x+300, 5064, 864), 'hmgantry',
                     top='hmgantry', bottom='hmgantry'))
    # Each gantry's arm and bed sit in the dry band between C1 and C2.
    y = (channels[0]['y'] + channels[1]['y']) / 2
    add('smelt', box((x-600, y-150, 560), (x+600, y+150, 768), 'hmfab', bottom='hmfabpnl'))
    x += 600 if x < 5000 else -600
    add('smelt', prism(x, y, 200, 352, 560, 'hmfabpnl', bottom='hmfabpnl', sides=4))
    add('smelt', box((x-300, y-180, 0), (x+300, y+180, 160), 'hmfabpnl', top='hmfabpnl'))
    b.decoration('hes_armour_plate', x, y, 160)

r = R['fabA']
# A southern production row leaves the north half clear between the jam and Fab B's door.
line_y = r['y'] + r['h']/2 - 300
add('fabA', box((r['x']+320, line_y-110, 768), (r['x']+r['w']-320, line_y+110, 864),
                'hmbeltsd', top='hmbelt'))
for i in range(4):
    x = r['x'] + 560 + i*(r['w']-1120)/3
    add('fabA', prism(x, line_y, 170, 864, 960, 'hmfabpnl', top='hmfabpnl'))
    add('fabA', box((x-230, line_y-160, 1216), (x+230, line_y+160, 1344), 'hmfab', bottom='hmfabpnl'))
    add('fabA', box((x-180, line_y-220, 768), (x-100, line_y-160, 1344), 'hmgantry'))
    b.decoration('hes_armour_plate', x, line_y, 960)
r = R['fabB']
x, y = r['x'] + r['w']/2, r['y'] + r['h'] - 400
add('fabB', box((x-600, y-150, 864), (x+600, y+150, 896), 'hmfabpnl', top='hmfabpnl'))
for dx in (-480, 480):
    add('fabB', box((x+dx-48, y-100, 768), (x+dx+48, y+100, 864), 'hmgantry'))
for rid, role, count in (('fabB', 'hmmould', 2), ('mould', 'hmmould', 3),
                          ('arming', 'hmrack', 3), ('plate', 'hmrack', 3)):
    r = R[rid]
    wall = Wall('y', r['y']+r['h'], (0, -1, 0))
    for i in range(count):
        x = r['x'] + r['w']*(i+0.5)/count
        width = min(560, r['w']/count-96)
        if any(h[0] < x + width/2 and h[1] > x - width/2 for h in holes.get(rid, {}).get('north', [])):
            continue                        # the Mould Shop's middle rack hung across the Arming Bay's door
        add(rid, plaque(wall, x, r['z']+32, width, r['ceiling']-96, role, out=48))

r = R['range']
for i in range(3):
    x = r['x'] + r['w']*(0.42 + i*0.15)
    y = r['y'] + r['h']*(0.30 if i % 2 else 0.7)
    add('range', box((x-400, y-80, 768), (x+400, y+80, 1152), 'hmwall', top='hmwall'))
    x = r['x']+r['w']-250
    y = (8340, 9000, 9250)[i]  # East-wall intervals outside the Fab B and Hall Stair openings.
    add('range', box((x-150, y-50, 768), (x+150, y+50, 1368), 'hmtarget', top='hmtarget'))

r = R['plant']
for i in range(3):
    x, y = r['x']+r['w']*(i+0.5)/3, r['y']+320
    # Section 7's 640-high pumps exceed the plan's 512 ceiling: keep the ceiling and compress the stacks to 448.
    add('plant', prism(x, y, 300, -768, -704, 'hmgantry', top='hmfabpnl'))
    add('plant', prism(x, y, 250, -704, -384, 'hmfabpnl', top='hmfabpnl'))
    add('plant', prism(x, y, 280, -384, -320, 'hmfabpnl', top='hmfabpnl'))
    add('plant', pipe((x, y, -400), (x, r['y'], -400), 80, 'hmpipe'))

r = R['sump']
for i in range(3):
    x = r['x']+r['w']*(i+0.5)/3
    y = r['y']+r['h']/2
    add('sump', floor(x-300, y-300, x+300, y+300, -767, 'hmchan'),
        name=f'slag_pool_{i}', flags=('lava',))
for i in range(4):
    r = R['smelt']
    # Clear of the chamfered corners.
    x = r['x']+420 if i % 2 == 0 else r['x']+r['w']-420
    y = r['y']+440 if i < 2 else r['y']+r['h']-440
    b.decoration('hes_ore_sledge', x, y, 0, 90)
for i, y in enumerate((1864, 3650, 4664)):
    b.decoration('hes_slag_heap', R['smelt']['x']+600, y, 0)
niche_locker = next(m for m in PLAN.marks if m['kind'] == 'chest_random' and 'foundryman' in m['label'])
b.decoration('hes_corpse_colonist', niche_locker['x'], niche_locker['y']+180, -768, 90)
for light in PLAN.lights:
    if light['id'] == 'B_smelt':
        light.update(x=2900, y=4650)        # the fire bowl stood in the Smelting Floor's chamfered corner
    b.plan_light(light, zone2.plans.FIXTURE_COG)

# Check the revised light positions on the room floors and authored raised surfaces, with every light on.
light_check = copy.copy(PLAN)
light_check.lights = [dict(light, floor='all') for light in PLAN.lights]
light_check.rooms = []
for rid, panels in list(b.rooms.items()) + [(t[1], t[2]) for t in b.triggers] + [(m[1], m[2]) for m in b.mechanisms]:
    for points, role, normal, *_ in panels:
        if normal[2] <= 0 or len({round(p[2], 4) for p in points}) != 1:
            continue
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        light_check.rooms.append(dict(name=rid, floor='all', x=min(xs), y=min(ys), w=max(xs)-min(xs),
                                      h=max(ys)-min(ys), z=points[0][2]))
overlap, where = zone2.plans.max_light_overlap(light_check, step=32)
assert overlap <= 4, (overlap, where)
assert len(ports) == 5 and len(PLAN.lights) == 55
(PROJECT/'review/fixes_checks.json').write_text(json.dumps(dict(max_light_overlap=overlap, overlap_at=where,
    sample_step=32, lights=len(PLAN.lights), furnace_ports=len(ports), fixed_chests=FIXED_CHESTS,
    ambient=AMBIENT, crate_gap=32), indent=2)+'\n')

packs = [m for m in PLAN.marks if m['kind'] in ('monster', 'boss')]
PACKS = [(10001, 20), (10001, 21), (10001, 22), (10002, 23), (10020, 24), (10020, 24), (10020, 24),
         (10002, 25), (10001, 26), (10002, 27), (10001, 28), (10001, 29), (10020, 35),
         [(10020, 36)]*4 + [(10001, 36)]*2, [(10040, 30)]*2 + [(10021, 37)]*2, (10002, 38),
         [(10020, 39)]*3 + [(10021, 39)]*2, (10056, 34), (10021, 40), (10021, 41),
         [(10110, 31), (10002, 32), (10002, 32)], (10002, 33)]
actors = []
for m, entries in zip(packs, PACKS):
    entries = entries if isinstance(entries, list) else [entries]*m['count']
    for i, (monster, group) in enumerate(entries):
        # Pack members fan out around their plan marker; the single boss remains exactly at its marker.
        x = m['x'] + (0 if i == 0 else 180 * math.cos(i * 2.39996))
        y = m['y'] + (0 if i == 0 else 180 * math.sin(i * 2.39996))
        z = PLAN.floors[m['floor']]
        # Walkability pass (2026-10-24): every pack stands on clear floor (check_walkability.py's actor check).
        for c in channels[:3] if m['floor'] == 'Floor (z 0)' and group != 24 else ():
            if abs(y - c['y']) < 200 + 100:
                y = c['y'] + (300 if y > c['y'] else -300)
        if group == 24:
            z = 0                           # the bridges are flush with the floor
        elif group == 29:
            # Two ride the middle belt, two walk the gaps beside it; clear of diverter 2's hit target.
            x, y, z = ((3500, 6900, 896), (3800, 6900, 896), (3650, 6650, 768), (3650, 7150, 768))[i]
        elif group == 35:
            x, y = (5100, 6650) if i == 0 else (5260, 6650)     # in the gap north of the jammed belt
        elif group == 36:
            y = max(y, 6020)                # north of Fab Line A's production row
        if m['label'].startswith("The Forgemaster's journeymen"):
            y -= 160                        # clear of Fab Line B's finishing bench
        elif group == 28:
            y += 150                        # clear of the pumps' plinths
        elif group == 34:
            x, y, z = m['x'], m['y'] + (i-1.5)*300, 1024
        elif group == 41:
            z = max(0, min(768, math.ceil((10000-y)/48)*32))
        sector = b.room_at(x, y, z)
        actors.append({'monster': monster, 'group': group, 'name': m['label'],
                       'position': [round(x), round(y), z], 'sector': list(b.rooms).index(sector)+1,
                       'posted': group in (24, 30, 31, 34, 35, 41), 'yaw_degrees': 0 if group == 34 else 270})
assert len(actors) == 72
start = next(m for m in PLAN.marks if m['kind'] == 'start')
# PICKUPS.md: wall-side supplies; event order is persistent pickup identity.
PICKUP_VATS = [
    ('arming', 10750, 8700, 768),
    ('arming', 10750, 8920, 768),
    ('arming', 10750, 9140, 768),
    ('arming', 10750, 9360, 768),
    ('arming', 10750, 9580, 768),
    ('coolant', 7620, 4560, 0),
    ('coolant', 7620, 4760, 0),
    ('coolant', 7620, 4960, 0),
    ('plant', 7650, 1100, -768),
    ('plant', 7870, 1100, -768),
]
PICKUP_BUNDLES = [
    ('gate', 4200, 250, 0),
    ('smelt', 7160, 2750, 0),
    ('smelt', 7000, 4500, 0),
    ('furnace', 600, 4750, 0),
    ('furnace', 2100, 1900, 0),
    ('coolant', 8470, 1820, 0),
    ('coolant', 8460, 4720, 0),
    ('plant', 9640, 1150, -768),
    ('plant', 8200, 1200, -768),
    ('sump', 620, -1000, -768),
    ('sump', 3750, -1020, -768),
    ('niche', 4100, -980, -768),
    ('maze', 2580, 6150, 768),
    ('maze', 5800, 7610, 768),
    ('fabA', 6450, 6650, 768),
    ('fabB', 6250, 7040, 768),
    ('mould', 10750, 5800, 768),
    ('arming', 9300, 9650, 768),
    ('range', 3500, 7900, 768),
    ('plate', 6250, 11980, 0),
]
assert (len(PICKUP_VATS), len(PICKUP_BUNDLES)) == (10, 20)
pickups = []
for model, first, positions in (("hes_serum_vat", 701, PICKUP_VATS),
                                 ("hes_scrap_bundle", 751, PICKUP_BUNDLES)):
    for event, (room, x, y, z) in enumerate(positions, first):
        b.decoration(model, x, y, z, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x, y, z]))

b.export({'pickups': pickups, 'arrivals': {'d08_slag_gate': {'position': [start['x'], start['y'], 0], 'direction_degrees': 90}},
          'door_ids': DOORS, 'chest_events': chest_events, 'monster_packs': packs, 'actors': actors,
          'channels': channels, 'boss_actor': next(i for i, a in enumerate(actors) if a['group'] == 31),
          'fixed_chests': FIXED_CHESTS})
