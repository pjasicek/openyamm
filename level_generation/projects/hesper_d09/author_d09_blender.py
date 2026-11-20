"""D9 Brood Pits: plan-driven BLV authoring. Run in background Blender from this directory."""
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
from blv_kit import (Wall, banded, box, ceiling, chamfer_rect, clip_to, floor, flight, flight_along,
                     hip_ceiling, plaque, prism, ramp, rect_minus, rect_walls)

spec = importlib.util.spec_from_file_location('zone3', ROOT / 'design/kreegan_world/zone3/dungeons/plans_zone3.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d9
assert not zone.plans.ceiling_problems(PLAN)
assert zone.plans.max_light_overlap(PLAN)[0] <= 4
R = {r['id']: dict(r) for r in PLAN.rooms}
kit.FOLDERS.append(ROOT / 'design/kreegan_world/art/textures_k7_hive/masters')
ROLES = {name: 'hb' + name for name in ('flesh', 'fold', 'root', 'sink', 'egg', 'shaft', 'glow', 'floor', 'wet',
                                      'bones', 'ceil', 'crust', 'acid', 'gland', 'vatrim', 'door', 'mother')}
ROLES.update(trim='hbfold', marker='hbglow')
b = kit.Builder('hes_d09.blv', ROLES, PROJECT / 'source')
holes, openings, doors = {}, [], {}


def connect(owner, side, other, centre, width, height=400, z=None, event=0):
    o, t = R[owner], R[other]
    z = o['z'] if z is None else z
    opposite = {'west': 'east', 'east': 'west', 'north': 'south', 'south': 'north'}[side]
    axis = 'x' if side in ('west', 'east') else 'y'
    toward = -1 if side in ('west', 'south') else 1
    plane = o[axis] + (o['w' if axis == 'x' else 'h'] if toward == 1 else 0)
    a0, a1 = centre - width / 2, centre + width / 2
    for rid, edge in ((owner, side), (other, opposite)):
        holes.setdefault(rid, {}).setdefault(edge, []).append((a0, a1, z, z + height))
    openings.append((owner, other, axis, plane, a0, a1, z, z + height, toward, event))
    if event:
        doors[f'membrane_{event}'] = event


# Every ordinary connection takes its centre and width from the plan's links, in plan order.
connections = [
    ('descent', 'west', 'east_ledge', 53), ('west_ledge', 'west', 'molt', 54),
    ('north_ledge', 'north', 'creche', 55), ('west_ledge', 'south', 'rim', 0),
    ('rim', 'north', 'east_ledge', 0), ('east_ledge', 'east', 'vats', 56),
    ('east_ledge', 'north', 'north_ledge', 0), ('north_ledge', 'south', 'west_ledge', 0),
    ('north_ledge', 'north', 'hatchery', 57),
    ('low_west', 'north', 'low_north', 0), ('low_east', 'north', 'low_north', 0),
    ('low_west', 'east', 'low_south', 0), ('low_west', 'west', 'larder', 58),
    ('low_south', 'east', 'low_east', 0), ('ponds', 'east', 'sump', 59),
    ('ponds', 'east', 'spawn', 60), ('sump', 'east', 'cistern', 61),
    ('ponds', 'west', 'barracks', 62), ('royal', 'east', 'throat', 63),
    ('throat', 'north', 'royal_hall', 64), ('throat', 'east', 'mother', 65),
    ('mother', 'north', 'pits', 66), ('mother', 'north', 'pits', 67),
    ('mother', 'east', 'passage', 51), ('passage', 'east', 'shaft', 0)]
links = [link for link in PLAN.links if link['kind'] in ('slide', 'open', 'locked')]
assert len(links) == len(connections)
for (owner, side, other, event), link in zip(connections, links):
    connect(owner, side, other, link['y' if side in ('east', 'west') else 'x'], link['width'], event=event)
connect('royal', 'north', 'barracks', 300, 600, 448, z=-1536)

# The two open air volumes have no floors. Horizontal portals preserve the stacked well's visibility.
R['well1'].update(z=0, ceiling=768)
R['well2'].update(z=-832, ceiling=832)
for rid in ('low_north', 'low_west', 'low_east', 'low_south'):
    R[rid]['ceiling'] = 768
for owner, side, other, centre, width, height, z in (
        ('west_ledge', 'east', 'well1', 2168, 2336, 768, 0),
        ('east_ledge', 'west', 'well1', 2168, 2336, 768, 0),
        ('north_ledge', 'south', 'well1', 3800, 2272, 768, 0),
        ('rim', 'north', 'well1', 3800, 2272, 768, 0),
        ('low_west', 'east', 'well2', 2136, 1072, 768, -768),
        ('low_east', 'west', 'well2', 2136, 1072, 768, -768),
        ('low_north', 'south', 'well2', 3800, 944, 768, -768),
        ('low_south', 'north', 'well2', 3800, 944, 768, -768)):
    connect(owner, side, other, centre, width, height, z)
holes.setdefault('descent', {})['east'] = [(1608, 1992, 0, 400)]

PONDS = [(3064, 1400, 3900, 2000), (4300, 1400, 5200, 2000),
         (3064, 2400, 3900, 2936), (4300, 2400, 5200, 2936)]
PITS = [(x - 300, 3400, x + 300, 4000) for x in (3300, 4300, 5300)]
CUTS = {'vats': [(6800, 2664, 7600, 3864)], 'ponds': PONDS,
        'sump': [(5964, 700, 6600, 1500)],
        'cistern': [(7300 + k * 320, 600, 7420 + k * 320, 1600) for k in range(3)],
        'mother': [(2864, -200, 3464, 400), (5200, -200, 5800, 400)], 'pits': PITS,
        'descent': [(7536, 1000, 7664, 2600)]}


# Cut the outer corners while preserving the well, stacked slabs and every existing doorway.
CHAMFER = {'descent': 180, 'east_ledge': {'se': 180, 'ne': 140},
           'west_ledge': {'sw': 140, 'nw': 140}, 'north_ledge': {'nw': 180, 'ne': 180},
           'rim': {'sw': 160, 'se': 160}, 'molt': 400, 'creche': 180, 'hatchery': 160,
           'vats': {'sw': 140, 'nw': 80}, 'larder': 120, 'ponds': {'sw': 180, 'se': 180, 'nw': 80, 'ne': 180},
           'sump': 120, 'cistern': 120, 'spawn': 140, 'barracks': {'se': 180, 'nw': 180, 'ne': 180},
           'throat': {'se': 160, 'ne': 160}, 'royal_hall': 200,
           'mother': {'sw': 180, 'se': 180, 'nw': 180}}
FOOTPRINTS = {rid: chamfer_rect(r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'], CHAMFER[rid])
              for rid, r in R.items() if rid in CHAMFER}
HIPS = {'molt': 128, 'descent': 96, 'creche': 96, 'hatchery': 64, 'larder': 48,
        'sump': 48, 'cistern': 48, 'spawn': 96, 'barracks': 96, 'throat': 64, 'royal_hall': 96}
# Positions only: stable actor order, groups and the Mother's model sockets are retained.
ACTOR_POSITIONS = {
    29: [6300, 3000, 0], 30: [6500, 2900, 0], 31: [6650, 3760, 0],
    32: [6400, 3760, 0], 33: [6250, 3450, 0],
    45: [4100, 3120, -1536], 46: [4400, 3120, -1536], 47: [3850, 3170, -1536], 48: [3650, 3170, -1536], 49: [3400, 3120, -1536],
    52: [6300, 2600, -1536], 53: [6050, 2630, -1536],
    55: [3200, 1250, -1536], 56: [2920, 1800, -1536], 57: [2900, 2200, -1536],
    58: [4500, 2200, -1536], 59: [4800, 2200, -1536], 60: [5100, 2200, -1536],
    61: [5800, 1000, -1536], 62: [5800, 1350, -1536],
    93: [7520, 1000, -1536], 94: [7840, 1050, -1536], 95: [8180, 1250, -1536],
}


def subtract_floor(rid, cuts, z, role, roof=False):
    r = R[rid]
    for a, c, d, e in rect_minus(r['x'], r['x'] + r['w'], r['y'], r['y'] + r['h'],
                                [(x0, x1, y0, y1) for x0, y0, x1, y1 in cuts]):
        b.rooms[rid] += clip_to((ceiling if roof else floor)(a, d, c, e, z, role), FOOTPRINTS.get(rid))


def wall_role(rid):
    if rid == 'descent':
        return 'sink'
    if rid in ('royal', 'throat', 'passage'):
        return 'root'
    if rid == 'shaft':
        return 'shaft'
    if rid in ('hatchery', 'low_south'):
        return 'egg'
    return 'fold' if R[rid]['z'] < 0 else 'flesh'


for rid, r in R.items():
    x, y, z, w, h, height = (r[k] for k in ('x', 'y', 'z', 'w', 'h', 'ceiling'))
    ambient = r['ambient']
    b.room(rid, (x, y, x + w, y + h, z - 257 if rid in CUTS else z - 1, z + height), ambient)
    if rid in FOOTPRINTS:
        b.footprints[rid] = FOOTPRINTS[rid]
    if rid.startswith('well'):
        if rid == 'well1':
            b.rooms[rid] += ceiling(x, y, x + w, y + h, 768, 'ceil')
        continue
    floor_role = 'bones' if rid in ('descent', 'throat', 'royal_hall', 'mother', 'pits', 'royal') else (
        'wet' if z == -1536 else 'floor')
    if rid != 'royal':
        subtract_floor(rid, CUTS.get(rid, []), z, floor_role)
        if rid in HIPS:
            b.rooms[rid] += hip_ceiling(FOOTPRINTS[rid], z + height - HIPS[rid], z + height, 'ceil')
        elif rid not in ('shaft', 'low_north', 'low_west', 'low_east', 'low_south'):
            subtract_floor(rid, [(3328, 1600, 4272, 2672)] if rid == 'ponds' else [], z + height, 'ceil', True)
    if rid == 'royal':
        continue
    spring = z + height - HIPS.get(rid, 0)
    bands = [(z, z + 192, wall_role(rid)), (z + 192, z + 224, 'glow'),
             (z + 224, spring - 64, wall_role(rid)), (spring - 64, spring, 'fold')]
    if rid in ('descent', 'shaft'):
        bands = [(z, spring - 96, wall_role(rid)), (spring - 96, spring, 'fold')]
    b.rooms[rid] += rect_walls(x, y, x + w, y + h, bands, holes.get(rid), CHAMFER.get(rid))

for owner, other, axis, plane, a0, a1, z0, z1, toward, event in openings:
    b.opening(owner, other, axis, plane, a0, a1, z0, z1, toward=toward,
              floor_role='floor', ceiling_role='fold', side_role='fold')
    if event:
        mid = plane + toward * 32
        lo, hi = ((mid - 8, a0, z0), (mid + 8, a1, z1)) if axis == 'x' else (
            (a0, mid - 8, z0), (a1, mid + 8, z1))
        panels = box(lo, hi, 'door', top='fold')
        # Each membrane is one fitted picture per side, with its thickness left in fold material.
        for i, panel in enumerate(panels):
            if (axis == 'x' and panel[2][0]) or (axis == 'y' and panel[2][1]):
                face_wall = Wall(axis, panel[0][0][0 if axis == 'x' else 1], panel[2])
                panels[i] = (*panel, face_wall.fit(a0, a1, z0, z1))
        b.door(f'membrane_{event}', owner, panels, event, 400, open_speed=400, close_speed=400,
               event=event if event < 66 else 0)

# Horizontal portals join the well to each gallery and the cut nursery roof.
for rid in ('low_north', 'low_west', 'low_east', 'low_south', 'well2'):
    r = R[rid]
    b.portal(rid, 'well1', floor(r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'], 0, 'marker')[0][0])
b.portal('ponds', 'well2', floor(3328, 1600, 4272, 2672, -832, 'marker')[0][0])
b.portal('shaft', 'vats', floor(6800, 2664, 7600, 3864, 0, 'marker')[0][0])

# Close the lower ledge slab between its floor and the nursery roof, facing into the inner well.
for wall, a0, a1 in ((Wall('x', 3328, (1, 0, 0)), 1600, 2672),
                     (Wall('x', 4272, (-1, 0, 0)), 1600, 2672),
                     (Wall('y', 1600, (0, 1, 0)), 3328, 3600),
                     (Wall('y', 1600, (0, 1, 0)), 4000, 4272),
                     (Wall('y', 2672, (0, -1, 0)), 3328, 4272)):
    b.rooms['well2'] += wall.quad(a0, a1, -832, -768, 'fold')

# Resin lips: real prisms, interrupted only at the three stair heads.
for rid, lo, hi in (
        ('west_ledge', (2472, 1000, 0), (2600, 3336, 128)),
        ('east_ledge', (5000, 1000, 0), (5128, 3336, 128)),
        ('north_ledge', (2664, 3400, 0), (4936, 3528, 128)),
        ('low_west', (3216, 1600, -768), (3264, 2672, -640)),
        ('low_east', (4336, 1600, -768), (4384, 2672, -640)),
        ('low_north', (3328, 2736, -768), (4272, 2864, -640))):
    b.rooms[rid] += box(lo, hi, 'vatrim', top='vatrim')
for xa, xb in ((2664, 2764), (3164, 4436), (4836, 4936)):
    b.rooms['rim'] += box((xa, 808, 0), (xb, 936, 128), 'vatrim', top='vatrim')
for xa, xb in ((3328, 3600), (4000, 4272)):
    b.rooms['low_south'] += box((xa, 1408, -768), (xb, 1536, -640), 'vatrim', top='vatrim')

# Twenty-four-unit risers on 44.875-unit treads: the planner never skips a tread. Thin sloped undersides
# preserve the lower ring's passages; continuous root rails close the sheer sides without staircase rail caps.
for rid, x0, y0, x1, y1, z0 in (('low_west', 2764, 1000, 3164, 2436, -768),
                                 ('low_east', 4436, 1000, 4836, 2436, -768),
                                 ('well2', 3600, 1600, 4000, 3036, -1536)):
    b.rooms[rid] += flight_along(((x0+x1)/2, y1), ((x0+x1)/2, y0), x1-x0, z0, 32,
                                  tread='floor', riser='root', rise=24)
    b.rooms[rid].append(([(x0,y0,z0+736),(x1,y0,z0+736),(x1,y1,z0-32),(x0,y1,z0-32)],
                         'root',(0,0,-1)))
    # Segment the sloped walls at each tread so the audit's conservative wall-height boxes leave the underpass open.
    for k in range(32):
        ya,yb=y0+(y1-y0)*k/32,y0+(y1-y0)*(k+1)/32
        low,high=z0+768-24*(k+1)-32,z0+768-24*(k+1)+160
        for xa,xb in ((x0-24,x0),(x1,x1+24)):
            corners=[(xa,yb,low),(xb,yb,low),(xb,ya,low+24),(xa,ya,low+24),
                     (xa,yb,high),(xb,yb,high),(xb,ya,high+24),(xa,ya,high+24)]
            for ids,normal in (((0,1,2,3),(0,0,-1)),((4,5,6,7),(0,0,1)),
                                ((0,3,7,4),(-1,0,0)),((1,2,6,5),(1,0,0))):
                b.rooms[rid].append(([corners[i] for i in ids],'root',normal))
            if k in (0,31):
                ids,normal=((3,2,6,7),(0,-1,0)) if k==0 else ((0,1,5,4),(0,1,0))
                b.rooms[rid].append(([corners[i] for i in ids],'root',normal))
# The Royal Tunnels' ceiling follows the stair continuously, with a flat foot landing.
b.rooms['royal'] += floor(0, -500, 600, 4, -2944, 'bones')
b.rooms['royal'] += ceiling(0, -500, 600, 4, -2496, 'ceil')
b.rooms['royal'] += flight_along((300, 4), (300, 2336), 600, -2944, 88,
                                tread='floor', riser='root', rise=16)
b.rooms['royal'].append(([(0,4,-2496), (600,4,-2496), (600,2336,-1088), (0,2336,-1088)],
                        'ceil', (0,0,-1)))
for side, wall in (('west', Wall('x', 0, (1, 0, 0))), ('east', Wall('x', 600, (-1, 0, 0)))):
    b.rooms['royal'] += banded(wall, -500, 4, [(-2944, -2496, 'root')], holes['royal'].get(side, []))
    b.rooms['royal'] += clip_to(wall.quad(4, 2336, -2944, -1088, 'root'), None,
                              below=((0, 4, -2496), (0, -1408 / 2332, 1)))
b.rooms['royal'] += Wall('y', -500, (0, 1, 0)).quad(0, 600, -2944, -2496, 'root')

# Recessed liquids and birth pits; their floor remains below the causeways, never a painted overlay.
for rid, depth in (('ponds', 32), ('sump', 200), ('cistern', 32), ('mother', 32), ('pits', 256)):
    z = R[rid]['z']
    for k, (x0, y0, x1, y1) in enumerate(CUTS[rid]):
        b.rooms[rid] += box((x0, y0, z - depth), (x1, y1, z), 'fold' if rid == 'pits' else 'crust')
        if rid == 'pits':
            # The west stair starts on a real 160-deep bottom landing, open to the rest of the pit.
            b.rooms[rid] += floor(x0+200,y0,x1,y1,z-depth,'fold')
            b.rooms[rid] += floor(x0,y1-160,x0+200,y1,z-depth,'fold')
            b.rooms[rid] += flight_along((x0+100,y1-160),(x0+100,y0),200,z-depth,16,
                                          tread='fold',riser='fold',rise=16,sides='root',rail=160)
        elif rid == 'sump':
            for a,c,d,e in rect_minus(x0,x1,y0,y1,[(6100,6600,940,1260)]):
                b.surface(f'{rid}_acid_{k}_{a}_{d}',rid,floor(a,d,c,e,z-depth,'acid'),flags=('lava',))
            b.rooms[rid] += ramp(6100,940,6600,1260,z-depth,z,'east',top='wet',skirt='crust',rail=128)
        else:
            b.surface(f'{rid}_acid_{k}', rid, floor(x0, y0, x1, y1, z - depth, 'acid'), flags=('lava',))

# An octagonal pool with the surrounding dry floor cut to its outline.
cx, cy, radius, z = 6200, 3336, 400, -1536
b.rooms['spawn'][:] = [p for p in b.rooms['spawn'] if p[2] != (0, 0, 1)]
subtract_floor('spawn', [(cx - radius, cy - radius, cx + radius, cy + radius)], z, 'wet')
corners = [(cx + radius * math.cos(k * math.pi / 4), cy + radius * math.sin(k * math.pi / 4)) for k in range(8)]
for k in range(8):
    ax, ay = corners[k]
    bx, by = corners[(k + 1) % 8]
    b.rooms['spawn'].append(([(ax, ay, z - 32), (bx, by, z - 32), (bx, by, z), (ax, ay, z)],
                             'crust', (cx - (ax + bx) / 2, cy - (ay + by) / 2, 0)))
    qa = (cx + max(-radius, min(radius, (ax - cx) * 2)), cy + max(-radius, min(radius, (ay - cy) * 2)), z)
    qb = (cx + max(-radius, min(radius, (bx - cx) * 2)), cy + max(-radius, min(radius, (by - cy) * 2)), z)
    b.rooms['spawn'].append(([(ax, ay, z), (bx, by, z), qb, qa], 'wet', (0, 0, 1)))
b.surface('spawn_acid', 'spawn', [([(x, y, z - 32) for x, y in corners], 'acid', (0, 0, 1))], flags=('lava',))

# Egg bays belong to the outer walls; all furniture is map geometry.
for rid, side in (('east_ledge', 'east'), ('north_ledge', 'north'), ('west_ledge', 'west'), ('rim', 'south'),
                  ('low_north', 'north')):
    r = R[rid]
    axis = 'x' if side in ('west', 'east') else 'y'
    plane = r[axis] + (r['w' if axis == 'x' else 'h'] if side in ('east', 'north') else 0)
    n = {'east': (-1, 0, 0), 'west': (1, 0, 0), 'north': (0, -1, 0), 'south': (0, 1, 0)}[side]
    wall = Wall(axis, plane, n)
    start, length = (r['y'], r['h']) if axis == 'x' else (r['x'], r['w'])
    for f in (0.25, 0.75):
        centre, width = start + length * f, min(640, length / 4)
        spans = [(centre - width / 2, centre + width / 2)]
        for a0, a1, _, _ in holes.get(rid, {}).get(side, []):
            spans = [(lo, hi) for left, right in spans
                     for lo, hi in ((left, min(right, a0 - 32)), (max(left, a1 + 32), right)) if hi - lo >= 64]
        for lo, hi in spans:
            assert all(hi <= a0 - 32 or lo >= a1 + 32 for a0, a1, _, _ in holes.get(rid, {}).get(side, []))
            b.rooms[rid] += plaque(wall, (lo + hi) / 2, r['z'] + 96, hi - lo, 384, 'egg', out=24)
for k in range(4):
    x, y = R['creche']['x'] + 250 + (k % 2) * 1000, R['creche']['y'] + 100 + (k // 2) * 600
    b.rooms['creche'] += box((x, y, 0), (x + 400, y + 400, 200), 'vatrim', top='floor')
for k in range(6):
    x, y = -600 + (k % 3) * 800, 1200 + (k // 3) * 1100
    b.rooms['molt'] += kit.pipe((x, y, 100), (x + 300, y, 100), 100, 'bones')
for rid in ('larder', 'barracks'):
    r = R[rid]
    for k in range(2 if rid == 'larder' else 3):
        x = r['x'] + (k + 0.5) * r['w'] / (2 if rid == 'larder' else 3)
        b.rooms[rid] += plaque(Wall('y', r['y'] + r['h'], (0, -1, 0)), x, r['z'],
                                400 if rid == 'larder' else 700, 320, 'bones' if rid == 'larder' else 'fold', out=200)

# Six bone-litter stand-ins, two small heaps against each room's side wall.
for rid in ('larder', 'creche', 'throat'):
    r = R[rid]
    for fraction in (0.25, 0.75):
        x, y, z = r['x'] + 80, r['y'] + r['h'] * fraction, r['z']
        for k in range(3):
            b.rooms[rid] += kit.beam((x, y + k * 24, z + 8), (x + 100, y + 40 - k * 20, z + 16),
                                    16, 'bones')

vat_marks = [m for m in PLAN.marks if m['kind'] == 'interact' and m['label'].startswith('Vat sac')]
for k, m in enumerate(vat_marks):
    x, y = m['x'], m['y']
    b.rooms['vats'] += prism(x, y, 250, 0, 128, 'vatrim', top='floor')
    # The design's 900-high sacs exceed this room's 640 ceiling; keep the sac beneath its ceiling ribs.
    b.trigger(f'vat_{k + 1}', 'vats', prism(x, y, 225, 128, 600, 'gland', top='gland', bottom='gland'),
              70 + k, cog=170 + k)
    for dx in (-180, 180):
        b.rooms['vats'] += prism(x + dx, y, 24, 128, 640, 'root', sides=6)

b.rooms['mother'] += plaque(Wall('y', 3000, (0, -1, 0)), 4300, -2912, 1024, 1024, 'mother', out=16)
for x in (3750, 4850):
    b.rooms['mother'] += kit.beam((x, 2900, -2944), (4300 + (x - 4300) * .75, 2760, -2000), 80, 'bones')

# Native support under the three cradle sockets, inside the Mother's existing body/cradle silhouette.
for x,y,top in ((3990,2300,-2654),(4320,2570,-2724),(4320,2010,-2724)):
    b.rooms['mother'] += prism(x,y,90,-2944,top,'root',top='fold',sides=8)

# The lift travels inside its clear column; two lips leave a 600-square landing opening.
platform = box((6900, 2964, -2976), (7500, 3564, -2944), 'vatrim', top='floor', bottom='fold')
b.door('egg_lift', 'shaft', platform, 52, 2944, open_speed=294.4, close_speed=294.4, event=73)
doors['egg_lift'] = 52
for lo, hi in (((6800, 2664, 0), (6824, 2964, 128)), ((6800, 3564, 0), (6824, 3864, 128)),
               ((6800, 3840, 0), (7600, 3864, 128))):
    b.rooms['vats'] += box(lo, hi, 'vatrim', top='vatrim')
# Plate controls are mounted on the shaft's west wall at the plan's y, reachable from each landing.
for event, rid, z in ((73, 'shaft', -2944), (74, 'vats', 0)):
    b.trigger(f'lift_plate_{event}', rid, plaque(Wall('x', 6800, (1 if event == 73 else -1, 0, 0)),
                                               3500, z + 96, 96, 96, 'glow', out=12), event)

exit_face, jambs = kit.recessed_door(Wall('x', 8400, (-1, 0, 0)), 1800, 0, 384, 400, 'door', trim='fold')
b.rooms['descent'] += jambs
b.trigger('membrane_mouth', 'descent', exit_face, 50)
b.trigger('null_field', 'descent', floor(7536, 1000, 7664, 2600, 0, 'bones'), 11, kind='pressure_plate')
note = next(m for m in PLAN.marks if m['kind'] == 'interact' and m['label'].startswith('The scouts'))
b.trigger('scouts_note', 'descent', box((note['x'] - 32, note['y'] - 20, 0),
                                      (note['x'] + 32, note['y'] + 20, 100), 'bones', top='bones'), 10)
chests = [m for m in PLAN.marks if m['kind'].startswith('chest_')]
for k, m in enumerate(chests):
    z = PLAN.floors[m['floor']]
    b.decoration('hes_ashrunner_crate' if k == 3 else 'hes_kreegan_pod_chest', m['x'], m['y'], z,
                  event=30 + k, cog=300 + k)

# Missing glow-sac models: a small amber sac prism on the specified wall, with the plan light unchanged.
for light in PLAN.lights:
    x, y, z = light['x'], light['y'], light['z']
    group = 3 if light['id'] == 'L11' else light['group']
    b.light(light['id'], x, y, z, light['radius'], light['colour'], group)
    if light['fixture']:
        rid = 'royal' if light['id'] in ('F11', 'F12') else b.room_at(x, y, z)
        facing = math.radians(light['facing'])
        b.rooms[rid] += prism(x + math.cos(facing) * 20, y + math.sin(facing) * 20, 20,
                              z - 25, z + 25, 'egg', top='egg', bottom='fold')

# Every interactive object and light stays inside the reshaped rooms; openings retain their original edges.
for rid, footprint in FOOTPRINTS.items():
    for side, hs in holes.get(rid,{}).items():
        for a0,a1,_,_ in hs:
            r=R[rid]
            for along in (a0,a1):
                x,y = ((r['x'] if side=='west' else r['x']+r['w']),along) if side in ('west','east') else \
                      (along,(r['y'] if side=='south' else r['y']+r['h']))
                if r['x']<=x<=r['x']+r['w'] and r['y']<=y<=r['y']+r['h']:
                    assert kit._inside(footprint,x,y), (rid,side,along)
    for light in PLAN.lights:
        r=R[rid]
        if r['x']<=light['x']<=r['x']+r['w'] and r['y']<=light['y']<=r['y']+r['h'] and r['z']<=light['z']<r['z']+r['ceiling']:
            assert kit._inside(footprint,light['x'],light['y']), (rid,light['id'])

# Recessed doors may extend into their wall reveals; every point inside the room rectangle must clear its cut.
for name, rid, panels, *_ in b.triggers:
    if rid not in FOOTPRINTS:
        continue
    r = R[rid]
    for panel in panels:
        for x, y, _ in panel[0]:
            if r['x'] <= x <= r['x'] + r['w'] and r['y'] <= y <= r['y'] + r['h']:
                assert kit._inside(FOOTPRINTS[rid], x, y), (name, x, y)
for name, x, y, z, *_ in b.decorations:
    assert b.room_at(x, y, z + 1), (name, x, y, z)

# Split authored room faces at the design's sector boundaries, including portals through the same cuts.
SPLITS = {'descent': ([7200], []), 'east_ledge': ([], [2200]), 'west_ledge': ([], [2200]),
          'north_ledge': ([3800], []), 'vats': ([], [3500]), 'molt': ([300], []),
          'ponds': ([4100], [2200]), 'barracks': ([1300], []), 'mother': ([4332], [1300]),
          'pits': ([4300], [])}


def clip(points, axis, value, sign):
    result = []
    for a, c in zip(points, points[1:] + points[:1]):
        av, cv = sign * (a[axis] - value), sign * (c[axis] - value)
        if av >= -0.001:
            result.append(tuple(a))
        if (av < -0.001 and cv > 0.001) or (av > 0.001 and cv < -0.001):
            f = (value - a[axis]) / (c[axis] - a[axis])
            result.append(tuple(a[i] + f * (c[i] - a[i]) for i in range(3)))
    return result


def clipped(points, bounds, rid):
    points = [tuple(p) for p in points]
    r = R[rid]
    # Reveals extend beyond room bounds: clip faces and portals only at internal sector splits.
    for axis, value, sign, edge in ((0, bounds[0], 1, r['x']), (0, bounds[2], -1, r['x'] + r['w']),
                                    (1, bounds[1], 1, r['y']), (1, bounds[3], -1, r['y'] + r['h'])):
        if value != edge:
            points = clip(points, axis, value, sign)
    if len(points) < 3:
        return []
    from mathutils import Vector
    area = sum((Vector(points[k]) - Vector(points[0])).cross(Vector(points[k + 1]) - Vector(points[0])).length
               for k in range(1, len(points) - 1))
    return points if area > 0.01 else []


parts = {}
for rid, (xcuts, ycuts) in SPLITS.items():
    panels, bounds, ambient = b.rooms.pop(rid), b.bounds.pop(rid), b.ambient.pop(rid)
    footprint = b.footprints.pop(rid, None)
    xs, ys = [bounds[0], *xcuts, bounds[2]], [bounds[1], *ycuts, bounds[3]]
    parts[rid] = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            name = f'{rid}_{i}_{j}'
            bound = (xs[i], ys[j], xs[i + 1], ys[j + 1], bounds[4], bounds[5])
            b.room(name, bound, ambient)
            if footprint:
                b.footprints[name] = [(p[0],p[1]) for p in clipped([(x,y,0) for x,y in footprint],bound,rid)]
            parts[rid].append(name)
            for panel in panels:
                points = clipped(panel[0], bound, rid)
                if points:
                    b.rooms[name].append((points, *panel[1:]))
            if i:
                b.portal(f'{rid}_{i - 1}_{j}', name,
                         [(xs[i], ys[j], bounds[4] + 1), (xs[i], ys[j + 1], bounds[4] + 1),
                          (xs[i], ys[j + 1], bounds[5]), (xs[i], ys[j], bounds[5])])
            if j:
                b.portal(f'{rid}_{i}_{j - 1}', name,
                         [(xs[i], ys[j], bounds[4] + 1), (xs[i + 1], ys[j], bounds[4] + 1),
                          (xs[i + 1], ys[j], bounds[5]), (xs[i], ys[j], bounds[5])])


def owner(rid, panels):
    if rid not in parts:
        return rid
    points = [p for panel in panels for p in panel[0]]
    x, y = (sum(p[i] for p in points) / len(points) for i in (0, 1))
    return min(parts[rid], key=lambda name: abs((b.bounds[name][0] + b.bounds[name][2]) / 2 - x)
               + abs((b.bounds[name][1] + b.bounds[name][3]) / 2 - y))


b.triggers = [(name, owner(rid, panels), panels, *tail) for name, rid, panels, *tail in b.triggers]
b.mechanisms = [(name, owner(rid, panels), panels, *tail) for name, rid, panels, *tail in b.mechanisms]
portals = b.portals
b.portals = []
for front, back, points in portals:
    for f in parts.get(front, [front]):
        for t in parts.get(back, [back]):
            p = points
            for original, part in ((front, f), (back, t)):
                if original in parts:
                    p = clipped(p, b.bounds[part], original)
            if p:
                b.portal(f, t, p)

start = next(m for m in PLAN.marks if m['kind'] == 'start')
# PICKUPS.md: wall-side supplies; event order is persistent pickup identity.
PICKUP_VATS = [
    ('barracks', 1600, 2540, -1536),
    ('barracks', 1800, 2540, -1536),
    ('barracks', 2000, 2540, -1536),
    ('barracks', 2200, 2540, -1536),
    ('larder', 2420, 850, -768),
    ('larder', 2420, 1050, -768),
    ('north_ledge', 4480, 4250, 0),
    ('north_ledge', 4700, 4250, 0),
]
PICKUP_BUNDLES = [
    ('descent', 8110, 1200, 0),
    ('descent', 6250, 2400, 0),
    ('east_ledge', 5810, 1200, 0),
    ('north_ledge', 5700, 4210, 0),
    ('west_ledge', 1770, 3000, 0),
    ('molt', -700, 1500, 0),
    ('molt', 1300, 1500, 0),
    ('hatchery', 2380, 5200, 0),
    ('creche', 5510, 5400, 0),
    ('creche', 3800, 5050, 0),
    ('larder', 1850, 1420, -768),
    ('low_north', 4750, 3190, -768),
    ('low_west', 2800, 2550, -768),
    ('low_east', 4800, 2550, -768),
    ('sump', 5850, 580, -1536),
    ('cistern', 8200, 580, -1536),
    ('barracks', 1100, 2590, -1536),
    ('throat', 2380, 500, -2944),
    ('royal_hall', 900, 2080, -2944),
    ('royal_hall', 2390, 950, -2944),
]
assert (len(PICKUP_VATS), len(PICKUP_BUNDLES)) == (8, 20)
pickups = []
for model, first, positions in (("hes_serum_vat", 701, PICKUP_VATS),
                                 ("hes_scrap_bundle", 751, PICKUP_BUNDLES)):
    for event, (room, x, y, z) in enumerate(positions, first):
        if room in FOOTPRINTS:
            assert all(kit._inside(FOOTPRINTS[room],x+dx,y+dy) for dx,dy in ((-60,-60),(-60,60),(60,-60),(60,60))), event
        b.decoration(model, x, y, z, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x, y, z]))

b.export({'actor_positions': ACTOR_POSITIONS, 'footprints': FOOTPRINTS, 'pickups': pickups, 'arrivals': {'from_hes_out3': {'position': [start['x'], start['y'], 0], 'direction_degrees': 180}},
          'door_ids': doors, 'chest_events': {30 + k: k for k in range(8)},
          'monster_packs': [m for m in PLAN.marks if m['kind'] in ('monster', 'boss')],
          'room_bounds': b.bounds, 'plan_budget': zone.plans.budget(PLAN)})

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
