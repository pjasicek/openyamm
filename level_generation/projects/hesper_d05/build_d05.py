"""Compile and validate D5, then assemble its stage-only map, scene, Lua and boss behaviour."""
import base64
import csv
import json
import shutil
import struct
import sys
from pathlib import Path
import yaml
from plan import ROOT, PROJECT, PLAN, check

sys.path.insert(0,str(PROJECT.parent/'hesper_stage'))
from blv_build import build

check()
stage=ROOT/'output/hesper_stage/assets_editor_dev'
semantic=json.loads((PROJECT/'source/hes_d05.semantic.json').read_text())
with (ROOT/'design/kreegan_world/data/monster_data.txt').open(newline='') as stream:
    rows={int(row[0]):row for row in csv.reader(stream,delimiter='\t') if row and row[0].isdigit()}
sizes={m['id']:(m['radius'],m['height']) for m in yaml.safe_load((PROJECT.parent/'hesper_stage/monsters.yml').read_text())['monsters']}
actors=[]
for a in semantic['actors']:
    mid=a['monster'];row=rows[mid];radius,height=sizes[mid];x,y,z=a['position']
    actors.append({'actor_index':len(actors),'name':a['name'],'npc_id':0,'attributes':0,'hp':int(row[4]),
                   'hostility_type':int(row[12]),'monster_info_id':mid,'monster_id':mid,'radius':radius,'height':height,
                   'move_speed':int(row[13]),'position':{'x':x,'y':y,'z':z},
                   'initial_yaw_units':round(a['yaw_degrees']/360*2048)%2048,'immobile':a['posted'],
                   'sprite_ids':[0,0,0,0],'sector_id':a['sector'],'current_action_animation':0,'carried_item_id':0,
                   'group':a['group'],'ally':0,'unique_name_index':0})
# This dependency is deliberately explicit: never invent the outdoor map's arrival coordinates.
exit_record=PROJECT.parent/'hesper_out3/out3_build.json'
exit_ready=exit_record.exists()
if exit_ready:
    out=json.loads(exit_record.read_text())
    destination=out['arrivals']['d05_root_door']
    x,y,z=destination['position'];direction=round(destination['direction_degrees']/360*2048)%2048
    arrival=f'{x}, {y}, {z}, {direction}, 0, 0, 0, 0'
else:
    arrival='0, 0, 0, 0, 0, 0, 0, 0'
chests=[{'name':'Armoury A','fixed':[11002,11028,11026,11331,11331,11331],'random':False,'gold':0},
        {'name':'Loom Control B','fixed':[11221,11331],'random':False,'gold':25000},
        {'name':'Jammer Cradle C','fixed':[11470,11475],'random':False,'gold':0}]
chests += [dict(name='Kreegan pod H2',gold=4000,random=True) for _ in range(5)]
report=build(PROJECT,'hes_d05.blv',{'BROOD_ARRIVAL':arrival},'from_hes_out3',chests,actors)
runtime=PROJECT/'runtime';tree=runtime/'worlds/hesper'
# Check the compiled sector-light lists, not just the authored marker positions.
from map_export import parse_blv_file
native=parse_blv_file(runtime/'hes_d05.blv')['payload']
assert native['version']==8
sector_names=['empty',*sorted(semantic['sectors'])]
light_owners={};cursor=0
for name,sector in zip(sector_names,native['sectors']):
    # MM8 sector records place lightCount at 0x58 (the Python summary uses MM7's offset).
    count=struct.unpack_from('<H',base64.b64decode(sector['raw_record_base64']),0x58)[0]
    for index in native['sector_light_data'][cursor:cursor+count]:light_owners[index]=name
    cursor+=count
assert cursor==len(native['sector_light_data'])==13
for light in native['lights']:
    group=struct.unpack_from('<H',base64.b64decode(light['raw_record_base64']),16)[0]
    if 21<=group<=26:
        assert light_owners[light['index']]=='room_shaft_0_0_'+('0' if group<=23 else '1')
        assert (light['radius'],light['red'],light['green'],light['blue'])==(900,120,230,255)
for room,z in [('root_stair',-1024),('ledge1',1024),('ledge2',3072)]:
    sector=sector_names.index('room_'+room)
    heights={native['vertices'][face['vertex_indices'][0]]['z'] for face in native['faces']
             if face['room_number']==sector and face['texture_name']=='hkfloor'}
    rise,steps=16,64
    assert {z+rise*k for k in range(1,steps+1)}<=heights,(room,sorted(heights))
assert actors[68]['position']==dict(x=4500,y=4000,z=4096)
assert all(actor['immobile'] for actor in actors if actor['group']==8)
chest_c=next(entity for entity in native['entities'] if entity['event_id_secondary']==32)
assert chest_c['position']==dict(x=3200,y=5500,z=4480)

# An unbuilt exit reports its missing destination instead of sending the party to made-up coordinates.
if not exit_ready:
    text=(runtime/'hes_d05.lua').read_text()
    text=text.replace('evt.MoveToMap('+arrival+', "hes_out3.odm")',
                      'evt.StatusText("The blast door: the way is not yet open.")')
    (runtime/'hes_d05.lua').write_text(text)
    shutil.copy2(runtime/'hes_d05.lua',tree/'events/maps/hes_d05.lua')
scene=json.loads((runtime/'hes_d05.scene.yml').read_text())
# The shared compiler defaults to H1; D5's five random pods use medium native treasure, pending Hesper loot rules.
for chest in scene['loot_containers'][3:]:chest['random_treasure_level']=4
item_rows={}
for path in [stage/'engine/data_tables/items.txt',stage/'worlds/hesper/data_tables/items.txt']:
    with path.open(encoding='latin1',newline='') as stream:
        item_rows.update({int(r[0]):r for r in csv.reader(stream,delimiter='\t') if r and r[0].isdigit()})
objects=[int(line.split('\t')[2]) for line in (stage/'engine/data_tables/object_list.txt')
         .read_text(encoding='latin1').splitlines()[1:] if line.strip()]
items=[]
for mid,x,y,z in [(11300,5730,4900,4096),(11300,5798,4900,4096),(11302,5764,4970,4096)]:
    sprite=int(item_rows[mid][11]);raw=bytearray(36);struct.pack_into('<I',raw,0,mid)
    items.append({'sprite_object_index':len(items),'sprite_id':sprite,'object_description_id':objects.index(sprite),
                  'position':dict(x=x,y=y,z=z),'velocity':dict(x=0,y=0,z=0),'yaw_angle':0,'sound_id':0,'attributes':0,
                  'sector_id':0,'time_since_created':0,'temporary_lifetime':0,'glow_radius_multiplier':0,'spell_id':0,
                  'spell_level':0,'spell_skill':0,'field54':0,'spell_caster_pid':0,'spell_target_pid':0,'lod_distance':0,
                  'spell_caster_ability':0,'initial_position':dict(x=0,y=0,z=0),'raw_containing_item_hex':raw.hex().upper()})
scene['initial_state']['sprite_objects']=items
(runtime/'hes_d05.scene.yml').write_text(json.dumps(scene,indent=2)+'\n')
shutil.copy2(runtime/'hes_d05.scene.yml',tree/'maps/hes_d05.scene.yml')
(tree/'behaviors').mkdir(exist_ok=True)
shutil.copy2(PROJECT/'source/hes_vhorrax_d5.lua',tree/'behaviors/hes_vhorrax_d5.lua')
report.update(actors=len(actors),chests=len(chests),ground_items=len(items),exit_ready=exit_ready)
(PROJECT/'d05_build.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['doors']==24 and report['actors']==69 and report['chests']==8
print(json.dumps(report))
