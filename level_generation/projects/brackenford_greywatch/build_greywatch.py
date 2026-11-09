"""Compile Greywatch and assemble native geometry, generated state and authored Lua.

This builds an intermediate runtime package. The complete two-map acceptance gates remain separate.
"""
import csv
import json
from pathlib import Path
import struct
import subprocess
import sys

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
SOURCE = PROJECT / 'source'
OUTPUT = PROJECT / 'runtime/worlds/mm8'
(OUTPUT/'maps').mkdir(parents=True,exist_ok=True)
(OUTPUT/'events/maps').mkdir(parents=True,exist_ok=True)
subprocess.run([str(ROOT/'build/tools/mm9_compile_indoor_source'),str(SOURCE/'lg02.glb'),
                str(SOURCE/'lg02.geometry.yml'),str(OUTPUT/'maps/lg02.blv'),str(SOURCE/'lg02.doors.yml'),
                str(SOURCE/'lg02.faces.yml')],check=True)
metadata=json.loads((SOURCE/'lg02.geometry.yml').read_text())
semantics=json.loads((SOURCE/'lg02.semantic.json').read_text())
scene=json.loads((SOURCE/'lg02.scene.yml').read_text())
doors=yaml.safe_load((SOURCE/'lg02.doors.yml').read_text())
assert {d['door_id'] for d in doors}=={1,2,3,4,5,6,7,8}
by_door={d['door_id']:d for d in doors}
assert by_door[1]['direction']==[65536,0,0]
assert by_door[2]['direction']==[-65536,0,0]
assert all(by_door[i]['direction']==[0,0,-65536] for i in [3,4,5,6,7,8])
scene['initial_state']['doors']=doors

blob=(SOURCE/'lg02.glb').read_bytes()
length=struct.unpack_from('<I',blob,12)[0]
gltf=json.loads(blob[20:20+length])
room_nodes=[]
def visit(index):
    node=gltf['nodes'][index]
    if 'mesh' in node and node.get('name','').startswith('ROOM_'):
        room_nodes.append(node['name'])
    for child in node.get('children',[]):
        visit(child)
for node_index in gltf['scenes'][gltf.get('scene',0)]['nodes']:
    visit(node_index)
sectors={name[5:]:index+1 for index,name in enumerate(room_nodes)}
assert len(sectors)==len(metadata['rooms'])
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_blv_file
native=parse_blv_file(OUTPUT/'maps/lg02.blv')['payload']
decoration_source=json.loads((SOURCE/'lg02.decorations.json').read_text())['records']
assert len(native['entities']) == len(metadata['entities']) == len(decoration_source)
assert len({entity['name'] for entity in native['entities']}) == len(native['entities'])
assert sorted((e['decoration_list_id'],tuple(e['position'][k] for k in 'xyz')) for e in native['entities']) == sorted(
    (e['id'],tuple(e['position'])) for e in decoration_source)
assert any(f['texture_name']=='gt003a' for f in native['faces']), 'Static furnishings were omitted'
lift_floors=[i for i in by_door[6]['face_ids'] if native['faces'][i]['facet_type']==3]
assert len(lift_floors)==1
assert native['faces'][lift_floors[0]]['face_param']['cog_triggered']==105
for door in doors:
    # Every Greywatch mesh is authored closed. Check physical coordinates, not just the state label.
    assert door['state'] == 2
    for index, vertex_id in enumerate(door['vertex_ids']):
        vertex = native['vertices'][vertex_id]
        for axis_index, axis in enumerate('xyz'):
            closed = door[axis+'_offsets'][index] + door['direction'][axis_index]/65536 * door['move_length']
            assert closed == vertex[axis], (door['door_id'], vertex_id, axis, closed, vertex[axis])
native_portals={(f['room_number'],f['room_behind_number']) for f in native['faces'] if f['is_portal']}
assert native_portals=={(sectors[p['front_room'][5:]],sectors[p['back_room'][5:]]) for p in metadata['portals']}

def read_table(name):
    with (ROOT/'assets_dev/engine/data_tables'/name).open(newline='') as stream:
        return {int(row[0]):row for row in csv.reader(stream,delimiter='\t') if row and row[0].isdigit()}
