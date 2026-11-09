"""Compile D15; source both external destinations from their owning build records."""
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path
import yaml
PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(PROJECT.parent/'hesper_stage'))
from blv_build import build
spec=importlib.util.spec_from_file_location('zone4',ROOT/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone=importlib.util.module_from_spec(spec);spec.loader.exec_module(zone)
PLAN=zone.d15
semantic=json.loads((PROJECT/'source/hes_d15.semantic.json').read_text())
rows={int(r[0]):r for r in (l.split('\t') for l in (ROOT/'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if r[0].isdigit()}
sizes={m['id']:(m['radius'],m['height']) for m in yaml.safe_load((PROJECT.parent/'hesper_stage/monsters.yml').read_text())['monsters']}
packs=[(1,[10322]*4),(1,[10322]*4),(1,[10322]*3),(1,[10322]*3),(2,[10322]*4),(2,[10322]*5),
       (3,[10322]*6),(4,[10022]*2+[10322]*4),(5,[10322]*6),(5,[10322]*4),
       (6,[10002]*6),(6,[10002]*6),(7,[10057]*4),(7,[10022]*4),(7,[10022]*2),(9,[10022]*3),(8,[10057]*2)]
marks=[m for m in PLAN.marks if m['kind']=='monster']
actors=[]


def sector_at(x,y,z):
    candidates=[(name,bd) for name,bd in semantic['room_bounds'].items()
                if bd[0]-1<=x<=bd[2]+1 and bd[1]-1<=y<=bd[3]+1 and bd[4]-1<=z<=bd[5]+1]
    assert candidates,(x,y,z)
    name=min(candidates,key=lambda p:(p[1][2]-p[1][0])*(p[1][3]-p[1][1]))[0]
    return semantic['sectors'].index('room_'+name)+1


def allowed(x,y,z,radius,room):
    if not(room['x']+radius+24<x<room['x']+room['w']-radius-24 and
           room['y']+radius+24<y<room['y']+room['h']-radius-24):return False
    cut=semantic['chamfers'].get(room['id'],0)
    dx=min(x-room['x'],room['x']+room['w']-x)
    dy=min(y-room['y'],room['y']+room['h']-y)
    if dx+dy<cut+radius*math.sqrt(2):return False
    for xa,ya,xb,yb in ((3300,200,5700,800),(4880,-150,7320,670),(4100,1640,6500,2280)):
        if xa-radius<x<xb+radius and ya-radius<y<yb+radius:return False
    for xa,ya,za,xb,yb,zb in semantic['dressing_solids']:
        if z<zb and z>=za and xa-radius<x<xb+radius and ya-radius<y<yb+radius:return False
    if z==0 and any(xa-radius<x<xb+radius and ya-radius<y<yb+radius
                    for xa,ya,xb,yb in semantic['ramp_bounds']):return False
    if room['id']=='shed':
        if y>2850:return False  # clear the breaker and locked locker
        for k in range(6):
            px,py=8500+k%3*450,2150+k//3*500
            if px-radius<x<px+240+radius and py-radius<y<py+280+radius:return False
    if room['id']=='pumpgal' and x<16300 and (y<4900 or y>5800):return False
    if room['id']=='junction':
        raised=(x<13400 and 9900<y<11900) or (x>15100 and 11700<y<12100) or (x>14800 and y<9800)
        if (z==256)!=raised:return False
        if z==256 and not (12492+radius<x<13400-radius and 9900+radius<y<11900-radius):return False
    return all(math.hypot(x-a['position']['x'],y-a['position']['y'])>radius+a['radius']+20
               for a in actors if abs(z-a['position']['z'])<300)


# Preserve actor indices and every Kreegan placement while regrouping the 43 former drones into 11 packs.
gloamer_points = []
for rid, centres in [('linew', [(3200, 1120), (4350, 1120), (5500, 1120), (6650, 1120)]),
                     ('cut', [(14600, 4400), (15200, 4400), (14600, 5500), (15200, 5500),
                              (14600, 6600), (15200, 6600), (15000, 7350)])]:
    room = next(r for r in PLAN.rooms if r['id'] == rid)
    for cx, cy in centres:
        for dx, dy in [(-100, -120), (100, -120), (-100, 120), (100, 120)]:
            gloamer_points.append((room, cx + dx, cy + dy, PLAN.floors[room['floor']]))
gloamer_points.pop()  # The final den is a three-member pack.
assert len(gloamer_points) == 43
gloamers = iter(gloamer_points)

for n,(m,(group,ids)) in enumerate(zip(marks,packs)):
    assert m['count']==len(ids)
    z=PLAN.floors[m['floor']]+(256 if n==12 else 0)
    room=next(r for r in PLAN.rooms if r['x']<=m['x']<=r['x']+r['w'] and r['y']<=m['y']<=r['y']+r['h']
              and r['floor']==m['floor'])
    for monster in ids:
        radius,height=sizes[monster];found=False
        for d in range(0,1400,100):
            for angle in range(0,360,30):
                x=round(m['x']+d*math.cos(math.radians(angle)));y=round(m['y']+d*math.sin(math.radians(angle)))
                if allowed(x,y,z,radius,room):found=True;break
            if found:break
        if monster == 10322:
            den, x, y, z = next(gloamers)
            assert allowed(x, y, z, radius, den), ('Gloamer den', x, y, z)
            found = True
        assert found,(n,monster)
        row=rows[monster];immobile=monster==10057 or (monster!=10322 and n in (7,14))
        actors.append({'actor_index':len(actors),'name':row[1],'npc_id':0,'attributes':0x10000 if group==9 else 0,
          'hp':int(row[4]),'hostility_type':int(row[12]),'monster_info_id':monster,'monster_id':monster,
          'radius':radius,'height':height,'move_speed':0 if monster==10057 else int(row[13]),
          'position':{'x':x,'y':y,'z':z},'initial_yaw_units':1024 if n==7 else 0 if n<=5 or n in (10,11) else 1536,'immobile':immobile,
          'sprite_ids':[0,0,0,0],'sector_id':sector_at(x,y,z),'current_action_animation':0,
          'carried_item_id':0,'group':group,'ally':0,'unique_name_index':0})
assert len(actors)==72


def fields(a):
    x,y,z=a['position'];return f'x={x}, y={y}, z={z}, direction={round(a["direction_degrees"]/360*2048)%2048}'


under=json.loads((PROJECT.parent/'hesper_undervault/source/hes_undervault.semantic.json').read_text())['arrivals']['deep_stair_bulkhead']
core_path=PROJECT.parent/'hesper_d12/source/hes_d12.semantic.json'
core_ready=core_path.exists() and (PROJECT.parent/'hesper_d12/runtime/worlds/hesper/maps/hes_d12.blv').exists()
core=fields(json.loads(core_path.read_text())['arrivals']['service_lift']) if core_ready else 'nil'
if not core_ready:print('BLOCKED D12 round trip: missing hesper_d12 semantic arrival service_lift; no guessed coordinates.')
chests=['Maintenance Bay','Siding strongbox','Tram Shed','Pump Gallery','Breach Burrow',
        {'name':'Root Lock Engram Core','fixed':[11332],'random':False,'gold':0}]
report=build(PROJECT,'hes_d15.blv',{'D15_UNDER':fields(under),'D15_CORE':core,
             'D15_WEST':fields(semantic['arrivals']['tram_west']),'D15_EAST':fields(semantic['arrivals']['tram_east'])},
             arrival='deep_stair',chests=chests,actors=actors)
scene_path=PROJECT/'runtime/hes_d15.scene.yml';scene=json.loads(scene_path.read_text())
for i,chest in enumerate(scene['loot_containers']):
    chest['presentation']='kreegan pod' if i==4 else 'colonial locker'
    if i<5:
        # shortcut: native T6 and fixed gold until the integrator supplies the Hesper H3 loot-pool implementation.
        chest.update(random_treasure_level=6,gold=13500 if i==2 else 9000)
scene['initial_state']['sprite_objects']=[]
scene_path.write_text(json.dumps(scene,indent=2)+'\n')
shutil.copy2(scene_path,PROJECT/'runtime/worlds/hesper/maps'/scene_path.name)
report.update(map_id=9136,actors=len(actors),d12_exit_ready=core_ready,
              actor_groups={str(g):[a['actor_index'] for a in actors if a['group']==g] for g in range(1,10)})
(PROJECT/'d15_build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
