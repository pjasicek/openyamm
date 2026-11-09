"""Build Crownspire one floor at a time: blender -b --python author_d12_blender.py -- --through core|palace|court|crown."""
import argparse
import math
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
from layout import ARRIVALS, DOORS, FLOORS, LEVELS, PLAN, ROOMS, ROOT, checks, zone
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
from blv_kit import (Wall, Fit, banded, beam, box, ceiling, floor, pipe, plaque, prism, chamfer_rect,
                     clip_to, hip_ceiling, rect_walls, flight_along, ring_flight)

parser = argparse.ArgumentParser()
parser.add_argument('--through', choices=LEVELS, default='crown')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
active = set(FLOORS[x] for x in LEVELS[:LEVELS.index(args.through) + 1])
kit.FOLDERS += [kit.ART / f'textures_{key}/masters' for key in ('k10_palace', 'k9_lattice', 'k3_transit', 'k5_grafted')]
keys = ('hpwall hprelief hpcolumn hpgraft hplift hpfloor hpring hpceil hptrim hpglow hpglass hpbanner '
        'hptroph1 hptroph2 hpsigil1 hpsigil2 hpsigil3 hpdoor hpthrone hpvoice hpvoicef hpvoicex hogate hogateof '
        'hcpanel hctrim hcrecess hcfloor hcceiling hcdoor hcconsole hcmachine htexch htgrid htgridof '
        'hnresin hnconduit hnmach hokwall hogold').split()
roles = {key: key for key in keys}
roles.update(floor='hpfloor', ceiling='hpceil', trim='hptrim', marker='hcconsole')
b = kit.Builder('hes_d12.blv', roles, PROJECT / 'source')
R = {k: dict(r) for k, r in ROOMS.items() if r['sectors'] and (r['floor'] in active or k == 'corelift')}
holes, links, cells = {}, [], {}
obstacles = []
if 'stair' in R: R['stair']['ceiling'] = 1280
CHAMFER = {'gate': 200, 'gatehouse': 320, 'barracks': 240, 'central': 320, 'graftw': 200,
           'grafte': 240, 'trophw': 128, 'trophe': 128, 'armoury': 240, 'court': 384,
           'ssekh': 200, 'mraal': 200, 'xith': 200, 'housegal': 160, 'noblegal': 240,
           'voice': 320, 'throne': {'sw': 300, 'se': 300, 'nw': 300, 'ne': 64},
           'sanctum': 240, 'corehalls': 240, 'coolant': 240, 'grid': 240}
HIPS = {'gatehouse': 128, 'central': 128, 'graftw': 96, 'grafte': 96, 'court': 256,
        'housegal': 96, 'voice': 96, 'throne': 256, 'corehalls': 128, 'coolant': 128}
FOOTPRINTS = {rid: chamfer_rect(r['x'], r['y'], r['x']+r['w'], r['y']+r['h'], CHAMFER.get(rid, 0))
              for rid, r in R.items()}

# A short 45-degree dogleg breaks the Core Corridor's long sightline; its two door centres stay fixed.
if 'corridor' in R:
    FOOTPRINTS['corridor'] = [(2728,2140),(3493,2140),(3749,2396),(4115,2396),(4371,2140),(5136,2140),
                             (5136,2588),(4557,2588),(4301,2844),(3563,2844),(3307,2588),(2728,2588)]
    R['corridor']['h'] = 704


def connect(owner, side, other, x, y, width, height=384, door=None, event=0, z=None):
    # Coordinates are the plan's link centres; the shared wall is always 64 units thick.
    a, c = ROOMS[owner], ROOMS[other]
    z = max(a['z'], c['z']) if z is None else z
    axis = 'y' if side in ('north', 'south') else 'x'
    along = x if axis == 'y' else y
    plane = a[axis] + (a['h' if axis == 'y' else 'w'] if side in ('north', 'east') else 0)
    toward = 1 if side in ('north', 'east') else -1
    opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[side]
    for rid, wall_side in ((owner, side), (other, opposite)):
        holes.setdefault(rid, {}).setdefault(wall_side, []).append(
            (along - width / 2, along + width / 2, z - ROOMS[rid]['z'], z - ROOMS[rid]['z'] + height))
    links.append((owner, other, axis, plane, along, width, z, height, toward, door, event))


