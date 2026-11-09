"""D4 Labor Pens: plan-driven BLV source; run with Blender --background --factory-startup."""
import importlib.util
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
from blv_kit import Wall, banded, box, ceiling, floor, flight, plaque, prism, rect_minus

spec = importlib.util.spec_from_file_location('zone2', ROOT / 'design/kreegan_world/zone2/dungeons/plans_zone2.py')
zone2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone2)
PLAN = zone2.d4
assert not zone2.plans.ceiling_problems(PLAN)
assert zone2.plans.max_light_overlap(PLAN)[0] <= 4
R = {r['id']: dict(r) for r in PLAN.rooms if r['sectors']}
ORIGINAL = {r['id']: dict(r) for r in PLAN.rooms}
kit.FOLDERS += [kit.ART / 'textures_k5_grafted/masters', kit.ART / 'textures_k6_foundry/masters']
ROLE = dict(wall='hkrock', vein='hkvein', resin='hoaresin', surgery='hksurg', slag='hmslag',
            mud='hkpen', floor='hkfloor', ceiling='hkceil', rib='hkrib', trim='hktrim', cage='hkcage',
            bone='hobone', door='hkdoor', bank='hkcollar', released='hkcollof', console='hkconsol',
            hacked='hkconsok', glyph='hkglyph', rack='hmrack', hot='hmchan', cold='hmchanx', marker='hkconsol')
b = kit.Builder('hes_d04.blv', ROLE, PROJECT / 'source', role_scale={'wall': 2, 'vein': 2, 'slag': 2})
holes, openings, door_specs = {}, [], []
DOORS = dict(guard=51, sleeping=52, cell_a=53, cell_b=54, surgery=55, tamsin=56, ilse=57,
             sump=58, prisoners=59, waste_lift=60, drain=61)


def sub(base, rid, x0, y0, x1, y1):
    R[rid] = dict(ORIGINAL[base], id=rid, base=base, x=x0, y=y0, w=x1-x0, h=y1-y0)


for rid, x0, y0, x1, y1 in [('pens_sw', 1200, 1300, 2900, 2870), ('pens_se', 2900, 1300, 4600, 2870),
                            ('pens_nw', 1200, 2870, 2900, 4436), ('pens_ne', 2900, 2870, 4600, 4436)]:
    sub('pens', rid, x0, y0, x1, y1)
for base, split, axis in [('dorm', -132, 'x'), ('cella', 5864, 'x'), ('hall', -400, 'y'), ('waste', 5964, 'x')]:
    r = ORIGINAL[base]
    x0, y0, x1, y1 = r['x'], r['y'], r['x']+r['w'], r['y']+r['h']
    sub(base, base+'_a', x0, y0, split if axis == 'x' else x1, split if axis == 'y' else y1)
    sub(base, base+'_b', split if axis == 'x' else x0, split if axis == 'y' else y0, x1, y1)
    del R[base]
del R['pens']
# The shaft is one sector through both landings, as in D1.
for rid in ('wlift', 'drain'):
    R[rid].update(z=-1312, ceiling=1184)
R['stairs'].update(z=-512, ceiling=1152)


def cut(rid, side, a0, a1, z0, z1):
    holes.setdefault(rid, {}).setdefault(side, []).append((a0, a1, z0, z1))


def connect(owner, other, axis, plane, centre, width, z, height, toward=1, door=None, role='door'):
    a0, a1 = centre-width/2, centre+width/2
    side = ('east' if toward > 0 else 'west') if axis == 'x' else ('north' if toward > 0 else 'south')
    opposite = {'east': 'west', 'west': 'east', 'north': 'south', 'south': 'north'}[side]
    cut(owner, side, a0, a1, z, z+height)
    cut(other, opposite, a0, a1, z, z+height)
    openings.append((owner, other, axis, plane, a0, a1, z, z+height, toward))
    if door:
        door_specs.append((door, owner, axis, plane+toward*32, a0, a1, z, z+height, role))


links = PLAN.links


def link(label):
    return next(v for v in links if label in v['label'])


def passage(label, owner, other, axis, plane, z, height, toward=1, door=None, role='door'):
    p = link(label)
    connect(owner, other, axis, plane, p['y'] if axis == 'x' else p['x'], p['width'], z, height,
            toward, door, role)


