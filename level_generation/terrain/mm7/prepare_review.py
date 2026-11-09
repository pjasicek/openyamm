"""Stage frozen MM7 assets and build isolated flat native test maps, preserving production content."""
import configparser,csv,json,shutil,subprocess,yaml
from common import *
from inventory import GROUPS
STAGE=Path('/tmp/openyamm-mm7-terrain-review')
def mount(mode,quality,fixture=None):
 dest=STAGE/mode;assets=dest/'assets_dev';assets.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'assets_dev').iterdir():
  if p.name!='worlds' and not (assets/p.name).exists():(assets/p.name).symlink_to(p,target_is_directory=p.is_dir())
 (assets/'worlds').mkdir(exist_ok=True)
 for p in (ROOT/'assets_dev/worlds').iterdir():
  target=assets/'worlds'/p.name
  if p.name!='mm7':
   if not target.exists():target.symlink_to(p,target_is_directory=p.is_dir())
   continue
  target.mkdir(exist_ok=True)
  for q in p.iterdir():
   if q.name=='terrain_x2' or fixture and q.name=='maps':continue
   if not (target/q.name).exists():(target/q.name).symlink_to(q,target_is_directory=q.is_dir())
  if fixture:
   maps=target/'maps';maps.mkdir(exist_ok=True)
   for q in (p/'maps').iterdir():
    if q.name.startswith('7out01.'):continue
    if not (maps/q.name).exists():(maps/q.name).symlink_to(q,target_is_directory=q.is_dir())
   for ext in ('odm','scene.yml'):shutil.copy2(fixture/('7out01.'+ext),maps/('7out01.'+ext))
  terrain=target/'terrain_x2';terrain.mkdir(exist_ok=True)
  for q in OUT.glob('*.png'):shutil.copy2(q,terrain/q.name)
 config=configparser.ConfigParser(interpolation=None);config.read(ROOT/'settings.ini');config['assets']['root']=str(assets)
 if 'video_quality' not in config:config['video_quality']={}
 config['video_quality']['terrain']=quality
 if 'debug' not in config:config['debug']={}
 config['debug']['start_map_file']='7out01.odm'
 config['video']={'resolution':'1600x1200','fullscreen':'false','vsync':'false'}
 with (dest/'settings.ini').open('w') as f:config.write(f)
 return dest