# Each link is matched to its design marker, not a second hand-placed coordinate table.
connections = [
    ('gate', 'north', 'gatehouse', 1, 'inner_gate', 102, 512, None),
    ('gatehouse', 'east', 'corelift', 2, 'corelift_gate', 109, 384, 0),
    ('gatehouse', 'north', 'central', 4, 'gatehouse', 103, 512, None),
    ('gatehouse', 'west', 'barracks', 5, 'barracks', 104, 384, None),
    ('central', 'west', 'graftw', 6, 'graftw', 110, 384, None),
    ('central', 'east', 'grafte', 7, 'grafte', 111, 384, None),
    ('graftw', 'north', 'trophw', 8, 'trophw', 112, 384, None),
    ('grafte', 'north', 'trophe', 9, 'trophe', 113, 384, None),
    ('trophe', 'north', 'armoury', 10, 'armoury', 74, 384, None),
    ('central', 'north', 'stair', 11, None, 0, 768, None),
    ('stair', 'north', 'court', 13, 'court', 105, 448, 768),
    ('court', 'west', 'ssekh', 14, 'ssekh', 0, 384, None),
    ('court', 'east', 'mraal', 15, 'mraal', 0, 384, None),
    ('court', 'east', 'xith', 16, 'xith', 0, 384, None),
    ('court', 'west', 'noblegal', 17, 'noblegal', 114, 384, None),
    ('xith', 'east', 'housegal', 18, 'housegal', 115, 384, None),
    ('court', 'north', 'liftbase', 19, 'crowns_gate', 75, 384, None),
    ('liftbase', 'north', 'voice', 21, None, 0, 448, 2304),
    ('voice', 'north', 'throne', 22, 'throne', 117, 768, None),
    ('throne', 'west', 'sanctum', 23, 'sanctum', 118, 384, None),
    ('throne', 'north', 'shaft', 24, 'shaft', 53, 384, None),
    ('corelift', 'east', 'corridor', 26, None, 0, 384, -1536),
    ('corridor', 'east', 'corehalls', 27, None, 0, 384, None),
    ('corehalls', 'east', 'service', 28, 'service', 123, 384, None),
    ('corehalls', 'north', 'grid', 30, 'grid', 124, 384, None),
    ('corehalls', 'south', 'coolant', 31, 'coolant', 125, 384, None),
    ('grid', 'east', 'padlift', 32, 'padlift', 126, 384, None),
]
for owner, side, other, index, door, event, height, z in connections:
    link = PLAN.links[index]
    connect(owner, side, other, link['x'], link['y'], link['width'], height, door, event, z)


def clip(panels, bounds):
    """Split a room's faces at its sector boundaries, preserving the shared UV frame."""
    result = []
    for panel in panels:
        points = [tuple(p) for p in panel[0]]
        for axis, edge, sign in ((0, bounds[0], 1), (0, bounds[2], -1),
                                  (1, bounds[1], 1), (1, bounds[3], -1)):
            old, points = points, []
            for a, c in zip(old, old[1:] + old[:1]):
                da, dc = sign * (a[axis] - edge), sign * (c[axis] - edge)
                if da >= -0.001: points.append(a)
                if (da >= 0) != (dc >= 0):
                    t = da / (da - dc)
                    points.append(tuple(a[k] + t * (c[k] - a[k]) for k in range(3)))
        area = [0, 0, 0]
        for a, c in zip(points, points[1:] + points[:1]):
            for axis in range(3):
                j, k = (axis + 1) % 3, (axis + 2) % 3
                area[axis] += a[j] * c[k] - a[k] * c[j]
        if sum(v*v for v in area) > 0.01:
            result.append((points, *panel[1:]))
    return result


def owner_at(rid, x, y):
    if rid == 'court':
        dx, dy = x, y - zone.COURT_RING[1]
        if math.hypot(dx, dy) < 1400: return 'court_ring'
        return 'court_' + str(court_wedge(dx, dy))
    for name in cells[rid]:
        x0, y0, x1, y1, *_ = b.bounds[name]
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01: return name
    raise ValueError((rid, x, y))


def add(rid, panels):
    if rid not in R: return
    panels = clip_to(panels, FOOTPRINTS[rid])
    if rid == 'court':
        for bounds in ((-1800,8256,0,10056),(0,8256,1800,10056),
                       (-1800,10056,0,11856),(0,10056,1800,11856)):
            for p in clip(panels, bounds):
                x, y = (sum(v[k] for v in p[0]) / len(p[0]) for k in (0, 1))
                b.rooms[owner_at(rid, x, y)] += [p]
    else:
        for cell in cells[rid]: b.rooms[cell] += clip(panels, b.bounds[cell])


def thing(rid, lo, hi, role, top=None):
    add(rid, box(lo, hi, role, top=top or role))
    obstacles.append([rid, *lo, *hi])