passage('Guard Room', 'stairs', 'guard', 'x', 2300, 0, 384, -1, 'guard')
passage('Sleeping Pit', 'pens_sw', 'dorm_b', 'x', 1200, -512, 448, -1, 'sleeping', 'cage')
# The opening crosses the Pens' north/south sector split.
cut('pens_nw', 'west', 2870, 3024, -512, -64)
passage('Cell Block A', 'pens_ne', 'cella_a', 'x', 4600, -512, 448, door='cell_a', role='cage')
passage('Cell Block B', 'cella_b', 'cellb', 'x', 7064, -512, 448, door='cell_b', role='cage')
passage('Surgery\'s door', 'cellb', 'surgery', 'y', 2700, -512, 384, -1, 'surgery')
# The split line cuts the entry and south gate: each half has its own portal.
for suffix, a0, a1 in [('w', 2580, 2900), ('e', 2900, 3220)]:
    connect('stairs', 'pens_n'+suffix, 'y', 4500, (a0+a1)/2, a1-a0, -512, 640, -1)
for suffix, a0, a1 in [('w', 2516, 2900), ('e', 2900, 3284)]:
    connect('sgate', 'pens_s'+suffix, 'y', 1236, (a0+a1)/2, a1-a0, -512, 448)
passage('passage into', 'sgate', 'hall_b', 'y', 800, -512, 448, -1)
connect('hall_b', 'hstair', 'x', 1200, -200, 384, -512, 448, -1)
passage('top landing opening', 'hstair', 'collar', 'x', 1136, 0, 448)
passage('hall to the Waste', 'hall_b', 'wlift', 'x', 4600, -512, 384)
passage('drain hatch', 'drain', 'surgery', 'y', 736, -512, 384)
passage('Waste Lift\'s foot', 'wlift', 'waste_a', 'y', 0, -1280, 384, -1)
passage('drain\'s foot', 'drain', 'waste_b', 'y', 0, -1280, 384, -1)
passage('slagged panel', 'waste_b', 'sump', 'x', 7900, -1280, 384, door='sump', role='slag')
for rid, centre in [('pens_sw', 2100), ('pens_se', 3600)]:
    connect('collar', rid, 'y', 1236, centre, 600, 64, 300)
cut('stairs', 'north', 2644, 3156, 0, 512)
cut('hall_b', 'north', 1200, 4000, -64, 512)
cut('hall_b', 'west', 236, 736, -64, 512)

OPEN = {'pens_sw': ('north', 'east'), 'pens_se': ('north', 'west'),
        'pens_nw': ('south', 'east'), 'pens_ne': ('south', 'west'),
        'dorm_a': ('east',), 'dorm_b': ('west',), 'cella_a': ('east',), 'cella_b': ('west',),
        'hall_a': ('north',), 'hall_b': ('south',), 'waste_a': ('east',), 'waste_b': ('west',),
        'collar': ('south',)}

# Recessed cells occupy only the plan's free wall stretches, in their parent sector.
PEN_CELLS = [('pens_nw', 'west', 3868, 4368), ('pens_se', 'east', 1364, 1864),
             ('pens_se', 'east', 1928, 2428), ('pens_ne', 'east', 3868, 4368)]
for rid, side, a0, a1 in PEN_CELLS:
    cut(rid, side, a0, a1, -512, -128)

CHAMFER = {'guard': {'sw': 180, 'se': 180, 'nw': 120},
           'dorm_a': {'sw': 180, 'nw': 180}, 'dorm_b': {'se': 180, 'ne': 180},
           'surgery': {'sw': 200, 'se': 24, 'ne': 200, 'nw': 200}, 'hall_a': {'sw': 220, 'se': 220},
           'waste_a': {'sw': 180}, 'waste_b': {'se': 180}, 'sump': 100,
           'stairs': {'sw': 120, 'se': 120}}
