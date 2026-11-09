"""D6: import the common Lattice rooms, then add the coolant middle and shield-panel arena."""
import importlib.util
import os
import json
import math
import sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path[:0]=[str(PROJECT.parent/'hesper_stage'),str(PROJECT.parent/'hesper_nodes_common')]
import blv_kit as kit
from blv_kit import Wall, box, floor, plaque, prism, pipe
from node_rooms import NodeRooms, ROLES, DOORS
from author_standins_blender import build as build_standins

spec=importlib.util.spec_from_file_location('zone4',ROOT/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone4=importlib.util.module_from_spec(spec); spec.loader.exec_module(zone4)
PLAN=zone4.d6
assert not zone4.plans.ceiling_problems(PLAN)
assert zone4.plans.max_light_overlap(PLAN)[0]<=4
kit.FOLDERS += [kit.ART/f'textures_{name}/masters' for name in ('k9_lattice','k3_transit','k5_grafted')]
build_standins()
b=kit.Builder('hes_d06.blv',ROLES,PROJECT/'source')
cuts={'core':[(3200,3400,6588,6844),(6200,6400,8188,8444)],
      'loop':[(x-200,x+200,y-200,y+200) for x,y in zone4.LOOP_VENTS]}
node=NodeRooms(b,PLAN,splits={'pumps':('x',[9264]),'loop':('y',[8056])},
               doors={'loop to T2':('t2',7,58)},floor_cuts=cuts,accent='cool',
               middle_walls={'pumps':'cool','loop':'cool'},middle_floors={'pumps':'grate','loop':'grate'},
               ambient={'loop':23})
node.shell()
node.common_contents(zone4,coupling_radius=800)
node.terminal('t2',81)

# D6's own middle: four stack silhouettes (plinth, casing, flange, motor), the straight manifold.
for x in (8500,9000,9700,10200):
    rid=node.at(x,5900,'pumps')
    for radius,z0,z1,role in [(260,-512,-416,'trim'),(200,-416,-92,'cool'),
                              (230,-92,-60,'trim'),(230,-60,48,'motor')]:
        b.rooms[rid]+=prism(x,5900,radius,z0,z1,role,top=role)
for rid,x0,x1 in [('pumps_0',8300,9264),('pumps_1',9264,10400)]:
    b.rooms[rid]+=pipe((x0,5900,-152),(x1,5900,-152),90,'cool',caps=('start','end'))
m=next(m for m in PLAN.marks if 'event 13' in m['label'])
b.trigger('coolant_gauge','pumps_1',plaque(Wall('y',6792,(0,-1,0)),m['x'],-288,256,160,'glyph'),13)
m=next(m for m in PLAN.marks if m['label'].startswith('Pump-room locker'))
b.decoration('hes_colonial_locker',m['x'],m['y'],-512,0,event=32)

x,y,w,h=zone4.LOOP_BLOCK
for rid,y0,y1,skip in [('loop_0',y,y+h/2,('north',)),('loop_1',y+h/2,y+h,('south',))]:
    b.rooms[rid]+=box((x,y0,-512),(x+w,y1,128),'cool',skip=skip)
    # Four upright frosted pipe ribs make the chiller readable from either approach.
    for xx in (x+100,x+w-100): b.rooms[rid]+=prism(xx,y0+80,70,-512,128,'cool',sides=8)
for k,(x,y) in enumerate(zone4.LOOP_VENTS):
    rect=(x-200,x+200,y-200,y+200)
    node.plate('vent_'+str(k),'loop',rect,100+k,z=-528,cog=100+k,role='grate')
    rid=node.at(x,y,'loop')
    b.rooms[rid]+=box((x-200,y-200,-528),(x+200,y+200,-512),'trim')

# Eight real solid walls, each one linear mover, initially alternating up/down.
for k,(x,y) in enumerate(zone4.SHIELD_PANELS):
    angle=math.radians(22.5+45*k)
    cs,sn=math.cos(angle),math.sin(angle)
    panels=[]
    for coords,role,n in box((-32,-425,-512),(32,425,512),'shield',top='trim',bottom='trim'):
        points=[(x+u*cs-v*sn,y+u*sn+v*cs,z) for u,v,z in coords]
        normal=(n[0]*cs-n[1]*sn,n[0]*sn+n[1]*cs,n[2])
        panels.append((points,role,normal))
    b.door('panel_'+str(k+1),node.at(x,y,'core'),panels,8+k,1024,direction=(0,0,-1),
           open_speed=1024/.6,close_speed=1024/.6,initial='open' if k%2==0 else 'closed')
for suffix,rect in [('west',(3200,3400,6588,6844)),('east',(6200,6400,8188,8444))]:
    node.plate('core_entry_'+suffix,'core',rect,152)

for light in PLAN.lights:
    # Plan z=0 on the ramp is its upper datum; floor fixtures follow its actual slope.
    light=dict(light)
    if light['fixture'] and 3288<light['y']<4928:
        light['z']-=round(512*(light['y']-3288)/1640)
    b.plan_light(light,zone4.plans.FIXTURE_COG)

b.rooms=dict(sorted(b.rooms.items()))
actors=[]
packs=[(1,10022,True),(1,10041,True),(2,10012,False),(2,10041,True),
       (5,10012,False),(6,10012,False),(3,10057,True),(3,10057,True),(9,10108,True),
       (4,10022,True),(10,10012,False),(11,10012,False),(3,10057,True)]
marks=[m for m in PLAN.marks if m['kind'] in ('monster','boss')]
assert len(marks)==len(packs)
for m,(group,mid,posted) in zip(marks,packs):
    for k in range(m['count']):
        x=m['x']+(k%3-1)*180; y=m['y']+(k//3)*180; z=PLAN.floors[m['floor']]
        monster=mid
        if group==1 and mid==10022: x=4350+(k%2)*900; y=2800+(k//2)*120; z=128
        if group==4:
            x=3650 if k%2==0 else 5950; y=6450 if k<2 else 8782
        if group==9: x=m['x']; y=m['y']
        if group==11:
            x=m['x']; y=m['y']+(k-1.5)*180
            if k==3: monster=10042
        if group==3: x=m['x']+(k*2-1)*140; y=m['y']
        # Keep full collision hulls clear of the dais, pipes, arc posts, pump flanges and terminal console.
        if group == 1 and mid == 10041: x = 3800
        if group == 5 and k == 3: y = 5520
        if group == 6: y = 5430+(k//3)*180
        if group == 10 and k == 3: x, y = 8390, 5450
        if group == 3 and m['x'] == 8300 and k == 1: y = 8420
        rid=node.at(x,y)
        actors.append(dict(name=m['label'],monster=monster,group=group,position=[x,y,z],posted=posted,
                           yaw_degrees=270,sector=list(b.rooms).index(rid)+1))
assert len(actors)==37
assert len(b.rooms)==21
assert len(b.mechanisms)==15
assert len(b.decorations)+len(b.lights)==len(PLAN.lights)+5
door_ids={**DOORS,'t2':7,**{'panel_'+str(k+1):8+k for k in range(8)}}
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
          'door_ids':door_ids,'chest_events':{'30':0,'31':1,'32':2,'33':3},'actors':actors,
          'couplings':zone4.couplings(800),'vents':zone4.LOOP_VENTS,
          'arc_light_positions':[[x,5472,-420] for x in zone4.ARC_X],
          'pending_dressing':'Two valves and ten frost drifts await position approval; Crown exits await out4_build.json.'})
next(s for s in b.metadata['surfaces'] if s['id']=='vault')['cog_number']=55
(PROJECT/'source/hes_d06.geometry.yml').write_text(json.dumps(b.metadata,indent=2)+'\n')

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
