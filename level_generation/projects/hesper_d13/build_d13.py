"""Compile Deepwell; actors and exits derive from the plan and the neighbouring build records."""
import json
import math
import shutil
import sys
import yaml
from layout import ARRIVALS, PLAN, PROJECT, ROOT, ROOMS, checks, zone
sys.path.insert(0,str(PROJECT.parent/'hesper_stage'))
from blv_build import build
semantic=json.loads((PROJECT/'source/hes_d13.semantic.json').read_text())
assert semantic['completed_through']=='escape'
rows={int(r[0]):r for r in (line.split('\t') for line in
      (ROOT/'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if r[0].isdigit()}
staged={m['id']:m for m in yaml.safe_load((PROJECT.parent/'hesper_stage/monsters.yml').read_text())['monsters']}
actors=[]

def sector(x,y,z):
    for name,b in semantic['room_bounds'].items():
        if b[0]-.1<=x<=b[2]+.1 and b[1]-.1<=y<=b[3]+.1 and b[4]-.1<=z<=b[5]+.1:
            return semantic['sectors'].index('room_'+name)+1
    raise ValueError((x,y,z))


def available(room,x,y,radius):
    r=ROOMS[room]
    if not(r['x']+radius+20<x<r['x']+r['w']-radius-20 and r['y']+radius+20<y<r['y']+r['h']-radius-20):return False
    if room=='control' and math.hypot(x-zone.TAP_CENTRE[0],y-zone.TAP_CENTRE[1])<950+radius:return False
    for rid,x0,y0,z0,x1,y1,z1 in semantic['obstacles']:
        if rid==room and x0-radius<x<x1+radius and y0-radius<y<y1+radius:return False
    return all(abs(r['z']-a['position']['z'])>200 or math.hypot(x-a['position']['x'],y-a['position']['y'])>radius+a['radius']+32 for a in actors)


for mark,(rid,group,monster) in zip([m for m in PLAN.marks if m['kind']=='monster'],[
    ('exch',1,10302),('vein',1,10322),('control',2,10057),('control',5,10242),('control',6,10242),
    ('loop',7,10302),('loop',8,10242),('upper',3,10322)]):
    for index in range(mark['count']):
        row=rows[monster];size=staged[monster];radius=size['radius']
        positions=[(round(mark['x']+d*math.cos(a*math.pi/6)),round(mark['y']+d*math.sin(a*math.pi/6)))
                   for d in range(0,2001,100) for a in range(12)]
        if monster == 10302:
            # Pyre Hounds are over three metres long; keep the whole bodies clear within the flat aisles.
            points = {1: [(2800, 1000), (3200, 1000), (3600, 1000), (3000, 1350), (3400, 1350)],
                      7: [(4500, 7100), (4900, 7420), (5300, 7100)]}
            positions = [points[group][index]]
        if monster == 10322:
            # Keep native wildlife beyond the tap and at the far end of the collapse gallery.
            points = {1: [(10000, 3500), (10300, 3500), (10150, 3800)],
                      3: [(7100, 5900), (7350, 5900), (7225, 6200)]}
            positions = [points[group][index]]
        x,y=next((x,y) for x,y in positions if available(rid,x,y,radius));z=ROOMS[rid]['z']
        actors.append(dict(actor_index=len(actors),name=row[1],npc_id=0,attributes=0x10000 if group>=5 else 0,
            hp=int(row[4]),hostility_type=int(row[12]),monster_info_id=monster,monster_id=monster,
            radius=radius,height=size['height'],move_speed=0 if group==2 else int(row[13]),
            position=dict(x=x,y=y,z=z),initial_yaw_units=1536,immobile=group==2,sprite_ids=[0]*4,
            sector_id=sector(x,y,z),current_action_animation=0,carried_item_id=0,group=group,ally=0,unique_name_index=0))
assert len(actors)==28
assert sum(a['monster_id']==10302 for a in actors)==8
exits={}
for name,project,file,key,mapfile in [('shaft','hesper_d12','source/hes_d12.semantic.json','shaft_head','hes_d12.blv'),
                                      ('pad','hesper_out4','out4_build.json','pad_lift','hes_out4.odm')]:
    data=json.loads((PROJECT.parent/project/file).read_text());v=data.get('arrivals',data)[key]
    pos=v['position'] if isinstance(v,dict) else v[:3];degrees=v['direction_degrees'] if isinstance(v,dict) else v[3]
    exits[name]=dict(map=mapfile,key=key,x=pos[0],y=pos[1],z=pos[2],direction=round(degrees/360*2048)%2048)
reset=dict(map='0',x=ARRIVALS['tap_ring']['position'][0],y=ARRIVALS['tap_ring']['position'][1],z=0,direction=0)
def lua(v):
    if isinstance(v,dict):return '{'+','.join('['+json.dumps(k)+']='+lua(x) for k,x in v.items())+'}'
    return json.dumps(v)
report=build(PROJECT,'hes_d13.blv',{'D13_EXITS':lua(exits),'D13_RESET':lua(reset)},'shaft_bottom',[],actors)
scene_path=PROJECT/'runtime/hes_d13.scene.yml';scene=json.loads(scene_path.read_text())
item_rows={int(r[0]):r for r in (line.split('\t') for line in
    (ROOT/'output/hesper_stage/assets_editor_dev/worlds/hesper/data_tables/items.txt').read_text().splitlines()) if r[0].isdigit()}
objects=[line.split('\t') for line in (ROOT/'assets_dev/engine/data_tables/object_list.txt').read_text(encoding='latin1').splitlines()[1:]]
mark=next(m for m in PLAN.marks if m['kind']=='item');x,y,z=mark['x'],mark['y'],80
raw=bytearray(36);raw[:4]=(11304).to_bytes(4,'little')
object_index,object_row=next((i,r) for i,r in enumerate(objects) if int(r[2])==int(item_rows[11304][11]))
sprite=int(object_row[7])
scene['initial_state']['sprite_objects']=[dict(sprite_object_index=0,sprite_id=sprite,object_description_id=object_index,
    position=dict(x=x,y=y,z=z),velocity=dict(x=0,y=0,z=0),yaw_angle=0,sound_id=0,attributes=0,sector_id=sector(x,y,z),
    time_since_created=0,temporary_lifetime=0,glow_radius_multiplier=0,spell_id=0,spell_level=0,spell_skill=0,field54=0,
    spell_caster_pid=0,spell_target_pid=0,lod_distance=0,spell_caster_ability=0,initial_position=dict(x=0,y=0,z=0),raw_containing_item_hex=raw.hex().upper())]
scene_path.write_text(json.dumps(scene,indent=2)+'\n')
tree=PROJECT/'runtime/worlds/hesper';shutil.copy2(scene_path,tree/'maps'/scene_path.name)
(tree/'effects').mkdir(exist_ok=True);shutil.copy2(PROJECT/'source/effects.yml',tree/'effects/d13.yml')
report.update(actors=len(actors),arrivals=ARRIVALS,exits=exits,
    actor_groups={str(g):[a['actor_index'] for a in actors if a['group']==g] for g in (1,2,3,5,6,7,8)},
    actor_positions={str(a['actor_index']):a['position'] for a in actors},checks=checks('final'))
assert report['sectors']==16 and report['doors']==6
(PROJECT/'d13_build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