HIPS = {'guard', 'dorm_a', 'dorm_b', 'surgery', 'waste_a', 'waste_b', 'sump'}
FOOTPRINTS = {}
for rid, r in R.items():
    base = r.get('base', rid)
    x0, y0, x1, y1 = r['x'], r['y'], r['x']+r['w'], r['y']+r['h']
    z, top = r['z'], r['z']+r['ceiling']
    wall = 'vein' if base in ('guard', 'hall') else 'slag' if base in ('waste', 'sump') else 'resin' if base == 'collar' else 'wall'
    floor_role = 'mud' if base in ('pens', 'dorm', 'cella', 'cellb', 'waste', 'sump') else 'floor'
    b.room(rid, (x0, y0, x1, y1, -769 if base == 'pens' else z-1, top), r['ambient'])
    if base not in ('pens', 'stairs', 'hstair', 'sgate', 'waste'):
        b.rooms[rid] += floor(x0, y0, x1, y1, z, floor_role)
    # The balcony occupies the hall's north 500; its slab's underside is the hall ceiling there.
    if rid == 'hall_b':
        for a0, a1, c0, c1 in rect_minus(x0, x1, y0, y1, [(1200, 4000, 236, 736)]):
            b.rooms[rid] += ceiling(a0, c0, a1, c1, top, 'ceiling')
        b.rooms[rid] += ceiling(1200, 236, 4000, 736, -64, 'ceiling')
        b.rooms[rid] += Wall('y', 236, (0, -1, 0)).quad(1200, 4000, -64, 0, 'rib')
        b.rooms[rid] += Wall('x', 4000, (1, 0, 0)).quad(236, 736, -64, top, 'resin')
    else:
        b.rooms[rid] += ceiling(x0, y0, x1, y1, top, 'ceiling')
    for side, wall_plane, a0, a1 in [('south', Wall('y', y0, (0, 1, 0)), x0, x1),
                                      ('north', Wall('y', y1, (0, -1, 0)), x0, x1),
                                      ('west', Wall('x', x0, (1, 0, 0)), y0, y1),
                                      ('east', Wall('x', x1, (-1, 0, 0)), y0, y1)]:
        if side in OPEN.get(rid, ()):
            continue
        role = 'surgery' if base == 'surgery' and side in ('north', 'east') else wall
        bands = [(z, z+64, 'trim'), (z+64, top-64, role), (top-64, top, 'rib')]
        b.rooms[rid] += banded(wall_plane, a0, a1, bands, holes.get(rid, {}).get(side, []))

    footprint = kit.chamfer_rect(x0, y0, x1, y1, CHAMFER.get(rid, 0))
    FOOTPRINTS[rid] = footprint
    if rid in CHAMFER:
        b.rooms[rid] = kit.clip_to(b.rooms[rid], footprint)
        b.rooms[rid] += [p for p in kit.rect_walls(x0, y0, x1, y1,
                         [(z, z+64, 'trim'), (z+64, top-64, wall), (top-64, top, 'rib')],
                         chamfer=CHAMFER[rid]) if p[2][0] and p[2][1]]
    b.footprints[rid] = footprint
    if rid in HIPS:
        b.rooms[rid] = [p for p in b.rooms[rid] if p[2][2] >= 0]
        b.rooms[rid] += kit.hip_ceiling(footprint, top, top+128, 'ceiling')
        b.bounds[rid] = (*b.bounds[rid][:5], top+128)
    if rid in ('stairs', 'hstair'):
        # The balcony's side door opens onto a flat landing before the first riser.
        # The arrival stair's roof starts at the Pens opening's 128 soffit: lower, the gap above it showed the void.
        ylo, yhi, clo, chi = (4500, 5600, 128, 640) if rid == 'stairs' else (0, 768, 0, 512)
        panels = [p for p in b.rooms[rid] if p[2][2] >= 0]
        roof = []
        for a, c, za, zc in ((y0, ylo, clo, clo), (ylo, yhi, clo, chi), (yhi, y1, chi, chi)):
            if c <= a: continue
            patch = kit.chamfer_rect(x0, a, x1, c, 0)
            slope = (zc-za)/(c-a)
            roof += kit.clip_to(panels, patch, below=((0, a, za), (0, -slope, 1)))
            roof += kit.clip_to([([(x0,a,za),(x1,a,za),(x1,c,zc),(x0,c,zc)],
                                  'ceiling',(0,slope,-1))], footprint)
        b.rooms[rid] = roof


