"""Isolated native comparison fixture and reproducible console screenshot tours."""
from pathlib import Path
import copy,json,hashlib,os,shutil,tempfile,yaml
P=Path(__file__).resolve().parents[1];R=P.parents[2];out=P/'review/ingame';out.mkdir(exist_ok=True)
source=R/'assets_dev';target=Path(tempfile.mkdtemp(prefix='visual-fixture-',dir=P/'work'))/'assets'
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
records=[]
for relative in map(Path,['worlds/mm6/maps/6d19.scene.yml','worlds/mm6/maps/oute3.scene.yml']):
 original=(source/relative).read_bytes();scene=yaml.safe_load(original);actors=scene['initial_state']['actors']
 for monster in [142,143,144]:
  actor=copy.deepcopy(actors[0]);actor.update(actor_index=len(actors),name='Boulder review fixture',monster_info_id=monster,monster_id=monster,unique_name_index=0,group=999,ally=999,hostility_type=0,sprite_ids=[0,0,0,0],immobile=True,initial_yaw_units=0,move_speed=0,radius=60,height=160,hp=1000)
  positions=[(-4303,3656,1),(-4303,3296,1),(-4303,2856,1)] if 'oute3' in str(relative) else [(1140,-2610,-47),(1140,-2940,-47),(1140,-3330,-47)]
  actor['position']=dict(zip('xyz',positions[monster-142]));actors.append(actor)
 (target/relative).unlink();(target/relative).write_text(yaml.safe_dump(scene,sort_keys=False));assert (source/relative).read_bytes()==original
 records.append({'path':str(relative),'original_sha256':hashlib.sha256(original).hexdigest(),'added_monster_ids':[142,143,144]})
manifest=target/'worlds/mm8/models/actors.yml';data=manifest.read_bytes();manifest.unlink();manifest.write_bytes(data)
scale=json.loads((P/'work/placement.json').read_text())['scale']
def save(name,steps):
 (out/f'{name}.yml').write_text(yaml.safe_dump({'output_dir':str(out/name),'exit':True,'steps':[{'expect':'gameplay'},{'wait':1}]+steps},sort_keys=False))
for place,positions in [('out',[(-4303,3616,1),(-4303,3296,1),(-4303,2896,1)]),('in',[(1140,-2610,-47),(1140,-2940,-47),(1140,-3330,-47)])]:
 for mode in ['models','sprites']:
  steps=[{'wait':.3},{'capture':'tiers'},{'wait':.8},{'capture':'standing'}]
  if mode=='models':steps += [{'console':'actor damage last 1'},{'wait':.05},{'capture':'hit'},{'console':'actor kill 2000'},{'wait':.1},{'capture':'death'},{'wait':1.5},{'capture':'rubble'}]
  save(place+'_'+mode+'_fixed',steps)
 # A deterministic close-up exercises every mesh clip and all colour LODs in the real renderer.
 x,y,z=positions[1];steps=[{'console':'actor kill 2000'},{'wait':2},{'console':f'model spawn worlds/mm8/models/mm8_m588.glb {x} {y} {z} {scale} -1.570796327'}]
 for clip,times in [('Standing',[0]),('Walking',[.25,.75]),('Attack',[.7,1.0,1.15]),('Cast',[.7,1.0]),('Hit',[.13]),('Death',[.4,.75,1.25]),('Dead',[.5])]:
  steps += [{'console':f'model play 0 {clip} once'},{'console':'model pause 0'}]
  for t in times:steps += [{'console':f'model scrub 0 {t}'},{'wait':.12},{'capture':clip.lower()+'_'+str(t).replace('.','_')}]
 steps += [{'console':'model play 0 Standing'},{'console':'model pause 0'},{'console':'model scrub 0 0'}]
 for lod in range(4):steps += [{'console':f'render lod {lod}'},{'wait':.2},{'capture':f'lod{lod}'}]
 save(place+'_poses',steps)
steps=[{'console':'actor damage 44 1'}]
for n in range(35):steps += [{'wait':.25},{'capture':f'combat-{n:02}'}]
save('out_combat',steps)
(out/'fixture.json').write_text(json.dumps({'assets_root':str(target),'scenes':records,'purpose':'Preload MM8 native sprite family for model/sprite comparisons in the shared MM6 indoor/outdoor reference rooms.'},indent=2)+'\n')
print(target)
