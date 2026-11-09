"""Build an isolated flat native ODM using OpenYAMM's editor writer and named regression cases."""
import json
from pathlib import Path
import subprocess
import sys
import yaml

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
F=P/'fixture'
F.mkdir(exist_ok=True)
catalogue=json.loads((P.parent/'mm6_new_sorpigal/catalogue.json').read_text())
ids={t['name']:t['raw_tile_ids'][0] for t in catalogue['tiles']}
cases=json.loads((P/'test_cases.json').read_text())
grid=[[ids['6dirttyl']]*128 for _ in range(128)]
x,y,row_height=2,2,0
pads=[]
for case in cases:
 if case['id']=='repeat:cobbles_material':continue
 patch=case['tiles'];h=len(patch);w=len(patch[0])
 if x+w+2>127:x=2;y+=row_height+2;row_height=0
 assert y+h+2<127,(case['id'],y)
 # Keep the two grass layout cameras inside the engine's outdoor travel boundary.
 px,py=(64,100) if case['id']=='layout:grass_dirt_hole' else ((78,100) if case['id']=='layout:grass_dirt_island' else (x,y))
 for dy,names in enumerate(patch):
  for dx,name in enumerate(names):
   if name:grid[py+dy][px+dx]=ids[name]
 pads.append({'case':case['id'],'column':px,'row':py,'width':w,'height':h,
              'center_x':-32768+(px+w/2)*512,'center_y':32768-(py+h/2)*512,
              'excluded':bool(case.get('conflict')), 'note':'Only internal nonblank joins are evaluated; pad borders are excluded.'})
 x+=w+2;row_height=max(row_height,h)
scene={'format_version':1,'kind':'outdoor_scene','source':{'geometry_file':'oute3.odm'},
       'environment':yaml.safe_load((ROOT/'assets_dev/worlds/mm6/maps/oute3.scene.yml').read_text())['environment'],
       'terrain':{'attribute_overrides':[],'footstep_sound_overrides':[]},
       'bmodel_faces':{'interactive_faces':[]},'entities':[],'spawns':[],
       'initial_state':{'location':{'respawn_count':0,'last_respawn_day':0,'reputation':0,'alert_status':0},
                        'face_attribute_overrides':[],'actors':[],'sprite_objects':[],'chests':[],
                        'variables':{'map':[0]*75,'decor':[0]*125}}}
package={'format_version':1,'kind':'outdoor_map_package','package_id':'mm6:terrain_fixture',
         'display_name':'Terrain transition fixture','map_file':'oute3.odm','scene_file':'oute3.scene.yml',
         'geometry_metadata_file':'oute3.geometry.yml','terrain_metadata_file':'oute3.terrain.yml',
         'map_stats_id':10001,
         'redbook_track':0,'environment_name':'grassland','is_top_level_area':True}
terrain={'version':1,'map_file':'oute3.odm','height_map_hex':bytes(128*128).hex(),
         'tile_map_hex':bytes(v for row in grid for v in row).hex(),'attribute_map_hex':bytes(128*128).hex()}
geometry={'version':1,'map_file':'oute3.odm','bmodels':[]}
for name,data in [('map',package),('scene',scene),('terrain',terrain),('geometry',geometry)]:
 (F/f'oute3.{name}.yml').write_text(json.dumps(data,indent=2)+'\n')
(F/'pads.json').write_text(json.dumps(pads,indent=2)+'\n')
with (F/'build.log').open('w') as stream:
 subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(ROOT/'assets_dev'),
                 '--headless-build-map',str(F/'oute3.map.yml')],stdout=stream,stderr=subprocess.STDOUT,check=True)
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
native=parse_odm_file(F/'oute3.odm')['payload']
assert not any(native['height_map']) and not native['bmodels'] and not native['entities']
assert bytes(native['tile_map']).hex()==terrain['tile_map_hex']
print('Built flat native fixture:',len(pads),'pads; no bmodels/entities; exact terrain round-trip.')
