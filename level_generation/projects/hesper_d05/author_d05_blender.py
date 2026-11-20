"""D5 Relay Spire: plan-owned rooms, links, marks and lights, using the shared Hesper BLV kit."""
import json
import math
import os
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
from plan import ROOT, PLAN, ROOMS, DOOR_IDS, check, zone
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
from blv_kit import Wall, Fit, banded, beam, box, ceiling, floor, flight, plaque, prism, rect_minus

check()
kit.FOLDERS.append(ROOT / 'design/kreegan_world/art/textures_k5_grafted/masters')
kit.FOLDERS.append(ROOT / 'design/kreegan_world/art/textures_k8_ship/masters')
KEYS = ('hkwall hkvein hkrib hktrim hkglow hkfloor hkflvein hkceil hkblast hkdoor hkgraft hkgraft2 hkgrlite '
        'hkwindow hkloom hkloomx hkconsol hkconsok hkglyph hkweb hkwebon hkdish hogold hobone hochitin hsrib hsfloor').split()
roles = {key: key for key in KEYS}
roles.update(floor='hkfloor', ceiling='hkceil', trim='hkrib', marker='hkconsol')
b = kit.Builder('hes_d05.blv', roles, PROJECT / 'source', role_scale={'hkwall': 2, 'hkvein': 2, 'hkfloor': 2,
                                                                    'hkceil': 2, 'hobone': 2})
# Sector splits stay on the plan lines; only the outer corners change shape.
splits = {'coolant': [2800, 4300], 'root_hall': [2300, 4100], 'root_gallery': [2300, 4100],
          'barracks': [3200], 'drill': [4000], 'looms': [3300], 'nests_n': [3400], 'nests_s': [3400]}
R, parts = {}, {}
for rid, source in ROOMS.items():
    if not source['sectors']:
        continue
    xs = [source['x'], *splits.get(rid, []), source['x'] + source['w']]
    ys = [source['y'], source['y'] + source['h']]
    zs = [source['z'], source['z'] + source['ceiling']]
    if rid == 'crown': xs.insert(1, 3200); ys.insert(1, 3200)
    if rid == 'shaft': zs.insert(1, 2048)
    parts[rid] = []
    for ix, (x0, x1) in enumerate(zip(xs, xs[1:])):
        for iy, (y0, y1) in enumerate(zip(ys, ys[1:])):
            for iz, (z0, z1) in enumerate(zip(zs, zs[1:])):
                name = rid if len(xs) == len(ys) == len(zs) == 2 else f'{rid}_{ix}_{iy}_{iz}'
                R[name] = dict(source, id=name, base=rid, x=x0, y=y0, w=x1-x0, h=y1-y0, z=z0, ceiling=z1-z0)
                parts[rid].append(name)
# The stair's well is part of its stair sector; the gallery opens into it at z=0.
R['root_stair']['h'] = 2000
R['root_stair']['ceiling'] = 1792
for name in ('ledge1','ledge2'): R[name]['ceiling'] = 1536


def owner(base, x, y, z):
    options = [name for name in parts[base] if R[name]['x']-1 <= x <= R[name]['x']+R[name]['w']+1
               and R[name]['y']-1 <= y <= R[name]['y']+R[name]['h']+1
               and R[name]['z']-1 <= z <= R[name]['z']+R[name]['ceiling']+1]
    assert options, (base, x, y, z)
    return options[0]


# Keep the door-bearing wall middles and all internal sector boundaries on the plan.
CHAMFERS = {
    'coolant': dict(nw=128, se=256, ne=256), 'root_heart': 256, 'root_door': 128, 'terminus': 256,
    'root_hall': dict(sw=256, se=256, nw=128, ne=128), 'root_gallery': dict(se=192, ne=192),
    'spine_lift': 128, 'lift1': 128, 'barracks': dict(sw=128, se=128, nw=64, ne=64),
    'armoury': dict(sw=128, se=128, ne=128), 'drill': 256, 'ledge_gate': 128,
    'looms': dict(sw=128, se=128, nw=96, ne=96), 'loom_ctrl': 128, 'weaver': 192, 'coil': 128,
    'nests_n': dict(sw=192, se=192, nw=128, ne=128), 'nests_s': 128,
    'lift2': 128, 'lift3': 128, 'roost_gate': 32, 'crown': dict(sw=320, se=320, nw=320, ne=32), 'cradle': 128,
}
HIPS = dict(terminus=128, armoury=64, loom_ctrl=64, coil=64, roost_gate=64)


