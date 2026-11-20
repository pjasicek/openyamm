"""Install the reviewed water candidate in a private enhanced New Sorpigal playtest."""
import argparse,configparser,hashlib,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--directory',type=Path,default=Path('/tmp/openyamm-sorpigal-peasants-playtest'))
 parser.add_argument('--with-map-correction',action='store_true')
 args=parser.parse_args();stage=args.directory.resolve(strict=True)
 marker=stage/'playtest_snapshot.json';snapshot=json.loads(marker.read_text())
 assert snapshot['world']=='mm6' and snapshot['map']=='oute3.odm'
 report=json.loads((P/'reports/validation_v1.json').read_text())
 assert not report['failures'] and not report['authoring_checks']['failures']
 assert json.loads((P/'reports/native_animation_check.json').read_text())['fixed_camera_land_stable']
 source=P/'runtime_x2/worlds/mm6/terrain_x2';target=stage/'enhanced/assets_dev/worlds/mm6/terrain_x2'
 for parent in (target,*target.parents):
  if parent==stage:break
  assert not parent.is_symlink(),parent
 for n,h in report['files'].items():
  assert Path(n).name==n and digest(source/n)==h
  assert not (target/n).is_symlink()
 maps=stage/'enhanced/assets_dev/worlds/mm6/maps'
 patch=json.loads((P/'map_correction/patch.json').read_text())
 if args.with_map_correction:
  assert digest(P/'map_correction/oute3.odm')==patch['output_sha256']
  assert digest(maps/'oute3.odm') in [patch['source_sha256'],patch['output_sha256']]
 target.mkdir(parents=True,exist_ok=True)
 for n in report['files']:shutil.copy2(source/n,target/n)
 if args.with_map_correction:
  if maps.is_symlink():
   original=maps.resolve();maps.unlink();shutil.copytree(original,maps)
  backup=stage/'seed/oute3_before_water_correction.odm'
  if not backup.exists():shutil.copy2(maps/'oute3.odm',backup)
  shutil.copy2(P/'map_correction/oute3.odm',maps/'oute3.odm')
 settings=configparser.ConfigParser(interpolation=None);settings.read(stage/'enhanced/settings.ini')
 settings['video_quality']['terrain']='x2'
 with (stage/'enhanced/settings.ini').open('w') as f:settings.write(f,space_around_delimiters=False)
 snapshot['water']={'version':'v1_candidate','source':str(source),'files':report['files'],'map_correction_installed':args.with_map_correction,'map_patch':patch if args.with_map_correction else None}
 marker.write_text(json.dumps(snapshot,indent=2)+'\n')
 print('Installed27 water/shore PNGs; corrected map:',args.with_map_correction)

if __name__=='__main__':main()
