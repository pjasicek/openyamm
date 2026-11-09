"""D16: common node rooms, clean capacitor banks, the Graft and three breakable columns."""
import importlib.util
import os
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path[:0]=[str(PROJECT.parent/'hesper_stage'),str(PROJECT.parent/'hesper_nodes_common')]
import blv_kit as kit
from blv_kit import Wall, box, floor, plaque, prism, pipe
from node_rooms import NodeRooms, ROLES, DOORS
spec=importlib.util.spec_from_file_location('zone4',ROOT/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone=importlib.util.module_from_spec(spec);spec.loader.exec_module(zone)
PLAN=zone.d16
assert not zone.plans.ceiling_problems(PLAN)
assert zone.plans.max_light_overlap(PLAN)[0]<=4
kit.FOLDERS += [kit.ART/f'textures_{name}/masters' for name in
                ('k9_lattice','k3_transit','k5_grafted','k4_transitions')]
roles=dict(ROLES,graft='hngraft',creep='hxcreepf',creep_wall='hxcreepw',creep_edge='hxcreepb',creep_ceiling='hkceil')
b=kit.Builder('hes_d16.blv',roles,PROJECT/'source')
cx,cy,radius=zone.CREEP_MOUND
node=NodeRooms(b,PLAN,splits={'graft':('y',[7500])},doors={'Graft to T2':('t2',7,58)},
               floor_cuts={'graft':[(cx-radius,cx+radius,cy-radius,cy+radius)],
                           'galleries':[(6800,8000,4992,5952)],'t2':[(9064,9464,7616,9016)]},
               accent='graft',middle_walls={'graft':'graft'},middle_floors={'graft':'creep'},
               ambient={'graft':24,'galleries':22,'tunnel':22})
node.shell()
node.common_contents(zone,coupling_radius=1000,coupling_geometry=False)
node.terminal('t2',81)

# Creep replaces the specified floor/wall bands; the clean geometry remains owned by the shared module.
for rid in ('graft_0','graft_1'):
    b.rooms[rid]=[(pts,'creep_ceiling' if role=='ceiling' else
                  'creep_wall' if role=='resin' and rid=='graft_1' else role,n,*extra)
                 for pts,role,n,*extra in b.rooms[rid]]
for x0,x1,y0,y1 in kit.rect_minus(6800,8000,4992,5952,[(7172,7428,4992,5952)]):
    b.rooms['galleries_2']+=floor(x0,y0,x1,y1,-512,'creep')
b.rooms['t2']+=kit.clip_to(floor(9064,7616,9464,9016,-512,'creep'), b.footprints['t2'])
for side,plane,inward in [('south',4992,(0,1,0)),('north',5952,(0,-1,0))]:
    b.rooms['galleries_2']+=Wall('y',plane,inward).quad(6800,8000,-512,-384,'creep_edge',out=4)
# The hall's 640-high design banks must fit its 512 ceiling. Retain the footprint, leave 64 overhead.
for x in (8264,9264):
    for y in (5292,5792,6292,6792):
        if x==8264 and abs(y-5472)<350 or x==9264 and abs(y-6600)<374:continue
        for z0,z1,role in [(-512,-480,'trim'),(-480,-96,'capacitor'),(-96,-64,'trim')]:
            b.rooms['cleanhall']+=box((x-200,y-150,z0),(x+200,y+150,z1),role,top=role)

# Sixteen broad dome faces, with a separate edge band and no floor hidden underneath it.
def add_face(points,role,base,normal=None):
    points=[Vector(p) for p in points]
    points=[p for i,p in enumerate(points) if (p-points[i-1]).length>.01]
    if len(points)<3:return
    n=Vector(normal) if normal else (points[1]-points[0]).cross(points[2]-points[0]).normalized()
    center=sum(points,Vector())/len(points)
    b.rooms[node.at(center.x,center.y,base)].append((points,role,n))

for k in range(8):
    a,c=k*math.pi/4,(k+1)*math.pi/4
    def ring(r,z):return [(cx+r*math.cos(t),cy+r*math.sin(t),z) for t in (a,c)]
    edge=ring(radius,-512); low=ring(radius-48,-496); high=ring(radius/2,-416)
    square=[(cx+radius*math.cos(t)/max(abs(math.cos(t)),abs(math.sin(t))),
             cy+radius*math.sin(t)/max(abs(math.cos(t)),abs(math.sin(t))),-512) for t in (a,c)]
    add_face([edge[0],square[0],square[1],edge[1]],'creep','graft',(0,0,1))
    add_face([edge[0],edge[1],low[1],low[0]],'creep_edge','graft')
    add_face([low[0],low[1],high[1],high[0]],'creep','graft')
    add_face([high[0],high[1],(cx,cy,-384)],'creep','graft')
# The mound's central glyph is a real slab, rooted in its top.
b.rooms['graft_0']+=box((cx-128,cy-64,-400),(cx+128,cy-8,-160),'resin',top='trim')
b.trigger('graft_glyph','graft_0',plaque(Wall('y',cy-64,(0,-1,0)),cx,-320,224,160,'glyph',out=4),15)
grafted=[(9928,6900),(11128,6900),(9928,8100),(11128,8100)]
for x,y in grafted:
    rid=node.at(x,y,'graft')
    b.rooms[rid]+=prism(x,y,220,-512,128,'graft',sides=8)
    # Provisional strands use the four specified column anchors; replace when dedicated art is supplied.
    for dx,dy,length in [(-100,-205,280),(90,-205,400),(-210,20,220)]:
        b.rooms[rid]+=prism(x+dx,y+dy,24,128-length,128,'resin',sides=5)
for x,y in [(9700,6000),(10100,6000),(11400,6100),(11400,7100),
            (11400,7900),(11400,8600),(9700,9000),(10200,9000)]:
    b.decoration('hes_creep_pod_static',x,y,-512)
m=next(m for m in PLAN.marks if m['kind']=='chest_random' and m['label'].startswith('Kreegan pod'))
b.decoration('hes_kreegan_pod_chest',m['x'],m['y'],-512,event=32)

# Hollow columns: the entire east semicircle is open for the first 384 units, exposing each living cell.
for k,(x,y) in enumerate(zone.COUPLINGS):
    by_room={}
    def column_face(points,normal):
        center=sum((Vector(p) for p in points),Vector())/len(points)
        rid=node.at(center.x,center.y,'core')
        by_room.setdefault(rid,[]).append((points,'capacitor',normal))
    for j in range(16):
        a,c=j*math.pi/8,(j+1)*math.pi/8
        def ring(r,z):return [(x+r*math.cos(t),y+r*math.sin(t),z) for t in (a,c)]
        n=(math.cos((a+c)/2),math.sin((a+c)/2),0)
        for z0,z1 in [(-512,-128),(-128,192),(192,640)]:
            if z0==-512 and n[0]>0:continue
            lo,hi=ring(200,z0),ring(200,z1)
            column_face([lo[0],lo[1],hi[1],hi[0]],n)
            if z0==-512:
                lo,hi=ring(160,z0),ring(160,z1)
                column_face([lo[1],lo[0],hi[0],hi[1]],(-n[0],-n[1],0))
        # Cap the underside of the intact upper column over the open cell gap.
        if n[0]>0:
            lo=ring(200,-128)
            column_face([lo[1],lo[0],(x,y,-128)],(0,0,-1))
    for yy,n in [(y-200,(0,-1,0)),(y+200,(0,1,0))]:
        inner=yy+(40 if yy<y else -40)
        column_face([(x,yy,-512),(x,inner,-512),(x,inner,-128),(x,yy,-128)],(1,0,0))
    for rid,panels in by_room.items():b.trigger(f'column_{k+1}_{rid}',rid,panels,85+k,cog=85+k)

for light in PLAN.lights:
    light=dict(light)
    if light['fixture'] and 3288<light['y']<4928:light['z']-=round(512*(light['y']-3288)/1640)
    b.plan_light(light,zone.plans.FIXTURE_COG)
b.rooms=dict(sorted(b.rooms.items()))
actors=[]
packs=[(1,[10032]+[10002]*3,True),(1,[10041],True),(2,[10002]*3,False),(2,[10041]*2,True),
       (5,[10002]*4,False),(6,[10002]*4,False),(3,[10057]*2,True),(3,[10057]*2,True),
       (9,[10109],True),(10,[10041]*2+[10032],True),(11,[10002]*5,False),
       (12,[10032,10042],True),(3,[10057]*2,True),
       (21,[10142],True),(22,[10142],True),(23,[10142],True)]
marks=[m for m in PLAN.marks if m['kind'] in ('monster','boss')]
assert len(marks)==len(packs)
for m,(group,ids,posted) in zip(marks,packs):
    assert m['count']==len(ids)
    for k,mid in enumerate(ids):
        x=m['x']+(k%3-(len(ids)-1)/2)*180;y=m['y']+(k//3)*180;z=PLAN.floors[m['floor']]
        if group==1 and len(ids)==4:x=4350+(k%2)*900;y=2800+(k//2)*120;z=128
        if group==3:x=m['x']+(k*2-1)*140;y=m['y']
        if group==9:x=m['x'];y=m['y']
        # Each living cell stands in its column's open gap, on the column's axis (DUNGEONS.md's Conductor fight);
        # the plan's mark sits 160 east of it, at the gap's edge.
        if group>=21:x,y=zone.COUPLINGS[group-21]
        if group==10:x=8580+k*180;y=6500
        if group==11:
            x,y=[(10200,8600),(10430,8710),(10660,8630),(10350,8930),(10880,8900)][k]
        if group==12:x=m['x']+(k*2-1)*160;y=m['y']
        # Keep full collision hulls off stairs, pipe trunks, arc posts and the terminal console.
        if group == 1 and mid == 10041: x = 3800
        if group == 5 and k == 3: y = 5520
        if group == 6: y = 5430+(k//3)*180
        if group == 3 and m['x'] == 8300 and k == 1: y = 8420
        rid=node.at(x,y)
        actors.append(dict(name=m['label'],monster=mid,group=group,position=[x,y,z],posted=posted,
                           yaw_degrees=0 if group>=21 else 270,sector=list(b.rooms).index(rid)+1))
assert len(actors)==38 and len(b.rooms)==20 and len(b.mechanisms)==7
# PICKUPS.md: supplies at room edges, with the event also serving as the sprite-swap cog.
pickups = json.loads((PROJECT / 'pickups.json').read_text())
assert len(pickups) == 20 and [p['event'] for p in pickups] == list(range(750, 770))
assert all(p['model'] in ('hes_colony_satchel', 'hes_scrap_bundle') and p['room'] != 'core' for p in pickups)
for pickup in pickups:
    x, y, z = pickup['position']
    room = node.parents[pickup['room']]
    assert room['x'] + 64 <= x <= room['x'] + room['w'] - 64
    assert room['y'] + 64 <= y <= room['y'] + room['h'] - 64
    assert z == room['z']
    b.decoration(pickup['model'], x, y, z, event=pickup['event'], cog=pickup['event'])

node.validate_shapes()
b.export({'pickups': pickups, 'arrivals':{'blast_door':{'position':[4800,300,0],'direction_degrees':90},
                     'service_tunnel':{'position':[3424,12200,-512],'direction_degrees':270}},
          'door_ids':dict(DOORS,t2=7),'chest_events':{'30':0,'31':1,'32':2,'33':3},'actors':actors,
          'couplings':zone.COUPLINGS,'arc_light_positions':[[x,5472,-420] for x in zone.ARC_X],
          'provisional_dressing':'Eight wall-side pods and strands on the four specified grafted columns.'})
next(s for s in b.metadata['surfaces'] if s['id']=='vault')['cog_number']=55
(PROJECT/'source/hes_d16.geometry.yml').write_text(json.dumps(b.metadata,indent=2)+'\n')

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