holes, openings = {}, []
# Link endpoints are semantic names; all opening positions and widths come from the plan.
pairs = [('root_door','root_hall'), ('root_gallery','root_door'), ('root_hall','terminus'),
         ('spine_lift','root_hall'), ('root_gallery','spine_lift'), ('shaft','root_hall'),
         ('root_gallery','shaft'), ('root_stair','coolant'), ('coolant','root_heart'),
         ('lift1','barracks'), ('armoury','lift1'), ('armoury','drill'), ('ledge_gate','barracks'),
         ('drill','ledge_gate'), ('shaft','barracks'), ('drill','shaft'), ('ledge_gate','ledge1'),
         ('looms','ledge1'), ('lift2','looms'), ('loom_ctrl','lift2'), ('coil','looms'),
         ('weaver','coil'), ('shaft','looms'), ('weaver','shaft'), ('lift3','nests_n'),
         ('nests_s','lift3'), ('roost_gate','nests_n'), ('nests_s','roost_gate'), ('shaft','nests_n'),
         ('nests_s','shaft'), ('roost_gate','ledge2'), ('crown','ledge2'), ('crown','cradle')]
links = [(link, door) for link, door in zip(PLAN.links, DOOR_IDS) if link['kind'] not in ('exit','stairs','lift')]
assert len(pairs) == len(links)
for (a, c), (link, door) in zip(pairs, links):
    ar, cr = ROOMS[a], ROOMS[c]
    axis = 'x' if ar['x'] + ar['w'] <= cr['x'] else 'y'
    z = PLAN.floors[link['floor']]
    if c == 'cradle': z = ROOMS['cradle']['z']
    centre = link['y'] if axis == 'x' else link['x']
    plane = link[axis] - 32
    width = link['width']
    height = 640 if c == 'terminus' else 512 if a == 'shaft' or c == 'shaft' else 384
    lo, hi = centre - width/2, centre + width/2
    along_key, extent_key = ('y','h') if axis == 'x' else ('x','w')
    lo = max(lo, ar[along_key], cr[along_key])
    hi = min(hi, ar[along_key]+ar[extent_key], cr[along_key]+cr[extent_key])
    assert hi > lo, link
    aside, cside = ('east','west') if axis == 'x' else ('north','south')
    # A split across an arch yields one portal per adjacent sector, with the same continuous reveal.
    cuts = {lo, hi}
    for base in (a,c):
        for name in parts[base]:
            rr = R[name]
            cuts.update(v for v in (rr['y'],rr['y']+rr['h']) if axis == 'x' and lo < v < hi)
            cuts.update(v for v in (rr['x'],rr['x']+rr['w']) if axis == 'y' and lo < v < hi)
    for p0,p1 in zip(sorted(cuts),sorted(cuts)[1:]):
        along=(p0+p1)/2
        x,y=(plane,along) if axis == 'x' else (along,plane)
        aa=owner(a,x,y,z)
        x,y=(plane+64,along) if axis == 'x' else (along,plane+64)
        cc=owner(c,x,y,z)
        for name,side in ((aa,aside),(cc,cside)):
            holes.setdefault(name,{}).setdefault(side,[]).append((p0,p1,z-R[name]['z'],z-R[name]['z']+height))
        openings.append((aa,cc,axis,plane,p0,p1,z,height))
    if door != '—':
        name = f'door_{door}'
        aa = openings[-1][0]
        low,high = ((plane+24,lo,z),(plane+40,hi,z+height)) if axis=='x' else ((lo,plane+24,z),(hi,plane+40,z+height))
        panels=box(low,high,'hkdoor',top='hkrib',bottom='hkrib')
        b.door(name,aa,panels,int(door),400,open_speed=400,close_speed=400,event=int(door))

