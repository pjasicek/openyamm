"""D15 Undercroft: plan-driven authoring with the shared Hesper indoor kit."""
import importlib.util
import math
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit as kit
from blv_kit import Wall, banded, box, ceiling, floor, flight, plaque, rect_minus

spec = importlib.util.spec_from_file_location('zone4', ROOT / 'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d15
assert not zone.plans.ceiling_problems(PLAN)
assert zone.plans.max_light_overlap(PLAN)[0] <= 4
R = {r['id']: dict(r) for r in PLAN.rooms}
for folder in ('textures_k3_transit', 'textures_k4_transitions', 'textures_k5_grafted', 'textures_k10_palace'):
    kit.FOLDERS.append(ROOT / 'design/kreegan_world/art' / folder / 'masters')
keys = ('httunnel htrib htseep htcrown htfloor htedge httrack htstripa htwater httram httramend httramrf '
        'htsign htsignon htbulk htbulkon htlock htlockon htbreach htrubble hipipe hipump hivalve '
        'hcmachine hcmachon hxcreepf hxcreepw hkwall hkglyph hpfloor').split()
b = kit.Builder('hes_d15.blv', {**{k: k for k in keys}, 'trim': 'htrib', 'marker': 'htstripa'}, PROJECT / 'source')
b.role_scale.update({k: 2 for k in ('httunnel', 'htcrown', 'hkwall', 'htrib')})
holes, openings, doors = {'landing':{'west':[(344,856,512,896)]},'lift':{'north':[(14164,14420,0,384)]}}, [], {}
# This stair must clear the party at its upper landing, which lies 512 above its plan base.
R['junramp']['ceiling'] = 1024
R['cutramp'].update(z=-512, ceiling=1280)

CHAMFERS = {'landing': 192, 'maint': 192, 'siding': 192, 'shed': 192,
            'cut': 256, 'pumpgal': 192, 'breach': 320, 'burrow': 240,
            'junction': 320, 'signal': 192, 'rootlock': 128, 'lift': 128}
HIPS = {'landing': 96, 'maint': 96, 'shed': 96, 'breach': 128, 'burrow': 96,
        'junction': 128, 'signal': 96, 'rootlock': 64, 'lift': 64}

# Link indices preserve the plan's positions and widths, including the long maintenance passage.
connections = [(1,'landing','east','servstair',1,512,384), (2,'servstair','east','linew',2,0,384),
 (3,'linew','south','maint',3,0,384), (4,'linew','north','siding',0,0,512),
 (5,'linew','east','platw',4,0,640), (6,'platw','north','shed',5,0,384),
 (9,'plate','north','cutramp',6,0,512), (10,'cutramp','north','cut',0,-512,384),
 (11,'cut','west','breach',0,-512,512), (12,'breach','west','burrow',0,-512,448),
 (13,'cut','east','pumpgal',9,-512,384), (14,'cut','north','junramp',10,-512,512),
 (15,'junramp','north','junction',11,0,512), (16,'junction','east','signal',12,0,384),
 (17,'junction','north','rootlock',13,0,384), (18,'rootlock','north','lift',14,0,384)]
for index, owner, side, other, door, z, height in connections:
    link, r, t = PLAN.links[index], R[owner], R[other]
    axis = 'x' if side in ('east','west') else 'y'
    toward = 1 if side in ('east','north') else -1
    plane = r[axis] + (r['w' if axis == 'x' else 'h'] if toward > 0 else 0)
    far = t[axis] + (t['w' if axis == 'x' else 'h'] if toward < 0 else 0)
    a = link['y' if axis == 'x' else 'x']; a0, a1 = a-link['width']/2, a+link['width']/2
    opposite = {'east':'west','west':'east','north':'south','south':'north'}[side]
    for rid, edge in ((owner,side),(other,opposite)):
        holes.setdefault(rid,{}).setdefault(edge,[]).append((a0,a1,z,z+height))
    openings.append((owner,other,axis,plane,far,a0,a1,z,z+height,door,link))


def carriage_panels(panels, bounds):
    """One window row per carriage side and one fitted end, including faces cut round a door."""
    x0,y0,z0,x1,y1,z1=bounds
    result=[]
    for points,role,normal,*extra in panels:
        if role not in ('httram','httramend'):
            result.append((points,role,normal,*extra));continue
        axis='x' if abs(normal[0])>.5 else 'y'
        wall=Wall(axis,points[0][0 if axis=='x' else 1],normal)
        a0,a1=(y0,y1) if axis=='x' else (x0,x1)
        fit=wall.fit(a0,a1,z0,z1)
        if axis=='y':fit.width/=2  # eight windows along the 2,400–2,600-unit side
        result.append((points,'httramend' if axis=='x' else 'httram',normal,fit))
    return result


def tiles(rid, x0,y0,x1,y1,z,role,roof=False):
    size=384 if rid=='linew' else 256 if rid in ('burrow','lift') else 320
    nx,ny = max(1,math.ceil((x1-x0)/size)),max(1,math.ceil((y1-y0)/size))
    for j in range(ny):
        for i in range(nx):
            b.rooms[rid] += (ceiling if roof else floor)(x0+(x1-x0)*i/nx,y0+(y1-y0)*j/ny,
                x0+(x1-x0)*(i+1)/nx,y0+(y1-y0)*(j+1)/ny,z,role)


for rid,r in R.items():
    x,y,z,w,h,height = (r[k] for k in ('x','y','z','w','h','ceiling'))
    b.room(rid,(x,y,x+w,y+h,min(z-1,-129) if rid in ('platw','plate','linew') else z-1,z+height),
           20 if rid in ('linew','siding') else 16 if r['role']=='transit' else 14)
    height -= HIPS.get(rid, 0)
    if rid not in ('servstair','cutramp','junramp','platw','plate','linew','cut'):
        tiles(rid,x,y,x+w,y+h,z,'hxcreepf' if rid in ('breach','burrow') else 'htfloor')
    if rid == 'linew':
        tiles(rid,x,y+800,x+w,y+h,0,'htfloor')
        tiles(rid,x,y,x+w,y+800,-24,'httrack')
        b.rooms[rid] += Wall('y',y+800,(0,-1,0)).quad(x,x+w,-24,0,'htedge')
    if rid in ('platw','plate'):
        tr = R['tramw' if rid == 'platw' else 'trame']
        tx,ty,tw,th = (tr[k] for k in ('x','y','w','h'));centre=tx+1300
        if rid == 'plate':
            tiles(rid,x,400,x+w*2/3,y+h,0,'htfloor')
            tiles(rid,x+w*2/3,400,x+w,y+h,0,'hxcreepf')
        else:
            tiles(rid,x,400,x+w,y+h,0,'htfloor')
        # A 24-deep bed leaves no trap beside the tram or step across the full-width platform gate.
        for a,c,d,e in rect_minus(x,x+w,y,400,[(tx-64,tx+tw+64,ty-64,ty+th+64),
                                               (centre-192,centre+192,224,400)]):
            tiles(rid,a,d,c,e,-24,'httrack')
        b.rooms[rid] += Wall('y',400,(0,-1,0)).quad(x,x+w,-24,0,'htedge')
    if rid == 'cut':
        tiles(rid,x,y,x+w,y+h,-512,'httrack')
        b.surface('cut_water',rid,floor(x,y,x+w,y+h,-384,'htwater'),flags=('untouchable',))
    if rid in HIPS:
        roof=kit.hip_ceiling(kit.chamfer_rect(x,y,x+w,y+h,CHAMFERS[rid]),z+height,z+r['ceiling'],'htcrown')
        spacing=400 if rid=='junction' else 320
        for xx in range(x,x+w,spacing):
            for yy in range(y,y+h,spacing):
                b.rooms[rid]+=kit.clip_to(roof,[(xx,yy),(min(xx+spacing,x+w),yy),
                    (min(xx+spacing,x+w),min(yy+spacing,y+h)),(xx,min(yy+spacing,y+h))])
    else:
        tiles(rid,x,y,x+w,y+h,z+height,'httramrf' if rid.startswith('tram') else 'htcrown',True)
    if rid.startswith('tram'):
        holes.setdefault(rid,{})['north']=[(x+1300-192,x+1300+192,-64,320)]
    for side,wall,a0,a1 in (
        ('south',Wall('y',y,(0,1,0)),x,x+w),('north',Wall('y',y+h,(0,-1,0)),x,x+w),
        ('west',Wall('x',x,(1,0,0)),y,y+h),('east',Wall('x',x+w,(-1,0,0)),y,y+h)):
        low = -128 if rid in ('platw','plate','linew') else z
        role = 'hkwall' if rid in ('breach','burrow','junction') else 'httunnel'
        if rid.startswith('tram'): role='httramend' if side in ('west','east') else 'httram'
        if rid == 'cut': role='htseep'
        if rid == 'junction': role='hxcreepw' if side in ('south','north') else 'httunnel'
        bands = [(low,min(z+448,z+height),role),(min(z+448,z+height),z+height,'htcrown')]
        if rid in ('breach','junction'):
            bands=[(low,z+128,'htrib'),(z+128,z+height-96,role),(z+height-96,z+height,'htrib')]
        panels=banded(wall,a0,a1,bands,holes.get(rid,{}).get(side,[]))
        if rid.startswith('tram'):
            panels=carriage_panels(panels,(x,y,z,x+w,y+h,z+height))
        b.rooms[rid] += panels

# Stair landings and 32 shallow 16-unit risers; no jumping is needed in either direction.
b.rooms['servstair'] += floor(1264,200,1452,1000,512,'htfloor')
b.rooms['servstair'] += kit.flight_along((2476,600),(1452,600),800,0,32,'htfloor','htrib',rise=16)
b.rooms['servstair'] += floor(2476,200,2664,1000,0,'htfloor')
for rid,y,direction in (('cutramp',1864,'south'),('junramp',7792,'north')):
    b.rooms[rid] += floor(13892,y,14692,y+188,0 if rid=='cutramp' else -512,'htfloor')
    b.rooms[rid] += kit.flight_along((14292,y+(188 if direction=='north' else 1212)),
        (14292,y+(1212 if direction=='north' else 188)),800,-512,32,'htfloor','htrib',rise=16)
    b.rooms[rid] += floor(13892,y+1212,14692,y+1400,-512 if rid=='cutramp' else 0,'htfloor')

# Ceilings follow the stairs; flat crowns remain above their high landings.
for rid, point, normal in [('servstair',(2476,0,512),(.5,0,1)),
                            ('cutramp',(0,2052,512),(0,.5,1)),
                            ('junramp',(0,7980,0),(0,-.5,1))]:
    r=R[rid];x,y,z,w,h,ht=(r[k] for k in ('x','y','z','w','h','ceiling'))
    roofs=[p for p in b.rooms[rid] if p[2]==(0,0,-1)]
    panels=[p for p in b.rooms[rid] if p[2]!=(0,0,-1)]
    b.rooms[rid]=kit.clip_to(panels,None,below=(point,normal))
    b.rooms[rid]+=[q for p in roofs if (q:=kit.clip_half(p,point,normal))]
    roof=[(px,py,point[2]-normal[0]*(px-point[0])-normal[1]*(py-point[1]))
          for px,py in ((x,y),(x+w,y),(x+w,y+h),(x,y+h))]
    b.rooms[rid]+=kit.clip_to([(roof,'htcrown',(0,0,-1))],None,below=((0,0,z+ht),(0,0,1)))

for owner,other,axis,plane,far,a0,a1,z0,z1,door,link in openings:
    if other=='maint':
        # Keep both door mouths straight; the service passage widens through 45-degree bends in its walls.
        passage=[(a0,plane),(a1,plane),(a1,plane-64),(a1+128,plane-192),
                 (a1+128,far+192),(a1,far+64),(a1,far),(a0,far),
                 (a0,far+64),(a0-64,far+128),(a0-64,plane-128),(a0,plane-64)]
        b.rooms[owner]+=kit.polygon_floor(passage,z0,'htfloor')+kit.polygon_ceiling(passage,z1,'htrib')
        for a,c in zip(passage,passage[1:]+passage[:1]):
            if a[1]==c[1] and a[1] in (plane,far):continue
            wall=Wall.line(a,c)
            b.rooms[owner]+=wall.quad(0,wall.length,z0,z1,'htrib')
        b.portal(owner,other,[(a0,far,z0),(a1,far,z0),(a1,far,z1),(a0,far,z1)])
    else:
        b.opening(owner,other,axis,plane,a0,a1,z0,z1,depth=abs(far-plane),toward=1 if far>plane else -1,
                  floor_role='htfloor',ceiling_role='htrib',side_role='htrib')
    if not door: continue
    mid=link[axis]
    lo,hi=((mid-8,a0,z0),(mid+8,a1,z1)) if axis=='x' else ((a0,mid-8,z0),(a1,mid+8,z1))
    travel={4:640,6:512,10:512,11:512,13:512,14:512}.get(door,384)
    seconds={4:1.5,6:1.5,10:1,11:1.5,13:1,14:2}.get(door,.8)
    event=100+door if door not in (4,6,11,14) else 0
    panels=box(lo,hi,'htbulk',top='htrib')
    for k,panel in enumerate(panels):
        if panel[2][0 if axis=='x' else 1]:
            wall=Wall(axis,panel[0][0][0 if axis=='x' else 1],panel[2])
            panels[k]=(*panel,wall.fit(a0,a1,z0,z1))
    b.door(f'door_{door}',owner,panels,door,travel,
           open_speed=travel/seconds,close_speed=travel/seconds,event=event)
    doors[f'door_{door}']=door

# One fitted breach picture wraps its aperture, raised four units above the torn wall.
wall=Wall('x',12892,(1,0,0))
fit=wall.fit(4800,5856,-512,128)
for a,c,d,e in rect_minus(4800,5856,-512,128,[(4944,5712,-512,0)]):
    b.rooms['cut'] += wall.quad(a,c,d,e,'htbreach',fit=fit,out=4)
b.rooms['cutramp'] += box((14036,3288,-128),(14548,3304,256),'htbulk',top='htrib')
# Tram bodies wrap separate interior sectors, with a 64-unit wall and a portal only at the passenger door.
for rid,platform,index,door in (('tramw','platw',7,7),('trame','plate',8,8)):
    r=R[rid];x,y,w,h=(r[k] for k in ('x','y','w','h'));centre=x+1300
    for side,wall,a0,a1 in (
        ('south',Wall('y',y-64,(0,-1,0)),x-64,x+w+64),
        ('north',Wall('y',y+h+64,(0,1,0)),x-64,x+w+64),
        ('west',Wall('x',x-64,(-1,0,0)),y-64,y+h+64),
        ('east',Wall('x',x+w+64,(1,0,0)),y-64,y+h+64)):
        panels=banded(wall,a0,a1,[(-128,512,'httramend' if side in ('west','east') else 'httram')],
                      [(centre-192,centre+192,-64,320)] if side=='north' else [])
        b.rooms[platform] += carriage_panels(panels,(x-64,y-64,-128,x+w+64,y+h+64,512))
    b.rooms[platform] += floor(x-64,y-64,x+w+64,y+h+64,512,'httramrf')
    b.opening(rid,platform,'y',y+h,centre-192,centre+192,-64,320,
              floor_role='htfloor',ceiling_role='htrib',side_role='htrib')
    b.rooms[platform] += floor(centre-192,224,centre+192,312,-32,'htedge')
    b.rooms[platform] += floor(centre-192,312,centre+192,400,0,'htedge')
    for edge in (centre-192,centre+192):
        b.rooms[platform] += Wall('x',edge,(1 if edge<centre else -1,0,0)).quad(224,400,-128,128,'htrib')
    for yy,zz in ((224,-32),(312,0)):
        b.rooms[platform] += Wall('y',yy,(0,-1,0)).quad(centre-192,centre+192,zz-32,zz,'htedge')
    b.door(f'door_{door}',rid,box((centre-192,160,-64),(centre+192,176,320),'httunnel',top='htrib'),
           door,384,direction=(1,0,0),open_speed=480,close_speed=480,initial='open' if door==8 else 'closed')
    doors[f'door_{door}']=door
    for seatx in (x+650,x+1350,x+2000):
        b.rooms[rid] += box((seatx,y,-64),(seatx+350,y+128,32),'httunnel',top='htfloor')

# Pressure plates replace their floor patches to avoid coplanar faces.
for event,rid,rect in ((60,'linew',(7208,0,7528,620)),(63,'platw',(7592,0,7912,620)),
                       (61,'plate',(14036,1480,14548,1800)),(62,'junramp',(14036,9004,14548,9192))):
    footprint=[(rect[0],rect[1]),(rect[2],rect[1]),(rect[2],rect[3]),(rect[0],rect[3])]
    surfaces=[];remaining=[]
    for panel in b.rooms[rid]:
        if panel[2][2]<=.9 or max(v[2] for v in panel[0])>0:
            remaining.append(panel);continue
        xs,ys=[v[0] for v in panel[0]],[v[1] for v in panel[0]]
        if max(xs)<=rect[0] or min(xs)>=rect[2] or max(ys)<=rect[1] or min(ys)>=rect[3]:
            remaining.append(panel);continue
        surfaces+=kit.clip_to([(panel[0],'htedge',panel[2])],footprint)
        for xa,xb,ya,yb in rect_minus(min(xs),max(xs),min(ys),max(ys),[(rect[0],rect[2],rect[1],rect[3])]):
            remaining+=kit.clip_to([panel],[(xa,ya),(xb,ya),(xb,yb),(xa,yb)])
    b.rooms[rid]=remaining
    b.trigger(f'plate_{event}',rid,surfaces,event,kind='pressure_plate')

# Collapsed tunnel mouths and structural ribs interrupt the long transit sightlines.
for rid,side in (('platw','east'),('plate','west')):
    r=R[rid];px=r['x']+r['w'] if side=='east' else r['x']
    b.rooms[rid] += plaque(Wall('x',px,(-1 if side=='east' else 1,0,0)),-100,-128,1000,640,'htrubble',out=32)
for rid in ('linew','platw','plate','cut'):
    r=R[rid];x,y,z,w,h,ht=(r[k] for k in ('x','y','z','w','h','ceiling'))
    along_y=rid=='cut'
    for p in range(1200,(h if along_y else w),1200):
        if along_y:
            b.rooms[rid] += box((x,y+p-32,z),(x+64,y+p+32,z+ht),'htrib',top='htrib')
            b.rooms[rid] += box((x+w-64,y+p-32,z),(x+w,y+p+32,z+ht),'htrib',top='htrib')
            b.rooms[rid] += box((x+64,y+p-32,z+ht-64),(x+w-64,y+p+32,z+ht),'htrib')
        else:
            # Do not obstruct a plan opening in the north/south wall.
            for side,ya,yb in (('south',y,y+64),('north',y+h-64,y+h)):
                if not any(a-64 < x+p < c+64 for a,c,_,_ in holes.get(rid,{}).get(side,[])):
                    b.rooms[rid] += box((x+p-32,ya,z),(x+p+32,yb,z+ht),'htrib',top='htrib')
            b.rooms[rid] += box((x+p-32,y+64,z+ht-64),(x+p+32,y+h-64,z+ht),'htrib')

# Derived furnishings, kept out of the north walkway and door approaches (recorded in README).
for xa,ya,xb,yb in ((3300,200,5700,800),(4900,-60,7300,580),(4100,1640,6500,2280)):
    rid='siding' if ya>1400 else 'linew'
    z0,z1=(-128 if rid=='linew' else 0),(512 if xa==3300 else 472 if rid=='linew' else 600)
    panels=carriage_panels(box((xa,ya,z0),(xb,yb,z1),'httram',top='httramrf'),(xa,ya,z0,xb,yb,z1))
    if xa==4900:
        from mathutils import Matrix,Vector
        rotate=Matrix.Rotation(math.radians(4),3,'Z');centre=Vector((6100,260,0))
        rotated=[]
        for points,role,normal,*extra in panels:
            if extra:
                fit=extra[0]
                extra=[kit.Fit(rotate@(fit.origin-centre)+centre,rotate@fit.right,rotate@fit.up,fit.width,fit.height)]
            rotated.append(([rotate@(Vector(v)-centre)+centre for v in points],role,rotate@Vector(normal),*extra))
        panels=rotated
    b.rooms[rid] += panels
for rid in ('maint','siding'):
    r=R[rid]
    for k in range(5):
        b.decoration('hes_container' if k<2 else 'hes_crate_clean',r['x']+300+k*360,r['y']+220 if rid=='maint' else r['y']+1200,r['z'])
for rid in ('linew','siding','shed','pumpgal'):
    r=R[rid];b.decoration('hes_drone_wreck',r['x']+200,r['y']+r['h']-220,r['z'])
for k in range(6):
    b.decoration('hes_creep_pod_static',10700+(k%3)*750,4300+(k//3)*2000,-512)
for k in range(20):
    b.decoration('hes_tunnel_lamp_off',3000+(k%10)*440, -200 if k<10 else 1400,280,
                 facing=0 if k<10 else 180)
# Dead pumps, conduits and drone cradles are architecture, not decoration collision cylinders.
for y in (4450,5950):
    b.rooms['pumpgal'] += box((15850,y,-512),(16200,y+350,-128),'hipump',top='hivalve')
    b.rooms['pumpgal'] += kit.prism(16000,y+170,64,-128,0,'hipipe',top='hivalve')
for k in range(6):
    x=8500+(k%3)*450;y=2150+(k//3)*500
    b.rooms['shed'] += box((x,y,0),(x+240,y+280,64),'htrib',top='htfloor')
# Three rampart runs leave every doorway clear; the western one contains the plan's Sentinel pack.
for lo,hi in (((12492,9900,0),(13400,11900,256)),((15100,11700,0),(16092,12100,256)),
              ((14800,9400,0),(16092,9800,256))):
    b.rooms['junction'] += box(lo,hi,'hkwall',top='hpfloor')

# The defensive walkways have railed approaches with no floor left beneath the ramp.
ramp_approaches=[((14424,10556),(13400,10556)),((15400,10932),(15400,11700)),
                 ((15100,10568),(15100,9800))]
ramp_bounds=[]
for (ax,ay),(bx,by) in ramp_approaches:
    xa,xb=min(ax,bx)-(256 if ax==bx else 0),max(ax,bx)+(256 if ax==bx else 0)
    ya,yb=min(ay,by)-(256 if ay==by else 0),max(ay,by)+(256 if ay==by else 0)
    ramp_bounds.append([xa,ya,xb,yb])
    panels=[]
    for panel in b.rooms['junction']:
        if panel[2]!=(0,0,1) or abs(panel[0][0][2])>.1:
            panels.append(panel);continue
        xs,ys=[v[0] for v in panel[0]],[v[1] for v in panel[0]]
        if max(xs)<=xa or min(xs)>=xb or max(ys)<=ya or min(ys)>=yb:
            panels.append(panel);continue
        # Keep doorway reveals outside the hall bounds when cutting the ramp footprint.
        for x0,x1,y0,y1 in rect_minus(min(xs),max(xs),min(ys),max(ys),[(xa,xb,ya,yb)]):
            panels+=kit.clip_to([panel],[(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
    b.rooms['junction']=panels
    b.rooms['junction']+=kit.ramp_along((ax,ay),(bx,by),512,0,256,'hpfloor','hkwall',rail=128)

# Resin buttresses grow from the hall edges; all central routes and plan openings stay clear.
dressing_solids=[]
for rid in ('breach','junction'):
    r=R[rid];z=r['z'];top=z+r['ceiling']
    ys=(r['y']+400,r['y']+r['h']-400) if rid=='breach' else (r['y']+240,r['y']+1600,r['y']+r['h']-240)
    for x in (r['x']+160,r['x']+r['w']-160):
        side='west' if x<r['x']+r['w']/2 else 'east'
        apertures=holes.get(rid,{}).get(side,[])
        for y in ys:
            for a0,a1,_,_ in apertures:
                if a0-224<y<a1+224:y=a1+224
            assert all(y+160<=a0-64 or y-160>=a1+64 for a0,a1,_,_ in apertures)
            dressing_solids.append([x-160,y-160,z,x+160,y+160,top])
            b.rooms[rid]+=box((x-160,y-160,z),(x+160,y+160,z+128),'htrib',top='htrib')
            b.rooms[rid]+=kit.prism(x,y,160,z+128,top-96,'hkwall',sides=6)
            b.rooms[rid]+=box((x-160,y-160,top-96),(x+160,y+160,top),'htrib')
# Broken ceramic panels flank the breach mouth, away from its 768-wide passage.
for y in (R['breach']['y']+200,R['breach']['y']+R['breach']['h']-420):
    x=R['breach']['x']+R['breach']['w']-700;z=R['breach']['z']
    dressing_solids.append([x,y,z,x+440,y+180,z+96])
    b.rooms['breach']+=box((x,y,z),(x+440,y+180,z+96),'httunnel',top='htbreach')
# Raised rampart rims and short returns make the three existing runs read as defensive walkways.
for lo,hi in (((12492,9900,256),(12556,11900,352)),((15100,12036,256),(16092,12100,352)),
              ((14800,9400,256),(16092,9464,352))):
    b.rooms['junction']+=box(lo,hi,'hkwall',top='hpfloor')

marks={int(m['label'].split('event ')[1].split(')')[0]):m for m in PLAN.marks
       if m['kind']=='interact' and 'event ' in m['label']}
for event,rid,key,width,height in ((10,'platw','htsign',256,240),(11,'signal','htsignon',700,240),
                                  (12,'breach','hkglyph',240,240),(75,'rootlock','htlock',384,256)):
    m=marks[event];z=R[rid]['z']
    b.trigger(f'console_{event}',rid,box((m['x']-width/2,m['y']-24,z),
                (m['x']+width/2,m['y']+24,z+height),key,top='htrib'),event,cog=200+event)
for event,rid in ((72,'tramw'),(73,'trame')):
    m=marks[event]
    b.trigger(f'tram_console_{event}',rid,box((m['x']-80,m['y']-60,-64),
              (m['x']+80,m['y']+60,144),'htsignon',top='htsignon'),event)
m=marks[70]
b.surface('breaker_cabinet','shed',box((m['x']-160,m['y']+40,0),(m['x']+160,m['y']+120,360),
                                       'hcmachine',top='htrib'),cog=270)
b.decoration('hes_line_lever',m['x'],m['y'],96,event=70,cog=370)
b.trigger('stair_warning','servstair',plaque(Wall('y',1000,(0,-1,0)),2100,400,180,128,'htsign',out=4),13)
b.trigger('lift_release','lift',plaque(Wall('y',13984,(0,1,0)),14650,96,96,128,'htlockon',out=12),76)
for event,rid,wall,centre,z,width in ((50,'landing',Wall('x',0,(1,0,0)),600,512,512),
                                    (51,'lift',Wall('y',15184,(0,-1,0)),14292,0,256)):
    face,jambs=kit.recessed_door(wall,centre,z,width,384,'htbulkon' if event==50 else 'htbulk',trim='htrib')
    b.rooms[rid] += jambs;b.trigger(f'exit_{event}',rid,face,event)
for k,m in enumerate(m for m in PLAN.marks if m['kind'].startswith('chest_')):
    b.decoration('hes_kreegan_pod_chest' if k==4 else 'hes_colonial_locker',m['x'],m['y'],PLAN.floors[m['floor']],
                  event=30+k,cog=300+k)
for k,m in enumerate(m for m in PLAN.marks if m['kind']=='item' and m['label'].startswith('Cache')):
    x,y=m['x'],m['y'];rid='plate' if k==0 else 'junction'
    b.trigger(f'supply_cache_{k}',rid,box((x-60,y-50,0),(x+60,y+50,100),'hcmachine',top='htfloor'),80+k)
# Live strips and lamps; no extra lights beyond the plan table.
for x in (3200,6200):
    b.rooms['linew'] += box((x-60,580,260),(x+60,620,300),'htstripa',top='htrib')
    b.rooms['linew'] += kit.beam((x,600,300),(x,600,640),12,'htrib')
    b.rooms['linew'] += plaque(Wall('y',1400,(0,-1,0)),x,96,700,32,'htstripa',out=4)
for ya,yb in ((3500,5150),(5500,7500)):
    b.rooms['cut'] += kit.pipe((15620,ya,-160),(15620,yb,-160),32,'hipipe')
for ya in (4000,7000):
    b.rooms['cut'] += plaque(Wall('x',15692,(-1,0,0)),ya,-260,96,96,'hivalve',out=12)
# The plan owns the map-specific fixture radii and the two cabin lamps.
lighting=PLAN.lights
for light in lighting:
    b.plan_light(light,zone.plans.FIXTURE_COG)

# Chamfer only outer corners; keep reveals spanning their original wall thickness.
for rid, cut in CHAMFERS.items():
    r=R[rid];x,y,z,w,h,ht=(r[k] for k in ('x','y','z','w','h','ceiling'))
    footprint=kit.chamfer_rect(x,y,x+w,y+h,cut)
    b.footprints[rid]=footprint
    if rid=='cut':
        b.triggers=[(name,room,kit.clip_to(panels,footprint) if name=='cut_water' else panels,*tail)
                    for name,room,panels,*tail in b.triggers]
    role='hkwall' if rid in ('breach','burrow','junction') else 'httunnel'
    b.rooms[rid]+=kit.rect_walls(x,y,x+w,y+h,[(z,z+ht-HIPS.get(rid,0),role)],
                                chamfer=cut,open_sides=('north','south','east','west'))
    for (ax,ay),(bx,by) in zip(footprint,footprint[1:]+footprint[:1]):
        if ax==bx or ay==by:continue
        point,normal=(ax,ay,0),(by-ay,ax-bx,0)
        b.rooms[rid]=[q for p in b.rooms[rid] if (q:=kit.clip_half(p,point,normal))]
        points=[v for _,room,panels,*_ in b.triggers+b.mechanisms if room==rid for p in panels for v in p[0]]
        points += [(px,py,pz) for _,px,py,pz,*_ in b.decorations+b.lights
                   if x<=px<=x+w and y<=py<=y+h and z<=pz<=z+ht]
        for v in points:
            assert (kit.Vector(v)-kit.Vector(point)).dot(kit.Vector(normal))<=1,(rid,v)

SPLITS={'linew':([3928,5128,6328],[]),'siding':([5128],[]),'platw':([8725,9859],[]),
        'plate':([13725,14859],[]),'cut':([],[4428,5528,6628]),'pumpgal':([],[5328]),
        'breach':([11228,12028],[]),'burrow':([9164],[]),'junction':([14292],[10856])}

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


def clipped(points, bounds):
    points = [tuple(p) for p in points]
    for axis, value, sign in ((0, bounds[0], 1), (0, bounds[2], -1),
                               (1, bounds[1], 1), (1, bounds[3], -1)):
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
    footprint=b.footprints.pop(rid,None)
    xs, ys = [bounds[0], *xcuts, bounds[2]], [bounds[1], *ycuts, bounds[3]]
    parts[rid] = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            name = f'{rid}_{i}_{j}'
            bound = (xs[i], ys[j], xs[i + 1], ys[j + 1], bounds[4], bounds[5])
            b.room(name, bound, ambient)
            if footprint:
                b.footprints[name]=[(v[0],v[1]) for v in clipped([(px,py,0) for px,py in footprint],bound)]
            parts[rid].append(name)
            for panel in panels:
                clip_bounds=list(bound)
                # Keep reveals beyond the room's outer walls; clip only at internal sector cuts.
                for axis,edge,outer in ((0,0,-100000),(2,2,100000),(1,1,-100000),(3,3,100000)):
                    if bound[axis]==bounds[edge]:clip_bounds[axis]=outer
                points = clipped(panel[0], clip_bounds)
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
                    # Clip only on internal split planes; reveals extend outside their owning room.
                    r, bd = R[original], list(b.bounds[part])
                    if bd[0] == r['x']: bd[0] = -100000
                    if bd[2] == r['x'] + r['w']: bd[2] = 100000
                    if bd[1] == r['y']: bd[1] = -100000
                    if bd[3] == r['y'] + r['h']: bd[3] = 100000
                    p = clipped(p, bd)
            if p:
                b.portal(f, t, p)

# Split liquid surfaces with their sectors; other controls are assigned to their owning part.
water = [t for t in b.triggers if t[0] == 'cut_water']
b.triggers = [t for t in b.triggers if t[0] != 'cut_water']
for name, rid, panels, event, kind, flags, cog in water:
    for part in parts['cut']:
        pieces = [(clipped(p[0], b.bounds[part]), *p[1:]) for p in panels]
        b.surface(name + '_' + part, part, [p for p in pieces if p[0]], flags=flags)
arrivals={}
for key,direction in (('deep_stair',0),('service_lift',270),('tram_west',0),('tram_east',0)):
    m=next(m for m in PLAN.marks if m['kind']=='start' and key in m['label'])
    arrivals[key]={'position':[m['x'],m['y'],-64 if key.startswith('tram_') else PLAN.floors[m['floor']]],
                   'direction_degrees':direction}
assert len(b.rooms)==38 and sorted(doors.values())==list(range(1,15))
# Blender's GLB nodes are name ordered; keep the semantic sector indices in that same order.
b.rooms=dict(sorted(b.rooms.items()))
pickup_groups = [
    ('hes_colony_satchel', 751, [
        ('landing', 1000, 200, 512), ('landing', 160, 1040, 512),
        ('maint', 3750, -850, 0), ('maint', 5650, -850, 0),
        ('siding', 3760, 1830, 0), ('siding', 6500, 2400, 0),
        ('linew', 7100, 1120, 0), ('platw', 7800, 1450, 0),
        ('platw', 10550, 1500, 0), ('shed', 9900, 2050, 0),
        ('plate', 12850, 1450, 0), ('plate', 15750, 650, 0),
        ('pumpgal', 17100, 4400, -512), ('pumpgal', 16400, 6000, -512),
        ('signal', 17450, 10300, 0), ('rootlock', 13850, 12720, 0),
    ]),
    ('hes_scrap_bundle', 767, [
        ('breach', 11300, 4350, -512), ('breach', 11300, 6300, -512),
        ('burrow', 8200, 4750, -512), ('burrow', 10000, 5900, -512),
    ]),
]
pickups = []
for model, first_event, points in pickup_groups:
    for event, (room, x, y, z) in enumerate(points, first_event):
        b.room_at(x,y,z)  # Fail if a pickup was swallowed by a new corner.
        b.decoration(model, x, y, z, 90, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x, y, z]))
b.export({'arrivals':arrivals,'door_ids':doors,'chest_events':{30+k:k for k in range(6)},
          'monster_packs':[m for m in PLAN.marks if m['kind']=='monster'],
          'room_bounds':b.bounds,'plan_budget':zone.plans.budget(PLAN),
          'dressing_solids':dressing_solids,'ramp_bounds':ramp_bounds,'chamfers':CHAMFERS,'review_lights':lighting,'pickups':pickups})

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