def portal(front, back, axis, plane, a0, a1, z0, z1):
    w = Wall(axis, plane, (1, 0, 0) if axis == 'x' else (0, 1, 0))
    b.portal(front, back, [w.point(a0,z0), w.point(a1,z0), w.point(a1,z1), w.point(a0,z1)])


for f, t, axis, p, a0, a1, z0, z1 in [
        ('pens_sw','pens_se','x',2900,1300,2870,-768,512),
        ('pens_nw','pens_ne','x',2900,2870,4436,-768,512),
        ('pens_sw','pens_nw','y',2870,1200,2900,-768,512),
        ('pens_se','pens_ne','y',2870,2900,4600,-768,512),
        ('dorm_a','dorm_b','x',-132,1800,3800,-512,128),
        ('pens_nw','dorm_b','x',1168,2870,3024,-512,-64),
        ('cella_a','cella_b','x',5864,2700,3800,-512,0),
        ('hall_a','hall_b','y',-400,1200,4600,-512,512),
        ('waste_a','waste_b','x',5964,-1600,-64,-1280,-512),
        ('hall_b','collar','y',236,1200,4000,112,512)]:
    portal(f,t,axis,p,a0,a1,z0,z1)
for owner, other, axis, plane, a0, a1, z0, z1, toward in openings:
    b.opening(owner, other, axis, plane, a0, a1, z0, z1, toward=toward, side_role='rib', ceiling_role='rib')
for name, owner, axis, plane, a0, a1, z0, z1, role in door_specs:
    lo, hi = ((plane-8,a0,z0),(plane+8,a1,z1)) if axis == 'x' else ((a0,plane-8,z0),(a1,plane+8,z1))
    length = 448 if role == 'cage' else 384
    b.door(name, owner, box(lo, hi, role, top='rib', bottom='rib'), DOORS[name], length,
           direction=(0,0,-1) if name == 'sump' else (0,0,1), open_speed=192 if name == 'sump' else length/(1.5 if role == 'cage' else 1),
           close_speed=256, event=DOORS[name], flags=('secret',) if name == 'sump' else ())

# Arrival stairs, balcony stair and the exit.
b.rooms['stairs'] += kit.clip_to(floor(2300,4500,3500,4632,-512,'floor'), FOOTPRINTS['stairs'])
b.rooms['stairs'] += flight(2300,4632,3500,5400,-512,32,'north',tread='floor',riser='rib',rise=16)
b.rooms['stairs'] += floor(2300,5400,3500,5600,0,'floor')
b.rooms['hstair'] += floor(500,-400,1136,0,-512,'floor')
b.rooms['hstair'] += flight(500,0,1136,768,-512,32,'north',tread='floor',riser='rib',rise=16)
b.rooms['hstair'] += floor(500,768,1136,1236,0,'floor')
face, jambs = kit.recessed_door(Wall('y',5600,(0,-1,0)),2900,0,512,512,'door',trim='rib')
b.rooms['stairs'] += jambs
b.trigger('leave_labor_pens','stairs',face,50)

# Each pit level meets its escape route at a landing: lower ramp, middle terrace, then shallow stairs.
pit = (1800,1920,4000,3820)
inner = (1928,2048,3872,3692)
for rid in ('pens_sw','pens_se','pens_nw','pens_ne'):
    r=R[rid]; x0,y0,x1,y1=r['x'],r['y'],r['x']+r['w'],r['y']+r['h']
    for rect,z,hole in [((x0,y0,x1,y1),-512,pit),(pit,-640,inner),(inner,-768,None)]:
        ax,ay,bx,by=max(x0,rect[0]),max(y0,rect[1]),min(x1,rect[2]),min(y1,rect[3])
        if bx <= ax or by <= ay: continue
        cuts=[] if hole is None else [(hole[0],hole[2],hole[1],hole[3])]
        if rid in ('pens_nw','pens_ne'): cuts.append((2740,3060,3436,4076))
        for p0,p1,q0,q1 in rect_minus(ax,bx,ay,by,cuts): b.rooms[rid] += floor(p0,q0,p1,q1,z,'mud')
    for rect,z0,z1 in [(pit,-640,-512),(inner,-768,-640)]:
        ax,ay,bx,by=rect
        for axis,p,a0,a1,n in [('x',ax,ay,by,(1,0,0)),('x',bx,ay,by,(-1,0,0)),
                              ('y',ay,ax,bx,(0,1,0)),('y',by,ax,bx,(0,-1,0))]:
            if axis=='x' and x0 <= p <= x1:
                b.rooms[rid] += Wall(axis,p,n).quad(max(a0,y0),min(a1,y1),z0,z1,'rib')
            elif axis=='y' and y0 <= p <= y1:
                for c0,c1,d0,d1 in rect_minus(max(a0,x0),min(a1,x1),z0,z1,[(2740,3060,z0,z1)] if p==by else []):
                    b.rooms[rid] += Wall(axis,p,n).quad(c0,c1,d0,d1,'rib')