# Shells. Special floors/ceilings are cut below before the geometry is exported.
for name,r in R.items():
    base=r['base']; x,y,z,w,h,c=r['x'],r['y'],r['z'],r['w'],r['h'],r['ceiling']
    wall='hkvein' if base in ('coolant','root_heart') else 'hkwall'
    ambient=r['ambient']
    sides=[]
    src=ROOMS[base]
    for side,inside in [('west',x>src['x']),('east',x+w<src['x']+src['w']),
                        ('south',y>src['y']),('north',y+h<src['y']+src['h'])]:
        if inside:sides.append(side)
    cuts = CHAMFERS.get(base, {})
    cuts = cuts if isinstance(cuts, dict) else dict(sw=cuts, se=cuts, ne=cuts, nw=cuts)
    cuts = {corner: amount for corner, amount in cuts.items()
            if not any(side in sides for side in {'sw': ('south', 'west'), 'se': ('south', 'east'),
                                                  'nw': ('north', 'west'), 'ne': ('north', 'east')}[corner])}
    spring = c - HIPS.get(base, 0)
    b.box_room(name,x,y,x+w,y+h,z,spring,[(0,32,'hktrim'),(32,spring-128,wall),(spring-128,spring,'hkrib')],
               holes.get(name,{}),ambient=ambient,open_sides=sides,chamfer=cuts,
               ceiling_role=None if base in HIPS else 'ceiling')
    if base in HIPS:
        b.rooms[name] += kit.hip_ceiling(b.footprints[name], z+spring, z+c, 'hkceil')
        b.bounds[name] = (x,y,x+w,y+h,z-1,z+c)
for base,names in parts.items():
    for i,a in enumerate(names):
        for c in names[i+1:]:
            ar,cr=R[a],R[c]; x0=max(ar['x'],cr['x']);x1=min(ar['x']+ar['w'],cr['x']+cr['w'])
            y0=max(ar['y'],cr['y']);y1=min(ar['y']+ar['h'],cr['y']+cr['h'])
            z0=max(ar['z'],cr['z']);z1=min(ar['z']+ar['ceiling'],cr['z']+cr['ceiling'])
            if x0==x1 and y1>y0 and z1>z0: coords=[(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)]
            elif y0==y1 and x1>x0 and z1>z0: coords=[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)]
            elif z0==z1 and x1>x0 and y1>y0: coords=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)]
            else:continue
            b.portal(a,c,coords)
for a,c,axis,plane,lo,hi,z,h in openings:
    b.opening(a,c,axis,plane,lo,hi,z,z+h,side_role='hkrib',ceiling_role='hkrib')


def horizontal(name,z,up,cut=()):
    r=R[name]
    b.rooms[name][:]=[p for p in b.rooms[name] if not (p[2]==(0,0,1 if up else -1)
        and abs(p[0][0][2]-z)<.1 and all(r['x']<=v[0]<=r['x']+r['w']
        and r['y']<=v[1]<=r['y']+r['h'] for v in p[0]))]
    if cut:
        for x0,x1,y0,y1 in rect_minus(r['x'],r['x']+r['w'],r['y'],r['y']+r['h'],cut):
            b.rooms[name] += (floor if up else ceiling)(x0,y0,x1,y1,z,'hkfloor' if up else 'hkceil')


pit=(2750,3650,2750,3650)
for name in parts['shaft']:
    horizontal(name,R[name]['z'],True);horizontal(name,R[name]['z']+R[name]['ceiling'],False)
horizontal('root_heart',-64,False,[pit])
for name in parts['crown']:horizontal(name,4096,True,[pit])
# The shaft passes through a 64-thick slab above the Root Heart.
for side,wall,a0,a1 in [('south',Wall('y',2750,(0,1,0)),2750,3650),('north',Wall('y',3650,(0,-1,0)),2750,3650),
                        ('west',Wall('x',2750,(1,0,0)),2750,3650),('east',Wall('x',3650,(-1,0,0)),2750,3650)]:
    b.rooms['root_heart']+=wall.quad(a0,a1,-64,0,'hkrib')
b.portal('root_heart',parts['shaft'][0],[(2750,2750,0),(3650,2750,0),(3650,3650,0),(2750,3650,0)])
for name in parts['crown']:
    r=R[name];x0=max(2750,r['x']);x1=min(3650,r['x']+r['w']);y0=max(2750,r['y']);y1=min(3650,r['y']+r['h'])
    b.portal(parts['shaft'][-1],name,[(x0,y0,4096),(x1,y0,4096),(x1,y1,4096),(x0,y1,4096)])
for z in (0,1024,2048,3072):
    name=parts['shaft'][0 if z<2048 else 1]
    for wall in (Wall('x',2750,(1,0,0)),Wall('x',3650,(-1,0,0))):
        b.rooms[name]+=wall.quad(2750,3650,z+448,z+480,'hkglow',out=2)