def trigger(name, rid, panels, event, **kwargs):
    if rid not in R: return
    if rid == 'court':
        p = panels[0][0]
        cell = owner_at(rid, sum(v[0] for v in p) / len(p), sum(v[1] for v in p) / len(p))
        b.trigger(name, cell, panels, event, **kwargs)
    else:
        for cell in cells[rid]:
            pieces = clip(panels, b.bounds[cell])
            if pieces: b.trigger(name + '_' + cell, cell, pieces, event, **kwargs)


def plate(name, rid, rect, z, event):
    # Replace the floor under the plate; no coplanar overlays.
    for cell in cells[rid]:
        updated = []
        for panel in b.rooms[cell]:
            if panel[2] == (0, 0, 1) and all(abs(v[2] - z) < .1 for v in panel[0]):
                xs, ys = [v[0] for v in panel[0]], [v[1] for v in panel[0]]
                for a0, a1, y0, y1 in kit.rect_minus(min(xs), max(xs), min(ys), max(ys),
                                                   [(rect[0], rect[2], rect[1], rect[3])]):
                    updated += clip_to(floor(a0, y0, a1, y1, z, panel[1]),
                                       [(v[0], v[1]) for v in panel[0]])
            else: updated.append(panel)
        b.rooms[cell] = updated
    trigger(name, rid, floor(*rect, z, 'hctrim' if z<0 else 'hptrim'), event, kind='pressure_plate')


def court_wedge(dx, dy):
    angle = math.atan2(dy, dx) % (2 * math.pi)
    return next(i for i, end in enumerate((math.pi / 2, math.pi, 5 * math.pi / 4,
                                         7 * math.pi / 4, 2 * math.pi)) if angle <= end + 1e-8)


