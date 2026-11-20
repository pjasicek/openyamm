from pathlib import Path
import copy,hashlib,json,tempfile,yaml,shutil,os
root=Path.cwd();p=Path(__file__).resolve().parents[1];out=p/'review/ingame';out.mkdir(exist_ok=True)
source=root/'assets_dev';target=Path(tempfile.mkdtemp(prefix='visual-fixture-',dir=p/'work'))/'assets'
overrides={'worlds/mm6/maps/oute3.scene.yml','worlds/mm6/maps/6d19.scene.yml','worlds/mm8/models/actors.yml'}
shutil.copytree(source,target,copy_function=os.link,symlinks=True)
for rel in overrides:
 data=(target/rel).read_bytes();(target/rel).unlink();(target/rel).write_bytes(data)
records=[]
for rel in ['worlds/mm6/maps/oute3.scene.yml','worlds/mm6/maps/6d19.scene.yml']:
 original=(source/rel).read_bytes();scene=yaml.safe_load(original);actors=scene['initial_state']['actors'];count=len(actors)
 for monster in [49,50,51]:
  a=copy.deepcopy(actors[0]);a.update(actor_index=len(actors),name='Vampire female peasant preload fixture',monster_info_id=monster,monster_id=monster,unique_name_index=0,group=999,ally=999,hostility_type=0,sprite_ids=[0,0,0,0],immobile=True);actors.append(a)
 (target/rel).write_text(yaml.safe_dump(scene,sort_keys=False));assert (source/rel).read_bytes()==original
 records.append({'path':rel,'original_sha256':hashlib.sha256(original).hexdigest(),'added_monster_ids':[49,50,51]})
(out/'fixture.json').write_text(json.dumps({'assets_root':str(target),'scenes':records,'purpose':'Preload native MM8 sprite families in isolated MM6 scene copies; production maps unchanged.'},indent=2)+'\n')
for place,positions in [('out',[(-4184,3266,1),(-4158,3149,1),(-4132,3032,1)]),('in',[(1223,-3059,-47),(1223,-2934,-47),(1223,-2809,-47)])]:
 for mode in ['models','sprites']:
  steps=[{'expect':'gameplay'},{'wait':1},{'key':'`'},{'wait':.25}]
  for monster,pos in zip([49,50,51],positions):steps += [{'text':f'actor spawn {monster} 1 '+' '.join(map(str,pos))+' friendly'},{'key':'Return'},{'wait':.25}]
  steps += [{'key':'`'},{'wait':.2},{'capture':'front'},{'wait':1},{'capture':'walk'},{'wait':1},{'capture':'later'}]
  if mode=='models':steps += [{'key':'`'},{'text':'render lod 2'},{'key':'Return'},{'key':'`'},{'wait':.3},{'capture':'lod2'}]
  (out/f'{place}_{mode}.yml').write_text(yaml.safe_dump({'output_dir':str(out/f'{place}_{mode}'),'exit':True,'steps':steps},sort_keys=False))
 steps=[{'expect':'gameplay'},{'wait':1},{'key':'`'},{'wait':.2}]
 pos=(-4145,3152,1) if place=='out' else (1223,-2934,-47)
 steps += [{'text':'model spawn worlds/mm8/models/mm8_m464.glb '+' '.join(map(str,pos))+' 127.16803763770572 -1.17'},{'key':'Return'}]
 for clip,times in {'Standing':[.3],'Walking':[.2,.6],'Running':[.2],'Hit':[.2],'Fidget':[.5],'Death':[.2,.5,1.,2.144444],'Dead':[0]}.items():
  for sec in times:
   for cmd in [f'model play 0 {clip} once','model pause 0',f'model scrub 0 {sec}']:steps += [{'text':cmd},{'key':'Return'}]
   steps += [{'key':'`'},{'wait':.05},{'capture':f'{clip}-{sec:.3f}'},{'key':'`'}]
 steps += [{'key':'`'}]
 (out/f'{place}_actions.yml').write_text(yaml.safe_dump({'output_dir':str(out/f'{place}_actions'),'exit':True,'steps':steps},sort_keys=False))
print(target)
