"""D3 Quarry Outpost: the zone-2 plan, authored with the shared Hesper BLV kit.

Run from this directory: blender --background --factory-startup --python author_d03_blender.py
"""
import importlib.util
import os
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit
from blv_kit import (Wall, banded, beam, box, ceiling, clip_half, clip_to, flight, floor, hip_ceiling, plaque, prism,
                     rect_minus)

spec = importlib.util.spec_from_file_location('zone2', ROOT / 'design/kreegan_world/zone2/dungeons/plans_zone2.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d3
R = {r['id']: dict(r) for r in PLAN.rooms}
for shaft, bottom, top in (('liftop', 'liftbot', 'liftop'), ('chute', 'chute', 'chutetop')):
    R[shaft] = dict(R[shaft], z=-1536, ceiling=1152)
del R['liftbot'], R['chutetop']

blv_kit.FOLDERS += [blv_kit.ART / 'textures_k5_grafted/masters', blv_kit.ART / 'textures_k6_foundry/masters']
KEYS = ('hoaresin hochitin hobone hkrock hkvein hkfloor hkore hkceil hkrib hktrim hkskylat hmcrate hmchan '
        'hkblast hkdoor hkgraft hkgraft2 hkgrlite hkpylon hkpylonx hkconsol hkconsok hkglyph hkloom hkloomx hkcage')
ROLE = {k: k for k in KEYS.split()}
ROLE.update(marker='hkconsol', trim='hkrib', floor='hkfloor')
b = blv_kit.Builder('hes_d03.blv', ROLE, PROJECT / 'source')
holes, openings, doors = {}, [], {}


def link(label):
    return next(l for l in PLAN.links if label in l['label'])


def mark(label):
    return next(m for m in PLAN.marks if label in m['label'])


def connect(owner, side, other, label, z, height=384, door=0, plate=0):
    l = link(label)
    o, t = R[owner], R[other]
    axis = 'x' if side in ('west', 'east') else 'y'
    toward = -1 if side in ('west', 'south') else 1
    plane = o[axis] + (o['w' if axis == 'x' else 'h'] if toward == 1 else 0)
    centre = l['y' if axis == 'x' else 'x']
    a0, a1 = centre - l['width'] / 2, centre + l['width'] / 2
    opposite = {'west': 'east', 'east': 'west', 'south': 'north', 'north': 'south'}[side]
    for rid, wall in ((owner, side), (other, opposite)):
        holes.setdefault(rid, {}).setdefault(wall, []).append((a0, a1, z - R[rid]['z'], z + height - R[rid]['z']))
    openings.append((owner, other, axis, plane, a0, a1, z, z + height, toward, plate))
    if door:
        doors[door] = openings[-1]


connect('gatehouse', 'west', 'gallery', 'inner gate', 0, door=51)
connect('gallery', 'south', 'estair', "East Stair's top", 0)
connect('yard', 'east', 'estair', "East Stair's foot", -768, plate=80)
connect('yard', 'north', 'barracks', 'Barracks door', -768, door=52, plate=80)
connect('yard', 'north', 'mess', 'Mess Hall door', -768, door=53, plate=80)
connect('yard', 'south', 'podbay', "Pod Bay's mouth", -768, plate=80)
connect('yard', 'south', 'liftop', "Ore Lift's gate", -768, plate=80)
connect('yard', 'west', 'rstair', "Roost Stair's mouth", -768, plate=80)
connect('rstair', 'north', 'roost', "Roost Stair's top", 0, plate=150)
connect('rstair', 'south', 'chute', "Ore Chute's gate", -768)
connect('roost', 'north', 'signal', 'Signal Room:', 0, door=54)
connect('liftop', 'south', 'storage', "Ore Lift's foot", -1536)
connect('storage', 'west', 'crusher', 'Lower Storage to', -1536)
connect('crusher', 'north', 'chute', "Ore Chute's foot", -1536)
connect('storage', 'east', 'lab', 'Emitter Lab:', -1536, door=55)
connect('crusher', 'south', 'quarry', 'Crusher Hall to', -1536)
connect('quarry', 'east', 'niche', 'cracked face:', -1536, door=58)

# Two open parapets share the Yard's airspace, with the same 64-unit reveals as the doors.
for owner, side, a0, a1, top in (('gallery', 'west', 1964, 3264, 576),
                                ('roost', 'east', 2264, 3600, 1024)):
    plane, toward = (5464, -1) if side == 'west' else (2136, 1)
    holes.setdefault(owner, {}).setdefault(side, []).append((a0, a1, 112, top))
    other_side = 'east' if side == 'west' else 'west'
    holes.setdefault('yard', {}).setdefault(other_side, []).append((a0, a1, 880, top + 768))
    openings.append((owner, 'yard', 'x', plane, a0, a1, 112, top, toward, 0))

exit_link = link('Outer Gate:')
holes.setdefault('gatehouse', {})['east'] = [(exit_link['y'] - 256, exit_link['y'] + 256, 0, 384)]
WALLS = {'gatehouse': 'hoaresin', 'gallery': 'hoaresin', 'roost': 'hkvein', 'signal': 'hoaresin',
         'barracks': 'hkvein', 'mess': 'hkvein', 'podbay': 'hoaresin', 'lab': 'hoaresin'}
AMBIENT = {'yard': 10, 'gatehouse': 12, 'gallery': 15, 'roost': 12, 'signal': 12, 'storage': 12,
           'lab': 12, 'crusher': 12, 'quarry': 12, 'niche': 20,
           'estair': 15, 'rstair': 15, 'liftop': 15, 'chute': 15}
# Room shapes (DUNGEON_PLAYBOOK, 2026-10-24): chamfered corners clear of every door, panel, light, chest and pickup;
# hipped ceilings springing below the plan's ceiling; sloped ceilings over the two stairs; a cave-in pocket.
CHAMFER = {'crusher': {'sw': 300, 'nw': 250, 'ne': 450, 'se': 450}, 'quarry': {'sw': 400, 'se': 400, 'nw': 200, 'ne': 300},
           'gatehouse': {'ne': 300, 'se': 300}, 'lab': {'sw': 250, 'nw': 250, 'ne': 250, 'se': 100},
           'mess': {'nw': 250, 'ne': 250, 'se': 120}, 'signal': {'sw': 150, 'se': 250, 'ne': 250, 'nw': 250}}
HIPS = {'crusher': 128, 'gatehouse': 128}        # the hip's rise; the walls stop that far below the plan's ceiling
STAIR_SLOPES = {'estair': ((6616, 0, 384), (-0.4, 0, 1)), 'rstair': ((536, 0, 384), (0.4, 0, 1))}
NICHE = [(4264, -3000), (4500, -3100), (4850, -3020), (4964, -2850), (4964, -2650), (4880, -2480), (4560, -2400),
         (4264, -2500)]        # a flat east face for its graft light
for rid, r in R.items():
    wall = WALLS.get(rid, 'hkrock')
    height = r['ceiling'] - HIPS.get(rid, 0)
    bands = [(0, 64, 'hktrim'), (64, height - 64, wall), (height - 64, height, 'hkrib')]
    if rid == 'yard':
        bands = [(0, 64, 'hktrim'), (64, 736, 'hkrock'), (736, 800, 'hktrim'),
                 (800, 1728, 'hoaresin'), (1728, 1792, 'hkrib')]
    floor_role = 'hkfloor' if rid in WALLS else 'hkore'
    if rid in ('estair', 'rstair', 'liftop', 'chute'):
        floor_role = 'hochitin'
    x0, y0, x1, y1, z = r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'], r['z']
    if rid == 'niche':
        # The west edge (from its last point south to its first) holds the cracked face's opening.
        cut = [(-2500 - h[1], -2500 - h[0], h[2], h[3]) for h in holes[rid]['west']]
        b.poly_room(rid, NICHE, z, height, bands, {len(NICHE) - 1: cut}, floor_role=floor_role,
                    ceiling_role='hkceil', ambient=AMBIENT.get(rid, 12))
        continue
    b.box_room(rid, x0, y0, x1, y1, z, height, bands, holes.get(rid), floor_role=floor_role,
               ceiling_role=None if rid in HIPS else 'hkskylat' if rid == 'yard' else 'hkceil',
               ambient=AMBIENT.get(rid, 12), chamfer=CHAMFER.get(rid))
    if rid in HIPS:
        footprint = b.footprints.get(rid) or [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        b.rooms[rid] += hip_ceiling(footprint, z + height, z + r['ceiling'], 'hkceil', top=0.5)
        b.bounds[rid] = (x0, y0, x1, y1, z - 1, z + r['ceiling'])
    if rid in STAIR_SLOPES:
        # The flat ceiling stays only over the top landing, where the slope would rise above it.
        (qx, qy, qz), (nx, ny, nz) = point, normal = STAIR_SLOPES[rid]
        panels = b.rooms[rid]
        top = z + r['ceiling']
        slope = [(px, py, qz - nx * (px - qx) - ny * (py - qy)) for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        flat = clip_half(panels[1], point, normal)
        b.rooms[rid] = panels[:1] + ([flat] if flat else []) + \
            clip_to([(slope, 'hkceil', (0, 0, -1))], None, below=((0, 0, top), (0, 0, 1))) + \
            clip_to(panels[2:], None, below=STAIR_SLOPES[rid])


def remove_floor(rid):
    assert b.rooms[rid][0][2] == (0, 0, 1)
    b.rooms[rid].pop(0)


for owner, other, axis, plane, a0, a1, z0, z1, toward, plate in openings:
    before = len(b.rooms[owner])
    b.opening(owner, other, axis, plane, a0, a1, z0, z1, toward=toward,
              floor_role='hochitin', ceiling_role='hkrib', side_role='hkrib')
    if plate:
        panel = b.rooms[owner].pop(before)
        b.trigger(f'mouth_{owner}_{other}', owner, [panel], plate, kind='pressure_plate')
for door, (owner, _, axis, plane, a0, a1, z0, z1, toward, _) in doors.items():
    mid = plane + toward * 32
    lo, hi = ((mid - 8, a0, z0), (mid + 8, a1, z1)) if axis == 'x' else (
        (a0, mid - 8, z0), (a1, mid + 8, z1))
    role = 'hkrock' if door == 58 else 'hkdoor'
    panels = box(lo, hi, role, top='hkrib')
    # The membrane's seam is one fitted image on each side of its leaf.
    fitted = []
    for coords, key, normal in panels:
        if key == role:
            wall = Wall('x' if normal[0] else 'y', coords[0][0 if normal[0] else 1], normal)
            along = [p[1 if normal[0] else 0] for p in coords]
            fitted.append((coords, key, normal, wall.fit(min(along), max(along), z0, z1)))
        else:
            fitted.append((coords, key, normal))
    speed = 192 if door == 58 else (256 if door in (54, 55) else 384)
    b.door(f'door_{door}', owner, fitted, door, 384, direction=(0, 0, -1 if door == 58 else 1),
           open_speed=speed, close_speed=speed, event=door, flags=('secret',) if door == 58 else ())

# Gate, grafted panels and the console's solid housing.
face, jambs = blv_kit.recessed_door(Wall('x', 8328, (-1, 0, 0)), exit_link['y'], 0, 512, 384, 'hkblast')
b.rooms['gatehouse'] += jambs
b.trigger('outer_gate', 'gatehouse', face, 50)
for y, normal in ((1964, (0, 1, 0)), (3264, (0, -1, 0))):
    b.rooms['gatehouse'] += plaque(Wall('y', y, normal), 7300, 160, 128, 256, 'hkgraft', edge='hkrib')


def panel(name, rid, wall, along, z, width, height, role, event, cog=0, depth=24):
    parts = plaque(wall, along, z, width, height, role, out=depth, edge='hkrib')
    b.rooms[rid] += parts[1:]
    b.trigger(name, rid, parts[:1], event, cog=cog)


panel('gate_console', 'gatehouse', Wall('y', 3264, (0, -1, 0)), mark('Gate turret')['x'],
      0, 300, 140, 'hkconsol', 71, 71, 120)
panel('watch_glyph', 'gallery', Wall('y', 3264, (0, -1, 0)), R['gallery']['x'] + 350,
      96, 128, 256, 'hkglyph', 10)

# The Yard's pressure plates replace its floor; cover includes P2's north foot and every opening's reveal.
remove_floor('yard')
xs = [2200, 3700, 4150, 5400]
ys = [1000, 1600, 2400, 2550, 3600]
for x0, x1 in zip(xs, xs[1:]):
    for y0, y1 in zip(ys, ys[1:]):
        exposed = y0 >= 1600 and y1 <= 2550 and not (x0 == 3700 and y0 == 2400)
        b.trigger(f'yard_floor_{x0}_{y0}', 'yard', floor(x0, y0, x1, y1, -768, 'hkore'),
                  77 if exposed else 80, kind='pressure_plate')
for k, extra in enumerate(zone.AUTOMAP_EXTRAS[PLAN.key]):
    points = extra['points']
    x0, y0 = points[0]
    x1, y1 = points[2]
    role = 'hochitin' if k == 4 else ('hkore' if k in (0, 3) else 'hmcrate')
    panels = box((x0, y0, -768), (x1, y1, extra['z']), 'hkrock' if role == 'hkore' else role, top=role)
    if role == 'hkore':
        from mathutils import Vector
        tapered = []
        for coords, key, normal in panels:
            coords = [(x + (48 if x == x0 else -48), y + (48 if y == y0 else -48), z)
                      if z == extra['z'] else (x, y, z) for x, y, z in coords]
            n = (Vector(coords[1]) - Vector(coords[0])).cross(Vector(coords[2]) - Vector(coords[0])).normalized()
            tapered.append((coords, key, tuple(n if n.dot(Vector(normal)) > 0 else -n)))
        panels = tapered
    b.rooms['yard'] += panels[:-1]
    b.trigger(f'cover_top_{k}', 'yard', panels[-1:], 80, kind='pressure_plate')
panels = box((3950, 2450, -768), (4150, 2650, -576), 'hmcrate', top='hmcrate')
b.rooms['yard'] += panels[:-1]
b.trigger('pylon_cover_top', 'yard', panels[-1:], 80, kind='pressure_plate')
pylon = mark('Pylon P2')
px, py = pylon['x'], pylon['y'] - 100
for coords, role, normal in box((px - 100, py - 100, -640), (px + 100, py + 100, 560), 'hkpylon', top='hkrib'):
    if role == 'hkpylon':
        wall = Wall('x' if normal[0] else 'y', coords[0][0 if normal[0] else 1], normal)
        along = [p[1 if normal[0] else 0] for p in coords]
        parts = [(coords, role, normal, wall.fit(min(along), max(along), -640, 560))]
        b.trigger(f'pylon_{normal}', 'yard', parts, 70 if normal == (0, 1, 0) else 0, cog=70)
    else:
        b.rooms['yard'].append((coords, role, normal))
for k in range(8):
    x = R['yard']['x'] + 200 + 400 * k
    b.rooms['yard'] += beam((x, 1000, 944), (x, 3600, 944), 160, 'hoaresin')

# Both flights have exactly 24 treads; the rest of each stair room is its landing.
for rid, x0, x1, direction in (('estair', 5464, 6616, 'east'), ('rstair', 536, 1688, 'west')):
    r = R[rid]
    remove_floor(rid)
    b.rooms[rid] += flight(x0, r['y'], x1, r['y'] + r['h'], -768, 24, direction,
                           tread='hochitin', riser='hkrib')
    if direction == 'east':
        b.rooms[rid] += floor(x1, r['y'], r['x'] + r['w'], r['y'] + r['h'], 0, 'hochitin')
    else:
        b.rooms[rid] += floor(r['x'], r['y'], x0, r['y'] + r['h'], 0, 'hochitin')
        b.trigger('roost_foot_landing', rid, floor(x1, r['y'], r['x'] + r['w'], r['y'] + r['h'], -768,
                                                 'hochitin'), 80, kind='pressure_plate')
panel('cache', 'rstair', Wall('x', 88, (1, 0, 0)), mark('Consumable cache')['y'], 64, 280, 96,
      'hkrib', 36, depth=112)

# Linear lift platforms and controls. The chute uses the plan's 500-wide shaft (see README's design discrepancy).
for rid, door in (('liftop', 56), ('chute', 57)):
    r = R[rid]
    remove_floor(rid)
    b.rooms[rid] += floor(r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'], -1568, 'hkrock')
    z = -768 if door == 56 else -1536
    platform = box((r['x'], r['y'], z - 24), (r['x'] + r['w'], r['y'] + r['h'], z),
                   'hkrib', top='hochitin', bottom='hkrib')
    b.door(f'lift_{door}', rid, platform, door, 768, direction=(0, 0, -1 if door == 56 else 1),
           open_speed=192, close_speed=192)
for label, event, rid, z in (('Ore Lift controls (top)', 74, 'liftop', -768),
                            ('Ore Lift controls (bottom)', 75, 'liftop', -1536),
                            ('Ore Chute controls', 78, 'chute', -1536)):
    m = mark(label)
    x, y = m['x'], m['y']
    wall_x = R[rid]['x'] if event != 75 else R[rid]['x'] + R[rid]['w']
    inward = (1, 0, 0) if event != 75 else (-1, 0, 0)
    panel(f'control_{event}', rid, Wall('x', wall_x, inward), y, z + 96, 120, 128, 'hkconsol', event)
panel('chute_top_control', 'rstair', Wall('y', 1000, (0, 1, 0)), 2090, -672, 80, 128, 'hkconsol', 79)

# Living rooms: eight two-tier shelves, trestles, and pod racks.
r = R['barracks']
for x in (r['x'] + 400, r['x'] + 1100):
    for y in (r['y'] + 60, r['y'] + r['h'] - 320):
        for height in (160, 480):
            b.rooms['barracks'] += box((x - 300, y, -768 + height - 32),
                                       (x + 300, y + 260, -768 + height), 'hkrib', top='hochitin', bottom='hkrib')
panel('barracks_glyph', 'barracks', Wall('y', 3664, (0, 1, 0)), mark('barracks caste')['x'],
      -672, 128, 256, 'hkglyph', 11)
f = next(l for l in PLAN.lights if l['id'] == 'F_mess')
for y in (f['y'] - 350, f['y'] + 350):
    b.rooms['mess'] += box((f['x'] - 450, y - 100, -768), (f['x'] + 450, y + 100, -672), 'hobone', top='hobone')
for wave, label in enumerate(('wave 1:', 'wave 2:')):
    m = mark(label)
    b.rooms['podbay'] += box((m['x'] - 320, 236, -768), (m['x'] + 320, 436, -640), 'hkrib', top='hkrib')
    for k in range(4):
        b.decoration('hes_drop_pod', m['x'] - 240 + k * 160, 336, -640, 0, cog=140 + wave)

# Krav's perch, three cage fronts, and the loom.
boss = mark('Overseer Krav')
bx, by = boss['x'], boss['y']
b.rooms['roost'] += box((bx - 150, by - 150, 0), (bx + 150, by + 150, 416), 'hoaresin', top='hochitin')
b.rooms['roost'] += box((bx - 300, by - 300, 416), (bx + 300, by + 300, 448), 'hkrib', top='hochitin', bottom='hkrib')
pens = []
for k in range(3):
    y = 2700 + k * 600
    pens.append((150, y))
    panel(f'pen_{k}', 'roost', Wall('x', 0, (1, 0, 0)), y, 0, 560, 384, 'hkcage', 0, 132 + k, 300)
panel('roost_glyph', 'roost', Wall('x', 2136, (-1, 0, 0)), mark("Overseer's sigil")['y'],
      96, 128, 256, 'hkglyph', 12)
panel('loom', 'signal', Wall('y', 5428, (0, -1, 0)), mark('signal loom')['x'], 64, 128, 256, 'hkloom', 76, 76)

# The stores, the crusher's recognizable housing/hopper/straps, and a cut-out hot throat.
r = R['storage']
# Three ore bins the Drudges fill (they were three plain blocks): crate-sided hoppers on a rib frame, heaped with ore.
for x in (4200, 4900, 5600):
    b.rooms['storage'] += box((x - 250, -1450, -1536), (x + 250, -1050, -1344), 'hmcrate')
    b.rooms['storage'] += box((x - 266, -1466, -1344), (x + 266, -1034, -1312), 'hkrib', top='hkrib', bottom='hkrib')
    heap = hip_ceiling([(x - 230, -1430), (x + 230, -1430), (x + 230, -1070), (x - 230, -1070)], -1312, -1216,
                       'hkore', top=0.3)
    b.rooms['storage'] += [(coords, role, tuple(-v for v in facing)) for coords, role, facing in heap]
    for px in (x - 250, x + 234):
        b.rooms['storage'] += box((px, -1450, -1536), (px + 16, -1050, -1344), 'hkrib', top='hkrib')
panel('foreman_console', 'storage', Wall('x', 6200, (-1, 0, 0)), mark('Foreman')['y'], -1440,
      128, 160, 'hkconsol', 73, 73)
hot = mark("crusher's throat")
hx, hy = hot['x'], hot['y']
b.rooms['crusher'] += box((hx - 450, hy + 200, -1536), (hx + 450, hy + 800, -1024), 'hkgraft2', top='hkrib')
b.rooms['crusher'] += box((hx - 300, hy + 300, -1024), (hx + 300, hy + 700, -864), 'hkrib', top='hkore')
for x in (hx - 350, hx + 350):
    b.rooms['crusher'] += beam((x, hy + 190, -1536), (x, hy + 190, -1024), 48, 'hoaresin')
remove_floor('crusher')
r = R['crusher']
for x0, x1, y0, y1 in rect_minus(r['x'], r['x'] + r['w'], r['y'], r['y'] + r['h'],
                                [(hx - 300, hx + 300, hy - 150, hy + 150)]):
    b.rooms['crusher'] += clip_to(floor(x0, y0, x1, y1, -1536, 'hkore'), b.footprints['crusher'])
# One 32 step down: the Drudges feeding the crusher stepped into a 64-deep throat and never climbed out.
b.surface('crusher_throat', 'crusher', floor(hx - 300, hy - 150, hx + 300, hy + 150, -1568, 'hmchan'),
          flags=('lava',))
for wall, a0, a1 in ((Wall('x', hx - 300, (1, 0, 0)), hy - 150, hy + 150),
                     (Wall('x', hx + 300, (-1, 0, 0)), hy - 150, hy + 150),
                     (Wall('y', hy - 150, (0, 1, 0)), hx - 300, hx + 300),
                     (Wall('y', hy + 150, (0, -1, 0)), hx - 300, hx + 300)):
    b.rooms['crusher'] += wall.quad(a0, a1, -1568, -1536, 'hkrib')

for x in (R['lab']['x'] + 450, R['lab']['x'] + 1150):
    b.rooms['lab'] += box((x - 350, -1300, -1536), (x + 350, -1000, -1376), 'hkgraft2', top='hkgrlite')
    b.rooms['lab'] += plaque(Wall('y', -1500, (0, 1, 0)), x, -1280, 128, 256, 'hkgraft')
panel('lab_console', 'lab', Wall('x', 7864, (-1, 0, 0)), mark('Lab turret')['y'], -1440,
      128, 160, 'hkconsol', 72, 72)
r = R['quarry']
for k in range(3):
    b.rooms['quarry'] += clip_to(box((r['x'], r['y'] + k * 300, -1536),
                                     (r['x'] + r['w'], r['y'] + (k + 1) * 300, -1536 + (3 - k) * 128),
                                     'hkrock', top='hkore'), b.footprints['quarry'])
# A broad, low rubble silhouette marks the cracked face, leaving its northern approach open.
for coords, role, normal in prism(4000, -2750, 200, -1536, -1376, 'hkrock', top='hkore', turn=0):
    from mathutils import Vector
    coords = [(4000 + (x - 4000) * (0.65 if z == -1376 else 1),
               -2750 + (y + 2750) * (0.325 if z == -1376 else 0.5), z) for x, y, z in coords]
    n = (Vector(coords[1]) - Vector(coords[0])).cross(Vector(coords[2]) - Vector(coords[0])).normalized()
    b.rooms['quarry'].append((coords, role, tuple(n if n.dot(Vector(normal)) > 0 else -n)))

# Loot placements come directly from the plan's markers.
chest_events = {36: 0}
for event, m in enumerate([m for m in PLAN.marks if m['kind'] in ('chest_fixed', 'chest_random')], 30):
    model = 'hes_colonial_locker' if event in (30, 35) else 'hes_kreegan_pod_chest'
    b.decoration(model, m['x'], m['y'], PLAN.floors[m['floor']], 0, event=event)
    chest_events[event] = event - 29

# Loose props are laid out from each room's walls/lanes, clear of the path and opening centres.
for rid, name, x, y, z in (
        ('gallery', 'hes_drum', 5590, 2950, 0), ('gallery', 'hes_ore_crates', 5620, 2170, 0),
        ('barracks', 'hes_drum', 4700, 4400, -768), ('barracks', 'hes_drum', 4700, 4520, -768),
        ('yard', 'hes_ore_cart', 2400, 1700, -768), ('yard', 'hes_ore_cart', 4350, 3350, -768),
        ('yard', 'hes_ore_cart', 5200, 1150, -768), ('yard', 'hes_salvage_heap', 3100, 3450, -768),
        ('yard', 'hes_salvage_heap', 3600, 1150, -768), ('yard', 'hes_corpse_kept', 2600, 1150, -768),
        ('quarry', 'hes_ore_cart', 1400, -2000, -1536), ('quarry', 'hes_ore_cart', 3800, -2000, -1536),
        ('quarry', 'hes_salvage_heap', 3950, -1800, -1536), ('niche', 'hes_corpse_colonist', 4700, -2950, -1536)):
    b.decoration(name, x, y, z)
for light in PLAN.lights:
    # Integrator's reviewed placements supersede the plan's buried fires and above-ceiling alarm light.
    if light['id'] in ('F_quarry1', 'F_quarry2'):
        light = dict(light, y=-2500, z=-1536)
    elif light['id'] == 'L4':
        light = dict(light, z=-420)
    b.plan_light(light, zone.plans.FIXTURE_COG)

# Split whole-room geometry at the plan's sector lines, keeping each polygon's fitted UV frame.
SPLITS = {'yard': ([2200, 3800, 5400], [1000, 2300, 3600]), 'roost': ([0, 2136], [2264, 3264, 4264]),
          'barracks': ([2400, 3600, 4800], [3664, 4964]), 'storage': ([3800, 5000, 6200], [-1500, 172]),
          'crusher': ([1200, 2500, 3736], [-1500, 300]), 'quarry': ([1200, 2700, 4200], [-3500, -1564])}


def clipped(panel, bounds):
    points = [tuple(p) for p in panel[0]]
    for axis, limit, sign in ((0, bounds[0], 1), (0, bounds[2], -1),
                              (1, bounds[1], 1), (1, bounds[3], -1)):
        result = []
        for a, c in zip(points, points[1:] + points[:1]):
            da, dc = (a[axis] - limit) * sign, (c[axis] - limit) * sign
            if da >= -0.001:
                result.append(a)
            if (da < 0 < dc) or (dc < 0 < da):
                t = da / (da - dc)
                result.append(tuple(a[k] + (c[k] - a[k]) * t for k in range(3)))
        points = result
        if len(points) < 3:
            return None
    from mathutils import Vector
    area = sum((Vector(points[k]) - Vector(points[0])).cross(Vector(points[k + 1]) - Vector(points[0])).length
               for k in range(1, len(points) - 1))
    return (points, *panel[1:]) if area > 0.01 else None


parts = {}
for rid in list(b.rooms):
    old, bound, ambient = b.rooms.pop(rid), b.bounds.pop(rid), b.ambient.pop(rid)
    xs, ys = SPLITS.get(rid, ([bound[0], bound[2]], [bound[1], bound[3]]))
    parts[rid] = []
    # Reveals extend beyond the logical room rectangle: include them in the outermost sector's clip bounds.
    for iy, (y0, y1) in enumerate(zip(ys, ys[1:])):
        for ix, (x0, x1) in enumerate(zip(xs, xs[1:])):
            name = f'{rid}_{ix}_{iy}' if rid in SPLITS else rid
            bounds = (x0, y0, x1, y1, bound[4], bound[5])
            clip = (x0 if ix else x0 - 64, y0 if iy else y0 - 64,
                    x1 if ix < len(xs) - 2 else x1 + 64, y1 if iy < len(ys) - 2 else y1 + 64)
            b.room(name, bounds, ambient)
            b.rooms[name] += [q for p in old if (q := clipped(p, clip))]
            parts[rid].append((name, clip))
    for a, ac in parts[rid]:
        ab = b.bounds[a]
        for c, cc in parts[rid]:
            cb = b.bounds[c]
            if ab[2] == cb[0] and ab[1:4:2] == cb[1:4:2]:
                b.portal(a, c, [(ab[2], ab[1], bound[4] + 1), (ab[2], ab[3], bound[4] + 1),
                                (ab[2], ab[3], bound[5]), (ab[2], ab[1], bound[5])])
            if ab[3] == cb[1] and ab[0:3:2] == cb[0:3:2]:
                b.portal(a, c, [(ab[0], ab[3], bound[4] + 1), (ab[2], ab[3], bound[4] + 1),
                                (ab[2], ab[3], bound[5]), (ab[0], ab[3], bound[5])])
portals = b.portals[:len(openings)]
b.portals = b.portals[len(openings):]
for front, back, coords in portals:
    for f, fc in parts[front]:
        for t, tc in parts[back]:
            p = clipped((coords, 'marker', (1, 0, 0)), fc)
            q = clipped(p, tc) if p else None
            if q:
                b.portal(f, t, q[0])
triggers, b.triggers = b.triggers, []
for name, rid, panels, event, kind, flags, cog in triggers:
    for part, clip in parts[rid]:
        cut = [q for p in panels if (q := clipped(p, clip))]
        if cut:
            b.trigger(f'{name}_{part}', part, cut, event, kind, flags, cog)
for k, mech in enumerate(b.mechanisms):
    name, rid, panels, *tail = mech
    centre = [sum(p[i] for p in panels[0][0]) / len(panels[0][0]) for i in range(3)]
    part = next(n for n, clip in parts[rid] if clip[0] <= centre[0] <= clip[2] and clip[1] <= centre[1] <= clip[3])
    b.mechanisms[k] = (name, part, panels, *tail)

# Packs retain stable actor indices for hooks; spread from the design's pack anchors within their rooms.
actors = []


def actor(monster, x, y, z, group, posted=False, yaw=0):
    actors.append({'monster': monster, 'position': [round(x), round(y), round(z)], 'group': group,
                   'posted': posted, 'yaw_degrees': yaw, 'name': '',
                   'sector': sorted(b.rooms).index(b.room_at(x, y, z + 1)) + 1})


for x, y in ((7060, 2100), (7060, 3130)):          # their pedestals stood 72 into the Gatehouse's west wall
    actor(10055, x, y, 160, 10, True, 180)
    rid = b.room_at(x, y, 1)
    b.rooms[rid] += prism(x, y, 110, 0, 160, 'hoaresin', top='hochitin', turn=0)
for y in (2400, 2650):
    actor(10010, 5700, y, 0, 25, True, 180)
pack_offsets = {
    20: [(-330, -100), (-150, 160), (110, -140), (335, 90), (60, 190)],
    21: [(-320, -100), (-170, 150), (180, 120), (330, -150)],
    22: [(-320, -100), (-100, 120), (210, -160), (370, 100), (70, 300)],
    23: [(-380, -90), (-170, 140), (80, -150), (350, 50), (-270, -320), (230, -340)],
    24: [(-370, 210), (-180, 460), (40, 180), (330, 370), (-320, 500), (170, 520)],
    26: [(-180, 65), (0, 170), (200, 85)],
    27: [(-185, 40), (25, 190), (215, 65)],
    40: [(-250, -70), (-90, 100), (90, -50), (250, 80)],
    41: [(-240, 80), (-70, -60), (110, 110), (250, -45)],
}
for label, count, group, monster, posted in (
        ('north cover lane', 3, 26, 10010, True), ('south cover lane', 3, 27, 10010, True),
        ('resting between', 5, 20, 10010, False), ('at the mess', 4, 21, 10010, False),
        ('wave 1:', 4, 40, 10010, False), ('wave 2:', 4, 41, 10010, False),
        ('moving ore', 5, 22, 10000, False), ('feeding the crusher', 6, 23, 10000, False),
        ('at the working face', 6, 24, 10000, False)):
    m = mark(label)
    assert len(pack_offsets[group]) == count
    for dx, dy in pack_offsets[group]:
        x, y = m['x'] + dx, m['y'] + dy
        if group == 23:
            y -= 400
        z = PLAN.floors[m['floor']]
        target = {20: (m['x'], m['y']), 21: (m['x'], m['y']),
                  22: (min((4200, 4900, 5600), key=lambda ore_x: abs(ore_x - x)), -1250),
                  23: (hx, hy), 24: (m['x'], -2800)}.get(group, (3800, 2300))
        actor(monster, x, y, z, group, posted, math.degrees(math.atan2(target[1] - y, target[0] - x)))
boss_index = len(actors)
actor(10102, bx, by, 448, 30)
for k in range(6):
    angle = 2 * math.pi * k / 6
    actor(10010, bx + 600 * math.cos(angle), by + 550 * math.sin(angle), 0, 31, True)
for k, (x, y) in enumerate(pens):
    for dy in (-140, 140):
        actor(10000, x + 230, y + dy, 0, 32 + k)
for x in (6800, 7400):
    actor(10055, x, -600, -1376, 11, True, 180)
    rid = b.room_at(x, -600, -1535)
    b.rooms[rid] += prism(x, -600, 110, -1536, -1376, 'hoaresin', top='hochitin', turn=0)

# R5 Ashkite wildlife: the open north half of the Quarry Face, clear of the stepped ore face and carts.
for flock, (cx, cy) in enumerate(((2000, -2300), (3100, -2300))):
    for dx, dy in ((-180, -140), (180, -140), (-180, 140), (180, 140)):
        actor(10310, cx + dx, cy + dy, -1536, 150 + flock, yaw=90)
        actors[-1]['name'] = f'Ashkite Quarry Face flock {flock + 1}'

assert len(b.rooms) == 25, len(b.rooms)
assert len(actors) == 67, len(actors)
assert {m[3] for m in b.mechanisms} == set(range(51, 59))
assert len(b.lights) + sum(bool(l['fixture']) for l in PLAN.lights) == len(PLAN.lights)
start = mark('Arrival:')
# Four vats in Lower Storage, two in the Barracks, two in Krav's rear Signal Room.
# 2510 faces reach the 20-bundle cap; the Yard corpse and Crusher replace the old fixed gold piles.
VATS = [
    ('storage_0_0', 701, 4150, -150, -1536, 270),
    ('storage_0_0', 702, 4330, -150, -1536, 270),
    ('storage_0_0', 703, 4510, -150, -1536, 270),
    ('storage_0_0', 704, 4690, -150, -1536, 270),
    ('barracks_1_0', 705, 4400, 4150, -768, 180),
    ('barracks_1_0', 706, 4400, 4330, -768, 180),
    ('signal', 707, 1700, 4900, 0, 180),
    ('signal', 708, 1700, 5100, 0, 180),
]
assert len(VATS) == 8 and {p[1] for p in VATS} == set(range(701, 709))
BUNDLES = [
    ('gatehouse', 751, 8020, 3080, 0, 240),
    ('gallery', 752, 6650, 3100, 0, 230),
    ('gallery', 753, 6650, 2120, 0, 100),
    ('yard_0_0', 754, 2750, 1120, -768, 20),
    ('yard_0_1', 755, 3400, 3450, -768, 140),
    ('yard_1_1', 756, 5000, 3450, -768, 220),
    ('yard_0_1', 757, 2320, 2900, -768, 30),
    ('barracks_1_0', 758, 4600, 3850, -768, 60),
    ('barracks_1_0', 759, 3950, 4800, -768, 180),
    ('mess', 760, 6200, 4200, -768, 70),
    ('mess', 761, 6200, 4750, -768, 210),
    ('storage_0_0', 762, 3950, -850, -1536, 20),
    ('storage_1_0', 763, 6050, -1250, -1536, 140),
    ('crusher_0_0', 764, 1500, -1300, -1536, 30),
    ('crusher_0_0', 765, 1450, 150, -1536, 240),
    ('lab', 766, 6400, -350, -1536, 180),
    ('quarry_0_0', 767, 1450, -1650, -1536, 140),
    ('quarry_1_0', 768, 3500, -1700, -1536, 210),
    ('niche', 769, 4400, -2900, -1536, 40),
    ('signal', 770, 500, 4500, 0, 45),
]
assert len(BUNDLES) == 20 and {p[1] for p in BUNDLES} == set(range(751, 771))
for name, placements in (('hes_serum_vat', VATS), ('hes_scrap_bundle', BUNDLES)):
    for room, event, x, y, z, facing in placements:
        assert b.room_at(x, y, z + 1) == room, (room, event)
        b.decoration(name, x, y, z, facing, event=event, cog=event)

b.export({'pickups': VATS + BUNDLES, 'arrivals': {'d03_outer_gate': {'position': [start['x'], start['y'], 0], 'direction_degrees': 180}},
          'door_ids': {m[0]: m[3] for m in b.mechanisms}, 'chest_events': chest_events, 'actors': actors,
          'boss_index': boss_index, 'barracks_indices': [i for i, a in enumerate(actors) if a['group'] == 20],
          'monster_packs': [m for m in PLAN.marks if m['kind'] in ('monster', 'boss')]})

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