def shell(rid):
    r = R[rid]
    x0, y0, x1, y1, z, h = r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'], r['z'], r['ceiling']
    if rid == 'corridor':
        cells[rid] = [rid]
        b.poly_room(rid, FOOTPRINTS[rid], z, h, [(0,320,'hcpanel'),(320,352,'hctrim'),(352,h,'hcrecess')],
                    holes={5:[(32,416,0,384)],11:[(32,416,0,384)]},
                    floor_role='hcfloor',ceiling_role='hcceiling',ambient=15)
        return
    core = r['floor'] == zone.CORE_L or rid == 'corelift'
    lower, trim, upper, ground, roof = ('hcpanel', 'hctrim', 'hcrecess', 'hcfloor', 'hcceiling') if core else (
        'hpwall', 'hptrim', 'hprelief', 'hpfloor', 'hpceil')
    if rid == 'liftbase': lower = upper = 'hplift'
    height = h - HIPS.get(rid, 0)
    cut = min(448 if core else 512, height - 32)
    bands = [(z, z + cut, lower), (z + cut, z + cut + 32, trim), (z + cut + 32, z + height, upper)]
    if rid in ('gatehouse','central','graftw','grafte','court','throne'):
        bands = [(z,z+cut-16,lower),(z+cut-16,z+cut,'hpglow')] + bands[1:]
    panels = []
    if rid not in ('stair', 'court'):
        cuts = [(-800, 800, 17400, 18600)] if rid == 'throne' else []
        for ax, bx, ay, by in kit.rect_minus(x0, x1, y0, y1, cuts):
            panels += floor(ax, ay, bx, by, z-32 if rid in ('corelift','liftbase') else z, ground)
    if rid in ('corelift','liftbase'):
        panels += rect_walls(x0,y0,x1,y1,[(z-32,z,lower)])
    if rid not in ('court', 'stair'):
        panels += (hip_ceiling(FOOTPRINTS[rid], z+height, z+h, roof) if rid in HIPS
                   else ceiling(x0, y0, x1, y1, z+h, roof))
    absolute_holes = {side: [(a, c, z+lo, z+hi) for a, c, lo, hi in hs]
                      for side, hs in holes.get(rid, {}).items()}
    walls = rect_walls(x0, y0, x1, y1, bands, absolute_holes, CHAMFER.get(rid))
    if rid == 'stair':
        # Keep 512 clear above the shallow flight, then a flat ceiling above its top landing.
        point, normal = (0, 6272, 512), (0, -768/1760, 1)
        walls = clip_to(walls, None, below=(point, normal))
        slope = [(x, y, 512+(y-6272)*768/1760) for x, y in FOOTPRINTS[rid]]
        panels += clip_to([(slope, roof, (0,0,-1))], None, below=((0,0,z+h),(0,0,1)))
        panels += [p for panel in ceiling(x0,y0,x1,y1,z+h,roof)
                   if (p := kit.clip_half(panel, point, normal))]
    panels = clip_to(panels+walls, FOOTPRINTS[rid])
    ambient = 15 if r['role'] == 'transit' else 12
    n = r['sectors']
    if rid == 'court':
        cells[rid] = ['court_ring'] + ['court_' + str(i) for i in range(5)]
        for cell in cells[rid]: b.room(cell, (x0, y0, x1, y1, z - 65, z + h), ambient)
        # Six sectors: one sixteen-sided ring and five surrounding slices.
        cx, cy, radius = zone.COURT_RING
        inner, outer = [], []
        for k in range(16):
            angle = k * math.pi / 8
            dx, dy = math.cos(angle), math.sin(angle)
            inner.append((cx + radius * dx, cy + radius * dy))
            scale = min(1800 / max(abs(dx), 1e-8), 1800 / max(abs(dy), 1e-8))
            outer.append((cx + scale * dx, cy + scale * dy))
        inner_step = [(cx + (x - cx) * 1304 / radius, cy + (y - cy) * 1304 / radius) for x, y in inner]
        b.rooms['court_ring'].append(([(x, y, z - 64) for x, y in inner_step], 'hpring', (0, 0, 1),
                                      Fit((-radius, cy - radius, z - 64), (1, 0, 0), (0, 1, 0), 2800, 2800)))
        for k in range(16):
            a, c, ia, ic, oa, oc = inner[k], inner[(k + 1) % 16], inner_step[k], inner_step[(k + 1) % 16], outer[k], outer[(k + 1) % 16]
            cell = 'court_' + str(court_wedge((a[0] + c[0]) / 2, (a[1] + c[1]) / 2 - cy))
            pa, pc = [(cx+(p[0]-cx)*1528/radius, cy+(p[1]-cy)*1528/radius) for p in (a,c)]
            rim = [([(x,y,z) for x,y in (a,pa,pc,c)], trim, (0,0,1))]
            if k % 2 == 0: b.trigger('rim_'+str(k),cell,rim,150,kind='pressure_plate')
            else: b.rooms[cell] += rim
            b.rooms[cell] += clip_to([([(x,y,z) for x,y in (pa,oa,oc,pc)],ground,(0,0,1))],
                                     FOOTPRINTS[rid])
            b.portal('court_ring', cell, [(a[0], a[1], z), (c[0], c[1], z), (c[0], c[1], z + h), (a[0], a[1], z + h)])
            prev = 'court_' + str(court_wedge((inner[k-1][0] + a[0]) / 2, (inner[k-1][1] + a[1]) / 2 - cy))
            if prev != cell: b.portal(prev, cell, [(a[0], a[1], z), (oa[0], oa[1], z), (oa[0], oa[1], z+h), (a[0], a[1], z+h)])
        b.rooms['court_ring'] += ring_flight(cx,cy,[1400,1368,1336,1304],z,-16,sides=16,phase=0,
                                               tread=trim,riser=trim)
        roof_panels = hip_ceiling(FOOTPRINTS[rid], z+height, z+h, roof)
        b.rooms['court_ring'] += clip_to(roof_panels, inner)
        for k in range(16):
            a, c, oa, oc = inner[k], inner[(k+1)%16], outer[k], outer[(k+1)%16]
            cell = 'court_'+str(court_wedge((a[0]+c[0])/2, (a[1]+c[1])/2-cy))
            b.rooms[cell] += clip_to(roof_panels, [a,oa,oc,c])
        add(rid, panels)
        return
    if rid == 'throne':
        # The dais owns a sector, four flanking strips and the approach own the other five.
        rects = [(x0,y0,x1,17200), (x0,17200,-800,18000), (-800,17200,800,18400),
                 (800,17200,x1,18000), (x0,18000,-800,y1), (800,18000,x1,y1)]
        rects[2] = (-800,17200,800,y1)
    else:
        axis = 'x' if rid in ('gatehouse','barracks','corehalls','coolant','grid','voice','sanctum') else 'y'
        rects = [(x0 + r['w'] * k/n, y0, x0 + r['w'] * (k+1)/n, y1) if axis == 'x' else
                 (x0, y0 + r['h'] * k/n, x1, y0 + r['h'] * (k+1)/n) for k in range(n)]
    cells[rid] = [rid if n == 1 else rid + '_' + str(k) for k in range(n)]
    for cell, rect in zip(cells[rid], rects):
        b.room(cell, (*rect, z-1, z+h), ambient)
        b.rooms[cell] += clip(panels, rect)
    for i, a in enumerate(rects):
        for j, c in enumerate(rects[i+1:], i+1):
            for axis in (0,1):
                other = 1-axis
                if abs(a[axis+2]-c[axis]) > .1: continue
                lo, hi = max(a[other],c[other]),min(a[other+2],c[other+2])
                if hi-lo < .1: continue
                plane = a[axis+2]
                pts = [(plane,lo,z),(plane,hi,z),(plane,hi,z+h),(plane,lo,z+h)] if axis == 0 else [
                    (lo,plane,z),(hi,plane,z),(hi,plane,z+h),(lo,plane,z+h)]
                b.portal(cells[rid][i],cells[rid][j],pts)


