"""Stage flat and corrected New Sorpigal trials without writing to development assets."""
import argparse
import configparser
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from PIL import Image

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
STUDY=P.parent/'mm6_new_sorpigal_master_study'
sys.path.insert(0,str(STUDY))
from prepare_trial import mirror_assets

parser=argparse.ArgumentParser()
parser.add_argument('--original',action='store_true',help='Prepare baseline fixture before composites exist')
parser.add_argument('--runtime-dir',type=Path,default=P/'runtime_x2/worlds/mm6/terrain_x2')
args=parser.parse_args()
pads={r['case']:r for r in json.loads((P/'fixture/pads.json').read_text())}
poses=[]
for case in ['layout:grass_dirt_island','layout:grass_dirt_hole','layout:rock_dirt_island','layout:rock_dirt_hole','layout:road_loop','layout:road_branch']:
 pad=pads[case];name=case.split(':')[1]
 poses.append({'name':name+'_top','stage':'flat','x':pad['center_x']-1400,'y':pad['center_y'],
               'z':5200,'yaw':0,'pitch':-75,'case':case})
# Four oblique directions and two distances exercise opposite-side sampling and mip selection.
for direction,angle in [('east',0),('north',90),('west',180),('south',270)]:
 for distance,z,pitch in [('near',161,-16),('far',750,-20)]:
  pad=pads['layout:road_loop'];a=math.radians(angle)
  poses.append({'name':f'road_{direction}_{distance}','stage':'flat',
                'x':pad['center_x']-1800*math.cos(a),'y':pad['center_y']-1800*math.sin(a),
                'z':z,'yaw':angle,'pitch':pitch,'case':'layout:road_loop'})
for name,pose in json.loads((STUDY/'poses.json').read_text())['poses'].items():
 poses.append({'name':name,'stage':'map','source_save':str(STUDY/'references/poses'/(name+'.oysav'))})
for i,(x,y) in enumerate([(18,86),(54,91),(57,95),(16,99)]):
 poses.append({'name':f'corrected_{i+1}','stage':'map','x':-32768+(x+.5)*512-600,
               'y':32768-(y+.5)*512,'z':2200,'yaw':0,'pitch':-65,'case':f'corrected:{x},{y}'})
 if i in (0,3):poses[-1].update(x=-22500,z=3000,yaw=180,pitch=-55)
for variant in ['flat','map']:
 stage=Path('/tmp/openyamm-sorpigal-terrain-transitions')/variant
 assets=stage/'assets_dev'
 mirror_assets(ROOT/'assets_dev',assets)
 maps=assets/'worlds/mm6/maps'
 if maps.is_symlink():maps.unlink();shutil.copytree(ROOT/'assets_dev/worlds/mm6/maps',maps)
 if variant=='flat':
  for overlay in maps.glob('oute3.scene.*.yml'):
   overlay.unlink()
  shutil.copy2(P/'fixture/oute3.odm',maps/'oute3.odm')
  shutil.copy2(P/'fixture/oute3.scene.yml',maps/'oute3.scene.yml')
 else:shutil.copy2(P/'map_corrections/oute3.odm',maps/'oute3.odm')
 terrain=assets/'engine/terrain_x2';terrain.mkdir(exist_ok=True)
 catalogue=P.parent/'mm6_new_sorpigal'
 for t in json.loads((catalogue/'catalogue.json').read_text())['tiles']:
  with Image.open(catalogue/t['source_rgb']) as im:im.resize((256,256),Image.Resampling.NEAREST).save(terrain/(t['name']+'.png'))
 for path in (catalogue/'water_animation/runtime_x1').glob('*.png'):
  with Image.open(path) as im:im.resize((256,256),Image.Resampling.NEAREST).save(terrain/path.name)
 if not args.original:
  files=list(args.runtime_dir.glob('*.png'));assert len(files)==36
  world_terrain=assets/'worlds/mm6/terrain_x2';world_terrain.mkdir(exist_ok=True)
  for file in files:shutil.copy2(file,world_terrain/file.name)
 else:
  for file in (P/'runtime_x2/worlds/mm6/terrain_x2').glob('*.png'):
   (assets/'worlds/mm6/terrain_x2'/file.name).unlink(missing_ok=True)
 settings=configparser.ConfigParser();settings.read(STUDY/'references/settings_original.ini')
 settings['assets']['root']=str(assets);settings['video_quality']['terrain']='x2'
 with (stage/'settings.ini').open('w') as stream:settings.write(stream)
 out=P/'captures/poses';out.mkdir(parents=True,exist_ok=True)
 for pose in [p for p in poses if p['stage']==variant]:
  output=out/(variant+'_'+pose['name']+'.oysav')
  if 'source_save' in pose:shutil.copy2(pose['source_save'],output)
  else:
   cmd=['/tmp/sorpigal-transition-capture-save',str(STUDY/'references/poses/overview.oysav'),str(output),
        str(pose['x']),str(pose['y']),str(pose['z']),str(math.radians(pose['yaw'])),str(math.radians(pose['pitch']))]
   if variant=='flat':cmd.append('empty-world')
   subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
  pose['save']=str(output);pose['stage_path']=str(stage)
(P/'captures/poses.json').write_text(json.dumps(poses,indent=2)+'\n')
print('Prepared flat/map trials and',len(poses),'saved camera poses.')
