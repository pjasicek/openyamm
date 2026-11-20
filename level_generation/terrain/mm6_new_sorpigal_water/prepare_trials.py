"""Prepare private original-water, candidate-water and flat native review stages."""
import configparser,json,shutil,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];L=P.parent/'mm6_new_sorpigal_transitions'
PLAY=Path('/tmp/openyamm-sorpigal-peasants-playtest');STAGE=Path('/tmp/openyamm-sorpigal-water-review')
sys.path.insert(0,str(ROOT/'level_generation/creatures/mm6_peasants'))
from prepare_playtest import mirror_assets
STAGE.mkdir(exist_ok=True)
if not (STAGE/'openyamm').exists():shutil.copy2(PLAY/'openyamm',STAGE/'openyamm')
for name in ['original','candidate','flat']:
 run=STAGE/name;run.mkdir(exist_ok=True);assets=run/'assets_dev'
 if not assets.exists():mirror_assets(PLAY/'enhanced/assets_dev',assets)
 terrain=assets/'worlds/mm6/terrain_x2'
 if terrain.is_symlink():terrain.unlink();shutil.copytree(PLAY/'enhanced/assets_dev/worlds/mm6/terrain_x2',terrain)
 if name!='original':
  for f in (P/'runtime_x2/worlds/mm6/terrain_x2').glob('*.png'):shutil.copy2(f,terrain/f.name)
 maps=assets/'worlds/mm6/maps'
 if maps.is_symlink():maps.unlink();shutil.copytree(ROOT/'assets_dev/worlds/mm6/maps',maps)
 shutil.copy2(P/'map_correction/oute3.odm',maps/'oute3.odm')
 if name=='flat':
  for f in maps.glob('oute3.scene*.yml'):f.unlink()
  shutil.copy2(P/'fixture/oute3.odm',maps/'oute3.odm');shutil.copy2(P/'fixture/oute3.scene.yml',maps/'oute3.scene.yml')
 settings=configparser.ConfigParser(interpolation=None);settings.read(PLAY/'enhanced/settings.ini')
 settings['assets']['root']=str(assets);settings['video_quality']['terrain']='x2'
 settings['debug']['start_flying']='true'
 with (run/'settings.ini').open('w') as f:settings.write(f)
print(STAGE)