# Rails sit at waist height; Ring 3's arches are open for flying Overseers.
for a,c,axis,plane,lo,hi,z,h in openings:
    if ('shaft' in a or 'shaft' in c) and z<3072:
        b.rooms[a]+=box((lo,plane,z+80),(hi,plane+48,z+176),'hobone',top='hobone',bottom='hobone')
for lo,hi in [((2726,2726,4096),(3674,2774,4192)),((2726,3626,4096),(3674,3674,4192)),
              ((2726,2774,4096),(2774,3626,4192)),((3626,2774,4096),(3674,3626,4192))]:
    name=owner('crown',(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,4096)
    b.rooms[name]+=box(lo,hi,'hobone',top='hobone')

# Exit face: the design's wall midline is 5832, the room's inner face is 5800.
w=Wall('x',5800,(-1,0,0));panels=plaque(w,3200,0,384,384,'hkblast',out=8)
b.trigger('blast_door','root_door',panels,50)
# All thirteen interactables come from plan marks.
for mark in (m for m in PLAN.marks if m['kind']=='interact'):
    event=int(re.search(r'event (\d+)',mark['label'])[1]);x,y=mark['x'],mark['y'];z=PLAN.floors[mark['floor']]
    if event==14:x,y=1950,4700
    if event==73:x,y=1444,3450
    if event==74:x,y=1444,2950
    if event==76:
        x,y=3300,5300
        # The console crosses the looms' sector split; each half belongs to its own bay.
        for lo,hi in ((3100,3300),(3300,3500)):
            name=owner('looms',(lo+hi)/2,5200,z)
            panels=box((lo,5100,z),(hi,5300,z+576),'hkrib',top='hobone',
                       skip=('east',) if hi==3300 else ('west',))
            panels+=plaque(Wall('y',5100,(0,-1,0)),(lo+hi)/2,z+64,hi-lo,448,'hkconsol',out=2)
            b.trigger(f'control_76_{lo}',name,panels,76)
        continue
    name=b.room_at(x,y,z+160)
    if event==10:
        b.decoration('hes_relay_post',x,y,z,180,event=10);continue
    if event==15:continue  # the actual core, below, owns this face event
    key='hkglyph' if 11<=event<=14 else 'hkweb' if event==70 else 'hkconsol'
    width,height=(512,512) if event==70 else (128,128) if 11<=event<=14 else (64,96) if 71<=event<=74 else (200,200)
    # Plan markers are on the visible face; depth extends back toward the room's nearest wall.
    r=R[name]
    choices=[(abs(x-r['x']),Wall('x',x,(1,0,0)),y),(abs(x-r['x']-r['w']),Wall('x',x,(-1,0,0)),y),
             (abs(y-r['y']),Wall('y',y,(0,1,0)),x),(abs(y-r['y']-r['h']),Wall('y',y,(0,-1,0)),x)]
    _,wall,along=min(choices,key=lambda v:v[0]);z0=z+64
    panels=plaque(wall,along,z0,width,height,key,out=12)
    b.trigger(f'control_{event}',name,panels,event,cog=170 if event==70 else 175 if event==75 else 0)
    if event==70:
        for k in range(8):
            a0=2*math.pi*k/8;a1=2*math.pi*(k+1)/8
            p0=(x+320*math.cos(a0),y-24,z0+256+320*math.sin(a0))
            p1=(x+320*math.cos(a1),y-24,z0+256+320*math.sin(a1))
            b.rooms[name]+=beam(p0,p1,64,'hogold')
        for dx in (-240,240): b.rooms[name]+=prism(x+dx,y,70,z,z+180,'hkvein',top='hkgraft')

# Roots, bays and the grafted core.
for x in range(1700,5600,900):
    name=owner('coolant',x,1400,-1024)
    b.rooms[name]+=prism(x,1400,150,-1024,-256,'hkvein')
for name in parts['coolant']:
    r=R[name]
    for y in (850,1850):b.rooms[name]+=floor(r['x'],y,r['x']+r['w'],y+300,-1000,'hkflvein')
for x in (2300,4100):
    for y in (4000,5100):
        name=owner('root_hall',x,y,0);b.rooms[name]+=prism(x,y,200,0,768,'hkvein')
core=prism(3200,3200,300,-1024,-324,'hkgrlite',top='hkdish')
b.trigger('root_core','root_heart',core,15)
for dx,dy in ((-420,0),(420,0),(0,-420),(0,420)):
    b.rooms['root_heart']+=beam((3200+dx,3200+dy,-1024),(3200+dx/2,3200+dy/2,-400),96,'hkvein')

# Fixed and random pods: plan order is the event order.
chests=[m for m in PLAN.marks if m['kind'] in ('chest_fixed','chest_random')]
for i,m in enumerate(chests):
    z=4480 if i==2 else PLAN.floors[m['floor']]
    b.decoration('hes_kreegan_pod_chest',m['x'],m['y'],z,0,event=30+i)
    # A fitted resin shell makes the small shared chest stand-in readable and keeps its click event.
    name=b.room_at(m['x'],m['y'],z)
    panels=prism(m['x'],m['y'],110,z,z+144,'hsrib' if i==2 else 'hochitin',top='hsfloor' if i==2 else 'hkrib')
    b.trigger(f'pod_{i}',name,panels,30+i)
# Native light sources: unavailable K5 fixtures use explicit stage stand-ins with the exact light spec.
for light in PLAN.lights:b.plan_light(light,zone.plans.FIXTURE_COG)

# Every placed pack is centred on its plan mark, spread without changing the pack's room.
pack_ids=[[10010]*2,[10000]*4,[10000]*5,[10010]*2,[10000]*3,[10000]*3+[10030],[10000]*3,
          [10010]*3,[10010,10011],[10010]*4,[10010]*2,[10020]*2+[10011]*2+[10030],
          [10020]+[10010]*3,[10000]*3,[10011]*2,[10030]*2+[10000]*4,[10030]*2+[10000]*3,
          [10020]*2+[10011]*2,[10011]*2,[10030]*3,[10105]]
actors=[]
for group,(mark,ids) in enumerate(zip((m for m in PLAN.marks if m['kind'] in ('monster','boss')),pack_ids),1):
    assert len(ids)==mark['count']
    z=4096 if group==19 else 2300 if group==20 else 4096 if group==21 else PLAN.floors[mark['floor']]
    for k,monster in enumerate(ids):
        x=mark['x']+(k-(len(ids)-1)/2)*140;y=mark['y']
        if group==6: y=1750
        if group==7: y=3900
        if group in (8,9): y=4700
        if group==12: y=3860
        if group==19: x=mark['x'];y=mark['y']+(k-.5)*150
        if group==21:x,y=4500,4000
        name=b.room_at(x,y,z+10)
        actors.append(dict(monster=monster,position=[round(x),round(y),z],yaw_degrees=180,group=group,
                           posted=group in (1,4,8,10,11,15,18,19),name='Lord Vhorrax' if group==21 else '',
                           sector=0))
assert len(actors)==69
# Geometry-specific details are added before export by the project module below.
exec(compile((PROJECT/'dress_d05.py').read_text(),str(PROJECT/'dress_d05.py'),'exec'))
# PICKUPS.md: wall-side supplies; event order is persistent pickup identity.
PICKUP_VATS = [
]
PICKUP_BUNDLES = [
    ('armoury', 1250, 2530, 1024),
    ('armoury', 2420, 2530, 1024),
    ('root_hall', 900, 5200, 0),
    ('root_hall', 5480, 5200, 0),
    ('root_gallery', 1700, 2480, 0),
    ('root_gallery', 5540, 2440, 0),
    ('coolant', 1500, 700, -1024),
    ('coolant', 5500, 700, -1024),
    ('root_heart', 2460, 3920, -1024),
    ('root_heart', 3940, 3920, -1024),
    ('barracks', 1160, 3900, 1024),
    ('barracks', 5200, 3900, 1024),
    ('drill', 2900, 1170, 1024),
    ('drill', 3450, 2450, 1024),
    ('looms', 5140, 5100, 2048),
    ('loom_ctrl', 1370, 2470, 2048),
    ('weaver', 5200, 1440, 2048),
    ('coil', 5200, 3500, 2048),
    ('nests_n', 1550, 3880, 3072),
    ('nests_s', 5200, 2520, 3072),
]
assert (len(PICKUP_VATS), len(PICKUP_BUNDLES)) == (0, 20)
pickups = []
for model, first, positions in (("hes_serum_vat", 701, PICKUP_VATS),
                                 ("hes_scrap_bundle", 751, PICKUP_BUNDLES)):
    for event, (room, x, y, z) in enumerate(positions, first):
        b.decoration(model, x, y, z, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x, y, z]))

