"""Seedship: zone-3 plan geometry, native sectors, movers, placements and semantic record."""
import importlib.util
import copy
import json
import math
import os
import sys
from pathlib import Path
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
import blv_kit
from blv_kit import (Wall, box, beam, floor, ceiling, prism, plaque, rect_minus, chamfer_rect,
                     clip_to, convex_pieces, hip_ceiling, flight_along, ramp_along)
spec = importlib.util.spec_from_file_location('zone3', ROOT / 'design/kreegan_world/zone3/dungeons/plans_zone3.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d11
R = {r['id']: dict(r) for r in PLAN.rooms if r['sectors']}
blv_kit.FOLDERS += [blv_kit.ART / 'textures_k8_ship/masters', blv_kit.ART / 'textures_k10_palace/masters']
keys = 'hsrib hsmemb hsnerve hsgest hsvault hsfloor hsgrill hsceil hstrim hsglow hshull hscradle hsbrain hsbraind hsduel hsdoor hpwall hptrim hpfloor hptroph1 hptroph2 hpbanner'
roles = {k: k for k in keys.split()}
roles.update(marker='hsdoor', trim='hstrim', floor='hsfloor')
b = blv_kit.Builder('hes_d11.blv', roles, PROJECT / 'source')
holes, openings, doors = {}, [], {}
nobles = {'quarters', 'dormitory', 'trophy', 'attend', 'vchamber', 'duel'}

CHAMFER = {'gantry':128, 'breach':{'sw':128,'nw':96}, 'gest_aft':240, 'gest_fore':192,
           'pens':160, 'lower_hall':64, 'rib_port':96, 'rib_star':96, 'gal_port':96,
           'quarters':{'sw':96,'nw':96,'ne':160,'se':160},
           'dormitory':{'sw':128,'se':64,'ne':64,'nw':0}, 'trophy':128, 'attend':128,
           'vchamber':96, 'vault':128, 'cradles':{'sw':128,'nw':128},
           'core':{'sw':64,'se':192,'ne':192,'nw':64},
           'sensorium':{'sw':128,'se':128,'nw':48,'ne':48},
           'duel':{'sw':200,'se':200,'nw':32,'ne':32},
           'spine_port':{'sw':96,'se':32,'nw':96,'ne':96},
           'spine_star':{'sw':32,'se':96,'nw':96,'ne':96},
           'brain':{'sw':256,'se':256,'nw':64,'ne':64}}
HIPS = {'gantry':96,'gest_aft':128,'gest_fore':128,'pens':96,'quarters':96,'dormitory':96,
        'trophy':64,'attend':64,'vchamber':64,'cradles':96,'vault':96,'duel':128}
FOOTPRINTS = {rid:chamfer_rect(r['x'],r['y'],r['x']+r['w'],r['y']+r['h'],CHAMFER.get(rid,0))
              for rid,r in R.items()}
# The aft approach to the starboard gallery has two 45-degree shoulders, clear of its windows and doorways.
FOOTPRINTS['gal_star'] = [(2960,3864),(3600,3864),(3600,7464),(2960,7464),
                         (2960,4164),(3024,4100),(3024,3928)]


def fitted(rid, panels):
    # Blender's float32 vectors put a chamfer's diagonal wall a hair outside the footprint; clipping it exactly
    # dropped some of those walls and left black slots in the corners. Outer edges keep half a unit of slack.
    outline=FOOTPRINTS[rid];outer={e for a,c in zip(outline,outline[1:]+outline[:1]) for e in ((a,c),(c,a))}
    result=[]
    for part in convex_pieces(outline):
        for panel in panels:
            for a,c in zip(part,part[1:]+part[:1]):
                if (tuple(a),tuple(c)) in outer:
                    n=Vector((c[1]-a[1],a[0]-c[0],0)).normalized()
                    panel=blv_kit.clip_half(panel,(a[0]+n.x*.5,a[1]+n.y*.5,0),tuple(n))
                else:
                    panel=blv_kit.clip_half(panel,(a[0],a[1],0),(c[1]-a[1],a[0]-c[0],0))
                if panel is None:break
            if panel is not None:result.append(panel)
    return result


def mark(label):
    return next(m for m in PLAN.marks if label in m['label'])


def connect(owner, side, other, link, event=0, centre=None, width=None, height=400):
    l = PLAN.links[link] if isinstance(link, int) else link
    a, c = R[owner], R[other]
    axis = 'x' if side in ('east', 'west') else 'y'
    toward = 1 if side in ('east', 'north') else -1
    plane = a[axis] + (a['w' if axis == 'x' else 'h'] if toward == 1 else 0)
    centre = l['y' if axis == 'x' else 'x'] if centre is None else centre
    width = l['width'] if width is None else width
    z = l.get('z', a['z'])
    a0, a1 = centre - width / 2, centre + width / 2
    opposite = dict(east='west', west='east', north='south', south='north')[side]
    for rid, wall in ((owner, side), (other, opposite)):
        holes.setdefault(rid, {}).setdefault(wall, []).append((a0, a1, z - R[rid]['z'], z + height - R[rid]['z']))
    openings.append((owner, other, axis, plane, a0, a1, z, z + height, toward))
    if event:
        doors[event] = openings[-1]


for owner, side, other, index, event in (
 ('gantry','east','breach',1,201),('gantry','south','lower_hall',2,202),
 ('lower_hall','south','gest_aft',3,203),('breach','south','gest_aft',4,204),
 ('gantry','north','rib_port',5,205),('breach','north','rib_star',6,206),
 ('rib_port','east','brain',7,0),('rib_star','west','brain',8,0),('brain','north','gest_fore',9,207),
 ('rib_port','east','gest_fore',10,208),('rib_star','west','gest_fore',11,209),('gest_fore','north','pens',12,210),
 ('quarters','south','gal_port',16,211),('dormitory','south','gal_star',17,212),
 ('quarters','east','dormitory',18,213),('quarters','north','trophy',19,214),('dormitory','north','attend',20,215),
 ('gal_port','east','gangway',21,216),('gal_star','west','gangway',22,217),
 ('gal_port','south','cradles',23,218),('gal_star','south','cradles',24,219),
 ('dormitory','north','vchamber',25,51),('cradles','south','vault',26,52),
 ('spine_port','east','core',28,53),('spine_star','west','core',29,54),
 ('spine_port','south','duel',30,220),('spine_star','south','duel',31,221),('core','north','sensorium',32,222)):
    # The drawn chamber entrance straddles a wall; the arena doors overhang its footprint (README).
    centre = {51:1960,220:472,221:3128}.get(event)
    connect(owner,side,other,index,event,centre,256 if event in (220,221) else None)

# The galleries' open windows are true portals into the cathedral, above a solid sill.
for rid, side, z, height in [('gal_port','east',1504,700),('gal_star','west',1504,700),
                              ('spine_port','east',2784,400),('spine_star','west',2784,400)]:
    for y in (4764,5964):
        connect(rid,side,'brain',{'x':0,'y':y,'width':800,'z':z},height=height)
holes.setdefault('gantry',{})['west']=[(2544,3056,0,400)]

for rid,r in R.items():
    h=r['ceiling']-HIPS.get(rid,0);wall='hpwall' if rid in nobles else ('hsnerve' if rid=='brain' else 'hsvault' if rid=='vault' else 'hscradle' if rid=='gantry' else 'hsrib')
    trim='hptrim' if rid in nobles else 'hstrim'
    bands=[(0,h-128,wall),(h-128,h-96,trim),(h-96,h,'hsmemb')]
    if r['role']=='transit':bands=[(0,256,wall),(256,288,'hsglow'),(288,h-128,wall),(h-128,h-96,trim),(h-96,h,'hsmemb')]
    if rid=='gantry':
        bands=[(0,96,'hsmemb'),(96,128,trim),(128,384,wall),(384,416,trim),(416,h-32,'hsmemb'),(h-32,h,trim)]
    if rid in ('rib_port','rib_star'):
        bands=[(0,96,'hsmemb'),(96,128,trim),(128,256,wall),(256,288,'hsglow'),(288,640,wall),
               (640,672,trim),(672,h-32,'hsmemb'),(h-32,h,trim)]
    role='hpfloor' if rid in nobles else 'hsgrill' if rid in ('brain','gangway') else 'hsfloor'
    roof='hsmemb' if rid in ('gantry','rib_port','rib_star') else 'hsceil'
    amb=15 if r['role']=='transit' else 10 if rid=='brain' else 12
    if rid=='gal_star':
        cut={}
        for side,edge,origin in [('south',0,2960),('north',2,3600),('west',3,7464)]:
            cut[edge]=[(a-origin,c-origin,lo,hi) if side=='south' else (origin-c,origin-a,lo,hi)
                       for a,c,lo,hi in holes.get(rid,{}).get(side,[])]
        b.poly_room(rid,FOOTPRINTS[rid],r['z'],h,bands,cut,floor_role=role,ceiling_role=roof,ambient=amb)
    else:
        b.box_room(rid,r['x'],r['y'],r['x']+r['w'],r['y']+r['h'],r['z'],h,bands,holes.get(rid),
                   floor_role=role,ceiling_role=None if rid in HIPS else roof,ambient=amb,
                   open_sides=('south','north','east','west') if rid=='gangway' else (),chamfer=CHAMFER.get(rid))
    if rid in HIPS:
        b.rooms[rid]+=hip_ceiling(FOOTPRINTS[rid],r['z']+h,r['z']+r['ceiling'],roof)
        b.bounds[rid]=(*b.bounds[rid][:5],r['z']+r['ceiling'])

# Cuts in structural slabs, not invisible ramps through intact ceilings.
slab_cuts={}
def slab(rid,up,cuts,role):
    normal=(0,0,1 if up else -1)
    r=R[rid];z=r['z'] if up else r['z']+r['ceiling']
    slab_cuts.setdefault((rid,up),[]).extend(cuts)
    if not up and rid in HIPS:
        # A roof opening cuts the hipped panels too, keeping their original slopes outside the shaft.
        panels=[p for p in b.rooms[rid] if p[2][2]<0]
        b.rooms[rid]=[p for p in b.rooms[rid] if p[2][2]>=0]
        for x0,x1,y0,y1 in rect_minus(r['x'],r['x']+r['w'],r['y'],r['y']+r['h'],cuts):
            b.rooms[rid]+=clip_to(panels,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
    else:
        b.rooms[rid]=[p for p in b.rooms[rid] if not(p[2]==normal and all(abs(v[2]-z)<.01 for v in p[0]))]
        for x0,x1,y0,y1 in rect_minus(r['x'],r['x']+r['w'],r['y'],r['y']+r['h'],slab_cuts[rid,up]):
            b.rooms[rid]+=fitted(rid,(floor if up else ceiling)(x0,y0,x1,y1,z,role))

shafts,shaft_portals=[],{}
for lower,upper,cut in [('rib_port','quarters',(120,520,8500,9500)),('rib_star','dormitory',(3080,3480,8500,9500)),
                        ('quarters','core',(800,1200,7800,8560)),('vault','duel',(1900,2900,1250,1650)),
                        ('breach','cradles',(3000,3600,3000,3800))]:
    roof='hsmemb' if lower in ('rib_port','rib_star') else 'hsceil'
    slab(lower,False,[cut],roof);slab(upper,True,[cut],'hpfloor' if upper in nobles else 'hsfloor')
    x0,x1,y0,y1=cut;z0=R[lower]['z']+R[lower]['ceiling'];z1=R[upper]['z']
    z2=R[upper]['z']+R[upper]['ceiling']
    b.bounds[lower]=(*b.bounds[lower][:5],z2)
    # The shaft owns the upper room's actual roof and hull walls within its aperture.
    aperture=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    shell=b.rooms[upper]
    b.rooms[lower]+=clip_to(shell,aperture)
    b.rooms[upper]=[p for ax,bx,ay,by in rect_minus(R[upper]['x'],R[upper]['x']+R[upper]['w'],
                       R[upper]['y'],R[upper]['y']+R[upper]['h'],[cut])
                    for p in clip_to(shell,[(ax,ay),(bx,ay),(bx,by),(ax,by)])]
    for wall,a0,a1 in [(Wall('x',x0,(1,0,0)),y0,y1),(Wall('x',x1,(-1,0,0)),y0,y1),
                        (Wall('y',y0,(0,1,0)),x0,x1),(Wall('y',y1,(0,-1,0)),x0,x1)]:
        b.rooms[lower]+=wall.quad(a0,a1,z0,z1,'hstrim')
    # Keep the eye in the stair sector until it crosses a vertical landing boundary.
    for coords in ([(x0,y0,z1),(x0,y1,z1),(x0,y1,z2),(x0,y0,z2)],
                   [(x1,y0,z1),(x1,y1,z1),(x1,y1,z2),(x1,y0,z2)],
                   [(x0,y0,z1),(x1,y0,z1),(x1,y0,z2),(x0,y0,z2)],
                   [(x0,y1,z1),(x1,y1,z1),(x1,y1,z2),(x0,y1,z2)]):
        cx=sum(p[0] for p in coords)/4;cy=sum(p[1] for p in coords)/4
        # A shaft on the hull has a wall here, not a portal into empty space.
        if R[upper]['x']<cx<R[upper]['x']+R[upper]['w'] and R[upper]['y']<cy<R[upper]['y']+R[upper]['h']:
            b.portal(lower,upper,coords);shaft_portals[tuple(coords)]=((x0+x1)/2,(y0+y1)/2,(z1+z2)/2)
    shafts.append((lower,upper,cut,z1,z2))
    if lower=='vault':
        for y in (y0-12,y1+12):
            b.rooms[upper]+=box((x0,y-8,z1),(x1,y+8,z1+128),'hstrim',top='hstrim')
    elif lower!='breach':
        for x in (x0-12,x1+12):
            b.rooms[upper]+=box((x-8,y0,z1),(x+8,y1,z1+128),'hstrim',top='hstrim')
def stair(rid, start, end, width, z, height, steps, tread, riser):
    # Continuous side rails avoid hundreds of coplanar strips beside the shallow treads.
    b.rooms[rid]+=flight_along(start,end,width,z,steps,tread=tread,riser=riser,rise=height/steps)
    wall='hpwall' if rid in nobles else 'hsvault' if rid=='vault' else 'hsrib'
    b.rooms[rid]+=[p for p in ramp_along(start,end,width,z,z+height,top=tread,skirt=wall,rail=64,rail_role=riser)
                   if p[2][2]==0]
    dx,dy=end[0]-start[0],end[1]-start[1];length=math.hypot(dx,dy)
    nx,ny=-dy/length*width/2,dx/length*width/2
    footprint=[(start[0]-nx,start[1]-ny),(end[0]-nx,end[1]-ny),
               (end[0]+nx,end[1]+ny),(start[0]+nx,start[1]+ny)]
    # Cut the base floor beneath the enclosed flight, keeping every existing upper landing aperture.
    xs,ys=zip(*footprint);slab(rid,True,[(min(xs),max(xs),min(ys),max(ys))],tread)
    # A pitched soffit below the original roof; the existing shaft and its landing stay open above it.
    normal=(-dx*height/length**2,-dy*height/length**2,1);point=(*start,z+448)
    updated=[]
    for panel in b.rooms[rid]:
        if panel[2]!=(0,0,-1) or not all(abs(v[2]-(R[rid]['z']+R[rid]['ceiling']))<.01 for v in panel[0]):
            updated.append(panel);continue
        xx,yy=zip(*[(v[0],v[1])for v in panel[0]])
        for ax,bx,ay,by in rect_minus(min(xx),max(xx),min(yy),max(yy),[(min(xs),max(xs),min(ys),max(ys))]):
            updated+=clip_to(ceiling(ax,ay,bx,by,panel[0][0][2],panel[1]),[(v[0],v[1])for v in panel[0]])
        for piece in clip_to([panel],footprint):
            slope=[(x,y,z+448+((x-start[0])*dx+(y-start[1])*dy)*height/length**2)for x,y,_ in piece[0]]
            updated+=clip_to([(slope,panel[1],(0,0,-1))],None,below=((0,0,panel[0][0][2]),(0,0,1)))
            cap=blv_kit.clip_half(piece,point,normal)
            if cap:updated.append(cap)
        # Close the exposed sides of the lowered soffit against the original flat roof.
        for a,c in zip(footprint,footprint[1:]+footprint[:1]):
            mx,my=(a[0]+c[0])/2,(a[1]+c[1])/2
            if not (R[rid]['x']<mx<R[rid]['x']+R[rid]['w'] and R[rid]['y']<my<R[rid]['y']+R[rid]['h']):
                continue
            coords=[(*a,z),(*c,z),(*c,panel[0][0][2]),(*a,panel[0][0][2])]
            fascia=(coords,wall,(c[1]-a[1],a[0]-c[0],0))
            updated+=clip_to([fascia],[(v[0],v[1])for v in panel[0]],
                             below=(point,tuple(-v for v in normal)))
    b.rooms[rid]=updated


for rid,x in [('rib_port',320),('rib_star',3280)]:
    stair(rid,(x,7000),(x,9500),400,0,1280,80,'hsfloor','hstrim')
stair('quarters',(1000,9700),(1000,7800),400,1280,1280,80,'hpfloor','hptrim')
stair('vault',(400,1450),(2900,1450),400,1280,1280,80,'hsfloor','hstrim')
stair('breach',(3300,1800),(3300,3800),600,0,1280,80,'hscradle','hsrib')


# The gangway is an open balcony within the sixth cathedral volume, with no invented ceiling.
b.rooms['gangway']=[p for p in b.rooms['gangway'] if p[2]!=(0,0,-1)]
b.bounds['gangway']=(*b.bounds['gangway'][:5],3700)
b.rooms['gangway']+=Wall('y',7464,(0,-1,0)).quad(704,2896,1280,3700,'hsnerve')
b.rooms['gangway']+=ceiling(704,6800,2896,7464,3700,'hsceil')
# Low rail base and sparse bone uprights leave the view of the brain open.
b.rooms['gangway']+=box((704,6800,1280),(2896,6824,1392),'hstrim',top='hstrim')
for x in (760,1280,1800,2320,2840):b.rooms['gangway']+=beam((x,6812,1392),(x,6812,2240),20,'hstrim')
b.rooms['gangway']+=beam((704,6812,2240),(2896,6812,2240),24,'hstrim')
b.portal('brain','gangway',[(704,6800,1280),(2896,6800,1280),(2896,6800,3700),(704,6800,3700)])

# Interaction faces and the gantry's real touch floor.
def panel(name,rid,wall,along,z,width,height,role,event):
    parts=plaque(wall,along,z,width,height,role,out=24,edge='hstrim')
    b.rooms[rid]+=parts[1:];b.trigger(name,rid,parts[:1],event)
parts,jambs=blv_kit.recessed_door(Wall('x',0,(1,0,0)),2800,0,512,400,'hshull')
hull_jambs=jambs
b.rooms['gantry']+=jambs;b.trigger('hull_exit','gantry',parts,50)
b.rooms['gantry'].pop(0);b.trigger('arrival_floor','gantry',fitted('gantry',floor(0,2300,1200,3800,0,'hsfloor')),10,kind='pressure_plate')
panel('journal','quarters',Wall('x',1768,(-1,0,0)),8800,1376,200,256,'hpbanner',11)
panel('eye','sensorium',Wall('y',11000,(0,-1,0)),1800,2656,400,320,'hsmemb',12)
# The marked hatch at (1800,200), despite the prose calling it south-west, is authoritative.
b.trigger('return_hatch','vault',box((1672,72,1280),(1928,328,1288),'hstrim',top='hsdoor'),223)

# Room-specific silhouette and furniture. Positions are relative to the plan's walls and its markers.
for x,y in ((1500,2000),(2700,3550)):
    b.rooms['breach']+=beam((x,y,0),(x+150,y+80,1000),200,'hsrib')
    b.rooms['breach']+=Wall('y',y,(0,1,0)).quad(x-100,x+150,650,1088,'hsmemb')
for rid in ('gest_aft','gest_fore'):
    r=R[rid]
    for row in range(3):
        y=r['y']+300+row*(r['h']-600)/2
        for x in (r['x']+350,r['x']+r['w']-350):
            b.rooms[rid]+=prism(x,y,70,0,100,'hsrib',top='hsrib')+prism(x,y,200,100,1000,'hsgest',top='hstrim')
# Stack octagonal lobes, scaled along the hull to the specified 1400 x 2400 x 1600 organ.
brain=[]
for z0,z1,radius in ((2000,2400,500),(2400,3000,700),(3000,3600,560)):
    for coords,role,normal in prism(1800,5664,radius,z0,z1,'hsbrain',top='hsbrain',bottom='hsbrain'):
        brain.append(([(x,5664+(y-5664)*12/7,z) for x,y,z in coords],role,tuple(Vector((normal[0],normal[1]*7/12,normal[2])).normalized())))
b.surface('navigation_brain','brain',brain,cog=155)
for x,y in ((1000,4160),(2600,4160),(820,7300),(2780,7300)):
    for dx in (-50,50):b.rooms['brain']+=prism(x+dx,y,80,200,3700,'hsnerve')
for index in range(1,5):
    m=dict(mark('Ganglion '+str(index)+' ('))

    if index in (1,2):m.update(x=1150 if index==1 else 2450,y=4400)
    z=PLAN.floors[m['floor']];rid='brain' if index<3 else 'gangway'
    b.rooms[rid]+=box((m['x']-200,m['y']-200,z),(m['x']+200,m['y']+200,z+200),'hsrib',top='hsfloor')
for x in (800,1800,2800):
    b.rooms['pens']+=box((x-300,10650,0),(x+300,10950,300),'hscradle',top='hsgest')
for x in (280,820,1360,2240,2780,3320):
    b.rooms['cradles']+=box((x-250,1800,1280),(x+250,1850,2280),'hsgest',top='hscradle')
    for dx in (-250,210):b.rooms['cradles']+=box((x+dx,1800,1280),(x+dx+40,2200,2280),'hscradle',top='hscradle')
b.rooms['vault']+=box((1200,300,1280),(2400,900,1480),'hsrib',top='hsfloor')
b.rooms['vault']+=flight_along((1800,1200),(1800,900),400,1280,7,tread='hsfloor',riser='hstrim',rise=200/7,sides='hstrim',rail=48)
# Table is 1600 along the hall, away from both stair lanes and the passage into the Dormitory.
b.rooms['quarters']+=box((1240,7740,1620),(1740,9340,1680),'hpwall',top='hpfloor')
for y in (7850,9200):b.rooms['quarters']+=box((1280,y,1280),(1700,y+60,1620),'hptrim',top='hptrim')
# Four cradles use shallow gilded frames; their fronts stay clear of the starboard stair.
for y in (7800,8300,8800,9300):
    b.rooms['dormitory']+=box((3500,y,1280),(3600,y+400,1980),'hpwall',top='hptrim')
for k,(x,y,role) in enumerate(((568,11000,'hptroph1'),(1136,10432,'hptroph2'))):
    w=Wall('y',y,(0,-1,0)) if k==0 else Wall('x',x,(-1,0,0))
    b.rooms['trophy']+=plaque(w,x if k==0 else y,1400,700,340,role,out=36,edge='hptrim')
    b.decoration('hes_trophy_relic',568 if k==0 else 980,10850 if k==0 else 10432,1280)
b.decoration('hes_trophy_relic',1700,10650,1280)
# The stated 1000-high rack cannot fit a 640-high chamber: fit the banner rack to 560 (README).
b.rooms['vchamber']+=box((1400,10740,1280),(2200,10800,1840),'hptrim',top='hptrim')
b.rooms['vchamber']+=plaque(Wall('y',10740,(0,-1,0)),1800,1320,720,480,'hpbanner',edge='hptrim')
b.rooms['core']+=prism(1800,8900,300,2560,3648,'hsnerve',top='hsnerve')
for x in (900,1800,2700):
    b.rooms['sensorium']+=prism(x,10880,150,2560,3000,'hsnerve',top='hsmemb')
# Three windows share the 2400 bow wall: edge windows wrap onto the flanks, retaining 900 width.
for w,c in ((Wall('x',600,(1,0,0)),10450),(Wall('y',11000,(0,-1,0)),1800),(Wall('x',3000,(-1,0,0)),10450)):
    b.rooms['sensorium']+=plaque(w,c,2900,900,400,'hsmemb',out=4,edge='hstrim')
# Ledges leave both corner entrance lanes, the stair landing and all bowls open.
for x0,y0,x1,y1 in ((700,300,2900,700),(700,2900,2900,3300),(300,700,700,900),(300,1200,700,2400),
                      (300,2700,700,2900),(2900,700,3300,900),(2900,1800,3300,2400),(2900,2700,3300,2900)):
    b.rooms['duel']+=box((x0,y0,2560),(x1,y1,2960),'hptrim',top='hpfloor')
for x,y in ((800,800),(2800,800),(800,2800),(2800,2800)):
    b.rooms['duel']+=prism(x,y,90,2560,3648,'hsrib',top='hstrim')
# Replace the surviving flat floor pieces with a fitted ring, preserving the hatch aperture.
old=[]
for p in b.rooms['duel']:
    if p[2]==(0,0,1) and all(abs(v[2]-2560)<.01 for v in p[0]):
        x0=min(v[0] for v in p[0]);x1=max(v[0] for v in p[0]);y0=min(v[1] for v in p[0]);y1=max(v[1] for v in p[0])
        for a,c,d,e in rect_minus(x0,x1,y0,y1,[(600,3000,600,3000)]):
            old+=clip_to(floor(a,d,c,e,2560,'hpfloor'),[(v[0],v[1])for v in p[0]])
        a,c,d,e=max(x0,600),min(x1,3000),max(y0,600),min(y1,3000)
        if a<c and d<e:
            q=floor(a,d,c,e,2560,'hsduel')[0];old+=clip_to([(*q,blv_kit.Fit((600,600,2560),(1,0,0),(0,1,0),2400,2400))],[(v[0],v[1])for v in p[0]])
    else:old.append(p)
b.rooms['duel']=old
for rid in ('gest_aft','gest_fore','lower_hall','pens'):
    r=R[rid];b.decoration('hes_bones_litter',r['x']+180,r['y']+180,r['z'])

for rid,y,z in [('gal_port',4100,1280),('spine_port',3700,2560)]:
    b.rooms[rid]+=box((220,y-60,z),(420,y+60,z+64),'hsrib',top='hsfloor')

# Leave the Core's seal clear; the existing lamps keep their anchors between the new ribs.
lights=list(PLAN.lights)
arch_ys=[y for y in range(3600,9300,512) if abs(y-8200)>280]
assert len(arch_ys)==11
for rid in ('spine_port','spine_star'):
    r=R[rid]
    for y in arch_ys:
        points=[(r['x']+x,y,r['z']+z) for x,z in ((16,0),(16,512),(128,736),(512,736),(624,512),(624,0))]
        for a,c in zip(points,points[1:]):b.rooms[rid]+=beam(a,c,32,'hstrim')
    fixture=next(l for l in PLAN.lights if l['note']==r['name']+', '+('west' if rid=='spine_port' else 'east')+' wall')
    for y in range(3856,9000,512):
        if any(l['note']==fixture['note'] and abs(l['y']-y)<64 for l in PLAN.lights):continue
        lights.append(dict(fixture,id=f'{rid}_{y}',y=y))
assert len(lights)==68
light_plan=copy.copy(PLAN);light_plan.lights=lights
overlap,where=zone.plans.max_light_overlap(light_plan,step=32)
assert overlap<=4,(overlap,where)
(PROJECT/'review/plan_checks.json').write_text(json.dumps(dict(lights=len(lights),spine_arches=22,
    max_floor_light_overlap=overlap,where=where),indent=2)+'\n')
chest_events={}
for e,m in enumerate([m for m in PLAN.marks if m['kind'] in ('chest_fixed','chest_random')],30):
    z=PLAN.floors[m['floor']]+(200 if e==32 else 0)
    b.decoration('hes_kreegan_pod_chest',m['x'],m['y'],z,event=e,cog=131 if e==31 else 0)
    if e>=32:chest_events[e]=e-32
for l in lights:b.plan_light(l,zone.plans.FIXTURE_COG)

# Keep every prop and replacement floor inside its room's new walls.
for rid in b.rooms:
    b.rooms[rid]=fitted(rid,[p for p in b.rooms[rid] if rid!='gantry' or p not in hull_jambs])
b.rooms['gantry']+=hull_jambs
for name,rid,panels,*_ in b.triggers:
    assert all(blv_kit._inside(FOOTPRINTS[rid],0 if name=='hull_exit' else v[0],v[1]) for p in panels for v in p[0]),(name,rid)
for o,t,axis,p,a0,a1,z0,z1,sign in openings:
    for rid,plane in ((o,p),(t,p+sign*64)):
        for a in (a0,a1):
            x,y=(plane,a)if axis=='x'else(a,plane)
            assert blv_kit._inside(FOOTPRINTS[rid],x,y),(rid,x,y)

for o,t,axis,p,a0,a1,z0,z1,sign in openings:
    before=len(b.rooms[o]);b.opening(o,t,axis,p,a0,a1,z0,z1,toward=sign,floor_role='hsfloor',side_role='hstrim',ceiling_role='hstrim')
    if any(doors.get(e)==(o,t,axis,p,a0,a1,z0,z1,sign) for e in (220,221)):
        panel=b.rooms[o].pop(before);b.trigger('terms_'+o,o,[panel],160,kind='pressure_plate')
for event,(o,t,axis,p,a0,a1,z0,z1,sign) in doors.items():
    mid=p+32*sign
    lo,hi=((mid-8,a0,z0),(mid+8,a1,z1)) if axis=='x' else ((a0,mid-8,z0),(a1,mid+8,z1))
    panels=[]
    for coords,role,normal in box(lo,hi,'hsdoor',top='hstrim'):
        if role=='hsdoor':
            w=Wall('x' if normal[0] else 'y',coords[0][0 if normal[0] else 1],normal)
            v=[p[1 if normal[0] else 0] for p in coords];panels.append((coords,role,normal,w.fit(min(v),max(v),z0,z1)))
        else:panels.append((coords,role,normal))
    b.door('door_'+str(event),o,panels,event,400,open_speed=400,close_speed=400,event=event)
b.door('vault_stair_hatch','duel',box((1900,1250,2544),(2900,1650,2560),'hsdoor',top='hsfloor'),552,400,open_speed=400,close_speed=400,event=52)


# Clip all surfaces, event faces and portals to the 52 plan sectors, including the cathedral's height split.
def clip(panel,bounds):
    points=list(panel[0])
    for axis,lo,hi in ((0,bounds[0],bounds[2]),(1,bounds[1],bounds[3]),(2,bounds[4],bounds[5])):
        for limit,sign in ((lo,1),(hi,-1)):
            out=[]
            for a,c in zip(points,points[1:]+points[:1]):
                da,dc=(a[axis]-limit)*sign,(c[axis]-limit)*sign
                if da>=-0.001:out.append(a)
                if da<0<dc or dc<0<da:
                    t=da/(da-dc);out.append(tuple(a[k]+(c[k]-a[k])*t for k in range(3)))
            points=out
            if len(points)<3:return None
    area=sum((Vector(points[k])-Vector(points[0])).cross(Vector(points[k+1])-Vector(points[0])).length for k in range(1,len(points)-1))
    return (points,*panel[1:]) if area>.01 else None

# Fore nerve trunks also occupy the gangway's upper airspace.
for p in b.rooms['brain']:
    if p[2]==(0,0,-1) or all(abs(v[1]-7464)<.01 for v in p[0]):continue
    q=clip(p,(704,6800,2896,7464,1280,3700))
    if q:b.rooms['gangway'].append(q)
parts={};original_portals=b.portals;b.portals=[]
for rid in list(b.rooms):
    panels=b.rooms.pop(rid);bound=b.bounds.pop(rid);amb=b.ambient.pop(rid);r=R[rid];n=r['sectors']
    xs=[bound[0],bound[2]];ys=[bound[1],bound[3]];zs=[bound[4],bound[5]]
    if rid=='duel':xs=[300,1800,3300];ys=[300,1800,3300]
    elif rid=='brain':ys=[3864,5064,6264,7464];zs=[-1,1280,3700]
    elif n>1:
        target=xs if r['w']>r['h'] else ys
        target[:]=[target[0]+(target[-1]-target[0])*i/n for i in range(n+1)]
        if rid=='breach':xs=[1264,2400,3600]
    parts[rid]=[]
    for iz,(z0,z1) in enumerate(zip(zs,zs[1:])):
        for iy,(y0,y1) in enumerate(zip(ys,ys[1:])):
            for ix,(x0,x1) in enumerate(zip(xs,xs[1:])):
                if rid=='brain' and iz==1 and iy==2:y1=6800
                name=f'{rid}_{ix}_{iy}_{iz}' if n>1 else rid
                bounds=(x0,y0,x1,y1,z0,z1)
                limits=(x0-64 if ix==0 else x0,y0-64 if iy==0 else y0,x1+64 if ix==len(xs)-2 else x1,
                        y1+64 if iy==len(ys)-2 and not(rid=='brain' and iz==1) else y1,
                        z0-1 if iz==0 else z0,z1 if iz<len(zs)-2 else z1+1)
                b.room(name,bounds,amb);b.rooms[name]+=[q for p in panels if (q:=clip(p,limits))]
                parts[rid].append((name,limits))
    for i,(a,_) in enumerate(parts[rid]):
        ab=b.bounds[a]
        for c,_ in parts[rid][i+1:]:
            cb=b.bounds[c]
            for axis in range(3):
                low=(0,1,4)[axis];high=(2,3,5)[axis]
                if ab[high]!=cb[low]:continue
                other=[k for k in range(3) if k!=axis];ranges=[]
                for k in other:
                    l,h=(0,1,4)[k],(2,3,5)[k];ranges.append((max(ab[l],cb[l]),min(ab[h],cb[h])))
                if any(lo>=hi for lo,hi in ranges):continue
                coords=[]
                for u,v in ((0,0),(1,0),(1,1),(0,1)):
                    p=[0,0,0];p[axis]=ab[high];p[other[0]]=ranges[0][u];p[other[1]]=ranges[1][v];coords.append(tuple(p))
                b.portal(a,c,coords)
def facing(front,back,coords,inside):
    """blv_kit faces a portal toward its front sector's bounds centre. A shaft on its lower room's edge has that
    centre outside the shaft, which hides the upper room from the stair, so the upper sector fronts it instead."""
    if inside is None:return front,back
    points=[Vector(p) for p in coords];normal=(points[1]-points[0]).cross(points[2]-points[0])
    def side(rid):
        x0,y0,x1,y1,z0,z1=b.bounds[rid];centre=Vector(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
        return normal if normal.dot(centre-points[0])>0 else -normal
    if side(front).dot(Vector(inside)-points[0])>0:return front,back
    assert side(back).dot(Vector(inside)-points[0])<0,(front,back,coords)
    return back,front
for front,back,coords in original_portals:
    inside=shaft_portals.get(tuple(coords))
    if inside is None:
        # An upper room's doorway on a shaft's edge opens into the stair sector, which owns that space.
        cx,cy,cz=(sum(p[k] for p in coords)/len(coords) for k in range(3))
        for lower,upper,(x0,x1,y0,y1),z1,z2 in shafts:
            if x0<=cx<=x1 and y0<=cy<=y1 and z1<=cz<=z2:
                front,back=(lower if front==upper else front),(lower if back==upper else back)
    for f,fc in parts[front]:
        for t,tc in parts[back]:
            p=clip((coords,'marker',(1,0,0)),fc);q=clip(p,tc) if p else None
            if q:b.portal(*facing(f,t,q[0],inside),q[0])
triggers,b.triggers=b.triggers,[]
for name,rid,panels,event,kind,flags,cog in triggers:
    for part,limits in parts[rid]:
        cut=[q for p in panels if (q:=clip(p,limits))]
        if cut:b.trigger(name+'_'+part,part,cut,event,kind,flags,cog)
for k,(name,rid,panels,*tail) in enumerate(b.mechanisms):
    centre=[sum(p[i] for p in panels[0][0])/len(panels[0][0]) for i in range(3)]
    candidates=[n for n,c in parts[rid] if c[0]<=centre[0]<=c[2] and c[1]<=centre[1]<=c[3]]
    assert candidates,(name,rid,centre)
    part=candidates[0]
    b.mechanisms[k]=(name,part,panels,*tail)

# Stable group/index ledger. Pack anchors stay in the design; formation offsets clear stairs and furnishings.
actors=[]
packs=[('in the breach',[10021,10021,10031],1),('field 230',[10045]*4+[10003]*4,2),
 ('port rib corridor',[10003]*4,3),('starboard rib corridor',[10003]*4,4),('Heavy Lancer ×1, Hatchlings ×2',[10021,10003,10003],5),
 ('Ganglion 1 (',[10131],6),('Ganglion 2 (',[10131],7),('Ganglion 3 (',[10131],8),('Ganglion 4 (',[10131],9),
 ('flying the Brain',[10031]*3,10),('field 231',[10045]*4+[10003]*3,11),('in their pens',[10003]*6,12),
 ('Keel Passage',[10003]*3,13),('in the cradles',[10021]*4+[10031],14),('port gallery',[10031]+[10003]*4,15),
 ('starboard gallery',[10021]*2,16),('Noble ×1, Noble Duellist ×1',[10040,10041],17),('in the dormitory',[10040,10040,10021],18),
 ('among the trophies',[10041,10040],19),('(attendants)',[10021,10021,10031],20),('in the Brain Core',[10031]*2,21),
 ('(port spine)',[10041,10040,10021],22),('(starboard spine)',[10021]*2,23),('at the eyes',[10031]+[10003]*4,24),
 ('Lord Vhorrax (',[10106],25),('Lord Vhorrax (',[10106],26)]
for label,ids,group in packs:
    m=mark(label);x,y=m['x'],m['y'];z=PLAN.floors[m['floor']]
    for i,mid in enumerate(ids):
        dx=(i-(len(ids)-1)/2)*160;dy=0
        if group in (3,4,5,15,16,22,23):dx=0;dy=(i-(len(ids)-1)/2)*180
        if group in (2,11):dx=((i%4)-1.5)*250;dy=(i//4-.5)*320
        az=z+200 if group in (6,7,8,9) else 1500 if group==10 else z
        if group==5:az=16*(math.floor((y+dy-7000)/31.25)+1)
        if group in (6,7):x,y=1150 if group==6 else 2450,4400
        if group==17:dx=-360;dy=(i-.5)*240  # between the bone and gilded stairs
        actors.append(dict(monster=mid,position=[round(x+dx),round(y+dy),round(az)],group=group,
                           posted=mid in (10045,10131) or group in (5,16,23),yaw_degrees=0,name='',
                           sector=sorted(b.rooms).index(b.room_at(x+dx,y+dy,az+1))+1))
assert len(b.rooms)==52,len(b.rooms)
assert len(actors)==81,len(actors)
assert len(b.mechanisms)==27,len(b.mechanisms)
assert len(PLAN.lights)==52
# PICKUPS.md: the Seed Vault's serum hold (14), then three grafting-deck supply groups (5/5/4).
pickup_groups = [
    ('hes_serum_vat', 701,
     [('vault', x, 160, 1280) for x in (220,420,620,820,1020,1220,1420,2180,2380,2580,2780,2980,3180,3380)]
     + [('cradles', 140, y, 1280) for y in (2400,2640,2880,3120,3360)]
     + [('dormitory', x, 7800, 1280) for x in (2050,2250,2450,2650,2850)]
     + [('attend', x, 10820, 1280) for x in (2700,2920,3140,3360)]),
    ('hes_scrap_bundle', 751, [
        ('gantry',180,3560,0), ('gantry',1000,3400,0), ('breach',1420,3200,0), ('breach',2780,2300,0),
        ('gest_aft',1200,180,0), ('gest_aft',2400,1450,0), ('gest_fore',1350,7700,0), ('gest_fore',2100,9600,0),
        ('pens',600,10080,0), ('pens',2700,10040,0), ('cradles',900,3530,1280), ('cradles',2500,3500,1280),
        ('dormitory',2250,9500,1280), ('attend',2640,10060,1280), ('trophy',850,10030,1280),
        ('vault',2700,1060,1280), ('sensorium',820,9800,2560), ('sensorium',2760,9900,2560),
        ('spine_port',130,7250,2560), ('spine_star',3470,7800,2560)]),
]
pickups = []
for model, first, points in pickup_groups:
    for event, (room, x, y, z) in enumerate(points, first):
        b.decoration(model, x, y, z, 90, event=event, cog=event)
        pickups.append(dict(model=model, event=event, room=room, position=[x,y,z]))
for name,x,y,z,*_ in b.decorations+b.lights:
    candidates=[rid for rid,r in R.items() if r['x']-1<=x<=r['x']+r['w']+1 and r['y']-1<=y<=r['y']+r['h']+1
                and r['z']<=z<=r['z']+r['ceiling']]
    assert any(blv_kit._inside(FOOTPRINTS[rid],x,y)for rid in candidates),(name,x,y,z)
b.export(dict(room_footprints=FOOTPRINTS,arrivals={'from_hes_out3':{'position':[300,2800,0],'direction_degrees':0}},
              door_ids={m[0]:m[3] for m in b.mechanisms},chest_events=chest_events,actors=actors,
              groups={g:[i for i,a in enumerate(actors) if a['group']==g] for g in range(1,27)},
              monster_packs=PLAN.marks,light_count=len(lights),sector_bounds={k:list(v) for k,v in b.bounds.items()},
              pickups=pickups))

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