def core():
    z = -1536
    for x in (5700, 7500):
        for y in (1400, 2800): thing('corehalls',(x-300,y-200,z),(x+300,y+200,z+512),'hcmachine')
    for x in (5800,7800):
        for y in (-1000,400):
            add('coolant',prism(x,y,230,z,z+64,'hctrim',top='hogold'))
            add('coolant',prism(x,y,200,z+64,z+560,'htexch',top='hcmachine'))
            add('coolant',pipe((x,y,z+560),(x,936,z+560),60,'hnconduit'))
            obstacles.append(['coolant',x-230,y-230,z,x+230,y+230,z+620])
    # The documented 900-high cabinet exceeds the 640 room; keep its footprint and fit its top below the panels.
    thing('grid',(5600,5064,z),(7200,5464,z+560),'hcmachine','hctrim')
    trigger('grid_console','grid',plaque(Wall('y',5064,(0,-1,0)),6400,z+180,1600,320,'htgrid',out=4),80,cog=180)
    for rid,event,width in (('service',51,256),('padlift',52,256)):
        r=R[rid]; wall=Wall('y',r['y']+r['h'],(0,-1,0)); centre=r['x']+r['w']/2
        trigger(rid+'_exit',rid,plaque(wall,centre,z, width,384,'hcdoor',out=12),event)
    trigger('pad_call','padlift',plaque(Wall('y',4308,(0,-1,0)),8164,z+96,96,128,'hcconsole',out=8),82)
    plate('voice_core_arrival','corehalls',(8050,2072,8350,2328),z,162)
    r=R['corelift']; x,y=r['x'],r['y']
    b.door('core_platform','corelift',box((x,y,-32),(x+1000,y+1000,0),'hctrim',top='hcfloor',bottom='hcpanel'),
           22,1536,direction=(0,0,-1),open_speed=256,close_speed=256)
    for height in (z+96,96):
        trigger('core_call_'+str(height),'corelift',plaque(Wall('x',x+1000,(-1,0,0)),2364,height,96,128,'hcconsole',out=12),122)


def palace():
    # The outer leaf retracts upward; a separate fitted exit face remains behind it.
    trigger('spire_exit','gate',plaque(Wall('y',0,(0,1,0)),0,0,768,768,'hogate',out=2),50)
    b.door('spire_gate','gate',box((-384,24,0),(384,40,768),'hpdoor',top='hptrim'),1,768,
           open_speed=384,close_speed=384,event=50)
    trigger('gate_console','gatehouse',plaque(Wall('y',1680,(0,-1,0)),-900,96,128,128,'hcconsole',out=4),72)
    for x in (-900,900):
        for y in (1900,3000):
            add('gatehouse',prism(x,y,220,0,864,'hpcolumn',top='hptrim'))
            obstacles.append(['gatehouse',x-220,y-220,0,x+220,y+220,864])
    # Leave the north doorway clear under the gallery.
    thing('gatehouse',(-1600,3400,448),(-320,3664,512),'hptrim','hpfloor')
    thing('gatehouse',(320,3400,448),(1600,3664,512),'hptrim','hpfloor')
    plate('voice_gate_arrival','gatehouse',(-256,1330,256,1500),0,162)
    for y in (1264,3064):
        thing('barracks',(-3964,y,0),(-2164,y+600,400),'hokwall','hpfloor')
    for y in (2000,2850): b.decoration('hes_shelf_rack',-4300,y,0,270)
    x,y=0,4928
    thing('central',(x-400,y-400,0),(x+400,y+400,160),'hptrim','hpfloor')
    for dx in (-320,320):
        for dy in (-320,320): add('central',prism(x+dx,y+dy,55,160,640,'hpcolumn',sides=8))
    thing('central',(-350,y-350,520),(350,y+350,640),'hnmach')
    trigger('press','central',plaque(Wall('y',y-400,(0,-1,0)),0,40,192,96,'hpsigil1',out=8),15)
    for x in (-4064,-2064):
        for y in (3928,4528,5128,5728):
            thing('graftw',(x-200,y-150,0),(x+200,y+150,640),'hpgraft','hpcolumn')
            thing('graftw',(x-140,y-174,240),(x+100,y-151,500),'hcpanel','hogold')
    for k in range(6):
        y=3928+k*360
        thing('grafte',(1950,y,0),(2250,y+200,320),'hpwall','hptrim')
        thing('grafte',(4180,y+50,0),(4380,y+150,640),'hpgraft','hpcolumn')
        add('grafte',beam((1700,y+100,640),(4420,y+100,640),40,'hpcolumn'))
        # hpinlay has no master yet; narrow gold trim marks the six firing lanes.
        plate('lane_'+str(k),'grafte',(2300,y+94,4180,y+106),0,0)
    for rid,role in (('trophw','hptroph1'),('trophe','hptroph2')):
        r=R[rid]
        for x in (r['x']+500,r['x']+1400,r['x']+2300):
            trigger('niche_'+str(x),rid,plaque(Wall('y',7392,(0,-1,0)),x,128,700,320,role,out=48),12)
    thing('trophw',(-3224,6740,0),(-2904,7060,112),'hpwall','hogold')
    b.decoration('hes_founder_head',-3064,6900,112,180,event=73,cog=173)
    add('stair',floor(-600,6192,600,6272,0,'hpfloor'))
    add('stair',flight_along((0,6272),(0,8032),1200,0,32,tread='hpfloor',riser='hptrim',rise=24))
    add('stair',floor(-600,8032,600,8192,768,'hpfloor'))


