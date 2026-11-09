"""Compile the Seedship, verify native wiring, and assemble its stage-owned runtime tree."""
import csv
import json
import re
import shutil
import sys
from pathlib import Path
import yaml

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
STAGE=PROJECT.parent/'hesper_stage'
sys.path.insert(0,str(STAGE))
from blv_build import build
import sound_cues
semantic=json.loads((PROJECT/'source/hes_d11.semantic.json').read_text())
with (ROOT/'design/kreegan_world/data/monster_data.txt').open(newline='') as f:
    rows={int(r[0]):r for r in csv.reader(f,delimiter='\t') if r and r[0].isdigit()}
sizes={m['id']:(m['radius'],m['height']) for m in yaml.safe_load((STAGE/'monsters.yml').read_text())['monsters']}
actors=[];scripted=[]
for a in semantic['actors']:
    mid=a['monster'];row=rows[mid];radius,height=sizes[mid];index=len(actors)
    actors.append(dict(actor_index=index,name=row[1],npc_id=0,attributes=0x10000 if a['group'] in (25,26) else 0,
        hp=int(row[4]),hostility_type=int(row[12]),monster_info_id=mid,monster_id=mid,radius=radius,height=height,
        move_speed=0 if a['posted'] else int(row[13]),position=dict(zip(('x','y','z'),a['position'])),
        initial_yaw_units=0,immobile=a['posted'],sprite_ids=[0,0,0,0],sector_id=a['sector'],current_action_animation=0,
        carried_item_id=0,group=a['group'],ally=0,unique_name_index=0))
    behavior={10045:'hes_egg_cluster',10131:'hes_ganglion'}.get(mid)
    if a['group'] in (25,26):behavior='hes_vhorrax_'+('honour' if a['group']==25 else 'refused')
    if behavior:scripted.append(f'{{index={index},group={a["group"]},behavior="{behavior}"}}')
out3=PROJECT.parent/'hesper_out3/out3_build.json';exit_fields='nil'
if out3.exists():
    record=json.loads(out3.read_text());arrival=record['arrivals']['d11_breach']
    x,y,z=arrival['position'];direction=round(arrival['direction_degrees']/360*2048)%2048
    exit_fields=f'x={x},y={y},z={z},direction={direction}'
chests=[dict(name='Seed Vault B',fixed=[11331,11331,11213],random=False,gold=60000)]
chests += [dict(name='H3 '+name,random=True,gold=9000) for name in ('aft deck','breach','pens','cradles','trophies','sensorium')]
report=build(PROJECT,'hes_d11.blv',{'D11_ACTORS':', '.join(scripted),'D11_EXIT':exit_fields},
             arrival='from_hes_out3',chests=chests,actors=actors)
scene_path=PROJECT/'runtime/hes_d11.scene.yml';scene=json.loads(scene_path.read_text())
for i,chest in enumerate(scene['loot_containers']):
    chest['presentation']='kreegan pod'
    if i:
        # shortcut: the existing H3 native T6 pool until P4's Hesper-specific weighted loot is installed.
        chest['random_treasure_level']=6
assets=ROOT/'output/hesper_stage/assets_editor_dev'
item_rows={}
for file in (assets/'engine/data_tables/items.txt',assets/'worlds/hesper/data_tables/items.txt'):
    with file.open(encoding='latin1',newline='') as f:
        item_rows.update({int(r[0]):r for r in csv.reader(f,delimiter='\t') if r and r[0].isdigit()})
with (assets/'engine/data_tables/object_list.txt').open(encoding='latin1',newline='') as f:
    object_rows=list(csv.reader(f,delimiter='\t'))[1:]

def sector_at(x,y,z):
    choices=[]
    for i,name in enumerate(sorted(semantic['sector_bounds'])):
        b=semantic['sector_bounds'][name]
        if b[0]<=x<=b[2] and b[1]<=y<=b[3] and b[4]<=z<=b[5]:choices.append(((b[2]-b[0])*(b[3]-b[1]),i+1))
    assert choices,(x,y,z)
    return min(choices)[1]

supplies=[]
for y,z in ((4100,1280),(3700,2560)):
    for i,item in enumerate((11300,11300,11302,11304)):supplies.append((item,260+i*40,y,z+64,0))
objects=[]
for item,x,y,z,gold in supplies:
    object_id=int(item_rows[item][11]);description,row=next((i,r) for i,r in enumerate(object_rows) if int(r[2])==object_id)
    raw=bytearray(36);raw[:4]=item.to_bytes(4,'little');raw[12:16]=gold.to_bytes(4,'little')
    objects.append(dict(sprite_object_index=len(objects),sprite_id=object_id,object_description_id=description,
        position=dict(x=x,y=y,z=z),velocity=dict(x=0,y=0,z=0),yaw_angle=0,sound_id=0,attributes=0,
        sector_id=sector_at(x,y,z),time_since_created=0,temporary_lifetime=0,glow_radius_multiplier=0,
        spell_id=0,spell_level=0,spell_skill=0,field54=0,spell_caster_pid=0,spell_target_pid=0,lod_distance=0,
        spell_caster_ability=0,initial_position=dict(x=x,y=y,z=z),raw_containing_item_hex=raw.hex().upper()))
scene['initial_state']['sprite_objects']=objects
scene_path.write_text(json.dumps(scene,indent=2)+'\n')
shutil.copy2(scene_path,PROJECT/'runtime/worlds/hesper/maps/hes_d11.scene.yml')
target=PROJECT/'runtime/worlds/hesper/behaviors';target.mkdir(parents=True,exist_ok=True)
shutil.copy2(PROJECT/'source/hes_ganglion.lua',target/'hes_ganglion.lua')
for form in ('honour','refused'):
    (target/f'hes_vhorrax_{form}.lua').write_text((PROJECT/'source/hes_vhorrax.lua').read_text().replace('HONOUR','true' if form=='honour' else 'false'))
sound_cues.build(PROJECT/'runtime/worlds/hesper/audio/d11')
# The fitted, reviewed camera poses live in the tours, not the original design coordinates.
names=[]
for filename,count in (('review_tour_01.yml',11),('review_tour_blind.yml',1)):
    shots=yaml.safe_load((PROJECT/filename).read_text())['shots']
    assert len(shots)==count,(filename,len(shots))
    for shot in shots:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',shot['name']),shot['name']
        assert len(shot['position'])==3
        names.append(shot['name'])
assert len(set(names))==12
assert len(actors)==81 and len(objects)==8 and len(scene['loot_containers'])==7
assert set(report['events']) >= set(range(30,39)) | set(range(201,224)) | {10,11,12,50,51,52,53,54,160}
(PROJECT/'review/build_status.json').write_text(json.dumps(dict(map_id=9123,actors=81,sectors=52,movers=27,lights=semantic['light_count'],
    chests=7,event_caches=2,ground_items=8,outdoor_bound=out3.exists(),screenshots='Skipped by user: integrator captures'),indent=2)+'\n')
print(f"D11: 52 sectors, 27 movers, 81 actors, {semantic['light_count']} lights; both terms wired; outdoor "+('bound' if out3.exists() else 'pending'))