for rid,x0,x1 in [('pens_nw',2740,2900),('pens_ne',2900,3060)]:
    b.rooms[rid] += kit.clip_to(kit.ramp_along((2900,3436),(2900,3692),320,-768,-640,
                                             top='mud',skirt='rib'), FOOTPRINTS[rid])
    b.rooms[rid] += floor(x0,3692,x1,3820,-640,'mud')
    b.rooms[rid] += flight(x0,3820,x1,4076,-640,8,'north',tread='mud',riser='rib',rise=16)
    edge = 2740 if rid == 'pens_nw' else 3060
    wall = Wall('x',edge,(1,0,0) if rid == 'pens_nw' else (-1,0,0))
    b.rooms[rid] += wall.quad(3436,3692,-768,-480,'rib')
    b.rooms[rid] += wall.quad(3820,4076,-640,-480,'rib')
for rid,side,a0,a1 in PEN_CELLS:
    x0,x1=(800,1200) if side=='west' else (4600,5000)
    # These low soffits read as black wedges from the pit when they use hkceil.
    b.rooms[rid] += floor(x0,a0,x1,a1,-512,'mud') + ceiling(x0,a0,x1,a1,-128,'rib')
    b.rooms[rid] += Wall('x',x0 if side=='west' else x1,(1,0,0) if side=='west' else (-1,0,0)).quad(a0,a1,-512,-128,'wall')
    for y,n in [(a0,(0,1,0)),(a1,(0,-1,0))]: b.rooms[rid] += Wall('y',y,n).quad(x0,x1,-512,-128,'rib')
    if side=='west': b.rooms[rid] += Wall('x',1200,(1,0,0)).quad(a0,a1,-512,-128,'cage')

# Cell blocks: four 400 x 300 pens, each with an independent leaf belonging to mover 59.
leaves=[]
for k,x in enumerate((4864,5428,6064,6628)):
    rid='cella_a' if x<5864 else 'cella_b'
    for y,front in [(2700,3000),(3500,3500)]:
        b.rooms[rid] += box((x,y,-512),(x+400,y+300,-128),'wall',top='rib',skip=('north','south'))
        w=Wall('y',front,(0,1,0) if y==2700 else (0,-1,0))
        panels=w.quad(x,x+400,-512,-128,'cage')
        if y==3500: leaves += panels
        else: b.rooms[rid] += panels
b.door('prisoners','cella_a',leaves,59,384,open_speed=256)
# Tamsin's authored position is in the east cell; the other deep cells occupy the north wall.
for x in (7400,7964):
    b.rooms['cellb'] += box((x,3400,-512),(x+500,3800,-128),'wall',top='rib',skip=('south','north'))
    b.rooms['cellb'] += Wall('y',3400,(0,-1,0)).quad(x,x+500,-512,-128,'cage')
b.rooms['cellb'] += box((8428,3050,-512),(8928,3450,-128),'wall',top='rib',skip=('east','west'))
b.door('tamsin','cellb',Wall('x',8428,(-1,0,0)).quad(3050,3450,-512,-128,'cage'),56,384,open_speed=256,event=56)
b.decoration('hes_cell_lever',7300,3600,-512,0,event=72,cog=150)