# Clip only the new diagonal corners: doorway reveals must still span the 64-unit wall thickness.
# Event faces, movers and markers must remain clear rather than silently being trimmed away.
for name, footprint in b.footprints.items():
    planes = [((ax, ay, 0), (by-ay, ax-bx, 0))
              for (ax, ay), (bx, by) in zip(footprint, footprint[1:] + footprint[:1])
              if ax != bx and ay != by]
    for point, normal in planes:
        b.rooms[name] = [q for p in b.rooms[name] if (q := kit.clip_half(p, point, normal))]
        points = [v for _, room, panels, *_ in b.triggers + b.mechanisms if room == name
                  for panel in panels for v in panel[0]]
        points += [(x,y,z) for _,x,y,z,*_ in b.decorations + b.lights
                   if b.room_at(x,y,z) == name]
        for v in points:
            assert (kit.Vector(v)-kit.Vector(point)).dot(kit.Vector(normal)) <= 1, (name, v)

# The open stair well owns its ceiling, outer walls and rail pieces above the gallery floor.
# A camera on its upper landing must see a complete shell before traversing either side portal.
panels=[]
for panel in b.rooms['root_stair']:
    if all(abs(v[1]-2686)<.01 for v in panel[0]):
        panel=kit.clip_half(panel,(0,0,0),(0,0,1))
    if panel is not None:panels.append(panel)
