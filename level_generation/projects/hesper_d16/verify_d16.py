"""Check D16's native contract and the real saved behavior/light state from its scenarios."""
import collections
import importlib.util
import json
from pathlib import Path
import struct
import sys
import yaml

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_blv_file


def saved_state(path,stage,off):
    """Read only D16's identifiable records in SaveGame.cpp's version-100 binary layout."""
    data=path.read_bytes()
    assert data[:8]==b'OYSAVE1\0' and struct.unpack_from('<I',data,8)[0]==100
    class Reader:
        def __init__(self,offset):self.offset=offset
        def get(self,fmt):
            result=struct.unpack_from('<'+fmt,data,self.offset);self.offset+=struct.calcsize('<'+fmt)
            return result[0] if len(result)==1 else result
        def string(self):
            n=self.get('Q');assert n<100000 and self.offset+n<=len(data)
            result=data[self.offset:self.offset+n];self.offset+=n;return result
    key=f'hesper/conductor_{stage}'.encode()
    assert data.count(key)==3,(path,key)  # active scene and the two serialized map snapshots
    pos=data.index(key);r=Reader(pos-20)
    assert r.get('Q')==22 and r.get('I')==22 and r.string()==key
    started,dead,hp,age,cooldown,seed=r.get('BBiffI')
    assert started and not dead and hp>0
    r.string()  # serialized Lua state is a byte vector
    thresholds=r.get('Q');assert thresholds==0
    timers={}
    for _ in range(r.get('Q')):
        name=r.string().decode();timers[name]=r.get('f')
    wards=[]
    for _ in range(r.get('Q')):
        name=r.string();radius,seconds=r.get('ff');effect=r.string()
        scale,interval,cooldown,age=r.get('ffff');visual=r.get('B3Bfff')
        wards.append((name,radius,seconds,visual))
    assert r.get('B')==0  # no scripted animation hold
    assert r.get('B')==1
    spell,skill,mastery,chance=r.get('IIii')
    assert (spell,skill,mastery,chance)==(9,14,3,45 if stage==0 else 30)
    if stage:
        assert len(wards)==1 and wards[0][0:2]==(b'drawn',500)
        duration={3:10,2:6,1:4}[stage]
        assert duration-.3<=wards[0][2]<=duration
        assert wards[0][3][0:4]==(1,205,175,255)
        timer='ward' if stage==3 else 'warn';period={3:10,2:11,1:15}[stage]
        assert period-.3<=timers[timer]<=period
    else:assert not wards and 'staff' in timers
    # Sprite overrides precede indoorLightsEnabled in EventRuntimeState. Identify the complete three-entry map,
    # then parse the adjacent light map; do not infer a light state from the handler's requested MapVar alone.
    candidates=[]
    for name in (b'hes_alarm_pylon',b'hes_tunnel_lamp',b'hes_lattice_coil'):
        pos=data.find(name)
        if pos<22:continue
        r=Reader(pos-22)
        if r.get('Q')!=3:continue
        sprites={}
        for _ in range(3):
            cog,hidden,present=r.get('IBB');assert present==1 and hidden==0
            sprites[cog]=r.string()
        assert set(sprites)=={70,121,122}
        count=r.get('Q');assert count<30
        lights={}
        for _ in range(count):
            light,enabled=r.get('IB');assert enabled in (0,1);lights[light]=enabled
        candidates.append(lights)
    assert len(candidates)==1
    for k,index in enumerate(column_lights):assert candidates[0][index]==(k not in off),(path,k,candidates[0])
    print(f'{path.name}: actor 22 conductor_{stage}, ward/timer/spell and column lights verified')


spec=importlib.util.spec_from_file_location('zone4',ROOT/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone=importlib.util.module_from_spec(spec);spec.loader.exec_module(zone)
assert not zone.plans.ceiling_problems(zone.d16) and zone.plans.max_light_overlap(zone.d16)[0]<=4
semantic=json.loads((PROJECT/'source/hes_d16.semantic.json').read_text())
meta=json.loads((PROJECT/'source/hes_d16.geometry.yml').read_text())
native=parse_blv_file(PROJECT/'runtime/hes_d16.blv')['payload']
scene=json.loads((PROJECT/'runtime/hes_d16.scene.yml').read_text())
assert len(native['sectors'])==21 and len(scene['initial_state']['actors'])==38
assert semantic['sectors']==sorted(semantic['sectors'])
assert set(semantic['door_ids'].values())==set(range(1,8))
assert set(semantic['arrivals'])=={'blast_door','service_tunnel'}
assert len(native['lights'])==10 and sum(bool(l['fixture']) for l in zone.d16.lights)==29
# The current plan has 39 lights (10 explicit + 29 fixtures), despite its summary saying 36.
assert len(zone.d16.lights)==39
assert len(scene['loot_containers'])==4
assert [i['item_id'] for i in scene['loot_containers'][3]['fixed_items']]==[11331,11113]
for actor,source in zip(scene['initial_state']['actors'],semantic['actors']):
    assert source['sector']==actor['sector_id'] and source['monster']==actor['monster_id']
    if actor['group']>=21:assert actor['immobile'] and actor['monster_id']==10142
counts=collections.Counter(f['room_number'] for f in native['faces'] if not f['is_portal'])
assert counts[0]==0 and max(counts.values())<=300
bindings={d['name']:d for d in yaml.safe_load((PROJECT.parent/'hesper_stage/decorations.yml').read_text())['decorations']}
for light in zone.d16.lights:
    if light['fixture']:assert bindings[light['fixture']]['light']==[light['radius'],*light['colour']]
stage=ROOT/'output/hesper_stage/assets_editor_dev/worlds/hesper'
for material in meta['materials']:
    key=material['texture'];assert len(key)<=10 and (stage/'textures_x4'/(key+'.oytex')).exists(),key
for name,sub in [('hes_d16.blv','maps'),('hes_d16.scene.yml','maps'),('hes_d16.lua','events/maps')]:
    assert (PROJECT/'runtime'/name).read_bytes()==(stage/sub/name).read_bytes(),name
column_lights=[next(i for i,l in enumerate(meta['lights']) if l['id']==name) for name in ('L8','L9','L10')]
print(f'D16: {len(native["faces"])} faces, 20 playable sectors, 7 doors, 38 actors, 4 chests; staged copies match.')
print('Sector faces:',min(counts.values()),'to',max(counts.values()),'; below 100:',sum(v<100 for v in counts.values()))
if '--saves' in sys.argv:
    folder=Path('/tmp/openyamm_scenario_saves/hesper_d16_main_path')
    for stage_id in (3,2,1,0):saved_state(folder/f'd16_stage{stage_id}.oysav',stage_id,set(range(3-stage_id)))
    folder=Path('/tmp/openyamm_scenario_saves/hesper_d16_columns')
    saved_state(folder/'d16_mixed_stage1.oysav',1,{0,1})
    saved_state(folder/'d16_mixed_stage0.oysav',0,{0,1,2})
