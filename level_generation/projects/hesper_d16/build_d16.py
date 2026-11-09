"""Compile D16 and assemble its scene and authored Lua into the isolated Hesper runtime tree."""
import csv
import json
import shutil
import struct
import sys
from pathlib import Path
import yaml

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(PROJECT.parent/'hesper_stage'))
from blv_build import build

semantic=json.loads((PROJECT/'source/hes_d16.semantic.json').read_text())
metadata=json.loads((PROJECT/'source/hes_d16.geometry.yml').read_text())
glb=(PROJECT/'source/hes_d16.glb').read_bytes()
gltf=json.loads(glb[20:20+struct.unpack_from('<I',glb,12)[0]])
assert semantic['sectors']==[n['name'].lower() for n in gltf['nodes'] if n['name'].startswith('ROOM_')]
rows={int(r[0]):r for r in csv.reader((ROOT/'design/kreegan_world/data/monster_data.txt').read_text().splitlines(),
                                     delimiter='\t') if r and r[0].isdigit()}
sizes={r['id']:(r['radius'],r['height']) for r in yaml.safe_load((PROJECT.parent/'hesper_stage/monsters.yml').read_text())['monsters']}
actors=[]
for a in semantic['actors']:
    mid=a['monster']; row=rows[mid]; radius,height=sizes[mid]; x,y,z=map(round,a['position'])
    actors.append(dict(actor_index=len(actors),name=a['name'],npc_id=0,attributes=0,hp=int(row[4]),
                       hostility_type=int(row[12]),monster_info_id=mid,monster_id=mid,radius=radius,height=height,
                       move_speed=int(row[13]),position=dict(x=x,y=y,z=z),initial_yaw_units=round(a['yaw_degrees']/360*2048)%2048,immobile=a['posted'],
                       sprite_ids=[0,0,0,0],sector_id=a['sector'],current_action_animation=0,
                       carried_item_id=0,group=a['group'],ally=0,unique_name_index=0))
boss=next(i for i,a in enumerate(actors) if a['group']==9)
record=PROJECT.parent/'hesper_out4/out4_build.json'
def crown_arrival(key):
    if not record.exists(): return 'nil'
    arrival=json.loads(record.read_text())['arrivals'][key]
    x,y,z=arrival['position']; direction=round(arrival['direction_degrees']/360*2048)%2048
    return f'{{{x},{y},{z},{direction},0,0,0,0,"hes_out4.odm"}}'

arc_indices=[next(i for i,l in enumerate(metadata['lights']) if l['id']==name) for name in ('L2','L3','L4')]
assert min(arc_indices)>0  # Negative ids address a single BLV light, bypassing MM8 light groups.
def lua_points(points): return ', '.join('{'+','.join(str(v) for v in p)+'}' for p in points)
chests=[dict(name='T1 Master locker',random=True,gold=18000),
        dict(name='Galleries locker',random=True,gold=12000),dict(name='Graft salvage pod',random=True,gold=12000),
        dict(name='Quiet-path vault',fixed=[11331,11113],random=False,gold=0)]
report=build(PROJECT,'hes_d16.blv',{'BOSS_INDEX':str(boss),'CROWN_DOOR_BINDING':crown_arrival('d16_door'),
             'CROWN_HATCH_BINDING':crown_arrival('d16_hatch'),'ARC_LIGHT_BINDINGS':','.join(str(-i) for i in arc_indices),
             'COUPLING_BINDINGS':lua_points(semantic['couplings'])},arrival='blast_door',chests=chests,actors=actors)
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_blv_file
native=parse_blv_file(PROJECT/'runtime/hes_d16.blv')['payload']
for index,pos in zip(arc_indices,semantic['arc_light_positions']):
    assert [native['lights'][index][key] for key in ('x','y','z')]==pos
assert report['sectors']==21 and report['doors']==7
runtime=PROJECT/'runtime'; tree=runtime/'worlds/hesper'
scene=json.loads((runtime/'hes_d16.scene.yml').read_text())
scene['loot_containers'][2]['presentation']='kreegan pod'
# shortcut: native T6 treasure, as D8, until the Hesper H3 pool and its consumable/salvage rolls are staged.
for i in range(3): scene['loot_containers'][i]['random_treasure_level']=6

# Resolve native object art from the same stand-in declarations that stage.py uses for each custom item.
objects=list(csv.reader((ROOT/'assets_dev/engine/data_tables/object_list.txt').read_text().splitlines(),delimiter='\t'))[1:]
native_items=list(csv.reader((ROOT/'assets_dev/engine/data_tables/items.txt').read_text(encoding='latin-1').splitlines(),delimiter='\t'))
sprites={}
for row in native_items:
    if len(row)>11 and row[0].isdigit() and row[11].isdigit() and int(row[11])>0: sprites.setdefault(row[1],row[11])
bindings={r['id']:r for r in yaml.safe_load((PROJECT.parent/'hesper_stage/items.yml').read_text())['items']}
scene['initial_state']['sprite_objects']=[]
def loose(item,x,y,z,sector,gold=0):
    sprite='85' if gold else sprites[bindings[item].get('ground',bindings[item]['icon'])]
    object_index,row=next((i,r) for i,r in enumerate(objects) if len(r)>7 and r[2]==sprite)
    raw=bytearray(36); struct.pack_into('<I',raw,0,item); struct.pack_into('<I',raw,12,gold)
    obj={key:0 for key in ('yaw_angle','sound_id','attributes','time_since_created','temporary_lifetime',
                          'glow_radius_multiplier','spell_id','spell_level','spell_skill','field54',
                          'spell_caster_pid','spell_target_pid','lod_distance','spell_caster_ability')}
    obj.update(sprite_object_index=len(scene['initial_state']['sprite_objects']),sprite_id=int(row[7]),
               object_description_id=object_index,sector_id=semantic['sectors'].index('room_'+sector)+1,
               position=dict(x=x,y=y,z=z),initial_position=dict(x=x,y=y,z=z),velocity=dict(x=0,y=0,z=0),
               raw_containing_item_hex=raw.hex())
    scene['initial_state']['sprite_objects'].append(obj)
loose(11304,2950,6150,-352,'t1')
for k,item in enumerate((11300,11300,11302,11302,11303)):
    loose(item,6500+100*k,7750,-352,'t3')
(runtime/'hes_d16.scene.yml').write_text(json.dumps(scene,indent=2)+'\n')
shutil.copy2(runtime/'hes_d16.scene.yml',tree/'maps/hes_d16.scene.yml')
(tree/'behaviors/bosses').mkdir(parents=True,exist_ok=True); (tree/'effects').mkdir(exist_ok=True)
source=(PROJECT/'source/conductor.lua').read_text()
for stage in range(4):
    (tree/f'behaviors/bosses/conductor_{stage}.lua').write_text(source.replace('CONDUCTOR_STAGE',str(stage)))
shutil.copy2(PROJECT/'source/effects.yml',tree/'effects/d16.yml')
report.update(actors=len(actors),boss_index=boss,chests=4,loose_items=6,gold_piles=0,
              crown_exits_ready=record.exists(),arrivals=semantic['arrivals'])
(PROJECT/'d16_build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
