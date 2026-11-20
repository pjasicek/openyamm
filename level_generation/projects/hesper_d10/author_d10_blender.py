"""Build the Colony Archive from the reviewed D10 plan with the shared Hesper indoor kit."""
import importlib.util
import os
import math
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
from blv_kit import Vector, Wall, banded, box, floor, plaque, prism

spec = importlib.util.spec_from_file_location('plans', ROOT / 'design/kreegan_world/zone1/dungeons/make_dungeon_plans.py')
plans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plans)
PLAN = plans.d10
R = {r['id']: dict(r) for r in PLAN.rooms}
ROLE = dict(wall='hcpanel', recess='hcrecess', trim='hctrim', floor='hcfloor', ceiling='hcceiling',
            grille='hcgrille', door='hcdoor', sign='hcsign', console='hcconsole', dome='hodome',
            marble='hamarble', shelf='hashelf', reader='hareader', ilen='hapilen', sesha='hapsesha',
            torvan='haptorvan', makers='hapmakers', well='hawell', off='hawelloff', on='hawellon',
            rack='harack', mural='hamural', water='hawater', gold='hogold', strip='hcstripw',
            alarm='hcstripr', hatch='hskyhatch', marker='hcconsole')
b = kit.Builder('hes_d10.blv', ROLE, PROJECT / 'source')
# The plan shares wall centre-lines; inset adjoining rooms 32 each for the kit's 64-unit reveals.
B = {rid: [r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']] for rid, r in R.items()}
B['atrium'][2] -= 32
B['atrium'][1] += 32
B['reading'][0] += 32
B['reading'][2] -= 32
B['stacks'][0] += 32
B['ramp'][1] += 32
B['ramp'][3] -= 32
B['wells'][0] += 32
B['wells'][2] -= 32
B['wells'][3] -= 32
B['armoury'][0] += 32
B['hall'][2] -= 32
SPLITS = {'atrium': (0, 1200), 'reading': (0, 3900), 'stacks': (0, 6600),
          'ramp': (1, -900), 'hall': (0, -800)}
AMBIENT = dict(atrium=18, reading=22, stacks=26, ramp=24, wells=24, armoury=24, hall=28)
FOOTPRINTS = {}
HOLES = {rid: {} for rid in R}
LINKS = []
# The links remain in plan order. The two ramp ends have different floor heights.
for link, (owner, side, other, height) in zip(PLAN.links[1:], [
        ('atrium', 'east', 'reading', 384), ('reading', 'east', 'stacks', 384),
        ('atrium', 'south', 'ramp', 384), ('ramp', 'south', 'wells', 384),
        ('wells', 'east', 'armoury', 384), ('wells', 'west', 'hall', 384)]):
    axis = 'x' if side in ('west', 'east') else 'y'
    along = link['y'] if axis == 'x' else link['x']
    a0, a1 = along - link['width'] / 2, along + link['width'] / 2
    z = -512 if other in ('wells', 'armoury', 'hall') else 0
    opposite = dict(west='east', east='west', south='north', north='south')[side]
    HOLES[owner].setdefault(side, []).append((a0, a1, z, z + height))
    HOLES[other].setdefault(opposite, []).append((a0, a1, z, z + height))
    plane = B[owner][dict(west=0, south=1, east=2, north=3)[side]]
    LINKS.append((owner, other, axis, plane, a0, a1, z, z + height, -1 if side in ('west', 'south') else 1))


def sector(rid, x, y):
    if rid not in SPLITS:
        return rid
    axis, value = SPLITS[rid]
    return rid + ('_a' if (x, y)[axis] < value else '_b')


def clip(coords, axis, value, sign):
    """Clip a convex panel at a sector split without introducing another wall."""
    result = []
    for a, c in zip(coords, coords[1:] + coords[:1]):
        da, dc = sign * (a[axis] - value), sign * (c[axis] - value)
        if da >= -0.001:
            result.append(a)
        if (da < -0.001 and dc > 0.001) or (dc < -0.001 and da > 0.001):
            result.append(a + (c - a) * (da / (da - dc)))
    return result


def add(rid, panels):
    for coords, role, normal, *extra in panels:
        coords = [Vector(p) for p in coords]
        if rid not in SPLITS:
            b.rooms[rid].append((coords, role, normal, *extra))
            continue
        axis, value = SPLITS[rid]
        for suffix, sign in (('_a', -1), ('_b', 1)):
            points = clip(coords, axis, value, sign)
            if len(points) >= 3 and (points[1] - points[0]).cross(points[2] - points[0]).length > 0.01:
                b.rooms[rid + suffix].append((points, role, normal, *extra))


def panel(coords, role, down=False):
    points = [Vector(p) for p in coords]
    normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
    if down and normal.z > 0:
        normal = -normal
    return [(points, role, normal)]


for rid, r in R.items():
    x0, y0, x1, y1 = B[rid]
    z, height = r['z'], r['ceiling']
    if rid in SPLITS:
        axis, value = SPLITS[rid]
        lo, hi = B[rid].copy(), B[rid].copy()
        lo[axis + 2], hi[axis] = value, value
        if rid=='ramp':lo[2]+=128;hi[2]+=128
        for suffix, bounds in (('_a', lo), ('_b', hi)):
            b.room(rid + suffix, (*bounds, -513 if rid == 'ramp' else z - 1, z + height), AMBIENT[rid])
    else:
        b.room(rid, (*B[rid], z - 1, z + height), AMBIENT[rid])
    if rid == 'ramp':
        # Both gallery walls turn at 45 degrees, preserving a 512-wide floor and the original doorway positions.
        def left(y):
            return x0 + min(128, max(0, y-y0-192), max(0, y1-192-y))
        def right(y):
            return x1+left(y)-x0
        turns=[y0,y0+192,y0+320,-900,y1-320,y1-192,y1]
        FOOTPRINTS[rid]=[(x0,y0),(x1,y0),(x1,y0+192),(x1+128,y0+320),
                         (x1+128,y1-320),(x1,y1-192),(x1,y1),(x0,y1),
                         (x0,y1-192),(x0+128,y1-320),(x0+128,y0+320),(x0,y0+192)]
        for ya, yb in zip(turns,turns[1:]):
            za, zb = -512 + 512 * (ya - y0) / (y1 - y0), -512 + 512 * (yb - y0) / (y1 - y0)
            add(rid, panel([(left(ya), ya, za), (right(ya), ya, za), (right(yb), yb, zb), (left(yb), yb, zb)], 'floor'))
            add(rid, panel([(left(ya), ya, za + 384), (right(ya), ya, za + 384),
                            (right(yb), yb, zb + 384), (left(yb), yb, zb + 384)], 'ceiling', True))
            for xa, xb, normal in ((left(ya), left(yb), Vector((yb-ya, left(ya)-left(yb), 0)).normalized()),
                                   (right(ya), right(yb), Vector((ya-yb, right(yb)-right(ya), 0)).normalized())):
                for low, high, role in ((0, 32, 'trim'), (32, 352, 'wall'), (352, 384, 'trim')):
                    add(rid, [([(xa, ya, za + low), (xb, yb, zb + low),
                                (xb, yb, zb + high), (xa, ya, za + high)], role, normal)])
        b.portal('ramp_a', 'ramp_b', [(left(-900), -900, -256), (right(-900), -900, -256),
                                     (right(-900), -900, 128), (left(-900), -900, 128)])
        continue
    chamfer = {'atrium':480, 'wells':180, 'reading':128}.get(rid,0)
    poly = [(x0 + chamfer, y0), (x1 - chamfer, y0), (x1, y0 + chamfer), (x1, y1 - chamfer),
            (x1 - chamfer, y1), (x0 + chamfer, y1), (x0, y1 - chamfer), (x0, y0 + chamfer)] if chamfer else [
                (x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    FOOTPRINTS[rid]=poly
    floor_role = 'marble' if rid in ('atrium', 'hall') else 'water' if rid == 'stacks' else 'floor'
    floors = [([(x, y, z) for x, y in poly], floor_role, (0, 0, 1))]
    if rid == 'stacks':
        # shortcut: the compiler has no indoor water flag; hawater is a safe walkable floor until shallow water exists.
        for suffix, sign in (('_a', -1), ('_b', 1)):
            coords = clip([Vector(p) for p in floors[0][0]], 0, SPLITS[rid][1], sign)
            b.surface('shallow_water' + suffix, rid + suffix, [(coords, 'water', (0, 0, 1))], flags=())
    else:
        add(rid, floors)
    wall_height = 640 if rid == 'atrium' else height
    bands = [(z, z + 32, 'trim'), (z + 32, z + 192, 'recess'), (z + 192, z + 224, 'gold'),
             (z + 224, z + wall_height - 32, 'wall'), (z + wall_height - 32, z + wall_height, 'trim')]
    for a, c in zip(poly, poly[1:] + poly[:1]):
        ax, ay = a
        cx, cy = c
        if ax == cx or ay == cy:
            side = ('west' if ax == x0 else 'east') if ax == cx else ('south' if ay == y0 else 'north')
            normal = dict(west=(1, 0, 0), east=(-1, 0, 0), south=(0, 1, 0), north=(0, -1, 0))[side]
            wall = Wall('x' if ax == cx else 'y', ax if ax == cx else ay, normal)
            a0, a1 = sorted((ay, cy) if ax == cx else (ax, cx))
            add(rid, banded(wall, a0, a1, bands, HOLES[rid].get(side, [])))
        else:
            normal = Vector((ay - cy, cx - ax, 0)).normalized()
            for za, zb, role in bands:
                add(rid, [([(ax, ay, za), (cx, cy, za), (cx, cy, zb), (ax, ay, zb)], role, normal)])
    if rid == 'atrium':
        centre = Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0))
        rings = [[(centre.x + (x - centre.x) * scale, centre.y + (y - centre.y) * scale, zz)
                  for x, y in poly] for scale, zz in ((1, 640), (.72, 1040), (.24, 1280))]
        for outer, inner in zip(rings, rings[1:]):
            for i in range(8):
                add(rid, panel([outer[i], outer[(i + 1) % 8], inner[(i + 1) % 8], inner[i]], 'dome', True))
        add(rid, [(rings[-1], 'hatch', (0, 0, -1))])
    else:
        add(rid, [([(x, y, z + height) for x, y in poly], 'ceiling', (0, 0, -1))])
    if rid in SPLITS:
        axis, value = SPLITS[rid]
        coords = [(value, y0, z), (value, y1, z), (value, y1, z + height), (value, y0, z + height)] if axis == 0 else [
            (x0, value, z), (x1, value, z), (x1, value, z + height), (x0, value, z + height)]
        b.portal(rid + '_a', rid + '_b', coords)

for rid,poly in FOOTPRINTS.items():
    if rid in SPLITS:
        axis,value=SPLITS[rid]
        for suffix,sign in (('_a',-1),('_b',1)):
            b.footprints[rid+suffix]=[(p.x,p.y) for p in clip([Vector((x,y,0)) for x,y in poly],axis,value,sign)]
    else:b.footprints[rid]=poly

DOORS = dict(reading=1, armoury=2, founders=3)
for i, (owner, other, axis, plane, a0, a1, z0, z1, toward) in enumerate(LINKS):
    x, y = (plane, (a0 + a1) / 2) if axis == 'x' else ((a0 + a1) / 2, plane)
    front, back = sector(owner, x, y), sector(other, x, y)
    first_reveal = len(b.rooms[front])
    b.opening(front, back, axis, plane, a0, a1, z0, z1, toward=toward)
    if owner == 'atrium' and other == 'ramp':
        # The doorway straddles both atrium sectors; split its portal and reveal without adding a central jamb.
        reveal = b.rooms[front][first_reveal:]
        del b.rooms[front][first_reveal:]
        add(owner, reveal)
        _, _, points = b.portals.pop()
        for suffix, sign in (('_a', -1), ('_b', 1)):
            half = clip([Vector(p) for p in points], *SPLITS[owner], sign)
            b.portal(owner + suffix, back, half)
    if i in (0, 4, 5):
        key, event = {0: ('reading', 21), 4: ('armoury', 16), 5: ('founders', 22)}[i]
        middle = plane + toward * 32
        panels = box((middle - 12, a0, z0), (middle + 12, a1, z1), 'door', top='trim')
        b.door(key + '_door', front, panels, DOORS[key], z1 - z0 + 32, open_speed=416, close_speed=416, event=event)

# Entry, relay and the four independent socket lights, anchored to the arrival and relay marks.
start = next(m for m in PLAN.marks if m['kind'] == 'start')
relay = next(m for m in PLAN.marks if m['label'].startswith('Aster relay'))
entry = PLAN.links[0]
b.trigger('dome_stair', 'atrium_b', plaque(Wall('y', entry['y'], (0, -1, 0)), entry['x'], 0,
                                                entry['width'], 384, 'door', out=16), 2)
b.decoration('hes_relay_post', relay['x'], relay['y'], 0, event=3)
for i, dx in enumerate((-420, -240, 240, 420)):
    x, y = start['x'] + dx, start['y']
    add('atrium', box((x - 64, y - 32, 0), (x + 64, y + 32, 80), 'marble', top='gold'))
    b.decoration('hes_crystal_socket', x, y, 80)
    b.light('socket_' + str(i + 1), x, y, 141, 120, (120, 230, 255), 41 + i)
for dx in (-600, 600):
    b.decoration('hes_tablet_plinth', relay['x'] + dx, relay['y'], 0)

# Desks and benches, anchored symmetrically to the two reading lights. Central aisle stays clear.
for light in [p for p in PLAN.lights if p['id'] in ('L2', 'L3')]:
    x, y = light['x'], light['y']
    for dy in (-350, 350):
        add('reading', box((x - 300, y + dy - 90, 0), (x + 300, y + dy + 90, 96), 'reader', top='reader'))
        b.decoration('hes_bench', x, y + dy + (170 if dy < 0 else -170), 0, 0 if dy < 0 else 180)
    b.decoration('hes_bench', x - 450, y - 350, 0, 90)
    for dx in (-220, 220):
        add('reading', kit.pipe((x + dx, y, 232), (x + dx, y, R['reading']['ceiling']), 8, 'trim'))
    add('reading', box((x - 250, y - 12, 208), (x + 250, y + 12, 232), 'strip', top='trim'))
plaques = next(m for m in PLAN.marks if m['label'].startswith('Founders\' plaques'))
for i, role in enumerate(('ilen', 'sesha', 'torvan', 'makers')):
    x, y = plaques['x'] + (i - 1.5) * 320, plaques['y']
    b.trigger(role + '_plaque', sector('reading', x, y),
              plaque(Wall('y', B['reading'][3], (0, -1, 0)), x, 192, 256, 256, role, out=8), 4 + i)
charter = [plaques['x'], plaques['y'] - 200, 115]
b.decoration('hes_lectern', charter[0], charter[1], 0)
# Ground items settle on BLV floors, so the lectern needs a physical tray as well as its decoration model.
x, y = charter[:2]
add('reading', box((x - 42, y - 42, 111), (x + 42, y + 42, 115), 'gold', top='gold'))

# Crystal shelves leave a 700-unit central aisle and a clear route to the drowned archivist.
trap = next(m for m in PLAN.marks if m['kind'] == 'trap')
for light in [p for p in PLAN.lights if p['id'] in ('L4', 'L5')]:
    for dy in (-850, 850):
        x, y = light['x'], light['y'] + dy
        end = x + 350
        for mark in PLAN.marks:
            if mark['kind'] in ('item', 'chest_random') and x - 350 < mark['x'] < end + 180 and abs(mark['y'] - y) < 180:
                end = min(end, mark['x'] - 180)
        add('stacks', box((x - 350, y - 80, 0), (end, y + 80, 448), 'shelf', top='trim'))
add('stacks', box((trap['x'] - 200, trap['y'] - 60, 0), (trap['x'] + 200, trap['y'] + 60, 400),
                  'shelf', top='strip'))
for event, mark in zip((8, 9), [m for m in PLAN.marks if m['kind'] == 'chest_random']):
    b.decoration('hes_colonial_locker', mark['x'], mark['y'], 0, event=event)
key = next(m for m in PLAN.marks if m['label'].startswith('The armoury key'))
b.decoration('hes_corpse_colonist', key['x'], key['y'], 0, event=10)

# Memory wells: ceramic octagonal drums and independent clickable, swappable glass tops.
wells = [m for m in PLAN.marks if m['label'].startswith('Memory well')]
for i, m in enumerate(wells):
    x, y = m['x'], m['y']
    add('wells', prism(x, y, 148, -512, -400, 'well'))
    top = prism(x, y, 148, -400, -399, 'well', top='off')[-1:]
    b.trigger('memory_well_' + str(i + 1), 'wells', top, 12 + i, cog=31 + i)
    image = Wall('y', y + 32, (0, -1, 0))
    fit = image.fit(x - 64, x + 64, -352, -192)
    b.surface('founder_image_' + str(i + 1), 'wells',
              image.quad(x - 64, x + 64, -352, -192, ('torvan', 'ilen', 'makers', 'sesha')[i], fit=fit),
              flags=('invisible', 'untouchable'), cog=51 + i)
console = next(m for m in PLAN.marks if m['label'].startswith('Armoury turret'))
# The marker is behind the locked door: expose its control face on the Wells side for the alternative route.
b.trigger('armoury_console', 'wells', plaque(Wall('x', B['wells'][2], (-1, 0, 0)), console['y'],
                                           -448, 224, 224, 'console', out=16), 17)
for side, wall, along, width in (
        ('north', Wall('y', B['armoury'][3], (0, -1, 0)), 2800, 1100),
        ('east', Wall('x', B['armoury'][2], (-1, 0, 0)), -2800, 800)):
    add('armoury', plaque(wall, along, -480, width, 352, 'rack', out=12))
shelf = next(m for m in PLAN.marks if m['label'].startswith('The relic gun'))
x, y = shelf['x'], shelf['y']
add('armoury', box((x - 230, y - 90, -512), (x + 230, y + 90, -400), 'reader', top='gold'))
ground_items = [dict(item=11372, position=charter, label='Founders Charter on the reading lectern'),
                dict(item=11420, position=[x - 80, y, -400], label='Founders Repeater on its shelf'),
                dict(item=189, amount=20000, position=[x + 100, y, -400], label='Armoury gold on its shelf')]
casket = next(m for m in PLAN.marks if m['kind'] == 'chest_fixed')
record = next(m for m in PLAN.marks if m['label'].startswith('The founders\' record'))
b.decoration('hes_casket', casket['x'], casket['y'], -512, event=19)
b.decoration('hes_lectern', record['x'], record['y'], -512, event=20)
for i in range(4):
    x, y = B['hall'][0] + 240, R['hall']['y'] + 420 + 520 * i
    add('hall', box((x - 110, y - 110, -512), (x + 110, y + 110, -480), 'marble', top='gold'))
    b.decoration('hes_founder_intact', x, y, -480, 90)
add('hall', plaque(Wall('y', B['hall'][1], (0, 1, 0)), casket['x'], -192, 1400, 448, 'mural', out=8))

for light in PLAN.lights:
    light = dict(light)
    if light['id'] in ('L7', 'L8', 'L9', 'L10'):
        light['group'] = int(light['id'][1:]) + 24
    b.plan_light(light, plans.FIXTURE_COG)
    if light['id'] in ('L6', 'L11', 'L13', 'L12'):
        x, y, z = light['x'], light['y'], light['z']
        rid = dict(L6='ramp', L11='armoury', L13='wells', L12='hall')[light['id']]
        if rid=='ramp':z+=128  # Keep the hanging fixture above the melee monsters' heads.
        add(rid, box((x - 96, y - 12, z + 8), (x + 96, y + 12, z + 24),
                     'alarm' if light['id'] == 'L11' else 'gold' if light['id'] == 'L12' else 'strip'))
        roof = (128 if rid == 'ramp' else R[rid]['z'] + R[rid]['ceiling'])
        for dx in (-64, 64):
            add(rid, kit.pipe((x + dx, y, z + 24), (x + dx, y, roof), 8, 'trim'))
# The GLB exporter emits ROOM meshes alphabetically; the compiler assigns sectors in that order.
actors = []
for group, (mark, monster) in enumerate(zip([m for m in PLAN.marks if m['kind'] == 'monster'],
                                           (10052, 10051, 10052, 10056)), 1):
    for i in range(mark['count']):
        rid = ('reading', 'stacks', 'wells', 'armoury')[group - 1]
        x, y = mark['x'], mark['y'] + (i - (mark['count'] - 1) / 2) * 160
        if group==1 and i==1:x=3500  # Clear the suspended reading-light crossbar.
        z = R[rid]['z'] + (180 if monster != 10056 else 0)
        actors.append(dict(monster=monster, position=[x, y, z], group=group, posted=monster == 10056,
                           yaw_degrees=180, sector=sorted(b.rooms).index(sector(rid, x, y)) + 1))
for item in ground_items:
    item['sector'] = sorted(b.rooms).index(b.room_at(*item['position'])) + 1
assert len(b.rooms) == 12 and len(b.portals) == 12 and len(b.mechanisms) == 3 and len(actors) == 11
assert len(wells) == 4 and len(b.lights) == 17
assert all(len(key) <= 10 and kit.texture_path(key).exists() for key in ROLE.values())
# PICKUPS.md: supplies at room edges, with the event also serving as the sprite-swap cog.
pickups = json.loads((PROJECT / 'pickups.json').read_text())
assert len(pickups) == 22 and sum(p['model'] == 'hes_stim_canister' for p in pickups) == 12
assert [p['event'] for p in pickups] == list(range(700, 712)) + list(range(750, 760))
for pickup in pickups:
    x, y, z = pickup['position']
    room = R[pickup['room']]
    assert room['x'] + 64 <= x <= room['x'] + room['w'] - 64
    assert room['y'] + 64 <= y <= room['y'] + room['h'] - 64
    assert z == room['z']
    assert b.room_at(x,y,z).startswith(pickup['room']),pickup
    b.decoration(pickup['model'], x, y, z, event=pickup['event'], cog=pickup['event'])

# Do not trim controls or fixtures away when a room corner changes.
for name,room,panels,*_ in b.triggers+b.mechanisms:
    if not room.startswith('reading'):continue
    for (ax,ay),(bx,by) in zip(FOOTPRINTS['reading'],FOOTPRINTS['reading'][1:]+FOOTPRINTS['reading'][:1]):
        if ax==bx or ay==by:continue
        for v in (v for panel in panels for v in panel[0]):
            assert (Vector(v)-Vector((ax,ay,0))).dot(Vector((by-ay,ax-bx,0)))<=1,(name,v)
for _,x,y,z,*_ in b.decorations+b.lights:b.room_at(x,y,z)
for actor in actors:b.room_at(*actor['position'])

b.export(dict(pickups=pickups, arrivals={'dome_stair': dict(position=[start['x'], start['y'], 0], direction_degrees=270)},
              door_ids=DOORS, chest_events={8: 0, 9: 1, 19: 2}, actors=actors, ground_items=ground_items,
              trap=dict(position=[trap['x'], trap['y'], 0], radius=300),
              adjustments=['64-unit thick walls; console exposed on outer Armoury wall',
                           '4 socket lights supplement the 13 plan lights',
                           'Charter lectern fitted beside the plaque group; incidental floor gold replaced by supply satchels']))

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