# The surgery cage and restraint frame; ceiling is only 512, so the documented 900-high frame lies down.
b.trigger('ilse_cage','surgery',box((8000,1200,-512),(8600,1800,-128),'cage',skip=('west','top')),57)
b.rooms['surgery'] += floor(8000,1200,8600,1800,-128,'rib')
b.door('ilse','surgery',Wall('x',8000,(-1,0,0)).quad(1200,1800,-512,-128,'cage'),57,384,open_speed=256,event=57)
b.rooms['surgery'] += box((7600,1850,-512),(7900,2550,-352),'resin',top='surgery')
for y in (1900,2450): b.rooms['surgery'] += box((7584,y,-352),(7916,y+32,-288),'bone',top='bone')
b.trigger('surgeons_console','surgery',plaque(Wall('y',800,(0,1,0)),8600,-416,192,192,'console',out=64),73,cog=173)

# Dressing from each room's job, with separate textures for each object kind.
b.rooms['guard'] += plaque(Wall('y',4500,(0,1,0)),1436,0,1200,384,'rack',out=200)
b.trigger('tally_board','guard',plaque(Wall('x',636,(1,0,0)),5050,128,256,192,'glyph'),10)
for y in (2050,2800,3550):
    for rid,x0,x1 in [('dorm_a',-1200,-132),('dorm_b',-132,600)]:
        b.rooms[rid] += kit.clip_to(box((x0,y,-512),(x1,y+260,-384),'rib',skip=('top',)), FOOTPRINTS[rid])
        b.rooms[rid] += kit.clip_to(box((x0,y,-384),(x1,y+260,-352),'trim',top='floor',skip=('bottom',)), FOOTPRINTS[rid])
# Keep the specified footprint and height; recess the trough bed below its rim.
b.rooms['dorm_b'] += box((850,2200,-512),(1050,3400,-480),'slag',top='slag')
for x0,x1,y0,y1 in rect_minus(850,1050,2200,3400,[(874,1026,2224,3376)]):
    b.rooms['dorm_b'] += box((x0,y0,-480),(x1,y1,-384),'slag',top='slag',skip=('bottom',))
for y in (2500,3100):
    for rid,x0,x1 in [('pens_sw' if y<2870 else 'pens_nw',2200,2900),
                      ('pens_se' if y<2870 else 'pens_ne',2900,3800)]:
        b.rooms[rid] += box((x0,y-150,-704),(x1,y+150,-672),'resin',top='bone')
        for x in (x0+64,x1-64): b.rooms[rid] += box((x-24,y-100,-768),(x+24,y+100,-704),'bone',top='bone')
b.rooms['collar'] += box((1200,236,0),(4000,268,112),'resin',top='trim')
for x in (2400,3400): b.rooms['hall_b'] += prism(x,500,162,-512,-64,'resin',sides=8)
b.rooms['collar'] += box((3800,236,0),(4000,1236,512),'resin',top='rib',skip=('east',))
b.trigger('collar_bank','collar',plaque(Wall('x',3800,(-1,0,0)),700,192,256,128,'bank'),70,cog=170)
b.trigger('bank_drawer','collar',plaque(Wall('y',1236,(0,-1,0)),2000,32,256,96,'resin',out=136),33)
b.trigger('collar_sigil','pens_sw',plaque(Wall('y',1300,(0,1,0)),2900,-16,256,64,'glyph',out=8),12)
b.trigger('supply_cache','pens_sw',box((2180,1320,-512),(2420,1480,-352),'bone',top='floor'),36)
b.rooms['sgate'] += floor(2516,800,3284,900,-512,'floor')+floor(2516,1000,3284,1236,-512,'floor')
b.trigger('ghulkat_approach','sgate',floor(2516,900,3284,1000,-512,'floor'),150,kind='pressure_plate')

# Both controls are reachable on the platform; the low call buttons sit just outside the shaft.
for rid,door,width,depth,event in [('wlift',60,700,600,74),('drain',61,600,736,76)]:
    r=R[rid]; x,y=r['x'],r['y']
    panels=box((x+4,y+4,-544),(x+width-4,y+depth-4,-512),'rib',bottom='ceiling',skip=('top',))
    panels += floor(x+36,y+36,x+width-36,y+depth-36,-512,'floor')
    for x0,x1,y0,y1 in rect_minus(x+4,x+width-4,y+4,y+depth-4,[(x+36,x+width-36,y+36,y+depth-36)]):
        panels += floor(x0,y0,x1,y1,-512,'trim')
    b.door('waste_lift' if rid=='wlift' else 'drain',rid,panels,
           door,768,direction=(0,0,-1),open_speed=192,close_speed=192)
