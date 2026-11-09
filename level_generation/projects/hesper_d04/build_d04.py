"""Compile D4, assemble actors/loot/events and publish its stage tree. Never writes assets_dev."""
import csv
import json
import shutil
import struct
import sys
from pathlib import Path
import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent/'hesper_stage'))
from blv_build import build

semantic = json.loads((PROJECT/'source/hes_d04.semantic.json').read_text())
glb = (PROJECT/'source/hes_d04.glb').read_bytes()
gltf = json.loads(glb[20:20+struct.unpack_from('<I',glb,12)[0]])
assert semantic['sectors'] == [n['name'].lower() for n in gltf['nodes'] if n['name'].startswith('ROOM_')]
rows = {int(r[0]):r for r in csv.reader((ROOT/'design/kreegan_world/data/monster_data.txt').read_text().splitlines(),
                                      delimiter='\t') if r and r[0].isdigit()}
monsters = {r['id']:r for r in yaml.safe_load((PROJECT.parent/'hesper_stage/monsters.yml').read_text())['monsters']}
sizes = {mid:(r['radius'],r['height']) for mid,r in monsters.items()}
# Ghulkat's accepted model is owned by the shared monster registry, as for the other actors.
assert monsters[10103]['height'] >= 1.3*max(monsters[mid]['height'] for mid in (10060,10200,10201,10202))
actors=[]
# Append the kennels so existing event-bound actor indices remain stable.
placed_actors = list(semantic['actors'])
for group, points in [(50, [(5000, -950), (5240, -950), (5120, -1190)]),
                      (51, [(7240, -950), (7480, -950), (7240, -1190), (7480, -1190)])]:
    for x, y in points:
        sector = semantic['sectors'].index('room_waste_a' if x < 5964 else 'room_waste_b') + 1
        assert 4800 <= x <= 7700 and -1400 <= y <= -800
        assert all((x-a['position'][0])**2+(y-a['position'][1])**2 > (sizes[10300][0]+sizes[a['monster']][0])**2
                   for a in placed_actors if a['position'][2] == -1280)
        placed_actors.append(dict(name='Waste Shafts kennel', monster=10300, group=group,
                                  position=[x, y, -1280], posted=False, yaw_degrees=90, sector=sector, npc=0))
assert len(placed_actors) == len(semantic['actors']) + 7
for a in placed_actors:
    mid=a['monster']; row=rows[mid]; radius,height=sizes[mid]; x,y,z=a['position']
    actors.append(dict(actor_index=len(actors),name=a['name'],npc_id=a['npc'],attributes=0,hp=int(row[4]),
                       hostility_type=int(row[12]),monster_info_id=mid,monster_id=mid,radius=radius,height=height,
                       move_speed=int(row[13]),position=dict(x=x,y=y,z=z),
                       initial_yaw_units=round(a['yaw_degrees']/360*2048)%2048,immobile=a['posted'],
                       sprite_ids=[0,0,0,0],sector_id=a['sector'],current_action_animation=0,
                       carried_item_id=0,group=a['group'],ally=0,unique_name_index=0))

scour_record=PROJECT.parent/'hesper_out2/out2_build.json'
scour='nil'
if scour_record.exists():
    out=json.loads(scour_record.read_text())
    arrival=out['arrivals']['d04_return']
    x,y,z=arrival['position']; direction=round(arrival['direction_degrees']/360*2048)%2048
    scour=f'{{{x},{y},{z},{direction},0,0,0,0,"hes_out2.odm"}}'
else:
    print('D4 INTEGRATION PENDING: hesper_out2/out2_build.json; event 50 reports the missing Scour explicitly.')

chests=[dict(name='unused zero slot',random=False,gold=0),
        dict(name='Surgery locker',fixed=[11200,11331,11374],random=False,gold=0),
        dict(name='Cell Block A pod',random=True,gold=0),dict(name='Sorting Pens tally pod',random=True,gold=0),
        dict(name='Collar bank drawer',fixed=[11331,11331],random=False,gold=0),
        dict(name='Waste Shafts pod',random=True,gold=0),
        dict(name='The Sump chest C',fixed=[11331,11331,11302,11302,11302],random=False,gold=0)]
report=build(PROJECT,'hes_d04.blv',
             {'ACTOR_BINDINGS':', '.join(f'[{k}]={a["group"]}' for k,a in enumerate(actors)),
              'SCOUR_BINDING':scour},arrival='d04_pit_stairs',chests=chests,actors=actors)
prisoner_door=next(d for d in yaml.safe_load((PROJECT/'source/hes_d04.doors.yml').read_text()) if d['door_id']==59)
assert len(set(prisoner_door['x_offsets'])) == 8, 'All four prisoner leaves must belong to mover 59'
runtime=PROJECT/'runtime'; tree=runtime/'worlds/hesper'
scene=json.loads((runtime/'hes_d04.scene.yml').read_text())
for i in (2,3,5): scene['loot_containers'][i]['random_treasure_level']=2

(runtime/'hes_d04.scene.yml').write_text(json.dumps(scene,indent=2)+'\n')
shutil.copy2(runtime/'hes_d04.scene.yml',tree/'maps/hes_d04.scene.yml')
(tree/'behaviors/bosses').mkdir(parents=True,exist_ok=True)
shutil.copy2(PROJECT/'source/ghulkat.lua',tree/'behaviors/bosses/ghulkat.lua')
report.update(actors=len(actors),combat_actors=60,chests=6,gold_piles=0,scour_exit_ready=scour!='nil',
              ghulkat_binding=monsters[10103]['binding'])
(PROJECT/'d04_build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
