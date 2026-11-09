"""Author Deepwell one level at a time with --through tap|escape."""
import argparse
import math
import sys
from pathlib import Path
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
from layout import ARRIVALS, PLAN, PROJECT, ROOT, ROOMS, checks, zone
sys.path.insert(0, str(PROJECT.parent/'hesper_stage'))
import blv_kit as kit
from blv_kit import Wall, banded, beam, box, ceiling, flight, floor, pipe, plaque, prism
parser=argparse.ArgumentParser()
parser.add_argument('--through', choices=['tap','escape'], default='escape')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
kit.FOLDERS += [kit.ART/'textures_k3_transit/masters']
keys='htexch htexchot htseep htbasalt htgrate htfloor htcrown hctrim htmagma htalarm hcstripd htcore htcorehot htrubble hcconsole hcmachine hcdoor hcpanel'.split()
roles={key:key for key in keys}
roles.update(floor='htfloor',ceiling='htcrown',trim='hctrim',marker='hcconsole')
b=kit.Builder('hes_d13.blv',roles,PROJECT/'source')
R={k:r for k,r in ROOMS.items() if args.through=='escape' or r['floor']==zone.TAP}
holes,connections,cells,obstacles={},{},{},[]

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

def owner(rid,x,y):
    return next(c for c in cells[rid] if b.bounds[c][0]-.01<=x<=b.bounds[c][2]+.01
                and b.bounds[c][1]-.01<=y<=b.bounds[c][3]+.01)


def add(rid,panels):
    if rid in R:
        for cell in cells[rid]: b.rooms[cell] += clip(panels,b.bounds[cell])


def thing(rid,lo,hi,role,top=None):
    add(rid,box(lo,hi,role,top=top or role)); obstacles.append([rid,*lo,*hi])


def trigger(name,rid,panels,event,**kwargs):
    if rid in R:
        for cell in cells[rid]:
            part=clip(panels,b.bounds[cell])
            if part: b.trigger(name+'_'+cell,cell,part,event,**kwargs)


for i,a,side,c,height in [(1,'shaft','east','exch',512),(2,'exch','east','control',512),
                         (3,'control','north','debris',512),(4,'debris','north','cstair',384),
                         (5,'cstair','north','upper',384),(6,'upper','north','loop',384),
                         (7,'upper','north','loop',384),(8,'lift','east','upper',384)]:
    link=PLAN.links[i]; axis='x' if side=='east' else 'y'; along=link['y' if axis=='x' else 'x']
    z=max(ROOMS[a]['z'],ROOMS[c]['z']); width=link['width']
    plane=ROOMS[a][axis]+ROOMS[a]['w' if axis=='x' else 'h']; far=ROOMS[c][axis]
    connections[i]=(a,c,axis,plane,far,along,width,z,height)
    for rid,s in [(a,side),(c,'west' if axis=='x' else 'south')]:
        holes.setdefault(rid,{}).setdefault(s,[]).append((along-width/2,along+width/2,z,z+height))

# A flat, dark side vein provides the design's den outside the Kreegans' 2,560-unit acquisition range.
connections[9]=('debris','vein','x',8128,8192,3600,512,0,384)
for rid,side in [('debris','east'),('vein','west')]:
    holes.setdefault(rid,{}).setdefault(side,[]).append((3344,3856,0,384))