def court():
    cx,cy,radius=zone.COURT_RING
    for angle in range(0,360,45):
        a=math.radians(angle)
        points=[(cx+1800*math.cos(a),cy+1800*math.sin(a),768+500),
                (cx+1100*math.cos(a),cy+1100*math.sin(a),768+1000),
                (cx+450*math.cos(a),cy+450*math.sin(a),768+1200)]
        for p,q in zip(points,points[1:]): add('court',beam(p,q,48,'hpcolumn'))
    for k in range(16):
        a,c=k*math.pi/8,(k+1)*math.pi/8
        add('court',beam((450*math.cos(a),cy+450*math.sin(a),1200),
                         (450*math.cos(c),cy+450*math.sin(c),1200),24,'hpglow'))
    for x,y,axis,normal,key in ((-1800,10056,'x',(1,0,0),'hpsigil1'),
                               (1800,10056,'x',(-1,0,0),'hpsigil2'),
                               (1800,11320,'x',(-1,0,0),'hpsigil3')):
        trigger(key,'court',plaque(Wall(axis,x,normal),y,1200,224,224,key,out=12),11)
    # Banners are thin membrane geometry and bone poles until the freestanding models exist.
    for rid in ('court','housegal'):
        r=R[rid]
        for k in range(4):
            margin=650 if rid=='court' else 300
            x=r['x']+margin+k*(r['w']-2*margin)/3
            y=r['y']+r['h']-24
            add(rid,plaque(Wall('y',y,(0,-1,0)),x,1000,160,360,'hpbanner',out=12))
            add(rid,prism(x-100,y-16,12,768,1420,'hpcolumn',sides=6,top='hptrim'))
    trigger('herald','court',box((-384,8310,768),(384,8460,800),'hptrim',top='hptrim'),154,kind='pressure_plate')
    for i,x in enumerate((3528,4328,5128),1):
        trigger('house_sigil_'+str(i),'housegal',plaque(Wall('y',9456,(0,1,0)),x,880,224,224,'hpsigil'+str(i),out=12),11)
    b.door('crowns_platform','liftbase',box((-600,11920,736),(600,13120,768),'hptrim',top='hpfloor',bottom='hpcolumn'),
           21,1536,direction=(0,0,1),open_speed=256,close_speed=256)
    for z in (864,2400):
        trigger('crowns_call_'+str(z),'liftbase',plaque(Wall('x',600,(-1,0,0)),12520,z,96,128,'hcconsole',out=12),121)


