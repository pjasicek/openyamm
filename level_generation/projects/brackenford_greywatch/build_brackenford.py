"""Build Brackenford from Blender-exported source through the native editor writer.

A fresh temporary source package prevents a stale ODM from replacing updated source geometry.
The output is an intermediate geometry package until services/population/review gates pass.
"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
SOURCE = PROJECT/'source'
OUTPUT = PROJECT/'runtime/worlds/mm8'
parser = argparse.ArgumentParser()
parser.add_argument('--asset-root', type=Path, default=Path('/tmp/openyamm-brackenford-greywatch/assets_editor_dev'))
args = parser.parse_args()
semantics = json.loads((SOURCE/'lg01.semantic.json').read_text())
reference = yaml.safe_load((ROOT/'assets_dev/worlds/mm8/maps/out02.scene.yml').read_text())
scene = {'format_version':1, 'kind':'outdoor_scene', 'source':{'geometry_file':'lg01.odm'},
         'environment':reference['environment'], 'terrain':{'attribute_overrides':[], 'footstep_sound_overrides':[]},
         'bmodel_faces':{'interactive_faces':[]}, 'entities':[], 'spawns':[],
         'initial_state':{'location':{'respawn_count':0,'last_respawn_day':0,'reputation':0,'alert_status':0},
                          'face_attribute_overrides':[], 'actors':[], 'sprite_objects':[], 'chests':[],
                          'variables':{'map':[0]*75,'decor':[0]*125}}}
scene['environment']['tile_set_lookup_indices'] = [90,126,162,414]
for event in semantics['events']:
    for face in event['faces']:
        scene['bmodel_faces']['interactive_faces'].append({'bmodel_index':event['bmodel_index'],'face_index':face,
          'legacy_attributes':0x2000000,'cog_number':0,'cog_triggered_number':event['id'],'cog_trigger':0})
start = next(a for a in semantics['arrivals'] if a['id']=='default')
scene['entities'].append({'entity_index':0,'name':'Party Start','decoration_list_id':13,'ai_attributes':2,
    'position':dict(zip('xyz',start['position'])),'facing':0,'event_id_primary':0,'event_id_secondary':0,
    'variable_primary':0,'variable_secondary':0,'special_trigger':0,'initial_decoration_flag':2})
from build_outdoor_content import apply_to_scene
apply_to_scene(scene)
decorations=json.loads((SOURCE/'lg01.decorations.json').read_text())
scene['entities'].extend(decorations['entities'])
map_stats_id = json.loads((SOURCE/'ids.json').read_text())['maps']['lg01.odm']
with (ROOT/'assets_dev/engine/data_tables/map_stats.txt').open() as stream:
    assert not any(row and row[0]==str(map_stats_id) for row in csv.reader(stream,delimiter='\t'))
package = {'format_version':1,'kind':'outdoor_map_package','package_id':'mm8:brackenford','display_name':'Brackenford',
    'map_file':'lg01.odm','scene_file':'lg01.scene.yml','geometry_metadata_file':'lg01.geometry.yml',
    'terrain_metadata_file':'lg01.terrain.yml','script_module':'maps/lg01.lua','map_stats_id':map_stats_id,
    'redbook_track':0,'environment_name':'grassland','is_top_level_area':True,
    'outdoor_bounds':{'enabled':True,'min_x':-24576,'max_x':24576,'min_y':-24576,'max_y':24576}}
(SOURCE/'lg01.scene.yml').write_text(json.dumps(scene,indent=2)+'\n')
(SOURCE/'lg01.map.yml').write_text(json.dumps(package,indent=2)+'\n')
(OUTPUT/'maps').mkdir(exist_ok=True,parents=True)
with tempfile.TemporaryDirectory(prefix='brackenford-build-') as directory:
    temp = Path(directory)
    for name in ['lg01.map.yml','lg01.scene.yml','lg01.geometry.yml','lg01.terrain.yml']:
        shutil.copy2(SOURCE/name,temp/name)
    log = PROJECT/'review/brackenford_build.log'
    with log.open('w') as stream:
        subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(args.asset_root),
            '--headless-build-map',str(temp/'lg01.map.yml')],check=True,stdout=stream,stderr=subprocess.STDOUT)
    shutil.copy2(temp/'lg01.odm',OUTPUT/'maps/lg01.odm')
shutil.copy2(SOURCE/'lg01.scene.yml',OUTPUT/'maps/lg01.scene.yml')

sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
native = parse_odm_file(OUTPUT/'maps/lg01.odm')['payload']
terrain = json.loads((SOURCE/'lg01.terrain.yml').read_text())
assert bytes(native['height_map']) == bytes.fromhex(terrain['height_map_hex'])
assert bytes(native['tile_map']) == bytes.fromhex(terrain['tile_map_hex'])
assert len(native['bmodels']) == len(semantics['bmodels'])
assert len(native['entities']) == len(scene['entities'])
for actual,expected in zip(native['entities'],scene['entities']):
    for key in ['name','decoration_list_id','position']:
        assert actual[key] == expected[key], (key,actual,expected)
bridge_index = next(m['index'] for m in semantics['bmodels'] if m['id']=='bridge_deck')
bridge = native['bmodels'][bridge_index]
assert bridge['faces'][0]['polygon_type'] == 5, 'Bridge underside must be a ceiling, never an upward floor'
assert bridge['faces'][1]['polygon_type'] == 3, 'Bridge deck must be an upward floor'
for index,sign in [(0,-1),(1,1)]:
    a,b,c = [bridge['vertices'][v] for v in bridge['faces'][index]['vertex_indices'][:3]]
    normal_z = (b['x']-a['x'])*(c['y']-a['y'])-(b['y']-a['y'])*(c['x']-a['x'])
    assert normal_z*sign > 0
for event in semantics['events']:
    model = native['bmodels'][event['bmodel_index']]
    for index in event['faces']:
        assert model['faces'][index]['cog_triggered_number'] == event['id']
report = {'status':'native content built; gameplay evidence is recorded separately in review', 'map':'lg01.odm',
          'bmodels':len(native['bmodels']), 'faces':sum(len(m['faces']) for m in native['bmodels']),
          'buildings':len(semantics['buildings']),'terrain_arrays_exact':True,
          'native_bytes':(OUTPUT/'maps/lg01.odm').stat().st_size,'events':semantics['events'],
          'actors':len(scene['initial_state']['actors']), 'chests':len(scene['loot_containers']),
          'loose_items':len(scene['world_items']), 'decorations':decorations['counts'],
          'native_decoration_records_exact':True}
(PROJECT/'brackenford_build.json').write_text(json.dumps(report,indent=2)+'\n')
from assemble_brackenford_events import assemble
assemble()
print(json.dumps({k:v for k,v in report.items() if k!='events'}))