for rid,r in R.items():
    x,y,z,w,h,high=(r[k] for k in ('x','y','z','w','h','ceiling'))
    n=r['sectors']; split=[x+round(w*i/n) for i in range(n+1)]
    if rid in ('upper','loop'): split=[x,4700,x+w]
    cells[rid]=[rid] if n==1 else [rid+str(i) for i in range(n)]
    for cell,lo,hi in zip(cells[rid],split,split[1:]):
        b.room(cell,(lo,y,hi,y+h,-769 if rid=='control' else z-1,z+high),26 if rid=='vein' else 15 if r['role']=='transit' else 14)
    for left,right,edge in zip(cells[rid],cells[rid][1:],split[1:-1]):
        b.portal(left,right,[(edge,y,z-768 if rid=='control' else z),(edge,y+h,z-768 if rid=='control' else z),
                             (edge,y+h,z+high),(edge,y,z+high)])
    ground='htgrate' if rid in ('exch','control','debris') else 'htfloor'
    if rid not in ('control','cstair'): add(rid,floor(x,y,x+w,y+h,z,ground))
    add(rid,ceiling(x,y,x+w,y+h,z+high,'htbasalt' if rid=='vein' else 'htcrown'))
    low=min(512,high-64)
    bands=[(z,z+low,'htbasalt' if rid in ('shaft','vein') else 'htexch'),(z+low,z+low+32,'hctrim'),
           (z+low+32,z+high,'htseep')]
    for side,wall,lo,hi in [('west',Wall('x',x,(1,0,0)),y,y+h),('east',Wall('x',x+w,(-1,0,0)),y,y+h),
                            ('south',Wall('y',y,(0,1,0)),x,x+w),('north',Wall('y',y+h,(0,-1,0)),x,x+w)]:
        add(rid,banded(wall,lo,hi,bands,holes.get(rid,{}).get(side,[])))

for i,(a,c,axis,plane,far,along,width,z,height) in connections.items():
    if a not in R or c not in R: continue
    # The plan leaves a 464-unit link into control; its continuous reveal bridges the whole marked gap.
    lo,hi=along-width/2,along+width/2
    temp=owner(a,ROOMS[a]['x']+ROOMS[a]['w']/2,ROOMS[a]['y']+ROOMS[a]['h']/2)
    old=len(b.rooms[temp])
    if axis=='x': b.reveal(temp,plane,lo,far,hi,z,z+height,'x')
    else: b.reveal(temp,lo,plane,hi,far,z,z+height,'y')
    panels=b.rooms[temp][old:]; del b.rooms[temp][old:]
    # Reveals outside room bounds belong to the nearest bordering sector, with no clipping along the link.
    for panel in panels:
        x=sum(v[0] for v in panel[0])/len(panel[0]); y=sum(v[1] for v in panel[0])/len(panel[0])
        rr=ROOMS[a]; x=min(rr['x']+rr['w'],max(rr['x'],x)); y=min(rr['y']+rr['h'],max(rr['y'],y))
        b.rooms[owner(a,x,y)].append(panel)
    edges={lo,hi}
    if axis=='y':
        for rid in (a,c):
            for cell in cells[rid]:
                for edge in b.bounds[cell][::2][:2]:
                    if lo<edge<hi: edges.add(edge)
    edges=sorted(edges)
    for l,h in zip(edges,edges[1:]):
        mid=(l+h)/2
        ca=owner(a,plane if axis=='x' else mid,mid if axis=='x' else plane)
        cc=owner(c,far if axis=='x' else mid,mid if axis=='x' else far)
        coords=[(far,l,z),(far,h,z),(far,h,z+height),(far,l,z+height)] if axis=='x' else [
            (l,far,z),(h,far,z),(h,far,z+height),(l,far,z+height)]
        b.portal(ca,cc,coords)
    if i in (2,3,8):
        door={2:3,3:4,8:2}[i]; event={2:73,3:74,8:72}[i]
        p=(plane+far)/2 if i!=2 else far-32
        panel=box((p-8,lo,z),(p+8,hi,z+height),'hcdoor') if axis=='x' else box((lo,p-8,z),(hi,p+8,z+height),'hcdoor')
        b.door('door_'+str(door),owner(c,far if axis=='x' else along,along if axis=='x' else far),panel,
               door,height,initial='open' if door==3 else 'closed',event=event,open_speed=480 if door==2 else 512)

# All furniture is attached to the plan's room or marker, leaving the main route clear.
r=ROOMS['exch']
for y in (r['y']+150,r['y']+r['h']-450):
    thing('exch',(r['x']+600,y,0),(r['x']+2200,y+300,512),'htexch',top='hcmachine')
    add('exch',pipe((r['x']+600,y+150,544),(r['x']+2200,y+150,544),32,'hctrim'))
b.decoration('hes_corpse_colonist',r['x']+r['w']-100,r['y']+r['h']-100,0,270)
cx,cy=zone.TAP_CENTRE
inner=[]; outer=[]
for i in range(32):
    a=i*math.tau/32; dx,dy=math.cos(a),math.sin(a)
    inner.append((cx+900*dx,cy+900*dy))
    d=1400/max(abs(dx),abs(dy));outer.append((cx+d*dx,cy+d*dy))