for label,rid,event in [('Waste Lift controls (top)','wlift',74),('Waste Lift controls (bottom)','waste_a',75),
                        ('Drain platform controls (top)','drain',76),('Drain platform controls (bottom)','waste_b',76)]:
    m=next(v for v in PLAN.marks if label in v['label'])
    z=PLAN.floors[m['floor']]
    b.trigger(label.lower().replace(' ','_'),rid,box((m['x']-48,m['y']-24,z),(m['x']+48,m['y']+24,z+224),
                                                'console',top='rib'),event)

trenches=[]
for k in range(3):
    x=5500+k*700; rid='waste_a' if x<5964 else 'waste_b'
    trenches.append((x-200,x+200,-650,-350))
    b.surface('slag_trench_'+str(k),rid,floor(x-200,-650,x+200,-350,-1280,'cold'),cog=160+k)
    b.rooms[rid] += box((x-200,-300,-1024),(x+200,-64,-700),'slag',top='rib',bottom='cold')
drag_marks=[(7640,7900,-1280,-1240),(7640,7900,-1160,-1120)]
for rid in ('waste_a','waste_b'):
    r=R[rid]
    for x0,x1,y0,y1 in rect_minus(r['x'],r['x']+r['w'],-1600,-64,trenches+drag_marks):
        b.rooms[rid] += kit.clip_to(floor(x0,y0,x1,y1,-1280,'mud'), FOOTPRINTS[rid])
for k,(x0,x1,y0,y1) in enumerate(drag_marks):
    b.surface('drag_marks_'+str(k),'waste_b',floor(x0,y0,x1,y1,-1280,'floor'))

for event,label,name in [(30,'Surgery:','hes_colonial_locker'),(31,'Cell Block A guard','hes_kreegan_pod_chest'),
                          (32,'Sorting Pens tally','hes_kreegan_pod_chest'),(34,'Waste Shafts pod','hes_kreegan_pod_chest'),
                          (35,'Chest C:','hes_kreegan_pod_chest')]:
    m=next(v for v in PLAN.marks if v['label'].startswith(label))
    b.decoration(name,m['x'],m['y'],PLAN.floors[m['floor']],0,event=event)
for x,y,z in [(2700,4800,-400),(1350,3400,-512),(4400,4100,-512)]: b.decoration('hes_ore_sledge',x,y,z)
for x,y in [(2200,2500),(3600,2500),(2300,3100),(3650,3100)]: b.decoration('hes_salvage_heap',x,y,-672)
for x,y in [(6450,-1300),(6800,-1350)]: b.decoration('hes_corpse_kept',x,y,-1280)
for light in PLAN.lights:
    light = dict(light)
    if light['id'] in ('F1', 'F11'): light['z'] = 36
    b.plan_light(light,zone2.plans.FIXTURE_COG)

# Packs retain the plan's centres. Fixed offsets keep bodies off furniture and out of each other's collision hulls.
# Blender exports ROOM nodes alphabetically; match the compiler's sector order in the scene and semantic record.
b.rooms=dict(sorted(b.rooms.items()))
actors=[]
pack_specs=[(20,10000,False),(22,10010,True),(40,10060,False),(21,10010,False),(42,10060,False),
            (41,10201,False),(43,10202,False),(44,10200,False),(45,10202,False),(23,10000,False),
            (30,10103,False),(33,10010,True),(24,10000,False)]


def actor(name,monster,group,x,y,z,posted=False,yaw=90,npc=0):
    rid=b.room_at(x,y,z)
    actors.append(dict(name=name,monster=monster,group=group,position=[x,y,z],posted=posted,yaw_degrees=yaw,
                       sector=list(b.rooms).index(rid)+1,npc=npc))


