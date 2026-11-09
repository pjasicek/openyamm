"""Check the D15 native payload, its source contract, and its staged copy."""
import base64
import collections
import copy
import importlib.util
import json
import struct
import sys
from pathlib import Path
import yaml

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_blv_file
spec=importlib.util.spec_from_file_location('zone4',ROOT/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone=importlib.util.module_from_spec(spec);spec.loader.exec_module(zone)
assert not zone.plans.ceiling_problems(zone.d15)
assert zone.plans.max_light_overlap(zone.d15)[0] <= 4
semantic=json.loads((PROJECT/'source/hes_d15.semantic.json').read_text())
metadata=json.loads((PROJECT/'source/hes_d15.geometry.yml').read_text())
native=parse_blv_file(PROJECT/'runtime/hes_d15.blv')['payload']
scene=json.loads((PROJECT/'runtime/hes_d15.scene.yml').read_text())
assert len(native['sectors'])==39 and len(metadata['rooms'])==38
assert semantic['sectors']==sorted(semantic['sectors'])
counts=collections.Counter(f['room_number'] for f in native['faces'] if not f['is_portal'])
assert counts[0]==0
assert all(100<=counts[i]<=300 for i in range(1,39)),counts
# Confirm native room numbers agree with semantic names, rather than assuming the metadata list is the import order.
for index,name in enumerate(semantic['sectors'],1):
    bd=semantic['room_bounds'][name.removeprefix('room_')]
    inside=0
    for face in native['faces']:
        if face['room_number']!=index or face['is_portal']:continue
        vs=[native['vertices'][v] for v in face['vertex_indices']]
        x=sum(v['x'] for v in vs)/len(vs);y=sum(v['y'] for v in vs)/len(vs)
        inside += bd[0]-1<=x<=bd[2]+1 and bd[1]-1<=y<=bd[3]+1
    assert inside>0,name
assert set(semantic['door_ids'].values())==set(range(1,15))
actors=scene['initial_state']['actors'];assert len(actors)==72
for a in actors:
    name=semantic['sectors'][a['sector_id']-1].removeprefix('room_');bd=semantic['room_bounds'][name]
    x,y,z=(a['position'][k] for k in ('x','y','z'))
    assert bd[0]<=x<=bd[2] and bd[1]<=y<=bd[3] and bd[4]<=z<=bd[5],a
assert sum(a['group']==9 and a['attributes']&0x10000!=0 for a in actors)==3
assert len(scene['loot_containers'])==6 and sum(c['random'] for c in scene['loot_containers'])==5
assert scene['loot_containers'][5]['fixed_items'][0]['item_id']==11332
assert not scene['initial_state']['sprite_objects']
assert len(native['lights'])==5 and sum(bool(l['fixture']) for l in zone.d15.lights)==30
bindings={d['name']:d for d in yaml.safe_load((PROJECT.parent/'hesper_stage/decorations.yml').read_text())['decorations']}
assert not bindings['hes_creep_pod_static'].get('light')
review_plan=copy.copy(zone.d15);review_plan.lights=semantic['review_lights']
assert len(review_plan.lights)==35 and zone.plans.max_light_overlap(review_plan)[0]<=4
for original,light in zip(zone.d15.lights,review_plan.lights):
    assert all(original[k]==light[k] for k in ('id','x','y','z','group'))
    if light['fixture']:assert bindings[light['fixture']]['light']==[light['radius'],*light['colour']]
assert next(l for l in review_plan.lights if l['id']=='L4')['colour']==[255,165,70]
powered=[e for e in metadata['entities'] if 'hes_d15_tunnel_lamp_off_' in e['id']]
assert len(powered)==3 and all(e['event_id_primary']==zone.plans.FIXTURE_COG+1==121 for e in powered)
handler=(PROJECT/'source/hes_d15.handlers.lua').read_text()
assert "SetSprite(121, 1, 'hes_d15_tunnel_lamp')" in handler
assert "SetSprite(121, 1, 'hes_d15_tunnel_lamp_off')" in handler
assert {r['min_ambient_light_level'] for r in metadata['rooms']}=={14,16,20}
# map_export labels these scalar fields with MM6 offsets; compiled MM8 ambient is at 0x66 (IndoorMapData.cpp).
for source,sector in zip(metadata['rooms'],native['sectors'][1:]):
    assert struct.unpack_from('<h',base64.b64decode(sector['raw_record_base64']),0x66)[0]==source['min_ambient_light_level']
carriages=[(3300,200,5700,800),(4880,-150,7320,670),(4100,1640,6500,2280),
           (7728,-544,10456,224),(12728,-544,15456,224)]
for face in native['faces']:
    key=face['texture_name']
    if key not in ('httram','httramend'):continue
    assert max(face['texture_vs'])-min(face['texture_vs'])<=(128 if key=='httram' else 256)
    vertices=[native['vertices'][i] for i in face['vertex_indices']]
    x,y=(sum(v[k] for v in vertices)/len(vertices) for k in ('x','y'))
    assert any(x0-1<=x<=x1+1 and y0-1<=y<=y1+1 for x0,y0,x1,y1 in carriages),(x,y,key)
assert len(semantic['dressing_solids'])==12
for a in actors:
    x,y,z=(a['position'][k] for k in ('x','y','z'));radius=a['radius']
    for x0,y0,z0,x1,y1,z1 in semantic['dressing_solids']:
        assert not (z0<=z<z1 and x0-radius<x<x1+radius and y0-radius<y<y1+radius),a
# The two tour sets must never overwrite one another, and their cameras stay outside the new solids.
names=[]
for file,prefix in [('review_tour_01.yml','dark_'),('review_tour_01_powered.yml','power_')]:
    tour=yaml.safe_load((PROJECT/file).read_text())
    for shot in tour['shots']:
        assert shot['name'].startswith(prefix);names.append(shot['name'])
        x,y,z=shot['position']
        assert not any(x0<=x<=x1 and y0<=y<=y1 and z0<=z+160<=z1
                       for x0,y0,z0,x1,y1,z1 in semantic['dressing_solids'])
assert len(names)==len(set(names))==9
water=[s for s in metadata['surfaces'] if s['id'].startswith('cut_water')]
assert len(water)==4 and all(s['flags']==['untouchable'] for s in water)
stage=ROOT/'output/hesper_stage/assets_editor_dev/worlds/hesper'
for material in metadata['materials']:
    key=material['texture'];assert len(key)<=10 and (stage/'textures_x4'/(key+'.oytex')).exists(),key
for name,subfolder in (('hes_d15.blv','maps'),('hes_d15.scene.yml','maps'),('hes_d15.lua','events/maps')):
    assert (PROJECT/'runtime'/name).read_bytes()==(stage/subfolder/name).read_bytes(),name
maps=yaml.safe_load((PROJECT.parent/'hesper_stage/maps.yml').read_text())['maps']
assert next(m for m in maps if m['file']=='hes_d15.blv')['id']==9136
print(f'D15 verified: {len(native["faces"])} faces; 38 occupied sectors ({min(counts.values())}-{max(counts.values())} faces each); '
      '14 doors; 72 actors; 6 chests; 35 planned lights; staged files identical.')