for i in range(32):
    a,c=inner[i],inner[(i+1)%32]; oa,oc=outer[i],outer[(i+1)%32]
    add('control',[([(x,y,0) for x,y in (a,oa,oc,c)],'htgrate',(0,0,1))])
    dx,dy=(a[0]+c[0])/2-cx,(a[1]+c[1])/2-cy; length=math.hypot(dx,dy)
    add('control',[([(*a,-768),(*c,-768),(*c,0),(*a,0)],'htbasalt',(-dx/length,-dy/length,0))])
    ra,rc=[(cx+(p[0]-cx)*932/900,cy+(p[1]-cy)*932/900) for p in (a,c)]
    rail=[([(x,y,z) for x,y,z in ((*a,0),(*c,0),(*c,128),(*a,128))],'hctrim',(-dx/length,-dy/length,0)),
          ([(x,y,z) for x,y,z in ((*ra,0),(*rc,0),(*rc,128),(*ra,128))],'hctrim',(dx/length,dy/length,0)),
          ([(x,y,128) for x,y in (a,ra,rc,c)],'hctrim',(0,0,1))]
    add('control',rail)
for cell in cells['control']:
    b.surface('magma_'+cell,cell,clip([([(x,y,-768) for x,y in inner],'htmagma',(0,0,1))],b.bounds[cell]),flags=('lava',))
# The tiled master carries the small rings; three collars provide the column's silhouette.
add('control',prism(cx,cy,368,-768,1024,'htcore',sides=16,turn=0))
for z in (-512,0,512):
    add('control',prism(cx,cy,400,z,z+64,'hctrim',top='hctrim',bottom='hctrim',sides=8,turn=0))
for i,(x,y) in enumerate(zone.TAP_LOCKS):
    trigger('lock_'+str(i+1),'control',box((x-64,y-48,0),(x+64,y+48,192),'hcconsole',top='hcconsole'),80+i)
    obstacles.append(['control',x-64,y-48,0,x+64,y+48,192])
item=next(m for m in PLAN.marks if m['kind']=='item')
b.decoration('hes_shelf_rack',item['x'],item['y'],0,180)
# A reachable low shelf carries the charge independently of the decorative rack's mesh.
thing('control',(item['x']-100,item['y']-100,0),(item['x']+100,item['y']+100,64),'hcmachine')
r=ROOMS['debris'];mx,my=r['x']+r['w']/2,r['y']+r['h']/2
# One fitted gauge row at eye height; the machinery keeps its original solid bounds.
obstacles.append(['debris',mx-600,my-300,0,mx+600,my+300,640])
for wall,a0,a1 in ((Wall('x',mx-600,(-1,0,0)),my-300,my+300),
                   (Wall('x',mx+600,(1,0,0)),my-300,my+300),
                   (Wall('y',my-300,(0,-1,0)),mx-600,mx+600),
                   (Wall('y',my+300,(0,1,0)),mx-600,mx+600)):
    add('debris',banded(wall,a0,a1,[(0,96,'hcpanel'),(224,640,'hcpanel')],[]))
    fit=wall.fit(a0,a1,96,224);fit.width=128
    add('debris',wall.quad(a0,a1,96,224,'hcmachine',fit=fit))