def crown():
    z=2304
    x,y=zone.VOICE_CORE
    add('voice',prism(x,y,480,z,z+96,'hptrim',top='hogold',sides=16))
    add('voice',prism(x,y,450,z+96,z+800,'hogold',top='hogold',sides=16))
    obstacles.append(['voice',x-480,y-480,z,x+480,y+480,z+800])
    trigger('voice','voice',plaque(Wall('y',y-450,(0,-1,0)),x,z+180,640,560,'hpvoice',out=4),160,cog=160)
    for dx in (-320,320):
        for rid,ya,yb in (('voice',y,15584),('throne',15648,18400)):
            panels=pipe((dx,ya,z+850),(dx,yb,z+850),60,'hnresin')
            trigger('cables_'+str(dx),rid,panels,0,cog=176)
    # A broad ceremonial flight keeps the throne raised without the old 85/170-unit ledges.
    add('throne',flight_along((0,17400),(0,18040),1600,z,16,tread='hpfloor',riser='hptrim',
                             rise=16,sides='hptrim',rail=48))
    thing('throne',(-800,18040,z),(800,18600,z+256),'hptrim','hpfloor')
    add('throne',plaque(Wall('y',18600,(0,-1,0)),0,z+256,1000,800,'hpthrone',out=80))
    for x in (-1790,1790):
        for y in (16900,18100):
            add('throne',plaque(Wall('x',x,(1 if x<0 else -1,0,0)),y,z+300,400,700,'hpglass',out=8))
    for x,y in zone.THRONE_TURRETS:
        add('throne',prism(x,y,160,z,z+32,'hpcolumn',top='hogold'))
    plate('voice_lift_top','voice',(-256,13240,256,13400),z,161)
    plate('throne_entry','throne',(-384,15700,384,15860),z,158)
    trigger('shaft_lift','shaft',plaque(Wall('y',19512,(0,-1,0)),1600,z+80,256,256,'hplift',out=12),53)
    thing('sanctum',(-4100,15850,z),(-3300,16250,z+240),'hpwall','hpfloor')


for rid in R: shell(rid)
core()
if zone.PALACE in active: palace()
if zone.COURT in active: court()
if zone.CROWN in active: crown()

chest_events={}
chest_marks=[m for m in PLAN.marks if m['kind'] in ('chest_fixed','chest_random')]
for mark,event in zip(chest_marks,(36,30,31,37,33,35,34,32)):
    if mark['floor'] not in active: continue
    model='hes_colonial_locker' if event in (31,34) else 'hes_kreegan_pod_chest' if event==30 else 'hes_palace_coffer'
    b.decoration(model,mark['x'],mark['y'],PLAN.floors[mark['floor']],180,event=event)
    chest_events[event]=event-30

# The caches are loose, fixed supplies on geometry shelves; build_d12.py places their item records.
for rid,x,y,z in (('stair',400,8092,768),('voice',800,15350,2304)):
    if rid in R:
        depth, rise = (50,32) if rid=='stair' else (100,64)
        thing(rid,(x-120,y-depth,z),(x+120,y+depth,z+rise),'hpwall','hptrim')

# Each level's dressing is added below, then the complete link and fixture pass is exported.

for owner, other, axis, plane, along, width, z, height, toward, door, event in links:
    if owner not in R or other not in R: continue
    a0, a1 = along-width/2, along+width/2
    coord = 0 if axis == 'y' else 1
    # Reveal the whole doorway once: sector splits must never add jambs down its centre.
    oc = owner_at(owner,along,plane) if axis=='y' else owner_at(owner,plane,along)
    before = len(b.rooms[oc]); far = plane+toward*64
    ground='hcfloor' if z<0 else 'hpfloor'
    if axis=='y': b.reveal(oc,a0,min(plane,far),a1,max(plane,far),z,z+height,'y',floor_role=ground)
    else: b.reveal(oc,min(plane,far),a0,max(plane,far),a1,z,z+height,'x',floor_role=ground)
    reveal = b.rooms[oc][before:]; del b.rooms[oc][before:]
    for cell in cells[owner]:
        bounds = list(b.bounds[cell])
        bounds[1-coord] -= 64; bounds[3-coord] += 64
        b.rooms[cell] += clip(reveal,bounds)
    for oc in cells[owner]:
        for tc in cells[other]:
            lo = max(a0,b.bounds[oc][coord],b.bounds[tc][coord])
            hi = min(a1,b.bounds[oc][coord+2],b.bounds[tc][coord+2])
            if hi-lo < 1: continue
            x,y = ((lo+hi)/2,plane) if axis=='y' else (plane,(lo+hi)/2)
            if owner_at(owner,x,y)!=oc: continue
            x,y = (x,plane+toward*64) if axis=='y' else (plane+toward*64,y)
            if owner_at(other,x,y)!=tc: continue
            pts = [(lo,far,z),(hi,far,z),(hi,far,z+height),(lo,far,z+height)] if axis=='y' else [
                (far,lo,z),(far,hi,z),(far,hi,z+height),(far,lo,z+height)]
            b.portal(oc,tc,pts)
    if door:
        mid=plane+toward*32
        lo,hi=((a0,mid-8,z),(a1,mid+8,z+height)) if axis=='y' else ((mid-8,a0,z),(mid+8,a1,z+height))
        x,y=(along,plane) if axis=='y' else (plane,along)
        role='hcdoor' if ROOMS[owner]['floor']==zone.CORE_L else 'hpdoor'
        panels=box(lo,hi,role,top='hptrim')
        travel=768 if door=='court' else height
        b.door(door,owner_at(owner,x,y),panels,DOORS[door],travel,event=event)