for m,(group,monster,posted) in zip([m for m in PLAN.marks if m['kind'] in ('monster','boss')],pack_specs):
    for k in range(m['count']):
        x=m['x']+(k%3-1)*160; y=m['y']+(k//3)*160; z=PLAN.floors[m['floor']]
        g,mid=group,monster
        if group==20: y,z=4566,-512
        if group==40: x=2500+(k%3)*300; y=2150+(k//3)*750; z=-768
        if group==42: x=-900+(k%2)*600; y=2450+(k//2)*750
        if group==41: x=4496; y=(1514,1714,2178,4118)[k]
        if group==44: x=(5064,5628,6264,6828)[k]; y=3650
        if group==30:
            if k==0: x,y=2900,-700
            else: x=1550+(k-1)*380; y=-500-(k%2)*120; g=31; mid=10201 if k<=4 else 10202; posted=True
        actor(m['label'] if group!=30 else 'Overseer Ghulkat' if k==0 else 'Ghulkat front line',mid,g,x,y,z,posted,
              yaw=180 if group==41 else 90)
for label,group in [('Tamsin',90),('Doctor Ilse',91)]:
    m=next(m for m in PLAN.marks if m['kind']=='npc' and label in m['label'])
    actor(label,10261,group,m['x'],m['y'],-512,True,180)
assert len(actors)==55
assert len(b.rooms)==22
# PICKUPS.md: wall-side supplies; event order is persistent pickup identity.
PICKUP_VATS = [
    ('guard', 850, 5450, 0),
    ('guard', 1050, 5450, 0),
    ('guard', 1250, 5450, 0),
    ('guard', 1450, 5450, 0),
    ('guard', 1650, 5450, 0),
    ('guard', 1850, 5450, 0),
    ('pens', 4100, 4320, -512),
    ('pens', 4300, 4320, -512),
    ('pens', 4500, 4320, -512),
    ('collar', 1400, 1100, 0),
    ('collar', 1600, 1100, 0),
    ('collar', 1800, 1100, 0),
]
PICKUP_BUNDLES = [
    ('guard', 850, 4860, 0),
    ('guard', 2080, 4800, 0),
    ('pens', 1330, 3100, -512),
    ('pens', 4450, 2750, -512),
    ('pens', 3700, 1420, -512),
    ('pens', 3500, 4300, -512),
    ('dorm', -1260, 2400, -512),
    ('dorm', -1260, 3200, -512),
    ('dorm', 700, 3650, -512),
    ('cella', 5120, 3100, -512),
    ('cella', 6300, 3400, -512),
    ('cellb', 8150, 2800, -512),
    ('surgery', 7250, 1000, -512),
    ('surgery', 8520, 2420, -512),
    ('waste', 6150, -1470, -1280),
    ('waste', 7100, -1470, -1280),
    ('sump', 8700, -1450, -1280),
]
assert (len(PICKUP_VATS), len(PICKUP_BUNDLES)) == (12, 17)
pickups = []
for model, first, positions in (("hes_serum_vat", 701, PICKUP_VATS),
                                 ("hes_scrap_bundle", 751, PICKUP_BUNDLES)):
    for event, (room, x, y, z) in enumerate(positions, first):
        b.decoration(model, x, y, z, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x, y, z]))

for rid in CHAMFER:
    r = R[rid]
    for side, cuts in holes.get(rid, {}).items():
        for a0, a1, _, _ in cuts:
            for a in (a0, a1):
                x, y = ((a, r['y'] + (r['h'] if side == 'north' else 0)) if side in ('north', 'south')
                        else (r['x'] + (r['w'] if side == 'east' else 0), a))
                assert kit._inside(FOOTPRINTS[rid], x, y), (rid, side, a)
    for name, x, y, z, *_ in b.decorations:
        if r['x'] <= x <= r['x']+r['w'] and r['y'] <= y <= r['y']+r['h'] and r['z'] <= z < r['z']+r['ceiling']:
            assert kit._inside(FOOTPRINTS[rid], x, y), (rid, name, x, y)
    for name, owner, panels, *_ in b.triggers:
        if owner == rid:
            for panel in panels:
                for x, y, _ in panel[0]:
                    if r['x'] <= x <= r['x']+r['w'] and r['y'] <= y <= r['y']+r['h']:
                        assert kit._inside(FOOTPRINTS[rid], x, y), (rid, name, x, y)

b.export({'pickups': pickups, 'arrivals': {'d04_pit_stairs': {'position':[2900,5400,0],'direction_degrees':270}},
          'actors':actors,'door_ids':DOORS,'chest_events':{event:event-29 for event in range(30,36)},
          'monster_packs':[m for m in PLAN.marks if m['kind'] in ('monster','boss')],
          'plan_checks':zone2.plans.budget(PLAN)})
