"""D7 shares the node shell, then adds its assembly line and minefields."""
import importlib.util
import os
import json
import sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path[:0]=[str(PROJECT),str(PROJECT.parent/'hesper_stage'),str(PROJECT.parent/'hesper_nodes_common')]
import blv_kit as kit
from blv_kit import Wall,box,floor,plaque,prism,pipe
from node_rooms import NodeRooms,ROLES,DOORS
from author_standins_blender import build as build_standins
spec=importlib.util.spec_from_file_location('zone4',ROOT/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
p=z.d7
assert not z.plans.ceiling_problems(p)
assert z.plans.max_light_overlap(p)[0]<=4
kit.FOLDERS += [kit.ART/f'textures_{n}/masters' for n in ('k9_lattice','k3_transit','k5_grafted')]
build_standins()
b=kit.Builder('hes_d07.blv',{**ROLES,'fabricator':'hnfab'},PROJECT/'source')
entry=[(3200,3400,6588,6844),(6200,6400,8188,8444)]
cuts={'assembly':[(8064,8264,5280,5664)],
      'capgallery':[(x-30,x+30,y-30,y+30) for x,y in z.GALLERY_MINES],
      'core':entry+[(x-30,x+30,y-30,y+30) for x,y in z.CORE_MINES]}
node=NodeRooms(b,p,splits={'assembly':('x',[9664])},
    doors={'assembly hall to':('assembly',7,58),'capacitor gallery to T2':('t2',8,59)},
    floor_cuts=cuts,accent='motor',middle_walls={'assembly':'motor','core':'motor'},
    wall_roles={('t2','west'):'wall',('t2','east'):'motor'})
node.shell();node.common_contents(z,coupling_radius=1000);node.terminal('t2',81)

# Split all line geometry at its owning sectors, including the cradle centred on their boundary.
for y in (5600,6400):
    for rid,x0,x1 in [('assembly_0',8364,9664),('assembly_1',9664,10964)]:
        b.rooms[rid]+=box((x0,y-200,-512),(x1,y+200,-392),'trim',top='grate',
                          skip=('east',) if rid.endswith('0') else ('west',))
    for x in (8664,9164,9664,10164,10664):
        for rid,r in node.parts.items():
            if r['base']!='assembly':continue
            x0,x1=max(x-150,r['x']),min(x+150,r['x']+r['w'])
            if x1<=x0:continue
            aisle='north' if y==5600 else 'south'
            skip=[aisle]
            if x0>x-150:skip.append('west')
            if x1<x+150:skip.append('east')
            b.rooms[rid]+=box((x0,y-150,-512),(x1,y+150,8),'motor',top='trim',skip=skip)
            face=Wall('y',y+(150 if y==5600 else -150),(0,1 if y==5600 else -1,0))
            b.rooms[rid].append((*face.quad(x0,x1,-512,8,'fabricator')[0],face.fit(x-150,x+150,-512,8)))
        b.decoration('hes_drone_shell',x,y+(175 if y==5600 else -175),-250)
    ay=5850 if y==5600 else 6150
    for x in (8914,9914,10414):
        rid=node.at(x,ay,'assembly')
        b.rooms[rid]+=prism(x,ay,60,-512,48,'motor',top='trim',sides=4)
        b.rooms[rid]+=pipe((x,ay,8),(x,ay+(-400 if y==5600 else 400),8),40,'motor',caps=('start','end'))

# The 900-high console cannot fit under 640; retain its footprint and the 64-unit headroom.
# Its mark is only 64 from the east wall, so the console extends west from the lever's named anchor.
m=next(m for m in p.marks if m['label'].startswith('Line-stop lever'))
x,y=m['x'],m['y'];rid=node.at(x,y,'assembly')
b.rooms[rid]+=box((x-336,y-150,-512),(x+64,y+150,64),'motor',top='trim')
b.decoration('hes_line_lever',x-344,y,-256,270,event=110,cog=110)
b.trigger('line_console',rid,plaque(Wall('x',x-336,(-1,0,0)),y,-384,128,192,'terminal',out=4),110)
m=next(m for m in p.marks if m['label'].startswith('Line placard'))
b.trigger('line_placard','assembly_0',plaque(Wall('y',7192,(0,-1,0)),m['x'],-288,256,160,'glyph'),14)
m=next(m for m in p.marks if m['label'].startswith('Assembly locker'))
b.decoration('hes_colonial_locker',m['x'],m['y'],-512,event=32)
node.plate('line_entry','assembly',cuts['assembly'][0],111)
for i,rect in enumerate(entry):node.plate('core_entry_'+str(i),'core',rect,153)
for base,points,start in [('capgallery',z.GALLERY_MINES,120),('core',z.CORE_MINES,130)]:
    for k,(x,y) in enumerate(points):
        node.plate('mine_'+str(start+k),base,(x-30,x+30,y-30,y+30),start+k)
        b.decoration('hes_kreegan_mine',x,y,-512,cog=start+k+100)
b.decoration('hes_bulwark_wreck',4800,6716,-512,cog=270)
for k in range(3): b.decoration('d07_bulwark_cable_'+str(k+1),4800,6716,-512,cog=260+k)

for light in p.lights:
    light=dict(light)
    if light['fixture'] and 3288<light['y']<4928:light['z']-=round(512*(light['y']-3288)/1640)
    b.plan_light(light,z.plans.FIXTURE_COG)
b.rooms=dict(sorted(b.rooms.items()))
actors=[]
packs=[(1,10240,True),(1,10041,True),(2,10052,False),(2,10041,True),(5,10052,False),
       (6,10052,False),(3,10057,True),(3,10057,True),(9,10141,True),(10,10052,False),
       (10,10241,True),(12,10052,False),(13,10052,False),(11,10052,True),(3,10057,True)]
marks=[m for m in p.marks if m['kind'] in ('monster','boss')]
assert len(marks)==len(packs)
for m,(group,mid,posted) in zip(marks,packs):
    for k in range(m['count']):
        x=m['x']+(k%3-1)*180;y=m['y']+(k//3)*180;zz=p.floors[m['floor']];monster=mid
        if group==1 and mid==10240:
            x=4350+(k%2)*900;y=2800+(k//2)*120;zz=128
            if k==3:monster=10241
        if group==3:x=m['x']+(k*2-1)*140;y=m['y']
        if group==9:x=m['x'];y=m['y']
        if group==10 and mid==10241:y=6000
        if group in (10,12,13) and mid==10052:zz=24  # Flying packs clear the raised beds.
        if group==11:
            x=m['x'];y=m['y']+(k-1)*100
            if k==0:monster=10042
        # Clear the shared dais, the alarm posts and the T2 console without changing actor order.
        if group == 1 and mid == 10041: x = 3800
        if group == 5 and k == 3: y = 5520
        if group == 6: y = 5430+(k//3)*180
        if group == 3 and m['x'] == 8300 and k == 1: y = 8420
        rid=node.at(x,y)
        actors.append(dict(name=m['label'],monster=monster,group=group,position=[x,y,zz],posted=posted,
                           yaw_degrees=90 if group==9 else 270,sector=list(b.rooms).index(rid)+1))
        if group==9:actors.append(dict(actors[-1],monster=10107,group=8,posted=False,name='The Bulwark (free)'))
assert len(actors)==41
assert len(b.rooms)==20 and len(b.mechanisms)==8
# PICKUPS.md: supplies at room edges, with the event also serving as the sprite-swap cog.
pickups = json.loads((PROJECT / 'pickups.json').read_text())
assert len(pickups) == 20 and [p['event'] for p in pickups] == list(range(750, 770))
assert all(p['model'] in ('hes_colony_satchel', 'hes_scrap_bundle') and p['room'] != 'core' for p in pickups)
for pickup in pickups:
    x, y, pickup_z = pickup['position']
    room = node.parents[pickup['room']]
    assert room['x'] + 64 <= x <= room['x'] + room['w'] - 64
    assert room['y'] + 64 <= y <= room['y'] + room['h'] - 64
    assert pickup_z == room['z']
    b.decoration(pickup['model'], x, y, pickup_z, event=pickup['event'], cog=pickup['event'])

node.validate_shapes()
b.export({'pickups': pickups, 'arrivals':{'blast_door':{'position':[4800,300,0],'direction_degrees':90},
                     'service_tunnel':{'position':[3424,12200,-512],'direction_degrees':270}},
          'door_ids':{**DOORS,'assembly':7,'t2':8},'chest_events':{'30':0,'31':1,'32':2,'33':3},
          'actors':actors,'couplings':z.couplings(),'gallery_mines':z.GALLERY_MINES,'core_mines':z.CORE_MINES,
          'mine_path':z.MINE_PATH,'arc_light_positions':[[x,5472,-420] for x in z.ARC_X],
          'pending_dressing':'Capacitor bank positions await approval: the stated wall spacing overlaps marked mines/path.'})
next(s for s in b.metadata['surfaces'] if s['id']=='vault')['cog_number']=55
(PROJECT/'source/hes_d07.geometry.yml').write_text(json.dumps(b.metadata,indent=2)+'\n')

sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