# Fixtures use the stage's radius and colour, with the planned id/cog for light switches.
for light in PLAN.lights:
    if light['floor'] not in active: continue
    light=dict(light)
    if light['id'] in ('F22','F23'):
        light['z']=min(768,max(0,math.floor((light['y']-6272)/55)+1)*24)
    if light['id']=='F54': light['x']=3100
    if light['id']=='F55': light['x']=4750
    if light['id']=='F40': light['z']=2688  # fit the beacon beneath the shaft's 2752 ceiling
    b.plan_light(light,zone.plans.FIXTURE_COG)

original_room_at=b.room_at
def room_at(x,y,z):
    if 'court' in R and -1800 <= x <= 1800 and 8256 <= y <= 11856 and 703 <= z <= 2048:
        return owner_at('court',x,y)
    return original_room_at(x,y,z)
b.room_at=room_at
checks(args.through)
expected=sum(r['sectors'] for r in R.values())
assert len(b.rooms)==expected,(len(b.rooms),expected)
assert clip(floor(0,0,10,10,0,'hpfloor'),(0,0,5,10))[0][0][1][0]==5
# The west graft hall's stores hold half the vats; the court's two residential galleries hold the rest.
pickup_groups = [
    ('hes_serum_vat', 701,
     [('graftw', x, 3900, 0) for x in (-3660,-3460,-3260,-3060,-2860,-2660,-2460)]
     + [('noblegal', x, 11600, 768) for x in (-3650,-3450,-3250,-3050)]
     + [('housegal', 3320, y, 768) for y in (9800,10040,10280)]),
    ('hes_scrap_bundle', 751, [
        ('gate',-600,900,0), ('gate',600,900,0), ('barracks',-1950,1650,0), ('barracks',-1950,3350,0),
        ('central',-1300,3900,0), ('central',1300,5900,0), ('graftw',-3600,5800,0),
        ('grafte',2800,3950,0), ('grafte',3800,5850,0), ('trophw',-4100,6500,0), ('trophe',1900,7150,0),
        ('noblegal',-2100,11550,768), ('housegal',5150,9800,768), ('sanctum',-4000,16600,2304)]),
    ('hes_colony_satchel', 765, [
        ('corehalls',6500,1180,-1536), ('corehalls',8200,3240,-1536),
        ('coolant',5400,-350,-1536), ('coolant',8180,-1220,-1536),
        ('service',8680,1800,-1536), ('padlift',7840,4170,-1536)]),
]
pickups = []
for model, first, points in pickup_groups:
    for event, (room, x, y, z) in enumerate(points, first):
        if room not in R: continue
        b.decoration(model, x, y, z, 90, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x,y,z]))
# Corner cuts must not bury doors, their panels, fixtures, chests or persistent pickups.
for name,x,y,z,*_ in b.decorations+b.lights:
    candidates=[rid for rid,r in R.items() if r['x']-1<=x<=r['x']+r['w']+1
                and r['y']-1<=y<=r['y']+r['h']+1 and r['z']-65<=z<=r['z']+r['ceiling']+1]
    assert any(kit._inside(FOOTPRINTS[rid],x,y) for rid in candidates),(name,x,y,z)
for owner,other,axis,plane,along,width,z,height,toward,*_ in links:
    for rid,at in ((owner,plane),(other,plane+toward*64)):
        if rid not in R: continue
        for a in (along-width/2,along+width/2):
            x,y=(a,at) if axis=='y' else (at,a)
            assert kit._inside(FOOTPRINTS[rid],x,y),(rid,x,y)
for name,cell,panels,*_ in b.triggers:
    rid=next(rid for rid,group in cells.items() if cell in group)
    for panel in panels:
        assert all(kit._inside(FOOTPRINTS[rid],v[0],v[1]) for v in panel[0]),(name,rid)
b.export({'room_footprints':FOOTPRINTS,'arrivals':ARRIVALS,'door_ids':{m[0]:m[3] for m in b.mechanisms},'room_bounds':b.bounds,
          'pickups':pickups,
          'room_cells':cells,'obstacles':obstacles,'completed_through':args.through,
          'decoration_positions':[[name,x,y,z] for name,x,y,z,*_ in b.decorations],
          'chest_events':chest_events, 'monster_packs':[m for m in PLAN.marks if m['kind'] in ('monster','boss')],
          'exit_arrivals':{'50':['hes_out4.odm','spire_gate'],'51':['hes_d15.blv','service_lift'],
                           '52':['hes_out4.odm','pad_lift'],'53':['hes_d13.blv','shaft_bottom']}})


sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