b.rooms['root_stair']=panels
gallery=parts['root_gallery'][0]
outside=[]
for panel in b.rooms[gallery]:
    for point,normal in [((1200,0,0),(1,0,0)),((0,1760,0),(0,-1,0))]:
        distances=[(kit.Vector(v)-kit.Vector(point)).dot(kit.Vector(normal)) for v in panel[0]]
        if max(distances)<=.01:continue
        if min(distances)>=-.01:
            outside.append(panel);panel=None;break
        remainder=kit.clip_half(panel,point,tuple(-v for v in normal))
        if remainder is not None:outside.append(remainder)
        panel=kit.clip_half(panel,point,normal)
        if panel is None:break
    if panel is not None:b.rooms['root_stair'].append(panel)
b.rooms[gallery]=outside
assert any(p[2]==(0,0,-1) and all(abs(v[2]-768)<.01 for v in p[0])
           for p in b.rooms['root_stair'])

# One sector per lift well keeps carried actors and both landing floors in the same navigation volume.
for lower, upper, shaft in [('spine_lift','lift1','lift_shaft_53'), ('lift2','lift3','lift_shaft_54')]:
    names={lower,upper,shaft}
    bounds=[b.bounds[name] for name in names]
    for name in (upper,shaft):
        b.rooms[lower]+=b.rooms.pop(name)
        b.bounds.pop(name);b.ambient.pop(name)
    b.bounds[lower]=tuple((min if i in (0,1,4) else max)(bd[i] for bd in bounds) for i in range(6))
    for name in names:b.footprints.pop(name,None)
    b.triggers=[(name,lower if room in names else room,*tail) for name,room,*tail in b.triggers]
    b.mechanisms=[(name,lower if room in names else room,*tail) for name,room,*tail in b.mechanisms]
    b.portals=[(lower if a in names else a,lower if c in names else c,p)
               for a,c,p in b.portals if not (a in names and c in names)]
for actor in actors:
    actor['sector']=sorted(b.rooms).index(b.room_at(*actor['position']))+1

b.export({'pickups': pickups, 'arrivals':{'from_hes_out3':{'position':[5500,3200,0],'direction_degrees':180},
                       'web_terminus':{'position':[3200,6000,0],'direction_degrees':270}},
          'actors':actors,'door_ids':{f'door_{n}':n for n in [51,52,53,54,*range(201,221)]},
          'chest_events':{30+i:i for i in range(8)},'plan_budget':check()})

# The pulse's end lights sit in the Heart/Crown apertures but light their adjoining shaft sectors.
for k in range(1,7):
    node=f'LIGHT_P{k}'
    for room in b.metadata['rooms']:
        if node in room['source_nodes']:room['source_nodes'].remove(node)
    target='room_'+parts['shaft'][0 if k<=3 else 1]
    next(room for room in b.metadata['rooms'] if room['id']==target)['source_nodes'].append(node)
(PROJECT/'source/hes_d05.geometry.yml').write_text(json.dumps(b.metadata,indent=2)+'\n')

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