stats=read_table('monster_data.txt')
descriptors=read_table('monster_descriptors.txt')
actors=[]
for marker in sorted(semantics['fixed_actors'],key=lambda a:a['id']):
    monster_id=marker['monster_id']; entry=stats[monster_id]; descriptor=descriptors[monster_id]
    assert entry[2].startswith('Human Mercenary ')
    actors.append({'actor_index':len(actors),'name':entry[1],'npc_id':0,'attributes':0x80000,
      'hp':int(entry[4]),'hostility_type':int(entry[12]),'monster_info_id':monster_id,'monster_id':monster_id,
      'radius':int(descriptor[3]),'height':int(descriptor[2]),'move_speed':int(entry[13]),
      'position':dict(zip('xyz',marker['position'])),'sprite_ids':[0,0,0,0],'sector_id':sectors[marker['room']],
      'current_action_animation':0,'carried_item_id':0,'group':1,'ally':0,'unique_name_index':0})
scene['initial_state']['actors']=actors
assert len(actors)==24
scene['loot_containers']=[]
for index,(name,position) in enumerate([('armory',[-3328,3328,768]),('secret',[8704,5504,384]),
                                       ('barracks',[9216,3200,384]),('vault',[9728,7936,768])]):
    scene['loot_containers'].append({'source_id':'mm8:greywatch:'+name+'_chest','source_object_index':index,
      'source_name':name+' chest','position':dict(zip('xyz',position)),'container_id':index,'kind':'chest',
      'presentation':'wooden chest','random_treasure_level':5,'treasure_type':0,'gold':750+index*250,
      'gold_only':False,'random':True,'ai_drop':False,'trap_level':1,'should_repopulate':True,
      'fixed_items':[],'remove_when_empty':False})
from configure_rewards import apply_reward_policy
apply_reward_policy('lg02.blv', scene['loot_containers'])
(OUTPUT/'maps/lg02.scene.yml').write_text(json.dumps(scene,indent=2)+'\n')

events={e['id']:e for e in semantics['events']}
bound={f['face_param']['cog_triggered'] for f in native['faces'] if f['face_param']['cog_triggered']}
assert bound==set(events), (bound,set(events))
text='-- Generated assembly; author source/lg02.handlers.lua and Blender semantic objects.\n'
text+='local LG = {outdoor={castle={15360,14848,1536},cave={15360,-17408,1280}}}\n'
text+='SetMapMetadata({onLoad={},onLeave={},openedChestIds={'
text+=','.join('['+str(201+i)+']={'+str(i)+'}' for i in range(4))+'}})\n'
text+=(SOURCE/'lg02.handlers.lua').read_text()+'\n'
for event_id,event in sorted(events.items()):
    title=event['name'].replace('_',' ').capitalize()
    text+='assert(type(handlers['+str(event_id)+']) == "function", "Missing Greywatch handler '+str(event_id)+'")\n'
    text+='RegisterEvent('+str(event_id)+','+json.dumps(title)+',handlers['+str(event_id)+'],'+json.dumps(title)+')\n'
(OUTPUT/'events/maps/lg02.lua').write_text(text)
report={'status':'compiled; gameplay evidence is recorded separately in review','map':'lg02.blv','sectors':sectors,
        'bounds':[[min(v[k] for v in native['vertices']) for k in 'xyz'],
                  [max(v[k] for v in native['vertices']) for k in 'xyz']],
        'faces':len(native['faces']),'portals':len(native_portals),'bsp_nodes':len(native['bsp_nodes']),
        'outlines':len(native['outlines']),'doors':{str(d['door_id']):{'slot':d['door_index'],'faces':d['face_ids'],
          'vertices':d['vertex_ids'],'direction':d['direction']} for d in doors},
        'events':{str(e):[f['index'] for f in native['faces'] if f['face_param']['cog_triggered']==e] for e in sorted(bound)},
        'actors':len(actors),'chests':len(scene['loot_containers']),'lights':len(native['lights']),
        'decorations':len(native['entities']),
        'lighting_provenance':{'torch':'MM8 d18 dec56; merged decoration row 299 / native index 298',
            'decoration_light_radius':96,'static_light_radius':640,
            'policy':'dec56 flame light plus larger authored static pool, as separate sources; native lighting evidence: review/lighting_perception.json'},
        'reuse':{'monsters':{str(i):stats[i][1:3] for i in [193,194,195]},
                 'textures':{m['texture']:str(texture) for m in metadata['materials']
                 for texture in [ROOT/'assets_dev/worlds/mm8/textures'/(m['texture'].lower()+'.bmp')]}}}
(PROJECT/'greywatch_build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['faces','portals','bsp_nodes','outlines','actors','chests','lights']}))