def main():
 STAGE.mkdir(exist_ok=True)
 if not (STAGE/'openyamm').exists():shutil.copy2(ROOT/'build/game/openyamm',STAGE/'openyamm')
 for mode in ('original','enhanced'):mount(mode,'x1' if mode=='original' else 'x2')
 fixtures=json.loads((P/'reports/flat_fixtures.json').read_text());table=list(csv.DictReader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data_2.txt').open(),delimiter='\t'))
 poses={};map_hashes={}
 for mode,lookup,families in [('green',[90,126,270,414],['grass','swamp','shore']),('dry',[234,342,306,414],['sand','snow','waste'])]:
  folder=P/'fixture'/mode;folder.mkdir(parents=True,exist_ok=True)
  names={table[i]['texture_name'].lower():i for i in range(90)}
  for slot,base in enumerate(lookup):
   for offset in range(36):names.setdefault(table[base+offset]['texture_name'].lower(),90+slot*36+offset)
  grid=[['7dirttyl']*128 for _ in range(128)]
  for row,g in enumerate(families):
   px,py=50,38+row*17;prefix=GROUPS[g][1]
   for i,pad in enumerate(fixtures[g]):
    if i==1:
     for j in range(7):
      grid[py-1][px+5+j]=prefix+('nw' if j==0 else 'ne' if j==6 else 'n')
      grid[py+5][px+5+j]=prefix+('sw' if j==0 else 'se' if j==6 else 's')
     for j in range(5):grid[py+j][px+5]=prefix+'w';grid[py+j][px+11]=prefix+'e'
    for y,line in enumerate(pad):
     for x,n in enumerate(line):grid[py+y][px+i*6+x]=n
   poses[g]=dict(mode=mode,x=(px+5.5-64)*512,y=(64-py-8)*512-1500,z=4800,yaw=1.5707963268,pitch=-.96)
  # Closed road network with all ordinary openings, plus native variants in a nearby pad.
  px,py=50,94
  for y in range(1,6):grid[py+y][px+3]='7drsrns'
  for x in range(1,6):grid[py+3][px+x]='7drsrew'
  for y,x,n in [(0,3,'7drsrncap'),(6,3,'7drsrscap'),(3,0,'7drsrwcap'),(3,6,'7drsrecap'),(3,3,'7drsrcros')]:grid[py+y][px+x]=n
  for y in range(3):
   for x in range(3):grid[py+y][px+9+x]=['7dirttyl','7dirt1','7dirt2'][x]
  if mode=='green':
   for y in range(3):
    for x in range(3):grid[py+4+y][px+9+x]=['7swtyl','7swtylv1','7swtylv2'][x]
  if mode=='green':
   for j in range(5):
    grid[py+3][px+8+j]='7swdrt'+('nw' if j==0 else 'ne' if j==4 else 'n')
    grid[py+7][px+8+j]='7swdrt'+('sw' if j==0 else 'se' if j==4 else 's')
   for j in range(3):grid[py+4+j][px+8]='7swdrtw';grid[py+4+j][px+12]='7swdrte'
  poses['roads_'+mode]=dict(mode=mode,x=(px+5.5-64)*512,y=(64-py-8)*512-1500,z=4800,yaw=1.5707963268,pitch=-.96)
  for kind in ('map','scene','terrain','geometry'):
   data=yaml.safe_load((T/'mm6_new_sorpigal_transitions/fixture'/('oute3.'+kind+'.yml')).read_text())
   data=json.loads(json.dumps(data).replace('oute3','7out01').replace('mm6:','mm7:'))
   if kind=='terrain':data['tile_map_hex']=bytes(names[n] for rr in grid for n in rr).hex()
   if kind=='scene':data['environment'].update(master_tile=1,tile_set_lookup_indices=lookup)
   if kind=='map':
    data.update(package_id='mm7:terrain_fixture_'+mode,display_name='MM7 terrain '+mode);data.pop('source_fingerprint',None);data.pop('built_source_fingerprint',None)
   (folder/('7out01.'+kind+'.yml')).write_text(json.dumps(data,indent=2)+'\n')
  with (folder/'build.log').open('w') as f:subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(ROOT/'assets_dev'),'--headless-build-map',str(folder/'7out01.map.yml')],stdout=f,stderr=subprocess.STDOUT,check=True)
  for quality in ('x1','x2'):mount(mode+'_'+quality,quality,folder)
  map_hashes[mode]=sha(folder/'7out01.odm')
 poses['road_ew_close']=dict(mode='dry',x=-6656,y=-17152,z=200,yaw=0,pitch=-.30)
 poses['road_close']=dict(mode='dry',x=-5376,y=-18400,z=200,yaw=1.5707963268,pitch=-.30)
 seed=P/'captures/emerald_seed.oysav'
 if not seed.exists():shutil.copy2('/tmp/openyamm_scenario_saves/levelgen_capture_mm7_emerald_original/view.oysav',seed)
 for mode in ('original','enhanced'):
  dest=STAGE/mode;(dest/'saves').mkdir(exist_ok=True)
  start=dest/'saves/MM7_Terrain_Start.oysav'
  if not start.exists():shutil.copy2(seed,start)
  config=configparser.ConfigParser();config.read(dest/'settings.ini')
  config['startup']={'start_in_main_menu':'false','save_file':str(start)}
  with (dest/'settings.ini').open('w') as f:config.write(f)
 for name,p in poses.items():
  subprocess.run(['/tmp/mm7-terrain-capture-save',str(seed),str(P/'captures'/(name+'.oysav')),*[str(p[k]) for k in ('x','y','z','yaw','pitch')],'empty-world','--fly-buff'],check=True,stdout=subprocess.DEVNULL)
 (P/'reports/review_stage.json').write_text(json.dumps(dict(stage=str(STAGE),binary_sha256=sha(STAGE/'openyamm'),map_hashes=map_hashes,files={p.name:sha(p) for p in OUT.glob('*.png')},poses=poses),indent=2)+'\n')
 print(STAGE)
if __name__=='__main__':main()