add('debris',floor(mx-600,my-300,mx+600,my+300,640,'hcpanel'))
r=ROOMS['cstair'];add('cstair',flight(r['x'],r['y'],r['x']+r['w'],r['y']+r['h'],0,16,'north',tread='htfloor',riser='hctrim'))
for event,rid in ((84,'debris'),(85,'upper')):
    if rid not in R: continue
    m=next(m for m in PLAN.marks if m['kind']=='interact' and f'event {event}' in m['label'])
    x,y,z=m['x'],m['y'],ROOMS[rid]['z'];rect=(x-320,y-200,x+320,y+200)
    for cell in cells[rid]:
        keep=[]
        for panel in b.rooms[cell]:
            if panel[2]==(0,0,1) and all(abs(v[2]-z)<.01 for v in panel[0]):
                xs=[v[0] for v in panel[0]];ys=[v[1] for v in panel[0]]
                for x0,x1,y0,y1 in kit.rect_minus(min(xs),max(xs),min(ys),max(ys),[(rect[0],rect[2],rect[1],rect[3])]):
                    keep+=floor(x0,y0,x1,y1,z,'htfloor')
            else: keep.append(panel)
        b.rooms[cell]=keep
    trigger('collapse_plate_'+str(event),rid,floor(*rect,z,'hctrim'),event,kind='pressure_plate')
    m=next(m for m in PLAN.marks if m['kind']=='trap' and ('block 1' if event==84 else 'block 2') in m['label'])
    x,y=m['x'],m['y'];w,d=(768,128) if event==84 else (640,1200)
    b.door('debris_'+str(event-83),owner(rid,x,y),box((x-w/2,y-d/2,z),(x+w/2,y+d/2,z+640),'htrubble'),
           5 if event==84 else 6,640,initial='open',open_speed=640,close_speed=640)
    r=ROOMS[rid]
    for j in range(3): b.decoration('hes_fallen_plates',r['x']+r['w']-180,r['y']+200+j*250,z,90*j)

trigger('shaft_lift','shaft',plaque(Wall('x',0,(1,0,0)),1000,0,512,512,'hcdoor',out=4),50)
b.door('shaft_platform','shaft',box((32,744,-32),(544,1256,0),'hctrim',top='htfloor'),1,512,event=50)
if 'lift' in R: trigger('service_lift','lift',plaque(Wall('y',5592,(0,1,0)),3264,512,256,384,'hcdoor',out=4),51)
# Split all switchable materials out by cog, retaining sector membership and native tiled UVs.
for rid in R:
    r=ROOMS[rid]
    if rid not in ('shaft','lift','vein'):
        add(rid,plaque(Wall('y',r['y']+r['h'],(0,-1,0)),r['x']+r['w']*.75,
                      r['z']+r['ceiling']-48,384,24,'hcstripd',out=2))
for cell,panels in b.rooms.items():
    for role,cog in [('htexch',200),('htcore',201),('hcstripd',202)]:
        selected=[p for p in panels if p[1]==role]
        if selected: b.surface(role+'_'+cell,cell,selected,cog=cog)
        panels[:]=[p for p in panels if p[1]!=role]
for light in PLAN.lights:
    if args.through=='escape' or light['floor']==zone.TAP: b.plan_light(light,120)
report=checks(args.through)
assert len(b.rooms)==sum(r['sectors'] for r in R.values())
# Sealed stores at the shaft (five); pump-crew supplies beside the exchangers and in the debris hall (three/two).
pickup_groups = [
    ('hes_stim_canister', 701,
     [('shaft', x, 1600, 0) for x in (450,650,850,1050,1250)]
     + [('exch',1850,y,0) for y in (1400,1600,1800)]
     + [('debris',x,3900,0) for x in (7800,8000)]),
    ('hes_colony_satchel', 751, [
        ('shaft',1400,450,0), ('shaft',1350,1550,0), ('exch',2000,200,0),
        ('exch',4000,450,0), ('exch',4200,1350,0), ('debris',4800,2850,0), ('debris',7800,3700,0),
        ('upper',7000,6500,512), ('upper',4100,5750,512), ('loop',5600,7450,512),
        ('loop',7100,7450,512), ('lift',2900,6500,512)]),
]
pickups = []
for model, first, points in pickup_groups:
    for event, (room, x, y, z) in enumerate(points, first):
        if room not in R: continue
        b.decoration(model, x, y, z, 90, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x,y,z]))
b.export({'door_ids':{m[0]:m[3] for m in b.mechanisms},'arrivals':ARRIVALS,'room_bounds':b.bounds,'obstacles':obstacles,'completed_through':args.through,
          'pickups':pickups,
          'plan_checks':report,'tap_centre':zone.TAP_CENTRE,'tap_locks':zone.TAP_LOCKS,
          'exit_arrivals':{'50':['hes_d12.blv','shaft_head'],'51':['hes_out4.odm','pad_lift']}})

# Blender can hang in the host audio shutdown after writing all outputs.
import os
sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
